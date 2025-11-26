# 🎮 Guía Rápida: Pygame - Sistema de Pausa y Carga Modal

## Inicio Rápido

```powershell
cd 'C:\Users\nydeb\OneDrive\Escritorio\proyecto-animales'
python3.13 "proyecto especies.py"
# → Selecciona opción 1 (Pygame)
```

---

## 🕹️ Controles en el Juego

### Movimiento (Personaje - Círculo Azul)
- **Flechas** ↑↓←→ o **WASD**

### Ataque
- **Espacio** (Barra espaciadora)
- Atacará a la primera entidad dentro del rango (línea roja)

### Botones de Interfaz (Esquina Superior Derecha)

#### 1. **Pause** 
   - Click para pausar
   - El juego se congela completamente
   - Los animales no se mueven
   - La IA no actualiza
   - Click de nuevo para reanudar

#### 2. **Guardar**
   - Click para guardar el estado actual
   - Se guarda automáticamente con un timestamp
   - Verás un mensaje de confirmación en la esquina superior izquierda

#### 3. **Cargar**
   - Click para abrir un menú de selección
   - Elige qué guardado quieres cargar

#### 4. **Salir**
   - Click para volver al menú principal
   - O presiona **ESC** (sin menú abierto)

---

## 📋 Menú de Carga Modal

Cuando haces click en **Cargar**, aparecerá una ventana flotante:

```
┌──────────────────────────────────────┐
│  Selecciona un guardado para cargar:  │
│                                      │
│  ◉ test_save_1 [Ciclo 25 - ...]      │  ← Seleccionado (azul)
│  ○ test_save_2 [Ciclo 50 - ...]      │
│  ○ GUI_1732606400 [Ciclo 100 - ...]  │
│                                      │
│  [ Cargar ]     [ Cancelar ]         │
└──────────────────────────────────────┘
```

### Cómo seleccionar

**Con Mouse:**
- Click en el guardado que quieres
- El guardado seleccionado se resalta en azul
- Click en "Cargar" para confirmar

**Con Teclado:**
- ↑ / ↓ (Flechas arriba/abajo) para navegar
- ENTER para cargar el seleccionado
- ESC para cancelar sin cargar

---

## 📊 Información en Pantalla

### Esquina Superior Izquierda (HUD)
```
Ciclo: 123  Animales: 8  Plantas: 12  Estado: Estable
```
Muestra el estado actual del ecosistema.

### Esquina Superior Izquierda (Mensajes)
```
Guardado GUI_1732606400 guardado
```
Confirmación de guardado/carga o mensajes de error.

### Centro Pantalla (Indicador de Pausa)
```
PAUSADO
```
Solo aparece cuando está pausado.

### Esquina Superior Derecha (Botones)
Clickeables con el ratón.

### Pie de Pantalla
```
Flechas/WASD = mover, Espacio = atacar, ESC = salir
```
Referencia rápida de controles.

---

## 🐛 Solución de Problemas

### "El juego no responde a las teclas"
**Solución:** Haz click dentro de la ventana del juego para darle foco.
- Verás un mensaje en la pantalla si no está enfocada.

### "No aparece el menú de carga"
**Posible causa:** No hay guardados.
**Solución:** Guarda primero (botón "Guardar") antes de intentar cargar.

### "No aparece el fondo"
**Causa:** El archivo `assets/fondos/fondos.png` no existe.
**Solución:** Usa un fondo de color sólido (funciona igual, es normal).

### "El personaje no se mueve"
1. Verifica que el juego no está pausado (botón "Pause" debe estar en color normal).
2. Haz click en la ventana para darle foco.
3. Presiona las flechas o WASD.

### "No puedo pausar"
**Nota:** Cuando el menú de carga está abierto, los botones normal no funcionan. Cierra el menú primero (ESC o "Cancelar").

### "Error al cargar: ..."
El guardado podría estar corrupto.
**Soluciones:**
1. Intenta cargar otro guardado.
2. Prueba guardar de nuevo.
3. Si persiste, reinicia el juego.

---

## 📈 Ejemplo de Sesión

1. **Inicia el juego** → Opción 1 en el menú principal
2. **Juega un poco** → Muévete, ataca, observa los animales
3. **Pausa** → Click en "Pause". El juego se detiene.
4. **Resume** → Click en "Pause" de nuevo.
5. **Guarda** → Click en "Guardar". Verás confirmación.
6. **Carga** → Click en "Cargar" → Selecciona un guardado → Click "Cargar"
7. **Salir** → Click en "Salir" para volver al menú principal.

---

## 🎯 Acciones Disponibles

| Acción | Atajo | Efecto |
|--------|-------|--------|
| Mover Arriba | ↑ o W | Mueve el personaje hacia arriba |
| Mover Abajo | ↓ o S | Mueve el personaje hacia abajo |
| Mover Izquierda | ← o A | Mueve el personaje hacia izquierda |
| Mover Derecha | → o D | Mueve el personaje hacia derecha |
| Atacar | Espacio | Ataca a entidades cercanas |
| Pausar/Reanudar | Botón "Pause" | Pausa el juego |
| Guardar | Botón "Guardar" | Guarda el estado actual |
| Cargar | Botón "Cargar" | Abre menú de carga |
| Salir | Botón "Salir" o ESC | Vuelve al menú principal |
| Seleccionar en Menú | Mouse o ↑↓ | Navega opciones |
| Confirmar en Menú | Click / ENTER | Confirma selección |
| Cancelar Menú | ESC / Cancelar | Cierra menú sin cargar |

---

## 💡 Tips

- **Guarda frecuentemente** durante sesiones largas.
- **La pausa** es perfecta para observar la IA sin presión.
- **Carga desde el menú** para experimentar con diferentes estados del ecosistema.
- **Explora el mapa** moviendo el personaje por toda la pantalla.
- **Observa los colores**: 
  - 🔵 Azul = Tu personaje
  - ⚫ Negro = Carnívoro
  - 🟢 Verde = Herbívoro
  - 🟫 Marrón = Omnívoro
  - 🟩 Verde claro = Planta

---

## 📝 Notas

- Guardar y cargar **nunca sale del pygame**.
- La pausa funciona en **todos los modos** (incluso con menú abierto).
- Los mensajes de error aparecen **en pantalla**, no desaparecen.
- El ecosistema sigue existiendo entre pausas y reanudas.

¡Disfruta! 🎮
