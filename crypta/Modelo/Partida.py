import random

from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Efecto import ANTORCHA, VELOCIDAD, VENENO, Efecto
from crypta.Modelo.EstadoJuego import EstadoJuego
from crypta.Modelo.Historial import RegistroAccion
from crypta.Modelo.Inventario import CLASE_PERGAMINO, CLASES_EQUIPABLES
from crypta.Modelo.Enemigo import CAZADOR
from crypta.Modelo.Perseguidor import ATACAR, MOVER, Perseguidor
from crypta.Modelo.Rastreador import salida_con_rastro_mas_fresco
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Bitacora import Bitacora


COSTO_ATACAR = 100
COSTO_ESPERAR = 100
COSTO_USAR = 50
COSTO_EQUIPAR = 50
COSTO_ABRIR = 50
COSTO_RECOGER = 25
COSTO_SOLTAR = 25

ERRANTE = "errante"
RASTREADOR = "rastreador"

INTERVALO_VENENO = 80       
DURACION_VENENO = 400       
INTERVALO_REGENERACION = 200
REARME_POR_DEFECTO = 300

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
    def __init__(self, mapa, jugador, id_sala_inicial, fichas, semilla=0,
                 id_sala_salida=None, llave_salida=None):
        self.mapa = mapa
        self.jugador = jugador
        self.estado = EstadoJuego(jugador.inventario)

        self.semilla = semilla
        self.azar = random.Random(semilla)

        self._fichas = fichas
        self._id_sala_inicial = id_sala_inicial

        self._id_sala_salida = id_sala_salida
        self._llave_salida = llave_salida
        self.puerta_de_salida_abierta = False

        self._azar_anotado = False

        self.iniciada = False
        self.terminada = False
        self.resultado = None

        self.acciones_jugador = 0
        self.enemigos_derrotados = 0

        self.veneno = None
        self.antorcha = None

        self.bitacora = Bitacora()

        # Las reglas del cazador y su búsqueda compartida (FR-013 a FR-019).
        # Se crea con el primer turno de un cazador: una partida sin
        # cazadores no paga nada. No es estado del juego (research D6).
        self._perseguidor = None

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
        sala = self.sala_actual()
        fichas = Vector()

        for i in range(sala.cantidad_objetos()):
            fichas.agregar(self._fichas(sala.objeto_en(i)))

        return fichas

    def iniciar(self):
        if self.iniciada:
            raise RuntimeError("La partida ya se inició")

        sala = self.mapa.obtener_sala(self._id_sala_inicial)

        if sala is None:
            raise ValueError(f"No existe la sala inicial {self._id_sala_inicial}")

        if not sala.contenido_cargado():
            raise RuntimeError(
                f"Falta el contenido de la sala inicial {sala.id}: "
                f"el controlador debe cargarlo antes de iniciar"
            )

        self.iniciada = True

        self._avisar(f"Entras en {sala.nombre}.")
        self._poner_jugador_en(sala)
        self._programar(self.jugador, 0, TURNO_JUGADOR)

        self._correr_hasta_el_jugador()

    def esperar(self):
        self._verificar_que_se_puede_actuar()
        self._empezar_accion("esperar")
        self._avisar("Esperas.")
        self._terminar_accion(COSTO_ESPERAR)

    def destino_de(self, direccion):
        puerta = self.sala_actual().obtener_puerta(direccion)

        if puerta is None:
            return None

        return puerta.sala_destino

    def mover(self, direccion):
        self._verificar_que_se_puede_actuar()

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

        self._empezar_accion("mover")
        self._avisar(f"Entras en {destino.nombre}.")
        self._poner_jugador_en(destino)

        self._activar_trampas(destino)

        if not self.terminada and self._es_victoria(destino):
            self.terminada = True
            self.resultado = "victoria"
            self._avisar("¡Escapaste de la cripta!")

        # Moverse tarda el costo de la salida (FR-003, FR-004).
        self._terminar_accion(puerta.costo)

        return destino

    def atacar(self, enemigo):
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


    def recoger(self, posicion):
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
        self._verificar_que_se_puede_actuar()

        if not self.jugador.inventario.tiene_pergamino():
            raise AccionInvalida("No tienes pergaminos")

        self._empezar_accion("soltar pergamino")
        self.jugador.inventario.soltar_pergamino_en(self.sala_actual())
        self._avisar("Sueltas un pergamino.")
        self._terminar_accion(COSTO_SOLTAR)


    def abrir(self, direccion):
        self._verificar_que_se_puede_actuar()

        puerta = self.sala_actual().obtener_puerta(direccion)

        if puerta is None:
            raise AccionInvalida(f"No hay salida hacia {direccion!r}")

        if not puerta.esta_cerrada():
            raise AccionInvalida("Esa puerta ya está abierta")

        if puerta.requiere_llave() and self.jugador.inventario.buscar_por_id(puerta.llave) is None:
            raise AccionInvalida("Está cerrada con llave y no tienes la llave")

        self._empezar_accion("abrir")

        self._anotar(Cambio.de_atributo("puerta", puerta, "cerrada", True))
        puerta.abrir()
        self._avisar(f"Abres la puerta hacia {direccion}.")

        if self._es_puerta_de_salida(puerta):
            self._anotar(Cambio.de_atributo(
                "salida", self, "puerta_de_salida_abierta", self.puerta_de_salida_abierta
            ))
            self.puerta_de_salida_abierta = True

        if puerta.cierre_automatico is not None:
            self._programar_evento(
                self.reloj + puerta.cierre_automatico, CIERRE_PUERTA, puerta
            )

        self._terminar_accion(COSTO_ABRIR)

    def usar_pergamino(self):
        if self.terminada:
            return False

        resultado = self.estado.usar_pergamino_retroceso()

        # Las búsquedas del cazador no entran al historial (research D6):
        # después de revertir se invalidan. No haría falta (las puertas
        # restauradas avisan y la sala del jugador se compara en cada
        # decisión), pero cuesta una búsqueda y se hace por seguridad
        # (FR-020).
        if resultado and self._perseguidor is not None:
            self._perseguidor.invalidar()

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

        self._refrescar_rastro()
        tiempo = self.reloj + self.jugador.intervalo(costo)
        self._programar(self.jugador, tiempo, TURNO_JUGADOR)

        self._correr_hasta_el_jugador()


    def _correr_hasta_el_jugador(self):
        while not self.terminada:
            evento = self.agenda.siguiente()

            if evento is None:
                raise RuntimeError("La agenda se quedó sin eventos")

            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", evento
            ))

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
            return

        if enemigo.comportamiento == CAZADOR:
            costo = self._turno_cazador(enemigo)
        elif enemigo.sala_actual == self.jugador.sala_actual:
            self._atacar_al_jugador(enemigo)
            costo = COSTO_ATACAR
        else:
            # Si no, su comportamiento: si se movió, tarda el costo de la
            # salida; si no, esperó (FR-003, FR-004, FR-005).
            puerta = self._aplicar_comportamiento(enemigo)
            costo = COSTO_ESPERAR if puerta is None else puerta.costo

        if self.terminada:
            return                       # el jugador murió: se acabó

        tiempo = self.reloj + enemigo.intervalo(costo)
        self._programar(enemigo, tiempo, TURNO_ENEMIGO)

    def _atacar_al_jugador(self, enemigo):
        danio = self._danio(enemigo.ataque, self.jugador.defensa_total())

        self._avisar(
            f"{self._nombre(enemigo)} te ataca y causa {danio} de daño."
        )

        self._herir_jugador(danio)

    def perseguidor(self):
        """El Perseguidor de esta partida; lo crea la primera vez y lo
        registra como observador de cada salida."""
        if self._perseguidor is None:
            self._perseguidor = Perseguidor(
                self.mapa, COSTO_ATACAR, COSTO_ESPERAR)
            self._perseguidor.observar_puertas()

        return self._perseguidor

    def _turno_cazador(self, cazador):
        """El cazador pide su Decision y la cumple: ataca con el daño de P1
        (que sí usa el azar), se mueve con los mismos Cambio de siempre
        (FR-020) o espera. Devuelve el costo de la acción (FR-004, FR-013,
        FR-016)."""
        decision = self.perseguidor().decidir(cazador, self.sala_actual())

        if decision.accion == ATACAR:
            self._atacar_al_jugador(cazador)
        elif decision.accion == MOVER:
            origen = self.mapa.obtener_sala(cazador.sala_actual)
            self._mover_enemigo(cazador, origen,
                                decision.puerta.sala_destino_ref)

        return decision.costo

    def _cerrar_puerta(self, puerta):
        if puerta.esta_cerrada():
            return

        self._anotar(Cambio.de_atributo("puerta", puerta, "cerrada", False))
        puerta.cerrar()
        self._avisar("Una puerta se cierra automáticamente.")


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


    def _empezar_velocidad(self, modificador, duracion):
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


    def _envenenar(self, danio):
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
        if self.veneno is None:
            return

        self._cancelar_efecto(self.veneno)
        self._anotar(Cambio.de_atributo("veneno", self, "veneno", self.veneno))
        self.veneno = None
        self._avisar("El veneno ha sido eliminado.")


    def _encender_antorcha(self, duracion):
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


    def _activar_trampas(self, sala):
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


    def _aplicar_comportamiento(self, enemigo):
        """Mueve al enemigo según su comportamiento y devuelve la salida que
        atravesó, o None si se quedó (FR-004, FR-006)."""
        sala = self.mapa.obtener_sala(enemigo.sala_actual)

        if enemigo.comportamiento == ERRANTE:
            puerta = self._destino_errante(sala)
        elif enemigo.comportamiento == RASTREADOR:
            puerta = salida_con_rastro_mas_fresco(sala, self.reloj)
        else:
            puerta = None

        if puerta is not None:
            self._mover_enemigo(enemigo, sala, puerta.sala_destino_ref)

        return puerta

    def _destino_errante(self, sala):
        """La salida abierta que elige el errante, al azar entre las que
        llevan a una sala, o None. Mismas opciones y mismas llamadas al azar
        que en P1 (FR-006); devuelve la puerta para que el movimiento tarde
        su costo."""
        posibles = Vector()
        puertas = sala.puertas(solo_abiertas=True)

        for i in range(len(puertas)):
            puerta = puertas.obtener(i)

            if puerta.sala_destino_ref is not None:
                posibles.agregar(puerta)

        if len(posibles) == 0:
            return None

        return posibles.obtener(self._tirar_dado(0, len(posibles) - 1))

    def _mover_enemigo(self, enemigo, origen, destino):
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


    def _danio(self, ataque, defensa):
        return max(1, ataque + self._tirar_dado(0, 4) - defensa)

    def _tirar_dado(self, minimo, maximo):
        if not self._azar_anotado:
            self._anotar(Cambio.de_operacion(
                "azar", self.azar, "setstate", self.azar.getstate()
            ))
            self._azar_anotado = True

        return self.azar.randint(minimo, maximo)

    def _herir_jugador(self, danio):
        self._anotar(Cambio.de_atributo("vida", self.jugador, "vida", self.jugador.vida))
        self.jugador.recibir_danio(danio)

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

        self._avisar(f"{self._nombre(enemigo)} ha muerto.")

        evento = enemigo.evento_siguiente

        if self.agenda.cancelar(evento):
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", evento
            ))

        if self.agenda.cancelar(enemigo.evento_regeneracion):
            self._anotar(Cambio.de_operacion(
                "agenda", self.agenda, "restaurar_evento", enemigo.evento_regeneracion
            ))

        sala = self.mapa.obtener_sala(enemigo.sala_actual)
        posicion = sala.quitar_enemigo(enemigo)
        self._anotar(Cambio.de_operacion(
            "sala", _EnemigoQuitado(sala, enemigo, posicion), "restaurar"
        ))

        self._anotar(Cambio.de_atributo(
            "derrotados", self, "enemigos_derrotados", self.enemigos_derrotados
        ))
        self.enemigos_derrotados += 1

        for id_objeto in enemigo.objetos_que_suelta():
            self._dejar_en_el_suelo(sala, id_objeto)

    
    def _dejar_en_el_suelo(self, sala, id_objeto):
        if self._es_pergamino(id_objeto):
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
        if sala.cantidad_pergaminos() > 0:
            sala.quitar_pergamino()
    
    def _avisar(self, texto):
        self.bitacora.agregar(self.reloj, texto)

    def _nombre(self, enemigo):
        return f"{enemigo.nombre} ({enemigo.id_instancia})"

    def _anotar(self, cambio):
        self.estado.historial.registrar_cambio(cambio)

    def _programar_evento(self, tiempo, tipo, objetivo):
        evento = self.agenda.programar(tiempo, tipo, objetivo)

        self._anotar(Cambio.de_operacion(
            "agenda", self.agenda, "deshacer_programacion", evento
        ))
        return evento

    def _programar(self, actor, tiempo, tipo):
        evento = self._programar_evento(tiempo, tipo, actor)

        self._anotar(Cambio.de_atributo(
            "evento", actor, "evento_siguiente", actor.evento_siguiente
        ))

        actor.asignar_evento(evento)
        return evento

    def _poner_jugador_en(self, sala):
        self._anotar(Cambio.de_atributo(
            "sala", self.jugador, "sala_actual", self.jugador.sala_actual
        ))
        self.jugador.sala_actual = sala.id

        self._anotar(Cambio.de_atributo(
            "rastro", sala, "ultimo_rastro", sala.ultimo_rastro
        ))
        sala.registrar_rastro(self.reloj)

        sala.apartar_pergaminos(self._es_pergamino)

        self._activar_enemigos(sala)

    def _refrescar_rastro(self):
        sala = self.sala_actual()

        if sala.ultimo_rastro != self.reloj:
            self._anotar(Cambio.de_atributo(
                "rastro", sala, "ultimo_rastro", sala.ultimo_rastro
            ))
            sala.registrar_rastro(self.reloj)

    def _es_puerta_de_salida(self, puerta):
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
        dormidos = sala.enemigos_dormidos()

        for i in range(len(dormidos)):
            enemigo = dormidos.obtener(i)

            enemigo.activar(self._fichas(enemigo.tipo))
            self._avisar(f"{self._nombre(enemigo)} despierta.")
            self._anotar(Cambio.de_operacion("activar", enemigo, "desactivar"))

            tiempo = self.reloj + enemigo.intervalo(COSTO_ESPERAR)
            self._programar(enemigo, tiempo, TURNO_ENEMIGO)

            if enemigo.regeneracion > 0:
                self._programar_regeneracion(enemigo)