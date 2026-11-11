"""Pruebas de la capacidad 001, historia 2: el cazador.

Especificación: specs/001-terreno-cazador/spec.md. Cada prueba cita su FR y
su escenario (HU2-n = escenario n de la historia 2).

    python -m unittest -v tests.test_cazador
"""

import os
import tempfile
import unittest

from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.Modelo.Enemigo import Enemigo
from crypta.Controlador.GestorCripta import GestorCripta
from crypta.Modelo.Partida import Partida
from crypta.estructuras.RutaPorCazador import RutaPorCazador
from tests.ayudas_cripta import (
    SIN_DECLARAR, VERSION_CATALOGO, FuenteContadora, buscar_enemigo,
    catalogo, contenido, controlador_sintetico, datos_generales,
    ficha_cazador, ficha_errante, nuevo_jugador, partida_sintetica, sala,
    salida,
)


# (valor de rango en la ficha, cómo aparece en el mensaje)
RANGOS_INVALIDOS = (
    (SIN_DECLARAR, "(no está)"),
    (-1, "-1"),
    (600.0, "600.0"),
    (True, "true"),
    ("600", '"600"'),
    (None, "null"),
)


def mensaje_esperado(texto):
    return (f"La ficha ent_cazador (cazador) tiene un rango inválido o "
            f"ausente: {texto}")


def una_sala_con_cazador(ficha):
    """Fuente con la sala 1 (inicial) y un cazador en ella."""
    esqueleto = [sala(1, {"E": salida(2)}), sala(2, {"O": salida(1)})]
    return FuenteContadora(
        esqueleto,
        [contenido(1, enemigos=[("e-1", "ent_cazador")]), contenido(2)],
        catalogo(ficha),
        generales=datos_generales(esqueleto),
    )


