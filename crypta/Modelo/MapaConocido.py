"""El conocimiento del jugador (capacidad 002, niebla de guerra).

FR-201 a FR-203, FR-235, FR-236; research D1, D3, D4; data-model
«MapaConocido».

- El estado de cada sala va en un `Vector` por `sala.indice` (D1): O(1).
- El estado recordado de cada puerta va en su `EstadoPuerta` compartido
  (`recordada`, D2): O(1), y los dos lados lo ven igual (FR-205).
- Toda escritura pasa por aquí (D3): cada una que **cambia** el valor anota
  un `Cambio.de_operacion` con el valor anterior por medio de la función
  `anotar` recibida; si el valor no cambia, no anota nada. Deshacer vuelve a
  pasar por aquí (`restaurar_sala`, `restaurar_puerta`), sin anotar, y avisa
  al observador igual que al cambiar.

Sin `dict`, `set` ni `collections` (principio I).
"""

import copy

from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Puerta import ABIERTA, CERRADA
from crypta.estructuras.Vector import Vector


DESCONOCIDA = 0
AVISTADA = 1
EXPLORADA = 2


def _recorrer(lista):
    """Los elementos de un `Vector` (lo que arma el guardado) o de
    cualquier iterable."""
    if isinstance(lista, Vector):
        for i in range(len(lista)):
            yield lista.obtener(i)
    else:
        yield from lista


