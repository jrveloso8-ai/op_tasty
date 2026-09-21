@echo off
setlocal
title Screener Tastytrade - 8 Estrategias

echo ======================================================================
echo           SCREENER TASTYTRADE - 8 ESTRATEGIAS DE OPCOES
echo ======================================================================
echo.

where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao foi encontrado no PATH do sistema.
    echo Por favor, instale o Python 3.10+ ou adicione-o ao PATH.
    pause
    exit /b 1
)

echo [1/3] Executando motor de varredura quantitativo...
python -m src.screener
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha na execucao da varredura do screener.
    pause
    exit /b 1
)

echo.
echo [2/3] Atualizando interface web single-file (index.html)...
python scripts/build_ui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha na atualizacao do index.html.
    pause
    exit /b 1
)

echo.
echo [3/3] Abrindo painel Financial Dark no navegador padrao...
start "" "index.html"

echo.
echo ======================================================================
echo  Execucao concluida com sucesso!
echo  Resultados disponiveis em:
echo    - index.html (Painel Interativo)
echo    - screener_output.csv (Exportacao Tabular)
echo    - screener_output.json (Payload Auditavel)
echo ======================================================================
echo.
pause
