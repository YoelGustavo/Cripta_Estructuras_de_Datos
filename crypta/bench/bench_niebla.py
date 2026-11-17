"""--bench de la niebla de guerra e «ir a» (capacidad 002): secciones N1 a N4
de specs/002-niebla-ir-a/contracts/bench.md.

- Generador (T045, FR-229): mapas conocidos completo, parcial y
  desactualizado sobre las `CriptaSintetica` de la 001; la copia local más
  grande (solo su esqueleto) o una sintética de 300 salas; pares de viajes y
  la huella.
- N1 (T046): consultas al mapa conocido, elegida frente a `ArbolBusqueda`.
- N2 (T047): exploración con antorcha y su reversión, elegida frente a
  «copia del mapa conocido por acción».
- N3 (T048): el paso de «ir a» con reutilización selectiva, total y
  recalculando.
- N4 (T049): igualdad de N1 a N3 con sus alternativas, fuera de lo
  cronometrado.

Mide directamente sobre `Mapa`, `MapaConocido` y `RutaConocida`, sin
`Partida`, sin vista y sin red (FR-233). `MapaConocido` recibe la función de
anotar que corresponde (research D3): en N2, la de un `RegistroAccion` por
entrada; en N1 y N3, una que no hace nada. Los dict y list de este archivo
son el JSON del esqueleto o datos para la huella (principio I).
"""

import gc
import hashlib
import json
import os
import random
import time

from crypta.bench.bench_cazador import SEMILLA, CriptaSintetica
from crypta.bench.bench_ciclo import Medicion
from crypta.bench.medicion import formato_tiempo, tabla
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.MapaConocido import DESCONOCIDA, EXPLORADA, MapaConocido
from crypta.Modelo.Perseguidor import RECALCULAR, SELECTIVA, TOTAL
from crypta.Modelo.Puerta import ABIERTA, CERRADA
from crypta.Modelo.RutaConocida import RutaConocida
from crypta.Modelo.Sala import indice_direccion


CARPETA_COPIAS = "cache"           # la de la aplicación; las pruebas pasan otra

FRACCION_DESACTUALIZADA = 0.05     # puertas cerradas recordadas abiertas
LIMITE_COCIENTE = 2                # N1 y N2 (FR-235, FR-236): <= 2
LIMITE_PASO_MS = 5                 # N3 (principio VI, «Paso de ir a»): p95 < 5
TAMANO_REFERENCIA = 300            # sintética si no hay copias locales


def _no_anotar(cambio):
    """La función de anotar de N1 y N3: no se deshace nada."""


_PERCENTIL = Medicion(0)           # el mismo percentil que la 001


# ======================================================================
# Generador (T045, FR-229)
# ======================================================================

_CRIPTAS = Vector()                # (salas, CriptaSintetica) ya generadas


def _cripta(salas):
    """Las criptas se generan una vez por tamaño. Solo se cambia lo que
    recuerda el jugador, y cada mapa conocido se arma de nuevo."""
    for i in range(len(_CRIPTAS)):
        cantidad, cripta = _CRIPTAS.obtener(i)
        if cantidad == salas:
            return cripta

    cripta = CriptaSintetica(salas)
    _CRIPTAS.agregar((salas, cripta))
    return cripta


def olvidar_puertas(mapa):
    """Deja todas las puertas sin observar (`recordada = None`). Las
    criptas se reutilizan entre secciones y lo recordado vive en cada
    `EstadoPuerta`: cada sección empieza sin lo que dejó la anterior, como
    una partida nueva (ninguna puerta de una sala desconocida observada)."""
    for i in range(mapa.cantidad_salas()):
        puertas = mapa.sala_por_indice(i).puertas()
        for j in range(len(puertas)):
            puertas.obtener(j).estado.recordada = None


