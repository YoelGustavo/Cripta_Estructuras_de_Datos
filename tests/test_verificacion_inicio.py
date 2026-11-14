"""La verificación de resolubilidad al iniciar una partida y con
--verificar (capacidad 003, historias 3 y 4; contracts/cli.md y
contracts/datos-servicio.md).

    python -m unittest -v tests.test_verificacion_inicio

Cada prueba corre en una carpeta temporal (ahí se escriben partida.log y
la copia local); nunca usa cache/.
"""

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from crypta import main as programa
from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Adaptadores.FuenteDatos import LlavesNoDisponibles
from crypta.Adaptadores.FuenteHTTP import FuenteHTTP, PresupuestoAgotado
from crypta.Adaptadores.FuenteOffline import FuenteOffline
from crypta.Controlador.GestorCripta import GestorCripta
from crypta.Controlador.Verificacion import preparar_verificacion
from crypta.Modelo.ResultadoVerificacion import NoVerificable
from tests.ayudas_cripta import (FuenteContadora, contenido, respuesta_llaves,
                                 sala, salida, ubicacion)
from tests.test_controlador import (CONTENIDOS_PRUEBA, DATOS_PRUEBA,
                                    ESQUELETO_PRUEBA, FICHAS_PRUEBA)


SALIDA = "itm_llave_salida"

# c-prueba (la de test_controlador) es resoluble: itm_llave en la sala 2,
# puerta 2 -> 3 que la pide, sala_salida 3.
LLAVES_PRUEBA = respuesta_llaves(ubicacion("itm_llave", 2))

# c-cerrada no es resoluble: `salida` detrás de la única puerta que abre.
ESQUELETO_CERRADA = [
    sala(1, {"E": salida(2, cerrada=True, llave=SALIDA)}),
    sala(2, {"O": salida(1, cerrada=True, llave=SALIDA)}),
]
CONTENIDOS_CERRADA = [contenido(1), contenido(2)]
DATOS_CERRADA = dict(DATOS_PRUEBA, id="c-cerrada", version="v7",
                     salas_total=2, sala_inicial=1, sala_salida=2,
                     llave_salida=SALIDA)
LLAVES_CERRADA = respuesta_llaves(ubicacion(SALIDA, 2))

REPORTE_CERRADA = (
    "Verificación de resolubilidad: la cripta NO es resoluble.\n"
    "Llaves que no se pueden obtener:\n"
    "  itm_llave_salida\n"
    "Frontera bloqueada:\n"
    "  sala 1, E -> sala 2, pide itm_llave_salida\n"
)
NO_INICIA = "La partida no inicia. Use --forzar para jugarla de todos modos."
FORZADA = "Se inicia la partida por --forzar."


def fuente_cerrada(llaves=LLAVES_CERRADA):
    return FuenteContadora(ESQUELETO_CERRADA, CONTENIDOS_CERRADA,
                           fichas=FICHAS_PRUEBA, generales=dict(DATOS_CERRADA),
                           version_catalogo="cat-1", llaves=llaves)


class FuenteQueFallaEnLlaves(FuenteContadora):
    """Como fuente_cerrada, pero pedir las llaves lanza `error`."""

    def __init__(self, error):
        super().__init__(ESQUELETO_CERRADA, CONTENIDOS_CERRADA,
                         fichas=FICHAS_PRUEBA, generales=dict(DATOS_CERRADA),
                         version_catalogo="cat-1")
        self.error = error

    def obtener_llaves(self, cripta_id):
        self._contar("obtener_llaves")
        raise self.error


