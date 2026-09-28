import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from tkinter import filedialog, messagebox

# Importación de modelos del dominio
from Modelos.Zona import Zona
from Modelos.Estacion import Estacion
from Modelos.Epicentro import Epicentro
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.AVL import AVL
from Modelos.BST import ArbolBST


class ControladorJSON:

    # =========================================================================
    # 1. EXPLORADOR DE ARCHIVOS (I/O)
    # =========================================================================
    @staticmethod
    def seleccionar_archivo_guardar(parent_window=None) -> Optional[str]:
        return filedialog.asksaveasfilename(
            parent=parent_window,
            title="Guardar Escenario Estructural (JSON)",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )

    @staticmethod
    def seleccionar_archivo_cargar(parent_window=None, titulo: str = "Seleccionar Archivo JSON") -> Optional[str]:
        return filedialog.askopenfilename(
            parent=parent_window,
            title=titulo,
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )

    # =========================================================================
    # 2. GUARDADO ESTRUCTURAL COMPLETO
    # =========================================================================
    @classmethod
    def guardar_escenario_completo(cls, escenario, parent_window=None) -> bool:
        ruta = cls.seleccionar_archivo_guardar(parent_window)
        if not ruta:
            return False

        try:
            # Serialización recursiva del árbol activo conservando su topología real
            def _serializar_nodo(nodo: Optional[Nodo]):
                if nodo is None:
                    return None
                ev = nodo.evento
                return {
                    "evento": {
                        "id_evento": getattr(ev, "id_evento", getattr(ev, "id", None)),
                        "magnitud": getattr(ev, "magnitud", 0.0),
                        "profundidad": getattr(ev, "profundidad", 0.0),
                        "fecha_hora": getattr(ev, "fecha_hora", None),
                        "clave": list(getattr(ev, "clave", [])),
                        "prioridad": getattr(ev, "prioridad", None),
                        "estado_atencion": getattr(ev, "estado", getattr(ev, "estado_atencion", "PENDIENTE")),
                        "epicentro": {
                            "x": ev.epicentro.x,
                            "y": ev.epicentro.y,
                            "zona": ev.epicentro.zona.nombre if getattr(ev.epicentro, "zona", None) else None
                        } if getattr(ev, "epicentro", None) else None,
                        "estacion_origen": {
                            "id_estacion": ev.estacion_origen.id_estacion,
                            "nombre": ev.estacion_origen.nombre,
                            "x": ev.estacion_origen.x,
                            "y": ev.estacion_origen.y,
                            "zona": ev.estacion_origen.zona.nombre if getattr(ev.estacion_origen, "zona", None) else None
                        } if getattr(ev, "estacion_origen", None) else None
                    },
                    "altura": getattr(nodo, "altura", 1),
                    "factor_balance": getattr(nodo, "factor_balance", 0),
                    "izquierdo": _serializar_nodo(getattr(nodo, "izquierda", None)),
                    "derecho": _serializar_nodo(getattr(nodo, "derecha", None))
                }

            raiz_nodo = getattr(escenario.arbol_avl, "raiz", None) if getattr(escenario, "arbol_avl", None) else None

            # Construcción del esquema JSON completo
            datos_completos = {
                "parametros": {
                    "W": getattr(escenario, "W", 48.0),
                    "R": getattr(escenario, "R", 40.0),
                    "L": getattr(escenario, "L", 3),
                    "T": getattr(escenario, "T", 72.0),
                    "reloj_simulacion": getattr(escenario, "reloj_simulacion", 0)
                },
                "modo_ejecucion": {
                    "modo_estres": getattr(getattr(escenario, "arbol_avl", None), "modo_estres", False)
                },
                "zonas": [
                    {
                        "nombre": z.nombre,
                        "x_min": z.x_min,
                        "x_max": z.x_max,
                        "y_min": z.y_min,
                        "y_max": z.y_max,
                        "es_poblada": getattr(z, "poblada", False)
                    } for z in getattr(escenario, "zonas", [])
                ],
                "estaciones": [
                    {
                        "id_estacion": est.id_estacion,
                        "nombre": est.nombre,
                        "x": est.x,
                        "y": est.y,
                        "zona": est.zona.nombre if getattr(est, "zona", None) else None
                    } for est in getattr(escenario, "estaciones", [])
                ],
                "epicentros": [
                    {
                        "x": epi.x,
                        "y": epi.y,
                        "zona": epi.zona.nombre if getattr(epi, "zona", None) else None
                    } for epi in getattr(escenario, "epicentros", [])
                ],
                "topologia_arbol": _serializar_nodo(raiz_nodo),
                "cola_reportes": [
                    getattr(r, "evento", r).id if hasattr(getattr(r, "evento", r), "id") else getattr(getattr(r, "evento", r), "id_evento", None)
                    for r in getattr(escenario, "cola_reportes", [])
                ],
                "historico": [
                    {
                        "id_evento": getattr(ev, "id_evento", getattr(ev, "id", None)),
                        "magnitud": getattr(ev, "magnitud", 0.0),
                        "profundidad": getattr(ev, "profundidad", 0.0),
                        "fecha_hora": getattr(ev, "fecha_hora", None),
                        "epicentro": {
                            "x": ev.epicentro.x,
                            "y": ev.epicentro.y,
                            "zona": ev.epicentro.zona.nombre if getattr(ev, "epicentro", None) and getattr(ev.epicentro, "zona", None) else None
                        } if getattr(ev, "epicentro", None) else None,
                        "estacion_origen": {
                            "id_estacion": ev.estacion_origen.id_estacion,
                            "nombre": ev.estacion_origen.nombre,
                            "x": ev.estacion_origen.x,
                            "y": ev.estacion_origen.y,
                            "zona": ev.estacion_origen.zona.nombre if getattr(ev, "estacion_origen", None) and getattr(ev.estacion_origen, "zona", None) else None
                        } if getattr(ev, "estacion_origen", None) else None
                    } for ev in getattr(escenario, "historico", [])
                ],
                "metricas": getattr(escenario, "metricas", {})
            }

            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos_completos, archivo, indent=4, ensure_ascii=False)

            messagebox.showinfo("Éxito", f"Escenario guardado en:\n{ruta}", parent=parent_window)
            return True

        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar el archivo:\n{e}", parent=parent_window)
            return False

    # =========================================================================
    # 3. MÉTODOS AUXILIARES DE RECONSTRUCCIÓN DE OBJETOS
    # =========================================================================
    @classmethod
    def _obtener_o_crear_zona(cls, datos_z, zonas_lista: List[Zona]) -> Zona:
        nombre = datos_z if isinstance(datos_z, str) else datos_z.get("nombre", "Zona")
        for z in zonas_lista:
            if z.nombre == nombre:
                return z
        poblada = False if isinstance(datos_z, str) else datos_z.get("es_poblada", datos_z.get("poblada", False))
        nueva_z = Zona(
            nombre=nombre,
            x_min=0.0 if isinstance(datos_z, str) else datos_z.get("x_min", 0.0),
            x_max=1000.0 if isinstance(datos_z, str) else datos_z.get("x_max", 1000.0),
            y_min=0.0 if isinstance(datos_z, str) else datos_z.get("y_min", 0.0),
            y_max=1000.0 if isinstance(datos_z, str) else datos_z.get("y_max", 1000.0),
            poblada=poblada
        )
        zonas_lista.append(nueva_z)
        return nueva_z

    @classmethod
    def _obtener_o_crear_estacion(cls, datos_est, estaciones_lista: List[Estacion], zonas_lista: List[Zona]) -> Estacion:
        id_est = str(datos_est.get("id_estacion", "EST-01")).strip()
        for est in estaciones_lista:
            if est.id_estacion == id_est:
                return est
        zona_obj = cls._obtener_o_crear_zona(datos_est.get("zona", "Zona Generica"), zonas_lista)
        nueva_est = Estacion(
            id_estacion=id_est,
            nombre=datos_est.get("nombre", "Estacion"),
            x=datos_est.get("x", 0.0),
            y=datos_est.get("y", 0.0),
            zona=zona_obj
        )
        estaciones_lista.append(nueva_est)
        return nueva_est

    @classmethod
    def _crear_evento_objeto(cls, d: dict, zonas_lista: List[Zona], estaciones_lista: List[Estacion], epicentros_lista: List[Epicentro]) -> Evento:
        d_epi = d.get("epicentro", {})
        d_est = d.get("estacion_origen", {})

        z_epi = cls._obtener_o_crear_zona(d_epi.get("zona", "Zona"), zonas_lista)
        epicentro = Epicentro(x=d_epi.get("x", 0.0), y=d_epi.get("y", 0.0))
        epicentro.zona = z_epi
        epicentros_lista.append(epicentro)

        estacion = cls._obtener_o_crear_estacion(d_est, estaciones_lista, zonas_lista)

        id_evt = d.get("id_evento", d.get("id"))
        evt = Evento(
            id_evento=id_evt,
            magnitud=d.get("magnitud", 0.0),
            profundidad=d.get("profundidad", 0.0),
            epicentro=epicentro,
            estacion_origen=estacion,
            fecha_hora=d.get("fecha_hora")
        )
        if "estado_atencion" in d:
            evt.estado = d["estado_atencion"]
        if "prioridad" in d:
            evt.actualizar_prioridad_y_clave(d["prioridad"])

        return evt

    # =========================================================================
    # 4. MODALIDAD: CARGA POR INSERCIONES
    # =========================================================================
    @classmethod
    def cargar_por_inserciones(cls, escenario, parent_window=None, lista_eventos: Optional[list] = None) -> bool:
        """
        Punto de entrada invocado por la GUI. Si no se pasa 'lista_eventos',
        solicita seleccionar el archivo JSON interactivamente.
        """
        if lista_eventos is None:
            ruta = cls.seleccionar_archivo_cargar(parent_window, "Seleccionar JSON para Carga por Inserciones")
            if not ruta:
                return False
            try:
                with open(ruta, "r", encoding="utf-8") as archivo:
                    lista_eventos = json.load(archivo)
            except Exception as e:
                messagebox.showerror("Error de Lectura", f"No se pudo leer el archivo JSON:\n{e}", parent=parent_window)
                return False

        if not isinstance(lista_eventos, list):
            messagebox.showerror("Error de Formato", "El archivo debe contener una lista JSON de eventos.", parent=parent_window)
            return False

        return cls.procesar_carga_por_inserciones(lista_eventos, escenario, parent_window)

    @classmethod
    def procesar_carga_por_inserciones(cls, lista_eventos: list, escenario, parent_window=None) -> bool:
        ids_vistos = set()
        for d in lista_eventos:
            id_e = d.get("id_evento", d.get("id"))
            if id_e in ids_vistos:
                messagebox.showerror(
                    "Carga Rechazada",
                    f"Archivo inválido: Se detectó el identificador duplicado SIS-{id_e:06d}.\n"
                    "El escenario anterior se mantiene intacto.",
                    parent=parent_window
                )
                return False
            ids_vistos.add(id_e)

        # Construir AVL y BST desde cero
        nuevo_avl = AVL(modo_estres=False)
        nuevo_bst = ArbolBST()

        temp_zonas = list(escenario.zonas)
        temp_estaciones = list(escenario.estaciones)
        temp_epicentros = list(escenario.epicentros)
        temp_dict = {}

        for d in lista_eventos:
            evt = cls._crear_evento_objeto(d, temp_zonas, temp_estaciones, temp_epicentros)
            temp_dict[evt.id] = evt
            nodo_avl = Nodo(evento=evt)
            nuevo_avl.insertar(nodo_avl, escenario.L)
            nuevo_bst.insertar(evt)

        # Cálculo de métricas
        def _metricas(nodo):
            if nodo is None:
                return 0, 0, 0
            alt_izq, pmax_izq, h_izq = _metricas(getattr(nodo, "izquierda", None))
            alt_der, pmax_der, h_der = _metricas(getattr(nodo, "derecha", None))
            alt = 1 + max(alt_izq, alt_der)
            pmax = max(pmax_izq, pmax_der) + 1 if (alt_izq or alt_der) else 0
            hojas = 1 if (getattr(nodo, "izquierda", None) is None and getattr(nodo, "derecha", None) is None) else (h_izq + h_der)
            return alt, pmax, hojas

        alt_avl, pmax_avl, h_avl = _metricas(nuevo_avl.raiz)
        alt_bst, pmax_bst, h_bst = _metricas(nuevo_bst.raiz)

        # Confirmación y sustitución atómica
        escenario.zonas = temp_zonas
        escenario.estaciones = temp_estaciones
        escenario.epicentros = temp_epicentros
        escenario.dict_eventos = temp_dict
        escenario.arbol_avl = nuevo_avl
        escenario.arbol_bst = nuevo_bst

        raiz_avl_id = getattr(nuevo_avl.raiz.evento, "id", getattr(nuevo_avl.raiz.evento, "id_evento", None)) if nuevo_avl.raiz else "N/A"
        raiz_bst_id = getattr(nuevo_bst.raiz.evento, "id", getattr(nuevo_bst.raiz.evento, "id_evento", None)) if nuevo_bst.raiz else "N/A"

        res_msg = (
            "Carga por Inserción Exitosa:\n\n"
            f"🌳 Árbol AVL (Con Balanceo):\n"
            f"  - Raíz: SIS-{raiz_avl_id:06d}\n"
            f"  - Altura: {alt_avl}\n"
            f"  - Profundidad Máxima: {pmax_avl}\n"
            f"  - Cantidad de Hojas: {h_avl}\n\n"
            f"🌲 Árbol BST (Sin Balanceo):\n"
            f"  - Raíz: SIS-{raiz_bst_id:06d}\n"
            f"  - Altura: {alt_bst}\n"
            f"  - Profundidad Máxima: {pmax_bst}\n"
            f"  - Cantidad de Hojas: {h_bst}"
        )
        messagebox.showinfo("Resultados de Carga por Inserción", res_msg, parent=parent_window)
        return True

    # =========================================================================
    # 5. MODALIDAD: CARGA POR TOPOLOGÍA
    # =========================================================================
    @classmethod
    def cargar_por_topologia(cls, escenario, parent_window=None, datos: Optional[dict] = None) -> bool:
        """
        Punto de entrada invocado por la GUI. Si no se entregan los datos en dict,
        solicita seleccionar el archivo JSON interactivamente.
        """
        if datos is None:
            ruta = cls.seleccionar_archivo_cargar(parent_window, "Seleccionar JSON para Carga por Topología")
            if not ruta:
                return False
            try:
                with open(ruta, "r", encoding="utf-8") as archivo:
                    datos = json.load(archivo)
            except Exception as e:
                messagebox.showerror("Error de Lectura", f"No se pudo leer el archivo JSON:\n{e}", parent=parent_window)
                return False

        if not isinstance(datos, dict) or "topologia_arbol" not in datos:
            messagebox.showerror("Error de Formato", "El archivo no contiene la clave 'topologia_arbol' requerida.", parent=parent_window)
            return False

        return cls.procesar_carga_por_topologia(datos, escenario, parent_window)

    @classmethod
    def procesar_carga_por_topologia(cls, datos: dict, escenario, parent_window=None) -> bool:
        try:
            # 1. Copia temporal para reconstrucción aislada
            temp_zonas = [
                Zona(z["nombre"], z["x_min"], z["x_max"], z["y_min"], z["y_max"], z.get("es_poblada", z.get("poblada", False)))
                for z in datos.get("zonas", [])
            ]
            temp_estaciones = []
            for est in datos.get("estaciones", []):
                cls._obtener_o_crear_estacion(est, temp_estaciones, temp_zonas)

            temp_epicentros = [
                Epicentro(epi["x"], epi["y"], zonas_escenario=temp_zonas)
                for epi in datos.get("epicentros", [])
            ]

            temp_dict = {}
            ids_activos = set()
            ids_historicos = set()
            nodos_visitados = set()
            desbalance_detectado = False

            # Validar histórico primero
            for h in datos.get("historico", []):
                id_h = h.get("id_evento", h.get("id"))
                if id_h in ids_historicos:
                    raise ValueError(f"Identificador duplicado en Histórico: SIS-{id_h:06d}")
                ids_historicos.add(id_h)

            # Reconstrucción recursiva de la topología sin reinserciones
            def _deserializar_nodo(dict_nodo) -> Optional[Nodo]:
                nonlocal desbalance_detectado
                if dict_nodo is None:
                    return None

                evt_data = dict_nodo["evento"]
                id_evt = evt_data.get("id_evento", evt_data.get("id"))

                # Validación de unicidad entre activos e históricos
                if id_evt in ids_activos:
                    raise ValueError(f"Violación de Unicidad Activa: Evento SIS-{id_evt:06d} duplicado.")
                if id_evt in ids_historicos:
                    raise ValueError(f"Conflicto Activo-Histórico: Evento SIS-{id_evt:06d} existe en histórico.")
                if id(dict_nodo) in nodos_visitados:
                    raise ValueError("Ciclo detectado en la topología: Un nodo reaparece en múltiples posiciones.")

                ids_activos.add(id_evt)
                nodos_visitados.add(id(dict_nodo))

                evt = cls._crear_evento_objeto(evt_data, temp_zonas, temp_estaciones, temp_epicentros)
                temp_dict[evt.id] = evt

                # Validación de prioridad calculada vs almacenada
                p_esperada = evt.prioridad
                p_almacenada = dict_nodo.get("evento", {}).get("prioridad", p_esperada)
                if p_esperada != p_almacenada:
                    raise ValueError(f"Inconsistencia de Prioridad en SIS-{evt.id:06d}: Calculada={p_esperada}, Guardada={p_almacenada}")

                nodo = Nodo(evento=evt)

                # Recuperación explícita de enlaces
                nodo.izquierda = _deserializar_nodo(dict_nodo.get("izquierdo"))
                nodo.derecha = _deserializar_nodo(dict_nodo.get("derecho"))

                # Validación de Orden Global BST
                if nodo.izquierda and nodo.izquierda.clave >= nodo.clave:
                    raise ValueError(f"Violación de Orden BST: Hijo Izquierdo {nodo.izquierda.clave} >= Padre {nodo.clave}")
                if nodo.derecha and nodo.derecha.clave <= nodo.clave:
                    raise ValueError(f"Violación de Orden BST: Hijo Derecho {nodo.derecha.clave} <= Padre {nodo.clave}")

                # Validación de Alturas y Balances
                alt_izq = nodo.izquierda.altura if nodo.izquierda else 0
                alt_der = nodo.derecha.altura if nodo.derecha else 0
                alt_calculada = 1 + max(alt_izq, alt_der)
                factor_bal = alt_izq - alt_der

                nodo.altura = dict_nodo.get("altura", alt_calculada)
                if nodo.altura != alt_calculada:
                    raise ValueError(f"Altura inconsistente en SIS-{evt.id:06d}: Guardada={nodo.altura}, Real={alt_calculada}")

                if abs(factor_bal) > 1:
                    desbalance_detectado = True

                return nodo

            raiz_reconstruida = _deserializar_nodo(datos.get("topologia_arbol"))

            # Manejo del Modo Estrés según estado o JSON
            modo_estres_solicitado = datos.get("modo_ejecucion", {}).get("modo_estres", getattr(getattr(escenario, "arbol_avl", None), "modo_estres", False))

            if desbalance_detectado and not modo_estres_solicitado:
                raise ValueError("La topología leída está desbalanceada. Requiere Modo Estrés activado para poder cargarse.")

            # Reconstrucción del Histórico
            historico_reconstruido = [
                cls._crear_evento_objeto(h, temp_zonas, temp_estaciones, temp_epicentros)
                for h in datos.get("historico", [])
            ]

            # Reemplazar escenario atómicamente
            p = datos.get("parametros", {})
            escenario.W = p.get("W", escenario.W)
            escenario.R = p.get("R", escenario.R)
            escenario.L = p.get("L", escenario.L)
            escenario.T = p.get("T", escenario.T)
            if "reloj_simulacion" in p:
                escenario.reloj_simulacion = p["reloj_simulacion"]

            escenario.zonas = temp_zonas
            escenario.estaciones = temp_estaciones
            escenario.epicentros = temp_epicentros
            escenario.dict_eventos = temp_dict
            escenario.historico = historico_reconstruido

            escenario.arbol_avl = AVL(modo_estres=modo_estres_solicitado)
            escenario.arbol_avl.raiz = raiz_reconstruida
            escenario.arbol_avl.actualizar_profundidades(escenario.L)

            alerta_estres = " (Cargado bajo MODO ESTRÉS debido a desbalance)" if desbalance_detectado else ""
            messagebox.showinfo("Éxito", f"Topología del escenario cargada correctamente{alerta_estres}.", parent=parent_window)
            return True

        except Exception as e:
            messagebox.showerror(
                "Carga Rechazada",
                f"No se pudo reemplazar el escenario debido a errores en el archivo:\n\n{e}\n\n"
                "El escenario anterior se conserva sin modificaciones.",
                parent=parent_window
            )
            return False

    # =========================================================================
    # 6. ENTRADA PRINCIPAL PARA ARCHIVOS EXTERNOS
    # =========================================================================
    @classmethod
    def cargar_json(cls, escenario, parent_window=None) -> bool:
        ruta = cls.seleccionar_archivo_cargar(parent_window)
        if not ruta:
            return False

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                cargado = json.load(archivo)

            if isinstance(cargado, list):
                return cls.procesar_carga_por_inserciones(cargado, escenario, parent_window)
            elif isinstance(cargado, dict):
                return cls.procesar_carga_por_topologia(cargado, escenario, parent_window)
            else:
                messagebox.showerror("Error", "El formato del JSON no es una lista ni un objeto válido.", parent=parent_window)
                return False
        except Exception as e:
            messagebox.showerror("Error de Lectura", f"No se pudo abrir o procesar el archivo:\n{e}", parent=parent_window)
            return False