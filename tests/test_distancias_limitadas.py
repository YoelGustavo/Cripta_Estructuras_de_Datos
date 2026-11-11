"""Pruebas de las búsquedas de costo mínimo de la capacidad 001 (tarea T032).

- `DistanciasLimitadas` (FR-014, FR-036; research D1, D5): búsqueda perezosa
  y reanudable desde la sala del jugador por las ENTRADAS de cada nodo, con
  vectores por índice denso y marca de cálculo.
- `RutaPorCazador` (FR-017, FR-031; research D2): búsqueda desde la sala del
  cazador por las salidas de ida, con etiqueta (distancia, primer paso).

Los grafos son pequeños y se escriben como listas de aristas
(origen, destino, costo) sobre nodos 0..V-1; el resultado se compara con un
cálculo sin límite hecho de la forma más simple posible.

    python -m unittest -v tests.test_distancias_limitadas
"""

import random
import unittest

from crypta.estructuras.DistanciasLimitadas import DistanciasLimitadas
from crypta.estructuras.RutaPorCazador import RutaPorCazador


INFINITO = float("inf")


class Grafo:
    """Grafo dirigido de prueba. `entradas(x)` da las aristas y→x como
    (y, costo); `salidas(x)`, las x→y como (y, costo)."""

    def __init__(self, cantidad, aristas):
        self.cantidad = cantidad
        self.aristas = list(aristas)

    def entradas(self, nodo):
        for origen, destino, costo in self.aristas:
            if destino == nodo:
                yield origen, costo

    def salidas(self, nodo):
        for origen, destino, costo in self.aristas:
            if origen == nodo:
                yield destino, costo

    def distancias_hacia(self, objetivo):
        """dist(x, objetivo) para cada x, relajando todas las aristas V
        veces (Bellman-Ford). INFINITO si x no llega."""
        dist = [INFINITO] * self.cantidad
        dist[objetivo] = 0

        for _ in range(self.cantidad):
            for origen, destino, costo in self.aristas:
                if dist[destino] + costo < dist[origen]:
                    dist[origen] = dist[destino] + costo

        return dist

    def primer_paso(self, origen, objetivo):
        """(d, menor vecino v con costo(origen, v) + dist(v) = d) o None."""
        dist = self.distancias_hacia(objetivo)

        if dist[origen] == INFINITO:
            return None

        if origen == objetivo:
            return 0, None

        pasos = [destino for destino, costo in self.salidas(origen)
                 if costo + dist[destino] == dist[origen]]
        return dist[origen], min(pasos)


def grafo_al_azar(semilla, cantidad=12, aristas=30, costos=(1, 2, 3, 5)):
    """Grafo dirigido al azar, con aristas sin vuelta y costos que empatan
    a menudo."""
    azar = random.Random(semilla)
    lista = []

    for _ in range(aristas):
        origen = azar.randrange(cantidad)
        destino = azar.randrange(cantidad)

        if origen != destino:
            lista.append((origen, destino, azar.choice(costos)))

    return Grafo(cantidad, lista)


def cuadricula(lado, costo=1):
    """Cuadrícula lado x lado con aristas en ambos sentidos y todos los
    costos iguales: muchísimas rutas mínimas que se cruzan."""
    aristas = []

    for fila in range(lado):
        for columna in range(lado):
            nodo = fila * lado + columna

            if columna + 1 < lado:
                aristas += [(nodo, nodo + 1, costo), (nodo + 1, nodo, costo)]

            if fila + 1 < lado:
                aristas += [(nodo, nodo + lado, costo),
                            (nodo + lado, nodo, costo)]

    return Grafo(lado * lado, aristas)


def busqueda(grafo):
    return DistanciasLimitadas(grafo.cantidad, grafo.entradas)


def asentados(distancias, cantidad):
    return [nodo for nodo in range(cantidad) if distancias.esta_asentada(nodo)]


