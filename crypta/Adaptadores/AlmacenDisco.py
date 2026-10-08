import json
import os


class AlmacenDisco:

    def __init__(self, ruta="cache"):
        self._ruta = ruta

        os.makedirs(
            self._ruta,
            exist_ok=True
        )

    def _ruta_catalogo(self):
        return os.path.join(
            self._ruta,
            "catalogo.json"
        )

    def _leer_catalogo(self):
        ruta = self._ruta_catalogo()

        if not os.path.exists(ruta):
            return None

        try:
            with open(
                ruta,
                "r",
                encoding="utf-8"
            ) as archivo:
                return json.load(archivo)

        except (OSError, json.JSONDecodeError):
            return None

    def guardar_catalogo(self, version, fichas):
        datos = {
            "version": version,
            "fichas": fichas
        }

        with open(
            self._ruta_catalogo(),
            "w",
            encoding="utf-8"
        ) as archivo:
            json.dump(
                datos,
                archivo,
                ensure_ascii=False,
                indent=2
            )

    def cargar_catalogo(self, version):
        datos = self._leer_catalogo()

        if datos is None:
            return {}

        if datos.get("version") != version:
            return {}

        return datos.get("fichas", {})

    def cargar_ficha(self, version, id_tipo):
        """
        Recupera UNA ficha desde el almacenamiento
        persistente.

        Esta operación realiza una lectura real de disco.
        """

        datos = self._leer_catalogo()

        if datos is None:
            return None

        # Si la versión cambió, ninguna ficha persistida
        # de este catálogo es válida.
        if datos.get("version") != version:
            return None

        fichas = datos.get(
            "fichas",
            {}
        )

        return fichas.get(id_tipo)

    def contiene_ficha(self, version, id_tipo):
        """
        Comprueba si una ficha válida existe en disco.
        """

        datos = self._leer_catalogo()

        if datos is None:
            return False

        if datos.get("version") != version:
            return False

        fichas = datos.get(
            "fichas",
            {}
        )

        return id_tipo in fichas

    def guardar_fichas(self, version, fichas_nuevas):
        """
        Agrega o actualiza fichas sin perder las
        que ya estaban persistidas.
        """

        datos = self._leer_catalogo()

        # Podemos reutilizar el catálogo existente
        # solamente si corresponde a la misma versión.
        if (
            datos is not None
            and datos.get("version") == version
        ):
            fichas = datos.get(
                "fichas",
                {}
            )
        else:
            fichas = {}

        # fichas_nuevas: cualquier recorrible de fichas (dict del JSON),
        # por ejemplo una ListaSimple. Aquí sí se arma un dict: es el
        # formato del archivo JSON, y esto es un adaptador (§7).
        for ficha in fichas_nuevas:
            fichas[ficha["id"]] = ficha

        self.guardar_catalogo(
            version,
            fichas
        )

    def cantidad_fichas(self, version):
        datos = self._leer_catalogo()

        if datos is None:
            return 0

        if datos.get("version") != version:
            return 0

        return len(
            datos.get("fichas", {})
        )

    def existe_catalogo(self):
        return os.path.exists(
            self._ruta_catalogo()
        )

    def _ruta_cripta(self, cripta_id):
        return os.path.join(
            self._ruta,
            f"{cripta_id}.json"
        )


    def guardar_cripta(
        self,
        cripta_id,
        version,
        esqueleto,
        contenidos
    ):
        datos = {
            "version": version,
            "esqueleto": esqueleto,
            "contenidos": contenidos
        }

        with open(
            self._ruta_cripta(cripta_id),
            "w",
            encoding="utf-8"
        ) as archivo:
            json.dump(
                datos,
                archivo,
                ensure_ascii=False,
                indent=2
            )


    def cargar_cripta(self, cripta_id, version):
        ruta = self._ruta_cripta(cripta_id)

        if not os.path.exists(ruta):
            return None

        try:
            with open(
                ruta,
                "r",
                encoding="utf-8"
            ) as archivo:
                datos = json.load(archivo)

        except (OSError, json.JSONDecodeError):
            return None

        # Solo reutilizamos lo persistido si corresponde
        # exactamente a la versión actual de la cripta.
        if datos.get("version") != version:
            return None

        return datos


    def existe_cripta(self, cripta_id):
        return os.path.exists(
            self._ruta_cripta(cripta_id)
        )