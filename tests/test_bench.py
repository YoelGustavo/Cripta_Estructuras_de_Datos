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
from crypta.bench import bench_cache, bench_ciclo, bench_inventario, bench_ordenamiento, bench_rastro, bench_red
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
        with patch("crypta.bench.bench.ejecutar", return_value=0) as ejecutar, \
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


# ======================================================================
# Rastro (§4.7)
# ======================================================================

class TestBenchRastro(unittest.TestCase):

    def test_la_lista_de_huellas_decide_igual_que_el_juego(self):
        from crypta.Modelo.Rastreador import sala_con_rastro_mas_fresco

        mapa, huellas, reloj, _ = bench_rastro.preparar(25, 7)
        for id_sala in (1, 2, 3, 6, 7, 25):
            sala = mapa.obtener_sala(id_sala)
            for instante in (reloj - 100, reloj + 250, reloj + 1000):
                self.assertIs(huellas.decidir(sala, instante),
                              sala_con_rastro_mas_fresco(sala, instante))

    def test_la_seccion_arma_la_tabla(self):
        self.assertIn("RASTRO (§4.7)", bench_rastro.ejecutar(rapido=True))


# ======================================================================
# Capacidad 001: secciones de --bench del cazador (B1 a B9 de
# specs/001-terreno-cazador/contracts/bench.md). Corren en modo rápido; no
# exigen los límites (eso lo comprueba el --bench completo, T086).
# ======================================================================

SECCIONES_CAZADOR = ("cazadores", "rangos", "tamano", "compartido",
                     "reutilizar", "equivalencia", "ciclo_cazadores",
                     "escala", "distancias")


