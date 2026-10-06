# SismoLab — Manual de Introducción y Guía de Uso

SismoLab es una aplicación diseñada para registrar, administrar y analizar datos de eventos sísmicos de manera organizada. Para garantizar que la información se guarde de forma eficiente y que las búsquedas sean rápidas incluso con grandes volúmenes de datos, la plataforma combina dos tipos de estructuras: **Árboles de Búsqueda Binaria (BST)** y **Árboles Auto-balanceados (AVL)**.

Además de organizar la información en memoria, el programa cuenta con una interfaz visual que permite monitorear ubicaciones geográficas en mapas, revisar estaciones de control, procesar reportes entrantes en tiempo real y deshacer cambios o restaurar la información a un punto anterior sin complicaciones.

---

## Qué puedes hacer con el programa

* **Organización eficiente de datos:** El sistema organiza los sismos mediante algoritmos AVL en modo normal para mantener la información siempre ordenada, aunque también cuenta con un modo de estrés para manejar estructuras complejas o cargadas hacia un solo lado.
* **Seguridad al cargar archivos:** Antes de aplicar cualquier cambio, el sistema verifica que los archivos de topología en formato JSON no estén dañados ni tengan datos incoherentes. Si detecta un error, rechaza la lectura y mantiene intacto el estado en el que estabas trabajando.
* **Interfaz clara y funcional:** Incluye paneles para ver zonas y epicentros, gestionar colas de procesamiento de reportes y aplicar acciones de retroceso (undo) si cometes algún error durante la sesión.

---

## Requisitos básicos

Para poder ejecutar el proyecto en tu equipo necesitas:

* Python versión 3.10 o superior.
* Un editor de código como Visual Studio Code, PyCharm o el IDE de tu preferencia.

---

## Estructura de las carpetas

Dentro del proyecto encontrarás las siguientes carpetas principales:

* **Logica:** Módulos encargados del procesamiento de datos, validación de estructuras y reglas del árbol.
* **Modelos:** Definición de los objetos del sistema (eventos, estaciones, nodos, entre otros).
* **Vista:** Componentes gráficos que forman la interfaz de usuario.
* **main_gui.py:** Archivo ejecutable principal situado en la raíz del proyecto.

---

## Pasos para ejecutar el proyecto

1. **Abrir la carpeta del proyecto:** Descarga o descomprime el proyecto y abre la carpeta raíz desde tu editor de código.
2. **Ubicarse en el archivo principal:** En el explorador de archivos del editor, busca y abre el archivo `main_gui.py` (asegúrate de que esté en la raíz, fuera de las subcarpetas `Logica`, `Modelos` y `Vista`).
3. **Iniciar la aplicación:**
   * Si usas un IDE como Visual Studio Code, haz clic en el botón de ejecución (**Run** o **Play**) ubicado en la esquina superior derecha de la ventana.
   * Si prefieres usar la terminal, abre una consola dentro de la carpeta del proyecto y ejecuta el comando:
     ```bash
     python main_gui.py
     ```