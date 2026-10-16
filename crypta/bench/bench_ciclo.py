"""--bench, sección CICLO (§5.2: menos de 20 ms entre dos decisiones).

§5.2: "Con la cripta de referencia ya cargada y excluyendo tiempo de red y
renderizado, resolver un ciclo completo de eventos entre dos decisiones
consecutivas del jugador debe tomar menos de 20 ms en el equipo local."

Qué se mide, en dos niveles:

  - MODELO: ejecutar_comando(partida, linea, ...). Es la acción del
    jugador más TODOS los eventos que ocurren hasta su próxima decisión
    (turnos de enemigos, veneno, regeneración, puertas, trampas...).
  - CICLO COMPLETO: Controlador.procesar_comando(texto), lo mismo que pasa
    al jugar: traducir el texto, el modelo, anotar el comando en el log
    (disco), actualizar las fichas en uso y buscar salas para precargar.
    Solo quedan afuera la pantalla (una vista muda) y la red (la cripta ya
    está toda cargada, como pide el §5.2).

La carga: una cripta de SALAS_CICLO salas toda cargada, con N enemigos en
la sala inicial. Por el §2.4 se activan TODOS en el instante 0, así que
desde el principio hay N actores con turnos en la agenda: rastreadores
rápidos que siguen al jugador, errantes que se reparten por la cripta (con
regeneración) y guardianes que se quedan. Tienen vida enorme para que
nadie muera y la carga no baje durante la medición: es una prueba de
ESTRÉS, más dura que una partida normal.
"""

import os
import random
import tempfile

from crypta.Adaptadores.RegistroPartida import Encabezado, RegistroPartida
from crypta.bench.medicion import cronometrar, formato_tiempo, tabla
from crypta.Controlador.Comandos import ComandoInvalido, ejecutar_comando
from crypta.Controlador.Controlador import Controlador
from crypta.Controlador.GestorContenido import LIMITE_VISITAS_PRECARGA, GestorContenido
from crypta.Controlador.RepositorioFichas import RepositorioFichas
from crypta.estructuras.ordenamiento import ordenar
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Partida import AccionInvalida, Partida


LIMITE_MS = 20                      # §5.2
SALAS_CICLO = 2500                  # cuadrícula de 50 x 50
ENEMIGOS = (50, 100, 200, 300, 500)
ENEMIGOS_RAPIDO = (20, 50)
CALENTAMIENTO = 20                  # acciones antes de medir (que se repartan)
ACCIONES = 60                       # acciones medidas

CATALOGO = {
    "ent_rastreador": {"id": "ent_rastreador", "clase": "enemigo", "nombre": "Rata",
                       "vida_max": 10 ** 6, "ataque": 5, "defensa": 1,
                       "velocidad": 150, "comportamiento": "rastreador"},
    "ent_errante": {"id": "ent_errante", "clase": "enemigo", "nombre": "Murciélago",
                    "vida_max": 10 ** 6, "ataque": 4, "defensa": 1,
                    "velocidad": 100, "comportamiento": "errante", "regeneracion": 2},
    "ent_guardian": {"id": "ent_guardian", "clase": "enemigo", "nombre": "Guardián",
                     "vida_max": 10 ** 6, "ataque": 7, "defensa": 3,
                     "velocidad": 90, "comportamiento": "guardián"},
    "itm_daga": {"id": "itm_daga", "clase": "arma", "nombre": "Daga",
                 "peso": 1, "valor": 1, "ataque_bonus": 2},
    "trp_dardos": {"id": "trp_dardos", "clase": "trampa", "nombre": "Dardos",
                   "daño": 3, "rearme": 300},
}
TIPOS_ENEMIGO = ("ent_rastreador", "ent_errante", "ent_guardian")


# ======================================================================
# LA CRIPTA DE CARGA
# ======================================================================

def esqueleto_y_contenidos(cantidad_salas, enemigos, semilla=1, cargadas=None):
    """Cuadrícula de 'cantidad_salas' salas. Los 'enemigos' empiezan en la
    sala 1. 'cargadas': cuántas salas traen contenido (None = todas)."""
    azar = random.Random(semilla)
    ancho = max(1, int(cantidad_salas ** 0.5))
    salas = []
    contenidos = []

    for i in range(1, cantidad_salas + 1):
        fila, columna = (i - 1) // ancho, (i - 1) % ancho
        salidas = {}

        if columna + 1 < ancho and i + 1 <= cantidad_salas:
            salidas["E"] = {"sala": i + 1}
        if columna > 0:
            salidas["O"] = {"sala": i - 1}
        if i + ancho <= cantidad_salas:
            salidas["S"] = {"sala": i + ancho}
        if fila > 0:
            salidas["N"] = {"sala": i - ancho}

        salas.append({"id": i, "nombre": f"Sala {i}", "salidas": salidas})

        if cargadas is not None and i > cargadas:
            continue

        contenidos.append({
            "sala": i,
            "enemigos": [{"instancia": f"e-{k}", "tipo": TIPOS_ENEMIGO[k % 3]}
                         for k in range(enemigos)] if i == 1 else [],
            "objetos": ["itm_daga"] if azar.random() < 0.3 else [],
            "trampas": ([{"instancia": f"t-{i}", "tipo": "trp_dardos"}]
                        if i > 1 and azar.random() < 0.1 else []),
        })

    return salas, contenidos


