"""Niebla de guerra en la partida (capacidad 002, fase 2).

- T006 `TestConocimientoEnPartida`: FR-201 a FR-206 (HU1-1 a HU1-5).
- T007 `TestBitacoraNiebla`: FR-205, FR-208 (HU1-6).
- T008 `TestVistaNiebla`: FR-207, FR-209 (HU1-7, HU1-10).
- T009 `TestAntorcha`: FR-212 a FR-215 (HU2-1 a HU2-4).

Cada prueba arma su cripta con `tests/ayudas_cripta.py`; ninguna lee
`cache/`.
"""

import io
import tempfile
import unittest
from contextlib import redirect_stdout

from crypta.Modelo.MapaConocido import AVISTADA, DESCONOCIDA, EXPLORADA
from crypta.Modelo.Partida import REARME_TRAMPA, REGENERACION
from crypta.Modelo.Puerta import ABIERTA, CERRADA
from tests.ayudas_cripta import (
    FuenteContadora,
    catalogo,
    contenido,
    controlador_sintetico,
    datos_generales,
    ficha_errante,
    nuevo_jugador,
    partida_sintetica,
    sala,
    salida,
)


FICHA_TRAMPA = {"id": "trp_aguja", "clase": "trampa", "nombre": "Aguja",
                "daño": 1, "rearme": 250}
FICHA_ANTORCHA = {"id": "itm_antorcha", "clase": "antorcha",
                  "nombre": "Antorcha", "peso": 1, "valor": 1,
                  "duracion": 400}


def estados(partida, ids):
    return [partida.conocimiento.estado(partida.mapa.obtener_sala(i))
            for i in ids]


def puerta(partida, id_sala, direccion):
    return partida.mapa.obtener_sala(id_sala).obtener_puerta(direccion)


def foto_conocimiento(partida):
    """Estados de todas las salas y `recordada` de todas las salidas."""
    salas = partida.mapa.obtener_todas()
    resultado = []

    for i in range(len(salas)):
        s = salas.obtener(i)
        resultado.append((s.id, partida.conocimiento.estado(s)))
        puertas = s.puertas()

        for j in range(len(puertas)):
            resultado.append(puertas.obtener(j).estado.recordada)

    return resultado


def texto_estado(partida):
    from crypta.Vista.VistaConsola import VistaConsola

    salida_capturada = io.StringIO()

    with redirect_stdout(salida_capturada):
        VistaConsola().mostrar_estado(partida)

    return salida_capturada.getvalue()


def seccion_salidas(texto):
    """Las líneas de SALIDAS de `mostrar_estado`."""
    lineas = texto.splitlines()
    inicio = lineas.index("SALIDAS") + 1
    fin = lineas.index("ENEMIGOS")
    return [linea.strip() for linea in lineas[inicio:fin] if linea.strip()]


# ---------------------------------------------------------------------------
# T006
# ---------------------------------------------------------------------------

def esqueleto_hu1():
    """1 —E→ 2, 1 —S→ 3; 2 —S→ 4 (la puerta 2–4); 3 —E→ 4; 5 —N→ 1 sin
    vuelta."""
    return [
        sala(1, {"E": salida(2), "S": salida(3)}),
        sala(2, {"O": salida(1), "S": salida(4)}),
        sala(3, {"N": salida(1), "E": salida(4)}),
        sala(4, {"N": salida(2), "O": salida(3)}),
        sala(5, {"N": salida(1)}),
    ]


