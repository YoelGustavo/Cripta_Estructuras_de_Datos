"""Pruebas de la capacidad 001, historia 1: terreno con costo.

Especificación: specs/001-terreno-cazador/spec.md. Cada prueba cita su FR y
su escenario (HU1-n = escenario n de la historia 1).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_terreno
"""

import json
import os
import unittest

from tests.datos.grabar_esperado_p1 import (
    RUTA_ESPERADO, RUTA_LOG, repetir_partida_p1,
)


class TestCompatibilidadP1(unittest.TestCase):
    """FR-008, HU1-8: una cripta sin ningún campo costo se juega exactamente
    igual que en la primera parte.

    Repite `tests/datos/p1_partida.log`, grabado con el código de la primera
    parte, sobre la copia fija `p1_cripta-01.json` y `p1_catalogo.json`
    (copiada a una carpeta temporal; nunca usa `cache/`), sin red, y compara
    con `p1_esperado.json`: mismos instantes, eventos, mensajes, estado del
    generador aleatorio y resultado, después de cada comando y al final.

    Esta prueba pasa desde antes de la capacidad 001: protege lo que ya
    funciona."""

    @classmethod
    def setUpClass(cls):
        with open(RUTA_ESPERADO, encoding="utf-8") as archivo:
            cls.esperado = json.load(archivo)

        cls.obtenido = repetir_partida_p1()

    def test_fr008_los_datos_fijos_no_declaran_costos(self):
        """FR-008: la copia fija es de la primera parte, sin campo costo."""
        carpeta = os.path.dirname(RUTA_LOG)

        for nombre in ("p1_cripta-01.json", "p1_catalogo.json"):
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as archivo:
                self.assertNotIn('"costo"', archivo.read(), nombre)

    def test_fr008_se_repiten_todos_los_comandos(self):
        """FR-008: el registro se repite completo, sin comandos rechazados."""
        self.assertEqual(len(self.obtenido["comandos"]),
                         len(self.esperado["comandos"]))

    def test_fr008_mismo_estado_despues_de_cada_comando(self):
        """FR-008: mismos instantes, eventos, mensajes y llamadas al azar
        después de cada comando."""
        for esperado, obtenido in zip(self.esperado["comandos"],
                                      self.obtenido["comandos"]):
            with self.subTest(numero=esperado["numero"],
                              comando=esperado["comando"]):
                self.assertEqual(obtenido, esperado)

    def test_fr008_mismo_resultado_final(self):
        """FR-008: mismo reloj, sala, vida, resultado y estado del azar al
        terminar."""
        self.assertEqual(self.obtenido["final"], self.esperado["final"])
        self.assertTrue(self.obtenido["final"]["terminada"])


if __name__ == "__main__":
    unittest.main()
