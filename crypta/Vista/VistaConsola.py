
from crypta.Modelo.Sala import DIRECCIONES


class VistaConsola:
    """Interfaz de texto. No ejecuta reglas del juego."""

    def mostrar_mensaje(self, mensaje):
        print(mensaje)

    def mostrar_error(self, mensaje):
        print(f"Error: {mensaje}")

    def leer_comando(self):
        """Devuelve el texto introducido, sin interpretarlo."""
        return input("\n¿Qué deseas hacer? > ").strip()

    def mostrar_ayuda(self):
        print("\nCOMANDOS DISPONIBLES")
        print("  mover N/S/E/O       Moverse")
        print("  abrir N/S/E/O       Abrir una puerta")
        print("  atacar 1            Atacar al enemigo número 1")
        print("  esperar             Esperar un turno")
        print("  recoger 1           Recoger el primer objeto")
        print("  recoger pergamino   Recoger un pergamino")
        print("  usar                Usar el objeto actual")
        print("  equipar             Equipar el objeto actual")
        print("  soltar              Soltar el objeto actual")
        print("  inventario          Mostrar inventario")
        print("  siguiente           Avanzar por el inventario")
        print("  anterior            Retroceder por el inventario")
        print("  ordenar nombre/peso/valor")
        print("  pergamino           Retroceder una acción")
        print("  puntajes            Ver la tabla de puntajes")
        print("  guardar             Guardar partida")
        print("  cargar              Cargar partida")
        print("  estado              Mostrar el estado")
        print("  ayuda               Mostrar esta ayuda")
        print("  salir               Salir del juego")

    def mostrar_estado(self, partida):
        sala = partida.sala_actual()
        jugador = partida.jugador
        inventario = jugador.inventario

        print("\n" + "=" * 55)
        print(f"CRIPTA | Tiempo: {partida.reloj}")
        print("=" * 55)

        print(f"\nSALA: {sala.nombre} (ID: {sala.id})")
        print(f"Vida: {jugador.vida}/{jugador.vida_max}")
        print(f"Pergaminos: {inventario.cantidad_pergaminos()}")

        efectos = []
        if partida.esta_envenenado():
            efectos.append("Veneno")
        if partida.antorcha_encendida():
            efectos.append("Antorcha encendida")

        print("Efectos: " + (", ".join(efectos) if efectos else "Ninguno"))

        print("\nSALIDAS")
        hay_salidas = False

        for direccion in DIRECCIONES:
            puerta = sala.obtener_puerta(direccion)
            if puerta is None:
                continue

            hay_salidas = True
            estado = "Cerrada" if puerta.esta_cerrada() else "Abierta"
            print(f"  {direccion}: sala {puerta.sala_destino} ({estado})")

        if not hay_salidas:
            print("  No hay salidas.")

        print("\nENEMIGOS")
        enemigos = partida.enemigos_presentes()

        if len(enemigos) == 0:
            print("  Ninguno.")
        else:
            for i in range(len(enemigos)):
                enemigo = enemigos.obtener(i)
                print(
                    f"  {i + 1}. {enemigo.nombre} "
                    f"[{enemigo.id_instancia}] "
                    f"- Vida: {enemigo.vida}"
                )

        print("\nOBJETOS EN EL SUELO")
        objetos = partida.objetos_del_suelo()

        if len(objetos) == 0:
            print("  Ninguno.")
        else:
            for i in range(len(objetos)):
                ficha = objetos.obtener(i)
                print(
                    f"  {i + 1}. "
                    f"{ficha.get('nombre', ficha.get('id', 'Objeto'))}"
                )

        pergaminos_suelo = sala.cantidad_pergaminos()
        if pergaminos_suelo:
            print(f"  Pergaminos de retroceso: {pergaminos_suelo}")

        print("\nINVENTARIO")
        self.mostrar_inventario(inventario)

        print("\nÚLTIMOS MENSAJES")
        mensajes = list(partida.bitacora)

        if not mensajes:
            print("  Sin mensajes.")
        else:
            for mensaje in mensajes[-20:]:
                print(f"  {mensaje}")

        if partida.terminada:
            if partida.resultado == "victoria":
                print("\n*** ¡VICTORIA! Escapaste de la cripta. ***")
            else:
                print("\n*** DERROTA: has muerto. ***")

    def mostrar_reporte(self, solicitudes, presupuesto, aciertos,
                        fallos_disco, fallos_red):
        """§5.1: lo que costó la partida en red y cómo le fue a la caché."""
        fallos = fallos_disco + fallos_red

        print("\nRECURSOS DE LA PARTIDA")
        print(f"  Solicitudes de red: {solicitudes} de {presupuesto} permitidas")
        print(
            f"  Caché de fichas: {aciertos} aciertos, {fallos} fallos "
            f"({fallos_disco} leídas del disco, {fallos_red} pedidas por red)"
        )

    def mostrar_puntajes(self, ranking, actual=None):
        """La tabla de puntajes ya ordenada (TablaPuntajes.ranking).
        'actual' es el puntaje de la partida que acaba de terminar: se
        marca para que el jugador vea en qué puesto quedó."""
        print("\nTABLA DE PUNTAJES")

        if len(ranking) == 0:
            print("  Todavía no hay partidas terminadas.")
            return

        print("  #   Jugador          Resultado  Tiempo  Acciones  Enemigos")

        aparece = False

        for i in range(len(ranking)):
            puntaje = ranking.obtener(i)
            marca = ""

            if puntaje is actual:
                marca = "  <- esta partida"
                aparece = True

            print(
                f"  {i + 1:<3} {puntaje.jugador:<16} "
                f"{puntaje.resultado:<10} {puntaje.tiempo:>6}  "
                f"{puntaje.acciones:>8}  {puntaje.enemigos:>8}{marca}"
            )

        if actual is not None and not aparece:
            print(f"  Esta partida quedó fuera de los primeros {len(ranking)}.")

    def mostrar_inventario(self, inventario):
        print(
            f"  Espacios: {inventario.ocupados()}/"
            f"{inventario.capacidad()}"
        )

        objetos = inventario.orden_real()
        actual, arma, armadura = inventario.posiciones()

        if not objetos:
            print("  Sin objetos.")

        for i, objeto in enumerate(objetos):
            marcas = []

            if i == actual:
                marcas.append("ACTUAL")
            if i == arma:
                marcas.append("ARMA")
            if i == armadura:
                marcas.append("ARMADURA")

            etiqueta = f" [{' | '.join(marcas)}]" if marcas else ""
            nombre = objeto.get("nombre", objeto.get("id", "Objeto"))

            print(f"  {i + 1}. {nombre}{etiqueta}")

        if inventario.cantidad_pergaminos():
            print(
                "  Pergaminos: "
                f"{inventario.cantidad_pergaminos()}"
            )

    def mostrar_inventario_ordenado(self, inventario, criterio):
        """Muestra una copia ordenada, sin cambiar el inventario."""
        objetos, algoritmo = inventario.vista_ordenada(criterio)

        print(f"\nINVENTARIO ORDENADO POR {criterio.upper()}")
        print(f"Algoritmo: {algoritmo}")

        if len(objetos) == 0:
            print("  Sin objetos.")
            return

        for i in range(len(objetos)):
            objeto = objetos.obtener(i)
            print(
                f"  {i + 1}. "
                f"{objeto.get('nombre', objeto.get('id', 'Objeto'))}"
            )
