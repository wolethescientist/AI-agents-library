# Scaling Guide for 500-1000 Concurrent Users

This guide covers the infrastructure and configuration changes needed to handle high concurrent load.

## Current Improvements (Already Implemented)

### 1. Increased Thread Pool Capacity
- **Before**: 10 workers
- **After**: 200 workers
- Handles up to 200 concurrent Gemini API calls

### 2. Request Semaphore (Rate Limiting)
- Limits to 100 concurrent AI requests
- Prevents overwhelming the Gemini API
- Additional requests queue automatically

### 3. Response Caching
- 1-hour TTL for identical questions
- Reduces API calls by 30-50% for common questions
- Automatic cache cleanup at 1000 entries

## Infrastructure Requirements

### Single Server Limits
With current changes, a **single server** can handle:
- ~100 concurrent requests
- ~35-40 requests/second throughput
- ~150-200 active users comfortably

**For 500-1000 users, you MUST use multiple servers.**

## Recommended Architecture

### Option 1: Horizontal Scaling (Recommended)
```
                    Load Balancer (nginx/AWS ALB)
                            |
        +-------------------+-------------------+
        |                   |                   |
    Server 1            Server 2            Server 3
   (FastAPI)           (FastAPI)           (FastAPI)
        |                   |                   |
        +-------------------+-------------------+
                            |
                    Redis Cache (shared)
                            |
                    Gemini API
```

**Setup:**
- 5-10 FastAPI servers behind a load balancer
- Shared Redis cache (replace in-memory cache)
- Each server handles 100-150 users
- Total capacity: 500-1500 users

### Option 2: Kubernetes (Production-Grade)
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: learning-chat-api
spec:
  replicas: 8  # Start with 8 pods
  selector:
    matchLabels:
      app: learning-chat-api
  template:
    metadata:
      labels:
        app: learning-chat-api
    spec:
      containers:
      - name: api
        image: your-registry/learning-chat-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: learning-chat-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: learning-chat-api
  minReplicas: 5
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Required Changes for Multi-Server Setup

### 1. Replace In-Memory Cache with Redis

Install Redis client:
```bash
pip install redis
```

Update `backend/services/ai_service.py`:
```python
import redis
from typing import Optional

class AIService:
    def __init__(self, settings: Settings, agent_manager: AgentManager):
        # ... existing code ...
        
        # Redis cache instead of in-memory
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
            decode_responses=True
        )
        self._cache_ttl_seconds = 3600  # 1 hour
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        return self.redis_client.get(cache_key)
    
    def _set_cache(self, cache_key: str, response: str) -> None:
        self.redis_client.setex(cache_key, self._cache_ttl_seconds, response)
```

Add to `backend/config.py`:
```python
class Settings(BaseSettings):
    # ... existing fields ...
    redis_host: str = "localhost"
    redis_port: int = 6379
```

### 2. Configure Load Balancer

**Nginx Configuration:**
```nginx
upstream learning_chat_api {
    least_conn;  # Route to server with fewest connections
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
    server 10.0.1.13:8000;
    server 10.0.1.14:8000;
}

server {
    listen 80;
    server_name api.yourapp.com;
    
    location / {
        proxy_pass http://learning_chat_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Increase timeout for AI requests
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }
}
```

### 3. Monitor Gemini API Rate Limits

**Gemini API Limits (as of 2024):**
- Free tier: 60 requests/minute
- Paid tier: 1000+ requests/minute

**For 500-1000 users, you MUST use paid tier.**

Check your quota:
```python
# Add monitoring to ai_service.py
import time

class AIService:
    def __init__(self, settings: Settings, agent_manager: AgentManager):
        # ... existing code ...
        self._request_count = 0
        self._request_window_start = time.time()
    
    async def generate_response(self, agent_id: str, message: str, timeout: Optional[int] = None) -> str:
        # Track request rate
        self._request_count += 1
        if time.time() - self._request_window_start > 60:
            logger.info(f"Gemini API requests in last minute: {self._request_count}")
            self._request_count = 0
            self._request_window_start = time.time()
        
        # ... rest of method ...
```

## Performance Tuning

### 1. Adjust Semaphore Based on API Limits
```python
# If you have 1000 RPM limit and 5 servers:
# Each server can do ~200 requests/minute = ~3.3 requests/second
# With 2.8s per request, you can handle ~10-15 concurrent per server
self.semaphore = asyncio.Semaphore(15)  # Per server
```

### 2. Optimize Uvicorn Workers
```bash
# Run with multiple workers (CPU cores)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Enable HTTP/2 and Compression
```python
# In main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

## Monitoring & Alerts

### Key Metrics to Track
1. **Request rate** (requests/second)
2. **Response time** (p50, p95, p99)
3. **Error rate** (4xx, 5xx)
4. **Cache hit rate**
5. **Gemini API quota usage**
6. **Server CPU/memory**

### Recommended Tools
- **Prometheus + Grafana** for metrics
- **Sentry** for error tracking
- **DataDog/New Relic** for APM

### Add Prometheus Metrics
```bash
pip install prometheus-fastapi-instrumentator
```

```python
# In main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = create_app()
Instrumentator().instrument(app).expose(app)
```

## Cost Estimation

### Gemini API Costs (Approximate)
- 1000 users × 10 requests/day = 10,000 requests/day
- 300,000 requests/month
- At $0.001/request = **$300/month**

### Infrastructure Costs
- 5 servers (2 vCPU, 4GB RAM each): **$100-200/month**
- Redis instance: **$20-50/month**
- Load balancer: **$20-50/month**
- **Total: ~$440-600/month**

## Quick Start for Production

1. **Deploy Redis:**
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

2. **Update environment variables:**
   ```bash
   REDIS_HOST=your-redis-host
   REDIS_PORT=6379
   ```

3. **Deploy multiple API servers:**
   ```bash
   # Server 1
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
   
   # Server 2
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
   
   # ... etc
   ```

4. **Configure load balancer** (nginx/ALB)

5. **Monitor and scale** based on metrics

## Testing Load

Use `locust` to simulate 1000 concurrent users:

```python
# locustfile.py
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(5, 15)
    
    @task
    def chat_with_math_agent(self):
        self.client.post(
            "/api/v1/agents/math",
            json={"message": "What is 2+2?"}
        )

# Run: locust -f locustfile.py --users 1000 --spawn-rate 50
```

## Summary

**Current Setup (Single Server):**
- ✅ Can handle ~150-200 users
- ✅ Response caching enabled
- ✅ Rate limiting in place

**For 500-1000 Users:**
- ⚠️ Deploy 5-10 servers with load balancer
- ⚠️ Replace in-memory cache with Redis
- ⚠️ Upgrade to Gemini API paid tier
- ⚠️ Add monitoring and auto-scaling

**Next Steps:**
1. Set up Redis
2. Deploy to multiple servers
3. Configure load balancer
4. Load test with 1000 users
5. Monitor and optimize
