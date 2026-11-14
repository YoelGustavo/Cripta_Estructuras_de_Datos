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

from crypta.Modelo.ResultadoVerificacion import (NO_ESTA_EN_LA_CRIPTA,
                                                SALA_INALCANZABLE, Dependencia,
                                                PuertaFrontera, Reporte,
                                                ResultadoVerificacion)
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
        hay_puerta = puerta_de_salida_desde(self.mapa, self.datos,
                                            self.en_region)

        if salida_obtenible and hay_puerta:
            return ResultadoVerificacion(True, self.rondas)

        reporte = Reporte()
        llenar_avisos(reporte, self.datos, salida_obtenible, hay_puerta)
        self.llenar_no_obtenibles(reporte)
        self.llenar_frontera(reporte)
        self.llenar_ubicaciones(reporte)
        self.recorrer_capas()
        self.llenar_dependencias(reporte)
        self.llenar_ciclos(reporte)
        return ResultadoVerificacion(False, self.rondas, reporte)

    def obtenible(self, k):
        return self.ronda_llave.obtener(k) != -1

    def bloqueada(self, puerta):
        """Puerta bloqueada: cerrada y pide una llave no obtenible."""
        return (puerta.cerrada and puerta.llave is not None
                and not self.obtenible(self.numeracion.numero(puerta.llave)))

    # -- partes del reporte sin recorrer de nuevo (D6) -------------------

    def llenar_no_obtenibles(self, reporte):
        """FR-309: recorrer 0..K-1 ya es el orden por id."""
        for k in range(len(self.numeracion)):
            if not self.obtenible(k):
                reporte.no_obtenibles.agregar(self.numeracion.id_de(k))

    def llenar_frontera(self, reporte):
        """FR-310: salas de la región por índice (= por id) y salidas en
        N, S, E, O; O(V + E), sin ordenar."""
        self.pide_frontera = vector_lleno(len(self.numeracion), False)

        for x in range(self.mapa.cantidad_salas()):
            if not self.en_region(x):
                continue

            sala = self.mapa.sala_por_indice(x)

            for d in range(len(DIRECCIONES)):
                puerta = sala.obtener_puerta(DIRECCIONES[d])

                if (puerta is None or puerta.sala_destino_ref is None
                        or not self.bloqueada(puerta)
                        or self.en_region(puerta.sala_destino_ref.indice)):
                    continue

                reporte.frontera.agregar(PuertaFrontera(
                    sala.id, DIRECCIONES[d], puerta.sala_destino_ref.id,
                    puerta.llave))
                self.pide_frontera.asignar(
                    self.numeracion.numero(puerta.llave), True)

    def llenar_ubicaciones(self, reporte):
        """FR-311: las ubicaciones se ordenan una vez por (llave, sala,
        enemigo); sin enemigo cuenta como "" y va primero en su sala. Un
        `Vector` de K+1 posiciones dice dónde empieza cada llave."""
        k_total = len(self.numeracion)
        ordenadas = Vector(max(1, len(self.ubicaciones)))

        for i in range(len(self.ubicaciones)):
            ordenadas.agregar(self.ubicaciones.obtener(i))

        ordenar(ordenadas, clave=lambda u: (u.numero_llave, u.id_sala,
                                            u.enemigo or ""))
        self.inicio_ubic = vector_lleno(k_total + 1, 0)
        siguiente = 0

        for k in range(k_total):
            self.inicio_ubic.asignar(k, siguiente)

            while (siguiente < len(ordenadas)
                   and ordenadas.obtener(siguiente).numero_llave == k):
                siguiente += 1

        self.inicio_ubic.asignar(k_total, siguiente)

        for k in range(k_total):
            if not self.pide_frontera.obtener(k):
                continue

            lugares = Vector()

            for i in range(self.inicio_ubic.obtener(k),
                           self.inicio_ubic.obtener(k + 1)):
                ubicacion = ordenadas.obtener(i)
                lugares.agregar((ubicacion.id_sala, ubicacion.enemigo))

            reporte.ubicaciones_frontera.agregar(
                (self.numeracion.id_de(k), lugares))

    # -- capas más allá de la frontera (D4) ------------------------------

    def marcar_en_capa(self, y, capa, origen, pendientes):
        self.capa_sala.asignar(y, capa)
        self.origen_sala.asignar(y, origen)
        pendientes.encolar(y)

        if self.observar is not None:
            self.observar("capa", y)

        llaves = self.llaves_en_sala.obtener(y)

        if llaves is None:
            return

        for i in range(len(llaves)):
            k = llaves.obtener(i)

            # La primera marca es la menor (capa, origen): las capas crecen
            # y dentro de cada capa los orígenes también.
            if not self.obtenible(k) and self.dependencia.obtener(k) == -1:
                self.dependencia.asignar(k, origen)

    def libre(self, y):
        return not self.en_region(y) and self.capa_sala.obtener(y) == -1

    def recorrer_capas(self):
        """FR-314: el mismo recorrido sigue más allá de la frontera. Cruzar
        una puerta bloqueada cuesta 1 y cualquier otra salida 0. Cada sala
        fuera de la región recibe (capa, origen): la menor cantidad de
        puertas bloqueadas desde la región y, entre esos caminos, la menor
        llave de su primera puerta bloqueada. Nunca un recorrido por llave
        (FR-313). O(V + E + L + E log E)."""
        v = self.mapa.cantidad_salas()
        k_total = len(self.numeracion)
        self.capa_sala = vector_lleno(v, -1)
        self.origen_sala = vector_lleno(v, -1)
        self.dependencia = vector_lleno(k_total, -1)

        # Capa 1: las puertas que siguen estacionadas (llaves que nunca
        # abrieron), recorridas por llave: ya salen ordenadas por origen.
        semillas = Vector()

        for k in range(k_total):
            estacionadas = self.estacionadas.obtener(k)

            if estacionadas is None:
                continue

            for j in range(len(estacionadas)):
                _, _, y = estacionadas.obtener(j)

                if not self.en_region(y):
                    semillas.agregar((k, y))

        capa = 1

        while len(semillas) > 0:
            siguientes = Vector()
            i = 0

            while i < len(semillas):
                origen = semillas.obtener(i)[0]
                pendientes = Cola()

                while i < len(semillas) and semillas.obtener(i)[0] == origen:
                    y = semillas.obtener(i)[1]

                    if self.libre(y):
                        self.marcar_en_capa(y, capa, origen, pendientes)

                    i += 1

                self.inundar(pendientes, capa, origen, siguientes)

            ordenar(siguientes, clave=lambda semilla: semilla[0])
            semillas = siguientes
            capa += 1

    def inundar(self, pendientes, capa, origen, siguientes):
        """Expande un grupo de la capa por salidas no bloqueadas (costo 0);
        las bloqueadas van a la capa siguiente con el origen heredado."""
        while not pendientes.esta_vacia():
            x = pendientes.desencolar()
            sala = self.mapa.sala_por_indice(x)

            for d in range(len(DIRECCIONES)):
                puerta = sala.obtener_puerta(DIRECCIONES[d])

                if puerta is None or puerta.sala_destino_ref is None:
                    continue

                if self.observar is not None:
                    self.observar("salida", x, d)

                y = puerta.sala_destino_ref.indice

                if not self.libre(y):
                    continue

                if self.bloqueada(puerta):
                    siguientes.agregar((origen, y))
                else:
                    self.marcar_en_capa(y, capa, origen, pendientes)

    def llenar_dependencias(self, reporte):
        """FR-312: por id; sin dependencia, el motivo."""
        for k in range(len(self.numeracion)):
            if self.obtenible(k):
                continue

            llave = self.numeracion.id_de(k)
            dependencia = self.dependencia.obtener(k)

            if dependencia != -1:
                reporte.dependencias.agregar(
                    Dependencia(llave, self.numeracion.id_de(dependencia)))
            elif self.inicio_ubic.obtener(k) == self.inicio_ubic.obtener(k + 1):
                reporte.dependencias.agregar(
                    Dependencia(llave, motivo=NO_ESTA_EN_LA_CRIPTA))
            else:
                reporte.dependencias.agregar(
                    Dependencia(llave, motivo=SALA_INALCANZABLE))

    # -- ciclos (D5) -----------------------------------------------------

    def llenar_ciclos(self, reporte):
        """FR-315: cada llave tiene a lo sumo una dependencia, así que cada
        componente tiene a lo sumo un ciclo. Marcas de tres estados (0 sin
        ver, 1 en el camino actual, 2 terminada); cada ciclo se rota a su
        menor llave y al final se ordenan por ella. O(K log K)."""
        k_total = len(self.numeracion)
        estado = vector_lleno(k_total, 0)
        ciclos = Vector()

        for inicio in range(k_total):
            if self.obtenible(inicio) or estado.obtener(inicio) != 0:
                continue

            camino = Vector()
            k = inicio

            while k != -1 and estado.obtener(k) == 0:
                estado.asignar(k, 1)
                camino.agregar(k)
                k = self.dependencia.obtener(k)

            if k != -1 and estado.obtener(k) == 1:
                ciclos.agregar(self.ciclo_desde(camino, k))

            for i in range(len(camino)):
                estado.asignar(camino.obtener(i), 2)

        ordenar(ciclos, clave=lambda ciclo: ciclo[0])

        for i in range(len(ciclos)):
            reporte.ciclos.agregar(ciclos.obtener(i)[1])

    def ciclo_desde(self, camino, k):
        """El ciclo que cierra `k` al final de `camino`, como (menor
        número, `Vector` de ids desde la menor llave)."""
        desde = len(camino) - 1

        while camino.obtener(desde) != k:
            desde -= 1

        largo = len(camino) - desde
        menor = desde

        for i in range(desde, len(camino)):
            if camino.obtener(i) < camino.obtener(menor):
                menor = i

        ids = Vector(largo)

        for paso in range(largo):
            i = desde + (menor - desde + paso) % largo
            ids.agregar(self.numeracion.id_de(camino.obtener(i)))

        return (camino.obtener(menor), ids)


def llenar_avisos(reporte, datos_cripta, salida_obtenible, hay_puerta):
    """FR-317 y FR-318."""
    reporte.llave_salida = datos_cripta.get("llave_salida")
    reporte.sala_salida = datos_cripta.get("sala_salida")
    reporte.falta_sala_salida = reporte.sala_salida is None
    reporte.falta_llave_salida = reporte.llave_salida is None
    reporte.salida_sin_puerta = (salida_obtenible and not hay_puerta
                                 and reporte.sala_salida is not None)


def verificar(mapa, datos_cripta, ubicaciones, observar=None):
    """Verifica la cripta con su esqueleto (`mapa`), sus datos generales
    (`sala_inicial`, `sala_salida`, `llave_salida`) y la ubicación de las
    llaves ya validada (`Vector` de `UbicacionLlave`). Devuelve un
    `ResultadoVerificacion` (FR-301 a FR-308).

    `observar(evento, *datos)` es solo para las pruebas (FR-313): se llama
    con ("region", sala) al procesar una sala de la región, con ("capa",
    sala) al marcar una sala en una capa más allá de la frontera y con
    ("salida", sala, dirección) cada vez que se examina una salida."""
    return _Verificacion(mapa, datos_cripta, ubicaciones, observar).resultado()
