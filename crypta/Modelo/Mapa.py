from crypta.Modelo.Sala import Sala
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector
from crypta.estructuras.Cola import Cola
from crypta.estructuras.ordenamiento import ordenar


class Mapa:
    def __init__(self):
        self._salas = ArbolBusqueda()
        self._por_indice = Vector()

    def cargar_desde_json(self, salas_json):
        salas = Vector()

        for datos in salas_json:
            salas.agregar(
                Sala(
                    id_sala=datos["id"],
                    nombre=datos["nombre"],
                    salidas=datos.get("salidas")
                )
            )

        self.cargar_salas(salas)

    def cargar_salas(self, salas):
        pares = Vector()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            pares.agregar(
                (sala.id, sala)
            )

        ordenar(
            pares,
            clave=lambda par: par[0]
        )

        for i in range(len(pares) - 1):
            if pares.obtener(i)[0] == pares.obtener(i + 1)[0]:
                raise ValueError(f"La sala {pares.obtener(i)[0]} está repetida")

        self._salas = ArbolBusqueda.desde_ordenados(
            pares
        )

        self._compartir_puertas()
        self._enlazar_salas_destino()
        self._asignar_indices_y_entradas()

    def obtener_sala(self, id_sala):
        return self._salas.obtener(id_sala)

    def contiene_sala(self, id_sala):
        return self._salas.contiene(id_sala)

    def cantidad_salas(self):
        return len(self._salas)

    def sala_por_indice(self, indice):
        """La sala con ese índice denso, 0..V-1 (FR-014, FR-036)."""
        return self._por_indice.obtener(indice)

    def obtener_vecinas(self, id_sala, solo_abiertas=False):
        sala = self.obtener_sala(id_sala)

        if sala is None:
            return Vector()

        vecinas = Vector()
        puertas = sala.puertas(solo_abiertas)

        for i in range(len(puertas)):
            vecina = puertas.obtener(i).sala_destino_ref

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
            puertas = sala.puertas()

            for j in range(len(puertas)):
                puerta = puertas.obtener(j)

                destino = self.obtener_sala(
                    puerta.sala_destino
                )

                if destino is not None:
                    puertas_destino = destino.puertas()

                    for k in range(len(puertas_destino)):
                        puerta_destino = puertas_destino.obtener(k)

                        if puerta_destino.sala_destino == sala.id:
                            # Valida y une los costos de los dos lados
                            # (FR-002, FR-010).
                            puerta.compartir_estado_con(
                                puerta_destino, sala, destino
                            )
                            break

                # Extremos de la salida (FR-018). Una salida hacia una sala
                # que no existe queda con (sala, None).
                if puerta.estado.extremos is None:
                    puerta.estado.extremos = (sala, destino)

    def _asignar_indices_y_entradas(self):
        """Índice denso de cada sala según el recorrido en orden y sus
        entradas (salidas y→x), en O(V + E) (FR-014, FR-036)."""
        salas = self.obtener_todas()
        self._por_indice = Vector(max(1, len(salas)))

        for i in range(len(salas)):
            sala = salas.obtener(i)
            sala.indice = i
            sala.entradas = Vector()
            self._por_indice.agregar(sala)

        for i in range(len(salas)):
            origen = salas.obtener(i)
            puertas = origen.puertas()

            for j in range(len(puertas)):
                puerta = puertas.obtener(j)
                destino = puerta.sala_destino_ref

                if destino is not None:
                    destino.entradas.agregar((puerta, origen))

    def _enlazar_salas_destino(self):
        salas = self.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)
            puertas = sala.puertas()

            for j in range(len(puertas)):
                puerta = puertas.obtener(j)

                puerta.sala_destino_ref = self.obtener_sala(
                    puerta.sala_destino
                )