"""
Celery Worker para processamento de documentos em background.
Usa Redis como broker.

Para iniciar o worker:
    python -m celery -A celery_worker worker --loglevel=info --pool=solo
"""

import os
import hashlib
from dotenv import load_dotenv
load_dotenv()

from celery import Celery
from neo4j import GraphDatabase

from langchain_text_splitters import TokenTextSplitter
from langchain_core.documents import Document as LCDocument
# Removido PyMuPDFLoader - agora usa FileProcessor

from llama_index.core import Settings
from llama_index.embeddings.openai import OpenAIEmbedding

from llm_providers import LLMProvider
from neo4j_store import CustomNeo4jVectorStore

# Configurar Redis
from urllib.parse import quote

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Se a URL tem caracteres especiais na senha, fazer URL encoding
if "@" in redis_url and "://" in redis_url:
    protocol, rest = redis_url.split("://", 1)
    if "@" in rest:
        auth, host = rest.rsplit("@", 1)
        user, password = auth.split(":", 1)
        password_encoded = quote(password, safe='')
        redis_url = f"{protocol}://{user}:{password_encoded}@{host}"

REDIS_URL = redis_url

# Criar app Celery
celery_app = Celery(
    "graphrag_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Sao_Paulo',
    enable_utc=True,
)

# Embeddings serão configurados dinamicamente baseado no modelo escolhido


def get_neo4j_driver():
    """Cria conexão com Neo4j"""
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )


def update_progress(driver, document_id: str, progress: float, status: str = None, error: str = None):
    """Atualiza progresso do processamento no Neo4j"""
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    with driver.session(database=database) as session:
        query = """
            MATCH (d:Document {id: $document_id})
            SET d.processingProgress = $progress,
                d.updatedAt = datetime()
        """
        params = {"document_id": document_id, "progress": progress}
        
        if status:
            query = query.replace("d.updatedAt", f"d.status = $status, d.updatedAt")
            params["status"] = status
        
        if error:
            query = query.replace("d.updatedAt", f"d.processingError = $error, d.updatedAt")
            params["error"] = error
        
        session.run(query, **params)


