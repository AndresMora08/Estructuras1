from collections import deque
from typing import List, Optional, Tuple


def nodos_por_niveles(raiz) -> list:
    """Level-order list of nodes (iterative)."""
    resultado = []
    if raiz is None:
        return resultado
    cola = deque([raiz])
    while cola:
        nodo = cola.popleft()
        resultado.append(nodo)
        if nodo.izquierda is not None:
            cola.append(nodo.izquierda)
        if nodo.derecha is not None:
            cola.append(nodo.derecha)
    return resultado


def altura(raiz) -> int:
    """Height with the project convention: empty = -1, leaf = 0."""
    if raiz is None:
        return -1
    niveles = 0
    actual = [raiz]
    while actual:
        niveles += 1
        siguiente = []
        for nodo in actual:
            if nodo.izquierda is not None:
                siguiente.append(nodo.izquierda)
            if nodo.derecha is not None:
                siguiente.append(nodo.derecha)
        actual = siguiente
    return niveles - 1


def contar_hojas(raiz) -> int:
    return sum(1 for n in nodos_por_niveles(raiz) if n.izquierda is None and n.derecha is None)


def costo_busqueda(raiz, clave) -> Tuple[Optional[object], int]:
    """
    Searches a key from the root. Returns (node or None, visited nodes).
    For an existing node, visited = depth + 1.
    """
    visitados = 0
    actual = raiz
    while actual is not None:
        visitados += 1
        if clave == actual.clave:
            return actual, visitados
        actual = actual.izquierda if clave < actual.clave else actual.derecha
    return None, visitados


def estadisticas_busqueda(raiz) -> dict:
    """Cost of searching every stored key: total, average and maximum (depth + 1)."""
    if raiz is None:
        return {"total": 0, "promedio": 0.0, "maximo": 0}
    total = 0
    maximo = 0
    cantidad = 0
    cola = deque([(raiz, 1)])
    while cola:
        nodo, costo = cola.popleft()
        total += costo
        cantidad += 1
        maximo = max(maximo, costo)
        if nodo.izquierda is not None:
            cola.append((nodo.izquierda, costo + 1))
        if nodo.derecha is not None:
            cola.append((nodo.derecha, costo + 1))
    return {"total": total, "promedio": total / cantidad, "maximo": maximo}


def resumen(raiz) -> dict:
    """Structural summary used to compare AVL and BST."""
    nodos = nodos_por_niveles(raiz)
    h = altura(raiz)
    busqueda = estadisticas_busqueda(raiz)
    return {
        "raiz": raiz.evento.id if raiz is not None else None,
        "nodos": len(nodos),
        "altura": h,
        "profundidad_maxima": h,
        "hojas": contar_hojas(raiz),
        "comparaciones_total": busqueda["total"],
        "comparaciones_promedio": busqueda["promedio"],
        "comparaciones_maximo": busqueda["maximo"],
    }


def eventos_costosos(raiz, limite_L: int) -> Tuple[List[dict], int]:
    """
    High-priority events (P = 3) whose node depth is strictly greater than L.

    Pruning by K = (P, M, I): the left subtree of a node holds only smaller
    keys, so if the node has P < 3 everything on its left has P < 3 and cannot
    qualify; that branch is skipped. Returns (results, visited nodes).
    """
    if raiz is None or limite_L < 0:
        return [], 0

    resultados = []
    visitados = 0
    pila = [(raiz, 0)]
    while pila:
        nodo, profundidad = pila.pop()
        visitados += 1
        evento = nodo.evento
        if evento.prioridad == 3 and profundidad > limite_L:
            resultados.append({
                "evento": evento,
                "profundidad_nodo": profundidad,
                "limite_L": limite_L,
                "nodos_visitados_busqueda": profundidad + 1,
            })
        if nodo.derecha is not None:
            pila.append((nodo.derecha, profundidad + 1))
        if nodo.izquierda is not None and evento.prioridad == 3:
            pila.append((nodo.izquierda, profundidad + 1))

    resultados.sort(key=lambda r: r["evento"].clave, reverse=True)
    return resultados, visitados