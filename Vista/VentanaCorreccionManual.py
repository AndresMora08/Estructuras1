import tkinter as tk
from tkinter import messagebox, ttk

from Logica.control_correcciones import ControladorCorrecciones
from Modelos.Epicentro import Epicentro
from Modelos.Evento import Evento
from Modelos.Asociaciones import recalcular_asociaciones_escenario


class VentanaCorreccionManual:

    def __init__(
        self,
        parent_window: tk.Toplevel,
        evento_viejo: Evento,
        arbol_avl,
        dict_eventos: dict,
        callback_refrescar,
        escenario=None,
    ):
        self.ventana = tk.Toplevel(parent_window)
        self.ventana.title(f"Corregir Evento SIS-{evento_viejo.id:06d}")
        self.ventana.geometry("380x350")
        self.ventana.resizable(False, False)
        self.ventana.grab_set()

        self.evento_viejo = evento_viejo
        self.callback_refrescar = callback_refrescar
        self.escenario = escenario

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

        ttk.Label(frame, text="Magnitud (Mw):").grid(
            row=0, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_magnitud = ttk.Entry(frame, width=15)
        self.entry_magnitud.insert(0, str(self.evento_viejo.magnitud))
        self.entry_magnitud.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(frame, text="Profundidad (km):").grid(
            row=1, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_profundidad = ttk.Entry(frame, width=15)
        self.entry_profundidad.insert(0, str(self.evento_viejo.profundidad))
        self.entry_profundidad.grid(row=1, column=1, padx=10, pady=8)

        val_x = self.evento_viejo.epicentro.x if self.evento_viejo.epicentro else 0.0
        val_y = self.evento_viejo.epicentro.y if self.evento_viejo.epicentro else 0.0

        ttk.Label(frame, text="Epicentro X:").grid(
            row=2, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_x = ttk.Entry(frame, width=15)
        self.entry_x.insert(0, str(val_x))
        self.entry_x.grid(row=2, column=1, padx=10, pady=8)

        ttk.Label(frame, text="Epicentro Y:").grid(
            row=3, column=0, sticky="w", padx=10, pady=8
        )
        self.entry_y = ttk.Entry(frame, width=15)
        self.entry_y.insert(0, str(val_y))
        self.entry_y.grid(row=3, column=1, padx=10, pady=8)

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

        esc = self.escenario

        # The new epicenter is classified against the scenario zones, so the
        # priority is derived from the NEW location (not the old zone).
        zonas = esc.zonas if esc is not None else None
        nuevo_epicentro = Epicentro(x=x, y=y, zonas_escenario=zonas)
        if not zonas:
            nuevo_epicentro.zona = (
                self.evento_viejo.epicentro.zona if self.evento_viejo.epicentro else None
            )

        evento_candidato = Evento(
            id_evento=self.evento_viejo.id,
            magnitud=mag,
            profundidad=prof,
            epicentro=nuevo_epicentro,
            estacion_origen=self.evento_viejo.estacion_origen,
            fecha_hora=self.evento_viejo.fecha_hora,
        )

        # The whole correction is ONE undoable action. The snapshot is taken
        # before touching anything; if it fails, the exact state is restored.
        if esc is not None:
            esc.guardar_estado_pila()

        try:
            exito = self.controlador.correccion_manual(
                evento_nuevo=evento_candidato, evento_viejo=self.evento_viejo
            )
            if exito and esc is not None:
                recalcular_asociaciones_escenario(esc, esc.W, esc.R)
        except Exception as error:
            if esc is not None:
                esc.deshacer_ultima_accion()
            messagebox.showerror(
                "Error en la corrección",
                f"No se aplicó ningún cambio (estado restaurado):\n{error}",
                parent=self.ventana,
            )
            self.ventana.destroy()
            self.callback_refrescar()
            return

        if exito:
            # Read the live event (case B replaces the object in dict_eventos)
            vivo = self.controlador.dict_eventos.get(self.evento_viejo.id, self.evento_viejo)
            messagebox.showinfo(
                "Corrección Exitosa",
                f"Evento SIS-{vivo.id:06d} actualizado a la revisión r{vivo.revision}.",
                parent=self.ventana,
            )
            self.callback_refrescar()
            self.ventana.destroy()
        else:
            if esc is not None:
                esc.descartar_ultimo_estado()
            messagebox.showerror(
                "Error de Validación",
                "Los datos ingresados no cumplen las reglas del sistema. No se aplicó ningún cambio.",
                parent=self.ventana,
            )