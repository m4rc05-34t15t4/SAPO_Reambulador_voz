@echo off
echo =========================================
echo  Configurando Ambiente de Desenvolvimento
echo =========================================

cd /d "%~dp0"

REM Cria um ambiente virtual limpo chamado .venv_dev (se não existir)
if not exist .venv_dev\Scripts\python.exe (
    echo Criando novo ambiente virtual...
    python -m venv .venv_dev
)

REM Resolve o bug do PostgreSQL no Windows que quebra os downloads do PIP
set CURL_CA_BUNDLE=
set REQUESTS_CA_BUNDLE=

REM Instala ou atualiza as bibliotecas
echo Instalando dependencias e ferramentas (PyInstaller, etc)...
.venv_dev\Scripts\python.exe -m pip install --upgrade pip
.venv_dev\Scripts\pip install -r requirements.txt
.venv_dev\Scripts\pip install pyinstaller

echo =========================================
echo Ambiente pronto! 
pause
