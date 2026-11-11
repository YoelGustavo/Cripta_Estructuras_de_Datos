import os
import struct

from crypta.Adaptadores.EstadoPartida import (
    ErrorGuardado, armar_partida, escribir_encabezado, escribir_general,
    escribir_sala, evento_suelto, leer_encabezado, leer_general, leer_sala,
    revisar_antes_de_guardar,
)
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


MAGIA = b"CRPT"
# 2: cada puerta guarda su costo (capacidad 001, FR-026).
FORMATO_GUARDADO = 2

_INICIO = struct.Struct("<4sH")
_CABECERA = struct.Struct("<HIIQI")
_ENTRADA = struct.Struct("<qQI")

_ENTERO = struct.Struct("<q")
_CANTIDAD = struct.Struct("<I")
_REAL = struct.Struct("<d")
_BYTE = struct.Struct("<B")


def guardar_partida(partida, ruta, encabezado):
    revisar_antes_de_guardar(partida, encabezado)

    e = EscritorBinario()
    escribir_encabezado(e, encabezado)
    bloque_encabezado = e.datos()

    e = EscritorBinario()
    escribir_general(e, partida)
    bloque_general = e.datos()

    salas = partida.mapa.obtener_todas()
    registros = Vector(len(salas))
    indice = Vector(len(salas))
    posicion = _INICIO.size + _CABECERA.size + len(bloque_encabezado) + len(bloque_general)

    for i in range(len(salas)):
        e = EscritorBinario()
        escribir_sala(e, salas.obtener(i))
        registro = e.datos()

        registros.agregar(registro)
        indice.agregar((salas.obtener(i).id, posicion, len(registro)))
        posicion += len(registro)

    ordenar(indice, clave=_id_de_entrada)

    temporal = ruta + ".tmp"

    with open(temporal, "wb") as archivo:
        archivo.write(_INICIO.pack(MAGIA, FORMATO_GUARDADO))
        archivo.write(_CABECERA.pack(0, len(bloque_encabezado), len(bloque_general),
                                     posicion, len(salas)))
        archivo.write(bloque_encabezado)
        archivo.write(bloque_general)

        for i in range(len(registros)):
            archivo.write(registros.obtener(i))

        for i in range(len(indice)):
            archivo.write(_ENTRADA.pack(*indice.obtener(i)))

    os.replace(temporal, ruta)


def _id_de_entrada(entrada):
    return entrada[0]