class TestConocimientoEnPartida(unittest.TestCase):
    """FR-201 a FR-206."""

    def test_hu1_1_fr201_fr202_partida_nueva(self):
        partida = partida_sintetica(esqueleto_hu1())

        self.assertEqual(estados(partida, range(1, 6)),
                         [EXPLORADA, AVISTADA, AVISTADA, DESCONOCIDA,
                          DESCONOCIDA])
        self.assertEqual(puerta(partida, 1, "E").estado.recordada, ABIERTA)
        self.assertEqual(puerta(partida, 1, "S").estado.recordada, ABIERTA)
        self.assertEqual(partida.conocimiento.exploradas, 1)
        self.assertEqual(partida.conocimiento.avistadas, 2)

    def test_hu1_2_fr201_fr202_al_entrar_queda_explorada(self):
        partida = partida_sintetica(esqueleto_hu1())
        partida.mover("E")

        self.assertEqual(estados(partida, range(1, 6)),
                         [EXPLORADA, EXPLORADA, AVISTADA, AVISTADA,
                          DESCONOCIDA])
        self.assertEqual(puerta(partida, 2, "S").estado.recordada, ABIERTA)

    def test_hu1_3_fr206_puerta_lejana_se_recuerda_como_se_vio(self):
        partida = partida_sintetica(esqueleto_hu1())
        partida.mover("E")
        partida.mover("O")
        puerta(partida, 2, "S").cerrar()
        partida.esperar()

        self.assertEqual(puerta(partida, 2, "S").estado.recordada, ABIERTA)
        self.assertEqual(puerta(partida, 4, "N").estado.recordada, ABIERTA)

        # Al volver a la 2, se observa cerrada desde los dos lados.
        partida.mover("E")
        self.assertEqual(puerta(partida, 2, "S").estado.recordada, CERRADA)
        self.assertEqual(puerta(partida, 4, "N").estado.recordada, CERRADA)

    def test_hu1_3_fr205_al_entrar_por_el_otro_lado(self):
        partida = partida_sintetica(esqueleto_hu1())
        partida.mover("E")
        partida.mover("O")
        puerta(partida, 2, "S").cerrar()

        partida.mover("S")
        partida.mover("E")              # entra a la 4

        self.assertEqual(puerta(partida, 4, "N").estado.recordada, CERRADA)
        self.assertEqual(puerta(partida, 2, "S").estado.recordada, CERRADA)

    def test_hu1_4_fr204_cierre_automatico_mientras_espera(self):
        esqueleto = [
            sala(1, {"E": salida(2, cerrada=True, cierre_automatico=150)}),
            sala(2, {"O": salida(1, cerrada=True, cierre_automatico=150)}),
        ]
        partida = partida_sintetica(esqueleto)
        este = puerta(partida, 1, "E")
        self.assertEqual(este.estado.recordada, CERRADA)

        partida.abrir("E")
        self.assertEqual(este.estado.recordada, ABIERTA)

        for _ in range(3):
            partida.esperar()
            # Antes de cada decisión, lo recordado es lo real (FR-204).
            self.assertEqual(este.estado.recordada,
                             CERRADA if este.esta_cerrada() else ABIERTA)

        self.assertTrue(este.esta_cerrada())
        self.assertEqual(este.estado.recordada, CERRADA)

    def test_hu1_5_fr202_fr205_salida_sin_vuelta_no_se_observa(self):
        partida = partida_sintetica(esqueleto_hu1())
        partida.esperar()

        self.assertIsNone(puerta(partida, 5, "N").estado.recordada)
        self.assertEqual(estados(partida, [5]), [DESCONOCIDA])
        self.assertNotIn("sala 5", texto_estado(partida))

    def test_fr201_fr224_el_pergamino_revierte_la_exploracion(self):
        jugador = nuevo_jugador(pergaminos=1)
        partida = partida_sintetica(esqueleto_hu1(), jugador=jugador)
        antes = foto_conocimiento(partida)

        partida.mover("E")
        self.assertNotEqual(foto_conocimiento(partida), antes)

        self.assertTrue(partida.usar_pergamino())
        self.assertEqual(foto_conocimiento(partida), antes)


# ---------------------------------------------------------------------------
# T007
# ---------------------------------------------------------------------------

def esqueleto_bitacora():
    """La sala 1 se une a la 2. Las salas 7 y 8 están lejos. La 9 tiene una
    salida sin vuelta que llega a la 1 (N) y otra a la 10 (E)."""
    return [
        sala(1, {"E": salida(2)}),
        sala(2, {"O": salida(1)}),
        sala(7, {"E": salida(8)}),
        sala(8, {"O": salida(7)}),
        sala(9, {"N": salida(1), "E": salida(10)}),
        sala(10, {"O": salida(9)}),
    ]


