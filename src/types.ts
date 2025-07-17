import { CollectionType } from 'arangojs/collection';

// Type definitions for request arguments
export interface BackupArgs {
	outputDir: string;
	collection?: string;
	docLimit?: number;
}

export interface QueryArgs {
	query: string;
	bindVars?: Record<string, unknown>;
}

export interface CollectionDocumentArgs {
	collection: string;
	document: Record<string, unknown>;
}

export interface CollectionKeyArgs {
	collection: string;
	key: string;
}

export interface UpdateDocumentArgs extends CollectionKeyArgs {
	update: Record<string, unknown>;
}

export interface CreateCollectionArgs {
	name: string;
	type?: 'document' | 'edge'; // Changed from CollectionType to string literals
	waitForSync?: boolean;
}

// New tool type definitions for entity-based article queries
export interface FindArticlesByEntityArgs {
    entityName: string;
    startDate?: string | null;
    endDate?: string | null;
    category?: string | null;
    source?: string | null;
    minMentionCount?: number | null;
    minMentionTF?: number | null;
    mentionBertSchema?: string | null;
}

export interface GetTopMentionedEntitiesArgs {
    entityType?: string | null; // e.g., "PERSON", "ORGANIZATION", etc.
    limit: number;
    articleStartDate?: string | null;
    articleEndDate?: string | null;
    articleCategory?: string | null;
    articleSource?: string | null;
    minMentionCountPerArticle?: number | null;
    minMentionTFPerArticle?: number | null;
    entityBertSchema?: string | null;
}

export interface FindArticlesByEntityAndKeywordsArgs {
    targetEntityName: string;
    keywords: string[];
    keywordOperator?: string; // "AND" or "OR"
    minMentionCount?: number | null;
    minMentionTF?: number | null;
    mentionBertSchema?: string | null;
    startDate?: string | null;
    endDate?: string | null;
    category?: string | null;
    source?: string | null;
}

export interface FindCoOccurringEntitiesArgs {
    targetEntityName: string;
    minCoOccurrences?: number;
    topNCoOccurringEntities?: number;
    targetEntityBertSchema?: string | null;
    sharedArticleStartDate?: string | null;
    sharedArticleEndDate?: string | null;
    sharedArticleCategory?: string | null;
    sharedArticleSource?: string | null;
    targetMinMentionCountInSharedArticle?: number | null;
    coOccurringEntityBertSchema?: string | null;
    coOccurringMinMentionCountInSharedArticle?: number | null;
}

export interface GetPaginatedArticlesWithEntitiesArgs {
    pageNumber: number;
    pageSize: number;
    topNEntitiesPerArticle?: number;    startDate?: string | null;
    endDate?: string | null;
    category?: string | null;
    source?: string | null;
    filterByEntities?: string[];
    returnOnlyEntityBertSchema?: string | null;
}
