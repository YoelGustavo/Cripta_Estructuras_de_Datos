"""Los comandos: el "idioma" común de las acciones del jugador.

Una línea de texto = una cosa que hace el jugador. La misma línea sirve
para tres cosas, y por eso hay UNA sola traducción a la Partida:
  - lo que escribe el jugador en la consola (Fase 7);
  - lo que se guarda en el registro de partida (§4.11);
  - lo que vuelve a ejecutar el reproductor (--replay).

Los comandos:

    esperar                 mover N|S|E|O         abrir N|S|E|O
    atacar <id-instancia>   recoger <posición>    soltar
    equipar                 usar                  recoger_pergamino
    soltar_pergamino        pergamino             avanzar
    retroceder

"avanzar" y "retroceder" mueven la posición del inventario. No son
acciones (no gastan tiempo)

Al atacar se usa el id de instancia del enemigo ("e-201") y no su número
en pantalla: el número cambia si otro enemigo entra o muere; el id no.

El controlador (al jugar) y el reproductor (al repetir un log) ejecutan
las líneas con la MISMA función, ejecutar_comando, pasándole cómo cargar
una sala. Así no hay dos caminos que se puedan separar.
"""

from crypta.Modelo.Partida import AccionInvalida


DIRECCIONES = "NSEO"

# Los que no llevan argumento.
_SIN_ARGUMENTO = ("esperar", "soltar", "equipar", "usar", "recoger_pergamino",
                  "soltar_pergamino", "pergamino", "avanzar", "retroceder")

# Los que llevan exactamente uno.
_CON_ARGUMENTO = ("mover", "abrir", "atacar", "recoger")


class ComandoInvalido(ValueError):
    """La línea no es un comando que se entienda (palabra desconocida,
    falta o sobra el argumento...). Es distinto de AccionInvalida: ahí el
    comando se entendió, pero la partida no lo permite."""


def ejecutar_comando(partida, linea, garantizar_sala=None):
    """Ejecuta una línea sobre la partida y devuelve lo que devuelva la
    partida.

    - ComandoInvalido: la línea no se entiende.
    - AccionInvalida: se entiende, pero no se puede hacer ahora.

    garantizar_sala(id_sala): la función que carga el contenido de una
    sala (la del GestorContenido al jugar, la del preparador al
    reproducir). §2.4: antes de entrar a una sala su contenido tiene que
    haber llegado; por eso "mover" la llama con la sala de destino ANTES
    de mover. Si no se pasa, se supone que todo ya está cargado.

    Regla para el registro: una línea se anota SOLO si esta función
    terminó sin excepción. Así el log tiene exactamente lo que pasó.
    """
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
        # usar_pergamino devuelve False si no se pudo. Para que la regla
        # "se anota solo si no hubo excepción" sirva igual para todos, aquí
        # ese False se convierte en AccionInvalida.
        if not partida.usar_pergamino():
            raise AccionInvalida("No puedes usar un pergamino ahora")
        return True

    if nombre == "avanzar":
        return partida.jugador.inventario.avanzar()

    # (el único que queda, _separar ya revisó que el nombre exista)
    return partida.jugador.inventario.retroceder()


def _cargar_destino(partida, direccion, garantizar_sala):
    """Carga la sala a la que se va a entrar, SOLO si de verdad se va a
    poder entrar: la partida está en juego y hay una salida abierta en esa
    dirección. Si no, mover dará el error, y cargar esa sala gastaría una
    solicitud de red por nada (además, la partida original cargaría una
    sala que su reproducción no carga, porque ese comando no se anotó)."""
    if not partida.iniciada or partida.terminada:
        return

    puerta = partida.sala_actual().obtener_puerta(direccion)

    if puerta is None or puerta.esta_cerrada():
        return

    garantizar_sala(puerta.sala_destino)


def _separar(linea):
    """("mover", "N") a partir de "mover N". Revisa que el comando exista
    y que traiga (o no) su argumento."""
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
    """El enemigo vivo de la sala con ese id de instancia."""
    presentes = partida.enemigos_presentes()

    for i in range(len(presentes)):
        enemigo = presentes.obtener(i)

        if enemigo.id_instancia == id_instancia:
            return enemigo

    raise AccionInvalida(f"No hay ningún enemigo '{id_instancia}' en esta sala")