class NodoArbol:
    __slots__ = ("clave", "valor", "izq", "der")
    
    def __init__(self, clave, valor):
        self.clave = clave
        self.valor = valor
        self.izq = None
        self.der = None


class ArbolBusqueda:
    def __init__(self):
        self._raiz = None
        self._n = 0

    def __len__(self):
        return self._n

    def esta_vacio(self):
        return self._n == 0

    def insertar(self, clave, valor):
        if self._raiz is None:
            self._raiz = NodoArbol(clave, valor)
            self._n += 1
            return

        actual = self._raiz
        while True:
            if clave == actual.clave:
                # Caso: Clave repetida. REEMPLAZAMOS el valor, no duplicamos y _n no sube.
                actual.valor = valor
                return
            elif clave < actual.clave:
                if actual.izq is None:
                    actual.izq = NodoArbol(clave, valor)
                    self._n += 1
                    return
                actual = actual.izq
            else:
                if actual.der is None:
                    actual.der = NodoArbol(clave, valor)
                    self._n += 1
                    return
                actual = actual.der

    def obtener(self, clave, defecto=None):
        actual = self._raiz
        while actual is not None:
            if clave == actual.clave:
                return actual.valor
            elif clave < actual.clave:
                actual = actual.izq
            else:
                actual = actual.der
        return defecto

    def contiene(self, clave):
        # Independiente de obtener() para diferenciar si una clave guardó el valor None
        actual = self._raiz
        while actual is not None:
            if clave == actual.clave:
                return True
            elif clave < actual.clave:
                actual = actual.izq
            else:
                actual = actual.der
        return False

    def eliminar(self, clave):
        padre = None
        actual = self._raiz
        #saca el padre del nodo.
        while actual is not None and actual.clave != clave:
            padre = actual
            if clave < actual.clave:
                actual = actual.izq
            else:
                actual = actual.der

        if actual is None:
            return False

        # 2. CASO 3: Tiene DOS hijos
        # Lo simplificamos convirtiéndolo en un caso 1 o 2.
        if actual.izq is not None and actual.der is not None:
            # Buscar el sucesor (uno a la derecha, luego todo a la izquierda)
            padre_suc = actual
            sucesor = actual.der
            while sucesor.izq is not None:
                padre_suc = sucesor
                sucesor = sucesor.izq

            actual.clave = sucesor.clave
            actual.valor = sucesor.valor

            # Ahora nuestro objetivo cambia: debemos borrar al 'sucesor' (que ya copiamos).
            # El sucesor sabemos que tiene a lo sumo UN hijo (el derecho), cayendo en los casos 1 o 2.
            actual = sucesor
            padre = padre_suc

        # 3. CASOS 1 Y 2: Tiene 0 o 1 hijo
        # 'hijo' guardará el único hijo que tiene (o None si es una hoja)
        hijo = actual.izq if actual.izq is not None else actual.der

        # Conectamos al padre directamente con el 'hijo', saltando al nodo 'actual'
        if padre is None:
            # Caso especial: estamos borrando la raíz
            self._raiz = hijo
        elif padre.izq is actual:
            padre.izq = hijo
        else:
            padre.der = hijo

        self._n -= 1
        return True

    def _en_orden_nodo(self, nodo):
        # Caso base
        if nodo is None:
            return

        # Llamadas recursivas clásicas
        yield from self._en_orden_nodo(nodo.izq)
        yield (nodo.clave, nodo.valor)
        yield from self._en_orden_nodo(nodo.der)

    def en_orden(self): #se separa la funcion publica.
        yield from self._en_orden_nodo(self._raiz)

    def _altura_nodo(self, nodo):
        # Caso base
        if nodo is None:
            return 0
        
        # Paso recursivo: 1 + la altura del lado más alto
        return 1 + max(self._altura_nodo(nodo.izq), self._altura_nodo(nodo.der))

    def altura(self):
        # La función pública delega el cálculo a partir de la raíz
        return self._altura_nodo(self._raiz)

    # =========================================================
    # CONSTRUCTOR DE ÁRBOL BALANCEADO
    # =========================================================

    @staticmethod
    def _construir_balanceado(vector_de_pares, inicio, fin):
        # Caso base: rango inválido, no hay nodo que crear
        if inicio > fin:
            return None

        # Punto medio
        medio = (inicio + fin) // 2
        clave, valor = vector_de_pares.obtener(medio)
        nodo = NodoArbol(clave, valor)

        # Paso recursivo: construir subárboles
        nodo.izq = ArbolBusqueda._construir_balanceado(vector_de_pares, inicio, medio - 1)
        nodo.der = ArbolBusqueda._construir_balanceado(vector_de_pares, medio + 1, fin)

        return nodo

    @staticmethod
    def desde_ordenados(vector_de_pares):
        arbol = ArbolBusqueda()
        arbol._n = len(vector_de_pares)
        
        # Inicia la construcción recursiva pasándole el rango completo (0 a n-1)
        arbol._raiz = ArbolBusqueda._construir_balanceado(vector_de_pares, 0, arbol._n - 1)
        return arbol