#!/usr/bin/env node
import 'node-fetch';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ErrorCode, McpError } from '@modelcontextprotocol/sdk/types.js';
import { Database } from 'arangojs';
import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createToolDefinitions } from './tools.js';
import { ToolHandlers } from './handlers.js';
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import fetch, { Headers, Request } from 'node-fetch'; // Import fetch (default export) here
global.Headers = Headers as any;
global.Request = Request as any;
global.fetch = fetch as any; // Add this line for fetch

// Polyfill FormData from the 'form-data' package
import FormData from 'form-data';
global.FormData = FormData as any;
// Load environment variables from .env file
dotenv.config();

// Environment variables for HTTP server
const HTTP_PORT = parseInt('6001');
const HTTP_HOST = 'localhost';

// Get package version from package.json
const __dirname = dirname(fileURLToPath(import.meta.url));
const packageJson = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'));
const MAX_RECONNECTION_ATTEMPTS = 3;
const RECONNECTION_DELAY = 1000; // 1 second

// Get connection details from environment variables
const ARANGO_URL = 'http://localhost:8529'; // Default ArangoDB URL
const ARANGO_DB = 'newsDB2022';
const ARANGO_USERNAME = 'root';
const ARANGO_PASSWORD = 'i-0172f1f969c7548c4';
const TOOLS = createToolDefinitions();

// Direct configuration validation
if (!ARANGO_USERNAME || !ARANGO_PASSWORD) {
    throw new Error('Database credentials are required');
}


class ArangoServer {
    private server: Server;
    private db!: Database;
    private isConnected: boolean = false;
    private reconnectionAttempts: number = 0;
    private toolHandlers: ToolHandlers;
    private app: express.Application;

    constructor() {
        this.initializeDatabase();

        // Initialize Express app
        this.app = express();
        this.app.use(cors());
        this.app.use(express.json());

        // Initialize MCP server
// Initialize MCP server
        
// Initialize MCP server
        this.server = new Server(
            { // This is the _serverInfo argument
                name: 'arango-server',
                version: packageJson.version,
                capabilities: { // This is the _serverInfo.capabilities
                    tools: TOOLS // This is correct for _serverInfo (your tool definitions)
                }
            },
            { // This is the options argument (ServerOptions)
                capabilities: { // This is the required ServerOptions.capabilities
                    tools: { // This object corresponds to z.ZodObject<{ listChanged: z.ZodOptional<z.ZodBoolean>; }
                        listChanged: true // Explicitly setting listChanged to false (or true, if needed)
                    }
                }
            }
        );

        // Initialize tool handlers
        this.toolHandlers = new ToolHandlers(this.db, TOOLS, this.ensureConnection.bind(this));

        // Set up HTTP endpoints
        this.setupHttpEndpoints();
    }

    private async initializeDatabase(): Promise<void> {
        try {
            this.db = new Database({
                url: ARANGO_URL,
                databaseName: ARANGO_DB,
                auth: { username: ARANGO_USERNAME!, password: ARANGO_PASSWORD! },
            });

            await this.checkConnection();
            this.isConnected = true;
            this.reconnectionAttempts = 0;
        } catch (error) {
            console.error('Database connection error:', error);
            this.isConnected = false;
            throw error;
        }
    }

    private async checkConnection(): Promise<void> {
        try {
            await this.db.version();
        } catch (error) {
            this.isConnected = false;
            throw error;
        }
    }
    
    
    private async checkCollections(): Promise<void> {
      try {
        console.log('=== COLLECTIONS ===');
        const collections = await this.db.collections();
        collections.forEach(col => console.log('Collection:', col.name));

        console.log('\n=== VIEWS ===');
        const views = await this.db.views();
        views.forEach(view => console.log('View:', view.name));

        console.log('\n=== GRAPHS ===');
        const graphs = await this.db.graphs();
        graphs.forEach(graph => console.log('Graph:', graph.name));
      } catch (error) {
        throw error;
      }
    }
    private async handleConnectionError(): Promise<void> {
        if (this.reconnectionAttempts >= MAX_RECONNECTION_ATTEMPTS) {
            throw new Error(`Failed to connect after ${MAX_RECONNECTION_ATTEMPTS} attempts`);
        }

        this.reconnectionAttempts++;
        console.error(`Attempting to reconnect (${this.reconnectionAttempts}/${MAX_RECONNECTION_ATTEMPTS})...`);

        await new Promise((resolve) => setTimeout(resolve, RECONNECTION_DELAY));
        await this.initializeDatabase();
    }    private async ensureConnection(): Promise<void> {
        if (!this.isConnected) {
            await this.handleConnectionError();
        }
    }

