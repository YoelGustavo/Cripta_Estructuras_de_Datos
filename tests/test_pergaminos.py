"""Pruebas de los pergaminos de retroceso (Fase 3, paso 3).
 
Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_pergaminos
o todas las pruebas del proyecto:
    python -m unittest -v
 
Las acciones se registran como lo hará la partida (§2.11): al EMPEZAR cada
acción, historial.registrar(RegistroAccion); cada cambio reversible con
registrar_cambio. Lo de los pergaminos NO se registra.
"""
 
import unittest
 
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.EstadoJuego import EstadoJuego
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Inventario import Inventario
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Sala import Sala
 
 
PERGAMINO = "itm_pergamino_retroceso"
 
 
def ficha(id_objeto, clase="arma"):
    return {"id": id_objeto, "nombre": id_objeto, "clase": clase, "peso": 1, "valor": 1}
 
 
def es_pergamino(id_objeto):
    # En el juego esto lo dirá la ficha: ficha["clase"] == "pergamino_retroceso".
    return id_objeto == PERGAMINO
 
 
def sala_con(*ids):
    sala = Sala(1, "Cripta", None)
    sala.asignar_contenido({"sala": 1, "objetos": list(ids)})
    sala.apartar_pergaminos(es_pergamino)
    return sala
 
 
def suelo(sala):
    return [sala.objeto_en(i) for i in range(sala.cantidad_objetos())]
 
 
class Partida:
    """Lo mínimo de la Fase 4 para probar acciones reales con el historial."""
 
    def __init__(self, capacidad=5, pergaminos=0):
        self.estado = EstadoJuego(Inventario(capacidad))
        self.inventario = self.estado.inventario
        self.inventario.fijar_pergaminos(pergaminos)
 
    def accion(self, nombre, costo):
        self.estado.historial.registrar(RegistroAccion(nombre))
        self.estado.avanzar_reloj(costo)
 
    def anotar(self, objetivo, metodo, contexto):
        self.estado.historial.registrar_cambio(
            Cambio.de_operacion("deshacer", objetivo, metodo, contexto))
 
    # --- las acciones -------------------------------------------------
 
    def recoger(self, sala, posicion):
        self.accion("recoger", 25)
        contexto = self.inventario.recoger_desde_sala(
            sala, posicion, ficha(sala.objeto_en(posicion)))
        self.anotar(self.inventario, "deshacer_recogida", contexto)
 
    def soltar_actual(self, sala):
        self.accion("soltar", 25)
        contexto = self.inventario.soltar_en_sala(sala)
        self.anotar(self.inventario, "deshacer_soltar_en_sala", contexto)
 
    def recoger_pergamino(self, sala):
        self.accion("recoger pergamino", 25)
        self.inventario.recoger_pergamino_de(sala)       # sin anotar nada
 
    def soltar_pergamino(self, sala):
        self.accion("soltar pergamino", 25)
        self.inventario.soltar_pergamino_en(sala)        # sin anotar nada
 
    def usar_pergamino(self):
        return self.estado.usar_pergamino_retroceso()
 
 
# ----------------------------------------------------------------------
# La regla del §2.11 "en ambos sentidos"
# ----------------------------------------------------------------------
 
class TestExcepcionDelPergamino(unittest.TestCase):
    def test_uno_solo_no_alcanza_para_siempre(self):
        """Si deshacer devolviera el pergamino gastado, con uno se podría
        retroceder sin fin."""
        partida = Partida(pergaminos=1)
        sala = sala_con("itm_daga", "itm_escudo")
        partida.recoger(sala, 0)
        partida.recoger(sala, 0)
        self.assertTrue(partida.usar_pergamino())
        self.assertEqual(partida.inventario.cantidad_pergaminos(), 0)
        self.assertFalse(partida.usar_pergamino())      # ya no queda
        self.assertEqual(len(partida.inventario), 1)
 
    def test_recoger_un_pergamino_no_se_deshace(self):
        partida = Partida(pergaminos=1)
        sala = sala_con(PERGAMINO)
        partida.recoger_pergamino(sala)                  # ahora tiene 2
        partida.usar_pergamino()
        self.assertEqual(partida.estado.reloj, 0)        # la acción sí se deshizo...
        self.assertEqual(partida.inventario.cantidad_pergaminos(), 1)   # 2 - 1
        self.assertEqual(sala.cantidad_pergaminos(), 0)  # ...y no reaparece en el suelo
 
    def test_soltar_un_pergamino_no_se_deshace(self):
        partida = Partida(pergaminos=2)
        sala = sala_con()
        partida.soltar_pergamino(sala)                   # ahora tiene 1
        partida.usar_pergamino()
        self.assertEqual(partida.estado.reloj, 0)
        self.assertEqual(partida.inventario.cantidad_pergaminos(), 0)   # 1 - 1
        self.assertEqual(sala.cantidad_pergaminos(), 1)  # sigue en el suelo
 
    def test_sin_nada_que_deshacer_no_se_gasta(self):
        partida = Partida(pergaminos=1)
        self.assertFalse(partida.usar_pergamino())
        self.assertEqual(partida.inventario.cantidad_pergaminos(), 1)
 
 
# ----------------------------------------------------------------------
# La trampa: el pergamino no puede estar DENTRO de las estructuras con
# deshacer por posición/vecino (con la versión anterior, estas se caían).
# ----------------------------------------------------------------------
 
