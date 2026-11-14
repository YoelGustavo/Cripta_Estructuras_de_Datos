from crypta.Adaptadores.RegistroPartida import leer_registro
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_y_registrar
from crypta.Modelo.LineaDeTiempo import K_POR_DEFECTO, LineaDeTiempo
from crypta.Modelo.Partida import AccionInvalida


class ReproduccionIncompatible(Exception):
    """El registro es de una versión de cripta o de catálogo que ya no se
    tiene. §4.11: hay que avisar que no se puede garantizar una
    reproducción fiel, y NO reproducir contra datos distintos."""


class ReproduccionFallida(Exception):
    def __init__(self, numero, comando, motivo):
        super().__init__(
            f"El comando {numero} del registro ('{comando}') no se pudo "
            f"repetir: {motivo}. La reproducción ya no es la partida original."
        )
        self.numero = numero
        self.comando = comando
        self.motivo = str(motivo)


class Reproduccion:
    """Lo que dejó un `--replay`: la partida reproducida, la cantidad de
    comandos repetidos y su línea de tiempo (capacidad 004, FR-413), armada
    igual que jugando."""

    def __init__(self, encabezado, partida, comandos, linea=None):
        self.encabezado = encabezado
        self.partida = partida
        self.comandos = comandos
        self.linea = linea


class Reproductor:

    def __init__(self, preparador):
        self._preparador = preparador

    def reproducir(self, ruta, al_ejecutar=None, k=K_POR_DEFECTO):
        encabezado, comandos = leer_registro(ruta)
        return self.reproducir_registro(encabezado, comandos, al_ejecutar, k)

    def reproducir_registro(self, encabezado, comandos, al_ejecutar=None,
                            k=K_POR_DEFECTO):
        self._revisar_versiones(encabezado)

        partida = self._preparador.crear_partida(encabezado)

        if partida.iniciada:
            raise ValueError("crear_partida debe devolver la partida SIN iniciar")

        if partida.semilla != encabezado.semilla:
            raise ValueError(
                f"crear_partida usó la semilla {partida.semilla} y el registro "
                f"dice {encabezado.semilla}"
            )

        partida.iniciar()

        # La misma línea que arma el Controlador al jugar (research D12).
        linea = LineaDeTiempo(k)
        linea.iniciar(partida)

        numero = 0

        while not comandos.esta_vacia():
            comando = comandos.desencolar()
            numero += 1

            if partida.terminada:
                raise ReproduccionFallida(numero, comando, "la partida ya había terminado")

            try:
                ejecutar_y_registrar(partida, linea, comando,
                                     self._preparador.garantizar_sala)
            except (ComandoInvalido, AccionInvalida) as error:
                raise ReproduccionFallida(numero, comando, error) from error

            if al_ejecutar is not None:
                al_ejecutar(numero, comando, partida)

        return Reproduccion(encabezado, partida, numero, linea)

    def _revisar_versiones(self, encabezado):
        if not self._preparador.cripta_disponible(encabezado.cripta_id,
                                                  encabezado.version_cripta):
            raise ReproduccionIncompatible(
                f"El registro es de la cripta '{encabezado.cripta_id}' en su "
                f"versión '{encabezado.version_cripta}', que ya no está "
                f"disponible (ni en el servidor ni en una copia local). No se "
                f"puede garantizar una reproducción fiel."
            )

        if not self._preparador.catalogo_disponible(encabezado.version_catalogo):
            raise ReproduccionIncompatible(
                f"El registro usa la versión '{encabezado.version_catalogo}' "
                f"del catálogo, que ya no está disponible (ni en el servidor "
                f"ni en una copia local). No se puede garantizar una "
                f"reproducción fiel."
            )