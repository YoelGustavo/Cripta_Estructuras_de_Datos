"""Verificación de resolubilidad (capacidad 003; research D3).

Un solo recorrido por anchura que avanza por **rondas** (oleadas). La ronda
r recorre todo lo que se alcanza con las llaves de las rondas anteriores;
una salida cerrada cuya llave todavía no abre se **estaciona** bajo esa
llave. Al cerrar la ronda, sus llaves nuevas (ordenadas por id) forman la
ronda r del orden, empiezan a abrir y se **liberan** sus puertas
estacionadas: sus destinos son las semillas de la ronda r+1. Una llave no
abre nada dentro de la ronda en que se obtiene; así cada ronda contiene
exactamente las llaves que se vuelven obtenibles con las anteriores
(FR-308).

Cada sala se encola una vez, cada salida se examina una vez desde su
origen y se libera a lo sumo una vez: O(V + E + L), más O((E + L) log K)
de la numeración y O(K log K) de ordenar las rondas (FR-335). Todo por
índice denso de sala (`Sala.indice`) y por número de llave
(`NumeracionLlaves`), en `Vector`; sin dict ni set (principio I).

No modifica el Mapa ni las puertas, no pide contenido (FR-321) y no es
estado del juego (FR-327).
"""

from crypta.Modelo.ResultadoVerificacion import Reporte, ResultadoVerificacion
from crypta.Modelo.Sala import DIRECCIONES
from crypta.estructuras.Cola import Cola
from crypta.estructuras.NumeracionLlaves import NumeracionLlaves
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


def vector_lleno(n, valor):
    vector = Vector(max(1, n))

    for _ in range(n):
        vector.agregar(valor)

    return vector


def juntar_ids_de_llaves(mapa, datos_cripta, ubicaciones):
    """Las llaves de la cripta (glosario de la spec): las de la ubicación,
    las que piden las salidas cerradas y `llave_salida`, con repetidos."""
    ids = Vector()

    for i in range(len(ubicaciones)):
        ids.agregar(ubicaciones.obtener(i).id_llave)

    for i in range(mapa.cantidad_salas()):
        sala = mapa.sala_por_indice(i)

        for d in range(len(DIRECCIONES)):
            puerta = sala.obtener_puerta(DIRECCIONES[d])

            if puerta is not None and puerta.cerrada and puerta.llave is not None:
                ids.agregar(puerta.llave)

    llave_salida = datos_cripta.get("llave_salida")

    if llave_salida is not None:
        ids.agregar(llave_salida)

    return ids


def llaves_por_sala(cantidad_salas, ubicaciones):
    """`Vector` de V posiciones: None o un `Vector` con los números de las
    llaves ubicadas en esa sala. Necesita `numero_llave` ya asignado."""
    por_sala = vector_lleno(cantidad_salas, None)

    for i in range(len(ubicaciones)):
        ubicacion = ubicaciones.obtener(i)
        lista = por_sala.obtener(ubicacion.indice_sala)

        if lista is None:
            lista = Vector(2)
            por_sala.asignar(ubicacion.indice_sala, lista)

        lista.agregar(ubicacion.numero_llave)

    return por_sala


def puerta_de_salida_desde(mapa, datos_cripta, en_region):
    """FR-305: ¿hay una salida cerrada que pide `llave_salida`, sale de una
    sala de la región (`en_region(indice)`) y lleva a `sala_salida`?"""
    llave_salida = datos_cripta.get("llave_salida")
    id_sala_salida = datos_cripta.get("sala_salida")

    if llave_salida is None or id_sala_salida is None:
        return False

    sala_salida = mapa.obtener_sala(id_sala_salida)

    if sala_salida is None:
        return False

    entradas = sala_salida.entradas

    for i in range(len(entradas)):
        puerta, origen = entradas.obtener(i)

        if (puerta.cerrada and puerta.llave == llave_salida
                and en_region(origen.indice)):
            return True

    return False


