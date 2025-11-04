import pygame
import math
import time
import random


class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, tiempo_vida_max=100):
        self.posicion_x = x
        self.posicion_y = y
        self.vida = vida
        self.reproducirse = reproducirse
        self.salto = salto
        self.atacar = atacar 
        self.correr = correr
        self.comer = comer
        self.tiempo_vida_max = tiempo_vida_max
        self.tiempo_vida_actual = tiempo_vida_max
        self.ultimo_update = time.time()
        
        # Atributos para movimiento aleatorio de las especies
        self.last_random_move_time = time.time()
        self.random_move_delay = 0.5 # Mover cada 0.5 segundos
        self.current_dx, self.current_dy = 0, 0 # Dirección actual (x, y)

    
    def update_tiempo_vida(self):
        """Actualiza el tiempo de vida de la especie. Devuelve True si sigue viva, False si ha muerto."""
        ahora = time.time()
        tiempo_transcurrido = ahora - self.ultimo_update
        # Reducir tiempo de vida (1 unidad cada segundo)
        self.tiempo_vida_actual = max(0, self.tiempo_vida_actual - tiempo_transcurrido)
        self.ultimo_update = ahora
        return self.tiempo_vida_actual > 0
    
    def get_porcentaje_vida(self):
        """Devuelve el porcentaje de tiempo de vida restante."""
        return (self.tiempo_vida_actual / self.tiempo_vida_max) * 100

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """
        Mueve la especie de forma aleatoria dentro de los límites de la pantalla.
        """
        ahora = time.time()
        if ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            self.current_dx = random.choice([-1, 0, 1])
            self.current_dy = random.choice([-1, 0, 1])
            
        # Mover la especie
        self.posicion_x += self.current_dx * self.salto
        self.posicion_y += self.current_dy * self.salto

        # Envolver la posición si sale de los límites de la pantalla
        # El operador % maneja bien los valores negativos para envolver.
        self.posicion_x %= screen_width
        self.posicion_y %= screen_height

class Carnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los carnívoros tienen tiempo de vida medio (180)
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, tiempo_vida_max=180)
        self.presa_objetivo = None
        self.estado_caza = "DEAMBULANDO"  # DEAMBULANDO, ACECHANDO, ATACANDO
        self.radio_deteccion = 150
        self.radio_ataque = 70

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """
        Comportamiento de depredador con estados: deambula, acecha y ataca.
        """
        # Verificar si la presa sigue viva, si no, la olvida.
        if self.presa_objetivo and (self.presa_objetivo not in posibles_presas.values() or self.presa_objetivo.get_porcentaje_vida() <= 0):
            self.presa_objetivo = None
            self.estado_caza = "DEAMBULANDO"

        # --- Lógica de Estados ---

        # 1. BÚSQUEDA (si está deambulando)
        if self.estado_caza == "DEAMBULANDO":
            presa_mas_cercana = None
            distancia_minima = self.radio_deteccion
            for especie in posibles_presas.values():
                if especie is self or isinstance(especie, Carnivoro):
                    continue
                dist = math.sqrt((self.posicion_x - especie.posicion_x)**2 + (self.posicion_y - especie.posicion_y)**2)
                if dist < distancia_minima:
                    distancia_minima = dist
                    presa_mas_cercana = especie
            
            if presa_mas_cercana:
                self.presa_objetivo = presa_mas_cercana
                self.estado_caza = "ACECHANDO" # Cambia a estado de acecho
            else:
                # Si no encuentra presa, deambula aleatoriamente.
                super().mover(screen_width, screen_height, posibles_presas)
                return # Termina la ejecución de este turno

        # 2. MOVIMIENTO (si está acechando o atacando)
        if self.estado_caza in ["ACECHANDO", "ATACANDO"]:
            if not self.presa_objetivo: # Seguridad por si pierde la presa
                self.estado_caza = "DEAMBULANDO"
                return

            dx = self.presa_objetivo.posicion_x - self.posicion_x
            dy = self.presa_objetivo.posicion_y - self.posicion_y
            dist = math.sqrt(dx**2 + dy**2)

            # Decide la velocidad según el estado y la distancia
            velocidad_actual = 0
            if dist < self.radio_ataque:
                self.estado_caza = "ATACANDO"
                # Velocidad progresiva: más rápido cuanto más cerca está.
                velocidad_base_ataque = 3.0
                aceleracion = 2.5
                progreso = 1 - (dist / self.radio_ataque) # 0 en el borde, 1 en el centro
                velocidad_actual = velocidad_base_ataque + (aceleracion * progreso)
            else:
                self.estado_caza = "ACECHANDO"
                velocidad_actual = 1.5 # Velocidad de acecho, discreta y lenta

            # Moverse hacia la presa
            if dist > 0:
                self.posicion_x += (dx / dist) * velocidad_actual
                self.posicion_y += (dy / dist) * velocidad_actual


