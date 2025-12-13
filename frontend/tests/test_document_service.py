"""Testes para DocumentService"""

import pytest
import responses
from services.document_service import DocumentService
from config.settings import API_URL


@responses.activate
def test_upload_document():
    """Testa upload de documento"""
    responses.add(
        responses.POST,
        f"{API_URL}/upload",
        json={"document_id": "123", "filename": "test.pdf", "status": "Pending"},
        status=200
    )
    
    # Mock de arquivo
    class MockFile:
        name = "test.pdf"
        def read(self):
            return b"%PDF-1.4"
    
    result = DocumentService.upload_document(MockFile())
    assert result["document_id"] == "123"
    assert result["status"] == "Pending"


@responses.activate
def test_list_documents():
    """Testa listagem de documentos"""
    responses.add(
        responses.GET,
        f"{API_URL}/documents",
        json={
            "documents": [
                {"document_id": "1", "filename": "doc1.pdf", "status": "Completed"},
                {"document_id": "2", "filename": "doc2.pdf", "status": "Pending"}
            ],
            "total": 2
        },
        status=200
    )
    
    result = DocumentService.list_documents()
    assert len(result) == 2
    assert result[0]["document_id"] == "1"


@responses.activate
def test_get_document_status():
    """Testa obtenção de status"""
    responses.add(
        responses.GET,
        f"{API_URL}/status/123",
        json={
            "document_id": "123",
            "filename": "test.pdf",
            "status": "Processing",
            "progress": 0.5
        },
        status=200
    )
    
    result = DocumentService.get_document_status("123")
    assert result["document_id"] == "123"
    assert result["status"] == "Processing"


@responses.activate
def test_delete_document():
    """Testa deleção de documento"""
    responses.add(
        responses.DELETE,
        f"{API_URL}/documents/123",
        json={"message": "Documento excluído com sucesso"},
        status=200
    )
    
    result = DocumentService.delete_document("123")
    assert "sucesso" in result["message"].lower()


@responses.activate
def test_get_doc_types():
    """Testa obtenção de tipos de documentos"""
    responses.add(
        responses.GET,
        f"{API_URL}/doc-types",
        json={
            "available_types": ["generic", "legal", "medical"],
            "descriptions": {
                "generic": "Extração genérica",
                "legal": "Documentos jurídicos",
                "medical": "Documentos médicos"
            }
        },
        status=200
    )
    
    result = DocumentService.get_doc_types()
    assert "generic" in result["available_types"]
    assert len(result["available_types"]) == 3
