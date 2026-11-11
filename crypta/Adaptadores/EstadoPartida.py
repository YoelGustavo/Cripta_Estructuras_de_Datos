
from crypta.Adaptadores.RegistroPartida import Encabezado
from crypta.Modelo.DatosInvalidos import DatosInvalidos
from crypta.Modelo.Efecto import ANTORCHA, VELOCIDAD, VENENO, Efecto
from crypta.Modelo.Enemigo import Enemigo
from crypta.Modelo.Evento import Evento
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import (
    APAGAR_ANTORCHA, CIERRE_PUERTA, FIN_VELOCIDAD, PULSO_VENENO, REARME_TRAMPA,
    REGENERACION, TURNO_ENEMIGO, TURNO_JUGADOR, Partida,
)
from crypta.Modelo.Puerta import Puerta
from crypta.Modelo.Sala import DIRECCIONES, Sala
from crypta.Modelo.Trampa import Trampa
from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.Vector import Vector


TIPOS_DE_EVENTO = (TURNO_JUGADOR, TURNO_ENEMIGO, CIERRE_PUERTA, PULSO_VENENO,
                   FIN_VELOCIDAD, APAGAR_ANTORCHA, REGENERACION, REARME_TRAMPA)


class ErrorGuardado(Exception):
    """El archivo no es una partida guardada válida: de otro programa, de
    otra versión del formato, cortado o con datos que no cuadran."""


def revisar_antes_de_guardar(partida, encabezado):
    
    if not partida.iniciada:
        raise ValueError("Solo se puede guardar una partida iniciada")

    if encabezado.semilla != partida.semilla:
        raise ValueError(
            f"El encabezado dice semilla {encabezado.semilla} y la partida "
            f"usa {partida.semilla}"
        )

    if encabezado.jugador != partida.jugador.nombre:
        raise ValueError(
            f"El encabezado dice jugador {encabezado.jugador!r} y la partida "
            f"es de {partida.jugador.nombre!r}"
        )


def escribir_encabezado(e, encabezado):
    e.texto("cripta", encabezado.cripta_id)
    e.texto("version_cripta", encabezado.version_cripta)
    e.texto("version_catalogo", encabezado.version_catalogo)
    e.entero("semilla", encabezado.semilla)
    e.texto("jugador", encabezado.jugador)


def leer_encabezado(l):
    return Encabezado(
        cripta_id=l.texto("cripta"),
        version_cripta=l.texto("version_cripta"),
        version_catalogo=l.texto("version_catalogo"),
        semilla=l.entero("semilla"),
        jugador=l.texto("jugador"),
    )


def escribir_general(e, partida):
    e.booleano("terminada", partida.terminada)
    e.texto_opcional("resultado", partida.resultado)
    e.entero("reloj", partida.reloj)
    e.entero("acciones", partida.acciones_jugador)
    e.entero("derrotados", partida.enemigos_derrotados)
    e.booleano("puerta_de_salida_abierta", partida.puerta_de_salida_abierta)
    e.entero("sala_inicial", partida.id_sala_inicial)
    e.entero_opcional("sala_salida", partida.id_sala_salida)
    e.texto_opcional("llave_salida", partida.llave_salida)

    # §2.6: el estado EXACTO del generador. Con eso, lo que salga del dado
    # después de cargar es lo mismo que habría salido sin guardar.
    version, estado, gauss = partida.azar.getstate()
    e.empezar_grupo("azar")
    e.entero("version", version)
    e.enteros32("estado", estado)
    e.real_opcional("gauss", gauss)
    e.terminar_grupo()

    _escribir_jugador(e, partida.jugador)
    _escribir_efecto(e, "veneno", partida.veneno)
    _escribir_efecto(e, "antorcha", partida.antorcha)
    _escribir_agenda(e, partida)

    mensajes = Vector()
    for mensaje in partida.bitacora:
        mensajes.agregar(mensaje)

    e.empezar_lista("bitacora", len(mensajes))
    for i in range(len(mensajes)):
        e.texto(None, mensajes.obtener(i))
    e.terminar_lista()


