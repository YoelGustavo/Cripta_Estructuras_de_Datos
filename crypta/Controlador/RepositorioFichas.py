from crypta.estructuras.CacheLRU import CacheLRU


class RepositorioFichas:

    def __init__(
        self,
        fuente,
        almacen=None,
        version_catalogo=None,
        cache_size=25
    ):
        self._fuente = fuente
        self._almacen = almacen
        self._version_catalogo = version_catalogo

        # Único almacenamiento de fichas completas en memoria.
        self._cache = CacheLRU(cache_size)

    def extraer_ids_contenido(self, contenido):
        ids = []
        vistos = set()

        # Enemigos
        for enemigo in contenido.get("enemigos", []):
            tipo = enemigo["tipo"]

            if tipo not in vistos:
                vistos.add(tipo)
                ids.append(tipo)

        # Objetos
        for tipo in contenido.get("objetos", []):
            if tipo not in vistos:
                vistos.add(tipo)
                ids.append(tipo)

        # Trampas
        for trampa in contenido.get("trampas", []):
            tipo = trampa["tipo"]

            if tipo not in vistos:
                vistos.add(tipo)
                ids.append(tipo)

        return ids

    def resolver_contenidos(self, contenidos):
        ids_necesarios = []
        vistos = set()

        # Reunimos todos los tipos únicos referenciados.
        for contenido in contenidos:
            ids = self.extraer_ids_contenido(
                contenido
            )

            for id_tipo in ids:
                if id_tipo in vistos:
                    continue

                vistos.add(id_tipo)
                ids_necesarios.append(id_tipo)

        ids_red = []

        for id_tipo in ids_necesarios:

            # 1. Buscar en RAM.
            if self._cache.contiene(id_tipo):
                self._cache.obtener(id_tipo)
                continue

            # 2. Buscar mediante lectura real de disco.
            ficha = self._cargar_desde_disco(
                id_tipo
            )

            if ficha is not None:
                self._cache.insertar(
                    id_tipo,
                    ficha
                )
                continue

            # 3. No existe en RAM ni en almacenamiento
            # persistente válido. Habrá que pedirla por red.
            ids_red.append(id_tipo)

        # El API admite como máximo 10 ids por solicitud.
        inicio = 0

        while inicio < len(ids_red):
            lote = ids_red[
                inicio:inicio + 10
            ]

            respuesta = self._fuente.obtener_catalogo(
                lote
            )

            self._guardar_respuesta(
                respuesta
            )

            inicio += 10

    def _cargar_desde_disco(self, id_tipo):
        if (
            self._almacen is None
            or self._version_catalogo is None
        ):
            return None

        return self._almacen.cargar_ficha(
            self._version_catalogo,
            id_tipo
        )

    def _guardar_respuesta(self, respuesta):
        entidades = respuesta.get(
            "entidades",
            []
        )

        fichas_nuevas = {}

        for ficha in entidades:
            id_tipo = ficha["id"]

            # Entra en la caché limitada.
            self._cache.insertar(
                id_tipo,
                ficha
            )

            # También se prepara para persistencia.
            fichas_nuevas[id_tipo] = ficha

        if (
            len(fichas_nuevas) > 0
            and self._almacen is not None
            and self._version_catalogo is not None
        ):
            self._almacen.guardar_fichas(
                self._version_catalogo,
                fichas_nuevas
            )

    def obtener_ficha(self, id_tipo):
        # 1. RAM
        ficha = self._cache.obtener(
            id_tipo
        )

        if ficha is not None:
            return ficha

        # 2. Disco
        ficha = self._cargar_desde_disco(
            id_tipo
        )

        if ficha is not None:
            self._cache.insertar(
                id_tipo,
                ficha
            )

            return ficha

        # 3. Red
        respuesta = self._fuente.obtener_catalogo(
            [id_tipo]
        )

        entidades = respuesta.get(
            "entidades",
            []
        )

        if len(entidades) == 0:
            return None

        ficha = entidades[0]

        self._cache.insertar(
            id_tipo,
            ficha
        )

        if (
            self._almacen is not None
            and self._version_catalogo is not None
        ):
            self._almacen.guardar_fichas(
                self._version_catalogo,
                {
                    id_tipo: ficha
                }
            )

        return ficha

    def contiene(self, id_tipo):
        # Esta operación representa pertenencia a la
        # caché EN MEMORIA y debe ser rápida.
        return self._cache.contiene(
            id_tipo
        )

    def esta_en_memoria(self, id_tipo):
        return self._cache.contiene(
            id_tipo
        )

    def marcar_en_uso(self, id_tipo):
        # Para proteger una ficha debe estar cargada
        # en memoria.
        ficha = self.obtener_ficha(
            id_tipo
        )

        if ficha is not None:
            self._cache.marcar_en_uso(
                id_tipo
            )

    def liberar_uso(self, id_tipo):
        self._cache.liberar(
            id_tipo
        )

    def esta_en_uso(self, id_tipo):
        return self._cache.esta_en_uso(
            id_tipo
        )

    def cantidad_fichas(self):
        # Total de fichas persistidas válidas.
        if (
            self._almacen is None
            or self._version_catalogo is None
        ):
            return self._cache.cantidad()

        return self._almacen.cantidad_fichas(
            self._version_catalogo
        )

    def cantidad_en_memoria(self):
        return self._cache.cantidad()

    def capacidad_cache(self):
        return self._cache.capacidad()