from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Historial import Historial
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Inventario import Inventario


CAPACIDAD_INVENTARIO_SUELTO = 10


class EstadoJuego:

    def __init__(self, inventario=None):
        self.reloj = 0
        self.agenda = Agenda()
        self.historial = Historial()

        if inventario is None:
            inventario = Inventario(CAPACIDAD_INVENTARIO_SUELTO)

        self.inventario = inventario

    @property
    def pergaminos_retroceso(self):
        return self.inventario.cantidad_pergaminos()

    @pergaminos_retroceso.setter
    def pergaminos_retroceso(self, cantidad):
        self.inventario.fijar_pergaminos(cantidad)

    def usar_pergamino_retroceso(self):
        if not self.inventario.tiene_pergamino():
            return False

        if not self.historial.puede_deshacer():
            return False

        self.historial.deshacer_ultima()
        self.inventario.consumir_pergamino()

        return True

    def avanzar_reloj(self, cantidad):
        if cantidad < 0:
            raise ValueError(
                "No se puede avanzar el reloj una cantidad negativa"
            )

        reloj_anterior = self.reloj

        self.reloj += cantidad

        self.historial.registrar_cambio(
            Cambio.de_atributo(
                "reloj",
                self,
                "reloj",
                reloj_anterior
            )
        )
    