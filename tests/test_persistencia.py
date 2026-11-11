"""Pruebas de la Fase 6 (persistencia), en un solo archivo, por pasos:

    6.1  comandos y registro de partida (§4.11)
    6.2  el reproductor: --replay (§4.11)
    6.3  la tabla de puntajes (§2.12 y §4.9)
    6.4  el guardado binario de la partida (§4.10)

Cómo correrlas, desde la carpeta raíz del proyecto:
    python -m unittest -v tests.test_persistencia
o todas las pruebas del proyecto:
    python -m unittest -v
"""

import copy
import json
import os
import random
import tempfile
import unittest

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Adaptadores.EstadoPartida import ErrorGuardado
from crypta.Adaptadores.GuardadoBinario import (
    ArchivoGuardado, FORMATO_GUARDADO, guardar_partida,
)
from crypta.Adaptadores.GuardadoJSON import ArchivoGuardadoJSON, guardar_partida_json
from crypta.Adaptadores.RegistroPartida import (
    Encabezado, ErrorRegistro, FORMATO_REGISTRO, RegistroPartida, leer_registro,
)
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Controlador.GestorCripta import GestorCripta
from crypta.Controlador.Reproductor import (
    Reproductor, ReproduccionFallida, ReproduccionIncompatible,
)
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Efecto import Efecto
from crypta.Modelo.Historial import Historial
from crypta.Modelo.Inventario import Inventario
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import (
    APAGAR_ANTORCHA, AccionInvalida, CIERRE_PUERTA, FIN_VELOCIDAD, PULSO_VENENO,
    Partida, REARME_TRAMPA, REGENERACION, TURNO_ENEMIGO,
)
from crypta.Modelo.Puerta import Puerta
from crypta.Modelo.Sala import Sala
from crypta.estructuras.Vector import Vector
from crypta.Modelo.TablaPuntajes import (
    DERROTA, ErrorTablaPuntajes, Puntaje, TablaPuntajes, VICTORIA, puntaje_de,
)
from tests.ayudas_cripta import (
    CRIPTA_ID, FuenteContadora, VERSION_CRIPTA, sala, salida,
)
from tests.test_partida import (
    CATALOGO, SEMILLA, enemigo, ids_inventario, partida_con_puertas, partida_de_dos_salas,
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
    - vida: la del jugador (las partidas al azar usan más, para durar).
    - esqueleto: otro mapa (el 6.4 usa uno con cierre automático)."""

    def __init__(self, cargar_todo=False, versiones_cripta=("v1",),
                 versiones_catalogo=("cat-1",), falta_sala=None, vida=60,
                 esqueleto=None):
        self._esqueleto = ESQUELETO_REPRO if esqueleto is None else esqueleto
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
        self._mapa.cargar_desde_json(self._esqueleto)

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

    def usar_mapa(self, mapa):
        """Para seguir una partida CARGADA: el contenido que falte se pone
        en el mapa de esa partida."""
        self._mapa = mapa

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


# ======================================================================
# 6.4  EL GUARDADO BINARIO DE LA PARTIDA (§4.10)
# ======================================================================

# El mapa del 6.2, pero la puerta Entrada -> Bodega (O) está cerrada y se
# vuelve a cerrar sola a los 2000: así hay un cierre automático pendiente.
ESQUELETO_GUARDADO = copy.deepcopy(ESQUELETO_REPRO)
ESQUELETO_GUARDADO[0]["salidas"]["O"] = {"sala": 3, "cerrada": True, "cierre_automatico": 2000}

# Lo que queda pendiente en partida_con_todo (el turno del jugador ya se
# sacó de la agenda: la partida está parada en su decisión).
TIPOS_PENDIENTES = {TURNO_ENEMIGO, REGENERACION, CIERRE_PUERTA, PULSO_VENENO,
                    FIN_VELOCIDAD, APAGAR_ANTORCHA, REARME_TRAMPA}

FORMATOS = (("binario", guardar_partida, ArchivoGuardado),
            ("json", guardar_partida_json, ArchivoGuardadoJSON))


def foto_sin_historial(partida, ids_salas=IDS_SALAS_REPRO):
    """Como foto(), pero la agenda se mira por sus eventos PENDIENTES (en
    orden de secuencia) y sin el historial: al cargar, el montículo no trae
    los cancelados (no van a ocurrir) y el historial empieza vacío. Mira
    además todo de las puertas, y que cada efecto apunte a su evento."""
    resultado = foto(partida, ids_salas)
    pendientes = list_de(partida.agenda.eventos_pendientes())
    resultado["agenda"] = [(evento(e), nombre_de(e.objetivo)) for e in pendientes]
    resultado["efectos_enlazados"] = all(e.objetivo.evento is e for e in pendientes
                                         if isinstance(e.objetivo, Efecto))
    resultado["puertas"] = [(i, d, partida.mapa.obtener_sala(i).obtener_puerta(d).llave,
                             partida.mapa.obtener_sala(i).obtener_puerta(d).cierre_automatico)
                            for i in ids_salas for d in "NSEO"
                            if partida.mapa.obtener_sala(i).obtener_puerta(d)]
    del resultado["historial"]
    return resultado


def tipos_pendientes(partida):
    pendientes = partida.agenda.eventos_pendientes()
    return {pendientes.obtener(i).tipo for i in range(len(pendientes))}


def ver_objeto(partida, id_objeto):
    """Mueve el inventario hasta ese objeto (como avanzar y retroceder)."""
    inventario = partida.jugador.inventario
    while inventario.retroceder() is not None:
        pass
    while inventario.actual()["id"] != id_objeto:
        if inventario.avanzar() is None:
            raise AssertionError(f"El jugador no tiene {id_objeto}")


def partida_con_todo():
    """(partida, preparador), parada en t=875 con TODO a la vez: veneno,
    antorcha, velocidad aumentada, un cierre automático, una trampa por
    rearmarse, un troll que regenera, enemigos activos en dos salas, arma
    equipada, objetos en el inventario y en el suelo, pergaminos, y dos
    salas (4 y 6) que todavía no se han cargado."""
    preparador = PreparadorDePrueba(esqueleto=ESQUELETO_GUARDADO, vida=150)
    partida = preparador.crear_partida(encabezado_repro())
    partida.iniciar()
    for comando in ("recoger 0", "equipar", "abrir O", "mover O", "atacar e-31", "atacar e-31",
                    "recoger 0", "recoger 0", "recoger 1", "mover E", "mover N", "mover E"):
        ejecutar_comando(partida, comando, preparador.garantizar_sala)
    ver_objeto(partida, "itm_antorcha")
    partida.usar()
    ver_objeto(partida, "itm_pocion_rapidez")
    partida.usar()
    return partida, preparador


def intentar(partida, preparador, comando):
    try:
        ejecutar_comando(partida, comando, preparador.garantizar_sala)
        return True
    except (ComandoInvalido, AccionInvalida):
        return False


def contenido_completo(contenido):
    """El contenido con sus tres listas, vengan o no en el JSON."""
    return {"sala": contenido["sala"], "objetos": list(contenido.get("objetos") or ()),
            "trampas": list(contenido.get("trampas") or ()),
            "enemigos": list(contenido.get("enemigos") or ())}


def foto_sala(sala):
    puertas = [(d, sala.obtener_puerta(d).sala_destino, sala.obtener_puerta(d).esta_cerrada(),
                sala.obtener_puerta(d).llave, sala.obtener_puerta(d).cierre_automatico)
               for d in "NSEO" if sala.obtener_puerta(d)]
    enemigos = [(e.id_instancia, e.tipo, e.vida_inicial, e.esta_activo(), e.vida, e.velocidad,
                 evento(e.evento_siguiente), evento(e.evento_regeneracion))
                for e in (sala.enemigo_en(i) for i in range(sala.cantidad_enemigos()))]
    return (sala.id, sala.nombre, puertas, sala.ultimo_rastro, sala.contenido_cargado(),
            sala.contenido and contenido_completo(sala.contenido),
            [sala.objeto_en(i) for i in range(sala.cantidad_objetos())],
            sala.cantidad_pergaminos(), sala.pergaminos_ya_apartados(),
            [(t.instancia, t.tipo, t.esta_activa()) for t in
             (sala.trampa_en(i) for i in range(sala.cantidad_trampas()))],
            enemigos)


def partida_grande(cantidad=300):
    """Un pasillo de 'cantidad' salas (1 - 2 - 3 - ...), todas cargadas,
    con objetos, trampas y enemigos; el jugador ya caminó un poco."""
    salas, contenidos = [], []
    for i in range(1, cantidad + 1):
        salidas = {}
        if i > 1:
            salidas["O"] = {"sala": i - 1}
        if i < cantidad:
            salidas["E"] = {"sala": i + 1}
        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})
        contenidos.append({"sala": i, "objetos": ["itm_daga"] * (i % 3),
                           "enemigos": [{"instancia": f"e-{i}", "tipo": "ent_lenta"}] if i % 4 == 0 else [],
                           "trampas": [{"instancia": f"t-{i}", "tipo": "trp_rapida"}] if i % 5 == 0 else []})
    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos(contenidos)
    jugador = Jugador("Héroe", vida_max=500, ataque=6, defensa=2, velocidad=100, inventario_max=6)
    partida = Partida(mapa, jugador, 1, CATALOGO.get, semilla=SEMILLA_REPRO)
    partida.iniciar()
    for _ in range(12):
        partida.mover("E")
    return partida


class TestGuardarYCargar(ConCarpetaTemporal):
    def guardar_y_cargar(self, partida, formato, fichas=CATALOGO_REPRO.get):
        nombre, guardar, Archivo = formato
        ruta = self.ruta(f"partida.{nombre}")
        guardar(partida, ruta, encabezado_repro(semilla=partida.semilla))
        return Archivo(ruta).cargar_partida(fichas)

    def test_queda_todo_igual(self):
        for formato in FORMATOS:
            with self.subTest(formato=formato[0]):
                partida, _ = partida_con_todo()
                self.assertEqual(tipos_pendientes(partida), TIPOS_PENDIENTES)   # sí hay de todo
                cargada = self.guardar_y_cargar(partida, formato)
                self.assertEqual(foto_sin_historial(cargada), foto_sin_historial(partida))

    def test_dos_trampas_en_una_sala(self):
        """Cada rearme vuelve a su trampa (se guarda la posición)."""
        for formato in FORMATOS:
            with self.subTest(formato=formato[0]):
                partida = partida_efectos(trampas_sala_2=("trp_dardos", "trp_rapida"), vida=30)
                partida.mover("N")
                self.assertEqual(len(partida.agenda.eventos_pendientes()), 2)
                nombre, guardar, Archivo = formato
                guardar(partida, self.ruta(nombre), encabezado_repro(semilla=SEMILLA))
                cargada = Archivo(self.ruta(nombre)).cargar_partida(CATALOGO.get)
                partida.estado.historial = Historial()
                for _ in range(4):
                    self.assertEqual(foto_sin_historial(cargada, (1, 2)),
                                     foto_sin_historial(partida, (1, 2)))
                    cargada.esperar()
                    partida.esperar()
                sala = cargada.mapa.obtener_sala(2)
                self.assertEqual([sala.trampa_en(i).esta_activa() for i in range(2)], [True, True])

    def test_seguir_jugando_da_lo_mismo(self):
        """Lo importante: cargar y seguir jugando es lo mismo que no haber
        guardado (con los mismos dados, §2.6). Al original se le vacía el
        historial, porque al cargar el historial empieza vacío."""
        comandos = (["esperar"] * 3 + ["atacar e-51", "pergamino", "atacar e-51", "atacar e-22",
                                       "mover O", "mover S", "mover O", "pergamino"] + ["esperar"] * 25)
        for formato in FORMATOS:
            with self.subTest(formato=formato[0]):
                partida, preparador = partida_con_todo()
                cargada = self.guardar_y_cargar(partida, formato)
                partida.estado.historial = Historial()
                otro = PreparadorDePrueba()
                otro.usar_mapa(cargada.mapa)

                for numero, comando in enumerate(comandos, 1):
                    self.assertEqual(intentar(cargada, otro, comando),
                                     intentar(partida, preparador, comando), f"comando {numero}")
                    self.assertEqual(foto_sin_historial(cargada), foto_sin_historial(partida),
                                     f"después del comando {numero} ({comando})")

                # Para que la prueba sirva: después de cargar ocurrió de todo.
                self.assertFalse(partida.terminada)
                self.assertEqual(tipos_pendientes(partida) & {CIERRE_PUERTA, PULSO_VENENO,
                                                              FIN_VELOCIDAD, APAGAR_ANTORCHA}, set())

    def test_partidas_al_azar(self):
        """Se guarda en un momento al azar de una partida al azar, se carga
        y se sigue con los mismos comandos: todo igual, paso por paso."""
        for semilla in range(6):
            for formato in FORMATOS:
                with self.subTest(semilla=semilla, formato=formato[0]):
                    comandos = comandos_al_azar(semilla, 250)
                    corte = random.Random(semilla).randint(0, 120)
                    preparador = PreparadorDePrueba(vida=200)
                    partida = preparador.crear_partida(encabezado_repro(semilla=semilla))
                    partida.iniciar()
                    for comando in comandos[:corte]:
                        if not partida.terminada:
                            intentar(partida, preparador, comando)

                    cargada = self.guardar_y_cargar(partida, formato)
                    self.assertEqual(foto_sin_historial(cargada), foto_sin_historial(partida))
                    partida.estado.historial = Historial()
                    otro = PreparadorDePrueba()
                    otro.usar_mapa(cargada.mapa)

                    for numero, comando in enumerate(comandos[corte:], 1):
                        if partida.terminada:
                            break
                        self.assertEqual(intentar(cargada, otro, comando),
                                         intentar(partida, preparador, comando))
                        self.assertEqual(foto_sin_historial(cargada), foto_sin_historial(partida),
                                         f"después del comando {numero} ({comando})")

    def test_guardar_lo_cargado_da_el_mismo_archivo(self):
        """Nada se pierde ni cambia de orden en el camino."""
        for nombre, guardar, Archivo in FORMATOS:
            with self.subTest(formato=nombre):
                partida, _ = partida_con_todo()
                guardar(partida, self.ruta("1"), encabezado_repro())
                cargada = Archivo(self.ruta("1")).cargar_partida(CATALOGO_REPRO.get)
                guardar(cargada, self.ruta("2"), encabezado_repro())
                with open(self.ruta("1"), "rb") as uno, open(self.ruta("2"), "rb") as dos:
                    self.assertEqual(uno.read(), dos.read())

    def test_el_historial_empieza_vacio(self):
        """Lo que NO se guarda: no se puede retroceder a antes de cargar.
        Los pergaminos sí se conservan, para usarlos desde ahí."""
        partida, _ = partida_con_todo()
        cargada = self.guardar_y_cargar(partida, FORMATOS[0])
        self.assertEqual(len(cargada.estado.historial), 0)
        self.assertEqual(cargada.jugador.inventario.cantidad_pergaminos(),
                         partida.jugador.inventario.cantidad_pergaminos())
        self.assertFalse(cargada.usar_pergamino())
        self.assertTrue(partida.usar_pergamino())

    def test_partida_terminada(self):
        original, _, _ = jugar_y_registrar(self.ruta(), comandos_guiados())
        for formato in FORMATOS:
            with self.subTest(formato=formato[0]):
                cargada = self.guardar_y_cargar(original, formato)
                self.assertEqual((cargada.terminada, cargada.resultado), (True, "victoria"))
                with self.assertRaises(RuntimeError):
                    cargada.esperar()

    def test_salas_y_puertas(self):
        """Las salas sin cargar siguen sin cargar; el contenido original
        (el que va a la caché) se conserva; las puertas siguen siendo UNA
        para las dos salas."""
        partida, _ = partida_con_todo()
        cargada = self.guardar_y_cargar(partida, FORMATOS[0])
        cargadas = [i for i in IDS_SALAS_REPRO if cargada.mapa.obtener_sala(i).contenido_cargado()]
        self.assertEqual(cargadas, [1, 2, 3, 5])
        for datos in CONTENIDO_REPRO:
            if datos["sala"] in cargadas:
                self.assertEqual(cargada.mapa.obtener_sala(datos["sala"]).contenido,
                                 contenido_completo(datos))

        oeste = cargada.mapa.obtener_sala(1).obtener_puerta("O")
        este = cargada.mapa.obtener_sala(3).obtener_puerta("E")
        self.assertIs(oeste.sala_destino_ref, cargada.mapa.obtener_sala(3))
        self.assertFalse(este.esta_cerrada())
        oeste.cerrar()
        self.assertTrue(este.esta_cerrada())

    def test_lo_que_dice_el_encabezado(self):
        partida, _ = partida_con_todo()
        for nombre, guardar, Archivo in FORMATOS:
            with self.subTest(formato=nombre):
                guardar(partida, self.ruta(nombre), encabezado_repro())
                encabezado = Archivo(self.ruta(nombre)).encabezado
                self.assertEqual((encabezado.cripta_id, encabezado.version_cripta,
                                  encabezado.version_catalogo, encabezado.semilla, encabezado.jugador),
                                 ("cripta-prueba", "v1", "cat-1", SEMILLA_REPRO, "Héroe"))

    def test_falta_una_ficha(self):
        """El catálogo de esa versión ya no está completo: se avisa."""
        partida, _ = partida_con_todo()
        sin_troll = dict(CATALOGO_REPRO)
        del sin_troll["ent_troll"]
        for formato in FORMATOS:
            with self.subTest(formato=formato[0]):
                with self.assertRaises(ErrorGuardado):
                    self.guardar_y_cargar(partida, formato, sin_troll.get)

    def test_guardar_encima(self):
        """La segunda vez reemplaza a la primera y no quedan temporales."""
        primera, _ = partida_con_todo()
        segunda, _ = partida_con_todo()
        segunda.esperar()
        for nombre, guardar, Archivo in FORMATOS:
            with self.subTest(formato=nombre):
                guardar(primera, self.ruta(nombre), encabezado_repro())
                guardar(segunda, self.ruta(nombre), encabezado_repro())
                self.assertEqual(Archivo(self.ruta(nombre)).cargar_partida(CATALOGO_REPRO.get).reloj,
                                 segunda.reloj)
        self.assertEqual(sorted(os.listdir(self.carpeta)), ["binario", "json"])


class TestGuardarMal(ConCarpetaTemporal):
    """Errores de quien llama: no se escribe nada."""

    def no_guarda(self, partida, encabezado):
        for nombre, guardar, _ in FORMATOS:
            with self.assertRaises(ValueError):
                guardar(partida, self.ruta(nombre), encabezado)
        self.assertEqual(os.listdir(self.carpeta), [])

    def test_sin_iniciar(self):
        self.no_guarda(PreparadorDePrueba().crear_partida(encabezado_repro()), encabezado_repro())

    def test_otra_semilla(self):
        self.no_guarda(partida_con_todo()[0], encabezado_repro(semilla=1))

    def test_otro_jugador(self):
        encabezado = encabezado_repro()
        encabezado.jugador = "Otro"
        self.no_guarda(partida_con_todo()[0], encabezado)


class TestLeerUnaSala(ConCarpetaTemporal):
    """§4.10: se puede recuperar UNA sala sin leer el archivo completo."""

    def guardar_grande(self):
        partida = partida_grande()
        guardar_partida(partida, self.ruta("p.bin"), encabezado_repro())
        guardar_partida_json(partida, self.ruta("p.json"), encabezado_repro())
        return partida

    def test_lee_solo_esa_sala(self):
        partida = self.guardar_grande()
        archivo = ArchivoGuardado(self.ruta("p.bin"))
        sala = archivo.leer_sala(240, CATALOGO.get)
        self.assertEqual(foto_sala(sala), foto_sala(partida.mapa.obtener_sala(240)))
        # Cabecera + encabezado + índice + ESA sala: mucho menos que todo.
        self.assertLess(archivo.bytes_leidos, archivo.tamano * 0.25)
        self.assertGreater(archivo.bytes_leidos, 300 * 20)        # al menos el índice

        # En cambio, cargar la partida lee cada byte del archivo una vez.
        completo = ArchivoGuardado(self.ruta("p.bin"))
        completo.cargar_partida(CATALOGO.get)
        self.assertEqual(completo.bytes_leidos, completo.tamano)

    def test_el_json_tiene_que_leer_todo(self):
        partida = self.guardar_grande()
        archivo = ArchivoGuardadoJSON(self.ruta("p.json"))
        self.assertEqual(foto_sala(archivo.leer_sala(240, CATALOGO.get)),
                         foto_sala(partida.mapa.obtener_sala(240)))
        self.assertEqual(archivo.bytes_leidos, archivo.tamano)

    def test_varias_salas_con_el_mismo_archivo(self):
        partida = self.guardar_grande()
        archivo = ArchivoGuardado(self.ruta("p.bin"))
        for id_sala in (1, 13, 300, 150, 2):
            self.assertEqual(foto_sala(archivo.leer_sala(id_sala, CATALOGO.get)),
                             foto_sala(partida.mapa.obtener_sala(id_sala)))
        self.assertEqual(list_de(archivo.ids_salas()), list(range(1, 301)))

    def test_sala_con_enemigos_activos(self):
        """Con sus eventos (tiempo, secuencia, tipo), aunque no haya agenda."""
        partida, _ = partida_con_todo()
        for nombre, guardar, Archivo in FORMATOS:
            with self.subTest(formato=nombre):
                guardar(partida, self.ruta(nombre), encabezado_repro())
                sala = Archivo(self.ruta(nombre)).leer_sala(5, CATALOGO_REPRO.get)
                self.assertEqual(foto_sala(sala), foto_sala(partida.mapa.obtener_sala(5)))
                self.assertEqual(sala.cantidad_enemigos(), 2)

    def test_sala_que_no_esta(self):
        self.guardar_grande()
        for Archivo, ruta in ((ArchivoGuardado, "p.bin"), (ArchivoGuardadoJSON, "p.json")):
            with self.assertRaises(KeyError):
                Archivo(self.ruta(ruta)).leer_sala(301, CATALOGO.get)


def list_de(vector):
    return [vector.obtener(i) for i in range(len(vector))]


class TestGuardadoDanado(ConCarpetaTemporal):
    """§4.10: detectar otra versión del formato; y un archivo dañado da
    ErrorGuardado con un mensaje claro, nunca otro error ni datos a medias."""

    def setUp(self):
        super().setUp()
        partida, _ = partida_con_todo()
        guardar_partida(partida, self.ruta("p.bin"), encabezado_repro())
        with open(self.ruta("p.bin"), "rb") as archivo:
            self.bytes = archivo.read()

    def con_bytes(self, datos):
        with open(self.ruta("malo.bin"), "wb") as archivo:
            archivo.write(datos)
        return self.ruta("malo.bin")

    def falla(self, datos):
        """ErrorGuardado al abrir o, si no, al leer las salas o cargar."""
        with self.assertRaises(ErrorGuardado) as error:
            archivo = ArchivoGuardado(self.con_bytes(datos))
            archivo.cargar_partida(CATALOGO_REPRO.get)
        return str(error.exception)

    def test_otra_version_del_formato(self):
        otra = (FORMATO_GUARDADO + 1).to_bytes(2, "little")
        mensaje = self.falla(self.bytes[:4] + otra + self.bytes[6:])
        self.assertIn("versión", mensaje)

    def test_no_es_un_guardado(self):
        self.assertIn("no es una partida guardada", self.falla(b"hola, esto no es una partida"))
        self.assertIn("no es una partida guardada", self.falla(b"CRPX" + self.bytes[4:]))
        self.falla(b"")
        with open(self.ruta("p.json"), "w") as archivo:
            archivo.write('{"formato": 1}')
        with self.assertRaises(ErrorGuardado):
            ArchivoGuardado(self.ruta("p.json"))

    def falla_al_abrir(self, datos):
        """Se detecta YA al abrir (no al leer la sala)."""
        with self.assertRaises(ErrorGuardado):
            ArchivoGuardado(self.con_bytes(datos))

    def test_indice_que_apunta_fuera_de_las_salas(self):
        """La primera entrada apunta al principio del archivo."""
        inicio = int.from_bytes(self.bytes[16:24], "little")
        self.falla_al_abrir(self.bytes[:inicio + 8] + (0).to_bytes(8, "little")
                            + self.bytes[inicio + 16:])

    def test_un_bloque_con_datos_de_mas(self):
        """Un byte de más al final del encabezado (y todo lo demás corrido
        para que cuadre): el encabezado no se leyó completo."""
        largo = int.from_bytes(self.bytes[8:12], "little")
        indice = int.from_bytes(self.bytes[16:24], "little")
        cantidad = int.from_bytes(self.bytes[24:28], "little")
        datos = bytearray(self.bytes[:28 + largo] + b"\0" + self.bytes[28 + largo:])
        datos[8:12] = (largo + 1).to_bytes(4, "little")
        datos[16:24] = (indice + 1).to_bytes(8, "little")
        for i in range(cantidad):
            posicion = indice + 1 + i * 20 + 8
            datos[posicion:posicion + 8] = (int.from_bytes(datos[posicion:posicion + 8], "little")
                                            + 1).to_bytes(8, "little")
        self.falla_al_abrir(bytes(datos))

    def test_no_existe(self):
        with self.assertRaises(ErrorGuardado):
            ArchivoGuardado(self.ruta("no_existe.bin"))

    def test_cortado_en_cualquier_parte(self):
        for corte in range(0, len(self.bytes), 7):
            with self.subTest(corte=corte):
                self.falla(self.bytes[:corte])

    def test_bytes_de_mas(self):
        self.falla(self.bytes + b"\0")

    def test_dato_imposible(self):
        """El primer dato de lo general es un booleano: un 7 no es ni 0 ni 1.
        (Inicio 6 bytes + cabecera 22 = 28; luego el encabezado.)"""
        largo_encabezado = int.from_bytes(self.bytes[8:12], "little")
        posicion = 28 + largo_encabezado
        self.assertIn(self.bytes[posicion], (0, 1))
        self.falla(self.bytes[:posicion] + b"\x07" + self.bytes[posicion + 1:])

    def test_indice_desordenado(self):
        """Se intercambian las dos primeras entradas del índice."""
        inicio = int.from_bytes(self.bytes[16:24], "little")
        primera, segunda = self.bytes[inicio:inicio + 20], self.bytes[inicio + 20:inicio + 40]
        self.falla(self.bytes[:inicio] + segunda + primera + self.bytes[inicio + 40:])

    def test_indice_que_no_cuadra_con_la_sala(self):
        """La última entrada dice sala 99, pero su registro es de la 6."""
        final = len(self.bytes) - 20
        self.falla(self.bytes[:final] + (99).to_bytes(8, "little") + self.bytes[final + 8:])
        archivo = ArchivoGuardado(self.ruta("malo.bin"))
        with self.assertRaises(ErrorGuardado):
            archivo.leer_sala(99, CATALOGO_REPRO.get)

    def test_json_danado(self):
        partida, _ = partida_con_todo()
        guardar_partida_json(partida, self.ruta("p.json"), encabezado_repro())
        with open(self.ruta("p.json"), encoding="utf-8") as archivo:
            documento = json.load(archivo)

        def falla(cambio):
            copia = copy.deepcopy(documento)
            cambio(copia)
            with open(self.ruta("malo.json"), "w", encoding="utf-8") as archivo:
                json.dump(copia, archivo)
            with self.assertRaises(ErrorGuardado) as error:
                ArchivoGuardadoJSON(self.ruta("malo.json")).cargar_partida(CATALOGO_REPRO.get)
            return str(error.exception)

        def troll(d):
            return d["salas"][4]["enemigos"][0]

        self.assertEqual(troll(documento)["instancia"], "e-51")
        self.assertIn("versión", falla(lambda d: d.update(formato=d["formato"] + 1)))
        # Un enemigo apunta a su turno con otro tiempo, o al de otro enemigo.
        falla(lambda d: troll(d)["turno"].update(tiempo=troll(d)["turno"]["tiempo"] + 1))
        falla(lambda d: troll(d)["turno"].update(secuencia=d["salas"][4]["enemigos"][1]["turno"]["secuencia"]))
        # Pendiente pero cancelado: imposible.
        falla(lambda d: troll(d)["turno"].update(valido=False))
        # La agenda fuera de orden (se avisa eso, no otra cosa).
        self.assertIn("orden", falla(lambda d: d["general"]["agenda"]["eventos"].reverse()))
        falla(lambda d: d["general"].pop("reloj"))
        falla(lambda d: d["general"].update(reloj="mucho"))
        falla(lambda d: d["salas"][0]["enemigos"].append("de más"))
        with open(self.ruta("malo.json"), "w", encoding="utf-8") as archivo:
            archivo.write("{esto no es json")
        with self.assertRaises(ErrorGuardado):
            ArchivoGuardadoJSON(self.ruta("malo.json"))


class TestComparacionConJSON(ConCarpetaTemporal):
    """§4.10: comparar tamaño en disco y tiempo de carga contra JSON. Los
    tiempos se miden con python -m crypta.bench.bench (en una prueba no se
    puede exigir un tiempo: depende de la máquina)."""

    def test_el_binario_ocupa_menos(self):
        for partida in (partida_con_todo()[0], partida_grande()):
            guardar_partida(partida, self.ruta("p.bin"), encabezado_repro())
            guardar_partida_json(partida, self.ruta("p.json"), encabezado_repro())
            self.assertLess(os.path.getsize(self.ruta("p.bin")), os.path.getsize(self.ruta("p.json")))

    def test_comparar_formatos(self):
        from crypta.bench.bench import comparar_formatos
        partida, _ = partida_con_todo()
        medida = comparar_formatos(partida, encabezado_repro(), CATALOGO_REPRO.get,
                                   self.carpeta, repeticiones=1)
        self.assertEqual(medida.tamano_binario, os.path.getsize(self.ruta("partida.bin")))
        self.assertEqual(medida.tamano_json, os.path.getsize(self.ruta("partida.json")))
        self.assertLess(medida.bytes_una_sala_binario, medida.tamano_binario)
        self.assertEqual(medida.bytes_una_sala_json, medida.tamano_json)
        for tiempo in (medida.carga_binario, medida.carga_json,
                       medida.una_sala_binario, medida.una_sala_json):
            self.assertGreater(tiempo, 0)
        self.assertIn("binario", str(medida))


class TestPiezasDelGuardado(unittest.TestCase):
    """Lo que se agregó a las clases del modelo para guardar y cargar."""

    def test_agenda_pendientes_en_orden_de_secuencia(self):
        agenda = Agenda()
        a, b, c = agenda.programar(300, "x"), agenda.programar(100, "y"), agenda.programar(200, "z")
        agenda.cancelar(b)
        self.assertEqual([e.secuencia for e in list_de(agenda.eventos_pendientes())],
                         [a.secuencia, c.secuencia])
        self.assertEqual(agenda.siguiente_secuencia, 3)

    def test_agenda_restaurar(self):
        agenda = Agenda()
        agenda.restaurar_secuencia(10)
        with self.assertRaises(ValueError):
            agenda.restaurar_pendiente(5, 10, "x", None)      # la secuencia tiene que ser < 10
        viejo = agenda.restaurar_pendiente(50, 7, "x", None)
        nuevo = agenda.programar(50, "y")
        self.assertEqual((nuevo.secuencia, len(agenda)), (10, 2))
        self.assertIs(agenda.siguiente(), viejo)              # mismo tiempo: gana la secuencia 7
        with self.assertRaises(ValueError):
            agenda.restaurar_secuencia(20)                    # ya no es nueva
        with self.assertRaises(ValueError):
            Agenda().restaurar_secuencia(-1)

    def test_inventario_posiciones_y_restaurar(self):
        daga, cota, pocion = CATALOGO["itm_daga"], CATALOGO["itm_cota"], CATALOGO["itm_pocion_menor"]
        self.assertEqual(Inventario(5).posiciones(), (-1, -1, -1))
        inventario = Inventario(5)
        inventario.restaurar(vector_de([pocion, cota, daga]), 1, 2, 1, 2)
        self.assertEqual(inventario.posiciones(), (1, 2, 1))
        self.assertEqual((inventario.actual(), inventario.arma(), inventario.armadura()),
                         (cota, daga, cota))
        self.assertEqual(inventario.cantidad_pergaminos(), 2)

        for argumentos in ((vector_de([daga]), 0, -1, -1, 0),        # no está vacío
                           ):
            with self.assertRaises(ValueError):
                inventario.restaurar(*argumentos)
        for objetos, actual, arma, armadura, pergaminos in (
                ([daga], 1, -1, -1, 0),            # fuera
                ([daga], 0, -1, 0, 0),             # una daga no es armadura
                ([daga], -1, -1, -1, 0),           # con objetos, uno a la vista
                ([], 0, -1, -1, 0),                # sin objetos, ninguno
                ([daga, cota], 0, -1, -1, 4),      # no caben
                ([daga] * 6, 0, -1, -1, 0)):       # no caben
            with self.assertRaises(ValueError, msg=repr((objetos, actual, arma, armadura))):
                Inventario(5).restaurar(vector_de(objetos), actual, arma, armadura, pergaminos)

    def test_mapa_con_salas_repetidas(self):
        with self.assertRaises(ValueError):
            Mapa().cargar_salas(vector_de([Sala(1, "a", None), Sala(1, "b", None)]))

    def test_evento_suelto_cancelado(self):
        """Un objeto que apunta a un evento cancelado (fuera de la agenda):
        se vuelve a crear cancelado."""
        partida, _ = partida_con_todo()
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = os.path.join(carpeta, "p.json")
            guardar_partida_json(partida, ruta, encabezado_repro())
            with open(ruta, encoding="utf-8") as archivo:
                documento = json.load(archivo)
            regeneracion = documento["salas"][4]["enemigos"][0]["regeneracion"]
            regeneracion.update(pendiente=False, valido=False)
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(documento, archivo)
            cargada = ArchivoGuardadoJSON(ruta).cargar_partida(CATALOGO_REPRO.get)
        troll = cargada.mapa.obtener_sala(5).enemigo_en(0)
        self.assertFalse(troll.evento_regeneracion.esta_valido())
        self.assertEqual(troll.evento_regeneracion.secuencia, regeneracion["secuencia"])

    def test_sala_poner_puerta_y_restaurar(self):
        sala = Sala(1, "a", None)
        sala.poner_puerta("N", Puerta(2))
        for direccion in ("N", "X"):
            with self.assertRaises(ValueError):
                sala.poner_puerta(direccion, Puerta(3))
        sala.restaurar_contenido({"sala": 1}, Vector(), Vector(), 2, True)
        self.assertEqual((sala.cantidad_pergaminos(), sala.pergaminos_ya_apartados()), (2, True))
        with self.assertRaises(ValueError):
            sala.restaurar_contenido({"sala": 1}, Vector(), Vector(), 0, False)
        with self.assertRaises(ValueError):
            Sala(2, "b", None).restaurar_contenido({"sala": 2}, Vector(), Vector(), -1, False)


def vector_de(elementos):
    vector = Vector()
    for elemento in elementos:
        vector.agregar(elemento)
    return vector


class TestCopiaLocalDeOtraVersion(ConCarpetaTemporal):
    """FR-025, FR-027, HU1-11 (tarea T025): una copia local del esqueleto de
    la primera parte, con otra versión de cripta, se invalida sola; se
    descarga el esqueleto nuevo con sus costos y se guarda con su versión,
    sin solicitudes de más."""

    def setUp(self):
        super().setUp()

        self.cripta_id = CRIPTA_ID
        self.version = VERSION_CRIPTA

        # Lo que guardó la primera parte: sin costos y con otra versión.
        self.almacen = AlmacenDisco(self.ruta("cache"))
        self.almacen.guardar_cripta(
            CRIPTA_ID, "v-primera-parte",
            [sala(1, {"E": salida(2)}), sala(2, {"O": salida(1)})], [])

        # Lo que entrega hoy el servicio: la misma cripta con costos.
        self.fuente = FuenteContadora(
            [sala(1, {"E": salida(2, costo=250)}),
             sala(2, {"O": salida(1, costo=250)})])

    def test_fr025_la_copia_vieja_se_reemplaza_por_la_nueva(self):
        """FR-025: el mapa trae los costos nuevos y queda guardado con la
        versión nueva, sin borrar archivos a mano."""
        gestor = GestorCripta(self.fuente, self.almacen)

        datos, mapa, desde_copia = gestor.cargar(self.cripta_id)

        self.assertFalse(desde_copia)
        self.assertEqual(
            mapa.obtener_sala(1).obtener_puerta("E").costo, 250)

        gestor.persistir(self.cripta_id, datos, mapa)

        self.assertIsNone(
            self.almacen.cargar_cripta(self.cripta_id, "v-primera-parte"))
        guardada = self.almacen.cargar_cripta(self.cripta_id, self.version)
        self.assertIsNotNone(guardada)
        self.assertEqual(
            guardada["esqueleto"][0]["salidas"]["E"]["costo"], 250)

    def test_fr027_sin_solicitudes_nuevas(self):
        """FR-027: los mismos pedidos que en P1 (datos generales y una
        página de salas); con la copia nueva, ninguna página más."""
        gestor = GestorCripta(self.fuente, self.almacen)
        datos, mapa, _ = gestor.cargar(self.cripta_id)
        gestor.persistir(self.cripta_id, datos, mapa)

        self.assertEqual(self.fuente.por_operacion,
                         {"obtener_cripta": 1, "obtener_pagina_salas": 1})

        _, mapa, desde_copia = GestorCripta(
            self.fuente, self.almacen).cargar(self.cripta_id)

        self.assertTrue(desde_copia)
        self.assertEqual(
            mapa.obtener_sala(2).obtener_puerta("O").costo, 250)
        self.assertEqual(self.fuente.por_operacion,
                         {"obtener_cripta": 2, "obtener_pagina_salas": 1})


class TestGuardadoConCazadores(ConCarpetaTemporal):
    """FR-026, HU3-8 (tarea T064): guardar y cargar una partida con costos y
    cazadores conserva todo lo que importa y la partida sigue igual que sin
    guardar. El rango no se guarda: sale de la ficha."""

    def setUp(self):
        super().setUp()
        from tests.ayudas_cripta import (
            catalogo, contenido, ficha_cazador, ficha_errante,
            partida_sintetica, sala, salida,
        )

        self.fichas = catalogo(ficha_cazador(rango=700, ataque=2),
                               ficha_errante(ataque=1))
        esqueleto = [
            sala(1, {"E": salida(2, costo=250), "S": salida(4)}),
            sala(2, {"O": salida(1), "E": salida(3, costo=150)}),
            sala(3, {"O": salida(2), "S": salida(4, costo=100),
                     "N": salida(5, costo=40)}),       # 3 —N→ 5 sin vuelta
            sala(4, {"N": salida(3), "O": salida(1, costo=300)}),
            sala(5),
        ]
        self.partida = partida_sintetica(
            esqueleto,
            [contenido(3, enemigos=[("c-1", "ent_cazador"),
                                    ("e-1", "ent_errante")])],
            self.fichas, sala_inicial=3)
        self.encabezado = Encabezado("cripta-prueba", "v-prueba", "c-prueba",
                                     self.partida.semilla, "Héroe")

        # Se juega un poco: el cazador y el errante despiertan en la 3.
        self.partida.mover("S")
        self.partida.esperar()
        self.partida.mover("O")
        self.partida.esperar()

    def foto(self, partida):
        """Todo lo que se compara de una partida con cazadores."""
        jugador = partida.jugador
        enemigos = []
        costos = []
        salas = partida.mapa.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            for direccion in "NSEO":
                puerta = sala.obtener_puerta(direccion)
                if puerta is not None:
                    costos.append((sala.id, direccion, puerta.costo,
                                   puerta.esta_cerrada()))

            for j in range(sala.cantidad_enemigos()):
                enemigo = sala.enemigo_en(j)
                evento = enemigo.evento_siguiente
                enemigos.append((enemigo.id_instancia, sala.id, enemigo.vida,
                                 enemigo.rango, enemigo.esta_activo(),
                                 None if evento is None else evento.tiempo))

        return (partida.reloj, jugador.sala_actual, jugador.vida,
                partida.terminada, tuple(costos), tuple(enemigos),
                tuple(partida.bitacora), partida.azar.getstate())

    def continuar(self, partida):
        for comando in (partida.esperar, lambda: partida.mover("E"),
                        partida.esperar, partida.esperar,
                        lambda: partida.mover("E"), partida.esperar):
            if partida.terminada:
                break
            comando()

    def guardar_y_cargar(self, formato):
        if formato == "binario":
            guardar_partida(self.partida, self.ruta("p.cripta"),
                            self.encabezado)
            return ArchivoGuardado(self.ruta("p.cripta")).cargar_partida(
                self.fichas.get)

        guardar_partida_json(self.partida, self.ruta("p.json"),
                             self.encabezado)
        return ArchivoGuardadoJSON(self.ruta("p.json")).cargar_partida(
            self.fichas.get)

    def test_fr026_se_conserva_todo_y_sigue_igual(self):
        """FR-026, HU3-8: costos, sala, vida, rango y próxima acción; y la
        partida cargada sigue igual que la original (FR-019, FR-021)."""
        for formato in ("binario", "json"):
            with self.subTest(formato=formato):
                cargada = self.guardar_y_cargar(formato)

                self.assertEqual(self.foto(cargada), self.foto(self.partida))

                cazador = next(e for e in self.foto(cargada)[5]
                               if e[0] == "c-1")
                self.assertEqual(cazador[3], 700)          # rango de la ficha

        # Las dos siguen igual (la original se juega una sola vez, al final).
        cargada = self.guardar_y_cargar("binario")
        self.continuar(cargada)
        self.continuar(self.partida)
        self.assertEqual(self.foto(cargada), self.foto(self.partida))
        self.assertIsNot(cargada.perseguidor(), self.partida.perseguidor())

    def test_fr026_la_partida_cargada_tiene_su_propio_perseguidor(self):
        """FR-019, FR-026 (T070): la partida cargada crea su perseguidor y lo
        registra en sus propias puertas, no en las de la original."""
        original = self.partida.perseguidor()
        cargada = self.guardar_y_cargar("binario")
        nuevo = cargada.perseguidor()

        self.assertIsNot(nuevo, original)
        salas = cargada.mapa.obtener_todas()
        for i in range(len(salas)):
            puertas = salas.obtener(i).puertas()
            for j in range(len(puertas)):
                self.assertIs(puertas.obtener(j).estado.observador, nuevo)

    def test_fr026_el_formato_1_se_rechaza(self):
        """FR-026: un archivo con formato 1 no se carga en silencio."""
        guardar_partida(self.partida, self.ruta("p.cripta"), self.encabezado)
        with open(self.ruta("p.cripta"), "rb") as archivo:
            datos = archivo.read()

        with open(self.ruta("viejo.cripta"), "wb") as archivo:
            archivo.write(datos[:4] + (1).to_bytes(2, "little") + datos[6:])

        with self.assertRaises(ErrorGuardado) as error:
            ArchivoGuardado(self.ruta("viejo.cripta"))

        self.assertEqual(FORMATO_GUARDADO, 2)
        self.assertEqual(
            str(error.exception),
            "La partida se guardó con la versión 1 del formato y este "
            "programa lee la versión 2: no se puede cargar")

    def test_fr026_el_formato_json_tambien_subio(self):
        """FR-026: el JSON del --bench sube de versión y rechaza el 1."""
        from crypta.Adaptadores.GuardadoJSON import FORMATO_JSON
        self.assertEqual(FORMATO_JSON, 2)

        guardar_partida_json(self.partida, self.ruta("p.json"),
                             self.encabezado)
        with open(self.ruta("p.json"), encoding="utf-8") as archivo:
            documento = json.load(archivo)
        documento["formato"] = 1
        with open(self.ruta("p.json"), "w", encoding="utf-8") as archivo:
            json.dump(documento, archivo)

        with self.assertRaises(ErrorGuardado):
            ArchivoGuardadoJSON(self.ruta("p.json"))

    def test_fr026_rango_invalido_es_error_de_guardado(self):
        """FR-011, FR-026: si al cargar la ficha del cazador trae un rango
        inválido, es ErrorGuardado (no DatosInvalidos)."""
        from crypta.Modelo.DatosInvalidos import DatosInvalidos
        from tests.ayudas_cripta import ficha_cazador

        guardar_partida(self.partida, self.ruta("p.cripta"), self.encabezado)
        malas = dict(self.fichas)
        malas["ent_cazador"] = ficha_cazador(rango=-1)

        with self.assertRaises(ErrorGuardado) as error:
            ArchivoGuardado(self.ruta("p.cripta")).cargar_partida(malas.get)

        self.assertNotIsInstance(error.exception, DatosInvalidos)
        self.assertIn("rango inválido", str(error.exception))

    def test_fr026_costos_distintos_en_los_dos_lados(self):
        """FR-010, FR-026: un archivo con los dos lados de una puerta con
        costos distintos está dañado: ErrorGuardado (no DatosInvalidos)."""
        from crypta.Modelo.DatosInvalidos import DatosInvalidos

        guardar_partida_json(self.partida, self.ruta("p.json"),
                             self.encabezado)
        with open(self.ruta("p.json"), encoding="utf-8") as archivo:
            documento = json.load(archivo)

        cambiadas = 0
        for sala in documento["salas"]:
            for puerta in sala["puertas"]:
                if sala["id"] == 2 and puerta["direccion"] == "O":
                    puerta["costo"] = 999
                    cambiadas += 1
        self.assertEqual(cambiadas, 1)

        with open(self.ruta("p.json"), "w", encoding="utf-8") as archivo:
            json.dump(documento, archivo)

        with self.assertRaises(ErrorGuardado) as error:
            ArchivoGuardadoJSON(self.ruta("p.json")).cargar_partida(
                self.fichas.get)

        self.assertNotIsInstance(error.exception, DatosInvalidos)
        self.assertIn("costos distintos", str(error.exception))

    def test_fr026_costo_invalido_en_el_archivo(self):
        """FR-026: un costo < 1 en el archivo es ErrorGuardado."""
        guardar_partida_json(self.partida, self.ruta("p.json"),
                             self.encabezado)
        with open(self.ruta("p.json"), encoding="utf-8") as archivo:
            documento = json.load(archivo)

        documento["salas"][0]["puertas"][0]["costo"] = 0
        with open(self.ruta("p.json"), "w", encoding="utf-8") as archivo:
            json.dump(documento, archivo)

        with self.assertRaises(ErrorGuardado):
            ArchivoGuardadoJSON(self.ruta("p.json")).cargar_partida(
                self.fichas.get)


if __name__ == "__main__":
    unittest.main()
