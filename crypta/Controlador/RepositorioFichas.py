from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.CacheLRU import CacheLRU
from crypta.estructuras.ListaSimple import ListaSimple

MAX_POR_LOTE = 10

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
        #ListaSimple con los ids de tipo (sin repetir) de un contenido.
        ids = ListaSimple()
        vistos = ArbolBusqueda()
 
        for id_tipo in self._tipos_de(contenido):
            if not vistos.contiene(id_tipo):
                vistos.insertar(id_tipo, True)
                ids.agregar_al_final(id_tipo)
 
        return ids
 

    def resolver_contenidos(self, contenidos):
        vistos = ArbolBusqueda()#cambie los sets por arboles.
        por_pedir = ListaSimple()

        for contenido in contenidos:
            for id_tipo in self._tipos_de(contenido):
                self._anotar(id_tipo, vistos, por_pedir)
 
        while not por_pedir.esta_vacia():
            lote = ListaSimple()
 
            while not por_pedir.esta_vacia() and len(lote) < MAX_POR_LOTE:
                lote.agregar_al_final(por_pedir.quitar_del_frente())
 
            recibidas = self._guardar_respuesta(
                self._fuente.obtener_catalogo(lote)
            )
 
            # Lo que sueltan los enemigos recin descargados entra a la
            # misma cola, así viaja en el prximo lote
            for ficha in recibidas:
                if ficha.get("clase") == "enemigo":
                    for id_suelta in ficha.get("suelta") or ():
                        self._anotar(id_suelta, vistos, por_pedir)

    def _anotar(self, id_tipo, vistos, por_pedir):
        if vistos.contiene(id_tipo):
            return
 
        vistos.insertar(id_tipo, True)
 
        # 1. Buscar en RAM.
        if self._cache.contiene(id_tipo):
            self._cache.obtener(id_tipo)
            return
 
        # 2. Buscar mediante lectura real de disco.
        ficha = self._cargar_desde_disco(id_tipo)
 
        if ficha is not None:
            self._cache.insertar(id_tipo, ficha)
            return
 
        # 3. No existe en RAM ni en almacenamiento
        # persistente válido. Habrá que pedirla por red.
        por_pedir.agregar_al_final(id_tipo)
 
    @staticmethod
    def _tipos_de(contenido):
        # Recorre los ids de tipo de un contenido (pueden repetirse).
        # "or ()": las listas pueden no venir, o venir en null.
        for enemigo in contenido.get("enemigos") or ():
            yield enemigo["tipo"]
 
        for tipo in contenido.get("objetos") or ():
            yield tipo
 
        for trampa in contenido.get("trampas") or ():
            yield trampa["tipo"]
 
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
        """Guarda en la caché y en disco las fichas que llegaron por red.
        Devuelve una ListaSimple con ellas."""
        recibidas = ListaSimple()
 
        for ficha in respuesta.get("entidades") or ():
            # Entra en la caché limitada.
            self._cache.insertar(
                ficha["id"],
                ficha
            )
 
            recibidas.agregar_al_final(ficha)
 
        if (
            len(recibidas) > 0
            and self._almacen is not None
            and self._version_catalogo is not None
        ):
            self._almacen.guardar_fichas(
                self._version_catalogo,
                recibidas
            )
 
        return recibidas
 
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
 
        # 3. Red (último recurso: no debería pasar si el contenido de la
        # sala se resolvió antes con resolver_contenidos)
        lote = ListaSimple()
        lote.agregar_al_final(id_tipo)
 
        recibidas = self._guardar_respuesta(
            self._fuente.obtener_catalogo(lote)
        )
 
        for ficha in recibidas:
            if ficha["id"] == id_tipo:
                return ficha
 
        return None
 
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