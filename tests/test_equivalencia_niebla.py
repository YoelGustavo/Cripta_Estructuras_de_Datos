"""Equivalencia de la niebla de guerra y de «ir a» (capacidad 002, T041).

- **SC-202** (FR-207, FR-209): después de cada comando y de cada paso de un
  viaje, ni la sección SALIDAS de `mostrar_estado`, ni el texto de `mapa`,
  ni los mensajes nuevos de la bitácora muestran algo que el jugador no
  conoce. Se lee por estructura (las líneas de cada sección), no buscando
  números en el texto crudo.
- **FR-204**: las salidas de la sala actual se recuerdan como son.
- **FR-201, FR-202**: `conocimiento.validar` no lanza.
- **SC-203** (FR-217, FR-218): antes de cada paso de `ir a`, la dirección
  elegida reutilizando coincide con `paso_desde_cero`.

Las partidas son las de `partida_niebla` (sin red, sin `cache/`), con
antorchas, puertas que cambian, pergaminos y viajes.
"""

import io
import random
import unittest
from contextlib import redirect_stdout

from crypta.Controlador.Comandos import (
    ComandoInvalido,
    ejecutar_comando,
    ejecutar_ir_a,
    leer_ir_a,
)
from crypta.Modelo.MapaConocido import AVISTADA, DESCONOCIDA, EXPLORADA
from crypta.Modelo.Partida import AccionInvalida
from crypta.Modelo.Puerta import ABIERTA, CERRADA
from crypta.Modelo.Resumen import armar_mapa_resumido
from crypta.Modelo.Viaje import SIN_RUTA
from crypta.Vista.FormatoMapa import formatear_mapa
from crypta.Vista.VistaConsola import VistaConsola
from tests.ayudas_cripta import comandos_niebla, partida_niebla


SEMILLAS = range(200, 222)            # 22 partidas
COMANDOS = 200
# Un viaje correcto nunca da vueltas: si una ruta reutilizada quedara mal,
# podría ir y venir sin fin. Con este tope la prueba falla en vez de colgarse.
MAXIMO_PASOS_POR_VIAJE = 200


def texto_estado(partida):
    capturada = io.StringIO()

    with redirect_stdout(capturada):
        VistaConsola().mostrar_estado(partida)

    return capturada.getvalue()


def lineas_salidas(texto):
    """Las líneas de la sección SALIDAS: «<d>: sala <id> (<estado>)»."""
    lineas = texto.splitlines()
    inicio = lineas.index("SALIDAS") + 1
    fin = lineas.index("ENEMIGOS")
    return [linea.strip() for linea in lineas[inicio:fin] if linea.strip()]


def id_de_salida(linea):
    """El id de «N: sala 7 (Abierta, costo 100)», leído por posición."""
    direccion, resto = linea.split(": ", 1)
    palabra, id_sala, _ = resto.split(" ", 2)
    assert direccion in "NSEO" and palabra == "sala", linea
    return int(id_sala)


def leer_mapa(texto):
    """(exploradas, avistadas, destinos) del texto de `mapa`
    (contracts/vista.md «Mapa»): ids de las salas exploradas, de las
    avistadas y de los destinos de sus salidas, leídos por estructura."""
    lineas = texto.rstrip("\n").split("\n")
    assert lineas[0].startswith("MAPA CONOCIDO ("), lineas[0]
    assert lineas[1] == "Exploradas:", lineas[1]
    assert lineas[-1].startswith("Avistadas: "), lineas[-1]

    exploradas = []
    destinos = []

    for linea in lineas[2:-1]:
        if linea.startswith("    "):
            direccion, resto = linea.strip().split(": ", 1)
            palabra, id_destino = resto.split(", ")[0].split(" ")
            assert direccion in "NSEO" and palabra == "sala", linea
            destinos.append(int(id_destino))
        else:
            assert linea.startswith("  ") and not linea.startswith("   "), linea
            exploradas.append(int(linea.strip().split(" ", 1)[0]))

    lista = lineas[-1][len("Avistadas: "):]
    avistadas = [] if lista == "ninguna" else [int(x) for x in lista.split(", ")]
    return exploradas, avistadas, destinos


