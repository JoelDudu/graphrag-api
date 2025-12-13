"""
Script de teste para a API GraphRAG v3 com autenticação JWT
"""

import requests
import time
import sys
from pathlib import Path

# Configuração
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"


def print_section(title):
    """Imprime seção formatada"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def authenticate():
    """Autentica e retorna token"""
    print_section("1. AUTENTICAÇÃO")
    
    response = requests.post(
        f"{API_URL}/auth/login",
        data={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Autenticado com sucesso!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Erro na autenticação: {response.text}")
        sys.exit(1)


def check_health():
    """Verifica saúde da API"""
    print_section("2. HEALTH CHECK")
    
    response = requests.get(f"{API_URL}/health")
    health = response.json()
    
    print(f"API: {health['api']}")
    print(f"Neo4j: {health['neo4j']}")
    print(f"Redis: {health['redis']}")
    
    if health['neo4j'] != 'ok' or health['redis'] != 'ok':
        print("\n⚠️ Alguns serviços não estão funcionando!")
        return False
    
    print("\n✅ Todos os serviços OK!")
    return True


def get_supported_formats(token):
    """Lista formatos suportados"""
    print_section("3. FORMATOS SUPORTADOS")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/supported-formats", headers=headers)
    
    if response.status_code == 200:
        formats = response.json()
        print(f"Total de formatos: {formats['total']}\n")
        for ext, desc in formats['supported_formats'].items():
            print(f"  {ext:8} - {desc}")
        return True
    else:
        print(f"❌ Erro: {response.text}")
        return False


def upload_document(token, file_path):
    """Faz upload de documento"""
    print_section("4. UPLOAD DE DOCUMENTO")
    
    if not Path(file_path).exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return None
    
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_URL}/upload",
            headers=headers,
            files=files
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Upload realizado com sucesso!")
        print(f"Document ID: {data['document_id']}")
        print(f"Filename: {data['filename']}")
        print(f"Status: {data['status']}")
        return data['document_id']
    else:
        print(f"❌ Erro no upload: {response.text}")
        return None


def process_document(token, document_id, model="claude", doc_type="generic"):
    """Inicia processamento do documento"""
    print_section("5. PROCESSAR DOCUMENTO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{API_URL}/process",
        headers=headers,
        json={
            "document_id": document_id,
            "model": model,
            "doc_type": doc_type
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Processamento iniciado!")
        print(f"Modelo: {data['model']}")
        print(f"Status: {data['status']}")
        return True
    else:
        print(f"❌ Erro ao processar: {response.text}")
        return False


def check_status(token, document_id, wait=True):
    """Verifica status do processamento"""
    print_section("6. VERIFICAR STATUS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    while True:
        response = requests.get(
            f"{API_URL}/status/{document_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            progress = data['progress']
            
            print(f"\rStatus: {status} | Progresso: {progress:.1f}%", end="")
            
            if status == "Completed":
                print(f"\n\n✅ Processamento concluído!")
                print(f"Chunks: {data['chunks']}")
                print(f"Entidades: {data['entities']}")
                print(f"Relacionamentos: {data['relationships']}")
                return True
            
            elif status == "Failed":
                print(f"\n\n❌ Processamento falhou!")
                print(f"Erro: {data['error']}")
                return False
            
            elif not wait:
                print()
                return None
            
            time.sleep(5)
        else:
            print(f"\n❌ Erro ao verificar status: {response.text}")
            return False


def query_document(token, document_id, query, search_type="hybrid"):
    """Faz consulta ao documento"""
    print_section("7. CONSULTAR DOCUMENTO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Pergunta: {query}\n")
    
    response = requests.post(
        f"{API_URL}/query",
        headers=headers,
        json={
            "query": query,
            "document_id": document_id,
            "search_type": search_type,
            "top_k": 5
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Resposta:\n{data['answer']}\n")
        print(f"Modelo usado: {data['model_used']}")
        print(f"Fontes encontradas: {len(data['sources'])}")
        return True
    else:
        print(f"❌ Erro na consulta: {response.text}")
        return False


def list_documents(token):
    """Lista todos os documentos"""
    print_section("LISTAR DOCUMENTOS")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/documents", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total de documentos: {data['total']}\n")
        
        for doc in data['documents']:
            print(f"ID: {doc['document_id']}")
            print(f"  Arquivo: {doc['filename']}")
            print(f"  Status: {doc['status']} ({doc['progress']:.1f}%)")
            print(f"  Modelo: {doc['model']}")
            print(f"  Criado: {doc['created_at']}")
            print()
        
        return True
    else:
        print(f"❌ Erro: {response.text}")
        return False


def main():
    """Função principal"""
    print("\n🚀 Teste da API GraphRAG v3 com Autenticação JWT")
    
    # 1. Autenticar
    token = authenticate()
    
    # 2. Health check
    if not check_health():
        print("\n⚠️ Continuando mesmo com serviços com problemas...")
    
    # 3. Formatos suportados
    get_supported_formats(token)
    
    # 4. Listar documentos existentes
    list_documents(token)
    
    # 5. Upload (se arquivo fornecido)
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        model = sys.argv[2] if len(sys.argv) > 2 else "claude"
        doc_type = sys.argv[3] if len(sys.argv) > 3 else "generic"
        
        document_id = upload_document(token, file_path)
        
        if document_id:
            # 6. Processar
            if process_document(token, document_id, model, doc_type):
                # 7. Aguardar conclusão
                if check_status(token, document_id, wait=True):
                    # 8. Fazer consulta
                    query_document(
                        token, 
                        document_id, 
                        "Faça um resumo do documento"
                    )
    else:
        print("\n💡 Para testar upload e processamento, execute:")
        print(f"   python test_api.py <caminho_do_arquivo> [modelo] [tipo_doc]")
        print(f"\nExemplo:")
        print(f"   python test_api.py documento.docx claude generic")
        print(f"   python test_api.py planilha.xlsx openai financial")
        print(f"   python test_api.py apresentacao.pptx claude technical")


if __name__ == "__main__":
    main()
