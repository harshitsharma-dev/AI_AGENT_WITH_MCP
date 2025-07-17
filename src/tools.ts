import { Tool } from '@modelcontextprotocol/sdk/types.js';
import { CollectionType } from 'arangojs/collection';

export function createToolDefinitions(): Tool[] {
	return [
		{
			name: API_TOOLS.QUERY as string,
			description: 'Execute an AQL query',
			inputSchema: {
				type: 'object',
				properties: {
					query: {
						type: 'string',
						description: 'AQL query string',
					},
					bindVars: {
						type: 'object',
						description: 'Query bind variables',
						additionalProperties: { type: 'object' },
					},
				},
				required: ['query'],
			},
		},
		{
			name: API_TOOLS.INSERT as string,
			description: 'Insert a document into a collection',
			inputSchema: {
				type: 'object',
				properties: {
					collection: {
						type: 'string',
						description: 'Collection name',
					},
					document: {
						type: 'object',
						description: 'Document to insert',
						additionalProperties: { type: 'object' },
					},
				},
				required: ['collection', 'document'],
			},
		},
		{
			name: API_TOOLS.UPDATE as string,
			description: 'Update a document in a collection',
			inputSchema: {
				type: 'object',
				properties: {
					collection: {
						type: 'string',
						description: 'Collection name',
					},
					key: {
						type: 'string',
						description: 'Document key',
					},
					update: {
						type: 'object',
						description: 'Update object',
						additionalProperties: { type: 'object' },
					},
				},
				required: ['collection', 'key', 'update'],
			},
		},
		{
			name: API_TOOLS.REMOVE as string,
			description: 'Remove a document from a collection',
			inputSchema: {
				type: 'object',
				properties: {
					collection: {
						type: 'string',
						description: 'Collection name',
					},
					key: {
						type: 'string',
						description: 'Document key',
					},
				},
				required: ['collection', 'key'],
			},
		},
		{
			name: API_TOOLS.COLLECTIONS as string,
			description: 'List all collections in the database',
			inputSchema: {
				type: 'object',
				properties: {},
			},
		},
		{
			name: API_TOOLS.CREATE_COLLECTION as string,
			description: 'Create a new collection in the database',
			inputSchema: {
				type: 'object',
				properties: {
					name: {
						type: 'string',
						description: 'Name of the collection to create',
					},
					type: {
						type: 'string',
						description: 'Type of collection to create ("document" or "edge")',
						default: 'document',
						enum: ['document', 'edge'],
					},
					waitForSync: {
						type: 'boolean',
						description: 'If true, wait for data to be synchronized to disk before returning',
						default: false,
					},
				},
				required: ['name'],
			},
		},
		{
			name: API_TOOLS.BACKUP as string,
			description: 'Backup collections to JSON files.',
			inputSchema: {
				type: 'object',
				properties: {
					outputDir: {
						type: 'string',
						description: 'An absolute directory path to store backup files',
						default: './backup',
						optional: true,
					},
					collection: {
						type: 'string',
						description: 'Collection name to backup. If not provided, backs up all collections.',
						optional: true,
					},
					docLimit: {
						type: 'integer',
						description: 'Limit the number of documents to backup. If not provided, backs up all documents.',
						optional: true,
					},
				},
				required: ['outputDir'],
			},
		},		{
			name: API_TOOLS.FIND_ARTICLES_BY_ENTITY as string,
			description: 'Find all articles mentioning a specific entity with comprehensive filters',
			inputSchema: {
				type: 'object',
				properties: {
					entityName: {
						type: 'string',
						description: 'Name of the entity to search for',
					},
					startDate: {
						type: 'string',
						description: 'Start date filter (ISO format)',
					},
					endDate: {
						type: 'string',
						description: 'End date filter (ISO format)',
					},
					category: {
						type: 'string',
						description: 'Article category filter',
					},
					source: {
						type: 'string',
						description: 'Article source filter',
					},
					minMentionCount: {
						type: 'number',
						description: 'Minimum mention count in article',
					},
					minMentionTF: {
						type: 'number',
						description: 'Minimum mention term frequency',
					},
					mentionBertSchema: {
						type: 'string',
						description: 'Filter by BERT schema in edge (e.g., PERSON)',
					}
				},
				required: ['entityName'],
			},
		},		{
			name: API_TOOLS.GET_TOP_MENTIONED_ENTITIES as string,
			description: 'Get the top N most mentioned entities with comprehensive filters',
			inputSchema: {
				type: 'object',
				properties: {
					entityType: {
						type: 'string',
						description: 'Type of entity (e.g., PERSON, ORGANIZATION)',
					},
					limit: {
						type: 'number',
						description: 'Number of top entities to return',
					},
					articleStartDate: {
						type: 'string',
						description: 'Article start date filter',
					},
					articleEndDate: {
						type: 'string',
						description: 'Article end date filter',
					},
					articleCategory: {
						type: 'string',
						description: 'Article category filter',
					},
					articleSource: {
						type: 'string',
						description: 'Article source filter',
					},
					minMentionCountPerArticle: {
						type: 'number',
						description: 'Minimum mention count per article',
					},
					minMentionTFPerArticle: {
						type: 'number',
						description: 'Minimum mention TF per article',
					},
					entityBertSchema: {
						type: 'string',
						description: 'Entity BERT schema filter',
					}
				},
				required: ['limit'],
			},
		},		{
			name: API_TOOLS.FIND_ARTICLES_BY_ENTITY_AND_KEYWORDS as string,
			description: 'Find articles mentioning an entity AND containing keywords with filters',
			inputSchema: {
				type: 'object',
				properties: {
					targetEntityName: {
						type: 'string',
						description: 'Name of the target entity',
					},
					keywords: {
						type: 'array',
						items: { type: 'string' },
						description: 'Keywords to search for in article content',
					},
					keywordOperator: {
						type: 'string',
						description: 'Keyword operator: AND or OR',
						default: 'OR',
					},
					minMentionCount: {
						type: 'number',
						description: 'Minimum mention count',
					},
					minMentionTF: {
						type: 'number',
						description: 'Minimum mention TF',
					},
					mentionBertSchema: {
						type: 'string',
						description: 'BERT schema filter for mentions',
					},
					startDate: {
						type: 'string',
						description: 'Article start date filter',
					},
					endDate: {
						type: 'string',
						description: 'Article end date filter',
					},
					category: {
						type: 'string',
						description: 'Article category filter',
					},
					source: {
						type: 'string',
						description: 'Article source filter',
					}
				},
				required: ['targetEntityName', 'keywords'],
			},
		},		{
			name: API_TOOLS.FIND_CO_OCCURRING_ENTITIES as string,
			description: 'Find entities frequently co-occurring with a target entity with comprehensive filters',
			inputSchema: {
				type: 'object',
				properties: {
					targetEntityName: {
						type: 'string',
						description: 'Name of the target entity',
					},
					minCoOccurrences: {
						type: 'number',
						description: 'Minimum number of shared articles',
						default: 1,
					},
					topNCoOccurringEntities: {
						type: 'number',
						description: 'Maximum number of co-occurring entities to return',
						default: 10,
					},
					targetEntityBertSchema: {
						type: 'string',
						description: 'Target entity BERT schema filter',
					},
					sharedArticleStartDate: {
						type: 'string',
						description: 'Shared article start date filter',
					},
					sharedArticleEndDate: {
						type: 'string',
						description: 'Shared article end date filter',
					},
					sharedArticleCategory: {
						type: 'string',
						description: 'Shared article category filter',
					},
					sharedArticleSource: {
						type: 'string',
						description: 'Shared article source filter',
					},
					targetMinMentionCountInSharedArticle: {
						type: 'number',
						description: 'Target entity min mention count in shared articles',
					},
					coOccurringEntityBertSchema: {
						type: 'string',
						description: 'Co-occurring entity BERT schema filter',
					},
					coOccurringMinMentionCountInSharedArticle: {
						type: 'number',
						description: 'Co-occurring entity min mention count in shared articles',
					}
				},
				required: ['targetEntityName'],
			},
		},		{
			name: API_TOOLS.GET_PAGINATED_ARTICLES_WITH_ENTITIES as string,
			description: 'Get paginated articles with their top mentioned entities and comprehensive filters',
			inputSchema: {
				type: 'object',
				properties: {
					pageNumber: {
						type: 'number',
						description: 'Page number (starting from 1)',
					},
					pageSize: {
						type: 'number',
						description: 'Number of articles per page',
					},
					topNEntitiesPerArticle: {
						type: 'number',
						description: 'Number of top entities to include per article',
						default: 5,
					},
					startDate: {
						type: 'string',
						description: 'Article start date filter',
					},
					endDate: {
						type: 'string',
						description: 'Article end date filter',
					},
					category: {
						type: 'string',
						description: 'Article category filter',
					},
					source: {
						type: 'string',
						description: 'Article source filter',
					},
					filterByEntities: {
						type: 'array',
						items: { type: 'string' },
						description: 'Filter by specific entity names',
					},
					returnOnlyEntityBertSchema: {
						type: 'string',
						description: 'Return only entities with specific BERT schema',
					}
				},
				required: ['pageNumber', 'pageSize'],
			},
		},
	];
}

export enum API_TOOLS {
	QUERY = 'query',
	INSERT = 'insert',
	UPDATE = 'update',
	REMOVE = 'remove',
	COLLECTIONS = 'collections',
	CREATE_COLLECTION = 'create_collection',
	BACKUP = 'backup',
	FIND_ARTICLES_BY_ENTITY = 'find_articles_by_entity',
	GET_TOP_MENTIONED_ENTITIES = 'get_top_mentioned_entities',
	FIND_ARTICLES_BY_ENTITY_AND_KEYWORDS = 'find_articles_by_entity_and_keywords',
	FIND_CO_OCCURRING_ENTITIES = 'find_co_occurring_entities',
	GET_PAGINATED_ARTICLES_WITH_ENTITIES = 'get_paginated_articles_with_entities'
}
