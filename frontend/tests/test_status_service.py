"""Testes para StatusService"""

import pytest
import responses
from services.status_service import StatusService
from config.settings import API_URL


@responses.activate
def test_get_status():
    """Testa obtenção de status"""
    responses.add(
        responses.GET,
        f"{API_URL}/status/123",
        json={
            "document_id": "123",
            "status": "Completed",
            "progress": 1.0,
            "chunks": 10,
            "entities": 50
        },
        status=200
    )
    
    result = StatusService.get_status("123")
    assert result["status"] == "Completed"
    assert result["progress"] == 1.0


@responses.activate
def test_poll_status_completed():
    """Testa polling até completar"""
    responses.add(
        responses.GET,
        f"{API_URL}/status/123",
        json={
            "document_id": "123",
            "status": "Completed",
            "progress": 1.0
        },
        status=200
    )
    
    result = StatusService.poll_status("123", interval=0.1, max_attempts=5)
    assert result["status"] == "Completed"


@responses.activate
def test_poll_status_error():
    """Testa polling com erro"""
    responses.add(
        responses.GET,
        f"{API_URL}/status/123",
        json={
            "document_id": "123",
            "status": "Error",
            "error": "Failed to process"
        },
        status=200
    )
    
    result = StatusService.poll_status("123", interval=0.1, max_attempts=5)
    assert result["status"] == "Error"


@responses.activate
def test_poll_status_timeout():
    """Testa timeout no polling"""
    responses.add(
        responses.GET,
        f"{API_URL}/status/123",
        json={
            "document_id": "123",
            "status": "Processing",
            "progress": 0.5
        },
        status=200
    )
    
    with pytest.raises(Exception, match="Timeout"):
        StatusService.poll_status("123", interval=0.01, max_attempts=2)
