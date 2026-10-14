import random

from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Efecto import ANTORCHA, VELOCIDAD, VENENO, Efecto
from crypta.Modelo.EstadoJuego import EstadoJuego
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Inventario import CLASE_PERGAMINO, CLASES_EQUIPABLES
from crypta.Modelo.Rastreador import sala_con_rastro_mas_fresco
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Bitacora import Bitacora


# Costo base de cada acción (§2.3). El tiempo real que tarda depende de
# la velocidad de quien la hace: Actor.intervalo(costo).
COSTO_MOVER = 100
COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_ABRIR = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25

# Comportamientos (§2.8), como vienen en la ficha. Cualquier otro valor
# ("guardián", con o sin tilde, o ninguno) se trata como guardián: espera.
ERRANTE = "errante"
RASTREADOR = "rastreador"

# Efectos temporales (§2.10).
INTERVALO_VENENO = 80          # un pulso de daño cada 80...
DURACION_VENENO = 400          # ...durante 400 desde que se aplica
INTERVALO_REGENERACION = 200
REARME_POR_DEFECTO = 300       # si la ficha de la trampa no dice otro

# Tipos de evento de la agenda.
TURNO_JUGADOR = "turno_jugador"
TURNO_ENEMIGO = "turno_enemigo"
CIERRE_PUERTA = "cierre_puerta"
PULSO_VENENO = "pulso_veneno"
FIN_VELOCIDAD = "fin_velocidad"
APAGAR_ANTORCHA = "apagar_antorcha"
REGENERACION = "regeneracion"
REARME_TRAMPA = "rearme_trampa"


class AccionInvalida(Exception):
    """El jugador pidió algo que no se puede hacer (no hay salida, la
    puerta está cerrada...). Se lanza ANTES de abrir la acción: no se
    gasta tiempo ni se anota nada. El controlador muestra el mensaje y le
    vuelve a pedir una decisión."""


class _EnemigoQuitado:
    """Para deshacer la salida de un enemigo de una sala (porque murió o,
    más adelante, porque se movió): lo vuelve a poner en la MISMA posición
    del Vector de la sala, para que todo quede exactamente igual."""

    def __init__(self, sala, enemigo, posicion):
        self.sala = sala
        self.enemigo = enemigo
        self.posicion = posicion

    def restaurar(self):
        self.sala.insertar_enemigo(self.posicion, self.enemigo)


