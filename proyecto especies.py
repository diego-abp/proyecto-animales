import pygame
import math
import time
import random

class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, tiempo_vida_max=100, sync_vida_with_tiempo=False, color=(255,255,255), size=15, is_baby=False, is_champion=False):
        self.posicion_x = x
        self.posicion_y = y
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
        # Estado de huida/escape 
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
        self.is_champion = is_champion
        self.birth_time = time.time()
        self.growth_duration = 30 # Segundos para crecer a adulto
        # Atributo para el modo de apareamiento
        self.mating_mode = False
        self.emergency_partner = None # Para saber a quién buscar en emergencia
        self.emergency_mating_mode = False # Nuevo modo para cruce de especies
        # Cada individuo tendrá valores ligeramente diferentes para que no se muevan igual.
        self.wander_speed_multiplier = random.uniform(0.8, 1.2) # Algunos pasean más rápido/lento
        self.wander_change_frequency_multiplier = random.uniform(0.7, 1.5) # Algunos cambian de dirección más/menos a menudo
        self.wander_pause_chance = random.uniform(0.001, 0.005) # Probabilidad de detenerse un momento
        self.is_paused = False
        self.pause_end_time = 0
        # Atributos de contraataque
        self.counter_attack_power = 1
        self.pushback_force = 40 # Fuerza de empuje al ser atacado

    def update_vida_por_tiempo(self):
        if self.vida == float('inf') or self.tiempo_vida_max <= 0:
            return

        ahora = time.time()
        tiempo_transcurrido = ahora - self.ultimo_update
        self.ultimo_update = ahora
        self.vida -= (self.vida_max / self.tiempo_vida_max) * tiempo_transcurrido

    def take_damage(self, attacker, damage):
        """Aplica daño a la especie y activa un contraataque/huida."""
        self.vida -= damage
        if self.vida > 0 and attacker is not None:
            # Contraatacar: empujar y dañar levemente al atacante
            if hasattr(attacker, 'vida'):
                attacker.vida = max(0, attacker.vida - self.counter_attack_power)
            
            dx = attacker.posicion_x - self.posicion_x
            dy = attacker.posicion_y - self.posicion_y
            dist = math.hypot(dx, dy)
            if dist > 0:
                attacker.posicion_x += (dx / dist) * self.pushback_force # Empujar al agresor
                attacker.posicion_y += (dy / dist) * self.pushback_force

            # Entrar en estado de huida
            self.escape_state = 'escaping'
            self.escape_target = attacker
            self.escape_end_time = time.time() + 5 # Huir durante 5 segundos

    def mover_hacia(self, target_x, target_y, velocidad=None):
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

        if next_x < 0: # limite de la ventana
            next_x = 960
        elif next_x > 960:
            next_x = 0
        
        if next_y < 0: # limite de la ventana
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

    def buscar_planta_cercana(self, all_species):
        """Busca la planta más cercana para curarse."""
        planta_cercana = None
        # Radio de detección grande para buscar curación
        distancia_min = 400 
        for entidad in all_species.values():
            if isinstance(entidad, Planta):
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    planta_cercana = entidad
        return planta_cercana


class Carnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=2, color=None, is_baby=False):
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, tiempo_vida_max=120, color=color or (255, 0, 0), size=7 if is_baby else 15, is_baby=is_baby, is_champion=False)
        self.attack_power = 25
        self.attack_cooldown = 2.0
        self.last_attack = 0.0
        self.player_attack_power = 35
        self.player_attack_cooldown = 1.5
        self.objetivo = None
        self.tiempo_busqueda = 0
        self.hunt_state = 'wandering'
        self.target = None
        self.detection_radius = 150
        self.chase_radius = 250
        self.food_target = None
        self.provoked_by_player = False

    def mover(self, screen_width, screen_height, all_species):
        ahora = time.time()

        if getattr(self, 'escape_state', None) == 'escaping':
            super().mover(screen_width, screen_height, all_species)
            if self.escape_state == 'escaping':
                self.hunt_state = 'wandering'
                return None

        if self.vida < self.vida_max * 0.35:
            planta_curativa = self.buscar_planta_cercana(all_species)
            if planta_curativa:
                self.mating_mode = False
                self.hunt_state = 'wandering'
                self.food_target = None
                self.target = None
                self.mover_hacia(planta_curativa.posicion_x, planta_curativa.posicion_y)
                return None


        if self.hunt_state == 'wandering' and self.puede_reproducirse() and random.random() < 0.005:
            self.mating_mode = True
        
        if not self.puede_reproducirse():
            self.mating_mode = False

        if self.mating_mode:
            pareja = self.buscar_pareja(all_species)
            if pareja:
                self.mover_hacia(pareja.posicion_x, pareja.posicion_y)
                return None
            else:
                self.mating_mode = False


        if self.hunt_state == 'wandering':
            if self.provoked_by_player and 'personaje' in all_species:
                self.target = all_species['personaje']
                self.hunt_state = 'chasing'
                return None

            if self.vida < self.vida_max * 0.7:
                if self.food_target is None or (hasattr(self.food_target, 'nutricion') and self.food_target.nutricion <= 0):
                    # Cadáveres eliminados: no buscamos cadáveres, dejamos sin objetivo alimentario aquí
                    self.food_target = None

                if self.food_target:
                    dist_comida = math.hypot(self.posicion_x - self.food_target.posicion_x, self.posicion_y - self.food_target.posicion_y)
                    if dist_comida < self.food_target.size + 5:
                        self.vida = min(self.vida_max, self.vida + 25)
                        self.food_target.nutricion -= 25
                        self.last_attack = ahora
                        if self.food_target.nutricion <= 0:
                            self.food_target = None # Se lo ha comido todo
                        return None
                    else:
                        # Moverse hacia el cadáver
                        self.mover_hacia(self.food_target.posicion_x, self.food_target.posicion_y)
                        return None
            else:
                self.food_target = None


            presa_mas_cercana = None
            distancia_minima = self.detection_radius

            for entidad in all_species.values():
                if entidad is self or isinstance(entidad, (Carnivoro, Planta)):
                    continue
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_minima:
                    distancia_minima = dist
                    presa_mas_cercana = entidad
            
            if presa_mas_cercana:
                self.target = presa_mas_cercana
                self.hunt_state = 'chasing'
            else:
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

            puede_atacar = (ahora - self.last_attack) >= self.attack_cooldown
            if distancia < 25 and puede_atacar:
                self.target.vida = max(0, self.target.vida - self.attack_power)
                self.last_attack = ahora
                return {'damage': self.attack_power, 'target': self.target}
            else:
                velocidad = self.salto * (0.5 if 25 <= distancia < 75 else 1.0)
                self.mover_hacia(self.target.posicion_x, self.target.posicion_y, velocidad=velocidad)
                return None


    def puede_reproducirse(self):
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y):
        vida_cria = self.vida_max // 2
        r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
        g = max(0, min(255, self.color[1] + random.randint(-30, 30)))
        b = max(0, min(255, self.color[2] + random.randint(-30, 30)))
        color_cria = (r, g, b)
        self.vida -= self.vida_max * 0.25
        return Carnivoro(x, y, vida_cria, color=color_cria, is_baby=True)

    def buscar_pareja(self, all_species):
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
        super().__init__(x, y, vida, reproducirse, salto, False, True, True, tiempo_vida_max=120, color=color or (0, 200, 0), size=7 if is_baby else 15, is_baby=is_baby, is_champion=False)

    def puede_reproducirse(self):
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y, is_champion=False):
        if is_champion:
            vida_cria = 200
            r = min(255, self.color[0] + 80)
            g = min(255, self.color[1] + 80)
            b = min(255, self.color[2] + 80)
            color_cria = (r, g, b)
            self.vida -= self.vida_max * 0.5
            cria = Herbivoro(x, y, vida_cria, color=color_cria, is_baby=True)
            cria.is_champion = True
            cria.atacar = True
            cria.attack_power = 25
            cria.detection_radius = 150
            cria.chase_radius = 250
            cria.attack_cooldown = 2.0
            cria.last_attack = 0.0
            cria.hunt_state = 'wandering'
            cria.target = None
            cria.salto *= 1.1
            cria.max_size *= 1.1
        else:
            vida_cria = self.vida_max // 2
            r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
            g = max(0, min(255, self.color[1] + random.randint(-20, 20)))
            b = max(0, min(255, self.color[2] + random.randint(-30, 30)))
            color_cria = (r, g, b)
            self.vida -= self.vida_max * 0.25
            cria = Herbivoro(x, y, vida_cria, color=color_cria, is_baby=True)

        return cria

    def mover(self, screen_width, screen_height, all_species={}):
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, all_species)
            if self.escape_state == 'escaping':
                self.mating_mode = False
                return

        if self.vida < self.vida_max * 0.35:
            planta_curativa = self.buscar_planta_cercana(all_species)
            if planta_curativa:
                self.mating_mode = False
                self.mover_hacia(planta_curativa.posicion_x, planta_curativa.posicion_y)
                return None

        if self.emergency_mating_mode:
            if self.emergency_partner and self.emergency_partner.vida > 0:
                self.mover_hacia(self.emergency_partner.posicion_x, self.emergency_partner.posicion_y)
                return


        if self.is_champion and self.atacar:
            ahora = time.time()
            if getattr(self, 'hunt_state', 'wandering') == 'wandering':
                carnivoro_cercano = None
                distancia_minima = getattr(self, 'detection_radius', 150)
                for entidad in all_species.values():
                    if isinstance(entidad, Carnivoro):
                        dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                        if dist < distancia_minima:
                            distancia_minima = dist
                            carnivoro_cercano = entidad
                if carnivoro_cercano:
                    self.target = carnivoro_cercano
                    self.hunt_state = 'chasing'
            
            if getattr(self, 'hunt_state', 'wandering') == 'chasing' and self.target:
                if not isinstance(self.target, Carnivoro) or getattr(self.target, 'vida', 0) <= 0:
                    self.hunt_state = 'wandering'
                    self.target = None
                else:
                    distancia = math.hypot(self.posicion_x - self.target.posicion_x, self.posicion_y - self.target.posicion_y)
                    chase_radius = getattr(self, 'chase_radius', 250)
                    if distancia > chase_radius:
                        self.hunt_state = 'wandering'
                        self.target = None
                    else:
                        puede_atacar = (ahora - getattr(self, 'last_attack', 0.0)) >= getattr(self, 'attack_cooldown', 2.0)
                        if distancia < 25 and puede_atacar:
                            self.target.vida = max(0, self.target.vida - self.attack_power)
                            self.last_attack = ahora
                            return {'damage': self.attack_power, 'target': self.target}
                        else:
                            velocidad = self.salto * (0.5 if 25 <= distancia < 75 else 1.0)
                            self.mover_hacia(self.target.posicion_x, self.target.posicion_y, velocidad=velocidad)
                            return None
            
            if getattr(self, 'hunt_state', 'wandering') == 'wandering':
                super().mover(screen_width, screen_height, all_species)
                return None

        if self.puede_reproducirse() and random.random() < 0.005:
            self.mating_mode = True
        
        if not self.puede_reproducirse():
            self.mating_mode = False

        if self.mating_mode:
            pareja = self.buscar_pareja(all_species)
            if pareja:
                self.mover_hacia(pareja.posicion_x, pareja.posicion_y)
                return
            else:
                self.mating_mode = False

        return super().mover(screen_width, screen_height, all_species)

    def buscar_pareja(self, all_species):
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

    def buscar_pareja_emergencia(self, all_species):
        mejor_pareja = None
        distancia_min = float('inf')
        for entidad in all_species.values():
            if isinstance(entidad, Omnivoro) and entidad.puede_reproducirse():
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = entidad
        return mejor_pareja