def _escribir_jugador(e, jugador):
    inventario = jugador.inventario

    e.empezar_grupo("jugador")
    e.texto("nombre", jugador.nombre)
    e.entero("vida_max", jugador.vida_max)
    e.entero("vida", jugador.vida)
    e.entero("ataque", jugador.ataque)
    e.entero("defensa", jugador.defensa)
    e.entero("velocidad", jugador.velocidad)
    e.entero_opcional("sala", jugador.sala_actual)
    _escribir_evento(e, "turno", jugador.evento_siguiente)

    e.empezar_grupo("inventario")
    e.entero("capacidad", inventario.capacidad())
    e.entero("pergaminos", inventario.cantidad_pergaminos())

    objetos = inventario.orden_real()
    e.empezar_lista("objetos", len(objetos))
    for objeto in objetos:
        e.texto(None, objeto["id"])
    e.terminar_lista()

    actual, arma, armadura = inventario.posiciones()
    e.entero("actual", actual)
    e.entero("arma", arma)
    e.entero("armadura", armadura)
    e.terminar_grupo()

    e.terminar_grupo()


def _escribir_efecto(e, nombre, efecto):
    e.empezar_grupo(nombre)
    e.booleano("hay", efecto is not None)

    if efecto is not None:
        e.entero("valor", efecto.valor)
        e.entero_opcional("hasta", efecto.hasta)
        _escribir_evento(e, "evento", efecto.evento)

    e.terminar_grupo()


def _escribir_evento(e, nombre, evento):
    
    e.empezar_grupo(nombre)
    e.booleano("hay", evento is not None)

    if evento is not None:
        e.entero("tiempo", evento.tiempo)
        e.entero("secuencia", evento.secuencia)
        e.texto("tipo", evento.tipo)
        e.booleano("valido", evento.esta_valido())
        e.booleano("pendiente", evento.esta_valido() and evento.en_monticulo)

    e.terminar_grupo()


def _escribir_agenda(e, partida):
    agenda = partida.agenda
    pendientes = agenda.eventos_pendientes()           # por secuencia

    e.empezar_grupo("agenda")
    e.entero("siguiente_secuencia", agenda.siguiente_secuencia)
    e.empezar_lista("eventos", len(pendientes))

    for i in range(len(pendientes)):
        evento = pendientes.obtener(i)

        if evento.datos is not None:
            raise ValueError(f"No se sabe guardar los datos del evento {evento.tipo}")

        e.empezar_grupo(None)
        e.entero("tiempo", evento.tiempo)
        e.entero("secuencia", evento.secuencia)
        e.texto("tipo", evento.tipo)
        _escribir_objetivo(e, partida, evento)
        e.terminar_grupo()

    e.terminar_lista()
    e.terminar_grupo()


def _escribir_objetivo(e, partida, evento):
    
    tipo, objetivo = evento.tipo, evento.objetivo

    if tipo == TURNO_JUGADOR:
        _exigir(objetivo is partida.jugador, "un turno del jugador apunta a otro actor")

    elif tipo == TURNO_ENEMIGO or tipo == REGENERACION:
        sala, posicion = _ubicar_enemigo(partida.mapa, objetivo)
        e.entero("sala", sala)
        e.entero("posicion", posicion)

    elif tipo == CIERRE_PUERTA:
        sala, direccion = _ubicar_puerta(partida.mapa, objetivo)
        e.entero("sala", sala)
        e.texto("direccion", direccion)

    elif tipo == PULSO_VENENO:
        _exigir(objetivo is partida.veneno, "un pulso de veneno que no es del veneno actual")

    elif tipo == APAGAR_ANTORCHA:
        _exigir(objetivo is partida.antorcha, "un apagado que no es de la antorcha actual")

    elif tipo == FIN_VELOCIDAD:
        # Este efecto solo lo conoce su evento: se guarda aquí mismo.
        e.entero("valor", objetivo.valor)
        e.entero_opcional("hasta", objetivo.hasta)

    elif tipo == REARME_TRAMPA:
        sala, posicion = _ubicar_trampa(partida.mapa, objetivo)
        e.entero("sala", sala)
        e.entero("posicion", posicion)

    else:
        raise ValueError(f"No se sabe guardar un evento de tipo {tipo!r}")


