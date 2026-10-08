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

        # Solo las puertas ABIERTAS (los enemigos no abren puertas, §2.5),
        # siempre en el mismo orden N, S, E, O. Como mucho son 4: el costo
        # no depende del tamaño de la cripta ni del recorrido (§4.7).
        puertas = sala.puertas(solo_abiertas=True)

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)

            id_destino = puerta.sala_destino
            sala_destino = puerta.sala_destino_ref

            if sala_destino is None:
                continue

            tiempo = sala_destino.obtener_rastro()

            # El jugador nunca estuvo allí.
            if tiempo is None:
                continue

            # Una huella de 400 o más ya no sirve.
            if reloj_actual - tiempo >= 400:
                continue

            if (
                mejor_tiempo is None
                or tiempo > mejor_tiempo
                or (
                    tiempo == mejor_tiempo
                    and id_destino < mejor_destino
                )
            ):
                mejor_tiempo = tiempo
                mejor_destino = id_destino

        return mejor_destino