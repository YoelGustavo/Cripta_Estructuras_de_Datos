"""Pruebas de la Pila (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_pila
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import random
import unittest

from crypta.estructuras.Pila import Pila


class TestPilaVacia(unittest.TestCase):
    def test_nace_vacia(self):
        pila = Pila()
        self.assertEqual(len(pila), 0)
        self.assertTrue(pila.esta_vacia())

    def test_desapilar_vacia_falla(self):
        with self.assertRaises(IndexError):
            Pila().desapilar()

    def test_ver_tope_vacia_falla(self):
        with self.assertRaises(IndexError):
            Pila().ver_tope()

    def test_descartar_fondo_vacia_falla(self):
        with self.assertRaises(IndexError):
            Pila().descartar_fondo()


class TestLIFO(unittest.TestCase):
    def test_ultimo_en_entrar_primero_en_salir(self):
        pila = Pila()
        for x in ["a", "b", "c"]:
            pila.apilar(x)
        self.assertEqual(pila.desapilar(), "c")
        self.assertEqual(pila.desapilar(), "b")
        self.assertEqual(pila.desapilar(), "a")
        self.assertTrue(pila.esta_vacia())

    def test_ver_tope_no_saca(self):
        pila = Pila()
        pila.apilar(1)
        pila.apilar(2)
        self.assertEqual(pila.ver_tope(), 2)
        self.assertEqual(len(pila), 2)

    def test_intercalado(self):
        pila = Pila()
        pila.apilar(1)
        pila.apilar(2)
        self.assertEqual(pila.desapilar(), 2)
        pila.apilar(3)
        self.assertEqual(pila.ver_tope(), 3)
        self.assertEqual(len(pila), 2)

    def test_vaciar_y_reusar(self):
        pila = Pila()
        pila.apilar("x")
        pila.desapilar()
        pila.apilar("y")
        self.assertEqual(pila.ver_tope(), "y")

    def test_muchos_elementos_hace_crecer_el_vector(self):
        pila = Pila()
        for k in range(10_000):
            pila.apilar(k)
        self.assertEqual(len(pila), 10_000)
        self.assertEqual(pila.ver_tope(), 9_999)
        for k in range(9_999, -1, -1):
            self.assertEqual(pila.desapilar(), k)

    def test_guarda_none(self):
        pila = Pila()
        pila.apilar(None)
        self.assertEqual(len(pila), 1)
        self.assertIsNone(pila.desapilar())


class TestDescartarFondo(unittest.TestCase):
    """Así se usará para el historial de 5 intervalos del pergamino (§4.6)."""

    def test_quita_el_mas_viejo_y_deja_el_tope(self):
        pila = Pila()
        for x in ["a", "b", "c"]:
            pila.apilar(x)
        pila.descartar_fondo()
        self.assertEqual(len(pila), 2)
        self.assertEqual(pila.desapilar(), "c")
        self.assertEqual(pila.desapilar(), "b")  # "a" ya no está

    def test_descartar_el_unico(self):
        pila = Pila()
        pila.apilar("solo")
        pila.descartar_fondo()
        self.assertTrue(pila.esta_vacia())

    def test_historial_con_tope_5(self):
        historial = Pila()
        for accion in range(1, 13):
            historial.apilar(f"intervalo {accion}")
            if len(historial) > 5:
                historial.descartar_fondo()
            self.assertLessEqual(len(historial), 5)
        # Deshacer saca del más reciente al más viejo de los 5 que quedan
        sacados = [historial.desapilar() for _ in range(5)]
        self.assertEqual(sacados, [f"intervalo {k}" for k in range(12, 7, -1)])
        self.assertTrue(historial.esta_vacia())


class TestAleatoria(unittest.TestCase):
    """Miles de operaciones al azar comparadas contra una list de Python."""

    def test_contra_referencia(self):
        azar = random.Random(11)
        pila, referencia = Pila(), []
        for paso in range(5000):
            op = azar.random()
            if op < 0.55:
                valor = azar.randrange(1000)
                pila.apilar(valor)
                referencia.append(valor)
            elif op < 0.9 and referencia:
                self.assertEqual(pila.desapilar(), referencia.pop(), f"paso {paso}")
            elif referencia:
                pila.descartar_fondo()
                referencia.pop(0)
            if referencia:
                self.assertEqual(pila.ver_tope(), referencia[-1], f"paso {paso}")
            self.assertEqual(len(pila), len(referencia), f"paso {paso}")


if __name__ == "__main__":
    unittest.main()