def _ubicar_enemigo(mapa, enemigo):
    
    _exigir(isinstance(enemigo, Enemigo), "un turno de enemigo sin enemigo")
    sala = mapa.obtener_sala(enemigo.sala_actual)

    if sala is not None:
        for posicion in range(sala.cantidad_enemigos()):
            if sala.enemigo_en(posicion) is enemigo:
                return sala.id, posicion

    raise ValueError(f"Un evento apunta a {enemigo.id_instancia}, que no está en su sala")


def _ubicar_puerta(mapa, puerta):
    salas = mapa.obtener_todas()

    for i in range(len(salas)):
        sala = salas.obtener(i)

        for d in range(len(DIRECCIONES)):
            if sala.obtener_puerta(DIRECCIONES[d]) is puerta:
                return sala.id, DIRECCIONES[d]

    raise ValueError("Un cierre automático apunta a una puerta que no está en el mapa")


def _ubicar_trampa(mapa, trampa):
    salas = mapa.obtener_todas()

    for i in range(len(salas)):
        sala = salas.obtener(i)

        for posicion in range(sala.cantidad_trampas()):
            if sala.trampa_en(posicion) is trampa:
                return sala.id, posicion

    raise ValueError("Un rearme apunta a una trampa que no está en el mapa")


def _exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(f"Estado inesperado al guardar: {mensaje}")



def escribir_sala(e, sala):
    e.entero("id", sala.id)
    e.texto("nombre", sala.nombre)

    puertas = sala.puertas()
    e.empezar_lista("puertas", len(puertas))

    for i in range(len(puertas)):
        puerta = puertas.obtener(i)
        e.empezar_grupo(None)
        e.texto("direccion", sala.direccion_de(puerta))
        e.entero("destino", puerta.sala_destino)
        e.booleano("cerrada", puerta.esta_cerrada())
        e.texto_opcional("llave", puerta.llave)
        e.entero_opcional("cierre_automatico", puerta.cierre_automatico)
        # Formato 2 (FR-026): el costo de la salida. El rango de los
        # cazadores NO se escribe: sale de la ficha (contracts/guardado.md).
        e.entero("costo", puerta.costo)
        e.terminar_grupo()

    e.terminar_lista()

    e.entero_opcional("rastro", sala.ultimo_rastro)
    e.booleano("cargada", sala.contenido_cargado())

    if sala.contenido_cargado():
        _escribir_contenido_original(e, sala.contenido)

        e.empezar_lista("objetos", sala.cantidad_objetos())
        for i in range(sala.cantidad_objetos()):
            e.texto(None, sala.objeto_en(i))
        e.terminar_lista()

        e.entero("pergaminos", sala.cantidad_pergaminos())
        e.booleano("pergaminos_apartados", sala.pergaminos_ya_apartados())

        e.empezar_lista("trampas", sala.cantidad_trampas())
        for i in range(sala.cantidad_trampas()):
            trampa = sala.trampa_en(i)
            e.empezar_grupo(None)
            e.texto("instancia", trampa.instancia)
            e.texto("tipo", trampa.tipo)
            e.booleano("activa", trampa.esta_activa())
            e.terminar_grupo()
        e.terminar_lista()

    
    e.empezar_lista("enemigos", sala.cantidad_enemigos())

    for i in range(sala.cantidad_enemigos()):
        enemigo = sala.enemigo_en(i)
        e.empezar_grupo(None)
        e.texto("instancia", enemigo.id_instancia)
        e.texto("tipo", enemigo.tipo)
        e.entero_opcional("vida_inicial", enemigo.vida_inicial)
        e.booleano("activo", enemigo.esta_activo())

        if enemigo.esta_activo():
            e.entero("vida", enemigo.vida)
            e.entero("velocidad", enemigo.velocidad)

        _escribir_evento(e, "turno", enemigo.evento_siguiente)
        _escribir_evento(e, "regeneracion", enemigo.evento_regeneracion)
        e.terminar_grupo()

    e.terminar_lista()


