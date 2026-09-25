@echo off
setlocal
cd /d "%~dp0"
title Pricing - Execucao Local

echo ============================================================
echo              PRICING - EXECUCAO LOCAL
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao foi encontrado no PATH.
  echo Instale/ative o Python ou Miniconda e tente novamente.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Criando ambiente virtual local...
  python -m venv .venv
  if errorlevel 1 goto :erro
)

echo [2/3] Verificando dependencias...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :erro

echo [3/3] Iniciando o Pricing...
echo O navegador sera aberto automaticamente.
echo Endereco: http://localhost:8501
echo.

start "Pricing Streamlit" cmd /k ""%CD%\.venv\Scripts\python.exe" -m streamlit run "%CD%\dashboard_pricing.py" --server.address=localhost --server.port=8501 --server.headless=true"

echo Aguardando o sistema iniciar...
timeout /t 5 /nobreak >nul
start "" "http://localhost:8501"

echo.
echo Pricing iniciado. O navegador foi aberto automaticamente.
echo Esta janela pode ser fechada.
timeout /t 2 /nobreak >nul
exit /b 0

:erro
echo.
echo [ERRO] Nao foi possivel preparar/executar o ambiente local.
pause
exit /b 1
