from crypta.Modelo.Puerta import Puerta
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Trampa import Trampa


# Orden FIJO en que se guardan y se recorren las salidas: N, S, E, O.
# No depende del orden en que vengan en el JSON. Así, recorrer las salidas
# (vecinas, rastreador, errante "al azar" con la misma semilla) da siempre
# el mismo resultado y --replay reproduce la partida exacta (§2.8, §2.9).
DIRECCIONES = "NSEO"


def indice_direccion(direccion):
    """Casilla de esa dirección: N=0, S=1, E=2, O=3. -1 si no es válida."""
    if not isinstance(direccion, str) or len(direccion) != 1:
        return -1

    return DIRECCIONES.find(direccion)


class Sala:
    def __init__(self, id_sala, nombre, salidas):
        self.id = id_sala
        self.nombre = nombre

        # Vector de 4 casillas, una por dirección (en el orden de
        # DIRECCIONES). None = no hay salida en esa dirección.
        # Antes era un dict: §7 prohíbe usarlo como estructura propia.
        self._puertas = Vector(len(DIRECCIONES))

        for _ in range(len(DIRECCIONES)):
            self._puertas.agregar(None)

        # 'salidas' es el dict del JSON (se puede LEER, §7) o None si la
        # sala no trae salidas. Se lee aquí y no se guarda.
        if salidas is not None:
            for direccion in salidas:
                indice = indice_direccion(direccion)

                if indice < 0:
                    raise ValueError(
                        f"La sala {id_sala} tiene una salida en una "
                        f"dirección inválida: {direccion!r}"
                    )

                datos = salidas[direccion]

                self._puertas.asignar(
                    indice,
                    Puerta(
                        sala_destino=datos["sala"],
                        cerrada=bool(datos.get("cerrada")),
                        llave=datos.get("llave"),
                        cierre_automatico=datos.get(
                            "cierre_automatico"
                        )
                    )
                )

        self.contenido = None
        self.objetos = Vector()
        self.trampas = Vector()

        # Instante del último rastro dejado por el jugador.
        # None significa que el jugador nunca ha estado en esta sala.
        self.ultimo_rastro = None

    # =========================================================
    # PUERTAS
    # =========================================================

    def obtener_puerta(self, direccion):
        """La puerta en esa dirección, o None si no hay salida (o si la
        dirección no es N, S, E u O). O(1): es una casilla del Vector."""
        indice = indice_direccion(direccion)

        if indice < 0:
            return None

        return self._puertas.obtener(indice)

    def puertas(self, solo_abiertas=False):
        """Vector con las puertas que existen, SIEMPRE en orden N, S, E, O.

        solo_abiertas=True: solo las que se pueden atravesar (para moverse,
        el errante y el rastreador: los enemigos no abren puertas, §2.5)."""
        resultado = Vector(len(DIRECCIONES))

        for i in range(len(DIRECCIONES)):
            puerta = self._puertas.obtener(i)

            if puerta is None:
                continue

            if solo_abiertas and puerta.esta_cerrada():
                continue

            resultado.agregar(puerta)

        return resultado

    def direccion_de(self, puerta):
        """La dirección ("N", "S", "E" u "O") de una puerta de esta sala."""
        for i in range(len(DIRECCIONES)):
            if self._puertas.obtener(i) is puerta:
                return DIRECCIONES[i]

        return None

    # =========================================================
    # CONTENIDO
    # =========================================================

    def contenido_cargado(self):
        return self.contenido is not None

    def asignar_contenido(self, contenido):
        self.contenido = contenido

        # Reconstruimos los objetos del suelo.
        self.objetos = Vector()
        self.trampas = Vector()

        for id_objeto in contenido.get("objetos") or ():
            self.objetos.agregar(id_objeto)

        for datos_trampa in contenido.get("trampas") or ():
            trampa = Trampa(
                instancia=datos_trampa["instancia"],
                tipo=datos_trampa["tipo"]
            )

            self.trampas.agregar(trampa)

    def cantidad_objetos(self):
        return len(self.objetos)

    def objeto_en(self, posicion):
        return self.objetos.obtener(posicion)

    def quitar_objeto(self, posicion):
        return self.objetos.quitar(posicion)

    def agregar_objeto(self, objeto):
        self.objetos.agregar(objeto)

    def insertar_objeto(self, posicion, objeto):
        self.objetos.insertar(
            posicion,
            objeto
        )

    def cantidad_trampas(self):
        return len(self.trampas)

    def trampa_en(self, posicion):
        return self.trampas.obtener(posicion)

    # =========================================================
    # RASTRO (§2.9)
    # =========================================================

    def registrar_rastro(self, tiempo):
        self.ultimo_rastro = tiempo

    def obtener_rastro(self):
        return self.ultimo_rastro