class Comprobador:
    """Comprueba SC-202, FR-201, FR-202 y FR-204 sobre una partida. Guarda
    los mensajes nuevos de la bitácora envolviendo `bitacora.agregar` (la
    bitácora guarda solo los últimos 20 y el pergamino no los borra)."""

    def __init__(self, prueba, partida):
        self.prueba = prueba
        self.partida = partida
        self.nuevos = []
        agregar = partida.bitacora.agregar

        def agregar_y_guardar(reloj, texto):
            self.nuevos.append(texto)
            agregar(reloj, texto)

        partida.bitacora.agregar = agregar_y_guardar
        self.comprobaciones = 0

    def estado_de(self, id_sala):
        sala = self.partida.mapa.obtener_sala(id_sala)
        return None if sala is None else self.partida.conocimiento.estado(sala)

    def comprobar(self, contexto):
        partida = self.partida
        prueba = self.prueba
        conocimiento = partida.conocimiento
        self.comprobaciones += 1

        # FR-201, FR-202.
        try:
            conocimiento.validar(partida.id_sala_inicial)
        except ValueError as error:
            prueba.fail(f"{contexto}: {error}")

        # FR-204: la sala actual se observó antes de esta decisión.
        if not partida.terminada:
            puertas = partida.sala_actual().puertas()

            for i in range(len(puertas)):
                estado = puertas.obtener(i).estado
                real = CERRADA if estado.cerrada else ABIERTA
                prueba.assertEqual(estado.recordada, real,
                                   f"{contexto}: FR-204")

        # SC-202 (a): cada sala de SALIDAS es conocida o no existe.
        salidas = lineas_salidas(texto_estado(partida))

        for linea in salidas:
            estado = self.estado_de(id_de_salida(linea))
            prueba.assertNotEqual(estado, DESCONOCIDA,
                                  f"{contexto}: SALIDAS «{linea}»")

        # SC-202 (b): el mapa lista exactamente lo explorado y lo avistado.
        texto_mapa = formatear_mapa(armar_mapa_resumido(partida))
        exploradas, avistadas, destinos = leer_mapa(texto_mapa)
        reales_exploradas = []
        reales_avistadas = []

        for sala, estado in conocimiento.salas_conocidas():
            if estado == EXPLORADA:
                reales_exploradas.append(sala.id)
            else:
                reales_avistadas.append(sala.id)

        prueba.assertEqual(exploradas, reales_exploradas, contexto)
        prueba.assertEqual(avistadas, reales_avistadas, contexto)
        prueba.assertEqual(conocimiento.exploradas, len(exploradas), contexto)
        prueba.assertEqual(conocimiento.avistadas, len(avistadas), contexto)

        for id_destino in destinos:
            prueba.assertNotEqual(self.estado_de(id_destino), DESCONOCIDA,
                                  f"{contexto}: destino {id_destino} del mapa")

        # SC-202 (c): ningún nombre de sala no explorada en SALIDAS, en el
        # mapa ni en los mensajes nuevos de la bitácora.
        textos = salidas + [texto_mapa] + self.nuevos
        todas = partida.mapa.obtener_todas()

        for i in range(len(todas)):
            sala = todas.obtener(i)

            if conocimiento.estado(sala) == EXPLORADA:
                continue

            for texto in textos:
                prueba.assertNotIn(sala.nombre, texto,
                                   f"{contexto}: FR-207/FR-209")

        self.nuevos = []


