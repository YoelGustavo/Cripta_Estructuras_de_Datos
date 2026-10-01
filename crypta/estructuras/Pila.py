from crypta.estructuras.Vector import Vector

class Pila:
    def __init__(self): 
        #usamos el Vector pq nos deja usar la ultima posicion para hacer pop y push
        #asi no hay que andar corriendo el vector.
        self._vector = Vector()

    def __len__(self):
        return len(self._vector)

    def esta_vacia(self):
        return len(self._vector) == 0

    def apilar(self, valor): # push
        # El "tope" de la pila siempre será el final de nuestro vector.
        # Agregar al final toma O(1) amortizado.
        self._vector.agregar(valor)

    def desapilar(self): # pop
        # Interceptamos para dar un mensaje enfocado en la Pila
        if self.esta_vacia():
            raise IndexError("No se puede desapilar: la pila está vacía")
            
        # Sacamos el último elemento que entró (el que está al final del vector)
        return self._vector.quitar_ultimo()

    def ver_tope(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía, no hay tope para ver")
            
        # El tope es el último elemento, que en un vector está en la posición tamaño - 1
        ultimo_indice = len(self._vector) - 1
        return self._vector.obtener(ultimo_indice)

    def descartar_fondo(self): #esto es para el historial de 5 a futuro pq quita el mas viejo.
        if self.esta_vacia():
            raise IndexError("No se puede descartar el fondo: la pila está vacía")    
        # El elemento más viejo está enterrado en el fondo, es decir, en el índice 0.
        # Esto usará el método 'quitar(0)' que desplaza todos los demás a la izquierda O(n).
        self._vector.quitar(0)