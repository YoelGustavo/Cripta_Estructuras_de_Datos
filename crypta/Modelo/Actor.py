class Actor:
    def __init__(self, nombre, velocidad):
        self.nombre = nombre
        self.velocidad = velocidad
        self.evento_siguiente = None

    def asignar_evento(self, evento):
        self.evento_siguiente = evento

    def intervalo(self, costo):

        if self.velocidad <= 0:
            raise ValueError(
                f"{self.nombre} no tiene una velocidad válida "
                f"({self.velocidad}); ¿es un enemigo que aún no se activa?"
            )

        intervalo = max(1, costo * 100 // self.velocidad)
        return intervalo