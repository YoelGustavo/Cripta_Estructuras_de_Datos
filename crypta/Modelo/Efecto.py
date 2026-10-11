# Tipos de efecto temporal (§2.10).
VENENO = "veneno"
VELOCIDAD = "velocidad"
ANTORCHA = "antorcha"


class Efecto:
    def __init__(self, tipo, valor=0, hasta=None):
        self.tipo = tipo

        # Veneno: daño de cada pulso.
        # Velocidad: cuánto cambió la velocidad (para devolverlo al final).
        self.valor = valor

        # Instante en que termina (veneno: el último pulso puede caer justo aquí).
        self.hasta = hasta

        # Su próximo evento en la agenda (pulso o fin), o None.
        self.evento = None

    def __repr__(self):
        return f"Efecto({self.tipo}, valor={self.valor}, hasta={self.hasta})"