def _escribir_contenido_original(e, contenido):
    
    objetos = contenido.get("objetos") or ()
    trampas = contenido.get("trampas") or ()
    enemigos = contenido.get("enemigos") or ()

    e.empezar_grupo("original")

    e.empezar_lista("objetos", len(objetos))
    for id_objeto in objetos:
        e.texto(None, id_objeto)
    e.terminar_lista()

    e.empezar_lista("trampas", len(trampas))
    for datos in trampas:
        e.empezar_grupo(None)
        e.texto("instancia", datos["instancia"])
        e.texto("tipo", datos["tipo"])
        e.terminar_grupo()
    e.terminar_lista()

    e.empezar_lista("enemigos", len(enemigos))
    for datos in enemigos:
        e.empezar_grupo(None)
        e.texto("instancia", datos["instancia"])
        e.texto("tipo", datos["tipo"])
        e.entero_opcional("vida", datos.get("vida"))
        e.terminar_grupo()
    e.terminar_lista()

    e.terminar_grupo()


class SalaLeida:

    def __init__(self, sala, referencias):
        self.sala = sala
        self.referencias = referencias


def leer_sala(l, fichas):
    sala = Sala(l.entero("id"), l.texto("nombre"), None)

    for _ in range(l.empezar_lista("puertas")):
        l.empezar_grupo(None)
        direccion = l.texto("direccion")
        destino = l.entero("destino")
        cerrada = l.booleano("cerrada")
        llave = l.texto_opcional("llave")
        cierre_automatico = l.entero_opcional("cierre_automatico")
        costo = l.entero("costo")

        if costo < 1:
            raise ErrorGuardado(
                f"Sala {sala.id}: la salida {direccion} tiene un costo "
                f"inválido ({costo})")

        puerta = Puerta(
            sala_destino=destino,
            cerrada=cerrada,
            llave=llave,
            cierre_automatico=cierre_automatico,
            costo=costo,
        )
        l.terminar_grupo()

        try:
            sala.poner_puerta(direccion, puerta)
        except ValueError as error:
            raise ErrorGuardado(f"Sala {sala.id}: {error}")

    l.terminar_lista()

    sala.ultimo_rastro = l.entero_opcional("rastro")

    if l.booleano("cargada"):
        contenido = _leer_contenido_original(l, sala.id)

        objetos = Vector()
        for _ in range(l.empezar_lista("objetos")):
            objetos.agregar(l.texto(None))
        l.terminar_lista()

        pergaminos = l.entero("pergaminos")
        apartados = l.booleano("pergaminos_apartados")

        trampas = Vector()
        for _ in range(l.empezar_lista("trampas")):
            l.empezar_grupo(None)
            trampas.agregar(Trampa(l.texto("instancia"), l.texto("tipo"), l.booleano("activa")))
            l.terminar_grupo()
        l.terminar_lista()

        try:
            sala.restaurar_contenido(contenido, objetos, trampas, pergaminos, apartados)
        except ValueError as error:
            raise ErrorGuardado(f"Sala {sala.id}: {error}")

    referencias = Vector()

    for _ in range(l.empezar_lista("enemigos")):
        l.empezar_grupo(None)
        enemigo = Enemigo(l.texto("instancia"), l.texto("tipo"), l.entero_opcional("vida_inicial"))

        if l.booleano("activo"):
            ficha = fichas(enemigo.tipo)

            if ficha is None:
                raise ErrorGuardado(f"Falta la ficha {enemigo.tipo} del catálogo")

            try:
                enemigo.activar(ficha)
            except (ValueError, DatosInvalidos) as error:
                # Una ficha de cazador con rango inválido: para quien carga,
                # es un guardado que no se puede usar (FR-011, FR-026).
                raise ErrorGuardado(str(error))

            enemigo.vida = l.entero("vida")
            enemigo.velocidad = l.entero("velocidad")

        referencias.agregar((enemigo, _leer_evento(l, "turno"), _leer_evento(l, "regeneracion")))
        l.terminar_grupo()

        sala.agregar_enemigo(enemigo)

    l.terminar_lista()

    return SalaLeida(sala, referencias)


