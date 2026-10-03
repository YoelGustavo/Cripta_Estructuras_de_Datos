from abc import ABC, abstractmethod
from typing import Any


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