@echo off
echo ========================================
echo   GraphRAG API v3.1 - Setup
echo   Autenticacao JWT + Multiplos Formatos
echo ========================================
echo.

echo [1/4] Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERRO: Falha ao instalar dependencias
    pause
    exit /b 1
)
echo.

echo [2/4] Verificando arquivo .env...
if not exist .env (
    echo ERRO: Arquivo .env nao encontrado!
    echo Por favor, crie o arquivo .env com as configuracoes necessarias.
    pause
    exit /b 1
)

findstr /C:"JWT_SECRET_KEY" .env >nul
if %errorlevel% neq 0 (
    echo.
    echo AVISO: JWT_SECRET_KEY nao encontrado no .env
    echo Adicionando configuracao padrao...
    echo. >> .env
    echo # JWT Authentication >> .env
    echo JWT_SECRET_KEY=your-secret-key-change-this-in-production-use-strong-random-key >> .env
    echo JWT_EXPIRE_MINUTES=1440 >> .env
    echo.
    echo IMPORTANTE: Altere JWT_SECRET_KEY no arquivo .env antes de usar em producao!
)
echo.

echo [3/4] Testando conexoes...
python -c "import requests; r=requests.get('http://localhost:8000/health'); print('API:', r.json())" 2>nul
if %errorlevel% neq 0 (
    echo AVISO: API nao esta rodando. Inicie com: python graph_api_v3.py
)
echo.

echo [4/4] Verificando estrutura de arquivos...
if not exist auth.py (
    echo ERRO: auth.py nao encontrado!
    pause
    exit /b 1
)
if not exist file_processor.py (
    echo ERRO: file_processor.py nao encontrado!
    pause
    exit /b 1
)
echo.

echo ========================================
echo   Setup Concluido!
echo ========================================
echo.
echo Proximos passos:
echo.
echo 1. Inicie o Celery Worker:
echo    python -m celery -A celery_worker worker --loglevel=info --pool=solo
echo.
echo 2. Em outro terminal, inicie a API:
echo    python graph_api_v3.py
echo.
echo 3. Teste a API:
echo    python test_api.py
echo.
echo 4. Ou teste com upload:
echo    python test_api.py seu_arquivo.docx claude generic
echo.
echo Documentacao:
echo - API_AUTH_GUIDE.md - Guia de autenticacao
echo - CHANGELOG_v3.1.md - Novidades da versao
echo.
echo Usuarios padrao:
echo - admin / admin123
echo - user / user123
echo.
echo IMPORTANTE: Altere JWT_SECRET_KEY no .env antes de producao!
echo.
pause
