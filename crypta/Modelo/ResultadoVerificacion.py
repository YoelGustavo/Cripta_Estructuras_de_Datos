"""Resultado de la verificación de resolubilidad (capacidad 003,
data-model.md). Solo datos, sin lógica.

Nada de esto es estado del juego (FR-327): no se guarda, no va a
`partida.log` y el pergamino no lo toca. Todas las colecciones son `Vector`
y ya vienen en el orden en que se muestran (contracts/reporte.md).
"""

from crypta.estructuras.Vector import Vector


# Motivos de «no depende de ninguna» (FR-312, FR-314).
NO_ESTA_EN_LA_CRIPTA = "no está en la cripta"
SALA_INALCANZABLE = "su sala no se alcanza ni abriendo todas las puertas"


class ResultadoVerificacion:
    """`resoluble`; `rondas`: `Vector` de rondas, cada una un `Vector` de ids
    ordenados (FR-306, FR-308); `reporte`: `Reporte` si no es resoluble,
    si no None."""

    __slots__ = ("resoluble", "rondas", "reporte")

    def __init__(self, resoluble, rondas=None, reporte=None):
        self.resoluble = resoluble
        self.rondas = rondas if rondas is not None else Vector()
        self.reporte = reporte


class Reporte:
    """Partes del reporte de una cripta no resoluble, en el orden de FR-316.

    - `no_obtenibles`: ids por id (FR-309).
    - `frontera`: `PuertaFrontera` por (id de origen, N S E O) (FR-310).
    - `ubicaciones_frontera`: pares (id de llave, `Vector` de pares
      (id de sala, enemigo o None)), por id de llave; un vector vacío
      significa que la llave no está en la cripta (FR-311).
    - `dependencias`: `Dependencia` por id de llave (FR-312, FR-314).
    - `ciclos`: `Vector` de ciclos, cada uno un `Vector` de ids que empieza
      en su menor id, ordenados por esa llave (FR-315).
    - `falta_sala_salida`, `falta_llave_salida` (FR-318).
    - `salida_sin_puerta`: `llave_salida` es obtenible pero ninguna puerta
      que la pide lleva a `sala_salida` desde la región (FR-317); para el
      texto, `llave_salida` y `sala_salida` son los de la cripta.
    """

    __slots__ = ("no_obtenibles", "frontera", "ubicaciones_frontera",
                 "dependencias", "ciclos", "falta_sala_salida",
                 "falta_llave_salida", "salida_sin_puerta", "llave_salida",
                 "sala_salida")

    def __init__(self):
        self.no_obtenibles = Vector()
        self.frontera = Vector()
        self.ubicaciones_frontera = Vector()
        self.dependencias = Vector()
        self.ciclos = Vector()
        self.falta_sala_salida = False
        self.falta_llave_salida = False
        self.salida_sin_puerta = False
        self.llave_salida = None
        self.sala_salida = None


class PuertaFrontera:
    """Una puerta de la frontera bloqueada (FR-310)."""

    __slots__ = ("id_origen", "direccion", "id_destino", "llave")

    def __init__(self, id_origen, direccion, id_destino, llave):
        self.id_origen = id_origen
        self.direccion = direccion
        self.id_destino = id_destino
        self.llave = llave


class Dependencia:
    """De qué llave depende una llave no obtenible (FR-312, FR-314).

    `depende_de` es un id o None; si es None, `motivo` es
    `NO_ESTA_EN_LA_CRIPTA` o `SALA_INALCANZABLE`."""

    __slots__ = ("llave", "depende_de", "motivo")

    def __init__(self, llave, depende_de=None, motivo=None):
        self.llave = llave
        self.depende_de = depende_de
        self.motivo = motivo


class NoVerificable:
    """No se pudo obtener la ubicación de las llaves (FR-324): sin
    conexión y sin copia local, falla de red o presupuesto agotado. Para
    decidir si la partida inicia cuenta como no resoluble (FR-325), pero el
    código de salida es 1 (FR-329)."""

    __slots__ = ("motivo",)

    def __init__(self, motivo):
        self.motivo = motivo
