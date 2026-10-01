"""Pruebas de la ListaDoble (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_lista_doble
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import random
import unittest

from crypta.estructuras.ListaDoble import ListaDoble


def revisar_invariantes(prueba, lista):
    """Recorre la lista en ambos sentidos y verifica que todo cuadre.

    - Hacia adelante y hacia atrás se encuentran los mismos nodos, en orden inverso.
    - Cada nodo es el 'anterior' de su 'siguiente' (las flechas van en pareja).
    - _n coincide con los nodos reales.
    - Vacía = el centinela se apunta a sí mismo.
    """
    c = lista._centinela
    adelante = []
    actual = c.siguiente
    while actual is not c:
        prueba.assertIs(actual.siguiente.anterior, actual, "flechas desparejas hacia adelante")
        adelante.append(actual)
        actual = actual.siguiente
        prueba.assertLessEqual(len(adelante), lista._n, "más nodos que _n (¿ciclo roto?)")

    atras = []
    actual = c.anterior
    while actual is not c:
        prueba.assertIs(actual.anterior.siguiente, actual, "flechas desparejas hacia atrás")
        atras.append(actual)
        actual = actual.anterior
        prueba.assertLessEqual(len(atras), lista._n, "más nodos que _n (¿ciclo roto?)")

    prueba.assertEqual(len(adelante), lista._n, "_n no coincide con los nodos reales")
    prueba.assertEqual(adelante, atras[::-1], "adelante y atrás no ven los mismos nodos")
    if lista._n == 0:
        prueba.assertIs(c.siguiente, c)
        prueba.assertIs(c.anterior, c)


def contenido(lista):
    # Corta si recorre más elementos de los que dice tener la lista:
    # si los punteros forman un ciclo, la prueba falla en vez de colgarse.
    valores = []
    for x in lista:
        valores.append(x)
        if len(valores) > len(lista):
            raise AssertionError("el recorrido no termina: los punteros forman un ciclo")
    return valores


def contenido_al_reves(lista):
    """Recorre con ultimo() y anterior(), como hará el cursor del inventario."""
    valores = []
    nodo = lista.ultimo()
    while nodo is not None:
        valores.append(nodo.valor)
        if len(valores) > len(lista):
            raise AssertionError("el recorrido hacia atrás no termina: hay un ciclo")
        nodo = lista.anterior(nodo)
    return valores


class TestListaVacia(unittest.TestCase):
    def test_nace_vacia(self):
        lista = ListaDoble()
        self.assertEqual(len(lista), 0)
        self.assertTrue(lista.esta_vacia())
        self.assertIsNone(lista.primero())
        self.assertIsNone(lista.ultimo())
        self.assertEqual(contenido(lista), [])
        revisar_invariantes(self, lista)


class TestAgregar(unittest.TestCase):
    def test_agregar_devuelve_el_nodo(self):
        lista = ListaDoble()
        nodo = lista.agregar_al_final("daga")
        self.assertEqual(nodo.valor, "daga")
        self.assertIs(lista.primero(), nodo)
        self.assertIs(lista.ultimo(), nodo)

    def test_primer_elemento_por_el_frente(self):
        lista = ListaDoble()
        nodo = lista.agregar_al_frente("x")
        self.assertIs(lista.primero(), nodo)
        self.assertIs(lista.ultimo(), nodo)
        revisar_invariantes(self, lista)

    def test_orden_al_final_y_al_frente(self):
        lista = ListaDoble()
        lista.agregar_al_final("b")
        lista.agregar_al_final("c")
        lista.agregar_al_frente("a")
        self.assertEqual(contenido(lista), ["a", "b", "c"])
        self.assertEqual(contenido_al_reves(lista), ["c", "b", "a"])
        self.assertEqual(len(lista), 3)
        revisar_invariantes(self, lista)


class TestNavegacion(unittest.TestCase):
    """Lo que usará el cursor del inventario para avanzar y retroceder."""

    def setUp(self):
        self.lista = ListaDoble()
        self.a = self.lista.agregar_al_final("a")
        self.b = self.lista.agregar_al_final("b")
        self.c = self.lista.agregar_al_final("c")

    def test_siguiente_y_anterior(self):
        self.assertIs(self.lista.siguiente(self.a), self.b)
        self.assertIs(self.lista.siguiente(self.b), self.c)
        self.assertIs(self.lista.anterior(self.c), self.b)
        self.assertIs(self.lista.anterior(self.b), self.a)

    def test_los_bordes_devuelven_none_y_no_el_centinela(self):
        self.assertIsNone(self.lista.siguiente(self.c))
        self.assertIsNone(self.lista.anterior(self.a))

    def test_un_solo_elemento_no_tiene_vecinos(self):
        lista = ListaDoble()
        solo = lista.agregar_al_final("solo")
        self.assertIsNone(lista.siguiente(solo))
        self.assertIsNone(lista.anterior(solo))


class TestQuitarNodo(unittest.TestCase):
    def setUp(self):
        self.lista = ListaDoble()
        self.a = self.lista.agregar_al_final("a")
        self.b = self.lista.agregar_al_final("b")
        self.c = self.lista.agregar_al_final("c")

    def test_quitar_en_medio(self):
        self.assertEqual(self.lista.quitar_nodo(self.b), "b")
        self.assertEqual(contenido(self.lista), ["a", "c"])
        self.assertEqual(contenido_al_reves(self.lista), ["c", "a"])
        revisar_invariantes(self, self.lista)

    def test_quitar_el_primero(self):
        self.lista.quitar_nodo(self.a)
        self.assertIs(self.lista.primero(), self.b)
        revisar_invariantes(self, self.lista)

    def test_quitar_el_ultimo(self):
        self.lista.quitar_nodo(self.c)
        self.assertIs(self.lista.ultimo(), self.b)
        self.lista.agregar_al_final("d")
        self.assertEqual(contenido(self.lista), ["a", "b", "d"])
        revisar_invariantes(self, self.lista)

    def test_quitar_todos_y_reusar(self):
        for nodo in (self.b, self.a, self.c):
            self.lista.quitar_nodo(nodo)
            revisar_invariantes(self, self.lista)
        self.assertTrue(self.lista.esta_vacia())
        self.assertIsNone(self.lista.primero())
        self.lista.agregar_al_frente("nuevo")
        self.assertEqual(contenido(self.lista), ["nuevo"])
        revisar_invariantes(self, self.lista)

    def test_nodo_quitado_queda_desconectado(self):
        self.lista.quitar_nodo(self.b)
        self.assertIsNone(self.b.anterior)
        self.assertIsNone(self.b.siguiente)

    def test_quitar_dos_veces_el_mismo_nodo_falla_sin_romper_la_lista(self):
        self.lista.quitar_nodo(self.b)
        with self.assertRaises(Exception):
            self.lista.quitar_nodo(self.b)
        self.assertEqual(contenido(self.lista), ["a", "c"])
        revisar_invariantes(self, self.lista)


class TestMover(unittest.TestCase):
    def setUp(self):
        self.lista = ListaDoble()
        self.nodos = [self.lista.agregar_al_final(x) for x in ["a", "b", "c", "d"]]

    def test_mover_al_frente_desde_el_medio(self):
        # Así funciona "equipar" en el inventario (§4.5)
        self.lista.mover_al_frente(self.nodos[2])
        self.assertEqual(contenido(self.lista), ["c", "a", "b", "d"])
        revisar_invariantes(self, self.lista)

    def test_mover_al_frente_el_primero_no_cambia_nada(self):
        self.lista.mover_al_frente(self.nodos[0])
        self.assertEqual(contenido(self.lista), ["a", "b", "c", "d"])
        revisar_invariantes(self, self.lista)

    def test_mover_al_frente_el_ultimo(self):
        self.lista.mover_al_frente(self.nodos[3])
        self.assertEqual(contenido(self.lista), ["d", "a", "b", "c"])
        revisar_invariantes(self, self.lista)

    def test_mover_al_final_desde_el_medio(self):
        # Así funciona "recién usada" en la caché LRU (§4.4)
        self.lista.mover_al_final(self.nodos[1])
        self.assertEqual(contenido(self.lista), ["a", "c", "d", "b"])
        revisar_invariantes(self, self.lista)

    def test_mover_al_final_el_ultimo_no_cambia_nada(self):
        self.lista.mover_al_final(self.nodos[3])
        self.assertEqual(contenido(self.lista), ["a", "b", "c", "d"])
        revisar_invariantes(self, self.lista)

    def test_mover_no_cambia_el_tamano(self):
        self.lista.mover_al_final(self.nodos[0])
        self.lista.mover_al_frente(self.nodos[2])
        self.assertEqual(len(self.lista), 4)

    def test_mover_con_un_solo_elemento(self):
        lista = ListaDoble()
        solo = lista.agregar_al_final("solo")
        lista.mover_al_frente(solo)
        lista.mover_al_final(solo)
        self.assertEqual(contenido(lista), ["solo"])
        revisar_invariantes(self, lista)

    def test_el_nodo_sigue_siendo_el_mismo_despues_de_mover(self):
        # Importante para el cursor y la caché: la referencia guardada sigue sirviendo
        nodo = self.nodos[2]
        self.lista.mover_al_frente(nodo)
        self.assertIs(self.lista.primero(), nodo)
        self.assertEqual(self.lista.quitar_nodo(nodo), "c")
        revisar_invariantes(self, self.lista)


class TestComoLRU(unittest.TestCase):
    """Simula el orden de uso de una caché: lo más viejo al frente, lo recién usado al final."""

    def test_desalojar_el_menos_usado(self):
        lista = ListaDoble()
        rata = lista.agregar_al_final("ent_rata")
        daga = lista.agregar_al_final("itm_daga")
        lista.agregar_al_final("trp_dardos")
        lista.mover_al_final(rata)   # se volvió a usar la rata
        lista.mover_al_final(daga)   # y luego la daga
        desalojada = lista.quitar_nodo(lista.primero())
        self.assertEqual(desalojada, "trp_dardos")
        self.assertEqual(contenido(lista), ["ent_rata", "itm_daga"])


class TestAleatoria(unittest.TestCase):
    """Miles de operaciones al azar comparadas contra una list de Python.

    La list guarda los nodos en el mismo orden que debería tener la ListaDoble.
    """

    def test_contra_referencia(self):
        azar = random.Random(4)
        lista, referencia = ListaDoble(), []
        for paso in range(5000):
            op = azar.randrange(6)
            if op == 0:
                referencia.append(lista.agregar_al_final(paso))
            elif op == 1:
                referencia.insert(0, lista.agregar_al_frente(paso))
            elif referencia:
                nodo = azar.choice(referencia)
                if op == 2:
                    valor = nodo.valor
                    self.assertEqual(lista.quitar_nodo(nodo), valor)
                    referencia.remove(nodo)
                elif op == 3:
                    lista.mover_al_frente(nodo)
                    referencia.remove(nodo)
                    referencia.insert(0, nodo)
                elif op == 4:
                    lista.mover_al_final(nodo)
                    referencia.remove(nodo)
                    referencia.append(nodo)
                else:
                    i = referencia.index(nodo)
                    sig = referencia[i + 1] if i + 1 < len(referencia) else None
                    ant = referencia[i - 1] if i > 0 else None
                    self.assertIs(lista.siguiente(nodo), sig, f"paso {paso}")
                    self.assertIs(lista.anterior(nodo), ant, f"paso {paso}")
            self.assertEqual(len(lista), len(referencia), f"paso {paso}")
            if paso % 250 == 0:
                revisar_invariantes(self, lista)
        self.assertEqual(contenido(lista), [n.valor for n in referencia])
        revisar_invariantes(self, lista)


if __name__ == "__main__":
    unittest.main()