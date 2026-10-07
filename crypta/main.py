from crypta.Modelo.Agenda import Agenda
from crypta.Modelo.EstadoJuego import EstadoJuego
from crypta.Modelo.Historial import Historial, RegistroAccion
from crypta.Modelo.Cambio import Cambio
from crypta.Modelo.Jugador import Jugador
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Rastreador import Rastreador

from crypta.Controlador.GestorContenido import GestorContenido
from crypta.Controlador.RepositorioFichas import RepositorioFichas

from crypta.Adaptadores.AlmacenDisco import AlmacenDisco

from crypta.estructuras.CacheLRU import CacheLRU


# ============================================================
# DATOS DE PRUEBA
# ============================================================

SALAS = [
    {
        "id": 1,
        "nombre": "Entrada",
        "salidas": {
            "N": {"sala": 2}
        }
    },
    {
        "id": 2,
        "nombre": "Pasillo",
        "salidas": {
            "S": {"sala": 1},
            "N": {"sala": 3},
            "E": {"sala": 4}
        }
    },
    {
        "id": 3,
        "nombre": "Cripta",
        "salidas": {
            "S": {"sala": 2}
        }
    },
    {
        "id": 4,
        "nombre": "Nicho",
        "salidas": {
            "O": {"sala": 2}
        }
    }
]


CONTENIDOS = {
    1: {
        "sala": 1,
        "enemigos": [],
        "objetos": [
            "itm_antorcha"
        ],
        "trampas": []
    },

    2: {
        "sala": 2,
        "enemigos": [
            {
                "instancia": "e-201",
                "tipo": "ent_rata_gigante",
                "vida": 12
            }
        ],
        "objetos": [
            "itm_daga_oxidada"
        ],
        "trampas": [
            {
                "instancia": "t-17",
                "tipo": "trp_dardos"
            }
        ]
    },

    3: {
        "sala": 3,
        "enemigos": [],
        "objetos": [
            "itm_coraza_cuero"
        ],
        "trampas": []
    },

    4: {
        "sala": 4,
        "enemigos": [],
        "objetos": [
            "itm_pocion_menor"
        ],
        "trampas": []
    }
}


FICHAS = {
    "itm_antorcha": {
        "id": "itm_antorcha",
        "nombre": "Antorcha",
        "clase": "antorcha",
        "peso": 1,
        "valor": 5
    },

    "itm_daga_oxidada": {
        "id": "itm_daga_oxidada",
        "nombre": "Daga oxidada",
        "clase": "arma",
        "peso": 2,
        "valor": 15
    },

    "itm_coraza_cuero": {
        "id": "itm_coraza_cuero",
        "nombre": "Coraza de cuero",
        "clase": "armadura",
        "peso": 4,
        "valor": 20
    },

    "itm_pocion_menor": {
        "id": "itm_pocion_menor",
        "nombre": "Poción menor",
        "clase": "pocion",
        "peso": 1,
        "valor": 10
    },

    "ent_rata_gigante": {
        "id": "ent_rata_gigante",
        "nombre": "Rata gigante",
        "clase": "enemigo",
        "vida_max": 12,
        "ataque": 5,
        "defensa": 1,
        "velocidad": 150
    },

    "trp_dardos": {
        "id": "trp_dardos",
        "nombre": "Dardos",
        "clase": "trampa",
        "daño": 4
    }
}


# ============================================================
# FUENTE FALSA
# Solo evita depender de Internet durante estas pruebas.
# ============================================================

class FuentePrueba:

    def __init__(self):
        self.solicitudes_contenido = 0
        self.solicitudes_catalogo = 0

    def obtener_contenido(
        self,
        cripta_id,
        salas
    ):
        self.solicitudes_contenido += 1

        resultado = []

        for id_sala in salas:
            if id_sala in CONTENIDOS:
                resultado.append(
                    CONTENIDOS[id_sala]
                )

        return {
            "contenido": resultado
        }

    def obtener_catalogo(self, ids):
        self.solicitudes_catalogo += 1

        entidades = []

        for id_tipo in ids:
            if id_tipo in FICHAS:
                entidades.append(
                    FICHAS[id_tipo]
                )

        return {
            "entidades": entidades
        }


