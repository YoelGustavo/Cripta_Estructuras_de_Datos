"""--bench, sección AGENDA (§4.1 "qué ocurre a continuación").

Lo que el juego hace decenas de miles de veces: sacar el evento más
próximo y volver a programar a ese actor (§12: "con varios cientos de
eventos programados, ¿qué operación se ejecutará decenas de miles de
veces?"). Y, menos seguido, cancelar un evento (un enemigo muere, un
antídoto cancela el veneno).

Se mide la Agenda del juego (MonticuloMin + borrado perezoso) contra dos
alternativas DESCARTADAS, hechas aquí con el Vector del curso (§8 pide que
al menos una sección mida directamente la alternativa descartada):

  - Vector ordenado: el próximo evento queda al final, así sacarlo es O(1);
    pero programar tiene que buscar su lugar y correr a los demás: O(n).
  - Vector sin orden: programar es agregar al final, O(1); pero sacar el
    próximo obliga a revisarlos todos: O(n).

Las tres dan exactamente el mismo orden (lo comprueba tests/test_bench.py),
así que lo único que cambia es el costo.
"""

import random

from crypta.bench.medicion import cronometrar, formato_tiempo, medir, tabla
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Evento import Evento, evento_menor


# Intervalos típicos entre dos turnos: acción de 100 a velocidad 150, 100 y
# 90, y acción de 50 a velocidad 100 (§2.3).
INTERVALOS = (66, 100, 111, 50)

TAMANOS = (10, 100, 1000, 5000)
TAMANOS_RAPIDO = (10, 100)


# ======================================================================
# LAS ALTERNATIVAS DESCARTADAS
# ======================================================================

class AgendaVectorOrdenado:
    """Vector de MAYOR a menor: el próximo evento siempre está al final."""

    def __init__(self):
        self._eventos = Vector()
        self._secuencia = 0

    def __len__(self):
        return len(self._eventos)

    def programar(self, tiempo, tipo, objetivo=None):
        evento = Evento(tiempo, self._secuencia, tipo, objetivo)
        self._secuencia += 1

        # Buscar el lugar: después de todos los que son posteriores a él.
        i = 0
        while i < len(self._eventos) and evento_menor(evento, self._eventos.obtener(i)):
            i += 1

        self._eventos.insertar(i, evento)     # corre a los demás: O(n)
        return evento

    def siguiente(self):
        if len(self._eventos) == 0:
            return None

        return self._eventos.quitar_ultimo()  # O(1)

    def cancelar(self, evento):
        for i in range(len(self._eventos)):
            if self._eventos.obtener(i) is evento:
                self._eventos.quitar(i)       # O(n)
                return


class AgendaVectorSinOrden:
    """Vector sin ningún orden: hay que buscar el próximo cada vez."""

    def __init__(self):
        self._eventos = Vector()
        self._secuencia = 0

    def __len__(self):
        return len(self._eventos)

    def programar(self, tiempo, tipo, objetivo=None):
        evento = Evento(tiempo, self._secuencia, tipo, objetivo)
        self._secuencia += 1
        self._eventos.agregar(evento)         # O(1)
        return evento

    def siguiente(self):
        if len(self._eventos) == 0:
            return None

        menor = 0
        for i in range(1, len(self._eventos)):  # revisar todos: O(n)
            if evento_menor(self._eventos.obtener(i), self._eventos.obtener(menor)):
                menor = i

        return self._quitar(menor)

    def cancelar(self, evento):
        for i in range(len(self._eventos)):
            if self._eventos.obtener(i) is evento:
                self._quitar(i)
                return

    def _quitar(self, i):
        # Sin orden que cuidar: el último pasa al hueco y no se corre nada.
        evento = self._eventos.obtener(i)
        ultimo = self._eventos.quitar_ultimo()

        if i < len(self._eventos):
            self._eventos.asignar(i, ultimo)

        return evento


AGENDAS = (
    ("montículo (el juego)", Agenda),
    ("vector ordenado", AgendaVectorOrdenado),
    ("vector sin orden", AgendaVectorSinOrden),
)


