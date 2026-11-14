"""Búsqueda binaria propia (capacidad 004, research D5; FR-403).

Sin `bisect` (principio I): la línea de tiempo la usa para ubicar, en el
`Vector` de decisiones ordenado por reloj, la primera decisión con reloj
mayor o igual que el instante pedido.
"""


def primera_no_menor(vector, valor, clave):
    """La primera posición i de `vector` con `clave(vector[i]) >= valor`, o
    `len(vector)` si no hay ninguna.

    `vector` es un `Vector` ordenado de forma no decreciente por `clave`.
    Si hay empates, devuelve la primera posición del grupo. O(log n): llama a
    `clave` a lo sumo ⌈log₂(n + 1)⌉ veces."""
    bajo = 0
    alto = len(vector)

    while bajo < alto:
        medio = (bajo + alto) // 2

        if clave(vector.obtener(medio)) < valor:
            bajo = medio + 1
        else:
            alto = medio

    return bajo
