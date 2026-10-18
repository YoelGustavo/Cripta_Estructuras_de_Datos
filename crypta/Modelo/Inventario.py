from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import copiar_a_vector, ordenar


CLASE_PERGAMINO = "pergamino_retroceso"

CLASES_EQUIPABLES = ("arma", "armadura")


class ContextoSoltar:
    def __init__(self, nodo, anterior, ranura=None):
        self.nodo = nodo
        self.anterior = anterior
        self.objeto = nodo.valor
        self.ranura = ranura

class ContextoEquipar:
    def __init__(self, nodo, anterior, ranura=None, equipado_antes=None):
        self.nodo = nodo          
        self.anterior = anterior
        self.ranura = ranura         
        self.equipado_antes = equipado_antes

class ContextoRecoger:

    def __init__(
        self,
        sala,
        posicion_suelo,
        id_objeto,
        nodo_inventario
    ):
        self.sala = sala
        self.posicion_suelo = posicion_suelo
        self.id_objeto = id_objeto
        self.nodo_inventario = nodo_inventario

class ContextoSoltarEnSala:
    def __init__(
        self,
        sala,
        contexto_inventario,
        posicion_suelo
    ):
        self.sala = sala
        self.contexto_inventario = contexto_inventario
        self.posicion_suelo = posicion_suelo

