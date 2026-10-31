@echo off
title YouTube to MP3 Downloader
cd /d "%~dp0"

echo ========================================================
echo         YouTube to MP3 - Audio Downloader
echo ========================================================
echo.
echo Launching application...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while launching the application.
    pause
)
