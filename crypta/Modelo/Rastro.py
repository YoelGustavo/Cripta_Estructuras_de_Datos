from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda


class Huella:
    def __init__(
        self,
        id_sala,
        tiempo,
        anterior_misma_sala=None
    ):
        self.id_sala = id_sala
        self.tiempo = tiempo
        self.anterior_misma_sala = anterior_misma_sala

    def esta_vigente(self, reloj_actual):
        return reloj_actual - self.tiempo < 400


class Rastro:
    def __init__(self):
        # Recorrido real del jugador.
        self._huellas = ListaDoble()

        # Última huella conocida de cada sala.
        self._por_sala = ArbolBusqueda()

    def __len__(self):
        return len(self._huellas)

    def registrar(self, id_sala, tiempo):
        anterior = self._por_sala.obtener(
            id_sala
        )

        huella = Huella(
            id_sala,
            tiempo,
            anterior
        )

        nodo = self._huellas.agregar_al_final(
            huella
        )

        self._por_sala.insertar(
            id_sala,
            huella
        )

        return nodo

    def obtener_reciente(
        self,
        id_sala,
        reloj_actual
    ):
        huella = self._por_sala.obtener(
            id_sala
        )

        if huella is None:
            return None

        if not huella.esta_vigente(
            reloj_actual
        ):
            return None

        return huella

    def quitar_ultimo(self):
        nodo = self._huellas.ultimo()

        if nodo is None:
            return None

        huella = nodo.valor

        self._huellas.quitar_nodo(
            nodo
        )

        # Restauramos el índice de esa sala.
        if huella.anterior_misma_sala is None:
            self._por_sala.eliminar(
                huella.id_sala
            )
        else:
            self._por_sala.insertar(
                huella.id_sala,
                huella.anterior_misma_sala
            )

        return huella

    def ultimo(self):
        return self._huellas.ultimo()

    def __iter__(self):
        return iter(self._huellas)