from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.Modelo.Evento import Evento, evento_menor


class Agenda:
    def __init__(self):
        self._monticulo = MonticuloMin(evento_menor)
        self._siguiente_secuencia = 0

    def programar(self, tiempo, tipo, objetivo=None, datos=None):
        evento = Evento(
            tiempo=tiempo,
            secuencia=self._siguiente_secuencia,
            tipo=tipo,
            objetivo=objetivo,
            datos=datos
        )

        self._siguiente_secuencia += 1
        self._monticulo.insertar(evento)
        return evento

    def cancelar(self, evento):
        evento.cancelar()

    def reprogramar_por_velocidad(self, actor, reloj_actual, velocidad_nueva):
        if velocidad_nueva <= 0:
            raise ValueError("La velocidad debe ser mayor que 0")
        
        evento_anterior = actor.evento_siguiente

        if evento_anterior is None or not evento_anterior.esta_valido():
            actor.velocidad = velocidad_nueva
            return None

        velocidad_anterior = actor.velocidad

        restante = evento_anterior.tiempo - reloj_actual

        restante_nuevo = max(
            1,
            restante * velocidad_anterior // velocidad_nueva
        )

        tiempo_nuevo = reloj_actual + restante_nuevo

        self.cancelar(evento_anterior)

        actor.velocidad = velocidad_nueva

        evento_nuevo = self.programar(
            tiempo_nuevo,
            evento_anterior.tipo,
            actor,
            evento_anterior.datos
        )

        actor.asignar_evento(evento_nuevo)

        return evento_nuevo

    def siguiente(self):
        while not self._monticulo.esta_vacia():
            evento = self._monticulo.extraer_min()

            if evento is not None and evento.esta_valido():
                return evento

        return None

    def siguiente_si_corresponde(self, reloj_actual):
        while not self._monticulo.esta_vacia():
            evento = self._monticulo.ver_min()

            # Quitamos eventos cancelados que hayan
            # quedado físicamente en el montículo.
            if not evento.esta_valido():
                self._monticulo.extraer_min()
                continue

            # El próximo evento todavía no debe ejecutarse.
            if evento.tiempo > reloj_actual:
                return None

            return self._monticulo.extraer_min()

        return None

    def esta_vacia(self):
        return self._monticulo.esta_vacia()

    def __len__(self):
        return len(self._monticulo)

    def restaurar_evento(self, evento):
        if evento is None:
            return

        evento.reactivar()
        self._monticulo.insertar(evento)

    def deshacer_programacion(self, evento):
        if evento is None:
            return

        evento.cancelar()