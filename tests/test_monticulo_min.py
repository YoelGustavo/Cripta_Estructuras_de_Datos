"""Pruebas del MonticuloMin (Fase 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_monticulo_min
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import random
import unittest

from crypta.estructuras.MonticuloMin import MonticuloMin


def revisar_regla(prueba, monticulo):
    """Verifica la regla del montículo: ningún hijo va antes que su padre."""
    v = monticulo._vector
    n = len(v)
    for i in range(1, n):
        padre = (i - 1) // 2
        prueba.assertFalse(
            monticulo._menor(v.obtener(i), v.obtener(padre)),
            f"el hijo en {i} va antes que su padre en {padre}",
        )


def vaciar(monticulo):
    salida = []
    while not monticulo.esta_vacia():
        salida.append(monticulo.extraer_min())
    return salida


class Evento:
    """Imitación mínima de los eventos de la agenda (§2.3)."""

    def __init__(self, tiempo, secuencia, nombre):
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.nombre = nombre


def menor_evento(a, b):
    return (a.tiempo, a.secuencia) < (b.tiempo, b.secuencia)


class TestVacio(unittest.TestCase):
    def test_nace_vacio(self):
        m = MonticuloMin()
        self.assertEqual(len(m), 0)
        self.assertTrue(m.esta_vacia())

    def test_ver_min_vacio_falla(self):
        with self.assertRaises(IndexError):
            MonticuloMin().ver_min()

    def test_extraer_vacio_falla(self):
        with self.assertRaises(IndexError):
            MonticuloMin().extraer_min()


class TestBasico(unittest.TestCase):
    def test_un_elemento(self):
        m = MonticuloMin()
        m.insertar(7)
        self.assertEqual(m.ver_min(), 7)
        self.assertEqual(m.extraer_min(), 7)
        self.assertTrue(m.esta_vacia())

    def test_ejemplo_de_la_explicacion(self):
        m = MonticuloMin()
        for x in [1, 3, 2, 5, 4, 8]:
            m.insertar(x)
        m.insertar(0)
        self.assertEqual(m.ver_min(), 0)
        revisar_regla(self, m)
        self.assertEqual(m.extraer_min(), 0)
        self.assertEqual(m.ver_min(), 1)
        revisar_regla(self, m)

    def test_ver_min_no_saca(self):
        m = MonticuloMin()
        m.insertar(3)
        m.insertar(1)
        self.assertEqual(m.ver_min(), 1)
        self.assertEqual(len(m), 2)

    def test_sale_ordenado(self):
        m = MonticuloMin()
        for x in [5, 3, 8, 1, 9, 2, 7]:
            m.insertar(x)
            revisar_regla(self, m)
        self.assertEqual(vaciar(m), [1, 2, 3, 5, 7, 8, 9])

    def test_repetidos(self):
        m = MonticuloMin()
        for x in [4, 1, 4, 1, 4]:
            m.insertar(x)
        self.assertEqual(vaciar(m), [1, 1, 4, 4, 4])

    def test_ya_ordenado_y_al_reves(self):
        for datos in (list(range(50)), list(range(50, 0, -1))):
            m = MonticuloMin()
            for x in datos:
                m.insertar(x)
            self.assertEqual(vaciar(m), sorted(datos))

    def test_dos_elementos_en_ambos_ordenes(self):
        for a, b in ((1, 2), (2, 1)):
            m = MonticuloMin()
            m.insertar(a)
            m.insertar(b)
            self.assertEqual(vaciar(m), [1, 2])

    def test_vaciar_y_reusar(self):
        m = MonticuloMin()
        m.insertar(5)
        m.extraer_min()
        m.insertar(3)
        m.insertar(9)
        self.assertEqual(vaciar(m), [3, 9])


class TestFuncionMenor(unittest.TestCase):
    def test_montículo_maximo_con_otra_funcion(self):
        # Con otra función de comparación, el mismo código sirve al revés.
        m = MonticuloMin(menor=lambda a, b: a > b)
        for x in [3, 9, 1, 7]:
            m.insertar(x)
        self.assertEqual(vaciar(m), [9, 7, 3, 1])

    def test_compara_textos(self):
        m = MonticuloMin()
        for x in ["rata", "antorcha", "daga"]:
            m.insertar(x)
        self.assertEqual(vaciar(m), ["antorcha", "daga", "rata"])


class TestComoAgenda(unittest.TestCase):
    """Lo que de verdad le importa al juego: orden por (tiempo, secuencia)."""

    def test_empates_por_tiempo_se_resuelven_por_secuencia(self):
        agenda = MonticuloMin(menor=menor_evento)
        # Varios eventos en el mismo instante, insertados en desorden
        for tiempo, secuencia, nombre in [
            (100, 4, "jugador"),
            (66, 2, "rata #1"),
            (100, 1, "veneno"),
            (100, 3, "rata #2"),
            (66, 5, "trampa"),
        ]:
            agenda.insertar(Evento(tiempo, secuencia, nombre))
        orden = [e.nombre for e in vaciar(agenda)]
        self.assertEqual(orden, ["rata #1", "trampa", "veneno", "rata #2", "jugador"])

    def test_mismo_resultado_sin_importar_el_orden_de_insercion(self):
        # Determinismo (§2.3): el orden de salida depende solo de (tiempo, secuencia)
        eventos = [(t, s) for s, t in enumerate([50, 10, 50, 30, 10, 50, 20, 30])]
        esperado = sorted(eventos)
        azar = random.Random(99)
        for _ in range(20):
            mezclados = eventos[:]
            azar.shuffle(mezclados)
            agenda = MonticuloMin(menor=menor_evento)
            for t, s in mezclados:
                agenda.insertar(Evento(t, s, f"e{s}"))
            salida = [(e.tiempo, e.secuencia) for e in vaciar(agenda)]
            self.assertEqual(salida, esperado)

    def test_simulacion_de_bucle_de_eventos(self):
        # Como el bucle del juego: sacar el menor y programar su siguiente acción.
        agenda = MonticuloMin(menor=menor_evento)
        secuencia = 0
        for nombre, velocidad in [("jugador", 100), ("rata", 150), ("murcielago", 200)]:
            agenda.insertar(Evento(0, secuencia, (nombre, velocidad)))
            secuencia += 1
        reloj_anterior = -1
        for _ in range(3000):
            e = agenda.extraer_min()
            self.assertGreaterEqual(e.tiempo, reloj_anterior, "el reloj nunca retrocede")
            reloj_anterior = e.tiempo
            nombre, velocidad = e.nombre
            intervalo = max(1, 100 * 100 // velocidad)
            agenda.insertar(Evento(e.tiempo + intervalo, secuencia, e.nombre))
            secuencia += 1
        self.assertEqual(len(agenda), 3)


class TestAleatoria(unittest.TestCase):
    """Miles de inserciones y extracciones al azar contra una referencia."""

    def test_contra_referencia(self):
        azar = random.Random(207)
        m, referencia = MonticuloMin(), []
        for paso in range(6000):
            if azar.random() < 0.6 or not referencia:
                x = azar.randrange(500)
                m.insertar(x)
                referencia.append(x)
            else:
                menor = min(referencia)
                referencia.remove(menor)
                self.assertEqual(m.extraer_min(), menor, f"paso {paso}")
            self.assertEqual(len(m), len(referencia))
            if referencia:
                self.assertEqual(m.ver_min(), min(referencia))
            if paso % 300 == 0:
                revisar_regla(self, m)
        self.assertEqual(vaciar(m), sorted(referencia))


if __name__ == "__main__":
    unittest.main()