# Environment Variables Documentation

This document outlines all environment variables used by the ArangoDB MCP Server with ChromaDB semantic search integration.

## ArangoDB Configuration

### Required Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ARANGO_URL` | ArangoDB server URL | `http://localhost:8529` | `http://localhost:8529` |
| `ARANGO_DB` | Database name | `_system` | `news_database` |
| `ARANGO_USERNAME` | Database username | `root` | `admin` |
| `ARANGO_PASSWORD` | Database password | `password` | `your_secure_password` |

## ChromaDB Configuration

### Primary Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CHROMA_MODE` | ChromaDB mode: `embedded` or `server` | `embedded` | `embedded`, `server` |
| `CHROMA_URL` or `CHROMADB_URL` | ChromaDB server URL (server mode only) | `http://localhost:8000` | `http://localhost:8000` |
| `CHROMA_DATA_PATH` | Local data directory (embedded mode only) | `./chroma_data` | `./data/chroma` |
| `CHROMA_COLLECTION_NAME` or `CHROMADB_COLLECTION` | Collection name for entity embeddings | `entity_embeddings` | `news_entities` |
| `CHROMA_EMBEDDING_FUNCTION` | Embedding function to use | `ollama` | `ollama`, `nomic`, `openai`, or `default` |

### Ollama Integration (Default & Recommended)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OLLAMA_URL` | Ollama server URL | `http://localhost:11434` | `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL` | Ollama embedding model | `nomic-embed-text` | `nomic-embed-text`, `all-minilm` |

> **Note**: Ollama integration is now the default. It provides local embeddings without external API dependencies.

### Nomic Embed Text Configuration (Default & Recommended)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `NOMIC_API_KEY` | Nomic API key for embeddings (optional for local models) | _(empty)_ | `nk-...` |

> **Note**: Nomic Embed Text is now the default embedding function. It provides high-quality embeddings and can work both with API keys (hosted) or locally installed models.

### OpenAI Integration (Legacy Option)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings | _(empty)_ | `sk-...` |
| `OPENAI_EMBEDDING_MODEL` or `CHROMA_EMBEDDING_MODEL` | OpenAI embedding model | `text-embedding-3-small` | `text-embedding-ada-002` |

### Performance Tuning (Optional)

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `CHROMA_MAX_RETRIES` | Maximum retry attempts for failed requests | `3` | `5` |
| `CHROMA_TIMEOUT` | Request timeout in milliseconds | `30000` | `60000` |

## Environment Setup Examples

### Local Development (.env file)

```bash
# ArangoDB Configuration
ARANGO_URL=http://localhost:8529
ARANGO_DB=news_database
ARANGO_USERNAME=root
ARANGO_PASSWORD=your_password

# ChromaDB Configuration (Embedded Mode with Ollama)
CHROMA_MODE=embedded
CHROMA_DATA_PATH=./chroma_data
CHROMA_COLLECTION_NAME=entity_embeddings
CHROMA_EMBEDDING_FUNCTION=ollama

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Performance Tuning
CHROMA_MAX_RETRIES=3
CHROMA_TIMEOUT=30000
```

### Server Mode with Ollama (.env file)

```bash
# ArangoDB Configuration
ARANGO_URL=http://localhost:8529
ARANGO_DB=news_database
ARANGO_USERNAME=root
ARANGO_PASSWORD=your_password

# ChromaDB Configuration (Server Mode)
CHROMA_MODE=server
CHROMA_URL=http://localhost:8000
CHROMA_COLLECTION_NAME=entity_embeddings
CHROMA_EMBEDDING_FUNCTION=ollama

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# Performance Tuning
CHROMA_MAX_RETRIES=3
CHROMA_TIMEOUT=30000
```

### Legacy OpenAI Configuration (.env file)

```bash
# ArangoDB Configuration
ARANGO_URL=http://localhost:8529
ARANGO_DB=news_database
ARANGO_USERNAME=root
ARANGO_PASSWORD=your_password

# ChromaDB Configuration with OpenAI (Legacy)
CHROMA_MODE=embedded
CHROMA_DATA_PATH=./chroma_data
CHROMA_COLLECTION_NAME=entity_embeddings
CHROMA_EMBEDDING_FUNCTION=openai

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Performance Tuning
CHROMA_MAX_RETRIES=3
CHROMA_TIMEOUT=30000
```

