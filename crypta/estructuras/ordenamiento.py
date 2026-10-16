"""
Todos ordenan EN SU LUGAR (modifican el vector que reciben) y aceptan una
función 'clave' que dice por qué campo ordenar, por ejemplo:

    ordenar(vista, clave=lambda objeto: objeto.peso)

USADOS POR EL JUEGO (el selector elige entre estos dos):
    insercion  -> estable, sin memoria extra, O(n) si está casi ordenado, O(n²) peor caso
    mergesort  -> estable, O(n log n) siempre, usa un vector auxiliar de tamaño n
    ordenar    -> el selector automático
"""

from crypta.estructuras.MonticuloMin import MonticuloMin
from crypta.estructuras.Vector import Vector


UMBRAL_PEQUENO = 24
UMBRAL_PEQUENO_COSTOSA = 16
FRACCION_CASI_ORDENADO = 0.05

# Fase 8 (lo midió el --bench): en un descenso, si el elemento es menor que
# el que está esta cantidad de lugares ANTES, inserción tiene que correrlo
# lejos: ya no es "casi ordenado" aunque haya pocos descensos.
DISTANCIA_CASI_ORDENADO = 8


def _identidad(x):
    return x


def copiar_a_vector(iterable):
    #copia distintos TDAs a un vector para ordenarlos.
    copia = Vector()
    for x in iterable:
        copia.agregar(x)
    return copia


def contar_descensos(vector, clave=None):
    """Cuántas veces un elemento es MAYOR que el siguiente. O(n).

    0 = ya ordenado; n - 1 = ordenado al revés. Es la medida de
    "qué tan desordenado está" que usa el selector.
    """
    if clave is None:
        clave = _identidad
    descensos = 0
    for i in range(len(vector) - 1):
        if clave(vector.obtener(i + 1)) < clave(vector.obtener(i)):
            descensos += 1
    return descensos


def esta_ordenado(vector, clave=None):
    return contar_descensos(vector, clave) == 0

def insercion(vector, clave=None):
    if clave is None:
        clave = _identidad
    for i in range(1, len(vector)):
        actual = vector.obtener(i)
        k = clave(actual)         
        j = i - 1
        while j >= 0 and clave(vector.obtener(j)) > k:
            vector.asignar(j + 1, vector.obtener(j))
            j -= 1
        vector.asignar(j + 1, actual)

def mergesort(vector, clave=None):
    if clave is None:
        clave = _identidad
    n = len(vector)
    if n <= 1:
        return
    aux = Vector(n)
    for _ in range(n):
        aux.agregar(None)  # n casillas listas para usar con asignar
    _mergesort_rango(vector, aux, 0, n, clave)


def _mergesort_rango(vector, aux, ini, fin, clave):
    # Ordena vector[ini:fin] (ini incluido, fin excluido)
    if fin - ini <= 1:
        return  # 0 o 1 elementos: ya está ordenado
    medio = (ini + fin) // 2
    _mergesort_rango(vector, aux, ini, medio, clave)
    _mergesort_rango(vector, aux, medio, fin, clave)
    _mezclar(vector, aux, ini, medio, fin, clave)


def _mezclar(vector, aux, ini, medio, fin, clave):
    # Mezcla dos mitades YA ORDENADAS: [ini, medio) y [medio, fin).
    # Dos "dedos": i recorre la izquierda, j la derecha; k escribe en aux.
    i, j, k = ini, medio, ini
    while i < medio and j < fin:
        izq = vector.obtener(i)
        der = vector.obtener(j)
        # '<=': en un empate se toma el de la IZQUIERDA, que iba primero
        # en el orden original. Eso hace al mergesort ESTABLE.
        if clave(izq) <= clave(der):
            aux.asignar(k, izq)
            i += 1
        else:
            aux.asignar(k, der)
            j += 1
        k += 1
    # Una de las dos mitades se acabó: se copia lo que sobre de la otra.
    while i < medio:
        aux.asignar(k, vector.obtener(i))
        i += 1
        k += 1
    while j < fin:
        aux.asignar(k, vector.obtener(j))
        j += 1
        k += 1
    # El resultado quedó en aux: se devuelve al vector original.
    for p in range(ini, fin):
        vector.asignar(p, aux.obtener(p))


def elegir_algoritmo(vector, clave=None, comparacion_costosa=False):
    """
    - Tamaño: con pocos elementos, inserción gana (casi no hace trabajo extra).
    - Desorden (descensos): si está casi ordenado, inserción es O(n).
    - Comparaciones costosas (dato que da quien llama, p. ej. ordenar por
      nombre): mergesort hace menos comparaciones, así que inserción solo
      conviene en tamaños aún más pequeños.

    Contar descensos no alcanza: "dos bloques ordenados" (p. ej.
    [6,7,8,9,1,2,3,4]) tiene 1 solo descenso, pero a inserción le cuesta
    O(n²) porque cada elemento del segundo bloque viaja lejos. El --bench
    lo midió (1000 elementos: 83 ms contra 5 ms de mergesort). Por eso
    _casi_ordenado revisa también qué tan lejos tiene que ir cada uno.
    """
    n = len(vector)
    umbral = UMBRAL_PEQUENO_COSTOSA if comparacion_costosa else UMBRAL_PEQUENO
    if n <= umbral:
        return "insercion"
    if _casi_ordenado(vector, clave, n):
        return "insercion"
    return "mergesort"


def _casi_ordenado(vector, clave, n):
    """Pocos descensos Y ninguno obliga a correr un elemento lejos. O(n),
    y se detiene apenas sabe que no."""
    if clave is None:
        clave = _identidad
    maximo = n * FRACCION_CASI_ORDENADO
    descensos = 0
    for i in range(n - 1):
        siguiente = clave(vector.obtener(i + 1))
        if siguiente < clave(vector.obtener(i)):
            descensos += 1
            if descensos > maximo:
                return False
            # ¿Tiene que viajar más de DISTANCIA lugares hacia atrás?
            lejos = i + 1 - DISTANCIA_CASI_ORDENADO
            if lejos >= 0 and siguiente < clave(vector.obtener(lejos)):
                return False
    return True


def ordenar(vector, clave=None, comparacion_costosa=False):
    algoritmo = elegir_algoritmo(vector, clave, comparacion_costosa)
    if algoritmo == "insercion":
        insercion(vector, clave)
    else:
        mergesort(vector, clave)
    return algoritmo