class ConCarpeta(unittest.TestCase):
    """Carpeta temporal como directorio actual y un almacén con el catálogo
    y las dos criptas (con sus llaves)."""

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.carpeta = self._carpeta.name
        self._antes = os.getcwd()
        os.chdir(self.carpeta)

        self.almacen = AlmacenDisco(os.path.join(self.carpeta, "cache"))
        self.almacen.guardar_catalogo("cat-1", FICHAS_PRUEBA)
        self.guardar_prueba(LLAVES_PRUEBA)
        self.guardar_cerrada(LLAVES_CERRADA)

    def tearDown(self):
        os.chdir(self._antes)
        self._carpeta.cleanup()

    def guardar_prueba(self, llaves):
        self.almacen.guardar_cripta("c-prueba", "v1", ESQUELETO_PRUEBA,
                                    CONTENIDOS_PRUEBA,
                                    datos_generales=DATOS_PRUEBA, llaves=llaves)

    def guardar_cerrada(self, llaves, version="v7"):
        self.almacen.guardar_cripta("c-cerrada", version, ESQUELETO_CERRADA,
                                    CONTENIDOS_CERRADA,
                                    datos_generales=DATOS_CERRADA, llaves=llaves)

    def correr(self, *argumentos, fuente=None, comandos=()):
        """El main de verdad. La vista es falsa (escribe `comandos` y
        "salir"); `self.vistas` cuenta cuántas veces se creó. En línea, la
        fuente es `fuente` en lugar de FuenteHTTP."""
        vista = Mock()
        vista.leer_comando.side_effect = list(comandos) + ["salir"]
        self.vistas = Mock(return_value=vista)
        salida_texto = io.StringIO()
        fuente_http = Mock(return_value=fuente) if fuente is not None else Mock(
            side_effect=AssertionError("no se esperaba usar la red"))

        with patch("crypta.main.AlmacenDisco", return_value=self.almacen), \
                patch("crypta.main.VistaConsola", self.vistas), \
                patch("crypta.main.FuenteHTTP", fuente_http), \
                patch.object(sys, "argv", ["crypta"] + list(argumentos)), \
                redirect_stdout(salida_texto):
            codigo = programa.main()

        return codigo, salida_texto.getvalue()

    def hay_partida_log(self):
        return os.path.exists(os.path.join(self.carpeta, "partida.log"))