# ============================================================
# UTILIDADES
# ============================================================

def titulo(texto):
    print()
    print("=" * 60)
    print(texto)
    print("=" * 60)


def comprobar(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)

    print("  OK ->", mensaje)


def crear_mapa():
    mapa = Mapa()
    mapa.cargar_desde_json(SALAS)
    return mapa


# ============================================================
# 4.1 QUÉ OCURRE A CONTINUACIÓN
# ============================================================

def prueba_4_1():

    titulo("4.1 QUÉ OCURRE A CONTINUACIÓN")

    agenda = Agenda()

    e1 = agenda.programar(
        500,
        "rata"
    )

    e2 = agenda.programar(
        200,
        "trampa"
    )

    e3 = agenda.programar(
        200,
        "guardian"
    )

    print("Eventos programados:")
    print("  rata     -> 500")
    print("  trampa   -> 200")
    print("  guardian -> 200")

    primero = agenda.siguiente()

    print(
        "\nPrimer evento:",
        primero.tipo,
        "- tiempo:",
        primero.tiempo
    )

    comprobar(
        primero is e2,
        "se ejecuta primero el menor tiempo"
    )

    segundo = agenda.siguiente()

    print(
        "Segundo evento:",
        segundo.tipo,
        "- tiempo:",
        segundo.tiempo
    )

    comprobar(
        segundo is e3,
        "los empates respetan la secuencia"
    )

    # Evento cancelado.
    agenda.cancelar(e1)

    comprobar(
        not e1.esta_valido(),
        "un evento puede cancelarse"
    )

    # Probamos que no se ejecute algo futuro.
    futuro = agenda.programar(
        1000,
        "evento_futuro"
    )

    resultado = (
        agenda.siguiente_si_corresponde(
            900
        )
    )

    comprobar(
        resultado is None,
        "un evento futuro no se ejecuta antes de tiempo"
    )

    resultado = (
        agenda.siguiente_si_corresponde(
            1000
        )
    )

    comprobar(
        resultado is futuro,
        "el evento se ejecuta cuando corresponde"
    )

    print("\n4.1 RESULTADO: OK")


# ============================================================
# 4.2 TRAER EL CONTENIDO ANTES DE QUE HAGA FALTA
# ============================================================

def prueba_4_2():

    titulo(
        "4.2 TRAER EL CONTENIDO ANTES DE QUE HAGA FALTA"
    )

    fuente = FuentePrueba()
    mapa = crear_mapa()

    gestor = GestorContenido(
        fuente,
        mapa,
        "cripta-prueba"
    )

    sala2 = mapa.obtener_sala(2)

    comprobar(
        not sala2.contenido_cargado(),
        "la sala inicia sin contenido"
    )

    print(
        "Solicitudes antes:",
        fuente.solicitudes_contenido
    )

    gestor.precargar_desde(2)

    print(
        "Solicitudes después:",
        fuente.solicitudes_contenido
    )

    comprobar(
        sala2.contenido_cargado(),
        "la precarga incorpora el contenido"
    )

    comprobar(
        sala2.cantidad_objetos() == 1,
        "los objetos de la sala fueron cargados"
    )

    comprobar(
        sala2.cantidad_trampas() == 1,
        "las trampas de la sala fueron cargadas"
    )

    solicitudes_antes = (
        fuente.solicitudes_contenido
    )

    gestor.garantizar_sala(2)

    comprobar(
        fuente.solicitudes_contenido
        == solicitudes_antes,
        "una sala ya cargada no vuelve a solicitarse"
    )

    print("\n4.2 RESULTADO: OK")


# ============================================================
# 4.3 RESOLUCIÓN DE REFERENCIAS DEL CATÁLOGO
# ============================================================

