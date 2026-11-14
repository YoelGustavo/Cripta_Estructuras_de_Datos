"""Pruebas de la línea de tiempo (capacidad 004).

Fase 2 (T005): lo que usan todas las historias. El historial sin límite, el
tope de tiempo y el callback de `Partida`, y la copia de una partida para
los puntos de control (research D3, D9; FR-407, FR-422, FR-426).
"""

import copy
import random
import unittest

from crypta.bench.oraculo_linea import serializar_estado
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Historial import Historial, RegistroAccion
from crypta.Modelo.Partida import TURNO_JUGADOR, AccionInvalida
from tests.ayudas_cripta import (
    catalogo, comando_al_azar, contenido, ficha_cazador, partida_con_pergaminos,
    partida_sintetica, sala, salida,
)


class _Caja:
    def __init__(self):
        self.valor = 0


def jugar(partida, garantizar, comandos):
    """Ejecuta los comandos y salta los que el juego rechaza."""
    for comando in comandos:
        if partida.terminada:
            return
        try:
            ejecutar_comando(partida, comando, garantizar)
        except (ComandoInvalido, AccionInvalida):
            pass
        except RuntimeError:
            # Una copia que intenta entrar en una sala que la partida viva
            # nunca cargó (solo en _garantizar_desde): no hay red.
            pass


def jugar_al_azar(partida, garantizar, semilla, cantidad):
    azar = random.Random(semilla)
    for _ in range(cantidad):
        if partida.terminada:
            return
        jugar(partida, garantizar, [comando_al_azar(partida, azar)])


def partida_con_cazador():
    """Tres salas en fila; un cazador en la sala del jugador, así su primer
    turno crea la búsqueda compartida (`Perseguidor`)."""
    esqueleto = [sala(1, {"E": salida(2)}),
                 sala(2, {"O": salida(1), "E": salida(3)}),
                 sala(3, {"O": salida(2)})]
    contenidos = [contenido(1, enemigos=(("c-1", "ent_cazador"),))]
    partida = partida_sintetica(esqueleto, contenidos,
                                catalogo(ficha_cazador(rango=1000)))
    partida.jugador.vida_max = partida.jugador.vida = 500
    for _ in range(3):
        partida.esperar()
    return partida


