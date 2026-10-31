"""Base agent class"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from loguru import logger

from src.llm.gemini_client import GeminiClient
from src.llm.groq_client import GroqClient
from src.utils.cache import SQLiteCache, get_cache
from src.utils.config import settings


class BaseAgent(ABC):
    """Base class for all agents"""

    def __init__(
        self,
        name: str,
        memory: Optional[Any] = None,
        orchestrator: Optional[Any] = None
    ):
        """Initialize base agent

        Args:
            name: Agent name
            memory: Shared memory system
            orchestrator: Reference to orchestrator for communication
        """
        self.name = name
        self.memory = memory
        self.orchestrator = orchestrator

        # Get agent-specific configuration
        agent_config = settings.get_agent_config(name)
        self.model_name = agent_config.model
        self.max_retries = agent_config.max_retries
        self.timeout = agent_config.timeout

        # Initialize LLM client based on provider
        provider = settings.llm_provider

        if provider == "groq" and settings.groq_api_key:
            # Use Groq with available models
            groq_models = {
                "gemini-1.5-flash": "qwen/qwen3.8-27b",  # Map to available model
                "gemini-1.5-pro": "qwen/qwen3.8-27b"  # Map to available model
            }
            groq_model = groq_models.get(self.model_name, "qwen/qwen3.8-27b")
            self.llm = GroqClient(model_name=groq_model)
            logger.info(f"Initialized {name} agent with Groq model: {groq_model}")

        elif provider == "gemini" and settings.gemini_api_key:
            # Use Gemini
            self.llm = GeminiClient(model_name=self.model_name)
            logger.info(f"Initialized {name} agent with Gemini model: {self.model_name}")

        else:
            # Auto-select based on available API key
            if settings.groq_api_key:
                self.llm = GroqClient(model_name="llama-3.1-70b-versatile")
                logger.info(f"Initialized {name} agent with Groq (auto-selected)")
            elif settings.gemini_api_key:
                self.llm = GeminiClient(model_name=self.model_name)
                logger.info(f"Initialized {name} agent with Gemini (auto-selected)")
            else:
                raise ValueError("No LLM API key configured! Set GROQ_API_KEY or GEMINI_API_KEY in .env")

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's main task

        Args:
            task: Task dictionary with parameters

        Returns:
            Result dictionary
        """
        pass

    def think(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 400  # Reduced for FREE tier (1000 OTPM limit)
    ) -> str:
        """Use LLM to reason about a problem

        Args:
            prompt: The prompt to reason about
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            LLM's response
        """
        logger.debug(f"[{self.name}] Thinking about prompt...")
        cache = get_cache()
        key = SQLiteCache.make_key("text", self.llm.model_name, prompt, temperature, max_tokens) if cache else None
        cached = cache.get(key) if cache else None
        if cached is not None:
            self.llm.last_truncated = False
            return cached

        result = self.llm.generate(prompt, temperature, max_tokens)
        if cache and result and not self.llm.last_truncated:
            cache.set(key, result)
        return result

    def think_json(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 400  # Reduced for FREE tier (1000 OTPM limit)
    ) -> Dict[str, Any]:
        """Use LLM to reason and return JSON

        Args:
            prompt: The prompt to reason about
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Parsed JSON response
        """
        logger.debug(f"[{self.name}] Thinking (JSON mode)...")
        cache = get_cache()
        key = SQLiteCache.make_key("json", self.llm.model_name, prompt, temperature, max_tokens) if cache else None
        cached = cache.get(key) if cache else None
        if cached:
            logger.info(f"[{self.name}] Reused cached reply")
            return cached

        result = self.llm.generate_json(prompt, temperature, max_tokens)
        if cache and result:
            cache.set(key, result)
        return result

    async def _ask_json(self, prompt: str, temperature: float = 0.7, max_tokens: int = 400) -> Dict[str, Any]:
        """Run think_json in a worker thread so the event loop stays responsive"""
        return await asyncio.to_thread(self.think_json, prompt, temperature, max_tokens)

    async def _ask_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 400) -> str:
        """Run think in a worker thread so the event loop stays responsive"""
        return await asyncio.to_thread(self.think, prompt, temperature, max_tokens)

    def remember(self, key: str, value: Any) -> None:
        """Store information in shared memory

        Args:
            key: Memory key
            value: Value to store
        """
        if self.memory:
            full_key = f"{self.name}:{key}"
            self.memory.store(full_key, value)
            logger.debug(f"[{self.name}] Stored memory: {full_key}")

    def recall(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """Retrieve information from shared memory

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters

        Returns:
            List of matching results
        """
        if self.memory:
            logger.debug(f"[{self.name}] Recalling: {query}")
            return self.memory.search(query, top_k=top_k, filters=filters)
        return []

    def send_message(self, to_agent: str, message: Dict[str, Any]) -> None:
        """Send message to another agent

        Args:
            to_agent: Target agent name
            message: Message content
        """
        if self.orchestrator:
            logger.debug(f"[{self.name}] Sending message to {to_agent}")
            self.orchestrator.route_message(
                from_agent=self.name,
                to_agent=to_agent,
                content=message
            )

    def notify(self, status: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Notify orchestrator of status update

        Args:
            status: Status message
            data: Optional data to include
        """
        if self.orchestrator:
            logger.info(f"[{self.name}] {status}")
            self.orchestrator.on_agent_update(
                agent_name=self.name,
                status=status,
                data=data or {}
            )

    def get_context(self, task: Dict[str, Any]) -> str:
        """Build context string for this agent's task

        Args:
            task: Task dictionary

        Returns:
            Context string
        """
        context_parts = [
            f"You are the {self.name.upper()} agent.",
            f"Your role: {self.get_role_description()}",
            f"\nCurrent task: {task.get('description', 'No description provided')}",
        ]

        # Add relevant memory context
        if self.memory and 'query' in task:
            relevant_memories = self.recall(task['query'], top_k=3)
            if relevant_memories:
                context_parts.append("\nRelevant context from memory:")
                for memory in relevant_memories:
                    context_parts.append(f"- {memory}")

        return "\n".join(context_parts)

    @abstractmethod
    def get_role_description(self) -> str:
        """Get description of this agent's role

        Returns:
            Role description
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' model='{self.model_name}'>"
