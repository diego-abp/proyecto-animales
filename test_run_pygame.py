import sys, os, traceback
sys.path.insert(0, r'c:\Users\nydeb\OneDrive\Escritorio\proyecto-animales')

try:
    from vista.pygame_view import VistaPygame
    from logica.ecosistema import Ecosistema
    from logica.carnivoro import Carnivoro
    from logica.herbivoro import Herbivoro
    from logica.omnivoro import Omnivoro
    from logica.planta import Planta
    import time

    # Crear ecosistema mínimo
    e = Ecosistema({'autoguardado_cada_n_ciclos': 100, 'version': '1.0'})

    # Añadir unas entidades simples
    e.animales = {}
    e.plantas = {}
    e.animales['c1'] = Carnivoro(100, 100, 100)
    e.animales['h1'] = Herbivoro(300, 200, 100)
    e.plantas['p1'] = Planta(500, 400)

    # Instanciar vista
    vp = VistaPygame(ecosistema=e)

    # Avanzar unos ticks sin abrir bucle interactivo completo
    for i in range(5):
        vp._update_ai()
        vp.check_reproduction()
        vp._update_plant_healing()
        vp._update_growth()
        vp._resolve_collisions()
        vp.draw()
        time.sleep(0.1)

    print('TEST_RUN_OK')

except Exception as ex:
    traceback.print_exc()
    print('TEST_RUN_FAILED')
