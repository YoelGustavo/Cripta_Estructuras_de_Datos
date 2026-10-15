
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from crypta.Controlador.Controlador import Controlador
from crypta.Controlador.Comandos import ComandoInvalido
from crypta.Modelo.Partida import AccionInvalida


class TestControlador(unittest.TestCase):

    def setUp(self):
        self.partida = Mock()
        self.partida.iniciada = True
        self.partida.terminada = False
        self.partida.jugador.sala_actual = 1

        self.gestor = Mock()
        self.vista = Mock()
        self.registro = Mock()

        self.controlador = Controlador(
            partida=self.partida,
            gestor_contenido=self.gestor,
            vista=self.vista,
            registro=self.registro,
        )

    def test_comando_vacio(self):
        resultado = self.controlador.procesar_comando("   ")

        self.assertFalse(resultado)
        self.vista.mostrar_error.assert_called_once()

    def test_ayuda(self):
        resultado = self.controlador.procesar_comando("ayuda")

        self.assertTrue(resultado)
        self.vista.mostrar_ayuda.assert_called_once()
        self.registro.anotar.assert_not_called()

    def test_estado(self):
        resultado = self.controlador.procesar_comando("estado")

        self.assertTrue(resultado)
        self.vista.mostrar_estado.assert_called_once_with(
            self.partida
        )
        self.registro.anotar.assert_not_called()

    def test_inventario(self):
        resultado = self.controlador.procesar_comando("inventario")

        self.assertTrue(resultado)
        self.vista.mostrar_inventario.assert_called_once_with(
            self.partida.jugador.inventario
        )

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_movimiento(self, ejecutar):
        resultado = self.controlador.procesar_comando("mover N")

        self.assertTrue(resultado)
        ejecutar.assert_called_once_with(
            self.partida,
            "mover N",
            garantizar_sala=self.gestor.garantizar_sala,
        )
        self.registro.anotar.assert_called_once_with("mover N")

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_registro_accion(self, ejecutar):
        resultado = self.controlador.procesar_comando("esperar")

        self.assertTrue(resultado)
        self.registro.anotar.assert_called_once_with("esperar")

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_accion_invalida_no_se_registra(self, ejecutar):
        ejecutar.side_effect = AccionInvalida("Acción inválida")

        resultado = self.controlador.procesar_comando("mover N")

        self.assertFalse(resultado)
        self.registro.anotar.assert_not_called()
        self.vista.mostrar_error.assert_called_once()

    @patch("crypta.Controlador.Controlador.ejecutar_comando")
    def test_comando_invalido_no_se_registra(self, ejecutar):
        ejecutar.side_effect = ComandoInvalido("Comando inválido")

        resultado = self.controlador.procesar_comando("desconocido")

        self.assertFalse(resultado)
        self.registro.anotar.assert_not_called()

    def test_guardar_sin_encabezado(self):
        resultado = self.controlador.procesar_comando("guardar")

        self.assertFalse(resultado)
        self.vista.mostrar_error.assert_called_once()

    @patch("crypta.Controlador.Controlador.guardar_partida")
    def test_guardar_con_encabezado(self, guardar):
        self.controlador.encabezado = Mock()

        resultado = self.controlador.procesar_comando("guardar")

        self.assertTrue(resultado)
        guardar.assert_called_once_with(
            self.partida,
            "partida.cripta",
            self.controlador.encabezado,
        )

    @patch.object(Controlador, "cargar_partida")
    def test_cargar(self, cargar):
        resultado = self.controlador.procesar_comando("cargar")

        self.assertTrue(resultado)
        cargar.assert_called_once_with("partida.cripta")

    @patch.object(Controlador, "cargar_partida")
    def test_error_al_cargar(self, cargar):
        cargar.side_effect = ValueError("Archivo incompatible")

        resultado = self.controlador.procesar_comando("cargar")

        self.assertFalse(resultado)
        self.vista.mostrar_error.assert_called_once()

    def test_alias_siguiente(self):
        self.assertEqual(
            self.controlador._traducir("siguiente"),
            "avanzar"
        )

    def test_recoger_numero(self):
        self.assertEqual(
            self.controlador._traducir("recoger 1"),
            "recoger 0"
        )

    def test_recoger_numero_invalido(self):
        with self.assertRaises(ComandoInvalido):
            self.controlador._traducir("recoger 0")


if __name__ == "__main__":
    unittest.main()
