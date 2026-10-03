class Actor:
    def __init__(self, nombre, velocidad):
        self.nombre = nombre
        self.velocidad = velocidad
        self.evento_siguiente = None

    def asignar_evento(self, evento):
        self.evento_siguiente = evento