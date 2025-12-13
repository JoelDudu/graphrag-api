"""Formatadores de dados"""

from datetime import datetime


def format_date(date_str: str) -> str:
    """Formata data ISO para formato legível"""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_str


def format_file_size(size_bytes: int) -> str:
    """Formata tamanho de arquivo"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_progress(progress: float) -> str:
    """Formata progresso como percentual"""
    return f"{int(progress * 100)}%"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Trunca texto com ellipsis"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def format_status(status: str) -> str:
    """Formata status com emoji"""
    status_map = {
        "Pending": "⏳ Pendente",
        "Processing": "⚙️ Processando",
        "Completed": "✅ Concluído",
        "Error": "❌ Erro",
    }
    return status_map.get(status, status)
