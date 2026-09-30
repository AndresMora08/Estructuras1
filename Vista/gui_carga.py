from Logica.controlador_json import ControladorJSON


class CargaMixin:

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
    # ACTUALIZAR INTERFAZ
    # ==================================================================

    def actualizar_interfaz(self):

        self.root.update_idletasks()

        self.actualizar_tabla_eventos()