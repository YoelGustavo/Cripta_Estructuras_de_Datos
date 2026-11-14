"""Pruebas de la búsqueda binaria propia (capacidad 004, T004; research D5).

Habilita FR-403: `historia <t>` ubica la primera decisión con reloj ≥ t sin
recorrer todas.
"""

import math
import unittest

from crypta.estructuras.BusquedaBinaria import primera_no_menor
from crypta.estructuras.Vector import Vector


def vector_de(*valores):
    vector = Vector()
    for valor in valores:
        vector.agregar(valor)
    return vector


def identidad(valor):
    return valor


class TestPrimeraNoMenor(unittest.TestCase):
    """`primera_no_menor(vector, valor, clave)`: la primera posición cuya clave
    es ≥ valor en un `Vector` ordenado por clave, o `len(vector)` si no hay
    ninguna (FR-403, research D5)."""

    def test_vector_vacio_da_0(self):
        self.assertEqual(primera_no_menor(Vector(), 5, identidad), 0)

    def test_un_elemento(self):
        vector = vector_de(10)
        self.assertEqual(primera_no_menor(vector, 3, identidad), 0)
        self.assertEqual(primera_no_menor(vector, 10, identidad), 0)
        self.assertEqual(primera_no_menor(vector, 11, identidad), 1)

    def test_empates_dan_la_primera_posicion(self):
        vector = vector_de(1, 4, 4, 4, 9)
        self.assertEqual(primera_no_menor(vector, 4, identidad), 1)
        self.assertEqual(primera_no_menor(vector, 2, identidad), 1)
        self.assertEqual(primera_no_menor(vector, 5, identidad), 4)

    def test_valor_mayor_que_todos_da_el_largo(self):
        vector = vector_de(1, 2, 3)
        self.assertEqual(primera_no_menor(vector, 99, identidad), 3)

    def test_valor_menor_que_todos_da_0(self):
        vector = vector_de(5, 6, 7)
        self.assertEqual(primera_no_menor(vector, -1, identidad), 0)

    def test_usa_la_clave_de_cada_elemento(self):
        vector = vector_de((0, "a"), (100, "b"), (250, "c"))
        clave = lambda par: par[0]
        self.assertEqual(primera_no_menor(vector, 100, clave), 1)
        self.assertEqual(primera_no_menor(vector, 101, clave), 2)

    def test_comparaciones_logaritmicas(self):
        """Con n = 1 000, a lo sumo ⌈log₂(n + 1)⌉ + 1 consultas de la clave
        para cualquier valor (FR-403: no recorre todas las decisiones)."""
        n = 1000
        vector = Vector(n)
        for i in range(n):
            vector.agregar(3 * i)

        limite = math.ceil(math.log2(n + 1)) + 1

        for valor in (-5, 0, 1, 1500, 2997, 2998, 5000):
            llamadas = [0]

            def clave(elemento):
                llamadas[0] += 1
                return elemento

            esperado = next((i for i in range(n) if 3 * i >= valor), n)
            self.assertEqual(primera_no_menor(vector, valor, clave), esperado)
            self.assertLessEqual(llamadas[0], limite, f"valor {valor}")


if __name__ == "__main__":
    unittest.main()
