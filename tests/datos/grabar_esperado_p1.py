"""Estado esperado de la partida de la primera parte (FR-008, tarea T002).

Repite `tests/datos/p1_partida.log` sin red, sobre una copia temporal de
`p1_cripta-01.json` y `p1_catalogo.json` (nunca sobre `cache/`), y anota el
estado después de cada comando y al final.

Se ejecutó una sola vez con el código de la primera parte, antes de cualquier
cambio de la capacidad 001, para escribir `p1_esperado.json`:

    python -m tests.datos.grabar_esperado_p1

`TestCompatibilidadP1` (tests/test_terreno.py) usa las mismas funciones
`repetir_partida_p1` y `estado_de` para comparar contra ese archivo, así que
lo que se graba y lo que se compara siempre se calculan igual.

Solo se usa la interfaz pública de la partida (reloj, jugador, resultado,
bitácora, azar y agenda), para que un cambio interno que no altere la
partida no rompa la comparación.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Adaptadores.FuenteOffline import FuenteOffline
from crypta.Controlador.PreparadorReplay import PreparadorReplay
from crypta.Controlador.Reproductor import Reproductor


CARPETA_DATOS = os.path.dirname(os.path.abspath(__file__))
RUTA_LOG = os.path.join(CARPETA_DATOS, "p1_partida.log")
RUTA_ESPERADO = os.path.join(CARPETA_DATOS, "p1_esperado.json")

# Copia fija -> nombre que espera el AlmacenDisco en su carpeta.
COPIAS_FIJAS = (
    ("p1_cripta-01.json", "cripta-01.json"),
    ("p1_catalogo.json", "catalogo.json"),
)


def huella_del_azar(azar):
    """Resumen estable del estado de un random.Random: si dos partidas
    hicieron exactamente las mismas llamadas al generador, coinciden."""
    estado = json.dumps(azar.getstate())
    return hashlib.sha256(estado.encode("utf-8")).hexdigest()


def estado_de(partida):
    """Lo que se compara de una partida en un instante dado."""
    jugador = partida.jugador

    return {
        "reloj": partida.reloj,
        "sala": jugador.sala_actual,
        "vida": jugador.vida,
        "acciones_jugador": partida.acciones_jugador,
        "enemigos_derrotados": partida.enemigos_derrotados,
        "terminada": partida.terminada,
        "resultado": partida.resultado,
        "eventos_programados": partida.agenda.siguiente_secuencia,
        "eventos_pendientes": len(partida.agenda),
        "azar": huella_del_azar(partida.azar),
        "mensajes": list(partida.bitacora),
    }


def preparar_carpeta(destino):
    """Copia los datos fijos de la primera parte a `destino` con los nombres
    que usa el AlmacenDisco."""
    for origen, nombre in COPIAS_FIJAS:
        shutil.copyfile(os.path.join(CARPETA_DATOS, origen),
                        os.path.join(destino, nombre))


def repetir_partida_p1(carpeta=None):
    """Repite el registro de la primera parte sin red y devuelve
    {"comandos": [estado después de cada comando], "final": estado final}.

    Si no se da `carpeta`, usa una temporal que se borra al terminar."""
    if carpeta is None:
        with tempfile.TemporaryDirectory() as temporal:
            return repetir_partida_p1(temporal)

    preparar_carpeta(carpeta)

    almacen = AlmacenDisco(carpeta)
    preparador = PreparadorReplay(FuenteOffline(almacen), almacen)
    pasos = []

    def al_ejecutar(numero, comando, partida):
        paso = estado_de(partida)
        paso["numero"] = numero
        paso["comando"] = comando
        pasos.append(paso)

    try:
        resultado = Reproductor(preparador).reproducir(RUTA_LOG, al_ejecutar)
    finally:
        preparador.cerrar()

    return {"comandos": pasos, "final": estado_de(resultado.partida)}


def main():
    esperado = repetir_partida_p1()

    with open(RUTA_ESPERADO, "w", encoding="utf-8", newline="\n") as archivo:
        json.dump(esperado, archivo, ensure_ascii=False, indent=1)
        archivo.write("\n")

    final = esperado["final"]
    print(f"Escrito {RUTA_ESPERADO}: {len(esperado['comandos'])} comandos, "
          f"reloj {final['reloj']}, resultado {final['resultado']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
