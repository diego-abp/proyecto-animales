# Documentación Técnica - Desafío Final POO

## Requerimientos del Desafío Cumplidos

### 1. SISTEMA DE PERSISTENCIA ✅

#### a) Sistema de Guardado Manual
- **Slots**: Mínimo 3 espacios independientes (Partida_1, Mi_Ecosistema, Prueba_Final)
- **Personalizables**: Usuario puede crear nuevos slots con nombres propios
- **Almacenamiento**: JSON con metadatos completos

#### b) Metadatos de Guardado
Cada archivo incluye:
- Fecha y hora del guardado ✅
- Número del ciclo de simulación ✅
- Cantidad total de animales ✅
- Cantidad total de plantas ✅
- Estado general del ecosistema ✅
- Configuraciones activas ✅
- Versión del simulador ✅

#### c) Sistema de Autoguardado
- **Configurable**: Ajustable por usuario (ej: cada 10, 30, 50 ciclos) ✅
- **No intrusivo**: No pausa simulación ✅
- **Sin confirmación**: Automático y silencioso ✅
- **Indicador visual**: Mensaje "[Autoguardado realizado]" ✅

#### d) Sistema de Carga
- **Listado**: Usuario visualiza todas las partidas con metadatos ✅
- **Confirmación informada**: Muestra fecha, ciclo, contenido, advertencia ✅
- **Manejo de errores**: Detección de corrupción e incompatibilidad ✅
- **Backups**: Opción de cargar desde copia si hay error ✅

#### e) Gestión Segura de Datos
- **Backups automáticos**: Antes de cada sobrescritura ✅
- **Limpieza**: Archivos temporales eliminados automáticamente ✅
- **Validación**: Verificación de versión antes de cargar ✅

### 2. REGLAS DE COMUNICACIÓN ENTRE CAPAS ✅

#### Flujo Permitido:
```
Vista → Lógica → Persistencia
```
1. Usuario interactúa con Vista (CLI)
2. Vista envía solicitud a Lógica
3. Lógica recopila datos
4. Lógica envía datos a Persistencia
5. Persistencia guarda/carga
6. Respuesta regresa a Vista
7. Vista muestra resultado al usuario

#### Flujo Prohibido:
- ❌ Persistencia llama a Vista
- ❌ Vista accede directamente a Persistencia
- ❌ Dependencias circulares

## Archivo Controlador Principal

**Archivo**: `proyecto especies.py`

Implementa la clase `ControladorSimulador` que:
- Instancia la Vista (InterfazCLI)
- Instancia la Persistencia (GestorGuardado)
- Instancia la Lógica (Ecosistema)
- Orquesta la comunicación entre capas
- Implementa menú principal
- Gestiona bucle de eventos

## Estructura de Capas

### Capa LÓGICA (logica/)

**Clases principales**:
- `Especies`: Clase base abstracta
- `Carnivoro`: Depredadores
- `Herbivoro`: Presas herbívoras
- `Omnivoro`: Híbridos (carnívoro + herbívoro)
- `Planta`: Recursos del ecosistema
- `Ecosistema`: Gestor central de estado

**Métodos clave**:
- `Ecosistema.agregar_animal()`
- `Ecosistema.remover_animal()`
- `Ecosistema.avanzar_ciclo()`
- `Ecosistema.resumen()`
- `Ecosistema.necesita_autoguardado()`
- `Especies.update_vida_por_tiempo()`

### Capa VISTA (vista/)

**Clase**: `InterfazCLI`

**Responsabilidades**:
- Mostrar menús
- Solicitar entrada del usuario
- Mostrar estado del ecosistema
- Mostrar errores y mensajes
- Mostrar confirmaciones

**Métodos principales**:
- `mostrar_menu_principal()`
- `mostrar_estado_simulacion()`
- `mostrar_guardados()`
- `mostrar_confirmacion_carga()`
- `solicitar_nombre_slot()`
- `solicitar_numero_ciclos_autoguardado()`

### Capa PERSISTENCIA (persistencia/)

**Clase**: `GestorGuardado`

**Responsabilidades**:
- Guardar estado del ecosistema
- Cargar partidas
- Crear backups
- Validar versiones
- Limpiar archivos temporales

**Métodos principales**:
- `guardar()` - Guarda con backup automático
- `cargar()` - Carga y valida versión
- `listar_guardados()` - Listado con metadatos
- `cargar_desde_backup()` - Recuperación de emergencia
- `limpiar_temporales()` - Limpieza automática
- `limpiar_backups_antiguos()` - Gestión de espacio