def _leer_contenido_original(l, id_sala):
    
    l.empezar_grupo("original")

    objetos = []
    for _ in range(l.empezar_lista("objetos")):
        objetos.append(l.texto(None))
    l.terminar_lista()

    trampas = []
    for _ in range(l.empezar_lista("trampas")):
        l.empezar_grupo(None)
        trampas.append({"instancia": l.texto("instancia"), "tipo": l.texto("tipo")})
        l.terminar_grupo()
    l.terminar_lista()

    enemigos = []
    for _ in range(l.empezar_lista("enemigos")):
        l.empezar_grupo(None)
        datos = {"instancia": l.texto("instancia"), "tipo": l.texto("tipo")}
        vida = l.entero_opcional("vida")
        if vida is not None:
            datos["vida"] = vida
        enemigos.append(datos)
        l.terminar_grupo()
    l.terminar_lista()

    l.terminar_grupo()

    return {"sala": id_sala, "objetos": objetos, "trampas": trampas, "enemigos": enemigos}


class _RefEvento:
    def __init__(self, tiempo, secuencia, tipo, valido, pendiente):
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.tipo = tipo
        self.valido = valido
        self.pendiente = pendiente


def _leer_evento(l, nombre):
    l.empezar_grupo(nombre)
    ref = None

    if l.booleano("hay"):
        ref = _RefEvento(l.entero("tiempo"), l.entero("secuencia"), l.texto("tipo"),
                         l.booleano("valido"), l.booleano("pendiente"))

        if ref.tipo not in TIPOS_DE_EVENTO:
            raise ErrorGuardado(f"Tipo de evento desconocido: {ref.tipo!r}")

        if ref.pendiente and not ref.valido:
            raise ErrorGuardado("Un evento pendiente no puede estar cancelado")

    l.terminar_grupo()
    return ref


def evento_suelto(ref, objetivo):
    
    if ref is None:
        return None

    evento = Evento(ref.tiempo, ref.secuencia, ref.tipo, objetivo)

    if not ref.valido:
        evento.cancelar()

    return evento



class _EventoLeido:
    def __init__(self, tiempo, secuencia, tipo):
        self.tiempo = tiempo
        self.secuencia = secuencia
        self.tipo = tipo
        self.sala = None             # enemigo, puerta o trampa: su sala
        self.posicion = None         # enemigo o trampa: su posición en la sala
        self.direccion = None        # puerta: su dirección
        self.valor = None            # FIN_VELOCIDAD
        self.hasta = None            # FIN_VELOCIDAD


class _EfectoLeido:
    def __init__(self, valor, hasta, ref):
        self.valor = valor
        self.hasta = hasta
        self.ref = ref


class GeneralLeido:
    """Lo general, tal como se leyó (leer_general le pone un atributo por
    cada dato); armar_partida lo junta con las salas."""


def leer_general(l):
    g = GeneralLeido()
    g.terminada = l.booleano("terminada")
    g.resultado = l.texto_opcional("resultado")
    g.reloj = l.entero("reloj")
    g.acciones = l.entero("acciones")
    g.derrotados = l.entero("derrotados")
    g.puerta_de_salida_abierta = l.booleano("puerta_de_salida_abierta")
    g.sala_inicial = l.entero("sala_inicial")
    g.sala_salida = l.entero_opcional("sala_salida")
    g.llave_salida = l.texto_opcional("llave_salida")

    l.empezar_grupo("azar")
    g.azar = (l.entero("version"), l.enteros32("estado"), l.real_opcional("gauss"))
    l.terminar_grupo()

    l.empezar_grupo("jugador")
    g.nombre = l.texto("nombre")
    g.vida_max = l.entero("vida_max")
    g.vida = l.entero("vida")
    g.ataque = l.entero("ataque")
    g.defensa = l.entero("defensa")
    g.velocidad = l.entero("velocidad")
    g.sala_jugador = l.entero_opcional("sala")
    g.turno_jugador = _leer_evento(l, "turno")

    l.empezar_grupo("inventario")
    g.capacidad = l.entero("capacidad")
    g.pergaminos = l.entero("pergaminos")
    g.objetos = Vector()
    for _ in range(l.empezar_lista("objetos")):
        g.objetos.agregar(l.texto(None))
    l.terminar_lista()
    g.actual = l.entero("actual")
    g.arma = l.entero("arma")
    g.armadura = l.entero("armadura")
    l.terminar_grupo()
    l.terminar_grupo()

    g.veneno = _leer_efecto(l, "veneno")
    g.antorcha = _leer_efecto(l, "antorcha")

    l.empezar_grupo("agenda")
    g.siguiente_secuencia = l.entero("siguiente_secuencia")
    g.eventos = Vector()

    for _ in range(l.empezar_lista("eventos")):
        l.empezar_grupo(None)
        evento = _EventoLeido(l.entero("tiempo"), l.entero("secuencia"), l.texto("tipo"))
        _leer_objetivo(l, evento)
        g.eventos.agregar(evento)
        l.terminar_grupo()

    l.terminar_lista()
    l.terminar_grupo()

    g.bitacora = Vector()
    for _ in range(l.empezar_lista("bitacora")):
        g.bitacora.agregar(l.texto(None))
    l.terminar_lista()

    return g


