# System Prompt Analysis Report

## Analysis Date: June 9, 2025

This report analyzes the mismatches between the system prompt's parameter mapping hints and JSON format instructions in the Python agent's `app.py` file compared to the actual tool schemas defined in the MCP server.

## Critical Issues Identified

### 1. Parameter Name Mismatches

**Current System Prompt Issues:**
- Uses `'entity'` parameter for entity searches
- Uses `'page'` parameter for pagination
- Uses `'limit'` parameter for result limits
- Uses `'keywords'` parameter for search terms

**Actual Tool Schema Parameters:**
- `'entityName'` (not `'entity'`)
- `'pageNumber'` (not `'page'`)
- `'pageSize'` (required alongside pageNumber)
- `'targetEntityName'` (for tools like `find_co_occurring_entities`)
- `'keywords'` (correct, but array type not mentioned)

### 2. Missing Required Parameters

**System Prompt Missing:**
- `pageSize` parameter is required for pagination tools
- `limit` parameter is required for `get_top_mentioned_entities`
- Proper array type specification for `keywords` parameter

### 3. Incorrect Parameter Mapping Hints

**Current (Incorrect) Hints:**
```
- For entity searches: use 'entity' parameter for person/organization/location names
- For pagination: use 'page' parameter when browsing results
- For limits: use 'limit' parameter (typically 10-50)
```

**Should Be:**
```
- For entity searches: use 'entityName' parameter for person/organization/location names
- For target entity searches: use 'targetEntityName' parameter for co-occurrence and keyword tools
- For pagination: use 'pageNumber' and 'pageSize' parameters
- For top entities: use 'limit' parameter for get_top_mentioned_entities
```

### 4. Tool-Specific Parameter Issues

#### find_articles_by_entity
- **Correct:** `entityName` (string, required)
- **Current hint says:** `entity`

#### get_paginated_articles_with_entities  
- **Correct:** `pageNumber` (number, required), `pageSize` (number, required)
- **Current hint says:** `page`

#### find_co_occurring_entities
- **Correct:** `targetEntityName` (string, required)
- **Current hint says:** `entity`

#### find_articles_by_entity_and_keywords
- **Correct:** `targetEntityName` (string, required), `keywords` (array of strings, required)
- **Current hint says:** `entity`, doesn't specify array type

#### get_top_mentioned_entities
- **Correct:** `limit` (number, required)
- **Current hint:** Correct parameter name but doesn't mention it's required

### 5. JSON Format Examples Issues

**Current format examples are generic and don't show:**
- Required vs optional parameters
- Array parameter syntax
- Proper parameter names matching actual schemas
- Tool-specific parameter requirements

### 6. Server Configuration Clarification

**Port Configuration (Actually Correct):**
- `SERVER_URL = 'http://localhost:5001'` in HTML template is CORRECT
- HTML interface communicates with Python Flask agent on port 5001
- Python agent communicates with MCP server on port 3000
- No configuration issue - this is the proper architecture

## Impact Assessment

**High Impact Issues:**
1. **Tool calls will fail** due to incorrect parameter names (`entity` vs `entityName`)
2. **Pagination won't work** due to missing `pageSize` parameter and incorrect `page` vs `pageNumber`
3. **Required parameters missing** causing tool execution failures

**Medium Impact Issues:**
1. **Suboptimal tool usage** due to missing optional parameter guidance
2. **Type confusion** for array parameters like `keywords`

**Low Impact Issues:**
1. **Documentation inconsistencies** in parameter descriptions

## Recommended Fixes

### 1. Update Parameter Mapping Hints ✅ COMPLETED
Replace the current hints with accurate parameter names matching the actual tool schemas.

### 2. Fix JSON Format Examples ✅ COMPLETED
Provide tool-specific examples showing correct parameter names and types.

### 3. Add Required Parameter Documentation ✅ COMPLETED
Clearly indicate which parameters are required vs optional for each tool category.

### 4. Server Configuration ✅ VERIFIED CORRECT
Port configuration is actually correct - no changes needed.

### 5. Add Array Parameter Syntax ✅ COMPLETED
Show proper syntax for array parameters like `keywords: ["term1", "term2"]`.

## Testing Recommendations

After fixes:
1. Test entity search with corrected `entityName` parameter
2. Test pagination with both `pageNumber` and `pageSize` parameters
3. Test keyword searches with proper array syntax
4. Verify all required parameters are included in tool calls
5. Test server connectivity with corrected URLs

## Files Requiring Updates

1. `python_agent/app.py` - System prompt method `_build_tool_system_prompt()` ✅ COMPLETED
2. `python_agent/index.html` - Server URL configuration ✅ VERIFIED CORRECT
3. Consider adding parameter validation in tool selection logic

## Summary of Changes Made

### ✅ Fixed Parameter Mapping Hints
- Changed `'entity'` → `'entityName'`
- Added `'targetEntityName'` for co-occurrence and keyword tools
- Changed `'page'` → `'pageNumber'` and added required `'pageSize'`
- Added proper array syntax for `'keywords'` parameter
- Added date and filtering parameter guidance

### ✅ Enhanced JSON Format Instructions
- Added specific tool call examples with correct parameter names
- Showed proper array syntax: `["item1", "item2"]`
- Demonstrated required parameter combinations
- Added pagination example with both required parameters

### ✅ Improved Parameter Type Guidance
- Specified numeric vs string parameter types
- Clarified array parameter syntax
- Added date format specifications (ISO format)
- Listed optional filtering parameters

## Expected Improvements

After these fixes, the Python agent should:
1. ✅ Generate correct tool calls with proper parameter names
2. ✅ Include all required parameters (especially for pagination)
3. ✅ Use proper array syntax for keywords
4. ✅ Provide better tool usage guidance to the LLM
5. ✅ Reduce tool call failures due to parameter mismatches
