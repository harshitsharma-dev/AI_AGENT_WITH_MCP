#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { ErrorCode, McpError } from '@modelcontextprotocol/sdk/types.js';
import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { createToolDefinitions } from './tools.js';
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Environment variables for HTTP server
const HTTP_PORT = parseInt(process.env.HTTP_PORT || '3000');
const HTTP_HOST = process.env.HTTP_HOST || 'localhost';

// Get package version from package.json
const __dirname = dirname(fileURLToPath(import.meta.url));
const packageJson = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'));
const TOOLS = createToolDefinitions();

class TestMCPServer {
    private app: express.Application;

    constructor() {
        // Initialize Express app
        this.app = express();
        this.app.use(cors());
        this.app.use(express.json());

        // Set up HTTP endpoints
        this.setupHttpEndpoints();
    }

    private async mockHandleListTools() {
        console.log('[MCP] handleListTools called');
        return {
            tools: TOOLS
        };
    }

    private async mockHandleCallTool(request: any) {
        // Mock implementation for testing
        return {
            content: [{ 
                type: 'text', 
                text: JSON.stringify({
                    message: 'Mock response - Database not connected',
                    tool: request.name,
                    arguments: request.arguments
                }, null, 2) 
            }]
        };
    }

    private async processMessageQueue(connection: { res: express.Response, messageQueue: any[], processing: boolean }): Promise<void> {
        if (connection.processing || connection.messageQueue.length === 0) return;
        connection.processing = true;

        while (connection.messageQueue.length > 0) {
            const message = connection.messageQueue.shift();
            try {
                const result = await this.mockHandleCallTool(message.params);
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
    }

    private setupHttpEndpoints(): void {
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
                    name: 'arango-server-test',
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
                        const tools = await this.mockHandleListTools();
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
                const tools = await this.mockHandleListTools();
                res.json({ tools });
            } catch (error) {
                res.status(500).json({ error: String(error) });
            }
        });

        // Call tool endpoint (REST API - keeping for backward compatibility)
        this.app.post('/tools/call', async (req, res) => {
            try {
                const result = await this.mockHandleCallTool(req.body);
                res.json(result);
            } catch (error) {
                res.status(500).json({ error: String(error), code: ErrorCode.InternalError });
            }
        });
    }

    public async start() {
        // Start HTTP server
        this.app.listen(HTTP_PORT, HTTP_HOST, () => {
            console.log(`🚀 Test MCP Server listening at http://${HTTP_HOST}:${HTTP_PORT}`);
            console.log(`📋 Available endpoints:`);
            console.log(`   GET  /health        - Health check`);
            console.log(`   GET  /tools         - List tools (REST)`);
            console.log(`   POST /tools/call    - Call tool (REST)`);
            console.log(`   GET  /sse           - SSE connection for MCP`);
            console.log(`   POST /sse/message   - Send MCP messages`);
            console.log(`🌐 Open test-sse.html in your browser to test SSE functionality`);
        });
    }
}

// Start server
const server = new TestMCPServer();
server.start().catch(error => {
    console.error('[MCP] Fatal error:', error);
    process.exit(1);
});
