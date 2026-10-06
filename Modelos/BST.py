
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo


class ArbolBST:
    """Simple binary search tree, without balancing."""

    def __init__(self):
        self.raiz = None
        self.modo_estres = False

    def insertar(
        self,
        evento: Evento,
        limite_L: int = 3,
        actualizar: bool = True
    ) -> bool:
        """
        Inserts an event using the same key/comparator as the AVL.

        Does not perform rotations because the BST must remain
        unbalanced when appropriate.
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
        """
        Searches for a key.

        Returns:
            (node, number_of_visited_nodes)
        """
        visitados = 0
        actual = self.raiz

        while actual is not None:
            visitados += 1

            if clave == actual.clave:
                return actual, visitados

            if clave < actual.clave:
                actual = actual.izquierda
            else:
                actual = actual.derecha

        return None, visitados

    def eliminar(
        self,
        clave,
        limite_L: int = 3
    ) -> bool:
        """
        Removes a node from the BST.

        Does not perform rotations.
        """
        padre = None
        actual = self.raiz

        # Search for the node
        while actual is not None and actual.clave != clave:
            padre = actual

            if clave < actual.clave:
                actual = actual.izquierda
            else:
                actual = actual.derecha

        if actual is None:
            return False

        # ----------------------------------------------------------
        # CASE 1: leaf node
        # ----------------------------------------------------------
        if actual.izquierda is None and actual.derecha is None:
            self._reemplazar_hijo(
                padre,
                actual,
                None
            )

        # ----------------------------------------------------------
        # CASE 2: only right child
        # ----------------------------------------------------------
        elif actual.izquierda is None:
            self._reemplazar_hijo(
                padre,
                actual,
                actual.derecha
            )

        # ----------------------------------------------------------
        # CASE 3: only left child
        # ----------------------------------------------------------
        elif actual.derecha is None:
            self._reemplazar_hijo(
                padre,
                actual,
                actual.izquierda
            )

        # ----------------------------------------------------------
        # CASE 4: has two children
        # ----------------------------------------------------------
        else:
            sucesor_padre = actual
            sucesor = actual.derecha

            while sucesor.izquierda is not None:
                sucesor_padre = sucesor
                sucesor = sucesor.izquierda

            # Copy the successor's event
            actual.evento = sucesor.evento

            # The successor can have at most a right child
            if sucesor_padre.izquierda is sucesor:
                sucesor_padre.izquierda = sucesor.derecha
            else:
                sucesor_padre.derecha = sucesor.derecha

        return True

    def _reemplazar_hijo(
        self,
        padre,
        nodo,
        nuevo_hijo
    ):
        """Replaces the link from the parent to a node."""

        # The deleted node was the root
        if padre is None:
            self.raiz = nuevo_hijo
            return

        if padre.izquierda is nodo:
            padre.izquierda = nuevo_hijo
        else:
            padre.derecha = nuevo_hijo

    def altura(self) -> int:
        """Returns the tree height. Empty tree = -1."""

        def calcular(nodo):
            if nodo is None:
                return -1

            izquierda = calcular(nodo.izquierda)
            derecha = calcular(nodo.derecha)

            return 1 + max(izquierda, derecha)

        return calcular(self.raiz)

    def factor_balance(self, nodo) -> int:
        """
        Calculates the balance factor of a node.

        It is included to maintain a useful interface similar to the AVL,
        although the BST does not use this value for rotations.
        """

        if nodo is None:
            return 0

        def altura_subarbol(actual):
            if actual is None:
                return -1

            return 1 + max(
                altura_subarbol(actual.izquierda),
                altura_subarbol(actual.derecha)
            )

        return (
            altura_subarbol(nodo.izquierda)
            - altura_subarbol(nodo.derecha)
        )

    def actualizar_profundidades(
        self,
        limite_L: int = 3
    ):
        """
        Updates the heights of the BST nodes.

        Does not balance or rotate the tree.
        """

        def actualizar(nodo):
            if nodo is None:
                return -1

            altura_izquierda = actualizar(
                nodo.izquierda
            )

            altura_derecha = actualizar(
                nodo.derecha
            )

            nodo.altura = 1 + max(
                altura_izquierda,
                altura_derecha
            )

            return nodo.altura

        actualizar(self.raiz)

    def obtener_nodos(self):
        """Returns all BST nodes in in-order traversal."""

        resultado = []

        def recorrer(nodo):
            if nodo is None:
                return

            recorrer(nodo.izquierda)
            resultado.append(nodo)
            recorrer(nodo.derecha)

        recorrer(self.raiz)

        return resultado