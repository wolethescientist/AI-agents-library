# AI Learning System Integration Prompt

## Context

I need to integrate an AI Learning System into my Next.js/TypeScript application. This system provides 5 subject-specific AI tutors (Math, English, Physics, Chemistry, Civic Education) and allows users to upload documents (PDFs/images) to create custom learning sessions with RAG (Retrieval-Augmented Generation).

## Project Setup

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS (or your preferred CSS framework)
- **State Management**: React hooks (useState, useEffect)
- **API Base URL**: `http://localhost:8000` (development)

## Requirements

### 1. Create API Service Layer

Create the following service files in `src/services/` or `lib/services/`:

#### `agentService.ts`
- `fetchAgents()` - GET /api/v1/agents/ - Returns list of 5 available agents
- `chatWithAgent(agentId, message)` - POST /api/v1/agents/{agentId} - Non-streaming chat
- `chatWithAgentStream(agentId, message, callbacks)` - POST /api/v1/agents/{agentId}/stream - Streaming chat with SSE

#### `documentService.ts`
- `uploadDocument(file)` - POST /api/v1/documents - Upload PDF/image, returns session_id
- `queryDocument(sessionId, message)` - POST /api/v1/documents/sessions/{sessionId}/query - Query uploaded document
- `deleteSession(sessionId)` - DELETE /api/v1/documents/sessions/{sessionId} - Clean up session

### 2. TypeScript Types

Create `src/types/api.ts` with these interfaces:

```typescript
interface Agent {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

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
  };
}

interface SourceChunk {
  page: number;
  excerpt: string;
  type: 'text' | 'image';
}

interface DocumentUploadResponse {
  session_id: string;
  expires_in_minutes: number;
  processing_time_ms: number;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  privacy?: string;
  error?: {
    code: number;
    message: string;
  };
}
```


### 3. UI Components to Create

#### Main Component: `AILearning.tsx`
Location: `src/components/AILearning.tsx` or `src/app/ai-learning/page.tsx`

**Features:**
- Sidebar with "AI Learning" button
- Shows list of 5 agents when clicked
- "Create Your Own Agent" button for document upload
- Navigation between agent list, chat, and document upload views

#### Sub-Components:

**`AgentList.tsx`**
- Display all 5 agents in a grid/list
- Show agent name, description, and icon
- Click handler to select agent and open chat
- "Create Your Own Agent" button at the bottom

**`AgentChat.tsx`**
- Props: `agentId: string`
- Chat interface with message history
- Input field and send button
- Support for both streaming and non-streaming responses
- Display agent name and description at top
- Show loading states

**`DocumentUpload.tsx`**
- File input for PDF/image upload
- File validation (max 30MB, types: PDF, PNG, JPG, HEIC)
- Upload progress indicator
- Display session_id after successful upload
- Automatic navigation to DocumentChat after upload

**`DocumentChat.tsx`**
- Props: `sessionId: string`
- Similar to AgentChat but shows document context
- Display source citations with page numbers
- Show session expiry warning (20 minutes)
- Delete session button
- Handle session expiration gracefully

### 4. User Flow Implementation

```
Step 1: User clicks "AI Learning" in sidebar
  ↓
Step 2: Show AgentList component with 5 agents:
  - Mathematics Agent
  - English Agent  
  - Physics Agent
  - Chemistry Agent
  - Civic Education Agent
  ↓
Step 3a: User clicks an agent → Open AgentChat
  - Call POST /api/v1/agents/{agent_id} or /stream
  - Display responses
  ↓
Step 3b: User clicks "Create Your Own Agent"
  ↓
Step 4: Show DocumentUpload component
  - User selects PDF or image file
  - Validate file (size, type)
  - Call POST /api/v1/documents
  - Receive session_id
  ↓
Step 5: Navigate to DocumentChat with session_id
  - User asks questions about document
  - Call POST /api/v1/documents/sessions/{session_id}/query
  - Display answers with source citations
  ↓
Step 6: When done, call DELETE /api/v1/documents/sessions/{session_id}
```


### 5. API Endpoints Reference

**Base URL**: `http://localhost:8000`

#### List Agents
```
GET /api/v1/agents/
Response: { success: true, data: { agents: [...] } }
```

#### Chat with Agent (Non-Streaming)
```
POST /api/v1/agents/{agent_id}
Body: { "message": "your question" }
Response: { success: true, data: { agent_id, reply, ... } }
```

