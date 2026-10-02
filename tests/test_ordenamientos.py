"""Pruebas de ordenamiento.py (Fase 1, §4.9).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_ordenamiento
o todas las pruebas del proyecto:
    python -m unittest -v

Aquí sí se usa sorted() de Python, pero SOLO como referencia para comparar
resultados en las pruebas; el juego nunca lo usa.
"""

import random
import unittest

from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.Vector import Vector
from crypta.estructuras import ordenamiento as ord_
from crypta.estructuras.ordenamiento import (
    contar_descensos,
    copiar_a_vector,
    elegir_algoritmo,
    esta_ordenado,
    insercion,
    mergesort,
    ordenar,
)

# Algoritmos opcionales para --bench: se prueban solo si existen en
# ordenamiento.py. Así la prueba funciona aunque se borren.
OPCIONALES = [getattr(ord_, nombre) for nombre in
              ("burbuja_mejorado", "seleccion", "quicksort", "heapsort")
              if hasattr(ord_, nombre)]

TODOS = [insercion, mergesort] + OPCIONALES
ESTABLES = [insercion, mergesort] + [a for a in OPCIONALES if a.__name__ == "burbuja_mejorado"]


def vector_de(valores):
    v = Vector()
    for x in valores:
        v.agregar(x)
    return v


def contenido(vector):
    return [vector.obtener(i) for i in range(len(vector))]


class Objeto:
    """Imitación de un objeto del inventario."""

    def __init__(self, nombre, peso, valor):
        self.nombre = nombre
        self.peso = peso
        self.valor = valor

    def __repr__(self):
        return f"{self.nombre}({self.peso})"


class TestCasosBorde(unittest.TestCase):
    def comprobar(self, datos):
        for algoritmo in TODOS:
            v = vector_de(datos)
            algoritmo(v)
            self.assertEqual(contenido(v), sorted(datos), f"{algoritmo.__name__} con {datos}")

    def test_vacio(self):
        self.comprobar([])

    def test_un_elemento(self):
        self.comprobar([7])

    def test_dos_elementos(self):
        self.comprobar([2, 1])
        self.comprobar([1, 2])

    def test_ya_ordenado(self):
        self.comprobar(list(range(30)))

    def test_al_reves(self):
        self.comprobar(list(range(30, 0, -1)))

    def test_repetidos(self):
        self.comprobar([3, 1, 3, 2, 1, 3, 2, 2])

    def test_todos_iguales(self):
        self.comprobar([5] * 20)

    def test_negativos_y_textos(self):
        self.comprobar([0, -5, 12, -1, 3])
        self.comprobar(["rata", "antorcha", "daga", "Llave", "arana"])


class TestAleatoria(unittest.TestCase):
    def test_contra_sorted_muchos_tamanos(self):
        azar = random.Random(207)
        for n in list(range(0, 40)) + [63, 64, 65, 100, 257]:
            datos = [azar.randrange(-50, 50) for _ in range(n)]
            for algoritmo in TODOS + [ordenar]:
                v = vector_de(datos)
                algoritmo(v)
                self.assertEqual(contenido(v), sorted(datos), f"{algoritmo.__name__}, n={n}")


class TestClave(unittest.TestCase):
    def setUp(self):
        self.objetos = [
            Objeto("daga", 3, 15),
            Objeto("antorcha", 2, 5),
            Objeto("pocion", 1, 30),
            Objeto("llave", 1, 10),
        ]

    def test_por_peso_valor_y_nombre(self):
        for algoritmo in TODOS + [ordenar]:
            v = vector_de(self.objetos)
            algoritmo(v, clave=lambda o: o.valor)
            self.assertEqual([o.valor for o in contenido(v)], [5, 10, 15, 30], algoritmo.__name__)
            v = vector_de(self.objetos)
            algoritmo(v, clave=lambda o: o.nombre)
            self.assertEqual(
                [o.nombre for o in contenido(v)],
                ["antorcha", "daga", "llave", "pocion"],
                algoritmo.__name__,
            )

    def test_mayor_a_menor_con_clave_negativa(self):
        # Para la tabla de puntajes (mayor puntaje primero)
        v = vector_de([40, 90, 10, 70])
        ordenar(v, clave=lambda p: -p)
        self.assertEqual(contenido(v), [90, 70, 40, 10])


class TestEstabilidad(unittest.TestCase):
    """Con pesos iguales, los objetos deben quedar en su orden original."""

    def objetos_con_empates(self, n, azar):
        return [Objeto(f"obj{i}", azar.randrange(4), 0) for i in range(n)]

    def test_estables_conservan_el_orden_de_los_empates(self):
        azar = random.Random(5)
        for n in [2, 5, 10, 30, 100]:
            originales = self.objetos_con_empates(n, azar)
            esperado = sorted(originales, key=lambda o: o.peso)  # sorted de Python es estable
            for algoritmo in ESTABLES + [ordenar]:
                v = vector_de(originales)
                algoritmo(v, clave=lambda o: o.peso)
                self.assertEqual(
                    [o.nombre for o in contenido(v)],
                    [o.nombre for o in esperado],
                    f"{algoritmo.__name__} no es estable (n={n})",
                )

    def test_ejemplo_del_inventario(self):
        llave = Objeto("llave", 1, 10)
        pocion = Objeto("pocion", 1, 30)
        daga = Objeto("daga", 3, 15)
        v = vector_de([daga, llave, pocion])  # llave estaba antes que la poción
        ordenar(v, clave=lambda o: o.peso)
        self.assertEqual([o.nombre for o in contenido(v)], ["llave", "pocion", "daga"])


