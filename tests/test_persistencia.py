"""Pruebas de la Fase 6 (persistencia), en un solo archivo, por pasos:

    6.1  comandos y registro de partida (§4.11)
    6.2  el reproductor: --replay (§4.11)
    6.3  la tabla de puntajes (§2.12 y §4.9)

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_persistencia
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import copy
import os
import random
import tempfile
import unittest

from crypta.Adaptadores.RegistroPartida import (
    Encabezado, ErrorRegistro, FORMATO_REGISTRO, RegistroPartida, leer_registro,
)
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Controlador.Reproductor import (
    Reproductor, ReproduccionFallida, ReproduccionIncompatible,
)
from crypta.Modelo.Enemigo import Enemigo
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida
from crypta.Modelo.Sala import Sala
from crypta.Modelo.TablaPuntajes import (
    DERROTA, ErrorTablaPuntajes, Puntaje, TablaPuntajes, VICTORIA, puntaje_de,
)
from tests.test_partida import (
    CATALOGO, enemigo, ids_inventario, partida_con_puertas, partida_de_dos_salas,
    partida_efectos, partida_objetos,
)


def comandos_de(cola):
    return [comando for comando in cola]


class ConCarpetaTemporal(unittest.TestCase):
    """Cada prueba escribe en su propia carpeta, que se borra al final."""

    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.carpeta = self._carpeta.name

    def tearDown(self):
        self._carpeta.cleanup()

    def ruta(self, nombre="partida.log"):
        return os.path.join(self.carpeta, nombre)


def encabezado_de_prueba(jugador="Héroe"):
    return Encabezado("cripta-01", "a3f91c", "cat-2026-08-01", 12345, jugador)


# ======================================================================
# 6.1  COMANDOS
# ======================================================================

class TestComandos(unittest.TestCase):
    def test_esperar_y_mover(self):
        partida = partida_con_puertas()
        ejecutar_comando(partida, "mover N")
        self.assertEqual((partida.jugador.sala_actual, partida.reloj), (2, 100))
        ejecutar_comando(partida, "esperar")
        self.assertEqual(partida.reloj, 200)

    def test_minusculas_y_espacios_de_mas(self):
        partida = partida_con_puertas()
        ejecutar_comando(partida, "   mover   n  ")
        self.assertEqual(partida.jugador.sala_actual, 2)

    def test_atacar_por_id_de_instancia(self):
        """Por id y no por número en pantalla: el número cambia si otro
        enemigo muere o entra; el id no."""
        partida = partida_de_dos_salas([("e-1", "ent_rata"), ("e-2", "ent_rata")])
        partida.iniciar()
        ejecutar_comando(partida, "atacar e-2")
        self.assertEqual(enemigo(partida, 1, 0).vida, 12)
        self.assertLess(enemigo(partida, 1, 1).vida, 12)

    def test_atacar_a_uno_que_no_esta(self):
        partida = partida_de_dos_salas([("e-1", "ent_rata")])
        partida.iniciar()
        with self.assertRaises(AccionInvalida):
            ejecutar_comando(partida, "atacar e-99")
        self.assertEqual(partida.reloj, 0)

    def test_objetos_y_puertas(self):
        partida = partida_objetos()
        ejecutar_comando(partida, "recoger 1")              # la llave de bronce
        ejecutar_comando(partida, "abrir E")
        ejecutar_comando(partida, "mover E")
        self.assertEqual(partida.jugador.sala_actual, 3)

    def test_moverse_por_el_inventario(self):
        partida = partida_objetos()
        ejecutar_comando(partida, "recoger 0")              # daga
        ejecutar_comando(partida, "recoger 0")              # llave
        ejecutar_comando(partida, "avanzar")
        self.assertEqual(partida.jugador.inventario.actual()["id"], "itm_llave_bronce")
        ejecutar_comando(partida, "retroceder")
        ejecutar_comando(partida, "equipar")
        self.assertEqual(partida.jugador.ataque_total(), 9)
        ejecutar_comando(partida, "avanzar")
        ejecutar_comando(partida, "soltar")
        self.assertEqual(ids_inventario(partida), ["itm_daga"])

    def test_usar(self):
        partida = partida_efectos(["itm_pocion_menor"], vida=20)
        ejecutar_comando(partida, "usar")
        self.assertEqual(partida.jugador.vida, 28)

    def test_pergaminos(self):
        partida = partida_objetos(pergaminos=1)
        ejecutar_comando(partida, "recoger_pergamino")
        ejecutar_comando(partida, "soltar_pergamino")
        self.assertEqual(partida.jugador.inventario.cantidad_pergaminos(), 1)
        self.assertTrue(ejecutar_comando(partida, "pergamino"))
        self.assertEqual(partida.reloj, 25)

    def test_pergamino_que_no_se_puede_usar(self):
        """usar_pergamino devuelve False; el comando lo convierte en
        AccionInvalida para que no se anote en el registro."""
        partida = partida_objetos()
        with self.assertRaises(AccionInvalida):
            ejecutar_comando(partida, "pergamino")

    def test_lineas_que_no_se_entienden(self):
        partida = partida_con_puertas()
        for linea in ("", "   ", "volar", "mover", "mover N S", "esperar 3",
                      "recoger x", "recoger -1", "mover X", "mover NE", "Mover N", 42):
            with self.assertRaises(ComandoInvalido, msg=repr(linea)):
                ejecutar_comando(partida, linea)
        self.assertEqual(partida.reloj, 0)
        self.assertEqual(len(partida.estado.historial), 0)

    def test_se_entiende_pero_no_se_puede(self):
        """Distinto de ComandoInvalido: la puerta del oeste está cerrada."""
        partida = partida_con_puertas()
        with self.assertRaises(AccionInvalida):
            ejecutar_comando(partida, "mover O")


# ======================================================================
# 6.1  REGISTRO DE PARTIDA (§4.11)
# ======================================================================

class TestRegistro(ConCarpetaTemporal):
    def test_ida_y_vuelta(self):
        registro = RegistroPartida.crear(self.ruta(), encabezado_de_prueba())
        for comando in ("mover N", "atacar e-201", "esperar"):
            registro.anotar(comando)
        encabezado, comandos = leer_registro(self.ruta())
        self.assertEqual((encabezado.cripta_id, encabezado.version_cripta,
                          encabezado.version_catalogo, encabezado.semilla, encabezado.jugador),
                         ("cripta-01", "a3f91c", "cat-2026-08-01", 12345, "Héroe"))
        self.assertEqual(encabezado.formato, FORMATO_REGISTRO)
        self.assertEqual(comandos_de(comandos), ["mover N", "atacar e-201", "esperar"])

    def test_solo_agrega_al_final(self):
        """Lo ya escrito nunca cambia; aunque se cree otro objeto
        RegistroPartida para el mismo archivo, se sigue agregando."""
        RegistroPartida.crear(self.ruta(), encabezado_de_prueba()).anotar("mover N")
        with open(self.ruta(), "rb") as archivo:
            antes = archivo.read()
        RegistroPartida(self.ruta()).anotar("esperar")
        with open(self.ruta(), "rb") as archivo:
            despues = archivo.read()
        self.assertTrue(despues.startswith(antes))
        self.assertEqual(comandos_de(leer_registro(self.ruta())[1]), ["mover N", "esperar"])

    def test_nombre_con_espacios_y_tildes(self):
        RegistroPartida.crear(self.ruta(), encabezado_de_prueba("Ana María Núñez"))
        self.assertEqual(leer_registro(self.ruta())[0].jugador, "Ana María Núñez")

    def test_registro_sin_comandos(self):
        RegistroPartida.crear(self.ruta(), encabezado_de_prueba())
        self.assertEqual(len(leer_registro(self.ruta())[1]), 0)

    def test_lineas_vacias_se_ignoran(self):
        RegistroPartida.crear(self.ruta(), encabezado_de_prueba())
        with open(self.ruta(), "a", encoding="utf-8") as archivo:
            archivo.write("\nmover N\n\n\nesperar\n")
        self.assertEqual(comandos_de(leer_registro(self.ruta())[1]), ["mover N", "esperar"])

    def test_no_se_anotan_saltos_de_linea(self):
        registro = RegistroPartida.crear(self.ruta(), encabezado_de_prueba())
        with self.assertRaises(ValueError):
            registro.anotar("mover N\nesperar")
        with self.assertRaises(ValueError):
            RegistroPartida.crear(self.ruta("otro.log"), encabezado_de_prueba("Ana\nMaría"))


class TestRegistroDanado(ConCarpetaTemporal):
    """Un archivo que no sirve se rechaza con un mensaje claro."""

    def escribir(self, texto):
        with open(self.ruta(), "w", encoding="utf-8") as archivo:
            archivo.write(texto)

    def registro_valido_cambiando(self, viejo, nuevo):
        RegistroPartida.crear(self.ruta(), encabezado_de_prueba()).anotar("esperar")
        with open(self.ruta(), encoding="utf-8") as archivo:
            texto = archivo.read()
        self.assertIn(viejo, texto)
        self.escribir(texto.replace(viejo, nuevo))

    def test_no_es_un_registro(self):
        self.escribir("hola, esto es otra cosa\n")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())

    def test_primera_linea_de_otro_programa(self):
        """Todo lo demás está bien; solo la marca de la primera línea no."""
        self.registro_valido_cambiando("# CRIPTA registro de partida\n", "# otro programa\n")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())

    def test_no_existe(self):
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta("no_existe.log"))

    def test_formato_distinto(self):
        self.registro_valido_cambiando("formato 1\n", "formato 2\n")
        with self.assertRaises(ErrorRegistro) as error:
            leer_registro(self.ruta())
        self.assertIn("formato", str(error.exception))

    def test_falta_la_semilla(self):
        self.registro_valido_cambiando("semilla 12345\n", "")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())

    def test_falta_la_version_del_catalogo(self):
        self.registro_valido_cambiando("version_catalogo cat-2026-08-01\n", "")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())

    def test_semilla_que_no_es_numero(self):
        self.registro_valido_cambiando("semilla 12345\n", "semilla doce\n")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())

    def test_sin_separador(self):
        self.registro_valido_cambiando("---\n", "")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())

    def test_dato_desconocido(self):
        self.registro_valido_cambiando("jugador Héroe\n", "jugador Héroe\ncolor azul\n")
        with self.assertRaises(ErrorRegistro):
            leer_registro(self.ruta())


class TestJugarYRegistrar(ConCarpetaTemporal):
    """Así lo usará el controlador (Fase 7): se ejecuta el comando y, SOLO
    si salió bien, se anota."""

    def jugar(self, partida, registro, comando):
        try:
            ejecutar_comando(partida, comando)
        except (ComandoInvalido, AccionInvalida):
            return False
        registro.anotar(comando)
        return True

    def test_el_registro_tiene_solo_lo_que_paso(self):
        partida = partida_con_puertas(pergaminos=1)
        registro = RegistroPartida.crear(self.ruta(), encabezado_de_prueba())
        for comando in ("mover O", "mover N", "volar", "esperar", "pergamino", "atacar e-1"):
            self.jugar(partida, registro, comando)
        self.assertEqual(comandos_de(leer_registro(self.ruta())[1]),
                         ["mover N", "esperar", "pergamino", "atacar e-1"])


# ======================================================================
# 6.2  EL REPRODUCTOR (§4.11)
# ======================================================================
#
# Una cripta de prueba con un poco de todo:
#
#                       [4] SALIDA (trampa de dardos)
#                        |  cerrada con itm_llave_negra
#        [6] Osario --- [2] Cruce --- [5] Nido
#        rata e-61       errante e-21     troll e-51 (regenera)
#                        rastreador e-22
#                        trampa de espinas (veneno)
#                        |
#        [3] Bodega --- [1] Entrada (inicial)
#        lenta e-31          daga, poción, pergamino
#        llave negra, antorcha, antídoto, poción de rapidez
#
# El errante y el rastreador pueden caminar a salas cuyo contenido todavía
# no se ha cargado (la 5 y la 6): justo el caso delicado del 6.2.

ESQUELETO_REPRO = [
    {"id": 1, "nombre": "Entrada", "salidas": {"N": {"sala": 2}, "O": {"sala": 3}}},
    {"id": 2, "nombre": "Cruce", "salidas": {
        "S": {"sala": 1}, "E": {"sala": 5}, "O": {"sala": 6},
        "N": {"sala": 4, "cerrada": True, "llave": "itm_llave_negra"}}},
    {"id": 3, "nombre": "Bodega", "salidas": {"E": {"sala": 1}}},
    {"id": 4, "nombre": "Salida", "salidas": {"S": {"sala": 2}}},
    {"id": 5, "nombre": "Nido", "salidas": {"O": {"sala": 2}}},
    {"id": 6, "nombre": "Osario", "salidas": {"E": {"sala": 2}}},
]

CONTENIDO_REPRO = [
    {"sala": 1, "objetos": ["itm_daga", "itm_pocion_menor", "itm_pergamino_retroceso"]},
    {"sala": 2, "enemigos": [{"instancia": "e-21", "tipo": "ent_errante_lento"},
                             {"instancia": "e-22", "tipo": "ent_rastreador", "vida": 8}],
     "trampas": [{"instancia": "t-21", "tipo": "trp_espinas"}]},
    {"sala": 3, "enemigos": [{"instancia": "e-31", "tipo": "ent_lenta"}],
     "objetos": ["itm_llave_negra", "itm_antorcha", "itm_antidoto", "itm_pocion_rapidez"]},
    {"sala": 4, "trampas": [{"instancia": "t-41", "tipo": "trp_dardos"}]},
    {"sala": 5, "enemigos": [{"instancia": "e-51", "tipo": "ent_troll"}],
     "objetos": ["itm_cota", "itm_pergamino_retroceso"]},
    {"sala": 6, "enemigos": [{"instancia": "e-61", "tipo": "ent_rata"}],
     "objetos": ["itm_pocion_lentitud"]},
]

CATALOGO_REPRO = dict(CATALOGO)
CATALOGO_REPRO["itm_llave_negra"] = {"id": "itm_llave_negra", "clase": "llave",
                                     "nombre": "Llave negra", "peso": 1, "valor": 50}

IDS_SALAS_REPRO = [datos["id"] for datos in ESQUELETO_REPRO]
SEMILLA_REPRO = 2026


class PreparadorDePrueba:
    """Hace de servidor y de copia local (lo que en la Fase 7 harán
    GestorCripta, GestorContenido y RepositorioFichas).

    - Como la red: el contenido de una sala se carga solo cuando se pide.
      Con cargar_todo=True imita una copia local completa: todo cargado
      desde el principio.
    - Solo "tiene" las versiones que se le indican.
    - falta_sala: una sala que no puede dar (copia local incompleta).
    - vida: la del jugador (las partidas al azar usan más, para durar)."""

    def __init__(self, cargar_todo=False, versiones_cripta=("v1",),
                 versiones_catalogo=("cat-1",), falta_sala=None, vida=60):
        self._cargar_todo = cargar_todo
        self._versiones_cripta = versiones_cripta
        self._versiones_catalogo = versiones_catalogo
        self._falta_sala = falta_sala
        self._vida = vida
        self._mapa = None
        self.partidas_creadas = 0
        self.salas_pedidas = []       # en el orden en que se cargaron
        self.ya_estaban = []          # (sala, enemigos que ya estaban al cargarla)

    def cripta_disponible(self, cripta_id, version):
        return cripta_id == "cripta-prueba" and version in self._versiones_cripta

    def catalogo_disponible(self, version):
        return version in self._versiones_catalogo

    def crear_partida(self, encabezado):
        self.partidas_creadas += 1
        self._mapa = Mapa()
        self._mapa.cargar_desde_json(ESQUELETO_REPRO)

        if self._cargar_todo:
            self._mapa.asignar_contenidos(copy.deepcopy(CONTENIDO_REPRO))
        else:
            self.garantizar_sala(1)

        jugador = Jugador(encabezado.jugador, vida_max=self._vida, ataque=6, defensa=2,
                          velocidad=100, inventario_max=6)
        jugador.inventario.fijar_pergaminos(2)
        return Partida(self._mapa, jugador, 1, CATALOGO_REPRO.get,
                       semilla=encabezado.semilla, id_sala_salida=4,
                       llave_salida="itm_llave_negra")

    def garantizar_sala(self, id_sala):
        if id_sala == self._falta_sala:
            raise ReproduccionIncompatible(f"La copia local no tiene la sala {id_sala}")

        sala = self._mapa.obtener_sala(id_sala)

        if sala.contenido_cargado():
            return

        self.salas_pedidas.append(id_sala)
        self.ya_estaban.append((id_sala, [sala.enemigo_en(i).id_instancia
                                          for i in range(sala.cantidad_enemigos())]))

        for datos in CONTENIDO_REPRO:
            if datos["sala"] == id_sala:
                self._mapa.asignar_contenidos([copy.deepcopy(datos)])


def encabezado_repro(version_cripta="v1", version_catalogo="cat-1", semilla=SEMILLA_REPRO):
    return Encabezado("cripta-prueba", version_cripta, version_catalogo, semilla, "Héroe")


def evento(e):
    if e is None:
        return None
    return (e.tiempo, e.secuencia, e.tipo, e.esta_valido())


def nombre_de(objetivo):
    for atributo in ("id_instancia", "instancia", "tipo", "nombre", "sala_destino"):
        if hasattr(objetivo, atributo):
            return getattr(objetivo, atributo)
    return None


def foto(partida, ids_salas=IDS_SALAS_REPRO):
    """TODO el estado de la partida, para comparar dos partidas.
    ids_salas: de qué salas se mira el estado."""
    jugador, inventario = partida.jugador, partida.jugador.inventario

    salas = []
    for id_sala in ids_salas:
        s = partida.mapa.obtener_sala(id_sala)
        enemigos = [s.enemigo_en(i) for i in range(s.cantidad_enemigos())]
        salas.append((
            id_sala, s.contenido_cargado(),
            [s.objeto_en(i) for i in range(s.cantidad_objetos())],
            s.cantidad_pergaminos(), s.ultimo_rastro,
            [(e.id_instancia, e.vida, e.esta_activo(), e.sala_actual, e.velocidad,
              evento(e.evento_siguiente), evento(e.evento_regeneracion)) for e in enemigos],
            [s.trampa_en(i).esta_activa() for i in range(s.cantidad_trampas())],
            [(d, s.obtener_puerta(d).esta_cerrada()) for d in "NSEO" if s.obtener_puerta(d)],
        ))

    # La agenda por dentro (solo se mira, no se toca): si la reproducción
    # es exacta, hasta el montículo queda igual, con los mismos números de
    # secuencia.
    monticulo = partida.agenda._monticulo._vector
    agenda = [(evento(monticulo.obtener(i)), nombre_de(monticulo.obtener(i).objetivo))
              for i in range(len(monticulo))]

    def efecto(e):
        return None if e is None else (e.tipo, e.valor, e.hasta, evento(e.evento))

    return {
        "reloj": partida.reloj, "terminada": partida.terminada,
        "resultado": partida.resultado, "acciones": partida.acciones_jugador,
        "derrotados": partida.enemigos_derrotados,
        "vida": jugador.vida, "velocidad": jugador.velocidad, "sala": jugador.sala_actual,
        "turno": evento(jugador.evento_siguiente),
        "inventario": [objeto["id"] for objeto in inventario.orden_real()],
        "actual": inventario.actual() and inventario.actual()["id"],
        "arma": inventario.arma() and inventario.arma()["id"],
        "armadura": inventario.armadura() and inventario.armadura()["id"],
        "pergaminos": inventario.cantidad_pergaminos(),
        "historial": len(partida.estado.historial),
        "veneno": efecto(partida.veneno), "antorcha": efecto(partida.antorcha),
        "puerta_salida": partida.puerta_de_salida_abierta,
        "azar": partida.azar.getstate(),
        "salas": salas, "agenda": agenda, "pendientes": len(partida.agenda),
        "bitacora": list(partida.bitacora),
    }


def salas_cargadas(partida):
    return [i for i in IDS_SALAS_REPRO if partida.mapa.obtener_sala(i).contenido_cargado()]


def jugar_y_registrar(ruta, comandos, preparador=None, semilla=SEMILLA_REPRO):
    """La partida ORIGINAL, jugada como la jugará el controlador (Fase 7):
    cada línea con ejecutar_comando y el garantizar_sala del preparador, y
    se anota SOLO si salió bien. Se para cuando la partida termina.

    Devuelve (partida, preparador, pasos); pasos tiene, por cada comando
    anotado, (salas cargadas, foto) justo después de ejecutarlo."""
    preparador = preparador or PreparadorDePrueba()
    encabezado = encabezado_repro(semilla=semilla)
    registro = RegistroPartida.crear(ruta, encabezado)
    partida = preparador.crear_partida(encabezado)
    partida.iniciar()
    pasos = []

    for comando in comandos:
        if partida.terminada:
            break
        try:
            ejecutar_comando(partida, comando, preparador.garantizar_sala)
        except (ComandoInvalido, AccionInvalida):
            continue
        registro.anotar(comando)
        cargadas = salas_cargadas(partida)
        pasos.append((cargadas, foto(partida, cargadas)))

    return partida, preparador, pasos


def reproducir_con_fotos(ruta, preparador, pasos):
    """Reproduce y saca una foto después de cada comando, de las mismas
    salas que tenía cargadas la partida original en ese paso."""
    fotos = []

    def al_ejecutar(numero, comando, partida):
        fotos.append(foto(partida, pasos[numero - 1][0]))

    resultado = Reproductor(preparador).reproducir(ruta, al_ejecutar)
    return resultado, fotos


# La partida de la prueba principal: (comando, ¿queda en el registro?).
# Los que no se pueden hacer (o no se entienden) NO se anotan.
PARTIDA_GUIADA = [
    ("recoger 0", True),             # daga
    ("equipar", True),
    ("recoger 0", True),             # poción menor
    ("retroceder", True), ("avanzar", True),
    ("volar", False),                # no se entiende
    ("mover S", False),              # no hay salida
    ("mover O", True),               # Bodega: se carga la 3 y despierta e-31
    ("atacar e-31", True),
    ("pergamino", True),             # deshace el ataque, con el dado incluido
    ("atacar e-31", True), ("atacar e-31", True),
    ("atacar e-31", False),          # ya murió
    ("recoger 0", True),             # llave negra
    ("recoger 0", True),             # antorcha
    ("avanzar", True), ("avanzar", True), ("avanzar", True),
    ("usar", True),                  # la antorcha
    ("recoger_pergamino", False),    # no hay pergaminos en el suelo
    ("soltar_pergamino", True), ("recoger_pergamino", True),
    ("mover E", True),               # Entrada
    ("mover N", True),               # Cruce: espinas (veneno); despiertan e-21 y e-22
    ("atacar e-22", True), ("atacar e-21", True),
    ("esperar", True),
    ("abrir N", True),               # con la llave negra
    ("mover N", True),               # Salida: dardos... y victoria
]


def comandos_guiados():
    return [comando for comando, _ in PARTIDA_GUIADA]


def anotados_guiados():
    return [comando for comando, se_anota in PARTIDA_GUIADA if se_anota]


# Para las partidas al azar.
COMANDOS_AL_AZAR = (
    "mover N", "mover S", "mover E", "mover O", "abrir N", "abrir S", "abrir E", "abrir O",
    "atacar e-21", "atacar e-22", "atacar e-31", "atacar e-51", "atacar e-61",
    "recoger 0", "recoger 1", "recoger 2", "soltar", "equipar", "usar", "avanzar",
    "retroceder", "pergamino", "recoger_pergamino", "soltar_pergamino", "esperar", "volar",
)


def comandos_al_azar(semilla, cantidad):
    azar = random.Random(semilla)
    return [azar.choice(COMANDOS_AL_AZAR) for _ in range(cantidad)]


class TestReproducir(ConCarpetaTemporal):
    def test_la_reproduccion_queda_identica(self):
        """La prueba principal: se juega, se registra, se reproduce en una
        partida NUEVA y, después de CADA comando, todo es igual: reloj,
        vidas, inventario, salas, enemigos, agenda, azar y bitácora."""
        original, _, pasos = jugar_y_registrar(self.ruta(), comandos_guiados())
        self.assertEqual(original.resultado, "victoria")      # se jugó de verdad
        self.assertEqual(comandos_de(leer_registro(self.ruta())[1]), anotados_guiados())

        resultado, fotos = reproducir_con_fotos(self.ruta(), PreparadorDePrueba(), pasos)

        self.assertEqual(resultado.comandos, len(pasos))
        for numero in range(len(pasos)):
            self.assertEqual(fotos[numero], pasos[numero][1], f"después del comando {numero + 1}")
        self.assertEqual(foto(resultado.partida), foto(original))
        self.assertEqual(resultado.partida.resultado, "victoria")

    def comparar_al_azar(self, cargar_todo):
        for semilla in range(8):
            with self.subTest(semilla=semilla):
                ruta = self.ruta(f"azar-{semilla}.log")
                original, _, pasos = jugar_y_registrar(
                    ruta, comandos_al_azar(semilla, 400), PreparadorDePrueba(vida=200),
                    semilla=semilla)
                resultado, fotos = reproducir_con_fotos(
                    ruta, PreparadorDePrueba(cargar_todo=cargar_todo, vida=200), pasos)
                self.assertEqual(len(fotos), len(pasos))
                for numero in range(len(pasos)):
                    self.assertEqual(fotos[numero], pasos[numero][1],
                                     f"después del comando {numero + 1}")

    def test_partidas_al_azar(self):
        """Ocho partidas con comandos al azar (muchos no se pueden hacer):
        cada una se reproduce igual, paso por paso."""
        self.comparar_al_azar(cargar_todo=False)

    def test_con_todo_cargado_desde_el_principio(self):
        """Al jugar, el contenido llega cuando llega (red, precarga); al
        reproducir puede venir todo de una copia local. Eso NO debe
        cambiar la partida."""
        self.comparar_al_azar(cargar_todo=True)

    def test_un_enemigo_llego_antes_que_el_contenido(self):
        """El caso delicado: el errante (lento) camina a la sala 5 cuando
        todavía no se ha cargado; el jugador entra y recién ahí se carga.
        Reproduciendo con todo cargado desde el principio, el contenido
        estaba ANTES que el errante. La sala debe quedar igual."""
        comandos = ["mover N", "mover S", "mover N", "mover E"]
        original, preparador, pasos = jugar_y_registrar(self.ruta(), comandos, semilla=0)
        self.assertIn((5, ["e-21"]), preparador.ya_estaban)    # sí pasó

        resultado, fotos = reproducir_con_fotos(
            self.ruta(), PreparadorDePrueba(cargar_todo=True), pasos)
        self.assertEqual(fotos, [foto for _, foto in pasos])
        sala_5 = original.mapa.obtener_sala(5)
        self.assertEqual([sala_5.enemigo_en(i).id_instancia for i in range(sala_5.cantidad_enemigos())],
                         ["e-51", "e-21", "e-22"])

    def test_carga_las_mismas_salas_y_cuando_hacen_falta(self):
        """Reproduciendo, cada sala se carga justo antes de entrar (§2.4),
        igual que al jugar; y una puerta cerrada no hace cargar nada."""
        _, al_jugar, _ = jugar_y_registrar(self.ruta(), comandos_guiados())
        al_reproducir = PreparadorDePrueba()
        Reproductor(al_reproducir).reproducir(self.ruta())
        self.assertEqual(al_reproducir.salas_pedidas, [1, 3, 2, 4])
        self.assertEqual(al_reproducir.salas_pedidas, al_jugar.salas_pedidas)

    def test_registro_sin_comandos(self):
        """Solo se inicia: el jugador en la sala inicial, en t=0."""
        RegistroPartida.crear(self.ruta(), encabezado_repro())
        resultado = Reproductor(PreparadorDePrueba()).reproducir(self.ruta())
        self.assertEqual(resultado.comandos, 0)
        self.assertTrue(resultado.partida.iniciada)
        self.assertEqual((resultado.partida.reloj, resultado.partida.jugador.sala_actual), (0, 1))
        self.assertEqual(list(resultado.partida.bitacora), ["[t=0] Entras en Entrada."])

    def test_registro_de_una_partida_sin_terminar(self):
        """El jugador salió (o el programa se cayó) a media partida: se
        reproduce hasta donde llegó."""
        original, _, pasos = jugar_y_registrar(self.ruta(), comandos_guiados()[:8])
        resultado = Reproductor(PreparadorDePrueba()).reproducir(self.ruta())
        self.assertFalse(resultado.partida.terminada)
        self.assertEqual(resultado.comandos, len(pasos))
        self.assertEqual(foto(resultado.partida), foto(original))

    def test_avisa_despues_de_cada_comando(self):
        jugar_y_registrar(self.ruta(), comandos_guiados()[:5])
        vistos = []
        resultado = Reproductor(PreparadorDePrueba()).reproducir(
            self.ruta(), lambda numero, comando, partida: vistos.append((numero, comando, partida.reloj)))
        self.assertEqual(vistos, [(1, "recoger 0", 25), (2, "equipar", 75), (3, "recoger 0", 100),
                                  (4, "retroceder", 100), (5, "avanzar", 100)])
        self.assertEqual(resultado.comandos, 5)

    def test_no_cambia_el_registro(self):
        """Reproducir solo LEE el registro."""
        jugar_y_registrar(self.ruta(), comandos_guiados())
        with open(self.ruta(), "rb") as archivo:
            antes = archivo.read()
        Reproductor(PreparadorDePrueba()).reproducir(self.ruta())
        with open(self.ruta(), "rb") as archivo:
            self.assertEqual(archivo.read(), antes)

    def test_archivo_que_no_es_un_registro(self):
        with open(self.ruta(), "w", encoding="utf-8") as archivo:
            archivo.write("hola\n")
        with self.assertRaises(ErrorRegistro):
            Reproductor(PreparadorDePrueba()).reproducir(self.ruta())


class TestReproduccionIncompatible(ConCarpetaTemporal):
    """§4.11 y Apéndice B: si no se tiene la versión del registro, se avisa
    que no se puede garantizar una reproducción fiel y NO se juega nada."""

    def reproducir_con(self, preparador, encabezado):
        RegistroPartida.crear(self.ruta(), encabezado).anotar("esperar")
        with self.assertRaises(ReproduccionIncompatible) as error:
            Reproductor(preparador).reproducir(self.ruta())
        self.assertIn("reproducción fiel", str(error.exception))
        self.assertEqual(preparador.partidas_creadas, 0)          # no se jugó nada
        return str(error.exception)

    def test_version_de_cripta_que_ya_no_esta(self):
        mensaje = self.reproducir_con(PreparadorDePrueba(versiones_cripta=("v2",)),
                                      encabezado_repro(version_cripta="v1"))
        self.assertIn("v1", mensaje)

    def test_version_de_catalogo_que_ya_no_esta(self):
        mensaje = self.reproducir_con(PreparadorDePrueba(versiones_catalogo=("cat-2",)),
                                      encabezado_repro(version_catalogo="cat-1"))
        self.assertIn("cat-1", mensaje)

    def test_otra_cripta(self):
        RegistroPartida.crear(self.ruta(), Encabezado("otra-cripta", "v1", "cat-1", 1, "Ana"))
        preparador = PreparadorDePrueba()
        with self.assertRaises(ReproduccionIncompatible):
            Reproductor(preparador).reproducir(self.ruta())
        self.assertEqual(preparador.partidas_creadas, 0)

    def test_version_vieja_pero_con_copia_local(self):
        """Si el preparador la tiene (el servidor ya cambió, pero hay copia
        local de esa versión), se reproduce normalmente."""
        jugar_y_registrar(self.ruta(), comandos_guiados())
        preparador = PreparadorDePrueba(versiones_cripta=("v2", "v1"),
                                        versiones_catalogo=("cat-2", "cat-1"))
        self.assertEqual(Reproductor(preparador).reproducir(self.ruta()).partida.resultado,
                         "victoria")

    def test_a_la_copia_local_le_falta_una_sala(self):
        """Se descubre a mitad de camino: tampoco se sigue en silencio."""
        jugar_y_registrar(self.ruta(), comandos_guiados())
        with self.assertRaises(ReproduccionIncompatible):
            Reproductor(PreparadorDePrueba(falta_sala=2)).reproducir(self.ruta())


class TestReproduccionFallida(ConCarpetaTemporal):
    """Un comando que no se puede repetir: la reproducción se separó de la
    partida original (o el registro se editó a mano). Se para y dice dónde."""

    def registro(self, *comandos):
        registro = RegistroPartida.crear(self.ruta(), encabezado_repro())
        for comando in comandos:
            registro.anotar(comando)

    def fallar(self):
        with self.assertRaises(ReproduccionFallida) as error:
            Reproductor(PreparadorDePrueba()).reproducir(self.ruta())
        return error.exception

    def test_accion_que_no_se_puede(self):
        self.registro("recoger 0", "mover S", "esperar")        # no hay salida al sur
        error = self.fallar()
        self.assertEqual((error.numero, error.comando), (2, "mover S"))
        self.assertIn("mover S", str(error))
        self.assertIsInstance(error.__cause__, AccionInvalida)

    def test_comando_que_no_se_entiende(self):
        self.registro("esperar", "volar")
        error = self.fallar()
        self.assertEqual((error.numero, error.comando), (2, "volar"))
        self.assertIsInstance(error.__cause__, ComandoInvalido)

    def test_atacar_a_uno_que_no_esta(self):
        self.registro("atacar e-21")                            # está en otra sala
        self.assertEqual(self.fallar().numero, 1)

    def test_pergamino_que_no_se_puede_usar(self):
        self.registro("pergamino")                              # nada que deshacer
        self.assertEqual(self.fallar().comando, "pergamino")

    def test_comandos_despues_del_final(self):
        """Ni siquiera los que no son acciones (avanzar)."""
        guiados = anotados_guiados()
        self.registro(*guiados, "avanzar")
        error = self.fallar()
        self.assertEqual(error.numero, len(guiados) + 1)
        self.assertIn("terminado", str(error))


class TestPreparadorMalHecho(ConCarpetaTemporal):
    """Errores de programación del preparador (Fase 7), no del registro."""

    class Preparador(PreparadorDePrueba):
        def __init__(self, semilla=None, iniciada=False):
            super().__init__()
            self._semilla, self._iniciada = semilla, iniciada

        def crear_partida(self, encabezado):
            partida = super().crear_partida(encabezado)
            if self._semilla is not None:
                partida.semilla = self._semilla
            if self._iniciada:
                partida.iniciar()
            return partida

    def setUp(self):
        super().setUp()
        RegistroPartida.crear(self.ruta(), encabezado_repro())

    def test_otra_semilla(self):
        with self.assertRaises(ValueError):
            Reproductor(self.Preparador(semilla=1)).reproducir(self.ruta())

    def test_partida_ya_iniciada(self):
        with self.assertRaises(ValueError):
            Reproductor(self.Preparador(iniciada=True)).reproducir(self.ruta())


class TestCargarAntesDeMover(unittest.TestCase):
    """ejecutar_comando con garantizar_sala: así lo usan el controlador y
    el reproductor (§2.4)."""

    def setUp(self):
        self.preparador = PreparadorDePrueba()
        self.partida = self.preparador.crear_partida(encabezado_repro())
        self.partida.iniciar()

    def ejecutar(self, comando):
        return ejecutar_comando(self.partida, comando, self.preparador.garantizar_sala)

    def test_carga_el_destino_y_entra(self):
        self.ejecutar("mover O")
        self.assertEqual(self.preparador.salas_pedidas, [1, 3])
        self.assertEqual(self.partida.jugador.sala_actual, 3)

    def test_sin_garantizar_no_se_puede_entrar(self):
        """Por eso hace falta: sin el contenido, la partida no deja entrar."""
        with self.assertRaises(RuntimeError):
            ejecutar_comando(self.partida, "mover O")

    def test_no_carga_si_no_se_va_a_poder_entrar(self):
        for comando in ("mover S", "mover E", "volar", "mover X", "esperar", "abrir O"):
            try:
                self.ejecutar(comando)
            except (AccionInvalida, ComandoInvalido):
                pass
        self.ejecutar("mover N")
        self.assertEqual(self.preparador.salas_pedidas, [1, 2])
        with self.assertRaises(AccionInvalida):
            self.ejecutar("mover N")                     # cerrada con llave
        self.assertEqual(self.preparador.salas_pedidas, [1, 2])     # la 4 no

    def test_partida_terminada_no_carga(self):
        self.partida.terminada = True
        with self.assertRaises(RuntimeError):
            self.ejecutar("mover O")
        self.assertEqual(self.preparador.salas_pedidas, [1])


# ======================================================================
# 6.3  LA TABLA DE PUNTAJES (§2.12 y §4.9)
# ======================================================================

def puntaje(jugador, resultado, tiempo, acciones=10, enemigos=0, cripta="cripta-01"):
    return Puntaje(jugador, cripta, "v1", resultado, acciones, enemigos, tiempo)


def nombres(puntajes):
    """Los nombres, en orden: de la tabla (orden de registro) o de un
    Vector (como el que devuelve ranking)."""
    if isinstance(puntajes, TablaPuntajes):
        return [p.jugador for p in puntajes]
    return [puntajes.obtener(i).jugador for i in range(len(puntajes))]


def datos(p):
    return (p.jugador, p.cripta_id, p.version_cripta, p.resultado, p.acciones,
            p.enemigos, p.tiempo)


class TestPuntaje(ConCarpetaTemporal):
    def test_de_una_partida_terminada(self):
        """§2.12: nombre, id y versión de la cripta, acciones, enemigos
        derrotados y tiempo final (y el resultado)."""
        partida, _, _ = jugar_y_registrar(self.ruta(), comandos_guiados())
        p = puntaje_de(partida, "cripta-prueba", "v1")
        self.assertEqual(datos(p), ("Héroe", "cripta-prueba", "v1", VICTORIA,
                                    partida.acciones_jugador, partida.enemigos_derrotados,
                                    partida.reloj))
        self.assertEqual((p.acciones, p.enemigos), (18, 3))     # para que no sean ceros

    def test_partida_sin_terminar(self):
        with self.assertRaises(ValueError) as error:
            puntaje_de(partida_con_puertas(), "cripta-01", "v1")
        self.assertIn("terminadas", str(error.exception))

    def test_datos_invalidos(self):
        for argumentos in (
            ("Ana", "c", "v1", "empate", 1, 1, 1),        # resultado desconocido
            ("Ana", "c", "v1", VICTORIA, -1, 1, 1),       # acciones negativas
            ("Ana", "c", "v1", VICTORIA, 1, 1, "100"),    # tiempo que no es número
            ("Ana\tMaría", "c", "v1", VICTORIA, 1, 1, 1),  # tabulador en el nombre
            ("Ana", "c\n2", "v1", DERROTA, 1, 1, 1),       # salto de línea
            (None, "c", "v1", DERROTA, 1, 1, 1),          # el nombre no es texto
        ):
            with self.assertRaises(ValueError, msg=repr(argumentos)):
                Puntaje(*argumentos)


class TestRanking(unittest.TestCase):
    """Tabla solo en memoria: aquí lo que importa es el orden."""

    def tabla(self, *puntajes):
        tabla = TablaPuntajes()
        for p in puntajes:
            tabla.registrar(p)
        return tabla

    def test_victorias_primero_de_la_mas_rapida_a_la_mas_lenta(self):
        tabla = self.tabla(puntaje("lenta", VICTORIA, 900), puntaje("muerto", DERROTA, 50),
                           puntaje("rapida", VICTORIA, 300), puntaje("media", VICTORIA, 600))
        self.assertEqual(nombres(tabla.ranking()), ["rapida", "media", "lenta", "muerto"])

    def test_empates_entre_victorias(self):
        """Mismo tiempo: menos acciones; luego más enemigos; si todo empata,
        la que se registró primero."""
        tabla = self.tabla(puntaje("a", VICTORIA, 500, acciones=20),
                           puntaje("b", VICTORIA, 500, acciones=12, enemigos=1),
                           puntaje("c", VICTORIA, 500, acciones=12, enemigos=4),
                           puntaje("d", VICTORIA, 500, acciones=12, enemigos=4))
        self.assertEqual(nombres(tabla.ranking()), ["c", "d", "b", "a"])

    def test_derrotas_de_la_que_llego_mas_lejos(self):
        """Más enemigos derrotados; luego más tiempo sobrevivido; luego
        menos acciones."""
        tabla = self.tabla(puntaje("pronto", DERROTA, 100, enemigos=2),
                           puntaje("torpe", DERROTA, 900, acciones=40, enemigos=2),
                           puntaje("cazador", DERROTA, 50, enemigos=5),
                           puntaje("tarde", DERROTA, 900, enemigos=2),
                           puntaje("nadie", DERROTA, 2000))
        self.assertEqual(nombres(tabla.ranking()),
                         ["cazador", "tarde", "torpe", "pronto", "nadie"])

    def test_no_cambia_el_orden_de_registro(self):
        tabla = self.tabla(puntaje("b", VICTORIA, 900), puntaje("a", VICTORIA, 100))
        tabla.ranking()
        self.assertEqual(nombres(tabla), ["b", "a"])

    def test_por_cripta_y_los_primeros(self):
        tabla = self.tabla(puntaje("a", VICTORIA, 400, cripta="c1"),
                           puntaje("b", VICTORIA, 100, cripta="c2"),
                           puntaje("c", VICTORIA, 200, cripta="c1"),
                           puntaje("d", DERROTA, 100, cripta="c1"))
        self.assertEqual(nombres(tabla.ranking(cripta_id="c1")), ["c", "a", "d"])
        self.assertEqual(nombres(tabla.ranking(cripta_id="c1", limite=2)), ["c", "a"])
        self.assertEqual(nombres(tabla.ranking(limite=10)), ["b", "c", "a", "d"])
        self.assertEqual(len(tabla.ranking(cripta_id="otra")), 0)

    def test_tabla_vacia(self):
        self.assertEqual(len(TablaPuntajes().ranking()), 0)

    def test_tablas_al_azar(self):
        """Chicas (ordenar usa inserción) y grandes (mergesort): siempre del
        mejor al peor y, en un empate total, en el orden de registro."""
        azar = random.Random(63)
        for cantidad in (0, 1, 7, 24, 25, 120, 400):
            with self.subTest(cantidad=cantidad):
                tabla = TablaPuntajes()
                for i in range(cantidad):
                    tabla.registrar(puntaje(f"j{i}", azar.choice((VICTORIA, DERROTA)),
                                            azar.randint(0, 30) * 100, azar.randint(1, 3),
                                            azar.randint(0, 2)))
                orden = tabla.ranking()
                self.assertEqual(len(orden), cantidad)
                for i in range(len(orden) - 1):
                    antes, despues = orden.obtener(i), orden.obtener(i + 1)
                    self.assertLessEqual(antes.clave_ranking, despues.clave_ranking)
                    if antes.clave_ranking == despues.clave_ranking:
                        self.assertLess(int(antes.jugador[1:]), int(despues.jugador[1:]))


class TestTablaEnDisco(ConCarpetaTemporal):
    def setUp(self):
        super().setUp()
        self.archivo = self.ruta("puntajes.txt")

    def test_ida_y_vuelta(self):
        """Lo que se registra sigue ahí al abrir la tabla otra vez (al
        volver a abrir el programa), en el mismo orden."""
        tabla = TablaPuntajes(self.archivo)
        guardados = (puntaje("Ana María Núñez", VICTORIA, 700, 30, 2),
                     puntaje("  Bo  ", DERROTA, 250, 9, 0, cripta="otra"),
                     puntaje("", VICTORIA, 0, 0, 0))
        for p in guardados:
            tabla.registrar(p)

        otra_vez = TablaPuntajes(self.archivo)
        self.assertEqual([datos(p) for p in otra_vez], [datos(p) for p in guardados])
        self.assertEqual(nombres(otra_vez.ranking()), ["", "Ana María Núñez", "  Bo  "])

    def test_el_archivo_se_ve_asi(self):
        TablaPuntajes(self.archivo).registrar(puntaje("Héroe", VICTORIA, 1100, 18, 3))
        with open(self.archivo, encoding="utf-8") as archivo:
            self.assertEqual(archivo.read(),
                             "# CRIPTA tabla de puntajes\nformato 1\n---\n"
                             "victoria\t1100\t18\t3\tcripta-01\tv1\tHéroe\n")

    def test_solo_agrega_al_final(self):
        """Lo ya escrito nunca cambia, aunque se abra la tabla de nuevo."""
        TablaPuntajes(self.archivo).registrar(puntaje("a", VICTORIA, 500))
        with open(self.archivo, "rb") as archivo:
            antes = archivo.read()
        TablaPuntajes(self.archivo).registrar(puntaje("b", DERROTA, 100))
        with open(self.archivo, "rb") as archivo:
            despues = archivo.read()
        self.assertTrue(despues.startswith(antes))
        self.assertEqual(nombres(TablaPuntajes(self.archivo)), ["a", "b"])

    def test_todavia_no_existe(self):
        """Abrir no crea el archivo; se crea al registrar el primero."""
        tabla = TablaPuntajes(self.archivo)
        self.assertEqual(len(tabla), 0)
        self.assertFalse(os.path.exists(self.archivo))
        tabla.registrar(puntaje("a", VICTORIA, 500))
        self.assertTrue(os.path.exists(self.archivo))

    def test_archivo_vacio(self):
        """0 bytes (el programa se cerró justo al crearlo): tabla nueva."""
        open(self.archivo, "w").close()
        tabla = TablaPuntajes(self.archivo)
        self.assertEqual(len(tabla), 0)
        tabla.registrar(puntaje("a", VICTORIA, 500))
        self.assertEqual(nombres(TablaPuntajes(self.archivo)), ["a"])

    def test_registrar_una_partida(self):
        """Así lo hará el controlador al terminar la partida."""
        partida, _, _ = jugar_y_registrar(self.ruta(), comandos_guiados())
        TablaPuntajes(self.archivo).registrar_partida(partida, "cripta-prueba", "v1")
        primero = TablaPuntajes(self.archivo).ranking().obtener(0)
        self.assertEqual(datos(primero), datos(puntaje_de(partida, "cripta-prueba", "v1")))

    def test_un_dato_invalido_no_escribe_nada(self):
        tabla = TablaPuntajes(self.archivo)
        with self.assertRaises(ValueError):
            tabla.registrar_partida(partida_con_puertas(), "cripta-01", "v1")   # sin terminar
        self.assertFalse(os.path.exists(self.archivo))
        self.assertEqual(len(tabla), 0)


class TestTablaDanada(ConCarpetaTemporal):
    """Un archivo que no sirve se rechaza con un mensaje claro (no se
    pierden ni se inventan puntajes en silencio)."""

    ENCABEZADO = "# CRIPTA tabla de puntajes\nformato 1\n---\n"
    BUENA = "victoria\t500\t10\t1\tcripta-01\tv1\tAna\n"

    def abrir(self, texto):
        ruta = self.ruta("puntajes.txt")
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(texto)
        return TablaPuntajes(ruta)

    def rechaza(self, texto):
        with self.assertRaises(ErrorTablaPuntajes) as error:
            self.abrir(texto)
        return str(error.exception)

    def test_otro_archivo(self):
        self.rechaza("hola\n")

    def test_primera_linea_de_otro_programa(self):
        """Todo lo demás está bien; solo la marca no."""
        self.rechaza(self.ENCABEZADO.replace("# CRIPTA tabla de puntajes", "# otro programa")
                     + self.BUENA)

    def test_formato_distinto(self):
        self.assertIn("formato", self.rechaza(self.ENCABEZADO.replace("formato 1", "formato 2")))

    def test_sin_separador(self):
        self.rechaza(self.ENCABEZADO.replace("---\n", "") + self.BUENA)

    def test_faltan_datos(self):
        self.assertIn("Línea 5", self.rechaza(self.ENCABEZADO + self.BUENA +
                                               "victoria\t500\t10\t1\tcripta-01\tv1\n"))

    def test_sobran_datos(self):
        self.rechaza(self.ENCABEZADO + self.BUENA.replace("Ana", "Ana\tx"))

    def test_numero_que_no_es_numero(self):
        for malo in ("5OO", "-5", ""):
            with self.subTest(malo=malo):
                self.assertIn("Línea 4", self.rechaza(self.ENCABEZADO +
                                                       self.BUENA.replace("\t10\t", f"\t{malo}\t")))

    def test_resultado_desconocido(self):
        self.assertIn("Línea 4", self.rechaza(self.ENCABEZADO + self.BUENA.replace("victoria", "empate")))

    def test_lineas_vacias_se_ignoran(self):
        tabla = self.abrir(self.ENCABEZADO + "\n" + self.BUENA + "\n\n")
        self.assertEqual(nombres(tabla), ["Ana"])


if __name__ == "__main__":
    unittest.main()