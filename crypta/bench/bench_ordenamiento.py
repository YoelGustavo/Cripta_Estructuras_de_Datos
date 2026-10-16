"""--bench, sección ORDENAMIENTO (§4.9).

§4.9: dos algoritmos con características distintas y un selector que
escoge solo, "sustentado con mediciones propias. Consideren tamaños
pequeños, datos casi ordenados y comparaciones costosas".

El juego tiene inserción (O(n) si ya casi está ordenado, O(n²) si no) y
mergesort (O(n log n) siempre). ordenar() mira el tamaño y cuántos
"descensos" hay (un elemento mayor que el siguiente) y elige. Aquí se
miden los dos en cada caso y se revisa si el selector eligió bien.
"""

import random

from crypta.bench.medicion import cronometrar, formato_tiempo, tabla
from crypta.estructuras.ordenamiento import (
    UMBRAL_PEQUENO,
    UMBRAL_PEQUENO_COSTOSA,
    elegir_algoritmo,
    insercion,
    mergesort,
)
from crypta.estructuras.Vector import Vector


# ======================================================================
# LOS DATOS
# ======================================================================

def generar(patron, n, semilla=1):
    """Una lista de n números con la forma pedida."""
    azar = random.Random(semilla)
    datos = list(range(n))

    if patron == "aleatorio":
        azar.shuffle(datos)
    elif patron == "casi ordenado":
        # Unos pocos vecinos intercambiados (como el índice del guardado o
        # una tabla de puntajes a la que se le agregó uno).
        for _ in range(max(1, n // 50)):
            i = azar.randrange(n - 1)
            datos[i], datos[i + 1] = datos[i + 1], datos[i]
    elif patron == "invertido":
        datos.reverse()
    elif patron == "dos bloques":
        # [mitad de arriba ordenada, mitad de abajo ordenada]: UN solo
        # descenso, pero cada elemento de la segunda mitad tiene que viajar
        # n/2 lugares. El límite conocido del selector.
        datos = datos[n // 2:] + datos[:n // 2]
    else:
        raise ValueError(f"patrón desconocido: {patron}")

    return datos


def _vector(datos):
    vector = Vector(len(datos))
    for x in datos:
        vector.agregar(x)
    return vector


def costo(algoritmo, datos, clave=None, repeticiones=3):
    """El mejor tiempo de ordenar una copia NUEVA de los datos (copiar no
    se mide: el algoritmo ordena en su lugar)."""
    mejor = None

    for _ in range(repeticiones):
        vector = _vector(datos)
        transcurrido = cronometrar(lambda: algoritmo(vector, clave))

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    return mejor


ALGORITMOS = (("insercion", insercion), ("mergesort", mergesort))


def fila(patron, n, clave=None, comparacion_costosa=False, datos=None):
    datos = datos if datos is not None else generar(patron, n)
    tiempos = [costo(funcion, datos, clave) for _, funcion in ALGORITMOS]
    elegido = elegir_algoritmo(_vector(datos), clave, comparacion_costosa)
    tiempo_elegido = tiempos[0] if elegido == "insercion" else tiempos[1]

    # "Bien" = el elegido no tardó más de un 20 % que el más rápido.
    bien = tiempo_elegido <= min(tiempos) * 1.2
    return (patron, str(n), formato_tiempo(tiempos[0]), formato_tiempo(tiempos[1]),
            elegido, "sí" if bien else "NO")


# ======================================================================
# LA SECCIÓN DEL --bench
# ======================================================================

def ejecutar(rapido=False):
    tamanos = (8, 24, 50) if rapido else (8, 24, 50, 200, 1000)
    filas = []

    for patron in ("aleatorio", "casi ordenado", "invertido", "dos bloques"):
        for n in tamanos:
            filas.append(fila(patron, n))

    encabezados = ("datos", "n", "inserción", "mergesort", "ordenar() elige", "¿bien?")
    general = tabla(
        f"ORDENAMIENTO (§4.9): números (comparar es barato). Umbral: hasta "
        f"{UMBRAL_PEQUENO} elementos, inserción",
        encabezados, filas,
        "¿bien? = lo que eligió no tardó más de un 20 % que el más rápido. "
        "'dos bloques': 1 solo descenso, pero O(n²) para inserción (por eso el selector "
        "no puede mirar solo los descensos).")

    # Comparación costosa: ordenar el inventario por nombre (texto en
    # minúsculas), como vista_ordenada("nombre").
    def por_nombre(objeto):
        return objeto["nombre"].lower()

    filas = []
    for n in ((12, 24) if rapido else (8, 16, 24, 50)):
        azar = random.Random(n)
        datos = [{"nombre": f"Objeto número {azar.randrange(10 ** 6):06d}"} for _ in range(n)]
        filas.append(fila("por nombre", n, por_nombre, True, datos))

    costosa = tabla(
        f"ORDENAMIENTO (§4.9): comparación costosa (por nombre). Umbral: hasta "
        f"{UMBRAL_PEQUENO_COSTOSA} elementos, inserción",
        encabezados, filas,
        "Mergesort hace menos comparaciones; cuando comparar cuesta, le gana a "
        "inserción con menos elementos.")

    return general + "\n\n" + costosa


if __name__ == "__main__":
    print(ejecutar())
