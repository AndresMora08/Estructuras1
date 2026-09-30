from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.Reporte import Reporte

FORMATO_FECHA_ISO = "%Y-%m-%dT%H:%M:%SZ"
TOLERANCIA = 1e-6


class ControladorReportes:
    """
    Business logic for the report queue (FIFO), the report processing rules
    (section 6), the stress mode and the global recovery (section 8).
    It never touches the GUI. It only uses the public API of the models.
    """

    def __init__(self, escenario):
        self.escenario = escenario

        # Optional hook: a callable(id_evento) that recalculates associations.
        # The GUI/other modules can assign it; it is called after every accepted change.
        self.actualizar_asociaciones = None

        # Counters kept in the scenario so they survive closing the reports window
        if not hasattr(escenario, "metricas_reportes"):
            escenario.metricas_reportes = {
                "nuevos": 0,
                "correcciones_aceptadas": 0,
                "reactivados": 0,
                "confirmaciones": 0,
                "conflictos": 0,
                "descartados_antiguos": 0,
                "rechazados_retirados": 0,
            }
        self.metricas = escenario.metricas_reportes

    # ==================================================================
    # DATE / VALIDATION HELPERS
    # ==================================================================

    @staticmethod
    def parsear_fecha_utc(texto: str) -> Optional[datetime]:
        """Parses 'YYYY-MM-DDTHH:MM:SSZ' into an aware UTC datetime (None if invalid)."""
        try:
            return datetime.strptime(str(texto).strip(), FORMATO_FECHA_ISO).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return None

    def _reloj_utc(self) -> datetime:
     reloj = self.escenario.reloj
     if reloj.tzinfo is None:
            reloj = reloj.replace(tzinfo=timezone.utc)
     return reloj.replace(microsecond=0)
 
    @staticmethod
    def _tiene_maximo_un_decimal(valor: float) -> bool:
        return abs(valor * 10 - round(valor * 10)) < TOLERANCIA
    
    def obtener_reloj_texto(self) -> str:
            """Simulation clock as ISO 8601 UTC text (same format as event dates)."""
            return self._reloj_utc().strftime(FORMATO_FECHA_ISO)

    def avanzar_reloj(self, horas: float) -> Tuple[bool, str]:
        """Advances the simulation clock. It can only move forward."""
        if horas <= 0:
            return False, "El avance debe ser mayor que 0 horas."
        self.escenario.reloj = self._reloj_utc() + timedelta(hours=horas)
        return True, f"Reloj avanzado {horas} h. Nuevo reloj: {self.obtener_reloj_texto()}."
    def _validar_rangos(
        self, id_evento, magnitud, profundidad, x, y, fecha: Optional[datetime]
    ) -> Tuple[bool, str]:
        if not (1 <= id_evento <= 999999):
            return False, "El identificador debe estar entre 1 y 999999."
        if not (-2.0 <= magnitud <= 10.0):
            return False, "La magnitud debe estar entre -2.0 y 10.0."
        if not (0.0 <= profundidad <= 700.0):
            return False, "La profundidad debe estar entre 0.0 y 700.0 km."
        if not (0.0 <= x <= 1000.0 and 0.0 <= y <= 1000.0):
            return False, "Las coordenadas del epicentro deben estar entre 0.0 y 1000.0 km."
        if fecha is None:
            return False, "La fecha debe tener formato ISO 8601 UTC (ej. 2026-09-07T10:00:00Z)."
        if fecha > self._reloj_utc():
            return False, (
                "La fecha de ocurrencia no puede ser posterior al reloj de simulación "
                f"({self.obtener_reloj_texto()}). Avance el reloj o use una fecha anterior."
            )
        return True, "OK"

    def crear_evento_reportado(
        self,
        id_evento: int,
        magnitud: float,
        profundidad: float,
        x: float,
        y: float,
        fecha_texto: str,
        estacion: Optional[Estacion],
        revision: int,
    ) -> Tuple[bool, str, Optional[Evento]]:
        """
        Validates the raw values typed by the user and builds a NEW Evento with the
        proposed data (the base event is never touched here).
        """
        if estacion is None:
            return False, "Debe seleccionar una estación emisora.", None
        if revision < 1:
            return False, "La revisión debe ser un entero positivo.", None

        for nombre, valor in (
            ("magnitud", magnitud),
            ("profundidad", profundidad),
            ("coordenada X", x),
            ("coordenada Y", y),
        ):
            if not self._tiene_maximo_un_decimal(valor):
                return False, f"La {nombre} admite máximo un decimal.", None

        fecha = self.parsear_fecha_utc(fecha_texto)
        valido, mensaje = self._validar_rangos(id_evento, magnitud, profundidad, x, y, fecha)
        if not valido:
            return False, mensaje, None

        epicentro = Epicentro(x, y, self.escenario.zonas)  # assigns the zone -> priority
        evento = Evento(
            id_evento=id_evento,
            magnitud=magnitud,
            profundidad=profundidad,
            epicentro=epicentro,
            estacion_origen=estacion,
            fecha_hora=fecha.strftime(FORMATO_FECHA_ISO),
            revision=revision,
        )
        return True, "OK", evento

    def validar_evento(self, evento: Evento) -> Tuple[bool, str]:
        """Validates an already-built Evento before it enters the queue."""
        if not evento.epicentro:
            return False, "El evento debe contener un epicentro válido."
        return self._validar_rangos(
            evento.id,
            evento.magnitud,
            evento.profundidad,
            evento.epicentro.x,
            evento.epicentro.y,
            self.parsear_fecha_utc(evento.fecha_hora),
        )

    # ==================================================================
    # QUEUE (FIFO): append = O(1), popleft = O(1)
    # ==================================================================

    def encolar_reporte(
        self, evento: Evento, estacion_emisora: Estacion, revision: int
    ) -> Tuple[bool, str]:
        """Validation step: only valid reports enter the FIFO queue."""
        if estacion_emisora is None:
            return False, "El reporte necesita una estación emisora."
        if int(revision) < 1:
            return False, "La revisión debe ser un entero positivo."
        valido, mensaje = self.validar_evento(evento)
        if not valido:
            return False, mensaje

        reporte = Reporte(evento=evento, estacion_emisora=estacion_emisora, revision=int(revision))
        self.escenario.cola_reportes.append(reporte)
        return True, "Reporte encolado correctamente."

    def obtener_cola(self) -> List[Reporte]:
        return list(self.escenario.cola_reportes)

    # ==================================================================
    # SMALL HELPERS
    # ==================================================================

    @staticmethod
    def _obtener_id_estacion(estacion) -> str:
        return getattr(estacion, "id_estacion", str(estacion))

    def _obtener_arbol(self):
        arbol = self.escenario.arbol_avl
        if arbol is None:
            raise ValueError("El escenario no tiene un árbol AVL inicializado.")
        return arbol

    def _copiar_rotaciones(self) -> Dict[str, int]:
        arbol = self.escenario.arbol_avl
        return dict(arbol.conteo_rotaciones) if arbol else {}

    def _diferencia_rotaciones(self, anteriores: Dict[str, int]) -> Dict[str, int]:
        actuales = self._copiar_rotaciones()
        return {k: actuales[k] - anteriores.get(k, 0) for k in actuales}

    def _buscar_en_historico(self, id_evento: int) -> Optional[Evento]:
        for evento in reversed(self.escenario.historico):
            if evento.id == id_evento:
                return evento
        return None

    @staticmethod
    def _agregar_estacion(evento: Evento, id_estacion: str) -> bool:
        if id_estacion not in evento.estaciones:
            evento.estaciones.append(id_estacion)
            return True
        return False

    def _datos_son_iguales(self, evento_a: Evento, evento_b: Evento) -> bool:
        """Equality of physical data: magnitude, depth, epicenter and occurrence time."""
        fecha_a = self.parsear_fecha_utc(evento_a.fecha_hora)
        fecha_b = self.parsear_fecha_utc(evento_b.fecha_hora)
        return (
            abs(evento_a.magnitud - evento_b.magnitud) < TOLERANCIA
            and abs(evento_a.profundidad - evento_b.profundidad) < TOLERANCIA
            and abs(evento_a.epicentro.x - evento_b.epicentro.x) < TOLERANCIA
            and abs(evento_a.epicentro.y - evento_b.epicentro.y) < TOLERANCIA
            and fecha_a is not None
            and fecha_a == fecha_b
        )

    def _notificar_asociaciones(self, id_evento: int) -> None:
        if callable(self.actualizar_asociaciones):
            try:
                self.actualizar_asociaciones(id_evento)
            except Exception:
                pass  # associations must never break report processing

    @staticmethod
    def _capturar_datos(evento: Evento) -> dict:
        return {
            "magnitud": evento.magnitud,
            "profundidad": evento.profundidad,
            "epicentro": evento.epicentro,
            "fecha_hora": evento.fecha_hora,
            "revision": evento.revision,
            "estado": evento.estado,
            "estado_catalogo": evento.estado_catalogo,
            "estaciones": list(evento.estaciones),
            "prioridad": evento.prioridad,
        }

    @staticmethod
    def _restaurar_datos(evento: Evento, datos: dict) -> None:
        evento.magnitud = datos["magnitud"]
        evento.profundidad = datos["profundidad"]
        evento.epicentro = datos["epicentro"]
        evento.fecha_hora = datos["fecha_hora"]
        evento.revision = datos["revision"]
        evento.estado = datos["estado"]
        evento.estado_catalogo = datos["estado_catalogo"]
        evento.estaciones = datos["estaciones"]
        evento.actualizar_prioridad_y_clave(datos["prioridad"])

    def _sustituir_datos(self, vigente: Evento, reportado: Evento, revision: int, id_estacion: str):
        vigente.magnitud = reportado.magnitud
        vigente.profundidad = reportado.profundidad
        vigente.epicentro = reportado.epicentro
        vigente.fecha_hora = reportado.fecha_hora
        vigente.revision = revision
        vigente.estado = "Pendiente"  # an accepted correction returns to pending
        self._agregar_estacion(vigente, id_estacion)
        vigente.calcular_prioridad()  # recomputes priority and key (P, M, I)

    @staticmethod
    def _resultado(base: dict, resultado: str, detalle: str, **extra) -> dict:
        datos = dict(base)
        datos["resultado"] = resultado
        datos["detalle"] = detalle
        datos.update(extra)
        return datos

    # ==================================================================
    # REPORT PROCESSING (one step)
    # ==================================================================

    def procesar_siguiente_reporte(self) -> Optional[dict]:
        """
        Dequeues ONE report and resolves it completely.
        Returns None if the queue is empty. On an unexpected error the report is put
        back at the front of the queue and the result is 'ERROR'.
        """
        cola: deque = self.escenario.cola_reportes
        if not cola:
            return None

        reporte = cola.popleft()
        rotaciones_previas = self._copiar_rotaciones()

        try:
            resultado = self._aplicar_reporte(reporte)
        except Exception as error:
            cola.appendleft(reporte)
            return {
                "id_evento": reporte.evento.id,
                "revision": reporte.revision,
                "estacion": self._obtener_id_estacion(reporte.estacion_emisora),
                "resultado": "ERROR",
                "detalle": f"No se pudo procesar el reporte (devuelto a la cola): {error}",
                "rotaciones": self._diferencia_rotaciones(rotaciones_previas),
            }

        resultado["rotaciones"] = self._diferencia_rotaciones(rotaciones_previas)
        return resultado

    def _aplicar_reporte(self, reporte: Reporte) -> dict:
        escenario = self.escenario
        evento_reportado = reporte.evento
        revision = int(reporte.revision)
        id_evento = evento_reportado.id
        id_estacion = self._obtener_id_estacion(reporte.estacion_emisora)
        base = {"id_evento": id_evento, "revision": revision, "estacion": id_estacion}

        evento_historico = self._buscar_en_historico(id_evento)

        # Removed (deleted) identifiers are rejected
        if evento_historico is not None and evento_historico.estado_catalogo == "Retirado":
            self.metricas["rechazados_retirados"] += 1
            return self._resultado(
                base,
                "RECHAZADO (RETIRADO)",
                f"SIS-{id_evento:06d} fue eliminado. Sus reportes se rechazan hasta deshacer la eliminación.",
            )

        evento_activo = escenario.dict_eventos.get(id_evento)

        # Situation 1: unknown identifier
        if evento_activo is None and evento_historico is None:
            return self._registrar_evento_nuevo(base, evento_reportado, revision, id_estacion)

        esta_archivado = evento_activo is None
        vigente = evento_historico if esta_archivado else evento_activo

        # Situation 2: greater revision
        if revision > vigente.revision:
            if esta_archivado:
                return self._reactivar_evento_archivado(base, vigente, evento_reportado, revision, id_estacion)
            return self._corregir_evento_activo(base, vigente, evento_reportado, revision, id_estacion)

        # Situation 3 / 4: same revision
        if revision == vigente.revision:
            if self._datos_son_iguales(evento_reportado, vigente):
                agregada = self._agregar_estacion(vigente, id_estacion)
                self.metricas["confirmaciones"] += 1
                if agregada:
                    detalle = f"Evento confirmado. Estación {id_estacion} añadida a la lista."
                else:
                    detalle = f"Confirmación repetida de {id_estacion}: no se crean nodos ni se duplican estaciones."
                if esta_archivado:
                    detalle += " El evento archivado NO se reactiva."
                return self._resultado(base, "CONFIRMADO", detalle)

            self.metricas["conflictos"] += 1
            return self._resultado(
                base,
                "CONFLICTO (RECHAZADO)",
                f"Con la misma revisión r{revision} los datos difieren de los vigentes. "
                "Reporte rechazado sin sobrescribir el evento.",
            )

        # Situation 5: lower revision
        self.metricas["descartados_antiguos"] += 1
        return self._resultado(
            base,
            "DESCARTADO (ANTIGUO)",
            f"Reporte antiguo (r{revision}); la revisión vigente es r{vigente.revision}. Evento sin cambios.",
        )

    # ------------------------------------------------------------------
    # Atomic operations over the AVL
    # ------------------------------------------------------------------

    def _registrar_evento_nuevo(self, base, reportado: Evento, revision, id_estacion) -> dict:
        arbol = self._obtener_arbol()
        limite_L = self.escenario.L

        reportado.revision = revision
        reportado.estado = "Pendiente"
        reportado.estado_catalogo = "Activo"
        reportado.calcular_prioridad()
        self._agregar_estacion(reportado, id_estacion)

        self.escenario.dict_eventos[reportado.id] = reportado
        try:
            arbol.insertar(Nodo(evento=reportado), limite_L)
        except Exception:
            del self.escenario.dict_eventos[reportado.id]
            raise

        self.metricas["nuevos"] += 1
        self._notificar_asociaciones(reportado.id)
        return self._resultado(
            base,
            "REGISTRADO (NUEVO)",
            f"Evento nuevo con revisión inicial r{revision}. Prioridad {reportado.prioridad}, "
            f"clave {reportado.clave}.",
            clave_nueva=reportado.clave,
        )

    def _corregir_evento_activo(self, base, vigente: Evento, reportado: Evento, revision, id_estacion) -> dict:
        arbol = self._obtener_arbol()
        limite_L = self.escenario.L

        clave_anterior = vigente.clave
        clave_nueva = reportado.clave  # (P, M, I) derived from the reported data
        datos_previos = self._capturar_datos(vigente)

        if clave_anterior == clave_nueva:
            # Same key: the node keeps its position, only data/revision change
            self._sustituir_datos(vigente, reportado, revision, id_estacion)
            detalle = (
                f"Datos actualizados a r{revision}. La clave {clave_nueva} no cambió: "
                "no se elimina ni reinserta el nodo."
            )
        else:
            if arbol.buscar(clave_anterior) is None:
                raise ValueError("El evento activo no se encontró en el AVL con su clave anterior.")

            arbol.eliminar(clave_anterior, limite_L)  # remove with the OLD key
            try:
                self._sustituir_datos(vigente, reportado, revision, id_estacion)
                arbol.insertar(Nodo(evento=vigente), limite_L)  # reinsert with the NEW key
            except Exception:
                self._restaurar_datos(vigente, datos_previos)
                if arbol.buscar(clave_anterior) is None:
                    arbol.insertar(Nodo(evento=vigente), limite_L)
                raise
            detalle = (
                f"Datos actualizados a r{revision}. Clave {clave_anterior} -> {clave_nueva}: "
                "nodo retirado y reinsertado."
            )

        self.metricas["correcciones_aceptadas"] += 1
        self._notificar_asociaciones(vigente.id)
        return self._resultado(
            base,
            "SUSTITUIDO (CORRECCIÓN)",
            detalle,
            clave_anterior=clave_anterior,
            clave_nueva=vigente.clave,
        )

    def _reactivar_evento_archivado(self, base, archivado: Evento, reportado: Evento, revision, id_estacion) -> dict:
        arbol = self._obtener_arbol()
        limite_L = self.escenario.L
        datos_previos = self._capturar_datos(archivado)

        self._sustituir_datos(archivado, reportado, revision, id_estacion)
        archivado.estado_catalogo = "Activo"
        self.escenario.historico.remove(archivado)
        self.escenario.dict_eventos[archivado.id] = archivado
        try:
            arbol.insertar(Nodo(evento=archivado), limite_L)
        except Exception:
            self._restaurar_datos(archivado, datos_previos)
            self.escenario.dict_eventos.pop(archivado.id, None)
            self.escenario.historico.append(archivado)
            raise

        self.metricas["reactivados"] += 1
        self._notificar_asociaciones(archivado.id)
        return self._resultado(
            base,
            "REACTIVADO (ARCHIVADO -> ACTIVO)",
            f"Revisión r{revision} mayor que la archivada: evento reactivado como pendiente "
            f"con clave {archivado.clave}.",
            clave_nueva=archivado.clave,
        )

    # ==================================================================
    # STRESS MODE, AUDIT AND GLOBAL RECOVERY
    # ==================================================================

    def modo_estres_activo(self) -> bool:
        arbol = self.escenario.arbol_avl
        return bool(arbol and arbol.modo_estres)

    def establecer_modo_estres(self, activo: bool) -> None:
        self._obtener_arbol().modo_estres = bool(activo)

    def auditar_arbol(self) -> dict:
        """
        Read-only audit: global BST order by K, uniqueness, recomputed heights vs stored
        heights and balance factors. Does not modify the tree.
        """
        arbol = self.escenario.arbol_avl
        errores_orden: List[str] = []
        errores_metadatos: List[str] = []
        desbalanceados: List[Tuple[int, int]] = []
        ids_vistos = set()
        total = [0]

        def visitar(nodo, minimo, maximo) -> int:
            if nodo is None:
                return 0
            total[0] += 1
            evento = nodo.evento
            clave = evento.clave

            if (minimo is not None and clave <= minimo) or (maximo is not None and clave >= maximo):
                errores_orden.append(f"SIS-{evento.id:06d}: clave {clave} viola el orden BST global.")
            if evento.id in ids_vistos:
                errores_metadatos.append(f"SIS-{evento.id:06d}: aparece en más de una posición.")
            ids_vistos.add(evento.id)
            if evento.id not in self.escenario.dict_eventos:
                errores_metadatos.append(f"SIS-{evento.id:06d}: está en el AVL pero no en dict_eventos.")

            altura_izq = visitar(nodo.izquierda, minimo, clave)
            altura_der = visitar(nodo.derecha, clave, maximo)
            altura_real = 1 + max(altura_izq, altura_der)

            if nodo.altura != altura_real:
                errores_metadatos.append(
                    f"SIS-{evento.id:06d}: altura almacenada {nodo.altura} != recalculada {altura_real}."
                )
            factor = altura_izq - altura_der
            if abs(factor) > 1:
                desbalanceados.append((evento.id, factor))
            return altura_real

        altura = visitar(arbol.raiz, None, None) if arbol else 0
        return {
            "orden_ok": not errores_orden,
            "metadatos_ok": not errores_metadatos,
            "balanceado": not desbalanceados,
            "desbalanceados": desbalanceados,
            "errores_orden": errores_orden,
            "errores_metadatos": errores_metadatos,
            "altura": altura,
            "total_nodos": total[0],
        }

    def puede_volver_a_modo_normal(self) -> Tuple[bool, dict]:
        """Returning to normal mode is only allowed when the audit confirms the balance."""
        auditoria = self.auditar_arbol()
        return auditoria["balanceado"] and auditoria["orden_ok"], auditoria

    def recuperar_equilibrio_global(self) -> dict:
        """
        Uses AVL.recuperar_equilibrio(L) (rotations over the existing nodes, no rebuild),
        then audits. Normal mode is only kept if the audit confirms the balance.
        """
        arbol = self._obtener_arbol()
        auditoria_previa = self.auditar_arbol()
        rotaciones_previas = self._copiar_rotaciones()

        arbol.recuperar_equilibrio(self.escenario.L)

        auditoria_final = self.auditar_arbol()
        confirmado = auditoria_final["balanceado"] and auditoria_final["orden_ok"]
        if not confirmado:
            arbol.modo_estres = True  # audit failed: stay in stress mode

        return {
            "confirmado": confirmado,
            "auditoria_previa": auditoria_previa,
            "auditoria_final": auditoria_final,
            "rotaciones": self._diferencia_rotaciones(rotaciones_previas),
        }

    # ==================================================================
    # DEMO BURST (section 8: highs, confirmations, old reports, key changes)
    # ==================================================================

    def _siguiente_id_libre(self, desde: int) -> int:
        ocupados = set(self.escenario.dict_eventos) | {e.id for e in self.escenario.historico}
        while desde in ocupados:
            desde += 1
        return desde

    def generar_rafaga_demostracion(self) -> Tuple[bool, str]:
        estaciones = list(self.escenario.estaciones)
        if not estaciones:
            return False, "Se necesita al menos una estación para generar la ráfaga."

        id_a = self._siguiente_id_libre(900001)
        id_b = self._siguiente_id_libre(id_a + 1)
        fecha = (self._reloj_utc() - timedelta(hours=2)).strftime(FORMATO_FECHA_ISO)

        # (id, revision, magnitude, depth, x, y)
        plan = [
            (id_a, 1, 6.5, 10.0, 500.0, 500.0),  # new high-priority event
            (id_a, 1, 6.5, 10.0, 500.0, 500.0),  # confirmation from another station
            (id_b, 1, 4.6, 20.0, 300.0, 300.0),  # another new event
            (id_a, 2, 4.8, 70.0, 500.0, 500.0),  # correction that changes the key
            (id_a, 1, 6.5, 10.0, 500.0, 500.0),  # old report (lower revision)
            (id_a, 2, 5.9, 70.0, 500.0, 500.0),  # conflict (same revision, other data)
        ]
        reportes = []
        for indice, (id_evento, revision, mag, prof, x, y) in enumerate(plan):
            estacion = estaciones[indice % len(estaciones)]
            valido, mensaje, evento = self.crear_evento_reportado(
                id_evento, mag, prof, x, y, fecha, estacion, revision
            )
            if not valido:
                return False, mensaje
            reportes.append((evento, estacion, revision))

        for evento, estacion, revision in reportes:
            self.encolar_reporte(evento, estacion, revision)
        return True, f"Ráfaga de {len(reportes)} reportes encolada (eventos SIS-{id_a:06d} y SIS-{id_b:06d})."