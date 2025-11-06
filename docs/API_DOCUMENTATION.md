# API Documentation

## Overview

The Multi-Agent Learning Chat API provides AI-powered educational assistance through subject-specific agents. This document provides comprehensive information about the API endpoints, request/response formats, error handling, and usage examples.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. The API is protected by CORS configuration.

## Content Type

All requests and responses use `application/json`.

## API Endpoints

### 1. List Available Agents

**Endpoint:** `GET /api/v1/agents`

**Description:** Returns a list of all enabled AI agents with their metadata.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/agents"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "id": "math",
        "name": "Mathematics Agent",
        "description": "Expert in mathematics, algebra, calculus, geometry, and problem-solving"
      },
      {
        "id": "english",
        "name": "English Language Agent",
        "description": "Expert in English grammar, literature, writing, and language arts"
      },
      {
        "id": "physics",
        "name": "Physics Agent",
        "description": "Expert in physics, mechanics, thermodynamics, and natural phenomena"
      },
      {
        "id": "chemistry",
        "name": "Chemistry Agent",
        "description": "Expert in chemistry, chemical reactions, elements, and compounds"
      },
      {
        "id": "civic",
        "name": "Civic Education Agent",
        "description": "Expert in civic education, government, citizenship, and social studies"
      }
    ]
  },
  "message": "Found 5 available agents"
}
```

---

### 2. Chat with Agent

**Endpoint:** `POST /api/v1/agents/{agent_id}`

**Description:** Send a message to a specific AI agent and receive a response.

**Path Parameters:**
- `agent_id` (string, required): The unique identifier of the agent
  - Valid values: `math`, `english`, `physics`, `chemistry`, `civic`

**Request Body:**
```json
{
  "message": "What is the Pythagorean theorem?"
}
```

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/math" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What is the Pythagorean theorem?"
     }'
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "agent_id": "math",
    "agent_name": "Mathematics Agent",
    "user_message": "What is the Pythagorean theorem?",
    "reply": "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse (c) equals the sum of squares of the other two sides (a and b): a² + b² = c²",
    "timestamp": "2025-11-06T10:30:00Z",
    "metadata": {
      "processing_time_ms": 1250
    }
  },
  "message": "Response generated successfully"
}
```

---

### 3. Chat with Agent (Streaming)

**Endpoint:** `POST /api/v1/agents/{agent_id}/stream`

**Description:** Send a message to a specific AI agent and receive a streaming response using Server-Sent Events (SSE). This provides real-time token-by-token responses, significantly improving perceived response time.

**Path Parameters:**
- `agent_id` (string, required): The unique identifier of the agent
  - Valid values: `math`, `english`, `physics`, `chemistry`, `civic`

**Request Body:**
```json
{
  "message": "What is the Pythagorean theorem?"
}
```

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/math/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What is the Pythagorean theorem?"
     }'
```

**Response (200 OK - Server-Sent Events):**

The response is streamed as Server-Sent Events (SSE) with `Content-Type: text/event-stream`.

**Event Format:**
```
data: {"chunk": "The Pythagorean"}

data: {"chunk": " theorem states"}

data: {"chunk": " that in a"}

data: {"done": true, "metadata": {"processing_time_ms": 1250}}
```

**Event Types:**
- **Chunk Event**: Contains a piece of the response text
  ```json
  {"chunk": "text content"}
  ```

- **Completion Event**: Indicates streaming is complete
  ```json
  {"done": true, "metadata": {"processing_time_ms": 1250}}
  ```

- **Error Event**: Indicates an error occurred
  ```json
  {"error": "error message", "code": 504}
  ```

**Benefits:**
- Immediate feedback (first tokens arrive in ~200-500ms)
- Better user experience for long responses
- Lower perceived latency compared to non-streaming endpoint

**JavaScript Example:**
```javascript
const eventSource = new EventSource('/api/v1/agents/math/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.chunk) {
    // Append chunk to display
    console.log('Chunk:', data.chunk);
  } else if (data.done) {
    // Streaming complete
    console.log('Done! Processing time:', data.metadata.processing_time_ms);
    eventSource.close();
  } else if (data.error) {
    // Error occurred
    console.error('Error:', data.error);
    eventSource.close();
  }
};
```

---

### 4. Health Check

**Endpoint:** `GET /api/v1/health`

**Description:** Check the service health status and availability.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2025-11-06T10:30:00Z",
    "services": {
      "gemini_api": "operational"
    }
  },
  "message": "Service is operational"
}
```

---

### 5. API Information

**Endpoint:** `GET /`

**Description:** Returns basic API information and navigation links.

**Request:**
```bash
curl -X GET "http://localhost:8000/"
```

