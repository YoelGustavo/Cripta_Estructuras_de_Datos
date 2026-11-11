"""Pruebas de la capacidad 001, historia 3: la decisión del cazador siempre
es la de un cálculo desde cero (FR-019, SC-002).

Especificación: specs/001-terreno-cazador/spec.md (HU3-n = escenario n de la
historia 3). Todas usan el `Verificador` (tarea T056): en CADA turno de cada
cazador compara la decisión de la partida (que reutiliza la búsqueda) con
`decidir_desde_cero` y con `RutaPorCazador`, y falla en el momento con el
instante, el cazador y las decisiones si alguna difiere.

    python -m unittest -v tests.test_equivalencia_cazador
"""

import os
import random
import tempfile
import unittest
from unittest.mock import patch

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Controlador.PreparadorReplay import PreparadorReplay
from crypta.Controlador.Reproductor import Reproductor
from crypta.Modelo.Partida import CIERRE_PUERTA, TURNO_ENEMIGO
from crypta.Modelo.Perseguidor import (
    ATACAR, ESPERAR, MOVER, RECALCULAR, SELECTIVA, TOTAL, Perseguidor,
)
from crypta.estructuras.RutaPorCazador import RutaPorCazador
from tests.ayudas_cripta import (
    FuenteContadora, buscar_enemigo, catalogo, contenido,
    controlador_sintetico, datos_generales, ficha_cazador, ficha_errante,
    ficha_rastreador, nuevo_jugador, partida_sintetica, sala, salida,
)


def resumen(decision):
    """(acción, id de la sala destino, costo) de una Decision."""
    destino = (None if decision.puerta is None
               else decision.puerta.sala_destino_ref.id)
    return decision.accion, destino, decision.costo


class Verificador:
    """T056 (FR-019, SC-002): envuelve el Perseguidor de la partida. En cada
    turno de cazador compara su Decision con `decidir_desde_cero` (otra
    búsqueda, siempre reiniciada) y con `RutaPorCazador`; también comprueba
    que decidir no toque el azar (FR-021). Si algo difiere, lanza
    AssertionError con el instante, el cazador y las decisiones."""

    def __init__(self, partida, perseguidor=None):
        self.partida = partida

        if perseguidor is not None:
            partida._perseguidor = perseguidor
            perseguidor.observar_puertas()

        self.perseguidor = partida.perseguidor()
        self._decidir = self.perseguidor.decidir
        self.perseguidor.decidir = self.decidir

        self.revisadas = 0
        self.por_accion = {ATACAR: 0, ESPERAR: 0, MOVER: 0}
        self.orden = []          # (instante, cazador) de cada turno

    def decidir(self, cazador, sala_jugador):
        partida = self.partida
        azar = partida.azar.getstate()

        decision = self._decidir(cazador, sala_jugador)
        desde_cero = self.perseguidor.decidir_desde_cero(cazador,
                                                         sala_jugador)
        con_ruta = self._con_ruta(cazador, sala_jugador)

        if (resumen(decision) != resumen(desde_cero)
                or resumen(decision)[:2] != con_ruta
                or partida.azar.getstate() != azar):
            raise AssertionError(
                f"Instante {partida.reloj}, cazador {cazador.id_instancia} "
                f"en la sala {cazador.sala_actual}, jugador en la sala "
                f"{sala_jugador.id}: la partida decidió {resumen(decision)}, "
                f"desde cero {resumen(desde_cero)} y RutaPorCazador "
                f"{con_ruta}" + ("" if partida.azar.getstate() == azar
                                 else "; además cambió el azar"))

        self.revisadas += 1
        self.por_accion[decision.accion] += 1
        self.orden.append((partida.reloj, cazador.id_instancia))
        return decision

    def _con_ruta(self, cazador, sala_jugador):
        """(acción, id de la sala destino) según RutaPorCazador."""
        mapa = self.partida.mapa
        u = mapa.obtener_sala(cazador.sala_actual)

        if u is sala_jugador:
            return ATACAR, None

        def salidas_de(indice):
            puertas = mapa.sala_por_indice(indice).puertas(solo_abiertas=True)

            for i in range(len(puertas)):
                puerta = puertas.obtener(i)

                if puerta.sala_destino_ref is not None:
                    yield puerta.sala_destino_ref.indice, puerta.costo

        resultado = RutaPorCazador(mapa.cantidad_salas(), salidas_de).buscar(
            u.indice, sala_jugador.indice, cazador.rango)

        if resultado is None:
            return ESPERAR, None

        return MOVER, mapa.sala_por_indice(resultado[1]).id


