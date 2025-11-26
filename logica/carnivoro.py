"""
Módulo de carnívoros - depredadores del ecosistema.
"""

import math
import time
import random
from .especies import Especies


class Carnivoro(Especies):
    """Clase que representa un carnívoro del ecosistema."""
    
    def __init__(self, x, y, vida, reproducirse=True, salto=2, color=None, is_baby=False):
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, 
                        tiempo_vida_max=120, color=color or (255, 0, 0), 
                        size=7 if is_baby else 15, is_baby=is_baby, is_champion=False)
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
        """Comportamiento de movimiento del carnívoro: buscar y atacar presas."""
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
                    self.food_target = None

                if self.food_target:
                    dist_comida = math.hypot(self.posicion_x - self.food_target.posicion_x, 
                                            self.posicion_y - self.food_target.posicion_y)
                    if dist_comida < self.food_target.size + 5:
                        self.vida = min(self.vida_max, self.vida + 25)
                        self.food_target.nutricion -= 25
                        self.last_attack = ahora
                        if self.food_target.nutricion <= 0:
                            self.food_target = None
                        return None
                    else:
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

            distancia = math.hypot(self.posicion_x - self.target.posicion_x, 
                                  self.posicion_y - self.target.posicion_y)
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
        """Verifica si el carnívoro puede reproducirse."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y):
        """Crea una cría carnívora."""
        vida_cria = self.vida_max // 2
        r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
        g = max(0, min(255, self.color[1] + random.randint(-30, 30)))
        b = max(0, min(255, self.color[2] + random.randint(-30, 30)))
        color_cria = (r, g, b)
        self.vida -= self.vida_max * 0.25
        return Carnivoro(x, y, vida_cria, color=color_cria, is_baby=True)

    def buscar_pareja(self, all_species):
        """Busca una pareja carnívora para reproducirse."""
        mejor_pareja = None
        distancia_min = float('inf')
        for nombre, otra_especie in all_species.items():
            if (isinstance(otra_especie, Carnivoro) and 
                otra_especie is not self and 
                hasattr(otra_especie, 'puede_reproducirse') and 
                otra_especie.puede_reproducirse()):
                
                dist = math.hypot(self.posicion_x - otra_especie.posicion_x, 
                                 self.posicion_y - otra_especie.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = otra_especie
        return mejor_pareja

    def serializar(self):
        """Convierte el carnívoro a diccionario para persistencia."""
        datos = super().serializar()
        datos['hunt_state'] = self.hunt_state
        datos['attack_power'] = self.attack_power
        return datos


# Importar Planta al final para evitar circular imports
from .planta import Planta
