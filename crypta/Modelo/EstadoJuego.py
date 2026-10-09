from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Historial import Historial
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Inventario import Inventario


# Solo para cuando no se le pasa el inventario del jugador (pruebas
# sueltas del historial). En la partida real siempre se le pasa.
CAPACIDAD_INVENTARIO_SUELTO = 10


class EstadoJuego:

    def __init__(self, inventario=None):
        self.reloj = 0
        self.agenda = Agenda()
        self.historial = Historial()

        # §2.11: el pergamino "se descuenta del inventario al usarlo", así
        # que los pergaminos viven en el inventario del jugador. La partida
        # le pasa ese inventario; si no se pasa, se usa uno propio.
        if inventario is None:
            inventario = Inventario(CAPACIDAD_INVENTARIO_SUELTO)

        self.inventario = inventario

    # Antes era un número guardado aquí. Ahora se lee del inventario, para
    # que haya UN solo lugar donde están los pergaminos. Se deja con el
    # mismo nombre para que las pruebas de 4.6 sigan funcionando igual.
    @property
    def pergaminos_retroceso(self):
        return self.inventario.cantidad_pergaminos()

    @pergaminos_retroceso.setter
    def pergaminos_retroceso(self, cantidad):
        self.inventario.fijar_pergaminos(cantidad)

    def usar_pergamino_retroceso(self):
        """Deshace la última acción del jugador (§2.11).

        - No consume tiempo y no se registra como acción.
        - El pergamino queda consumido DESPUÉS de completar el retroceso.
        - Su cantidad no se anota en el historial, así que el retroceso
          no la cambia: queda como estaba al usarlo, menos el gastado.
        """
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
    