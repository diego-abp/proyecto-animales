#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba interactiva para demostrar:
1. Pausa funcional (IA detiene)
2. Menú de carga modal
3. Guardado/cargado sin salir del pygame
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vista.pygame_view import VistaPygame
from logica.ecosistema import Ecosistema
from logica.carnivoro import Carnivoro
from logica.herbivoro import Herbivoro
from logica.omnivoro import Omnivoro
from logica.planta import Planta
from persistencia.gestor_guardado import GestorGuardado
import random
import math
import time

def test_pause_and_load_menu():
    """Prueba que:
    1. Pausa detiene realmente los updates (IA no se mueve)
    2. Menú de carga se dibuja correctamente
    """
    print("[TEST] Creando ecosistema de prueba...")
    
    config = {'autoguardado_cada_n_ciclos': 10, 'version': '1.0'}
    ecosistema = Ecosistema(config)
    
    # Crear algunas entidades
    for clase_entidad, nombre_base, cantidad in [
        (Carnivoro, 'carnivoro', 1),
        (Herbivoro, 'herbivoro', 1),
        (Omnivoro, 'omnivoro', 1),
        (Planta, 'planta', 3)
    ]:
        for i in range(cantidad):
            x = random.randint(50, 900)
            y = random.randint(50, 650)
            nombre_unico = f"{nombre_base}_{i+1}"
            if issubclass(clase_entidad, Planta):
                ecosistema.agregar_planta(nombre_unico, clase_entidad(x, y))
            else:
                ecosistema.agregar_animal(nombre_unico, clase_entidad(x, y, 100, is_baby=False))
    
    print(f"[TEST] Ecosistema creado: {len(ecosistema.animales)} animales, {len(ecosistema.plantas)} plantas")
    
    # Guardar un par de veces para que haya guardados para cargar
    gestor = GestorGuardado()
    for i in range(2):
        meta = ecosistema.resumen()
        meta['fecha'] = f"2025-11-26 10:{15+i}:00"
        slot = f"test_save_{i+1}"
        exitoso, msg = gestor.guardar(slot, ecosistema, meta)
        print(f"[TEST] {msg}")
        ecosistema.avanzar_ciclo()
    
    print("[TEST] Guardados creados. Iniciando VistaPygame...")
    print("[INSTRUCCIONES]")
    print("  1. Haz clic en 'Pause' → verás que los animales se detienen")
    print("  2. Haz clic en 'Pause' de nuevo → verás que los animales se mueven")
    print("  3. Haz clic en 'Cargar' → aparecerá un menú modal con los guardados")
    print("     - Usa mouse o flechas (UP/DOWN) para seleccionar")
    print("     - ENTER para confirmar, ESC para cancelar")
    print("  4. Prueba 'Guardar' → guardar adentro del pygame")
    print("  5. ESC para salir del pygame\n")
    
    vp = VistaPygame(ecosistema=ecosistema)
    
    # Verificar que el estado inicial sea correcto
    assert vp.paused == False, "[ERROR] Debe empezar sin pausa"
    assert vp.show_load_menu == False, "[ERROR] Menú de carga no debe estar visible inicialmente"
    print("[PASS] Estado inicial correcto (sin pausa, sin menú)")
    
    # Iniciar el pygame (esto bloqueará hasta que el usuario cierre)
    try:
        vp.iniciar()
    except Exception as e:
        print(f"[ERROR] Al ejecutar pygame: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("[TEST] Pygame cerrado por el usuario")
    print("[PASS] Prueba completada exitosamente")
    return True

if __name__ == '__main__':
    success = test_pause_and_load_menu()
    sys.exit(0 if success else 1)
