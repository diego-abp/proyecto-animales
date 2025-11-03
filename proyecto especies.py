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
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        super().__init__(x, y, vida, reproducirse, salto, True, True, True)

class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        super().__init__(x, y, vida, reproducirse, salto, False, True, True)

class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
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
        self.direction = 'down' # Dirección inicial
        self.is_moving = False
        # Atributos para la animación
        self.animation_frame = 0
        self.animation_timer = 0
        self.velocidad_extra = 0
        self.ticks_velocidad = 0

    def mover_arriba(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y > 0:
            self.posicion_y -= salto
        else:
            self.posicion_y = 360 # Aparece en el borde opuesto
        self.direction = 'up'
        self.is_moving = True

    def mover_abajo(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y < 360:
            self.posicion_y += salto
        else:
            self.posicion_y = 0 # Aparece en el borde opuesto
        self.direction = 'down'
        self.is_moving = True

    def mover_derecha(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x < 490:
            self.posicion_x += salto
        else:
            self.posicion_x = 0 # Aparece en el borde opuesto
        self.direction = 'right'
        self.is_moving = True

    def mover_izquierda(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x > 0:
            self.posicion_x -= salto
        else:
            self.posicion_x = 490 # Aparece en el borde opuesto
        self.direction = 'left'
        self.is_moving = True

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
        super().__init__(x, y, vida)
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

        # Cargar los sprites del jugador desde la hoja de sprites
        self.player_sprites = self._cargar_sprites_jugador()

        # Fuente para texto
        try:
            self.font = pygame.font.SysFont(None, 20)
        except Exception:
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 20)

        self.running = False

    def _cargar_sprites_jugador(self):
        """Carga, recorta y escala los sprites del jugador desde la hoja de sprites."""
        try:
            # CORRECCIÓN: Se carga la imagen, se establece el color verde (0, 255, 0) como transparente
            # y luego se convierte para un rendimiento óptimo.
            spritesheet = pygame.image.load("assets/sprites/player.png")
            # CORRECCIÓN: El color de fondo es un verde azulado (teal), no verde puro.
            spritesheet.set_colorkey((0, 128, 128))
            spritesheet = spritesheet.convert_alpha()

            def get_scaled_image(x, y, w, h, scale_factor=1.5):
                """Función auxiliar para recortar y escalar un sprite."""
                sprite = spritesheet.subsurface(pygame.Rect(x, y, w, h))
                nuevo_ancho = int(w * scale_factor)
                nuevo_alto = int(h * scale_factor)
                return pygame.transform.scale(sprite, (nuevo_ancho, nuevo_alto))

            # Coordenadas precisas para cada animación en la hoja de sprites
            # Formato: (x_inicial, y, ancho, alto, numero_de_fotogramas, espacio_horizontal)
            # CORRECCIÓN: Se ajustan las claves y coordenadas para que coincidan con los sprites.
            anim_coords = {
                'down':  (1, 4, 16, 24, 8, 17),
                'up':    (1, 100, 16, 25, 8, 17), # CORREGIDO: La altura (h) es 25, no 24.
                'right': (1, 68, 16, 24, 8, 17),
            }

            # Diccionario para guardar las listas de animación completas
            sprites = {}

            for name, coords in anim_coords.items():
                x_start, y, w, h, frames, spacing = coords
                # Cargar la tira de animación
                raw_strip = [get_scaled_image(x_start + i * spacing, y, w, h) for i in range(frames)]
                
                # CORRECCIÓN: Para la animación 'up', recortar el espacio transparente para un mejor ajuste.
                if name == 'up':
                    animation_strip = [img.subsurface(img.get_bounding_rect()) for img in raw_strip]
                else:
                    animation_strip = raw_strip
                sprites[name] = animation_strip

            # CORRECCIÓN: Crear sprites para la izquierda volteando los de la derecha.
            # Se recorta el espacio transparente extra para centrar el sprite al voltearlo.
            sprites['left'] = []
            for img in sprites['right']:
                # Recortar el espacio transparente para un volteo preciso
                bounding_rect = img.get_bounding_rect()
                cropped_img = img.subsurface(bounding_rect)
                sprites['left'].append(pygame.transform.flip(cropped_img, True, False))

            return sprites

        except pygame.error as e:
            print(f"Error al cargar sprites: {e}")
            print("Asegúrate de que 'assets/sprites/player.png' existe y la ruta es correcta.")
            return None

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False

    def draw(self):
        # Fondo
        self.screen.fill((255, 255, 255))

        # Texto de posición
        texto = f"X: {self.personaje.posicion_x}, Y: {self.personaje.posicion_y}"
        text_surf = self.font.render(texto, True, (0, 0, 0))
        self.screen.blit(text_surf, (10, 10))

        # Dibujar personaje (sprite o círculo)
        if self.player_sprites:
            # Decidir qué animación usar (caminando o quieto)
            if self.personaje.is_moving:
                animation_list = self.player_sprites[self.personaje.direction]
                # Asegurarse de que el índice del fotograma no se salga de la lista
                frame_index = self.personaje.animation_frame % len(animation_list)
                current_sprite = animation_list[frame_index]
            else:
                # Si no se mueve, mostrar el primer fotograma de la animación de la dirección actual
                animation_list = self.player_sprites[self.personaje.direction]
                current_sprite = animation_list[0]

            player_rect = current_sprite.get_rect(center=(self.personaje.posicion_x, self.personaje.posicion_y))
            self.screen.blit(current_sprite, player_rect)
        else: # Si no se carga la imagen, dibujar un círculo azul como antes
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

            # Resetear el estado de movimiento antes de comprobar las teclas
            self.personaje.is_moving = False

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

            # Lógica de animación
            if self.personaje.is_moving:
                self.personaje.animation_timer += 1
                # Cambiar de fotograma cada 6 ticks del juego (ajusta este valor para cambiar la velocidad de la animación)
                if self.personaje.animation_timer >= 5:
                    self.personaje.animation_timer = 0
                    self.personaje.animation_frame = (self.personaje.animation_frame + 1)
            else:
                self.personaje.animation_frame = 0 # Resetear animación al detenerse

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

    
        
