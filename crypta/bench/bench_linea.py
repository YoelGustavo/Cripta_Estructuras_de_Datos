"""--bench de la línea de tiempo (capacidad 004; specs/004-linea-de-tiempo/
contracts/bench.md, FR-427 a FR-434).

Secciones L1 a L8 (las registra `crypta/bench/bench.py` como `linea_l1` …
`linea_l8`). Sin vista ni red (FR-431): las partidas se arman en memoria o
desde la copia local, que se lee con `json` sin pasar por ninguna fuente.

Los tiempos se miden con `tracemalloc` apagado; la memoria, aparte, con
`tracemalloc` encendido y sin medir tiempos (contracts/bench.md).

Los `dict` de este archivo son datos con forma de JSON (contenido, fichas)
que se traducen a nuestras estructuras, como en los otros bench.
"""

import copy
import gc
import hashlib
import json
import os
import random
import sys
import tempfile
import time
import tracemalloc

from crypta.Adaptadores.EstadoPartida import (
    armar_partida, escribir_general, escribir_sala, leer_general, leer_sala,
)
from crypta.Adaptadores.GuardadoBinario import (
    ArchivoGuardado, EscritorBinario, LectorBinario, guardar_partida,
)
from crypta.Adaptadores.RegistroPartida import Encabezado
from crypta.Controlador.Comandos import (
    ComandoInvalido, ejecutar_comando, ejecutar_y_registrar,
)
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.LineaDeTiempo import ACCION, K_POR_DEFECTO, LineaDeTiempo
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida
from crypta.Modelo.Puerta import EstadoPuerta
from crypta.Modelo.Reconstruccion import Sello, _reejecutar, consultar
from crypta.Modelo.Resumen import armar_resumen
from crypta.Modelo.Sala import Sala
from crypta.Vista.FormatoResumen import formatear_resumen
from crypta.bench.bench_ciclo import (
    LIMITE_MS, Medicion, _activar_salas_con_cazadores, _ficha_cazador_bench,
    _fichas_en_arbol,
)
from crypta.bench.medicion import cronometrar, formato_tiempo, medir, tabla
from crypta.bench.oraculo_linea import Oraculo, serializar_estado
from crypta.estructuras.Vector import Vector


# Parámetros de medición (contracts/bench.md), no datos de una cripta.
LIMITE_HISTORIA_MS = 50
SEMILLA = 2026
SALAS_REFERENCIA = 300
ENEMIGOS_REFERENCIA = 20
SALAS_ESCALA = 2000
CAZADORES_ESCALA = 50
ACCIONES_REFERENCIA = 5000
ACCIONES_ESCALA = 1000
ACCIONES_L3 = 1000
ACCIONES_L4 = 500
CALENTAMIENTO_L4 = 20
INTERVALO_PERGAMINO = 50
CONSULTAS = 200
CONSULTAS_SIN_PUNTOS = 20
COMPARADAS_L3 = 300
VALORES_K = (10, 16, 22, 32, 64)
VALORES_K_RAPIDO = (5, K_POR_DEFECTO)
CARPETA_COPIAS = "cache"

# La consulta elegida; L3 la compara con todo. Una prueba la reemplaza por
# una saboteada para comprobar que L3 la detecta (HU5-6).
CONSULTAR_ADELANTE = consultar

_OBJETOS = (
    {"id": "itm_espada_l", "clase": "arma", "nombre": "Espada", "peso": 3,
     "valor": 5, "ataque_bonus": 3},
    {"id": "itm_escudo_l", "clase": "armadura", "nombre": "Escudo", "peso": 4,
     "valor": 4, "defensa_bonus": 2},
    {"id": "itm_pocion_l", "clase": "pocion", "nombre": "Poción", "peso": 1,
     "valor": 2, "cura": 10},
    {"id": "itm_rapida_l", "clase": "pocion", "nombre": "Poción rápida", "peso": 1,
     "valor": 3, "cura": 1, "modificador_velocidad": 40, "duracion": 300},
    {"id": "itm_antorcha_l", "clase": "antorcha", "nombre": "Antorcha", "peso": 1,
     "valor": 1, "duracion": 500},
    {"id": "itm_llave_l", "clase": "llave", "nombre": "Llave", "peso": 0, "valor": 1},
    {"id": "itm_pergamino_l", "clase": "pergamino_retroceso", "nombre": "Pergamino",
     "peso": 0, "valor": 1},
)
_ENEMIGOS = (
    {"id": "ent_errante_l", "clase": "enemigo", "nombre": "Murciélago",
     "vida_max": 10 ** 6, "ataque": 3, "defensa": 1, "velocidad": 110,
     "comportamiento": "errante", "suelta": []},
    {"id": "ent_rastreador_l", "clase": "enemigo", "nombre": "Rata",
     "vida_max": 10 ** 6, "ataque": 2, "defensa": 1, "velocidad": 130,
     "comportamiento": "rastreador", "suelta": []},
    {"id": "ent_guardian_l", "clase": "enemigo", "nombre": "Guardián",
     "vida_max": 10 ** 6, "ataque": 4, "defensa": 2, "velocidad": 90,
     "comportamiento": "guardián", "suelta": []},
)
_PERGAMINO = "itm_pergamino_l"


# ======================================================================
# Generador (FR-427)
# ======================================================================

def _objetos_de_sala(azar):
    objetos = []
    r = azar.random()

    if r < 0.08:
        objetos.append("itm_espada_l")
    elif r < 0.14:
        objetos.append("itm_escudo_l")
    elif r < 0.26:
        objetos.append("itm_pocion_l")
    elif r < 0.30:
        objetos.append("itm_rapida_l")
    elif r < 0.33:
        objetos.append("itm_antorcha_l")

    if azar.random() < 0.30:
        objetos.extend([_PERGAMINO, _PERGAMINO])

    return objetos


