from crypta.Modelo.Actor import Actor


VIGENCIA_RASTRO = 400


def sala_con_rastro_mas_fresco(sala, reloj_actual):

    mejor = None
    mejor_tiempo = None

    puertas = sala.puertas(solo_abiertas=True)

    for i in range(len(puertas)):
        vecina = puertas.obtener(i).sala_destino_ref

        if vecina is None:
            continue

        tiempo = vecina.obtener_rastro()

        if tiempo is None:
            continue

        if reloj_actual - tiempo >= VIGENCIA_RASTRO:
            continue

        if (
            mejor is None
            or tiempo > mejor_tiempo
            or (tiempo == mejor_tiempo and vecina.id < mejor.id)
        ):
            mejor = vecina
            mejor_tiempo = tiempo

    return mejor


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

        destino = sala_con_rastro_mas_fresco(sala, reloj_actual)

        if destino is None:
            return None

        return destino.id