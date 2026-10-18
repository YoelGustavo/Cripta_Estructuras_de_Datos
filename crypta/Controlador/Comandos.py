from crypta.Modelo.Partida import AccionInvalida


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