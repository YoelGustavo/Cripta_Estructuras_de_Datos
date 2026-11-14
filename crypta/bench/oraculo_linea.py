"""Oráculo de la línea de tiempo (capacidad 004, T003; data-model.md, «Oráculo»).

Lo usa la sección L3 del bench (FR-430) y lo reutilizan las pruebas: el
bench no importa nada de `tests/`.

- `serializar_estado`: los bytes del estado de una partida con el mismo
  recorrido que el guardado (`escribir_general`, `escribir_sala`), para
  comparar dos estados (research D8).
- `jugar_con_oraculo`: juega una lista de comandos y, mientras tanto, toma el
  texto del resumen de la partida **viva** en cada decisión del jugador y en
  el instante de cada evento. Es la referencia contra la que se comparan las
  consultas reconstruidas (FR-421, SC-402).

Los imports del Controlador van dentro de las funciones: el Modelo y los
adaptadores no dependen de este módulo.
"""

from crypta.estructuras.Vector import Vector


OMITIDA = "omitida"


def _contiene(vector, valor):
    for i in range(len(vector)):
        if vector.obtener(i) == valor:
            return True

    return False


def serializar_estado(partida, omitir_salas=None):
    """Bytes del estado de `partida`: el bloque general y el registro de cada
    sala, en el orden del mapa, con `EscritorBinario`.

    - La bitácora no es estado del juego (research D3): se serializa como si
      estuviera vacía, así una copia (que tiene una bitácora propia vacía) y
      el original se pueden comparar.
    - `omitir_salas` (un `Vector` de ids, o None): de esas salas solo se
      escribe el id con la marca «omitida». Son las salas que una consulta
      cargó en un punto de control y que quedan cargadas (decisión del grupo,
      research D7 y D8): su contenido, objetos, trampas y enemigos no se
      comparan.

    No modifica la partida: la bitácora se cambia solo mientras se escribe el
    bloque general y se devuelve la misma."""
    from crypta.Adaptadores.EstadoPartida import escribir_general, escribir_sala
    from crypta.Adaptadores.GuardadoBinario import EscritorBinario
    from crypta.Modelo.Bitacora import Bitacora

    e = EscritorBinario()
    bitacora = partida.bitacora
    partida.bitacora = Bitacora()

    try:
        escribir_general(e, partida)
    finally:
        partida.bitacora = bitacora

    salas = partida.mapa.obtener_todas()

    for i in range(len(salas)):
        sala = salas.obtener(i)

        if omitir_salas is not None and _contiene(omitir_salas, sala.id):
            e.entero("id", sala.id)
            e.texto(OMITIDA, OMITIDA)
        else:
            escribir_sala(e, sala)

    return e.datos()


class EntradaOraculo:
    """Un resumen tomado de la partida viva.

    - `tiempo`: reloj de la partida cuando se tomó.
    - `pedido`: «instante <t>» o «acción #<k>», como lo escribiría el jugador.
    - `texto`: el resumen formateado (contracts/resumen.md).
    - `es_evento`: verdadero si se tomó después de un evento (y puede quedar
      reemplazado por otro evento del mismo instante)."""

    def __init__(self, tiempo, pedido, texto, es_evento):
        self.tiempo = tiempo
        self.pedido = pedido
        self.texto = texto
        self.es_evento = es_evento

    def __repr__(self):
        return f"EntradaOraculo({self.tiempo}, {self.pedido!r})"


class Oraculo:
    """Los resúmenes de la partida viva, en orden de tiempo.

    Reglas (FR-401, FR-402, research D6):

    - Después de cada evento se toma el resumen del instante del evento. Si
      el anterior era otro evento del mismo instante, se reemplaza: el estado
      en t es el de después de **todos** los eventos ≤ t.
    - Antes de cada comando, el reloj es el de la decisión: se quitan las
      entradas con tiempo ≥ reloj (las reemplaza el estado de la decisión) y
      se toman «instante <reloj>» y «acción #<k>». Un comando que no es acción
      (`avanzar`, `retroceder`) o un pergamino hacen lo mismo antes del
      comando siguiente, así lo revertido deja de estar en el oráculo
      (FR-410)."""

    def __init__(self):
        self.entradas = Vector()

    def __len__(self):
        return len(self.entradas)

    def obtener(self, i):
        return self.entradas.obtener(i)

    def al_evento(self, partida, evento):
        from crypta.Modelo.Resumen import armar_resumen, pedido_instante
        from crypta.Vista.FormatoResumen import formatear_resumen

        tiempo = partida.reloj
        texto = formatear_resumen(armar_resumen(partida, pedido_instante(tiempo)))
        nueva = EntradaOraculo(tiempo, pedido_instante(tiempo), texto, True)

        n = len(self.entradas)

        if n > 0:
            ultima = self.entradas.obtener(n - 1)

            if ultima.es_evento and ultima.tiempo == tiempo:
                self.entradas.asignar(n - 1, nueva)
                return

        self.entradas.agregar(nueva)

    def en_decision(self, partida):
        from crypta.Modelo.Resumen import armar_resumen, pedido_accion, pedido_instante
        from crypta.Vista.FormatoResumen import formatear_resumen

        tiempo = partida.reloj

        while (len(self.entradas) > 0
               and self.entradas.obtener(len(self.entradas) - 1).tiempo >= tiempo):
            self.entradas.quitar_ultimo()

        k = partida.acciones_jugador + 1

        for pedido in (pedido_instante(tiempo), pedido_accion(k)):
            texto = formatear_resumen(armar_resumen(partida, pedido))
            self.entradas.agregar(EntradaOraculo(tiempo, pedido, texto, False))


def jugar_con_oraculo(partida, linea, comandos, garantizar):
    """Juega `comandos` (un iterable de textos ya traducidos) sobre la partida
    viva con `ejecutar_y_registrar` (T020) y devuelve el `Oraculo`.

    Los comandos que el juego rechaza (`ComandoInvalido`, `AccionInvalida`)
    se saltan, como en el bench del ciclo. Al terminar, el callback
    `al_ejecutar_evento` vuelve a None (FR-426)."""
    from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_y_registrar
    from crypta.Modelo.Partida import AccionInvalida

    oraculo = Oraculo()
    partida.al_ejecutar_evento = oraculo.al_evento

    try:
        for comando in comandos:
            if partida.terminada:
                break

            oraculo.en_decision(partida)

            try:
                ejecutar_y_registrar(partida, linea, comando, garantizar)
            except (ComandoInvalido, AccionInvalida):
                pass

        if not partida.terminada:
            oraculo.en_decision(partida)
    finally:
        partida.al_ejecutar_evento = None

    return oraculo
