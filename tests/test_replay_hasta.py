"""`--replay … --hasta t` (capacidad 004, T029; FR-413 a FR-416, HU3).

Se llama al `main` de verdad, sin conexión, sobre una copia local en una
carpeta temporal, con una vista que falla si se instancia (FR-414).
"""

import os
import sys
from argparse import Namespace
from unittest.mock import Mock, patch

from crypta import main as programa
from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Vista.FormatoResumen import formatear_resumen
from tests.ayudas_cripta import (
    FICHAS_LINEA, catalogo, contenidos_linea, datos_generales, esqueleto_linea,
)
from tests.test_controlador import ConCriptaDePrueba


CRIPTA_LINEA = "c-linea"


def almacen_de_linea(carpeta):
    """La cripta de la línea de tiempo de las ayudas (con pergaminos en el
    suelo) en una copia local de prueba."""
    almacen = AlmacenDisco(os.path.join(carpeta, "cache"))
    almacen.guardar_catalogo("cat-1", catalogo(*FICHAS_LINEA))
    esqueleto = esqueleto_linea()
    almacen.guardar_cripta(
        CRIPTA_LINEA, "v1", esqueleto, contenidos_linea(),
        datos_generales=datos_generales(esqueleto, presupuesto=1000, version="v1",
                                        cripta_id=CRIPTA_LINEA),
        llaves={"llaves": []})
    return almacen


class ConReplay(ConCriptaDePrueba):
    """Ayudas: jugar una sesión guardando los resúmenes de `historia` y
    correr el `main` con argumentos."""

    cripta = "c-prueba"

    def sesion_con_historia(self, comandos, semilla=7):
        """Juega `comandos` con el Controlador de verdad y devuelve
        (controlador, textos de cada `historia` mostrada)."""
        args = Namespace(cripta=self.cripta, offline=True, jugador="Ana",
                         semilla=semilla, cache_size=25, replay=None, bench=False)

        with patch("crypta.main.AlmacenDisco", return_value=self.almacen):
            controlador, _, _, _ = programa.crear_partida(args)

        controlador.vista = Mock()
        controlador.vista.leer_comando.side_effect = list(comandos) + ["salir"]
        textos = []
        controlador.vista.mostrar_resumen.side_effect = (
            lambda resumen: textos.append(formatear_resumen(resumen)))

        controlador.iniciar()
        controlador.gestor_contenido.cerrar()
        return controlador, textos

    def hasta(self, t, ruta="partida.log"):
        return self.correr_main("--offline", "--replay", ruta, "--hasta", str(t))


class TestReplayHastaConLaCriptaDePrueba(ConReplay):
    """HU3-2, HU3-3 y HU3-4, sobre la cripta de prueba de P1."""

    def test_fr415_hu3_2_partida_terminada_antes_de_t(self):
        """HU3-2 (Apéndice B): se muestra el estado final con su aviso y el
        programa termina con 0."""
        partida = self.morir()
        self.assertTrue(partida.terminada)
        r = partida.reloj

        codigo, salida = self.hasta(r + 7000)

        self.assertEqual(codigo, 0)
        self.assertIn(f"HISTORIA instante {r + 7000}\n", salida)
        self.assertIn(f"Reloj: {r}   ", salida)
        self.assertTrue(salida.endswith(
            f"Aviso: La partida terminó en el instante {r}, antes de {r + 7000}.\n"))

    def test_fr415_hu3_3_log_que_termina_antes_de_t(self):
        partida = self.jugar(["esperar", "esperar", "esperar"])
        self.assertFalse(partida.terminada)
        r = partida.reloj

        codigo, salida = self.hasta(9000)

        self.assertEqual(codigo, 0)
        self.assertIn(f"Reloj: {r}   ", salida)
        self.assertTrue(salida.endswith(
            f"Aviso: El log termina en el instante {r}, antes de 9000.\n"))

    def test_fr415_hu3_3_log_ilegible_termina_con_1(self):
        with open("roto.log", "w", encoding="utf-8") as archivo:
            archivo.write("esto no es un partida.log\n")

        codigo, salida = self.hasta(10, ruta="roto.log")

        self.assertEqual(codigo, 1)
        self.assertNotIn("HISTORIA", salida)

    def test_fr416_hu3_4_hasta_sin_replay_o_invalido(self):
        """HU3-4: error de argumentos (código 2 de argparse), sin iniciar
        ninguna partida: no se crea partida.log."""
        self.jugar(["esperar"])
        os.remove("partida.log")

        for argumentos in (("--hasta", "500"),
                           ("--offline", "--replay", "x.log", "--hasta", "-1"),
                           ("--offline", "--replay", "x.log", "--hasta", "x"),
                           ("--offline", "--replay", "x.log", "--hasta", "2.5")):
            with self.subTest(argumentos=argumentos):
                with patch("sys.stderr"), self.assertRaises(SystemExit) as salida:
                    self.correr_main(*argumentos)
                self.assertEqual(salida.exception.code, 2)
                self.assertFalse(os.path.exists("partida.log"))

    def test_sin_hasta_el_replay_no_cambia(self):
        self.jugar(["esperar", "esperar"])
        codigo, salida = self.correr_main("--offline", "--replay", "partida.log")

        self.assertEqual(codigo, 0)
        self.assertIn("Replay terminado: 2 comandos repetidos.", salida)
        self.assertNotIn("HISTORIA", salida)


