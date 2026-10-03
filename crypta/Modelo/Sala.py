class Sala:
    def __init__(self, id_sala, nombre, salidas):
        self.id = id_sala
        self.nombre = nombre

        # Por ahora proviene directamente del JSON del API.
        self.salidas = salidas

        # El contenido todavía no ha sido solicitado.
        self.contenido = None

    def contenido_cargado(self):
        return self.contenido is not None

    def asignar_contenido(self, contenido):
        self.contenido = contenido