"""Herramientas comunes del --bench (§5.3): medir tiempos y armar tablas.

Cómo se mide: cada medición se repite varias veces y se toma el MEJOR
tiempo (el menor). El sistema operativo, otros programas o el recolector de
basura de Python solo pueden hacer que una vuelta tarde MÁS, nunca menos:
el mínimo es lo que más se acerca al costo real de la operación. Además,
mientras se mide se apaga el recolector de basura (gc), que si no se mete
en medio de una vuelta cualquiera.
"""

import gc
import time


def medir(funcion, repeticiones=5):
    """Ejecuta funcion() 'repeticiones' veces y devuelve el mejor tiempo,
    en segundos."""
    mejor = None

    for _ in range(repeticiones):
        transcurrido = cronometrar(funcion)

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    return mejor


def cronometrar(funcion):
    """Segundos que tarda UNA llamada a funcion(), sin el recolector de
    basura en medio."""
    activo = gc.isenabled()
    gc.disable()

    try:
        inicio = time.perf_counter()
        funcion()
        return time.perf_counter() - inicio
    finally:
        if activo:
            gc.enable()


def formato_tiempo(segundos):
    """12.3 µs, 4.56 ms o 1.20 s: la unidad que se lea mejor."""
    if segundos < 1e-3:
        return f"{segundos * 1e6:.1f} µs"

    if segundos < 1:
        return f"{segundos * 1e3:.2f} ms"

    return f"{segundos:.2f} s"


def tabla(titulo, encabezados, filas, nota=None):
    """Texto de una tabla con columnas alineadas. 'filas' son tuplas de
    textos, una por fila, en el orden de 'encabezados'."""
    anchos = [len(e) for e in encabezados]

    for fila in filas:
        for i, celda in enumerate(fila):
            anchos[i] = max(anchos[i], len(celda))

    def linea(celdas):
        # La primera columna a la izquierda; los números, a la derecha.
        partes = [celdas[0].ljust(anchos[0])]
        partes += [c.rjust(anchos[i + 1]) for i, c in enumerate(celdas[1:])]
        return "  " + "   ".join(partes)

    texto = [titulo, linea(encabezados)]
    texto += [linea(fila) for fila in filas]

    if nota:
        texto.append(f"  {nota}")

    return "\n".join(texto)
