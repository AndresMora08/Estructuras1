from tkinter import messagebox, simpledialog, Toplevel, Listbox, Button, SINGLE, END
from Logica.controlador_json import ControladorJSON


class CargaMixin:

    # ==================================================================
    # DESHACER (PILA DE RETROCESO)
    # ==================================================================
    def deshacer_accion(self):
        """Invoca el retroceso del escenario y actualiza la interfaz."""
        exito = self.escenario.deshacer_ultima_accion()
        if exito:
            self.actualizar_interfaz()
            messagebox.showinfo("Deshacer", "Se restableció con éxito el estado operativo anterior.", parent=self.root)
        else:
            messagebox.showwarning("Deshacer", "No hay acciones previas en la pila para deshacer.", parent=self.root)

    # ==================================================================
    # GESTIÓN DE VERSIONES PERSISTENTES
    # ==================================================================
    def guardar_version_con_nombre(self):
        """Solicita un nombre al usuario y persiste la versión actual en disco."""
        nombre = simpledialog.askstring("Guardar Versión", "Ingrese el nombre de la versión:", parent=self.root)
        if nombre:
            exito, mensaje = self.escenario.guardar_version_persistente(nombre)
            if exito:
                messagebox.showinfo("Éxito", mensaje, parent=self.root)
            else:
                messagebox.showerror("Error", mensaje, parent=self.root)

    def restaurar_version_dialogo(self):
        """Despliega una ventana emergente para elegir y restaurar una versión persistente."""
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
            
            # Restaurar (registra en la pila de deshacer automáticamente)
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
    # CARGA POR INSERCIONES (APILANDO ESTADO PREVIO)
    # ==================================================================
    def _cargar_por_inserciones(self):
        # Guardar estado previo para permitir deshacer la carga
        self.escenario.guardar_estado_pila()

        exito = ControladorJSON.cargar_por_inserciones(
            self.escenario,
            parent_window=self.root
        )

        if exito:
            self.actualizar_interfaz()
            self.actualizar_tabla_eventos()
        else:
            # Si la carga falló/se canceló, removemos el snapshot redundante de la pila
            self.escenario.pila_deshacer.pop()

    # ==================================================================
    # CARGA POR TOPOLOGÍA (APILANDO ESTADO PREVIO)
    # ==================================================================
    def _cargar_por_topologia(self):
        # Guardar estado previo para permitir deshacer la carga
        self.escenario.guardar_estado_pila()

        exito = ControladorJSON.cargar_por_topologia(
            self.escenario,
            parent_window=self.root
        )

        if exito:
            self.actualizar_interfaz()
            self.actualizar_tabla_eventos()
        else:
            # Si la carga falló/se canceló, removemos el snapshot redundante de la pila
            self.escenario.pila_deshacer.pop()

    # ==================================================================
    # GUARDADO
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
    # ACTUALIZAR INTERFAZ
    # ==================================================================
    def actualizar_interfaz(self):
        self.root.update_idletasks()
        self.actualizar_tabla_eventos()