def prueba_4_3():

    titulo(
        "4.3 RESOLUCIÓN DE REFERENCIAS DEL CATÁLOGO"
    )

    fuente = FuentePrueba()

    repositorio = RepositorioFichas(
        fuente,
        cache_size=25
    )

    contenidos = [
        CONTENIDOS[2],
        CONTENIDOS[3]
    ]

    ids = repositorio.extraer_ids_contenido(
        CONTENIDOS[2]
    )

    print("Referencias encontradas:")

    for id_tipo in ids:
        print(" ", id_tipo)

    comprobar(
        "ent_rata_gigante" in ids,
        "detecta referencias de enemigos"
    )

    comprobar(
        "itm_daga_oxidada" in ids,
        "detecta referencias de objetos"
    )

    comprobar(
        "trp_dardos" in ids,
        "detecta referencias de trampas"
    )

    repositorio.resolver_contenidos(
        contenidos
    )

    daga = repositorio.obtener_ficha(
        "itm_daga_oxidada"
    )

    rata = repositorio.obtener_ficha(
        "ent_rata_gigante"
    )

    print(
        "\nDaga resuelta:",
        daga["nombre"]
    )

    print(
        "Enemigo resuelto:",
        rata["nombre"]
    )

    comprobar(
        daga["nombre"] == "Daga oxidada",
        "la referencia del objeto se resuelve"
    )

    comprobar(
        rata["nombre"] == "Rata gigante",
        "la referencia del enemigo se resuelve"
    )

    print(
        "Solicitudes de catálogo:",
        fuente.solicitudes_catalogo
    )

    print("\n4.3 RESULTADO: OK")


# ============================================================
# 4.4 REUTILIZACIÓN Y CACHÉ PERSISTENTE
# ============================================================

def prueba_4_4():

    titulo(
        "4.4 REUTILIZACIÓN Y CACHÉ PERSISTENTE"
    )

    # --------------------------------------------------------
    # LRU
    # --------------------------------------------------------

    cache = CacheLRU(3)

    cache.insertar("A", {"nombre": "A"})
    cache.insertar("B", {"nombre": "B"})
    cache.insertar("C", {"nombre": "C"})

    # A vuelve a usarse.
    cache.obtener("A")

    # B queda protegido.
    cache.marcar_en_uso("B")

    desalojada = cache.insertar(
        "D",
        {"nombre": "D"}
    )

    print(
        "Ficha desalojada:",
        desalojada[0]
    )

    comprobar(
        desalojada[0] == "C",
        "LRU desaloja la ficha menos reciente disponible"
    )

    comprobar(
        cache.contiene("B"),
        "una ficha en uso no se desaloja"
    )

    # --------------------------------------------------------
    # PERSISTENCIA
    # --------------------------------------------------------

    ruta_prueba = "cache_prueba_integracion"

    almacen = AlmacenDisco(
        ruta_prueba
    )

    # Usamos una versión distinta para que esta prueba
    # no reutilice datos de ejecuciones anteriores.
    version = "version-prueba-4-4"

    almacen.guardar_catalogo(
        version,
        {
            "itm_antorcha":
                FICHAS["itm_antorcha"]
        }
    )

    ficha = almacen.cargar_ficha(
        version,
        "itm_antorcha"
    )

    comprobar(
        ficha is not None,
        "una ficha puede recuperarse desde disco"
    )

    comprobar(
        ficha["nombre"] == "Antorcha",
        "la ficha persistida conserva sus datos"
    )

    ficha_invalida = almacen.cargar_ficha(
        "otra-version",
        "itm_antorcha"
    )

    comprobar(
        ficha_invalida is None,
        "una versión distinta invalida la caché persistente"
    )

    # --------------------------------------------------------
    # RAM -> DISCO -> RED
    # --------------------------------------------------------

    fuente = FuentePrueba()

    repositorio = RepositorioFichas(
        fuente,
        almacen=almacen,
        version_catalogo=version,
        cache_size=2
    )

    solicitudes_antes = (
        fuente.solicitudes_catalogo
    )

    # Debe salir del disco.
    antorcha = repositorio.obtener_ficha(
        "itm_antorcha"
    )

    comprobar(
        antorcha is not None,
        "Repositorio recupera la ficha persistida"
    )

    comprobar(
        fuente.solicitudes_catalogo
        == solicitudes_antes,
        "la ficha de disco evita una solicitud de red"
    )

    # La daga NO fue guardada en esta versión.
    solicitudes_antes_red = (
        fuente.solicitudes_catalogo
    )

    daga = repositorio.obtener_ficha(
        "itm_daga_oxidada"
    )

    comprobar(
        daga is not None,
        "la ficha inexistente en disco se obtiene"
    )

    comprobar(
        fuente.solicitudes_catalogo
        == solicitudes_antes_red + 1,
        "si no está en RAM ni disco se consulta la fuente"
    )

    print("\n4.4 RESULTADO: OK")


