from crypta.estructuras.DistanciasLimitadas import DistanciasLimitadas


ATACAR = "atacar"
ESPERAR = "esperar"
MOVER = "mover"


class Decision:
    """Lo que hace un cazador en su turno (data-model.md).

    - `accion`: ATACAR, ESPERAR o MOVER.
    - `puerta`: la salida que atraviesa si mueve; si no, None.
    - `costo`: el de P1 para atacar y esperar; `puerta.costo` para mover.
    """

    def __init__(self, accion, puerta, costo):
        self.accion = accion
        self.puerta = puerta
        self.costo = costo

    def __repr__(self):
        destino = None if self.puerta is None else self.puerta.sala_destino
        return f"Decision({self.accion}, hacia {destino}, costo {self.costo})"


class Perseguidor:
    """Las reglas del cazador (FR-013 a FR-018, FR-021; research D3).

    Hay uno por partida, con UNA búsqueda compartida por todos los
    cazadores: las distancias de cada sala hasta la sala del jugador, por
    las entradas abiertas (research D2). Cada cazador solo mira las salidas
    de su sala. La búsqueda se extiende lo justo para el cazador que decide
    y se reutiliza mientras no cambien la sala del jugador ni las puertas.

    Es observador de los `EstadoPuerta`: cuando una puerta se abre o se
    cierra, `puerta_cambio` invalida la búsqueda. Por ahora invalida
    siempre; la invalidación selectiva es de la fase 5.

    Nada de esto es estado del juego (research D6): no se guarda ni se
    revierte; si hace falta, se vuelve a calcular. No usa el azar (FR-021).
    """

    def __init__(self, mapa, costo_atacar, costo_esperar):
        """`costo_atacar` y `costo_esperar` son los de P1 §2.3; los pasa la
        Partida, que es dueña de esas constantes."""
        self._mapa = mapa
        self._costo_atacar = costo_atacar
        self._costo_esperar = costo_esperar

        self._distancias = DistanciasLimitadas(
            mapa.cantidad_salas(), self._entradas_abiertas)
        self._vigente = False

        # Contadores para el --bench y las pruebas.
        self.decisiones = 0
        self.invalidaciones = 0

    def observar_puertas(self):
        """Se registra como observador de cada salida del mapa."""
        salas = self._mapa.obtener_todas()

        for i in range(len(salas)):
            puertas = salas.obtener(i).puertas()

            for j in range(len(puertas)):
                puertas.obtener(j).estado.observador = self

    def _entradas_abiertas(self, indice):
        """(índice de la sala origen, costo) de cada salida abierta que
        llega a la sala `indice`."""
        entradas = self._mapa.sala_por_indice(indice).entradas

        for i in range(len(entradas)):
            puerta, origen = entradas.obtener(i)

            if not puerta.esta_cerrada():
                yield origen.indice, puerta.costo

    def puerta_cambio(self, estado):
        """Aviso de una puerta que se abrió o se cerró (FR-018, FR-019)."""
        self.invalidar()

    def invalidar(self):
        """Lo calculado ya no sirve; la próxima decisión empieza de nuevo.
        La llaman los avisos de puertas, el pergamino y la carga."""
        if self._vigente:
            self.invalidaciones += 1

        self._vigente = False

    def decidir(self, cazador, sala_jugador):
        """La Decision del `cazador` (un Enemigo activo con `rango`) con el
        jugador en `sala_jugador` (research D3)."""
        self.decisiones += 1
        u = self._mapa.obtener_sala(cazador.sala_actual)

        # 1. Comparte sala: ataca (FR-013).
        if u is sala_jugador:
            return Decision(ATACAR, None, self._costo_atacar)

        # 2. Extiende la búsqueda mientras el mínimo sea <= rango y u no
        #    esté asentada (FR-014, FR-015).
        if not self._vigente or self._distancias.origen != sala_jugador.indice:
            self._distancias.reiniciar(sala_jugador.indice)
            self._vigente = True

        rango = cazador.rango
        self._distancias.extender_hasta(rango, objetivo=u.indice)
        d = self._distancias.distancia(u.indice)

        # 3. Sin ruta, o d > rango (otro cazador pudo haber extendido la
        #    búsqueda más allá de este rango): espera (FR-015).
        if d is None or d > rango:
            return Decision(ESPERAR, None, self._costo_esperar)

        # 4. Entre las salidas abiertas de u hacia v con
        #    costo(u, v) + dist(v) = d, la v de menor id; con dos salidas a
        #    la misma v, la primera en orden N, S, E, O (FR-016, FR-017).
        #    Toda candidata tiene dist(v) < d, así que ya está asentada.
        elegida = None
        puertas = u.puertas(solo_abiertas=True)

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)
            v = puerta.sala_destino_ref

            if v is None:
                continue

            dist_v = self._distancias.distancia(v.indice)

            if dist_v is None or puerta.costo + dist_v != d:
                continue

            if elegida is None or v.id < elegida.sala_destino_ref.id:
                elegida = puerta

        return Decision(MOVER, elegida, elegida.costo)
