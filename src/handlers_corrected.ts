import { Database } from 'arangojs';
import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { API_TOOLS } from "./tools.js";
import {
    FindArticlesByEntityArgs,
    GetTopMentionedEntitiesArgs,
    FindArticlesByEntityAndKeywordsArgs,
    FindCoOccurringEntitiesArgs,
    GetPaginatedArticlesWithEntitiesArgs,
} from "./types.js";

interface ToolHandler<T = any> {
    name: string;
    handler: (args: T) => Promise<any>;
    inputSchema: {
        type: "object";
        properties: Record<string, unknown>;
        required?: string[];
    };
    description?: string;
}

export class ToolHandlers {
    private db: Database;
    private tools: ToolHandler[];
    private mcpTools: Tool[];
    private ensureConnectionFn?: () => Promise<void>;

    constructor(db?: Database, mcpTools?: Tool[], ensureConnectionFn?: () => Promise<void>) {
        // Initialize database connection with direct localhost configuration
        this.db = db || new Database({
            url: 'http://localhost:8529',
            databaseName: 'newsDB2022',
            auth: { 
                username: 'root',
                password: 'i-0172f1f969c7548c4'
            }
        });
        
        this.mcpTools = mcpTools || [];
        this.ensureConnectionFn = ensureConnectionFn;        
        // Initialize tools with proper TypeScript typing
        this.tools = [
            {
                name: API_TOOLS.FIND_ARTICLES_BY_ENTITY,
                handler: (args: FindArticlesByEntityArgs) => this.handleFindArticlesByEntity(args),
                inputSchema: {
                    type: "object",
                    properties: {
                        entityName: { type: "string" }
                    },
                    required: ["entityName"]
                }
            },
            {
                name: API_TOOLS.GET_TOP_MENTIONED_ENTITIES,
                handler: (args: GetTopMentionedEntitiesArgs) => this.handleGetTopMentionedEntities(args),
                inputSchema: {
                    type: "object",
                    properties: {
                        entityType: { type: "string" },
                        limit: { type: "number" }
                    },
                    required: ["limit"]
                }
            },
            {
                name: API_TOOLS.FIND_ARTICLES_BY_ENTITY_AND_KEYWORDS,
                handler: (args: FindArticlesByEntityAndKeywordsArgs) => this.handleFindArticlesByEntityAndKeywords(args),
                inputSchema: {
                    type: "object",
                    properties: {
                        targetEntityName: { type: "string" },
                        keywords: { type: "array", items: { type: "string" } }
                    },
                    required: ["targetEntityName", "keywords"]
                }
            },
            {
                name: API_TOOLS.FIND_CO_OCCURRING_ENTITIES,
                handler: (args: FindCoOccurringEntitiesArgs) => this.handleFindCoOccurringEntities(args),
                inputSchema: {
                    type: "object",
                    properties: {
                        targetEntityName: { type: "string" },
                        minCoOccurrences: { type: "number" },
                        topNCoOccurringEntities: { type: "number" }
                    },
                    required: ["targetEntityName"]
                }
            },
            {
                name: API_TOOLS.GET_PAGINATED_ARTICLES_WITH_ENTITIES,
                handler: (args: GetPaginatedArticlesWithEntitiesArgs) => this.handleGetPaginatedArticlesWithEntities(args),
                inputSchema: {
                    type: "object",
                    properties: {
                        pageNumber: { type: "number" },
                        pageSize: { type: "number" },
                        topNEntitiesPerArticle: { type: "number" }
                    },
                    required: ["pageNumber", "pageSize"]
                }
            }
        ] as ToolHandler[];
    }

    getTools(): { tools: ToolHandler[] } {
        return { tools: this.tools };
    }

    async handleListTools(): Promise<Tool[]> {
        return this.mcpTools;
    }

