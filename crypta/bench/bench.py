"""El --bench: cargas sintéticas y tiempos por subsistema (§5.3).

Cada subsistema es una SECCIÓN con su propio archivo (bench_agenda.py...);
aquí se juntan. La comparación del guardado (§4.10, binario contra JSON)
vive en este mismo archivo.

Uso (desde la carpeta raíz del proyecto):
    python -m crypta.main --bench                  todas las secciones
    python -m crypta.bench.bench                   lo mismo
    python -m crypta.bench.bench agenda guardado   solo esas
    python -m crypta.bench.bench --rapido          tamaños chicos (para probar)
"""

import os
import platform
import random
import sys
import tempfile
import time

from crypta.bench import bench_agenda
from crypta.bench.medicion import formato_tiempo

from crypta.Adaptadores.GuardadoBinario import ArchivoGuardado, guardar_partida
from crypta.Adaptadores.GuardadoJSON import ArchivoGuardadoJSON, guardar_partida_json
from crypta.Adaptadores.RegistroPartida import Encabezado
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida


#compara los 2 guardados (bin y jason)
class ComparacionGuardado:
    """Lo que mide comparar_formatos. Tiempos en segundos (el promedio de
    las repeticiones); tamaños y bytes en bytes."""

    def __init__(self):
        self.tamano_binario = 0
        self.tamano_json = 0
        self.carga_binario = 0.0           # abrir + cargar_partida
        self.carga_json = 0.0
        self.una_sala_binario = 0.0        # abrir + leer_sala
        self.una_sala_json = 0.0
        self.bytes_una_sala_binario = 0    # lo que se leyó del archivo
        self.bytes_una_sala_json = 0

    def __str__(self):
        return "\n".join((
            "Guardado de la partida (§4.10)       binario        JSON",
            f"  tamaño en disco (bytes)       {self.tamano_binario:>10}  {self.tamano_json:>10}",
            f"  cargar la partida (ms)        {self.carga_binario * 1000:>10.2f}  {self.carga_json * 1000:>10.2f}",
            f"  leer UNA sala (ms)            {self.una_sala_binario * 1000:>10.3f}  {self.una_sala_json * 1000:>10.3f}",
            f"  bytes leídos para UNA sala    {self.bytes_una_sala_binario:>10}  {self.bytes_una_sala_json:>10}",
        ))


def comparar_formatos(partida, encabezado, fichas, carpeta, repeticiones=10, id_sala=None):
    """Guarda la MISMA partida en los dos formatos y mide. id_sala: la sala
    que se lee sola (por defecto, la del jugador)."""
    if id_sala is None:
        id_sala = partida.jugador.sala_actual

    ruta_binario = os.path.join(carpeta, "partida.bin")
    ruta_json = os.path.join(carpeta, "partida.json")
    guardar_partida(partida, ruta_binario, encabezado)
    guardar_partida_json(partida, ruta_json, encabezado)

    resultado = ComparacionGuardado()
    resultado.tamano_binario = os.path.getsize(ruta_binario)
    resultado.tamano_json = os.path.getsize(ruta_json)

    resultado.carga_binario = _medir(
        lambda: ArchivoGuardado(ruta_binario).cargar_partida(fichas), repeticiones)
    resultado.carga_json = _medir(
        lambda: ArchivoGuardadoJSON(ruta_json).cargar_partida(fichas), repeticiones)

    resultado.una_sala_binario = _medir(
        lambda: ArchivoGuardado(ruta_binario).leer_sala(id_sala, fichas), repeticiones)
    resultado.una_sala_json = _medir(
        lambda: ArchivoGuardadoJSON(ruta_json).leer_sala(id_sala, fichas), repeticiones)

    archivo = ArchivoGuardado(ruta_binario)
    archivo.leer_sala(id_sala, fichas)
    resultado.bytes_una_sala_binario = archivo.bytes_leidos

    archivo = ArchivoGuardadoJSON(ruta_json)
    archivo.leer_sala(id_sala, fichas)
    resultado.bytes_una_sala_json = archivo.bytes_leidos

    return resultado


def _medir(funcion, repeticiones):
    inicio = time.perf_counter()

    for _ in range(repeticiones):
        funcion()

    return (time.perf_counter() - inicio) / repeticiones


# ======================================================================
# UNA CRIPTA SINTÉTICA
# ======================================================================

def _enemigo(id_tipo, velocidad, comportamiento):
    return {"id": id_tipo, "clase": "enemigo", "nombre": id_tipo, "vida_max": 20,
            "ataque": 4, "defensa": 1, "velocidad": velocidad,
            "comportamiento": comportamiento}


CATALOGO_SINTETICO = {
    "ent_guardian": _enemigo("ent_guardian", 80, "guardián"),
    "ent_errante": _enemigo("ent_errante", 120, "errante"),
    "ent_rastreador": _enemigo("ent_rastreador", 100, "rastreador"),
    "itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 2,
                 "valor": 15, "ataque_bonus": 3},
    "itm_pocion": {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción", "peso": 1,
                   "valor": 10, "cura": 8},
    "trp_dardos": {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos", "daño": 2,
                   "rearme": 300},
}


