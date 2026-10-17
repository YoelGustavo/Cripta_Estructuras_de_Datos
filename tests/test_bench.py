"""Pruebas del --bench (Fase 8). Todas las del bench van en este archivo,
por secciones (B1 agenda, B2...). No miden tiempos (dependen de la
máquina): revisan que lo que se mide sea correcto y comparable."""

import io
import os
import random
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from crypta import main as programa
from crypta.bench import bench
from crypta.bench.bench_agenda import (
    AGENDAS,
    AgendaVectorOrdenado,
    AgendaVectorSinOrden,
    costo_cancelar,
    costo_turno,
    hacer_turnos,
    llenar,
)
from crypta.bench import bench_cache, bench_ciclo, bench_inventario, bench_ordenamiento, bench_red
from crypta.bench.medicion import formato_tiempo, medir, tabla
from crypta.Controlador.GestorContenido import LIMITE_VISITAS_PRECARGA, GestorContenido
from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Mapa import Mapa


# ======================================================================
# B1: la base del bench (medicion.py y bench.py)
# ======================================================================

class TestMedicion(unittest.TestCase):

    def test_medir_devuelve_el_mejor_tiempo(self):
        # perf_counter da inicio y fin de cada vuelta: duran 0.3, 0.1 y 0.2.
        tiempos = iter([0.0, 0.3, 1.0, 1.1, 2.0, 2.2])

        with patch("crypta.bench.medicion.time.perf_counter",
                   side_effect=lambda: next(tiempos)):
            mejor = medir(lambda: None, repeticiones=3)

        self.assertAlmostEqual(mejor, 0.1)

    def test_formato_tiempo_elige_la_unidad(self):
        self.assertEqual(formato_tiempo(0.0000123), "12.3 µs")
        self.assertEqual(formato_tiempo(0.00456), "4.56 ms")
        self.assertEqual(formato_tiempo(1.2), "1.20 s")

    def test_tabla_alinea_las_columnas(self):
        texto = tabla("T", ("n", "a"), [("10", "1.0 µs"), ("1000", "12.0 µs")])
        lineas = texto.splitlines()

        self.assertEqual(lineas[0], "T")
        self.assertEqual(len(set(len(l) for l in lineas[1:])), 1)


class TestEjecutarBench(unittest.TestCase):

    def correr(self, *nombres):
        lineas = []
        bench.ejecutar(list(nombres) or None, rapido=True, salida=lineas.append)
        return "\n".join(str(l) for l in lineas)

    def test_corre_solo_las_secciones_pedidas(self):
        texto = self.correr("agenda")

        self.assertIn("=== Agenda de eventos", texto)
        self.assertNotIn("=== Guardado", texto)

    def test_una_seccion_que_no_existe_se_rechaza(self):
        with self.assertRaises(ValueError) as contexto:
            self.correr("agendaa")

        self.assertIn("agenda", str(contexto.exception))

    def test_main_bench_no_crea_la_vista(self):
        with patch("crypta.bench.bench.ejecutar") as ejecutar, \
                patch("crypta.main.VistaConsola",
                      side_effect=AssertionError("--bench creó la vista")), \
                patch.object(sys, "argv", ["crypta", "--bench"]), \
                redirect_stdout(io.StringIO()):
            codigo = programa.main()

        self.assertEqual(codigo, 0)
        ejecutar.assert_called_once_with()

    # B7: guardado en tabla y --guardar

    def test_el_guardado_sale_en_una_tabla(self):
        texto = bench.ejecutar_guardado(rapido=True)

        self.assertIn("GUARDADO (§4.10)", texto)
        self.assertIn("leer UNA sala", texto)

    def test_guardar_escribe_los_resultados_en_utf8(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "docs", "resultados.txt")

            with redirect_stdout(io.StringIO()):
                codigo = bench.principal(["red", "--rapido", "--guardar", ruta])

            with open(ruta, encoding="utf-8") as archivo:
                texto = archivo.read()

        self.assertEqual(codigo, 0)
        self.assertIn("BITÁCORA (§4.8)", texto)
        self.assertIn("bench completo en", texto)


# ======================================================================
# B1: la agenda contra las alternativas descartadas (§4.1)
# ======================================================================

