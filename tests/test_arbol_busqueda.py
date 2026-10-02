"""Pruebas del ArbolBusqueda (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_arbol_busqueda
o todas las pruebas del proyecto:
    python -m unittest -v

En la prueba aleatoria se usa un dict de Python SOLO como referencia para
comparar resultados; el juego nunca lo usa.
"""

import math
import random
import unittest

from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector


def revisar_invariantes(prueba, arbol):
    """Verifica la regla del ABB y el contador.

    - Recorrido en orden con claves ESTRICTAMENTE crecientes
      (si alguna se repite o sale desordenada, la regla se rompió).
    - La cantidad de nodos reales coincide con _n.
    - Cada nodo respeta los límites que le imponen sus ancestros
      (no basta con comparar solo con el padre).
    """
    claves = [c for c, _ in arbol.en_orden()]
    for a, b in zip(claves, claves[1:]):
        prueba.assertLess(a, b, "el recorrido en orden no sale estrictamente creciente")
    prueba.assertEqual(len(claves), len(arbol), "_n no coincide con los nodos reales")

    pendientes = [(arbol._raiz, None, None)]
    while pendientes:
        nodo, minimo, maximo = pendientes.pop()
        if nodo is None:
            continue
        if minimo is not None:
            prueba.assertGreater(nodo.clave, minimo)
        if maximo is not None:
            prueba.assertLess(nodo.clave, maximo)
        pendientes.append((nodo.izq, minimo, nodo.clave))
        pendientes.append((nodo.der, nodo.clave, maximo))


def arbol_con(claves):
    arbol = ArbolBusqueda()
    for c in claves:
        arbol.insertar(c, f"valor de {c}")
    return arbol


def vector_de_pares(pares):
    v = Vector()
    for par in pares:
        v.agregar(par)
    return v


class TestVacio(unittest.TestCase):
    def test_nace_vacio(self):
        arbol = ArbolBusqueda()
        self.assertEqual(len(arbol), 0)
        self.assertTrue(arbol.esta_vacio())
        self.assertEqual(arbol.altura(), 0)
        self.assertEqual(list(arbol.en_orden()), [])

    def test_buscar_en_vacio(self):
        arbol = ArbolBusqueda()
        self.assertFalse(arbol.contiene(5))
        self.assertIsNone(arbol.obtener(5))
        self.assertEqual(arbol.obtener(5, "no está"), "no está")

    def test_eliminar_en_vacio(self):
        self.assertFalse(ArbolBusqueda().eliminar(5))


class TestInsertarYBuscar(unittest.TestCase):
    def test_encuentra_cada_clave(self):
        claves = [50, 30, 70, 20, 40, 60, 80]
        arbol = arbol_con(claves)
        for c in claves:
            self.assertTrue(arbol.contiene(c))
            self.assertEqual(arbol.obtener(c), f"valor de {c}")
        self.assertEqual(len(arbol), 7)
        revisar_invariantes(self, arbol)

    def test_claves_ausentes(self):
        arbol = arbol_con([50, 30, 70])
        for c in [10, 35, 55, 99]:
            self.assertFalse(arbol.contiene(c))
            self.assertIsNone(arbol.obtener(c))

    def test_clave_repetida_reemplaza_y_no_duplica(self):
        arbol = arbol_con([5, 3, 8])
        arbol.insertar(3, "nuevo")
        self.assertEqual(len(arbol), 3)
        self.assertEqual(arbol.obtener(3), "nuevo")
        revisar_invariantes(self, arbol)

    def test_valor_none_se_distingue_de_ausente(self):
        arbol = ArbolBusqueda()
        arbol.insertar("x", None)
        self.assertTrue(arbol.contiene("x"))
        self.assertIsNone(arbol.obtener("x", "no está"))
        self.assertEqual(arbol.obtener("y", "no está"), "no está")

    def test_ids_del_catalogo(self):
        ids = ["itm_daga", "ent_rata", "trp_foso", "ent_arana", "itm_llave"]
        arbol = ArbolBusqueda()
        for i in ids:
            arbol.insertar(i, {"id": i})  # el dict es solo el "valor" de prueba
        self.assertEqual(arbol.obtener("ent_rata")["id"], "ent_rata")
        self.assertEqual(
            [c for c, _ in arbol.en_orden()],
            ["ent_arana", "ent_rata", "itm_daga", "itm_llave", "trp_foso"],
        )

    def test_en_orden_sale_ordenado_y_con_su_valor(self):
        arbol = arbol_con([50, 30, 70, 20, 40])
        self.assertEqual(
            list(arbol.en_orden()),
            [(c, f"valor de {c}") for c in [20, 30, 40, 50, 70]],
        )


