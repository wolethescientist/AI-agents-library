# Documentation Index

Welcome to the Multi-Agent Learning Chat API documentation. This directory contains comprehensive guides and references for using the API.

## Documentation Files

### 📚 [Quick Start Guide](QUICK_START.md)
**Start here if you're new to the API**

Get up and running in minutes with:
- Installation instructions
- Environment setup
- First API calls
- Common commands
- Basic troubleshooting

**Best for:** New users, quick setup, getting started

---

### 📖 [API Documentation](API_DOCUMENTATION.md)
**Complete API reference**

Comprehensive documentation including:
- All endpoints with examples
- Request/response models
- Authentication and configuration
- Code examples (Python, JavaScript, cURL)
- Best practices
- Architecture overview

**Best for:** Integration, development, detailed reference

---

### 🚀 [Deployment Guide](DEPLOYMENT.md)
**Production deployment instructions**

Comprehensive deployment guide with:
- Environment configuration reference
- Docker deployment
- Cloud platform guides (AWS, GCP, Azure, Heroku)
- Health monitoring setup
- Production best practices
- Security checklist
- Troubleshooting deployment issues

**Best for:** DevOps, production deployment, system administration

---

### ⚠️ [Error Codes Reference](ERROR_CODES.md)
**Troubleshooting and error handling**

Complete error reference with:
- All HTTP status codes
- Error messages and causes
- Solutions and fixes
- Error handling best practices
- Troubleshooting guide

**Best for:** Debugging, error handling, troubleshooting

---

## Interactive Documentation

The API provides auto-generated interactive documentation:

### Swagger UI
**URL:** http://localhost:8000/docs

**Features:**
- Try out API endpoints directly in the browser
- See request/response examples
- View schema definitions
- Test with different parameters

### ReDoc
**URL:** http://localhost:8000/redoc

**Features:**
- Clean, readable documentation
- Detailed schema information
- Code samples
- Search functionality

---

## Quick Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents` | List all available agents |
| POST | `/api/v1/agents/{agent_id}` | Chat with a specific agent |
| GET | `/api/v1/health` | Health check endpoint |
| GET | `/` | API information |

### Available Agents

- `math` - Mathematics Agent
- `english` - English Language Agent
- `physics` - Physics Agent
- `chemistry` - Chemistry Agent
- `civic` - Civic Education Agent

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/agents/math" \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the Pythagorean theorem?"}'
```

---

## Documentation Standards

All documentation follows these principles:

1. **Clear Examples:** Every endpoint includes working code examples
2. **Error Handling:** Comprehensive error documentation with solutions
3. **Best Practices:** Recommended patterns and approaches
4. **Code Samples:** Examples in multiple languages (Python, JavaScript, cURL)
5. **Troubleshooting:** Common issues and solutions

---

## Getting Help

### For Setup Issues
→ See [Quick Start Guide](QUICK_START.md)

### For Deployment
→ See [Deployment Guide](DEPLOYMENT.md)

### For API Questions
→ See [API Documentation](API_DOCUMENTATION.md)

### For Errors
→ See [Error Codes Reference](ERROR_CODES.md)

### For Interactive Testing
→ Visit http://localhost:8000/docs

### For General Information
→ See [Main README](../README.md)

---

## Contributing to Documentation

When updating documentation:

1. **Keep examples working:** Test all code examples
2. **Update all references:** If changing an endpoint, update all docs
3. **Follow the format:** Maintain consistent structure
4. **Include examples:** Always provide working examples
5. **Test thoroughly:** Verify all links and code samples

---

## Documentation Checklist

When adding a new endpoint:

- [ ] Add to API_DOCUMENTATION.md with examples
- [ ] Document all error codes in ERROR_CODES.md
- [ ] Add docstrings with examples in the code
- [ ] Include in OpenAPI schema (automatic with FastAPI)
- [ ] Update Quick Start if relevant
- [ ] Update Deployment Guide if configuration changes
- [ ] Test all examples
- [ ] Update this index if needed

---

## Version History

### v1.0.0 (2025-11-06)
- Initial documentation release
- Quick Start Guide
- Complete API Documentation
- Deployment Guide
- Error Codes Reference
- Interactive Swagger UI
- ReDoc documentation

---

## Feedback

Found an issue with the documentation?
- Open an issue on GitHub
- Submit a pull request with improvements
- Contact the development team

---

**Last Updated:** 2025-11-06  
**API Version:** v1.0.0
