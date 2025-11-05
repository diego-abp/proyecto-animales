import pygame
import math
import time
import random

class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False):
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
        # Atributos para movimiento aleatorio
        self.last_random_move_time = time.time()
        self.random_move_delay = random.uniform(1, 3) # Cambiar de dirección cada 1-3 segundos
        self.random_move_target = None
        # Atributos para contraataque y huida
        self.escape_state = 'none' # 'none', 'escaping'
        self.escape_target = None
        self.escape_end_time = 0
        self.counter_attack_power = 5
        self.pushback_force = 25

    def take_damage(self, attacker, damage):
        """Aplica daño a la especie y activa un contraataque/huida."""
        self.vida -= damage
        if self.vida > 0 and attacker is not None:
            # Contraatacar: empujar y dañar levemente al atacante
            if hasattr(attacker, 'vida'):
                attacker.vida -= self.counter_attack_power
            
            dx = attacker.posicion_x - self.posicion_x
            dy = attacker.posicion_y - self.posicion_y
            dist = math.hypot(dx, dy)
            if dist > 0:
                attacker.posicion_x += (dx / dist) * self.pushback_force
                attacker.posicion_y += (dy / dist) * self.pushback_force

            # Entrar en estado de huida
            self.escape_state = 'escaping'
            self.escape_target = attacker
            self.escape_end_time = time.time() + 3 # Huir durante 3 segundos

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
        next_x = self.posicion_x + nx * velocidad
        next_y = self.posicion_y + ny * velocidad

        # Wrap (coincide con límites usados en Personaje)
        if next_x < 0:
            next_x = 490
        elif next_x > 490:
            next_x = 0
        
        if next_y < 0:
            next_y = 360
        elif next_y > 360:
            next_y = 0

        # Actualizar la posición final después de comprobar el wrap
        self.posicion_x = next_x
        self.posicion_y = next_y

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Comportamiento de movimiento base: deambular aleatoriamente."""
        ahora = time.time()

        # --- Lógica de Huida (Prioridad Máxima) ---
        if self.escape_state == 'escaping':
            if ahora > self.escape_end_time or self.escape_target is None or self.escape_target.vida <= 0:
                self.escape_state = 'none' # Terminar huida
                self.escape_target = None
            else:
                # --- CORRECCIÓN DEL BUG DE PARPADEO ---
                # En lugar de calcular un punto de destino, calculamos la dirección de escape
                # y aplicamos el movimiento directamente. Esto evita el parpadeo en los bordes.
                dx = self.posicion_x - self.escape_target.posicion_x
                dy = self.posicion_y - self.escape_target.posicion_y
                dist = math.hypot(dx, dy)
                velocidad_escape = self.salto * 1.2
                if dist > 0:
                    # Moverse directamente en la dirección opuesta al atacante
                    self.mover_hacia(self.posicion_x + dx, self.posicion_y + dy, velocidad=velocidad_escape)
                return # Durante la huida, no hacer nada más

        # --- Lógica de Deambulación (si no está huyendo) ---
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
    def __init__(self, x, y, vida, reproducirse=True, salto=3.5):
        # Los carnívoros tienen tiempo de vida medio (80). Son más rápidos para cazar.
        super().__init__(x, y, vida, reproducirse, salto, True, True, True)
        # Atributos de ataque: menos daño por golpe y cooldown mayor (no mata de un golpe)
        self.attack_power = 25
        self.attack_cooldown = 2.0  # segundos entre ataques
        self.last_attack = 0.0      # timestamp del último ataque

        # Atributos para la IA de caza
        self.hunt_state = 'wandering'  # Estados: 'wandering', 'chasing'
        self.target = None
        self.detection_radius = 150  # Radio para empezar a cazar
        self.chase_radius = 250      # Radio para dejar de cazar si la presa escapa
        self.provoked_by_player = False # Se vuelve True si el jugador le ataca

    def mover(self, screen_width, screen_height, all_species):
        """
        IA del Carnívoro: Deambula, detecta presas, las caza con una estrategia de acecho y embestida,
        y pierde el interés si se alejan demasiado.
        """
        ahora = time.time()

        # La lógica de huida de la clase base tiene prioridad
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, all_species)
            if self.escape_state == 'escaping': # Comprobar si sigue huyendo
                self.hunt_state = 'wandering' # Si huye, interrumpe la caza
                return

        # --- Lógica de Estados ---
        if self.hunt_state == 'wandering':
            # 1. Deambular aleatoriamente
            super().mover(screen_width, screen_height)
            
            # 2. Buscar presas.
            possible_targets = []
            # Si está provocado, el jugador es la máxima prioridad.
            if self.provoked_by_player and 'personaje' in all_species:
                self.target = all_species['personaje']
                self.hunt_state = 'chasing'
                return # Cambia a modo caza inmediatamente

            # Si no está provocado, busca otras presas (no al jugador).
            if 'herbivoro' in all_species: possible_targets.append(all_species['herbivoro'])
            if 'omnivoro' in all_species: possible_targets.append(all_species['omnivoro'])
            # Descomentar la siguiente línea para que ataque al jugador si está provocado, incluso mientras deambula.
            # if self.provoked_by_player and 'personaje' in all_species:
            #     possible_targets.insert(0, all_species['personaje']) # Prioridad al jugador

            for prey in possible_targets:
                dist = math.hypot(self.posicion_x - prey.posicion_x, self.posicion_y - prey.posicion_y)
                if dist < self.detection_radius:
                    self.target = prey
                    self.hunt_state = 'chasing'
                    break # Encontró un objetivo, deja de buscar

        elif self.hunt_state == 'chasing':
            # Verificar si el objetivo sigue siendo válido o si el jugador lo ha provocado
            if self.target is None or self.target.vida <= 0:
                self.hunt_state = 'wandering'
                self.target = None
                return

            distancia = math.hypot(self.posicion_x - self.target.posicion_x, self.posicion_y - self.target.posicion_y)

            # Si la presa escapa del radio de persecución, pierde el interés
            if distancia > self.chase_radius:
                self.hunt_state = 'wandering'
                self.target = None
                return

            # Lógica de acecho y embestida
            velocidad_actual = self.salto
            puede_atacar = ahora - self.last_attack >= self.attack_cooldown

            if distancia < 25 and puede_atacar:
                # Embestida de ataque
                self.mover_hacia(self.target.posicion_x, self.target.posicion_y, velocidad=self.salto * 2.5)
                # Aplicar daño a través del nuevo método para activar contraataque
                self.target.take_damage(self, self.attack_power)
                self.last_attack = ahora
                # Devolvemos el daño para que la vista lo muestre
                return {'damage': self.attack_power, 'target': self.target}
            else:
                # Acecho o persecución normal
                if 25 <= distancia < 75:
                    velocidad_actual *= 0.5  # Acecho
                self.mover_hacia(self.target.posicion_x, self.target.posicion_y, velocidad=velocidad_actual)

class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los herbívoros tienen tiempo de vida largo (120)
        super().__init__(x, y, vida, reproducirse, salto, False, True, True)

class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los omnívoros tienen tiempo de vida equilibrado (100)
        super().__init__(x, y, vida, reproducirse, salto=3, atacar=True, correr=True, comer=True)
        self.presa = None
        self.modo_caza = False # Alterna entre cazar y deambular

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """
        Comportamiento mixto: a veces caza, a veces deambula tranquilamente.
        """
        # La lógica de huida de la clase base tiene prioridad
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, posibles_presas)
            if self.escape_state == 'escaping': # Comprobar si sigue huyendo
                return

        ahora = time.time()
        if ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            # 50% de probabilidad de cambiar de modo (caza/deambular)
            if random.random() < 0.5:
                self.modo_caza = not self.modo_caza
                self.presa = None # Olvida la presa al cambiar de modo

        if self.modo_caza:
            # Comportamiento de caza (similar al carnívoro pero menos agresivo)
            if self.presa and (self.presa not in posibles_presas.values() or self.presa.vida <= 0):
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
    def __init__(self, x, y, reproducirse=False):
        # Las plantas son permanentes. No tienen vida ni tiempo de vida.
        # Pasamos valores dummy a la clase base y desactivamos la reproducción por ahora.
        super().__init__(x, y, float('inf'), reproducirse, 0, False, False, False)
        # Atributos para la curación
        self.healing_target = None
        self.time_on_plant = 0
        self.is_healing = False
        self.heal_amount = 5  # Puntos de vida por segundo
        self.heal_cooldown = 1.0 # Cura cada segundo
        self.last_heal_time = 0

    # El método mover de la clase base (deambular) no se aplica a las plantas estáticas.
        
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
        self.vida_max = vida
        self.salto = 2
        self.velocidad_extra = 0
        self.ticks_velocidad = 0

        # Atributos de animación
        self.state = self.IDLE_DOWN
        self.direction = 'down' # 'down', 'up', 'left', 'right'
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100 # ms por cuadro

        # Atributos de ataque del jugador
        self.attack_power = 30
        self.attack_range = 40
        self.attack_cooldown = 1.0 # 1 segundo
        self.last_attack_time = 0

    def take_damage(self, attacker, damage):
        """El jugador solo recibe daño, no contraataca automáticamente."""
        self.vida -= damage
        # Aquí se podría añadir un efecto visual o sonoro para el jugador al ser golpeado.

    def update_animation(self, animation_strip):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.frame_index = (self.frame_index + 1) % len(animation_strip)

    def mover_arriba(self):
        salto = self.salto + self.velocidad_extra
        next_y = self.posicion_y - salto
        if next_y < 0:
            self.posicion_y = 360 # Aparece en el borde opuesto
        else:
            self.posicion_y = next_y

    def mover_abajo(self):
        salto = self.salto + self.velocidad_extra
        next_y = self.posicion_y + salto
        if next_y > 360:
            self.posicion_y = 0 # Aparece en el borde opuesto
        else:
            self.posicion_y = next_y

    def mover_derecha(self):
        salto = self.salto + self.velocidad_extra
        next_x = self.posicion_x + salto
        if next_x > 490:
            self.posicion_x = 0 # Aparece en el borde opuesto
        else:
            self.posicion_x = next_x

    def mover_izquierda(self):
        salto = self.salto + self.velocidad_extra
        next_x = self.posicion_x - salto
        if next_x < 0:
            self.posicion_x = 490 # Aparece en el borde opuesto
        else:
            self.posicion_x = next_x

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
        # Añadir varias plantas en posiciones aleatorias
        num_plantas = 10
        for i in range(num_plantas):
            x = random.randint(20, self.ancho - 20)
            y = random.randint(20, self.alto - 20)
            self.especies_vivas[f'planta_{i}'] = Planta(x, y)

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
            # --- Lógica de ataque del jugador ---
            elif event.key == pygame.K_SPACE:
                ahora = time.time()
                if ahora - self.personaje.last_attack_time >= self.personaje.attack_cooldown:
                    self.personaje.last_attack_time = ahora
                    # Buscar un objetivo en rango
                    for nombre, especie in self.especies_vivas.items():
                        dist = math.hypot(self.personaje.posicion_x - especie.posicion_x, self.personaje.posicion_y - especie.posicion_y)
                        if dist < self.personaje.attack_range:
                            # El jugador ataca a la especie
                            especie.take_damage(self.personaje, self.personaje.attack_power)
                            self.damage_popups.append({
                                'text': f"-{int(especie.counter_attack_power)}",
                                'x': self.personaje.posicion_x, 'y': self.personaje.posicion_y - 10, 'start': pygame.time.get_ticks()})

                            self.damage_popups.append({
                                'text': f"-{int(self.personaje.attack_power)}",
                                'x': especie.posicion_x,
                                'y': especie.posicion_y - 10,
                                'start': pygame.time.get_ticks()
                            })

                            # Si el objetivo es un carnívoro, provocarlo
                            if isinstance(especie, Carnivoro):
                                especie.provoked_by_player = True
                                # Forzar cambio de objetivo al jugador
                                especie.target = self.personaje
                                especie.hunt_state = 'chasing'
                            break # Ataca solo a un objetivo por pulsación
    
    def _draw_hp_bar(self, entity, y_offset=-25, color_healthy=(0, 200, 0), color_low=(200, 0, 0), low_threshold=0.3):
        """Dibuja una barra de vida sobre una entidad."""
        if not hasattr(entity, 'vida') or not hasattr(entity, 'vida_max') or entity.vida_max == 0:
            return

        hp_percent = entity.vida / entity.vida_max
        bar_width = 30
        bar_height = 5
        x = entity.posicion_x - bar_width / 2
        y = entity.posicion_y + y_offset

        # Color de la barra según el porcentaje de vida
        color = color_healthy if hp_percent > low_threshold else color_low

        # Dibujar fondo de la barra (rojo oscuro o gris)
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, bar_width, bar_height))
        # Dibujar barra de vida actual
        pygame.draw.rect(self.screen, color, (x, y, bar_width * hp_percent, bar_height))

    def _update_plant_healing(self):
        """Gestiona la lógica de curación de las plantas."""
        ahora = time.time()
        all_entities = list(self.especies_vivas.values()) + [self.personaje]
        
        # Separar plantas de otras entidades
        plants = [e for e in self.especies_vivas.values() if isinstance(e, Planta)]
        movable_entities = [e for e in all_entities if not isinstance(e, Planta)]

        for plant in plants:
            current_target = None
            # Comprobar si alguna entidad está sobre la planta
            for entity in movable_entities:
                dist = math.hypot(plant.posicion_x - entity.posicion_x, plant.posicion_y - entity.posicion_y)
                if dist < 15: # Radio de contacto
                    current_target = entity
                    break
            
            if current_target:
                if plant.healing_target is current_target:
                    # La misma entidad sigue en la planta, acumular tiempo
                    plant.time_on_plant += self.clock.get_time() / 1000.0
                else:
                    # Nueva entidad en la planta, reiniciar temporizador
                    plant.healing_target = current_target
                    plant.time_on_plant = 0
                    plant.is_healing = False

                # Si ha estado 2 segundos, empezar a curar
                if plant.time_on_plant >= 2 and not plant.is_healing:
                    plant.is_healing = True
                    plant.last_heal_time = ahora # Iniciar curación inmediatamente

                if plant.is_healing and ahora - plant.last_heal_time >= plant.heal_cooldown:
                    plant.last_heal_time = ahora
                    target = plant.healing_target
                    target.vida = min(target.vida_max, target.vida + plant.heal_amount)
            else:
                # Nadie en la planta, resetear estado
                plant.healing_target = None
                plant.time_on_plant = 0
                plant.is_healing = False

    def _update_ai(self):
        """Actualiza el comportamiento de las especies controladas por IA."""
        # Crear un diccionario con todas las entidades "atacables" para la IA
        all_entities = self.especies_vivas.copy()
        all_entities['personaje'] = self.personaje

        # Iteramos sobre una copia de los items para poder modificar el diccionario original
        # de forma segura (p. ej., al eliminar una especie que ha muerto).
        for nombre, especie in list(self.especies_vivas.items()):
            # Las plantas no se mueven
            if isinstance(especie, Planta):
                continue
            # El método mover puede devolver información sobre el ataque
            attack_info = especie.mover(self.ancho, self.alto, all_entities)

            if attack_info and isinstance(especie, Carnivoro):
                # El carnívoro atacó, procesamos el resultado
                target = attack_info['target']
                damage = attack_info['damage']

                # Crear popup de daño
                self.damage_popups.append({
                    'text': f"-{int(damage)}",
                    'x': target.posicion_x,
                    'y': target.posicion_y - 10,
                    'start': pygame.time.get_ticks()
                })

                # Verificar si el objetivo murió
                if target.vida <= 0:
                    if target is self.personaje:
                        self.running = False
                    else:
                        # Eliminar cualquier tipo de especie que haya muerto
                        # Buscamos la clave del diccionario para eliminarla de forma segura
                        for key, value in list(self.especies_vivas.items()):
                            if value is target:
                                del self.especies_vivas[key]
                                break

    def draw(self):
        # Fondo
        self.screen.fill((255, 255, 255))
        especies_muertas = []
        
        # Comprobar qué especies han muerto por daño y marcarlas para eliminar
        for nombre, especie in list(self.especies_vivas.items()):
            if hasattr(especie, 'vida') and especie.vida <= 0:
                especies_muertas.append(nombre)

        # Eliminar especies muertas
        for nombre in especies_muertas:
            del self.especies_vivas[nombre]

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
        
        # Dibujar barra de vida sobre el jugador
        self._draw_hp_bar(self.personaje, y_offset=-10, color_healthy=(0, 100, 255))

        # Dibujar especies vivas
        for nombre, especie in self.especies_vivas.items():
            if isinstance(especie, Carnivoro):
                pygame.draw.circle(self.screen, (255, 0, 0), 
                                (int(especie.posicion_x), int(especie.posicion_y)), 15)
                self._draw_hp_bar(especie)
            elif isinstance(especie, Herbivoro):
                pygame.draw.circle(self.screen, (0, 200, 0), 
                                (int(especie.posicion_x), int(especie.posicion_y)), 15)
                self._draw_hp_bar(especie)
            elif isinstance(especie, Omnivoro):
                omni_size = 20
                omni_x = int(especie.posicion_x) - omni_size // 2
                omni_y = int(especie.posicion_y) - omni_size // 2
                pygame.draw.rect(self.screen, (128, 0, 128), 
                              (omni_x, omni_y, omni_size, omni_size))
                self._draw_hp_bar(especie)
            elif isinstance(especie, Planta):
                # Dibujar la planta como un triángulo verde con un contorno negro
                color_contorno = (0, 255, 0) if especie.is_healing else (0, 0, 0)
                p1 = (int(especie.posicion_x), int(especie.posicion_y) - 8)
                p2 = (int(especie.posicion_x) - 8, int(especie.posicion_y) + 8)
                p3 = (int(especie.posicion_x) + 8, int(especie.posicion_y) + 8)
                # Primero el relleno verde
                pygame.draw.polygon(self.screen, (0, 100, 0), [p1, p2, p3])
                # Luego el contorno (negro por defecto, verde brillante si está curando)
                pygame.draw.polygon(self.screen, color_contorno, [p1, p2, p3], 2)

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
        instrucciones = self.font.render("Flechas/WASD = mover, Espacio = atacar, ESC = salir", True, (0, 0, 150))
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

            # IA: actualizar comportamiento de las especies (carnívoro persigue/ataca)
            self._update_ai()

            # Actualizar lógica de curación de las plantas
            self._update_plant_healing()

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

    
        
