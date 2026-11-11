
import copy
import io
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from crypta import main as programa
from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Adaptadores.FuenteHTTP import FuenteHTTP, PresupuestoAgotado
from crypta.Adaptadores.FuenteOffline import FuenteOffline
from crypta.Controlador.Controlador import Controlador
from crypta.Controlador.Comandos import ComandoInvalido
from crypta.Controlador.Fabrica import nueva_partida
from crypta.Controlador.FichasEnUso import FichasEnUso
from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.Controlador.PreparadorReplay import PreparadorReplay
from crypta.Controlador.Reproductor import (
    ReproduccionFallida,
    ReproduccionIncompatible,
    Reproductor,
)
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import TURNO_ENEMIGO, AccionInvalida
from crypta.Modelo.TablaPuntajes import Puntaje, TablaPuntajes
from crypta.Vista.VistaConsola import VistaConsola


class TestControlador(unittest.TestCase):

    def setUp(self):
        self.partida = Mock()
        self.partida.iniciada = True
        self.partida.terminada = False
        self.partida.jugador.sala_actual = 1

        self.gestor = Mock()
        self.vista = Mock()
        self.registro = Mock()

        self.controlador = Controlador(
            partida=self.partida,
            gestor_contenido=self.gestor,
            vista=self.vista,
            registro=self.registro,
        )

    def test_comando_vacio(self):
        resultado = self.controlador.procesar_comando("   ")

        self.assertFalse(resultado)
        self.vista.mostrar_error.assert_called_once()

    def test_ayuda(self):
        resultado = self.controlador.procesar_comando("ayuda")

        self.assertTrue(resultado)
        self.vista.mostrar_ayuda.assert_called_once()
        self.registro.anotar.assert_not_called()

    def test_estado(self):
        resultado = self.controlador.procesar_comando("estado")

        self.assertTrue(resultado)
        self.vista.mostrar_estado.assert_called_once_with(
            self.partida
        )
        self.registro.anotar.assert_not_called()

    def test_inventario(self):
        resultado = self.controlador.procesar_comando("inventario")

        self.assertTrue(resultado)
        self.vista.mostrar_inventario.assert_called_once_with(
            self.partida.jugador.inventario
        )

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_movimiento(self, ejecutar):
        resultado = self.controlador.procesar_comando("mover N")

        self.assertTrue(resultado)
        ejecutar.assert_called_once_with(
            self.partida,
            "mover N",
            garantizar_sala=self.gestor.garantizar_sala,
        )
        self.registro.anotar.assert_called_once_with("mover N")

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_registro_accion(self, ejecutar):
        resultado = self.controlador.procesar_comando("esperar")

        self.assertTrue(resultado)
        self.registro.anotar.assert_called_once_with("esperar")

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_accion_invalida_no_se_registra(self, ejecutar):
        ejecutar.side_effect = AccionInvalida("Acción inválida")

        resultado = self.controlador.procesar_comando("mover N")

        self.assertFalse(resultado)
        self.registro.anotar.assert_not_called()
        self.vista.mostrar_error.assert_called_once()

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_comando_invalido_no_se_registra(self, ejecutar):
        ejecutar.side_effect = ComandoInvalido("Comando inválido")

        resultado = self.controlador.procesar_comando("desconocido")

        self.assertFalse(resultado)
        self.registro.anotar.assert_not_called()

    def test_guardar_sin_encabezado(self):
        resultado = self.controlador.procesar_comando("guardar")

        self.assertFalse(resultado)
        self.vista.mostrar_error.assert_called_once()

    @patch("crypta.Controlador.Controlador.copiar_archivo")
    @patch("crypta.Controlador.Controlador.guardar_partida")
    def test_guardar_con_encabezado(self, guardar, copiar):
        self.controlador.encabezado = Mock()

        resultado = self.controlador.procesar_comando("guardar")

        self.assertTrue(resultado)
        guardar.assert_called_once_with(
            self.partida,
            "partida.cripta",
            self.controlador.encabezado,
        )
        # Corrección 3: junto al guardado va una copia del log.
        copiar.assert_called_once_with(
            self.registro.ruta,
            "partida.cripta.log",
        )

    @patch.object(Controlador, "cargar_partida")
    def test_cargar(self, cargar):
        resultado = self.controlador.procesar_comando("cargar")

        self.assertTrue(resultado)
        cargar.assert_called_once_with("partida.cripta")

    @patch.object(Controlador, "cargar_partida")
    def test_error_al_cargar(self, cargar):
        cargar.side_effect = ValueError("Archivo incompatible")

        resultado = self.controlador.procesar_comando("cargar")

        self.assertFalse(resultado)
        self.vista.mostrar_error.assert_called_once()

    def test_alias_siguiente(self):
        self.assertEqual(
            self.controlador._traducir("siguiente"),
            "avanzar"
        )

    def test_alias_anterior(self):
        self.assertEqual(
            self.controlador._traducir("anterior"),
            "retroceder"
        )

    def test_comando_sin_alias_no_cambia(self):
        self.assertEqual(
            self.controlador._traducir("mover N"),
            "mover N"
        )

    def test_recoger_numero(self):
        self.assertEqual(
            self.controlador._traducir("recoger 1"),
            "recoger 0"
        )

    def test_recoger_numero_invalido(self):
        with self.assertRaises(ComandoInvalido):
            self.controlador._traducir("recoger 0")


# ======================================================================
# CORRECCIÓN 2: --replay con el Reproductor de la Fase 6 (§4.11)
# ======================================================================
# Una cripta chica guardada en una caché de prueba (carpeta temporal):
# se JUEGA con el controlador de verdad y después se REPRODUCE el log.

DATOS_PRUEBA = {
    "id": "c-prueba", "version": "v1", "salas_total": 3, "paginas": 1,
    "sala_inicial": 1, "sala_salida": 3, "llave_salida": "itm_llave",
    "presupuesto_solicitudes": 9, "inventario_max": 5,
    "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2, "velocidad": 100},
}

