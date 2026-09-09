import tkinter as tk
from tkinter import ttk

class SismoLabGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        
        # 1. Configuración de la ventana principal
        self.root.title("SismoLab AVL - Monitor")
        self.root.geometry("800x500")  # Ancho x Alto en píxeles
        
        # 2. Agregar un mensaje de prueba
        self._agregar_mensaje_prueba()

    def _agregar_mensaje_prueba(self):
        # Un widget de texto simple (Label)
        etiqueta = ttk.Label(
            self.root, 
            text="¡Bienvenido a SismoLab AVL!", 
            font=("Arial", 14, "bold")
        )
        # .pack() posiciona la etiqueta en la ventana
        etiqueta.pack(pady=20)