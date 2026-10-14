"""El MISMO estado de la partida, guardado en JSON (§4.10).

No es el formato del juego: existe para comparar contra el binario el
tamaño en disco y el tiempo de carga (crypta/bench/bench.py). Usa el mismo
recorrido del estado (EstadoPartida); solo cambian el escritor y el lector.

    {"formato": 1,
     "encabezado": {"cripta": ..., "semilla": ...},
     "general":    {"reloj": ..., "jugador": {...}, "agenda": {...}, ...},
     "salas":      [{"id": 1, ...}, {"id": 2, ...}, ...]}

La diferencia que importa: para sacar UNA sala de aquí hay que leer y
decodificar el archivo COMPLETO (json.load no puede saltar a una parte).

Los dict y list de este archivo son SOLO el documento JSON (lo que pide y
da el módulo json, como en AlmacenDisco), no estructuras del juego.
"""

import json
import os

from crypta.Adaptadores.EstadoPartida import (
    ErrorGuardado, armar_partida, escribir_encabezado, escribir_general,
    escribir_sala, evento_suelto, leer_encabezado, leer_general, leer_sala,
    revisar_antes_de_guardar,
)
from crypta.estructuras.Pila import Pila
from crypta.estructuras.Vector import Vector


FORMATO_JSON = 1


def guardar_partida_json(partida, ruta, encabezado):
    revisar_antes_de_guardar(partida, encabezado)

    documento = {"formato": FORMATO_JSON}
    e = EscritorJSON(documento)

    e.empezar_grupo("encabezado")
    escribir_encabezado(e, encabezado)
    e.terminar_grupo()

    e.empezar_grupo("general")
    escribir_general(e, partida)
    e.terminar_grupo()

    salas = partida.mapa.obtener_todas()
    e.empezar_lista("salas", len(salas))

    for i in range(len(salas)):
        e.empezar_grupo(None)
        escribir_sala(e, salas.obtener(i))
        e.terminar_grupo()

    e.terminar_lista()

    # Sin espacios ni sangría: la comparación de tamaño es contra el JSON
    # más chico posible, no contra uno "bonito".
    temporal = ruta + ".tmp"

    with open(temporal, "w", encoding="utf-8") as archivo:
        json.dump(documento, archivo, ensure_ascii=False, separators=(",", ":"))

    os.replace(temporal, ruta)


class ArchivoGuardadoJSON:
    """La misma forma de uso que ArchivoGuardado (el binario), para poder
    medir los dos igual. Aquí abrir YA lee y decodifica todo el archivo."""

    def __init__(self, ruta):
        try:
            with open(ruta, encoding="utf-8") as archivo:
                texto = archivo.read()
        except OSError as error:
            raise ErrorGuardado(f"No se pudo abrir la partida guardada {ruta}: {error}")

        self.tamano = os.path.getsize(ruta)
        self.bytes_leidos = self.tamano

        try:
            self._documento = json.loads(texto)
        except json.JSONDecodeError as error:
            raise ErrorGuardado(f"{ruta} no es un JSON válido: {error}")

        if not isinstance(self._documento, dict) or "formato" not in self._documento:
            raise ErrorGuardado(f"{ruta} no es una partida guardada de CRIPTA")

        if self._documento["formato"] != FORMATO_JSON:
            raise ErrorGuardado(
                f"La partida se guardó con la versión {self._documento['formato']} del "
                f"formato JSON y este programa lee la versión {FORMATO_JSON}"
            )

        l = LectorJSON(self._documento)
        l.empezar_grupo("encabezado")
        self.encabezado = leer_encabezado(l)
        l.terminar_grupo()

    def leer_sala(self, id_sala, fichas):
        """Hay que buscarla en la lista (y el archivo ya se leyó entero)."""
        l = LectorJSON(self._documento)

        for _ in range(l.empezar_lista("salas")):
            l.empezar_grupo(None)

            if l.ver("id") == id_sala:
                leida = leer_sala(l, fichas)

                for i in range(len(leida.referencias)):
                    enemigo, turno, regeneracion = leida.referencias.obtener(i)
                    enemigo.evento_siguiente = evento_suelto(turno, enemigo)
                    enemigo.evento_regeneracion = evento_suelto(regeneracion, enemigo)

                return leida.sala

            l.terminar_grupo()

        raise KeyError(f"La partida guardada no tiene la sala {id_sala}")

    def cargar_partida(self, fichas):
        l = LectorJSON(self._documento)

        l.empezar_grupo("general")
        general = leer_general(l)
        l.terminar_grupo()

        salas = Vector()

        for _ in range(l.empezar_lista("salas")):
            l.empezar_grupo(None)
            salas.agregar(leer_sala(l, fichas))
            l.terminar_grupo()

        l.terminar_lista()

        return armar_partida(self.encabezado, general, salas, fichas)


