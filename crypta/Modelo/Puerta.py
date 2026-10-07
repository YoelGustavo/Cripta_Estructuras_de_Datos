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
        otra_puerta._estado = self._estado

    def esta_cerrada(self):
        return self.cerrada

    def abrir(self):
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True

    def requiere_llave(self):
        return self.llave is not None