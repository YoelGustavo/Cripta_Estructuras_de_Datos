"""Pruebas del --bench (Fase 8). Todas las del bench van en este archivo,
por secciones (B1 agenda, B2...). No miden tiempos (dependen de la
máquina): revisan que lo que se mide sea correcto y comparable."""

import io
import random
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from crypta import main as programa
from crypta.bench import bench
from crypta.bench.bench_agenda import (
    AGENDAS,
    AgendaVectorOrdenado,
    AgendaVectorSinOrden,
    costo_cancelar,
    costo_turno,
    hacer_turnos,
    llenar,
)
from crypta.bench.medicion import formato_tiempo, medir, tabla
from crypta.Modelo.Agenda import Agenda


# ======================================================================
# B1: la base del bench (medicion.py y bench.py)
# ======================================================================

class TestMedicion(unittest.TestCase):

    def test_medir_devuelve_el_mejor_tiempo(self):
        # perf_counter da inicio y fin de cada vuelta: duran 0.3, 0.1 y 0.2.
        tiempos = iter([0.0, 0.3, 1.0, 1.1, 2.0, 2.2])

        with patch("crypta.bench.medicion.time.perf_counter",
                   side_effect=lambda: next(tiempos)):
            mejor = medir(lambda: None, repeticiones=3)

        self.assertAlmostEqual(mejor, 0.1)

    def test_formato_tiempo_elige_la_unidad(self):
        self.assertEqual(formato_tiempo(0.0000123), "12.3 µs")
        self.assertEqual(formato_tiempo(0.00456), "4.56 ms")
        self.assertEqual(formato_tiempo(1.2), "1.20 s")

    def test_tabla_alinea_las_columnas(self):
        texto = tabla("T", ("n", "a"), [("10", "1.0 µs"), ("1000", "12.0 µs")])
        lineas = texto.splitlines()

        self.assertEqual(lineas[0], "T")
        self.assertEqual(len(set(len(l) for l in lineas[1:])), 1)


class TestEjecutarBench(unittest.TestCase):

    def correr(self, *nombres):
        lineas = []
        bench.ejecutar(list(nombres) or None, rapido=True, salida=lineas.append)
        return "\n".join(str(l) for l in lineas)

    def test_corre_solo_las_secciones_pedidas(self):
        texto = self.correr("agenda")

        self.assertIn("=== Agenda de eventos", texto)
        self.assertNotIn("=== Guardado", texto)

    def test_una_seccion_que_no_existe_se_rechaza(self):
        with self.assertRaises(ValueError) as contexto:
            self.correr("agendaa")

        self.assertIn("agenda", str(contexto.exception))

    def test_main_bench_no_crea_la_vista(self):
        with patch("crypta.bench.bench.ejecutar") as ejecutar, \
                patch("crypta.main.VistaConsola",
                      side_effect=AssertionError("--bench creó la vista")), \
                patch.object(sys, "argv", ["crypta", "--bench"]), \
                redirect_stdout(io.StringIO()):
            codigo = programa.main()

        self.assertEqual(codigo, 0)
        ejecutar.assert_called_once_with()


# ======================================================================
# B1: la agenda contra las alternativas descartadas (§4.1)
# ======================================================================

def recorrido(clase, semilla, pasos=400):
    """Programar, sacar y cancelar al azar; devuelve (tiempo, secuencia,
    actor) de cada evento que salió, en orden."""
    azar = random.Random(semilla)
    agenda = clase()
    vivos = llenar(agenda, 30, azar)
    salieron = []

    for _ in range(pasos):
        decision = azar.random()

        if decision < 0.6 and len(agenda) > 0:
            evento = agenda.siguiente()
            if evento is not None:
                salieron.append((evento.tiempo, evento.secuencia, evento.objetivo))
                vivos.append(agenda.programar(evento.tiempo + azar.choice((50, 66, 100)),
                                              "turno", evento.objetivo))
        elif decision < 0.8:
            vivos.append(agenda.programar(azar.randrange(1000), "turno", "nuevo"))
        elif vivos:
            agenda.cancelar(vivos.pop(azar.randrange(len(vivos))))

    return salieron


class TestAgendasComparables(unittest.TestCase):
    """Si las alternativas no dieran el MISMO orden que la Agenda del juego,
    compararlas no tendría sentido."""

    def test_las_tres_dan_el_mismo_orden(self):
        for semilla in range(5):
            esperado = recorrido(Agenda, semilla)

            self.assertGreater(len(esperado), 100)
            self.assertEqual(recorrido(AgendaVectorOrdenado, semilla), esperado)
            self.assertEqual(recorrido(AgendaVectorSinOrden, semilla), esperado)

    def test_empates_por_secuencia(self):
        for clase in (AgendaVectorOrdenado, AgendaVectorSinOrden):
            agenda = clase()
            a = agenda.programar(10, "a")
            b = agenda.programar(10, "b")
            agenda.programar(5, "c")

            self.assertEqual([agenda.siguiente().tipo for _ in range(3)],
                             ["c", "a", "b"])
            self.assertIsNone(agenda.siguiente())

    def test_los_turnos_mantienen_la_cantidad_de_pendientes(self):
        for _, clase in AGENDAS:
            agenda = clase()
            azar = random.Random(1)
            llenar(agenda, 50, azar)
            hacer_turnos(agenda, 200, azar)

            self.assertEqual(len(agenda), 50)

    def test_los_costos_son_tiempos_positivos(self):
        for _, clase in AGENDAS:
            self.assertGreater(costo_turno(clase, 20, 50, repeticiones=1), 0)
            self.assertGreater(costo_cancelar(clase, 20, 5, repeticiones=1), 0)

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench.bench_agenda.ejecutar(rapido=True)

        self.assertEqual(texto.count("AGENDA DE EVENTOS"), 2)
        for nombre, _ in AGENDAS:
            self.assertIn(nombre, texto)


if __name__ == "__main__":
    unittest.main()
