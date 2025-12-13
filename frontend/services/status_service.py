"""Serviço de status com polling"""

import logging
import time
from typing import Dict, Any, Optional
from services.document_service import get_document_service

logger = logging.getLogger(__name__)


class StatusService:
    """Serviço para polling de status de documentos"""
    
    @staticmethod
    def poll_status(
        document_id: str,
        interval: int = 5,
        max_attempts: int = 120
    ) -> Dict[str, Any]:
        """
        Faz polling do status de um documento até completar ou erro
        
        Args:
            document_id: ID do documento
            interval: Intervalo entre tentativas em segundos
            max_attempts: Número máximo de tentativas
        
        Returns:
            Dict com status final
        
        Raises:
            Exception: Se timeout ou erro
        """
        service = get_document_service()
        attempts = 0
        
        while attempts < max_attempts:
            try:
                status = service.get_document_status(document_id)
                current_status = status.get("status")
                
                logger.info(f"Polling {document_id}: {current_status} ({attempts + 1}/{max_attempts})")
                
                # Se completado ou erro, retornar
                if current_status in ["Completed", "Error"]:
                    logger.info(f"Polling finalizado para {document_id}: {current_status}")
                    return status
                
                # Aguardar antes de próxima tentativa
                time.sleep(interval)
                attempts += 1
            
            except Exception as e:
                logger.error(f"Erro durante polling: {str(e)}")
                raise
        
        # Timeout
        logger.warning(f"Timeout ao fazer polling de {document_id}")
        raise Exception(f"Timeout ao processar documento (máximo {max_attempts * interval}s)")
    
    @staticmethod
    def get_status(document_id: str) -> Dict[str, Any]:
        """
        Obtém status atual sem polling
        
        Args:
            document_id: ID do documento
        
        Returns:
            Dict com status
        
        Raises:
            Exception: Se falhar
        """
        service = get_document_service()
        return service.get_document_status(document_id)


# Instância global
_status_service = StatusService()


def get_status_service() -> StatusService:
    """Retorna instância do serviço de status"""
    return _status_service
