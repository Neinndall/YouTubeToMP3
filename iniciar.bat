@echo off
title YouTube to MP3 Downloader
cd /d "%~dp0"

echo ========================================================
echo         YouTube to MP3 - Descargador de Musica
echo ========================================================
echo.
echo Iniciando aplicacion...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