ESQUELETO_PRUEBA = [
    {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
    {"id": 2, "nombre": "Pasillo", "salidas": {
        "S": {"sala": 1},
        "N": {"sala": 3, "cerrada": True, "llave": "itm_llave"}}},
    {"id": 3, "nombre": "Salida", "salidas": {"S": {"sala": 2}}},
]

CONTENIDOS_PRUEBA = [
    {"sala": 1, "enemigos": [], "objetos": ["itm_antorcha", "itm_daga"],
     "trampas": []},
    {"sala": 2, "enemigos": [
        {"instancia": "e-1", "tipo": "ent_rata"},
        {"instancia": "e-2", "tipo": "ent_rata"}],
     "objetos": ["itm_llave"], "trampas": []},
    {"sala": 3, "enemigos": [], "objetos": [], "trampas": []},
]

FICHAS_PRUEBA = {
    "itm_antorcha": {"id": "itm_antorcha", "nombre": "Antorcha",
                     "clase": "antorcha", "peso": 1, "valor": 5,
                     "duracion": 2000},
    "itm_daga": {"id": "itm_daga", "nombre": "Daga", "clase": "arma",
                 "peso": 2, "valor": 15, "ataque_bonus": 3},
    "itm_llave": {"id": "itm_llave", "nombre": "Llave", "clase": "llave",
                  "peso": 1, "valor": 0},
    "ent_rata": {"id": "ent_rata", "nombre": "Rata", "clase": "enemigo",
                 "vida_max": 12, "ataque": 3, "defensa": 1,
                 "velocidad": 150, "comportamiento": "rastreador"},
}


def almacen_de_prueba(carpeta):
    almacen = AlmacenDisco(os.path.join(carpeta, "cache"))
    almacen.guardar_catalogo("cat-1", FICHAS_PRUEBA)
    almacen.guardar_cripta("c-prueba", "v1", ESQUELETO_PRUEBA,
                           CONTENIDOS_PRUEBA, datos_generales=DATOS_PRUEBA)
    return almacen


def foto(partida):
    """Todo lo que se ve de una partida, para comparar dos partidas."""
    jugador = partida.jugador
    return (
        jugador.nombre, partida.semilla,
        partida.reloj, jugador.sala_actual, jugador.vida,
        partida.acciones_jugador, partida.terminada, partida.resultado,
        tuple(ficha["id"] for ficha in jugador.inventario.orden_real()),
        tuple(partida.bitacora),
    )


class FuenteSinServidor:
    """Como un servidor caído: toda solicitud falla."""

    def obtener_version_cripta(self, cripta_id):
        raise RuntimeError("sin red")

    def obtener_version_catalogo(self):
        raise RuntimeError("sin red")


class ConCriptaDePrueba(unittest.TestCase):
    """Base de las pruebas que JUEGAN de verdad sobre la cripta de prueba.
    No tiene pruebas propias: solo la carpeta temporal y los ayudantes."""

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.carpeta = self._carpeta.name
        self.almacen = almacen_de_prueba(self.carpeta)

        # partida.log se escribe en la carpeta actual: la temporal.
        self._antes = os.getcwd()
        os.chdir(self.carpeta)

    def tearDown(self):
        os.chdir(self._antes)
        self._carpeta.cleanup()

    def sesion(self, comandos, semilla=7, cache_size=25):
        """Una ejecución del programa, con el main y el controlador DE
        VERDAD; solo la vista es falsa (escribe los comandos de la lista y
        al final "salir"). Devuelve el controlador."""
        args = Namespace(cripta="c-prueba", offline=True, jugador="Ana",
                         semilla=semilla, cache_size=cache_size, replay=None,
                         bench=False)

        with patch("crypta.main.AlmacenDisco", return_value=self.almacen):
            controlador, _, _, _ = programa.crear_partida(args)

        controlador.vista = Mock()
        controlador.vista.leer_comando.side_effect = list(comandos) + ["salir"]

        # Cada pantalla que se mostró: (reloj, ¿terminada?) EN ESE MOMENTO.
        self.pantallas = []
        controlador.vista.mostrar_estado.side_effect = (
            lambda partida: self.pantallas.append((partida.reloj, partida.terminada))
        )

        controlador.iniciar()
        controlador.gestor_contenido.cerrar()
        return controlador

    def jugar(self, comandos, semilla=7):
        return self.sesion(comandos, semilla).partida

    def reproducir(self, ruta="partida.log", fuente=None):
        if fuente is None:
            fuente = FuenteOffline(self.almacen)

        preparador = PreparadorReplay(fuente, self.almacen)

        try:
            return Reproductor(preparador).reproducir(ruta).partida
        finally:
            preparador.cerrar()

    def morir(self):
        return self.jugar(["mover N"] + ["esperar"] * 30)

    def escribir_log(self, nombre, comandos, version_cripta="v1",
                     version_catalogo="cat-1"):
        with open("partida.log", encoding="utf-8") as archivo:
            encabezado = archivo.read().split("---")[0]

        encabezado = encabezado.replace("version_cripta v1",
                                        f"version_cripta {version_cripta}")
        encabezado = encabezado.replace("version_catalogo cat-1",
                                        f"version_catalogo {version_catalogo}")

        with open(nombre, "w", encoding="utf-8") as archivo:
            archivo.write(encabezado + "---\n")
            for comando in comandos:
                archivo.write(comando + "\n")

        return nombre

    def correr_main(self, *argumentos):
        salida = io.StringIO()

        with patch("crypta.main.AlmacenDisco", return_value=self.almacen), \
                patch("crypta.main.VistaConsola",
                      side_effect=AssertionError("el replay creó la vista")), \
                patch.object(sys, "argv", ["crypta"] + list(argumentos)), \
                redirect_stdout(salida):
            codigo = programa.main()

        return codigo, salida.getvalue()


class TestReplay(ConCriptaDePrueba):

    def test_jugar_y_reproducir_da_la_misma_partida(self):
        # Una partida completa hasta la victoria. "atacar 1" ataca primero
        # a e-1 y, cuando muere, a e-2: el log guarda los ids reales.
        jugada = self.jugar(["recoger 2", "equipar", "recoger 1", "siguiente",
                             "usar", "mover N", "atacar 1", "atacar 1",
                             "atacar 1", "atacar 1", "recoger 1", "abrir N",
                             "mover N"])

        self.assertEqual(jugada.resultado, "victoria")
        self.assertEqual(foto(self.reproducir()), foto(jugada))

        with open("partida.log", encoding="utf-8") as archivo:
            comandos = archivo.read().split("---")[1].split()

        self.assertIn("e-2", comandos)

    def test_lo_invalido_no_llega_al_log_y_el_replay_coincide(self):
        jugada = self.jugar(["volar", "atacar 1", "abrir N", "mover O",
                             "recoger 9", "mover N", "esperar"])

        self.assertEqual(jugada.acciones_jugador, 2)
        self.assertEqual(foto(self.reproducir()), foto(jugada))

    def test_se_reproduce_hasta_la_derrota(self):
        jugada = self.morir()

        self.assertTrue(jugada.terminada)
        self.assertEqual(foto(self.reproducir()), foto(jugada))

    def test_una_accion_imposible_en_el_log_no_cae_el_programa(self):
        self.jugar([])
        ruta = self.escribir_log("malo.log", ["esperar", "atacar e-999"])

        with self.assertRaises(ReproduccionFallida) as contexto:
            self.reproducir(ruta)

        self.assertEqual(contexto.exception.numero, 2)

    def test_comandos_despues_del_final_se_reportan(self):
        self.morir()

        with open("partida.log", "a", encoding="utf-8") as archivo:
            archivo.write("esperar\n")

        with self.assertRaises(ReproduccionFallida) as contexto:
            self.reproducir()

        self.assertIn("terminado", str(contexto.exception))

    def test_una_version_que_no_se_tiene_es_incompatible(self):
        self.jugar(["esperar"])
        ruta = self.escribir_log("otra.log", ["esperar"], version_cripta="v9")

        with self.assertRaises(ReproduccionIncompatible):
            self.reproducir(ruta)

    def test_otro_catalogo_es_incompatible(self):
        self.jugar(["esperar"])
        ruta = self.escribir_log("otra.log", ["esperar"],
                                 version_catalogo="cat-9")

        with self.assertRaises(ReproduccionIncompatible):
            self.reproducir(ruta)

    def test_nueva_partida_usa_los_datos_de_la_cripta(self):
        # El juego y el replay la usan los dos: un error aquí no se vería
        # comparando jugar contra reproducir, por eso se prueba sola.
        partida = nueva_partida(DATOS_PRUEBA, Mock(), Mock(), 7, "Ana")
        jugador = partida.jugador

        self.assertFalse(partida.iniciada)
        self.assertEqual(partida.semilla, 7)
        self.assertEqual(jugador.nombre, "Ana")
        self.assertEqual((jugador.vida, jugador.vida_max, jugador.ataque,
                          jugador.defensa, jugador.velocidad),
                         (30, 30, 6, 2, 100))
        self.assertEqual(jugador.inventario.capacidad(), 5)
        self.assertEqual((partida.id_sala_inicial, partida.id_sala_salida,
                          partida.llave_salida), (1, 3, "itm_llave"))

    def test_sala_que_falta_en_la_copia_local_es_incompatible(self):
        self.jugar(["mover N", "esperar"])

        # La copia local pierde el contenido de la sala 2 (la versión es la
        # misma, pero está incompleta): no se puede reproducir fielmente.
        self.almacen.guardar_cripta("c-prueba", "v1", ESQUELETO_PRUEBA,
                                    CONTENIDOS_PRUEBA[:1],
                                    datos_generales=DATOS_PRUEBA)

        with self.assertRaises(ReproduccionIncompatible):
            self.reproducir()

    def test_sin_servidor_usa_la_copia_local(self):
        jugada = self.jugar(["mover N", "esperar"])

        reproducida = self.reproducir(fuente=FuenteSinServidor())

        self.assertEqual(foto(reproducida), foto(jugada))

    def test_main_replay_no_crea_la_vista(self):
        self.jugar(["mover N", "esperar"])

        codigo, salida = self.correr_main("--offline", "--replay", "partida.log")

        self.assertEqual(codigo, 0)
        self.assertIn("2 comandos repetidos", salida)

    def test_main_replay_incompatible_avisa_y_devuelve_1(self):
        self.jugar(["esperar"])
        ruta = self.escribir_log("otra.log", ["esperar"], version_cripta="v9")

        codigo, salida = self.correr_main("--offline", "--replay", ruta)

        self.assertEqual(codigo, 1)
        self.assertIn("no se puede garantizar", salida.lower())

    def test_main_replay_con_accion_imposible_devuelve_1(self):
        self.jugar([])
        ruta = self.escribir_log("malo.log", ["atacar e-999"])

        codigo, salida = self.correr_main("--offline", "--replay", ruta)

        self.assertEqual(codigo, 1)
        self.assertIn("comando 1", salida)


class TestArranqueConDatosInvalidos(ConCriptaDePrueba):
    """FR-010 (tarea T008): una cripta con una salida inválida no se juega.
    `main` muestra el mensaje de DatosInvalidos y termina sin crear la
    Partida ni la vista."""

    def setUp(self):
        super().setUp()

        esqueleto = copy.deepcopy(ESQUELETO_PRUEBA)
        esqueleto[0]["salidas"]["N"]["costo"] = 0

        self.almacen = AlmacenDisco(os.path.join(self.carpeta, "invalida"))
        self.almacen.guardar_catalogo("cat-1", FICHAS_PRUEBA)
        self.almacen.guardar_cripta("c-prueba", "v1", esqueleto,
                                    CONTENIDOS_PRUEBA,
                                    datos_generales=DATOS_PRUEBA)

    def test_fr010_costo_cero_no_inicia_la_partida(self):
        """FR-010: costo 0 → mensaje de DatosInvalidos, código 1, sin
        Partida, sin vista y sin partida.log."""
        salida = io.StringIO()
        argumentos = ["crypta", "--offline", "--cripta", "c-prueba",
                      "--semilla", "7", "--jugador", "Ana"]

        with patch("crypta.main.AlmacenDisco", return_value=self.almacen), \
                patch("crypta.main.VistaConsola",
                      side_effect=AssertionError("se creó la vista")), \
                patch("crypta.main.nueva_partida",
                      side_effect=AssertionError("se creó la partida")), \
                patch.object(sys, "argv", argumentos), \
                redirect_stdout(salida):
            codigo = programa.main()

        self.assertEqual(codigo, 1)
        self.assertIn("La salida N de la sala 1 tiene un costo inválido: 0",
                      salida.getvalue())
        self.assertFalse(os.path.exists("partida.log"))


# ======================================================================
# CORRECCIÓN 3: el log al guardar y al cargar (§4.10 + §4.11)
# ======================================================================
# Al guardar se copia el log junto al guardado; al cargar, esa copia
# vuelve a ser el log. Lo jugado entre guardar y cargar desaparece del
# log, igual que desaparece de la partida.

def leer(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.read()


class TestGuardarYCargar(ConCriptaDePrueba):

    def test_guardar_deja_una_copia_del_log(self):
        controlador = self.sesion(["recoger 2", "equipar", "guardar"])

        self.assertEqual(leer("partida.cripta.log"), leer("partida.log"))
        self.assertIn("equipar", leer("partida.cripta.log"))

    def test_guardar_jugar_cargar_y_reproducir(self):
        # El caso que fallaba: después de cargar, el replay daba otra partida.
        jugada = self.jugar(["recoger 2", "equipar", "guardar", "mover N",
                             "esperar", "cargar", "recoger 1", "mover N",
                             "esperar"])

        self.assertNotIn("esperar\nrecoger", leer("partida.log"))
        self.assertEqual(foto(self.reproducir()), foto(jugada))

    def test_cargar_en_otra_ejecucion_del_programa(self):
        # Primera ejecución: semilla 7, guarda y sigue.
        self.jugar(["recoger 2", "guardar", "mover N", "esperar"], semilla=7)

        # Segunda ejecución: otra semilla; carga y juega.
        jugada = self.jugar(["cargar", "mover N", "esperar"], semilla=99)

        self.assertEqual(jugada.semilla, 7)
        self.assertIn("semilla 7", leer("partida.log"))
        self.assertEqual(foto(self.reproducir()), foto(jugada))

    def test_cargar_varias_veces(self):
        jugada = self.jugar(["recoger 2", "guardar", "mover N", "cargar",
                             "esperar", "cargar", "equipar", "guardar",
                             "mover N", "atacar 1", "cargar", "mover N",
                             "esperar"])

        self.assertEqual(foto(self.reproducir()), foto(jugada))

    def test_sin_el_log_guardado_no_se_carga(self):
        controlador = self.sesion(["guardar", "esperar"])
        os.remove("partida.cripta.log")
        log_antes = leer("partida.log")
        reloj_antes = controlador.partida.reloj

        self.assertFalse(controlador.procesar_comando("cargar"))

        self.assertEqual(controlador.partida.reloj, reloj_antes)
        self.assertEqual(leer("partida.log"), log_antes)
        self.assertIn("partida.cripta.log",
                      str(controlador.vista.mostrar_error.call_args))

    def test_un_log_de_otra_partida_no_se_carga(self):
        controlador = self.sesion(["guardar", "esperar"])

        with open("partida.cripta.log", "w", encoding="utf-8") as archivo:
            archivo.write(leer("partida.log").replace("semilla 7", "semilla 8"))

        reloj_antes = controlador.partida.reloj

        self.assertFalse(controlador.procesar_comando("cargar"))
        self.assertEqual(controlador.partida.reloj, reloj_antes)

    def test_guardar_y_cargar_no_se_anotan(self):
        self.jugar(["esperar", "guardar", "cargar", "esperar"])

        comandos = leer("partida.log").split("---")[1].split()

        self.assertEqual(comandos, ["esperar", "esperar"])


# ======================================================================
# CORRECCIÓN 4: el final de la partida y la tabla de puntajes (§2.12)
# ======================================================================

GANAR = ["recoger 2", "equipar", "recoger 1", "siguiente", "usar", "mover N",
         "atacar 1", "atacar 1", "atacar 1", "atacar 1", "recoger 1",
         "abrir N", "mover N"]


class TestFinDePartida(ConCriptaDePrueba):

    def tabla(self):
        # Se lee DEL DISCO: así se prueba también que quedó guardada.
        return TablaPuntajes("puntajes.txt")

    def test_al_morir_se_muestra_la_ultima_pantalla(self):
        partida = self.morir()

        # La última pantalla mostrada ya es la de la partida terminada,
        # con el reloj del final (antes no se mostraba nunca).
        self.assertEqual(self.pantallas[-1], (partida.reloj, True))

    def test_al_morir_se_registra_la_derrota(self):
        partida = self.morir()
        tabla = self.tabla()

        self.assertEqual(len(tabla), 1)
        puntaje = tabla.ranking().obtener(0)
        self.assertEqual(
            (puntaje.jugador, puntaje.cripta_id, puntaje.version_cripta,
             puntaje.resultado, puntaje.tiempo, puntaje.acciones),
            ("Ana", "c-prueba", "v1", "derrota", partida.reloj,
             partida.acciones_jugador))

    def test_al_ganar_se_registra_la_victoria(self):
        partida = self.jugar(GANAR)
        puntaje = self.tabla().ranking().obtener(0)

        self.assertEqual(self.pantallas[-1], (partida.reloj, True))
        self.assertEqual((puntaje.resultado, puntaje.enemigos),
                         ("victoria", 2))

    def test_salir_sin_terminar_no_registra(self):
        controlador = self.sesion(["mover N", "esperar"])

        self.assertEqual(len(self.tabla()), 0)
        controlador.vista.mostrar_puntajes.assert_not_called()
        controlador.vista.mostrar_error.assert_not_called()

    def pantalla_final(self, partida):
        salida = io.StringIO()
        with redirect_stdout(salida):
            VistaConsola().mostrar_estado(partida)
        return salida.getvalue()

    def test_la_pantalla_final_dice_como_termino(self):
        self.assertIn("VICTORIA", self.pantalla_final(self.jugar(GANAR)))
        self.assertIn("DERROTA", self.pantalla_final(self.morir()))

    def test_se_muestra_el_ranking_con_esta_partida(self):
        controlador = self.sesion(["mover N"] + ["esperar"] * 30)

        ranking, actual = controlador.vista.mostrar_puntajes.call_args[0]
        self.assertEqual(len(ranking), 1)
        self.assertIs(ranking.obtener(0), actual)

    def test_las_partidas_se_acumulan_en_el_archivo(self):
        self.morir()
        self.jugar(GANAR)

        ranking = self.tabla().ranking()
        # La victoria va primero aunque se jugó después.
        self.assertEqual([ranking.obtener(i).resultado for i in range(2)],
                         ["victoria", "derrota"])

    def test_comando_puntajes_no_se_anota_ni_gasta_tiempo(self):
        controlador = self.sesion(["puntajes", "esperar"])

        controlador.vista.mostrar_puntajes.assert_called_once()
        self.assertEqual(leer("partida.log").split("---")[1].split(),
                         ["esperar"])
        self.assertEqual(controlador.partida.acciones_jugador, 1)

    def test_el_replay_no_registra_otra_vez(self):
        self.morir()

        codigo, _ = self.correr_main("--offline", "--replay", "partida.log")

        self.assertEqual(codigo, 0)
        self.assertEqual(len(self.tabla()), 1)

    def test_una_tabla_danada_no_impide_jugar(self):
        with open("puntajes.txt", "w", encoding="utf-8") as archivo:
            archivo.write("esto no es una tabla\n")

        with redirect_stdout(io.StringIO()) as salida:
            partida = self.morir()

        self.assertTrue(partida.terminada)
        self.assertIn("Aviso", salida.getvalue())
        self.assertEqual(leer("puntajes.txt"), "esto no es una tabla\n")


class TestVistaPuntajes(unittest.TestCase):

    def mostrar(self, ranking, actual=None):
        salida = io.StringIO()
        with redirect_stdout(salida):
            VistaConsola().mostrar_puntajes(ranking, actual)
        return salida.getvalue()

    def test_marca_la_partida_actual(self):
        tabla = TablaPuntajes()
        tabla.registrar(Puntaje("Ana", "c", "v", "derrota", 3, 0, 200))
        actual = Puntaje("Beto", "c", "v", "victoria", 9, 2, 700)
        tabla.registrar(actual)

        texto = self.mostrar(tabla.ranking(), actual)

        self.assertLess(texto.index("Beto"), texto.index("Ana"))
        self.assertIn("Beto", [l for l in texto.splitlines() if "<-" in l][0])

    def test_tabla_vacia(self):
        self.assertIn("Todavía no hay", self.mostrar(TablaPuntajes().ranking()))


# ======================================================================
# CORRECCIÓN 5: el presupuesto de red y el reporte final (§5.1)
# ======================================================================

class Respuesta:
    """Lo mínimo de una respuesta de requests."""

    def __init__(self, datos, codigo=200):
        self.status_code = codigo
        self._datos = datos

    def json(self):
        return self._datos


class ServidorFalso:
    """Hace de servidor para FuenteHTTP (se pone en lugar de requests.get)
    con la cripta de prueba. Anota cada solicitud y, como el de verdad,
    rechaza lotes de más de 10."""

    def __init__(self, presupuesto=9):
        self.pedidos = []
        self.datos = dict(DATOS_PRUEBA, presupuesto_solicitudes=presupuesto)

    def get(self, url, headers=None, timeout=None):
        ruta = url.split("/v1", 1)[1]
        self.pedidos.append(ruta)
        camino, _, consulta = ruta.partition("?")
        valor = consulta.partition("=")[2]

        if camino == "/criptas":
            return Respuesta({"criptas": [
                {"id": "c-prueba", "nombre": "Prueba", "salas": 3,
                 "dificultad": 1},
                {"id": "c-otra", "nombre": "Otra", "salas": 60,
                 "dificultad": 2}]})
        if camino == "/criptas/c-prueba":
            return Respuesta(self.datos)
        if camino == "/criptas/c-prueba/salas":
            return Respuesta({"pagina": 1, "total_paginas": 1,
                              "salas": ESQUELETO_PRUEBA})
        if camino == "/criptas/c-prueba/contenido":
            ids = [int(i) for i in valor.split(",")]
            assert len(ids) <= 10
            return Respuesta({"contenido": [c for i in ids
                                            for c in CONTENIDOS_PRUEBA
                                            if c["sala"] == i]})
        if camino == "/catalogo":
            ids = valor.split(",")
            assert len(ids) <= 10
            return Respuesta({"entidades": [FICHAS_PRUEBA[i] for i in ids]})
        if camino == "/catalogo/version":
            return Respuesta({"version": "cat-1"})
        if camino == "/criptas/c-prueba/version":
            return Respuesta({"id": "c-prueba", "version": "v1"})
        raise AssertionError(f"ruta desconocida: {ruta}")

    def de_catalogo(self):
        return [p for p in self.pedidos if p.startswith("/catalogo?")]


class TestPresupuestoFuenteHTTP(unittest.TestCase):

    def test_no_pasa_del_presupuesto(self):
        fuente = FuenteHTTP()
        fuente.fijar_presupuesto(2)

        with patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                   return_value=Respuesta({"version": "x"})) as get:
            fuente.obtener_version_catalogo()
            fuente.obtener_version_catalogo()

            with self.assertRaises(PresupuestoAgotado):
                fuente.obtener_version_catalogo()

        self.assertEqual(get.call_count, 2)       # la tercera no se envió
        self.assertEqual(fuente.cantidad_solicitudes(), 2)
        self.assertEqual(fuente.solicitudes_restantes(), 0)

    def test_un_reintento_por_429_tambien_cuenta(self):
        fuente = FuenteHTTP()
        fuente.fijar_presupuesto(5)
        respuestas = [Respuesta({"reintentar_en": 0}, 429),
                      Respuesta({"version": "x"})]

        with patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                   side_effect=respuestas), \
                patch("crypta.Adaptadores.FuenteHTTP.time.sleep"), \
                redirect_stdout(io.StringIO()):
            fuente.obtener_version_catalogo()

        self.assertEqual(fuente.cantidad_solicitudes(), 2)
        self.assertEqual(fuente.solicitudes_restantes(), 3)

    def test_antes_de_conocer_la_cripta_no_hay_limite(self):
        self.assertIsNone(FuenteHTTP().solicitudes_restantes())

    def test_la_fuente_sin_conexion_no_cuenta_ni_tiene_limite(self):
        fuente = FuenteOffline(AlmacenDisco(tempfile.gettempdir()))
        fuente.fijar_presupuesto(3)

        self.assertEqual(fuente.cantidad_solicitudes(), 0)
        self.assertIsNone(fuente.solicitudes_restantes())