class _Verificacion:
    """El estado de una verificación; se crea y se descarta en cada llamada
    (data-model.md, «Recorrido»)."""

    def __init__(self, mapa, datos_cripta, ubicaciones, observar):
        self.mapa = mapa
        self.datos = datos_cripta
        self.ubicaciones = ubicaciones
        self.observar = observar

        self.numeracion = NumeracionLlaves(
            juntar_ids_de_llaves(mapa, datos_cripta, ubicaciones))

        for i in range(len(ubicaciones)):
            ubicacion = ubicaciones.obtener(i)
            ubicacion.numero_llave = self.numeracion.numero(ubicacion.id_llave)

        v = mapa.cantidad_salas()
        k = len(self.numeracion)

        self.llaves_en_sala = llaves_por_sala(v, ubicaciones)
        self.ronda_sala = vector_lleno(v, -1)
        self.ronda_llave = vector_lleno(k, -1)
        self.abre = vector_lleno(k, False)
        self.estacionadas = vector_lleno(k, None)
        self.rondas = Vector()

    # -- recorrido por oleadas (D3) ------------------------------------

    def llave_que_falta(self, puerta):
        """Número de la llave que hace falta para cruzar, o -1 si la salida
        ya es cruzable (abierta, cerrada sin llave o con llave que abre)."""
        if not puerta.cerrada or puerta.llave is None:
            return -1

        numero = self.numeracion.numero(puerta.llave)
        return -1 if self.abre.obtener(numero) else numero

    def marcar(self, indice, ronda, pendientes):
        if self.ronda_sala.obtener(indice) == -1:
            self.ronda_sala.asignar(indice, ronda)
            pendientes.encolar(indice)

    def procesar_sala(self, x, ronda, pendientes, nuevas):
        if self.observar is not None:
            self.observar("region", x)

        llaves = self.llaves_en_sala.obtener(x)

        if llaves is not None:
            for i in range(len(llaves)):
                k = llaves.obtener(i)

                if self.ronda_llave.obtener(k) == -1:
                    self.ronda_llave.asignar(k, ronda)
                    nuevas.agregar(k)

        sala = self.mapa.sala_por_indice(x)

        for d in range(len(DIRECCIONES)):
            puerta = sala.obtener_puerta(DIRECCIONES[d])

            if puerta is None or puerta.sala_destino_ref is None:
                continue

            if self.observar is not None:
                self.observar("salida", x, d)

            y = puerta.sala_destino_ref.indice
            falta = self.llave_que_falta(puerta)

            if falta == -1:
                self.marcar(y, ronda, pendientes)
            else:
                estacionadas = self.estacionadas.obtener(falta)

                if estacionadas is None:
                    estacionadas = Vector(2)
                    self.estacionadas.asignar(falta, estacionadas)

                estacionadas.agregar((x, d, y))

    def cerrar_ronda(self, nuevas, ronda, pendientes):
        """Agrega la ronda al orden, activa sus llaves y libera sus puertas
        estacionadas como semillas de la ronda siguiente."""
        ordenar(nuevas)
        ids = Vector(max(1, len(nuevas)))

        for i in range(len(nuevas)):
            k = nuevas.obtener(i)
            ids.agregar(self.numeracion.id_de(k))
            self.abre.asignar(k, True)

        self.rondas.agregar(ids)

        for i in range(len(nuevas)):
            k = nuevas.obtener(i)
            estacionadas = self.estacionadas.obtener(k)

            if estacionadas is None:
                continue

            self.estacionadas.asignar(k, None)

            for j in range(len(estacionadas)):
                x, d, y = estacionadas.obtener(j)

                if self.observar is not None:
                    self.observar("salida", x, d)

                self.marcar(y, ronda + 1, pendientes)

    def recorrer(self):
        pendientes = Cola()
        inicial = self.mapa.obtener_sala(self.datos.get("sala_inicial"))

        if inicial is not None:
            self.marcar(inicial.indice, 0, pendientes)

        ronda = 0

        while True:
            nuevas = Vector()

            while not pendientes.esta_vacia():
                self.procesar_sala(pendientes.desencolar(), ronda, pendientes,
                                   nuevas)

            if len(nuevas) == 0:
                return

            self.cerrar_ronda(nuevas, ronda, pendientes)
            ronda += 1

    # -- resultado -------------------------------------------------------

    def en_region(self, indice):
        return self.ronda_sala.obtener(indice) != -1

    def resultado(self):
        self.recorrer()

        llave_salida = self.datos.get("llave_salida")
        numero_salida = (self.numeracion.numero(llave_salida)
                         if llave_salida is not None else None)
        salida_obtenible = (numero_salida is not None
                            and self.ronda_llave.obtener(numero_salida) != -1)

        if salida_obtenible and puerta_de_salida_desde(
                self.mapa, self.datos, self.en_region):
            return ResultadoVerificacion(True, self.rondas)

        return ResultadoVerificacion(False, self.rondas, self.reporte())

    def reporte(self):
        """Reporte de una cripta no resoluble. Por ahora solo las llaves no
        obtenibles (FR-309); el resto llega con la historia 2."""
        reporte = Reporte()

        for k in range(len(self.numeracion)):
            if self.ronda_llave.obtener(k) == -1:
                reporte.no_obtenibles.agregar(self.numeracion.id_de(k))

        return reporte


def verificar(mapa, datos_cripta, ubicaciones, observar=None):
    """Verifica la cripta con su esqueleto (`mapa`), sus datos generales
    (`sala_inicial`, `sala_salida`, `llave_salida`) y la ubicación de las
    llaves ya validada (`Vector` de `UbicacionLlave`). Devuelve un
    `ResultadoVerificacion` (FR-301 a FR-308).

    `observar(evento, *datos)` es solo para las pruebas (FR-313): se llama
    con ("region", sala) al procesar una sala de la región y con
    ("salida", sala, dirección) cada vez que se examina una salida."""
    return _Verificacion(mapa, datos_cripta, ubicaciones, observar).resultado()