class TestBaseLinea(unittest.TestCase):
    """T005: base común de la línea de tiempo."""

    # --- Historial sin límite (D2; FR-423) ---------------------------------

    def test_fr423_historial_sin_limite(self):
        historial = Historial(limite=None)
        caja = _Caja()

        for i in range(1000):
            historial.registrar(RegistroAccion(f"a{i}"))
            historial.registrar_cambio(Cambio.de_atributo("v", caja, "valor", caja.valor))
            caja.valor = i + 1

        self.assertEqual(len(historial), 1000)

        while historial.puede_deshacer():
            historial.deshacer_ultima()

        self.assertEqual(caja.valor, 0)

    def test_historial_sigue_con_limite_5_por_omision(self):
        historial = Historial()
        for i in range(8):
            historial.registrar(RegistroAccion(f"a{i}"))
        self.assertEqual(len(historial), 5)

        with self.assertRaises(ValueError):
            Historial(0)

    # --- Tope de tiempo y callback (D9; FR-401, FR-426) --------------------

    def test_fr426_tope_y_callback_por_omision_no_cambian_el_juego(self):
        a = partida_con_pergaminos(semilla=11)
        b = partida_con_pergaminos(semilla=11)
        try:
            self.assertIsNone(a.partida.tope_tiempo)
            self.assertIsNone(a.partida.al_ejecutar_evento)

            vistos = []
            b.partida.tope_tiempo = None
            b.partida.al_ejecutar_evento = lambda partida, evento: vistos.append(evento)

            jugar_al_azar(a.partida, a.garantizar, 5, 60)
            jugar_al_azar(b.partida, b.garantizar, 5, 60)

            self.assertEqual(serializar_estado(a.partida), serializar_estado(b.partida))
            self.assertGreater(len(vistos), 0)
        finally:
            a.cerrar()
            b.cerrar()

    def test_fr426_callback_una_vez_por_evento_que_no_es_del_jugador(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            vistos = []
            partida.al_ejecutar_evento = lambda p, evento: vistos.append(evento)

            antes = partida.agenda.siguiente_secuencia
            jugar(partida, cripta.garantizar, ["mover E", "esperar", "esperar"])

            self.assertTrue(all(e.tipo != TURNO_JUGADOR for e in vistos))
            self.assertTrue(all(e.secuencia < partida.agenda.siguiente_secuencia
                                for e in vistos))
            self.assertEqual(len(vistos), len({id(e) for e in vistos}))
            self.assertGreater(partida.agenda.siguiente_secuencia, antes)
        finally:
            cripta.cerrar()

    def test_fr401_con_tope_se_detiene_antes_del_primer_evento_posterior(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E"])     # sala 2, con el errante
            inicio = partida.reloj
            tope = inicio + 40                                  # en medio de «esperar» (100)

            partida.tope_tiempo = tope
            partida.esperar()

            self.assertLessEqual(partida.reloj, tope)
            siguiente = min((e.tiempo for e in partida.agenda.recorrer_pendientes()))
            self.assertGreater(siguiente, tope)
        finally:
            cripta.cerrar()

    def test_fr401_con_tope_en_la_decision_se_detiene_antes_de_decidir(self):
        """Si el siguiente evento es el turno del jugador en t, el estado es
        el de justo antes de esa decisión: los eventos de t que vienen
        después en la agenda no se ejecutan."""
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E"])
            turno = partida.reloj + partida.jugador.intervalo(100)

            partida.tope_tiempo = turno
            partida.esperar()

            self.assertEqual(partida.reloj, turno)
            pendientes = [e for e in partida.agenda.recorrer_pendientes()]
            self.assertTrue(all(e.tiempo > turno or e.tipo != TURNO_JUGADOR
                                for e in pendientes))
        finally:
            cripta.cerrar()

    def test_fr407_deshacer_una_accion_a_medias_deja_todo_igual(self):
        """El tope deja la acción a medias; sus cambios están en su
        `RegistroAccion` y deshacerla restaura el estado (D2, D9). El número
        de secuencia de la agenda no lo rebobina el historial de P1: lo
        restaura el sello de la consulta (D8, T019)."""
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E", "esperar"])
            antes = serializar_estado(partida)
            secuencia = partida.agenda.siguiente_secuencia

            partida.tope_tiempo = partida.reloj + 30
            partida.esperar()
            partida.tope_tiempo = None
            partida.estado.historial.deshacer_ultima()
            partida.agenda._siguiente_secuencia = secuencia      # lo que hace el sello (D8)

            self.assertEqual(serializar_estado(partida), antes)
        finally:
            cripta.cerrar()

    # --- Copia para los puntos de control (D3; FR-422) ---------------------

    def test_fr422_la_copia_comparte_lo_inmutable(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E", "mover E", "mover S"])
            copia = copy.deepcopy(partida)

            self.assertIs(copia._fichas, partida._fichas)

            originales = partida.mapa.obtener_todas()
            copias = copia.mapa.obtener_todas()
            cargadas = 0

            for i in range(len(originales)):
                original = originales.obtener(i)
                copiada = copias.obtener(i)
                self.assertIsNot(copiada, original)
                self.assertEqual(copiada.id, original.id)

                if original.contenido_cargado():
                    cargadas += 1
                    self.assertIs(copiada.contenido, original.contenido)

            self.assertGreaterEqual(cargadas, 3)
        finally:
            cripta.cerrar()

    def test_fr422_la_copia_deja_fuera_lo_que_no_es_estado(self):
        partida = partida_con_cazador()
        partida.al_ejecutar_evento = lambda p, e: None
        self.assertIsNotNone(partida._perseguidor)

        copia = copy.deepcopy(partida)

        self.assertIsNone(copia._perseguidor)
        self.assertIsNone(copia.al_ejecutar_evento)
        self.assertIsNotNone(partida.al_ejecutar_evento)
        self.assertIsNot(copia.bitacora, partida.bitacora)
        self.assertEqual(len(copia.bitacora), 0)
        self.assertGreater(len(partida.bitacora), 0)
        self.assertIsNot(copia.estado.historial, partida.estado.historial)
        self.assertEqual(len(copia.estado.historial), 0)
        self.assertIsNone(copia.estado.historial._limite)

        salas = copia.mapa.obtener_todas()
        for i in range(len(salas)):
            puertas = salas.obtener(i).puertas()
            for j in range(len(puertas)):
                self.assertIsNone(puertas.obtener(j).estado.observador)

        vivas = partida.mapa.obtener_todas().obtener(0).puertas()
        self.assertIs(vivas.obtener(0).estado.observador, partida._perseguidor)

    def test_fr422_la_copia_serializa_igual(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar_al_azar(partida, cripta.garantizar, 3, 40)
            self.assertEqual(serializar_estado(copy.deepcopy(partida)),
                             serializar_estado(partida))
        finally:
            cripta.cerrar()

    def test_fr407_jugar_sobre_la_copia_no_toca_el_original(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar_al_azar(partida, cripta.garantizar, 4, 30)
            antes = serializar_estado(partida)
            bitacora = len(partida.bitacora)
            azar = partida.azar.getstate()

            copia = copy.deepcopy(partida)
            garantizar_copia = _garantizar_desde(partida, copia)
            jugar_al_azar(copia, garantizar_copia, 9, 20)

            self.assertGreater(copia.acciones_jugador, partida.acciones_jugador)
            self.assertEqual(serializar_estado(partida), antes)
            self.assertEqual(len(partida.bitacora), bitacora)
            self.assertEqual(partida.azar.getstate(), azar)
        finally:
            cripta.cerrar()

    def test_fr422_copia_de_300_salas_sin_subir_el_limite_de_recursion(self):
        """El mapa se copia en dos pasadas (D3): sin eso, `deepcopy` baja por
        la cadena de salas vecinas y pasa el límite de recursión de Python."""
        from crypta.bench.bench_ciclo import CATALOGO, partida_de_carga

        partida = partida_de_carga(20, CATALOGO.get, semilla=1, cantidad_salas=300)
        copia = copy.deepcopy(partida)
        self.assertEqual(serializar_estado(copia), serializar_estado(partida))


def _garantizar_desde(viva, copia):
    """Carga en la copia el contenido de una sala tomándolo de la partida
    viva, sin red (research D7)."""
    def garantizar(id_sala):
        sala_copia = copia.mapa.obtener_sala(id_sala)
        if not sala_copia.contenido_cargado():
            sala_viva = viva.mapa.obtener_sala(id_sala)
            if sala_viva.contenido_cargado():
                sala_copia.asignar_contenido(sala_viva.contenido)
    return garantizar


if __name__ == "__main__":
    unittest.main()
