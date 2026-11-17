"""Texto del mapa conocido (capacidad 002, FR-210; contracts/vista.md «Mapa»).

Funciones puras sobre un `MapaResumido` (`crypta/Modelo/Resumen.py`); la
vista solo imprime lo que devuelven.

```text
MAPA CONOCIDO (<E> exploradas, <A> avistadas)
Exploradas:
  <id> <nombre>
    <dir>: sala <destino>, costo <costo>, <abierta|cerrada>
Avistadas: <id>, <id>, ... | ninguna
```
"""

from crypta.Modelo.Puerta import CERRADA
from crypta.Modelo.Viaje import (
    DANIO,
    ENEMIGOS,
    FIN_PARTIDA,
    LLEGADA,
    PASO_IMPOSIBLE,
    SIN_RUTA,
)


def lineas_exploradas(mapa_resumido, sangria):
    """Las líneas de las salas exploradas: cada sala con `sangria` y sus
    salidas con dos espacios más. Las salidas ya vienen en orden N, S, E, O.
    Una salida de una sala explorada siempre fue observada (FR-204)."""
    lineas = []
    exploradas = mapa_resumido.exploradas

    for i in range(len(exploradas)):
        sala = exploradas.obtener(i)
        lineas.append(f"{sangria}{sala.id} {sala.nombre}")

        for j in range(len(sala.salidas)):
            direccion, destino, costo, recordada = sala.salidas.obtener(j)
            estado = "cerrada" if recordada == CERRADA else "abierta"
            lineas.append(f"{sangria}  {direccion}: sala {destino}, "
                          f"costo {costo}, {estado}")

    return lineas


def linea_avistadas(mapa_resumido):
    """«Avistadas: 3, 4» o «Avistadas: ninguna». Sin nombres (FR-203)."""
    avistadas = mapa_resumido.avistadas

    if len(avistadas) == 0:
        return "Avistadas: ninguna"

    ids = [str(avistadas.obtener(i)) for i in range(len(avistadas))]
    return "Avistadas: " + ", ".join(ids)


def lineas_mapa(mapa_resumido, sangria):
    """Las líneas del mapa sin encabezado, todas con `sangria` delante de
    las salas y de la línea de avistadas. Las usa el resumen de la 004
    (T037), con `sangria` de dos espacios."""
    return (lineas_exploradas(mapa_resumido, sangria)
            + [sangria + linea_avistadas(mapa_resumido)])


def formatear_mapa(mapa_resumido):
    """El texto del comando `mapa`, terminado en salto de línea."""
    exploradas = len(mapa_resumido.exploradas)
    avistadas = len(mapa_resumido.avistadas)

    lineas = [f"MAPA CONOCIDO ({exploradas} exploradas, {avistadas} avistadas)",
              "Exploradas:"]
    lineas.extend(lineas_exploradas(mapa_resumido, "  "))
    lineas.append(linea_avistadas(mapa_resumido))
    return "\n".join(lineas) + "\n"


def texto_motivo(viaje):
    """Por qué se detuvo un viaje (FR-221; contracts/vista.md «Motivos de
    parada»)."""
    n = viaje.pasos
    destino = viaje.destino.id
    motivo = viaje.motivo

    if motivo == LLEGADA:
        return f"Llegaste a la sala {destino} en {n} pasos."

    if motivo == ENEMIGOS:
        return f"El viaje se detuvo: hay enemigos en esta sala ({n} pasos)."

    if motivo == DANIO:
        return f"El viaje se detuvo: recibiste daño ({n} pasos)."

    if motivo == SIN_RUTA:
        return ("El viaje se detuvo: ya no conoces una ruta abierta hasta la "
                f"sala {destino} ({n} pasos).")

    if motivo == PASO_IMPOSIBLE:
        return ("El viaje se detuvo: no se pudo cargar la sala siguiente "
                f"({n} pasos). {viaje.detalle}")

    if motivo == FIN_PARTIDA:
        return f"El viaje terminó con la partida ({n} pasos)."

    raise ValueError(f"Motivo de parada desconocido: {motivo!r}")
