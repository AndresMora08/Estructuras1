from Modelos.Evento import Evento
from Modelos.Nodo import Nodo


class ArbolBST:
    """Árbol binario de búsqueda simple, sin balanceo."""

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
        Inserta un evento usando la misma clave/comparador del AVL.

        No realiza rotaciones porque el BST debe permanecer
        desbalanceado cuando corresponda.
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
        Busca una clave.

        Retorna:
            (nodo, cantidad_visitados)
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
        Elimina un nodo del BST.

        No realiza rotaciones.
        """
        padre = None
        actual = self.raiz

        # Buscar nodo
        while actual is not None and actual.clave != clave:
            padre = actual

            if clave < actual.clave:
                actual = actual.izquierda
            else:
                actual = actual.derecha

        if actual is None:
            return False

        # ----------------------------------------------------------
        # CASO 1: nodo hoja
        # ----------------------------------------------------------
        if actual.izquierda is None and actual.derecha is None:
            self._reemplazar_hijo(
                padre,
                actual,
                None
            )

        # ----------------------------------------------------------
        # CASO 2: solo hijo derecho
        # ----------------------------------------------------------
        elif actual.izquierda is None:
            self._reemplazar_hijo(
                padre,
                actual,
                actual.derecha
            )

        # ----------------------------------------------------------
        # CASO 3: solo hijo izquierdo
        # ----------------------------------------------------------
        elif actual.derecha is None:
            self._reemplazar_hijo(
                padre,
                actual,
                actual.izquierda
            )

        # ----------------------------------------------------------
        # CASO 4: tiene dos hijos
        # ----------------------------------------------------------
        else:
            sucesor_padre = actual
            sucesor = actual.derecha

            while sucesor.izquierda is not None:
                sucesor_padre = sucesor
                sucesor = sucesor.izquierda

            # Copiamos el evento del sucesor
            actual.evento = sucesor.evento

            # El sucesor tendrá como máximo hijo derecho
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
        """Reemplaza el enlace del padre hacia un nodo."""

        # El nodo eliminado era la raíz
        if padre is None:
            self.raiz = nuevo_hijo
            return

        if padre.izquierda is nodo:
            padre.izquierda = nuevo_hijo
        else:
            padre.derecha = nuevo_hijo

    def altura(self) -> int:
        """Retorna la altura del árbol. Árbol vacío = -1."""

        def calcular(nodo):
            if nodo is None:
                return -1

            izquierda = calcular(nodo.izquierda)
            derecha = calcular(nodo.derecha)

            return 1 + max(izquierda, derecha)

        return calcular(self.raiz)

    def factor_balance(self, nodo) -> int:
        """
        Calcula el factor de balance de un nodo.

        Se incluye para mantener una interfaz útil similar al AVL,
        aunque el BST no utiliza este valor para hacer rotaciones.
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
        Actualiza las alturas de los nodos del BST.

        No balancea ni rota el árbol.
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
        """Retorna todos los nodos del BST en recorrido inorden."""

        resultado = []

        def recorrer(nodo):
            if nodo is None:
                return

            recorrer(nodo.izquierda)
            resultado.append(nodo)
            recorrer(nodo.derecha)

        recorrer(self.raiz)

        return resultado