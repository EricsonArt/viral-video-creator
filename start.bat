@echo off
echo Uruchamiam Viral Video Creator...

start "Streamlit" cmd /k "cd /d %~dp0 && streamlit run app.py"

timeout /t 4 /nobreak >nul

start "ngrok" cmd /k "ngrok http 8501"

echo.
echo Gotowe! Sprawdz okno ngrok po link publiczny.
echo Nie zamykaj tych okien przez noc.
pause
