# Error Codes Reference

This document provides a comprehensive reference for all error codes and messages returned by the Multi-Agent Learning Chat API.

## Error Response Format

All errors follow this consistent structure:

```json
{
  "success": false,
  "error": {
    "code": <HTTP_STATUS_CODE>,
    "message": "<ERROR_MESSAGE>"
  }
}
```

---

## HTTP Status Codes

### 200 - Success
**Description:** Request completed successfully.

**When it occurs:** All successful requests return 200 status code.

**Response structure:**
```json
{
  "success": true,
  "data": { ... },
  "message": "..."
}
```

---

### 400 - Bad Request

**Description:** The request contains invalid data or fails validation.

**Common causes:**
- Empty or whitespace-only message
- Message exceeds maximum length (5000 characters)
- Invalid JSON format
- Missing required fields
- Invalid field types

#### Error: Empty Message

**Message:** `"Message cannot be empty or only whitespace"`

**Cause:** The message field is empty, contains only whitespace, or is missing.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Message cannot be empty or only whitespace"
  }
}
```

**Solution:** Provide a non-empty message with actual content.

**Example fix:**
```json
{
  "message": "What is photosynthesis?"
}
```

---

#### Error: Message Too Long

**Message:** `"Message exceeds maximum length of 5000 characters"`

**Cause:** The message field contains more than 5000 characters.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Message exceeds maximum length of 5000 characters"
  }
}
```

**Solution:** Shorten your message to 5000 characters or less, or split it into multiple requests.

---

#### Error: Invalid JSON

**Message:** `"Invalid JSON format"` (or similar validation error)

**Cause:** The request body is not valid JSON.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Invalid JSON format"
  }
}
```

**Solution:** Ensure your request body is properly formatted JSON.

**Correct format:**
```json
{
  "message": "Your question here"
}
```

---

#### Error: Missing Required Field

**Message:** `"field required"` (Pydantic validation error)

**Cause:** The required `message` field is missing from the request body.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "field required"
  }
}
```

**Solution:** Include the `message` field in your request body.

---

### 404 - Not Found

**Description:** The requested resource (agent) does not exist or is disabled.

**Common causes:**
- Invalid agent ID
- Agent is disabled
- Typo in agent ID

#### Error: Agent Not Found

**Message:** `"Agent '{agent_id}' not found. Available agents: math, english, physics, chemistry, civic"`

**Cause:** The specified agent ID does not exist or is disabled.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 404,
    "message": "Agent 'history' not found. Available agents: math, english, physics, chemistry, civic"
  }
}
```

**Solution:** Use one of the available agent IDs:
- `math` - Mathematics Agent
- `english` - English Language Agent
- `physics` - Physics Agent
- `chemistry` - Chemistry Agent
- `civic` - Civic Education Agent

**Example fix:**
```bash
# Wrong
curl -X POST "http://localhost:8000/api/v1/agents/history" ...

# Correct
curl -X POST "http://localhost:8000/api/v1/agents/civic" ...
```

---

### 500 - Internal Server Error

**Description:** An unexpected error occurred on the server.

**Common causes:**
- Gemini API is unavailable
- Invalid API key
- Network connectivity issues
- Unexpected exceptions in the application

#### Error: AI Service Unavailable

**Message:** `"AI service temporarily unavailable. Please try again later."`

**Cause:** The Gemini API is not responding or returned an error.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 500,
    "message": "AI service temporarily unavailable. Please try again later."
  }
}
```

**Possible reasons:**
1. Invalid or expired Gemini API key
2. Gemini API is down or experiencing issues
3. Network connectivity problems
4. API quota exceeded

**Solutions:**
1. Verify your `GEMINI_API_KEY` is valid
2. Check Gemini API status: https://status.cloud.google.com/
3. Check your internet connection
4. Review API quotas and limits
5. Wait a few moments and retry

---

#### Error: Service Not Initialized

**Message:** `"Service not properly initialized"`

