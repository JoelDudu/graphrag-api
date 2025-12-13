"""Cliente HTTP para comunicação com API GraphRAG"""

import requests
from typing import Any, Dict, Optional
import logging
from config.settings import API_URL, API_TIMEOUT, MAX_RETRIES
from utils.session_manager import get_token

logger = logging.getLogger(__name__)


class APIClient:
    """Cliente HTTP com autenticação e retry automático"""
    
    def __init__(self, base_url: str = API_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers com token de autenticação"""
        headers = {"Content-Type": "application/json"}
        token = get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        retries: int = 0
    ) -> Dict[str, Any]:
        """Faz requisição HTTP com retry automático"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=self.timeout)
            elif method == "POST":
                if files:
                    # Para upload de arquivo, não usar JSON
                    response = self.session.post(
                        url,
                        files=files,
                        headers={k: v for k, v in headers.items() if k != "Content-Type"},
                        timeout=self.timeout
                    )
                else:
                    response = self.session.post(
                        url,
                        json=data,
                        headers=headers,
                        timeout=self.timeout
                    )
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            # Tratamento de erro 401 (token expirado)
            if response.status_code == 401:
                logger.warning("Token expirado")
                from utils.session_manager import clear_session
                clear_session()
                raise Exception("Token expirado. Por favor, faça login novamente.")
            
            # Retry para erros de rede
            if response.status_code >= 500 and retries < MAX_RETRIES:
                logger.warning(f"Erro 5xx, tentando novamente... ({retries + 1}/{MAX_RETRIES})")
                return self._request(method, endpoint, data, files, retries + 1)
            
            response.raise_for_status()
            
            # Retornar JSON se disponível
            try:
                return response.json()
            except:
                return {"status": "ok", "data": response.text}
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout na requisição para {url}")
            raise Exception(f"Timeout ao conectar com a API ({self.timeout}s)")
        
        except requests.exceptions.ConnectionError:
            if retries < MAX_RETRIES:
                logger.warning(f"Erro de conexão, tentando novamente... ({retries + 1}/{MAX_RETRIES})")
                return self._request(method, endpoint, data, files, retries + 1)
            logger.error(f"Erro de conexão com {url}")
            raise Exception("Erro ao conectar com a API. Verifique se o servidor está rodando.")
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                raise Exception(error_data.get("detail", str(e)))
            except:
                raise Exception(f"Erro HTTP {e.response.status_code}: {e.response.text}")
        
        except Exception as e:
            logger.error(f"Erro na requisição: {str(e)}")
            raise
    
    def get(self, endpoint: str) -> Dict[str, Any]:
        """Faz requisição GET"""
        return self._request("GET", endpoint)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Faz requisição POST"""
        return self._request("POST", endpoint, data, files)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Faz requisição DELETE"""
        return self._request("DELETE", endpoint)
    
    def close(self):
        """Fecha session"""
        self.session.close()


# Instância global
_client = None


def get_api_client() -> APIClient:
    """Retorna instância global do cliente API"""
    global _client
    if _client is None:
        _client = APIClient()
    return _client
