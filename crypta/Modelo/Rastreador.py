from crypta.Modelo.Actor import Actor


VIGENCIA_RASTRO = 400


def sala_con_rastro_mas_fresco(sala, reloj_actual):
    """La sala vecina con el rastro más fresco, o None (P1 §2.9)."""
    puerta = salida_con_rastro_mas_fresco(sala, reloj_actual)

    if puerta is None:
        return None

    return puerta.sala_destino_ref


def salida_con_rastro_mas_fresco(sala, reloj_actual):
    """La salida abierta que lleva a la sala vecina con el rastro más
    fresco, o None. Misma regla y mismo orden que en P1; devuelve la puerta
    para que el movimiento tarde su costo (FR-004, FR-006)."""
    mejor = None
    mejor_puerta = None
    mejor_tiempo = None

    puertas = sala.puertas(solo_abiertas=True)

    for i in range(len(puertas)):
        puerta = puertas.obtener(i)
        vecina = puerta.sala_destino_ref

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
            mejor_puerta = puerta
            mejor_tiempo = tiempo

    return mejor_puerta


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