class TestLaTrampa(unittest.TestCase):
    def test_suelo_posiciones_no_se_corren(self):
        """Suelo [pergamino, daga]. Se recoge la daga (anotado: posición 1)
        y luego el pergamino (no se deshace). Si el pergamino estuviera en
        el Vector, la daga tendría que volver a la posición 1 de un Vector
        vacío -> IndexError."""
        partida = Partida(pergaminos=1)
        sala = sala_con(PERGAMINO, "itm_daga")
        partida.recoger(sala, 0)                         # la daga
        partida.recoger_pergamino(sala)
        partida.usar_pergamino()
        partida.usar_pergamino()
        self.assertEqual(suelo(sala), ["itm_daga"])
        self.assertEqual(len(partida.inventario), 0)
        self.assertEqual(partida.inventario.cantidad_pergaminos(), 0)
        self.assertEqual(sala.cantidad_pergaminos(), 0)
        self.assertEqual(partida.estado.reloj, 0)
 
    def test_inventario_vecinos_no_se_pierden(self):
        """Inventario [A, B] y pergaminos. Se suelta B (anotado: "va después
        de A") y luego un pergamino (no se deshace). Si el pergamino fuera
        un nodo entre A y B, B tendría que volver "después del pergamino",
        que ya no está en la lista -> se cae."""
        partida = Partida(pergaminos=3)
        for nombre in ("A", "B"):
            partida.inventario.recoger(ficha(nombre))
        partida.inventario.avanzar()                     # viendo B
        sala = sala_con()
        partida.soltar_actual(sala)
        partida.soltar_pergamino(sala)
        partida.usar_pergamino()
        partida.usar_pergamino()
        self.assertEqual([o["id"] for o in partida.inventario.orden_real()], ["A", "B"])
        self.assertEqual(suelo(sala), [])
        self.assertEqual(sala.cantidad_pergaminos(), 1)  # el soltado se queda allí
        self.assertEqual(partida.inventario.cantidad_pergaminos(), 0)   # 2 - 1 - 1
 
 
# ----------------------------------------------------------------------
# Las piezas por separado
# ----------------------------------------------------------------------
 
class TestInventarioPergaminos(unittest.TestCase):
    def test_ocupan_lugar(self):
        """§2.7: cada objeto ocupa una posición, también un pergamino."""
        inventario = Inventario(2)
        inventario.recoger(ficha("A"))
        inventario.fijar_pergaminos(1)
        self.assertTrue(inventario.esta_lleno())
        self.assertEqual(inventario.espacio_disponible(), 0)
        self.assertFalse(inventario.recoger(ficha("B")))
        self.assertFalse(inventario.recoger_pergamino_de(sala_con(PERGAMINO)))
 
    def test_no_entran_como_objeto_comun(self):
        with self.assertRaises(ValueError):
            Inventario(5).recoger(ficha(PERGAMINO, "pergamino_retroceso"))
 
    def test_no_se_ven_en_la_lista(self):
        inventario = Inventario(5)
        inventario.fijar_pergaminos(2)
        self.assertEqual(len(inventario), 0)
        self.assertEqual(inventario.orden_real(), [])
        self.assertIsNone(inventario.actual())
 
    def test_fijar_valida(self):
        inventario = Inventario(2)
        with self.assertRaises(ValueError):
            inventario.fijar_pergaminos(3)
        with self.assertRaises(ValueError):
            inventario.fijar_pergaminos(-1)
 
    def test_sin_pergaminos(self):
        inventario = Inventario(2)
        self.assertFalse(inventario.consumir_pergamino())
        self.assertFalse(inventario.soltar_pergamino_en(sala_con()))
 
 
class TestSalaPergaminos(unittest.TestCase):
    def test_apartar_conserva_el_orden_de_lo_demas(self):
        sala = Sala(1, "x", None)
        sala.asignar_contenido({"sala": 1, "objetos": [
            "itm_daga", PERGAMINO, "itm_antorcha", PERGAMINO, "itm_llave"]})
        sala.apartar_pergaminos(es_pergamino)
        self.assertEqual(suelo(sala), ["itm_daga", "itm_antorcha", "itm_llave"])
        self.assertEqual(sala.cantidad_pergaminos(), 2)
 
    def test_apartar_dos_veces_no_cuenta_doble(self):
        sala = sala_con(PERGAMINO)
        sala.apartar_pergaminos(es_pergamino)
        self.assertEqual(sala.cantidad_pergaminos(), 1)
 
    def test_apartar_sin_contenido_falla(self):
        with self.assertRaises(ValueError):
            Sala(1, "x", None).apartar_pergaminos(es_pergamino)
 
    def test_quitar_sin_pergaminos_falla(self):
        with self.assertRaises(ValueError):
            sala_con().quitar_pergamino()
 
 
class TestEstadoConElJugador(unittest.TestCase):
    def test_usa_el_inventario_del_jugador(self):
        jugador = Jugador("Héroe", vida_max=30, ataque=5, defensa=2,
                          velocidad=100, inventario_max=5)
        estado = EstadoJuego(jugador.inventario)
        jugador.inventario.fijar_pergaminos(2)
        self.assertEqual(estado.pergaminos_retroceso, 2)
        estado.historial.registrar(RegistroAccion("esperar"))
        estado.avanzar_reloj(100)
        self.assertTrue(estado.usar_pergamino_retroceso())
        self.assertEqual(jugador.inventario.cantidad_pergaminos(), 1)
 
    def test_sin_inventario_sigue_funcionando(self):
        """Así lo usan las pruebas viejas del 4.6 (main y revisiones)."""
        estado = EstadoJuego()
        estado.pergaminos_retroceso = 2
        self.assertEqual(estado.inventario.cantidad_pergaminos(), 2)
 
 
if __name__ == "__main__":
    unittest.main()
 