#### Chat with Agent (Streaming)
```
POST /api/v1/agents/{agent_id}/stream
Body: { "message": "your question" }
Response: Server-Sent Events (SSE)
  data: {"chunk": "text"}
  data: {"done": true}
```

#### Upload Document
```
POST /api/v1/documents
Body: FormData with 'file' field
Response: { success: true, data: { session_id, expires_in_minutes } }
```

#### Query Document
```
POST /api/v1/documents/sessions/{session_id}/query
Body: { "message": "question about document" }
Response: { success: true, data: { reply, source_chunks, ... } }
```

#### Delete Session
```
DELETE /api/v1/documents/sessions/{session_id}
Response: { success: true, data: { deleted: true } }
```

### 6. Implementation Details

#### Error Handling
- All API calls should have try-catch blocks
- Display user-friendly error messages
- Handle common errors: 404 (not found), 413 (file too large), 422 (invalid type), 504 (timeout)
- Show error toasts or alerts

#### File Validation
```typescript
// Validate before upload
- Max size: 30 MB (30 * 1024 * 1024 bytes)
- Allowed types: ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/heic']
- Show clear error messages if validation fails
```

#### Session Management
```typescript
// Store session_id in state or localStorage
// Set 20-minute expiry timer
// Clean up session on component unmount
// Handle expired sessions gracefully
```

#### Streaming Implementation
```typescript
// Use EventSource or fetch with ReadableStream
// Parse SSE format: "data: {json}\n\n"
// Handle chunks, completion, and errors
// Update UI in real-time as chunks arrive
```

#### Loading States
- Show spinners during API calls
- Disable buttons while loading
- Show "Typing..." indicator for streaming
- Display upload progress for files


### 7. Styling Guidelines

#### Agent Cards
- Display in a responsive grid (2-3 columns on desktop, 1 on mobile)
- Include agent icon/emoji (📐 Math, 📚 English, ⚛️ Physics, 🧪 Chemistry, 🏛️ Civic)
- Show name and description
- Hover effects and click animations
- Clear visual hierarchy

#### Chat Interface
- Message bubbles (user on right, agent on left)
- Different colors for user vs agent messages
- Timestamps for each message
- Auto-scroll to latest message
- Input field at bottom with send button
- Responsive design

#### Document Upload
- Drag-and-drop zone or file input button
- Show selected file name and size
- Progress bar during upload
- Success/error states with icons
- Clear instructions

#### Source Citations
- Display in collapsible sections or cards
- Show page numbers prominently
- Excerpt text in quotes or highlighted
- Link to specific pages if possible

### 8. Accessibility Requirements

- Proper ARIA labels on all interactive elements
- Keyboard navigation support (Tab, Enter, Escape)
- Focus indicators on buttons and inputs
- Screen reader friendly messages
- Alt text for images and icons
- Semantic HTML (header, main, nav, article)

### 9. Performance Optimizations

- Lazy load chat components
- Debounce input validation (300ms)
- Cache agent list (don't refetch on every render)
- Optimize re-renders with React.memo where appropriate
- Use pagination for long chat histories
- Compress images before upload if possible

### 10. Environment Configuration

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Update for production:
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```


## Example Code Structure

### Service Layer Example

```typescript
// src/services/agentService.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAgents(): Promise<Agent[]> {
  const response = await fetch(`${BASE_URL}/api/v1/agents/`);
  if (!response.ok) throw new Error('Failed to fetch agents');
  const result = await response.json();
  return result.data.agents;
}

export async function chatWithAgent(agentId: string, message: string): Promise<ChatMessage> {
  const response = await fetch(`${BASE_URL}/api/v1/agents/${agentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error?.message || 'Chat failed');
  }
  const result = await response.json();
  return result.data;
}

export async function chatWithAgentStream(
  agentId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: string) => void
): Promise<void> {
  const response = await fetch(`${BASE_URL}/api/v1/agents/${agentId}/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
  
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader!.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.chunk) onChunk(data.chunk);
        if (data.done) onComplete();
        if (data.error) onError(data.error);
      }
    }
  }
}
```

### Component Example

```typescript
// src/components/AgentList.tsx
'use client';

import { useEffect, useState } from 'react';
import { fetchAgents } from '@/services/agentService';