### Docker Environment

```bash
# ArangoDB Configuration
ARANGO_URL=http://arangodb:8529
ARANGO_DB=production_news
ARANGO_USERNAME=mcpuser
ARANGO_PASSWORD=secure_production_password

# ChromaDB Configuration
CHROMA_URL=http://chromadb:8000
CHROMA_COLLECTION_NAME=production_entities

# OpenAI Integration
OPENAI_API_KEY=sk-production-api-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Performance Tuning
CHROMA_MAX_RETRIES=5
CHROMA_TIMEOUT=45000
```

### Production Environment

```bash
# ArangoDB Configuration
ARANGO_URL=https://your-arangodb-cluster.com:8529
ARANGO_DB=production_news
ARANGO_USERNAME=production_user
ARANGO_PASSWORD=ultra_secure_password

# ChromaDB Configuration
CHROMA_URL=https://your-chromadb-cluster.com:8000
CHROMA_COLLECTION_NAME=production_news_entities

# OpenAI Integration
OPENAI_API_KEY=sk-production-openai-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Performance Tuning
CHROMA_MAX_RETRIES=5
CHROMA_TIMEOUT=60000
```

## Configuration Priority

The system uses the following priority order for configuration:

1. **Constructor parameters** (highest priority)
2. **Environment variables**
3. **Default values** (lowest priority)

## ChromaDB Setup Notes

### Default Embedding Function

If no `OPENAI_API_KEY` is provided, ChromaDB will use its default embedding function. This is suitable for:
- Development and testing
- Basic semantic similarity search
- Scenarios where OpenAI integration is not required

### OpenAI Embedding Function

When `OPENAI_API_KEY` is provided, the system will:
- Use OpenAI's embedding models for semantic search
- Provide higher quality semantic similarity results
- Support more advanced natural language queries

### Supported OpenAI Models

| Model | Description | Use Case |
|-------|-------------|----------|
| `text-embedding-3-small` | Fast, cost-effective (default) | General purpose |
| `text-embedding-3-large` | High performance | Production environments |
| `text-embedding-ada-002` | Legacy model | Compatibility |

## Troubleshooting

### Common Issues

1. **ChromaDB Connection Failed**
   - Check `CHROMA_URL` is correct and accessible
   - Verify ChromaDB server is running
   - Check firewall/network settings

2. **Collection Not Found**
   - The system will automatically create collections
   - Ensure `CHROMA_COLLECTION_NAME` is valid
   - Check ChromaDB server permissions

3. **OpenAI API Errors**
   - Verify `OPENAI_API_KEY` is valid and has credits
   - Check `OPENAI_EMBEDDING_MODEL` is supported
   - Monitor API rate limits

### Health Check

Use the semantic tool's health check feature:

```javascript
// The ChromaDB service includes health check functionality
const healthStatus = await chromaService.healthCheck();
console.log('ChromaDB Status:', healthStatus);
```

## Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive configuration
3. **Rotate API keys** regularly in production
4. **Use HTTPS** for production URLs
5. **Implement proper access controls** for database connections

## New Semantic Tool

The new `get_semantic_entity_articles` tool uses these environment variables to:

1. **Connect to ChromaDB** using `CHROMA_URL`
2. **Search embeddings** in the specified collection
3. **Use OpenAI embeddings** (if configured) for better results
4. **Perform graph traversal** in ArangoDB to find related articles
5. **Return comprehensive results** with semantic similarity scores

### Tool Parameters

- `searchQuery` (required): Natural language query
- `nResults` (optional): Number of similar entities to find (default: 10)
- `graphDepth` (optional): Graph traversal depth (default: 2)
- `maxArticles` (optional): Maximum articles to return (default: 50)
- `categoryFilter` (optional): Filter by article category
- `timeWindow` (optional): Time-based filtering
- `minSimilarity` (optional): Minimum similarity threshold (default: 0.5)
- `includeEntityMetadata` (optional): Include entity metadata (default: true)
