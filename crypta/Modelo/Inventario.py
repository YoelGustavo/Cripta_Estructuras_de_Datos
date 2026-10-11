from crypta.estructuras.ListaDoble import ListaDoble
from crypta.estructuras.ordenamiento import copiar_a_vector, ordenar


# Clase de la ficha de los pergaminos de retroceso (§2.7 y §2.11).
CLASE_PERGAMINO = "pergamino_retroceso"

# Lo único que se puede equipar (§2.7). La clase de la ficha es también
# el nombre de la "ranura": una para el arma y otra para la armadura.
CLASES_EQUIPABLES = ("arma", "armadura")


class ContextoSoltar:
    def __init__(self, nodo, anterior, ranura=None):
        self.nodo = nodo
        self.anterior = anterior
        self.objeto = nodo.valor
        # "arma" o "armadura" si lo que se soltó estaba equipado; None si no.
        self.ranura = ranura

class ContextoEquipar:
    def __init__(self, nodo, anterior, ranura=None, equipado_antes=None):
        self.nodo = nodo            # el nodo que se movió al frente
        self.anterior = anterior
        self.ranura = ranura                  # "arma" o "armadura"
        self.equipado_antes = equipado_antes  # nodo que estaba equipado ahí (o None)

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

        # Lo equipado (§2.7: como máximo un arma y una armadura). Se guarda
        # el NODO y no la ficha: dos dagas son la misma ficha (el mismo
        # dict), pero cada una está en su propio nodo. Así se sabe cuál de
        # las dos es la equipada, y soltar la otra no la desequipa.
        self._arma = None
        self._armadura = None

        # Pergaminos de retroceso: una CANTIDAD aparte, fuera de la
        # ListaDoble. §2.11 los excluye del estado reversible (ni usarlos,
        # ni recogerlos, ni soltarlos se deshace). Si fueran nodos de la
        # lista, quitar uno sin deshacerlo dejaría a otros contextos de
        # deshacer apuntando a un vecino que ya no está (se cae). Con un
        # contador no hay vecinos ni posiciones que se desordenen.
        self._pergaminos = 0

    def __len__(self):
        """Objetos de la lista (sin contar los pergaminos)."""
        return len(self._objetos)

    def ocupados(self):
        """Posiciones usadas: §2.7 "cada objeto ocupa una posición", y un
        pergamino también es un objeto."""
        return len(self._objetos) + self._pergaminos

    def esta_vacio(self):
        return self._objetos.esta_vacia()

    def esta_lleno(self):
        return self.ocupados() >= self._capacidad

    def capacidad(self):
        return self._capacidad

    def espacio_disponible(self):
        return self._capacidad - self.ocupados()

    # =========================================================
    # PERGAMINOS DE RETROCESO (§2.11 y §4.6)
    # =========================================================
    # Ninguno de estos métodos devuelve un contexto para deshacer: a
    # propósito, porque nada de esto se registra en el historial.

    def cantidad_pergaminos(self):
        return self._pergaminos

    def tiene_pergamino(self):
        return self._pergaminos > 0

    def consumir_pergamino(self):
        """Gasta uno al usarlo. Devuelve False si no había."""
        if self._pergaminos == 0:
            return False

        self._pergaminos -= 1
        return True

    def recoger_pergamino_de(self, sala):
        """Pasa un pergamino del suelo de la sala al inventario."""
        if sala.cantidad_pergaminos() == 0 or self.esta_lleno():
            return False

        sala.quitar_pergamino()
        self._pergaminos += 1
        return True

    def soltar_pergamino_en(self, sala):
        """Deja un pergamino en el suelo de la sala."""
        if self._pergaminos == 0:
            return False

        self._pergaminos -= 1
        sala.agregar_pergamino()
        return True

    def fijar_pergaminos(self, cantidad):
        """Pone la cantidad directamente (al cargar una partida guardada,
        o en pruebas)."""
        if cantidad < 0 or len(self._objetos) + cantidad > self._capacidad:
            raise ValueError(
                f"No caben {cantidad} pergaminos en el inventario"
            )

        self._pergaminos = cantidad

    def buscar_por_id(self, id_objeto):
        """La ficha del primer objeto con ese id, o None. Recorre la lista:
        O(n), con n <= inventario_max (unos pocos objetos). Sirve, por
        ejemplo, para saber si el jugador tiene la llave de una puerta."""
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
        # Igual que soltar_actual_con_contexto, pero sin devolver el
        # contexto (así no hay dos versiones de la misma lógica).
        contexto = self.soltar_actual_con_contexto()

        if contexto is None:
            return None

        return contexto.objeto

    # =========================================================
    # EQUIPO (§2.7 y §4.5)
    # =========================================================

    def arma(self):
        """La ficha del arma equipada, o None."""
        return None if self._arma is None else self._arma.valor

    def armadura(self):
        """La ficha de la armadura equipada, o None."""
        return None if self._armadura is None else self._armadura.valor

    def actual_esta_equipado(self):
        """Para que la vista marque el objeto que se está viendo."""
        return self._ranura_de(self._actual) is not None

    def _ranura_de(self, nodo):
        """En qué ranura está equipado ese nodo, o None si no lo está."""
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
        """Equipa el objeto que se está viendo: lo mueve al frente del
        orden real (§4.5) y lo pone en su ranura. Si ya había otra arma
        (o armadura), esa queda desequipada pero sigue en el inventario
        (§2.7). Todo es O(1)."""
        if self._actual is None:
            return None

        nodo = self._actual
        ranura = nodo.valor.get("clase")

        if ranura not in CLASES_EQUIPABLES:
            raise ValueError(
                f"{nodo.valor.get('nombre', nodo.valor.get('id'))} no se "
                f"puede equipar: solo armas y armaduras"
            )

        # Se guarda todo lo necesario para deshacer ANTES de cambiar nada:
        # quién estaba antes en la lista y qué estaba equipado.
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

        # Se saca del frente y vuelve justo después de su vecino de antes.
        # Es el mismo truco del paso anterior: el MISMO nodo, en O(1).
        self._objetos.quitar_nodo(contexto.nodo)

        self._objetos.reinsertar_despues(
            contexto.nodo,
            contexto.anterior
        )

        self._actual = contexto.nodo

        # Vuelve a estar equipado lo que estaba antes (o nada).
        if contexto.ranura is not None:
            self._poner_en(contexto.ranura, contexto.equipado_antes)

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

        # Lo que sale del inventario deja de estar equipado.
        ranura = self._ranura_de(nodo)

        if ranura is not None:
            self._poner_en(ranura, None)

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
        # Un pergamino nunca entra a la lista (ver __init__).
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

        # Guardamos quién está antes: O(1), sin recorrer la lista.
        siguiente = self._objetos.siguiente(nodo)
        anterior = self._objetos.anterior(nodo)

        if siguiente is not None:
            self._actual = siguiente
        elif anterior is not None:
            self._actual = anterior
        else:
            self._actual = None

        self._objetos.quitar_nodo(nodo)

        # Si estaba equipado, se desequipa (y se anota para deshacer).
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

        # Vuelve el MISMO nodo, justo después del que tenía antes.
        # Como se deshace en orden inverso, ese vecino ya está de vuelta
        # en la lista (y también es el mismo nodo de siempre).
        self._objetos.reinsertar_despues(
            contexto.nodo,
            contexto.anterior
        )

        self._actual = contexto.nodo

        # Si estaba equipado cuando se soltó, vuelve a estarlo.
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

        # Sale exactamente el nodo que entró al recoger.
        self.quitar_nodo(
            contexto.nodo_inventario
        )

        # El ID vuelve exactamente a su posición
        # original en el suelo.
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