def activar(partida, instancia, ficha, en=None):
    """Activa a un enemigo dormido y le programa su primer turno en
    reloj + intervalo(100), como P1 §2.4 (o en el instante `en`)."""
    enemigo = buscar_enemigo(partida, instancia)
    enemigo.activar(ficha)
    tiempo = partida.reloj + enemigo.intervalo(100) if en is None else en
    partida._programar(enemigo, tiempo, TURNO_ENEMIGO)
    return enemigo


def esperar_hasta(partida, instante):
    while partida.reloj < instante and not partida.terminada:
        partida.esperar()


def anillo():
    """1 —E→ 2 —E→ 3 —S→ 6 —O→ 5 —N→ 1, todas de costo 100 y con vuelta."""
    return [
        sala(1, {"E": salida(2, costo=100), "S": salida(5, costo=100)}),
        sala(2, {"O": salida(1), "E": salida(3, costo=100)}),
        sala(3, {"O": salida(2), "S": salida(6, costo=100)}),
        sala(6, {"N": salida(3), "O": salida(5, costo=100)}),
        sala(5, {"E": salida(6), "N": salida(1)}),
    ]


class TestEquivalenciaEscenarios(unittest.TestCase):
    """HU3-1 a HU3-6, cada uno con el verificador en cada turno."""

    def partida_con_cazador(self, esqueleto, sala_cazador, sala_jugador,
                            rango=1000, pergaminos=0):
        ficha = ficha_cazador(rango=rango, ataque=2)
        partida = partida_sintetica(
            esqueleto,
            [contenido(sala_cazador, enemigos=[("c-1", "ent_cazador")])],
            catalogo(ficha), sala_inicial=sala_jugador,
            jugador=nuevo_jugador(pergaminos=pergaminos),
        )
        verificador = Verificador(partida)
        cazador = activar(partida, "c-1", ficha)
        return partida, verificador, cazador

    def cripta_hu3_1(self, cierre_automatico=None, con_alternativa=True):
        """4 —100→ 1 —100 (puerta)→ 2 y, si hay alternativa,
        1 —200→ 3 —200→ 2. La puerta 1–2 empieza cerrada."""
        salidas_1 = {"O": salida(4),
                     "E": salida(2, costo=100, cerrada=True,
                                 cierre_automatico=cierre_automatico)}
        salidas_2 = {"O": salida(1)}
        esqueleto = [sala(4, {"E": salida(1, costo=100)})]

        if con_alternativa:
            salidas_1["S"] = salida(3, costo=200)
            salidas_2["S"] = salida(3)
            esqueleto.append(sala(3, {"N": salida(1),
                                      "E": salida(2, costo=200)}))

        return esqueleto + [sala(1, salidas_1), sala(2, salidas_2)]

    def test_hu3_1_la_puerta_se_cierra_sola_entre_dos_turnos(self):
        """FR-019, HU3-1: el cazador va hacia la puerta 1–2; se cierra por
        cierre automático antes de su siguiente turno → toma 1–3–2."""
        partida, verificador, cazador = self.partida_con_cazador(
            self.cripta_hu3_1(cierre_automatico=150), 4, 2)

        partida.abrir("O")          # 0: abre; se cierra sola en 150
        esperar_hasta(partida, 150)  # 100: el cazador va de 4 a 1
        self.assertEqual(cazador.sala_actual, 1)

        esperar_hasta(partida, 250)  # 150: se cierra; 200: decide
        self.assertTrue(partida.mapa.obtener_sala(1).obtener_puerta("E")
                        .esta_cerrada())
        self.assertEqual(cazador.sala_actual, 3)
        self.assertEqual(verificador.revisadas, 2)

    def test_hu3_1_la_puerta_se_cierra_por_otro_evento(self):
        """FR-019, HU3-1: igual, cerrándola cualquier otro evento."""
        partida, verificador, cazador = self.partida_con_cazador(
            self.cripta_hu3_1(), 4, 2)

        partida.abrir("O")
        esperar_hasta(partida, 150)
        self.assertEqual(cazador.sala_actual, 1)

        partida.mapa.obtener_sala(2).obtener_puerta("O").cerrar()
        esperar_hasta(partida, 250)
        self.assertEqual(cazador.sala_actual, 3)
        self.assertEqual(verificador.revisadas, 2)

    def test_hu3_1_sin_otra_ruta_espera(self):
        """FR-019, HU3-1: si al cerrarse ya no hay ruta, espera."""
        partida, verificador, cazador = self.partida_con_cazador(
            self.cripta_hu3_1(cierre_automatico=150, con_alternativa=False),
            4, 2)

        partida.abrir("O")
        esperar_hasta(partida, 250)

        self.assertEqual(cazador.sala_actual, 1)
        self.assertEqual(cazador.evento_siguiente.tiempo, 300)
        self.assertEqual(verificador.por_accion[ESPERAR], 1)

    def test_hu3_2_se_abre_una_puerta_y_crea_una_ruta(self):
        """FR-019, HU3-2: esperaba sin ruta; se abre la puerta → avanza."""
        partida, verificador, cazador = self.partida_con_cazador(
            [sala(1, {"E": salida(2, costo=300, cerrada=True)}),
             sala(2, {"O": salida(1)})], 1, 2)

        partida.esperar()            # 100: espera (no hay ruta)
        self.assertEqual(cazador.sala_actual, 1)

        partida.abrir("O")           # 100
        esperar_hasta(partida, 250)  # 200: avanza

        self.assertEqual(cazador.sala_actual, 2)
        self.assertEqual(verificador.por_accion[ESPERAR], 1)
        self.assertEqual(verificador.por_accion[MOVER], 1)

    def test_hu3_3_el_jugador_se_mueve_entre_dos_turnos(self):
        """FR-014, FR-019, HU3-3: con el jugador en 3 va a la 2; el jugador
        pasa a la 6 y el cazador decide hacia la 6."""
        partida, verificador, cazador = self.partida_con_cazador(
            anillo(), 1, 3)

        partida.esperar()            # 100: de 1 a 2 (hacia la 3)
        self.assertEqual(cazador.sala_actual, 2)

        partida.mover("S")           # 100: el jugador a la 6; en 200 el
                                     # cazador va de 2 a 3 (2–3–6 = 200)

        self.assertEqual(cazador.sala_actual, 3)
        self.assertEqual(verificador.revisadas, 2)

    def test_hu3_4_varios_cazadores_en_el_mismo_instante(self):
        """FR-019, FR-023, HU3-4: c-1, un cierre de puerta y c-2 en el
        instante 100, en ese orden de secuencia. c-1 cruza la puerta 1–2;
        c-2 decide después del cierre y toma 1–4–3."""
        esqueleto = [
            sala(1, {"E": salida(2, costo=100), "S": salida(4, costo=100)}),
            sala(2, {"O": salida(1), "E": salida(3, costo=100)}),
            sala(4, {"N": salida(1), "E": salida(3, costo=200)}),
            sala(3, {"O": salida(2), "S": salida(4)}),
        ]
        ficha = ficha_cazador(ataque=2)
        partida = partida_sintetica(
            esqueleto,
            [contenido(1, enemigos=[("c-1", "ent_cazador"),
                                    ("c-2", "ent_cazador")])],
            catalogo(ficha), sala_inicial=3)
        verificador = Verificador(partida)

        c1 = activar(partida, "c-1", ficha, en=100)
        partida._programar_evento(
            100, CIERRE_PUERTA,
            partida.mapa.obtener_sala(1).obtener_puerta("E"))
        c2 = activar(partida, "c-2", ficha, en=100)

        partida.esperar()

        self.assertEqual(verificador.orden, [(100, "c-1"), (100, "c-2")])
        self.assertEqual(c1.sala_actual, 2)
        self.assertEqual(c2.sala_actual, 4)

    def test_hu3_6_pergamino_despues_de_que_el_cazador_se_movio(self):
        """FR-019, FR-020, HU3-6: el pergamino lo devuelve a su sala, vida
        y próxima acción; después sus decisiones siguen coincidiendo."""
        partida, verificador, cazador = self.partida_con_cazador(
            anillo(), 1, 3, pergaminos=1)
        antes = (cazador.sala_actual, cazador.vida,
                 cazador.evento_siguiente.tiempo)

        partida.esperar()                    # 100: el cazador va a la 2
        self.assertEqual(cazador.sala_actual, 2)

        self.assertTrue(partida.usar_pergamino())

        self.assertEqual((cazador.sala_actual, cazador.vida,
                          cazador.evento_siguiente.tiempo), antes)
        self.assertFalse(verificador.perseguidor._vigente)   # T066

        partida.mover("S")                   # ahora el jugador va a la 6
        esperar_hasta(partida, 600)
        self.assertGreaterEqual(verificador.revisadas, 5)


