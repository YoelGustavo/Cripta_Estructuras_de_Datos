"""Ayudas compartidas por las pruebas de la capacidad 001 (terreno y cazador).

Tarea T003; habilita las pruebas de FR-001 a FR-027. No contiene pruebas:
solo arma datos y partidas sintéticas pequeñas, escritas a mano para que
cada prueba muestre exactamente la cripta que usa.

- `salida`, `sala`, `contenido`: piezas del esqueleto y del contenido con el
  mismo formato JSON que entrega el servicio (P2 §4.1, contracts/).
- `ficha_errante`, `ficha_rastreador`, `ficha_cazador`, `catalogo`: fichas
  del catálogo.
- `partida_sintetica`: una `Partida` con el jugador y los enemigos en salas
  dadas, sin red.
- `FuenteContadora`: fuente en memoria que cuenta las solicitudes (FR-027).
- `FuenteQueFalla`: fuente que falla si se la llama (FR-018, FR-034).
- `controlador_sintetico`: una sesión con el Controlador de verdad sobre una
  fuente en memoria y una vista falsa (FR-011).
- Capacidad 003: `ubicacion` y `respuesta_llaves` arman la ubicación de las
  llaves; `verificar_cripta` verifica una cripta escrita a mano;
  `FuenteContadora` acepta `llaves` y cuenta `obtener_llaves`.

Los `dict` de este archivo son datos de entrada con forma de JSON, igual
que los que devuelve `json`; no son estructuras del juego (principio I).
"""

from crypta.Adaptadores.FuenteDatos import FuenteDatos, LlavesNoDisponibles
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import Partida


SEMILLA = 7
CRIPTA_ID = "cripta-prueba"
VERSION_CRIPTA = "v-prueba"
VERSION_CATALOGO = "c-prueba"

# Distingue «no declarar el campo» de declararlo con valor null (FR-001).
SIN_DECLARAR = object()


# ---------------------------------------------------------------------------
# Esqueleto y contenido
# ---------------------------------------------------------------------------

def salida(destino, costo=SIN_DECLARAR, cerrada=False, llave=None,
           cierre_automatico=None):
    """Una salida del esqueleto. `costo` puede omitirse (no se declara),
    ser None (se declara null) o cualquier valor, válido o no, para probar
    la validación (FR-010)."""
    datos = {"sala": destino}

    if costo is not SIN_DECLARAR:
        datos["costo"] = costo

    if cerrada:
        datos["cerrada"] = True

    if llave is not None:
        datos["llave"] = llave

    if cierre_automatico is not None:
        datos["cierre_automatico"] = cierre_automatico

    return datos


def sala(id_sala, salidas=None, nombre=None):
    """Una sala del esqueleto. `salidas` es {dirección: salida(...)}."""
    return {
        "id": id_sala,
        "nombre": nombre if nombre is not None else f"Sala {id_sala}",
        "salidas": dict(salidas or {}),
    }


def contenido(id_sala, enemigos=(), objetos=(), trampas=()):
    """Contenido de una sala. `enemigos` son pares (instancia, tipo) o
    tríos (instancia, tipo, vida); `trampas`, pares (instancia, tipo)."""
    return {
        "sala": id_sala,
        "enemigos": [_enemigo(datos) for datos in enemigos],
        "objetos": list(objetos),
        "trampas": [{"instancia": instancia, "tipo": tipo}
                    for instancia, tipo in trampas],
    }


def _enemigo(datos):
    resultado = {"instancia": datos[0], "tipo": datos[1]}

    if len(datos) > 2:
        resultado["vida"] = datos[2]

    return resultado


def contenidos_vacios(esqueleto):
    """Contenido sin enemigos, objetos ni trampas para cada sala."""
    return [contenido(datos["id"]) for datos in esqueleto]


# ---------------------------------------------------------------------------
# Fichas del catálogo
# ---------------------------------------------------------------------------

