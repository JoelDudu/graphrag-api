"""Testes para validadores"""

import pytest
from utils.validators import (
    validate_email,
    validate_password,
    validate_pdf_file,
    validate_query
)


def test_validate_email_valid():
    """Testa validação de email válido"""
    assert validate_email("test@example.com") is True
    assert validate_email("user.name@domain.co.uk") is True


def test_validate_email_invalid():
    """Testa validação de email inválido"""
    assert validate_email("invalid") is False
    assert validate_email("@example.com") is False
    assert validate_email("test@") is False


def test_validate_password_valid():
    """Testa validação de senha válida"""
    assert validate_password("password123") is True
    assert validate_password("a") is True


def test_validate_password_invalid():
    """Testa validação de senha inválida"""
    assert validate_password("") is False
    assert validate_password(None) is False


def test_validate_pdf_file_valid():
    """Testa validação de arquivo PDF válido"""
    class MockFile:
        name = "test.pdf"
        def read(self):
            return b"%PDF-1.4"
        def seek(self, pos):
            pass
    
    assert validate_pdf_file(MockFile()) is True


def test_validate_pdf_file_invalid_extension():
    """Testa validação com extensão inválida"""
    class MockFile:
        name = "test.txt"
        def read(self):
            return b"%PDF-1.4"
        def seek(self, pos):
            pass
    
    assert validate_pdf_file(MockFile()) is False


def test_validate_pdf_file_invalid_content():
    """Testa validação com conteúdo inválido"""
    class MockFile:
        name = "test.pdf"
        def read(self):
            return b"Not a PDF"
        def seek(self, pos):
            pass
    
    assert validate_pdf_file(MockFile()) is False


def test_validate_query_valid():
    """Testa validação de query válida"""
    assert validate_query("What is this?") is True
    assert validate_query("   Hello world   ") is True


def test_validate_query_invalid():
    """Testa validação de query inválida"""
    assert validate_query("") is False
    assert validate_query("ab") is False
    assert validate_query("   ") is False
