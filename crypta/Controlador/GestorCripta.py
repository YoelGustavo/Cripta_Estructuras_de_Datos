from crypta.Modelo.Mapa import Mapa


class GestorCripta:

    def __init__(self, fuente, almacen):
        self._fuente = fuente
        self._almacen = almacen

        # El esqueleto TAL COMO LLEGÓ del servicio (la lista de dict del
        # JSON). Es lo que se persiste: el JSON original se puede guardar
        # directo; los objetos del modelo (Sala, Puerta) no.
        self._esqueleto_json = None

    def cargar(self, cripta_id):
        # Necesitamos los datos generales para conocer
        # la versión actual de la cripta.
        datos_cripta = self._fuente.obtener_cripta(
            cripta_id
        )

        version = datos_cripta["version"]

        # Intentamos recuperar una copia persistida que
        # corresponda exactamente a esta versión.
        guardada = self._almacen.cargar_cripta(
            cripta_id,
            version
        )

        if guardada is not None:
            self._esqueleto_json = guardada.get("esqueleto") or ()

            mapa = Mapa()

            mapa.cargar_desde_json(
                self._esqueleto_json
            )

            mapa.asignar_contenidos(
                guardada.get("contenidos") or ()
            )

            return datos_cripta, mapa, True

        # No existe una copia válida.
        # Descargamos todas las páginas del esqueleto.
        esqueleto = []

        for numero_pagina in range(
            1,
            datos_cripta["paginas"] + 1
        ):
            pagina = (
                self._fuente.obtener_pagina_salas(
                    cripta_id,
                    numero_pagina
                )
            )

            esqueleto.extend(
                pagina.get("salas") or ()
            )

        self._esqueleto_json = esqueleto

        mapa = Mapa()

        mapa.cargar_desde_json(
            esqueleto
        )

        return datos_cripta, mapa, False

    def persistir(
        self,
        cripta_id,
        datos_cripta,
        mapa
    ):
        if self._esqueleto_json is None:
            raise ValueError("Primero hay que cargar la cripta con cargar()")

        contenidos = []

        # Para persistencia necesitamos TODAS las salas,
        # no solamente las alcanzadas por un recorrido
        # de cercanía.
        salas = mapa.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            if sala.contenido_cargado():
                contenidos.append(
                    sala.contenido
                )

        # Antes se armaba el esqueleto con sala.salidas, que eran objetos
        # Puerta: json no sabe guardarlos y persistir se caía con
        # "Object of type Puerta is not JSON serializable". Además se
        # habría guardado el estado ACTUAL de las puertas (abiertas por el
        # jugador) y no el de la cripta. Se guarda el esqueleto original.
        self._almacen.guardar_cripta(
            cripta_id,
            datos_cripta["version"],
            self._esqueleto_json,
            contenidos
        )