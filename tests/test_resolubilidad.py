"""Pruebas de la verificación de resolubilidad (capacidad 003).

Cada prueba cita su FR (y su escenario HUx-n cuando lo tiene) en el nombre o
en el docstring (principio IX).

    python -m unittest -v tests.test_resolubilidad
"""

import random
import unittest

from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
from tests.ayudas_cripta import (contenido, datos_generales, mapa_de,
                                 respuesta_llaves, sala, salida, ubicacion,
                                 verificar_cripta)


# Abreviaturas de los escenarios: `a`, `b`, `c`, `salida`... (spec, HU1).
A, B, C, D, SALIDA = ("itm_llave_a", "itm_llave_b", "itm_llave_c",
                      "itm_llave_d", "itm_llave_salida")


def generales(esqueleto, sala_salida, llave_salida=SALIDA, sala_inicial=1):
    return datos_generales(esqueleto, sala_inicial=sala_inicial,
                           sala_salida=sala_salida, llave_salida=llave_salida)


def rondas_de(resultado):
    """Las rondas como listas de ids, para comparar."""
    rondas = []

    for i in range(len(resultado.rondas)):
        ronda = resultado.rondas.obtener(i)
        rondas.append([ronda.obtener(j) for j in range(len(ronda))])

    return rondas


def lista(vector):
    return [vector.obtener(i) for i in range(len(vector))]


def texto(resultado):
    from crypta.Vista.FormatoVerificacion import texto_resultado
    return texto_resultado(resultado)


def puerta(destino, llave=None):
    """Una salida cerrada (con llave o sin ella)."""
    return salida(destino, cerrada=True, llave=llave)


# HU1-1: sala 1 inicial, sala 4 de salida; `c` en la 1, `a` en la 2; 1–2
# abierta, 2–3 pide `a`; `b` y `salida` en la 3; 3–4 pide `salida`.
ESQUELETO_HU1_1 = [
    sala(1, {"E": salida(2)}),
    sala(2, {"O": salida(1), "E": puerta(3, A)}),
    sala(3, {"O": puerta(2, A), "E": puerta(4, SALIDA)}),
    sala(4, {"O": puerta(3, SALIDA)}),
]
LLAVES_HU1_1 = [ubicacion(C, 1), ubicacion(A, 2), ubicacion(B, 3),
                ubicacion(SALIDA, 3)]
TEXTO_HU1_1 = (
    "Verificación de resolubilidad: la cripta es resoluble.\n"
    "Orden de llaves:\n"
    "  Ronda 1: itm_llave_a, itm_llave_c\n"
    "  Ronda 2: itm_llave_b, itm_llave_salida"
)


# Salas 1 a 5 en cadena; solo importa qué salas existen.
ESQUELETO_CINCO = [
    sala(1, {"E": salida(2)}),
    sala(2, {"O": salida(1), "E": salida(3)}),
    sala(3, {"O": salida(2), "E": salida(4)}),
    sala(4, {"O": salida(3), "E": salida(5)}),
    sala(5, {"O": salida(4)}),
]


