"""«ir a <sala>» (capacidad 002, fase 3, historia 3).

- T018 `TestRutaConocida`: FR-217, FR-218 (research D5, D6).
- T019 `TestIrAValidacion`: FR-216 (HU3-1 a HU3-3).
- T020 `TestIrARuta`: FR-217 a FR-219 (HU3-4 a HU3-8).
- T021 `TestIrAPasos`: FR-220, FR-221 (HU3-9 a HU3-13, HU3-16).
- T022 `TestIrALog`: FR-222, FR-223 (HU3-14, HU3-15; SC-206).

Las criptas se escriben a mano con `tests/ayudas_cripta.py`; ninguna prueba
lee `cache/`.
"""

import os
import tempfile
import unittest

from crypta.Controlador.Comandos import (
    ComandoInvalido,
    ejecutar_comando,
    ejecutar_ir_a,
    leer_ir_a,
)
from crypta.Modelo.MapaConocido import MapaConocido
from crypta.Modelo.Partida import CIERRE_PUERTA, AccionInvalida
from crypta.Modelo.Perseguidor import RECALCULAR, SELECTIVA, TOTAL
from crypta.Modelo.Puerta import CERRADA
from crypta.Modelo.RutaConocida import RutaConocida
from crypta.Modelo.Viaje import (
    DANIO,
    ENEMIGOS,
    FIN_PARTIDA,
    LLEGADA,
    PASO_IMPOSIBLE,
    SIN_RUTA,
)
from crypta.Vista.FormatoMapa import texto_motivo
from tests.ayudas_cripta import (
    catalogo,
    contenido,
    ficha_errante,
    ficha_rastreador,
    mapa_de,
    nuevo_jugador,
    partida_sintetica,
    sala,
    salida,
)


FICHA_LLAVE = {"id": "itm_llave", "clase": "llave", "nombre": "Llave",
               "peso": 1, "valor": 1}


def cuadro():
    """1 —E→ 2, 1 —S→ 3, 2 —S→ 4, 3 —E→ 4, 4 —E→ 5 (todas de ida y vuelta,
    costo 100). Además 6 —N→ 7 y 6 —E→ 7, dos salidas sin vuelta a la
    misma sala."""
    return [
        sala(1, {"E": salida(2), "S": salida(3)}),
        sala(2, {"O": salida(1), "S": salida(4)}),
        sala(3, {"N": salida(1), "E": salida(4)}),
        sala(4, {"N": salida(2), "O": salida(3), "E": salida(5)}),
        sala(5, {"O": salida(4)}),
        sala(6, {"N": salida(7), "E": salida(7)}),
        sala(7, {}),
    ]


def pasillo(costos=(100, 100, 100)):
    """1 — 2 — 3 — 4 … hacia el E, con los costos dados."""
    salas = []
    n = len(costos) + 1

    for i in range(1, n + 1):
        salidas = {}

        if i < n:
            salidas["E"] = salida(i + 1, costo=costos[i - 1])
        if i > 1:
            salidas["O"] = salida(i - 1, costo=costos[i - 2])

        salas.append(sala(i, salidas))

    return salas


def explorar(partida, *ids):
    for id_sala in ids:
        partida.conocimiento.explorar(partida.mapa.obtener_sala(id_sala))


def viajar(partida, id_destino, garantizar=None, comentarios=None,
           antes_de_cada_paso=None):
    """`ejecutar_ir_a` con `ejecutar_comando` como paso. Devuelve
    (viaje, pasos), con cada paso como (comando, reloj después)."""
    pasos = []

    def ejecutar_paso(comando):
        if antes_de_cada_paso is not None:
            antes_de_cada_paso(comando)

        ejecutar_comando(partida, comando, garantizar)
        pasos.append((comando, partida.reloj))

    anotar = comentarios.append if comentarios is not None else None
    viaje = ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar,
                          anotar)
    return viaje, pasos


# ---------------------------------------------------------------------------
# T018
# ---------------------------------------------------------------------------

