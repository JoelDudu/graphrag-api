"""Serviço de autenticação"""

import logging
from services.api_client import get_api_client
from utils.session_manager import set_token

logger = logging.getLogger(__name__)


class AuthService:
    """Serviço de autenticação com API"""
    
    @staticmethod
    def login(email: str, password: str) -> dict:
        """
        Faz login na API
        
        Args:
            email: Email do usuário
            password: Senha do usuário
        
        Returns:
            Dict com token e dados do usuário
        
        Raises:
            Exception: Se falhar na autenticação
        """
        try:
            client = get_api_client()
            response = client.post(
                "/login",
                data={"email": email, "password": password}
            )
            
            # Armazenar token
            token = response.get("token")
            if token:
                set_token(token)
            
            logger.info(f"Login bem-sucedido para {email}")
            return response
        
        except Exception as e:
            logger.error(f"Erro ao fazer login: {str(e)}")
            raise


# Instância global
_auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Retorna instância do serviço de autenticação"""
    return _auth_service
