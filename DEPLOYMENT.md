# Deployment Guide

This guide explains how to deploy the ArangoDB MCP Server with its separate ChromaDB and Ollama services.

## Architecture

The system consists of three main components:

1. **MCP Server**: Node.js server that handles MCP protocol and ArangoDB operations
2. **ChromaDB Server**: Python Flask server that manages embeddings and vector search
3. **Ollama**: Local LLM service for generating embeddings

## Prerequisites

- Docker and Docker Compose
- 4GB RAM minimum (8GB recommended)
- 10GB disk space for container images and data

## Quick Start

### On the Source Machine

1. **Build and package:**
   ```bash
   # Make deploy script executable
   chmod +x deploy.sh
   
   # Run deploy script
   ./deploy.sh
   ```

2. **Transfer files:**
   - Copy the generated `deploy.tar.gz` to the target machine

### On the Target Machine

1. **Extract deployment package:**
   ```bash
   tar -xzf deploy.tar.gz
   ```

2. **Load Docker images:**
   ```bash
   docker load -i mcp-server.tar
   docker load -i chroma-server.tar
   ```

3. **Start services:**
   ```bash
   docker compose up -d
   ```

4. **Verify deployment:**
   ```bash
   # Check service status
   docker compose ps
   
   # Check logs
   docker compose logs
   
   # Test endpoints
   curl http://localhost:3000/health    # MCP Server
   curl http://localhost:5002/health    # ChromaDB Server
   curl http://localhost:11434/api/tags # Ollama
   ```

## Environment Variables

### MCP Server (docker-compose.yml)
```yaml
environment:
  - ARANGO_URL=your_arango_url
  - ARANGO_DB=your_database
  - ARANGO_USERNAME=your_username
  - ARANGO_PASSWORD=your_password
  - HTTP_PORT=3000
  - HTTP_HOST=0.0.0.0
  - CHROMA_SERVER_URL=http://chroma-server:5002
  - CHROMA_COLLECTION_NAME=entity_embeddings
```

### ChromaDB Server (docker-compose.yml)
```yaml
environment:
  - CHROMA_MODE=embedded
  - CHROMA_DATA_PATH=/data/chroma
  - CHROMA_COLLECTION_NAME=entity_embeddings
  - CHROMA_EMBEDDING_FUNCTION=ollama
  - OLLAMA_URL=http://ollama:11434
  - OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Data Persistence

Data is stored in Docker volumes:
- `chroma_data`: ChromaDB embeddings and metadata
- `ollama_data`: Ollama models and data

To backup:
```bash
docker run --rm -v chroma_data:/data -v $(pwd):/backup alpine tar czf /backup/chroma_backup.tar.gz /data
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama_backup.tar.gz /data
```

To restore:
```bash
docker run --rm -v chroma_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/chroma_backup.tar.gz --strip 1"
docker run --rm -v ollama_data:/data -v $(pwd):/backup alpine sh -c "cd /data && tar xzf /backup/ollama_backup.tar.gz --strip 1"
```

## Client Configuration

### VSCode Setup

Update `.vscode/mcp.json`:
```json
{
  "servers": {
    "arango-mcp": {
      "type": "stdio",
      "command": "docker",
      "args": ["exec", "-i", "mcp-server", "node", "build/index.js"]
    }
  }
}
```

### Claude Desktop Setup

Update `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "arango-mcp": {
      "command": "docker",
      "args": ["exec", "-i", "mcp-server", "node", "build/index.js"]
    }
  }
}
```

## Scaling Considerations

1. **Memory Usage**:
   - MCP Server: 200-500MB
   - ChromaDB Server: 500MB-2GB (depends on collection size)
   - Ollama: 2-4GB (depends on model)

2. **Storage**:
   - ChromaDB data grows with number of entities
   - Ollama models: ~4GB per model

3. **CPU**:
   - Recommend 2+ cores for production use
   - Heavy embedding operations will use significant CPU

## Troubleshooting

1. **ChromaDB Server Issues**:
   ```bash
   # Check logs
   docker compose logs chroma-server
   # Restart service
   docker compose restart chroma-server
   ```

2. **Ollama Issues**:
   ```bash
   # Check model status
   docker exec ollama ollama list
   # Pull model again
   docker exec ollama ollama pull nomic-embed-text
   ```

3. **MCP Server Issues**:
   ```bash
   # Check logs
   docker compose logs mcp-server
   # Verify ChromaDB connection
   curl http://localhost:3000/health
   ```

## Security Notes

1. Use strong passwords for ArangoDB
2. Configure firewalls to restrict port access
3. Use HTTPS in production environments
4. Keep Docker and all dependencies updated
5. Regularly backup data volumes

## Updates and Maintenance

1. **Update Images**:
   ```bash
   docker compose pull
   docker compose build --no-cache
   docker compose up -d
   ```

2. **Cleanup**:
   ```bash
   # Remove unused images
   docker image prune
   # Remove unused volumes
   docker volume prune
   ```

3. **Monitoring**:
   ```bash
   # Check resource usage
   docker stats
   # Check logs
   docker compose logs --tail=100 -f
   ```