def _cuadricula(salas, azar):
    """Esqueleto en cuadrícula con costos variables y puertas abiertas,
    cerradas y con llave. Cada salida se escribe igual en los dos lados."""
    ancho = int(salas ** 0.5) + 1
    salidas = [{} for _ in range(salas)]

    def unir(a, b, ida, vuelta):
        costo = azar.randint(20, 300)
        r = azar.random()
        datos = {"costo": costo}

        if r < 0.12:
            datos["cerrada"] = True
        elif r < 0.15:
            datos["cerrada"] = True
            datos["llave"] = "itm_llave_l"

        salidas[a - 1][ida] = dict(datos, sala=b)
        salidas[b - 1][vuelta] = dict(datos, sala=a)

    for i in range(1, salas + 1):
        columna = (i - 1) % ancho

        if columna + 1 < ancho and i + 1 <= salas:
            unir(i, i + 1, "E", "O")
        if i + ancho <= salas:
            unir(i, i + ancho, "S", "N")

    return [{"id": i, "nombre": f"Sala {i}", "salidas": salidas[i - 1]}
            for i in range(1, salas + 1)]


def _jugador():
    return Jugador("Bench", vida_max=10 ** 9, ataque=8, defensa=3, velocidad=100,
                   inventario_max=12)


def _partida_sintetica(semilla):
    """(a) sin copia local: 300 salas y 20 enemigos activos repartidos."""
    azar = random.Random(semilla)
    esqueleto = _cuadricula(SALAS_REFERENCIA, azar)
    contenidos = [{"sala": datos["id"], "objetos": _objetos_de_sala(azar),
                   "trampas": [], "enemigos": []} for datos in esqueleto]
    contenidos[azar.randrange(1, len(contenidos))]["objetos"].append("itm_llave_l")

    salas_con_enemigo = azar.sample(range(1, len(contenidos)), ENEMIGOS_REFERENCIA)
    for i, indice in enumerate(salas_con_enemigo):
        contenidos[indice]["enemigos"].append(
            {"instancia": f"l-{i:02d}", "tipo": _ENEMIGOS[i % len(_ENEMIGOS)]["id"]})

    mapa = Mapa()
    mapa.cargar_desde_json(esqueleto)
    mapa.asignar_contenidos(contenidos)

    fichas = _fichas_en_arbol(_OBJETOS + _ENEMIGOS)
    partida = Partida(mapa, _jugador(), 1, fichas.obtener, semilla=semilla)
    partida.iniciar()
    _activar_salas_con_cazadores(partida)
    return partida, f"sintética {SALAS_REFERENCIA} salas"


def copia_con_contenidos(carpeta=None):
    """(id, datos, fichas) de la copia local **más grande** (la cripta de
    referencia es la publicada más grande), solo si tiene el contenido de
    todas sus salas y hay catálogo; si no, None y (a) usa la sintética. Así
    no se escribe su id en el código (principio IV) y nunca se mide una
    cripta más chica que la de referencia."""
    carpeta = carpeta if carpeta is not None else CARPETA_COPIAS
    ruta_catalogo = os.path.join(carpeta, "catalogo.json")

    if not os.path.isdir(carpeta) or not os.path.exists(ruta_catalogo):
        return None

    mejor = None

    for nombre in os.listdir(carpeta):
        if not nombre.endswith(".json") or nombre == "catalogo.json":
            continue

        try:
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, ValueError):
            continue

        if not isinstance(datos, dict) or not datos.get("esqueleto"):
            continue

        clave = (-len(datos["esqueleto"]), nombre)

        if mejor is None or clave < mejor[2]:
            mejor = (nombre[:-len(".json")], datos, clave)

    if (mejor is None or not mejor[1].get("contenidos")
            or len(mejor[1]["contenidos"]) < len(mejor[1]["esqueleto"])):
        return None

    with open(ruta_catalogo, encoding="utf-8") as archivo:
        fichas = (json.load(archivo).get("fichas") or {}).values()

    return mejor[0], mejor[1], fichas


def _partida_de_copia(copia, semilla):
    cripta_id, datos, fichas = copia
    mapa = Mapa()
    mapa.cargar_desde_json(datos["esqueleto"])
    mapa.asignar_contenidos(datos["contenidos"])

    salas = mapa.obtener_todas()
    for i in range(len(salas)):
        if not salas.obtener(i).contenido_cargado():
            return None

    generales = datos.get("datos_generales") or {}
    inicial = generales.get("sala_inicial") or datos["esqueleto"][0]["id"]
    partida = Partida(mapa, _jugador(), inicial, _fichas_en_arbol(fichas).obtener,
                      semilla=semilla)
    partida.iniciar()
    _activar_salas_con_cazadores(partida)
    return partida, cripta_id


def _partida_de_escala(semilla):
    """(b): 2000 salas con 50 cazadores activos (la de B7), con objetos y
    pergaminos."""
    from crypta.bench.bench_cazador import CriptaSintetica

    cripta = CriptaSintetica(SALAS_ESCALA, semilla)
    rango = cripta.rango_mediano()
    ficha = _ficha_cazador_bench(rango)
    azar = random.Random(semilla)
    contenidos = cripta.contenidos(cripta.ubicar_cazadores(CAZADORES_ESCALA, rango))

    for datos in contenidos:
        datos["objetos"] = _objetos_de_sala(azar)

    cripta.mapa.asignar_contenidos(contenidos)
    fichas = _fichas_en_arbol((ficha,) + _OBJETOS)
    partida = Partida(cripta.mapa, _jugador(), cripta.sala_jugador.id, fichas.obtener,
                      semilla=semilla)
    partida.iniciar()
    _activar_salas_con_cazadores(partida)
    return partida, f"sintética {SALAS_ESCALA} salas, {CAZADORES_ESCALA} cazadores"


