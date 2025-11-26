# -*- coding: utf-8 -*-
"""Interfaz gráfica simple basada en tkinter para visualizar el ecosistema.
Esta implementación es ligera y no introduce dependencias externas (usa tkinter incluido en la distribución estándar).
La clase InterfazGrafica expone métodos: start(ecosistema), stop(), update().
"""

try:
    import tkinter as tk
except Exception:
    tk = None

import threading
import time

class InterfazGrafica:
    def __init__(self, width=960, height=720, scale_w=0.75):
        if tk is None:
            raise RuntimeError("tkinter no está disponible en este entorno")
        self.root = tk.Tk()
        self.root.title("Simulador de Ecosistema - Visual")
        self.width = width
        self.height = height
        self.canvas_width = int(width * scale_w)
        self.canvas_height = int(height * scale_w)
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height, bg='black')
        self.canvas.pack()
        self._running = False
        self._ecosistema = None
        # mapping from entity name to canvas id
        self._items = {}
        # basic legend
        self.legend = tk.Frame(self.root)
        self.legend.pack(fill='x')
        tk.Label(self.legend, text='C: Carnívoro  H: Herbívoro  O: Omnívoro  P: Planta', fg='white', bg='black').pack()

    def start(self, ecosistema, update_interval=0.5):
        """Comienza el loop de actualización en un hilo. La ventana corre en el hilo principal de tkinter."""
        self._ecosistema = ecosistema
        self._update_interval = update_interval
        self._running = True
        # ejecutar loop de actualización en hilo
        self._thread = threading.Thread(target=self._loop_update, daemon=True)
        self._thread.start()
        # arrancar mainloop (bloqueante)
        try:
            self.root.mainloop()
        finally:
            self._running = False

    def stop(self):
        self._running = False
        try:
            self.root.quit()
        except Exception:
            pass

    def _loop_update(self):
        while self._running:
            try:
                self.update()
            except Exception:
                pass
            time.sleep(self._update_interval)

    def update(self):
        """Renderiza el estado actual del ecosistema en el canvas."""
        if not self._ecosistema:
            return
        # limpiar canvas (es sencillo pero efectivo)
        self.canvas.delete('all')
        max_x, max_y = 960, 720
        # dibujar plantas como puntos verdes
        for nombre, planta in self._ecosistema.plantas.items():
            x = (planta.posicion_x / max_x) * self.canvas_width
            y = (planta.posicion_y / max_y) * self.canvas_height
            r = 4
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill='green', outline='')
        # dibujar animales con diferente color por tipo
        for nombre, animal in self._ecosistema.animales.items():
            x = (animal.posicion_x / max_x) * self.canvas_width
            y = (animal.posicion_y / max_y) * self.canvas_height
            r = 6
            cls_name = animal.__class__.__name__.lower()
            color = 'white'
            if 'carn' in cls_name:
                color = 'red'
            elif 'herb' in cls_name:
                color = 'cyan'
            elif 'omn' in cls_name:
                color = 'yellow'
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline='')
            # vida como texto pequeño
            try:
                vida_text = str(int(animal.vida))
                self.canvas.create_text(x, y - 10, text=vida_text, fill='white', font=('Helvetica', 8))
            except Exception:
                pass

# InterfazGrafica puede instanciarse desde el controlador
