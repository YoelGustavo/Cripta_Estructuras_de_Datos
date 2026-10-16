from crypta.estructuras.Vector import Vector


def _menor_por_defecto(a, b):
    return a < b

class MonticuloMin:
    def __init__(self, menor=None):
        if menor is not None:
            self._menor = menor
        else:
            self._menor = _menor_por_defecto
        self._vector = Vector()

    def __len__(self):
        return len(self._vector)

    def esta_vacia(self):
        return len(self._vector) == 0

    def __iter__(self):
        """Recorre los elementos en el orden del arreglo interno, que NO es
        el orden de menor a mayor. O(n). Sirve para revisarlos todos sin
        sacarlos (por ejemplo, para guardar la agenda)."""
        for i in range(len(self._vector)):
            yield self._vector.obtener(i)

    #operaciones para sacar padres e hijos.
    def _padre(self, i):
        return (i - 1) // 2

    def _hijo_izq(self, i):
        return 2 * i + 1

    def _hijo_der(self, i):
        return 2 * i + 2

    # _subir y _bajar usan la técnica del "HUECO" (Fase 8, la encontró el
    # --bench): en vez de INTERCAMBIAR en cada nivel (2 lecturas y 2
    # escrituras), se guarda aparte el elemento que se mueve, se corren los
    # demás un nivel y el elemento se escribe UNA sola vez, en su lugar
    # final. Es el mismo algoritmo (deja el arreglo exactamente igual que
    # con intercambios), con un tercio de los accesos al vector. La agenda
    # saca un evento por cada turno de cada actor: es lo que más se repite
    # en todo el juego.

    def _subir(self, i):
        # "Flotamos" el elemento hacia arriba mientras sea menor que su padre
        vector = self._vector
        elemento = vector.obtener(i)

        while i > 0:
            p = self._padre(i)
            padre = vector.obtener(p)

            if not self._menor(elemento, padre):
                break  # ya encontró su lugar

            vector.asignar(i, padre)  # el padre baja al hueco...
            i = p                     # ...y el hueco sube

        vector.asignar(i, elemento)

    def _bajar(self, i):
        # "Hundimos" el elemento hacia abajo mientras algún hijo sea menor
        vector = self._vector
        n = len(vector)
        elemento = vector.obtener(i)

        while True:
            izq = self._hijo_izq(i)

            if izq >= n:
                break  # sin hijos: es una hoja

            # El menor de los dos hijos (el derecho, si existe y es menor).
            hijo = izq
            valor_hijo = vector.obtener(izq)
            der = izq + 1

            if der < n:
                valor_der = vector.obtener(der)

                if self._menor(valor_der, valor_hijo):
                    hijo = der
                    valor_hijo = valor_der

            if not self._menor(valor_hijo, elemento):
                break  # el elemento es menor (o igual) que sus dos hijos

            vector.asignar(i, valor_hijo)  # el hijo sube al hueco...
            i = hijo                       # ...y el hueco baja

        vector.asignar(i, elemento)


    def insertar(self, valor):
        self._vector.agregar(valor)        
        self._subir(len(self._vector) - 1)
        #primero se agrega al final y luego se sube hasta su lugar correcto.

    def ver_min(self):
        if self.esta_vacia():
            raise IndexError("El montículo está vacío, no se puede ver el mínimo")
            
        # O(1): En un Min-Heap, el menor de todos SIEMPRE es la raíz (índice 0)
        return self._vector.obtener(0)

    def extraer_min(self):
        if self.esta_vacia():
            raise IndexError("El montículo está vacío, no se puede extraer el mínimo")
            
        # Caso especial: Si solo hay un elemento, lo quitamos directamente sin hacer reajustes
        if len(self._vector) == 1:
            return self._vector.quitar_ultimo()
            
        # 1. Guardamos el verdadero mínimo (la raíz) para devolverlo al final
        minimo = self._vector.obtener(0)
        
        # 2. Tomamos el elemento que está al fondo del árbol (el final del vector)
        ultimo_valor = self._vector.quitar_ultimo()
        
        # 3. Y lo ponemos a la fuerza en la raíz
        self._vector.asignar(0, ultimo_valor)
        
        # 4. O(log n): Como ese elemento seguramente no es el menor, lo hacemos "hundirse"
        self._bajar(0)
        
        return minimo