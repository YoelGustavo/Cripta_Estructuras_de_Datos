
import random
import tempfile

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.bench.medicion import formato_tiempo, medir, tabla
from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Cola import Cola
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Mapa import Mapa


class BitacoraVector:

    def __init__(self, maximo):
        self._mensajes = Vector(maximo)
        self._maximo = maximo

    def agregar(self, texto):
        if len(self._mensajes) == self._maximo:
            self._mensajes.quitar(0)
        self._mensajes.agregar(texto)

    def __len__(self):
        return len(self._mensajes)


class BitacoraCola:

    def __init__(self, maximo):
        self._mensajes = Cola(capacidad_max=maximo)

    def agregar(self, texto):
        self._mensajes.encolar(texto)

    def __len__(self):
        return len(self._mensajes)


def costo_agregar(clase, maximo, mensajes=5000):
    bitacora = clase(maximo)
    for i in range(maximo):
        bitacora.agregar(f"m{i}")

    def agregar_muchos():
        for i in range(mensajes):
            bitacora.agregar(f"mensaje {i}")

    tiempo = medir(agregar_muchos, repeticiones=3) / mensajes

    if len(bitacora) != maximo:
        raise AssertionError("la bitácora creció")

    return tiempo

TIPOS_ENEMIGO = [f"ent_{i}" for i in range(10)]
TIPOS_OBJETO = [f"itm_{i}" for i in range(15)]
TIPOS_TRAMPA = [f"trp_{i}" for i in range(5)]


def cripta_en_cuadricula(cantidad_salas, semilla=1):
    azar = random.Random(semilla)
    ancho = max(1, int(cantidad_salas ** 0.5))
    salas = []
    contenidos = []

    for i in range(1, cantidad_salas + 1):
        fila, columna = (i - 1) // ancho, (i - 1) % ancho
        salidas = {}
        if columna + 1 < ancho and i + 1 <= cantidad_salas:
            salidas["E"] = {"sala": i + 1}
        if columna > 0:
            salidas["O"] = {"sala": i - 1}
        if i + ancho <= cantidad_salas:
            salidas["S"] = {"sala": i + ancho}
        if fila > 0:
            salidas["N"] = {"sala": i - ancho}
        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})

        contenidos.append({
            "sala": i,
            "enemigos": [{"instancia": f"e-{i}-{k}", "tipo": azar.choice(TIPOS_ENEMIGO)}
                         for k in range(azar.randint(0, 2))],
            "objetos": [azar.choice(TIPOS_OBJETO) for _ in range(azar.randint(0, 3))],
            "trampas": ([{"instancia": f"t-{i}", "tipo": azar.choice(TIPOS_TRAMPA)}]
                        if azar.random() < 0.2 else []),
        })

    return salas, contenidos


class FuenteContada:

    def __init__(self, contenidos):
        self.contenidos = contenidos
        self.solicitudes = 0

    def obtener_contenido(self, cripta_id, salas):
        self.solicitudes += 1
        ids = list(salas)
        return {"contenido": [self.contenidos[i - 1] for i in ids]}

    def obtener_catalogo(self, ids):
        self.solicitudes += 1
        return {"entidades": [{"id": i, "nombre": i, "clase": "objeto"} for i in ids]}


def solicitudes_ingenuas(contenidos):
    vistos = ArbolBusqueda()
    for contenido in contenidos:
        tipos = ([e["tipo"] for e in contenido["enemigos"]] + contenido["objetos"]
                 + [t["tipo"] for t in contenido["trampas"]])
        for tipo in tipos:
            if not vistos.contiene(tipo):
                vistos.insertar(tipo, True)
    return len(contenidos) + len(vistos)


def solicitudes_del_juego(cantidad_salas, carpeta, semilla=1):
    salas, contenidos = cripta_en_cuadricula(cantidad_salas, semilla)
    almacen = AlmacenDisco(carpeta)
    resultados = []

    for vuelta in ("fría", "caliente"):
        fuente = FuenteContada(contenidos)
        mapa = Mapa()
        mapa.cargar_desde_json(salas)

        if vuelta == "caliente":
            mapa.asignar_contenidos(contenidos)

        repositorio = RepositorioFichas(fuente, almacen, "v1")
        gestor = GestorContenido(fuente, mapa, "bench", repositorio)

        for id_sala in range(1, cantidad_salas + 1):
            gestor.garantizar_sala(id_sala)
            gestor.precargar_desde(id_sala)

        gestor.cerrar()
        resultados.append(fuente.solicitudes)

    return resultados[0], resultados[1]


def ejecutar(rapido=False):
    filas = []
    for maximo in ((20,) if rapido else (20, 1000)):
        filas.append((str(maximo),
                      formato_tiempo(costo_agregar(BitacoraCola, maximo)),
                      formato_tiempo(costo_agregar(BitacoraVector, maximo))))

    bitacora = tabla(
        "BITÁCORA (§4.8): agregar UN mensaje con la bitácora llena",
        ("mensajes guardados", "cola con tope (el juego)", "vector (corre a todos)"),
        filas,
        "Con 20 casi no se nota; la cola no corre a nadie y su memoria nunca pasa "
        "del tope (se revisa en cada medición).")

    filas = []
    for cantidad in ((25, 100) if rapido else (25, 100, 400)):
        _, contenidos = cripta_en_cuadricula(cantidad)
        with tempfile.TemporaryDirectory() as carpeta:
            fria, caliente = solicitudes_del_juego(cantidad, carpeta)
        filas.append((str(cantidad), str(solicitudes_ingenuas(contenidos)),
                      str(fria), str(caliente)))

    red = tabla(
        "RED (§4.2 y §5.1): solicitudes para recorrer TODA la cripta "
        "(contenido + fichas)",
        ("salas", "ingenuo (1 por sala y por ficha)", "el juego, caché vacía",
         "el juego, caché caliente"),
        filas,
        "Lotes de 10 salas y de 10 fichas, precarga por cercanía y caché en disco. "
        "Sin contar los datos generales y el esqueleto (iguales en todos). Límite: "
        "la precarga revisa como máximo 100 salas alrededor (para no pasarse del "
        "tiempo del turno, §5.2); en una cripta grande ya casi toda cargada, "
        "encuentra pocas salas nuevas por vez y los lotes salen chicos.")

    return bitacora + "\n\n" + red


if __name__ == "__main__":
    print(ejecutar())