# ============================================================
# 4.5 INVENTARIO
# ============================================================

def prueba_4_5():

    titulo("4.5 INVENTARIO")

    jugador = Jugador(
        nombre="Jugador",
        vida_max=30,
        ataque=5,
        defensa=2,
        velocidad=100,
        inventario_max=5
    )

    inventario = jugador.inventario

    # --------------------------------------------------------
    # RECOGER OBJETOS
    # --------------------------------------------------------

    comprobar(
        inventario.recoger(
            FICHAS["itm_antorcha"]
        ),
        "se recoge la antorcha"
    )

    comprobar(
        inventario.recoger(
            FICHAS["itm_daga_oxidada"]
        ),
        "se recoge la daga"
    )

    comprobar(
        inventario.recoger(
            FICHAS["itm_coraza_cuero"]
        ),
        "se recoge la coraza"
    )

    print("\nInventario:")

    for objeto in inventario.orden_real():
        print(
            " ",
            objeto["nombre"]
        )

    comprobar(
        len(inventario) == 3,
        "se agregaron tres objetos"
    )

    # --------------------------------------------------------
    # OBJETO ACTUAL Y NAVEGACIÓN
    # --------------------------------------------------------

    actual = inventario.actual()

    comprobar(
        actual is not None,
        "el inventario tiene objeto actual"
    )

    print(
        "Objeto actual:",
        actual["nombre"]
    )

    comprobar(
        actual["id"] == "itm_antorcha",
        "el primer objeto queda como actual"
    )

    siguiente = inventario.avanzar()

    print(
        "Después de avanzar:",
        siguiente["nombre"]
    )

    comprobar(
        siguiente["id"]
        == "itm_daga_oxidada",
        "se puede avanzar por el inventario"
    )

    anterior = inventario.retroceder()

    print(
        "Después de retroceder:",
        anterior["nombre"]
    )

    comprobar(
        anterior["id"]
        == "itm_antorcha",
        "se puede retroceder por el inventario"
    )

    # --------------------------------------------------------
    # CAPACIDAD
    # --------------------------------------------------------

    comprobar(
        inventario.capacidad() == 5,
        "respeta la capacidad configurada"
    )

    comprobar(
        inventario.espacio_disponible() == 2,
        "calcula correctamente el espacio disponible"
    )

    # --------------------------------------------------------
    # RECOGER DESDE EL SUELO
    # --------------------------------------------------------

    mapa = crear_mapa()

    mapa.asignar_contenidos([
        CONTENIDOS[4]
    ])

    sala = mapa.obtener_sala(4)

    print(
        "\nObjetos en suelo antes:",
        sala.cantidad_objetos()
    )

    id_objeto = sala.objeto_en(0)

    objeto = FICHAS[id_objeto]

    contexto_recoger = (
        inventario.recoger_desde_sala(
            sala,
            0,
            objeto
        )
    )

    comprobar(
        contexto_recoger is not None,
        "se puede recoger un objeto del suelo"
    )

    comprobar(
        len(inventario) == 4,
        "el objeto entra al inventario"
    )

    comprobar(
        sala.cantidad_objetos() == 0,
        "el objeto desaparece del suelo"
    )

    print(
        "Recogido del suelo:",
        objeto["nombre"]
    )

    # --------------------------------------------------------
    # DESHACER RECOGIDA
    # --------------------------------------------------------

    inventario.deshacer_recogida(
        contexto_recoger
    )

    comprobar(
        len(inventario) == 3,
        "deshacer recogida quita el objeto del inventario"
    )

    comprobar(
        sala.cantidad_objetos() == 1,
        "deshacer recogida restaura el objeto en el suelo"
    )

    # --------------------------------------------------------
    # SOLTAR EN LA SALA
    # --------------------------------------------------------

    objeto_actual = inventario.actual()

    contexto_soltar = (
        inventario.soltar_en_sala(
            sala
        )
    )

    comprobar(
        contexto_soltar is not None,
        "se puede soltar el objeto actual"
    )

    comprobar(
        len(inventario) == 2,
        "el objeto sale del inventario"
    )

    comprobar(
        sala.cantidad_objetos() == 2,
        "el objeto soltado aparece en el suelo"
    )

    print(
        "Soltado:",
        objeto_actual["nombre"]
    )

    # --------------------------------------------------------
    # DESHACER SOLTAR
    # --------------------------------------------------------

    inventario.deshacer_soltar_en_sala(
        contexto_soltar
    )

    comprobar(
        len(inventario) == 3,
        "deshacer soltar restaura el inventario"
    )

    comprobar(
        sala.cantidad_objetos() == 1,
        "deshacer soltar restaura el suelo"
    )

    comprobar(
        inventario.actual()["id"]
        == objeto_actual["id"],
        "deshacer soltar restaura el objeto actual"
    )

    print("\n4.5 RESULTADO: OK")


