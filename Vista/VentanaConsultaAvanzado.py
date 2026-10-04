import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

from Modelos import Metricas
from Modelos.Asociaciones import (
    candidatos_de,
    distancia,
    estado_en_catalogo,
    obtener_eventos_escenario,
    replicas_de,
    seleccionar_referencia,
)

FORMATO_FECHA_ISO = "%Y-%m-%dT%H:%M:%SZ"


class VentanaConsultaAvanzado:

    def __init__(
        self,
        parent_window: tk.Toplevel,
        arbol_avl: Optional[object] = None,
        escenario: Optional[object] = None,
        dict_eventos: Optional[dict] = None,
    ):
        self.ventana = tk.Toplevel(parent_window)
        self.ventana.title("Consultas Avanzadas y Análisis de Desempeño")
        self.ventana.geometry("800x580")

        self._arbol_inicial = arbol_avl
        self.escenario = escenario
        self.dict_eventos = dict_eventos or {}

        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self._crear_tab_top_k()
        self._crear_tab_rango_magnitud()
        self._crear_tab_fecha_profundidad()
        self._crear_tab_acceso_costoso()
        self._crear_tab_asociaciones()

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    @property
    def arbol(self):
        """Always the LIVE tree (undo / restore replace the object)."""
        if self.escenario is not None:
            return self.escenario.arbol_avl
        return self._arbol_inicial

    def _nueva_tab(self, titulo, columnas, encabezados, ancho=110):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=titulo)

        f_controles = ttk.Frame(frame)
        f_controles.pack(pady=10)

        lbl = ttk.Label(frame, text="Nodos examinados: -")
        lbl.pack(pady=5)

        tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=12)
        for col, enc in zip(columnas, encabezados):
            tabla.heading(col, text=enc)
            tabla.column(col, width=ancho, anchor="center")
        tabla.pack(fill="both", expand=True, padx=10, pady=5)
        return f_controles, lbl, tabla

    @staticmethod
    def _limpiar(tabla):
        tabla.delete(*tabla.get_children())

    def _arbol_o_error(self):
        arbol = self.arbol
        if not arbol:
            messagebox.showerror("Error", "No hay árbol AVL cargado.", parent=self.ventana)
        return arbol

    @staticmethod
    def _normalizar_fecha(texto: str, fin: bool) -> str:
        """Accepts YYYY-MM-DD or full ISO 8601 UTC; a date-only end covers the whole day."""
        t = texto.strip()
        if len(t) == 10:
            t += "T23:59:59Z" if fin else "T00:00:00Z"
        datetime.strptime(t, FORMATO_FECHA_ISO)  # validates
        return t

    # ------------------------------------------------------------------
    # TAB 1: TOP-K PENDING
    # ------------------------------------------------------------------
    def _crear_tab_top_k(self):
        ctr, lbl, tabla = self._nueva_tab(
            "Top-K Pendientes",
            ("id", "magnitud", "profundidad", "prioridad", "estado"),
            ("ID", "Magnitud", "Profundidad", "Prioridad", "Estado"),
        )
        ttk.Label(ctr, text="Cantidad (k):").pack(side=tk.LEFT, padx=5)
        entry_k = ttk.Entry(ctr, width=8)
        entry_k.pack(side=tk.LEFT, padx=5)

        def ejecutar():
            self._limpiar(tabla)
            try:
                k = int(entry_k.get().strip())
                if k <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "k debe ser un entero positivo.", parent=self.ventana)
                return
            arbol = self._arbol_o_error()
            if not arbol:
                return

            eventos, visitados = arbol.buscar_top_k_pendientes(k)
            lbl.config(text=f"Nodos examinados: {visitados} | Resultados: {len(eventos)} "
                            "(recorrido inverso: claves descendentes, se detiene al reunir k)")
            for ev in eventos:
                tabla.insert("", tk.END, values=(
                    f"SIS-{ev.id:06d}", ev.magnitud, ev.profundidad, ev.prioridad, ev.estado
                ))

        ttk.Button(ctr, text="Buscar", command=ejecutar).pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # TAB 2: MAGNITUDE RANGE
    # ------------------------------------------------------------------
    def _crear_tab_rango_magnitud(self):
        ctr, lbl, tabla = self._nueva_tab(
            "Rango Magnitud",
            ("id", "magnitud", "profundidad", "prioridad", "estado"),
            ("ID", "Magnitud", "Profundidad", "Prioridad", "Estado"),
        )
        ttk.Label(ctr, text="Mag. Mín:").pack(side=tk.LEFT, padx=2)
        entry_min = ttk.Entry(ctr, width=6)
        entry_min.pack(side=tk.LEFT, padx=5)
        ttk.Label(ctr, text="Mag. Máx:").pack(side=tk.LEFT, padx=2)
        entry_max = ttk.Entry(ctr, width=6)
        entry_max.pack(side=tk.LEFT, padx=5)

        def ejecutar():
            self._limpiar(tabla)
            try:
                m_min = float(entry_min.get().strip())
                m_max = float(entry_max.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Ingrese valores numéricos válidos.", parent=self.ventana)
                return
            if m_min > m_max:
                messagebox.showerror("Error", "La magnitud mínima no puede ser mayor a la máxima.", parent=self.ventana)
                return
            arbol = self._arbol_o_error()
            if not arbol:
                return

            eventos, visitados = arbol.buscar_por_rango_magnitud(m_min, m_max)
            lbl.config(text=f"Nodos examinados: {visitados} | Resultados: {len(eventos)} "
                            "(la magnitud solo está ordenada dentro de una misma prioridad: se recorre todo el árbol, O(n))")
            for ev in eventos:
                tabla.insert("", tk.END, values=(
                    f"SIS-{ev.id:06d}", ev.magnitud, ev.profundidad, ev.prioridad, ev.estado
                ))

        ttk.Button(ctr, text="Filtrar", command=ejecutar).pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # TAB 3: DATE RANGE + DEPTH
    # ------------------------------------------------------------------
    def _crear_tab_fecha_profundidad(self):
        ctr, lbl, tabla = self._nueva_tab(
            "Fecha y Profundidad",
            ("id", "fecha", "profundidad", "magnitud", "prioridad"),
            ("ID", "Fecha (UTC)", "Prof. hipocentro", "Magnitud", "Prioridad"),
            ancho=130,
        )
        ttk.Label(ctr, text="Inicio:").pack(side=tk.LEFT, padx=2)
        entry_ini = ttk.Entry(ctr, width=12)
        entry_ini.insert(0, "2020-01-01")
        entry_ini.pack(side=tk.LEFT, padx=2)

        ttk.Label(ctr, text="Fin:").pack(side=tk.LEFT, padx=2)
        entry_fin = ttk.Entry(ctr, width=12)
        reloj = getattr(self.escenario, "reloj", None)
        entry_fin.insert(0, reloj.strftime("%Y-%m-%d") if reloj else "2026-12-31")
        entry_fin.pack(side=tk.LEFT, padx=2)

        ttk.Label(ctr, text="Prof. Máx (km):").pack(side=tk.LEFT, padx=2)
        entry_prof = ttk.Entry(ctr, width=6)
        entry_prof.pack(side=tk.LEFT, padx=2)

        def ejecutar():
            self._limpiar(tabla)
            try:
                f_ini = self._normalizar_fecha(entry_ini.get(), fin=False)
                f_fin = self._normalizar_fecha(entry_fin.get(), fin=True)
            except ValueError:
                messagebox.showerror(
                    "Error", "Fechas inválidas. Use 2026-09-07 o 2026-09-07T10:00:00Z.", parent=self.ventana
                )
                return
            try:
                p_lim = float(entry_prof.get().strip())
                if p_lim < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "La profundidad debe ser un número no negativo.", parent=self.ventana)
                return
            if f_ini > f_fin:
                messagebox.showerror("Error", "La fecha de inicio debe ser menor o igual a la de fin.", parent=self.ventana)
                return
            arbol = self._arbol_o_error()
            if not arbol:
                return

            eventos, visitados = arbol.buscar_por_fecha_y_profundidad(f_ini, f_fin, p_lim)
            lbl.config(text=f"Nodos examinados: {visitados} | Resultados: {len(eventos)} "
                            "(la fecha y la profundidad no forman parte de K: se recorre todo el árbol, O(n))")
            for ev in eventos:
                tabla.insert("", tk.END, values=(
                    f"SIS-{ev.id:06d}", ev.fecha_hora, ev.profundidad, ev.magnitud, ev.prioridad
                ))

        ttk.Button(ctr, text="Filtrar", command=ejecutar).pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # TAB 4: EXPENSIVE ACCESS (priority 3 and node depth > L)
    # ------------------------------------------------------------------
    def _crear_tab_acceso_costoso(self):
        ctr, lbl, tabla = self._nueva_tab(
            "Eventos Costosos (d > L)",
            ("id", "prioridad", "profundidad_nodo", "limite_L", "costo_busqueda"),
            ("ID Evento", "Prioridad", "Prof. Nodo (d)", "Límite (L)", "Nodos visitados (d+1)"),
            ancho=130,
        )
        limite_defecto = getattr(self.escenario, "L", 3) if self.escenario else 3

        ttk.Label(ctr, text="Límite L:").pack(side=tk.LEFT, padx=5)
        entry_L = ttk.Entry(ctr, width=6)
        entry_L.insert(0, str(limite_defecto))
        entry_L.pack(side=tk.LEFT, padx=5)

        def ejecutar():
            self._limpiar(tabla)
            try:
                L = int(entry_L.get().strip())
                if L < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "L debe ser un entero no negativo.", parent=self.ventana)
                return
            arbol = self._arbol_o_error()
            if not arbol:
                return

            # Computed with the L typed here (not with the flag stored in the event)
            resultados, visitados = Metricas.eventos_costosos(arbol.raiz, L)
            lbl.config(text=f"Nodos examinados: {visitados} | Costosos hallados: {len(resultados)} "
                            "(se omite el subárbol izquierdo de todo nodo con P < 3: solo contiene claves menores)")
            for item in resultados:
                ev = item["evento"]
                tabla.insert("", tk.END, values=(
                    f"SIS-{ev.id:06d}", ev.prioridad, item["profundidad_nodo"],
                    item["limite_L"], item["nodos_visitados_busqueda"],
                ))

        ttk.Button(ctr, text="Analizar", command=ejecutar).pack(side=tk.LEFT, padx=5)

    # ------------------------------------------------------------------
    # TAB 5: ASSOCIATIONS (active + archived)
    # ------------------------------------------------------------------
    def _crear_tab_asociaciones(self):
        ctr, lbl, tabla = self._nueva_tab(
            "Asociaciones",
            ("rol", "id", "catalogo", "magnitud", "fecha", "distancia"),
            ("Rol", "ID", "Catálogo", "Magnitud", "Fecha (UTC)", "Distancia (km)"),
            ancho=120,
        )
        tabla.column("rol", width=230)

        ttk.Label(ctr, text="ID Evento:").pack(side=tk.LEFT, padx=5)
        entry_id = ttk.Entry(ctr, width=10)
        entry_id.pack(side=tk.LEFT, padx=5)

        def ejecutar():
            self._limpiar(tabla)
            if self.escenario is None:
                messagebox.showerror("Error", "No hay un escenario activo.", parent=self.ventana)
                return
            try:
                id_evento = int(entry_id.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Ingrese un ID numérico.", parent=self.ventana)
                return

            estado, evento = estado_en_catalogo(self.escenario, id_evento)
            if evento is None:
                messagebox.showwarning("Aviso", f"El ID {id_evento} no existe.", parent=self.ventana)
                return
            if estado == "Retirado":
                lbl.config(text=f"SIS-{id_evento:06d} fue eliminado: los eliminados no participan en asociaciones.")
                return

            candidatos = candidatos_de(self.escenario, evento)
            id_ref = seleccionar_referencia(evento, candidatos)
            replicas = replicas_de(self.escenario, id_evento)
            examinados = len(obtener_eventos_escenario(self.escenario))

            def fila(rol, ev):
                tabla.insert("", tk.END, values=(
                    rol, f"SIS-{ev.id:06d}", ev.estado_catalogo, ev.magnitud,
                    ev.fecha_hora, f"{distancia(ev, evento):.1f}",
                ))

            for cand in candidatos:
                fila("Candidato ★ (referencia elegida)" if cand.id == id_ref else "Candidato", cand)
            for rep in replicas:
                fila("Réplica (lo usa como referencia)", rep)

            lbl.config(text=(
                f"SIS-{id_evento:06d} [{estado}] | Eventos examinados (activos + archivados): {examinados} | "
                f"Candidatos: {len(candidatos)} | Réplicas: {len(replicas)} | "
                f"W={self.escenario.W} h, R={self.escenario.R} km"
                + ("" if candidatos else " | Sin candidatos: queda sin asociación")
            ))

        ttk.Button(ctr, text="Consultar", command=ejecutar).pack(side=tk.LEFT, padx=5)