class FuenteContada:
    """Fuente en memoria para GestorContenido: cuenta lo que se pide y
    puede fallar a propósito."""

    def __init__(self, restantes=None, falla_contenido=0):
        self.restantes = restantes
        self.falla_contenido = falla_contenido    # cuántas veces falla
        self.contenido = []
        self.catalogo = []

    def solicitudes_restantes(self):
        return self.restantes

    def obtener_contenido(self, cripta_id, salas):
        ids = list(salas)
        self.contenido.append(ids)
        if self.falla_contenido > 0:
            self.falla_contenido -= 1
            raise RuntimeError("sin red")
        return {"contenido": [c for c in CONTENIDOS_PRUEBA if c["sala"] in ids]}

    def obtener_catalogo(self, ids):
        ids = list(ids)
        self.catalogo.append(ids)
        return {"entidades": [FICHAS_PRUEBA[i] for i in ids]}


def mapa_de_prueba():
    mapa = Mapa()
    mapa.cargar_desde_json(ESQUELETO_PRUEBA)
    return mapa


class TestGestorContenidoYPresupuesto(unittest.TestCase):

    def gestor(self, fuente, con_repositorio=False, mapa=None):
        repositorio = RepositorioFichas(fuente) if con_repositorio else None
        gestor = GestorContenido(fuente, mapa or mapa_de_prueba(), "c-prueba",
                                 repositorio)
        self.addCleanup(gestor.cerrar)
        return gestor, repositorio

    def test_la_precarga_no_gasta_la_reserva(self):
        fuente = FuenteContada(restantes=2)
        gestor, _ = self.gestor(fuente)

        self.assertIsNone(gestor.precargar_async(1))
        gestor.cerrar()
        self.assertEqual(fuente.contenido, [])

    def test_con_presupuesto_si_precarga(self):
        fuente = FuenteContada(restantes=3)
        gestor, _ = self.gestor(fuente)

        self.assertIsNotNone(gestor.precargar_async(1))
        gestor.cerrar()
        self.assertEqual(fuente.contenido, [[1, 2, 3]])

    def test_una_precarga_fallida_no_detiene_el_juego(self):
        fuente = FuenteContada(falla_contenido=1)
        gestor, _ = self.gestor(fuente)

        gestor.precargar_async(1)       # esta falla (en el otro hilo)
        gestor.cerrar()                 # espera a que termine
        gestor.procesar_pendientes()    # antes: el error salía en cada turno
        gestor.procesar_pendientes()

        sala = gestor.garantizar_sala(2)   # se pide sola y sí llega

        self.assertTrue(sala.contenido_cargado())
        self.assertEqual(fuente.contenido, [[1, 2, 3], [2]])

    def test_garantizar_tras_una_precarga_fallida(self):
        fuente = FuenteContada(falla_contenido=1)
        gestor, _ = self.gestor(fuente)

        gestor.precargar_async(1)
        sala = gestor.garantizar_sala(1)   # esperaba esa precarga, que falló

        self.assertTrue(sala.contenido_cargado())

    def test_las_fichas_llegan_en_un_solo_lote(self):
        fuente = FuenteContada()
        gestor, repositorio = self.gestor(fuente, con_repositorio=True)

        gestor.precargar_desde(1)          # contenido de las 3 salas
        gestor.garantizar_sala(2)

        # Un solo pedido de catálogo para todas las fichas de las 3 salas.
        self.assertEqual(len(fuente.catalogo), 1)
        self.assertEqual(sorted(fuente.catalogo[0]), sorted(FICHAS_PRUEBA))

        repositorio.obtener_ficha("ent_rata")
        gestor.garantizar_sala(1)
        self.assertEqual(len(fuente.catalogo), 1)   # ya no se pidió nada


    def test_garantizar_completa_las_fichas_de_una_sala_ya_cargada(self):
        # Como al empezar desde la copia local: el contenido ya está en el
        # mapa, pero sus fichas todavía no se pidieron.
        mapa = mapa_de_prueba()
        mapa.asignar_contenidos(CONTENIDOS_PRUEBA)
        fuente = FuenteContada()
        gestor, _ = self.gestor(fuente, con_repositorio=True, mapa=mapa)

        gestor.garantizar_sala(2)

        self.assertEqual(fuente.contenido, [])
        self.assertEqual([sorted(lote) for lote in fuente.catalogo],
                         [["ent_rata", "itm_llave"]])


