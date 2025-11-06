# Implementation Plan

- [x] 1. Set up project structure and configuration management






  - Create new module structure: `backend/config.py`, `backend/models/`, `backend/services/`, `backend/api/v1/`, `backend/middleware/`
  - Implement Pydantic Settings class for environment-based configuration with validation
  - Add configuration for API keys, timeouts, CORS, and logging levels
  - _Requirements: 1.1, 1.2, 11.1, 11.2, 11.3, 11.4, 11.5_
-

- [x] 2. Implement agent configuration and management






  - Create `backend/agents/config.py` with AgentConfig dataclass
  - Define all five subject agents (math, english, physics, chemistry, civic) with enhanced system prompts
  - Implement AgentManager service class with validation and retrieval methods
  - Add agent enabled/disabled support
  - _Requirements: 1.3, 1.4, 5.1, 5.2, 5.3, 5.4, 5.5_
-

- [x] 3. Create standardized request and response models







  - Implement `backend/models/requests.py` with ChatRequest model including validation
  - Implement `backend/models/responses.py` with SuccessResponse, ErrorResponse, ErrorDetail, and AgentResponse models
  - Add field validators for message length and sanitization
  - Ensure all models use snake_case and descriptive field names
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.1, 8.2, 8.3, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 4. Build async AI service layer





- [x] 4.1 Create AIService class with async architecture


  - Implement `backend/services/ai_service.py` with AIService class
  - Set up ThreadPoolExecutor for handling blocking Gemini API calls
  - Configure Gemini API client in service initialization
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4.2 Implement async response generation with timeout protection


  - Create `generate_response()` async method using `run_in_executor` for Gemini calls
  - Implement timeout protection using `asyncio.wait_for()` with configurable timeout
  - Add graceful timeout error handling with user-friendly messages
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 4.3 Implement prompt construction and response cleaning


  - Create `_build_prompt()` method to combine system prompts with user messages
  - Implement `_clean_response()` method to format and sanitize AI responses
  - Ensure markdown preservation for frontend rendering
  - _Requirements: 5.3, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 4.4 Implement rate limiting for API protection






  - Add rate limiting middleware to prevent API quota exhaustion
  - Implement per-IP rate limiting (e.g., 100 requests per minute)
  - Add global rate limiting for Gemini API calls
  - Return 429 Too Many Requests with Retry-After header
  - Add rate limit monitoring and logging
  - _Requirements: 6.1, 6.2, 15.1, 15.2_

- [ ]* 4.5 Write unit tests for AI service
  - Mock Gemini API responses for testing
  - Test timeout behavior and error handling
  - Verify prompt construction logic
  - Test response cleaning functionality
  - Test rate limiting behavior
  - _Requirements: 2.1, 2.2, 2.3, 6.1, 6.2_

- [x] 5. Implement centralized exception handling





  - Create `backend/api/exceptions.py` with custom exception handlers
  - Implement validation_exception_handler for Pydantic errors (400)
  - Implement http_exception_handler for HTTPException (404, etc.)
  - Implement general_exception_handler for unexpected errors (500)
  - Implement timeout_exception_handler for AsyncIO timeouts (504)
  - Ensure all handlers return consistent ErrorResponse format
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 6. Create API v1 routers




- [x] 6.1 Implement agents router


  - Create `backend/api/v1/agents.py` with APIRouter
  - Implement GET `/api/v1/agents` endpoint to list all enabled agents
  - Implement POST `/api/v1/agents/{agent_id}` endpoint for chat functionality
  - Add proper dependency injection for services
  - Validate agent_id and return 404 with helpful message for invalid agents
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.5, 8.4_

- [x] 6.2 Implement health check router


  - Create `backend/api/v1/health.py` with APIRouter
  - Implement GET `/api/v1/health` endpoint
  - Return service status, version, timestamp, and Gemini API status
  - Ensure response time under 1 second
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 6.3 Write integration tests for API endpoints
  - Test all endpoints with valid inputs
  - Test error scenarios (invalid agent, validation errors, timeouts)
  - Verify response structure and status codes
  - Test concurrent requests
  - _Requirements: 3.1, 3.2, 3.4, 4.1, 4.2, 4.3_

- [x] 7. Implement logging middleware





  - Create `backend/middleware/logging.py` with request/response logging
  - Log request method, path, and timestamp on request start
  - Log response status code and processing time on request completion
  - Add structured logging for easy parsing
  - Track performance metrics (latency)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 8. Update main application file





  - Refactor `backend/main.py` to use new architecture
  - Initialize Settings, AgentManager, and AIService
  - Register exception handlers
  - Add logging middleware
  - Include v1 API routers
  - Configure CORS with environment-based origins
  - Add startup event to validate configuration
  - _Requirements: 1.1, 1.5, 4.5, 11.1, 11.2, 11.3_

- [x] 9. Update dependencies





  - Update `requirements.txt` with specific versions
  - Add `pydantic-settings` for configuration management
  - Ensure `fastapi` and `uvicorn` are up to date
  - Pin all dependency versions for reproducibility
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_
-

- [x] 10. Create comprehensive API documentation




  - Ensure FastAPI auto-generates OpenAPI docs at `/docs`
  - Add detailed docstrings to all endpoints
  - Include request/response examples in docstrings
  - Document error codes and messages
  - Add README section with API usage examples
  - _Requirements: 3.4, 3.5, 7.3, 8.5_

- [ ]* 11. Implement performance and load testing
  - Create load testing script to simulate concurrent users
  - Measure response times under various loads
  - Verify timeout behavior under stress
  - Test system stability with sustained load
  - Document performance benchmarks
  - _Requirements: 2.4, 6.1, 6.2, 15.4_

- [x] 12. Update Streamlit testing interface





  - Update `frontend/streamlit_app.py` to use new v1 API endpoints
  - Update request format to match new ChatRequest model
  - Update response parsing to handle new SuccessResponse format
  - Add error handling for new error response structure
  - Display agent metadata and timestamps
  - _Requirements: 3.1, 3.2, 12.1, 12.2_

- [x] 13. Create deployment documentation





  - Document required environment variables
  - Create example `.env.example` file
  - Add deployment instructions for common platforms
  - Document health check endpoint for monitoring
  - Add troubleshooting guide
  - _Requirements: 10.1, 10.2, 11.1, 11.2, 11.3, 11.4, 11.5_