class TestUbicacionLlaves(unittest.TestCase):
    """FR-319: lectura y validación de GET /criptas/<id>/llaves
    (contracts/datos-servicio.md); carga de HU3-7."""

    def setUp(self):
        self.mapa = mapa_de(ESQUELETO_CINCO)

    def leer(self, respuesta):
        return leer_ubicaciones(respuesta, self.mapa)

    def rechaza(self, respuesta, *fragmentos):
        with self.assertRaises(DatosInvalidos) as contexto:
            self.leer(respuesta)

        mensaje = str(contexto.exception)
        self.assertIn("la ubicación de llaves tiene un dato inválido", mensaje)

        for fragmento in fragmentos:
            self.assertIn(fragmento, mensaje)

        return mensaje

    def test_respuesta_valida_FR_319(self):
        ubicaciones = self.leer(respuesta_llaves(
            ubicacion("itm_llave_a", 2),
            ubicacion("itm_llave_b", 5, enemigo="e-501"),
        ))

        self.assertEqual(len(ubicaciones), 2)

        primera = ubicaciones.obtener(0)
        self.assertEqual(primera.id_llave, "itm_llave_a")
        self.assertEqual(primera.id_sala, 2)
        self.assertEqual(primera.indice_sala, self.mapa.obtener_sala(2).indice)
        self.assertIsNone(primera.enemigo)
        self.assertIsNone(primera.numero_llave)

        segunda = ubicaciones.obtener(1)
        self.assertEqual(segunda.id_llave, "itm_llave_b")
        self.assertEqual(segunda.id_sala, 5)
        self.assertEqual(segunda.indice_sala, self.mapa.obtener_sala(5).indice)
        self.assertEqual(segunda.enemigo, "e-501")

    def test_repetidas_lista_vacia_y_campos_extra_son_validos_FR_319(self):
        repetidas = self.leer(respuesta_llaves(
            ubicacion("itm_llave_a", 2), ubicacion("itm_llave_a", 2),
            ubicacion("itm_llave_a", 4)))
        self.assertEqual(len(repetidas), 3)

        self.assertEqual(len(self.leer({"llaves": []})), 0)

        extra = self.leer({"llaves": [{"id": "itm_llave_a", "sala": 1,
                                       "enemigo": None, "otro": 7}],
                           "version": "v9"})
        self.assertEqual(len(extra), 1)
        self.assertIsNone(extra.obtener(0).enemigo)

    def test_raiz_invalida_FR_319(self):
        self.rechaza({}, "llaves")
        self.rechaza({"llaves": {"id": "itm_llave_a", "sala": 1}}, "llaves")
        self.rechaza([], "llaves")
        self.rechaza(None, "llaves")

    def test_entrada_que_no_es_objeto_FR_319(self):
        self.rechaza({"llaves": [ubicacion("itm_llave_a", 1), "itm_llave_b"]},
                     "entrada 2")

    def test_id_invalido_FR_319(self):
        self.rechaza({"llaves": [{"sala": 1}]}, "entrada 1", "id")
        self.rechaza({"llaves": [{"id": "", "sala": 1}]}, "entrada 1", "id")
        self.rechaza({"llaves": [{"id": 7, "sala": 1}]}, "entrada 1", "id")
        self.rechaza({"llaves": [ubicacion("itm_llave_a", 1),
                                 {"id": None, "sala": 1}]}, "entrada 2", "id")

    def test_sala_invalida_FR_319(self):
        """Solo vale un entero JSON: se rechazan bool, float y texto, como
        el costo de la 001."""
        for valor in (True, 2.5, 2.0, "4", None):
            with self.subTest(sala=valor):
                self.rechaza({"llaves": [{"id": "itm_llave_a", "sala": valor}]},
                             "entrada 1", "itm_llave_a", "sala")

        self.rechaza({"llaves": [{"id": "itm_llave_a"}]},
                     "entrada 1", "itm_llave_a", "sala")

    def test_sala_inexistente_FR_319_HU3_7(self):
        """HU3-7: una llave en una sala que no existe en el esqueleto."""
        mensaje = self.rechaza(respuesta_llaves(
            ubicacion("itm_llave_a", 1), ubicacion("itm_llave_b", 99)),
            "entrada 2", "itm_llave_b", "99")
        self.assertIn("no existe", mensaje)

    def test_enemigo_invalido_FR_319(self):
        for valor in (5, True, ["e-1"]):
            with self.subTest(enemigo=valor):
                self.rechaza({"llaves": [{"id": "itm_llave_a", "sala": 1,
                                          "enemigo": valor}]},
                             "entrada 1", "itm_llave_a", "enemigo")


