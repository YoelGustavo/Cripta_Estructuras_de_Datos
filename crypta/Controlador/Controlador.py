
import os
import shutil

from crypta.Controlador.Comandos import (
    ComandoInvalido,
    ejecutar_comando,
)
from crypta.Modelo.Partida import AccionInvalida
from crypta.Vista.VistaConsola import VistaConsola
from crypta.Adaptadores.GuardadoBinario import guardar_partida
from crypta.Adaptadores.GuardadoBinario import ArchivoGuardado
from crypta.Adaptadores.RegistroPartida import ErrorRegistro, leer_registro
from crypta.Controlador.GestorContenido import GestorContenido


RUTA_GUARDADO = "partida.cripta"

# Cuántos puestos de la tabla de puntajes se muestran.
LIMITE_RANKING = 10


def ruta_del_log_guardado(ruta_guardado):
    """Cada partida guardada va acompañada de una COPIA del log hasta ese
    momento: "partida.cripta" -> "partida.cripta.log"."""
    return ruta_guardado + ".log"


def copiar_archivo(origen, destino):
    """Copia a un temporal y reemplaza de una sola vez: si el programa se
    cae a mitad de la copia, el destino anterior queda intacto."""
    temporal = destino + ".tmp"
    shutil.copyfile(origen, temporal)
    os.replace(temporal, destino)