class TestLlavesFuentes(ConCarpeta):
    """FR-322, FR-323, FR-324; HU3-4, HU3-5, HU3-6."""

    def test_fuente_http_pide_llaves_y_cuenta_FR_322(self):
        respuesta = Mock(status_code=200)
        respuesta.json.return_value = LLAVES_CERRADA
        fuente = FuenteHTTP()
        fuente.fijar_presupuesto(1)

        with patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                   return_value=respuesta) as get:
            self.assertEqual(fuente.obtener_llaves("c-cerrada"), LLAVES_CERRADA)
            self.assertTrue(get.call_args[0][0].endswith("/criptas/c-cerrada/llaves"))
            self.assertEqual(fuente.cantidad_solicitudes(), 1)

            # Presupuesto agotado: no se envía (FR-322).
            with self.assertRaises(PresupuestoAgotado):
                fuente.obtener_llaves("c-cerrada")

            self.assertEqual(get.call_count, 1)

    def test_fuente_offline_lee_la_copia_local_FR_324(self):
        fuente = FuenteOffline(self.almacen)
        self.assertEqual(fuente.obtener_llaves("c-cerrada"), LLAVES_CERRADA)

        self.guardar_cerrada(None)

        with self.assertRaises(LlavesNoDisponibles) as contexto:
            fuente.obtener_llaves("c-cerrada")

        self.assertIn("sin conexión", str(contexto.exception))

    def test_almacen_guarda_las_llaves_con_la_version_FR_323(self):
        guardada = self.almacen.cargar_cripta("c-cerrada", "v7")
        self.assertEqual(guardada["llaves"], LLAVES_CERRADA)
        self.assertEqual(guardada["version"], "v7")
        self.assertIsNone(self.almacen.cargar_cripta("c-cerrada", "v8"))

    def gestor(self, fuente):
        gestor = GestorCripta(fuente, self.almacen)
        gestor.cargar("c-cerrada")
        return gestor

    def test_misma_version_no_vuelve_a_pedir_FR_323_HU3_5(self):
        fuente = fuente_cerrada()
        self.assertEqual(self.gestor(fuente).cargar_llaves("c-cerrada"),
                         LLAVES_CERRADA)
        self.assertNotIn("obtener_llaves", fuente.por_operacion)

    def test_otra_version_se_invalida_y_se_pide_FR_323_HU3_5(self):
        self.guardar_cerrada({"llaves": []}, version="v6")
        fuente = fuente_cerrada()
        gestor = self.gestor(fuente)

        self.assertEqual(gestor.cargar_llaves("c-cerrada"), LLAVES_CERRADA)
        self.assertEqual(fuente.por_operacion["obtener_llaves"], 1)
        self.assertEqual(fuente.por_operacion["obtener_pagina_salas"], 1)

    def test_copia_sin_llaves_solo_pide_las_llaves_FR_323(self):
        self.guardar_cerrada(None)
        fuente = fuente_cerrada()
        gestor = self.gestor(fuente)

        self.assertEqual(gestor.cargar_llaves("c-cerrada"), LLAVES_CERRADA)
        self.assertEqual(fuente.por_operacion["obtener_llaves"], 1)
        self.assertNotIn("obtener_pagina_salas", fuente.por_operacion)

        gestor.persistir("c-cerrada", DATOS_CERRADA, gestor_mapa(gestor))
        self.assertEqual(self.almacen.cargar_cripta("c-cerrada", "v7")["llaves"],
                         LLAVES_CERRADA)

    def test_no_verificable_con_su_motivo_FR_324(self):
        self.guardar_cerrada(None)

        for error, motivo in (
                (LlavesNoDisponibles("sin conexión y sin la ubicación de las "
                                     "llaves en la copia local"),
                 "sin conexión y sin la ubicación de las llaves en la copia local"),
                (PresupuestoAgotado("se agotó"),
                 "presupuesto de solicitudes agotado"),
                (RuntimeError("Error de red al consultar /x"),
                 "falla de red: Error de red al consultar /x")):
            with self.subTest(error=type(error).__name__):
                resultado = self.gestor(
                    FuenteQueFallaEnLlaves(error)).cargar_llaves("c-cerrada")
                self.assertIsInstance(resultado, NoVerificable)
                self.assertEqual(resultado.motivo, motivo)


def gestor_mapa(gestor):
    """El Mapa que cargó el gestor (para persistir en las pruebas)."""
    from crypta.Modelo.Mapa import Mapa
    mapa = Mapa()
    mapa.cargar_desde_json(ESQUELETO_CERRADA)
    return mapa


