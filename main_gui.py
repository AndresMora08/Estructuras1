import tkinter as tk
from Modelos.Escenario import Escenario
from Vista.interfaz import SismoLabGUI  # Ajusta la ruta de importación según tu estructura

if __name__ == "__main__":
  # 1. Crear el objeto de Escenario global único
  escenario_global = Escenario()

  # 2. Inicializar Tkinter
  root = tk.Tk()

  # 3. Pasar el escenario a la interfaz gráfica
  app = SismoLabGUI(root, escenario=escenario_global)

  # 4. Iniciar el loop de la interfaz
  root.mainloop()