@celery_app.task(bind=True)
def process_document_task(self, document_id: str, file_path: str, model: str = None, extraction_prompt: str = None):
    """
    Task Celery para processar documento em background.
    
    Etapas:
    1. Chunking (0-20%)
    2. Extração de Grafo (20-80%)
    3. Embeddings (80-95%)
    4. Finalização (95-100%)
    """
    # Usar modelo padrão se não especificado
    if not model:
        model = os.getenv("DEFAULT_MODEL", "deepseek")
    
    driver = get_neo4j_driver()
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    try:
        # Validar modelo
        if not LLMProvider.validate_model(model):
            raise ValueError(f"Modelo '{model}' não suportado. Use: {LLMProvider.SUPPORTED_MODELS}")
        
        print(f"🚀 Iniciando processamento: {document_id} com modelo {model}")
        update_progress(driver, document_id, 0, "Processing")
        
        # ============================================
        # VALIDAÇÃO: Testar conexão com LLM
        # ============================================
        print(f"🔍 Validando conexão com LLM ({model})...")
        try:
            llm = LLMProvider.get_llm(model)
            from langchain_core.messages import HumanMessage
            test_response = llm.invoke([HumanMessage(content="Responda apenas 'OK'")])
            test_result = test_response.content if hasattr(test_response, 'content') else str(test_response)
            if not test_result or len(test_result) < 1:
                raise ValueError("LLM não retornou resposta válida")
            print(f"   ✅ LLM respondendo: {test_result[:50]}...")
        except Exception as llm_error:
            error_msg = f"❌ Falha ao conectar com LLM ({model}): {str(llm_error)}"
            print(error_msg)
            update_progress(driver, document_id, 0, "Error", error=error_msg)
            raise ValueError(error_msg)
        
        # ============================================
        # ETAPA 1: Carregar e criar chunks (0-20%)
        # ============================================
        print("📦 Etapa 1: Carregando documento e criando chunks...")
        update_progress(driver, document_id, 5)
        
        # Verificar se arquivo existe localmente (Fallback para download HTTP se volumes não estiverem compartilhados)
        if not os.path.exists(file_path):
            print(f"⚠️ Arquivo não encontrado localmente: {file_path}")
            print(f"🔄 Tentando baixar da API interna...")
            
            try:
                import requests
                filename = os.path.basename(file_path)
                # Tenta adivinhar URL interna ou usa env var
                api_url = os.getenv("API_INTERNAL_URL", "http://app-ragapi:8000")
                download_url = f"{api_url}/uploads/{filename}"
                
                print(f"   ⬇️ Baixando de: {download_url}")
                response = requests.get(download_url, stream=True, timeout=30)
                
                if response.status_code == 200:
                    # Garantir diretório
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"   ✅ Arquivo baixado com sucesso!")
                else:
                    print(f"   ❌ Falha ao baixar arquivo: Status {response.status_code}")
                    # Se falhar, tenta localhost (caso worker e api estejam na mesma rede host - raro em docker, mas possível)
                    if "app-ragapi" in api_url:
                        fallback_url = f"http://localhost:8000/uploads/{filename}"
                        print(f"   🔄 Tentando fallback localhost: {fallback_url}")
                        response = requests.get(fallback_url, stream=True, timeout=10)
                        if response.status_code == 200:
                            with open(file_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            print(f"   ✅ Arquivo baixado via localhost!")
            except Exception as e:
                print(f"   ❌ Erro ao tentar baixar arquivo: {str(e)}")

        # Carregar documento (suporta múltiplos formatos)
        from file_processor import FileProcessor
        
        if not FileProcessor.is_supported(file_path):
            raise ValueError(f"Tipo de arquivo não suportado: {file_path}")
        
        # Extrair texto do arquivo
        text_content = FileProcessor.extract_text(file_path)
        
        # ============================================
        # LIMPEZA: Remover dados antigos (reprocessamento)
        # ============================================
        print("🧹 Limpando dados anteriores do documento...")
        with driver.session(database=database) as session:
            # Remover entidades e relacionamentos conectados ao documento
            session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                OPTIONAL MATCH (c)-[r1]->(e)
                OPTIONAL MATCH (e)-[r2]-()
                DELETE r1, r2
            """, document_id=document_id)
            
            # Remover entidades órfãs conectadas aos chunks
            session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)-[r]->(e)
                DELETE r, e
            """, document_id=document_id)
            
            # Remover chunks
            session.run("""
                MATCH (d:Document {id: $document_id})<-[:PART_OF]-(c:Chunk)
                DETACH DELETE c
            """, document_id=document_id)
            
            # Resetar contadores do documento (NÃO resetar batchId/batchStatus/total_chunks para reuso de 24h)
            session.run("""
                MATCH (d:Document {id: $document_id})
                SET d.entityNodeCount = 0,
                    d.entityEntityRelCount = 0,
                    d.summary = null
            """, document_id=document_id)
        print("   ✅ Dados anteriores removidos")
        
        # Criar documento LangChain
        pages = [LCDocument(
            page_content=text_content,
            metadata={'source': file_path, 'file_type': FileProcessor.get_file_type(file_path)}
        )]
        
        update_progress(driver, document_id, 10)
        
        # Configuração de chunking
        token_chunk_size = int(os.getenv('TOKEN_CHUNK_SIZE', 130))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 15))
        MAX_TOKEN_CHUNK_SIZE = int(os.getenv('MAX_TOKEN_CHUNK_SIZE', 10000))
        chunk_to_be_created = int(MAX_TOKEN_CHUNK_SIZE / token_chunk_size)
        
        text_splitter = TokenTextSplitter(
            chunk_size=token_chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Criar chunks
        chunks = []
        for i, document in enumerate(pages):
            page_number = i + 1
            if len(chunks) >= chunk_to_be_created:
                break
            page_chunks = text_splitter.split_documents([document])
            for chunk in page_chunks:
                if len(chunks) >= chunk_to_be_created:
                    break
                chunk_position = len(chunks) + 1
                new_chunk = LCDocument(
                    page_content=chunk.page_content,
                    metadata={'page_number': page_number, 'chunk_position': chunk_position}
                )
                chunks.append(new_chunk)
        
        print(f"   ✅ {len(chunks)} chunks criados")
        update_progress(driver, document_id, 20)
        
        # ============================================
        # ETAPA 2: Extração de Grafo com LLM (20-80%)
        # ============================================
        print(f"🕸️ Etapa 2: Extraindo grafo com {model}...")
        
        # Analisar tamanho dos chunks
        chunk_sizes = [len(chunk.page_content) for chunk in chunks]
        avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        max_chunk_size = max(chunk_sizes) if chunk_sizes else 0
        min_chunk_size = min(chunk_sizes) if chunk_sizes else 0
        
        print(f"   📊 Análise de chunks:")
        print(f"      - Total: {len(chunks)} chunks")
        print(f"      - Tamanho médio: {avg_chunk_size:.0f} caracteres")
        print(f"      - Tamanho máximo: {max_chunk_size} caracteres")
        print(f"      - Tamanho mínimo: {min_chunk_size} caracteres")
        
        graph_documents = []
        total_chunks = len(chunks)
        failed_chunks = []
        
        # Usar Batch API para Claude, OpenAI ou Kimi
        if model.lower() in ["claude", "openai", "kimi"]:
            if model.lower() == "claude":
                print(f"   🚀 Usando Batch API do Claude (50% mais barato)...")
                from llm_providers import ClaudeBatchProcessor as BatchProcessor
            elif model.lower() == "openai":
                print(f"   🚀 Usando Batch API do OpenAI (50% mais barato)...")
                from llm_providers import OpenAIBatchProcessor as BatchProcessor
            else:
                print(f"   🚀 Usando processamento paralelo do Kimi (máx 3 simultâneos)...")
                from llm_providers import KimiBatchProcessor as BatchProcessor
            
            def batch_callback(batch_id, status):
                """Callback quando batch termina"""
                if status == "completed":
                    print(f"   📢 Batch {batch_id} completado!")
                    with driver.session(database=database) as session:
                        session.run("""
                            MATCH (d:Document {id: $document_id})
                            SET d.batchId = $batch_id,
                                d.batchStatus = 'completed',
                                d.batchCompletedAt = datetime()
                        """, document_id=document_id, batch_id=batch_id)
                elif status == "timeout":
                    print(f"   ⚠️ Batch {batch_id} expirou!")
                    with driver.session(database=database) as session:
                        session.run("""
                            MATCH (d:Document {id: $document_id})
                            SET d.batchStatus = 'timeout'
                        """, document_id=document_id)
            
            processor = BatchProcessor()
            
            # Verificar se já existe batch que pode ser reutilizado
            with driver.session(database=database) as session:
                result = session.run("""
                    MATCH (d:Document {id: $document_id})
                    RETURN d.batchId as batchId, 
                           d.batchStatus as batchStatus, 
                           d.batchCompletedAt as batchCompletedAt,
                           d.total_chunks as previousChunks
                """, document_id=document_id)
                record = result.single()
                existing_batch_id = record["batchId"] if record and record["batchId"] else None
                existing_batch_status = record["batchStatus"] if record and record["batchStatus"] else None
                batch_completed_at = record["batchCompletedAt"] if record else None
                previous_chunks = record["previousChunks"] if record else None
            
            # Verificar se batch pode ser reutilizado:
            # 1. Batch existe
            # 2. Foi completado há menos de 24 horas OU ainda está em processamento
            # 3. Mesmo número de chunks (documento não mudou)
            can_reuse_batch = False
            if existing_batch_id:
                if existing_batch_status in ['processing', 'in_progress', 'validating']:
                    # Batch ainda em andamento
                    can_reuse_batch = True
                    print(f"   🔄 Batch anterior ainda em processamento: {existing_batch_id}")
                elif existing_batch_status == 'completed' and batch_completed_at:
                    # Verificar se foi há menos de 24h
                    from datetime import datetime, timedelta, timezone
                    try:
                        # batch_completed_at vem como string do Neo4j
                        if isinstance(batch_completed_at, str):
                            completed_time = datetime.fromisoformat(batch_completed_at.replace('Z', '+00:00'))
                        else:
                            completed_time = batch_completed_at.to_native()
                        
                        hours_since = (datetime.now(timezone.utc) - completed_time).total_seconds() / 3600
                        if hours_since < 24 and previous_chunks == total_chunks:
                            can_reuse_batch = True
                            print(f"   🔄 Batch completado há {hours_since:.1f}h (< 24h), reutilizando: {existing_batch_id}")
                        elif hours_since >= 24:
                            print(f"   ⏰ Batch expirado ({hours_since:.1f}h > 24h), criando novo...")
                        elif previous_chunks != total_chunks:
                            print(f"   📄 Documento mudou ({previous_chunks} → {total_chunks} chunks), criando novo batch...")
                    except Exception as e:
                        print(f"   ⚠️ Erro ao verificar data do batch: {e}")
            
            # Tentar recuperar batch existente
            if can_reuse_batch and existing_batch_id:
                print(f"   🔄 Recuperando batch: {existing_batch_id}")
                try:
                    batch_results = processor.recover_batch(existing_batch_id, callback=batch_callback)
                    print(f"   ✅ Batch recuperado com sucesso!")
                except Exception as e:
                    print(f"   ⚠️ Não foi possível recuperar batch: {str(e)[:100]}")
                    print(f"   🆕 Criando novo batch...")
                    can_reuse_batch = False
            
            # Criar novo batch se necessário
            if not can_reuse_batch or not existing_batch_id:
                def save_batch_id(bid):
                    with driver.session(database=database) as s:
                        s.run("""
                            MATCH (d:Document {id: $document_id})
                            SET d.batchId = $batch_id, 
                                d.batchStatus = 'processing',
                                d.batchStartedAt = datetime()
                        """, document_id=document_id, batch_id=bid)
                
                batch_results = processor.process_chunks_batch(
                    chunks, 
                    callback=batch_callback, 
                    system_prompt=extraction_prompt,
                    save_batch_id=save_batch_id
                )
            
            # Processar resultados do batch
            for result in batch_results:
                chunk_num = int(result['chunk_id'].split('_')[1]) + 1
                
                if result['status'] in ['success', 'parse_error']:
                    data = result.get('data', {})
                    
                    # Armazenar dados do grafo para processar depois
                    graph_documents.append({
                        'nodes': data.get('nodes', []),
                        'relationships': data.get('relationships', [])
                    })
                    
                    progress = 20 + (60 * chunk_num / total_chunks)
                    update_progress(driver, document_id, progress)
                    
                    if result['status'] == 'success':
                        print(f"   ✅ Chunk {chunk_num}/{total_chunks} processado ({progress:.1f}%)")
                    else:
                        print(f"   ⚠️ Chunk {chunk_num}/{total_chunks} com erro de parse, continuando ({progress:.1f}%)")
                else:
                    print(f"   ❌ Chunk {chunk_num}/{total_chunks} falhou: {result.get('error', 'Unknown')}")
                    failed_chunks.append((chunk_num, result.get('error', 'Unknown')))
        else:
            # Usar LLMGraphTransformer para outros modelos
            llm_transformer = LLMProvider.get_graph_transformer(model)
            
            # Processar chunks com LLMGraphTransformer (para modelos que não usam Batch)
            for i, chunk in enumerate(chunks):
                try:
                    # Processar cada chunk com timeout
                    docs = llm_transformer.convert_to_graph_documents([chunk])
                    graph_documents.extend(docs)
                    
                    # Atualizar progresso (20-80% = 60% range)
                    progress = 20 + (60 * (i + 1) / total_chunks)
                    update_progress(driver, document_id, progress)
                    print(f"   ✅ Chunk {i+1}/{total_chunks} processado ({progress:.1f}%)")
                    
                except Exception as e:
                    error_msg = str(e)[:150]
                    print(f"   ⚠️ Chunk {i+1}/{total_chunks} falhou: {error_msg}")
                    failed_chunks.append((i, error_msg))
                    
                    # Tentar novamente com chunk menor (split em 2)
                    if len(chunk.page_content) > 500:
                        try:
                            print(f"      🔄 Tentando com chunk dividido...")
                            mid = len(chunk.page_content) // 2
                            chunk1 = LCDocument(
                                page_content=chunk.page_content[:mid],
                                metadata=chunk.metadata
                            )
                            chunk2 = LCDocument(
                                page_content=chunk.page_content[mid:],
                                metadata=chunk.metadata
                            )
                            docs1 = llm_transformer.convert_to_graph_documents([chunk1])
                            docs2 = llm_transformer.convert_to_graph_documents([chunk2])
                            graph_documents.extend(docs1)
                            graph_documents.extend(docs2)
                            print(f"      ✅ Chunk dividido processado com sucesso")
                            failed_chunks.pop()  # Remove do registro de falhas
                        except Exception as e2:
                            print(f"      ❌ Chunk dividido também falhou: {str(e2)[:100]}")
                    
                    # Continuar com próximo chunk
                    progress = 20 + (60 * (i + 1) / total_chunks)
                    update_progress(driver, document_id, progress)
        
        print(f"   ✅ {len(graph_documents)} graph documents gerados")
        if failed_chunks:
            print(f"   ⚠️ {len(failed_chunks)} chunks falharam (continuando...)")
        
        # Contar quantas entidades foram realmente extraídas
        total_nodes_extracted = 0
        for graph_doc in graph_documents:
            if isinstance(graph_doc, dict):
                total_nodes_extracted += len(graph_doc.get('nodes', []))
            else:
                total_nodes_extracted += len(graph_doc.nodes) if hasattr(graph_doc, 'nodes') else 0
        
        print(f"   📊 Total de entidades extraídas: {total_nodes_extracted}")
        
        # Verificar se TODOS os chunks falharam OU se nenhuma entidade foi extraída
        if len(failed_chunks) == total_chunks or len(graph_documents) == 0 or total_nodes_extracted == 0:
            error_msg = f"Extração de entidades falhou. "
            if total_nodes_extracted == 0 and len(graph_documents) > 0:
                error_msg += f"Foram processados {len(graph_documents)} chunks mas nenhuma entidade foi extraída."
            else:
                error_msg += f"Todos os {total_chunks} chunks falharam."
            if failed_chunks:
                # Pegar o primeiro erro como exemplo
                first_error = failed_chunks[0][1] if len(failed_chunks[0]) > 1 else "Erro desconhecido"
                error_msg += f" Erro: {first_error[:200]}"
            print(f"   ❌ {error_msg}")
            update_progress(driver, document_id, 0, "Failed", error_msg)
            driver.close()
            return {
                "document_id": document_id,
                "status": "Failed",
                "error": error_msg,
                "chunks": len(chunks),
                "entities": 0,
                "relationships": 0
            }
        
        # ============================================
        # ETAPA 3: Salvar no Neo4j (80-95%)
        # ============================================
        print("💾 Etapa 3: Salvando no Neo4j...")
        update_progress(driver, document_id, 82)
        
        with driver.session(database=database) as session:
            # Obter filename do documento
            result = session.run("""
                MATCH (d:Document {id: $document_id})
                RETURN d.fileName as fileName
            """, document_id=document_id)
            record = result.single()
            filename = record["fileName"] if record else document_id
            
            # Labels reservados
            RESERVED_LABELS = {'Document', 'Chunk', 'Session', 'Message'}
            
            # Salvar chunks
            chunk_id_list = []
            for i, chunk in enumerate(chunks):
                chunk_position = chunk.metadata.get('chunk_position', i + 1)
                content_with_position = f"{chunk_position}:{chunk.page_content}"
                chunk_id = hashlib.sha1(content_with_position.encode()).hexdigest()
                chunk_id_list.append(chunk_id)
                
                session.run("""
                    MATCH (d:Document {id: $document_id})
                    MERGE (c:Chunk {id: $chunk_id})
                    SET c.text = $text,
                        c.position = $position,
                        c.length = $length,
                        c.fileName = $filename,
                        c.page_number = $page_number
                    MERGE (c)-[:PART_OF]->(d)
                """, 
                    document_id=document_id,
                    chunk_id=chunk_id,
                    text=chunk.page_content,
                    position=chunk_position,
                    length=len(chunk.page_content),
                    filename=filename,
                    page_number=chunk.metadata.get('page_number', 1)
                )
                
                # FIRST_CHUNK e NEXT_CHUNK
                if i == 0:
                    session.run("""
                        MATCH (d:Document {id: $document_id})
                        MATCH (c:Chunk {id: $chunk_id})
                        MERGE (d)-[:FIRST_CHUNK]->(c)
                    """, document_id=document_id, chunk_id=chunk_id)
                
                if i > 0:
                    prev_chunk_id = chunk_id_list[i-1]
                    session.run("""
                        MATCH (prev:Chunk {id: $prev_id})
                        MATCH (curr:Chunk {id: $curr_id})
                        MERGE (prev)-[:NEXT_CHUNK]->(curr)
                    """, prev_id=prev_chunk_id, curr_id=chunk_id)
            
            update_progress(driver, document_id, 88)
            
            # Salvar entidades e relacionamentos
            entity_count = 0
            relationship_count = 0
            
            for i, graph_doc in enumerate(graph_documents):
                chunk_id = chunk_id_list[i] if i < len(chunk_id_list) else None
                
                # Verificar se é dict (do batch) ou objeto (do LLMGraphTransformer)
                if isinstance(graph_doc, dict):
                    nodes = graph_doc.get('nodes', [])
                    relationships = graph_doc.get('relationships', [])
                else:
                    nodes = graph_doc.nodes
                    relationships = graph_doc.relationships
                
                # Processar nós
                for node in nodes:
                    if isinstance(node, dict):
                        node_type = node.get('type', 'Entity')
                        node_id = node.get('id')
                        description = node.get('properties', {}).get('description', '')
                    else:
                        node_type = node.type if node.type else "Entity"
                        node_id = node.id
                        description = node.properties.get('description', '') if node.properties else ''
                    
                    if not node_id:
                        continue
                    
                    # Renomear tipos reservados
                    if node_type in RESERVED_LABELS:
                        node_type = f"{node_type}Entity"
                    
                    entity_count += 1
                    session.run(f"""
                        MERGE (e:`{node_type}`:__Entity__ {{id: $node_id}})
                        SET e.description = $description
                    """, node_id=node_id, description=description)
                    
                    if chunk_id:
                        session.run(f"""
                            MATCH (c:Chunk {{id: $chunk_id}})
                            MATCH (e:`{node_type}` {{id: $node_id}})
                            MERGE (c)-[:HAS_ENTITY]->(e)
                        """, chunk_id=chunk_id, node_id=node_id)
                
                # Processar relacionamentos
                for rel in relationships:
                    if isinstance(rel, dict):
                        source_id = rel.get('source')
                        target_id = rel.get('target')
                        rel_type = rel.get('type', 'RELATED_TO')
                    else:
                        source_id = rel.source.id
                        target_id = rel.target.id
                        rel_type = rel.type
                    
                    if not source_id or not target_id:
                        continue
                    
                    relationship_count += 1
                    rel_type = rel_type.upper().replace(" ", "_").replace("-", "_")
                    
                    session.run(f"""
                        MATCH (s:__Entity__ {{id: $source}})
                        MATCH (t:__Entity__ {{id: $target}})
                        MERGE (s)-[r:`{rel_type}`]->(t)
                    """, source=source_id, target=target_id)
            
            # Atualizar documento
            session.run("""
                MATCH (d:Document {id: $document_id})
                SET d.total_chunks = $chunk_count,
                    d.chunkNodeCount = $chunk_count,
                    d.entityNodeCount = $entity_count,
                    d.entityEntityRelCount = $rel_count
            """, document_id=document_id, chunk_count=len(chunks),
                entity_count=entity_count, rel_count=relationship_count)
        
        print(f"   ✅ Grafo salvo: {len(chunks)} chunks, {entity_count} entidades, {relationship_count} relacionamentos")
        update_progress(driver, document_id, 95)
        
        # ============================================
        # ETAPA 4: Embeddings (95-100%)
        # ============================================
        print("🔧 Etapa 4: Gerando embeddings...")
        
        # Usar embedding model (local por padrão, OpenAI se FORCE_OPENAI_EMBEDDINGS=true)
        from llama_index.core.schema import TextNode
        embed_model = LLMProvider.get_embedding_model(model)
        
        # Determinar dimensão do embedding baseado no modelo
        # OpenAI: 1536, all-MiniLM-L6-v2: 384, all-mpnet-base-v2: 768
        force_openai = os.getenv("FORCE_OPENAI_EMBEDDINGS", "").lower() == "true"
        if force_openai:
            embedding_dimension = 1536
        else:
            # Modelos locais - dimensão configurável
            embedding_dimension = int(os.getenv("LOCAL_EMBEDDING_DIMENSION", "384"))
        
        vector_store = CustomNeo4jVectorStore(
            username=os.getenv("NEO4J_USER"),
            password=os.getenv("NEO4J_PASSWORD"),
            url=os.getenv("NEO4J_URI"),
            embedding_dimension=embedding_dimension,
            database=database
        )
        
        llama_nodes = []
        for chunk in chunks:
            node = TextNode(text=chunk.page_content, metadata=chunk.metadata)
            node.embedding = embed_model.get_text_embedding(node.get_content())
            llama_nodes.append(node)
        
        # Log da dimensão real do embedding gerado
        if llama_nodes and llama_nodes[0].embedding:
            actual_dim = len(llama_nodes[0].embedding)
            print(f"   📊 Dimensão do embedding: {actual_dim} (esperado: {embedding_dimension})")
            if actual_dim != embedding_dimension:
                print(f"   ⚠️ ATENÇÃO: Dimensão não confere! Verifique LOCAL_EMBEDDING_DIMENSION no .env")
        
        vector_store.add(llama_nodes)
        
        print("   ✅ Embeddings salvos")
        
        # ============================================
        # ETAPA 5: Gerar Resumo (97-99%)
        # ============================================
        print("📝 Etapa 5: Gerando resumo do documento...")
        update_progress(driver, document_id, 97)
        
        try:
            # Juntar primeiros chunks para contexto (limite de tokens)
            context_text = "\n\n".join([c.page_content for c in chunks[:5]])[:8000]
            
            # Obter LLM para gerar resumo
            llm = LLMProvider.get_llm(model)
            
            summary_prompt = f"""Analise o seguinte conteúdo de documento e gere um resumo executivo conciso.

O resumo deve:
1. Ter no máximo 3 parágrafos
2. Destacar os pontos principais
3. Ser contextual e informativo
4. Estar em português

CONTEÚDO:
{context_text}

RESUMO:"""
            
            # Usar invoke() para LangChain chat models
            from langchain_core.messages import HumanMessage
            summary_response = llm.invoke([HumanMessage(content=summary_prompt)])
            document_summary = summary_response.content.strip()
            
            # Salvar resumo no documento
            with driver.session(database=database) as session:
                session.run("""
                    MATCH (d:Document {id: $document_id})
                    SET d.summary = $summary
                """, document_id=document_id, summary=document_summary)
            
            print(f"   ✅ Resumo gerado ({len(document_summary)} caracteres)")
        except Exception as e:
            print(f"   ⚠️ Erro ao gerar resumo: {str(e)}")
            document_summary = ""
        
        # ============================================
        # Finalização
        # ============================================
        update_progress(driver, document_id, 100, "Completed")
        print(f"✅ Processamento concluído: {document_id}")
        
        return {
            "document_id": document_id,
            "status": "Completed",
            "chunks": len(chunks),
            "entities": entity_count,
            "relationships": relationship_count
        }
        
    except Exception as e:
        print(f"❌ Erro no processamento: {str(e)}")
        update_progress(driver, document_id, 0, "Failed", str(e))
        raise
    finally:
        driver.close()
