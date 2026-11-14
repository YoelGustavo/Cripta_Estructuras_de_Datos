from abc import ABC, abstractmethod
from typing import Any


class LlavesNoDisponibles(RuntimeError):
    """No se puede obtener la ubicación de las llaves de la cripta
    (capacidad 003, FR-324): por ejemplo, sin conexión y sin copia local.
    Quien verifica la trata como «no se pudo verificar»."""


class FuenteDatos(ABC):

    @abstractmethod
    def listar_criptas(self) -> Any:
        pass

    @abstractmethod
    def obtener_cripta(self, cripta_id) -> Any:
        pass

    @abstractmethod
    def obtener_pagina_salas(self, cripta_id, pagina) -> Any:
        pass

    @abstractmethod
    def obtener_contenido(self, cripta_id, salas) -> Any:
        pass

    @abstractmethod
    def obtener_catalogo(self, ids) -> Any:
        pass

    @abstractmethod
    def obtener_version_cripta(self, cripta_id) -> Any:
        pass

    @abstractmethod
    def obtener_version_catalogo(self) -> Any:
        pass


    def obtener_llaves(self, cripta_id) -> Any:
        """Respuesta de GET /criptas/<id>/llaves (P2 §4.2). No es abstracto:
        una fuente que no la sabe dar lanza LlavesNoDisponibles, y así las
        fuentes que no la implementan siguen funcionando (FR-324)."""
        raise LlavesNoDisponibles(
            f"la fuente no tiene la ubicación de las llaves de {cripta_id}")

    def fijar_presupuesto(self, presupuesto):
        pass

    def cantidad_solicitudes(self):
        return 0

    def solicitudes_restantes(self):
        return None      # None = sin límite