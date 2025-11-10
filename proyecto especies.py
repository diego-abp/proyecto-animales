import pygame
import math
import time
import random

class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, tiempo_vida_max=100, sync_vida_with_tiempo=False, color=(255,255,255), size=15, is_baby=False, is_champion=False):
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
        self.is_champion = is_champion
        self.birth_time = time.time()
        self.growth_duration = 30 # Segundos para crecer a adulto
        # Atributo para el modo de apareamiento
        self.mating_mode = False
        self.emergency_partner = None # Para saber a quién buscar en emergencia
        self.emergency_mating_mode = False # Nuevo modo para cruce de especies
        # --- ATRIBUTOS DE "PERSONALIDAD" PARA MOVIMIENTO ÚNICO ---
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
        """
        Reduce la vida de la especie con el tiempo, simulando el envejecimiento.
        No se aplica a plantas o entidades con vida infinita.
        """
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
        # Los carnívoros tienen un tiempo de vida de 2 minutos (120s). Se mueven más rápido para cazar.
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, tiempo_vida_max=120, color=color or (255, 0, 0), size=7 if is_baby else 15, is_baby=is_baby, is_champion=False)
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
        self.food_target = None # Para buscar cadáveres
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

        # --- LÓGICA DE BÚSQUEDA DE CURACIÓN (ALTA PRIORIDAD) ---
        if self.vida < self.vida_max * 0.35:
            planta_curativa = self.buscar_planta_cercana(all_species)
            if planta_curativa:
                # Anular otras acciones y moverse hacia la planta
                self.mating_mode = False
                self.hunt_state = 'wandering'
                self.food_target = None
                self.target = None
                self.mover_hacia(planta_curativa.posicion_x, planta_curativa.posicion_y)
                return None # Prioridad es curarse


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

            # --- LÓGICA DE COMER CADÁVERES (PRIORIDAD SI LA VIDA ES BAJA) ---
            # Si tiene poca vida, buscará comida fácil (cadáveres) antes que cazar.
            if self.vida < self.vida_max * 0.7:
                if self.food_target is None or self.food_target.nutricion <= 0:
                    self.food_target = self.buscar_cadaver_cercano(all_species)

                if self.food_target:
                    dist_comida = math.hypot(self.posicion_x - self.food_target.posicion_x, self.posicion_y - self.food_target.posicion_y)
                    if dist_comida < self.food_target.size + 5: # Si está suficientemente cerca para comer
                        # Comer el cadáver
                        self.vida = min(self.vida_max, self.vida + 25) # Recupera 25 de vida
                        self.food_target.nutricion -= 25
                        self.last_attack = ahora # Reutilizar cooldown de ataque como cooldown de comer
                        if self.food_target.nutricion <= 0:
                            self.food_target = None # Se lo ha comido todo
                        return None
                    else:
                        # Moverse hacia el cadáver
                        self.mover_hacia(self.food_target.posicion_x, self.food_target.posicion_y)
                        return None
            else:
                # Si tiene mucha vida, olvida el cadáver y se centra en cazar
                self.food_target = None


            # Búsqueda constante de presas: cualquier entidad que no sea un Carnívoro o una Planta.
            presa_mas_cercana = None
            distancia_minima = self.detection_radius

            for entidad in all_species.values():
                # No puede cazarse a sí mismo, a otros carnívoros o a plantas.
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

    def buscar_cadaver_cercano(self, all_species):
        """Busca el cadáver más cercano."""
        cadaver_cercano = None
        distancia_min = self.detection_radius # Usa el mismo radio de detección
        for entidad in all_species.values():
            if isinstance(entidad, Cadaver):
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    cadaver_cercano = entidad
        return cadaver_cercano


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
        # Los herbívoros tienen un tiempo de vida de 2 minutos (120s)
        super().__init__(x, y, vida, reproducirse, salto, False, True, True, tiempo_vida_max=120, color=color or (0, 200, 0), size=7 if is_baby else 15, is_baby=is_baby, is_champion=False)

    def puede_reproducirse(self):
        """Los herbívoros pueden reproducirse si tienen suficiente vida."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y, is_champion=False): # Added is_champion parameter
        """Crea una nueva cría de Herbívoro."""
        if is_champion:
            # Cría de emergencia: mucho más fuerte
            vida_cria = 200
            # Color más brillante y saturado
            r = min(255, self.color[0] + 80)
            g = min(255, self.color[1] + 80)
            b = min(255, self.color[2] + 80)
            color_cria = (r, g, b)
            self.vida -= self.vida_max * 0.5 # Cuesta más energía
            cria = Herbivoro(x, y, vida_cria, color=color_cria, is_baby=True)
            cria.is_champion = True
            cria.atacar = True # Champion Herbivore can attack
            cria.attack_power = 25 # Attack power similar to a normal Carnivore
            cria.detection_radius = 150 # Can detect enemies
            cria.chase_radius = 250 # Can chase enemies
            cria.attack_cooldown = 2.0 # Attack cooldown
            cria.last_attack = 0.0 # Initialize last attack time
            cria.hunt_state = 'wandering' # New state for champion herbivore
            cria.target = None # New target for champion herbivore
            cria.salto *= 1.1 # Slightly faster
            cria.max_size *= 1.1 # Slightly larger
        else:
            # Cría normal
            vida_cria = self.vida_max // 2
            # Generar una tonalidad de color ligeramente diferente
            r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
            g = max(0, min(255, self.color[1] + random.randint(-20, 20)))
            b = max(0, min(255, self.color[2] + random.randint(-30, 30)))
            color_cria = (r, g, b)
            # Los padres pierden algo de vida al reproducirse
            self.vida -= self.vida_max * 0.25 # Normal energy cost
            cria = Herbivoro(x, y, vida_cria, color=color_cria, is_baby=True)

        return cria

    def mover(self, screen_width, screen_height, all_species={}): # Changed posibles_presas to all_species for consistency
        """El herbívoro deambula y huye, pero también busca pareja activamente."""
        # La lógica de huida de la clase base tiene prioridad
        if self.escape_state == 'escaping':
            super().mover(screen_width, screen_height, all_species)
            if self.escape_state == 'escaping': # Comprobar si sigue huyendo
                self.mating_mode = False # Si huye, no se aparea
                return

        # --- LÓGICA DE BÚSQUEDA DE CURACIÓN (ALTA PRIORIDAD) ---
        if self.vida < self.vida_max * 0.35:
            planta_curativa = self.buscar_planta_cercana(all_species)
            if planta_curativa:
                # Anular apareamiento y moverse a la planta
                self.mating_mode = False
                self.mover_hacia(planta_curativa.posicion_x, planta_curativa.posicion_y)
                return None # Prioridad es curarse

        # --- LÓGICA DE APAREAMIENTO DE EMERGENCIA (PRIORIDAD ALTA) ---
        if self.emergency_mating_mode:
            if self.emergency_partner and self.emergency_partner.vida > 0:
                self.mover_hacia(self.emergency_partner.posicion_x, self.emergency_partner.posicion_y)
                return # Prioridad es encontrar a la pareja designada


        # --- LÓGICA DE ATAQUE DE CAMPEÓN HERBÍVORO (PRIORIZA CARNÍVOROS) ---
        # Solo si es un campeón y puede atacar
        if self.is_champion and self.atacar:
            ahora = time.time()
            if getattr(self, 'hunt_state', 'wandering') == 'wandering':
                # Buscar Carnívoro más cercano
                carnivoro_cercano = None
                distancia_minima = getattr(self, 'detection_radius', 150) # Use attribute if exists, else default
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
                # Asegurarse de que el objetivo sigue siendo un carnívoro y está vivo
                if not isinstance(self.target, Carnivoro) or getattr(self.target, 'vida', 0) <= 0:
                    self.hunt_state = 'wandering'
                    self.target = None
                else:
                    distancia = math.hypot(self.posicion_x - self.target.posicion_x, self.posicion_y - self.target.posicion_y)
                    chase_radius = getattr(self, 'chase_radius', 250)
                    if distancia > chase_radius:
                        # Perdió el objetivo, vuelve a deambular
                        self.hunt_state = 'wandering'
                        self.target = None
                    else:
                        # Moverse hacia el objetivo o atacar
                        puede_atacar = (ahora - getattr(self, 'last_attack', 0.0)) >= getattr(self, 'attack_cooldown', 2.0)
                        if distancia < 25 and puede_atacar:
                            # Atacar al carnívoro
                            self.target.vida = max(0, self.target.vida - self.attack_power)
                            self.last_attack = ahora
                            return {'damage': self.attack_power, 'target': self.target} # Devolver info de ataque
                        else:
                            # Perseguir
                            velocidad = self.salto * (0.5 if 25 <= distancia < 75 else 1.0)
                            self.mover_hacia(self.target.posicion_x, self.target.posicion_y, velocidad=velocidad)
                            return None # El campeón está ocupado atacando/persiguiendo
            
            # Si el campeón no está atacando/persiguiendo un carnívoro, puede deambular
            if getattr(self, 'hunt_state', 'wandering') == 'wandering':
                super().mover(screen_width, screen_height, all_species)
                return None # El campeón ya ha gestionado su movimiento

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
        return super().mover(screen_width, screen_height, all_species) # This will be called if champion logic didn't return

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

    def buscar_pareja_emergencia(self, all_species):
        """Busca un Omnivoro para el cruce de emergencia."""
        mejor_pareja = None
        distancia_min = float('inf')
        for entidad in all_species.values():
            # Un Herbívoro busca un Omnívoro
            if isinstance(entidad, Omnivoro) and entidad.puede_reproducirse():
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = entidad
        return mejor_pareja


class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=3, color=None, is_baby=False, is_champion=False):
        # Los omnívoros tienen un tiempo de vida de 2 minutos (120s)
        # El tamaño se usa como radio, así que un omnívoro de 20x20 tiene un "radio" de 10
        super().__init__(x, y, vida, reproducirse, salto=salto, atacar=True, correr=True, comer=True, tiempo_vida_max=120, color=color or (128, 0, 128), size=5 if is_baby else 10, is_baby=is_baby, is_champion=is_champion)
        self.max_size = 10  # Tamaño adulto (radio)
        self.presa = None
        self.modo_caza = False # Alterna entre cazar y deambular
        self.food_target = None # Para buscar cadáveres
        self.detection_radius = 150 # Default detection radius for omnivores
        self.chase_radius = 250 # Default chase radius for omnivores
        self.attack_power = 15 # Poder de ataque normal

        
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

        if self.vida < self.vida_max * 0.35: # LÓGICA DE BÚSQUEDA DE CURACIÓN (ALTA PRIORIDAD)
            planta_curativa = self.buscar_cadaver_cercano(posibles_presas) # Reutilizamos la función, pero debería ser buscar_planta_cercana
            planta_curativa = self.buscar_planta_cercana(posibles_presas)
            if planta_curativa:
                # Anular otras acciones y moverse hacia la planta
                self.mating_mode = False
                self.modo_caza = False
                self.food_target = None
                self.presa = None
                self.mover_hacia(planta_curativa.posicion_x, planta_curativa.posicion_y)
                return None # Prioridad es curarse

        # --- LÓGICA DE APAREAMIENTO DE EMERGENCIA (PRIORIDAD ALTA) ---
        if self.emergency_mating_mode:
            if self.emergency_partner and self.emergency_partner.vida > 0:
                self.mover_hacia(self.emergency_partner.posicion_x, self.emergency_partner.posicion_y)
                return # Prioridad es encontrar a la pareja designada


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
            # --- LÓGICA DE COMER CADÁVERES (PRIORIDAD EN MODO CAZA) ---
            if self.food_target is None or self.food_target.nutricion <= 0:
                self.food_target = self.buscar_cadaver_cercano(posibles_presas)
            
            if self.food_target:
                dist_comida = math.hypot(self.posicion_x - self.food_target.posicion_x, self.posicion_y - self.food_target.posicion_y)
                if dist_comida < self.food_target.size + 5:
                    # Comer
                    self.vida = min(self.vida_max, self.vida + 20)
                    self.food_target.nutricion -= 20
                    self.last_random_move_time = time.time() # Cooldown para no comer instantáneamente
                    if self.food_target.nutricion <= 0:
                        self.food_target = None
                    return None
                else:
                    # Moverse hacia el cadáver
                    self.mover_hacia(self.food_target.posicion_x, self.food_target.posicion_y)
                    return None
            else:
                # Si no hay cadáveres, busca presas vivas (o carnívoros si es campeón)
                self.food_target = None

            # --- LÓGICA DE CAZA DE CAMPEÓN OMNÍVORO (PRIORIZA CARNÍVOROS) ---
            if self.is_champion:
                # Si no tiene presa o la presa no es un carnívoro o está muerta
                if self.presa is None or not isinstance(self.presa, Carnivoro) or getattr(self.presa, 'vida', 0) <= 0:
                    # Buscar Carnívoro más cercano
                    carnivoro_cercano = None
                    distancia_minima = getattr(self, 'detection_radius', 200) # Usar detection_radius del campeón
                    for entidad in posibles_presas.values(): # all_species es el parámetro correcto
                        if isinstance(entidad, Carnivoro):
                            dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                            if dist < distancia_minima:
                                distancia_minima = dist
                                carnivoro_cercano = entidad
                    self.presa = carnivoro_cercano
                
                if self.presa: # Si un carnívoro es el objetivo
                    distancia = math.hypot(self.posicion_x - self.presa.posicion_x, self.posicion_y - self.presa.posicion_y)
                    chase_radius = getattr(self, 'chase_radius', 300) # Usar chase_radius del campeón
                    if distancia > chase_radius:
                        # Perdió el objetivo, vuelve a deambular
                        self.presa = None
                    else:
                        # Moverse hacia el objetivo o atacar
                        puede_atacar = (ahora - getattr(self, 'last_attack', 0.0)) >= getattr(self, 'attack_cooldown', 1.5) # Omnivores have their own cooldown
                        if distancia < 25 and puede_atacar:
                            # Atacar al carnívoro
                            self.presa.vida = max(0, self.presa.vida - self.attack_power)
                            self.last_attack = ahora
                            return {'damage': self.attack_power, 'target': self.presa} # Devolver info de ataque
                        else:
                            # Perseguir
                            velocidad = self.salto * (0.5 if 25 <= distancia < 75 else 1.0)
                            self.mover_hacia(self.presa.posicion_x, self.presa.posicion_y, velocidad=velocidad)
                            return None # El campeón está ocupado atacando/persiguiendo
            
            # --- LÓGICA DE CAZA NORMAL (SI NO ES CAMPEÓN O NO ENCONTRÓ CARNÍVORO) ---
            # Si no es campeón o el campeón no encontró un carnívoro, busca otras presas
            if self.presa and (self.presa not in posibles_presas.values() or self.presa.vida <= 0): # all_species
                self.presa = None

            # Comportamiento de caza (similar al carnívoro pero menos agresivo)
            if self.presa and (self.presa not in posibles_presas.values() or self.presa.vida <= 0):
                self.presa = None

            if not self.presa:
                presa_mas_cercana = None
                distancia_minima = getattr(self, 'detection_radius', 100) # Usar detection_radius del omnívoro
                for especie in posibles_presas.values():
                    if especie is self or isinstance(especie, (Carnivoro, Omnivoro, Planta, Cadaver)):
                        continue
                    dist = math.sqrt((self.posicion_x - especie.posicion_x)**2 + (self.posicion_y - especie.posicion_y)**2)
                    if dist < distancia_minima:
                        distancia_minima = dist
                        presa_mas_cercana = especie
                self.presa = presa_mas_cercana

            if self.presa:
                velocidad_caza = self.salto * 0.8 # Omnivores are not as fast as carnivores
                dx = self.presa.posicion_x - self.posicion_x
                dy = self.presa.posicion_y - self.posicion_y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    self.posicion_x += (dx / dist) * velocidad_caza
                    self.posicion_y += (dy / dist) * velocidad_caza
                    # Check for attack range and cooldown
                    if dist < 25 and (ahora - getattr(self, 'last_attack', 0.0)) >= getattr(self, 'attack_cooldown', 1.5):
                        self.presa.vida = max(0, self.presa.vida - self.attack_power)
                        self.last_attack = ahora
                        return {'damage': self.attack_power, 'target': self.presa}
            else: # Si no encuentra presa en modo caza, deambula
                super().mover(screen_width, screen_height, posibles_presas)
        else: # Si no está en modo caza, deambula
            return super().mover(screen_width, screen_height, posibles_presas) # all_species

    def puede_reproducirse(self):
        """Los omnívoros pueden reproducirse si tienen suficiente vida."""
        return self.reproducirse and self.vida >= self.vida_max * 0.7

    def reproducir(self, x, y, is_champion=False):
        """Crea una nueva cría de Omnívoro."""
        if is_champion:
            # Cría de emergencia: más fuerte que un carnívoro
            vida_cria = 250
            # Color más brillante y saturado
            r = min(255, self.color[0] + 80)
            g = min(255, self.color[1] + 80)
            b = min(255, self.color[2] + 80)
            color_cria = (r, g, b)
            color_cria = (255, 255, 0) # Híbrido siempre es amarillo brillante
            self.vida -= self.vida_max * 0.5 # Cuesta más energía
            cria = Omnivoro(x, y, vida_cria, color=color_cria, is_baby=True, is_champion=True)
            cria.attack_power = 45 # Poder de ataque de campeón aumentado
            cria.attack_cooldown = 1.5 # Cooldown de ataque
            cria.last_attack = 0.0 # Inicializar
            cria.detection_radius = 250 # Mayor radio de detección
            cria.salto *= 1.2 # Más rápido
            cria.max_size *= 1.25 # Más grande
            return cria
        else:
            vida_cria = self.vida_max // 2
            r = max(0, min(255, self.color[0] + random.randint(-30, 30)))
            g = max(0, min(255, self.color[1] + random.randint(-30, 30)))
            b = max(0, min(255, self.color[2] + random.randint(-20, 20)))
            color_cria = (r, g, b)
            self.vida -= self.vida_max * 0.25 # Normal energy cost
            cria = Omnivoro(x, y, vida_cria, color=color_cria, is_baby=True)
            return cria

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

    def buscar_pareja_emergencia(self, all_species):
        """Busca un Herbivoro para el cruce de emergencia."""
        mejor_pareja = None
        distancia_min = float('inf')
        for entidad in all_species.values():
            # Un Omnívoro busca un Herbívoro
            if isinstance(entidad, Herbivoro) and entidad.puede_reproducirse():
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    mejor_pareja = entidad
        return mejor_pareja


    def buscar_cadaver_cercano(self, all_species):
        """Busca el cadáver más cercano."""
        cadaver_cercano = None
        distancia_min = 150 # Radio de detección
        for entidad in all_species.values():
            if isinstance(entidad, Cadaver):
                dist = math.hypot(self.posicion_x - entidad.posicion_x, self.posicion_y - entidad.posicion_y)
                if dist < distancia_min:
                    distancia_min = dist
                    cadaver_cercano = entidad
        return cadaver_cercano

class Cadaver(Especies):
    def __init__(self, x, y, original_size, original_color, original_shape='circle'):
        # Los cadáveres no se mueven, no se reproducen, etc.
        super().__init__(x, y, vida=0, reproducirse=False, salto=0)
        self.nutricion = original_size * 5 # Valor nutricional basado en el tamaño
        self.size = original_size
        # Convertir el color original a escala de grises para la apariencia de cadáver
        gris = int(sum(original_color) / 3 * 0.6) # Más oscuro
        self.color = (gris, gris, gris)
        self.original_shape = original_shape # 'circle' o 'rect'
        self.tiempo_creacion = time.time()
        self.tiempo_descomposicion_max = 45 # Segundos hasta que desaparece


class Planta(Especies):
    def __init__(self, x, y, reproducirse=False):
        # Las plantas son permanentes. No tienen vida ni tiempo de vida.
        # Pasamos valores dummy a la clase base y desactivamos la reproducción por ahora.
        super().__init__(x, y, float('inf'), reproducirse, 0, False, False, False)
        # Atributos para la curación
        self.healing_target = None
        self.time_on_plant = 0
        self.is_healing = False
        self.heal_amount = 15  # Puntos de vida por tick
        self.heal_cooldown = 0.5 # Cura cada medio segundo
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

        # --- Cargar y tintar fondo ---
        try:
            # Cargar la imagen original
            background_image = pygame.image.load("assets/fondos/fondos.png").convert()
            # Escalarla al tamaño de la ventana
            self.background_image = pygame.transform.scale(background_image, (self.ancho, self.alto))
            
            # Crear una superficie para el tinte verde
            green_tint = pygame.Surface(self.background_image.get_size()).convert_alpha()
            # Rellenar con un verde semi-transparente (R, G, B, Alpha). Ajusta el último valor (alpha) para más o menos tinte.
            green_tint.fill((20, 90, 40, 120))
            self.background_image.blit(green_tint, (0, 0))
        except pygame.error:
            self.background_image = None # Si no se encuentra, se usará un color sólido

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

        self.personaje = Personaje(200, 200, 1000) # Vida del jugador aumentada x10
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
                    (isinstance(otra_especie, type(especie)) or especie.emergency_mating_mode or otra_especie.emergency_mating_mode) and # Permite cruce
                    hasattr(especie, 'puede_reproducirse') and especie.puede_reproducirse() and 
                    hasattr(otra_especie, 'puede_reproducirse') and otra_especie.puede_reproducirse()):
                    
                    # Verificar que no se exceda el límite de población para este tipo de especie
                    # Solo puede haber una cría a la vez por tipo de especie.
                    # Para el híbrido, solo puede haber uno en total.
                    hay_campeon_existente = any(e.is_champion for e in self.especies_vivas.values())

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
                        
                        # Lógica de reproducción
                        if especie.emergency_mating_mode or otra_especie.emergency_mating_mode:
                            if hay_campeon_existente: continue # Solo un campeón a la vez
                            # Siempre es el Omnívoro el que "da a luz" al híbrido campeón
                            if isinstance(especie, Omnivoro):
                                nueva_especie = especie.reproducir(new_x, new_y, is_champion=True)
                            else: # Si la especie es Herbivoro, la otra es Omnivoro
                                nueva_especie = otra_especie.reproducir(new_x, new_y, is_champion=True)
                        else: # Reproducción normal
                            if hay_cria_existente: continue
                            nueva_especie = especie.reproducir(new_x, new_y)

                        if nueva_especie:
                            # Actualizar el tiempo del último intento de reproducción
                            especie.ultimo_intento_reproduccion = tiempo_actual
                            otra_especie.ultimo_intento_reproduccion = tiempo_actual
                            
                            # --- SEPARACIÓN POST-REPRODUCCIÓN --- (Se aplica a ambos casos)
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
                            especie.emergency_mating_mode = False
                            otra_especie.emergency_mating_mode = False
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

    def _check_emergency_reproduction(self):
        """
        Activa el modo de apareamiento de emergencia si solo queda un herbívoro o un omnívoro,
        para que busquen cruzarse.
        """
        # Primero, resetear todos los flags de emergencia para re-evaluar la situación
        for e in self.especies_vivas.values():
            e.emergency_mating_mode = False
            e.emergency_partner = None

        # Contar cuántos individuos de cada tipo hay
        herbivoros_vivos = [e for e in self.especies_vivas.values() if isinstance(e, Herbivoro) and not e.is_baby]
        omnivoros_vivos = [e for e in self.especies_vivas.values() if isinstance(e, Omnivoro) and not e.is_baby]

        # Caso 1: Solo queda un herbívoro y hay omnívoros para cruzar
        if len(herbivoros_vivos) == 1 and len(omnivoros_vivos) > 0:
            survivor = herbivoros_vivos[0]
            if survivor.puede_reproducirse():
                # Encontrar al omnívoro más cercano como pareja forzada
                best_partner = min(omnivoros_vivos, 
                                   key=lambda p: math.hypot(survivor.posicion_x - p.posicion_x, survivor.posicion_y - p.posicion_y) 
                                   if p.puede_reproducirse() else float('inf'))
                
                if best_partner and best_partner.puede_reproducirse():
                    survivor.emergency_mating_mode = True
                    best_partner.emergency_mating_mode = True
                    survivor.emergency_partner = best_partner
                    best_partner.emergency_partner = survivor
        
        # Caso 2: Solo queda un omnívoro y hay herbívoros para cruzar
        elif len(omnivoros_vivos) == 1 and len(herbivoros_vivos) > 0:
            survivor = omnivoros_vivos[0]
            if survivor.puede_reproducirse():
                # Encontrar al herbívoro más cercano como pareja forzada
                best_partner = min(herbivoros_vivos, 
                                   key=lambda p: math.hypot(survivor.posicion_x - p.posicion_x, survivor.posicion_y - p.posicion_y)
                                   if p.puede_reproducirse() else float('inf'))

                if best_partner and best_partner.puede_reproducirse():
                    survivor.emergency_mating_mode = True
                    best_partner.emergency_mating_mode = True
                    survivor.emergency_partner = best_partner
                    best_partner.emergency_partner = survivor
        
        # No es necesario un 'else' porque el reseteo se hace al principio de la función,
        # asegurando que el modo de emergencia solo esté activo si se cumplen las condiciones
        # en este mismo fotograma.


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
                # La curación es ahora instantánea al contacto, sin el retardo de 2 segundos.
                plant.is_healing = True
                plant.healing_target = current_target
                
                # Aplicar curación si el cooldown ha pasado
                if ahora - plant.last_heal_time >= plant.heal_cooldown:
                    plant.last_heal_time = ahora
                    target = plant.healing_target
                    if target.vida < target.vida_max:
                        target.vida = min(target.vida_max, target.vida + plant.heal_amount)
            else:
                # Nadie en la planta, resetear estado
                plant.healing_target = None
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
        # Primero, actualizamos la vida por tiempo para todas las especies
        self._update_vida_por_tiempo()

        # Ahora, procedemos con la IA de movimiento y ataque

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

            if attack_info:
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

    def _update_vida_por_tiempo(self):
        """Llama al método de actualización de vida por tiempo para cada especie."""
        for especie in self.especies_vivas.values():
            especie.update_vida_por_tiempo()

    def draw(self):
        # Fondo
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((130, 170, 110)) # Color de fondo alternativo si la imagen no carga
        
        # --- GESTIÓN DE MUERTES Y CADÁVERES ---
        nombres_muertos = []
        nuevos_cadaveres = {}
        
        # Comprobar qué especies han muerto por daño y marcarlas para eliminar
        for nombre, especie in list(self.especies_vivas.items()):
            # Los cadáveres se gestionan por su nutrición/tiempo
            if isinstance(especie, Cadaver):
                if especie.nutricion <= 0:
                    nombres_muertos.append(nombre)
                continue
            
            if hasattr(especie, 'vida') and especie.vida <= 0 and not isinstance(especie, Planta):
                nombres_muertos.append(nombre)
                # Crear un cadáver en su lugar si es un animal
                if isinstance(especie, (Carnivoro, Herbivoro, Omnivoro)):
                    forma = 'rect' if isinstance(especie, Omnivoro) else 'circle'
                    cadaver = Cadaver(especie.posicion_x, especie.posicion_y, especie.size, especie.color, forma)
                    nombre_cadaver = f"cadaver_{time.time()}"
                    nuevos_cadaveres[nombre_cadaver] = cadaver

        # Eliminar especies muertas
        for nombre in nombres_muertos:
            del self.especies_vivas[nombre]
        
        # Añadir los nuevos cadáveres al diccionario principal de entidades
        self.especies_vivas.update(nuevos_cadaveres)

        # Dibujar el sprite del personaje
        if self.animations:
            # Obtener la animación y el cuadro actual
            animation_strip = self.animations[self.personaje.state]
            self.personaje.update_animation(animation_strip)
            current_frame = animation_strip[self.personaje.frame_index]

            # Voltear la imagen si la dirección es izquierda
            flip = self.personaje.direction == 'left'
            image_to_draw = pygame.transform.flip(current_frame, flip, False)

            # --- Dibujar contorno para el jugador ---
            # Creamos una máscara a partir de la imagen para dibujar solo el contorno de la silueta.
            mask = pygame.mask.from_surface(image_to_draw)
            outline_surface = mask.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
            rect = image_to_draw.get_rect(midtop=(int(self.personaje.posicion_x), int(self.personaje.posicion_y)))
            # Dibujar el contorno en las 4 direcciones diagonales
            self.screen.blit(outline_surface, (rect.x - 1, rect.y - 1))
            self.screen.blit(outline_surface, (rect.x + 1, rect.y - 1))
            self.screen.blit(outline_surface, (rect.x - 1, rect.y + 1))
            self.screen.blit(outline_surface, (rect.x + 1, rect.y + 1))
            
            # Dibujar el sprite principal encima del contorno
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
            elif isinstance(especie, Cadaver):
                # Dibujar el cadáver según su forma original pero en gris
                if especie.original_shape == 'circle':
                    pygame.draw.circle(self.screen, (20,20,20), (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size) + 1)
                    pygame.draw.circle(self.screen, especie.color, (int(especie.posicion_x), int(especie.posicion_y)), int(especie.size))
                else: # rect
                    size = int(especie.size) * 2
                    x, y = int(especie.posicion_x - size // 2), int(especie.posicion_y - size // 2)
                    pygame.draw.rect(self.screen, (20,20,20), (x - 1, y - 1, size + 2, size + 2))
                    pygame.draw.rect(self.screen, especie.color, (x, y, size, size))
            elif isinstance(especie, Planta):
                # Dibujar la planta como un triángulo verde con un contorno negro
                color_contorno = (50, 255, 50) if especie.is_healing else (0, 0, 0) # Verde lima brillante al curar
                size = 12 # Tamaño aumentado
                p1 = (int(especie.posicion_x), int(especie.posicion_y) - size)
                p2 = (int(especie.posicion_x) - size, int(especie.posicion_y) + size)
                p3 = (int(especie.posicion_x) + size, int(especie.posicion_y) + size)
                # Primero el relleno verde más brillante
                pygame.draw.polygon(self.screen, (0, 140, 20), [p1, p2, p3])
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
        # --- Dibujar texto con contorno ---
        texto_str = "Flechas/WASD = mover, Espacio = atacar, ESC = salir"
        pos_x, pos_y = 10, self.alto - 25
        color_texto = (200, 200, 255) # Un azul más claro para que resalte
        color_contorno = (0, 0, 0)
        # Dibujar el contorno (texto en negro desplazado)
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            self.screen.blit(self.font.render(texto_str, True, color_contorno), (pos_x + dx, pos_y + dy))
        # Dibujar el texto principal encima
        self.screen.blit(self.font.render(texto_str, True, color_texto), (pos_x, pos_y))

        pygame.display.flip()

    def _update_cadaveres(self):
        """Actualiza el estado de los cadáveres, como la descomposición."""
        ahora = time.time()
        for especie in self.especies_vivas.values():
            if isinstance(especie, Cadaver):
                if ahora - especie.tiempo_creacion > especie.tiempo_descomposicion_max:
                    especie.nutricion = 0 # Marcar para eliminación por descomposición

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

            # Verificar si alguna especie puede reproducirse
            self.check_reproduction()

            # Verificar si alguna especie necesita reproducción de emergencia
            self._check_emergency_reproduction()

            # Actualizar lógica de curación de las plantas
            self._update_plant_healing()

            # Actualizar crecimiento de las crías
            self._update_growth()

            # Actualizar estado de los cadáveres (descomposición)
            self._update_cadaveres()

            # Dibujar
            self.draw()

            # Mantener FPS
            self.clock.tick(self.fps)

        pygame.quit()

if __name__ == "__main__":
    print("=== Juego en 2 capas Lógica y Vista ===")
    juego = VistaPygame()
    juego.iniciar()
