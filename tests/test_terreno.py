"""Pruebas de la capacidad 001, historia 1: terreno con costo.

Especificación: specs/001-terreno-cazador/spec.md. Cada prueba cita su FR y
su escenario (HU1-n = escenario n de la historia 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_terreno
"""

import json
import os
import unittest

from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.Modelo.Efecto import VELOCIDAD, Efecto
from crypta.Modelo.Partida import FIN_VELOCIDAD
from tests.ayudas_cripta import (
    SIN_DECLARAR, buscar_enemigo, catalogo, contenido, ficha_enemigo,
    ficha_errante,
    ficha_rastreador, mapa_de, nuevo_jugador, partida_sintetica, sala,
    salida,
)
from tests.datos.grabar_esperado_p1 import (
    RUTA_ESPERADO, RUTA_LOG, repetir_partida_p1,
)


class TestCompatibilidadP1(unittest.TestCase):
    """FR-008, HU1-8: una cripta sin ningún campo costo se juega exactamente
    igual que en la primera parte.

    Repite `tests/datos/p1_partida.log`, grabado con el código de la primera
    parte, sobre la copia fija `p1_cripta-01.json` y `p1_catalogo.json`
    (copiada a una carpeta temporal; nunca usa `cache/`), sin red, y compara
    con `p1_esperado.json`: mismos instantes, eventos, mensajes, estado del
    generador aleatorio y resultado, después de cada comando y al final.

    Esta prueba pasa desde antes de la capacidad 001: protege lo que ya
    funciona."""

    @classmethod
    def setUpClass(cls):
        with open(RUTA_ESPERADO, encoding="utf-8") as archivo:
            cls.esperado = json.load(archivo)

        cls.obtenido = repetir_partida_p1()

    def test_fr008_los_datos_fijos_no_declaran_costos(self):
        """FR-008: la copia fija es de la primera parte, sin campo costo."""
        carpeta = os.path.dirname(RUTA_LOG)

        for nombre in ("p1_cripta-01.json", "p1_catalogo.json"):
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as archivo:
                self.assertNotIn('"costo"', archivo.read(), nombre)

    def test_fr008_se_repiten_todos_los_comandos(self):
        """FR-008: el registro se repite completo, sin comandos rechazados."""
        self.assertEqual(len(self.obtenido["comandos"]),
                         len(self.esperado["comandos"]))

    def test_fr008_mismo_estado_despues_de_cada_comando(self):
        """FR-008: mismos instantes, eventos, mensajes y llamadas al azar
        después de cada comando."""
        for esperado, obtenido in zip(self.esperado["comandos"],
                                      self.obtenido["comandos"]):
            with self.subTest(numero=esperado["numero"],
                              comando=esperado["comando"]):
                self.assertEqual(obtenido, esperado)

    def test_fr008_mismo_resultado_final(self):
        """FR-008: mismo reloj, sala, vida, resultado y estado del azar al
        terminar."""
        self.assertEqual(self.obtenido["final"], self.esperado["final"])
        self.assertTrue(self.obtenido["final"]["terminada"])


def dos_salas(costo_ida=None, costo_vuelta=None, **ida):
    """Salas 1 y 2 unidas por 1 —E→ 2 y 2 —O→ 1. Un costo None no se
    declara."""
    def con_costo(destino, costo, **otros):
        if costo is None:
            return salida(destino, **otros)
        return salida(destino, costo=costo, **otros)

    return [
        sala(1, {"E": con_costo(2, costo_ida, **ida)}),
        sala(2, {"O": con_costo(1, costo_vuelta)}),
    ]


def costos(mapa):
    """(costo de 1 —E→ 2, costo de 2 —O→ 1)."""
    return (mapa.obtener_sala(1).obtener_puerta("E").costo,
            mapa.obtener_sala(2).obtener_puerta("O").costo)


