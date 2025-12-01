"""
Módulo de plantas - recurso natural del ecosistema.
"""

from .especies import Especies


class Planta(Especies):
    """Clase que representa una planta del ecosistema."""
    
    def __init__(self, x, y, reproducirse=False):
        super().__init__(x, y, float('inf'), reproducirse, 0, False, False, False)
        self.healing_target = None
        self.time_on_plant = 0
        self.is_healing = False
        self.heal_amount = 15
        self.heal_cooldown = 0.5
        self.last_heal_time = 0
        self.nutricion = 100  # Para que pueda ser "comida"

    def serializar(self):
        """Convierte la planta a diccionario para persistencia."""
        return {
            'tipo': 'Planta',
            'posicion': (self.posicion_x, self.posicion_y),
            'vida': float('inf'),
        }
