# tableau-github-sync
Sincronización automática de workbooks de Tableau Online con GitHub

# Tableau Workbooks Sync
Sincrnización automática de workbooks de Tableau con GitHub

## ¿Qué hace?
Monitorea una carpeta local y sube automáticamente los archivos '.twbx' a GitHub.

## Requisitos
- Python 3.8+
- Git instalado
- Carpeta: 'Documentos/Tableau Workbooks/'

## Instalación Rápida
### 1. Clonar repositorio

```bash
git clone https://github.com/{usuario_git}/tableau-github-sync.git
cd tableau-github-sync
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Crear carpetas

Windows:
```bash
mkdir "%USERPROFILE%\Documents\Tableau Workbooks\{carpeta}"
```

### 3. Ejecutar script

Windows:
```bash
"C:\Users\{usuario_window}\AppData\Local\Microsoft\WindowsApps\python.exe sync_local.py
```

### Cómo usar
1. Descarga un workbook de Tableau Online
2. Guárdalo en: 'Documentos/Tableau Workbooks/{carpeta}/' (u otra carpeta)
3. El script lo detecta y lo sube a GitHub automáticamente
