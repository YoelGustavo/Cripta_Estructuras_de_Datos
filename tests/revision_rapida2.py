"""Segunda revisión rápida: casos que la primera no cubría (no cambia nada).

Póngalo en tests/ y córralo igual que el otro:
    python -m tests.revision_rapida_2

Igual que antes: situaciones normales del juego (nada del Apéndice B), cada
una con la sección del enunciado que pide ese resultado. Imprime OK o FALLA.
"""

import time

from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.EstadoJuego import EstadoJuego
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Inventario import Inventario
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Sala import Sala
from crypta.estructuras.ListaDoble import ListaDoble


def sala(numero, **salidas):
    return {"id": numero, "nombre": f"Sala {numero}",
            "salidas": {d: (v if isinstance(v, dict) else {"sala": v}) for d, v in salidas.items()}}


def mapa_de(*salas):
    mapa = Mapa()
    mapa.cargar_desde_json(list(salas))
    return mapa


def ficha(id_tipo, clase="arma"):
    return {"id": id_tipo, "nombre": id_tipo, "clase": clase, "peso": 1, "valor": 1}


class Actor:
    def __init__(self, vida):
        self.vida = vida


# ----------------------------------------------------------------------

def caso_soltar_no_depende_de_la_posicion():
    """§4.5: "Debe poder soltarse el objeto que se está viendo, en cualquier
    posición, sin que el costo dependa de la posición dentro del inventario"."""
    pasos = []
    original = ListaDoble.siguiente

    def contar(self, nodo):
        pasos.append(1)
        return original(self, nodo)

    resultados = []
    for posicion in (0, 999):
        inventario = Inventario(1000)
        for i in range(1000):
            inventario.recoger(ficha(f"o{i}"))
        for _ in range(posicion):
            inventario.avanzar()
        pasos.clear()
        ListaDoble.siguiente = contar
        try:
            inventario.soltar_actual_con_contexto()
        finally:
            ListaDoble.siguiente = original
        resultados.append(len(pasos))
    return resultados[1] <= resultados[0] + 5, (
        f"soltar el 1.º recorre {resultados[0]} nodos; soltar el 1000.º recorre {resultados[1]}"
    )


def caso_deshacer_equipar():
    """§2.7/§4.6: equipar es una acción (costo 50); el pergamino debe poder deshacerla."""
    inventario = Inventario(5)
    for nombre in "ABC":
        inventario.recoger(ficha(nombre))
    inventario.avanzar()
    inventario.avanzar()
    inventario.equipar_actual()                    # [C, A, B]
    for nombre in ("restaurar_equipado", "deshacer_equipar", "equipar_actual_con_contexto"):
        if hasattr(inventario, nombre):
            return True, ""
    return False, "ya no existe ningún método para deshacer equipar (se borró equipar_actual_con_contexto)"


def caso_deshacer_recoger_con_dos_iguales():
    """§2.7/§4.6: dos dagas son la misma ficha; deshacer debe quitar la que se recogió."""
    daga, antorcha = ficha("itm_daga"), ficha("itm_antorcha", "antorcha")
    inventario = Inventario(5)
    inventario.recoger(daga)
    inventario.recoger(antorcha)                   # [daga, antorcha]
    suelo = Sala(1, "S", {})
    suelo.agregar_objeto("itm_daga")
    contexto = inventario.recoger_desde_sala(suelo, 0, daga)   # [daga, antorcha, daga]
    inventario.deshacer_recogida(contexto)
    orden = [o["id"] for o in inventario.orden_real()]
    return orden == ["itm_daga", "itm_antorcha"], f"quedó {orden} (quitó la daga que ya tenía)"


def caso_deshacer_evento_ya_ejecutado():
    """§2.11: "la reversión incluye ... acciones enemigas ... eventos programados"."""
    agenda = Agenda()
    agenda.programar(66, "rata actúa")
    evento = agenda.siguiente()      # la rata actuó
    agenda.restaurar_evento(evento)  # el pergamino deshace ese turno
    vuelve = agenda.siguiente()
    return vuelve is evento, f"el turno de la rata desapareció de la agenda (siguiente() = {vuelve})"


