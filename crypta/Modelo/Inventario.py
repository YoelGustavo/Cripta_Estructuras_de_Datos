from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.ordenamiento import copiar_a_vector, ordenar


class Inventario:

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError(
                "La capacidad del inventario debe ser mayor que 0"
            )

        self._capacidad = capacidad
        self._objetos = ListaDoble()

        # Nodo que el jugador está viendo actualmente.
        self._actual = None

    def __len__(self):
        return len(self._objetos)

    def esta_vacio(self):
        return self._objetos.esta_vacia()

    def esta_lleno(self):
        return len(self._objetos) >= self._capacidad

    def capacidad(self):
        return self._capacidad

    def espacio_disponible(self):
        return self._capacidad - len(self._objetos)

    def recoger(self, objeto):
        if self.esta_lleno():
            return False

        nodo = self._objetos.agregar_al_final(
            objeto
        )

        # Si es el primer objeto recogido,
        # pasa a ser la posición actual.
        if self._actual is None:
            self._actual = nodo

        return True

    def actual(self):
        if self._actual is None:
            return None

        return self._actual.valor

    def avanzar(self):
        if self._actual is None:
            return None

        siguiente = self._objetos.siguiente(
            self._actual
        )

        if siguiente is None:
            return None

        self._actual = siguiente

        return self._actual.valor

    def retroceder(self):
        if self._actual is None:
            return None

        anterior = self._objetos.anterior(
            self._actual
        )

        if anterior is None:
            return None

        self._actual = anterior

        return self._actual.valor

    def soltar_actual(self):
        if self._actual is None:
            return None

        nodo_eliminar = self._actual

        # Decidimos cuál será la nueva posición actual
        # ANTES de quitar el nodo.
        siguiente = self._objetos.siguiente(
            nodo_eliminar
        )

        anterior = self._objetos.anterior(
            nodo_eliminar
        )

        if siguiente is not None:
            self._actual = siguiente

        elif anterior is not None:
            self._actual = anterior

        else:
            self._actual = None

        return self._objetos.quitar_nodo(
            nodo_eliminar
        )

    def equipar_actual(self):
        if self._actual is None:
            return None

        self._objetos.mover_al_frente(
            self._actual
        )

        return self._actual.valor

    def orden_real(self):
        resultado = []

        for objeto in self._objetos:
            resultado.append(objeto)

        return resultado

    def vista_ordenada(self, criterio):
        # Creamos una copia del orden real.
        # Así nunca modificamos la ListaDoble del inventario.
        vista = copiar_a_vector(self._objetos)

        if criterio == "peso":
            clave = lambda objeto: objeto["peso"]
            comparacion_costosa = False

        elif criterio == "valor":
            clave = lambda objeto: objeto["valor"]
            comparacion_costosa = False

        elif criterio == "nombre":
            clave = lambda objeto: objeto["nombre"].lower()
            comparacion_costosa = True

        else:
            raise ValueError(
                "Criterio inválido. Use: peso, valor o nombre"
            )

        algoritmo = ordenar(
            vista,
            clave=clave,
            comparacion_costosa=comparacion_costosa
        )

        return vista, algoritmo