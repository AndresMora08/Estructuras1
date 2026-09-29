
import tkinter as tk
from tkinter import messagebox, ttk

# ==============================================================
# CONTROLADOR JSON
# ==============================================================

from Logica.controlador_json import ControladorJSON


# ==============================================================
# MODELOS
# ==============================================================

from Modelos.Epicentro import Epicentro
from Modelos.Escenario import Escenario
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.Zona import Zona
from Modelos.Asociaciones import recalcular_asociaciones_escenario


# ==============================================================
# VISTAS
# ==============================================================

from Vista.ConsultaEventos import ConsultaEventos
from Vista.VentanaEliminacionManual import VentanaEliminacionManual
from Vista.VisualizadorAVL import VisualizadorAVL
from Vista.VentanaAsociaciones import VentanaAsociaciones


class SismoLabGUI:

    def __init__(self, root: tk.Tk, escenario: Escenario):

        self.root = root
        self.escenario = escenario

        # Compatibilidad con VentanaAsociaciones
        self.escenario_actual = escenario

        self.root.title("SismoLab AVL - Monitor")
        self.root.geometry("1200x700")

        # ==========================================================
        # TÍTULO
        # ==========================================================

        ttk.Label(
            self.root,
            text="SismoLab AVL",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # ==========================================================
        # MENÚ PRINCIPAL
        # ==========================================================

        f_botones = ttk.Frame(self.root)
        f_botones.pack(pady=5)

        botones = [
            ("Crear Zona", self._abrir_formulario_zona),
            ("Crear Estación", self._abrir_formulario_estacion),
            ("Crear Epicentro", self._abrir_formulario_epicentro),
            ("Crear Evento", self._abrir_formulario_evento),
            ("Ver Árbol AVL", self._abrir_visualizador_arbol),
            ("Consultar Eventos", self._abrir_busqueda),
            ("Cargar Inserciones", self._cargar_por_inserciones),
            ("Cargar Topología", self._cargar_por_topologia),
            ("Gestión y JSON", self.abrir_ventana_gestion),
            ("Asociaciones", self.abrir_ventana_asociaciones),
        ]

        for texto, comando in botones:

            ttk.Button(
                f_botones,
                text=texto,
                command=comando
            ).pack(
                side=tk.LEFT,
                padx=2
            )

        # ==========================================================
        # VENTANA PRINCIPAL
        #
        # IMPORTANTE:
        # No se crea ninguna tabla de eventos aquí.
        # La ventana principal muestra únicamente el título y
        # los botones del menú.
        #
        # La tabla y los parámetros de asociaciones se gestionan
        # desde sus ventanas independientes.
        # ==========================================================

    # ==================================================================
    # FORMULARIO GENERAL
    # ==================================================================

    def _crear_formulario(
        self,
        titulo: str,
        dimension: str
    ):

        win = tk.Toplevel(
            self.root
        )

        win.title(
            titulo
        )

        win.geometry(
            dimension
        )

        win.resizable(
            False,
            False
        )

        win.grab_set()

        frame = ttk.Frame(
            win,
            padding=15
        )

        frame.pack(
            fill="both",
            expand=True
        )

        return win, frame

    # ==================================================================
    # ASOCIACIONES
    #
    # La ventana se abre únicamente al presionar el botón.
    # ==================================================================

    def abrir_ventana_asociaciones(self):

        if not self.escenario:

            messagebox.showwarning(
                "Atención",
                "No hay un escenario activo.",
                parent=self.root
            )

            return

        VentanaAsociaciones(
            self.root,
            self.escenario,
            callback_actualizar=self.actualizar_tabla_eventos
        )

    # ==================================================================
    # CARGA POR INSERCIONES
    # ==================================================================

    def _cargar_por_inserciones(self):

        exito = ControladorJSON.cargar_por_inserciones(
            self.escenario,
            parent_window=self.root
        )

        if exito:

            self.actualizar_interfaz()

            self.actualizar_tabla_eventos()

    # ==================================================================
    # CARGA POR TOPOLOGÍA
    # ==================================================================

    def _cargar_por_topologia(self):

        exito = ControladorJSON.cargar_por_topologia(
            self.escenario,
            parent_window=self.root
        )

        if exito:

            self.actualizar_interfaz()

            self.actualizar_tabla_eventos()

    # ==================================================================
    # CONSULTA DE EVENTOS
    # ==================================================================

    def _abrir_busqueda(self):

        dict_eventos = getattr(
            self.escenario,
            "dict_eventos",
            {}
        )

        if not dict_eventos:

            messagebox.showinfo(
                "Sin Eventos",
                "No hay registro de eventos en el sistema.",
                parent=self.root
            )

            return

        ConsultaEventos(
            self.root,
            dict_eventos,
            getattr(
                self.escenario,
                "arbol_avl",
                None
            ),
            self.escenario
        )

    # ==================================================================
    # VISUALIZADOR AVL
    # ==================================================================

    def _abrir_visualizador_arbol(self):

        arbol = getattr(
            self.escenario,
            "arbol_avl",
            None
        )

        if not arbol or not arbol.raiz:

            messagebox.showinfo(
                "Árbol Vacío",
                "El árbol AVL no contiene eventos registrados aún.",
                parent=self.root
            )

            return

        VisualizadorAVL(
            self.root,
            arbol
        )

    # ==================================================================
    # GESTIÓN Y JSON
    # ==================================================================

    def abrir_ventana_gestion(self):

        dict_eventos = getattr(
            self.escenario,
            "dict_eventos",
            {}
        )

        if not dict_eventos:

            messagebox.showwarning(
                "Advertencia",
                "No hay ningún evento disponible para gestionar o eliminar.",
                parent=self.root
            )

            return

        evento_actual = getattr(
            self,
            "evento_seleccionado",
            None
        )

        if not evento_actual:

            evento_actual = next(
                iter(dict_eventos.values()),
                None
            )

        if not evento_actual:

            messagebox.showwarning(
                "Advertencia",
                "No hay ningún evento disponible.",
                parent=self.root
            )

            return

        VentanaEliminacionManual(
            parent_window=self.root,
            evento=evento_actual,
            arbol_avl=getattr(
                self.escenario,
                "arbol_avl",
                None
            ),
            dict_eventos=dict_eventos,
            escenario=self.escenario,
            callback_al_eliminar=self.actualizar_interfaz
        )

    # ==================================================================
    # ACTUALIZAR INTERFAZ
    # ==================================================================

    def actualizar_interfaz(self):

        self.root.update_idletasks()

        self.actualizar_tabla_eventos()

    # ==================================================================
    # RECÁLCULO DE ASOCIACIONES
    #
    # Se conserva para compatibilidad con código existente.
    # ==================================================================

    def ejecutar_recalculo_asociaciones(self):

        try:

            W = float(
                self.entry_W.get()
            )

            R = float(
                self.entry_R.get()
            )

            if W <= 0 or R <= 0:

                raise ValueError(
                    "W y R deben ser estrictamente positivos."
                )

        except (ValueError, AttributeError) as e:

            messagebox.showerror(
                "Error de Parámetros",
                "Ingrese valores numéricos válidos para W y R (> 0).\n"
                f"Detalle: {e}",
                parent=self.root
            )

            return

        if not self.escenario:

            messagebox.showwarning(
                "Atención",
                "No hay un escenario activo.",
                parent=self.root
            )

            return

        try:

            recalcular_asociaciones_escenario(
                self.escenario,
                W,
                R
            )

            self.actualizar_tabla_eventos()

            messagebox.showinfo(
                "Asociaciones",
                "Asociaciones recalculadas con éxito.",
                parent=self.root
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                f"No se pudieron recalcular las asociaciones:\n{e}",
                parent=self.root
            )

    # ==================================================================
    # PANEL DE PARÁMETROS DE ASOCIACIÓN
    #
    # Se conserva por compatibilidad.
    # No se llama desde __init__.
    # ==================================================================

    def crear_paneles_parametros_asociacion(
        self,
        parent_frame
    ):

        frame_aso = ttk.LabelFrame(
            parent_frame,
            text=" Parámetros de Asociación "
        )

        frame_aso.pack(
            fill="x",
            padx=10,
            pady=5
        )

        # --------------------------------------------------------------
        # W
        # --------------------------------------------------------------

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
            width=8
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

        # --------------------------------------------------------------
        # R
        # --------------------------------------------------------------

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
            width=8
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

        # --------------------------------------------------------------
        # BOTÓN RECALCULAR
        # --------------------------------------------------------------

        ttk.Button(
            frame_aso,
            text="Recalcular Asociaciones",
            command=self.ejecutar_recalculo_asociaciones
        ).grid(
            row=0,
            column=4,
            padx=10,
            pady=5
        )

    # ==================================================================
    # TABLA DE EVENTOS
    #
    # Este método se conserva, pero ya no se ejecuta al iniciar
    # la ventana principal.
    # ==================================================================

    def configurar_tabla_eventos(
        self,
        parent_frame
    ):

        columnas = (
            "ID",
            "Fecha / Hora",
            "Magnitud",
            "Profundidad",
            "Epicentro X",
            "Epicentro Y",
            "Estado",
            "Ref. / Principal"
        )

        self.tabla_eventos = ttk.Treeview(
            parent_frame,
            columns=columnas,
            show="headings"
        )

        anchos = [
            60,
            180,
            80,
            90,
            100,
            100,
            100,
            160
        ]

        for col, ancho in zip(
            columnas,
            anchos
        ):

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
            parent_frame,
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

    # ==================================================================
    # ACTUALIZAR TABLA
    # ==================================================================

    def actualizar_tabla_eventos(self):

        if not hasattr(
            self,
            "tabla_eventos"
        ):
            return

        # --------------------------------------------------------------
        # LIMPIAR TABLA
        # --------------------------------------------------------------

        for item in self.tabla_eventos.get_children():

            self.tabla_eventos.delete(
                item
            )

        if not self.escenario:

            return

        # --------------------------------------------------------------
        # OBTENER EVENTOS
        # --------------------------------------------------------------

        eventos = []

        if (
            hasattr(
                self.escenario,
                "arbol_eventos"
            )
            and self.escenario.arbol_eventos
        ):

            try:

                if hasattr(
                    self.escenario.arbol_eventos,
                    "obtener_todos_los_eventos"
                ):

                    eventos = (
                        self.escenario
                        .arbol_eventos
                        .obtener_todos_los_eventos()
                    )

                elif hasattr(
                    self.escenario.arbol_eventos,
                    "inorden"
                ):

                    eventos = (
                        self.escenario
                        .arbol_eventos
                        .inorden()
                    )

                else:

                    eventos = list(
                        self.escenario.arbol_eventos
                    )

            except Exception:

                eventos = list(
                    getattr(
                        self.escenario,
                        "dict_eventos",
                        {}
                    ).values()
                )

        elif hasattr(
            self.escenario,
            "dict_eventos"
        ):

            eventos = list(
                self.escenario.dict_eventos.values()
            )

        elif hasattr(
            self.escenario,
            "eventos"
        ):

            eventos = self.escenario.eventos

        # --------------------------------------------------------------
        # INSERTAR EVENTOS
        # --------------------------------------------------------------

        for ev in eventos:

            # ----------------------------------------------------------
            # ID
            # ----------------------------------------------------------

            id_evento = getattr(
                ev,
                "id",
                getattr(
                    ev,
                    "id_evento",
                    ""
                )
            )

            # ----------------------------------------------------------
            # FECHA
            # ----------------------------------------------------------

            fecha = getattr(
                ev,
                "fecha_hora",
                getattr(
                    ev,
                    "fecha",
                    ""
                )
            )

            # ----------------------------------------------------------
            # MAGNITUD
            # ----------------------------------------------------------

            magnitud = getattr(
                ev,
                "magnitud",
                ""
            )

            # ----------------------------------------------------------
            # PROFUNDIDAD
            # ----------------------------------------------------------

            profundidad = getattr(
                ev,
                "profundidad",
                ""
            )

            # ----------------------------------------------------------
            # EPICENTRO
            # ----------------------------------------------------------

            epicentro = getattr(
                ev,
                "epicentro",
                None
            )

            if epicentro is not None:

                if hasattr(
                    epicentro,
                    "x"
                ):

                    x = epicentro.x

                elif isinstance(
                    epicentro,
                    (tuple, list)
                ):

                    x = epicentro[0]

                else:

                    x = ""

                if hasattr(
                    epicentro,
                    "y"
                ):

                    y = epicentro.y

                elif isinstance(
                    epicentro,
                    (tuple, list)
                ):

                    y = epicentro[1]

                else:

                    y = ""

            else:

                x = ""
                y = ""

            # ----------------------------------------------------------
            # ESTADO
            # ----------------------------------------------------------

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

            # ----------------------------------------------------------
            # REFERENCIA
            # ----------------------------------------------------------

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

            # ----------------------------------------------------------
            # INSERTAR
            # ----------------------------------------------------------

            self.tabla_eventos.insert(
                "",
                "end",
                values=(
                    id_evento,
                    fecha,
                    magnitud,
                    profundidad,
                    x,
                    y,
                    estado,
                    ref_str
                )
            )

    # ==================================================================
    # FORMULARIO: ZONA
    # ==================================================================

    def _abrir_formulario_zona(self):

        win, frame = self._crear_formulario(
            "Crear Zona",
            "280x260"
        )

        campos = [
            "Nombre:",
            "X Mín:",
            "X Máx:",
            "Y Mín:",
            "Y Máx:"
        ]

        entries = {}

        for i, label in enumerate(campos):

            ttk.Label(
                frame,
                text=label
            ).grid(
                row=i,
                column=0,
                sticky="w",
                pady=2
            )

            e = ttk.Entry(
                frame
            )

            e.grid(
                row=i,
                column=1,
                pady=2
            )

            entries[label] = e

        var_poblada = tk.BooleanVar(
            value=False
        )

        ttk.Checkbutton(
            frame,
            text="¿Zona Poblada?",
            variable=var_poblada
        ).grid(
            row=5,
            columnspan=2,
            pady=5
        )

        def guardar():

            nombre = entries[
                "Nombre:"
            ].get().strip()

            if not nombre:

                messagebox.showerror(
                    "Error",
                    "El nombre no puede estar vacío.",
                    parent=win
                )

                return

            if any(
                z.nombre.lower() == nombre.lower()
                for z in self.escenario.zonas
            ):

                messagebox.showerror(
                    "Error",
                    f"Ya existe la zona '{nombre}'.",
                    parent=win
                )

                return

            try:

                x_min = float(
                    entries["X Mín:"].get()
                )

                x_max = float(
                    entries["X Máx:"].get()
                )

                y_min = float(
                    entries["Y Mín:"].get()
                )

                y_max = float(
                    entries["Y Máx:"].get()
                )

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Las coordenadas deben ser números válidos.",
                    parent=win
                )

                return

            if not (
                0 <= x_min <= 1000
                and 0 <= x_max <= 1000
                and 0 <= y_min <= 1000
                and 0 <= y_max <= 1000
            ):

                messagebox.showerror(
                    "Error",
                    "Las coordenadas deben estar entre 0 y 1000.",
                    parent=win
                )

                return

            if (
                x_min >= x_max
                or y_min >= y_max
            ):

                messagebox.showerror(
                    "Error",
                    "Mínimos deben ser menores que máximos.",
                    parent=win
                )

                return

            self.escenario.zonas.append(
                Zona(
                    nombre,
                    x_min,
                    x_max,
                    y_min,
                    y_max,
                    var_poblada.get()
                )
            )

            messagebox.showinfo(
                "Éxito",
                f"Zona '{nombre}' guardada con éxito.",
                parent=win
            )

            win.destroy()

        ttk.Button(
            frame,
            text="Guardar",
            command=guardar
        ).grid(
            row=6,
            columnspan=2,
            pady=10
        )

    # ==================================================================
    # FORMULARIO: ESTACIÓN
    # ==================================================================

    def _abrir_formulario_estacion(self):

        if not self.escenario.zonas:

            messagebox.showwarning(
                "Atención",
                "Cree al menos una zona antes de continuar.",
                parent=self.root
            )

            return

        win, frame = self._crear_formulario(
            "Crear Estación",
            "280x220"
        )

        ttk.Label(
            frame,
            text="ID Estación:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        entry_id = ttk.Entry(
            frame
        )

        entry_id.grid(
            row=0,
            column=1,
            pady=2
        )

        ttk.Label(
            frame,
            text="Nombre:"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )

        entry_nombre = ttk.Entry(
            frame
        )

        entry_nombre.grid(
            row=1,
            column=1,
            pady=2
        )

        ttk.Label(
            frame,
            text="Zona:"
        ).grid(
            row=2,
            column=0,
            sticky="w"
        )

        zonas_dict = {
            z.nombre: z
            for z in self.escenario.zonas
        }

        combo_zona = ttk.Combobox(
            frame,
            values=list(
                zonas_dict.keys()
            ),
            state="readonly"
        )

        combo_zona.grid(
            row=2,
            column=1,
            pady=2
        )

        combo_zona.current(0)

        ttk.Label(
            frame,
            text="Coord X:"
        ).grid(
            row=3,
            column=0,
            sticky="w"
        )

        entry_x = ttk.Entry(
            frame
        )

        entry_x.grid(
            row=3,
            column=1,
            pady=2
        )

        ttk.Label(
            frame,
            text="Coord Y:"
        ).grid(
            row=4,
            column=0,
            sticky="w"
        )

        entry_y = ttk.Entry(
            frame
        )

        entry_y.grid(
            row=4,
            column=1,
            pady=2
        )

        def guardar():

            id_est = entry_id.get().strip()
            nom = entry_nombre.get().strip()

            if not id_est or not nom:

                messagebox.showerror(
                    "Error",
                    "El ID y Nombre son obligatorios.",
                    parent=win
                )

                return

            if any(
                e.id_estacion.lower() == id_est.lower()
                for e in self.escenario.estaciones
            ):

                messagebox.showerror(
                    "Error",
                    f"Ya existe la estación ID '{id_est}'.",
                    parent=win
                )

                return

            try:

                x = float(
                    entry_x.get()
                )

                y = float(
                    entry_y.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Las coordenadas deben ser números válidos.",
                    parent=win
                )

                return

            if not (
                0 <= x <= 1000
                and 0 <= y <= 1000
            ):

                messagebox.showerror(
                    "Error",
                    "Coordenadas fuera de rango (0-1000).",
                    parent=win
                )

                return

            try:

                nueva_estacion = Estacion(
                    id_estacion=id_est,
                    nombre=nom,
                    x=x,
                    y=y,
                    zona=zonas_dict[
                        combo_zona.get()
                    ]
                )

            except ValueError as err:

                messagebox.showerror(
                    "Error",
                    str(err),
                    parent=win
                )

                return

            self.escenario.estaciones.append(
                nueva_estacion
            )

            messagebox.showinfo(
                "Éxito",
                "Estación creada con éxito.",
                parent=win
            )

            win.destroy()

        ttk.Button(
            frame,
            text="Guardar",
            command=guardar
        ).grid(
            row=5,
            columnspan=2,
            pady=10
        )

    # ==================================================================
    # FORMULARIO: EPICENTRO
    # ==================================================================

    def _abrir_formulario_epicentro(self):

        if not self.escenario.zonas:

            messagebox.showwarning(
                "Atención",
                "Cree al menos una zona antes de continuar.",
                parent=self.root
            )

            return

        win, frame = self._crear_formulario(
            "Crear Epicentro",
            "250x150"
        )

        ttk.Label(
            frame,
            text="Coord X:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        entry_x = ttk.Entry(
            frame
        )

        entry_x.grid(
            row=0,
            column=1,
            pady=2
        )

        ttk.Label(
            frame,
            text="Coord Y:"
        ).grid(
            row=1,
            column=0,
            sticky="w"
        )

        entry_y = ttk.Entry(
            frame
        )

        entry_y.grid(
            row=1,
            column=1,
            pady=2
        )

        def guardar():

            try:

                x = float(
                    entry_x.get()
                )

                y = float(
                    entry_y.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Coordenadas no válidas.",
                    parent=win
                )

                return

            if not (
                0 <= x <= 1000
                and 0 <= y <= 1000
            ):

                messagebox.showerror(
                    "Error",
                    "Coordenadas fuera de rango (0-1000).",
                    parent=win
                )

                return

            nuevo_epi = Epicentro(
                x=x,
                y=y,
                zonas_escenario=self.escenario.zonas
            )

            if nuevo_epi.zona is None:

                messagebox.showerror(
                    "Error",
                    f"El punto ({x}, {y}) no pertenece a ninguna zona.",
                    parent=win
                )

                return

            self.escenario.epicentros.append(
                nuevo_epi
            )

            messagebox.showinfo(
                "Éxito",
                f"Epicentro creado en zona "
                f"'{nuevo_epi.zona.nombre}'.",
                parent=win
            )

            win.destroy()

        ttk.Button(
            frame,
            text="Guardar",
            command=guardar
        ).grid(
            row=2,
            columnspan=2,
            pady=10
        )

    # ==================================================================
    # FORMULARIO: EVENTO
    # ==================================================================

    def _abrir_formulario_evento(self):

        if (
            not self.escenario.epicentros
            or not self.escenario.estaciones
        ):

            messagebox.showwarning(
                "Atención",
                "Requiere al menos 1 Epicentro y 1 Estación creados.",
                parent=self.root
            )

            return

        win, frame = self._crear_formulario(
            "Crear Evento",
            "320x250"
        )

        campos = [
            "ID Evento:",
            "Magnitud:",
            "Profundidad:",
            "Epicentro:",
            "Estación:",
            "Fecha/Hora:"
        ]

        entries = {}

        epicentros_dict = {
            f"({epi.x}, {epi.y})": epi
            for epi in self.escenario.epicentros
        }

        estaciones_dict = {
            f"{est.id_estacion} - {est.nombre}": est
            for est in self.escenario.estaciones
        }

        for i, label in enumerate(campos):

            ttk.Label(
                frame,
                text=label
            ).grid(
                row=i,
                column=0,
                sticky="w",
                pady=2
            )

            if label == "Epicentro:":

                e = ttk.Combobox(
                    frame,
                    values=list(
                        epicentros_dict.keys()
                    ),
                    state="readonly"
                )

                e.current(0)

            elif label == "Estación:":

                e = ttk.Combobox(
                    frame,
                    values=list(
                        estaciones_dict.keys()
                    ),
                    state="readonly"
                )

                e.current(0)

            else:

                e = ttk.Entry(
                    frame
                )

            e.grid(
                row=i,
                column=1,
                pady=2
            )

            entries[label] = e

        def guardar():

            # ----------------------------------------------------------
            # ID
            # ----------------------------------------------------------

            try:

                id_evt = int(
                    entries[
                        "ID Evento:"
                    ].get().strip()
                )

                if not (
                    1 <= id_evt <= 999999
                ):

                    raise ValueError()

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "ID debe ser entero entre 1 y 999999.",
                    parent=win
                )

                return

            if id_evt in self.escenario.dict_eventos:

                messagebox.showerror(
                    "Error",
                    f"El ID '{id_evt}' ya existe.",
                    parent=win
                )

                return

            # ----------------------------------------------------------
            # MAGNITUD Y PROFUNDIDAD
            # ----------------------------------------------------------

            try:

                mag = float(
                    entries[
                        "Magnitud:"
                    ].get().strip()
                )

                prof = float(
                    entries[
                        "Profundidad:"
                    ].get().strip()
                )

            except ValueError:

                messagebox.showerror(
                    "Error",
                    "Magnitud y Profundidad deben ser números.",
                    parent=win
                )

                return

            if (
                not (-2.0 <= mag <= 10.0)
                or not (0.0 <= prof <= 700.0)
            ):

                messagebox.showerror(
                    "Error",
                    "Magnitud (-2 a 10) o Profundidad "
                    "(0 a 700) fuera de rango.",
                    parent=win
                )

                return

            # ----------------------------------------------------------
            # CREAR EVENTO
            # ----------------------------------------------------------

            nuevo_evento = Evento(
                id_evento=id_evt,
                magnitud=mag,
                profundidad=prof,
                epicentro=epicentros_dict[
                    entries[
                        "Epicentro:"
                    ].get()
                ],
                estacion_origen=estaciones_dict[
                    entries[
                        "Estación:"
                    ].get()
                ],
                fecha_hora=(
                    entries[
                        "Fecha/Hora:"
                    ].get().strip()
                    or None
                )
            )

            # ----------------------------------------------------------
            # GUARDAR EN DICCIONARIO
            # ----------------------------------------------------------

            self.escenario.dict_eventos[
                id_evt
            ] = nuevo_evento

            # ----------------------------------------------------------
            # HISTÓRICO
            # ----------------------------------------------------------

            self.escenario.historico.append(
                nuevo_evento
            )

            # ----------------------------------------------------------
            # AVL
            # ----------------------------------------------------------

            arbol_avl = getattr(
                self.escenario,
                "arbol_avl",
                None
            )

            if arbol_avl is not None:

                arbol_avl.insertar(
                    Nodo(
                        evento=nuevo_evento
                    ),
                    self.escenario.L
                )

            # ----------------------------------------------------------
            # ACTUALIZAR TABLA
            # ----------------------------------------------------------

            self.actualizar_tabla_eventos()

            # ----------------------------------------------------------
            # MENSAJE
            # ----------------------------------------------------------

            messagebox.showinfo(
                "Éxito",
                f"Evento SIS-{nuevo_evento.id:06d} registrado.",
                parent=win
            )

            win.destroy()

        ttk.Button(
            frame,
            text="Guardar Evento",
            command=guardar
        ).grid(
            row=6,
            columnspan=2,
            pady=10
        )