def jugar(prueba, semilla):
    """Juega una partida de `partida_niebla(semilla)` con `comandos_niebla`
    y comprueba todo después de cada comando y de cada paso. Devuelve
    (pasos comparados, diferencias SC-203, cuántos usos de antorcha,
    pergamino y viajes con pasos)."""
    partida = partida_niebla(semilla)
    comprobador = Comprobador(prueba, partida)
    azar = random.Random(semilla)
    cuenta = {"pasos": 0, "diferencias": 0, "antorcha": 0, "pergamino": 0,
              "viajes": 0}
    comprobador.comprobar(f"semilla {semilla}, inicio")

    for numero, comando in enumerate(comandos_niebla(partida, azar, COMANDOS)):
        contexto = f"semilla {semilla}, comando {numero} «{comando}»"

        if comando.startswith("ir a "):
            id_destino = leer_ir_a(comando)
            pasos_del_viaje = [0]

            def paso(linea, id_destino=id_destino, contexto=contexto,
                     pasos_del_viaje=pasos_del_viaje):
                pasos_del_viaje[0] += 1

                if pasos_del_viaje[0] > MAXIMO_PASOS_POR_VIAJE:
                    prueba.fail(f"{contexto}: el viaje no termina")

                # SC-203: la dirección elegida reutilizando es la de un
                # cálculo desde cero sobre el mismo conocimiento.
                sala = partida.sala_actual()
                destino = partida.mapa.obtener_sala(id_destino)
                desde_cero = partida.ruta_conocida().paso_desde_cero(
                    sala, destino)
                cuenta["pasos"] += 1

                if (desde_cero is None
                        or linea != f"mover {sala.direccion_de(desde_cero)}"):
                    cuenta["diferencias"] += 1

                ejecutar_comando(partida, linea)
                comprobador.comprobar(f"{contexto}, paso {linea}")

            def sin_ruta_desde_cero(id_destino=id_destino):
                """SC-203 también cuando la ruta reutilizada dice que no
                hay ruta: desde cero tampoco debe haberla."""
                cuenta["pasos"] += 1
                destino = partida.mapa.obtener_sala(id_destino)

                if partida.ruta_conocida().paso_desde_cero(
                        partida.sala_actual(), destino) is not None:
                    cuenta["diferencias"] += 1

            try:
                viaje = ejecutar_ir_a(partida, id_destino, paso)
            except AccionInvalida as error:
                # Solo el rechazo al validar es esperable; un error dentro
                # de un paso (mover contra una puerta cerrada) es un fallo.
                if pasos_del_viaje[0] > 0:
                    raise

                if str(error).startswith("No conoces una ruta"):
                    sin_ruta_desde_cero()

                continue

            if viaje.motivo == SIN_RUTA:
                sin_ruta_desde_cero()

            if viaje.pasos > 0:
                cuenta["viajes"] += 1
        else:
            antorcha_antes = partida.antorcha_encendida()
            pergaminos_antes = partida.jugador.inventario.cantidad_pergaminos()

            try:
                ejecutar_comando(partida, comando)
            except (ComandoInvalido, AccionInvalida):
                continue

            if not antorcha_antes and partida.antorcha_encendida():
                cuenta["antorcha"] += 1

            if (comando == "pergamino"
                    and partida.jugador.inventario.cantidad_pergaminos()
                    < pergaminos_antes):
                cuenta["pergamino"] += 1

        comprobador.comprobar(contexto)

    return cuenta


class TestEquivalenciaNiebla(unittest.TestCase):
    """SC-202, SC-203 (FR-201, FR-202, FR-204, FR-207, FR-209, FR-217,
    FR-218)."""

    def test_sc202_sc203_niebla_y_ruta_en_partidas_generadas(self):
        total = {"pasos": 0, "diferencias": 0, "antorcha": 0, "pergamino": 0,
                 "viajes": 0}
        con_antorcha = 0
        con_pergamino = 0

        for semilla in SEMILLAS:
            with self.subTest(semilla=semilla):
                cuenta = jugar(self, semilla)

                for clave in total:
                    total[clave] += cuenta[clave]

                con_antorcha += cuenta["antorcha"] > 0
                con_pergamino += cuenta["pergamino"] > 0
                self.assertEqual(cuenta["diferencias"], 0)

        # Al menos 20 partidas con antorcha, pergaminos y viajes de verdad.
        self.assertGreaterEqual(len(SEMILLAS), 20)
        self.assertGreaterEqual(con_antorcha, len(SEMILLAS) // 2)
        self.assertGreaterEqual(con_pergamino, len(SEMILLAS) // 2)
        self.assertGreaterEqual(total["viajes"], 2 * len(SEMILLAS))
        self.assertGreaterEqual(total["pasos"], 200)
        self.assertEqual(total["diferencias"], 0)


if __name__ == "__main__":
    unittest.main()
