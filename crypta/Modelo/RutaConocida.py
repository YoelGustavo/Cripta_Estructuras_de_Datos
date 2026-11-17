"""La ruta de «ir a» por el mapa conocido (capacidad 002, FR-217, FR-218).

Research D5, D6, D12; data-model «RutaConocida». No es estado del juego
(research D7): no se guarda, no se revierte y no va a los puntos de control.
"""

from crypta.Modelo.Perseguidor import MODOS, RECALCULAR, SELECTIVA
from crypta.Modelo.Puerta import ABIERTA
from crypta.estructuras.DistanciasLimitadas import DistanciasLimitadas
from crypta.estructuras.RutaPorCazador import RutaPorCazador


INFINITO = float("inf")


class RutaConocida:
    """Distancias de cada sala al destino por lo que el jugador conoce.

    Comparte la estructura con el cazador (`DistanciasLimitadas`, desde el
    destino y por las entradas) y separa las reglas: solo cuentan las salas
    exploradas y las salidas que el jugador recuerda abiertas (FR-217).
    Como el destino no cambia entre pasos, las distancias asentadas siguen
    valiendo y el paso siguiente cuesta O(grado) sin buscar (D5).

    Es el `observador` del `MapaConocido` (D6):

    - `puerta_recordada(estado)`: en modo SELECTIVA invalida si alguno de
      los extremos de la salida está asentado; en TOTAL, siempre.
    - `sala_explorada(sala)`: en SELECTIVA invalida si la sala o el otro
      extremo de alguna de sus salidas o entradas está asentado.

    Si ninguna sala tocada está asentada, la arista nunca se relajó y las
    distancias asentadas son las de un cálculo desde cero (demostración en
    research D6). `paso_desde_cero` es el verificador (SC-203, N4).
    """

    def __init__(self, mapa, conocimiento, modo=SELECTIVA):
        if modo not in MODOS:
            raise ValueError(f"Modo de reutilización desconocido: {modo!r}")

        self._mapa = mapa
        self._conocimiento = conocimiento
        self.modo = modo

        self._distancias = DistanciasLimitadas(
            mapa.cantidad_salas(), self.entradas_conocidas)
        self._vigente = False
        self._desde_cero = None

        # Contadores para el --bench y las pruebas.
        self.invalidaciones = 0
        self.pasos = 0

    @property
    def busquedas(self):
        """Búsquedas empezadas desde el destino."""
        return self._distancias.busquedas

    # -- el grafo conocido ---------------------------------------------------

    def _conocida(self, puerta, origen, destino):
        """Si la salida `origen` → `destino` es parte del mapa conocido: los
        dos extremos explorados y la salida recordada abierta."""
        return (destino is not None
                and puerta.estado.recordada == ABIERTA
                and self._conocimiento.esta_explorada(origen)
                and self._conocimiento.esta_explorada(destino))

    def entradas_conocidas(self, indice):
        """(índice de la sala origen, costo) de cada salida conocida que
        llega a la sala `indice`. O(entradas de la sala)."""
        sala = self._mapa.sala_por_indice(indice)
        entradas = sala.entradas

        for i in range(len(entradas)):
            puerta, origen = entradas.obtener(i)

            if self._conocida(puerta, origen, sala):
                yield origen.indice, puerta.costo

    def _salidas_conocidas(self, indice):
        """(índice de la sala destino, costo) de cada salida conocida de la
        sala `indice`. La usa el verificador hacia adelante."""
        sala = self._mapa.sala_por_indice(indice)
        puertas = sala.puertas()

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)
            destino = puerta.sala_destino_ref

            if self._conocida(puerta, sala, destino):
                yield destino.indice, puerta.costo

    # -- pasos ---------------------------------------------------------------

    def siguiente_paso(self, sala, destino):
        """La `Puerta` del próximo paso de `sala` hacia `destino` por la
        ruta conocida más barata, o None si no hay ruta (FR-217). Reutiliza
        la búsqueda si sigue vigente y el destino es el mismo (D6)."""
        self.pasos += 1
        return self._elegir(sala, destino)

    def hay_ruta(self, sala, destino):
        """Si hay ruta conocida, sin contar un paso. La usa `Viaje.validar`;
        la búsqueda que hace sirve para el primer paso."""
        return self._elegir(sala, destino) is not None

    def _elegir(self, sala, destino):
        if (self.modo == RECALCULAR or not self._vigente
                or self._distancias.origen != destino.indice):
            self._distancias.reiniciar(destino.indice)
            self._vigente = True

        if not self._distancias.extender_hasta(INFINITO,
                                               objetivo=sala.indice):
            return None

        return self._mejor_salida(sala, self._distancias.distancia(sala.indice))

    def _mejor_salida(self, sala, d):
        """Entre las salidas conocidas de `sala` hacia una v con
        costo + dist(v) == d, la de menor id de v; con dos salidas a la
        misma v, la primera en N, S, E, O (FR-217; la regla de
        `Perseguidor._decidir_con`). Toda candidata tiene dist(v) < d, así
        que ya está asentada."""
        elegida = None
        puertas = sala.puertas()

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)
            v = puerta.sala_destino_ref

            if not self._conocida(puerta, sala, v):
                continue

            dist_v = self._distancias.distancia(v.indice)

            if dist_v is None or puerta.costo + dist_v != d:
                continue

            if elegida is None or v.id < elegida.sala_destino_ref.id:
                elegida = puerta

        return elegida

    def paso_desde_cero(self, sala, destino):
        """El mismo paso con `RutaPorCazador` hacia adelante, siempre desde
        cero (SC-203, N4). No toca la búsqueda vigente ni los contadores."""
        if self._desde_cero is None:
            self._desde_cero = RutaPorCazador(self._mapa.cantidad_salas(),
                                              self._salidas_conocidas)

        resultado = self._desde_cero.buscar(sala.indice, destino.indice,
                                            INFINITO)

        if resultado is None or resultado[1] is None:
            return None

        # La vecina del primer paso; entre las salidas conocidas hacia ella,
        # la más barata, y con el mismo costo, la primera en N, S, E, O.
        vecina = self._mapa.sala_por_indice(resultado[1])
        elegida = None
        puertas = sala.puertas()

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)

            if (puerta.sala_destino_ref is vecina
                    and self._conocida(puerta, sala, vecina)
                    and (elegida is None or puerta.costo < elegida.costo)):
                elegida = puerta

        return elegida

    # -- avisos del MapaConocido (D6) ----------------------------------------

    def _asentada(self, sala):
        return sala is not None and self._distancias.esta_asentada(sala.indice)

    def puerta_recordada(self, estado):
        if not self._vigente:
            return

        if self.modo != SELECTIVA:
            self.invalidar()
            return

        for sala in estado.extremos or ():
            if self._asentada(sala):
                self.invalidar()
                return

    def sala_explorada(self, sala):
        if not self._vigente:
            return

        if self.modo != SELECTIVA or self._asentada(sala):
            self.invalidar()
            return

        puertas = sala.puertas()

        for i in range(len(puertas)):
            if self._asentada(puertas.obtener(i).sala_destino_ref):
                self.invalidar()
                return

        entradas = sala.entradas

        for i in range(len(entradas)):
            if self._asentada(entradas.obtener(i)[1]):
                self.invalidar()
                return

    def invalidar(self):
        """Lo calculado ya no sirve; el próximo paso busca de nuevo. La
        llaman los avisos del MapaConocido y el pergamino."""
        if self._vigente:
            self.invalidaciones += 1

        self._vigente = False
