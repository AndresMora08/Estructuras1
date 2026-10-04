from collections import deque
from typing import Dict, List, Optional, Tuple
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from datetime import datetime as Datetime
from datetime import datetime
from datetime import timezone

class AVL:
    def __init__(self, modo_estres: bool = False):
        self.raiz: Optional[Nodo] = None
        self.modo_estres = modo_estres
        self.conteo_rotaciones = {"LL": 0, "RR": 0, "LR": 0, "RL": 0, "giros_simples": 0, "giros_izquierda": 0, "giros_derecha": 0}

    def actualizar_profundidades(self, limite_L: int) -> None:
        self._recorrer_y_actualizar_profundidades(self.raiz, 0, limite_L)

    def _recorrer_y_actualizar_profundidades(self, nodo: Optional[Nodo], prof_actual: int, limite_L: int) -> None:
        if nodo is None: return
        nodo.actualizar_profundidad_y_costo(prof_actual, limite_L)
        self._recorrer_y_actualizar_profundidades(nodo.izquierda, prof_actual + 1, limite_L)
        self._recorrer_y_actualizar_profundidades(nodo.derecha, prof_actual + 1, limite_L)

    def _obtener_altura(self, nodo: Optional[Nodo]) -> int:
        return -1 if nodo is None else nodo.altura

    def _actualizar_altura(self, nodo: Nodo) -> None:
        nodo.actualizar_altura()

    def _factor_balance(self, nodo: Optional[Nodo]) -> int:
        return 0 if nodo is None else self._obtener_altura(nodo.izquierda) - self._obtener_altura(nodo.derecha)

    def _rotacion_derecha(self, y: Nodo) -> Nodo:
        x = y.izquierda
        temporal = x.derecha
        x.derecha = y
        y.izquierda = temporal
        self._actualizar_altura(y)
        self._actualizar_altura(x)
        self.conteo_rotaciones["giros_simples"] += 1
        self.conteo_rotaciones["giros_derecha"] += 1
        return x

    def _rotacion_izquierda(self, x: Nodo) -> Nodo:
        y = x.derecha
        temporal = y.izquierda
        y.izquierda = x
        x.derecha = temporal
        self._actualizar_altura(x)
        self._actualizar_altura(y)
        self.conteo_rotaciones["giros_simples"] += 1
        self.conteo_rotaciones["giros_izquierda"] += 1
        return y

    def insertar(self, nodo: Nodo, limite_L: int) -> None:
        self.raiz = self._insertar(self.raiz, nodo)
        self.actualizar_profundidades(limite_L)

    def _insertar(self, nodo_actual: Optional[Nodo], nuevo_nodo: Nodo) -> Nodo:
        if nodo_actual is None: return nuevo_nodo
        if nuevo_nodo.clave < nodo_actual.clave:
            nodo_actual.izquierda = self._insertar(nodo_actual.izquierda, nuevo_nodo)
        elif nuevo_nodo.clave > nodo_actual.clave:
            nodo_actual.derecha = self._insertar(nodo_actual.derecha, nuevo_nodo)
        else: return nodo_actual
        self._actualizar_altura(nodo_actual)
        if self.modo_estres: return nodo_actual
        balance = self._factor_balance(nodo_actual)
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

    def eliminar(self, clave: Tuple[int, float, int], limite_L: int) -> None:
        self.raiz = self._eliminar(self.raiz, clave)
        self.actualizar_profundidades(limite_L)

    def _eliminar(self, raiz: Optional[Nodo], clave: Tuple[int, float, int]) -> Optional[Nodo]:
        if raiz is None: return None
        if clave < raiz.evento.clave:
            raiz.izquierda = self._eliminar(raiz.izquierda, clave)
        elif clave > raiz.evento.clave:
            raiz.derecha = self._eliminar(raiz.derecha, clave)
        else:
            if raiz.es_hoja(): return None
            if raiz.tiene_dos_hijos():
                sucesor = self._buscar_minimo(raiz.derecha)
                raiz.evento = sucesor.evento
                raiz.derecha = self._eliminar(raiz.derecha, sucesor.evento.clave)
            elif raiz.tiene_hijo_izquierdo(): return raiz.izquierda
            elif raiz.tiene_hijo_derecho(): return raiz.derecha
        if raiz is None: return None
        self._actualizar_altura(raiz)
        if self.modo_estres: return raiz
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

    def _esta_desbalanceado(self, nodo: Optional[Nodo]) -> bool:
        if nodo is None: return False
        if abs(self._factor_balance(nodo)) > 1: return True
        return self._esta_desbalanceado(nodo.izquierda) or self._esta_desbalanceado(nodo.derecha)

    def recuperar_equilibrio(self, limite_L: int) -> None:
        if self.raiz is None:
            self.modo_estres = False
            self.actualizar_profundidades(limite_L)
            return
        self.raiz = self._recuperar_equilibrio_paso(self.raiz)
        self.actualizar_profundidades(limite_L)
        self.modo_estres = self._esta_desbalanceado(self.raiz)

    def _recuperar_equilibrio_paso(self, nodo: Optional[Nodo]) -> Optional[Nodo]:
        if nodo is None: return None
        nodo.izquierda = self._recuperar_equilibrio_paso(nodo.izquierda)
        nodo.derecha = self._recuperar_equilibrio_paso(nodo.derecha)
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

    def buscar(self, clave: Tuple[int, float, int]) -> Optional[Nodo]:
        return self._buscar(self.raiz, clave)

    def _buscar(self, nodo: Optional[Nodo], clave: Tuple[int, float, int]) -> Optional[Nodo]:
        if nodo is None or nodo.clave == clave: return nodo
        if clave < nodo.clave: return self._buscar(nodo.izquierda, clave)
        return self._buscar(nodo.derecha, clave)

    def _buscar_minimo(self, raiz: Nodo) -> Nodo:
        actual = raiz
        while actual.tiene_hijo_izquierdo(): actual = actual.izquierda
        return actual

    def es_nodo_archivable(self, nodo, reloj, T_horas: float) -> bool:
        if nodo is None: return True
        if isinstance(nodo.evento.fecha_hora, str):
            fecha_ev = datetime.strptime(nodo.evento.fecha_hora, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        else:
            fecha_ev = nodo.evento.fecha_hora
            if fecha_ev.tzinfo is None: fecha_ev = fecha_ev.replace(tzinfo=timezone.utc)
        reloj_utc = reloj if getattr(reloj, "tzinfo", None) is not None else reloj.replace(tzinfo=timezone.utc)
        antiguedad_horas = (reloj_utc - fecha_ev).total_seconds() / 3600.0
        if nodo.evento.prioridad != 1 or antiguedad_horas <= T_horas: return False
        return self.es_nodo_archivable(nodo.izquierda, reloj, T_horas) and self.es_nodo_archivable(nodo.derecha, reloj, T_horas)

    def buscar_nodo_y_profundidad(self, id_evento: int):
        def _buscar(nodo, prof_actual):
            if nodo is None: return None, 0
            if nodo.evento.id == id_evento: return nodo, prof_actual
            izq, p_izq = _buscar(nodo.izquierda, prof_actual + 1)
            if izq: return izq, p_izq
            return _buscar(nodo.derecha, prof_actual + 1)
        return _buscar(self.raiz, 0)

    def obtener_subarbol_eventos(self, nodo):
        eventos = []
        def _recolectar(n):
            if n:
                eventos.append(n.evento)
                _recolectar(n.izquierda)
                _recolectar(n.derecha)
        _recolectar(nodo)
        return eventos

    def buscar_rama_elegible_optima(self, reloj, T_horas: float):
        candidatos = []
        def _evaluar(nodo, prof_actual=0):
            if nodo is None: return
            if self.es_nodo_archivable(nodo, reloj, T_horas):
                eventos_subarbol = self.obtener_subarbol_eventos(nodo)
                candidatos.append({"nodo_raiz": nodo, "id_raiz": nodo.evento.id, "cant_nodos": len(eventos_subarbol), "profundidad": prof_actual, "eventos": eventos_subarbol})
            _evaluar(nodo.izquierda, prof_actual + 1)
            _evaluar(nodo.derecha, prof_actual + 1)
        _evaluar(self.raiz)
        if not candidatos: return None
        candidatos.sort(key=lambda c: (c["cant_nodos"], c["profundidad"], c["id_raiz"]), reverse=True)
        return candidatos[0]

    def buscar_top_k_pendientes(self, k: int) -> tuple[list, int]:
        eventos = []
        nodos_visitados = [0]
        if k <= 0 or self.raiz is None: return eventos, 0
        self._buscar_top_k_pendientes(self.raiz, k, eventos, nodos_visitados)
        return eventos, nodos_visitados[0]

    def _buscar_top_k_pendientes(self, raiz: Optional[Nodo], k: int, eventos: list, nodos_visitados: list[int]) -> None:
        if raiz is None or len(eventos) >= k: return
        self._buscar_top_k_pendientes(raiz.derecha, k, eventos, nodos_visitados)
        if len(eventos) < k:
            nodos_visitados[0] += 1
            if raiz.evento.estado == "Pendiente": eventos.append(raiz.evento)
        if len(eventos) < k: self._buscar_top_k_pendientes(raiz.izquierda, k, eventos, nodos_visitados)

    def buscar_por_rango_magnitud(self, m_min: float, m_max: float) -> tuple[list, int]:
        if m_min > m_max or self.raiz is None: return [], 0
        eventos = []
        nodos_visitados = [0]
        self._buscar_por_rango_magnitud(self.raiz, m_min, m_max, eventos, nodos_visitados)
        return eventos, nodos_visitados[0]

    def _buscar_por_rango_magnitud(self, raiz: Optional[Nodo], m_min: float, m_max: float, eventos: list, nodos_visitados: list[int]) -> None:
        if raiz is None: return
        nodos_visitados[0] += 1
        mag_actual = raiz.evento.magnitud
        if mag_actual > m_min: self._buscar_por_rango_magnitud(raiz.izquierda, m_min, m_max, eventos, nodos_visitados)
        if m_min <= mag_actual <= m_max: eventos.append(raiz.evento)
        if mag_actual < m_max: self._buscar_por_rango_magnitud(raiz.derecha, m_min, m_max, eventos, nodos_visitados)

    def buscar_por_fecha_y_profundidad(self, fecha_inicio: str, fecha_fin: str, profundidad_limite: float) -> tuple[list, int]:
        if fecha_inicio > fecha_fin or profundidad_limite < 0.0 or self.raiz is None: return [], 0
        eventos = []
        nodos_visitados = [0]
        self._buscar_por_fecha_y_profundidad(self.raiz, fecha_inicio, fecha_fin, profundidad_limite, eventos, nodos_visitados)
        return eventos, nodos_visitados[0]

    def _buscar_por_fecha_y_profundidad(self, raiz: Optional[Nodo], fecha_inicio: str, fecha_fin: str, profundidad_limite: float, eventos: list, nodos_visitados: list[int]) -> None:
        if raiz is None: return
        nodos_visitados[0] += 1
        self._buscar_por_fecha_y_profundidad(raiz.izquierda, fecha_inicio, fecha_fin, profundidad_limite, eventos, nodos_visitados)
        evento = raiz.evento
        if fecha_inicio <= evento.fecha_hora <= fecha_fin and evento.profundidad <= profundidad_limite: eventos.append(evento)
        self._buscar_por_fecha_y_profundidad(raiz.derecha, fecha_inicio, fecha_fin, profundidad_limite, eventos, nodos_visitados)

    def buscar_eventos_prioritarios_costosos(self, limite_L: int) -> tuple[list[dict], int]:
        if limite_L < 0 or self.raiz is None: return [], 0
        eventos_costosos = []
        nodos_visitados = [0]
        self._buscar_eventos_prioritarios_costosos(self.raiz, 0, limite_L, eventos_costosos, nodos_visitados)
        return eventos_costosos, nodos_visitados[0]

    def _buscar_eventos_prioritarios_costosos(self, raiz: Optional[Nodo], profundidad_actual: int, limite_L: int, eventos_costosos: list[dict], nodos_visitados: list[int]) -> None:
        if raiz is None: return
        nodos_visitados[0] += 1
        self._buscar_eventos_prioritarios_costosos(raiz.izquierda, profundidad_actual + 1, limite_L, eventos_costosos, nodos_visitados)
        if profundidad_actual > limite_L:
            evento = raiz.evento
            if evento.acceso_costoso:
                eventos_costosos.append({"evento": evento, "profundidad_nodo": profundidad_actual, "limite_L": limite_L, "nodos_visitados_busqueda": profundidad_actual + 1})
        self._buscar_eventos_prioritarios_costosos(raiz.derecha, profundidad_actual + 1, limite_L, eventos_costosos, nodos_visitados)

    def contar_hojas(self) -> int:
        return self._contar_hojas(self.raiz)

    def _contar_hojas(self, nodo: Optional[Nodo]) -> int:
        if nodo is None: return 0
        if nodo.izquierda is None and nodo.derecha is None: return 1
        return self._contar_hojas(nodo.izquierda) + self._contar_hojas(nodo.derecha)

    def recorrido_inorden(self) -> list:
        resultado = []
        self._inorden(self.raiz, resultado)
        return resultado

    def _inorden(self, nodo: Optional[Nodo], resultado: list):
        if nodo:
            self._inorden(nodo.izquierda, resultado)
            resultado.append(f"SIS-{nodo.evento.id:06d}")
            self._inorden(nodo.derecha, resultado)

    def recorrido_preorden(self) -> list:
        resultado = []
        self._preorden(self.raiz, resultado)
        return resultado

    def _preorden(self, nodo: Optional[Nodo], resultado: list):
        if nodo:
            resultado.append(f"SIS-{nodo.evento.id:06d}")
            self._preorden(nodo.izquierda, resultado)
            self._preorden(nodo.derecha, resultado)

    def recorrido_postorden(self) -> list:
        resultado = []
        self._postorden(self.raiz, resultado)
        return resultado

    def _postorden(self, nodo: Optional[Nodo], resultado: list):
        if nodo:
            self._postorden(nodo.izquierda, resultado)
            self._postorden(nodo.derecha, resultado)
            resultado.append(f"SIS-{nodo.evento.id:06d}")

    def recorrido_por_niveles(self) -> list:
        if not self.raiz: return []
        resultado = []
        cola = deque([self.raiz])
        while cola:
            nodo = cola.popleft()
            resultado.append(f"SIS-{nodo.evento.id:06d}")
            if nodo.izquierda: cola.append(nodo.izquierda)
            if nodo.derecha: cola.append(nodo.derecha)
        return resultado