## Rutas de Datos

### Guardado Manual
```
Usuario presiona "G"
↓
Vista.solicitar_nombre_slot()
↓
Controlador._guardar_partida_manual()
↓
Lógica.Ecosistema.resumen()
↓
Controlador._generar_metadatos()
↓
Persistencia.guardar(slot, ecosistema, meta)
   ├─ Crear backup si existe
   ├─ Escribir archivo temporal
   ├─ Validar JSON
   └─ Reemplazar si válido
↓
Vista.mostrar_mensaje("Guardado exitosamente")
```

### Autoguardado
```
Usuario avanza ciclo
↓
Lógica.avanzar_ciclo()
↓
Lógica.necesita_autoguardado() → True
↓
Controlador._generar_metadatos()
↓
Persistencia.guardar('autoguardado', ecosistema, meta)
↓
Vista.mostrar_autoguardado() - Mensaje temporal
```

### Carga de Partida
```
Usuario presiona "3"
↓
Persistencia.listar_guardados()
↓
Vista.mostrar_guardados()
↓
Usuario selecciona slot
↓
Persistencia.cargar(slot)
   ├─ Validar archivo existe
   ├─ Validar JSON válido
   ├─ Validar versión
   └─ Retornar (meta, datos)
↓
Vista.mostrar_confirmacion_carga(meta)
   ├─ Mostrar información
   └─ Advertencia sobre pérdida
↓
Si confirma:
   Lógica.crear_ecosistema_desde(datos)
   ↓
   Controlador._ejecutar_simulacion()
```

## Validaciones Implementadas

### Validación de Versiones
```python
versión_guardada = contenido.get('version', '0.0')
if versión_guardada != VERSION_ACTUAL:
    # Rechazar y ofrecer backup
```

### Validación de Archivos
```python
try:
    with open(archivo) as f:
        json.load(f)  # Detecta JSON inválido
except json.JSONDecodeError:
    # Archivo corrupto
```

### Sanitización de Nombres
```python
caracteres_permitidos = 'abc...0123456789_-'
nombre_limpio = ''.join(c for c in nombre if c in caracteres_permitidos)
```

## Manejo de Errores

### Archivo No Encontrado
- Mensaje: "El archivo 'xxx' no existe"
- Oferta: "¿Cargar desde backup?"

### Archivo Corrupto
- Mensaje: "Archivo corrupto: 'xxx'"
- Oferta: Cargar desde backup

### Versión Incompatible
- Mensaje: "Versión incompatible. Guardada: X, Actual: Y"
- Acción: Rechazar carga, ofrecer backup

### Error General
- Mensaje: "Error al operación: descripción"
- Acción: Volver al menú principal

## Archivos Generados

### Guardados
```
guardados/
├── Partida_1.json
├── Mi_Ecosistema.json
├── Prueba_Final.json
├── [nombre_usuario].json
└── autoguardado.json
```

### Backups
```
guardados/backups/
├── Partida_1_backup_20251126_090000.json
├── Partida_1_backup_20251126_091000.json
└── ...
```

## Configuración Predeterminada

```python
CONFIG = {
    'autoguardado_cada_n_ciclos': 10,
    'version': '1.0',
    'carpeta_guardados': 'guardados',
    'carpeta_backups': 'guardados/backups',
    'limpiar_backups_mas_antiguos_que_dias': 7
}
```

## Formato JSON de Guardado

```json
{
  "meta": {
    "fecha": "2025-11-26 09:30:15",
    "ciclo": 42,
    "animales": 5,
    "plantas": 10,
    "estado": "Normal",
    "tipos_animales": {
      "carnivoros": 2,
      "herbivoros": 2,
      "omnivoros": 1
    },
    "config": {
      "autoguardado_cada_n_ciclos": 10,
      "version": "1.0"
    },
    "version": "1.0"
  },
  "datos": {
    "ciclo": 42,
    "animales": {},
    "plantas": {},
    "estado": "Normal",
    "config": {},
    "version": "1.0"
  },
  "version": "1.0",
  "timestamp_guardado": "2025-11-26T09:30:15.123456"
}
```

---

**Última actualización**: 26-11-2025
**Versión**: 1.0
**Estado**: ✅ Completado y testeado
