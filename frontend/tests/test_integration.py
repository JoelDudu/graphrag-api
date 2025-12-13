"""Testes de integração"""

import pytest
import responses
from config.settings import API_URL
from services.document_service import DocumentService
from services.status_service import StatusService
from services.query_service import QueryService


@responses.activate
def test_upload_and_process_flow():
    \"\"\"Testa fluxo completo: upload -> processamento -> busca\"\"\"
    
    # Mock upload
    responses.add(
        responses.POST,
        f"{API_URL}/upload",
        json={"document_id": "123", "filename": "test.pdf", "status": "Pending"},
        status=200
    )
    
    # Mock process
    responses.add(
        responses.POST,
        f"{API_URL}/process",
        json={"document_id": "123", "status": "Processing"},
        status=200
    )
    
    # Mock status (completed)
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
    
    # Mock query
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Test answer",
            "sources": [{"text": "Source 1"}],
            "model_used": "claude"
        },
        status=200
    )
    
    # Executar fluxo
    class MockFile:
        name = "test.pdf"
        def read(self):
            return b"%PDF-1.4"
        def seek(self, pos):
            pass
    
    # Upload
    upload_result = DocumentService.upload_document(MockFile())
    assert upload_result["document_id"] == "123"
    
    # Status
    status_result = StatusService.get_status("123")
    assert status_result["status"] == "Completed"
    
    # Query
    query_result = QueryService.query_semantic("Test query")
    assert query_result["answer"] == "Test answer"


@responses.activate
def test_list_and_delete_flow():
    \"\"\"Testa fluxo: listar -> deletar\"\"\"
    
    # Mock list
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
    
    # Mock delete
    responses.add(
        responses.DELETE,
        f"{API_URL}/documents/1",
        json={"message": "Deleted"},
        status=200
    )
    
    # Listar
    docs = DocumentService.list_documents()
    assert len(docs) == 2
    
    # Deletar
    delete_result = DocumentService.delete_document("1")
    assert "Deleted" in delete_result["message"]


@responses.activate
def test_search_types_flow():
    \"\"\"Testa diferentes tipos de busca\"\"\"
    
    # Mock semantic search
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Semantic answer",
            "sources": [{"text": "Semantic source"}],
            "model_used": "claude"
        },
        status=200
    )
    
    # Mock graph search
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Graph answer",
            "sources": [{"entity": "Entity1"}],
            "model_used": "claude"
        },
        status=200
    )
    
    # Mock hybrid search
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Hybrid answer",
            "sources": [{"text": "Source"}, {"entity": "Entity"}],
            "model_used": "claude"
        },
        status=200
    )
    
    # Semantic
    semantic = QueryService.query_semantic("Query")
    assert "Semantic" in semantic["answer"]
    
    # Graph
    graph = QueryService.query_graph("Query")
    assert "Graph" in graph["answer"]
    
    # Hybrid
    hybrid = QueryService.query_hybrid("Query")
    assert "Hybrid" in hybrid["answer"]


@responses.activate
def test_error_handling():
    \"\"\"Testa tratamento de erros\"\"\"
    
    # Mock 404 error
    responses.add(
        responses.GET,
        f"{API_URL}/status/invalid",
        json={"detail": "Document not found"},
        status=404
    )
    
    # Deve lançar exceção
    with pytest.raises(Exception):
        StatusService.get_status("invalid")