class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los herbívoros tienen un comportamiento más tranquilo.
        # Se mueven más lento (salto=1) y cambian de dirección con menos frecuencia.
        super().__init__(x, y, vida, reproducirse, salto=1, atacar=False, correr=True, comer=True, tiempo_vida_max=60)
        self.random_move_delay = 2.0 # Cambia de dirección cada 2 segundos.

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """
        Comportamiento de movimiento específico para el herbívoro: más tranquilo y
        con tendencia a quedarse quieto.
        """
        ahora = time.time()
        if ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            
            # 50% de probabilidad de quedarse quieto, 50% de moverse.
            if random.random() < 0.5:
                self.current_dx, self.current_dy = 0, 0
            else:
                self.current_dx = random.choice([-1, 0, 1])
                self.current_dy = random.choice([-1, 0, 1])

        # Reutiliza la lógica de movimiento y envoltura de la clase padre.
        super().mover(screen_width, screen_height)

class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los omnívoros tienen tiempo de vida equilibrado (100)
        super().__init__(x, y, vida, reproducirse, salto=3, atacar=True, correr=True, comer=True, tiempo_vida_max=100)
        self.presa = None
        self.modo_caza = False # Alterna entre cazar y deambular

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """
        Comportamiento mixto: a veces caza, a veces deambula tranquilamente.
        """
        ahora = time.time()
        if ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            # 50% de probabilidad de cambiar de modo (caza/deambular)
            if random.random() < 0.5:
                self.modo_caza = not self.modo_caza
                self.presa = None # Olvida la presa al cambiar de modo

        if self.modo_caza:
            # Comportamiento de caza (similar al carnívoro pero menos agresivo)
            if self.presa and (self.presa not in posibles_presas.values() or self.presa.get_porcentaje_vida() <= 0):
                self.presa = None

            if not self.presa:
                presa_mas_cercana = None
                distancia_minima = 100  # Radio de detección más pequeño
                for especie in posibles_presas.values():
                    if especie is self or isinstance(especie, (Carnivoro, Omnivoro)):
                        continue
                    dist = math.sqrt((self.posicion_x - especie.posicion_x)**2 + (self.posicion_y - especie.posicion_y)**2)
                    if dist < distancia_minima:
                        distancia_minima = dist
                        presa_mas_cercana = especie
                self.presa = presa_mas_cercana

            if self.presa:
                velocidad_caza = 1.5
                dx = self.presa.posicion_x - self.posicion_x
                dy = self.presa.posicion_y - self.posicion_y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.posicion_x += (dx / dist) * velocidad_caza
                    self.posicion_y += (dy / dist) * velocidad_caza
            else: # Si no encuentra presa en modo caza, deambula
                super().mover(screen_width, screen_height)
        else:
            # Comportamiento de recolección (similar al herbívoro)
            super().mover(screen_width, screen_height)