export default function AgentList({ onSelectAgent, onCreateCustom }) {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents()
      .then(setAgents)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading agents...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
      {agents.map((agent) => (
        <div
          key={agent.id}
          onClick={() => onSelectAgent(agent.id)}
          className="p-6 border rounded-lg hover:shadow-lg cursor-pointer transition"
        >
          <h3 className="text-xl font-bold mb-2">{agent.name}</h3>
          <p className="text-gray-600">{agent.description}</p>
        </div>
      ))}
      
      <div
        onClick={onCreateCustom}
        className="p-6 border-2 border-dashed rounded-lg hover:border-blue-500 cursor-pointer transition"
      >
        <h3 className="text-xl font-bold mb-2">📄 Create Your Own Agent</h3>
        <p className="text-gray-600">Upload a document to create a custom learning session</p>
      </div>
    </div>
  );
}
```


## Specific Implementation Tasks

### Task 1: Set Up Project Structure
```
src/
├── app/
│   └── ai-learning/
│       └── page.tsx          # Main AI Learning page
├── components/
│   ├── AILearning.tsx        # Main container component
│   ├── AgentList.tsx         # List of 5 agents
│   ├── AgentChat.tsx         # Chat with selected agent
│   ├── DocumentUpload.tsx    # Upload PDF/image
│   └── DocumentChat.tsx      # Chat with document context
├── services/
│   ├── agentService.ts       # Agent API calls
│   └── documentService.ts    # Document API calls
├── types/
│   └── api.ts                # TypeScript interfaces
└── utils/
    └── errorHandler.ts       # Error handling utilities
