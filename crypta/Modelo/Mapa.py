from crypta.Modelo.Sala import Sala
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector
from crypta.estructuras.Cola import Cola


class Mapa:
    def __init__(self):
        self._salas = ArbolBusqueda()

    def cargar_desde_json(self, salas_json):
        pares = Vector()

        # El API entrega las salas por páginas.
        # Convertimos cada dato JSON en un objeto del modelo.
        for datos in salas_json:
            sala = Sala(
                id_sala=datos["id"],
                nombre=datos["nombre"],
                salidas=datos["salidas"]
            )

            # El árbol necesita pares (clave, valor)
            pares.agregar((sala.id, sala))

        # Las salas del esqueleto vienen ordenadas por id.
        # Aprovechamos el constructor balanceado en vez de insertarlas
        # una por una.
        self._salas = ArbolBusqueda.desde_ordenados(pares)

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