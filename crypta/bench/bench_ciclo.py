import os
import random
import tempfile

from crypta.Adaptadores.RegistroPartida import Encabezado, RegistroPartida
from crypta.bench.medicion import cronometrar, formato_tiempo, tabla
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Controlador.Controlador import Controlador
from crypta.Controlador.GestorContenido import LIMITE_VISITAS_PRECARGA, GestorContenido
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.ordenamiento import ordenar
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida


LIMITE_MS = 20     
SALAS_CICLO = 2500 
ENEMIGOS = (50, 100, 200, 300, 500)
ENEMIGOS_RAPIDO = (20, 50)
CALENTAMIENTO = 20 
ACCIONES = 60      

CATALOGO = {
    "ent_rastreador": {"id": "ent_rastreador", "clase": "enemigo", "nombre": "Rata",
                       "vida_max": 10 ** 6, "ataque": 5, "defensa": 1,
                       "velocidad": 150, "comportamiento": "rastreador"},
    "ent_errante": {"id": "ent_errante", "clase": "enemigo", "nombre": "Murciélago",
                    "vida_max": 10 ** 6, "ataque": 4, "defensa": 1,
                    "velocidad": 100, "comportamiento": "errante", "regeneracion": 2},
    "ent_guardian": {"id": "ent_guardian", "clase": "enemigo", "nombre": "Guardián",
                     "vida_max": 10 ** 6, "ataque": 7, "defensa": 3,
                     "velocidad": 90, "comportamiento": "guardián"},
    "itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga",
                 "peso": 1, "valor": 1, "ataque_bonus": 2},
    "trp_dardos": {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos",
                   "daño": 3, "rearme": 300},
}
TIPOS_ENEMIGO = ("ent_rastreador", "ent_errante", "ent_guardian")

def esqueleto_y_contenidos(cantidad_salas, enemigos, semilla=1, cargadas=None):
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

        if cargadas is not None and i > cargadas:
            continue

        contenidos.append({
            "sala": i,
            "enemigos": [{"instancia": f"e-{k}", "tipo": TIPOS_ENEMIGO[k % 3]}
                         for k in range(enemigos)] if i == 1 else [],
            "objetos": ["itm_daga"] if azar.random() < 0.3 else [],
            "trampas": ([{"instancia": f"t-{i}", "tipo": "trp_dardos"}]
                        if i > 1 and azar.random() < 0.1 else []),
        })

    return salas, contenidos


def partida_de_carga(enemigos, fichas, semilla=1, cantidad_salas=SALAS_CICLO):
    salas, contenidos = esqueleto_y_contenidos(cantidad_salas, enemigos, semilla)
    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos(contenidos)

    jugador = Jugador("Bench", vida_max=10 ** 9, ataque=8, defensa=3,
                      velocidad=100, inventario_max=8)
    partida = Partida(mapa, jugador, 1, fichas, semilla=semilla)
    partida.iniciar()
    return partida


def proxima_accion(partida, azar):
    presentes = partida.enemigos_presentes()

    if len(presentes) > 0 and azar.random() < 0.3:
        return f"atacar {presentes.obtener(0).id_instancia}"

    if azar.random() < 0.1:
        return "esperar"

    return "mover " + azar.choice("NSEO")



class _FuenteEnMemoria:

    def obtener_catalogo(self, ids):
        return {"entidades": [CATALOGO[i] for i in ids]}

    def obtener_contenido(self, cripta_id, salas):
        raise AssertionError("el ciclo medido pidió contenido por red")


class _VistaMuda:

    def __getattr__(self, nombre):
        return lambda *argumentos, **opciones: None


