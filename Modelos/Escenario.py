from collections import deque
from datetime import datetime as Datetime, datetime, timezone
from typing import Dict, List, Optional, Tuple
from copy import deepcopy
import json
import os

from Modelos.AVL import AVL
from Modelos.Asociaciones import recalcular_asociaciones_escenario
from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Zona import Zona
from Logica.controlador_json import ControladorJSON
from Modelos.BST import ArbolBST

class Escenario:

    def __init__(
        self,
        zonas: List[Zona] = None,
        estaciones: List[Estacion] = None,
        epicentros: List[Epicentro] = None,
        reloj: Optional[Datetime] = None,
        arbol_avl: Optional[AVL] = None,
        arbol_bst=None
    ):
        # None defaults avoid sharing mutable lists between instances
        self.zonas: List[Zona] = zonas if zonas is not None else []
        self.estaciones: List[Estacion] = estaciones if estaciones is not None else []
        self.epicentros: List[Epicentro] = epicentros if epicentros is not None else []

        self.reloj = reloj if reloj is not None else datetime.now(timezone.utc)
        self.arbol_avl = arbol_avl if arbol_avl is not None else AVL()
        self.arbol_bst = arbol_bst if arbol_bst is not None else ArbolBST()
        self.cola_reportes = deque()
        self.historico: List[Evento] = []
        self.dict_eventos: Dict[int, Evento] = {}

        self.W: float = 48.0
        self.R: float = 40.0
        self.L: int = 3
        self.T: float = 72.0

        self.metricas_reportes = {
            "nuevos": 0,
            "correcciones_aceptadas": 0,
            "reactivados": 0,
            "confirmaciones": 0,
            "conflictos": 0,
            "descartados_antiguos": 0,
            "rechazados_retirados": 0,
            "archivos_masivos": 0,
            "eventos_archivados": 0,
        }

        # In-memory undo stack (LIFO: append / pop are O(1))
        self.pila_deshacer = []
        # Persistent folder for named versions
        self.carpeta_versiones = "versiones_guardadas"
        if not os.path.exists(self.carpeta_versiones):
            os.makedirs(self.carpeta_versiones)

    # =========================================================================
    # UNDO STACK
    # =========================================================================
    def guardar_estado_pila(self):
        """
        Stores a full snapshot of the operational state.

        A SINGLE deepcopy over the whole dictionary is required: deepcopy keeps
        one memo table per call, so every shared object (events referenced by
        the AVL, the BST, dict_eventos, the queue and the history; zones
        referenced by stations and epicenters) is copied exactly once and the
        identities stay consistent inside the snapshot.
        """
        snapshot = deepcopy({
            "zonas": self.zonas,
            "estaciones": self.estaciones,
            "epicentros": self.epicentros,
            "reloj": self.reloj,
            "arbol_avl": self.arbol_avl,
            "arbol_bst": self.arbol_bst,
            "dict_eventos": self.dict_eventos,
            "historico": self.historico,
            "cola_reportes": self.cola_reportes,
            "W": self.W,
            "R": self.R,
            "L": self.L,
            "T": self.T,
            "metricas_reportes": self.metricas_reportes,
        })
        self.pila_deshacer.append(snapshot)

    def descartar_ultimo_estado(self) -> None:
        """Drops the last snapshot (used when an action ends up not changing anything)."""
        if self.pila_deshacer:
            self.pila_deshacer.pop()

    def deshacer_ultima_accion(self) -> bool:
        if not self.pila_deshacer:
            return False

        snapshot = self.pila_deshacer.pop()

        self.zonas = snapshot["zonas"]
        self.estaciones = snapshot["estaciones"]
        self.epicentros = snapshot["epicentros"]
        self.reloj = snapshot["reloj"]
        self.arbol_avl = snapshot["arbol_avl"]
        self.arbol_bst = snapshot["arbol_bst"]
        self.dict_eventos = snapshot["dict_eventos"]
        self.historico = snapshot["historico"]
        self.cola_reportes = snapshot["cola_reportes"]
        self.W = snapshot["W"]
        self.R = snapshot["R"]
        self.L = snapshot["L"]
        self.T = snapshot["T"]

        # Updated in place so open windows keep pointing to the same dict
        if isinstance(getattr(self, "metricas_reportes", None), dict):
            self.metricas_reportes.clear()
            self.metricas_reportes.update(snapshot["metricas_reportes"])
        else:
            self.metricas_reportes = snapshot["metricas_reportes"]

        return True

    # =========================================================================
    # PARAMETERS (W, R, L, T) - one undoable action
    # =========================================================================
    def cambiar_parametros(self, W, R, L, T) -> Tuple[bool, str]:
        """
        Validates and applies W, R, L and T as a single undoable action.
        L updates node depths / expensive-access marks; W and R recompute associations.
        """
        try:
            W = float(W)
            R = float(R)
            T = float(T)
            if float(L) != int(float(L)):
                raise ValueError("L no es entero")
            L = int(float(L))
        except (TypeError, ValueError):
            return False, "W, R y T deben ser números y L un entero."

        if W <= 0 or R <= 0 or T <= 0:
            return False, "W, R y T deben ser estrictamente positivos."
        if L < 0:
            return False, "L debe ser un entero no negativo."

        if (W, R, L, T) == (self.W, self.R, self.L, self.T):
            return True, "Los parámetros no cambiaron."

        self.guardar_estado_pila()
        try:
            self.W, self.R, self.L, self.T = W, R, L, T
            if self.arbol_avl is not None:
                self.arbol_avl.actualizar_profundidades(L)
            recalcular_asociaciones_escenario(self, W, R)
        except Exception as e:
            self.deshacer_ultima_accion()
            return False, f"No se pudieron aplicar los parámetros: {e}"

        return True, f"Parámetros actualizados: W={W} h, R={R} km, L={L}, T={T} h."

    # =========================================================================
    # NAMED PERSISTENT VERSIONS (DISK)
    # =========================================================================
    def guardar_version_persistente(self, nombre_version: str) -> Tuple[bool, str]:
        nombre_limpio = "".join(c for c in nombre_version if c.isalnum() or c in (" ", "_", "-")).strip()
        if not nombre_limpio:
            return False, "Nombre de versión no válido."

        ruta_archivo = os.path.join(self.carpeta_versiones, f"{nombre_limpio}.json")

        try:
            datos = ControladorJSON.construir_diccionario_topologia(self)
            ControladorJSON._escribir_json_atomico(ruta_archivo, datos)
            return True, f"Versión '{nombre_limpio}' guardada exitosamente."
        except Exception as e:
            return False, f"Error al guardar la versión persistente: {str(e)}"

    def listar_versiones_persistentes(self) -> List[str]:
        if not os.path.exists(self.carpeta_versiones):
            return []
        archivos = os.listdir(self.carpeta_versiones)
        return [os.path.splitext(f)[0] for f in archivos if f.endswith(".json")]

    def restaurar_version_persistente(self, nombre_version: str) -> Tuple[bool, str]:
        ruta_archivo = os.path.join(self.carpeta_versiones, f"{nombre_version}.json")
        if not os.path.exists(ruta_archivo):
            return False, f"La versión '{nombre_version}' no existe."

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)

            estado_nuevo, errores, _ = ControladorJSON.validar_topologia(datos, self)
            if errores:
                return False, f"Error al validar el archivo de la versión:\n" + "\n".join(errores)

            self.guardar_estado_pila()
            ControladorJSON._aplicar_estado(self, estado_nuevo)

            return True, f"Versión '{nombre_version}' restaurada exitosamente."
        except Exception as e:
            return False, f"Error al restaurar la versión: {str(e)}"

    # =========================================================================
    # OPERATIONS
    # =========================================================================
    def registrar_accion_operativa(self, funcion_modificadora, *args, **kwargs):
        self.guardar_estado_pila()
        return funcion_modificadora(*args, **kwargs)

    def eliminar_evento_por_id(self, id_evento):
    
     if id_evento not in self.dict_eventos:
        return False, "Evento no encontrado."

     evento = self.dict_eventos[id_evento]

     self.guardar_estado_pila()

     try:
        if hasattr(evento, "clave"):

            if self.arbol_avl is not None:
                self.arbol_avl.eliminar(
                    evento.clave,
                    self.L
                )

            if self.arbol_bst is not None:
                self.arbol_bst.eliminar(
                    evento.clave,
                    self.L
                )

        del self.dict_eventos[id_evento]

        evento.estado_catalogo = "Retirado"
        self.historico.append(evento)

        return True, (
            f"SIS-{id_evento:06d} eliminado correctamente."
        )

     except Exception:
        self.deshacer_ultima_accion()

        return False, (
            "No se pudo eliminar el evento."
        )

    def archivar_evento_por_id(self, id_evento: int):
        if not self.arbol_avl or not self.arbol_avl.raiz:
            return False, "El árbol AVL no está inicializado o está vacío.", None

        if id_evento not in self.dict_eventos:
            return False, f"El evento ID {id_evento} no existe en los eventos activos.", None

        nodo_target, prof_target = self.arbol_avl.buscar_nodo_y_profundidad(id_evento)
        if not nodo_target:
            return False, f"El evento ID {id_evento} no se encontró físicamente en el árbol AVL.", None

        if not self.arbol_avl.es_nodo_archivable(nodo_target, self.reloj, self.T):
            return False, f"La rama con raíz ID {id_evento} NO es elegible.", None

        # The affected set is fixed BEFORE modifying the tree
        eventos_a_archivar = self.arbol_avl.obtener_subarbol_eventos(nodo_target)
        cant_nodos = len(eventos_a_archivar)
        ids_afectados = [e.id for e in eventos_a_archivar]

        justificacion = (
            f"Selección de rama elegible para archivo con raíz ID {id_evento}:\n"
            f"- Cantidad de eventos afectados: {cant_nodos}\n"
            f"- Profundidad de la raíz en el árbol: Nivel {prof_target}\n"
            f"- Identificadores afectados: {ids_afectados}"
        )

        self.guardar_estado_pila()
        try:
            for ev in eventos_a_archivar:
    
              if self.arbol_avl is not None:
                 self.arbol_avl.eliminar(
                   ev.clave,
                  self.L
                  )

            if self.arbol_bst is not None:
              self.arbol_bst.eliminar(
              ev.clave,
              self.L
            )

            if ev.id in self.dict_eventos:
                del self.dict_eventos[ev.id]

            ev.estado_catalogo = "Archivado"
            self.historico.append(ev)
        except Exception as e:
            self.deshacer_ultima_accion()
            return False, f"Error al archivar la rama: {str(e)}", None

        return True, justificacion, ids_afectados