class TestRangoDeLaFicha(unittest.TestCase):
    """FR-011, HU2-14 (antes de iniciar): la ficha de un cazador debe traer
    `rango` entero (no bool) y ≥ 0; si no, DatosInvalidos y la partida no
    se inicia."""

    def test_fr011_la_ficha_invalida_se_rechaza_al_llegar_por_red(self):
        """FR-011: la ficha se valida al entrar al RepositorioFichas."""
        for rango, texto in RANGOS_INVALIDOS:
            with self.subTest(rango=rango):
                fuente = FuenteContadora([], fichas=catalogo(
                    ficha_cazador(rango=rango)))
                repositorio = RepositorioFichas(fuente)

                with self.assertRaises(DatosInvalidos) as contexto:
                    repositorio.obtener_ficha("ent_cazador")

                self.assertEqual(str(contexto.exception),
                                 mensaje_esperado(texto))
                self.assertFalse(repositorio.contiene("ent_cazador"))

    def test_fr011_tambien_al_resolver_el_contenido(self):
        """FR-011: igual cuando la ficha llega en el lote del contenido."""
        fuente = FuenteContadora([], fichas=catalogo(
            ficha_cazador(rango=-1)))
        repositorio = RepositorioFichas(fuente)

        with self.assertRaises(DatosInvalidos):
            repositorio.resolver_contenidos(
                [contenido(1, enemigos=[("e-1", "ent_cazador")])])

    def test_fr011_la_ficha_invalida_no_se_guarda_en_disco(self):
        """FR-011, FR-025: una ficha inválida no queda en la copia local."""
        with tempfile.TemporaryDirectory() as carpeta:
            almacen = AlmacenDisco(carpeta)
            fuente = FuenteContadora([], fichas=catalogo(
                ficha_cazador(rango="600")))
            repositorio = RepositorioFichas(fuente, almacen, VERSION_CATALOGO)

            with self.assertRaises(DatosInvalidos):
                repositorio.obtener_ficha("ent_cazador")

            self.assertIsNone(
                almacen.cargar_ficha(VERSION_CATALOGO, "ent_cazador"))

    def test_fr011_la_ficha_invalida_se_rechaza_al_leerla_de_disco(self):
        """FR-011: la copia local también se valida al leerla."""
        with tempfile.TemporaryDirectory() as carpeta:
            almacen = AlmacenDisco(carpeta)
            almacen.guardar_catalogo(
                VERSION_CATALOGO, catalogo(ficha_cazador(rango=True)))
            repositorio = RepositorioFichas(FuenteContadora([]), almacen,
                                            VERSION_CATALOGO)

            with self.assertRaises(DatosInvalidos) as contexto:
                repositorio.obtener_ficha("ent_cazador")

            self.assertEqual(str(contexto.exception),
                             mensaje_esperado("true"))

    def test_fr011_rangos_validos(self):
        """FR-011, FR-024: rango 0 (incluido) y cualquier entero ≥ 0; el
        enemigo toma el rango de la ficha al activarse."""
        for rango in (0, 1, 600, 10 ** 6):
            with self.subTest(rango=rango):
                ficha = ficha_cazador(rango=rango)
                fuente = FuenteContadora([], fichas=catalogo(ficha))

                self.assertIs(
                    RepositorioFichas(fuente).obtener_ficha("ent_cazador"),
                    ficha)

                enemigo = Enemigo("e-1", "ent_cazador")
                enemigo.activar(ficha)
                self.assertEqual(enemigo.comportamiento, "cazador")
                self.assertEqual(enemigo.rango, rango)

    def test_fr011_los_que_no_son_cazadores_no_necesitan_rango(self):
        """FR-011: errantes, rastreadores y guardianes siguen como en P1;
        su rango es None."""
        ficha = ficha_errante()
        fuente = FuenteContadora([], fichas=catalogo(ficha))
        self.assertIs(RepositorioFichas(fuente).obtener_ficha("ent_errante"),
                      ficha)

        enemigo = Enemigo("e-1", "ent_errante")
        enemigo.activar(ficha)
        self.assertIsNone(enemigo.rango)

    def test_fr011_activar_valida_otra_vez(self):
        """FR-011: Enemigo.activar valida el rango por defensa y, si es
        inválido, el enemigo no se activa."""
        for rango, texto in RANGOS_INVALIDOS:
            with self.subTest(rango=rango):
                enemigo = Enemigo("e-1", "ent_cazador")

                with self.assertRaises(DatosInvalidos) as contexto:
                    enemigo.activar(ficha_cazador(rango=rango))

                self.assertEqual(str(contexto.exception),
                                 mensaje_esperado(texto))
                self.assertFalse(enemigo.esta_activo())
                self.assertIsNone(enemigo.rango)

    def test_fr011_desactivar_borra_el_rango(self):
        """FR-011: el rango no es estado del juego; sale de la ficha."""
        enemigo = Enemigo("e-1", "ent_cazador")
        enemigo.activar(ficha_cazador(rango=600))
        enemigo.desactivar()
        self.assertIsNone(enemigo.rango)

    def test_hu2_14_no_se_inicia_la_partida(self):
        """FR-011, HU2-14: con el cazador inválido en la sala inicial, la
        sesión muestra el mensaje y la partida no se inicia."""
        with tempfile.TemporaryDirectory() as carpeta:
            controlador = controlador_sintetico(
                una_sala_con_cazador(ficha_cazador(rango=-1)), carpeta,
                ["esperar"])

            controlador.iniciar()

            self.assertFalse(controlador.partida.iniciada)
            self.assertIsInstance(controlador.error_datos, DatosInvalidos)
            controlador.vista.mostrar_error.assert_called_once_with(
                "La cripta no se puede jugar: " + mensaje_esperado("-1"))
            controlador.vista.leer_comando.assert_not_called()
            controlador.gestor_contenido.cerrar()

            with open(os.path.join(carpeta, "partida.log"),
                      encoding="utf-8") as archivo:
                self.assertTrue(archivo.read().endswith("---\n"))


class Turno:
    """Lo que pasó en un turno del cazador."""

    def __init__(self, partida, cazador, sala_antes, vida_antes):
        self.partida = partida
        self.cazador = cazador
        self.sala_antes = sala_antes
        self.sala = cazador.sala_actual
        self.se_movio = self.sala != sala_antes
        self.danio = vida_antes - partida.jugador.vida
        self.ataco = self.danio > 0
        # Cuánto después queda su siguiente acción.
        self.intervalo = cazador.evento_siguiente.tiempo - partida.reloj

    @property
    def espero(self):
        return not self.se_movio and not self.ataco