class TestDistanciasLimitadas(unittest.TestCase):
    """FR-014, FR-017, FR-036: distancias hacia el origen por las entradas,
    con corte por límite, reanudación y marca."""

    def test_distancias_iguales_a_un_calculo_sin_limite(self):
        """FR-014: extendida sin límite, da dist(x, origen) para cada x."""
        for semilla in range(40):
            grafo = grafo_al_azar(semilla)
            esperado = grafo.distancias_hacia(0)
            distancias = busqueda(grafo)

            distancias.reiniciar(0)
            distancias.extender_hasta(10 ** 9)

            with self.subTest(semilla=semilla):
                for nodo in range(grafo.cantidad):
                    if esperado[nodo] == INFINITO:
                        self.assertIsNone(distancias.distancia(nodo))
                        self.assertFalse(distancias.esta_asentada(nodo))
                    else:
                        self.assertEqual(distancias.distancia(nodo),
                                         esperado[nodo])

    def test_corte_por_limite(self):
        """FR-036: solo se asientan los nodos con dist ≤ límite."""
        for semilla in range(40):
            grafo = grafo_al_azar(semilla)
            esperado = grafo.distancias_hacia(3)

            for limite in (0, 1, 2, 4, 7):
                distancias = busqueda(grafo)
                distancias.reiniciar(3)
                distancias.extender_hasta(limite)

                with self.subTest(semilla=semilla, limite=limite):
                    self.assertEqual(
                        asentados(distancias, grafo.cantidad),
                        [n for n in range(grafo.cantidad)
                         if esperado[n] <= limite])
                    self.assertLessEqual(distancias.hasta, limite)

    def test_extender_en_dos_pasos_es_lo_mismo_que_de_una_vez(self):
        """FR-014, FR-036: la búsqueda se reanuda donde quedó, sin volver a
        asentar nada."""
        for semilla in range(40):
            grafo = grafo_al_azar(semilla)

            de_una_vez = busqueda(grafo)
            de_una_vez.reiniciar(1)
            de_una_vez.extender_hasta(6)

            en_dos = busqueda(grafo)
            en_dos.reiniciar(1)
            en_dos.extender_hasta(2)
            en_dos.extender_hasta(6)

            with self.subTest(semilla=semilla):
                self.assertEqual(asentados(en_dos, grafo.cantidad),
                                 asentados(de_una_vez, grafo.cantidad))
                self.assertEqual(
                    [en_dos.distancia(n) for n in range(grafo.cantidad)],
                    [de_una_vez.distancia(n) for n in range(grafo.cantidad)])
                self.assertEqual(en_dos.asentados, de_una_vez.asentados)

    def test_se_detiene_al_asentar_el_objetivo(self):
        """FR-014: con objetivo, no asienta nada más lejano que él."""
        grafo = cuadricula(5)
        distancias = busqueda(grafo)
        distancias.reiniciar(0)

        self.assertTrue(distancias.extender_hasta(10 ** 9, objetivo=6))

        self.assertEqual(distancias.distancia(6), 2)
        for nodo in asentados(distancias, grafo.cantidad):
            self.assertLessEqual(distancias.distancia(nodo), 2)

        # Si el objetivo ya está asentado, no hace falta hacer nada.
        antes = distancias.asentados
        self.assertTrue(distancias.extender_hasta(10 ** 9, objetivo=6))
        self.assertEqual(distancias.asentados, antes)

    def test_objetivo_fuera_de_limite(self):
        """FR-015: si el objetivo está más lejos que el límite, no queda
        asentado."""
        grafo = cuadricula(5)
        distancias = busqueda(grafo)
        distancias.reiniciar(0)

        self.assertFalse(distancias.extender_hasta(3, objetivo=24))
        self.assertFalse(distancias.esta_asentada(24))
        self.assertTrue(distancias.extender_hasta(8, objetivo=24))
        self.assertEqual(distancias.distancia(24), 8)

    def test_reiniciar_no_limpia_y_lo_viejo_no_se_lee(self):
        """FR-036: reiniciar es O(1): no recorre los vectores; los valores
        del cálculo anterior siguen ahí pero la marca los invalida."""
        grafo = cuadricula(4)
        distancias = busqueda(grafo)
        distancias.reiniciar(0)
        distancias.extender_hasta(10 ** 9)
        self.assertEqual(distancias._dist.obtener(14), 5)

        distancias.reiniciar(15)

        self.assertEqual(distancias._dist.obtener(14), 5)   # no se limpió
        self.assertEqual(distancias.origen, 15)
        self.assertEqual(distancias.busquedas, 2)
        for nodo in range(grafo.cantidad):
            self.assertFalse(distancias.esta_asentada(nodo))
            self.assertIsNone(distancias.distancia(nodo))

        distancias.extender_hasta(10 ** 9)
        self.assertEqual(distancias.distancia(15), 0)
        self.assertEqual(distancias.distancia(0), 6)

    def test_sin_reiniciar_no_hay_nada(self):
        """Antes del primer reiniciar no hay origen ni distancias."""
        distancias = busqueda(cuadricula(2))
        self.assertIsNone(distancias.origen)
        self.assertIsNone(distancias.distancia(0))
        self.assertFalse(distancias.extender_hasta(10, objetivo=0))

    def test_salidas_sin_vuelta_se_recorren_por_las_entradas(self):
        """FR-014: dist(x, jugador) usa las salidas x→...→jugador. Con
        0 —5→ 1 sin vuelta y 1 —2→ 2 sin vuelta, desde el jugador en 1: el
        nodo 0 está a 5 y el 2 no llega."""
        grafo = Grafo(3, [(0, 1, 5), (1, 2, 2)])
        distancias = busqueda(grafo)
        distancias.reiniciar(1)
        distancias.extender_hasta(10 ** 9)

        self.assertEqual(distancias.distancia(0), 5)
        self.assertIsNone(distancias.distancia(2))

    def test_las_entradas_se_piden_solo_al_asentar(self):
        """FR-036: el trabajo depende de lo asentado, no del tamaño total:
        solo se piden las entradas de los nodos asentados."""
        grafo = Grafo(1000, [(n + 1, n, 1) for n in range(999)])
        pedidas = []

        def entradas(nodo):
            pedidas.append(nodo)
            return grafo.entradas(nodo)

        distancias = DistanciasLimitadas(grafo.cantidad, entradas)
        distancias.reiniciar(0)
        distancias.extender_hasta(5)

        self.assertEqual(pedidas, [0, 1, 2, 3, 4, 5])
        self.assertEqual(distancias.asentados, 6)