class TestAciertosYFallos(unittest.TestCase):

    def test_cuenta_aciertos_y_fallos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            almacen = AlmacenDisco(carpeta)
            almacen.guardar_catalogo("cat-1", {"itm_daga": FICHAS_PRUEBA["itm_daga"]})
            fuente = FuenteContada()
            repositorio = RepositorioFichas(fuente, almacen, "cat-1")

            repositorio.obtener_ficha("itm_daga")     # del disco
            repositorio.obtener_ficha("itm_daga")     # de memoria
            repositorio.obtener_ficha("ent_rata")     # por red

        self.assertEqual((repositorio.aciertos, repositorio.fallos_disco,
                          repositorio.fallos_red), (1, 1, 1))


class TestPresupuestoEnElJuego(ConCriptaDePrueba):
    """Partidas EN LÍNEA (FuenteHTTP de verdad, con el servidor falso) y
    con la caché vacía: lo más caro que puede pasar."""

    def jugar_en_linea(self, comandos, presupuesto=9):
        servidor = ServidorFalso(presupuesto)
        vista = Mock()
        vista.leer_comando.side_effect = list(comandos) + ["salir"]
        almacen = AlmacenDisco(os.path.join(self.carpeta, "cache_vacia"))
        argumentos = ["crypta", "--cripta", "c-prueba", "--jugador", "Ana",
                      "--semilla", "7"]

        with patch("crypta.main.AlmacenDisco", return_value=almacen), \
                patch("crypta.main.VistaConsola", return_value=vista), \
                patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                      side_effect=servidor.get), \
                patch.object(sys, "argv", argumentos), \
                redirect_stdout(io.StringIO()):
            codigo = programa.main()

        return codigo, servidor, vista

    def test_una_partida_completa_en_frio_cabe_en_el_presupuesto(self):
        codigo, servidor, vista = self.jugar_en_linea(GANAR)

        self.assertEqual(codigo, 0)
        # general, esqueleto, versión del catálogo, UN lote de contenido
        # (las 3 salas) y UN lote de fichas (las 4).
        self.assertEqual(len(servidor.pedidos), 5)
        self.assertEqual(len(servidor.de_catalogo()), 1)

    def test_el_reporte_dice_lo_que_se_gasto(self):
        _, servidor, vista = self.jugar_en_linea(GANAR)

        solicitudes, presupuesto, aciertos, disco, red = (
            vista.mostrar_reporte.call_args[0])

        self.assertEqual((solicitudes, presupuesto),
                         (len(servidor.pedidos), 9))
        self.assertEqual(red, len(FICHAS_PRUEBA))   # cada ficha, una vez
        self.assertGreater(aciertos, 0)

    def test_sin_presupuesto_la_accion_no_se_hace_y_el_juego_sigue(self):
        # Con 5 solo alcanza para la sala inicial: entrar a la 2 no se puede.
        codigo, servidor, vista = self.jugar_en_linea(
            ["mover N", "recoger 1", "mover N"], presupuesto=5)

        self.assertEqual(codigo, 0)
        self.assertLessEqual(len(servidor.pedidos), 5)
        errores = [str(c) for c in vista.mostrar_error.call_args_list]
        self.assertEqual(len(errores), 2)
        self.assertIn("presupuesto", errores[0])
        # Ni "mover N" quedó en el log; "recoger 1" sí.
        self.assertEqual(leer("partida.log").split("---")[1].split(),
                         ["recoger", "0"])
        vista.mostrar_reporte.assert_called_once()

    def test_al_cargar_el_gestor_nuevo_tambien_pide_fichas_en_lote(self):
        controlador = self.sesion(["guardar", "cargar"])

        self.assertIs(controlador.gestor_contenido._repositorio,
                      controlador.repositorio_fichas)

    def test_en_modo_sin_conexion_no_se_gasta_red(self):
        controlador = self.sesion(["mover N", "esperar"])
        repositorio = controlador.repositorio_fichas

        self.assertEqual(controlador.gestor_contenido._fuente.cantidad_solicitudes(), 0)
        self.assertEqual(repositorio.fallos_red, 0)


