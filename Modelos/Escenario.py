from collections import deque
from datetime import datetime as Datetime, datetime, timezone
from typing import Dict, List, Optional, Tuple
from copy import deepcopy
import json
import os

from Modelos.AVL import AVL
from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Zona import Zona
from Logica.controlador_json import ControladorJSON


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
        self.arbol_bst = None
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
        }

        # Pila de retroceso en memoria
        self.pila_deshacer = []
        # Carpeta persistente para versiones con nombre
        self.carpeta_versiones = "versiones_guardadas"
        if not os.path.exists(self.carpeta_versiones):
            os.makedirs(self.carpeta_versiones)

    # =========================================================================
    # PILA DE RETROCESO (DESHACER COMPLETO)
    # =========================================================================
    def guardar_estado_pila(self):
        """
        Guarda un snapshot completo del estado operativo antes de ejecutar cualquier
        acción que altere el escenario (altas, eliminaciones, avances de reloj,
        cambios de atención, pasos de la cola, cargas, etc.).
        """
        snapshot = {
            "zonas": deepcopy(self.zonas),
            "estaciones": deepcopy(self.estaciones),
            "epicentros": deepcopy(self.epicentros),
            "reloj": deepcopy(self.reloj),
            "arbol_avl": deepcopy(self.arbol_avl),
            "arbol_bst": deepcopy(self.arbol_bst),
            "dict_eventos": deepcopy(self.dict_eventos),
            "historico": deepcopy(self.historico),
            "cola_reportes": deepcopy(self.cola_reportes),
            "W": self.W,
            "R": self.R,
            "L": self.L,
            "T": self.T,
            "metricas_reportes": deepcopy(self.metricas_reportes),
        }
        self.pila_deshacer.append(snapshot)

    def deshacer_ultima_accion(self) -> bool:
        """
        Recupera el estado anterior exacto desde la pila de retroceso, restaurando
        datos, histórico, referencias, cola, reloj, parámetros, modo y métricas.
        """
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

        if isinstance(getattr(self, "metricas_reportes", None), dict):
            self.metricas_reportes.clear()
            self.metricas_reportes.update(snapshot["metricas_reportes"])
        else:
            self.metricas_reportes = snapshot["metricas_reportes"]

        return True

    # =========================================================================
    # VERSIONES PERSISTENTES CON NOMBRE (DISCO)
    # =========================================================================
    def guardar_version_persistente(self, nombre_version: str) -> Tuple[bool, str]:
        """
        Guarda una versión persistente con nombre en el disco.
        Aprovecha la serialización completa de ControladorJSON sin modificarlo.
        """
        nombre_limpio = "".join(c for c in nombre_version if c.isalnum() or c in (" ", "_", "-")).strip()
        if not nombre_limpio:
            return False, "Nombre de versión no válido."

        ruta_archivo = os.path.join(self.carpeta_versiones, f"{nombre_limpio}.json")

        try:
            # Reutiliza el método de serialización estándar del controlador JSON
            datos = ControladorJSON.construir_diccionario_topologia(self)
            ControladorJSON._escribir_json_atomico(ruta_archivo, datos)
            return True, f"Versión '{nombre_limpio}' guardada exitosamente."
        except Exception as e:
            return False, f"Error al guardar la versión persistente: {str(e)}"

    def listar_versiones_persistentes(self) -> List[str]:
        """Retorna los nombres de las versiones guardadas en disco."""
        if not os.path.exists(self.carpeta_versiones):
            return []
        archivos = os.listdir(self.carpeta_versiones)
        return [os.path.splitext(f)[0] for f in archivos if f.endswith(".json")]

    def restaurar_version_persistente(self, nombre_version: str) -> Tuple[bool, str]:
        """
        Restaura una versión guardada en disco.
        REGLA DEL PUNTO 13: Restaurar una versión es una acción que puede deshacerse,
        por lo que se apila la situación actual ANTES de aplicar los cambios.
        """
        ruta_archivo = os.path.join(self.carpeta_versiones, f"{nombre_version}.json")
        if not os.path.exists(ruta_archivo):
            return False, f"La versión '{nombre_version}' no existe."

        try:
            with open(ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)

            # Validar la topología usando las rutinas sin modificar del controlador
            estado_nuevo, errores, _ = ControladorJSON.validar_topologia(datos, self)
            if errores:
                return False, f"Error al validar el archivo de la versión:\n" + "\n".join(errores)

            # 1. Se registra en la pila para que la restauración sea deshacible
            self.guardar_estado_pila()

            # 2. Se aplican los datos restaurados en el escenario
            ControladorJSON._aplicar_estado(self, estado_nuevo)

            return True, f"Versión '{nombre_version}' restaurada exitosamente."
        except Exception as e:
            return False, f"Error al restaurar la versión: {str(e)}"

    # =========================================================================
    # MÉTODOS DE OPERACIÓN (TODOS GUARDAN ESTADO EN PILA ANTES DE MODIFICAR)
    # =========================================================================
    def registrar_accion_operativa(self, funcion_modificadora, *args, **kwargs):
        """
        Wrapper auxiliar para garantizar que cualquier alta, cambio de parámetros,
        cambio de atención, avance de reloj, etc., sea registrado en la pila antes de ejecutarse.
        """
        self.guardar_estado_pila()
        return funcion_modificadora(*args, **kwargs)

    def eliminar_evento_por_id(self, id_evento: int) -> Tuple[bool, str]:
        if id_evento not in self.dict_eventos:
            return False, f"El evento ID {id_evento} no existe en los eventos activos."

        evento = self.dict_eventos[id_evento]
        try:
            self.guardar_estado_pila()

            if self.arbol_avl and hasattr(evento, "clave"):
                self.arbol_avl.eliminar(evento.clave, self.L)

            del self.dict_eventos[id_evento]
            evento.estado_catalogo = "Retirado"
            self.historico.append(evento)

            return True, f"Evento SIS-{id_evento:06d} retirado del catálogo exitosamente."
        except Exception as e:
            return False, f"Error al eliminar el evento: {str(e)}"

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

        for ev in eventos_a_archivar:
            self.arbol_avl.eliminar(ev.clave, self.L)
            if ev.id in self.dict_eventos:
                del self.dict_eventos[ev.id]
            ev.estado_catalogo = "Archivado"
            self.historico.append(ev)

        return True, justificacion, ids_afectados