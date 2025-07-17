#!/bin/bash

# Deploy script for ArangoDB MCP Server with ChromaDB and Ollama

echo "📦 Building Docker images..."

# Build all images
docker compose build

echo "💾 Saving images to tar files..."

# Save each image to a tar file
docker save -o mcp-server.tar mcp-server
docker save -o chroma-server.tar chroma-server

# Create a deployment package
echo "📁 Creating deployment package..."
tar -czf deploy.tar.gz \
    mcp-server.tar \
    chroma-server.tar \
    docker-compose.yml \
    chroma_server.py \
    requirements.txt \
    README.md \
    DOCKER_SETUP.md

echo "✅ Deployment package created: deploy.tar.gz"
echo "
To deploy on another machine:
1. Copy deploy.tar.gz to the target machine
2. Extract: tar -xzf deploy.tar.gz
3. Load images: 
   docker load -i mcp-server.tar
   docker load -i chroma-server.tar
4. Run: docker compose up -d
"
