import tkinter as tk
from tkinter import messagebox, ttk

from Logica.control_correcciones import ControladorCorrecciones
from Modelos.Epicentro import Epicentro
from Modelos.Evento import Evento


class VentanaCorreccionManual:

    def __init__(
        self,
        parent_window: tk.Toplevel,
        evento_viejo: Evento,
        arbol_avl,
        dict_eventos: dict,
        callback_refrescar,
        escenario=None,  # <-- ACEPTAR ESCENARIO
    ):
        self.ventana = tk.Toplevel(parent_window)
        self.ventana.title(f"Corregir Evento SIS-{evento_viejo.id:06d}")
        self.ventana.geometry("380x350")
        self.ventana.resizable(False, False)
        self.ventana.grab_set()

        self.evento_viejo = evento_viejo
        self.callback_refrescar = callback_refrescar
        
        # PASAR EL ESCENARIO AL CONTROLADOR
        self.controlador = ControladorCorrecciones(
            arbol_avl=arbol_avl, 
            dict_eventos=dict_eventos,
            escenario=escenario
        )

        self._crear_formulario()

    def _crear_formulario(self):
        frame = ttk.LabelFrame(
            self.ventana,
            text=f" Formulario de Corrección (Rev. Actual: r{self.evento_viejo.revision}) ",
        )
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 1. Magnitud
        ttk.Label(frame, text="Magnitud (Mw):").grid(
            row=0, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_magnitud = ttk.Entry(frame, width=15)
        self.entry_magnitud.insert(0, str(self.evento_viejo.magnitud))
        self.entry_magnitud.grid(row=0, column=1, padx=10, pady=8)

        # 2. Profundidad
        ttk.Label(frame, text="Profundidad (km):").grid(
            row=1, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_profundidad = ttk.Entry(frame, width=15)
        self.entry_profundidad.insert(0, str(self.evento_viejo.profundidad))
        self.entry_profundidad.grid(row=1, column=1, padx=10, pady=8)

        # Coordenadas actuales
        val_x = self.evento_viejo.epicentro.x if self.evento_viejo.epicentro else 0.0
        val_y = self.evento_viejo.epicentro.y if self.evento_viejo.epicentro else 0.0

        # 3. Epicentro X
        ttk.Label(frame, text="Epicentro X:").grid(
            row=2, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_x = ttk.Entry(frame, width=15)
        self.entry_x.insert(0, str(val_x))
        self.entry_x.grid(row=2, column=1, padx=10, pady=8)

        # 4. Epicentro Y
        ttk.Label(frame, text="Epicentro Y:").grid(
            row=3, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_y = ttk.Entry(frame, width=15)
        self.entry_y.insert(0, str(val_y))
        self.entry_y.grid(row=3, column=1, padx=10, pady=8)

        # Botón Guardar
        btn_guardar = ttk.Button(
            frame, text="Guardar Corrección", command=self._procesar_guardado
        )
        btn_guardar.grid(row=4, column=0, columnspan=2, pady=15)

    def _procesar_guardado(self):
        try:
            mag = float(self.entry_magnitud.get().strip())
            prof = float(self.entry_profundidad.get().strip())
            x = float(self.entry_x.get().strip())
            y = float(self.entry_y.get().strip())
        except ValueError:
            messagebox.showerror(
                "Error de Entrada",
                "Todos los campos deben ser números válidos.",
                parent=self.ventana,
            )
            return

        zona_existente = (
            self.evento_viejo.epicentro.zona if self.evento_viejo.epicentro else None
        )
        nuevo_epicentro = Epicentro(x=x, y=y)
        nuevo_epicentro.zona = zona_existente

        evento_candidato = Evento(
            id_evento=self.evento_viejo.id,
            magnitud=mag,
            profundidad=prof,
            epicentro=nuevo_epicentro,
            estacion_origen=self.evento_viejo.estacion_origen,
            fecha_hora=self.evento_viejo.fecha_hora,
        )

        exito = self.controlador.correccion_manual(
            evento_nuevo=evento_candidato, evento_viejo=self.evento_viejo
        )

        if exito:
            messagebox.showinfo(
                "Corrección Exitosa",
                f"Evento SIS-{self.evento_viejo.id:06d} actualizado a la revisión"
                f" r{self.evento_viejo.revision}.",
                parent=self.ventana,
            )
            self.callback_refrescar()
            self.ventana.destroy()
        else:
            messagebox.showerror(
                "Error de Validación",
                "Los datos ingresados no cumplen las reglas del sistema. No se aplicó ningún cambio.",
                parent=self.ventana,
            )