class TestInicioPartida(ConCarpeta):
    """HU3-1, HU3-2, HU3-3, HU3-11 (FR-325, FR-327)."""

    def test_HU3_1_no_resoluble_sin_forzar_no_inicia_FR_325(self):
        """HU3-1 (Apéndice B): se muestra el reporte, la partida no inicia,
        no hay vista ni partida.log y el código es 2."""
        codigo, texto = self.correr("--offline", "--cripta", "c-cerrada")

        self.assertEqual(codigo, 2)
        self.assertIn(REPORTE_CERRADA, texto)
        self.assertIn(NO_INICIA, texto)
        self.vistas.assert_not_called()
        self.assertFalse(self.hay_partida_log())

    def test_HU3_2_con_forzar_inicia_FR_325(self):
        codigo, texto = self.correr("--offline", "--cripta", "c-cerrada",
                                    "--forzar")

        self.assertEqual(codigo, 0)
        self.assertIn(REPORTE_CERRADA, texto)
        self.assertIn(FORZADA, texto)
        self.assertNotIn(NO_INICIA, texto)
        self.vistas.assert_called_once()
        self.assertTrue(self.hay_partida_log())

    def test_HU3_3_resoluble_muestra_el_orden_e_inicia_FR_325(self):
        codigo, texto = self.correr("--offline", "--cripta", "c-prueba")

        self.assertEqual(codigo, 0)
        self.assertIn("Verificación de resolubilidad: la cripta es resoluble.\n"
                      "Orden de llaves:\n"
                      "  Ronda 1: itm_llave\n", texto)
        self.assertNotIn(FORZADA, texto)
        self.vistas.assert_called_once()
        self.assertTrue(self.hay_partida_log())

    def test_HU3_11_la_verificacion_no_cambia_el_mapa_FR_325_327(self):
        """HU3-11: el reporte nombra salas no exploradas y la verificación no
        cambia ninguna sala ni puerta del Mapa. La parte sobre el mapa
        conocido (las salas siguen desconocidas) se prueba en la capacidad
        002, que es la que crea el mapa conocido."""
        gestor = GestorCripta(FuenteOffline(self.almacen), self.almacen)
        datos, mapa, _ = gestor.cargar("c-cerrada")

        def foto():
            salas = mapa.obtener_todas()
            return [(s.id, s.contenido_cargado(),
                     [(p.sala_destino, p.cerrada, p.llave)
                      for p in (s.puertas().obtener(i)
                                for i in range(len(s.puertas())))])
                    for s in (salas.obtener(i) for i in range(len(salas)))]

        antes = foto()
        resultado = preparar_verificacion(gestor, "c-cerrada", datos, mapa)

        self.assertFalse(resultado.resoluble)
        self.assertEqual(foto(), antes)


class TestInicioSinVerificar(ConCarpeta):
    """HU3-4 a HU3-8 (FR-319, FR-321 a FR-325)."""

    def test_HU3_4_y_5_en_linea_pide_una_vez_y_guarda_FR_322_323(self):
        """HU3-4: sin llaves en la copia local se piden (contadas) y se
        guardan con la versión. HU3-5 / SC-306: el segundo inicio no las
        vuelve a pedir. HU3-8 / FR-321: no se pide contenido."""
        self.guardar_cerrada(None)
        fuente = fuente_cerrada()

        codigo, _ = self.correr("--cripta", "c-cerrada", fuente=fuente)

        self.assertEqual(codigo, 2)
        self.assertEqual(fuente.por_operacion["obtener_llaves"], 1)
        self.assertNotIn("obtener_contenido", fuente.por_operacion)
        guardada = self.almacen.cargar_cripta("c-cerrada", "v7")
        self.assertEqual(guardada["llaves"], LLAVES_CERRADA)

        otra = fuente_cerrada()
        codigo, _ = self.correr("--cripta", "c-cerrada", fuente=otra)

        self.assertEqual(codigo, 2)
        self.assertNotIn("obtener_llaves", otra.por_operacion)

    def test_HU3_6_sin_conexion_con_llaves_no_pide_nada_FR_324(self):
        with patch.object(FuenteOffline, "obtener_llaves",
                          side_effect=AssertionError("pidió las llaves")):
            codigo, texto = self.correr("--offline", "--cripta", "c-cerrada")

        self.assertEqual(codigo, 2)
        self.assertIn(REPORTE_CERRADA, texto)

    def test_HU3_6_sin_conexion_sin_llaves_FR_324_325(self):
        self.guardar_cerrada(None)

        codigo, texto = self.correr("--offline", "--cripta", "c-cerrada")

        self.assertEqual(codigo, 1)
        self.assertIn("Verificación de resolubilidad: no se pudo verificar "
                      "(sin conexión y sin la ubicación de las llaves en la "
                      "copia local). Se trata como no resoluble.", texto)
        self.assertIn(NO_INICIA, texto)
        self.assertFalse(self.hay_partida_log())

        codigo, texto = self.correr("--offline", "--cripta", "c-cerrada",
                                    "--forzar")

        self.assertEqual(codigo, 0)
        self.assertIn(FORZADA, texto)
        self.assertTrue(self.hay_partida_log())

    def test_HU3_6_falla_de_red_y_presupuesto_agotado_FR_322_324(self):
        self.guardar_cerrada(None)

        for error, motivo in ((RuntimeError("sin red"), "falla de red: sin red"),
                              (PresupuestoAgotado("se agotó"),
                               "presupuesto de solicitudes agotado")):
            with self.subTest(motivo=motivo):
                codigo, texto = self.correr(
                    "--cripta", "c-cerrada",
                    fuente=FuenteQueFallaEnLlaves(error))

                self.assertEqual(codigo, 1)
                self.assertIn(f"no se pudo verificar ({motivo})", texto)
                self.assertFalse(self.hay_partida_log())

    def test_HU3_7_sala_inexistente_no_inicia_ni_con_forzar_FR_319(self):
        self.guardar_cerrada(respuesta_llaves(ubicacion(SALIDA, 99)))

        for extra in ((), ("--forzar",)):
            with self.subTest(extra=extra):
                codigo, texto = self.correr("--offline", "--cripta",
                                            "c-cerrada", *extra)

                self.assertEqual(codigo, 1)
                self.assertIn("La cripta no se puede jugar: la ubicación de "
                              "llaves tiene un dato inválido: entrada 1 "
                              "(itm_llave_salida): la sala 99 no existe", texto)
                self.assertNotIn(FORZADA, texto)
                self.vistas.assert_not_called()
                self.assertFalse(self.hay_partida_log())


