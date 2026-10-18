import gc
import time


def medir(funcion, repeticiones=5):
    
    mejor = None

    for _ in range(repeticiones):
        transcurrido = cronometrar(funcion)

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    return mejor


def cronometrar(funcion):
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
    if segundos < 1e-3:
        return f"{segundos * 1e6:.1f} µs"

    if segundos < 1:
        return f"{segundos * 1e3:.2f} ms"

    return f"{segundos:.2f} s"


def tabla(titulo, encabezados, filas, nota=None):
    
    anchos = [len(e) for e in encabezados]

    for fila in filas:
        for i, celda in enumerate(fila):
            anchos[i] = max(anchos[i], len(celda))

    def linea(celdas):
        partes = [celdas[0].ljust(anchos[0])]
        partes += [c.rjust(anchos[i + 1]) for i, c in enumerate(celdas[1:])]
        return "  " + "   ".join(partes)

    texto = [titulo, linea(encabezados)]
    texto += [linea(fila) for fila in filas]

    if nota:
        texto.append(f"  {nota}")

    return "\n".join(texto)
