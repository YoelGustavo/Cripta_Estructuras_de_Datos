

import json

from crypta.Adaptadores.FuenteDatos import FuenteDatos, LlavesNoDisponibles
from crypta.Adaptadores.AlmacenDisco import AlmacenDisco


class FuenteOffline(FuenteDatos):

    def __init__(self, almacen=None):
        self._almacen = (
            almacen if almacen is not None
            else AlmacenDisco()
        )
        self._solicitudes = 0


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

    
    def listar_criptas(self):
        criptas = []

        for cripta_id in self._almacen.criptas_guardadas():
            try:
                generales = self._cripta_local(cripta_id).get("datos_generales") or {}
            except RuntimeError:
                continue      # un archivo dañado no impide listar las demás

            criptas.append({
                "id": cripta_id,
                "nombre": "(copia local)",
                "salas": generales.get("salas_total"),
                "dificultad": None,
            })

        return {"criptas": criptas}

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


    def obtener_llaves(self, cripta_id):
        """La ubicación de las llaves guardada en la copia local (FR-323).
        Si la copia no la tiene, no se puede verificar (FR-324)."""
        llaves = self._cripta_local(cripta_id).get("llaves")

        if llaves is None:
            raise LlavesNoDisponibles(
                "sin conexión y sin la ubicación de las llaves en la copia "
                "local")

        return llaves

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