**Response (200 OK):**
```json
{
  "message": "Multi-Agent Learning Chat API",
  "version": "1.0.0",
  "api_version": "v1",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

---

## Request Models

### ChatRequest

**Fields:**
- `message` (string, required): User message to send to the agent
  - Minimum length: 1 character
  - Maximum length: 5000 characters
  - Automatically trimmed of leading/trailing whitespace

**Validation Rules:**
- Message cannot be empty or only whitespace
- Message length must be between 1 and 5000 characters

**Example:**
```json
{
  "message": "Explain Newton's laws of motion"
}
```

---

## Response Models

### SuccessResponse

**Fields:**
- `success` (boolean): Always `true` for successful responses
- `data` (object): Response data (structure varies by endpoint)
- `message` (string): Optional success message

### AgentResponse (in data field)

**Fields:**
- `agent_id` (string): Agent identifier
- `agent_name` (string): Agent display name
- `user_message` (string): Original user message
- `reply` (string): Agent's AI-generated response
- `timestamp` (string): ISO 8601 timestamp (UTC)
- `metadata` (object): Additional metadata
  - `processing_time_ms` (integer): Processing time in milliseconds

### ErrorResponse

**Fields:**
- `success` (boolean): Always `false` for errors
- `error` (object): Error details
  - `code` (integer): HTTP status code
  - `message` (string): Error message

---

## Error Handling

All errors follow a consistent response structure:

```json
{
  "success": false,
  "error": {
    "code": <HTTP_STATUS_CODE>,
    "message": "<ERROR_MESSAGE>"
  }
}
```

### HTTP Status Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid input or validation error |
| 404 | Not Found | Agent ID does not exist or is disabled |
| 500 | Internal Server Error | AI service unavailable or unexpected error |
| 504 | Gateway Timeout | Request exceeded timeout limit (15 seconds) |

### Error Examples

#### 400 - Validation Error (Empty Message)
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Message cannot be empty or only whitespace"
  }
}
```

#### 400 - Validation Error (Message Too Long)
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Message exceeds maximum length of 5000 characters"
  }
}
```

#### 404 - Agent Not Found
```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"
  }
}
```

#### 500 - Service Error
```json
{
  "success": false,
  "error": {
    "code": 500,
    "message": "AI service temporarily unavailable. Please try again later."
  }
}
```

#### 504 - Request Timeout
```json
{
  "success": false,
  "error": {
    "code": 504,
    "message": "Request timed out after 15 seconds. Please try again or simplify your question."
  }
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse and protect against API quota exhaustion.

### Rate Limit Configuration

Rate limiting can be configured via environment variables:

```env
# Enable/disable rate limiting (default: True)
RATE_LIMIT_ENABLED=True

# Maximum requests per IP per minute (default: 100)
RATE_LIMIT_PER_IP=100

# Maximum total requests per minute (default: 1000)
RATE_LIMIT_GLOBAL=1000
```

### Rate Limit Levels

#### 1. Per-IP Rate Limiting
- **Default:** 100 requests per minute per IP address
- **Purpose:** Prevent individual client abuse
- **Scope:** Applied to each unique IP address independently

#### 2. Global Rate Limiting
- **Default:** 1000 requests per minute (total)
- **Purpose:** Stay within Gemini API quotas and protect system resources
- **Scope:** Applied across all requests to the API

### Rate Limit Headers

All successful responses include rate limit information in headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699272000
```

**Header Descriptions:**
- `X-RateLimit-Limit`: Maximum requests allowed per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

### Rate Limit Exceeded (429)

When rate limits are exceeded, the API returns a 429 status code:

**Response:**
```json
{
  "success": false,
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Please slow down your requests."
  }
}
```

**Headers:**
```
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699272000
```

**Header Descriptions:**
- `Retry-After`: Seconds to wait before retrying

### Rate Limit Examples

#### Per-IP Limit Exceeded
```json
{
  "success": false,
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Please slow down your requests."
  }
}
```

#### Global Limit Exceeded
```json
{
  "success": false,
  "error": {
    "code": 429,
    "message": "Global rate limit exceeded. Please try again later."
  }
}
```

### Handling Rate Limits in Code

#### Python Example
```python
import requests
import time

def chat_with_rate_limit_handling(agent_id, message):
    response = requests.post(
        f"http://localhost:8000/api/v1/agents/{agent_id}",
        json={"message": message}
    )
    
    if response.status_code == 429:
        # Get retry-after header
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        # Retry the request
        return chat_with_rate_limit_handling(agent_id, message)
    
    return response.json()
