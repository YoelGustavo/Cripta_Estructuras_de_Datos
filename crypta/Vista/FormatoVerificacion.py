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
FLECHA = " -> "


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


def _seccion(lineas, titulo, elementos, formato):
    """Título y una línea por elemento; «(ninguna)» si no hay elementos."""
    lineas.agregar(titulo)

    if len(elementos) == 0:
        lineas.agregar("  (ninguna)")
        return

    for i in range(len(elementos)):
        lineas.agregar("  " + formato(elementos.obtener(i)))


def _puerta(puerta):
    return (f"sala {puerta.id_origen}, {puerta.direccion} -> "
            f"sala {puerta.id_destino}, pide {puerta.llave}")


def _ubicaciones(par):
    llave, lugares = par

    if len(lugares) == 0:
        return f"{llave}: no está en la cripta"

    textos = Vector(len(lugares))

    for i in range(len(lugares)):
        id_sala, enemigo = lugares.obtener(i)
        textos.agregar(f"sala {id_sala}" if enemigo is None
                       else f"sala {id_sala} (la suelta {enemigo})")

    return f"{llave}: {_unir(textos)}"


def _dependencia(dependencia):
    if dependencia.depende_de is not None:
        return f"{dependencia.llave} depende de {dependencia.depende_de}"

    return f"{dependencia.llave} no depende de ninguna: {dependencia.motivo}"


def _ciclo(ciclo):
    return _unir(ciclo, FLECHA) + FLECHA + ciclo.obtener(0)


def _texto_no_resoluble(resultado):
    """Las partes del reporte en el orden de FR-316."""
    reporte = resultado.reporte
    lineas = Vector()
    lineas.agregar(ENCABEZADO + "la cripta NO es resoluble.")
    _seccion(lineas, "Llaves que no se pueden obtener:", reporte.no_obtenibles,
             str)
    _seccion(lineas, "Frontera bloqueada:", reporte.frontera, _puerta)
    _seccion(lineas, "Dónde están las llaves de la frontera:",
             reporte.ubicaciones_frontera, _ubicaciones)
    _seccion(lineas, "Dependencias:", reporte.dependencias, _dependencia)
    _seccion(lineas, "Ciclos de dependencia:", reporte.ciclos, _ciclo)

    if reporte.falta_sala_salida:
        lineas.agregar("Falta sala_salida en la cripta.")

    if reporte.falta_llave_salida:
        lineas.agregar("Falta llave_salida en la cripta.")

    if reporte.salida_sin_puerta:
        lineas.agregar(
            f"Se puede obtener {reporte.llave_salida}, pero ninguna puerta "
            f"que la pide lleva a la sala {reporte.sala_salida} desde la "
            f"región alcanzable.")

    return lineas


def texto_resultado(resultado):
    """El texto de un `ResultadoVerificacion`, según contracts/reporte.md."""
    if resultado.resoluble:
        lineas = _texto_resoluble(resultado)
    else:
        lineas = _texto_no_resoluble(resultado)

    return _unir(lineas, "\n")
