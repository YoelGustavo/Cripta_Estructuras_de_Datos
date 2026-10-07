"""Revisión rápida de 4.1 a 4.7 contra el código ACTUAL (no cambia nada).

Cópienlo a crypta/revision_rapida.py y córranlo igual que el main:
    python -m crypta.revision_rapida

Cada caso es una situación normal del juego (no del Apéndice B) y dice qué
sección del enunciado pide ese resultado. Imprime OK o FALLA.
"""

from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.EstadoJuego import EstadoJuego
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Inventario import Inventario
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Rastreador import Rastreador
from crypta.Modelo.Rastro import Rastro
from crypta.Modelo.Sala import Sala
from crypta.estructuras.CacheLRU import CacheLRU
from crypta.Modelo.Jugador import Jugador


def sala(numero, **salidas):
    return {"id": numero, "nombre": f"Sala {numero}",
            "salidas": {d: (v if isinstance(v, dict) else {"sala": v}) for d, v in salidas.items()}}


def mapa_de(*salas):
    mapa = Mapa()
    mapa.cargar_desde_json(list(salas))
    return mapa


class FuenteLinea:
    """30 salas en fila, sin contenido. Anota qué salas se piden."""

    def __init__(self):
        self.pedidas = []

    def obtener_contenido(self, cripta_id, salas):
        self.pedidas.append(list(salas))
        return {"contenido": [{"sala": s} for s in salas]}

    def obtener_catalogo(self, ids):
        return {"entidades": []}


# ----------------------------------------------------------------------

def caso_salas_desordenadas():
    """§3.3/§4.2: nada garantiza que el servidor mande las salas en orden."""
    mapa = mapa_de(sala(3), sala(1), sala(2))
    perdidas = [n for n in (1, 2, 3) if mapa.obtener_sala(n) is None]
    return perdidas == [], f"no encuentra las salas {perdidas} (están cargadas pero el árbol quedó mal)"


def caso_puerta_compartida():
    """§2.1: una salida conecta dos salas; abrir la puerta la abre de los dos lados."""
    cerrada = {"cerrada": True, "llave": "itm_llave"}
    mapa = mapa_de(sala(1, N={"sala": 2, **cerrada}), sala(2, S={"sala": 1, **cerrada}))
    mapa.obtener_sala(1).obtener_puerta("N").abrir()
    otro_lado = mapa.obtener_sala(2).obtener_puerta("S")
    return not otro_lado.esta_cerrada(), "abrí desde la sala 1 y desde la sala 2 sigue cerrada"


def caso_rastreador_puerta_cerrada():
    """§2.5 y §2.9: los enemigos no abren puertas; el rastreador solo mira salidas abiertas."""
    mapa = mapa_de(
        sala(
            5,
            N={
                "sala": 9,
                "cerrada": True,
                "llave": "itm_llave"
            },
            S=3
        ),
        sala(9, S=5),
        sala(3, N=5)
    )

    # El rastro reciente está almacenado en cada sala.
    mapa.obtener_sala(3).registrar_rastro(200)
    mapa.obtener_sala(9).registrar_rastro(300)

    rastro = Rastro()

    destino = Rastreador(
        "rata",
        150,
        sala_actual=5
    ).decidir_destino(
        mapa,
        rastro,
        350
    )

    return (
        destino == 3,
        f"eligió la sala {destino}; debía ignorar la puerta cerrada hacia 9"
    )


def caso_rastreador_empate():
    """§2.9: con el mismo tiempo de rastro se escoge la sala de menor id."""
    mapa = mapa_de(
        sala(5, N=9, S=3),
        sala(9, S=5),
        sala(3, N=5)
    )

    # Ambas salas tienen un rastro igualmente reciente.
    mapa.obtener_sala(9).registrar_rastro(100)
    mapa.obtener_sala(3).registrar_rastro(100)

    rastro = Rastro()

    destino = Rastreador(
        "rata",
        150,
        sala_actual=5
    ).decidir_destino(
        mapa,
        rastro,
        150
    )

    return (
        destino == 3,
        f"eligió la sala {destino}; en empate debía elegir la sala 3"
    )


