"""Pruebas de la Cola (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_cola
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import random
import unittest

from crypta.estructuras.Cola import Cola


def contenido(cola):
    return [x for x in cola]


class TestColaVacia(unittest.TestCase):
    def test_nace_vacia(self):
        cola = Cola()
        self.assertEqual(len(cola), 0)
        self.assertTrue(cola.esta_vacia())
        self.assertEqual(contenido(cola), [])

    def test_desencolar_vacia_falla(self):
        with self.assertRaises(IndexError):
            Cola().desencolar()

    def test_ver_frente_vacia_falla(self):
        with self.assertRaises(IndexError):
            Cola().ver_frente()


class TestFIFO(unittest.TestCase):
    def test_primero_en_entrar_primero_en_salir(self):
        cola = Cola()
        for x in ["a", "b", "c"]:
            cola.encolar(x)
        self.assertEqual(cola.desencolar(), "a")
        self.assertEqual(cola.desencolar(), "b")
        self.assertEqual(cola.desencolar(), "c")
        self.assertTrue(cola.esta_vacia())

    def test_ver_frente_no_saca(self):
        cola = Cola()
        cola.encolar(1)
        cola.encolar(2)
        self.assertEqual(cola.ver_frente(), 1)
        self.assertEqual(len(cola), 2)

    def test_recorre_del_mas_viejo_al_mas_nuevo(self):
        cola = Cola()
        for x in [1, 2, 3]:
            cola.encolar(x)
        self.assertEqual(contenido(cola), [1, 2, 3])
        self.assertEqual(len(cola), 3)  # recorrer no consume

    def test_vaciar_y_reusar(self):
        cola = Cola()
        cola.encolar("x")
        cola.desencolar()
        cola.encolar("y")
        self.assertEqual(contenido(cola), ["y"])

    def test_intercalado(self):
        cola = Cola()
        cola.encolar(1)
        cola.encolar(2)
        self.assertEqual(cola.desencolar(), 1)
        cola.encolar(3)
        self.assertEqual(contenido(cola), [2, 3])


class TestSinTope(unittest.TestCase):
    def test_crece_sin_limite(self):
        cola = Cola()
        for k in range(10_000):
            cola.encolar(k)
        self.assertEqual(len(cola), 10_000)
        self.assertEqual(cola.ver_frente(), 0)


class TestConTope(unittest.TestCase):
    """Así se usará para la bitácora de 20 mensajes (§4.8)."""

    def test_al_llenarse_sale_el_mas_viejo(self):
        cola = Cola(capacidad_max=3)
        for x in ["m1", "m2", "m3", "m4"]:
            cola.encolar(x)
        self.assertEqual(len(cola), 3)
        self.assertEqual(contenido(cola), ["m2", "m3", "m4"])

    def test_bitacora_de_20_guarda_los_ultimos_20(self):
        bitacora = Cola(capacidad_max=20)
        for k in range(1, 101):
            bitacora.encolar(f"mensaje {k}")
            self.assertLessEqual(len(bitacora), 20)  # memoria constante
        mensajes = contenido(bitacora)
        self.assertEqual(len(mensajes), 20)
        self.assertEqual(mensajes[0], "mensaje 81")
        self.assertEqual(mensajes[-1], "mensaje 100")

    def test_tope_uno(self):
        cola = Cola(capacidad_max=1)
        cola.encolar("a")
        cola.encolar("b")
        self.assertEqual(contenido(cola), ["b"])

    def test_desencolar_libera_espacio(self):
        cola = Cola(capacidad_max=2)
        cola.encolar(1)
        cola.encolar(2)
        cola.desencolar()
        cola.encolar(3)  # hay espacio: no debe sacar al 2
        self.assertEqual(contenido(cola), [2, 3])

    def test_tope_cero_o_negativo_no_tiene_sentido(self):
        # Una cola que no puede guardar nada es un error de quien la crea:
        # debe avisarse al construirla, no explotar después al encolar.
        with self.assertRaises(ValueError):
            Cola(capacidad_max=0)
        with self.assertRaises(ValueError):
            Cola(capacidad_max=-5)


class TestAleatoria(unittest.TestCase):
    """Miles de operaciones al azar comparadas contra una list de Python."""

    def comparar(self, tope):
        azar = random.Random(207)
        cola, referencia = Cola(capacidad_max=tope), []
        for paso in range(5000):
            if azar.random() < 0.6:
                valor = azar.randrange(1000)
                cola.encolar(valor)
                referencia.append(valor)
                if tope is not None and len(referencia) > tope:
                    referencia.pop(0)
            elif referencia:
                self.assertEqual(cola.desencolar(), referencia.pop(0), f"paso {paso}")
            self.assertEqual(len(cola), len(referencia), f"paso {paso}")
        self.assertEqual(contenido(cola), referencia)

    def test_sin_tope(self):
        self.comparar(None)

    def test_con_tope_20(self):
        self.comparar(20)


if __name__ == "__main__":
    unittest.main()