class Partida:
    """Las reglas del juego (§2): el reloj, los turnos y las acciones.

    No sabe nada de red ni de consola. Lo que necesita de afuera se lo dan:
      - mapa: con el contenido de las salas ya cargado donde haga falta
        (el controlador llama a garantizar_sala ANTES de pedir una acción).
      - fichas: una función id_de_catálogo -> ficha (dict). El controlador
        le pasa repositorio.obtener_ficha.

    Cómo funciona el tiempo (§2.3): entre dos llamadas de afuera, la
    partida siempre está parada en una DECISIÓN del jugador. Cada acción:
      1. abre una acción en el historial (todo lo que pase desde aquí se
         puede deshacer con un pergamino, §2.11);
      2. hace lo suyo y programa el próximo turno del jugador;
      3. corre la agenda (enemigos, efectos...) hasta que vuelva a ser
         turno del jugador.
    """

    def __init__(self, mapa, jugador, id_sala_inicial, fichas, semilla=0,
                 id_sala_salida=None, llave_salida=None):
        self.mapa = mapa
        self.jugador = jugador
        self.estado = EstadoJuego(jugador.inventario)

        # §2.6: toda la aleatoriedad sale de AQUÍ, nunca del random global.
        # Misma semilla + mismas acciones = misma partida (--replay).
        self.semilla = semilla
        self.azar = random.Random(semilla)

        self._fichas = fichas
        self._id_sala_inicial = id_sala_inicial

        # §2.12: se gana al entrar a la sala de salida DESPUÉS de haber
        # abierto con su llave la puerta que lleva a ella (datos generales
        # de la cripta: "sala_salida" y "llave_salida").
        self._id_sala_salida = id_sala_salida
        self._llave_salida = llave_salida
        self.puerta_de_salida_abierta = False

        # Para el pergamino: si en el intervalo de la acción actual ya se
        # anotó cómo estaba el generador de azar (ver _tirar_dado).
        self._azar_anotado = False

        self.iniciada = False
        self.terminada = False
        self.resultado = None            # "victoria" o "derrota"

        # Para la tabla de puntajes (§2.12). Las acciones deshechas con un
        # pergamino no cuentan (el contador vuelve atrás con todo lo demás),
        # y usar el pergamino no es una acción (§2.11).
        self.acciones_jugador = 0
        self.enemigos_derrotados = 0

        # Efectos activos del jugador (§2.10). None = no tiene.
        self.veneno = None
        self.antorcha = None

        self.bitacora = Bitacora()

    # Atajos de lectura (para la vista, las pruebas y el guardado).
    @property
    def id_sala_inicial(self):
        return self._id_sala_inicial

    @property
    def id_sala_salida(self):
        return self._id_sala_salida

    @property
    def llave_salida(self):
        return self._llave_salida

    @property
    def reloj(self):
        return self.estado.reloj

    @property
    def agenda(self):
        return self.estado.agenda

    def sala_actual(self):
        return self.mapa.obtener_sala(self.jugador.sala_actual)

    def enemigos_presentes(self):
        """Vector con los enemigos vivos de la sala del jugador, en el orden
        de la sala. La vista los numera ("Rata gigante #1", "#2"...) y el
        jugador escoge a cuál atacar (§2.6)."""
        sala = self.sala_actual()
        presentes = Vector()

        for i in range(sala.cantidad_enemigos()):
            enemigo = sala.enemigo_en(i)

            if enemigo.esta_activo() and enemigo.esta_vivo():
                presentes.agregar(enemigo)

        return presentes

    def esta_envenenado(self):
        return self.veneno is not None

    def antorcha_encendida(self):
        return self.antorcha is not None

    def objetos_del_suelo(self):
        """Vector con las fichas de los objetos del suelo de la sala del
        jugador, en orden (la posición es la que se le pasa a recoger).
        Los pergaminos van aparte: sala_actual().cantidad_pergaminos()."""
        sala = self.sala_actual()
        fichas = Vector()

        for i in range(sala.cantidad_objetos()):
            fichas.agregar(self._fichas(sala.objeto_en(i)))

        return fichas

    # =========================================================
    # INICIO (§2.4)
    # =========================================================

    def iniciar(self):
        """Reloj en 0, el jugador en la sala inicial (con rastro en 0), los
        enemigos de esa sala se activan y el jugador decide primero."""
        if self.iniciada:
            raise RuntimeError("La partida ya se inició")

        sala = self.mapa.obtener_sala(self._id_sala_inicial)

        if sala is None:
            raise ValueError(f"No existe la sala inicial {self._id_sala_inicial}")

        # §2.4: "El contenido de la sala inicial debe cargarse antes de
        # aceptar la primera acción".
        if not sala.contenido_cargado():
            raise RuntimeError(
                f"Falta el contenido de la sala inicial {sala.id}: "
                f"el controlador debe cargarlo antes de iniciar"
            )

        self.iniciada = True

        # Nada de esto se anota en el historial: todavía no hay ninguna
        # acción del jugador que deshacer (registrar_cambio lo ignora).
        # §2.4: el jugador está en la sala inicial desde el instante 0.
        self._avisar(f"Entras en {sala.nombre}.")
        self._poner_jugador_en(sala)
        self._programar(self.jugador, 0, TURNO_JUGADOR)

        self._correr_hasta_el_jugador()

    # =========================================================
    # ACCIONES DEL JUGADOR
    # =========================================================

    def esperar(self):
        self._verificar_que_se_puede_actuar()
        self._empezar_accion("esperar")
        self._avisar("Esperas.")
        self._terminar_accion(COSTO_ESPERAR)

    def destino_de(self, direccion):
        """Id de la sala a la que lleva la salida en esa dirección, o None
        si no hay. El controlador lo usa para cargar el contenido de esa
        sala ANTES de llamar a mover (§2.4: la acción no se confirma hasta
        tener el contenido; esperar la red no avanza el reloj)."""
        puerta = self.sala_actual().obtener_puerta(direccion)

        if puerta is None:
            return None

        return puerta.sala_destino

    def mover(self, direccion):
        """Moverse a la sala vecina por la salida en esa dirección (N, S,
        E u O). Costo 100. Devuelve la sala a la que llegó."""
        self._verificar_que_se_puede_actuar()

        # Primero se revisa TODO lo que puede impedirlo. Si algo falla,
        # no se abrió ninguna acción: no pasa el tiempo ni se anota nada.
        puerta = self.sala_actual().obtener_puerta(direccion)

        if puerta is None:
            raise AccionInvalida(f"No hay salida hacia {direccion!r}")

        if puerta.esta_cerrada():
            if puerta.requiere_llave():
                raise AccionInvalida("La puerta está cerrada con llave")

            raise AccionInvalida("La puerta está cerrada")

        destino = puerta.sala_destino_ref

        if destino is None:
            destino = self.mapa.obtener_sala(puerta.sala_destino)

        if destino is None:
            raise ValueError(f"La salida lleva a la sala {puerta.sala_destino}, que no existe")

        if not destino.contenido_cargado():
            raise RuntimeError(
                f"Falta el contenido de la sala {destino.id}: el controlador "
                f"debe llamar a garantizar_sala antes de mover"
            )

        # Ahora sí: la acción ocurre en el instante actual. El jugador
        # entra YA a la sala; el costo solo decide cuándo vuelve a actuar
        # (§2.13: en t=0 se mueve al norte y en t=66 la rata ya lo ve ahí).
        self._empezar_accion("mover")
        self._avisar(f"Entras en {destino.nombre}.")
        self._poner_jugador_en(destino)

        # §2.10: las trampas armadas se activan inmediatamente después de
        # completar el movimiento, antes del siguiente evento del reloj.
        self._activar_trampas(destino)

        # §2.12: victoria (si la trampa no lo mató antes).
        if not self.terminada and self._es_victoria(destino):
            self.terminada = True
            self.resultado = "victoria"
            self._avisar("¡Escapaste de la cripta!")

        self._terminar_accion(COSTO_MOVER)

        return destino

    def atacar(self, enemigo):
        """Atacar a un enemigo de la misma sala (§2.6). Costo 100.
        Devuelve el daño hecho."""
        self._verificar_que_se_puede_actuar()

        if enemigo is None or not enemigo.esta_activo() or not enemigo.esta_vivo():
            raise AccionInvalida("Ese enemigo no está para pelear")

        if enemigo.sala_actual != self.jugador.sala_actual:
            raise AccionInvalida(f"{enemigo.nombre} no está en esta sala")

        self._empezar_accion("atacar")

        danio = self._danio(self.jugador.ataque_total(), enemigo.defensa)

        self._avisar(
            f"Atacas a {self._nombre(enemigo)} y causas {danio} de daño."
            )
        
        self._herir_enemigo(enemigo, danio)

        self._terminar_accion(COSTO_ATACAR)
        return danio

    # ---------------------------------------------------------
    # Objetos (§2.7, §4.5). La posición actual del inventario (lo que el
    # jugador "está viendo") se mueve con inventario.avanzar/retroceder:
    # eso no es una acción y no gasta tiempo.
    # ---------------------------------------------------------

    def recoger(self, posicion):
        """Recoge el objeto del suelo en esa posición. Costo 25."""
        self._verificar_que_se_puede_actuar()

        sala = self.sala_actual()
        inventario = self.jugador.inventario

        if not isinstance(posicion, int) or not 0 <= posicion < sala.cantidad_objetos():
            raise AccionInvalida("No hay ningún objeto en esa posición del suelo")

        if inventario.esta_lleno():
            raise AccionInvalida("El inventario está lleno: suelta algo primero")

        ficha = self._fichas(sala.objeto_en(posicion))

        if ficha is None:
            raise ValueError(f"No se conoce la ficha de {sala.objeto_en(posicion)}")

        self._empezar_accion("recoger")

        contexto = inventario.recoger_desde_sala(sala, posicion, ficha)
        self._avisar(
            f"Recoges {ficha.get('nombre', ficha.get('id'))}."
        )
        self._anotar(Cambio.de_operacion(
            "inventario", inventario, "deshacer_recogida", contexto
        ))

        self._terminar_accion(COSTO_RECOGER)
        return ficha

    def soltar(self):
        """Suelta en el suelo el objeto que se está viendo. Costo 25."""
        self._verificar_que_se_puede_actuar()

        inventario = self.jugador.inventario

        if inventario.actual() is None:
            raise AccionInvalida("No tienes nada que soltar")

        self._empezar_accion("soltar")

        contexto = inventario.soltar_en_sala(self.sala_actual())

        objeto_soltado = contexto.contexto_inventario.objeto
        self._avisar(
            f"Sueltas {objeto_soltado.get('nombre', objeto_soltado.get('id'))}."
        )

        self._anotar(Cambio.de_operacion(
            "inventario", inventario, "deshacer_soltar_en_sala", contexto
        ))

        self._terminar_accion(COSTO_SOLTAR)
        return contexto.contexto_inventario.objeto

    def equipar(self):
        """Equipa el arma o armadura que se está viendo. Costo 50."""
        self._verificar_que_se_puede_actuar()

        inventario = self.jugador.inventario
        objeto = inventario.actual()

        if objeto is None:
            raise AccionInvalida("No tienes nada que equipar")

        if objeto.get("clase") not in CLASES_EQUIPABLES:
            raise AccionInvalida(f"{objeto.get('nombre')} no se puede equipar")

        self._empezar_accion("equipar")

        contexto = inventario.equipar_actual_con_contexto()
        self._avisar(
            f"Equipas {objeto.get('nombre', objeto.get('id'))}."
        )
        self._anotar(Cambio.de_operacion(
            "inventario", inventario, "restaurar_equipado", contexto
        ))

        self._terminar_accion(COSTO_EQUIPAR)
        return objeto

    def usar(self):
        """Usa el objeto que se está viendo (§2.7). Costo 50. Se consume:
          - poción: cura (sin pasar de vida_max) y/o cambia la velocidad
            por un tiempo ("modificador_velocidad" durante "duracion");
          - antídoto: cancela el veneno (si no hay, se gasta igual);
          - antorcha: queda encendida "duracion" unidades.
        Armas y armaduras se equipan, y las llaves se usan al abrir."""
        self._verificar_que_se_puede_actuar()

        inventario = self.jugador.inventario
        objeto = inventario.actual()

        if objeto is None:
            raise AccionInvalida("No tienes nada que usar")

        clase = objeto.get("clase")
        nombre = objeto.get("nombre", objeto.get("id"))

        if clase in CLASES_EQUIPABLES:
            raise AccionInvalida(f"{nombre} se equipa, no se usa")

        if clase == "llave":
            raise AccionInvalida("Las llaves se usan al abrir una puerta")

        if clase not in ("pocion", "antidoto", "antorcha"):
            raise AccionInvalida(f"{nombre} no se puede usar")

        self._empezar_accion("usar")

        # Se consume: sale del inventario (el pergamino lo devuelve a su
        # mismo lugar con restaurar_soltado).
        contexto = inventario.soltar_actual_con_contexto()
        self._anotar(Cambio.de_operacion(
            "inventario", inventario, "restaurar_soltado", contexto
        ))

        if clase == "pocion":
            self._tomar_pocion(objeto)
        elif clase == "antidoto":
            self._quitar_veneno()
        else:
            self._encender_antorcha(objeto["duracion"])

        self._avisar(f"Usas {nombre}.")

        self._terminar_accion(COSTO_USAR)
        return objeto

    def recoger_pergamino(self):
        """Recoge un pergamino del suelo. Costo 25. La acción (su tiempo y
        lo que pase después) sí se puede deshacer; el pergamino recogido NO
        (§2.11, paso 3.3): por eso aquí no se anota nada de él."""
        self._verificar_que_se_puede_actuar()

        if self.sala_actual().cantidad_pergaminos() == 0:
            raise AccionInvalida("No hay pergaminos en el suelo")

        if self.jugador.inventario.esta_lleno():
            raise AccionInvalida("El inventario está lleno: suelta algo primero")

        self._empezar_accion("recoger pergamino")
        self.jugador.inventario.recoger_pergamino_de(self.sala_actual())
        self._avisar("Recoges un pergamino.")
        self._terminar_accion(COSTO_RECOGER)

    def soltar_pergamino(self):
        """Deja un pergamino en el suelo. Costo 25. Igual que al recogerlo:
        el pergamino soltado no se deshace (§2.11)."""
        self._verificar_que_se_puede_actuar()

        if not self.jugador.inventario.tiene_pergamino():
            raise AccionInvalida("No tienes pergaminos")

        self._empezar_accion("soltar pergamino")
        self.jugador.inventario.soltar_pergamino_en(self.sala_actual())
        self._avisar("Sueltas un pergamino.")
        self._terminar_accion(COSTO_SOLTAR)

    # ---------------------------------------------------------
    # Puertas (§2.5)
    # ---------------------------------------------------------

    def abrir(self, direccion):
        """Abre la puerta cerrada en esa dirección. Costo 50. Si tiene
        cerradura, hace falta un objeto del inventario cuyo id sea el de su
        llave; la llave no se consume. Abrir y atravesar son dos acciones
        distintas: después hay que mover."""
        self._verificar_que_se_puede_actuar()

        puerta = self.sala_actual().obtener_puerta(direccion)

        if puerta is None:
            raise AccionInvalida(f"No hay salida hacia {direccion!r}")

        if not puerta.esta_cerrada():
            raise AccionInvalida("Esa puerta ya está abierta")

        if puerta.requiere_llave() and self.jugador.inventario.buscar_por_id(puerta.llave) is None:
            raise AccionInvalida("Está cerrada con llave y no tienes la llave")

        self._empezar_accion("abrir")

        # La puerta es UNA para las dos salas (EstadoPuerta compartido):
        # abrirla desde aquí la abre también desde el otro lado.
        self._anotar(Cambio.de_atributo("puerta", puerta, "cerrada", True))
        puerta.abrir()
        self._avisar(f"Abres la puerta hacia {direccion}.")

        if self._es_puerta_de_salida(puerta):
            self._anotar(Cambio.de_atributo(
                "salida", self, "puerta_de_salida_abierta", self.puerta_de_salida_abierta
            ))
            self.puerta_de_salida_abierta = True

        # §2.5: si declara cierre automático, se programa su cierre.
        if puerta.cierre_automatico is not None:
            self._programar_evento(
                self.reloj + puerta.cierre_automatico, CIERRE_PUERTA, puerta
            )

        self._terminar_accion(COSTO_ABRIR)

    def usar_pergamino(self):
        """Deshace la última acción del jugador y todo lo que pasó después
        (§2.11). No consume tiempo ni es una acción: no abre nada en el
        historial. Devuelve False si no se pudo (sin pergaminos, sin
        acciones que deshacer, o la partida ya terminó)."""
        # Si el jugador murió ya no hay "siguiente decisión" donde usarlo.
        if self.terminada:
            return False

        resultado = self.estado.usar_pergamino_retroceso()

        if resultado:
            self._avisar("Usas un pergamino y retrocedes una acción.")

        return resultado

    def _verificar_que_se_puede_actuar(self):
        if not self.iniciada:
            raise RuntimeError("Primero hay que iniciar la partida")

        if self.terminada:
            raise RuntimeError("La partida ya terminó")

    def _empezar_accion(self, nombre):
        self.estado.historial.registrar(RegistroAccion(nombre))
        self._azar_anotado = False

        self._anotar(Cambio.de_atributo(
            "acciones", self, "acciones_jugador", self.acciones_jugador
        ))
        self.acciones_jugador += 1

    def _terminar_accion(self, costo):
        # Apéndice B: con cada acción se refresca el rastro de la sala
        # donde queda el jugador (§2.9: "el instante en que estuvo allí por
        # última vez"). Al moverse, esa es la sala destino; la que deja
        # conserva el instante de su última acción allí.
        self._refrescar_rastro()

        # §2.3: tiempo_siguiente = reloj_actual + intervalo.
        tiempo = self.reloj + self.jugador.intervalo(costo)
        self._programar(self.jugador, tiempo, TURNO_JUGADOR)

        self._correr_hasta_el_jugador()

    # =========================================================
    # EL BUCLE (§2.3)
    # =========================================================

    def _correr_hasta_el_jugador(self):
        """Saca eventos en orden (menor tiempo, luego menor secuencia) y
        los ejecuta, hasta que sale un turno del jugador: ahí se detiene
        para que decida."""
        while not self.terminada:
            evento = self.agenda.siguiente()

            if evento is None:
                # Nunca debería pasar: el jugador siempre tiene un turno
                # programado mientras la partida sigue.
                raise RuntimeError("La agenda se quedó sin eventos")

            # Para deshacer: el evento vuelve a la agenda como pendiente.
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", evento
            ))

            # Paso 2 del §2.3: avanzar el reloj a ese instante.
            self.estado.avanzar_reloj(evento.tiempo - self.reloj)

            if evento.tipo == TURNO_JUGADOR:
                return

            self._ejecutar(evento)

    def _ejecutar(self, evento):
        tipo = evento.tipo

        if tipo == TURNO_ENEMIGO:
            self._turno_enemigo(evento.objetivo)
        elif tipo == CIERRE_PUERTA:
            self._cerrar_puerta(evento.objetivo)
        elif tipo == PULSO_VENENO:
            self._pulso_de_veneno(evento.objetivo)
        elif tipo == FIN_VELOCIDAD:
            self._terminar_velocidad(evento.objetivo)
        elif tipo == APAGAR_ANTORCHA:
            self._apagar_antorcha(evento.objetivo)
        elif tipo == REGENERACION:
            self._regenerar(evento.objetivo)
        elif tipo == REARME_TRAMPA:
            self._rearmar_trampa(evento.objetivo)
        else:
            raise ValueError(f"Tipo de evento desconocido: {evento.tipo}")

    def _turno_enemigo(self, enemigo):
        if not enemigo.esta_vivo():
            return                       # (no pasa: al morir se cancela su turno)

        # §2.8: primero, si comparte sala con el jugador, ataca y no se mueve.
        if enemigo.sala_actual == self.jugador.sala_actual:
            danio = self._danio(enemigo.ataque, self.jugador.defensa_total())

            self._avisar(
                f"{self._nombre(enemigo)} te ataca y causa {danio} de daño."
            )

            self._herir_jugador(danio)
        else:
            # Si no, su comportamiento.
            self._aplicar_comportamiento(enemigo)

        if self.terminada:
            return                       # el jugador murió: se acabó

        # Atacar, moverse o esperar cuestan 100 (§2.8).
        tiempo = self.reloj + enemigo.intervalo(COSTO_ATACAR)
        self._programar(enemigo, tiempo, TURNO_ENEMIGO)

    def _cerrar_puerta(self, puerta):
        """Evento de cierre automático (§2.5): la puerta vuelve a cerrarse
        (desde los dos lados). Abrirla otra vez pide la llave de nuevo."""
        if puerta.esta_cerrada():
            return

        self._anotar(Cambio.de_atributo("puerta", puerta, "cerrada", False))
        puerta.cerrar()
        self._avisar("Una puerta se cierra automáticamente.")

    # =========================================================
    # EFECTOS TEMPORALES (§2.10)
    # =========================================================
    # Cada efecto activo es un Efecto que apunta a su próximo evento: así
    # se cancela en O(1) (borrado perezoso), sin recorrer la agenda.

    def _cancelar_efecto(self, efecto):
        if self.agenda.cancelar(efecto.evento):
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", efecto.evento
            ))

    def _tomar_pocion(self, ficha):
        cura = ficha.get("cura")

        if cura:
            self._anotar(Cambio.de_atributo("vida", self.jugador, "vida", self.jugador.vida))
            self.jugador.curar(cura)          # nunca pasa de vida_max (§2.2)
            self._avisar(f"Recuperas vida (ahora {self.jugador.vida}).")

        modificador = ficha.get("modificador_velocidad")
        duracion = ficha.get("duracion")

        if modificador and duracion:
            self._empezar_velocidad(modificador, duracion)

    # --- Cambio de velocidad ---

    def _empezar_velocidad(self, modificador, duracion):
        """La velocidad cambia YA y vuelve a la normal en reloj + duracion.
        El Efecto guarda cuánto cambió de verdad (nunca baja de 1), para
        devolver exactamente eso al final."""
        anterior = self.jugador.velocidad
        nueva = max(1, anterior + modificador)

        efecto = Efecto(VELOCIDAD, valor=nueva - anterior, hasta=self.reloj + duracion)
        self._cambiar_velocidad(self.jugador, nueva)
        self._avisar(f"Tu velocidad cambia de {anterior} a {nueva}.")
        efecto.evento = self._programar_evento(efecto.hasta, FIN_VELOCIDAD, efecto)

    def _terminar_velocidad(self, efecto):
        self._cambiar_velocidad(self.jugador, max(1, self.jugador.velocidad - efecto.valor))
        self._avisar(f"El efecto de velocidad termina. Velocidad actual: {self.jugador.velocidad}.")

    def _cambiar_velocidad(self, actor, nueva):
        """§2.3: si el actor ya tiene su próxima acción programada, lo que le
        falta se escala (Agenda.reprogramar_por_velocidad: cancela el evento
        y programa otro, con número de secuencia nuevo). Todo se anota."""
        evento_anterior = actor.evento_siguiente

        self._anotar(Cambio.de_atributo("velocidad", actor, "velocidad", actor.velocidad))
        self._anotar(Cambio.de_atributo("evento", actor, "evento_siguiente", evento_anterior))

        evento_nuevo = self.agenda.reprogramar_por_velocidad(actor, self.reloj, nueva)

        if evento_nuevo is not None:
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", evento_anterior
            ))
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "deshacer_programacion", evento_nuevo
            ))

    # --- Veneno ---

    def _envenenar(self, danio):
        """Hace 'danio' cada 80, durante 400 desde ahora (el pulso que cae
        justo en t+400 todavía cuenta: 5 pulsos). Un veneno nuevo reemplaza
        al que hubiera (no se acumulan)."""
        if self.veneno is not None:
            self._cancelar_efecto(self.veneno)

        efecto = Efecto(VENENO, valor=danio, hasta=self.reloj + DURACION_VENENO)

        self._anotar(Cambio.de_atributo("veneno", self, "veneno", self.veneno))
        self.veneno = efecto
        self._avisar(f"Has sido envenenado. Daño por pulso: {danio}.")
        efecto.evento = self._programar_evento(
            self.reloj + INTERVALO_VENENO, PULSO_VENENO, efecto
        )

    def _pulso_de_veneno(self, efecto):
        if efecto is not self.veneno:
            return                       # (no pasa: el antídoto cancela su evento)

        self._avisar(f"El veneno te causa {efecto.valor} de daño.")
        self._herir_jugador(efecto.valor)

        if self.terminada:
            return

        siguiente = self.reloj + INTERVALO_VENENO

        if siguiente <= efecto.hasta:
            self._anotar(Cambio.de_atributo("efecto", efecto, "evento", efecto.evento))
            efecto.evento = self._programar_evento(siguiente, PULSO_VENENO, efecto)
        else:
            self._anotar(Cambio.de_atributo("veneno", self, "veneno", efecto))
            self.veneno = None

    def _quitar_veneno(self):
        """Antídoto: cancela los pulsos que faltan (§2.10)."""
        if self.veneno is None:
            return

        self._cancelar_efecto(self.veneno)
        self._anotar(Cambio.de_atributo("veneno", self, "veneno", self.veneno))
        self.veneno = None
        self._avisar("El veneno ha sido eliminado.")

    # --- Antorcha ---

    def _encender_antorcha(self, duracion):
        """Queda encendida 'duracion' unidades. Si ya había una encendida,
        la nueva la reemplaza (cuenta desde ahora)."""
        if self.antorcha is not None:
            self._cancelar_efecto(self.antorcha)

        efecto = Efecto(ANTORCHA, hasta=self.reloj + duracion)

        self._anotar(Cambio.de_atributo("antorcha", self, "antorcha", self.antorcha))
        self.antorcha = efecto
        self._avisar("Enciendes una antorcha.")
        efecto.evento = self._programar_evento(efecto.hasta, APAGAR_ANTORCHA, efecto)

    def _apagar_antorcha(self, efecto):
        if efecto is not self.antorcha:
            return

        self._anotar(Cambio.de_atributo("antorcha", self, "antorcha", efecto))
        self.antorcha = None
        self._avisar("La antorcha se ha apagado.")

    # --- Regeneración de enemigos ---

    def _programar_regeneracion(self, enemigo):
        self._anotar(Cambio.de_atributo(
            "regeneracion", enemigo, "evento_regeneracion", enemigo.evento_regeneracion
        ))
        enemigo.evento_regeneracion = self._programar_evento(
            self.reloj + INTERVALO_REGENERACION, REGENERACION, enemigo
        )

    def _regenerar(self, enemigo):
        if not enemigo.esta_vivo():
            return                       # (no pasa: al morir se cancela)

        self._anotar(Cambio.de_atributo("vida", enemigo, "vida", enemigo.vida))
        enemigo.curar(enemigo.regeneracion)       # nunca pasa de vida_max
        self._avisar(f"{self._nombre(enemigo)} regenera vida.")
        self._programar_regeneracion(enemigo)

    # --- Trampas ---

    def _activar_trampas(self, sala):
        """Cada trampa ARMADA de la sala se activa: hace el daño de su ficha
        (sin defensa ni dado: no es un ataque entre actores), queda
        desarmada y programa su rearme (300, o el "rearme" de la ficha).
        Si la ficha trae "veneno", además envenena con ese daño por pulso."""
        for i in range(sala.cantidad_trampas()):
            trampa = sala.trampa_en(i)

            if not trampa.esta_activa():
                continue

            ficha = self._fichas(trampa.tipo)

            self._anotar(Cambio.de_atributo("trampa", trampa, "activa", True))
            trampa.desactivar()
            self._avisar(
                f"Se activa una trampa y recibes {ficha.get('daño', 0)} de daño."
            )

            rearme = ficha.get("rearme")

            if rearme is None:
                rearme = REARME_POR_DEFECTO

            self._programar_evento(self.reloj + rearme, REARME_TRAMPA, trampa)

            if ficha.get("veneno"):
                self._envenenar(ficha["veneno"])

            self._herir_jugador(ficha.get("daño", 0))

            if self.terminada:
                return

    def _rearmar_trampa(self, trampa):
        if trampa.esta_activa():
            return

        self._anotar(Cambio.de_atributo("trampa", trampa, "activa", False))
        trampa.activar()
        self._avisar("Una trampa vuelve a estar armada.")

    # =========================================================
    # COMPORTAMIENTOS (§2.8)
    # =========================================================

    def _aplicar_comportamiento(self, enemigo):
        """Lo que hace un enemigo cuando el jugador NO está en su sala.
        Moverse o esperar cuestan lo mismo (100), así que solo hay que
        decidir a dónde va; None = espera."""
        sala = self.mapa.obtener_sala(enemigo.sala_actual)

        if enemigo.comportamiento == ERRANTE:
            destino = self._destino_errante(sala)
        elif enemigo.comportamiento == RASTREADOR:
            destino = sala_con_rastro_mas_fresco(sala, self.reloj)
        else:
            destino = None           # guardián: nunca deja su sala

        if destino is not None:
            self._mover_enemigo(enemigo, sala, destino)

    def _destino_errante(self, sala):
        """Una salida abierta al azar (§2.8). Las salidas siempre están en
        el mismo orden (N, S, E, O) y el dado es el de la semilla: misma
        semilla, mismo camino. Si no hay salidas abiertas, espera y no se
        tira el dado."""
        posibles = Vector()
        puertas = sala.puertas(solo_abiertas=True)

        for i in range(len(puertas)):
            vecina = puertas.obtener(i).sala_destino_ref

            if vecina is not None:
                posibles.agregar(vecina)

        if len(posibles) == 0:
            return None

        return posibles.obtener(self._tirar_dado(0, len(posibles) - 1))

    def _mover_enemigo(self, enemigo, origen, destino):
        """El enemigo pasa de una sala a otra. No hay ataque gratis al
        entrar (§2.5): si queda con el jugador, ataca en su PRÓXIMO turno."""
        posicion = origen.quitar_enemigo(enemigo)
        self._anotar(Cambio.de_operacion(
            "sala", _EnemigoQuitado(origen, enemigo, posicion), "restaurar"
        ))

        destino.agregar_enemigo(enemigo)
        self._anotar(Cambio.de_operacion("sala", destino, "quitar_enemigo", enemigo))

        if destino.id == self.jugador.sala_actual:
            self._avisar(f"{self._nombre(enemigo)} entra en la sala.")

        elif origen.id == self.jugador.sala_actual:
            self._avisar(f"{self._nombre(enemigo)} se va.")

    # =========================================================
    # COMBATE (§2.6)
    # =========================================================

    def _danio(self, ataque, defensa):
        """daño = max(1, ataque + azar.randint(0, 4) - defensa)"""
        return max(1, ataque + self._tirar_dado(0, 4) - defensa)

    def _tirar_dado(self, minimo, maximo):
        """Todo el azar del juego pasa por aquí.

        El generador también es parte del estado (§2.11: "cualquier otro
        dato modificado"). La PRIMERA vez que se usa en el intervalo de una
        acción se anota cómo estaba; el pergamino lo deja así y repetir la
        acción da el mismo resultado (no sirve para "volver a tirar el
        dado"). Si en el intervalo nadie usa el azar, no se guarda nada."""
        if not self._azar_anotado:
            self._anotar(Cambio.de_operacion(
                "azar", self.azar, "setstate", self.azar.getstate()
            ))
            self._azar_anotado = True

        return self.azar.randint(minimo, maximo)

    def _herir_jugador(self, danio):
        self._anotar(Cambio.de_atributo("vida", self.jugador, "vida", self.jugador.vida))
        self.jugador.recibir_danio(danio)

        # §2.12: derrota. No se anota para deshacer: el jugador ya no tendrá
        # otra decisión, y el pergamino solo se usa en una decisión.
        if not self.jugador.esta_vivo():
            self.terminada = True
            self.resultado = "derrota"
            self._avisar("Has muerto. Fin de la partida.")

    def _herir_enemigo(self, enemigo, danio):
        self._anotar(Cambio.de_atributo("vida", enemigo, "vida", enemigo.vida))
        enemigo.recibir_danio(danio)

        if not enemigo.esta_vivo():
            self._matar_enemigo(enemigo)

    def _matar_enemigo(self, enemigo):
        """§2.6: muere inmediatamente, deja de ejecutar eventos y suelta
        sus objetos en el suelo de la sala."""

        self._avisar(f"{self._nombre(enemigo)} ha muerto.")

        # 1. Su próximo turno se cancela (borrado perezoso, §4.1).
        evento = enemigo.evento_siguiente

        if self.agenda.cancelar(evento):
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", evento
            ))

        # Y su regeneración, si tenía.
        if self.agenda.cancelar(enemigo.evento_regeneracion):
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", enemigo.evento_regeneracion
            ))

        # 2. Sale de la sala (así no aparece para atacar).
        sala = self.mapa.obtener_sala(enemigo.sala_actual)
        posicion = sala.quitar_enemigo(enemigo)
        self._anotar(Cambio.de_operacion(
            "sala", _EnemigoQuitado(sala, enemigo, posicion), "restaurar"
        ))

        # 3. Cuenta para el puntaje.
        self._anotar(Cambio.de_atributo(
            "derrotados", self, "enemigos_derrotados", self.enemigos_derrotados
        ))
        self.enemigos_derrotados += 1

        # 4. Suelta sus objetos.
        for id_objeto in enemigo.objetos_que_suelta():
            self._dejar_en_el_suelo(sala, id_objeto)

    
    def _dejar_en_el_suelo(self, sala, id_objeto):
        if self._es_pergamino(id_objeto):
            # Va al contador del suelo (paso 3.3).
            sala.agregar_pergamino()
            self._anotar(Cambio.de_operacion(
                "suelo", self, "_retirar_pergamino_soltado", sala
            ))

            self._avisar("Cae al suelo: pergamino.")
            return

        posicion = sala.cantidad_objetos()
        sala.agregar_objeto(id_objeto)
        self._anotar(Cambio.de_operacion(
            "suelo", sala, "quitar_objeto", posicion
        ))

        ficha = self._fichas(id_objeto)
        nombre = ficha.get("nombre", id_objeto) if ficha is not None else id_objeto
        self._avisar(f"Cae al suelo: {nombre}.")


    def _retirar_pergamino_soltado(self, sala):
        # Si el jugador ya lo recogió (eso no se deshace, §2.11), no queda
        # nada que quitar del suelo.
        if sala.cantidad_pergaminos() > 0:
            sala.quitar_pergamino()

    # =========================================================
    # AYUDANTES
    # =========================================================
    
    def _avisar(self, texto):
        """Registra un mensaje sin modificar el estado reversible."""
        self.bitacora.agregar(self.reloj, texto)

    def _nombre(self, enemigo):
        """Identifica al enemigo por nombre e ID de instancia."""
        return f"{enemigo.nombre} ({enemigo.id_instancia})"

    def _anotar(self, cambio):
        """Anota un cambio en la acción abierta (si hay una)."""
        self.estado.historial.registrar_cambio(cambio)

    def _programar_evento(self, tiempo, tipo, objetivo):
        """Programa un evento cualquiera y anota cómo deshacerlo (que nunca
        ocurra)."""
        evento = self.agenda.programar(tiempo, tipo, objetivo)

        self._anotar(Cambio.de_operacion(
            "agenda", self.agenda, "deshacer_programacion", evento
        ))
        return evento

    def _programar(self, actor, tiempo, tipo):
        """Programa el próximo turno de un actor, y anota cómo deshacerlo:
        cancelar ese evento y devolverle al actor el evento que tenía."""
        evento = self._programar_evento(tiempo, tipo, actor)

        self._anotar(Cambio.de_atributo(
            "evento", actor, "evento_siguiente", actor.evento_siguiente
        ))

        actor.asignar_evento(evento)
        return evento

    def _poner_jugador_en(self, sala):
        """El jugador entra a la sala, con todo lo que eso implica. Cada
        cambio se anota para que el pergamino lo pueda deshacer.

        No usa Jugador.mover_a: esa guarda además el recorrido completo en
        la clase Rastro vieja, que crece con cada paso. Lo que pide §2.9
        es solo el último instante en cada sala, y eso lo tiene la Sala
        (es lo que lee el rastreador)."""
        self._anotar(Cambio.de_atributo(
            "sala", self.jugador, "sala_actual", self.jugador.sala_actual
        ))
        self.jugador.sala_actual = sala.id

        # §2.9: la sala recibe el tiempo actual como rastro.
        self._anotar(Cambio.de_atributo(
            "rastro", sala, "ultimo_rastro", sala.ultimo_rastro
        ))
        sala.registrar_rastro(self.reloj)

        # Paso 3.3: los pergaminos del suelo pasan a su contador. No hace
        # falta anotarlo: es solo otra forma de guardar lo mismo, y
        # apartar_pergaminos ya no hace nada la segunda vez.
        sala.apartar_pergaminos(self._es_pergamino)

        # §2.4: entrar activa a los dormidos. Los que ya estaban activos
        # no se tocan (entrar no reinicia sus tiempos, §2.13).
        self._activar_enemigos(sala)

    def _refrescar_rastro(self):
        sala = self.sala_actual()

        if sala.ultimo_rastro != self.reloj:
            self._anotar(Cambio.de_atributo(
                "rastro", sala, "ultimo_rastro", sala.ultimo_rastro
            ))
            sala.registrar_rastro(self.reloj)

    def _es_puerta_de_salida(self, puerta):
        """La puerta que da acceso a la sala de salida, con su llave. Puede
        abrirse desde afuera (lleva a la salida) o desde adentro."""
        if self._id_sala_salida is None or self._llave_salida is None:
            return False

        if puerta.llave != self._llave_salida:
            return False

        return (puerta.sala_destino == self._id_sala_salida
                or self.jugador.sala_actual == self._id_sala_salida)

    def _es_victoria(self, sala):
        return sala.id == self._id_sala_salida and self.puerta_de_salida_abierta

    def _es_pergamino(self, id_objeto):
        ficha = self._fichas(id_objeto)
        return ficha is not None and ficha.get("clase") == CLASE_PERGAMINO

    def _activar_enemigos(self, sala):
        """§2.4: los dormidos de la sala se activan, en orden de id de
        instancia, y su primera acción se programa como una de costo 100."""
        dormidos = sala.enemigos_dormidos()

        for i in range(len(dormidos)):
            enemigo = dormidos.obtener(i)

            enemigo.activar(self._fichas(enemigo.tipo))
            self._avisar(f"{self._nombre(enemigo)} despierta.")
            self._anotar(Cambio.de_operacion("activar", enemigo, "desactivar"))

            tiempo = self.reloj + enemigo.intervalo(COSTO_ESPERAR)
            self._programar(enemigo, tiempo, TURNO_ENEMIGO)

            # §2.10: si declara regeneración, recupera vida cada 200.
            if enemigo.regeneracion > 0:
                self._programar_regeneracion(enemigo)