# ======================================================================
# CORRECCIÓN 6: las fichas en uso no se desalojan (§4.4)
# ======================================================================

class TestRecorrerPendientes(unittest.TestCase):

    def test_solo_los_que_todavia_van_a_ocurrir(self):
        agenda = Agenda()
        a = agenda.programar(10, "a")
        b = agenda.programar(20, "b")
        c = agenda.programar(30, "c")
        agenda.cancelar(b)
        agenda.siguiente()                       # ocurre a

        self.assertEqual(list(agenda.recorrer_pendientes()), [c])
        self.assertEqual(len(agenda), 1)         # mirar no cambia nada


def partida_falsa(eventos=(), inventario=(), suelo=(), trampas=(), enemigos=()):
    """Lo mínimo que FichasEnUso lee de una partida."""
    sala = Mock()
    sala.cantidad_objetos.return_value = len(suelo)
    sala.objeto_en.side_effect = lambda i: suelo[i]
    sala.cantidad_trampas.return_value = len(trampas)
    sala.trampa_en.side_effect = lambda i: Mock(tipo=trampas[i])
    sala.cantidad_enemigos.return_value = len(enemigos)
    sala.enemigo_en.side_effect = lambda i: Mock(tipo=enemigos[i])

    partida = Mock()
    partida.sala_actual.return_value = sala
    partida.jugador.inventario.orden_real.return_value = [
        {"id": i} for i in inventario]
    partida.agenda.recorrer_pendientes.side_effect = lambda: iter(eventos)
    return partida


