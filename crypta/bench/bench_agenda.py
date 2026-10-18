import random

from crypta.bench.medicion import cronometrar, formato_tiempo, medir, tabla
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Evento import Evento, evento_menor


INTERVALOS = (66, 100, 111, 50)

TAMANOS = (10, 100, 1000, 5000)
TAMANOS_RAPIDO = (10, 100)


class AgendaVectorOrdenado:

    def __init__(self):
        self._eventos = Vector()
        self._secuencia = 0

    def __len__(self):
        return len(self._eventos)

    def programar(self, tiempo, tipo, objetivo=None):
        evento = Evento(tiempo, self._secuencia, tipo, objetivo)
        self._secuencia += 1

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

def llenar(agenda, cantidad, azar):
    """'cantidad' actores, cada uno con su próximo turno pendiente."""
    eventos = []

    for actor in range(cantidad):
        eventos.append(agenda.programar(azar.randrange(100), "turno", actor))

    return eventos


def hacer_turnos(agenda, cantidad, azar):
    salieron = []

    for _ in range(cantidad):
        evento = agenda.siguiente()
        salieron.append(evento)
        agenda.programar(evento.tiempo + azar.choice(INTERVALOS), "turno",
                         evento.objetivo)

    return salieron


def costo_turno(clase, pendientes, turnos, repeticiones=3, semilla=1):
    azar = random.Random(semilla)
    agenda = clase()
    llenar(agenda, pendientes, azar)

    return medir(lambda: hacer_turnos(agenda, turnos, azar), repeticiones) / turnos


def costo_cancelar(clase, pendientes, cancelaciones, repeticiones=2, semilla=1):
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
    return max(100, min(1000, 500000 // pendientes))

def ejecutar(rapido=False):
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
