"""Equivalencia de la verificación con la alternativa ingenua y con una
referencia escrita en la prueba (capacidad 003; FR-307, SC-302).

    python -m unittest -v tests.test_equivalencia_resolubilidad

La referencia usa `set` y `dict` de Python a propósito: es un recorrido
simple, independiente del verificador, que solo existe en la prueba (el
juego nunca lo usa; principio I).
"""

import random
import unittest

from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
from crypta.Modelo.Verificador import verificar
from crypta.Modelo.VerificadorIngenuo import verificar_ingenuo
from tests.ayudas_cripta import datos_generales, mapa_de, sala, salida


CRIPTAS = 240
OPUESTA = {"N": "S", "S": "N", "E": "O", "O": "E"}


def generar(semilla):
    """Una cripta pequeña al azar: salas con salidas abiertas, cerradas sin
    llave, cerradas con llave y sin vuelta; llaves con 0, 1 o 2
    ubicaciones (a veces de un enemigo); `llave_salida` y `sala_salida`."""
    azar = random.Random(semilla)
    n = azar.randint(2, 12)
    k = azar.randint(1, 6)
    llaves = [f"itm_llave_{chr(ord('a') + i)}" for i in range(k)]
    salidas = {i: {} for i in range(1, n + 1)}

    for _ in range(azar.randint(n - 1, 3 * n)):
        x, y = azar.randint(1, n), azar.randint(1, n)
        libres = [d for d in "NSEO"
                  if d not in salidas[x] and OPUESTA[d] not in salidas[y]]

        if x == y or not libres or any(
                datos["sala"] == y for datos in salidas[x].values()) or any(
                datos["sala"] == x for datos in salidas[y].values()):
            continue

        d = azar.choice(libres)
        tipo = azar.random()

        if tipo < 0.4:
            datos = salida(y)
        elif tipo < 0.5:
            datos = salida(y, cerrada=True)
        else:
            datos = salida(y, cerrada=True, llave=azar.choice(llaves))

        salidas[x][d] = datos

        if azar.random() < 0.8:            # con vuelta: el mismo estado
            vuelta = dict(datos)
            vuelta["sala"] = x
            salidas[y][OPUESTA[d]] = vuelta

    ubicaciones = []

    for llave in llaves:
        for _ in range(azar.choice((0, 1, 1, 1, 2))):
            entrada = {"id": llave, "sala": azar.randint(1, n)}

            if azar.random() < 0.2:
                entrada["enemigo"] = f"e-{azar.randint(1, 99)}"

            ubicaciones.append(entrada)

    azar.shuffle(ubicaciones)
    esqueleto = [sala(i, salidas[i]) for i in range(1, n + 1)]
    generales = datos_generales(
        esqueleto, sala_inicial=1,
        sala_salida=azar.choice([None] + list(range(1, n + 1)) * 3),
        llave_salida=azar.choice([None] + llaves * 3))
    return esqueleto, generales, {"llaves": ubicaciones}


def alcanzables(esqueleto, inicial, tengo):
    """Salas alcanzables desde `inicial` con las llaves de `tengo`."""
    por_id = {datos["id"]: datos for datos in esqueleto}
    vistas = {inicial}
    pendientes = [inicial]

    while pendientes:
        actual = pendientes.pop()

        for datos in por_id[actual]["salidas"].values():
            cerrada = datos.get("cerrada", False)
            llave = datos.get("llave")

            if cerrada and llave is not None and llave not in tengo:
                continue

            if datos["sala"] not in vistas:
                vistas.add(datos["sala"])
                pendientes.append(datos["sala"])

    return vistas


def rondas_de(resultado):
    rondas = []

    for i in range(len(resultado.rondas)):
        ronda = resultado.rondas.obtener(i)
        rondas.append([ronda.obtener(j) for j in range(len(ronda))])

    return rondas


class TestOrdenSeguible(unittest.TestCase):
    """FR-307, SC-302: el orden se sigue paso a paso y coincide con el de la
    alternativa ingenua."""

    def test_orden_seguible_y_igual_a_la_ingenua_FR_307_SC_302(self):
        resolubles = 0

        for semilla in range(CRIPTAS):
            esqueleto, generales, llaves = generar(semilla)

            with self.subTest(semilla=semilla):
                mapa = mapa_de(esqueleto)
                ubicaciones = leer_ubicaciones(llaves, mapa)
                resultado = verificar(mapa, generales, ubicaciones)
                ingenuo = verificar_ingenuo(mapa, generales, ubicaciones)
                rondas = rondas_de(resultado)

                self.assertEqual(rondas, rondas_de(ingenuo))
                self.assertEqual(resultado.resoluble, ingenuo.resoluble)

                lugares = {}

                for entrada in llaves["llaves"]:
                    lugares.setdefault(entrada["id"], set()).add(entrada["sala"])

                # Paso a paso: cada llave de la ronda r se alcanza con las
                # de las rondas anteriores, y no con menos (FR-307, FR-308).
                tengo = set()
                antes = None

                for ronda in rondas:
                    self.assertEqual(ronda, sorted(ronda))
                    region = alcanzables(esqueleto, 1, tengo)

                    for llave in ronda:
                        self.assertNotIn(llave, tengo)
                        self.assertTrue(lugares[llave] & region, llave)

                        if antes is not None:
                            self.assertFalse(lugares[llave] & antes, llave)

                    antes = region
                    tengo |= set(ronda)

                # Al final no queda ninguna llave obtenible fuera del orden.
                region = alcanzables(esqueleto, 1, tengo)
                obtenibles = {llave for llave, salas in lugares.items()
                              if salas & region}
                self.assertEqual(obtenibles, tengo)

                # FR-305 con la misma referencia.
                llave_salida = generales["llave_salida"]
                sala_salida = generales["sala_salida"]
                esperado = llave_salida in tengo and any(
                    datos["sala"] == sala_salida and datos.get("cerrada")
                    and datos.get("llave") == llave_salida
                    for origen in esqueleto if origen["id"] in region
                    for datos in origen["salidas"].values())
                self.assertEqual(resultado.resoluble, esperado)
                resolubles += esperado

        # Que la muestra tenga de los dos casos.
        self.assertGreater(resolubles, 10)
        self.assertLess(resolubles, CRIPTAS - 10)


if __name__ == "__main__":
    unittest.main()
