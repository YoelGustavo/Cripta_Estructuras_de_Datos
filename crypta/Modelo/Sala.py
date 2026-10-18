from crypta.Modelo.Enemigo import Enemigo
from crypta.Modelo.Puerta import Puerta
from crypta.Modelo.Trampa import Trampa
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar


DIRECCIONES = "NSEO"


def indice_direccion(direccion):
    if not isinstance(direccion, str) or len(direccion) != 1:
        return -1

    return DIRECCIONES.find(direccion)


class Sala:
    def __init__(self, id_sala, nombre, salidas):
        self.id = id_sala
        self.nombre = nombre

        self._puertas = Vector(len(DIRECCIONES))

        for _ in range(len(DIRECCIONES)):
            self._puertas.agregar(None)

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

        self.enemigos = Vector()

        self.pergaminos = 0
        self._pergaminos_apartados = False

        self.ultimo_rastro = None

    def obtener_puerta(self, direccion):
        indice = indice_direccion(direccion)

        if indice < 0:
            return None

        return self._puertas.obtener(indice)

    def puertas(self, solo_abiertas=False):
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
        indice = indice_direccion(direccion)

        if indice < 0:
            raise ValueError(f"Dirección inválida: {direccion!r}")

        if self._puertas.obtener(indice) is not None:
            raise ValueError(f"La sala {self.id} ya tiene salida hacia {direccion}")

        self._puertas.asignar(indice, puerta)

    def direccion_de(self, puerta):
        for i in range(len(DIRECCIONES)):
            if self._puertas.obtener(i) is puerta:
                return DIRECCIONES[i]

        return None


    def contenido_cargado(self):
        return self.contenido is not None

    def asignar_contenido(self, contenido):
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


    def apartar_pergaminos(self, es_pergamino):
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
        enemigo.sala_actual = self.id
        self.enemigos.agregar(enemigo)

    def insertar_enemigo(self, posicion, enemigo):
        enemigo.sala_actual = self.id
        self.enemigos.insertar(posicion, enemigo)

    def quitar_enemigo(self, enemigo):
        for i in range(len(self.enemigos)):
            if self.enemigos.obtener(i) is enemigo:
                self.enemigos.quitar(i)
                return i

        raise ValueError(
            f"{enemigo.id_instancia} no está en la sala {self.id}"
        )

    def enemigos_dormidos(self):
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