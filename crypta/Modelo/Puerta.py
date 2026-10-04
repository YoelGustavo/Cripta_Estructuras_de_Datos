class Puerta:
    def __init__(
        self,
        sala_destino,
        cerrada=False,
        llave=None,
        cierre_automatico=None
    ):
        self.sala_destino = sala_destino
        self.cerrada = cerrada
        self.llave = llave
        self.cierre_automatico = cierre_automatico

    def esta_cerrada(self):
        return self.cerrada

    def abrir(self):
        self.cerrada = False

    def cerrar(self):
        self.cerrada = True

    def requiere_llave(self):
        return self.llave is not None