**Cause:** The application failed to initialize properly on startup.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 500,
    "message": "Service not properly initialized"
  }
}
```

**Solutions:**
1. Check server logs for initialization errors
2. Verify all environment variables are set correctly
3. Restart the application
4. Ensure `GEMINI_API_KEY` is configured

---

#### Error: Failed to Retrieve Agent List

**Message:** `"Failed to retrieve agent list"`

**Cause:** An error occurred while fetching the list of agents.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 500,
    "message": "Failed to retrieve agent list"
  }
}
```

**Solutions:**
1. Check server logs for detailed error information
2. Restart the application
3. Verify agent configuration is valid

---

### 429 - Too Many Requests

**Description:** Rate limit exceeded. Too many requests have been made in a short period.

**Common causes:**
- Sending requests too quickly
- Exceeding per-IP rate limit (default: 100 requests/minute)
- Exceeding global rate limit (default: 1000 requests/minute)
- Multiple clients from same IP

#### Error: Per-IP Rate Limit Exceeded

**Message:** `"Rate limit exceeded. Please slow down your requests."`

**Cause:** The IP address has exceeded the per-IP rate limit.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 429,
    "message": "Rate limit exceeded. Please slow down your requests."
  }
}
```

**Response Headers:**
```
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699272000
```

**Solutions:**
1. **Wait before retrying:** Check the `Retry-After` header for wait time
2. **Implement rate limiting:** Add delays between requests in your client
3. **Monitor rate limit headers:** Check `X-RateLimit-Remaining` before sending requests
4. **Cache responses:** Store and reuse responses for common queries
5. **Batch requests:** Group multiple questions when possible

**Example with retry logic:**
```python
import time
import requests

def chat_with_rate_limit(agent_id, message):
    response = requests.post(
        f"http://localhost:8000/api/v1/agents/{agent_id}",
        json={"message": message}
    )
    
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return chat_with_rate_limit(agent_id, message)
    
    return response.json()
```

---

#### Error: Global Rate Limit Exceeded

**Message:** `"Global rate limit exceeded. Please try again later."`

**Cause:** The total number of requests across all clients has exceeded the global rate limit.

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 429,
    "message": "Global rate limit exceeded. Please try again later."
  }
}
```

**Solutions:**
1. **Wait and retry:** The global limit resets every minute
2. **Implement exponential backoff:** Gradually increase wait time between retries
3. **Contact administrator:** If you frequently hit global limits, the limit may need adjustment

---

### 504 - Gateway Timeout

**Description:** The request took too long to process and exceeded the timeout limit.

**Common causes:**
- Complex or lengthy questions
- Slow Gemini API response
- Network latency
- High server load

#### Error: Request Timeout

**Message:** `"Request timed out after 15 seconds. Please try again or simplify your question."`

**Cause:** The AI generation took longer than the configured timeout (default: 15 seconds).

**Example:**
```json
{
  "success": false,
  "error": {
    "code": 504,
    "message": "Request timed out after 15 seconds. Please try again or simplify your question."
  }
}
```

**Solutions:**
1. **Simplify your question:** Break complex questions into smaller parts
2. **Retry the request:** The issue might be temporary
3. **Increase timeout:** Set `REQUEST_TIMEOUT` environment variable to a higher value (e.g., 30)
4. **Check Gemini API status:** Verify the API is responding normally

**Example of simplifying:**
```json
// Instead of:
{
  "message": "Explain the entire history of calculus, including all major contributors, their discoveries, the mathematical foundations, applications in physics, and modern uses in computer science and engineering."
}

// Try:
{
  "message": "Who were the main contributors to the development of calculus?"
}
```

---

## Error Handling Best Practices

### 1. Always Check the Success Field

```python
response = requests.post(url, json=data)
result = response.json()

if result["success"]:
    # Handle success
    process_data(result["data"])
else:
    # Handle error
    handle_error(result["error"])
```