class TestRutaConocida(unittest.TestCase):
    """FR-217, FR-218; research D5, D6; data-model «RutaConocida»."""

    def armar(self, ids, modo=SELECTIVA, esqueleto=None):
        self.mapa = mapa_de(esqueleto if esqueleto is not None else cuadro())
        self.conocido = MapaConocido(self.mapa, lambda cambio: None)

        for id_sala in ids:
            self.conocido.explorar(self.s(id_sala))

        self.ruta = RutaConocida(self.mapa, self.conocido, modo)
        self.conocido.observador = self.ruta

    def s(self, id_sala):
        return self.mapa.obtener_sala(id_sala)

    def paso(self, desde, hasta):
        """El paso elegido; comprueba que coincide con el cálculo desde
        cero (SC-203)."""
        elegido = self.ruta.siguiente_paso(self.s(desde), self.s(hasta))
        self.assertIs(elegido,
                      self.ruta.paso_desde_cero(self.s(desde), self.s(hasta)))
        return elegido

    def test_fr217_solo_salas_exploradas(self):
        self.armar([1, 5])                  # la 4 queda avistada
        self.assertIsNone(self.paso(1, 5))

    def test_fr217_solo_salidas_recordadas_abiertas(self):
        self.armar([1, 2, 3, 4, 5])
        self.s(1).obtener_puerta("E").cerrar()
        self.conocido.observar(self.s(1))

        self.assertIs(self.paso(1, 4), self.s(1).obtener_puerta("S"))

    def test_fr217_lo_recordado_manda_sobre_lo_real(self):
        self.armar([1, 2, 3, 4, 5])
        self.s(1).obtener_puerta("S").cerrar()     # sin observar

        self.assertIs(self.paso(1, 3), self.s(1).obtener_puerta("S"))

    def test_fr217_desempate_por_menor_id_de_la_vecina(self):
        self.armar([1, 2, 3, 4, 5])
        self.assertIs(self.paso(1, 4), self.s(1).obtener_puerta("E"))

    def test_fr217_desempate_a_la_misma_vecina_en_orden_nseo(self):
        self.armar([6, 7])
        self.assertIs(self.paso(6, 7), self.s(6).obtener_puerta("N"))

    def test_d6_un_paso_sin_cambios_no_busca_de_nuevo(self):
        self.armar([1, 2, 3, 4, 5])
        self.paso(1, 5)
        self.assertEqual(self.ruta.busquedas, 1)

        self.paso(2, 5)
        self.paso(4, 5)
        self.assertEqual(self.ruta.busquedas, 1)

    def test_d6_cambio_con_extremo_asentado_invalida(self):
        self.armar([1, 2, 3, 4, 5])
        self.paso(1, 5)
        self.s(2).obtener_puerta("S").cerrar()
        self.conocido.observar(self.s(2))

        self.assertEqual(self.ruta.invalidaciones, 1)
        self.assertIs(self.paso(1, 5), self.s(1).obtener_puerta("S"))
        self.assertEqual(self.ruta.busquedas, 2)

    def test_d6_cambio_sin_extremos_asentados_no_invalida(self):
        self.armar([1, 2, 3, 4, 5])
        self.paso(4, 5)                     # asienta solo 5 y 4
        self.s(1).obtener_puerta("E").cerrar()
        self.conocido.observar(self.s(1))

        self.assertEqual(self.ruta.invalidaciones, 0)
        self.paso(4, 5)
        self.assertEqual(self.ruta.busquedas, 1)

    def test_d6_explorar_una_vecina_de_una_asentada_invalida(self):
        self.armar([2, 4, 5])               # 1 y 3 avistadas
        self.paso(4, 5)                     # asienta 5 y 4

        self.conocido.explorar(self.s(1))   # sus vecinas: 2 y 3, no asentadas
        self.assertEqual(self.ruta.invalidaciones, 0)

        self.conocido.explorar(self.s(3))   # vecina de la 4, asentada
        self.assertEqual(self.ruta.invalidaciones, 1)
        self.paso(3, 5)

    def test_d6_modo_total_invalida_con_cualquier_cambio(self):
        self.armar([1, 2, 3, 4, 5], modo=TOTAL)
        self.paso(4, 5)
        self.s(1).obtener_puerta("E").cerrar()
        self.conocido.observar(self.s(1))

        self.assertEqual(self.ruta.invalidaciones, 1)
        self.paso(4, 5)
        self.assertEqual(self.ruta.busquedas, 2)

    def test_d6_modo_recalcular_busca_en_cada_paso(self):
        self.armar([1, 2, 3, 4, 5], modo=RECALCULAR)
        self.paso(1, 5)
        self.paso(2, 5)
        self.paso(4, 5)
        self.assertEqual(self.ruta.busquedas, 3)


