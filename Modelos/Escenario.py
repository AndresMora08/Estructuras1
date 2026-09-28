from collections import deque
from datetime import datetime as Datetime, datetime, timezone
from typing import Dict, List, Optional, Tuple

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
        self.arbol_avl = arbol_avl
        self.cola_reportes = deque()
        self.historico: List[Evento] = []
        self.dict_eventos: Dict[int, Evento] = {}

        self.W: float = 48.0
        self.R: float = 40.0
        self.L: int = 3
        self.T: float = 72.0

    def archivar_evento_por_id(self, id_evento: int):
        """
        Verifica la rama del evento seleccionado. Si es archivable, elimina sus nodos del
        árbol mediante self.arbol_avl.eliminar(clave, L), traslada los eventos a self.historico
        y guarda copia de respaldo para deshacer.
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

        # 4. Guardar respaldo previo para la acción de deshacer
        self._respaldo_previo_archivo = {
            "raiz_avl": self._clonar_arbol(self.arbol_avl.raiz),
            "dict_eventos": dict(self.dict_eventos),
            "historico": list(self.historico)
        }

        # 5. Eliminar cada evento del subárbol usando TU MÉTODO eliminar(clave, limite_L)
        for ev in eventos_a_archivar:
            # Eliminar del AVL activo por su clave
            self.arbol_avl.eliminar(ev.clave, self.L)
            
            # Remover de dict_eventos
            if ev.id in self.dict_eventos:
                del self.dict_eventos[ev.id]
            
            # Transferir al histórico
            self.historico.append(ev)

        return True, justificacion, ids_afectados

    def deshacer_ultimo_archivado(self):
        """
        Restablece el árbol AVL y el estado del escenario exactamente a cómo estaban
        antes de ejecutar la última operación de archivado.
        """
        if hasattr(self, "_respaldo_previo_archivo") and self._respaldo_previo_archivo:
            self.arbol_avl.raiz = self._respaldo_previo_archivo["raiz_avl"]
            self.dict_eventos = self._respaldo_previo_archivo["dict_eventos"]
            self.historico = self._respaldo_previo_archivo["historico"]
            self.arbol_avl.actualizar_profundidades(self.L)
            self._respaldo_previo_archivo = None
            return True
        return False

    def _clonar_arbol(self, raiz):
        """Clona la estructura del árbol para poder deshacer cambios si el usuario cancela."""
        if raiz is None:
            return None
        from copy import deepcopy
        nodo_clon = deepcopy(raiz)
        return nodo_clon