def _leer_efecto(l, nombre):
    l.empezar_grupo(nombre)
    efecto = None

    if l.booleano("hay"):
        efecto = _EfectoLeido(l.entero("valor"), l.entero_opcional("hasta"),
                              _leer_evento(l, "evento"))

    l.terminar_grupo()
    return efecto


def _leer_objetivo(l, evento):
    tipo = evento.tipo

    if tipo == TURNO_ENEMIGO or tipo == REGENERACION:
        evento.sala = l.entero("sala")
        evento.posicion = l.entero("posicion")
    elif tipo == CIERRE_PUERTA:
        evento.sala = l.entero("sala")
        evento.direccion = l.texto("direccion")
    elif tipo == FIN_VELOCIDAD:
        evento.valor = l.entero("valor")
        evento.hasta = l.entero_opcional("hasta")
    elif tipo == REARME_TRAMPA:
        evento.sala = l.entero("sala")
        evento.posicion = l.entero("posicion")
    elif tipo not in TIPOS_DE_EVENTO:
        raise ErrorGuardado(f"Tipo de evento desconocido: {tipo!r}")


def armar_partida(encabezado, general, salas_leidas, fichas):
    
    try:
        return _armar(encabezado, general, salas_leidas, fichas)
    except DatosInvalidos as error:
        # Los dos lados de una puerta con costos distintos: el archivo está
        # dañado (FR-010, FR-026; contracts/guardado.md).
        raise ErrorGuardado(f"Datos inválidos en el guardado: {error}") from error
    except ValueError as error:
        # Los modelos rechazan datos imposibles con ValueError (por ejemplo,
        # una posición fuera del inventario): para quien carga, es un
        # guardado dañado.
        raise ErrorGuardado(f"Datos inválidos en el guardado: {error}") from error


def _armar(encabezado, g, salas_leidas, fichas):
    
    salas = Vector()
    for i in range(len(salas_leidas)):
        salas.agregar(salas_leidas.obtener(i).sala)

    mapa = Mapa()
    mapa.cargar_salas(salas)

    
    jugador = Jugador(g.nombre, g.vida_max, g.ataque, g.defensa, g.velocidad, g.capacidad)
    jugador.vida = g.vida
    jugador.sala_actual = g.sala_jugador

    objetos = Vector()
    for i in range(len(g.objetos)):
        ficha = fichas(g.objetos.obtener(i))
        if ficha is None:
            raise ErrorGuardado(f"Falta la ficha {g.objetos.obtener(i)} del catálogo")
        objetos.agregar(ficha)

    jugador.inventario.restaurar(objetos, g.actual, g.arma, g.armadura, g.pergaminos)

    if jugador.sala_actual is None or mapa.obtener_sala(jugador.sala_actual) is None:
        raise ErrorGuardado(f"El jugador está en la sala {jugador.sala_actual}, que no existe")

    partida = Partida(mapa, jugador, g.sala_inicial, fichas, semilla=encabezado.semilla,
                      id_sala_salida=g.sala_salida, llave_salida=g.llave_salida)
    partida.iniciada = True
    partida.terminada = g.terminada
    partida.resultado = g.resultado
    partida.acciones_jugador = g.acciones
    partida.enemigos_derrotados = g.derrotados
    partida.puerta_de_salida_abierta = g.puerta_de_salida_abierta
    partida.estado.reloj = g.reloj

    try:
        partida.azar.setstate(g.azar)
    except (TypeError, ValueError) as error:
        raise ErrorGuardado(f"El estado del azar está dañado: {error}")

    veneno = None if g.veneno is None else Efecto(VENENO, g.veneno.valor, g.veneno.hasta)
    antorcha = None if g.antorcha is None else Efecto(ANTORCHA, g.antorcha.valor, g.antorcha.hasta)
    partida.veneno = veneno
    partida.antorcha = antorcha

    partida.agenda.restaurar_secuencia(g.siguiente_secuencia)
    pares = Vector()

    for i in range(len(g.eventos)):
        leido = g.eventos.obtener(i)

        if i > 0 and leido.secuencia <= g.eventos.obtener(i - 1).secuencia:
            raise ErrorGuardado("Los eventos de la agenda no vienen en orden de secuencia")

        objetivo = _objetivo(leido, partida)
        evento = partida.agenda.restaurar_pendiente(leido.tiempo, leido.secuencia,
                                                     leido.tipo, objetivo)

        if leido.tipo == FIN_VELOCIDAD:
            objetivo.evento = evento

        pares.agregar((leido.secuencia, evento))

    pendientes = ArbolBusqueda.desde_ordenados(pares)

    jugador.evento_siguiente = _enlazar(g.turno_jugador, jugador, pendientes)

    if veneno is not None:
        veneno.evento = _enlazar(g.veneno.ref, veneno, pendientes)

    if antorcha is not None:
        antorcha.evento = _enlazar(g.antorcha.ref, antorcha, pendientes)

    for i in range(len(salas_leidas)):
        referencias = salas_leidas.obtener(i).referencias

        for j in range(len(referencias)):
            enemigo, turno, regeneracion = referencias.obtener(j)
            enemigo.evento_siguiente = _enlazar(turno, enemigo, pendientes)
            enemigo.evento_regeneracion = _enlazar(regeneracion, enemigo, pendientes)

    for i in range(len(g.bitacora)):
        partida.bitacora.restaurar_mensaje(g.bitacora.obtener(i))

    return partida


