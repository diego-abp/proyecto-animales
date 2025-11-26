# -*- coding: utf-8 -*-
"""Vista usando pygame. Se integra con las clases de `logica` (Carnivoro, Herbivoro, Omnivoro, Planta)
La implementación sigue la lógica del main que proveíste, adaptada para usar las clases existentes en `logica`.
"""
import pygame
import math
import time
import random

from logica.carnivoro import Carnivoro
from logica.herbivoro import Herbivoro
from logica.omnivoro import Omnivoro
from logica.planta import Planta
from logica.ecosistema import Ecosistema
from persistencia.gestor_guardado import GestorGuardado

class VistaPygame:
    def __init__(self, ancho=960, alto=720, fps=30, ecosistema: Ecosistema = None):
        pygame.init()
        self.ancho = ancho
        self.alto = alto
        self.screen = pygame.display.set_mode((self.ancho, self.alto))
        pygame.display.set_caption("Juego - Proyecto Especies")
        # asegurar que la ventana capture teclas y repetir eventos para movimiento sostenido
        try:
            pygame.key.set_repeat(50, 50)
            pygame.event.pump()
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.fps = fps

        try:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            img_path = os.path.join(base_dir, '..', 'assets', 'fondos', 'fondos.png')
            img_path = os.path.normpath(img_path)
            if not os.path.exists(img_path):
                raise FileNotFoundError(img_path)
            background_image = pygame.image.load(img_path).convert()
            self.background_image = pygame.transform.scale(background_image, (self.ancho, self.alto))
            green_tint = pygame.Surface(self.background_image.get_size()).convert_alpha()
            green_tint.fill((20, 90, 40, 120))
            self.background_image.blit(green_tint, (0, 0))
        except Exception as e:
            # no se encontró asset o error al cargar -> usar fondo procedimental
            try:
                print(f"[VistaPygame] fondo no cargado: {e}")
            except Exception:
                pass
            self.background_image = None

        self.especies_vivas = {}
        # si se proporcionó un Ecosistema, usar su estado; si no, crear entidades nuevas
        self.ecosistema = ecosistema
        self.gestor = GestorGuardado()
        self.paused = False

        entidades_a_crear = [
            (Carnivoro, "carnivoro", 2),
            (Herbivoro, "herbivoro", 2),
            (Omnivoro, "omnivoro", 2),
            (Planta, "planta", 10)
        ]
        min_dist_entidades = 100

        if self.ecosistema is not None:
            # referenciar directamente los diccionarios del ecosistema para render
            try:
                self.especies_vivas = {**getattr(self.ecosistema, 'animales', {}), **getattr(self.ecosistema, 'plantas', {})}
            except Exception:
                self.especies_vivas = {}
        else:
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
                                # many constructors accept (x,y,vida, is_baby)
                                try:
                                    self.especies_vivas[nombre_unico] = clase_entidad(x, y, 100, is_baby=False)
                                except TypeError:
                                    # fallback for constructors with different signature
                                    self.especies_vivas[nombre_unico] = clase_entidad(x, y, 100)
                            break
                        intentos += 1

        # Player personaje (optional) — implementación segura con métodos de movimiento
        class Personaje:
            def __init__(self, x=200, y=200, screen_limits=(960,720)):
                self.posicion_x = x
                self.posicion_y = y
                self.vida = 1000
                self.vida_max = 1000
                self.salto = 2
                self.velocidad_extra = 0
                self.ticks_velocidad = 0
                self.attack_power = 30
                self.attack_range = 40
                self.attack_cooldown = 1.0
                self.last_attack_time = 0
                self.screen_limits = screen_limits

            def mover_arriba(self, amount=4):
                self.posicion_y = max(0, self.posicion_y - amount)

            def mover_abajo(self, amount=4):
                self.posicion_y = min(self.screen_limits[1]-1, self.posicion_y + amount)

            def mover_izquierda(self, amount=4):
                self.posicion_x = max(0, self.posicion_x - amount)

            def mover_derecha(self, amount=4):
                self.posicion_x = min(self.screen_limits[0]-1, self.posicion_x + amount)

            def take_damage(self, attacker, amount):
                try:
                    self.vida -= amount
                except Exception:
                    pass

        self.personaje = Personaje(200, 200, screen_limits=(self.ancho, self.alto))

        self.damage_popups = []
        self.animations = None

        try:
            self.font = pygame.font.SysFont(None, 20)
        except Exception:
            pygame.font.init()
            self.font = pygame.font.SysFont(None, 20)

        self.running = False
        # UI buttons (x,y,w,h,label)
        self.buttons = []
        btn_w, btn_h = 120, 28
        margin = 10
        x0 = self.ancho - btn_w - margin
        y0 = margin
        labels = ['Pause', 'Guardar', 'Cargar', 'Salir']
        for i, lab in enumerate(labels):
            self.buttons.append((x0, y0 + i*(btn_h+6), btn_w, btn_h, lab))
        self._last_save_msg = None
        
        # Modal de carga
        self.show_load_menu = False
        self.load_menu_items = []  # list of (slot_name, meta_dict)
        self.selected_load_index = 0

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

    def _draw_load_menu(self):
        """Dibuja un menú modal para seleccionar qué guardado cargar."""
        # Dimensiones del menú
        menu_width, menu_height = 400, 300
        menu_x = (self.ancho - menu_width) // 2
        menu_y = (self.alto - menu_height) // 2
        
        # Fondo semi-transparente para oscurecer el fondo
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Caja del menú
        pygame.draw.rect(self.screen, (40, 40, 40), (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, (200, 200, 200), (menu_x, menu_y, menu_width, menu_height), 2)
        
        # Título
        title_surf = self.font.render("Selecciona un guardado para cargar:", True, (255, 255, 255))
        self.screen.blit(title_surf, (menu_x + 10, menu_y + 10))
        
        # Listar guardados con fondo seleccionado
        item_height = 30
        start_y = menu_y + 40
        for i, (slot_name, meta) in enumerate(self.load_menu_items):
            item_y = start_y + i * item_height
            if item_y > menu_y + menu_height - 40:
                break
            # Fondo del ítem (resaltado si está seleccionado)
            if i == self.selected_load_index:
                pygame.draw.rect(self.screen, (100, 100, 150), (menu_x + 5, item_y, menu_width - 10, item_height - 5))
            # Texto: "Ciclo X - Fecha"
            try:
                ciclo = meta.get('ciclo', '?')
                fecha = meta.get('fecha', 'N/A')
                item_text = f"{slot_name} [Ciclo {ciclo} - {fecha}]"
            except Exception:
                item_text = slot_name
            item_surf = self.font.render(item_text[:50], True, (240, 240, 240))
            self.screen.blit(item_surf, (menu_x + 10, item_y + 5))
        
        # Botones de acción
        btn_y = menu_y + menu_height - 30
        btn_w, btn_h = 80, 25
        
        # Botón "Cargar"
        load_rect = pygame.Rect(menu_x + 20, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (50, 100, 50), load_rect)
        pygame.draw.rect(self.screen, (150, 255, 150), load_rect, 1)
        load_surf = self.font.render("Cargar", True, (255, 255, 255))
        self.screen.blit(load_surf, (load_rect.x + 10, load_rect.y + 3))
        
        # Botón "Cancelar"
        cancel_rect = pygame.Rect(menu_x + menu_width - 100, btn_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (100, 50, 50), cancel_rect)
        pygame.draw.rect(self.screen, (255, 150, 150), cancel_rect, 1)
        cancel_surf = self.font.render("Cancelar", True, (255, 255, 255))
        self.screen.blit(cancel_surf, (cancel_rect.x + 5, cancel_rect.y + 3))
        
        # Guardar rects para detección de clicks
        self.load_menu_load_rect = load_rect
        self.load_menu_cancel_rect = cancel_rect

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
                    hay_cria_existente = any(isinstance(e, type(especie)) and getattr(e, 'is_baby', False) for e in self.especies_vivas.values())
                    if hay_cria_existente:
                        continue
                    dist = math.hypot(especie.posicion_x - otra_especie.posicion_x, especie.posicion_y - otra_especie.posicion_y)
                    if dist < 30:
                        new_x = especie.posicion_x + random.randint(-30, 30)
                        new_y = especie.posicion_y + random.randint(-30, 30)
                        new_x = max(0, min(new_x, self.ancho))
                        new_y = max(0, min(new_y, self.alto))
                        if especie.emergency_mating_mode or otra_especie.emergency_mating_mode:
                            if hay_campeon_existente: continue
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
                            dist = max(0.1, math.hypot(dx, dy))
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
                            self.damage_popups.append({'text': "<3", 'x': especie.posicion_x, 'y': especie.posicion_y - 10, 'start': pygame.time.get_ticks()})
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
                candidates = [p for p in omnivoros_vivos if p.puede_reproducirse()]
                if candidates:
                    best_partner = min(candidates, key=lambda p: math.hypot(survivor.posicion_x - p.posicion_x, survivor.posicion_y - p.posicion_y))
                    survivor.emergency_mating_mode = True
                    best_partner.emergency_mating_mode = True
                    survivor.emergency_partner = best_partner
                    best_partner.emergency_partner = survivor
        elif len(omnivoros_vivos) == 1 and len(herbivoros_vivos) > 0:
            survivor = omnivoros_vivos[0]
            if survivor.puede_reproducirse():
                candidates = [p for p in herbivoros_vivos if p.puede_reproducirse()]
                if candidates:
                    best_partner = min(candidates, key=lambda p: math.hypot(survivor.posicion_x - p.posicion_x, survivor.posicion_y - p.posicion_y))
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
                    combined_radius = getattr(entity1, 'size', 10) + getattr(entity2, 'size', 10)
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
                if dist < 15:
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
                tiempo_transcurrido = ahora - getattr(especie, 'birth_time', 0)
                if tiempo_transcurrido >= getattr(especie, 'growth_duration', 30):
                    especie.is_baby = False
                    especie.size = getattr(especie, 'max_size', especie.size)
                else:
                    progreso = tiempo_transcurrido / getattr(especie, 'growth_duration', 30)
                    tamaño_inicial = getattr(especie, 'max_size', 10) / 2
                    especie.size = tamaño_inicial + (getattr(especie, 'max_size', 10) - tamaño_inicial) * progreso

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
                self.damage_popups.append({'text': f"-{int(damage)}", 'x': target.posicion_x, 'y': target.posicion_y - 10, 'start': pygame.time.get_ticks()})
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
        nombres_muertos = []
        for nombre, especie in list(self.especies_vivas.items()):
            if hasattr(especie, 'vida') and especie.vida <= 0 and not isinstance(especie, Planta):
                nombres_muertos.append(nombre)
        for nombre in nombres_muertos:
            del self.especies_vivas[nombre]

        # draw player simple
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
            elif isinstance(especie, Planta):
                color_contorno = (50, 255, 50) if getattr(especie, 'is_healing', False) else (0, 0, 0)
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

        # dibujar botones y HUD encima antes de volcar a pantalla
        for x,y,w,h,label in self.buttons:
            pygame.draw.rect(self.screen, (30,30,30), (x,y,w,h))
            pygame.draw.rect(self.screen, (200,200,200), (x,y,w,h), 1)
            # Cambiar color del botón Pause si está pausado
            if label == 'Pause' and self.paused:
                pygame.draw.rect(self.screen, (100,50,50), (x,y,w,h))
            txt = self.font.render(label, True, (240,240,240))
            self.screen.blit(txt, (x+8, y+6))
        # HUD: ciclo/estadísticas si ecosistema
        if self.ecosistema is not None and hasattr(self.ecosistema, 'resumen'):
            try:
                resumen = self.ecosistema.resumen()
                hud_text = f"Ciclo: {resumen.get('ciclo',0)}  Animales:{resumen.get('animales',0)}  Plantas:{resumen.get('plantas',0)}  Estado:{resumen.get('estado','N/A')}"
                surf = self.font.render(hud_text, True, (255,255,255))
                self.screen.blit(surf, (10,10))
            except Exception:
                pass
        if self._last_save_msg:
            surf = self.font.render(self._last_save_msg, True, (255,255,0))
            self.screen.blit(surf, (10,30))

        # Mostrar indicación si la ventana no tiene foco para que el usuario haga click y reciba teclas
        try:
            if not pygame.key.get_focused():
                hint = "Haga click en la ventana para controlar (teclado)"
                hint_surf = self.font.render(hint, True, (255, 180, 0))
                rect = hint_surf.get_rect()
                rect.topleft = (10, 50)
                # fondo semi-transparente
                bg = pygame.Surface((rect.width + 8, rect.height + 6), pygame.SRCALPHA)
                bg.fill((0,0,0,150))
                self.screen.blit(bg, (rect.x - 4, rect.y - 3))
                self.screen.blit(hint_surf, rect.topleft)
        except Exception:
            pass

        # Mostrar indicación de pausa si está pausado
        if self.paused:
            paused_text = "PAUSADO"
            paused_surf = self.font.render(paused_text, True, (255, 100, 100))
            paused_rect = paused_surf.get_rect(center=(self.ancho // 2, 60))
            self.screen.blit(paused_surf, paused_rect)

        # Dibujar menú de carga si está abierto
        if self.show_load_menu:
            self._draw_load_menu()

        pygame.display.flip()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            
            # Si el menú de carga está abierto, procesar clicks en el menú
            if self.show_load_menu:
                # Scroll: UP/DOWN entre items
                item_height = 30
                start_y = (self.alto - 300) // 2 + 40
                for i, (slot_name, meta) in enumerate(self.load_menu_items):
                    item_y = start_y + i * item_height
                    if (self.alto - 300) // 2 + 300 - 40 < item_y:
                        break
                    if item_y <= my <= item_y + item_height:
                        self.selected_load_index = i
                        break
                
                # Botón "Cargar"
                if hasattr(self, 'load_menu_load_rect') and self.load_menu_load_rect.collidepoint(mx, my):
                    if self.load_menu_items and 0 <= self.selected_load_index < len(self.load_menu_items):
                        slot_name, meta = self.load_menu_items[self.selected_load_index]
                        self._do_load_game(slot_name, meta)
                    self.show_load_menu = False
                
                # Botón "Cancelar"
                if hasattr(self, 'load_menu_cancel_rect') and self.load_menu_cancel_rect.collidepoint(mx, my):
                    self.show_load_menu = False
                return
            
            # Si no está el menú de carga, procesar clicks en los botones normales
            for x,y,w,h,label in self.buttons:
                if x <= mx <= x+w and y <= my <= y+h:
                    if label == 'Pause':
                        self.paused = not self.paused
                        self._last_save_msg = "PAUSADO" if self.paused else "Reanudado"
                    elif label == 'Guardar':
                        # guardar con nombre timestamp
                        if self.ecosistema is not None:
                            slot = f"GUI_{int(time.time())}"
                            meta = self.ecosistema.resumen() if hasattr(self.ecosistema, 'resumen') else {'ciclo':0}
                            exitoso, msg = self.gestor.guardar(slot, self.ecosistema, meta)
                            self._last_save_msg = msg if isinstance(msg, str) else str(msg)
                    elif label == 'Cargar':
                        # Mostrar el menú de selección de guardados
                        self._prepare_load_menu()
                    elif label == 'Salir':
                        self.running = False
                    break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.show_load_menu:
                    self.show_load_menu = False
                else:
                    self.running = False
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                # Navegación en el menú de carga si está abierto
                if self.show_load_menu:
                    self.selected_load_index = max(0, self.selected_load_index - 1)
                else:
                    # Ataque espacial no se debe hacer aquí
                    pass
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                # Navegación en el menú de carga si está abierto
                if self.show_load_menu:
                    self.selected_load_index = min(len(self.load_menu_items) - 1, self.selected_load_index + 1)
                else:
                    pass
            elif event.key == pygame.K_RETURN:
                # Confirmar selección en el menú de carga
                if self.show_load_menu and self.load_menu_items and 0 <= self.selected_load_index < len(self.load_menu_items):
                    slot_name, meta = self.load_menu_items[self.selected_load_index]
                    self._do_load_game(slot_name, meta)
                    self.show_load_menu = False
            elif event.key == pygame.K_SPACE:
                if not self.show_load_menu:
                    ahora = time.time()
                    if ahora - self.personaje.last_attack_time >= self.personaje.attack_cooldown:
                        self.personaje.last_attack_time = ahora
                        for nombre, especie in self.especies_vivas.items():
                            dist = math.hypot(self.personaje.posicion_x - especie.posicion_x, self.personaje.posicion_y - especie.posicion_y)
                            if dist < self.personaje.attack_range:
                                damage_dealt = self.personaje.attack_power
                                try:
                                    if hasattr(especie, 'take_damage'):
                                        especie.take_damage(self.personaje, damage_dealt)
                                    else:
                                        # si la entidad no implementa take_damage, restar vida directamente si es posible
                                        if hasattr(especie, 'vida'):
                                            especie.vida = max(0, especie.vida - damage_dealt)
                                except Exception:
                                    pass
                                self.damage_popups.append({'text': f"-{int(damage_dealt)}", 'x': getattr(especie, 'posicion_x', 0), 'y': getattr(especie, 'posicion_y', 0) - 10, 'start': pygame.time.get_ticks()})
                                break

    def _prepare_load_menu(self):
        """Prepara la lista de guardados y abre el menú de selección."""
        try:
            guardados = self.gestor.listar_guardados()
            self.load_menu_items = []
            if guardados:
                for slot_name, meta_info in guardados.items():
                    if isinstance(meta_info, dict):
                        self.load_menu_items.append((slot_name, meta_info))
                    else:
                        # fallback si el formato es diferente
                        self.load_menu_items.append((slot_name, {'ciclo': 0, 'fecha': 'N/A'}))
                self.selected_load_index = 0
                self.show_load_menu = True
                self._last_save_msg = "Selecciona un guardado"
            else:
                self._last_save_msg = "No hay guardados disponibles"
        except Exception as e:
            self._last_save_msg = f"Error al listar guardados: {e}"

    def _do_load_game(self, slot_name, meta):
        """Carga el juego desde un slot específico."""
        try:
            exitoso, meta_data, datos = self.gestor.cargar(slot_name)
            if exitoso:
                try:
                    new_ec = Ecosistema(meta.get('config', {}))
                    if hasattr(new_ec, 'deserializar'):
                        new_ec.deserializar(datos)
                        self.ecosistema = new_ec
                        self.especies_vivas = {**getattr(self.ecosistema, 'animales', {}), **getattr(self.ecosistema, 'plantas', {})}
                        self._last_save_msg = f'Guardado {slot_name} cargado'
                    else:
                        self._last_save_msg = 'Carga: deserializar no soportado'
                except Exception as e:
                    self._last_save_msg = f'Error al cargar: {e}'
            else:
                self._last_save_msg = f'Error: {meta_data}'
        except Exception as e:
            self._last_save_msg = f'Error: {e}'

    def iniciar(self):
        self.running = True
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            
            # Si está pausado, no hacer nada de la lógica del juego
            if not self.paused:
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
                if dx != 0 or dy != 0:
                    if dy < 0:
                        self.personaje.mover_arriba()
                    elif dy > 0:
                        self.personaje.mover_abajo()
                    if dx < 0 and dy == 0:
                        self.personaje.mover_izquierda()
                    elif dx > 0 and dy == 0:
                        self.personaje.mover_derecha()

                if getattr(self.personaje, 'ticks_velocidad', 0) > 0:
                    self.personaje.ticks_velocidad -= 1
                    if self.personaje.ticks_velocidad == 0:
                        self.personaje.velocidad_extra = 0

                self._update_ai()
                self.check_reproduction()
                self._check_emergency_reproduction()
                self._update_plant_healing()
                self._update_growth()
                self._resolve_collisions()
            
            self.draw()
            self.clock.tick(self.fps)
        pygame.quit()

if __name__ == "__main__":
    juego = VistaPygame()
    juego.iniciar()