class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=3, color=None, is_baby=False, is_champion=False):
        super().__init__(x, y, vida, reproducirse, salto=salto, atacar=True, correr=True, comer=True, tiempo_vida_max=120, color=color or (128, 0, 128), size=5 if is_baby else 10, is_baby=is_baby, is_champion=is_champion)
        self.max_size = 10
        self.presa = None
        self.modo_caza = False
        self.food_target = None
        self.detection_radius = 150
        self.chase_radius = 250
        self.attack_power = 15

        
    def mover(self, screen_width, screen_height, posibles_presas={}):
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, posibles_presas)
            if self.escape_state == 'escaping':
                self.mating_mode = False
                return

        if self.vida < self.vida_max * 0.35:
            # Antes buscábamos cadáveres; ahora sólo buscamos plantas curativas
            planta_curativa = self.buscar_planta_cercana(posibles_presas)
            if planta_curativa:
                self.mating_mode = False
                self.modo_caza = False
                self.food_target = None
                self.presa = None
                self.mover_hacia(planta_curativa.posicion_x, planta_curativa.posicion_y)
                return None

        if self.emergency_mating_mode:
            if self.emergency_partner and self.emergency_partner.vida > 0:
                self.mover_hacia(self.emergency_partner.posicion_x, self.emergency_partner.posicion_y)
                return


        if not self.modo_caza and self.puede_reproducirse() and random.random() < 0.005:
            self.mating_mode = True
        
        if not self.puede_reproducirse():
            self.mating_mode = False

        if self.mating_mode:
            pareja = self.buscar_pareja(posibles_presas)
            if pareja:
                self.mover_hacia(pareja.posicion_x, pareja.posicion_y)
                return
            else:
                self.mating_mode = False

        ahora = time.time()
        if ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            if random.random() < 0.5:
                self.modo_caza = not self.modo_caza
                self.presa = None

        if self.modo_caza:
            if self.food_target is None or (hasattr(self.food_target, 'nutricion') and self.food_target.nutricion <= 0):
                # No buscar cadáveres; no asignamos objetivo alimentario por cadáver
                self.food_target = None
            
            if self.food_target:
                dist_comida = math.hypot(self.posicion_x - self.food_target.posicion_x, self.posicion_y - self.food_target.posicion_y)
                if dist_comida < self.food_target.size + 5:
                    self.vida = min(self.vida_max, self.vida + 20)
                    self.food_target.nutricion -= 20
                    self.last_random_move_time = time.time()
                    if self.food_target.nutricion <= 0:
                        self.food_target = None
                    return None
                else:
                    self.mover_hacia(self.food_target.posicion_x, self.food_target.posicion_y)
                    return None
            else:
                self.food_target = None

            if self.is_champion:
                if self.presa is None or not isinstance(self.presa, Carnivoro) or getattr(self.presa, 'vida', 0) <= 0:
                    carnivoro_cercano = None
                    distancia_minima = getattr(self, 'detection_radius', 200)
                    for entidad in posibles_presas.values():
                        if isinstance(entidad, Carnivoro):
                            dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                            if dist < distancia_minima:
                                distancia_minima = dist
                                carnivoro_cercano = entidad
                    self.presa = carnivoro_cercano
                
                if self.presa:
                    distancia = math.hypot(self.posicion_x - self.presa.posicion_x, self.posicion_y - self.presa.posicion_y)
                    chase_radius = getattr(self, 'chase_radius', 300)
                    if distancia > chase_radius:
                        self.presa = None
                    else:
                        puede_atacar = (ahora - getattr(self, 'last_attack', 0.0)) >= getattr(self, 'attack_cooldown', 1.5)
                        if distancia < 25 and puede_atacar:
                            self.presa.vida = max(0, self.presa.vida - self.attack_power)
                            self.last_attack = ahora
                            return {'damage': self.attack_power, 'target': self.presa}
                        else:
                            velocidad = self.salto * (0.5 if 25 <= distancia < 75 else 1.0)
                            self.mover_hacia(self.presa.posicion_x, self.presa.posicion_y, velocidad=velocidad)
                            return None
            
            if self.presa and (self.presa not in posibles_presas.values() or self.presa.vida <= 0):
                self.presa = None

            if self.presa and (self.presa not in posibles_presas.values() or self.presa.vida <= 0):
                self.presa = None

            if not self.presa:
                presa_mas_cercana = None
                distancia_minima = getattr(self, 'detection_radius', 100)
                for especie in posibles_presas.values():
                    if especie is self or isinstance(especie, (Carnivoro, Omnivoro, Planta)):
                        continue
                    dist = math.sqrt((self.posicion_x - especie.posicion_x)**2 + (self.posicion_y - especie.posicion_y)**2)
                    if dist < distancia_minima:
                        distancia_minima = dist
                        presa_mas_cercana = especie
                self.presa = presa_mas_cercana

            if self.presa:
                velocidad_caza = self.salto * 0.8
                dx = self.presa.posicion_x - self.posicion_x
                dy = self.presa.posicion_y - self.posicion_y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.posicion_x += (dx / dist) * velocidad_caza
                    self.posicion_y += (dy / dist) * velocidad_caza
                    if dist < 25 and (ahora - getattr(self, 'last_attack', 0.0)) >= getattr(self, 'attack_cooldown', 1.5):
                        self.presa.vida = max(0, self.presa.vida - self.attack_power)
                        self.last_attack = ahora
                        return {'damage': self.attack_power, 'target': self.presa}
            else:
                super().mover(screen_width, screen_height, posibles_presas)
        else:
            return super().mover(screen_width, screen_height, posibles_presas)

    def puede_reproducirse(self):
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y, is_champion=False):
        if is_champion:
            vida_cria = 250
            r = min(255, self.color[0] + 80)
            g = min(255, self.color[1] + 80)
            b = min(255, self.color[2] + 80)
            color_cria = (r, g, b)
            color_cria = (255, 255, 0)
            self.vida -= self.vida_max * 0.5
            cria = Omnivoro(x, y, vida_cria, color=color_cria, is_baby=True, is_champion=True)
            cria.attack_power = 45
            cria.attack_cooldown = 1.5
            cria.last_attack = 0.0
            cria.detection_radius = 250
            cria.salto *= 1.2
            cria.max_size *= 1.25
            return cria
        else:
            vida_cria = self.vida_max // 2
            r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
            g = max(0, min(255, self.color[1] + random.randint(-30, 30)))
            b = max(0, min(255, self.color[2] + random.randint(-20, 20)))
            color_cria = (r, g, b)
            self.vida -= self.vida_max * 0.25
            cria = Omnivoro(x, y, vida_cria, color=color_cria, is_baby=True)
            return cria

    def buscar_pareja(self, all_species):
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

    def buscar_pareja_emergencia(self, all_species):
        mejor_pareja = None
        distancia_min = float('inf')
        for entidad in all_species.values():
            if isinstance(entidad, Herbivoro) and entidad.puede_reproducirse():
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = entidad
        return mejor_pareja