def turno_del_cazador(esqueleto, sala_cazador, sala_jugador, rango=1000,
                      velocidad=100, partida=None):
    """Arma una partida con el jugador en `sala_jugador` y un cazador activo
    en `sala_cazador` y juega UN turno del cazador, en el instante 0. Con
    `partida`, usa esa (el cazador se llama c-1)."""
    ficha = ficha_cazador(rango=rango, velocidad=velocidad, ataque=8)

    if partida is None:
        partida = partida_sintetica(
            esqueleto,
            [contenido(sala_cazador, enemigos=[("c-1", "ent_cazador")])],
            catalogo(ficha),
            sala_inicial=sala_jugador,
        )

    cazador = buscar_enemigo(partida, "c-1")

    if not cazador.esta_activo():
        cazador.activar(ficha)

    sala_antes = cazador.sala_actual
    vida_antes = partida.jugador.vida

    partida._turno_enemigo(cazador)

    return Turno(partida, cazador, sala_antes, vida_antes)


def ruta_5_a(costo_directo=500):
    """HU2-5: 1–2 cuesta `costo_directo`; 1–3–4–2, 100 cada salida."""
    return [
        sala(1, {"E": salida(2, costo=costo_directo),
                 "S": salida(3, costo=100)}),
        sala(2, {"O": salida(1), "S": salida(4, costo=100)}),
        sala(3, {"N": salida(1), "E": salida(4, costo=100)}),
        sala(4, {"O": salida(3), "N": salida(2)}),
    ]


def dos_salas(costo, cerrada=False):
    return [sala(1, {"E": salida(2, costo=costo, cerrada=cerrada)}),
            sala(2, {"O": salida(1)})]