class TestFichasEnUso(unittest.TestCase):

    def setUp(self):
        self.repositorio = Mock()
        self.fichas = FichasEnUso(self.repositorio)

    def marcadas(self):
        return sorted(c[0][0] for c in self.repositorio.marcar_en_uso.call_args_list)

    def liberadas(self):
        return sorted(c[0][0] for c in self.repositorio.liberar_uso.call_args_list)

    def test_marca_todo_lo_que_pide_el_enunciado(self):
        despierto = Mock(tipo=TURNO_ENEMIGO, objetivo=Mock(tipo="ent_lejos"))
        otro_evento = Mock(tipo="cierre_puerta", objetivo=Mock(tipo="no"))

        self.fichas.actualizar(partida_falsa(
            eventos=[despierto, otro_evento], inventario=["itm_daga"],
            suelo=["itm_llave"], trampas=["trp_dardos"],
            enemigos=["ent_rata", "ent_rata"]))

        # Cada id una sola vez, aunque haya dos ratas.
        self.assertEqual(self.marcadas(), ["ent_lejos", "ent_rata", "itm_daga",
                                           "itm_llave", "trp_dardos"])

    def test_libera_lo_que_ya_no_se_usa_y_no_repite_marcas(self):
        self.fichas.actualizar(partida_falsa(inventario=["itm_daga"],
                                             suelo=["itm_llave"]))
        self.fichas.actualizar(partida_falsa(inventario=["itm_daga"]))

        self.assertEqual(self.marcadas(), ["itm_daga", "itm_llave"])
        self.assertEqual(self.liberadas(), ["itm_llave"])
        self.assertTrue(self.fichas.esta_marcada("itm_daga"))
        self.assertFalse(self.fichas.esta_marcada("itm_llave"))


