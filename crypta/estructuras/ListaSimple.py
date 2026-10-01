
class NodoSimple:
    __slots__ = ("valor", "siguiente")

    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None

class ListaSimple:
    def __init__(self):
        self._frente = None
        self._final = None
        self._n = 0

    def __len__(self): #retorna la cant de elementos de la lista
        return self._n

    def esta_vacia(self):
        return self._n == 0

    def agregar_al_final(self, valor): #O(1)
        nuevo_nodo = NodoSimple(valor)
        
        if self.esta_vacia():
            self._frente = nuevo_nodo
            self._final = nuevo_nodo
        else:
            self._final.siguiente = nuevo_nodo
            self._final = nuevo_nodo
            
        self._n += 1

    def agregar_al_frente(self, valor): #O(1)
        nuevo_nodo = NodoSimple(valor)
        
        if self.esta_vacia():
            self._frente = nuevo_nodo
            self._final = nuevo_nodo
        else:
            nuevo_nodo.siguiente = self._frente
            self._frente = nuevo_nodo
            
        self._n += 1

    def ver_frente(self): #O(1)
        if self.esta_vacia():
            raise IndexError("La lista está vacía")
        return self._frente.valor #retorna el valor del primer nodo

    def quitar_del_frente(self): #O(1) - quita el primer nodo de la lista y retorna su valor
        if self.esta_vacia():
            raise IndexError("No se puede quitar de una lista vacía")
            
        valor = self._frente.valor
        
        self._frente = self._frente.siguiente
        self._n -= 1
        
        # ¡Ojo aquí! Si al quitar el elemento la lista quedó vacía, 
        # también debemos limpiar el puntero _final
        if self.esta_vacia():
            self._final = None
            
        return valor

    def contiene(self, valor): #O(n) - verifica si un valor está en la lista
        actual = self._frente
        
        while actual is not None:
            if actual.valor == valor:
                return True
            actual = actual.siguiente
            
        return False

    def quitar(self, valor): #O(n)
        if self.esta_vacia():
            return False

        # Caso especial 1: ¿El valor que buscamos está de primero?
        if self._frente.valor == valor:
            self.quitar_del_frente()
            return True

        # Para quitar un nodo en el medio, necesitamos pararnos en el nodo ANTERIOR.
        actual = self._frente
        
        # Mientras haya un siguiente nodo al que mirar...
        while actual.siguiente is not None:
            if actual.siguiente.valor == valor:
                # ¡Lo encontramos! Nos saltamos el nodo que queremos borrar.
                # Hacemos que el actual apunte al "siguiente del siguiente".
                actual.siguiente = actual.siguiente.siguiente
                self._n -= 1
                
                # Caso especial 2: ¿Borramos el último elemento? 
                # Si es así, debemos actualizar nuestro puntero _final
                if actual.siguiente is None:
                    self._final = actual
                    
                return True
                
            # Avanzamos al siguiente nodo
            actual = actual.siguiente
            
        return False



    def __iter__(self):
        # Esta función mágica (generador) le permite a Python usar nuestra lista en ciclos 'for'.
        # yield actúa como un "pausa y entrega el valor", luego retoma desde aquí.
        actual = self._frente
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente
