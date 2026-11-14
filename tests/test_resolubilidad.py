"""Pruebas de la verificación de resolubilidad (capacidad 003).

Cada prueba cita su FR (y su escenario HUx-n cuando lo tiene) en el nombre o
en el docstring (principio IX).

    python -m unittest -v tests.test_resolubilidad
"""

import unittest

from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
from tests.ayudas_cripta import mapa_de, respuesta_llaves, sala, salida, ubicacion


# Salas 1 a 5 en cadena; solo importa qué salas existen.
ESQUELETO_CINCO = [
    sala(1, {"E": salida(2)}),
    sala(2, {"O": salida(1), "E": salida(3)}),
    sala(3, {"O": salida(2), "E": salida(4)}),
    sala(4, {"O": salida(3), "E": salida(5)}),
    sala(5, {"O": salida(4)}),
]


class TestUbicacionLlaves(unittest.TestCase):
    """FR-319: lectura y validación de GET /criptas/<id>/llaves
    (contracts/datos-servicio.md); carga de HU3-7."""

    def setUp(self):
        self.mapa = mapa_de(ESQUELETO_CINCO)

    def leer(self, respuesta):
        return leer_ubicaciones(respuesta, self.mapa)

    def rechaza(self, respuesta, *fragmentos):
        with self.assertRaises(DatosInvalidos) as contexto:
            self.leer(respuesta)

        mensaje = str(contexto.exception)
        self.assertIn("la ubicación de llaves tiene un dato inválido", mensaje)

        for fragmento in fragmentos:
            self.assertIn(fragmento, mensaje)

        return mensaje

    def test_respuesta_valida_FR_319(self):
        ubicaciones = self.leer(respuesta_llaves(
            ubicacion("itm_llave_a", 2),
            ubicacion("itm_llave_b", 5, enemigo="e-501"),
        ))

        self.assertEqual(len(ubicaciones), 2)

        primera = ubicaciones.obtener(0)
        self.assertEqual(primera.id_llave, "itm_llave_a")
        self.assertEqual(primera.id_sala, 2)
        self.assertEqual(primera.indice_sala, self.mapa.obtener_sala(2).indice)
        self.assertIsNone(primera.enemigo)
        self.assertIsNone(primera.numero_llave)

        segunda = ubicaciones.obtener(1)
        self.assertEqual(segunda.id_llave, "itm_llave_b")
        self.assertEqual(segunda.id_sala, 5)
        self.assertEqual(segunda.indice_sala, self.mapa.obtener_sala(5).indice)
        self.assertEqual(segunda.enemigo, "e-501")

    def test_repetidas_lista_vacia_y_campos_extra_son_validos_FR_319(self):
        repetidas = self.leer(respuesta_llaves(
            ubicacion("itm_llave_a", 2), ubicacion("itm_llave_a", 2),
            ubicacion("itm_llave_a", 4)))
        self.assertEqual(len(repetidas), 3)

        self.assertEqual(len(self.leer({"llaves": []})), 0)

        extra = self.leer({"llaves": [{"id": "itm_llave_a", "sala": 1,
                                       "enemigo": None, "otro": 7}],
                           "version": "v9"})
        self.assertEqual(len(extra), 1)
        self.assertIsNone(extra.obtener(0).enemigo)

    def test_raiz_invalida_FR_319(self):
        self.rechaza({}, "llaves")
        self.rechaza({"llaves": {"id": "itm_llave_a", "sala": 1}}, "llaves")
        self.rechaza([], "llaves")
        self.rechaza(None, "llaves")

    def test_entrada_que_no_es_objeto_FR_319(self):
        self.rechaza({"llaves": [ubicacion("itm_llave_a", 1), "itm_llave_b"]},
                     "entrada 2")

    def test_id_invalido_FR_319(self):
        self.rechaza({"llaves": [{"sala": 1}]}, "entrada 1", "id")
        self.rechaza({"llaves": [{"id": "", "sala": 1}]}, "entrada 1", "id")
        self.rechaza({"llaves": [{"id": 7, "sala": 1}]}, "entrada 1", "id")
        self.rechaza({"llaves": [ubicacion("itm_llave_a", 1),
                                 {"id": None, "sala": 1}]}, "entrada 2", "id")

    def test_sala_invalida_FR_319(self):
        """Solo vale un entero JSON: se rechazan bool, float y texto, como
        el costo de la 001."""
        for valor in (True, 2.5, 2.0, "4", None):
            with self.subTest(sala=valor):
                self.rechaza({"llaves": [{"id": "itm_llave_a", "sala": valor}]},
                             "entrada 1", "itm_llave_a", "sala")

        self.rechaza({"llaves": [{"id": "itm_llave_a"}]},
                     "entrada 1", "itm_llave_a", "sala")

    def test_sala_inexistente_FR_319_HU3_7(self):
        """HU3-7: una llave en una sala que no existe en el esqueleto."""
        mensaje = self.rechaza(respuesta_llaves(
            ubicacion("itm_llave_a", 1), ubicacion("itm_llave_b", 99)),
            "entrada 2", "itm_llave_b", "99")
        self.assertIn("no existe", mensaje)

    def test_enemigo_invalido_FR_319(self):
        for valor in (5, True, ["e-1"]):
            with self.subTest(enemigo=valor):
                self.rechaza({"llaves": [{"id": "itm_llave_a", "sala": 1,
                                          "enemigo": valor}]},
                             "entrada 1", "itm_llave_a", "enemigo")


if __name__ == "__main__":
    unittest.main()
