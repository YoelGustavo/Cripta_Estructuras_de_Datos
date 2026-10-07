from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Historial import Historial
from crypta.Modelo.Cambio import Cambio


class EstadoJuego:

    def __init__(self):
        self.reloj = 0
        self.agenda = Agenda()
        self.historial = Historial()

        # Los pergaminos quedan fuera del estado reversible.
        self.pergaminos_retroceso = 0

    def usar_pergamino_retroceso(self):
        if self.pergaminos_retroceso <= 0:
            return False

        if not self.historial.puede_deshacer():
            return False

        # Se consume y NO se registra en el historial.
        self.pergaminos_retroceso -= 1

        return self.historial.deshacer_ultima()

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

    