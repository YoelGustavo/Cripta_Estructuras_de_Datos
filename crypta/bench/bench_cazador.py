"""--bench del cazador (capacidad 001): secciones B1 a B6, B8 y B9 de
specs/001-terreno-cazador/contracts/bench.md. B7 está en bench_ciclo.py.

- Generador de criptas sintéticas con costos (T078, FR-028, FR-030): una
  cuadrícula en la que el costo y la puerta de cada salida salen SOLO de
  (semilla, coordenadas). Así la región alrededor del jugador es idéntica en
  criptas de distinto tamaño, y B3 compara lo mismo.
- B1 a B6 miden las decisiones directamente sobre el Perseguidor y
  RutaPorCazador (sin Partida): el jugador sigue un recorrido fijo derivado
  de la semilla y cada cazador decide una vez por acción del jugador.
- B6 repite los recorridos de B4 y B5 comparando cada decisión con un
  cálculo desde cero, fuera de lo que se cronometra (FR-033).

No instancia la vista ni usa la red (FR-034). Los dict de este archivo son
el JSON del esqueleto, igual que el que entrega el servicio (principio I).
"""

import gc
import hashlib
import json
import random
import time

from crypta.bench.medicion import formato_tiempo, tabla
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.DistanciasLimitadas import DistanciasLimitadas
from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.estructuras.RutaPorCazador import RutaPorCazador
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Perseguidor import (
    ATACAR, ESPERAR, MOVER, RECALCULAR, SELECTIVA, TOTAL, Decision,
    Perseguidor,
)


SEMILLA = 2026

# (ancho, alto) de cada tamaño. El jugador está en las mismas coordenadas
# en todas, lejos de los bordes, así que la región que lo rodea es la misma.
TAMANOS = {2000: (50, 40), 20000: (200, 100)}
JUGADOR = (20, 25)                 # (fila, columna)

COSTO_MINIMO = 1
COSTO_MAXIMO = 500
PROB_SIN_SALIDA = 0.1              # salidas quitadas, para que haya rodeos
PROB_PUERTA = 0.15                 # salidas con puerta (las que cambian)
PROB_CERRADA = 0.3                 # puertas que empiezan cerradas

SALAS_RANGO_PEQUENO = 100          # «rango pequeño»: ~100 salas dentro
RANGO_GRANDE = 10 ** 9             # «rango grande»: toda la cripta
COSTO_ACCION = 100                 # atacar y esperar (P1 §2.3)

LIMITE_COCIENTE_TAMANO = 2         # B3, SC-005: < 2
LIMITE_COCIENTE_CAZADORES = 2      # B8, SC-008: <= 2


# ======================================================================
# Generador (T078)
# ======================================================================

def _azar_de(semilla, fila, columna, direccion):
    """Un random.Random propio de una salida: depende solo de la semilla,
    las coordenadas y la dirección (0 = este, 1 = sur)."""
    return random.Random(
        ((semilla * 1_000_003 + fila) * 1_000_003 + columna) * 2 + direccion)


def _salida(semilla, fila, columna, direccion):
    """Datos de la salida que va al este (0) o al sur (1) desde
    (fila, columna), o None si se quitó."""
    azar = _azar_de(semilla, fila, columna, direccion)

    if azar.random() < PROB_SIN_SALIDA:
        return None

    costo = azar.randint(COSTO_MINIMO, COSTO_MAXIMO)
    puerta = azar.random() < PROB_PUERTA
    cerrada = puerta and azar.random() < PROB_CERRADA
    return costo, puerta, cerrada


