from crypta.Modelo.Actor import Actor

class Enemigo(Actor):
    def __init__(self, id_instancia, tipo, vida_inicial=None):
        # Mientras duerme no se sabe su nombre ni su velocidad.
        super().__init__(tipo, 0)
 
        self.id_instancia = id_instancia   # p. ej. "e-201" (único en la cripta)
        self.tipo = tipo                   # id de la ficha, p. ej. "ent_rata_gigante"
        self.vida_inicial = vida_inicial   # None = empieza con vida_max
 
        self.ficha = None
        self.vida_max = 0
        self.vida = 0
        self.ataque = 0
        self.defensa = 0
        self.comportamiento = None# "guardián", "errante" o "rastreador"
 
        self.activo = False
        self.sala_actual = None            # id de la sala (igual que en Jugador)
 
  
    def esta_activo(self):
        return self.activo
 
    def activar(self, ficha): #activa al enemigo con la ficha correspondiente (si no lo estaba ya)
        if self.activo:
            return
 
        if ficha.get("id") != self.tipo:
            raise ValueError(
                f"{self.id_instancia} es de tipo {self.tipo}, "
                f"pero se le dio la ficha {ficha.get('id')}"
            )
 
        if ficha.get("clase") != "enemigo":
            raise ValueError(
                f"La ficha {ficha.get('id')} no es de un enemigo "
                f"(clase {ficha.get('clase')!r})"
            )
 
        self.ficha = ficha
        self.nombre = ficha.get("nombre", self.tipo)
        self.vida_max = ficha["vida_max"]
        self.ataque = ficha["ataque"]
        self.defensa = ficha["defensa"]
        self.velocidad = ficha["velocidad"]
        self.comportamiento = ficha.get("comportamiento")
 
        if self.vida_inicial is None:
            self.vida = self.vida_max
        else:
            self.vida = max(0, min(self.vida_inicial, self.vida_max))
 
        self.activo = True
 
    def desactivar(self): #desactiva el enemigo, solo sirve para la funcion del pergamino.
        self.activo = False
        self.evento_siguiente = None
 
 
    def esta_vivo(self):
        if not self.activo:
            return True
 
        return self.vida > 0
 
    def recibir_danio(self, cantidad):
        if cantidad < 0:
            raise ValueError("El daño no puede ser negativo")
 
        if not self.activo:
            raise RuntimeError(
                f"{self.id_instancia} está dormido: hay que activarlo antes"
            )
 
        self.vida = max(0, self.vida - cantidad)
 
    def curar(self, cantidad):
        if cantidad < 0:
            raise ValueError("La curación no puede ser negativa")
 
        self.vida = min(self.vida_max, self.vida + cantidad)
 
    def objetos_que_suelta(self):
        
        if self.ficha is None:
            return ()
 
        return self.ficha.get("suelta") or ()
 
    def __repr__(self):
        estado = "activo" if self.activo else "dormido"
        return f"Enemigo({self.id_instancia}, {self.tipo}, {estado}, vida={self.vida})"