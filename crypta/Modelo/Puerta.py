class EstadoPuerta:
    def __init__(
        self,
        cerrada=False,
        llave=None,
        cierre_automatico=None
    ):
        self.cerrada = cerrada
        self.llave = llave
        self.cierre_automatico = cierre_automatico


class Puerta:
    def __init__(
        self,
        sala_destino,
        cerrada=False,
        llave=None,
        cierre_automatico=None
    ):
        self.sala_destino = sala_destino
        self.sala_destino_ref = None

        self._estado = EstadoPuerta(
            cerrada,
            llave,
            cierre_automatico
        )

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

    def compartir_estado_con(self, otra_puerta):
        if otra_puerta._estado is self._estado:
            return  # ya comparten estado

        # Las dos mitades describen la MISMA puerta, cada una desde su
        # lado. Antes de compartir se junta lo que dice cada una; si no,
        # se pierde lo que solo decía la otra (por ejemplo, la llave).
        mio = self._estado
        suyo = otra_puerta._estado

        mio.cerrada = mio.cerrada or suyo.cerrada

        if mio.llave is None:
            mio.llave = suyo.llave

        if mio.cierre_automatico is None:
            mio.cierre_automatico = suyo.cierre_automatico

        otra_puerta._estado = mio

    def esta_cerrada(self):
        return self.cerrada

    def abrir(self):
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True

    def requiere_llave(self):
        return self.llave is not None