class TestDescensos(unittest.TestCase):
    def test_valores(self):
        self.assertEqual(contar_descensos(vector_de([])), 0)
        self.assertEqual(contar_descensos(vector_de([1])), 0)
        self.assertEqual(contar_descensos(vector_de([1, 2, 3, 4])), 0)
        self.assertEqual(contar_descensos(vector_de([4, 3, 2, 1])), 3)
        self.assertEqual(contar_descensos(vector_de([1, 3, 2, 4, 0])), 2)
        self.assertEqual(contar_descensos(vector_de([2, 2, 2])), 0)  # iguales no cuentan

    def test_esta_ordenado(self):
        self.assertTrue(esta_ordenado(vector_de([1, 1, 2])))
        self.assertFalse(esta_ordenado(vector_de([2, 1])))


class TestSelector(unittest.TestCase):
    def test_pequeno_usa_insercion(self):
        v = vector_de(list(range(ord_.UMBRAL_PEQUENO, 0, -1)))  # al revés pero pequeño
        self.assertEqual(elegir_algoritmo(v), "insercion")

    def test_grande_al_azar_usa_mergesort(self):
        azar = random.Random(1)
        v = vector_de([azar.randrange(1000) for _ in range(500)])
        self.assertEqual(elegir_algoritmo(v), "mergesort")

    def test_grande_casi_ordenado_usa_insercion(self):
        datos = list(range(500))
        for i in range(0, 500, 50):  # 10 intercambios de vecinos: 2 % de descensos
            datos[i], datos[i + 1] = datos[i + 1], datos[i]
        self.assertEqual(elegir_algoritmo(vector_de(datos)), "insercion")

    def test_comparacion_costosa_baja_el_umbral(self):
        n = (ord_.UMBRAL_PEQUENO + ord_.UMBRAL_PEQUENO_COSTOSA) // 2
        v = vector_de(list(range(n, 0, -1)))
        self.assertEqual(elegir_algoritmo(v), "insercion")
        self.assertEqual(elegir_algoritmo(v, comparacion_costosa=True), "mergesort")

    def test_ordenar_devuelve_el_algoritmo_usado(self):
        self.assertEqual(ordenar(vector_de([3, 1, 2])), "insercion")
        azar = random.Random(2)
        v = vector_de([azar.randrange(1000) for _ in range(300)])
        self.assertEqual(ordenar(v), "mergesort")
        self.assertTrue(esta_ordenado(v))

    def test_limite_conocido_dos_bloques(self):
        # Dos bloques ordenados: 1 solo descenso, así que el selector elige
        # inserción aunque aquí le cueste O(n²). Igual ordena bien; esta
        # prueba deja el límite documentado para el Documento de Decisiones.
        datos = list(range(250, 500)) + list(range(250))
        v = vector_de(datos)
        self.assertEqual(elegir_algoritmo(v), "insercion")
        ordenar(v)
        self.assertEqual(contenido(v), sorted(datos))


class TestCosto(unittest.TestCase):
    """Cuenta cuántas veces se calcula la clave: es proporcional a las comparaciones."""

    def contar(self, algoritmo, datos):
        llamadas = [0]

        def clave(x):
            llamadas[0] += 1
            return x

        algoritmo(vector_de(datos), clave)
        return llamadas[0]

    def test_insercion_es_lineal_si_ya_esta_ordenado(self):
        self.assertLessEqual(self.contar(insercion, list(range(1000))), 2 * 1000)

    def test_mergesort_es_n_log_n(self):
        azar = random.Random(3)
        datos = [azar.randrange(10_000) for _ in range(1024)]
        # n log2 n = 10 240 comparaciones como máximo; cada una calcula 2 claves
        self.assertLessEqual(self.contar(mergesort, datos), 2 * 1024 * 10)

    def test_insercion_al_azar_es_cuadratica(self):
        azar = random.Random(4)
        datos = [azar.randrange(10_000) for _ in range(1024)]
        self.assertGreater(self.contar(insercion, datos), 5 * self.contar(mergesort, datos))

    @unittest.skipUnless(hasattr(ord_, "quicksort"), "quicksort no está en ordenamiento.py")
    def test_quicksort_no_revienta_la_recursion(self):
        # Con datos ordenados o todos iguales, un quicksort ingenuo llega a O(n) de profundidad
        quicksort = ord_.quicksort
        for datos in (list(range(5000)), [7] * 3000):
            v = vector_de(datos)
            quicksort(v)
            self.assertTrue(esta_ordenado(v))


class TestCopiarAVector(unittest.TestCase):
    def test_vista_ordenada_no_altera_el_orden_real(self):
        # §4.5: "vista ordenada por peso, valor o nombre sin alterar el orden real"
        inventario = ListaDoble()
        for nombre, peso in [("daga", 3), ("antorcha", 2), ("pocion", 1)]:
            inventario.agregar_al_final(Objeto(nombre, peso, 0))

        vista = copiar_a_vector(inventario)
        ordenar(vista, clave=lambda o: o.peso)

        self.assertEqual([o.nombre for o in contenido(vista)], ["pocion", "antorcha", "daga"])
        self.assertEqual([o.nombre for o in inventario], ["daga", "antorcha", "pocion"])

    def test_copia_referencias_no_objetos(self):
        objeto = Objeto("daga", 3, 15)
        inventario = ListaDoble()
        inventario.agregar_al_final(objeto)
        vista = copiar_a_vector(inventario)
        self.assertIs(vista.obtener(0), objeto)


if __name__ == "__main__":
    unittest.main()