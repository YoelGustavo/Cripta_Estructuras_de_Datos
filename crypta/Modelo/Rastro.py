from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda


class Huella:
    def __init__(
        self,
        id_sala,
        tiempo,
        anterior_misma_sala=None,
        sala=None
    ):
        self.id_sala = id_sala
        self.tiempo = tiempo
        self.anterior_misma_sala = anterior_misma_sala
        self.sala = sala

    def esta_vigente(self, reloj_actual):
        return reloj_actual - self.tiempo < 400


class Rastro:
    def __init__(self):
        self._huellas = ListaDoble()

        self._por_sala = ArbolBusqueda()

    def __len__(self):
        return len(self._huellas)

    def registrar(
        self,
        id_sala,
        tiempo,
        sala=None
    ):
        anterior = self._por_sala.obtener(
            id_sala
        )

        huella = Huella(
            id_sala,
            tiempo,
            anterior,
            sala
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

        if huella.anterior_misma_sala is None:
            self._por_sala.eliminar(
                huella.id_sala
            )
        else:
            self._por_sala.insertar(
                huella.id_sala,
                huella.anterior_misma_sala
            )

        if huella.sala is not None:
            if huella.anterior_misma_sala is None:
                huella.sala.ultimo_rastro = None
            else:
                huella.sala.ultimo_rastro = (
                    huella.anterior_misma_sala.tiempo
                )

        return huella

    def ultimo(self):
        return self._huellas.ultimo()

    def __iter__(self):
        return iter(self._huellas)