def ficha_enemigo(id_tipo, comportamiento, velocidad=100, vida_max=12,
                  ataque=5, defensa=1, suelta=()):
    return {
        "id": id_tipo,
        "clase": "enemigo",
        "nombre": id_tipo,
        "vida_max": vida_max,
        "ataque": ataque,
        "defensa": defensa,
        "velocidad": velocidad,
        "comportamiento": comportamiento,
        "suelta": list(suelta),
    }


def ficha_errante(id_tipo="ent_errante", velocidad=100, **otros):
    return ficha_enemigo(id_tipo, "errante", velocidad, **otros)


def ficha_rastreador(id_tipo="ent_rastreador", velocidad=100, **otros):
    return ficha_enemigo(id_tipo, "rastreador", velocidad, **otros)


def ficha_cazador(id_tipo="ent_cazador", rango=1000, velocidad=100, **otros):
    """Ficha de cazador (FR-011). Con `rango=SIN_DECLARAR` la ficha no trae
    el campo; cualquier otro valor se escribe tal cual, válido o no."""
    ficha = ficha_enemigo(id_tipo, "cazador", velocidad, **otros)

    if rango is not SIN_DECLARAR:
        ficha["rango"] = rango

    return ficha


def catalogo(*fichas):
    """{id: ficha} con las fichas dadas."""
    return {ficha["id"]: ficha for ficha in fichas}


# ---------------------------------------------------------------------------
# Partida
# ---------------------------------------------------------------------------

def nuevo_jugador(velocidad=100, vida_max=30, ataque=6,
                  defensa=2, inventario_max=10, pergaminos=0):
    jugador = Jugador("Héroe", vida_max=vida_max, ataque=ataque,
                      defensa=defensa, velocidad=velocidad,
                      inventario_max=inventario_max)
    jugador.inventario.fijar_pergaminos(pergaminos)
    return jugador


def mapa_de(esqueleto, contenidos=None):
    """Mapa cargado desde el esqueleto, con el contenido de todas las salas
    (las que no aparecen en `contenidos` quedan vacías)."""
    mapa = Mapa()
    mapa.cargar_desde_json(esqueleto)

    dados = list(contenidos or ())
    con_contenido = [datos["sala"] for datos in dados]
    dados.extend(contenido(datos["id"]) for datos in esqueleto
                 if datos["id"] not in con_contenido)

    mapa.asignar_contenidos(dados)
    return mapa


def partida_sintetica(esqueleto, contenidos=None, fichas=None, sala_inicial=1,
                      semilla=SEMILLA, jugador=None, iniciar=True,
                      sala_salida=None, llave_salida=None):
    """Partida sobre una cripta escrita a mano, sin red.

    `fichas` es un {id: ficha} (ver `catalogo`). Si `iniciar` es True, la
    partida queda iniciada: el jugador está en `sala_inicial` y los enemigos
    de esa sala ya se activaron."""
    mapa = mapa_de(esqueleto, contenidos)
    fichas = dict(fichas or {})

    partida = Partida(
        mapa,
        jugador if jugador is not None else nuevo_jugador(),
        sala_inicial,
        fichas.get,
        semilla=semilla,
        id_sala_salida=sala_salida,
        llave_salida=llave_salida,
    )

    if iniciar:
        partida.iniciar()

    return partida


def buscar_enemigo(partida, instancia):
    """El enemigo con esa instancia, esté en la sala que esté."""
    salas = partida.mapa.obtener_todas()

    for i in range(len(salas)):
        sala_mapa = salas.obtener(i)

        for j in range(sala_mapa.cantidad_enemigos()):
            enemigo = sala_mapa.enemigo_en(j)

            if enemigo.id_instancia == instancia:
                return enemigo

    raise AssertionError(f"No está el enemigo {instancia}")


# ---------------------------------------------------------------------------
# Ubicación de las llaves (capacidad 003, P2 §4.2)
# ---------------------------------------------------------------------------

