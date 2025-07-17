
# Fix OpenMP library conflict on Windows (must be set before importing scientific libraries)
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
# from flask_caching import Cache


import json
import requests
import sys
import traceback
from flask import Flask, request, jsonify, render_template_string, send_file
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import logging
import time
import threading
from datetime import datetime, timedelta
import difflib
import re
from collections import defaultdict
import spacy
from dateutil import parser as date_parser
import calendar

# Set up detailed logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

MCP_URL = "http://localhost:6001"

@dataclass
class MCPTool:
    """MCP Tool representation matching your API format"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ExtractedEntities:
    """Extracted entities from user query"""
    dates: List[str] = None
    date_ranges: List[Tuple[str, str]] = None
    time_keywords: List[str] = None
    names: List[str] = None
    categories: List[str] = None
    search_terms: List[str] = None
    authors: List[str] = None
    keywords: List[str] = None
    numbers: List[int] = None
    sources: List[str] = None
    locations: List[str] = None
    intent: str = None
    
    def __post_init__(self):
        if self.dates is None: self.dates = []
        if self.date_ranges is None: self.date_ranges = []
        if self.time_keywords is None: self.time_keywords = []
        if self.names is None: self.names = []
        if self.categories is None: self.categories = []
        if self.search_terms is None: self.search_terms = []
        if self.authors is None: self.authors = []
        if self.keywords is None: self.keywords = []
        if self.numbers is None: self.numbers = []
        if self.sources is None: self.sources = []
        if self.locations is None: self.locations = []

class EntityExtractor:
    """Advanced NLP entity extraction for news chatbot queries"""
    
    def __init__(self):
        # Try to load spaCy model, fallback to simple extraction if not available
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
        except:
            logger.warning("spaCy model not available, using simple extraction")
            self.nlp = None
            self.spacy_available = False
        
        # Date/time related keywords
        self.time_keywords = {
            'recent': ['recent', 'latest', 'new', 'current', 'fresh'],
            'past': ['past', 'previous', 'earlier', 'before', 'ago'],
            'today': ['today', 'today\'s'],
            'yesterday': ['yesterday', 'yesterday\'s'],
            'week': ['week', 'weekly', 'this week', 'last week'],
            'month': ['month', 'monthly', 'this month', 'last month'],
            'year': ['year', 'yearly', 'this year', 'last year'],
            'range': ['from', 'to', 'between', 'since', 'until', 'during']
        }
        
        # Intent keywords
        self.intent_keywords = {
            'search': ['find', 'search', 'look for', 'show me', 'get', 'fetch'],
            'list': ['list', 'all', 'show all', 'browse', 'display'],
            'related': ['related', 'similar', 'connected', 'linked'],
            'category': ['category', 'topic', 'section', 'type'],
            'author': ['author', 'writer', 'journalist', 'by'],
            'date': ['date', 'time', 'when', 'published'],
            'recent': ['recent', 'latest', 'new'],
            'specific': ['specific', 'particular', 'exact']
        }
        
        # News categories (extend based on your data)
        self.news_categories = [
            'politics', 'sports', 'technology', 'business', 'entertainment',
            'health', 'science', 'world', 'national',
            'opinion', 'lifestyle', 'travel', 'food', 'fashion', 'education'
        ]
        
        # Common news sources (extend based on your data)
        # self.news_sources = [
        #     'cnn', 'bbc', 'reuters', 'ap', 'nytimes', 'washingtonpost',
        #     'guardian', 'fox', 'npr', 'bloomberg', 'wsj', 'usa today'
        # ]
        self.news_sources = [
            'zee_mews', 'wion'
        ]
        
        # Common locations (extend based on your data)
        self.locations = [
            'usa', 'uk', 'canada', 'australia', 'europe', 'asia',
            'africa', 'america', 'china', 'russia', 'india', 'japan',
            'new york', 'london', 'paris', 'tokyo', 'washington', 'israel'
        ]
        
        # Regex patterns
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        self.number_pattern = r'\b\d+\b'
    
    def extract_entities(self, query: str) -> ExtractedEntities:
        """Extract all relevant entities from user query"""
        query_lower = query.lower()
        entities = ExtractedEntities()
        
        # Extract intent
        entities.intent = self._extract_intent(query_lower)
        
        # Extract dates and time-related info
        entities.dates = self._extract_dates(query)
        entities.date_ranges = self._extract_date_ranges(query)
        entities.time_keywords = self._extract_time_keywords(query_lower)
        
        # Extract names and entities using spaCy if available
        if self.spacy_available:
            entities.names, entities.search_terms = self._extract_names_spacy(query)
        else:
            entities.names, entities.search_terms = self._extract_names_simple(query)
        
        # Extract categories
        entities.categories = self._extract_categories(query_lower)
        
        # Extract sources
        entities.sources = self._extract_sources(query_lower)
        
        # Extract locations
        entities.locations = self._extract_locations(query_lower)
        
        # Extract authors
        entities.authors = self._extract_authors(query)
        
        # Extract keywords
        entities.keywords = self._extract_keywords(query_lower)
        
        # Extract numbers
        entities.numbers = self._extract_numbers(query)
        
        logger.info(f"EXTRACTED ENTITIES: {entities}")
        return entities
    
    def _extract_intent(self, query: str) -> str:
        """Extract primary intent from query"""
        intent_scores = defaultdict(int)
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    intent_scores[intent] += 1
        
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        return 'search'  # default intent
    
    def _extract_dates(self, query: str) -> List[str]:
        """Extract explicit dates from query"""
        dates = []
        
        # Try regex patterns first
        for pattern in self.date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            dates.extend(matches)
        
        # Try dateutil parser for more complex dates
        words = query.split()
        for i in range(len(words)):
            for j in range(i+1, min(i+4, len(words)+1)):
                phrase = ' '.join(words[i:j])
                try:
                    parsed_date = date_parser.parse(phrase, fuzzy=True)
                    if parsed_date:
                        dates.append(parsed_date.strftime('%Y-%m-%d'))
                except:
                    continue
        
        return list(set(dates))
    
    def _extract_date_ranges(self, query: str) -> List[Tuple[str, str]]:
        """Extract date ranges from query"""
        ranges = []
        query_lower = query.lower()
        
        # Look for range indicators
        range_patterns = [
            r'from\s+(.+?)\s+to\s+(.+?)(?:\s|$)',
            r'between\s+(.+?)\s+and\s+(.+?)(?:\s|$)',
            r'since\s+(.+?)(?:\s|$)',
            r'until\s+(.+?)(?:\s|$)'
        ]
        
        for pattern in range_patterns:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                try:
                    if 'since' in pattern or 'until' in pattern:
                        date_str = match.group(1)
                        parsed_date = date_parser.parse(date_str, fuzzy=True)
                        if 'since' in pattern:
                            ranges.append((parsed_date.strftime('%Y-%m-%d'), 'now'))
                        else:
                            ranges.append(('', parsed_date.strftime('%Y-%m-%d')))
                    else:
                        start_date = date_parser.parse(match.group(1), fuzzy=True)
                        end_date = date_parser.parse(match.group(2), fuzzy=True)
                        ranges.append((start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
                except:
                    continue
        
        return ranges
    
    def _extract_time_keywords(self, query: str) -> List[str]:
        """Extract time-related keywords"""
        found_keywords = []
        
        for category, keywords in self.time_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    found_keywords.append(category)
                    break
        
        return found_keywords
    
    def _extract_names_spacy(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract person names and other entities using spaCy"""
        doc = self.nlp(query)
        names = []
        search_terms = []
        
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                names.append(ent.text)
            elif ent.label_ in ["ORG", "GPE", "EVENT"]:
                search_terms.append(ent.text)
        
        return names, search_terms
    
    def _extract_names_simple(self, query: str) -> Tuple[List[str], List[str]]:
        """Simple name extraction without spaCy"""
        # Look for capitalized words that might be names
        words = query.split()
        names = []
        search_terms = []
        
        for word in words:
            if word[0].isupper() and len(word) > 2 and word.isalpha():
                if any(indicator in query.lower() for indicator in ['by ', 'author ', 'written by']):
                    names.append(word)
                else:
                    search_terms.append(word)
        
        return names, search_terms
    
    def _extract_categories(self, query: str) -> List[str]:
        """Extract news categories from query"""
        found_categories = []
        
        for category in self.news_categories:
            if category in query:
                found_categories.append(category)
        
        return found_categories
    
    def _extract_sources(self, query: str) -> List[str]:
        """Extract news sources from query"""
        found_sources = []
        
        for source in self.news_sources:
            if source in query:
                found_sources.append(source)
        
        return found_sources
    
    def _extract_locations(self, query: str) -> List[str]:
        """Extract locations from query"""
        found_locations = []
        
        for location in self.locations:
            if location in query:
                found_locations.append(location)
        
        return found_locations
    
    def _extract_authors(self, query: str) -> List[str]:
        """Extract author names from query"""
        authors = []
        query_lower = query.lower()
        
        # Look for author indicators
        author_patterns = [
            r'by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'author\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'written\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in author_patterns:
            matches = re.findall(pattern, query)
            authors.extend(matches)
        
        return authors
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        
        words = re.findall(r'\b[a-zA-Z]+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _extract_numbers(self, query: str) -> List[int]:
        """Extract numbers from query"""
        numbers = re.findall(self.number_pattern, query)
        return [int(num) for num in numbers]

class ToolCategorizer:
    """Categorize tools by their functionality and create mappings"""
    
    def __init__(self):
        self.tool_categories = {
            'search': {
                'tools': [
                    'flexible_fulltext_search_articles',
                    'flexible_fulltext_search_documents',
                    'flexible_search_articles_by_category',
                    'flexible_search_articles_by_author',
                    'flexible_articles_by_entity'
                ],
                'keywords': ['search', 'find', 'look for', 'get'],
                'entities': ['search_terms', 'keywords', 'categories', 'authors', 'names']
            },
            'date_time': {
                'tools': [
                    'flexible_articles_by_date_range',
                    'flexible_documents_by_date_range',
                    'flexible_recent_articles',
                    'get_system_time'
                ],
                'keywords': ['date', 'time', 'recent', 'latest', 'when', 'published'],
                'entities': ['dates', 'date_ranges', 'time_keywords']
            },
            'list_browse': {
                'tools': [
                    'flexible_paginated_article_list',
                    'flexible_list_authors',
                    'flexible_list_categories',
                    'flexible_list_document_authors',
                    'flexible_list_document_categories'
                ],
                'keywords': ['list', 'all', 'show all', 'browse', 'display'],
                'entities': ['keywords']
            },
            'specific_retrieval': {
                'tools': [
                    'flexible_article_by_key',
                    'flexible_document_by_key'
                ],
                'keywords': ['specific', 'particular', 'exact', 'id', 'key'],
                'entities': ['keywords', 'numbers']
            },
            'related_content': {
                'tools': [
                    'get_crlr_related_articles',
                    'get_path_related_articles',
                    'get_related_articles_graph',
                    'get_crlr_related_docs',
                    'get_path_related_docs',
                    'get_crlr_related_articles_unset',
                    'get_path_related_articles_unset'
                ],
                'keywords': ['related', 'similar', 'connected', 'linked'],
                'entities': ['search_terms', 'keywords']
            },
            'association_search': {
                'tools': [
                    'find_articles_by_author_date',
                    'find_articles_by_author_category',
                    'find_articles_by_author_source',
                    'find_articles_by_category_date',
                    'find_articles_by_category_source',
                    'find_articles_by_source_date',
                    'find_articles_by_location_date',
                    'find_articles_by_location_category'
                ],
                'keywords': ['by author', 'by category', 'by source', 'by location', 'written by', 'in category', 'from source'],
                'entities': ['authors', 'categories', 'sources', 'locations', 'dates']
            },
            'multi_entity_search': {
                'tools': [
                    'find_articles_by_author_category_date',
                    'find_articles_by_author_source_date',
                    'find_articles_by_author_source_category',
                    'find_articles_by_category_source_date',
                    'find_articles_by_location_category_date',
                    'find_articles_by_location_source_date',
                    'find_articles_by_location_source_category'
                ],
                'keywords': ['author and category', 'source and date', 'location and category', 'multiple criteria'],
                'entities': ['authors', 'categories', 'sources', 'locations', 'dates']
            },
            'complex_association_search': {
                'tools': [
                    'find_articles_by_author_category_source_date',
                    'find_articles_by_location_category_source_date'
                ],
                'keywords': ['complex search', 'multiple filters', 'all criteria', 'comprehensive search'],
                'entities': ['authors', 'categories', 'sources', 'locations', 'dates']
            },
            'analysis_discovery': {
                'tools': [
                    'analyze_article_associations',
                    'discover_missing_associations',
                    'suggest_related_searches'
                ],
                'keywords': ['analyze', 'discover', 'patterns', 'associations', 'trends', 'suggestions'],
                'entities': ['keywords', 'analysis_terms']
            },
            'database_ops': {
                'tools': [
                    'arango_query',
                    'arango_insert',
                    'arango_update',
                    'arango_remove',
                    'arango_backup',
                    'arango_list_collections',
                    'arango_create_collection'
                ],
                'keywords': ['database', 'query', 'insert', 'update', 'delete'],
                'entities': ['keywords']
            },
            'graph_analysis': {
                'tools': [
                    'get_document_edges'
                ],
                'keywords': ['edges', 'graph', 'connections'],
                'entities': ['keywords']
            }
        }
        
        # Create reverse mapping
        self.tool_to_category = {}
        for category, info in self.tool_categories.items():
            for tool in info['tools']:
                self.tool_to_category[tool] = category
    
    def get_relevant_categories(self, entities: ExtractedEntities) -> List[str]:
        """Get relevant tool categories based on extracted entities"""
        relevant_categories = []
        
        # Map intent to categories
        intent_mapping = {
            'search': ['search', 'association_search', 'date_time'],
            'list': ['list_browse'],
            'related': ['related_content'],
            'category': ['search', 'association_search'],
            'author': ['search', 'association_search'],
            'date': ['date_time', 'association_search'],
            'recent': ['date_time'],
            'specific': ['specific_retrieval'],
            'analyze': ['analysis_discovery'],
            'discover': ['analysis_discovery']
        }
        
        if entities.intent in intent_mapping:
            relevant_categories.extend(intent_mapping[entities.intent])
        
        # Check entity types for additional categories
        if entities.dates or entities.date_ranges or entities.time_keywords:
            relevant_categories.extend(['date_time', 'association_search'])
        
        if entities.categories or entities.authors or entities.search_terms:
            relevant_categories.extend(['search', 'association_search'])
            
        # Check for multi-entity queries
        entity_count = 0
        if entities.authors: entity_count += 1
        if entities.categories: entity_count += 1
        if entities.sources: entity_count += 1
        if entities.locations: entity_count += 1
        if entities.dates or entities.date_ranges: entity_count += 1
        
        if entity_count >= 2:
            relevant_categories.append('multi_entity_search')
        if entity_count >= 3:
            relevant_categories.append('complex_association_search')
        
        # Check for analysis keywords
        analysis_keywords = ['analyze', 'pattern', 'trend', 'association', 'discover', 'suggest']
        query_text = (entities.search_terms or []) + (entities.keywords or [])
        if any(keyword in ' '.join(query_text).lower() for keyword in analysis_keywords):
            relevant_categories.append('analysis_discovery')
        
        if not relevant_categories:
            relevant_categories = ['search', 'list_browse']  # default
        
        return list(set(relevant_categories))

class SmartToolSelector:
    """Select the most appropriate tools based on entities and context"""
    
    def __init__(self, tools: Dict[str, MCPTool]):
        self.tools = tools
        self.categorizer = ToolCategorizer()
        self.entity_extractor = EntityExtractor()
    
    def select_tools(self, query: str) -> Dict[str, Any]:
        """Select the most relevant tools for a query"""
        entities = self.entity_extractor.extract_entities(query)
        relevant_categories = self.categorizer.get_relevant_categories(entities)
        
        selected_tools = {}
        tool_scores = defaultdict(int)
        
        # Score tools based on categories
        for category in relevant_categories:
            if category in self.categorizer.tool_categories:
                for tool_name in self.categorizer.tool_categories[category]['tools']:
                    if tool_name in self.tools:
                        tool_scores[tool_name] += 10
        
        # Additional scoring based on specific entities
        for tool_name, tool in self.tools.items():
            score = tool_scores[tool_name]
            
            # Date-related tools
            if (entities.dates or entities.date_ranges or 'recent' in entities.time_keywords):
                if 'date' in tool_name or 'recent' in tool_name:
                    score += 5
            
            # Search tools
            if entities.search_terms or entities.keywords:
                if 'search' in tool_name or 'fulltext' in tool_name:
                    score += 5
            
            # Category tools
            if entities.categories:
                if 'category' in tool_name:
                    score += 5
            
            # Author tools
            if entities.authors:
                if 'author' in tool_name:
                    score += 5
            
            if score > 0:
                tool_scores[tool_name] = score
        
        # Select top tools (max 3-5 to avoid overwhelming LLM)
        sorted_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        top_tools = sorted_tools[:5]
        
        for tool_name, score in top_tools:
            selected_tools[tool_name] = {
                'tool': self.tools[tool_name],
                'score': score,
                'category': self.categorizer.tool_to_category.get(tool_name, 'other')
            }
        
        return {
            'entities': entities,
            'relevant_categories': relevant_categories,
            'selected_tools': selected_tools,
            'tool_count': len(selected_tools)
        }
    
    def build_optimized_context(self, selection_result: Dict[str, Any]) -> str:
        """Build optimized context for LLM with full tool descriptions"""
        entities = selection_result['entities']
        selected_tools = selection_result['selected_tools']
        
        context_parts = []
        
        # Add extracted entities summary
        context_parts.append("EXTRACTED FROM QUERY:")
        if entities.intent:
            context_parts.append(f"Intent: {entities.intent}")
        if entities.dates:
            context_parts.append(f"Dates: {entities.dates}")
        if entities.categories:
            context_parts.append(f"Categories: {entities.categories}")
        if entities.authors:
            context_parts.append(f"Authors: {entities.authors}")
        if entities.search_terms:
            context_parts.append(f"Search terms: {entities.search_terms}")
        
        # Add full list of all available tools
        context_parts.append("\nALL AVAILABLE TOOLS:")
        context_parts.append("=" * 40)
        for tool_name, tool in self.tools.items():
            context_parts.append(f"\nTool: {tool_name}")
            context_parts.append(f"Description: {tool.description}")
            if tool.inputSchema and 'properties' in tool.inputSchema:
                properties = tool.inputSchema['properties']
                required = tool.inputSchema.get('required', [])
                
                if required:
                    context_parts.append("Required parameters:")
                    for param in required:
                        if param in properties:
                            prop_info = properties[param]
                            param_desc = f"  - {param} ({prop_info.get('type', 'unknown')})"
                            if 'description' in prop_info:
                                param_desc += f": {prop_info['description']}"
                            context_parts.append(param_desc)
                
                optional_params = [p for p in properties.keys() if p not in required]
                if optional_params:
                    context_parts.append("Optional parameters:")
                    for param in optional_params:
                        prop_info = properties[param]
                        param_desc = f"  - {param} ({prop_info.get('type', 'unknown')})"
                        if 'description' in prop_info:
                            param_desc += f": {prop_info['description']}"
                        context_parts.append(param_desc)
                
            context_parts.append("-" * 40)
            
        # Add section for relevant tools
        context_parts.append("\nMOST RELEVANT TOOLS FOR YOUR QUERY:")
        context_parts.append("=" * 40)
        
        for tool_name, tool_info in selected_tools.items():
            tool = tool_info['tool']
            context_parts.append(f"\nTool: {tool_name} (Score: {tool_info['score']})")
            context_parts.append(f"Description: {tool.description}")
            
            # Add only essential parameters
            if tool.inputSchema and 'properties' in tool.inputSchema:
                required = tool.inputSchema.get('required', [])
                properties = tool.inputSchema['properties']
                
                if required:
                    context_parts.append("Required parameters:")
                    for param in required:
                        if param in properties:
                            prop_info = properties[param]
                            param_desc = f"  - {param} ({prop_info.get('type', 'unknown')})"
                            if 'description' in prop_info:
                                param_desc += f": {prop_info['description']}"
                            context_parts.append(param_desc)
                
                # Add a few important optional parameters
                optional = [p for p in properties.keys() if p not in required][:3]
                if optional:
                    context_parts.append("Key optional parameters:")
                    for param in optional:
                        prop_info = properties[param]
                        param_desc = f"  - {param} ({prop_info.get('type', 'unknown')})"
                        if 'description' in prop_info:
                            param_desc += f": {prop_info['description']}"
                        context_parts.append(param_desc)
            
            context_parts.append("-" * 25)
        
        return "\n".join(context_parts)

class MCPClient:
    """MCP Client that works with your specific API format"""
    
    def __init__(self, server_url: str = MCP_URL):
        self.server_url = server_url
        self.tools = {}
        self.connected = False
        self.last_error = None
        self.request_id = 1
        
    def _get_next_id(self) -> int:
        """Get next request ID for JSON-RPC"""
        self.request_id += 1
        return self.request_id
        
    def test_connection(self) -> bool:
        """Test if MCP server is accessible via health endpoint"""
        try:
            health_endpoint = f"{self.server_url}/health"
            response = requests.get(health_endpoint, timeout=5)
            self.connected = response.status_code == 200
            if self.connected:
                logger.info(f"SUCCESS: Connected to MCP server health check at {health_endpoint}")
            else:
                logger.error(f"ERROR: MCP health check returned status {response.status_code}")
            return self.connected
        except requests.exceptions.RequestException as e:
            self.connected = False
            self.last_error = str(e)
            logger.error(f"ERROR: Cannot connect to MCP health endpoint: {e}")
            return False
    
    def fetch_tools(self) -> Dict[str, MCPTool]:
        """Fetch available tools from MCP server /tools endpoint"""
        try:
            tools_endpoint = f"{self.server_url}/tools"
            logger.info(f"FETCHING: Getting tools from {tools_endpoint}")
            
            response = requests.get(tools_endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.tools = {}
                
                logger.info(f"RAW RESPONSE: {json.dumps(data, indent=2)}")
                
                # Handle your specific response format: {"tools": {"tools": [...]}}
                tools_data = []
                if isinstance(data, dict) and 'tools' in data:
                    if isinstance(data['tools'], dict) and 'tools' in data['tools']:
                        # Your format: {"tools": {"tools": [...]}}
                        tools_data = data['tools']['tools']
                        logger.info(f"PARSED: Found nested tools structure with {len(tools_data)} tools")
                    elif isinstance(data['tools'], list):
                        # Alternative format: {"tools": [...]}
                        tools_data = data['tools']
                        logger.info(f"PARSED: Found direct tools list with {len(tools_data)} tools")
                    else:
                        logger.error(f"ERROR: Unexpected tools structure in 'tools' field: {type(data['tools'])}")
                        return {}
                else:
                    logger.error(f"ERROR: No 'tools' field found in response: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return {}
                
                for tool_info in tools_data:
                    if isinstance(tool_info, dict) and 'name' in tool_info:
                        tool = MCPTool(
                            name=tool_info.get('name'),
                            description=tool_info.get('description', 'No description available'),
                            inputSchema=tool_info.get('inputSchema', {})
                        )
                        self.tools[tool.name] = tool
                        logger.info(f"LOADED: Tool '{tool.name}' - {tool.description}")
                
                logger.info(f"SUCCESS: Loaded {len(self.tools)} tools: {list(self.tools.keys())}")
                return self.tools
            else:
                logger.error(f"ERROR: Failed to fetch tools: HTTP {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"ERROR: Error fetching tools: {e}")
            traceback.print_exc()
            return {}
    
    def _find_similar_tool(self, tool_name: str) -> Optional[str]:
        """Find similar tool names using fuzzy matching"""
        if not self.tools:
            return None
        
        # Direct match
        if tool_name in self.tools:
            return tool_name
        
        # Try with underscores/hyphens variations
        variations = [
            tool_name.replace('_', '-'),
            tool_name.replace('-', '_'),
            tool_name.lower(),
            tool_name.upper()
        ]
        
        for variation in variations:
            if variation in self.tools:
                return variation
        
        # Fuzzy matching
        available_tools = list(self.tools.keys())
        close_matches = difflib.get_close_matches(tool_name, available_tools, n=1, cutoff=0.6)
        
        return close_matches[0] if close_matches else None
    
    def _convert_parameter_types(self, arguments: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parameter types based on schema"""
        if not schema or 'properties' not in schema:
            return arguments
        
        converted = {}
        properties = schema['properties']
        
        for key, value in arguments.items():
            if key in properties:
                prop_type = properties[key].get('type')
                try:
                    if prop_type == 'integer' or prop_type == 'number':
                        if isinstance(value, str):
                            converted[key] = int(value) if prop_type == 'integer' else float(value)
                        else:
                            converted[key] = value
                    elif prop_type == 'boolean':
                        if isinstance(value, str):
                            converted[key] = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            converted[key] = bool(value)
                    elif prop_type == 'array' and isinstance(value, str):
                        # Try to parse JSON string to array
                        try:
                            converted[key] = json.loads(value)
                        except:
                            converted[key] = value
                    else:
                        converted[key] = value
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert parameter {key}: {e}, using original value")
                    converted[key] = value
            else:
                converted[key] = value
        
        return converted
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with comprehensive error handling and tool name matching"""
        
        # Find the correct tool name (handle variations)
        actual_tool_name = self._find_similar_tool(tool_name)
        
        if not actual_tool_name:
            available_tools = list(self.tools.keys())
            close_matches = difflib.get_close_matches(tool_name, available_tools, n=3, cutoff=0.3)
            
            error_msg = f"Tool '{tool_name}' not found."
            if close_matches:
                error_msg += f" Did you mean: {', '.join(close_matches)}?"
            error_msg += f" Available tools: {available_tools}"
            
            return {
                "success": False,
                "error": error_msg,
                "suggestions": close_matches,
                "available_tools": available_tools
            }
        
        if actual_tool_name != tool_name:
            logger.info(f"TOOL NAME CORRECTION: '{tool_name}' -> '{actual_tool_name}'")
        
        try:
            call_endpoint = f"{self.server_url}/tools/call"
            
            # Convert parameter types based on schema
            tool = self.tools[actual_tool_name]
            converted_args = self._convert_parameter_types(arguments, tool.inputSchema)
            
            # Format payload according to JSON-RPC 2.0 specification
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": actual_tool_name,
                    "arguments": converted_args
                },
                "id": self._get_next_id()
            }
            
            logger.info(f"CALLING: {call_endpoint}")
            logger.info(f"PAYLOAD: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                call_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=1200
            )
            
            logger.info(f"RESPONSE STATUS: {response.status_code}")
            logger.info(f"RESPONSE TEXT: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # Handle JSON-RPC response format
                    if 'result' in result:
                        logger.info(f"SUCCESS: Tool {actual_tool_name} executed successfully")
                        return {
                            "success": True,
                            "result": result['result'],
                            "tool_name": actual_tool_name,
                            "original_tool_name": tool_name,
                            "endpoint_used": call_endpoint
                        }
                    elif 'error' in result:
                        logger.error(f"ERROR: JSON-RPC error: {result['error']}")
                        return {
                            "success": False,
                            "error": f"JSON-RPC error: {result['error']}",
                            "tool_name": actual_tool_name
                        }
                    else:
                        # Fallback for non-standard responses
                        logger.info(f"SUCCESS: Tool {actual_tool_name} executed (non-standard response)")
                        return {
                            "success": True,
                            "result": result,
                            "tool_name": actual_tool_name,
                            "original_tool_name": tool_name,
                            "endpoint_used": call_endpoint
                        }
                except json.JSONDecodeError:
                    # Handle non-JSON responses
                    return {
                        "success": True,
                        "result": response.text,
                        "tool_name": actual_tool_name,
                        "original_tool_name": tool_name,
                        "endpoint_used": call_endpoint
                    }
            else:
                logger.error(f"ERROR: Tool execution failed with status {response.status_code}")
                # Try fallback with simple format
                return self._execute_tool_fallback(actual_tool_name, converted_args, tool_name)
                
        except Exception as e:
            logger.error(f"ERROR: Error executing tool {actual_tool_name}: {e}")
            traceback.print_exc()
            # Try fallback with simple format
            return self._execute_tool_fallback(actual_tool_name, arguments, tool_name)
    
    def _execute_tool_fallback(self, tool_name: str, arguments: Dict[str, Any], original_tool_name: str = None) -> Dict[str, Any]:
        """Fallback execution with simple format"""
        try:
            call_endpoint = f"{self.server_url}/tools/call"
            
            # Simple format payload
            payload = {
                "name": tool_name,
                "arguments": arguments
            }
            
            logger.info(f"FALLBACK CALLING: {call_endpoint}")
            logger.info(f"FALLBACK PAYLOAD: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                call_endpoint,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=1200
            )
            
            logger.info(f"FALLBACK RESPONSE STATUS: {response.status_code}")
            logger.info(f"FALLBACK RESPONSE TEXT: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    logger.info(f"SUCCESS: Tool {tool_name} executed successfully (fallback)")
                    return {
                        "success": True,
                        "result": result,
                        "tool_name": tool_name,
                        "original_tool_name": original_tool_name,
                        "endpoint_used": call_endpoint,
                        "method": "fallback"
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "result": response.text,
                        "tool_name": tool_name,
                        "original_tool_name": original_tool_name,
                        "endpoint_used": call_endpoint,
                        "method": "fallback"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Tool execution failed: HTTP {response.status_code} - {response.text}",
                    "response_text": response.text,
                    "status_code": response.status_code,
                    "method": "fallback",
                    "tool_name": tool_name
                }
                
        except Exception as e:
            logger.error(f"ERROR: Fallback execution failed for {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "method": "fallback"
            }

class OllamaClient:
    """Ollama client with connection testing"""
    
    def __init__(self, model: str = "llama3.2:latest", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.available = False
        
    def test_connection(self) -> bool:
        """Test Ollama connection"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                self.available = any(self.model in name for name in model_names)
                
                if self.available:
                    logger.info(f"SUCCESS: Ollama connected, model '{self.model}' available")
                else:
                    logger.error(f"ERROR: Model '{self.model}' not found. Available: {model_names}")
                    if model_names:
                        self.model = model_names[0].split(':')[0]
                        logger.info(f"SWITCHING: Using available model: {self.model}")
                        self.available = True
                
                return self.available
            else:
                logger.error(f"ERROR: Ollama server error: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"ERROR: Cannot connect to Ollama: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using Ollama"""
        if not self.available:
            return "Error: Ollama not available"
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=1800
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: Ollama returned status {response.status_code}"
                
        except Exception as e:
            logger.error(f"ERROR: Ollama generation error: {e}")
            return f"Error generating response: {e}"

class SmartAIAgent:
    """Advanced AI Agent with NLP-powered tool selection"""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.ollama_client = OllamaClient()
        self.tool_selector = None
        self.conversation_history = []
        self.initialized = False
        self.status = {"mcp": False, "ollama": False, "tools": 0}
        
    def initialize(self) -> bool:
        """Initialize all components with detailed status reporting"""
        logger.info("INITIALIZING: Starting AI Agent initialization...")
        
        # Test MCP connection via health endpoint
        self.status["mcp"] = self.mcp_client.test_connection()
        
        # Test Ollama connection
        self.status["ollama"] = self.ollama_client.test_connection()
        
        # Fetch tools if MCP is available
        if self.status["mcp"]:
            tools = self.mcp_client.fetch_tools()
            self.status["tools"] = len(tools)
            if tools:
                self.tool_selector = SmartToolSelector(tools)
        
        self.initialized = self.status["mcp"] and self.status["ollama"]
        
        if self.initialized:
            logger.info("SUCCESS: AI Agent initialized successfully!")
        else:
            logger.error("ERROR: AI Agent initialization failed!")
            self._print_diagnostics()
        
        return self.initialized
    
    def _print_diagnostics(self):
        """Print diagnostic information"""
        print("\n" + "="*60)
        print("DIAGNOSTIC INFORMATION")
        print("="*60)
        print(f"MCP Server: {'SUCCESS Connected' if self.status['mcp'] else 'ERROR Failed'}")
        print(f"Ollama: {'SUCCESS Connected' if self.status['ollama'] else 'ERROR Failed'}")
        print(f"Tools Available: {self.status['tools']}")
        
        if not self.status["mcp"]:
            print(f"\nERROR MCP Server Issues:")
            print(f"   - Check if your MCP server is running on localhost:6001")
            print(f"   - Last error: {self.mcp_client.last_error}")
            print(f"   - Try: curl "+MCP_URL+"/health")
            print(f"   - Try: curl "+MCP_URL+"/tools")
        
        if not self.status["ollama"]:
            print(f"\nERROR Ollama Issues:")
            print(f"   - Check if Ollama is running: ollama serve")
            print(f"   - Install model: ollama pull llama3.2:latest")
            print(f"   - Check available models: ollama list")
        
        print("\n" + "="*60)
    
    def _is_tool_request(self, parsed_response: Dict[str, Any]) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """Determine if response is a tool request and extract tool info"""
        tool_name = None
        arguments = {}
        
        if parsed_response.get("action") == "use_tool":
            # Standard format: {"action": "use_tool", "tool": "tool_name", "arguments": {...}}
            tool_name = parsed_response.get("tool")
            arguments = parsed_response.get("arguments", {})
            logger.info(f"DETECTED: Standard tool format")
        elif "action" in parsed_response:
            # Check if action is a valid tool name (with variations)
            action_name = parsed_response["action"]
            actual_tool_name = self.mcp_client._find_similar_tool(action_name)
            
            if actual_tool_name:
                tool_name = action_name  # Keep original for validation
                arguments = parsed_response.get("arguments", {})
                logger.info(f"DETECTED: Direct tool name format: {action_name}")
        
        return (tool_name is not None, tool_name, arguments)
    
    def _format_response_for_display(self, response: str) -> str:
        """Format the LLM response for better display in HTML"""
        import re
        
        # Convert markdown-style formatting to HTML
        formatted = response
        
        # Headers (##, ###, etc.)
        formatted = re.sub(r'^### (.+)$', r'<h3>\1</h3>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^## (.+)$', r'<h2>\1</h2>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^# (.+)$', r'<h1>\1</h1>', formatted, flags=re.MULTILINE)
        
        # Bold text (**text**)
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', formatted)
        
        # Italic text (*text*)
        formatted = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', formatted)
        
        # Lists
        lines = formatted.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Numbered lists
            if re.match(r'^\d+\.\s+', stripped):
                if not in_list:
                    result_lines.append('<ol>')
                    in_list = 'ol'
                item_text = re.sub(r'^\d+\.\s+', '', stripped)
                result_lines.append(f'<li>{item_text}</li>')
            
            # Bullet lists
            elif stripped.startswith('- ') or stripped.startswith('* '):
                if in_list != 'ul':
                    if in_list == 'ol':
                        result_lines.append('</ol>')
                    result_lines.append('<ul>')
                    in_list = 'ul'
                item_text = stripped[2:].strip()
                result_lines.append(f'<li>{item_text}</li>')
            
            else:
                # Close any open list
                if in_list:
                    if in_list == 'ol':
                        result_lines.append('</ol>')
                    else:
                        result_lines.append('</ul>')
                    in_list = False
                
                # Regular paragraph
                if stripped:
                    result_lines.append(f'<p>{line}</p>')
                else:
                    result_lines.append('<br>')
        
        # Close any remaining open list
        if in_list:
            if in_list == 'ol':
                result_lines.append('</ol>')
            else:
                result_lines.append('</ul>')
        
        formatted = '\n'.join(result_lines)
        
        # Clean up extra paragraph tags around headers
        formatted = re.sub(r'<p>(<h[1-6]>.*?</h[1-6]>)</p>', r'\1', formatted)
        
        return formatted

    def process_query(self, user_input: str) -> Dict[str, Any]:
        """Process user query with intelligent NLP-based tool selection"""
        if not self.initialized:
            return {
                "response": "Agent not initialized. Please check connections.",
                "success": False,
                "status": self.status
            }
        
        start_time = time.time()
        logger.info(f"PROCESSING: User query: {user_input}")
        
        try:
            # Use smart tool selection to get relevant tools and context
            selection_result = self.tool_selector.select_tools(user_input)
            optimized_context = self.tool_selector.build_optimized_context(selection_result)
            
            logger.info(f"SMART SELECTION: {selection_result['tool_count']} tools selected")
            logger.info(f"CATEGORIES: {selection_result['relevant_categories']}")
            logger.info(f"SELECTED TOOLS: {list(selection_result['selected_tools'].keys())}")
            
            # Build focused system prompt with only relevant tools
            system_prompt = f"""You are an intelligent News AI assistant specialized in news and document search. Based on the user query analysis, I've selected the most relevant tools for you.

{optimized_context}

INSTRUCTIONS:
1. Based on the extracted entities and available tools above, select the MOST APPROPRIATE tool, and give priority to date and time related parameters in tools selection than anything else if date or time is present in query.
2. If the request requires a tool, respond with JSON in one of these EXACT formats:
   Format 1: {{"action": "use_tool", "tool": "tool_name", "arguments": {{"parameter": "value"}}}}
   Format 2: {{"action": "tool_name", "arguments": {{"parameter": "value"}}}}
   Format 3: {{"action": "tool_name"}} (for tools with no parameters)
   In case the query is having something else as well like summarize this or predict this something not related to fetching but doing English task.
   Then, ignore that and give correct format of json parsing.
   Later, when query is sent it will get handled.
3. Use EXACT tool names from the relevant tools list above
4. For numeric parameters, use actual numbers not strings (e.g., 5 not "5")
5. Match parameter names and types exactly to the tool schema.
6. Only include required parameters and relevant optional ones
7. If no tool is needed, respond normally with helpful information
8. When someone ask for something specific in a date range and you are calling the date_range function, with limit param 100 so that , it is possible to find relevant content from it.

PARAMETER MAPPING HINTS:
- For date queries: use start_epoch/end_epoch (Unix timestamps)
- For search queries: use 'query' parameter for search terms
- For limits: use 'limit' parameter (typically 10-50)
- For categories: use exact category names
- For authors: use exact author names

Remember: Only use tools when they're specifically needed for the user's request. The tools above are pre-selected as most relevant for this query."""
            
            # Get LLM response with optimized context
            llm_response = self.ollama_client.generate(
                prompt=user_input,
                system_prompt=system_prompt
            )
            
            logger.info(f"LLM RESPONSE: {llm_response}")
            
            # Try to parse as JSON (tool usage)
            try:
                # Clean the response - sometimes LLMs add extra text
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_part = llm_response[json_start:json_end]
                    parsed_response = json.loads(json_part)
                else:
                    parsed_response = json.loads(llm_response.strip())
                
                # Check for tool usage
                is_tool_request, tool_name, arguments = self._is_tool_request(parsed_response)
                
                if is_tool_request and tool_name:
                    logger.info(f"TOOL REQUEST: {tool_name} with args {arguments}")
                    
                    # Execute the tool
                    tool_result = self.mcp_client.execute_tool(tool_name, arguments)
                    
                    if tool_result["success"]:
                        # Generate final response with tool result
                        final_prompt = f"""The user asked: {user_input}

I executed the tool '{tool_result.get('tool_name', tool_name)}' and got this result:
{json.dumps(tool_result['result'], indent=2)}

You are a news assistant. Please provide a clear, helpful, and well-formatted response based on this tool result.
- If the response is empty or don't contain required things just say it that you didn't found the results don't make on your own.
- Summarize the key information
- Present data in a readable format  
- Answer the user's question directly
- If the result contains structured data, format it nicely
- Be conversational and helpful
"""
                        logger.info(str({json.dumps(tool_result['result'], indent=2)}))
                        final_response = self.ollama_client.generate(final_prompt)
                        
                        return {
                            "response": final_response,
                            "formatted_response": self._format_response_for_display(final_response),
                            "success": True,
                            "tool_used": tool_result.get('tool_name', tool_name),
                            "tool_arguments": arguments,
                            "tool_result": tool_result,
                            "entities_extracted": selection_result['entities'].__dict__,
                            "relevant_categories": selection_result['relevant_categories'],
                            "selected_tools": list(selection_result['selected_tools'].keys()),
                            "raw_llm_response": llm_response,
                            "execution_time": time.time() - start_time
                        }
                    else:
                        return {
                            "response": f"Tool execution failed: {tool_result['error']}",
                            "success": False,
                            "tool_used": tool_name,
                            "error": tool_result['error'],
                            "entities_extracted": selection_result['entities'].__dict__,
                            "raw_llm_response": llm_response,
                            "tool_result": tool_result
                        }
                        
            except json.JSONDecodeError as e:
                # Not a tool request, return LLM response directly
                logger.info("DIRECT RESPONSE: No tool usage detected or JSON parse failed")
            
            # Store conversation
            self.conversation_history.append({
                "user": user_input,
                "assistant": llm_response,
                "entities": selection_result['entities'].__dict__,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "response": llm_response,
                "formatted_response": self._format_response_for_display(llm_response),
                "success": True,
                "entities_extracted": selection_result['entities'].__dict__,
                "relevant_categories": selection_result['relevant_categories'],
                "selected_tools": list(selection_result['selected_tools'].keys()),
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"ERROR: Error processing query: {e}")
            traceback.print_exc()
            return {
                "response": f"Error processing your request: {e}",
                "success": False,
                "error": str(e)
            }

# Global agent instance
agent = SmartAIAgent()

# Hardcoded HTML template with separate response sections
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart AI Agent - MCP Tool Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 1.3em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px solid #eee;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #555;
        }
        select, textarea, input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e1e1e1;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        select:focus, textarea:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            height: 100px;
            resize: vertical;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online {
            background: #28a745;
        }
        .status-offline {
            background: #dc3545;
        }
        .endpoint-description {
            background: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            font-size: 14px;
            color: #1565c0;
        }
        /* SEPARATE AI RESPONSE SECTION - GREEN */
        .ai-response-section {
            margin-bottom: 30px;
            border: 3px solid #4CAF50;
            border-radius: 15px;
            background: linear-gradient(145deg, #f0f8f0, #ffffff);
            box-shadow: 0 8px 25px rgba(76, 175, 80, 0.2);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }
        .ai-response-section:hover {
            transform: translateY(-2px);
        }
        .ai-response-section .section-title {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            margin: -20px -20px 25px -20px;
            padding: 20px 25px;
            border-radius: 12px 12px 0 0;
            font-size: 1.4em;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        /* SEPARATE TECHNICAL RESPONSE SECTION - BLUE */
        .technical-response-section {
            margin-bottom: 20px;
            border: 3px solid #2196F3;
            border-radius: 15px;
            background: linear-gradient(145deg, #f0f8ff, #ffffff);
            box-shadow: 0 8px 25px rgba(33, 150, 243, 0.2);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }
        .technical-response-section:hover {
            transform: translateY(-2px);
        }
        .technical-response-section .section-title {
            background: linear-gradient(135deg, #2196F3, #1976D2);
            color: white;
            margin: -20px -20px 25px -20px;
            padding: 20px 25px;
            border-radius: 12px 12px 0 0;
            font-size: 1.4em;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .empty-state {
            padding: 20px;
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .response-box {
            background: #f8f9fa;
            border: 1px solid #e1e1e1;
            border-radius: 8px;
            padding: 20px;
            min-height: 200px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 600px;
            overflow-y: auto;
        }
        .formatted-response {
            background: linear-gradient(135deg, #f8f9ff 0%, #fff5f5 100%);
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: #333;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
            max-height: 500px;
            overflow-y: auto;
        }
        .json-key { color: #d73a49; font-weight: bold; }
        .json-string { color: #032f62; }
        .json-number { color: #005cc5; }
        .json-boolean { color: #e36209; }
        .json-null { color: #6f42c1; }
        .example-queries {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .example-query {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .example-query:hover {
            background: #e9ecef;
        }
        .example-query strong {
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        @media (max-width: 768px) {
            .two-column {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Smart AI Agent Interface</h1>
            <p>MCP Tool Selection & News Search System</p>
            <div style="margin-top: 15px;">
                <span class="status-indicator status-online" id="serverStatus"></span>
                <span id="serverStatusText">Server Online</span>
            </div>
        </div>

        <div class="content">
            <div class="two-column">
                <div>
                    <div class="section">
                        <h2 class="section-title">🔧 API Configuration</h2>
                        
                        <div class="form-group">
                            <label for="endpoint">Select Endpoint:</label>
                            <select id="endpoint" onchange="updateEndpointDescription()">
                                <option value="/chat">💬 Chat - Main conversation endpoint</option>
                                <option value="/analyze">🔍 Analyze - Query analysis & tool selection</option>
                                <option value="/tools">🛠️ Tools - List available tools</option>
                                <option value="/status">📊 Status - System health check</option>
                                <option value="/test">🧪 Test - Run connection tests</option>
                                <option value="/initialize">🚀 Initialize - Force re-initialization</option>
                                <option value="/tools/refresh">🔄 Refresh Tools - Reload from MCP server</option>
                                <option value="/health">❤️ Health - Basic health check</option>
                            </select>
                        </div>

                        <div id="endpointDescription" class="endpoint-description">
                            Select an endpoint to see its description
                        </div>

                        <div class="form-group" id="messageGroup">
                            <label for="message">Message/Query:</label>
                            <textarea id="message" placeholder="Enter your query here..."></textarea>
                        </div>

                        <button class="btn" onclick="makeRequest()" id="submitBtn">
                            Send Request
                        </button>
                    </div>

                    <div class="section" id="exampleSection">
                        <h2 class="section-title">💡 Example Queries</h2>
                        <div class="example-queries">
                            <div class="example-query" onclick="setExample('Show me recent sports news')">
                                <strong>Recent News</strong>
                                Show me recent sports news
                            </div>
                            <div class="example-query" onclick="setExample('Find articles by John Smith from last month')">
                                <strong>Author Search</strong>
                                Find articles by John Smith from last month
                            </div>
                            <div class="example-query" onclick="setExample('Get technology news from January 2024')">
                                <strong>Date Range</strong>
                                Get technology news from January 2024
                            </div>
                            <div class="example-query" onclick="setExample('Search for climate change articles')">
                                <strong>Full-text Search</strong>
                                Search for climate change articles
                            </div>
                        </div>
                    </div>
                </div>
                
                <div>
                    <!-- COMPLETELY SEPARATE AI RESPONSE CONTAINER - GREEN -->
                    <div class="section ai-response-section">
                        <h2 class="section-title">💬 AI Response</h2>
                        
                        <div class="loading" id="loading">
                            <div class="spinner"></div>
                            <div>Processing request...</div>
                        </div>

                        <div class="formatted-response" id="formattedResponse">
                            <div class="empty-state">
                                <em>✨ Your beautifully formatted AI response will appear here...</em>
                            </div>
                        </div>
                    </div>

                    <!-- COMPLETELY SEPARATE TECHNICAL RESPONSE CONTAINER - BLUE -->
                    <div class="section technical-response-section">
                        <h2 class="section-title">📄 Technical Response (JSON)</h2>
                        
                        <div class="response-box" id="responseBox">
                            <div class="empty-state">
                                <em>🔧 Raw technical response data will appear here...</em>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const SERVER_URL = 'http://n8.lsdiedb39c.pagekite.me';

        const endpointDescriptions = {
            '/chat': {
                description: 'Main conversation endpoint. Processes natural language queries and automatically selects the best tools.',
                needsMessage: true,
                example: 'Show me recent sports news from last week'
            },
            '/analyze': {
                description: 'Analyzes your query to show entity extraction and tool selection process.',
                needsMessage: true,
                example: 'Find articles about technology'
            },
            '/tools': {
                description: 'Lists all available tools organized by category.',
                needsMessage: false
            },
            '/status': {
                description: 'Detailed system status including MCP connection, Ollama availability, tool count.',
                needsMessage: false
            },
            '/test': {
                description: 'Runs comprehensive connection tests for MCP server, Ollama, and NLP capabilities.',
                needsMessage: false
            },
            '/initialize': {
                description: 'Forces re-initialization of the agent.',
                needsMessage: false
            },
            '/tools/refresh': {
                description: 'Refreshes the tool list from the MCP server.',
                needsMessage: false
            },
            '/health': {
                description: 'Basic health check endpoint.',
                needsMessage: false
            }
        };

        function setExample(exampleText) {
            document.getElementById('message').value = exampleText;
        }

        function updateEndpointDescription() {
            const endpoint = document.getElementById('endpoint').value;
            const info = endpointDescriptions[endpoint];
            const messageGroup = document.getElementById('messageGroup');
            const exampleSection = document.getElementById('exampleSection');
            
            if (info) {
                document.getElementById('endpointDescription').innerHTML = 
                    `<strong>${endpoint}</strong><br>${info.description}`;
                
                messageGroup.style.display = info.needsMessage ? 'block' : 'none';
                exampleSection.style.display = info.needsMessage ? 'block' : 'none';
                
                if (info.example) {
                    document.getElementById('message').placeholder = info.example;
                }
            }
        }

        // Server status is handled automatically - server is online when page loads

        async function makeRequest() {
            const endpoint = document.getElementById('endpoint').value;
            const message = document.getElementById('message').value;
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const responseBox = document.getElementById('responseBox');
            const formattedResponse = document.getElementById('formattedResponse');

            // Show loading state
            submitBtn.disabled = true;
            loading.style.display = 'block';
            responseBox.innerHTML = '';
            formattedResponse.innerHTML = '<div class="empty-state"><em>🔄 Processing your request...</em></div>';

            try {
                const info = endpointDescriptions[endpoint];
                let url = SERVER_URL + endpoint;
                let options = {
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };

                if (info.needsMessage) {
                    if (!message.trim()) {
                        throw new Error('Message is required for this endpoint');
                    }
                    options.method = 'POST';
                    options.body = JSON.stringify({ message: message.trim() });
                } else {
                    options.method = endpoint === '/initialize' || endpoint === '/tools/refresh' ? 'POST' : 'GET';
                }

                const response = await fetch(url, options);
                const data = await response.json();

                // Display response in both sections
                displayResponse(data, response.ok);

            } catch (error) {
                displayResponse({
                    error: error.message,
                    details: 'Failed to connect to the server. Make sure the Flask app is running on localhost:5001'
                }, false);
            } finally {
                // Hide loading state
                submitBtn.disabled = false;
                loading.style.display = 'none';
            }
        }

        function displayResponse(data, success) {
            const responseBox = document.getElementById('responseBox');
            const formattedResponse = document.getElementById('formattedResponse');
            
            // Show formatted response if we have a successful response with content
            if ((data.response || data.formatted_response) && success) {
                if (data.formatted_response) {
                    formattedResponse.innerHTML = data.formatted_response;
                } else if (data.response) {
                    formattedResponse.innerHTML = formatResponseText(data.response);
                }
            } else {
                formattedResponse.innerHTML = '<div class="empty-state"><em>❌ No formatted response available</em></div>';
            }
            
            // Always show technical JSON response
            if (success) {
                responseBox.innerHTML = formatJSON(data);
                responseBox.style.color = '#333';
                responseBox.style.backgroundColor = '#f8f9fa';
            } else {
                responseBox.innerHTML = formatJSON(data);
                responseBox.style.color = '#721c24';
                responseBox.style.backgroundColor = '#f8d7da';
            }
        }

        function formatResponseText(text) {
            if (!text) return '';
            
            let formatted = text
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\n\\n+/g, '</p><p>')
                .replace(/\\n/g, '<br>');
            
            if (!formatted.includes('<p>') && !formatted.includes('<strong>')) {
                formatted = '<p>' + formatted + '</p>';
            }
            
            return formatted;
        }

        function formatJSON(obj) {
            if (typeof obj === 'string') {
                return obj;
            }
            return syntaxHighlight(JSON.stringify(obj, null, 2));
        }

        function syntaxHighlight(json) {
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\\\u[a-zA-Z0-9]{4}|\\\\[^u]|[^\\\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g, function (match) {
                var cls = 'json-number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'json-key';
                    } else {
                        cls = 'json-string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'json-boolean';
                } else if (/null/.test(match)) {
                    cls = 'json-null';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }

        // Initialize the page
        document.addEventListener('DOMContentLoaded', function() {
            updateEndpointDescription();

            // Add Enter key support for message textarea
            document.getElementById('message').addEventListener('keydown', function(event) {
                if (event.ctrlKey && event.key === 'Enter') {
                    makeRequest();
                }
            });
        });
    </script>
</body>
</html>"""

# Flask Routes
@app.route('/', methods=['GET'])
def index():
    """Serve the hardcoded HTML template with separate response sections"""
    return HTML_TEMPLATE

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    return jsonify({
        "service": "Smart AI Agent with NLP Tool Selection",
        "status": agent.status,
        "initialized": agent.initialized,
        "timestamp": datetime.now().isoformat(),
        "tools_available": list(agent.mcp_client.tools.keys()) if agent.mcp_client.tools else [],
        "nlp_available": agent.tool_selector.entity_extractor.spacy_available if agent.tool_selector else False
    })

@app.route('/initialize', methods=['POST'])
def initialize_agent():
    """Force re-initialization"""
    success = agent.initialize()
    return jsonify({
        "success": success,
        "status": agent.status,
        "message": "Agent initialized successfully" if success else "Initialization failed"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with NLP-powered tool selection"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing 'message' in request body",
                "example": {"message": "Show me recent sports news"}
            }), 400
        
        user_message = data['message']
        result = agent.process_query(user_message)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ERROR: Chat endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_query():
    """Analyze query and show entity extraction + tool selection"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing 'message' in request body"
            }), 400
        
        if not agent.tool_selector:
            return jsonify({
                "error": "Tool selector not initialized"
            }), 500
        
        user_message = data['message']
        selection_result = agent.tool_selector.select_tools(user_message)
        optimized_context = agent.tool_selector.build_optimized_context(selection_result)
        
        return jsonify({
            "query": user_message,
            "entities_extracted": selection_result['entities'].__dict__,
            "relevant_categories": selection_result['relevant_categories'],
            "selected_tools": {
                name: {
                    "score": info['score'],
                    "category": info['category'],
                    "description": info['tool'].description
                }
                for name, info in selection_result['selected_tools'].items()
            },
            "optimized_context": optimized_context,
            "tool_count": selection_result['tool_count']
        })
        
    except Exception as e:
        logger.error(f"ERROR: Analyze endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/tools', methods=['GET'])
def get_tools():
    """Get available tools with categorization"""
    if not agent.tool_selector:
        return jsonify({
            "error": "Tool selector not initialized",
            "tools": {},
            "count": 0
        })
    
    categorizer = agent.tool_selector.categorizer
    tools_by_category = {}
    
    for category, info in categorizer.tool_categories.items():
        tools_by_category[category] = {
            "description": f"Tools for {category.replace('_', ' ')}",
            "keywords": info['keywords'],
            "entities": info['entities'],
            "tools": []
        }
        
        for tool_name in info['tools']:
            if tool_name in agent.mcp_client.tools:
                tool = agent.mcp_client.tools[tool_name]
                tools_by_category[category]['tools'].append({
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": list(tool.inputSchema.get('properties', {}).keys()) if tool.inputSchema else []
                })
    
    return jsonify({
        "tools_by_category": tools_by_category,
        "total_tools": len(agent.mcp_client.tools),
        "categories": list(categorizer.tool_categories.keys()),
        "mcp_connected": agent.status["mcp"]
    })

@app.route('/tools/refresh', methods=['POST'])
def refresh_tools():
    """Refresh tools from MCP server and reinitialize tool selector"""
    try:
        tools = agent.mcp_client.fetch_tools()
        agent.status["tools"] = len(tools)
        
        if tools:
            agent.tool_selector = SmartToolSelector(tools)
        
        return jsonify({
            "success": True,
            "tools_count": len(tools),
            "tools": list(tools.keys())
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get detailed agent status"""
    return jsonify({
        "agent_initialized": agent.initialized,
        "mcp_connected": agent.status["mcp"],
        "ollama_connected": agent.status["ollama"],
        "tools_count": agent.status["tools"],
        "nlp_available": agent.tool_selector.entity_extractor.spacy_available if agent.tool_selector else False,
        "conversation_count": len(agent.conversation_history),
        "mcp_url": agent.mcp_client.server_url,
        "ollama_model": agent.ollama_client.model,
        "last_mcp_error": agent.mcp_client.last_error
    })

@app.route('/test', methods=['POST'])
def test_connections():
    """Test all connections and NLP capabilities"""
    results = {}
    
    # Test MCP health
    results["mcp_health"] = agent.mcp_client.test_connection()
    
    # Test Ollama
    results["ollama"] = agent.ollama_client.test_connection()
    
    # Test NLP extraction
    if agent.tool_selector:
        try:
            test_query = "Show me recent sports news from last week"
            selection_result = agent.tool_selector.select_tools(test_query)
            results["nlp_extraction"] = True
            results["test_entities"] = selection_result['entities'].__dict__
            results["test_tools_selected"] = list(selection_result['selected_tools'].keys())
        except Exception as e:
            results["nlp_extraction"] = False
            results["nlp_error"] = str(e)
    
    # Test tools endpoint
    if results["mcp_health"]:
        try:
            tools_url = f"{agent.mcp_client.server_url}/tools"
            response = requests.get(tools_url, timeout=5)
            results["mcp_tools"] = response.status_code == 200
            results["tools_count"] = len(agent.mcp_client.tools)
        except Exception as e:
            results["mcp_tools"] = False
            results["tools_error"] = str(e)
    
    # Test a simple query if everything is working
    if results["mcp_health"] and results["ollama"] and results.get("nlp_extraction"):
        test_result = agent.process_query("Hello, are you working?")
        results["agent_test"] = test_result["success"]
        results["test_response"] = test_result.get("response", "")
    
    return jsonify(results)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SMART AI AGENT WITH NLP-POWERED TOOL SELECTION")
    print("="*80)
    print("FEATURES:")
    print("- Advanced entity extraction (dates, names, categories, etc.)")
    print("- Smart tool categorization and selection")
    print("- Optimized context for LLM efficiency")
    print("- Intent recognition and mapping")
    print("="*80)
    print("STARTING: Starting initialization...")
    
    # Initialize the agent
    if agent.initialize():
        print(f"\nSUCCESS: Smart Agent ready with {agent.status['tools']} tools!")
        print(f"NLP Available: {agent.tool_selector.entity_extractor.spacy_available if agent.tool_selector else False}")
        print("STARTING: Starting Flask server on http://localhost:5001")
        print("\nNEW ENDPOINTS:")
        print("   POST /analyze           - Analyze query entities and tool selection")
        print("   GET  /tools             - List tools by category")
        print("\nEXAMPLE QUERIES:")
        print('   "Show me recent sports news"')
        print('   "Find articles by John Smith from last month"')  
        print('   "Get technology news from January 2024"')
        print('   "List all authors in politics category"')
        print("\nEXAMPLE CURL:")
        print('   curl -X POST http://localhost:5001/analyze \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"message": "Show me recent sports news"}\'')
        print("\n" + "="*80)
        # cache = Cache(app)

        # Clear the cache
        # cache.clear()
        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    else:
        print("\nERROR: Initialization failed!")
        agent._print_diagnostics()
        print("\nADDITIONAL SETUP (Optional for better NLP):")
        print("pip install spacy")
        print("python -m spacy download en_core_web_sm")
        sys.exit(1)