def partida_sintetica(cantidad_salas, semilla=1, pasos=200):
    """Una cripta en cuadrícula con 'cantidad_salas' salas, todas con su
    contenido cargado, y 'pasos' acciones al azar ya jugadas (para que haya
    enemigos activos, eventos pendientes, objetos movidos...).

    Devuelve (partida, encabezado, fichas)."""
    azar = random.Random(semilla)
    ancho = max(1, int(cantidad_salas ** 0.5))
    salas = []
    contenidos = []

    for i in range(1, cantidad_salas + 1):
        fila, columna = (i - 1) // ancho, (i - 1) % ancho
        salidas = {}

        if columna + 1 < ancho and i + 1 <= cantidad_salas:
            salidas["E"] = {"sala": i + 1}
        if columna > 0:
            salidas["O"] = {"sala": i - 1}
        if i + ancho <= cantidad_salas:
            salidas["S"] = {"sala": i + ancho}
        if fila > 0:
            salidas["N"] = {"sala": i - ancho}

        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})

        enemigos = []
        for j in range(azar.randint(0, 2)):
            tipo = azar.choice(("ent_guardian", "ent_errante", "ent_rastreador"))
            enemigos.append({"instancia": f"e-{i}-{j}", "tipo": tipo})

        contenidos.append({
            "sala": i,
            "objetos": [azar.choice(("itm_daga", "itm_pocion")) for _ in range(azar.randint(0, 3))],
            "enemigos": enemigos,
            "trampas": [{"instancia": f"t-{i}", "tipo": "trp_dardos"}] if azar.random() < 0.2 else [],
        })

    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos(contenidos)

    jugador = Jugador("Bench", vida_max=10 ** 6, ataque=8, defensa=3, velocidad=100,
                      inventario_max=8)
    fichas = CATALOGO_SINTETICO.get
    partida = Partida(mapa, jugador, 1, fichas, semilla=semilla)
    partida.iniciar()

    for _ in range(pasos):
        _accion_al_azar(partida, azar)

    encabezado = Encabezado("bench", "v1", "cat-1", semilla, "Bench")
    return partida, encabezado, fichas


def _accion_al_azar(partida, azar):
    try:
        presentes = partida.enemigos_presentes()

        if len(presentes) > 0 and azar.random() < 0.5:
            partida.atacar(presentes.obtener(0))
        elif partida.sala_actual().cantidad_objetos() > 0 and azar.random() < 0.3:
            partida.recoger(0)
        else:
            partida.mover(azar.choice("NSEO"))
    except AccionInvalida:
        partida.esperar()


def ejecutar_guardado(rapido=False):
    """La sección GUARDADO: la misma partida en binario y en JSON."""
    tamanos = (100,) if rapido else (100, 1000, 5000)
    textos = []

    for cantidad in tamanos:
        partida, encabezado, fichas = partida_sintetica(cantidad)

        with tempfile.TemporaryDirectory() as carpeta:
            resultado = comparar_formatos(partida, encabezado, fichas, carpeta,
                                          repeticiones=5)
            textos.append(f"Cripta sintética de {cantidad} salas\n{resultado}")

    return "\n\n".join(textos)


# ======================================================================
# TODAS LAS SECCIONES
# ======================================================================

# (nombre para pedirla, título, función que mide y devuelve el texto)
SECCIONES = (
    ("agenda", "Agenda de eventos (§4.1)", bench_agenda.ejecutar),
    ("guardado", "Guardado binario contra JSON (§4.10)", ejecutar_guardado),
)


def ejecutar(nombres=None, rapido=False, salida=print):
    """Corre las secciones pedidas (todas si 'nombres' es None) y muestra
    cada una apenas termina. 'salida' es print, o algo que junte el texto
    (las pruebas)."""
    validos = [nombre for nombre, _, _ in SECCIONES]

    for nombre in nombres or ():
        if nombre not in validos:
            raise ValueError(f"No existe la sección '{nombre}'. "
                             f"Las secciones son: {', '.join(validos)}")

    salida(f"CRIPTA --bench | Python {platform.python_version()} | "
           f"{platform.system()} {platform.machine()}"
           + (" | modo rápido" if rapido else ""))

    for nombre, titulo, funcion in SECCIONES:
        if nombres and nombre not in nombres:
            continue

        salida(f"\n=== {titulo} ===")
        inicio = time.perf_counter()
        salida(funcion(rapido))
        salida(f"(sección medida en {formato_tiempo(time.perf_counter() - inicio)})")


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    rapido = "--rapido" in argumentos
    nombres = [a for a in argumentos if a != "--rapido"]

    try:
        ejecutar(nombres or None, rapido)
    except ValueError as error:
        print(error)
        sys.exit(1)
