class Trampa:
    def __init__(
        self,
        instancia,
        tipo,
        activa=True
    ):
        self.instancia = instancia
        self.tipo = tipo
        self.activa = activa

    def esta_activa(self):
        return self.activa

    def activar(self):
        self.activa = True

    def desactivar(self):
        self.activa = False