def centro_de(cripta):
    return cripta.mapa.obtener_sala(cripta.id_de(cripta.alto // 2,
                                                 cripta.ancho // 2))


def mapa_conocido_completo(mapa, anotar):
    """Todas las salas exploradas y cada puerta recordada con su estado
    real. O(V + E)."""
    conocimiento = MapaConocido(mapa, anotar)

    for i in range(mapa.cantidad_salas()):
        conocimiento.explorar(mapa.sala_por_indice(i))

    return conocimiento


def mapa_conocido_parcial(mapa, n, anotar, centro=None):
    """Las n primeras salas de un recorrido en anchura desde `centro` (por
    omisión, la sala de la mitad del índice), exploradas con `explorar`."""
    if centro is None:
        centro = mapa.sala_por_indice(mapa.cantidad_salas() // 2)

    conocimiento = MapaConocido(mapa, anotar)
    visto = Vector(mapa.cantidad_salas())
    for _ in range(mapa.cantidad_salas()):
        visto.agregar(False)

    cola = Vector()                # cola con un índice de frente
    cola.agregar(centro)
    visto.asignar(centro.indice, True)
    frente = 0
    exploradas = 0

    while frente < len(cola) and exploradas < n:
        sala = cola.obtener(frente)
        frente += 1
        conocimiento.explorar(sala)
        exploradas += 1
        puertas = sala.puertas()

        for i in range(len(puertas)):
            destino = puertas.obtener(i).sala_destino_ref

            if destino is not None and not visto.obtener(destino.indice):
                visto.asignar(destino.indice, True)
                cola.agregar(destino)

    return conocimiento


def desactualizar(mapa, conocimiento, fraccion, azar):
    """Una `fraccion` de las puertas cerradas (elegidas con `azar`) queda
    recordada abierta: el viaje las descubre al observar. Escribe sin
    anotar: arma el estado de partida. Devuelve cuántas cambió."""
    cerradas = Vector()

    for i in range(mapa.cantidad_salas()):
        sala = mapa.sala_por_indice(i)
        puertas = sala.puertas()

        for j in range(len(puertas)):
            estado = puertas.obtener(j).estado

            # Un solo lado de cada salida compartida.
            if (estado.cerrada and estado.extremos[0] is sala
                    and conocimiento.recordada(puertas.obtener(j)) == CERRADA):
                cerradas.agregar(estado)

    if len(cerradas) == 0:
        return 0

    cantidad = max(1, round(fraccion * len(cerradas)))

    for indice in azar.sample(range(len(cerradas)), cantidad):
        cerradas.obtener(indice).recordada = ABIERTA

    return cantidad


def copia_mas_grande(carpeta):
    """(id, Mapa) del esqueleto de la copia local con más salas de
    `carpeta`, o None. El id no se escribe en el código (principio IV)."""
    if carpeta is None or not os.path.isdir(carpeta):
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

        clave = (-len(datos["esqueleto"]), nombre)      # empate: por nombre

        if mejor is None or clave < mejor[2]:
            mejor = (nombre[:-len(".json")], datos["esqueleto"], clave)

    if mejor is None:
        return None

    mapa = Mapa()
    mapa.cargar_desde_json(mejor[1])
    return mejor[0], mapa


def _largo_de_ruta(ruta, origen, destino, tope):
    """Pasos de la ruta conocida de `origen` a `destino` sin moverse ni
    observar, o None si no hay ruta."""
    sala = origen
    pasos = 0

    while sala is not destino:
        puerta = ruta.siguiente_paso(sala, destino)

        if puerta is None or pasos > tope:
            return None

        sala = puerta.sala_destino_ref
        pasos += 1

    return pasos


def viajes(mapa, conocimiento, azar, minimo_viajes=20, minimo_pasos=200):
    """(pares, pasos): `Vector` de pares (origen, destino) distintos, entre
    salas exploradas y con ruta conocida, elegidos con `azar` hasta tener
    al menos `minimo_viajes` y `minimo_pasos` pasos en total (medidos sobre
    el conocimiento de ahora). No cambia el conocimiento."""
    exploradas = Vector()
    for sala, estado in conocimiento.salas_conocidas():
        if estado == EXPLORADA:
            exploradas.agregar(sala)

    ruta = RutaConocida(mapa, conocimiento)
    pares = Vector()
    vistos = ArbolBusqueda()
    pasos = 0
    intentos = 0
    tope = 4 * mapa.cantidad_salas()

    while ((len(pares) < minimo_viajes or pasos < minimo_pasos)
           and intentos < 100 * (minimo_viajes + minimo_pasos)):
        intentos += 1
        origen = exploradas.obtener(azar.randrange(len(exploradas)))
        destino = exploradas.obtener(azar.randrange(len(exploradas)))

        if origen is destino or vistos.contiene((origen.id, destino.id)):
            continue

        largo = _largo_de_ruta(ruta, origen, destino, tope)

        if largo is None:
            continue

        vistos.insertar((origen.id, destino.id), True)
        pares.agregar((origen, destino))
        pasos += largo

    return pares, pasos


def _foto_conocimiento(mapa, conocimiento):
    """Estados de todas las salas y `recordada` de todas las salidas."""
    foto = []

    for i in range(mapa.cantidad_salas()):
        sala = mapa.sala_por_indice(i)
        puertas = sala.puertas()
        foto.append([conocimiento.estado(sala)]
                    + [puertas.obtener(j).estado.recordada
                       for j in range(len(puertas))])

    return foto


def huella(mapa, conocimiento, pares, elegidos):
    """HU5-1: salas, salidas, puertas cerradas, estados del mapa conocido,
    pares de viajes y pasos elegidos, serializados en orden."""
    salas = []

    for i in range(mapa.cantidad_salas()):
        sala = mapa.sala_por_indice(i)
        puertas = sala.puertas()
        salas.append([sala.id] + [[sala.direccion_de(p), p.sala_destino,
                                   p.costo, p.estado.cerrada]
                                  for p in (puertas.obtener(j)
                                            for j in range(len(puertas)))])

    datos = {
        "salas": salas,
        "conocimiento": _foto_conocimiento(mapa, conocimiento),
        "pares": [[pares.obtener(i)[0].id, pares.obtener(i)[1].id]
                  for i in range(len(pares))],
        "pasos": [list(elegidos.obtener(i)) for i in range(len(elegidos))],
    }
    texto = json.dumps(datos, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def huella_n3(semilla=SEMILLA):
    """La huella de una corrida de N3 sobre una sintética de 300 salas con
    conocimiento desactualizado (HU5-1). Genera la cripta de nuevo."""
    mapa = CriptaSintetica(TAMANO_REFERENCIA, semilla).mapa
    conocimiento = mapa_conocido_completo(mapa, _no_anotar)
    desactualizar(mapa, conocimiento, FRACCION_DESACTUALIZADA,
                  random.Random(semilla))
    pares, _ = viajes(mapa, conocimiento, random.Random(semilla), 5, 50)
    resultado = simular_viajes(mapa, conocimiento, pares, SELECTIVA,
                               calentar=False)
    return huella(mapa, conocimiento, pares, resultado.elegidos)


# ======================================================================
# N1: consultas al mapa conocido (T046; FR-230, FR-235)
# ======================================================================

class ConsultasN1:
    """Las salas y salidas conocidas de un mapa conocido, las consultas
    elegidas con la semilla y los dos árboles de la alternativa, armados
    con `desde_ordenados` (insertar en orden degeneraría el árbol)."""

    def __init__(self, conocimiento, consultas, azar):
        self.conocimiento = conocimiento
        salas = Vector()
        pares_salas = Vector()
        puertas = Vector()
        pares_puertas = Vector()

        # salas_conocidas va en orden de id, y las salidas en N, S, E, O:
        # las claves salen ordenadas.
        for sala, estado in conocimiento.salas_conocidas():
            salas.agregar(sala)
            pares_salas.agregar((sala.id, estado))

            if estado != EXPLORADA:
                continue

            lista = sala.puertas()
            for j in range(len(lista)):
                puerta = lista.obtener(j)
                clave = (sala.id, indice_direccion(sala.direccion_de(puerta)))
                puertas.agregar((puerta, clave))
                pares_puertas.agregar((clave, puerta.estado.recordada))

        self.arbol_salas = ArbolBusqueda.desde_ordenados(pares_salas)
        self.arbol_puertas = ArbolBusqueda.desde_ordenados(pares_puertas)

        self.salas = Vector(consultas)
        self.puertas = Vector(consultas)
        for _ in range(consultas):
            self.salas.agregar(salas.obtener(azar.randrange(len(salas))))
            self.puertas.agregar(puertas.obtener(azar.randrange(len(puertas))))

    def medir(self):
        """(estado elegida, recordada elegida, estado árbol, recordada
        árbol): media por consulta en segundos."""
        n = len(self.salas)
        conocimiento = self.conocimiento
        arbol_salas = self.arbol_salas
        arbol_puertas = self.arbol_puertas
        salas = self.salas
        puertas = self.puertas
        tiempos = []
        activo = gc.isenabled()
        gc.disable()

        try:
            inicio = time.perf_counter_ns()
            for i in range(n):
                conocimiento.estado(salas.obtener(i))
            tiempos.append(time.perf_counter_ns() - inicio)

            inicio = time.perf_counter_ns()
            for i in range(n):
                conocimiento.recordada(puertas.obtener(i)[0])
            tiempos.append(time.perf_counter_ns() - inicio)

            inicio = time.perf_counter_ns()
            for i in range(n):
                arbol_salas.obtener(salas.obtener(i).id)
            tiempos.append(time.perf_counter_ns() - inicio)

            inicio = time.perf_counter_ns()
            for i in range(n):
                arbol_puertas.obtener(puertas.obtener(i)[1])
            tiempos.append(time.perf_counter_ns() - inicio)
        finally:
            if activo:
                gc.enable()

        return [t / n / 1e9 for t in tiempos]

    def comparar(self, diferencias):
        """N4: cada consulta da lo mismo con la elegida y con el árbol.
        Devuelve cuántas comparó."""
        for i in range(len(self.salas)):
            sala = self.salas.obtener(i)
            if self.conocimiento.estado(sala) != self.arbol_salas.obtener(sala.id):
                diferencias.agregar(f"N1: la sala {sala.id} da otro estado")

            puerta, clave = self.puertas.obtener(i)
            if (self.conocimiento.recordada(puerta)
                    != self.arbol_puertas.obtener(clave)):
                diferencias.agregar(f"N1: la salida {clave} da otro recordado")

        return 2 * len(self.salas)


def _casos_n1(rapido):
    cripta = _cripta(2000)
    mapa = cripta.mapa
    olvidar_puertas(mapa)
    consultas = 2000 if rapido else 100_000
    centro = centro_de(cripta)
    casos = Vector(2)
    # El parcial antes que el completo: los dos escriben el estado real en
    # las puertas que observan, así que no se pisan.
    for exploradas, conocimiento in (
            (200, mapa_conocido_parcial(mapa, 200, _no_anotar, centro)),
            (2000, mapa_conocido_completo(mapa, _no_anotar))):
        casos.agregar((exploradas, ConsultasN1(conocimiento, consultas,
                                               random.Random(SEMILLA))))
    return consultas, casos


def ejecutar_n1(rapido=False):
    """N1 (FR-230, FR-235; SC-205): consultas de `estado` y `recordada` con
    200 y 2000 salas exploradas, elegida frente a `ArbolBusqueda`."""
    consultas, casos = _casos_n1(rapido)
    filas = []
    medias = Vector(2)

    for i in range(len(casos)):
        exploradas, caso = casos.obtener(i)
        caso.medir()                                  # calentamiento
        estado, recordada, arbol_estado, arbol_recordada = caso.medir()
        medias.agregar(((estado + recordada) / 2,
                        (arbol_estado + arbol_recordada) / 2))
        filas.append(("Vector + EstadoPuerta", str(exploradas),
                      formato_tiempo(estado), formato_tiempo(recordada)))
        filas.append(("ArbolBusqueda", str(exploradas),
                      formato_tiempo(arbol_estado),
                      formato_tiempo(arbol_recordada)))

    pequeno, grande = medias.obtener(0), medias.obtener(1)
    cociente = grande[0] / pequeno[0]
    cociente_arbol = grande[1] / pequeno[1]
    cumple = cociente <= LIMITE_COCIENTE

    return tabla(
        f"N1 CONSULTAS AL MAPA CONOCIDO (FR-230, FR-235). 2000 salas, "
        f"{consultas} consultas de cada tipo",
        ("estructura", "exploradas", "estado: media", "recordada: media"),
        filas,
        f"cociente 2000 / 200: elegida {cociente:.2f}, ArbolBusqueda "
        f"{cociente_arbol:.2f} (límite de la elegida <= {LIMITE_COCIENTE}). "
        f"¿cumple? {'sí' if cumple else 'NO'}. El árbol también crece poco "
        f"(log n); se descarta por el costo por consulta y porque cada puerta "
        f"tendría que escribirse por los dos lados (research D1).")


# ======================================================================
# N2: exploración con antorcha y su reversión (T047; FR-230, FR-236)
# ======================================================================

def explorar_con_antorcha(conocimiento, sala):
    """Lo que hace la Partida al entrar con antorcha (FR-212, FR-213): la
    sala y cada destino de sus salidas, abiertas o cerradas."""
    conocimiento.explorar(sala)
    puertas = sala.puertas()

    for i in range(len(puertas)):
        destino = puertas.obtener(i).sala_destino_ref

        if destino is not None:
            conocimiento.explorar(destino)


def elegir_entradas_n2(cripta, region, azar, cantidad):
    """`cantidad` salas (con repetición) elegidas con `azar` entre las que
    están a más de 2 pasos de toda sala conocida de `region`, contando
    salidas y entradas: ni la sala, ni sus vecinas, ni los destinos de
    estas tocan la región, así que cada entrada revela lo mismo en los dos
    mapas."""
    mapa = cripta.mapa
    total = mapa.cantidad_salas()
    pasos = Vector(total)
    for _ in range(total):
        pasos.agregar(None)

    frente = Vector()
    for sala, _ in region.salas_conocidas():
        pasos.asignar(sala.indice, 0)
        frente.agregar(sala)

    for nivel in (1, 2):
        siguiente = Vector()

        for i in range(len(frente)):
            sala = frente.obtener(i)
            vecinas = Vector()
            puertas = sala.puertas()
            for j in range(len(puertas)):
                vecinas.agregar(puertas.obtener(j).sala_destino_ref)
            for j in range(len(sala.entradas)):
                vecinas.agregar(sala.entradas.obtener(j)[1])

            for j in range(len(vecinas)):
                vecina = vecinas.obtener(j)
                if vecina is not None and pasos.obtener(vecina.indice) is None:
                    pasos.asignar(vecina.indice, nivel)
                    siguiente.agregar(vecina)

        frente = siguiente

    lejanas = Vector()
    for i in range(total):
        if pasos.obtener(i) is None:
            lejanas.agregar(mapa.sala_por_indice(i))

    entradas = Vector(cantidad)
    for _ in range(cantidad):
        entradas.agregar(lejanas.obtener(azar.randrange(len(lejanas))))
    return entradas


class CopiaPorAccion:
    """La alternativa de N2 (prohibida por el principio VII; solo se mide):
    antes de cada acción se copia el mapa conocido entero (cada sala
    conocida con lo que recuerda de sus salidas) y deshacer es volver a la
    copia. Cuesta O(salas conocidas) por acción.

    Lleva la lista de salas conocidas, como la llevaría un mapa guardado
    como lista; las que se conocen durante la acción las saca del aviso de
    cambio de sala (solo para saber qué borrar al volver)."""

    def __init__(self, mapa):
        self.mapa = mapa
        self.conocidas = Vector()
        self.nuevas = Vector()

    def anotar(self, cambio):
        if (cambio.operacion == "restaurar_sala"
                and cambio.dato[1] == DESCONOCIDA):
            self.nuevas.agregar(cambio.dato[0])

    def empezar(self, conocimiento):
        self.conocidas = Vector()
        for sala, _ in conocimiento.salas_conocidas():
            self.conocidas.agregar(sala.indice)

    def copiar(self, conocimiento):
        copia = Vector(len(self.conocidas))
        self.nuevas = Vector()

        for i in range(len(self.conocidas)):
            indice = self.conocidas.obtener(i)
            sala = self.mapa.sala_por_indice(indice)
            puertas = sala.puertas()
            recordadas = Vector(len(puertas))
            for j in range(len(puertas)):
                estado = puertas.obtener(j).estado
                recordadas.agregar((estado, estado.recordada))
            copia.agregar((indice, conocimiento.estado(sala), recordadas))

        return copia

    def volver(self, conocimiento, copia):
        for i in range(len(self.nuevas)):
            indice = self.nuevas.obtener(i)
            conocimiento.restaurar_sala((indice, DESCONOCIDA))
            puertas = self.mapa.sala_por_indice(indice).puertas()
            for j in range(len(puertas)):
                conocimiento.restaurar_puerta((puertas.obtener(j).estado, None))

        for i in range(len(copia)):
            indice, estado, recordadas = copia.obtener(i)
            conocimiento.restaurar_sala((indice, estado))
            for j in range(len(recordadas)):
                conocimiento.restaurar_puerta(recordadas.obtener(j))


def _firma(cambio):
    """Un cambio, comparable entre dos mapas conocidos sobre el mismo
    mapa: la operación, qué tocó y el valor anterior."""
    objetivo, anterior = cambio.dato

    if cambio.operacion == "restaurar_puerta":
        origen, destino = objetivo.extremos
        objetivo = (origen.id, None if destino is None else destino.id)

    return cambio.operacion, objetivo, anterior


def _foto_local(conocimiento, sala):
    """Estados y recordados de la sala, sus vecinas y los destinos de
    estas: todo lo que puede tocar una entrada con antorcha."""
    foto = []
    nivel = [sala]

    for _ in range(3):
        siguiente = []
        for actual in nivel:
            foto.append(conocimiento.estado(actual))
            puertas = actual.puertas()
            for j in range(len(puertas)):
                puerta = puertas.obtener(j)
                foto.append(puerta.estado.recordada)
                if puerta.sala_destino_ref is not None:
                    siguiente.append(puerta.sala_destino_ref)
        nivel = siguiente

    return foto + [conocimiento.exploradas, conocimiento.avistadas]


class ResultadoN2:
    def __init__(self, tamano):
        self.tamano = tamano
        self.explorar = Vector()
        self.deshacer = Vector()
        self.copia_explorar = Vector()
        self.copia_deshacer = Vector()
        self.cambios = Vector()          # firmas de cada entrada
        self.total_cambios = 0


def _correr_n2(rapido, verificar, diferencias):
    """Corre las entradas sobre los dos mapas parciales. Devuelve
    (cripta, resultados, entradas comparadas, diferencias de N4)."""
    salas, tamanos, cantidad = ((2000, (20, 200), 50) if rapido
                                else (20000, (200, 2000), 1000))
    cripta = _cripta(salas)
    mapa = cripta.mapa
    olvidar_puertas(mapa)
    centro = centro_de(cripta)
    vigente = [None]                     # el RegistroAccion de la entrada
    alternativa = CopiaPorAccion(mapa)

    def anotar(cambio):
        if vigente[0] is not None:
            vigente[0].registrar_cambio(cambio)
            firmas.append(_firma(cambio))
        else:
            alternativa.anotar(cambio)

    firmas = []
    mapas = Vector(2)
    # Al armarlos no hay registro vigente: los cambios van a la alternativa,
    # que los olvida al empezar.
    for tamano in tamanos:
        mapas.agregar(mapa_conocido_parcial(mapa, tamano, anotar, centro))

    entradas = elegir_entradas_n2(cripta, mapas.obtener(1),
                                  random.Random(SEMILLA), cantidad)
    resultados = Vector(2)
    comparadas = 0
    activo = gc.isenabled()

    for m in range(2):
        conocimiento = mapas.obtener(m)
        resultado = ResultadoN2(tamanos[m])
        alternativa.empezar(conocimiento)

        for e in range(len(entradas)):
            sala = entradas.obtener(e)
            antes = _foto_local(conocimiento, sala) if verificar else None

            # La elegida: un Cambio por valor que cambia; deshacer en orden
            # inverso.
            firmas = []
            registro = RegistroAccion()
            vigente[0] = registro
            gc.disable()
            inicio = time.perf_counter_ns()
            explorar_con_antorcha(conocimiento, sala)
            medio = time.perf_counter_ns()
            vigente[0] = None
            registro.deshacer()
            fin = time.perf_counter_ns()
            if activo:
                gc.enable()
            resultado.explorar.agregar(medio - inicio)
            resultado.deshacer.agregar(fin - medio)
            resultado.cambios.agregar(firmas)
            resultado.total_cambios += registro.cantidad_cambios()

            if verificar:
                firmas = []
                vigente[0] = RegistroAccion()
                explorar_con_antorcha(conocimiento, sala)
                despues = _foto_local(conocimiento, sala)
                vigente[0].deshacer()
                vigente[0] = None
                if _foto_local(conocimiento, sala) != antes:
                    diferencias.agregar(f"N2: deshacer la entrada {e} (sala "
                                        f"{sala.id}) no deja el mapa como "
                                        f"estaba")

            # La alternativa: copiar todo, actuar, volver a la copia.
            gc.disable()
            inicio = time.perf_counter_ns()
            copia = alternativa.copiar(conocimiento)
            explorar_con_antorcha(conocimiento, sala)
            medio = time.perf_counter_ns()
            if verificar:
                gc.enable()
                if _foto_local(conocimiento, sala) != despues:
                    diferencias.agregar(f"N2: la entrada {e} revela distinto "
                                        f"con la copia por acción")
                gc.disable()
                medio = time.perf_counter_ns()
            alternativa.volver(conocimiento, copia)
            fin = time.perf_counter_ns()
            if activo:
                gc.enable()
            resultado.copia_explorar.agregar(medio - inicio)
            resultado.copia_deshacer.agregar(fin - medio)

            if verificar:
                comparadas += 1
                if _foto_local(conocimiento, sala) != antes:
                    diferencias.agregar(f"N2: volver a la copia en la entrada "
                                        f"{e} no deja el mapa como estaba")

        resultados.agregar(resultado)

    return cripta, resultados, comparadas


def _media(tiempos):
    total = 0
    for i in range(len(tiempos)):
        total += tiempos.obtener(i)
    return total / max(1, len(tiempos)) / 1e9


def ejecutar_n2(rapido=False):
    """N2 (FR-230, FR-236; SC-205): exploración con antorcha y su
    reversión con mapas conocidos de 200 y 2000 salas. Devuelve
    (texto, errores): ERROR si una entrada registra cambios distintos en
    los dos mapas (la comparación no sería justa)."""
    cripta, resultados, _ = _correr_n2(rapido, False, Vector())
    pequeno, grande = resultados.obtener(0), resultados.obtener(1)
    errores = Vector()

    for e in range(len(pequeno.cambios)):
        if pequeno.cambios.obtener(e) != grande.cambios.obtener(e):
            errores.agregar(f"N2: la entrada {e} registra cambios distintos "
                            f"con {pequeno.tamano} y con {grande.tamano} "
                            f"salas conocidas")

    filas = []
    for resultado in (pequeno, grande):
        entradas = len(resultado.explorar)
        filas.append((str(resultado.tamano),
                      formato_tiempo(_media(resultado.explorar)),
                      formato_tiempo(_media(resultado.deshacer)),
                      formato_tiempo(_media(resultado.copia_explorar)),
                      formato_tiempo(_media(resultado.copia_deshacer)),
                      f"{resultado.total_cambios / max(1, entradas):.1f}"))

    def cociente(nombre):
        return _media(getattr(grande, nombre)) / _media(getattr(pequeno, nombre))

    c_explorar, c_deshacer = cociente("explorar"), cociente("deshacer")
    cumple = c_explorar <= LIMITE_COCIENTE and c_deshacer <= LIMITE_COCIENTE
    salas = cripta.mapa.cantidad_salas()

    texto = tabla(
        f"N2 EXPLORACIÓN CON ANTORCHA Y SU REVERSIÓN (FR-230, FR-236). "
        f"{salas} salas, {len(pequeno.explorar)} entradas a más de 2 pasos "
        f"de lo conocido",
        ("conocidas", "explorar", "deshacer", "copia por acción: explorar",
         "copia por acción: deshacer", "cambios por entrada"),
        filas,
        f"cociente {grande.tamano} / {pequeno.tamano}: explorar "
        f"{c_explorar:.2f}, deshacer {c_deshacer:.2f}; copia por acción: "
        f"explorar {cociente('copia_explorar'):.2f}, deshacer "
        f"{cociente('copia_deshacer'):.2f} (límite de la elegida <= "
        f"{LIMITE_COCIENTE}). ¿cumple? {'sí' if cumple else 'NO'}. "
        f"La copia por acción está prohibida por el principio VII: solo se "
        f"mide para mostrar que crece con lo conocido.")

    texto += _lineas_error(errores)
    return texto, len(errores)


def _lineas_error(errores):
    texto = ""
    for i in range(min(20, len(errores))):
        texto += f"\nERROR: {errores.obtener(i)}"
    if len(errores) > 20:
        texto += f"\nERROR: ... y {len(errores) - 20} diferencias más"
    return texto


# ======================================================================
# N3: el paso de «ir a» (T048; FR-231, FR-234)
# ======================================================================

class ResultadoN3:
    def __init__(self):
        self.tiempos = Vector()          # ns de cada paso
        self.primeros = Vector()         # ns del primer paso de cada viaje
        self.pasos_por_viaje = Vector()
        self.buscaron = 0
        self.busquedas = 0
        self.invalidaciones = 0
        self.asentadas = 0
        self.sin_ruta = 0
        self.elegidos = Vector()         # (sala, dirección) de cada paso
        self.comparados = 0


def simular_viajes(mapa, conocimiento, pares, modo, fabrica=None,
                   diferencias=None, calentar=True, nombre=""):
    """Hace los viajes de `pares` con una ruta del `modo` dado registrada
    como observador del conocimiento. Antes de cada paso se observan las
    salidas de la sala actual (lo que hace la Partida); solo se cronometra
    `siguiente_paso`. Con `diferencias`, compara cada paso con
    `paso_desde_cero` fuera de lo cronometrado (N4)."""
    fabrica = fabrica or RutaConocida
    ruta = fabrica(mapa, conocimiento, modo)
    conocimiento.observador = ruta
    resultado = ResultadoN3()
    tope = 4 * mapa.cantidad_salas()
    activo = gc.isenabled()

    if calentar:                         # un viaje que no se reporta
        _un_viaje(ruta, conocimiento, pares.obtener(0), ResultadoN3(), None,
                  tope, nombre)
        resultado.busquedas = -ruta.busquedas
        resultado.invalidaciones = -ruta.invalidaciones
        resultado.asentadas = -ruta.asentadas

    for i in range(len(pares)):
        gc.disable()
        try:
            _un_viaje(ruta, conocimiento, pares.obtener(i), resultado,
                      diferencias, tope, nombre)
        finally:
            if activo:
                gc.enable()

    resultado.busquedas += ruta.busquedas
    resultado.invalidaciones += ruta.invalidaciones
    resultado.asentadas += ruta.asentadas
    conocimiento.observador = None
    return resultado


def _un_viaje(ruta, conocimiento, par, resultado, diferencias, tope, nombre):
    origen, destino = par
    sala = origen
    conocimiento.observar(sala)
    pasos = 0

    while sala is not destino:
        busquedas = ruta.busquedas
        inicio = time.perf_counter_ns()
        puerta = ruta.siguiente_paso(sala, destino)
        transcurrido = time.perf_counter_ns() - inicio

        resultado.tiempos.agregar(transcurrido)
        if pasos == 0:
            resultado.primeros.agregar(transcurrido)
        if ruta.busquedas > busquedas:
            resultado.buscaron += 1

        if diferencias is not None:
            resultado.comparados += 1
            desde_cero = ruta.paso_desde_cero(sala, destino)
            if desde_cero is not puerta:
                diferencias.agregar(
                    f"N3 {nombre}: de la sala {sala.id} a la {destino.id} "
                    f"eligió {_texto_paso(sala, puerta)} y desde cero "
                    f"{_texto_paso(sala, desde_cero)}")

        if puerta is None:
            resultado.sin_ruta += 1
            break

        resultado.elegidos.agregar((sala.id, sala.direccion_de(puerta)))
        sala = puerta.sala_destino_ref
        pasos += 1
        conocimiento.observar(sala)      # el movimiento y la observación

        if pasos > tope:
            if diferencias is not None:
                diferencias.agregar(f"N3 {nombre}: el viaje a la sala "
                                    f"{destino.id} no termina")
            break

    resultado.pasos_por_viaje.agregar(pasos)


def _texto_paso(sala, puerta):
    return "ninguno" if puerta is None else sala.direccion_de(puerta)


def _casos_n3(rapido, carpeta):
    """(nombre, mapa, desactualizado, modos, mínimo de viajes, mínimo de
    pasos) de (a), (b) y (c). En modo rápido, (a) y (b) usan la sintética
    de 300 salas: N4 compara cada paso con un cálculo desde cero y con 2000
    salas tardaría demasiado para las pruebas."""
    minimo_viajes, minimo_pasos = (3, 30) if rapido else (20, 200)
    grande = _cripta(TAMANO_REFERENCIA if rapido else 2000).mapa
    salas = grande.cantidad_salas()
    copia = copia_mas_grande(carpeta)

    if copia is None:
        referencia = _cripta(TAMANO_REFERENCIA).mapa
        nombre_c = f"sintética {TAMANO_REFERENCIA} salas"
    else:
        referencia = copia[1]
        nombre_c = f"{copia[0]} ({referencia.cantidad_salas()} salas)"

    return (
        (f"(a) {salas} salas, completo", grande, False,
         (SELECTIVA, RECALCULAR), minimo_viajes, minimo_pasos),
        (f"(b) {salas} salas, desactualizado", grande, True,
         (SELECTIVA, TOTAL, RECALCULAR), minimo_viajes, minimo_pasos),
        (f"(c) {nombre_c}, completo", referencia, False,
         (SELECTIVA, RECALCULAR), minimo_viajes, 0),
    )


def _conocimiento_n3(mapa, desactualizado):
    """El mismo mapa conocido de partida para cada variante: armarlo de
    nuevo deja cada `recordada` como al principio."""
    olvidar_puertas(mapa)
    conocimiento = mapa_conocido_completo(mapa, _no_anotar)
    if desactualizado:
        desactualizar(mapa, conocimiento, FRACCION_DESACTUALIZADA,
                      random.Random(SEMILLA))
    return conocimiento


def _correr_n3(rapido, carpeta, fabrica=None, diferencias=None):
    """Vector de (caso, modo, ResultadoN3)."""
    salida = Vector()

    for (nombre, mapa, desactualizado, modos, minimo_viajes,
         minimo_pasos) in _casos_n3(rapido, carpeta):
        pares, _ = viajes(mapa, _conocimiento_n3(mapa, desactualizado),
                          random.Random(SEMILLA), minimo_viajes, minimo_pasos)
        primera = None

        for modo in modos:
            conocimiento = _conocimiento_n3(mapa, desactualizado)
            resultado = simular_viajes(mapa, conocimiento, pares, modo,
                                       fabrica, diferencias,
                                       nombre=f"{nombre} {modo}")
            salida.agregar((nombre, modo, resultado))

            if diferencias is None:
                continue

            if primera is None:
                primera = resultado
            elif not _mismos_pasos(primera.elegidos, resultado.elegidos):
                diferencias.agregar(f"N3 {nombre}: {modo} elige otros pasos "
                                    f"que {modos[0]}")

    return salida


def _mismos_pasos(a, b):
    if len(a) != len(b):
        return False
    for i in range(len(a)):
        if a.obtener(i) != b.obtener(i):
            return False
    return True


def _ms(ns):
    return ns / 1e6


def _estadisticas(tiempos):
    """(media, p95, máximo) en segundos."""
    if len(tiempos) == 0:
        return 0.0, 0.0, 0.0
    return (_media(tiempos), _PERCENTIL.percentil(tiempos, 95) / 1e9,
            _PERCENTIL.maximo(tiempos) / 1e9)


def ejecutar_n3(rapido=False, carpeta=None):
    """N3 (FR-231, FR-234; SC-204; principio VI «Paso de ir a: 5 ms»)."""
    carpeta = carpeta if carpeta is not None else CARPETA_COPIAS
    corridas = _correr_n3(rapido, carpeta)
    filas_pasos = []
    filas_busqueda = []
    limites = []

    for i in range(len(corridas)):
        nombre, modo, r = corridas.obtener(i)
        media, p95, maximo = _estadisticas(r.tiempos)
        p_media, p_p95, p_maximo = _estadisticas(r.primeros)
        total = len(r.tiempos)

        if modo == SELECTIVA and not nombre.startswith("(b)"):
            cumple = "sí" if p95 * 1000 < LIMITE_PASO_MS else "NO"
            if p_maximo * 1000 >= LIMITE_PASO_MS:
                limites.append(f"{nombre}: el primer paso llega a "
                               f"{formato_tiempo(p_maximo)}")
        else:
            cumple = "-"

        por_viaje = r.pasos_por_viaje
        largos = [por_viaje.obtener(j) for j in range(len(por_viaje))]
        filas_pasos.append((
            nombre, modo, str(total), formato_tiempo(media),
            formato_tiempo(p95), formato_tiempo(maximo), cumple))
        filas_busqueda.append((
            nombre, modo, formato_tiempo(p_media), formato_tiempo(p_p95),
            formato_tiempo(p_maximo),
            f"{min(largos)} / {sum(largos) / len(largos):.1f} / {max(largos)}",
            f"{100 * r.buscaron / max(1, total):.1f} %",
            str(r.busquedas), str(r.invalidaciones), str(r.asentadas)))

    texto = tabla(
        "N3 PASO DE «IR A» (FR-231, FR-234): todos los pasos",
        ("caso", "variante", "pasos", "media", "p95", "máximo", "¿cumple?"),
        filas_pasos,
        f"Límite: p95 < {LIMITE_PASO_MS} ms con la selectiva en (a) y (c). "
        f"El p95 incluye los pasos que buscan; el criterio se cumple si esos "
        f"pasos son menos del 5 % del total (research D6).")
    texto += "\n" + tabla(
        "N3 primer paso de cada viaje y búsquedas",
        ("caso", "variante", "primer paso: media", "p95", "máximo",
         "pasos por viaje (mín / media / máx)", "buscaron", "búsquedas",
         "invalidaciones", "asentadas"),
        filas_busqueda,
        "Solo se cronometra siguiente_paso; la observación y el movimiento "
        "no. Hubo un viaje de calentamiento que no se reporta.")

    for linea in limites:
        texto += f"\nPara Límites (FR-234): {linea} (más de {LIMITE_PASO_MS} ms)."

    return texto


# ======================================================================
# N4: igualdad con la alternativa (T049; FR-232, SC-203)
# ======================================================================

def ejecutar_n4(rapido=False, fabrica=None):
    """N4 (FR-232; SC-203): fuera de lo cronometrado, cada paso de N3 con
    `paso_desde_cero` y entre variantes, cada consulta de N1 y cada entrada
    de N2 entre la elegida y la alternativa. Devuelve (texto, errores)."""
    filas = []
    total_comparadas = 0
    errores = Vector()

    diferencias = Vector()
    _, casos = _casos_n1(rapido)
    comparadas = 0
    for i in range(len(casos)):
        comparadas += casos.obtener(i)[1].comparar(diferencias)
    filas.append(("N1", "consultas: Vector + EstadoPuerta / ArbolBusqueda",
                  str(comparadas), str(len(diferencias))))
    total_comparadas += comparadas
    _juntar(errores, diferencias)

    diferencias = Vector()
    cripta, resultados, comparadas = _correr_n2(rapido, True, diferencias)
    pequeno, grande = resultados.obtener(0), resultados.obtener(1)
    for e in range(len(pequeno.cambios)):
        if pequeno.cambios.obtener(e) != grande.cambios.obtener(e):
            diferencias.agregar(f"N2: la entrada {e} registra cambios "
                                f"distintos en los dos mapas")
    filas.append(("N2", "entradas: elegida / copia por acción",
                  str(comparadas), str(len(diferencias))))
    total_comparadas += comparadas
    _juntar(errores, diferencias)

    diferencias = Vector()
    corridas = _correr_n3(rapido, CARPETA_COPIAS, fabrica, diferencias)
    comparadas = 0
    for i in range(len(corridas)):
        comparadas += corridas.obtener(i)[2].comparados
    filas.append(("N3", "pasos: reutilizando / paso_desde_cero y entre "
                  "variantes", str(comparadas), str(len(diferencias))))
    total_comparadas += comparadas
    _juntar(errores, diferencias)

    texto = tabla(
        "N4 IGUALDAD CON LA ALTERNATIVA (FR-232, SC-203)",
        ("sección", "qué se compara", "comparadas", "diferencias"),
        filas,
        f"Total: {total_comparadas} comparaciones, {len(errores)} "
        f"diferencias.")

    texto += _lineas_error(errores)
    return texto, len(errores)


def _juntar(errores, diferencias):
    for i in range(len(diferencias)):
        errores.agregar(diferencias.obtener(i))
