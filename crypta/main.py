import argparse
import random
import tempfile

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Adaptadores.FuenteHTTP import FuenteHTTP
from crypta.Adaptadores.FuenteOffline import FuenteOffline
from crypta.Adaptadores.RegistroPartida import (
    Encabezado,
    ErrorRegistro,
    RegistroPartida,
)

from crypta.Controlador.Controlador import Controlador
from crypta.Controlador.Fabrica import nueva_partida
from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.GestorCripta import GestorCripta
from crypta.Controlador.PreparadorReplay import PreparadorReplay
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.Modelo.TablaPuntajes import ErrorTablaPuntajes, TablaPuntajes
from crypta.Controlador.Reproductor import (
    ReproduccionFallida,
    ReproduccionIncompatible,
    Reproductor,
)

from crypta.Vista.VistaConsola import VistaConsola


# La tabla de puntajes (§2.12): un archivo de texto de solo anexado.
RUTA_PUNTAJES = "puntajes.txt"

# El registro de la partida (§4.11). Es el de la ÚLTIMA partida: la
# siguiente lo reemplaza (para conservarlo, hay que copiarlo).
RUTA_REGISTRO = "partida.log"


def crear_argumentos():
    parser = argparse.ArgumentParser(
        description="CRIPTA - Juego de exploración de mazmorras"
    )

    parser.add_argument(
        "--cripta",
        default="cripta-01",
        help="ID de la cripta (predeterminado: cripta-01)"
    )

    parser.add_argument(
        "--offline",
        action="store_true",
        help="Utilizar exclusivamente los datos almacenados en disco"
    )

    parser.add_argument(
        "--jugador",
        default="Aventurero",
        help="Nombre del jugador"
    )

    parser.add_argument(
        "--semilla",
        type=int,
        default=None,
        help="Semilla para la partida"
    )

    parser.add_argument(
        "--replay",
        metavar="ARCHIVO",
        default=None,
        help="Reproducir una partida registrada sin interacción"
    )

    parser.add_argument(
        "--bench",
        action="store_true",
        help="Ejecutar benchmarks sin iniciar el juego"
    )

    parser.add_argument(
        "--cache-size",
        type=int,
        default=25,
        help="Capacidad de la caché de fichas (predeterminado: 25)"
    )

    return parser.parse_args()



def crear_fuente(args, almacen):
    """El ÚNICO lugar donde se decide entre red y modo sin conexión (§6)."""
    if args.offline:
        return FuenteOffline(almacen)

    return FuenteHTTP()


def crear_partida(args):
    """Construye los componentes de una partida para JUGAR.
    (Para reproducir se usa PreparadorReplay, con el mismo nueva_partida.)"""

    almacen = AlmacenDisco()
    fuente = crear_fuente(args, almacen)

    gestor_cripta = GestorCripta(
        fuente,
        almacen
    )

    datos_cripta, mapa, desde_cache = gestor_cripta.cargar(
        args.cripta
    )

    # §5.1: desde aquí la fuente no deja pasar del presupuesto de la
    # cripta. (En modo sin conexión no hace nada: no hay red.)
    fuente.fijar_presupuesto(datos_cripta["presupuesto_solicitudes"])

    version_catalogo = fuente.obtener_version_catalogo()["version"]

    repositorio = RepositorioFichas(
        fuente=fuente,
        almacen=almacen,
        version_catalogo=version_catalogo,
        cache_size=args.cache_size
    )

    semilla = (
        args.semilla
        if args.semilla is not None
        else random.randint(0, 2**31 - 1)
    )

    # El MISMO código que usa el replay para armar la partida.
    partida = nueva_partida(
        datos_cripta,
        mapa,
        repositorio.obtener_ficha,
        semilla,
        args.jugador
    )

    gestor_contenido = GestorContenido(
        fuente,
        mapa,
        args.cripta,
        repositorio
    )

    encabezado = Encabezado(
        cripta_id=args.cripta,
        version_cripta=datos_cripta["version"],
        version_catalogo=version_catalogo,
        semilla=semilla,
        jugador=args.jugador
    )

    registro = RegistroPartida.crear(
        RUTA_REGISTRO,
        encabezado
    )

    # Un archivo de puntajes dañado no impide jugar: se avisa y esta
    # partida simplemente no se registra (no se sobrescribe el archivo).
    try:
        tabla = TablaPuntajes(RUTA_PUNTAJES)
    except ErrorTablaPuntajes as error:
        print(f"Aviso: {error}. Esta partida no se registrará en la tabla de puntajes.")
        tabla = None

    controlador = Controlador(
        partida=partida,
        gestor_contenido=gestor_contenido,
        vista=VistaConsola(),
        registro=registro,
        encabezado=encabezado,
        repositorio_fichas=repositorio,
        tabla_puntajes=tabla
    )

    return controlador, gestor_cripta, datos_cripta, fuente


