"""Reconstrucción de un estado pasado (capacidad 004; research D2, D7, D8).

Elegida: **hacia adelante sobre el punto de control y deshacer después**.
Sobre el punto anterior se re-ejecutan a lo sumo K acciones con
`ejecutar_comando` (inyectado como `reejecutar`, así el Modelo no importa el
Controlador), se arma el resumen y se deshacen con `Historial.deshacer_ultima`,
el mecanismo del pergamino de P1. Lo que el historial no restaura lo guarda y
lo devuelve el `Sello` (D8). La partida viva solo se lee (FR-407): de ella sale
el contenido de las salas que el punto todavía no tenía (D7), sin red.
"""

from crypta.Modelo.Bitacora import Bitacora
from crypta.Modelo.LineaDeTiempo import ACCION, AJUSTE
from crypta.Modelo.Partida import AccionInvalida
from crypta.Modelo.Resumen import armar_resumen
from crypta.estructuras.Vector import Vector


class ReconstruccionFallida(RuntimeError):
    """Re-ejecutar una entrada de la línea no dio lo mismo que en la partida:
    es un error de programa, no del jugador."""


class Sello:
    """Lo que el historial de P1 no restaura (research D8), tomado del punto
    antes de re-ejecutar y devuelto después de deshacer.

    No restaura la carga de contenido de las salas que la consulta cargó:
    quedan cargadas (decisión del grupo, research D7)."""

    def __init__(self, partida):
        self.partida = partida
        self.terminada = partida.terminada
        self.resultado = partida.resultado
        self.puerta_de_salida_abierta = partida.puerta_de_salida_abierta
        self.enemigos_derrotados = partida.enemigos_derrotados

        inventario = partida.jugador.inventario
        self.pergaminos = inventario.cantidad_pergaminos()
        self.actual = inventario.nodo_actual()

        # El pergamino de P1 no rebobina el número de secuencia de la agenda.
        self.secuencia = partida.agenda.siguiente_secuencia

        # (sala, estado de sus pergaminos) de cada sala en la que el jugador
        # está o entra: a lo sumo K + 1.
        self.salas = Vector()

    def anotar_sala(self, sala):
        for i in range(len(self.salas)):
            if self.salas.obtener(i)[0] is sala:
                return

        self.salas.agregar((sala, sala.estado_de_pergaminos()))

    def restaurar(self):
        partida = self.partida
        partida.terminada = self.terminada
        partida.resultado = self.resultado
        partida.puerta_de_salida_abierta = self.puerta_de_salida_abierta
        partida.enemigos_derrotados = self.enemigos_derrotados

        inventario = partida.jugador.inventario
        inventario.fijar_pergaminos(self.pergaminos)
        inventario.poner_nodo_actual(self.actual)

        partida.agenda.rebobinar_secuencia(self.secuencia)

        for i in range(len(self.salas)):
            sala, estado = self.salas.obtener(i)
            sala.restaurar_estado_de_pergaminos(estado)

        # La bitácora del punto no es estado: vuelve a estar vacía.
        partida.bitacora = Bitacora()

        # La búsqueda del cazador del punto es una caché: después de deshacer
        # se invalida, como hace el pergamino (FR-020).
        if partida._perseguidor is not None:
            partida._perseguidor.invalidar()


def consultar(linea, objetivo, partida_viva, reejecutar):
    """El `Resumen` del estado que pide `objetivo` (FR-401, FR-402, FR-421).

    Re-ejecuta y deshace a lo sumo K acciones (FR-423), examina un solo punto
    de control (FR-425) y no cambia la partida viva ni el punto (FR-407,
    salvo las salas que carga, D7)."""
    linea.puntos_examinados = 0
    linea.ultimas_reejecutadas = 0

    if objetivo.es_actual:
        return armar_resumen(partida_viva, objetivo.pedido)

    m = objetivo.acciones_completas
    punto = linea.punto_para(m)
    copia = punto.partida
    sello = Sello(copia)
    garantizar = _garantizar_desde_la_viva(punto, partida_viva, sello)

    siguiente = linea.posicion_de_accion(m + 1)
    hechas = 0

    try:
        sello.anotar_sala(copia.sala_actual())

        for i in range(punto.posicion, siguiente):
            hechas += _reejecutar(copia, linea.entradas.obtener(i), reejecutar,
                                  garantizar, sello)

        if objetivo.tope is not None:
            copia.tope_tiempo = objetivo.tope
            hechas += _reejecutar(copia, linea.entradas.obtener(siguiente),
                                  reejecutar, garantizar, sello)

        resumen = armar_resumen(copia, objetivo.pedido)
    finally:
        copia.tope_tiempo = None

        for _ in range(hechas):
            copia.estado.historial.deshacer_ultima()

        sello.restaurar()

    linea.ultimas_reejecutadas = hechas
    return resumen


def _reejecutar(copia, entrada, reejecutar, garantizar, sello):
    """Re-ejecuta una entrada sobre la copia; devuelve 1 si fue una acción
    (dejó un `RegistroAccion` que hay que deshacer) y 0 si no."""
    if entrada.tipo == AJUSTE:
        raise ReconstruccionFallida(
            "La línea tiene un ajuste por pergamino: lo aplica la historia 2")

    sello.anotar_sala(copia.sala_actual())
    antes = copia.acciones_jugador

    try:
        reejecutar(copia, entrada.comando, garantizar)
    except (ValueError, RuntimeError, AccionInvalida) as error:
        raise ReconstruccionFallida(
            f"No se pudo repetir '{entrada.comando}' (acción #{entrada.numero_accion}, "
            f"instante {entrada.reloj}): {error}") from error

    hecha = copia.acciones_jugador - antes

    if hecha != (1 if entrada.tipo == ACCION else 0):
        raise ReconstruccionFallida(
            f"'{entrada.comando}' no dio la misma cantidad de acciones al repetirse")

    return hecha


def _garantizar_desde_la_viva(punto, partida_viva, sello):
    """El `garantizar_sala` de la re-ejecución (research D7): si la sala no
    tiene contenido en el punto, lo toma de la partida viva, que ya lo tiene
    porque el jugador entró en ella. Nunca hay red (FR-407)."""
    copia = punto.partida

    def garantizar(id_sala):
        sala = copia.mapa.obtener_sala(id_sala)

        if sala is None:
            raise ValueError(f"No existe la sala {id_sala}")

        if sala.contenido_cargado():
            sello.anotar_sala(sala)
            return sala

        viva = partida_viva.mapa.obtener_sala(id_sala)

        if viva is None or not viva.contenido_cargado():
            raise RuntimeError(
                f"La sala {id_sala} no tiene contenido en la partida: la línea de "
                f"tiempo no puede pedirlo a la red")

        sala.asignar_contenido(viva.contenido)
        punto.salas_cargadas.agregar(id_sala)
        return sala

    return garantizar