class MapaConocido:
    """Uno por `Partida` (`partida.conocimiento`). Es estado del juego.

    - `anotar`: función(Cambio). En la partida, `partida._anotar`, que busca
      el historial vigente en cada llamada; nunca un
      `historial.registrar_cambio` guardado (research D3).
    - `exploradas`, `avistadas`: contadores; se ajustan con cada cambio y al
      deshacer.
    - `observador`: la `RutaConocida` de «ir a», o None; no es estado del
      juego. Recibe `sala_explorada(sala)` cuando una sala pasa a explorada o
      deja de estarlo, y `puerta_recordada(estado)` cuando `recordada`
      cambia de valor.
    """

    def __init__(self, mapa, anotar):
        self._mapa = mapa
        self._anotar = anotar
        self._estados = self._vector_vacio()
        self.exploradas = 0
        self.avistadas = 0
        self.observador = None

    def _vector_vacio(self):
        cantidad = self._mapa.cantidad_salas()
        estados = Vector(max(1, cantidad))

        for _ in range(cantidad):
            estados.agregar(DESCONOCIDA)

        return estados

    def __deepcopy__(self, memo):
        """Copia para un punto de control (capacidad 004). `observador` no es
        estado del juego: la copia no avisa a la ruta de la partida viva. El
        `_mapa` y el `_anotar` se reubican por el `memo`."""
        copia = MapaConocido.__new__(MapaConocido)
        memo[id(self)] = copia

        for nombre, valor in vars(self).items():
            if nombre == "observador":
                copia.observador = None
            else:
                setattr(copia, nombre, copy.deepcopy(valor, memo))

        return copia

    # -- consultas, O(1) (FR-235) --------------------------------------------

    def estado(self, sala):
        return self._estados.obtener(sala.indice)

    def esta_explorada(self, sala):
        return self._estados.obtener(sala.indice) == EXPLORADA

    def recordada(self, puerta):
        return puerta.estado.recordada

    def salas_conocidas(self):
        """Pares (Sala, estado) de las salas no desconocidas, en orden de
        índice, que es el orden de id (FR-210). O(V)."""
        for indice in range(len(self._estados)):
            estado = self._estados.obtener(indice)

            if estado != DESCONOCIDA:
                yield self._mapa.sala_por_indice(indice), estado

    # -- escrituras (research D3, D4) ----------------------------------------

    def explorar(self, sala):
        """La sala pasa a explorada (FR-201), se observan sus salidas
        (FR-204) y cada destino desconocido pasa a avistado (FR-202). Una
        salida hacia una sala que no existe no avista nada (D4).
        O(salidas de la sala)."""
        if self.estado(sala) != EXPLORADA:
            self._escribir_sala(sala, EXPLORADA)

        self.observar(sala)

        puertas = sala.puertas()

        for i in range(len(puertas)):
            destino = puertas.obtener(i).sala_destino_ref

            if destino is not None:
                self.avistar(destino)

    def observar(self, sala):
        """`recordada` ← estado real de cada salida de la sala (FR-204).
        Solo anota las que cambian. O(4)."""
        puertas = sala.puertas()

        for i in range(len(puertas)):
            estado = puertas.obtener(i).estado
            real = CERRADA if estado.cerrada else ABIERTA

            if estado.recordada != real:
                anterior = estado.recordada
                estado.recordada = real
                self._anotar(Cambio.de_operacion(
                    "conocimiento", self, "restaurar_puerta",
                    (estado, anterior)))
                self._avisar_puerta(estado)

    def avistar(self, sala):
        """Desconocida → avistada. Cualquier otro estado no cambia. O(1)."""
        if self.estado(sala) == DESCONOCIDA:
            self._escribir_sala(sala, AVISTADA)

    def _escribir_sala(self, sala, nuevo):
        anterior = self._estados.obtener(sala.indice)
        self._fijar_sala(sala.indice, nuevo)
        self._anotar(Cambio.de_operacion(
            "conocimiento", self, "restaurar_sala", (sala.indice, anterior)))

    # -- deshacer: sin anotar, con aviso -------------------------------------

    def restaurar_sala(self, dato):
        indice, anterior = dato
        self._fijar_sala(indice, anterior)

    def restaurar_puerta(self, dato):
        estado, anterior = dato

        if estado.recordada == anterior:
            return

        estado.recordada = anterior
        self._avisar_puerta(estado)

    def _fijar_sala(self, indice, nuevo):
        """Escribe el estado, ajusta los contadores y avisa si la sala pasa a
        explorada o deja de estarlo."""
        anterior = self._estados.obtener(indice)

        if anterior == nuevo:
            return

        self._estados.asignar(indice, nuevo)
        self._contar(anterior, -1)
        self._contar(nuevo, 1)

        if (anterior == EXPLORADA or nuevo == EXPLORADA) \
                and self.observador is not None:
            self.observador.sala_explorada(self._mapa.sala_por_indice(indice))

    def _contar(self, estado, delta):
        if estado == EXPLORADA:
            self.exploradas += delta
        elif estado == AVISTADA:
            self.avistadas += delta

    def _avisar_puerta(self, estado):
        if self.observador is not None:
            self.observador.puerta_recordada(estado)

    # -- guardado (contracts/guardado.md) ------------------------------------

    def restaurar(self, lista, id_sala_inicial):
        """Fija el conocimiento leído de un guardado. `lista`: pares
        (id de sala, estado) de las salas no desconocidas, en orden creciente
        de id; estado 1 (avistada) o 2 (explorada). Los `recordada` ya vienen
        en las puertas. No anota ni avisa. Después llama a `validar`.

        `ValueError` si un id no existe, se repite o está fuera de orden, si
        un estado no es 1 ni 2, o si `validar` falla. O(V + E): los ids se
        buscan avanzando por el índice denso, que está en orden de id."""
        estados = self._vector_vacio()
        exploradas = 0
        avistadas = 0
        cantidad = self._mapa.cantidad_salas()
        indice = 0
        id_anterior = None

        for elemento in _recorrer(lista):
            try:
                id_sala, estado = elemento
            except (TypeError, ValueError):
                raise ValueError(
                    f"Conocimiento: entrada inválida {elemento!r}") from None

            if type(id_sala) is not int:
                raise ValueError(
                    f"Conocimiento: id de sala inválido {id_sala!r}")

            if type(estado) is not int or estado not in (AVISTADA, EXPLORADA):
                raise ValueError(
                    f"Conocimiento: la sala {id_sala} tiene un estado "
                    f"inválido: {estado!r}")

            if id_anterior is not None and id_sala == id_anterior:
                raise ValueError(
                    f"Conocimiento: la sala {id_sala} aparece dos veces")

            if id_anterior is not None and id_sala < id_anterior:
                raise ValueError(
                    f"Conocimiento: la sala {id_sala} está fuera de orden "
                    f"(después de la {id_anterior})")

            while (indice < cantidad
                   and self._mapa.sala_por_indice(indice).id < id_sala):
                indice += 1

            if (indice == cantidad
                    or self._mapa.sala_por_indice(indice).id != id_sala):
                raise ValueError(
                    f"Conocimiento: la sala {id_sala} no existe en la cripta")

            estados.asignar(indice, estado)

            if estado == EXPLORADA:
                exploradas += 1
            else:
                avistadas += 1

            id_anterior = id_sala

        self._estados = estados
        self.exploradas = exploradas
        self.avistadas = avistadas
        self.validar(id_sala_inicial)

    def validar(self, id_sala_inicial):
        """Comprueba las reglas de FR-201 a FR-204 en O(V + E):

        - la sala inicial está explorada (FR-201);
        - cada salida de una sala explorada fue observada (FR-203, FR-204) y
          su destino, si existe, no es desconocido (FR-202);
        - cada sala avistada es destino de una salida de una sala explorada
          (FR-202).

        `ValueError` con la sala si algo falla. La usan `restaurar` y la
        prueba de equivalencia (T041)."""
        inicial = self._mapa.obtener_sala(id_sala_inicial)

        if inicial is None or not self.esta_explorada(inicial):
            raise ValueError(
                f"Conocimiento: la sala inicial {id_sala_inicial} no está "
                f"explorada")

        for indice in range(len(self._estados)):
            estado = self._estados.obtener(indice)
            sala = self._mapa.sala_por_indice(indice)

            if estado == EXPLORADA:
                self._validar_explorada(sala)
            elif estado == AVISTADA:
                self._validar_avistada(sala)

    def _validar_explorada(self, sala):
        puertas = sala.puertas()

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)

            if puerta.estado.recordada is None:
                raise ValueError(
                    f"Conocimiento: la sala {sala.id} está explorada pero su "
                    f"salida {sala.direccion_de(puerta)} no fue observada")

            destino = puerta.sala_destino_ref

            if destino is not None and self.estado(destino) == DESCONOCIDA:
                raise ValueError(
                    f"Conocimiento: la sala {destino.id} es destino de la "
                    f"sala explorada {sala.id} y no está avistada")

    def _validar_avistada(self, sala):
        entradas = sala.entradas

        for i in range(len(entradas)):
            _, origen = entradas.obtener(i)

            if self.esta_explorada(origen):
                return

        raise ValueError(
            f"Conocimiento: la sala {sala.id} está avistada pero ninguna "
            f"salida de una sala explorada llega a ella")
