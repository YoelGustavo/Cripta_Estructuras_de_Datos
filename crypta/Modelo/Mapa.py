from crypta.Modelo.Sala import Sala
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector
from crypta.estructuras.Cola import Cola
from crypta.estructuras.ordenamiento import ordenar


class Mapa:
    def __init__(self):
        self._salas = ArbolBusqueda()

    def cargar_desde_json(self, salas_json):
        pares = Vector()

        for datos in salas_json:
            sala = Sala(
                id_sala=datos["id"],
                nombre=datos["nombre"],
                salidas=datos.get("salidas") or {}
            )

            pares.agregar(
                (sala.id, sala)
            )

        ordenar(
            pares,
            clave=lambda par: par[0]
        )

        self._salas = ArbolBusqueda.desde_ordenados(
            pares
        )

        self._compartir_puertas()
        self._enlazar_salas_destino()

    def obtener_sala(self, id_sala):
        return self._salas.obtener(id_sala)

    def contiene_sala(self, id_sala):
        return self._salas.contiene(id_sala)

    def cantidad_salas(self):
        return len(self._salas)

    def obtener_vecinas(self, id_sala):
        sala = self.obtener_sala(id_sala)

        if sala is None:
            return Vector()

        vecinas = Vector()

        for puerta in sala.salidas.values():
            id_vecina = puerta.sala_destino

            vecina = self.obtener_sala(id_vecina)

            if vecina is not None:
                vecinas.agregar(vecina)

        return vecinas

    def asignar_contenidos(self, contenidos_json):
        for datos in contenidos_json:
            id_sala = datos["sala"]

            sala = self.obtener_sala(id_sala)

            if sala is not None:
                sala.asignar_contenido(datos)

    def obtener_cercanas(self, id_sala, limite=10):
        if limite < 1:
            return Vector()

        sala_inicial = self.obtener_sala(id_sala)

        if sala_inicial is None:
            raise ValueError(
                f"No existe la sala {id_sala}"
            )

        resultado = Vector()
        pendientes = Cola()
        visitadas = ArbolBusqueda()

        pendientes.encolar(id_sala)
        visitadas.insertar(id_sala, True)

        while not pendientes.esta_vacia() and len(resultado) < limite:
            actual_id = pendientes.desencolar()
            actual = self.obtener_sala(actual_id)

            if actual is None:
                continue

            resultado.agregar(actual)

            vecinas = self.obtener_vecinas(actual_id)

            for i in range(len(vecinas)):
                vecina = vecinas.obtener(i)

                if vecina is not None:
                    if not visitadas.contiene(vecina.id):
                        visitadas.insertar(vecina.id, True)
                        pendientes.encolar(vecina.id)

        return resultado

    def obtener_todas(self):
        salas = Vector()

        for clave, sala in self._salas.en_orden():
            salas.agregar(sala)

        return salas

    def _compartir_puertas(self):
        salas = self.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            for direccion, puerta in sala.salidas.items():
                destino = self.obtener_sala(
                    puerta.sala_destino
                )

                if destino is None:
                    continue

                for puerta_destino in destino.salidas.values():

                    if puerta_destino.sala_destino == sala.id:
                        puerta.compartir_estado_con(
                            puerta_destino
                        )
                        break

    def _enlazar_salas_destino(self):
        salas = self.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            for puerta in sala.salidas.values():
                puerta.sala_destino_ref = self.obtener_sala(
                    puerta.sala_destino
                )