class TestCostoSalidas(unittest.TestCase):
    """FR-001, FR-002, FR-010 (carga de HU1-12 y HU1-13): cómo se lee y se
    valida el costo de cada salida del esqueleto
    (contracts/datos-servicio.md)."""

    def test_fr001_sin_costo_vale_100(self):
        """FR-001: ningún lado declara costo → 100 en ambos sentidos."""
        self.assertEqual(costos(mapa_de(dos_salas())), (100, 100))

    def test_fr001_costo_null_cuenta_como_no_declarado(self):
        """FR-001: "costo": null es lo mismo que no traer el campo."""
        esqueleto = [sala(1, {"E": salida(2, costo=None)}),
                     sala(2, {"O": salida(1, costo=None)})]
        self.assertEqual(costos(mapa_de(esqueleto)), (100, 100))

    def test_fr001_null_de_un_lado_y_250_del_otro(self):
        """FR-001, FR-010: un lado null y el otro 250 → 250, sin rechazo."""
        esqueleto = [sala(1, {"E": salida(2, costo=None)}),
                     sala(2, {"O": salida(1, costo=250)})]
        self.assertEqual(costos(mapa_de(esqueleto)), (250, 250))

    def test_fr010_solo_un_lado_declara_vale_para_los_dos(self):
        """FR-002, FR-010, HU1-13 (carga): solo un lado declara 250 → 250 en
        ambos sentidos y la cripta no se rechaza."""
        self.assertEqual(costos(mapa_de(dos_salas(costo_ida=250))),
                         (250, 250))
        self.assertEqual(costos(mapa_de(dos_salas(costo_vuelta=250))),
                         (250, 250))

    def test_fr002_ambos_lados_iguales(self):
        """FR-002: ambos lados declaran 250 → 250."""
        self.assertEqual(costos(mapa_de(dos_salas(250, 250))), (250, 250))

    def test_fr002_los_dos_lados_comparten_el_costo(self):
        """FR-002: es la misma salida, así que el costo es uno solo."""
        mapa = mapa_de(dos_salas(250))
        ida = mapa.obtener_sala(1).obtener_puerta("E")
        vuelta = mapa.obtener_sala(2).obtener_puerta("O")
        self.assertIs(ida.estado, vuelta.estado)

    def test_fr001_salida_sin_vuelta_conserva_su_costo(self):
        """FR-001: una salida sin pareja queda con su costo o con 100."""
        esqueleto = [sala(1, {"E": salida(2, costo=300), "N": salida(3)}),
                     sala(2), sala(3)]
        mapa = mapa_de(esqueleto)
        self.assertEqual(mapa.obtener_sala(1).obtener_puerta("E").costo, 300)
        self.assertEqual(mapa.obtener_sala(1).obtener_puerta("N").costo, 100)

    def test_fr001_el_costo_es_de_solo_lectura(self):
        """FR-001: el costo sale del esqueleto y no se cambia en la
        partida."""
        puerta = mapa_de(dos_salas(250)).obtener_sala(1).obtener_puerta("E")
        with self.assertRaises(AttributeError):
            puerta.costo = 1

    def test_fr010_lados_distintos_se_rechazan(self):
        """FR-010, HU1-12: lados 200 y 300 → DatosInvalidos, con las dos
        salas, las dos direcciones y los dos costos."""
        with self.assertRaises(DatosInvalidos) as contexto:
            mapa_de(dos_salas(200, 300))

        mensaje = str(contexto.exception)
        self.assertIn("La salida entre las salas 1 (E) y 2 (O)", mensaje)
        self.assertIn("costos distintos", mensaje)
        self.assertIn("200", mensaje)
        self.assertIn("300", mensaje)

    def test_fr010_costos_invalidos_se_rechazan(self):
        """FR-010, HU1-12: costo 0, negativo, 2.5, 250.0, true y "250" →
        DatosInvalidos que nombra la sala, la dirección y el valor."""
        for valor in (0, -5, 2.5, 250.0, True, False, "250"):
            with self.subTest(costo=valor):
                with self.assertRaises(DatosInvalidos) as contexto:
                    mapa_de(dos_salas(costo_ida=valor))

                mensaje = str(contexto.exception)
                self.assertIn("La salida E de la sala 1", mensaje)
                self.assertIn("costo inválido", mensaje)
                self.assertIn(str(valor), mensaje)

    def test_fr010_tambien_se_valida_el_lado_de_vuelta(self):
        """FR-010: el valor inválido puede venir de cualquiera de los
        lados."""
        with self.assertRaises(DatosInvalidos) as contexto:
            mapa_de(dos_salas(costo_ida=250, costo_vuelta=0))

        self.assertIn("La salida O de la sala 2", str(contexto.exception))

    def test_fr010_datos_invalidos_no_es_un_comando_invalido(self):
        """FR-010, FR-011: DatosInvalidos no hereda de ValueError ni de
        RuntimeError, para que nadie la confunda con un comando inválido o
        un error de red."""
        self.assertFalse(issubclass(DatosInvalidos, ValueError))
        self.assertFalse(issubclass(DatosInvalidos, RuntimeError))
        self.assertTrue(issubclass(DatosInvalidos, Exception))