def cuadricula_al_azar(azar, lado=6):
    """Cuadrícula lado x lado con costos variados, algunas puertas
    cerradas y algunas con cierre automático. Id 1..lado²."""
    esqueleto = []

    def id_de(fila, columna):
        return fila * lado + columna + 1

    for fila in range(lado):
        for columna in range(lado):
            salidas = {}

            # Cada salida se declara del lado de la sala de menor id.
            for direccion, (df, dc) in (("S", (1, 0)), ("E", (0, 1))):
                f, c = fila + df, columna + dc

                if f < lado and c < lado:
                    salidas[direccion] = salida(
                        id_de(f, c), costo=azar.choice((50, 100, 150, 250)),
                        cerrada=azar.random() < 0.2,
                        cierre_automatico=(azar.choice((60, 200, 450))
                                           if azar.random() < 0.2 else None))

            for direccion, (df, dc) in (("N", (-1, 0)), ("O", (0, -1))):
                f, c = fila + df, columna + dc

                if f >= 0 and c >= 0:
                    salidas[direccion] = salida(id_de(f, c))

            esqueleto.append(sala(id_de(fila, columna), salidas))

    return esqueleto


class TestPartidaLarga(unittest.TestCase):
    """HU3-5 y SC-002 (FR-019): partida sintética determinista con muchos
    cambios de puertas, movimientos, muertes y cambios de velocidad; en
    cada turno de cada cazador, 100 % de coincidencia con el verificador."""

    def _jugar(self, semilla, turnos_de_cazador, modo):
        azar = random.Random(semilla)
        lado = 6
        esqueleto = cuadricula_al_azar(azar, lado)

        cazadores = [
            ficha_cazador("ent_caz_300", rango=300, velocidad=80,
                          vida_max=10 ** 6, ataque=1),
            ficha_cazador("ent_caz_600", rango=600, velocidad=100,
                          vida_max=10 ** 6, ataque=1),
            ficha_cazador("ent_caz_1000", rango=1000, velocidad=120,
                          vida_max=10 ** 6, ataque=1),
            ficha_cazador("ent_caz_5000", rango=5000, velocidad=150,
                          vida_max=10 ** 6, ataque=1),
        ]
        otros = [ficha_errante(vida_max=5, ataque=1),
                 ficha_rastreador(vida_max=5, ataque=1)]

        enemigos = []
        for i, ficha in enumerate(cazadores):
            enemigos.append((f"c-{i}", ficha, azar.randrange(1, 37)))
        for i in range(6):
            ficha = otros[i % 2]
            enemigos.append((f"o-{i}", ficha, azar.randrange(1, 37)))

        contenidos = []
        for id_sala in range(1, lado * lado + 1):
            aqui = [(instancia, ficha["id"]) for instancia, ficha, en
                    in enemigos if en == id_sala]
            contenidos.append(contenido(id_sala, enemigos=aqui))

        partida = partida_sintetica(
            esqueleto, contenidos, catalogo(*cazadores, *otros),
            sala_inicial=15, semilla=semilla,
            jugador=nuevo_jugador(vida_max=10 ** 6, ataque=4))

        perseguidor = (None if modo is None else
                       Perseguidor(partida.mapa, 100, 100, modo=modo))
        verificador = Verificador(partida, perseguidor)

        for instancia, ficha, _ in enemigos:
            enemigo = buscar_enemigo(partida, instancia)
            if not enemigo.esta_activo():
                activar(partida, instancia, ficha)

        estadisticas = {"puertas": 0, "muertes": 0, "velocidades": 0,
                        "movimientos_del_jugador": 0}
        todas = partida.mapa.obtener_todas()
        puertas = [todas.obtener(i).obtener_puerta(d)
                   for i in range(len(todas)) for d in "SE"
                   if todas.obtener(i).obtener_puerta(d) is not None]

        pasos = 0
        while verificador.revisadas < turnos_de_cazador and pasos < 20000:
            pasos += 1
            self._un_paso(partida, azar, puertas, estadisticas)

        estadisticas["invalidaciones"] = verificador.perseguidor.invalidaciones
        return verificador, estadisticas

    def _un_paso(self, partida, azar, puertas, estadisticas):
        # Cambios de puertas entre turnos, como haría cualquier evento.
        for _ in range(azar.choice((0, 1, 1, 2))):
            puerta = azar.choice(puertas)
            puerta.cerrada = not puerta.cerrada
            estadisticas["puertas"] += 1

        # De vez en cuando, otro enemigo cambia de velocidad.
        vivos = partida.enemigos_presentes()
        if azar.random() < 0.05:
            todas = partida.mapa.obtener_todas()
            for i in range(len(todas)):
                sala_mapa = todas.obtener(i)
                for j in range(sala_mapa.cantidad_enemigos()):
                    enemigo = sala_mapa.enemigo_en(j)
                    if (enemigo.esta_activo() and enemigo.esta_vivo()
                            and enemigo.comportamiento != "cazador"):
                        partida._cambiar_velocidad(
                            enemigo, azar.choice((50, 100, 200)))
                        estadisticas["velocidades"] += 1
                        break

        sala_actual = partida.sala_actual()
        abiertas = sala_actual.puertas(solo_abiertas=True)
        cerradas = [sala_actual.obtener_puerta(d) for d in "NSEO"
                    if sala_actual.obtener_puerta(d) is not None
                    and sala_actual.obtener_puerta(d).esta_cerrada()]
        tirada = azar.random()

        otros = [vivos.obtener(i) for i in range(len(vivos))
                 if vivos.obtener(i).comportamiento != "cazador"
                 and vivos.obtener(i).esta_activo()
                 and vivos.obtener(i).esta_vivo()]

        if otros and tirada < 0.3:
            enemigo = azar.choice(otros)
            partida.atacar(enemigo)
            if not enemigo.esta_vivo():
                estadisticas["muertes"] += 1
        elif cerradas and tirada < 0.45:
            puerta = azar.choice(cerradas)
            partida.abrir(sala_actual.direccion_de(puerta))
        elif len(abiertas) > 0 and tirada < 0.8:
            puerta = abiertas.obtener(azar.randrange(len(abiertas)))
            partida.mover(sala_actual.direccion_de(puerta))
            estadisticas["movimientos_del_jugador"] += 1
        else:
            partida.esperar()

    def test_sc002_mil_turnos_de_cazador_con_invalidacion_selectiva(self):
        """SC-002, HU3-5: ≥ 1 000 turnos de cazador, todos iguales al
        cálculo desde cero, con muertes, cambios de sala y de velocidad."""
        verificador, estadisticas = self._jugar(2026, 1000, None)

        self.assertGreaterEqual(verificador.revisadas, 1000)
        self.assertEqual(verificador.perseguidor.modo, SELECTIVA)
        for accion in (ATACAR, ESPERAR, MOVER):
            self.assertGreater(verificador.por_accion[accion], 20, accion)
        self.assertGreater(estadisticas["muertes"], 0)
        self.assertGreater(estadisticas["velocidades"], 0)
        self.assertGreater(estadisticas["movimientos_del_jugador"], 100)
        self.assertGreater(estadisticas["puertas"], 200)
        # La invalidación selectiva deja pasar cambios que no importan.
        self.assertLess(estadisticas["invalidaciones"],
                        estadisticas["puertas"])

    def test_sc002_los_otros_modos_tambien_coinciden(self):
        """FR-019, FR-032: «invalidación total» y «recalcular siempre»
        deciden lo mismo que desde cero."""
        for modo in (TOTAL, RECALCULAR):
            with self.subTest(modo=modo):
                verificador, _ = self._jugar(7, 300, modo)
                self.assertGreaterEqual(verificador.revisadas, 300)
                self.assertEqual(verificador.perseguidor.modo, modo)


