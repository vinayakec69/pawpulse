@echo off
cd /d "%~dp0"
echo ===================================================
echo   PawPulse GitHub Push
echo   Remote: https://github.com/vinayakec69/pawpulse.git
echo ===================================================
git push -u origin main
echo.
pause