def partida_de_carga(enemigos, fichas, semilla=1, cantidad_salas=SALAS_CICLO):
    salas, contenidos = esqueleto_y_contenidos(cantidad_salas, enemigos, semilla)
    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos(contenidos)

    # Vida enorme: el jugador tampoco muere durante la medición.
    jugador = Jugador("Bench", vida_max=10 ** 9, ataque=8, defensa=3,
                      velocidad=100, inventario_max=8)
    partida = Partida(mapa, jugador, 1, fichas, semilla=semilla)
    partida.iniciar()
    return partida


def proxima_accion(partida, azar):
    """El "jugador" del bench: casi siempre camina, a veces ataca o espera."""
    presentes = partida.enemigos_presentes()

    if len(presentes) > 0 and azar.random() < 0.3:
        return f"atacar {presentes.obtener(0).id_instancia}"

    if azar.random() < 0.1:
        return "esperar"

    return "mover " + azar.choice("NSEO")


# ======================================================================
# LAS DOS MEDICIONES
# ======================================================================

class _FuenteEnMemoria:
    """El catálogo sin red. El contenido ya está todo cargado: si alguien lo
    pidiera, la medición estaría contando red, y eso no se permite."""

    def obtener_catalogo(self, ids):
        return {"entidades": [CATALOGO[i] for i in ids]}

    def obtener_contenido(self, cripta_id, salas):
        raise AssertionError("el ciclo medido pidió contenido por red")


class _VistaMuda:
    """La pantalla queda fuera de la medición (§5.2): no hace nada."""

    def __getattr__(self, nombre):
        return lambda *argumentos, **opciones: None