class TestSinVerificacion(ConCarpeta):
    """HU3-9 y HU3-10 (FR-326, FR-327)."""

    def test_HU3_9_replay_de_partida_forzada_no_verifica_FR_326(self):
        codigo, _ = self.correr("--offline", "--cripta", "c-cerrada",
                                "--semilla", "7", "--forzar",
                                comandos=["esperar", "esperar"])
        self.assertEqual(codigo, 0)

        with patch("crypta.Controlador.Verificacion.verificar",
                   side_effect=AssertionError("el replay verificó")), \
                patch.object(FuenteOffline, "obtener_llaves",
                             side_effect=AssertionError("el replay pidió llaves")):
            codigo, texto = self.correr("--offline", "--replay", "partida.log")

        self.assertEqual(codigo, 0)
        self.assertNotIn("Verificación de resolubilidad", texto)
        self.assertIn("Replay terminado: 2 comandos repetidos.", texto)

    def test_HU3_10_guardar_y_cargar_no_verifican_FR_326_327(self):
        from crypta.Controlador import Verificacion
        verificaciones = Mock(wraps=Verificacion.verificar)

        with patch("crypta.Controlador.Verificacion.verificar", verificaciones):
            codigo, texto = self.correr(
                "--offline", "--cripta", "c-cerrada", "--forzar",
                comandos=["esperar", "guardar", "esperar", "cargar"])

        self.assertEqual(codigo, 0)
        self.assertEqual(verificaciones.call_count, 1)    # solo al iniciar

        with open("partida.log", encoding="utf-8") as archivo:
            registro = archivo.read()

        self.assertNotIn("resolub", registro)
        self.assertNotIn("Ronda", registro)

        with open("partida.cripta", "rb") as archivo:
            guardado = archivo.read()

        self.assertNotIn("Verificación".encode("utf-8"), guardado)
        self.assertNotIn(b"no se pueden obtener", guardado)


