import tkinter as tk
from tkinter import messagebox, ttk

from Modelos.Escenario import Escenario
from Vista.gui_asociaciones import AsociacionesMixin
from Vista.gui_carga import CargaMixin
from Vista.gui_eventos import EventosMixin
from Vista.gui_formularios import FormulariosMixin
from Vista.VentanaReportes import VentanaReportes
from Vista.Mapa import Mapa


class SismoLabGUI(
    FormulariosMixin,
    EventosMixin,
    AsociacionesMixin,
    CargaMixin
):

    def __init__(self, root: tk.Tk, escenario: Escenario):

        self.root = root
        self.escenario = escenario

        # Compatibilidad con VentanaAsociaciones
        self.escenario_actual = escenario

        self.root.title("SismoLab AVL - Monitor")
        self.root.geometry("1000x400")

        # ==========================================================
        # TÍTULO
        # ==========================================================

        ttk.Label(
            self.root,
            text="SismoLab AVL",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # ==========================================================
        # MENÚ PRINCIPAL (BOTONES CATEGORÍA QUE ABREN VENTANAS)
        # ==========================================================

        f_botones = ttk.Frame(self.root)
        f_botones.pack(pady=15)

        # Definición de categorías y sus opciones internas
        self.categorias = {
            "Crear": [
                ("Crear Zona", self._abrir_formulario_zona),
                ("Crear Estación", self._abrir_formulario_estacion),
                ("Crear Epicentro", self._abrir_formulario_epicentro),
                ("Crear Evento", self._abrir_formulario_evento),
            ],
            "Mapa y Árbol": [
                ("Plano Geográfico", self.abrir_plano_geografico),
                ("Ver Árbol AVL", self._abrir_visualizador_arbol),
            ],
            "JSON": [
                ("Cargar Inserciones", self._cargar_por_inserciones),
                ("Guardar Inserciones", self._guardar_inserciones_json),
                ("Cargar Topología", self._cargar_por_topologia),
                ("Guardar Topología", self._guardar_topologia_json),
            ],
            "Versiones y Retroceso": [
                ("Guardar Versión", self.guardar_version_con_nombre),
                ("Restaurar Versión", self.restaurar_version_dialogo),
                ("Deshacer Acción", self.deshacer_accion),
            ],
            "Consultas y Asociaciones": [
                ("Consultar Eventos", self._abrir_busqueda),
                ("Procesar Reportes", self.abrir_ventana_reportes),
                ("Asociaciones", self.abrir_ventana_asociaciones),
            ]
        }

        # Generar botón principal por cada categoría
        for nombre_cat, opciones in self.categorias.items():
            ttk.Button(
                f_botones,
                text=nombre_cat,
                command=lambda cat=nombre_cat, ops=opciones: self._abrir_menu_categoria(cat, ops)
            ).pack(side=tk.LEFT, padx=10, ipady=5)

    # ==========================================================
    # VENTANA FLOTANTE DE OPCIONES POR CATEGORÍA
    # ==========================================================

    def _abrir_menu_categoria(self, titulo: str, opciones: list):
        """Abre una ventana pequeña centrándola en pantalla con las opciones de la categoría."""
        ventana_menu = tk.Toplevel(self.root)
        ventana_menu.title(f"Opciones: {titulo}")
        ventana_menu.transient(self.root)  # Bloquea interacción con la ventana padre
        ventana_menu.grab_set()
        ventana_menu.resizable(False, False)

        ttk.Label(
            ventana_menu,
            text=f"Seleccione una acción ({titulo}):",
            font=("Arial", 11, "bold")
        ).pack(pady=(15, 10), padx=20)

        f_opciones = ttk.Frame(ventana_menu)
        f_opciones.pack(pady=10, padx=20)

        for texto, comando in opciones:
            # Función auxiliar para ejecutar la acción y cerrar el submenú
            def ejecutar_y_cerrar(cmd=comando):
                ventana_menu.destroy()
                cmd()

            ttk.Button(
                f_opciones,
                text=texto,
                width=25,
                command=ejecutar_y_cerrar
            ).pack(pady=4)

        ttk.Button(
            ventana_menu,
            text="Cancelar",
            command=ventana_menu.destroy
        ).pack(pady=(5, 15))

    # ==========================================================
    # MÉTODOS DE VENTANAS Y ACCIONES
    # ==========================================================

    def abrir_ventana_reportes(self):
        """Abre la ventana independiente de gestión y procesamiento de reportes."""
        VentanaReportes(
            self.root,
            self.escenario
        )

    def _deshacer_accion(self):
        """Restaura el estado anterior almacenado en la pila."""

        if self.escenario.deshacer_ultima_accion():

            messagebox.showinfo(
                "Deshacer",
                "Acción revertida exitosamente.",
                parent=self.root
            )

            self.actualizar_interfaz()

        else:

            messagebox.showwarning(
                "Deshacer",
                "No hay acciones previas para deshacer.",
                parent=self.root
            )

    def abrir_plano_geografico(self):
        """Abre la ventana del mapa geográfico."""
        Mapa(self.root, self.escenario)