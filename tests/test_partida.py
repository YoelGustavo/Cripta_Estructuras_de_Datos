"""Pruebas de la Partida (Fase 4), todas en un solo archivo, por pasos:

    4.1  inicio, reloj, turnos y pergamino
    4.2  moverse entre salas
    4.3  combate
    4.4  comportamientos de los enemigos
    4.5  objetos (recoger, soltar, equipar, pergaminos) y abrir puertas
    4.6  usar objetos, efectos temporales y trampas
    4.7  rastro con cada acción, victoria y puntaje

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_partida
o todas las pruebas del proyecto:
    python -m unittest -v

Salvo en la sección 4.4, los enemigos de estas pruebas son "guardián":
esperan si el jugador no está en su sala.
"""

import random
import unittest

from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida, TURNO_JUGADOR


SEMILLA = 7


def ficha_enemigo(id_tipo, velocidad, defensa=1, suelta=(), comportamiento="guardián"):
    return {"id": id_tipo, "clase": "enemigo", "nombre": id_tipo, "vida_max": 12,
            "ataque": 5, "defensa": defensa, "velocidad": velocidad,
            "comportamiento": comportamiento, "suelta": list(suelta)}


CATALOGO = {
    "ent_rata": ficha_enemigo("ent_rata", 150, suelta=["itm_pocion_menor"]),   # §2.13
    "ent_lenta": ficha_enemigo("ent_lenta", 100),
    "ent_rapida": ficha_enemigo("ent_rapida", 300),
    "ent_acorazada": ficha_enemigo("ent_acorazada", 100, defensa=50),
    "ent_mago": ficha_enemigo("ent_mago", 100, suelta=["itm_pergamino_retroceso"]),
    "ent_tortuga": ficha_enemigo("ent_tortuga", 50),            # intervalo 200
    "ent_errante": ficha_enemigo("ent_errante", 100, comportamiento="errante"),
    "ent_rastreador": ficha_enemigo("ent_rastreador", 100, comportamiento="rastreador"),
    "ent_rastreador_400": ficha_enemigo("ent_rastreador_400", 25, comportamiento="rastreador"),
    "ent_rastreador_384": ficha_enemigo("ent_rastreador_384", 26, comportamiento="rastreador"),
    # Lentos (velocidad 50): su primer turno es en t=200, no en t=100.
    "ent_rastreador_294": ficha_enemigo("ent_rastreador_294", 34, comportamiento="rastreador"),
    "ent_errante_lento": ficha_enemigo("ent_errante_lento", 50, comportamiento="errante"),
    "ent_rastreador_lento": ficha_enemigo("ent_rastreador_lento", 50, comportamiento="rastreador"),
    "itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 2,
                 "valor": 15, "ataque_bonus": 3},
    "itm_pocion_menor": {"id": "itm_pocion_menor", "clase": "pocion", "nombre": "Poción",
                         "peso": 1, "valor": 10, "cura": 8},
    "itm_pergamino_retroceso": {"id": "itm_pergamino_retroceso", "clase": "pergamino_retroceso",
                                "nombre": "Pergamino", "peso": 1, "valor": 30},
    "itm_llave_bronce": {"id": "itm_llave_bronce", "clase": "llave", "nombre": "Llave de bronce",
                         "peso": 1, "valor": 5, "abre": [3]},
    "itm_cota": {"id": "itm_cota", "clase": "armadura", "nombre": "Cota", "peso": 5,
                 "valor": 20, "defensa_bonus": 4},
    # 4.6
    "itm_pocion_rapidez": {"id": "itm_pocion_rapidez", "clase": "pocion", "nombre": "Rapidez",
                           "peso": 1, "valor": 20, "modificador_velocidad": 100, "duracion": 300},
    "itm_pocion_lentitud": {"id": "itm_pocion_lentitud", "clase": "pocion", "nombre": "Lentitud",
                            "peso": 1, "valor": 1, "modificador_velocidad": -50, "duracion": 200},
    "itm_pocion_paralisis": {"id": "itm_pocion_paralisis", "clase": "pocion", "nombre": "Parálisis",
                             "peso": 1, "valor": 1, "modificador_velocidad": -500, "duracion": 200},
    "itm_antidoto": {"id": "itm_antidoto", "clase": "antidoto", "nombre": "Antídoto",
                     "peso": 1, "valor": 15},
    "itm_antorcha": {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha",
                     "peso": 1, "valor": 5, "duracion": 500},
    "trp_dardos": {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 4,
                   "rearme": 300},
    "trp_lanzas": {"id": "trp_lanzas", "clase": "trampa", "nombre": "Lanzas", "daño": 10},
    "trp_rapida": {"id": "trp_rapida", "clase": "trampa", "nombre": "Aguja", "daño": 1,
                   "rearme": 150},
    "trp_espinas": {"id": "trp_espinas", "clase": "trampa", "nombre": "Espinas", "daño": 0,
                    "veneno": 2, "rearme": 1000},
    "ent_troll": dict(ficha_enemigo("ent_troll", 50), regeneracion=3),
}


def datos_enemigos(enemigos):
    """(instancia, tipo) o (instancia, tipo, vida_inicial)."""
    return [{"instancia": e[0], "tipo": e[1], **({"vida": e[2]} if len(e) > 2 else {})}
            for e in enemigos]


def nuevo_jugador(pergaminos=0, inventario_max=10):
    jugador = Jugador("Héroe", vida_max=30, ataque=6, defensa=2,
                      velocidad=100, inventario_max=inventario_max)
    jugador.inventario.fijar_pergaminos(pergaminos)
    return jugador


def partida_de_dos_salas(enemigos_sala_1=(), enemigos_sala_2=(), pergaminos=0, cargar=True):
    """Sala 1 (inicial) <-> sala 2. SIN iniciar."""
    mapa = Mapa()
    mapa.cargar_desde_json([
        {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {"S": {"sala": 1}}},
    ])
    if cargar:
        mapa.asignar_contenidos([
            {"sala": 1, "enemigos": datos_enemigos(enemigos_sala_1)},
            {"sala": 2, "enemigos": datos_enemigos(enemigos_sala_2)},
        ])
    return Partida(mapa, nuevo_jugador(pergaminos), 1, CATALOGO.get, semilla=SEMILLA)


def partida_con_puertas(pergaminos=0, enemigos_sala_2=(("e-1", "ent_rata"),)):
    """YA iniciada. El mapa:

                [4] (sin contenido cargado)
                 |
                [2] rata e-1 + un pergamino en el suelo
                 |
        [5] -- [1] inicial: daga + pergamino -- [3]
         (cerrada)                         (cerrada con llave)
    """
    mapa = Mapa()
    mapa.cargar_desde_json([
        {"id": 1, "nombre": "Entrada", "salidas": {
            "N": {"sala": 2},
            "E": {"sala": 3, "cerrada": True, "llave": "itm_llave"},
            "O": {"sala": 5, "cerrada": True}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {"S": {"sala": 1}, "N": {"sala": 4}}},
        {"id": 3, "nombre": "Bodega", "salidas": {"O": {"sala": 1}}},
        {"id": 4, "nombre": "Torre", "salidas": {"S": {"sala": 2}}},
        {"id": 5, "nombre": "Celda", "salidas": {"E": {"sala": 1}}},
    ])
    mapa.asignar_contenidos([
        {"sala": 1, "objetos": ["itm_daga", "itm_pergamino_retroceso"]},
        {"sala": 2, "objetos": ["itm_pergamino_retroceso"],
         "enemigos": datos_enemigos(enemigos_sala_2)},
        {"sala": 3}, {"sala": 5},
    ])                                      # la sala 4 queda SIN contenido
    partida = Partida(mapa, nuevo_jugador(pergaminos), 1, CATALOGO.get, semilla=SEMILLA)
    partida.iniciar()
    return partida


def partida_cruce(enemigos_sala_2=(), pergaminos=0):
    """YA iniciada. El jugador EMPIEZA en la sala 2, con los enemigos (así
    se activan en t=0). Todas las salidas abiertas:

                [6]      (la 6 NO es vecina de la 2)
                 |
                [4]
                 |
          [5] - [2] - [3]
                 |
                [1]
    """
    mapa = Mapa()
    mapa.cargar_desde_json([
        {"id": 1, "nombre": "Sur", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Cruce", "salidas": {
            "N": {"sala": 4}, "S": {"sala": 1}, "E": {"sala": 3}, "O": {"sala": 5}}},
        {"id": 3, "nombre": "Este", "salidas": {"O": {"sala": 2}}},
        {"id": 4, "nombre": "Norte", "salidas": {"S": {"sala": 2}, "N": {"sala": 6}}},
        {"id": 5, "nombre": "Oeste", "salidas": {"E": {"sala": 2}}},
        {"id": 6, "nombre": "Lejos", "salidas": {"S": {"sala": 4}}},
    ])
    mapa.asignar_contenidos([
        {"sala": 1}, {"sala": 3}, {"sala": 4}, {"sala": 5}, {"sala": 6},
        {"sala": 2, "enemigos": datos_enemigos(enemigos_sala_2)},
    ])
    partida = Partida(mapa, nuevo_jugador(pergaminos), 2, CATALOGO.get, semilla=SEMILLA)
    partida.iniciar()
    return partida


def partida_objetos(pergaminos=0, inventario_max=10):
    """YA iniciada. El jugador empieza en la sala 1. En el suelo: daga,
    llave de bronce, poción y un pergamino (que pasa a su contador).

                         [2]
                          |  N: cerrada, sin cerradura
        [4] ------------ [1] ------------ [3]
     O: cerrada con          E: cerrada con itm_llave_bronce
     itm_llave_negra            y cierre automático a los 500
    """
    mapa = Mapa()
    mapa.cargar_desde_json([
        {"id": 1, "nombre": "Bodega", "salidas": {
            "N": {"sala": 2, "cerrada": True},
            "E": {"sala": 3, "cerrada": True, "llave": "itm_llave_bronce",
                  "cierre_automatico": 500},
            "O": {"sala": 4, "cerrada": True, "llave": "itm_llave_negra"}}},
        {"id": 2, "nombre": "Norte", "salidas": {"S": {"sala": 1}}},
        {"id": 3, "nombre": "Este", "salidas": {"O": {"sala": 1}}},
        {"id": 4, "nombre": "Oeste", "salidas": {"E": {"sala": 1}}},
    ])
    mapa.asignar_contenidos([
        {"sala": 1, "objetos": ["itm_daga", "itm_llave_bronce", "itm_pocion_menor",
                                "itm_pergamino_retroceso"]},
        {"sala": 2}, {"sala": 3}, {"sala": 4},
    ])
    partida = Partida(mapa, nuevo_jugador(pergaminos, inventario_max), 1, CATALOGO.get,
                      semilla=SEMILLA)
    partida.iniciar()
    return partida


