#!/usr/bin/env python3
"""
Script para sincronizar la carpeta workbooks/ con GitHub automáticamente.
Monitorea cambios locales y hace push a GitHub.
"""

import os
import sys
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path
import git

# Configurar logging para visualización en terminal
logging.basicConfig(
    level=logging.INFO, # Mostrar todos los mensajes de INFO en adelante
    format="%(asctime)s - %(levelname)s - %(message)s" # Formato: [fecha-hora] - [tipo] - [mensaje]
)

logger = logging.getLogger(__name__) # Crear un "logger" para escribir mensajes

def main():
    """Función principal"""

    # Obtener y definir rutas del repositorio
    repo_path = os.getcwd() # Ruta actual del repositorio Git
    source_path = r"C:\Users\alejandro.romaguera\Documents\Tableau Workbooks" # Carpeta a monitorear
    github_workbooks = os.path.join(repo_path, "workbooks") # Carpeta destino en GitHub

    logger.info("=" * 60)
    logger.info("Monitor de Workbooks - Tableau <-> GitHub (con subcarpetas)")
    logger.info("=" * 60)
    logger.info(f"Carpeta monitoreada: {source_path}")
    logger.info(f"Repositorio: {repo_path}")
    logger.info("Destino GitHub: workbooks/<subcarpeta>/")
    logger.info("")
    logger.info("Estructura soportada:")
    logger.info("Documentos/Tableau Workbooks/")
    logger.info(" |--- Stangest")
    logger.info("")

    # Verificar que Git está configurado
    try:
	# Intentar abrir el repositorio Git
        repo = git.Repo(repo_path)
        logger.info("Repositorio Git encontrado")
    except Exception as e:
        logger.error("Error: No es un repositorio Git válido")
        logger.error(e)
        sys.exit(1)

    # Verificar que la carpeta origen existe
    if not Path(source_path).exists():
        logger.error(f"La carpeta NO EXISTE: {source_path}")
        sys.exit(1)

    logger.info(f"Carpeta encontrada: {source_path}\n")

    # Rastrear archivos procesados, evitando el mismo archivo varias veces
    processed_files = set()

    logger.info("Esperando cambios...")
    logger.info("Presiona Ctrl+C para detener")
    logger.info("=" * 60)

    # Monitorear Archivos
    try:
        while True: # Repetir hasta presionar (Ctrl+C)

            # Buscar todos los archivos .twbx
            for root, dirs, files in os.walk(source_path):

                for file in files:

                    if not file.endswith(".twbx"):
                        continue

		    # Crear ruta completa del archivo
                    file_path = os.path.join(root, file)

                    # Si ya lo procesamos, continuar
                    if file_path in processed_files:
                        continue

                    # Nuevo archivo encontrado
                    rel_path = os.path.relpath(file_path, source_path)
                    logger.info(f"Archivo encontrado: {rel_path}")

                    try:
                        # Esperar a que se descargue el archivo
                        time.sleep(2)

                        # Determinar ruta en GitHub
                        subfolder = os.path.dirname(rel_path)

                        if subfolder and subfolder != ".":
                            github_path = os.path.join(
                                "workbooks",
                                subfolder,
                                file
                            )
                        else:
                            github_path = os.path.join(
                                "workbooks",
                                file
                            )

			# Convertir barras de Windows a barras de Git
                        github_path = github_path.replace("\\", "/")

                        # Crear directorio destino
                        github_dir = os.path.dirname(
                            os.path.join(repo_path, github_path)
                        )
                        os.makedirs(github_dir, exist_ok=True)

                        # Copiar archivo al repositorio
                        dest_file = os.path.join(repo_path, github_path)
                        shutil.copy2(file_path, dest_file)

                        # Agregar y commitear a  Git
                        repo.index.add([github_path])

                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        commit_message = f"[NUEVO] {rel_path} - {timestamp}"

                        repo.index.commit(commit_message)
                        logger.info(f"Commit: {commit_message}")

                        # Subir a GitHub
                        try:
                            origin = repo.remote("origin") # Obtener la conexion a GitHub
                            origin.push() # Enviar cambios a GitHub
                            logger.info("Push a GitHub exitoso\n")

                        except Exception as e:
                            logger.error(f"Error en el push: {e}\n")

                        # Marcar como procesado
                        processed_files.add(file_path)

                    except Exception as e:
                        logger.error(
                            f"Error procesando {rel_path}: {e}\n"
                        )
                        processed_files.add(file_path)

            # Esperar 5 segundos antes de escanear la carpeta de nuevo
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("\n\nDeteniendo monitor...")

    logger.info("Monitor detenido")


if __name__ == "__main__":
    main()
