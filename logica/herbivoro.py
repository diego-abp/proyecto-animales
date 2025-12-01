"""
Módulo de herbívoros - comedores de plantas.
"""

import math
import time
import random
from .especies import Especies


class Herbivoro(Especies):
    """Clase que representa un herbívoro del ecosistema."""
    
    def __init__(self, x, y, vida, reproducirse=True, salto=4, color=None, is_baby=False):
        super().__init__(x, y, vida, reproducirse, salto, False, True, True, 
                        tiempo_vida_max=120, color=color or (0, 200, 0), 
                        size=7 if is_baby else 15, is_baby=is_baby, is_champion=False)

    def puede_reproducirse(self):
        """Verifica si el herbívoro puede reproducirse."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y, is_champion=False):
        """Crea una cría herbívora."""
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
        """Comportamiento de movimiento del herbívoro."""
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
                    distancia = math.hypot(self.posicion_x - self.target.posicion_x, 
                                          self.posicion_y - self.target.posicion_y)
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
        """Busca una pareja herbívora para reproducirse."""
        mejor_pareja = None
        distancia_min = float('inf')
        for nombre, otra_especie in all_species.items():
            if (isinstance(otra_especie, Herbivoro) and otra_especie is not self and 
                hasattr(otra_especie, 'puede_reproducirse') and otra_especie.puede_reproducirse()):
                dist = math.hypot(self.posicion_x - otra_especie.posicion_x, 
                                 self.posicion_y - otra_especie.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = otra_especie
        return mejor_pareja

    def buscar_pareja_emergencia(self, all_species):
        """Busca una pareja omnívora en caso de emergencia."""
        mejor_pareja = None
        distancia_min = float('inf')
        for entidad in all_species.values():
            if isinstance(entidad, Omnivoro) and entidad.puede_reproducirse():
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = entidad
        return mejor_pareja

    def serializar(self):
        """Convierte el herbívoro a diccionario para persistencia."""
        return super().serializar()


# Importar al final para evitar circular imports
from .carnivoro import Carnivoro
from .omnivoro import Omnivoro
