import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, Optional
from Logica.controlador_json import ControladorJSON


class VentanaEliminacionManual:

    def __init__(
        self,
        parent_window: tk.Toplevel,
        evento: object,
        arbol_avl: Optional[object],
        dict_eventos: Dict[int, object],
        escenario: object,
        callback_al_eliminar: Callable[[], None],
    ):
        self.evento = evento
        self.arbol_avl = arbol_avl
        self.dict_eventos = dict_eventos
        self.escenario = escenario
        self.callback_al_eliminar = callback_al_eliminar

        # Configuración de la ventana modal
        self.ventana = tk.Toplevel(parent_window)
        self.ventana.title("Gestión y Eliminación de Evento")
        self.ventana.geometry("380x320")
        self.ventana.resizable(False, False)
        self.ventana.grab_set()

        # Etiqueta principal con el ID del evento
        id_evt = getattr(self.evento, "id_evento", getattr(self.evento, "id", 0))
        ttk.Label(
            self.ventana,
            text=f"Evento: SIS-{id_evt:06d}",
            font=("Arial", 11, "bold"),
        ).pack(pady=15)

        # Marco contenedor para los botones de acción
        f_acciones = ttk.Frame(self.ventana)
        f_acciones.pack(fill=tk.BOTH, expand=True, padx=20)

        # 1. BOTÓN ELIMINAR
        btn_eliminar = ttk.Button(
            f_acciones, text="🗑️ Eliminar Evento", command=self._ejecutar_eliminacion
        )
        btn_eliminar.pack(fill=tk.X, pady=8)

        # 2. BOTÓN GUARDAR JSON
        btn_guardar = ttk.Button(
            f_acciones, text="💾 Guardar Escenario en JSON", command=self.guardar_json
        )
        btn_guardar.pack(fill=tk.X, pady=8)

        # 3. BOTÓN CARGAR JSON
        btn_cargar = ttk.Button(
            f_acciones, text="📂 Cargar desde JSON", command=self.cargar_json
        )
        btn_cargar.pack(fill=tk.X, pady=8)

        # Botón inferior para cerrar
        ttk.Button(
            self.ventana, text="Cancelar", command=self.ventana.destroy
        ).pack(pady=10)

    def _ejecutar_eliminacion(self):
        id_evt = getattr(self.evento, "id_evento", getattr(self.evento, "id", None))
        if id_evt is None:
            messagebox.showerror("Error", "No se pudo determinar el ID del evento.", parent=self.ventana)
            return

        if not messagebox.askyesno(
            "Confirmar", 
            f"¿Está seguro de eliminar el evento SIS-{id_evt:06d}?", 
            parent=self.ventana
        ):
            return

        # Delegación de la lógica de negocio al Escenario
        exito, mensaje = self.escenario.eliminar_evento_por_id(id_evt)

        if exito:
            messagebox.showinfo("Éxito", mensaje, parent=self.ventana)
            self.ventana.destroy()
            self.callback_al_eliminar()
        else:
            messagebox.showerror("Error", mensaje, parent=self.ventana)

    def guardar_json(self):
        """Delega la serialización completa al ControladorJSON."""
        ControladorJSON.guardar_escenario_completo(self.escenario, parent_window=self.ventana)

    def cargar_json(self):
        """Delega la lectura y reconstrucción atómica al ControladorJSON."""
        exito = ControladorJSON.cargar_json(self.escenario, parent_window=self.ventana)
        if exito:
            self.callback_al_eliminar()
            self.ventana.destroy()