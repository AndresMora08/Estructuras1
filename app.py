import sys
import os

# Aseguramos que la raíz del proyecto esté en el path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import copy
import json
import time
from flask import Flask, render_template, request, jsonify

# ==========================================
# IMPORTACIONES DE MODELOS
# ==========================================
from Modelos.Cola import Cola
from Modelos.BST import ArbolBST
from Modelos.AVL import AVL as ArbolAVL
from Modelos.Nodo import Nodo
from Modelos.Evento import Evento
from Modelos.Epicentro import Epicentro
from Modelos.Zona import Zona

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN PARA DESACTIVAR CACHÉ
# ==========================================
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    """
    Agrega encabezados a cada respuesta para evitar que el navegador o
    proxies guarden en caché el HTML, JS o respuestas JSON.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


# ==========================================
# MÓDULO PILA DE DESHACER
# ==========================================
class PilaDeshacer:
    def __init__(self, limite_versiones=20):
        self.pila = []
        self.limite = limite_versiones

    def guardar_estado(self, estado_actual):
        estado_copia = copy.deepcopy(estado_actual)
        self.pila.append(estado_copia)
        if len(self.pila) > self.limite:
            self.pila.pop(0)

    def deshacer(self):
        if not self.esta_vacia():
            return self.pila.pop()
        return None

    def esta_vacia(self):
        return len(self.pila) == 0

historial = PilaDeshacer()

# Estado global del sistema
estado_sistema = {
    "sismos": [],
    "cola_reportes": Cola()
}
ARCHIVO_JSON = "sismolab_backup.json"

# Instancia global del árbol AVL oficial del sistema para la vista gráfica
avl_global = ArbolAVL()


# ==========================================
# EXTENSIÓN PARA EL NODO AVL (SERIALIZACIÓN JSON)
# ==========================================
def nodo_to_dict(nodo_actual):
    if nodo_actual is None:
        return None
    
    evento = getattr(nodo_actual, 'evento', None)
    if evento:
        p = getattr(evento, 'prioridad', 0)
        m = getattr(evento, 'magnitud', 0.0)
        id_val = getattr(evento, 'id', 0)
        key_str = f"P:{p} M:{m} ID:{id_val}"
    else:
        key_str = "Nodo"

    return {
        "key": key_str,
        "left": nodo_to_dict(nodo_actual.izq) if hasattr(nodo_actual, 'izq') else None,
        "right": nodo_to_dict(nodo_actual.der) if hasattr(nodo_actual, 'der') else None
    }


# ==========================================
# RUTAS DE FLASK
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cargar_avl', methods=['POST'])
def cargar_avl():
    global estado_sistema, avl_global
    try:
        sismos = estado_sistema.get("sismos", [])
        return jsonify({
            "exito": True, 
            "mensaje": f"Se han cargado {len(sismos)} eventos al Árbol AVL.", 
            "sismos": sismos
        })
    except Exception as e:
        return jsonify({"exito": False, "mensaje": f"Error al cargar AVL: {str(e)}"})


@app.route('/procesar_reporte', methods=['POST'])
def procesar_reporte():
    try:
        cola = estado_sistema.get("cola_reportes")
        if cola and not cola.esta_vacia():
            reporte = cola.desencolar()
            return jsonify({"exito": True, "mensaje": f"Reporte procesado con éxito: {reporte}"})
        return jsonify({"exito": False, "mensaje": "La cola de reportes está vacía actualmente."})
    except Exception as e:
        return jsonify({"exito": False, "mensaje": f"Error al procesar reporte: {str(e)}"})


@app.route('/ver_todos', methods=['GET'])
def ver_todos():
    sismos = estado_sistema.get("sismos", [])
    return jsonify({
        "exito": True, 
        "mensaje": f"Mostrando todos los eventos ({len(sismos)} registrados).", 
        "sismos": sismos
    })


@app.route('/consultar_pendientes', methods=['GET'])
def consultar_pendientes():
    return jsonify({"exito": True, "mensaje": "Consulta de reportes pendientes ejecutada correctamente."})


@app.route('/buscar_rango', methods=['GET'])
def buscar_rango():
    min_val = request.args.get('min', 0, type=float)
    max_val = request.args.get('max', 10, type=float)
    sismos = estado_sistema.get("sismos", [])
    sismos_filtrados = [s for s in sismos if min_val <= s.get('magnitud', 0) <= max_val]
    return jsonify({
        "exito": True, 
        "mensaje": f"Se encontraron {len(sismos_filtrados)} sismos en el rango de magnitud [{min_val} - {max_val}].",
        "sismos": sismos_filtrados
    })


@app.route('/cargar_bst', methods=['POST'])
def cargar_bst():
    return jsonify({"exito": True, "mensaje": "Datos cargados al Árbol BST para pruebas de rendimiento."})


@app.route('/deshacer', methods=['POST'])
def deshacer_accion():
    global estado_sistema
    estado_anterior = historial.deshacer()
    
    if estado_anterior is not None:
        estado_sistema = estado_anterior
        return jsonify({
            "mensaje": "Se ha deshecho la última acción correctamente.", 
            "exito": True,
            "sismos": estado_sistema["sismos"]
        })
    else:
        return jsonify({
            "mensaje": "La pila está vacía. No hay acciones para deshacer.", 
            "exito": False
        })


@app.route('/guardar_json', methods=['GET'])
def guardar_json():
    try:
        datos_a_guardar = {"sismos": estado_sistema["sismos"]}
        with open(ARCHIVO_JSON, 'w') as f:
            json.dump(datos_a_guardar, f, indent=4)
        return jsonify({"mensaje": "Estado del sistema guardado en sismolab_backup.json", "exito": True})
    except Exception as e:
        return jsonify({"mensaje": f"Error al guardar: {str(e)}", "exito": False})


@app.route('/cargar_json', methods=['POST'])
def cargar_json():
    global estado_sistema
    try:
        if not os.path.exists(ARCHIVO_JSON):
            return jsonify({"mensaje": "No se encontró el archivo de respaldo JSON.", "exito": False})
            
        with open(ARCHIVO_JSON, 'r') as f:
            estado_cargado = json.load(f)
        
        historial.guardar_estado(estado_sistema)
        estado_sistema["sismos"] = estado_cargado.get("sismos", [])
        
        return jsonify({
            "mensaje": "Estado cargado desde JSON exitosamente.", 
            "exito": True,
            "sismos": estado_sistema["sismos"]
        })
    except Exception as e:
        return jsonify({"mensaje": f"Error al cargar JSON: {str(e)}", "exito": False})


@app.route('/insertar_sismo', methods=['POST'])
def insertar_sismo():
    global estado_sistema, avl_global
    historial.guardar_estado(estado_sistema)
    
    datos = request.json
    nuevo_sismo = {
        "id": datos.get("id", len(estado_sistema["sismos"]) + 1),
        "x": datos.get("x", 0), 
        "y": datos.get("y", 0), 
        "magnitud": float(datos.get("magnitud", 1.0)),
        "profundidad": float(datos.get("profundidad", 10.0)),
        "fecha_hora": datos.get("fecha_hora", "2026-09-19 00:00:00")
    }
    estado_sistema["sismos"].append(nuevo_sismo)
    
    # Insertamos también en el árbol AVL global
    try:
        zona_dummy = Zona(nombre="Zona Central", x_min=0, x_max=1000, y_min=0, y_max=1000, poblada=True)
        epicentro_dummy = Epicentro(x=nuevo_sismo['x'], y=nuevo_sismo['y'], zonas_escenario=[zona_dummy])
        evento = Evento(
            id=nuevo_sismo['id'],
            magnitud=nuevo_sismo['magnitud'],
            profundidad=nuevo_sismo['profundidad'],
            epicentro=epicentro_dummy,
            fecha_hora=nuevo_sismo['fecha_hora']
        )
        if hasattr(evento, 'calcular_prioridad'):
            evento.calcular_prioridad()
        
        nodo_avl = Nodo(evento)
        avl_global.insertar(nodo_avl)
    except Exception as ex:
        print(f"Aviso al insertar en AVL: {ex}")
    
    return jsonify({
        "mensaje": "Sismo insertado correctamente.", 
        "exito": True, 
        "sismos": estado_sistema["sismos"]
    })


@app.route('/api/arbol-avl', methods=['GET'])
def obtener_arbol_avl():
    raiz_avl = getattr(avl_global, 'raiz', getattr(avl_global, 'root', None))
    if not raiz_avl:
        return jsonify(None)
    return jsonify(nodo_to_dict(raiz_avl))


@app.route('/comparar_rendimiento', methods=['GET'])
def comparar_rendimiento():
    global estado_sistema
    sismos = estado_sistema.get("sismos", [])
    
    if len(sismos) == 0:
        return jsonify({"exito": False, "mensaje": "No hay sismos registrados para comparar. Simula algunos primero."})

    bst_prueba = ArbolBST()
    avl_prueba = ArbolAVL()

    eventos_prueba = []
    for i, s_data in enumerate(sismos):
        zona_dummy = Zona(nombre="Zona Central", x_min=0, x_max=1000, y_min=0, y_max=1000, poblada=True)
        epicentro_dummy = Epicentro(x=s_data.get('x', 0), y=s_data.get('y', 0), zonas_escenario=[zona_dummy])
        
        evento = Evento(
            id=s_data.get('id', i + 1),
            magnitud=s_data.get('magnitud', 3.0),
            profundidad=s_data.get('profundidad', 10.0),
            epicentro=epicentro_dummy,
            fecha_hora=s_data.get('fecha_hora', "2026-09-19 00:00:00")
        )
        if hasattr(evento, 'calcular_prioridad'):
            evento.calcular_prioridad()
        eventos_prueba.append(evento)

    # Medición BST
    inicio_bst = time.perf_counter()
    for evento in eventos_prueba:
        nodo_bst = Nodo(evento)
        bst_prueba.insertar(nodo_bst)
    fin_bst = time.perf_counter()
    tiempo_bst = (fin_bst - inicio_bst) * 1000 

    # Medición AVL
    inicio_avl = time.perf_counter()
    for evento in eventos_prueba:
        nodo_avl = Nodo(evento)
        avl_prueba.insertar(nodo_avl)
    fin_avl = time.perf_counter()
    tiempo_avl = (fin_avl - inicio_avl) * 1000

    # Texto con saltos de línea legibles para la consola de JS (sin usar etiquetas HTML crudas)
    mensaje = f"⏱️ Rendimiento con {len(sismos)} sismos:\n- Tiempo BST: {tiempo_bst:.4f} ms\n- Tiempo AVL: {tiempo_avl:.4f} ms"
    
    return jsonify({"exito": True, "mensaje": mensaje})


if __name__ == '__main__':
    app.run(debug=True)