class Animal:
    def __init__(self, nombre, especie, edad):
        self.nombre = nombre
        self.especie = especie
        self.edad = edad

    def comunicar(self):
        return f'{self.nombre} emite un sonido.'
