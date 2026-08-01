@echo off
echo =========================================
echo  Testando o script Python diretamente
echo =========================================

cd /d "%~dp0"

if not exist .venv_dev\Scripts\python.exe (
    echo O ambiente virtual nao foi encontrado. Execute o configurar_ambiente_dev.bat primeiro.
    pause
    exit /b
)

.venv_dev\Scripts\python.exe main.py

pause
