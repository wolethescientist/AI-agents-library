# Deployment Guide

This guide provides comprehensive instructions for deploying the Multi-Agent Learning Chat API to various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
  - [Docker Deployment](#docker-deployment)
  - [Cloud Platforms](#cloud-platforms)
- [Health Monitoring](#health-monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the application, ensure you have:

1. **Python 3.9 or higher** installed
2. **Google Gemini API Key** - Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)
3. **pip** package manager
4. **Git** (for cloning the repository)

## Environment Configuration

### Required Environment Variables

The application requires the following environment variable to function:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | **Yes** | Your Google Gemini API key | `AIzaSy...` |

### Optional Environment Variables

These variables have sensible defaults but can be customized:

| Variable | Default | Description | Valid Values |
|----------|---------|-------------|--------------|
| `API_VERSION` | `v1` | API version prefix | Any string |
| `REQUEST_TIMEOUT` | `15` | Max timeout for AI requests (seconds) | 1-60 |
| `MAX_MESSAGE_LENGTH` | `5000` | Max characters in user messages | 1-10000 |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins | JSON array of URLs |
| `LOG_LEVEL` | `INFO` | Logging verbosity | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `RATE_LIMIT_ENABLED` | `True` | Enable rate limiting | True, False |
| `RATE_LIMIT_PER_IP` | `100` | Max requests per IP per minute | 1-10000 |
| `RATE_LIMIT_GLOBAL` | `1000` | Max total requests per minute | 1-100000 |
| `APP_NAME` | `Multi-Agent Learning Chat API` | Application name | Any string |
| `APP_VERSION` | `1.0.0` | Application version | Semantic version |

### Setting Up Environment Variables

1. **Copy the example file:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` and add your API key:**
   ```bash
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Customize optional settings** (if needed):
   ```bash
   LOG_LEVEL=INFO
   REQUEST_TIMEOUT=15
   CORS_ORIGINS=["https://yourdomain.com"]
   RATE_LIMIT_ENABLED=True
   RATE_LIMIT_PER_IP=100
   RATE_LIMIT_GLOBAL=1000
   ```

## Local Development

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   copy .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

5. **Run the application:**
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify the deployment:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health
   - Alternative Docs: http://localhost:8000/redoc

### Development with Streamlit Testing Interface

To use the Streamlit testing interface:

```bash
streamlit run frontend/streamlit_app.py
```

This will open a browser window with an interactive testing interface for the API.

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY .env .env

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

# Run application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - LOG_LEVEL=INFO
      - REQUEST_TIMEOUT=15
      - CORS_ORIGINS=["*"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 5s
```

#### 3. Build and Run

```bash
# Build the image
docker build -t multi-agent-chat-api .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Cloud Platforms

#### AWS Elastic Beanstalk

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize EB application:**
   ```bash
   eb init -p python-3.11 multi-agent-chat-api
   ```

3. **Create environment:**
   ```bash
   eb create production-env
   ```

4. **Set environment variables:**
   ```bash
   eb setenv GEMINI_API_KEY=your_api_key_here
   eb setenv LOG_LEVEL=INFO
   ```

5. **Deploy:**
   ```bash
   eb deploy
   ```

6. **Check health:**
   ```bash
   eb health
   ```

#### Google Cloud Run

1. **Create Dockerfile** (see Docker section above)

2. **Build and push to Google Container Registry:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/multi-agent-chat-api
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy multi-agent-chat-api \
     --image gcr.io/PROJECT_ID/multi-agent-chat-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GEMINI_API_KEY=your_api_key_here
   ```

4. **Get service URL:**
   ```bash
   gcloud run services describe multi-agent-chat-api --region us-central1
   ```

#### Azure App Service

1. **Create App Service:**
   ```bash
   az webapp create \
     --resource-group myResourceGroup \
     --plan myAppServicePlan \
     --name multi-agent-chat-api \
     --runtime "PYTHON:3.11"
   ```

2. **Configure environment variables:**
   ```bash
   az webapp config appsettings set \
     --resource-group myResourceGroup \
     --name multi-agent-chat-api \
     --settings GEMINI_API_KEY=your_api_key_here
   ```

3. **Deploy code:**
   ```bash
   az webapp up \
     --name multi-agent-chat-api \
     --resource-group myResourceGroup
   ```

#### Heroku

1. **Create Heroku app:**
   ```bash
   heroku create multi-agent-chat-api
   ```

2. **Set environment variables:**
   ```bash
   heroku config:set GEMINI_API_KEY=your_api_key_here
   heroku config:set LOG_LEVEL=INFO
   ```

3. **Create Procfile:**
   ```
   web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   ```

5. **Check logs:**
   ```bash
   heroku logs --tail
   ```

### Production Configuration Best Practices

1. **Security:**
   - Never commit `.env` files to version control
   - Use secrets management services (AWS Secrets Manager, Azure Key Vault, etc.)
   - Restrict CORS origins to specific domains
   - Use HTTPS in production

2. **Performance:**
   - Set appropriate `REQUEST_TIMEOUT` based on your needs
   - Monitor response times and adjust as needed
   - Consider using a CDN for static assets

3. **Logging:**
   - Use `INFO` or `WARNING` level in production
   - Use `DEBUG` only for troubleshooting
   - Integrate with log aggregation services (CloudWatch, Stackdriver, etc.)

4. **Monitoring:**
   - Set up health check monitoring
   - Configure alerts for service degradation
   - Monitor API usage and rate limits

5. **Rate Limiting:**
   - Enable rate limiting in production (`RATE_LIMIT_ENABLED=True`)
   - Set appropriate per-IP limits based on expected usage
   - Adjust global limits based on Gemini API quotas
   - Monitor rate limit violations in logs

## Health Monitoring

### Health Check Endpoint

The API provides a health check endpoint for monitoring:

**Endpoint:** `GET /api/v1/health`

**Response:**
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

### Monitoring Setup

#### Using curl

```bash
# Simple health check
curl http://your-domain.com/api/v1/health

# With status code check
curl -f http://your-domain.com/api/v1/health || echo "Service is down"
```

#### Using monitoring tools

**Uptime Robot:**
1. Create new monitor
2. Monitor Type: HTTP(s)
3. URL: `https://your-domain.com/api/v1/health`
4. Monitoring Interval: 5 minutes

**Pingdom:**
1. Add new check
2. Check type: HTTP
3. URL: `https://your-domain.com/api/v1/health`
4. Check interval: 1 minute

**AWS CloudWatch:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name api-health-check \
  --alarm-description "Alert when API is unhealthy" \
  --metric-name HealthCheckStatus \
  --namespace AWS/Route53 \
  --statistic Minimum \
  --period 60 \
  --evaluation-periods 2 \
  --threshold 1 \
  --comparison-operator LessThanThreshold
```

### Health Check Response Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Service is healthy | No action needed |
| 500 | Service error | Check logs, restart service |
| 503 | Service unavailable | Check dependencies, scale resources |
| Timeout | No response | Check network, server status |

## Troubleshooting

### Common Issues and Solutions

#### 1. Application Won't Start

**Symptom:** Error on startup or immediate crash

**Possible Causes:**
- Missing or invalid `GEMINI_API_KEY`
- Invalid environment variable values
- Missing dependencies

**Solutions:**
```bash
# Check if .env file exists
dir .env

# Verify API key is set
type .env | findstr GEMINI_API_KEY

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check for configuration errors
python -c "from backend.config import get_settings; print(get_settings())"
```

#### 2. API Returns 500 Errors

**Symptom:** All requests return Internal Server Error

**Possible Causes:**
- Gemini API key is invalid or expired
- Gemini API is down or rate limited
- Network connectivity issues

**Solutions:**
```bash
# Test API key manually
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print('API key valid')"

# Check logs for detailed error
# Look for ERROR level messages

# Verify network connectivity
curl https://generativelanguage.googleapis.com/

# Check health endpoint
curl http://localhost:8000/api/v1/health
```

#### 3. Timeout Errors

**Symptom:** Requests timeout with 504 errors

**Possible Causes:**
- `REQUEST_TIMEOUT` is too low
- Gemini API is slow
- Complex queries taking too long

**Solutions:**
```bash
# Increase timeout in .env
REQUEST_TIMEOUT=30

# Restart the application
# Test with simpler queries first
```

#### 4. CORS Errors

**Symptom:** Browser shows CORS policy errors

**Possible Causes:**
- Frontend domain not in `CORS_ORIGINS`
- Incorrect CORS configuration format

**Solutions:**
```bash
# Update .env with correct origins
CORS_ORIGINS=["https://yourdomain.com","http://localhost:3000"]

# For development, allow all origins
CORS_ORIGINS=["*"]

# Restart the application
```

#### 5. High Memory Usage

**Symptom:** Application consumes excessive memory

**Possible Causes:**
- Too many concurrent requests
- Memory leak in dependencies
- Large response caching

**Solutions:**
```bash
# Monitor memory usage
# On Windows: Task Manager
# On Linux: htop or top

# Restart the application periodically
# Consider horizontal scaling instead of vertical

# Reduce concurrent workers if using gunicorn
gunicorn backend.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker
```

#### 6. Agent Not Found Errors

**Symptom:** 404 errors when accessing specific agents

**Possible Causes:**
- Invalid agent ID in request
- Agent is disabled in configuration

**Solutions:**
```bash
# List available agents
curl http://localhost:8000/api/v1/agents

# Check agent configuration
python -c "from backend.agents.config import AGENTS; print(list(AGENTS.keys()))"

# Valid agent IDs: math, english, physics, chemistry, civic
```

### Debugging Tips

#### Enable Debug Logging

```bash
# In .env file
LOG_LEVEL=DEBUG

# Restart application
# Check logs for detailed information
```

#### Test Individual Components

```python
# Test configuration loading
python -c "from backend.config import get_settings; print(get_settings())"

# Test agent manager
python -c "from backend.agents.config import AGENTS; print(AGENTS)"

# Test AI service (requires valid API key)
python -c "
from backend.services.ai_service import AIService
from backend.config import get_settings
import asyncio

async def test():
    service = AIService(get_settings())
    response = await service.generate_response('math', 'What is 2+2?')
    print(response)

asyncio.run(test())
"
```

#### Check API Documentation

Visit `http://localhost:8000/docs` to:
- View all available endpoints
- Test endpoints interactively
- See request/response schemas
- Check error responses

### Getting Help

If you continue to experience issues:

1. **Check the logs** - Most issues are logged with detailed error messages
2. **Review the API documentation** - Visit `/docs` endpoint
3. **Test the health endpoint** - Verify service status
4. **Check environment variables** - Ensure all required variables are set
5. **Verify API key** - Test your Gemini API key independently
6. **Review error codes** - See `docs/ERROR_CODES.md` for detailed error information

### Performance Optimization

#### Monitoring Response Times

```bash
# Test endpoint response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/health

# Create curl-format.txt:
echo "time_total: %{time_total}s\n" > curl-format.txt
```

#### Scaling Recommendations

- **Low traffic (<100 req/min):** Single instance with 2-4 workers
- **Medium traffic (100-1000 req/min):** 2-3 instances with load balancer
- **High traffic (>1000 req/min):** Auto-scaling group with 5+ instances

#### Resource Requirements

**Minimum:**
- CPU: 1 vCPU
- RAM: 512 MB
- Disk: 1 GB

**Recommended:**
- CPU: 2 vCPU
- RAM: 2 GB
- Disk: 5 GB

**High Load:**
- CPU: 4+ vCPU
- RAM: 4+ GB
- Disk: 10 GB

## Security Checklist

Before deploying to production:

- [ ] API key stored securely (not in code)
- [ ] CORS origins restricted to specific domains
- [ ] HTTPS enabled
- [ ] Environment variables not committed to version control
- [ ] Logging doesn't expose sensitive data
- [ ] Health check endpoint accessible
- [ ] Error messages don't expose internal details
- [ ] Rate limiting enabled and configured appropriately
- [ ] Rate limit thresholds set based on API quotas
- [ ] Monitoring and alerts set up
- [ ] Backup and recovery plan in place

## Next Steps

After successful deployment:

1. **Monitor the health endpoint** regularly
2. **Set up alerts** for service degradation
3. **Review logs** periodically for errors
4. **Monitor API usage** and costs
5. **Plan for scaling** based on traffic patterns
6. **Keep dependencies updated** for security patches
7. **Document any custom configurations** for your team

For more information, see:
- [API Documentation](API_DOCUMENTATION.md)
- [Quick Start Guide](QUICK_START.md)
- [Error Codes Reference](ERROR_CODES.md)
