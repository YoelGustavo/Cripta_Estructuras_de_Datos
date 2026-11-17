"""Pruebas de la estructura de la niebla de guerra (capacidad 002, fase 1).

- T002, `TestPuertaRecordada`: el estado recordado de una puerta vive en su
  `EstadoPuerta` compartido (FR-204 a FR-206; research D2).
- T003, `TestMapaConocido`: el conocimiento del jugador (FR-201 a FR-203,
  FR-224, FR-235, FR-236; data-model «MapaConocido»; research D1, D3, D4).

Cripta de prueba (`esqueleto`):

    sala 1: E → 2, S → 4 (cerrada), O → 99 (no existe)
    sala 2: O → 1, E → 3
    sala 3: O → 2
    sala 4: N → 1 (cerrada)
    sala 5: N → 1 (sin vuelta: la sala 1 no tiene salida hacia la 5)
"""

import copy
import unittest

from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.MapaConocido import (
    AVISTADA,
    DESCONOCIDA,
    EXPLORADA,
    MapaConocido,
)
from crypta.Modelo.Puerta import ABIERTA, CERRADA, EstadoPuerta, Puerta
from tests.ayudas_cripta import mapa_de, sala, salida


def esqueleto():
    return [
        sala(1, {"E": salida(2), "S": salida(4, cerrada=True),
                 "O": salida(99)}),
        sala(2, {"O": salida(1), "E": salida(3)}),
        sala(3, {"O": salida(2)}),
        sala(4, {"N": salida(1, cerrada=True)}),
        sala(5, {"N": salida(1)}),
    ]


class ObservadorFalso:
    """Anota cada aviso como (nombre, argumento)."""

    def __init__(self):
        self.avisos = []

    def sala_explorada(self, sala_mapa):
        self.avisos.append(("sala_explorada", sala_mapa))

    def puerta_recordada(self, estado):
        self.avisos.append(("puerta_recordada", estado))


# ---------------------------------------------------------------------------
# T002
# ---------------------------------------------------------------------------

class TestPuertaRecordada(unittest.TestCase):
    """FR-204 a FR-206; research D2."""

    def test_fr204_puerta_nueva_nunca_observada(self):
        self.assertIsNone(Puerta(2).estado.recordada)
        self.assertIsNone(EstadoPuerta().recordada)

    def test_fr205_los_dos_lados_comparten_recordada(self):
        mapa = mapa_de(esqueleto())
        ida = mapa.obtener_sala(1).obtener_puerta("E")
        vuelta = mapa.obtener_sala(2).obtener_puerta("O")

        ida.estado.recordada = ABIERTA
        self.assertEqual(vuelta.estado.recordada, ABIERTA)

        vuelta.estado.recordada = CERRADA
        self.assertEqual(ida.estado.recordada, CERRADA)

    def test_fr204_puerta_acepta_recordada_leida(self):
        self.assertEqual(Puerta(2, recordada=ABIERTA).estado.recordada,
                         ABIERTA)
        self.assertEqual(Puerta(2, recordada=CERRADA).estado.recordada,
                         CERRADA)

    def test_fr205_compartir_con_un_lado_none_toma_el_otro(self):
        sin_dato = Puerta(2)
        con_dato = Puerta(1, recordada=CERRADA)
        sin_dato.compartir_estado_con(con_dato)
        self.assertEqual(sin_dato.estado.recordada, CERRADA)
        self.assertIs(sin_dato.estado, con_dato.estado)

        con_dato = Puerta(2, recordada=ABIERTA)
        sin_dato = Puerta(1)
        con_dato.compartir_estado_con(sin_dato)
        self.assertEqual(sin_dato.estado.recordada, ABIERTA)

    def test_fr206_compartir_con_recordadas_distintas_falla(self):
        abierta = Puerta(2, recordada=ABIERTA)
        cerrada = Puerta(1, recordada=CERRADA)

        with self.assertRaises(DatosInvalidos):
            abierta.compartir_estado_con(cerrada)

    def test_fr206_compartir_con_recordadas_iguales_pasa(self):
        a = Puerta(2, recordada=CERRADA)
        b = Puerta(1, recordada=CERRADA)
        a.compartir_estado_con(b)
        self.assertEqual(b.estado.recordada, CERRADA)

    def test_d2_deepcopy_copia_recordada_sin_observador(self):
        estado = EstadoPuerta()
        estado.recordada = CERRADA
        estado.observador = ObservadorFalso()

        copia = copy.deepcopy(estado)

        self.assertEqual(copia.recordada, CERRADA)
        self.assertIsNone(copia.observador)


