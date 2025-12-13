"""Validadores de entrada"""

import re
from pathlib import Path


def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """Valida senha (não vazia)"""
    return len(password) > 0


def validate_office_file(file) -> bool:
    """Valida se arquivo é um formato suportado"""
    if file is None:
        return False
    
    # Extensões suportadas
    valid_extensions = [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv"]
    
    # Verificar extensão
    file_ext = Path(file.name).lower()
    if not any(file_ext.endswith(ext) for ext in valid_extensions):
        return False
    
    return True


def validate_query(query: str) -> bool:
    """Valida query (não vazia, mínimo 3 caracteres)"""
    return len(query.strip()) >= 3