class Planta(Especies):
    def __init__(self, x, y, reproducirse=False):
        super().__init__(x, y, float('inf'), reproducirse, 0, False, False, False)
        self.healing_target = None
        self.time_on_plant = 0
        self.is_healing = False
        self.heal_amount = 15
        self.heal_cooldown = 0.5
        self.last_heal_time = 0

        
class Personaje:
    def __init__(self, x, y, vida):
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

        self.state = self.IDLE_DOWN
        self.direction = 'down'
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100

        self.attack_power = 30
        self.attack_range = 40
        self.attack_cooldown = 1.0
        self.last_attack_time = 0

    def take_damage(self, attacker, damage):
        self.vida -= damage

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
        self.velocidad_extra = 1
        self.ticks_velocidad = 10

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
    def __init__(self, ancho=960, alto=720, fps=30):
        pygame.init()
        self.ancho = ancho
        self.alto = alto
        self.screen = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Juego - Proyecto Especies")
        self.clock = pygame.time.Clock()
        self.fps = fps

        try:
            background_image = pygame.image.load("assets/fondos/fondos.png").convert()
            self.background_image = pygame.transform.scale(background_image, (self.ancho, self.alto))
            
            green_tint = pygame.Surface(self.background_image.get_size()).convert_alpha()
            green_tint.fill((20, 90, 40, 120))
            self.background_image.blit(green_tint, (0, 0))
        except pygame.error:
            self.background_image = None

        self.especies_vivas = {}
        entidades_a_crear = [
            (Carnivoro, "carnivoro", 2),
            (Herbivoro, "herbivoro", 2),
            (Omnivoro, "omnivoro", 2),
            (Planta, "planta", 10)
        ]
        
        min_dist_entidades = 100

        for clase_entidad, nombre_base, cantidad in entidades_a_crear:
            for i in range(cantidad):
                intentos = 0
                while intentos < 100:
                    x = random.randint(20, self.ancho - 20)
                    y = random.randint(20, self.alto - 20)
                    
                    demasiado_cerca = False
                    for entidad_existente in self.especies_vivas.values():
                        if math.hypot(x - entidad_existente.posicion_x, y - entidad_existente.posicion_y) < min_dist_entidades:
                            demasiado_cerca = True
                            break
                    
                    if not demasiado_cerca:
                        nombre_unico = f"{nombre_base}_{i+1}"
                        if issubclass(clase_entidad, Planta):
                            self.especies_vivas[nombre_unico] = clase_entidad(x, y)
                        else:
                            self.especies_vivas[nombre_unico] = clase_entidad(x, y, 100, is_baby=False)
                        break
                    intentos += 1

        self.personaje = Personaje(200, 200, 1000)
        self.damage_popups = []

        self.animations = self._load_animations()

        try:
            self.font = pygame.font.SysFont(None, 20)
        except Exception:
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 20)

        self.running = False

    def _load_animations(self):
        animations = {}
        sprite_sheet = pygame.image.load("assets/sprites/player.png").convert_alpha()

        animation_definitions = {
            self.personaje.WALK_DOWN:   (5, 1, 17),
            self.personaje.WALK_RIGHT:  (37, 1, 17),
            self.personaje.WALK_UP:     (101, 1, 17),
        }

        frame_width, frame_height = 16, 22
        scale_width, scale_height = 48, 48

        for state, (y_pos, num_frames, spacing) in animation_definitions.items():
            animation_strip = []
            for i in range(num_frames):
                x = 1 + (i * spacing)
                y = y_pos
                try:
                    original_frame = sprite_sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height)).copy()
                except Exception:
                    original_frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)

                bounding = original_frame.get_bounding_rect()
                if bounding.width == 0 or bounding.height == 0:
                    cropped_frame = original_frame
                else:
                    cropped_frame = original_frame.subsurface(bounding).copy()

                w = max(1, cropped_frame.get_width())
                h = max(1, cropped_frame.get_height())
                scale_x = scale_width / w
                scale_y = scale_height / h
                scale_factor = min(scale_x, scale_y)
                new_w = max(1, int(w * scale_factor))
                new_h = max(1, int(h * scale_factor))
                try:
                    scaled_frame = pygame.transform.smoothscale(cropped_frame, (new_w, new_h))
                except Exception:
                    scaled_frame = pygame.transform.scale(cropped_frame, (new_w, new_h))

                canvas = pygame.Surface((scale_width, scale_height), pygame.SRCALPHA)
                dest_rect = scaled_frame.get_rect(midbottom=(scale_width // 2, scale_height))
                canvas.blit(scaled_frame, dest_rect)
                animation_strip.append(canvas)

            animations[state] = animation_strip
        
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
            elif event.key == pygame.K_SPACE:
                ahora = time.time()
                if ahora - self.personaje.last_attack_time >= self.personaje.attack_cooldown:
                    self.personaje.last_attack_time = ahora
                    for nombre, especie in self.especies_vivas.items():
                        dist = math.hypot(self.personaje.posicion_x - especie.posicion_x, self.personaje.posicion_y - especie.posicion_y)
                        if dist < self.personaje.attack_range:
                            damage_dealt = self.personaje.attack_power
                            especie.take_damage(self.personaje, self.personaje.attack_power)
                            self.damage_popups.append({
                                'text': f"-{int(damage_dealt)}",
                                'x': especie.posicion_x, 'y': especie.posicion_y - 10, 'start': pygame.time.get_ticks()})
                            break
    def _draw_hp_bar(self, entity, y_offset=-20, width=36, height=6, color_healthy=(0,200,0), color_low=(200,0,0), low_threshold=0.3):
        try:
            hp_percent = max(0.0, min(1.0, entity.vida / entity.vida_max))
        except Exception:
            return
        x = int(entity.posicion_x - width // 2)
        y = int(entity.posicion_y + y_offset)
        pygame.draw.rect(self.screen, (50,50,50), (x, y, width, height))
        color = color_healthy if hp_percent > low_threshold else color_low
        pygame.draw.rect(self.screen, color, (x, y, int(width * hp_percent), height))

    def check_reproduction(self):
        nuevas_especies = {}
        tiempo_actual = time.time()
        
        for nombre, especie in self.especies_vivas.items():
            if hasattr(especie, 'ultimo_intento_reproduccion'):
                if tiempo_actual - especie.ultimo_intento_reproduccion < 10:
                    continue
            
            for otro_nombre, otra_especie in self.especies_vivas.items():
                if (especie is not otra_especie and
                    (isinstance(otra_especie, type(especie)) or especie.emergency_mating_mode or otra_especie.emergency_mating_mode) and
                    hasattr(especie, 'puede_reproducirse') and especie.puede_reproducirse() and 
                    hasattr(otra_especie, 'puede_reproducirse') and otra_especie.puede_reproducirse()):
                    
                    hay_campeon_existente = any(e.is_champion for e in self.especies_vivas.values())

                    hay_cria_existente = any(
                        isinstance(e, type(especie)) and getattr(e, 'is_baby', False) for e in self.especies_vivas.values())
                    if hay_cria_existente:
                        continue

                    dist = math.hypot(especie.posicion_x - otra_especie.posicion_x,
                                      especie.posicion_y - otra_especie.posicion_y)
                    
                    if dist < 30:
                        new_x = especie.posicion_x + random.randint(-30, 30)
                        new_y = especie.posicion_y + random.randint(-30, 30)
                        
                        new_x = max(0, min(new_x, self.ancho))
                        new_y = max(0, min(new_y, self.alto))
                        
                        if especie.emergency_mating_mode or otra_especie.emergency_mating_mode:
                            if hay_campeon_existente: continue # Solo un campeón a la vez
                            if isinstance(especie, Omnivoro):
                                nueva_especie = especie.reproducir(new_x, new_y, is_champion=True)
                            else:
                                nueva_especie = otra_especie.reproducir(new_x, new_y, is_champion=True)
                        else:
                            if hay_cria_existente: continue
                            nueva_especie = especie.reproducir(new_x, new_y)

                        if nueva_especie:
                            especie.ultimo_intento_reproduccion = tiempo_actual
                            otra_especie.ultimo_intento_reproduccion = tiempo_actual
                            
                            push_force_parents = 30
                            push_force_baby = 40
                            dx = especie.posicion_x - otra_especie.posicion_x
                            dy = especie.posicion_y - otra_especie.posicion_y
                            
                            if dist > 0:
                                push_x = (dx / dist) * push_force_parents
                                push_y = (dy / dist) * push_force_parents
                                especie.posicion_x += push_x
                                especie.posicion_y += push_y
                                otra_especie.posicion_x -= push_x
                                otra_especie.posicion_y -= push_y
                                
                                nueva_especie.posicion_x -= push_y * (push_force_baby / push_force_parents)
                                nueva_especie.posicion_y += push_x * (push_force_baby / push_force_parents)

                            especie.mating_mode = False
                            otra_especie.mating_mode = False
                            especie.emergency_mating_mode = False
                            otra_especie.emergency_mating_mode = False
                            base_name = especie.__class__.__name__.lower()
                            new_name = f"{base_name}_{len(self.especies_vivas) + len(nuevas_especies)}"
                            nuevas_especies[new_name] = nueva_especie
                            
                            self.damage_popups.append({
                                'text': "<3",
                                'x': especie.posicion_x,
                                'y': especie.posicion_y - 10,
                                'start': pygame.time.get_ticks()
                            })
                            break
        self.especies_vivas.update(nuevas_especies)

    def _check_emergency_reproduction(self):
        for e in self.especies_vivas.values():
            e.emergency_mating_mode = False
            e.emergency_partner = None
        herbivoros_vivos = [e for e in self.especies_vivas.values() if isinstance(e, Herbivoro) and not e.is_baby]
        omnivoros_vivos = [e for e in self.especies_vivas.values() if isinstance(e, Omnivoro) and not e.is_baby]

        if len(herbivoros_vivos) == 1 and len(omnivoros_vivos) > 0:
            survivor = herbivoros_vivos[0]
            if survivor.puede_reproducirse():
                best_partner = min(omnivoros_vivos, 
                                   key=lambda p: math.hypot(survivor.posicion_x - p.posicion_x, survivor.posicion_y - p.posicion_y) 
                                   if p.puede_reproducirse() else float('inf'))
                
                if best_partner and best_partner.puede_reproducirse():
                    survivor.emergency_mating_mode = True
                    best_partner.emergency_mating_mode = True
                    survivor.emergency_partner = best_partner
                    best_partner.emergency_partner = survivor
        
        elif len(omnivoros_vivos) == 1 and len(herbivoros_vivos) > 0:
            survivor = omnivoros_vivos[0]
            if survivor.puede_reproducirse():
                best_partner = min(herbivoros_vivos, 
                                   key=lambda p: math.hypot(survivor.posicion_x - p.posicion_x, survivor.posicion_y - p.posicion_y)
                                   if p.puede_reproducirse() else float('inf'))

                if best_partner and best_partner.puede_reproducirse():
                    survivor.emergency_mating_mode = True
                    best_partner.emergency_mating_mode = True
                    survivor.emergency_partner = best_partner
                    best_partner.emergency_partner = survivor
        

    def _resolve_collisions(self):
        movable_entities = [e for e in self.especies_vivas.values() if not isinstance(e, Planta)]
        
        for i in range(len(movable_entities)):
            for j in range(i + 1, len(movable_entities)):
                entity1 = movable_entities[i]
                entity2 = movable_entities[j]

                if type(entity1) is type(entity2):
                    dist = math.hypot(entity1.posicion_x - entity2.posicion_x, entity1.posicion_y - entity2.posicion_y)
                    
                    combined_radius = entity1.size + entity2.size
                    
                    if dist < combined_radius:
                        overlap = combined_radius - dist
                        
                        if dist == 0:
                            dist = 0.1
                            entity1.posicion_x += 0.1

                        push_x = (entity1.posicion_x - entity2.posicion_x) / dist
                        push_y = (entity1.posicion_y - entity2.posicion_y) / dist
                        
                        move_amount = overlap / 2
                        
                        entity1.posicion_x += push_x * move_amount
                        entity2.posicion_x -= push_x * move_amount
                        
                        entity1.posicion_y += push_y * move_amount
                        entity2.posicion_y -= push_y * move_amount

    def _update_plant_healing(self):
        ahora = time.time()
        all_entities = list(self.especies_vivas.values()) + [self.personaje]
        
        plants = [e for e in self.especies_vivas.values() if isinstance(e, Planta)]
        movable_entities = [e for e in all_entities if not isinstance(e, Planta)]

        for plant in plants:
            current_target = None
            for entity in movable_entities:
                dist = math.hypot(plant.posicion_x - entity.posicion_x, plant.posicion_y - entity.posicion_y)
                if dist < 15: # Radio de contacto
                    current_target = entity
                    break
            
            if current_target:
                plant.is_healing = True
                plant.healing_target = current_target
                
                if ahora - plant.last_heal_time >= plant.heal_cooldown:
                    plant.last_heal_time = ahora
                    target = plant.healing_target
                    if target.vida < target.vida_max:
                        target.vida = min(target.vida_max, target.vida + plant.heal_amount)
            else:
                plant.healing_target = None
                plant.is_healing = False

    def _update_growth(self):
        ahora = time.time()
        for especie in self.especies_vivas.values():
            if getattr(especie, 'is_baby', False):
                tiempo_transcurrido = ahora - especie.birth_time
                if tiempo_transcurrido >= especie.growth_duration:
                    especie.is_baby = False
                    especie.size = especie.max_size
                else:
                    progreso = tiempo_transcurrido / especie.growth_duration
                    tamaño_inicial = especie.max_size / 2
                    especie.size = tamaño_inicial + (especie.max_size - tamaño_inicial) * progreso
    def _update_ai(self):
        self._update_vida_por_tiempo()

        all_entities = self.especies_vivas.copy()
        all_entities['personaje'] = self.personaje

        for nombre, especie in list(self.especies_vivas.items()):
            if isinstance(especie, Planta):
                continue
            attack_info = especie.mover(self.ancho, self.alto, all_entities)

            if attack_info:
                target = attack_info['target']
                damage = attack_info['damage']

                self.damage_popups.append({
                    'text': f"-{int(damage)}",
                    'x': target.posicion_x,
                    'y': target.posicion_y - 10,
                    'start': pygame.time.get_ticks()
                })

                if target.vida <= 0:
                    if target is self.personaje:
                        self.running = False
                    else:
                        for key, value in list(self.especies_vivas.items()):
                            if value is target:
                                del self.especies_vivas[key]
                                break

    def _update_vida_por_tiempo(self):
        for especie in self.especies_vivas.values():
            especie.update_vida_por_tiempo()

    def draw(self):
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((130, 170, 110))
        
        # Eliminar especies muertas (sin crear cadáveres)
        nombres_muertos = []
        for nombre, especie in list(self.especies_vivas.items()):
            if hasattr(especie, 'vida') and especie.vida <= 0 and not isinstance(especie, Planta):
                nombres_muertos.append(nombre)

        for nombre in nombres_muertos:
            del self.especies_vivas[nombre]

        if self.animations:
            animation_strip = self.animations[self.personaje.state]
            self.personaje.update_animation(animation_strip)
            current_frame = animation_strip[self.personaje.frame_index]

            flip = self.personaje.direction == 'left'
            image_to_draw = pygame.transform.flip(current_frame, flip, False)

            mask = pygame.mask.from_surface(image_to_draw)
            outline_surface = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
            rect = image_to_draw.get_rect(midbottom=(int(self.personaje.posicion_x), int(self.personaje.posicion_y)))
            self.screen.blit(outline_surface, (rect.x - 1, rect.y - 1))
            self.screen.blit(outline_surface, (rect.x + 1, rect.y - 1))
            self.screen.blit(outline_surface, (rect.x - 1, rect.y + 1))
            self.screen.blit(outline_surface, (rect.x + 1, rect.y + 1))
            
            self.screen.blit(image_to_draw, rect)

            hp_y_offset = rect.top - int(self.personaje.posicion_y) - 8
            self._draw_hp_bar(self.personaje, y_offset=hp_y_offset, color_healthy=(0, 100, 255))
        else:
            pygame.draw.circle(self.screen, (0, 0, 255), (int(self.personaje.posicion_x), int(self.personaje.posicion_y)), 15)
            self._draw_hp_bar(self.personaje, y_offset=-10, color_healthy=(0, 100, 255))

        for nombre, especie in self.especies_vivas.items():
            if isinstance(especie, Carnivoro):
                pygame.draw.circle(self.screen, (0,0,0), (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size) + 1)
                pygame.draw.circle(self.screen, especie.color, (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size))
                self._draw_hp_bar(especie)
            elif isinstance(especie, Herbivoro):
                pygame.draw.circle(self.screen, (0,0,0), (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size) + 1)
                pygame.draw.circle(self.screen, especie.color, (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size))
                self._draw_hp_bar(especie)
            elif isinstance(especie, Omnivoro):
                omni_size = int(especie.size) * 2
                omni_x = int(especie.posicion_x) - omni_size // 2
                omni_y = int(especie.posicion_y) - omni_size // 2
                pygame.draw.rect(self.screen, (0,0,0), (omni_x - 1, omni_y - 1, omni_size + 2, omni_size + 2))
                pygame.draw.rect(self.screen, especie.color, (omni_x, omni_y, omni_size, omni_size))
                self._draw_hp_bar(especie)
            # Cadáveres están deshabilitados; no dibujamos nada especial aquí.
            elif isinstance(especie, Planta):
                color_contorno = (50, 255, 50) if especie.is_healing else (0, 0, 0)
                size = 12
                p1 = (int(especie.posicion_x), int(especie.posicion_y) - size)
                p2 = (int(especie.posicion_x) - size, int(especie.posicion_y) + size)
                p3 = (int(especie.posicion_x) + size, int(especie.posicion_y) + size)
                pygame.draw.polygon(self.screen, (0, 140, 20), [p1, p2, p3])
                pygame.draw.polygon(self.screen, color_contorno, [p1, p2, p3], 2)

        now_ms = pygame.time.get_ticks()
        popups_a_quitar = []
        for i, popup in enumerate(self.damage_popups):
            elapsed = now_ms - popup['start']
            if elapsed > 1000:
                popups_a_quitar.append(i)
                continue
            y_off = popup['y'] - (elapsed * 0.03)
            alpha = max(0, 255 - int(elapsed / 1000 * 255))
            surf = self.font.render(popup['text'], True, (200, 0, 0))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (popup['x'] - surf.get_width()//2, y_off))

        for idx in reversed(popups_a_quitar):
            del self.damage_popups[idx]

        texto_str = "Flechas/WASD = mover, Espacio = atacar, ESC = salir"
        pos_x, pos_y = 10, self.alto - 25
        color_texto = (200, 200, 255)
        color_contorno = (0, 0, 0)
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            self.screen.blit(self.font.render(texto_str, True, color_contorno), (pos_x + dx, pos_y + dy))
        self.screen.blit(self.font.render(texto_str, True, color_texto), (pos_x, pos_y))

        pygame.display.flip()

    
    def iniciar(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

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

            old_state = self.personaje.state
            is_moving = dx != 0 or dy != 0

            if is_moving:
                if dy < 0:
                    self.personaje.state = self.personaje.WALK_UP
                    self.personaje.direction = 'up'
                    self.personaje.mover_arriba()
                elif dy > 0:
                    self.personaje.state = self.personaje.WALK_DOWN
                    self.personaje.direction = 'down'
                    self.personaje.mover_abajo()
                
                if dx < 0 and dy == 0:
                    self.personaje.state = self.personaje.WALK_RIGHT
                    self.personaje.direction = 'left'
                    self.personaje.mover_izquierda()
                elif dx > 0 and dy == 0:
                    self.personaje.state = self.personaje.WALK_RIGHT
                    self.personaje.direction = 'right'
                    self.personaje.mover_derecha()
            else:
                if self.personaje.direction == 'up': self.personaje.state = self.personaje.IDLE_UP
                elif self.personaje.direction == 'down': self.personaje.state = self.personaje.IDLE_DOWN
                else: self.personaje.state = self.personaje.IDLE_RIGHT

            if self.personaje.state != old_state:
                self.personaje.frame_index = 0


            self.personaje.tick_velocidad()
            self._update_ai()
            self.check_reproduction()
            self._check_emergency_reproduction()
            self._update_plant_healing()
            self._update_growth()
            self.draw()
            self.clock.tick(self.fps)

        pygame.quit()

if __name__ == "__main__":
    print("=== Juego en 2 capas Lógica y Vista ===")
    juego = VistaPygame()
    juego.iniciar()