def partida_inicial(cripta, semilla):
    """(partida iniciada, nombre de la cripta) para «a» o «b»."""
    if cripta == "b":
        return _partida_de_escala(semilla)

    copia = copia_con_contenidos()
    if copia is not None:
        armada = _partida_de_copia(copia, semilla)
        if armada is not None:
            return armada

    return _partida_sintetica(semilla)


class LineaMedida(LineaDeTiempo):
    """La línea de siempre, que además suma el tiempo de crear los puntos de
    control (para L1, L2 y L4). No cambia nada de lo que guarda."""

    def __init__(self, k=K_POR_DEFECTO):
        super().__init__(k)
        self.tiempo_puntos = 0.0
        self.copias = 0

    def registrar(self, partida, comando, acciones_antes, reloj_antes):
        antes = len(self.puntos)
        inicio = time.perf_counter()
        super().registrar(partida, comando, acciones_antes, reloj_antes)

        if len(self.puntos) > antes:
            self.tiempo_puntos += time.perf_counter() - inicio
            self.copias += 1


class _Ritmo:
    """Cuándo toca un pergamino: uno cada INTERVALO_PERGAMINO acciones."""

    def __init__(self):
        self.acciones = 0
        self.debe_pergamino = False


def _siguiente_comando(partida, azar, ritmo):
    """Un comando probable de ser válido. Si toca un pergamino: lo usa si
    tiene; si no, lo recoge si hay en el suelo; si no, sigue jugando."""
    inventario = partida.jugador.inventario
    sala = partida.sala_actual()

    if (ritmo.debe_pergamino and inventario.tiene_pergamino()
            and partida.estado.historial.puede_deshacer()):
        return "pergamino"

    # Una reserva de pergaminos: si hay en el suelo y lleva menos de dos, los
    # recoge (y, si no cabe, suelta algo antes).
    if sala.cantidad_pergaminos() > 0 and inventario.cantidad_pergaminos() < 2:
        if inventario.esta_lleno():
            return "soltar"
        return "recoger_pergamino"

    presentes = partida.enemigos_presentes()
    r = azar.random()

    if len(presentes) > 0 and r < 0.35:
        return f"atacar {presentes.obtener(0).id_instancia}"

    if sala.cantidad_objetos() > 0 and not inventario.esta_lleno() and r < 0.45:
        return f"recoger {azar.randrange(sala.cantidad_objetos())}"

    actual = inventario.actual()

    if actual is not None and r < 0.55:
        clase = actual.get("clase")
        if clase in ("arma", "armadura") and not inventario.actual_esta_equipado():
            return "equipar"
        if clase in ("pocion", "antorcha"):
            return "usar"

    r = azar.random()

    if r < 0.05:
        return azar.choice(("avanzar", "retroceder"))

    if inventario.esta_lleno() and r < 0.15:
        return "soltar"

    abiertas = []
    cerradas = []
    for direccion in "NSEO":
        puerta = sala.obtener_puerta(direccion)
        if puerta is not None:
            (cerradas if puerta.esta_cerrada() else abiertas).append(direccion)

    if cerradas and r < 0.22:
        return f"abrir {azar.choice(cerradas)}"

    if r < 0.30 or not abiertas:
        return "esperar"

    return "mover " + azar.choice(abiertas)


class PartidaLinea:
    """Una partida jugada para el bench, con su línea (y su oráculo, si se
    pidió). `huella()` identifica la partida (HU5-5)."""

    def __init__(self, cripta, semilla, acciones, k, con_oraculo=False):
        self.semilla = semilla
        self.partida, self.nombre = partida_inicial(cripta, semilla)
        self.salas = self.partida.mapa.cantidad_salas()
        self.enemigos_activos = _contar_activos(self.partida)
        self.linea = LineaMedida(k)
        self.linea.iniciar(self.partida)
        self.comandos = Vector()
        self.oraculo = Oraculo() if con_oraculo else None
        self._jugar(acciones)

    def _jugar(self, acciones):
        azar = random.Random(self.semilla)
        ritmo = _Ritmo()
        partida = self.partida
        intentos = 0

        if self.oraculo is not None:
            partida.al_ejecutar_evento = self.oraculo.al_evento

        try:
            while self.linea.cantidad_acciones() < acciones:
                intentos += 1
                if intentos > 40 * acciones + 1000:
                    raise RuntimeError("El generador no llega a las acciones pedidas")

                comando = _siguiente_comando(partida, azar, ritmo)
                antes = partida.acciones_jugador

                if self.oraculo is not None:
                    self.oraculo.en_decision(partida)

                try:
                    ejecutar_y_registrar(partida, self.linea, comando, None)
                except (ComandoInvalido, AccionInvalida):
                    continue

                self.comandos.agregar(comando)

                if partida.acciones_jugador == antes + 1:
                    ritmo.acciones += 1
                    if ritmo.acciones % INTERVALO_PERGAMINO == 0:
                        ritmo.debe_pergamino = True
                elif partida.acciones_jugador == antes - 1:
                    ritmo.debe_pergamino = False

            if self.oraculo is not None:
                self.oraculo.en_decision(partida)
        finally:
            partida.al_ejecutar_evento = None

    def huella(self):
        """Cantidades del generador, comandos, reloj final y estado final."""
        resumen = hashlib.sha256()
        resumen.update(repr((self.nombre, self.salas, self.enemigos_activos,
                             self.linea.cantidad_acciones(), INTERVALO_PERGAMINO,
                             self.partida.reloj)).encode("utf-8"))
        for i in range(len(self.comandos)):
            resumen.update(self.comandos.obtener(i).encode("utf-8") + b"\n")
        resumen.update(serializar_estado(self.partida))
        return resumen.hexdigest()

    def pedidos(self, cantidad, semilla=None):
        """`cantidad` consultas repartidas con la semilla: mitad `#k`, mitad
        instantes (que suelen caer entre dos decisiones)."""
        azar = random.Random(self.semilla + 1 if semilla is None else semilla)
        n = self.linea.cantidad_acciones()
        pedidos = Vector(max(1, cantidad))

        for i in range(cantidad):
            if i % 2 == 0:
                pedidos.agregar(("accion", azar.randint(1, n + 1)))
            else:
                pedidos.agregar(("instante", azar.randint(0, self.partida.reloj)))

        return pedidos

    def ubicar(self, pedido):
        tipo, valor = pedido
        if tipo == "instante":
            return self.linea.ubicar_instante(valor, self.partida.reloj)
        return self.linea.ubicar_accion(valor)

    def consultar(self, pedido, funcion=None):
        funcion = CONSULTAR_ADELANTE if funcion is None else funcion
        return funcion(self.linea, self.ubicar(pedido), self.partida, ejecutar_comando)


