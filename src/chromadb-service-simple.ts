import { ChromaClient } from 'chromadb';

/**
 * ChromaDB Configuration Interface
 */
export interface ChromaDBConfig {
    url?: string;
    collectionName?: string;
    openaiApiKey?: string;
    openaiModel?: string;
    maxRetries?: number;
    timeout?: number;
}

/**
 * Simplified ChromaDB service for entity embedding operations
 * Handles semantic similarity search for entities with basic functionality
 */
export class ChromaDBService {
    private client: ChromaClient;
    private entityCollection: any = null;
    private isInitialized = false;
    private config: Required<ChromaDBConfig>;

    constructor(config?: ChromaDBConfig) {
        // Load configuration from environment variables with defaults
        this.config = {
            url: config?.url || process.env.CHROMA_URL || process.env.CHROMADB_URL || 'http://localhost:8000',
            collectionName: config?.collectionName || process.env.CHROMA_COLLECTION_NAME || process.env.CHROMADB_COLLECTION || 'entity_embeddings',
            openaiApiKey: config?.openaiApiKey || process.env.OPENAI_API_KEY || '',
            openaiModel: config?.openaiModel || process.env.OPENAI_EMBEDDING_MODEL || process.env.CHROMA_EMBEDDING_MODEL || 'text-embedding-3-small',
            maxRetries: config?.maxRetries || parseInt(process.env.CHROMA_MAX_RETRIES || '3'),
            timeout: config?.timeout || parseInt(process.env.CHROMA_TIMEOUT || '30000')
        };

        console.log(`🔧 ChromaDB Service configured:
        URL: ${this.config.url}
        Collection: ${this.config.collectionName}
        Embedding Model: ${this.config.openaiModel}
        Max Retries: ${this.config.maxRetries}
        Timeout: ${this.config.timeout}ms`);
        
        this.client = new ChromaClient({
            path: this.config.url
        });
    }

    /**
     * Initialize the ChromaDB connection and collection
     */
    async initialize(): Promise<void> {
        try {
            if (this.isInitialized) return;

            // Test connection with timeout
            console.log(`🔌 Connecting to ChromaDB at ${this.config.url}...`);
            await this.client.heartbeat();
            console.log('✅ ChromaDB connection established');

            console.log(`🤖 Using ChromaDB default embedding function`);
            if (this.config.openaiApiKey) {
                console.log(`📝 Note: OpenAI API key provided - consider upgrading to use custom OpenAI embeddings`);
            }

            // Get or create entity collection (using simplified API)
            try {
                this.entityCollection = await this.client.getCollection({
                    name: this.config.collectionName
                } as any);
                console.log(`✅ Connected to existing collection: ${this.config.collectionName}`);
            } catch (error) {
                console.log(`📝 Creating new collection: ${this.config.collectionName}`);
                
                this.entityCollection = await this.client.createCollection({
                    name: this.config.collectionName
                } as any);
                console.log(`✅ Created new collection: ${this.config.collectionName}`);
            }

            this.isInitialized = true;
            console.log('🎯 ChromaDB service fully initialized');
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

        if (!this.entityCollection) {
            throw new Error('Entity collection not initialized');
        }

        try {
            const queryResponse = await this.entityCollection.query({
                queryTexts: [query],
                nResults: nResults,
                where: whereFilter
            });

            // Filter results by similarity threshold
            const validResults = {
                entityIds: [] as string[],
                entityNames: [] as string[],
                similarities: [] as number[],
                metadata: [] as Record<string, any>[]
            };

            if (queryResponse.ids && queryResponse.ids[0] && 
                queryResponse.distances && queryResponse.distances[0] &&
                queryResponse.metadatas && queryResponse.metadatas[0]) {
                
                for (let i = 0; i < queryResponse.ids[0].length; i++) {
                    const similarity = 1 - (queryResponse.distances[0][i] || 1); // Convert distance to similarity
                    
                    if (similarity >= minSimilarity) {
                        validResults.entityIds.push(queryResponse.ids[0][i]);
                        validResults.similarities.push(similarity);
                        
                        const metadata = queryResponse.metadatas[0][i] || {};
                        validResults.metadata.push(metadata);
                        
                        // Extract entity name from metadata or use ID as fallback
                        const entityName = String(metadata.name || metadata.entity_name || queryResponse.ids[0][i]);
                        validResults.entityNames.push(entityName);
                    }
                }
            }

            console.log(`🔍 Found ${validResults.entityIds.length} similar entities for query: "${query}"`);
            return validResults;
        } catch (error) {
            console.error('❌ ChromaDB search failed:', error);
            throw new Error(`Semantic search failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }

    /**
     * Add entities to the collection (for initial setup or updates)
     */
    async addEntities(
        entityIds: string[],
        entityTexts: string[],
        metadata: Record<string, any>[]
    ): Promise<void> {
        await this.ensureInitialized();

        if (!this.entityCollection) {
            throw new Error('Entity collection not initialized');
        }

        if (entityIds.length !== entityTexts.length || entityIds.length !== metadata.length) {
            throw new Error('All input arrays must have the same length');
        }

        try {
            await this.entityCollection.add({
                ids: entityIds,
                documents: entityTexts,
                metadatas: metadata
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

        if (!this.entityCollection) {
            throw new Error('Entity collection not initialized');
        }

        try {
            const count = await this.entityCollection.count();
            return {
                count,
                name: this.config.collectionName
            };
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
            await this.client.heartbeat();
            const connected = true;
            
            let collectionReady = false;
            if (this.entityCollection) {
                await this.entityCollection.count();
                collectionReady = true;
            }

            return { connected, collectionReady };
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
     */
    async close(): Promise<void> {
        // ChromaDB client doesn't require explicit closing in current version
        this.isInitialized = false;
        this.entityCollection = null;
        console.log('🔌 ChromaDB connection closed');
    }
}
