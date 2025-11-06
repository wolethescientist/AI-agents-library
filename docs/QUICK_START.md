# Quick Start Guide

Get up and running with the Multi-Agent Learning Chat API in minutes.

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Start the Server

```bash
uvicorn backend.main:app --reload
```

The API will be available at: http://localhost:8000

## Verify Installation

### Check API Information

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Multi-Agent Learning Chat API",
  "version": "1.0.0",
  "api_version": "v1",
  "docs": "/docs",
  "health": "/api/v1/health"
}
```

### Check Health Status

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
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

## First API Call

### List Available Agents

```bash
curl http://localhost:8000/api/v1/agents
```

### Chat with an Agent

```bash
curl -X POST "http://localhost:8000/api/v1/agents/math" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is 2 + 2?"}'
```

## Interactive Documentation

Open your browser and visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try out the API directly from the browser!

## Available Agents

| Agent ID | Name | Description |
|----------|------|-------------|
| `math` | Mathematics Agent | Expert in mathematics, algebra, calculus, geometry |
| `english` | English Language Agent | Expert in English grammar, literature, writing |
| `physics` | Physics Agent | Expert in physics, mechanics, thermodynamics |
| `chemistry` | Chemistry Agent | Expert in chemistry, chemical reactions, elements |
| `civic` | Civic Education Agent | Expert in civic education, government, citizenship |

## Common Commands

### Start Server (Development)
```bash
uvicorn backend.main:app --reload
```

### Start Server (Production)
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Start Server (Custom Port)
```bash
uvicorn backend.main:app --reload --port 8080
```

### Start with Debug Logging
```bash
LOG_LEVEL=DEBUG uvicorn backend.main:app --reload
```

## Testing Interface

Start the Streamlit testing interface:

```bash
streamlit run frontend/streamlit_app.py
```

Access at: http://localhost:8501

## Next Steps

- Read the [API Documentation](API_DOCUMENTATION.md) for detailed endpoint information
- Review [Error Codes](ERROR_CODES.md) for troubleshooting
- Check the [README](../README.md) for advanced configuration

## Troubleshooting

### Server won't start

**Check Python version:**
```bash
python --version  # Should be 3.8 or higher
```

**Check dependencies:**
```bash
pip install -r requirements.txt
```

**Check environment variables:**
```bash
# Make sure .env file exists and contains GEMINI_API_KEY
cat .env
```

### API returns 500 errors

**Verify API key:**
- Check that `GEMINI_API_KEY` is set correctly in `.env`
- Ensure the API key is valid and active

**Check logs:**
- Look for error messages in the console output
- Enable debug logging: `LOG_LEVEL=DEBUG`

### CORS errors in browser

**Add your origin to CORS configuration:**
```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8501"]
```

## Getting Help

- Interactive docs: http://localhost:8000/docs
- API documentation: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- Error reference: [ERROR_CODES.md](ERROR_CODES.md)
- Main README: [README.md](../README.md)
