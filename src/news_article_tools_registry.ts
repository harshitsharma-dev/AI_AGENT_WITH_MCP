// Registry of currently implemented ArangoDB MCP graph analysis tools for articles and documents.
// This registry contains only the 7 tools that are actually implemented in handlers.ts.
// Update this file when adding, removing, or renaming any graph analysis tool or handler.
//
// NOTE: Previous flexible tools (get_recent_articles, search_articles_by_category, etc.) 
// have been removed and are no longer available. The current tools focus on graph-based
// relationship discovery and traversal using CRLR and path-based algorithms.

export interface NewsArticleToolRegistryEntry {
  toolName: string;
  handlerName: string;
  description: string;
}

export const NEWS_ARTICLE_TOOLS: NewsArticleToolRegistryEntry[] = [
  {
    toolName: 'get_crlr_related_articles_unset',
    handlerName: 'handleCrlrRelatedArticlesUnset',
    description: 'Get related articles using CRLR algorithm without detailed content (UNSET), returning minimal article data for graph traversal.'
  },
  {
    toolName: 'get_crlr_related_articles',
    handlerName: 'handleCrlrRelatedArticles',
    description: 'Get related articles using CRLR (Content Relationship Link Ranking) algorithm with full content details.'
  },
  {
    toolName: 'get_path_related_articles_unset',
    handlerName: 'handlePathRelatedArticlesUnset',
    description: 'Get related articles using path-based graph traversal without detailed content (UNSET), within a time window.'
  },
  {
    toolName: 'get_path_related_articles',
    handlerName: 'handlePathRelatedArticles',
    description: 'Get related articles using path-based graph traversal with full content details, filtered by category and time.'
  },
  {
    toolName: 'get_related_articles_graph',
    handlerName: 'handleRelatedArticlesGraph',
    description: 'Get related articles using graph-based analysis with topic terms, category filtering, and time constraints.'
  },  {
    toolName: 'get_crlr_related_docs',
    handlerName: 'handleCrlrRelatedDocs',
    description: 'Get related documents using CRLR algorithm for cross-document relationship discovery.'
  },
  {
    toolName: 'get_path_related_docs',
    handlerName: 'handlePathRelatedDocs',
    description: 'Get related documents using path-based graph traversal for document relationship analysis.'
  },
  {
    toolName: 'get_semantic_entity_articles',
    handlerName: 'handleSemanticEntityArticles',
    description: 'Find articles semantically related to entities using ChromaDB embeddings for intelligent content discovery based on natural language queries.'
  }
];
