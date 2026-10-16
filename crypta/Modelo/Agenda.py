from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar
from crypta.Modelo.Evento import Evento, evento_menor


def _esta_pendiente(evento):
    # Pendiente = todavía va a ocurrir: no se canceló y sigue en el montículo.
    return evento.esta_valido() and evento.en_monticulo


class Agenda:
    def __init__(self):
        self._monticulo = MonticuloMin(evento_menor)
        self._siguiente_secuencia = 0

        # Cuántos eventos PENDIENTES hay. Los cancelados que todavía están
        # dentro del montículo (borrado perezoso) NO cuentan.
        self._pendientes = 0

    def programar(self, tiempo, tipo, objetivo=None, datos=None):
        evento = Evento(
            tiempo=tiempo,
            secuencia=self._siguiente_secuencia,
            tipo=tipo,
            objetivo=objetivo,
            datos=datos
        )

        self._siguiente_secuencia += 1
        self._insertar(evento)
        self._pendientes += 1
        return evento

    def cancelar(self, evento):
        # Solo se cancela algo que todavía va a ocurrir. Cancelar dos veces,
        # o cancelar un evento que ya se ejecutó, no hace nada.
        if evento is None or not _esta_pendiente(evento):
            return False

        evento.cancelar()
        self._pendientes -= 1
        return True

    def reprogramar_por_velocidad(self, actor, reloj_actual, velocidad_nueva):
        if velocidad_nueva <= 0:
            raise ValueError("La velocidad debe ser mayor que 0")
        
        evento_anterior = actor.evento_siguiente

        # Si su acción no está pendiente (no tiene, se canceló, o es la que
        # se está ejecutando ahora mismo), solo cambia la velocidad.
        if evento_anterior is None or not _esta_pendiente(evento_anterior):
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
            evento = self._sacar()

            if evento is not None and evento.esta_valido():
                self._pendientes -= 1
                return evento

        return None

    def siguiente_si_corresponde(self, reloj_actual):
        while not self._monticulo.esta_vacia():
            evento = self._monticulo.ver_min()

            # Quitamos eventos cancelados que hayan
            # quedado físicamente en el montículo.
            if not evento.esta_valido():
                self._sacar()
                continue

            # El próximo evento todavía no debe ejecutarse.
            if evento.tiempo > reloj_actual:
                return None

            self._pendientes -= 1
            return self._sacar()

        return None

    def esta_vacia(self):
        # Vacía para el JUEGO: no queda nada pendiente, aunque el montículo
        # todavía tenga cancelados esperando a ser descartados.
        return self._pendientes == 0

    def __len__(self):
        return self._pendientes

    def restaurar_evento(self, evento):
        if evento is None or _esta_pendiente(evento):
            return

        # Vuelve a estar pendiente.
        evento.reactivar()
        self._pendientes += 1

        # Si ya había salido del montículo (se ejecutó, o se canceló y
        # ya se descartó), hay que volver a meterlo. Si sigue adentro,
        # basta con reactivarlo: meterlo otra vez lo duplicaría.
        if not evento.en_monticulo:
            self._insertar(evento)

    def deshacer_programacion(self, evento):
        # Deshacer "programé este evento" = que nunca ocurra.
        self.cancelar(evento)

    # =========================================================
    # GUARDAR Y CARGAR LA PARTIDA (§4.10)
    # =========================================================

    @property
    def siguiente_secuencia(self):
        """El número de secuencia que recibirá el próximo evento."""
        return self._siguiente_secuencia

    def recorrer_pendientes(self):
        """Recorre los eventos pendientes SIN ordenarlos: O(n). Es para
        quien solo necesita mirarlos todos (el controlador, al buscar los
        enemigos despiertos para las fichas en uso, §4.4). No cambia nada.
        eventos_pendientes, en cambio, los ordena por secuencia porque el
        guardado necesita ese orden; ordenar en cada turno costaría más."""
        for evento in self._monticulo:
            if _esta_pendiente(evento):
                yield evento

    def eventos_pendientes(self):
        """Vector con los eventos pendientes, ordenados por secuencia. Los
        cancelados que siguen dentro del montículo (borrado perezoso) no
        están: no van a ocurrir, así que no hace falta guardarlos."""
        pendientes = Vector()

        for evento in self._monticulo:
            if _esta_pendiente(evento):
                pendientes.agregar(evento)

        ordenar(pendientes, clave=lambda evento: evento.secuencia)
        return pendientes

    def restaurar_pendiente(self, tiempo, secuencia, tipo, objetivo):
        """Vuelve a poner un evento guardado CON SU número de secuencia:
        así los empates se resuelven igual que antes de guardar (§2.3)."""
        if secuencia >= self._siguiente_secuencia:
            raise ValueError(
                f"La secuencia {secuencia} no es menor que la siguiente "
                f"({self._siguiente_secuencia}): primero restaurar_secuencia"
            )

        evento = Evento(tiempo=tiempo, secuencia=secuencia, tipo=tipo, objetivo=objetivo)
        self._insertar(evento)
        self._pendientes += 1
        return evento

    def restaurar_secuencia(self, siguiente):
        """Solo en una agenda nueva: fija el próximo número de secuencia."""
        if self._siguiente_secuencia != 0 or not self._monticulo.esta_vacia():
            raise ValueError("Solo se puede restaurar la secuencia de una agenda nueva")

        if siguiente < 0:
            raise ValueError("La secuencia no puede ser negativa")

        self._siguiente_secuencia = siguiente

    def _insertar(self, evento):
        self._monticulo.insertar(evento)
        evento.en_monticulo = True

    def _sacar(self):
        evento = self._monticulo.extraer_min()
        evento.en_monticulo = False
        return evento