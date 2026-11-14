import os
import platform
import random
import sys
import tempfile
import time

from crypta.bench import (bench_agenda, bench_cache, bench_cazador, bench_ciclo,
                          bench_inventario, bench_ordenamiento, bench_rastro,
                          bench_red, bench_resolubilidad)
from crypta.bench.medicion import formato_tiempo, tabla

from crypta.Adaptadores.GuardadoBinario import ArchivoGuardado, guardar_partida
from crypta.Adaptadores.GuardadoJSON import ArchivoGuardadoJSON, guardar_partida_json
from crypta.Adaptadores.RegistroPartida import Encabezado
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida


class ComparacionGuardado:
 
    def __init__(self):
        self.tamano_binario = 0
        self.tamano_json = 0
        self.carga_binario = 0.0     
        self.carga_json = 0.0
        self.una_sala_binario = 0.0
        self.una_sala_json = 0.0
        self.bytes_una_sala_binario = 0
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


def formato_bytes(cantidad):
    if cantidad < 1024:
        return f"{cantidad} B"
    if cantidad < 1024 * 1024:
        return f"{cantidad / 1024:.1f} KB"
    return f"{cantidad / (1024 * 1024):.2f} MB"


def ejecutar_guardado(rapido=False):
    tamanos = (100,) if rapido else (100, 1000, 5000)
    filas = []

    for cantidad in tamanos:
        partida, encabezado, fichas = partida_sintetica(cantidad)

        with tempfile.TemporaryDirectory() as carpeta:
            r = comparar_formatos(partida, encabezado, fichas, carpeta, repeticiones=5)

        filas.append((
            str(cantidad),
            f"{formato_bytes(r.tamano_binario)} / {formato_bytes(r.tamano_json)}",
            f"{formato_tiempo(r.carga_binario)} / {formato_tiempo(r.carga_json)}",
            f"{formato_tiempo(r.una_sala_binario)} / {formato_tiempo(r.una_sala_json)}",
            f"{formato_bytes(r.bytes_una_sala_binario)} / "
            f"{formato_bytes(r.bytes_una_sala_json)}",
        ))

    return tabla(
        "GUARDADO (§4.10): la misma partida en binario / JSON",
        ("salas", "tamaño", "cargar todo", "leer UNA sala", "bytes leídos para UNA sala"),
        filas,
        "El binario tiene un índice al final: para una sala lee solo el índice y ese "
        "registro. El JSON hay que leerlo entero.")

