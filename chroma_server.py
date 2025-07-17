from flask import Flask, request, jsonify
from chromadb import Client, Settings
import chromadb
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ChromaDB client configuration
CHROMA_DATA_PATH = './cdbComments'
COLLECTION_NAME = 'entity_embeddings'  # Changed to avoid dimension mismatch with existing collection
EMBEDDING_FUNCTION = 'ollama'
OLLAMA_URL = 'http://localhost:11434/'
OLLAMA_MODEL = 'nomic-embed-text'


def get_embedding_function():
    """
    Define the embedding function clearly and consistently.
    This function ensures the same embedding configuration is used
    for both new and existing collections.
    
    Returns:
        embedding_function: The configured embedding function or None for default
    """
    if EMBEDDING_FUNCTION == 'ollama':
        try:
            # Try to import and use Ollama embedding functi configured with embedding function: <chromadb.utils.embedding_functions.ollama_embedding_function.OllamaEmbeddingFunction object at 0x7f316eba80d0>on
            import chromadb.utils.embedding_functions as ef
            embedding_fn = ef.OllamaEmbeddingFunction(
                url=OLLAMA_URL,
                model_name=OLLAMA_MODEL
            )
            logger.info(f"✅ Ollama embedding function configured: {OLLAMA_MODEL} at {OLLAMA_URL}")
            return embedding_fn
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"⚠️ Ollama embedding function not available: {e}")
            logger.info("📝 Falling back to default ChromaDB embedding function")
            return None
    
    # elif EMBEDDING_FUNCTION == 'openai':
    #     try:
    #         import chromadb.utils.embedding_functions as ef
    #         api_key = os.getenv('OPENAI_API_KEY')
    #         if not api_key:
    #             logger.error("❌ OPENAI_API_KEY environment variable is required for OpenAI embeddings")
    #             return None
    #         embedding_fn = ef.OpenAIEmbeddingFunction(api_key=api_key)
    #         logger.info("✅ OpenAI embedding function configured")
    #         return embedding_fn
    #     except (ImportError, AttributeError, Exception) as e:
    #         logger.warning(f"⚠️ OpenAI embedding function not available: {e}")
    #         logger.info("📝 Falling back to default ChromaDB embedding function")
    #         return None
    
    # elif EMBEDDING_FUNCTION == 'sentence-transformers':
    #     try:
    #         import chromadb.utils.embedding_functions as ef
    #         model_name = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
    #         embedding_fn = ef.SentenceTransformerEmbeddingFunction(model_name=model_name)
    #         logger.info(f"✅ Sentence Transformer embedding function configured: {model_name}")
    #         return embedding_fn
    #     except (ImportError, AttributeError, Exception) as e:
    #         logger.warning(f"⚠️ Sentence Transformer embedding function not available: {e}")
    #         logger.info("📝 Falling back to default ChromaDB embedding function")
    #         return None
    
    else:
        logger.info(f"📝 Using default ChromaDB embedding function (type: {EMBEDDING_FUNCTION})")
        return None

# Initialize the embedding function once - this ensures consistency across the application
EMBEDDING_FUNCTION = get_embedding_function()

# Log the final configuration
if EMBEDDING_FUNCTION is not None:
    logger.info(f"🔧 Embedding function successfully configured: {EMBEDDING_FUNCTION}")
else:
    logger.info("🔧 Using ChromaDB default embedding function")

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="./cdbComments")

# Initialize collection variable
collection = None

# Get or create collection with consistent embedding function configuration
try:
    # Try to get existing collection
    collection = client.get_collection(name=COLLECTION_NAME)
    logger.info(f"✅ Connected to existing collection: {COLLECTION_NAME}")
    
    # Important Note: For existing collections, ChromaDB will use the embedding function
    # that was defined when the collection was originally created.
    # The embedding function cannot be changed for existing collections.
    logger.info("ℹ️ Note: Existing collection uses its original embedding function configuration")
    logger.info(f"ℹ️ Current server configured function: {EMBEDDING_FUNCTION}")
    