def reproducir(args):
    """--replay: repite el log con el Reproductor de la Fase 6, SIN vista
    ni teclado (§6). Devuelve el código de salida del programa."""

    almacen = AlmacenDisco()
    preparador = PreparadorReplay(
        crear_fuente(args, almacen),
        almacen,
        args.cache_size
    )

    try:
        resultado = Reproductor(preparador).reproducir(args.replay)

    except ErrorRegistro as error:
        print(f"El registro no se puede leer: {error}")
        return 1

    except ReproduccionIncompatible as error:
        print(f"Reproducción incompatible: {error}")
        return 1

    except ReproduccionFallida as error:
        print(f"Reproducción fallida: {error}")
        return 1

    except (RuntimeError, ValueError, OSError) as error:
        print(f"Error durante la reproducción: {error}")
        return 1

    finally:
        preparador.cerrar()

    partida = resultado.partida
    jugador = partida.jugador

    print(f"Cripta: {resultado.encabezado.cripta_id}")
    print(f"Jugador: {resultado.encabezado.jugador}")
    print(f"Semilla: {resultado.encabezado.semilla}")
    print(f"Replay terminado: {resultado.comandos} comandos repetidos.")
    print(f"Reloj: {partida.reloj}")
    print(f"Sala actual: {jugador.sala_actual}")
    print(f"Vida: {jugador.vida}/{jugador.vida_max}")
    print(f"Acciones del jugador: {partida.acciones_jugador}")
    print(
        f"Resultado: {partida.resultado}"
        if partida.terminada
        else "Resultado: la partida no había terminado"
    )

    return 0


def ejecutar_benchmarks():
    """Ejecuta las mediciones existentes sin crear una vista."""

    from crypta.bench.bench import (
        partida_sintetica,
        comparar_formatos,
    )

    for cantidad in (100, 1000, 5000):
        partida, encabezado, fichas = partida_sintetica(
            cantidad
        )

        with tempfile.TemporaryDirectory() as carpeta:
            resultado = comparar_formatos(
                partida,
                encabezado,
                fichas,
                carpeta,
                repeticiones=5
            )

            print(
                f"\nCripta sintética de {cantidad} salas"
            )
            print(resultado)


def main():
    args = crear_argumentos()

    if args.cache_size < 1:
        print("Error: --cache-size debe ser mayor que cero.")
        return 1

    if args.bench and args.replay is not None:
        print(
            "Error: --bench y --replay no pueden utilizarse juntos."
        )
        return 1

    # Los benchmarks no utilizan HTTP ni vista interactiva.
    if args.bench:
        ejecutar_benchmarks()
        return 0

    print("=" * 45)
    print("              CRIPTA")
    print("=" * 45)

    # El replay no crea la vista ni el controlador (§6).
    if args.replay is not None:
        print(
            "Modo: REPLAY OFFLINE"
            if args.offline
            else "Modo: REPLAY ONLINE"
        )
        return reproducir(args)

    controlador = None
    codigo = 0

    try:
        controlador, gestor_cripta, datos_cripta, fuente = crear_partida(
            args
        )

        print(f"Cripta: {args.cripta}")
        print(f"Jugador: {args.jugador}")
        print(f"Semilla: {controlador.partida.semilla}")
        print(
            "Modo: OFFLINE" if args.offline
            else "Modo: ONLINE"
        )

        controlador.iniciar()

    except (RuntimeError, ValueError, OSError) as error:
        print(f"\nError: {error}")
        codigo = 1

    except KeyboardInterrupt:
        # Ctrl+C fuera de la lectura de comandos (mientras se carga una
        # sala, por ejemplo): se termina igual de ordenado.
        print("\nPartida interrumpida.")

    finally:
        if controlador is not None:
            # Al cargar una partida el controlador cambia de gestor: se
            # cierra el que tiene AHORA.
            controlador.gestor_contenido.cerrar()

            # Conservar lo descargado (modo en línea) SIEMPRE, también si
            # hubo un error o un Ctrl+C: el replay necesita la copia local.
            if not args.offline:
                try:
                    gestor_cripta.persistir(
                        args.cripta,
                        datos_cripta,
                        controlador.partida.mapa
                    )
                except OSError as error:
                    print(f"No se pudo guardar la copia local: {error}")

            print(
                f"\nLa partida quedó registrada en {RUTA_REGISTRO} "
                f"(la próxima partida lo reemplaza). Para repetirla:\n"
                f"  python -m crypta.main"
                f"{' --offline' if args.offline else ''} --replay {RUTA_REGISTRO}"
            )

            # §5.1: el reporte sale siempre que se jugó, aunque haya
            # habido un error.
            repositorio = controlador.repositorio_fichas
            controlador.vista.mostrar_reporte(
                fuente.cantidad_solicitudes(),
                datos_cripta["presupuesto_solicitudes"],
                repositorio.aciertos,
                repositorio.fallos_disco,
                repositorio.fallos_red,
            )

    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
