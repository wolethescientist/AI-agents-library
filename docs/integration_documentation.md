# AI Learning System - Frontend Integration Guide

## Overview

This guide provides comprehensive documentation for integrating the AI Learning System into your Next.js/TypeScript frontend application. The system provides subject-specific AI tutors and custom document-based learning through RAG (Retrieval-Augmented Generation).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Authentication & Base URL](#authentication--base-url)
3. [Available Agents](#available-agents)
4. [API Endpoints](#api-endpoints)
5. [Integration Flow](#integration-flow)
6. [TypeScript Types](#typescript-types)
7. [Code Examples](#code-examples)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)

---

## Architecture Overview

### User Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Learning Sidebar                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. List Available Agents (GET /api/v1/agents/)             │
│     ├─ Mathematics Agent                                     │
│     ├─ English Agent                                         │
│     ├─ Physics Agent                                         │
│     ├─ Chemistry Agent                                       │
│     └─ Civic Education Agent                                 │
│                                                               │
│  2. Select Agent → Chat Interface                            │
│     ├─ POST /api/v1/agents/{agent_id}                       │
│     └─ POST /api/v1/agents/{agent_id}/stream                │
│                                                               │
│  3. Create Your Own Agent (Custom Document Upload)           │
│     ├─ POST /api/v1/documents (upload PDF/image)            │
│     ├─ POST /api/v1/documents/sessions/{id}/query           │
│     └─ DELETE /api/v1/documents/sessions/{id}               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentication & Base URL

### Base URL
```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```


### Headers
Currently, no authentication is required. For production, add:
```typescript
const headers = {
  'Content-Type': 'application/json',
  // Add authentication headers when implemented
  // 'Authorization': `Bearer ${token}`
};
```

---

## Available Agents

The system provides 5 subject-specific AI tutors:

| Agent ID | Name | Description |
|----------|------|-------------|
| `math` | Mathematics Agent | Expert in algebra, geometry, calculus, statistics, and problem-solving |
| `english` | English Agent | Expert in grammar, writing, literature, and reading comprehension |
| `physics` | Physics Agent | Expert in mechanics, energy, forces, waves, and electricity |
| `chemistry` | Chemistry Agent | Expert in reactions, elements, compounds, and molecular interactions |
| `civic` | Civic Education Agent | Expert in governance, citizenship, rights, and civic engagement |

---

## API Endpoints

### 1. List Available Agents

**Endpoint:** `GET /api/v1/agents/`

**Description:** Retrieves all available AI agents with their metadata.

**Response:**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "math",
        "name": "Mathematics Agent",
        "description": "Ask me about any math topic - algebra, geometry, calculus, and more",
        "enabled": true
      },
      {
        "id": "english",
        "name": "English Agent",
        "description": "Improve your grammar, writing, reading comprehension, and literature analysis",
        "enabled": true
      }
      // ... other agents
    ]
  },
  "message": "Found 5 available agents"
}
```


---

### 2. Chat with Agent (Non-Streaming)

**Endpoint:** `POST /api/v1/agents/{agent_id}`

**Description:** Send a message to a specific agent and receive a complete response.

**Request Body (JSON):**
```json
{
  "message": "What is the Pythagorean theorem?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent_id": "math",
    "agent_name": "Mathematics Agent",
    "mode": "general",
    "message_type": "text",
    "user_message": "What is the Pythagorean theorem?",
    "reply": "The Pythagorean theorem states that in a right triangle, the square of the hypotenuse equals the sum of squares of the other two sides: a² + b² = c²",
    "timestamp": "2025-11-17T10:30:00Z",
    "metadata": {
      "processing_time_ms": 1250
    }
  },
  "message": "Response generated successfully"
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"
  }
}
```

---

### 3. Chat with Agent (Streaming)

**Endpoint:** `POST /api/v1/agents/{agent_id}/stream`

**Description:** Send a message and receive a streaming response via Server-Sent Events (SSE).

**Request:** Same as non-streaming (multipart/form-data or JSON)

**Response Format:** Server-Sent Events (text/event-stream)

**Stream Events:**
```
data: {"chunk": "The Pythagorean"}

data: {"chunk": " theorem states"}

data: {"chunk": " that in a"}

