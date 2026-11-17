from crypta.Modelo.Partida import AccionInvalida
from crypta.Modelo.Viaje import PASO_IMPOSIBLE, Viaje


DIRECCIONES = "NSEO"

_SIN_ARGUMENTO = ("esperar", "soltar", "equipar", "usar", "recoger_pergamino",
                  "soltar_pergamino", "pergamino", "avanzar", "retroceder")

_CON_ARGUMENTO = ("mover", "abrir", "atacar", "recoger")


class ComandoInvalido(ValueError):
    """La línea no es un comando que se entienda (palabra desconocida,
    falta o sobra el argumento...). Es distinto de AccionInvalida: ahí el
    comando se entendió, pero la partida no lo permite."""


def ejecutar_comando(partida, linea, garantizar_sala=None):

    nombre, argumento = _separar(linea)

    if nombre == "esperar":
        return partida.esperar()

    if nombre == "mover":
        direccion = _direccion(argumento)

        if garantizar_sala is not None:
            _cargar_destino(partida, direccion, garantizar_sala)

        return partida.mover(direccion)

    if nombre == "abrir":
        return partida.abrir(_direccion(argumento))

    if nombre == "atacar":
        return partida.atacar(_enemigo(partida, argumento))

    if nombre == "recoger":
        return partida.recoger(_posicion(argumento))

    if nombre == "soltar":
        return partida.soltar()

    if nombre == "equipar":
        return partida.equipar()

    if nombre == "usar":
        return partida.usar()

    if nombre == "recoger_pergamino":
        return partida.recoger_pergamino()

    if nombre == "soltar_pergamino":
        return partida.soltar_pergamino()

    if nombre == "pergamino":
        if not partida.usar_pergamino():
            raise AccionInvalida("No puedes usar un pergamino ahora")
        return True

    if nombre == "avanzar":
        return partida.jugador.inventario.avanzar()

    return partida.jugador.inventario.retroceder()


def ejecutar_y_registrar(partida, linea, comando, garantizar_sala=None):
    """`ejecutar_comando` y, si el comando se ejecutó, anotarlo en la línea
    de tiempo (capacidad 004, research D12; FR-408, FR-413). Lo usan el
    Controlador, la reproducción y el bench, así la línea se arma igual
    jugando que reproduciendo un log. Si el comando lanza, la línea no
    cambia. Con `linea = None` es `ejecutar_comando`."""
    acciones_antes = partida.acciones_jugador
    reloj_antes = partida.reloj

    resultado = ejecutar_comando(partida, comando, garantizar_sala)

    if linea is not None:
        linea.registrar(partida, comando, acciones_antes, reloj_antes)

    return resultado


def leer_historia(texto):
    """`historia <t>` → ("instante", t); `historia #k` → ("accion", k)
    (FR-403, FR-404). t y k son dígitos ASCII, sin signo ni espacios
    internos; cualquier otra forma es un `ComandoInvalido`, igual que un
    comando que no se entiende en P1 (FR-405)."""
    if not isinstance(texto, str):
        raise ComandoInvalido("El comando debe ser texto")

    partes = texto.strip().split()

    if not partes or partes[0].lower() != "historia":
        raise ComandoInvalido("No es un comando historia")

    if len(partes) != 2:
        raise ComandoInvalido(
            "'historia' lleva exactamente un dato: un instante (historia 500) "
            "o una acción (historia #3)")

    argumento = partes[1]

    if argumento.startswith("#"):
        numero = argumento[1:]

        if not _son_digitos(numero):
            raise ComandoInvalido(
                f"Acción inválida: '{argumento}' (usa # y un número, como #3)")

        return "accion", int(numero)

    if not _son_digitos(argumento):
        raise ComandoInvalido(
            f"Instante inválido: '{argumento}' (un número entero desde 0)")

    return "instante", int(argumento)


