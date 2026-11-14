"""Línea de tiempo de la partida (capacidad 004; research D1, D5, D6).

Guarda la **secuencia neta** de comandos (sin los revertidos) y un punto de
control (una copia de la partida) cada K acciones del jugador. Con eso, la
reconstrucción (`crypta/Modelo/Reconstruccion.py`) da el estado en cualquier
instante o antes de cualquier acción, re-ejecutando a lo sumo K acciones
sobre el punto anterior y deshaciéndolas después (D2).

No es atributo de la `Partida` (D12): la tienen el Controlador y la
reproducción. Si fuera parte de la partida, copiar un punto de control
copiaría todos los demás.

Estructuras (principio I): tres `Vector`; la búsqueda por reloj usa la
búsqueda binaria propia. Sin `dict` ni `bisect`.
"""

import copy

from crypta.estructuras.BusquedaBinaria import primera_no_menor
from crypta.estructuras.Vector import Vector


# K por defecto (research D4): el menor que cumple FR-433 con margen (4,5 %
# de las acciones copian, menos del 5 %) y deja margen en FR-432 (≈ 34 ms
# estimados con 300 salas). Lo confirma o lo cambia `--bench` (T050).
K_POR_DEFECTO = 22

ACCION = "accion"
NO_ACCION = "no_accion"
AJUSTE = "ajuste"


class ConsultaRechazada(ValueError):
    """La consulta se entendió pero no se puede hacer (FR-403, FR-404): el
    mensaje es el de contracts/cli.md. No cambia nada."""


class EntradaLinea:
    """Un paso de la secuencia neta (data-model.md).

    - `tipo`: `ACCION`, `NO_ACCION` o `AJUSTE`.
    - `comando`: texto ya traducido, el mismo que va a `partida.log`; vacío
      en `AJUSTE`.
    - `reloj`: `int ≥ 0`, el reloj de la partida al decidir el comando.
    - `numero_accion`: `int ≥ 1`, k de la acción (en `ACCION`) o de la
      próxima acción (en los otros dos tipos).
    - `pergaminos_inventario`, `posicion_actual`, `pergaminos_sala`: solo en
      `AJUSTE` (historia 2)."""

    def __init__(self, tipo, comando, reloj, numero_accion,
                 pergaminos_inventario=None, posicion_actual=None,
                 pergaminos_sala=None):
        if tipo not in (ACCION, NO_ACCION, AJUSTE):
            raise ValueError(f"Tipo de entrada desconocido: {tipo!r}")

        if reloj < 0:
            raise ValueError("El reloj de una entrada no puede ser negativo")

        if numero_accion < 1:
            raise ValueError("El número de acción empieza en 1")

        self.tipo = tipo
        self.comando = "" if tipo == AJUSTE else comando
        self.reloj = reloj
        self.numero_accion = numero_accion
        self.pergaminos_inventario = pergaminos_inventario
        self.posicion_actual = posicion_actual
        self.pergaminos_sala = pergaminos_sala

    def __repr__(self):
        return f"EntradaLinea({self.tipo}, {self.comando!r}, t={self.reloj}, #{self.numero_accion})"


class PuntoDeControl:
    """Copia completa de la partida (data-model.md; FR-422).

    - `ancla`: acciones netas completas en ese estado (a₀ + j·K).
    - `posicion`: índice de la primera entrada que va después del punto.
    - `partida`: copia independiente (research D3), con historial sin límite.
    - `salas_cargadas`: `Vector` de ids de las salas que una consulta cargó
      en esta copia y que quedan cargadas (decisión del grupo, research D7)."""

    def __init__(self, ancla, posicion, partida):
        self.ancla = ancla
        self.posicion = posicion
        self.partida = partida
        self.salas_cargadas = Vector()

    def __repr__(self):
        return f"PuntoDeControl(ancla={self.ancla}, posicion={self.posicion})"


class Objetivo:
    """Lo que pide una consulta, ya ubicado (data-model.md).

    - `pedido`: «instante <t>» o «acción #<k>».
    - `acciones_completas`: m, acciones que el estado ya tiene enteras.
    - `tope`: None (estado antes de la acción #(m + 1)), o t: además se
      re-ejecuta la acción #(m + 1) solo hasta el instante t (research D9).
    - `es_actual`: el estado pedido es el actual; se resume la partida viva."""

    def __init__(self, pedido, acciones_completas, tope=None, es_actual=False):
        self.pedido = pedido
        self.acciones_completas = acciones_completas
        self.tope = tope
        self.es_actual = es_actual

    def __repr__(self):
        return (f"Objetivo({self.pedido!r}, m={self.acciones_completas}, "
                f"tope={self.tope}, actual={self.es_actual})")


