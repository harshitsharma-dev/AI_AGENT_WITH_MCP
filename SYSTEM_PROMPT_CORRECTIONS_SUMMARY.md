# System Prompt Corrections Summary

## Before vs After Comparison

### Parameter Mapping Hints - BEFORE (Incorrect)
```
PARAMETER MAPPING HINTS:
- For entity searches: use 'entity' parameter for person/organization/location names
- For keyword searches: use 'keywords' parameter for search terms
- For entity analysis: use 'entity' parameter for entities to analyze
- For limits: use 'limit' parameter (typically 10-50)
- For pagination: use 'page' parameter when browsing results
```

### Parameter Mapping Hints - AFTER (Corrected)
```
PARAMETER MAPPING HINTS:
- For entity searches: use 'entityName' parameter for person/organization/location names
- For target entity searches: use 'targetEntityName' parameter (co-occurrence, keyword searches)
- For keyword searches: use 'keywords' parameter as array of strings ["term1", "term2"]
- For pagination: use 'pageNumber' (1-based) AND 'pageSize' parameters (both required)
- For top entities: use 'limit' parameter (required, typically 10-50)
- For dates: use 'startDate' and 'endDate' parameters (ISO format strings)
- For filtering: use 'category', 'source', 'minMentionCount', 'minMentionTF' parameters
```

### JSON Format Instructions - BEFORE (Generic)
```
2. If the request requires a tool, respond with JSON in one of these EXACT formats:
   Format 1: {"action": "use_tool", "tool": "tool_name", "arguments": {"parameter": "value"}}
   Format 2: {"action": "tool_name", "arguments": {"parameter": "value"}}
   Format 3: {"action": "tool_name"} (for tools with no parameters)
```

### JSON Format Instructions - AFTER (With Examples)
```
2. If the request requires a tool, respond with JSON in one of these EXACT formats:
   Format 1: {"action": "use_tool", "tool": "tool_name", "arguments": {"parameter": "value"}}
   Format 2: {"action": "tool_name", "arguments": {"parameter": "value"}}
   Format 3: {"action": "tool_name"} (for tools with no parameters)

   EXAMPLE TOOL CALLS:
   Entity search: {"action": "find_articles_by_entity", "arguments": {"entityName": "John Smith"}}
   Pagination: {"action": "get_paginated_articles_with_entities", "arguments": {"pageNumber": 1, "pageSize": 20}}
   Keywords: {"action": "find_articles_by_entity_and_keywords", "arguments": {"targetEntityName": "Tesla", "keywords": ["electric", "vehicle"]}}
   Top entities: {"action": "get_top_mentioned_entities", "arguments": {"limit": 10}}
```

## Key Corrections Made

### 1. Parameter Name Corrections
- ❌ `'entity'` → ✅ `'entityName'`
- ❌ `'page'` → ✅ `'pageNumber'` + `'pageSize'`
- ➕ Added `'targetEntityName'` for specific tools
- ➕ Added array syntax specification for `'keywords'`

### 2. Missing Required Parameters Added
- ✅ Both `pageNumber` AND `pageSize` required for pagination
- ✅ `limit` parameter required for top entities tool
- ✅ Array format clarification for keywords

### 3. Enhanced Guidance
- ✅ Added date parameter format (ISO strings)
- ✅ Added filtering parameter options
- ✅ Specified 1-based page numbering
- ✅ Added type specifications (arrays, numbers, strings)

### 4. Tool-Specific Examples
- ✅ Entity search with correct parameter name
- ✅ Pagination with both required parameters
- ✅ Keyword search with array syntax and targetEntityName
- ✅ Top entities with required limit parameter

## Impact of Changes

### Before (Failures Expected)
```json
// This would FAIL - wrong parameter name
{"action": "find_articles_by_entity", "arguments": {"entity": "John Smith"}}

// This would FAIL - missing pageSize parameter
{"action": "get_paginated_articles_with_entities", "arguments": {"page": 1}}

// This would FAIL - wrong parameter name
{"action": "find_co_occurring_entities", "arguments": {"entity": "Tesla"}}
```

### After (Correct Usage)
```json
// This will SUCCEED
{"action": "find_articles_by_entity", "arguments": {"entityName": "John Smith"}}

// This will SUCCEED - both required parameters
{"action": "get_paginated_articles_with_entities", "arguments": {"pageNumber": 1, "pageSize": 20}}

// This will SUCCEED - correct parameter name
{"action": "find_co_occurring_entities", "arguments": {"targetEntityName": "Tesla"}}

// This will SUCCEED - proper array syntax
{"action": "find_articles_by_entity_and_keywords", "arguments": {"targetEntityName": "Tesla", "keywords": ["electric", "car"]}}
```

## Tool Schema Reference

### find_articles_by_entity
- **Required:** `entityName` (string)
- **Optional:** `startDate`, `endDate`, `category`, `source`, `minMentionCount`, `minMentionTF`, `mentionBertSchema`

### get_paginated_articles_with_entities
- **Required:** `pageNumber` (number), `pageSize` (number)
- **Optional:** `topNEntitiesPerArticle`, `startDate`, `endDate`, `category`, `source`, `filterByEntities`, `returnOnlyEntityBertSchema`

### find_co_occurring_entities
- **Required:** `targetEntityName` (string)
- **Optional:** `minCoOccurrences`, `topNCoOccurringEntities`, `targetEntityBertSchema`, date/category filters

### find_articles_by_entity_and_keywords
- **Required:** `targetEntityName` (string), `keywords` (array of strings)
- **Optional:** `keywordOperator`, mention filters, date/category filters

### get_top_mentioned_entities
- **Required:** `limit` (number)
- **Optional:** `entityType`, article filters, mention filters, `entityBertSchema`

## Files Modified

1. ✅ `python_agent/app.py` - Updated `_build_tool_system_prompt()` method
2. ✅ `SYSTEM_PROMPT_ANALYSIS_REPORT.md` - Created comprehensive analysis
3. ✅ `SYSTEM_PROMPT_CORRECTIONS_SUMMARY.md` - This summary document

## Testing Recommendations

After these changes, test:
1. Entity searches with `entityName` parameter
2. Pagination with both `pageNumber` and `pageSize`
3. Keyword searches with array syntax
4. Co-occurrence searches with `targetEntityName`
5. Top entities with required `limit` parameter