data: {"done": true, "metadata": {"processing_time_ms": 1500}}
```


---

### 4. Upload Document (Create Custom Agent)

**Endpoint:** `POST /api/v1/documents`

**Description:** Upload a PDF or image to create a custom learning session with document context.

**Request:** multipart/form-data

**Supported File Types:**
- PDF: `application/pdf`
- Images: `image/png`, `image/jpeg`, `image/jpg`, `image/heic`

**Maximum File Size:** 30 MB

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "s_Ab3xYz1234567890",
    "expires_in_minutes": 20,
    "processing_time_ms": 3500
  },
  "message": "Document processed in memory. It will be available for 20 minutes.",
  "privacy": "Uploaded file and derived data are not saved to disk or DB and will be removed after expiry."
}
```

**Error Response (413 - File Too Large):**
```json
{
  "success": false,
  "error": {
    "code": 413,
    "message": "File too large: 35.2 MB. Maximum allowed: 30 MB. Compress the file or reduce its size before uploading."
  }
}
```

**Error Response (422 - Unsupported Type):**
```json
{
  "success": false,
  "error": {
    "code": 422,
    "message": "Unsupported file type 'application/msword'. Supported types: PDF, PNG, JPG, JPEG, HEIC. Ensure your file has the correct MIME type and extension."
  }
}
```

---

### 5. Query Document Session

**Endpoint:** `POST /api/v1/documents/sessions/{session_id}/query`

**Description:** Ask questions about an uploaded document using its session ID.

**Request Body:**
```json
{
  "message": "What are the main points discussed in this document?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "agent": "document",
    "reply": "The document discusses three main points: 1) The importance of renewable energy...",
    "source_chunks": [
      {
        "page": 2,
        "excerpt": "Renewable energy sources such as solar and wind...",
        "type": "text"
      },
      {
        "page": 5,
        "excerpt": "The transition to clean energy requires...",
        "type": "text"
      }
    ],
    "model_info": {
      "model": "gemini-2.0-flash",
      "latency_ms": 2100,
      "chunks_retrieved": 5
    },
    "timestamp": "2025-11-17T10:35:00Z"
  },
  "message": "Answer generated from uploaded document context."
}
```


**Error Response (404 - Session Not Found):**
```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "Session 's_invalid123' not found or expired. Sessions expire after 20 minutes of inactivity. Upload a new document to create a new session."
  }
}
```

---

### 6. Delete Document Session

**Endpoint:** `DELETE /api/v1/documents/sessions/{session_id}`

**Description:** Explicitly delete a document session and free its resources.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "s_Ab3xYz1234567890",
    "deleted": true
  },
  "message": "Session deleted successfully. All data has been removed from memory."
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "Session 's_invalid123' not found. It may have already been deleted or expired."
  }
}
```

---

## Integration Flow

### Flow 1: Using Pre-built Subject Agents

```
User clicks "AI Learning" in sidebar
    ↓
Frontend calls GET /api/v1/agents/
    ↓
Display list of 5 agents (math, english, physics, chemistry, civic)
    ↓
User selects "Mathematics Agent"
    ↓
Frontend opens chat interface
    ↓
User types: "What is the Pythagorean theorem?"
    ↓
Frontend calls POST /api/v1/agents/math (or /stream for real-time)
    ↓
Display agent response
```

### Flow 2: Creating Custom Document Agent

```
User clicks "Create Your Own Agent"
    ↓
Frontend shows file upload interface
    ↓
User uploads homework.pdf
    ↓
Frontend calls POST /api/v1/documents with file
    ↓
Backend returns session_id: "s_Ab3xYz..."
    ↓
Frontend stores session_id and opens chat interface
    ↓
User asks: "What's question 2 about?"
    ↓
Frontend calls POST /api/v1/documents/sessions/s_Ab3xYz.../query
    ↓
Display answer with source citations
    ↓
When done, call DELETE /api/v1/documents/sessions/s_Ab3xYz...
```


---

## TypeScript Types

### Core Types

```typescript
// API Response Types
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  privacy?: string;
  error?: {
    code: number;
    message: string;
    details?: Record<string, any>;
    suggestion?: string;
  };
}

