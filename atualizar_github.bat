@echo off
setlocal enabledelayedexpansion
title Atualizar Repositorio GitHub - Op_Tasty

echo ======================================================================
echo           ATUALIZACAO AUTOMATIZADA DO REPOSITORIO GITHUB
echo ======================================================================
echo.

where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] O comando 'git' nao foi encontrado no PATH do sistema.
    echo Por favor, instale o Git ou configure o PATH.
    pause
    exit /b 1
)

echo [1/4] Verificando integridade e seguranca de credenciais...
rem Garantir que arquivos sensiveis nao sejam versionados
git status --porcelain | findstr /I "\.env$" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [ALERTA DE SEGURANCA] O arquivo .env foi detectado no rastreamento!
    echo Cancelando operacao para evitar exposicao de credenciais.
    git reset HEAD .env >nul 2>&1
    pause
    exit /b 1
)
echo [OK] Nenhuma credencial sensivel exposta.

echo.
echo [2/4] Verificando modificacoes locais...
git status -s
echo.

rem Verifica se ha alteracoes para enviar
git status --porcelain | findstr /r "." >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Nenhuma alteracao pendente para commit.
    echo Verificando se ha commits locais pendentes de envio...
    git push origin master
    if !ERRORLEVEL! EQU 0 (
        echo.
        echo [OK] Repositorio no GitHub ja esta 100%% atualizado!
    ) else (
        echo.
        echo [ERRO] Falha ao enviar para o GitHub. Verifique sua conexao ou permissoes.
    )
    echo.
    pause
    exit /b 0
)

echo [3/4] Preparando commit...
set /p COMMIT_MSG="Digite a mensagem do commit (Enter para padrao): "
if "!COMMIT_MSG!"=="" (
    set "COMMIT_MSG=Atualizacao do sistema: %date% %time%"
)

git add -A

rem Dupla checagem antes de comitar: impedir inclusao acidental do .env
git diff --staged --name-only | findstr /I "\.env$" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [ALERTA DE SEGURANCA] Impedindo commit acidental do arquivo .env!
    git reset HEAD .env >nul 2>&1
    echo [OK] .env desmarcado do commit com sucesso.
)

git commit -m "!COMMIT_MSG!"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao criar o commit.
    pause
    exit /b 1
)

echo.
echo [4/4] Enviando alteracoes para o GitHub (origin master)...
git push origin master
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Falha ao enviar para o GitHub. Verifique sua autenticacao/conexao.
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo  SUCESSO: Codigo atualizado e sincronizado no GitHub com seguranca!
echo  Repositorio: https://github.com/jrveloso8-ai/op_tasty
echo ======================================================================
echo.
pause