def partida_efectos(inventario=(), trampas_sala_1=(), trampas_sala_2=(), enemigos_sala_1=(),
                    enemigos_sala_2=(), pergaminos=0, vida=None):
    """YA iniciada. Sala 1 (inicial) <-> sala 2 (al norte). 'inventario':
    ids del catálogo que el jugador ya tiene al empezar."""
    mapa = Mapa()
    mapa.cargar_desde_json([
        {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}}},
        {"id": 2, "nombre": "Pasillo", "salidas": {"S": {"sala": 1}}},
    ])
    mapa.asignar_contenidos([
        {"sala": 1, "enemigos": datos_enemigos(enemigos_sala_1),
         "trampas": [{"instancia": f"t-1{i}", "tipo": t} for i, t in enumerate(trampas_sala_1)]},
        {"sala": 2, "enemigos": datos_enemigos(enemigos_sala_2),
         "trampas": [{"instancia": f"t-2{i}", "tipo": t} for i, t in enumerate(trampas_sala_2)]},
    ])
    jugador = nuevo_jugador(pergaminos)
    for id_objeto in inventario:
        jugador.inventario.recoger(CATALOGO[id_objeto])
    if vida is not None:
        jugador.vida = vida
    partida = Partida(mapa, jugador, 1, CATALOGO.get, semilla=SEMILLA)
    partida.iniciar()
    return partida


def esperar_hasta(partida, reloj):
    while partida.reloj < reloj:
        partida.esperar()


def ids_suelo(partida):
    return [partida.sala_actual().objeto_en(i) for i in range(partida.sala_actual().cantidad_objetos())]


def ids_inventario(partida):
    return [objeto["id"] for objeto in partida.jugador.inventario.orden_real()]


def donde_esta(partida, un_enemigo):
    """Revisa que el enemigo esté en la sala que dice (en su Vector) y la devuelve."""
    sala_del_enemigo = sala(partida, un_enemigo.sala_actual)
    for i in range(sala_del_enemigo.cantidad_enemigos()):
        if sala_del_enemigo.enemigo_en(i) is un_enemigo:
            return un_enemigo.sala_actual
    raise AssertionError(f"{un_enemigo.id_instancia} dice estar en {un_enemigo.sala_actual} pero no está ahí")


def sala(partida, id_sala):
    return partida.mapa.obtener_sala(id_sala)


def enemigo(partida, id_sala, posicion=0):
    return sala(partida, id_sala).enemigo_en(posicion)


def proximo(actor):
    return actor.evento_siguiente.tiempo


def dados(cantidad):
    """Los primeros 'cantidad' resultados de randint(0, 4) con la semilla
    de las pruebas: así se sabe el daño exacto que debe salir."""
    azar = random.Random(SEMILLA)
    return [azar.randint(0, 4) for _ in range(cantidad)]


# ======================================================================
# 4.1  INICIO (§2.4)
# ======================================================================

class TestInicio(unittest.TestCase):
    def test_estado_inicial(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(partida.jugador.sala_actual, 1)
        self.assertEqual(sala(partida, 1).obtener_rastro(), 0)          # §2.9

    def test_el_jugador_decide_primero_en_0(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        self.assertEqual(partida.jugador.evento_siguiente.tipo, TURNO_JUGADOR)
        self.assertEqual(proximo(partida.jugador), 0)
        self.assertEqual(len(partida.agenda), 1)          # solo queda la rata

    def test_rata_de_la_sala_inicial_se_activa_en_66(self):
        """§2.4: velocidad 150 activada en 0 -> tiempo_siguiente = 66."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        self.assertTrue(enemigo(partida, 1).esta_activo())
        self.assertEqual(proximo(enemigo(partida, 1)), 66)

    def test_los_de_otras_salas_siguen_dormidos(self):
        partida = partida_de_dos_salas(enemigos_sala_2=[("e-9", "ent_rata")])
        partida.iniciar()
        self.assertFalse(enemigo(partida, 2).esta_activo())
        self.assertEqual(len(partida.agenda), 0)

    def test_activacion_en_orden_de_id(self):
        """§2.4: si se activan en el mismo instante, en orden de id."""
        partida = partida_de_dos_salas([("e-202", "ent_rata"), ("e-201", "ent_rata")])
        partida.iniciar()
        e202, e201 = enemigo(partida, 1, 0), enemigo(partida, 1, 1)
        self.assertEqual(proximo(e201), proximo(e202))
        self.assertLess(e201.evento_siguiente.secuencia, e202.evento_siguiente.secuencia)

    def test_sin_contenido_no_inicia(self):
        with self.assertRaises(RuntimeError):
            partida_de_dos_salas(cargar=False).iniciar()

    def test_no_se_inicia_dos_veces(self):
        partida = partida_de_dos_salas()
        partida.iniciar()
        with self.assertRaises(RuntimeError):
            partida.iniciar()

    def test_no_se_actua_sin_iniciar(self):
        with self.assertRaises(RuntimeError):
            partida_de_dos_salas().esperar()


# ======================================================================
# 4.1  EL RELOJ Y LOS TURNOS (§2.3)
# ======================================================================

class TestTurnos(unittest.TestCase):
    def test_esperar_cuesta_100(self):
        partida = partida_de_dos_salas()
        partida.iniciar()
        partida.esperar()
        self.assertEqual(partida.reloj, 100)
        partida.esperar()
        self.assertEqual(partida.reloj, 200)

    def test_la_rata_actua_entre_decisiones(self):
        """§2.13: la rata (150) actúa en 66 y queda para 132."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        partida.esperar()
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(proximo(enemigo(partida, 1)), 132)

    def test_varias_decisiones(self):
        """Rata: 66, 132, 198, 264 -> la próxima es 330."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        for _ in range(3):
            partida.esperar()
        self.assertEqual(partida.reloj, 300)
        self.assertEqual(proximo(enemigo(partida, 1)), 330)

    def test_un_enemigo_rapido_actua_varias_veces(self):
        """§2.3: velocidad 300 -> actúa en 33, 66 y 99; la próxima en 132."""
        partida = partida_de_dos_salas([("e-1", "ent_rapida")])
        partida.iniciar()
        partida.esperar()
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(proximo(enemigo(partida, 1)), 132)

    def test_empate_lo_decide_la_secuencia(self):
        """Enemigo (100) y jugador, los dos en t=100: el enemigo se programó
        antes, así que actúa primero."""
        partida = partida_de_dos_salas([("e-1", "ent_lenta")])
        partida.iniciar()
        partida.esperar()
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(proximo(enemigo(partida, 1)), 200)            # ya actuó en 100

    def test_la_semilla_fija_el_azar(self):
        a, b = partida_de_dos_salas(), partida_de_dos_salas()
        self.assertEqual([a.azar.randint(0, 4) for _ in range(20)],
                         [b.azar.randint(0, 4) for _ in range(20)])


# ======================================================================
# 4.1  EL PERGAMINO SOBRE TURNOS REALES (§2.11)
# ======================================================================

class TestPergamino(unittest.TestCase):
    def test_deshace_reloj_y_agenda(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")], pergaminos=1)
        partida.iniciar()
        partida.esperar()                                  # reloj 100, rata 132
        partida.esperar()                                  # reloj 200, rata 264
        self.assertTrue(partida.usar_pergamino())
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(proximo(enemigo(partida, 1)), 132)
        self.assertEqual(proximo(partida.jugador), 100)
        self.assertEqual(len(partida.agenda), 1)           # solo la rata

    def test_despues_de_deshacer_todo_sigue_igual(self):
        """Repetir la acción deshecha da exactamente lo mismo (también la vida)."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")], pergaminos=1)
        partida.iniciar()
        partida.esperar()
        partida.esperar()
        vida_antes = partida.jugador.vida
        partida.usar_pergamino()
        partida.esperar()
        self.assertEqual(partida.reloj, 200)
        self.assertEqual(proximo(enemigo(partida, 1)), 264)
        self.assertEqual(partida.jugador.vida, vida_antes)

    def test_deshacer_la_primera_accion(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")], pergaminos=1)
        partida.iniciar()
        partida.esperar()
        partida.usar_pergamino()
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(proximo(enemigo(partida, 1)), 66)
        self.assertEqual(len(partida.agenda), 1)
        self.assertEqual(partida.jugador.vida, 30)
        partida.esperar()
        self.assertEqual((partida.reloj, proximo(enemigo(partida, 1))), (100, 132))

    def test_sin_acciones_o_sin_pergaminos(self):
        partida = partida_de_dos_salas(pergaminos=1)
        partida.iniciar()
        self.assertFalse(partida.usar_pergamino())         # nada que deshacer
        partida.esperar()
        partida.jugador.inventario.fijar_pergaminos(0)
        self.assertFalse(partida.usar_pergamino())         # no tiene
        self.assertEqual(partida.reloj, 100)

    def test_maximo_5_acciones_atras(self):
        """§4.6: el historial guarda como máximo 5 acciones del jugador."""
        partida = partida_de_dos_salas(pergaminos=6)
        partida.iniciar()
        for _ in range(6):
            partida.esperar()                              # reloj 600
        for _ in range(5):
            self.assertTrue(partida.usar_pergamino())
        self.assertEqual(partida.reloj, 100)
        self.assertFalse(partida.usar_pergamino())
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)


# ======================================================================
# 4.2  MOVERSE (§2.5, §2.9)
# ======================================================================

class TestMover(unittest.TestCase):
    def test_mover_cuesta_100(self):
        partida = partida_con_puertas()
        llegada = partida.mover("N")
        self.assertIs(llegada, sala(partida, 2))
        self.assertEqual(partida.jugador.sala_actual, 2)
        self.assertEqual(partida.reloj, 100)

    def test_rastro_en_la_sala_destino(self):
        """§2.9: la sala destino recibe el tiempo del instante del movimiento."""
        partida = partida_con_puertas()
        partida.mover("N")                          # en t=0
        partida.mover("S")                          # en t=100
        self.assertEqual(sala(partida, 2).obtener_rastro(), 0)
        self.assertEqual(sala(partida, 1).obtener_rastro(), 100)

    def test_destino_de(self):
        partida = partida_con_puertas()
        self.assertEqual(partida.destino_de("N"), 2)
        self.assertEqual(partida.destino_de("E"), 3)     # existe, aunque esté cerrada
        self.assertIsNone(partida.destino_de("S"))