// Agent Types
interface Agent {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface AgentListResponse {
  agents: Agent[];
}

// Chat Types
interface ChatMessage {
  agent_id: string;
  agent_name: string;
  mode: 'general' | 'document';
  message_type: 'text' | 'file_ack' | 'answer';
  user_message: string;
  reply: string;
  session_id?: string;
  source_chunks?: SourceChunk[];
  timestamp: string;
  metadata: {
    processing_time_ms: number;
    chunks_retrieved?: number;
    document_type?: 'pdf' | 'image';
  };
}

interface SourceChunk {
  page: number;
  excerpt: string;
  type: 'text' | 'image';
}

// Document Types
interface DocumentUploadResponse {
  session_id: string;
  expires_in_minutes: number;
  processing_time_ms: number;
}

interface DocumentQueryResponse {
  agent: string;
  reply: string;
  source_chunks: SourceChunk[];
  model_info: {
    model: string;
    latency_ms: number;
    chunks_retrieved: number;
  };
  timestamp: string;
}

interface SessionDeleteResponse {
  session_id: string;
  deleted: boolean;
}

// Stream Event Types
interface StreamChunk {
  chunk?: string;
  done?: boolean;
  session_id?: string;
  mode?: string;
  message_type?: string;
  metadata?: Record<string, any>;
  status?: string;
  message?: string;
  error?: string;
  code?: number;
}
```


---

## Code Examples

### Example 1: Fetching Available Agents (Mathematics)

```typescript
// services/agentService.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAgents(): Promise<Agent[]> {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/agents/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result: ApiResponse<AgentListResponse> = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to fetch agents');
    }

    return result.data?.agents || [];
  } catch (error) {
    console.error('Error fetching agents:', error);
    throw error;
  }
}

// Usage in component
'use client';

import { useEffect, useState } from 'react';
import { fetchAgents } from '@/services/agentService';

export default function AgentList() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await fetchAgents();
        setAgents(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agents');
      } finally {
        setLoading(false);
      }
    }

    loadAgents();
  }, []);

  if (loading) return <div>Loading agents...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="agent-list">
      <h2>AI Learning Agents</h2>
      {agents.map((agent) => (
        <div key={agent.id} className="agent-card">
          <h3>{agent.name}</h3>
          <p>{agent.description}</p>
          <button onClick={() => handleAgentSelect(agent.id)}>
            Start Learning
          </button>
        </div>
      ))}
    </div>
  );
}
```


---

### Example 2: Chatting with English Agent (Non-Streaming)

```typescript
// services/agentService.ts
export async function chatWithAgent(
  agentId: string,
  message: string
): Promise<ChatMessage> {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/agents/${agentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
    }

    const result: ApiResponse<ChatMessage> = await response.json();
    
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Failed to get response');
    }

    return result.data;
  } catch (error) {
    console.error('Error chatting with agent:', error);
    throw error;
  }
}

// Usage in component
'use client';

import { useState } from 'react';
import { chatWithAgent } from '@/services/agentService';

export default function EnglishAgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    setLoading(true);
    try {
      const response = await chatWithAgent('english', input);
      setMessages([...messages, response]);
      setInput('');
    } catch (error) {
      console.error('Chat error:', error);
      alert(error instanceof Error ? error.message : 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className="message">
            <div className="user-message">{msg.user_message}</div>
            <div className="agent-reply">{msg.reply}</div>
            <div className="timestamp">{new Date(msg.timestamp).toLocaleString()}</div>
          </div>
        ))}
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about grammar, writing, or literature..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
```


---

### Example 3: Streaming Chat with Physics Agent

```typescript
// services/agentService.ts
export async function chatWithAgentStream(
  agentId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onComplete: (metadata?: any) => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/agents/${agentId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          
          try {
            const parsed: StreamChunk = JSON.parse(data);
            
            if (parsed.error) {
              onError(parsed.error);
              return;
            }
            
            if (parsed.chunk) {
              onChunk(parsed.chunk);
            }
            
            if (parsed.done) {
              onComplete(parsed.metadata);
              return;
            }
          } catch (e) {
            console.warn('Failed to parse SSE data:', data);
          }
        }
      }
    }
  } catch (error) {
    console.error('Streaming error:', error);
    onError(error instanceof Error ? error.message : 'Streaming failed');
  }
}

// Usage in component
'use client';

import { useState } from 'react';
import { chatWithAgentStream } from '@/services/agentService';

