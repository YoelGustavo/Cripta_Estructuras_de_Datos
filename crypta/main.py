
import argparse
import random
import tempfile

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco
from crypta.Adaptadores.FuenteHTTP import FuenteHTTP
from crypta.Adaptadores.FuenteOffline import FuenteOffline
from crypta.Controlador.RepositorioFichas import RepositorioFichas

from crypta.Adaptadores.RegistroPartida import (
    Encabezado,
    RegistroPartida,
    leer_registro,
    ErrorRegistro,
)

from crypta.Controlador.Controlador import Controlador
from crypta.Controlador.Comandos import ejecutar_comando
from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.GestorCripta import GestorCripta

from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Partida import Partida

from crypta.Vista.VistaConsola import VistaConsola


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


def crear_partida(args):
    """Construye los componentes de una partida."""

    almacen = AlmacenDisco()

    if args.offline:
        fuente = FuenteOffline(almacen)
    else:
        fuente = FuenteHTTP()

    gestor_cripta = GestorCripta(
        fuente,
        almacen
    )

    datos_cripta, mapa, desde_cache = gestor_cripta.cargar(
        args.cripta
    )

    version_catalogo = fuente.obtener_version_catalogo()["version"]

    repositorio = RepositorioFichas(
        fuente=fuente,
        almacen=almacen,
        version_catalogo=version_catalogo,
        cache_size=args.cache_size
    )

    datos_jugador = datos_cripta["jugador"]

    jugador = Jugador(
        nombre=args.jugador,
        vida_max=datos_jugador["vida_max"],
        ataque=datos_jugador["ataque"],
        defensa=datos_jugador["defensa"],
        velocidad=datos_jugador["velocidad"],
        inventario_max=datos_cripta["inventario_max"]
    )

    semilla = (
        args.semilla
        if args.semilla is not None
        else random.randint(0, 2**31 - 1)
    )

    partida = Partida(
        mapa=mapa,
        jugador=jugador,
        id_sala_inicial=datos_cripta["sala_inicial"],
        fichas=repositorio.obtener_ficha,
        semilla=semilla,
        id_sala_salida=datos_cripta["sala_salida"],
        llave_salida=datos_cripta["llave_salida"]
    )

    gestor_contenido = GestorContenido(
        fuente,
        mapa,
        args.cripta
    )

    encabezado = Encabezado(
        cripta_id=args.cripta,
        version_cripta=datos_cripta["version"],
        version_catalogo=version_catalogo,
        semilla=semilla,
        jugador=args.jugador
    )

    # En modo replay no se crea ni sobrescribe el registro.
    registro = None

    if args.replay is None:
        registro = RegistroPartida.crear(
            "partida.log",
            encabezado
        )

    # En replay no se instancia VistaConsola ni Controlador.
    if args.replay is not None:
        return (
            partida,
            gestor_contenido,
            gestor_cripta,
            datos_cripta,
            encabezado,
        )

    controlador = Controlador(
        partida=partida,
        gestor_contenido=gestor_contenido,
        vista=VistaConsola(),
        registro=registro,
        encabezado=encabezado,
        repositorio_fichas=repositorio
    )

    return controlador, gestor_cripta, datos_cripta


def reproducir_partida(partida, gestor, encabezado_actual,
                      encabezado_registro, comandos):
    """Reproduce comandos internos sin vista ni entrada de teclado."""

    if encabezado_registro.cripta_id != encabezado_actual.cripta_id:
        raise ValueError(
            "La cripta del registro no coincide."
        )

    if encabezado_registro.version_cripta != encabezado_actual.version_cripta:
        raise ValueError(
            "La versión de la cripta no coincide."
        )

    if encabezado_registro.version_catalogo != encabezado_actual.version_catalogo:
        raise ValueError(
            "La versión del catálogo no coincide."
        )

    if encabezado_registro.semilla != encabezado_actual.semilla:
        raise ValueError(
            "La semilla del registro no coincide."
        )

    if not partida.iniciada:
        gestor.garantizar_sala(
            partida.id_sala_inicial
        )
        partida.iniciar()

    cantidad = 0

    while not comandos.esta_vacia() and not partida.terminada:
        comando = comandos.desencolar()

        ejecutar_comando(
            partida,
            comando,
            garantizar_sala=gestor.garantizar_sala
        )

        cantidad += 1

    print(
        f"Replay finalizado: {cantidad} comandos ejecutados."
    )

    print(f"Sala actual: {partida.jugador.sala_actual}")
    print(
        f"Vida: {partida.jugador.vida}/{partida.jugador.vida_max}"
    )

    return cantidad


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

    encabezado_registro = None
    comandos_replay = None

    if args.replay is not None:
        try:
            encabezado_registro, comandos_replay = leer_registro(
                args.replay
            )
        except ErrorRegistro as error:
            print(f"Error de replay: {error}")
            return 1

        args.cripta = encabezado_registro.cripta_id
        args.jugador = encabezado_registro.jugador
        args.semilla = encabezado_registro.semilla

    print("=" * 45)
    print("              CRIPTA")
    print("=" * 45)

    gestor_contenido = None

    try:
        if args.replay is not None:
            (
                partida,
                gestor_contenido,
                gestor_cripta,
                datos_cripta,
                encabezado_actual,
            ) = crear_partida(args)

            print(f"Cripta: {args.cripta}")
            print(f"Jugador: {args.jugador}")
            print(f"Semilla: {partida.semilla}")
            print(
                "Modo: REPLAY OFFLINE"
                if args.offline
                else "Modo: REPLAY ONLINE"
            )

            reproducir_partida(
                partida,
                gestor_contenido,
                encabezado_actual,
                encabezado_registro,
                comandos_replay
            )

            mapa_final = partida.mapa

        else:
            controlador, gestor_cripta, datos_cripta = crear_partida(
                args
            )

            gestor_contenido = controlador.gestor_contenido

            print(f"Cripta: {args.cripta}")
            print(f"Jugador: {args.jugador}")
            print(f"Semilla: {controlador.partida.semilla}")
            print(
                "Modo: OFFLINE" if args.offline
                else "Modo: ONLINE"
            )

            controlador.iniciar()

            mapa_final = controlador.partida.mapa

        # Conservar los datos descargados en modo online.
        if not args.offline:
            gestor_cripta.persistir(
                args.cripta,
                datos_cripta,
                mapa_final
            )

    except (RuntimeError, ValueError, OSError) as error:
        print(f"\nError: {error}")
        return 1

    finally:
        if gestor_contenido is not None:
            gestor_contenido._ejecutor.shutdown(
                wait=True
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