def ubicacion(id_llave, sala_llave, enemigo=None):
    """Una entrada de la ubicación de las llaves, con el formato de
    GET /criptas/<id>/llaves (contracts/datos-servicio.md de la 003)."""
    datos = {"id": id_llave, "sala": sala_llave}

    if enemigo is not None:
        datos["enemigo"] = enemigo

    return datos


def respuesta_llaves(*ubicaciones):
    """La respuesta completa del servicio: {"llaves": [...]}."""
    return {"llaves": list(ubicaciones)}


def verificar_cripta(esqueleto, generales, llaves):
    """Verifica una cripta escrita a mano, sin red (FR-301): arma el Mapa,
    lee y valida la ubicación de las llaves (`llaves` es la respuesta del
    servicio) y llama al verificador. Devuelve el ResultadoVerificacion.

    Los imports van aquí dentro para que las demás pruebas no se rompan
    mientras el verificador no existe (tareas de la 003)."""
    from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
    from crypta.Modelo.Verificador import verificar

    mapa = mapa_de(esqueleto)
    ubicaciones = leer_ubicaciones(llaves, mapa)
    return verificar(mapa, generales, ubicaciones)


# ---------------------------------------------------------------------------
# Fuentes de datos falsas
# ---------------------------------------------------------------------------

def datos_generales(esqueleto, sala_inicial=1, sala_salida=None,
                    presupuesto=100, version=VERSION_CRIPTA,
                    cripta_id=CRIPTA_ID, llave_salida=None):
    return {
        "id": cripta_id,
        "version": version,
        "salas_total": len(esqueleto),
        "paginas": 1,
        "salas_por_pagina": max(1, len(esqueleto)),
        "sala_inicial": sala_inicial,
        "sala_salida": sala_salida,
        "llave_salida": llave_salida,
        "presupuesto_solicitudes": presupuesto,
        "inventario_max": 10,
        "jugador": {"vida_max": 30, "ataque": 6, "defensa": 2,
                    "velocidad": 100},
    }


class FuenteContadora(FuenteDatos):
    """Fuente en memoria con el contrato de FuenteDatos. Cuenta cada
    solicitud, en total y por operación, para comprobar que no hay
    solicitudes nuevas (FR-027)."""

    def __init__(self, esqueleto, contenidos=None, fichas=None,
                 generales=None, version_catalogo=VERSION_CATALOGO,
                 llaves=None):
        self.esqueleto = list(esqueleto)
        self.llaves = llaves
        self.contenidos = list(contenidos if contenidos is not None
                               else contenidos_vacios(esqueleto))
        self.fichas = dict(fichas or {})
        self.generales = (generales if generales is not None
                          else datos_generales(esqueleto))
        self.version_catalogo = version_catalogo
        self.solicitudes = 0
        self.por_operacion = {}

    def _contar(self, operacion):
        self.solicitudes += 1
        self.por_operacion[operacion] = self.por_operacion.get(operacion, 0) + 1

    def cantidad_solicitudes(self):
        return self.solicitudes

    def listar_criptas(self):
        self._contar("listar_criptas")
        return {"criptas": [{"id": self.generales["id"], "nombre": "prueba",
                             "salas": len(self.esqueleto), "dificultad": None}]}

    def obtener_cripta(self, cripta_id):
        self._contar("obtener_cripta")
        return dict(self.generales)

    def obtener_pagina_salas(self, cripta_id, pagina):
        self._contar("obtener_pagina_salas")
        return {"salas": list(self.esqueleto) if pagina == 1 else []}

    def obtener_contenido(self, cripta_id, salas):
        self._contar("obtener_contenido")
        pedidas = list(salas)
        return {"contenido": [datos for datos in self.contenidos
                              if datos["sala"] in pedidas]}

    def obtener_catalogo(self, ids):
        self._contar("obtener_catalogo")
        return {"entidades": [self.fichas[id_tipo] for id_tipo in ids
                              if id_tipo in self.fichas]}

    def obtener_version_cripta(self, cripta_id):
        self._contar("obtener_version_cripta")
        return {"version": self.generales["version"]}

    def obtener_version_catalogo(self):
        self._contar("obtener_version_catalogo")
        return {"version": self.version_catalogo}

    def obtener_llaves(self, cripta_id):
        """La ubicación de las llaves (capacidad 003). Sin `llaves`, se
        comporta como una fuente que no las tiene (FR-324)."""
        self._contar("obtener_llaves")

        if self.llaves is None:
            raise LlavesNoDisponibles(
                f"la cripta {cripta_id} no tiene ubicación de llaves")

        return self.llaves


