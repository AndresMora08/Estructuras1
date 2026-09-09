import tkinter as tk
from interfaz import SismoLabGUI

if __name__ == "__main__":
    # 1. Crear la ventana principal
    root = tk.Tk()
    
    # 2. Instanciar la interfaz pasando la ventana raíz
    app = SismoLabGUI(root)
    
    # 3. Iniciar el bucle de eventos
    root.mainloop()
    
    #ayudado con IA
    ####