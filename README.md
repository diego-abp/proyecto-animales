# Simulador de Ecosistema Virtual - Desafío Final POO

## 📋 Descripción del Proyecto

Sistema completo de simulación de ecosistema con persistencia de datos, implementado en Python siguiendo principios SOLID y arquitectura de tres capas (MVC).

## 🏗️ Arquitectura de Tres Capas

### 1. **LÓGICA** (`logica/`)
Contiene toda la lógica de negocio del simulador:
- `especies.py`: Clase base para todas las especies
- `carnivoro.py`: Implementación de carnívoros (depredadores)
- `herbivoro.py`: Implementación de herbívoros (presas)
- `omnivoro.py`: Implementación de omnívoros (híbridos)
- `planta.py`: Recursos naturales del ecosistema
- `ecosistema.py`: Gestor central del estado de la simulación

### 2. **VISTA** (`vista/`)
Interfaz de usuario (CLI - Command Line Interface):
- `cli.py`: Menús, solicitudes de entrada y muestra de información
- Implementa comunicación única con el usuario sin lógica de negocio

### 3. **PERSISTENCIA** (`persistencia/`)
Sistema de guardado y carga de datos:
- `gestor_guardado.py`: Manejo completo de persistencia con:
  - Guardado manual en múltiples slots
  - Autoguardado configurable
  - Backups automáticos
  - Validación de versiones
  - Generación de metadatos completos
  - Limpieza de archivos temporales y antiguos

## 🔄 Flujo de Comunicación

```
VISTA ─→ LÓGICA ─→ PERSISTENCIA
  ↓
Usuario          Simulación        Almacenamiento
interactúa        del ecosistema    de datos
```

### Flujo Permitido
- Vista → Lógica → Persistencia
- Usuario interactúa con Vista
- Vista envía solicitudes a Lógica
- Lógica gestiona datos y solicita a Persistencia
- Solo Vista muestra información

### Flujo Prohibido ✗
- Persistencia → Vista (NUNCA)
- Vista → Persistencia (NUNCA)
- Dependencias circulares

## 📂 Estructura de Carpetas

```
proyecto-animales/
├── proyecto especies.py          ← ARCHIVO PRINCIPAL (Controlador)
├── logica/
│   ├── __init__.py
│   ├── especies.py               (Clase base)
│   ├── carnivoro.py              (Depredador)
│   ├── herbivoro.py              (Presa)
│   ├── omnivoro.py               (Híbrido)
│   ├── planta.py                 (Recurso)
│   ├── animal.py                 (Referencia)
│   └── ecosistema.py             (Gestor)
├── vista/
│   ├── __init__.py
│   ├── cli.py                    (CLI Principal)
│   └── interfaz.py               (Referencia)
├── persistencia/
│   ├── __init__.py
│   └── gestor_guardado.py        (Gestor de datos)
└── guardados/                     (Se crea automáticamente)
    ├── Partida_1.json
    ├── Mi_Ecosistema.json
    ├── Prueba_Final.json
    └── backups/                  (Copias de seguridad)
```

## ✨ Características Implementadas

### Sistema de Guardado Manual
- ✅ 3 slots predeterminados: `Partida_1`, `Mi_Ecosistema`, `Prueba_Final`
- ✅ Nombramiento personalizado por usuario
- ✅ Guardado de múltiples partidas simultáneamente

### Metadatos Completos
- ✅ Fecha y hora del guardado
- ✅ Número del ciclo de simulación
- ✅ Cantidad de animales y plantas
- ✅ Estado del ecosistema
- ✅ Configuraciones activas
- ✅ Tipos de animales (carnívoros, herbívoros, omnívoros)
- ✅ Versión del simulador

### Autoguardado Configurable
- ✅ Configurable cada N ciclos (por defecto: 10)
- ✅ No pausa la simulación
- ✅ No requiere confirmación
- ✅ Indicador visual en la interfaz

### Gestión Segura de Datos
- ✅ Backups automáticos antes de sobrescribir
- ✅ Limpieza de archivos temporales
- ✅ Validación de versiones
- ✅ Detección de archivos corruptos
- ✅ Opción de cargar desde backup en caso de error

### Listado de Guardados
- ✅ Visualización de todas las partidas disponibles
- ✅ Muestra de metadatos para cada partida
- ✅ Confirmación informada antes de cargar
- ✅ Advertencia sobre pérdida de progreso actual

## 🚀 Uso del Programa

### Ejecutar el Simulador
```bash
python "proyecto especies.py"
```

### Menú Principal
```
1. Iniciar Simulación
2. Guardar Partida
3. Cargar Partida
4. Configurar Autoguardado
5. Ver Partidas Guardadas
6. Salir
```

### Durante la Simulación
- **ESPACIO**: Avanzar un ciclo
- **G**: Guardar partida manual
- **C**: Ver estado actual del ecosistema
- **Q**: Salir de la simulación

## 🔐 Validaciones y Manejo de Errores

- ✅ Validación de versiones entre guardados
- ✅ Detección de archivos JSON corruptos
- ✅ Manejo de excepciones en operaciones de archivo
- ✅ Mensajes de error claros y útiles
- ✅ Oferecimiento de alternativas (cargar desde backup)

## 📊 Requerimientos Cumplidos del Desafío

### Requerimientos Funcionales

#### 1. Sistema de Guardado Manual ✅
- Múltiples slots independientes
- Nombres identificables personalizados
- Metadatos completos
- Información de ciclos, animales, plantas, estado

#### 2. Sistema de Autoguardado ✅
- Configurable cada N ciclos
- No intrusivo (no pausa)
- No solicita confirmación
- Indicador visual

#### 3. Sistema de Carga ✅
- Listado de guardados con metadatos
- Confirmación informada
- Manejo de archivos corruptos
- Opción de cargar desde backup

#### 4. Gestión Segura ✅
- Backups automáticos
- Limpieza de temporales
- Validación de versiones

### Arquitectura y Diseño ✅

- Separación estricta de capas
- Flujo: Vista → Lógica → Persistencia
- Prohibidas dependencias circulares
- Principios SOLID aplicados
- Documentación completa

## 🛠️ Configuración Técnica

- **Lenguaje**: Python 3.7+
- **Dependencias**: ninguna (solo librería estándar)
- **Formato de datos**: JSON
- **Codificación**: UTF-8

## 📝 Ejemplo de Metadatos Guardado

```json
{
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
}
```

## 🎓 Lecciones de POO Aplicadas

1. **Encapsulación**: Atributos privados y métodos públicos
2. **Herencia**: Clases base (Especies) y subclases (Carnívoro, etc.)
3. **Polimorfismo**: Métodos sobrescritos en cada especie
4. **Abstracción**: Interfaces limpias, detalles ocultos
5. **MVC**: Separación clara de responsabilidades
6. **SOLID**: Principios de diseño respetados

## 📞 Soporte

Para reportar problemas o sugerencias, contacte al desarrollador.

---

**Última actualización**: 26 de Noviembre de 2025
**Versión**: 1.0
**Estado**: ✅ Completado