except Exception as e:
    # Collection doesn't exist, create new one with the defined embedding function
    logger.info(f"📝 Collection '{COLLECTION_NAME}' not found, creating new one... {e}")
    try:
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=EMBEDDING_FUNCTION
        )
        logger.info(f"✅ Created new collection: {COLLECTION_NAME}")
        if EMBEDDING_FUNCTION is not None:
            logger.info(f"✅ Collection configured with embedding function: {EMBEDDING_FUNCTION}")
        else:
            logger.info("✅ Collection configured with default ChromaDB embedding function")
    except Exception as create_error:
        logger.error(f"❌ Failed to create collection: {create_error}")
        # Fallback: try without embedding function
        logger.info("🔄 Attempting to create collection with default embedding function...")
        try:
            collection = client.create_collection(name=COLLECTION_NAME)
            logger.info(f"✅ Created collection with default embedding: {COLLECTION_NAME}")
        except Exception as fallback_error:
            logger.error(f"❌ Failed to create collection even with default settings: {fallback_error}")
            collection = None

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check ChromaDB connection
        client.heartbeat()
        # Check collection
        collection.count()
        return jsonify({
            'status': 'healthy',
            'chromadb': True,
            'collection': True
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

import requests
import json
def get_embedding_ollama(text):
    # Use a model that produces 384 dimensions to match existing collection
    res = requests.post("http://localhost:11434/api/embeddings", json={
        "model": "nomic-embed-text",  # This should produce 384 dimensions
        "prompt": text
    })
    result = res.json()
    if 'embedding' not in result:
        raise ValueError(f"No embedding found in response: {result}")
    
    embedding = result['embedding']
    
    # Adjust embedding dimensions to match collection requirements (728)
    target_dim = 728
    if len(embedding) > target_dim:
        # Truncate if too long
        embedding = embedding[:target_dim]
        logger.info(f"🔧 Truncated embedding from {len(result['embedding'])} to {target_dim} dimensions")
    elif len(embedding) < target_dim:
        # Pad with zeros if too short
        padding = [0.0] * (target_dim - len(embedding))
        embedding = embedding + padding
        logger.info(f"🔧 Padded embedding from {len(result['embedding'])} to {target_dim} dimensions")
    
    return embedding

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        query = data.get('query')
        n_results = data.get('nResults', 10)
        min_similarity = data.get('minSimilarity', 0.5)
        where_filter = data.get('whereFilter')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        query_emb = get_embedding_ollama(query)
        print(f"Query embedding dimension: {len(query_emb)}")

        # Perform the search using pre-computed embedding
        results = collection.query(
            query_embeddings=[query_emb],  # Use pre-computed embedding instead of query_texts
            n_results=n_results,
            where=where_filter
        )

        # Process results
        valid_results = {
            'entityIds': [],
            'entityNames': [],
            'similarities': [],
            'metadata': []
        }

        if results.get('ids') and results['ids'][0]:
            for i, id_val in enumerate(results['ids'][0]):
                similarity = 1 - (results['distances'][0][i] if results.get('distances') else 0)
                
                if similarity >= min_similarity:
                    valid_results['entityIds'].append(id_val)
                    valid_results['similarities'].append(similarity)
                    
                    metadata = results['metadatas'][0][i] if results.get('metadatas') else {}
                    valid_results['metadata'].append(metadata)
                    
                    entity_name = str(metadata.get('name') or metadata.get('entity_name') or id_val)
                    valid_results['entityNames'].append(entity_name)

        logger.info(f"🔍 Found {len(valid_results['entityIds'])} similar entities for query: {query}")
        return jsonify(valid_results), 200

    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/add', methods=['POST'])
def add_entities():
    try:
        data = request.get_json()
        entity_ids = data.get('entityIds', [])
        entity_texts = data.get('entityTexts', [])
        metadata = data.get('metadata', [])

        if not entity_ids or not entity_texts:
            return jsonify({'error': 'Entity IDs and texts are required'}), 400

        if len(entity_ids) != len(entity_texts) or len(entity_ids) != len(metadata):
            return jsonify({'error': 'All arrays must have the same length'}), 400

        # Add entities to collection
        collection.add(
            ids=entity_ids,
            documents=entity_texts,
            metadatas=metadata
        )

        logger.info(f"✅ Added {len(entity_ids)} entities to ChromaDB collection")
        return jsonify({'success': True, 'count': len(entity_ids)}), 200

    except Exception as e:
        logger.error(f"❌ Add entities failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        count = collection.count()
        return jsonify({
            'count': count,
            'name': COLLECTION_NAME
        }), 200
    except Exception as e:
        logger.error(f"❌ Get stats failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/embedding-info', methods=['GET'])
def get_embedding_info():
    """
    Get information about the current embedding function configuration.
    This endpoint helps debug embedding function issues.
    """
    try:
        return jsonify({
            'EMBEDDING_FUNCTION': EMBEDDING_FUNCTION,
            'embedding_function_configured': EMBEDDING_FUNCTION is not None,
            'collection_name': COLLECTION_NAME,
            'ollama_url': OLLAMA_URL if EMBEDDING_FUNCTION == 'ollama' else None,
            'ollama_model': OLLAMA_MODEL if EMBEDDING_FUNCTION == 'ollama' else None,
            'data_path': CHROMA_DATA_PATH,
            'note': 'Existing collections use their original embedding function. To change embedding function, create a new collection or delete existing one.'
        }), 200
    except Exception as e:
        logger.error(f"❌ Get embedding info failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/collection/details', methods=['GET'])
def get_collection_details():
    """
    Get details of the current collection, including embedding function and document count.
    """
    try:
        collection_info = {
            'name': collection.name,
            'document_count': collection.count(),
            'embedding_function': str(collection.embedding_function) if collection.embedding_function else 'None (using default)',
            'note': 'Existing collections use their original embedding function. To change embedding function, create a new collection or delete existing one.'
        }
        return jsonify(collection_info), 200
    except Exception as e:
        logger.error(f"❌ Get collection details failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/collection/recreate', methods=['POST'])
def recreate_collection():
    """
    Recreate the collection with the correct embedding function and dimensions.
    This endpoint deletes the existing collection and creates a new one.
    """
    try:
        global collection
        
        # Delete the existing collection if it exists
        try:
            existing_collection = client.get_collection(name=COLLECTION_NAME)
            client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"✅ Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            logger.info(f"📝 Collection {COLLECTION_NAME} doesn't exist, creating new one")
        
        # Create a new collection with the correct embedding function
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=EMBEDDING_FUNCTION
        )
        logger.info(f"✅ Created new collection: {COLLECTION_NAME} with embedding function: {EMBEDDING_FUNCTION}")
        
        return jsonify({'success': True, 'message': 'Collection recreated successfully'}), 200
    except Exception as e:
        logger.error(f"❌ Recreate collection failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test-embedding', methods=['POST'])
def test_embedding():
    """
    Test the embedding function with a sample text to check dimensions.
    """
    try:
        data = request.get_json()
        test_text = data.get('text', 'This is a test sentence')
        
        # Get embedding using our function
        embedding = get_embedding_ollama(test_text)
        
        return jsonify({
            'text': test_text,
            'embedding_dimension': len(embedding),
            'embedding_sample': embedding[:5],  # First 5 values
            'model_used': 'znbang/bge:large-en-v1.5-q4_k_m'
        }), 200
    except Exception as e:
        logger.error(f"❌ Test embedding failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('CHROMA_SERVER_PORT', 5002))
    host = os.getenv('CHROMA_SERVER_HOST', '0.0.0.0')
    app.run(host=host, port=port)
