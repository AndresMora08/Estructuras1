# modelo.py

class GestorDatos:
    def __init__(self):
        
        self.datos = [
            {"id": 1, "zona": "Manizales", "magnitud": 4.5, "epicentro": "Centro"},
            {"id": 2, "zona": "Villamaría", "magnitud": 3.2, "epicentro": "Rural"}
        ]

    def obtener_datos(self):
        return self.datos

    def establecer_datos(self, nuevos_datos):
        if isinstance(nuevos_datos, list):
            self.datos = nuevos_datos
            return True
        return False

    def eliminar_por_id(self, id_a_eliminar):
        """Filtra la lista eliminando el elemento que coincida con el ID."""
        self.datos = [item for item in self.datos if str(item.get("id")) != str(id_a_eliminar)]