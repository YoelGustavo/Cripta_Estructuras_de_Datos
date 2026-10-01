from crypta.estructuras.ListaSimple import ListaSimple

class Cola:
    def __init__(self, capacidad_max=None):
    # None = sin tope. Un tope de 0 o negativo no tiene sentido:
    # se avisa al crear la cola, no después al encolar.
        if capacidad_max is not None and capacidad_max < 1:
            raise ValueError("La capacidad máxima de la cola debe ser al menos 1")
        self._lista = ListaSimple()
        self._capacidad_max = capacidad_max

    

    def __len__(self):
        return len(self._lista)

    def esta_vacia(self):
        return self._lista.esta_vacia()

    def encolar(self, valor): #enqueue
        if self._capacidad_max is not None:
            if len(self._lista) == self._capacidad_max:
                self._lista.quitar_del_frente()                
        # El nuevo siempre entra por la puerta de atrás (el final)
        self._lista.agregar_al_final(valor)

    def desencolar(self): #dequeue
        # Nuestra función 'quitar_del_frente' en ListaSimple ya está programada usamos esa misma
        return self._lista.quitar_del_frente()

    def ver_frente(self):
        return self._lista.ver_frente() #usamos la de la lista simple

    def __iter__(self):
        # Como nuestra ListaSimple ya tiene la función mágica __iter__, 
        # va a recorrer desde _frente hasta _final (es decir, del más viejo al más nuevo).
        # Podemos usar 'yield' para ir pasando esos valores.
        for elemento in self._lista:
            yield elemento