def recorrido(clase, semilla, pasos=400):
    """Programar, sacar y cancelar al azar; devuelve (tiempo, secuencia,
    actor) de cada evento que salió, en orden."""
    azar = random.Random(semilla)
    agenda = clase()
    vivos = llenar(agenda, 30, azar)
    salieron = []

    for _ in range(pasos):
        decision = azar.random()

        if decision < 0.6 and len(agenda) > 0:
            evento = agenda.siguiente()
            if evento is not None:
                salieron.append((evento.tiempo, evento.secuencia, evento.objetivo))
                vivos.append(agenda.programar(evento.tiempo + azar.choice((50, 66, 100)),
                                              "turno", evento.objetivo))
        elif decision < 0.8:
            vivos.append(agenda.programar(azar.randrange(1000), "turno", "nuevo"))
        elif vivos:
            agenda.cancelar(vivos.pop(azar.randrange(len(vivos))))

    return salieron


class TestAgendasComparables(unittest.TestCase):
    """Si las alternativas no dieran el MISMO orden que la Agenda del juego,
    compararlas no tendría sentido."""

    def test_las_tres_dan_el_mismo_orden(self):
        for semilla in range(5):
            esperado = recorrido(Agenda, semilla)

            self.assertGreater(len(esperado), 100)
            self.assertEqual(recorrido(AgendaVectorOrdenado, semilla), esperado)
            self.assertEqual(recorrido(AgendaVectorSinOrden, semilla), esperado)

    def test_empates_por_secuencia(self):
        for clase in (AgendaVectorOrdenado, AgendaVectorSinOrden):
            agenda = clase()
            a = agenda.programar(10, "a")
            b = agenda.programar(10, "b")
            agenda.programar(5, "c")

            self.assertEqual([agenda.siguiente().tipo for _ in range(3)],
                             ["c", "a", "b"])
            self.assertIsNone(agenda.siguiente())

    def test_los_turnos_mantienen_la_cantidad_de_pendientes(self):
        for _, clase in AGENDAS:
            agenda = clase()
            azar = random.Random(1)
            llenar(agenda, 50, azar)
            hacer_turnos(agenda, 200, azar)

            self.assertEqual(len(agenda), 50)

    def test_los_costos_son_tiempos_positivos(self):
        for _, clase in AGENDAS:
            self.assertGreater(costo_turno(clase, 20, 50, repeticiones=1), 0)
            self.assertGreater(costo_cancelar(clase, 20, 5, repeticiones=1), 0)

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench.bench_agenda.ejecutar(rapido=True)

        self.assertEqual(texto.count("AGENDA DE EVENTOS"), 2)
        for nombre, _ in AGENDAS:
            self.assertIn(nombre, texto)


# ======================================================================
# B2: el ciclo entre dos decisiones (§5.2) y lo que el bench encontró
# ======================================================================

