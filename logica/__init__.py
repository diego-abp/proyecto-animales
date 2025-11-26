"""
Paquete de lógica del Simulador de Ecosistema Virtual
Contiene todas las clases de especies y la lógica del ecosistema
"""

from .especies import Especies
from .carnivoro import Carnivoro
from .herbivoro import Herbivoro
from .omnivoro import Omnivoro
from .planta import Planta
from .ecosistema import Ecosistema

__all__ = ['Especies', 'Carnivoro', 'Herbivoro', 'Omnivoro', 'Planta', 'Ecosistema']
