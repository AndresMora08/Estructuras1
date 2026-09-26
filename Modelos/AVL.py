from collections import deque
from typing import Dict, List, Optional, Tuple
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo


class AVL:

    def __init__(self, modo_estres: bool = False):
        self.raiz: Optional[Nodo] = None
        self.modo_estres: bool = modo_estres

        self.conteo_rotaciones = {
            "LL": 0,
            "RR": 0,
            "LR": 0,
            "RL": 0,
            "giros_simples": 0,
        }

 
    def actualizar_profundidades(self, limite_L: int) -> None:

        self._recorrer_y_actualizar_profundidades(self.raiz, 0, limite_L)

    def _recorrer_y_actualizar_profundidades(
        self, nodo: Optional[Nodo], prof_actual: int, limite_L: int
    ) -> None:
        if nodo is None:
            return

        # 1. Asigna profundidad al nodo e invoca la evaluación en el Evento
        nodo.actualizar_profundidad_y_costo(prof_actual, limite_L)

        # 2. Los hijos directos reciben la profundidad de su nivel + 1
        self._recorrer_y_actualizar_profundidades(
            nodo.izquierda, prof_actual + 1, limite_L
        )
        self._recorrer_y_actualizar_profundidades(
            nodo.derecha, prof_actual + 1, limite_L
        )

 
    def _obtener_altura(self, nodo: Optional[Nodo]) -> int:
        if nodo is None:
            return 0
        return nodo.altura

    def _actualizar_altura(self, nodo: Nodo) -> None:
        nodo.actualizar_altura()

    def _factor_balance(self, nodo: Optional[Nodo]) -> int:
        if nodo is None:
            return 0
        return self._obtener_altura(nodo.izquierda) - self._obtener_altura(
            nodo.derecha
        )

    def _rotacion_derecha(self, y: Nodo) -> Nodo:
        x = y.izquierda
        temporal = x.derecha

        x.derecha = y
        y.izquierda = temporal

        self._actualizar_altura(y)
        self._actualizar_altura(x)

        self.conteo_rotaciones["giros_simples"] += 1
        return x

    def _rotacion_izquierda(self, x: Nodo) -> Nodo:
        y = x.derecha
        temporal = y.izquierda

        y.izquierda = x
        x.derecha = temporal

        self._actualizar_altura(x)
        self._actualizar_altura(y)

        self.conteo_rotaciones["giros_simples"] += 1
        return y

  
    def insertar(self, nodo: Nodo, limite_L: int) -> None:
  
        self.raiz = self._insertar(self.raiz, nodo)
        self.actualizar_profundidades(limite_L)

    def _insertar(
        self, nodo_actual: Optional[Nodo], nuevo_nodo: Nodo
    ) -> Nodo:
        if nodo_actual is None:
            return nuevo_nodo

        if nuevo_nodo.clave < nodo_actual.clave:
            nodo_actual.izquierda = self._insertar(
                nodo_actual.izquierda, nuevo_nodo
            )
        elif nuevo_nodo.clave > nodo_actual.clave:
            nodo_actual.derecha = self._insertar(
                nodo_actual.derecha, nuevo_nodo
            )
        else:
            # Clave duplicada
            return nodo_actual

        self._actualizar_altura(nodo_actual)

        if self.modo_estres:
            return nodo_actual

        balance = self._factor_balance(nodo_actual)

        # Rebalanceo AVL
        if balance > 1 and nuevo_nodo.clave < nodo_actual.izquierda.clave:
            self.conteo_rotaciones["LL"] += 1
            return self._rotacion_derecha(nodo_actual)

        if balance < -1 and nuevo_nodo.clave > nodo_actual.derecha.clave:
            self.conteo_rotaciones["RR"] += 1
            return self._rotacion_izquierda(nodo_actual)

        if balance > 1 and nuevo_nodo.clave > nodo_actual.izquierda.clave:
            self.conteo_rotaciones["LR"] += 1
            nodo_actual.izquierda = self._rotacion_izquierda(
                nodo_actual.izquierda
            )
            return self._rotacion_derecha(nodo_actual)

        if balance < -1 and nuevo_nodo.clave < nodo_actual.derecha.clave:
            self.conteo_rotaciones["RL"] += 1
            nodo_actual.derecha = self._rotacion_derecha(nodo_actual.derecha)
            return self._rotacion_izquierda(nodo_actual)

        return nodo_actual

    # =========================================================================
    # ELIMINACIÓN
    # =========================================================================
    def eliminar(self, clave: Tuple[int, float, int], limite_L: int) -> None:
        """Punto de entrada público para eliminar por la tupla clave (P, M,

        I).
        """
        self.raiz = self._eliminar(self.raiz, clave)
        self.actualizar_profundidades(limite_L)

    def _eliminar(
        self, raiz: Optional[Nodo], clave: Tuple[int, float, int]
    ) -> Optional[Nodo]:
        if raiz is None:
            return None

        # 1. Búsqueda recursiva
        if clave < raiz.evento.clave:
            raiz.izquierda = self._eliminar(raiz.izquierda, clave)
        elif clave > raiz.evento.clave:
            raiz.derecha = self._eliminar(raiz.derecha, clave)
        else:
            # 2. Caso encontrado
            if raiz.es_hoja():
                return None

            if raiz.tiene_dos_hijos():
                sucesor = self._buscar_minimo(raiz.derecha)
                raiz.evento = sucesor.evento
                raiz.clave = sucesor.evento.clave
                raiz.derecha = self._eliminar(
                    raiz.derecha, sucesor.evento.clave
                )
            elif raiz.tiene_hijo_izquierdo():
                return raiz.izquierda
            elif raiz.tiene_hijo_derecho():
                return raiz.derecha

        if raiz is None:
            return None

        # 3. Actualización de altura
        self._actualizar_altura(raiz)

        if self.modo_estres:
            return raiz

        # 4. Rebalanceo
        balance = self._factor_balance(raiz)

        if balance > 1 and self._factor_balance(raiz.izquierda) >= 0:
            self.conteo_rotaciones["LL"] += 1
            return self._rotacion_derecha(raiz)

        if balance > 1 and self._factor_balance(raiz.izquierda) < 0:
            self.conteo_rotaciones["LR"] += 1
            raiz.izquierda = self._rotacion_izquierda(raiz.izquierda)
            return self._rotacion_derecha(raiz)

        if balance < -1 and self._factor_balance(raiz.derecha) <= 0:
            self.conteo_rotaciones["RR"] += 1
            return self._rotacion_izquierda(raiz)

        if balance < -1 and self._factor_balance(raiz.derecha) > 0:
            self.conteo_rotaciones["RL"] += 1
            raiz.derecha = self._rotacion_derecha(raiz.derecha)
            return self._rotacion_izquierda(raiz)

        return raiz

    # =========================================================================
    # MODO ESTRÉS Y RECUPERACIÓN
    # =========================================================================
    def _esta_desbalanceado(self, nodo: Optional[Nodo]) -> bool:
        if nodo is None:
            return False

        if abs(self._factor_balance(nodo)) > 1:
            return True

        return self._esta_desbalanceado(
            nodo.izquierda
        ) or self._esta_desbalanceado(nodo.derecha)

    def _recuperar_equilibrio_nodo(
        self, nodo: Optional[Nodo]
    ) -> Optional[Nodo]:
        if nodo is None:
            return None

        nodo.izquierda = self._recuperar_equilibrio_nodo(nodo.izquierda)
        nodo.derecha = self._recuperar_equilibrio_nodo(nodo.derecha)

        self._actualizar_altura(nodo)
        balance = self._factor_balance(nodo)

        if balance > 1:
            if self._factor_balance(nodo.izquierda) < 0:
                self.conteo_rotaciones["LR"] += 1
                nodo.izquierda = self._rotacion_izquierda(nodo.izquierda)
            else:
                self.conteo_rotaciones["LL"] += 1
            return self._rotacion_derecha(nodo)

        if balance < -1:
            if self._factor_balance(nodo.derecha) > 0:
                self.conteo_rotaciones["RL"] += 1
                nodo.derecha = self._rotacion_derecha(nodo.derecha)
            else:
                self.conteo_rotaciones["RR"] += 1
            return self._rotacion_izquierda(nodo)

        return nodo

    def recuperar_equilibrio(self, limite_L: int) -> None:
        """Rebalancea el árbol tras salir del modo estrés y recalcula las

        profundidades.
        """
        mientras_desbalanceado = True

        while mientras_desbalanceado:
            self.raiz = self._recuperar_equilibrio_nodo(self.raiz)
            mientras_desbalanceado = self._esta_desbalanceado(self.raiz)

        self.modo_estres = False
        self.actualizar_profundidades(limite_L)

  
    def buscar(self, clave: Tuple[int, float, int]) -> Optional[Nodo]:
        return self._buscar(self.raiz, clave)

    def _buscar(
        self, nodo: Optional[Nodo], clave: Tuple[int, float, int]
    ) -> Optional[Nodo]:
        if nodo is None or nodo.clave == clave:
            return nodo

        if clave < nodo.clave:
            return self._buscar(nodo.izquierda, clave)

        return self._buscar(nodo.derecha, clave)

    def _buscar_minimo(self, raiz: Nodo) -> Nodo:
        actual = raiz
        while actual.tiene_hijo_izquierdo():
            actual = actual.izquierda
        return actual