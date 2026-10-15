
from crypta.Controlador.Comandos import (
    ComandoInvalido,
    ejecutar_comando,
)
from crypta.Modelo.Partida import AccionInvalida
from crypta.Vista.VistaConsola import VistaConsola
from crypta.Adaptadores.GuardadoBinario import guardar_partida
from crypta.Adaptadores.GuardadoBinario import ArchivoGuardado
from crypta.Controlador.GestorContenido import GestorContenido


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
    ):
        self.partida = partida
        self.gestor_contenido = gestor_contenido
        self.vista = vista if vista is not None else VistaConsola()
        self.registro = registro
        self.encabezado = encabezado
        self.repositorio_fichas = repositorio_fichas
    
    def iniciar(self):
        """Prepara la primera sala y ejecuta el ciclo de consola."""
        if not self.partida.iniciada:
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

        self.vista.mostrar_mensaje("Sesión finalizada.")

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

        # Los comandos de persistencia se conectarán
        # cuando integremos los adaptadores correspondientes.
        if nombre == "guardar" and len(partes) == 1:
            if self.encabezado is None:
                self.vista.mostrar_error(
                    "No hay información de la cripta para guardar."
                )
                return False

            try:
                guardar_partida(
                    self.partida,
                    "partida.cripta",
                    self.encabezado,
                )
            except (OSError, ValueError) as error:
                self.vista.mostrar_error(
                    f"No se pudo guardar la partida: {error}"
                )
                return False

            self.vista.mostrar_mensaje(
                "Partida guardada correctamente en partida.cripta"
            )
            return True

        if nombre == "cargar" and len(partes) == 1:
            try:
                self.cargar_partida("partida.cripta")
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


    def cargar_partida(self, ruta="partida.cripta"):
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

        nueva_partida = archivo.cargar_partida(
            self.repositorio_fichas.obtener_ficha
        )

        nuevo_gestor = GestorContenido(
            self.gestor_contenido._fuente,
            nueva_partida.mapa,
            encabezado_guardado.cripta_id,
        )

        # Sustituimos ambos únicamente después de restaurar
        # correctamente la partida.
        gestor_anterior = self.gestor_contenido
        self.partida = nueva_partida
        self.gestor_contenido = nuevo_gestor
        self.encabezado = encabezado_guardado

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
        # lenguaje común utilizado por el replay.
        alias = {
            "siguiente": "avanzar",
            "anterior": "retroceder",
        }

        nombre = alias.get(nombre, nombre)

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
