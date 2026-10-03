class CacheLRU:

    def __init__(self, capacidad=25):
        if capacidad <= 0:
            raise ValueError(
                "La capacidad debe ser mayor que 0"
            )

        self._capacidad = capacidad

        # id -> ficha
        self._datos = {}

        # id -> número del último acceso
        self._ultimo_acceso = {}

        # IDs que no pueden desalojarse.
        self._en_uso = set()

        # Reloj lógico para ordenar accesos.
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
            desalojada = self._desalojar()

        self._datos[id_tipo] = ficha
        self._registrar_acceso(id_tipo)

        return desalojada

    def _desalojar(self):
        candidato = None
        acceso_mas_antiguo = None

        for id_tipo in self._datos:

            # Una ficha actualmente utilizada por el juego
            # no puede salir de la caché.
            if id_tipo in self._en_uso:
                continue

            acceso = self._ultimo_acceso[id_tipo]

            if (
                candidato is None
                or acceso < acceso_mas_antiguo
            ):
                candidato = id_tipo
                acceso_mas_antiguo = acceso

        if candidato is None:
            raise RuntimeError(
                "No se puede desalojar ninguna ficha: "
                "todas están en uso"
            )

        ficha = self._datos.pop(candidato)
        self._ultimo_acceso.pop(candidato)

        return candidato, ficha

    def marcar_en_uso(self, id_tipo):
        if id_tipo in self._datos:
            self._en_uso.add(id_tipo)

    def liberar(self, id_tipo):
        self._en_uso.discard(id_tipo)

    def esta_en_uso(self, id_tipo):
        return id_tipo in self._en_uso

    def cantidad(self):
        return len(self._datos)

    def capacidad(self):
        return self._capacidad

    def esta_llena(self):
        return len(self._datos) >= self._capacidad