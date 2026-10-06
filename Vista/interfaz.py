import tkinter as tk
from tkinter import messagebox, ttk

from Modelos.Escenario import Escenario
from Vista.ConsultaEventos import ConsultaEventos
from Vista.gui_asociaciones import AsociacionesMixin
from Vista.gui_carga import CargaMixin
from Vista.gui_eventos import EventosMixin
from Vista.gui_formularios import FormulariosMixin
from Vista.VentanaReportes import VentanaReportes
from Vista.VentanaParametros import VentanaParametros
from Vista.VentanaComparativaBST import VentanaComparativaBST
from Vista.VisualizadorAVL import VisualizadorAVL
from Vista.Mapa import Mapa
from Vista.VentanaEventosEstado import VentanaEventosEstado

class SismoLabGUI(
    FormulariosMixin,
    EventosMixin,
    AsociacionesMixin,
    CargaMixin
):

    def __init__(self, root: tk.Tk, escenario: Escenario):

        self.root = root
        self.escenario = escenario

        # Compatibility with VentanaAsociaciones
        self.escenario_actual = escenario

        self.root.title("SismoLab AVL - Monitor")
        self.root.geometry("1000x400")

        ttk.Label(
            self.root,
            text="SismoLab AVL",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        f_botones = ttk.Frame(self.root)
        f_botones.pack(pady=15)

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
                ("Comparar AVL vs BST", self.abrir_comparativa_bst),
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
                 ("Eventos Activos e Histórico", self.abrir_ventana_eventos_estado),
                ("Procesar Reportes", self.abrir_ventana_reportes),
                ("Asociaciones", self.abrir_ventana_asociaciones),
                ("Parámetros W, R, L, T", self.abrir_ventana_parametros),
            ]
        }

        for nombre_cat, opciones in self.categorias.items():
            ttk.Button(
                f_botones,
                text=nombre_cat,
                command=lambda cat=nombre_cat, ops=opciones: self._abrir_menu_categoria(cat, ops)
            ).pack(side=tk.LEFT, padx=10, ipady=5)

    # ==========================================================
    # FLOATING OPTIONS WINDOW PER CATEGORY
    # ==========================================================

    def _abrir_menu_categoria(self, titulo: str, opciones: list):
        """Small modal window with the options of the category."""
        ventana_menu = tk.Toplevel(self.root)
        ventana_menu.title(f"Opciones: {titulo}")
        ventana_menu.transient(self.root)
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
    # WINDOWS AND ACTIONS
    # ==========================================================

    def abrir_ventana_reportes(self):
        """Independent window to manage and process reports."""
        VentanaReportes(
            self.root,
            self.escenario
        )

    def abrir_ventana_parametros(self):
        """Edits W, R, L and T (undoable)."""
        VentanaParametros(
            self.root,
            self.escenario,
            callback_actualizar=self.actualizar_interfaz
        )

    def _abrir_busqueda(self):
        """
        Overrides EventosMixin: the query also works when only archived or
        removed events exist (it must report active / archived / removed).
        """
        esc = self.escenario

        if not esc.dict_eventos and not esc.historico:
            messagebox.showinfo(
                "Sin Eventos",
                "No hay registro de eventos en el sistema.",
                parent=self.root
            )
            return

        ConsultaEventos(self.root, esc.dict_eventos, esc.arbol_avl, esc)

    def _abrir_visualizador_arbol(self):
        """
        Overrides EventosMixin: passes the scenario so the viewer always reads
        the live tree (undo / restore replace the AVL object).
        """
        arbol = getattr(self.escenario, "arbol_avl", None)

        if not arbol or not arbol.raiz:
            messagebox.showinfo(
                "Árbol Vacío",
                "El árbol AVL no contiene eventos registrados aún.",
                parent=self.root
            )
            return

        VisualizadorAVL(self.root, self.escenario)

    def abrir_comparativa_bst(self):
        """AVL vs BST built from the same active events and insertion order."""
        arbol = getattr(self.escenario, "arbol_avl", None)

        if not arbol or not arbol.raiz:
            messagebox.showinfo(
                "Sin eventos",
                "No hay eventos activos para comparar.",
                parent=self.root
            )
            return

        VentanaComparativaBST(self.root, self.escenario)

    def _deshacer_accion(self):
        """Restores the previous state stored in the stack."""

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
        """Opens the geographic map window."""
        Mapa(self.root, self.escenario)
    
    def abrir_ventana_eventos_estado(self):
    
     VentanaEventosEstado(
        self.root,
        self.escenario
    )