def _objetivo(leido, partida):
    tipo = leido.tipo

    if tipo == TURNO_JUGADOR:
        return partida.jugador

    if tipo == TURNO_ENEMIGO or tipo == REGENERACION:
        sala = partida.mapa.obtener_sala(leido.sala)
        if sala is None or not 0 <= leido.posicion < sala.cantidad_enemigos():
            raise ErrorGuardado(f"Un evento apunta a un enemigo que no está ({leido.sala}, {leido.posicion})")
        return sala.enemigo_en(leido.posicion)

    if tipo == CIERRE_PUERTA:
        sala = partida.mapa.obtener_sala(leido.sala)
        puerta = None if sala is None else sala.obtener_puerta(leido.direccion)
        if puerta is None:
            raise ErrorGuardado(f"Un cierre apunta a una puerta que no está ({leido.sala}, {leido.direccion})")
        return puerta

    if tipo == PULSO_VENENO:
        if partida.veneno is None:
            raise ErrorGuardado("Hay un pulso de veneno pendiente, pero no hay veneno")
        return partida.veneno

    if tipo == APAGAR_ANTORCHA:
        if partida.antorcha is None:
            raise ErrorGuardado("Hay una antorcha por apagarse, pero no hay antorcha")
        return partida.antorcha

    if tipo == FIN_VELOCIDAD:
        return Efecto(VELOCIDAD, leido.valor, leido.hasta)

    sala = partida.mapa.obtener_sala(leido.sala)
    if sala is None or not 0 <= leido.posicion < sala.cantidad_trampas():
        raise ErrorGuardado(f"Un rearme apunta a una trampa que no está ({leido.sala}, {leido.posicion})")
    return sala.trampa_en(leido.posicion)


def _enlazar(ref, objetivo, pendientes):
    """El evento al que apuntaba un objeto. Si estaba pendiente, es el
    MISMO evento de la agenda (si no, cancelarlo no lo cancelaría)."""
    if ref is None or not ref.pendiente:
        return evento_suelto(ref, objetivo)

    evento = pendientes.obtener(ref.secuencia)

    if (evento is None or evento.tiempo != ref.tiempo or evento.tipo != ref.tipo
            or evento.objetivo is not objetivo):
        raise ErrorGuardado(
            f"Un objeto apunta al evento {ref.secuencia} ({ref.tipo}), que no está "
            f"en la agenda como se esperaba"
        )

    return evento
