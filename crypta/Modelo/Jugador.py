from crypta.Modelo.Actor import Actor
from crypta.Modelo.Inventario import Inventario
from crypta.Modelo.Rastro import Rastro
 
 
class Jugador(Actor): #hereda de Actor.
 
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
        self.rastro = Rastro()
 
    def esta_vivo(self):
        return self.vida > 0
 
 
    def arma(self):
        return self.inventario.arma()
 
    def armadura(self):
        return self.inventario.armadura()
 
    def ataque_total(self):
        """Ataque base + ataque_bonus del arma equipada (si hay)."""
        arma = self.inventario.arma()
        bono = 0 if arma is None else arma.get("ataque_bonus", 0)
        return self.ataque + bono
 
    def defensa_total(self):
        """Defensa base + defensa_bonus de la armadura equipada (si hay)."""
        armadura = self.inventario.armadura()
        bono = 0 if armadura is None else armadura.get("defensa_bonus", 0)
        return self.defensa + bono
 
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
 
    def mover_a(self, sala, tiempo):
        self.sala_actual = sala.id
 
        self.rastro.registrar(
            sala.id,
            tiempo,
            sala
        )
 
        sala.registrar_rastro(
            tiempo
        )
 
    def deshacer_ultimo_movimiento( #esto para el pergamino igual.
        self,
        sala_anterior
    ):
        self.rastro.quitar_ultimo()
        self.sala_actual = sala_anterior