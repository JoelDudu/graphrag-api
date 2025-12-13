"""Serviço de query/busca"""

import logging
from typing import Dict, Any, Optional
from services.api_client import get_api_client

logger = logging.getLogger(__name__)


class QueryService:
    """Serviço para operações de busca"""
    
    @staticmethod
    def query_semantic(
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Faz busca semântica
        
        Args:
            query: Pergunta/query
            document_id: ID do documento (opcional)
            top_k: Número de resultados
        
        Returns:
            Dict com resposta e fontes
        
        Raises:
            Exception: Se falhar na busca
        """
        try:
            client = get_api_client()
            response = client.post(
                "/query",
                data={
                    "query": query,
                    "document_id": document_id,
                    "search_type": "semantic",
                    "top_k": top_k
                }
            )
            
            logger.info(f"Busca semântica realizada: {query[:50]}...")
            return response
        
        except Exception as e:
            logger.error(f"Erro na busca semântica: {str(e)}")
            raise
    
    @staticmethod
    def query_graph(
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Faz busca por grafo
        
        Args:
            query: Pergunta/query
            document_id: ID do documento (opcional)
            top_k: Número de resultados
        
        Returns:
            Dict com resposta e entidades
        
        Raises:
            Exception: Se falhar na busca
        """
        try:
            client = get_api_client()
            response = client.post(
                "/query",
                data={
                    "query": query,
                    "document_id": document_id,
                    "search_type": "graph",
                    "top_k": top_k
                }
            )
            
            logger.info(f"Busca por grafo realizada: {query[:50]}...")
            return response
        
        except Exception as e:
            logger.error(f"Erro na busca por grafo: {str(e)}")
            raise
    
    @staticmethod
    def query_hybrid(
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Faz busca híbrida (semântica + grafo)
        
        Args:
            query: Pergunta/query
            document_id: ID do documento (opcional)
            top_k: Número de resultados
        
        Returns:
            Dict com resposta e fontes combinadas
        
        Raises:
            Exception: Se falhar na busca
        """
        try:
            client = get_api_client()
            response = client.post(
                "/query",
                data={
                    "query": query,
                    "document_id": document_id,
                    "search_type": "hybrid",
                    "top_k": top_k
                }
            )
            
            logger.info(f"Busca híbrida realizada: {query[:50]}...")
            return response
        
        except Exception as e:
            logger.error(f"Erro na busca híbrida: {str(e)}")
            raise


# Instância global
_query_service = QueryService()


def get_query_service() -> QueryService:
    """Retorna instância do serviço de query"""
    return _query_service