export default function PhysicsAgentStreamChat() {
  const [messages, setMessages] = useState<Array<{ user: string; agent: string }>>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [currentReply, setCurrentReply] = useState('');

  const handleSend = async () => {
    if (!input.trim() || streaming) return;

    const userMessage = input;
    setInput('');
    setStreaming(true);
    setCurrentReply('');

    await chatWithAgentStream(
      'physics',
      userMessage,
      // onChunk
      (chunk) => {
        setCurrentReply((prev) => prev + chunk);
      },
      // onComplete
      (metadata) => {
        setMessages((prev) => [...prev, { user: userMessage, agent: currentReply }]);
        setCurrentReply('');
        setStreaming(false);
        console.log('Stream complete:', metadata);
      },
      // onError
      (error) => {
        alert(`Error: ${error}`);
        setStreaming(false);
        setCurrentReply('');
      }
    );
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx}>
            <div className="user-message">{msg.user}</div>
            <div className="agent-reply">{msg.agent}</div>
          </div>
        ))}
        {streaming && currentReply && (
          <div className="agent-reply streaming">{currentReply}</div>
        )}
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask about motion, forces, energy..."
          disabled={streaming}
        />
        <button onClick={handleSend} disabled={streaming}>
          {streaming ? 'Streaming...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
```


---

### Example 4: Uploading Document for Chemistry Agent

```typescript
// services/documentService.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${BASE_URL}/api/v1/documents`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
    }

    const result: ApiResponse<DocumentUploadResponse> = await response.json();
    
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Failed to upload document');
    }

    return result.data;
  } catch (error) {
    console.error('Error uploading document:', error);
    throw error;
  }
}

// Usage in component
'use client';

import { useState } from 'react';
import { uploadDocument } from '@/services/documentService';

export default function ChemistryDocumentUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      
      // Validate file size (30 MB)
      if (selectedFile.size > 30 * 1024 * 1024) {
        alert('File too large. Maximum size is 30 MB.');
        return;
      }
      
      // Validate file type
      const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
      if (!validTypes.includes(selectedFile.type)) {
        alert('Invalid file type. Please upload PDF or image (PNG, JPG).');
        return;
      }
      
      setFile(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    try {
      const result = await uploadDocument(file);
      setSessionId(result.session_id);
      alert(`Document uploaded! Session expires in ${result.expires_in_minutes} minutes.`);
      
      // Navigate to chat interface with session_id
      // router.push(`/chat/chemistry?session=${result.session_id}`);
    } catch (error) {
      console.error('Upload error:', error);
      alert(error instanceof Error ? error.message : 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>Upload Chemistry Document</h2>
      <p>Upload your chemistry homework, lab report, or study material</p>
      
      <input
        type="file"
        accept=".pdf,image/png,image/jpeg,image/jpg"
        onChange={handleFileChange}
        disabled={uploading}
      />
      
      {file && (
        <div className="file-info">
          <p>Selected: {file.name}</p>
          <p>Size: {(file.size / 1024 / 1024).toFixed(2)} MB</p>
        </div>
      )}
      
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
      
      {sessionId && (
        <div className="success-message">
          <p>✓ Document uploaded successfully!</p>
          <p>Session ID: {sessionId}</p>
        </div>
      )}
    </div>
  );
}
```


---

### Example 5: Querying Document Session for Civic Education

```typescript
// services/documentService.ts
export async function queryDocument(
  sessionId: string,
  message: string
): Promise<DocumentQueryResponse> {
  try {
    const response = await fetch(
      `${BASE_URL}/api/v1/documents/sessions/${sessionId}/query`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
    }

    const result: ApiResponse<DocumentQueryResponse> = await response.json();
    
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Failed to query document');
    }

    return result.data;
  } catch (error) {
    console.error('Error querying document:', error);
    throw error;
  }
}

// Usage in component
'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { queryDocument } from '@/services/documentService';

