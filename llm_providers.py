"""
LLM Providers Factory
Suporte a múltiplos LLMs para extração de grafo e chat.
Inclui: Claude, OpenAI, Kimi e DeepSeek (via LM Studio local)
"""

import os
import json
import time
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer
import anthropic
from openai import OpenAI as OpenAIClient


class ClaudeBatchProcessor:
    """Processa múltiplos chunks usando Anthropic Batch API (50% mais barato)"""
    
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    
    def create_batch_requests(self, chunks: list, system_prompt: str = None) -> list:
        """Cria requisições para batch processing"""
        requests = []
        
        # Prompt padrão genérico (máximo de entidades e relacionamentos)
        if not system_prompt:
            system_prompt = """Extract all entities and relationships from this text to build a knowledge graph.

Return ONLY this JSON format:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "what is this"}}
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "RELATIONSHIP", "properties": {"description": "how they relate"}}
  ]
}

Rules:
- Extract EVERY entity: people, organizations, places, concepts, products, events
- Use simple IDs like "person_name", "org_name", "concept_name"
- Extract ALL relationships between entities
- If no entities, return {"nodes": [], "relationships": []}
- Return ONLY JSON, no markdown or text"""
        
        for i, chunk in enumerate(chunks):
            requests.append({
                "custom_id": f"chunk_{i}",
                "params": {
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 2048,
                    "system": system_prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Extract entities and relationships from this text:\n\n{chunk.page_content}"
                        }
                    ]
                }
            })
        
        return requests
    
    def submit_batch(self, requests: list) -> str:
        """Submete batch para processamento"""
        print(f"📤 Submetendo batch com {len(requests)} requisições...")
        
        batch = self.client.beta.messages.batches.create(
            requests=requests
        )
        
        print(f"   Batch ID: {batch.id}")
        print(f"   Status: {batch.processing_status}")
        
        return batch.id
    
    def wait_batch_completion(self, batch_id: str, max_wait: int = 3600, callback=None) -> dict:
        """Aguarda conclusão do batch (máx 1 hora)"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            batch = self.client.beta.messages.batches.retrieve(batch_id)
            
            # Mostrar status apenas quando muda
            # request_counts tem: succeeded, errored, expired, processing
            total = batch.request_counts.succeeded + batch.request_counts.errored + batch.request_counts.expired + batch.request_counts.processing
            current_status = f"{batch.processing_status} | Processados: {batch.request_counts.processing}/{total}"
            if current_status != last_status:
                print(f"   Status: {current_status}")
                last_status = current_status
            
            if batch.processing_status == "ended":
                elapsed = time.time() - start_time
                print(f"   ✅ Batch concluído em {elapsed:.0f}s!")
                print(f"      - Sucesso: {batch.request_counts.succeeded}")
                print(f"      - Erros: {batch.request_counts.errored}")
                print(f"      - Expirados: {batch.request_counts.expired}")
                
                # Chamar callback se fornecido
                if callback:
                    callback(batch_id, "completed")
                
                return batch
            
            time.sleep(10)  # Verificar a cada 10 segundos
        
        # Timeout
        if callback:
            callback(batch_id, "timeout")
        
        raise TimeoutError(f"Batch {batch_id} não completou em {max_wait}s")
    
    def process_batch_results(self, batch_id: str) -> list:
        """Processa resultados do batch"""
        results = []
        
        print(f"📥 Processando resultados do batch {batch_id}...")
        
        for i, result in enumerate(self.client.beta.messages.batches.results(batch_id)):
            try:
                if result.result.type == "succeeded":
                    content = result.result.message.content[0].text
                    
                    # Debug: mostrar primeiras respostas
                    if i < 3:
                        print(f"   [DEBUG] Chunk {i+1} resposta: {content[:200]}")
                    
                    # Tentar parse JSON
                    if not content or content.strip() == "":
                        print(f"   ⚠️ Chunk {result.custom_id}: resposta vazia")
                        graph_data = {"nodes": [], "relationships": []}
                    else:
                        graph_data = json.loads(content)
                    
                    results.append({
                        "chunk_id": result.custom_id,
                        "status": "success",
                        "data": graph_data
                    })
                else:
                    results.append({
                        "chunk_id": result.custom_id,
                        "status": "failed",
                        "error": result.result.error.message if hasattr(result.result, 'error') else "Unknown error"
                    })
            except json.JSONDecodeError as e:
                print(f"   ⚠️ Chunk {result.custom_id}: JSON inválido - {str(e)[:100]}")
                results.append({
                    "chunk_id": result.custom_id,
                    "status": "parse_error",
                    "error": str(e),
                    "data": {"nodes": [], "relationships": []}
                })
        
        return results
    
    def recover_batch(self, batch_id: str, callback=None) -> list:
        """Recupera resultados de um batch existente"""
        print(f"🔄 Recuperando batch {batch_id}...")
        
        # Verificar status do batch
        batch = self.client.beta.messages.batches.retrieve(batch_id)
        
        if batch.processing_status == "ended":
            print(f"   ✅ Batch já concluído, processando resultados...")
            if callback:
                callback(batch_id, "completed")
            return self.process_batch_results(batch_id)
        elif batch.processing_status in ["in_progress", "validating"]:
            print(f"   ⏳ Batch ainda em processamento, aguardando...")
            batch = self.wait_batch_completion(batch_id, callback=callback)
            return self.process_batch_results(batch_id)
        else:
            raise Exception(f"Batch em estado inválido: {batch.processing_status}")
    
    def process_chunks_batch(self, chunks: list, callback=None, system_prompt: str = None, save_batch_id=None) -> list:
        """Processa todos os chunks usando Batch API
        
        Args:
            chunks: Lista de documentos para processar
            callback: Função chamada quando batch termina
            system_prompt: Prompt customizado para extração (se None, usa genérico)
            save_batch_id: Função para salvar batch_id no banco
        """
        requests = self.create_batch_requests(chunks, system_prompt=system_prompt)
        batch_id = self.submit_batch(requests)
        
        # Salvar batch_id se função fornecida
        if save_batch_id:
            save_batch_id(batch_id)
        
        batch = self.wait_batch_completion(batch_id, callback=callback)
        results = self.process_batch_results(batch_id)
        
        return results


class OpenAIBatchProcessor:
    """Processa múltiplos chunks usando OpenAI Batch API (50% mais barato)"""
    
    def __init__(self, api_key: str = None):
        self.client = OpenAIClient(api_key=api_key or os.getenv("OPENAI_API_KEY"))
    
    def create_batch_requests(self, chunks: list, system_prompt: str = None) -> str:
        """Cria arquivo JSONL com requisições para batch"""
        import tempfile
        
        if not system_prompt:
            system_prompt = """Extract all entities and relationships from this text to build a knowledge graph.