class Medicion:

    def __init__(self, enemigos):
        self.enemigos = enemigos
        self.eventos_por_accion = 0.0
        self.modelo = Vector()
        self.ciclo = Vector()

    def media(self, tiempos):
        total = 0.0
        for i in range(len(tiempos)):
            total += tiempos.obtener(i)
        return total / len(tiempos)

    def percentil(self, tiempos, p):
        copia = Vector(len(tiempos))
        for i in range(len(tiempos)):
            copia.agregar(tiempos.obtener(i))
        ordenar(copia)
        indice = max(0, -(-len(copia) * p // 100) - 1)
        return copia.obtener(indice)

    def maximo(self, tiempos):
        return self.percentil(tiempos, 100)

    def cumple(self):
        return self.percentil(self.ciclo, 95) * 1000 < LIMITE_MS


def _una_vuelta_modelo(enemigos, acciones, calentamiento, semilla):
    partida = partida_de_carga(enemigos, CATALOGO.get, semilla)
    azar = random.Random(semilla)
    tiempos = Vector()
    eventos = 0

    for numero in range(calentamiento + acciones):
        linea = proxima_accion(partida, azar)
        antes = partida.agenda.siguiente_secuencia

        def accion():
            try:
                ejecutar_comando(partida, linea, lambda id_sala: None)
            except (AccionInvalida, ComandoInvalido):
                pass

        transcurrido = cronometrar(accion)

        if numero >= calentamiento:
            tiempos.agregar(transcurrido)
            eventos += partida.agenda.siguiente_secuencia - antes

    return tiempos, eventos


def _una_vuelta_ciclo(enemigos, acciones, calentamiento, semilla, carpeta):
    repositorio = RepositorioFichas(_FuenteEnMemoria())
    partida = partida_de_carga(enemigos, repositorio.obtener_ficha, semilla)
    encabezado = Encabezado("bench", "v1", "cat-1", semilla, "Bench")
    controlador = Controlador(
        partida=partida,
        gestor_contenido=GestorContenido(_FuenteEnMemoria(), partida.mapa,
                                         "bench", repositorio),
        vista=_VistaMuda(),
        registro=RegistroPartida.crear(os.path.join(carpeta, "bench.log"), encabezado),
        encabezado=encabezado,
        repositorio_fichas=repositorio,
    )
    azar = random.Random(semilla)
    tiempos = Vector()
    eventos = 0

    try:
        for numero in range(calentamiento + acciones):
            texto = proxima_accion(partida, azar)
            antes = partida.agenda.siguiente_secuencia
            transcurrido = cronometrar(lambda: controlador.procesar_comando(texto))

            if numero >= calentamiento:
                tiempos.agregar(transcurrido)
                eventos += partida.agenda.siguiente_secuencia - antes
    finally:
        controlador.gestor_contenido.cerrar()

    return tiempos, eventos


def _mejor_de(vueltas, una_vuelta):
    mejores, eventos = una_vuelta()

    for _ in range(vueltas - 1):
        tiempos, otros = una_vuelta()

        if otros != eventos:
            raise AssertionError("dos vueltas iguales no dieron la misma partida")

        for i in range(len(tiempos)):
            if tiempos.obtener(i) < mejores.obtener(i):
                mejores.asignar(i, tiempos.obtener(i))

    return mejores, eventos


def medir(enemigos, acciones=ACCIONES, calentamiento=CALENTAMIENTO, vueltas=3,
          semilla=1):
    resultado = Medicion(enemigos)
    resultado.modelo, eventos = _mejor_de(vueltas, lambda: _una_vuelta_modelo(
        enemigos, acciones, calentamiento, semilla))
    resultado.eventos_por_accion = eventos / acciones

    with tempfile.TemporaryDirectory() as carpeta:
        resultado.ciclo, eventos_ciclo = _mejor_de(vueltas, lambda: _una_vuelta_ciclo(
            enemigos, acciones, calentamiento, semilla, carpeta))

    if eventos_ciclo != eventos:
        raise AssertionError("el ciclo completo jugó otra partida que el modelo")

    return resultado

def costo_precarga(cantidad_salas, cargadas, repeticiones=20):
    salas, contenidos = esqueleto_y_contenidos(cantidad_salas, 0, cargadas=cargadas)
    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos(contenidos)
    gestor = GestorContenido(_FuenteEnMemoria(), mapa, "bench")

    mejor = None
    for _ in range(repeticiones):
        transcurrido = cronometrar(lambda: gestor._salas_para_precargar(1))
        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    gestor.cerrar()
    return mejor


def ejecutar(rapido=False):
    cantidades = ENEMIGOS_RAPIDO if rapido else ENEMIGOS
    acciones = 15 if rapido else ACCIONES
    calentamiento = 5 if rapido else CALENTAMIENTO
    filas = []

    for enemigos in cantidades:
        m = medir(enemigos, acciones, calentamiento, vueltas=1 if rapido else 3)
        filas.append((
            str(enemigos),
            f"{m.eventos_por_accion:.0f}",
            formato_tiempo(m.media(m.modelo)),
            formato_tiempo(m.media(m.ciclo)),
            formato_tiempo(m.percentil(m.ciclo, 95)),
            formato_tiempo(m.maximo(m.ciclo)),
            f"{m.media(m.ciclo) / max(1.0, m.eventos_por_accion) * 1e6:.0f} µs",
            "sí" if m.cumple() else "NO",
        ))

    ciclo = tabla(
        f"CICLO ENTRE DOS DECISIONES (§5.2: menos de {LIMITE_MS} ms). Cripta de "
        f"{SALAS_CICLO} salas toda cargada; {acciones} acciones medidas "
        f"(cada una, la mejor de {1 if rapido else 3} vueltas)",
        ("enemigos activos", "eventos por acción", "modelo: media",
         "ciclo completo: media", "p95", "máximo", "por evento", "¿cumple?"),
        filas,
        "p95: el 95 % de las acciones tardó eso o menos (se exige al p95; el "
        "máximo depende también del sistema operativo).")

    tamanos = (1000, 5000) if rapido else (1000, 5000, 10000)
    filas_precarga = []

    for cantidad in tamanos:
        filas_precarga.append((
            str(cantidad),
            formato_tiempo(costo_precarga(cantidad, cantidad)),
            formato_tiempo(costo_precarga(cantidad, cantidad - cantidad // 100)),
        ))

    precarga = tabla(
        "PRECARGA (§4.2): buscar salas para pedir, en cada acción",
        ("salas de la cripta", "toda cargada", "falta el 1 % (lejos)"),
        filas_precarga,
        f"Toda cargada: no busca nada, O(1). Si falta algo: revisa como máximo "
        f"{LIMITE_VISITAS_PRECARGA} salas, sin importar el tamaño de la cripta.")

    return ciclo + "\n\n" + precarga


# ======================================================================
# B7: ciclo con cazadores (capacidad 001, FR-035, SC-004)
# ======================================================================

CAZADORES_CICLO = 50
ID_CRIPTA_REFERENCIA = "cripta-referencia"   # copia local, si se publicó


def _ficha_cazador_bench(rango):
    return {"id": "ent_cazador_bench", "clase": "enemigo",
            "nombre": "Sabueso", "vida_max": 10 ** 6, "ataque": 1,
            "defensa": 1, "velocidad": 100, "comportamiento": "cazador",
            "rango": rango, "suelta": []}


def _fichas_en_arbol(fichas):
    """Las fichas en un ArbolBusqueda por id: los dict de json solo se
    leen y se pasan a nuestras estructuras (principio I)."""
    arbol = ArbolBusqueda()

    for ficha in fichas:
        arbol.insertar(ficha["id"], ficha)

    return arbol


def _activar_salas_con_cazadores(partida):
    """Activa a los cazadores donde estén, como si el jugador hubiera
    pasado por sus salas (P1 §2.4): primera acción en reloj + intervalo."""
    salas = partida.mapa.obtener_todas()

    for i in range(len(salas)):
        sala = salas.obtener(i)

        if sala.cantidad_enemigos() > 0 and sala.id != partida.jugador.sala_actual:
            partida._activar_enemigos(sala)


def partida_con_cazadores(cantidad, semilla=None):
    """2000 salas sintéticas con `cantidad` cazadores repartidos dentro de
    su rango (media cripta), ninguno en la sala del jugador (FR-029). Toda
    cargada y sin red. Devuelve (partida, recorrido fijo del jugador)."""
    from crypta.bench.bench_cazador import SEMILLA, CriptaSintetica

    semilla = SEMILLA if semilla is None else semilla
    cripta = CriptaSintetica(2000, semilla)
    rango = cripta.rango_mediano()
    ficha = _ficha_cazador_bench(rango)
    cripta.mapa.asignar_contenidos(
        cripta.contenidos(cripta.ubicar_cazadores(cantidad, rango)))

    jugador = Jugador("Bench", vida_max=10 ** 9, ataque=8, defensa=3,
                      velocidad=100, inventario_max=8)
    partida = Partida(cripta.mapa, jugador, cripta.sala_jugador.id,
                      _fichas_en_arbol((ficha,)).obtener, semilla=semilla)
    partida.iniciar()
    _activar_salas_con_cazadores(partida)
    return partida, cripta


def _una_vuelta_cazadores(crear, acciones, calentamiento, semilla):
    from crypta.bench.bench_cazador import recorrido_desde

    partida = crear()
    recorrido = recorrido_desde(partida.sala_actual(),
                                calentamiento + acciones, semilla)
    tiempos = Vector()
    eventos = 0

    for numero in range(len(recorrido)):
        direccion = recorrido.obtener(numero)
        antes = partida.agenda.siguiente_secuencia
        transcurrido = cronometrar(lambda: partida.mover(direccion))

        if numero >= calentamiento:
            tiempos.agregar(transcurrido)
            eventos += partida.agenda.siguiente_secuencia - antes

    return tiempos, eventos


def medir_ciclo_cazadores(cantidad, acciones=ACCIONES,
                          calentamiento=CALENTAMIENTO, vueltas=3,
                          semilla=None, crear=None):
    """Ciclo entre dos decisiones del jugador con `cantidad` cazadores
    activos (B7, B8). Cada acción, la mejor de `vueltas` vueltas
    idénticas. El jugador sigue un recorrido fijo: no ataca ni espera, así
    los cazadores siguen buscando rutas."""
    from crypta.bench.bench_cazador import SEMILLA

    semilla = SEMILLA if semilla is None else semilla
    if crear is None:
        crear = lambda: partida_con_cazadores(cantidad, semilla)[0]

    resultado = Medicion(cantidad)
    resultado.ciclo, eventos = _mejor_de(vueltas, lambda: _una_vuelta_cazadores(
        crear, acciones, calentamiento, semilla))
    resultado.eventos_por_accion = eventos / max(1, len(resultado.ciclo))
    return resultado


def partida_de_referencia(carpeta="cache"):
    """La cripta oficial de referencia, si hay una copia local en
    `carpeta` (con el catálogo). None si todavía no se publicó."""
    import json

    ruta = os.path.join(carpeta, ID_CRIPTA_REFERENCIA + ".json")
    ruta_catalogo = os.path.join(carpeta, "catalogo.json")

    if not os.path.exists(ruta) or not os.path.exists(ruta_catalogo):
        return None

    with open(ruta, encoding="utf-8") as archivo:
        guardada = json.load(archivo)
    with open(ruta_catalogo, encoding="utf-8") as archivo:
        fichas = _fichas_en_arbol(
            (json.load(archivo).get("fichas") or {}).values())

    mapa = Mapa()
    mapa.cargar_desde_json(guardada["esqueleto"])
    mapa.asignar_contenidos(guardada.get("contenidos") or ())

    # Las salas sin contenido en la copia quedan vacías.
    salas = mapa.obtener_todas()
    for i in range(len(salas)):
        if not salas.obtener(i).contenido_cargado():
            salas.obtener(i).asignar_contenido(
                {"sala": salas.obtener(i).id, "enemigos": [], "objetos": [],
                 "trampas": []})

    generales = guardada.get("datos_generales") or {}
    sala_inicial = generales.get("sala_inicial") or guardada["esqueleto"][0]["id"]
    jugador = Jugador("Bench", vida_max=10 ** 9, ataque=8, defensa=3,
                      velocidad=100, inventario_max=8)
    partida = Partida(mapa, jugador, sala_inicial, fichas.obtener, semilla=1)
    partida.iniciar()
    _activar_salas_con_cazadores(partida)
    return partida


def ejecutar_ciclo_cazadores(rapido=False, carpeta="cache"):
    """B7 (FR-035, SC-004): p95 del ciclo con 50 cazadores en 2000 salas,
    y en la cripta oficial si hay copia local."""
    acciones = 15 if rapido else ACCIONES
    calentamiento = 5 if rapido else CALENTAMIENTO
    vueltas = 1 if rapido else 3
    filas = []

    casos = Vector(2)
    casos.agregar(("sintética 2000 salas", CAZADORES_CICLO, None))
    if partida_de_referencia(carpeta) is not None:
        casos.agregar(("oficial", None,
                       lambda: partida_de_referencia(carpeta)))

    for i in range(len(casos)):
        nombre, cantidad, crear = casos.obtener(i)
        m = medir_ciclo_cazadores(cantidad, acciones, calentamiento, vueltas,
                                  crear=crear)
        filas.append((nombre, str(cantidad if cantidad else "los suyos"),
                      formato_tiempo(m.media(m.ciclo)),
                      formato_tiempo(m.percentil(m.ciclo, 95)),
                      formato_tiempo(m.maximo(m.ciclo)),
                      "sí" if m.cumple() else "NO"))

    nota = ("Con la cripta oficial publicada se agrega su fila."
            if len(casos) == 1 else
            "La cripta oficial se midió desde la copia local.")

    return tabla(
        f"B7 CICLO CON CAZADORES (FR-035, SC-004: p95 menor que {LIMITE_MS} "
        f"ms). {acciones} acciones del jugador (cada una, la mejor de "
        f"{vueltas} vueltas), con {calentamiento} de calentamiento",
        ("cripta", "cazadores", "media", "p95", "máximo", "¿cumple?"),
        filas,
        "El jugador se mueve por un recorrido fijo, sin atacar ni esperar. "
        + nota)


if __name__ == "__main__":
    print(ejecutar())