# ============================================================
# 4.6 PERGAMINOS E HISTORIAL REVERSIBLE
# ============================================================

def prueba_4_6():

    titulo(
        "4.6 PERGAMINOS DE RETROCESO E HISTORIAL REVERSIBLE"
    )

    estado = EstadoJuego()

    estado.historial = Historial(
        limite=5
    )

    estado.pergaminos_retroceso = 2

    jugador = Jugador(
        nombre="Jugador",
        vida_max=30,
        ataque=5,
        defensa=2,
        velocidad=100,
        inventario_max=5
    )

    print("Vida inicial:", jugador.vida)
    print(
        "Pergaminos:",
        estado.pergaminos_retroceso
    )

    accion = RegistroAccion(
        "Recibir daño"
    )

    accion.registrar_cambio(
        Cambio.de_atributo(
            "vida",
            jugador,
            "vida",
            jugador.vida
        )
    )

    jugador.recibir_danio(10)

    estado.historial.registrar(
        accion
    )

    print(
        "\nDespués del daño:",
        jugador.vida
    )

    comprobar(
        jugador.vida == 20,
        "la acción modificó la vida"
    )

    comprobar(
        len(estado.historial) == 1,
        "la acción quedó registrada"
    )

    resultado = (
        estado.usar_pergamino_retroceso()
    )

    print(
        "\nRetroceso:",
        resultado
    )

    print(
        "Vida restaurada:",
        jugador.vida
    )

    print(
        "Pergaminos restantes:",
        estado.pergaminos_retroceso
    )

    comprobar(
        resultado,
        "el pergamino deshace la última acción"
    )

    comprobar(
        jugador.vida == 30,
        "la vida vuelve a su valor anterior"
    )

    comprobar(
        estado.pergaminos_retroceso == 1,
        "el pergamino sí se consume"
    )

    comprobar(
        len(estado.historial) == 0,
        "la acción deshecha sale del historial"
    )

    # No debe consumir otro si no hay nada que deshacer.

    resultado = (
        estado.usar_pergamino_retroceso()
    )

    comprobar(
        not resultado,
        "no se retrocede con historial vacío"
    )

    comprobar(
        estado.pergaminos_retroceso == 1,
        "no se consume pergamino si no hay acción"
    )

    print("\n4.6 RESULTADO: OK")


# ============================================================
# 4.7 RASTRO DEL JUGADOR
# ============================================================

