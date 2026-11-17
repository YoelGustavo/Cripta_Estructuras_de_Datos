"""Pruebas del resumen de un estado y de su texto (capacidad 004, T006).

FR-406 y contracts/resumen.md: el mismo texto para `historia`,
`--replay … --hasta` y después de cargar, sin el reloj actual de la partida.
"""

import copy
import unittest

from crypta.Modelo.Enemigo import Enemigo
from crypta.Modelo.Resumen import armar_resumen, pedido_accion, pedido_instante
from crypta.Vista.FormatoResumen import formatear_resumen
from tests.ayudas_cripta import (
    catalogo, contenido, ficha_errante, ficha_rastreador, partida_sintetica,
    sala, salida,
)


DAGA = {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "ataque_bonus": 2}
COTA = {"id": "itm_cota", "clase": "armadura", "nombre": "Cota", "defensa_bonus": 1}
POCION = {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción", "cura": 5}


def partida_armada():
    """Sala 1 con dos enemigos activos y vivos (a-1 y a-2), uno activo y
    muerto (a-3, vida 0) y, agregado a mano, uno dormido (z-9). El jugador
    lleva cota y daga equipadas (en ese orden real: equipar pasa el objeto
    al frente), una poción a la vista, dos pergaminos, y
    está envenenado, con antorcha y con un efecto de velocidad, en el
    instante 0."""
    esqueleto = [sala(1, {"E": salida(2)}), sala(2, {"O": salida(1)})]
    contenidos = [contenido(1, enemigos=(("a-1", "ent_errante"),
                                         ("a-2", "ent_rastreador", 7),
                                         ("a-3", "ent_errante", 0)))]
    fichas = catalogo(ficha_errante(), ficha_rastreador())
    partida = partida_sintetica(esqueleto, contenidos, fichas)

    inventario = partida.jugador.inventario
    inventario.recoger(DAGA)
    inventario.recoger(COTA)
    inventario.recoger(POCION)
    inventario.equipar_actual()          # daga (equipar la pasa al frente)
    inventario.avanzar()
    inventario.equipar_actual()          # cota, ahora primera: cota, daga, poción
    inventario.avanzar()
    inventario.avanzar()                 # a la vista: la poción
    inventario.fijar_pergaminos(2)

    partida.sala_actual().agregar_enemigo(Enemigo("z-9", "ent_errante"))

    partida._envenenar(2)                # hasta 400
    partida._encender_antorcha(300)      # hasta 300
    partida._empezar_velocidad(30, 200)  # +30 hasta 200
    return partida


TEXTO_ESPERADO = (
    "HISTORIA instante 0\n"
    "Reloj: 0   Próxima acción: #1\n"
    "Sala: 1 Sala 1\n"
    "Vida: 30/30   Ataque: 8   Defensa: 3   Velocidad: 130\n"
    "Efectos: veneno hasta 400, antorcha hasta 300, velocidad +30 hasta 200\n"
    "Inventario (5/10):\n"
    "  1. Cota (itm_cota) [armadura equipada]\n"
    "  2. Daga (itm_daga) [arma equipada]\n"
    "  3. Poción (itm_pocion) <- actual\n"
    "  Pergaminos: 2\n"
    "Enemigos en la sala:\n"
    "  a-1 ent_errante: vida 12\n"
    "  a-2 ent_rastreador: vida 7\n"
    # Capacidad 002 (FR-228; ajuste de SC-207): la línea fija «no
    # disponible» pasa a ser el mapa conocido de ese estado
    # (contracts/vista.md «Resumen»).
    "Mapa conocido: 1 exploradas, 1 avistadas\n"
    "  1 Sala 1\n"
    "    E: sala 2, costo 100, abierta\n"
    "  Avistadas: 2\n"
)


class TestTextoDelResumen(unittest.TestCase):
    """FR-406: el texto exacto de contracts/resumen.md."""

    def test_fr406_texto_completo(self):
        """Orden fijo de efectos (veneno, antorcha, velocidad), inventario en
        orden real con equipados y el actual, pergaminos, solo los enemigos
        activos y vivos, y el mapa conocido (capacidad 002, FR-228)."""
        partida = partida_armada()
        texto = formatear_resumen(armar_resumen(partida, pedido_instante(0)))
        self.assertEqual(texto, TEXTO_ESPERADO)

    def test_fr406_sin_efectos_ni_enemigos_ni_objetos(self):
        esqueleto = [sala(1)]
        partida = partida_sintetica(esqueleto)
        texto = formatear_resumen(armar_resumen(partida, pedido_accion(1)))

        self.assertEqual(texto, (
            "HISTORIA acción #1\n"
            "Reloj: 0   Próxima acción: #1\n"
            "Sala: 1 Sala 1\n"
            "Vida: 30/30   Ataque: 6   Defensa: 2   Velocidad: 100\n"
            "Efectos: ninguno\n"
            "Inventario (0/10):\n"
            "  Pergaminos: 0\n"
            "Enemigos en la sala: ninguno\n"
            # Capacidad 002 (FR-228; ajuste de SC-207).
            "Mapa conocido: 1 exploradas, 0 avistadas\n"
            "  1 Sala 1\n"
            "  Avistadas: ninguna\n"
        ))

    def test_fr406_no_muestra_el_reloj_actual(self):
        """El resumen de un estado anterior lleva el reloj de ese estado,
        no el de la partida que siguió (FR-406, HU1-1)."""
        partida = partida_armada()
        anterior = copy.deepcopy(partida)

        partida.esperar()
        partida.esperar()
        self.assertGreater(partida.reloj, 0)

        texto = formatear_resumen(armar_resumen(anterior, pedido_instante(0)))
        self.assertIn("Reloj: 0   Próxima acción: #1\n", texto)
        self.assertNotIn(f"Reloj: {partida.reloj}", texto)

    def test_fr415_aviso_solo_si_se_pasa(self):
        partida = partida_armada()
        sin_aviso = formatear_resumen(armar_resumen(partida, pedido_instante(0)))
        con_aviso = formatear_resumen(armar_resumen(
            partida, pedido_instante(0),
            aviso="El log termina en el instante 0, antes de 9000."))

        self.assertNotIn("Aviso:", sin_aviso)
        self.assertEqual(
            con_aviso,
            TEXTO_ESPERADO + "Aviso: El log termina en el instante 0, antes de 9000.\n")

    def test_fr406_termina_con_salto_de_linea(self):
        partida = partida_armada()
        texto = formatear_resumen(armar_resumen(partida, pedido_accion(1)))
        self.assertTrue(texto.endswith("\n"))
        self.assertFalse(texto.endswith("\n\n"))

    def test_fr407_armar_el_resumen_no_cambia_la_partida(self):
        from crypta.bench.oraculo_linea import serializar_estado

        partida = partida_armada()
        antes = serializar_estado(partida)
        armar_resumen(partida, pedido_instante(0))
        self.assertEqual(serializar_estado(partida), antes)


if __name__ == "__main__":
    unittest.main()