def partida_linea(cripta, semilla, acciones, k=K_POR_DEFECTO, con_oraculo=False):
    """La partida del bench (FR-427): «a» (tamaño de la de referencia) o «b»
    (escala), con al menos `acciones` acciones netas."""
    return PartidaLinea(cripta, semilla, acciones, k, con_oraculo)


def _contar_activos(partida):
    total = 0
    salas = partida.mapa.obtener_todas()
    for i in range(len(salas)):
        sala = salas.obtener(i)
        for j in range(sala.cantidad_enemigos()):
            if sala.enemigo_en(j).esta_activo():
                total += 1
    return total


# ======================================================================
# Medición
# ======================================================================

def _percentil(tiempos, p):
    return Medicion(0).percentil(tiempos, p)


def _media(tiempos):
    return Medicion(0).media(tiempos)


def _tiempos_de_consulta(jugada, cantidad, funcion=None):
    tiempos = Vector(max(1, cantidad))
    pedidos = jugada.pedidos(cantidad)

    for i in range(len(pedidos)):
        pedido = pedidos.obtener(i)
        tiempos.agregar(cronometrar(lambda: jugada.consultar(pedido, funcion)))

    return tiempos


def memoria_de(crear):
    """Bytes que ocupa lo que devuelve `crear()`, con `tracemalloc`. Se usa
    siempre aparte de las mediciones de tiempo."""
    gc.collect()
    tracemalloc.start()
    try:
        antes = tracemalloc.get_traced_memory()[0]
        objeto = crear()
        despues = tracemalloc.get_traced_memory()[0]
    finally:
        tracemalloc.stop()
    del objeto
    return max(0, despues - antes)


def memoria_de_la_linea(linea):
    """Memoria de la línea: una copia, medida con `tracemalloc`, de sus
    entradas y sus puntos de control (cada punto se copia con los mismos
    ganchos, así ocupa lo mismo que el original)."""
    return memoria_de(lambda: copy.deepcopy((linea.entradas, linea.decisiones,
                                             linea.puntos)))


def _mb(bytes_):
    return f"{bytes_ / 1e6:.1f} MB"


def _ms(segundos):
    return formato_tiempo(segundos)


_CACHE = Vector()          # (clave, PartidaLinea): a lo sumo dos


def _jugada(cripta, semilla, acciones, k):
    """Una partida ya jugada con esos parámetros (se reusa entre secciones;
    se guardan a lo sumo dos para no juntar memoria)."""
    clave = (cripta, semilla, acciones, k)

    for i in range(len(_CACHE)):
        if _CACHE.obtener(i)[0] == clave:
            return _CACHE.obtener(i)[1]

    jugada = partida_linea(cripta, semilla, acciones, k)

    if len(_CACHE) >= 2:
        _CACHE.quitar(0)

    _CACHE.agregar((clave, jugada))
    return jugada


def _olvidar():
    while len(_CACHE) > 0:
        _CACHE.quitar_ultimo()
    gc.collect()