export default function CivicDocumentChat() {
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session');
  
  const [messages, setMessages] = useState<Array<{
    user: string;
    agent: string;
    sources?: SourceChunk[];
  }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  if (!sessionId) {
    return <div>No session ID provided. Please upload a document first.</div>;
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input;
    setInput('');
    setLoading(true);

    try {
      const response = await queryDocument(sessionId, userMessage);
      
      setMessages((prev) => [
        ...prev,
        {
          user: userMessage,
          agent: response.reply,
          sources: response.source_chunks,
        },
      ]);
    } catch (error) {
      console.error('Query error:', error);
      alert(error instanceof Error ? error.message : 'Failed to query document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-chat-container">
      <div className="session-info">
        <p>📄 Document Session Active</p>
        <p className="session-id">Session: {sessionId}</p>
        <p className="expiry-warning">⏱️ Expires after 20 minutes of inactivity</p>
      </div>

      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx} className="message-group">
            <div className="user-message">{msg.user}</div>
            <div className="agent-reply">
              <div className="reply-text">{msg.agent}</div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <h4>📚 Sources:</h4>
                  {msg.sources.map((source, sIdx) => (
                    <div key={sIdx} className="source-chunk">
                      <span className="page-number">Page {source.page}</span>
                      <p className="excerpt">{source.excerpt}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask questions about your civic education document..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>
          {loading ? 'Asking...' : 'Ask'}
        </button>
      </div>
    </div>
  );
}
```


---

### Example 6: Deleting Document Session

```typescript
// services/documentService.ts
export async function deleteSession(sessionId: string): Promise<SessionDeleteResponse> {
  try {
    const response = await fetch(
      `${BASE_URL}/api/v1/documents/sessions/${sessionId}`,
      {
        method: 'DELETE',
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`);
    }

    const result: ApiResponse<SessionDeleteResponse> = await response.json();
    
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Failed to delete session');
    }

    return result.data;
  } catch (error) {
    console.error('Error deleting session:', error);
    throw error;
  }
}

// Usage in component
'use client';

import { deleteSession } from '@/services/documentService';

export default function DocumentSessionManager({ sessionId }: { sessionId: string }) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this session? All data will be removed.')) {
      return;
    }

    setDeleting(true);
    try {
      await deleteSession(sessionId);
      alert('Session deleted successfully!');
      // Navigate back to home or agent list
      // router.push('/ai-learning');
    } catch (error) {
      console.error('Delete error:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete session');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <button 
      onClick={handleDelete} 
      disabled={deleting}
      className="delete-session-btn"
    >
      {deleting ? 'Deleting...' : '🗑️ Delete Session'}
    </button>
  );
}
```

---

## Error Handling

### Common Error Codes

| Code | Meaning | Common Causes | Solution |
|------|---------|---------------|----------|
| 400 | Bad Request | Invalid message format, empty message | Validate input before sending |
| 404 | Not Found | Invalid agent_id or expired session_id | Check agent exists, re-upload document |
| 413 | Payload Too Large | File exceeds 30 MB | Compress file or split into smaller parts |
| 422 | Unprocessable Entity | Unsupported file type | Use PDF, PNG, JPG, or HEIC only |
| 504 | Gateway Timeout | Request took too long | Retry with simpler query or smaller file |
| 500 | Internal Server Error | Server-side issue | Retry after a moment, contact support if persists |


### Error Handling Best Practices

```typescript
// utils/errorHandler.ts
export function handleApiError(error: any): string {
  // Handle network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return 'Network error. Please check your connection and try again.';
  }

  // Handle API errors
  if (error.message) {
    return error.message;
  }

  // Fallback
  return 'An unexpected error occurred. Please try again.';
}

// Usage in service
export async function chatWithAgent(agentId: string, message: string): Promise<ChatMessage> {
  try {
    const response = await fetch(`${BASE_URL}/api/v1/agents/${agentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    const result: ApiResponse<ChatMessage> = await response.json();
    
    if (!result.success || !result.data) {
      throw new Error(result.error?.message || 'Request failed');
    }

    return result.data;
  } catch (error) {
    const errorMessage = handleApiError(error);
    console.error('Chat error:', errorMessage);
    throw new Error(errorMessage);
  }
}
```

---

## Best Practices

### 1. Session Management

```typescript
// Store session ID in state or localStorage
const [sessionId, setSessionId] = useState<string | null>(
  () => localStorage.getItem('document_session_id')
);

// Save session ID after upload
const handleUpload = async (file: File) => {
  const result = await uploadDocument(file);
  setSessionId(result.session_id);
  localStorage.setItem('document_session_id', result.session_id);
  
  // Set expiry timer (20 minutes)
  setTimeout(() => {
    localStorage.removeItem('document_session_id');
    setSessionId(null);
    alert('Your document session has expired. Please upload again.');
  }, 20 * 60 * 1000);
};

// Clean up on unmount
useEffect(() => {
  return () => {
    if (sessionId) {
      deleteSession(sessionId).catch(console.error);
    }
  };
}, [sessionId]);
```

### 2. File Validation

```typescript
function validateFile(file: File): { valid: boolean; error?: string } {
  // Check file size (30 MB)
  const MAX_SIZE = 30 * 1024 * 1024;
  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: `File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum: 30 MB`,
    };
  }

  // Check file type
  const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/heic'];
  if (!validTypes.includes(file.type)) {
    return {
      valid: false,
      error: `Invalid file type (${file.type}). Supported: PDF, PNG, JPG, HEIC`,
    };
  }

  return { valid: true };
}
```

### 3. Loading States

```typescript
// Use proper loading states for better UX
const [state, setState] = useState<'idle' | 'loading' | 'streaming' | 'error'>('idle');

// Show appropriate UI based on state
{state === 'loading' && <Spinner />}
{state === 'streaming' && <StreamingIndicator />}
{state === 'error' && <ErrorMessage />}
```

### 4. Retry Logic

```typescript
async function fetchWithRetry<T>(
  fetchFn: () => Promise<T>,
  maxRetries = 3,
  delay = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fetchFn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
    }
  }
  throw new Error('Max retries reached');
}

// Usage
const agents = await fetchWithRetry(() => fetchAgents());
```


### 5. Optimistic UI Updates

```typescript
const handleSend = async () => {
  const userMessage = input;
  setInput('');
  
  // Optimistically add user message
  const tempId = Date.now();
  setMessages(prev => [...prev, {
    id: tempId,
    user: userMessage,
    agent: '',
    loading: true
  }]);

  try {
    const response = await chatWithAgent('math', userMessage);
    
    // Update with actual response
    setMessages(prev => prev.map(msg => 
      msg.id === tempId 
        ? { ...msg, agent: response.reply, loading: false }
        : msg
    ));
  } catch (error) {
    // Remove failed message or show error
    setMessages(prev => prev.filter(msg => msg.id !== tempId));
    alert('Failed to send message');
  }
};
```

### 6. Accessibility

```typescript
// Add proper ARIA labels and keyboard navigation
<button
  onClick={handleSend}
  disabled={loading}
  aria-label="Send message to agent"
  aria-busy={loading}
>
  Send
</button>

<div role="log" aria-live="polite" aria-atomic="false">
  {messages.map((msg, idx) => (
    <div key={idx} role="article">
      <div role="heading" aria-level={3}>User</div>
      <p>{msg.user}</p>
      <div role="heading" aria-level={3}>Agent</div>
      <p>{msg.agent}</p>
    </div>
  ))}
</div>
```

---

## Complete Integration Example

### Full-Featured AI Learning Component

```typescript
// components/AILearning.tsx
'use client';

import { useState, useEffect } from 'react';
import { fetchAgents, chatWithAgent, chatWithAgentStream } from '@/services/agentService';
import { uploadDocument, queryDocument, deleteSession } from '@/services/documentService';

type Mode = 'agent-list' | 'agent-chat' | 'document-upload' | 'document-chat';

export default function AILearning() {
  const [mode, setMode] = useState<Mode>('agent-list');
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Load agents on mount
  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await fetchAgents();
      setAgents(data);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const handleAgentSelect = (agentId: string) => {
    setSelectedAgent(agentId);
    setMode('agent-chat');
  };

  const handleCreateCustomAgent = () => {
    setMode('document-upload');
  };

  const handleDocumentUploaded = (newSessionId: string) => {
    setSessionId(newSessionId);
    setMode('document-chat');
  };

  const handleBack = () => {
    setMode('agent-list');
    setSelectedAgent(null);
    if (sessionId) {
      deleteSession(sessionId).catch(console.error);
      setSessionId(null);
    }
  };

  return (
    <div className="ai-learning-container">
      <header>
        <h1>🎓 AI Learning</h1>
        {mode !== 'agent-list' && (
          <button onClick={handleBack}>← Back to Agents</button>
        )}
      </header>

      {mode === 'agent-list' && (
        <AgentListView 
          agents={agents} 
          onSelectAgent={handleAgentSelect}
          onCreateCustom={handleCreateCustomAgent}
        />
      )}

      {mode === 'agent-chat' && selectedAgent && (
        <AgentChatView agentId={selectedAgent} />
      )}

      {mode === 'document-upload' && (
        <DocumentUploadView onUploaded={handleDocumentUploaded} />
      )}

      {mode === 'document-chat' && sessionId && (
        <DocumentChatView sessionId={sessionId} />
      )}
    </div>
  );
}

// Sub-components would be implemented similarly to examples above
```

---

## Testing

### Unit Test Example (Jest + React Testing Library)

```typescript
// __tests__/agentService.test.ts
import { fetchAgents, chatWithAgent } from '@/services/agentService';

global.fetch = jest.fn();

describe('Agent Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch agents successfully', async () => {
    const mockResponse = {
      success: true,
      data: {
        agents: [
          { id: 'math', name: 'Mathematics Agent', description: 'Math expert', enabled: true },
        ],
      },
    };

    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const agents = await fetchAgents();
    
    expect(agents).toHaveLength(1);
    expect(agents[0].id).toBe('math');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/agents/'),
      expect.any(Object)
    );
  });

  it('should handle chat errors', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({
        success: false,
        error: { code: 404, message: 'Agent not found' },
      }),
    });

    await expect(chatWithAgent('invalid', 'test')).rejects.toThrow('Agent not found');
  });
});
```

---

## Performance Optimization

### 1. Debounce Input

```typescript
import { useDebounce } from '@/hooks/useDebounce';

