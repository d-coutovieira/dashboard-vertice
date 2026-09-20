@echo off
chcp 65001 > nul
title Servidor Dashboard Vertice Retail - EloGroup
echo =================================================================
echo   EloGroup Executive Dashboard ^& AI Report Server
echo =================================================================
echo [1/2] Verificando dependencias Python...
python -m pip install -r requirements.txt --quiet
echo [2/2] Iniciando servidor do Dashboard...
echo Acesse no seu navegador: http://localhost:8088/
echo.
start http://localhost:8088/
python dashboard_server.py
pause
