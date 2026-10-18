import os

from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


FORMATO_PUNTAJES = 1

MARCA = "# CRIPTA tabla de puntajes"
SEPARADOR = "---"
SEPARADOR_CAMPOS = "\t"
CANTIDAD_CAMPOS = 7

VICTORIA = "victoria"
DERROTA = "derrota"


class ErrorTablaPuntajes(Exception):
    """El archivo de puntajes no tiene el formato esperado."""


class Puntaje:

    def __init__(self, jugador, cripta_id, version_cripta, resultado,
                 acciones, enemigos, tiempo):
        if resultado != VICTORIA and resultado != DERROTA:
            raise ValueError(f"Resultado inválido: {resultado!r} (victoria o derrota)")

        for nombre, valor in (("acciones", acciones), ("enemigos", enemigos),
                              ("tiempo", tiempo)):
            if not isinstance(valor, int) or valor < 0:
                raise ValueError(f"'{nombre}' debe ser un entero >= 0, no {valor!r}")

        for valor in (jugador, cripta_id, version_cripta):
            if not isinstance(valor, str):
                raise ValueError(f"Se esperaba texto, no {valor!r}")
            if SEPARADOR_CAMPOS in valor or "\n" in valor or "\r" in valor:
                raise ValueError(f"{valor!r} no puede tener tabuladores ni saltos de línea")

        self.jugador = jugador
        self.cripta_id = cripta_id
        self.version_cripta = version_cripta
        self.resultado = resultado
        self.acciones = acciones
        self.enemigos = enemigos
        self.tiempo = tiempo

        if resultado == VICTORIA:
            self.clave_ranking = (0, tiempo, acciones, -enemigos)
        else:
            self.clave_ranking = (1, -enemigos, -tiempo, acciones)

    def __repr__(self):
        return (f"Puntaje({self.jugador!r}, {self.cripta_id} v{self.version_cripta}, "
                f"{self.resultado}, t={self.tiempo}, acciones={self.acciones}, "
                f"enemigos={self.enemigos})")


def puntaje_de(partida, cripta_id, version_cripta):
    if not partida.terminada:
        raise ValueError("Solo se registran partidas terminadas (§2.12)")

    return Puntaje(partida.jugador.nombre, cripta_id, version_cripta,
                   partida.resultado, partida.acciones_jugador,
                   partida.enemigos_derrotados, partida.reloj)


class TablaPuntajes:

    def __init__(self, ruta=None):
        self._ruta = ruta
        self._puntajes = Vector()

        if ruta is not None and not _sin_tabla(ruta):
            self._leer()

    def __len__(self):
        return len(self._puntajes)

    def __iter__(self):
        for i in range(len(self._puntajes)):
            yield self._puntajes.obtener(i)

    def registrar(self, puntaje):
        if self._ruta is not None:
            nuevo = _sin_tabla(self._ruta)

            with open(self._ruta, "a", encoding="utf-8") as archivo:
                if nuevo:
                    archivo.write(f"{MARCA}\nformato {FORMATO_PUNTAJES}\n{SEPARADOR}\n")
                archivo.write(_linea_de(puntaje))

        self._puntajes.agregar(puntaje)

    def registrar_partida(self, partida, cripta_id, version_cripta):
        puntaje = puntaje_de(partida, cripta_id, version_cripta)
        self.registrar(puntaje)
        return puntaje

    def ranking(self, cripta_id=None, limite=None):
        copia = Vector()

        for i in range(len(self._puntajes)):
            puntaje = self._puntajes.obtener(i)

            if cripta_id is None or puntaje.cripta_id == cripta_id:
                copia.agregar(puntaje)

        ordenar(copia, clave=_clave_ranking)

        if limite is not None:
            while len(copia) > limite:
                copia.quitar_ultimo()

        return copia

    def _leer(self):
        with open(self._ruta, encoding="utf-8") as archivo:
            if archivo.readline().rstrip("\n") != MARCA:
                raise ErrorTablaPuntajes(f"{self._ruta} no es una tabla de puntajes de CRIPTA")

            formato = archivo.readline().rstrip("\n")

            if formato != f"formato {FORMATO_PUNTAJES}":
                raise ErrorTablaPuntajes(
                    f"La tabla es del '{formato}'; este programa lee el "
                    f"formato {FORMATO_PUNTAJES}"
                )

            if archivo.readline().rstrip("\n") != SEPARADOR:
                raise ErrorTablaPuntajes("Falta el separador '---' de la tabla de puntajes")

            numero = 3

            for linea in archivo:
                numero += 1
                linea = linea.rstrip("\n")

                if linea:
                    self._puntajes.agregar(_puntaje_de_linea(linea, numero))


def _sin_tabla(ruta):
    return not os.path.exists(ruta) or os.path.getsize(ruta) == 0


def _clave_ranking(puntaje):
    return puntaje.clave_ranking


def _linea_de(puntaje):
    campos = (puntaje.resultado, str(puntaje.tiempo), str(puntaje.acciones),
              str(puntaje.enemigos), puntaje.cripta_id, puntaje.version_cripta,
              puntaje.jugador)
    return SEPARADOR_CAMPOS.join(campos) + "\n"


def _puntaje_de_linea(linea, numero):
    campos = _separar_campos(linea)

    if len(campos) != CANTIDAD_CAMPOS:
        raise ErrorTablaPuntajes(
            f"Línea {numero} de la tabla de puntajes: tiene {len(campos)} "
            f"datos y deberían ser {CANTIDAD_CAMPOS}"
        )

    numeros = Vector(3)

    for i in range(1, 4):
        texto = campos.obtener(i)

        if not texto.isdigit():
            raise ErrorTablaPuntajes(
                f"Línea {numero} de la tabla de puntajes: '{texto}' no es un número"
            )

        numeros.agregar(int(texto))

    try:
        return Puntaje(jugador=campos.obtener(6), cripta_id=campos.obtener(4),
                       version_cripta=campos.obtener(5), resultado=campos.obtener(0),
                       tiempo=numeros.obtener(0), acciones=numeros.obtener(1),
                       enemigos=numeros.obtener(2))
    except ValueError as error:
        raise ErrorTablaPuntajes(f"Línea {numero} de la tabla de puntajes: {error}")


def _separar_campos(linea):
    campos = Vector(CANTIDAD_CAMPOS)
    resto = linea

    while True:
        campo, separador, resto = resto.partition(SEPARADOR_CAMPOS)
        campos.agregar(campo)

        if not separador:
            return campos