class ArchivoGuardado:
    """Una partida guardada, abierta para leer.

    Al abrirla se leen solo el inicio, la cabecera, el encabezado y el
    índice. Lo demás se lee cuando se pide:
      - leer_sala(id, fichas): solo esa sala;
      - cargar_partida(fichas): todo, para seguir jugando.

    bytes_leidos cuenta lo que se ha leído del archivo (para comprobar que
    leer una sala no lee el archivo completo)."""

    def __init__(self, ruta):
        self._ruta = ruta
        self.bytes_leidos = 0

        try:
            archivo = open(ruta, "rb")
        except OSError as error:
            raise ErrorGuardado(f"No se pudo abrir la partida guardada {ruta}: {error}")

        with archivo:
            self.tamano = os.fstat(archivo.fileno()).st_size

            magia, formato = _INICIO.unpack(self._leer(archivo, _INICIO.size))

            if magia != MAGIA:
                raise ErrorGuardado(f"{ruta} no es una partida guardada de CRIPTA")

            if formato != FORMATO_GUARDADO:
                raise ErrorGuardado(
                    f"La partida se guardó con la versión {formato} del formato y "
                    f"este programa lee la versión {FORMATO_GUARDADO}: no se puede cargar"
                )

            (_, largo_encabezado, largo_general, posicion_indice,
             cantidad) = _CABECERA.unpack(self._leer(archivo, _CABECERA.size))

            inicio_salas = _INICIO.size + _CABECERA.size + largo_encabezado + largo_general

            if (inicio_salas > posicion_indice
                    or posicion_indice + cantidad * _ENTRADA.size != self.tamano):
                raise ErrorGuardado("La partida guardada está cortada o dañada")

            l = LectorBinario(self._leer(archivo, largo_encabezado))
            self.encabezado = leer_encabezado(l)
            l.terminar()

            self._posicion_general = _INICIO.size + _CABECERA.size + largo_encabezado
            self._largo_general = largo_general

            archivo.seek(posicion_indice)
            self._leer_indice(self._leer(archivo, cantidad * _ENTRADA.size),
                              cantidad, inicio_salas, posicion_indice)

    def _leer_indice(self, datos, cantidad, inicio_salas, posicion_indice):
        pares = Vector(cantidad)
        self._ids = Vector(cantidad)

        for i in range(cantidad):
            id_sala, posicion, largo = _ENTRADA.unpack_from(datos, i * _ENTRADA.size)

            if i > 0 and id_sala <= self._ids.obtener(i - 1):
                raise ErrorGuardado("El índice de la partida guardada no está ordenado")

            if posicion < inicio_salas or posicion + largo > posicion_indice:
                raise ErrorGuardado(f"El índice apunta fuera de las salas (sala {id_sala})")

            pares.agregar((id_sala, (posicion, largo)))
            self._ids.agregar(id_sala)

        self._indice = ArbolBusqueda.desde_ordenados(pares)

    def _leer(self, archivo, cantidad):
        datos = archivo.read(cantidad)

        if len(datos) != cantidad:
            raise ErrorGuardado("La partida guardada está cortada")

        self.bytes_leidos += cantidad
        return datos

    def ids_salas(self):
        """Vector con los ids de las salas, de menor a mayor."""
        copia = Vector(len(self._ids))
        for i in range(len(self._ids)):
            copia.agregar(self._ids.obtener(i))
        return copia

    def leer_sala(self, id_sala, fichas):
        """La Sala con ese id, tal como estaba, leyendo SOLO su registro.
        Es una sala suelta: sus puertas no apuntan a otras salas y los
        eventos de sus enemigos no están en ninguna agenda."""
        entrada = self._indice.obtener(id_sala)

        if entrada is None:
            raise KeyError(f"La partida guardada no tiene la sala {id_sala}")

        with open(self._ruta, "rb") as archivo:
            leida = self._leer_registro(archivo, id_sala, entrada, fichas)

        for i in range(len(leida.referencias)):
            enemigo, turno, regeneracion = leida.referencias.obtener(i)
            enemigo.evento_siguiente = evento_suelto(turno, enemigo)
            enemigo.evento_regeneracion = evento_suelto(regeneracion, enemigo)

        return leida.sala

    def cargar_partida(self, fichas):
        """La partida completa, lista para seguir jugando. 'fichas' tiene
        que ser del catálogo de la versión self.encabezado.version_catalogo
        (y el contenido que falte, de esa versión de la cripta): eso lo
        revisa quien llama, igual que en --replay."""
        salas = Vector(len(self._ids))

        with open(self._ruta, "rb") as archivo:
            archivo.seek(self._posicion_general)
            l = LectorBinario(self._leer(archivo, self._largo_general))
            general = leer_general(l)
            l.terminar()

            for i in range(len(self._ids)):
                id_sala = self._ids.obtener(i)
                entrada = self._indice.obtener(id_sala)
                salas.agregar(self._leer_registro(archivo, id_sala, entrada, fichas))

        return armar_partida(self.encabezado, general, salas, fichas)

    def _leer_registro(self, archivo, id_sala, entrada, fichas):
        posicion, largo = entrada
        archivo.seek(posicion)
        l = LectorBinario(self._leer(archivo, largo))

        leida = leer_sala(l, fichas)
        l.terminar()

        if leida.sala.id != id_sala:
            raise ErrorGuardado(f"El índice dice sala {id_sala} y el registro es de la {leida.sala.id}")

        return leida


