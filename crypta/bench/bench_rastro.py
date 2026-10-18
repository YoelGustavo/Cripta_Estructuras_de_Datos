from crypta.bench.bench_red import cripta_en_cuadricula
from crypta.bench.medicion import formato_tiempo, medir, tabla
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Rastreador import VIGENCIA_RASTRO, sala_con_rastro_mas_fresco


class HuellasEnLista:
    def __init__(self):
        self._huellas = Vector()

    def pisar(self, id_sala, tiempo):
        self._huellas.agregar((id_sala, tiempo))

    def rastro_de(self, id_sala):
        for i in range(len(self._huellas) - 1, -1, -1):
            sala, tiempo = self._huellas.obtener(i)
            if sala == id_sala:
                return tiempo
        return None

    def decidir(self, sala, reloj):
        mejor = None
        mejor_tiempo = None
        puertas = sala.puertas(solo_abiertas=True)

        for i in range(len(puertas)):
            vecina = puertas.obtener(i).sala_destino_ref
            tiempo = self.rastro_de(vecina.id)

            if tiempo is None or reloj - tiempo >= VIGENCIA_RASTRO:
                continue
            if (mejor is None or tiempo > mejor_tiempo
                    or (tiempo == mejor_tiempo and vecina.id < mejor.id)):
                mejor, mejor_tiempo = vecina, tiempo

        return mejor


def preparar(cantidad_salas, pasos):
    salas, _ = cripta_en_cuadricula(cantidad_salas)
    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    huellas = HuellasEnLista()
    reloj = 0

    for paso in range(pasos):
        id_sala = 1 + paso % 2
        mapa.obtener_sala(id_sala).registrar_rastro(reloj)
        huellas.pisar(id_sala, reloj)
        reloj += 100

    return mapa, huellas, reloj, mapa.obtener_sala(cantidad_salas)


def costo_decision(cantidad_salas, pasos, vueltas=200):
    mapa, huellas, reloj, sala = preparar(cantidad_salas, pasos)

    def juego():
        for _ in range(vueltas):
            sala_con_rastro_mas_fresco(sala, reloj)

    def lista():
        for _ in range(vueltas):
            huellas.decidir(sala, reloj)

    return medir(juego) / vueltas, medir(lista, repeticiones=3) / vueltas


def ejecutar(rapido=False):
    casos = ((100, 10), (100, 1000)) if rapido else (
        (100, 10), (100, 1000), (2500, 10), (2500, 10000))
    filas = []

    for cantidad_salas, pasos in casos:
        juego, lista = costo_decision(cantidad_salas, pasos, 50 if rapido else 200)
        filas.append((str(cantidad_salas), str(pasos),
                      formato_tiempo(juego), formato_tiempo(lista)))

    return tabla(
        "RASTRO (§4.7): decisión de UN rastreador lejos del jugador",
        ("salas de la cripta", "pasos del jugador", "rastro en cada sala (el juego)",
         "lista de huellas"),
        filas,
        "El juego mira solo las salidas abiertas de su sala (a lo sumo 4) y un número "
        "por sala. La lista de huellas tiene que buscar hacia atrás todo el recorrido.")


if __name__ == "__main__":
    print(ejecutar())
