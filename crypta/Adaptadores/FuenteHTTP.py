import threading
import time
import uuid
import requests

from crypta.Adaptadores.FuenteDatos import FuenteDatos


BASE_URL = "https://cripta-api.kad06a0zhgs84.us-east-2.cs.amazonlightsail.com/v1"


class PresupuestoAgotado(RuntimeError):
    """§5.1: se llegó a presupuesto_solicitudes de la cripta. La solicitud
    NO se envía."""


class FuenteHTTP(FuenteDatos):

    def __init__(self):
        self._client_id = str(uuid.uuid4())

        self._headers = {
            "X-Cripta-Client-Id": self._client_id
        }

        self._solicitudes = 0

        self._presupuesto = None

        self._candado = threading.Lock()

    def fijar_presupuesto(self, presupuesto):
        self._presupuesto = presupuesto

    def solicitudes_restantes(self):
        if self._presupuesto is None:
            return None

        return max(0, self._presupuesto - self._solicitudes)

    def _contar_una(self, ruta):
        with self._candado:
            if (self._presupuesto is not None
                    and self._solicitudes >= self._presupuesto):
                raise PresupuestoAgotado(
                    f"Se agotó el presupuesto de {self._presupuesto} "
                    f"solicitudes de red de esta cripta (al pedir {ruta})"
                )

            self._solicitudes += 1

    def _get(self, ruta):
        while True:
            self._contar_una(ruta)

            try:
                respuesta = requests.get(
                    f"{BASE_URL}{ruta}",
                    headers=self._headers,
                    timeout=10
                )

            except requests.RequestException as error:
                raise RuntimeError(
                    f"Error de red al consultar {ruta}: {error}"
                )

            if respuesta.status_code == 200:
                return respuesta.json()

            if respuesta.status_code == 429:
                try:
                    datos = respuesta.json()
                    espera = datos.get("reintentar_en", 1)
                except ValueError:
                    espera = 1

                print(
                    f"HTTP 429. Reintentando en {espera} segundos..."
                )

                time.sleep(espera)
                continue

            raise RuntimeError(
                f"Error HTTP {respuesta.status_code} "
                f"al consultar {ruta}"
            )

    def listar_criptas(self):
        return self._get("/criptas")

    def obtener_cripta(self, cripta_id):
        return self._get(
            f"/criptas/{cripta_id}"
        )

    def obtener_pagina_salas(self, cripta_id, pagina):
        return self._get(
            f"/criptas/{cripta_id}/salas?pagina={pagina}"
        )

    def obtener_contenido(self, cripta_id, salas):
        if len(salas) == 0:
            return {"contenido": []}

        if len(salas) > 10:
            raise ValueError(
                "Contenido permite un máximo de 10 salas por solicitud"
            )

        salas_texto = ",".join(str(sala) for sala in salas)

        return self._get(
            f"/criptas/{cripta_id}/contenido?salas={salas_texto}"
        )

    def obtener_catalogo(self, ids):
        if len(ids) == 0:
            return {"entidades": []}

        if len(ids) > 10:
            raise ValueError(
                "Catálogo permite un máximo de 10 ids por solicitud"
            )

        ids_texto = ",".join(str(id_) for id_ in ids)

        return self._get(
            f"/catalogo?ids={ids_texto}"
        )

    def obtener_version_cripta(self, cripta_id):
        return self._get(
            f"/criptas/{cripta_id}/version"
        )

    def obtener_version_catalogo(self):
        return self._get(
            "/catalogo/version"
        )

    def obtener_llaves(self, cripta_id):
        """Ubicación de las llaves (P2 §4.2). Cuenta y respeta el
        presupuesto como toda solicitud, incluidos los reintentos de un 429
        (FR-322)."""
        return self._get(
            f"/criptas/{cripta_id}/llaves"
        )

    def cantidad_solicitudes(self):
        return self._solicitudes