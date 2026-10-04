from crypta.Modelo.Actor import Actor


class Rastreador(Actor):

    def __init__(
        self,
        nombre,
        velocidad,
        sala_actual=None
    ):
        super().__init__(
            nombre,
            velocidad
        )

        self.sala_actual = sala_actual

    def decidir_destino(
        self,
        mapa,
        rastro,
        reloj_actual
    ):
        sala = mapa.obtener_sala(
            self.sala_actual
        )

        if sala is None:
            return None

        mejor_destino = None
        mejor_tiempo = None

        # Solo examinamos las salidas de
        # la sala donde está el rastreador.
        for puerta in sala.salidas.values():
            id_destino = puerta.sala_destino

            huella = rastro.obtener_reciente(
                id_destino,
                reloj_actual
            )

            if huella is None:
                continue

            if (
                mejor_tiempo is None
                or huella.tiempo > mejor_tiempo
            ):
                mejor_tiempo = huella.tiempo
                mejor_destino = id_destino

        return mejor_destino