class TestBitacoraNiebla(unittest.TestCase):
    """FR-205, FR-208 (HU1-6; contracts/vista.md «Bitácora»)."""

    def setUp(self):
        fichas = catalogo(ficha_errante("ent_errante", vida_max=50),
                          FICHA_TRAMPA)
        contenidos = [
            contenido(1, enemigos=(("e-1", "ent_errante", 10),),
                      trampas=(("t-1", "trp_aguja"),)),
            contenido(7, enemigos=(("e-7", "ent_errante", 10),)),
            contenido(8, trampas=(("t-8", "trp_aguja"),)),
        ]
        jugador = nuevo_jugador(vida_max=1000, defensa=50)
        self.partida = partida_sintetica(esqueleto_bitacora(), contenidos,
                                         fichas, jugador=jugador)

    def mensajes_nuevos(self, programar):
        """Programa con `programar(tiempo)` un evento que cae dentro del
        próximo `esperar` y devuelve los mensajes nuevos de la bitácora."""
        antes = len(list(self.partida.bitacora))
        programar(self.partida.reloj + 10)
        self.partida.esperar()
        return list(self.partida.bitacora)[antes:]

    def sala(self, id_sala):
        return self.partida.mapa.obtener_sala(id_sala)

    def test_fr208_regeneracion_lejos_no_avisa(self):
        enemigo = self.sala(7).enemigo_en(0)
        mensajes = self.mensajes_nuevos(
            lambda t: self.partida.agenda.programar(t, REGENERACION, enemigo))

        self.assertFalse(any("regenera vida" in m for m in mensajes))

    def test_fr208_regeneracion_en_la_sala_avisa(self):
        enemigo = self.sala(1).enemigo_en(0)
        mensajes = self.mensajes_nuevos(
            lambda t: self.partida.agenda.programar(t, REGENERACION, enemigo))

        self.assertTrue(any("(e-1) regenera vida." in m for m in mensajes))

    def test_fr208_rearme_lejos_no_avisa(self):
        trampa = self.sala(8).trampa_en(0)
        trampa.desactivar()
        mensajes = self.mensajes_nuevos(
            lambda t: self.partida.agenda.programar(t, REARME_TRAMPA, trampa))

        self.assertTrue(trampa.esta_activa())
        self.assertFalse(any("Una trampa vuelve a estar armada." in m
                             for m in mensajes))

    def test_fr208_rearme_en_la_sala_avisa(self):
        trampa = self.sala(1).trampa_en(0)
        trampa.desactivar()
        mensajes = self.mensajes_nuevos(
            lambda t: self.partida.agenda.programar(t, REARME_TRAMPA, trampa))

        self.assertTrue(any("Una trampa vuelve a estar armada." in m
                            for m in mensajes))

    def cierre(self, id_sala, direccion):
        from crypta.Modelo.Partida import CIERRE_PUERTA

        objetivo = self.sala(id_sala).obtener_puerta(direccion)
        mensajes = self.mensajes_nuevos(
            lambda t: self.partida.agenda.programar(t, CIERRE_PUERTA,
                                                    objetivo))
        self.assertTrue(objetivo.esta_cerrada())
        return any("Una puerta se cierra automáticamente." in m
                   for m in mensajes)

    def test_fr208_cierre_lejos_no_avisa(self):
        self.assertFalse(self.cierre(9, "E"))

    def test_fr205_fr208_cierre_de_salida_sin_vuelta_que_llega_no_avisa(self):
        self.assertFalse(self.cierre(9, "N"))

    def test_fr208_cierre_de_una_salida_de_la_sala_avisa(self):
        self.assertTrue(self.cierre(1, "E"))

    def test_fr208_cierre_del_otro_lado_de_una_salida_de_la_sala_avisa(self):
        # La 2 —O→ 1 es el otro lado de la 1 —E→ 2: la misma puerta.
        self.assertTrue(self.cierre(2, "O"))


# ---------------------------------------------------------------------------
# T008
# ---------------------------------------------------------------------------

NOMBRES_OCULTOS = ("Cámara Oculta", "Tesoro Prohibido", "Sombra Acechante",
                   "Corona Maldita", "ent_sombra", "e-2", "itm_corona")


def cripta_oculta():
    """(esqueleto, contenidos, fichas). Las salas 2 y 3 y su contenido
    tienen nombres que nunca deben verse desde la sala 1."""
    esqueleto = [
        sala(1, {"E": salida(2)}, nombre="Vestíbulo"),
        sala(2, {"O": salida(1), "E": salida(3)}, nombre="Cámara Oculta"),
        sala(3, {"O": salida(2)}, nombre="Tesoro Prohibido"),
    ]
    sombra = ficha_errante("ent_sombra")
    sombra["nombre"] = "Sombra Acechante"
    corona = {"id": "itm_corona", "clase": "tesoro", "nombre": "Corona Maldita",
              "peso": 1, "valor": 9}
    contenidos = [
        contenido(1),
        contenido(2, enemigos=(("e-2", "ent_sombra"),)),
        contenido(3, objetos=("itm_corona",)),
    ]
    return esqueleto, contenidos, catalogo(sombra, corona)


