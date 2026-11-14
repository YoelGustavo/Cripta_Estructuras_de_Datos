"""Alternativa ingenua de la verificación (capacidad 003; research D8).

Existe para medirla en el `--bench` (FR-331) y para comprobar el resultado
del verificador en las pruebas y en el bench (FR-332, SC-302). No usa
puertas estacionadas: **repite el recorrido completo** desde
`sala_inicial`, con marcas nuevas, cada vez que aparecen llaves nuevas.
Con llaves encadenadas cada repetición obtiene una sola llave: «repetir el
recorrido cada vez que se obtiene una llave», O(R · (V + E)).

Si no es resoluble, el reporte también se calcula por su cuenta: frontera
y ubicaciones con búsquedas lineales, las dependencias con **un recorrido
0-1 por cada llave de la frontera** (lo que FR-313 prohíbe al verificador)
y los ciclos siguiendo la cadena de cada llave.

Comparte con `Verificador` solo lo que no se mide: la lectura validada de
la ubicación, la numeración de llaves y los criterios de FR-305, FR-317 y
FR-318.
"""

from crypta.Modelo.ResultadoVerificacion import (NO_ESTA_EN_LA_CRIPTA,
                                                SALA_INALCANZABLE, Dependencia,
                                                PuertaFrontera, Reporte,
                                                ResultadoVerificacion)
from crypta.Modelo.Sala import DIRECCIONES
from crypta.Modelo.Verificador import (juntar_ids_de_llaves, llaves_por_sala,
                                       llenar_avisos, puerta_de_salida_desde,
                                       vector_lleno)
from crypta.estructuras.Cola import Cola
from crypta.estructuras.NumeracionLlaves import NumeracionLlaves
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


def _recorrido_completo(mapa, inicial, numeracion, tengo):
    """Marcas (`Vector` de V booleanos) de las salas alcanzables desde
    `inicial` con las llaves de `tengo`. Siempre desde cero."""
    vistas = vector_lleno(mapa.cantidad_salas(), False)

    if inicial is None:
        return vistas

    pendientes = Cola()
    vistas.asignar(inicial.indice, True)
    pendientes.encolar(inicial.indice)

    while not pendientes.esta_vacia():
        sala = mapa.sala_por_indice(pendientes.desencolar())

        for d in range(len(DIRECCIONES)):
            puerta = sala.obtener_puerta(DIRECCIONES[d])

            if puerta is None or puerta.sala_destino_ref is None:
                continue

            if (puerta.cerrada and puerta.llave is not None
                    and not tengo.obtener(numeracion.numero(puerta.llave))):
                continue

            y = puerta.sala_destino_ref.indice

            if not vistas.obtener(y):
                vistas.asignar(y, True)
                pendientes.encolar(y)

    return vistas


def verificar_ingenuo(mapa, datos_cripta, ubicaciones):
    """Mismo contrato que `Verificador.verificar`."""
    numeracion = NumeracionLlaves(
        juntar_ids_de_llaves(mapa, datos_cripta, ubicaciones))

    for i in range(len(ubicaciones)):
        ubicacion = ubicaciones.obtener(i)
        ubicacion.numero_llave = numeracion.numero(ubicacion.id_llave)

    v = mapa.cantidad_salas()
    llaves_en_sala = llaves_por_sala(v, ubicaciones)
    tengo = vector_lleno(len(numeracion), False)
    inicial = mapa.obtener_sala(datos_cripta.get("sala_inicial"))
    rondas = Vector()

    while True:
        vistas = _recorrido_completo(mapa, inicial, numeracion, tengo)
        nuevas = Vector()

        for x in range(v):
            llaves = llaves_en_sala.obtener(x)

            if not vistas.obtener(x) or llaves is None:
                continue

            for i in range(len(llaves)):
                k = llaves.obtener(i)

                if not tengo.obtener(k):
                    tengo.asignar(k, True)   # no abre hasta la próxima vuelta
                    nuevas.agregar(k)

        if len(nuevas) == 0:
            break

        ordenar(nuevas)
        ids = Vector(max(1, len(nuevas)))

        for i in range(len(nuevas)):
            ids.agregar(numeracion.id_de(nuevas.obtener(i)))

        rondas.agregar(ids)

    llave_salida = datos_cripta.get("llave_salida")
    numero_salida = (numeracion.numero(llave_salida)
                     if llave_salida is not None else None)
    salida_obtenible = numero_salida is not None and tengo.obtener(numero_salida)
    hay_puerta = puerta_de_salida_desde(mapa, datos_cripta, vistas.obtener)

    if salida_obtenible and hay_puerta:
        return ResultadoVerificacion(True, rondas)

    return ResultadoVerificacion(
        False, rondas,
        _reporte(mapa, datos_cripta, ubicaciones, numeracion, tengo, vistas,
                 salida_obtenible, hay_puerta))


