"""
Exemplo de Cliente Python para GraphRAG API v3.1
Demonstra uso completo da API com autenticação JWT e múltiplos formatos
"""

import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any


class GraphRAGClient:
    """Cliente Python para GraphRAG API v3.1"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
    
    def login(self, username: str, password: str) -> bool:
        """
        Autentica na API e armazena token
        
        Args:
            username: Nome de usuário
            password: Senha
            
        Returns:
            True se autenticação bem-sucedida
        """
        response = requests.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"✅ Autenticado como {username}")
            return True
        else:
            print(f"❌ Erro na autenticação: {response.text}")
            return False
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Retorna informações do usuário autenticado"""
        if not self.token:
            print("❌ Não autenticado")
            return None
        
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def health_check(self) -> Dict[str, str]:
        """Verifica saúde da API"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Lista formatos de arquivo suportados"""
        response = requests.get(
            f"{self.base_url}/supported-formats",
            headers=self.headers
        )
        return response.json()
    
    def upload_file(self, file_path: str) -> Optional[str]:
        """
        Faz upload de arquivo
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            document_id se sucesso, None se falha
        """
        if not Path(file_path).exists():
            print(f"❌ Arquivo não encontrado: {file_path}")
            return None
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{self.base_url}/upload",
                headers=self.headers,
                files=files
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload: {data['filename']} (ID: {data['document_id']})")
            return data['document_id']
        else:
            print(f"❌ Erro no upload: {response.text}")
            return None
    
    def process_document(
        self, 
        document_id: str, 
        model: str = "claude",
        doc_type: str = "generic"
    ) -> bool:
        """
        Inicia processamento de documento
        
        Args:
            document_id: ID do documento
            model: Modelo LLM (claude, openai, kimi, deepseek)
            doc_type: Tipo do documento (generic, legal, medical, etc.)
            
        Returns:
            True se processamento iniciado
        """
        response = requests.post(
            f"{self.base_url}/process",
            headers=self.headers,
            json={
                "document_id": document_id,
                "model": model,
                "doc_type": doc_type
            }
        )
        
        if response.status_code == 200:
            print(f"✅ Processamento iniciado com {model}")
            return True
        else:
            print(f"❌ Erro ao processar: {response.text}")
            return False
    
    def get_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retorna status do processamento"""
        response = requests.get(
            f"{self.base_url}/status/{document_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def wait_for_completion(
        self, 
        document_id: str, 
        timeout: int = 600,
        interval: int = 5
    ) -> bool:
        """
        Aguarda conclusão do processamento
        
        Args:
            document_id: ID do documento
            timeout: Tempo máximo de espera em segundos
            interval: Intervalo entre verificações em segundos
            
        Returns:
            True se completado com sucesso
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_status(document_id)
            
            if not status:
                return False
            
            current_status = status['status']
            progress = status['progress']
            
            print(f"\r⏳ Status: {current_status} | Progresso: {progress:.1f}%", end="")
            
            if current_status == "Completed":
                print(f"\n✅ Processamento concluído!")
                print(f"   Chunks: {status['chunks']}")
                print(f"   Entidades: {status['entities']}")
                print(f"   Relacionamentos: {status['relationships']}")
                return True
            
            elif current_status == "Failed":
                print(f"\n❌ Processamento falhou: {status.get('error', 'Unknown')}")
                return False
            
            time.sleep(interval)
        
        print(f"\n⏰ Timeout após {timeout}s")
        return False
    
    def query(
        self,
        query: str,
        document_id: Optional[str] = None,
        search_type: str = "hybrid",
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Faz consulta aos documentos
        
        Args:
            query: Pergunta
            document_id: ID do documento (opcional, busca em todos se None)
            search_type: Tipo de busca (semantic, graph, hybrid)
            top_k: Número de resultados
            
        Returns:
            Resposta com answer e sources
        """
        payload = {
            "query": query,
            "search_type": search_type,
            "top_k": top_k
        }
        
        if document_id:
            payload["document_id"] = document_id
        
        response = requests.post(
            f"{self.base_url}/query",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro na consulta: {response.text}")
            return None
    
    def list_documents(self) -> Optional[Dict[str, Any]]:
        """Lista todos os documentos"""
        response = requests.get(
            f"{self.base_url}/documents",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def delete_document(self, document_id: str) -> bool:
        """Exclui documento"""
        response = requests.delete(
            f"{self.base_url}/documents/{document_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            print(f"✅ Documento excluído: {document_id}")
            return True
        else:
            print(f"❌ Erro ao excluir: {response.text}")
            return False
    
    def get_doc_types(self) -> Optional[Dict[str, Any]]:
        """Lista tipos de documentos disponíveis"""
        response = requests.get(
            f"{self.base_url}/doc-types",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None


def example_usage():
    """Exemplo de uso completo"""
    
    # Criar cliente
    client = GraphRAGClient("http://localhost:8000")
    
    # 1. Autenticar
    if not client.login("admin", "admin123"):
        return
    
    # 2. Verificar saúde
    health = client.health_check()
    print(f"\n🏥 Health: API={health['api']}, Neo4j={health['neo4j']}, Redis={health['redis']}")
    
    # 3. Ver formatos suportados
    formats = client.get_supported_formats()
    print(f"\n📁 Formatos suportados: {formats['total']}")
    
    # 4. Ver tipos de documentos
    doc_types = client.get_doc_types()
    print(f"\n📋 Tipos de documentos: {', '.join(doc_types['available_types'])}")
    
    # 5. Listar documentos existentes
    docs = client.list_documents()
    print(f"\n📚 Documentos existentes: {docs['total']}")
    
    # 6. Upload e processamento (exemplo)
    file_path = "exemplo.docx"  # Altere para seu arquivo
    
    if Path(file_path).exists():
        print(f"\n📤 Fazendo upload de {file_path}...")
        
        # Upload
        document_id = client.upload_file(file_path)
        
        if document_id:
            # Processar
            if client.process_document(document_id, model="claude", doc_type="generic"):
                # Aguardar conclusão
                if client.wait_for_completion(document_id):
                    # Fazer consultas
                    print("\n🔍 Fazendo consultas...")
                    
                    # Consulta 1: Resumo
                    result = client.query(
                        "Faça um resumo do documento",
                        document_id=document_id,
                        search_type="hybrid"
                    )
                    
                    if result:
                        print(f"\n📝 Resumo:")
                        print(result['answer'])
                        print(f"\n🔗 Fontes: {len(result['sources'])}")
                    
                    # Consulta 2: Busca específica
                    result = client.query(
                        "Quais são os principais tópicos?",
                        document_id=document_id,
                        search_type="graph"
                    )
                    
                    if result:
                        print(f"\n🎯 Principais tópicos:")
                        print(result['answer'])
    else:
        print(f"\n💡 Para testar upload, crie um arquivo 'exemplo.docx'")
    
    print("\n✅ Exemplo concluído!")


if __name__ == "__main__":
    example_usage()
