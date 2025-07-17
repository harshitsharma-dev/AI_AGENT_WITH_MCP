# Docker Setup Guide

This guide explains how to build and run the ArangoDB MCP Server with embedded ChromaDB and Ollama using Docker.

## Features

The Docker container includes:
- **ArangoDB MCP Server** with semantic search capabilities
- **Embedded ChromaDB** for vector storage (no external server needed)
- **Ollama** with `nomic-embed-text` model for local embeddings
- **Automatic setup** and model downloading
- **Persistent data volumes** for ChromaDB and Ollama data

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Build and start the container**:
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode**:
   ```bash
   docker-compose up -d --build
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f
   ```

4. **Stop the container**:
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker directly

1. **Build the image**:
   ```bash
   docker build -t arango-mcp-server .
   ```

2. **Run the container**:
   ```bash
   docker run -p 3000:3000 -p 11434:11434 \
     -v arango_chroma_data:/app/chroma_data \
     -v arango_ollama_data:/app/.ollama \
     --name arango-mcp-server \
     arango-mcp-server
   ```

3. **Run in detached mode**:
   ```bash
   docker run -d -p 3000:3000 -p 11434:11434 \
     -v arango_chroma_data:/app/chroma_data \
     -v arango_ollama_data:/app/.ollama \
     --name arango-mcp-server \
     arango-mcp-server
   ```

## Configuration

### Environment Variables

You can customize the configuration by modifying the environment variables in `docker-compose.yml` or passing them with `-e` flag:

```yaml
environment:
  # ArangoDB Configuration
  - ARANGO_URL=http://your-arangodb-server:8529
  - ARANGO_DB=your_database_name
  - ARANGO_USERNAME=your_username
  - ARANGO_PASSWORD=your_password
  
  # Server Configuration
  - HTTP_PORT=3000
  - HTTP_HOST=0.0.0.0
  
  # ChromaDB Configuration
  - CHROMA_MODE=embedded
  - CHROMA_DATA_PATH=/app/chroma_data
  - CHROMA_COLLECTION_NAME=entity_embeddings
  - CHROMA_EMBEDDING_FUNCTION=ollama
  
  # Ollama Configuration
  - OLLAMA_URL=http://localhost:11434
  - OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### Ports

- **3000**: MCP Server HTTP port
- **11434**: Ollama API port (for external access if needed)

### Volumes

- **chroma_data**: Persists ChromaDB vector database
- **ollama_data**: Persists Ollama models and configuration

## Startup Process

When the container starts, it will:

1. 🦙 Start Ollama server in the background
2. ⏳ Wait for Ollama to be ready (10 seconds)
3. 📦 Pull the `nomic-embed-text` embedding model
4. 🎯 Start the MCP server

The entire startup process typically takes 2-3 minutes on first run (downloading the model).

## Health Check

The container includes a health check that verifies the MCP server is responding:

```bash
# Check container health
docker-compose ps

# Manual health check
curl -f http://localhost:3000/health
```

## Logs and Troubleshooting

### View logs
```bash
# Docker Compose
docker-compose logs -f

# Docker directly
docker logs -f arango-mcp-server
```

### Common startup messages
```
🚀 Starting ArangoDB MCP Server with ChromaDB and Ollama...
🦙 Starting Ollama server...
⏳ Waiting for Ollama to be ready...
📦 Pulling nomic-embed-text model...
🎯 Starting MCP server...
🔧 ChromaDB Service configured: Mode: embedded
📁 Using embedded ChromaDB with local data storage
🤖 Using ollama embedding function
🦙 Configuring Ollama embeddings
✅ Created new collection: entity_embeddings with ollama embeddings
🎯 ChromaDB service fully initialized
```

### Troubleshooting

1. **Ollama model download fails**:
   - The container will continue with cached models if available
   - You can manually pull the model: `docker exec -it arango-mcp-server ollama pull nomic-embed-text`

2. **ChromaDB data persistence**:
   - Data is stored in Docker volumes (`chroma_data`, `ollama_data`)
   - To reset data: `docker-compose down -v`

3. **Memory issues**:
   - The container uses `NODE_OPTIONS=--max-old-space-size=4096`
   - Increase if needed for large datasets

## Using with MCP Clients

### Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "arango-docker": {
      "command": "docker",
      "args": ["exec", "-i", "arango-mcp-server", "node", "build/index.js"],
      "env": {}
    }
  }
}
```

### VS Code with MCP Extension

Add to your `.vscode/mcp.json`:

```json
{
  "servers": {
    "arango-docker": {
      "type": "stdio",
      "command": "docker",
      "args": ["exec", "-i", "arango-mcp-server", "node", "build/index.js"],
      "env": {}
    }
  }
}
```

## Development

### Building with custom changes

```bash
# Make your changes to the code
# Rebuild the image
docker-compose build --no-cache

# Start with new image
docker-compose up
```

### Accessing the container

```bash
# Get a shell in the running container
docker exec -it arango-mcp-server bash

# Check Ollama status
docker exec -it arango-mcp-server ollama list

# Test Ollama embeddings
docker exec -it arango-mcp-server ollama run nomic-embed-text "test query"
```

## Production Deployment

For production deployment:

1. **Use Docker secrets** for sensitive environment variables
2. **Configure proper logging** and monitoring
3. **Set up backup** for persistent volumes
4. **Use a reverse proxy** (nginx, traefik) for HTTPS
5. **Configure resource limits** in docker-compose.yml

Example production docker-compose.yml additions:

```yaml
services:
  arango-mcp-server:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

## Cleanup

```bash
# Stop and remove containers, networks
docker-compose down

# Remove containers, networks, and volumes
docker-compose down -v

# Remove the built image
docker rmi arango-mcp-server
```
