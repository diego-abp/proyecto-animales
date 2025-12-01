# -*- coding: utf-8 -*-
"""Simulador de Ecosistema Virtual - Desafio Final POO
Archivo Principal que integra Logica, Vista y Persistencia"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logica.ecosistema import Ecosistema
from logica.carnivoro import Carnivoro
from logica.herbivoro import Herbivoro
from logica.omnivoro import Omnivoro
from logica.planta import Planta
from vista.cli import InterfazCLI
try:
    from vista.gui import InterfazGrafica
except Exception:
    InterfazGrafica = None
try:
    from vista.pygame_view import VistaPygame
except Exception:
    VistaPygame = None
from persistencia.gestor_guardado import GestorGuardado

import time, random, math
from datetime import datetime

class ControladorSimulador:
    def __init__(self):
        self.interfaz = InterfazCLI()
        self.gestor_guardado = GestorGuardado()
        self.ecosistema = None
        self.en_simulacion = False
        self.autoguardado_cada_n_ciclos = 10

    def iniciar(self):
        while True:
            self.interfaz.limpiar_pantalla()
            self.interfaz.mostrar_menu_principal()
            # Nota: opción adicional para iniciar la vista Pygame (ventana)
            print("7. Iniciar Vista Pygame (ventana)")
            opcion = input("\nSeleccione opcion: ").strip()
            if opcion == '1':
                # Opción por defecto: iniciar la simulación con la vista Pygame (ventana)
                self._iniciar_simulacion_con_pygame()
            elif opcion == '2': self._guardar_partida_manual()
            elif opcion == '3': self._cargar_partida()
            elif opcion == '4': self._configurar_autoguardado()
            elif opcion == '5': self._ver_partidas_guardadas()
            elif opcion == '7':
                # Iniciar vista pygame independiente
                if VistaPygame is None:
                    self.interfaz.mostrar_error('Vista pygame no disponible')
                    input('Enter...')
                else:
                    vp = VistaPygame()
                    vp.iniciar()
            elif opcion == '6': self.interfaz.mostrar_mensaje("Hasta luego!"); break
            else: self.interfaz.mostrar_error("Opcion no valida"); input("Enter...")

    def _iniciar_simulacion_nueva(self, auto: bool = False):
        config = {'autoguardado_cada_n_ciclos': self.autoguardado_cada_n_ciclos, 'version': '1.0'}
        self.ecosistema = Ecosistema(config)
        self._inicializar_ecosistema()
        # Si auto=True se ejecuta en modo continuo con visualización ASCII
        self._ejecutar_simulacion(auto_mode=auto)

    def _inicializar_ecosistema(self):
        for clase_entidad, nombre_base, cantidad in [(Carnivoro, 'carnivoro', 2), (Herbivoro, 'herbivoro', 2), (Omnivoro, 'omnivoro', 2), (Planta, 'planta', 10)]:
            for i in range(cantidad):
                for intentos in range(100):
                    x, y = random.randint(20, 940), random.randint(20, 700)
                    if not any(math.hypot(x - e.posicion_x, y - e.posicion_y) < 100 for e in list(self.ecosistema.animales.values()) + list(self.ecosistema.plantas.values())):
                        nombre_unico = f"{nombre_base}_{i+1}_{int(time.time() * 1000) % 10000}"
                        if issubclass(clase_entidad, Planta): self.ecosistema.agregar_planta(nombre_unico, clase_entidad(x, y))
                        else: self.ecosistema.agregar_animal(nombre_unico, clase_entidad(x, y, 100, is_baby=False))
                        break

    def _ejecutar_simulacion(self, auto_mode: bool = False, delay: float = 0.6):
        """Ejecuta la simulación.
        Si auto_mode es True, avanza automáticamente cada `delay` segundos y muestra una visualización ASCII.
        Si es False, usa el modo interactivo por comandos (ESPACIO/G/C/Q).
        """
        self.en_simulacion = True
        self.interfaz.limpiar_pantalla()
        self.interfaz.mostrar_menu_durante_simulacion()
        if auto_mode:
            try:
                while self.en_simulacion:
                    self._avanzar_ciclo()
                    resumen = self.ecosistema.resumen()
                    # Mostrar estado y render ASCII
                    self.interfaz.limpiar_pantalla()
                    print(f"Ciclo: {resumen['ciclo']}  Animales: {resumen['animales']}  Plantas: {resumen['plantas']}  Estado: {resumen['estado']}")
                    self._render_ascii()
                    if self.ecosistema.necesita_autoguardado():
                        meta = self._generar_metadatos()
                        exitoso, msg = self.gestor_guardado.guardar('autoguardado', self.ecosistema, meta)
                        if exitoso: self.interfaz.mostrar_autoguardado('autoguardado')
                        self.ecosistema.reset_ciclos_autoguardado()
                    time.sleep(max(0.05, delay))
            except KeyboardInterrupt:
                self.en_simulacion = False
                self.interfaz.mostrar_mensaje("Simulación interrumpida por usuario.")
        else:
            while self.en_simulacion:
                try:
                    entrada = input("\nAccion (ESPACIO=avanzar, G=guardar, C=ver, Q=salir): ").strip().upper()
                    if entrada in ('', ' '):
                        self._avanzar_ciclo()
                        self.interfaz.mostrar_estado_simulacion(self.ecosistema.resumen())
                        if self.ecosistema.necesita_autoguardado():
                            meta = self._generar_metadatos()
                            exitoso, msg = self.gestor_guardado.guardar('autoguardado', self.ecosistema, meta)
                            if exitoso: self.interfaz.mostrar_autoguardado('autoguardado')
                            self.ecosistema.reset_ciclos_autoguardado()
                    elif entrada == 'G': self._guardar_partida_manual()
                    elif entrada == 'C': self.interfaz.mostrar_estado_simulacion(self.ecosistema.resumen())
                    elif entrada == 'Q': self.en_simulacion = False; self.interfaz.mostrar_mensaje("Saliendo...")
                    else: self.interfaz.mostrar_error("Comando no valido")
                except (KeyboardInterrupt, Exception) as e:
                    self.en_simulacion = False
                    self.interfaz.mostrar_error(f"Error: {e}")

    def _iniciar_gui_y_simulacion(self):
        """Inicia la GUI (tkinter) en el hilo principal y la simulación en segundo plano."""
        if not self.ecosistema:
            self.interfaz.mostrar_error("No hay simulacion iniciada")
            return
        gui = InterfazGrafica()
        # hilo que avanza la simulación continuamente
        def sim_loop():
            self.en_simulacion = True
            try:
                while self.en_simulacion:
                    self._avanzar_ciclo()
                    if self.ecosistema.necesita_autoguardado():
                        meta = self._generar_metadatos()
                        exitoso, msg = self.gestor_guardado.guardar('autoguardado', self.ecosistema, meta)
                        if exitoso: self.interfaz.mostrar_autoguardado('autoguardado')
                        self.ecosistema.reset_ciclos_autoguardado()
                    time.sleep(0.5)
            except Exception:
                pass
        t = __import__('threading').Thread(target=sim_loop, daemon=True)
        t.start()
        try:
            gui.start(self.ecosistema, update_interval=0.5)
        finally:
            # cuando la GUI se cierre, detener la simulación
            self.en_simulacion = False

    def _iniciar_simulacion_con_pygame(self):
        """Crea el ecosistema, lo inicializa y arranca la vista Pygame que lo renderiza.
        La vista controlará el avance de ciclos y proveerá botones para pausar/guardar.
        """
        config = {'autoguardado_cada_n_ciclos': self.autoguardado_cada_n_ciclos, 'version': '1.0'}
        self.ecosistema = Ecosistema(config)
        self._inicializar_ecosistema()
        if VistaPygame is None:
            # fallback a modo CLI/ASCII si pygame no está disponible
            self._ejecutar_simulacion(auto_mode=True)
            return

        # Instanciar vista pasando el ecosistema
        vp = VistaPygame(ecosistema=self.ecosistema)
        try:
            vp.iniciar()
        except Exception as e:
            self.interfaz.mostrar_error(f"Error en Vista Pygame: {e}")
            # fallback: ejecutar modo ASCII interactivo
            self._ejecutar_simulacion(auto_mode=True)

    def _render_ascii(self, width: int = 80, height: int = 20):
        """Render ASCII simple del ecosistema en la consola.
        Usa las posiciones x:[0..960], y:[0..720] y las escala al grid.
        """
        try:
            grid = [[' ' for _ in range(width)] for _ in range(height)]
            max_x, max_y = 960, 720
            for nombre, planta in self.ecosistema.plantas.items():
                gx = min(width - 1, int((planta.posicion_x / max_x) * width))
                gy = min(height - 1, int((planta.posicion_y / max_y) * height))
                grid[gy][gx] = 'P'
            for nombre, animal in self.ecosistema.animales.items():
                gx = min(width - 1, int((animal.posicion_x / max_x) * width))
                gy = min(height - 1, int((animal.posicion_y / max_y) * height))
                char = 'A'
                cls_name = animal.__class__.__name__.lower()
                if 'carn' in cls_name: char = 'C'
                elif 'herb' in cls_name: char = 'H'
                elif 'omn' in cls_name: char = 'O'
                # superpone animales sobre plantas
                grid[gy][gx] = char
            # Imprimir grid
            for row in grid:
                print(''.join(row))
        except Exception as e:
            # Si falla el render, no debe romper la simulación
            print(f"Render error: {e}")

    def _avanzar_ciclo(self):
        self.ecosistema.avanzar_ciclo()
        for nombre, animal in list(self.ecosistema.animales.items()):
            animal.update_vida_por_tiempo()
            if animal.vida <= 0: self.ecosistema.remover_animal(nombre)

    def _guardar_partida_manual(self):
        if not self.ecosistema: self.interfaz.mostrar_error("No hay simulacion"); return
        slot = self.interfaz.solicitar_nombre_slot()
        if slot:
            meta = self._generar_metadatos()
            exitoso, msg = self.gestor_guardado.guardar(slot, self.ecosistema, meta)
            self.interfaz.mostrar_mensaje(msg) if exitoso else self.interfaz.mostrar_error(msg)
        input("Enter...")

    def _cargar_partida(self):
        guardados = self.gestor_guardado.listar_guardados()
        if not guardados: self.interfaz.mostrar_error("Sin partidas"); input("Enter..."); return
        self.interfaz.mostrar_guardados(guardados)
        slot = self.interfaz.solicitar_seleccion_slot()
        exitoso, meta, datos = self.gestor_guardado.cargar(slot)
        if not exitoso:
            self.interfaz.mostrar_error(meta)
            if input("Backup? (s/n): ").lower() == 's': exitoso, meta, datos = self.gestor_guardado.cargar_desde_backup(slot)
            if not exitoso: input("Enter..."); return
        if self.interfaz.mostrar_confirmacion_carga(meta):
            self.ecosistema = Ecosistema(meta.get('config', {}))
            self._ejecutar_simulacion()
        input("Enter...")

    def _configurar_autoguardado(self):
        self.autoguardado_cada_n_ciclos = self.interfaz.solicitar_numero_ciclos_autoguardado()
        self.interfaz.mostrar_mensaje(f"Autoguardado cada {self.autoguardado_cada_n_ciclos} ciclos")
        input("Enter...")

    def _ver_partidas_guardadas(self):
        self.interfaz.mostrar_guardados(self.gestor_guardado.listar_guardados())
        self.gestor_guardado.limpiar_temporales()
        self.gestor_guardado.limpiar_backups_antiguos(dias=7)
        input("Enter...")

    def _generar_metadatos(self):
        resumen = self.ecosistema.resumen()
        return {'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ciclo': resumen['ciclo'], 'animales': resumen['animales'], 'plantas': resumen['plantas'], 'estado': resumen['estado'], 'tipos_animales': resumen['tipos_animales'], 'config': self.ecosistema.config, 'version': '1.0'}

def main():
    try: ControladorSimulador().iniciar()
    except Exception as e: print(f"Error critico: {e}"); import traceback; traceback.print_exc()

if __name__ == '__main__': main()