class TestReplayConCazadores(unittest.TestCase):
    """FR-021, HU3-7: --replay de una partida con cazadores toma las mismas
    decisiones en los mismos instantes."""

    def test_hu3_7_mismas_decisiones_en_el_replay(self):
        esqueleto = anillo()
        fuente = FuenteContadora(
            esqueleto,
            [contenido(1, enemigos=[("c-1", "ent_cazador")]),
             contenido(2), contenido(3), contenido(5), contenido(6)],
            catalogo(ficha_cazador(ataque=2)),
            generales=datos_generales(esqueleto),
        )
        original = Perseguidor.decidir

        def grabar(destino):
            def espia(perseguidor, cazador, sala_jugador):
                decision = original(perseguidor, cazador, sala_jugador)
                destino.append((cazador.evento_siguiente.tiempo,
                                cazador.id_instancia, cazador.sala_actual,
                                resumen(decision)))
                return decision
            return espia

        jugadas, repetidas = [], []

        with tempfile.TemporaryDirectory() as carpeta:
            with patch.object(Perseguidor, "decidir", grabar(jugadas)):
                controlador = controlador_sintetico(
                    fuente, carpeta,
                    ["mover E", "mover E", "esperar", "mover S", "esperar",
                     "mover O", "esperar", "mover N", "esperar"])
                controlador.iniciar()
                controlador.gestor_contenido.cerrar()

            preparador = PreparadorReplay(
                fuente, AlmacenDisco(os.path.join(carpeta, "cache")))

            with patch.object(Perseguidor, "decidir", grabar(repetidas)):
                try:
                    Reproductor(preparador).reproducir(
                        os.path.join(carpeta, "partida.log"))
                finally:
                    preparador.cerrar()

        self.assertGreater(len(jugadas), 3)
        self.assertIn(MOVER, [d[3][0] for d in jugadas])
        self.assertEqual(repetidas, jugadas)


if __name__ == "__main__":
    unittest.main()
