"""
AI Service Layer for handling async AI interactions with Google Gemini API.

This module provides the AIService class that manages async communication with
the Gemini API, including timeout protection, prompt construction, and response
formatting.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
import google.generativeai as genai

from backend.config import Settings
from backend.agents.config import AgentManager

logger = logging.getLogger(__name__)


class AIService:
    """Service class for async AI response generation using Google Gemini API.
    
    This service handles:
    - Async communication with the synchronous Gemini API
    - Timeout protection for AI generation requests
    - Prompt construction with agent-specific system prompts
    - Response cleaning and formatting
    """
    
    def __init__(self, settings: Settings, agent_manager: AgentManager):
        """Initialize the AI service with configuration and agent manager.
        
        Args:
            settings: Application settings containing API keys and timeouts
            agent_manager: Agent manager for retrieving agent configurations
        """
        self.settings = settings
        self.agent_manager = agent_manager
        
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Set up thread pool executor for handling blocking Gemini API calls
        # Configurable via MAX_CONCURRENT_REQUESTS and THREAD_POOL_WORKERS env vars
        self.executor = ThreadPoolExecutor(
            max_workers=settings.thread_pool_workers,
            thread_name_prefix="gemini"
        )
        
        # Semaphore to limit concurrent AI requests and prevent API rate limit issues
        # Adjust MAX_CONCURRENT_REQUESTS based on your Gemini API quota
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        
        # Initialize the Gemini model with optimized settings
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            }
        )
        
        logger.info(
            f"AIService initialized with Gemini API "
            f"(workers={settings.thread_pool_workers}, "
            f"concurrent={settings.max_concurrent_requests})"
        )
    
    def __del__(self):
        """Cleanup executor on service destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
            logger.debug("AIService executor shutdown")

    async def generate_response(
        self,
        agent_id: str,
        message: str,
        timeout: Optional[int] = None
    ) -> str:
        """Generate an AI response asynchronously with timeout protection.
        
        This method wraps the synchronous Gemini API call in an executor to make it
        async, and applies timeout protection to prevent hanging requests.
        
        Args:
            agent_id: The ID of the agent to use for response generation
            message: The user's message/question
            timeout: Optional timeout in seconds (uses settings default if not provided)
        
        Returns:
            The cleaned AI response text
        
        Raises:
            asyncio.TimeoutError: If the request exceeds the timeout limit
            KeyError: If the agent is not found or disabled
            Exception: For other AI service errors
        """
        # Use configured timeout if not specified
        if timeout is None:
            timeout = self.settings.request_timeout
        
        logger.info(f"Generating response for agent '{agent_id}' with timeout {timeout}s")
        
        try:
            # Use semaphore to limit concurrent requests and prevent overwhelming the API
            async with self.semaphore:
                # Apply timeout protection using asyncio.wait_for
                response = await asyncio.wait_for(
                    self._generate_response_async(agent_id, message),
                    timeout=timeout
                )
            
            logger.info(f"Successfully generated response for agent '{agent_id}'")
            return response
            
        except asyncio.TimeoutError:
            logger.warning(
                f"Request timeout for agent '{agent_id}' after {timeout}s"
            )
            # Graceful timeout error with user-friendly message
            raise asyncio.TimeoutError(
                f"Request timed out after {timeout} seconds. "
                "Please try again or simplify your question."
            )
        except KeyError as e:
            # Agent not found or disabled
            logger.error(f"Agent error: {e}")
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Error generating response for agent '{agent_id}': {e}",
                exc_info=True
            )
            raise Exception("AI service temporarily unavailable. Please try again later.")

    async def generate_response_stream(
        self,
        agent_id: str,
        message: str,
        timeout: Optional[int] = None
    ):
        """Generate an AI response with streaming support.
        
        This method streams tokens as they're generated, providing immediate feedback
        to users and significantly improving perceived response time.
        
        Args:
            agent_id: The ID of the agent to use for response generation
            message: The user's message/question
            timeout: Optional timeout in seconds (uses settings default if not provided)
        
        Yields:
            Chunks of the AI response as they're generated
        
        Raises:
            asyncio.TimeoutError: If the request exceeds the timeout limit
            KeyError: If the agent is not found or disabled
            Exception: For other AI service errors
        """
        if timeout is None:
            timeout = self.settings.request_timeout
        
        logger.info(f"Generating streaming response for agent '{agent_id}' with timeout {timeout}s")
        
        try:
            async with self.semaphore:
                async for chunk in self._generate_response_stream_async(agent_id, message, timeout):
                    yield chunk
            
            logger.info(f"Successfully completed streaming response for agent '{agent_id}'")
            
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout for agent '{agent_id}' after {timeout}s")
            raise asyncio.TimeoutError(
                f"Request timed out after {timeout} seconds. "
                "Please try again or simplify your question."
            )
        except KeyError as e:
            logger.error(f"Agent error: {e}")
            raise
        except Exception as e:
            logger.error(
                f"Error generating streaming response for agent '{agent_id}': {e}",
                exc_info=True
            )
            raise Exception("AI service temporarily unavailable. Please try again later.")
    
    async def _generate_response_async(self, agent_id: str, message: str) -> str:
        """Internal async wrapper for the synchronous Gemini API call.
        
        This method runs the blocking Gemini API call in a thread pool executor
        to avoid blocking the async event loop.
        
        Args:
            agent_id: The ID of the agent to use
            message: The user's message
        
        Returns:
            The cleaned AI response
        
        Raises:
            KeyError: If the agent is not found
            Exception: For Gemini API errors
        """
        # Get the event loop
        loop = asyncio.get_event_loop()
        
        # Run the blocking call in the executor
        response = await loop.run_in_executor(
            self.executor,
            self._sync_generate,
            agent_id,
            message
        )
        
        return response

    async def _generate_response_stream_async(self, agent_id: str, message: str, timeout: int):
        """Internal async wrapper for streaming Gemini API call.
        
        Args:
            agent_id: The ID of the agent to use
            message: The user's message
            timeout: Timeout in seconds
        
        Yields:
            Chunks of the AI response
        
        Raises:
            KeyError: If the agent is not found
            Exception: For Gemini API errors
        """
        loop = asyncio.get_event_loop()
        
        # Build the prompt
        prompt = self._build_prompt(agent_id, message)
        
        # Create a queue for streaming chunks
        queue = asyncio.Queue()
        
        # Run streaming in executor
        async def stream_worker():
            try:
                await loop.run_in_executor(
                    self.executor,
                    self._sync_generate_stream,
                    prompt,
                    queue,
                    loop  # Pass the event loop to the thread
                )
            except Exception as e:
                await queue.put(("error", e))
            finally:
                await queue.put(("done", None))
        
        # Start the worker
        task = asyncio.create_task(stream_worker())
        
        try:
            # Stream chunks with timeout
            start_time = loop.time()
            
            while True:
                # Check timeout
                elapsed = loop.time() - start_time
                if elapsed > timeout:
                    task.cancel()
                    raise asyncio.TimeoutError()
                
                # Get next chunk with remaining timeout
                remaining_timeout = timeout - elapsed
                try:
                    msg_type, data = await asyncio.wait_for(
                        queue.get(),
                        timeout=remaining_timeout
                    )
                except asyncio.TimeoutError:
                    task.cancel()
                    raise
                
                if msg_type == "done":
                    break
                elif msg_type == "error":
                    raise data
                elif msg_type == "chunk":
                    yield data
                    
        finally:
            if not task.done():
                task.cancel()
    
    def _sync_generate(self, agent_id: str, message: str) -> str:
        """Synchronous method that calls the Gemini API.
        
        This method is executed in a thread pool to avoid blocking the async loop.
        
        Args:
            agent_id: The ID of the agent to use
            message: The user's message
        
        Returns:
            The cleaned AI response
        
        Raises:
            KeyError: If the agent is not found
            Exception: For Gemini API errors
        """
        # Build the prompt with system context
        prompt = self._build_prompt(agent_id, message)
        
        # Call Gemini API (blocking call)
        response = self.model.generate_content(prompt)
        
        # Clean and format the response
        cleaned_response = self._clean_response(response.text)
        
        return cleaned_response

    def _sync_generate_stream(self, prompt: str, queue, loop):
        """Synchronous method that streams from Gemini API.
        
        This method is executed in a thread pool and puts chunks into a queue.
        
        Args:
            prompt: The complete prompt
            queue: Async queue to put chunks into
            loop: The event loop to use for thread-safe queue operations
        """
        try:
            # Call Gemini API with streaming
            response = self.model.generate_content(prompt, stream=True)
            
            # Stream chunks
            for chunk in response:
                if chunk.text:
                    # Put chunk in queue (thread-safe)
                    asyncio.run_coroutine_threadsafe(
                        queue.put(("chunk", chunk.text)),
                        loop
                    ).result()
                    
        except Exception as e:
            # Put error in queue
            asyncio.run_coroutine_threadsafe(
                queue.put(("error", e)),
                loop
            ).result()

    def _build_prompt(self, agent_id: str, message: str) -> str:
        """Construct a prompt by combining agent system prompt with user message.
        
        This method retrieves the agent's system prompt and combines it with the
        user's message to provide context-aware responses.
        
        Args:
            agent_id: The ID of the agent
            message: The user's message
        
        Returns:
            The complete prompt string
        
        Raises:
            KeyError: If the agent is not found or disabled
        """
        # Get the agent configuration
        agent = self.agent_manager.get_agent(agent_id)
        
        # Combine system prompt with user message
        prompt = f"{agent.system_prompt}\n\nUser Question: {message}"
        
        logger.debug(f"Built prompt for agent '{agent_id}' (length: {len(prompt)} chars)")
        
        return prompt
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the AI response.
        
        This method sanitizes the AI response by removing system artifacts and
        ensuring proper formatting while preserving markdown for frontend rendering.
        
        Args:
            response: The raw AI response text
        
        Returns:
            The cleaned and formatted response
        """
        if not response:
            return ""
        
        # Strip leading/trailing whitespace
        cleaned = response.strip()
        
        # Remove any potential system artifacts or control characters
        # while preserving markdown formatting
        cleaned = cleaned.replace('\r\n', '\n')  # Normalize line endings
        cleaned = cleaned.replace('\r', '\n')
        
        # Remove excessive blank lines (more than 2 consecutive newlines)
        while '\n\n\n' in cleaned:
            cleaned = cleaned.replace('\n\n\n', '\n\n')
        
        logger.debug(f"Cleaned response (length: {len(cleaned)} chars)")
        
        return cleaned
    
    def is_document_related_query(
        self,
        message: str,
        has_active_session: bool
    ) -> bool:
        """Determine if a query is document-related.
        
        When a document session is active, we default to treating ALL queries
        as document-related. This allows the RAG system to intelligently decide
        whether to use document context or fall back to general knowledge.
        
        This approach is more robust than keyword-based heuristics because:
        1. Users naturally refer to uploaded content without explicit keywords
        2. The AI can see the document context and decide relevance
        3. No false negatives from missing keyword patterns
        
        Args:
            message: The user's query message
            has_active_session: Whether a document session is currently active
        
        Returns:
            True if a document session is active, False otherwise
        """
        if not has_active_session:
            return False
        
        # When a document is uploaded, assume all queries are document-related
        # The RAG system will handle context intelligently
        logger.debug("Document query detected (active session present)")
        return True
