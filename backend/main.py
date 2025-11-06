"""
Multi-Agent Learning Chat API - Main Application

This is the main FastAPI application file that initializes and configures
the AI-powered educational chat system with modular architecture.
"""
import warnings
import logging
from contextlib import asynccontextmanager

# Suppress pkg_resources deprecation warning from google.rpc
warnings.filterwarnings("ignore", category=UserWarning, module="google.rpc")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import Settings, configure_logging
from backend.agents.config import AgentManager, AGENTS
from backend.services.ai_service import AIService
from backend.api.v1 import agents, health
from backend.api.exceptions import register_exception_handlers
from backend.middleware.logging import LoggingMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware

# Initialize logger (will be configured after settings are loaded)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    
    Handles:
    - Configuration validation on startup
    - Service initialization
    - Cleanup on shutdown
    """
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Multi-Agent Learning Chat API")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        settings = app.state.settings
        logger.info(f"Configuration loaded successfully")
        logger.info(f"  - App Name: {settings.app_name}")
        logger.info(f"  - App Version: {settings.app_version}")
        logger.info(f"  - API Version: {settings.api_version}")
        logger.info(f"  - Request Timeout: {settings.request_timeout}s")
        logger.info(f"  - Max Message Length: {settings.max_message_length}")
        logger.info(f"  - Log Level: {settings.log_level}")
        logger.info(f"  - CORS Origins: {settings.cors_origins}")
        logger.info(f"  - Rate Limiting: {'Enabled' if settings.rate_limit_enabled else 'Disabled'}")
        if settings.rate_limit_enabled:
            logger.info(f"    - Per-IP Limit: {settings.rate_limit_per_ip} req/min")
            logger.info(f"    - Global Limit: {settings.rate_limit_global} req/min")
        
        # Validate agent configuration
        agent_manager = app.state.agent_manager
        agent_count = agent_manager.get_agent_count()
        logger.info(f"Agent Manager initialized with {agent_count} enabled agents:")
        for agent in agent_manager.list_agents():
            logger.info(f"  - {agent['id']}: {agent['name']}")
        
        # Validate AI service
        logger.info("AI Service initialized successfully")
        logger.info(f"  - Gemini API configured: ✓")
        
        logger.info("=" * 60)
        logger.info("Application startup complete")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multi-Agent Learning Chat API")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Load settings
    settings = Settings()
    
    # Configure logging based on settings
    configure_logging(settings)
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Production-grade AI-powered educational chat system with subject-specific agents",
        lifespan=lifespan
    )
    
    # Store settings in app state
    app.state.settings = settings
    
    # Initialize services
    agent_manager = AgentManager(AGENTS)
    ai_service = AIService(settings, agent_manager)
    
    # Store services in app state
    app.state.agent_manager = agent_manager
    app.state.ai_service = ai_service
    
    # Set services for router dependency injection
    agents.set_services(agent_manager, ai_service)
    
    # Configure CORS with environment-based origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add rate limiting middleware (if enabled)
    if settings.rate_limit_enabled:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=settings.rate_limit_per_ip,
            global_requests_per_minute=settings.rate_limit_global,
            window_size=60
        )
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include v1 API routers
    app.include_router(agents.router)
    app.include_router(health.router)
    
    # Root endpoint for basic info
    @app.get(
        "/",
        tags=["root"],
        summary="API information",
        description="Returns basic information about the API and links to documentation"
    )
    async def root():
        """Root endpoint providing basic API information and navigation.
        
        **Example Response:**
        ```json
        {
            "message": "Multi-Agent Learning Chat API",
            "version": "1.0.0",
            "api_version": "v1",
            "docs": "/docs",
            "health": "/api/v1/health"
        }
        ```
        """
        return {
            "message": settings.app_name,
            "version": settings.app_version,
            "api_version": settings.api_version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    return app


# Create the application instance
app = create_app()