class TestFichasEnUsoEnElJuego(ConCriptaDePrueba):
    """Con el juego de verdad y una caché de UNA sola ficha: si no fuera
    por las fichas en uso, cada ficha nueva desalojaría a la anterior."""

    def en_uso(self, controlador, *ids):
        repositorio = controlador.repositorio_fichas
        return [repositorio.esta_en_uso(i) for i in ids]

    def test_al_empezar_ya_esta_en_uso_lo_de_la_sala_inicial(self):
        controlador = self.sesion([])

        self.assertEqual(self.en_uso(controlador, "itm_antorcha", "itm_daga",
                                     "ent_rata"),
                         [True, True, False])

    def test_lo_que_se_usa_queda_en_memoria_aunque_no_quepa(self):
        controlador = self.sesion(["recoger 2", "mover N"], cache_size=1)
        repositorio = controlador.repositorio_fichas

        # Daga en el inventario; ratas y llave en la sala 2: en uso.
        # La antorcha quedó en el suelo de la sala 1: ya no.
        self.assertEqual(
            self.en_uso(controlador, "itm_daga", "ent_rata", "itm_llave",
                        "itm_antorcha"),
            [True, True, True, False])
        self.assertTrue(repositorio.esta_en_memoria("itm_daga"))
        self.assertTrue(repositorio.esta_en_memoria("ent_rata"))

    def test_al_morir_los_enemigos_su_ficha_se_libera(self):
        controlador = self.sesion(GANAR, cache_size=1)

        self.assertEqual(controlador.partida.resultado, "victoria")
        self.assertEqual(
            self.en_uso(controlador, "ent_rata", "itm_daga", "itm_llave"),
            [False, True, True])

    def test_al_cargar_se_recalcula(self):
        # Se guarda en la sala 1; después se entra a la 2 (ratas despiertas)
        # y se carga: las ratas vuelven a estar dormidas y lejos.
        controlador = self.sesion(["recoger 2", "guardar", "mover N", "cargar"])

        self.assertEqual(controlador.partida.jugador.sala_actual, 1)
        self.assertEqual(self.en_uso(controlador, "ent_rata", "itm_daga"),
                         [False, True])


# ======================================================================
# CORRECCIÓN 7: el modo sin conexión (--offline, §3)
# ======================================================================
# No hay paquete del curso: --offline usa la copia local que el programa
# guarda al jugar con conexión (ver FuenteOffline.py).

