"""Equivalencia de la línea de tiempo con la partida viva (capacidad 004, T025).

FR-421 y SC-402: en partidas sintéticas generadas por semilla (al menos 20,
con pergaminos), el 100 % de las consultas coincide con el estado obtenido
jugando, para al menos tres valores de K. Un K mayor que la cantidad de
acciones deja solo el punto inicial: es la alternativa sin puntos de control.

El oráculo son los resúmenes que se tomaron de la partida viva mientras se
jugaba (crypta/bench/oraculo_linea.py): en cada decisión del jugador
(`acción #k` e `instante <t>`) y en el instante de cada evento.
"""

import random
import unittest

from tests.test_linea_tiempo import Jugada, con_pergaminos_en_mano
from tests.ayudas_cripta import comandos_al_azar


SEMILLAS = range(100, 120)            # 20 partidas
VALORES_DE_K = (1, 10, 22, 10 ** 6)   # el último: solo el punto inicial
COMANDOS = 150
PERGAMINOS_EN_MANO = 3


class TestEquivalenciaConLaPartidaViva(unittest.TestCase):
    """SC-402 (FR-421)."""

    def test_fr421_sc402_todas_las_consultas_coinciden(self):
        partidas_con_pergamino = 0

        for semilla in SEMILLAS:
            for k in VALORES_DE_K:
                cripta = con_pergaminos_en_mano(PERGAMINOS_EN_MANO, semilla)
                jugada = Jugada(k, cripta=cripta, comandos=comandos_al_azar(
                    cripta.partida, random.Random(semilla), COMANDOS))
                try:
                    if k == VALORES_DE_K[0] and any(
                            jugada.linea.entradas.obtener(i).tipo == "ajuste"
                            for i in range(len(jugada.linea.entradas))):
                        partidas_con_pergamino += 1

                    if k == VALORES_DE_K[-1]:
                        self.assertEqual(len(jugada.linea.puntos), 1)

                    comparadas = 0
                    for i in range(len(jugada.oraculo)):
                        entrada = jugada.oraculo.obtener(i)
                        if entrada.pedido.startswith("acción") or entrada.es_evento:
                            with self.subTest(semilla=semilla, k=k, pedido=entrada.pedido):
                                self.assertEqual(jugada.consultar(entrada.pedido),
                                                 entrada.texto)
                            comparadas += 1

                    self.assertGreater(comparadas, 50)
                finally:
                    jugada.cerrar()

        # Al menos la mitad de las partidas usó pergaminos (SC-402: «con
        # pergaminos»).
        self.assertGreaterEqual(partidas_con_pergamino, len(SEMILLAS) // 2)


if __name__ == "__main__":
    unittest.main()
