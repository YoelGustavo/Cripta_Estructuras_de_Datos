from crypta.Modelo.Actor import Actor
from crypta.Modelo.Inventario import Inventario
from crypta.estructuras.ListaDoble import ListaDoble


class Jugador(Actor):

    def __init__(
        self,
        nombre,
        vida_max,
        ataque,
        defensa,
        velocidad,
        inventario_max
    ):
        super().__init__(
            nombre,
            velocidad
        )

        self.vida_max = vida_max
        self.vida = vida_max

        self.ataque = ataque
        self.defensa = defensa

        self.inventario = Inventario(
            inventario_max
        )

        self.sala_actual = None

        # Guarda el recorrido real del jugador.
        self.rastro = ListaDoble()

    def esta_vivo(self):
        return self.vida > 0

    def recibir_danio(self, cantidad):
        if cantidad < 0:
            raise ValueError(
                "El daño no puede ser negativo"
            )

        self.vida = max(
            0,
            self.vida - cantidad
        )

    def curar(self, cantidad):
        if cantidad < 0:
            raise ValueError(
                "La curación no puede ser negativa"
            )

        self.vida = min(
            self.vida_max,
            self.vida + cantidad
        )

    def mover_a(self, id_sala):
        self.sala_actual = id_sala
        self.rastro.agregar_al_final(
            id_sala
        )

    def deshacer_ultimo_movimiento(self, sala_anterior):
        ultimo = self.rastro.ultimo()

        if ultimo is not None:
            self.rastro.quitar_nodo(ultimo)

        self.sala_actual = sala_anterior