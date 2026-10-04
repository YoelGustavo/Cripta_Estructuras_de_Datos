from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.ordenamiento import copiar_a_vector, ordenar


class ContextoSoltar:
    def __init__(self, objeto, anterior, siguiente):
        self.objeto = objeto
        self.anterior = anterior
        self.siguiente = siguiente

class ContextoEquipar:
    def __init__(self, nodo, anterior, siguiente):
        self.nodo = nodo
        self.anterior = anterior
        self.siguiente = siguiente

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

        # Nodo que el jugador está viendo actualmente.
        self._actual = None

    def __len__(self):
        return len(self._objetos)

    def esta_vacio(self):
        return self._objetos.esta_vacia()

    def esta_lleno(self):
        return len(self._objetos) >= self._capacidad

    def capacidad(self):
        return self._capacidad

    def espacio_disponible(self):
        return self._capacidad - len(self._objetos)

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
        if self._actual is None:
            return None

        nodo_eliminar = self._actual

        # Decidimos cuál será la nueva posición actual
        # ANTES de quitar el nodo.
        siguiente = self._objetos.siguiente(
            nodo_eliminar
        )

        anterior = self._objetos.anterior(
            nodo_eliminar
        )

        if siguiente is not None:
            self._actual = siguiente

        elif anterior is not None:
            self._actual = anterior

        else:
            self._actual = None

        return self._objetos.quitar_nodo(
            nodo_eliminar
        )

    def equipar_actual(self):
        if self._actual is None:
            return None

        self._objetos.mover_al_frente(
            self._actual
        )

        return self._actual.valor

    def orden_real(self):
        resultado = []

        for objeto in self._objetos:
            resultado.append(objeto)

        return resultado

    def vista_ordenada(self, criterio):
        # Creamos una copia del orden real.
        # Así nunca modificamos la ListaDoble del inventario.
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

        # Si justamente estamos viendo este nodo,
        # elegimos una nueva posición actual.
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
        objeto = nodo.valor

        anterior = self._objetos.anterior(nodo)
        siguiente = self._objetos.siguiente(nodo)

        contexto = ContextoSoltar(
            objeto,
            anterior,
            siguiente
        )

        if siguiente is not None:
            self._actual = siguiente
        elif anterior is not None:
            self._actual = anterior
        else:
            self._actual = None

        self._objetos.quitar_nodo(nodo)

        return contexto


    def restaurar_soltado(self, contexto):
        if contexto is None:
            return

        objeto = contexto.objeto
        anterior = contexto.anterior
        siguiente = contexto.siguiente

        if siguiente is not None:
            nodo = self._objetos.insertar_antes(
                siguiente,
                objeto
            )

        elif anterior is not None:
            nodo = self._objetos.insertar_despues(
                anterior,
                objeto
            )

        else:
            nodo = self._objetos.agregar_al_final(
                objeto
            )

        self._actual = nodo

    def equipar_actual_con_contexto(self):
        if self._actual is None:
            return None

        nodo = self._actual

        anterior = self._objetos.anterior(nodo)
        siguiente = self._objetos.siguiente(nodo)

        contexto = ContextoEquipar(
            nodo,
            anterior,
            siguiente
        )

        self._objetos.mover_al_frente(nodo)

        return contexto

    def restaurar_equipado(self, contexto):
        if contexto is None:
            return

        nodo = contexto.nodo
        anterior = contexto.anterior
        siguiente = contexto.siguiente

        if siguiente is not None:
            self._objetos.mover_antes(
                nodo,
                siguiente
            )

        elif anterior is not None:
            self._objetos.mover_despues(
                nodo,
                anterior
            )

        # Si no tenía anterior ni siguiente,
        # era el único objeto y no hay nada que mover.

        self._actual = nodo

    def recoger_desde_sala(
        self,
        sala,
        posicion,
        objeto
    ):
        if self.esta_lleno():
            return None

        # Primero quitamos el ID del suelo.
        id_objeto = sala.quitar_objeto(
            posicion
        )

        # La ficha completa entra al inventario.
        nodo = self.recoger_con_nodo(
            objeto
        )

        # Por seguridad: si por alguna razón no pudo entrar,
        # restauramos inmediatamente el suelo.
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

        # Sale del inventario.
        self.quitar_nodo(
            contexto.nodo_inventario
        )

        # Regresa exactamente a su posición anterior
        # en el suelo.
        contexto.sala.insertar_objeto(
            contexto.posicion_suelo,
            contexto.id_objeto
        )

    def soltar_en_sala(self, sala):
        if self._actual is None:
            return None

        # Primero guardamos y quitamos el objeto
        # del inventario.
        contexto_inventario = (
            self.soltar_actual_con_contexto()
        )

        if contexto_inventario is None:
            return None

        objeto = contexto_inventario.objeto
        id_objeto = objeto["id"]

        # Lo dejamos al final del suelo.
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

        # Quitamos del suelo el objeto que
        # apareció al soltarlo.
        contexto.sala.quitar_objeto(
            contexto.posicion_suelo
        )

        # Lo restauramos en su posición exacta
        # dentro del inventario.
        self.restaurar_soltado(
            contexto.contexto_inventario
        )