# ---------------------------------------------------------------------------
# T019
# ---------------------------------------------------------------------------

class TestIrAValidacion(unittest.TestCase):
    """FR-216 (HU3-1 a HU3-3; contracts/cli.md)."""

    def rechazo(self, partida, id_destino):
        reloj, acciones = partida.reloj, partida.acciones_jugador
        comentarios = []

        with self.assertRaises(AccionInvalida) as error:
            viajar(partida, id_destino, comentarios=comentarios)

        self.assertEqual((partida.reloj, partida.acciones_jugador),
                         (reloj, acciones))
        self.assertEqual(comentarios, [])
        return str(error.exception)

    def test_hu3_1_no_explorada_e_inexistente_dan_el_mismo_mensaje(self):
        partida = partida_sintetica(cuadro())

        self.assertEqual(self.rechazo(partida, 3), "No conoces la sala 3.")
        self.assertEqual(self.rechazo(partida, 4), "No conoces la sala 4.")
        self.assertEqual(self.rechazo(partida, 99999),
                         "No conoces la sala 99999.")

    def test_hu3_2_la_sala_actual(self):
        partida = partida_sintetica(cuadro())
        self.assertEqual(self.rechazo(partida, 1), "Ya estás en la sala 1.")

    def test_hu3_2_explorada_sin_ruta_conocida(self):
        esqueleto = [sala(1, {"E": salida(2, cerrada=True)}),
                     sala(2, {"O": salida(1, cerrada=True)})]
        partida = partida_sintetica(esqueleto)
        explorar(partida, 2)

        self.assertEqual(self.rechazo(partida, 2),
                         "No conoces una ruta abierta hasta la sala 2.")

    def test_hu3_3_formas_mal_escritas(self):
        for texto in ("ir", "ir a", "ir a x", "ir a -3", "ir a 3 4", "ir b 3",
                      "ir a 3.5", "ir a +3"):
            with self.subTest(texto=texto):
                with self.assertRaises(ComandoInvalido):
                    leer_ir_a(texto)

    def test_hu3_3_formas_bien_escritas(self):
        self.assertEqual(leer_ir_a("ir a 7"), 7)
        self.assertEqual(leer_ir_a("  IR A 12 "), 12)


# ---------------------------------------------------------------------------
# T020
# ---------------------------------------------------------------------------

