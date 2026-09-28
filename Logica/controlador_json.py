# controlador_json.py
import json
from tkinter import messagebox, filedialog

class ControladorJSON:
    @staticmethod
    def guardar_json(datos, ruta="sismolab_backup.json"):
        """Método para guardar los datos actuales en un archivo JSON."""
        try:
            with open(ruta, "w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", f"Datos guardados correctamente en {ruta}.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

    @staticmethod
    def cargar_json():
        """Método para abrir un explorador de archivos y cargar un JSON externo."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo JSON",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        if not ruta:
            return None
        
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                cargado = json.load(archivo)
                if isinstance(cargado, list):
                    messagebox.showinfo("Éxito", "Datos cargados correctamente.")
                    return cargado
                else:
                    messagebox.showwarning("Advertencia", "El formato del JSON no es una lista válida.")
                    return None
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo JSON:\n{e}")
            return None