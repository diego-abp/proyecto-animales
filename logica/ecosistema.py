"""
Módulo del Ecosistema - Gestor central de la simulación.
Coordina la lógica de todas las especies y el estado general del sistema.
"""

import time
import math
import random


class Ecosistema:
    """Gestor del ecosistema que coordina todas las especies y el estado de la simulación."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.ciclo = 0
        self.animales = {}
        self.plantas = {}
        self.estado = 'Normal'
        self.tiempo_inicio = time.time()
        self.ciclos_desde_autoguardado = 0
        self.autoguardado_cada_n_ciclos = self.config.get('autoguardado_cada_n_ciclos', 10)
        self.version = self.config.get('version', '1.0')

    def agregar_animal(self, nombre, animal):
        """Agrega un animal al ecosistema."""
        self.animales[nombre] = animal

    def agregar_planta(self, nombre, planta):
        """Agrega una planta al ecosistema."""
        self.plantas[nombre] = planta

    def remover_animal(self, nombre):
        """Remueve un animal del ecosistema."""
        if nombre in self.animales:
            del self.animales[nombre]

    def remover_planta(self, nombre):
        """Remueve una planta del ecosistema."""
        if nombre in self.plantas:
            del self.plantas[nombre]

    def avanzar_ciclo(self):
        """Avanza un ciclo de simulación."""
        self.ciclo += 1
        self.ciclos_desde_autoguardado += 1
        self._actualizar_estado()

    def _actualizar_estado(self):
        """Actualiza el estado general del ecosistema."""
        cantidad_animales = len(self.animales)
        cantidad_plantas = len(self.plantas)
        
        carnivoros = sum(1 for a in self.animales.values() if a.__class__.__name__ == 'Carnivoro')
        herbivoros = sum(1 for a in self.animales.values() if a.__class__.__name__ == 'Herbivoro')
        omnivoros = sum(1 for a in self.animales.values() if a.__class__.__name__ == 'Omnivoro')
        
        if cantidad_animales == 0:
            self.estado = 'Extinción'
        elif carnivoros == 0 and herbivoros > 0:
            self.estado = 'Herbívoros Dominantes'
        elif herbivoros == 0 and carnivoros > 0:
            self.estado = 'Carnívoros Dominantes'
        elif cantidad_plantas == 0:
            self.estado = 'Escasez de Recursos'
        else:
            self.estado = 'Normal'

    def resumen(self):
        """Retorna un resumen del estado actual del ecosistema."""
        return {
            'ciclo': self.ciclo,
            'animales': len(self.animales),
            'plantas': len(self.plantas),
            'estado': self.estado,
            'config': self.config,
            'tipos_animales': {
                'carnivoros': sum(1 for a in self.animales.values() if a.__class__.__name__ == 'Carnivoro'),
                'herbivoros': sum(1 for a in self.animales.values() if a.__class__.__name__ == 'Herbivoro'),
                'omnivoros': sum(1 for a in self.animales.values() if a.__class__.__name__ == 'Omnivoro'),
            }
        }

    def necesita_autoguardado(self):
        """Verifica si es momento de hacer autoguardado."""
        return self.ciclos_desde_autoguardado >= self.autoguardado_cada_n_ciclos

    def reset_ciclos_autoguardado(self):
        """Reinicia el contador de ciclos para autoguardado."""
        self.ciclos_desde_autoguardado = 0

    def serializar(self):
        """Serializa el estado completo del ecosistema."""
        return {
            'ciclo': self.ciclo,
            'animales': self.animales,
            'plantas': self.plantas,
            'estado': self.estado,
            'config': self.config,
            'version': self.version,
        }

    def deserializar(self, datos):
        """Restaura el ecosistema desde datos serializados."""
        self.ciclo = datos.get('ciclo', 0)
        self.estado = datos.get('estado', 'Normal')
        self.config = datos.get('config', {})
        self.version = datos.get('version', '1.0')
        # Los animales y plantas se restauran en un nivel superior

