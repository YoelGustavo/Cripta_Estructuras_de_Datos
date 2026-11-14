from crypta.Adaptadores.FuenteDatos import LlavesNoDisponibles
from crypta.Adaptadores.FuenteHTTP import PresupuestoAgotado
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.ResultadoVerificacion import NoVerificable


class GestorCripta:

    def __init__(self, fuente, almacen):
        self._fuente = fuente
        self._almacen = almacen

        self._esqueleto_json = None
        # Ubicación de las llaves (capacidad 003): la respuesta del servicio
        # tal cual, de la copia local o de la red; None si aún no se tiene.
        self._llaves_json = None

    def cargar(self, cripta_id):
        datos_cripta = self._fuente.obtener_cripta(
            cripta_id
        )

        version = datos_cripta["version"]

        guardada = self._almacen.cargar_cripta(
            cripta_id,
            version
        )

        if guardada is not None:
            self._esqueleto_json = (
                guardada.get("esqueleto") or ()
            )
            # Misma versión: las llaves guardadas valen (FR-323).
            self._llaves_json = guardada.get("llaves")

            mapa = Mapa()

            mapa.cargar_desde_json(
                self._esqueleto_json
            )

            mapa.asignar_contenidos(
                guardada.get("contenidos") or ()
            )

            return datos_cripta, mapa, True

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
        self._llaves_json = None

        mapa = Mapa()
        mapa.cargar_desde_json(esqueleto)

        return datos_cripta, mapa, False

    def cargar_llaves(self, cripta_id):
        """La respuesta de ubicación de llaves: la de la copia local si la
        versión coincide (sin solicitud), o la de la fuente (FR-322,
        FR-323). Si no se puede obtener devuelve `NoVerificable` con el
        motivo (FR-324). Hay que llamar antes a `cargar`."""
        if self._llaves_json is not None:
            return self._llaves_json

        try:
            self._llaves_json = self._fuente.obtener_llaves(cripta_id)
        except LlavesNoDisponibles as error:
            return NoVerificable(str(error))
        except PresupuestoAgotado:
            return NoVerificable("presupuesto de solicitudes agotado")
        except RuntimeError as error:
            return NoVerificable(f"falla de red: {error}")

        return self._llaves_json

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

        salas = mapa.obtener_todas()

        for i in range(len(salas)):
            sala = salas.obtener(i)

            if sala.contenido_cargado():
                contenidos.append(
                    sala.contenido
                )

        self._almacen.guardar_cripta(
            cripta_id,
            datos_cripta["version"],
            self._esqueleto_json,
            contenidos,
            datos_generales=datos_cripta,
            llaves=self._llaves_json
        )
