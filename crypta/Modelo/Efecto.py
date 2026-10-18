VENENO = "veneno"
VELOCIDAD = "velocidad"
ANTORCHA = "antorcha"


class Efecto:
    def __init__(self, tipo, valor=0, hasta=None):
        self.tipo = tipo

        self.valor = valor

        self.hasta = hasta

        self.evento = None

    def __repr__(self):
        return f"Efecto({self.tipo}, valor={self.valor}, hasta={self.hasta})"