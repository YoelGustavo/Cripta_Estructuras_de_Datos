"""--offline: la fuente de datos sin red (§3).

El enunciado dice que el curso publicaría un "paquete de respuestas
previamente descargadas". No se publicó, así que el paquete es la COPIA
LOCAL que el propio programa guarda al jugar con conexión (carpeta cache/):
el esqueleto, el contenido de las salas que se cargaron, los datos
generales de la cripta y las fichas del catálogo.

Devuelve lo mismo que FuenteHTTP (el mismo "contrato"): ni el modelo ni el
controlador saben si los datos vinieron de la red o del disco (§6). Si el
curso publica el paquete, solo cambia esta clase.

Límite (decisión del grupo): sin conexión solo se puede entrar a las salas
que se cargaron alguna vez con conexión. Entrar a otra no termina la
partida: el controlador avisa y la acción no se hace.
"""

import json

from crypta.Adaptadores.FuenteDatos import FuenteDatos
from crypta.Adaptadores.AlmacenDisco import AlmacenDisco


class FuenteOffline(FuenteDatos):

    def __init__(self, almacen=None):
        self._almacen = (
            almacen if almacen is not None
            else AlmacenDisco()
        )
        self._solicitudes = 0

    # =========================================================
    # LECTURA LOCAL
    # =========================================================

    def _cripta_local(self, cripta_id):
        if not self._almacen.existe_cripta(cripta_id):
            raise RuntimeError(
                f"Modo sin conexión: la cripta {cripta_id} no tiene "
                f"copia local. Juégala una vez con conexión para que "
                f"se guarde (queda en la carpeta cache)"
            )

        try:
            with open(
                self._almacen._ruta_cripta(cripta_id),
                "r",
                encoding="utf-8"
            ) as archivo:
                datos = json.load(archivo)

        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"No se pudo leer la cripta local: {error}"
            ) from error

        version = datos.get("version")

        if version is None:
            raise RuntimeError(
                "La cripta almacenada no tiene versión."
            )

        cripta = self._almacen.cargar_cripta(
            cripta_id,
            version
        )

        if cripta is None:
            raise RuntimeError(
                "No se pudo recuperar la cripta local."
            )

        return cripta

    # =========================================================
    # CRIPTAS
    # =========================================================

    def listar_criptas(self):
        raise RuntimeError(
            "El listado de criptas no está disponible "
            "en modo offline. Indica el ID de una "
            "cripta almacenada localmente."
        )

    def obtener_cripta(self, cripta_id):
        datos = self._cripta_local(cripta_id)

        generales = datos.get("datos_generales")

        if generales is None:
            raise RuntimeError(
                f"La cripta {cripta_id} tiene una caché "
                "antigua sin datos generales. "
                "Actualízala desde el modo online."
            )

        # Devolver una copia de los datos originales.
        return dict(generales)

    def obtener_pagina_salas(self, cripta_id, pagina):
        datos = self._cripta_local(cripta_id)

        if pagina != 1:
            raise ValueError(
                "La cripta offline tiene una sola "
                "página local."
            )

        return {
            "salas": datos.get("esqueleto") or []
        }

    def obtener_contenido(self, cripta_id, salas):
        if len(salas) == 0:
            return {"contenido": []}

        if len(salas) > 10:
            raise ValueError(
                "Contenido permite un máximo "
                "de 10 salas por solicitud"
            )

        datos = self._cripta_local(cripta_id)
        contenidos = datos.get("contenidos") or []

        resultado = []

        for id_sala in salas:
            encontrado = None

            for contenido in contenidos:
                if contenido.get("sala") == id_sala:
                    encontrado = contenido
                    break

            if encontrado is None:
                raise RuntimeError(
                    f"Modo sin conexión: la sala {id_sala} no está en "
                    f"la copia local. Sin conexión solo se puede entrar "
                    f"a salas que ya se cargaron alguna vez con conexión"
                )

            resultado.append(encontrado)

        return {"contenido": resultado}

    # =========================================================
    # CATÁLOGO
    # =========================================================

    def obtener_catalogo(self, ids):
        if len(ids) == 0:
            return {"entidades": []}

        if len(ids) > 10:
            raise ValueError(
                "Catálogo permite un máximo "
                "de 10 ids por solicitud"
            )

        version = (
            self.obtener_version_catalogo()["version"]
        )

        entidades = []

        for id_tipo in ids:
            ficha = self._almacen.cargar_ficha(
                version,
                id_tipo
            )

            if ficha is None:
                raise RuntimeError(
                    f"La ficha {id_tipo} no está "
                    "disponible sin conexión."
                )

            entidades.append(ficha)

        return {"entidades": entidades}

    # =========================================================
    # VERSIONES
    # =========================================================

    def obtener_version_cripta(self, cripta_id):
        datos = self._cripta_local(cripta_id)

        return {
            "version": datos["version"]
        }

    def obtener_version_catalogo(self):
        datos = self._almacen._leer_catalogo()

        if datos is None or "version" not in datos:
            raise RuntimeError(
                "No hay un catálogo disponible "
                "en la caché local."
            )

        return {
            "version": datos["version"]
        }

    def cantidad_solicitudes(self):
        return self._solicitudes
