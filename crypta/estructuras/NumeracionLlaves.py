"""Id de llave → número 0..K-1 (capacidad 003, research D1).

`NumeracionLlaves` es la decisión: se ordenan los ids con `ordenar`, se
quitan los repetidos y se arma un `ArbolBusqueda.desde_ordenados`
(balanceado). El número de una llave es su posición en el orden por id, así
que `numero(a) < numero(b)` ⇔ `a < b` como texto (FR-308): ordenar llaves
es ordenar enteros y recorrer 0..K-1 ya da el orden por id.

`NumeracionPorInsercion` es la alternativa que mide el bench (R5):
`ArbolBusqueda.insertar` en orden de llegada. Si los ids llegan ordenados
el árbol se degenera en una lista (límite de P1 §4.4).

La tabla hash queda solo como alternativa analizada en research D1.
"""

from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Pila import Pila
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


def _altura(raiz):
    """Altura de un árbol sin recursión: el árbol por inserción puede tener
    miles de niveles y la recursión de Python se corta en ~1000."""
    if raiz is None:
        return 0

    altura = 0
    pendientes = Pila()
    pendientes.apilar((raiz, 1))

    while not pendientes.esta_vacia():
        nodo, nivel = pendientes.desapilar()

        if nivel > altura:
            altura = nivel

        if nodo.izq is not None:
            pendientes.apilar((nodo.izq, nivel + 1))

        if nodo.der is not None:
            pendientes.apilar((nodo.der, nivel + 1))

    return altura


class NumeracionLlaves:
    """Números por orden de id, con búsqueda O(log K) garantizada.

    Construcción: O(n log n) para n ids (con repetidos). `numero(id)`:
    O(log K). `id_de(n)`: O(1)."""

    def __init__(self, vector_ids):
        ordenados = Vector(max(1, len(vector_ids)))

        for i in range(len(vector_ids)):
            ordenados.agregar(vector_ids.obtener(i))

        ordenar(ordenados)

        self._ids = Vector(max(1, len(ordenados)))
        pares = Vector(max(1, len(ordenados)))

        for i in range(len(ordenados)):
            id_llave = ordenados.obtener(i)

            if i > 0 and id_llave == ordenados.obtener(i - 1):
                continue

            pares.agregar((id_llave, len(self._ids)))
            self._ids.agregar(id_llave)

        self._arbol = ArbolBusqueda.desde_ordenados(pares)

    def __len__(self):
        return len(self._ids)

    def numero(self, id_llave):
        """El número de la llave, o None si no es una llave de la cripta."""
        return self._arbol.obtener(id_llave)

    def id_de(self, numero):
        return self._ids.obtener(numero)

    def altura(self):
        return _altura(self._arbol._raiz)


class NumeracionPorInsercion:
    """Alternativa del bench (R5): número = orden de llegada.

    `numero(id)`: O(log K) esperado si los ids llegan en orden aleatorio,
    O(K) si llegan ordenados."""

    def __init__(self, vector_ids):
        self._ids = Vector(max(1, len(vector_ids)))
        self._arbol = ArbolBusqueda()

        for i in range(len(vector_ids)):
            id_llave = vector_ids.obtener(i)

            if self._arbol.contiene(id_llave):
                continue

            self._arbol.insertar(id_llave, len(self._ids))
            self._ids.agregar(id_llave)

    def __len__(self):
        return len(self._ids)

    def numero(self, id_llave):
        return self._arbol.obtener(id_llave)

    def id_de(self, numero):
        return self._ids.obtener(numero)

    def altura(self):
        return _altura(self._arbol._raiz)