class TestModoSinConexion(ConCriptaDePrueba):

    def test_no_usa_la_red(self):
        with patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                   side_effect=AssertionError("usó la red")) as get:
            partida = self.jugar(GANAR)

        self.assertEqual(partida.resultado, "victoria")
        get.assert_not_called()

    def test_una_sala_sin_copia_local_no_termina_la_partida(self):
        # La copia local solo tiene el contenido de la sala 1.
        self.almacen.guardar_cripta("c-prueba", "v1", ESQUELETO_PRUEBA,
                                    CONTENIDOS_PRUEBA[:1],
                                    datos_generales=DATOS_PRUEBA)

        controlador = self.sesion(["mover N", "recoger 1", "mover N"])
        errores = [c[0][0] for c in controlador.vista.mostrar_error.call_args_list]

        self.assertEqual(len(errores), 2)
        self.assertIn("sin conexión", errores[0])
        self.assertTrue(errores[0].endswith("con conexión. La acción no se hizo."))
        self.assertEqual(controlador.partida.jugador.sala_actual, 1)
        self.assertFalse(controlador.partida.terminada)
        # Se siguió jugando: "recoger 1" sí se hizo y quedó en el log.
        self.assertEqual(leer("partida.log").split("---")[1].split(),
                         ["recoger", "0"])

    def test_sin_copia_local_lo_dice_y_termina_bien(self):
        vacio = AlmacenDisco(os.path.join(self.carpeta, "otra_cache"))
        salida = io.StringIO()
        argumentos = ["crypta", "--offline", "--cripta", "c-prueba"]

        with patch("crypta.main.AlmacenDisco", return_value=vacio), \
                patch.object(sys, "argv", argumentos), \
                redirect_stdout(salida):
            codigo = programa.main()

        self.assertEqual(codigo, 1)
        self.assertIn("no tiene copia local", salida.getvalue())


# ======================================================================
# CORRECCIÓN 8: detalles finales
# ======================================================================

class TestDetallesFinales(ConCriptaDePrueba):

    def pantalla(self, partida):
        salida = io.StringIO()
        with redirect_stdout(salida):
            VistaConsola().mostrar_estado(partida)
        return salida.getvalue()

    def correr(self, vista, en_linea=False):
        """El main de verdad con una vista falsa; en línea usa el servidor
        falso y una caché vacía."""
        servidor = ServidorFalso()
        almacen = (AlmacenDisco(os.path.join(self.carpeta, "cache_vacia"))
                   if en_linea else self.almacen)
        argumentos = ["crypta", "--cripta", "c-prueba", "--semilla", "7"]
        if not en_linea:
            argumentos.append("--offline")
        salida = io.StringIO()

        with patch("crypta.main.AlmacenDisco", return_value=almacen), \
                patch("crypta.main.VistaConsola", return_value=vista), \
                patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                      side_effect=servidor.get), \
                patch.object(sys, "argv", argumentos), \
                redirect_stdout(salida):
            codigo = programa.main()

        return codigo, salida.getvalue(), almacen

    def test_la_pantalla_muestra_las_estadisticas(self):
        partida = self.jugar(["recoger 2", "equipar"])

        texto = self.pantalla(partida)

        # Ataque 6 + 3 de la daga equipada.
        self.assertIn("Ataque: 9", texto)
        self.assertIn("Defensa: 2", texto)
        self.assertIn("Velocidad: 100", texto)

    def test_la_pantalla_dice_que_llave_pide_una_puerta(self):
        partida = self.jugar(["mover N"])

        texto = self.pantalla(partida)

        self.assertIn("N: sala 3 (Cerrada, necesita itm_llave)", texto)
        self.assertIn("Vida: 12/12", texto)

    def test_ctrl_c_fuera_de_la_lectura_termina_ordenado(self):
        vista = Mock()
        vista.mostrar_estado.side_effect = KeyboardInterrupt

        codigo, texto, _ = self.correr(vista)

        self.assertEqual(codigo, 0)
        self.assertIn("interrumpida", texto)
        vista.mostrar_reporte.assert_called_once()

    def test_ctrl_c_en_linea_igual_guarda_la_copia_local(self):
        vista = Mock()
        vista.leer_comando.side_effect = ["mover N"]
        vista.mostrar_estado.side_effect = [None, KeyboardInterrupt]

        _, _, almacen = self.correr(vista, en_linea=True)

        self.assertIsNotNone(almacen.cargar_cripta("c-prueba", "v1"))

    def test_al_terminar_dice_como_repetir_la_partida(self):
        vista = Mock()
        vista.leer_comando.side_effect = ["esperar", "salir"]

        _, texto, _ = self.correr(vista)

        self.assertIn("--offline --replay partida.log", texto)


# ======================================================================
# CORRECCIÓN 9: --listar, para elegir otra cripta (§10.2)
# ======================================================================

class TestListarCriptas(ConCriptaDePrueba):

    def listar(self, *extra, almacen=None):
        servidor = ServidorFalso()
        salida = io.StringIO()

        with patch("crypta.main.AlmacenDisco", return_value=almacen or self.almacen), \
                patch("crypta.main.VistaConsola",
                      side_effect=AssertionError("--listar creó la vista")), \
                patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                      side_effect=servidor.get), \
                patch.object(sys, "argv", ["crypta", "--listar"] + list(extra)), \
                redirect_stdout(salida):
            codigo = programa.main()

        return codigo, salida.getvalue(), servidor

    def test_en_linea_muestra_las_del_servidor(self):
        codigo, texto, servidor = self.listar()

        self.assertEqual(codigo, 0)
        self.assertIn("c-prueba", texto)
        self.assertIn("c-otra", texto)
        self.assertIn("60 salas", texto)
        self.assertEqual(servidor.pedidos, ["/criptas"])

    def test_sin_conexion_muestra_las_que_tienen_copia_local(self):
        codigo, texto, servidor = self.listar("--offline")

        self.assertEqual(codigo, 0)
        self.assertIn("c-prueba", texto)
        self.assertNotIn("c-otra", texto)
        self.assertIn("3 salas", texto)
        self.assertEqual(servidor.pedidos, [])

    def test_sin_conexion_y_sin_copias_lo_dice(self):
        vacio = AlmacenDisco(os.path.join(self.carpeta, "nada"))

        codigo, texto, _ = self.listar("--offline", almacen=vacio)

        self.assertEqual(codigo, 0)
        self.assertIn("No hay criptas disponibles", texto)

    def test_criptas_guardadas_no_cuenta_el_catalogo(self):
        self.assertEqual(self.almacen.criptas_guardadas(), ["c-prueba"])


if __name__ == "__main__":
    unittest.main()
