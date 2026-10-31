@echo off
title Stop YouTube to MP3 Background Service
echo Stopping background service...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*main.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Service stopped.
timeout /t 2 >nul
