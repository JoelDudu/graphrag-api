from typing import Any, List, Optional
from llama_index.core.vector_stores.types import (
    VectorStore,
    VectorStoreQuery,
    VectorStoreQueryResult,
)
from llama_index.core.schema import TextNode, BaseNode
from neo4j import GraphDatabase
import logging
import json
import hashlib

logger = logging.getLogger(__name__)

class CustomNeo4jVectorStore(VectorStore):
    stores_text: bool = True
    
    def __init__(
        self,
        username: str,
        password: str,
        url: str,
        embedding_dimension: int,
        index_name: str = "vector",  # Mesmo nome do llm-graph-builder
        node_label: str = "Chunk",   # Usar Chunk, não DocumentChunk
        database: str = "neo4j",
    ):
        self.driver = GraphDatabase.driver(url, auth=(username, password))
        self.embedding_dimension = embedding_dimension
        self.index_name = index_name
        self.node_label = node_label
        self.database = database
        
        # Criar índice vetorial se não existir
        self._create_index()

    def _create_index(self):
        query = f"""
        CREATE VECTOR INDEX {self.index_name} IF NOT EXISTS
        FOR (n:{self.node_label})
        ON (n.embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {self.embedding_dimension},
            `vector.similarity_function`: 'cosine'
        }}}}
        """
        with self.driver.session(database=self.database) as session:
            session.run(query)

    def add(
        self,
        nodes: List[BaseNode],
        **add_kwargs: Any,
    ) -> List[str]:
        """Adiciona embeddings aos Chunk nodes existentes (usando SHA1 do conteúdo + posição como ID)"""
        print(f"\n💾 VectorStore.add(): Salvando {len(nodes)} embeddings nos Chunk nodes...")
        ids = []
        updated_count = 0
        with self.driver.session(database=self.database) as session:
            for i, node in enumerate(nodes):
                embedding = node.get_embedding()
                if not embedding:
                    print(f"   ⚠️ Node {i+1}: sem embedding, pulando")
                    continue
                
                # Usar SHA1 do texto + posição como ID (igual ao save_to_neo4j)
                text_content = node.get_content()
                chunk_position = node.metadata.get('chunk_position', i + 1)
                content_with_position = f"{chunk_position}:{text_content}"
                chunk_id = hashlib.sha1(content_with_position.encode()).hexdigest()
                
                # Atualizar Chunk existente com embedding (não criar novo)
                result = session.run("""
                    MATCH (n:Chunk {id: $id})
                    SET n.embedding = $embedding
                    RETURN n.id as updated_id
                """,
                    id=chunk_id,
                    embedding=embedding
                )
                
                record = result.single()
                if record:
                    updated_count += 1
                    print(f"   ✅ Chunk {i+1} (ID={chunk_id[:8]}...): embedding salvo")
                else:
                    print(f"   ❌ Chunk {i+1} (ID={chunk_id[:8]}...): NÃO ENCONTRADO no Neo4j!")
                
                ids.append(chunk_id)
        
        print(f"📤 VectorStore.add() RESULTADO: {updated_count}/{len(nodes)} embeddings salvos")
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        # Implementação simplificada
        pass

    def query(
        self,
        query: VectorStoreQuery,
        **kwargs: Any,
    ) -> VectorStoreQueryResult:
        """Query Chunk nodes usando índice vetorial"""
        cypher_query = """
        CALL db.index.vector.queryNodes($index_name, $k, $embedding)
        YIELD node, score
        RETURN node.text as text, node.id as id, 
               node.position as position, node.page_number as page_number, 
               node.fileName as fileName, score
        """
        
        nodes = []
        similarities = []
        ids = []
        
        with self.driver.session(database=self.database) as session:
            result = session.run(
                cypher_query,
                index_name=self.index_name,
                k=query.similarity_top_k,
                embedding=query.query_embedding
            )
            
            for record in result:
                # Construir metadata a partir das propriedades do Chunk
                metadata = {
                    "position": record.get("position"),
                    "page_number": record.get("page_number"),
                    "fileName": record.get("fileName")
                }
                    
                node = TextNode(
                    text=record["text"] or "",
                    id_=record["id"],
                    metadata=metadata
                )
                nodes.append(node)
                similarities.append(record["score"])
                ids.append(record["id"])

        return VectorStoreQueryResult(
            nodes=nodes,
            similarities=similarities,
            ids=ids
        )

    @property
    def client(self) -> Any:
        return self.driver