Return ONLY this JSON format:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "what is this"}}
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "RELATIONSHIP", "properties": {"description": "how they relate"}}
  ]
}

Rules:
- Extract EVERY entity: people, organizations, places, concepts, products, events
- Use simple IDs like "person_name", "org_name", "concept_name"
- Extract ALL relationships between entities
- If no entities, return {"nodes": [], "relationships": []}
- Return ONLY JSON, no markdown or text"""
        
        # Criar arquivo JSONL temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i, chunk in enumerate(chunks):
                request = {
                    "custom_id": f"chunk_{i}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Extract entities and relationships:\n\n{chunk.page_content}"}
                        ],
                        "temperature": 0
                    }
                }
                f.write(json.dumps(request) + '\n')
            
            return f.name
    
    def submit_batch(self, jsonl_file: str) -> str:
        """Submete batch para processamento"""
        print(f"📤 Submetendo batch com arquivo JSONL...")
        
        with open(jsonl_file, 'rb') as f:
            batch_input_file = self.client.files.create(
                file=f,
                purpose="batch"
            )
        
        batch = self.client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        print(f"   Batch ID: {batch.id}")
        print(f"   Status: {batch.status}")
        
        return batch.id
    
    def wait_batch_completion(self, batch_id: str, max_wait: int = 86400, callback=None) -> dict:
        """Aguarda conclusão do batch (máx 24 horas)"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < max_wait:
            batch = self.client.batches.retrieve(batch_id)
            
            current_status = f"{batch.status} | Processados: {batch.request_counts.completed}/{batch.request_counts.total}"
            if current_status != last_status:
                print(f"   Status: {current_status}")
                last_status = current_status
            
            if batch.status == "completed":
                elapsed = time.time() - start_time
                print(f"   ✅ Batch concluído em {elapsed:.0f}s!")
                print(f"      - Sucesso: {batch.request_counts.completed}")
                print(f"      - Erros: {batch.request_counts.failed}")
                
                if callback:
                    callback(batch_id, "completed")
                
                return batch
            
            time.sleep(10)
        
        if callback:
            callback(batch_id, "timeout")
        
        raise TimeoutError(f"Batch {batch_id} não completou em {max_wait}s")
    
    def process_batch_results(self, batch_id: str) -> list:
        """Processa resultados do batch"""
        results = []
        
        print(f"📥 Processando resultados do batch {batch_id}...")
        
        # Obter informações do batch
        batch = self.client.batches.retrieve(batch_id)
        
        if not batch.output_file_id:
            print(f"   ⚠️ Batch sem arquivo de output")
            return results
        
        # Baixar arquivo de resultados
        file_response = self.client.files.content(batch.output_file_id)
        
        # Processar cada linha do JSONL
        for line in file_response.text.strip().split('\n'):
            if not line:
                continue
            
            try:
                result = json.loads(line)
                custom_id = result.get('custom_id')
                response = result.get('response', {})
                
                if response.get('status_code') == 200:
                    body = response.get('body', {})
                    content = body.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    if not content or content.strip() == "":
                        graph_data = {"nodes": [], "relationships": []}
                    else:
                        graph_data = json.loads(content)
                    
                    results.append({
                        "chunk_id": custom_id,
                        "status": "success",
                        "data": graph_data
                    })
                else:
                    results.append({
                        "chunk_id": custom_id,
                        "status": "failed",
                        "error": f"HTTP {response.get('status_code')}"
                    })
            except json.JSONDecodeError as e:
                results.append({
                    "chunk_id": custom_id if 'custom_id' in locals() else "unknown",
                    "status": "parse_error",
                    "error": str(e),
                    "data": {"nodes": [], "relationships": []}
                })
        
        return results
    
    def recover_batch(self, batch_id: str, callback=None) -> list:
        """Recupera resultados de um batch existente"""
        print(f"🔄 Recuperando batch {batch_id}...")
        
        # Verificar status do batch
        batch = self.client.batches.retrieve(batch_id)
        
        if batch.status == "completed":
            print(f"   ✅ Batch já concluído, processando resultados...")
            if callback:
                callback(batch_id, "completed")
            return self.process_batch_results(batch_id)
        elif batch.status in ["validating", "in_progress", "finalizing"]:
            print(f"   ⏳ Batch ainda em processamento, aguardando...")
            batch = self.wait_batch_completion(batch_id, callback=callback)
            return self.process_batch_results(batch_id)
        else:
            raise Exception(f"Batch em estado inválido: {batch.status}")
    
    def process_chunks_batch(self, chunks: list, callback=None, system_prompt: str = None, save_batch_id=None) -> list:
        """Processa todos os chunks usando Batch API"""
        jsonl_file = self.create_batch_requests(chunks, system_prompt=system_prompt)
        batch_id = self.submit_batch(jsonl_file)
        
        # Salvar batch_id se função fornecida
        if save_batch_id:
            save_batch_id(batch_id)
        
        batch = self.wait_batch_completion(batch_id, callback=callback)
        results = self.process_batch_results(batch_id)
        
        # Limpar arquivo temporário
        import os as os_module
        os_module.unlink(jsonl_file)
        
        return results


