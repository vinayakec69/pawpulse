@echo off
title PawPulse Shelter Vision & Telemetry Dashboard
echo ========================================================
echo  PawPulse Meowville Caretaker Dashboard
echo  Serving at: http://localhost:8080
echo ========================================================
echo.
cd /d "C:\animal\dashboard"
start "" "http://localhost:8080"
"C:\animal\.venv\Scripts\python.exe" -m http.server 8080 --bind 127.0.0.1