def caso_ejemplo_2_11():
    """§2.11 (el ejemplo del enunciado): t=100 el jugador ataca a la rata,
    t=150 la rata ataca (-4), t=200 pergamino: vuelven la vida de la rata,
    la vida del jugador y el reloj."""
    estado = EstadoJuego()
    estado.pergaminos_retroceso = 1
    jugador, rata = Actor(30), Actor(12)
    estado.reloj = 100

    accion = RegistroAccion("atacar")
    accion.registrar_cambio(Cambio.de_atributo("vida", rata, "vida", rata.vida))
    rata.vida = 5
    estado.historial.registrar(accion)

    # t=150: actúa la rata. No hay una acción del jugador "abierta" donde
    # anotarlo; lo más parecido que existe es registrar_cambio_pendiente.
    estado.avanzar_reloj(50)
    estado.historial.registrar_cambio(
        Cambio.de_atributo("vida", jugador, "vida", jugador.vida)
    )
    jugador.vida = 26

    estado.usar_pergamino_retroceso()
    obtenido = (rata.vida, jugador.vida, estado.reloj)
    return obtenido == (12, 30, 100), (
        f"(vida rata, vida jugador, reloj) = {obtenido}; el enunciado pide (12, 30, 100)"
    )


def caso_puerta_con_llave_descrita_de_un_lado():
    """§2.1/§2.5: si la cripta describe la cerradura solo desde un lado, la
    puerta igual debe quedar cerrada (desde los dos lados)."""
    mapa = mapa_de(sala(1, N=2), sala(2, S={"sala": 1, "cerrada": True, "llave": "itm_llave"}))
    lado_1 = mapa.obtener_sala(1).obtener_puerta("N")
    lado_2 = mapa.obtener_sala(2).obtener_puerta("S")
    return lado_1.esta_cerrada() and lado_2.esta_cerrada(), (
        f"cerrada desde 1: {lado_1.esta_cerrada()}, desde 2: {lado_2.esta_cerrada()} "
        f"(se perdió la llave al compartir)"
    )


def caso_sala_sin_salidas():
    """§3.3 + Swagger: en el esqueleto, "salidas" es opcional."""
    try:
        mapa_de({"id": 1, "nombre": "Celda"})
    except Exception as error:
        return False, f"se cae: {type(error).__name__}: {error}"
    return True, ""


def caso_segunda_precarga_async():
    """§4.2: la precarga ANTICIPADA (en otro hilo) tampoco debe quedarse sin salas nuevas."""
    salas = [sala(n, **({"E": n + 1} if n < 30 else {}), **({"O": n - 1} if n > 1 else {}))
             for n in range(1, 31)]

    class Fuente:
        def obtener_contenido(self, cripta_id, ids):
            return {"contenido": [{"sala": s, "enemigos": [], "objetos": [], "trampas": []} for s in ids]}

    gestor = GestorContenido(Fuente(), mapa_de(*salas), "prueba")
    gestor.precargar_async(1)          # trae 1..10
    gestor.garantizar_sala(1)          # espera esa respuesta
    secuencia = gestor.precargar_async(5)
    gestor._ejecutor.shutdown(wait=True)
    return secuencia is not None, "la segunda precarga anticipada no pidió nada (debía traer 11..20)"


def caso_agenda_vacia_con_cancelados():
    """§4.1: un actor muerto deja eventos cancelados; el bucle principal no
    debe creer que todavía hay algo que ejecutar."""
    agenda = Agenda()
    agenda.cancelar(agenda.programar(80, "rata muerta"))
    vacia, cantidad = agenda.esta_vacia(), len(agenda)
    if not vacia and agenda.siguiente() is None:
        return False, f"esta_vacia() = False y len = {cantidad}, pero siguiente() da None"
    return True, ""


CASOS = [
    ("4.1 agenda con solo eventos cancelados", caso_agenda_vacia_con_cancelados),
    ("4.2 segunda precarga anticipada", caso_segunda_precarga_async),
    ("3.3 sala sin 'salidas'", caso_sala_sin_salidas),
    ("2.1 cerradura descrita de un solo lado", caso_puerta_con_llave_descrita_de_un_lado),
    ("4.5 soltar no depende de la posición", caso_soltar_no_depende_de_la_posicion),
    ("4.6 deshacer equipar", caso_deshacer_equipar),
    ("4.6 deshacer recoger con dos objetos iguales", caso_deshacer_recoger_con_dos_iguales),
    ("4.6 deshacer un turno enemigo ya ejecutado", caso_deshacer_evento_ya_ejecutado),
    ("4.6 ejemplo del §2.11 (jugador + rata)", caso_ejemplo_2_11),
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
