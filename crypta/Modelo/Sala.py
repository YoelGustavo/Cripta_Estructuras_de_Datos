from crypta.Modelo.Puerta import Puerta
from crypta.estructuras.Vector import Vector
from crypta.Modelo.Trampa import Trampa


class Sala:
    def __init__(self, id_sala, nombre, salidas):
        self.id = id_sala
        self.nombre = nombre

        self.salidas = {}

        for direccion, datos in salidas.items():
            self.salidas[direccion] = Puerta(
                sala_destino=datos["sala"],
                cerrada=bool(datos.get("cerrada")),
                llave=datos.get("llave"),
                cierre_automatico=datos.get(
                    "cierre_automatico"
                )
            )

        self.contenido = None
        self.objetos = Vector()
        self.trampas = Vector()

        # Instante del último rastro dejado por el jugador.
        # None significa que el jugador nunca ha estado en esta sala.
        self.ultimo_rastro = None

    def contenido_cargado(self):
        return self.contenido is not None

    def asignar_contenido(self, contenido):
        self.contenido = contenido

        # Reconstruimos los objetos del suelo.
        self.objetos = Vector()
        self.trampas = Vector()

        for id_objeto in contenido.get("objetos") or []:
            self.objetos.agregar(id_objeto)

        for datos_trampa in contenido.get("trampas") or []:
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

    def obtener_puerta(self, direccion):
        return self.salidas.get(direccion)

    def cantidad_trampas(self):
        return len(self.trampas)

    def trampa_en(self, posicion):
        return self.trampas.obtener(posicion)

    def registrar_rastro(self, tiempo):
        self.ultimo_rastro = tiempo

    def obtener_rastro(self):
        return self.ultimo_rastro