const [input, setInput] = useState('');
const debouncedInput = useDebounce(input, 300);

// Only trigger search/validation after user stops typing
useEffect(() => {
  if (debouncedInput) {
    validateInput(debouncedInput);
  }
}, [debouncedInput]);
```

### 2. Lazy Load Components

```typescript
import dynamic from 'next/dynamic';

const DocumentChatView = dynamic(() => import('@/components/DocumentChatView'), {
  loading: () => <p>Loading chat...</p>,
  ssr: false,
});
```

### 3. Cache Agent List

```typescript
// Use SWR or React Query for caching
import useSWR from 'swr';

function useAgents() {
  const { data, error, isLoading } = useSWR('/api/v1/agents/', fetchAgents, {
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
    dedupingInterval: 60000, // Cache for 1 minute
  });

  return {
    agents: data || [],
    isLoading,
    error,
  };
}
```

---

## Security Considerations

1. **Input Validation**: Always validate user input on the frontend before sending to API
2. **File Size Limits**: Enforce 30 MB limit before upload to save bandwidth
3. **File Type Validation**: Check MIME types before upload
4. **Session Management**: Clear session IDs from localStorage on logout
5. **Error Messages**: Don't expose sensitive information in error messages
6. **HTTPS**: Always use HTTPS in production
7. **Rate Limiting**: Implement client-side rate limiting to prevent abuse

```typescript
// Simple rate limiter
class RateLimiter {
  private requests: number[] = [];
  private limit: number;
  private window: number;