class TestResolubleYOrden(unittest.TestCase):
    """HU1-1 a HU1-5 (FR-301, FR-303, FR-304, FR-305, FR-306, FR-308)."""

    def test_HU1_1_rondas_y_texto_FR_305_306_308(self):
        """HU1-1: resoluble; primero, por id, las que se obtienen sin llaves
        (`a`, `c`); luego las que se vuelven obtenibles con ellas (`b`,
        `salida`). Se muestra por rondas, solo con ids."""
        resultado = verificar_cripta(ESQUELETO_HU1_1,
                                     generales(ESQUELETO_HU1_1, 4),
                                     respuesta_llaves(*LLAVES_HU1_1))

        self.assertTrue(resultado.resoluble)
        self.assertIsNone(resultado.reporte)
        self.assertEqual(rondas_de(resultado), [[A, C], [B, SALIDA]])
        self.assertEqual(texto(resultado), TEXTO_HU1_1)

    def test_HU1_2_mismo_orden_en_cualquier_orden_de_entrada_FR_308_320(self):
        """HU1-2 (Apéndice B): con varios órdenes válidos, dos ejecuciones
        dan el mismo orden, y también con la ubicación de las llaves y las
        salas del esqueleto en otro orden."""
        base = texto(verificar_cripta(ESQUELETO_HU1_1,
                                      generales(ESQUELETO_HU1_1, 4),
                                      respuesta_llaves(*LLAVES_HU1_1)))
        otra = texto(verificar_cripta(ESQUELETO_HU1_1,
                                      generales(ESQUELETO_HU1_1, 4),
                                      respuesta_llaves(*LLAVES_HU1_1)))
        self.assertEqual(otra, base)

        azar = random.Random(2)

        for _ in range(10):
            llaves = list(LLAVES_HU1_1)
            salas = list(ESQUELETO_HU1_1)
            azar.shuffle(llaves)
            azar.shuffle(salas)
            self.assertEqual(
                texto(verificar_cripta(salas, generales(salas, 4),
                                       respuesta_llaves(*llaves))),
                base)

    def test_HU1_3_llave_de_enemigo_en_su_sala_inicial_FR_304(self):
        """HU1-3 (Apéndice B): la llave que suelta un enemigo errante se
        considera obtenible en la sala donde ese enemigo inicia (la de la
        ubicación). FR-321 (no pedir contenido) se prueba en T031."""
        esqueleto = list(ESQUELETO_CINCO) + [sala(6, {"O": puerta(5, A)})]
        esqueleto[4] = sala(5, {"O": salida(4), "E": puerta(6, A)})
        resultado = verificar_cripta(
            esqueleto, generales(esqueleto, 6, llave_salida=A),
            respuesta_llaves(ubicacion(A, 5, enemigo="e-501")))

        self.assertTrue(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[A]])

    def test_HU1_4_cerrada_sin_llave_se_cruza_FR_303(self):
        """HU1-4: una salida cerrada sin llave entre la región y la sala de
        `salida` se cruza: la llave es obtenible."""
        esqueleto = [
            sala(1, {"E": puerta(2)}),
            sala(2, {"O": puerta(1), "E": puerta(3, SALIDA)}),
            sala(3, {"O": puerta(2, SALIDA)}),
        ]
        resultado = verificar_cripta(esqueleto, generales(esqueleto, 3),
                                     respuesta_llaves(ubicacion(SALIDA, 2)))

        self.assertTrue(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[SALIDA]])

    def test_HU1_5_trampas_cierres_y_costos_no_cambian_nada_FR_303(self):
        """HU1-5: con trampas, cierres automáticos y costos distintos, el
        resultado es el mismo que sin ellos."""
        con_todo = [
            sala(1, {"E": salida(2, costo=400)}),
            sala(2, {"O": salida(1, costo=400),
                     "E": salida(3, costo=7, cerrada=True, llave=A,
                                 cierre_automatico=500)}),
            sala(3, {"O": salida(2, costo=7, cerrada=True, llave=A,
                                 cierre_automatico=500),
                     "E": salida(4, costo=900, cerrada=True, llave=SALIDA,
                                 cierre_automatico=100)}),
            sala(4, {"O": salida(3, costo=900, cerrada=True, llave=SALIDA)}),
        ]
        contenidos = [contenido(2, trampas=[("t-1", "trp_pinchos")]),
                      contenido(3, trampas=[("t-2", "trp_pinchos")])]
        mapa = mapa_de(con_todo, contenidos)
        from crypta.Modelo.Verificador import verificar
        resultado = verificar(mapa, generales(con_todo, 4),
                              leer_ubicaciones(respuesta_llaves(*LLAVES_HU1_1),
                                               mapa))

        self.assertEqual(texto(resultado), TEXTO_HU1_1)


