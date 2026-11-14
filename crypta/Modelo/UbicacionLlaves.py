"""Lectura y validación de la ubicación de las llaves (capacidad 003,
research D2 y D7; FR-319; contracts/datos-servicio.md).

La respuesta de GET /criptas/<id>/llaves (de la red o de la copia local) es
un `dict` de `json`: aquí solo se lee y se traduce a un `Vector` de
`UbicacionLlave` (principio I). Se valida entera antes de devolver nada;
la primera entrada inválida lanza `DatosInvalidos`, como los costos de la
001: con datos inválidos la partida no inicia, ni con --forzar.
"""

from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.estructuras.Vector import Vector


PREFIJO = "la ubicación de llaves tiene un dato inválido"


class UbicacionLlave:
    """Una entrada de la ubicación: la llave `id_llave` está en la sala
    `id_sala` (índice denso `indice_sala` del `Mapa`), en el campo `suelta`
    del enemigo `enemigo` si no es None (FR-304). `numero_llave` lo llena
    la verificación con la numeración de la cripta (research D1)."""

    __slots__ = ("id_llave", "id_sala", "indice_sala", "enemigo",
                 "numero_llave")

    def __init__(self, id_llave, id_sala, indice_sala, enemigo=None):
        self.id_llave = id_llave
        self.id_sala = id_sala
        self.indice_sala = indice_sala
        self.enemigo = enemigo
        self.numero_llave = None


def _invalido(problema):
    return DatosInvalidos(f"{PREFIJO}: {problema}")


def _es_texto_no_vacio(valor):
    return isinstance(valor, str) and valor != ""


def _es_entero(valor):
    # bool es subclase de int en Python; JSON no lo trata como número.
    return isinstance(valor, int) and not isinstance(valor, bool)


def leer_ubicaciones(respuesta, mapa):
    """`Vector` de `UbicacionLlave` en el orden de la respuesta, o
    `DatosInvalidos` con la entrada (desde 1), el id si lo tiene y el
    problema. Cuesta O(L log V)."""
    if not isinstance(respuesta, dict) or not isinstance(
            respuesta.get("llaves"), list):
        raise _invalido("la respuesta no trae la lista «llaves»")

    entradas = respuesta["llaves"]
    ubicaciones = Vector(max(1, len(entradas)))

    for posicion, entrada in enumerate(entradas, start=1):
        if not isinstance(entrada, dict):
            raise _invalido(f"entrada {posicion}: no es un objeto")

        id_llave = entrada.get("id")

        if not _es_texto_no_vacio(id_llave):
            raise _invalido(
                f"entrada {posicion}: el id debe ser un texto no vacío "
                f"(trae {id_llave!r})")

        nombre = f"entrada {posicion} ({id_llave})"

        if "sala" not in entrada:
            raise _invalido(f"{nombre}: no trae sala")

        id_sala = entrada["sala"]

        if not _es_entero(id_sala):
            raise _invalido(
                f"{nombre}: la sala debe ser un entero (trae {id_sala!r})")

        sala = mapa.obtener_sala(id_sala)

        if sala is None:
            raise _invalido(
                f"{nombre}: la sala {id_sala} no existe en el esqueleto")

        enemigo = entrada.get("enemigo")

        if enemigo is not None and not isinstance(enemigo, str):
            raise _invalido(
                f"{nombre}: el enemigo debe ser un texto (trae {enemigo!r})")

        ubicaciones.agregar(
            UbicacionLlave(id_llave, id_sala, sala.indice, enemigo))

    return ubicaciones
