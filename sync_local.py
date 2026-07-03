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
    logger.info(f"Archivo {action} : {file_name}")

    # Espera un poco a que el archivo se escriba completamente
    time.sleep(1)

    try:
      # Agregar cambios
      self.repo.index.add([file_path])

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

def main():
  """Función principal"""

  # Obtener ruta del repositorio
  repo_path = os.getcwd()
  workbooks_path = os.path.join(repo_path, 'workbooks')

  logger.info("=" * 60)
  logger.info("Monitor de Workbooks - Tableau <-> GitHub")
  logger.info("=" * 60)
  logger.info(f"Carpeta monitoreada: {workbooks_path}")
  logger.info(f"Repositorio: {repo_path}")
  logger.info("")
  logger.info("Esperando cambios en la carpeta workbooks/...")
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
  if not os.path.exists(workbooks_path):
    logger.warning(f"La carpeta {workbooks_path} no existe")
    logger.info(f"Creando carpeta...")
    os.makedirs(workbooks_path, exist_ok=True)

  # Crear observador
  event_handler = TableauWorkbookHandler(repo_path)
  observer = Observer()
  observer.schedule(event_handler, workbooks_path, recursive=False)

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
