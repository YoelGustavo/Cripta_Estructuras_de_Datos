"""Tercera revisión rápida: el paso 11 (salidas sin dict) y lo que lo rodea.

Póngalo en tests/ y córralo igual que los otros:
    python -m tests.revision_rapida_3

Esta vez las fuentes falsas son ESTRICTAS (como el servidor real): si se
piden más de 10 salas o ids repetidos, fallan. Así se detecta también un
cambio aplicado a medias. Imprime OK o FALLA.
"""

import ast
import os
import tempfile

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.GestorCripta import GestorCripta
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Rastreador import Rastreador


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sala(numero, **salidas):
    return {"id": numero, "nombre": f"Sala {numero}",
            "salidas": {d: (v if isinstance(v, dict) else {"sala": v}) for d, v in salidas.items()}}


def mapa_de(*salas):
    mapa = Mapa()
    mapa.cargar_desde_json(list(salas))
    return mapa


def linea(cantidad):
    return [sala(n, **({"E": n + 1} if n < cantidad else {}), **({"O": n - 1} if n > 1 else {}))
            for n in range(1, cantidad + 1)]


def revisar_lote(ids, operacion):
    lista = list(ids)
    if len(lista) > 10:
        raise ValueError(f"{operacion}: {len(lista)} ids (máximo 10)")
    if len(set(lista)) != len(lista):
        raise ValueError(f"{operacion}: ids repetidos {lista}")
    return lista


class FuenteEstricta:
    def __init__(self, salas=None, catalogo=None):
        self.salas = salas or []
        self.catalogo = catalogo or {}
        self.pedidos = []

    def obtener_cripta(self, cripta_id):
        self.pedidos.append("general")
        return {"id": cripta_id, "version": "v1", "paginas": 1, "salas_total": len(self.salas)}

    def obtener_pagina_salas(self, cripta_id, pagina):
        self.pedidos.append("pagina")
        return {"pagina": pagina, "total_paginas": 1, "salas": self.salas}

    def obtener_contenido(self, cripta_id, ids):
        lista = revisar_lote(ids, "contenido")
        self.pedidos.append(("contenido", tuple(lista)))
        return {"contenido": [{"sala": i, "enemigos": [], "objetos": [], "trampas": []} for i in lista]}

    def obtener_catalogo(self, ids):
        lista = revisar_lote(ids, "catálogo")
        self.pedidos.append(("catalogo", tuple(lista)))
        return {"entidades": [self.catalogo[i] for i in lista if i in self.catalogo]}


# ----------------------------------------------------------------------

def caso_sin_dict_ni_set():
    """§7: sin dict ni set como estructura en Modelo, estructuras y Controlador."""
    hallados = []
    for capa in ("Modelo", "estructuras", "Controlador"):
        carpeta = os.path.join(RAIZ, "crypta", capa)
        for nombre in sorted(os.listdir(carpeta)):
            if not nombre.endswith(".py"):
                continue
            ruta = os.path.join(carpeta, nombre)
            with open(ruta, encoding="utf-8") as archivo:
                arbol = ast.parse(archivo.read())
            for nodo in ast.walk(arbol):
                es_llamada = (isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
                              and nodo.func.id in ("dict", "set"))
                if isinstance(nodo, (ast.Dict, ast.DictComp, ast.Set, ast.SetComp)) or es_llamada:
                    hallados.append(f"{capa}/{nombre}:{nodo.lineno}")
    return hallados == [], "quedan dict/set en " + ", ".join(hallados)


def caso_vecinas_en_orden_fijo():
    """§2.8: el orden de las salidas no puede depender del orden del JSON."""
    a = mapa_de({"id": 1, "nombre": "x", "salidas": {"O": {"sala": 4}, "N": {"sala": 2}, "E": {"sala": 3}}},
                sala(2), sala(3), sala(4))
    b = mapa_de({"id": 1, "nombre": "x", "salidas": {"E": {"sala": 3}, "O": {"sala": 4}, "N": {"sala": 2}}},
                sala(2), sala(3), sala(4))
    orden_a = [a.obtener_vecinas(1).obtener(i).id for i in range(3)]
    orden_b = [b.obtener_vecinas(1).obtener(i).id for i in range(3)]
    return orden_a == orden_b == [2, 3, 4], f"{orden_a} y {orden_b} (debía ser N, E, O = [2, 3, 4])"


def caso_direccion_invalida():
    """Una dirección que no es N, S, E u O es un error de datos y debe avisarse."""
    try:
        mapa_de({"id": 1, "nombre": "x", "salidas": {"NE": {"sala": 2}}}, sala(2))
    except ValueError:
        pass
    except Exception as error:
        return False, f"se cae con {type(error).__name__} en vez de un ValueError claro: {error}"
    else:
        return False, "aceptó la dirección 'NE' sin avisar"
    mapa = mapa_de(sala(1, N=2), sala(2, S=1))
    return mapa.obtener_sala(1).obtener_puerta("X") is None, "obtener_puerta('X') debería dar None"