# ---------------------------------------------------------------------------
# Reporte por su cuenta: búsquedas lineales y un recorrido por llave
# ---------------------------------------------------------------------------

def _bloqueada(puerta, numeracion, tengo):
    return (puerta.cerrada and puerta.llave is not None
            and not tengo.obtener(numeracion.numero(puerta.llave)))


def _contiene(vector, valor):
    for i in range(len(vector)):
        if vector.obtener(i) == valor:
            return True

    return False


def _frontera(mapa, numeracion, tengo, vistas):
    """Pares (PuertaFrontera, número de llave) de la frontera, por sala de
    origen y N, S, E, O."""
    frontera = Vector()

    for x in range(mapa.cantidad_salas()):
        if not vistas.obtener(x):
            continue

        sala = mapa.sala_por_indice(x)

        for d in range(len(DIRECCIONES)):
            puerta = sala.obtener_puerta(DIRECCIONES[d])

            if (puerta is not None and puerta.sala_destino_ref is not None
                    and _bloqueada(puerta, numeracion, tengo)
                    and not vistas.obtener(puerta.sala_destino_ref.indice)):
                frontera.agregar((PuertaFrontera(
                    sala.id, DIRECCIONES[d], puerta.sala_destino_ref.id,
                    puerta.llave), numeracion.numero(puerta.llave)))

    return frontera


def _clave_lugar(ubicacion):
    enemigo = ubicacion.enemigo if ubicacion.enemigo is not None else ""
    return (ubicacion.id_sala, enemigo)


def _lugares(ubicaciones, k):
    """Ubicaciones de la llave k, buscadas una por una y ordenadas por sala y
    enemigo (sin enemigo primero)."""
    propias = Vector()

    for i in range(len(ubicaciones)):
        ubicacion = ubicaciones.obtener(i)

        if ubicacion.numero_llave == k:
            propias.agregar(ubicacion)

    ordenar(propias, clave=_clave_lugar)
    lugares = Vector()

    for i in range(len(propias)):
        lugares.agregar((propias.obtener(i).id_sala, propias.obtener(i).enemigo))

    return lugares


def _capas_desde(mapa, numeracion, tengo, vistas, semillas):
    """Recorrido 0-1 por niveles desde `semillas` (índices de sala, capa 1):
    capa de cada sala fuera de la región (-1 si no se alcanza)."""
    capa_de = vector_lleno(mapa.cantidad_salas(), -1)
    actual = Cola()
    siguiente = Cola()

    for i in range(len(semillas)):
        siguiente.encolar(semillas.obtener(i))

    capa = 0

    while not siguiente.esta_vacia():
        capa += 1

        while not siguiente.esta_vacia():
            y = siguiente.desencolar()

            if capa_de.obtener(y) == -1:
                capa_de.asignar(y, capa)
                actual.encolar(y)

        while not actual.esta_vacia():
            sala = mapa.sala_por_indice(actual.desencolar())

            for d in range(len(DIRECCIONES)):
                puerta = sala.obtener_puerta(DIRECCIONES[d])

                if puerta is None or puerta.sala_destino_ref is None:
                    continue

                y = puerta.sala_destino_ref.indice

                if vistas.obtener(y) or capa_de.obtener(y) != -1:
                    continue

                if _bloqueada(puerta, numeracion, tengo):
                    siguiente.encolar(y)
                else:
                    capa_de.asignar(y, capa)
                    actual.encolar(y)

    return capa_de