class TestNoSePuedeMover(unittest.TestCase):
    """Si no se puede, no pasa NADA: ni tiempo, ni historial."""

    def revisar_que_no_paso_nada(self, partida):
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(partida.jugador.sala_actual, 1)
        self.assertEqual(len(partida.estado.historial), 0)

    def test_sin_salida(self):
        partida = partida_con_puertas()
        with self.assertRaises(AccionInvalida):
            partida.mover("S")
        self.revisar_que_no_paso_nada(partida)

    def test_direccion_que_no_existe(self):
        partida = partida_con_puertas()
        with self.assertRaises(AccionInvalida):
            partida.mover("X")
        self.revisar_que_no_paso_nada(partida)

    def test_puerta_cerrada(self):
        partida = partida_con_puertas()
        with self.assertRaises(AccionInvalida):
            partida.mover("O")
        self.revisar_que_no_paso_nada(partida)

    def test_puerta_con_llave(self):
        partida = partida_con_puertas()
        with self.assertRaises(AccionInvalida) as error:
            partida.mover("E")
        self.assertIn("llave", str(error.exception))
        self.revisar_que_no_paso_nada(partida)

    def test_sala_sin_contenido(self):
        """§2.4: no se entra a una sala cuyo contenido no ha llegado."""
        partida = partida_con_puertas()
        partida.mover("N")
        with self.assertRaises(RuntimeError):
            partida.mover("N")                      # a la 4
        self.assertEqual(partida.jugador.sala_actual, 2)
        self.assertEqual(partida.reloj, 100)


class TestActivarAlEntrar(unittest.TestCase):
    def test_la_rata_duerme_hasta_que_entra_el_jugador(self):
        partida = partida_con_puertas()
        self.assertFalse(enemigo(partida, 2).esta_activo())
        partida.mover("N")
        self.assertTrue(enemigo(partida, 2).esta_activo())

    def test_secuencia_del_2_13(self):
        """t=0 se mueve al norte y activa la rata (-> 66). En 66 la rata
        actúa y queda para 132; el jugador vuelve en 100."""
        partida = partida_con_puertas()
        partida.mover("N")
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(proximo(enemigo(partida, 2)), 132)

    def test_volver_a_entrar_no_reinicia_sus_tiempos(self):
        """§2.13: entrar a una sala no reinicia los tiempos de los enemigos."""
        partida = partida_con_puertas()
        partida.mover("N")                          # t=0: rata 66, 132
        partida.mover("S")                          # t=100: rata 198
        partida.mover("N")                          # t=200: rata 264 (no se reactiva)
        self.assertEqual(partida.reloj, 300)
        self.assertEqual(proximo(enemigo(partida, 2)), 330)

    def test_dos_al_entrar_en_orden_de_id(self):
        partida = partida_con_puertas(enemigos_sala_2=(("e-9", "ent_rata"), ("e-3", "ent_rata")))
        partida.mover("N")
        e9, e3 = enemigo(partida, 2, 0), enemigo(partida, 2, 1)
        self.assertEqual(proximo(e9), proximo(e3))
        self.assertLess(e3.evento_siguiente.secuencia, e9.evento_siguiente.secuencia)


class TestPergaminosDelSuelo(unittest.TestCase):
    def test_se_apartan_al_iniciar(self):
        partida = partida_con_puertas()
        self.assertEqual(sala(partida, 1).cantidad_objetos(), 1)      # solo la daga
        self.assertEqual(sala(partida, 1).cantidad_pergaminos(), 1)

    def test_se_apartan_al_entrar(self):
        partida = partida_con_puertas()
        self.assertEqual(sala(partida, 2).cantidad_objetos(), 1)      # aún sin apartar
        partida.mover("N")
        self.assertEqual(sala(partida, 2).cantidad_objetos(), 0)
        self.assertEqual(sala(partida, 2).cantidad_pergaminos(), 1)


class TestDeshacerMover(unittest.TestCase):
    def test_vuelve_todo_atras(self):
        partida = partida_con_puertas(pergaminos=1)
        partida.mover("N")
        self.assertTrue(partida.usar_pergamino())
        self.assertEqual(partida.jugador.sala_actual, 1)
        self.assertEqual(partida.reloj, 0)
        self.assertIsNone(sala(partida, 2).obtener_rastro())         # nunca estuvo
        self.assertFalse(enemigo(partida, 2).esta_activo())          # vuelve a dormir
        self.assertEqual(len(partida.agenda), 0)                     # su turno se canceló
        self.assertEqual(partida.jugador.vida, 30)                   # y su ataque en 66

    def test_el_enemigo_vuelve_a_dormir_igual(self):
        """Al deshacer la activación, el enemigo no se queda con la vida ni
        la velocidad de su ficha: vuelve EXACTAMENTE a como estaba dormido
        (lo encontró una partida larga al azar)."""
        partida = partida_con_puertas(pergaminos=1)
        rata = enemigo(partida, 2)
        partida.mover("N")
        partida.usar_pergamino()
        self.assertEqual((rata.vida, rata.vida_max, rata.velocidad, rata.ataque,
                          rata.comportamiento, rata.nombre), (0, 0, 0, 0, None, "ent_rata"))

    def test_rehacer_da_lo_mismo(self):
        partida = partida_con_puertas(pergaminos=1)
        partida.mover("N")
        vida = partida.jugador.vida
        partida.usar_pergamino()
        partida.mover("N")
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(proximo(enemigo(partida, 2)), 132)
        self.assertEqual(len(partida.agenda), 1)
        self.assertEqual(partida.jugador.vida, vida)

    def test_deshacer_el_segundo_movimiento(self):
        partida = partida_con_puertas(pergaminos=1)
        partida.mover("N")                          # t=0
        partida.mover("S")                          # t=100: rastro de la 1 pasa a 100
        partida.usar_pergamino()
        self.assertEqual(partida.jugador.sala_actual, 2)
        self.assertEqual(partida.reloj, 100)
        self.assertEqual(sala(partida, 1).obtener_rastro(), 0)       # vuelve a 0
        self.assertTrue(enemigo(partida, 2).esta_activo())           # esa activación no se deshizo
        self.assertEqual(proximo(enemigo(partida, 2)), 132)


# ======================================================================
# 4.3  EL JUGADOR ATACA (§2.6)
# ======================================================================

class TestAtacar(unittest.TestCase):
    def test_danio_con_la_formula(self):
        """daño = max(1, ataque + randint(0,4) - defensa) = 6 + dado - 1."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        rata = enemigo(partida, 1)
        danio = partida.atacar(rata)
        self.assertEqual(danio, 6 + dados(1)[0] - 1)
        self.assertEqual(rata.vida, 12 - danio)

    def test_atacar_cuesta_100(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        partida.atacar(enemigo(partida, 1))
        self.assertEqual(partida.reloj, 100)

    def test_el_dado_va_de_0_a_4(self):
        """randint(0, 4) incluye los dos extremos: 0, 1, 2, 3 o 4 (§2.6)."""
        partida = partida_de_dos_salas()
        danios = [partida._danio(6, 1) for _ in range(300)]
        self.assertEqual(danios, [6 + d - 1 for d in dados(300)])
        self.assertEqual(min(danios), 5)
        self.assertEqual(max(danios), 9)

    def test_danio_minimo_1(self):
        partida = partida_de_dos_salas([("e-1", "ent_acorazada")])    # defensa 50
        partida.iniciar()
        self.assertEqual(partida.atacar(enemigo(partida, 1)), 1)

    def test_el_arma_equipada_suma(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.jugador.inventario.recoger(CATALOGO["itm_daga"])
        partida.jugador.inventario.equipar_actual_con_contexto()
        partida.iniciar()
        self.assertEqual(partida.atacar(enemigo(partida, 1)), 6 + 3 + dados(1)[0] - 1)

    def test_escoger_a_cual(self):
        """§2.6: con varios en la sala, el jugador escoge."""
        partida = partida_de_dos_salas([("e-1", "ent_rata"), ("e-2", "ent_rata")])
        partida.iniciar()
        presentes = partida.enemigos_presentes()
        self.assertEqual(len(presentes), 2)
        partida.atacar(presentes.obtener(1))
        self.assertEqual(enemigo(partida, 1, 0).vida, 12)
        self.assertLess(enemigo(partida, 1, 1).vida, 12)

    def test_no_a_uno_de_otra_sala(self):
        partida = partida_con_puertas()
        partida.mover("N")                          # activa la rata de la 2
        partida.mover("S")                          # y se va
        reloj = partida.reloj
        with self.assertRaises(AccionInvalida):
            partida.atacar(enemigo(partida, 2))
        self.assertEqual(partida.reloj, reloj)

    def test_no_a_uno_dormido(self):
        partida = partida_con_puertas()
        with self.assertRaises(AccionInvalida):
            partida.atacar(enemigo(partida, 2))
        self.assertEqual(len(partida.estado.historial), 0)


class TestElEnemigoAtaca(unittest.TestCase):
    def test_ataca_si_comparte_sala(self):
        """§2.8: en su turno, si está con el jugador, ataca: 5 + dado - 2."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        partida.esperar()                           # la rata actúa en 66
        self.assertEqual(partida.jugador.vida, 30 - (5 + dados(1)[0] - 2))

    def test_no_ataca_desde_otra_sala(self):
        partida = partida_con_puertas()
        partida.mover("N")                          # en 66 la rata lo ataca
        partida.mover("S")                          # en 132 y 198 ya no está
        self.assertEqual(partida.reloj, 200)
        self.assertEqual(partida.jugador.vida, 30 - (5 + dados(1)[0] - 2))

    def test_la_armadura_resta(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        cota = {"id": "itm_cota", "clase": "armadura", "nombre": "Cota", "peso": 5,
                "valor": 20, "defensa_bonus": 4}
        partida.jugador.inventario.recoger(cota)
        partida.jugador.inventario.equipar_actual_con_contexto()
        partida.iniciar()
        partida.esperar()
        self.assertEqual(partida.jugador.vida, 30 - max(1, 5 + dados(1)[0] - 6))


# ======================================================================
# 4.3  MUERTE Y DERROTA
# ======================================================================

class TestMuerteDeUnEnemigo(unittest.TestCase):
    def matar_rata(self, pergaminos=0):
        # Vida 3: cualquier golpe del jugador (mínimo 5) la mata.
        partida = partida_de_dos_salas([("e-1", "ent_rata", 3)], pergaminos=pergaminos)
        partida.iniciar()
        rata = enemigo(partida, 1)
        partida.atacar(rata)
        return partida, rata

    def test_muere_y_sale_de_la_sala(self):
        partida, rata = self.matar_rata()
        self.assertFalse(rata.esta_vivo())
        self.assertEqual(sala(partida, 1).cantidad_enemigos(), 0)
        self.assertEqual(len(partida.enemigos_presentes()), 0)
        self.assertEqual(partida.enemigos_derrotados, 1)

    def test_deja_de_actuar(self):
        """§2.6: muere inmediatamente y deja de ejecutar eventos futuros."""
        partida, rata = self.matar_rata()
        self.assertEqual(len(partida.agenda), 0)
        partida.esperar()
        partida.esperar()
        self.assertEqual(partida.jugador.vida, 30)

    def test_su_turno_se_cancela_al_morir(self):
        """Una tortuga (intervalo 200) muere en t=0; su turno de t=200 ya
        no debe quedar pendiente en la agenda."""
        partida = partida_de_dos_salas([("e-1", "ent_tortuga", 3)], pergaminos=1)
        partida.iniciar()
        tortuga = enemigo(partida, 1)
        partida.atacar(tortuga)
        self.assertEqual(len(partida.agenda), 0)
        partida.usar_pergamino()
        self.assertEqual(len(partida.agenda), 1)
        self.assertEqual(proximo(tortuga), 200)

    def test_suelta_sus_objetos(self):
        partida, rata = self.matar_rata()
        self.assertEqual(sala(partida, 1).objeto_en(0), "itm_pocion_menor")

    def test_un_pergamino_soltado_va_al_contador(self):
        partida = partida_de_dos_salas([("e-1", "ent_mago", 1)])
        partida.iniciar()
        partida.atacar(enemigo(partida, 1))
        self.assertEqual(sala(partida, 1).cantidad_objetos(), 0)
        self.assertEqual(sala(partida, 1).cantidad_pergaminos(), 1)

    def test_no_se_ataca_a_un_muerto(self):
        partida, rata = self.matar_rata()
        with self.assertRaises(AccionInvalida):
            partida.atacar(rata)


class TestDerrota(unittest.TestCase):
    def morir(self, pergaminos=0):
        partida = partida_de_dos_salas([("e-1", "ent_rata")], pergaminos=pergaminos)
        partida.jugador.vida = 1
        partida.iniciar()
        partida.esperar()                           # la rata ataca en 66
        return partida

    def test_la_partida_termina(self):
        """§2.12: derrota cuando la vida del jugador llega a 0."""
        partida = self.morir()
        self.assertEqual(partida.jugador.vida, 0)
        self.assertTrue(partida.terminada)
        self.assertEqual(partida.resultado, "derrota")
        self.assertEqual(partida.reloj, 66)         # se detiene en ese instante

    def test_ya_no_se_puede_actuar(self):
        partida = self.morir()
        with self.assertRaises(RuntimeError):
            partida.esperar()

    def test_ni_usar_pergamino(self):
        partida = self.morir(pergaminos=1)
        self.assertFalse(partida.usar_pergamino())
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)


