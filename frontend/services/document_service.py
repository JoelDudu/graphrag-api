"""Serviço de documentos"""

import logging
from typing import List, Dict, Any, Optional
from services.api_client import get_api_client

logger = logging.getLogger(__name__)


class DocumentService:
    """Serviço para operações com documentos"""
    
    @staticmethod
    def upload_document(file) -> Dict[str, Any]:
        """
        Faz upload de documento
        
        Args:
            file: Arquivo para upload
        
        Returns:
            Dict com document_id e status
        
        Raises:
            Exception: Se falhar no upload
        """
        try:
            client = get_api_client()
            files = {"file": (file.name, file, "application/pdf")}
            response = client.post("/upload", files=files)
            
            logger.info(f"Upload bem-sucedido: {file.name}")
            return response
        
        except Exception as e:
            logger.error(f"Erro ao fazer upload: {str(e)}")
            raise
    
    @staticmethod
    def list_documents() -> List[Dict[str, Any]]:
        """
        Lista todos os documentos
        
        Returns:
            Lista de documentos
        
        Raises:
            Exception: Se falhar na listagem
        """
        try:
            client = get_api_client()
            response = client.get("/documents")
            
            documents = response.get("documents", [])
            logger.info(f"Listados {len(documents)} documentos")
            return documents
        
        except Exception as e:
            logger.error(f"Erro ao listar documentos: {str(e)}")
            raise
    
    @staticmethod
    def get_document_status(document_id: str) -> Dict[str, Any]:
        """
        Obtém status de um documento
        
        Args:
            document_id: ID do documento
        
        Returns:
            Dict com status e metadados
        
        Raises:
            Exception: Se falhar ao obter status
        """
        try:
            client = get_api_client()
            response = client.get(f"/status/{document_id}")
            
            logger.info(f"Status obtido para {document_id}: {response.get('status')}")
            return response
        
        except Exception as e:
            logger.error(f"Erro ao obter status: {str(e)}")
            raise
    
    @staticmethod
    def delete_document(document_id: str) -> Dict[str, Any]:
        """
        Deleta um documento
        
        Args:
            document_id: ID do documento
        
        Returns:
            Dict com mensagem de sucesso
        
        Raises:
            Exception: Se falhar na deleção
        """
        try:
            client = get_api_client()
            response = client.delete(f"/documents/{document_id}")
            
            logger.info(f"Documento deletado: {document_id}")
            return response
        
        except Exception as e:
            logger.error(f"Erro ao deletar documento: {str(e)}")
            raise
    
    @staticmethod
    def get_doc_types() -> Dict[str, Any]:
        """
        Obtém tipos de documentos disponíveis
        
        Returns:
            Dict com tipos e descrições
        
        Raises:
            Exception: Se falhar ao obter tipos
        """
        try:
            client = get_api_client()
            response = client.get("/doc-types")
            
            logger.info("Tipos de documentos obtidos")
            return response
        
        except Exception as e:
            logger.error(f"Erro ao obter tipos de documentos: {str(e)}")
            raise


# Instância global
_document_service = DocumentService()


def get_document_service() -> DocumentService:
    """Retorna instância do serviço de documentos"""
    return _document_service
