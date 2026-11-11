from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.estructuras.Vector import Vector


class RutaPorCazador:
    """Búsqueda de costo mínimo desde la sala de UN cazador hasta el
    jugador, por las salidas de ida (FR-017, FR-031; research D2).

    Es la alternativa que se mide en el --bench frente a la búsqueda
    compartida, y un segundo verificador en las pruebas. Genérica sobre
    nodos 0..V-1: recibe `salidas(nodo)`, que recorre los pares
    (nodo destino, costo) de las aristas abiertas que salen de `nodo`.

    Cada nodo lleva la etiqueta (distancia, primer paso), comparada en
    orden lexicográfico: al empatar en distancia se conserva el primer paso
    de menor índice. Como los costos son ≥ 1, todos los predecesores de un
    nodo en rutas mínimas se asientan antes que él, así que al asentar al
    jugador su primer paso es el vecino de menor índice que inicia una ruta
    mínima. Los índices densos siguen el orden de los id de sala, así que
    «menor índice» es «menor id» (FR-017).

    Usa los mismos `Vector` con marca que `DistanciasLimitadas`: cada
    búsqueda nueva suma 1 a `_calculo` y no limpia nada.
    """

    def __init__(self, cantidad, salidas):
        self._cantidad = cantidad
        self._salidas = salidas

        self._dist = _vector_de(cantidad, 0)
        self._primero = _vector_de(cantidad, -1)
        self._marca = _vector_de(cantidad, 0)
        self._asentada = _vector_de(cantidad, 0)
        self._calculo = 0

        # Contadores para el --bench.
        self.busquedas = 0
        self.asentados = 0

    def buscar(self, origen, objetivo, limite):
        """(distancia, primer paso) de la ruta más barata de `origen` a
        `objetivo`, o None si no hay ruta de costo ≤ `limite`. Si
        `origen == objetivo`, (0, None)."""
        self._calculo += 1
        self.busquedas += 1

        calculo = self._calculo
        dist = self._dist
        primero = self._primero
        marca = self._marca
        asentada = self._asentada
        frontera = MonticuloMin()

        dist.asignar(origen, 0)
        primero.asignar(origen, -1)
        marca.asignar(origen, calculo)
        frontera.insertar((0, origen))

        while not frontera.esta_vacia():
            distancia, nodo = frontera.extraer_min()

            if distancia > limite:
                return None

            if asentada.obtener(nodo) == calculo:
                continue                      # entrada vieja

            asentada.asignar(nodo, calculo)
            self.asentados += 1

            if nodo == objetivo:
                paso = primero.obtener(nodo)
                return distancia, (None if paso < 0 else paso)

            for destino, costo in self._salidas(nodo):
                nueva = distancia + costo
                paso = destino if nodo == origen else primero.obtener(nodo)

                if (marca.obtener(destino) != calculo
                        or nueva < dist.obtener(destino)):
                    dist.asignar(destino, nueva)
                    primero.asignar(destino, paso)
                    marca.asignar(destino, calculo)
                    frontera.insertar((nueva, destino))

                elif (nueva == dist.obtener(destino)
                        and asentada.obtener(destino) != calculo
                        and paso < primero.obtener(destino)):
                    # Misma distancia, primer paso menor: la entrada que ya
                    # está en el montículo sigue valiendo.
                    primero.asignar(destino, paso)

        return None


def _vector_de(cantidad, valor):
    vector = Vector(cantidad)

    for _ in range(cantidad):
        vector.agregar(valor)

    return vector