class MonticuloConIntercambios:
    """El montículo como estaba ANTES del B2 (intercambiando en cada nivel):
    la referencia para comprobar que la técnica del hueco es el MISMO
    algoritmo. Compara solo la clave (x[0]), como el montículo."""

    def __init__(self):
        self.a = []

    def insertar(self, x):
        self.a.append(x)
        i = len(self.a) - 1
        while i > 0 and self.a[i][0] < self.a[(i - 1) // 2][0]:
            p = (i - 1) // 2
            self.a[i], self.a[p] = self.a[p], self.a[i]
            i = p

    def extraer_min(self):
        minimo = self.a[0]
        ultimo = self.a.pop()
        if self.a:
            self.a[0] = ultimo
            i, n = 0, len(self.a)
            while True:
                izq, der, menor = 2 * i + 1, 2 * i + 2, i
                if izq < n and self.a[izq][0] < self.a[menor][0]:
                    menor = izq
                if der < n and self.a[der][0] < self.a[menor][0]:
                    menor = der
                if menor == i:
                    break
                self.a[i], self.a[menor] = self.a[menor], self.a[i]
                i = menor
        return minimo


class TestMonticuloConHueco(unittest.TestCase):

    def test_deja_el_arreglo_igual_que_con_intercambios(self):
        # Mismo arreglo interno = misma agenda = misma partida (el replay y
        # las partidas guardadas no notan el cambio). Los elementos son
        # (clave, número) y solo se compara la clave: con claves repetidas,
        # el número deja ver si dos iguales quedaron en otro lugar.
        for semilla in range(200):
            azar = random.Random(semilla)
            nuevo = MonticuloMin(lambda a, b: a[0] < b[0])
            viejo = MonticuloConIntercambios()

            for paso in range(300):
                if azar.random() < 0.6 or len(nuevo) == 0:
                    x = (azar.randint(0, 40), paso)
                    nuevo.insertar(x)
                    viejo.insertar(x)
                else:
                    self.assertEqual(nuevo.extraer_min(), viejo.extraer_min())

                self.assertEqual(list(nuevo), viejo.a)


class TestVectorSigueRevisandoIndices(unittest.TestCase):

    def test_obtener_y_asignar_fuera_de_rango(self):
        v = Vector()
        v.agregar("a")

        for i in (-1, 1, 5):
            with self.assertRaises(IndexError):
                v.obtener(i)
            with self.assertRaises(IndexError):
                v.asignar(i, "x")


def mapa_en_linea(cantidad, cargadas):
    """Salas 1..cantidad en fila (cada una con la siguiente al este); solo
    las primeras 'cargadas' con contenido."""
    salas = []
    for i in range(1, cantidad + 1):
        salidas = {}
        if i < cantidad:
            salidas["E"] = {"sala": i + 1}
        if i > 1:
            salidas["O"] = {"sala": i - 1}
        salas.append({"id": i, "nombre": f"S{i}", "salidas": salidas})

    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos([{"sala": i, "enemigos": [], "objetos": [], "trampas": []}
                             for i in range(1, cargadas + 1)])
    return mapa


class FuenteDeContenido:
    def __init__(self):
        self.pedidos = []

    def obtener_contenido(self, cripta_id, salas):
        ids = list(salas)
        self.pedidos.append(ids)
        return {"contenido": [{"sala": i, "enemigos": [], "objetos": [], "trampas": []}
                              for i in ids]}


class TestPrecargaAcotada(unittest.TestCase):

    def gestor(self, mapa):
        fuente = FuenteDeContenido()
        gestor = GestorContenido(fuente, mapa, "c")
        self.addCleanup(gestor.cerrar)
        return gestor, fuente

    def test_con_todo_cargado_no_busca_ni_pide(self):
        mapa = mapa_en_linea(400, 400)
        gestor, fuente = self.gestor(mapa)

        with patch.object(mapa, "obtener_sala", wraps=mapa.obtener_sala) as obtener:
            self.assertEqual(len(gestor._salas_para_precargar(1)), 0)

        # Antes recorría las 400; ahora ni empieza la búsqueda.
        self.assertLessEqual(obtener.call_count, 1)
        self.assertIsNone(gestor.precargar_async(1))
        gestor.cerrar()
        self.assertEqual(fuente.pedidos, [])

    def test_cuenta_las_salas_que_faltan(self):
        gestor, _ = self.gestor(mapa_en_linea(30, 25))
        self.assertEqual(gestor._sin_cargar, 5)

        gestor.garantizar_sala(27)
        self.assertEqual(gestor._sin_cargar, 4)

        gestor.precargar_desde(27)                  # trae 26, 28, 29 y 30
        self.assertEqual(gestor._sin_cargar, 0)

    def test_lo_que_esta_lejos_no_se_busca(self):
        # Faltan las salas 391..400, a más de LIMITE_VISITAS_PRECARGA salas.
        gestor, _ = self.gestor(mapa_en_linea(400, 390))

        self.assertEqual(len(gestor._salas_para_precargar(1)), 0)

        # Desde la 370 (a 21-30 salas, en los dos sentidos ~60 visitas) sí.
        cerca = gestor._salas_para_precargar(370)
        self.assertEqual([cerca.obtener(i).id for i in range(len(cerca))],
                         list(range(391, 401)))


class TestBenchCiclo(unittest.TestCase):

    def test_mide_las_dos_cosas_sobre_la_misma_partida(self):
        # medir() falla si el controlador jugara otra partida que el modelo
        # o si pidiera contenido por red.
        m = bench_ciclo.medir(9, acciones=4, calentamiento=1, vueltas=2)

        self.assertEqual(len(m.modelo), 4)
        self.assertEqual(len(m.ciclo), 4)
        self.assertGreater(m.eventos_por_accion, 9)   # todos actúan
        self.assertIn(m.cumple(), (True, False))

    def test_percentil(self):
        m = bench_ciclo.Medicion(0)
        tiempos = Vector()
        for x in (5, 1, 4, 2, 3, 10, 9, 8, 7, 6):
            tiempos.agregar(x)

        self.assertEqual(m.percentil(tiempos, 50), 5)
        self.assertEqual(m.percentil(tiempos, 95), 10)
        self.assertEqual(m.maximo(tiempos), 10)
        self.assertEqual(m.media(tiempos), 5.5)

    def test_los_enemigos_de_la_sala_inicial_se_activan(self):
        partida = bench_ciclo.partida_de_carga(12, bench_ciclo.CATALOGO.get,
                                               cantidad_salas=25)
        presentes = partida.enemigos_presentes()

        self.assertEqual(len(presentes), 12)
        self.assertTrue(all(presentes.obtener(i).esta_activo() for i in range(12)))

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench_ciclo.ejecutar(rapido=True)

        self.assertIn("CICLO ENTRE DOS DECISIONES", texto)
        self.assertIn("PRECARGA", texto)


# ======================================================================
# B3: la caché (§4.4)
# ======================================================================

class TestBenchCache(unittest.TestCase):

    def test_la_alternativa_responde_igual_que_la_cache(self):
        lineal = bench_cache.CacheLineal()
        for i in range(10):
            lineal.insertar(f"itm_{i}", {})

        self.assertTrue(lineal.contiene("itm_3"))
        self.assertFalse(lineal.contiene("itm_99"))

    def test_recuperar_no_usa_la_red(self):
        memoria, disco = bench_cache.costo_recuperar(10)   # _SinRed falla si la usa

        self.assertGreater(memoria, 0)
        self.assertGreater(disco, 0)

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench_cache.ejecutar(rapido=True)

        self.assertEqual(texto.count("CACHÉ (§4.4)"), 2)


# ======================================================================
# B4: inventario e historial (§4.5 y §4.6)
# ======================================================================

class TestBenchInventario(unittest.TestCase):

    def test_soltar_y_devolver_deja_el_inventario_igual(self):
        # Si no quedara igual, cada vuelta mediría otra cosa.
        bench_inventario.costo_soltar_lista(5, 2, vueltas=3)   # no debe fallar
        self.assertGreater(bench_inventario.costo_soltar_vector(5, 2, vueltas=3), 0)

    def test_deshacer_usa_de_verdad_el_pergamino(self):
        deshacer, foto = bench_inventario.costo_deshacer(5, cantidad_salas=25, vueltas=2)

        self.assertGreater(deshacer, 0)
        self.assertGreater(foto, 0)

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench_inventario.ejecutar(rapido=True)

        self.assertIn("INVENTARIO (§4.5)", texto)
        self.assertIn("HISTORIAL (§4.6)", texto)


# ======================================================================
# B5: ordenamiento (§4.9)
# ======================================================================

class TestBenchOrdenamiento(unittest.TestCase):

    def test_los_patrones_tienen_la_forma_que_dicen(self):
        def descensos(datos):
            return sum(1 for a, b in zip(datos, datos[1:]) if b < a)

        n = 200
        self.assertEqual(descensos(bench_ordenamiento.generar("invertido", n)), n - 1)
        self.assertEqual(descensos(bench_ordenamiento.generar("dos bloques", n)), 1)
        self.assertLessEqual(descensos(bench_ordenamiento.generar("casi ordenado", n)), n // 50)
        self.assertEqual(sorted(bench_ordenamiento.generar("aleatorio", n)), list(range(n)))

    def test_mide_los_dos_algoritmos_y_lo_que_elige(self):
        patron, n, _, _, elegido, bien = bench_ordenamiento.fila("aleatorio", 30)

        self.assertEqual((patron, n), ("aleatorio", "30"))
        self.assertIn(elegido, ("insercion", "mergesort"))
        self.assertIn(bien, ("sí", "NO"))

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench_ordenamiento.ejecutar(rapido=True)

        self.assertEqual(texto.count("ORDENAMIENTO (§4.9)"), 2)


# ======================================================================
# B6: bitácora y red (§4.8 y §5.1)
# ======================================================================

class TestBenchRed(unittest.TestCase):

    def test_las_dos_bitacoras_se_quedan_en_el_tope(self):
        for clase in (bench_red.BitacoraCola, bench_red.BitacoraVector):
            bitacora = clase(20)
            for i in range(50):
                bitacora.agregar(f"m{i}")
            self.assertEqual(len(bitacora), 20)

    def test_el_juego_pide_menos_que_la_forma_ingenua(self):
        _, contenidos = bench_red.cripta_en_cuadricula(25)
        with tempfile.TemporaryDirectory() as carpeta:
            fria, caliente = bench_red.solicitudes_del_juego(25, carpeta)

        self.assertLess(fria, bench_red.solicitudes_ingenuas(contenidos))
        self.assertEqual(caliente, 0)

    def test_la_seccion_arma_las_dos_tablas(self):
        texto = bench_red.ejecutar(rapido=True)

        self.assertIn("BITÁCORA (§4.8)", texto)
        self.assertIn("RED (§4.2 y §5.1)", texto)


if __name__ == "__main__":
    unittest.main()