# ---------------------------------------------------------------------------
# T003
# ---------------------------------------------------------------------------

class TestMapaConocido(unittest.TestCase):
    """FR-201 a FR-203, FR-224, FR-235, FR-236; research D1, D3, D4."""

    def setUp(self):
        self.mapa = mapa_de(esqueleto())
        self.registro = RegistroAccion()
        self.cambios = []
        self.conocido = MapaConocido(self.mapa, self._anotar)

    def _anotar(self, cambio):
        # Busca `self.registro` en cada llamada, como `partida._anotar`
        # busca el historial vigente (research D3).
        self.cambios.append(cambio)
        self.registro.registrar_cambio(cambio)

    def s(self, id_sala):
        return self.mapa.obtener_sala(id_sala)

    def p(self, id_sala, direccion):
        return self.s(id_sala).obtener_puerta(direccion)

    def todas_las_puertas(self):
        for id_sala in range(1, 6):
            puertas = self.s(id_sala).puertas()

            for i in range(len(puertas)):
                yield puertas.obtener(i)

    def foto(self):
        """Estados, `recordada` y contadores, para comparar."""
        return (
            [self.conocido.estado(self.s(i)) for i in range(1, 6)],
            [puerta.estado.recordada for puerta in self.todas_las_puertas()],
            self.conocido.exploradas,
            self.conocido.avistadas,
        )

    # -- consultas -----------------------------------------------------------

    def test_fr201_todo_empieza_desconocido(self):
        for i in range(1, 6):
            self.assertEqual(self.conocido.estado(self.s(i)), DESCONOCIDA)
            self.assertFalse(self.conocido.esta_explorada(self.s(i)))

        for puerta in self.todas_las_puertas():
            self.assertIsNone(self.conocido.recordada(puerta))

        self.assertEqual(self.conocido.exploradas, 0)
        self.assertEqual(self.conocido.avistadas, 0)

    def test_fr235_recordada_lee_el_estado_de_la_puerta(self):
        self.p(1, "E").estado.recordada = CERRADA
        self.assertEqual(self.conocido.recordada(self.p(1, "E")), CERRADA)
        self.assertEqual(self.conocido.recordada(self.p(2, "O")), CERRADA)

    # -- explorar ------------------------------------------------------------

    def test_fr201_fr202_explorar_marca_observa_y_avista(self):
        self.conocido.explorar(self.s(1))

        self.assertEqual(self.conocido.estado(self.s(1)), EXPLORADA)
        self.assertTrue(self.conocido.esta_explorada(self.s(1)))
        self.assertEqual(self.conocido.recordada(self.p(1, "E")), ABIERTA)
        self.assertEqual(self.conocido.recordada(self.p(1, "S")), CERRADA)
        self.assertEqual(self.conocido.recordada(self.p(1, "O")), ABIERTA)
        self.assertEqual(self.conocido.estado(self.s(2)), AVISTADA)
        self.assertEqual(self.conocido.estado(self.s(4)), AVISTADA)
        self.assertEqual(self.conocido.estado(self.s(3)), DESCONOCIDA)
        self.assertEqual(self.conocido.exploradas, 1)
        self.assertEqual(self.conocido.avistadas, 2)

    def test_fr202_salida_sin_vuelta_no_avista_su_origen(self):
        self.conocido.explorar(self.s(1))

        self.assertEqual(self.conocido.estado(self.s(5)), DESCONOCIDA)
        self.assertIsNone(self.conocido.recordada(self.p(5, "N")))

    def test_d4_salida_hacia_sala_inexistente_no_avista_nada(self):
        self.conocido.explorar(self.s(1))
        conocidas = [s.id for s, _ in self.conocido.salas_conocidas()]
        self.assertEqual(conocidas, [1, 2, 4])

    def test_fr201_destino_ya_explorado_no_cambia(self):
        self.conocido.explorar(self.s(2))
        self.conocido.explorar(self.s(1))

        self.assertEqual(self.conocido.estado(self.s(2)), EXPLORADA)
        self.assertEqual(self.conocido.estado(self.s(1)), EXPLORADA)
        self.assertEqual(self.conocido.exploradas, 2)
        self.assertEqual(self.conocido.avistadas, 2)    # 3 y 4

    def test_fr201_avistar_no_cambia_una_explorada(self):
        self.conocido.explorar(self.s(1))
        self.conocido.avistar(self.s(1))
        self.assertEqual(self.conocido.estado(self.s(1)), EXPLORADA)

    # -- observar ------------------------------------------------------------

    def test_fr204_observar_solo_cambia_lo_que_difiere(self):
        self.conocido.explorar(self.s(1))
        self.cambios.clear()

        self.p(1, "S").abrir()
        self.conocido.observar(self.s(1))

        self.assertEqual(len(self.cambios), 1)
        self.assertEqual(self.conocido.recordada(self.p(1, "S")), ABIERTA)
        self.assertEqual(self.conocido.recordada(self.p(4, "N")), ABIERTA)

    def test_fr204_sin_observar_recordada_no_sigue_al_real(self):
        self.conocido.explorar(self.s(1))
        self.p(1, "E").cerrar()
        self.assertEqual(self.conocido.recordada(self.p(1, "E")), ABIERTA)

    # -- cambios y deshacer --------------------------------------------------

    def test_d3_explorar_dos_veces_no_anota_la_segunda(self):
        self.conocido.explorar(self.s(1))
        self.assertGreater(len(self.cambios), 0)
        self.cambios.clear()

        self.conocido.explorar(self.s(1))

        self.assertEqual(self.cambios, [])

    def test_d3_cada_cambio_es_de_operacion_sobre_el_mapa_conocido(self):
        self.conocido.explorar(self.s(1))

        # 1 explorada + 3 salidas observadas + 2 avistadas.
        self.assertEqual(len(self.cambios), 6)

        for cambio in self.cambios:
            self.assertEqual(cambio.tipo, "conocimiento")
            self.assertIs(cambio.objetivo, self.conocido)
            self.assertIn(cambio.operacion,
                          ("restaurar_sala", "restaurar_puerta"))

    def test_fr224_fr236_deshacer_devuelve_todo_como_estaba(self):
        inicial = self.foto()

        self.conocido.explorar(self.s(1))
        tras_explorar = self.foto()
        primero = self.registro

        self.registro = RegistroAccion()
        self.p(1, "S").abrir()
        self.conocido.explorar(self.s(4))
        self.conocido.explorar(self.s(2))
        self.conocido.observar(self.s(1))
        self.assertNotEqual(self.foto(), tras_explorar)

        self.registro.deshacer()
        self.p(1, "S").cerrar()
        self.assertEqual(self.foto(), tras_explorar)

        primero.deshacer()
        self.assertEqual(self.foto(), inicial)

    def test_d3_el_observador_recibe_avisos_al_cambiar_y_al_deshacer(self):
        observador = ObservadorFalso()
        self.conocido.observador = observador

        self.conocido.explorar(self.s(1))

        self.assertIn(("sala_explorada", self.s(1)), observador.avisos)
        self.assertIn(("puerta_recordada", self.p(1, "E").estado),
                      observador.avisos)
        self.assertIn(("puerta_recordada", self.p(1, "S").estado),
                      observador.avisos)

        observador.avisos.clear()
        self.registro.deshacer()

        self.assertIn(("sala_explorada", self.s(1)), observador.avisos)
        self.assertIn(("puerta_recordada", self.p(1, "E").estado),
                      observador.avisos)
        self.assertIn(("puerta_recordada", self.p(1, "S").estado),
                      observador.avisos)

    # -- recorrido -----------------------------------------------------------

    def test_fr210_salas_conocidas_en_orden_de_id(self):
        self.conocido.explorar(self.s(3))
        self.conocido.explorar(self.s(2))

        conocidas = [(s.id, estado)
                     for s, estado in self.conocido.salas_conocidas()]

        self.assertEqual(conocidas,
                         [(1, AVISTADA), (2, EXPLORADA), (3, EXPLORADA)])

    # -- validar -------------------------------------------------------------

    def test_fr201_fr204_validar_pasa_con_lo_explorado(self):
        self.conocido.explorar(self.s(1))
        self.conocido.explorar(self.s(2))
        self.conocido.validar(1)

    def test_fr201_validar_rechaza_sala_inicial_no_explorada(self):
        self.conocido.explorar(self.s(1))

        with self.assertRaises(ValueError):
            self.conocido.validar(2)

    def test_fr202_validar_rechaza_avistada_sin_salida_explorada(self):
        self.conocido.explorar(self.s(1))
        self.conocido.avistar(self.s(3))

        with self.assertRaises(ValueError):
            self.conocido.validar(1)

    def test_fr202_validar_rechaza_destino_desconocido(self):
        self.conocido.explorar(self.s(1))
        self.conocido.restaurar_sala((self.s(2).indice, DESCONOCIDA))

        with self.assertRaises(ValueError):
            self.conocido.validar(1)

    def test_fr203_validar_rechaza_salida_explorada_sin_observar(self):
        self.conocido.explorar(self.s(1))
        self.p(1, "E").estado.recordada = None

        with self.assertRaises(ValueError):
            self.conocido.validar(1)

    # -- restaurar -----------------------------------------------------------

    def lista_valida(self):
        """Explora 1 y 2 con otro MapaConocido sobre el mismo mapa (las
        puertas quedan observadas) y devuelve su lista de salas."""
        otro = MapaConocido(self.mapa, lambda cambio: None)
        otro.explorar(self.s(1))
        otro.explorar(self.s(2))
        return [(s.id, estado) for s, estado in otro.salas_conocidas()]

    def test_fr226_restaurar_acepta_una_lista_valida(self):
        lista = self.lista_valida()
        self.assertEqual(lista, [(1, EXPLORADA), (2, EXPLORADA),
                                 (3, AVISTADA), (4, AVISTADA)])

        self.conocido.restaurar(lista, 1)

        conocidas = [(s.id, estado)
                     for s, estado in self.conocido.salas_conocidas()]
        self.assertEqual(conocidas, lista)
        self.assertEqual(self.conocido.exploradas, 2)
        self.assertEqual(self.conocido.avistadas, 2)
        self.assertEqual(self.cambios, [])

    def test_fr226_restaurar_rechaza_listas_invalidas(self):
        self.lista_valida()
        malas = {
            "id inexistente": [(1, EXPLORADA), (2, AVISTADA), (4, AVISTADA),
                               (99, AVISTADA)],
            "id repetido": [(1, EXPLORADA), (1, EXPLORADA), (2, AVISTADA),
                            (4, AVISTADA)],
            "desordenada": [(2, AVISTADA), (1, EXPLORADA), (4, AVISTADA)],
            "estado 3": [(1, EXPLORADA), (2, 3), (4, AVISTADA)],
            "estado 0": [(1, EXPLORADA), (2, DESCONOCIDA), (4, AVISTADA)],
            "falta una avistada": [(1, EXPLORADA), (2, AVISTADA)],
            "inicial no explorada": [(1, AVISTADA), (2, EXPLORADA),
                                     (3, AVISTADA)],
            "avistada de más": [(1, EXPLORADA), (2, AVISTADA), (4, AVISTADA),
                                (5, AVISTADA)],
        }

        for motivo, lista in malas.items():
            with self.subTest(motivo):
                conocido = MapaConocido(self.mapa, self._anotar)

                with self.assertRaises(ValueError):
                    conocido.restaurar(lista, 1)

    def test_fr203_restaurar_rechaza_salida_explorada_sin_observar(self):
        lista = self.lista_valida()
        self.p(2, "E").estado.recordada = None

        with self.assertRaises(ValueError):
            self.conocido.restaurar(lista, 1)

    # -- copia ---------------------------------------------------------------

    def test_fr224_deepcopy_copia_estados_sin_observador(self):
        registro = RegistroAccion()
        conocido = MapaConocido(self.mapa, registro.registrar_cambio)
        conocido.explorar(self.s(1))
        conocido.observador = ObservadorFalso()

        copia_mapa, copia = copy.deepcopy((self.mapa, conocido))

        self.assertIsNone(copia.observador)
        self.assertEqual(copia.exploradas, 1)
        self.assertEqual(copia.avistadas, 2)

        for i in range(1, 6):
            self.assertEqual(copia.estado(copia_mapa.obtener_sala(i)),
                             conocido.estado(self.s(i)))

        # La copia es independiente del original.
        copia.explorar(copia_mapa.obtener_sala(2))
        self.assertEqual(copia.estado(copia_mapa.obtener_sala(2)), EXPLORADA)
        self.assertEqual(conocido.estado(self.s(2)), AVISTADA)
        self.assertEqual(conocido.estado(self.s(3)), DESCONOCIDA)


if __name__ == "__main__":
    unittest.main()
