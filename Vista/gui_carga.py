from tkinter import messagebox, simpledialog, Toplevel, Listbox, Button, SINGLE, END
from Logica.controlador_json import ControladorJSON
from Modelos.Asociaciones import recalcular_asociaciones_escenario


class CargaMixin:

    # ==================================================================
    # UNDO (STACK)
    # ==================================================================
    def deshacer_accion(self):
        """Undoes the last action and refreshes the interface."""
        exito = self.escenario.deshacer_ultima_accion()
        if exito:
            self.actualizar_interfaz()
            messagebox.showinfo("Deshacer", "Se restableció con éxito el estado operativo anterior.", parent=self.root)
        else:
            messagebox.showwarning("Deshacer", "No hay acciones previas en la pila para deshacer.", parent=self.root)

    # ==================================================================
    # PERSISTENT NAMED VERSIONS
    # ==================================================================
    def guardar_version_con_nombre(self):
        """Asks for a name and stores the current version on disk."""
        nombre = simpledialog.askstring("Guardar Versión", "Ingrese el nombre de la versión:", parent=self.root)
        if nombre:
            exito, mensaje = self.escenario.guardar_version_persistente(nombre)
            if exito:
                messagebox.showinfo("Éxito", mensaje, parent=self.root)
            else:
                messagebox.showerror("Error", mensaje, parent=self.root)

    def restaurar_version_dialogo(self):
        """Pop-up to choose and restore a persistent version."""
        versiones = self.escenario.listar_versiones_persistentes()
        if not versiones:
            messagebox.showinfo("Restaurar Versión", "No hay versiones guardadas actualmente.", parent=self.root)
            return

        ventana = Toplevel(self.root)
        ventana.title("Restaurar Versión Persistente")
        ventana.geometry("300x250")
        ventana.transient(self.root)
        ventana.grab_set()

        listbox = Listbox(ventana, selectmode=SINGLE)
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for v in versiones:
            listbox.insert(END, v)

        def confirmar_restauracion():
            seleccion = listbox.curselection()
            if not seleccion:
                messagebox.showwarning("Atención", "Seleccione una versión de la lista.", parent=ventana)
                return
            nombre_version = listbox.get(seleccion[0])

            # Restoring pushes its own snapshot, so it can be undone
            exito, mensaje = self.escenario.restaurar_version_persistente(nombre_version)
            ventana.destroy()

            if exito:
                self.actualizar_interfaz()
                messagebox.showinfo("Éxito", mensaje, parent=self.root)
            else:
                messagebox.showerror("Error", mensaje, parent=self.root)

        btn_restaurar = Button(ventana, text="Restaurar Selección", command=confirmar_restauracion)
        btn_restaurar.pack(pady=5)

    # ==================================================================
    # ASSOCIATIONS AFTER A LOAD
    # ==================================================================
    def _recalcular_asociaciones_tras_carga(self):
        """
        A load replaces the catalog, so the associations are recomputed with the
        deterministic policy (same logical result as the stored references).
        """
        try:
            recalcular_asociaciones_escenario(self.escenario, self.escenario.W, self.escenario.R)
        except Exception as error:
            messagebox.showwarning(
                "Asociaciones",
                f"La carga fue exitosa pero no se pudieron recalcular las asociaciones:\n{error}",
                parent=self.root
            )

    # ==================================================================
    # LOAD BY INSERTIONS (STACKING PREVIOUS STATE)
    # ==================================================================
    def _cargar_por_inserciones(self):
        # Snapshot first so the load can be undone
        self.escenario.guardar_estado_pila()

        exito = ControladorJSON.cargar_por_inserciones(
            self.escenario,
            parent_window=self.root
        )

        if exito:
            self._recalcular_asociaciones_tras_carga()
            self.actualizar_interfaz()
            self.actualizar_tabla_eventos()
        else:
            # Failed or cancelled: drop the redundant snapshot
            self.escenario.pila_deshacer.pop()

    # ==================================================================
    # LOAD BY TOPOLOGY (STACKING PREVIOUS STATE)
    # ==================================================================
    def _cargar_por_topologia(self):
        self.escenario.guardar_estado_pila()

        exito = ControladorJSON.cargar_por_topologia(
            self.escenario,
            parent_window=self.root
        )

        if exito:
            self._recalcular_asociaciones_tras_carga()
            self.actualizar_interfaz()
            self.actualizar_tabla_eventos()
        else:
            self.escenario.pila_deshacer.pop()

    # ==================================================================
    # SAVE
    # ==================================================================
    def _guardar_topologia_json(self):
        """Saves the full operational state (reloadable with 'Cargar Topología')."""
        ControladorJSON.guardar_escenario_completo(
            self.escenario,
            parent_window=self.root
        )

    def _guardar_inserciones_json(self):
        """Saves the active events (reloadable with 'Cargar Inserciones')."""
        ControladorJSON.guardar_para_inserciones(
            self.escenario,
            parent_window=self.root
        )

    # ==================================================================
    # REFRESH INTERFACE
    # ==================================================================
    def actualizar_interfaz(self):
        self.root.update_idletasks()
        self.actualizar_tabla_eventos()