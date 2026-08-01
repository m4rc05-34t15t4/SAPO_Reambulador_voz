@echo off
echo =========================================
echo  Gerando o executavel com PyInstaller
echo =========================================

cd /d "%~dp0"

echo Encerrando qualquer instancia aberta do app...
taskkill /F /IM sapo_audio_desc_point.exe 2>nul

if not exist .venv_dev\Scripts\pyinstaller.exe (
    echo O PyInstaller nao foi encontrado. Execute o configurar_ambiente_dev.bat primeiro.
    pause
    exit /b
)

.venv_dev\Scripts\python.exe -m PyInstaller --clean --paths .venv_dev\Lib\site-packages --icon=sapo_reambulador_digitando.ico --noconfirm --add-data "whisper;whisper" --add-data "ffmpeg;ffmpeg" --distpath ../ --name=sapo_audio_desc_point main.py

echo =========================================
echo Concluido!
pause
