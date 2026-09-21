@echo off
setlocal
title Gate de Auditoria - Screener Tastytrade

echo ======================================================================
echo           GATE DE AUDITORIA AUTOMATIZADO (OP_TASTY)
echo ======================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao foi encontrado no PATH do sistema.
    pause
    exit /b 1
)

python scripts/run_gate.py
echo.
pause