    async handleCallTool(params: { name: string; arguments?: any }): Promise<{ content: Array<{ type: 'text'; text: string }> }> {
        try {
            if (this.ensureConnectionFn) {
                await this.ensureConnectionFn();
            } else {
                await this.ensureConnection();
            }

            const result = await this.handle(params.name, params.arguments || {});
            
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify(result, null, 2)
                }]
            };
        } catch (error) {
            return {
                content: [{
                    type: 'text',
                    text: JSON.stringify({
                        error: error instanceof Error ? error.message : String(error),
                        tool: params.name,
                        arguments: params.arguments,
                        timestamp: new Date().toISOString()
                    }, null, 2)
                }]
            };
        }
    }

    async handle(toolName: string, args: any): Promise<any> {
        try {
            await this.ensureConnection();
            
            // Convert string inputs to lowercase while preserving numeric and boolean values
            const processedArgs = this.convertStringInputsToLowercase(args);
            
            switch (toolName) {
                case API_TOOLS.QUERY:
                    return await this.handleQuery(processedArgs);
                case API_TOOLS.INSERT:
                    return await this.handleInsert(processedArgs);
                case API_TOOLS.UPDATE:
                    return await this.handleUpdate(processedArgs);
                case API_TOOLS.REMOVE:
                    return await this.handleRemove(processedArgs);
                case API_TOOLS.COLLECTIONS:
                    return await this.handleCollections(processedArgs);
                case API_TOOLS.CREATE_COLLECTION:
                    return await this.handleCreateCollection(processedArgs);
                case API_TOOLS.BACKUP:
                    return await this.handleBackup(processedArgs);
                case API_TOOLS.FIND_ARTICLES_BY_ENTITY:
                    return await this.handleFindArticlesByEntity(processedArgs);
                case API_TOOLS.GET_TOP_MENTIONED_ENTITIES:
                    return await this.handleGetTopMentionedEntities(processedArgs);
                case API_TOOLS.FIND_ARTICLES_BY_ENTITY_AND_KEYWORDS:
                    return await this.handleFindArticlesByEntityAndKeywords(processedArgs);
                case API_TOOLS.FIND_CO_OCCURRING_ENTITIES:
                    return await this.handleFindCoOccurringEntities(processedArgs);
                case API_TOOLS.GET_PAGINATED_ARTICLES_WITH_ENTITIES:
                    return await this.handleGetPaginatedArticlesWithEntities(processedArgs);
                default:
                    throw new Error(`Unknown tool: ${toolName}`);
            }
        } catch (error) {
            console.error(`Error handling tool ${toolName}:`, error);
            throw error;
        }
    }

    private async ensureConnection(): Promise<void> {
        try {
            await this.db.version();
        } catch (error) {
            console.error('Database connection error:', error);
            throw error;
        }
    }

    // Utility function to convert string inputs to lowercase
    private convertStringInputsToLowercase(args: any): any {
        if (args === null || args === undefined) {
            return args;
        }

        if (typeof args === 'string') {
            return args.toLowerCase();
        }

        if (Array.isArray(args)) {
            return args.map(item => this.convertStringInputsToLowercase(item));
        }

        if (typeof args === 'object') {
            const converted: any = {};
            for (const [key, value] of Object.entries(args)) {
                // Convert string values to lowercase, but preserve certain fields that should remain case-sensitive
                const caseSensitiveFields = ['_id', '_key', '_rev', 'pageNumber', 'pageSize', 'limit',
                                           'minMentionCount', 'minMentionTF', 'minCoOccurrences', 'topNCoOccurringEntities',
                                           'topNEntitiesPerArticle', 'minMentionCountPerArticle', 'minMentionTFPerArticle',
                                           'targetMinMentionCountInSharedArticle', 'coOccurringMinMentionCountInSharedArticle',
                                           'waitForSync'];
                
                if (caseSensitiveFields.includes(key)) {
                    converted[key] = value;
                } else {
                    converted[key] = this.convertStringInputsToLowercase(value);
                }
            }
            return converted;
        }

        return args;
    }

    // New handler implementations for entity-article analysis
    private async handleFindArticlesByEntity(args: FindArticlesByEntityArgs): Promise<any> {
        const { 
            entityName,
            startDate = null,
            endDate = null,
            category = null,
            source = null,
            minMentionCount = null,
            minMentionTF = null,
            mentionBertSchema = null
        } = args;

        const query = `
            FOR entityDoc IN Entity
                FILTER LOWER(entityDoc.name) == LOWER(@entityName)
                LIMIT 1

                FOR ae IN article_entities
                    FILTER ae._to == entityDoc._id
                    
                    FILTER @minMentionCount == null OR ae.ne_count >= @minMentionCount
                    FILTER @minMentionTF == null OR ae.ne_tf >= @minMentionTF
                    FILTER @mentionBertSchema == null OR @mentionBertSchema IN ae.bert_schema

                    FOR articleDoc IN Article
                        FILTER ae._from == articleDoc._id

                        FILTER @startDate == null OR articleDoc.date_added >= @startDate
                        FILTER @endDate == null OR articleDoc.date_added <= @endDate
                        FILTER @category == null OR @category IN articleDoc.category
                        FILTER @source == null OR articleDoc.default.source == @source

                        SORT articleDoc.date_added DESC

                        RETURN {
                            articleId: articleDoc._id,
                            title: articleDoc.default.title,
                            date_added: articleDoc.date_added,
                            summary: articleDoc.default_summary,
                            category: articleDoc.category,
                            source: articleDoc.default.source,
                            entityMentionDetails: {
                                count: ae.ne_count,
                                tf: ae.ne_tf,
                                bertSchema: ae.bert_schema,
                                originList: ae.origin_list
                            }
                        }
        `;
        
        const cursor = await this.db.query(query, {
            entityName,
            startDate,
            endDate,
            category,
            source,
            minMentionCount,
            minMentionTF,
            mentionBertSchema
        });
        return await cursor.all();
    }

    private async handleGetTopMentionedEntities(args: GetTopMentionedEntitiesArgs): Promise<any> {
        const { 
            entityType = null,
            limit,
            articleStartDate = null,
            articleEndDate = null,
            articleCategory = null,
            articleSource = null,
            minMentionCountPerArticle = null,
            minMentionTFPerArticle = null,
            entityBertSchema = null
        } = args;

        const query = `
            FOR ae IN article_entities
                FOR articleDoc IN Article
                    FILTER ae._from == articleDoc._id

                    FILTER @articleStartDate == null OR articleDoc.date_added >= @articleStartDate
                    FILTER @articleEndDate == null OR articleDoc.date_added <= @articleEndDate
                    FILTER @articleCategory == null OR @articleCategory IN articleDoc.category
                    FILTER @articleSource == null OR articleDoc.default.source == @articleSource

                    FILTER @minMentionCountPerArticle == null OR ae.ne_count >= @minMentionCountPerArticle
                    FILTER @minMentionTFPerArticle == null OR ae.ne_tf >= @minMentionTFPerArticle

                    FOR entityDoc IN Entity
                        FILTER ae._to == entityDoc._id

                        FILTER @entityBertSchema == null OR @entityBertSchema IN entityDoc.bert_schema

                        COLLECT entityId = entityDoc._id,
                                entityName = entityDoc.name
                        AGGREGATE totalMentions = SUM(ae.ne_count),
                                  articleCount = COUNT_DISTINCT(articleDoc._id)

                        SORT totalMentions DESC
                        LIMIT @limit

                        RETURN {
                            entityId: entityId,
                            entityName: entityName,
                            totalMentions: totalMentions,
                            articleCount: articleCount
                        }
        `;

        const cursor = await this.db.query(query, {
            limit,
            articleStartDate,
            articleEndDate,
            articleCategory,
            articleSource,
            minMentionCountPerArticle,
            minMentionTFPerArticle,
            entityBertSchema
        });
        return await cursor.all();
    }

    private async handleFindArticlesByEntityAndKeywords(args: FindArticlesByEntityAndKeywordsArgs): Promise<any> {
        const { 
            targetEntityName,
            keywords,
            keywordOperator = "OR",
            minMentionCount = null,
            minMentionTF = null,
            mentionBertSchema = null,
            startDate = null,
            endDate = null,
            category = null,
            source = null
        } = args;

        const query = `
            LET targetEntity = (
                FOR e IN Entity
                    FILTER LOWER(e.name) == LOWER(@targetEntityName)
                    LIMIT 1
                    RETURN e._id
            )

            FILTER LENGTH(targetEntity) > 0

            LET articlesByEntity = (
                FOR ae IN article_entities
                    FILTER ae._to == targetEntity[0]
                    
                    FILTER @minMentionCount == null OR ae.ne_count >= @minMentionCount
                    FILTER @minMentionTF == null OR ae.ne_tf >= @minMentionTF
                    FILTER @mentionBertSchema == null OR @mentionBertSchema IN ae.bert_schema

                    RETURN DISTINCT ae._from
            )

            LET articlesByKeywords = (
                LENGTH(@keywords) == 0 ? 
                (FOR a IN Article RETURN a._id) :
                (
                    FOR a IN Article
                        LET searchText = CONCAT_SEPARATOR(" ", a.default.title, a.default_summary, a.default.description)
                        LET matchesKeywords = (
                            @keywordOperator == "AND" ?
                            (
                                FOR keyword IN @keywords
                                    FILTER CONTAINS(LOWER(searchText), LOWER(keyword))
                                    RETURN true
                            ) :
                            (
                                FOR keyword IN @keywords
                                    FILTER CONTAINS(LOWER(searchText), LOWER(keyword))
                                    RETURN true
                            )
                        )
                        FILTER LENGTH(matchesKeywords) > 0
                        RETURN a._id
                )
            )

            FOR articleId IN INTERSECTION(articlesByEntity, articlesByKeywords)
                FOR articleDoc IN Article
                    FILTER articleDoc._id == articleId

                    FILTER @startDate == null OR articleDoc.date_added >= @startDate
                    FILTER @endDate == null OR articleDoc.date_added <= @endDate
                    FILTER @category == null OR @category IN articleDoc.category
                    FILTER @source == null OR articleDoc.default.source == @source

                    SORT articleDoc.date_added DESC

                    RETURN {
                        articleId: articleDoc._id,
                        title: articleDoc.default.title,
                        date_added: articleDoc.date_added,
                        summary: articleDoc.default_summary,
                        category: articleDoc.category,
                        source: articleDoc.default.source
                    }
        `;

        const cursor = await this.db.query(query, {
            targetEntityName,
            keywords,
            keywordOperator,
            minMentionCount,
            minMentionTF,
            mentionBertSchema,
            startDate,
            endDate,
            category,
            source
        });
        return await cursor.all();
    }

    private async handleFindCoOccurringEntities(args: FindCoOccurringEntitiesArgs): Promise<any> {
        const { 
            targetEntityName,
            minCoOccurrences = 1,
            topNCoOccurringEntities = 10,
            targetEntityBertSchema = null,
            sharedArticleStartDate = null,
            sharedArticleEndDate = null,
            sharedArticleCategory = null,
            sharedArticleSource = null,
            targetMinMentionCountInSharedArticle = null,
            coOccurringEntityBertSchema = null,
            coOccurringMinMentionCountInSharedArticle = null
        } = args;

        const query = `
            // Find the target entity
            LET targetEntity = FIRST(
                FOR e IN Entity
                    FILTER LOWER(e.name) == LOWER(@targetEntityName)
                    FILTER @targetEntityBertSchema == null OR @targetEntityBertSchema IN e.bert_schema
                    RETURN e._id
            )

            // Get articles that mention the target entity
            LET targetEntityArticles = (
                FOR ae IN article_entities
                    FILTER ae._to == targetEntity
                    FILTER @targetMinMentionCountInSharedArticle == null OR ae.ne_count >= @targetMinMentionCountInSharedArticle
                    
                    FOR a IN Article
                        FILTER ae._from == a._id
                        FILTER @sharedArticleStartDate == null OR a.date_added >= @sharedArticleStartDate
                        FILTER @sharedArticleEndDate == null OR a.date_added <= @sharedArticleEndDate
                        FILTER @sharedArticleCategory == null OR @sharedArticleCategory IN a.category
                        FILTER @sharedArticleSource == null OR a.default.source == @sharedArticleSource
                        
                        RETURN a._id
            )

            // Find other entities that appear in the same articles
            FOR articleId IN targetEntityArticles
                FOR ae IN article_entities
                    FILTER ae._from == articleId
                    FILTER ae._to != targetEntity
                    FILTER @coOccurringMinMentionCountInSharedArticle == null OR ae.ne_count >= @coOccurringMinMentionCountInSharedArticle

                    FOR e IN Entity
                        FILTER ae._to == e._id
                        FILTER @coOccurringEntityBertSchema == null OR @coOccurringEntityBertSchema IN e.bert_schema
                        
                        COLLECT entityId = e._id,
                                entityName = e.name
                        AGGREGATE sharedArticleCount = COUNT_DISTINCT(articleId)
                        
                        FILTER sharedArticleCount >= @minCoOccurrences
                        
                        SORT sharedArticleCount DESC
                        LIMIT @topNCoOccurringEntities
                        
                        RETURN {
                            coOccurringEntityId: entityId,
                            coOccurringEntityName: entityName,
                            sharedArticleCount: sharedArticleCount
                        }
        `;

        const cursor = await this.db.query(query, {
            targetEntityName,
            minCoOccurrences,
            topNCoOccurringEntities,
            targetEntityBertSchema,
            sharedArticleStartDate,
            sharedArticleEndDate,
            sharedArticleCategory,
            sharedArticleSource,
            targetMinMentionCountInSharedArticle,
            coOccurringEntityBertSchema,
            coOccurringMinMentionCountInSharedArticle
        });
        return await cursor.all();
    }

    private async handleGetPaginatedArticlesWithEntities(args: GetPaginatedArticlesWithEntitiesArgs): Promise<any> {
        const { 
            pageNumber,
            pageSize,
            topNEntitiesPerArticle = 5,
            startDate = null,
            endDate = null,
            category = null,
            source = null,
            filterByEntities = [],
            returnOnlyEntityBertSchema = null
        } = args;

        const query = `
            LET pageNumber = @pageNumber
            LET pageSize = @pageSize
            LET topNEntitiesPerArticle = @topNEntitiesPerArticle

            LET filterByEntities = @filterByEntities
            LET filterByEntityIds = (
                FOR e IN Entity
                    FILTER LOWER(e.name) IN (FOR name IN filterByEntities RETURN LOWER(name))
                    RETURN e._id
            )

            FOR articleDoc IN Article
                FILTER @startDate == null OR articleDoc.date_added >= @startDate
                FILTER @endDate == null OR articleDoc.date_added <= @endDate
                FILTER @category == null OR @category IN articleDoc.category
                FILTER @source == null OR articleDoc.default.source == @source

                FILTER LENGTH(filterByEntities) == 0 OR (
                    LENGTH(
                        FOR ae IN article_entities
                            FILTER ae._from == articleDoc._id
                            FILTER ae._to IN filterByEntityIds
                            LIMIT 1 RETURN 1
                    ) > 0
                )

                SORT articleDoc.date_added DESC
                LIMIT (pageNumber - 1) * pageSize, pageSize

                LET mentionedEntities = (
                    FOR ae IN article_entities
                        FILTER ae._from == articleDoc._id
                        FOR entityDoc IN Entity
                            FILTER ae._to == entityDoc._id

                            FILTER @returnOnlyEntityBertSchema == null OR @returnOnlyEntityBertSchema IN entityDoc.bert_schema

                            SORT ae.ne_tf DESC, ae.ne_count DESC
                            LIMIT topNEntitiesPerArticle
                            RETURN {
                                entityId: entityDoc._id,
                                entityName: entityDoc.name,
                                bertSchema: entityDoc.bert_schema,
                                mentionCount: ae.ne_count,
                                mentionTF: ae.ne_tf
                            }
                )

                FILTER LENGTH(mentionedEntities) > 0

                RETURN {
                    articleId: articleDoc._id,
                    title: articleDoc.default.title,
                    date_added: articleDoc.date_added,
                    summary: articleDoc.default_summary,
                    category: articleDoc.category,
                    source: articleDoc.default.source,
                    topEntities: mentionedEntities
                }
        `;

        const cursor = await this.db.query(query, {
            pageNumber,
            pageSize,
            topNEntitiesPerArticle,
            startDate,
            endDate,
            category,
            source,
            filterByEntities,
            returnOnlyEntityBertSchema
        });
        return await cursor.all();
    }

    // Basic ArangoDB handler methods
    private async handleQuery(args: any): Promise<any> {
        const { query, bindVars = {} } = args;
        const cursor = await this.db.query(query, bindVars);
        return await cursor.all();
    }

    private async handleInsert(args: any): Promise<any> {
        const { collection, document } = args;
        const result = await this.db.collection(collection).save(document);
        return result;
    }

    private async handleUpdate(args: any): Promise<any> {
        const { collection, key, update } = args;
        const result = await this.db.collection(collection).update(key, update);
        return result;
    }

    private async handleRemove(args: any): Promise<any> {
        const { collection, key } = args;
        const result = await this.db.collection(collection).remove(key);
        return result;
    }

    private async handleCollections(args: any): Promise<any> {
        const collections = await this.db.collections();
        return collections.map(col => ({
            name: col.name
        }));
    }

    private async handleCreateCollection(args: any): Promise<any> {
        const { name, type = 'document', waitForSync = false } = args;
        let collection;
        
        if (type === 'edge') {
            collection = await this.db.createEdgeCollection(name, { waitForSync });
        } else {
            collection = await this.db.createCollection(name, { waitForSync });
        }
        
        return {
            name: collection.name,
            type: type
        };
    }

    private async handleBackup(args: any): Promise<any> {
        const { outputDir, collection, docLimit } = args;
        const fs = await import('fs/promises');
        const path = await import('path');

        try {
            // Ensure output directory exists
            await fs.mkdir(outputDir, { recursive: true });

            let collections;
            if (collection) {
                collections = [this.db.collection(collection)];
            } else {
                collections = await this.db.collections();
            }

            const results = [];
            for (const col of collections) {
                const collectionName = col.name;
                let query = `FOR doc IN ${collectionName} RETURN doc`;
                
                if (docLimit) {
                    query += ` LIMIT ${docLimit}`;
                }

                const cursor = await this.db.query(query);
                const docs = await cursor.all();
                
                const fileName = path.join(outputDir, `${collectionName}.json`);
                await fs.writeFile(fileName, JSON.stringify(docs, null, 2));
                
                results.push({
                    collection: collectionName,
                    documentCount: docs.length,
                    fileName: fileName
                });
            }

            return {
                backupPath: outputDir,
                collections: results,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            throw new Error(`Backup failed: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
}
