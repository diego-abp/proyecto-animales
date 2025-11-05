import pygame
import math
import time
import random

class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, tiempo_vida_max=100, sync_vida_with_tiempo=False, color=(255,255,255), size=15, is_baby=False):
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
        # Tiempo de vida (duración) y sincronización con HP
        self.tiempo_vida_max = tiempo_vida_max
        self.tiempo_vida_actual = tiempo_vida_max
        self.ultimo_update = time.time()
        self.sync_vida_with_tiempo = sync_vida_with_tiempo
        # Estado de huida/escape (usado por subclases que implementan huida)
        self.escape_state = None
        # Atributos para movimiento aleatorio
        self.last_random_move_time = time.time()
        self.random_move_delay = random.uniform(0.5, 2.5) # Desincronizar el primer movimiento
        self.random_move_target = None
        # Atributo para cooldown de reproducción
        self.ultimo_intento_reproduccion = 0
        # Atributos para crecimiento y apariencia
        self.color = color
        self.max_size = 15 # Tamaño adulto
        self.size = size
        self.is_baby = is_baby
        self.birth_time = time.time()
        self.growth_duration = 30 # Segundos para crecer a adulto
        # Atributo para el modo de apareamiento
        self.mating_mode = False
        # --- ATRIBUTOS DE "PERSONALIDAD" PARA MOVIMIENTO ÚNICO ---
        # Cada individuo tendrá valores ligeramente diferentes para que no se muevan igual.
        self.wander_speed_multiplier = random.uniform(0.8, 1.2) # Algunos pasean más rápido/lento
        self.wander_change_frequency_multiplier = random.uniform(0.7, 1.5) # Algunos cambian de dirección más/menos a menudo
        self.wander_pause_chance = random.uniform(0.001, 0.005) # Probabilidad de detenerse un momento
        self.is_paused = False
        self.pause_end_time = 0

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
        if next_x < 0: # Usar los límites de la nueva ventana
            next_x = 960
        elif next_x > 960:
            next_x = 0
        
        if next_y < 0: # Usar los límites de la nueva ventana
            next_y = 720
        elif next_y > 720:
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

        # --- Lógica de Pausa (Personalidad) ---
        if self.is_paused:
            if ahora > self.pause_end_time:
                self.is_paused = False
            else:
                return # No moverse mientras está en pausa
        elif random.random() < self.wander_pause_chance:
            self.is_paused = True
            self.pause_end_time = ahora + random.uniform(0.5, 1.5)

        # --- Lógica de Deambulación (si no está huyendo) ---
        ahora = time.time()
        # Si llega cerca del objetivo o ha pasado suficiente tiempo, elige uno nuevo.
        # Esto crea un movimiento más continuo y menos propenso a detenerse.
        dist_to_target = math.hypot(self.posicion_x - (self.random_move_target[0] if self.random_move_target else self.posicion_x), 
                                 self.posicion_y - (self.random_move_target[1] if self.random_move_target else self.posicion_y))

        if self.random_move_target is None or dist_to_target < 50 or ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            # El delay se ve afectado por la "personalidad" del animal
            self.random_move_delay = random.uniform(2, 5) * self.wander_change_frequency_multiplier
            # Elige un punto aleatorio en la pantalla
            self.random_move_target = (random.randint(0, screen_width), random.randint(0, screen_height))

        # Moverse hacia el objetivo aleatorio
        if self.random_move_target:
            self.mover_hacia(self.random_move_target[0], self.random_move_target[1], velocidad=self.salto * self.wander_speed_multiplier)

class Carnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=2, color=None, is_baby=False):
        # Los carnívoros tienen tiempo de vida medio (150). Se mueven más rápido para cazar.
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, tiempo_vida_max=150, color=color or (255, 0, 0), size=7 if is_baby else 15, is_baby=is_baby)
        # Atributos de ataque
        self.attack_power = 25
        self.attack_cooldown = 2.0
        self.last_attack = 0.0
        # Daño y cooldown especiales contra el jugador
        self.player_attack_power = 35
        self.player_attack_cooldown = 1.5
        # Estado y objetivos
        self.objetivo = None
        self.tiempo_busqueda = 0
        # Atributos para la IA de caza
        self.hunt_state = 'wandering'  # Estados: 'wandering', 'chasing'
        self.target = None
        self.detection_radius = 150  # Radio para empezar a cazar
        self.chase_radius = 250      # Radio para dejar de cazar si la presa escapa
        self.provoked_by_player = False # Se vuelve True si el jugador le ataca

    def mover(self, screen_width, screen_height, all_species):
        """
        IA del Carnívoro: Deambula, detecta presas, las caza con una estrategia de acecho y embestida,
        y pierde el interés si se alejan demasiado. Devuelve un dict {'damage', 'target'} si ataca.
        """
        ahora = time.time()

        # Si estamos en modo escape (heredado), respetarlo
        if getattr(self, 'escape_state', None) == 'escaping':
            super().mover(screen_width, screen_height, all_species)
            if self.escape_state == 'escaping':
                self.hunt_state = 'wandering'
                return None

        # --- Lógica de Apareamiento (si no está cazando ni huyendo) ---
        # Decide si entra en modo apareamiento aleatoriamente
        if self.hunt_state == 'wandering' and self.puede_reproducirse() and random.random() < 0.005:
            self.mating_mode = True
        
        # Si no puede reproducirse, sale del modo apareamiento
        if not self.puede_reproducirse():
            self.mating_mode = False

        if self.mating_mode:
            # Buscar una pareja viable
            pareja = self.buscar_pareja(all_species)
            if pareja:
                # Moverse hacia la pareja
                self.mover_hacia(pareja.posicion_x, pareja.posicion_y)
                return None # Prioridad es aparearse
            else:
                # No encontró pareja, vuelve a deambular
                self.mating_mode = False


        # Estados de la IA
        if self.hunt_state == 'wandering':
            if self.provoked_by_player and 'personaje' in all_species:
                self.target = all_species['personaje']
                self.hunt_state = 'chasing'
                return None

            # Buscar presas prioritarias: herbívoros, luego omnívoros
            posibles = []
            if 'herbivoro' in all_species:
                posibles.append(all_species['herbivoro'])
            if 'omnivoro' in all_species:
                posibles.append(all_species['omnivoro'])

            for prey in posibles:
                dist = math.hypot(self.posicion_x - prey.posicion_x, self.posicion_y - prey.posicion_y)
                if dist < self.detection_radius:
                    self.target = prey
                    self.hunt_state = 'chasing'
                    return None # Salir del método mover para procesar la caza en el siguiente frame
            # Si no se encontró presa, deambular
            super().mover(screen_width, screen_height, all_species)
            return None

        if self.hunt_state == 'chasing':
            if self.target is None or getattr(self.target, 'vida', 1) <= 0:
                self.hunt_state = 'wandering'
                self.target = None
                return None

            distancia = math.hypot(self.posicion_x - self.target.posicion_x, self.posicion_y - self.target.posicion_y)
            if distancia > self.chase_radius:
                self.hunt_state = 'wandering'
                self.target = None
                return None

            # Prepararse para atacar
            puede_atacar = (ahora - self.last_attack) >= self.attack_cooldown
            if distancia < 25 and puede_atacar:
                # Embestida: infligir daño y devolver info para que la vista lo muestre
                self.target.vida = max(0, self.target.vida - self.attack_power)
                self.last_attack = ahora
                return {'damage': self.attack_power, 'target': self.target}
            else:
                # Acecho/persecución
                velocidad = self.salto * (0.5 if 25 <= distancia < 75 else 1.0)
                self.mover_hacia(self.target.posicion_x, self.target.posicion_y, velocidad=velocidad)
                return None

    def puede_reproducirse(self):
        """Los carnívoros pueden reproducirse si tienen suficiente vida."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y):
        """Crea una nueva cría de Carnívoro."""
        # La cría nace con la mitad de la vida máxima de sus padres.
        vida_cria = self.vida_max // 2
        # Generar una tonalidad de color ligeramente diferente
        r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
        g = max(0, min(255, self.color[1] + random.randint(-30, 30)))
        b = max(0, min(255, self.color[2] + random.randint(-30, 30)))
        color_cria = (r, g, b)
        # Los padres pierden algo de vida al reproducirse
        self.vida -= self.vida_max * 0.25
        return Carnivoro(x, y, vida_cria, color=color_cria, is_baby=True)

    def buscar_pareja(self, all_species):
        """Busca otra instancia de la misma clase para reproducirse."""
        mejor_pareja = None
        distancia_min = float('inf')
        for nombre, otra_especie in all_species.items():
            if (isinstance(otra_especie, Carnivoro) and 
                otra_especie is not self and 
                hasattr(otra_especie, 'puede_reproducirse') and 
                otra_especie.puede_reproducirse()):
                
                dist = math.hypot(self.posicion_x - otra_especie.posicion_x, self.posicion_y - otra_especie.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = otra_especie
        return mejor_pareja

class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4, color=None, is_baby=False):
        # Los herbívoros tienen tiempo de vida largo (120)
        super().__init__(x, y, vida, reproducirse, salto, False, True, True, color=color or (0, 200, 0), size=7 if is_baby else 15, is_baby=is_baby)

    def puede_reproducirse(self):
        """Los herbívoros pueden reproducirse si tienen suficiente vida."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y):
        """Crea una nueva cría de Herbívoro."""
        # La cría nace con la mitad de la vida máxima de sus padres.
        vida_cria = self.vida_max // 2
        # Generar una tonalidad de color ligeramente diferente
        r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
        g = max(0, min(255, self.color[1] + random.randint(-20, 20)))
        b = max(0, min(255, self.color[2] + random.randint(-30, 30)))
        color_cria = (r, g, b)
        # Los padres pierden algo de vida al reproducirse
        self.vida -= self.vida_max * 0.25
        return Herbivoro(x, y, vida_cria, color=color_cria, is_baby=True)

    def mover(self, screen_width, screen_height, all_species={}):
        """El herbívoro deambula y huye, pero también busca pareja activamente."""
        # La lógica de huida de la clase base tiene prioridad
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, all_species)
            if self.escape_state == 'escaping': # Comprobar si sigue huyendo
                self.mating_mode = False # Si huye, no se aparea
                return

        # --- Lógica de Apareamiento ---
        if self.puede_reproducirse() and random.random() < 0.005: # Probabilidad de entrar en modo apareamiento
            self.mating_mode = True
        
        if not self.puede_reproducirse():
            self.mating_mode = False

        if self.mating_mode:
            pareja = self.buscar_pareja(all_species)
            if pareja:
                self.mover_hacia(pareja.posicion_x, pareja.posicion_y)
                return # Prioridad es aparearse
            else:
                self.mating_mode = False # No encontró pareja

        # Si no está huyendo ni buscando pareja, deambula
        super().mover(screen_width, screen_height, all_species)

    def buscar_pareja(self, all_species):
        """Busca otra instancia de Herbivoro para reproducirse."""
        mejor_pareja = None
        distancia_min = float('inf')
        for nombre, otra_especie in all_species.items():
            if (isinstance(otra_especie, Herbivoro) and otra_especie is not self and 
                hasattr(otra_especie, 'puede_reproducirse') and otra_especie.puede_reproducirse()):
                dist = math.hypot(self.posicion_x - otra_especie.posicion_x, self.posicion_y - otra_especie.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = otra_especie
        return mejor_pareja

class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=3, color=None, is_baby=False):
        # Los omnívoros tienen tiempo de vida equilibrado (100)
        # El tamaño se usa como radio, así que un omnívoro de 20x20 tiene un "radio" de 10
        super().__init__(x, y, vida, reproducirse, salto=salto, atacar=True, correr=True, comer=True, color=color or (128, 0, 128), size=5 if is_baby else 10, is_baby=is_baby)
        self.max_size = 10 # Tamaño adulto (radio)
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
                self.mating_mode = False # Si huye, no se aparea
                return

        # --- Lógica de Apareamiento (si no está cazando ni huyendo) ---
        if not self.modo_caza and self.puede_reproducirse() and random.random() < 0.005:
            self.mating_mode = True
        
        if not self.puede_reproducirse():
            self.mating_mode = False

        if self.mating_mode:
            pareja = self.buscar_pareja(posibles_presas)
            if pareja:
                self.mover_hacia(pareja.posicion_x, pareja.posicion_y)
                return # Prioridad es aparearse
            else:
                self.mating_mode = False

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
                super().mover(screen_width, screen_height, posibles_presas)
        else:
            # Comportamiento de recolección (similar al herbívoro)
            super().mover(screen_width, screen_height, posibles_presas)

    def puede_reproducirse(self):
        """Los omnívoros pueden reproducirse si tienen suficiente vida."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y):
        """Crea una nueva cría de Omnívoro."""
        # La cría nace con la mitad de la vida máxima de sus padres.
        vida_cria = self.vida_max // 2
        # Generar una tonalidad de color ligeramente diferente
        r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
        g = max(0, min(255, self.color[1] + random.randint(-30, 30)))
        b = max(0, min(255, self.color[2] + random.randint(-20, 20)))
        color_cria = (r, g, b)
        # Los padres pierden algo de vida al reproducirse
        self.vida -= self.vida_max * 0.25
        return Omnivoro(x, y, vida_cria, color=color_cria, is_baby=True)

    def buscar_pareja(self, all_species):
        """Busca otra instancia de Omnivoro para reproducirse."""
        mejor_pareja = None
        distancia_min = float('inf')
        for nombre, otra_especie in all_species.items():
            if (isinstance(otra_especie, Omnivoro) and 
                otra_especie is not self and 
                hasattr(otra_especie, 'puede_reproducirse') and 
                otra_especie.puede_reproducirse()):
                dist = math.hypot(self.posicion_x - otra_especie.posicion_x, self.posicion_y - otra_especie.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = otra_especie
        return mejor_pareja

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
            self.posicion_y = 720
        else:
            self.posicion_y = next_y

    def mover_abajo(self):
        salto = self.salto + self.velocidad_extra
        next_y = self.posicion_y + salto
        if next_y > 720:
            self.posicion_y = 0
        else:
            self.posicion_y = next_y

    def mover_derecha(self):
        salto = self.salto + self.velocidad_extra
        next_x = self.posicion_x + salto
        if next_x > 960:
            self.posicion_x = 0
        else:
            self.posicion_x = next_x

    def mover_izquierda(self):
        salto = self.salto + self.velocidad_extra
        next_x = self.posicion_x - salto
        if next_x < 0:
            self.posicion_x = 960
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
    def __init__(self, ancho=960, alto=720, fps=30):
        pygame.init()
        self.ancho = ancho
        self.alto = alto
        self.screen = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Juego - Proyecto Especies")
        self.clock = pygame.time.Clock()
        self.fps = fps

        # --- Generación Procedural de Entidades ---
        self.especies_vivas = {}
        entidades_a_crear = [
            (Carnivoro, "carnivoro", 2),
            (Herbivoro, "herbivoro", 2),
            (Omnivoro, "omnivoro", 2),
            (Planta, "planta", 10)
        ]
        
        min_dist_entidades = 100 # Distancia mínima entre cualquier par de entidades

        for clase_entidad, nombre_base, cantidad in entidades_a_crear:
            for i in range(cantidad):
                intentos = 0
                while intentos < 100: # Evitar bucles infinitos
                    x = random.randint(20, self.ancho - 20)
                    y = random.randint(20, self.alto - 20)
                    
                    # Comprobar distancia con todas las entidades ya creadas
                    demasiado_cerca = False
                    for entidad_existente in self.especies_vivas.values():
                        if math.hypot(x - entidad_existente.posicion_x, y - entidad_existente.posicion_y) < min_dist_entidades:
                            demasiado_cerca = True
                            break
                    
                    if not demasiado_cerca:
                        nombre_unico = f"{nombre_base}_{i+1}"
                        if issubclass(clase_entidad, Planta):
                            self.especies_vivas[nombre_unico] = clase_entidad(x, y)
                        else: # Para animales
                            self.especies_vivas[nombre_unico] = clase_entidad(x, y, 100, is_baby=False)
                        break
                    intentos += 1

        # Añadir plantas en posiciones aleatorias, asegurando que no estén demasiado juntas

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
                            damage_dealt = self.personaje.attack_power
                            especie.take_damage(self.personaje, self.personaje.attack_power)
                            self.damage_popups.append({
                                'text': f"-{int(damage_dealt)}",
                                'x': especie.posicion_x, 'y': especie.posicion_y - 10, 'start': pygame.time.get_ticks()})
                            # Solo ataca a un objetivo por pulsación
                            break
    def _draw_hp_bar(self, entity, y_offset=-20, width=36, height=6, color_healthy=(0,200,0), color_low=(200,0,0), low_threshold=0.3):
        """Dibuja una barra de vida simple sobre una entidad."""
        try:
            hp_percent = max(0.0, min(1.0, entity.vida / entity.vida_max))
        except Exception:
            return
        x = int(entity.posicion_x - width // 2)
        y = int(entity.posicion_y + y_offset)
        # Fondo
        pygame.draw.rect(self.screen, (50,50,50), (x, y, width, height))
        # Color según porcentaje
        color = color_healthy if hp_percent > low_threshold else color_low
        # Barra de vida
        pygame.draw.rect(self.screen, color, (x, y, int(width * hp_percent), height))

    def check_reproduction(self):
        """Verifica y maneja la reproducción de las especies."""
        nuevas_especies = {}
        # Obtener el tiempo actual para el cooldown
        tiempo_actual = time.time()
        
        for nombre, especie in self.especies_vivas.items():
            # Verificar cooldown de reproducción
            if hasattr(especie, 'ultimo_intento_reproduccion'):
                if tiempo_actual - especie.ultimo_intento_reproduccion < 10:  # 10 segundos de cooldown
                    continue
            
            # Comprobar si hay otras especies del mismo tipo cerca
            for otro_nombre, otra_especie in self.especies_vivas.items():
                # Condiciones para reproducirse:
                # 1. No ser la misma instancia.
                # 2. Ser de la misma clase (Carnivoro con Carnivoro, etc.).
                # 3. Ambos deben tener suficiente vida para reproducirse.
                if (especie is not otra_especie and 
                    isinstance(otra_especie, type(especie)) and
                    hasattr(especie, 'puede_reproducirse') and especie.puede_reproducirse() and 
                    hasattr(otra_especie, 'puede_reproducirse') and otra_especie.puede_reproducirse()):
                    
                    # Verificar que no se exceda el límite de población para este tipo de especie
                    # Solo puede haber una cría a la vez por tipo de especie.
                    # Si ya hay una cría de este tipo, no se puede crear otra.
                    hay_cria_existente = any(
                        isinstance(e, type(especie)) and getattr(e, 'is_baby', False) for e in self.especies_vivas.values())
                    if hay_cria_existente:
                        continue

                    # Calcular distancia entre las dos especies
                    dist = math.hypot(especie.posicion_x - otra_especie.posicion_x,
                                      especie.posicion_y - otra_especie.posicion_y)
                    
                    # Si están lo suficientemente cerca, se reproducen
                    if dist < 30:  # Distancia más corta para reproducción (casi tocándose)
                        # Posición aleatoria cercana para la nueva especie
                        new_x = especie.posicion_x + random.randint(-30, 30)
                        new_y = especie.posicion_y + random.randint(-30, 30)
                        
                        # Mantener dentro de los límites
                        new_x = max(0, min(new_x, self.ancho))
                        new_y = max(0, min(new_y, self.alto))
                        
                        nueva_especie = especie.reproducir(new_x, new_y)
                        if nueva_especie:
                            # Actualizar el tiempo del último intento de reproducción
                            especie.ultimo_intento_reproduccion = tiempo_actual
                            otra_especie.ultimo_intento_reproduccion = tiempo_actual
                            
                            # --- SEPARACIÓN POST-REPRODUCCIÓN ---
                            # Empujar a los padres en direcciones opuestas para que no se queden atascados.
                            # Y también a la cría para que no aparezca encima de ellos.
                            push_force_parents = 30
                            push_force_baby = 40
                            dx = especie.posicion_x - otra_especie.posicion_x
                            dy = especie.posicion_y - otra_especie.posicion_y
                            
                            # Normalizar el vector de empuje
                            if dist > 0:
                                # Empujar a los padres
                                push_x = (dx / dist) * push_force_parents
                                push_y = (dy / dist) * push_force_parents
                                especie.posicion_x += push_x
                                especie.posicion_y += push_y
                                otra_especie.posicion_x -= push_x
                                otra_especie.posicion_y -= push_y
                                
                                # Empujar a la cría lejos del punto medio de los padres
                                # Usamos un vector perpendicular para que no salga en la misma línea
                                nueva_especie.posicion_x -= push_y * (push_force_baby / push_force_parents)
                                nueva_especie.posicion_y += push_x * (push_force_baby / push_force_parents)

                            # Salir del modo de apareamiento
                            especie.mating_mode = False
                            otra_especie.mating_mode = False
                            # Generar un nuevo nombre único para la especie
                            base_name = especie.__class__.__name__.lower()
                            new_name = f"{base_name}_{len(self.especies_vivas) + len(nuevas_especies)}"
                            nuevas_especies[new_name] = nueva_especie
                            
                            # Crear un popup visual para la reproducción
                            self.damage_popups.append({
                                'text': "<3",
                                'x': especie.posicion_x,
                                'y': especie.posicion_y - 10,
                                'start': pygame.time.get_ticks()
                            })
                            # Salir del bucle interior para evitar que una misma especie se reproduzca varias veces en un frame
                            break
        # Añadir las nuevas especies a la lista principal
        self.especies_vivas.update(nuevas_especies)

    def _resolve_collisions(self):
        """Resuelve las colisiones entre entidades de la misma especie para que no se superpongan."""
        # Obtener todas las entidades móviles
        movable_entities = [e for e in self.especies_vivas.values() if not isinstance(e, Planta)]
        
        # Iterar sobre todos los pares de entidades
        for i in range(len(movable_entities)):
            for j in range(i + 1, len(movable_entities)):
                entity1 = movable_entities[i]
                entity2 = movable_entities[j]

                # Solo comprobar colisiones entre individuos de la misma clase
                if type(entity1) is type(entity2):
                    dist = math.hypot(entity1.posicion_x - entity2.posicion_x, entity1.posicion_y - entity2.posicion_y)
                    
                    # El tamaño se usa como radio para las especies circulares. Para el omnívoro (cuadrado), es una aproximación.
                    combined_radius = entity1.size + entity2.size
                    
                    if dist < combined_radius:
                        # Hay una colisión, empujarlos para separarlos
                        overlap = combined_radius - dist
                        
                        # Evitar división por cero si están exactamente en el mismo punto
                        if dist == 0:
                            dist = 0.1
                            entity1.posicion_x += 0.1 # Mover uno ligeramente

                        # Calcular el vector de empuje (normalizado)
                        push_x = (entity1.posicion_x - entity2.posicion_x) / dist
                        push_y = (entity1.posicion_y - entity2.posicion_y) / dist
                        
                        # Mover cada entidad la mitad de la superposición
                        move_amount = overlap / 2
                        
                        entity1.posicion_x += push_x * move_amount
                        entity2.posicion_x -= push_x * move_amount
                        
                        entity1.posicion_y += push_y * move_amount
                        entity2.posicion_y -= push_y * move_amount

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

    def _update_growth(self):
        """Gestiona el crecimiento de las crías."""
        ahora = time.time()
        for especie in self.especies_vivas.values():
            if getattr(especie, 'is_baby', False):
                tiempo_transcurrido = ahora - especie.birth_time
                if tiempo_transcurrido >= especie.growth_duration:
                    especie.is_baby = False
                    especie.size = especie.max_size
                else:
                    # Interpolar linealmente el tamaño
                    progreso = tiempo_transcurrido / especie.growth_duration
                    tamaño_inicial = especie.max_size / 2
                    especie.size = tamaño_inicial + (especie.max_size - tamaño_inicial) * progreso
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
                # Dibuja contorno negro y luego el relleno
                pygame.draw.circle(self.screen, (0,0,0), (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size) + 1)
                pygame.draw.circle(self.screen, especie.color, (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size))
                self._draw_hp_bar(especie)
            elif isinstance(especie, Herbivoro):
                # Dibuja contorno negro y luego el relleno
                pygame.draw.circle(self.screen, (0,0,0), (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size) + 1)
                pygame.draw.circle(self.screen, especie.color, (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size))
                self._draw_hp_bar(especie)
            elif isinstance(especie, Omnivoro):
                omni_size = int(especie.size) * 2 # El tamaño es el radio, el lado del cuadrado es el diámetro
                omni_x = int(especie.posicion_x) - omni_size // 2
                omni_y = int(especie.posicion_y) - omni_size // 2
                # Dibuja contorno negro y luego el relleno
                pygame.draw.rect(self.screen, (0,0,0), (omni_x - 1, omni_y - 1, omni_size + 2, omni_size + 2))
                pygame.draw.rect(self.screen, especie.color, (omni_x, omni_y, omni_size, omni_size))
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
        self.screen.blit(instrucciones, (10, self.alto - 25)) # Se ajusta automáticamente con self.alto

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

            # Resolver colisiones entre especies
            self._resolve_collisions()

            # Verificar si alguna especie puede reproducirse
            self.check_reproduction()

            # Actualizar lógica de curación de las plantas
            self._update_plant_healing()

            # Actualizar crecimiento de las crías
            self._update_growth()

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

    
        
