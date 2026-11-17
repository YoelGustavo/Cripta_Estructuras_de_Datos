"""Pruebas de la línea de tiempo (capacidad 004).

Fase 2 (T005): lo que usan todas las historias. El historial sin límite, el
tope de tiempo y el callback de `Partida`, y la copia de una partida para
los puntos de control (research D3, D9; FR-407, FR-422, FR-426).

Historia 1 (T014, T016): `historia <t>` e `historia #k` contra el oráculo
tomado de la partida viva (FR-401 a FR-408, FR-423, FR-425).

Historia 2 (T024): la línea respeta el pergamino (FR-410 a FR-412).
"""

import copy
import random
import unittest

from crypta.bench.oraculo_linea import serializar_estado
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Historial import Historial, RegistroAccion
from crypta.Modelo.Partida import TURNO_JUGADOR, AccionInvalida
from tests.ayudas_cripta import (
    catalogo, comando_al_azar, comandos_al_azar, contenido, ficha_cazador,
    ficha_enemigo, nuevo_jugador, partida_con_pergaminos, partida_sintetica,
    sala, salida, FuenteQueFalla,
)
from tests.test_replay_hasta import ConReplay


class _Caja:
    def __init__(self):
        self.valor = 0


def jugar(partida, garantizar, comandos):
    """Ejecuta los comandos y salta los que el juego rechaza."""
    for comando in comandos:
        if partida.terminada:
            return
        try:
            ejecutar_comando(partida, comando, garantizar)
        except (ComandoInvalido, AccionInvalida):
            pass
        except RuntimeError:
            # Una copia que intenta entrar en una sala que la partida viva
            # nunca cargó (solo en _garantizar_desde): no hay red.
            pass


def jugar_al_azar(partida, garantizar, semilla, cantidad):
    azar = random.Random(semilla)
    for _ in range(cantidad):
        if partida.terminada:
            return
        jugar(partida, garantizar, [comando_al_azar(partida, azar)])


def partida_con_cazador():
    """Tres salas en fila; un cazador en la sala del jugador, así su primer
    turno crea la búsqueda compartida (`Perseguidor`)."""
    esqueleto = [sala(1, {"E": salida(2)}),
                 sala(2, {"O": salida(1), "E": salida(3)}),
                 sala(3, {"O": salida(2)})]
    contenidos = [contenido(1, enemigos=(("c-1", "ent_cazador"),))]
    partida = partida_sintetica(esqueleto, contenidos,
                                catalogo(ficha_cazador(rango=1000)))
    partida.jugador.vida_max = partida.jugador.vida = 500
    for _ in range(3):
        partida.esperar()
    return partida