def _reloj_de_decision(fila):
    return fila[0]


class LineaDeTiempo:
    """La historia de la partida tal como quedó (FR-401 a FR-404, FR-422,
    FR-425).

    - `k`: acciones entre dos puntos de control (`int ≥ 1`).
    - `entradas`: `Vector` de `EntradaLinea`, la secuencia neta.
    - `decisiones`: `Vector` de (reloj, posición de la entrada); la fila i es
      la acción #(a₀ + i + 1). Ordenado por reloj: toda acción avanza el
      reloj al menos 1 (research D5), así que es estrictamente creciente.
    - `puntos`: `Vector` de `PuntoDeControl`; el punto j tiene ancla a₀ + j·K.

    Contadores para las pruebas y el bench: `puntos_examinados` (FR-425) y
    `ultimas_reejecutadas` (FR-423), de la última consulta."""

    def __init__(self, k=K_POR_DEFECTO):
        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
            raise ValueError(f"K debe ser un entero mayor o igual que 1: {k!r}")

        self.k = k
        self.entradas = Vector()
        self.decisiones = Vector()
        self.puntos = Vector()
        self.accion_base = 0
        self.reloj_base = 0
        self.iniciada = False

        self.puntos_examinados = 0
        self.ultimas_reejecutadas = 0
        # Entradas y puntos que miró el último pergamino (FR-412).
        self.ultimas_examinadas = 0

    # --- Construcción -----------------------------------------------------

    def iniciar(self, partida):
        """Primer punto de control, con ancla a₀ = acciones de la partida (0
        en una partida nueva). Va después de `Partida.iniciar`."""
        if self.iniciada:
            raise RuntimeError("La línea de tiempo ya se inició")

        if not partida.iniciada:
            raise RuntimeError("Primero hay que iniciar la partida")

        self.accion_base = partida.acciones_jugador
        self.reloj_base = partida.reloj
        self.puntos.agregar(PuntoDeControl(self.accion_base, 0, copy.deepcopy(partida)))
        self.iniciada = True

    def registrar(self, partida, comando, acciones_antes, reloj_antes):
        """Anota un comando que se ejecutó bien (research D6).

        - Sumó una acción: entrada `ACCION` y fila en `decisiones`; si el
          total llega a a₀ + j·K y ese punto no existe, se crea (una copia).
        - No cambió las acciones (`avanzar`, `retroceder`): entrada
          `NO_ACCION`.
        - Bajó en 1 (pergamino): `revertir`."""
        acciones = partida.acciones_jugador
        diferencia = acciones - acciones_antes

        if diferencia == 1:
            posicion = len(self.entradas)
            self.entradas.agregar(EntradaLinea(ACCION, comando, reloj_antes, acciones))
            self.decisiones.agregar((reloj_antes, posicion))

            hechas = acciones - self.accion_base

            if hechas % self.k == 0 and len(self.puntos) == hechas // self.k:
                self.puntos.agregar(PuntoDeControl(
                    acciones, len(self.entradas), copy.deepcopy(partida)))

        elif diferencia == 0:
            self.entradas.agregar(EntradaLinea(NO_ACCION, comando, reloj_antes,
                                               acciones + 1))

        elif diferencia == -1:
            self.revertir(partida)

        else:
            raise ValueError(
                f"Un comando cambió las acciones en {diferencia}: no es un "
                f"comando de P1")

    def revertir(self, partida):
        """Recorte por pergamino (research D6; FR-410 a FR-412).

        - Quita del final las entradas hasta la última `ACCION` incluida (las
          que no son acción y venían después, y los ajustes anteriores, se van
          con ella) y su fila de `decisiones`: lo revertido deja de existir y
          `#k` queda numerado con las acciones que quedaron.
        - Quita los puntos de control cuya ancla supera el nuevo total.
        - Agrega una entrada `AJUSTE` con lo que el pergamino deja fuera del
          historial: pergaminos del inventario, posición del objeto actual y
          pergaminos de la sala actual. El pergamino se gasta en ese punto de
          la secuencia neta, justo antes de la acción siguiente.

        Solo mira lo que quita: O(lo revertido), nunca toda la historia."""
        examinadas = 0
        quito_accion = False

        while len(self.entradas) > 0:
            entrada = self.entradas.quitar_ultimo()
            examinadas += 1

            if entrada.tipo == ACCION:
                self.decisiones.quitar_ultimo()
                quito_accion = True
                break

        if not quito_accion or self.cantidad_acciones() != partida.acciones_jugador:
            # El pergamino revirtió una acción anterior a esta línea (una
            # línea creada a mitad de partida): se empieza de nuevo desde el
            # estado actual.
            self._reiniciar(partida)
            self.ultimas_examinadas = examinadas
            return

        n = self.cantidad_acciones()

        while len(self.puntos) > 1 and self.puntos.obtener(len(self.puntos) - 1).ancla > n:
            self.puntos.quitar_ultimo()
            examinadas += 1

        inventario = partida.jugador.inventario
        actual, _, _ = inventario.posiciones()

        self.entradas.agregar(EntradaLinea(
            AJUSTE, "", partida.reloj, n + 1,
            pergaminos_inventario=inventario.cantidad_pergaminos(),
            posicion_actual=None if actual == -1 else actual,
            pergaminos_sala=partida.sala_actual().cantidad_pergaminos(),
        ))
        self.ultimas_examinadas = examinadas

    def _reiniciar(self, partida):
        self.entradas = Vector()
        self.decisiones = Vector()
        self.puntos = Vector()
        self.iniciada = False
        self.iniciar(partida)

    # --- Consultas ----------------------------------------------------------

    def cantidad_acciones(self):
        """n: acciones netas de la partida."""
        return self.accion_base + len(self.decisiones)

    def ubicar_accion(self, k):
        """`historia #k` (FR-402, FR-404): estado justo antes de la acción
        #k, con k entre a₀ + 1 y n + 1 (#(n + 1) es el estado actual)."""
        self._exigir_consultable()
        n = self.cantidad_acciones()
        primera = self.accion_base + 1

        if not primera <= k <= n + 1:
            raise ConsultaRechazada(
                f"No hay acción #{k}: la partida tiene {n} acciones "
                f"(consulta de #{primera} a #{n + 1}).")

        pedido = f"acción #{k}"

        if k == n + 1:
            return Objetivo(pedido, n, es_actual=True)

        return Objetivo(pedido, k - 1)

    def ubicar_instante(self, t, reloj_actual):
        """`historia <t>` (FR-401, FR-403). Primera decisión con reloj ≥ t,
        con búsqueda binaria (O(log n), D5):

        - si decide justo en t: estado antes de esa acción;
        - si decide después de t: la acción anterior re-ejecutada solo hasta
          t (tope);
        - si t es el reloj actual: el estado actual."""
        self._exigir_consultable()

        if t > reloj_actual:
            raise ConsultaRechazada(
                f"No se puede consultar el instante {t}: el reloj de la "
                f"partida va en {reloj_actual}.")

        if t < self.reloj_base:
            raise ConsultaRechazada(
                f"No se puede consultar el instante {t}: la línea de tiempo "
                f"empieza en el instante {self.reloj_base}.")

        pedido = f"instante {t}"
        fila = primera_no_menor(self.decisiones, t, _reloj_de_decision)

        if fila < len(self.decisiones):
            k = self.accion_base + fila + 1

            if _reloj_de_decision(self.decisiones.obtener(fila)) == t:
                return Objetivo(pedido, k - 1)

            # Decide después de t: t cae en el ciclo de la acción #(k - 1).
            return Objetivo(pedido, k - 2, tope=t)

        if t == reloj_actual:
            return Objetivo(pedido, self.cantidad_acciones(), es_actual=True)

        # Entre la última decisión y el reloj actual: ciclo de la acción #n.
        return Objetivo(pedido, self.cantidad_acciones() - 1, tope=t)

    def punto_para(self, acciones_completas):
        """El punto de control con mayor ancla ≤ `acciones_completas`. Se
        **calcula** (j = ⌊(m − a₀) / K⌋), no se busca: examina un solo punto
        (FR-425)."""
        j = (acciones_completas - self.accion_base) // self.k
        self.puntos_examinados = 1
        return self.puntos.obtener(j)

    def posicion_de_accion(self, k):
        """Índice en `entradas` de la acción #k (a₀ < k ≤ n)."""
        return self.decisiones.obtener(k - self.accion_base - 1)[1]

    def _exigir_consultable(self):
        if not self.iniciada:
            raise RuntimeError("La línea de tiempo no se inició")
