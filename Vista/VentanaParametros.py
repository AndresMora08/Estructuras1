import tkinter as tk
from tkinter import messagebox, ttk


class VentanaParametros(tk.Toplevel):
    """Edits W, R, L and T. Applying is a single undoable action."""

    def __init__(self, parent, escenario, callback_actualizar=None):
        super().__init__(parent)
        self.title("Parámetros del Escenario")
        self.geometry("360x260")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.escenario = escenario
        self.callback_actualizar = callback_actualizar
        self.entradas = {}

        frame = ttk.LabelFrame(self, text=" W, R, L y T ", padding=15)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        campos = [
            ("W", "Ventana W (horas):", escenario.W),
            ("R", "Radio R (km):", escenario.R),
            ("L", "Límite L (profundidad):", escenario.L),
            ("T", "Antigüedad T (horas):", escenario.T),
        ]
        for fila, (clave, etiqueta, valor) in enumerate(campos):
            ttk.Label(frame, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=6)
            entrada = ttk.Entry(frame, width=12)
            entrada.insert(0, str(valor))
            entrada.grid(row=fila, column=1, padx=10, pady=6)
            self.entradas[clave] = entrada

        ttk.Button(frame, text="Aplicar", command=self._aplicar).grid(
            row=len(campos), column=0, columnspan=2, pady=12
        )

    def _aplicar(self):
        exito, mensaje = self.escenario.cambiar_parametros(
            self.entradas["W"].get().strip(),
            self.entradas["R"].get().strip(),
            self.entradas["L"].get().strip(),
            self.entradas["T"].get().strip(),
        )
        if not exito:
            messagebox.showerror("Parámetros inválidos", mensaje, parent=self)
            return

        if self.callback_actualizar:
            self.callback_actualizar()
        messagebox.showinfo("Parámetros", mensaje, parent=self)
        self.destroy()
