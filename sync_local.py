#!/usr/bin/env python3
"""
Script para sincronizar la carpeta workbooks/ con GitHub automáticamente
Monitorea cambios locales y hace push a GitHub
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fit

# Configurar logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TableauWorkbookHandler(FileSystemEventHandler):
  """Manejador de eventos para cambios en workbooks"""
  def __init__(self, repo_path):
    self.repo_path = repo_path
    self.repo = git.Repo(repo_path)
    self.debounce_time = 2 #segundos
    self.last_action_time = {}

  def on_modified(self, event):
    if event.is_directory:
      return
    if not event.src_path.endswith('.twbx'):
      return

    self._handle_change(event.src_path, "modificado")

  def on_created(self, event):
    if event.is_directory:
      return
    if not event.src_path.endswith('.twbx')
      return

    self._handle_change(event.src_path, "creado")

  def on_deleted(self, event):
    if event.is_directory:
      return
    if not event.src_path.endswith('.twbx')
      return

    self._handle_change(event.src_path, "eliminado")

  def _handle_change(self, file_path, action):
    """Maneja cambios en archivos"""

    # Anti-rebote: evita múltiples eventos del mismo archivo
    current-time = time.time()
    if file_path in self.last_action_time:
      if current_time - self.last_action_time[file_path] < self.debounce_time:
        return

    self.last_action_time[file_path] = current_time

    file_name = os.path.basename(file_path)

    # Obtener la ruta relativa (para saber en qué carpeta está)
    rel_path = os.path.relpath(file_path, self.source_path)
    subfolder = os.path.dirname(rel_path)
    
    logger.info(f"Archivo {action} : {file_name}")

    # Espera un poco a que el archivo se escriba completamente
    time.sleep(1)

    try:
      # Ruta de destino en GitHub
      if subfolder and subfolder != '.':
        github_path = os.path.join('workbooks', subfolder, file_name)
      else:
        github_path = os.path.join('workbooks', file_name)

      # Normalizar la ruta (Windows usa \, Git usa /)
      github_path = github_path.replace('\\','/')

      # Crear directorio en GitHub si no existe
      github_dir = os.path.dirname(os.path.join(self.repo_path, github_path))
      os.makedirs(github_dir, exist_ok = True)

      # Copiar archivo a la ubicación del repositorio
      dest_file = os.path.join(self.repo_path, github_path)

      if action == "eliminado":
        # Si el archivo fue eliminado localmente, también eliminarlo en GitHub 
        if os.path.exists(dest_file):
          os.remove(dest_file)
          self.repo.index.remove([github_path])
      else:
        #Copiar archivo
        import shutil
        shutil.copy2(file_path, dest_file)
        self.repo.index.add([github_path])

      # Crear comit
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      commit_message = f"[{action.upper()}] {file_name} - {timestamp}"

      self.repo.index.commit(commit_message)
      logger.info(f"Commit creado: {commit_message}")

      # Push a GitHub
      try:
        origin = self.repo.remote('origin')
        origin.push()
        logger.info(f"Push a GitHub exitoso")
      except Exception as e:
        logger.error(f"x Error al hacer push: {e}")
        logger.warning("Verifica a que tu token de GitHub sea válido")

    except Exception as e:
      logger.error(f"x Error al procesar cambio: {e}")

def get_documents_path():
  """Obtiene la ruta de la carpeta Documentos según el sistema operativo"""
  if sys.platform=='win32':
    return os.path.join(os.path.expanduser('-'), 'Documents', 'Tableau Workbooks')

def main():
  """Función principal"""

  # Obtener ruta del repositorio
  repo_path = os.getcwd()
  source_path = get_documents_path()

  logger.info("=" * 60)
  logger.info("Monitor de Workbooks - Tableau <-> GitHub (con subcarpetas)")
  logger.info("=" * 60)
  logger.info(f"Carpeta monitoreada: {source_path}")
  logger.info(f"Repositorio: {repo_path}")
  logger.info(f"Destino GitHub: workbooks/<subcarpeta>/")
  logger.info("")
  logger.info("Estructura soportada:")
  logger.info("Documentos/Tableau Workbooks/")
  logger.info(" |--- Stangest")
  logger.info("")
  logger.info("Esperando cambios...")
  logger.info("Presiona Ctrl+C para detener")
  logger.info("=" * 60)

  # Verificar que Git está configurado
  try:
    repo = git.Repo(repo_path)
    logger.info(f"Repositorio Git encontrado")
  except Exception as e:
    logger.error(f"x Error: No es un repositorio Git válido")
    logger.error(f" {e}")
    sys.exit(1)

  # Verificar que la carpeta workbooks existe
  if not os.path.exists(source_path):
    logger.warning(f"La carpeta {source_path} no existe")
    logger.info(f"Creando carpeta...")
    os.makedirs(source_path, exist_ok=True)

  # Crear observador
  event_handler = TableauWorkbookHandler(repo_path)
  observer = Observer()
  observer.schedule(event_handler, source_path, recursive=False)

  # Iniciar monitoreo
  observer.start()

  try:
    while True:
      time_sleep(1)
  except KeyboardInterrupt:
    logger.info("\n\n Deteniendo monitor...")
    observer.stop()

  observer.join()
  logger.info("Monitor detenido")


if __name__=="__main__":
  main()
