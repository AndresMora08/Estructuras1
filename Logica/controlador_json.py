import json
import os
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from tkinter import filedialog, messagebox

from Modelos.Zona import Zona
from Modelos.Estacion import Estacion
from Modelos.Epicentro import Epicentro
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.Reporte import Reporte
from Modelos.AVL import AVL
from Modelos.BST import ArbolBST

FORMATO_FECHA_ISO = "%Y-%m-%dT%H:%M:%SZ"
TIPO_TOPOLOGIA = "sismolab-topologia"
TIPO_INSERCIONES = "sismolab-inserciones"
VERSION_ESQUEMA = 1
TOLERANCIA = 1e-6
MAXIMO_ERRORES_MOSTRADOS = 15

CLAVES_ROTACIONES = ("LL", "RR", "LR", "RL", "giros_simples")
CLAVES_METRICAS_REPORTES = (
    "nuevos",
    "correcciones_aceptadas",
    "reactivados",
    "confirmaciones",
    "conflictos",
    "descartados_antiguos",
    "rechazados_retirados",
)
ATRIBUTOS_ESCENARIO = (
    "zonas", "estaciones", "epicentros", "reloj", "arbol_avl", "arbol_bst",
    "dict_eventos", "historico", "cola_reportes", "W", "R", "L", "T",
)
_AUSENTE = object()


class _ContextoCarga:
    """Shared state while validating a file: catalogs, clock and collected errors."""

    def __init__(self, reloj: datetime, zonas=None, estaciones=None):
        self.reloj = reloj
        self.zonas: List[Zona] = list(zonas or [])
        self.lista_estaciones: List[Estacion] = list(estaciones or [])
        self.estaciones_por_id: Dict[str, Estacion] = {
            e.id_estacion: e for e in self.lista_estaciones
        }
        self.errores: List[str] = []

    def error(self, mensaje: str) -> None:
        self.errores.append(mensaje)


