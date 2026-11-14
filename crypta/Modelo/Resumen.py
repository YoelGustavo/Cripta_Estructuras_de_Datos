"""Resumen de un estado de la partida (capacidad 004, research D10; FR-406).

Datos, sin texto: el texto lo arma `crypta/Vista/FormatoResumen.py`
(contracts/resumen.md). Se arma desde cualquier `Partida` (la viva, un punto
de control o una reproducción) y solo la lee (FR-407).
"""

from crypta.Modelo.Efecto import VELOCIDAD
from crypta.Modelo.Partida import FIN_VELOCIDAD
from crypta.estructuras.Vector import Vector


def pedido_instante(t):
    """El pedido de `historia <t>`, como aparece en el resumen."""
    return f"instante {t}"


def pedido_accion(k):
    """El pedido de `historia #k`, como aparece en el resumen."""
    return f"acción #{k}"


class ObjetoResumido:
    """Un objeto del inventario: `nombre`, `id`, `equipado` («arma»,
    «armadura» o None) y `es_actual`."""

    def __init__(self, nombre, id_objeto, equipado, es_actual):
        self.nombre = nombre
        self.id = id_objeto
        self.equipado = equipado
        self.es_actual = es_actual


class EfectoResumido:
    """Un efecto activo: `tipo` (veneno, antorcha, velocidad), `valor` (el
    cambio de velocidad; 0 en los otros) y `hasta`."""

    def __init__(self, tipo, valor, hasta):
        self.tipo = tipo
        self.valor = valor
        self.hasta = hasta


class EnemigoResumido:
    def __init__(self, id_instancia, nombre, vida):
        self.id_instancia = id_instancia
        self.nombre = nombre
        self.vida = vida


class Resumen:
    """Los datos de FR-406 de un estado.

    - `pedido`: «instante <t>» o «acción #<k>».
    - `reloj`: el reloj de ese estado, nunca el actual de la partida.
    - `proxima_accion`: k de la próxima acción del jugador en ese estado.
    - `sala_id`, `sala_nombre`.
    - `vida`, `vida_max`, `ataque`, `defensa` (con el equipo), `velocidad`.
    - `efectos`: `Vector` de `EfectoResumido` en el orden fijo veneno,
      antorcha, velocidad.
    - `inventario`: `Vector` de `ObjetoResumido` en el orden real;
      `ocupados`, `capacidad`, `pergaminos`.
    - `enemigos`: `Vector` de `EnemigoResumido` con los activos y vivos de la
      sala, en el orden de la sala.
    - `mapa_conocido`: lo define la capacidad 002; mientras no exista, None.
    - `aviso`: texto de FR-415, o None."""

    def __init__(self):
        self.pedido = None
        self.reloj = 0
        self.proxima_accion = 1
        self.sala_id = None
        self.sala_nombre = None
        self.vida = 0
        self.vida_max = 0
        self.ataque = 0
        self.defensa = 0
        self.velocidad = 0
        self.efectos = Vector()
        self.inventario = Vector()
        self.ocupados = 0
        self.capacidad = 0
        self.pergaminos = 0
        self.enemigos = Vector()
        self.mapa_conocido = None
        self.aviso = None


def armar_resumen(partida, pedido, aviso=None):
    """El `Resumen` del estado actual de `partida`. No la modifica."""
    resumen = Resumen()
    jugador = partida.jugador
    sala = partida.sala_actual()

    resumen.pedido = pedido
    resumen.aviso = aviso
    resumen.reloj = partida.reloj
    resumen.proxima_accion = partida.acciones_jugador + 1
    resumen.sala_id = sala.id
    resumen.sala_nombre = sala.nombre

    resumen.vida = jugador.vida
    resumen.vida_max = jugador.vida_max
    resumen.ataque = jugador.ataque_total()
    resumen.defensa = jugador.defensa_total()
    resumen.velocidad = jugador.velocidad

    _efectos(partida, resumen.efectos)
    _inventario(jugador.inventario, resumen)
    _enemigos(sala, resumen.enemigos)
    return resumen


def _efectos(partida, efectos):
    if partida.veneno is not None:
        efectos.agregar(EfectoResumido("veneno", partida.veneno.valor,
                                       partida.veneno.hasta))

    if partida.antorcha is not None:
        efectos.agregar(EfectoResumido("antorcha", 0, partida.antorcha.hasta))

    # Un efecto de velocidad no es atributo de la partida: es el evento que
    # lo termina (Partida._empezar_velocidad). Se listan por secuencia.
    pendientes = partida.agenda.eventos_pendientes()

    for i in range(len(pendientes)):
        evento = pendientes.obtener(i)

        if evento.tipo == FIN_VELOCIDAD and evento.objetivo.tipo == VELOCIDAD:
            efectos.agregar(EfectoResumido("velocidad", evento.objetivo.valor,
                                           evento.objetivo.hasta))


def _inventario(inventario, resumen):
    actual, arma, armadura = inventario.posiciones()
    objetos = inventario.orden_real()

    for i in range(len(objetos)):
        objeto = objetos[i]
        equipado = "arma" if i == arma else ("armadura" if i == armadura else None)
        resumen.inventario.agregar(ObjetoResumido(
            objeto.get("nombre", objeto.get("id")), objeto.get("id"),
            equipado, i == actual))

    resumen.ocupados = inventario.ocupados()
    resumen.capacidad = inventario.capacidad()
    resumen.pergaminos = inventario.cantidad_pergaminos()


def _enemigos(sala, enemigos):
    for i in range(sala.cantidad_enemigos()):
        enemigo = sala.enemigo_en(i)

        if enemigo.esta_activo() and enemigo.esta_vivo():
            enemigos.agregar(EnemigoResumido(enemigo.id_instancia, enemigo.nombre,
                                             enemigo.vida))
