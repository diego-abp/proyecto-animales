import wx
import math
import time
import random

class especies:
    def __init__(self, x, y, vida, reproducirse, salto, atacar, correr, comer):
        self.posicion_x = x
        self.posicion_y = y
        self.vida = vida
        self.reproducirse = reproducirse
        self.salto = 5
        self.atacar = atacar 
        self.correr = False
        self.comer = False    

class carnivoro(especies):
    def __intit__(self, x, y, vida, reproducirse, salto, atacar, false, false):
        super().__init__(self, x, y, vida, reproducirse, salto, atacar, false, false)

class hervivoro(especies):
    def __init__(self, x, y, vida, reproducirse, salto, false, false):
        super().__init__(self, x, y, vida, reproducirse, salto, false,false)

class homniboro(especies):
    def __intit__(self, x, y, vida, reproducirse, salto, atacar, false, false):
        super().__init__(self, x, y, vida, reproducirse, salto, atacar, false, false)
# prubeba de commit
class planta(especies):
    def __init__(self, x, y, vida, reproducirse, ):
        super().__init__(self, x, y, vida, reproducirse, )

class Personaje:
	def __init__(self, x, y, vida):
		self.posicion_x = x
		self.posicion_y = y
		self.vida = vida
		self.salto = 5
		self.escudo_activo = False
		self.velocidad_extra = 0
		self.ticks_velocidad = 0

	def mover_arriba(self):
		salto = self.salto + self.velocidad_extra
		if(self.posicion_y >0):
			self.posicion_y = self.posicion_y - salto
		else:
			self.posicion_y = 200
			self.posicion_x = 250
            
	def mover_abajo(self):
		salto = self.salto + self.velocidad_extra
		if(self.posicion_y <360):
			self.posicion_y = self.posicion_y + salto
		else:
			self.posicion_y = 200
			self.posicion_x = 250
            
	def mover_derecha(self):
		salto = self.salto + self.velocidad_extra
		if (self.posicion_x < 490):
			self.posicion_x = self.posicion_x + salto
		else:
			self.posicion_x = 250
			self.posicion_y = 200
            
	def mover_izquierda(self):
		salto = self.salto + self.velocidad_extra
		if (self.posicion_x > 0):
			self.posicion_x = self.posicion_x - salto
		else:
			self.posicion_x = 250
			self.posicion_y = 200
	def activar_escudo(self):
		self.escudo_activo = True

	def desactivar_escudo(self):
		self.escudo_activo = False

	def activar_velocidad_extra(self):
		self.velocidad_extra = 2
		self.ticks_velocidad = 10  # dura 10 movimientos

	def tick_velocidad(self):
		if self.ticks_velocidad > 0:
			self.ticks_velocidad -= 1
			if self.ticks_velocidad == 0:
				self.velocidad_extra = 0

class Caballero(Personaje):
	def __init__(self, x, y, vida, defensa):
		super().__init__(x,y,vida)
		self.defensa = defensa

class VistaSimple:
    def __init__(self):
        self.app = wx.App()
        self.ventana = wx.Frame(None, title="Juego", size=(500, 400))
        self.panel = wx.Panel(self.ventana)
        
        # CAMBIO IMPORTANTE: Usar EVT_CHAR_HOOK en lugar de EVT_KEY_DOWN
        self.panel.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.panel.SetFocus()
        
        self.carnivoro = carnivoro(250, 200, 100)
        self.hervivoro = hervivoro(10, 200, 100, 100)
        self.Personaje = Personaje (200, 200, 100)
        self.instrucciones = wx.StaticText(self.panel, pos=(10, 10), 
            label="Flechas/WASD = mover, ESC = salir")
        self.instrucciones.SetForegroundColour('blue')
        self.ventana.Centre()
        self.ventana.Show()

    def on_paint(self, event):
        dc = wx.PaintDC(self.panel)
        dc.SetBackground(wx.Brush('white'))
        dc.Clear()
        dc.DrawText(f"X: {self.personaje.posicion_x}, Y: {self.personaje.posicion_y}", 10, 40)
        dc.SetBrush(wx.Brush('green'))
        dc.DrawCircle(self.personaje.posicion_x, self.personaje.posicion_y, 15)
        dc.SetBrush(wx.Brush('red'))
        if self.monstruo.vida > 0:
            dc.DrawCircle(self.monstruo.posicion_x, self.monstruo.posicion_y, 15)
    
    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        print(f"tecla-->{keycode}")
        
        # Flechas direccionales
        if keycode == wx.WXK_UP:
            print("¡Flecha Arriba!")
            self.personaje.mover_arriba()
        elif keycode == wx.WXK_DOWN:
            print("¡Flecha Abajo!")
            self.personaje.mover_abajo()
        elif keycode == wx.WXK_LEFT:
            print("¡Flecha Izquierda!")
            self.personaje.mover_izquierda()
        elif keycode == wx.WXK_RIGHT:
            print("¡Flecha Derecha!")
            self.personaje.mover_derecha()
        # WASD
        elif keycode == ord('W') or keycode == ord('w'):
            self.personaje.mover_arriba()
        elif keycode == ord('S') or keycode == ord('s'):
            self.personaje.mover_abajo()
        elif keycode == ord('A') or keycode == ord('a'):
            self.personaje.mover_izquierda()
        elif keycode == ord('D') or keycode == ord('d'):
            self.personaje.mover_derecha()
        elif keycode == wx.WXK_ESCAPE:
            self.ventana.Close()
            return
        
        self.panel.Refresh()
        event.Skip()  # Importante para EVT_CHAR_HOOK

    def iniciar(self):
        self.app.MainLoop()

if __name__ == "__main__":
    print("=== Juego en 2 capas Lógica y Vista ===")
    juego = VistaSimple()
    juego.iniciar()
#hola 

    
        


