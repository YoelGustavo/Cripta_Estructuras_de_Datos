from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.estructuras.Vector import Vector


class DistanciasLimitadas:
    """Búsqueda de costo mínimo (Dijkstra) perezosa y reanudable, desde un
    origen, por las ENTRADAS de cada nodo (FR-014, FR-036; research D1, D5).

    Es genérica: no conoce salas ni puertas. Trabaja sobre nodos 0..V-1
    (los índices densos del mapa) y recibe `entradas(nodo)`, que recorre
    los pares (nodo de origen, costo) de las aristas abiertas que llegan a
    `nodo`. Así `distancia(x)` es el costo mínimo para ir de x al origen,
    aunque haya salidas sin vuelta.

    - Perezosa: solo asienta lo que se le pide con `extender_hasta`; como
      los costos son ≥ 1, los nodos se asientan en orden de distancia y
      parar al pasar el límite deja exactamente los de dist ≤ límite.
    - Reanudable: el montículo queda como estaba; la siguiente llamada
      sigue desde ahí.
    - Inserción perezosa: no hay «bajar clave»; se inserta de nuevo y la
      entrada vieja se descarta al sacarla.
    - Marca: `_marca` y `_asentada` guardan el número del cálculo en que se
      tocó o se asentó cada nodo. Empezar de nuevo es sumar 1 a
      `_calculo`, O(1), sin limpiar los V valores.

    Memoria: 3 `Vector` de V enteros, reservados una sola vez, más el
    montículo (a lo sumo una entrada por arista relajada).
    """

    def __init__(self, cantidad, entradas):
        self._cantidad = cantidad
        self._entradas = entradas

        self._dist = _vector_de_ceros(cantidad)
        self._marca = _vector_de_ceros(cantidad)
        self._asentada = _vector_de_ceros(cantidad)

        self._frontera = MonticuloMin()
        self._calculo = 0
        self._origen = None
        self._hasta = 0

        # Contadores para el --bench.
        self.busquedas = 0
        self.asentados = 0

    @property
    def cantidad(self):
        return self._cantidad

    @property
    def origen(self):
        """Nodo de origen del cálculo vigente, o None si no hay ninguno."""
        return self._origen

    @property
    def hasta(self):
        """Mayor distancia asentada en el cálculo vigente (ρ)."""
        return self._hasta

    def reiniciar(self, origen):
        """Empieza un cálculo nuevo desde `origen`. O(1)."""
        self._calculo += 1
        self._origen = origen
        self._hasta = 0
        self._frontera = MonticuloMin()
        self.busquedas += 1

        self._dist.asignar(origen, 0)
        self._marca.asignar(origen, self._calculo)
        self._frontera.insertar((0, origen))

    def extender_hasta(self, limite, objetivo=None):
        """Asienta nodos en orden de distancia mientras el mínimo de la
        frontera sea ≤ `limite`. Si se da `objetivo`, para en cuanto queda
        asentado. Devuelve si `objetivo` está asentado (o None si no se dio
        objetivo)."""
        if self._origen is None:
            return False if objetivo is not None else None

        if objetivo is not None and self.esta_asentada(objetivo):
            return True

        calculo = self._calculo
        frontera = self._frontera
        dist = self._dist
        marca = self._marca
        asentada = self._asentada

        while not frontera.esta_vacia():
            distancia, nodo = frontera.ver_min()

            if distancia > limite:
                break

            frontera.extraer_min()

            if asentada.obtener(nodo) == calculo:
                continue                      # entrada vieja

            asentada.asignar(nodo, calculo)
            self._hasta = distancia
            self.asentados += 1

            for origen, costo in self._entradas(nodo):
                nueva = distancia + costo

                if (marca.obtener(origen) != calculo
                        or nueva < dist.obtener(origen)):
                    dist.asignar(origen, nueva)
                    marca.asignar(origen, calculo)
                    frontera.insertar((nueva, origen))

            if nodo == objetivo:
                return True

        if objetivo is None:
            return None

        return self.esta_asentada(objetivo)

    def esta_asentada(self, nodo):
        """Si `nodo` tiene su distancia definitiva en el cálculo vigente.
        O(1)."""
        return (self._origen is not None
                and self._asentada.obtener(nodo) == self._calculo)

    def distancia(self, nodo):
        """Distancia definitiva de `nodo` al origen, o None si todavía no
        está asentado en el cálculo vigente. O(1)."""
        if not self.esta_asentada(nodo):
            return None

        return self._dist.obtener(nodo)


def _vector_de_ceros(cantidad):
    vector = Vector(cantidad)

    for _ in range(cantidad):
        vector.agregar(0)

    return vector