    private async processMessageQueue(connection: { res: express.Response, messageQueue: any[], processing: boolean }): Promise<void> {
        if (connection.processing || connection.messageQueue.length === 0) return;
        connection.processing = true;        while (connection.messageQueue.length > 0) {
            const message = connection.messageQueue.shift();
            try {
                // Extract name and arguments from the JSON-RPC message structure
                const toolCallParams = {
                    name: message.params?.name,
                    arguments: message.params?.arguments
                };
                const result = await this.toolHandlers.handleCallTool(toolCallParams);
                const response = {
                    jsonrpc: '2.0',
                    id: message.id,
                    result
                };
                if (!connection.res.writableEnded) {
                    connection.res.write(`data: ${JSON.stringify(response)}\n\n`);
                }
            } catch (error) {
                const errorResponse = {
                    jsonrpc: '2.0',
                    id: message.id,
                    error: {
                        code: -32000,
                        message: error instanceof Error ? error.message : 'Unknown error'
                    }
                };
                if (!connection.res.writableEnded) {
                    connection.res.write(`data: ${JSON.stringify(errorResponse)}\n\n`);
                }
            }
        }

        connection.processing = false;
    }private setupHttpEndpoints(): void {
        // Health check endpoint
        this.app.get('/health', (req: express.Request, res: express.Response) => {
            res.json({ status: 'ok', version: packageJson.version });
        });

        // Store SSE connections and message queues
        const sseConnections = new Map<string, { res: express.Response, messageQueue: any[], processing: boolean }>();

        // SSE endpoint for MCP protocol
        this.app.get('/sse', (req: express.Request, res: express.Response) => {
            // Set headers for SSE
            res.setHeader('Content-Type', 'text/event-stream');
            res.setHeader('Cache-Control', 'no-cache');
            res.setHeader('Connection', 'keep-alive');
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Headers', 'Cache-Control');
            res.flushHeaders();

            // Generate unique connection ID
            const connectionId = Math.random().toString(36).substring(7);

            // Send initial connection message
            const connectionResponse = {
                jsonrpc: '2.0',
                result: {
                    connectionId,
                    name: 'arango-server',
                    version: packageJson.version,
                    capabilities: {
                        tools: TOOLS
                    }
                }
            };
            res.write(`data: ${JSON.stringify(connectionResponse)}\n\n`);

            // Store connection
            sseConnections.set(connectionId, {
                res,
                messageQueue: [],
                processing: false
            });

            // Send a heartbeat every 30 seconds to keep the connection alive
            const heartbeat = setInterval(() => {
                if (!res.writableEnded) {
                    res.write('event: heartbeat\ndata: {}\n\n');
                } else {
                    clearInterval(heartbeat);
                    sseConnections.delete(connectionId);
                }
            }, 30000);

            // Handle client disconnect
            req.on('close', () => {
                clearInterval(heartbeat);
                sseConnections.delete(connectionId);
                res.end();
            });

            req.on('error', () => {
                clearInterval(heartbeat);
                sseConnections.delete(connectionId);
                res.end();
            });
        });        // Handle MCP protocol messages through POST
        this.app.post('/sse/message', express.json(), async (req, res) => {
            try {
                const message = req.body;
                const connectionId = req.headers['x-connection-id'] as string;
                
                if (!connectionId || !sseConnections.has(connectionId)) {
                    res.status(400).json({
                        jsonrpc: '2.0',
                        id: message.id,
                        error: {
                            code: -32000,
                            message: 'Invalid or missing connection ID'
                        }
                    });
                    return;
                }

                const connection = sseConnections.get(connectionId)!;

                switch (message.method) {
                    case 'tools/list':
                        const tools = await this.toolHandlers.handleListTools();
                        const listResponse = {
                            jsonrpc: '2.0',
                            id: message.id,
                            result: { tools }
                        };
                        if (!connection.res.writableEnded) {
                            connection.res.write(`data: ${JSON.stringify(listResponse)}\n\n`);
                        }
                        res.json({ status: 'sent' });
                        break;

                    case 'tools/call':
                        // Add to message queue for processing
                        connection.messageQueue.push(message);
                        this.processMessageQueue(connection);
                        res.json({ status: 'queued' });
                        break;

                    default:
                        const errorResponse = {
                            jsonrpc: '2.0',
                            id: message.id,
                            error: {
                                code: -32601,
                                message: 'Method not found'
                            }
                        };
                        if (!connection.res.writableEnded) {
                            connection.res.write(`data: ${JSON.stringify(errorResponse)}\n\n`);
                        }
                        res.json({ status: 'error', message: 'Method not found' });
                }
            } catch (error) {
                console.error('SSE message handling error:', error);
                const errorResponse = {
                    jsonrpc: '2.0',
                    id: null,
                    error: {
                        code: -32700,
                        message: 'Parse error'
                    }
                };
                res.status(400).json(errorResponse);
            }
        });

        // List tools endpoint (REST API - keeping for backward compatibility)
        this.app.get('/tools', async (req, res) => {
            try {
                const tools = await this.toolHandlers.handleListTools();
                res.json({ tools });
            } catch (error) {
                res.status(500).json({ error: String(error) });
            }
        });

        // Call tool endpoint (REST API - keeping for backward compatibility)
        this.app.post('/tools/call', async (req, res) => {
            try {
                const result = await this.toolHandlers.handleCallTool(req.body);
                res.json(result);
            } catch (error) {
                if (error instanceof McpError) {
                    res.status(400).json({ error: error.message, code: error.code });
                } else {
                    res.status(500).json({ error: String(error), code: ErrorCode.InternalError });
                }
            }
        });
    }

    public async start() {
        // Start HTTP server
        this.app.listen(HTTP_PORT, HTTP_HOST, () => {
            console.log(`HTTP server listening at http://${HTTP_HOST}:${HTTP_PORT}`);
        });
    }
}

// Start server
const server = new ArangoServer();
server.start().catch(error => {
    console.error('[MCP] Fatal error:', error);
    process.exit(1);
});
