"""Pruebas de la numeración de llaves (capacidad 003, research D1).

Habilitan FR-308 (las llaves se ordenan por id, comparado como texto) y
FR-320 (el resultado no depende del orden en que llegan los ids).

    python -m unittest -v tests.test_numeracion_llaves

Las listas de Python de este archivo son solo datos de entrada y valores
esperados; la numeración nunca las usa (principio I).
"""

import math
import random
import unittest

from crypta.estructuras.NumeracionLlaves import (NumeracionLlaves,
                                                  NumeracionPorInsercion)
from crypta.estructuras.Vector import Vector


def vector_de(valores):
    vector = Vector()

    for valor in valores:
        vector.agregar(valor)

    return vector


IDS_VARIADOS = [
    "itm_llave_b", "itm_llave_9", "itm_llave_A", "itm_llave_10",
    "itm_llave_b", "itm_llave_salida", "itm_llave_a", "itm_llave_9",
    "itm_llave", "Z", "itm_llave_a",
]


class TestNumeracionLlaves(unittest.TestCase):

    def test_len_cuenta_ids_distintos_D1(self):
        """D1: con repetidos, la numeración tiene un número por id distinto."""
        numeracion = NumeracionLlaves(vector_de(IDS_VARIADOS))

        self.assertEqual(len(numeracion), len(set(IDS_VARIADOS)))

    def test_numero_sigue_el_orden_por_id_FR_308(self):
        """FR-308: numero(a) < numero(b) ⇔ a < b como texto, carácter por
        carácter (mayúsculas antes que minúsculas, '1' antes que '9', un
        prefijo antes que lo que lo extiende)."""
        numeracion = NumeracionLlaves(vector_de(IDS_VARIADOS))
        distintos = set(IDS_VARIADOS)

        for a in distintos:
            for b in distintos:
                self.assertEqual(numeracion.numero(a) < numeracion.numero(b),
                                 a < b, (a, b))

        self.assertLess(numeracion.numero("itm_llave_10"),
                        numeracion.numero("itm_llave_9"))
        self.assertLess(numeracion.numero("itm_llave"),
                        numeracion.numero("itm_llave_10"))
        self.assertLess(numeracion.numero("itm_llave_A"),
                        numeracion.numero("itm_llave_a"))

    def test_numeros_son_0_a_k_menos_1_D1(self):
        numeracion = NumeracionLlaves(vector_de(IDS_VARIADOS))
        numeros = sorted(numeracion.numero(x) for x in set(IDS_VARIADOS))

        self.assertEqual(numeros, list(range(len(numeracion))))

    def test_id_de_invierte_numero_D1(self):
        numeracion = NumeracionLlaves(vector_de(IDS_VARIADOS))

        for x in IDS_VARIADOS:
            self.assertEqual(numeracion.id_de(numeracion.numero(x)), x)

    def test_id_ausente_da_none_D1(self):
        numeracion = NumeracionLlaves(vector_de(IDS_VARIADOS))

        self.assertIsNone(numeracion.numero("itm_llave_x"))
        self.assertIsNone(numeracion.numero(""))

    def test_sin_ids_D1(self):
        numeracion = NumeracionLlaves(Vector())

        self.assertEqual(len(numeracion), 0)
        self.assertIsNone(numeracion.numero("itm_llave_a"))

    def test_mismo_resultado_en_cualquier_orden_de_llegada_FR_320(self):
        """FR-320: barajar los ids no cambia ningún número."""
        base = NumeracionLlaves(vector_de(IDS_VARIADOS))
        azar = random.Random(303)

        for _ in range(20):
            barajados = list(IDS_VARIADOS)
            azar.shuffle(barajados)
            otra = NumeracionLlaves(vector_de(barajados))

            for x in IDS_VARIADOS:
                self.assertEqual(otra.numero(x), base.numero(x))

    def test_ids_ordenados_dan_arbol_balanceado_D1(self):
        """D1: aunque los ids lleguen ya ordenados, el árbol interno tiene
        altura logarítmica (desde_ordenados)."""
        ids = [f"itm_llave_{i:04d}" for i in range(1000)]
        numeracion = NumeracionLlaves(vector_de(ids))

        self.assertEqual(len(numeracion), 1000)
        self.assertLessEqual(numeracion.altura(), math.ceil(math.log2(1001)))

        for i, x in enumerate(ids):
            self.assertEqual(numeracion.numero(x), i)


class TestNumeracionPorInsercion(unittest.TestCase):
    """La alternativa medida en R5 (solo bench): ArbolBusqueda.insertar en
    orden de llegada."""

    def test_ids_ordenados_degeneran_en_lista_P1_4_4(self):
        """Límite documentado en P1 §4.4: con ids que llegan ordenados, el
        árbol por inserción tiene altura n."""
        ids = [f"itm_llave_{i:04d}" for i in range(1000)]
        numeracion = NumeracionPorInsercion(vector_de(ids))

        self.assertEqual(len(numeracion), 1000)
        self.assertEqual(numeracion.altura(), 1000)

        for x in ids:
            self.assertEqual(numeracion.id_de(numeracion.numero(x)), x)

    def test_numero_es_el_orden_de_llegada_D1(self):
        numeracion = NumeracionPorInsercion(vector_de(IDS_VARIADOS))

        self.assertEqual(len(numeracion), len(set(IDS_VARIADOS)))
        self.assertEqual(numeracion.numero("itm_llave_b"), 0)
        self.assertEqual(numeracion.numero("itm_llave_9"), 1)
        self.assertIsNone(numeracion.numero("itm_llave_x"))

        for x in IDS_VARIADOS:
            self.assertEqual(numeracion.id_de(numeracion.numero(x)), x)


if __name__ == "__main__":
    unittest.main()
