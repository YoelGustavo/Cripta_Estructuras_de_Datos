
from crypta.Modelo.Mapa import Mapa


class GestorCripta:

    def __init__(self, fuente, almacen):
        self._fuente = fuente
        self._almacen = almacen

        # Esqueleto original recibido de la fuente.
        self._esqueleto_json = None

    def cargar(self, cripta_id):
        # Obtener los datos generales de la cripta.
        datos_cripta = self._fuente.obtener_cripta(
            cripta_id
        )

        version = datos_cripta["version"]

        # Intentar recuperar el esqueleto y los
        # contenidos previamente almacenados.
        guardada = self._almacen.cargar_cripta(
            cripta_id,
            version
        )

        if guardada is not None:
            self._esqueleto_json = (
                guardada.get("esqueleto") or ()
            )

            mapa = Mapa()

            mapa.cargar_desde_json(
                self._esqueleto_json
            )

            mapa.asignar_contenidos(
                guardada.get("contenidos") or ()
            )

            return datos_cripta, mapa, True

        # No existe una copia válida.
        # Recuperar todas las páginas del esqueleto.
        esqueleto = []

        for numero_pagina in range(
            1,
            datos_cripta["paginas"] + 1
        ):
            pagina = self._fuente.obtener_pagina_salas(
                cripta_id,
                numero_pagina
            )

            esqueleto.extend(
                pagina.get("salas") or ()
            )

        self._esqueleto_json = esqueleto

        mapa = Mapa()
        mapa.cargar_desde_json(esqueleto)

        return datos_cripta, mapa, False

    def persistir(
        self,
        cripta_id,
        datos_cripta,
        mapa
    ):
        if self._esqueleto_json is None:
            raise ValueError(
                "Primero hay que cargar la cripta con cargar()"
            )

        contenidos = []

        # Guardamos todas las salas cuyo contenido
        # ya está disponible.
        salas = mapa.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            if sala.contenido_cargado():
                contenidos.append(
                    sala.contenido
                )

        # Guardar el esqueleto original, los contenidos
        # y ahora también los datos generales completos.
        self._almacen.guardar_cripta(
            cripta_id,
            datos_cripta["version"],
            self._esqueleto_json,
            contenidos,
            datos_generales=datos_cripta
        )