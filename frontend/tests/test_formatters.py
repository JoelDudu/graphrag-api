"""Testes para formatadores"""

import pytest
from utils.formatters import (
    format_date,
    format_file_size,
    format_progress,
    truncate_text,
    format_status
)


def test_format_date():
    """Testa formatação de data"""
    result = format_date("2024-01-15T10:30:00")
    assert "15" in result
    assert "01" in result or "1" in result


def test_format_file_size_bytes():
    """Testa formatação de tamanho em bytes"""
    assert "B" in format_file_size(512)


def test_format_file_size_kb():
    """Testa formatação de tamanho em KB"""
    assert "KB" in format_file_size(1024 * 10)


def test_format_file_size_mb():
    """Testa formatação de tamanho em MB"""
    assert "MB" in format_file_size(1024 * 1024 * 5)


def test_format_progress():
    """Testa formatação de progresso"""
    assert format_progress(0.5) == "50%"
    assert format_progress(1.0) == "100%"
    assert format_progress(0.0) == "0%"


def test_truncate_text_short():
    """Testa truncação de texto curto"""
    text = "Hello"
    assert truncate_text(text) == text


def test_truncate_text_long():
    """Testa truncação de texto longo"""
    text = "A" * 300
    result = truncate_text(text, max_length=200)
    assert len(result) <= 203  # 200 + "..."
    assert result.endswith("...")


def test_format_status():
    """Testa formatação de status"""
    assert "Pendente" in format_status("Pending")
    assert "Processando" in format_status("Processing")
    assert "Concluído" in format_status("Completed")
    assert "Erro" in format_status("Error")