class TestRutaPorCazador(unittest.TestCase):
    """FR-017, FR-031: la alternativa por cazador da la distancia y el
    primer paso de menor índice entre los que inician una ruta mínima."""

    def comparar(self, grafo, origen, objetivo, limite=10 ** 9):
        esperado = grafo.primer_paso(origen, objetivo)

        if esperado is not None and esperado[0] > limite:
            esperado = None

        ruta = RutaPorCazador(grafo.cantidad, grafo.salidas)
        self.assertEqual(ruta.buscar(origen, objetivo, limite), esperado)

    def test_primer_paso_de_menor_indice_en_grafos_al_azar(self):
        """FR-017: con costos que empatan seguido."""
        for semilla in range(40):
            grafo = grafo_al_azar(semilla, costos=(1, 1, 2))

            for origen in range(grafo.cantidad):
                with self.subTest(semilla=semilla, origen=origen):
                    self.comparar(grafo, origen, 0)

    def test_cuadricula_con_rutas_que_se_cruzan(self):
        """FR-017: en la cuadrícula, desde cada nodo."""
        grafo = cuadricula(5)

        for origen in range(grafo.cantidad):
            for objetivo in (0, 12, 24):
                with self.subTest(origen=origen, objetivo=objetivo):
                    self.comparar(grafo, origen, objetivo)

    def test_limite(self):
        """FR-015: d > límite → None; d = límite → avanza."""
        grafo = cuadricula(5)
        ruta = RutaPorCazador(grafo.cantidad, grafo.salidas)

        self.assertIsNone(ruta.buscar(24, 0, 7))
        self.assertEqual(ruta.buscar(24, 0, 8), (8, 19))

    def test_mismo_nodo_y_sin_ruta(self):
        """FR-013, FR-014: en el mismo nodo la distancia es 0 y no hay
        paso; sin ruta, None."""
        grafo = Grafo(3, [(0, 1, 5), (1, 2, 2)])
        ruta = RutaPorCazador(grafo.cantidad, grafo.salidas)

        self.assertEqual(ruta.buscar(1, 1, 0), (0, None))
        self.assertIsNone(ruta.buscar(2, 0, 10 ** 9))
        self.assertEqual(ruta.buscar(0, 2, 10 ** 9), (7, 1))
        self.assertEqual(ruta.busquedas, 3)

    def test_la_ruta_con_menos_nodos_no_siempre_es_la_mas_barata(self):
        """FR-014, Apéndice B: 0–1 cuesta 500; 0–2–3–1 cuesta 300."""
        grafo = Grafo(4, [(0, 1, 500), (0, 2, 100), (2, 3, 100),
                          (3, 1, 100)])
        ruta = RutaPorCazador(grafo.cantidad, grafo.salidas)

        self.assertEqual(ruta.buscar(0, 1, 10 ** 9), (300, 2))


if __name__ == "__main__":
    unittest.main()