# ======================================================================
# 4.3  DESHACER EL COMBATE (§2.11) Y AZAR REPRODUCIBLE (§2.6)
# ======================================================================

class TestDeshacerCombate(unittest.TestCase):
    def test_deshacer_un_ataque(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")], pergaminos=1)
        partida.iniciar()
        partida.atacar(enemigo(partida, 1))
        partida.usar_pergamino()
        self.assertEqual(enemigo(partida, 1).vida, 12)
        self.assertEqual(partida.jugador.vida, 30)          # y el ataque de la rata en 66
        self.assertEqual(partida.reloj, 0)

    def test_el_azar_tambien_vuelve(self):
        """Deshacer y repetir el ataque da el MISMO daño: el pergamino no
        sirve para volver a tirar el dado."""
        partida = partida_de_dos_salas([("e-1", "ent_rata")], pergaminos=1)
        partida.iniciar()
        estado_azar = partida.azar.getstate()
        primero = partida.atacar(enemigo(partida, 1))
        partida.usar_pergamino()
        self.assertEqual(partida.azar.getstate(), estado_azar)
        self.assertEqual(partida.atacar(enemigo(partida, 1)), primero)

    def test_deshacer_una_muerte(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata", 3)], pergaminos=1)
        partida.iniciar()
        rata = enemigo(partida, 1)
        partida.atacar(rata)
        partida.usar_pergamino()
        self.assertIs(enemigo(partida, 1), rata)            # volvió a la sala
        self.assertEqual(rata.vida, 3)
        self.assertEqual(partida.enemigos_derrotados, 0)
        self.assertEqual(sala(partida, 1).cantidad_objetos(), 0)   # sin la poción
        self.assertEqual(proximo(rata), 66)                 # su turno volvió
        partida.esperar()
        self.assertLess(partida.jugador.vida, 30)           # y vuelve a atacar

    def test_vuelve_a_su_misma_posicion(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata", 3), ("e-2", "ent_rata")], pergaminos=1)
        partida.iniciar()
        primera = enemigo(partida, 1, 0)
        partida.atacar(primera)
        self.assertIsNot(enemigo(partida, 1, 0), primera)
        partida.usar_pergamino()
        self.assertIs(enemigo(partida, 1, 0), primera)

    def test_no_regala_pergaminos(self):
        """Matar a uno que suelta un pergamino y deshacerlo: el pergamino
        no se queda en el suelo (si no, matar-deshacer-matar los regalaría)."""
        partida = partida_de_dos_salas([("e-1", "ent_mago", 1)], pergaminos=1)
        partida.iniciar()
        partida.atacar(enemigo(partida, 1))
        partida.usar_pergamino()
        self.assertEqual(sala(partida, 1).cantidad_pergaminos(), 0)

    def test_si_ya_lo_recogio_no_se_cae(self):
        """Si el jugador ya recogió ese pergamino (eso no se deshace), al
        deshacer la muerte no queda nada que quitar del suelo."""
        partida = partida_de_dos_salas([("e-1", "ent_mago", 1)], pergaminos=1)
        partida.iniciar()
        partida.atacar(enemigo(partida, 1))
        partida.jugador.inventario.recoger_pergamino_de(sala(partida, 1))   # ahora tiene 2
        self.assertTrue(partida.usar_pergamino())
        self.assertEqual(sala(partida, 1).cantidad_pergaminos(), 0)
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)
        self.assertTrue(enemigo(partida, 1).esta_vivo())

    def test_misma_semilla_misma_partida(self):
        """§2.6: misma semilla y mismas acciones -> misma partida."""
        resultados = []
        for _ in range(2):
            partida = partida_de_dos_salas([("e-1", "ent_rata"), ("e-2", "ent_lenta")])
            partida.iniciar()
            partida.atacar(enemigo(partida, 1, 0))
            partida.esperar()
            partida.atacar(enemigo(partida, 1, 1))
            resultados.append((partida.jugador.vida, enemigo(partida, 1, 0).vida,
                               enemigo(partida, 1, 1).vida, partida.reloj))
        self.assertEqual(resultados[0], resultados[1])



# ======================================================================
# 4.4  COMPORTAMIENTOS (§2.8 y §2.9)
# ======================================================================
# En partida_cruce el jugador sale de la sala 2 en t=0 (mover "S", a la 1).
# El enemigo (velocidad 100) actúa en t=100, ANTES que el jugador (se
# programó primero), y ya no comparte sala: aplica su comportamiento.

class TestGuardian(unittest.TestCase):
    def test_nunca_deja_su_sala(self):
        partida = partida_cruce([("e-1", "ent_lenta")])           # guardián
        guardian = enemigo(partida, 2)
        partida.mover("S")
        partida.esperar()
        partida.esperar()
        self.assertEqual(donde_esta(partida, guardian), 2)
        self.assertEqual(partida.jugador.vida, 30)


class TestErrante(unittest.TestCase):
    def test_sale_por_una_salida_al_azar(self):
        """Salidas abiertas de la 2, siempre en orden N, S, E, O: 4, 1, 3, 5.
        Es el primer dado de la partida: randint(0, 3) con la semilla."""
        partida = partida_cruce([("e-1", "ent_errante")])
        errante = enemigo(partida, 2)
        partida.mover("S")
        esperado = [4, 1, 3, 5][random.Random(SEMILLA).randint(0, 3)]
        self.assertEqual(donde_esta(partida, errante), esperado)
        self.assertEqual(sala(partida, 2).cantidad_enemigos(), 0)

    def test_cada_salida_con_su_numero_del_dado(self):
        """Muchas decisiones seguidas: la salida n.º k (en orden N, S, E, O)
        sale cuando el dado da k, con randint(0, cantidad - 1)."""
        partida = partida_de_dos_salas()
        cruce = partida_cruce().mapa.obtener_sala(2)
        elegidas = [partida._destino_errante(cruce).id for _ in range(200)]
        azar = random.Random(SEMILLA)
        self.assertEqual(elegidas, [[4, 1, 3, 5][azar.randint(0, 3)] for _ in range(200)])
        self.assertEqual(sorted(set(elegidas)), [1, 3, 4, 5])

    def test_solo_por_salidas_abiertas(self):
        """§2.5: los enemigos no abren puertas. Con N y E cerradas, solo
        quedan S (1) y O (5)."""
        partida = partida_cruce([("e-1", "ent_errante")])
        errante = enemigo(partida, 2)
        sala(partida, 2).obtener_puerta("N").cerrar()
        sala(partida, 2).obtener_puerta("E").cerrar()
        partida.mover("S")
        esperado = [1, 5][random.Random(SEMILLA).randint(0, 1)]
        self.assertEqual(donde_esta(partida, errante), esperado)

    def test_sin_salidas_abiertas_espera(self):
        """Un errante lento (actúa en t=200). El jugador sale en t=0 y en
        t=100 se cierran todas las salidas de la 2: en t=200 espera."""
        partida = partida_cruce([("e-1", "ent_errante_lento")])
        errante = enemigo(partida, 2)
        partida.mover("S")                                       # reloj 100
        for direccion in "NSEO":
            sala(partida, 2).obtener_puerta(direccion).cerrar()
        estado_azar = partida.azar.getstate()
        partida.esperar()                                        # en t=200 le toca
        self.assertEqual(proximo(errante), 400)                  # sí actuó...
        self.assertEqual(donde_esta(partida, errante), 2)        # ...esperando
        self.assertEqual(partida.azar.getstate(), estado_azar)   # y sin tirar el dado

    def test_si_esta_el_jugador_ataca_y_no_se_mueve(self):
        """§2.8: si comparte sala con el jugador, ataca y no ejecuta movimiento."""
        partida = partida_cruce([("e-1", "ent_errante")])
        errante = enemigo(partida, 2)
        partida.esperar()                                        # en t=100 ataca
        self.assertEqual(donde_esta(partida, errante), 2)
        self.assertEqual(partida.jugador.vida, 30 - (5 + dados(1)[0] - 2))

    def test_misma_semilla_mismo_camino(self):
        caminos = []
        for _ in range(2):
            partida = partida_cruce([("e-1", "ent_errante"), ("e-2", "ent_errante")])
            a, b = enemigo(partida, 2, 0), enemigo(partida, 2, 1)
            partida.mover("S")
            recorrido = []
            for _ in range(5):
                partida.esperar()
                recorrido.append((a.sala_actual, b.sala_actual))
            caminos.append(recorrido)
        self.assertEqual(caminos[0], caminos[1])


class TestRastreador(unittest.TestCase):
    def test_sigue_el_rastro_fresco(self):
        """El jugador sale a la 1 en t=0 (rastro 0). En t=100 el rastreador
        ve ese rastro (antigüedad 100) y lo sigue."""
        partida = partida_cruce([("e-1", "ent_rastreador")])
        rastreador = enemigo(partida, 2)
        partida.mover("S")
        self.assertEqual(donde_esta(partida, rastreador), 1)

    def test_escoge_el_mas_reciente(self):
        """Velocidad 34 -> actúa en t=294. Antes, el jugador va a la 3
        (t=0), vuelve a la 2 (t=100) y sale a la 1 (t=200). Rastros
        frescos en la 3 (0) y en la 1 (200): sigue el MÁS reciente."""
        partida = partida_cruce([("e-1", "ent_rastreador_294")])
        rastreador = enemigo(partida, 2)
        partida.mover("E")
        partida.mover("O")
        partida.mover("S")
        self.assertEqual(partida.reloj, 300)
        self.assertEqual(donde_esta(partida, rastreador), 1)

    def test_no_hay_ataque_gratis_al_llegar(self):
        """§2.5: llega en t=100 pero ataca en su PRÓXIMO turno (t=200)."""
        partida = partida_cruce([("e-1", "ent_rastreador")])
        partida.mover("S")
        self.assertEqual(partida.jugador.vida, 30)
        partida.esperar()
        self.assertEqual(partida.jugador.vida, 30 - (5 + dados(1)[0] - 2))

    def test_rastro_de_400_ya_no_sirve(self):
        """Velocidad 25 -> actúa en t=400. El jugador pasa por la 4 en t=0
        y en t=100 se va a la 6 (que no es vecina de la 2): el rastro de la
        4 queda en 0. En t=400 tiene antigüedad 400 y ya no sirve (debe ser
        MENOS de 400). Espera."""
        partida = partida_cruce([("e-1", "ent_rastreador_400")])
        rastreador = enemigo(partida, 2)
        partida.mover("N")                                       # a la 4 en t=0
        partida.mover("N")                                       # a la 6 en t=100
        partida.esperar()
        partida.esperar()                                        # reloj 400
        self.assertEqual(sala(partida, 4).obtener_rastro(), 0)
        self.assertEqual(partida.reloj, 400)
        self.assertEqual(proximo(rastreador), 800)               # ya actuó en 400
        self.assertEqual(donde_esta(partida, rastreador), 2)

    def test_rastro_de_384_si_sirve(self):
        """Velocidad 26 -> actúa en t=384: antigüedad 384 < 400. Lo sigue."""
        partida = partida_cruce([("e-1", "ent_rastreador_384")])
        rastreador = enemigo(partida, 2)
        partida.mover("N")
        partida.mover("N")
        partida.esperar()
        partida.esperar()
        self.assertEqual(donde_esta(partida, rastreador), 4)

    def test_quedarse_quieto_mantiene_fresco_el_rastro(self):
        """Apéndice B: cada acción refresca el rastro de la sala actual. El
        jugador se queda esperando en la 1: en t=400 su rastro es de t=300
        y el rastreador lo sigue."""
        partida = partida_cruce([("e-1", "ent_rastreador_400")])
        rastreador = enemigo(partida, 2)
        partida.mover("S")
        for _ in range(3):
            partida.esperar()
        self.assertEqual(sala(partida, 1).obtener_rastro(), 300)
        self.assertEqual(donde_esta(partida, rastreador), 1)

    def test_no_pasa_por_puertas_cerradas(self):
        """Un rastreador lento (actúa en t=200). El jugador sale a la 1 en
        t=0 y en t=100 se cierra esa puerta: el rastro es fresco, pero
        está detrás de una puerta cerrada (§2.5). Espera."""
        partida = partida_cruce([("e-1", "ent_rastreador_lento")])
        rastreador = enemigo(partida, 2)
        partida.mover("S")                                       # reloj 100
        sala(partida, 1).obtener_puerta("N").cerrar()            # (la misma puerta que 2-S)
        partida.esperar()                                        # en t=200 le toca
        self.assertEqual(proximo(rastreador), 400)
        self.assertEqual(donde_esta(partida, rastreador), 2)

    def test_sin_rastro_espera(self):
        """Si el jugador nunca pisó las vecinas, no hay nada que seguir."""
        partida = partida_cruce([("e-1", "ent_rastreador")])
        rastreador = enemigo(partida, 2)
        partida.esperar()                                        # el jugador sigue en la 2: ataca
        self.assertEqual(donde_esta(partida, rastreador), 2)


class TestDeshacerComportamientos(unittest.TestCase):
    def test_deshacer_el_paso_de_un_errante(self):
        partida = partida_cruce([("e-1", "ent_errante"), ("e-2", "ent_lenta")], pergaminos=1)
        errante = enemigo(partida, 2, 0)
        estado_azar = partida.azar.getstate()
        partida.mover("S")
        self.assertNotEqual(errante.sala_actual, 2)
        partida.usar_pergamino()
        self.assertEqual(donde_esta(partida, errante), 2)
        self.assertIs(enemigo(partida, 2, 0), errante)           # en su misma posición
        self.assertEqual(partida.azar.getstate(), estado_azar)

    def test_rehacer_da_el_mismo_camino(self):
        partida = partida_cruce([("e-1", "ent_errante")], pergaminos=1)
        errante = enemigo(partida, 2)
        partida.mover("S")
        primera = errante.sala_actual
        partida.usar_pergamino()
        partida.mover("S")
        self.assertEqual(errante.sala_actual, primera)

    def test_deshacer_el_paso_de_un_rastreador(self):
        partida = partida_cruce([("e-1", "ent_rastreador")], pergaminos=1)
        rastreador = enemigo(partida, 2)
        partida.mover("S")
        partida.usar_pergamino()
        self.assertEqual(donde_esta(partida, rastreador), 2)
        self.assertEqual(sala(partida, 1).cantidad_enemigos(), 0)



# ======================================================================
# 4.5  OBJETOS (§2.7, §4.5)
# ======================================================================

class TestRecoger(unittest.TestCase):
    def test_recoger_cuesta_25(self):
        partida = partida_objetos()
        ficha = partida.recoger(0)
        self.assertEqual(ficha["id"], "itm_daga")
        self.assertEqual(ids_inventario(partida), ["itm_daga"])
        self.assertEqual(ids_suelo(partida), ["itm_llave_bronce", "itm_pocion_menor"])
        self.assertEqual(partida.reloj, 25)

    def test_objetos_del_suelo_para_la_vista(self):
        partida = partida_objetos()
        fichas = partida.objetos_del_suelo()
        self.assertEqual([fichas.obtener(i)["nombre"] for i in range(len(fichas))],
                         ["Daga", "Llave de bronce", "Poción"])

    def test_posicion_invalida(self):
        partida = partida_objetos()
        for posicion in (3, -1, "0"):
            with self.assertRaises(AccionInvalida):
                partida.recoger(posicion)
        self.assertEqual(partida.reloj, 0)

    def test_inventario_lleno(self):
        """§4.5: al llegar a inventario_max, recoger queda prohibido."""
        partida = partida_objetos(inventario_max=2)
        partida.recoger(0)
        partida.recoger(0)
        with self.assertRaises(AccionInvalida):
            partida.recoger(0)
        self.assertEqual(partida.reloj, 50)
        self.assertEqual(len(partida.estado.historial), 2)

    def test_deshacer_recoger(self):
        partida = partida_objetos(pergaminos=1)
        partida.recoger(1)                                       # la llave
        partida.usar_pergamino()
        self.assertEqual(ids_suelo(partida), ["itm_daga", "itm_llave_bronce", "itm_pocion_menor"])
        self.assertEqual(ids_inventario(partida), [])
        self.assertEqual(partida.reloj, 0)


class TestSoltar(unittest.TestCase):
    def test_soltar_lo_que_se_ve(self):
        partida = partida_objetos()
        partida.recoger(0)                                       # daga
        partida.recoger(0)                                       # llave
        partida.jugador.inventario.avanzar()                     # viendo la llave (no gasta tiempo)
        self.assertEqual(partida.reloj, 50)
        soltado = partida.soltar()
        self.assertEqual(soltado["id"], "itm_llave_bronce")
        self.assertEqual(ids_inventario(partida), ["itm_daga"])
        self.assertEqual(ids_suelo(partida), ["itm_pocion_menor", "itm_llave_bronce"])
        self.assertEqual(partida.reloj, 75)

    def test_sin_nada_que_soltar(self):
        partida = partida_objetos()
        with self.assertRaises(AccionInvalida):
            partida.soltar()

    def test_soltar_el_arma_equipada(self):
        partida = partida_objetos()
        partida.recoger(0)
        partida.equipar()
        self.assertEqual(partida.jugador.ataque_total(), 9)
        partida.soltar()
        self.assertEqual(partida.jugador.ataque_total(), 6)

    def test_deshacer_soltar(self):
        partida = partida_objetos(pergaminos=1)
        partida.recoger(0)
        partida.soltar()
        partida.usar_pergamino()
        self.assertEqual(ids_inventario(partida), ["itm_daga"])
        self.assertEqual(ids_suelo(partida), ["itm_llave_bronce", "itm_pocion_menor"])
        self.assertEqual(partida.reloj, 25)


class TestEquipar(unittest.TestCase):
    def test_secuencia_del_2_13(self):
        """t=100 recoge una daga (25) -> 125; equipa la daga (50) -> 175."""
        partida = partida_objetos()
        partida.esperar()
        partida.recoger(0)
        self.assertEqual(partida.reloj, 125)
        partida.equipar()
        self.assertEqual(partida.reloj, 175)
        self.assertEqual(partida.jugador.ataque_total(), 6 + 3)

    def test_equipar_mueve_al_frente(self):
        partida = partida_objetos()
        partida.recoger(1)                                       # llave
        partida.recoger(0)                                       # daga
        partida.jugador.inventario.avanzar()                     # viendo la daga
        partida.equipar()
        self.assertEqual(ids_inventario(partida), ["itm_daga", "itm_llave_bronce"])

    def test_no_se_equipa_una_llave(self):
        partida = partida_objetos()
        partida.recoger(1)
        with self.assertRaises(AccionInvalida):
            partida.equipar()
        self.assertEqual(partida.reloj, 25)

    def test_sin_nada_que_equipar(self):
        with self.assertRaises(AccionInvalida):
            partida_objetos().equipar()

    def test_deshacer_equipar(self):
        partida = partida_objetos(pergaminos=1)
        partida.recoger(1)                                       # llave
        partida.recoger(0)                                       # daga
        partida.jugador.inventario.avanzar()
        partida.equipar()
        partida.usar_pergamino()
        self.assertEqual(partida.jugador.ataque_total(), 6)
        self.assertEqual(ids_inventario(partida), ["itm_llave_bronce", "itm_daga"])
        self.assertEqual(partida.reloj, 50)


class TestPergaminosComoAcciones(unittest.TestCase):
    def test_recoger_un_pergamino(self):
        partida = partida_objetos()
        partida.recoger_pergamino()
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)
        self.assertEqual(partida.sala_actual().cantidad_pergaminos(), 0)
        self.assertEqual(partida.reloj, 25)
        with self.assertRaises(AccionInvalida):
            partida.recoger_pergamino()                          # ya no hay

    def test_soltar_un_pergamino(self):
        partida = partida_objetos(pergaminos=2)
        partida.soltar_pergamino()
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)
        self.assertEqual(partida.sala_actual().cantidad_pergaminos(), 2)
        self.assertEqual(partida.reloj, 25)

    def test_sin_pergaminos_que_soltar(self):
        with self.assertRaises(AccionInvalida):
            partida_objetos().soltar_pergamino()

    def test_ocupan_lugar_en_el_inventario(self):
        partida = partida_objetos(pergaminos=1, inventario_max=1)
        with self.assertRaises(AccionInvalida):
            partida.recoger(0)
        with self.assertRaises(AccionInvalida):
            partida.recoger_pergamino()

    def test_deshacer_recoger_pergamino(self):
        """§2.11: se deshace la acción (el reloj vuelve), pero el pergamino
        recogido se queda: 1 + 1 recogido - 1 gastado = 1, y no vuelve al suelo."""
        partida = partida_objetos(pergaminos=1)
        partida.recoger_pergamino()
        partida.usar_pergamino()
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)
        self.assertEqual(partida.sala_actual().cantidad_pergaminos(), 0)

    def test_deshacer_soltar_pergamino(self):
        partida = partida_objetos(pergaminos=2)
        partida.soltar_pergamino()
        partida.usar_pergamino()
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 0)
        self.assertEqual(partida.sala_actual().cantidad_pergaminos(), 2)