class TestIrARuta(unittest.TestCase):
    """FR-217 a FR-219 (HU3-4 a HU3-8)."""

    def test_hu3_4_la_ruta_mas_barata(self):
        esqueleto = [
            sala(1, {"E": salida(2, costo=100), "S": salida(4, costo=500)}),
            sala(2, {"O": salida(1, costo=100), "S": salida(4, costo=100)}),
            sala(4, {"N": salida(2, costo=100), "O": salida(1, costo=500)}),
        ]
        partida = partida_sintetica(esqueleto)
        explorar(partida, 2, 4)

        viaje, pasos = viajar(partida, 4)

        self.assertEqual([c for c, _ in pasos], ["mover E", "mover S"])
        self.assertEqual(viaje.motivo, LLEGADA)
        self.assertEqual(partida.reloj, 200)

    def test_hu3_5_empate_va_a_la_vecina_de_menor_id(self):
        esqueleto = [
            sala(1, {"E": salida(5), "S": salida(3)}),
            sala(3, {"N": salida(1), "E": salida(4)}),
            sala(4, {"O": salida(3), "N": salida(5)}),
            sala(5, {"O": salida(1), "S": salida(4)}),
        ]
        partida = partida_sintetica(esqueleto)
        explorar(partida, 3, 4, 5)

        _, pasos = viajar(partida, 4)

        self.assertEqual(pasos[0][0], "mover S")

    def test_hu3_6_no_pasa_por_una_sala_avistada(self):
        esqueleto = [
            sala(1, {"E": salida(2, costo=100), "S": salida(3, costo=300)}),
            sala(2, {"O": salida(1, costo=100), "S": salida(4, costo=100)}),
            sala(3, {"N": salida(1, costo=300), "E": salida(4, costo=100)}),
            sala(4, {"N": salida(2, costo=100), "O": salida(3, costo=100)}),
        ]
        partida = partida_sintetica(esqueleto)
        explorar(partida, 3, 4)             # la 2 sigue avistada

        _, pasos = viajar(partida, 4)

        self.assertEqual([c for c, _ in pasos], ["mover S", "mover E"])

    def esqueleto_hu3_7(self, con_alternativa):
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1), "E": salida(4)}),
            sala(4, {"O": salida(2)}),
        ]

        if con_alternativa:
            esqueleto[0]["salidas"]["S"] = salida(3, costo=300)
            esqueleto.insert(2, sala(3, {"N": salida(1, costo=300),
                                         "E": salida(4, costo=300)}))
            esqueleto[3]["salidas"]["S"] = salida(3, costo=300)

        return esqueleto

    def test_hu3_7_puerta_cerrada_en_realidad_se_evita(self):
        partida = partida_sintetica(self.esqueleto_hu3_7(True))
        explorar(partida, 2, 3, 4)
        puerta = partida.mapa.obtener_sala(2).obtener_puerta("E")
        puerta.cerrar()                     # sin observar

        viaje, pasos = viajar(partida, 4)

        self.assertEqual([c for c, _ in pasos],
                         ["mover E", "mover O", "mover S", "mover E"])
        self.assertEqual(puerta.estado.recordada, CERRADA)
        self.assertEqual(viaje.motivo, LLEGADA)

    def test_hu3_7_sin_alternativa_se_detiene_sin_gastar_tiempo(self):
        partida = partida_sintetica(self.esqueleto_hu3_7(False))
        explorar(partida, 2, 4)
        partida.mapa.obtener_sala(2).obtener_puerta("E").cerrar()

        viaje, pasos = viajar(partida, 4)

        self.assertEqual(viaje.motivo, SIN_RUTA)
        self.assertEqual(viaje.pasos, 1)
        self.assertEqual(partida.reloj, pasos[-1][1])
        self.assertEqual(partida.acciones_jugador, 1)
        self.assertEqual(
            texto_motivo(viaje),
            "El viaje se detuvo: ya no conoces una ruta abierta hasta la "
            "sala 4 (1 pasos).")

    def con_llave(self, esqueleto):
        partida = partida_sintetica(
            esqueleto, [contenido(1, objetos=("itm_llave",))],
            catalogo(FICHA_LLAVE))
        partida.recoger(0)
        self.assertIsNotNone(
            partida.jugador.inventario.buscar_por_id("itm_llave"))
        return partida

    def test_hu3_8_fr219_rechazo_si_la_ruta_cruza_una_puerta_cerrada(self):
        esqueleto = [
            sala(1, {"E": salida(2, cerrada=True, llave="itm_llave")}),
            sala(2, {"O": salida(1, cerrada=True, llave="itm_llave")}),
        ]
        partida = self.con_llave(esqueleto)
        explorar(partida, 2)

        with self.assertRaises(AccionInvalida):
            viajar(partida, 2)

        self.assertTrue(partida.mapa.obtener_sala(1).obtener_puerta("E")
                        .esta_cerrada())

    def test_hu3_8_fr219_no_abre_la_puerta_descubierta_cerrada(self):
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1), "E": salida(3, llave="itm_llave")}),
            sala(3, {"O": salida(2, llave="itm_llave")}),
        ]
        partida = self.con_llave(esqueleto)
        explorar(partida, 2, 3)
        puerta = partida.mapa.obtener_sala(2).obtener_puerta("E")
        puerta.cerrar()

        viaje, pasos = viajar(partida, 3)

        self.assertEqual(viaje.motivo, SIN_RUTA)
        self.assertTrue(puerta.esta_cerrada())
        self.assertEqual([c for c, _ in pasos], ["mover E"])


# ---------------------------------------------------------------------------
# T021
# ---------------------------------------------------------------------------