def caso_costo_del_rastro():
    """§4.7: decidir no puede costar según la longitud del recorrido del jugador."""
    mapa = mapa_de(
        sala(5, N=9, S=3),
        sala(9, S=5),
        sala(3, N=5)
    )

    # Las únicas salas relevantes para el rastreador son sus vecinas.
    mapa.obtener_sala(3).registrar_rastro(200)
    mapa.obtener_sala(9).registrar_rastro(300)

    class RastroNoConsultable:
        def obtener_reciente(self, *args, **kwargs):
            raise AssertionError(
                "El rastreador consultó el historial global"
            )

    rastro = RastroNoConsultable()

    try:
        destino = Rastreador(
            "rata",
            150,
            sala_actual=5
        ).decidir_destino(
            mapa,
            rastro,
            350
        )
    except AssertionError as error:
        return False, str(error)

    return (
        destino == 9,
        "la decisión depende de las salidas vecinas, no del recorrido completo"
    )


def caso_dos_soltar_y_deshacer():
    """§2.11/§4.6: se pueden deshacer hasta 5 acciones seguidas (un pergamino por acción)."""
    inventario = Inventario(5)
    for letra in "ABC":
        inventario.recoger({"id": letra, "peso": 1, "valor": 1, "nombre": letra})
    inventario.avanzar()
    primera = inventario.soltar_actual_con_contexto()   # suelta B
    segunda = inventario.soltar_actual_con_contexto()   # suelta C
    try:
        inventario.restaurar_soltado(segunda)
        inventario.restaurar_soltado(primera)
    except Exception as error:
        return False, f"se cae: {type(error).__name__}: {error}"
    orden = [o["id"] for o in inventario.orden_real()]
    return orden == ["A", "B", "C"], f"quedó {orden}"


def caso_recoger_soltar_y_deshacer():
    """§2.11/§4.6: recoger y luego soltar; dos pergaminos deben dejar todo como antes."""
    suelo = Sala(1, "S", {})
    suelo.agregar_objeto("itm_daga")
    inventario = Inventario(5)
    recogida = inventario.recoger_desde_sala(suelo, 0, {"id": "itm_daga", "peso": 2, "valor": 15, "nombre": "Daga"})
    soltada = inventario.soltar_en_sala(suelo)
    try:
        inventario.deshacer_soltar_en_sala(soltada)
        inventario.deshacer_recogida(recogida)
    except Exception as error:
        return False, f"se cae: {type(error).__name__}: {error}"
    return (len(inventario), suelo.cantidad_objetos()) == (0, 1), "no volvió al estado inicial"


def caso_deshacer_cancelacion():
    """§2.11/§4.6: deshacer debe dejar la agenda como estaba (el evento ocurre UNA vez)."""
    agenda = Agenda()
    evento = agenda.programar(100, "rata ataca")
    agenda.cancelar(evento)          # p. ej. la rata murió durante la acción
    agenda.restaurar_evento(evento)  # el pergamino deshace esa muerte
    veces = 0
    while agenda.siguiente() is not None:
        veces += 1
    return veces == 1, f"el evento se ejecutó {veces} veces"


def caso_pergamino_y_reloj():
    """§2.11 (el ejemplo del propio enunciado): el retroceso restaura el reloj."""
    estado = EstadoJuego()
    estado.pergaminos_retroceso = 1

    class Jugador:
        vida = 30

    jugador = Jugador()
    accion = RegistroAccion("atacar")
    accion.registrar_cambio(Cambio.de_atributo("vida", jugador, "vida", jugador.vida))
    jugador.vida = 26
    estado.historial.registrar(accion)
    estado.avanzar_reloj(100)        # la acción consumió tiempo
    estado.usar_pergamino_retroceso()
    return estado.reloj == 0, f"la vida volvió a {jugador.vida}, pero el reloj quedó en {estado.reloj}"


def caso_dos_ratas_misma_ficha():
    """§4.4: una ficha usada por AL MENOS una instancia activa no se libera."""
    cache = CacheLRU(2)
    cache.insertar("ent_rata", {"id": "ent_rata"})
    cache.marcar_en_uso("ent_rata")   # rata 1
    cache.marcar_en_uso("ent_rata")   # rata 2
    cache.liberar("ent_rata")         # muere la rata 1
    return cache.esta_en_uso("ent_rata"), "la rata 2 sigue viva pero su ficha ya se puede desalojar"


