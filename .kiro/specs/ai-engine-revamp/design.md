# Design Document

## Overview

This design document outlines the technical architecture for revamping the AI-powered educational chat system into a production-grade FastAPI service. The system will provide subject-specific AI agents (Mathematics, English, Physics, Chemistry, Civic Education) through a modular, asynchronous, and scalable architecture.

### Design Goals

- **Modularity**: Separate concerns into distinct layers (API, service, configuration)
- **Performance**: Fully async operations with concurrent request handling
- **Reliability**: Robust error handling, timeouts, and graceful degradation
- **Developer Experience**: Consistent API responses optimized for frontend team integration, clear documentation, easy extensibility
- **Production-Ready**: Comprehensive logging, health checks, and monitoring capabilities
- **Testing**: Streamlit interface for internal API testing and validation

### Technology Stack

- **Framework**: FastAPI (async-native Python web framework)
- **AI Service**: Google Gemini API via `google-generativeai` SDK
- **Async Runtime**: Python asyncio with thread pool executor for blocking operations
- **Validation**: Pydantic v2 for request/response models
- **Configuration**: python-dotenv for environment management
- **Logging**: Python standard logging with structured output

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│         (Team's Frontend Apps + Streamlit for Testing)      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routers    │  │  Middleware  │  │   Exception  │     │
│  │  (v1 API)    │  │  (Logging)   │  │   Handlers   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           AI Service (Async Operations)              │  │
│  │  - Request validation & sanitization                 │  │
│  │  - Prompt construction with system prompts           │  │
│  │  - Async Gemini API calls with timeout               │  │
│  │  - Response formatting & cleaning                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Agent Manager                              │  │
│  │  - Agent registry and validation                     │  │
│  │  - Agent metadata management                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Configuration Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Agent     │  │  Environment │  │   Settings   │     │
│  │    Config    │  │   Variables  │  │   (Pydantic) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Services                          │
│                   Google Gemini API                          │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### API Layer
- Route handling and request routing
- Request/response validation using Pydantic
- HTTP status code management
- CORS configuration
- Middleware for logging and performance tracking
- Centralized exception handling

#### Service Layer
- Business logic for AI interactions
- Async communication with Gemini API
- Timeout management and retry logic
- Response formatting and cleaning
- Agent management and validation

#### Configuration Layer
- Environment variable management
- Agent definitions and system prompts
- Application settings (timeouts, limits, etc.)
- Validation of configuration on startup

## Components and Interfaces

### 1. Configuration Module (`backend/config.py`)

**Purpose**: Centralized configuration management using Pydantic Settings

```python
class Settings(BaseSettings):
    # API Configuration
    gemini_api_key: str
    api_version: str = "v1"
    
    # Performance Settings
    request_timeout: int = 15
    max_message_length: int = 5000
    
    # Server Settings
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
```

**Key Features**:
- Type-safe configuration with validation
- Environment variable loading
- Default values for optional settings
- Validation on application startup

### 2. Agent Configuration Module (`backend/agents/config.py`)

**Purpose**: Define and manage subject-specific AI agents

```python
@dataclass
class AgentConfig:
    id: str
    name: str
    description: str
    system_prompt: str
    enabled: bool = True

# Agent registry
AGENTS: dict[str, AgentConfig] = {
    "math": AgentConfig(...),
    "english": AgentConfig(...),
    # ... other agents
}
```

**Key Features**:
- Strongly typed agent definitions
- Centralized agent registry
- Easy to add/modify agents
- Support for enabling/disabling agents

### 3. Response Models (`backend/models/responses.py`)

**Purpose**: Standardized API response structures

```python
class SuccessResponse(BaseModel):
    success: bool = True
    data: dict
    message: str = ""

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

class ErrorDetail(BaseModel):
    code: int
    message: str

class AgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    user_message: str
    reply: str
    timestamp: datetime
    metadata: dict = {}
```

**Key Features**:
- Consistent response structure
- Type validation
- Automatic JSON serialization
- Clear separation of success/error responses

### 4. Request Models (`backend/models/requests.py`)

**Purpose**: Input validation and sanitization

```python
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    
    @validator('message')
    def sanitize_message(cls, v):
        return v.strip()
```

**Key Features**:
- Automatic validation
- Length constraints
- Input sanitization
- Clear error messages for invalid input

### 5. AI Service (`backend/services/ai_service.py`)

**Purpose**: Core AI interaction logic with async operations

```python
class AIService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.executor = ThreadPoolExecutor(max_workers=10)
        genai.configure(api_key=settings.gemini_api_key)
    
    async def generate_response(
        self,
        agent_id: str,
        message: str,
        timeout: int = None
    ) -> str:
        """Generate AI response with timeout protection"""
        pass
    
    def _build_prompt(self, agent_id: str, message: str) -> str:
        """Construct prompt with system context"""
        pass
    
    def _clean_response(self, response: str) -> str:
        """Clean and format AI response"""
        pass
```

**Key Features**:
- Async-first design
- Thread pool executor for blocking Gemini calls
- Timeout protection using asyncio.wait_for()
- Prompt construction with system prompts
- Response cleaning and formatting

**Async Implementation Strategy**:
Since `google-generativeai` SDK is synchronous, we'll use:
```python
async def generate_response(self, agent_id: str, message: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        self.executor,
        self._sync_generate,
        agent_id,
        message
    )
```

### 6. Agent Manager (`backend/services/agent_manager.py`)

**Purpose**: Manage agent registry and validation

```python
class AgentManager:
    def __init__(self, agents: dict[str, AgentConfig]):
        self.agents = self._validate_agents(agents)
    
    def get_agent(self, agent_id: str) -> AgentConfig:
        """Get agent by ID with validation"""
        pass
    
    def list_agents(self) -> list[dict]:
        """List all enabled agents"""
        pass
    
    def _validate_agents(self, agents: dict) -> dict:
        """Validate agent configurations"""
        pass
```

**Key Features**:
- Agent validation on initialization
- Safe agent retrieval
- Support for enabled/disabled agents
- Easy agent listing for API

### 7. API Routers (`backend/api/v1/`)

**Purpose**: HTTP endpoint definitions

#### Agents Router (`backend/api/v1/agents.py`)

```python
router = APIRouter(prefix="/api/v1/agents", tags=["agents"])

@router.get("/")
async def list_agents() -> SuccessResponse:
    """List all available agents"""
    pass

@router.post("/{agent_id}")
async def chat_with_agent(
    agent_id: str,
    request: ChatRequest
) -> SuccessResponse:
    """Send message to specific agent"""
    pass
```

#### Health Router (`backend/api/v1/health.py`)

```python
router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check() -> SuccessResponse:
    """Service health check"""
    pass
```

### 8. Exception Handlers (`backend/api/exceptions.py`)

**Purpose**: Centralized error handling

```python
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors"""
    pass

async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions"""
    pass

async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected errors"""
    pass
```

### 9. Middleware (`backend/middleware/logging.py`)

**Purpose**: Request/response logging and performance tracking

```python
async def logging_middleware(request: Request, call_next):
    """Log requests and track performance"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    # Log response with timing
    duration = time.time() - start_time
    logger.info(f"Response: {response.status_code} ({duration:.3f}s)")
    
    return response
```

## Data Models

### Agent Metadata
```python
{
    "id": "math",
    "name": "Mathematics Agent",
    "description": "Ask me about any math topic",
    "enabled": true
}
```

### Chat Request
```python
{
    "message": "What is the Pythagorean theorem?"
}
```

### Success Response
```python
{
    "success": true,
    "data": {
        "agent_id": "math",
        "agent_name": "Mathematics Agent",
        "user_message": "What is the Pythagorean theorem?",
        "reply": "The Pythagorean theorem states...",
        "timestamp": "2025-11-06T10:30:00Z",
        "metadata": {
            "processing_time_ms": 1250
        }
    },
    "message": "Response generated successfully"
}
```

### Error Response
```python
{
    "success": false,
    "error": {
        "code": 404,
        "message": "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"
    }
}
```

### Health Check Response
```python
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

## Error Handling

### Error Categories and Responses

#### 1. Validation Errors (400)
- **Trigger**: Invalid input, missing fields, length violations
- **Response**: Detailed validation error with field-specific messages
- **Example**: "Message exceeds maximum length of 5000 characters"

#### 2. Not Found Errors (404)
- **Trigger**: Invalid agent_id
- **Response**: Clear message with list of available agents
- **Example**: "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"

#### 3. Timeout Errors (504)
- **Trigger**: AI generation exceeds timeout limit
- **Response**: Graceful message with retry suggestion
- **Example**: "Request timed out. Please try again or simplify your question."

#### 4. Service Errors (500)
- **Trigger**: Gemini API failures, unexpected exceptions
- **Response**: Generic error message without exposing internals
- **Example**: "AI service temporarily unavailable. Please try again later."

#### 5. Rate Limit Errors (429)
- **Trigger**: Too many requests (if implemented)
- **Response**: Retry-after information
- **Example**: "Rate limit exceeded. Please try again in 60 seconds."

### Error Handling Flow

```
Request → Validation → Agent Lookup → AI Service → Response
   ↓          ↓            ↓              ↓           ↓
  400        400          404        500/504       200
```

### Logging Strategy

- **INFO**: Request received, response sent, agent operations
- **WARNING**: Timeouts, rate limits, degraded performance
- **ERROR**: Service failures, unexpected exceptions
- **DEBUG**: Detailed request/response data (development only)

## Testing Strategy

### Unit Tests

#### Configuration Tests
- Validate settings loading from environment
- Test default values
- Verify validation rules

#### Agent Manager Tests
- Test agent registration and validation
- Verify agent retrieval
- Test enabled/disabled agent filtering

#### AI Service Tests
- Mock Gemini API responses
- Test timeout behavior
- Verify prompt construction
- Test response cleaning

#### Response Model Tests
- Validate serialization/deserialization
- Test field validation
- Verify error response structure

### Integration Tests

#### API Endpoint Tests
- Test all endpoints with valid inputs
- Verify response structure
- Test error scenarios
- Validate status codes

#### End-to-End Tests
- Test complete request flow
- Verify async behavior under load
- Test concurrent requests
- Validate timeout handling

### Performance Tests

#### Load Testing
- Simulate concurrent users
- Measure response times
- Identify bottlenecks
- Verify system stability under load

#### Stress Testing
- Test system limits
- Verify graceful degradation
- Test recovery from failures

### Test Coverage Goals
- Minimum 80% code coverage
- 100% coverage for critical paths (AI service, error handling)
- All API endpoints tested
- All error scenarios covered

## Performance Optimizations

### 1. Async Operations
- All endpoints use `async def`
- Blocking Gemini calls wrapped in executor
- Concurrent request handling via asyncio

### 2. Timeout Protection
- 15-second default timeout for AI generation
- Configurable per environment
- Graceful timeout handling with user-friendly messages

### 3. Connection Pooling
- Reuse Gemini API connections
- Configure appropriate pool sizes
- Monitor connection health

### 4. Response Caching (Future Enhancement)
- Cache common questions/responses
- Implement TTL-based invalidation
- Reduce API calls for repeated questions

### 5. Request Validation
- Early validation to reject invalid requests
- Minimize processing for bad inputs
- Clear error messages to reduce retry attempts

## Security Considerations

### 1. Input Validation
- Maximum message length (5000 characters)
- Input sanitization (strip whitespace, remove control characters)
- Pydantic validation for type safety

### 2. API Key Management
- Store in environment variables
- Never log or expose in responses
- Validate on startup

### 3. Rate Limiting (Future Enhancement)
- Implement per-IP rate limiting
- Protect against abuse
- Configurable limits

### 4. CORS Configuration
- Configure allowed origins appropriately
- Restrict in production environments
- Allow credentials only when necessary

### 5. Error Message Safety
- Never expose internal errors to users
- Log detailed errors server-side
- Return generic messages for security issues

## Deployment Considerations

### Environment Variables
```
GEMINI_API_KEY=<your-api-key>
REQUEST_TIMEOUT=15
MAX_MESSAGE_LENGTH=5000
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

### Docker Support
- Lightweight Python base image
- Multi-stage builds for smaller images
- Health check endpoint for container orchestration

### Monitoring and Observability
- Structured logging for log aggregation
- Health check endpoint for uptime monitoring
- Performance metrics (response times, error rates)
- Request tracing for debugging

### Scalability
- Stateless design for horizontal scaling
- No in-memory state (except configuration)
- Compatible with load balancers
- Thread pool sizing based on deployment environment

## Migration Path

### Phase 1: Core Refactoring
1. Create new module structure
2. Implement configuration layer
3. Build AI service with async support
4. Create response models

### Phase 2: API Implementation
1. Implement v1 API routers
2. Add exception handlers
3. Implement middleware
4. Update CORS configuration

### Phase 3: Testing and Validation
1. Write unit tests
2. Implement integration tests
3. Perform load testing
4. Validate against requirements

### Phase 4: Deployment
1. Update documentation
2. Configure environment
3. Deploy to staging
4. Monitor and validate
5. Deploy to production

### Backward Compatibility
- Old endpoints can coexist during migration
- Gradual frontend migration to new endpoints
- Deprecation notices for old endpoints
- Remove old endpoints after migration complete

## API Documentation

### Developer-Friendly Documentation
- OpenAPI/Swagger auto-generated documentation at `/docs`
- ReDoc alternative documentation at `/redoc`
- Clear request/response examples
- Error code reference
- Rate limiting information (if implemented)

### Example API Usage

#### List Available Agents
```bash
curl -X GET http://localhost:8000/api/v1/agents
```

#### Chat with Agent
```bash
curl -X POST http://localhost:8000/api/v1/agents/math \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the Pythagorean theorem?"}'
```

#### Health Check
```bash
curl -X GET http://localhost:8000/api/v1/health
```

## Future Enhancements

### 1. Response Streaming
- Stream AI responses as they're generated
- Improve perceived performance
- Better user experience for long responses

### 2. Conversation History
- Maintain conversation context
- Multi-turn conversations
- Session management

### 3. Advanced Agent Features
- Agent-specific parameters (temperature, max tokens)
- Custom agent creation via API
- Agent performance analytics

### 4. Caching Layer
- Redis for response caching
- Reduce API costs
- Improve response times

### 5. Observability
- OpenTelemetry integration
- Distributed tracing
- Metrics dashboard
- Alert configuration