def controlador_sintetico(fuente, carpeta, comandos, semilla=SEMILLA):
    """Una sesión del juego con el Controlador, el GestorContenido y el
    RepositorioFichas de verdad sobre `fuente`, sin disco de caché, con
    `partida.log` en `carpeta` y una vista falsa que escribe `comandos` y
    después "salir".

    Antes de entregar cada comando, la vista espera a que terminen las
    precargas pedidas, para que la prueba no dependa de cuánto tarde el
    hilo de la precarga."""
    from unittest.mock import Mock
    import os

    from crypta.Adaptadores.RegistroPartida import Encabezado, RegistroPartida
    from crypta.Controlador.Controlador import Controlador
    from crypta.Controlador.Fabrica import nueva_partida
    from crypta.Controlador.GestorContenido import GestorContenido
    from crypta.Controlador.GestorCripta import GestorCripta
    from crypta.Controlador.RepositorioFichas import RepositorioFichas

    cripta_id = fuente.generales["id"]
    datos, mapa, _ = GestorCripta(fuente, _AlmacenVacio()).cargar(cripta_id)
    repositorio = RepositorioFichas(fuente)
    partida = nueva_partida(datos, mapa, repositorio.obtener_ficha, semilla,
                            "Ana")
    gestor = GestorContenido(fuente, mapa, cripta_id, repositorio)
    encabezado = Encabezado(cripta_id, datos["version"],
                            fuente.version_catalogo, semilla, "Ana")
    registro = RegistroPartida.crear(os.path.join(carpeta, "partida.log"),
                                     encabezado)

    vista = Mock()
    controlador = Controlador(partida, gestor, vista, registro, encabezado,
                              repositorio)
    pendientes = list(comandos) + ["salir"]

    def leer_comando():
        for _, _, futuro in controlador.gestor_contenido._pendientes:
            futuro.exception()          # espera sin lanzar

        return pendientes.pop(0)

    vista.leer_comando.side_effect = leer_comando
    controlador.comandos_sin_leer = pendientes
    return controlador


class _AlmacenVacio:
    """Almacén sin nada guardado: obliga a descargar el esqueleto."""

    def cargar_cripta(self, cripta_id, version):
        return None


class FuenteQueFalla(FuenteDatos):
    """Cualquier solicitud hace fallar la prueba: sirve para demostrar que
    algo funciona sin red (FR-018, FR-027, FR-034)."""

    def _fallar(self, operacion):
        raise AssertionError(f"No se esperaba ninguna solicitud ({operacion})")

    def listar_criptas(self):
        self._fallar("listar_criptas")

    def obtener_cripta(self, cripta_id):
        self._fallar("obtener_cripta")

    def obtener_pagina_salas(self, cripta_id, pagina):
        self._fallar("obtener_pagina_salas")

    def obtener_contenido(self, cripta_id, salas):
        self._fallar("obtener_contenido")

    def obtener_catalogo(self, ids):
        self._fallar("obtener_catalogo")

    def obtener_version_cripta(self, cripta_id):
        self._fallar("obtener_version_cripta")

    def obtener_version_catalogo(self):
        self._fallar("obtener_version_catalogo")

    def obtener_llaves(self, cripta_id):
        self._fallar("obtener_llaves")


