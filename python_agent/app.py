# Fix OpenMP library conflict on Windows (must be set before importing scientific libraries)
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import json
import requests
import sys
import traceback
from flask import Flask, request, jsonify
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
from flask_cors import CORS  
CORS(app)


MCP_URL = "http://localhost:6001"
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart AI Agent - Enhanced with Memory & Prompt Breaking</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
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
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        .status-bar {
            margin-top: 15px;
            padding: 10px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            background: #28a745;
        }
        .status-offline {
            background: #dc3545;
        }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px;
        }
        .control-panel {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        label {
            font-weight: 600;
            color: #555;
            font-size: 14px;
        }
        select, textarea, input {
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s ease;
        }
        select:focus, textarea:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 20px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .examples {
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
        }
        .example-btn {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 12px;
            border-radius: 6px;
            cursor: pointer;
            text-align: left;
            font-size: 14px;
            transition: background-color 0.2s ease;
        }
        .example-btn:hover {
            background: #e9ecef;
        }
        .example-title {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 4px;
        }
        .memory-section {
            background: #fff3e0;
            border: 2px solid #ff9800;
            border-radius: 8px;
            padding: 15px;
            display: none;
        }
        .response-section {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .response-box {
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            padding: 20px;
            min-height: 200px;
            background: #f8f9fa;
        }
        .ai-response {
            border-color: #28a745;
            background: linear-gradient(145deg, #f0f8f0, #ffffff);
        }
        .tech-response {
            border-color: #007bff;
            background: linear-gradient(145deg, #f0f8ff, #ffffff);
            font-family: 'Courier New', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        .response-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #eee;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Smart AI Agent</h1>
            <p>Enhanced with Memory, Prompt Breaking & Chaining</p>
            <div class="status-bar">
                <span id="status-indicator" class="status-indicator"></span>
                <span id="status-text">Checking connection...</span>
            </div>
        </div>

        <div class="main-content">
            <div class="control-panel">
                <div class="form-group">
                    <label for="endpoint-select">Select Endpoint</label>
                    <select id="endpoint-select">
                        <option value="/chat">💬 Chat</option>
                        <option value="/chat/memory">🧠 Chat with Memory</option>
                        <option value="/chat/chain">🔗 Chat with Chaining</option>
                        <option value="/analyze">🔍 Analyze Query</option>
                        <option value="/tools">🛠️ List Tools</option>
                        <option value="/status">📊 System Status</option>
                        <option value="/test">🧪 Run Tests</option>
                        <option value="/initialize">🚀 Initialize</option>
                    </select>
                </div>

                <div id="memory-section" class="memory-section">
                    <div class="form-group">
                        <label for="conversation-id">Conversation ID</label>
                        <input type="text" id="conversation-id" value="default" placeholder="Enter conversation ID">
                    </div>
                </div>

                <div id="message-section" class="form-group">
                    <label for="message-input">Your Message</label>
                    <textarea id="message-input" placeholder="Type your message here..."></textarea>
                </div>

                <button id="send-button" class="btn">Send Request</button>

                <div class="form-group">
                    <label>Example Queries</label>
                    <div class="examples">
                        <div class="example-btn" data-message="Show me recent sports news">
                            <div class="example-title">Recent News</div>
                            Show me recent sports news
                        </div>
                        <div class="example-btn" data-message="Find articles about technology">
                            <div class="example-title">Tech Articles</div>
                            Find articles about technology
                        </div>
                        <div class="example-btn" data-message="List all available categories">
                            <div class="example-title">Categories</div>
                            List all available categories
                        </div>
                        <div class="example-btn" data-message="What did we discuss earlier?">
                            <div class="example-title">Memory Query</div>
                            What did we discuss earlier?
                        </div>
                        <div class="example-btn" data-message="Research and analyze technology trends from multiple sources and provide a comprehensive report">
                            <div class="example-title">Chain Query</div>
                            Research and analyze technology trends
                        </div>
                    </div>
                </div>
            </div>

            <div class="response-section">
                <div>
                    <div class="response-title">💬 AI Response</div>
                    <div id="loading" class="loading">
                        <div class="spinner"></div>
                        <div>Processing your request...</div>
                    </div>
                    <div id="ai-response" class="response-box ai-response">
                        <em>Your AI response will appear here...</em>
                    </div>
                </div>

                <div>
                    <div class="response-title">📄 Technical Details</div>
                    <div id="tech-response" class="response-box tech-response">
                        <em>Technical response data will appear here...</em>
                    </div>
                </div>
            </div>
            <div class="mcp-data-section" style="display: none;" id="mcp-data-section">
                <h3>🔧 MCP Data Options</h3>
                <div class="form-group">
                    <label>Conversation ID:</label>
                    <input type="text" id="mcp-conversation-id" value="default">
                </div>
                <div class="form-group">
                    <label>Entity Types (optional):</label>
                    <input type="text" id="mcp-entity-types" placeholder="ids,names,titles (comma-separated)">
                </div>
                <div class="form-group" id="search-criteria-group" style="display: none;">
                    <label>Search Criteria (JSON):</label>
                    <textarea id="search-criteria" placeholder='{"tool_name": "tool_name", "entity_value": "value"}'></textarea>
                </div>
            </div>
        </div>
    </div>

    <script>
        const CONFIG = {
            serverUrl: 'http://localhost:5001',
            endpoints: {
                '/chat': { needsMessage: true, hasMemory: false },
                '/chat/memory': { needsMessage: true, hasMemory: true },
                '/chat/chain': { needsMessage: true, hasMemory: true },
                '/analyze': { needsMessage: true, hasMemory: false },
                '/tools': { needsMessage: false, hasMemory: false },
                '/status': { needsMessage: false, hasMemory: false },
                '/test': { needsMessage: false, hasMemory: false },
                '/initialize': { needsMessage: false, hasMemory: false },
                '/memory/mcp-data': { needsMessage: false, hasMemory: false, isMcpData: true },
                '/memory/entities': { needsMessage: false, hasMemory: false, isMcpData: true },
                '/memory/search-mcp': { needsMessage: false, hasMemory: false, isMcpData: true, needsSearch: true }
            }
        };

        const elements = {
            endpointSelect: null,
            memorySection: null,
            messageSection: null,
            messageInput: null,
            conversationId: null,
            sendButton: null,
            loading: null,
            aiResponse: null,
            techResponse: null,
            statusIndicator: null,
            statusText: null
        };

        function initElements() {
            elements.endpointSelect = document.getElementById('endpoint-select');
            elements.memorySection = document.getElementById('memory-section');
            elements.messageSection = document.getElementById('message-section');
            elements.messageInput = document.getElementById('message-input');
            elements.conversationId = document.getElementById('conversation-id');
            elements.sendButton = document.getElementById('send-button');
            elements.loading = document.getElementById('loading');
            elements.aiResponse = document.getElementById('ai-response');
            elements.techResponse = document.getElementById('tech-response');
            elements.statusIndicator = document.getElementById('status-indicator');
            elements.statusText = document.getElementById('status-text');
        }

        function setExampleMessage(message) {
            if (elements.messageInput) {
                elements.messageInput.value = message;
            }
        }

        function updateEndpointUI() {
            const endpoint = elements.endpointSelect.value;
            const config = CONFIG.endpoints[endpoint];

            if (elements.messageSection) {
                elements.messageSection.style.display = config.needsMessage ? 'block' : 'none';
            }

            if (elements.memorySection) {
                elements.memorySection.style.display = config.hasMemory ? 'block' : 'none';
            }

            // NEW: Show MCP data section
            const mcpDataSection = document.getElementById('mcp-data-section');
            if (mcpDataSection) {
                mcpDataSection.style.display = config.isMcpData ? 'block' : 'none';
            }

            // NEW: Show search criteria for search endpoints
            const searchCriteriaGroup = document.getElementById('search-criteria-group');
            if (searchCriteriaGroup) {
                searchCriteriaGroup.style.display = config.needsSearch ? 'block' : 'none';
            }
        }

        function showLoading() {
            if (elements.loading) elements.loading.style.display = 'block';
            if (elements.sendButton) elements.sendButton.disabled = true;
            if (elements.aiResponse) elements.aiResponse.innerHTML = '<em>Processing...</em>';
            if (elements.techResponse) elements.techResponse.innerHTML = '<em>Processing...</em>';
        }

        function hideLoading() {
            if (elements.loading) elements.loading.style.display = 'none';
            if (elements.sendButton) elements.sendButton.disabled = false;
        }

        function updateStatus(online) {
            if (elements.statusIndicator) {
                elements.statusIndicator.className = 'status-indicator' + (online ? '' : ' status-offline');
            }
            if (elements.statusText) {
                elements.statusText.textContent = online ? 'Server Online' : 'Server Offline';
            }
        }

        function displayResponse(data, success) {
            const aiContent = success && data.response ? data.response : 
                             success ? 'Request completed successfully' : 
                             'Error: ' + (data.error || 'Unknown error');

            const techContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);

            if (elements.aiResponse) {
                elements.aiResponse.innerHTML = aiContent;
            }

            if (elements.techResponse) {
                elements.techResponse.textContent = techContent;
            }
        }

        async function makeRequest() {
            const endpoint = elements.endpointSelect.value;
            const config = CONFIG.endpoints[endpoint];

            showLoading();

            try {
                const url = CONFIG.serverUrl + endpoint;
                const options = {
                    headers: { 'Content-Type': 'application/json' }
                };
                if (config.isMcpData) {
                    const conversationId = document.getElementById('mcp-conversation-id').value.trim() || 'default';

                    if (endpoint === '/memory/mcp-data' || endpoint === '/memory/entities') {
                        url += `/${conversationId}`;

                        // Add entity types as query parameters
                        const entityTypes = document.getElementById('mcp-entity-types').value.trim();
                        if (entityTypes) {
                            const types = entityTypes.split(',').map(t => t.trim());
                            const params = types.map(t => `entity_types=${encodeURIComponent(t)}`).join('&');
                            url += `?${params}`;
                        }

                        options.method = 'GET';
                    } else if (endpoint === '/memory/search-mcp') {
                        url += `/${conversationId}`;
                        options.method = 'POST';

                        const searchCriteria = document.getElementById('search-criteria').value.trim();
                        let criteria = {};
                        if (searchCriteria) {
                            try {
                                criteria = JSON.parse(searchCriteria);
                            } catch (e) {
                                throw new Error('Invalid JSON in search criteria');
                            }
                        }

                        options.body = JSON.stringify({ criteria });
                    }
                } else {
                    if (config.needsMessage) {
                        const message = elements.messageInput.value.trim();
                        if (!message) {
                            throw new Error('Please enter a message');
                        }

                        options.method = 'POST';
                        const body = { message: message };

                        if (config.hasMemory && elements.conversationId.value.trim()) {
                            body.conversation_id = elements.conversationId.value.trim();
                        }

                        options.body = JSON.stringify(body);
                    } else {
                        options.method = endpoint === '/initialize' ? 'POST' : 'GET';
                    }
                }
                const response = await fetch(url, options);
                const data = await response.json();

                displayResponse(data, response.ok);
                updateStatus(true);

            } catch (error) {
                displayResponse({ error: error.message }, false);
                updateStatus(false);
            } finally {
                hideLoading();
            }
        }

        async function testConnection() {
            try {
                const response = await fetch(CONFIG.serverUrl + '/health');
                const success = response.ok;
                updateStatus(success);
                
                if (success) {
                    const data = await response.json();
                    displayResponse(data, true);
                }
            } catch (error) {
                updateStatus(false);
                displayResponse({ error: 'Cannot connect to server' }, false);
            }
        }

        function setupEventListeners() {
            if (elements.endpointSelect) {
                elements.endpointSelect.addEventListener('change', updateEndpointUI);
            }

            if (elements.sendButton) {
                elements.sendButton.addEventListener('click', makeRequest);
            }

            document.querySelectorAll('.example-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const message = this.getAttribute('data-message');
                    setExampleMessage(message);
                });
            });

            if (elements.messageInput) {
                elements.messageInput.addEventListener('keydown', function(event) {
                    if (event.ctrlKey && event.key === 'Enter') {
                        makeRequest();
                    }
                });
            }
        }

        function initApp() {
            initElements();
            setupEventListeners();
            updateEndpointUI();
            testConnection();
        }

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initApp);
        } else {
            initApp();
        }

        window.setExample = setExampleMessage;
        window.makeRequest = makeRequest;
        window.updateEndpointDescription = updateEndpointUI;
    </script>