class CriptaSintetica:
    """Cuadrícula de `salas` salas (uno de los TAMANOS) con salidas a las 4
    vecinas, algunas quitadas, costos en [1, 500] y una fracción con
    puerta. Todo determinista por semilla (FR-028)."""

    def __init__(self, salas=2000, semilla=SEMILLA):
        if salas not in TAMANOS:
            raise ValueError(f"Tamaños disponibles: {tuple(TAMANOS)}")

        self.semilla = semilla
        self.ancho, self.alto = TAMANOS[salas]
        self.esqueleto = self._armar_esqueleto()

        self.mapa = Mapa()
        self.mapa.cargar_desde_json(self.esqueleto)
        self.sala_jugador = self.mapa.obtener_sala(self.id_de(*JUGADOR))

        # Las salidas con puerta (un lado de cada una) y su estado inicial,
        # para cambiarlas en B4 y B5 y restaurarlas entre variantes.
        self.puertas = Vector()
        self._cerradas_al_inicio = Vector()
        self._juntar_puertas()

        self._orden = None

    def id_de(self, fila, columna):
        return fila * self.ancho + columna + 1

    def coordenadas(self, sala):
        return divmod(sala.id - 1, self.ancho)

    def _armar_esqueleto(self):
        esqueleto = []

        for fila in range(self.alto):
            for columna in range(self.ancho):
                salidas = {}

                if columna + 1 < self.ancho:
                    self._poner(salidas, "E", fila, columna, 0,
                                self.id_de(fila, columna + 1))
                if fila + 1 < self.alto:
                    self._poner(salidas, "S", fila, columna, 1,
                                self.id_de(fila + 1, columna))
                if columna > 0 and _salida(self.semilla, fila, columna - 1,
                                           0) is not None:
                    salidas["O"] = {"sala": self.id_de(fila, columna - 1)}
                if fila > 0 and _salida(self.semilla, fila - 1, columna,
                                        1) is not None:
                    salidas["N"] = {"sala": self.id_de(fila - 1, columna)}

                esqueleto.append({"id": self.id_de(fila, columna),
                                  "nombre": f"Sala {fila},{columna}",
                                  "salidas": salidas})

        return esqueleto

    def _poner(self, salidas, direccion, fila, columna, sentido, destino):
        datos = _salida(self.semilla, fila, columna, sentido)

        if datos is None:
            return

        costo, puerta, cerrada = datos
        salida = {"sala": destino, "costo": costo}

        if puerta:
            salida["puerta"] = True        # solo informativo para la huella
            salida["cerrada"] = cerrada

        salidas[direccion] = salida

    def _juntar_puertas(self):
        for datos in self.esqueleto:
            sala = self.mapa.obtener_sala(datos["id"])

            for direccion in ("E", "S"):
                salida = datos["salidas"].get(direccion)

                if salida is not None and salida.get("puerta"):
                    puerta = sala.obtener_puerta(direccion)
                    self.puertas.agregar(puerta)
                    self._cerradas_al_inicio.agregar(puerta.esta_cerrada())

    def restaurar_puertas(self):
        """Deja cada puerta como al generar la cripta, sin observadores."""
        for i in range(len(self.puertas)):
            estado = self.puertas.obtener(i).estado
            estado.observador = None
            estado.cerrada = self._cerradas_al_inicio.obtener(i)

    def contenidos(self, cazadores=None, tipo="ent_cazador_bench"):
        """Contenido de cada sala: vacío, salvo un cazador en cada sala de
        `cazadores` (repetidas, varios)."""
        por_sala = Vector(len(self.esqueleto))
        for _ in range(len(self.esqueleto)):
            por_sala.agregar(None)

        for i in range(len(cazadores or ())):
            sala = cazadores.obtener(i)
            lista = por_sala.obtener(sala.indice)
            if lista is None:
                lista = []
                por_sala.asignar(sala.indice, lista)
            lista.append({"instancia": f"c-{i:03d}", "tipo": tipo})

        return [{"sala": datos["id"], "objetos": [], "trampas": [],
                 "enemigos": por_sala.obtener(i) or []}
                for i, datos in enumerate(self.esqueleto)]

    # -- distancias al jugador -------------------------------------------

    def salas_en_orden(self, limite):
        """Vector de (sala, distancia al jugador) de las salas con
        distancia <= limite, en el orden en que DistanciasLimitadas las
        asienta (de la más cercana a la más lejana). Sin sorted()."""
        if self._orden is None or self._orden[0] < limite:
            orden = Vector()
            busqueda = DistanciasLimitadas(self.mapa.cantidad_salas(),
                                           entradas_abiertas(self.mapa))
            busqueda.al_asentar = lambda nodo, d: orden.agregar(
                (self.mapa.sala_por_indice(nodo), d))
            busqueda.reiniciar(self.sala_jugador.indice)
            busqueda.extender_hasta(limite)
            self._orden = (limite, orden)

        orden = self._orden[1]
        resultado = Vector()
        for i in range(len(orden)):
            if orden.obtener(i)[1] <= limite:
                resultado.agregar(orden.obtener(i))
        return resultado

    def distancia_al_jugador(self, sala):
        busqueda = DistanciasLimitadas(self.mapa.cantidad_salas(),
                                       entradas_abiertas(self.mapa))
        busqueda.reiniciar(self.sala_jugador.indice)
        busqueda.extender_hasta(RANGO_GRANDE, objetivo=sala.indice)
        return busqueda.distancia(sala.indice)

    def rango_pequeno(self):
        """La distancia de la sala número 100 en orden de distancia: deja
        unas 100 salas dentro (FR-030)."""
        return self._distancia_de_la_sala(SALAS_RANGO_PEQUENO)

    def rango_mediano(self):
        """La distancia de la sala que está a mitad de camino: deja la
        mitad de la cripta dentro (B7 y B8)."""
        return self._distancia_de_la_sala(len(self.esqueleto) // 2)

    def _distancia_de_la_sala(self, numero):
        orden = self.salas_en_orden(RANGO_GRANDE)
        return orden.obtener(min(numero, len(orden) - 1))[1]

    def ubicar_cazadores(self, cantidad, rango):
        """Salas para `cantidad` cazadores, a distancias repartidas dentro
        de `rango` (FR-029): se toman a intervalos regulares del orden de
        distancia, sin la sala del jugador (la primera)."""
        orden = self.salas_en_orden(rango)
        disponibles = len(orden) - 1
        salas = Vector(max(1, cantidad))

        for i in range(cantidad):
            salas.agregar(orden.obtener(1 + (i * disponibles) // cantidad)[0])

        return salas

    def recorrido(self, pasos, semilla=None):
        """Direcciones de un recorrido fijo del jugador (B7, B8)."""
        return recorrido_desde(self.sala_jugador, pasos,
                               self.semilla if semilla is None else semilla)


def recorrido_desde(sala, pasos, semilla):
    """Direcciones de un recorrido fijo por salidas abiertas, derivado de
    la semilla. Sin ataques ni esperas: el jugador siempre se mueve."""
    azar = random.Random(semilla)
    direcciones = []

    for _ in range(pasos):
        abiertas = sala.puertas(solo_abiertas=True)

        if len(abiertas) == 0:
            break

        puerta = abiertas.obtener(azar.randrange(len(abiertas)))
        direcciones.append(sala.direccion_de(puerta))
        sala = puerta.sala_destino_ref

    return direcciones


def entradas_abiertas(mapa):
    """La función de entradas abiertas que usa el Perseguidor."""
    def entradas(indice):
        lista = mapa.sala_por_indice(indice).entradas

        for i in range(len(lista)):
            puerta, origen = lista.obtener(i)

            if not puerta.esta_cerrada():
                yield origen.indice, puerta.costo

    return entradas


def salidas_abiertas(mapa):
    def salidas(indice):
        puertas = mapa.sala_por_indice(indice).puertas(solo_abiertas=True)

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)

            if puerta.sala_destino_ref is not None:
                yield puerta.sala_destino_ref.indice, puerta.costo

    return salidas


def huella(cripta, cazadores):
    """Resumen de la cripta generada: salas, salidas, costos, puertas y
    ubicación de los cazadores, serializados en orden (SC-006)."""
    datos = {
        "esqueleto": cripta.esqueleto,
        "jugador": cripta.sala_jugador.id,
        "cazadores": [cazadores.obtener(i).id for i in range(len(cazadores))],
    }
    texto = json.dumps(datos, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ======================================================================
# Simulación de decisiones (B1 a B6)
# ======================================================================

class _Cazador:
    """Lo que el Perseguidor mira de un cazador."""

    def __init__(self, numero, sala, rango):
        self.id_instancia = f"c-{numero:03d}"
        self.sala_actual = sala.id
        self.rango = rango


class PorCazador:
    """La alternativa medida (FR-031): una RutaPorCazador por decisión,
    con la misma interfaz que el Perseguidor."""

    def __init__(self, mapa):
        self._mapa = mapa
        self._ruta = RutaPorCazador(mapa.cantidad_salas(),
                                    salidas_abiertas(mapa))

    @property
    def busquedas(self):
        return self._ruta.busquedas

    @property
    def asentados(self):
        return self._ruta.asentados

    def decidir(self, cazador, sala_jugador):
        u = self._mapa.obtener_sala(cazador.sala_actual)

        if u is sala_jugador:
            return Decision(ATACAR, None, COSTO_ACCION)

        resultado = self._ruta.buscar(u.indice, sala_jugador.indice,
                                      cazador.rango)

        if resultado is None:
            return Decision(ESPERAR, None, COSTO_ACCION)

        v = self._mapa.sala_por_indice(resultado[1])
        puertas = u.puertas(solo_abiertas=True)
        elegida = None

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)
            if (puerta.sala_destino_ref is v
                    and (elegida is None or puerta.costo < elegida.costo)):
                elegida = puerta

        return Decision(MOVER, elegida, elegida.costo)


class Resultado:
    def __init__(self):
        self.tiempo = 0.0
        self.decisiones = 0
        self.ciclos = 0
        self.busquedas = 0
        self.asentados = 0
        self.comparadas = 0
        self.diferencias = []

    def por_decision(self):
        return self.tiempo / max(1, self.decisiones)

    def por_ciclo(self):
        return self.tiempo / max(1, self.ciclos)


def _resumen(decision):
    destino = (None if decision.puerta is None
               else decision.puerta.sala_destino_ref.id)
    return decision.accion, destino, decision.costo


def simular(cripta, salas_cazadores, rango, pasos, variante,
            cambios=0.0, verificar=False, fabrica=None):
    """El jugador da `pasos` pasos por el recorrido fijo; después de cada
    paso cada cazador decide una vez (y se mueve si decide moverse).

    - `variante`: un modo del Perseguidor (RECALCULAR, TOTAL, SELECTIVA) o
      "por cazador".
    - `cambios`: cambios de puerta antes de cada decisión; 0.02 es uno cada
      50 acciones, 1 es uno por acción.
    - `verificar`: compara cada decisión con decidir_desde_cero (FR-033).
    Solo se cronometran las decisiones (con el aviso de puertas que
    disparan los cambios); la verificación no cuenta."""
    cripta.restaurar_puertas()
    mapa = cripta.mapa

    if variante == "por cazador":
        decisor = PorCazador(mapa)
        verificador = Perseguidor(mapa, COSTO_ACCION, COSTO_ACCION)
    else:
        decisor = (fabrica or Perseguidor)(mapa, COSTO_ACCION, COSTO_ACCION,
                                           modo=variante)
        decisor.observar_puertas()
        verificador = decisor

    cazadores = [_Cazador(i, salas_cazadores.obtener(i), rango)
                 for i in range(len(salas_cazadores))]
    azar = random.Random(cripta.semilla + 1)
    resultado = Resultado()
    jugador = cripta.sala_jugador
    pendiente = 0.0

    activo = gc.isenabled()
    gc.disable()

    try:
        for _ in range(pasos):
            abiertas = jugador.puertas(solo_abiertas=True)
            if len(abiertas) > 0:
                jugador = abiertas.obtener(
                    azar.randrange(len(abiertas))).sala_destino_ref
            resultado.ciclos += 1

            for cazador in cazadores:
                inicio = time.perf_counter()

                pendiente += cambios
                while pendiente >= 1:
                    pendiente -= 1
                    puerta = cripta.puertas.obtener(
                        azar.randrange(len(cripta.puertas)))
                    puerta.cerrada = not puerta.cerrada

                decision = decisor.decidir(cazador, jugador)
                resultado.tiempo += time.perf_counter() - inicio
                resultado.decisiones += 1

                if verificar:
                    esperada = verificador.decidir_desde_cero(cazador,
                                                              jugador)
                    resultado.comparadas += 1
                    if _resumen(decision) != _resumen(esperada):
                        resultado.diferencias.append(
                            f"{variante}, ciclo {resultado.ciclos}, "
                            f"{cazador.id_instancia} en la sala "
                            f"{cazador.sala_actual}: decidió "
                            f"{_resumen(decision)} y desde cero "
                            f"{_resumen(esperada)}")

                if decision.accion == MOVER:
                    cazador.sala_actual = decision.puerta.sala_destino_ref.id
    finally:
        if activo:
            gc.enable()
        cripta.restaurar_puertas()

    resultado.busquedas = decisor.busquedas
    resultado.asentados = decisor.asentados
    return resultado


_CRIPTAS = Vector()       # (salas, CriptaSintetica) ya generadas


def _cripta(salas=2000):
    """Las criptas se generan una vez por tamaño y se reutilizan entre
    secciones (las puertas se restauran en cada simulación)."""
    for i in range(len(_CRIPTAS)):
        cantidad, cripta = _CRIPTAS.obtener(i)
        if cantidad == salas:
            return cripta

    cripta = CriptaSintetica(salas)
    _CRIPTAS.agregar((salas, cripta))
    return cripta


# ======================================================================
# B1 y B2 (T079)
# ======================================================================

def ejecutar_uno_y_muchos(rapido=False):
    """B1 (FR-029): 1 frente a 50 cazadores, todos dentro de su rango."""
    cripta = _cripta()
    rango = cripta.rango_mediano()
    pasos = 3 if rapido else 20
    filas = []

    for cantidad in (1, 50):
        r = simular(cripta, cripta.ubicar_cazadores(cantidad, rango), rango,
                    pasos, SELECTIVA)
        filas.append((str(cantidad), formato_tiempo(r.por_decision()),
                      formato_tiempo(r.por_ciclo()),
                      f"{r.asentados / max(1, r.ciclos):.0f}"))

    return tabla(
        f"B1 UN CAZADOR FRENTE A MUCHOS (FR-029). 2000 salas, rango {rango} "
        f"(media cripta), {pasos} acciones del jugador",
        ("cazadores", "por decisión", "por ciclo", "salas asentadas por ciclo"),
        filas,
        "Ciclo: una decisión de cada cazador después de cada paso del "
        "jugador. La búsqueda es una sola para todos.")


def ejecutar_rangos(rapido=False):
    """B2 (FR-030): rango pequeño (~100 salas) frente a grande."""
    cripta = _cripta()
    pasos = 3 if rapido else 20
    filas = []

    for nombre, rango in (("pequeño", cripta.rango_pequeno()),
                          ("grande", RANGO_GRANDE)):
        r = simular(cripta, cripta.ubicar_cazadores(10, rango), rango,
                    pasos, SELECTIVA)
        filas.append((nombre, str(rango if rango < RANGO_GRANDE else "todo"),
                      formato_tiempo(r.por_decision()),
                      f"{r.asentados / max(1, r.decisiones):.0f}"))

    return tabla(
        f"B2 RANGO PEQUEÑO FRENTE A GRANDE (FR-030). 2000 salas, 10 "
        f"cazadores, {pasos} acciones del jugador",
        ("rango", "valor", "por decisión", "salas asentadas por decisión"),
        filas)


# ======================================================================
# B3 (T080)
# ======================================================================

def ejecutar_tamano(rapido=False):
    """B3 (FR-030, FR-036, SC-005): misma región, 2000 frente a 20000
    salas. El jugador no se mueve; cada decisión empieza de cero."""
    repeticiones = 50 if rapido else 500
    rango = _cripta(2000).rango_pequeno()
    filas = []
    tiempos = []

    for salas in (2000, 20000):
        cripta = _cripta(salas)
        cripta.restaurar_puertas()
        perseguidor = Perseguidor(cripta.mapa, COSTO_ACCION, COSTO_ACCION)
        lejana = cripta.salas_en_orden(rango)
        cazador = _Cazador(0, lejana.obtener(len(lejana) - 1)[0], rango)

        perseguidor.decidir(cazador, cripta.sala_jugador)    # calentamiento
        asentados_antes = perseguidor.asentados
        activo = gc.isenabled()
        gc.disable()
        try:
            inicio = time.perf_counter()
            for _ in range(repeticiones):
                perseguidor.invalidar()
                perseguidor.decidir(cazador, cripta.sala_jugador)
            tiempo = (time.perf_counter() - inicio) / repeticiones
        finally:
            if activo:
                gc.enable()

        tiempos.append(tiempo)
        filas.append((str(salas), formato_tiempo(tiempo),
                      f"{(perseguidor.asentados - asentados_antes) / repeticiones:.0f}"))

    cociente = tiempos[1] / tiempos[0]
    cumple = cociente < LIMITE_COCIENTE_TAMANO

    return tabla(
        f"B3 TAMAÑO DE LA CRIPTA CON LA MISMA REGIÓN (FR-036, SC-005). Rango "
        f"{rango} (~{SALAS_RANGO_PEQUENO} salas), {repeticiones} decisiones "
        f"desde cero",
        ("salas", "por decisión", "salas asentadas"),
        filas,
        f"cociente 20000 / 2000: {cociente:.2f} (límite < "
        f"{LIMITE_COCIENTE_TAMANO}). ¿cumple? {'sí' if cumple else 'NO'}")


# ======================================================================
# B4, B5 y B6 (T081, T082)
# ======================================================================

CAMBIOS_ESTABLES = 1 / 50          # ~1 cambio de puerta cada 50 acciones
CAMBIOS_INESTABLES = 1.0           # >= 1 cambio por acción


def _rango_b4_b6(cripta, rapido):
    """Rango de B4 a B6: media cripta; en modo rápido (solo para las
    pruebas) el pequeño, para que la verificación no tarde."""
    return cripta.rango_pequeno() if rapido else cripta.rango_mediano()


def _casos_compartido(rapido):
    pasos = 2 if rapido else 15
    for cantidad in (1, 10, 50):
        for nombre, cambios in (("estables", 0.0),
                                ("inestables", CAMBIOS_INESTABLES)):
            yield cantidad, nombre, cambios, pasos


def ejecutar_compartido(rapido=False):
    """B4 (FR-031): búsqueda compartida (Perseguidor) frente a una
    búsqueda por cazador (RutaPorCazador)."""
    cripta = _cripta()
    rango = _rango_b4_b6(cripta, rapido)
    filas = []

    for cantidad, nombre, cambios, pasos in _casos_compartido(rapido):
        salas = cripta.ubicar_cazadores(cantidad, rango)
        compartida = simular(cripta, salas, rango, pasos, SELECTIVA, cambios)
        por_cazador = simular(cripta, salas, rango, pasos, "por cazador",
                              cambios)
        gana = ("compartida" if compartida.tiempo <= por_cazador.tiempo
                else "por cazador")
        filas.append((str(cantidad), nombre,
                      formato_tiempo(compartida.por_ciclo()),
                      formato_tiempo(por_cazador.por_ciclo()),
                      str(compartida.busquedas), str(por_cazador.busquedas),
                      gana))

    return tabla(
        f"B4 BÚSQUEDA COMPARTIDA FRENTE A UNA POR CAZADOR (FR-031). 2000 "
        f"salas, rango {rango}",
        ("cazadores", "puertas", "compartida: ciclo", "por cazador: ciclo",
         "búsquedas compartida", "búsquedas por cazador", "gana"),
        filas,
        "Puertas estables: no cambian. Inestables: una cambia antes de cada "
        "decisión.")


def _casos_reutilizar(rapido):
    pasos = 2 if rapido else 15
    for nombre, cambios in (("casi estables", CAMBIOS_ESTABLES),
                            ("inestables", CAMBIOS_INESTABLES)):
        for modo in (RECALCULAR, TOTAL, SELECTIVA):
            yield nombre, cambios, modo, pasos


def ejecutar_reutilizar(rapido=False):
    """B5 (FR-032): recalcular siempre, invalidación total y selectiva."""
    cripta = _cripta()
    rango = _rango_b4_b6(cripta, rapido)
    salas = cripta.ubicar_cazadores(50, rango)
    filas = []

    for nombre, cambios, modo, pasos in _casos_reutilizar(rapido):
        r = simular(cripta, salas, rango, pasos, modo, cambios)
        filas.append((nombre, modo, formato_tiempo(r.por_ciclo()),
                      str(r.busquedas), str(r.asentados)))

    return tabla(
        f"B5 REUTILIZAR FRENTE A RECALCULAR (FR-032). 2000 salas, 50 "
        f"cazadores, rango {rango}",
        ("puertas", "variante", "por ciclo", "búsquedas", "salas asentadas"),
        filas,
        "Casi estables: ~1 cambio de puerta cada 50 acciones. Inestables: "
        "uno antes de cada decisión.")


def ejecutar_equivalencia(rapido=False, fabrica=None):
    """B6 (FR-033): repite los recorridos de B4 y B5 comparando cada
    decisión con decidir_desde_cero. Devuelve (texto, errores)."""
    fabrica = fabrica or Perseguidor
    cripta = _cripta()
    rango = _rango_b4_b6(cripta, rapido)
    filas = []
    errores = []

    casos = [("B4", cantidad, nombre, cambios, pasos, variante)
             for cantidad, nombre, cambios, pasos in _casos_compartido(rapido)
             for variante in (SELECTIVA, "por cazador")]
    casos += [("B5", 50, nombre, cambios, pasos, modo)
              for nombre, cambios, modo, pasos in _casos_reutilizar(rapido)]

    for seccion, cantidad, nombre, cambios, pasos, variante in casos:
        r = simular(cripta, cripta.ubicar_cazadores(cantidad, rango), rango,
                    pasos, variante, cambios, verificar=True,
                    fabrica=fabrica)
        filas.append((seccion, str(cantidad), nombre, variante,
                      str(r.comparadas), str(len(r.diferencias))))
        errores.extend(r.diferencias)

    texto = tabla(
        "B6 EQUIVALENCIA (FR-033): cada decisión de B4 y B5 contra un "
        "cálculo desde cero",
        ("sección", "cazadores", "puertas", "variante", "comparadas",
         "diferencias"),
        filas,
        f"Total: {sum(int(f[4]) for f in filas)} decisiones comparadas, "
        f"{len(errores)} diferencias.")

    for error in errores[:20]:
        texto += f"\nERROR: {error}"
    if len(errores) > 20:
        texto += f"\nERROR: ... y {len(errores) - 20} diferencias más"

    return texto, len(errores)


# ======================================================================
# B8 y B9 (T084)
# ======================================================================

def ejecutar_escala(rapido=False):
    """B8 (FR-037, SC-008): ciclo del juego con 10, 25, 50 y 100
    cazadores; tiempo por cazador y cociente 100 / 10."""
    from crypta.bench.bench_ciclo import medir_ciclo_cazadores

    acciones = 15 if rapido else 60
    calentamiento = 5 if rapido else 20
    filas = []
    por_cazador = Vector()

    for cantidad in (10, 25, 50, 100):
        medicion = medir_ciclo_cazadores(cantidad, acciones, calentamiento,
                                         vueltas=1 if rapido else 3)
        media = medicion.media(medicion.ciclo)
        por_cazador.agregar(media / cantidad)
        filas.append((str(cantidad), formato_tiempo(media),
                      formato_tiempo(media / cantidad)))

    cociente = por_cazador.obtener(3) / por_cazador.obtener(0)  # 100 / 10
    cumple = cociente <= LIMITE_COCIENTE_CAZADORES

    return tabla(
        f"B8 ESCALA EN CANTIDAD DE CAZADORES (FR-037, SC-008). 2000 salas, "
        f"{acciones} acciones medidas",
        ("cazadores", "ciclo: media", "por cazador"),
        filas,
        f"cociente por cazador 100 / 10: {cociente:.2f} (límite <= "
        f"{LIMITE_COCIENTE_CAZADORES}). ¿cumple? {'sí' if cumple else 'NO'}")


class DistanciasEnArbol:
    """La misma búsqueda que DistanciasLimitadas, guardando las distancias
    en un ArbolBusqueda nuevo por cálculo en lugar de vectores con marca
    (la alternativa de research D5, solo para medir)."""

    def __init__(self, entradas):
        self._entradas = entradas
        self._dist = ArbolBusqueda()
        self._asentadas = ArbolBusqueda()
        self._frontera = MonticuloMin()

    def reiniciar(self, origen):
        self._dist = ArbolBusqueda()
        self._asentadas = ArbolBusqueda()
        self._frontera = MonticuloMin()
        self._dist.insertar(origen, 0)
        self._frontera.insertar((0, origen))

    def extender_hasta(self, limite):
        while not self._frontera.esta_vacia():
            distancia, nodo = self._frontera.ver_min()
            if distancia > limite:
                return
            self._frontera.extraer_min()

            if self._asentadas.contiene(nodo):
                continue
            self._asentadas.insertar(nodo, True)

            for origen, costo in self._entradas(nodo):
                nueva = distancia + costo
                actual = self._dist.obtener(origen)
                if actual is None or nueva < actual:
                    self._dist.insertar(origen, nueva)
                    self._frontera.insertar((nueva, origen))

    def distancia(self, nodo):
        if not self._asentadas.contiene(nodo):
            return None
        return self._dist.obtener(nodo)


def ejecutar_distancias(rapido=False):
    """B9 (research D5): la misma búsqueda con vectores y marca frente a
    ArbolBusqueda."""
    cripta = _cripta()
    cripta.restaurar_puertas()
    repeticiones = 3 if rapido else 20
    origen = cripta.sala_jugador.indice
    filas = []

    for nombre, rango in (("pequeño", cripta.rango_pequeno()),
                          ("media cripta", cripta.rango_mediano())):
        con_vectores = DistanciasLimitadas(cripta.mapa.cantidad_salas(),
                                           entradas_abiertas(cripta.mapa))
        con_arbol = DistanciasEnArbol(entradas_abiertas(cripta.mapa))
        tiempos = []

        for busqueda in (con_vectores, con_arbol):
            inicio = time.perf_counter()
            for _ in range(repeticiones):
                busqueda.reiniciar(origen)
                busqueda.extender_hasta(rango)
            tiempos.append((time.perf_counter() - inicio) / repeticiones)

        filas.append((nombre, formato_tiempo(tiempos[0]),
                      formato_tiempo(tiempos[1]),
                      f"{tiempos[1] / tiempos[0]:.1f}x"))

    return tabla(
        "B9 DÓNDE GUARDAR LAS DISTANCIAS (research D5): la misma búsqueda, "
        "2000 salas",
        ("rango", "vectores con marca", "ArbolBusqueda", "árbol / vectores"),
        filas,
        "El árbol se crea de nuevo en cada búsqueda y no se autobalancea.")