# ---------------------------------------------------------------------------
# Línea de tiempo (capacidad 004, T003)
# ---------------------------------------------------------------------------
#
# El oráculo (`jugar_con_oraculo`) y `serializar_estado` viven en
# `crypta/bench/oraculo_linea.py`, porque los usa también el bench (FR-430);
# las pruebas los importan de ahí. Aquí solo se arma la partida y se eligen
# los comandos.

FICHAS_LINEA = (
    {"id": "itm_daga", "clase": "arma", "nombre": "Daga", "peso": 1,
     "valor": 1, "ataque_bonus": 2},
    {"id": "itm_cota", "clase": "armadura", "nombre": "Cota", "peso": 3,
     "valor": 2, "defensa_bonus": 1},
    {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción", "peso": 1,
     "valor": 1, "cura": 5},
    {"id": "itm_pocion_rapida", "clase": "pocion", "nombre": "Poción rápida",
     "peso": 1, "valor": 1, "cura": 2, "modificador_velocidad": 50,
     "duracion": 300},
    {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha",
     "peso": 1, "valor": 1, "duracion": 400},
    {"id": "itm_pergamino", "clase": "pergamino_retroceso",
     "nombre": "Pergamino", "peso": 0, "valor": 1},
    {"id": "trp_veneno", "clase": "trampa", "nombre": "Aguja", "daño": 1,
     "veneno": 1, "rearme": 250},
    ficha_errante("ent_errante", velocidad=90, vida_max=14,
                  suelta=("itm_pergamino",)),
    ficha_rastreador("ent_rastreador", velocidad=120, vida_max=10),
)


def esqueleto_linea():
    """Cuadrícula de 3 × 3 (salas 1 a 9) con costos distintos y una puerta
    cerrada sin llave con cierre automático entre 1 y 4."""
    def vecinas(i):
        fila, columna = (i - 1) // 3, (i - 1) % 3
        salidas = {}

        if columna < 2:
            salidas["E"] = salida(i + 1, costo=50 + 25 * columna)
        if columna > 0:
            salidas["O"] = salida(i - 1, costo=50 + 25 * (columna - 1))
        if fila < 2:
            salidas["S"] = salida(i + 3, costo=100)
        if fila > 0:
            salidas["N"] = salida(i - 3, costo=100)

        return salidas

    esqueleto = [sala(i, vecinas(i)) for i in range(1, 10)]
    esqueleto[0]["salidas"]["S"] = salida(4, costo=100, cerrada=True,
                                          cierre_automatico=150)
    esqueleto[3]["salidas"]["N"] = salida(1, costo=100, cerrada=True,
                                          cierre_automatico=150)
    return esqueleto


def contenidos_linea():
    return [
        contenido(1, objetos=("itm_daga", "itm_cota", "itm_pocion",
                              "itm_pergamino", "itm_pergamino",
                              "itm_antorcha")),
        contenido(2, enemigos=(("e-1", "ent_errante"),)),
        contenido(3, enemigos=(("r-1", "ent_rastreador"),),
                  objetos=("itm_pocion_rapida",)),
        contenido(4),
        contenido(5, trampas=(("t-5", "trp_veneno"),)),
        contenido(6, objetos=("itm_pergamino", "itm_pocion")),
        contenido(7),
        contenido(8, enemigos=(("e-2", "ent_errante"),)),
        contenido(9, objetos=("itm_cota",)),
    ]