class TestIrAPasos(unittest.TestCase):
    """FR-220, FR-221 (HU3-9 a HU3-13, HU3-16; contracts/vista.md)."""

    def test_hu3_9_cada_paso_es_una_accion_y_corre_el_reloj(self):
        esqueleto = pasillo((100, 250, 100, 300))
        esqueleto.append(sala(9, {"E": salida(10)}))
        esqueleto.append(sala(10, {"O": salida(9)}))
        partida = partida_sintetica(esqueleto)
        explorar(partida, 2, 3, 4, 5)
        lejana = partida.mapa.obtener_sala(9).obtener_puerta("E")
        partida.agenda.programar(200, CIERRE_PUERTA, lejana)
        cerrada_antes = []

        viaje, pasos = viajar(
            partida, 5,
            antes_de_cada_paso=lambda c: cerrada_antes.append(
                lejana.esta_cerrada()))

        self.assertEqual(pasos, [("mover E", 100), ("mover E", 350),
                                 ("mover E", 450), ("mover E", 750)])
        self.assertEqual(partida.acciones_jugador, 4)
        self.assertEqual(cerrada_antes, [False, False, True, True])
        self.assertEqual(viaje.motivo, LLEGADA)
        self.assertEqual(texto_motivo(viaje),
                         "Llegaste a la sala 5 en 4 pasos.")

    def test_hu3_10_sala_con_enemigos_dormidos(self):
        partida = partida_sintetica(
            pasillo(), [contenido(3, enemigos=(("e-3", "ent_errante"),))],
            catalogo(ficha_errante("ent_errante", velocidad=1)))
        explorar(partida, 2, 3, 4)

        viaje, _ = viajar(partida, 4)

        self.assertEqual(viaje.motivo, ENEMIGOS)
        self.assertEqual(partida.jugador.sala_actual, 3)
        self.assertTrue(partida.mapa.obtener_sala(3).enemigo_en(0)
                        .esta_activo())
        self.assertEqual(texto_motivo(viaje),
                         "El viaje se detuvo: hay enemigos en esta sala "
                         "(2 pasos).")

    def test_hu3_11_danio_por_trampa(self):
        trampa = {"id": "trp_aguja", "clase": "trampa", "nombre": "Aguja",
                  "daño": 2}
        partida = partida_sintetica(
            pasillo(), [contenido(2, trampas=(("t-2", "trp_aguja"),))],
            catalogo(trampa))
        explorar(partida, 2, 3, 4)

        viaje, _ = viajar(partida, 4)

        self.assertEqual((viaje.motivo, viaje.pasos), (DANIO, 1))
        self.assertEqual(texto_motivo(viaje),
                         "El viaje se detuvo: recibiste daño (1 pasos).")

    def test_hu3_11_danio_por_pulso_de_veneno(self):
        veneno = {"id": "trp_veneno", "clase": "trampa", "nombre": "Púa",
                  "daño": 0, "veneno": 1}
        partida = partida_sintetica(
            pasillo(), [contenido(2, trampas=(("t-2", "trp_veneno"),))],
            catalogo(veneno))
        explorar(partida, 2, 3, 4)
        vida = partida.jugador.vida

        viaje, _ = viajar(partida, 4)

        self.assertEqual(viaje.motivo, DANIO)
        self.assertLess(partida.jugador.vida, vida)

    def test_hu3_11_danio_por_ataque_tiene_prioridad_sobre_enemigos(self):
        partida = partida_sintetica(
            pasillo(), [contenido(2, enemigos=(("e-2", "ent_errante"),))],
            catalogo(ficha_errante("ent_errante", velocidad=200, ataque=20)),
            jugador=nuevo_jugador(vida_max=500))
        explorar(partida, 2, 3, 4)

        viaje, _ = viajar(partida, 4)

        self.assertEqual((viaje.motivo, viaje.pasos), (DANIO, 1))
        self.assertLess(partida.jugador.vida, 500)

    def test_hu3_12_paso_imposible_al_cargar_la_sala(self):
        partida = partida_sintetica(pasillo())
        explorar(partida, 2, 3, 4)

        def garantizar(id_sala):
            if id_sala == 3:
                raise RuntimeError("Sin conexión y sin presupuesto")

        viaje, pasos = viajar(partida, 4, garantizar=garantizar)

        self.assertEqual((viaje.motivo, viaje.pasos), (PASO_IMPOSIBLE, 1))
        self.assertEqual(partida.jugador.sala_actual, 2)
        self.assertEqual((partida.reloj, partida.acciones_jugador), (100, 1))
        self.assertEqual(
            texto_motivo(viaje),
            "El viaje se detuvo: no se pudo cargar la sala siguiente "
            "(1 pasos). Sin conexión y sin presupuesto")

    def test_d8_un_error_dentro_del_mover_no_es_paso_imposible(self):
        partida = partida_sintetica(pasillo())
        explorar(partida, 2, 3, 4)

        def ejecutar_paso(comando):
            raise RuntimeError("defecto")

        with self.assertRaises(RuntimeError):
            ejecutar_ir_a(partida, 4, ejecutar_paso)

    def test_hu3_13_muerte(self):
        trampa = {"id": "trp_mortal", "clase": "trampa", "nombre": "Foso",
                  "daño": 100}
        partida = partida_sintetica(
            pasillo(), [contenido(2, trampas=(("t-2", "trp_mortal"),))],
            catalogo(trampa))
        explorar(partida, 2, 3, 4)

        viaje, _ = viajar(partida, 4)

        self.assertTrue(partida.terminada)
        self.assertEqual(viaje.motivo, FIN_PARTIDA)
        self.assertEqual(texto_motivo(viaje),
                         "El viaje terminó con la partida (1 pasos).")

    def test_hu3_13_victoria(self):
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1),
                     "E": salida(3, cerrada=True, llave="itm_llave")}),
            sala(3, {"O": salida(2, cerrada=True, llave="itm_llave")}),
        ]
        partida = partida_sintetica(
            esqueleto, [contenido(1, objetos=("itm_llave",))],
            catalogo(FICHA_LLAVE), sala_salida=3, llave_salida="itm_llave")
        partida.recoger(0)
        partida.mover("E")
        partida.abrir("E")
        partida.mover("O")
        explorar(partida, 3)

        viaje, _ = viajar(partida, 3)

        self.assertEqual(partida.resultado, "victoria")
        self.assertEqual(viaje.motivo, FIN_PARTIDA)

    def test_fr221_desde_una_sala_con_enemigos_se_hace_el_primer_paso(self):
        partida = partida_sintetica(
            pasillo(), [contenido(1, enemigos=(("e-1", "ent_errante"),))],
            catalogo(ficha_errante("ent_errante", velocidad=1)))
        explorar(partida, 2, 3)
        self.assertEqual(len(partida.enemigos_presentes()), 1)

        viaje, pasos = viajar(partida, 3)

        self.assertEqual((viaje.motivo, len(pasos)), (LLEGADA, 2))

    def test_hu3_16_enemigo_que_entra_sin_atacar_no_detiene(self):
        partida = partida_sintetica(
            pasillo((100, 100, 100, 100)),
            [contenido(1, enemigos=(("r-1", "ent_rastreador"),))],
            catalogo(ficha_rastreador("ent_rastreador", velocidad=100)))
        explorar(partida, 2, 3, 4, 5)
        acompanado = []

        def despues(comando):
            acompanado.append(len(partida.enemigos_presentes()) > 0)

        viaje, _ = viajar(partida, 5, antes_de_cada_paso=despues)

        self.assertIn(True, acompanado[1:])      # entró entre dos pasos
        self.assertEqual(viaje.motivo, LLEGADA)

    def test_hu3_16_enemigo_que_entra_y_ataca_detiene(self):
        partida = partida_sintetica(
            pasillo((300, 300, 300)),
            [contenido(1, enemigos=(("r-1", "ent_rastreador"),))],
            catalogo(ficha_rastreador("ent_rastreador", velocidad=300,
                                      ataque=20)),
            jugador=nuevo_jugador(vida_max=500))
        explorar(partida, 2, 3, 4)

        viaje, _ = viajar(partida, 4)

        self.assertEqual(viaje.motivo, DANIO)
        self.assertLess(partida.jugador.vida, 500)


