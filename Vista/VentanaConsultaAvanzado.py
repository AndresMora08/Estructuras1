import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional


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
        self.ventana.geometry("750x550")

        self.arbol_avl = arbol_avl
        self.escenario = escenario
        self.dict_eventos = dict_eventos or {}

        # Contenedor de pestañas
        self.notebook = ttk.Notebook(self.ventana)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Construir cada pestaña
        self._crear_tab_top_k()
        self._crear_tab_rango_magnitud()
        self._crear_tab_fecha_profundidad()
        self._crear_tab_acceso_costoso()

    # --- Pestaña 1: Top K Pendientes ---
    def _crear_tab_top_k(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Top-K Pendientes")

        f_controles = ttk.Frame(frame)
        f_controles.pack(pady=10)

        ttk.Label(f_controles, text="Cantidad (k):").pack(side=tk.LEFT, padx=5)
        entry_k = ttk.Entry(f_controles, width=8)
        entry_k.pack(side=tk.LEFT, padx=5)

        lbl_metricas = ttk.Label(frame, text="Nodos visitados: -")

        # Tabla de resultados
        columnas = ("id", "magnitud", "profundidad", "prioridad", "estado")
        tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=12)
        for col in columnas:
            tabla.heading(col, text=col.capitalize())
            tabla.column(col, width=110, anchor="center")

        def ejecutar():
            tabla.delete(*tabla.get_children())
            try:
                k = int(entry_k.get().strip())
                if not self.arbol_avl:
                    messagebox.showerror("Error", "No hay árbol AVL cargado.", parent=self.ventana)
                    return
                
                eventos, visitados = self.arbol_avl.buscar_top_k_pendientes(k)
                lbl_metricas.config(text=f"Nodos visitados: {visitados} | Resultados: {len(eventos)}")

                for ev in eventos:
                    tabla.insert("", tk.END, values=(
                        f"SIS-{ev.id:06d}", ev.magnitud, ev.profundidad, ev.prioridad, ev.estado
                    ))
            except ValueError:
                messagebox.showerror("Error", "Ingrese un valor numérico entero para k.", parent=self.ventana)

        ttk.Button(f_controles, text="Buscar", command=ejecutar).pack(side=tk.LEFT, padx=5)
        lbl_metricas.pack(pady=5)
        tabla.pack(fill="both", expand=True, padx=10, pady=5)

    # --- Pestaña 2: Rango de Magnitud ---
    def _crear_tab_rango_magnitud(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Rango Magnitud")

        f_controles = ttk.Frame(frame)
        f_controles.pack(pady=10)

        ttk.Label(f_controles, text="Mag. Mín:").pack(side=tk.LEFT, padx=2)
        entry_min = ttk.Entry(f_controles, width=6)
        entry_min.pack(side=tk.LEFT, padx=5)

        ttk.Label(f_controles, text="Mag. Máx:").pack(side=tk.LEFT, padx=2)
        entry_max = ttk.Entry(f_controles, width=6)
        entry_max.pack(side=tk.LEFT, padx=5)

        lbl_metricas = ttk.Label(frame, text="Nodos visitados: -")

        columnas = ("id", "magnitud", "profundidad", "prioridad", "estado")
        tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=12)
        for col in columnas:
            tabla.heading(col, text=col.capitalize())
            tabla.column(col, width=110, anchor="center")

        def ejecutar():
            tabla.delete(*tabla.get_children())
            try:
                m_min = float(entry_min.get().strip())
                m_max = float(entry_max.get().strip())

                if m_min > m_max:
                    messagebox.showerror("Error", "La magnitud mínima no puede ser mayor a la máxima.", parent=self.ventana)
                    return

                if not self.arbol_avl:
                    messagebox.showerror("Error", "No hay árbol AVL cargado.", parent=self.ventana)
                    return

                eventos, visitados = self.arbol_avl.buscar_por_rango_magnitud(m_min, m_max)
                lbl_metricas.config(text=f"Nodos visitados: {visitados} | Resultados: {len(eventos)}")

                for ev in eventos:
                    tabla.insert("", tk.END, values=(
                        f"SIS-{ev.id:06d}", ev.magnitud, ev.profundidad, ev.prioridad, ev.estado
                    ))
            except ValueError:
                messagebox.showerror("Error", "Ingrese valores numéricos válidos.", parent=self.ventana)

        ttk.Button(f_controles, text="Filtrar", command=ejecutar).pack(side=tk.LEFT, padx=5)
        lbl_metricas.pack(pady=5)
        tabla.pack(fill="both", expand=True, padx=10, pady=5)

    # --- Pestaña 3: Fecha y Profundidad ---
    def _crear_tab_fecha_profundidad(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Fecha y Profundidad")

        f_controles = ttk.Frame(frame)
        f_controles.pack(pady=10)

        ttk.Label(f_controles, text="Inicio:").pack(side=tk.LEFT, padx=2)
        entry_f_inicio = ttk.Entry(f_controles, width=12)
        entry_f_inicio.insert(0, "2024-01-01")
        entry_f_inicio.pack(side=tk.LEFT, padx=2)

        ttk.Label(f_controles, text="Fin:").pack(side=tk.LEFT, padx=2)
        entry_f_fin = ttk.Entry(f_controles, width=12)
        entry_f_fin.insert(0, "2026-12-31")
        entry_f_fin.pack(side=tk.LEFT, padx=2)

        ttk.Label(f_controles, text="Prof. Máx:").pack(side=tk.LEFT, padx=2)
        entry_prof = ttk.Entry(f_controles, width=6)
        entry_prof.pack(side=tk.LEFT, padx=2)

        lbl_metricas = ttk.Label(frame, text="Nodos visitados: -")

        columnas = ("id", "fecha", "profundidad", "magnitud", "prioridad")
        tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=12)
        for col in columnas:
            tabla.heading(col, text=col.capitalize())
            tabla.column(col, width=120, anchor="center")

        def ejecutar():
            tabla.delete(*tabla.get_children())
            try:
                f_ini = entry_f_inicio.get().strip()
                f_fin = entry_f_fin.get().strip()
                p_lim = float(entry_prof.get().strip())

                if f_ini > f_fin:
                    messagebox.showerror("Error", "La fecha de inicio debe ser menor o igual a la de fin.", parent=self.ventana)
                    return

                if not self.arbol_avl:
                    messagebox.showerror("Error", "No hay árbol AVL cargado.", parent=self.ventana)
                    return

                eventos, visitados = self.arbol_avl.buscar_por_fecha_y_profundidad(f_ini, f_fin, p_lim)
                lbl_metricas.config(text=f"Nodos visitados: {visitados} | Resultados: {len(eventos)}")

                for ev in eventos:
                    tabla.insert("", tk.END, values=(
                        f"SIS-{ev.id:06d}", getattr(ev, "fecha_hora", "-"), ev.profundidad, ev.magnitud, ev.prioridad
                    ))
            except ValueError:
                messagebox.showerror("Error", "Ingrese una profundidad numérica válida.", parent=self.ventana)

        ttk.Button(f_controles, text="Filtrar", command=ejecutar).pack(side=tk.LEFT, padx=5)
        lbl_metricas.pack(pady=5)
        tabla.pack(fill="both", expand=True, padx=10, pady=5)

    # --- Pestaña 4: Accesos Costosos ---
    def _crear_tab_acceso_costoso(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Eventos Costosos (d > L)")

        f_controles = ttk.Frame(frame)
        f_controles.pack(pady=10)

        # Obtener L por defecto del escenario si está disponible
        limite_defecto = getattr(self.escenario, "limite_L", 3) if self.escenario else 3

        ttk.Label(f_controles, text="Límite L:").pack(side=tk.LEFT, padx=5)
        entry_L = ttk.Entry(f_controles, width=6)
        entry_L.insert(0, str(limite_defecto))
        entry_L.pack(side=tk.LEFT, padx=5)

        lbl_metricas = ttk.Label(frame, text="Nodos visitados: -")

        columnas = ("id", "prioridad", "profundidad_nodo", "limite_L", "costo_busqueda")
        tabla = ttk.Treeview(frame, columns=columnas, show="headings", height=12)
        tabla.heading("id", text="ID Evento")
        tabla.heading("prioridad", text="Prioridad")
        tabla.heading("profundidad_nodo", text="Prof. Nodo (d)")
        tabla.heading("limite_L", text="Límite (L)")
        tabla.heading("costo_busqueda", text="Costo Búsqueda (d+1)")

        for col in columnas:
            tabla.column(col, width=120, anchor="center")

        def ejecutar():
            tabla.delete(*tabla.get_children())
            try:
                L = int(entry_L.get().strip())

                if not self.arbol_avl:
                    messagebox.showerror("Error", "No hay árbol AVL cargado.", parent=self.ventana)
                    return

                res_costosos, visitados = self.arbol_avl.buscar_eventos_prioritarios_costosos(L)
                lbl_metricas.config(text=f"Nodos visitados recorrido: {visitados} | Costosos hallados: {len(res_costosos)}")

                for item in res_costosos:
                    ev = item["evento"]
                    tabla.insert("", tk.END, values=(
                        f"SIS-{ev.id:06d}",
                        ev.prioridad,
                        item["profundidad_nodo"],
                        item["limite_L"],
                        item["nodos_visitados_busqueda"]
                    ))
            except ValueError:
                messagebox.showerror("Error", "Ingrese un límite L entero.", parent=self.ventana)

        ttk.Button(f_controles, text="Analizar", command=ejecutar).pack(side=tk.LEFT, padx=5)
        lbl_metricas.pack(pady=5)
        tabla.pack(fill="both", expand=True, padx=10, pady=5)