class CriptaConPergaminos:
    """Una partida pequeña para la línea de tiempo (T003).

    - `partida`: iniciada en la sala 1; solo la sala 1 tiene su contenido,
      las demás se cargan al entrar con `garantizar` (salas aún sin
      contenido, HU1-12).
    - `fuente`: `FuenteContadora` (cuenta las solicitudes).
    - `gestor`: `GestorContenido` de verdad sobre esa fuente.
    - `garantizar`: `gestor.garantizar_sala`, para `ejecutar_comando`.

    Hay objetos de todas las clases que usa la línea (arma, armadura,
    pociones, antorcha), pergaminos en el suelo y que suelta un enemigo, un
    errante, un rastreador, una trampa con veneno y una puerta con cierre
    automático. El jugador tiene vida de sobra. Llamar a `cerrar()` al
    final."""

    def __init__(self, semilla=SEMILLA, inventario_max=10):
        from crypta.Controlador.GestorContenido import GestorContenido

        esqueleto = esqueleto_linea()
        contenidos = contenidos_linea()
        fichas = catalogo(*FICHAS_LINEA)

        self.fuente = FuenteContadora(esqueleto, contenidos, fichas)
        mapa = Mapa()
        mapa.cargar_desde_json(esqueleto)
        mapa.asignar_contenidos([datos for datos in contenidos
                                 if datos["sala"] == 1])

        jugador = nuevo_jugador(vida_max=500, ataque=7, defensa=2,
                                inventario_max=inventario_max)
        self.partida = Partida(mapa, jugador, 1, fichas.get, semilla=semilla)
        self.gestor = GestorContenido(self.fuente, mapa, CRIPTA_ID)
        self.garantizar = self.gestor.garantizar_sala
        self.partida.iniciar()

    def cerrar(self):
        self.gestor.cerrar()


def partida_con_pergaminos(semilla=SEMILLA, inventario_max=10):
    """Ver `CriptaConPergaminos`."""
    return CriptaConPergaminos(semilla, inventario_max)


def comando_al_azar(partida, azar):
    """Un comando probable de ser válido en el estado actual de `partida`.
    El juego puede rechazarlo (por ejemplo, mover contra una puerta que se
    cerró): el que juega lo salta."""
    sala_actual = partida.sala_actual()
    inventario = partida.jugador.inventario
    presentes = partida.enemigos_presentes()
    r = azar.random()

    if len(presentes) > 0 and r < 0.30:
        return f"atacar {presentes.obtener(0).id_instancia}"

    if sala_actual.cantidad_objetos() > 0 and r < 0.40:
        return f"recoger {azar.randrange(sala_actual.cantidad_objetos())}"

    actual = inventario.actual()

    if actual is not None and r < 0.50:
        if actual.get("clase") in ("arma", "armadura"):
            return "equipar"
        return "usar"

    if r < 0.56:
        return azar.choice(("avanzar", "retroceder"))

    if sala_actual.cantidad_pergaminos() > 0 and r < 0.62:
        return "recoger_pergamino"

    if (inventario.tiene_pergamino() and partida.estado.historial.puede_deshacer()
            and r < 0.68):
        return "pergamino"

    if r < 0.70:
        return "soltar"

    if r < 0.74:
        for direccion in "NSEO":
            puerta = sala_actual.obtener_puerta(direccion)

            if puerta is not None and puerta.esta_cerrada():
                return f"abrir {direccion}"

    if r < 0.78:
        return "esperar"

    abiertas = [direccion for direccion in "NSEO"
                if sala_actual.obtener_puerta(direccion) is not None
                and not sala_actual.obtener_puerta(direccion).esta_cerrada()]

    if not abiertas:
        return "esperar"

    return "mover " + azar.choice(abiertas)


def comandos_al_azar(partida, azar, cantidad):
    """Generador de `cantidad` comandos que mezclan mover, atacar, recoger,
    usar, equipar, soltar, abrir, esperar, avanzar, retroceder,
    recoger_pergamino y pergamino. Cada comando se elige **cuando se pide**,
    mirando el estado de ese momento, así sirve directamente como
    `comandos` de `jugar_con_oraculo`."""
    for _ in range(cantidad):
        if partida.terminada:
            return

        yield comando_al_azar(partida, azar)