class KimiBatchProcessor:
    """Processa múltiplos chunks em paralelo usando Kimi (simula Batch)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("MOONSHOT_API_KEY não configurada")
    
    def create_batch_requests(self, chunks: list, system_prompt: str = None) -> list:
        """Cria requisições para processamento paralelo"""
        requests = []
        
        if not system_prompt:
            system_prompt = """Extract all entities and relationships from this text to build a knowledge graph.

Return ONLY this JSON format:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "what is this"}}
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "RELATIONSHIP", "properties": {"description": "how they relate"}}
  ]
}

Rules:
- Extract EVERY entity: people, organizations, places, concepts, products, events
- Use simple IDs like "person_name", "org_name", "concept_name"
- Extract ALL relationships between entities
- If no entities, return {"nodes": [], "relationships": []}
- Return ONLY JSON, no markdown or text"""
        
        for i, chunk in enumerate(chunks):
            requests.append({
                "custom_id": f"chunk_{i}",
                "system_prompt": system_prompt,
                "user_message": f"Extract entities and relationships:\n\n{chunk.page_content}"
            })
        
        return requests
    
    def process_chunk(self, request: dict) -> dict:
        """Processa um chunk individual"""
        from openai import OpenAI
        
        client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.ai/v1"
        )
        
        try:
            response = client.chat.completions.create(
                model="kimi-k2-thinking-turbo",
                messages=[
                    {"role": "system", "content": request["system_prompt"]},
                    {"role": "user", "content": request["user_message"]}
                ],
                temperature=0,
                timeout=300
            )
            
            content = response.choices[0].message.content
            
            if not content or content.strip() == "":
                graph_data = {"nodes": [], "relationships": []}
            else:
                graph_data = json.loads(content)
            
            return {
                "chunk_id": request["custom_id"],
                "status": "success",
                "data": graph_data
            }
        except json.JSONDecodeError as e:
            return {
                "chunk_id": request["custom_id"],
                "status": "parse_error",
                "error": str(e),
                "data": {"nodes": [], "relationships": []}
            }
        except Exception as e:
            return {
                "chunk_id": request["custom_id"],
                "status": "failed",
                "error": str(e)
            }
    
    def recover_batch(self, batch_id: str, callback=None) -> list:
        """Kimi não suporta recuperação (processamento síncrono)"""
        raise Exception("Kimi não suporta recuperação de batch - reprocesse o documento")
    
    def process_chunks_batch(self, chunks: list, callback=None, system_prompt: str = None, max_workers: int = 3, save_batch_id=None) -> list:
        """Processa chunks em paralelo (máx 3 simultâneos para não sobrecarregar)"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        requests = self.create_batch_requests(chunks, system_prompt=system_prompt)
        results = []
        
        print(f"📤 Processando {len(requests)} chunks em paralelo (máx {max_workers} simultâneos)...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.process_chunk, req): req for req in requests}
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1
                print(f"   ✅ {completed}/{len(requests)} chunks processados")
        
        if callback:
            callback("kimi_batch", "completed")
        
        return results


class LLMProvider:
    """Factory para criar LLMs baseado no modelo escolhido"""
    
    SUPPORTED_MODELS = ["claude", "openai", "kimi", "deepseek"]
    
    @staticmethod
    def get_llm(model: str):
        """
        Retorna o LLM baseado no modelo escolhido.
        
        Args:
            model: 'claude', 'openai', 'kimi' ou 'deepseek'
        """
        model = model.lower()
        
        if model == "claude":
            return ChatAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model="claude-haiku-4-5-20251001",
                temperature=0
            )
        elif model == "openai":
            return ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4o",
                temperature=0
            )
        elif model == "kimi":
            api_key = os.getenv("MOONSHOT_API_KEY")
            if not api_key:
                raise ValueError("MOONSHOT_API_KEY não configurada")
            return ChatOpenAI(
                api_key=api_key,
                model="kimi-k2-thinking-turbo",
                base_url="https://api.moonshot.ai/v1",
                temperature=0.3,
                timeout=300.0,
                max_retries=3
            )
        elif model == "deepseek":
            # DeepSeek via LM Studio (local)
            lm_studio_url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
            return ChatOpenAI(
                api_key="not-needed",  # LM Studio não requer API key
                model="deepseek-r1-0528-qwen3-8b",  # Ajuste conforme o modelo carregado no LM Studio
                base_url=lm_studio_url,
                temperature=0
            )
        else:
            raise ValueError(f"Modelo '{model}' não suportado. Use: {LLMProvider.SUPPORTED_MODELS}")
    
    @staticmethod
    def get_graph_transformer(model: str):
        """
        Retorna LLMGraphTransformer configurado com o modelo escolhido.
        """
        from langchain_core.prompts import PromptTemplate
        
        llm = LLMProvider.get_llm(model)
        
        # Prompt customizado para garantir formato correto
        system_prompt = """You are an expert at extracting information and building knowledge graphs.
Extract all entities and relationships from the text. Return a valid JSON with this exact structure:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "brief description"}}
  ],
  "relationships": [
    {"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "properties": {"description": "brief description"}}
  ]
}

IMPORTANT:
- Every node MUST have an "id", "type", and "properties" field
- The "type" field is REQUIRED and should be a single word (e.g., Person, Organization, Location, Concept)
- Every relationship MUST have "source", "target", "type", and "properties" fields
- Return ONLY valid JSON, no markdown, no extra text
- If no entities found, return {"nodes": [], "relationships": []}"""
        
        return LLMGraphTransformer(
            llm=llm,
            node_properties=["description"],
            relationship_properties=["description"],
            system_prompt=system_prompt
        )
    
    @staticmethod
    def validate_model(model: str) -> bool:
        """Valida se o modelo é suportado"""
        return model.lower() in LLMProvider.SUPPORTED_MODELS
    
    @staticmethod
    def get_batch_processor(model: str = "claude"):
        """Retorna processador de batch para Claude"""
        if model.lower() != "claude":
            raise ValueError("Batch processing só suportado para Claude")
        return ClaudeBatchProcessor()
