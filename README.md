# GraphRAG Agent

Multi-tenant GraphRAG agent with LangChain & LangGraph.

## Features

- 🔐 **Multi-tenancy** - Tenant isolation via JWT, RLS policies, and bucket-per-tenant
- 🧠 **GraphRAG** - Knowledge graph + vector retrieval for enhanced RAG
- ⚡ **Groq LLM** - Fast inference with Llama, Mixtral, and more
- 🔒 **OAuth 2.0** - Google and GitHub authentication
- 📄 **Document Processing** - PDF, TXT, MD, HTML, CSV, JSON support

## Quick Start

### 1. Clone and Setup

```bash
# Clone repository
cd graphrag_agent

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
# Required: GROQ_API_KEY, NEO4J_PASSWORD, JWT_SECRET
```

### 2. Start Services

```bash
# Start all services with Docker
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### 3. Run Migrations

```bash
# With Docker (automatic on startup)
# Or manually:
alembic upgrade head
```

## Development

### Local Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Start infrastructure only
docker-compose up neo4j postgres minio -d

# Run the API locally
uvicorn src.main:app --reload
```

### Project Structure

```
graphrag_agent/
├── config/
│   └── models.yaml          # LLM/embedding model configuration
├── docker/
│   └── Dockerfile
├── migrations/
│   ├── env.py
│   └── versions/
├── src/
│   ├── api/                  # FastAPI routes
│   │   ├── admin_routes.py
│   │   └── auth_routes.py
│   ├── auth/                 # Authentication
│   │   ├── dependencies.py
│   │   ├── jwt.py
│   │   └── providers/
│   ├── core/                 # Core utilities
│   │   └── tenant.py
│   ├── db/                   # Database models
│   │   ├── models.py
│   │   └── session.py
│   ├── llm/                  # LLM adapters
│   │   └── model_registry.py
│   ├── config.py
│   └── main.py
├── tests/
├── .env.example
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/login/{provider}` | GET | Start OAuth flow |
| `/auth/callback/{provider}` | GET | OAuth callback |
| `/auth/providers` | GET | List OAuth providers |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key |
| `NEO4J_PASSWORD` | Yes | Neo4j password |
| `JWT_SECRET` | Yes | JWT signing secret |
| `DATABASE_URL` | No | PostgreSQL connection URL |
| `MINIO_ACCESS_KEY` | No | MinIO access key |
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GITHUB_CLIENT_ID` | No | GitHub OAuth client ID |

### Model Selection

Models are configured in `config/models.yaml`. Available models:

- **LLMs**: Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B, Gemma 2 9B, DeepSeek R1
- **Embeddings**: MiniLM L6 v2, BGE Small, BGE Large

## License

MIT
