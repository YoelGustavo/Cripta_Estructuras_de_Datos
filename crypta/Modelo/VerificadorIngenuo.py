"""Alternativa ingenua de la verificación (capacidad 003; research D8).

Existe para medirla en el `--bench` (FR-331) y para comprobar el resultado
del verificador en las pruebas y en el bench (FR-332, SC-302). No usa
puertas estacionadas: **repite el recorrido completo** desde
`sala_inicial`, con marcas nuevas, cada vez que aparecen llaves nuevas.
Con llaves encadenadas cada repetición obtiene una sola llave: «repetir el
recorrido cada vez que se obtiene una llave», O(R · (V + E)).

Comparte con `Verificador` solo lo que no se mide: la lectura validada de
la ubicación, la numeración de llaves y el criterio de FR-305.
"""

from crypta.Modelo.ResultadoVerificacion import Reporte, ResultadoVerificacion
from crypta.Modelo.Sala import DIRECCIONES
from crypta.Modelo.Verificador import (juntar_ids_de_llaves, llaves_por_sala,
                                       puerta_de_salida_desde, vector_lleno)
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

    if (numero_salida is not None and tengo.obtener(numero_salida)
            and puerta_de_salida_desde(mapa, datos_cripta, vistas.obtener)):
        return ResultadoVerificacion(True, rondas)

    reporte = Reporte()

    for k in range(len(numeracion)):
        if not tengo.obtener(k):
            reporte.no_obtenibles.agregar(numeracion.id_de(k))

    return ResultadoVerificacion(False, rondas, reporte)
