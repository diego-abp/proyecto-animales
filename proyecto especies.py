import pygame
import math
import time
import random


class Especies:
    def __init__(self, x, y, vida, reproducirse, salto=5, atacar=False, correr=False, comer=False, tiempo_vida_max=100, sync_vida_with_tiempo=False):
        self.posicion_x = x
        self.posicion_y = y
        # vida es la vida actual (puede bajar por daño), vida_max es la vida inicial máxima
        self.vida = vida
        self.vida_max = vida
        self.vista = None  # Referencia a la vista que se establecerá después
        self.reproducirse = reproducirse
        self.salto = salto
        self.atacar = atacar
        self.correr = correr
        self.comer = comer
        self.tiempo_vida_max = tiempo_vida_max
        self.tiempo_vida_actual = tiempo_vida_max
        self.ultimo_update = time.time()
        # Si es True, el envejecimiento por tiempo también reduce la vida (HP)
        # Atributos para movimiento aleatorio
        self.last_random_move_time = time.time()
        self.random_move_delay = random.uniform(1, 3) # Cambiar de dirección cada 1-3 segundos
        self.random_move_target = None
        self.sync_vida_with_tiempo = sync_vida_with_tiempo

    def update_tiempo_vida(self):
        """Actualiza el tiempo de vida de la especie. Devuelve True si sigue viva, False si ha muerto."""
        ahora = time.time()
        tiempo_transcurrido = ahora - self.ultimo_update
        # Reducir tiempo de vida más lentamente (0.3 unidades cada segundo)
        self.tiempo_vida_actual = max(0, self.tiempo_vida_actual - (tiempo_transcurrido * 0.3))

        # Si la especie sincroniza vida con el tiempo, reducir la vida (HP) proporcionalmente
        if getattr(self, 'sync_vida_with_tiempo', False) and self.tiempo_vida_max > 0:
            # pérdida de vida por envejecimiento proporcional al tiempo transcurrido
            aging_loss = (tiempo_transcurrido * 0.3 / self.tiempo_vida_max) * getattr(self, 'vida_max', 0)
            self.vida = max(0, self.vida - aging_loss)

        # Mostrar advertencia cuando el tiempo de vida es bajo
        if self.tiempo_vida_actual < self.tiempo_vida_max * 0.3 and self.vista:  # Menos del 30% de vida
            if random.random() < 0.1:  # Solo mostrar la advertencia ocasionalmente
                self.vista.damage_popups.append({
                    'text': "⚠️",  # Emoji de advertencia
                    'x': self.posicion_x,
                    'y': self.posicion_y - 25,
                    'start': pygame.time.get_ticks()
                })

        self.ultimo_update = ahora
        return self.tiempo_vida_actual > 0
    
    def get_porcentaje_vida(self):
        """Devuelve el porcentaje de tiempo de vida restante."""
        return (self.tiempo_vida_actual / self.tiempo_vida_max) * 100

    def puede_reproducirse(self):
        """Verifica si la especie puede reproducirse."""
        # Solo puede reproducirse si tiene más del 30% de vida y tiempo de vida
        return (self.vida / self.vida_max > 0.3 and 
                self.tiempo_vida_actual / self.tiempo_vida_max > 0.3 and 
                self.reproducirse)

    def reproducir(self, x, y):
        """Crea una nueva instancia de la misma especie."""
        if self.puede_reproducirse():
            # Crear nueva instancia con vida completa pero tiempo de vida reducido
            nueva_especie = self.__class__(x, y, self.vida_max)
            # La reproducción consume energía
            self.vida = max(self.vida - self.vida_max * 0.2, 1)  # Cuesta 20% de vida
            return nueva_especie
        return None

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
        self.posicion_x += nx * velocidad
        self.posicion_y += ny * velocidad
        # Wrap (coincide con límites usados en Personaje)
        if self.posicion_x < 0:
            self.posicion_x = 490
        elif self.posicion_x > 490:
            self.posicion_x = 0
        if self.posicion_y < 0:
            self.posicion_y = 360
        elif self.posicion_y > 360:
            self.posicion_y = 0

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Comportamiento de movimiento base: deambular aleatoriamente y buscar pareja."""
        ahora = time.time()
        
        # Buscar pareja cercana del mismo tipo
        pareja_cercana = None
        menor_distancia = float('inf')
        for otra in posibles_presas.values():
            if type(otra) == type(self) and otra is not self:
                dist = math.hypot(self.posicion_x - otra.posicion_x, 
                                self.posicion_y - otra.posicion_y)
                if dist < menor_distancia:
                    menor_distancia = dist
                    pareja_cercana = otra

        # Si hay una pareja cercana, moverse hacia ella más rápido
        if pareja_cercana and menor_distancia > 10:
            self.mover_hacia(pareja_cercana.posicion_x, pareja_cercana.posicion_y, self.salto * 1.5)
            return

        # Si no hay pareja o ya está muy cerca, moverse aleatoriamente
        if self.random_move_target is None or ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            self.random_move_delay = random.uniform(1, 3)  # Intervalos más cortos
            # Elige un punto aleatorio en la pantalla
            self.random_move_target = (random.randint(0, screen_width), 
                                     random.randint(0, screen_height))

        # Moverse hacia el objetivo aleatorio
        if self.random_move_target:
            self.mover_hacia(self.random_move_target[0], self.random_move_target[1])
            # Si llega cerca del objetivo, lo olvida para poder elegir uno nuevo
            if math.hypot(self.posicion_x - self.random_move_target[0], 
                         self.posicion_y - self.random_move_target[1]) < 10:
                self.random_move_target = None

class Carnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=2):
        # Los carnívoros tienen tiempo de vida medio (150). Se mueven más rápido para cazar.
        super().__init__(x, y, vida, reproducirse, salto, True, True, True, tiempo_vida_max=150)
        # Atributos de ataque: menos daño por golpe y cooldown menor cuando ataca al personaje
        self.attack_power = 25
        self.attack_cooldown = 2.0
        self.last_attack = 0
        # El daño es mayor contra el personaje cuando no hay herbívoros
        self.player_attack_power = 35
        self.player_attack_cooldown = 1.5  # Ataca más rápido al personaje
        self.objetivo = None
        self.tiempo_busqueda = 0

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Los carnívoros alternan entre buscar pareja y cazar."""
        ahora = time.time()
        
        # Cada 5 segundos cambia entre modo caza y reproducción
        if ahora - self.tiempo_busqueda > 5:
            self.tiempo_busqueda = ahora
            self.objetivo = None  # Reset objetivo
        
        # Si no tiene objetivo, buscar el más cercano
        if not self.objetivo:
            menor_distancia = float('inf')
            
            # Primero buscar pareja si no hay 3 carnívoros
            num_carnivoros = sum(1 for otra in posibles_presas.values() 
                               if isinstance(otra, Carnivoro))
            
            if num_carnivoros < 3:
                for otra in posibles_presas.values():
                    if isinstance(otra, Carnivoro) and otra is not self:
                        dist = math.hypot(self.posicion_x - otra.posicion_x,
                                        self.posicion_y - otra.posicion_y)
                        if dist < menor_distancia:
                            menor_distancia = dist
                            self.objetivo = ('pareja', otra)
            
            # Si no busca pareja o no encuentra, buscar presa
            if not self.objetivo:
                # Verificar si hay herbívoros vivos
                hay_herbivoros = False
                for otra in posibles_presas.values():
                    if isinstance(otra, Herbivoro):
                        hay_herbivoros = True
                        dist = math.hypot(self.posicion_x - otra.posicion_x,
                                        self.posicion_y - otra.posicion_y)
                        if dist < menor_distancia:
                            menor_distancia = dist
                            self.objetivo = ('presa', otra)
                
                # Si no hay herbívoros, perseguir al jugador
                if not hay_herbivoros:
                    for otra in posibles_presas.values():
                        if not isinstance(otra, (Carnivoro, Omnivoro, Herbivoro)):
                            dist = math.hypot(self.posicion_x - otra.posicion_x,
                                            self.posicion_y - otra.posicion_y)
                            if dist < menor_distancia:
                                menor_distancia = dist
                                self.objetivo = ('presa', otra)
        
        # Moverse hacia el objetivo
        if self.objetivo:
            tipo, objetivo = self.objetivo
            dist = math.hypot(self.posicion_x - objetivo.posicion_x,
                            self.posicion_y - objetivo.posicion_y)
            
            if tipo == 'presa':
                # Perseguir y atacar
                velocidad = self.salto * 1.2  # Más rápido al cazar
                if dist < 30:  # Distancia de ataque
                    # Atacar si el cooldown lo permite
                    cooldown_actual = (self.player_attack_cooldown 
                                     if not isinstance(objetivo, Herbivoro) 
                                     else self.attack_cooldown)
                    if ahora - self.last_attack >= cooldown_actual:
                        self.last_attack = ahora
                        if isinstance(objetivo, Herbivoro):
                            objetivo.vida -= self.attack_power
                            if self.vista:
                                # Mostrar el daño causado
                                self.vista.damage_popups.append({
                                    'text': f"-{int(self.attack_power)}",
                                    'x': objetivo.posicion_x,
                                    'y': objetivo.posicion_y - 20,
                                    'start': pygame.time.get_ticks()
                                })
                        else:  # Es el personaje
                            objetivo.vida -= self.player_attack_power
                            if self.vista:
                                # Mostrar el daño causado al personaje
                                self.vista.damage_popups.append({
                                    'text': f"-{int(self.player_attack_power)}",
                                    'x': objetivo.posicion_x,
                                    'y': objetivo.posicion_y - 20,
                                    'start': pygame.time.get_ticks()
                                })
                else:
                    self.mover_hacia(objetivo.posicion_x, objetivo.posicion_y, velocidad)
            
            else:  # tipo == 'pareja'
                # Moverse para reproducirse
                if dist > 10:
                    self.mover_hacia(objetivo.posicion_x, objetivo.posicion_y, self.salto)
        
        else:
            # Si no tiene objetivo, moverse aleatoriamente
            super().mover(screen_width, screen_height)
        self.attack_cooldown = 2.0  # segundos entre ataques
        self.last_attack = 0.0

class Herbivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=3):
        # Los herbívoros tienen tiempo de vida medio (180)
        # sync_vida_with_tiempo=True hace que el envejecimiento reduzca su HP
        super().__init__(x, y, vida, reproducirse, salto, False, True, True, tiempo_vida_max=180, sync_vida_with_tiempo=True)
        self.objetivo = None
        self.tiempo_busqueda = 0
        
    def mover(self, screen_width, screen_height, posibles_presas={}):
        """Los herbívoros buscan pareja y huyen de los carnívoros."""
        ahora = time.time()
        
        # Cada 3 segundos actualiza objetivo
        if ahora - self.tiempo_busqueda > 3:
            self.tiempo_busqueda = ahora
            self.objetivo = None
            
        # Primero revisar si hay carnívoros cerca para huir
        carnivoro_cercano = None
        dist_carnivoro = float('inf')
        
        for otra in posibles_presas.values():
            if isinstance(otra, Carnivoro):
                dist = math.hypot(self.posicion_x - otra.posicion_x,
                                self.posicion_y - otra.posicion_y)
                if dist < 100:  # Radio de detección de peligro
                    carnivoro_cercano = otra
                    dist_carnivoro = dist
                    break
        
        if carnivoro_cercano:
            # Huir en dirección opuesta al carnívoro
            dx = self.posicion_x - carnivoro_cercano.posicion_x
            dy = self.posicion_y - carnivoro_cercano.posicion_y
            # Normalizar y multiplicar por la velocidad
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 0:
                self.posicion_x = max(0, min(screen_width, 
                    self.posicion_x + (dx/dist) * self.salto * 2))
                self.posicion_y = max(0, min(screen_height, 
                    self.posicion_y + (dy/dist) * self.salto * 2))
            return
            
        # Si no hay peligro y no tiene objetivo, buscar pareja
        if not self.objetivo:
            menor_distancia = float('inf')
            num_herbivoros = sum(1 for otra in posibles_presas.values() 
                               if isinstance(otra, Herbivoro))
            
            if num_herbivoros < 3:
                for otra in posibles_presas.values():
                    if isinstance(otra, Herbivoro) and otra is not self:
                        dist = math.hypot(self.posicion_x - otra.posicion_x,
                                        self.posicion_y - otra.posicion_y)
                        if dist < menor_distancia:
                            menor_distancia = dist
                            self.objetivo = otra
        
        # Si tiene objetivo (pareja), moverse hacia ella
        if self.objetivo:
            dist = math.hypot(self.posicion_x - self.objetivo.posicion_x,
                            self.posicion_y - self.objetivo.posicion_y)
            if dist > 10:
                self.mover_hacia(self.objetivo.posicion_x, 
                               self.objetivo.posicion_y, self.salto)
        else:
            # Si no tiene objetivo, moverse aleatoriamente
            super().mover(screen_width, screen_height)

