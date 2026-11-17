"""Una orden «ir a» en curso (capacidad 002, FR-216, FR-221).

Data-model «Viaje»; research D8. No es estado del juego: vive lo que dura la
orden. No sabe de red ni de log: el bucle está en
`Comandos.ejecutar_ir_a`.
"""

from crypta.Modelo.Partida import AccionInvalida


# Motivos de parada (FR-221). Los textos están en
# `crypta/Vista/FormatoMapa.texto_motivo` (contracts/vista.md).
LLEGADA = "llegada"
ENEMIGOS = "enemigos"
DANIO = "daño"
SIN_RUTA = "sin ruta"
PASO_IMPOSIBLE = "paso imposible"
FIN_PARTIDA = "fin de la partida"


class Viaje:
    """- `destino`: la `Sala` a la que se viaja (explorada, distinta de la
      actual).
    - `pasos`: pasos hechos.
    - `motivo`: por qué se detuvo, o None mientras sigue.
    - `detalle`: el mensaje del error de un PASO_IMPOSIBLE, o None."""

    def __init__(self, destino):
        self.destino = destino
        self.pasos = 0
        self.motivo = None
        self.detalle = None

    @staticmethod
    def validar(partida, id_destino):
        """El `Viaje` hacia `id_destino`, o `AccionInvalida` con los
        mensajes de contracts/cli.md (FR-216). Una sala que no existe da el
        mismo mensaje que una no explorada: el jugador no sabe cuáles hay."""
        destino = partida.mapa.obtener_sala(id_destino)

        if destino is None or not partida.conocimiento.esta_explorada(destino):
            raise AccionInvalida(f"No conoces la sala {id_destino}.")

        actual = partida.sala_actual()

        if destino is actual:
            raise AccionInvalida(f"Ya estás en la sala {id_destino}.")

        if not partida.ruta_conocida().hay_ruta(actual, destino):
            raise AccionInvalida(
                f"No conoces una ruta abierta hasta la sala {id_destino}.")

        return Viaje(destino)

    @property
    def terminado(self):
        return self.motivo is not None

    def siguiente_direccion(self, partida):
        """La dirección del próximo paso, o None (y el motivo SIN_RUTA) si
        ya no hay ruta conocida."""
        sala = partida.sala_actual()
        puerta = partida.ruta_conocida().siguiente_paso(sala, self.destino)

        if puerta is None:
            self.detener(SIN_RUTA)
            return None

        return sala.direccion_de(puerta)

    def despues_del_paso(self, partida, vida_antes):
        """Cuenta el paso y fija el motivo de parada de FR-221, en este
        orden: FIN_PARTIDA, LLEGADA, DANIO, ENEMIGOS. Devuelve el motivo, o
        None si el viaje sigue.

        - Daño: durante un viaje nada cura al jugador (curar es una acción
          suya), así que bajar la vida es haber recibido daño.
        - Enemigos: los que había al entrar (`partida.enemigos_al_entrar`),
          no los que llegan después (HU3-16)."""
        self.pasos += 1

        if partida.terminada:
            self.detener(FIN_PARTIDA)
        elif partida.sala_actual() is self.destino:
            self.detener(LLEGADA)
        elif partida.jugador.vida < vida_antes:
            self.detener(DANIO)
        elif partida.enemigos_al_entrar > 0:
            self.detener(ENEMIGOS)

        return self.motivo

    def detener(self, motivo, detalle=None):
        self.motivo = motivo
        self.detalle = detalle