def _dependencias(mapa, numeracion, tengo, vistas, frontera, ubicaciones):
    """FR-314 por fuerza bruta: un recorrido 0-1 por cada llave distinta de
    la frontera, desde los destinos de sus puertas; cada llave no obtenible
    depende de la de menor (capas, id) que alcance alguna de sus
    ubicaciones."""
    k_total = len(numeracion)
    mejor_capa = vector_lleno(k_total, -1)
    mejor_llave = vector_lleno(k_total, -1)

    for f in range(k_total):
        semillas = Vector()

        for i in range(len(frontera)):
            puerta, k = frontera.obtener(i)

            if k == f:
                semillas.agregar(mapa.obtener_sala(puerta.id_destino).indice)

        if len(semillas) == 0:
            continue

        capa_de = _capas_desde(mapa, numeracion, tengo, vistas, semillas)

        for i in range(len(ubicaciones)):
            ubicacion = ubicaciones.obtener(i)
            c = ubicacion.numero_llave
            capa = capa_de.obtener(ubicacion.indice_sala)

            if tengo.obtener(c) or capa == -1:
                continue

            # f recorre en orden creciente: ante un empate gana la primera.
            if mejor_capa.obtener(c) == -1 or capa < mejor_capa.obtener(c):
                mejor_capa.asignar(c, capa)
                mejor_llave.asignar(c, f)

    return mejor_llave


def _ciclos(numeracion, tengo, dependencia):
    """Para cada llave no obtenible se sigue su cadena hasta K pasos; si
    vuelve a ella y es la menor del ciclo, el ciclo empieza ahí. Ya salen
    ordenados por su primera llave. O(K^2)."""
    k_total = len(numeracion)
    ciclos = Vector()

    for inicio in range(k_total):
        if tengo.obtener(inicio):
            continue

        miembros = Vector()
        k = inicio

        for _ in range(k_total):
            miembros.agregar(k)
            k = dependencia.obtener(k)

            if k == -1 or k == inicio:
                break

        if k != inicio:
            continue

        es_menor = True

        for i in range(len(miembros)):
            if miembros.obtener(i) < inicio:
                es_menor = False

        if es_menor:
            ids = Vector(len(miembros))

            for i in range(len(miembros)):
                ids.agregar(numeracion.id_de(miembros.obtener(i)))

            ciclos.agregar(ids)

    return ciclos


def _reporte(mapa, datos_cripta, ubicaciones, numeracion, tengo, vistas,
             salida_obtenible, hay_puerta):
    reporte = Reporte()
    llenar_avisos(reporte, datos_cripta, salida_obtenible, hay_puerta)
    k_total = len(numeracion)

    for k in range(k_total):
        if not tengo.obtener(k):
            reporte.no_obtenibles.agregar(numeracion.id_de(k))

    frontera = _frontera(mapa, numeracion, tengo, vistas)
    llaves_frontera = Vector()

    for i in range(len(frontera)):
        puerta, k = frontera.obtener(i)
        reporte.frontera.agregar(puerta)

        if not _contiene(llaves_frontera, k):
            llaves_frontera.agregar(k)

    ordenar(llaves_frontera)

    for i in range(len(llaves_frontera)):
        k = llaves_frontera.obtener(i)
        reporte.ubicaciones_frontera.agregar(
            (numeracion.id_de(k), _lugares(ubicaciones, k)))

    dependencia = _dependencias(mapa, numeracion, tengo, vistas, frontera,
                                ubicaciones)

    for k in range(k_total):
        if tengo.obtener(k):
            continue

        llave = numeracion.id_de(k)

        if dependencia.obtener(k) != -1:
            reporte.dependencias.agregar(
                Dependencia(llave, numeracion.id_de(dependencia.obtener(k))))
        elif len(_lugares(ubicaciones, k)) == 0:
            reporte.dependencias.agregar(
                Dependencia(llave, motivo=NO_ESTA_EN_LA_CRIPTA))
        else:
            reporte.dependencias.agregar(
                Dependencia(llave, motivo=SALA_INALCANZABLE))

    ciclos = _ciclos(numeracion, tengo, dependencia)

    for i in range(len(ciclos)):
        reporte.ciclos.agregar(ciclos.obtener(i))

    return reporte