def leer_ir_a(texto):
    """`ir a <sala>` → el id de la sala (contracts/cli.md). Tres palabras:
    `ir`, `a` y la sala en dígitos ASCII, sin signo. Cualquier otra forma
    es un `ComandoInvalido` (FR-216, HU3-3)."""
    if not isinstance(texto, str):
        raise ComandoInvalido("El comando debe ser texto")

    partes = texto.strip().split()

    if (len(partes) != 3 or partes[0].lower() != "ir"
            or partes[1].lower() != "a"):
        raise ComandoInvalido(
            "Para viajar escribe 'ir a' y el número de una sala (ir a 7)")

    if not _son_digitos(partes[2]):
        raise ComandoInvalido(
            f"Sala inválida: '{partes[2]}' (un número de sala, como 7)")

    return int(partes[2])


def ejecutar_ir_a(partida, id_destino, ejecutar_paso, garantizar_sala=None,
                  anotar_comentario=None):
    """La orden `ir a <id_destino>` (FR-216 a FR-222; research D8).
    Devuelve el `Viaje` detenido, con su motivo.

    - Valida con `Viaje.validar`: un rechazo es `AccionInvalida` y no
      consume tiempo ni anota nada.
    - Por cada paso: la dirección (sin ruta → SIN_RUTA); `garantizar_sala`
      del destino **antes** del `mover` (solo su `RuntimeError` es
      PASO_IMPOSIBLE, sin hacer el paso); antes del primer paso,
      `anotar_comentario("ir a <id>")`; `ejecutar_paso("mover <d>")`, que en
      el Controlador es exactamente un `mover` escrito a mano; y las
      paradas de `Viaje.despues_del_paso`.
    - Un error que sale de `ejecutar_paso` no es una parada: se propaga, y
      los pasos ya hechos quedan hechos."""
    viaje = Viaje.validar(partida, id_destino)

    while not viaje.terminado:
        direccion = viaje.siguiente_direccion(partida)

        if direccion is None:
            break

        if garantizar_sala is not None:
            puerta = partida.sala_actual().obtener_puerta(direccion)

            try:
                garantizar_sala(puerta.sala_destino)
            except RuntimeError as error:
                viaje.detener(PASO_IMPOSIBLE, str(error))
                break

        if viaje.pasos == 0 and anotar_comentario is not None:
            anotar_comentario(f"ir a {id_destino}")

        vida_antes = partida.jugador.vida
        ejecutar_paso(f"mover {direccion}")
        viaje.despues_del_paso(partida, vida_antes)

    return viaje


def _son_digitos(texto):
    if not texto:
        return False

    for caracter in texto:
        if caracter not in "0123456789":
            return False

    return True


def _cargar_destino(partida, direccion, garantizar_sala):

    if not partida.iniciada or partida.terminada:
        return

    puerta = partida.sala_actual().obtener_puerta(direccion)

    if puerta is None or puerta.esta_cerrada():
        return

    garantizar_sala(puerta.sala_destino)


def _separar(linea):

    if not isinstance(linea, str):
        raise ComandoInvalido("El comando debe ser texto")

    nombre, _, argumento = linea.strip().partition(" ")
    argumento = argumento.strip()

    if nombre in _SIN_ARGUMENTO:
        if argumento:
            raise ComandoInvalido(f"'{nombre}' no lleva nada más")
        return nombre, None

    if nombre in _CON_ARGUMENTO:
        if not argumento or " " in argumento:
            raise ComandoInvalido(f"'{nombre}' lleva exactamente un dato")
        return nombre, argumento

    if not nombre:
        raise ComandoInvalido("Línea vacía")

    raise ComandoInvalido(f"Comando desconocido: '{nombre}'")


def _direccion(texto):
    direccion = texto.upper()

    if len(direccion) != 1 or direccion not in DIRECCIONES:
        raise ComandoInvalido(f"Dirección inválida: '{texto}' (usa N, S, E u O)")

    return direccion


def _posicion(texto):
    if not texto.isdigit():
        raise ComandoInvalido(f"Posición inválida: '{texto}' (un número desde 0)")

    return int(texto)


def _enemigo(partida, id_instancia):
    presentes = partida.enemigos_presentes()

    for i in range(len(presentes)):
        enemigo = presentes.obtener(i)

        if enemigo.id_instancia == id_instancia:
            return enemigo

    raise AccionInvalida(f"No hay ningún enemigo '{id_instancia}' en esta sala")
