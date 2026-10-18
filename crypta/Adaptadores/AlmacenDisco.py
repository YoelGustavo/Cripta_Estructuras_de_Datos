
import json
import os


class AlmacenDisco:

    def __init__(self, ruta="cache"):
        self._ruta = ruta
        os.makedirs(self._ruta, exist_ok=True)


    def _ruta_catalogo(self):
        return os.path.join(self._ruta, "catalogo.json")

    def _leer_catalogo(self):
        ruta = self._ruta_catalogo()

        if not os.path.exists(ruta):
            return None

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
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
        datos = self._leer_catalogo()

        if datos is None:
            return None

        if datos.get("version") != version:
            return None

        fichas = datos.get("fichas", {})
        return fichas.get(id_tipo)

    def contiene_ficha(self, version, id_tipo):
        datos = self._leer_catalogo()

        if datos is None:
            return False

        if datos.get("version") != version:
            return False

        return id_tipo in datos.get("fichas", {})

    def guardar_fichas(self, version, fichas_nuevas):
        datos = self._leer_catalogo()

        if (
            datos is not None
            and datos.get("version") == version
        ):
            fichas = datos.get("fichas", {})
        else:
            fichas = {}

        for ficha in fichas_nuevas:
            fichas[ficha["id"]] = ficha

        self.guardar_catalogo(version, fichas)

    def cantidad_fichas(self, version):
        datos = self._leer_catalogo()

        if datos is None:
            return 0

        if datos.get("version") != version:
            return 0

        return len(datos.get("fichas", {}))

    def existe_catalogo(self):
        return os.path.exists(self._ruta_catalogo())


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
        contenidos,
        datos_generales=None
    ):
        datos = {
            "version": version,
            "esqueleto": esqueleto,
            "contenidos": contenidos
        }

        
        if datos_generales is not None:
            datos["datos_generales"] = datos_generales

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

        if datos.get("version") != version:
            return None

        return datos

    def existe_cripta(self, cripta_id):
        return os.path.exists(
            self._ruta_cripta(cripta_id)
        )

    def criptas_guardadas(self):
        
        ids = []

        for nombre in sorted(os.listdir(self._ruta)):
            if nombre.endswith(".json") and nombre != "catalogo.json":
                ids.append(nombre[:-len(".json")])

        return ids