# ======================================================================
# 4.5  ABRIR PUERTAS (§2.5)
# ======================================================================

class TestAbrir(unittest.TestCase):
    def test_con_la_llave(self):
        partida = partida_objetos()
        partida.recoger(1)                                       # llave de bronce
        partida.abrir("E")
        self.assertFalse(partida.sala_actual().obtener_puerta("E").esta_cerrada())
        self.assertFalse(sala(partida, 3).obtener_puerta("O").esta_cerrada())   # los dos lados
        self.assertEqual(partida.reloj, 25 + 50)
        self.assertEqual(ids_inventario(partida), ["itm_llave_bronce"])         # no se consume

    def test_abrir_y_atravesar_son_dos_acciones(self):
        partida = partida_objetos()
        partida.recoger(1)
        partida.abrir("E")
        partida.mover("E")
        self.assertEqual(partida.jugador.sala_actual, 3)
        self.assertEqual(partida.reloj, 25 + 50 + 100)

    def test_sin_la_llave(self):
        partida = partida_objetos()
        partida.recoger(0)                                       # tiene una daga, no la llave
        with self.assertRaises(AccionInvalida) as error:
            partida.abrir("E")
        self.assertIn("llave", str(error.exception))
        with self.assertRaises(AccionInvalida):
            partida.abrir("O")                                   # su llave no está en la cripta
        self.assertEqual(partida.reloj, 25)

    def test_puerta_sin_cerradura(self):
        """Cerrada pero sin "llave": se abre sin necesitar nada."""
        partida = partida_objetos()
        partida.abrir("N")
        partida.mover("N")
        self.assertEqual(partida.jugador.sala_actual, 2)

    def test_ya_abierta_o_sin_salida(self):
        partida = partida_objetos()
        partida.abrir("N")
        with self.assertRaises(AccionInvalida):
            partida.abrir("N")
        with self.assertRaises(AccionInvalida):
            partida.abrir("S")

    def test_deshacer_abrir(self):
        partida = partida_objetos(pergaminos=1)
        partida.recoger(1)
        pendientes = len(partida.agenda)
        partida.abrir("E")
        partida.usar_pergamino()
        self.assertTrue(partida.sala_actual().obtener_puerta("E").esta_cerrada())
        self.assertEqual(len(partida.agenda), pendientes)        # su cierre ya no está programado


