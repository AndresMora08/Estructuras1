
import tkinter as tk
from tkinter import ttk, messagebox

from Modelos.Asociaciones import recalcular_asociaciones_escenario


class VentanaAsociaciones(tk.Toplevel):

    def __init__(self, parent, escenario_actual, callback_actualizar=None):

        super().__init__(parent)

        self.title("Asociación Sísmica")
        self.geometry("900x500")
        self.minsize(750, 400)

        self.escenario_actual = escenario_actual
        self.callback_actualizar = callback_actualizar

        self.transient(parent)
        self.grab_set()

        self.crear_interfaz()

    # ==============================================================
    # INTERFAZ
    # ==============================================================

    def crear_interfaz(self):

        main_frame = ttk.Frame(
            self,
            padding=10
        )

        main_frame.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------------
        # CONFIGURACIÓN DE PARÁMETROS
        # ----------------------------------------------------------

        frame_aso = ttk.LabelFrame(
            main_frame,
            text=" Configuración de Parámetros "
        )

        frame_aso.pack(
            fill="x",
            padx=5,
            pady=5
        )

        ttk.Label(
            frame_aso,
            text="Ventana W (horas):"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )

        self.entry_W = ttk.Entry(
            frame_aso,
            width=10
        )

        self.entry_W.insert(
            0,
            "48.0"
        )

        self.entry_W.grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Label(
            frame_aso,
            text="Radio R (km):"
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5
        )

        self.entry_R = ttk.Entry(
            frame_aso,
            width=10
        )

        self.entry_R.insert(
            0,
            "40.0"
        )

        self.entry_R.grid(
            row=0,
            column=3,
            padx=5,
            pady=5
        )

        btn_recalcular = ttk.Button(
            frame_aso,
            text="Calcular Asociaciones",
            command=self.ejecutar_recalculo
        )

        btn_recalcular.grid(
            row=0,
            column=4,
            padx=15,
            pady=5
        )

        # ----------------------------------------------------------
        # TABLA DE EVENTOS
        # ----------------------------------------------------------

        tabla_frame = ttk.Frame(
            main_frame
        )

        tabla_frame.pack(
            fill="both",
            expand=True,
            pady=10
        )

        columnas = (
            "ID",
            "Fecha / Hora",
            "Magnitud",
            "Profundidad",
            "Estado",
            "Ref. / Principal"
        )

        self.tabla_eventos = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings"
        )

        anchos = [
            60,
            180,
            90,
            90,
            100,
            140
        ]

        for col, ancho in zip(columnas, anchos):

            self.tabla_eventos.heading(
                col,
                text=col
            )

            self.tabla_eventos.column(
                col,
                width=ancho,
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            tabla_frame,
            orient="vertical",
            command=self.tabla_eventos.yview
        )

        self.tabla_eventos.configure(
            yscrollcommand=scrollbar.set
        )

        self.tabla_eventos.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        # Cargar eventos al abrir la ventana

        self.actualizar_tabla()

    # ==============================================================
    # OBTENER EVENTOS DEL ESCENARIO
    #
    # Compatible con el ControladorJSON actual:
    # - escenario.dict_eventos
    # - escenario.arbol_avl
    # ==============================================================

    def obtener_eventos(self):

        if not self.escenario_actual:
            return []

        escenario = self.escenario_actual

        # ----------------------------------------------------------
        # PRIMERA OPCIÓN: DICCIONARIO DE EVENTOS
        # ----------------------------------------------------------

        dict_eventos = getattr(
            escenario,
            "dict_eventos",
            None
        )

        if isinstance(dict_eventos, dict):

            return list(
                dict_eventos.values()
            )

        # ----------------------------------------------------------
        # SEGUNDA OPCIÓN: ÁRBOL AVL
        # ----------------------------------------------------------

        arbol_avl = getattr(
            escenario,
            "arbol_avl",
            None
        )

        if arbol_avl is not None:

            if hasattr(
                arbol_avl,
                "obtener_todos_los_eventos"
            ):

                return arbol_avl.obtener_todos_los_eventos()

            if hasattr(
                arbol_avl,
                "inorden"
            ):

                return arbol_avl.inorden()

        # ----------------------------------------------------------
        # TERCERA OPCIÓN: ÁRBOL DE EVENTOS ANTIGUO
        # ----------------------------------------------------------

        arbol_eventos = getattr(
            escenario,
            "arbol_eventos",
            None
        )

        if arbol_eventos is not None:

            if hasattr(
                arbol_eventos,
                "obtener_todos_los_eventos"
            ):

                return arbol_eventos.obtener_todos_los_eventos()

            if hasattr(
                arbol_eventos,
                "inorden"
            ):

                return arbol_eventos.inorden()

        # ----------------------------------------------------------
        # CUARTA OPCIÓN: LISTA DE EVENTOS
        # ----------------------------------------------------------

        eventos = getattr(
            escenario,
            "eventos",
            None
        )

        if eventos is not None:

            return list(eventos)

        return []

    # ==============================================================
    # EJECUTAR RECÁLCULO DE ASOCIACIONES
    # ==============================================================

    def ejecutar_recalculo(self):

        # ----------------------------------------------------------
        # VALIDAR W Y R
        # ----------------------------------------------------------

        try:

            W = float(
                self.entry_W.get()
            )

            R = float(
                self.entry_R.get()
            )

            if W <= 0 or R <= 0:

                raise ValueError(
                    "W y R deben ser mayores a 0."
                )

        except ValueError as e:

            messagebox.showerror(
                "Error de Parámetros",
                f"Ingrese valores válidos para W y R.\n\nDetalle: {e}",
                parent=self
            )

            return

        # ----------------------------------------------------------
        # VALIDAR ESCENARIO
        # ----------------------------------------------------------

        if self.escenario_actual is None:

            messagebox.showwarning(
                "Atención",
                "No hay un escenario activo cargado.",
                parent=self
            )

            return

        # ----------------------------------------------------------
        # VALIDAR EVENTOS
        # ----------------------------------------------------------

        eventos = self.obtener_eventos()

        if not eventos:

            messagebox.showwarning(
                "Sin Eventos",
                "No hay eventos cargados para calcular asociaciones.\n\n"
                "Utilice primero Cargar Inserciones o Cargar Topología.",
                parent=self
            )

            self.actualizar_tabla()

            return

        # ----------------------------------------------------------
        # CALCULAR ASOCIACIONES
        # ----------------------------------------------------------

        try:

            recalcular_asociaciones_escenario(
                self.escenario_actual,
                W,
                R
            )

            # Actualizar tabla de la ventana

            self.actualizar_tabla()

            # Actualizar tabla principal

            if self.callback_actualizar:

                self.callback_actualizar()

            messagebox.showinfo(
                "Éxito",
                f"Asociaciones calculadas correctamente.\n\n"
                f"Eventos procesados: {len(eventos)}\n"
                f"Ventana W: {W} horas\n"
                f"Radio R: {R} km",
                parent=self
            )

        except Exception as e:

            messagebox.showerror(
                "Error de Asociaciones",
                "No se pudieron calcular las asociaciones.\n\n"
                f"Detalle: {e}",
                parent=self
            )

    # ==============================================================
    # ACTUALIZAR TABLA
    # ==============================================================

    def actualizar_tabla(self):

        # ----------------------------------------------------------
        # LIMPIAR TABLA
        # ----------------------------------------------------------

        for item in self.tabla_eventos.get_children():

            self.tabla_eventos.delete(
                item
            )

        # ----------------------------------------------------------
        # OBTENER EVENTOS
        # ----------------------------------------------------------

        eventos = self.obtener_eventos()

        if not eventos:
            return

        # ----------------------------------------------------------
        # INSERTAR EVENTOS
        # ----------------------------------------------------------

        for ev in eventos:

            # ID

            id_evento = getattr(
                ev,
                "id",
                getattr(
                    ev,
                    "id_evento",
                    ""
                )
            )

            # FECHA

            fecha = getattr(
                ev,
                "fecha_hora",
                getattr(
                    ev,
                    "fecha",
                    ""
                )
            )

            # MAGNITUD

            magnitud = getattr(
                ev,
                "magnitud",
                ""
            )

            # PROFUNDIDAD

            profundidad = getattr(
                ev,
                "profundidad",
                ""
            )

            # ESTADO

            estado = getattr(
                ev,
                "estado",
                ""
            )

            if hasattr(
                estado,
                "value"
            ):

                estado = estado.value

            else:

                estado = str(
                    estado
                )

            # REFERENCIA

            id_referencia = getattr(
                ev,
                "id_referencia",
                None
            )

            if id_referencia is not None:

                ref_str = str(
                    id_referencia
                )

            else:

                ref_str = "Ninguna (Principal)"

            # INSERTAR EN TABLA

            self.tabla_eventos.insert(
                "",
                "end",
                values=(
                    id_evento,
                    fecha,
                    magnitud,
                    profundidad,
                    estado,
                    ref_str
                )
            )