class TestVistaNiebla(unittest.TestCase):
    """FR-207, FR-209 (HU1-7, HU1-10)."""

    def test_fr207_salidas_leen_lo_recordado(self):
        partida = partida_sintetica(esqueleto_hu1())
        puerta(partida, 1, "E").cerrar()      # sin observar

        salidas = seccion_salidas(texto_estado(partida))

        self.assertIn("E: sala 2 (Abierta, costo 100)", salidas)

    def test_fr207_recordada_cerrada_con_llave_se_muestra(self):
        esqueleto = [
            sala(1, {"E": salida(2, cerrada=True, llave="itm_llave")}),
            sala(2, {"O": salida(1, cerrada=True, llave="itm_llave")}),
        ]
        partida = partida_sintetica(esqueleto)

        self.assertIn("E: sala 2 (Cerrada, necesita itm_llave, costo 100)",
                      seccion_salidas(texto_estado(partida)))

    def test_hu1_7_vecinas_solo_por_su_id(self):
        esqueleto, contenidos, fichas = cripta_oculta()
        partida = partida_sintetica(esqueleto, contenidos, fichas)
        texto = texto_estado(partida)

        self.assertIn("E: sala 2", texto)

        for nombre in NOMBRES_OCULTOS:
            self.assertNotIn(nombre, texto)

    def test_fr209_hu1_10_la_precarga_no_revela_nada(self):
        from crypta.Modelo.Resumen import armar_mapa_resumido
        from crypta.Vista.FormatoMapa import formatear_mapa

        esqueleto, contenidos, fichas = cripta_oculta()
        fuente = FuenteContadora(esqueleto, contenidos, fichas)

        with tempfile.TemporaryDirectory() as carpeta:
            controlador = controlador_sintetico(fuente, carpeta, ["esperar"])
            controlador.iniciar()
            controlador.gestor_contenido.cerrar()

        partida = controlador.partida

        # La precarga sí trajo el contenido de las salas no exploradas.
        self.assertTrue(partida.mapa.obtener_sala(2).contenido_cargado())
        self.assertTrue(partida.mapa.obtener_sala(3).contenido_cargado())
        self.assertEqual(estados(partida, [1, 2, 3]),
                         [EXPLORADA, AVISTADA, DESCONOCIDA])

        textos = (texto_estado(partida),
                  formatear_mapa(armar_mapa_resumido(partida)),
                  "\n".join(partida.bitacora))

        for texto in textos:
            for nombre in NOMBRES_OCULTOS:
                self.assertNotIn(nombre, texto)

    def test_fr209_la_resolubilidad_no_cambia_el_mapa_conocido(self):
        from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
        from crypta.Modelo.Verificador import verificar
        from tests.ayudas_cripta import respuesta_llaves

        esqueleto = esqueleto_hu1()
        partida = partida_sintetica(esqueleto)
        antes = foto_conocimiento(partida)

        verificar(partida.mapa, datos_generales(esqueleto),
                  leer_ubicaciones(respuesta_llaves(), partida.mapa))

        self.assertEqual(foto_conocimiento(partida), antes)


# ---------------------------------------------------------------------------
# T009
# ---------------------------------------------------------------------------

def esqueleto_antorcha():
    """La 2 tiene salidas a la 3 (N, abierta), a la 4 (E, cerrada) y a la 5
    (S, abierta). Más allá: 3 —N→ 6 y 4 —E→ 7. La 1 tiene además 1 —S→ 8."""
    return [
        sala(1, {"E": salida(2), "S": salida(8)}),
        sala(2, {"O": salida(1), "N": salida(3),
                 "E": salida(4, cerrada=True), "S": salida(5)}),
        sala(3, {"S": salida(2), "N": salida(6)}),
        sala(4, {"O": salida(2, cerrada=True), "E": salida(7)}),
        sala(5, {"N": salida(2)}),
        sala(6, {"S": salida(3)}),
        sala(7, {"O": salida(4)}),
        sala(8, {"N": salida(1)}),
    ]


def contenidos_antorcha():
    return [
        contenido(1, objetos=("itm_antorcha",)),
        contenido(3, enemigos=(("e-3", "ent_errante"),)),
        contenido(4, objetos=("itm_cofre",)),
        contenido(5, trampas=(("t-5", "trp_aguja"),)),
    ]


def fichas_antorcha():
    cofre = {"id": "itm_cofre", "clase": "tesoro", "nombre": "Cofre Secreto",
             "peso": 1, "valor": 5}
    return catalogo(ficha_errante("ent_errante"), FICHA_TRAMPA,
                    FICHA_ANTORCHA, cofre)


