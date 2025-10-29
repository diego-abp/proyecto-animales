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
        self.correr = correr
        self.comer = False    

class carnivoro(especies):
    def __intit__(self, x, y, vida, reproducirse, salto, atacar, correr, comer):
        super().__init__(self, x, y, vida, reproducirse, salto, atacar, correr, comer)

class hervivoro(especies):
    def __init__(self, x, y, vida, reproducirse, salto, correr, comer):
        super().__init__(self, x, y, vida, reproducirse, salto, correr, comer)

class homniboro(especies):
    def __intit__(self, x, y, vida, reproducirse, salto, atacar, correr, comer):
        super().__init__(self, x, y, vida, reproducirse, salto, atacar, correr, comer)
# prubeba de commit

    






#hola