</body>
</html>"""
@dataclass
class MCPTool:
    """MCP Tool representation matching your API format"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
    def to_dict(self):
        return asdict(self)

@dataclass
class ChatMessage:
    """Enhanced chat message with comprehensive MCP data storage"""
    role: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    raw_mcp_data: Dict[str, Any] = None  # NEW: Store raw MCP response
    extracted_entities: Dict[str, Any] = None  # NEW: Store extracted keys/IDs/names
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.raw_mcp_data is None:
            self.raw_mcp_data = {}
        if self.extracted_entities is None:
            self.extracted_entities = {}

@dataclass
class ConversationMemory:
    """Enhanced memory with MCP data tracking"""
    conversation_id: str
    messages: List[ChatMessage]
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any] = None
    mcp_data_summary: Dict[str, Any] = None  # NEW: Summary of all MCP data
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.mcp_data_summary is None:
            self.mcp_data_summary = {"total_tool_calls": 0, "tools_used": [], "entities_collected": []}


class ChatMemoryManager:
    """Enhanced memory manager with MCP data extraction and storage"""
    
    def __init__(self, max_conversations: int = 100, max_messages_per_conversation: int = 50):
        self.conversations: Dict[str, ConversationMemory] = {}
        self.max_conversations = max_conversations
        self.max_messages_per_conversation = max_messages_per_conversation
        self.lock = threading.Lock()
        
    def add_message(self, conversation_id: str, role: str, content: str, 
                   metadata: Dict[str, Any] = None, raw_mcp_data: Dict[str, Any] = None,
                   extracted_entities: Dict[str, Any] = None):
        """Enhanced message storage with MCP data"""
        with self.lock:
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ConversationMemory(
                    conversation_id=conversation_id,
                    messages=[],
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )
            
            conversation = self.conversations[conversation_id]
            
            # Extract entities from MCP data if provided
            if raw_mcp_data and not extracted_entities:
                extracted_entities = self._extract_entities_from_mcp_data(raw_mcp_data)
            
            message = ChatMessage(
                role=role,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {},
                raw_mcp_data=raw_mcp_data or {},
                extracted_entities=extracted_entities or {}
            )
            
            conversation.messages.append(message)
            conversation.last_updated = datetime.now()
            
            # Update conversation MCP summary
            if raw_mcp_data and role == "assistant":
                self._update_mcp_summary(conversation, raw_mcp_data, extracted_entities)
            
            # Trim messages if exceeding limit
            if len(conversation.messages) > self.max_messages_per_conversation:
                system_messages = [m for m in conversation.messages if m.role == 'system']
                recent_messages = [m for m in conversation.messages if m.role != 'system'][-self.max_messages_per_conversation:]
                conversation.messages = system_messages + recent_messages
            
            self._cleanup_old_conversations()
    def get_conversation_context(self, conversation_id: str, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """Get conversation context optimized for token limits"""
        if conversation_id not in self.conversations:
            return []
        
        conversation = self.conversations[conversation_id]
        context = []
        total_tokens = 0
        
        # Start from most recent messages and work backwards
        for message in reversed(conversation.messages):
            message_tokens = len(message.content) // 4
            
            if total_tokens + message_tokens > max_tokens:
                break
                
            context.insert(0, {
                "role": message.role,
                "content": message.content
            })
            total_tokens += message_tokens
        
        return context
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """Get a summary of the conversation for context"""
        if conversation_id not in self.conversations:
            return ""
        
        conversation = self.conversations[conversation_id]
        if len(conversation.messages) < 3:
            return ""
        
        summary_points = []
        for message in conversation.messages[-10:]:
            if message.role == 'user' and len(message.content) > 20:
                summary_points.append(f"User asked: {message.content[:100]}...")
            elif message.role == 'assistant' and message.metadata.get('tool_used'):
                summary_points.append(f"Used tool: {message.metadata['tool_used']}")
        
        return " | ".join(summary_points)
    
    def _extract_entities_from_mcp_data(self, mcp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract useful entities from MCP response data"""
        entities = {
            "ids": [],
            "keys": [],
            "names": [],
            "titles": [],
            "urls": [],
            "dates": [],
            "categories": [],
            "authors": [],
            "sources": [],
            "counts": {}
        }
        
        def extract_recursive(data, path=""):
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Extract IDs
                    if key.lower() in ['id', '_id', 'key', 'uuid', 'identifier']:
                        entities["ids"].append({"key": key, "value": value, "path": current_path})
                    
                    # Extract names/titles
                    elif key.lower() in ['name', 'title', 'headline', 'subject']:
                        entities["names"].append({"key": key, "value": value, "path": current_path})
                        if key.lower() == 'title':
                            entities["titles"].append({"key": key, "value": value, "path": current_path})
                    
                    # Extract URLs
                    elif key.lower() in ['url', 'link', 'href', 'src']:
                        entities["urls"].append({"key": key, "value": value, "path": current_path})
                    
                    # Extract dates
                    elif key.lower() in ['date', 'created_at', 'updated_at', 'published_at', 'timestamp']:
                        entities["dates"].append({"key": key, "value": value, "path": current_path})
                    
                    # Extract categories
                    elif key.lower() in ['category', 'type', 'section', 'tag']:
                        entities["categories"].append({"key": key, "value": value, "path": current_path})
                    
                    # Extract authors
                    elif key.lower() in ['author', 'writer', 'creator', 'by']:
                        entities["authors"].append({"key": key, "value": value, "path": current_path})
                    
                    # Extract sources
                    elif key.lower() in ['source', 'provider', 'origin']:
                        entities["sources"].append({"key": key, "value": value, "path": current_path})
                    
                    # Store all keys for reference
                    entities["keys"].append({"key": key, "type": type(value).__name__, "path": current_path})
                    
                    # Recurse into nested structures
                    extract_recursive(value, current_path)
                    
            elif isinstance(data, list):
                entities["counts"][f"{path}_count"] = len(data)
                for i, item in enumerate(data):
                    extract_recursive(item, f"{path}[{i}]")
        
        if mcp_data.get("result"):
            extract_recursive(mcp_data["result"])
        
        return entities
    
    def _update_mcp_summary(self, conversation: ConversationMemory, mcp_data: Dict[str, Any], 
                           extracted_entities: Dict[str, Any]):
        """Update conversation MCP data summary"""
        summary = conversation.mcp_data_summary
        summary["total_tool_calls"] += 1
        
        # Track tools used
        if mcp_data.get("tool_name"):
            if mcp_data["tool_name"] not in summary["tools_used"]:
                summary["tools_used"].append(mcp_data["tool_name"])
        
        # Aggregate entities
        for entity_type, entities in extracted_entities.items():
            if entities and entity_type != "keys":
                if entity_type not in summary["entities_collected"]:
                    summary["entities_collected"].append(entity_type)
    
    def get_mcp_data_from_conversation(self, conversation_id: str, 
                                      entity_types: List[str] = None) -> Dict[str, Any]:
        """Get all MCP data from a conversation, optionally filtered by entity types"""
        if conversation_id not in self.conversations:
            return {}
        
        conversation = self.conversations[conversation_id]
        mcp_data = {
            "conversation_id": conversation_id,
            "summary": conversation.mcp_data_summary,
            "detailed_data": [],
            "aggregated_entities": {}
        }
        
        # Collect all MCP data from messages
        for message in conversation.messages:
            if message.raw_mcp_data:
                entry = {
                    "timestamp": message.timestamp.isoformat(),
                    "tool_used": message.raw_mcp_data.get("tool_name"),
                    "raw_data": message.raw_mcp_data,
                    "extracted_entities": message.extracted_entities
                }
                mcp_data["detailed_data"].append(entry)
        
        # Aggregate entities across all messages
        for message in conversation.messages:
            if message.extracted_entities:
                for entity_type, entities in message.extracted_entities.items():
                    if entity_types is None or entity_type in entity_types:
                        if entity_type not in mcp_data["aggregated_entities"]:
                            mcp_data["aggregated_entities"][entity_type] = []
                        if isinstance(entities, list):
                            mcp_data["aggregated_entities"][entity_type].extend(entities)
        
        return mcp_data
    
    def search_mcp_data(self, conversation_id: str, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search MCP data based on criteria"""
        if conversation_id not in self.conversations:
            return []
        
        conversation = self.conversations[conversation_id]
        results = []
        
        for message in conversation.messages:
            if not message.raw_mcp_data:
                continue
                
            match = True
            
            # Check tool name
            if "tool_name" in search_criteria:
                if message.raw_mcp_data.get("tool_name") != search_criteria["tool_name"]:
                    match = False
            
            # Check for specific entity values
            if "entity_value" in search_criteria and message.extracted_entities:
                found_value = False
                for entity_type, entities in message.extracted_entities.items():
                    if isinstance(entities, list):
                        for entity in entities:
                            if isinstance(entity, dict) and entity.get("value") == search_criteria["entity_value"]:
                                found_value = True
                                break
                if not found_value:
                    match = False
            
            if match:
                results.append({
                    "timestamp": message.timestamp.isoformat(),
                    "message_content": message.content,
                    "raw_mcp_data": message.raw_mcp_data,
                    "extracted_entities": message.extracted_entities
                })
        
        return results
    def _cleanup_old_conversations(self):
        """Remove old conversations to maintain memory limits"""
        if len(self.conversations) <= self.max_conversations:
            return

        sorted_conversations = sorted(
            self.conversations.items(),
            key=lambda x: x[1].last_updated
        )

        conversations_to_remove = len(self.conversations) - self.max_conversations
        for i in range(conversations_to_remove):
            del self.conversations[sorted_conversations[i][0]]


class PromptBreaker:
    """Advanced prompt breaking for handling large queries"""
    
    def __init__(self, max_chunk_tokens: int = 2000, overlap_tokens: int = 200):
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def break_prompt(self, prompt: str, context: str = "") -> List[Dict[str, Any]]:
        """Break large prompts into manageable chunks"""
        total_tokens = self.estimate_tokens(prompt + context)
        
        if total_tokens <= self.max_chunk_tokens:
            return [{
                "chunk_id": 0,
                "content": prompt,
                "context": context,
                "is_final": True,
                "total_chunks": 1
            }]
        
        chunks = self._split_by_logical_boundaries(prompt)
        
        if any(self.estimate_tokens(chunk) > self.max_chunk_tokens for chunk in chunks):
            chunks = self._split_by_sentences(prompt)
        
        result_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_context = context
            if i > 0:
                chunk_context += f"\n\nPrevious context: Processing part {i+1} of {len(chunks)} of a larger query."
            
            result_chunks.append({
                "chunk_id": i,
                "content": chunk,
                "context": chunk_context,
                "is_final": i == len(chunks) - 1,
                "total_chunks": len(chunks)
            })
        
        return result_chunks
    
    def _split_by_logical_boundaries(self, text: str) -> List[str]:
        """Split text by logical boundaries like paragraphs, sections"""
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if self.estimate_tokens(current_chunk + paragraph) > self.max_chunk_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    chunks.extend(self._split_by_sentences(paragraph))
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences when paragraphs are too large"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if self.estimate_tokens(current_chunk + sentence) > self.max_chunk_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    chunks.extend(self._split_by_words(sentence))
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_words(self, text: str) -> List[str]:
        """Split text by words as last resort"""
        words = text.split()
        chunks = []
        current_chunk = ""
        
        for word in words:
            if self.estimate_tokens(current_chunk + " " + word) > self.max_chunk_tokens:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = word
                else:
                    chunks.append(word)
            else:
                current_chunk += " " + word if current_chunk else word
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

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
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
        except:
            logger.warning("spaCy model not available, using simple extraction")
            self.nlp = None
            self.spacy_available = False
        
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
        
        self.news_categories = [
            'politics', 'sports', 'technology', 'business', 'entertainment',
            'health', 'science', 'world', 'national',
            'opinion', 'lifestyle', 'travel', 'food', 'fashion', 'education'
        ]
        
        self.news_sources = ['zee_news', 'wion']
        
        # Current ArangoDB MCP tools (5 graph analysis tools)
        self.current_tools = [
            'find_articles_by_entity',
            'get_top_mentioned_entities', 
            'find_articles_by_entity_and_keywords',
            'find_co_occurring_entities',
            'get_paginated_articles_with_entities'
        ]
        
        self.locations = [
            'usa', 'uk', 'canada', 'australia', 'europe', 'asia',
            'africa', 'america', 'china', 'russia', 'india', 'japan',
            'new york', 'london', 'paris', 'tokyo', 'washington', 'israel'
        ]
        
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',
            r'\d{2}/\d{2}/\d{4}',
            r'\d{2}-\d{2}-\d{4}',
            r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        self.number_pattern = r'\b\d+\b'
    
    def extract_entities(self, query: str) -> ExtractedEntities:
        """Extract all relevant entities from user query"""
        query_lower = query.lower()
        entities = ExtractedEntities()
        
        entities.intent = self._extract_intent(query_lower)
        entities.dates = self._extract_dates(query)
        entities.date_ranges = self._extract_date_ranges(query)
        entities.time_keywords = self._extract_time_keywords(query_lower)
        
        if self.spacy_available:
            entities.names, entities.search_terms = self._extract_names_spacy(query)
        else:
            entities.names, entities.search_terms = self._extract_names_simple(query)
        
        entities.categories = self._extract_categories(query_lower)
        entities.sources = self._extract_sources(query_lower)
        entities.locations = self._extract_locations(query_lower)
        entities.authors = self._extract_authors(query)
        entities.keywords = self._extract_keywords(query_lower)
        entities.numbers = self._extract_numbers(query)
        
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
        return 'search'
    
    def _extract_dates(self, query: str) -> List[str]:
        """Extract explicit dates from query"""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            dates.extend(matches)
        
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
            'entity_search': {
                'tools': [
                    'find_articles_by_entity',
                    'find_articles_by_entity_and_keywords'
                ],
                'keywords': ['search', 'find', 'look for', 'entity', 'person', 'organization', 'location'],
                'entities': ['search_terms', 'keywords', 'names', 'entities']
            },
            'entity_analysis': {
                'tools': [
                    'get_top_mentioned_entities',
                    'find_co_occurring_entities'
                ],
                'keywords': ['top', 'most', 'mentioned', 'popular', 'frequent', 'co-occurring', 'related', 'associated'],
                'entities': ['entities', 'names']
            },
            'browse_paginated': {
                'tools': [
                    'get_paginated_articles_with_entities'
                ],
                'keywords': ['list', 'all', 'browse', 'display', 'paginated', 'page'],
                'entities': ['keywords', 'page_numbers']
            }
        }
        
        self.tool_to_category = {}
        for category, info in self.tool_categories.items():
            for tool in info['tools']:
                self.tool_to_category[tool] = category
    
    def get_relevant_categories(self, entities: ExtractedEntities) -> List[str]:
        """Get relevant tool categories based on extracted entities"""
        relevant_categories = []
        
        intent_mapping = {
            'search': ['entity_search'],
            'list': ['browse_paginated'],
            'recent': ['entity_search'],
            'specific': ['entity_search']
        }
        
        if entities.intent in intent_mapping:
            relevant_categories.extend(intent_mapping[entities.intent])
        
        # Entity-focused queries should use entity analysis tools
        if entities.names or entities.search_terms:
            relevant_categories.extend(['entity_analysis'])
        
        # Search terms and keywords should use entity search tools
        if entities.categories or entities.authors or entities.search_terms:
            relevant_categories.extend(['entity_search'])
        
        # Default to entity search if no specific intent
        if not relevant_categories:
            relevant_categories = ['entity_search', 'browse_paginated']
        
        return list(set(relevant_categories))

class SmartToolSelector:
    """Select the most appropriate tools based on entities and context"""
    def __init__(self, tools: Dict[str, MCPTool]):
        SmartAIAgent.tools = tools
        self.categorizer = ToolCategorizer()
        self.entity_extractor = EntityExtractor()
    
    def select_tools(self, query: str) -> Dict[str, Any]:
        """Select the most relevant tools for a query"""
        entities = self.entity_extractor.extract_entities(query)
        relevant_categories = self.categorizer.get_relevant_categories(entities)
        
        selected_tools = {}
        tool_scores = defaultdict(int)
        
        for category in relevant_categories:
            if category in self.categorizer.tool_categories:
                for tool_name in self.categorizer.tool_categories[category]['tools']:
                    if tool_name in SmartAIAgent.tools:
                        tool_scores[tool_name] += 10
        
        for tool_name, tool in SmartAIAgent.tools.items():
            score = tool_scores[tool_name]
            
            # Entity-focused scoring
            if entities.names or entities.search_terms:
                if 'entity' in tool_name:
                    score += 5
                if 'co_occurring' in tool_name or 'top_mentioned' in tool_name:
                    score += 3
            
            # Search terms and keywords boost entity search tools
            if entities.search_terms or entities.keywords:
                if 'find_articles_by_entity' in tool_name:
                    score += 5
                if 'find_articles_by_entity_and_keywords' in tool_name:
                    score += 7  # Higher score for keyword combination
            
            # Categories and authors still relevant for entity search
            if entities.categories or entities.authors:
                if 'find_articles_by_entity' in tool_name:
                    score += 3
            
            # Boost analysis tools for analytical queries
            if any(word in query.lower() for word in ['top', 'most', 'popular', 'frequent', 'analysis', 'related']):
                if 'top_mentioned' in tool_name or 'co_occurring' in tool_name:
                    score += 5
            
            if score > 0:
                tool_scores[tool_name] = score
        
        sorted_tools = sorted(tool_scores.items(), key=lambda x: x[1], reverse=True)
        top_tools = sorted_tools[:5]
        
        for tool_name, score in top_tools:
            selected_tools[tool_name] = {
                'tool': SmartAIAgent.tools[tool_name],
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
        """Build optimized context for LLM with only relevant tools"""
        entities = selection_result['entities']
        selected_tools = selection_result['selected_tools']
        
        context_parts = []
        
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
        
        context_parts.append("\nRELEVANT TOOLS:")
        context_parts.append("=" * 40)
        
        for tool_name, tool_info in selected_tools.items():
            tool = tool_info['tool']
            context_parts.append(f"\nTool: {tool_name} (Score: {tool_info['score']})")
            context_parts.append(f"Description: {tool.description}")
            
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
                
                optional = [p for p in properties.keys() if p not in required]
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

class PromptChainer:
    """Advanced prompt chaining for complex multi-step tasks"""
    
    def __init__(self, ollama_client, mcp_client):
        self.ollama_client = ollama_client
        self.mcp_client = mcp_client
        self.chain_history = []
        
    def identify_chain_requirements(self, query: str, entities: ExtractedEntities) -> Dict[str, Any]:
        """Analyze if query requires prompt chaining and identify subtasks"""
        
        chain_indicators = [
            'analyze and summarize', 'research and report', 'find and compare',
            'gather information and create', 'collect data and analyze',
            'step by step', 'comprehensive report', 'detailed analysis'
        ]
        
        query_lower = query.lower()
        needs_chaining = any(indicator in query_lower for indicator in chain_indicators)
        
        entity_complexity = 0
        if entities.dates or entities.date_ranges: entity_complexity += 1
        if entities.categories: entity_complexity += 1
        if entities.authors: entity_complexity += 1
        if entities.search_terms: entity_complexity += 1
        if entities.locations: entity_complexity += 1
        
        if entity_complexity >= 3 or needs_chaining:
            return {
                "needs_chaining": True,
                "complexity_score": entity_complexity,
                "suggested_steps": self._suggest_chain_steps(query, entities)
            }
        
        return {"needs_chaining": False}
    
    def _suggest_chain_steps(self, query: str, entities: ExtractedEntities) -> List[Dict[str, Any]]:
        """Suggest optimal chain steps based on query analysis"""
        
        steps = []
        
        if entities.search_terms or entities.categories:
            steps.append({
                "step_id": 1,
                "type": "data_collection",
                "description": "Gather relevant articles and information",
                "tools_needed": ["search", "category_filter"],
                "prompt_template": "Find articles about {search_terms} in {categories}"
            })
        
        if entities.dates or entities.date_ranges or entities.time_keywords:
            steps.append({
                "step_id": 2,
                "type": "temporal_analysis",
                "description": "Analyze information within specified time frames",
                "tools_needed": ["date_range_search"],
                "prompt_template": "Filter and analyze data from {date_range}"
            })
        
        if entities.authors or entities.locations:
            steps.append({
                "step_id": 3,
                "type": "entity_analysis",
                "description": "Analyze by specific entities (authors, locations)",
                "tools_needed": ["author_search", "location_filter"],
                "prompt_template": "Focus analysis on {authors} and {locations}"
            })
        
        steps.append({
            "step_id": len(steps) + 1,
            "type": "synthesis",
            "description": "Synthesize findings and create comprehensive response",
            "tools_needed": [],
            "prompt_template": "Synthesize all collected information into a comprehensive response"
        })
        
        return steps
    
    def execute_chain(self, query: str, chain_steps: List[Dict[str, Any]], 
                     selection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the prompt chain with tool integration"""
        
        chain_results = []
        accumulated_context = ""
        
        for step in chain_steps:
            logger.info(f"EXECUTING CHAIN STEP {step['step_id']}: {step['type']}")
            
            step_prompt = self._build_step_prompt(
                query, step, accumulated_context, selection_result
            )
            
            step_result = self._execute_chain_step(step_prompt, step, selection_result)
            chain_results.append(step_result)
            
            if step_result.get("success"):
                accumulated_context += f"\n\nStep {step['step_id']} Result:\n{step_result.get('response', '')}"
            
            if not step_result.get("success") and step['type'] != 'synthesis':
                logger.warning(f"Step {step['step_id']} failed, but continuing chain")
        
        return self._synthesize_chain_results(chain_results, query)
    
    def _build_step_prompt(self, original_query: str, step: Dict[str, Any], 
                          context: str, selection_result: Dict[str, Any]) -> str:
        """Build prompt for individual chain step"""
        
        entities = selection_result['entities']
        
        step_prompt = f"""CHAIN STEP {step['step_id']}: {step['description']}

ORIGINAL USER QUERY: {original_query}

STEP OBJECTIVE: {step['description']}

{context}

INSTRUCTIONS FOR THIS STEP:
{SmartAIAgent.TOOL_FORMAT_INSTRUCTIONS.format(tools=SmartAIAgent.get_tools_info())}
1. Focus specifically on: {step['description']}
2. Use the most appropriate tool for this step, with appropriate parameters, interpret English like recent to numerical values like dates.
3. If this is a data collection step, gather comprehensive information
4. If this is an analysis step, provide detailed insights
5. If this is a synthesis step, create a comprehensive final response

STEP TYPE: {step['type']}

AVAILABLE ENTITIES:
- Search Terms: {entities.search_terms}
- Categories: {entities.categories}
- Authors: {entities.authors}
- Dates: {entities.dates}
- Locations: {entities.locations}

OUTPUT REQUIREMENTS:
- If tool is needed: Respond with JSON format for tool usage, again use appropriate parameters in that don't skip to use any parameter, even if you are searching like recent it should be used in dates related parameters with current date that is 2023 Feb.
- If analysis is needed: Provide structured analysis
- If synthesis is needed: Create comprehensive final response

Focus on this specific step while keeping the overall objective in mind."""

        return step_prompt
    
    def _execute_chain_step(self, step_prompt: str, step: Dict[str, Any], 
                           selection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual step in the chain"""
        
        system_prompt = self.build_chain_tool_prompt(
            step['type'], 
            step['description'],
            "8. When someone ask for something specific in a date range and you are calling the date_range function, with limit param 100 so that , it is possible to find relevant content from it.\n\nANALYSIS INSTRUCTIONS:\n- Focus on the specific objective of this step\n- Build upon previous step results if available\n- Prepare output that will be useful for subsequent steps\n- Be thorough but focused on this step's purpose\n\nRemember: This is part of a larger analysis chain. Stay focused on THIS step's objective."
        )

        llm_response = self.ollama_client.generate(step_prompt, system_prompt)
        
        return self._handle_chain_step_response(llm_response, step, selection_result)
    
    def _handle_chain_step_response(self, llm_response: str, step: Dict[str, Any], 
                                   selection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle response from chain step (tool usage or analysis)"""
        
        try:
            if llm_response.strip().startswith('{'):
                parsed_response = json.loads(llm_response.strip())
                
                if "action" in parsed_response:
                    tool_name = parsed_response["action"]
                    arguments = parsed_response.get("arguments", {})
                    
                    tool_result = self.mcp_client.execute_tool(tool_name, arguments)
                    
                    if tool_result["success"]:
                        analysis_prompt = f"""Step {step['step_id']} completed using tool '{tool_name}'.

Tool Result:
{json.dumps(tool_result['result'], indent=2)}

Step Objective: {step['description']}

Please provide a focused analysis of this data for step {step['step_id']}.
- Summarize key findings relevant to this step
- Highlight important patterns or insights
- Prepare this information for use in subsequent steps
- Keep the analysis focused on this step's specific objective"""

                        analysis = self.ollama_client.generate(analysis_prompt)
                        
                        return {
                            "step_id": step['step_id'],
                            "step_type": step['type'],
                            "response": analysis,
                            "tool_used": tool_name,
                            "tool_result": tool_result,
                            "success": True
                        }
                    else:
                        return {
                            "step_id": step['step_id'],
                            "step_type": step['type'],
                            "response": f"Tool execution failed: {tool_result['error']}",
                            "error": tool_result['error'],
                            "success": False
                        }
        except json.JSONDecodeError:
            pass
        
        return {
            "step_id": step['step_id'],
            "step_type": step['type'],
            "response": llm_response,
            "success": True
        }
    
    def _synthesize_chain_results(self, chain_results: List[Dict[str, Any]], 
                                 original_query: str) -> Dict[str, Any]:
        """Synthesize all chain step results into final comprehensive response"""
        
        synthesis_context = f"ORIGINAL QUERY: {original_query}\n\n"
        synthesis_context += "CHAIN EXECUTION RESULTS:\n"
        synthesis_context += "=" * 50 + "\n"
        
        successful_steps = []
        for result in chain_results:
            if result.get("success"):
                successful_steps.append(result)
                synthesis_context += f"\nSTEP {result['step_id']} ({result['step_type']}):\n"
                synthesis_context += f"{result['response']}\n"
                synthesis_context += "-" * 30 + "\n"
        
        synthesis_prompt = f"""You have completed a multi-step analysis chain. Please synthesize all findings into a comprehensive, well-structured response.

{synthesis_context}

SYNTHESIS INSTRUCTIONS:
1. Create a comprehensive response that addresses the original query
2. Integrate insights from all successful steps
3. Organize information logically with clear structure
4. Highlight key findings and patterns
5. Provide actionable insights where appropriate
6. Use formatting (headers, lists, etc.) for better readability

RESPONSE REQUIREMENTS:
- Be comprehensive but concise
- Address the original query directly
- Show how different pieces of information connect
- Provide a satisfying conclusion

Create a response that demonstrates the value of the multi-step analysis."""

        final_synthesis = self.ollama_client.generate(synthesis_prompt)
        
        return {
            "response": final_synthesis,
            "chain_steps_executed": len(chain_results),
            "successful_steps": len(successful_steps),
            "chain_results": chain_results,
            "success": True,
            "method": "prompt_chaining"
        }

class MCPClient:
    """MCP Client that works with your specific API format"""
    
    def __init__(self, server_url: str = MCP_URL):
        self.server_url = server_url
        SmartAIAgent.tools = {}
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
                SmartAIAgent.tools = {}
                
                tools_data = []
                if isinstance(data, dict) and 'tools' in data:
                    if isinstance(data['tools'], dict) and 'tools' in data['tools']:
                        tools_data = data['tools']['tools']
                        logger.info(f"PARSED: Found nested tools structure with {len(tools_data)} tools")
                    elif isinstance(data['tools'], list):
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
                        SmartAIAgent.tools[tool.name] = tool
                        logger.info(f"LOADED: Tool '{tool.name}' - {tool.description}")
                
                logger.info(f"SUCCESS: Loaded {len(SmartAIAgent.tools)} tools: {list(SmartAIAgent.tools.keys())}")
                return SmartAIAgent.tools
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
        if not SmartAIAgent.tools:
            return None
        
        if tool_name in SmartAIAgent.tools:
            return tool_name
        
        variations = [
            tool_name.replace('_', '-'),
            tool_name.replace('-', '_'),
            tool_name.lower(),
            tool_name.upper()
        ]
        
        for variation in variations:
            if variation in SmartAIAgent.tools:
                return variation
        
        available_tools = list(SmartAIAgent.tools.keys())
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
        
        # Critical validation: Prevent undefined tool names from reaching MCP server
        if tool_name is None or tool_name == "undefined" or tool_name == "" or not isinstance(tool_name, str):
            logger.error(f"CRITICAL VALIDATION ERROR: Invalid tool_name: {tool_name} (type: {type(tool_name)})")
            return {
                "success": False,
                "error": f"Invalid tool name: '{tool_name}'. Tool name cannot be None, undefined, empty, or non-string.",
                "tool_name": str(tool_name) if tool_name is not None else "None"
            }
        
        # Validate arguments is a dictionary
        if not isinstance(arguments, dict):
            logger.error(f"VALIDATION ERROR: arguments must be a dictionary, got {type(arguments)}")
            return {
                "success": False,
                "error": f"Invalid arguments type: {type(arguments)}. Must be a dictionary.",
                "tool_name": tool_name
            }
        
        actual_tool_name = self._find_similar_tool(tool_name)
        
        if not actual_tool_name:
            available_tools = list(SmartAIAgent.tools.keys())
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
            
            tool = SmartAIAgent.tools[actual_tool_name]
            converted_args = self._convert_parameter_types(arguments, tool.inputSchema)
            
            payload = {
                "name": actual_tool_name,
                "arguments": converted_args
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
                        logger.info(f"SUCCESS: Tool {actual_tool_name} executed (non-standard response)")
                        return {
                            "success": True,
                            "result": result,
                            "tool_name": actual_tool_name,
                            "original_tool_name": tool_name,
                            "endpoint_used": call_endpoint
                        }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "result": response.text,
                        "tool_name": actual_tool_name,
                        "original_tool_name": tool_name,
                        "endpoint_used": call_endpoint
                    }
            else:
                logger.error(f"ERROR: Tool execution failed with status {response.status_code}")
                return self._execute_tool_fallback(actual_tool_name, converted_args, tool_name)
                
        except Exception as e:
            logger.error(f"ERROR: Error executing tool {actual_tool_name}: {e}")
            traceback.print_exc()
            return self._execute_tool_fallback(actual_tool_name, arguments, tool_name)
    
    def _execute_tool_fallback(self, tool_name: str, arguments: Dict[str, Any], original_tool_name: str = None) -> Dict[str, Any]:
        """Fallback execution with simple format"""
        try:
            call_endpoint = f"{self.server_url}/tools/call"
            
            # When using /tools/call directly, we send only name and arguments
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
    """Enhanced AI Agent with memory, prompt breaking, and prompt chaining"""
    tools = None
    
    # CLASS-LEVEL INSTRUCTION CONSTANTS - Centralized to eliminate repetition
    TOOL_FORMAT_INSTRUCTIONS = """TOOL USAGE INSTRUCTIONS:
I am sharing available tools again: {tools}
skip using source filter for now, unless mentioned.
You are highly encouraged to use more parameters, also allowed to repeat in different forms if required, but don't make things on your own like source or something unless mentioned to keep query general.
1. Based on the extracted entities and available tools above, select the MOST APPROPRIATE tool, and give priority to date and time related parameters in tools selection than anything else if date or time is present in query.
the appropriate filters like Dates and whatever is available to be used in the formats, use those parameters very well. Interpret English to numericals if required like recent news to dates etc.
2. If the request requires a tool, respond with JSON in one of these EXACT formats:
   Format 1: {{"action": "use_tool", "tool": "tool_name", "arguments": {{"parameter": "value"}}}}
   Format 2: {{"action": "tool_name", "arguments": {{"parameter": "value"}}}}
   Format 3: {{"action": "tool_name"}} (for tools with no parameters)

   EXAMPLE TOOL CALLS:
   Entity search: {{"action": "find_articles_by_entity", "arguments": {{"entityName": "John Smith"}}}}
   Pagination: {{"action": "get_paginated_articles_with_entities", "arguments": {{"pageNumber": 1, "pageSize": 20}}}}
   Keywords: {{"action": "find_articles_by_entity_and_keywords", "arguments": {{"targetEntityName": "Tesla", "keywords": ["electric", "vehicle"]}}}}
   Top entities: {{"action": "get_top_mentioned_entities", "arguments": {{"limit": 10}}}}

3. Use EXACT tool names from the relevant tools list above
4. For numeric parameters, use actual numbers not strings (e.g., 5 not "5")
5. For array parameters, use proper JSON array syntax: ["item1", "item2"]
6. Match parameter names and types exactly to the tool schema
7. Only include required parameters and relevant optional ones
8. Use appropriate limits for paginated results (typically 10-50 articles)"""

    PARAMETER_MAPPING_HINTS = """PARAMETER MAPPING HINTS:
• For entity searches: use 'entityName' parameter for person/organization/location names
• For target entity searches: use 'targetEntityName' parameter (co-occurrence, keyword searches)
• For keyword searches: use 'keywords' parameter as array of strings ["term1", "term2"]
• For pagination: use 'pageNumber' (1-based) AND 'pageSize' parameters (both required)
• For top entities: use 'limit' parameter (required, typically 10-50)
• For dates: use 'startDate' and 'endDate' parameters (ISO format strings)
• For filtering: use 'category', 'source', 'minMentionCount', 'minMentionTF' parameters"""

    CRITICAL_JSON_RULES = """CRITICAL JSON FORMAT RULES:
• When using tools, respond with ONLY valid JSON - no extra text, no explanations, no markdown
• Start your response directly with { and end with }
• No text before or after the JSON
• Use double quotes for all strings
• Tool names must be EXACT matches from the list above
• Never use undefined, null, or empty tool names"""

    RESPONSE_FORMAT_RULES = """RESPONSE FORMAT: 
• For tools: ONLY JSON (no other text)
• For conversation: Natural language response"""

    # Chain-specific instruction additions
    CHAIN_STEP_ADDITIONS = """   In case the query is having something else as well like summarize this or predict this something not related to fetching but doing English task.
   Then, ignore that and give correct format of json parsing.
   Later, when query is sent it will get handled."""

    MULTI_CHUNK_ADDITIONS = """Remember: Only use tools when they're specifically needed for the user's request. The tools above are pre-selected as most relevant for this query.

MULTI-CHUNK PROCESSING:
- Process this chunk in context of the larger query
- If this is not the final chunk, provide intermediate results
- If this is the final chunk, provide comprehensive results
- Maintain consistency across chunks"""

    # Alternative parameter hints for different contexts
    ALT_PARAMETER_HINTS = """PARAMETER MAPPING HINTS:
- For entity searches: use 'entity' parameter for person/organization/location names
- For keyword searches: use 'keywords' parameter for search terms
- For entity analysis: use 'entity' parameter for entities to analyze
- For limits: use 'limit' parameter (typically 10-50)
- For pagination: use 'page' parameter when browsing results"""

    CHAIN_PARAMETER_HINTS = """PARAMETER MAPPING HINTS:
- For date queries: use start_epoch/end_epoch (Unix timestamps)
- For search queries: use 'query' parameter for search terms
- For limits: use 'limit' parameter (typically 10-50)
- For categories: use exact category names
- For authors: use exact author names"""

    # Available categories from the dataset - for context and guidance
    AVAILABLE_CATEGORIES_CONTEXT = """
AVAILABLE CATEGORIES IN DATASET (with article counts):
Major Categories:
• politics (61,992 articles) • politics,COVID (8,257 articles)  
• entertainment (41,153 articles) • entertainment,COVID (1,240 articles)
• sports (29,084 articles) • sports,COVID (1,089 articles)
• finance (24,797 articles) • finance,COVID (587 articles)
• lifestyle (10,654 articles) • lifestyle,COVID (396 articles)
• world (9,124 articles) • world,COVID (1,659 articles)
• technology (8,468 articles) • technology,COVID (139 articles)

Regional/Location Categories:
• delhi and ncr (48 articles) • bengaluru (14 articles) • north east (38 articles)
• karnataka-2 (10 articles) • telangana (14 articles) • himachal (3 articles)

Specialized Categories:
• editorial (237 articles) • viral (389 articles) • environment (40 articles)
• health and medicine (40 articles) • science and environment (110 articles)
• assembly elections (71 articles) • home and kitchen (156 articles)
• electronics (22 articles) • auto (10 articles) • blog (14 articles)

When using category-based tools, use these exact category names for best results."""
    def __init__(self):
        self.mcp_client = MCPClient()
        self.ollama_client = OllamaClient()
        self.tool_selector = None
        self.memory_manager = ChatMemoryManager()
        self.prompt_breaker = PromptBreaker()
        self.prompt_chainer = None
        self.conversation_history = []
        self.initialized = False
        self.status = {"mcp": False, "ollama": False, "tools": 0}

    @classmethod
    def get_tools_info(cls) -> str:
        """Get tools information in a consistent format"""
        return str(cls.tools) if cls.tools else "No tools available"

    @classmethod
    def build_tool_system_prompt_with_context(cls, context: str, use_alt_hints: bool = False, include_categories: bool = True) -> str:
        """Build complete tool system prompt with context - globally accessible"""
        parameter_hints = cls.ALT_PARAMETER_HINTS if use_alt_hints else cls.PARAMETER_MAPPING_HINTS
        
        category_context = cls.AVAILABLE_CATEGORIES_CONTEXT if include_categories else ""
        
        return f"""You are an intelligent News AI assistant.

{context}

{cls.TOOL_FORMAT_INSTRUCTIONS.format(tools=cls.get_tools_info())}

{parameter_hints}

{category_context}

{cls.CRITICAL_JSON_RULES}

{cls.RESPONSE_FORMAT_RULES}"""

    @classmethod  
    def build_chain_tool_prompt(cls, step_type: str, step_description: str, additional_instructions: str = "", include_categories: bool = True) -> str:
        """Build tool prompt for chain steps - globally accessible"""
        category_context = cls.AVAILABLE_CATEGORIES_CONTEXT if include_categories else ""
        
        return f"""You are executing a chain step.

STEP TYPE: {step_type}
STEP DESCRIPTION: {step_description}

{cls.TOOL_FORMAT_INSTRUCTIONS.format(tools=cls.get_tools_info())}
{cls.CHAIN_STEP_ADDITIONS}
{additional_instructions}

{cls.CHAIN_PARAMETER_HINTS}

{category_context}

Remember: Only use tools when they're specifically needed for the user's request. The tools above are pre-selected as most relevant for this query."""
        
    def initialize(self) -> bool:
        """Initialize all components with detailed status reporting"""
        logger.info("INITIALIZING: Starting AI Agent initialization...")
        
        self.status["mcp"] = self.mcp_client.test_connection()
        self.status["ollama"] = self.ollama_client.test_connection()
        
        if self.status["mcp"]:
            SmartAIAgent.tools = self.mcp_client.fetch_tools()

            self.status["tools"] = len(SmartAIAgent.tools)
            if SmartAIAgent.tools:
                self.tool_selector = SmartToolSelector(SmartAIAgent.tools)
                self.prompt_chainer = PromptChainer(self.ollama_client, self.mcp_client)
        
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
    
    def _should_use_tools(self, user_query: str, selection_result: Dict[str, Any]) -> bool:
        """Determine if the query should use tools based on intent and available tools"""
        
        if len(selection_result['selected_tools']) == 0:
            return False
        
        entities = selection_result['entities']
        tool_intents = ['search', 'list', 'recent', 'specific']
        
        tool_keywords = [
            'find', 'search', 'show', 'get', 'list', 'recent', 'latest',
            'articles', 'news', 'by author', 'category', 'date', 'when'
        ]
        
        query_lower = user_query.lower()
        
        if entities.intent in tool_intents:
            return True
        
        if any(keyword in query_lower for keyword in tool_keywords):
            return True
        
        if (entities.dates or entities.categories or entities.authors or 
            entities.search_terms or entities.time_keywords):
            return True
        
        return False
    
    def _build_tool_system_prompt(self, context: str) -> str:
        """Build system prompt with tool usage instructions"""
        return self.build_tool_system_prompt_with_context(context)

    def _build_conversational_system_prompt(self, context: str) -> str:
        """Build system prompt for conversational responses"""
        return f"""You are an intelligent News AI assistant.

{context}

INSTRUCTIONS:
- Respond conversationally and helpfully
- Provide informative responses based on your knowledge
- If the user is asking for specific current data, explain what information you would need access to"""
    
    def process_query(self, user_input: str, context: str = None) -> Dict[str, Any]:
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
            selection_result = self.tool_selector.select_tools(user_input)
            optimized_context = self.tool_selector.build_optimized_context(selection_result)
            
            logger.info(f"SMART SELECTION: {selection_result['tool_count']} tools selected")
            logger.info(f"CATEGORIES: {selection_result['relevant_categories']}")
            logger.info(f"SELECTED TOOLS: {list(selection_result['selected_tools'].keys())}")
            
            prompt_chunks = self.prompt_breaker.break_prompt(user_input, optimized_context)
            
            if len(prompt_chunks) == 1:
                result = self._process_single_chunk(
                    prompt_chunks[0], selection_result, "default"
                )
            else:
                result = self._process_multiple_chunks(
                    prompt_chunks, selection_result, "default"
                )
            
            result["execution_time"] = time.time() - start_time
            result["chunks_processed"] = len(prompt_chunks)
            result["entities_extracted"] = selection_result['entities'].__dict__
            result["relevant_categories"] = selection_result['relevant_categories']
            result["selected_tools"] = list(selection_result['selected_tools'].keys())
            
            self.conversation_history.append({
                "user": user_input,
                "assistant": result.get("response", ""),
                "entities": selection_result['entities'].__dict__,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"ERROR: Error processing query: {e}")
            traceback.print_exc()
            return {
                "response": f"Error processing your request: {e}",
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
        
    def process_query_with_memory(self, user_input: str, conversation_id: str = "default") -> Dict[str, Any]:
        """Enhanced memory processing with MCP data storage"""
        if not self.initialized:
            return {
                "response": "Agent not initialized. Please check connections.",
                "success": False,
                "status": self.status
            }
        
        start_time = time.time()
        logger.info(f"PROCESSING WITH MEMORY: User query: {user_input}")
        
        try:
            # Store user message
            self.memory_manager.add_message(conversation_id, "user", user_input)
            
            conversation_context = self.memory_manager.get_conversation_context(
                conversation_id, max_tokens=2000
            )
            
            conversation_summary = self.memory_manager.get_conversation_summary(conversation_id)
            
            selection_result = self.tool_selector.select_tools(user_input)
            optimized_context = self.tool_selector.build_optimized_context(selection_result)
            
            memory_context = ""
            if conversation_context:
                memory_context = "\n\nCONVERSATION HISTORY:\n"
                for msg in conversation_context[-5:]:
                    memory_context += f"{msg['role'].upper()}: {msg['content']}\n"
            
            if conversation_summary:
                memory_context += f"\nCONVERSATION SUMMARY: {conversation_summary}\n"
            
            full_context = optimized_context + memory_context
            prompt_chunks = self.prompt_breaker.break_prompt(user_input, full_context)
            
            if len(prompt_chunks) == 1:
                result = self._process_single_chunk(
                    prompt_chunks[0], selection_result, conversation_id
                )
            else:
                result = self._process_multiple_chunks(
                    prompt_chunks, selection_result, conversation_id
                )
            
            # Enhanced storage with MCP data
            metadata = {
                "tool_used": result.get("tool_used"),
                "execution_time": result.get("execution_time"),
                "chunks_processed": len(prompt_chunks)
            }
            
            raw_mcp_data = result.get("mcp_storage_data") or result.get("tool_result", {})
            
            self.memory_manager.add_message(
                conversation_id, 
                "assistant", 
                result.get("response", ""),
                metadata=metadata,
                raw_mcp_data=raw_mcp_data,
                extracted_entities=None  # Will be auto-extracted
            )
            
            result["conversation_id"] = conversation_id
            result["chunks_processed"] = len(prompt_chunks)
            result["execution_time"] = time.time() - start_time
            
            return result
            
        except Exception as e:
            logger.error(f"ERROR: Error processing query with memory: {e}")
            return {
                "response": f"Error processing your request: {e}",
                "success": False,
                "error": str(e),
                "conversation_id": conversation_id
            }    
    def process_query_with_chaining(self, user_input: str, conversation_id: str = "default") -> Dict[str, Any]:
        """Process query with intelligent chaining decision"""
        
        if not self.initialized:
            return {
                "response": "Agent not initialized",
                "success": False,
                "status": self.status
            }
        
        start_time = time.time()
        
        try:
            selection_result = self.tool_selector.select_tools(user_input)
            chain_analysis = self.prompt_chainer.identify_chain_requirements(
                user_input, selection_result['entities']
            )
            
            if chain_analysis.get("needs_chaining"):
                logger.info(f"CHAIN DETECTED: Complexity score {chain_analysis['complexity_score']}")
                
                result = self.prompt_chainer.execute_chain(
                    user_input, 
                    chain_analysis['suggested_steps'],
                    selection_result
                )
                
                result["chaining_used"] = True
                result["complexity_score"] = chain_analysis['complexity_score']
                
            else:
                logger.info("STANDARD PROCESSING: No chaining needed")
                result = self.process_query_with_memory(user_input, conversation_id)
                result["chaining_used"] = False
            
            result["execution_time"] = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"ERROR: Error in chaining process: {e}")
            return {
                "response": f"Error processing request: {e}",
                "success": False,
                "error": str(e)
            }
    
    def _process_single_chunk(self, chunk: Dict[str, Any], selection_result: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """Process a single chunk with smart tool instruction inclusion"""
        
        should_use_tools = self._should_use_tools(chunk['content'], selection_result)
        
        if should_use_tools:
            system_prompt = self._build_tool_system_prompt(chunk['context'])
        else:
            system_prompt = self._build_conversational_system_prompt(chunk['context'])

        llm_response = self.ollama_client.generate(
            prompt=chunk['content'],
            system_prompt=system_prompt
        )
        
        return self._handle_llm_response(llm_response, chunk['content'], selection_result)
    
    def _process_multiple_chunks(self, chunks: List[Dict[str, Any]], selection_result: Dict[str, Any], conversation_id: str) -> Dict[str, Any]:
        """Process multiple chunks and aggregate results"""
        chunk_results = []
        accumulated_context = ""
        has_relevant_tools = len(selection_result['selected_tools']) > 0
        
        for chunk in chunks:
            enhanced_context = chunk['context'] + accumulated_context
            
            if has_relevant_tools:
                system_prompt = f"""You are processing part {chunk['chunk_id'] + 1} of {chunk['total_chunks']} of a larger query.

{enhanced_context}

{self.TOOL_FORMAT_INSTRUCTIONS.format(tools=self.get_tools_info())}
{self.CHAIN_STEP_ADDITIONS}

{self.ALT_PARAMETER_HINTS}

{self.AVAILABLE_CATEGORIES_CONTEXT}

{self.MULTI_CHUNK_ADDITIONS}"""
            else:
                system_prompt = f"""You are processing part {chunk['chunk_id'] + 1} of {chunk['total_chunks']} of a larger query.
{enhanced_context}

INSTRUCTIONS:
- Process this chunk conversationally
- Maintain context across chunks
- If this is the final chunk, provide a comprehensive response"""

            llm_response = self.ollama_client.generate(
                prompt=chunk['content'],
                system_prompt=system_prompt
            )
            
            chunk_result = self._handle_llm_response(llm_response, chunk['content'], selection_result)
            chunk_results.append(chunk_result)
            
            if chunk_result.get("success"):
                accumulated_context += f"\n\nPrevious chunk result: {chunk_result.get('response', '')[:200]}..."
        
        return self._aggregate_chunk_results(chunk_results)
    
    def _aggregate_chunk_results(self, chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple chunks"""
        if not chunk_results:
            return {"response": "No results from chunks", "success": False}
        
        tool_results = [r for r in chunk_results if r.get("tool_used")]
        if tool_results:
            return tool_results[-1]
        
        combined_response = ""
        for i, result in enumerate(chunk_results):
            if result.get("success"):
                combined_response += f"Part {i+1}: {result.get('response', '')}\n\n"
        
        return {
            "response": combined_response.strip(),
            "success": True,
            "chunks_processed": len(chunk_results),
            "execution_time": sum(r.get("execution_time", 0) for r in chunk_results)        }

    def _handle_llm_response(self, llm_response: str, original_query: str, selection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced LLM response handling with comprehensive MCP data storage"""
        start_time = time.time()
        
        try:
            # Clean and validate the response first
            llm_response = llm_response.strip()
            
            # PREPROCESSING: Fix common LLM JSON formatting issues
            # Handle double braces (template confusion)
            if llm_response.startswith('{{') and llm_response.endswith('}}'):
                llm_response = llm_response[1:-1]  # Remove outer braces
                logger.info(f"PREPROCESSING: Fixed double braces in response")
            
            # Handle multiple opening/closing braces
            if llm_response.count('{{') > 0 or llm_response.count('}}') > 0:
                llm_response = llm_response.replace('{{', '{').replace('}}', '}')
                logger.info(f"PREPROCESSING: Fixed template-style braces")
                logger.info(f"LLM RESPONSE: {llm_response}")
            
            # Enhanced JSON extraction with validation and repair
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}')
            
            if json_start != -1:
                json_part = llm_response[json_start:]  # Take everything after the first {
                
                # Count braces to detect missing closure
                open_braces = json_part.count('{')
                close_braces = json_part.count('}')
                
                # Add missing closing braces if needed
                if open_braces > close_braces:
                    json_part = json_part + ('}' * (open_braces - close_braces))
                    logger.info(f"FIXED JSON: Added {open_braces - close_braces} missing closing braces")
                
                try:
                    parsed_response = json.loads(json_part)
                except json.JSONDecodeError as e:
                    # If still invalid, try stricter extraction
                    if json_end != -1:
                        json_part = llm_response[json_start:json_end + 1]
                        parsed_response = json.loads(json_part)
                logger.info(f"JSON EXTRACTED: {json_part}")
            else:
                # Try parsing entire response as JSON
                if llm_response.startswith('{') and llm_response.endswith('}'):
                    parsed_response = json.loads(llm_response)
                    logger.info(f"FULL RESPONSE AS JSON: {llm_response}")
                else:
                    # Not a JSON response
                    raise json.JSONDecodeError("No valid JSON found", llm_response, 0)
            
            # Validate parsed response structure
            if not isinstance(parsed_response, dict):
                logger.error(f"PARSING ERROR: Response is not a dictionary: {parsed_response}")
                raise json.JSONDecodeError("Response is not a JSON object", str(parsed_response), 0)
            
            # Check for undefined or null action values
            if "action" in parsed_response:
                action_value = parsed_response["action"]
                if action_value is None or action_value == "undefined" or action_value == "":
                    logger.error(f"VALIDATION ERROR: Action is undefined/null/empty: {action_value}")
                    raise ValueError(f"Invalid action value: {action_value}")
            
            is_tool_request, tool_name, arguments = self._is_tool_request(parsed_response)
            
            if is_tool_request and tool_name:
                tool_result = self.mcp_client.execute_tool(tool_name, arguments)
                
                if tool_result["success"]:
                    final_prompt = f"""The user asked: {original_query}

I executed the tool '{tool_result.get('tool_name', tool_name)}' and got this result:
{json.dumps(tool_result['result'], indent=2)}

Please provide a clear, helpful, and well-formatted response based on this tool result.
- If the response is empty or doesn't contain required information, say so
- Summarize the key information
- Present data in a readable format
- Answer the user's question directly
- Be conversational and helpful"""
                    
                    final_response = self.ollama_client.generate(final_prompt)
                    
                    return {
                        "response": final_response,
                        "formatted_response": self._format_response_for_display(final_response),
                        "success": True,
                        "tool_used": tool_result.get('tool_name', tool_name),
                        "tool_arguments": arguments,
                        "tool_result": tool_result,
                        "raw_llm_response": llm_response,
                        # NEW: Include comprehensive MCP data for storage
                        "mcp_storage_data": {
                            "tool_name": tool_result.get('tool_name', tool_name),
                            "arguments": arguments,
                            "result": tool_result.get('result'),
                            "success": tool_result["success"],
                            "execution_details": {
                                "endpoint_used": tool_result.get("endpoint_used"),
                                "method": tool_result.get("method"),
                                "original_tool_name": tool_result.get("original_tool_name")
                            }
                        }
                    }
                else:
                    return {
                        "response": f"Tool execution failed: {tool_result['error']}",
                        "success": False,
                        "tool_used": tool_name,
                        "error": tool_result['error'],
                        "raw_llm_response": llm_response,
                        # Store failed attempt data too
                        "mcp_storage_data": {
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "success": False,
                            "error": tool_result['error']
                        }
                    }
                    
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON PARSING ERROR: {e}")
            logger.error(f"PROBLEMATIC RESPONSE: {llm_response}")
            # Return the raw response as conversational
            return {
                "response": llm_response,
                "formatted_response": self._format_response_for_display(llm_response),
                "success": True,
                "error_info": f"JSON parsing error: {e}"
            }
        except Exception as e:
            logger.error(f"UNEXPECTED ERROR in _handle_llm_response: {e}")
            logger.error(f"RESPONSE THAT CAUSED ERROR: {llm_response}")
            return {
                "response": f"There was an error processing your request: {e}",
                "formatted_response": self._format_response_for_display(f"There was an error processing your request: {e}"),
                "success": False,
                "error_info": f"Unexpected error: {e}"
            }
    def _is_tool_request(self, parsed_response: Dict[str, Any]) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """Determine if response is a tool request and extract tool info"""
        tool_name = None
        arguments = {}
        
        # Validate the parsed response structure
        if not isinstance(parsed_response, dict):
            logger.warning("VALIDATION ERROR: Response is not a dictionary")
            return (False, None, {})
        
        # First format: {"action": "use_tool", "tool": "tool_name", "arguments": {...}}
        if parsed_response.get("action") == "use_tool":
            tool_name = parsed_response.get("tool")
            arguments = parsed_response.get("arguments", {})
            logger.info(f"DETECTED: Standard tool format with use_tool action")
            
        # Second format: {"action": "tool_name", "arguments": {...}}
        elif "action" in parsed_response:
            action_name = parsed_response["action"]
            
            # Validate action_name is not undefined, null, or empty
            if action_name is None or action_name == "undefined" or action_name == "":
                logger.error(f"VALIDATION ERROR: action is undefined/null/empty: {action_name}")
                return (False, None, {})
                
            # Check if action is directly a tool name
            actual_tool_name = self.mcp_client._find_similar_tool(action_name)
            
            if actual_tool_name:
                tool_name = action_name
                arguments = parsed_response.get("arguments", {})
                logger.info(f"DETECTED: Direct tool name format: {action_name}")
            else:
                logger.warning(f"VALIDATION ERROR: Unknown tool name: {action_name}")
                return (False, None, {})
        
        # Final validation - ensure tool_name is valid
        if tool_name is None or tool_name == "undefined" or tool_name == "":
            logger.error(f"VALIDATION ERROR: Final tool_name validation failed: {tool_name}")
            return (False, None, {})
            
        # Make sure arguments is a dictionary
        if not isinstance(arguments, dict):
            logger.warning(f"VALIDATION WARNING: Arguments is not a dictionary, using empty dictionary")
            arguments = {}
            
        logger.info(f"TOOL REQUEST DETECTED: {tool_name} with arguments: {arguments}")
        return (True, tool_name, arguments)
    
    def _format_response_for_display(self, response: str) -> str:
        """Format the LLM response for better display in HTML"""
        import re
        
        formatted = response
        
        formatted = re.sub(r'^### (.+)$', r'<h3>\1</h3>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^## (.+)$', r'<h2>\1</h2>', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^# (.+)$', r'<h1>\1</h1>', formatted, flags=re.MULTILINE)
        
        formatted = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', formatted)
        formatted = re.sub(r'\*([^*]+?)\*', r'<em>\1</em>', formatted)
        
        lines = formatted.split('\n')
        in_list = False
        result_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            if re.match(r'^\d+\.\s+', stripped):
                if not in_list:
                    result_lines.append('<ol>')
                    in_list = 'ol'
                item_text = re.sub(r'^\d+\.\s+', '', stripped)
                result_lines.append(f'<li>{item_text}</li>')
            
            elif stripped.startswith('- ') or stripped.startswith('* '):
                if in_list != 'ul':
                    if in_list == 'ol':
                        result_lines.append('</ol>')
                    result_lines.append('<ul>')
                    in_list = 'ul'
                item_text = stripped[2:].strip()
                result_lines.append(f'<li>{item_text}</li>')
            
            else:
                if in_list:
                    if in_list == 'ol':
                        result_lines.append('</ol>')
                    else:
                        result_lines.append('</ul>')
                    in_list = False
                
                if stripped:
                    result_lines.append(f'<p>{line}</p>')
                else:
                    result_lines.append('<br>')
        
        if in_list:
            if in_list == 'ol':
                result_lines.append('</ol>')
            else:
                result_lines.append('</ul>')
        
        formatted = '\n'.join(result_lines)
        formatted = re.sub(r'<p>(<h[1-6]>.*?</h[1-6]>)</p>', r'\1', formatted)
        
        return formatted

# Global agent instance
agent = SmartAIAgent()

# Flask Routes
@app.route('/', methods=['GET'])
def index():
    """Serve the main interface"""
    return HTML_TEMPLATE

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    return jsonify({
        "service": "Smart AI Agent with Memory, Prompt Breaking, and Chaining",
        "status": agent.status,
        "initialized": agent.initialized,
        "timestamp": datetime.now().isoformat(),
        "tools_available": list(SmartAIAgent.tools.keys()) if SmartAIAgent.tools else [],
        "memory_conversations": len(agent.memory_manager.conversations)
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
    """Main chat endpoint without memory"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing 'message' in request body",
                "example": {"message": "Show me recent sports news"}
            }), 400
        
        user_message = data['message']
        print("getting ready to process query", user_message)
        result = agent.process_query(user_message)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ERROR: Chat endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/chat/memory', methods=['POST'])
def chat_with_memory():
    """Chat endpoint with memory support"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing 'message' in request body",
                "example": {"message": "Show me recent sports news", "conversation_id": "optional"}
            }), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id', 'default')
        
        result = agent.process_query_with_memory(user_message, conversation_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ERROR: Memory chat endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/chat/chain', methods=['POST'])
def chat_with_chaining():
    """Chat endpoint with intelligent prompt chaining"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                "error": "Missing 'message' in request body",
                "example": {"message": "Research and analyze recent technology trends"}
            }), 400
        
        user_message = data['message']
        conversation_id = data.get('conversation_id', 'default')
        
        result = agent.process_query_with_chaining(user_message, conversation_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"ERROR: Chaining chat endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500
@app.route('/memory/mcp-data/<conversation_id>', methods=['GET'])
def get_mcp_data(conversation_id: str):
    """Get all MCP data from a conversation"""
    try:
        entity_types = request.args.getlist('entity_types')
        mcp_data = agent.memory_manager.get_mcp_data_from_conversation(
            conversation_id, entity_types if entity_types else None
        )
        return jsonify(mcp_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory/search-mcp/<conversation_id>', methods=['POST'])
def search_mcp_data(conversation_id: str):
    """Search MCP data in a conversation"""
    try:
        data = request.get_json()
        search_criteria = data.get('criteria', {})
        results = agent.memory_manager.search_mcp_data(conversation_id, search_criteria)
        return jsonify({
            "conversation_id": conversation_id,
            "search_criteria": search_criteria,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory/entities/<conversation_id>', methods=['GET'])
def get_extracted_entities(conversation_id: str):
    """Get all extracted entities from a conversation"""
    try:
        entity_type = request.args.get('type')
        mcp_data = agent.memory_manager.get_mcp_data_from_conversation(conversation_id)
        
        if entity_type:
            entities = mcp_data.get("aggregated_entities", {}).get(entity_type, [])
        else:
            entities = mcp_data.get("aggregated_entities", {})
        
        return jsonify({
            "conversation_id": conversation_id,
            "entity_type": entity_type,
            "entities": entities,
            "summary": mcp_data.get("summary", {})
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/memory/rebuild-entities/<conversation_id>', methods=['POST'])
def rebuild_entities(conversation_id: str):
    """Rebuild extracted entities for a conversation"""
    try:
        if conversation_id not in agent.memory_manager.conversations:
            return jsonify({"error": "Conversation not found"}), 404
        
        conversation = agent.memory_manager.conversations[conversation_id]
        rebuilt_count = 0
        
        for message in conversation.messages:
            if message.raw_mcp_data and not message.extracted_entities:
                message.extracted_entities = agent.memory_manager._extract_entities_from_mcp_data(
                    message.raw_mcp_data
                )
                rebuilt_count += 1
        
        return jsonify({
            "conversation_id": conversation_id,
            "rebuilt_count": rebuilt_count,
            "message": f"Rebuilt entities for {rebuilt_count} messages"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            if tool_name in SmartAIAgent.tools:
                tool = SmartAIAgent.tools[tool_name]
                tools_by_category[category]['tools'].append({
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": list(tool.inputSchema.get('properties', {}).keys()) if tool.inputSchema else []
                })
    
    return jsonify({
        "tools_by_category": tools_by_category,
        "total_tools": len(SmartAIAgent.tools),
        "categories": list(categorizer.tool_categories.keys()),
        "mcp_connected": agent.status["mcp"]
    })

@app.route('/tools/refresh', methods=['POST'])
def refresh_tools():
    """Refresh tools from MCP server and reinitialize tool selector"""
    try:
        SmartAIAgent.tools = agent.mcp_client.fetch_tools()
        agent.status["tools"] = len(SmartAIAgent.tools)
        
        if SmartAIAgent.tools:
            agent.tool_selector = SmartToolSelector(SmartAIAgent.tools)
        
        return jsonify({
            "success": True,
            "tools_count": len(SmartAIAgent.tools),
            "tools": list(SmartAIAgent.tools.keys())
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
    
    # Test tools endpoint        if results["mcp_health"]:
            try:
                tools_url = f"{agent.mcp_client.server_url}/tools"
                response = requests.get(tools_url, timeout=5)
                results["mcp_tools"] = response.status_code == 200
                results["tools_count"] = len(SmartAIAgent.tools)
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
    print("ENHANCED SMART AI AGENT WITH PROMPT CHAINING")
    print("="*80)
    print("FEATURES:")
    print("- ✅ Advanced Memory Management")
    print("- ✅ Intelligent Prompt Breaking")
    print("- ✅ Multi-step Prompt Chaining")
    print("- ✅ NLP Entity Extraction")
    print("- ✅ Smart Tool Selection")
    print("- ✅ Conversation Context")
    print("- ✅ Token-aware Memory")
    print("- ✅ Working Web Interface")
    print("="*80)
    print("STARTING: Initializing enhanced agent...")
    
    try:
        if agent.initialize():
            print(f"\n🎉 SUCCESS: Enhanced Agent ready!")
            print(f"🔧 Tools Available: {agent.status['tools']}")
            print(f"🧠 Memory System: ✅ Active")
            print(f"📝 Prompt Breaking: ✅ Active")
            print(f"🔗 Prompt Chaining: ✅ Active")
            print(f"🔍 NLP Extraction: ✅ Active")
            
            print("\n📡 AVAILABLE ENDPOINTS:")
            print("   POST /chat                           - Standard chat")
            print("   POST /chat/memory                    - Chat with persistent memory")
            print("   POST /chat/chain                     - Chat with intelligent chaining")
            print("   POST /analyze                        - Query analysis & tool selection")
            print("   GET  /tools                          - List available tools")
            print("   GET  /status                         - System health check")
            print("   POST /test                           - Run comprehensive tests")
            print("   GET  /memory/conversations           - List all conversations")
            print("   GET  /memory/conversation/<id>       - Get conversation history")
            print("   DELETE /memory/clear/<id>            - Clear conversation")
            print("   POST /tools/refresh                  - Refresh tools from MCP")
            print("   POST /initialize                     - Force re-initialization")
            
            print("\n💡 EXAMPLE USAGE:")
            print('   curl -X POST http://localhost:5001/chat/chain \\')
            print('        -H "Content-Type: application/json" \\')
            print('        -d \'{"message": "Research and analyze recent AI developments"}\'')
            
            print("\n🌐 WEB INTERFACE:")
            print("   Open: http://localhost:5001")
            print("   Features: Interactive UI with all endpoints including chaining")
            
            print("\n" + "="*80)
            print("🚀 SERVER STARTING...")
            print("="*80)
            
            app.run(
                host='0.0.0.0', 
                port=5001, 
                debug=False,
                threaded=True,
                use_reloader=False
            )
            
        else:
            print("\n❌ ERROR: Initialization failed!")
            agent._print_diagnostics()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
