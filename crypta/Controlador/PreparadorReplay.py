"""El preparador de verdad para --replay (§4.11).

El Reproductor (Fase 6.2) sabe repetir los comandos de un log, pero no
sabe de dónde sacar la cripta ni el catálogo. Eso se lo da este objeto,
con los cuatro métodos que pide Reproductor.py:

    cripta_disponible(cripta_id, version)
    catalogo_disponible(version)
    crear_partida(encabezado)
    garantizar_sala(id_sala)

De dónde salen los datos, en este orden:
  1. La fuente normal (el servidor, o la caché con --offline), si sirve
     EXACTAMENTE las versiones del log.
  2. Si no (por ejemplo, el servidor ya publicó otra versión, o no hay
     red), la copia local en disco, si es de esas versiones. Se usa SIN
     red: FuenteOffline solo lee el disco.
  3. Si ninguna sirve, el Reproductor avisa que no se puede garantizar una
     reproducción fiel (ReproduccionIncompatible) y no juega nada.
"""

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

        # Las dos fuentes posibles, en orden de preferencia.
        self._candidatas = (fuente, FuenteOffline(almacen))

        self._cripta_id = None
        self._version_cripta = None
        self._fuente = None              # la elegida en catalogo_disponible
        self._gestor_contenido = None    # se crea en crear_partida

    # =========================================================
    # 1. ¿SE TIENEN LAS VERSIONES DEL LOG?
    # =========================================================

    def cripta_disponible(self, cripta_id, version):
        self._cripta_id = cripta_id
        self._version_cripta = version

        for fuente in self._candidatas:
            if self._version_de_cripta(fuente) == version:
                return True

        return False

    def catalogo_disponible(self, version):
        # Se elige UNA fuente que tenga las DOS versiones del log. Así nunca
        # se mezcla la cripta de una versión con el catálogo de otra.
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
            # Sin red, o sin copia local: esta fuente no sirve.
            return None

    def _version_de_catalogo(self, fuente):
        try:
            return fuente.obtener_version_catalogo().get("version")
        except RuntimeError:
            return None

    # =========================================================
    # 2. LA MISMA PARTIDA DEL PRINCIPIO
    # =========================================================

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

        # El MISMO código que al jugar, con la semilla y el nombre del log.
        partida = nueva_partida(
            datos_cripta,
            mapa,
            repositorio.obtener_ficha,
            encabezado.semilla,
            encabezado.jugador
        )

        # El Reproductor la quiere SIN iniciar y con la sala inicial cargada.
        self.garantizar_sala(partida.id_sala_inicial)

        return partida

    # =========================================================
    # 3. LAS SALAS, SIEMPRE DE LA VERSIÓN DEL LOG
    # =========================================================

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
        """Apaga el hilo de la precarga, si se llegó a crear."""
        if self._gestor_contenido is not None:
            self._gestor_contenido.cerrar()
