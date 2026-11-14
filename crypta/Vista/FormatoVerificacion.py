"""Texto del resultado de la verificación (capacidad 003; research D10;
contracts/reporte.md).

Función pura: no guarda estado ni escribe nada; la usan `--verificar`, el
inicio de partida y la comparación del bench. Recorre vectores que ya
vienen ordenados, así que el texto es el mismo byte por byte en cada
ejecución (FR-320, SC-305). Sin «→»: la flecha es «->».

El texto no termina en salto de línea; quien lo imprime lo agrega.
"""

from crypta.estructuras.Vector import Vector


ENCABEZADO = "Verificación de resolubilidad: "


def _unir(vector, separador=", "):
    return separador.join(vector.obtener(i) for i in range(len(vector)))


def _texto_resoluble(resultado):
    """FR-306: solo los ids, agrupados por ronda, en el orden de las
    rondas (FR-308)."""
    lineas = Vector()
    lineas.agregar(ENCABEZADO + "la cripta es resoluble.")
    lineas.agregar("Orden de llaves:")

    for i in range(len(resultado.rondas)):
        lineas.agregar(f"  Ronda {i + 1}: {_unir(resultado.rondas.obtener(i))}")

    return lineas


def _seccion(lineas, titulo, elementos):
    lineas.agregar(titulo)

    if len(elementos) == 0:
        lineas.agregar("  (ninguna)")
        return

    for i in range(len(elementos)):
        lineas.agregar(f"  {elementos.obtener(i)}")


def _texto_no_resoluble(resultado):
    """Por ahora el resultado y las llaves no obtenibles (FR-309); las demás
    partes del reporte (FR-310 a FR-318) llegan con la historia 2."""
    reporte = resultado.reporte
    lineas = Vector()
    lineas.agregar(ENCABEZADO + "la cripta NO es resoluble.")
    _seccion(lineas, "Llaves que no se pueden obtener:", reporte.no_obtenibles)
    return lineas


def texto_resultado(resultado):
    """El texto de un `ResultadoVerificacion`, según contracts/reporte.md."""
    if resultado.resoluble:
        lineas = _texto_resoluble(resultado)
    else:
        lineas = _texto_no_resoluble(resultado)

    return _unir(lineas, "\n")
