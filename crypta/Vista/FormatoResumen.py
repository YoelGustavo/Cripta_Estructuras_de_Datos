"""Texto del resumen de un estado (capacidad 004; FR-406, contracts/resumen.md).

Función pura: el mismo texto para `historia`, para `--replay … --hasta` y
después de cargar. No incluye el reloj actual de la partida.
"""

MAPA_NO_DISPONIBLE = "no disponible (capacidad 002)"


def formatear_resumen(resumen):
    lineas = [
        f"HISTORIA {resumen.pedido}",
        f"Reloj: {resumen.reloj}   Próxima acción: #{resumen.proxima_accion}",
        f"Sala: {resumen.sala_id} {resumen.sala_nombre}",
        (f"Vida: {resumen.vida}/{resumen.vida_max}   Ataque: {resumen.ataque}   "
         f"Defensa: {resumen.defensa}   Velocidad: {resumen.velocidad}"),
        "Efectos: " + _efectos(resumen.efectos),
        f"Inventario ({resumen.ocupados}/{resumen.capacidad}):",
    ]

    for i in range(len(resumen.inventario)):
        lineas.append(_objeto(i + 1, resumen.inventario.obtener(i)))

    lineas.append(f"  Pergaminos: {resumen.pergaminos}")

    if len(resumen.enemigos) == 0:
        lineas.append("Enemigos en la sala: ninguno")
    else:
        lineas.append("Enemigos en la sala:")

        for i in range(len(resumen.enemigos)):
            enemigo = resumen.enemigos.obtener(i)
            lineas.append(f"  {enemigo.id_instancia} {enemigo.nombre}: vida {enemigo.vida}")

    mapa = MAPA_NO_DISPONIBLE if resumen.mapa_conocido is None else resumen.mapa_conocido
    lineas.append(f"Mapa conocido: {mapa}")

    if resumen.aviso is not None:
        lineas.append(f"Aviso: {resumen.aviso}")

    return "\n".join(lineas) + "\n"


def _efectos(efectos):
    if len(efectos) == 0:
        return "ninguno"

    partes = []

    for i in range(len(efectos)):
        efecto = efectos.obtener(i)

        if efecto.tipo == "velocidad":
            partes.append(f"velocidad {efecto.valor:+d} hasta {efecto.hasta}")
        else:
            partes.append(f"{efecto.tipo} hasta {efecto.hasta}")

    return ", ".join(partes)


def _objeto(numero, objeto):
    texto = f"  {numero}. {objeto.nombre} ({objeto.id})"

    if objeto.equipado is not None:
        texto += f" [{objeto.equipado} equipada]"

    if objeto.es_actual:
        texto += " <- actual"

    return texto
