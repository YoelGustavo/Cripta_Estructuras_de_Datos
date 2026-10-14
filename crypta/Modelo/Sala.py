from crypta.Modelo.Enemigo import Enemigo
from crypta.Modelo.Puerta import Puerta
from crypta.Modelo.Trampa import Trampa
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


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

        # Enemigos que están AHORA en la sala: los dormidos que trajo su
        # contenido y los activos que llegaron caminando desde otra (§2.4).
        self.enemigos = Vector()

        # Pergaminos de retroceso en el suelo: una CANTIDAD aparte, por la
        # misma razón que en el inventario (§2.11). Si su id se quedara en
        # el Vector de objetos, recogerlo (sin deshacerlo) correría las
        # posiciones que otros contextos de deshacer tienen anotadas.
        self.pergaminos = 0
        self._pergaminos_apartados = False

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

    def poner_puerta(self, direccion, puerta):
        """Pone la puerta de esa dirección (al cargar una partida guardada,
        §4.10, la sala se arma sin el JSON). Solo en una casilla vacía."""
        indice = indice_direccion(direccion)

        if indice < 0:
            raise ValueError(f"Dirección inválida: {direccion!r}")

        if self._puertas.obtener(indice) is not None:
            raise ValueError(f"La sala {self.id} ya tiene salida hacia {direccion}")

        self._puertas.asignar(indice, puerta)

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
        # El contenido de una sala se incorpora UNA sola vez. Si llegara
        # de nuevo (p. ej. una respuesta anticipada que llega tarde), se
        # ignora: volver a cargarlo reviviría objetos que el jugador ya
        # recogió y duplicaría los enemigos.
        if self.contenido_cargado():
            return

        self.contenido = contenido

        for id_objeto in contenido.get("objetos") or ():
            self.objetos.agregar(id_objeto)

        for datos_trampa in contenido.get("trampas") or ():
            trampa = Trampa(
                instancia=datos_trampa["instancia"],
                tipo=datos_trampa["tipo"]
            )

            self.trampas.agregar(trampa)

        # Un enemigo activo pudo haber entrado caminando ANTES de que se
        # cargara el contenido de esta sala: ese no se borra. Los del
        # contenido se ponen DELANTE de él, en el orden del JSON. Así el
        # orden de la sala es siempre "los del contenido, y después los que
        # llegaron caminando", sin importar CUÁNDO llegó el contenido (al
        # jugar llega por la red o la precarga; al reproducir puede venir
        # todo de una copia local). Si no, la partida y su reproducción
        # podrían quedar con los enemigos en otro orden (§4.11).
        # Todos nacen dormidos (§2.4: cargar el contenido no activa a nadie).
        posicion = 0

        for datos_enemigo in contenido.get("enemigos") or ():
            self.insertar_enemigo(
                posicion,
                Enemigo(
                    id_instancia=datos_enemigo["instancia"],
                    tipo=datos_enemigo["tipo"],
                    vida_inicial=datos_enemigo.get("vida")
                )
            )
            posicion += 1

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

    # =========================================================
    # PERGAMINOS EN EL SUELO (§2.11)
    # =========================================================

    def apartar_pergaminos(self, es_pergamino):
        """Saca del Vector de objetos los ids que son pergaminos y los
        cuenta aparte. 'es_pergamino(id)' dice si un id lo es (eso lo sabe
        la ficha del catálogo, que la sala no tiene).

        Se llama UNA vez, cuando el jugador entra a la sala y ya se
        conocen las fichas, antes de cualquier acción allí. O(k), con k
        los objetos del suelo; las demás vuelven en el mismo orden."""
        if self._pergaminos_apartados:
            return

        if not self.contenido_cargado():
            raise ValueError(
                f"La sala {self.id} todavía no tiene su contenido"
            )

        restantes = Vector()

        for i in range(len(self.objetos)):
            id_objeto = self.objetos.obtener(i)

            if es_pergamino(id_objeto):
                self.pergaminos += 1
            else:
                restantes.agregar(id_objeto)

        self.objetos = restantes
        self._pergaminos_apartados = True

    def cantidad_pergaminos(self):
        return self.pergaminos

    def pergaminos_ya_apartados(self):
        return self._pergaminos_apartados

    def restaurar_contenido(self, contenido, objetos, trampas, pergaminos,
                            pergaminos_apartados):
        """Al cargar una partida guardada (§4.10): el contenido como ESTABA
        al guardar (no como vino del servidor). 'contenido' es el original
        (el que se guarda en la caché); objetos y trampas son Vectores con
        lo que hay ahora. Los enemigos se ponen aparte, con agregar_enemigo:
        pueden estar aquí aunque el contenido no se haya cargado."""
        if self.contenido_cargado():
            raise ValueError(f"La sala {self.id} ya tiene su contenido")

        if pergaminos < 0:
            raise ValueError("La cantidad de pergaminos no puede ser negativa")

        self.contenido = contenido
        self.objetos = objetos
        self.trampas = trampas
        self.pergaminos = pergaminos
        self._pergaminos_apartados = pergaminos_apartados

    def agregar_pergamino(self):
        self.pergaminos += 1

    def quitar_pergamino(self):
        if self.pergaminos == 0:
            raise ValueError(f"No hay pergaminos en la sala {self.id}")

        self.pergaminos -= 1

    def cantidad_trampas(self):
        return len(self.trampas)

    def trampa_en(self, posicion):
        return self.trampas.obtener(posicion)

    def cantidad_enemigos(self):
        return len(self.enemigos)

    def enemigo_en(self, posicion):
        return self.enemigos.obtener(posicion)

    def agregar_enemigo(self, enemigo):
        """Un enemigo entra a esta sala (viene en el contenido o llega
        caminando). Su sala_actual pasa a ser esta."""
        enemigo.sala_actual = self.id
        self.enemigos.agregar(enemigo)

    def insertar_enemigo(self, posicion, enemigo):
        """Lo vuelve a poner en la posición que tenía (para deshacer)."""
        enemigo.sala_actual = self.id
        self.enemigos.insertar(posicion, enemigo)

    def quitar_enemigo(self, enemigo):
        """Saca ESE enemigo de la sala (porque se movió o murió) y devuelve
        la posición que tenía, para poder deshacerlo con insertar_enemigo.

        Se busca con 'is' y no con '==': dos ratas del mismo tipo son
        objetos distintos y hay que quitar la que es. O(k), con k los
        enemigos de esta sala (pocos)."""
        for i in range(len(self.enemigos)):
            if self.enemigos.obtener(i) is enemigo:
                self.enemigos.quitar(i)
                return i

        raise ValueError(
            f"{enemigo.id_instancia} no está en la sala {self.id}"
        )

    def enemigos_dormidos(self):
        """Vector con los enemigos que aún no se activan, en orden
        ascendente de id de instancia. §2.4: si varios se activan en el
        mismo instante, se programan en ese orden para que sus números de
        secuencia sean deterministas."""
        dormidos = Vector()

        for i in range(len(self.enemigos)):
            enemigo = self.enemigos.obtener(i)

            if not enemigo.esta_activo():
                dormidos.agregar(enemigo)

        ordenar(dormidos, clave=lambda enemigo: enemigo.id_instancia)

        return dormidos

    def registrar_rastro(self, tiempo):
        self.ultimo_rastro = tiempo

    def obtener_rastro(self):
        return self.ultimo_rastro