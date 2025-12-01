"""
Módulo de omnívoros - depredadores y herbívoros a la vez.
"""

import math
import time
import random
from .especies import Especies


class Omnivoro(Especies):
    """Clase que representa un omnívoro del ecosistema."""
    
    def __init__(self, x, y, vida, reproducirse=True, salto=3, color=None, 
                 is_baby=False, is_champion=False):
        super().__init__(x, y, vida, reproducirse, salto=salto, atacar=True, correr=True, 
                        comer=True, tiempo_vida_max=120, color=color or (128, 0, 128), 
                        size=5 if is_baby else 10, is_baby=is_baby, is_champion=is_champion)
        self.max_size = 10
        self.presa = None
        self.modo_caza = False
        self.food_target = None
        self.detection_radius = 150
        self.chase_radius = 250
        self.attack_power = 15
        self.attack_cooldown = 1.5
        self.last_attack = 0.0

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Comportamiento de movimiento del omnívoro."""
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, posibles_presas)
            if self.escape_state == 'escaping':
                self.mating_mode = False
                return

        if self.vida < self.vida_max * 0.35:
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
                self.food_target = None
            
            if self.food_target:
                dist_comida = math.hypot(self.posicion_x - self.food_target.posicion_x, 
                                        self.posicion_y - self.food_target.posicion_y)
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
                            dist = math.hypot(self.posicion_x - entidad.posicion_x, 
                                            self.posicion_y - entidad.posicion_y)
                            if dist < distancia_minima:
                                distancia_minima = dist
                                carnivoro_cercano = entidad
                    self.presa = carnivoro_cercano
                
                if self.presa:
                    distancia = math.hypot(self.posicion_x - self.presa.posicion_x, 
                                          self.posicion_y - self.presa.posicion_y)
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

            if not self.presa:
                presa_mas_cercana = None
                distancia_minima = getattr(self, 'detection_radius', 100)
                for especie in posibles_presas.values():
                    if especie is self or isinstance(especie, (Carnivoro, Omnivoro, Planta)):
                        continue
                    dist = math.sqrt((self.posicion_x - especie.posicion_x)**2 + 
                                    (self.posicion_y - especie.posicion_y)**2)
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
        """Verifica si el omnívoro puede reproducirse."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y, is_champion=False):
        """Crea una cría omnívora."""
        if is_champion:
            vida_cria = 250
            r = min(255, self.color[0] + 80)
            g = min(255, self.color[1] + 80)
            b = min(255, self.color[2] + 80)
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
        """Busca una pareja omnívora para reproducirse."""
        mejor_pareja = None
        distancia_min = float('inf')
        for nombre, otra_especie in all_species.items():
            if (isinstance(otra_especie, Omnivoro) and 
                otra_especie is not self and 
                hasattr(otra_especie, 'puede_reproducirse') and 
                otra_especie.puede_reproducirse()):
                dist = math.hypot(self.posicion_x - otra_especie.posicion_x, 
                                 self.posicion_y - otra_especie.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = otra_especie
        return mejor_pareja

    def buscar_pareja_emergencia(self, all_species):
        """Busca una pareja herbívora en caso de emergencia."""
        mejor_pareja = None
        distancia_min = float('inf')
        for entidad in all_species.values():
            if isinstance(entidad, Herbivoro) and entidad.puede_reproducirse():
                dist = math.hypot(self.posicion_x - entidad.posicion_x, 
                                 self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = entidad
        return mejor_pareja

    def serializar(self):
        """Convierte el omnívoro a diccionario para persistencia."""
        datos = super().serializar()
        datos['modo_caza'] = self.modo_caza
        return datos


# Importar al final para evitar circular imports
from .carnivoro import Carnivoro
from .herbivoro import Herbivoro
from .planta import Planta
