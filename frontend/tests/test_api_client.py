"""Testes para APIClient"""

import pytest
import responses
from services.api_client import APIClient
from config.settings import API_URL


@pytest.fixture
def client():
    """Fixture para cliente API"""
    return APIClient(base_url=API_URL)


@responses.activate
def test_get_request(client):
    """Testa requisição GET"""
    responses.add(
        responses.GET,
        f"{API_URL}/health",
        json={"status": "ok"},
        status=200
    )
    
    result = client.get("/health")
    assert result["status"] == "ok"


@responses.activate
def test_post_request(client):
    """Testa requisição POST"""
    responses.add(
        responses.POST,
        f"{API_URL}/login",
        json={"token": "test_token"},
        status=200
    )
    
    result = client.post("/login", data={"email": "test@test.com", "password": "123"})
    assert result["token"] == "test_token"


@responses.activate
def test_delete_request(client):
    """Testa requisição DELETE"""
    responses.add(
        responses.DELETE,
        f"{API_URL}/documents/123",
        json={"message": "Deleted"},
        status=200
    )
    
    result = client.delete("/documents/123")
    assert result["message"] == "Deleted"


@responses.activate
def test_retry_on_500_error(client):
    """Testa retry automático em erro 500"""
    # Primeira tentativa falha, segunda sucede
    responses.add(
        responses.GET,
        f"{API_URL}/health",
        json={"error": "Server error"},
        status=500
    )
    responses.add(
        responses.GET,
        f"{API_URL}/health",
        json={"status": "ok"},
        status=200
    )
    
    result = client.get("/health")
    assert result["status"] == "ok"


@responses.activate
def test_timeout_error(client):
    """Testa tratamento de timeout"""
    responses.add(
        responses.GET,
        f"{API_URL}/health",
        body=Exception("Timeout")
    )
    
    with pytest.raises(Exception):
        client.get("/health")


@responses.activate
def test_connection_error_with_retry(client):
    """Testa retry em erro de conexão"""
    # Simular erro de conexão seguido de sucesso
    responses.add(
        responses.GET,
        f"{API_URL}/health",
        body=ConnectionError("Connection failed")
    )
    responses.add(
        responses.GET,
        f"{API_URL}/health",
        json={"status": "ok"},
        status=200
    )
    
    result = client.get("/health")
    assert result["status"] == "ok"
