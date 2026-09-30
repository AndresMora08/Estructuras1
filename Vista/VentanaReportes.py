import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from Modelos.Escenario import Escenario
from Modelos.Evento import Evento
from Logica.control_reportes import ControladorReportes


class VentanaReportes(tk.Toplevel):
    """Window to prepare, queue (FIFO) and process seismic reports."""

    INTERVALO_CONTINUO_MS = 1000
    ETIQUETA_NUEVO = "[Nuevo Evento Manual]"

    def __init__(self, parent, escenario: Escenario):
        super().__init__(parent)

        self.title("SismoLab - Gestión y Procesamiento de Reportes Sísmicos")
        self.geometry("1250x820")

        self.escenario = escenario
        self.controlador = ControladorReportes(escenario)

        self.mapa_eventos: Dict[str, Optional[Evento]] = {}
        self.mapa_estaciones: Dict[str, object] = {}

        self.var_modo_estres = tk.BooleanVar(value=self.controlador.modo_estres_activo())
        self.ejecutando_continuo = False
        self.timer_id: Optional[str] = None

        self._crear_interfaz()
        self._cargar_eventos_combo()
        self._cargar_estaciones()
        self._limpiar_formulario()
        self._actualizar_tabla_cola()
        self._actualizar_estado_arbol()
        self._actualizar_metricas()

        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ------------------------------------------------------------------
    # INTERFACE
    # ------------------------------------------------------------------

    def _crear_interfaz(self):
        # 1. Operation mode and AVL state
        f_top = ttk.LabelFrame(self, text=" Modo de Operación y Estado AVL ", padding=10)
        f_top.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(
            f_top,
            text="Modo Estrés (aplazar rotaciones AVL)",
            variable=self.var_modo_estres,
            command=self._on_toggle_modo_estres,
        ).pack(side=tk.LEFT, padx=10)

        self.lbl_estado_arbol = ttk.Label(f_top, text="", font=("Arial", 10, "bold"))
        self.lbl_estado_arbol.pack(side=tk.LEFT, padx=20)

        ttk.Button(
            f_top, text="Recuperación Global (rebalancear AVL)", command=self._ejecutar_recuperacion_global
        ).pack(side=tk.RIGHT, padx=5)
        ttk.Button(f_top, text="Verificar estructura", command=self._verificar_estructura).pack(
            side=tk.RIGHT, padx=5
        )
        self.lbl_reloj = ttk.Label(f_top, text="", font=("Arial", 9, "bold"))
        self.lbl_reloj.pack(side=tk.RIGHT, padx=(5, 15))
        ttk.Button(f_top, text="Avanzar reloj", command=self._avanzar_reloj).pack(side=tk.RIGHT, padx=2)
        self.ent_horas_reloj = ttk.Entry(f_top, width=5)
        self.ent_horas_reloj.insert(0, "1")
        self.ent_horas_reloj.pack(side=tk.RIGHT, padx=2)
        ttk.Label(f_top, text="Horas:").pack(side=tk.RIGHT)

        # 2. Report preparation form
        f_form = ttk.LabelFrame(self, text=" Preparar y Validar Reporte ", padding=10)
        f_form.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(f_form, text="Cargar desde evento:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.combo_evento_base = ttk.Combobox(f_form, state="readonly", width=38)
        self.combo_evento_base.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=2)
        self.combo_evento_base.bind("<<ComboboxSelected>>", self._on_evento_base_selected)

        ttk.Label(f_form, text="ID Evento:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_id = ttk.Entry(f_form, width=12)
        self.ent_id.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(f_form, text="Revisión (r):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.ent_rev = ttk.Entry(f_form, width=8)
        self.ent_rev.grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(f_form, text="Estaciones emisoras (una o varias):").grid(
            row=0, column=4, sticky=tk.W, padx=15, pady=2
        )
        self.lista_estaciones = tk.Listbox(
            f_form, selectmode=tk.EXTENDED, height=4, exportselection=False, width=22
        )
        self.lista_estaciones.grid(row=1, column=4, rowspan=3, sticky=tk.W, padx=15, pady=2)

        ttk.Label(f_form, text="Magnitud:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_mag = ttk.Entry(f_form, width=12)
        self.ent_mag.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(f_form, text="Profundidad (km):").grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        self.ent_prof = ttk.Entry(f_form, width=8)
        self.ent_prof.grid(row=2, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(f_form, text="Epicentro X:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_x = ttk.Entry(f_form, width=12)
        self.ent_x.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(f_form, text="Epicentro Y:").grid(row=3, column=2, sticky=tk.W, padx=5, pady=2)
        self.ent_y = ttk.Entry(f_form, width=8)
        self.ent_y.grid(row=3, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(f_form, text="Fecha/Hora (ISO UTC):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.ent_fecha = ttk.Entry(f_form, width=24)
        self.ent_fecha.grid(row=4, column=1, columnspan=2, sticky=tk.W, padx=5, pady=2)

        f_botones_form = ttk.Frame(f_form)
        f_botones_form.grid(row=4, column=3, columnspan=3, sticky=tk.E, padx=5, pady=5)
        ttk.Button(f_botones_form, text="Cargar ráfaga de ejemplo", command=self._cargar_rafaga_ejemplo).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(f_botones_form, text="Validar y Encolar Reporte", command=self._encolar_reporte_manual).pack(
            side=tk.LEFT, padx=5
        )

        # 3. FIFO queue and log
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        f_cola = ttk.LabelFrame(paned, text=" Cola FIFO de Recepción (el #1 sale primero) ", padding=5)
        paned.add(f_cola, weight=1)

        columnas = ("pos", "id", "rev", "estacion", "mag", "prof")
        self.tree_cola = ttk.Treeview(f_cola, columns=columnas, show="headings", height=12)
        encabezados = {"pos": "#", "id": "ID Evento", "rev": "Rev.", "estacion": "Estación", "mag": "Mag.", "prof": "Prof."}
        anchos = {"pos": 30, "id": 90, "rev": 45, "estacion": 80, "mag": 50, "prof": 50}
        for col in columnas:
            self.tree_cola.heading(col, text=encabezados[col])
            self.tree_cola.column(col, width=anchos[col], anchor=tk.CENTER)

        sb_cola = ttk.Scrollbar(f_cola, orient=tk.VERTICAL, command=self.tree_cola.yview)
        self.tree_cola.configure(yscrollcommand=sb_cola.set)

        f_controles = ttk.Frame(f_cola)
        f_controles.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        self.btn_paso = ttk.Button(f_controles, text="Procesar 1 Paso", command=self._procesar_un_paso)
        self.btn_paso.pack(side=tk.LEFT, padx=2)
        self.btn_continuo = ttk.Button(f_controles, text="Procesar Continuo", command=self._iniciar_continuo)
        self.btn_continuo.pack(side=tk.LEFT, padx=2)
        self.btn_pausa = ttk.Button(f_controles, text="Pausar", state=tk.DISABLED, command=self._pausar_continuo)
        self.btn_pausa.pack(side=tk.LEFT, padx=2)

        self.tree_cola.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_cola.pack(side=tk.RIGHT, fill=tk.Y)

        f_log = ttk.LabelFrame(paned, text=" Bitácora de Procesamiento ", padding=5)
        paned.add(f_log, weight=2)

        self.txt_log = tk.Text(f_log, wrap=tk.WORD, font=("Consolas", 9))
        sb_log = ttk.Scrollbar(f_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=sb_log.set)
        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_log.pack(side=tk.RIGHT, fill=tk.Y)

        # 4. Counters
        self.lbl_metricas = ttk.Label(self, text="", font=("Arial", 9))
        self.lbl_metricas.pack(fill=tk.X, padx=10, pady=(0, 8))

    # ------------------------------------------------------------------
    # LOADING / SELECTION
    # ------------------------------------------------------------------

    def _cargar_eventos_combo(self):
        seleccion_previa = self.combo_evento_base.get()
        self.mapa_eventos.clear()
        self.mapa_eventos[self.ETIQUETA_NUEVO] = None

        for evento in self.escenario.dict_eventos.values():
            self.mapa_eventos[f"[ACTIVO] SIS-{evento.id:06d}"] = evento
        for evento in self.escenario.historico:
            etiqueta = evento.estado_catalogo.upper()  # ARCHIVADO or RETIRADO
            self.mapa_eventos[f"[{etiqueta}] SIS-{evento.id:06d}"] = evento

        etiquetas = list(self.mapa_eventos.keys())
        self.combo_evento_base["values"] = etiquetas
        if seleccion_previa in self.mapa_eventos:
            self.combo_evento_base.set(seleccion_previa)
        else:
            self.combo_evento_base.current(0)

    def _cargar_estaciones(self):
        self.mapa_estaciones.clear()
        self.lista_estaciones.delete(0, tk.END)
        for estacion in self.escenario.estaciones:
            id_estacion = str(getattr(estacion, "id_estacion", estacion))
            self.mapa_estaciones[id_estacion] = estacion
            self.lista_estaciones.insert(tk.END, id_estacion)
        if self.mapa_estaciones:
            self.lista_estaciones.selection_set(0)

    def _reemplazar_texto(self, entrada: ttk.Entry, valor):
        entrada.delete(0, tk.END)
        entrada.insert(0, str(valor))

    def _limpiar_formulario(self):
        for entrada in (self.ent_id, self.ent_mag, self.ent_prof, self.ent_x, self.ent_y):
            entrada.delete(0, tk.END)
        self._reemplazar_texto(self.ent_rev, 1)
        self._reemplazar_texto(self.ent_fecha, self.controlador.obtener_reloj_texto())
        self._actualizar_reloj()

    def _on_evento_base_selected(self, event=None):
        evento = self.mapa_eventos.get(self.combo_evento_base.get())
        if evento is None:
            self._limpiar_formulario()
            return

        self._reemplazar_texto(self.ent_id, evento.id)
        self._reemplazar_texto(self.ent_rev, evento.revision + 1)  # suggested next revision
        self._reemplazar_texto(self.ent_mag, evento.magnitud)
        self._reemplazar_texto(self.ent_prof, evento.profundidad)
        self._reemplazar_texto(self.ent_fecha, evento.fecha_hora)
        self._reemplazar_texto(self.ent_x, evento.epicentro.x if evento.epicentro else 0.0)
        self._reemplazar_texto(self.ent_y, evento.epicentro.y if evento.epicentro else 0.0)

    # ------------------------------------------------------------------
    # ENQUEUE
    # ------------------------------------------------------------------

    def _encolar_reporte_manual(self):
        try:
            id_evento = int(self.ent_id.get())
            revision = int(self.ent_rev.get())
            magnitud = float(self.ent_mag.get())
            profundidad = float(self.ent_prof.get())
            x = float(self.ent_x.get())
            y = float(self.ent_y.get())
        except ValueError as error:
            messagebox.showerror("Error de formato", f"Ingrese números válidos: {error}")
            return
        fecha_texto = self.ent_fecha.get().strip()

        indices = self.lista_estaciones.curselection()
        if not self.mapa_estaciones or not indices:
            messagebox.showwarning("Estación requerida", "Seleccione al menos una estación emisora.")
            return

        # Build every report first so the burst is all-or-nothing
        preparados = []
        for indice in indices:
            id_estacion = self.lista_estaciones.get(indice)
            estacion = self.mapa_estaciones[id_estacion]
            valido, mensaje, evento = self.controlador.crear_evento_reportado(
                id_evento, magnitud, profundidad, x, y, fecha_texto, estacion, revision
            )
            if not valido:
                messagebox.showerror("Reporte rechazado", f"Datos no válidos: {mensaje}")
                return
            preparados.append((evento, estacion, id_estacion))

        for evento, estacion, id_estacion in preparados:
            exito, mensaje = self.controlador.encolar_reporte(evento, estacion, revision)
            if exito:
                self._log(f"[ENCOLADO] SIS-{id_evento:06d} (r{revision}) desde {id_estacion}.")
            else:
                messagebox.showerror("Reporte rechazado", mensaje)
                break
        self._actualizar_tabla_cola()

    def _cargar_rafaga_ejemplo(self):
        exito, mensaje = self.controlador.generar_rafaga_demostracion()
        if exito:
            self._log(f"[RÁFAGA] {mensaje}")
            self._actualizar_tabla_cola()
        else:
            messagebox.showwarning("Ráfaga de ejemplo", mensaje)

    # ------------------------------------------------------------------
    # PROCESSING
    # ------------------------------------------------------------------

    def _procesar_un_paso(self) -> bool:
        """Processes one report. Returns True when the loop may continue."""
        resultado = self.controlador.procesar_siguiente_reporte()

        if resultado is None:
            self._log("--- La cola de reportes se encuentra vacía. ---")
            self._pausar_continuo()
            return False

        self._actualizar_tabla_cola()
        self._cargar_eventos_combo()
        self._actualizar_estado_arbol()
        self._actualizar_metricas()

        rot = resultado.get("rotaciones", {})
        texto_rotaciones = (
            f"LL={rot.get('LL', 0)} RR={rot.get('RR', 0)} LR={rot.get('LR', 0)} "
            f"RL={rot.get('RL', 0)} (giros simples: {rot.get('giros_simples', 0)})"
        )
        lineas = [
            "--------------------------------------------------",
            f" RESULTADO  : {resultado['resultado']}",
            f" EVENTO     : SIS-{resultado['id_evento']:06d} (r{resultado['revision']})",
            f" ESTACIÓN   : {resultado['estacion']}",
            f" DETALLE    : {resultado['detalle']}",
            f" ROTACIONES : {texto_rotaciones}",
            "--------------------------------------------------",
        ]
        self._log("\n".join(lineas))

        if resultado["resultado"] == "ERROR":
            self._pausar_continuo()
            messagebox.showerror("Error de procesamiento", resultado["detalle"])
            return False
        return True

    def _iniciar_continuo(self):
        if not self.escenario.cola_reportes:
            messagebox.showinfo("Cola vacía", "No hay reportes pendientes.")
            return
        self.ejecutando_continuo = True
        self.btn_continuo.config(state=tk.DISABLED)
        self.btn_paso.config(state=tk.DISABLED)
        self.btn_pausa.config(state=tk.NORMAL)
        self._bucle_continuo()

    def _bucle_continuo(self):
        if not self.ejecutando_continuo:
            return
        if self._procesar_un_paso() and self.ejecutando_continuo:
            self.timer_id = self.after(self.INTERVALO_CONTINUO_MS, self._bucle_continuo)

    def _pausar_continuo(self):
        self.ejecutando_continuo = False
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.btn_continuo.config(state=tk.NORMAL)
        self.btn_paso.config(state=tk.NORMAL)
        self.btn_pausa.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # STRESS MODE, AUDIT, RECOVERY
    # ------------------------------------------------------------------

    def _on_toggle_modo_estres(self):
        if not self.var_modo_estres.get():
            # Leaving stress mode is only allowed if the audit confirms the balance
            permitido, auditoria = self.controlador.puede_volver_a_modo_normal()
            if not permitido:
                self.var_modo_estres.set(True)
                messagebox.showwarning(
                    "No se puede volver al modo normal",
                    f"La auditoría detectó {len(auditoria['desbalanceados'])} nodos desbalanceados "
                    f"y {len(auditoria['errores_orden'])} errores de orden.\n"
                    "Ejecute la Recuperación Global primero.",
                )
                self._log(">>> Retorno a modo normal RECHAZADO: el árbol aún no está balanceado.")
                return

        self.controlador.establecer_modo_estres(self.var_modo_estres.get())
        estado = "ACTIVADO" if self.var_modo_estres.get() else "DESACTIVADO"
        self._log(f">>> Modo estrés {estado}.")
        self._actualizar_estado_arbol()

    def _ejecutar_recuperacion_global(self):
        self._pausar_continuo()  # global recovery pauses the report processing
        try:
            resultado = self.controlador.recuperar_equilibrio_global()
        except Exception as error:
            messagebox.showerror("Recuperación global", f"No se pudo recuperar el equilibrio: {error}")
            return

        previa = resultado["auditoria_previa"]
        final = resultado["auditoria_final"]
        rot = resultado["rotaciones"]
        max_dif = max((abs(f) for _, f in previa["desbalanceados"]), default=0)
        lineas = [
            "==================================================",
            " RECUPERACIÓN GLOBAL",
            f" Nodos desbalanceados antes : {len(previa['desbalanceados'])} (mayor |factor| = {max_dif})",
            f" Altura antes -> después    : {previa['altura']} -> {final['altura']}",
            f" Rotaciones aplicadas       : LL={rot.get('LL', 0)} RR={rot.get('RR', 0)} "
            f"LR={rot.get('LR', 0)} RL={rot.get('RL', 0)} (giros simples: {rot.get('giros_simples', 0)})",
            f" Auditoría                  : {'EQUILIBRIO CONFIRMADO' if resultado['confirmado'] else 'FALLÓ'}",
            "==================================================",
        ]
        self._log("\n".join(lineas))

        self.var_modo_estres.set(self.controlador.modo_estres_activo())
        self._actualizar_estado_arbol()

    def _verificar_estructura(self):
        auditoria = self.controlador.auditar_arbol()
        lineas = [
            "--------------------- AUDITORÍA ---------------------",
            f" Nodos: {auditoria['total_nodos']} | Altura: {auditoria['altura']}",
            f" Orden BST global: {'OK' if auditoria['orden_ok'] else 'ERRORES'}",
            f" Metadatos (alturas/unicidad): {'OK' if auditoria['metadatos_ok'] else 'ERRORES'}",
            f" Balance AVL: {'OK' if auditoria['balanceado'] else 'DESBALANCEADO'}",
        ]
        for id_evento, factor in auditoria["desbalanceados"]:
            lineas.append(f"   - SIS-{id_evento:06d}: factor de balance {factor}")
        for error in auditoria["errores_orden"] + auditoria["errores_metadatos"]:
            lineas.append(f"   ! {error}")
        lineas.append("-----------------------------------------------------")
        self._log("\n".join(lineas))

    def _actualizar_estado_arbol(self):
        auditoria = self.controlador.auditar_arbol()
        if self.controlador.modo_estres_activo():
            if auditoria["balanceado"]:
                texto, color = "MODO ESTRÉS (el árbol aún cumple AVL)", "orange"
            else:
                texto = f"MODO ESTRÉS: ÁRBOL DESBALANCEADO ({len(auditoria['desbalanceados'])} nodos)"
                color = "red"
        else:
            texto, color = "NORMAL (AVL balanceado)", "green"
        self.lbl_estado_arbol.config(text=f"Estado Árbol: {texto}", foreground=color)

    # ------------------------------------------------------------------
    # TABLES / LOG / COUNTERS
    # ------------------------------------------------------------------

    def _actualizar_tabla_cola(self):
        for item in self.tree_cola.get_children():
            self.tree_cola.delete(item)

        for posicion, reporte in enumerate(self.escenario.cola_reportes, start=1):
            id_estacion = getattr(reporte.estacion_emisora, "id_estacion", str(reporte.estacion_emisora))
            evento = reporte.evento
            self.tree_cola.insert(
                "",
                tk.END,
                values=(
                    posicion,
                    f"SIS-{evento.id:06d}",
                    f"r{reporte.revision}",
                    id_estacion,
                    evento.magnitud,
                    evento.profundidad,
                ),
            )

    def _actualizar_metricas(self):
        m = self.controlador.metricas
        self.lbl_metricas.config(
            text=(
                f"Nuevos: {m['nuevos']} | Correcciones aceptadas: {m['correcciones_aceptadas']} | "
                f"Reactivados: {m['reactivados']} | Confirmaciones: {m['confirmaciones']} | "
                f"Conflictos: {m['conflictos']} | Descartados (antiguos): {m['descartados_antiguos']} | "
                f"Rechazados (retirados): {m['rechazados_retirados']} | "
                f"En cola: {len(self.escenario.cola_reportes)}"
            )
        )

    def _actualizar_reloj(self):
        self.lbl_reloj.config(text=f"Reloj: {self.controlador.obtener_reloj_texto()}")

    def _avanzar_reloj(self):
        try:
            horas = float(self.ent_horas_reloj.get())
        except ValueError:
            messagebox.showerror("Error de formato", "Ingrese un número de horas válido.")
            return
        exito, mensaje = self.controlador.avanzar_reloj(horas)
        if exito:
            self._actualizar_reloj()
            self._log(f"[RELOJ] {mensaje}")
        else:
            messagebox.showerror("Reloj", mensaje)

    def _log(self, mensaje: str):
        self.txt_log.insert(tk.END, mensaje + "\n")
        self.txt_log.see(tk.END)

    def _al_cerrar(self):
        self._pausar_continuo()
        self.destroy()