class Planta(Especies):
    def __init__(self, x, y, vida, reproducirse=True):
        # Las plantas tienen tiempo de vida muy largo (150)
        super().__init__(x, y, vida, reproducirse, 0, False, False, False, tiempo_vida_max=150)
        
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

        # Lista de especies vivas
        self.especies_vivas = {
            'carnivoro': Carnivoro(250, 200, 100),
            'herbivoro': Herbivoro(10, 200, 100),
            'omnivoro': Omnivoro(400, 200, 100)
        }
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
        # Cargar la hoja con alpha y trabajar por rectángulos (más fiable y rápido).
        sprite_sheet = pygame.image.load("assets/sprites/player.png").convert_alpha()

        # Definiciones (y_pos, num_frames, spacing). Mantengo las posiciones usadas
        # originalmente: si la hoja cambia, ajustar estos valores.
        # Para usar un frame estático, simplemente cargamos 1 fotograma en lugar de 8.
        animation_definitions = {
            self.personaje.WALK_DOWN:   (5, 1, 17),
            self.personaje.WALK_RIGHT:  (37, 1, 17),
            self.personaje.WALK_UP:     (101, 1, 17),
        }

        frame_width, frame_height = 16, 22
        scale_width, scale_height = 48, 48

        # Cargar animaciones de caminar de forma segura.
        for state, (y_pos, num_frames, spacing) in animation_definitions.items():
            animation_strip = []
            for i in range(num_frames):
                x = 1 + (i * spacing)
                y = y_pos
                # Recortar el área esperada y usar un copy() para evitar referencias a la hoja.
                try:
                    original_frame = sprite_sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height)).copy()
                except Exception:
                    # Si las coordenadas están fuera de rango, crear un frame transparente de respaldo.
                    original_frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)

                # Intentar recortar la región no transparente; si está vacía, usar el frame completo.
                bounding = original_frame.get_bounding_rect()
                if bounding.width == 0 or bounding.height == 0:
                    cropped_frame = original_frame
                else:
                    cropped_frame = original_frame.subsurface(bounding).copy()

                # Escalar el sprite recortado manteniendo proporciones y calidad.
                scale_factor = max(1, min(scale_width / max(1, cropped_frame.get_width()), scale_height / max(1, cropped_frame.get_height())))
                new_w = max(1, int(cropped_frame.get_width() * scale_factor))
                new_h = max(1, int(cropped_frame.get_height() * scale_factor))
                try:
                    scaled_frame = pygame.transform.smoothscale(cropped_frame, (new_w, new_h))
                except Exception:
                    scaled_frame = pygame.transform.scale(cropped_frame, (new_w, new_h))

                # Crear un canvas y pegar el sprite alineado por la parte inferior.
                # Esto asegura que los pies del personaje estén siempre a la misma altura.
                canvas = pygame.Surface((scale_width, scale_height), pygame.SRCALPHA)
                # Usamos 'midbottom' para alinear el centro horizontal y la parte inferior vertical.
                dest_rect = scaled_frame.get_rect(midbottom=(scale_width // 2, scale_height))
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

        # Actualizar tiempo de vida de las especies
        especies_muertas = []
        y_offset = 10
        
        for nombre, especie in self.especies_vivas.items():
            if especie.update_tiempo_vida():
                # Especie viva: mostrar tiempo de vida restante
                porcentaje = especie.get_porcentaje_vida()
                # Color según porcentaje de vida
                if porcentaje > 60:
                    color = (0, 150, 0)  # Verde
                elif porcentaje > 30:
                    color = (200, 150, 0)  # Amarillo
                else:
                    color = (200, 0, 0)  # Rojo
                
                texto = f"{especie.__class__.__name__}: {porcentaje:.1f}%"
                text_surf = self.font.render(texto, True, color)
                self.screen.blit(text_surf, (10, y_offset))
                y_offset += 20
            else:
                # Especie muerta: marcar para eliminar silenciosamente
                especies_muertas.append(nombre)

        # Eliminar especies muertas
        for nombre in especies_muertas:
            del self.especies_vivas[nombre]

        # Texto de posición del personaje
        texto = f"X: {self.personaje.posicion_x}, Y: {self.personaje.posicion_y}"
        text_surf = self.font.render(texto, True, (0, 0, 0))
        self.screen.blit(text_surf, (10, y_offset))

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
            # Alinear por la parte superior central para que posicion_y represente la parte superior del personaje
            rect = image_to_draw.get_rect(midtop=(int(self.personaje.posicion_x), int(self.personaje.posicion_y)))
            self.screen.blit(image_to_draw, rect)
        else:
            # Si no hay sprites, dibujar el círculo azul
            pygame.draw.circle(self.screen, (0, 0, 255), (int(self.personaje.posicion_x), int(self.personaje.posicion_y)), 15)

        # Dibujar especies vivas
        for nombre, especie in self.especies_vivas.items():
            if nombre == 'carnivoro':
                pygame.draw.circle(self.screen, (255, 0, 0), 
                                (int(especie.posicion_x), int(especie.posicion_y)), 15)
            elif nombre == 'herbivoro':
                pygame.draw.circle(self.screen, (0, 200, 0), 
                                (int(especie.posicion_x), int(especie.posicion_y)), 15)
            elif nombre == 'omnivoro':
                omni_size = 20
                omni_x = int(especie.posicion_x) - omni_size // 2
                omni_y = int(especie.posicion_y) - omni_size // 2
                pygame.draw.rect(self.screen, (128, 0, 128), 
                              (omni_x, omni_y, omni_size, omni_size))

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

            # Movimiento aleatorio de las especies
            for nombre, especie in self.especies_vivas.items():
                especie.mover(self.ancho, self.alto, self.especies_vivas)

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

    
        
