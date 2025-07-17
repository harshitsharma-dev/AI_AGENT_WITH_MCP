# ChromaDB Embedded with Ollama Setup Guide

This guide will help you set up the local embedding environment for the ArangoDB MCP server's semantic search capabilities.

## Prerequisites

### 1. Install Ollama

**Windows:**
- Download from [https://ollama.ai/download](https://ollama.ai/download)
- Run the installer
- Ollama will start automatically as a service

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Service

**Windows:**
- Ollama should start automatically
- If not, search for "Ollama" in the Start menu and run it

**macOS/Linux:**
```bash
ollama serve
```

### 3. Pull the Embedding Model

```bash
ollama pull nomic-embed-text
```

This downloads the Nomic Embed Text model (~1.5GB) which provides high-quality embeddings.

### 4. Verify Installation

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check available models
ollama list
```

You should see `nomic-embed-text` in the list.

## Configuration

The ArangoDB MCP server is pre-configured to use:
- **Mode**: Embedded ChromaDB (no external server needed)
- **Embedding Function**: Ollama with nomic-embed-text
- **Data Storage**: Local `./chroma_data` directory

## Testing

Run the test script to verify everything is working:

```bash
node test_chromadb_embedded.js
```

## Environment Variables (Optional)

If you need to customize the configuration, set these in your `.env` file:

```bash
# ChromaDB Configuration
CHROMA_MODE=embedded
CHROMA_DATA_PATH=./chroma_data
CHROMA_COLLECTION_NAME=entity_embeddings

# Ollama Configuration
CHROMA_EMBEDDING_FUNCTION=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Troubleshooting

### Ollama Not Responding
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it
ollama serve
```

### Model Not Found
```bash
# List available models
ollama list

# Pull the model if missing
ollama pull nomic-embed-text
```

### ChromaDB Data Directory Issues
- The `chroma_data` directory will be created automatically
- Make sure the application has write permissions
- Delete the directory to reset the database

### Performance Issues
- Increase timeout: `CHROMA_TIMEOUT=60000`
- Increase retries: `CHROMA_MAX_RETRIES=5`
- Use a faster embedding model: `OLLAMA_EMBEDDING_MODEL=all-minilm`

## Benefits of This Setup

1. **No External Dependencies**: Everything runs locally
2. **No API Costs**: Free embeddings with Ollama
3. **Privacy**: Your data never leaves your machine
4. **Fast**: Local processing without network latency
5. **Offline Capable**: Works without internet connection
6. **Easy Setup**: Minimal configuration required

## Model Alternatives

You can use different embedding models with Ollama:

```bash
# Lighter model (faster, slightly lower quality)
ollama pull all-minilm
# Set: OLLAMA_EMBEDDING_MODEL=all-minilm

# Multilingual model
ollama pull multilingual-e5-large
# Set: OLLAMA_EMBEDDING_MODEL=multilingual-e5-large
```

## Next Steps

Once setup is complete:
1. Start your ArangoDB instance
2. Run the MCP server: `npm start` or `npx arango-server`
3. Use semantic search queries in Claude or your MCP client
4. The system will automatically create embeddings for your entities
