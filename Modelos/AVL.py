from collections import deque
from typing import Optional, List, Tuple, Dict
from .Nodo import Nodo
from .Evento import Evento


class AVL:

    def __init__(self, modo_estres: bool = False):
        self.raiz: Optional[Nodo] = None
        self.modo_estres: bool = modo_estres

        # Contadores de métricas exigidos por el PDF
        self.conteo_rotaciones = {
            "LL": 0,
            "RR": 0,
            "LR": 0,
            "RL": 0,
            "giros_simples": 0,
        }

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
    
    def insertar(self, nodo: Nodo) -> None:
        """Recibe una instancia de Nodo ya creada y la inserta en el árbol."""
        self.raiz = self._insertar(self.raiz, nodo)

    def _insertar(self, nodo_actual: Optional[Nodo], nuevo_nodo: Nodo) -> Nodo:
        if nodo_actual is None:
            return nuevo_nodo

        # Comparación lexicográfica utilizando la tupla clave = (P, M, I)
        if nuevo_nodo.clave < nodo_actual.clave:
            nodo_actual.izquierda = self._insertar(nodo_actual.izquierda, nuevo_nodo)
        elif nuevo_nodo.clave > nodo_actual.clave:
            nodo_actual.derecha = self._insertar(nodo_actual.derecha, nuevo_nodo)
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
            nodo_actual.izquierda = self._rotacion_izquierda(nodo_actual.izquierda)
            return self._rotacion_derecha(nodo_actual)

        if balance < -1 and nuevo_nodo.clave < nodo_actual.derecha.clave:
            self.conteo_rotaciones["RL"] += 1
            nodo_actual.derecha = self._rotacion_derecha(nodo_actual.derecha)
            return self._rotacion_izquierda(nodo_actual)

        return nodo_actual
    
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

        # Rebalancear subárboles primero (post-orden)
        nodo.izquierda = self._recuperar_equilibrio_nodo(nodo.izquierda)
        nodo.derecha = self._recuperar_equilibrio_nodo(nodo.derecha)

        self._actualizar_altura(nodo)
        balance = self._factor_balance(nodo)

        # Si hay desbalance, aplicamos las rotaciones requeridas
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

    def recuperar_equilibrio(self) -> None:
        """Aplica rotaciones a un árbol degradado en modo estrés hasta cumplir la propiedad AVL."""
        mientras_desbalanceado = True

        while mientras_desbalanceado:
            self.raiz = self._recuperar_equilibrio_nodo(self.raiz)
            mientras_desbalanceado = self._esta_desbalanceado(self.raiz)

        self.modo_estres = False
        
    def mostrar_arbol_consola(self) -> None:
        """Muestra el árbol de forma horizontal/espaciada.

        Arriba: Subárbol Derecho (Valores mayores)
        Centro: Raíz / Nodo actual
        Abajo: Subárbol Izquierdo (Valores menores)
        """
        if self.raiz is None:
            print("\n[ ÁRBOL AVL VACÍO ]\n")
            return

        print("\n" + "=" * 60)
        self._imprimir_nodo_espaciado(self.raiz, nivel=0)
        print("=" * 60 + "\n")

    def _imprimir_nodo_espaciado(
        self, nodo: Optional[Nodo], nivel: int
    ) -> None:
        if nodo is None:
            return

        # 1. Procesar primero el hijo DERECHO (se imprime arriba)
        self._imprimir_nodo_espaciado(nodo.derecha, nivel + 1)

        # 2. Imprimir el NODO ACTUAL con sangría según su nivel de profundidad
        espacios = "         " * nivel  # 9 espacios por nivel
        
        # Formato claro del nodo
        info = f"[ID:{nodo.evento.id} | K={nodo.clave} | H:{nodo.altura}]"

        if nivel == 0:
            print(f"RAÍZ ──> {info}")
        else:
            print(f"{espacios}└── {info}")

        # Separador vertical suave para dar más aire entre ramas
        print(f"{espacios}    │")

        # 3. Procesar el hijo IZQUIERDO (se imprime abajo)
        self._imprimir_nodo_espaciado(nodo.izquierda, nivel + 1)
        
        
    def _buscar_minimo(self, raiz: Nodo) -> Nodo:
            actual = raiz
            while actual.tiene_hijo_izquierdo():
              actual = actual.izquierda
            return actual
        
    def eliminar(self, clave: Tuple[int, float, int]) -> None:
        """Punto de entrada público para eliminar por la tupla clave (P, M, I)."""
        self.raiz = self._eliminar(self.raiz, clave)

    def _eliminar(
        self,
        raiz: Optional[Nodo],
        clave: Tuple[int, float, int]
    ) -> Optional[Nodo]:

        if raiz is None:
            return None

        # 1. BÚSQUEDA RECURSIVA POR CLAVE (P, M, I)
        if clave < raiz.evento.clave:
            raiz.izquierda = self._eliminar(raiz.izquierda, clave)

        elif clave > raiz.evento.clave:
            raiz.derecha = self._eliminar(raiz.derecha, clave)

        else:
            # 2. CASO ENCONTRADO: EVALUACIÓN DE CASOS DE ELIMINACIÓN

            # Caso 1: Nodo Hoja (sin hijos)
            if raiz.es_hoja():
                return None

            # Caso 2: Tiene dos hijos
            if raiz.tiene_dos_hijos():
                sucesor = self._buscar_minimo(raiz.derecha)
                
                # Reemplazamos la instancia del evento (su clave cambia automáticamente)
                raiz.evento = sucesor.evento

                # Eliminamos el sucesor de la rama derecha usando su clave
                raiz.derecha = self._eliminar(raiz.derecha, sucesor.evento.clave)

            # Caso 3: Solo tiene un hijo (Izquierdo)
            elif raiz.tiene_hijo_izquierdo():
                return raiz.izquierda

            # Caso 4: Solo tiene un hijo (Derecho)
            elif raiz.tiene_hijo_derecho():
                return raiz.derecha

        # Si el subárbol quedó vacío
        if raiz is None:
            return None

        # 3. ACTUALIZACIÓN DE ALTURA
        self._actualizar_altura(raiz)

        # Si estamos en modo estrés, omitimos rebalanceo inmediato
        if self.modo_estres:
            return raiz

        # 4. REBALANCEO AVL Y CONTEO DE ROTACIONES
        balance = self._factor_balance(raiz)

        # Caso LL
        if balance > 1 and self._factor_balance(raiz.izquierda) >= 0:
            self.conteo_rotaciones["LL"] += 1
            return self._rotacion_derecha(raiz)

        # Caso LR
        if balance > 1 and self._factor_balance(raiz.izquierda) < 0:
            self.conteo_rotaciones["LR"] += 1
            raiz.izquierda = self._rotacion_izquierda(raiz.izquierda)
            return self._rotacion_derecha(raiz)

        # Caso RR
        if balance < -1 and self._factor_balance(raiz.derecha) <= 0:
            self.conteo_rotaciones["RR"] += 1
            return self._rotacion_izquierda(raiz)

        # Caso RL
        if balance < -1 and self._factor_balance(raiz.derecha) > 0:
            self.conteo_rotaciones["RL"] += 1
            raiz.derecha = self._rotacion_derecha(raiz.derecha)
            return self._rotacion_izquierda(raiz)

        return raiz
    
    def buscar(self, clave: Tuple[int, float, int]) -> Optional[Nodo]:
        """Búsqueda eficiente en el AVL usando la tupla clave O(log n)."""
        return self._buscar(self.raiz, clave)

    def _buscar(self, nodo: Optional[Nodo], clave: Tuple[int, float, int]) -> Optional[Nodo]:
        if nodo is None or nodo.clave == clave:
            return nodo

        if clave < nodo.clave:
            return self._buscar(nodo.izquierda, clave)

        return self._buscar(nodo.derecha, clave)