import tkinter as tk
from tkinter import messagebox, ttk

from Modelos.Epicentro import Epicentro
from Modelos.Estacion import Estacion
from Modelos.Evento import Evento
from Modelos.Nodo import Nodo
from Modelos.Zona import Zona
from datetime import datetime, timezone
from Modelos.Asociaciones import recalcular_asociaciones_escenario


class FormulariosMixin:

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
            # FECHA / HORA (empty = simulation clock, never > clock)
            # ----------------------------------------------------------

            reloj = self.escenario.reloj
            if reloj.tzinfo is None:
                reloj = reloj.replace(tzinfo=timezone.utc)
            reloj = reloj.replace(microsecond=0)

            texto_fecha = entries["Fecha/Hora:"].get().strip()
            if not texto_fecha:
                texto_fecha = reloj.strftime("%Y-%m-%dT%H:%M:%SZ")

            try:
                fecha_evento = datetime.strptime(
                    texto_fecha, "%Y-%m-%dT%H:%M:%SZ"
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "Fecha inválida. Use el formato 2026-09-07T10:00:00Z.",
                    parent=win
                )
                return

            if fecha_evento > reloj:
                messagebox.showerror(
                    "Error",
                    "La fecha no puede ser posterior al reloj de simulación "
                    f"({reloj.strftime('%Y-%m-%dT%H:%M:%SZ')}).",
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
                fecha_hora=texto_fecha
            )

            # ----------------------------------------------------------
            # GUARDAR EN DICCIONARIO
            # ----------------------------------------------------------

            self.escenario.dict_eventos[
                id_evt
            ] = nuevo_evento

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

            # --- NUEVO: Recalcular asociaciones tras una nueva alta ---
            W_actual = getattr(self.escenario, "W", 48.0)
            R_actual = getattr(self.escenario, "R", 40.0)
            recalcular_asociaciones_escenario(self.escenario, W_actual, R_actual)
            # ----------------------------------------------------------

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