  constructor(limit: number, windowMs: number) {
    this.limit = limit;
    this.window = windowMs;
  }

  canMakeRequest(): boolean {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.window);
    
    if (this.requests.length < this.limit) {
      this.requests.push(now);
      return true;
    }
    
    return false;
  }
}

const chatRateLimiter = new RateLimiter(10, 60000); // 10 requests per minute
```

---

## Support & Resources

### API Documentation
- Base URL: `http://localhost:8000` (development)
- Interactive API Docs: `http://localhost:8000/docs`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Available Agents
1. **Mathematics** (`math`) - Algebra, calculus, geometry, statistics
2. **English** (`english`) - Grammar, writing, literature, comprehension
3. **Physics** (`physics`) - Mechanics, energy, forces, waves
4. **Chemistry** (`chemistry`) - Reactions, elements, compounds, bonding
5. **Civic Education** (`civic`) - Governance, citizenship, rights, civic processes

### Session Limits
- Document sessions expire after **20 minutes** of inactivity
- Maximum file size: **30 MB**
- Supported formats: PDF, PNG, JPG, JPEG, HEIC

### Contact
For issues or questions, please contact the backend team or refer to the API documentation at `/docs`.

---

**Last Updated:** November 17, 2025  
**API Version:** v1  
**Document Version:** 1.0.0