class Inventario:

    def __init__(self, capacidad):
        if capacidad < 1:
            raise ValueError(
                "La capacidad del inventario debe ser mayor que 0"
            )

        self._capacidad = capacidad
        self._objetos = ListaDoble()

        self._actual = None

        self._arma = None
        self._armadura = None
        self._pergaminos = 0

    def __len__(self):
        return len(self._objetos)

    def ocupados(self):
        return len(self._objetos) + self._pergaminos

    def esta_vacio(self):
        return self._objetos.esta_vacia()

    def esta_lleno(self):
        return self.ocupados() >= self._capacidad

    def capacidad(self):
        return self._capacidad

    def espacio_disponible(self):
        return self._capacidad - self.ocupados()


    def cantidad_pergaminos(self):
        return self._pergaminos

    def tiene_pergamino(self):
        return self._pergaminos > 0

    def consumir_pergamino(self):
        if self._pergaminos == 0:
            return False

        self._pergaminos -= 1
        return True

    def recoger_pergamino_de(self, sala):
        if sala.cantidad_pergaminos() == 0 or self.esta_lleno():
            return False

        sala.quitar_pergamino()
        self._pergaminos += 1
        return True

    def soltar_pergamino_en(self, sala):
        if self._pergaminos == 0:
            return False

        self._pergaminos -= 1
        sala.agregar_pergamino()
        return True

    def fijar_pergaminos(self, cantidad):
        if cantidad < 0 or len(self._objetos) + cantidad > self._capacidad:
            raise ValueError(
                f"No caben {cantidad} pergaminos en el inventario"
            )

        self._pergaminos = cantidad

    def buscar_por_id(self, id_objeto):
        for objeto in self._objetos:
            if objeto.get("id") == id_objeto:
                return objeto

        return None

    def actual(self):
        if self._actual is None:
            return None

        return self._actual.valor

    def avanzar(self):
        if self._actual is None:
            return None

        siguiente = self._objetos.siguiente(
            self._actual
        )

        if siguiente is None:
            return None

        self._actual = siguiente

        return self._actual.valor

    def retroceder(self):
        if self._actual is None:
            return None

        anterior = self._objetos.anterior(
            self._actual
        )

        if anterior is None:
            return None

        self._actual = anterior

        return self._actual.valor

    def soltar_actual(self):
        contexto = self.soltar_actual_con_contexto()

        if contexto is None:
            return None

        return contexto.objeto


    def arma(self):
        return None if self._arma is None else self._arma.valor

    def armadura(self):
        return None if self._armadura is None else self._armadura.valor

    def actual_esta_equipado(self):
        return self._ranura_de(self._actual) is not None

    def _ranura_de(self, nodo):
        if nodo is None:
            return None

        if nodo is self._arma:
            return "arma"

        if nodo is self._armadura:
            return "armadura"

        return None

    def _nodo_en(self, ranura):
        return self._arma if ranura == "arma" else self._armadura

    def _poner_en(self, ranura, nodo):
        if ranura == "arma":
            self._arma = nodo
        else:
            self._armadura = nodo

    def equipar_actual(self):
        contexto = self.equipar_actual_con_contexto()

        if contexto is None:
            return None

        return contexto.nodo.valor

    def equipar_actual_con_contexto(self):
        if self._actual is None:
            return None

        nodo = self._actual
        ranura = nodo.valor.get("clase")

        if ranura not in CLASES_EQUIPABLES:
            raise ValueError(
                f"{nodo.valor.get('nombre', nodo.valor.get('id'))} no se "
                f"puede equipar: solo armas y armaduras"
            )

        contexto = ContextoEquipar(
            nodo,
            self._objetos.anterior(nodo),
            ranura,
            self._nodo_en(ranura)
        )

        self._objetos.mover_al_frente(nodo)
        self._poner_en(ranura, nodo)

        return contexto

    def restaurar_equipado(self, contexto):
        if contexto is None:
            return

        self._objetos.quitar_nodo(contexto.nodo)

        self._objetos.reinsertar_despues(
            contexto.nodo,
            contexto.anterior
        )

        self._actual = contexto.nodo

        if contexto.ranura is not None:
            self._poner_en(contexto.ranura, contexto.equipado_antes)

    def posiciones(self):
        actual = arma = armadura = -1
        nodo = self._objetos.primero()
        posicion = 0

        while nodo is not None:
            if nodo is self._actual:
                actual = posicion
            if nodo is self._arma:
                arma = posicion
            if nodo is self._armadura:
                armadura = posicion

            nodo = self._objetos.siguiente(nodo)
            posicion += 1

        return actual, arma, armadura

    def restaurar(self, objetos, actual, arma, armadura, pergaminos):
        if not self.esta_vacio() or self._pergaminos != 0:
            raise ValueError("Solo se puede restaurar un inventario vacío")

        nodos = Vector()

        for i in range(len(objetos)):
            nodo = self.recoger_con_nodo(objetos.obtener(i))

            if nodo is None:
                raise ValueError(f"No caben {len(objetos)} objetos en el inventario")

            nodos.agregar(nodo)

        for posicion in (actual, arma, armadura):
            if not -1 <= posicion < len(nodos):
                raise ValueError(f"Posición {posicion} fuera del inventario")

        if (actual == -1) != (len(nodos) == 0):
            raise ValueError("Con objetos, siempre hay uno a la vista (y sin objetos, ninguno)")

        self._actual = nodos.obtener(actual) if actual != -1 else None

        for ranura, posicion in (("arma", arma), ("armadura", armadura)):
            if posicion == -1:
                continue

            if nodos.obtener(posicion).valor.get("clase") != ranura:
                raise ValueError(f"El objeto {posicion} no es un(a) {ranura}")

            self._poner_en(ranura, nodos.obtener(posicion))

        self.fijar_pergaminos(pergaminos)

    def orden_real(self):
        resultado = []

        for objeto in self._objetos:
            resultado.append(objeto)

        return resultado

    def vista_ordenada(self, criterio):
        vista = copiar_a_vector(self._objetos)

        if criterio == "peso":
            clave = lambda objeto: objeto["peso"]
            comparacion_costosa = False

        elif criterio == "valor":
            clave = lambda objeto: objeto["valor"]
            comparacion_costosa = False

        elif criterio == "nombre":
            clave = lambda objeto: objeto["nombre"].lower()
            comparacion_costosa = True

        else:
            raise ValueError(
                "Criterio inválido. Use: peso, valor o nombre"
            )

        algoritmo = ordenar(
            vista,
            clave=clave,
            comparacion_costosa=comparacion_costosa
        )

        return vista, algoritmo

    def quitar_nodo(self, nodo):
        if nodo is None:
            return None

        ranura = self._ranura_de(nodo)

        if ranura is not None:
            self._poner_en(ranura, None)

        if self._actual is nodo:
            siguiente = self._objetos.siguiente(nodo)
            anterior = self._objetos.anterior(nodo)

            if siguiente is not None:
                self._actual = siguiente
            elif anterior is not None:
                self._actual = anterior
            else:
                self._actual = None

        return self._objetos.quitar_nodo(nodo)


    def restaurar_antes(self, referencia, objeto):
        nodo = self._objetos.insertar_antes(
            referencia,
            objeto
        )

        return nodo


    def restaurar_despues(self, referencia, objeto):
        nodo = self._objetos.insertar_despues(
            referencia,
            objeto
        )

        return nodo

    def recoger_con_nodo(self, objeto):
        if objeto.get("clase") == CLASE_PERGAMINO:
            raise ValueError(
                "Los pergaminos de retroceso se recogen con "
                "recoger_pergamino_de, no como un objeto más"
            )

        if self.esta_lleno():
            return None

        nodo = self._objetos.agregar_al_final(
            objeto
        )

        if self._actual is None:
            self._actual = nodo

        return nodo

    def recoger(self, objeto):
        return self.recoger_con_nodo(objeto) is not None

    def soltar_actual_con_contexto(self):
        if self._actual is None:
            return None

        nodo = self._actual

        siguiente = self._objetos.siguiente(nodo)
        anterior = self._objetos.anterior(nodo)

        if siguiente is not None:
            self._actual = siguiente
        elif anterior is not None:
            self._actual = anterior
        else:
            self._actual = None

        self._objetos.quitar_nodo(nodo)

        ranura = self._ranura_de(nodo)

        if ranura is not None:
            self._poner_en(ranura, None)

        return ContextoSoltar(
            nodo,
            anterior,
            ranura
        )

    def restaurar_soltado(self, contexto):
        if contexto is None:
            return

        self._objetos.reinsertar_despues(
            contexto.nodo,
            contexto.anterior
        )

        self._actual = contexto.nodo

        if contexto.ranura is not None:
            self._poner_en(contexto.ranura, contexto.nodo)

    def recoger_desde_sala(
        self,
        sala,
        posicion,
        objeto
    ):
        if self.esta_lleno():
            return None

        id_objeto = sala.quitar_objeto(
            posicion
        )

        nodo = self.recoger_con_nodo(
            objeto
        )

        if nodo is None:
            sala.insertar_objeto(
                posicion,
                id_objeto
            )
            return None

        return ContextoRecoger(
            sala,
            posicion,
            id_objeto,
            nodo
        )


    def deshacer_recogida(self, contexto):
        if contexto is None:
            return

        self.quitar_nodo(
            contexto.nodo_inventario
        )

        contexto.sala.insertar_objeto(
            contexto.posicion_suelo,
            contexto.id_objeto
        )

    def soltar_en_sala(self, sala):
        if self._actual is None:
            return None

        contexto_inventario = (
            self.soltar_actual_con_contexto()
        )

        if contexto_inventario is None:
            return None

        objeto = contexto_inventario.objeto
        id_objeto = objeto["id"]

        posicion_suelo = sala.cantidad_objetos()

        sala.agregar_objeto(
            id_objeto
        )

        return ContextoSoltarEnSala(
            sala,
            contexto_inventario,
            posicion_suelo
        )


    def deshacer_soltar_en_sala(self, contexto):
        if contexto is None:
            return

        contexto.sala.quitar_objeto(
            contexto.posicion_suelo
        )

        self.restaurar_soltado(
            contexto.contexto_inventario
        )