```

#### JavaScript Example
```javascript
async function chatWithRateLimitHandling(agentId, message) {
  const response = await fetch(`http://localhost:8000/api/v1/agents/${agentId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  
  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    // Retry the request
    return chatWithRateLimitHandling(agentId, message);
  }
  
  return response.json();
}
```

### Best Practices

1. **Monitor Rate Limit Headers**: Check `X-RateLimit-Remaining` to avoid hitting limits
2. **Implement Exponential Backoff**: When rate limited, wait before retrying
3. **Respect Retry-After**: Always honor the `Retry-After` header value
4. **Cache Responses**: Cache common queries to reduce API calls
5. **Batch Requests**: Group multiple questions when possible

### Exemptions

The following endpoints are exempt from rate limiting:
- `GET /api/v1/health` - Health check endpoint

### Production Recommendations

For production deployments, consider:
- **Lower per-IP limits** (e.g., 60 requests/minute) for public APIs
- **Higher global limits** based on your Gemini API quota
- **IP whitelisting** for trusted clients
- **API keys** for authenticated rate limit tiers

---

## CORS Configuration

CORS is configured via the `CORS_ORIGINS` environment variable. By default, all origins are allowed (`["*"]`).

For production, configure specific origins:
```env
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

---

## Timeout Configuration

The default request timeout is 15 seconds. This can be configured via the `REQUEST_TIMEOUT` environment variable:

```env
REQUEST_TIMEOUT=20
```

If a request exceeds the timeout, a 504 Gateway Timeout error is returned.

---

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

### Swagger UI
- **URL:** http://localhost:8000/docs
- **Features:**
  - Interactive API testing
  - Request/response examples
  - Schema documentation
  - Try-it-out functionality

### ReDoc
- **URL:** http://localhost:8000/redoc
- **Features:**
  - Clean, readable documentation
  - Detailed schema information
  - Code samples
  - Search functionality

---

## Code Examples

### Python (requests)

```python
import requests

# List agents
response = requests.get("http://localhost:8000/api/v1/agents")
agents = response.json()
print(agents)

# Chat with agent
response = requests.post(
    "http://localhost:8000/api/v1/agents/math",
    json={"message": "What is the Pythagorean theorem?"}
)
result = response.json()
print(result["data"]["reply"])
```

### JavaScript (fetch)

```javascript
// List agents
fetch('http://localhost:8000/api/v1/agents')
  .then(response => response.json())
  .then(data => console.log(data));

// Chat with agent
fetch('http://localhost:8000/api/v1/agents/math', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'What is the Pythagorean theorem?'
  })
})
  .then(response => response.json())
  .then(data => console.log(data.data.reply));
```

### cURL

```bash
# List agents
curl -X GET "http://localhost:8000/api/v1/agents"

# Chat with agent
curl -X POST "http://localhost:8000/api/v1/agents/math" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the Pythagorean theorem?"}'

# Health check
curl -X GET "http://localhost:8000/api/v1/health"
```

---

## Best Practices

### 1. Error Handling
Always check the `success` field in responses:
```python
response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    # Handle success
    print(result["data"])
else:
    # Handle error
    print(f"Error {result['error']['code']}: {result['error']['message']}")
```

### 2. Timeout Handling
Implement client-side timeouts and retry logic:
```python
import time

def chat_with_retry(agent_id, message, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"http://localhost:8000/api/v1/agents/{agent_id}",
                json={"message": message},
                timeout=20
            )
            return response.json()
        except requests.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

### 3. Message Validation
Validate messages before sending:
```python
def validate_message(message):
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    if len(message) > 5000:
        raise ValueError("Message too long (max 5000 characters)")
    return message.strip()
```

### 4. Agent Validation
Check if agent exists before sending messages:
```python
def get_available_agents():
    response = requests.get("http://localhost:8000/api/v1/agents")
    data = response.json()
    return [agent["id"] for agent in data["data"]["agents"]]

available_agents = get_available_agents()
if agent_id not in available_agents:
    print(f"Invalid agent. Available: {', '.join(available_agents)}")
```

---

## Troubleshooting

### Common Issues

**Issue: Connection refused**
- Ensure the server is running: `uvicorn backend.main:app --reload`
- Check the correct port (default: 8000)

**Issue: CORS errors in browser**
- Add your frontend origin to `CORS_ORIGINS` environment variable
- Format: `CORS_ORIGINS=["http://localhost:3000"]`

**Issue: "AI service temporarily unavailable"**
- Verify `GEMINI_API_KEY` is set correctly in `.env`
- Check Gemini API status and quotas
- Review server logs for detailed error information

**Issue: Request timeouts**
- Try simplifying the question
- Increase `REQUEST_TIMEOUT` if needed
- Check Gemini API response times

**Issue: Validation errors**
- Ensure message is not empty
- Check message length (max 5000 characters)
- Verify JSON format is correct

---

## Support

For additional help:
- Check the interactive documentation at `/docs`
- Review server logs for detailed error information
- Open an issue on GitHub

---

## Version History

### v1.0.0 (2025-11-06)
- Initial production release
- 5 subject-specific AI agents
- Comprehensive error handling
- Auto-generated documentation
- Health check endpoint
- Performance monitoring