class TestEliminar(unittest.TestCase):
    #          50
    #        /    \
    #      30      70
    #     /  \    /  \
    #   20   40  60   80
    #              \
    #               65
    def setUp(self):
        self.arbol = arbol_con([50, 30, 70, 20, 40, 60, 80, 65])

    def claves(self):
        return [c for c, _ in self.arbol.en_orden()]

    def test_caso1_hoja(self):
        self.assertTrue(self.arbol.eliminar(20))
        self.assertFalse(self.arbol.contiene(20))
        self.assertEqual(self.claves(), [30, 40, 50, 60, 65, 70, 80])
        revisar_invariantes(self, self.arbol)

    def test_caso2_un_hijo(self):
        self.assertTrue(self.arbol.eliminar(60))  # 60 solo tiene a 65
        self.assertTrue(self.arbol.contiene(65))
        self.assertEqual(self.claves(), [20, 30, 40, 50, 65, 70, 80])
        revisar_invariantes(self, self.arbol)

    def test_caso3_dos_hijos_sucesor_lejano(self):
        # El sucesor de 50 es 60 (uno a la derecha, todo a la izquierda),
        # y 60 tiene un hijo derecho (65) que NO se debe perder.
        self.assertTrue(self.arbol.eliminar(50))
        self.assertEqual(self.claves(), [20, 30, 40, 60, 65, 70, 80])
        self.assertEqual(self.arbol.obtener(60), "valor de 60")
        self.assertEqual(self.arbol.obtener(65), "valor de 65")
        revisar_invariantes(self, self.arbol)

    def test_caso3_sucesor_es_el_hijo_derecho_directo(self):
        # El sucesor de 30 es 40, que es su hijo derecho directo
        self.assertTrue(self.arbol.eliminar(30))
        self.assertEqual(self.claves(), [20, 40, 50, 60, 65, 70, 80])
        revisar_invariantes(self, self.arbol)

    def test_eliminar_la_raiz_hasta_vaciar(self):
        while not self.arbol.esta_vacio():
            raiz = self.arbol._raiz.clave
            self.assertTrue(self.arbol.eliminar(raiz))
            self.assertFalse(self.arbol.contiene(raiz))
            revisar_invariantes(self, self.arbol)
        self.assertIsNone(self.arbol._raiz)

    def test_eliminar_raiz_con_un_solo_hijo(self):
        arbol = arbol_con([10, 5])
        self.assertTrue(arbol.eliminar(10))
        self.assertEqual(arbol._raiz.clave, 5)
        revisar_invariantes(self, arbol)

    def test_eliminar_inexistente(self):
        self.assertFalse(self.arbol.eliminar(99))
        self.assertEqual(len(self.arbol), 8)

    def test_eliminar_y_reinsertar(self):
        self.arbol.eliminar(70)
        self.arbol.insertar(70, "otra vez")
        self.assertEqual(self.arbol.obtener(70), "otra vez")
        self.assertEqual(len(self.arbol), 8)
        revisar_invariantes(self, self.arbol)


class TestAltura(unittest.TestCase):
    def test_un_nodo(self):
        self.assertEqual(arbol_con([1]).altura(), 1)

    def test_equilibrado(self):
        self.assertEqual(arbol_con([50, 30, 70, 20, 40, 60, 80]).altura(), 3)

    def test_degenerado_por_claves_ordenadas(self):
        # El riesgo explicado: claves en orden convierten el árbol en una lista
        arbol = arbol_con(range(1, 301))
        self.assertEqual(arbol.altura(), 300)
        self.assertTrue(arbol.contiene(300))  # funciona, pero buscar cuesta O(n)


class TestDesdeOrdenados(unittest.TestCase):
    """Así se cargará el mapa: las salas llegan ordenadas por número."""

    def test_vacio(self):
        arbol = ArbolBusqueda.desde_ordenados(Vector())
        self.assertEqual(len(arbol), 0)
        self.assertIsNone(arbol._raiz)

    def test_un_par(self):
        arbol = ArbolBusqueda.desde_ordenados(vector_de_pares([(7, "sala 7")]))
        self.assertEqual(arbol.obtener(7), "sala 7")
        self.assertEqual(arbol.altura(), 1)

    def test_queda_balanceado(self):
        for n in [2, 3, 7, 8, 100, 1000]:
            pares = vector_de_pares([(k, f"sala {k}") for k in range(1, n + 1)])
            arbol = ArbolBusqueda.desde_ordenados(pares)
            self.assertEqual(len(arbol), n)
            # Altura mínima posible para n nodos: techo(log2(n + 1))
            self.assertEqual(arbol.altura(), math.ceil(math.log2(n + 1)), f"n={n}")
            revisar_invariantes(self, arbol)

    def test_se_puede_usar_normalmente_despues(self):
        pares = vector_de_pares([(k, f"sala {k}") for k in range(1, 21)])
        arbol = ArbolBusqueda.desde_ordenados(pares)
        self.assertEqual(arbol.obtener(13), "sala 13")
        arbol.insertar(21, "sala 21")
        self.assertTrue(arbol.eliminar(10))
        self.assertEqual(len(arbol), 20)
        revisar_invariantes(self, arbol)

    def test_ids_de_texto_ordenados(self):
        ids = ["ent_arana", "ent_rata", "itm_daga", "itm_llave", "trp_foso"]
        arbol = ArbolBusqueda.desde_ordenados(vector_de_pares([(i, i.upper()) for i in ids]))
        self.assertEqual(arbol.obtener("itm_daga"), "ITM_DAGA")
        self.assertEqual(arbol._raiz.clave, "itm_daga")  # el del medio queda de raíz


class TestAleatoria(unittest.TestCase):
    """Miles de operaciones al azar comparadas contra un dict de Python (solo referencia)."""

    def test_contra_referencia(self):
        azar = random.Random(5)
        arbol, referencia = ArbolBusqueda(), {}
        for paso in range(6000):
            clave = azar.randrange(300)
            op = azar.random()
            if op < 0.5:
                arbol.insertar(clave, paso)
                referencia[clave] = paso
            elif op < 0.8:
                esperado = clave in referencia
                self.assertEqual(arbol.eliminar(clave), esperado, f"paso {paso}")
                referencia.pop(clave, None)
            else:
                self.assertEqual(arbol.contiene(clave), clave in referencia)
                self.assertEqual(arbol.obtener(clave), referencia.get(clave))
            self.assertEqual(len(arbol), len(referencia), f"paso {paso}")
            if paso % 500 == 0:
                revisar_invariantes(self, arbol)
        self.assertEqual(list(arbol.en_orden()), sorted(referencia.items()))


if __name__ == "__main__":
    unittest.main()