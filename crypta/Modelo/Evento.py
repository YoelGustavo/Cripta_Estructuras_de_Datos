class Evento:
    def __init__(self, tiempo, secuencia, tipo, objetivo=None, datos=None):
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.tipo = tipo
        self.objetivo = objetivo
        self.datos = datos
        self.valido = True
        self.en_monticulo = False

    def cancelar(self):
        self.valido = False

    def esta_valido(self):
        return self.valido

    def reactivar(self):
        self.valido = True
    
def evento_menor(a, b):
    if a.tiempo != b.tiempo:
        return a.tiempo < b.tiempo

    return a.secuencia < b.secuencia