def caso_cache_llena_en_uso():
    """§4.4 + --cache-size: con un tope pequeño y una sala con más tipos que el tope."""
    cache = CacheLRU(2)
    for clave in ("a", "b"):
        cache.insertar(clave, {"id": clave})
        cache.marcar_en_uso(clave)
    try:
        cache.insertar("c", {"id": "c"})
    except Exception as error:
        return False, f"se cae: {type(error).__name__}: {error}"
    return True, ""


def caso_segunda_precarga():
    """§4.2: precargar por lotes de 10; una sala pedida no se vuelve a pedir."""
    salas = [sala(n, **({"E": n + 1} if n < 30 else {}), **({"O": n - 1} if n > 1 else {}))
             for n in range(1, 31)]
    fuente = FuenteLinea()
    gestor = GestorContenido(fuente, mapa_de(*salas), "prueba")
    gestor.precargar_desde(1)    # trae 1..10
    gestor.precargar_desde(5)    # debería traer 11..20
    nuevas = [s for lote in fuente.pedidas[1:] for s in lote]
    return len(nuevas) > 0, f"la segunda precarga pidió {nuevas}"

def caso_deshacer_restaura_rastro():
    """§4.6: deshacer un movimiento restaura el rastro anterior de la sala."""

    mapa = mapa_de(
        sala(3, N=4),
        sala(4, S=3)
    )

    jugador = Jugador(
        nombre="Jugador",
        vida_max=30,
        ataque=5,
        defensa=2,
        velocidad=100,
        inventario_max=5
    )

    sala3 = mapa.obtener_sala(3)
    sala4 = mapa.obtener_sala(4)

    # Primera visita a sala 3.
    jugador.mover_a(
        sala3,
        100
    )

    # Visita a sala 4.
    jugador.mover_a(
        sala4,
        200
    )

    # Segunda visita a sala 3.
    jugador.mover_a(
        sala3,
        300
    )

    # Antes de deshacer, el rastro más reciente
    # de la sala 3 debe ser 300.
    if sala3.obtener_rastro() != 300:
        return (
            False,
            f"antes de deshacer esperaba 300 y obtuvo "
            f"{sala3.obtener_rastro()}"
        )

    jugador.deshacer_ultimo_movimiento(
        4
    )

    # Debe reaparecer la visita anterior a sala 3.
    return (
        sala3.obtener_rastro() == 100,
        f"esperaba restaurar 100 y obtuvo "
        f"{sala3.obtener_rastro()}"
    )


CASOS = [
    ("4.2 salas que llegan desordenadas", caso_salas_desordenadas),
    ("4.2 segunda precarga trae salas nuevas", caso_segunda_precarga),
    ("2.1 puerta compartida por las dos salas", caso_puerta_compartida),
    ("4.1 deshacer una cancelación", caso_deshacer_cancelacion),
    ("4.4 dos ratas con la misma ficha", caso_dos_ratas_misma_ficha),
    ("4.4 caché llena con fichas en uso", caso_cache_llena_en_uso),
    ("4.5 soltar dos y deshacer las dos", caso_dos_soltar_y_deshacer),
    ("4.5 recoger, soltar y deshacer las dos", caso_recoger_soltar_y_deshacer),
    ("4.6 el pergamino restaura el reloj", caso_pergamino_y_reloj),
    ("4.6 deshacer restaura el rastro", caso_deshacer_restaura_rastro),
    ("4.7 rastreador y puerta cerrada", caso_rastreador_puerta_cerrada),
    ("4.7 rastreador con empate", caso_rastreador_empate),
    ("4.7 costo del rastro", caso_costo_del_rastro),
]


def main():
    fallas = 0
    for nombre, caso in CASOS:
        try:
            bien, detalle = caso()
        except Exception as error:
            bien, detalle = False, f"se cae: {type(error).__name__}: {error}"
        print(f"{'OK   ' if bien else 'FALLA'}  {nombre}" + ("" if bien else f"\n         -> {detalle}"))
        fallas += 0 if bien else 1
    print(f"\n{len(CASOS) - fallas} de {len(CASOS)} casos bien")


if __name__ == "__main__":
    main()