class TestBaseLinea(unittest.TestCase):
    """T005: base común de la línea de tiempo."""

    # --- Historial sin límite (D2; FR-423) ---------------------------------

    def test_fr423_historial_sin_limite(self):
        historial = Historial(limite=None)
        caja = _Caja()

        for i in range(1000):
            historial.registrar(RegistroAccion(f"a{i}"))
            historial.registrar_cambio(Cambio.de_atributo("v", caja, "valor", caja.valor))
            caja.valor = i + 1

        self.assertEqual(len(historial), 1000)

        while historial.puede_deshacer():
            historial.deshacer_ultima()

        self.assertEqual(caja.valor, 0)

    def test_historial_sigue_con_limite_5_por_omision(self):
        historial = Historial()
        for i in range(8):
            historial.registrar(RegistroAccion(f"a{i}"))
        self.assertEqual(len(historial), 5)

        with self.assertRaises(ValueError):
            Historial(0)

    # --- Tope de tiempo y callback (D9; FR-401, FR-426) --------------------

    def test_fr426_tope_y_callback_por_omision_no_cambian_el_juego(self):
        a = partida_con_pergaminos(semilla=11)
        b = partida_con_pergaminos(semilla=11)
        try:
            self.assertIsNone(a.partida.tope_tiempo)
            self.assertIsNone(a.partida.al_ejecutar_evento)

            vistos = []
            b.partida.tope_tiempo = None
            b.partida.al_ejecutar_evento = lambda partida, evento: vistos.append(evento)

            jugar_al_azar(a.partida, a.garantizar, 5, 60)
            jugar_al_azar(b.partida, b.garantizar, 5, 60)

            self.assertEqual(serializar_estado(a.partida), serializar_estado(b.partida))
            self.assertGreater(len(vistos), 0)
        finally:
            a.cerrar()
            b.cerrar()

    def test_fr426_callback_una_vez_por_evento_que_no_es_del_jugador(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            vistos = []
            partida.al_ejecutar_evento = lambda p, evento: vistos.append(evento)

            antes = partida.agenda.siguiente_secuencia
            jugar(partida, cripta.garantizar, ["mover E", "esperar", "esperar"])

            self.assertTrue(all(e.tipo != TURNO_JUGADOR for e in vistos))
            self.assertTrue(all(e.secuencia < partida.agenda.siguiente_secuencia
                                for e in vistos))
            self.assertEqual(len(vistos), len({id(e) for e in vistos}))
            self.assertGreater(partida.agenda.siguiente_secuencia, antes)
        finally:
            cripta.cerrar()

    def test_fr401_con_tope_se_detiene_antes_del_primer_evento_posterior(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E"])     # sala 2, con el errante
            inicio = partida.reloj
            tope = inicio + 40                                  # en medio de «esperar» (100)

            partida.tope_tiempo = tope
            partida.esperar()

            self.assertLessEqual(partida.reloj, tope)
            siguiente = min((e.tiempo for e in partida.agenda.recorrer_pendientes()))
            self.assertGreater(siguiente, tope)
        finally:
            cripta.cerrar()

    def test_fr401_con_tope_en_la_decision_se_detiene_antes_de_decidir(self):
        """Si el siguiente evento es el turno del jugador en t, el estado es
        el de justo antes de esa decisión: los eventos de t que vienen
        después en la agenda no se ejecutan."""
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E"])
            turno = partida.reloj + partida.jugador.intervalo(100)

            partida.tope_tiempo = turno
            partida.esperar()

            self.assertEqual(partida.reloj, turno)
            pendientes = [e for e in partida.agenda.recorrer_pendientes()]
            self.assertTrue(all(e.tiempo > turno or e.tipo != TURNO_JUGADOR
                                for e in pendientes))
        finally:
            cripta.cerrar()

    def test_fr407_deshacer_una_accion_a_medias_deja_todo_igual(self):
        """El tope deja la acción a medias; sus cambios están en su
        `RegistroAccion` y deshacerla restaura el estado (D2, D9). El número
        de secuencia de la agenda no lo rebobina el historial de P1: lo
        restaura el sello de la consulta (D8, T019)."""
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E", "esperar"])
            antes = serializar_estado(partida)
            secuencia = partida.agenda.siguiente_secuencia

            partida.tope_tiempo = partida.reloj + 30
            partida.esperar()
            partida.tope_tiempo = None
            partida.estado.historial.deshacer_ultima()
            partida.agenda._siguiente_secuencia = secuencia      # lo que hace el sello (D8)

            self.assertEqual(serializar_estado(partida), antes)
        finally:
            cripta.cerrar()

    # --- Copia para los puntos de control (D3; FR-422) ---------------------

    def test_fr422_la_copia_comparte_lo_inmutable(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar(partida, cripta.garantizar, ["mover E", "mover E", "mover S"])
            copia = copy.deepcopy(partida)

            self.assertIs(copia._fichas, partida._fichas)

            originales = partida.mapa.obtener_todas()
            copias = copia.mapa.obtener_todas()
            cargadas = 0

            for i in range(len(originales)):
                original = originales.obtener(i)
                copiada = copias.obtener(i)
                self.assertIsNot(copiada, original)
                self.assertEqual(copiada.id, original.id)

                if original.contenido_cargado():
                    cargadas += 1
                    self.assertIs(copiada.contenido, original.contenido)

            self.assertGreaterEqual(cargadas, 3)
        finally:
            cripta.cerrar()

    def test_fr422_la_copia_deja_fuera_lo_que_no_es_estado(self):
        partida = partida_con_cazador()
        partida.al_ejecutar_evento = lambda p, e: None
        self.assertIsNotNone(partida._perseguidor)

        copia = copy.deepcopy(partida)

        self.assertIsNone(copia._perseguidor)
        self.assertIsNone(copia.al_ejecutar_evento)
        self.assertIsNotNone(partida.al_ejecutar_evento)
        self.assertIsNot(copia.bitacora, partida.bitacora)
        self.assertEqual(len(copia.bitacora), 0)
        self.assertGreater(len(partida.bitacora), 0)
        self.assertIsNot(copia.estado.historial, partida.estado.historial)
        self.assertEqual(len(copia.estado.historial), 0)
        self.assertIsNone(copia.estado.historial._limite)

        salas = copia.mapa.obtener_todas()
        for i in range(len(salas)):
            puertas = salas.obtener(i).puertas()
            for j in range(len(puertas)):
                self.assertIsNone(puertas.obtener(j).estado.observador)

        vivas = partida.mapa.obtener_todas().obtener(0).puertas()
        self.assertIs(vivas.obtener(0).estado.observador, partida._perseguidor)

    def test_fr422_la_copia_serializa_igual(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar_al_azar(partida, cripta.garantizar, 3, 40)
            self.assertEqual(serializar_estado(copy.deepcopy(partida)),
                             serializar_estado(partida))
        finally:
            cripta.cerrar()

    def test_fr407_jugar_sobre_la_copia_no_toca_el_original(self):
        cripta = partida_con_pergaminos()
        try:
            partida = cripta.partida
            jugar_al_azar(partida, cripta.garantizar, 4, 30)
            antes = serializar_estado(partida)
            bitacora = len(partida.bitacora)
            azar = partida.azar.getstate()

            copia = copy.deepcopy(partida)
            garantizar_copia = _garantizar_desde(partida, copia)
            jugar_al_azar(copia, garantizar_copia, 9, 20)

            self.assertGreater(copia.acciones_jugador, partida.acciones_jugador)
            self.assertEqual(serializar_estado(partida), antes)
            self.assertEqual(len(partida.bitacora), bitacora)
            self.assertEqual(partida.azar.getstate(), azar)
        finally:
            cripta.cerrar()

    def test_fr422_copia_de_300_salas_sin_subir_el_limite_de_recursion(self):
        """El mapa se copia en dos pasadas (D3): sin eso, `deepcopy` baja por
        la cadena de salas vecinas y pasa el límite de recursión de Python."""
        from crypta.bench.bench_ciclo import CATALOGO, partida_de_carga

        partida = partida_de_carga(20, CATALOGO.get, semilla=1, cantidad_salas=300)
        copia = copy.deepcopy(partida)
        self.assertEqual(serializar_estado(copia), serializar_estado(partida))


def _garantizar_desde(viva, copia):
    """Carga en la copia el contenido de una sala tomándolo de la partida
    viva, sin red (research D7)."""
    def garantizar(id_sala):
        sala_copia = copia.mapa.obtener_sala(id_sala)
        if not sala_copia.contenido_cargado():
            sala_viva = viva.mapa.obtener_sala(id_sala)
            if sala_viva.contenido_cargado():
                sala_copia.asignar_contenido(sala_viva.contenido)
    return garantizar


# ---------------------------------------------------------------------------
# Historia 1 (T014, T016)
# ---------------------------------------------------------------------------

def _linea_y_consulta():
    """Imports de la historia 1, dentro de una función para que las pruebas
    de la fase 2 no dependan de estos módulos."""
    from crypta.Modelo.LineaDeTiempo import ConsultaRechazada, LineaDeTiempo
    from crypta.Modelo.Reconstruccion import consultar
    return LineaDeTiempo, ConsultaRechazada, consultar


def sin_pergamino(comandos):
    """Los pergaminos son de la historia 2: aquí se cambian por «esperar»."""
    for comando in comandos:
        yield "esperar" if comando == "pergamino" else comando


def hasta_acciones(partida, comandos, acciones):
    """Toma comandos hasta que la partida tiene `acciones` acciones."""
    for comando in comandos:
        if partida.acciones_jugador >= acciones:
            return
        yield comando


SEMILLA_LINEA = 23


class Jugada:
    """Una partida jugada con su línea de tiempo y su oráculo."""

    def __init__(self, k, semilla=SEMILLA_LINEA, cantidad=90, acciones=None,
                 cripta=None, partida=None, comandos=None):
        from crypta.bench.oraculo_linea import jugar_con_oraculo

        LineaDeTiempo, _, _ = _linea_y_consulta()
        self.cripta = cripta if cripta is not None else (
            partida_con_pergaminos(semilla) if partida is None else None)
        self.partida = partida if partida is not None else self.cripta.partida
        self.garantizar = None if self.cripta is None else self.cripta.garantizar

        if comandos is None:
            comandos = sin_pergamino(comandos_al_azar(
                self.partida, random.Random(semilla), cantidad))

        if acciones is not None:
            comandos = hasta_acciones(self.partida, comandos, acciones)

        self.linea = LineaDeTiempo(k)
        self.linea.iniciar(self.partida)
        self.oraculo = jugar_con_oraculo(self.partida, self.linea, comandos,
                                         self.garantizar)

    def cerrar(self):
        if self.cripta is not None:
            self.cripta.cerrar()

    def consultar(self, pedido):
        """Texto de `historia <pedido>`: «instante <t>» o «acción #<k>»."""
        _, _, consultar = _linea_y_consulta()
        return formatear(consultar(self.linea, self.ubicar(pedido), self.partida,
                                   ejecutar_comando))

    def ubicar(self, pedido):
        tipo, valor = pedido.split(" ")
        if tipo == "instante":
            return self.linea.ubicar_instante(int(valor), self.partida.reloj)
        return self.linea.ubicar_accion(int(valor[1:]))

    def esperado_en_instante(self, t):
        """El texto del oráculo para el instante t: el de la última entrada
        de instante con tiempo ≤ t, con el encabezado de t."""
        elegida = None
        for i in range(len(self.oraculo)):
            entrada = self.oraculo.obtener(i)
            if entrada.tiempo <= t and entrada.pedido.startswith("instante"):
                elegida = entrada
        lineas = elegida.texto.split("\n", 1)
        return f"HISTORIA instante {t}\n" + lineas[1]

    def instantes_entre_eventos(self):
        """Instantes t estrictamente entre dos entradas de evento seguidas del
        oráculo (sin decisión en medio)."""
        resultado = []
        for i in range(len(self.oraculo) - 1):
            a = self.oraculo.obtener(i)
            b = self.oraculo.obtener(i + 1)
            if a.es_evento and b.es_evento and b.tiempo - a.tiempo >= 2:
                resultado.append((a.tiempo + b.tiempo) // 2)
        return resultado



def formatear(resumen):
    from crypta.Vista.FormatoResumen import formatear_resumen
    return formatear_resumen(resumen)


def partida_de_guardianes(cantidad, velocidad_enemigo, velocidad_jugador):
    """Una sala con `cantidad` guardianes (no se mueven y atacan al jugador)
    y un jugador con vida de sobra."""
    esqueleto = [sala(1, {"E": salida(2)}), sala(2, {"O": salida(1)})]
    enemigos = tuple((f"g-{i}", "ent_guardian") for i in range(1, cantidad + 1))
    contenidos = [contenido(1, enemigos=enemigos)]
    fichas = catalogo(ficha_enemigo("ent_guardian", "guardián",
                                    velocidad=velocidad_enemigo, ataque=4))
    jugador = nuevo_jugador(velocidad=velocidad_jugador, vida_max=500)
    return partida_sintetica(esqueleto, contenidos, fichas, jugador=jugador)


class TestConsultas(unittest.TestCase):
    """T014: `historia <t>` e `historia #k` dan el estado pedido (FR-401 a
    FR-404), comparado con el oráculo, con K = 3, 10 y 22."""

    def test_fr401_fr402_todo_el_oraculo_con_varios_k(self):
        """Cada instante y cada acción que tomó el oráculo, y los instantes
        entre dos eventos, dan el mismo texto reconstruidos."""
        for k in (3, 10, 22):
            jugada = Jugada(k)
            try:
                self.assertGreater(jugada.partida.acciones_jugador, 30)
                for i in range(len(jugada.oraculo)):
                    entrada = jugada.oraculo.obtener(i)
                    with self.subTest(k=k, pedido=entrada.pedido):
                        self.assertEqual(jugada.consultar(entrada.pedido), entrada.texto)

                entre = jugada.instantes_entre_eventos()
                self.assertGreater(len(entre), 0)
                for t in entre:
                    with self.subTest(k=k, entre=t):
                        self.assertEqual(jugada.consultar(f"instante {t}"),
                                         jugada.esperado_en_instante(t))
            finally:
                jugada.cerrar()

    def test_fr403_hu1_1_un_instante_pasado_lleva_su_reloj(self):
        """HU1-1: con la partida mucho más adelante, el resumen muestra el
        reloj de ese estado, no el actual."""
        jugada = Jugada(10, cantidad=200)
        try:
            self.assertGreater(jugada.partida.reloj, 1000)
            eventos = [jugada.oraculo.obtener(i).tiempo for i in range(len(jugada.oraculo))
                       if jugada.oraculo.obtener(i).es_evento
                       and jugada.oraculo.obtener(i).tiempo <= 500]
            t = max(eventos)
            texto = jugada.consultar(f"instante {t}")
            self.assertEqual(texto, jugada.esperado_en_instante(t))
            self.assertIn(f"Reloj: {t}   ", texto)
            self.assertNotIn(f"Reloj: {jugada.partida.reloj}   ", texto)
        finally:
            jugada.cerrar()

    def test_fr403_hu1_2_instante_futuro_se_rechaza(self):
        """HU1-2 (Apéndice B): t mayor que el reloj → mensaje de contracts/cli.md."""
        _, ConsultaRechazada, _ = _linea_y_consulta()
        jugada = Jugada(10, cantidad=30)
        try:
            reloj = jugada.partida.reloj
            with self.assertRaises(ConsultaRechazada) as error:
                jugada.ubicar(f"instante {reloj + 1}")
            self.assertEqual(
                str(error.exception),
                f"No se puede consultar el instante {reloj + 1}: el reloj de la "
                f"partida va en {reloj}.")
        finally:
            jugada.cerrar()

    def test_fr401_hu1_3_tres_eventos_en_el_mismo_instante(self):
        """HU1-3 (Apéndice B): tres guardianes atacan en el instante 100 y el
        jugador no decide en 100 (velocidad 90: decide en 0, 111, 222): el
        estado en 100 es el de después de los tres ataques."""
        partida = partida_de_guardianes(3, velocidad_enemigo=100, velocidad_jugador=90)
        en_100 = []
        jugada = Jugada(3, partida=partida, comandos=["esperar", "esperar", "esperar"])
        try:
            self.assertNotIn(100, [jugada.linea.decisiones.obtener(i)[0]
                                   for i in range(len(jugada.linea.decisiones))])
            # Repetir sobre una copia para contar los eventos del instante 100.
            copia = copy.deepcopy(jugada.linea.puntos.obtener(0).partida)
            copia.al_ejecutar_evento = (
                lambda p, e: en_100.append(e) if e.tiempo == 100 else None)
            jugar(copia, None, ["esperar", "esperar"])
            self.assertEqual(len(en_100), 3)

            texto = jugada.consultar("instante 100")
            self.assertEqual(texto, jugada.esperado_en_instante(100))
            vida_antes = int(jugada.consultar("instante 99").split("Vida: ")[1].split("/")[0])
            vida_en_100 = int(texto.split("Vida: ")[1].split("/")[0])
            self.assertLess(vida_en_100, vida_antes)
        finally:
            jugada.cerrar()

    def test_fr401_hu1_4_decision_y_evento_posterior_del_mismo_instante(self):
        """HU1-4: el jugador decide en 100 y un guardián (velocidad 200) tiene
        un turno en 100 programado después: el estado en 100 es el de antes
        de la decisión, sin ese ataque."""
        partida = partida_de_guardianes(1, velocidad_enemigo=200, velocidad_jugador=100)
        jugada = Jugada(3, partida=partida, comandos=["esperar", "esperar", "esperar"])
        try:
            self.assertEqual(jugada.linea.decisiones.obtener(1)[0], 100)
            texto = jugada.consultar("instante 100")
            self.assertEqual(texto, jugada.consultar("acción #2").replace(
                "HISTORIA acción #2", "HISTORIA instante 100"))
            self.assertEqual(texto, jugada.esperado_en_instante(100))

            # El ataque de 100 sí llegó: en 101 la vida es menor.
            vida_100 = int(texto.split("Vida: ")[1].split("/")[0])
            vida_101 = int(jugada.consultar("instante 101").split("Vida: ")[1].split("/")[0])
            self.assertLess(vida_101, vida_100)
        finally:
            jugada.cerrar()

    def test_fr402_fr404_hu1_5_cuarenta_acciones(self):
        """HU1-5: con 40 acciones, #1, #20 y #41 (= estado actual)."""
        from crypta.Modelo.Resumen import armar_resumen, pedido_accion

        jugada = Jugada(10, cantidad=400, acciones=40)
        try:
            self.assertEqual(jugada.partida.acciones_jugador, 40)
            for k in (1, 20, 41):
                entrada = [jugada.oraculo.obtener(i) for i in range(len(jugada.oraculo))
                           if jugada.oraculo.obtener(i).pedido == f"acción #{k}"][-1]
                self.assertEqual(jugada.consultar(f"acción #{k}"), entrada.texto)

            actual = formatear(armar_resumen(jugada.partida, pedido_accion(41)))
            self.assertEqual(jugada.consultar("acción #41"), actual)
        finally:
            jugada.cerrar()

    def test_fr404_hu1_6_acciones_fuera_de_rango(self):
        """HU1-6: #0 y #42 con 40 acciones → mensaje de contracts/cli.md."""
        _, ConsultaRechazada, _ = _linea_y_consulta()
        jugada = Jugada(10, cantidad=400, acciones=40)
        try:
            for k in (0, 42):
                with self.assertRaises(ConsultaRechazada) as error:
                    jugada.ubicar(f"acción #{k}")
                self.assertEqual(
                    str(error.exception),
                    f"No hay acción #{k}: la partida tiene 40 acciones "
                    f"(consulta de #1 a #41).")
        finally:
            jugada.cerrar()

    def test_fr401_casos_borde(self):
        """`historia 0`; t = reloj actual (= estado actual); consulta que cae
        justo en un punto de control (no re-ejecuta nada)."""
        from crypta.Modelo.Resumen import armar_resumen, pedido_instante

        jugada = Jugada(5, cantidad=80)
        try:
            self.assertEqual(jugada.consultar("instante 0"),
                             jugada.esperado_en_instante(0))

            reloj = jugada.partida.reloj
            self.assertEqual(jugada.consultar(f"instante {reloj}"),
                             formatear(armar_resumen(jugada.partida, pedido_instante(reloj))))

            # #11 = estado antes de la acción 11 = punto de control con ancla 10.
            texto = jugada.consultar("acción #11")
            self.assertEqual(jugada.linea.ultimas_reejecutadas, 0)
            entrada = [jugada.oraculo.obtener(i) for i in range(len(jugada.oraculo))
                       if jugada.oraculo.obtener(i).pedido == "acción #11"][-1]
            self.assertEqual(texto, entrada.texto)
        finally:
            jugada.cerrar()


class TestConsultaNoCambiaNada(unittest.TestCase):
    """T016: una consulta no cambia nada (FR-407, FR-408; SC-403)."""

    def consultas_al_azar(self, jugada, azar, cantidad):
        pedidos = []
        n = jugada.partida.acciones_jugador
        for _ in range(cantidad):
            if azar.random() < 0.5:
                pedidos.append(f"acción #{azar.randint(1, n + 1)}")
            else:
                pedidos.append(f"instante {azar.randint(0, jugada.partida.reloj)}")
        return pedidos

    def test_fr407_hu1_8_treinta_consultas_no_cambian_la_partida(self):
        """HU1-8 (Apéndice B): ni el estado, ni el generador, ni el
        historial del pergamino, ni el reloj, ni las acciones, ni las
        solicitudes."""
        jugada = Jugada(10, cantidad=120)
        try:
            partida = jugada.partida
            antes = serializar_estado(partida)
            azar = partida.azar.getstate()
            historial = partida.estado.historial
            largo = len(historial)
            ultima = historial._acciones.ultimo().valor
            reloj, acciones = partida.reloj, partida.acciones_jugador
            solicitudes = jugada.cripta.fuente.cantidad_solicitudes()

            for pedido in self.consultas_al_azar(jugada, random.Random(4), 30):
                jugada.consultar(pedido)

            self.assertEqual(serializar_estado(partida), antes)
            self.assertEqual(partida.azar.getstate(), azar)
            self.assertIs(partida.estado.historial, historial)
            self.assertEqual(len(historial), largo)
            self.assertIs(historial._acciones.ultimo().valor, ultima)
            self.assertEqual((partida.reloj, partida.acciones_jugador), (reloj, acciones))
            self.assertEqual(jugada.cripta.fuente.cantidad_solicitudes(), solicitudes)
        finally:
            jugada.cerrar()

    def test_fr407_hu1_12_sin_red(self):
        """HU1-12: con la fuente cambiada por una que falla, las consultas no
        hacen ninguna solicitud (las salas salen de la partida viva)."""
        jugada = Jugada(10, cantidad=60)
        try:
            cargadas = sum(1 for i in range(len(jugada.partida.mapa.obtener_todas()))
                           if jugada.partida.mapa.obtener_todas().obtener(i).contenido_cargado())
            self.assertLess(cargadas, 9)          # quedan salas sin descargar
            self.assertGreater(cargadas, 2)
            solicitudes = jugada.cripta.fuente.cantidad_solicitudes()
            jugada.cripta.gestor._fuente = FuenteQueFalla()

            for pedido in self.consultas_al_azar(jugada, random.Random(8), 40):
                jugada.consultar(pedido)

            self.assertEqual(jugada.cripta.fuente.cantidad_solicitudes(), solicitudes)
        finally:
            jugada.cerrar()

    def test_d8_el_punto_queda_igual_y_las_consultas_se_repiten(self):
        """D7 y D8: cada punto serializa igual antes y después de 50
        consultas, sin el contenido de las salas que las consultas cargaron
        en él (quedan cargadas, decisión del grupo); y repetir una consulta
        da el mismo texto."""
        jugada = Jugada(10, cantidad=150)
        try:
            puntos = jugada.linea.puntos
            # Copias tomadas ANTES de consultar: no las toca ninguna consulta.
            originales = [copy.deepcopy(puntos.obtener(j).partida)
                          for j in range(len(puntos))]
            pedidos = self.consultas_al_azar(jugada, random.Random(15), 50)
            textos = [jugada.consultar(pedido) for pedido in pedidos]

            alguna_cargada = False
            for j in range(len(puntos)):
                punto = puntos.obtener(j)
                omitir = punto.salas_cargadas
                alguna_cargada = alguna_cargada or len(omitir) > 0
                self.assertEqual(serializar_estado(punto.partida, omitir),
                                 serializar_estado(originales[j], omitir),
                                 f"punto {j}")
            self.assertTrue(alguna_cargada)      # el caso de D7 sí se probó

            for pedido, texto in zip(pedidos, textos):
                self.assertEqual(jugada.consultar(pedido), texto, pedido)
        finally:
            jugada.cerrar()

    def test_fr423_fr425_cada_consulta_rehace_a_lo_sumo_k_y_mira_un_punto(self):
        for k in (3, 10):
            jugada = Jugada(k, cantidad=120)
            try:
                for pedido in self.consultas_al_azar(jugada, random.Random(k), 40):
                    jugada.consultar(pedido)
                    self.assertLessEqual(jugada.linea.ultimas_reejecutadas, k, pedido)
                    if jugada.linea.ultimas_reejecutadas > 0:
                        self.assertEqual(jugada.linea.puntos_examinados, 1, pedido)
            finally:
                jugada.cerrar()

    def test_fr408_hu1_9_misma_partida_con_y_sin_consultas(self):
        """HU1-9 y SC-403: con la misma cripta, semilla y comandos, una
        partida con 30 consultas intercaladas y otra sin ninguna terminan con
        el mismo estado, el mismo resultado y el mismo `partida.log`, byte
        por byte."""
        import os
        import tempfile

        from tests.ayudas_cripta import controlador_desde_linea

        comandos = ["mover E", "esperar", "atacar 1", "esperar", "mover O",
                    "recoger 1", "equipar", "siguiente", "recoger 1", "mover E",
                    "mover E", "atacar 1", "esperar", "mover S", "esperar"]
        consultas = ["historia 0", "historia #2", "historia 150", "historia #1",
                     "historia 77", "historia #3"]
        con_consultas = []
        for i, comando in enumerate(comandos):
            con_consultas.append(comando)
            con_consultas.append(consultas[i % len(consultas)])
            con_consultas.append(consultas[(i + 3) % len(consultas)])

        self.assertEqual(sum(1 for c in con_consultas if c.startswith("historia")), 30)

        resultados = []
        for lista in (comandos, con_consultas):
            with tempfile.TemporaryDirectory() as carpeta:
                controlador = controlador_desde_linea(carpeta, lista)
                controlador.iniciar()
                with open(os.path.join(carpeta, "partida.log"), "rb") as archivo:
                    log = archivo.read()
                resultados.append((serializar_estado(controlador.partida),
                                   controlador.partida.resultado, log))
                controlador.gestor_contenido.cerrar()

        self.assertEqual(resultados[0], resultados[1])
        self.assertNotIn(b"historia", resultados[1][2])


# ---------------------------------------------------------------------------
# Historia 2 (T024)
# ---------------------------------------------------------------------------

NO_SON_ACCION = ("avanzar", "retroceder")


def seguir_netos(partida, comandos, netos):
    """Deja pasar `comandos` y, mirando la partida entre uno y el siguiente,
    arma en `netos` la lista de comandos que quedaron (FR-410): una acción
    que se hizo se agrega; `avanzar`/`retroceder` se agregan; un pergamino
    que se usó quita la última acción y lo que vino después de ella; lo que
    el juego rechazó no se agrega. No usa la línea de tiempo."""
    anterior = None
    acciones = partida.acciones_jugador

    for comando in comandos:
        if anterior is not None:
            _anotar_neto(netos, anterior, acciones, partida.acciones_jugador)
        anterior = comando
        acciones = partida.acciones_jugador
        yield comando

    if anterior is not None:
        _anotar_neto(netos, anterior, acciones, partida.acciones_jugador)


def _anotar_neto(netos, comando, antes, despues):
    if despues == antes + 1:
        netos.append((comando, True))
    elif despues == antes - 1:
        while netos and not netos[-1][1]:
            netos.pop()
        netos.pop()
    elif comando in NO_SON_ACCION:
        netos.append((comando, False))


def normalizar(texto):
    """Quita lo que el pergamino no devuelve (HU2-3): pergaminos gastados
    (también cuentan en los espacios ocupados), los de la sala y la posición
    del objeto actual del inventario."""
    lineas = []
    for linea in texto.split("\n"):
        if linea.startswith("Inventario ("):
            linea = "Inventario (*)"
        if linea.startswith("  Pergaminos:"):
            continue
        lineas.append(linea.replace(" <- actual", ""))
    return "\n".join(lineas)


def con_pergaminos_en_mano(cantidad, semilla=SEMILLA_LINEA, inventario_max=10):
    cripta = partida_con_pergaminos(semilla, inventario_max)
    cripta.partida.jugador.inventario.fijar_pergaminos(cantidad)
    return cripta


class TestPergamino(unittest.TestCase):
    """T024: la línea de tiempo después de un pergamino (FR-410 a FR-412)."""

    def comparar_con_oraculo(self, jugada):
        for i in range(len(jugada.oraculo)):
            entrada = jugada.oraculo.obtener(i)
            with self.subTest(pedido=entrada.pedido):
                self.assertEqual(jugada.consultar(entrada.pedido), entrada.texto)

    def test_fr410_fr411_hu2_1_tres_pergaminos_seguidos(self):
        """HU2-1 (Apéndice B): 30 acciones y tres pergaminos seguidos: lo
        revertido no aparece, #28 es el estado actual y #29 se rechaza."""
        from crypta.Modelo.Resumen import armar_resumen, pedido_accion

        _, ConsultaRechazada, _ = _linea_y_consulta()
        cripta = con_pergaminos_en_mano(3)
        partida = cripta.partida
        comandos = sin_pergamino(comandos_al_azar(partida, random.Random(31), 400))
        jugada = Jugada(10, cripta=cripta,
                        comandos=_seguidos(partida, comandos, 30, ["pergamino"] * 3))
        try:
            self.assertEqual(partida.acciones_jugador, 27)
            self.assertEqual(jugada.linea.cantidad_acciones(), 27)
            self.assertEqual(jugada.consultar("acción #28"),
                             formatear(armar_resumen(partida, pedido_accion(28))))
            with self.assertRaises(ConsultaRechazada):
                jugada.ubicar("acción #29")
            self.comparar_con_oraculo(jugada)
        finally:
            jugada.cerrar()

    def test_fr403_fr410_hu2_2_instante_posterior_al_reloj_que_quedo(self):
        _, ConsultaRechazada, _ = _linea_y_consulta()
        cripta = con_pergaminos_en_mano(1)
        jugada = Jugada(10, cripta=cripta,
                        comandos=["mover E", "esperar", "esperar", "pergamino"])
        try:
            reloj = jugada.partida.reloj
            self.assertEqual(jugada.partida.acciones_jugador, 2)
            with self.assertRaises(ConsultaRechazada):
                jugada.ubicar(f"instante {reloj + 1}")
        finally:
            jugada.cerrar()

    def test_fr410_fr411_hu2_3_igual_a_la_partida_sin_lo_revertido(self):
        """HU2-3: con pergaminos y acciones nuevas después, cada `#k` es igual
        al de una partida que hizo directamente las acciones que quedaron,
        salvo pergaminos gastados, pergaminos de las salas y objeto actual; y
        sin normalizar, igual al oráculo. El inventario de las dos es grande
        para que la capacidad no las separe: los pergaminos gastados dejan
        espacio libre solo en la que los gastó."""
        for semilla in (3, 8, 13):
            with self.subTest(semilla=semilla):
                cripta = con_pergaminos_en_mano(4, semilla, inventario_max=30)
                netos = []
                comandos = seguir_netos(cripta.partida, comandos_al_azar(
                    cripta.partida, random.Random(semilla), 160), netos)
                jugada = Jugada(7, cripta=cripta, comandos=comandos)
                directa = Jugada(7, cripta=con_pergaminos_en_mano(4, semilla, 30),
                                 comandos=[c for c, _ in netos])
                try:
                    tipos = [jugada.linea.entradas.obtener(i).tipo
                             for i in range(len(jugada.linea.entradas))]
                    self.assertIn("ajuste", tipos)          # sí hubo pergaminos
                    n = jugada.partida.acciones_jugador
                    self.assertEqual(directa.partida.acciones_jugador, n)

                    for k in range(1, n + 2):
                        texto = jugada.consultar(f"acción #{k}")
                        self.assertEqual(normalizar(texto),
                                         normalizar(directa.consultar(f"acción #{k}")),
                                         f"#{k}")
                    self.comparar_con_oraculo(jugada)
                finally:
                    jugada.cerrar()
                    directa.cerrar()

    def test_fr412_hu2_4_el_recorte_no_depende_de_lo_anterior(self):
        """HU2-4: el pergamino examina las mismas entradas con 100 y con 2 000
        acciones previas."""
        examinadas = []
        for previas in (100, 2000):
            cripta = con_pergaminos_en_mano(1)
            jugador = cripta.partida.jugador
            jugador.vida_max = jugador.vida = 10 ** 9      # que no muera antes
            comandos = sin_pergamino(
                comandos_al_azar(cripta.partida, random.Random(5), 10 * previas))
            jugada = Jugada(22, cripta=cripta,
                            comandos=_seguidos(cripta.partida, comandos, previas,
                                               ["avanzar", "esperar", "avanzar",
                                                "pergamino"]))
            try:
                self.assertEqual(jugada.linea.cantidad_acciones(), previas)
                examinadas.append(jugada.linea.ultimas_examinadas)
            finally:
                jugada.cerrar()

        self.assertEqual(examinadas[0], examinadas[1])
        self.assertLessEqual(examinadas[0], 3)

    def test_fr410_pergamino_que_revierte_el_ancla_de_un_punto(self):
        """El punto de la acción revertida desaparece y se vuelve a crear al
        llegar otra vez a ese total; justo después de crearse, y consultando
        inmediatamente después del pergamino."""
        cripta = con_pergaminos_en_mano(2)
        partida = cripta.partida
        jugada = Jugada(5, cripta=cripta, comandos=["esperar"] * 10)
        try:
            linea = jugada.linea
            self.assertEqual([linea.puntos.obtener(j).ancla for j in range(len(linea.puntos))],
                             [0, 5, 10])
            _jugar_y_registrar(jugada, ["pergamino"])
            self.assertEqual([linea.puntos.obtener(j).ancla for j in range(len(linea.puntos))],
                             [0, 5])
            from crypta.Modelo.Resumen import armar_resumen, pedido_accion
            self.assertEqual(jugada.consultar("acción #10"),
                             formatear(armar_resumen(partida, pedido_accion(10))))

            _jugar_y_registrar(jugada, ["mover E"])
            self.assertEqual(linea.puntos.obtener(2).ancla, 10)
            self.assertIsNot(linea.puntos.obtener(2).partida, partida)
            self.assertEqual(jugada.consultar("acción #11"),
                             formatear(armar_resumen(partida, pedido_accion(11))))
        finally:
            jugada.cerrar()

    def test_fr410_avanzar_despues_de_la_accion_revertida(self):
        """`avanzar` después de la acción revertida: su efecto (el objeto a la
        vista) queda en el ajuste, y las consultas coinciden con el oráculo."""
        cripta = con_pergaminos_en_mano(2)
        jugada = Jugada(4, cripta=cripta, comandos=[
            "recoger 0", "recoger 0", "recoger 0", "esperar", "avanzar", "avanzar",
            "pergamino", "esperar", "retroceder", "esperar", "pergamino", "esperar"])
        try:
            self.assertIn("ajuste", [jugada.linea.entradas.obtener(i).tipo
                                     for i in range(len(jugada.linea.entradas))])
            self.comparar_con_oraculo(jugada)
        finally:
            jugada.cerrar()

    def test_fr421_consultas_con_pergaminos_contra_el_oraculo(self):
        """Partidas al azar con pergaminos y varios K: todo el oráculo, y lo
        que la línea deja en los puntos después de consultar."""
        for k in (2, 6):
            cripta = con_pergaminos_en_mano(5, 40 + k)
            jugada = Jugada(k, cripta=cripta, comandos=comandos_al_azar(
                cripta.partida, random.Random(40 + k), 150))
            try:
                self.comparar_con_oraculo(jugada)
            finally:
                jugada.cerrar()


def _seguidos(partida, primeros, acciones, despues):
    """`primeros` hasta tener `acciones` acciones, y después `despues`."""
    for comando in hasta_acciones(partida, primeros, acciones):
        yield comando
    for comando in despues:
        yield comando


def _jugar_y_registrar(jugada, comandos):
    from crypta.Controlador.Comandos import ejecutar_y_registrar
    for comando in comandos:
        ejecutar_y_registrar(jugada.partida, jugada.linea, comando, jugada.garantizar)


# ---------------------------------------------------------------------------
# Capacidad 002: el mapa conocido en la línea de tiempo (T033, T034; T057
# de la 004)
# ---------------------------------------------------------------------------

def esqueleto_puerta_que_se_cierra():
    """1 —E→ 2 con una puerta cerrada que se cierra sola 500 después de
    abrirse."""
    return [sala(1, {"E": salida(2, cerrada=True, cierre_automatico=500)}),
            sala(2, {"O": salida(1, cerrada=True, cierre_automatico=500)})]


# Se abre en el instante 300 (abierta a la vista desde el 350); se cierra
# sola en el 800 y el jugador la ve cerrada en la decisión del 850.
COMANDOS_PUERTA = (["esperar"] * 3 + ["abrir E"] + ["esperar"] * 6)
LINEA_ABIERTA = "  1 Sala 1\n    E: sala 2, costo 100, abierta\n"
LINEA_CERRADA = "  1 Sala 1\n    E: sala 2, costo 100, cerrada\n"


def jugada_de_la_puerta(k=3):
    partida = partida_sintetica(esqueleto_puerta_que_se_cierra())
    return Jugada(k, partida=partida, comandos=list(COMANDOS_PUERTA))


def encabezado_de(partida):
    from crypta.Adaptadores.RegistroPartida import Encabezado

    return Encabezado("cripta-prueba", "v-prueba", "c-prueba", partida.semilla,
                      partida.jugador.nombre)


def consultar_en(linea, partida, t):
    _, _, consultar = _linea_y_consulta()
    objetivo = linea.ubicar_instante(t, partida.reloj)
    return formatear(consultar(linea, objetivo, partida, ejecutar_comando))


class TestMapaConocidoEnHistoria(unittest.TestCase):
    """T033 (T057 de la 004; HU1-11 de la 004; FR-228 y HU4-5 de la 002):
    `historia` muestra el mapa conocido del instante consultado, no el
    actual."""

    def entrada_de_accion(self, jugada, k):
        return [jugada.oraculo.obtener(i) for i in range(len(jugada.oraculo))
                if jugada.oraculo.obtener(i).pedido == f"acción #{k}"][-1]

    def test_fr228_historia_muestra_lo_que_se_recordaba(self):
        jugada = jugada_de_la_puerta()
        self.assertEqual(jugada.partida.reloj, 950)

        self.assertIn(LINEA_ABIERTA, jugada.consultar("instante 500"))
        self.assertIn(LINEA_CERRADA, jugada.consultar("instante 900"))

        # Contra el oráculo, en los pedidos que el oráculo de la 004 registra
        # (decisiones y eventos): en la decisión #6 (instante 450) se
        # recordaba abierta; en el 800 la puerta ya se cerró sola, pero el
        # jugador todavía no la vio (la observa en la decisión del 850).
        texto = jugada.consultar("acción #6")
        self.assertEqual(texto, self.entrada_de_accion(jugada, 6).texto)
        self.assertIn(LINEA_ABIERTA, texto)

        texto = jugada.consultar("instante 800")
        self.assertEqual(texto, jugada.esperado_en_instante(800))
        self.assertIn(LINEA_ABIERTA, texto)

        texto = jugada.consultar("acción #10")
        self.assertEqual(texto, self.entrada_de_accion(jugada, 10).texto)
        self.assertIn(LINEA_CERRADA, texto)

        # El resumen del estado actual la muestra cerrada.
        from crypta.Modelo.Resumen import armar_resumen, pedido_instante
        actual = formatear(armar_resumen(jugada.partida, pedido_instante(950)))
        self.assertIn(LINEA_CERRADA, actual)

    def test_fr228_igual_tras_guardar_y_cargar(self):
        import os
        import tempfile

        from crypta.Adaptadores.GuardadoBinario import (
            ArchivoGuardado, guardar_partida)
        from crypta.Adaptadores.GuardadoJSON import (
            ArchivoGuardadoJSON, guardar_partida_json)

        jugada = jugada_de_la_puerta()
        esperado = jugada.consultar("instante 500")

        for guardar, Archivo in ((guardar_partida, ArchivoGuardado),
                                 (guardar_partida_json, ArchivoGuardadoJSON)):
            with self.subTest(archivo=Archivo.__name__), \
                    tempfile.TemporaryDirectory() as carpeta:
                ruta = os.path.join(carpeta, "partida")
                guardar(jugada.partida, ruta, encabezado_de(jugada.partida),
                        linea=jugada.linea)
                archivo = Archivo(ruta)
                cargada = archivo.cargar_partida(jugada.partida._fichas)

                self.assertEqual(consultar_en(archivo.linea, cargada, 500),
                                 esperado)


class TestConocimientoTrasCargar(unittest.TestCase):
    """T034 (FR-224, FR-228; research D3): después de cargar, consultar no
    daña el conocimiento de los puntos de control. Fallaría si el
    MapaConocido guardara `historial.registrar_cambio` en vez de
    `partida._anotar`: `leer_linea` le pone a cada punto un historial nuevo
    por asignación, y los cambios de conocimiento de la consulta irían a un
    historial que nadie deshace."""

    @staticmethod
    def foto(partida):
        salas = partida.mapa.obtener_todas()
        resultado = []

        for i in range(len(salas)):
            s = salas.obtener(i)
            resultado.append((s.id, partida.conocimiento.estado(s)))
            puertas = s.puertas()

            for j in range(len(puertas)):
                resultado.append(puertas.obtener(j).estado.recordada)

        return resultado

    def fotos_de_los_puntos(self, linea):
        return [self.foto(linea.puntos.obtener(i).partida)
                for i in range(len(linea.puntos))]

    def test_fr224_research_d3_consultar_dos_veces_tras_cargar(self):
        import os
        import tempfile

        from crypta.Adaptadores.GuardadoBinario import (
            ArchivoGuardado, guardar_partida)

        esqueleto = [sala(i, {**({"E": salida(i + 1)} if i < 8 else {}),
                              **({"O": salida(i - 1)} if i > 1 else {})})
                     for i in range(1, 9)]
        partida = partida_sintetica(esqueleto)
        jugada = Jugada(2, partida=partida,
                        comandos=["mover E"] * 7 + ["esperar"])

        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "partida.cripta")
            guardar_partida(partida, ruta, encabezado_de(partida),
                            linea=jugada.linea)
            archivo = ArchivoGuardado(ruta)
            cargada = archivo.cargar_partida(partida._fichas)

        linea = archivo.linea
        self.assertGreater(len(linea.puntos), 2)
        antes = self.fotos_de_los_puntos(linea)

        for t in (350, 550):
            with self.subTest(t=t):
                primera = consultar_en(linea, cargada, t)
                segunda = consultar_en(linea, cargada, t)

                self.assertEqual(primera, segunda)
                self.assertEqual(primera, jugada.consultar(f"instante {t}"))
                self.assertEqual(self.fotos_de_los_puntos(linea), antes)


class TestMapaConocidoEnReplayHasta(ConReplay):
    """T033: `--replay … --hasta 500` muestra lo mismo que `historia 500`
    en la partida (FR-228; HU1-11 de la 004)."""

    cripta = "c-niebla"

    def setUp(self):
        import os

        from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
        from tests.ayudas_cripta import contenidos_vacios, datos_generales

        super().setUp()
        esqueleto = esqueleto_puerta_que_se_cierra()
        self.almacen = AlmacenDisco(os.path.join(self.carpeta, "cache"))
        self.almacen.guardar_catalogo("cat-1", catalogo())
        self.almacen.guardar_cripta(
            self.cripta, "v1", esqueleto, contenidos_vacios(esqueleto),
            datos_generales=datos_generales(esqueleto, presupuesto=1000,
                                            version="v1",
                                            cripta_id=self.cripta),
            llaves={"llaves": []})

    def test_fr228_replay_hasta_500(self):
        _, textos = self.sesion_con_historia(COMANDOS_PUERTA
                                             + ["historia 500"])
        self.assertEqual(len(textos), 1)
        self.assertIn(LINEA_ABIERTA, textos[0])

        codigo, salida_main = self.hasta(500)

        self.assertEqual(codigo, 0)
        self.assertTrue(salida_main.endswith(textos[0]), salida_main)


if __name__ == "__main__":
    unittest.main()