class ControladorJSON:

    # =========================================================================
    # 1. FILE DIALOGS AND LOW LEVEL I/O
    # =========================================================================
    @staticmethod
    def seleccionar_archivo_guardar(parent_window=None, titulo: str = "Guardar Escenario (JSON)") -> Optional[str]:
        return filedialog.asksaveasfilename(
            parent=parent_window,
            title=titulo,
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
        )

    @staticmethod
    def seleccionar_archivo_cargar(parent_window=None, titulo: str = "Seleccionar Archivo JSON") -> Optional[str]:
        return filedialog.askopenfilename(
            parent=parent_window,
            title=titulo,
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")],
        )

    @staticmethod
    def _escribir_json_atomico(ruta: str, datos: dict) -> None:
        """Writes to a temporary file first so a failure never leaves a half-written file."""
        ruta_temporal = ruta + ".tmp"
        with open(ruta_temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2, ensure_ascii=False, allow_nan=False)
        os.replace(ruta_temporal, ruta)

    @classmethod
    def _leer_archivo_json(cls, parent_window, titulo: str):
        """Returns (ok, datos). Shows an error message when the file cannot be parsed."""
        ruta = cls.seleccionar_archivo_cargar(parent_window, titulo)
        if not ruta:
            return False, None
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                return True, json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            messagebox.showerror("Error de Lectura", f"No se pudo leer el archivo JSON:\n{error}", parent=parent_window)
            return False, None

    @staticmethod
    def _mostrar_errores(titulo: str, errores: List[str], parent_window=None) -> None:
        visibles = errores[:MAXIMO_ERRORES_MOSTRADOS]
        texto = "\n".join(f"- {e}" for e in visibles)
        restantes = len(errores) - len(visibles)
        if restantes > 0:
            texto += f"\n... y {restantes} problema(s) más."
        messagebox.showerror(
            titulo,
            f"Se detectaron {len(errores)} problema(s):\n\n{texto}\n\n"
            "El escenario anterior se conserva sin modificaciones.",
            parent=parent_window,
        )

    # =========================================================================
    # 2. SMALL VALUE HELPERS
    # =========================================================================
    @staticmethod
    def _a_numero(valor) -> Optional[float]:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            return None
        if valor != valor or valor in (float("inf"), float("-inf")):
            return None
        return float(valor)

    @staticmethod
    def _a_entero(valor) -> Optional[int]:
        if isinstance(valor, bool) or not isinstance(valor, int):
            return None
        return valor

    @staticmethod
    def _tiene_maximo_un_decimal(valor: float) -> bool:
        return abs(valor * 10 - round(valor * 10)) < TOLERANCIA

    @staticmethod
    def _parsear_fecha(texto) -> Optional[datetime]:
        if not isinstance(texto, str):
            return None
        try:
            return datetime.strptime(texto.strip(), FORMATO_FECHA_ISO).replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _normalizar_reloj(reloj: datetime) -> datetime:
        if reloj.tzinfo is None:
            reloj = reloj.replace(tzinfo=timezone.utc)
        return reloj.replace(microsecond=0)

    @classmethod
    def _reloj_a_texto(cls, reloj: datetime) -> str:
        return cls._normalizar_reloj(reloj).strftime(FORMATO_FECHA_ISO)

    @staticmethod
    def _fecha_a_texto(fecha_hora) -> str:
        if isinstance(fecha_hora, datetime):
            return fecha_hora.strftime(FORMATO_FECHA_ISO)
        return str(fecha_hora)

    @classmethod
    def _validar_numero(cls, datos: dict, campo: str, minimo: float, maximo: float, etiqueta: str, ctx) -> Optional[float]:
        valor = cls._a_numero(datos.get(campo))
        if valor is None:
            ctx.error(f"{etiqueta}: '{campo}' debe ser un número finito.")
            return None
        if not (minimo <= valor <= maximo):
            ctx.error(f"{etiqueta}: '{campo}' = {valor} fuera de rango [{minimo}, {maximo}].")
            return None
        if not cls._tiene_maximo_un_decimal(valor):
            ctx.error(f"{etiqueta}: '{campo}' = {valor} admite máximo un decimal.")
            return None
        return valor

    # =========================================================================
    # 3. SERIALIZATION (scenario -> dict)
    # =========================================================================
    @classmethod
    def _serializar_evento(cls, evento: Evento) -> dict:
        epicentro = evento.epicentro
        return {
            "id_evento": evento.id,
            "magnitud": evento.magnitud,
            "profundidad": evento.profundidad,
            "epicentro": {"x": epicentro.x, "y": epicentro.y} if epicentro else None,
            "estacion_origen": evento.estacion_origen.id_estacion if evento.estacion_origen else None,
            "fecha_hora": cls._fecha_a_texto(evento.fecha_hora),
            "revision": evento.revision,
            "estado_atencion": evento.estado,
            "estado_catalogo": evento.estado_catalogo,
            "id_referencia": evento.id_referencia,
            "estaciones": list(evento.estaciones),
            "prioridad": evento.prioridad,
            "clave": [evento.clave[0], evento.clave[1], evento.clave[2]],
        }

    @staticmethod
    def _serializar_zonas(zonas) -> List[dict]:
        return [
            {
                "nombre": z.nombre,
                "x_min": z.x_min,
                "x_max": z.x_max,
                "y_min": z.y_min,
                "y_max": z.y_max,
                "poblada": bool(z.poblada),
            }
            for z in zonas
        ]

    @staticmethod
    def _serializar_estaciones(estaciones) -> List[dict]:
        return [
            {
                "id_estacion": e.id_estacion,
                "nombre": e.nombre,
                "x": e.x,
                "y": e.y,
                "zona": e.zona.nombre if e.zona else None,
            }
            for e in estaciones
        ]

    @classmethod
    def _serializar_arbol(cls, raiz) -> dict:
        """Preorder traversal (iterative) into a flat node table with explicit links."""
        if raiz is None:
            return {"raiz": None, "nodos": []}

        nodos = []
        vistos = set()
        pila = [raiz]
        while pila:
            nodo = pila.pop()
            if id(nodo) in vistos:
                continue  # safety guard against corrupted in-memory cycles
            vistos.add(id(nodo))

            altura_izq = nodo.izquierda.altura if nodo.izquierda is not None else 0
            altura_der = nodo.derecha.altura if nodo.derecha is not None else 0
            nodos.append({
                "evento": cls._serializar_evento(nodo.evento),
                "izquierdo": nodo.izquierda.evento.id if nodo.izquierda is not None else None,
                "derecho": nodo.derecha.evento.id if nodo.derecha is not None else None,
                "altura": nodo.altura,
                "factor_balance": altura_izq - altura_der,
            })
            if nodo.derecha is not None:
                pila.append(nodo.derecha)
            if nodo.izquierda is not None:
                pila.append(nodo.izquierda)
        return {"raiz": raiz.evento.id, "nodos": nodos}

    @staticmethod
    def _nodos_por_niveles(raiz) -> list:
        """Level-order list of nodes. Re-inserting in this order rebuilds the same BST shape."""
        resultado = []
        if raiz is None:
            return resultado
        cola = deque([raiz])
        while cola:
            nodo = cola.popleft()
            resultado.append(nodo)
            izquierda = getattr(nodo, "izquierda", None)
            derecha = getattr(nodo, "derecha", None)
            if izquierda is not None:
                cola.append(izquierda)
            if derecha is not None:
                cola.append(derecha)
        return resultado

    @classmethod
    def _serializar_cabecera(cls, escenario, tipo: str) -> dict:
        arbol = getattr(escenario, "arbol_avl", None)
        return {
            "formato": tipo,
            "version": VERSION_ESQUEMA,
            "parametros": {
                "W": escenario.W,
                "R": escenario.R,
                "L": escenario.L,
                "T": escenario.T,
            },
            "reloj": cls._reloj_a_texto(escenario.reloj),
            "modo_ejecucion": {"modo_estres": bool(arbol and arbol.modo_estres)},
            "zonas": cls._serializar_zonas(escenario.zonas),
            "estaciones": cls._serializar_estaciones(escenario.estaciones),
            "epicentros": [{"x": e.x, "y": e.y} for e in escenario.epicentros],
        }

    @classmethod
    def construir_diccionario_topologia(cls, escenario) -> dict:
        """Full operational state: real tree topology, history, queue, clock, params and metrics."""
        arbol = getattr(escenario, "arbol_avl", None)
        datos = cls._serializar_cabecera(escenario, TIPO_TOPOLOGIA)

        cola = []
        for reporte in escenario.cola_reportes:
            cola.append({
                "revision": reporte.revision,
                "estacion_emisora": getattr(reporte.estacion_emisora, "id_estacion", str(reporte.estacion_emisora)),
                "evento": cls._serializar_evento(reporte.evento),
            })

        metricas_reportes = getattr(escenario, "metricas_reportes", {})
        rotaciones = arbol.conteo_rotaciones if arbol else {}

        datos["arbol_activo"] = cls._serializar_arbol(arbol.raiz if arbol else None)
        datos["historico"] = [cls._serializar_evento(e) for e in escenario.historico]
        datos["cola_reportes"] = cola
        datos["metricas"] = {
            "reportes": {k: int(v) for k, v in metricas_reportes.items()},
            "rotaciones": {k: int(v) for k, v in rotaciones.items()},
        }
        return datos

    @classmethod
    def construir_diccionario_inserciones(cls, escenario) -> dict:
        """Active events in level order, ready for the 'load by insertions' mode."""
        arbol = getattr(escenario, "arbol_avl", None)
        raiz = arbol.raiz if arbol else None
        datos = cls._serializar_cabecera(escenario, TIPO_INSERCIONES)
        datos["modo_ejecucion"] = {"modo_estres": False}  # insertion load always balances
        datos["eventos"] = [cls._serializar_evento(n.evento) for n in cls._nodos_por_niveles(raiz)]
        return datos

    # =========================================================================
    # 4. SAVE (with dialogs)
    # =========================================================================
    @classmethod
    def diagnosticar_antes_de_guardar(cls, escenario) -> List[str]:
        """Detects in-memory inconsistencies that would produce a file that cannot be reloaded."""
        problemas: List[str] = []
        arbol = getattr(escenario, "arbol_avl", None)
        ids_arbol = set()

        if arbol is not None and arbol.raiz is not None:
            vistos = set()
            pila = [arbol.raiz]
            while pila:
                nodo = pila.pop()
                if id(nodo) in vistos:
                    problemas.append("El árbol contiene un ciclo.")
                    break
                vistos.add(id(nodo))
                if nodo.evento.id in ids_arbol:
                    problemas.append(f"SIS-{nodo.evento.id:06d} aparece en más de un nodo del árbol.")
                ids_arbol.add(nodo.evento.id)
                if nodo.izquierda is not None:
                    pila.append(nodo.izquierda)
                if nodo.derecha is not None:
                    pila.append(nodo.derecha)

        ids_diccionario = set(escenario.dict_eventos.keys())
        for id_evento in sorted(ids_diccionario - ids_arbol):
            problemas.append(f"SIS-{id_evento:06d} está en eventos activos pero no en el árbol AVL.")
        for id_evento in sorted(ids_arbol - ids_diccionario):
            problemas.append(f"SIS-{id_evento:06d} está en el árbol AVL pero no en eventos activos.")

        ids_historico = [e.id for e in escenario.historico]
        for id_evento in sorted(set(ids_historico) & ids_diccionario):
            problemas.append(f"SIS-{id_evento:06d} está a la vez en eventos activos y en el histórico.")
        return problemas

    @classmethod
    def _guardar_con_dialogo(cls, escenario, parent_window, titulo: str, constructor) -> bool:
        problemas = cls.diagnosticar_antes_de_guardar(escenario)
        if problemas:
            detalle = "\n".join(f"- {p}" for p in problemas[:MAXIMO_ERRORES_MOSTRADOS])
            continuar = messagebox.askyesno(
                "Inconsistencias antes de guardar",
                "El escenario actual tiene inconsistencias; el archivo resultante podría ser "
                f"rechazado al cargarlo:\n\n{detalle}\n\n¿Guardar de todas formas?",
                parent=parent_window,
            )
            if not continuar:
                return False

        ruta = cls.seleccionar_archivo_guardar(parent_window, titulo)
        if not ruta:
            return False

        try:
            cls._escribir_json_atomico(ruta, constructor(escenario))
        except Exception as error:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar el archivo:\n{error}", parent=parent_window)
            return False

        messagebox.showinfo("Éxito", f"Archivo guardado en:\n{ruta}", parent=parent_window)
        return True

    @classmethod
    def guardar_escenario_completo(cls, escenario, parent_window=None) -> bool:
        """Saves the full operational state (topology mode)."""
        return cls._guardar_con_dialogo(
            escenario, parent_window, "Guardar Escenario Estructural (Topología)", cls.construir_diccionario_topologia
        )

    @classmethod
    def guardar_para_inserciones(cls, escenario, parent_window=None) -> bool:
        """Saves the active events in level order (insertion mode)."""
        return cls._guardar_con_dialogo(
            escenario, parent_window, "Guardar Eventos para Carga por Inserciones", cls.construir_diccionario_inserciones
        )

    # =========================================================================
    # 5. VALIDATION BUILDERS (dict -> model objects, collecting every error)
    # =========================================================================
    @classmethod
    def _crear_zona(cls, datos, ctx, etiqueta: str, nombres_usados: set) -> Optional[Zona]:
        if not isinstance(datos, dict):
            ctx.error(f"{etiqueta}: debe ser un objeto JSON.")
            return None
        nombre = datos.get("nombre")
        if not isinstance(nombre, str) or not nombre.strip():
            ctx.error(f"{etiqueta}: 'nombre' debe ser un texto no vacío.")
            return None
        nombre = nombre.strip()
        if nombre.lower() in nombres_usados:
            ctx.error(f"{etiqueta}: nombre de zona duplicado '{nombre}'.")
            return None

        limites = [cls._a_numero(datos.get(c)) for c in ("x_min", "x_max", "y_min", "y_max")]
        if any(v is None for v in limites):
            ctx.error(f"Zona '{nombre}': los límites deben ser números.")
            return None
        x_min, x_max, y_min, y_max = limites
        if not all(0.0 <= v <= 1000.0 for v in limites):
            ctx.error(f"Zona '{nombre}': los límites deben estar entre 0 y 1000.")
            return None
        if x_min >= x_max or y_min >= y_max:
            ctx.error(f"Zona '{nombre}': los mínimos deben ser menores que los máximos.")
            return None

        poblada = datos.get("poblada", datos.get("es_poblada", False))
        if not isinstance(poblada, bool):
            ctx.error(f"Zona '{nombre}': 'poblada' debe ser true o false.")
            return None

        nombres_usados.add(nombre.lower())
        return Zona(nombre, x_min, x_max, y_min, y_max, poblada)

    @classmethod
    def _construir_zonas(cls, lista, ctx) -> None:
        ctx.zonas = []
        if not isinstance(lista, list):
            ctx.error("'zonas' debe ser una lista.")
            return
        nombres_usados: set = set()
        for indice, datos in enumerate(lista):
            zona = cls._crear_zona(datos, ctx, f"Zona #{indice + 1}", nombres_usados)
            if zona is not None:
                ctx.zonas.append(zona)

    @classmethod
    def _crear_estacion(cls, datos, ctx, etiqueta: str) -> Optional[Estacion]:
        if not isinstance(datos, dict):
            ctx.error(f"{etiqueta}: la estación debe ser un objeto JSON.")
            return None
        errores_iniciales = len(ctx.errores)

        id_estacion = datos.get("id_estacion")
        if isinstance(id_estacion, int) and not isinstance(id_estacion, bool):
            id_estacion = str(id_estacion)
        if not isinstance(id_estacion, str) or not id_estacion.strip():
            ctx.error(f"{etiqueta}: 'id_estacion' debe ser un texto no vacío.")
            return None
        id_estacion = id_estacion.strip()
        etiqueta = f"Estación {id_estacion}"

        nombre = datos.get("nombre")
        if not isinstance(nombre, str) or not nombre.strip():
            ctx.error(f"{etiqueta}: 'nombre' debe ser un texto no vacío.")
        x = cls._validar_numero(datos, "x", 0.0, 1000.0, etiqueta, ctx)
        y = cls._validar_numero(datos, "y", 0.0, 1000.0, etiqueta, ctx)

        zona = None
        nombre_zona = datos.get("zona")
        if nombre_zona is not None:
            zona = next((z for z in ctx.zonas if z.nombre == nombre_zona), None)
            if zona is None:
                ctx.error(f"{etiqueta}: la zona '{nombre_zona}' no existe.")

        if len(ctx.errores) > errores_iniciales:
            return None
        try:
            return Estacion(id_estacion=id_estacion, nombre=nombre, x=x, y=y, zona=zona)
        except ValueError as error:
            ctx.error(f"{etiqueta}: {error}")
            return None

    @classmethod
    def _construir_estaciones(cls, lista, ctx) -> None:
        ctx.lista_estaciones = []
        ctx.estaciones_por_id = {}
        if not isinstance(lista, list):
            ctx.error("'estaciones' debe ser una lista.")
            return
        for indice, datos in enumerate(lista):
            estacion = cls._crear_estacion(datos, ctx, f"Estación #{indice + 1}")
            if estacion is None:
                continue
            if estacion.id_estacion in ctx.estaciones_por_id:
                ctx.error(f"Estación {estacion.id_estacion}: identificador duplicado.")
                continue
            ctx.lista_estaciones.append(estacion)
            ctx.estaciones_por_id[estacion.id_estacion] = estacion

    @classmethod
    def _construir_epicentros(cls, lista, ctx) -> List[Epicentro]:
        epicentros: List[Epicentro] = []
        if not isinstance(lista, list):
            ctx.error("'epicentros' debe ser una lista.")
            return epicentros
        for indice, datos in enumerate(lista):
            etiqueta = f"Epicentro #{indice + 1}"
            if not isinstance(datos, dict):
                ctx.error(f"{etiqueta}: debe ser un objeto JSON.")
                continue
            x = cls._validar_numero(datos, "x", 0.0, 1000.0, etiqueta, ctx)
            y = cls._validar_numero(datos, "y", 0.0, 1000.0, etiqueta, ctx)
            if x is not None and y is not None:
                epicentros.append(Epicentro(x, y, ctx.zonas))
        return epicentros

    @classmethod
    def _leer_parametros(cls, datos_parametros, escenario, ctx) -> dict:
        parametros = {
            "W": float(escenario.W),
            "R": float(escenario.R),
            "L": int(escenario.L),
            "T": float(escenario.T),
        }
        if datos_parametros is None:
            return parametros
        if not isinstance(datos_parametros, dict):
            ctx.error("'parametros' debe ser un objeto JSON.")
            return parametros

        for nombre in ("W", "R", "T"):
            if nombre in datos_parametros:
                valor = cls._a_numero(datos_parametros[nombre])
                if valor is None or valor <= 0:
                    ctx.error(f"Parámetro {nombre} debe ser un número positivo.")
                else:
                    parametros[nombre] = valor
        if "L" in datos_parametros:
            valor = cls._a_entero(datos_parametros["L"])
            if valor is None or valor < 0:
                ctx.error("Parámetro L debe ser un entero no negativo.")
            else:
                parametros["L"] = valor
        return parametros

    @classmethod
    def _resolver_estacion(cls, valor, ctx, etiqueta: str) -> Optional[Estacion]:
        """Station by id; a full station object is also accepted (it is created if unknown)."""
        if valor is None:
            ctx.error(f"{etiqueta}: falta 'estacion_origen'.")
            return None
        if isinstance(valor, str):
            estacion = ctx.estaciones_por_id.get(valor.strip())
            if estacion is None:
                ctx.error(f"{etiqueta}: la estación '{valor}' no existe en el escenario.")
            return estacion
        if isinstance(valor, dict):
            id_estacion = str(valor.get("id_estacion", "")).strip()
            if id_estacion in ctx.estaciones_por_id:
                return ctx.estaciones_por_id[id_estacion]
            estacion = cls._crear_estacion(valor, ctx, etiqueta)
            if estacion is not None:
                ctx.lista_estaciones.append(estacion)
                ctx.estaciones_por_id[estacion.id_estacion] = estacion
            return estacion
        ctx.error(f"{etiqueta}: 'estacion_origen' debe ser un identificador de estación.")
        return None

    @staticmethod
    def _clave_coincide(valor, esperado: tuple) -> bool:
        try:
            return (
                isinstance(valor, list)
                and len(valor) == 3
                and int(valor[0]) == esperado[0]
                and abs(float(valor[1]) - esperado[1]) < TOLERANCIA
                and int(valor[2]) == esperado[2]
            )
        except (TypeError, ValueError):
            return False

    @classmethod
    def _construir_evento(cls, datos, ctx, etiqueta: str, catalogos_permitidos: tuple) -> Optional[Evento]:
        """Validates one event dict and builds the Evento. Derived values are re-checked."""
        if not isinstance(datos, dict):
            ctx.error(f"{etiqueta}: el evento debe ser un objeto JSON.")
            return None
        errores_iniciales = len(ctx.errores)

        id_evento = cls._a_entero(datos.get("id_evento", datos.get("id")))
        if id_evento is None or not (1 <= id_evento <= 999999):
            ctx.error(f"{etiqueta}: 'id_evento' debe ser un entero entre 1 y 999999.")
            return None
        etiqueta = f"SIS-{id_evento:06d}"

        magnitud = cls._validar_numero(datos, "magnitud", -2.0, 10.0, etiqueta, ctx)
        profundidad = cls._validar_numero(datos, "profundidad", 0.0, 700.0, etiqueta, ctx)

        x = y = None
        datos_epicentro = datos.get("epicentro")
        if isinstance(datos_epicentro, dict):
            x = cls._validar_numero(datos_epicentro, "x", 0.0, 1000.0, f"{etiqueta} (epicentro)", ctx)
            y = cls._validar_numero(datos_epicentro, "y", 0.0, 1000.0, f"{etiqueta} (epicentro)", ctx)
        else:
            ctx.error(f"{etiqueta}: falta el objeto 'epicentro' con x e y.")

        estacion_origen = cls._resolver_estacion(datos.get("estacion_origen"), ctx, etiqueta)

        fecha = cls._parsear_fecha(datos.get("fecha_hora"))
        if fecha is None:
            ctx.error(f"{etiqueta}: 'fecha_hora' debe tener formato 2026-09-07T10:00:00Z.")
        elif fecha > ctx.reloj:
            ctx.error(
                f"{etiqueta}: la fecha {datos.get('fecha_hora')} es posterior al reloj de simulación "
                f"({ctx.reloj.strftime(FORMATO_FECHA_ISO)})."
            )

        revision = cls._a_entero(datos.get("revision", 1))
        if revision is None or revision < 1:
            ctx.error(f"{etiqueta}: 'revision' debe ser un entero positivo.")

        estado_texto = datos.get("estado_atencion", datos.get("estado", "Pendiente"))
        estado = None
        if isinstance(estado_texto, str) and estado_texto.strip().lower() in ("pendiente", "revisado"):
            estado = "Pendiente" if estado_texto.strip().lower() == "pendiente" else "Revisado"
        else:
            ctx.error(f"{etiqueta}: 'estado_atencion' debe ser Pendiente o Revisado.")

        catalogo = datos.get("estado_catalogo", "Activo")
        if catalogo not in catalogos_permitidos:
            ctx.error(f"{etiqueta}: 'estado_catalogo' debe ser {' o '.join(catalogos_permitidos)} (recibido: {catalogo!r}).")

        id_referencia = datos.get("id_referencia")
        if id_referencia is not None:
            id_referencia = cls._a_entero(id_referencia)
            if id_referencia is None or id_referencia < 1:
                ctx.error(f"{etiqueta}: 'id_referencia' debe ser null o un identificador entero válido.")

        estaciones = datos.get("estaciones")
        if estaciones is not None:
            if not isinstance(estaciones, list) or not all(isinstance(e, str) for e in estaciones):
                ctx.error(f"{etiqueta}: 'estaciones' debe ser una lista de identificadores.")
            else:
                for id_estacion in estaciones:
                    if id_estacion not in ctx.estaciones_por_id:
                        ctx.error(f"{etiqueta}: la estación '{id_estacion}' de la lista no existe.")

        if len(ctx.errores) > errores_iniciales:
            return None

        epicentro = Epicentro(x, y, ctx.zonas)
        evento = Evento(
            id_evento=id_evento,
            magnitud=magnitud,
            profundidad=profundidad,
            epicentro=epicentro,
            estacion_origen=estacion_origen,
            fecha_hora=fecha.strftime(FORMATO_FECHA_ISO),
            estado=estado,
            estado_catalogo=catalogo,
            id_referencia=id_referencia,
            revision=revision,
        )
        if estaciones is not None:
            evento.estaciones = list(dict.fromkeys(estaciones))

        # Stored derived values must match the calculated ones
        if "prioridad" in datos and cls._a_entero(datos["prioridad"]) != evento.prioridad:
            ctx.error(f"{etiqueta}: prioridad almacenada {datos['prioridad']} != calculada {evento.prioridad}.")
        if "clave" in datos and not cls._clave_coincide(datos["clave"], evento.clave):
            ctx.error(f"{etiqueta}: clave almacenada {datos['clave']} != calculada {list(evento.clave)}.")

        if len(ctx.errores) > errores_iniciales:
            return None
        return evento

    @classmethod
    def _validar_referencias(cls, activos: Dict[int, Evento], archivados: Dict[int, Evento], retirados: set, ctx) -> None:
        """References must point to active/archived events (not removed) and never form cycles."""
        visibles: Dict[int, Evento] = {}
        visibles.update(archivados)
        visibles.update(activos)

        for id_evento, evento in visibles.items():
            referencia = evento.id_referencia
            if referencia is None or referencia == id_evento:
                continue
            if referencia in retirados:
                ctx.error(f"SIS-{id_evento:06d}: referencia al evento eliminado SIS-{referencia:06d}.")
            elif referencia not in visibles:
                ctx.error(f"SIS-{id_evento:06d}: referencia a un evento inexistente SIS-{referencia:06d}.")

        reportados: set = set()
        for inicio in visibles:
            if inicio in reportados:
                continue
            camino: List[int] = []
            vistos: set = set()
            actual = inicio
            while actual is not None and actual in visibles and actual not in vistos:
                vistos.add(actual)
                camino.append(actual)
                actual = visibles[actual].id_referencia
            if actual is not None and actual in vistos:
                ciclo = camino[camino.index(actual):]
                ctx.error("Ciclo de referencias: " + " -> ".join(f"SIS-{i:06d}" for i in ciclo + [actual]))
                reportados.update(ciclo)

    @classmethod
    def _leer_metricas(cls, datos_metricas, ctx) -> Tuple[dict, dict]:
        reportes = {clave: 0 for clave in CLAVES_METRICAS_REPORTES}
        rotaciones = {clave: 0 for clave in CLAVES_ROTACIONES}
        if datos_metricas is None:
            return reportes, rotaciones
        if not isinstance(datos_metricas, dict):
            ctx.error("'metricas' debe ser un objeto JSON.")
            return reportes, rotaciones

        for seccion, destino in (("reportes", reportes), ("rotaciones", rotaciones)):
            valores = datos_metricas.get(seccion, {})
            if not isinstance(valores, dict):
                ctx.error(f"'metricas.{seccion}' debe ser un objeto JSON.")
                continue
            for clave, valor in valores.items():
                entero = cls._a_entero(valor)
                if clave not in destino:
                    ctx.error(f"Métrica desconocida 'metricas.{seccion}.{clave}'.")
                elif entero is None or entero < 0:
                    ctx.error(f"Métrica 'metricas.{seccion}.{clave}' debe ser un entero no negativo.")
                else:
                    destino[clave] = entero
        return reportes, rotaciones

    # =========================================================================
    # 6. TOPOLOGY: validation and reconstruction (no re-insertions)
    # =========================================================================
    @classmethod
    def _reconstruir_arbol(cls, datos_arbol, ctx):
        """
        Returns (root Nodo, is_unbalanced, {id: Evento}).
        Checks links, single position, no cycles, global BST order, heights and balance factors.
        """
        eventos_activos: Dict[int, Evento] = {}
        
        # NUEVO: Si el árbol es null/None, lo aceptamos como un árbol vacío
        if datos_arbol is None:
            return None, False, eventos_activos
            
        if not isinstance(datos_arbol, dict) or not isinstance(datos_arbol.get("nodos"), list):
            ctx.error("El árbol debe ser null o un objeto con la lista 'nodos' y la clave 'raiz'.")
            return None, False, eventos_activos

        errores_iniciales = len(ctx.errores)
        entradas: Dict[int, dict] = {}
        nodos: Dict[int, Nodo] = {}

        for indice, entrada in enumerate(datos_arbol["nodos"]):
            etiqueta = f"Nodo #{indice + 1}"
            if not isinstance(entrada, dict):
                ctx.error(f"{etiqueta}: debe ser un objeto JSON.")
                continue
            evento = cls._construir_evento(entrada.get("evento"), ctx, etiqueta, ("Activo",))
            if evento is None:
                continue
            if evento.id in nodos:
                ctx.error(f"SIS-{evento.id:06d}: aparece en más de una posición del árbol.")
                continue
            entradas[evento.id] = entrada
            nodos[evento.id] = Nodo(evento=evento)
            eventos_activos[evento.id] = evento

        if len(ctx.errores) > errores_iniciales:
            return None, False, eventos_activos

        # Explicit links
        padres: Dict[int, int] = {}
        for id_nodo, entrada in entradas.items():
            for lado, atributo in (("izquierdo", "izquierda"), ("derecho", "derecha")):
                bruto = entrada.get(lado)
                if bruto is None:
                    continue
                destino = cls._a_entero(bruto)
                if destino is None or destino not in nodos:
                    ctx.error(f"SIS-{id_nodo:06d}: enlace {lado} inválido ({bruto!r}).")
                    continue
                if destino == id_nodo:
                    ctx.error(f"SIS-{id_nodo:06d}: el enlace {lado} apunta a sí mismo.")
                    continue
                if destino in padres:
                    ctx.error(
                        f"SIS-{destino:06d}: tiene más de un padre "
                        f"(SIS-{padres[destino]:06d} y SIS-{id_nodo:06d})."
                    )
                    continue
                padres[destino] = id_nodo
                setattr(nodos[id_nodo], atributo, nodos[destino])

        # Root
        raiz = None
        id_raiz = datos_arbol.get("raiz")
        if id_raiz is None:
            if nodos:
                ctx.error("El árbol tiene nodos pero 'raiz' es null.")
        else:
            id_raiz = cls._a_entero(id_raiz)
            if id_raiz is None or id_raiz not in nodos:
                ctx.error("'raiz' no corresponde a ningún nodo del árbol.")
            elif id_raiz in padres:
                ctx.error(f"La raíz SIS-{id_raiz:06d} aparece como hijo de SIS-{padres[id_raiz]:06d} (ciclo).")
            else:
                raiz = nodos[id_raiz]

        if len(ctx.errores) > errores_iniciales or raiz is None:
            return None, False, eventos_activos

        # Reachability (also detects cycles among unreachable nodes)
        preorden: List[Nodo] = []
        visitados = set()
        pila = [raiz]
        while pila:
            nodo = pila.pop()
            if id(nodo) in visitados:
                ctx.error(f"SIS-{nodo.evento.id:06d}: aparece en más de una posición del árbol.")
                continue
            visitados.add(id(nodo))
            preorden.append(nodo)
            if nodo.derecha is not None:
                pila.append(nodo.derecha)
            if nodo.izquierda is not None:
                pila.append(nodo.izquierda)

        if len(preorden) != len(nodos):
            alcanzados = {n.evento.id for n in preorden}
            huerfanos = sorted(set(nodos) - alcanzados)
            ctx.error(
                "Nodos no alcanzables desde la raíz (ciclo o enlaces rotos): "
                + ", ".join(f"SIS-{i:06d}" for i in huerfanos[:10])
            )
            return None, False, eventos_activos

        # Global BST order by K = (P, M, I)
        pila_orden = [(raiz, None, None)]
        while pila_orden:
            nodo, minimo, maximo = pila_orden.pop()
            clave = nodo.clave
            if (minimo is not None and clave <= minimo) or (maximo is not None and clave >= maximo):
                ctx.error(f"SIS-{nodo.evento.id:06d}: la clave {clave} viola el orden BST global.")
            if nodo.izquierda is not None:
                pila_orden.append((nodo.izquierda, minimo, clave))
            if nodo.derecha is not None:
                pila_orden.append((nodo.derecha, clave, maximo))

        # Recomputed heights and balance factors against the stored ones
        alturas: Dict[int, int] = {}
        desbalanceado = False
        for nodo in reversed(preorden):  # children always appear after their parent in preorder
            altura_izq = alturas[id(nodo.izquierda)] if nodo.izquierda is not None else 0
            altura_der = alturas[id(nodo.derecha)] if nodo.derecha is not None else 0
            altura = 1 + max(altura_izq, altura_der)
            factor = altura_izq - altura_der
            alturas[id(nodo)] = altura

            entrada = entradas[nodo.evento.id]
            altura_guardada = cls._a_entero(entrada.get("altura"))
            factor_guardado = cls._a_entero(entrada.get("factor_balance"))
            if altura_guardada != altura:
                ctx.error(f"SIS-{nodo.evento.id:06d}: altura almacenada {altura_guardada} != recalculada {altura}.")
            if factor_guardado != factor:
                ctx.error(f"SIS-{nodo.evento.id:06d}: factor de balance almacenado {factor_guardado} != recalculado {factor}.")
            if abs(factor) > 1:
                desbalanceado = True
            nodo.altura = altura

        return raiz, desbalanceado, eventos_activos

    @classmethod
    def _construir_historico(cls, lista, ctx) -> Dict[int, Evento]:
        historico: Dict[int, Evento] = {}
        if not isinstance(lista, list):
            ctx.error("'historico' debe ser una lista.")
            return historico
        for indice, datos in enumerate(lista):
            evento = cls._construir_evento(datos, ctx, f"Histórico #{indice + 1}", ("Archivado", "Retirado"))
            if evento is None:
                continue
            if evento.id in historico:
                ctx.error(f"SIS-{evento.id:06d}: identificador duplicado en el histórico.")
                continue
            historico[evento.id] = evento
        return historico

    @classmethod
    def _construir_cola(cls, lista, ctx) -> List[Reporte]:
        cola: List[Reporte] = []
        if not isinstance(lista, list):
            ctx.error("'cola_reportes' debe ser una lista.")
            return cola
        for indice, entrada in enumerate(lista):
            etiqueta = f"Reporte en cola #{indice + 1}"
            if not isinstance(entrada, dict):
                ctx.error(f"{etiqueta}: debe ser un objeto JSON.")
                continue
            revision = cls._a_entero(entrada.get("revision"))
            if revision is None or revision < 1:
                ctx.error(f"{etiqueta}: 'revision' debe ser un entero positivo.")
                continue
            id_emisora = entrada.get("estacion_emisora")
            estacion = ctx.estaciones_por_id.get(id_emisora) if isinstance(id_emisora, str) else None
            if estacion is None:
                ctx.error(f"{etiqueta}: la estación emisora {id_emisora!r} no existe.")
                continue
            datos_evento = entrada.get("evento")
            if not isinstance(datos_evento, dict):
                ctx.error(f"{etiqueta}: falta el objeto 'evento'.")
                continue
            datos_evento = dict(datos_evento)
            datos_evento.setdefault("estacion_origen", id_emisora)
            datos_evento["revision"] = revision
            evento = cls._construir_evento(datos_evento, ctx, etiqueta, ("Activo",))
            if evento is not None:
                cola.append(Reporte(evento=evento, estacion_emisora=estacion, revision=revision))
        return cola

    @classmethod
    def _construir_bst_desde_arbol(cls, raiz) -> ArbolBST:
        """Comparison BST: same events inserted in level order (same comparator, no balancing)."""
        bst = ArbolBST()
        for nodo in cls._nodos_por_niveles(raiz):
            bst.insertar(nodo.evento)
        return bst

    @classmethod
    def validar_topologia(cls, datos, escenario) -> Tuple[Optional[dict], List[str], List[str]]:
        """Returns (new state or None, errors, warnings). Nothing is applied here."""
        if not isinstance(datos, dict):
            return None, ["El archivo de topología debe ser un objeto JSON."], []
            
        # NUEVO: Busca la clave que exista en el JSON
        clave_arbol = "arbol_activo" if "arbol_activo" in datos else "arbol_avl"
        
        if clave_arbol not in datos:
            return None, ["Falta la sección del árbol AVL (¿es un archivo de inserciones?)."], []
        if datos.get("version", VERSION_ESQUEMA) != VERSION_ESQUEMA:
            return None, [f"Versión de esquema no soportada: {datos.get('version')}."], []

        reloj = cls._normalizar_reloj(escenario.reloj)
        errores_reloj: List[str] = []
        if "reloj" in datos:
            reloj_leido = cls._parsear_fecha(datos["reloj"])
            if reloj_leido is None:
                errores_reloj.append("'reloj' debe tener formato 2026-09-07T10:00:00Z.")
            else:
                reloj = reloj_leido

        ctx = _ContextoCarga(reloj)
        ctx.errores.extend(errores_reloj)
        cls._construir_zonas(datos.get("zonas", []), ctx)
        cls._construir_estaciones(datos.get("estaciones", []), ctx)
        epicentros = cls._construir_epicentros(datos.get("epicentros", []), ctx)
        parametros = cls._leer_parametros(datos.get("parametros"), escenario, ctx)
        if ctx.errores:
            return None, ctx.errores, []  

        # NUEVO: Usa la clave dinámica aquí
        raiz, desbalanceado, activos = cls._reconstruir_arbol(datos.get(clave_arbol), ctx)
        
        historico = cls._construir_historico(datos.get("historico", []), ctx)
        cola = cls._construir_cola(datos.get("cola_reportes", []), ctx)
        metricas_reportes, rotaciones = cls._leer_metricas(datos.get("metricas"), ctx)

        for id_evento in sorted(set(activos) & set(historico)):
            ctx.error(f"SIS-{id_evento:06d}: identidad duplicada entre eventos activos e histórico.")

        archivados = {i: e for i, e in historico.items() if e.estado_catalogo == "Archivado"}
        retirados = {i for i, e in historico.items() if e.estado_catalogo == "Retirado"}
        cls._validar_referencias(activos, archivados, retirados, ctx)

        modo_archivo = datos.get("modo_ejecucion", {}).get("modo_estres", False)
        if not isinstance(modo_archivo, bool):
            ctx.error("'modo_ejecucion.modo_estres' debe ser true o false.")
            modo_archivo = False
        arbol_actual = getattr(escenario, "arbol_avl", None)
        modo_estres = modo_archivo or bool(arbol_actual and arbol_actual.modo_estres)

        advertencias: List[str] = []
        if desbalanceado and not modo_estres:
            ctx.error(
                "La topología está ordenada pero desbalanceada: solo puede cargarse con el "
                "modo estrés activado (en el archivo o en la aplicación)."
            )
        if desbalanceado and modo_estres:
            advertencias.append("La topología cargada está desbalanceada y se cargó en MODO ESTRÉS.")

        if ctx.errores:
            return None, ctx.errores, []

        arbol = AVL(modo_estres=modo_estres)
        arbol.raiz = raiz
        arbol.conteo_rotaciones = dict(rotaciones)
        arbol.actualizar_profundidades(parametros["L"])

        estado = {
            "zonas": ctx.zonas,
            "estaciones": ctx.lista_estaciones,
            "epicentros": epicentros,
            "reloj": reloj,
            "parametros": parametros,
            "arbol_avl": arbol,
            "arbol_bst": cls._construir_bst_desde_arbol(raiz),
            "dict_eventos": activos,
            "historico": list(historico.values()),
            "cola": cola,
            "metricas_reportes": metricas_reportes,
        }
        return estado, [], advertencias

    # =========================================================================
    # 7. INSERTIONS: validation and reconstruction
    # =========================================================================
    @classmethod
    def validar_inserciones(cls, datos, escenario) -> Tuple[Optional[dict], List[str]]:
        """Builds the AVL (balanced) and the BST with the same insertion order. Nothing is applied."""
        if isinstance(datos, list):
            seccion: dict = {}
            lista_eventos = datos
        elif isinstance(datos, dict):
            seccion = datos
            lista_eventos = datos.get("eventos")
            if seccion.get("version", VERSION_ESQUEMA) != VERSION_ESQUEMA:
                return None, [f"Versión de esquema no soportada: {seccion.get('version')}."]
        else:
            return None, ["El archivo de inserciones debe ser una lista o un objeto JSON con 'eventos'."]
        if not isinstance(lista_eventos, list):
            return None, ["'eventos' debe ser una lista de eventos."]

        reloj = cls._normalizar_reloj(escenario.reloj)
        errores_reloj: List[str] = []
        if "reloj" in seccion:
            reloj_leido = cls._parsear_fecha(seccion["reloj"])
            if reloj_leido is None:
                errores_reloj.append("'reloj' debe tener formato 2026-09-07T10:00:00Z.")
            else:
                reloj = reloj_leido

        ctx = _ContextoCarga(reloj, escenario.zonas, escenario.estaciones)
        ctx.errores.extend(errores_reloj)
        epicentros = list(escenario.epicentros)

        if "zonas" in seccion or "estaciones" in seccion:
            cls._construir_zonas(seccion.get("zonas", []), ctx)
            cls._construir_estaciones(seccion.get("estaciones", []), ctx)
            epicentros = cls._construir_epicentros(seccion.get("epicentros", []), ctx)
        parametros = cls._leer_parametros(seccion.get("parametros"), escenario, ctx)
        if ctx.errores:
            return None, ctx.errores

        activos: Dict[int, Evento] = {}
        for indice, datos_evento in enumerate(lista_eventos):
            evento = cls._construir_evento(datos_evento, ctx, f"Evento #{indice + 1}", ("Activo",))
            if evento is None:
                continue
            if evento.id in activos:
                ctx.error(f"SIS-{evento.id:06d}: identificador duplicado en la secuencia de carga.")
                continue
            activos[evento.id] = evento

        cls._validar_referencias(activos, {}, set(), ctx)
        if ctx.errores:
            return None, ctx.errores

        # Same comparator and same insertion order for both trees
        arbol_avl = AVL(modo_estres=False)
        arbol_bst = ArbolBST()
        for evento in activos.values():
            arbol_avl.insertar(Nodo(evento=evento), parametros["L"])
            arbol_bst.insertar(evento)

        estado = {
            "zonas": ctx.zonas,
            "estaciones": ctx.lista_estaciones,
            "epicentros": epicentros,
            "reloj": reloj,
            "parametros": parametros,
            "arbol_avl": arbol_avl,
            "arbol_bst": arbol_bst,
            "dict_eventos": activos,
            "historico": [],
            "cola": [],
            "metricas_reportes": {clave: 0 for clave in CLAVES_METRICAS_REPORTES},
        }
        return estado, []

    # =========================================================================
    # 8. ATOMIC APPLY
    # =========================================================================
    @classmethod
    def _aplicar_estado(cls, escenario, estado: dict) -> None:
        """Replaces the scenario completely; restores the previous values if anything fails."""
        respaldo = {atributo: getattr(escenario, atributo, _AUSENTE) for atributo in ATRIBUTOS_ESCENARIO}
        metricas_objeto = getattr(escenario, "metricas_reportes", None)
        metricas_copia = dict(metricas_objeto) if isinstance(metricas_objeto, dict) else None

        try:
            parametros = estado["parametros"]
            escenario.zonas = estado["zonas"]
            escenario.estaciones = estado["estaciones"]
            escenario.epicentros = estado["epicentros"]
            escenario.reloj = estado["reloj"]
            escenario.W = parametros["W"]
            escenario.R = parametros["R"]
            escenario.L = parametros["L"]
            escenario.T = parametros["T"]
            escenario.arbol_avl = estado["arbol_avl"]
            escenario.arbol_bst = estado["arbol_bst"]
            escenario.dict_eventos = estado["dict_eventos"]
            escenario.historico = estado["historico"]
            escenario.cola_reportes = deque(estado["cola"])

            # Updated in place so an open reports window keeps pointing to the same dict
            if isinstance(metricas_objeto, dict):
                metricas_objeto.clear()
                metricas_objeto.update(estado["metricas_reportes"])
            else:
                escenario.metricas_reportes = dict(estado["metricas_reportes"])
        except Exception:
            for atributo, valor in respaldo.items():
                if valor is _AUSENTE:
                    if hasattr(escenario, atributo):
                        delattr(escenario, atributo)
                else:
                    setattr(escenario, atributo, valor)
            if isinstance(metricas_objeto, dict) and metricas_copia is not None:
                metricas_objeto.clear()
                metricas_objeto.update(metricas_copia)
            raise

    # =========================================================================
    # 9. RESULT SUMMARIES
    # =========================================================================
    @staticmethod
    def _calcular_metricas_arbol(raiz) -> dict:
        if raiz is None:
            return {"raiz": None, "altura": -1, "profundidad_maxima": -1, "hojas": 0, "nodos": 0}
        profundidad_maxima = 0
        hojas = 0
        nodos = 0
        cola = deque([(raiz, 0)])
        while cola:
            nodo, profundidad = cola.popleft()
            nodos += 1
            profundidad_maxima = max(profundidad_maxima, profundidad)
            izquierda = getattr(nodo, "izquierda", None)
            derecha = getattr(nodo, "derecha", None)
            if izquierda is None and derecha is None:
                hojas += 1
            if izquierda is not None:
                cola.append((izquierda, profundidad + 1))
            if derecha is not None:
                cola.append((derecha, profundidad + 1))
        return {
            "raiz": raiz.evento.id,
            "altura": profundidad_maxima,  # empty tree = -1, leaf = 0
            "profundidad_maxima": profundidad_maxima,
            "hojas": hojas,
            "nodos": nodos,
        }

    @classmethod
    def _resumen_arbol(cls, titulo: str, raiz) -> str:
        m = cls._calcular_metricas_arbol(raiz)
        raiz_texto = f"SIS-{m['raiz']:06d}" if m["raiz"] is not None else "N/A"
        return (
            f"{titulo}\n"
            f"  - Raíz: {raiz_texto}\n"
            f"  - Altura (hoja = 0): {m['altura']}\n"
            f"  - Profundidad máxima: {m['profundidad_maxima']}\n"
            f"  - Cantidad de hojas: {m['hojas']}\n"
            f"  - Nodos: {m['nodos']}"
        )

    # =========================================================================
    # 10. PUBLIC LOAD ENTRY POINTS
    # =========================================================================
    @staticmethod
    def _detectar_tipo(datos) -> str:
        if isinstance(datos, list):
            return "inserciones"
        if isinstance(datos, dict):
            formato = datos.get("formato")
            # Ahora reconoce cualquiera de las dos claves
            if formato == TIPO_TOPOLOGIA or "arbol_activo" in datos or "arbol_avl" in datos:
                return "topologia"
            if formato == TIPO_INSERCIONES or "eventos" in datos:
                return "inserciones"
        return "desconocido"

    @classmethod
    def cargar_por_inserciones(cls, escenario, parent_window=None, lista_eventos=None) -> bool:
        if lista_eventos is None:
            ok, lista_eventos = cls._leer_archivo_json(parent_window, "Seleccionar JSON para Carga por Inserciones")
            if not ok:
                return False
        if cls._detectar_tipo(lista_eventos) == "topologia":
            messagebox.showerror(
                "Tipo de archivo incorrecto",
                "Este archivo es una topología completa. Use 'Cargar Topología'.",
                parent=parent_window,
            )
            return False
        return cls.procesar_carga_por_inserciones(lista_eventos, escenario, parent_window)

    @classmethod
    def procesar_carga_por_inserciones(cls, datos, escenario, parent_window=None) -> bool:
        try:
            estado, errores = cls.validar_inserciones(datos, escenario)
            if errores:
                cls._mostrar_errores("Carga por Inserciones Rechazada", errores, parent_window)
                return False
            cls._aplicar_estado(escenario, estado)
        except Exception as error:
            messagebox.showerror(
                "Carga por Inserciones Rechazada",
                f"Error inesperado: {error}\n\nEl escenario anterior se conserva.",
                parent=parent_window,
            )
            return False

        mensaje = (
            "Carga por Inserciones exitosa.\n"
            f"Eventos cargados: {len(estado['dict_eventos'])}\n"
            "(El histórico y la cola de reportes quedan vacíos.)\n\n"
            + cls._resumen_arbol("Árbol AVL (con balanceo):", estado["arbol_avl"].raiz)
            + "\n\n"
            + cls._resumen_arbol("Árbol BST (sin balanceo):", estado["arbol_bst"].raiz)
        )
        messagebox.showinfo("Resultados de Carga por Inserciones", mensaje, parent=parent_window)
        return True

    @classmethod
    def cargar_por_topologia(cls, escenario, parent_window=None, datos=None) -> bool:
        if datos is None:
            ok, datos = cls._leer_archivo_json(parent_window, "Seleccionar JSON para Carga por Topología")
            if not ok:
                return False
        if cls._detectar_tipo(datos) != "topologia":
            messagebox.showerror(
                "Tipo de archivo incorrecto",
                "El archivo no contiene la sección 'arbol_activo'. Si es una lista de eventos, "
                "use 'Cargar Inserciones'.",
                parent=parent_window,
            )
            return False
        return cls.procesar_carga_por_topologia(datos, escenario, parent_window)

    @classmethod
    def procesar_carga_por_topologia(cls, datos, escenario, parent_window=None) -> bool:
        try:
            estado, errores, advertencias = cls.validar_topologia(datos, escenario)
            if errores:
                cls._mostrar_errores("Carga por Topología Rechazada", errores, parent_window)
                return False
            cls._aplicar_estado(escenario, estado)
        except Exception as error:
            messagebox.showerror(
                "Carga por Topología Rechazada",
                f"Error inesperado: {error}\n\nEl escenario anterior se conserva.",
                parent=parent_window,
            )
            return False

        mensaje = (
            "Topología cargada correctamente.\n\n"
            f"Eventos activos: {len(estado['dict_eventos'])}\n"
            f"Eventos en histórico: {len(estado['historico'])}\n"
            f"Reportes en cola: {len(estado['cola'])}\n"
            f"Modo estrés: {'ACTIVO' if estado['arbol_avl'].modo_estres else 'normal'}"
        )
        if advertencias:
            mensaje += "\n\n" + "\n".join(advertencias)
        messagebox.showinfo("Éxito", mensaje, parent=parent_window)
        return True

    @classmethod
    def cargar_json(cls, escenario, parent_window=None) -> bool:
        """Generic entry point: detects the file type and dispatches to the right loader."""
        ok, datos = cls._leer_archivo_json(parent_window, "Seleccionar Archivo JSON")
        if not ok:
            return False
        tipo = cls._detectar_tipo(datos)
        if tipo == "inserciones":
            return cls.procesar_carga_por_inserciones(datos, escenario, parent_window)
        if tipo == "topologia":
            return cls.procesar_carga_por_topologia(datos, escenario, parent_window)
        messagebox.showerror(
            "Formato no reconocido",
            "El archivo no es una lista/objeto de inserciones ni una topología de SismoLab.",
            parent=parent_window,
        )
        return False