class TestBenchCazador(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Corre una sola vez todas las secciones nuevas, en modo rápido,
        con una red que falla si se la llama y una vista que falla si se
        crea (FR-034, HU4-7)."""
        lineas = []

        with patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                   side_effect=AssertionError("--bench usó la red")), \
                patch("crypta.Vista.VistaConsola.VistaConsola.__init__",
                      side_effect=AssertionError("--bench creó la vista")), \
                patch("crypta.Adaptadores.FuenteOffline.FuenteOffline.__init__",
                      side_effect=AssertionError("--bench usó una fuente")):
            cls.codigo = bench.ejecutar(list(SECCIONES_CAZADOR), rapido=True,
                                        salida=lineas.append)

        cls.texto = "\n".join(str(linea) for linea in lineas)

    def seccion(self, titulo):
        """El texto de una sección, desde su título hasta la siguiente."""
        inicio = self.texto.index(f"=== {titulo}")
        fin = self.texto.find("\n=== ", inicio + 1)
        return self.texto[inicio:] if fin < 0 else self.texto[inicio:fin]

    # HU4-1 -------------------------------------------------------------

    def test_hu4_1_misma_semilla_misma_cripta(self):
        """FR-028, SC-006, HU4-1: dos generaciones con la misma semilla dan
        la misma huella (salas, salidas, costos, puertas y cazadores)."""
        from crypta.bench.bench_cazador import CriptaSintetica, huella

        def generar(semilla):
            cripta = CriptaSintetica(2000, semilla)
            cazadores = cripta.ubicar_cazadores(50, cripta.rango_pequeno())
            return huella(cripta, cazadores)

        self.assertEqual(generar(11), generar(11))
        self.assertNotEqual(generar(11), generar(12))

    def test_hu4_1_la_cripta_tiene_costos_variables_y_puertas(self):
        """FR-028: costos enteros en [1, 500], algunas salidas quitadas y
        una fracción con puerta."""
        from crypta.bench.bench_cazador import CriptaSintetica

        cripta = CriptaSintetica(2000, 11)
        costos = []
        salidas = 0
        for sala in cripta.esqueleto:
            for datos in sala["salidas"].values():
                salidas += 1
                if "costo" in datos:
                    costos.append(datos["costo"])

        self.assertEqual(len(cripta.esqueleto), 2000)
        self.assertTrue(all(1 <= c <= 500 for c in costos))
        self.assertGreater(len(set(costos)), 100)
        self.assertLess(salidas, 4 * 2000 - 2 * (50 + 40))   # hay quitadas
        self.assertGreater(len(cripta.puertas), 0)

    def test_hu4_1_la_region_del_jugador_es_igual_en_2000_y_20000(self):
        """FR-030, FR-036: las distancias de las ~100 salas más cercanas
        al jugador son las mismas en las dos criptas."""
        from crypta.bench.bench_cazador import _cripta

        chica = _cripta(2000)               # las mismas que usó el --bench
        grande = _cripta(20000)
        rango = chica.rango_pequeno()

        def region(cripta):
            orden = cripta.salas_en_orden(rango)
            return [(cripta.coordenadas(orden.obtener(i)[0]),
                     orden.obtener(i)[1]) for i in range(len(orden))]

        self.assertEqual(rango, grande.rango_pequeno())
        self.assertEqual(region(chica), region(grande))
        self.assertGreaterEqual(len(region(chica)), 100)

    # HU4-2 y HU4-3 -----------------------------------------------------

    def test_hu4_2_cazadores_repartidos_dentro_de_su_rango(self):
        """FR-029: ninguno en la sala del jugador y todos dentro de su
        rango, a distancias distintas."""
        from crypta.bench.bench_cazador import CriptaSintetica

        cripta = CriptaSintetica(2000, 11)
        for rango in (cripta.rango_pequeno(), cripta.rango_mediano()):
            salas = cripta.ubicar_cazadores(50, rango)
            distancias = [cripta.distancia_al_jugador(salas.obtener(i))
                          for i in range(len(salas))]

            self.assertEqual(len(salas), 50)
            self.assertNotIn(0, distancias)
            self.assertTrue(all(d is not None and d <= rango
                                for d in distancias))
            self.assertGreater(len(set(distancias)), 25)

    def test_hu4_2_b1_reporta_uno_y_cincuenta(self):
        """FR-029, HU4-2: B1 con 1 y 50 cazadores."""
        texto = self.seccion("B1")
        self.assertRegex(texto, r"\n\s+1\s")
        self.assertRegex(texto, r"\n\s+50\s")
        self.assertIn("por decisión", texto)

    def test_hu4_3_b2_y_b3(self):
        """FR-030, HU4-3: B2 con rango pequeño y grande; B3 con 2000 y
        20000 salas."""
        b2 = self.seccion("B2")
        self.assertIn("pequeño", b2)
        self.assertIn("grande", b2)
        self.assertIn("salas asentadas", b2)

        b3 = self.seccion("B3")
        self.assertRegex(b3, r"\n\s+2000\s")
        self.assertRegex(b3, r"\n\s+20000\s")

    # HU4-4 y HU4-5 -----------------------------------------------------

    def test_hu4_4_b4_compartido_frente_a_por_cazador(self):
        """FR-031, HU4-4: con 1, 10 y 50 cazadores, puertas estables e
        inestables, y cuál gana."""
        texto = self.seccion("B4")
        for cantidad in ("1", "10", "50"):
            self.assertRegex(texto, rf"\n\s+{cantidad}\s")
        self.assertIn("estables", texto)
        self.assertIn("inestables", texto)
        self.assertIn("gana", texto)

    def test_hu4_5_b5_las_tres_variantes(self):
        """FR-032, HU4-5: recalcular, invalidación total y selectiva, con
        puertas casi estables e inestables; tiempo, búsquedas y salas."""
        texto = self.seccion("B5")
        for variante in ("recalcular siempre", "invalidación total",
                         "selectiva"):
            self.assertIn(variante, texto)
        for columna in ("casi estables", "inestables", "búsquedas",
                        "salas asentadas"):
            self.assertIn(columna, texto)

    # HU4-6 -------------------------------------------------------------

    def test_hu4_6_b6_sin_diferencias(self):
        """FR-033, HU4-6: todas las decisiones de B4 y B5 coinciden con el
        cálculo desde cero, y el código de salida es 0."""
        texto = self.seccion("B6")
        self.assertIn("0 diferencias", texto)
        self.assertNotIn("ERROR", self.texto)
        self.assertEqual(self.codigo, 0)

    def test_hu4_6_una_variante_saboteada_da_error(self):
        """FR-033, HU4-6: si una variante decide mal, B6 imprime ERROR y el
        --bench sale con código distinto de 0."""
        from crypta.bench import bench_cazador
        from crypta.Modelo.Perseguidor import Perseguidor

        class Saboteado(Perseguidor):
            def decidir(self, cazador, sala_jugador):
                decision = super().decidir(cazador, sala_jugador)
                if self.decisiones % 7 == 0:
                    decision.costo += 1
                return decision

        texto, errores = bench_cazador.ejecutar_equivalencia(
            rapido=True, fabrica=Saboteado)
        self.assertGreater(errores, 0)
        self.assertIn("ERROR", texto)

        with patch.object(bench_cazador, "Perseguidor", Saboteado), \
                redirect_stdout(io.StringIO()):
            codigo = bench.principal(["equivalencia", "--rapido"])
        self.assertNotEqual(codigo, 0)

    # HU4-7 -------------------------------------------------------------

    def test_hu4_7_sin_vista_ni_red(self):
        """FR-034, HU4-7: todas las secciones corrieron con la red, las
        fuentes y la vista saboteadas (setUpClass)."""
        for titulo in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9"):
            self.assertIn(f"=== {titulo}", self.texto)

    # HU4-8, HU4-9 y HU4-10 ---------------------------------------------

    def test_hu4_8_b7_reporta_p95_y_si_cumple(self):
        """FR-035, HU4-8: media, p95, máximo y ¿cumple? (p95 < 20 ms)."""
        texto = self.seccion("B7")
        for columna in ("media", "p95", "máximo", "¿cumple?", "50"):
            self.assertIn(columna, texto)

    def test_hu4_8_b7_tambien_corre_sobre_la_cripta_oficial(self):
        """FR-035: si hay copia local de la cripta oficial, B7 la mide
        también (aquí, una copia falsa armada con el generador)."""
        import json
        from crypta.bench import bench_ciclo
        from crypta.bench.bench_cazador import CriptaSintetica

        cripta = CriptaSintetica(2000, 11)
        ficha = bench_ciclo._ficha_cazador_bench(cripta.rango_mediano())
        contenidos = cripta.contenidos(cripta.ubicar_cazadores(
            20, cripta.rango_mediano()))

        with tempfile.TemporaryDirectory() as carpeta:
            with open(os.path.join(carpeta, "cripta-referencia.json"), "w",
                      encoding="utf-8") as archivo:
                json.dump({"version": "v", "esqueleto": cripta.esqueleto,
                           "contenidos": contenidos,
                           "datos_generales": {
                               "sala_inicial": cripta.sala_jugador.id}},
                          archivo)
            with open(os.path.join(carpeta, "catalogo.json"), "w",
                      encoding="utf-8") as archivo:
                json.dump({"version": "c", "fichas": {ficha["id"]: ficha}},
                          archivo)

            partida = bench_ciclo.partida_de_referencia(carpeta)
            texto = bench_ciclo.ejecutar_ciclo_cazadores(rapido=True,
                                                         carpeta=carpeta)

        activos = 0
        salas = partida.mapa.obtener_todas()
        for i in range(len(salas)):
            for j in range(salas.obtener(i).cantidad_enemigos()):
                activos += salas.obtener(i).enemigo_en(j).esta_activo()

        self.assertEqual(activos, 20)
        self.assertIn("oficial", texto)
        self.assertIsNone(bench_ciclo.partida_de_referencia(
            os.path.join(tempfile.gettempdir(), "no-existe-cripta")))

    def test_hu4_9_b3_reporta_el_cociente(self):
        """FR-036, HU4-9: cociente 20000 / 2000 y ¿cumple? (< 2)."""
        texto = self.seccion("B3")
        self.assertIn("cociente", texto)
        self.assertIn("¿cumple?", texto)

    def test_hu4_10_b8_reporta_el_cociente_por_cazador(self):
        """FR-037, HU4-10: 10, 25, 50 y 100; cociente 100 / 10 y
        ¿cumple? (≤ 2)."""
        texto = self.seccion("B8")
        for cantidad in ("10", "25", "50", "100"):
            self.assertRegex(texto, rf"\n\s+{cantidad}\s")
        self.assertIn("por cazador", texto)
        self.assertIn("cociente", texto)
        self.assertIn("¿cumple?", texto)

    def test_b9_vectores_con_marca_frente_a_arbol(self):
        """research D5: la misma búsqueda guardada en vectores con marca y
        en ArbolBusqueda da las mismas distancias."""
        from crypta.bench.bench_cazador import (
            CriptaSintetica, DistanciasEnArbol, entradas_abiertas,
        )
        from crypta.estructuras.DistanciasLimitadas import DistanciasLimitadas

        cripta = CriptaSintetica(2000, 11)
        origen = cripta.sala_jugador.indice
        con_vectores = DistanciasLimitadas(2000, entradas_abiertas(cripta.mapa))
        con_arbol = DistanciasEnArbol(entradas_abiertas(cripta.mapa))

        for busqueda in (con_vectores, con_arbol):
            busqueda.reiniciar(origen)
            busqueda.extender_hasta(cripta.rango_mediano())

        self.assertEqual(
            [con_vectores.distancia(n) for n in range(2000)],
            [con_arbol.distancia(n) for n in range(2000)])
        self.assertIn("ArbolBusqueda", self.seccion("B9"))

    def test_main_devuelve_el_codigo_del_bench(self):
        """FR-033: python -m crypta.main --bench devuelve lo que devuelve
        el bench."""
        with patch("crypta.bench.bench.ejecutar", return_value=1), \
                patch.object(sys, "argv", ["crypta", "--bench"]), \
                redirect_stdout(io.StringIO()):
            self.assertEqual(programa.main(), 1)


# ======================================================================
# Capacidad 003: resolubilidad (specs/003-resolubilidad/contracts/bench.md)
# ======================================================================

SECCIONES_RESOLUBILIDAD = ("resol_ingenua", "resol_limite", "resol_crecimiento",
                           "resol_igualdad", "resol_numeracion")


class TestGeneradorResolubilidad(unittest.TestCase):
    """T044 (FR-330; HU5-1)."""

    def test_hu5_1_misma_semilla_misma_cripta_FR_330(self):
        from crypta.bench.bench_resolubilidad import generar_cripta_llaves, huella

        for resoluble in (True, False):
            a = generar_cripta_llaves(7, 300, 40, resoluble)
            b = generar_cripta_llaves(7, 300, 40, resoluble)
            otra = generar_cripta_llaves(8, 300, 40, resoluble)

            self.assertEqual(huella(*a[:3]), huella(*b[:3]))
            self.assertEqual(a[3], b[3])               # mismo barajado
            self.assertNotEqual(huella(*a[:3]), huella(*otra[:3]))

    def verificar(self, generales, esqueleto, llaves):
        from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
        from crypta.Modelo.Verificador import verificar

        mapa = Mapa()
        mapa.cargar_desde_json(esqueleto)
        return verificar(mapa, generales, leer_ubicaciones(llaves, mapa))

    def test_resoluble_una_ronda_por_llave_encadenada_FR_330(self):
        from crypta.bench.bench_resolubilidad import generar_cripta_llaves

        generales, esqueleto, ordenadas, barajadas = generar_cripta_llaves(
            3, 400, 50, resoluble=True)
        resultado = self.verificar(generales, esqueleto, barajadas)

        self.assertTrue(resultado.resoluble)
        self.assertEqual(len(resultado.rondas), 51)   # 50 llaves + la de salida

    def test_no_resoluble_con_ciclo_FR_330(self):
        from crypta.bench.bench_resolubilidad import generar_cripta_llaves

        for semilla in range(6):
            with self.subTest(semilla=semilla):
                generales, esqueleto, _, barajadas = generar_cripta_llaves(
                    semilla, 400, 50, resoluble=False)
                resultado = self.verificar(generales, esqueleto, barajadas)

                self.assertFalse(resultado.resoluble)
                self.assertGreaterEqual(len(resultado.reporte.ciclos), 1)

    def test_ids_con_ceros_y_respuesta_ordenada_y_barajada_FR_330(self):
        from crypta.bench.bench_resolubilidad import generar_cripta_llaves

        _, esqueleto, ordenadas, barajadas = generar_cripta_llaves(5, 2000, 500)
        ids = [entrada["id"] for entrada in ordenadas["llaves"]]

        self.assertIn("itm_llave_00000", ids)
        self.assertIn("itm_llave_00499", ids)
        self.assertEqual(ids, sorted(ids))
        self.assertNotEqual([e["id"] for e in barajadas["llaves"]], ids)
        self.assertEqual(sorted(e["id"] for e in barajadas["llaves"]), ids)
        self.assertLess(abs(len(esqueleto) - 2000), 20)


class TestBenchResolubilidad(unittest.TestCase):
    """T045 (FR-331 a FR-335; HU5-2, HU5-3, HU5-6)."""

    @classmethod
    def setUpClass(cls):
        """Corre una vez las secciones R1 a R5 en modo rápido, con una red
        que falla si se la llama, una vista que falla si se crea y sin
        copias locales (FR-333, HU5-6)."""
        from crypta.bench import bench_resolubilidad

        lineas = []
        cls._carpeta = tempfile.TemporaryDirectory()

        with patch("crypta.Adaptadores.FuenteHTTP.requests.get",
                   side_effect=AssertionError("--bench usó la red")), \
                patch("crypta.Vista.VistaConsola.VistaConsola.__init__",
                      side_effect=AssertionError("--bench creó la vista")), \
                patch("crypta.Adaptadores.FuenteOffline.FuenteOffline.__init__",
                      side_effect=AssertionError("--bench usó una fuente")), \
                patch.object(bench_resolubilidad, "CARPETA_COPIAS",
                             cls._carpeta.name):
            cls.codigo = bench.ejecutar(list(SECCIONES_RESOLUBILIDAD),
                                        rapido=True, salida=lineas.append)

        cls.texto = "\n".join(str(linea) for linea in lineas)

    @classmethod
    def tearDownClass(cls):
        cls._carpeta.cleanup()

    def seccion(self, titulo):
        inicio = self.texto.index(f"=== {titulo}")
        fin = self.texto.find("\n=== ", inicio + 1)
        return self.texto[inicio:] if fin < 0 else self.texto[inicio:fin]

    def test_hu5_6_corren_todas_sin_vista_ni_red_FR_333(self):
        for titulo in ("R1", "R2", "R3", "R4", "R5"):
            self.assertIn(f"=== {titulo}", self.texto)

        self.assertEqual(self.codigo, 0)

    def test_hu5_2_r1_incremental_frente_a_ingenua_FR_331(self):
        texto = self.seccion("R1")
        for columna in ("incremental", "ingenua", "resoluble",
                        "ingenua / incremental"):
            self.assertIn(columna, texto)

    def test_hu5_4_r2_limite_FR_334(self):
        texto = self.seccion("R2")
        for columna in ("media", "p95", "máximo", "cargar esqueleto",
                        "¿cumple?", "sintética resoluble",
                        "sintética no resoluble"):
            self.assertIn(columna, texto)
        self.assertIn("No hay copia local", texto)

    def test_hu5_4_r2_mide_la_cripta_publicada_mas_grande_FR_334(self):
        """R2 mide la copia local más grande que tenga llaves (sin su id en
        el código); las copias sin llaves no cuentan."""
        import json
        from crypta.bench import bench_resolubilidad
        from crypta.bench.bench_resolubilidad import CriptaLlaves

        grande = CriptaLlaves(1, 120, 10)
        chica = CriptaLlaves(2, 60, 5)
        sin_llaves = CriptaLlaves(3, 400, 20)

        with tempfile.TemporaryDirectory() as carpeta:
            for nombre, cripta, llaves in (
                    ("c-grande", grande, grande.llaves_ordenadas),
                    ("c-chica", chica, chica.llaves_ordenadas),
                    ("c-sin-llaves", sin_llaves, None)):
                datos = {"version": "v", "esqueleto": cripta.esqueleto,
                         "contenidos": [], "datos_generales": cripta.generales}
                if llaves is not None:
                    datos["llaves"] = llaves
                with open(os.path.join(carpeta, f"{nombre}.json"), "w",
                          encoding="utf-8") as archivo:
                    json.dump(datos, archivo)

            self.assertEqual(bench_resolubilidad.copia_mas_grande(carpeta)[0],
                             "c-grande")
            texto = bench_resolubilidad.ejecutar_limite(rapido=True,
                                                        carpeta=carpeta)

        self.assertIn("c-grande (publicada)", texto)
        self.assertIsNone(bench_resolubilidad.copia_mas_grande(
            os.path.join(tempfile.gettempdir(), "no-existe-copia")))

    def test_hu5_5_r3_cocientes_FR_335(self):
        texto = self.seccion("R3")
        self.assertIn("cociente", texto)
        self.assertIn("¿cumple?", texto)
        self.assertIn("ingenua", texto)

    def test_hu5_3_r4_sin_diferencias_FR_332(self):
        texto = self.seccion("R4")
        self.assertIn("Total: 0 diferencias", texto)
        self.assertNotIn("ERROR", texto)

    def test_hu5_3_r4_una_ingenua_saboteada_da_error_FR_332(self):
        """FR-332, HU5-3: si la ingenua da otro resultado, R4 imprime ERROR
        y el --bench sale con código distinto de 0."""
        from crypta.bench import bench_resolubilidad
        from crypta.Modelo.VerificadorIngenuo import verificar_ingenuo

        def saboteada(mapa, generales, ubicaciones):
            resultado = verificar_ingenuo(mapa, generales, ubicaciones)
            if resultado.reporte is not None:
                resultado.reporte.no_obtenibles.agregar("itm_llave_falsa")
            else:
                resultado.rondas.agregar(Vector())
            return resultado

        texto, errores = bench_resolubilidad.ejecutar_igualdad(
            rapido=True, ingenuo=saboteada)
        self.assertGreater(errores, 0)
        self.assertIn("ERROR", texto)

        with patch.object(bench_resolubilidad.ejecutar_igualdad,
                          "__defaults__", (False, saboteada)), \
                redirect_stdout(io.StringIO()):
            codigo = bench.principal(["resol_igualdad", "--rapido"])
        self.assertNotEqual(codigo, 0)

    def test_r5_numeracion_y_altura_D1(self):
        texto = self.seccion("R5")
        for columna in ("ordenar + desde_ordenados", "insertar", "barajados",
                        "ordenados", "altura"):
            self.assertIn(columna, texto)
        # Con 500 ids ordenados, insertar da altura 500 (P1 §4.4).
        self.assertRegex(texto, r"500\s+insertar\s+ordenados\s+\S+ \S+\s+500")


if __name__ == "__main__":
    unittest.main()
