
import tkinter as tk
from tkinter import messagebox, ttk

from Modelos.Asociaciones import recalcular_asociaciones_escenario

from Vista.VentanaAsociaciones import VentanaAsociaciones


class AsociacionesMixin:

    # ==================================================================
    # ASSOCIATIONS
    #
    # The window is opened only when the button is pressed.
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
    # ASSOCIATIONS RECALCULATION
    #
    # Kept for compatibility with existing code.
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
    # ASSOCIATION PARAMETERS PANEL
    #
    # Kept for compatibility.
    # Not called from __init__.
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
        # RECALCULATE BUTTON
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

