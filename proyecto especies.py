import pygame
import math
import time
import random


class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, tiempo_vida_max=100, sync_vida_with_tiempo=False):
        self.posicion_x = x
        self.posicion_y = y
        # vida es la vida actual (puede bajar por daño), vida_max es la vida inicial máxima
        self.vida = vida
        self.vida_max = vida
        self.reproducirse = reproducirse
        self.salto = salto
        self.atacar = atacar
        self.correr = correr
        self.comer = comer
        self.tiempo_vida_max = tiempo_vida_max
        self.tiempo_vida_actual = tiempo_vida_max
        self.ultimo_update = time.time()
        # Si es True, el envejecimiento por tiempo también reduce la vida (HP)
        # Atributos para movimiento aleatorio
        self.last_random_move_time = time.time()
        self.random_move_delay = random.uniform(1, 3) # Cambiar de dirección cada 1-3 segundos
        self.random_move_target = None
        self.sync_vida_with_tiempo = sync_vida_with_tiempo

    def update_tiempo_vida(self):
        """Actualiza el tiempo de vida de la especie. Devuelve True si sigue viva, False si ha muerto."""
        ahora = time.time()
        tiempo_transcurrido = ahora - self.ultimo_update
        # Reducir tiempo de vida (1 unidad cada segundo)
        self.tiempo_vida_actual = max(0, self.tiempo_vida_actual - tiempo_transcurrido)

        # Si la especie sincroniza vida con el tiempo, reducir la vida (HP) proporcionalmente
        if getattr(self, 'sync_vida_with_tiempo', False) and self.tiempo_vida_max > 0:
            # pérdida de vida por envejecimiento proporcional al tiempo transcurrido
            aging_loss = (tiempo_transcurrido / self.tiempo_vida_max) * getattr(self, 'vida_max', 0)
            self.vida = max(0, self.vida - aging_loss)

        self.ultimo_update = ahora
        return self.tiempo_vida_actual > 0
    
    def get_porcentaje_vida(self):
        """Devuelve el porcentaje de tiempo de vida restante."""
        return (self.tiempo_vida_actual / self.tiempo_vida_max) * 100

    def mover_hacia(self, target_x, target_y, velocidad=None):
        """Mueve la especie hacia (target_x, target_y) usando su salto como velocidad.
        No gestiona colisiones; hace wrap en los bordes igual que el personaje.
        """
        if velocidad is None:
            velocidad = self.salto
        dx = target_x - self.posicion_x
        dy = target_y - self.posicion_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        # Normalizar y mover
        nx = dx / dist
        ny = dy / dist
        self.posicion_x += nx * velocidad
        self.posicion_y += ny * velocidad
        # Wrap (coincide con límites usados en Personaje)
        if self.posicion_x < 0:
            self.posicion_x = 490
        elif self.posicion_x > 490:
            self.posicion_x = 0
        if self.posicion_y < 0:
            self.posicion_y = 360
        elif self.posicion_y > 360:
            self.posicion_y = 0

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Comportamiento de movimiento base: deambular aleatoriamente."""
        ahora = time.time()
        # Si no tiene objetivo o ha pasado suficiente tiempo, elige uno nuevo
        if self.random_move_target is None or ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            self.random_move_delay = random.uniform(2, 5) # Nuevo intervalo
            # Elige un punto aleatorio en la pantalla
            self.random_move_target = (random.randint(0, screen_width), random.randint(0, screen_height))

        # Moverse hacia el objetivo aleatorio
        if self.random_move_target:
            self.mover_hacia(self.random_move_target[0], self.random_move_target[1])
            # Si llega cerca del objetivo, lo olvida para poder elegir uno nuevo
            if math.hypot(self.posicion_x - self.random_move_target[0], self.posicion_y - self.random_move_target[1]) < 10:
                self.random_move_target = None

class Carnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=1.5):
        # Los carnívoros tienen tiempo de vida medio (80). Se mueven más despacio por defecto.
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, tiempo_vida_max=80)
        # Atributos de ataque: menos daño por golpe y cooldown mayor (no mata de un golpe)
        self.attack_power = 25
        self.attack_cooldown = 2.0  # segundos entre ataques
        self.last_attack = 0.0

class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los herbívoros tienen tiempo de vida largo (120)
        # sync_vida_with_tiempo=True hace que el envejecimiento reduzca su HP
        super().__init__(x, y, vida, reproducirse, salto, False, True, True, tiempo_vida_max=120, sync_vida_with_tiempo=True)

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
            'carnivoro': Carnivoro(250, 200, 100, 15),
            'herbivoro': Herbivoro(10, 200, 100),
            'omnivoro': Omnivoro(400, 200, 100)
        }
        self.personaje = Personaje(200, 200, 100)
        # Popups de daño: lista de dict {text,x,y,start_ms}
        self.damage_popups = []

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

    def _update_ai(self):
        """Lógica simple de IA para carnívoro: perseguir y atacar al herbívoro si existe,
        si no, perseguir y atacar al personaje.
        """
        ahora = time.time()
        if 'carnivoro' not in self.especies_vivas:
            return
        carn = self.especies_vivas['carnivoro']

        # Elegir objetivo: preferir herbívoro si existe
        if 'herbivoro' in self.especies_vivas:
            objetivo = self.especies_vivas['herbivoro']
            objetivo_especie = 'herbivoro'
        else:
            objetivo = self.personaje
            objetivo_especie = 'personaje'

        # Mover hacia objetivo
        carn.mover_hacia(objetivo.posicion_x, objetivo.posicion_y)

        # Atacar si está lo suficientemente cerca
        distancia = math.hypot(carn.posicion_x - objetivo.posicion_x, carn.posicion_y - objetivo.posicion_y)
        if distancia < 25:
            last = getattr(carn, 'last_attack', 0)
            if ahora - last >= carn.attack_cooldown:
                carn.last_attack = ahora
                if objetivo_especie == 'herbivoro':
                    # Atacar al herbívoro reduciendo su vida; eliminar si llega a 0
                    if 'herbivoro' in self.especies_vivas:
                        objetivo.vida -= carn.attack_power
                        # Crear popup de daño
                        self.damage_popups.append({
                            'text': f"-{int(carn.attack_power)}",
                            'x': objetivo.posicion_x,
                            'y': objetivo.posicion_y - 10,
                            'start': pygame.time.get_ticks()
                        })
                        # opcional: imprimir daño en consola para depuración
                        # print(f"Herbivoro atacado! vida={objetivo.vida}")
                        if objetivo.vida <= 0:
                            del self.especies_vivas['herbivoro']
                else:
                    # Atacar al jugador reduciendo vida
                    self.personaje.vida -= carn.attack_power
                    # Crear popup de daño para el jugador
                    self.damage_popups.append({
                        'text': f"-{int(carn.attack_power)}",
                        'x': self.personaje.posicion_x,
                        'y': self.personaje.posicion_y - 10,
                        'start': pygame.time.get_ticks()
                    })
                    # print(f"Player attacked! vida={self.personaje.vida}")
                    if self.personaje.vida <= 0:
                        # Fin del juego si el jugador muere
                        self.running = False

    def draw(self):
        # Fondo
        self.screen.fill((255, 255, 255))

        # Actualizar tiempo de vida de las especies
        especies_muertas = []
        y_offset = 10
        
        for nombre, especie in self.especies_vivas.items():
            if especie.update_tiempo_vida():
                # Especie viva: mostrar tiempo de vida restante (excepto herbívoro)
                if nombre != 'herbivoro':
                    porcentaje = especie.get_porcentaje_vida()
                    # Color según porcentaje de vida (no mostrar verde):
                    # Usar negro cuando no está bajo, rojo cuando está bajo
                    if porcentaje > 30:
                        color = (0, 0, 0)  # Negro para suficiente
                    else:
                        color = (200, 0, 0)  # Rojo para bajo
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
        texto = f"X: {self.personaje.posicion_x}, Y: {self.personaje.posicion_y}  HP: {int(self.personaje.vida)}"
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
                # Mostrar vida (HP) cerca del herbívoro
                hp_text = self.font.render(f"HP:{int(especie.vida)}", True, (0, 0, 0))
                self.screen.blit(hp_text, (int(especie.posicion_x) - hp_text.get_width()//2, int(especie.posicion_y) - 25))
            elif nombre == 'omnivoro':
                omni_size = 20
                omni_x = int(especie.posicion_x) - omni_size // 2
                omni_y = int(especie.posicion_y) - omni_size // 2
                pygame.draw.rect(self.screen, (128, 0, 128), 
                              (omni_x, omni_y, omni_size, omni_size))

        # Dibujar popups de daño (flotantes)
        now_ms = pygame.time.get_ticks()
        popups_a_quitar = []
        for i, popup in enumerate(self.damage_popups):
            elapsed = now_ms - popup['start']
            if elapsed > 1000:
                popups_a_quitar.append(i)
                continue
            # subir ligeramente con el tiempo
            y_off = popup['y'] - (elapsed * 0.03)
            alpha = max(0, 255 - int(elapsed / 1000 * 255))
            surf = self.font.render(popup['text'], True, (200, 0, 0))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (popup['x'] - surf.get_width()//2, y_off))

        # limpiar popups caducados
        for idx in reversed(popups_a_quitar):
            del self.damage_popups[idx]

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

            # IA: actualizar comportamiento de las especies (carnívoro persigue/ataca)
            self._update_ai()

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

    
        