class TestReplayHastaConPergaminos(ConReplay):
    """HU3-1 y HU3-5, sobre la cripta de la línea de tiempo (con
    pergaminos en el suelo)."""

    cripta = CRIPTA_LINEA

    def setUp(self):
        super().setUp()
        self.almacen = almacen_de_linea(self.carpeta)

    def test_fr413_fr414_hu3_1_mismo_texto_que_historia(self):
        """HU3-1: `--hasta t` imprime exactamente lo que dio `historia t` en
        la partida, aunque allí el reloj fuera otro, sin la vista."""
        comandos = ["mover E", "esperar", "atacar 1", "esperar", "mover O",
                    "recoger 1", "equipar", "esperar", "esperar", "mover E",
                    "esperar", "esperar"]
        controlador, _ = self.sesion_con_historia(comandos)
        self.assertGreater(controlador.partida.reloj, 500)

        consultas = ["historia 500", "historia 0", "historia 333",
                     f"historia {controlador.partida.reloj}"]
        _, textos = self.sesion_con_historia(comandos + consultas)
        self.assertEqual(len(textos), len(consultas))

        for consulta, texto in zip(consultas, textos):
            t = consulta.split()[1]
            with self.subTest(t=t):
                codigo, salida = self.hasta(t)
                self.assertEqual(codigo, 0)
                self.assertTrue(salida.endswith(texto), salida)

    def test_fr410_fr413_hu3_5_log_con_pergamino(self):
        """HU3-5: el resumen corresponde a la partida tal como quedó, sin las
        acciones revertidas."""
        comandos = ["recoger pergamino", "recoger pergamino", "mover E", "esperar",
                    "mover E", "pergamino", "pergamino", "esperar", "esperar"]
        controlador, _ = self.sesion_con_historia(comandos)
        partida = controlador.partida
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 0)

        with open("partida.log", encoding="utf-8") as archivo:
            comandos_log = archivo.read().split("---")[1].split("\n")
        self.assertEqual(comandos_log.count("pergamino"), 2)

        n = partida.acciones_jugador
        consultas = [f"historia #{k}" for k in range(1, n + 2)] + \
                    [f"historia {t}" for t in (0, 120, 260, partida.reloj)]
        _, textos = self.sesion_con_historia(comandos + consultas)

        for consulta, texto in zip(consultas, textos):
            t = consulta.split()[1]
            if t.startswith("#"):
                continue          # --hasta solo recibe instantes
            with self.subTest(t=t):
                codigo, salida = self.hasta(t)
                self.assertEqual(codigo, 0)
                self.assertTrue(salida.endswith(texto), salida)

        # Lo revertido no está: en el instante final el jugador sigue en la
        # sala del primer «mover E» (el segundo se revirtió).
        codigo, salida = self.hasta(partida.reloj)
        self.assertIn(f"Sala: {partida.jugador.sala_actual} ", salida)


if __name__ == "__main__":
    import unittest
    unittest.main()