def _parametros(rapido):
    if rapido:
        return {"acciones": 150, "escala": 30, "consultas": 16, "sin_puntos": 4,
                "ks": VALORES_K_RAPIDO, "l3": 120, "comparadas": 60, "l4": 25,
                "calentamiento": 5, "l5": (100, 200), "l8": 150}

    return {"acciones": ACCIONES_REFERENCIA, "escala": ACCIONES_ESCALA,
            "consultas": CONSULTAS, "sin_puntos": CONSULTAS_SIN_PUNTOS,
            "ks": VALORES_K, "l3": ACCIONES_L3, "comparadas": COMPARADAS_L3,
            "l4": ACCIONES_L4, "calentamiento": CALENTAMIENTO_L4,
            "l5": (ACCIONES_REFERENCIA // 2, ACCIONES_REFERENCIA),
            "l8": ACCIONES_REFERENCIA}


# ======================================================================
# L1 (FR-428, FR-432, SC-404, SC-406)
# ======================================================================

def ejecutar_l1(rapido=False):
    p = _parametros(rapido)
    filas = []
    sin_limite = []

    casos = [("a", k) for k in p["ks"]] + [("a", None), ("b", K_POR_DEFECTO)]

    for cripta, k in casos:
        acciones = p["acciones"] if cripta == "a" else p["escala"]
        k_real = k if k is not None else 10 * acciones + 1      # solo el punto 0
        jugada = partida_linea(cripta, SEMILLA, acciones, k_real)
        cantidad = p["consultas"] if k is not None else p["sin_puntos"]
        tiempos = _tiempos_de_consulta(jugada, cantidad)
        memoria = memoria_de_la_linea(jugada.linea)
        p95 = _percentil(tiempos, 95)

        if cripta == "a" and k == K_POR_DEFECTO:
            cumple = "sí" if p95 * 1000 < LIMITE_HISTORIA_MS else "NO"
        elif cripta == "b":
            cumple = "sin límite"
            if p95 * 1000 >= LIMITE_HISTORIA_MS:
                sin_limite.append(f"{jugada.nombre}: p95 {_ms(p95)}")
        else:
            cumple = "—"

        filas.append((jugada.nombre, "sin puntos" if k is None else str(k),
                      str(len(jugada.linea.puntos)), str(cantidad),
                      _ms(_media(tiempos)), _ms(p95), _ms(_percentil(tiempos, 100)),
                      _ms(jugada.linea.tiempo_puntos), _mb(memoria), cumple))

        del jugada, tiempos
        _olvidar()

    nota = ("«¿cumple?» solo aplica a la cripta del tamaño de la de referencia con el K "
            f"por defecto ({K_POR_DEFECTO}). La de escala se reporta sin límite; si pasa "
            "de 50 ms va a Límites. Tiempos sin tracemalloc; memoria aparte, con "
            "tracemalloc, de una copia de la línea.")
    if sin_limite:
        nota += " Para Límites: " + "; ".join(sin_limite) + "."

    return tabla(
        f"L1 CONSULTA DE HISTORIA POR K (FR-428, FR-432, SC-404: p95 menor que "
        f"{LIMITE_HISTORIA_MS} ms). (a) {p['acciones']} acciones, (b) {p['escala']} "
        f"acciones; un pergamino cada {INTERVALO_PERGAMINO}",
        ("cripta", "K", "puntos", "consultas", "media", "p95", "máximo",
         "crear puntos", "memoria", "¿cumple?"),
        filas, nota)


# ======================================================================
# L2 (FR-429): hacia adelante frente a hacia atrás
# ======================================================================

class _SalaAntes:
    """Lo que el historial no devuelve de una sala: sus objetos (copiados),
    sus pergaminos y si ya se apartaron."""

    def __init__(self, sala):
        objetos, pergaminos, apartados = sala.estado_de_pergaminos()
        copia = Vector(max(1, len(objetos)))
        for i in range(len(objetos)):
            copia.agregar(objetos.obtener(i))
        self.sala = sala
        self.estado = (copia, pergaminos, apartados)

    def devolver(self):
        objetos = Vector(max(1, len(self.estado[0])))
        for i in range(len(self.estado[0])):
            objetos.agregar(self.estado[0].obtener(i))
        self.sala.restaurar_estado_de_pergaminos(
            (objetos, self.estado[1], self.estado[2]))


class _Foto:
    """Lo no reversible en una frontera entre dos entradas del tramo:
    pergaminos del inventario, objeto a la vista y las salas del tramo."""

    def __init__(self, partida, salas):
        inventario = partida.jugador.inventario
        self.pergaminos = inventario.cantidad_pergaminos()
        self.actual = inventario.posiciones()[0]
        self.salas = Vector(max(1, len(salas)))
        for i in range(len(salas)):
            self.salas.agregar(_SalaAntes(salas.obtener(i)))

    def devolver(self, partida, primeras):
        inventario = partida.jugador.inventario
        inventario.fijar_pergaminos(self.pergaminos)
        inventario.poner_actual_por_posicion(None if self.actual == -1 else self.actual)

        # Las salas que todavía no se visitaban: como al empezar el tramo.
        for i in range(len(primeras)):
            primera = primeras.obtener(i)
            if not _esta(self.salas, primera.sala):
                primera.devolver()

        for i in range(len(self.salas)):
            self.salas.obtener(i).devolver()


def _esta(fotos, sala):
    for i in range(len(fotos)):
        if fotos.obtener(i).sala is sala:
            return True
    return False


class PuntoFinal:
    """B_j: una copia del punto C_j a la que se le re-ejecutan las entradas
    de su tramo con historial sin límite (research D2). Queda al final del
    tramo con los cambios del tramo registrados sobre sus propios objetos.
    Como el historial de P1 no devuelve pergaminos ni el objeto a la vista,
    guarda además una `_Foto` en cada frontera entre entradas: es parte del
    costo de ir hacia atrás."""

    def __init__(self, jugada, j):
        linea = jugada.linea
        punto = linea.puntos.obtener(j)
        self.inicio = punto.posicion
        self.fin = (linea.puntos.obtener(j + 1).posicion if j + 1 < len(linea.puntos)
                    else len(linea.entradas))
        self.partida = copy.deepcopy(punto.partida)
        self.acciones_fin = punto.ancla
        self.salas = Vector()          # salas del tramo, en orden de visita
        self.primeras = Vector()       # cada una como al empezar el tramo
        self.fotos = Vector()          # foto antes de la entrada inicio + i
        self._viva = jugada.partida
        self._visitar(self.partida.sala_actual())

        sello = Sello(self.partida)
        for i in range(self.inicio, self.fin):
            self.fotos.agregar(_Foto(self.partida, self.salas))
            self.acciones_fin += _reejecutar(self.partida, linea.entradas.obtener(i),
                                             ejecutar_comando, self.garantizar, sello)

    def _visitar(self, sala):
        for i in range(len(self.salas)):
            if self.salas.obtener(i) is sala:
                return
        self.salas.agregar(sala)
        self.primeras.agregar(_SalaAntes(sala))

    def garantizar(self, id_sala):
        sala = self.partida.mapa.obtener_sala(id_sala)

        if not sala.contenido_cargado():
            sala.asignar_contenido(self._viva.mapa.obtener_sala(id_sala).contenido)

        self._visitar(sala)
        return sala


def consultar_hacia_atras(finales, linea, objetivo, partida_viva):
    """Hacia atrás (FR-429): sobre B_j, deshacer desde el final del tramo
    hasta el objetivo, devolver lo no reversible con la foto de esa
    frontera, resumir y volver al final re-ejecutando (Cambio no sabe
    rehacer)."""
    if objetivo.es_actual:
        return armar_resumen(partida_viva, objetivo.pedido)

    m = objetivo.acciones_completas
    j = (m - linea.accion_base) // linea.k
    final = finales.obtener(j)
    b = final.partida
    siguiente = linea.posicion_de_accion(m + 1)
    sello = Sello(b)
    for i in range(len(final.salas)):
        sello.anotar_sala(final.salas.obtener(i))

    for _ in range(final.acciones_fin - m):
        b.estado.historial.deshacer_ultima()
    if b._perseguidor is not None:
        b._perseguidor.invalidar()

    foto = final.fotos.obtener(siguiente - final.inicio)
    foto.devolver(b, final.primeras)

    if objetivo.tope is not None:
        b.tope_tiempo = objetivo.tope
        hecha = _reejecutar(b, linea.entradas.obtener(siguiente), ejecutar_comando,
                            final.garantizar, Sello(b))
        resumen = armar_resumen(b, objetivo.pedido)
        b.tope_tiempo = None
        for _ in range(hecha):
            b.estado.historial.deshacer_ultima()
        foto.devolver(b, final.primeras)
    else:
        resumen = armar_resumen(b, objetivo.pedido)

    # Volver al final del tramo: re-ejecutar desde el objetivo.
    for i in range(siguiente, final.fin):
        _reejecutar(b, linea.entradas.obtener(i), ejecutar_comando, final.garantizar,
                    Sello(b))

    # Los eventos re-programados al volver tienen números de secuencia nuevos
    # (más altos, en el mismo orden relativo): no se rebobina.
    sello.secuencia = b.agenda.siguiente_secuencia
    sello.restaurar()
    return resumen


def puntos_finales(jugada):
    finales = Vector(max(1, len(jugada.linea.puntos)))
    for j in range(len(jugada.linea.puntos)):
        finales.agregar(PuntoFinal(jugada, j))
    return finales


def ejecutar_l2(rapido=False):
    p = _parametros(rapido)
    jugada = _jugada("a", SEMILLA, p["acciones"], K_POR_DEFECTO)
    linea = jugada.linea

    inicio = time.perf_counter()
    finales = puntos_finales(jugada)
    crear_atras = time.perf_counter() - inicio

    adelante = _tiempos_de_consulta(jugada, p["consultas"])
    atras = Vector()
    pedidos = jugada.pedidos(p["consultas"])
    for i in range(len(pedidos)):
        objetivo = jugada.ubicar(pedidos.obtener(i))
        atras.agregar(cronometrar(lambda: consultar_hacia_atras(
            finales, linea, objetivo, jugada.partida)))

    memoria_adelante = memoria_de_la_linea(linea)
    memoria_atras = memoria_de(lambda: puntos_finales(jugada))
    del finales
    gc.collect()

    puntos = len(linea.puntos)
    filas = [
        ("hacia adelante (elegida)", _ms(_media(adelante)), _ms(_percentil(adelante, 95)),
         _ms(linea.tiempo_puntos / max(1, linea.copias)), _mb(memoria_adelante)),
        ("hacia atrás", _ms(_media(atras)), _ms(_percentil(atras, 95)),
         _ms(crear_atras / max(1, puntos)), _mb(memoria_atras)),
    ]

    return tabla(
        f"L2 HACIA ADELANTE FRENTE A HACIA ATRÁS (FR-429). {jugada.nombre}, "
        f"{p['acciones']} acciones, K = {K_POR_DEFECTO}, {p['consultas']} consultas",
        ("variante", "consulta: media", "p95", "crear un punto", "memoria"),
        filas,
        "Hacia atrás: cada punto B_j re-ejecuta su tramo al crearse y guarda todos sus "
        "cambios y una foto de lo no reversible por entrada (research D2).")


# ======================================================================
# L3 (FR-430): igualdad de resúmenes
# ======================================================================

def _entradas_a_comparar(oraculo, cantidad):
    """Cada «acción #k» y cada evento del oráculo, tomados a intervalos
    regulares hasta `cantidad`."""
    elegibles = Vector()
    for i in range(len(oraculo)):
        entrada = oraculo.obtener(i)
        if entrada.es_evento or entrada.pedido.startswith("acción"):
            elegibles.agregar(entrada)

    paso = max(1, len(elegibles) // max(1, cantidad))
    elegidas = Vector()
    for i in range(0, len(elegibles), paso):
        elegidas.agregar(elegibles.obtener(i))
    return elegidas


def _pedido_de(entrada):
    tipo, valor = entrada.pedido.split(" ")
    return ("instante", int(valor)) if tipo == "instante" else ("accion", int(valor[1:]))


def ejecutar_l3(rapido=False):
    """Devuelve (texto, errores)."""
    p = _parametros(rapido)
    filas = []
    errores = []

    variantes = [(f"adelante, K = {k}", k, False) for k in p["ks"]]
    variantes.append(("sin puntos de control", 10 * p["l3"] + 1, False))
    variantes.append((f"hacia atrás, K = {K_POR_DEFECTO}", K_POR_DEFECTO, True))

    for nombre, k, atras in variantes:
        jugada = partida_linea("a", SEMILLA, p["l3"], k, con_oraculo=True)
        cantidad = p["comparadas"] if "sin puntos" not in nombre else max(10, p["comparadas"] // 10)
        elegidas = _entradas_a_comparar(jugada.oraculo, cantidad)
        finales = puntos_finales(jugada) if atras else None
        diferencias = 0

        for i in range(len(elegidas)):
            entrada = elegidas.obtener(i)
            objetivo = jugada.ubicar(_pedido_de(entrada))

            if atras:
                resumen = consultar_hacia_atras(finales, jugada.linea, objetivo,
                                                jugada.partida)
            else:
                resumen = CONSULTAR_ADELANTE(jugada.linea, objetivo, jugada.partida,
                                             ejecutar_comando)

            if formatear_resumen(resumen) != entrada.texto:
                diferencias += 1
                if len(errores) < 20:
                    errores.append(f"{nombre}: {entrada.pedido} distinto del oráculo")

        filas.append((nombre if "sin puntos" not in nombre else "sin puntos de control",
                      str(len(elegidas)), str(diferencias)))
        del jugada, finales
        _olvidar()

    total = sum(int(fila[2]) for fila in filas)
    texto = tabla(
        f"L3 IGUALDAD DE RESÚMENES (FR-430). {SALAS_REFERENCIA} salas, {p['l3']} "
        f"acciones con pergaminos; oráculo: la partida viva mientras se jugaba",
        ("variante", "comparadas", "diferencias"),
        filas,
        f"Total: {total} diferencias.")

    for error in errores:
        texto += f"\nERROR: {error}"

    return texto, total


# ======================================================================
# L4 (FR-433, SC-405): ciclo de la 001 con la línea activa
# ======================================================================

def _ciclo(con_linea, acciones, calentamiento, semilla):
    from crypta.bench.bench_ciclo import partida_con_cazadores
    from crypta.bench.bench_cazador import recorrido_desde

    partida, _ = partida_con_cazadores(CAZADORES_ESCALA, semilla)
    linea = None
    if con_linea:
        linea = LineaMedida(K_POR_DEFECTO)
        linea.iniciar(partida)

    recorrido = recorrido_desde(partida.sala_actual(), calentamiento + acciones, semilla)
    tiempos = Vector(max(1, acciones))
    copiaron = 0

    for numero in range(len(recorrido)):
        comando = "mover " + recorrido.obtener(numero)
        copias = 0 if linea is None else linea.copias
        transcurrido = cronometrar(
            lambda: ejecutar_y_registrar(partida, linea, comando, None))

        if numero >= calentamiento:
            tiempos.agregar(transcurrido)
            if linea is not None and linea.copias > copias:
                copiaron += 1

    return tiempos, copiaron


def ejecutar_l4(rapido=False):
    from crypta.bench.bench_cazador import SEMILLA as SEMILLA_CAZADOR

    p = _parametros(rapido)
    filas = []

    for con_linea in (False, True):
        tiempos, copiaron = _ciclo(con_linea, p["l4"], p["calentamiento"], SEMILLA_CAZADOR)
        p95 = _percentil(tiempos, 95)
        filas.append(("con línea" if con_linea else "sin línea", str(len(tiempos)),
                      str(copiaron) if con_linea else "—",
                      _ms(_media(tiempos)), _ms(p95), _ms(_percentil(tiempos, 100)),
                      "sí" if p95 * 1000 < LIMITE_MS else "NO"))
        gc.collect()

    return tabla(
        f"L4 CICLO CON LA LÍNEA ACTIVA (FR-433, SC-405: p95 menor que {LIMITE_MS} ms). "
        f"Escenario B7 de la 001 ({SALAS_ESCALA} salas, {CAZADORES_ESCALA} cazadores), "
        f"K = {K_POR_DEFECTO}, {p['l4']} acciones medidas",
        ("ciclo", "acciones", "copiaron", "media", "p95", "máximo", "¿cumple?"),
        filas,
        "Cada ciclo es ejecutar el comando y anotarlo en la línea: incluye las copias "
        f"(1 de cada {K_POR_DEFECTO} acciones). El máximo y la media sí las ven.")


# ======================================================================
# L5 (FR-424, FR-434, SC-409), L6 (FR-425)
# ======================================================================

def ejecutar_l5(rapido=False):
    p = _parametros(rapido)
    mitad, todas = p["l5"]
    memorias = []

    for acciones in (mitad, todas):
        jugada = _jugada("a", SEMILLA, acciones, K_POR_DEFECTO)
        memorias.append(memoria_de_la_linea(jugada.linea))
        copia_una = memoria_de(lambda: copy.deepcopy(jugada.partida))

    cociente = memorias[1] / max(1, memorias[0])
    por_accion = todas * copia_una
    fraccion = memorias[1] / max(1, por_accion)
    _olvidar()

    filas = [
        (f"{mitad} acciones", _mb(memorias[0]), "", ""),
        (f"{todas} acciones", _mb(memorias[1]), "", ""),
        ("5 000 / 2 500" if not rapido else f"{todas} / {mitad} (5 000 / 2 500)",
         f"{cociente:.2f}", "≤ 2,5", "sí" if cociente <= 2.5 else "NO"),
        (f"copia por acción ({todas} × {_mb(copia_una)})", _mb(por_accion), "", ""),
        ("línea / copia por acción", f"{fraccion:.3f}", "< 1/3",
         "sí" if fraccion < 1 / 3 else "NO"),
    ]

    return tabla(
        f"L5 MEMORIA DE LA LÍNEA (FR-424, FR-434, SC-409). K = {K_POR_DEFECTO}, "
        f"{SALAS_REFERENCIA} salas",
        ("medida", "valor", "límite", "¿cumple?"),
        filas,
        "Con tracemalloc, aparte de los tiempos. La copia por acción no se materializa: "
        "acciones × lo que ocupa una copia medida.")


def ejecutar_l6(rapido=False):
    p = _parametros(rapido)
    filas = []

    for acciones in p["l5"]:
        jugada = _jugada("a", SEMILLA, acciones, K_POR_DEFECTO)
        pedidos = jugada.pedidos(p["consultas"])
        maximo = 0
        for i in range(len(pedidos)):
            jugada.consultar(pedidos.obtener(i))
            maximo = max(maximo, jugada.linea.puntos_examinados)
        filas.append((str(acciones), str(len(jugada.linea.puntos)), str(len(pedidos)),
                      str(maximo)))

    return tabla(
        f"L6 PUNTOS EXAMINADOS POR CONSULTA (FR-425). K = {K_POR_DEFECTO}",
        ("acciones", "puntos de control", "consultas", "examinados (máximo)"),
        filas,
        "El punto se calcula (j = ⌊(m − a₀) / K⌋): siempre 1, sin importar cuántos haya.")


# ======================================================================
# L7 (research D3): cómo se copia un punto; L8 (FR-417): guardar y cargar
# ======================================================================

_GANCHOS = (Partida, Mapa, Sala, EstadoPuerta)


def _copia_sin_ganchos(partida):
    """`deepcopy` sin los ganchos de la capacidad 004 (copia también las
    fichas, la búsqueda y la bitácora). Necesita subir el límite de
    recursión: sin la copia del mapa en dos pasadas, baja por la cadena de
    salas vecinas."""
    guardados = [(clase, clase.__dict__["__deepcopy__"]) for clase in _GANCHOS]
    limite = sys.getrecursionlimit()

    try:
        for clase, _ in guardados:
            setattr(clase, "__deepcopy__", None)
        sys.setrecursionlimit(max(limite, 200000))
        return copy.deepcopy(partida)
    finally:
        sys.setrecursionlimit(limite)
        for clase, gancho in guardados:
            setattr(clase, "__deepcopy__", gancho)


def _copia_por_recorrido(partida):
    """Escribir la partida con el recorrido de `EstadoPartida` y armarla."""
    e = EscritorBinario()
    escribir_general(e, partida)
    salas = partida.mapa.obtener_todas()
    e.empezar_lista("salas", len(salas))
    for i in range(len(salas)):
        escribir_sala(e, salas.obtener(i))
    e.terminar_lista()

    l = LectorBinario(e.datos())
    general = leer_general(l)
    leidas = Vector(max(1, len(salas)))
    for _ in range(l.empezar_lista("salas")):
        leidas.agregar(leer_sala(l, partida._fichas))
    l.terminar()

    encabezado = Encabezado("bench", "v", "c", partida.semilla, partida.jugador.nombre)
    return armar_partida(encabezado, general, leidas, partida._fichas)


def ejecutar_l7(rapido=False):
    filas = []
    repeticiones = 1 if rapido else 3

    # En modo rápido solo (a): medir con tracemalloc tres copias de la de
    # 2000 salas tarda minutos.
    for cripta in (("a",) if rapido else ("a", "b")):
        partida, nombre = partida_inicial(cripta, SEMILLA)

        for variante, copiar in (("deepcopy sin ganchos", _copia_sin_ganchos),
                                 ("deepcopy con ganchos (elegida)", copy.deepcopy),
                                 ("recorrido de EstadoPartida", _copia_por_recorrido)):
            try:
                tiempo = medir(lambda: copiar(partida), repeticiones)
                memoria = memoria_de(lambda: copiar(partida))
                filas.append((nombre, variante, _ms(tiempo), _mb(memoria)))
            except RecursionError:
                filas.append((nombre, variante, "RecursionError", "—"))
            gc.collect()

        del partida
        gc.collect()

    return tabla(
        "L7 CÓMO SE COPIA UN PUNTO DE CONTROL (research D3)",
        ("cripta", "variante", "tiempo", "memoria"),
        filas,
        "Sin ganchos copia también las fichas (con su fuente), la búsqueda del cazador y "
        "la bitácora. Tiempo sin tracemalloc; memoria aparte.")


def ejecutar_l8(rapido=False):
    p = _parametros(rapido)
    jugada = _jugada("a", SEMILLA, p["l8"], K_POR_DEFECTO)
    partida = jugada.partida
    encabezado = Encabezado("bench-linea", "v", "c", partida.semilla, partida.jugador.nombre)

    with tempfile.TemporaryDirectory() as carpeta:
        ruta = os.path.join(carpeta, "linea.cripta")
        guardar = medir(lambda: guardar_partida(partida, ruta, encabezado,
                                                linea=jugada.linea), 1)
        tamano = os.path.getsize(ruta)
        cargar = medir(lambda: ArchivoGuardado(ruta).cargar_partida(partida._fichas), 1)

    _olvidar()
    return tabla(
        f"L8 GUARDAR Y CARGAR CON LA LÍNEA (FR-417, research D11). {jugada.nombre}, "
        f"{p['l8']} acciones, K = {K_POR_DEFECTO}, binario",
        ("puntos de control", "tamaño", "guardar", "cargar"),
        [(str(len(jugada.linea.puntos)), _mb(tamano), _ms(guardar), _ms(cargar))],
        "Cada punto se guarda con el mismo recorrido que la partida viva.")
