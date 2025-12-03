"""
Módulo de clases base para las especies del simulador.
Define la clase Especies con atributos y métodos fundamentales.
"""

import math
import time
import random


class Especies:
    """Clase base para todas las especies del ecosistema."""
    
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, 
                 tiempo_vida_max=100, sync_vida_with_tiempo=False, color=(255,255,255), size=15, 
                 is_baby=False, is_champion=False):
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
        self.random_move_delay = random.uniform(0.5, 2.5)
        self.random_move_target = None
        # Atributo para cooldown de reproducción
        self.ultimo_intento_reproduccion = 0
        # Atributos para crecimiento y apariencia
        self.color = color
        self.max_size = 15
        self.size = size
        self.is_baby = is_baby
        self.is_champion = is_champion
        self.birth_time = time.time()
        self.growth_duration = 30
        # Atributo para el modo de apareamiento
        self.mating_mode = False
        self.emergency_partner = None
        self.emergency_mating_mode = False
        # Personalidad individual
        self.wander_speed_multiplier = random.uniform(0.8, 1.2)
        self.wander_change_frequency_multiplier = random.uniform(0.7, 1.5)
        self.wander_pause_chance = random.uniform(0.001, 0.005)
        self.is_paused = False
        self.pause_end_time = 0
        # Atributos de contraataque
        self.counter_attack_power = 1
        self.pushback_force = 40

    def update_vida_por_tiempo(self):
        """Reduce la vida según el tiempo transcurrido."""
        if self.vida == float('inf') or self.tiempo_vida_max <= 0:
            return
        ahora = time.time()
        tiempo_transcurrido = ahora - self.ultimo_update
        self.ultimo_update = ahora
        self.vida -= (self.vida_max / self.tiempo_vida_max) * tiempo_transcurrido

    def take_damage(self, attacker, damage):
        """Aplica daño y activa contraataque/huida."""
        self.vida -= damage
        if self.vida > 0 and attacker is not None:
            # Contraatacar
            if hasattr(attacker, 'vida'):
                attacker.vida = max(0, attacker.vida - self.counter_attack_power)
            
            dx = attacker.posicion_x - self.posicion_x
            dy = attacker.posicion_y - self.posicion_y
            dist = math.hypot(dx, dy)
            if dist > 0:
                attacker.posicion_x += (dx / dist) * self.pushback_force
                attacker.posicion_y += (dy / dist) * self.pushback_force

            # Entrar en estado de huida
            self.escape_state = 'escaping'
            self.escape_target = attacker
            self.escape_end_time = time.time() + 5

    def mover_hacia(self, target_x, target_y, velocidad=None):
        """Mueve la especie hacia un objetivo."""
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

        # Wrapping de pantalla
        if next_x < 0:
            next_x = 960
        elif next_x > 960:
            next_x = 0
        
        if next_y < 0:
            next_y = 720
        elif next_y > 720:
            next_y = 0

        self.posicion_x = next_x
        self.posicion_y = next_y

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Comportamiento de movimiento base: deambular aleatoriamente."""
        ahora = time.time()

        # --- Lógica de Huida ---
        if self.escape_state == 'escaping':
            if ahora > self.escape_end_time or self.escape_target is None or self.escape_target.vida <= 0:
                self.escape_state = 'none'
                self.escape_target = None
            else:
                dx = self.posicion_x - self.escape_target.posicion_x
                dy = self.posicion_y - self.escape_target.posicion_y
                dist = math.hypot(dx, dy)
                velocidad_escape = self.salto * 1.2
                if dist > 0:
                    self.mover_hacia(self.posicion_x + dx, self.posicion_y + dy, velocidad=velocidad_escape)
                return

        # --- Lógica de Pausa ---
        if self.is_paused:
            if ahora > self.pause_end_time:
                self.is_paused = False
            else:
                return
        elif random.random() < self.wander_pause_chance:
            self.is_paused = True
            self.pause_end_time = ahora + random.uniform(0.5, 1.5)

        # --- Lógica de Deambulación ---
        dist_to_target = math.hypot(
            self.posicion_x - (self.random_move_target[0] if self.random_move_target else self.posicion_x), 
            self.posicion_y - (self.random_move_target[1] if self.random_move_target else self.posicion_y)
        )

        if self.random_move_target is None or dist_to_target < 50 or ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            self.random_move_delay = random.uniform(2, 5) * self.wander_change_frequency_multiplier
            self.random_move_target = (random.randint(0, screen_width), random.randint(0, screen_height))

        if self.random_move_target:
            self.mover_hacia(self.random_move_target[0], self.random_move_target[1], 
                            velocidad=self.salto * self.wander_speed_multiplier)

    def buscar_planta_cercana(self, all_species):
        """Busca la planta más cercana para curarse."""
        planta_cercana = None
        distancia_min = 400
        for entidad in all_species.values():
            if isinstance(entidad, Planta):
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    planta_cercana = entidad
        return planta_cercana

    def serializar(self):
        """Convierte la especie a un diccionario para persistencia."""
        return {
            'tipo': self.__class__.__name__,
            'posicion': (self.posicion_x, self.posicion_y),
            'vida': self.vida,
            'vida_max': self.vida_max,
            'color': self.color,
            'is_baby': self.is_baby,
            'is_champion': self.is_champion,
        }

    @staticmethod
    def deserializar(datos):
        """Reconstruye una especie desde un diccionario."""
        # Este método será sobrescrito en subclases
        pass


# Importar al final para evitar circular imports
from .planta import Planta
