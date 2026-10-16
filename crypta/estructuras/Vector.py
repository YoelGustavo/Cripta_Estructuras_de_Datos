class Vector:
    #Esto es un constructor en python al parecer
    def __init__(self, capacidad=8): #por defecto tendrá 8 pero se puede editar
        self._capacidad = max(1,capacidad)
        self._n = 0 #contador es como tam de c++
        self._array = [None] * self._capacidad #rellena la estructura con puro None mientras

    def __len__(self):
        return self._n #retorna Tam
    
    def _verificar_indice(self, i):#Es como pa ver si esta fuera del vector
        # Método auxiliar para evitar repetición de código
        if i < 0 or i >= self._n:
            raise IndexError(f"Índice {i} fuera de rango. El vector tiene tamaño {self._n}")

    # obtener y asignar revisan el índice aquí mismo, sin llamar a
    # _verificar_indice: son lo que más se ejecuta en todo el programa (el
    # montículo de la agenda las usa en cada evento) y en Python cada
    # llamada a otra función cuesta. Lo midió el --bench (Fase 8).
    def obtener(self, i):
        if i < 0 or i >= self._n:
            raise IndexError(f"Índice {i} fuera de rango. El vector tiene tamaño {self._n}")
        return self._array[i]
    
    def asignar(self, i, valor):  # O(1)
        if i < 0 or i >= self._n:
            raise IndexError(f"Índice {i} fuera de rango. El vector tiene tamaño {self._n}")
        self._array[i] = valor

    def _crecer(self): #duplica capacidad
        #Esta funcion lo q hace es extender el vector por si se queda sin espacio
        nueva_capacidad = self._capacidad * 2
        nuevo_array = [None] * nueva_capacidad
        
        # Copiamos los elementos 1 x 1 (O(n))
        for i in range(self._n):
            nuevo_array[i] = self._array[i]
            
        #cambia los vectores
        self._array = nuevo_array
        self._capacidad = nueva_capacidad

    def agregar(self, valor):
        if self._n == self._capacidad:
            self._crecer()
            
        self._array[self._n] = valor
        self._n += 1

    def quitar_ultimo(self):
        if self._n == 0:
            raise IndexError("No se puede quitar el último elemento de un vector vacío")
            
        # Obtenemos el último valor para retornarlo
        valor = self._array[self._n - 1]        
        self._array[self._n - 1] = None 
        self._n -= 1

        return valor         # O(1)
    
    def insertar(self, i, valor): # desplaza a la derecha, O(n)
        #esto es que lo agrega en cierta posicion y no al final
        if i < 0 or i > self._n:
            raise IndexError(f"Índice {i} fuera de rango para inserción.")
            
        if self._n == self._capacidad:
            self._crecer()
            
        #desplazamiento
        for j in range(self._n, i, -1):
            self._array[j] = self._array[j - 1]
            
        # Una vez hecho el hueco, insertamos el nuevo valor
        self._array[i] = valor
        #mas 1 a tam
        self._n += 1

    def quitar(self, i): # desplaza a la izquierda, O(n)
        #igual q el de insertar pero de eliminar cierto valor en la posicion i
        self._verificar_indice(i)
        valor_eliminado = self._array[i]
        
        # DESPLAZAMIENTO A LA IZQUIERDA:
        for j in range(i, self._n - 1):
            self._array[j] = self._array[j + 1]
            
        # Disminuimos el contador
        self._n -= 1
        # Limpiamos la última posición que quedó duplicada después del desplazamiento
        self._array[self._n] = None 
        
        return valor_eliminado
    