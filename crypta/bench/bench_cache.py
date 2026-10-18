
import random
import tempfile

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.bench.medicion import formato_tiempo, medir, tabla
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.estructuras.CacheLRU import CacheLRU
from crypta.estructuras.Vector import Vector


class CacheLineal:

    def __init__(self):
        self._ids = Vector()

    def insertar(self, id_tipo, ficha):
        self._ids.agregar(id_tipo)

    def contiene(self, id_tipo):
        for i in range(len(self._ids)):
            if self._ids.obtener(i) == id_tipo:
                return True
        return False


def costo_busqueda(clase, cantidad, busquedas=1000, semilla=1):
    azar = random.Random(semilla)
    ids = [f"itm_{i:05d}" for i in range(cantidad)]
    azar.shuffle(ids)

    cache = clase(cantidad) if clase is CacheLRU else clase()
    for id_tipo in ids:
        cache.insertar(id_tipo, {"id": id_tipo})

    buscadas = [azar.choice(ids) if i % 2 == 0 else f"no_{i}" for i in range(busquedas)]

    def buscar():
        for id_tipo in buscadas:
            cache.contiene(id_tipo)

    return medir(buscar) / busquedas


class _SinRed:
    def obtener_catalogo(self, ids):
        raise AssertionError("la medición no debe usar la red")


def costo_recuperar(cantidad_fichas=200):
    with tempfile.TemporaryDirectory() as carpeta:
        almacen = AlmacenDisco(carpeta)
        fichas = {f"itm_{i}": {"id": f"itm_{i}", "nombre": f"Objeto {i}"}
                  for i in range(cantidad_fichas)}
        almacen.guardar_catalogo("v1", fichas)

        repositorio = RepositorioFichas(_SinRed(), almacen, "v1", cache_size=1)

        def en_memoria():
            repositorio.obtener_ficha("itm_1")

        def desde_disco():
            repositorio.obtener_ficha("itm_0")
            repositorio.obtener_ficha("itm_1")

        memoria = medir(lambda: [en_memoria() for _ in range(200)]) / 200
        disco = medir(lambda: [desde_disco() for _ in range(50)]) / 100
        return memoria, disco


def ejecutar(rapido=False):
    tamanos = (25, 250) if rapido else (25, 250, 2500)
    filas = []

    for cantidad in tamanos:
        filas.append((str(cantidad),
                      formato_tiempo(costo_busqueda(CacheLRU, cantidad)),
                      formato_tiempo(costo_busqueda(CacheLineal, cantidad))))

    busqueda = tabla(
        "CACHÉ (§4.4): ¿está esta ficha en memoria? (una búsqueda)",
        ("fichas en caché", "árbol de búsqueda (el juego)", "recorrer la lista"),
        filas,
        "Árbol: O(log n) en promedio. Lista: O(n). --cache-size es 25 por defecto.")

    memoria, disco = costo_recuperar(50 if rapido else 200)
    recuperar = tabla(
        "CACHÉ (§4.4): obtener una ficha",
        ("dónde estaba", "tiempo"),
        [("en memoria (acierto)", formato_tiempo(memoria)),
         ("liberada, se lee del disco (fallo)", formato_tiempo(disco))],
        "Una ficha liberada nunca vuelve a costar red: solo una lectura de disco.")

    return busqueda + "\n\n" + recuperar


if __name__ == "__main__":
    print(ejecutar())