class TestCierreAutomatico(unittest.TestCase):
    def abierta_en_25(self, pergaminos=0):
        partida = partida_objetos(pergaminos=pergaminos)
        partida.recoger(1)                                       # t=0
        partida.abrir("E")                                       # t=25: cierre en 525
        return partida

    def test_se_cierra_a_los_500(self):
        partida = self.abierta_en_25()
        puerta = partida.sala_actual().obtener_puerta("E")
        while partida.reloj < 475:
            partida.esperar()                                    # 75, 175, ..., 475
        self.assertFalse(puerta.esta_cerrada())
        partida.esperar()                                        # pasa por t=525
        self.assertEqual(partida.reloj, 575)
        self.assertTrue(puerta.esta_cerrada())
        self.assertTrue(sala(partida, 3).obtener_puerta("O").esta_cerrada())

    def test_se_puede_volver_a_abrir(self):
        partida = self.abierta_en_25()
        for _ in range(6):
            partida.esperar()                                    # ya se cerró
        partida.abrir("E")
        self.assertFalse(partida.sala_actual().obtener_puerta("E").esta_cerrada())

    def test_deshacer_el_cierre(self):
        partida = self.abierta_en_25(pergaminos=1)
        while partida.reloj < 475:
            partida.esperar()
        partida.esperar()                                        # aquí se cerró
        partida.usar_pergamino()
        self.assertEqual(partida.reloj, 475)
        self.assertFalse(partida.sala_actual().obtener_puerta("E").esta_cerrada())



# ======================================================================
# 4.6  USAR OBJETOS (§2.7)
# ======================================================================

class TestUsar(unittest.TestCase):
    def test_pocion_que_cura(self):
        partida = partida_efectos(["itm_pocion_menor"], vida=20)
        partida.usar()
        self.assertEqual(partida.jugador.vida, 28)
        self.assertEqual(ids_inventario(partida), [])           # se consume
        self.assertEqual(partida.reloj, 50)

    def test_la_cura_no_pasa_de_vida_max(self):
        partida = partida_efectos(["itm_pocion_menor"], vida=28)
        partida.usar()
        self.assertEqual(partida.jugador.vida, 30)

    def test_lo_que_no_se_usa(self):
        partida = partida_efectos(["itm_daga", "itm_llave_bronce"])
        with self.assertRaises(AccionInvalida) as error:
            partida.usar()                                       # la daga se equipa
        self.assertIn("equipa", str(error.exception))
        partida.jugador.inventario.avanzar()
        with self.assertRaises(AccionInvalida):
            partida.usar()                                       # la llave abre puertas
        with self.assertRaises(AccionInvalida):
            partida_efectos().usar()                             # no tiene nada
        self.assertEqual(partida.reloj, 0)

    def test_deshacer_usar(self):
        partida = partida_efectos(["itm_daga", "itm_pocion_menor"], pergaminos=1, vida=20)
        partida.jugador.inventario.avanzar()                     # viendo la poción
        partida.usar()
        partida.usar_pergamino()
        self.assertEqual(partida.jugador.vida, 20)
        self.assertEqual(ids_inventario(partida), ["itm_daga", "itm_pocion_menor"])
        self.assertEqual(partida.jugador.inventario.actual()["id"], "itm_pocion_menor")


# ======================================================================
# 4.6  CAMBIO DE VELOCIDAD (§2.3, §2.10)
# ======================================================================