class TestAntorcha(unittest.TestCase):
    """FR-212 a FR-215 (HU2-1 a HU2-4)."""

    def partida(self, encender):
        jugador = nuevo_jugador(vida_max=1000)
        partida = partida_sintetica(esqueleto_antorcha(), contenidos_antorcha(),
                                    fichas_antorcha(), jugador=jugador)
        partida.recoger(0)

        if encender:
            partida.usar()
            self.assertTrue(partida.antorcha_encendida())

        return partida

    def test_hu2_1_fr212_fr213_revela_las_vecinas(self):
        partida = self.partida(encender=True)
        partida.mover("E")

        self.assertEqual(estados(partida, range(1, 9)),
                         [EXPLORADA, EXPLORADA, EXPLORADA, EXPLORADA,
                          EXPLORADA, AVISTADA, AVISTADA, AVISTADA])
        self.assertEqual(puerta(partida, 3, "N").estado.recordada, ABIERTA)
        self.assertEqual(puerta(partida, 4, "O").estado.recordada, CERRADA)
        self.assertEqual(puerta(partida, 4, "E").estado.recordada, ABIERTA)
        self.assertEqual(puerta(partida, 5, "N").estado.recordada, ABIERTA)

    def test_hu2_2_fr214_no_toca_el_contenido(self):
        partida = self.partida(encender=True)
        partida.mover("E")

        enemigo = partida.mapa.obtener_sala(3).enemigo_en(0)
        trampa = partida.mapa.obtener_sala(5).trampa_en(0)
        self.assertFalse(enemigo.esta_activo())
        self.assertTrue(trampa.esta_activa())

        texto = texto_estado(partida)
        for oculto in ("ent_errante", "e-3", "Cofre Secreto", "Aguja"):
            self.assertNotIn(oculto, texto)

    def test_hu2_3_sin_antorcha_solo_la_sala(self):
        partida = self.partida(encender=False)
        partida.mover("E")

        self.assertEqual(estados(partida, range(1, 9)),
                         [EXPLORADA, EXPLORADA, AVISTADA, AVISTADA, AVISTADA,
                          DESCONOCIDA, DESCONOCIDA, AVISTADA])
        self.assertIsNone(puerta(partida, 3, "N").estado.recordada)

    def test_hu2_4_fr215_al_apagarse_sigue_explorado(self):
        partida = self.partida(encender=True)
        partida.mover("E")

        while partida.antorcha_encendida():
            partida.esperar()

        partida.mover("N")                  # entra a la 3, sin antorcha

        self.assertEqual(estados(partida, range(1, 9)),
                         [EXPLORADA, EXPLORADA, EXPLORADA, EXPLORADA,
                          EXPLORADA, AVISTADA, AVISTADA, AVISTADA])

    def test_fr214_al_entrar_despues_despierta_y_activa(self):
        partida = self.partida(encender=True)
        partida.mover("E")
        partida.mover("N")
        self.assertTrue(partida.mapa.obtener_sala(3).enemigo_en(0).esta_activo())

        partida.mover("S")
        partida.mover("S")
        self.assertFalse(partida.mapa.obtener_sala(5).trampa_en(0).esta_activa())

    def test_fr213_revelar_una_sala_ya_explorada_la_vuelve_a_observar(self):
        partida = self.partida(encender=True)
        puerta(partida, 1, "S").cerrar()      # cambia sin que se observe…
        partida.mover("E")                    # …y se sale de la 1

        # La antorcha revela la 1 desde la 2: su salida S se observa.
        self.assertEqual(estados(partida, [1]), [EXPLORADA])
        self.assertEqual(puerta(partida, 1, "S").estado.recordada, CERRADA)

    def test_fr214_mismas_solicitudes_con_y_sin_antorcha(self):
        def solicitudes(comandos):
            esqueleto = esqueleto_antorcha()
            fuente = FuenteContadora(
                esqueleto, contenidos_antorcha() + [
                    contenido(i) for i in (2, 6, 7, 8)],
                fichas_antorcha(),
                generales=datos_generales(esqueleto, presupuesto=1000))

            with tempfile.TemporaryDirectory() as carpeta:
                controlador = controlador_sintetico(fuente, carpeta, comandos)
                controlador.iniciar()
                controlador.gestor_contenido.cerrar()

            return controlador.partida, dict(fuente.por_operacion)

        con, por_operacion_con = solicitudes(
            ["recoger 1", "usar", "mover E", "mover N"])
        sin, por_operacion_sin = solicitudes(
            ["recoger 1", "esperar", "mover E", "mover N"])

        self.assertTrue(con.conocimiento.esta_explorada(
            con.mapa.obtener_sala(5)))
        self.assertFalse(sin.conocimiento.esta_explorada(
            sin.mapa.obtener_sala(5)))
        self.assertEqual(por_operacion_con, por_operacion_sin)


if __name__ == "__main__":
    unittest.main()
