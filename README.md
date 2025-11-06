# Multi-Agent Learning Chat API

A production-grade AI-powered educational chat system with subject-specific agents powered by Google Gemini API. Built with FastAPI for high performance, scalability, and developer-friendly integration.

## Features

- **5 Specialized Learning Agents**: Mathematics, English, Physics, Chemistry, and Civic Education
- **Real-Time Streaming Responses**: Server-Sent Events (SSE) for instant token-by-token responses
- **Production-Ready Architecture**: Modular, async-first design with comprehensive error handling
- **Consistent API Design**: Standardized request/response formats with detailed error messages
- **Performance Optimized**: Async operations, timeout protection, and concurrent request handling
- **Developer-Friendly**: Auto-generated OpenAPI documentation, clear examples, and type-safe models
- **Monitoring Ready**: Health check endpoint, structured logging, and performance metrics
- **Testing Interface**: Streamlit frontend with streaming support for internal API testing

## Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone the repository and install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment variables:**

Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_actual_key_here
REQUEST_TIMEOUT=15
MAX_MESSAGE_LENGTH=5000
LOG_LEVEL=INFO
CORS_ORIGINS=["*"]
```

3. **Start the FastAPI backend:**
```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

4. **(Optional) Start the Streamlit testing interface:**
```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit interface will be available at `http://localhost:8501`

## API Documentation

### Interactive Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Base URL

```
http://localhost:8000/api/v1
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents` | List all available agents |
| POST | `/api/v1/agents/{agent_id}` | Chat with a specific agent |
| POST | `/api/v1/agents/{agent_id}/stream` | Chat with streaming response (SSE) |
| GET | `/api/v1/health` | Health check endpoint |
| GET | `/` | API information |

---

## API Usage Examples

### 1. List Available Agents

Get a list of all enabled AI agents with their metadata.

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

### 2. Chat with an Agent

Send a message to a specific agent and receive an AI-generated response.

**Request:**
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
    "reply": "The Pythagorean theorem states that in a right triangle, the square of the length of the hypotenuse (c) equals the sum of squares of the other two sides (a and b): a² + b² = c²\n\nThis fundamental theorem is used extensively in geometry, trigonometry, and many real-world applications like construction, navigation, and physics.",
    "timestamp": "2025-11-06T10:30:00Z",
    "metadata": {
      "processing_time_ms": 1250
    }
  },
  "message": "Response generated successfully"
}
```

**Available Agent IDs:**
- `math` - Mathematics Agent
- `english` - English Language Agent
- `physics` - Physics Agent
- `chemistry` - Chemistry Agent
- `civic` - Civic Education Agent

---

### 3. Chat with an Agent (Streaming)

Send a message to a specific agent and receive a real-time streaming response using Server-Sent Events (SSE). This provides immediate feedback as tokens are generated, significantly improving perceived response time.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/agents/math/stream" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "What is the Pythagorean theorem?"
     }'
```

**Response (200 OK - Server-Sent Events):**
```
data: {"chunk": "The Pythagorean"}

data: {"chunk": " theorem states"}

data: {"chunk": " that in a"}

data: {"done": true, "metadata": {"processing_time_ms": 1250}}
```

**Benefits:**
- First tokens arrive in ~200-500ms (vs 3-4 seconds for full response)
- Better user experience for long responses
- Real-time feedback improves perceived performance

**JavaScript Example:**
```javascript
const response = await fetch('/api/v1/agents/math/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'What is the Pythagorean theorem?' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.chunk) {
        console.log('Chunk:', data.chunk);
      } else if (data.done) {
        console.log('Done!');
      }
    }
  }
}
```

---

### 4. Health Check

Check the service health status and availability.

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

### Error Codes and Messages

| Status Code | Error Type | Description | Example Message |
|-------------|------------|-------------|-----------------|
| **400** | Bad Request | Invalid input or validation error | `"Message exceeds maximum length of 5000 characters"` |
| **404** | Not Found | Agent ID does not exist or is disabled | `"Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"` |
| **500** | Internal Server Error | AI service unavailable or unexpected error | `"AI service temporarily unavailable. Please try again later."` |
| **504** | Gateway Timeout | Request exceeded timeout limit (15s) | `"Request timed out after 15 seconds. Please try again or simplify your question."` |

### Error Examples

#### 400 - Validation Error
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Message cannot be empty or only whitespace"
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

---

## Request/Response Models

### ChatRequest

**Fields:**
- `message` (string, required): User message to send to the agent
  - Minimum length: 1 character
  - Maximum length: 5000 characters
  - Automatically trimmed of leading/trailing whitespace

**Example:**
```json
{
  "message": "Explain Newton's laws of motion"
}
```

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
- `timestamp` (string): ISO 8601 timestamp
- `metadata` (object): Additional metadata
  - `processing_time_ms` (integer): Processing time in milliseconds

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | - | Yes |
| `REQUEST_TIMEOUT` | Request timeout in seconds | 15 | No |
| `MAX_MESSAGE_LENGTH` | Maximum message length | 5000 | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO | No |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | ["*"] | No |

