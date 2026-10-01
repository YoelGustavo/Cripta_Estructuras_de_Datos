class NodoDoble:
    __slots__ = ("valor", "anterior", "siguiente")
    
    def __init__(self, valor=None):
        self.valor = valor
        self.anterior = None
        self.siguiente = None

class ListaDoble:
    def __init__(self):
        self._centinela = NodoDoble()#cuando se crea apunta a si mismo
        self._centinela.anterior = self._centinela
        self._centinela.siguiente = self._centinela
        self._n = 0

    def __len__(self):
        return self._n

    def esta_vacia(self):
        return self._n == 0

    # =========================================================
    # LOS DOS MOTORES PRINCIPALES (Privados)
    # =========================================================

    def _enlazar_despues(self, ref, nuevo): 
        #esto es para agregar un nodo nuevo despues de otro nodo ref
        # 1. Identificamos quién es el nodo que actualmente está después de 'ref'
        sig = ref.siguiente
        
        # 2. Conectamos 'nuevo' con sus dos nuevos vecinos ('ref' a la izq, 'sig' a la der)
        nuevo.anterior = ref
        nuevo.siguiente = sig
        
        # 3. Actualizamos a los vecinos para que apunten al 'nuevo'
        ref.siguiente = nuevo
        sig.anterior = nuevo
        
        self._n += 1

    def _desenlazar(self, nodo):
        if nodo.anterior is None:
            raise ValueError("Ese nodo no pertenece a la lista (¿ya fue quitado?)")
        # agarrar vecino para borrar.
        ant = nodo.anterior
        sig = nodo.siguiente
        
        # 2. Los conectamos entre ellos, puenteando/ignorando al 'nodo'
        ant.siguiente = sig
        sig.anterior = ant
        #limpia nodos por si la dudas        
        nodo.anterior = None
        nodo.siguiente = None
        
        self._n -= 1


    def agregar_al_frente(self, valor):
        nuevo = NodoDoble(valor)
        # El frente de la lista es justo después del centinela
        self._enlazar_despues(self._centinela, nuevo)
        return nuevo  # DEVOLVEMOS EL NODO para uso externo O(1)

    def agregar_al_final(self, valor):
        nuevo = NodoDoble(valor)
        # El final de la lista es justo después del ÚLTIMO nodo.
        # ¿Quién es el último? El anterior al centinela.
        self._enlazar_despues(self._centinela.anterior, nuevo)
        return nuevo  # DEVOLVEMOS EL NODO

    def quitar_nodo(self, nodo):
        self._desenlazar(nodo)
        return nodo.valor

    def mover_al_frente(self, nodo):
        # Lo saca de donde esté y lo ponemos después del centinela
        self._desenlazar(nodo)
        self._enlazar_despues(self._centinela, nodo)

    def mover_al_final(self, nodo):
        # Lo saca de donde esté y lo ponemos antes del centinela
        self._desenlazar(nodo)
        self._enlazar_despues(self._centinela.anterior, nodo)

    
    def primero(self):
        if self.esta_vacia():
            return None
        return self._centinela.siguiente

    def ultimo(self):
        if self.esta_vacia():
            return None
        return self._centinela.anterior

    def siguiente(self, nodo):
        # Si el siguiente es el centinela, significa que estamos en el último nodo real
        if nodo.siguiente is self._centinela:
            return None
        return nodo.siguiente

    def anterior(self, nodo):
        # Si el anterior es el centinela, significa que estamos en el primer nodo real
        if nodo.anterior is self._centinela:
            return None
        return nodo.anterior

    def __iter__(self):
        # Empezamos en el primer nodo real
        actual = self._centinela.siguiente
        
        # Iteramos hasta volver a toparnos con el centinela
        while actual is not self._centinela:
            yield actual.valor
            actual = actual.siguiente