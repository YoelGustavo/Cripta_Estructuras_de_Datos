"""Pruebas del equipo: arma y armadura (Fase 3, paso 2).

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_equipo
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import unittest

from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Inventario import Inventario
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Sala import Sala


# Fichas como las del catálogo (§2.7 y §3.3).
DAGA = {"id": "itm_daga_oxidada", "clase": "arma", "nombre": "Daga oxidada",
        "peso": 2, "valor": 15, "ataque_bonus": 3}
ESPADA = {"id": "itm_espada", "clase": "arma", "nombre": "Espada",
          "peso": 4, "valor": 40, "ataque_bonus": 6}
COTA = {"id": "itm_cota", "clase": "armadura", "nombre": "Cota de malla",
        "peso": 8, "valor": 50, "defensa_bonus": 4}
POCION = {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción menor",
          "peso": 1, "valor": 10, "cura": 8}


def nombres(inventario):
    return [o["nombre"] for o in inventario.orden_real()]


def jugador_con(*objetos):
    """Jugador del ejemplo del enunciado (ataque 5, defensa 2) con esos
    objetos en el inventario, viendo el primero."""
    jugador = Jugador("Héroe", vida_max=30, ataque=5, defensa=2,
                      velocidad=100, inventario_max=10)
    for objeto in objetos:
        jugador.inventario.recoger(objeto)
    return jugador


def ir_a(inventario, posicion):
    while inventario.retroceder() is not None:
        pass
    for _ in range(posicion):
        inventario.avanzar()


# ----------------------------------------------------------------------

class TestSinEquipo(unittest.TestCase):
    def test_totales_son_los_base(self):
        jugador = jugador_con(DAGA, COTA)
        self.assertIsNone(jugador.arma())
        self.assertIsNone(jugador.armadura())
        self.assertEqual((jugador.ataque_total(), jugador.defensa_total()), (5, 2))

    def test_inventario_vacio(self):
        self.assertIsNone(Inventario(3).equipar_actual_con_contexto())


class TestEquipar(unittest.TestCase):
    def test_equipar_arma(self):
        jugador = jugador_con(POCION, DAGA)
        ir_a(jugador.inventario, 1)
        jugador.inventario.equipar_actual_con_contexto()
        self.assertIs(jugador.arma(), DAGA)
        self.assertEqual(jugador.ataque_total(), 5 + 3)
        self.assertEqual(jugador.defensa_total(), 2)          # no la toca

    def test_equipar_mueve_al_frente(self):
        """§4.5: equipar mueve el objeto al frente del orden real."""
        jugador = jugador_con(POCION, DAGA)
        ir_a(jugador.inventario, 1)
        jugador.inventario.equipar_actual_con_contexto()
        self.assertEqual(nombres(jugador.inventario), ["Daga oxidada", "Poción menor"])

    def test_equipar_armadura(self):
        jugador = jugador_con(COTA)
        jugador.inventario.equipar_actual_con_contexto()
        self.assertIs(jugador.armadura(), COTA)
        self.assertEqual(jugador.defensa_total(), 2 + 4)

    def test_arma_y_armadura_a_la_vez(self):
        jugador = jugador_con(DAGA, COTA)
        jugador.inventario.equipar_actual_con_contexto()          # daga
        ir_a(jugador.inventario, 1)
        jugador.inventario.equipar_actual_con_contexto()          # cota
        self.assertEqual((jugador.ataque_total(), jugador.defensa_total()), (8, 6))

    def test_otra_arma_sustituye_y_la_vieja_se_queda(self):
        """§2.7: equipar otra del mismo tipo sustituye a la anterior,
        que permanece en el inventario."""
        jugador = jugador_con(DAGA, ESPADA)
        jugador.inventario.equipar_actual_con_contexto()          # daga
        ir_a(jugador.inventario, 1)
        jugador.inventario.equipar_actual_con_contexto()          # espada
        self.assertIs(jugador.arma(), ESPADA)
        self.assertEqual(jugador.ataque_total(), 5 + 6)
        self.assertEqual(nombres(jugador.inventario), ["Espada", "Daga oxidada"])

    def test_no_se_puede_equipar_una_pocion(self):
        jugador = jugador_con(DAGA, POCION)
        ir_a(jugador.inventario, 1)
        with self.assertRaises(ValueError):
            jugador.inventario.equipar_actual_con_contexto()
        self.assertEqual(nombres(jugador.inventario), ["Daga oxidada", "Poción menor"])
        self.assertIsNone(jugador.arma())

    def test_arma_sin_bono_en_la_ficha(self):
        palo = {"id": "itm_palo", "clase": "arma", "nombre": "Palo", "peso": 1, "valor": 1}
        jugador = jugador_con(palo)
        jugador.inventario.equipar_actual_con_contexto()
        self.assertEqual(jugador.ataque_total(), 5)

    def test_marca_de_equipado(self):
        jugador = jugador_con(DAGA, POCION)
        self.assertFalse(jugador.inventario.actual_esta_equipado())
        jugador.inventario.equipar_actual_con_contexto()
        self.assertTrue(jugador.inventario.actual_esta_equipado())
        jugador.inventario.avanzar()
        self.assertFalse(jugador.inventario.actual_esta_equipado())

    def test_equipar_viejo_sigue_funcionando(self):
        jugador = jugador_con(DAGA)
        self.assertIs(jugador.inventario.equipar_actual(), DAGA)
        self.assertIs(jugador.arma(), DAGA)


class TestDeshacerEquipar(unittest.TestCase):
    def test_deshacer_sin_nada_equipado_antes(self):
        jugador = jugador_con(POCION, DAGA)
        ir_a(jugador.inventario, 1)
        contexto = jugador.inventario.equipar_actual_con_contexto()
        jugador.inventario.restaurar_equipado(contexto)
        self.assertIsNone(jugador.arma())
        self.assertEqual(jugador.ataque_total(), 5)
        self.assertEqual(nombres(jugador.inventario), ["Poción menor", "Daga oxidada"])

    def test_deshacer_vuelve_al_arma_anterior(self):
        jugador = jugador_con(DAGA, ESPADA)
        jugador.inventario.equipar_actual_con_contexto()          # daga
        ir_a(jugador.inventario, 1)
        contexto = jugador.inventario.equipar_actual_con_contexto()   # espada
        jugador.inventario.restaurar_equipado(contexto)
        self.assertIs(jugador.arma(), DAGA)
        self.assertEqual(nombres(jugador.inventario), ["Daga oxidada", "Espada"])

    def test_con_el_historial(self):
        """Así lo usará la partida: un Cambio de operación dentro de la acción."""
        jugador = jugador_con(POCION, ESPADA)
        ir_a(jugador.inventario, 1)
        accion = RegistroAccion("equipar")
        contexto = jugador.inventario.equipar_actual_con_contexto()
        accion.registrar_cambio(
            Cambio.de_operacion("equipar", jugador.inventario, "restaurar_equipado", contexto))
        accion.deshacer()
        self.assertIsNone(jugador.arma())
        self.assertEqual(nombres(jugador.inventario), ["Poción menor", "Espada"])


class TestSoltarEquipado(unittest.TestCase):
    def test_soltar_el_arma_la_desequipa(self):
        jugador = jugador_con(DAGA, POCION)
        jugador.inventario.equipar_actual_con_contexto()
        jugador.inventario.soltar_actual_con_contexto()
        self.assertIsNone(jugador.arma())
        self.assertEqual(jugador.ataque_total(), 5)

    def test_deshacer_soltar_la_vuelve_a_equipar(self):
        jugador = jugador_con(DAGA, POCION)
        jugador.inventario.equipar_actual_con_contexto()
        contexto = jugador.inventario.soltar_actual_con_contexto()
        jugador.inventario.restaurar_soltado(contexto)
        self.assertIs(jugador.arma(), DAGA)
        self.assertEqual(jugador.ataque_total(), 8)

    def test_soltar_otro_objeto_no_desequipa(self):
        jugador = jugador_con(DAGA, POCION)
        jugador.inventario.equipar_actual_con_contexto()
        jugador.inventario.avanzar()
        jugador.inventario.soltar_actual_con_contexto()           # la poción
        self.assertIs(jugador.arma(), DAGA)

    def test_dos_dagas_iguales(self):
        """§2.7: varias instancias comparten la ficha. Soltar la daga que NO
        está equipada no debe desequipar la otra."""
        jugador = jugador_con(DAGA, DAGA)                         # el MISMO dict
        ir_a(jugador.inventario, 1)
        jugador.inventario.equipar_actual_con_contexto()          # la 2.ª, pasa al frente
        jugador.inventario.avanzar()                              # la 1.ª (sin equipar)
        self.assertFalse(jugador.inventario.actual_esta_equipado())
        jugador.inventario.soltar_actual_con_contexto()
        self.assertIs(jugador.arma(), DAGA)
        self.assertEqual(len(jugador.inventario), 1)

    def test_soltar_en_sala_y_deshacer(self):
        jugador = jugador_con(COTA)
        jugador.inventario.equipar_actual_con_contexto()
        sala = Sala(1, "Celda", None)
        contexto = jugador.inventario.soltar_en_sala(sala)
        self.assertIsNone(jugador.armadura())
        self.assertEqual(sala.objeto_en(0), "itm_cota")
        jugador.inventario.deshacer_soltar_en_sala(contexto)
        self.assertIs(jugador.armadura(), COTA)
        self.assertEqual(sala.cantidad_objetos(), 0)

    def test_soltar_viejo_tambien_desequipa(self):
        jugador = jugador_con(DAGA)
        jugador.inventario.equipar_actual_con_contexto()
        self.assertIs(jugador.inventario.soltar_actual(), DAGA)
        self.assertIsNone(jugador.arma())


if __name__ == "__main__":
    unittest.main()