### Example `.env` File

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (with defaults)
REQUEST_TIMEOUT=15
MAX_MESSAGE_LENGTH=5000
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8501"]
```

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────┐
│     Client Applications / Frontend      │
└──────────────────┬──────────────────────┘
                   │ HTTP/JSON
                   ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  ┌──────────┐  ┌──────────┐            │
│  │ Routers  │  │Exception │            │
│  │ (v1 API) │  │ Handlers │            │
│  └────┬─────┘  └────┬─────┘            │
└───────┼─────────────┼──────────────────┘
        │             │
        ▼             ▼
┌─────────────────────────────────────────┐
│         Service Layer                   │
│  ┌──────────────┐  ┌──────────────┐   │
│  │  AI Service  │  │Agent Manager │   │
│  │   (Async)    │  │              │   │
│  └──────┬───────┘  └──────────────┘   │
└─────────┼──────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│       Google Gemini API                 │
└─────────────────────────────────────────┘
```

### Key Features

- **Async-First Design**: All operations are non-blocking for optimal performance
- **Modular Architecture**: Clear separation of concerns (API, service, configuration)
- **Type Safety**: Pydantic models for request/response validation
- **Centralized Error Handling**: Consistent error responses across all endpoints
- **Performance Monitoring**: Request logging and processing time tracking
- **Timeout Protection**: Configurable timeouts prevent resource exhaustion

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html
```

### Code Quality

```bash
# Format code
black backend/

# Lint code
flake8 backend/

# Type checking
mypy backend/
```

### Development Server

```bash
# Run with auto-reload
uvicorn backend.main:app --reload --log-level debug

# Run on custom port
uvicorn backend.main:app --reload --port 8080
```

---

## Deployment

For comprehensive deployment instructions including Docker, cloud platforms (AWS, GCP, Azure, Heroku), monitoring setup, and troubleshooting, see the **[Deployment Guide](docs/DEPLOYMENT.md)**.

### Quick Deploy with Docker

```bash
# Copy environment file
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Build and run
docker build -t multi-agent-chat-api .
docker run -p 8000:8000 --env-file .env multi-agent-chat-api
```

### Production Checklist

- [ ] Set `GEMINI_API_KEY` in environment
- [ ] Configure `CORS_ORIGINS` for your domain
- [ ] Set up health check monitoring
- [ ] Enable HTTPS
- [ ] Configure logging aggregation
- [ ] Set up alerts for errors
- [ ] Review security best practices

See the **[Deployment Guide](docs/DEPLOYMENT.md)** for detailed instructions.

---

## Monitoring and Observability

### Logging

The application uses structured logging with the following levels:

- **INFO**: Request/response logging, agent operations
- **WARNING**: Timeouts, degraded performance
- **ERROR**: Service failures, unexpected exceptions
- **DEBUG**: Detailed request/response data (development only)

### Metrics

Each response includes processing time in the metadata:

```json
{
  "metadata": {
    "processing_time_ms": 1250
  }
}
```

### Health Checks

Use the `/api/v1/health` endpoint for:
- Container orchestration health checks
- Load balancer health checks
- Monitoring system integration
- Uptime monitoring

---

## Troubleshooting

### Common Issues

**Issue: "Service not properly initialized"**
- Ensure the application started successfully
- Check logs for initialization errors
- Verify environment variables are set correctly

**Issue: "AI service temporarily unavailable"**
- Verify Gemini API key is valid
- Check internet connectivity
- Review Gemini API status and quotas

**Issue: "Request timed out"**
- Try simplifying the question
- Check if Gemini API is responding slowly
- Consider increasing `REQUEST_TIMEOUT` if needed

**Issue: CORS errors in browser**
- Add your frontend origin to `CORS_ORIGINS` environment variable
- Ensure the format is a valid JSON array: `["http://localhost:3000"]`

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## License

This project is licensed under the MIT License.

---

## Documentation

### Quick Links

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in minutes
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Error Codes Reference](docs/ERROR_CODES.md)** - Comprehensive error handling guide
- **[Interactive Swagger UI](http://localhost:8000/docs)** - Try the API in your browser
- **[ReDoc Documentation](http://localhost:8000/redoc)** - Alternative documentation view

### Documentation Structure

```
docs/
├── QUICK_START.md          # Installation and first steps
├── API_DOCUMENTATION.md    # Complete API reference
├── DEPLOYMENT.md           # Production deployment guide
└── ERROR_CODES.md          # Error handling guide
```

## Support

For issues, questions, or contributions:
- Check the [Quick Start Guide](docs/QUICK_START.md) for common setup issues
- Review the [Error Codes Reference](docs/ERROR_CODES.md) for troubleshooting
- Open an issue on GitHub
- Check the interactive API documentation at `/docs`
- Review the logs for detailed error information

---

## Changelog

### Version 1.0.0 (2025-11-06)

- Initial production release
- 5 subject-specific AI agents
- Async-first architecture
- Comprehensive error handling
- Auto-generated API documentation
- Health check endpoint
- Performance monitoring
- Streamlit testing interface