class TestResolubleCasosBorde(unittest.TestCase):
    """HU1-6 a HU1-9 y casos borde (FR-303 a FR-306, FR-308)."""

    def test_HU1_6_salida_sin_vuelta_solo_en_su_sentido_FR_303(self):
        """HU1-6: la única conexión entre 1 y 2 es una salida sin vuelta de
        2 a 1; `salida` solo está en la 2: no es obtenible."""
        esqueleto = [
            sala(1, {}),
            sala(2, {"O": salida(1), "E": puerta(3, SALIDA)}),
            sala(3, {"O": puerta(2, SALIDA)}),
        ]
        resultado = verificar_cripta(esqueleto, generales(esqueleto, 3),
                                     respuesta_llaves(ubicacion(SALIDA, 2)))

        self.assertFalse(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [])
        self.assertEqual(lista(resultado.reporte.no_obtenibles), [SALIDA])

    def test_HU1_7_basta_una_ubicacion_alcanzable_FR_304(self):
        """HU1-7: `a` está en una sala alcanzable y en otra que no."""
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1), "E": puerta(3, D)}),
            sala(3, {"O": puerta(2, D)}),
            sala(4, {"N": puerta(2, A)}),
        ]
        esqueleto[1]["salidas"]["S"] = puerta(4, A)
        resultado = verificar_cripta(
            esqueleto, generales(esqueleto, 4, llave_salida=A),
            respuesta_llaves(ubicacion(A, 3), ubicacion(A, 1)))

        self.assertTrue(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[A]])

    def test_HU1_8_llave_que_ninguna_puerta_pide_va_en_el_orden_FR_306(self):
        """HU1-8: una llave alcanzable que ninguna puerta pide aparece en el
        orden."""
        z = "itm_llave_z"
        resultado = verificar_cripta(
            ESQUELETO_HU1_1, generales(ESQUELETO_HU1_1, 4),
            respuesta_llaves(*(LLAVES_HU1_1 + [ubicacion(z, 3)])))

        self.assertTrue(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[A, C], [B, SALIDA, z]])

    def test_HU1_9_salida_alcanzable_solo_por_salida_abierta_FR_305(self):
        """HU1-9: `sala_salida` se alcanza solo por una salida abierta; aunque
        `salida` sea obtenible, no es resoluble."""
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1)}),
        ]
        resultado = verificar_cripta(esqueleto, generales(esqueleto, 2),
                                     respuesta_llaves(ubicacion(SALIDA, 1)))

        self.assertFalse(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[SALIDA]])
        self.assertEqual(lista(resultado.reporte.no_obtenibles), [])

    def test_sala_inicial_es_sala_salida_FR_305(self):
        """Caso borde: si `sala_inicial` es `sala_salida`, igual hay que
        llegar a ella por una puerta que pida `llave_salida`."""
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1), "E": salida(3)}),
            sala(3, {"O": salida(2), "N": puerta(1, SALIDA)}),
        ]
        llaves = respuesta_llaves(ubicacion(SALIDA, 3))

        resultado = verificar_cripta(esqueleto, generales(esqueleto, 1), llaves)
        self.assertTrue(resultado.resoluble)

        sin_puerta = [esqueleto[0], esqueleto[1],
                      sala(3, {"O": salida(2)})]
        resultado = verificar_cripta(sin_puerta, generales(sin_puerta, 1),
                                     llaves)
        self.assertFalse(resultado.resoluble)

    def test_puerta_hacia_salida_con_otra_llave_no_cuenta_FR_305(self):
        """Caso borde: la única puerta hacia `sala_salida` pide otra llave,
        obtenible: no es resoluble."""
        esqueleto = [
            sala(1, {"E": salida(2)}),
            sala(2, {"O": salida(1), "E": puerta(3, A)}),
            sala(3, {"O": puerta(2, A)}),
        ]
        resultado = verificar_cripta(
            esqueleto, generales(esqueleto, 3),
            respuesta_llaves(ubicacion(A, 1), ubicacion(SALIDA, 1)))

        self.assertFalse(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[A, SALIDA]])

    def test_llave_no_abre_puertas_en_su_misma_ronda_FR_308(self):
        """Una llave obtenida en la ronda r no abre puertas dentro de esa
        ronda: `a` está junto a la puerta que abre, pero `b` (detrás) va en
        la ronda siguiente, no con `a` y `c`."""
        esqueleto = [
            sala(1, {"E": puerta(2, A), "S": salida(5)}),
            sala(2, {"O": puerta(1, A), "E": puerta(6, B)}),
            sala(5, {"N": salida(1)}),
            sala(6, {"O": puerta(2, B)}),
        ]
        resultado = verificar_cripta(
            esqueleto, generales(esqueleto, 6, llave_salida=B),
            respuesta_llaves(ubicacion(A, 1), ubicacion(B, 2),
                             ubicacion(C, 5)))

        self.assertTrue(resultado.resoluble)
        self.assertEqual(rondas_de(resultado), [[A, C], [B]])