class Observador:
    """Anota cada aviso de una puerta y el valor de cerrada en ese
    momento."""

    def __init__(self):
        self.avisos = []

    def puerta_cambio(self, estado):
        self.avisos.append((estado, estado.cerrada))


class TestIndicesYEntradas(unittest.TestCase):
    """Habilita FR-014, FR-018, FR-019 y FR-036: índices densos, entradas
    de cada sala, extremos de cada salida y aviso de cambio de puerta."""

    def setUp(self):
        # 1 —E→ 2, 2 —O→ 1, 2 —N→ 3 sin vuelta, 3 —S→ 1 sin vuelta.
        # Las salas se dan desordenadas a propósito.
        self.mapa = mapa_de([
            sala(3, {"S": salida(1)}),
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1), "N": salida(3)}),
        ])

    def puerta(self, id_sala, direccion):
        return self.mapa.obtener_sala(id_sala).obtener_puerta(direccion)

    def test_indices_densos_en_orden_del_mapa(self):
        """FR-014, FR-036: índices 0..V−1 según el recorrido en orden."""
        self.assertEqual(self.mapa.cantidad_salas(), 3)

        for indice, id_sala in enumerate((1, 2, 3)):
            sala_mapa = self.mapa.obtener_sala(id_sala)
            self.assertEqual(sala_mapa.indice, indice)
            self.assertIs(self.mapa.sala_por_indice(indice), sala_mapa)

    def test_indices_sin_repetir_con_ids_salteados(self):
        """FR-036: los índices no dependen de los id."""
        mapa = mapa_de([sala(40), sala(7), sala(1000), sala(12)])
        indices = [mapa.obtener_sala(id_sala).indice
                   for id_sala in (7, 12, 40, 1000)]
        self.assertEqual(indices, [0, 1, 2, 3])

    def entradas(self, id_sala):
        """[(id de la sala origen, dirección de la salida)] de una sala."""
        destino = self.mapa.obtener_sala(id_sala)
        resultado = []

        for i in range(len(destino.entradas)):
            puerta, origen = destino.entradas.obtener(i)
            self.assertIs(origen.obtener_puerta(origen.direccion_de(puerta)),
                          puerta)
            self.assertIs(puerta.sala_destino_ref, destino)
            resultado.append((origen.id, origen.direccion_de(puerta)))

        return resultado

    def test_entradas_de_cada_sala(self):
        """FR-014, FR-036: las entradas de x son las salidas y→x, incluidas
        las que no tienen vuelta."""
        self.assertCountEqual(self.entradas(1), [(2, "O"), (3, "S")])
        self.assertCountEqual(self.entradas(2), [(1, "E")])
        self.assertCountEqual(self.entradas(3), [(2, "N")])

    def test_extremos_de_cada_salida(self):
        """FR-018: los extremos de una salida son sus dos salas."""
        sala_1, sala_2, sala_3 = (self.mapa.obtener_sala(i)
                                  for i in (1, 2, 3))

        self.assertCountEqual(self.puerta(1, "E").estado.extremos,
                              (sala_1, sala_2))
        self.assertIs(self.puerta(1, "E").estado, self.puerta(2, "O").estado)
        self.assertCountEqual(self.puerta(2, "N").estado.extremos,
                              (sala_2, sala_3))
        self.assertCountEqual(self.puerta(3, "S").estado.extremos,
                              (sala_3, sala_1))

    def test_sin_observador_no_pasa_nada(self):
        """FR-019: sin búsqueda vigente, abrir y cerrar funcionan igual."""
        puerta = self.puerta(1, "E")
        self.assertIsNone(puerta.estado.observador)
        puerta.cerrar()
        puerta.abrir()
        self.assertFalse(puerta.esta_cerrada())

    def test_avisa_solo_si_cerrada_cambia(self):
        """FR-018, FR-019: un aviso por cada cambio de valor, desde
        cualquiera de los dos lados; asignar el mismo valor no avisa."""
        ida, vuelta = self.puerta(1, "E"), self.puerta(2, "O")
        observador = Observador()
        ida.estado.observador = observador

        ida.abrir()                       # ya estaba abierta
        vuelta.cerrar()
        vuelta.cerrar()                   # ya estaba cerrada
        ida.cerrada = True                # setattr con el mismo valor
        ida.abrir()

        self.assertEqual(observador.avisos,
                         [(ida.estado, True), (ida.estado, False)])

    def test_avisa_al_abrir_al_cerrarse_sola_y_con_el_pergamino(self):
        """FR-018, FR-019: el comando abrir, el cierre automático y el
        pergamino (que vuelve atrás con setattr) avisan al observador."""
        partida = partida_sintetica(
            [sala(1, {"E": salida(2, cerrada=True, cierre_automatico=50)}),
             sala(2, {"O": salida(1)})],
            jugador=nuevo_jugador(pergaminos=1),
        )
        estado = partida.sala_actual().obtener_puerta("E").estado
        observador = Observador()
        estado.observador = observador

        partida.abrir("E")                # se abre y se cierra sola en 50
        self.assertEqual(observador.avisos,
                         [(estado, False), (estado, True)])

        self.assertTrue(partida.usar_pergamino())
        self.assertEqual(observador.avisos,
                         [(estado, False), (estado, True),
                          (estado, False), (estado, True)])


