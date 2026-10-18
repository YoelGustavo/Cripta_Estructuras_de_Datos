from concurrent.futures import ThreadPoolExecutor

from crypta.estructuras.Cola import Cola
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.ListaSimple import ListaSimple
from crypta.estructuras.Vector import Vector


RESERVA_PRECARGA = 2

LIMITE_VISITAS_PRECARGA = 100


class GestorContenido:

    def __init__(self, fuente, mapa, cripta_id, repositorio=None):
        self._fuente = fuente
        self._mapa = mapa
        self._cripta_id = cripta_id

        self._repositorio = repositorio

        self._sin_cargar = 0
        todas = mapa.obtener_todas()

        for i in range(len(todas)):
            if not todas.obtener(i).contenido_cargado():
                self._sin_cargar += 1

        self._ejecutor = ThreadPoolExecutor(max_workers=2)

        self._pendientes = Cola()

        self._siguiente_secuencia = 0

    def cargar_salas(self, salas):
        ids_pendientes = []

        for i in range(len(salas)):
            sala = salas.obtener(i)

            if not sala.contenido_cargado():
                ids_pendientes.append(sala.id)

            if len(ids_pendientes) == 10:
                self._solicitar_lote(ids_pendientes)
                ids_pendientes = []

        if len(ids_pendientes) > 0:
            self._solicitar_lote(ids_pendientes)

    def _solicitar_lote(self, ids):
        respuesta = self._fuente.obtener_contenido(
            self._cripta_id,
            ids
        )

        self._asignar(respuesta["contenido"])
        self._resolver_fichas(respuesta["contenido"])

    def _asignar(self, contenidos):
        antes = self._contar_sin_cargar(contenidos)
        self._mapa.asignar_contenidos(contenidos)
        self._sin_cargar -= antes - self._contar_sin_cargar(contenidos)

    def _contar_sin_cargar(self, contenidos):
        cuantas = 0

        for contenido in contenidos:
            sala = self._mapa.obtener_sala(contenido["sala"])

            if sala is not None and not sala.contenido_cargado():
                cuantas += 1

        return cuantas

    def _resolver_fichas(self, contenidos):
        if self._repositorio is not None:
            self._repositorio.resolver_contenidos(contenidos)


    def precargar_desde(self, id_sala):
        self.cargar_salas(
            self._salas_para_precargar(id_sala)
        )

    def _salas_para_precargar(self, id_sala):

        sala_actual = self._mapa.obtener_sala(id_sala)

        if sala_actual is None:
            raise ValueError(
                f"No existe la sala {id_sala}"
            )

        pendientes = Cola()
        visitadas = ArbolBusqueda()
        salas_nuevas = Vector()

        if self._sin_cargar == 0:
            return salas_nuevas

        pendientes.encolar(id_sala)
        visitadas.insertar(id_sala, True)
        revisadas = 0

        while (
            not pendientes.esta_vacia()
            and len(salas_nuevas) < 10
            and revisadas < LIMITE_VISITAS_PRECARGA
        ):
            revisadas += 1
            actual_id = pendientes.desencolar()

            actual = self._mapa.obtener_sala(
                actual_id
            )

            if actual is None:
                continue

            if (
                not actual.contenido_cargado()
                and self._buscar_pendiente_de_sala(actual.id) is None
            ):
                salas_nuevas.agregar(actual)

            puertas = actual.puertas()

            for i in range(len(puertas)):
                vecino_id = puertas.obtener(i).sala_destino

                if not visitadas.contiene(vecino_id):
                    visitadas.insertar(
                        vecino_id,
                        True
                    )
                    pendientes.encolar(
                        vecino_id
                    )

        return salas_nuevas


    def _hay_presupuesto_para_precargar(self):
        restantes = getattr(self._fuente, "solicitudes_restantes", lambda: None)()
        return restantes is None or restantes > RESERVA_PRECARGA

    def precargar_async(self, id_sala):
        if not self._hay_presupuesto_para_precargar():
            return None

        salas = self._salas_para_precargar(id_sala)

        ids = []

        for i in range(len(salas)):
            ids.append(salas.obtener(i).id)

        if len(ids) == 0:
            return None

        secuencia = self._siguiente_secuencia
        self._siguiente_secuencia += 1

        futuro = self._ejecutor.submit(
            self._fuente.obtener_contenido,
            self._cripta_id,
            ids
        )

        self._pendientes.encolar(
            (secuencia, ids, futuro)
        )

        return secuencia

    def _buscar_pendiente_de_sala(self, id_sala):
        for pendiente in self._pendientes:
            secuencia, ids, futuro = pendiente

            if id_sala in ids:
                return futuro

        return None

    def procesar_pendientes(self):

        while not self._pendientes.esta_vacia():

            secuencia, ids, futuro = self._pendientes.ver_frente()
            if not futuro.done():
                return

            self._incorporar_la_primera()

    def _incorporar_la_primera(self):
        secuencia, ids, futuro = self._pendientes.desencolar()

        try:
            respuesta = futuro.result()
        except RuntimeError:
            return

        self._asignar(respuesta["contenido"])
        try:
            self._resolver_fichas(respuesta["contenido"])
        except RuntimeError:
            pass

    def _esperar_hasta_sala(self, id_sala):

        while not self._pendientes.esta_vacia():

            self._incorporar_la_primera()

            sala = self._mapa.obtener_sala(id_sala)

            if sala.contenido_cargado():
                return


    def garantizar_sala(self, id_sala):
        sala = self._mapa.obtener_sala(id_sala)

        if sala is None:
            raise ValueError(
                f"No existe la sala {id_sala}"
            )

        if (not sala.contenido_cargado()
                and self._buscar_pendiente_de_sala(id_sala) is not None):
            self._esperar_hasta_sala(id_sala)

        if not sala.contenido_cargado():
            self._solicitar_lote([id_sala])

        if not sala.contenido_cargado():
            raise RuntimeError(
                f"No se pudo cargar el contenido de la sala {id_sala}"
            )

        lote = ListaSimple()
        lote.agregar_al_final(sala.contenido)
        self._resolver_fichas(lote)

        return sala

    def cerrar(self):
        self._ejecutor.shutdown(wait=True)