class TestModoVerificar(ConCarpeta):
    """HU4-1 a HU4-6 (FR-322, FR-323, FR-328, FR-329, FR-336)."""

    def verificar(self, *argumentos, fuente=None):
        """--verificar sin vista ni partida: crear una u otra falla."""
        with patch("crypta.main.nueva_partida",
                   side_effect=AssertionError("--verificar creó una partida")):
            codigo, texto = self.correr(*argumentos, fuente=fuente)

        self.vistas.assert_not_called()
        self.assertFalse(self.hay_partida_log())
        return codigo, texto

    def test_HU4_1_resoluble_codigo_0_FR_328_329(self):
        codigo, texto = self.verificar("--offline", "--verificar", "c-prueba")

        self.assertEqual(codigo, 0)
        self.assertIn("Verificación de resolubilidad: la cripta es resoluble.\n"
                      "Orden de llaves:\n"
                      "  Ronda 1: itm_llave\n", texto)

    def test_HU4_2_no_resoluble_codigo_2_FR_328_329(self):
        codigo, texto = self.verificar("--offline", "--verificar", "c-cerrada")

        self.assertEqual(codigo, 2)
        self.assertIn(REPORTE_CERRADA, texto)
        self.assertNotIn(NO_INICIA, texto)

    def test_HU4_3_errores_codigo_1_FR_329(self):
        """Falla de red, datos inválidos y sin conexión sin llaves en la
        copia: se imprime el motivo y el código es 1."""
        self.guardar_cerrada(None)
        codigo, texto = self.verificar(
            "--verificar", "c-cerrada",
            fuente=FuenteQueFallaEnLlaves(RuntimeError("sin red")))
        self.assertEqual(codigo, 1)
        self.assertIn("no se pudo verificar (falla de red: sin red)", texto)

        codigo, texto = self.verificar("--offline", "--verificar", "c-cerrada")
        self.assertEqual(codigo, 1)
        self.assertIn("no se pudo verificar (sin conexión y sin la ubicación "
                      "de las llaves en la copia local)", texto)

        self.guardar_cerrada(respuesta_llaves(ubicacion(SALIDA, 99)))
        codigo, texto = self.verificar("--offline", "--verificar", "c-cerrada")
        self.assertEqual(codigo, 1)
        self.assertIn("la ubicación de llaves tiene un dato inválido", texto)

        # Una falla de red al pedir los datos de la cripta también es 1.
        sin_red = Mock()
        sin_red.obtener_cripta.side_effect = RuntimeError("Error de red")
        codigo, texto = self.verificar("--verificar", "c-cerrada",
                                       fuente=sin_red)
        self.assertEqual(codigo, 1)
        self.assertIn("Error de red", texto)

    def test_HU4_5_en_linea_cuenta_y_guarda_la_copia_FR_322_323(self):
        """HU4-5: sin copia local, pide esqueleto y llaves (contadas) y las
        guarda en la copia local como un inicio normal."""
        self.almacen = AlmacenDisco(os.path.join(self.carpeta, "vacia"))
        fuente = fuente_cerrada()

        codigo, _ = self.verificar("--verificar", "c-cerrada", fuente=fuente)

        self.assertEqual(codigo, 2)
        self.assertEqual(fuente.por_operacion["obtener_pagina_salas"], 1)
        self.assertEqual(fuente.por_operacion["obtener_llaves"], 1)
        self.assertNotIn("obtener_contenido", fuente.por_operacion)
        guardada = self.almacen.cargar_cripta("c-cerrada", "v7")
        self.assertEqual(guardada["llaves"], LLAVES_CERRADA)
        self.assertEqual(guardada["esqueleto"], ESQUELETO_CERRADA)

    def test_HU4_6_combinaciones_FR_336(self):
        """HU4-6: --verificar con --replay o --bench es error de uso
        (código 1, sin verificar); --forzar no cambia nada."""
        for extra in (("--replay", "partida.log"), ("--bench",)):
            with self.subTest(extra=extra), \
                    patch.object(FuenteOffline, "obtener_llaves",
                                 side_effect=AssertionError("verificó")), \
                    patch("crypta.bench.bench.ejecutar",
                          side_effect=AssertionError("corrió el bench")):
                codigo, texto = self.verificar("--offline", "--verificar",
                                               "c-cerrada", *extra)

                self.assertEqual(codigo, 1)
                self.assertNotIn("Verificación de resolubilidad", texto)

        sin = self.verificar("--offline", "--verificar", "c-cerrada")
        con = self.verificar("--offline", "--verificar", "c-cerrada",
                             "--forzar")
        self.assertEqual(con, sin)


if __name__ == "__main__":
    unittest.main()