class TestVelocidad(unittest.TestCase):
    def test_la_rapidez_acorta_la_proxima_accion(self):
        """Velocidad 100 + 100 = 200: usar (50) tarda 50 * 100 // 200 = 25."""
        partida = partida_efectos(["itm_pocion_rapidez"])
        partida.usar()
        self.assertEqual(partida.jugador.velocidad, 200)
        self.assertEqual(partida.reloj, 25)
        partida.esperar()
        self.assertEqual(partida.reloj, 75)                     # 100 * 100 // 200 = 50

    def test_al_terminar_se_reescala_lo_que_falta(self):
        """Dura hasta t=300. El jugador quedó para 325 (a velocidad 200):
        en 300 le faltaban 25, que a velocidad 100 son 25 * 200 // 100 = 50.
        Vuelve a decidir en 350, no en 325 (§2.3)."""
        partida = partida_efectos(["itm_pocion_rapidez"])
        partida.usar()                                          # t=0 -> 25
        for esperado in (75, 125, 175, 225, 275):
            partida.esperar()
            self.assertEqual(partida.reloj, esperado)
        partida.esperar()                                       # quedó para 325...
        self.assertEqual(partida.reloj, 350)                    # ...y se reescaló
        self.assertEqual(partida.jugador.velocidad, 100)

    def test_la_lentitud_alarga(self):
        """Velocidad 50 por 200: usar -> 100. Esperar -> quedaría en 300; en
        200 le faltan 100, a velocidad 100 son 100 * 50 // 100 = 50 -> 250."""
        partida = partida_efectos(["itm_pocion_lentitud"])
        partida.usar()
        self.assertEqual(partida.reloj, 100)
        partida.esperar()
        self.assertEqual(partida.reloj, 250)
        self.assertEqual(partida.jugador.velocidad, 100)

    def test_nunca_baja_de_1(self):
        partida = partida_efectos(["itm_pocion_paralisis"])     # -500
        partida.usar()
        self.assertEqual(partida.reloj, 200 + (5000 - 200) * 1 // 100)   # 248
        self.assertEqual(partida.jugador.velocidad, 100)

    def test_deshacer_la_pocion(self):
        partida = partida_efectos(["itm_pocion_rapidez"], pergaminos=1)
        partida.usar()
        partida.usar_pergamino()
        self.assertEqual(partida.jugador.velocidad, 100)
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(len(partida.agenda), 0)                # su fin ya no está programado

    def test_deshacer_el_intervalo_donde_termino(self):
        partida = partida_efectos(["itm_pocion_rapidez"], pergaminos=1)
        partida.usar()
        esperar_hasta(partida, 275)
        partida.esperar()                                       # aquí terminó (t=300)
        partida.usar_pergamino()
        self.assertEqual(partida.reloj, 275)
        self.assertEqual(partida.jugador.velocidad, 200)
        partida.esperar()
        self.assertEqual((partida.reloj, partida.jugador.velocidad), (350, 100))


# ======================================================================
# 4.6  VENENO Y ANTÍDOTO (§2.10)
# ======================================================================
# El veneno lo pone la trampa "trp_espinas" (daño 0, veneno 2) de la sala 2.
# El jugador entra en t=0: pulsos en 80, 160, 240, 320 y 400.

class TestVeneno(unittest.TestCase):
    def test_cinco_pulsos_en_400(self):
        partida = partida_efectos(trampas_sala_2=["trp_espinas"])
        partida.mover("N")
        self.assertTrue(partida.esta_envenenado())
        self.assertEqual(partida.jugador.vida, 28)              # pulso de t=80
        esperar_hasta(partida, 500)
        self.assertEqual(partida.jugador.vida, 30 - 5 * 2)
        self.assertFalse(partida.esta_envenenado())
        partida.esperar()
        self.assertEqual(partida.jugador.vida, 20)

    def test_antidoto_antes_del_siguiente_pulso(self):
        """Los pulsos cancelados no hacen daño."""
        partida = partida_efectos(["itm_antidoto"], trampas_sala_2=["trp_espinas"])
        partida.mover("N")                                      # vida 28
        partida.usar()                                          # t=100 -> 150
        self.assertFalse(partida.esta_envenenado())
        self.assertEqual(len(partida.agenda), 1)                # solo el rearme: el pulso se canceló
        esperar_hasta(partida, 600)
        self.assertEqual(partida.jugador.vida, 28)
        self.assertEqual(ids_inventario(partida), [])

    def test_deshacer_el_antidoto(self):
        partida = partida_efectos(["itm_antidoto"], trampas_sala_2=["trp_espinas"], pergaminos=1)
        partida.mover("N")
        partida.usar()
        partida.usar_pergamino()
        self.assertTrue(partida.esta_envenenado())
        self.assertEqual(ids_inventario(partida), ["itm_antidoto"])
        esperar_hasta(partida, 500)
        self.assertEqual(partida.jugador.vida, 20)

    def test_antidoto_despues_de_deshacer_un_pulso(self):
        """El pergamino también devuelve a qué pulso apunta el veneno: si
        no, el antídoto cancelaría un evento que ya no está y dejaría vivo
        el pulso restaurado."""
        partida = partida_efectos(["itm_antidoto"], trampas_sala_2=["trp_espinas"], pergaminos=1)
        partida.mover("N")                                      # pulso de 80
        partida.esperar()                                       # pulso de 160
        partida.usar_pergamino()                                # vuelve a t=100
        partida.usar()                                          # antídoto
        self.assertEqual(len(partida.agenda), 1)                # solo el rearme
        esperar_hasta(partida, 600)
        self.assertEqual(partida.jugador.vida, 28)

    def test_un_veneno_nuevo_reemplaza_al_anterior(self):
        """Dos trampas venenosas a la vez: no se acumulan."""
        partida = partida_efectos(trampas_sala_2=["trp_espinas", "trp_espinas"])
        partida.mover("N")
        esperar_hasta(partida, 600)
        self.assertEqual(partida.jugador.vida, 20)

    def test_el_veneno_viejo_se_cancela(self):
        """Al reemplazarlo, el pulso pendiente del veneno anterior se
        cancela (no basta con ignorarlo cuando llegue)."""
        partida = partida_efectos()
        partida._envenenar(2)
        partida._envenenar(2)
        self.assertEqual(len(partida.agenda), 1)                # un solo pulso pendiente

    def test_el_veneno_puede_matar(self):
        partida = partida_efectos(trampas_sala_2=["trp_espinas"], vida=3)
        partida.mover("N")                                      # pulso de 80: queda en 1
        partida.esperar()                                       # pulso de 160: muere
        self.assertTrue(partida.terminada)
        self.assertEqual(partida.resultado, "derrota")
        self.assertEqual(partida.reloj, 160)

    def test_deshacer_un_pulso(self):
        partida = partida_efectos(trampas_sala_2=["trp_espinas"], pergaminos=1)
        partida.mover("N")                                      # vida 28
        partida.esperar()                                       # pulso de 160: 26
        partida.usar_pergamino()
        self.assertEqual(partida.jugador.vida, 28)
        esperar_hasta(partida, 500)
        self.assertEqual(partida.jugador.vida, 20)


# ======================================================================
# 4.6  TRAMPAS (§2.10)
# ======================================================================

class TestTrampas(unittest.TestCase):
    def test_se_activa_al_entrar(self):
        partida = partida_efectos(trampas_sala_2=["trp_dardos"])
        partida.mover("N")
        self.assertEqual(partida.jugador.vida, 26)
        self.assertFalse(sala(partida, 2).trampa_en(0).esta_activa())

    def test_desarmada_no_hace_nada_hasta_su_rearme(self):
        partida = partida_efectos(trampas_sala_2=["trp_dardos"])   # rearme 300
        partida.mover("N")                                      # t=0: -4
        partida.mover("S")
        partida.mover("N")                                      # t=200: desarmada
        self.assertEqual(partida.jugador.vida, 26)
        partida.mover("S")
        partida.mover("N")                                      # t=400: ya se rearmó (300)
        self.assertEqual(partida.jugador.vida, 22)

    def test_rearme_por_defecto_300(self):
        partida = partida_efectos(trampas_sala_2=["trp_lanzas"])   # sin "rearme"
        partida.mover("N")
        partida.mover("S")
        partida.mover("N")                                      # t=200: nada
        self.assertEqual(partida.jugador.vida, 20)
        partida.mover("S")
        partida.mover("N")                                      # t=400
        self.assertEqual(partida.jugador.vida, 10)

    def test_rearme_de_la_ficha(self):
        partida = partida_efectos(trampas_sala_2=["trp_rapida"])   # rearme 150
        partida.mover("N")
        partida.mover("S")
        partida.mover("N")                                      # t=200: rearmada en 150
        self.assertEqual(partida.jugador.vida, 28)

    def test_varias_trampas(self):
        partida = partida_efectos(trampas_sala_2=["trp_dardos", "trp_lanzas"])
        partida.mover("N")
        self.assertEqual(partida.jugador.vida, 16)

    def test_la_sala_inicial_no_dispara_al_empezar(self):
        """Las trampas se activan al ENTRAR por un movimiento; al empezar
        el jugador ya está en la sala inicial (decisión del grupo)."""
        partida = partida_efectos(trampas_sala_1=["trp_dardos"])
        self.assertEqual(partida.jugador.vida, 30)
        self.assertTrue(sala(partida, 1).trampa_en(0).esta_activa())

    def test_una_trampa_puede_matar(self):
        partida = partida_efectos(trampas_sala_2=["trp_dardos"], vida=4)
        partida.mover("N")
        self.assertTrue(partida.terminada)
        self.assertEqual(partida.reloj, 0)

    def test_deshacer_la_trampa(self):
        partida = partida_efectos(trampas_sala_2=["trp_dardos"], pergaminos=1)
        partida.mover("N")
        partida.usar_pergamino()
        self.assertEqual(partida.jugador.vida, 30)
        self.assertTrue(sala(partida, 2).trampa_en(0).esta_activa())
        self.assertEqual(len(partida.agenda), 0)                # su rearme ya no está

    def test_deshacer_un_rearme(self):
        """Como en el ejemplo del §2.11 ("t=180 se rearma una trampa")."""
        partida = partida_efectos(trampas_sala_2=["trp_rapida"], pergaminos=1)
        partida.mover("N")                                      # t=0
        partida.mover("S")                                      # t=100; en 150 se rearma
        self.assertTrue(sala(partida, 2).trampa_en(0).esta_activa())
        partida.usar_pergamino()
        self.assertFalse(sala(partida, 2).trampa_en(0).esta_activa())
        partida.esperar()                                       # pasa por 150 otra vez
        self.assertTrue(sala(partida, 2).trampa_en(0).esta_activa())


# ======================================================================
# 4.6  ANTORCHA (§2.10)
# ======================================================================

class TestAntorcha(unittest.TestCase):
    def test_dura_lo_que_dice_la_ficha(self):
        partida = partida_efectos(["itm_antorcha"])
        partida.usar()                                          # t=0, dura 500
        self.assertTrue(partida.antorcha_encendida())
        self.assertEqual(ids_inventario(partida), [])
        esperar_hasta(partida, 450)
        self.assertTrue(partida.antorcha_encendida())
        partida.esperar()                                       # pasa por 500
        self.assertFalse(partida.antorcha_encendida())

    def test_otra_antorcha_reemplaza_a_la_encendida(self):
        partida = partida_efectos(["itm_antorcha", "itm_antorcha"])
        partida.usar()                                          # t=0: hasta 500
        partida.usar()                                          # t=50: hasta 550
        self.assertEqual(len(partida.agenda), 1)                # el apagado de 500 se canceló
        esperar_hasta(partida, 500)
        self.assertTrue(partida.antorcha_encendida())           # la de 500 ya no cuenta
        partida.esperar()
        self.assertFalse(partida.antorcha_encendida())

    def test_deshacer_encenderla(self):
        partida = partida_efectos(["itm_antorcha"], pergaminos=1)
        partida.usar()
        partida.usar_pergamino()
        self.assertFalse(partida.antorcha_encendida())
        self.assertEqual(ids_inventario(partida), ["itm_antorcha"])
        self.assertEqual(len(partida.agenda), 0)


# ======================================================================
# 4.6  REGENERACIÓN (§2.10)
# ======================================================================
# Troll: vida_max 12, empieza con 5, regenera 3 cada 200, velocidad 50.

class TestRegeneracion(unittest.TestCase):
    def test_cada_200_sin_pasar_de_vida_max(self):
        partida = partida_efectos(enemigos_sala_1=[("e-1", "ent_troll", 5)])
        troll = enemigo(partida, 1)
        for reloj, vida in ((200, 8), (400, 11), (600, 12), (800, 12)):
            esperar_hasta(partida, reloj)
            self.assertEqual(troll.vida, vida, f"en t={reloj}")

    def test_se_cancela_al_morir(self):
        partida = partida_efectos(enemigos_sala_1=[("e-1", "ent_troll", 5)])
        partida.atacar(enemigo(partida, 1))                    # el golpe mínimo es 5
        self.assertEqual(len(partida.agenda), 0)                # ni turno ni regeneración

    def test_dormido_no_regenera(self):
        partida = partida_efectos(enemigos_sala_2=[("e-1", "ent_troll", 5)])
        esperar_hasta(partida, 600)
        self.assertEqual(len(partida.agenda), 0)

    def test_deshacer_la_regeneracion(self):
        partida = partida_efectos(enemigos_sala_1=[("e-1", "ent_troll", 5)], pergaminos=1)
        troll = enemigo(partida, 1)
        esperar_hasta(partida, 200)
        self.assertEqual(troll.vida, 8)
        partida.usar_pergamino()
        self.assertEqual(troll.vida, 5)
        partida.esperar()
        self.assertEqual(troll.vida, 8)



# ======================================================================
# 4.7  EL RASTRO SE REFRESCA CON CADA ACCIÓN (Apéndice B, §2.9)
# ======================================================================

class TestRastroConCadaAccion(unittest.TestCase):
    def test_cada_accion_refresca_la_sala_actual(self):
        partida = partida_de_dos_salas()
        partida.iniciar()
        partida.esperar()                                       # acción en t=0
        partida.esperar()                                       # acción en t=100
        self.assertEqual(sala(partida, 1).obtener_rastro(), 100)

    def test_cualquier_accion_cuenta(self):
        partida = partida_objetos()
        partida.recoger(0)                                      # t=0
        partida.recoger(0)                                      # t=25
        partida.equipar()                                       # t=50
        self.assertEqual(sala(partida, 1).obtener_rastro(), 50)

    def test_al_moverse_la_sala_que_deja_no_se_refresca(self):
        """Decisión: al moverse, el rastro va a la sala DESTINO; la que deja
        conserva el instante de su última acción allí (si no, las dos
        quedarían empatadas y un rastreador podría ir a la vacía)."""
        partida = partida_con_puertas()
        partida.esperar()                                       # t=0
        partida.esperar()                                       # t=100
        partida.mover("N")                                      # t=200
        self.assertEqual(sala(partida, 1).obtener_rastro(), 100)
        self.assertEqual(sala(partida, 2).obtener_rastro(), 200)

    def test_el_pergamino_lo_devuelve(self):
        partida = partida_de_dos_salas(pergaminos=1)
        partida.iniciar()
        partida.esperar()
        partida.esperar()
        partida.usar_pergamino()
        self.assertEqual(sala(partida, 1).obtener_rastro(), 0)


# ======================================================================
# 4.7  VICTORIA Y PUNTAJE (§2.12)
# ======================================================================

def partida_salida(pergaminos=0, trampa_en_salida=False, vida=None):
    """YA iniciada. La sala 2 es la de SALIDA. La puerta 1-2 está cerrada
    con la llave de salida, que está en el suelo de la 1. Hay otro camino
    a la 2, por la 3 (el rodeo): una puerta cerrada pero SIN cerradura.

        [2] SALIDA -------- [3] rodeo
         |   cerrada, sin    |
         |   cerradura       |
         | cerrada con       |
         | itm_llave_negra   |
        [1] inicio ----------+
    """
    mapa = Mapa()
    mapa.cargar_desde_json([
        {"id": 1, "nombre": "Inicio", "salidas": {
            "N": {"sala": 2, "cerrada": True, "llave": "itm_llave_negra"},
            "E": {"sala": 3}}},
        {"id": 2, "nombre": "Salida", "salidas": {"S": {"sala": 1}, "E": {"sala": 3}}},
        {"id": 3, "nombre": "Rodeo", "salidas": {"O": {"sala": 1}, "N": {"sala": 2, "cerrada": True}}},
    ])
    mapa.asignar_contenidos([
        {"sala": 1, "objetos": ["itm_llave_negra"]},
        {"sala": 2, "trampas": [{"instancia": "t-9", "tipo": "trp_lanzas"}] if trampa_en_salida else []},
        {"sala": 3},
    ])
    catalogo = dict(CATALOGO)
    catalogo["itm_llave_negra"] = {"id": "itm_llave_negra", "clase": "llave",
                                   "nombre": "Llave negra", "peso": 1, "valor": 50}
    jugador = nuevo_jugador(pergaminos)
    if vida is not None:
        jugador.vida = vida
    partida = Partida(mapa, jugador, 1, catalogo.get, semilla=SEMILLA,
                      id_sala_salida=2, llave_salida="itm_llave_negra")
    partida.iniciar()
    return partida


class TestVictoria(unittest.TestCase):
    def test_abrir_con_la_llave_y_entrar(self):
        partida = partida_salida()
        partida.recoger(0)                                      # t=0
        partida.abrir("N")                                      # t=25
        self.assertFalse(partida.terminada)
        partida.mover("N")                                      # t=75: entra
        self.assertTrue(partida.terminada)
        self.assertEqual(partida.resultado, "victoria")
        self.assertEqual(partida.reloj, 75)                     # tiempo final

    def test_entrar_por_otro_lado_no_gana(self):
        """Abrir OTRA puerta que lleva a la salida (sin la llave de salida)
        no cuenta."""
        partida = partida_salida()
        partida.mover("E")
        partida.abrir("N")                                      # la del rodeo, sin cerradura
        partida.mover("N")                                      # está en la salida...
        self.assertEqual(partida.jugador.sala_actual, 2)
        self.assertFalse(partida.terminada)                     # ...sin haber abierto LA puerta

    def test_si_la_trampa_lo_mata_es_derrota(self):
        partida = partida_salida(trampa_en_salida=True, vida=5)
        partida.recoger(0)
        partida.abrir("N")
        partida.mover("N")
        self.assertEqual(partida.resultado, "derrota")

    def test_abrirla_desde_adentro_y_volver_a_entrar(self):
        partida = partida_salida()
        partida.recoger(0)
        partida.mover("E")
        partida.abrir("N")
        partida.mover("N")                                      # entra por el rodeo
        partida.abrir("S")                                      # abre la puerta de la llave
        self.assertFalse(partida.terminada)
        partida.mover("S")
        partida.mover("N")
        self.assertEqual(partida.resultado, "victoria")

    def test_deshacer_abrir_la_puerta_de_salida(self):
        """Si el pergamino deshace la apertura, ya no cuenta como abierta."""
        partida = partida_salida(pergaminos=1)
        partida.recoger(0)
        partida.abrir("N")
        partida.usar_pergamino()
        partida.mover("E")
        partida.abrir("N")
        partida.mover("N")                                      # entra por el rodeo
        self.assertFalse(partida.terminada)

    def test_ya_no_se_juega(self):
        partida = partida_salida(pergaminos=1)
        partida.recoger(0)
        partida.abrir("N")
        partida.mover("N")
        with self.assertRaises(RuntimeError):
            partida.esperar()
        self.assertFalse(partida.usar_pergamino())

    def test_sin_sala_de_salida_no_se_gana(self):
        """Las demás pruebas no dan sala de salida: nunca se termina por esto."""
        partida = partida_objetos()
        partida.recoger(1)
        partida.abrir("E")
        partida.mover("E")
        self.assertFalse(partida.terminada)


class TestPuntaje(unittest.TestCase):
    def test_cuenta_las_acciones(self):
        partida = partida_salida()
        partida.recoger(0)
        partida.abrir("N")
        partida.mover("N")
        self.assertEqual(partida.acciones_jugador, 3)

    def test_lo_rechazado_no_cuenta(self):
        partida = partida_salida()
        with self.assertRaises(AccionInvalida):
            partida.abrir("N")                                  # sin la llave
        self.assertEqual(partida.acciones_jugador, 0)

    def test_lo_deshecho_no_cuenta_y_el_pergamino_tampoco(self):
        partida = partida_salida(pergaminos=1)
        partida.esperar()
        partida.esperar()
        partida.usar_pergamino()
        self.assertEqual(partida.acciones_jugador, 1)

    def test_datos_para_la_tabla(self):
        """§2.12: nombre, acciones, enemigos derrotados y tiempo final (el
        id y la versión de la cripta los pone el controlador)."""
        partida = partida_de_dos_salas([("e-1", "ent_rata", 3)])
        partida.iniciar()
        partida.atacar(enemigo(partida, 1))
        partida.esperar()
        self.assertEqual((partida.jugador.nombre, partida.acciones_jugador,
                          partida.enemigos_derrotados, partida.reloj), ("Héroe", 2, 1, 200))


if __name__ == "__main__":
    unittest.main()