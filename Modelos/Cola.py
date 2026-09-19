class Cola:
    def __init__(self):
        self.items = []

    def esta_vacia(self) -> bool:
        return len(self.items) == 0

    def encolar(self, item):
        """Agrega un elemento al final de la cola (FIFO)."""
        self.items.append(item)

    def desencolar(self):
        """Saca y retorna el primer elemento de la cola."""
        if not self.esta_vacia():
            return self.items.pop(0)
        return None

    def tamano(self) -> int:
        return len(self.items)