def controlador_desde_linea(carpeta, comandos, semilla=SEMILLA):
    """`controlador_sintetico` sobre la cripta de la línea de tiempo
    (`esqueleto_linea`, `contenidos_linea`, `FICHAS_LINEA`), con presupuesto
    de sobra. La partida empieza sin iniciar: `controlador.iniciar()` la
    juega con `comandos` y después «salir»."""
    esqueleto = esqueleto_linea()
    fuente = FuenteContadora(esqueleto, contenidos_linea(),
                             catalogo(*FICHAS_LINEA),
                             generales=datos_generales(esqueleto, presupuesto=1000))
    return controlador_sintetico(fuente, carpeta, comandos, semilla)


# ---------------------------------------------------------------------------
# Niebla de guerra e «ir a» (capacidad 002, T040; SC-202, SC-203)
# ---------------------------------------------------------------------------

LADO_NIEBLA = 5                     # cuadrícula de 5 × 5: salas 1 a 25
SALA_INEXISTENTE_NIEBLA = 999       # destino de una salida que no lleva a nada

FICHAS_NIEBLA = (
    {"id": "itm_antorcha", "clase": "antorcha", "nombre": "Antorcha",
     "peso": 1, "valor": 1, "duracion": 400},
    {"id": "itm_pergamino", "clase": "pergamino_retroceso",
     "nombre": "Pergamino", "peso": 0, "valor": 1},
    {"id": "itm_pocion", "clase": "pocion", "nombre": "Poción", "peso": 1,
     "valor": 1, "cura": 5},
    {"id": "trp_aguja", "clase": "trampa", "nombre": "Aguja", "daño": 1,
     "rearme": 250},
    ficha_errante("ent_errante", velocidad=110, vida_max=8, ataque=3),
)


def nombre_niebla(id_sala):
    """Nombres únicos y ninguno contenido en otro: el id va entre un prefijo
    y un sufijo fijos («Cámara-1-fin» no está dentro de «Cámara-11-fin»)."""
    return f"Cámara-{id_sala}-fin"


def esqueleto_niebla(azar):
    """Cuadrícula de 5 × 5 con costos variables; algunas salidas empiezan
    cerradas (sin llave) con cierre automático. Además, una salida sin
    vuelta de la 25 a la 1 (FR-202, FR-205) y una de la 5 hacia una sala que
    no existe (research D4)."""
    lado = LADO_NIEBLA
    salidas = [dict() for _ in range(lado * lado + 1)]

    def unir(a, dir_a, b, dir_b):
        costo = azar.choice((50, 100, 150, 250, 400))
        cerrada = azar.random() < 0.3
        cierre = azar.choice((150, 300)) if cerrada else None
        salidas[a][dir_a] = salida(b, costo=costo, cerrada=cerrada,
                                   cierre_automatico=cierre)
        salidas[b][dir_b] = salida(a, costo=costo, cerrada=cerrada,
                                   cierre_automatico=cierre)

    for i in range(1, lado * lado + 1):
        fila, columna = (i - 1) // lado, (i - 1) % lado

        if columna < lado - 1:
            unir(i, "E", i + 1, "O")
        if fila < lado - 1:
            unir(i, "S", i + lado, "N")

    ultima = lado * lado
    salidas[ultima]["S"] = salida(1, costo=100)
    salidas[lado]["N"] = salida(SALA_INEXISTENTE_NIEBLA, costo=100)

    return [sala(i, salidas[i], nombre=nombre_niebla(i))
            for i in range(1, ultima + 1)]


