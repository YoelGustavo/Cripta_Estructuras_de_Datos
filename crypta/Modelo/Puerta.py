from crypta.Modelo.DatosInvalidos import DatosInvalidos


# Costo de una salida que no declara costo en ningún lado (FR-001). Es la
# única constante de costo de movimiento (FR-024, principio IV).
COSTO_POR_OMISION = 100


class EstadoPuerta:
    """Lo que comparten los dos lados de una salida.

    - `cerrada`, `llave`, `cierre_automatico`: como en la primera parte.
    - costo (FR-001, FR-002): el declarado por los lados, o None si ninguno
      lo declara; `costo` da COSTO_POR_OMISION en ese caso.
    - `extremos` (Sala, Sala): lo fija el Mapa; no es estado del juego.
    - `observador`: la búsqueda vigente, o None; no es estado del juego.
      Recibe `puerta_cambio(estado)` cada vez que `cerrada` cambia de valor
      (abrir, cierre automático o el pergamino, que usa setattr).
    """

    def __init__(
        self,
        cerrada=False,
        llave=None,
        cierre_automatico=None,
        costo=None
    ):
        self._cerrada = cerrada
        self.llave = llave
        self.cierre_automatico = cierre_automatico
        self.costo_declarado = costo
        self.extremos = None
        self.observador = None

    @property
    def cerrada(self):
        return self._cerrada

    @cerrada.setter
    def cerrada(self, valor):
        if valor == self._cerrada:
            return

        self._cerrada = valor

        if self.observador is not None:
            self.observador.puerta_cambio(self)

    @property
    def costo(self):
        if self.costo_declarado is None:
            return COSTO_POR_OMISION

        return self.costo_declarado


class Puerta:
    def __init__(
        self,
        sala_destino,
        cerrada=False,
        llave=None,
        cierre_automatico=None,
        costo=None
    ):
        """`costo` es el valor que declara este lado (ya validado por la
        Sala), o None si no lo declara."""
        self.sala_destino = sala_destino
        self.sala_destino_ref = None

        self._estado = EstadoPuerta(
            cerrada,
            llave,
            cierre_automatico,
            costo
        )

    @property
    def estado(self):
        return self._estado

    @property
    def cerrada(self):
        return self._estado.cerrada

    @cerrada.setter
    def cerrada(self, valor):
        self._estado.cerrada = valor

    @property
    def llave(self):
        return self._estado.llave

    @llave.setter
    def llave(self, valor):
        self._estado.llave = valor

    @property
    def cierre_automatico(self):
        return self._estado.cierre_automatico

    @cierre_automatico.setter
    def cierre_automatico(self, valor):
        self._estado.cierre_automatico = valor

    @property
    def costo(self):
        """Costo de atravesar la salida (FR-001, FR-002). Solo lectura."""
        return self._estado.costo

    def compartir_estado_con(self, otra_puerta, sala=None, sala_otra=None):
        """Une los dos lados de una salida en un solo estado.

        `sala` es la sala de esta puerta y `sala_otra` la de la otra; solo
        sirven para nombrar la salida si los costos no coinciden (FR-010).
        Costos: ambos iguales → ese; solo uno → ese en ambos sentidos;
        ninguno → COSTO_POR_OMISION; distintos → DatosInvalidos."""
        if otra_puerta._estado is self._estado:
            return

        mio = self._estado
        suyo = otra_puerta._estado

        if (mio.costo_declarado is not None
                and suyo.costo_declarado is not None
                and mio.costo_declarado != suyo.costo_declarado):
            raise DatosInvalidos(
                f"La salida entre las salas "
                f"{self._describir(sala, otra_puerta.sala_destino)} y "
                f"{otra_puerta._describir(sala_otra, self.sala_destino)} "
                f"declara costos distintos: "
                f"{mio.costo_declarado} y {suyo.costo_declarado}"
            )

        if mio.costo_declarado is None:
            mio.costo_declarado = suyo.costo_declarado

        mio.cerrada = mio.cerrada or suyo.cerrada

        if mio.llave is None:
            mio.llave = suyo.llave

        if mio.cierre_automatico is None:
            mio.cierre_automatico = suyo.cierre_automatico

        otra_puerta._estado = mio

    def _describir(self, sala, id_sala):
        """«3 (E)»: la sala de esta puerta y su dirección, si se conocen."""
        if sala is None:
            return f"{id_sala}"

        return f"{sala.id} ({sala.direccion_de(self)})"

    def esta_cerrada(self):
        return self.cerrada

    def abrir(self):
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True

    def requiere_llave(self):
        return self.llave is not None
