import tkinter as tk
from tkinter import ttk, messagebox

from Modelos.Asociaciones import recalcular_asociaciones_escenario


class VentanaAsociaciones(tk.Toplevel):

    def __init__(self, parent, escenario_actual, callback_actualizar=None):
        super().__init__(parent)
        self.title("Asociación Sísmica")
        self.geometry("1100x500") 
        self.minsize(950, 400)

        self.escenario_actual = escenario_actual
        self.callback_actualizar = callback_actualizar

        self.transient(parent)
        self.grab_set()

        self.crear_interfaz()

    # ==============================================================
    # INTERFAZ
    # ==============================================================
    def crear_interfaz(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)

        # ----------------------------------------------------------
        # CONFIGURACIÓN DE PARÁMETROS
        # ----------------------------------------------------------
        frame_aso = ttk.LabelFrame(main_frame, text=" Configuración de Parámetros ")
        frame_aso.pack(fill="x", padx=5, pady=5)

        ttk.Label(frame_aso, text="Ventana W (horas):").grid(row=0, column=0, padx=5, pady=5)
        self.entry_W = ttk.Entry(frame_aso, width=10)
        self.entry_W.insert(0, "48.0")
        self.entry_W.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_aso, text="Radio R (km):").grid(row=0, column=2, padx=5, pady=5)
        self.entry_R = ttk.Entry(frame_aso, width=10)
        self.entry_R.insert(0, "40.0")
        self.entry_R.grid(row=0, column=3, padx=5, pady=5)

        btn_recalcular = ttk.Button(
            frame_aso,
            text="Calcular Asociaciones",
            command=self.ejecutar_recalculo
        )
        btn_recalcular.grid(row=0, column=4, padx=15, pady=5)

        # ----------------------------------------------------------
        # TABLA DE EVENTOS
        # ----------------------------------------------------------
        tabla_frame = ttk.Frame(main_frame)
        tabla_frame.pack(fill="both", expand=True, pady=10)

        columnas = (
            "ID",
            "Fecha / Hora",
            "Magnitud",
            "Profundidad",
            "Estado",
            "Candidatos",
            "Ref. / Principal",
            "Réplicas (IDs)"
        )

        self.tabla_eventos = ttk.Treeview(tabla_frame, columns=columnas, show="headings")

        anchos = [60, 160, 80, 80, 90, 140, 120, 140]

        for col, ancho in zip(columnas, anchos):
            self.tabla_eventos.heading(col, text=col)
            self.tabla_eventos.column(col, width=ancho, anchor="center")

        scrollbar = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tabla_eventos.yview)
        self.tabla_eventos.configure(yscrollcommand=scrollbar.set)

        self.tabla_eventos.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.actualizar_tabla()

    # ==============================================================
    # OBTENER EVENTOS DEL ESCENARIO
    # ==============================================================
    def obtener_eventos(self):
        if not self.escenario_actual:
            return []

        escenario = self.escenario_actual

        dict_eventos = getattr(escenario, "dict_eventos", None)
        if isinstance(dict_eventos, dict):
            return list(dict_eventos.values())

        arbol_avl = getattr(escenario, "arbol_avl", None)
        if arbol_avl is not None:
            if hasattr(arbol_avl, "obtener_todos_los_eventos"):
                return arbol_avl.obtener_todos_los_eventos()
            if hasattr(arbol_avl, "inorden"):
                return arbol_avl.inorden()

        arbol_eventos = getattr(escenario, "arbol_eventos", None)
        if arbol_eventos is not None:
            if hasattr(arbol_eventos, "obtener_todos_los_eventos"):
                return arbol_eventos.obtener_todos_los_eventos()
            if hasattr(arbol_eventos, "inorden"):
                return arbol_eventos.inorden()

        eventos = getattr(escenario, "eventos", None)
        if eventos is not None:
            return list(eventos)

        return []

    # ==============================================================
    # EJECUTAR RECÁLCULO DE ASOCIACIONES
    # ==============================================================
    def ejecutar_recalculo(self):
        try:
            W = float(self.entry_W.get())
            R = float(self.entry_R.get())
            if W <= 0 or R <= 0:
                raise ValueError("W y R deben ser mayores a 0.")
        except ValueError as e:
            messagebox.showerror("Error de Parámetros", f"Ingrese valores válidos para W y R.\n\nDetalle: {e}", parent=self)
            return

        if self.escenario_actual is None:
            messagebox.showwarning("Atención", "No hay un escenario activo cargado.", parent=self)
            return

        eventos = self.obtener_eventos()
        if not eventos:
            messagebox.showwarning(
                "Sin Eventos",
                "No hay eventos cargados para calcular asociaciones.\n\nUtilice primero Cargar Inserciones o Cargar Topología.",
                parent=self
            )
            self.actualizar_tabla()
            return

        try:
            recalcular_asociaciones_escenario(self.escenario_actual, W, R)
            self.actualizar_tabla()
            if self.callback_actualizar:
                self.callback_actualizar()

            messagebox.showinfo(
                "Éxito",
                f"Asociaciones calculadas correctamente.\n\nEventos procesados: {len(eventos)}\nVentana W: {W} horas\nRadio R: {R} km",
                parent=self
            )
        except Exception as e:
            messagebox.showerror("Error de Asociaciones", f"No se pudieron calcular las asociaciones.\n\nDetalle: {e}", parent=self)

    # ==============================================================
    # ACTUALIZAR TABLA
    # ==============================================================
    def actualizar_tabla(self):
        for item in self.tabla_eventos.get_children():
            self.tabla_eventos.delete(item)

        eventos = self.obtener_eventos()
        if not eventos:
            return

        # Diccionario para encontrar quién apunta a quién (Réplicas)
        referencias_inversas = {}
        for ev in eventos:
            id_ref = getattr(ev, "id_referencia", None)
            if id_ref is not None:
                if id_ref not in referencias_inversas:
                    referencias_inversas[id_ref] = []
                referencias_inversas[id_ref].append(str(getattr(ev, "id", "")))

        for ev in eventos:
            id_evento = getattr(ev, "id", getattr(ev, "id_evento", ""))
            fecha = getattr(ev, "fecha_hora", getattr(ev, "fecha", ""))
            magnitud = getattr(ev, "magnitud", "")
            profundidad = getattr(ev, "profundidad", "")
            
            estado = getattr(ev, "estado", "")
            if hasattr(estado, "value"):
                estado = estado.value
            else:
                estado = str(estado)

            id_referencia = getattr(ev, "id_referencia", None)
            ref_str = str(id_referencia) if id_referencia is not None else "Ninguna"

            replicas = referencias_inversas.get(id_evento, [])
            replicas_str = ", ".join(replicas) if replicas else "Ninguna"

            # Obtención robusta de candidatos con respaldo de seguridad
            candidatos_lista = getattr(ev, "candidatos_ids", None)
            if not candidatos_lista:
                candidatos_lista = getattr(ev, "candidatos", [])

            if not candidatos_lista and id_referencia is not None:
                candidatos_lista = [id_referencia]

            candidatos_formateados = []
            for c in candidatos_lista:
                if hasattr(c, "id"):
                    candidatos_formateados.append(str(c.id))
                elif isinstance(c, dict) and "id" in c:
                    candidatos_formateados.append(str(c["id"]))
                else:
                    candidatos_formateados.append(str(c))

            candidatos_str = ", ".join(candidatos_formateados) if candidatos_formateados else "Ninguno"

            self.tabla_eventos.insert(
                "",
                "end",
                values=(id_evento, fecha, magnitud, profundidad, estado, candidatos_str, ref_str, replicas_str)
            )