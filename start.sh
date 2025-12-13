#!/bin/bash

# Script para iniciar a aplicação localmente

echo "🚀 Iniciando GraphRAG API v3.1"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Copie .env.example para .env e configure suas credenciais"
    exit 1
fi

# Verificar se venv existe
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python -m venv venv
fi

# Ativar venv
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# Criar diretório de uploads
mkdir -p uploads

echo ""
echo "✅ Ambiente configurado!"
echo ""
echo "Iniciando serviços..."
echo ""

# Iniciar Redis (se não estiver rodando)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "🔴 Redis não está rodando. Inicie com: redis-server"
fi

# Iniciar Worker em background
echo "🔧 Iniciando Celery Worker..."
python -m celery -A celery_worker worker --loglevel=info --pool=solo &
WORKER_PID=$!

# Aguardar um pouco
sleep 2

# Iniciar API
echo "🌐 Iniciando API..."
python graph_api_v3.py

# Cleanup ao sair
trap "kill $WORKER_PID" EXIT