# ---------------------------------------------------------------------------
# T022
# ---------------------------------------------------------------------------

class TestIrALog(unittest.TestCase):
    """FR-222, FR-223 (HU3-14, HU3-15; SC-206)."""

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.carpeta = self._carpeta.name

    def tearDown(self):
        self._carpeta.cleanup()

    def registro(self):
        from crypta.Adaptadores.RegistroPartida import (
            Encabezado, RegistroPartida)

        ruta = os.path.join(self.carpeta, "partida.log")
        encabezado = Encabezado("cripta-prueba", "v", "c", 7, "Ana")
        return ruta, RegistroPartida.crear(ruta, encabezado)

    def lineas_despues_del_separador(self, ruta):
        with open(ruta, encoding="utf-8") as archivo:
            lineas = archivo.read().splitlines()

        return lineas[lineas.index("---") + 1:]

    def viajar_anotando(self, partida, registro, id_destino, garantizar=None):
        def ejecutar_paso(comando):
            ejecutar_comando(partida, comando, garantizar)
            registro.anotar(comando)

        return ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar,
                             registro.anotar_comentario)

    def test_hu3_14_fr222_comentario_y_tres_mover(self):
        ruta, registro = self.registro()
        partida = partida_sintetica(pasillo())
        explorar(partida, 2, 3, 4)

        self.viajar_anotando(partida, registro, 4)

        self.assertEqual(self.lineas_despues_del_separador(ruta),
                         ["# ir a 4", "mover E", "mover E", "mover E"])

    def test_hu3_14_viaje_sin_pasos_no_deja_lineas(self):
        ruta, registro = self.registro()
        partida = partida_sintetica(pasillo())
        explorar(partida, 2, 3, 4)

        def garantizar(id_sala):
            raise RuntimeError("sin red")

        viaje = self.viajar_anotando(partida, registro, 4, garantizar)

        self.assertEqual(viaje.motivo, PASO_IMPOSIBLE)
        self.assertEqual(self.lineas_despues_del_separador(ruta), [])

    def test_fr223_leer_registro_ignora_los_comentarios(self):
        from crypta.Adaptadores.RegistroPartida import leer_registro

        ruta, registro = self.registro()
        registro.anotar("esperar")
        registro.anotar_comentario("ir a 4")
        registro.anotar("mover E")

        _, comandos = leer_registro(ruta)
        leidos = []
        while not comandos.esta_vacia():
            leidos.append(comandos.desencolar())

        self.assertEqual(leidos, ["esperar", "mover E"])

    def test_sc206_el_log_de_p1_se_lee_igual(self):
        from crypta.Adaptadores.RegistroPartida import leer_registro
        from tests.datos.grabar_esperado_p1 import RUTA_LOG

        _, comandos = leer_registro(RUTA_LOG)
        leidos = []
        while not comandos.esta_vacia():
            leidos.append(comandos.desencolar())

        self.assertEqual(leidos,
                         [linea for linea
                          in self.lineas_despues_del_separador(RUTA_LOG)
                          if linea.strip()])

    def test_hu3_15_fr223_la_reproduccion_da_la_misma_partida(self):
        from crypta.Adaptadores.RegistroPartida import leer_registro
        from crypta.bench.oraculo_linea import serializar_estado
        from tests.ayudas_cripta import (
            FuenteContadora, controlador_sintetico, datos_generales)

        def fuente():
            esqueleto = pasillo()
            return FuenteContadora(
                esqueleto, generales=datos_generales(esqueleto,
                                                     presupuesto=1000))

        controlador = controlador_sintetico(
            fuente(), self.carpeta,
            ["mover E", "mover E", "mover E", "mover O", "mover O", "mover O",
             "ir a 4", "esperar"])
        controlador.iniciar()
        controlador.gestor_contenido.cerrar()
        ruta = os.path.join(self.carpeta, "partida.log")
        self.assertIn("# ir a 4", self.lineas_despues_del_separador(ruta))

        with tempfile.TemporaryDirectory() as otra:
            repeticion = controlador_sintetico(fuente(), otra, [])
            partida = repeticion.partida
            gestor = repeticion.gestor_contenido
            gestor.garantizar_sala(partida.id_sala_inicial)
            partida.iniciar()
            _, comandos = leer_registro(ruta)

            while not comandos.esta_vacia():
                ejecutar_comando(partida, comandos.desencolar(),
                                 gestor.garantizar_sala)

            gestor.cerrar()

        self.assertEqual(partida.reloj, controlador.partida.reloj)
        self.assertEqual(partida.resultado, controlador.partida.resultado)
        self.assertEqual(serializar_estado(partida),
                         serializar_estado(controlador.partida))


if __name__ == "__main__":
    unittest.main()
