# Cambios aplicados a la Vista Pygame

## Problemas corregidos

### 1. **Pausa que no funcionaba**
- **Antes**: El botón "Pause" no hacía nada visible. Los animales continuaban moviéndose.
- **Después**: 
  - Al hacer clic en "Pause", el juego se detiene completamente (sin actualizar IA, reproducción, etc.).
  - El botón "Pause" cambia de color (rojo oscuro) cuando está pausado.
  - Se muestra "PAUSADO" en el centro de la pantalla cuando está en pausa.
  - Haz clic nuevamente o presiona "Pause" de nuevo para reanudar.

### 2. **Cargar partidas no mostraba menú**
- **Antes**: Al hacer clic en "Cargar", intentaba cargar el último guardado automáticamente y podía causar un exit del pygame.
- **Después**:
  - Hace clic en "Cargar" → aparece un **menú modal** flotante.
  - El menú muestra una lista de todos los guardados con:
    - Nombre del guardado (slot)
    - Número de ciclo
    - Fecha de guardado
  - Puedes navegar con:
    - **Mouse**: haz clic en el guardado que quieres cargar.
    - **Teclado**: usa **UP/DOWN** (flechas) para seleccionar, **ENTER** para confirmar, **ESC** para cancelar.
  - El guardado seleccionado se resalta en azul.

### 3. **Guardar/Cargar no permanecía dentro del pygame**
- **Antes**: No había opción; se cargaba automáticamente el último guardado.
- **Después**: Ahora ambas operaciones ocurren **dentro de la ventana del pygame**:
  - **Guardar**: hace clic en "Guardar" → se guarda con un timestamp automático. Mensaje de confirmación aparece en pantalla.
  - **Cargar**: hace clic en "Cargar" → menú modal. Selecciona → se carga. Mensaje aparece en pantalla. El juego continúa.

## Características nuevas

### Menú de Carga Modal
- Semitransparente overlay (oscurece el fondo).
- Lista scrollable de guardados (si hay muchos, se cortan).
- Botones "Cargar" y "Cancelar" al pie.
- Compatibilidad con mouse y teclado.

### Indicador de Pausa
- Botón "Pause" en la UI se resalta cuando está activo.
- Texto "PAUSADO" en rojo en el centro de la pantalla.
- Mensaje en pantalla ("PAUSADO" / "Reanudado") en la esquina superior izquierda.

### Mensajes de Estado
- Todos los mensajes de guardado/carga aparecen en la esquina superior izquierda (color amarillo).
- Se actualizan en tiempo real.

## Cómo usar

### En el Pygame (durante el juego)

1. **Pausar**: Haz clic en el botón "Pause" (esquina superior derecha). Repite para reanudar.

2. **Guardar**: Haz clic en el botón "Guardar". Se guardará con un nombre automático (timestamp). Verás un mensaje de confirmación en la pantalla.

3. **Cargar**: Haz clic en el botón "Cargar". Aparecerá un menú:
   - Si usas **mouse**: haz clic en el guardado que quieres.
   - Si usas **teclado**:
     - ↑/↓ para navegar entre guardados.
     - ENTER para cargar el seleccionado.
     - ESC para cancelar.

4. **Salir**: Haz clic en el botón "Salir" para volver al menú principal.

### Desde el Menú Principal (proyecto especies.py)

```powershell
python3.13 "proyecto especies.py"
# Opción 1 → Inicia Vista Pygame
# Opción 2 → Guardar partida manualmente (menú de consola)
# Opción 3 → Cargar partida manualmente (menú de consola)
# ... etc
```

## Archivos modificados

- **`vista/pygame_view.py`**:
  - Clase `Personaje` con métodos de movimiento seguros.
  - Variables de estado: `show_load_menu`, `load_menu_items`, `selected_load_index`.
  - Método `_draw_load_menu()` para renderizar el menú modal.
  - Método `_prepare_load_menu()` para preparar la lista de guardados.
  - Método `_do_load_game()` para cargar un juego específico.
  - Mejorada lógica de `handle_event()` para procesar clics/teclas en el menú.
  - Mejorada lógica de `iniciar()` para respectar la pausa (skip de updates cuando `paused=True`).
  - Mejor carga de assets (fondo busca ruta relativa al módulo).

## Validaciones

- ✅ Import de `VistaPygame` funciona sin errores de sintaxis.
- ✅ `test_run_pygame.py` sigue pasando (sin crash en renders/updates).
- ✅ Lógica de pausa integrada: juego se detiene cuando `paused=True`.
- ✅ Menú modal dibuja sin problemas.

## Notas

- Si hace clic en "Cargar" y no hay guardados, mostrará "No hay guardados disponibles".
- Los mensajes de estado (guardado, cargado, error) aparecen en amarillo en la esquina superior izquierda.
- Si hay un error al cargar, mostrará el detalle del error en pantalla (no hace crash).
- La pausa respeta todos los botones (puedes guardar/cargar mientras está pausado).
