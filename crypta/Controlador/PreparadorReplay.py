from crypta.Adaptadores.FuenteOffline import FuenteOffline
from crypta.Controlador.Fabrica import nueva_partida
from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.GestorCripta import GestorCripta
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.Controlador.Reproductor import ReproduccionIncompatible


class PreparadorReplay:

    def __init__(self, fuente, almacen, cache_size=25):
        self._almacen = almacen
        self._cache_size = cache_size

        self._candidatas = (fuente, FuenteOffline(almacen))

        self._cripta_id = None
        self._version_cripta = None
        self._fuente = None          
        self._gestor_contenido = None

    def cripta_disponible(self, cripta_id, version):
        self._cripta_id = cripta_id
        self._version_cripta = version

        for fuente in self._candidatas:
            if self._version_de_cripta(fuente) == version:
                return True

        return False

    def catalogo_disponible(self, version):
        for fuente in self._candidatas:
            if (self._version_de_cripta(fuente) == self._version_cripta
                    and self._version_de_catalogo(fuente) == version):
                self._fuente = fuente
                return True

        return False

    def _version_de_cripta(self, fuente):
        try:
            return fuente.obtener_version_cripta(self._cripta_id).get("version")
        except RuntimeError:
            return None

    def _version_de_catalogo(self, fuente):
        try:
            return fuente.obtener_version_catalogo().get("version")
        except RuntimeError:
            return None

    def crear_partida(self, encabezado):
        if self._fuente is None:
            raise ValueError("Primero hay que revisar las versiones del registro")

        datos_cripta, mapa, _ = GestorCripta(
            self._fuente,
            self._almacen
        ).cargar(encabezado.cripta_id)

        repositorio = RepositorioFichas(
            fuente=self._fuente,
            almacen=self._almacen,
            version_catalogo=encabezado.version_catalogo,
            cache_size=self._cache_size
        )

        self._gestor_contenido = GestorContenido(
            self._fuente,
            mapa,
            encabezado.cripta_id,
            repositorio
        )

        partida = nueva_partida(
            datos_cripta,
            mapa,
            repositorio.obtener_ficha,
            encabezado.semilla,
            encabezado.jugador
        )

        self.garantizar_sala(partida.id_sala_inicial)

        return partida


    def garantizar_sala(self, id_sala):
        try:
            self._gestor_contenido.garantizar_sala(id_sala)
        except RuntimeError as error:
            raise ReproduccionIncompatible(
                f"No se pudo obtener la sala {id_sala} de la versión "
                f"'{self._version_cripta}' de la cripta ({error}). No se "
                f"puede garantizar una reproducción fiel."
            ) from error

    def cerrar(self):
        if self._gestor_contenido is not None:
            self._gestor_contenido.cerrar()
