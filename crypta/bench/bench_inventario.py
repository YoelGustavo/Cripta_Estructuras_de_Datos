"""--bench, secciones INVENTARIO (§4.5) e HISTORIAL (§4.6).

Inventario: §4.5 pide soltar el objeto que se ve "en cualquier posición,
sin que el costo dependa de la posición". El juego usa una ListaDoble (se
quita el nodo); la alternativa descartada es un Vector (quitar corre a
todos los que están después).

Historial: el pergamino deshace la última acción y TODO lo que pasó
después. El juego anota solo los CAMBIOS de cada acción (Pila de Cambio);
la alternativa descartada es sacar una FOTO completa de la partida antes
de cada acción (copy.deepcopy).
"""

import copy
import sys

from crypta.bench import bench_ciclo
from crypta.bench.medicion import cronometrar, formato_tiempo, medir, tabla
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Inventario import Inventario


# ======================================================================
# INVENTARIO
# ======================================================================

def _ficha(i):
    return {"id": f"itm_{i}", "nombre": f"Objeto {i}", "clase": "arma",
            "peso": 1, "valor": 1}


def costo_soltar_lista(cantidad, posicion, vueltas=200):
    """Soltar el objeto de 'posicion' del inventario real (y devolverlo,
    para que el inventario no cambie entre vueltas)."""
    inventario = Inventario(cantidad)
    for i in range(cantidad):
        inventario.recoger(_ficha(i))
    for _ in range(posicion):
        inventario.avanzar()

    def soltar_y_devolver():
        for _ in range(vueltas):
            contexto = inventario.soltar_actual_con_contexto()
            inventario.restaurar_soltado(contexto)

    return medir(soltar_y_devolver) / vueltas


def costo_soltar_vector(cantidad, posicion, vueltas=200):
    """Lo mismo con un Vector: quitar(posicion) e insertar(posicion)."""
    vector = Vector()
    for i in range(cantidad):
        vector.agregar(_ficha(i))

    def soltar_y_devolver():
        for _ in range(vueltas):
            objeto = vector.quitar(posicion)
            vector.insertar(posicion, objeto)

    return medir(soltar_y_devolver) / vueltas


# ======================================================================
# HISTORIAL
# ======================================================================

def costo_deshacer(enemigos, cantidad_salas=100, vueltas=10):
    """(deshacer con el historial, sacar una foto completa): segundos.
    La partida es la de estrés del ciclo: con más enemigos, cada acción
    del jugador arrastra más eventos que hay que deshacer."""
    partida = bench_ciclo.partida_de_carga(enemigos, bench_ciclo.CATALOGO.get,
                                           cantidad_salas=cantidad_salas)
    mejor = None

    for _ in range(vueltas):
        partida.jugador.inventario.fijar_pergaminos(1)
        partida.esperar()                                  # no se mide
        transcurrido = cronometrar(partida.usar_pergamino)

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    # deepcopy recorre los nodos enlazados (listas, árboles) uno dentro de
    # otro: con una partida grande pasa el límite de recursión de Python.
    limite = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limite, 50000))
    try:
        foto = medir(lambda: copy.deepcopy(partida), repeticiones=2)
    finally:
        sys.setrecursionlimit(limite)

    return mejor, foto


# ======================================================================
# LA SECCIÓN DEL --bench
# ======================================================================

def ejecutar(rapido=False):
    tamanos = (10, 100) if rapido else (10, 100, 1000)
    filas = []

    for cantidad in tamanos:
        filas.append((
            str(cantidad),
            formato_tiempo(costo_soltar_lista(cantidad, 0)),
            formato_tiempo(costo_soltar_lista(cantidad, cantidad - 1)),
            formato_tiempo(costo_soltar_vector(cantidad, 0)),
            formato_tiempo(costo_soltar_vector(cantidad, cantidad - 1)),
        ))

    inventario = tabla(
        "INVENTARIO (§4.5): soltar el objeto que se ve (y volver a ponerlo)",
        ("objetos", "lista doble: el 1.º", "lista doble: el último",
         "vector: el 1.º", "vector: el último"),
        filas,
        "Lista doble: igual en cualquier posición, O(1). Vector: soltar el 1.º "
        "corre a todos los demás, O(n).")

    enemigos = (10, 50) if rapido else (10, 100, 300)
    filas = []

    for cantidad in enemigos:
        deshacer, foto = costo_deshacer(cantidad, 25 if rapido else 100)
        filas.append((str(cantidad), formato_tiempo(deshacer), formato_tiempo(foto)))

    historial = tabla(
        "HISTORIAL (§4.6): usar un pergamino (deshacer UNA acción)",
        ("enemigos activos", "anotar los cambios (el juego)",
         "foto completa (deepcopy, solo sacarla)"),
        filas,
        "El historial guarda solo lo que cambió; la foto copia la partida "
        "entera ANTES de cada acción, aunque nunca se use un pergamino.")

    return inventario + "\n\n" + historial


if __name__ == "__main__":
    print(ejecutar())
