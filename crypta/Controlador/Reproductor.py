"""El reproductor: --replay partida.Log
Lee un registro de partida y vuelve a jugar TODOS sus comandos, en orden,
sin pedirle nada al usuario. Como el modelo es determinista (§2.6: misma
versión de cripta, misma semilla y mismas acciones = misma partida), el
resultado es la misma partida que se jugó: mismo reloj, misma vida, mismos
enemigos, misma bitácora...
Lo que el reproductor NO sabe hacer (red, disco, armar el jugador con los
datos de la cripta) se lo da quien lo usa, con un objeto "preparador" que
tiene estos cuatro métodos:
    cripta_disponible(cripta_id, version) -> bool
        ¿Se tiene ESA versión de la cripta? Sí, si es la que sirve hoy el
        servidor o si hay una copia local completa de esa versión.
    catalogo_disponible(version) -> bool
        Lo mismo para el catálogo.
    crear_partida(encabezado) -> Partida
        Una partida NUEVA, sin iniciar, con la semilla del encabezado y
        con el contenido de la sala inicial ya cargado. Debe armarse igual
        que cuando se juega (en la Fase 7, con el mismo código).
    garantizar_sala(id_sala)
        Carga el contenido de esa sala, de la versión del registro. Si en
        medio de la reproducción resulta que no se tiene (por ejemplo, la
        copia local no trae esa sala y el servidor ya cambió de versión),
        lanza ReproduccionIncompatible: tampoco se sigue en silencio.
Así se puede probar con un preparador de prueba, sin red, y en la Fase 7
el preparador de verdad usa GestorCripta, GestorContenido y
RepositorioFichas.
"""

from crypta.Adaptadores.RegistroPartida import leer_registro
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Modelo.Partida import AccionInvalida


class ReproduccionIncompatible(Exception):
    """El registro es de una versión de cripta o de catálogo que ya no se
    tiene. §4.11: hay que avisar que no se puede garantizar una
    reproducción fiel, y NO reproducir contra datos distintos."""


class ReproduccionFallida(Exception):
    """Un comando del registro no se pudo ejecutar. En la partida original
    sí se pudo (solo se anota lo que salió bien), así que la reproducción
    se separó de la original: seguir no tendría sentido."""

    def __init__(self, numero, comando, motivo):
        super().__init__(
            f"El comando {numero} del registro ('{comando}') no se pudo "
            f"repetir: {motivo}. La reproducción ya no es la partida original."
        )
        self.numero = numero        # 1 = el primer comando del registro
        self.comando = comando
        self.motivo = str(motivo)


class Reproduccion:
    """Lo que queda al terminar: el encabezado del registro, la partida
    tal como quedó y cuántos comandos se repitieron."""

    def __init__(self, encabezado, partida, comandos):
        self.encabezado = encabezado
        self.partida = partida
        self.comandos = comandos


class Reproductor:

    def __init__(self, preparador):
        self._preparador = preparador

    def reproducir(self, ruta, al_ejecutar=None):
        #reproduce el registro de la partida.
        encabezado, comandos = leer_registro(ruta)
        return self.reproducir_registro(encabezado, comandos, al_ejecutar)

    def reproducir_registro(self, encabezado, comandos, al_ejecutar=None):
        """Lo mismo, con el registro ya leído (Encabezado y Cola de
        comandos). La cola queda vacía."""

        # 1. Antes de jugar nada: ¿se tienen EXACTAMENTE esas versiones?
        self._revisar_versiones(encabezado)

        # 2. La misma partida del principio, con la misma semilla.
        partida = self._preparador.crear_partida(encabezado)

        if partida.iniciada:
            raise ValueError("crear_partida debe devolver la partida SIN iniciar")

        if partida.semilla != encabezado.semilla:
            raise ValueError(
                f"crear_partida usó la semilla {partida.semilla} y el registro "
                f"dice {encabezado.semilla}"
            )

        partida.iniciar()

        # 3. Los comandos, en el orden en que se jugaron.
        numero = 0

        while not comandos.esta_vacia():
            comando = comandos.desencolar()
            numero += 1

            # En la partida original, después del final ya no se juega.
            if partida.terminada:
                raise ReproduccionFallida(numero, comando, "la partida ya había terminado")

            try:
                ejecutar_comando(partida, comando, self._preparador.garantizar_sala)
            except (ComandoInvalido, AccionInvalida) as error:
                raise ReproduccionFallida(numero, comando, error) from error

            if al_ejecutar is not None:
                al_ejecutar(numero, comando, partida)

        return Reproduccion(encabezado, partida, numero)

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