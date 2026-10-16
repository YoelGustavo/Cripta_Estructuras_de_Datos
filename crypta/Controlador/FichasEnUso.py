"""Las fichas en uso no se desalojan de la caché (§4.4).

El enunciado: "Una ficha referenciada por al menos una instancia activa
—un enemigo vivo, un objeto en el inventario o en el suelo de la sala
actual, una trampa de la sala actual— queda fuera de la política de
desalojo mientras dure esa referencia."

Después de cada comando que salió bien (y al empezar o cargar una
partida), el controlador llama a actualizar(partida). Se arma el conjunto
de ids que están en uso AHORA y se compara con el de la vez anterior:
  - los que entraron se marcan:  repositorio.marcar_en_uso(id)
  - los que salieron se liberan: repositorio.liberar_uso(id)
Cada id se marca UNA sola vez, aunque haya tres ratas: la CacheLRU cuenta
usos y así cada marca tiene exactamente una liberación.

Los conjuntos son ArbolBusqueda (id -> True): sin dict ni set (§7).
"""

from crypta.Modelo.Partida import TURNO_ENEMIGO
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda


class FichasEnUso:

    def __init__(self, repositorio):
        self._repositorio = repositorio
        self._marcadas = ArbolBusqueda()

    def actualizar(self, partida):
        ahora = self._en_uso(partida)

        for id_tipo, _ in ahora.en_orden():
            if not self._marcadas.contiene(id_tipo):
                self._repositorio.marcar_en_uso(id_tipo)

        for id_tipo, _ in self._marcadas.en_orden():
            if not ahora.contiene(id_tipo):
                self._repositorio.liberar_uso(id_tipo)

        self._marcadas = ahora

    def esta_marcada(self, id_tipo):
        return self._marcadas.contiene(id_tipo)

    def _en_uso(self, partida):
        ahora = ArbolBusqueda()
        sala = partida.sala_actual()

        # Objetos del inventario (también los equipados: están en la lista).
        for ficha in partida.jugador.inventario.orden_real():
            _anotar(ahora, ficha["id"])

        # Objetos del suelo y trampas de la sala actual.
        for i in range(sala.cantidad_objetos()):
            _anotar(ahora, sala.objeto_en(i))

        for i in range(sala.cantidad_trampas()):
            _anotar(ahora, sala.trampa_en(i).tipo)

        # Enemigos vivos: los de la sala actual...
        for i in range(sala.cantidad_enemigos()):
            _anotar(ahora, sala.enemigo_en(i).tipo)

        # ...y los despiertos en OTRAS salas: cada uno tiene su próximo
        # turno pendiente en la agenda. Un enemigo muerto ya no lo tiene
        # (se cancela al morir). Los dormidos de salas que el jugador no
        # visitó todavía no son instancias activas.
        for evento in partida.agenda.recorrer_pendientes():
            if evento.tipo == TURNO_ENEMIGO:
                _anotar(ahora, evento.objetivo.tipo)

        return ahora


def _anotar(arbol, id_tipo):
    if not arbol.contiene(id_tipo):
        arbol.insertar(id_tipo, True)