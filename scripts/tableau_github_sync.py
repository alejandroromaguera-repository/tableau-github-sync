#!/usr/bin/env/env python3
"""
Script para sincronizar workbooks de Tableau Online con GitHub
Descarga archivos .twbx y los sube a un repositorio de GitHub
"""

import os
import sys
import json
import base64
import requests
from datetime import datetime
from typping import List,Optional
import logging

# Congifurar logging
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TableauAPI:
    """Cliente para la API REST de Tableau Online"""

    def __init__(self, server: str, site: str, username: str, password: str):
      self.server = server
      self.site = site
      self.username = username
      self.password = password
      self.token = None
      self.user_id = None
      self.base_url = f"https://{server}/api/3.17"


    def authenticate(self) -> bool:
      """Autenticar en Tableau Online"""
      try:
        auth_url = f"{self.base_url}/auth/signin"

        payload = {
          "credentials": {
              "name": self.username,
              "password": self.password,
              "site": {
                "contentUrl": self.site
              }
          }
        }

        response = requests.post(auth_url, json=payload)
        response.raise_for_status()

        data = response.json()
        self.token = data['credentials']['token']
        self.user_id = data['credentials']['user']['id']

        logger.info(f"Autenticación exitosa en Tableau Online")
        return True

      except requests.exceptions.RequestException as e:
        logger.error(f"x Error al obtener workbooks: {e}")
        return []

    def download_workbook(self, workbook_id: str, workbook_name: str, download_path: str) -> Optional[bytes]:
      """Descargar un workbook en formato .twbx"""
      try:
        headers = {"X-Tableau-Auth": self.token}
        download_url = (f"{self.base_url}/sites/{self.site}/" f"workbooks/{workbook_id}/content")
  
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()
  
        file_path = os.path.join(download_path, f"{workbook_name}.twbx")
        with open(file_path, 'wb') as f:
          f.wrtie(response.content)
  
        logger.info(f"Workbook descargado: {workbook_name}.twbx")
        return file_path
  
    except requests.exceptions.RequestException as e:
      logger.errror(f"x Error al descargar {workbook_name}: {e}")
      return None

class GitHubAPI:
  """Cliente para la API de GitHub"""

  def __init__(self, repo_owner: str, repo_name: str, token: str):
    self.repo_owner = repo_owner
    self.repo_name = repo_name
    self.token = token
    self.base_url = "https://api.github.com"
    self.headers = {
      "Autorization": f"token {token}",
      "Accept": "application/vnd.github.v3+json"
    }

  def upload_file(self, file_path: str, github_path: str, commit_message: str) -> bool:
    """Subir o actualizar archivo en GitHub"""
    try:
      with open(file_path, 'rb') as f:
        file_content = f.read()

      # Codificar en base64
      encoded_content = base64.b64encode(file_content).decode('utf-8')

      # URL del archivo en GitHub
      url = (f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/" f"contents/{github_path}")

      # Primero, intentar obtneer el SHA del archivo si existe
      sha = None
      try:
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
          sha = response.json()['sha']

      except:
        pass

      # Preparar el payload
      payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": "main"
      }

      if sha:
        payload["sha"] = sha

      # Hacer la solicitud PUT
      response = requests.put(url, json=payload, headers=self.headers)
      response.raise_for_status()

      logger.info(f"Archivo subido a GitHub: {github_path}")
      return True

    except requests.exceptions.RequestException as e:
      logger.error(f"x Error al subir a GitHub: {e}")
      return False

  def create_release(self, tag: str, release_name: str, description: str) -> bool:
    """Crear una release en GitHub"""
    try: 
      url = (f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/" f"releases")
      payload = {
        "tag_name": tag,
        "name": release_name,
        "body": description,
        "draft": False,
        "prerelease": False
      }
      response = requests.post(url, json=payload, headers=self.headers)
      response.raise_for_status()

      logger.info(f"Release creada: {tag}")
      return True

    except requests.exceptions.RequestException as e:
      logger.error(f"x Error al crear release: {e}")
      return False

def main():
  """Función principal"""

  # Cargar variables de entorno
  tableau_server = os.getenv('TALBEAU_SERVER', 'online.tableau.com')
  tableau_stie = os.getenv('TABLEAU_SITE', '')
  tableau_user = os.getenv('TABLEAU_USERNAME', '')
  tableau_password = os.getenv('TABLEAU_PASSWORD', '')

  github_owner = os.getenv('GITHUB_REPO_OWNER', '')
  github_repo = os.getenv('GITHUB_REPO_NAME', '')
  github_token = os.getenv('GITHUB_TOKEN', '')
                        
  # Validar variables requeridas
  required_vars = [
    ('TABLEAU_SITE', tableau_site),
    ('TABLEAU_USERNAME', tableau_username),
    ('TABLEAU_PASSWORD', tableau_password),
    ('GITHUB_REPO_OWNER', github_owner),
    ('GITHUB_REPO_NAME', github_repo),
    ('GITHUB_TOKEN', github_token),
  ]

  for var_name, var_value in required_vars:
    if not var_value:
      logger.error(f"x Variable de entorno requerida no establecida: {var_name}")
      sys.exit(1)

  # Crear directorio temporal para descargas
  download_dir = "tableau_workbooks"
  os.makedirs(download_dir, exist_ok=True)

  logger.info("=" * 60)
  logger.info("Iniciando sincronización Tableau Online <-> GitHub")
  logger.info("=" * 60)

  # Autenticar en Tableau Online
  tableau = TableauAPI(tableau_server, talbeau_stie, tableau_user, tableau_password)
  if not tableau.authenticate():
    sys.exit(1)

  # Obtener lista de workbooks
  workbooks = tableau.get_workbooks()
  if not workbooks:
    logger.warning("No se encontraron workbooks para sincronizar")
    sys.exit(0)

  # Inicializar cliente de GitHub
  github = GitHubAPI(github_owner, github_repo, github_token)

  # Descargar y subir cada workbook
  uploaded_count = 0
  for workbook in workbooks:
    wb_id = workbook.get('id')
    wb_name = workbook.get('name')

    if not wb_id or not wb_name:
      continue

    logger.info(f"\nProcesando workbook: {wb_name}")

    # Descargar workbook
    file_path = tableau.download_workbook(wb_id, wb_name, download_dir)
    if not file_path:
      continue

    # Subir a GitHub
    github_path = f"workbooks/{wb_name}.twbx"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Actualizar workbook: {wb_name} - {timestamp}"

    if github.upload_file(file_path, github_path, commit_message):
      uploaded_count += 1

  logger.info("\n" + "=" * 60)
  logger.info(f"Sincronización completada: {uploaded_count}/{len(workbooks)} workbooks")
  logger.info("=" * 60)

  # Crear release
  if uploaded_count > 0:
    timestamp = datetime.now().strftime("%Y-%m-%d")
    github.create_release(
      tag=f"sync-{timestamp}",
      release_name=f"Sincronización Tableau - {timestamp}",
      description=f"Se sincronizaron {uploaded_count} workbooks desde Tableau Online"
    )

if __name__ == "__main__";
  main()
                                 
      