def caso_rastreador_puerta_cerrada_y_orden():
    """§2.9: solo salidas abiertas y el mismo resultado sin importar el JSON."""
    cerrada = {"sala": 9, "cerrada": True, "llave": "itm_llave"}
    for salidas in ({"N": cerrada, "S": {"sala": 3}}, {"S": {"sala": 3}, "N": cerrada}):
        mapa = mapa_de({"id": 5, "nombre": "x", "salidas": salidas}, sala(9, S=5), sala(3, N=5))
        mapa.obtener_sala(3).registrar_rastro(200)
        mapa.obtener_sala(9).registrar_rastro(300)
        destino = Rastreador("rata", 150, sala_actual=5).decidir_destino(mapa, None, 350)
        if destino != 3:
            return False, f"eligió {destino} con las salidas en el orden {list(salidas)}"
    return True, ""


def caso_persistir_y_recargar():
    """§4.4: el esqueleto se puede persistir y volver a cargar sin pedirlo otra vez."""
    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteEstricta(salas=[sala(1, N={"sala": 2, "cerrada": True, "llave": "k"}), sala(2, S=1)])
        gestor = GestorCripta(fuente, AlmacenDisco(carpeta))
        datos, mapa, _ = gestor.cargar("c1")
        mapa.obtener_sala(1).obtener_puerta("N").abrir()    # el jugador la abre
        try:
            gestor.persistir("c1", datos, mapa)
        except Exception as error:
            return False, f"persistir se cae: {type(error).__name__}: {error}"
        otro = GestorCripta(fuente, AlmacenDisco(carpeta))
        antes = fuente.pedidos.count("pagina")
        _, mapa2, de_disco = otro.cargar("c1")
        if not de_disco or fuente.pedidos.count("pagina") != antes:
            return False, "volvió a descargar el esqueleto"
        puerta = mapa2.obtener_sala(2).obtener_puerta("S")
        if not puerta.esta_cerrada():
            return False, "se guardó la puerta ABIERTA por el jugador: debía guardarse la cripta original"
        mapa2.obtener_sala(1).obtener_puerta("N").abrir()
        return not puerta.esta_cerrada(), "al recargar, las dos mitades de la puerta ya no se comparten"


def caso_precarga_anticipada_lotes_validos():
    """§3.4/§4.2: el servidor acepta hasta 10 salas DISTINTAS por solicitud."""
    fuente = FuenteEstricta()
    gestor = GestorContenido(fuente, mapa_de(*linea(30)), "c1")
    try:
        gestor.precargar_async(1)
        gestor.garantizar_sala(1)
        gestor.precargar_async(5)
        gestor.garantizar_sala(11)
    except Exception as error:
        return False, f"se cae: {type(error).__name__}: {error}"
    finally:
        gestor._ejecutor.shutdown(wait=True)
    lotes = [p[1] for p in fuente.pedidos if p[0] == "contenido"]
    return lotes == [tuple(range(1, 11)), tuple(range(11, 21))], f"lotes pedidos: {lotes}"


def caso_fichas_a_disco():
    """§4.4: lo que llega por red se guarda en disco; la próxima ejecución no lo pide."""
    catalogo = {"itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga"}}
    with tempfile.TemporaryDirectory() as carpeta:
        fuente = FuenteEstricta(catalogo=catalogo)
        try:
            RepositorioFichas(fuente, AlmacenDisco(carpeta), "cat-1").resolver_contenidos(
                [{"sala": 1, "objetos": ["itm_daga"]}])
        except Exception as error:
            return False, f"se cae al guardar en disco: {type(error).__name__}: {error}"
        antes = len(fuente.pedidos)
        RepositorioFichas(fuente, AlmacenDisco(carpeta), "cat-1").resolver_contenidos(
            [{"sala": 1, "objetos": ["itm_daga"]}])
        return len(fuente.pedidos) == antes, "la segunda vez volvió a pedir la ficha por red"


CASOS = [
    ("7   sin dict ni set en Modelo/estructuras/Controlador", caso_sin_dict_ni_set),
    ("2.8 vecinas en orden N, S, E, O", caso_vecinas_en_orden_fijo),
    ("3.3 dirección inválida en el JSON", caso_direccion_invalida),
    ("2.9 rastreador: puerta cerrada y orden del JSON", caso_rastreador_puerta_cerrada_y_orden),
    ("4.4 persistir el esqueleto y recargarlo", caso_persistir_y_recargar),
    ("4.2 precarga anticipada con lotes válidos", caso_precarga_anticipada_lotes_validos),
    ("4.4 fichas guardadas en disco", caso_fichas_a_disco),
]


def main():
    fallas = 0
    for nombre, caso in CASOS:
        try:
            bien, detalle = caso()
        except Exception as error:
            bien, detalle = False, f"se cae: {type(error).__name__}: {error}"
        print(f"{'OK   ' if bien else 'FALLA'}  {nombre}" + ("" if bien else f"\n         -> {detalle}"))
        fallas += 0 if bien else 1
    print(f"\n{len(CASOS) - fallas} de {len(CASOS)} casos bien")


if __name__ == "__main__":
    main()
