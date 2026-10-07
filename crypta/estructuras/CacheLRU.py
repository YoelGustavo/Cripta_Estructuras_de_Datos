from crypta.estructuras.ArbolBusqueda import ArbolBusqueda

class CacheLRU:
    def __init__(self, capacidad=25):
        if capacidad <= 0:
            raise ValueError(
                "La capacidad debe ser mayor que 0"
            )

        self._capacidad = capacidad

        # Por ahora dejamos estas partes como están.
        self._datos = {}
        self._ultimo_acceso = {}

        # id -> cantidad de instancias que usan la ficha.
        self._en_uso = ArbolBusqueda()

        self._contador = 0

    def _registrar_acceso(self, id_tipo):
        self._contador += 1
        self._ultimo_acceso[id_tipo] = self._contador

    def contiene(self, id_tipo):
        return id_tipo in self._datos

    def obtener(self, id_tipo):
        ficha = self._datos.get(id_tipo)

        if ficha is not None:
            self._registrar_acceso(id_tipo)

        return ficha

    def insertar(self, id_tipo, ficha):
        # Si ya existe, actualizamos la ficha.
        if id_tipo in self._datos:
            self._datos[id_tipo] = ficha
            self._registrar_acceso(id_tipo)
            return None

        desalojada = None

        if len(self._datos) >= self._capacidad:
            desalojada = self._desalojar_si_es_posible()

        self._datos[id_tipo] = ficha
        self._registrar_acceso(id_tipo)

        return desalojada

    def _desalojar_si_es_posible(self):
        candidato = None
        acceso_mas_antiguo = None

        for id_tipo in self._datos:

            if self.esta_en_uso(id_tipo):
                continue

            acceso = self._ultimo_acceso[id_tipo]

            if (
                candidato is None
                or acceso < acceso_mas_antiguo
            ):
                candidato = id_tipo
                acceso_mas_antiguo = acceso

        # Todas las fichas están protegidas.
        # Permitimos superar temporalmente la capacidad.
        if candidato is None:
            return None

        ficha = self._datos.pop(candidato)
        self._ultimo_acceso.pop(candidato)

        return candidato, ficha

    def marcar_en_uso(self, id_tipo):
        if id_tipo in self._datos:
            cantidad = self._en_uso.obtener(
                id_tipo,
                0
            )

            self._en_uso.insertar(
                id_tipo,
                cantidad + 1
            )

    def liberar(self, id_tipo):
        cantidad = self._en_uso.obtener(
            id_tipo,
            0
        )

        if cantidad <= 1:
            self._en_uso.eliminar(id_tipo)
        else:
            self._en_uso.insertar(
                id_tipo,
                cantidad - 1
            )

    def esta_en_uso(self, id_tipo):
        return self._en_uso.obtener(
            id_tipo,
            0
        ) > 0

    def cantidad(self):
        return len(self._datos)

    def capacidad(self):
        return self._capacidad

    def esta_llena(self):
        return len(self._datos) >= self._capacidad