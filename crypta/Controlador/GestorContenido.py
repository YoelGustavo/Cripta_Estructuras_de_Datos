from concurrent.futures import ThreadPoolExecutor

from crypta.estructuras.Cola import Cola
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.ListaSimple import ListaSimple
from crypta.estructuras.Vector import Vector


# §5.1: la precarga es una apuesta (quizá el jugador nunca va a esas
# salas). Nunca gasta las últimas solicitudes del presupuesto: esas quedan
# para lo indispensable, la sala a la que el jugador SÍ quiere entrar.
RESERVA_PRECARGA = 2


class GestorContenido:

    def __init__(self, fuente, mapa, cripta_id, repositorio=None):
        self._fuente = fuente
        self._mapa = mapa
        self._cripta_id = cripta_id

        # Si se da, al llegar el contenido de unas salas se piden JUNTAS
        # (en lotes de 10) las fichas que usan. Sin esto, la Partida
        # pediría cada ficha por separado, una solicitud por ficha.
        self._repositorio = repositorio

        # Permite realizar solicitudes HTTP anticipadas
        # sin bloquear inmediatamente el juego.
        self._ejecutor = ThreadPoolExecutor(max_workers=2)

        # Solicitudes iniciadas pero todavía no incorporadas.
        # La cola conserva el orden en que fueron iniciadas.
        self._pendientes = Cola()

        # Número de secuencia para mantener un orden
        # determinista entre solicitudes.
        self._siguiente_secuencia = 0

    # =========================================================
    # CARGA NORMAL DE CONTENIDO
    # =========================================================

    def cargar_salas(self, salas):
        ids_pendientes = []

        for i in range(len(salas)):
            sala = salas.obtener(i)

            # Una sala ya cargada no se vuelve a solicitar.
            if not sala.contenido_cargado():
                ids_pendientes.append(sala.id)

            # El servicio permite máximo 10 salas por consulta.
            if len(ids_pendientes) == 10:
                self._solicitar_lote(ids_pendientes)
                ids_pendientes = []

        # Puede quedar un último lote de menos de 10.
        if len(ids_pendientes) > 0:
            self._solicitar_lote(ids_pendientes)

    def _solicitar_lote(self, ids):
        respuesta = self._fuente.obtener_contenido(
            self._cripta_id,
            ids
        )

        self._mapa.asignar_contenidos(
            respuesta["contenido"]
        )

        self._resolver_fichas(respuesta["contenido"])

    def _resolver_fichas(self, contenidos):
        """Las fichas de todo lo que trae ese contenido, en lotes de 10.
        Las que ya están en memoria o en disco no se piden."""
        if self._repositorio is not None:
            self._repositorio.resolver_contenidos(contenidos)


    def precargar_desde(self, id_sala):
        self.cargar_salas(
            self._salas_para_precargar(id_sala)
        )

    def _salas_para_precargar(self, id_sala):
        """Hasta 10 salas, por cercanía (BFS desde id_sala), que haga falta
        pedir: ni cargadas ni ya pedidas en una solicitud anticipada.

        La usan las DOS precargas (normal y anticipada), así las dos
        eligen igual. Las salas que no hace falta pedir no ocupan lugar en
        el lote, pero se sigue explorando a través de ellas: si no, después
        del primer lote no se encontraría ninguna sala nueva."""

        sala_actual = self._mapa.obtener_sala(id_sala)

        if sala_actual is None:
            raise ValueError(
                f"No existe la sala {id_sala}"
            )

        pendientes = Cola()
        visitadas = ArbolBusqueda()
        salas_nuevas = Vector()

        pendientes.encolar(id_sala)
        visitadas.insertar(id_sala, True)

        while (
            not pendientes.esta_vacia()
            and len(salas_nuevas) < 10
        ):
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

    # =========================================================
    # PRECARGA ASÍNCRONA
    # =========================================================

    def _hay_presupuesto_para_precargar(self):
        # Las fuentes de las pruebas no tienen presupuesto: sin el método,
        # getattr da una función que devuelve None (= sin límite).
        restantes = getattr(self._fuente, "solicitudes_restantes", lambda: None)()
        return restantes is None or restantes > RESERVA_PRECARGA

    def precargar_async(self, id_sala):
        if not self._hay_presupuesto_para_precargar():
            return None

        salas = self._salas_para_precargar(id_sala)

        ids = []

        for i in range(len(salas)):
            ids.append(salas.obtener(i).id)

        # No hay nada nuevo que solicitar.
        if len(ids) == 0:
            return None

        secuencia = self._siguiente_secuencia
        self._siguiente_secuencia += 1

        # La solicitud se ejecuta en otro hilo.
        futuro = self._ejecutor.submit(
            self._fuente.obtener_contenido,
            self._cripta_id,
            ids
        )

        # Conservamos la solicitud junto con su secuencia.
        self._pendientes.encolar(
            (secuencia, ids, futuro)
        )

        return secuencia

    # =========================================================
    # BÚSQUEDA DE SOLICITUDES PENDIENTES
    # =========================================================

    def _buscar_pendiente_de_sala(self, id_sala):
        for pendiente in self._pendientes:
            secuencia, ids, futuro = pendiente

            if id_sala in ids:
                return futuro

        return None

    # =========================================================
    # INCORPORACIÓN DETERMINISTA
    # =========================================================

    def procesar_pendientes(self):
        """
        Incorpora las respuestas terminadas respetando el orden
        en que fueron iniciadas las solicitudes.
        """

        while not self._pendientes.esta_vacia():

            secuencia, ids, futuro = self._pendientes.ver_frente()

            # Si la primera todavía no terminó, no incorporamos
            # respuestas posteriores aunque ya estén listas.
            if not futuro.done():
                return

            self._incorporar_la_primera()

    def _incorporar_la_primera(self):
        """Saca la primera solicitud anticipada (espera si no terminó) y
        agrega su contenido al mapa.

        Si FALLÓ (sin red, presupuesto agotado...), se descarta y el juego
        sigue: esas salas quedan sin cargar y garantizar_sala las pedirá
        solo si el jugador de verdad entra. Antes, la solicitud fallida se
        quedaba al frente de la cola y su error se repetía en cada turno."""
        secuencia, ids, futuro = self._pendientes.desencolar()

        try:
            respuesta = futuro.result()
        except RuntimeError:
            return

        self._mapa.asignar_contenidos(
            respuesta["contenido"]
        )

        # Las fichas son una apuesta igual que la precarga: si fallan, se
        # piden después, cuando de verdad se entra (garantizar_sala).
        try:
            self._resolver_fichas(respuesta["contenido"])
        except RuntimeError:
            pass

    # =========================================================
    # ESPERAR UNA SALA QUE YA VIENE EN CAMINO
    # =========================================================

    def _esperar_hasta_sala(self, id_sala):
        """
        Espera e incorpora solicitudes pendientes en su orden
        hasta que el contenido de id_sala esté disponible.

        La espera es tiempo real y NO modifica el reloj virtual.
        """

        while not self._pendientes.esta_vacia():

            # Esperamos la solicitud que corresponde incorporar
            # primero según nuestro orden determinista.
            self._incorporar_la_primera()

            sala = self._mapa.obtener_sala(id_sala)

            if sala.contenido_cargado():
                return

    # =========================================================
    # GARANTIZAR CONTENIDO ANTES DEL MOVIMIENTO
    # =========================================================

    def garantizar_sala(self, id_sala):
        sala = self._mapa.obtener_sala(id_sala)

        if sala is None:
            raise ValueError(
                f"No existe la sala {id_sala}"
            )

        # Caso 1: el contenido ya está disponible (no se hace nada).

        # Caso 2:
        # La sala ya está siendo descargada por una
        # solicitud anticipada.
        if (not sala.contenido_cargado()
                and self._buscar_pendiente_de_sala(id_sala) is not None):
            self._esperar_hasta_sala(id_sala)

        # Caso 3:
        # La sala no está cargada ni venía en una solicitud (o venía en
        # una anticipada que falló): se pide sola.
        if not sala.contenido_cargado():
            self._solicitar_lote([id_sala])

        # Nunca permitimos que el jugador entre a una sala
        # cuyo contenido siga siendo desconocido.
        if not sala.contenido_cargado():
            raise RuntimeError(
                f"No se pudo cargar el contenido de la sala {id_sala}"
            )

        # Las fichas de la sala, ANTES de que la Partida las use. Si el
        # contenido ya estaba (copia local, o una precarga cuyas fichas
        # fallaron), aquí se completan. Lo que ya está en memoria o en
        # disco no gasta red. Si falla, falla ANTES de la acción: la
        # partida no queda a medias.
        lote = ListaSimple()
        lote.agregar_al_final(sala.contenido)
        self._resolver_fichas(lote)

        return sala

    def cerrar(self):
        """Espera las solicitudes anticipadas en camino y apaga el hilo."""
        self._ejecutor.shutdown(wait=True)