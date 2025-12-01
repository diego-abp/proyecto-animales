"""
Módulo de Interfaz de Línea de Comandos (CLI) para el Simulador
Maneja la interacción con el usuario a través de menús de texto
"""


class InterfazCLI:
    """Interfaz de usuario basada en línea de comandos."""
    
    def __init__(self):
        self.autoguardado_activo = False

    def mostrar_menu_principal(self):
        """Muestra el menú principal del simulador."""
        print("\n" + "="*60)
        print(" SIMULADOR DE ECOSISTEMA VIRTUAL - MENÚ PRINCIPAL")
        print("="*60)
        print("1. Iniciar Simulación")
        print("2. Guardar Partida")
        print("3. Cargar Partida")
        print("4. Configurar Autoguardado")
        print("5. Ver Partidas Guardadas")
        print("6. Salir")
        print("="*60)

    def mostrar_menu_durante_simulacion(self):
        """Muestra el menú disponible durante la simulación."""
        print("\n--- Durante la Simulación ---")
        print("ESPACIO: Avanzar ciclo")
        print("G: Guardar partida manual")
        print("C: Ver estado actual")
        print("Q: Salir de simulación")

    def mostrar_estado_simulacion(self, resumen):
        """Muestra el estado actual de la simulación."""
        print("\n--- ESTADO DEL ECOSISTEMA ---")
        print(f"Ciclo: {resumen['ciclo']}")
        print(f"Animales: {resumen['animales']}")
        print(f"Plantas: {resumen['plantas']}")
        print(f"Estado: {resumen['estado']}")
        if 'tipos_animales' in resumen:
            print(f"  Carnívoros: {resumen['tipos_animales']['carnivoros']}")
            print(f"  Herbívoros: {resumen['tipos_animales']['herbivoros']}")
            print(f"  Omnívoros: {resumen['tipos_animales']['omnivoros']}")

    def mostrar_autoguardado(self, slot):
        """Muestra un mensaje de autoguardado."""
        print(f"\n✓ [Autoguardado realizado en slot: {slot}]")

    def mostrar_guardados(self, guardados):
        """Muestra la lista de partidas guardadas."""
        if not guardados:
            print("\nNo hay partidas guardadas.")
            return
        
        print("\n" + "="*60)
        print(" PARTIDAS GUARDADAS")
        print("="*60)
        for i, (slot, meta) in enumerate(guardados.items(), 1):
            print(f"\n{i}. {slot}")
            print(f"   Fecha: {meta.get('fecha', 'N/A')}")
            print(f"   Ciclo: {meta.get('ciclo', 'N/A')}")
            print(f"   Animales: {meta.get('animales', 0)}")
            print(f"   Plantas: {meta.get('plantas', 0)}")
            print(f"   Estado: {meta.get('estado', 'N/A')}")

    def mostrar_mensaje(self, mensaje):
        """Muestra un mensaje general."""
        print(f"\n→ {mensaje}")

    def mostrar_error(self, error):
        """Muestra un mensaje de error."""
        print(f"\n✗ ERROR: {error}")

    def mostrar_confirmacion_carga(self, meta):
        """Muestra información de confirmación antes de cargar."""
        print("\n" + "="*60)
        print(" CONFIRMACIÓN DE CARGA")
        print("="*60)
        print(f"Fecha: {meta.get('fecha', 'N/A')}")
        print(f"Ciclo: {meta.get('ciclo', 'N/A')}")
        print(f"Animales: {meta.get('animales', 0)}")
        print(f"Plantas: {meta.get('plantas', 0)}")
        print(f"Estado: {meta.get('estado', 'N/A')}")
        print("\n⚠ ADVERTENCIA: Esto sobrescribirá el progreso actual.")
        respuesta = input("\n¿Desea cargar esta partida? (s/n): ").lower()
        return respuesta == 's'

    def solicitar_nombre_slot(self):
        """Solicita el nombre para un nuevo slot de guardado."""
        return input("\nIngrese un nombre para el slot de guardado: ").strip()

    def solicitar_numero_ciclos_autoguardado(self):
        """Solicita el número de ciclos para autoguardado."""
        while True:
            try:
                valor = int(input("\nIngrese el número de ciclos para autoguardado (10, 30, 50, etc.): "))
                if valor > 0:
                    return valor
                else:
                    print("El valor debe ser mayor a 0.")
            except ValueError:
                print("Ingrese un número válido.")

    def solicitar_seleccion_slot(self):
        """Solicita la selección de un slot."""
        return input("\nIngrese el nombre del slot a cargar: ").strip()

    def limpiar_pantalla(self):
        """Limpia la pantalla de la consola."""
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
