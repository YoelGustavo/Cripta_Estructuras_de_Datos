from crypta.estructuras.ListaDoble import ListaDoble


class RegistroAccion:
    def __init__(self, descripcion=""):
        self.descripcion = descripcion
        self._cambios = ListaDoble()

    def registrar_cambio(self, cambio):
        self._cambios.agregar_al_final(cambio)

    def cantidad_cambios(self):
        return len(self._cambios)

    def esta_vacio(self):
        return len(self._cambios) == 0

    def deshacer(self):
        """
        Los cambios deben deshacerse en orden inverso.

        Si una acción produjo:
            A -> B -> C

        restauramos:
            C -> B -> A
        """
        nodo = self._cambios.ultimo()

        while nodo is not None:
            anterior = self._cambios.anterior(nodo)

            cambio = nodo.valor
            cambio.deshacer()

            nodo = anterior


class Historial:
    def __init__(self, limite=5):
        if limite < 1:
            raise ValueError(
                "El límite del historial debe ser mayor que 0"
            )

        self._limite = limite
        self._acciones = ListaDoble()

    def __len__(self):
        return len(self._acciones)

    def esta_vacio(self):
        return self._acciones.esta_vacia()

    def registrar(self, accion):
        """Abre la acción del jugador que empieza AHORA.

        Llamarlo al EMPEZAR la acción, antes de hacer cualquier cambio.
        Desde aquí y hasta la próxima acción del jugador, todo cambio
        (lo que hace el jugador, las ratas, el veneno, el reloj...) se
        anota en esta acción con registrar_cambio (§2.11). Por eso se
        guarda aunque todavía esté vacía.
        """
        if accion is None:
            raise ValueError("Falta la acción a registrar")

        self._acciones.agregar_al_final(
            accion
        )

        if len(self._acciones) > self._limite:
            mas_antigua = self._acciones.primero()

            if mas_antigua is not None:
                self._acciones.quitar_nodo(
                    mas_antigua
                )

    def registrar_cambio(self, cambio):
        """Anota un cambio en la acción abierta (la última registrada).

        Antes de la primera acción del jugador no hay nada que deshacer:
        el cambio no se anota."""
        nodo = self._acciones.ultimo()

        if nodo is None or cambio is None:
            return

        nodo.valor.registrar_cambio(cambio)

    def puede_deshacer(self):
        return not self._acciones.esta_vacia()

    def deshacer_ultima(self):
        nodo = self._acciones.ultimo()

        if nodo is None:
            return False

        accion = nodo.valor

        accion.deshacer()

        self._acciones.quitar_nodo(
            nodo
        )

        return True