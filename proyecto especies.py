import pygame
import math
import time
import random


class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False):
        self.posicion_x = x
        self.posicion_y = y
        self.vida = vida
        self.reproducirse = reproducirse
        self.salto = salto
        self.atacar = atacar 
        self.correr = correr
        self.comer = comer    

class Carnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=5):
        super().__init__(x, y, vida, reproducirse, salto, True, True, True)

class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=5):
        super().__init__(x, y, vida, reproducirse, salto, False, True, True)

class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=5):
        super().__init__(x, y, vida, reproducirse, salto, True, True, True)

class Planta(Especies):
    def __init__(self, x, y, vida, reproducirse=True):
        super().__init__(x, y, vida, reproducirse, 0, False, False, False)

class Personaje:
    def __init__(self, x, y, vida):
        self.posicion_x = x
        self.posicion_y = y
        self.vida = vida
        # velocidad base (píxeles por frame). Reducida para movimiento más lento.
        self.salto = 2
        self.escudo_activo = False
        self.velocidad_extra = 0
        self.ticks_velocidad = 0

    def mover_arriba(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y > 0:
            self.posicion_y = self.posicion_y - salto
        else:
            self.posicion_y = 200
            self.posicion_x = 250

    def mover_abajo(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y < 360:
            self.posicion_y = self.posicion_y + salto
        else:
            self.posicion_y = 200
            self.posicion_x = 250

    def mover_derecha(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x < 490:
            self.posicion_x = self.posicion_x + salto
        else:
            self.posicion_x = 250
            self.posicion_y = 200

    def mover_izquierda(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x > 0:
            self.posicion_x = self.posicion_x - salto
        else:
            self.posicion_x = 250
            self.posicion_y = 200

    def activar_escudo(self):
        self.escudo_activo = True

    def desactivar_escudo(self):
        self.escudo_activo = False

    def activar_velocidad_extra(self):
        # bono de velocidad temporal (mantener pequeño para no romper la sensación)
        self.velocidad_extra = 1
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

class VistaPygame:
    """Interfaz simple usando pygame: dibuja 3 entidades y permite mover el personaje.

    Controles:
    - Flechas o WASD: mover
    - ESC o cerrar ventana: salir
    """
    def __init__(self, ancho=500, alto=400, fps=30):
        pygame.init()
        self.ancho = ancho
        self.alto = alto
        self.screen = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Juego - Proyecto Especies")
        self.clock = pygame.time.Clock()
        self.fps = fps

        # Entidades
        self.carnivoro = Carnivoro(250, 200, 100)
        self.herbivoro = Herbivoro(10, 200, 100)
        self.omnivoro = Omnivoro(400, 200, 100)
        self.personaje = Personaje(200, 200, 100)

        # Fuente para texto
        try:
            self.font = pygame.font.SysFont(None, 20)
        except Exception:
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 20)

        self.running = False

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.personaje.mover_arriba()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.personaje.mover_abajo()
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.personaje.mover_izquierda()
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.personaje.mover_derecha()

    def draw(self):
        # Fondo
        self.screen.fill((255, 255, 255))

        # Texto de posición
        texto = f"X: {self.personaje.posicion_x}, Y: {self.personaje.posicion_y}"
        text_surf = self.font.render(texto, True, (0, 0, 0))
        self.screen.blit(text_surf, (10, 10))

        # Dibujar personaje
        pygame.draw.circle(self.screen, (0, 0, 255), (int(self.personaje.posicion_x), int(self.personaje.posicion_y)), 15)

        # Carnívoro
        pygame.draw.circle(self.screen, (255, 0, 0), (int(self.carnivoro.posicion_x), int(self.carnivoro.posicion_y)), 15)

        # Herbívoro
        pygame.draw.circle(self.screen, (0, 200, 0), (int(self.herbivoro.posicion_x), int(self.herbivoro.posicion_y)), 15)

        # Omnívoro: dibujar como cuadrado morado
        omni_size = 20
        omni_x = int(self.omnivoro.posicion_x) - omni_size // 2
        omni_y = int(self.omnivoro.posicion_y) - omni_size // 2
        pygame.draw.rect(self.screen, (128, 0, 128), (omni_x, omni_y, omni_size, omni_size))

        # Instrucciones
        instrucciones = self.font.render("Flechas/WASD = mover, ESC = salir", True, (0, 0, 150))
        self.screen.blit(instrucciones, (10, self.alto - 25))

        pygame.display.flip()

    def iniciar(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            # Movimiento sostenido: comprobar teclas mantenidas
            keys = pygame.key.get_pressed()
            # salir con ESC también por keys
            if keys[pygame.K_ESCAPE]:
                self.running = False

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.personaje.mover_arriba()
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.personaje.mover_abajo()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.personaje.mover_izquierda()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.personaje.mover_derecha()

            # Actualizaciones por tick
            self.personaje.tick_velocidad()

            # Dibujar
            self.draw()

            # Mantener FPS
            self.clock.tick(self.fps)

        pygame.quit()

if __name__ == "__main__":
    print("=== Juego en 2 capas Lógica y Vista ===")
    juego = VistaPygame()
    juego.iniciar()
#hola 

    
        