class Contador:
    """Cuenta los eventos que avisa el verificador (parámetro `observar`):
    ("region", sala), ("capa", sala) y ("salida", sala, dirección)."""

    def __init__(self):
        self.eventos = {}

    def __call__(self, tipo, *datos):
        clave = (tipo,) + datos
        self.eventos[clave] = self.eventos.get(clave, 0) + 1

    def maximo(self, tipo):
        return max((n for clave, n in self.eventos.items()
                    if clave[0] == tipo), default=0)

    def salas_marcadas(self):
        """Veces que se marcó cada sala, en la región o en una capa."""
        veces = {}

        for clave, n in self.eventos.items():
            if clave[0] in ("region", "capa"):
                veces[clave[1]] = veces.get(clave[1], 0) + n

        return veces


def cadena(n, resoluble=True):
    """n zonas de dos salas en fila; la zona i+1 detrás de una puerta que
    pide la llave i, ubicada en la zona i. Si no es resoluble, la última
    llave queda detrás de su propia puerta y hay una puerta más allá."""
    esqueleto = []
    llaves = []

    for i in range(n):
        x, y = 2 * i + 1, 2 * i + 2
        llave = f"itm_llave_{i:03d}"
        salidas_x = {"E": salida(y)}

        if i > 0:
            salidas_x["O"] = puerta(x - 1, f"itm_llave_{i - 1:03d}")

        salidas_y = {"O": salida(x), "E": puerta(y + 1, llave)}
        esqueleto.append(sala(x, salidas_x))
        esqueleto.append(sala(y, salidas_y))
        llaves.append(ubicacion(llave, y))

    ultima = 2 * n + 1
    esqueleto.append(sala(ultima, {"O": puerta(2 * n, f"itm_llave_{n - 1:03d}"),
                                   "E": puerta(ultima + 1, SALIDA)}))
    esqueleto.append(sala(ultima + 1, {"O": puerta(ultima, SALIDA)}))

    if resoluble:
        llaves.append(ubicacion(SALIDA, ultima))
    else:
        # `salida` detrás de su puerta, y una zona más detrás de otra que
        # pide `a`, que tampoco se obtiene: varias capas.
        llaves.append(ubicacion(SALIDA, ultima + 1))
        esqueleto[-1]["salidas"]["E"] = puerta(ultima + 2, A)
        esqueleto.append(sala(ultima + 2, {"O": puerta(ultima + 1, A),
                                           "E": salida(ultima + 3)}))
        esqueleto.append(sala(ultima + 3, {"O": salida(ultima + 2)}))
        llaves.append(ubicacion(A, ultima + 3))

    return esqueleto, generales(esqueleto, ultima + 1), respuesta_llaves(*llaves)


class TestVisitasUnaVez(unittest.TestCase):
    """FR-313, FR-335: un solo recorrido, sin repetirlo por llave."""

    def contar(self, esqueleto, datos, llaves):
        from crypta.Modelo.Verificador import verificar
        mapa = mapa_de(esqueleto)
        contador = Contador()
        resultado = verificar(mapa, datos, leer_ubicaciones(llaves, mapa),
                              observar=contador)
        return resultado, contador

    def test_resoluble_cada_sala_una_vez_y_cada_salida_dos_FR_313(self):
        """Cripta resoluble de 20 llaves encadenadas (21 rondas): cada sala
        se desencola a lo sumo una vez y cada salida se examina a lo sumo
        dos veces (al procesar su origen y al liberarse)."""
        resultado, contador = self.contar(*cadena(20))

        self.assertTrue(resultado.resoluble)
        self.assertEqual(len(resultado.rondas), 21)
        self.assertEqual(contador.maximo("region"), 1)
        self.assertLessEqual(contador.maximo("salida"), 2)

    @unittest.expectedFailure       # se activa con las capas (T024)
    def test_no_resoluble_cada_sala_una_vez_y_cada_salida_tres_FR_313(self):
        """Cripta no resoluble con varias capas más allá de la frontera:
        cada sala se marca a lo sumo una vez (en la región o en una capa) y
        cada salida se examina a lo sumo tres veces (origen, liberación y
        capa). Hay al menos una sala marcada en una capa."""
        resultado, contador = self.contar(*cadena(20, resoluble=False))

        self.assertFalse(resultado.resoluble)
        self.assertGreater(contador.maximo("capa"), 0)
        self.assertLessEqual(max(contador.salas_marcadas().values()), 1)
        self.assertLessEqual(contador.maximo("salida"), 3)


if __name__ == "__main__":
    unittest.main()