class Controlador:
    """Conecta la vista con una partida ya construida."""

    def __init__(
        self,
        partida,
        gestor_contenido,
        vista=None,
        registro=None,
        encabezado=None,
        repositorio_fichas=None,
        tabla_puntajes=None,
    ):
        self.partida = partida
        self.gestor_contenido = gestor_contenido
        self.vista = vista if vista is not None else VistaConsola()
        self.registro = registro
        self.encabezado = encabezado
        self.repositorio_fichas = repositorio_fichas
        self.tabla_puntajes = tabla_puntajes
    
    def iniciar(self):
        """Prepara la primera sala y ejecuta el ciclo de consola."""
        if not self.partida.iniciada:
            # La sala inicial y sus vecinas más cercanas llegan en UNA sola
            # solicitud (hasta 10 salas por lote, §3.4); garantizar_sala
            # espera esa respuesta en vez de pedir la sala inicial sola.
            self.gestor_contenido.precargar_async(
                self.partida.id_sala_inicial
            )
            self.gestor_contenido.garantizar_sala(
                self.partida.id_sala_inicial
            )
            self.partida.iniciar()

        self.vista.mostrar_ayuda()

        while not self.partida.terminada:
            self.gestor_contenido.procesar_pendientes()
            self.vista.mostrar_estado(self.partida)

            try:
                texto = self.vista.leer_comando()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if texto.lower() == "salir":
                break

            self.procesar_comando(texto)

        # El ciclo termina por "salir" o porque terminó la partida. Solo en
        # el segundo caso hay final que mostrar y puntaje que registrar.
        if self.partida.terminada:
            self._terminar_partida()

        self.vista.mostrar_mensaje("Sesión finalizada.")

    def _terminar_partida(self):
        """§2.12: mostrar cómo terminó la partida y registrar su puntaje.
        Se llama UNA sola vez: el ciclo ya no vuelve a empezar."""
        # La última pantalla: el golpe final, "Has muerto" o la victoria.
        self.vista.mostrar_estado(self.partida)

        if self.tabla_puntajes is None or self.encabezado is None:
            return

        try:
            puntaje = self.tabla_puntajes.registrar_partida(
                self.partida,
                self.encabezado.cripta_id,
                self.encabezado.version_cripta,
            )
        except (OSError, ValueError) as error:
            self.vista.mostrar_error(
                f"No se pudo registrar el puntaje: {error}"
            )
            return

        self.vista.mostrar_puntajes(
            self.tabla_puntajes.ranking(
                self.encabezado.cripta_id,
                LIMITE_RANKING,
            ),
            puntaje,
        )

    def procesar_comando(self, texto):
        """Interpreta comandos de interfaz y delega las acciones."""
        texto = texto.strip()

        if not texto:
            self.vista.mostrar_error("Escribe un comando.")
            return False

        partes = texto.split()
        nombre = partes[0].lower()

        if nombre == "ayuda" and len(partes) == 1:
            self.vista.mostrar_ayuda()
            return True

        if nombre == "estado" and len(partes) == 1:
            self.vista.mostrar_estado(self.partida)
            return True

        if nombre == "inventario" and len(partes) == 1:
            self.vista.mostrar_inventario(
                self.partida.jugador.inventario
            )
            return True

        if nombre == "puntajes" and len(partes) == 1:
            if self.tabla_puntajes is None or self.encabezado is None:
                self.vista.mostrar_error("No hay tabla de puntajes.")
                return False

            self.vista.mostrar_puntajes(
                self.tabla_puntajes.ranking(
                    self.encabezado.cripta_id,
                    LIMITE_RANKING,
                )
            )
            return True

        if nombre == "ordenar" and len(partes) == 2:
            try:
                self.vista.mostrar_inventario_ordenado(
                    self.partida.jugador.inventario,
                    partes[1].lower(),
                )
                return True
            except ValueError as error:
                self.vista.mostrar_error(str(error))
                return False

        # Guardar y cargar no se anotan en el log: no cambian la partida.
        if nombre == "guardar" and len(partes) == 1:
            if self.encabezado is None:
                self.vista.mostrar_error(
                    "No hay información de la cripta para guardar."
                )
                return False

            try:
                self.guardar(RUTA_GUARDADO)
            except (OSError, ValueError) as error:
                self.vista.mostrar_error(
                    f"No se pudo guardar la partida: {error}"
                )
                return False

            self.vista.mostrar_mensaje(
                f"Partida guardada correctamente en {RUTA_GUARDADO}"
            )
            return True

        if nombre == "cargar" and len(partes) == 1:
            try:
                self.cargar_partida(RUTA_GUARDADO)
                self.vista.mostrar_mensaje(
                    "Partida cargada correctamente."
                )
                return True
            except (OSError, ValueError) as error:
                self.vista.mostrar_error(
                    f"No se pudo cargar la partida: {error}"
                )
                return False

        
        try:
            comando = self._traducir(texto)

            ejecutar_comando(
                self.partida,
                comando,
                garantizar_sala=self.gestor_contenido.garantizar_sala,
            )

            # Registrar solo los comandos ejecutados correctamente.
            if self.registro is not None:
                self.registro.anotar(comando)

            # Precargar después de ejecutar el comando.
            if not self.partida.terminada:
                self.gestor_contenido.precargar_async(
                    self.partida.jugador.sala_actual
                )

            return True

        except (ComandoInvalido, AccionInvalida, ValueError) as error:
            self.vista.mostrar_error(str(error))
            return False

        except RuntimeError as error:
            # Sin red, o se agotó el presupuesto (PresupuestoAgotado es un
            # RuntimeError). Pasa en garantizar_sala, ANTES de la acción:
            # la partida no cambió y el comando no se anota. Se puede
            # seguir jugando en las salas ya cargadas, guardar o salir.
            self.vista.mostrar_error(
                f"{error}. La acción no se hizo."
            )
            return False


    def guardar(self, ruta=RUTA_GUARDADO):
        """Guarda la partida y, junto a ella, una copia del log hasta este
        momento. Al cargar, esa copia vuelve a ser el log: así el log
        siempre cuenta la historia de la partida que se está jugando, y el
        --replay la repite exactamente (§4.11)."""
        if self.registro is not None:
            copiar_archivo(self.registro.ruta, ruta_del_log_guardado(ruta))

        guardar_partida(
            self.partida,
            ruta,
            self.encabezado,
        )

    def _revisar_log_guardado(self, ruta_log, encabezado_guardado):
        """El log que acompaña al guardado tiene que existir y ser de ESA
        partida. Si no, cargar dejaría un log que el --replay no puede
        repetir: mejor no cargar y decirlo."""
        if not os.path.exists(ruta_log):
            raise ValueError(
                f"Falta {ruta_log}, el registro de la partida guardada. "
                f"Sin él, el --replay no podría repetir la partida."
            )

        try:
            encabezado_log, _ = leer_registro(ruta_log)
        except ErrorRegistro as error:
            raise ValueError(
                f"El registro de la partida guardada está dañado: {error}"
            ) from error

        if (encabezado_log.cripta_id != encabezado_guardado.cripta_id
                or encabezado_log.version_cripta != encabezado_guardado.version_cripta
                or encabezado_log.version_catalogo != encabezado_guardado.version_catalogo
                or encabezado_log.semilla != encabezado_guardado.semilla
                or encabezado_log.jugador != encabezado_guardado.jugador):
            raise ValueError(
                f"{ruta_log} no es el registro de la partida guardada."
            )

    def cargar_partida(self, ruta=RUTA_GUARDADO):
        if self.repositorio_fichas is None:
            raise ValueError(
                "No hay un repositorio de fichas configurado."
            )

        if self.encabezado is None:
            raise ValueError(
                "No hay información de la cripta actual."
            )

        archivo = ArchivoGuardado(ruta)
        encabezado_guardado = archivo.encabezado

        if encabezado_guardado.cripta_id != self.encabezado.cripta_id:
            raise ValueError(
                "La partida pertenece a otra cripta."
            )

        if encabezado_guardado.version_cripta != self.encabezado.version_cripta:
            raise ValueError(
                "La versión de la cripta no coincide."
            )

        if encabezado_guardado.version_catalogo != self.encabezado.version_catalogo:
            raise ValueError(
                "La versión del catálogo no coincide."
            )

        ruta_log = ruta_del_log_guardado(ruta)

        if self.registro is not None:
            self._revisar_log_guardado(ruta_log, encabezado_guardado)

        nueva_partida = archivo.cargar_partida(
            self.repositorio_fichas.obtener_ficha
        )

        nuevo_gestor = GestorContenido(
            self.gestor_contenido._fuente,
            nueva_partida.mapa,
            encabezado_guardado.cripta_id,
            self.repositorio_fichas,
        )

        # Sustituimos ambos únicamente después de restaurar
        # correctamente la partida.
        gestor_anterior = self.gestor_contenido
        self.partida = nueva_partida
        self.gestor_contenido = nuevo_gestor
        self.encabezado = encabezado_guardado

        # El log vuelve a ser el de la partida guardada. Lo que se jugó
        # después de guardar ya no pasó: no puede quedar en el log.
        if self.registro is not None:
            copiar_archivo(ruta_log, self.registro.ruta)

        # No esperamos solicitudes HTTP antiguas para continuar.
        gestor_anterior._ejecutor.shutdown(
            wait=False,
            cancel_futures=True,
        )


    def _traducir(self, texto):
        """Convierte números de pantalla en identificadores internos."""
        partes = texto.strip().split()

        if not partes:
            raise ComandoInvalido("Línea vacía")

        nombre = partes[0].lower()

        # Los nombres de la interfaz son diferentes de los del
        # lenguaje común utilizado por el replay. Sin dict (§7):
        # son solo dos nombres, alcanza con comparar.
        if nombre == "siguiente":
            nombre = "avanzar"
        elif nombre == "anterior":
            nombre = "retroceder"

        if nombre == "recoger" and len(partes) == 2:
            if partes[1].lower() == "pergamino":
                return "recoger_pergamino"

            if partes[1].isdigit():
                numero = int(partes[1])

                if numero < 1:
                    raise ComandoInvalido(
                        "El primer objeto es el número 1"
                    )

                return f"recoger {numero - 1}"

        if nombre == "atacar" and len(partes) == 2:
            if partes[1].isdigit():
                numero = int(partes[1])
                enemigos = self.partida.enemigos_presentes()

                if numero < 1 or numero > len(enemigos):
                    raise AccionInvalida(
                        "No hay un enemigo con ese número"
                    )

                enemigo = enemigos.obtener(numero - 1)
                return f"atacar {enemigo.id_instancia}"

        return " ".join([nombre] + partes[1:])
