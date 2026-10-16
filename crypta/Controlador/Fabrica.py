"""Una sola manera de crear una Partida nueva.

La usan el juego (main.crear_partida) y la reproducción (PreparadorReplay).
Si cada uno armara la Partida a su manera, bastaría una diferencia mínima
(otro orden de parámetros, otra sala inicial) para que el --replay diera
otra partida. Con una sola función eso no puede pasar.
"""

from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Partida import Partida


def nueva_partida(datos_cripta, mapa, fichas, semilla, nombre_jugador):
   
    estadisticas = datos_cripta["jugador"]

    jugador = Jugador(
        nombre=nombre_jugador,
        vida_max=estadisticas["vida_max"],
        ataque=estadisticas["ataque"],
        defensa=estadisticas["defensa"],
        velocidad=estadisticas["velocidad"],
        inventario_max=datos_cripta["inventario_max"]
    )

    return Partida(
        mapa=mapa,
        jugador=jugador,
        id_sala_inicial=datos_cripta["sala_inicial"],
        fichas=fichas,
        semilla=semilla,
        id_sala_salida=datos_cripta["sala_salida"],
        llave_salida=datos_cripta["llave_salida"]
    )