from crypta.Modelo.Mapa import Mapa


class GestorCripta:

    def __init__(self, fuente, almacen):
        self._fuente = fuente
        self._almacen = almacen

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
            mapa = Mapa()

            mapa.cargar_desde_json(
                guardada.get(
                    "esqueleto",
                    []
                )
            )

            mapa.asignar_contenidos(
                guardada.get(
                    "contenidos",
                    []
                )
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
                pagina.get("salas", [])
            )

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
        esqueleto = []
        contenidos = []

        # Para persistencia necesitamos TODAS las salas,
        # no solamente las alcanzadas por un recorrido
        # de cercanía.
        salas = mapa.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            esqueleto.append({
                "id": sala.id,
                "nombre": sala.nombre,
                "salidas": sala.salidas
            })

            if sala.contenido_cargado():
                contenidos.append(
                    sala.contenido
                )

        self._almacen.guardar_cripta(
            cripta_id,
            datos_cripta["version"],
            esqueleto,
            contenidos
        )