from crypta.estructuras.DistanciasLimitadas import DistanciasLimitadas


ATACAR = "atacar"
ESPERAR = "esperar"
MOVER = "mover"

# Modos de reutilización de la búsqueda (FR-032; research D4). Los tres
# deciden lo mismo (FR-019); cambia cuánto se recalcula.
RECALCULAR = "recalcular siempre"      # cada decisión empieza de cero
TOTAL = "invalidación total"           # cualquier cambio de puerta invalida
SELECTIVA = "selectiva"                # solo si toca la región asentada

MODOS = (RECALCULAR, TOTAL, SELECTIVA)


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
    """Las reglas del cazador (FR-013 a FR-019, FR-021; research D3, D4).

    Hay uno por partida, con UNA búsqueda compartida por todos los
    cazadores: las distancias de cada sala hasta la sala del jugador, por
    las entradas abiertas (research D2). Cada cazador solo mira las salidas
    de su sala. La búsqueda se extiende lo justo para el cazador que decide
    y se reutiliza mientras siga siendo la que daría un cálculo desde cero:

    - la sala del jugador se compara en cada decisión (moverse, el
      pergamino y la carga cambian el origen);
    - las puertas avisan con `puerta_cambio` cuando se abren o se cierran.
      En modo SELECTIVA solo invalida si alguno de los extremos de la
      salida está asentado: si ninguno lo está, la salida nunca se relajó
      y las distancias asentadas no pueden cambiar (demostración en
      research D4). En modo TOTAL invalida siempre; en RECALCULAR no hace
      falta, porque cada decisión empieza de cero.

    `decidir_desde_cero` usa su propia búsqueda, siempre reiniciada: es el
    verificador de las pruebas y del --bench (FR-033).

    Nada de esto es estado del juego (research D6): no se guarda ni se
    revierte; si hace falta, se vuelve a calcular. No usa el azar (FR-021).
    """

    def __init__(self, mapa, costo_atacar, costo_esperar, modo=SELECTIVA):
        """`costo_atacar` y `costo_esperar` son los de P1 §2.3; los pasa la
        Partida, que es dueña de esas constantes."""
        if modo not in MODOS:
            raise ValueError(f"Modo de reutilización desconocido: {modo!r}")

        self._mapa = mapa
        self._costo_atacar = costo_atacar
        self._costo_esperar = costo_esperar
        self.modo = modo

        self._distancias = DistanciasLimitadas(
            mapa.cantidad_salas(), self._entradas_abiertas)
        self._vigente = False

        # Para el verificador: se crea la primera vez que se usa.
        self._desde_cero = None

        # Contadores para el --bench y las pruebas.
        self.decisiones = 0
        self.invalidaciones = 0

    @property
    def busquedas(self):
        """Búsquedas empezadas por la búsqueda compartida."""
        return self._distancias.busquedas

    @property
    def asentados(self):
        """Salas asentadas por la búsqueda compartida, en total."""
        return self._distancias.asentados

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
        """Aviso de una puerta que se abrió o se cerró (FR-018, FR-019).
        O(1)."""
        if not self._vigente:
            return

        if self.modo == SELECTIVA:
            for sala in estado.extremos or ():
                if (sala is not None
                        and self._distancias.esta_asentada(sala.indice)):
                    self.invalidar()
                    return

            return          # ningún extremo asentado: la búsqueda sirve

        self.invalidar()

    def invalidar(self):
        """Lo calculado ya no sirve; la próxima decisión empieza de nuevo.
        La llaman los avisos de puertas, el pergamino y la carga."""
        if self._vigente:
            self.invalidaciones += 1

        self._vigente = False

    def decidir(self, cazador, sala_jugador):
        """La Decision del `cazador` (un Enemigo activo con `rango`) con el
        jugador en `sala_jugador`, reutilizando la búsqueda compartida
        (research D3)."""
        self.decisiones += 1

        if (self.modo == RECALCULAR or not self._vigente
                or self._distancias.origen != sala_jugador.indice):
            self._distancias.reiniciar(sala_jugador.indice)
            self._vigente = True

        return self._decidir_con(self._distancias, cazador, sala_jugador)

    def decidir_desde_cero(self, cazador, sala_jugador):
        """La misma decisión con una búsqueda propia, siempre reiniciada
        (FR-033). No toca la búsqueda compartida ni los contadores."""
        if self._desde_cero is None:
            self._desde_cero = DistanciasLimitadas(
                self._mapa.cantidad_salas(), self._entradas_abiertas)

        self._desde_cero.reiniciar(sala_jugador.indice)
        return self._decidir_con(self._desde_cero, cazador, sala_jugador)

    def _decidir_con(self, distancias, cazador, sala_jugador):
        u = self._mapa.obtener_sala(cazador.sala_actual)

        # 1. Comparte sala: ataca (FR-013).
        if u is sala_jugador:
            return Decision(ATACAR, None, self._costo_atacar)

        # 2. Extiende la búsqueda mientras el mínimo sea <= rango y u no
        #    esté asentada (FR-014, FR-015).
        rango = cazador.rango
        distancias.extender_hasta(rango, objetivo=u.indice)
        d = distancias.distancia(u.indice)

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

            dist_v = distancias.distancia(v.indice)

            if dist_v is None or puerta.costo + dist_v != d:
                continue

            if elegida is None or v.id < elegida.sala_destino_ref.id:
                elegida = puerta

        return Decision(MOVER, elegida, elegida.costo)
