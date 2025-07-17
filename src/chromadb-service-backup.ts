import axios from 'axios';

/**
 * ChromaDB Configuration Interface
 * Defines configuration options for the ChromaDB HTTP client
 */
export interface ChromaDBConfig {
    serverUrl?: string;          // URL for the ChromaDB Flask server
    collectionName?: string;     // Name of the collection to use
    maxRetries?: number;         // Maximum number of retries for failed requests
    timeout?: number;            // Timeout in milliseconds for requests
}

/**
 * Simplified ChromaDB service for entity embedding operations
 * Communicates with a separate ChromaDB Flask server
 */
export class ChromaDBService {
    private isInitialized = false;
    private config: Required<ChromaDBConfig>;

    constructor(config?: ChromaDBConfig) {
        this.config = {
            serverUrl: config?.serverUrl || process.env.CHROMA_SERVER_URL || 'http://localhost:5002',
            collectionName: config?.collectionName || process.env.CHROMA_COLLECTION_NAME || 'entity_embeddings',
            maxRetries: config?.maxRetries || parseInt(process.env.CHROMA_MAX_RETRIES || '3'),
            timeout: config?.timeout || parseInt(process.env.CHROMA_TIMEOUT || '30000')
        };

        console.log(`🔧 ChromaDB Service configured:
        Server URL: ${this.config.serverUrl}
        Collection: ${this.config.collectionName}
        Max Retries: ${this.config.maxRetries}
        Timeout: ${this.config.timeout}ms`);
    }

    /**
     * Initialize the ChromaDB connection
     */
    async initialize(): Promise<void> {
        try {
            if (this.isInitialized) return;

            // Check server health
            const response = await axios.get(`${this.config.serverUrl}/health`, {
                timeout: this.config.timeout
            });

            if (response.data.status === 'healthy') {
                console.log('✅ ChromaDB server connection established');
                this.isInitialized = true;
            } else {
                throw new Error('ChromaDB server is not healthy');
            }
        } catch (error) {
            console.error('❌ Failed to initialize ChromaDB:', error);
            throw new Error(`ChromaDB initialization failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Search for semantically similar entities
     */
    async searchSimilarEntities(
        query: string,
        nResults: number = 10,
        minSimilarity: number = 0.5,
        whereFilter?: Record<string, any>
    ): Promise<{
        entityIds: string[];
        entityNames: string[];
        similarities: number[];
        metadata: Record<string, any>[];
    }> {
        await this.ensureInitialized();

        try {
            const response = await axios.post(`${this.config.serverUrl}/search`, {
                query,
                nResults,
                minSimilarity,
                whereFilter
            }, {
                timeout: this.config.timeout
            });

            console.log(`🔍 Found ${response.data.entityIds.length} similar entities for query: "${query}"`);
            return response.data;
        } catch (error) {
            console.error('❌ ChromaDB search failed:', error);
            throw new Error(`Semantic search failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Add entities to the collection
     */
    async addEntities(
        entityIds: string[],
        entityTexts: string[],
        metadata: Record<string, any>[]
    ): Promise<void> {
        await this.ensureInitialized();

        if (entityIds.length !== entityTexts.length || entityIds.length !== metadata.length) {
            throw new Error('All input arrays must have the same length');
        }

        try {
            await axios.post(`${this.config.serverUrl}/add`, {
                entityIds,
                entityTexts,
                metadata
            }, {
                timeout: this.config.timeout
            });

            console.log(`✅ Added ${entityIds.length} entities to ChromaDB collection`);
        } catch (error) {
            console.error('❌ Failed to add entities to ChromaDB:', error);
            throw new Error(`Failed to add entities: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Get collection statistics
     */
    async getCollectionStats(): Promise<{
        count: number;
        name: string;
    }> {
        await this.ensureInitialized();

        try {
            const response = await axios.get(`${this.config.serverUrl}/stats`, {
                timeout: this.config.timeout
            });

            return response.data;
        } catch (error) {
            console.error('❌ Failed to get collection stats:', error);
            throw new Error(`Failed to get stats: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Check if ChromaDB is connected and collection is ready
     */
    async healthCheck(): Promise<{
        connected: boolean;
        collectionReady: boolean;
        error?: string;
    }> {
        try {
            const response = await axios.get(`${this.config.serverUrl}/health`, {
                timeout: this.config.timeout
            });

            return {
                connected: response.data.chromadb,
                collectionReady: response.data.collection
            };
        } catch (error) {
            return {
                connected: false,
                collectionReady: false,
                error: error instanceof Error ? error.message : String(error)
            };
        }
    }

    private async ensureInitialized(): Promise<void> {
        if (!this.isInitialized) {
            await this.initialize();
        }
    }

    /**
     * Close the ChromaDB connection
     * Note: This is now a no-op since we're using HTTP
     */
    async close(): Promise<void> {
        this.isInitialized = false;
        console.log('🔌 ChromaDB connection closed');
    }
}