"""Pruebas de la ListaSimple (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_lista_simple
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import random
import unittest

from crypta.estructuras.ListaSimple import ListaSimple


def revisar_invariantes(prueba, lista):
    """Verifica que los punteros internos sean coherentes entre sí.

    Muchos errores de listas enlazadas no se ven desde afuera hasta mucho
    después (por ejemplo, un _final que apunta a un nodo que ya no está).
    Esta función los detecta en el momento.
    """
    if lista._n == 0:
        prueba.assertIsNone(lista._frente, "lista vacía con _frente distinto de None")
        prueba.assertIsNone(lista._final, "lista vacía con _final distinto de None")
        return

    contados = 0
    ultimo = None
    actual = lista._frente
    while actual is not None:
        contados += 1
        ultimo = actual
        actual = actual.siguiente
        prueba.assertLessEqual(contados, lista._n, "hay más nodos que _n (¿un ciclo?)")

    prueba.assertEqual(contados, lista._n, "_n no coincide con los nodos reales")
    prueba.assertIs(lista._final, ultimo, "_final no apunta al último nodo")
    prueba.assertIsNone(lista._final.siguiente, "el último nodo debe apuntar a None")


def contenido(lista):
    return [x for x in lista]


class TestListaVacia(unittest.TestCase):
    def test_nace_vacia(self):
        lista = ListaSimple()
        self.assertEqual(len(lista), 0)
        self.assertTrue(lista.esta_vacia())
        revisar_invariantes(self, lista)

    def test_ver_frente_en_vacia_falla(self):
        with self.assertRaises(IndexError):
            ListaSimple().ver_frente()

    def test_quitar_del_frente_en_vacia_falla(self):
        with self.assertRaises(IndexError):
            ListaSimple().quitar_del_frente()

    def test_quitar_en_vacia_devuelve_false(self):
        self.assertFalse(ListaSimple().quitar("x"))

    def test_contiene_en_vacia(self):
        self.assertFalse(ListaSimple().contiene("x"))

    def test_recorrer_vacia(self):
        self.assertEqual(contenido(ListaSimple()), [])


class TestAgregar(unittest.TestCase):
    def test_primer_elemento_es_frente_y_final(self):
        lista = ListaSimple()
        lista.agregar_al_final("a")
        self.assertIs(lista._frente, lista._final)
        revisar_invariantes(self, lista)

    def test_primer_elemento_al_frente_es_frente_y_final(self):
        lista = ListaSimple()
        lista.agregar_al_frente("a")
        self.assertIs(lista._frente, lista._final)
        revisar_invariantes(self, lista)

    def test_agregar_al_final_conserva_orden(self):
        lista = ListaSimple()
        for x in ["a", "b", "c"]:
            lista.agregar_al_final(x)
        self.assertEqual(contenido(lista), ["a", "b", "c"])
        self.assertEqual(len(lista), 3)
        revisar_invariantes(self, lista)

    def test_agregar_al_frente_invierte_orden(self):
        lista = ListaSimple()
        for x in ["a", "b", "c"]:
            lista.agregar_al_frente(x)
        self.assertEqual(contenido(lista), ["c", "b", "a"])
        revisar_invariantes(self, lista)

    def test_mezclar_frente_y_final(self):
        lista = ListaSimple()
        lista.agregar_al_final("b")
        lista.agregar_al_frente("a")
        lista.agregar_al_final("c")
        self.assertEqual(contenido(lista), ["a", "b", "c"])
        self.assertEqual(lista.ver_frente(), "a")
        revisar_invariantes(self, lista)


class TestQuitarDelFrente(unittest.TestCase):
    def test_sale_en_orden_de_llegada(self):
        lista = ListaSimple()
        for x in [1, 2, 3]:
            lista.agregar_al_final(x)
        self.assertEqual(lista.quitar_del_frente(), 1)
        self.assertEqual(lista.quitar_del_frente(), 2)
        self.assertEqual(lista.quitar_del_frente(), 3)
        self.assertTrue(lista.esta_vacia())
        revisar_invariantes(self, lista)

    def test_quitar_unico_limpia_final(self):
        # El error clásico: _final queda apuntando a un nodo "fantasma".
        lista = ListaSimple()
        lista.agregar_al_final("solo")
        lista.quitar_del_frente()
        revisar_invariantes(self, lista)
        lista.agregar_al_final("nuevo")
        self.assertEqual(contenido(lista), ["nuevo"])
        revisar_invariantes(self, lista)

    def test_ver_frente_no_quita(self):
        lista = ListaSimple()
        lista.agregar_al_final("a")
        self.assertEqual(lista.ver_frente(), "a")
        self.assertEqual(len(lista), 1)


class TestQuitarValor(unittest.TestCase):
    def setUp(self):
        self.lista = ListaSimple()
        for x in ["a", "b", "c", "d"]:
            self.lista.agregar_al_final(x)

    def test_quitar_el_primero(self):
        self.assertTrue(self.lista.quitar("a"))
        self.assertEqual(contenido(self.lista), ["b", "c", "d"])
        revisar_invariantes(self, self.lista)

    def test_quitar_en_medio(self):
        self.assertTrue(self.lista.quitar("c"))
        self.assertEqual(contenido(self.lista), ["a", "b", "d"])
        revisar_invariantes(self, self.lista)

    def test_quitar_el_ultimo_mueve_final(self):
        self.assertTrue(self.lista.quitar("d"))
        self.assertEqual(contenido(self.lista), ["a", "b", "c"])
        revisar_invariantes(self, self.lista)
        self.lista.agregar_al_final("e")  # debe engancharse después de "c"
        self.assertEqual(contenido(self.lista), ["a", "b", "c", "e"])

    def test_quitar_inexistente(self):
        self.assertFalse(self.lista.quitar("z"))
        self.assertEqual(len(self.lista), 4)
        revisar_invariantes(self, self.lista)

    def test_quitar_solo_la_primera_aparicion(self):
        self.lista.agregar_al_final("b")
        self.assertTrue(self.lista.quitar("b"))
        self.assertEqual(contenido(self.lista), ["a", "c", "d", "b"])
        revisar_invariantes(self, self.lista)

    def test_quitar_todos_uno_por_uno(self):
        for x in ["c", "a", "d", "b"]:
            self.assertTrue(self.lista.quitar(x))
            revisar_invariantes(self, self.lista)
        self.assertTrue(self.lista.esta_vacia())

    def test_quitar_unico_por_valor(self):
        lista = ListaSimple()
        lista.agregar_al_final("x")
        self.assertTrue(lista.quitar("x"))
        revisar_invariantes(self, lista)

    def test_contiene(self):
        self.assertTrue(self.lista.contiene("a"))
        self.assertTrue(self.lista.contiene("d"))
        self.assertFalse(self.lista.contiene("z"))


class TestObjetosDelJuego(unittest.TestCase):
    """La lista guardará enemigos, objetos y trampas, no solo textos."""

    def test_quitar_una_instancia_entre_dos_iguales_por_tipo(self):
        class Enemigo:  # objeto sin __eq__: Python compara por identidad
            def __init__(self, tipo):
                self.tipo = tipo

        rata1, rata2 = Enemigo("rata"), Enemigo("rata")
        lista = ListaSimple()
        lista.agregar_al_final(rata1)
        lista.agregar_al_final(rata2)
        self.assertTrue(lista.quitar(rata2))
        self.assertEqual(len(lista), 1)
        self.assertIs(lista.ver_frente(), rata1)
        revisar_invariantes(self, lista)

    def test_guarda_none(self):
        lista = ListaSimple()
        lista.agregar_al_final(None)
        self.assertEqual(len(lista), 1)
        self.assertTrue(lista.contiene(None))
        self.assertTrue(lista.quitar(None))
        revisar_invariantes(self, lista)


class TestAleatoria(unittest.TestCase):
    """Hace miles de operaciones al azar y compara contra una list de Python.

    Usar list aquí está bien: es solo la referencia de la prueba, no parte del juego.
    """

    def test_contra_referencia(self):
        azar = random.Random(2026)
        lista, referencia = ListaSimple(), []
        for paso in range(5000):
            op = azar.randrange(5)
            valor = azar.randrange(20)
            if op == 0:
                lista.agregar_al_final(valor)
                referencia.append(valor)
            elif op == 1:
                lista.agregar_al_frente(valor)
                referencia.insert(0, valor)
            elif op == 2 and referencia:
                self.assertEqual(lista.quitar_del_frente(), referencia.pop(0))
            elif op == 3:
                esperado = valor in referencia
                if esperado:
                    referencia.remove(valor)
                self.assertEqual(lista.quitar(valor), esperado, f"paso {paso}")
            else:
                self.assertEqual(lista.contiene(valor), valor in referencia)
            self.assertEqual(len(lista), len(referencia), f"paso {paso}")
        self.assertEqual(contenido(lista), referencia)
        revisar_invariantes(self, lista)


if __name__ == "__main__":
    unittest.main()