```

### Task 2: Implement Agent List View
- Fetch agents from GET /api/v1/agents/
- Display 5 agents: math, english, physics, chemistry, civic
- Add "Create Your Own Agent" card
- Handle loading and error states
- Make cards clickable to navigate to chat

### Task 3: Implement Agent Chat (Non-Streaming)
- Create chat interface with message history
- Input field with validation (max 5000 chars)
- Send button that calls POST /api/v1/agents/{agent_id}
- Display user message and agent reply
- Show timestamps and processing time
- Handle errors gracefully

### Task 4: Implement Agent Chat (Streaming)
- Add toggle or separate mode for streaming
- Call POST /api/v1/agents/{agent_id}/stream
- Parse Server-Sent Events (SSE)
- Update UI in real-time as chunks arrive
- Show typing indicator
- Handle stream completion and errors

### Task 5: Implement Document Upload
- File input with drag-and-drop support
- Validate file type (PDF, PNG, JPG, HEIC)
- Validate file size (max 30 MB)
- Show file preview (name, size, type)
- Upload progress indicator
- Call POST /api/v1/documents
- Store session_id in state/localStorage
- Navigate to DocumentChat on success

### Task 6: Implement Document Chat
- Accept session_id as prop or from URL params
- Chat interface similar to AgentChat
- Call POST /api/v1/documents/sessions/{session_id}/query
- Display answers with source citations
- Show page numbers and excerpts
- Handle session expiration (404 errors)
- Add "Delete Session" button
- Show 20-minute expiry warning

### Task 7: Add Error Handling
- Create error handler utility
- Display user-friendly error messages
- Handle network errors
- Handle API errors (400, 404, 413, 422, 504, 500)
- Show error toasts or modals
- Provide retry options

### Task 8: Add Loading States
- Skeleton loaders for agent list
- Spinner for API calls
- Progress bar for file uploads
- Typing indicator for streaming
- Disable buttons during operations
- Show processing time in metadata

### Task 9: Implement Session Management
- Store session_id in localStorage
- Set 20-minute expiry timer
- Clear session on component unmount
- Handle expired sessions gracefully
- Provide option to delete session manually
- Show remaining time indicator

### Task 10: Polish UI/UX
- Responsive design (mobile, tablet, desktop)
- Smooth transitions and animations
- Proper spacing and typography
- Consistent color scheme
- Icons for agents and actions
- Empty states for no messages
- Success/error feedback


## Testing Checklist

### Functional Testing
- [ ] Agent list loads and displays all 5 agents
- [ ] Clicking an agent opens chat interface
- [ ] Sending a message to agent returns response
- [ ] Streaming chat displays chunks in real-time
- [ ] File upload validates size and type
- [ ] Document upload returns session_id
- [ ] Document chat answers questions with sources
- [ ] Session deletion works correctly
- [ ] Error messages display for invalid inputs
- [ ] Session expiry is handled gracefully

### UI/UX Testing
- [ ] Responsive on mobile, tablet, desktop
- [ ] Loading states show during operations
- [ ] Buttons disable during API calls
- [ ] Error messages are user-friendly
- [ ] Success feedback is clear
- [ ] Navigation between views works smoothly
- [ ] Chat auto-scrolls to latest message
- [ ] File upload shows progress
- [ ] Source citations are readable
- [ ] Timestamps display correctly

### Edge Cases
- [ ] Empty message submission is prevented
- [ ] File over 30 MB is rejected
- [ ] Invalid file type is rejected
- [ ] Expired session shows appropriate error
- [ ] Network errors are handled
- [ ] API timeout is handled
- [ ] Invalid agent_id shows error
- [ ] Rapid button clicks don't cause issues
- [ ] Browser back button works correctly
- [ ] Page refresh maintains state (if using localStorage)

## Common Issues and Solutions

### Issue 1: CORS Errors
**Solution**: Backend should have CORS enabled. If not, add proxy in `next.config.js`:
```javascript
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};
```

### Issue 2: Streaming Not Working
**Solution**: Ensure proper SSE parsing. Use `ReadableStream` with `TextDecoder`. Check that response headers include `Content-Type: text/event-stream`.

### Issue 3: File Upload Fails
**Solution**: 
- Don't set `Content-Type` header manually (browser sets it with boundary)
- Use `FormData` correctly
- Check file size before upload
- Verify MIME type matches backend expectations

### Issue 4: Session Expires Too Quickly
**Solution**: Sessions expire after 20 minutes of inactivity. Implement:
- Visual countdown timer
- Warning before expiry
- Auto-refresh on user activity
- Clear error message on expiry

### Issue 5: Large Chat History Causes Performance Issues
**Solution**:
- Implement pagination or virtualization
- Limit visible messages (e.g., last 50)
- Use `React.memo` to prevent unnecessary re-renders
- Consider using a state management library for large apps


## Agent-Specific Details

### Mathematics Agent (ID: `math`)
- **Icon**: 📐 or 🔢
- **Color Theme**: Blue
- **Example Questions**:
  - "What is the Pythagorean theorem?"
  - "Solve: 2x + 5 = 15"
  - "Explain derivatives in calculus"

### English Agent (ID: `english`)
- **Icon**: 📚 or ✍️
- **Color Theme**: Green
- **Example Questions**:
  - "What is a metaphor?"
  - "Correct this sentence: 'Me and him went to store'"
  - "Analyze the theme of Romeo and Juliet"

### Physics Agent (ID: `physics`)
- **Icon**: ⚛️ or 🔬
- **Color Theme**: Purple
- **Example Questions**:
  - "What is Newton's second law?"
  - "Explain kinetic energy"
  - "How does a lever work?"

### Chemistry Agent (ID: `chemistry`)
- **Icon**: 🧪 or ⚗️
- **Color Theme**: Orange
- **Example Questions**:
  - "What is the periodic table?"
  - "Balance this equation: H2 + O2 → H2O"
  - "Explain ionic bonding"

### Civic Education Agent (ID: `civic`)
- **Icon**: 🏛️ or ⚖️
- **Color Theme**: Red
- **Example Questions**:
  - "What is democracy?"
  - "Explain the three branches of government"
  - "What are human rights?"

## Additional Features (Optional Enhancements)

### 1. Chat History Persistence
- Save chat history to localStorage
- Load previous conversations on return
- Clear history button
- Export chat as PDF or text

### 2. Voice Input
- Add microphone button
- Use Web Speech API
- Convert speech to text
- Send to agent

### 3. Dark Mode
- Toggle between light and dark themes
- Persist preference in localStorage
- Adjust colors for readability

### 4. Keyboard Shortcuts
- `Ctrl/Cmd + Enter` to send message
- `Escape` to close modals
- `Ctrl/Cmd + K` to focus search/input
- Arrow keys for message navigation

### 5. Message Actions
- Copy message text
- Regenerate response
- Rate response (thumbs up/down)
- Report inappropriate content

### 6. Multi-language Support
- Detect user language
- Translate UI elements
- Support RTL languages
- Language selector

### 7. Offline Support
- Cache agent list
- Queue messages when offline
- Sync when connection restored
- Show offline indicator

### 8. Analytics
- Track agent usage
- Monitor response times
- Log errors
- User engagement metrics


## Code Quality Standards

### TypeScript
- Use strict mode
- Define all types explicitly
- Avoid `any` type
- Use interfaces for objects
- Use enums for constants

### React Best Practices
- Use functional components
- Implement proper error boundaries
- Use custom hooks for reusable logic
- Memoize expensive computations
- Clean up effects properly

### Code Organization
- One component per file
- Group related files in folders
- Use barrel exports (index.ts)
- Separate business logic from UI
- Keep components small and focused

### Naming Conventions
- Components: PascalCase (AgentChat.tsx)
- Functions: camelCase (fetchAgents)
- Constants: UPPER_SNAKE_CASE (BASE_URL)
- Types/Interfaces: PascalCase (ChatMessage)
- CSS classes: kebab-case or Tailwind

### Comments and Documentation
- Add JSDoc comments for functions
- Explain complex logic
- Document API response formats
- Include usage examples
- Keep comments up to date

## Deployment Considerations

### Environment Variables
```bash
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Staging
NEXT_PUBLIC_API_URL=https://api-staging.yourdomain.com