def prueba_4_7():

    titulo("4.7 EL RASTRO DEL JUGADOR")

    mapa = crear_mapa()

    jugador = Jugador(
        nombre="Jugador",
        vida_max=30,
        ataque=5,
        defensa=2,
        velocidad=100,
        inventario_max=5
    )

    # --------------------------------------------------------
    # Rastro y caducidad
    # --------------------------------------------------------

    jugador.mover_a(
        mapa.obtener_sala(1),
        100
    )

    jugador.mover_a(
        mapa.obtener_sala(2),
        200
    )

    jugador.mover_a(
        mapa.obtener_sala(4),
        300
    )

    print(
        "Huellas registradas:",
        len(jugador.rastro)
    )

    comprobar(
        len(jugador.rastro) == 3,
        "cada movimiento genera una huella"
    )

    huella = (
        jugador.rastro.obtener_reciente(
            4,
            699
        )
    )

    comprobar(
        huella is not None,
        "una huella de 399 unidades sigue vigente"
    )

    huella = (
        jugador.rastro.obtener_reciente(
            4,
            700
        )
    )

    comprobar(
        huella is None,
        "una huella de 400 unidades está caducada"
    )

    # --------------------------------------------------------
    # Rastreador
    # --------------------------------------------------------

    # Rastreador en sala 2.
    # Sus salidas son 1, 3 y 4.
    rastreador = Rastreador(
        "Rata rastreadora",
        150,
        sala_actual=2
    )

    destino = rastreador.decidir_destino(
        mapa,
        jugador.rastro,
        500
    )

    print(
        "\nDestino elegido:",
        destino
    )

    comprobar(
        destino == 4,
        "elige la salida con la huella vigente más reciente"
    )

    destino_caducado = (
        rastreador.decidir_destino(
            mapa,
            jugador.rastro,
            850
        )
    )

    print(
        "Destino en reloj 850:",
        destino_caducado
    )

    comprobar(
        destino_caducado is None,
        "ignora las huellas caducadas"
    )

    # --------------------------------------------------------
    # Deshacer movimiento
    # --------------------------------------------------------

    jugador.deshacer_ultimo_movimiento(
        2
    )

    comprobar(
        jugador.sala_actual == 2,
        "deshacer restaura la sala anterior"
    )

    comprobar(
        len(jugador.rastro) == 2,
        "deshacer elimina la última huella"
    )

    # --------------------------------------------------------
    # Varios rastreadores
    # --------------------------------------------------------

    agenda = Agenda()

    rastreadores = []

    for i in range(5):

        r = Rastreador(
            f"R{i + 1}",
            100,
            sala_actual=2
        )

        rastreadores.append(r)

    # Solo dos deben actuar en reloj 500.
    tiempos = [
        500,
        500,
        600,
        700,
        800
    ]

    for i in range(5):

        evento = agenda.programar(
            tiempos[i],
            "turno_rastreador",
            rastreadores[i]
        )

        rastreadores[i].asignar_evento(
            evento
        )

    actuaron = 0

    print("\nCiclo en reloj 500:")

    while True:

        evento = (
            agenda.siguiente_si_corresponde(
                500
            )
        )

        if evento is None:
            break

        actuaron += 1

        print(
            " Actúa:",
            evento.objetivo.nombre,
            "- tiempo:",
            evento.tiempo
        )

    comprobar(
        actuaron == 2,
        "solo se procesan los rastreadores que realmente actúan"
    )

    comprobar(
        len(agenda) == 3,
        "los eventos futuros permanecen pendientes"
    )

    print("\n4.7 RESULTADO: OK")


# ============================================================
# MAIN GENERAL
# ============================================================

def main():

    pruebas = [
        ("4.1", prueba_4_1),
        ("4.2", prueba_4_2),
        ("4.3", prueba_4_3),
        ("4.4", prueba_4_4),
        ("4.5", prueba_4_5),
        ("4.6", prueba_4_6),
        ("4.7", prueba_4_7)
    ]

    resultados = []

    for numero, prueba in pruebas:

        try:
            prueba()

            resultados.append(
                (numero, True, None)
            )

        except Exception as error:

            resultados.append(
                (numero, False, error)
            )

            print()
            print(
                f"{numero} RESULTADO: ERROR"
            )

            print(
                type(error).__name__ + ":",
                error
            )

    titulo("RESUMEN GENERAL")

    aprobadas = 0

    for numero, correcto, error in resultados:

        if correcto:
            print(
                numero,
                "✅"
            )

            aprobadas += 1

        else:
            print(
                numero,
                "❌",
                "-",
                error
            )

    print()
    print(
        f"Pruebas superadas: "
        f"{aprobadas}/{len(pruebas)}"
    )

    if aprobadas == len(pruebas):
        print()
        print(
            "TODO 4.1 - 4.7 FUNCIONA ✅"
        )
        print(
            "Listos para continuar con 4.8."
        )


if __name__ == "__main__":
    main()