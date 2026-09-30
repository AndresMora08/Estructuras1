from collections import deque
from datetime import datetime as Datetime, datetime, timezone
from typing import Dict, List, Optional, Tuple
from copy import deepcopy

from Modelos.AVL import AVL
from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Zona import Zona


class Escenario:

    def __init__(
        self,
        zonas: List[Zona] = [],
        estaciones: List[Estacion] = [],
        epicentros: List[Epicentro] = [],
        reloj: Optional[Datetime] = None,
        arbol_avl: Optional[AVL] = None,
    ):
        self.zonas: List[Zona] = zonas
        self.estaciones: List[Estacion] = estaciones
        self.epicentros: List[Epicentro] = epicentros

        self.reloj = reloj if reloj is not None else datetime.now(timezone.utc)
        self.arbol_avl = arbol_avl if arbol_avl is not None else AVL()
        self.cola_reportes = deque()
        self.historico: List[Evento] = []
        self.dict_eventos: Dict[int, Evento] = {}

        self.W: float = 48.0
        self.R: float = 40.0
        self.L: int = 3
        self.T: float = 72.0

        # Pila de historial para deshacer operaciones (JSON, borrados, etc.)
        self.pila_deshacer = []

    def guardar_estado_pila(self):
        """Guarda un snapshot del estado actual antes de modificar el escenario."""
        snapshot = {
            "zonas": list(self.zonas),
            "estaciones": list(self.estaciones),
            "epicentros": list(self.epicentros),
            "reloj": self.reloj,
            "raiz_avl": deepcopy(self.arbol_avl.raiz) if self.arbol_avl else None,
            "dict_eventos": dict(self.dict_eventos),
            "cola_reportes": deque(self.cola_reportes),
            "historico": list(self.historico),
            "W": self.W,
            "R": self.R,
            "L": self.L,
            "T": self.T
        }
        self.pila_deshacer.append(snapshot)

    def deshacer_ultima_accion(self) -> bool:
        """Restaura el estado del escenario a la versión anterior guardada en la pila."""
        if not self.pila_deshacer:
            return False

        snapshot = self.pila_deshacer.pop()
        self.zonas = snapshot["zonas"]
        self.estaciones = snapshot["estaciones"]
        self.epicentros = snapshot["epicentros"]
        self.reloj = snapshot["reloj"]
        
        if not self.arbol_avl:
            self.arbol_avl = AVL()
        self.arbol_avl.raiz = snapshot["raiz_avl"]
        
        self.dict_eventos = snapshot["dict_eventos"]
        self.cola_reportes = snapshot["cola_reportes"]
        self.historico = snapshot["historico"]
        self.W = snapshot["W"]
        self.R = snapshot["R"]
        self.L = snapshot["L"]
        self.T = snapshot["T"]
        return True

    def eliminar_evento_por_id(self, id_evento: int) -> Tuple[bool, str]:
        """
        Elimina un evento individual del árbol AVL y del diccionario de eventos activos,
        marca su estado_catalogo como 'Retirado' y lo traslada al historial.
        """
        if id_evento not in self.dict_eventos:
            return False, f"El evento ID {id_evento} no existe en los eventos activos."

        evento = self.dict_eventos[id_evento]

        try:
            self.guardar_estado_pila()

            # 1. Eliminar del árbol AVL si está inicializado
            if self.arbol_avl and hasattr(evento, "clave"):
                self.arbol_avl.eliminar(evento.clave, self.L)

            # 2. Remover del diccionario de eventos activos
            del self.dict_eventos[id_evento]

            # 3. Actualizar estado de catálogo a 'Retirado' y trasladar al histórico
            evento.estado_catalogo = "Retirado"
            self.historico.append(evento)

            return True, f"Evento SIS-{id_evento:06d} retirado del catálogo exitosamente."

        except Exception as e:
            return False, f"Error al eliminar el evento: {str(e)}"

    def archivar_evento_por_id(self, id_evento: int):
        """
        Verifica la rama del evento seleccionado. Si es archivable, elimina sus nodos del
        árbol mediante self.arbol_avl.eliminar(clave, L), traslada los eventos a self.historico
        marcando su estado_catalogo = "Archivado".
        """
        if not self.arbol_avl or not self.arbol_avl.raiz:
            return False, "El árbol AVL no está inicializado o está vacío.", None

        # 1. Búsqueda en el diccionario activo
        if id_evento not in self.dict_eventos:
            return False, f"El evento ID {id_evento} no existe en los eventos activos.", None

        # 2. Localizar nodo y su profundidad
        nodo_target, prof_target = self.arbol_avl.buscar_nodo_y_profundidad(id_evento)
        if not nodo_target:
            return False, f"El evento ID {id_evento} no se encontró físicamente en el árbol AVL.", None

        # 3. Comprobar si todo el subárbol colgado es elegible
        if not self.arbol_avl.es_nodo_archivable(nodo_target, self.reloj, self.T):
            return False, f"La rama con raíz ID {id_evento} NO es elegible (todos sus nodos deben ser Prioridad 1 y tener antigüedad > {self.T}h).", None

        eventos_a_archivar = self.arbol_avl.obtener_subarbol_eventos(nodo_target)
        cant_nodos = len(eventos_a_archivar)
        ids_afectados = [e.id for e in eventos_a_archivar]

        # Justificación explicativa
        justificacion = (
            f"Selección de rama elegible para archivo con raíz ID {id_evento}:\n"
            f"- Cantidad de eventos afectados: {cant_nodos}\n"
            f"- Profundidad de la raíz en el árbol: Nivel {prof_target}\n"
            f"- Identificadores afectados: {ids_afectados}"
        )

        # 4. Guardar respaldo previo
        self.guardar_estado_pila()

        # 5. Eliminar cada evento del subárbol usando eliminar(clave, limite_L)
        for ev in eventos_a_archivar:
            self.arbol_avl.eliminar(ev.clave, self.L)
            if ev.id in self.dict_eventos:
                del self.dict_eventos[ev.id]
            ev.estado_catalogo = "Archivado"
            self.historico.append(ev)

        return True, justificacion, ids_afectados

    def deshacer_ultimo_archivado(self):
        """Restablece el estado mediante la pila genérica."""
        return self.deshacer_ultima_accion()

    def _clonar_arbol(self, raiz):
        """Clona la estructura del árbol."""
        if raiz is None:
            return None
        return deepcopy(raiz)