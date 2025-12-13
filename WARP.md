# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

GraphRAG API v3.1 is an asynchronous document processing API with knowledge graph extraction using LLMs. The system uses a multi-service architecture with FastAPI (backend), Next.js (frontend), Celery (async processing), Redis (message broker), and Neo4j (graph database + vector store).

## Common Commands

### Development Setup

**Backend:**
```powershell
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Frontend:**
```powershell
cd frontend

# Install dependencies (prefer pnpm)
pnpm install
# Or: npm install / yarn install
```

### Running Services Locally

You need 4 terminals for full local development:

**Terminal 1 - Redis:**
```powershell
redis-server
```

**Terminal 2 - Celery Worker:**
```powershell
python -m celery -A celery_worker worker --loglevel=info --pool=solo
```

**Terminal 3 - FastAPI Backend:**
```powershell
python graph_api_v3.py
```

**Terminal 4 - Next.js Frontend:**
```powershell
cd frontend
pnpm dev
```

### Docker Commands

```powershell
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Testing & Documentation

- **API Documentation (Swagger):** http://localhost:8000/docs
- **API Documentation (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health
- **Frontend:** http://localhost:3000

### Frontend Commands

```powershell
cd frontend

# Development
pnpm dev

# Production build
pnpm build
pnpm start

# Linting
pnpm lint
```

## Architecture

### High-Level Flow

1. **Upload Phase**: User uploads document → API validates format → Creates `Document` node in Neo4j with `status='Pending'`
2. **Processing Phase**: API submits async task to Celery → Worker processes in background → Creates `Chunk` nodes and graph entities
3. **Query Phase**: User queries → System performs semantic search (vector) and/or graph traversal → LLM generates response

### Service Responsibilities

**FastAPI Backend (`graph_api_v3.py`):**
- JWT authentication (via `auth.py`)
- REST API endpoints (upload, process, status, query)
- Document validation and initial Neo4j node creation
- Task delegation to Celery

**Celery Worker (`celery_worker.py`):**
- Async document processing (4 stages: chunking, graph extraction, embeddings, finalization)
- Uses batch APIs (Claude/OpenAI/Kimi) for 50% cost savings
- Updates processing progress in Neo4j
- Creates `Chunk` nodes and graph relationships

**Frontend (Next.js):**
- React components with Radix UI and Tailwind
- Document management UI
- Real-time processing status monitoring
- Query interface

### Key Components

**`llm_providers.py`:**
- Factory for multiple LLM providers (Claude, OpenAI, Kimi, DeepSeek)
- Batch processing classes (`ClaudeBatchProcessor`, `OpenAIBatchProcessor`, `KimiBatchProcessor`)
- Cost-optimized batch APIs

**`file_processor.py`:**
- Multi-format document parser (PDF, DOCX, XLSX, PPTX, TXT, CSV)
- Text extraction with format-specific handling

**`neo4j_store.py`:**
- Custom vector store implementation for LlamaIndex
- Manages embeddings on `Chunk` nodes
- Vector similarity search using Neo4j's vector index

**`extraction_prompts.py`:**
- Domain-specific extraction prompts (generic, legal, medical, technical, financial, aesthetics, health, IT)
- JSON schema enforcement for graph extraction

**`auth.py`:**
- JWT token generation and validation
- Simple user authentication (default users: admin/admin123, user/user123)
- **Security Note:** Uses in-memory user store - replace with real database in production

### Data Model

**Neo4j Schema:**
- `Document` nodes: Metadata, status, progress tracking
- `Chunk` nodes: Text chunks with embeddings, linked to Document
- Entity nodes: Extracted from text (Person, Organization, Concept, etc.)
- Relationships: RELATED_TO, MENTIONS, etc.

**Processing States:**
- `Pending`: Document uploaded, awaiting processing
- `Processing`: Celery worker active
- `Completed`: Processing finished successfully
- `Failed`: Error occurred (check `processingError` property)

### Environment Configuration

Critical environment variables (see `.env.example`):

**Neo4j:**
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`

**LLM APIs:**
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MOONSHOT_API_KEY`

**Redis:**
- `REDIS_URL` (must handle special characters in passwords - use URL encoding)

**JWT:**
- `JWT_SECRET_KEY` (MUST change in production)
- `JWT_EXPIRE_MINUTES` (default: 1440)

**Chunking:**
- `TOKEN_CHUNK_SIZE` (default: 130)
- `CHUNK_OVERLAP` (default: 15)
- `MAX_TOKEN_CHUNK_SIZE` (default: 10000)

**Model:**
- `DEFAULT_MODEL` (options: claude, openai, kimi, deepseek)

## Development Patterns

### Authentication

All endpoints except `/auth/login` and `/health` require JWT token in `Authorization: Bearer <token>` header.

### Async Processing

Never block the API waiting for document processing. Always use Celery tasks. The pattern:
1. Create initial state in Neo4j
2. Return `document_id` to client immediately
3. Submit background task
4. Client polls `/status/{document_id}` for updates

### LLM Model Selection

Choose model based on use case:
- **Claude (Haiku)**: Fast, cost-effective for graph extraction (default)
- **OpenAI**: Alternative for variety
- **Kimi**: Chinese language support
- **DeepSeek**: Local deployment via LM Studio

### Batch Processing

When processing multiple chunks, use batch APIs (`ClaudeBatchProcessor`, etc.) instead of individual API calls - saves 50% on costs and is more efficient.

### Error Handling

The Celery worker updates `Document.processingError` on failure. Always check this field when `status='Failed'`.

## File Structure

```
graphrag--API/
├── graph_api_v3.py          # Main FastAPI application
├── auth.py                  # JWT authentication
├── celery_worker.py         # Async task processor
├── llm_providers.py         # LLM provider factory + batch processors
├── file_processor.py        # Multi-format document parser
├── neo4j_store.py          # Custom vector store for Neo4j
├── extraction_prompts.py    # Domain-specific extraction prompts
├── requirements.txt         # Python dependencies
├── Dockerfile              # API container image
├── Dockerfile.worker       # Worker container image
├── docker-compose.yml      # Service orchestration
├── .env.example           # Environment template
├── uploads/               # Document storage (volume-mounted)
└── frontend/              # Next.js dashboard
    ├── app/               # Next.js 16 app directory
    ├── components/        # React components (Radix UI + Tailwind)
    ├── package.json       # Node dependencies
    └── .env.local         # Frontend environment (NEXT_PUBLIC_API_URL)
```

## Security Considerations

**Before deploying to production:**
1. Change `JWT_SECRET_KEY` to a strong random value
2. Replace in-memory user store in `auth.py` with real database
3. Update default passwords (admin123, user123)
4. Configure CORS for specific domains
5. Enable HTTPS
6. Implement rate limiting
7. Review Neo4j access controls

## Common Issues

**Celery worker not processing tasks:**
- Verify Redis is running and accessible
- Check `REDIS_URL` format (passwords with special chars need URL encoding)
- Ensure worker and API share same Redis instance
- Verify Docker volumes are properly mounted for `uploads/`

**Neo4j connection failures:**
- Confirm URI format: `neo4j://host:7687` or `neo4j+s://host:7687`
- Test credentials manually with Neo4j Browser
- Check network/firewall rules for port 7687

**Upload failures:**
- Verify file format is in `FileProcessor.SUPPORTED_EXTENSIONS`
- Check disk space and upload directory permissions
- Ensure `uploads/` directory exists and is writable

**Batch processing timeouts:**
- Claude/OpenAI batch APIs can take 10+ minutes for large documents
- Worker logs show progress updates every 10 seconds
- Check `Document.processingProgress` for current status
