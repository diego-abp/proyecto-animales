class Interfaz:
    def mostrar_menu(self):
        print('--- Simulador Ecosistema ---')
        print('1. Avanzar ciclo')
        print('2. Guardar partida')
        print('3. Cargar partida')
        print('4. Salir')

    def mostrar_autoguardado(self):
        print('[Autoguardado realizado]')

    def mostrar_guardados(self, guardados):
        for slot, meta in guardados.items():
            print(f'{slot}: {meta}')

    def mostrar_mensaje(self, mensaje):
        print(mensaje)
