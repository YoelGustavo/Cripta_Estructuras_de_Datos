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

    def _intercambiar(self, i, j):
        temp_i = self._vector.obtener(i)
        temp_j = self._vector.obtener(j)
        
        self._vector.asignar(i, temp_j)
        self._vector.asignar(j, temp_i)

    def _subir(self, i):
        # "Flotamos" el elemento hacia arriba mientras no sea la raíz
        while i > 0:
            p = self._padre(i)
            # Si el elemento actual es MENOR que su padre, rompe la regla, así que los cambiamos
            if self._menor(self._vector.obtener(i), self._vector.obtener(p)):
                self._intercambiar(i, p)
                i = p  # Actualizamos nuestra posición a la del padre para seguir subiendo
            else:
                break  # Si no es menor que el padre, ya encontró su lugar correcto

    def _bajar(self, i):
        # "Hundimos" el elemento hacia abajo
        n = len(self._vector)
        while True:
            izq = self._hijo_izq(i)
            der = self._hijo_der(i)
            mas_pequeno = i

            # Si el hijo izquierdo existe y es menor que el actual, él es el nuevo candidato a subir
            if izq < n and self._menor(self._vector.obtener(izq), self._vector.obtener(mas_pequeno)):
                mas_pequeno = izq

            # Si el hijo derecho existe y es menor que el candidato anterior, él gana
            if der < n and self._menor(self._vector.obtener(der), self._vector.obtener(mas_pequeno)):
                mas_pequeno = der

            # Si el más pequeño ya no es el actual (alguno de los hijos ganó), los intercambiamos
            if mas_pequeno != i:
                self._intercambiar(i, mas_pequeno)
                i = mas_pequeno  # Seguimos bajando desde la nueva posición
            else:
                break  # Si el actual es menor que ambos hijos, terminamos


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