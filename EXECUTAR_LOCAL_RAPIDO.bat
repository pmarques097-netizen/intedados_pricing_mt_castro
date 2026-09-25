@echo off
setlocal
cd /d "%~dp0"
title Pricing - Local Rapido

set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=%CD%\.venv\Scripts\python.exe"

start "Pricing Streamlit" cmd /k ""%PY%" -m streamlit run "%CD%\dashboard_pricing.py" --server.address=localhost --server.port=8501 --server.headless=true"
timeout /t 4 /nobreak >nul
start "" "http://localhost:8501"
exit /b 0
