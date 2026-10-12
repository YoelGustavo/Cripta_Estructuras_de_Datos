
from crypta.estructuras.Cola import Cola

MAXIMO_MENSAJES = 20


class Bitacora:
    """Almacena los últimos 20 mensajes del juego."""

    def __init__(self):
        self._mensajes = Cola(
            capacidad_max=MAXIMO_MENSAJES
        )

    def agregar(self, reloj, texto):
        self._mensajes.encolar(
            f"[t={reloj}] {texto}"
        )

    def __len__(self):
        return len(self._mensajes)

    def __iter__(self):
        return iter(self._mensajes)

