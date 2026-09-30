from tkinter import messagebox
from Logica.controlador_json import ControladorJSON


class CargaMixin:

    def _cargar_por_inserciones(self):

        exito = ControladorJSON.cargar_por_inserciones(
            self.escenario,
            parent_window=self.root
        )

        if exito:
            self.actualizar_interfaz()
            messagebox.showinfo(
                "Carga exitosa",
                "La carga por inserciones se realizó correctamente."
            )

    def _guardar_por_inserciones(self):

        ControladorJSON.guardar_secuencia_inserciones(
            self.escenario,
            parent_window=self.root
        )

    def _cargar_por_topologia(self):

        exito = ControladorJSON.cargar_por_topologia(
            self.escenario,
            parent_window=self.root
        )

        if exito:
            self.actualizar_interfaz()
            messagebox.showinfo(
                "Carga exitosa",
                "La carga por topología se realizó correctamente."
            )

    def _guardar_por_topologia(self):

        ControladorJSON.guardar_escenario_completo(
            self.escenario,
            parent_window=self.root
        )

    def actualizar_interfaz(self):

        self.root.update_idletasks()

        if hasattr(
            self,
            "actualizar_tabla_eventos"
        ):
            self.actualizar_tabla_eventos()