### 2. Implement Retry Logic for Transient Errors

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
            result = response.json()
            
            if result["success"]:
                return result
            
            # Don't retry on client errors (4xx)
            if result["error"]["code"] < 500:
                return result
            
            # Retry on server errors (5xx)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    
    return result
```

### 3. Handle Specific Error Codes

```python
def handle_error(error):
    code = error["code"]
    message = error["message"]
    
    if code == 400:
        print(f"Invalid request: {message}")
        print("Please check your input and try again.")
    elif code == 404:
        print(f"Agent not found: {message}")
        print("Use one of the available agents: math, english, physics, chemistry, civic")
    elif code == 500:
        print(f"Server error: {message}")
        print("Please try again later or contact support.")
    elif code == 504:
        print(f"Request timeout: {message}")
        print("Try simplifying your question or retry in a moment.")
    else:
        print(f"Unexpected error ({code}): {message}")
```

### 4. Validate Input Before Sending

```python
def validate_message(message):
    """Validate message before sending to API."""
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    if len(message) > 5000:
        raise ValueError("Message too long (max 5000 characters)")
    
    return message.strip()

def validate_agent_id(agent_id, available_agents):
    """Validate agent ID before sending request."""
    if agent_id not in available_agents:
        raise ValueError(
            f"Invalid agent '{agent_id}'. "
            f"Available: {', '.join(available_agents)}"
        )
```

### 5. Log Errors for Debugging

```python
import logging

logger = logging.getLogger(__name__)

def chat_with_agent(agent_id, message):
    try:
        response = requests.post(
            f"http://localhost:8000/api/v1/agents/{agent_id}",
            json={"message": message}
        )
        result = response.json()
        
        if not result["success"]:
            logger.error(
                f"API error: {result['error']['code']} - "
                f"{result['error']['message']}"
            )
        
        return result
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
```

---

## Troubleshooting Guide

### Problem: Getting 400 errors frequently

**Possible causes:**
- Not validating input before sending
- Sending empty or whitespace-only messages
- Messages exceeding length limit

**Solutions:**
1. Implement client-side validation
2. Trim whitespace from messages
3. Check message length before sending
4. Validate JSON format

---

### Problem: Getting 404 errors

**Possible causes:**
- Using incorrect agent ID
- Typo in agent ID
- Agent is disabled

**Solutions:**
1. Call `GET /api/v1/agents` to get list of available agents
2. Use exact agent IDs: `math`, `english`, `physics`, `chemistry`, `civic`
3. Check for typos (agent IDs are case-sensitive)

---

### Problem: Getting 500 errors

**Possible causes:**
- Invalid Gemini API key
- Gemini API is down
- Network issues
- Server misconfiguration

**Solutions:**
1. Verify `GEMINI_API_KEY` in `.env` file
2. Check Gemini API status
3. Review server logs for detailed errors
4. Restart the application
5. Check network connectivity

---

### Problem: Getting 429 rate limit errors

**Possible causes:**
- Sending requests too quickly
- Multiple requests from same IP
- High traffic from all users

**Solutions:**
1. Implement delays between requests (e.g., 1 second)
2. Monitor `X-RateLimit-Remaining` header
3. Respect `Retry-After` header when rate limited
4. Cache common responses
5. Implement exponential backoff for retries

---

### Problem: Getting 504 timeout errors

**Possible causes:**
- Questions are too complex
- Gemini API is slow
- Timeout setting is too low

**Solutions:**
1. Simplify questions
2. Break complex questions into parts
3. Increase `REQUEST_TIMEOUT` environment variable
4. Retry the request
5. Check Gemini API performance

---

## Getting Help

If you continue to experience errors:

1. **Check the logs:** Server logs contain detailed error information
2. **Review documentation:** Visit `/docs` for interactive API documentation
3. **Test with curl:** Verify the API works with simple curl commands
4. **Check configuration:** Ensure all environment variables are set correctly
5. **Open an issue:** Report persistent issues on GitHub

---

## Related Documentation

- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
- [README](../README.md) - Setup and usage guide
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
