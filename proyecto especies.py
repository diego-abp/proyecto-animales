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
        self.salto = salto
        self.atacar = atacar 
        self.correr = correr
        self.comer = False    
        self.dormir = False
