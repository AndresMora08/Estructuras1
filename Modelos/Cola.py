
class Cola:
    def __init__(self):
        self.items = []

    def esta_vacia(self) -> bool:
        return len(self.items) == 0

    def encolar(self, item):
        """Adds an element to the end of the queue (FIFO)."""
        self.items.append(item)

    def desencolar(self):
        """Removes and returns the first element from the queue."""
        if not self.esta_vacia():
            return self.items.pop(0)
        return None

    def tamano(self) -> int:
        return len(self.items)