SECCIONES = (
    ("agenda", "Agenda de eventos (§4.1)", bench_agenda.ejecutar),
    ("ciclo", "Ciclo entre dos decisiones (§5.2)", bench_ciclo.ejecutar),
    ("cache", "Caché de fichas (§4.4)", bench_cache.ejecutar),
    ("inventario", "Inventario e historial (§4.5 y §4.6)", bench_inventario.ejecutar),
    ("rastro", "Rastro del jugador (§4.7)", bench_rastro.ejecutar),
    ("ordenamiento", "Ordenamiento (§4.9)", bench_ordenamiento.ejecutar),
    ("red", "Bitácora y red (§4.8 y §5.1)", bench_red.ejecutar),
    ("guardado", "Guardado binario contra JSON (§4.10)", ejecutar_guardado),
    # Capacidad 001 (specs/001-terreno-cazador/contracts/bench.md).
    ("cazadores", "B1 Un cazador frente a muchos (FR-029)",
     bench_cazador.ejecutar_uno_y_muchos),
    ("rangos", "B2 Rango pequeño frente a grande (FR-030)",
     bench_cazador.ejecutar_rangos),
    ("tamano", "B3 Tamaño de la cripta con la misma región (FR-036)",
     bench_cazador.ejecutar_tamano),
    ("compartido", "B4 Búsqueda compartida frente a por cazador (FR-031)",
     bench_cazador.ejecutar_compartido),
    ("reutilizar", "B5 Reutilizar frente a recalcular (FR-032)",
     bench_cazador.ejecutar_reutilizar),
    ("equivalencia", "B6 Equivalencia con el cálculo desde cero (FR-033)",
     bench_cazador.ejecutar_equivalencia),
    ("ciclo_cazadores", "B7 Ciclo con cazadores (FR-035)",
     bench_ciclo.ejecutar_ciclo_cazadores),
    ("escala", "B8 Escala en cantidad de cazadores (FR-037)",
     bench_cazador.ejecutar_escala),
    ("distancias", "B9 Dónde guardar las distancias (research D5)",
     bench_cazador.ejecutar_distancias),
    # Capacidad 003 (specs/003-resolubilidad/contracts/bench.md).
    ("resol_ingenua", "R1 Incremental frente a ingenua (FR-331)",
     bench_resolubilidad.ejecutar_ingenua),
    ("resol_limite", "R2 Límite de la verificación (FR-334)",
     bench_resolubilidad.ejecutar_limite),
    ("resol_crecimiento", "R3 Crecimiento al duplicar el tamaño (FR-335)",
     bench_resolubilidad.ejecutar_crecimiento),
    ("resol_igualdad", "R4 Igualdad con la alternativa ingenua (FR-332)",
     bench_resolubilidad.ejecutar_igualdad),
    ("resol_numeracion", "R5 Numeración de llaves (research D1)",
     bench_resolubilidad.ejecutar_numeracion),
)


def ejecutar(nombres=None, rapido=False, salida=print):
    """Corre las secciones pedidas (todas si no se pide ninguna). Una
    sección devuelve su texto, o (texto, errores) si comprueba algo (B6).
    Devuelve 0, o 1 si alguna sección reportó errores (FR-033)."""
    
    validos = [nombre for nombre, _, _ in SECCIONES]

    for nombre in nombres or ():
        if nombre not in validos:
            raise ValueError(f"No existe la sección '{nombre}'. "
                             f"Las secciones son: {', '.join(validos)}")

    salida(f"CRIPTA --bench | Python {platform.python_version()} | "
           f"{platform.system()} {platform.machine()}"
           + (" | modo rápido" if rapido else ""))

    inicio_total = time.perf_counter()
    errores = 0

    for nombre, titulo, funcion in SECCIONES:
        if nombres and nombre not in nombres:
            continue

        salida(f"\n=== {titulo} ===")
        inicio = time.perf_counter()
        resultado = funcion(rapido)

        if isinstance(resultado, tuple):
            resultado, de_la_seccion = resultado
            errores += de_la_seccion

        salida(resultado)
        salida(f"(sección medida en {formato_tiempo(time.perf_counter() - inicio)})")

    salida(f"\n(bench completo en {formato_tiempo(time.perf_counter() - inicio_total)})")

    if errores:
        salida(f"\nERROR: el --bench encontró {errores} diferencias (ver arriba).")
        return 1

    return 0


def principal(argumentos):
    rapido = "--rapido" in argumentos
    ruta = None
    nombres = []
    i = 0

    while i < len(argumentos):
        if argumentos[i] == "--guardar":
            if i + 1 >= len(argumentos):
                print("Falta el archivo después de --guardar")
                return 1
            ruta = argumentos[i + 1]
            i += 2
            continue
        if argumentos[i] != "--rapido":
            nombres.append(argumentos[i])
        i += 1

    lineas = []

    def mostrar_y_juntar(texto):
        print(texto, flush=True)
        lineas.append(str(texto))

    try:
        codigo = ejecutar(nombres or None, rapido, mostrar_y_juntar)
    except ValueError as error:
        print(error)
        return 1

    if ruta is not None:
        carpeta = os.path.dirname(ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write("\n".join(lineas) + "\n")
        print(f"\nResultados guardados en {ruta}")

    return codigo


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