class TestDecisionDelCazador(unittest.TestCase):
    """Historia 2: ataca si comparte sala; espera sin ruta o con d > rango;
    si no, un paso hacia la vecina de menor id que inicia una ruta de
    costo mínimo."""

    def test_hu2_1_en_la_sala_del_jugador_ataca(self):
        """FR-013, HU2-1: ataca con costo 100 y no se mueve."""
        partida = partida_sintetica(
            dos_salas(100),
            [contenido(1, enemigos=[("c-1", "ent_cazador")])],
            catalogo(ficha_cazador(ataque=8)),
        )
        cazador = buscar_enemigo(partida, "c-1")

        partida.esperar()               # el cazador actúa en 100

        self.assertLess(partida.jugador.vida, partida.jugador.vida_max)
        self.assertEqual(cazador.sala_actual, 1)
        self.assertEqual(cazador.evento_siguiente.tiempo, 200)
        self.assertIn("te ataca", " ".join(partida.bitacora))

    def test_hu2_2_sin_ruta_espera(self):
        """FR-014, FR-015, HU2-2: la única salida está cerrada → espera con
        costo 100."""
        turno = turno_del_cazador(dos_salas(100, cerrada=True), 1, 2)

        self.assertTrue(turno.espero)
        self.assertEqual(turno.intervalo, 100)

    def test_hu2_2_salida_sin_vuelta_hacia_el_cazador(self):
        """FR-014, HU2-2: hay salida del jugador hacia el cazador pero no
        del cazador hacia el jugador → no hay ruta y espera."""
        esqueleto = [sala(1), sala(2, {"O": salida(1)})]
        turno = turno_del_cazador(esqueleto, 1, 2)

        self.assertTrue(turno.espero)
        self.assertEqual(turno.intervalo, 100)

    def test_hu2_3_ruta_mas_cara_que_el_rango(self):
        """FR-015, HU2-3: rango 600, ruta de 700 → espera con costo 100."""
        turno = turno_del_cazador(dos_salas(700), 1, 2, rango=600)

        self.assertTrue(turno.espero)
        self.assertEqual(turno.intervalo, 100)

    def test_hu2_4_ruta_igual_al_rango(self):
        """FR-015, FR-016, HU2-4: rango 600, ruta de exactamente 600 →
        avanza (solo espera si d > rango)."""
        turno = turno_del_cazador(dos_salas(600), 1, 2, rango=600)

        self.assertEqual(turno.sala, 2)
        self.assertEqual(turno.intervalo, 600)

    def test_hu2_5_la_ruta_mas_barata_aunque_tenga_mas_salas(self):
        """FR-014, FR-016, HU2-5: 1–2 cuesta 500 y 1–3–4–2 cuesta 300 → va
        a la 3 y la acción cuesta 100."""
        turno = turno_del_cazador(ruta_5_a(), 1, 2)

        self.assertEqual(turno.sala, 3)
        self.assertEqual(turno.intervalo, 100)

    def test_hu2_6_empate_va_a_la_vecina_de_menor_id(self):
        """FR-017, HU2-6: vecinas 5 y 3 inician rutas mínimas → va a la 3,
        aunque la salida hacia la 5 venga primero en el orden N, S, E, O."""
        esqueleto = [
            sala(1, {"N": salida(5, costo=100), "E": salida(3, costo=100)}),
            sala(5, {"S": salida(1), "E": salida(2, costo=100)}),
            sala(3, {"O": salida(1), "N": salida(2, costo=100)}),
            sala(2, {"O": salida(5), "S": salida(3)}),
        ]
        turno = turno_del_cazador(esqueleto, 1, 2)

        self.assertEqual(turno.sala, 3)
        self.assertEqual(turno.intervalo, 100)

    def test_hu2_7_cuadricula_con_rutas_que_se_cruzan(self):
        """FR-017, HU2-7: en una cuadrícula 4x4 con todas las salidas de
        costo 100 hay muchas rutas mínimas; desde cada sala, el primer paso
        es el mismo que da RutaPorCazador (vecina de menor id). Los id no
        siguen el orden de la cuadrícula."""
        lado = 4
        ids = [23, 7, 41, 15, 2, 36, 18, 50, 9, 31, 12, 44, 27, 5, 38, 20]

        def id_de(fila, columna):
            return ids[fila * lado + columna]

        esqueleto = []
        for fila in range(lado):
            for columna in range(lado):
                salidas = {}
                if fila > 0:
                    salidas["N"] = salida(id_de(fila - 1, columna), costo=100)
                if fila < lado - 1:
                    salidas["S"] = salida(id_de(fila + 1, columna), costo=100)
                if columna < lado - 1:
                    salidas["E"] = salida(id_de(fila, columna + 1), costo=100)
                if columna > 0:
                    salidas["O"] = salida(id_de(fila, columna - 1), costo=100)
                esqueleto.append(sala(id_de(fila, columna), salidas))

        jugador = id_de(3, 3)
        eligio_el_este = 0

        for posicion in range(lado * lado):
            fila, columna = divmod(posicion, lado)
            id_cazador = id_de(fila, columna)

            if id_cazador == jugador:
                continue

            with self.subTest(cazador=id_cazador):
                turno = turno_del_cazador(esqueleto, id_cazador, jugador)
                mapa = turno.partida.mapa

                def salidas_de(indice):
                    origen = mapa.sala_por_indice(indice)
                    puertas = origen.puertas(solo_abiertas=True)
                    for i in range(len(puertas)):
                        puerta = puertas.obtener(i)
                        yield puerta.sala_destino_ref.indice, puerta.costo

                ruta = RutaPorCazador(mapa.cantidad_salas(), salidas_de)
                _, paso = ruta.buscar(mapa.obtener_sala(id_cazador).indice,
                                      mapa.obtener_sala(jugador).indice, 1000)

                self.assertEqual(turno.sala, mapa.sala_por_indice(paso).id)

                # Con dos vecinas posibles (sur y este), la del sur viene
                # antes en el orden N, S, E, O; si eligió el este, decidió
                # el id.
                if (fila < lado - 1 and columna < lado - 1
                        and turno.sala == id_de(fila, columna + 1)):
                    eligio_el_este += 1

        self.assertGreater(eligio_el_este, 0)

    def test_hu2_8_no_usa_ni_abre_la_puerta_cerrada(self):
        """FR-014, FR-018, HU2-8: 1–2 de costo 100 cerrada y 1–3–2 de 400
        abierta → va a la 3 y la puerta sigue cerrada."""
        esqueleto = [
            sala(1, {"E": salida(2, costo=100, cerrada=True),
                     "S": salida(3, costo=200)}),
            sala(2, {"O": salida(1), "S": salida(3)}),
            sala(3, {"N": salida(1), "E": salida(2, costo=200)}),
        ]
        turno = turno_del_cazador(esqueleto, 1, 2)

        self.assertEqual(turno.sala, 3)
        self.assertEqual(turno.intervalo, 200)
        self.assertTrue(
            turno.partida.mapa.obtener_sala(1).obtener_puerta("E")
            .esta_cerrada())

    def test_hu2_8_una_puerta_que_cambia_cambia_la_decision(self):
        """FR-018, FR-019: si se cierra o se abre una puerta de la ruta, el
        siguiente turno lo tiene en cuenta (la búsqueda vieja no sirve)."""
        partida = partida_sintetica(
            ruta_5_a(costo_directo=100),
            [contenido(1, enemigos=[("c-1", "ent_cazador")])],
            catalogo(ficha_cazador()), sala_inicial=2)
        directa = partida.mapa.obtener_sala(1).obtener_puerta("E")

        turno = turno_del_cazador(None, 1, 2, partida=partida)
        self.assertEqual(turno.sala, 2)        # 1–2 abierta, costo 100

        def volver_a_la_1():
            cazador = turno.cazador
            partida.mapa.obtener_sala(cazador.sala_actual).quitar_enemigo(
                cazador)
            partida.mapa.obtener_sala(1).agregar_enemigo(cazador)

        volver_a_la_1()
        directa.cerrar()
        turno = turno_del_cazador(None, 1, 2, partida=partida)
        self.assertEqual(turno.sala, 3)

        volver_a_la_1()
        directa.abrir()
        turno = turno_del_cazador(None, 1, 2, partida=partida)
        self.assertEqual(turno.sala, 2)

    def test_hu2_9_salas_sin_contenido_descargado(self):
        """FR-018, FR-027, HU2-9: la ruta pasa por las salas 3 y 4, cuyo
        contenido no se descargó → misma decisión y ninguna solicitud."""
        fuente = FuenteContadora(ruta_5_a())
        _, mapa, _ = GestorCripta(fuente, _SinCopia()).cargar(
            fuente.generales["id"])
        solicitudes = fuente.solicitudes

        mapa.asignar_contenidos([
            contenido(1, enemigos=[("c-1", "ent_cazador")]), contenido(2)])
        partida = Partida(mapa, nuevo_jugador(), 2,
                          catalogo(ficha_cazador()).get, semilla=7)
        partida.iniciar()

        turno = turno_del_cazador(None, 1, 2, partida=partida)
        con_todo = turno_del_cazador(ruta_5_a(), 1, 2)

        self.assertEqual(turno.sala, con_todo.sala)
        self.assertEqual(turno.intervalo, con_todo.intervalo)
        self.assertEqual(fuente.solicitudes, solicitudes)
        self.assertFalse(mapa.obtener_sala(3).contenido_cargado())
        self.assertFalse(mapa.obtener_sala(4).contenido_cargado())

    def test_hu2_10_se_activa_como_cualquier_enemigo(self):
        """FR-012, HU2-10: dormido en una sala no visitada; al entrar el
        jugador se activa con primera acción en reloj + 100, y varios en
        orden de id de instancia."""
        partida = partida_sintetica(
            [sala(1, {"E": salida(2, costo=50)}), sala(2, {"O": salida(1)})],
            [contenido(2, enemigos=[("c-2", "ent_cazador"),
                                    ("c-1", "ent_cazador")])],
            catalogo(ficha_cazador()),
        )
        c1 = buscar_enemigo(partida, "c-1")
        c2 = buscar_enemigo(partida, "c-2")
        self.assertFalse(c1.esta_activo())

        partida.mover("E")              # llega en 0; el jugador sigue en 50

        self.assertTrue(c1.esta_activo() and c2.esta_activo())
        self.assertEqual(c1.evento_siguiente.tiempo, 100)
        self.assertEqual(c2.evento_siguiente.tiempo, 100)
        self.assertLess(c1.evento_siguiente.secuencia,
                        c2.evento_siguiente.secuencia)

    def test_hu2_11_el_movimiento_tarda_segun_su_velocidad(self):
        """FR-003, FR-016, HU2-11: velocidad 120 y salida de costo 250 →
        max(1, 250 * 100 // 120) = 208."""
        turno = turno_del_cazador(dos_salas(250), 1, 2, velocidad=120)

        self.assertEqual(turno.sala, 2)
        self.assertEqual(turno.intervalo, 208)

    def test_hu2_13_el_rango_sale_de_la_ficha(self):
        """FR-011, HU2-13: el jugador a costo 700; con rango 600 espera y
        con rango 800 avanza."""
        con_600 = turno_del_cazador(dos_salas(700), 1, 2, rango=600)
        con_800 = turno_del_cazador(dos_salas(700), 1, 2, rango=800)

        self.assertTrue(con_600.espero)
        self.assertEqual(con_600.intervalo, 100)
        self.assertEqual(con_800.sala, 2)
        self.assertEqual(con_800.intervalo, 700)

    def test_hu2_13_cada_cazador_con_su_rango_en_la_busqueda_compartida(self):
        """FR-011, FR-015: un cazador de rango 1000 extiende la búsqueda
        compartida hasta 900; otro de rango 600, a 700 del jugador, igual
        espera aunque su sala ya quedó asentada."""
        esqueleto = [
            sala(1, {"E": salida(2, costo=700)}),
            sala(2, {"O": salida(1), "E": salida(3, costo=200)}),
            sala(3, {"O": salida(2)}),
        ]
        largo = ficha_cazador("ent_largo", rango=1000)
        corto = ficha_cazador("ent_corto", rango=600)
        partida = partida_sintetica(
            esqueleto,
            [contenido(3, enemigos=[("c-1", "ent_largo")]),
             contenido(2, enemigos=[("c-2", "ent_corto")])],
            catalogo(largo, corto),
        )
        lejano = buscar_enemigo(partida, "c-1")
        cercano = buscar_enemigo(partida, "c-2")
        lejano.activar(largo)
        cercano.activar(corto)

        partida._turno_enemigo(lejano)       # asienta 1, 2 y 3
        partida._turno_enemigo(cercano)

        self.assertEqual(lejano.sala_actual, 2)
        self.assertEqual(cercano.sala_actual, 2)       # no se movió
        self.assertEqual(cercano.evento_siguiente.tiempo, 100)

    def test_hu2_15_rango_0(self):
        """FR-011, FR-013, FR-015, HU2-15: rango 0 sin compartir sala →
        espera con costo 100; compartiendo sala → ataca."""
        lejos = turno_del_cazador(dos_salas(1), 1, 2, rango=0)
        self.assertTrue(lejos.espero)
        self.assertEqual(lejos.intervalo, 100)

        cerca = turno_del_cazador(dos_salas(1), 1, 1, rango=0)
        self.assertTrue(cerca.ataco)
        self.assertEqual(cerca.sala, 1)
        self.assertEqual(cerca.intervalo, 100)

    def test_fr021_no_usa_el_azar_para_decidir(self):
        """FR-021: moverse y esperar no tocan el generador aleatorio (el
        daño del ataque sí, como en P1)."""
        for esqueleto, rango in ((ruta_5_a(), 1000), (dos_salas(700), 600)):
            with self.subTest(rango=rango):
                partida = partida_sintetica(
                    esqueleto,
                    [contenido(1, enemigos=[("c-1", "ent_cazador")])],
                    catalogo(ficha_cazador(rango=rango)), sala_inicial=2)
                antes = partida.azar.getstate()

                turno_del_cazador(None, 1, 2, rango=rango, partida=partida)

                self.assertEqual(partida.azar.getstate(), antes)


class _SinCopia:
    """Almacén vacío: obliga a descargar el esqueleto."""

    def cargar_cripta(self, cripta_id, version):
        return None

if __name__ == "__main__":
    unittest.main()
