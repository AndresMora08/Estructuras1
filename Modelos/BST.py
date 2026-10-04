from Modelos.Evento import Evento
from Modelos.Nodo import Nodo


class ArbolBST:
    """Plain (unbalanced) binary search tree with the same comparator as the AVL."""

    def __init__(self):
        self.raiz = None

    def insertar(self, evento: Evento, limite_L: int = 3, actualizar: bool = True) -> bool:
        """
        Iterative insertion (an ascending order creates a chain, so recursion
        would overflow). Returns False when the key already exists.
        Accepts optional parameters to match AVL interface during bulk loading.
        """
        nuevo = Nodo(evento)
        if self.raiz is None:
            self.raiz = nuevo
            return True

        actual = self.raiz
        while True:
            if nuevo.clave < actual.clave:
                if actual.izquierda is None:
                    actual.izquierda = nuevo
                    return True
                actual = actual.izquierda
            elif nuevo.clave > actual.clave:
                if actual.derecha is None:
                    actual.derecha = nuevo
                    return True
                actual = actual.derecha
            else:
                return False

    def buscar(self, clave):
        """Returns (node or None, visited nodes)."""
        visitados = 0
        actual = self.raiz
        while actual is not None:
            visitados += 1
            if clave == actual.clave:
                return actual, visitados
            actual = actual.izquierda if clave < actual.clave else actual.derecha
        return None, visitados