# Production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Build Optimization
- Enable Next.js image optimization
- Use dynamic imports for large components
- Implement code splitting
- Minimize bundle size
- Enable compression

### Security
- Validate all user inputs
- Sanitize file uploads
- Use HTTPS in production
- Implement rate limiting
- Add CSRF protection
- Don't expose sensitive data in client

### Monitoring
- Set up error tracking (Sentry, etc.)
- Monitor API response times
- Track user interactions
- Log critical errors
- Set up alerts for failures

## Final Checklist

Before considering the implementation complete:

- [ ] All 5 agents are accessible and functional
- [ ] Chat interface works for all agents
- [ ] Streaming responses work correctly
- [ ] Document upload validates and processes files
- [ ] Document chat shows source citations
- [ ] Session management works (create, use, delete)
- [ ] Error handling covers all edge cases
- [ ] Loading states are implemented
- [ ] UI is responsive on all devices
- [ ] Accessibility requirements are met
- [ ] Code is typed with TypeScript
- [ ] Components are well-organized
- [ ] API services are properly abstracted
- [ ] Environment variables are configured
- [ ] Testing checklist items pass
- [ ] Code follows best practices
- [ ] Documentation is complete
- [ ] Performance is optimized
- [ ] Security considerations addressed

## Getting Started Command

To begin implementation, start with:

1. **Set up the project structure** (folders and files)
2. **Create TypeScript types** (src/types/api.ts)
3. **Implement API services** (agentService.ts, documentService.ts)
4. **Build AgentList component** (fetch and display agents)
5. **Build AgentChat component** (basic chat functionality)
6. **Add streaming support** (SSE parsing)
7. **Build DocumentUpload component** (file validation and upload)
8. **Build DocumentChat component** (query with citations)
9. **Add error handling and loading states**
10. **Polish UI/UX and test thoroughly**

---

**API Documentation Reference**: See `integration_documentation.md` for complete API details, request/response formats, and code examples.

**Backend Base URL**: `http://localhost:8000`

**Interactive API Docs**: `http://localhost:8000/docs`

---

## Example Prompt for AI Coding Tool

> "I need to build an AI Learning System integration in my Next.js/TypeScript app. Create a complete implementation with:
> 
> 1. Service layer for API calls (agentService.ts, documentService.ts)
> 2. TypeScript types for all API responses
> 3. AgentList component showing 5 agents (math, english, physics, chemistry, civic)
> 4. AgentChat component with streaming support
> 5. DocumentUpload component with file validation
> 6. DocumentChat component with source citations
> 7. Proper error handling and loading states
> 8. Responsive UI with Tailwind CSS
> 
> Use the API endpoints:
> - GET /api/v1/agents/ (list agents)
> - POST /api/v1/agents/{id} (chat)
> - POST /api/v1/agents/{id}/stream (streaming chat)
> - POST /api/v1/documents (upload)
> - POST /api/v1/documents/sessions/{id}/query (query document)
> - DELETE /api/v1/documents/sessions/{id} (delete session)
> 
> Base URL: http://localhost:8000
> 
> Follow the structure and requirements in this prompt document."

---

**Document Version**: 1.0.0  
**Last Updated**: November 17, 2025  
**Compatible with**: Next.js 14+, React 18+, TypeScript 5+
