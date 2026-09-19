from Modelos.Evento import Evento
from Modelos.Nodo import Nodo

class ArbolBST:
    def __init__(self):
        self.raiz = None

    def insertar(self, evento: Evento):
        if self.raiz is None:
            self.raiz = Nodo(evento)
        else:
            self._insertar_recursivo(self.raiz, evento)

    def _insertar_recursivo(self, nodo_actual: Nodo, evento: Evento):
        # Comparamos usando la tupla 'clave', igual que el AVL de tu compañero
        if evento.clave < nodo_actual.clave:
            if nodo_actual.izquierda is None:
                nodo_actual.izquierda = Nodo(evento)
            else:
                self._insertar_recursivo(nodo_actual.izquierda, evento)
        else:
            if nodo_actual.derecha is None:
                nodo_actual.derecha = Nodo(evento)
            else:
                self._insertar_recursivo(nodo_actual.derecha, evento)