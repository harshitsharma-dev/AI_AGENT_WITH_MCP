// Utility functions for building field projections in ArangoDB queries

/**
 * Build article projection object based on detail level and optional field list
 * @param detail The detail level ('minimal', 'summary', or 'full') 
 * @param projection Optional array of specific fields to include
 * @returns AQL object definition for article projection
 */
export function buildArticleProjection(detail: string, projection?: string[]): string {
    if (projection && projection.length > 0) {
        return `{ ${projection.map(f => `${f}: article.${f}`).join(', ')} }`;
    }

    switch (detail) {
        case 'minimal':
            return `{
                _key: article._key,
                title: article.default.title,
                url: article.default.url,
                epoch_time: article.default.epoch_time
            }`;

        case 'summary':
            return `{
                _key: article._key,
                title: article.default.title,
                url: article.default.url,
                summary: article.default_summary,
                author: article.author,
                category: article.category,
                subcategory: article.subcategory,
                source_name: article.default.source_name,
                epoch_time: article.default.epoch_time,
                image: article.default.image,
                thumbnail: article.default?.thumbnail,
                source_tags: article.source_tags
            }`;

        case 'full':
        default:
            return 'article';
    }
}

/**
 * Build document projection object based on detail level and optional field list
 * @param detail The detail level ('minimal', 'summary', or 'full')
 * @param projection Optional array of specific fields to include  
 * @returns AQL object definition for document projection
 */
export function buildDocumentProjection(detail: string, projection?: string[]): string {
    if (projection && projection.length > 0) {
        return `{ ${projection.map(f => `${f}: doc.${f}`).join(', ')} }`;
    }

    switch (detail) {
        case 'minimal':
            return `{
                _key: doc._key,
                title: doc.title,
                url: doc.url,
                epoch_published: doc.epoch_published
            }`;

        case 'summary': 
            return `{
                _key: doc._key,
                title: doc.title,
                url: doc.url,
                description: doc.description,
                author: doc.author,
                category: doc.category,
                subcategory: doc.subcategory,
                source_name: doc.source_name,
                epoch_published: doc.epoch_published,
                date_published: doc.date_published,
                image: doc.image,
                thumbnail: doc.thumbnail,
                source_tags: doc.source_tags
            }`;

        case 'full':
        default:
            return 'doc';
    }
}
