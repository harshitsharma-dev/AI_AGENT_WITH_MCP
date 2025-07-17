# Python Agent for ArangoDB MCP Server

## Index

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Environment Variables](#environment-variables)
6. [Semantic Search Setup](#semantic-search-setup)
7. [Usage Examples](#usage-examples)
8. [Integration: Claude & VSCode](#integration-claude--vscode)
9. [Development](#development)
10. [Debugging](#debugging)
11. [License](#license)

---

## Overview

This Python agent provides Model Context Protocol (MCP) support for ArangoDB, enabling advanced database operations and semantic search via ChromaDB and Ollama embeddings. It is designed for use with Claude, VSCode extensions, and other MCP-compatible tools.

---

## Features

- **AQL Query Execution**: Run ArangoDB queries with bind variables.
- **Document Operations**: Insert, update, remove documents.
- **Collection Management**: List, create, and backup collections.
- **Semantic Search**: Find entities and articles using natural language queries.
- **Graph Traversal**: Combine semantic search with ArangoDB graph operations.
- **Local Embeddings**: No external API required.

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd mcp-server-arangodb/python_agent

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration

Configure the agent via environment variables or config files. Example `.env`:

```env
ARANGO_URL=http://localhost:8529
ARANGO_DB=your_db
ARANGO_USERNAME=your_user
ARANGO_PASSWORD=your_password
CHROMA_MODE=embedded
CHROMA_EMBEDDING_FUNCTION=ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

---

## Environment Variables

- `ARANGO_URL`: ArangoDB server URL
- `ARANGO_DB`: Database name
- `ARANGO_USERNAME`: Username
- `ARANGO_PASSWORD`: Password
- `CHROMA_MODE`: ChromaDB mode (`embedded` recommended)
- `CHROMA_EMBEDDING_FUNCTION`: Embedding function (`ollama`)
- `OLLAMA_URL`: Ollama server URL
- `OLLAMA_EMBEDDING_MODEL`: Embedding model (`nomic-embed-text`)

---

## Semantic Search Setup

1. **Install Ollama**: [https://ollama.ai/](https://ollama.ai/)
2. **Pull Model**:
   ```bash
   ollama pull nomic-embed-text
   ```
3. **Start Ollama**:
   ```bash
   ollama serve
   ```

---

## Usage Examples

- **List Collections**: "List all collections in the database"
- **Query Users**: "FOR user IN users RETURN user"
- **Insert Document**: "Insert a new document with name 'John Doe' and email 'john@example.com' to the 'users' collection"
- **Semantic Search**: "Find articles related to artificial intelligence using semantic search"

---

## Integration: Claude & VSCode

- **Claude Desktop**: Add MCP server config in `claude_desktop_config.json`
- **VSCode Extension (Cline)**: Add MCP server config in `cline.cline/config.json`

---

## Development

```bash
# Build and run with auto-reload
npm run build
npm run watch
```

---

## Debugging

Use [MCP Inspector](https://github.com/modelcontextprotocol/inspector) for debugging MCP servers:

```bash
npm run inspector
```

---

## License

MIT License. See [LICENSE](../LICENSE) for details.

---

## AI Agent Architecture

The Python AI Agent is the core intelligence layer for the ArangoDB MCP server. It combines:

- **NLP-powered Entity Extraction**: Uses spaCy and custom logic to extract dates, names, categories, authors, keywords, and more from user queries.
- **Smart Tool Selection**: Dynamically selects the most relevant database or semantic tools based on query context and extracted entities.
- **Semantic Reasoning**: Integrates with Ollama for local LLM-powered prompt generation and semantic search.
- **MCP Protocol Client**: Communicates with the MCP server using JSON-RPC, handling tool discovery, invocation, and error recovery.
- **Extensible Categorization**: Supports a wide range of tool categories (search, association, analysis, graph, database ops) for flexible query handling.
- **Conversational Memory**: (Planned) Tracks conversation history for context-aware responses and multi-turn workflows.

### How it Works

1. **User Query**: Receives a natural language query via HTTP (Flask API).
2. **Entity Extraction**: Parses the query to identify intent, entities, dates, and other relevant information.
3. **Tool Selection**: Scores and selects the best tools for the query using a categorizer and scoring logic.
4. **Prompt Generation**: Builds optimized prompts for the LLM and MCP server, including tool schemas and context.
5. **Tool Execution**: Invokes the selected tool(s) via MCP, handling parameter conversion and error recovery.
6. **Response Formatting**: Formats the result for display, including markdown/HTML conversion for rich output.

### Key Classes
- `SmartAIAgent`: Main orchestrator for query processing, initialization, and diagnostics.
- `EntityExtractor`: NLP-based entity extraction from queries.
- `SmartToolSelector`: Scores and selects tools based on query context.
- `MCPClient`: Handles MCP protocol communication and tool execution.
- `OllamaClient`: Integrates with Ollama for LLM-powered reasoning and semantic search.

### Extending the Agent
- Add new tool schemas to MCP server and update the categorizer for new capabilities.
- Extend entity extraction logic for domain-specific queries.
- Integrate additional LLMs or semantic models as needed.
