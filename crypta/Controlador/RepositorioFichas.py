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
 
        self._cache = CacheLRU(cache_size)

        self.aciertos = 0
        self.fallos_disco = 0
        self.fallos_red = 0
 
    def extraer_ids_contenido(self, contenido):
        ids = ListaSimple()
        vistos = ArbolBusqueda()
 
        for id_tipo in self._tipos_de(contenido):
            if not vistos.contiene(id_tipo):
                vistos.insertar(id_tipo, True)
                ids.agregar_al_final(id_tipo)
 
        return ids
 

    def resolver_contenidos(self, contenidos):
        vistos = ArbolBusqueda()
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
 
            for ficha in recibidas:
                if ficha.get("clase") == "enemigo":
                    for id_suelta in ficha.get("suelta") or ():
                        self._anotar(id_suelta, vistos, por_pedir)

    def _anotar(self, id_tipo, vistos, por_pedir):
        if vistos.contiene(id_tipo):
            return
 
        vistos.insertar(id_tipo, True)
 
        if self._cache.contiene(id_tipo):
            self._cache.obtener(id_tipo)
            self.aciertos += 1
            return
 
        ficha = self._cargar_desde_disco(id_tipo)
 
        if ficha is not None:
            self._cache.insertar(id_tipo, ficha)
            self.fallos_disco += 1
            return
 
        self.fallos_red += 1
        por_pedir.agregar_al_final(id_tipo)
 
    @staticmethod
    def _tipos_de(contenido):
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
        recibidas = ListaSimple()
 
        for ficha in respuesta.get("entidades") or ():
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
        ficha = self._cache.obtener(
            id_tipo
        )
 
        if ficha is not None:
            self.aciertos += 1
            return ficha
 
        ficha = self._cargar_desde_disco(
            id_tipo
        )
 
        if ficha is not None:
            self._cache.insertar(
                id_tipo,
                ficha
            )
 
            self.fallos_disco += 1
            return ficha
 
        self.fallos_red += 1
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
        return self._cache.contiene(
            id_tipo
        )
 
    def esta_en_memoria(self, id_tipo):
        return self._cache.contiene(
            id_tipo
        )
 
    def marcar_en_uso(self, id_tipo):
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