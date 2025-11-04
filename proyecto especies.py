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
        # Estados de animación
        self.IDLE_DOWN = 0
        self.IDLE_RIGHT = 1
        self.IDLE_UP = 2
        self.WALK_DOWN = 3
        self.WALK_RIGHT = 4
        self.WALK_UP = 5

        self.posicion_x = x
        self.posicion_y = y
        self.vida = vida
        self.salto = 2
        self.velocidad_extra = 0
        self.ticks_velocidad = 0

        # Atributos de animación
        self.state = self.IDLE_DOWN
        self.direction = 'down' # 'down', 'up', 'left', 'right'
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100 # ms por cuadro

    def update_animation(self, animation_strip):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.frame_index = (self.frame_index + 1) % len(animation_strip)

    def mover_arriba(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y > 0:
            self.posicion_y -= salto
        else:
            self.posicion_y = 360 # Aparece en el borde opuesto

    def mover_abajo(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y < 360:
            self.posicion_y += salto
        else:
            self.posicion_y = 0 # Aparece en el borde opuesto

    def mover_derecha(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x < 490:
            self.posicion_x += salto
        else:
            self.posicion_x = 0 # Aparece en el borde opuesto

    def mover_izquierda(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x > 0:
            self.posicion_x -= salto
        else:
            self.posicion_x = 490 # Aparece en el borde opuesto

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

        # Cargar animaciones del personaje
        self.animations = self._load_animations()

        try:
            self.font = pygame.font.SysFont(None, 20)
        except Exception:
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 20)

        self.running = False

    def _load_animations(self):
        """Extrae, escala y organiza las animaciones desde la hoja de sprites."""
        animations = {}
        sprite_sheet = pygame.image.load("assets/sprites/player.png").convert_alpha()

        # Limpiar el fondo de la hoja de sprites para evitar bordes de color.
        sprite_sheet_limpia = pygame.Surface(sprite_sheet.get_size(), pygame.SRCALPHA)
        for x in range(sprite_sheet.get_width()):
            for y in range(sprite_sheet.get_height()):
                color_pixel = sprite_sheet.get_at((x, y))
                if color_pixel[:3] != (0, 128, 128) and color_pixel[:3] != (0, 64, 64):
                    sprite_sheet_limpia.set_at((x, y), color_pixel)
        
        # CORRECCIÓN: Las definiciones ahora coinciden con la hoja de sprites real (sprites de 16x22).
        animation_definitions = {
            self.personaje.WALK_DOWN:   (5, 8, 17),  # y=5, 8 frames, 17px de espacio
            self.personaje.WALK_RIGHT:  (37, 8, 17),
            self.personaje.WALK_UP:     (101, 8, 17),
        }

        frame_width, frame_height = 16, 22
        scale_width, scale_height = 48, 48

        # Cargar animaciones de caminar
        for state, (y_pos, num_frames, spacing) in animation_definitions.items():
            animation_strip = []
            for i in range(num_frames):
                x = 1 + (i * spacing)
                y = y_pos
                # 1. Recortar el sprite original.
                original_frame = sprite_sheet_limpia.subsurface(pygame.Rect(x, y, frame_width, frame_height))
                # 2. Recortar el espacio transparente para obtener solo el personaje (esto evita el deslizamiento).
                cropped_frame = original_frame.subsurface(original_frame.get_bounding_rect())
                # 3. Escalar el personaje ya recortado.
                scaled_frame = pygame.transform.scale(cropped_frame, (int(cropped_frame.get_width() * 1.5), int(cropped_frame.get_height() * 1.5)))
                # 4. Crear un lienzo consistente y pegar el personaje en el centro.
                canvas = pygame.Surface((scale_width, scale_height), pygame.SRCALPHA)
                dest_rect = scaled_frame.get_rect(center=(scale_width // 2, scale_height // 2))
                canvas.blit(scaled_frame, dest_rect)
                animation_strip.append(canvas)
            animations[state] = animation_strip
        
        # Crear animaciones "idle" usando el primer fotograma de las de caminar
        animations[self.personaje.IDLE_DOWN] = [animations[self.personaje.WALK_DOWN][0]]
        animations[self.personaje.IDLE_RIGHT] = [animations[self.personaje.WALK_RIGHT][0]]
        animations[self.personaje.IDLE_UP] = [animations[self.personaje.WALK_UP][0]]

        return animations

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

        # Dibujar el sprite del personaje
        if self.animations:
            # Obtener la animación y el cuadro actual
            animation_strip = self.animations[self.personaje.state]
            self.personaje.update_animation(animation_strip)
            current_frame = animation_strip[self.personaje.frame_index]

            # Voltear la imagen si la dirección es izquierda
            flip = self.personaje.direction == 'left'
            image_to_draw = pygame.transform.flip(current_frame, flip, False)

            # Dibujar el sprite centrado en la posición del personaje
            rect = image_to_draw.get_rect(center=(int(self.personaje.posicion_x), int(self.personaje.posicion_y)))
            self.screen.blit(image_to_draw, rect)
        else:
            # Si no hay sprites, dibujar el círculo azul
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

            # --- Lógica de Movimiento y Estado de Animación ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                self.running = False

            dx, dy = 0, 0
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = 1

            # --- CORRECCIÓN: Lógica de estado mejorada para prevenir IndexError ---
            old_state = self.personaje.state
            is_moving = dx != 0 or dy != 0

            if is_moving:
                # La prioridad de movimiento es vertical, luego horizontal
                if dy < 0:
                    self.personaje.state = self.personaje.WALK_UP
                    self.personaje.direction = 'up'
                    self.personaje.mover_arriba()
                elif dy > 0:
                    self.personaje.state = self.personaje.WALK_DOWN
                    self.personaje.direction = 'down'
                    self.personaje.mover_abajo()
                
                # El movimiento horizontal solo se aplica si no hay movimiento vertical
                if dx < 0 and dy == 0:
                    self.personaje.state = self.personaje.WALK_RIGHT # Se usa el de la derecha y se voltea al dibujar
                    self.personaje.direction = 'left'
                    self.personaje.mover_izquierda()
                elif dx > 0 and dy == 0:
                    self.personaje.state = self.personaje.WALK_RIGHT
                    self.personaje.direction = 'right'
                    self.personaje.mover_derecha()
            else:
                # Si no se mueve, cambiar al estado IDLE correspondiente a la última dirección
                if self.personaje.direction == 'up': self.personaje.state = self.personaje.IDLE_UP
                elif self.personaje.direction == 'down': self.personaje.state = self.personaje.IDLE_DOWN
                else: self.personaje.state = self.personaje.IDLE_RIGHT # Para 'left' y 'right'

            # Si el estado de la animación ha cambiado, reiniciar el índice del fotograma.
            if self.personaje.state != old_state:
                self.personaje.frame_index = 0

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

    
        