class Medicion:
    """Lo que se midió para una cantidad de enemigos. Tiempos en segundos."""

    def __init__(self, enemigos):
        self.enemigos = enemigos
        self.eventos_por_accion = 0.0
        self.modelo = Vector()        # un tiempo por acción
        self.ciclo = Vector()

    def media(self, tiempos):
        total = 0.0
        for i in range(len(tiempos)):
            total += tiempos.obtener(i)
        return total / len(tiempos)

    def percentil(self, tiempos, p):
        """El tiempo que no supera el p % de las acciones."""
        copia = Vector(len(tiempos))
        for i in range(len(tiempos)):
            copia.agregar(tiempos.obtener(i))
        ordenar(copia)
        indice = max(0, -(-len(copia) * p // 100) - 1)    # techo(n·p/100) - 1
        return copia.obtener(indice)

    def maximo(self, tiempos):
        return self.percentil(tiempos, 100)

    def cumple(self):
        return self.percentil(self.ciclo, 95) * 1000 < LIMITE_MS


def _una_vuelta_modelo(enemigos, acciones, calentamiento, semilla):
    partida = partida_de_carga(enemigos, CATALOGO.get, semilla)
    azar = random.Random(semilla)
    tiempos = Vector()
    eventos = 0

    for numero in range(calentamiento + acciones):
        linea = proxima_accion(partida, azar)
        antes = partida.agenda.siguiente_secuencia

        def accion():
            try:
                ejecutar_comando(partida, linea, lambda id_sala: None)
            except (AccionInvalida, ComandoInvalido):
                pass    # una pared: el jugador no se movió y no gastó tiempo

        transcurrido = cronometrar(accion)

        if numero >= calentamiento:
            tiempos.agregar(transcurrido)
            eventos += partida.agenda.siguiente_secuencia - antes

    return tiempos, eventos


def _una_vuelta_ciclo(enemigos, acciones, calentamiento, semilla, carpeta):
    repositorio = RepositorioFichas(_FuenteEnMemoria())
    partida = partida_de_carga(enemigos, repositorio.obtener_ficha, semilla)
    encabezado = Encabezado("bench", "v1", "cat-1", semilla, "Bench")
    controlador = Controlador(
        partida=partida,
        gestor_contenido=GestorContenido(_FuenteEnMemoria(), partida.mapa,
                                         "bench", repositorio),
        vista=_VistaMuda(),
        registro=RegistroPartida.crear(os.path.join(carpeta, "bench.log"), encabezado),
        encabezado=encabezado,
        repositorio_fichas=repositorio,
    )
    azar = random.Random(semilla)
    tiempos = Vector()
    eventos = 0

    try:
        for numero in range(calentamiento + acciones):
            texto = proxima_accion(partida, azar)
            antes = partida.agenda.siguiente_secuencia
            transcurrido = cronometrar(lambda: controlador.procesar_comando(texto))

            if numero >= calentamiento:
                tiempos.agregar(transcurrido)
                eventos += partida.agenda.siguiente_secuencia - antes
    finally:
        controlador.gestor_contenido.cerrar()

    return tiempos, eventos


def _mejor_de(vueltas, una_vuelta):
    """La partida es determinista: cada vuelta juega EXACTAMENTE las mismas
    acciones. Para cada acción se queda el mejor tiempo de las vueltas, como
    en medicion.medir (lo que se meta en medio solo puede sumar)."""
    mejores, eventos = una_vuelta()

    for _ in range(vueltas - 1):
        tiempos, otros = una_vuelta()

        if otros != eventos:
            raise AssertionError("dos vueltas iguales no dieron la misma partida")

        for i in range(len(tiempos)):
            if tiempos.obtener(i) < mejores.obtener(i):
                mejores.asignar(i, tiempos.obtener(i))

    return mejores, eventos


def medir(enemigos, acciones=ACCIONES, calentamiento=CALENTAMIENTO, vueltas=3,
          semilla=1):
    resultado = Medicion(enemigos)
    resultado.modelo, eventos = _mejor_de(vueltas, lambda: _una_vuelta_modelo(
        enemigos, acciones, calentamiento, semilla))
    resultado.eventos_por_accion = eventos / acciones

    with tempfile.TemporaryDirectory() as carpeta:
        resultado.ciclo, eventos_ciclo = _mejor_de(vueltas, lambda: _una_vuelta_ciclo(
            enemigos, acciones, calentamiento, semilla, carpeta))

    # El controlador juega la MISMA partida que el modelo solo.
    if eventos_ciclo != eventos:
        raise AssertionError("el ciclo completo jugó otra partida que el modelo")

    return resultado


# ======================================================================
# LA PRECARGA YA NO RECORRE TODO EL MAPA
# ======================================================================

def costo_precarga(cantidad_salas, cargadas, repeticiones=20):
    """Lo que tarda buscar salas para precargar con 'cargadas' de
    'cantidad_salas' salas con contenido (y el resto, lejos)."""
    salas, contenidos = esqueleto_y_contenidos(cantidad_salas, 0, cargadas=cargadas)
    mapa = Mapa()
    mapa.cargar_desde_json(salas)
    mapa.asignar_contenidos(contenidos)
    gestor = GestorContenido(_FuenteEnMemoria(), mapa, "bench")

    mejor = None
    for _ in range(repeticiones):
        transcurrido = cronometrar(lambda: gestor._salas_para_precargar(1))
        if mejor is None or transcurrido < mejor:
            mejor = transcurrido

    gestor.cerrar()
    return mejor


# ======================================================================
# LA SECCIÓN DEL --bench
# ======================================================================

def ejecutar(rapido=False):
    cantidades = ENEMIGOS_RAPIDO if rapido else ENEMIGOS
    acciones = 15 if rapido else ACCIONES
    calentamiento = 5 if rapido else CALENTAMIENTO
    filas = []

    for enemigos in cantidades:
        m = medir(enemigos, acciones, calentamiento, vueltas=1 if rapido else 3)
        filas.append((
            str(enemigos),
            f"{m.eventos_por_accion:.0f}",
            formato_tiempo(m.media(m.modelo)),
            formato_tiempo(m.media(m.ciclo)),
            formato_tiempo(m.percentil(m.ciclo, 95)),
            formato_tiempo(m.maximo(m.ciclo)),
            f"{m.media(m.ciclo) / max(1.0, m.eventos_por_accion) * 1e6:.0f} µs",
            "sí" if m.cumple() else "NO",
        ))

    ciclo = tabla(
        f"CICLO ENTRE DOS DECISIONES (§5.2: menos de {LIMITE_MS} ms). Cripta de "
        f"{SALAS_CICLO} salas toda cargada; {acciones} acciones medidas "
        f"(cada una, la mejor de {1 if rapido else 3} vueltas)",
        ("enemigos activos", "eventos por acción", "modelo: media",
         "ciclo completo: media", "p95", "máximo", "por evento", "¿cumple?"),
        filas,
        "p95: el 95 % de las acciones tardó eso o menos (se exige al p95; el "
        "máximo depende también del sistema operativo).")

    tamanos = (1000, 5000) if rapido else (1000, 5000, 10000)
    filas_precarga = []

    for cantidad in tamanos:
        filas_precarga.append((
            str(cantidad),
            formato_tiempo(costo_precarga(cantidad, cantidad)),
            formato_tiempo(costo_precarga(cantidad, cantidad - cantidad // 100)),
        ))

    precarga = tabla(
        "PRECARGA (§4.2): buscar salas para pedir, en cada acción",
        ("salas de la cripta", "toda cargada", "falta el 1 % (lejos)"),
        filas_precarga,
        f"Toda cargada: no busca nada, O(1). Si falta algo: revisa como máximo "
        f"{LIMITE_VISITAS_PRECARGA} salas, sin importar el tamaño de la cripta.")

    return ciclo + "\n\n" + precarga


if __name__ == "__main__":
    print(ejecutar())
