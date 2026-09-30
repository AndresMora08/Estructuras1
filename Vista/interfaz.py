import tkinter as tk
from tkinter import ttk

from Modelos.Escenario import Escenario

from Vista.gui_formularios import FormulariosMixin
from Vista.gui_eventos import EventosMixin
from Vista.gui_asociaciones import AsociacionesMixin
from Vista.gui_carga import CargaMixin
from Vista.VentanaReportes import VentanaReportes  # <-- IMPORTAR LA NUEVA VENTANA


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
        self.root.geometry("1200x700")

        # ==========================================================
        # TÍTULO
        # ==========================================================

        ttk.Label(
            self.root,
            text="SismoLab AVL",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # ==========================================================
        # MENÚ PRINCIPAL
        # ==========================================================

        f_botones = ttk.Frame(self.root)
        f_botones.pack(pady=5)

        botones = [
            ("Crear Zona", self._abrir_formulario_zona),
            ("Crear Estación", self._abrir_formulario_estacion),
            ("Crear Epicentro", self._abrir_formulario_epicentro),
            ("Crear Evento", self._abrir_formulario_evento),
            ("Ver Árbol AVL", self._abrir_visualizador_arbol),
            ("Consultar Eventos", self._abrir_busqueda),
            ("Procesar Reportes", self.abrir_ventana_reportes),  # <-- NUEVO BOTÓN
            ("Cargar Inserciones", self._cargar_por_inserciones),
            ("Cargar Topología", self._cargar_por_topologia),
            ("Gestión y JSON", self.abrir_ventana_gestion),
            ("Asociaciones", self.abrir_ventana_asociaciones),
        ]

        for texto, comando in botones:

            ttk.Button(
                f_botones,
                text=texto,
                command=comando
            ).pack(
                side=tk.LEFT,
                padx=2
            )

    # ==========================================================
    # MÉTODO PARA ABRIR VENTANA DE REPORTES
    # ==========================================================

    def abrir_ventana_reportes(self):
        """Abre la ventana independiente de gestión y procesamiento de reportes."""
        VentanaReportes(self.root, self.escenario)