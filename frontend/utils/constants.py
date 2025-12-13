"""Constantes da aplicação"""

# Modelos de IA disponíveis
MODELS = ["claude", "openai", "kimi"]

# Tipos de documentos
DOC_TYPES = {
    "generic": "Extração genérica - máximo de entidades e relacionamentos",
    "legal": "Documentos jurídicos - contratos, processos, leis",
    "medical": "Documentos médicos - diagnósticos, tratamentos, procedimentos",
    "technical": "Documentos técnicos - software, arquitetura, frameworks",
    "financial": "Documentos financeiros - transações, investimentos, mercado",
    "aesthetics": "Documentos de estética - procedimentos, produtos, tratamentos",
    "health": "Documentos de saúde geral - wellness, nutrição, lifestyle",
    "it": "Documentos de TI - infraestrutura, DevOps, segurança"
}

# Tipos de busca
SEARCH_TYPES = ["semantic", "graph", "hybrid"]

# Status de documento
DOCUMENT_STATUS = ["Pending", "Processing", "Completed", "Error"]

# Páginas disponíveis
PAGES = {
    "Dashboard": "pages/1_🏠_Dashboard.py",
    "Upload": "pages/2_📤_Upload.py",
    "Processamento": "pages/3_⚙️_Processamento.py",
    "Gestão": "pages/4_📋_Gestão.py",
    "Busca Semântica": "pages/5_🔍_Busca_Semântica.py",
    "Busca Grafo": "pages/6_🌐_Busca_Grafo.py",
    "Busca Híbrida": "pages/7_🔀_Busca_Híbrida.py",
    "Chatbot": "pages/8_💬_Chatbot.py",
}
