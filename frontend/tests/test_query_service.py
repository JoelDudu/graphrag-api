"""Testes para QueryService"""

import pytest
import responses
from services.query_service import QueryService
from config.settings import API_URL


@responses.activate
def test_query_semantic():
    """Testa busca semântica"""
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "A resposta é...",
            "sources": [
                {"text": "Fonte 1", "score": 0.95},
                {"text": "Fonte 2", "score": 0.87}
            ],
            "model_used": "claude"
        },
        status=200
    )
    
    result = QueryService.query_semantic("Qual é a pergunta?")
    assert "answer" in result
    assert len(result["sources"]) == 2


@responses.activate
def test_query_graph():
    """Testa busca por grafo"""
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Resposta baseada em grafo",
            "sources": [
                {
                    "entity": "Entidade1",
                    "type": "Pessoa",
                    "description": "Descrição"
                }
            ],
            "model_used": "claude"
        },
        status=200
    )
    
    result = QueryService.query_graph("Qual é a pergunta?")
    assert "answer" in result
    assert len(result["sources"]) > 0


@responses.activate
def test_query_hybrid():
    """Testa busca híbrida"""
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Resposta híbrida",
            "sources": [
                {"text": "Fonte semântica", "metadata": {"search_type": "semantic"}},
                {"entity": "Entidade", "metadata": {"search_type": "graph"}}
            ],
            "model_used": "claude"
        },
        status=200
    )
    
    result = QueryService.query_hybrid("Qual é a pergunta?")
    assert "answer" in result
    assert len(result["sources"]) == 2


@responses.activate
def test_query_with_document_id():
    """Testa busca com document_id específico"""
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Resposta",
            "sources": [],
            "model_used": "claude"
        },
        status=200
    )
    
    result = QueryService.query_semantic("Pergunta", document_id="123")
    assert result["answer"] == "Resposta"


@responses.activate
def test_query_with_top_k():
    """Testa busca com top_k customizado"""
    responses.add(
        responses.POST,
        f"{API_URL}/query",
        json={
            "answer": "Resposta",
            "sources": [{"text": f"Fonte {i}"} for i in range(10)],
            "model_used": "claude"
        },
        status=200
    )
    
    result = QueryService.query_semantic("Pergunta", top_k=10)
    assert len(result["sources"]) == 10