def contenidos_niebla(azar):
    """Antorchas y pergaminos en el suelo (dos de cada uno en la sala 1),
    pociones, una trampa y tres errantes lejos de la sala 1."""
    total = LADO_NIEBLA * LADO_NIEBLA
    con_enemigo = azar.sample(range(2, total + 1), 3)
    con_trampa = azar.randrange(2, total + 1)
    resultado = []

    for i in range(1, total + 1):
        objetos = []

        if i == 1:
            objetos = ["itm_antorcha", "itm_antorcha", "itm_pergamino",
                       "itm_pergamino"]
        else:
            for id_objeto, probabilidad in (("itm_antorcha", 0.2),
                                            ("itm_pergamino", 0.2),
                                            ("itm_pocion", 0.15)):
                if azar.random() < probabilidad:
                    objetos.append(id_objeto)

        enemigos = ()
        if i in con_enemigo:
            enemigos = ((f"e-{i}", "ent_errante"),)

        trampas = ((f"t-{i}", "trp_aguja"),) if i == con_trampa else ()
        resultado.append(contenido(i, enemigos=enemigos, objetos=objetos,
                                   trampas=trampas))

    return resultado


def partida_niebla(semilla):
    """Partida de la 002 para las pruebas de equivalencia (SC-202, SC-203):
    cripta sintética pequeña sin red, con todo el contenido cargado, armada
    con `semilla`. El jugador empieza en la sala 1 con vida de sobra y dos
    pergaminos."""
    import random

    azar = random.Random(semilla)
    esqueleto = esqueleto_niebla(azar)
    contenidos = contenidos_niebla(azar)
    jugador = nuevo_jugador(vida_max=400, ataque=7, pergaminos=2)
    return partida_sintetica(esqueleto, contenidos,
                             catalogo(*FICHAS_NIEBLA), semilla=semilla,
                             jugador=jugador)


def _comando_antorcha(partida, azar):
    """Recoger una antorcha del suelo, ponerla como actual o encenderla; o
    None si no hay ninguna a mano."""
    sala_actual = partida.sala_actual()

    for i in range(sala_actual.cantidad_objetos()):
        if sala_actual.objeto_en(i) == "itm_antorcha":
            return f"recoger {i}"

    inventario = partida.jugador.inventario
    actual = inventario.actual()

    if actual is not None and actual.get("id") == "itm_antorcha":
        return "usar"

    if inventario.buscar_por_id("itm_antorcha") is not None:
        return azar.choice(("avanzar", "retroceder"))

    return None


def _comando_ir_a(partida, azar, anterior=None):
    """`ir a` hacia una sala explorada elegida al azar (puede ser la actual
    o no tener ruta: el juego la rechaza). Más de la mitad de las veces
    repite el destino `anterior`: así la ruta conocida se reutiliza entre
    viajes y se prueba su invalidación cuando, entre los dos, cambió alguna
    puerta recordada (SC-203; research D6)."""
    if anterior is not None and azar.random() < 0.6:
        return f"ir a {anterior}"

    exploradas = [s.id for s, estado in partida.conocimiento.salas_conocidas()
                  if estado == 2]
    return f"ir a {azar.choice(exploradas)}"


def comando_niebla(partida, azar, destino_anterior=None):
    """Un comando de `comando_al_azar`, de antorcha o `ir a`. Nunca mueve
    hacia una salida que lleva a una sala que no existe.
    `destino_anterior`: el id del último `ir a`, o None."""
    r = azar.random()

    if r < 0.15:
        return _comando_ir_a(partida, azar, destino_anterior)

    if r < 0.30:
        comando = _comando_antorcha(partida, azar)

        if comando is not None:
            return comando

    comando = comando_al_azar(partida, azar)

    if comando.startswith("mover "):
        puerta = partida.sala_actual().obtener_puerta(comando[-1])

        if puerta.sala_destino_ref is None:
            return "esperar"

    return comando


def comandos_niebla(partida, azar, cantidad):
    """Generador de `cantidad` comandos (ver `comando_niebla`), elegidos
    cuando se piden, como `comandos_al_azar`."""
    destino_anterior = None

    for _ in range(cantidad):
        if partida.terminada:
            return

        comando = comando_niebla(partida, azar, destino_anterior)

        if comando.startswith("ir a "):
            destino_anterior = int(comando[len("ir a "):])

        yield comando
