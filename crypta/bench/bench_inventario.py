import copy
import sys

from crypta.bench import bench_ciclo
from crypta.bench.medicion import cronometrar, formato_tiempo, medir, tabla
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Inventario import Inventario

def _ficha(i):
    return {"id": f"itm_{i}", "nombre": f"Objeto {i}", "clase": "arma",
            "peso": 1, "valor": 1}


def costo_soltar_lista(cantidad, posicion, vueltas=200):
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
    vector = Vector()
    for i in range(cantidad):
        vector.agregar(_ficha(i))

    def soltar_y_devolver():
        for _ in range(vueltas):
            objeto = vector.quitar(posicion)
            vector.insertar(posicion, objeto)

    return medir(soltar_y_devolver) / vueltas


def costo_deshacer(enemigos, cantidad_salas=100, vueltas=10):
    partida = bench_ciclo.partida_de_carga(enemigos, bench_ciclo.CATALOGO.get,
                                           cantidad_salas=cantidad_salas)
    mejor = None

    for _ in range(vueltas):
        partida.jugador.inventario.fijar_pergaminos(1)
        partida.esperar()
        transcurrido = cronometrar(partida.usar_pergamino)

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    
    limite = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limite, 50000))
    try:
        foto = medir(lambda: copy.deepcopy(partida), repeticiones=2)
    finally:
        sys.setrecursionlimit(limite)

    return mejor, foto


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
