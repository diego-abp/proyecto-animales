"""
Módulo de Persistencia - Gestión de guardados y carga de partidas
Implementa sistema seguro con backups automáticos, validación de versiones y metadatos
"""

import os
import json
import shutil
from datetime import datetime


class GestorGuardado:
    """Gestor de guardados y cargas de partidas del simulador."""
    
    # Slots predeterminados
    SLOTS_PREDETERMINADOS = ['Partida_1', 'Mi_Ecosistema', 'Prueba_Final']
    
    def __init__(self, carpeta_guardados='guardados', carpeta_backups='guardados/backups'):
        """Inicializa el gestor de guardados."""
        self.carpeta_guardados = carpeta_guardados
        self.carpeta_backups = carpeta_backups
        self.version_actual = '1.0'
        
        # Crear carpetas si no existen
        os.makedirs(self.carpeta_guardados, exist_ok=True)
        os.makedirs(self.carpeta_backups, exist_ok=True)

    def guardar(self, slot, ecosistema, meta=None):
        """
        Guarda una partida en un slot específico.
        Crea backup automático antes de sobrescribir.
        
        Args:
            slot: Nombre del slot de guardado
            ecosistema: Objeto del ecosistema a guardar
            meta: (Ignorado) Se mantiene por compatibilidad
        """
        slot_limpio = self._sanitizar_nombre_slot(slot)
        save_path = os.path.join(self.carpeta_guardados, f'{slot_limpio}.json')
        
        # Crear backup si el archivo ya existe
        if os.path.exists(save_path):
            self._crear_backup(slot_limpio, save_path)
        
        # Validación: crear archivo temporal primero
        temp_path = os.path.join(self.carpeta_guardados, f'{slot_limpio}_tmp.json')
        try:
            # Estructura simple: solo datos y timestamp
            datos_guardado = {
                'timestamp': datetime.now().isoformat(),
                'version': self.version_actual,
                'data': ecosistema.serializar() if hasattr(ecosistema, 'serializar') else ecosistema,
            }
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(datos_guardado, f, indent=2, default=str)
            
            # Si todo va bien, reemplazar archivo original
            os.replace(temp_path, save_path)
            return True, f"Partida guardada exitosamente en '{slot_limpio}'"
        
        except Exception as e:
            # Limpiar archivo temporal en caso de error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False, f"Error al guardar: {str(e)}"

    def cargar(self, slot):
        """
        Carga una partida desde un slot específico.
        Valida versión y detecta archivos corruptos.
        
        Args:
            slot: Nombre del slot a cargar
            
        Returns:
            Tupla (exitoso, datos_ecosistema, None) o (False, mensaje_error, None)
        """
        slot_limpio = self._sanitizar_nombre_slot(slot)
        save_path = os.path.join(self.carpeta_guardados, f'{slot_limpio}.json')
        
        try:
            if not os.path.exists(save_path):
                return False, f"El archivo '{slot_limpio}' no existe", None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                contenido = json.load(f)
            
            # Validar versión
            version_guardada = contenido.get('version', '0.0')
            if not self._validar_version(version_guardada):
                return False, f"Versión incompatible. Guardada: {version_guardada}, Actual: {self.version_actual}", None
            
            datos = contenido.get('data', {})
            
            return True, datos, None
            
        except json.JSONDecodeError:
            return False, f"Archivo corrupto: '{slot_limpio}'. Intente cargar desde backup.", None
        except Exception as e:
            return False, f"Error al cargar partida: {str(e)}", None

    def listar_guardados(self):
        """
        Lista todos los guardados disponibles.
        
        Returns:
            Diccionario {slot_name: {"timestamp": fecha}}
        """
        guardados = {}
        try:
            for archivo in os.listdir(self.carpeta_guardados):
                if archivo.endswith('.json') and not archivo.endswith('_backup.json') and not archivo.endswith('_tmp.json'):
                    slot_name = archivo.replace('.json', '')
                    archivo_path = os.path.join(self.carpeta_guardados, archivo)
                    
                    try:
                        with open(archivo_path, 'r', encoding='utf-8') as f:
                            contenido = json.load(f)
                        timestamp = contenido.get('timestamp', 'N/A')
                        guardados[slot_name] = {'timestamp': timestamp}
                    except:
                        guardados[slot_name] = {'timestamp': 'Corrupto'}
        except Exception as e:
            print(f"Error al listar guardados: {e}")
        
        return guardados

    def _crear_backup(self, slot, ruta_original):
        """Crea una copia de seguridad del archivo guardado."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.carpeta_backups, f'{slot}_backup_{timestamp}.json')
        
        try:
            shutil.copy2(ruta_original, backup_path)
            return True
        except Exception as e:
            print(f"Advertencia: No se pudo crear backup: {e}")
            return False

    def cargar_desde_backup(self, slot):
        """
        Carga una partida desde el backup más reciente.
        
        Args:
            slot: Nombre del slot
            
        Returns:
            Tupla (exitoso, datos_ecosistema, None)
        """
        try:
            # Buscar el backup más reciente
            archivos_backup = [
                f for f in os.listdir(self.carpeta_backups) 
                if f.startswith(f'{slot}_backup_') and f.endswith('.json')
            ]
            
            if not archivos_backup:
                return False, f"No hay backups disponibles para '{slot}'", None
            
            archivos_backup.sort(reverse=True)  # Más reciente primero
            backup_reciente = archivos_backup[0]
            backup_path = os.path.join(self.carpeta_backups, backup_reciente)
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                contenido = json.load(f)
            
            datos = contenido.get('data', {})
            
            return True, datos, None
        
        except Exception as e:
            return False, f"Error al cargar desde backup: {str(e)}", None

    def _sanitizar_nombre_slot(self, nombre):
        """Sanitiza el nombre del slot (remove caracteres peligrosos)."""
        caracteres_permitidos = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        return ''.join(c for c in nombre if c in caracteres_permitidos)

    def _validar_version(self, version_guardada):
        """Valida que la versión del guardado sea compatible."""
        try:
            # Comparación simple: versión debe ser exacta
            return version_guardada == self.version_actual
        except:
            return False

    def limpiar_temporales(self):
        """Elimina archivos temporales (_tmp.json)."""
        try:
            for archivo in os.listdir(self.carpeta_guardados):
                if archivo.endswith('_tmp.json'):
                    os.remove(os.path.join(self.carpeta_guardados, archivo))
        except Exception as e:
            print(f"Error al limpiar temporales: {e}")

    def limpiar_backups_antiguos(self, dias=7):
        """Limpia backups más antiguos que N días."""
        import time
        try:
            ahora = time.time()
            tiempo_limite = ahora - (dias * 24 * 60 * 60)
            
            for archivo in os.listdir(self.carpeta_backups):
                ruta_archivo = os.path.join(self.carpeta_backups, archivo)
                if os.path.isfile(ruta_archivo):
                    if os.path.getctime(ruta_archivo) < tiempo_limite:
                        os.remove(ruta_archivo)
        except Exception as e:
            print(f"Error al limpiar backups antiguos: {e}")

    def exportar_guardado(self, slot, ruta_exportacion):
        """Exporta un guardado a una ubicación externa para backup manual."""
        try:
            slot_limpio = self._sanitizar_nombre_slot(slot)
            save_path = os.path.join(self.carpeta_guardados, f'{slot_limpio}.json')
            
            if not os.path.exists(save_path):
                return False, f"El guardado '{slot}' no existe"
            
            shutil.copy2(save_path, ruta_exportacion)
            return True, f"Guardado exportado a: {ruta_exportacion}"
        except Exception as e:
            return False, f"Error al exportar: {str(e)}"

    def importar_guardado(self, ruta_importacion, nuevo_slot):
        """Importa un guardado desde una ubicación externa."""
        try:
            if not os.path.exists(ruta_importacion):
                return False, "El archivo no existe"
            
            slot_limpio = self._sanitizar_nombre_slot(nuevo_slot)
            save_path = os.path.join(self.carpeta_guardados, f'{slot_limpio}.json')
            
            # Validar que sea un JSON válido
            with open(ruta_importacion, 'r', encoding='utf-8') as f:
                json.load(f)
            
            shutil.copy2(ruta_importacion, save_path)
            return True, f"Guardado importado en slot: {slot_limpio}"
        except json.JSONDecodeError:
            return False, "Archivo no es un guardado válido"
        except Exception as e:
            return False, f"Error al importar: {str(e)}"
