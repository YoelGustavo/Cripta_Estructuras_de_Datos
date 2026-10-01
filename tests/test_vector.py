"""Pruebas del Vector (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto (proyecto-cripta/):
    python -m unittest -v tests.test_vector
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import unittest

from crypta.estructuras.Vector import Vector


class TestVectorVacio(unittest.TestCase):
    def test_nace_vacio(self):
        v = Vector()
        self.assertEqual(len(v), 0)

    def test_obtener_en_vacio_falla(self):
        with self.assertRaises(IndexError):
            Vector().obtener(0)

    def test_quitar_ultimo_en_vacio_falla(self):
        with self.assertRaises(IndexError):
            Vector().quitar_ultimo()

    def test_quitar_en_vacio_falla(self):
        with self.assertRaises(IndexError):
            Vector().quitar(0)


class TestAgregarYObtener(unittest.TestCase):
    def test_agregar_mil_conserva_el_orden(self):
        v = Vector()
        for k in range(1000):
            v.agregar(k)
        self.assertEqual(len(v), 1000)
        for k in range(1000):
            self.assertEqual(v.obtener(k), k)

    def test_asignar_reemplaza(self):
        v = Vector()
        v.agregar("a")
        v.asignar(0, "b")
        self.assertEqual(v.obtener(0), "b")
        self.assertEqual(len(v), 1)

    def test_guarda_none_como_valor(self):
        # None es un valor válido: el tamaño lo da el contador, no los None.
        v = Vector()
        v.agregar(None)
        self.assertEqual(len(v), 1)
        self.assertIsNone(v.obtener(0))


class TestCrecimiento(unittest.TestCase):
    def test_capacidad_se_duplica_al_llenarse(self):
        v = Vector(capacidad=4)
        for k in range(4):
            v.agregar(k)
        self.assertEqual(v._capacidad, 4)  # lleno, todavía no crece
        v.agregar(4)
        self.assertEqual(v._capacidad, 8)  # al pasarse, se duplica
        self.assertEqual([v.obtener(k) for k in range(5)], [0, 1, 2, 3, 4])

    def test_capacidad_uno(self):
        v = Vector(capacidad=1)
        for k in range(10):
            v.agregar(k)
        self.assertEqual(len(v), 10)
        self.assertEqual(v.obtener(9), 9)

    def test_capacidad_cero(self):
        # Caso borde: alguien crea Vector(0). No debe romperse al agregar.
        v = Vector(capacidad=0)
        v.agregar("x")
        self.assertEqual(v.obtener(0), "x")

    def test_insertar_cuando_esta_lleno_crece(self):
        v = Vector(capacidad=2)
        v.agregar("a")
        v.agregar("c")
        v.insertar(1, "b")
        self.assertEqual([v.obtener(k) for k in range(3)], ["a", "b", "c"])


class TestInsertar(unittest.TestCase):
    def setUp(self):
        self.v = Vector()
        for x in ["b", "c", "d"]:
            self.v.agregar(x)

    def contenido(self):
        return [self.v.obtener(k) for k in range(len(self.v))]

    def test_insertar_al_inicio(self):
        self.v.insertar(0, "a")
        self.assertEqual(self.contenido(), ["a", "b", "c", "d"])

    def test_insertar_en_medio(self):
        self.v.insertar(2, "X")
        self.assertEqual(self.contenido(), ["b", "c", "X", "d"])

    def test_insertar_al_final_es_valido(self):
        self.v.insertar(3, "e")  # i == tamaño está permitido
        self.assertEqual(self.contenido(), ["b", "c", "d", "e"])

    def test_insertar_fuera_de_rango_falla(self):
        with self.assertRaises(IndexError):
            self.v.insertar(5, "z")
        with self.assertRaises(IndexError):
            self.v.insertar(-1, "z")
        self.assertEqual(self.contenido(), ["b", "c", "d"])  # no cambió nada


class TestQuitar(unittest.TestCase):
    def setUp(self):
        self.v = Vector()
        for x in ["a", "b", "c", "d"]:
            self.v.agregar(x)

    def contenido(self):
        return [self.v.obtener(k) for k in range(len(self.v))]

    def test_quitar_al_inicio(self):
        self.assertEqual(self.v.quitar(0), "a")
        self.assertEqual(self.contenido(), ["b", "c", "d"])

    def test_quitar_en_medio(self):
        self.assertEqual(self.v.quitar(1), "b")
        self.assertEqual(self.contenido(), ["a", "c", "d"])

    def test_quitar_al_final(self):
        self.assertEqual(self.v.quitar(3), "d")
        self.assertEqual(self.contenido(), ["a", "b", "c"])

    def test_quitar_ultimo_devuelve_y_reduce(self):
        self.assertEqual(self.v.quitar_ultimo(), "d")
        self.assertEqual(len(self.v), 3)

    def test_quitar_limpia_la_casilla_sobrante(self):
        # Evita que el arreglo guarde referencias a objetos ya quitados.
        self.v.quitar(0)
        self.assertIsNone(self.v._array[3])

    def test_vaciar_y_volver_a_usar(self):
        while len(self.v) > 0:
            self.v.quitar_ultimo()
        self.v.agregar("nuevo")
        self.assertEqual(self.contenido(), ["nuevo"])


class TestIndicesInvalidos(unittest.TestCase):
    def setUp(self):
        self.v = Vector()
        self.v.agregar(10)
        self.v.agregar(20)

    def test_negativo_falla(self):
        # En una list de Python, -1 sería el último; en su Vector debe fallar.
        with self.assertRaises(IndexError):
            self.v.obtener(-1)

    def test_igual_al_tamano_falla(self):
        with self.assertRaises(IndexError):
            self.v.obtener(2)

    def test_casilla_con_capacidad_pero_sin_dato_falla(self):
        # Hay capacidad 8, pero solo 2 datos: la posición 5 no existe.
        with self.assertRaises(IndexError):
            self.v.asignar(5, 99)


if __name__ == "__main__":
    unittest.main()