class EscritorBinario:
    """Va juntando los bytes de un bloque. Los nombres no se escriben."""

    def __init__(self):
        self._bytes = bytearray()

    def datos(self):
        return bytes(self._bytes)

    def entero(self, nombre, valor):
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise ValueError(f"'{nombre}' debe ser un entero, no {valor!r}")

        try:
            self._bytes += _ENTERO.pack(valor)
        except struct.error:
            raise ValueError(f"'{nombre}' = {valor} no cabe en 8 bytes")

    def entero_opcional(self, nombre, valor):
        self._presencia(valor)
        if valor is not None:
            self.entero(nombre, valor)

    def texto(self, nombre, valor):
        if not isinstance(valor, str):
            raise ValueError(f"'{nombre}' debe ser texto, no {valor!r}")

        codificado = valor.encode("utf-8")
        self._bytes += _CANTIDAD.pack(len(codificado))
        self._bytes += codificado

    def texto_opcional(self, nombre, valor):
        self._presencia(valor)
        if valor is not None:
            self.texto(nombre, valor)

    def booleano(self, nombre, valor):
        if not isinstance(valor, bool):
            raise ValueError(f"'{nombre}' debe ser True o False, no {valor!r}")

        self._bytes += _BYTE.pack(1 if valor else 0)

    def real_opcional(self, nombre, valor):
        self._presencia(valor)
        if valor is not None:
            self._bytes += _REAL.pack(valor)

    def enteros32(self, nombre, valores):
        self._bytes += _CANTIDAD.pack(len(valores))
        self._bytes += struct.pack(f"<{len(valores)}I", *valores)

    def empezar_grupo(self, nombre):
        pass

    def terminar_grupo(self):
        pass

    def empezar_lista(self, nombre, cantidad):
        self._bytes += _CANTIDAD.pack(cantidad)

    def terminar_lista(self):
        pass

    def _presencia(self, valor):
        self._bytes += _BYTE.pack(0 if valor is None else 1)


class LectorBinario:
    """Lee un bloque en el MISMO orden en que se escribió. Si los bytes no
    alcanzan o no tienen sentido, ErrorGuardado (nunca un struct.error)."""

    def __init__(self, datos):
        self._datos = datos
        self._posicion = 0

    def terminar(self):
        """El bloque tiene que haberse leído completo: si sobran bytes, el
        archivo no es lo que dice ser."""
        if self._posicion != len(self._datos):
            raise ErrorGuardado("La partida guardada tiene datos de más o está dañada")

    def entero(self, nombre):
        return _ENTERO.unpack(self._tomar(_ENTERO.size))[0]

    def entero_opcional(self, nombre):
        return self.entero(nombre) if self._hay() else None

    def texto(self, nombre):
        largo = _CANTIDAD.unpack(self._tomar(_CANTIDAD.size))[0]

        try:
            return self._tomar(largo).decode("utf-8")
        except UnicodeDecodeError:
            raise ErrorGuardado(f"Texto dañado en la partida guardada ('{nombre}')")

    def texto_opcional(self, nombre):
        return self.texto(nombre) if self._hay() else None

    def booleano(self, nombre):
        return self._byte_0_o_1(nombre) == 1

    def real_opcional(self, nombre):
        return _REAL.unpack(self._tomar(_REAL.size))[0] if self._hay() else None

    def enteros32(self, nombre):
        cantidad = self._cantidad()
        return struct.unpack(f"<{cantidad}I", self._tomar(4 * cantidad))

    def empezar_grupo(self, nombre):
        pass

    def terminar_grupo(self):
        pass

    def empezar_lista(self, nombre):
        return self._cantidad()

    def terminar_lista(self):
        pass

    def _cantidad(self):
        return _CANTIDAD.unpack(self._tomar(_CANTIDAD.size))[0]

    def _hay(self):
        return self._byte_0_o_1("presencia") == 1

    def _byte_0_o_1(self, nombre):
        valor = self._tomar(1)[0]

        if valor > 1:
            raise ErrorGuardado(f"Dato dañado en la partida guardada ('{nombre}')")

        return valor

    def _tomar(self, cantidad):
        fin = self._posicion + cantidad

        if fin > len(self._datos):
            raise ErrorGuardado("La partida guardada está cortada o dañada")

        datos = self._datos[self._posicion:fin]
        self._posicion = fin
        return datos
