from crypta.Modelo.Actor import Actor


# §2.9: un rastro de 400 unidades o más de antigüedad ya no sirve.
VIGENCIA_RASTRO = 400


def sala_con_rastro_mas_fresco(sala, reloj_actual):
    """La decisión del rastreador (§2.9), sin depender de quién la pide.

    Mira SOLO las salas vecinas por salidas abiertas (los enemigos no
    abren puertas, §2.5), siempre en el mismo orden N, S, E, O, y devuelve
    la que tenga el rastro más reciente, si es fresco (menos de 400 de
    antigüedad). Empate: la de menor id. Si ninguna sirve, None (espera).

    Costo: a lo sumo 4 salidas. No depende del tamaño de la cripta ni de
    lo largo del recorrido del jugador (§4.7). La caducidad se detecta al
    consultar: no hay que borrar rastros viejos.
    """
    mejor = None
    mejor_tiempo = None

    puertas = sala.puertas(solo_abiertas=True)

    for i in range(len(puertas)):
        vecina = puertas.obtener(i).sala_destino_ref

        if vecina is None:
            continue

        tiempo = vecina.obtener_rastro()

        # El jugador nunca estuvo allí.
        if tiempo is None:
            continue

        # Una huella de 400 o más ya no sirve.
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
    """Versión anterior (un actor aparte). La partida ya no la usa: usa
    sala_con_rastro_mas_fresco con sus enemigos. Se deja porque la usan
    las revisiones rápidas; se puede quitar en la limpieza final."""

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
        """Id de la sala a la que se mueve, o None si espera."""
        sala = mapa.obtener_sala(
            self.sala_actual
        )

        if sala is None:
            return None

        destino = sala_con_rastro_mas_fresco(sala, reloj_actual)

        if destino is None:
            return None

        return destino.id