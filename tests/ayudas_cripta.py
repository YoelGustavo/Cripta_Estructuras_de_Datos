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
