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

        for ficha in partida.jugador.inventario.orden_real():
            _anotar(ahora, ficha["id"])

        for i in range(sala.cantidad_objetos()):
            _anotar(ahora, sala.objeto_en(i))

        for i in range(sala.cantidad_trampas()):
            _anotar(ahora, sala.trampa_en(i).tipo)

        for i in range(sala.cantidad_enemigos()):
            _anotar(ahora, sala.enemigo_en(i).tipo)

        for evento in partida.agenda.recorrer_pendientes():
            if evento.tipo == TURNO_ENEMIGO:
                _anotar(ahora, evento.objetivo.tipo)

        return ahora


def _anotar(arbol, id_tipo):
    if not arbol.contiene(id_tipo):
        arbol.insertar(id_tipo, True)