def ida_y_vuelta(costo, desde=1, hasta=2):
    """Salas `desde` —E→ `hasta` y `hasta` —O→ `desde`; solo el lado de
    ida declara el costo (o ninguno, con SIN_DECLARAR)."""
    return [sala(desde, {"E": salida(hasta, costo=costo)}),
            sala(hasta, {"O": salida(desde)})]


class TestMovimientoConCosto(unittest.TestCase):
    """Historia 1: todo movimiento tarda según el costo de la salida; lo
    demás queda como en P1."""

    def test_hu1_1_el_jugador_tarda_el_costo_de_la_salida(self):
        """FR-001, FR-003, HU1-1: velocidad 100, salida de costo 250 → llega
        a la sala destino y su siguiente acción queda en 250."""
        partida = partida_sintetica(ida_y_vuelta(250))

        partida.mover("E")

        self.assertEqual(partida.jugador.sala_actual, 2)
        self.assertEqual(partida.jugador.evento_siguiente.tiempo, 250)
        self.assertEqual(partida.reloj, 250)

    def test_hu1_2_sin_costo_tarda_100_como_en_p1(self):
        """FR-001, FR-003, HU1-2: salida sin campo costo → 100 unidades."""
        partida = partida_sintetica(ida_y_vuelta(SIN_DECLARAR))

        partida.mover("E")

        self.assertEqual(partida.jugador.evento_siguiente.tiempo, 100)

    def test_hu1_3_mismo_costo_en_ambos_sentidos(self):
        """FR-002, FR-003, HU1-3: salida de costo 250 entre 3 y 7; de 3 a 7
        y de 7 a 3 cuestan 250."""
        esqueleto = ida_y_vuelta(250, desde=3, hasta=7)

        de_3_a_7 = partida_sintetica(esqueleto, sala_inicial=3)
        de_3_a_7.mover("E")

        de_7_a_3 = partida_sintetica(esqueleto, sala_inicial=7)
        de_7_a_3.mover("O")

        self.assertEqual((de_3_a_7.jugador.sala_actual, de_3_a_7.reloj),
                         (7, 250))
        self.assertEqual((de_7_a_3.jugador.sala_actual, de_7_a_3.reloj),
                         (3, 250))

    def test_hu1_4_el_intervalo_nunca_es_0(self):
        """FR-003, FR-004, HU1-4: velocidad 150 y costo 1 →
        max(1, 1 * 100 // 150) = 1."""
        partida = partida_sintetica(ida_y_vuelta(1),
                                    jugador=nuevo_jugador(velocidad=150))

        partida.mover("E")

        self.assertEqual(partida.reloj, 1)

    def test_hu1_5_cambio_de_velocidad_a_mitad_del_movimiento(self):
        """FR-007, HU1-5: costo 300 en el instante 0 (programado en 300); en
        100 la velocidad pasa de 100 a 200 → reprogramado en
        100 + max(1, (300 − 100) * 100 // 200) = 200, con secuencia nueva."""
        partida = partida_sintetica(ida_y_vuelta(300))

        # En el instante 100 termina un efecto que valía −100: la velocidad
        # pasa de 100 a 200.
        efecto = Efecto(VELOCIDAD, valor=-100, hasta=100)
        fin = partida.agenda.programar(100, FIN_VELOCIDAD, efecto)

        partida.mover("E")                 # su evento: 300, secuencia fin+1

        evento = partida.jugador.evento_siguiente
        self.assertEqual(partida.jugador.velocidad, 200)
        self.assertEqual(evento.tiempo, 200)
        self.assertEqual(partida.reloj, 200)
        self.assertGreater(evento.secuencia, fin.secuencia + 1)

    def primera_decision(self, con_costos, semilla):
        """Errante y rastreador en la sala 1 (salidas de costo 250, 400 y
        300, o sin costo); el jugador se va por E a la sala 2 y cada enemigo
        decide una vez en el instante 100."""
        def costo(valor):
            return valor if con_costos else SIN_DECLARAR

        esqueleto = [
            sala(1, {"E": salida(2, costo=costo(250)),
                     "N": salida(3, costo=costo(400)),
                     "S": salida(4, costo=costo(300))}),
            sala(2, {"O": salida(1)}),
            sala(3, {"S": salida(1)}),
            sala(4, {"N": salida(1)}),
        ]
        partida = partida_sintetica(
            esqueleto,
            [contenido(1, enemigos=[("e-1", "ent_errante"),
                                    ("e-2", "ent_rastreador")])],
            catalogo(ficha_errante(), ficha_rastreador()),
            semilla=semilla,
        )

        partida.mover("E")

        errante = buscar_enemigo(partida, "e-1")
        rastreador = buscar_enemigo(partida, "e-2")
        return {
            "errante": (errante.sala_actual,
                        errante.evento_siguiente.tiempo),
            "rastreador": (rastreador.sala_actual,
                           rastreador.evento_siguiente.tiempo),
            "azar": partida.azar.getstate(),
        }

    def test_hu1_6_errante_y_rastreador_eligen_como_en_p1(self):
        """FR-004, FR-006, HU1-6: con y sin costos eligen el mismo destino y
        hacen las mismas llamadas al azar; solo cambia el instante de su
        siguiente acción (100 + costo de la salida elegida)."""
        costo_hacia = {2: 250, 3: 400, 4: 300}
        destinos_del_errante = []

        for semilla in range(1, 16):
            with self.subTest(semilla=semilla):
                con = self.primera_decision(True, semilla)
                sin = self.primera_decision(False, semilla)

                self.assertEqual(con["azar"], sin["azar"])

                destino, tiempo = con["errante"]
                self.assertEqual(sin["errante"], (destino, 200))
                self.assertEqual(tiempo, 100 + costo_hacia[destino])
                destinos_del_errante.append(destino)

                self.assertEqual(sin["rastreador"], (2, 200))
                self.assertEqual(con["rastreador"], (2, 350))

        # Las semillas cubren más de una salida del errante.
        self.assertLess(destinos_del_errante.count(destinos_del_errante[0]),
                        len(destinos_del_errante))

    def test_hu1_7_las_demas_acciones_conservan_su_costo(self):
        """FR-005, HU1-7: en una sala con salidas de costo 400, atacar,
        esperar, usar, equipar, recoger, soltar y abrir cuestan lo de
        P1 §2.3."""
        esqueleto = [
            sala(1, {"E": salida(2, costo=400),
                     "N": salida(3, costo=400, cerrada=True)}),
            sala(2, {"O": salida(1)}),
            sala(3, {"S": salida(1)}),
        ]
        fichas = catalogo(
            ficha_enemigo("ent_debil", "guardián", ataque=1),
            {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 2,
             "valor": 15, "ataque_bonus": 3},
            {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción",
             "peso": 1, "valor": 10, "cura": 8},
        )
        partida = partida_sintetica(
            esqueleto,
            [contenido(1, enemigos=[("e-1", "ent_debil", 40)],
                       objetos=["itm_pocion", "itm_daga"])],
            fichas,
        )
        enemigo = buscar_enemigo(partida, "e-1")

        acciones = [
            ("recoger", lambda: partida.recoger(0), 25),
            ("usar", partida.usar, 50),
            ("recoger", lambda: partida.recoger(0), 25),
            ("equipar", partida.equipar, 50),
            ("soltar", partida.soltar, 25),
            ("abrir", lambda: partida.abrir("N"), 50),
            ("esperar", partida.esperar, 100),
            ("atacar", lambda: partida.atacar(enemigo), 100),
        ]

        for nombre, accion, costo in acciones:
            with self.subTest(accion=nombre):
                antes = partida.reloj
                accion()
                self.assertFalse(partida.terminada)
                self.assertEqual(partida.reloj - antes, costo)

    def jugar(self, costo_e, costo_n, comandos):
        """Instantes en que le toca al jugador después de cada comando."""
        esqueleto = [
            sala(1, {"E": salida(2, costo=costo_e),
                     "N": salida(3, costo=costo_n)}),
            sala(2, {"O": salida(1)}),
            sala(3, {"S": salida(1)}),
        ]
        partida = partida_sintetica(esqueleto, semilla=11)
        instantes = []

        for comando in comandos:
            comando(partida)
            instantes.append(partida.reloj)

        return instantes

    def test_hu1_10_los_costos_salen_de_los_datos(self):
        """FR-024, HU1-10: dos criptas iguales salvo los costos, misma
        semilla y mismos comandos → los instantes siguen a los costos de
        cada una; ningún costo está escrito en el código."""
        comandos = [
            lambda p: p.mover("E"), lambda p: p.mover("O"),
            lambda p: p.esperar(), lambda p: p.mover("N"),
        ]

        self.assertEqual(self.jugar(250, 40, comandos),
                         [250, 500, 600, 640])
        self.assertEqual(self.jugar(150, 777, comandos),
                         [150, 300, 400, 1177])

    def test_hu1_13_solo_un_lado_declara_y_se_cruza_desde_el_otro(self):
        """FR-001, FR-010, HU1-13: solo el lado de la sala 3 declara 250; el
        jugador va de 7 a 3 → cuesta 250 y la cripta no se rechaza."""
        partida = partida_sintetica(ida_y_vuelta(250, desde=3, hasta=7),
                                    sala_inicial=7)

        partida.mover("O")

        self.assertEqual(partida.jugador.sala_actual, 3)
        self.assertEqual(partida.reloj, 250)


if __name__ == "__main__":
    unittest.main()
