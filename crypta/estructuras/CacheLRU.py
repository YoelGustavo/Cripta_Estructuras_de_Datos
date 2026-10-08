from crypta.estructuras.ArbolBusqueda import ArbolBusqueda
from crypta.estructuras.ListaDoble import ListaDoble
 
 
class _EntradaCache:
    __slots__ = ("id", "ficha", "usos", "nodo")
 
    def __init__(self, id_tipo, ficha):
        self.id = id_tipo
        self.ficha = ficha
        self.usos = 0      # cuántas instancias activas la usan ahora
        self.nodo = None   # su nodo en la lista de desalojables (None = está en uso)


class CacheLRU:
    def __init__(self, capacidad=25):
        if capacidad <= 0:
            raise ValueError(
                "La capacidad debe ser mayor que 0"
            )
 
        self._capacidad = capacidad
        self._indice = ArbolBusqueda()
        self._desalojables = ListaDoble()
 
    def contiene(self, id_tipo):
        return self._indice.contiene(id_tipo)
 
    def obtener(self, id_tipo):
        entrada = self._indice.obtener(id_tipo)
 
        if entrada is None:
            return None
 
        self._usar(entrada)
        return entrada.ficha
 
    def insertar(self, id_tipo, ficha):
        entrada = self._indice.obtener(id_tipo)
 
        # Si ya existe, actualizamos la ficha (y cuenta como uso).
        if entrada is not None:
            entrada.ficha = ficha
            self._usar(entrada)
            return None
 
        desalojada = None
 
        # Se hace espacio ANTES de agregar: la nueva nunca se desaloja a sí misma.
        if len(self._indice) >= self._capacidad:
            desalojada = self._desalojar_si_es_posible()
 
        entrada = _EntradaCache(id_tipo, ficha)
        entrada.nodo = self._desalojables.agregar_al_final(entrada)
        self._indice.insertar(id_tipo, entrada)
 
        return desalojada
 
    def _usar(self, entrada):
        # La más reciente va al final. Si está en uso no está en la lista.
        if entrada.nodo is not None:
            self._desalojables.mover_al_final(entrada.nodo)
 
    def _desalojar_si_es_posible(self):
        # Todas están en uso: se permite pasar el tope temporalmente.
        if self._desalojables.esta_vacia():
            return None
 
        # La del frente es la que lleva más tiempo sin usarse.
        entrada = self._desalojables.quitar_nodo(
            self._desalojables.primero()
        )
        entrada.nodo = None
        self._indice.eliminar(entrada.id)
 
        return entrada.id, entrada.ficha
 
    def marcar_en_uso(self, id_tipo):
        entrada = self._indice.obtener(id_tipo)
 
        if entrada is None:
            return
 
        entrada.usos += 1
 
        # Primer uso: sale de la lista de desalojables.
        if entrada.nodo is not None:
            self._desalojables.quitar_nodo(entrada.nodo)
            entrada.nodo = None
 
    def liberar(self, id_tipo):
        entrada = self._indice.obtener(id_tipo)
 
        if entrada is None or entrada.usos == 0:
            return
 
        entrada.usos -= 1
 
        # Ya nadie la usa: vuelve a ser desalojable, como la más reciente.
        if entrada.usos == 0:
            entrada.nodo = self._desalojables.agregar_al_final(entrada)
 
    def esta_en_uso(self, id_tipo):
        entrada = self._indice.obtener(id_tipo)
        return entrada is not None and entrada.usos > 0
 
    def cantidad(self):
        return len(self._indice)
 
    def capacidad(self):
        return self._capacidad
 
    def esta_llena(self):
        return len(self._indice) >= self._capacidad