# ======================================================================
# LA CARGA: COMO EN EL JUEGO
# ======================================================================

def llenar(agenda, cantidad, azar):
    """'cantidad' actores, cada uno con su próximo turno pendiente."""
    eventos = []

    for actor in range(cantidad):
        eventos.append(agenda.programar(azar.randrange(100), "turno", actor))

    return eventos


def hacer_turnos(agenda, cantidad, azar):
    """Lo que hace el ciclo del juego: sacar el próximo evento y volver a
    programar a su actor más adelante. Devuelve los eventos que salieron."""
    salieron = []

    for _ in range(cantidad):
        evento = agenda.siguiente()
        salieron.append(evento)
        agenda.programar(evento.tiempo + azar.choice(INTERVALOS), "turno",
                         evento.objetivo)

    return salieron


def costo_turno(clase, pendientes, turnos, repeticiones=3, semilla=1):
    """Segundos por turno con 'pendientes' eventos en la agenda. Llenarla
    no se mide: solo los turnos (la agenda queda siempre con la misma
    cantidad, porque cada turno saca uno y programa uno)."""
    azar = random.Random(semilla)
    agenda = clase()
    llenar(agenda, pendientes, azar)

    return medir(lambda: hacer_turnos(agenda, turnos, azar), repeticiones) / turnos


def costo_cancelar(clase, pendientes, cancelaciones, repeticiones=2, semilla=1):
    """Segundos por cancelación (por ejemplo, muere un enemigo). Cada vuelta
    necesita una agenda nueva (las canceladas ya no están), y llenar el
    vector ordenado es lento: por eso solo 2 vueltas."""
    mejor = None

    for vuelta in range(repeticiones):
        azar = random.Random(semilla + vuelta)
        agenda = clase()
        eventos = llenar(agenda, pendientes, azar)
        elegidos = azar.sample(eventos, cancelaciones)

        transcurrido = cronometrar(lambda: _cancelar_todos(agenda, elegidos))

        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    return mejor / cancelaciones


def _cancelar_todos(agenda, eventos):
    for evento in eventos:
        agenda.cancelar(evento)


def _turnos_para(pendientes):
    # Más turnos con agendas chicas (cada uno dura poco), menos con las
    # grandes (para que las alternativas lentas no tarden minutos).
    return max(100, min(1000, 500000 // pendientes))


# ======================================================================
# LA SECCIÓN DEL --bench
# ======================================================================

def ejecutar(rapido=False):
    """Mide y devuelve el texto de las dos tablas."""
    tamanos = TAMANOS_RAPIDO if rapido else TAMANOS
    encabezados = ("eventos pendientes",) + tuple(nombre for nombre, _ in AGENDAS)

    filas_turno = []
    filas_cancelar = []

    for pendientes in tamanos:
        turnos = _turnos_para(pendientes)
        filas_turno.append((str(pendientes),) + tuple(
            formato_tiempo(costo_turno(clase, pendientes, turnos))
            for _, clase in AGENDAS))

        cancelaciones = max(1, min(100, pendientes // 2))
        filas_cancelar.append((str(pendientes),) + tuple(
            formato_tiempo(costo_cancelar(clase, pendientes, cancelaciones))
            for _, clase in AGENDAS))

    return "\n\n".join((
        tabla("AGENDA DE EVENTOS (§4.1): costo de UN turno "
              "(sacar el próximo evento y volver a programarlo)",
              encabezados, filas_turno,
              "Montículo: O(log n) por turno. Vector ordenado: O(n) al programar. "
              "Vector sin orden: O(n) al sacar."),
        tabla("AGENDA DE EVENTOS (§4.1): costo de cancelar UN evento "
              "(muere un enemigo, el antídoto cancela el veneno)",
              encabezados, filas_cancelar,
              "Montículo: O(1), solo se marca (borrado perezoso; sale cuando le "
              "toca). Vectores: O(n), hay que buscarlo y quitarlo."),
    ))


if __name__ == "__main__":
    print(ejecutar())