class Omnivoro(Especies):
    def __init__(self, x, y, vida, reproducirse=True, salto=4):
        # Los omnívoros tienen tiempo de vida equilibrado (200)
        super().__init__(x, y, vida, reproducirse, salto=3, atacar=True, correr=True, comer=True, tiempo_vida_max=200)
        self.presa = None
        self.modo_caza = False # Alterna entre cazar y deambular

    def mover(self, screen_width, screen_height, posibles_presas={}):
        """
        Comportamiento mixto: a veces caza, a veces deambula tranquilamente.
        """
        ahora = time.time()
        if ahora - self.last_random_move_time > self.random_move_delay:
            self.last_random_move_time = ahora
            # 50% de probabilidad de cambiar de modo (caza/deambular)
            if random.random() < 0.5:
                self.modo_caza = not self.modo_caza
                self.presa = None # Olvida la presa al cambiar de modo

        if self.modo_caza:
            # Comportamiento de caza (similar al carnívoro pero menos agresivo)
            if self.presa and (self.presa not in posibles_presas.values() or self.presa.get_porcentaje_vida() <= 0):
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
                super().mover(screen_width, screen_height)
        else:
            # Comportamiento de recolección (similar al herbívoro)
            super().mover(screen_width, screen_height)
class Planta(Especies):
    def __init__(self, x, y, vida, reproducirse=True):
        # Las plantas tienen tiempo de vida muy largo (150)
        super().__init__(x, y, vida, reproducirse, 0, False, False, False, tiempo_vida_max=150)
        
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
        self.salto = 2
        self.velocidad_extra = 0
        self.ticks_velocidad = 0

        # Atributos de animación
        self.state = self.IDLE_DOWN
        self.direction = 'down' # 'down', 'up', 'left', 'right'
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100 # ms por cuadro

    def update_animation(self, animation_strip):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.frame_index = (self.frame_index + 1) % len(animation_strip)

    def mover_arriba(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y > 0:
            self.posicion_y -= salto
        else:
            self.posicion_y = 360 # Aparece en el borde opuesto

    def mover_abajo(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_y < 360:
            self.posicion_y += salto
        else:
            self.posicion_y = 0 # Aparece en el borde opuesto

    def mover_derecha(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x < 490:
            self.posicion_x += salto
        else:
            self.posicion_x = 0 # Aparece en el borde opuesto

    def mover_izquierda(self):
        salto = self.salto + self.velocidad_extra
        if self.posicion_x > 0:
            self.posicion_x -= salto
        else:
            self.posicion_x = 490 # Aparece en el borde opuesto

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
    def __init__(self, ancho=500, alto=400, fps=30):
        pygame.init()
        self.ancho = ancho
        self.alto = alto
        self.screen = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Juego - Proyecto Especies")
        self.clock = pygame.time.Clock()
        self.fps = fps

        # Lista de especies vivas - Comenzar con dos de cada tipo
        self.especies_vivas = {}
        
        # Crear carnívoros
        c1 = Carnivoro(100, 100, 200)
        c2 = Carnivoro(400, 100, 200)
        c1.vista = self
        c2.vista = self
        self.especies_vivas['carnivoro_1'] = c1
        self.especies_vivas['carnivoro_2'] = c2

        # Crear herbívoros
        h1 = Herbivoro(100, 200, 200)
        h2 = Herbivoro(400, 200, 200)
        h1.vista = self
        h2.vista = self
        self.especies_vivas['herbivoro_1'] = h1
        self.especies_vivas['herbivoro_2'] = h2

        # Crear omnívoros
        o1 = Omnivoro(100, 300, 200)
        o2 = Omnivoro(400, 300, 200)
        o1.vista = self
        o2.vista = self
        self.especies_vivas['omnivoro_1'] = o1
        self.especies_vivas['omnivoro_2'] = o2
        
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

    def check_reproduction(self):
        """Verifica y maneja la reproducción de las especies."""
        # Contar cuántas hay de cada tipo
        num_carnivoros = sum(1 for nombre in self.especies_vivas if 'carnivoro' in nombre)
        num_herbivoros = sum(1 for nombre in self.especies_vivas if 'herbivoro' in nombre)
        num_omnivoros = sum(1 for nombre in self.especies_vivas if 'omnivoro' in nombre)

        nuevas_especies = {}
        # Obtener el tiempo actual para el cooldown
        tiempo_actual = time.time()
        
        for nombre, especie in self.especies_vivas.items():
            # Verificar cooldown de reproducción
            if hasattr(especie, 'ultimo_intento_reproduccion'):
                if tiempo_actual - especie.ultimo_intento_reproduccion < 5:  # 5 segundos de cooldown
                    continue
            
            # Comprobar si hay otras especies del mismo tipo cerca
            for otro_nombre, otra_especie in self.especies_vivas.items():
                if (otro_nombre != nombre and 
                    type(especie) == type(otra_especie) and
                    especie.puede_reproducirse() and 
                    otra_especie.puede_reproducirse()):
                    
                    # Calcular distancia entre especies
                    dist = math.hypot(especie.posicion_x - otra_especie.posicion_x,
                                    especie.posicion_y - otra_especie.posicion_y)
                    
                    # Si están lo suficientemente cerca, intentar reproducirse
                    # Verificar límites por tipo de especie
                    tipo_actual = especie.__class__.__name__.lower()
                    num_actual = sum(1 for nombre in self.especies_vivas if tipo_actual in nombre)
                    
                    if ((tipo_actual == 'carnivoro' and num_actual >= 3) or
                        (tipo_actual == 'herbivoro' and num_actual >= 3) or
                        (tipo_actual == 'omnivoro' and num_actual >= 3)):
                        continue
                        
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
                            
                            # Generar un nuevo nombre único para la especie
                            base_name = especie.__class__.__name__.lower()
                            new_name = f"{base_name}_{len(self.especies_vivas) + len(nuevas_especies)}"
                            nuevas_especies[new_name] = nueva_especie
                            
                            # Crear un popup visual para la reproducción
                            self.damage_popups.append({
                                'text': "¡Nueva especie!",
                                'x': new_x,
                                'y': new_y - 20,
                                'start': pygame.time.get_ticks()
                            })
                            
                            # Mostrar un mensaje de reproducción exitosa
                            print(f"¡{base_name} se ha reproducido! Nueva especie: {new_name}")
                            
                            # Separar a las especies después de reproducirse
                            direccion_x = random.choice([-1, 1])
                            direccion_y = random.choice([-1, 1])
                            
                            # Mover la primera especie
                            especie.posicion_x = max(0, min(self.ancho, 
                                especie.posicion_x + direccion_x * 50))
                            especie.posicion_y = max(0, min(self.alto, 
                                especie.posicion_y + direccion_y * 50))
                            
                            # Mover la segunda especie en dirección opuesta
                            otra_especie.posicion_x = max(0, min(self.ancho, 
                                otra_especie.posicion_x - direccion_x * 50))
                            otra_especie.posicion_y = max(0, min(self.alto, 
                                otra_especie.posicion_y - direccion_y * 50))
                            
                            break  # Solo una reproducción por ciclo        # Agregar las nuevas especies al diccionario
        self.especies_vivas.update(nuevas_especies)

    def _update_ai(self):
        """Lógica simple de IA para carnívoro: perseguir y atacar al herbívoro si existe,
        si no, perseguir y atacar al personaje.
        """
        ahora = time.time()
        if 'carnivoro' not in self.especies_vivas:
            return
        carn = self.especies_vivas['carnivoro']

        # Elegir objetivo: preferir herbívoro si existe
        if 'herbivoro' in self.especies_vivas:
            objetivo = self.especies_vivas['herbivoro']
            objetivo_especie = 'herbivoro'
        else:
            objetivo = self.personaje
            objetivo_especie = 'personaje'

        # Mover hacia objetivo
        carn.mover_hacia(objetivo.posicion_x, objetivo.posicion_y)

        # Atacar si está lo suficientemente cerca
        distancia = math.hypot(carn.posicion_x - objetivo.posicion_x, carn.posicion_y - objetivo.posicion_y)
        if distancia < 25:
            last = getattr(carn, 'last_attack', 0)
            if ahora - last >= carn.attack_cooldown:
                carn.last_attack = ahora
                if objetivo_especie == 'herbivoro':
                    # Atacar al herbívoro reduciendo su vida; eliminar si llega a 0
                    if 'herbivoro' in self.especies_vivas:
                        objetivo.vida -= carn.attack_power
                        # Crear popup de daño
                        self.damage_popups.append({
                            'text': f"-{int(carn.attack_power)}",
                            'x': objetivo.posicion_x,
                            'y': objetivo.posicion_y - 10,
                            'start': pygame.time.get_ticks()
                        })
                        # opcional: imprimir daño en consola para depuración
                        # print(f"Herbivoro atacado! vida={objetivo.vida}")
                        if objetivo.vida <= 0:
                            del self.especies_vivas['herbivoro']
                else:
                    # Atacar al jugador reduciendo vida
                    self.personaje.vida -= carn.attack_power
                    # Crear popup de daño para el jugador
                    self.damage_popups.append({
                        'text': f"-{int(carn.attack_power)}",
                        'x': self.personaje.posicion_x,
                        'y': self.personaje.posicion_y - 10,
                        'start': pygame.time.get_ticks()
                    })
                    # print(f"Player attacked! vida={self.personaje.vida}")
                    if self.personaje.vida <= 0:
                        # Fin del juego si el jugador muere
                        self.running = False

    def draw(self):
        # Fondo
        self.screen.fill((255, 255, 255))

        # Actualizar tiempo de vida de las especies
        especies_muertas = []
        
        for nombre, especie in self.especies_vivas.items():
            # Verificar vida y tiempo de vida
            if not especie.update_tiempo_vida() or especie.vida <= 0:
                especies_muertas.append(nombre)
                # Crear efecto visual de muerte
                self.damage_popups.append({
                    'text': "☠️",  # Emoji de calavera para indicar muerte
                    'x': especie.posicion_x,
                    'y': especie.posicion_y - 20,
                    'start': pygame.time.get_ticks()
                })

        # Eliminar especies muertas
        for nombre in especies_muertas:
            del self.especies_vivas[nombre]

        # Texto de posición del personaje
        texto = f"X: {self.personaje.posicion_x}, Y: {self.personaje.posicion_y}  HP: {int(self.personaje.vida)}"
        text_surf = self.font.render(texto, True, (0, 0, 0))
        self.screen.blit(text_surf, (10, 10))

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

        # Contar y mostrar número de cada especie
        num_carnivoros = sum(1 for nombre in self.especies_vivas if 'carnivoro' in nombre)
        num_herbivoros = sum(1 for nombre in self.especies_vivas if 'herbivoro' in nombre)
        num_omnivoros = sum(1 for nombre in self.especies_vivas if 'omnivoro' in nombre)
        
        # Mostrar contadores de especies
        y_offset = self.alto - 80
        count_carnivoros = self.font.render(f"Carnívoros: {num_carnivoros}/3", True, (255, 0, 0))
        count_herbivoros = self.font.render(f"Herbívoros: {num_herbivoros}/3", True, (0, 255, 0))
        count_omnivoros = self.font.render(f"Omnívoros: {num_omnivoros}/3", True, (160, 32, 240))
        
        self.screen.blit(count_carnivoros, (10, y_offset))
        self.screen.blit(count_herbivoros, (10, y_offset + 20))
        self.screen.blit(count_omnivoros, (10, y_offset + 40))

        for nombre, especie in self.especies_vivas.items():
            pos_x = int(especie.posicion_x)
            pos_y = int(especie.posicion_y)
            if 'carnivoro' in nombre:
                # Carnívoro: círculo rojo más grande con borde negro
                pygame.draw.circle(self.screen, (0, 0, 0), (pos_x, pos_y), 22)  # Borde negro
                pygame.draw.circle(self.screen, (255, 0, 0), (pos_x, pos_y), 20)  # Interior rojo
            elif 'herbivoro' in nombre:
                # Herbívoro: círculo verde más grande con borde negro
                pygame.draw.circle(self.screen, (0, 0, 0), (pos_x, pos_y), 22)  # Borde negro
                pygame.draw.circle(self.screen, (0, 255, 0), (pos_x, pos_y), 20)  # Interior verde brillante
                # Mostrar vida (HP) cerca del herbívoro
                hp_text = self.font.render(f"HP:{int(especie.vida)}", True, (0, 0, 0))
                self.screen.blit(hp_text, (pos_x - hp_text.get_width()//2, pos_y - 30))
            elif 'omnivoro' in nombre:
                # Omnívoro: cuadrado morado más grande con borde negro
                omni_size = 35
                pygame.draw.rect(self.screen, (0, 0, 0), 
                              (pos_x - omni_size//2 - 2, pos_y - omni_size//2 - 2, 
                               omni_size + 4, omni_size + 4))  # Borde negro
                pygame.draw.rect(self.screen, (160, 32, 240), 
                              (pos_x - omni_size//2, pos_y - omni_size//2, 
                               omni_size, omni_size))  # Interior morado más brillante

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
        instrucciones = self.font.render("Flechas/WASD = mover, ESC = salir", True, (0, 0, 150))
        self.screen.blit(instrucciones, (10, self.alto - 25))

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

            # Movimiento aleatorio de las especies
            for nombre, especie in self.especies_vivas.items():
                especie.mover(self.ancho, self.alto, self.especies_vivas)

            # Actualizaciones por tick
            self.personaje.tick_velocidad()

            # IA: actualizar comportamiento de las especies (carnívoro persigue/ataca)
            self._update_ai()
            
            # Verificar reproducción de especies
            self.check_reproduction()

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

    
        