# ======================================================================
# ESCRITOR Y LECTOR
# ======================================================================

class EscritorJSON:
    """Arma el documento: cada grupo es un objeto JSON y cada lista una
    lista JSON. La Pila guarda dónde se estaba antes de entrar a uno."""

    def __init__(self, documento):
        self._actual = documento
        self._pila = Pila()

    def _poner(self, nombre, valor):
        if isinstance(self._actual, list):
            self._actual.append(valor)
        else:
            self._actual[nombre] = valor

    def entero(self, nombre, valor):
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ValueError(f"'{nombre}' debe ser un entero, no {valor!r}")
        self._poner(nombre, valor)

    def entero_opcional(self, nombre, valor):
        if valor is None:
            self._poner(nombre, None)
        else:
            self.entero(nombre, valor)

    def texto(self, nombre, valor):
        if not isinstance(valor, str):
            raise ValueError(f"'{nombre}' debe ser texto, no {valor!r}")
        self._poner(nombre, valor)

    def texto_opcional(self, nombre, valor):
        if valor is None:
            self._poner(nombre, None)
        else:
            self.texto(nombre, valor)

    def booleano(self, nombre, valor):
        if not isinstance(valor, bool):
            raise ValueError(f"'{nombre}' debe ser True o False, no {valor!r}")
        self._poner(nombre, valor)

    def real_opcional(self, nombre, valor):
        self._poner(nombre, valor)

    def enteros32(self, nombre, valores):
        self._poner(nombre, list(valores))

    def empezar_grupo(self, nombre):
        self._entrar(nombre, {})

    def terminar_grupo(self):
        self._actual = self._pila.desapilar()

    def empezar_lista(self, nombre, cantidad):
        self._entrar(nombre, [])

    def terminar_lista(self):
        self._actual = self._pila.desapilar()

    def _entrar(self, nombre, nuevo):
        self._poner(nombre, nuevo)
        self._pila.apilar(self._actual)
        self._actual = nuevo


class LectorJSON:
    """Recorre el documento con los mismos pasos que el escritor. Si falta
    un dato o no es del tipo esperado, ErrorGuardado."""

    def __init__(self, documento):
        self._actual = documento
        self._indice = 0               # siguiente elemento, si se está en una lista
        self._pila = Pila()

    def ver(self, nombre):
        """Mira un dato del grupo actual sin avanzar."""
        if not isinstance(self._actual, dict) or nombre not in self._actual:
            raise ErrorGuardado(f"Falta '{nombre}' en la partida guardada")
        return self._actual[nombre]

    def _tomar(self, nombre):
        if isinstance(self._actual, list):
            if self._indice >= len(self._actual):
                raise ErrorGuardado("Una lista de la partida guardada está incompleta")
            valor = self._actual[self._indice]
            self._indice += 1
            return valor

        return self.ver(nombre)

    def _de_tipo(self, nombre, valor, tipo, opcional=False):
        if opcional and valor is None:
            return None

        if not isinstance(valor, tipo) or (tipo is int and isinstance(valor, bool)):
            raise ErrorGuardado(f"'{nombre}' tiene un valor inválido: {valor!r}")

        return valor

    def entero(self, nombre):
        return self._de_tipo(nombre, self._tomar(nombre), int)

    def entero_opcional(self, nombre):
        return self._de_tipo(nombre, self._tomar(nombre), int, opcional=True)

    def texto(self, nombre):
        return self._de_tipo(nombre, self._tomar(nombre), str)

    def texto_opcional(self, nombre):
        return self._de_tipo(nombre, self._tomar(nombre), str, opcional=True)

    def booleano(self, nombre):
        return self._de_tipo(nombre, self._tomar(nombre), bool)

    def real_opcional(self, nombre):
        valor = self._tomar(nombre)
        if valor is None:
            return None
        return float(self._de_tipo(nombre, valor, (int, float)))

    def enteros32(self, nombre):
        valores = self._de_tipo(nombre, self._tomar(nombre), list)
        for valor in valores:
            self._de_tipo(nombre, valor, int)
        return tuple(valores)

    def empezar_grupo(self, nombre):
        self._entrar(self._de_tipo(nombre or "grupo", self._tomar(nombre), dict))

    def terminar_grupo(self):
        self._salir()

    def empezar_lista(self, nombre):
        lista = self._de_tipo(nombre, self._tomar(nombre), list)
        self._entrar(lista)
        return len(lista)

    def terminar_lista(self):
        # (empezar_lista devolvió el largo y el recorrido lee exactamente
        # esa cantidad: no puede sobrar nada.)
        self._salir()

    def _entrar(self, nuevo):
        self._pila.apilar((self._actual, self._indice))
        self._actual = nuevo
        self._indice = 0

    def _salir(self):
        self._actual, self._indice = self._pila.desapilar()
