#!/usr/bin/env python3
"""
CHATTY Unified Model Router
Automatic failover between AI providers with intelligent task routing
No more manual API key management - handles everything automatically
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=True)  # secrets always win

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    """Supported AI providers"""
    XAI_GROK = "xai_grok"
    OPENROUTER = "openrouter"
    COHERE = "cohere"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    NVIDIA = "nvidia"  # Free Kimi 2.5 via NVIDIA Build API


class TaskType(Enum):
    """Types of tasks for optimal model selection"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CONTENT_CREATION = "content_creation"
    ANALYSIS = "analysis"
    CHAT = "chat"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    REASONING = "reasoning"
    CREATIVE = "creative"


@dataclass
class ProviderStatus:
    """Status tracking for each provider"""
    provider: ModelProvider
    is_available: bool = True
    last_error: Optional[str] = None
    last_used: Optional[datetime] = None
    success_count: int = 0
    error_count: int = 0
    average_latency: float = 0.0
    consecutive_failures: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_reset_time: Optional[datetime] = None


@dataclass
class GenerationResult:
    """Result from a generation attempt"""
    success: bool
    content: str = ""
    provider_used: Optional[ModelProvider] = None
    model_used: Optional[str] = None
    latency_ms: float = 0.0
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    fallback_used: bool = False
    confidence: float = 0.0


class ModelRouter:
    """
    Unified Model Router for CHATTY
    
    Features:
    - Automatic failover between providers
    - Intelligent task routing (best model for the job)
    - Circuit breaker pattern for failing providers
    - Health monitoring and metrics
    - Confidence scoring for outputs
    """
    
    # Provider priority by task type
    # NOTE: Cloud providers only in default paths; Ollama available but CPU-only (slow)
    _CLOUD_PRIORITY = [
        ModelProvider.NVIDIA,
        ModelProvider.ANTHROPIC,
        ModelProvider.OPENAI,
        ModelProvider.XAI_GROK,
        ModelProvider.OPENROUTER,
        ModelProvider.COHERE,
    ]
    TASK_PROVIDER_PRIORITY = {
        TaskType.CODE_GENERATION: _CLOUD_PRIORITY,
        TaskType.CODE_REVIEW: _CLOUD_PRIORITY,
        TaskType.CONTENT_CREATION: _CLOUD_PRIORITY,
        TaskType.ANALYSIS: _CLOUD_PRIORITY,
        TaskType.CHAT: _CLOUD_PRIORITY,
        TaskType.REASONING: _CLOUD_PRIORITY,
        TaskType.CREATIVE: _CLOUD_PRIORITY,
        TaskType.SUMMARIZATION: _CLOUD_PRIORITY,
        TaskType.TRANSLATION: _CLOUD_PRIORITY,
    }
    
    # Model mappings for each provider
    PROVIDER_MODELS = {
        ModelProvider.XAI_GROK: {
            "default": "grok-3",
            "fast": "grok-2",
            "vision": "grok-3-vision",
        },
        ModelProvider.OPENROUTER: {
            "default": "meta-llama/llama-3.2-3b-instruct:free",
            "fast": "meta-llama/llama-3.2-3b-instruct:free",
            "powerful": "anthropic/claude-3.5-sonnet",
            "cheap": "meta-llama/llama-3.2-3b-instruct:free",
        },
        ModelProvider.COHERE: {
            "default": "command-r",
            "fast": "command-light",
            "powerful": "command-r-plus",
        },
        ModelProvider.OPENAI: {
            "default": "gpt-4o-mini",
            "fast": "gpt-4o-mini",
            "powerful": "gpt-4o",
        },
        ModelProvider.ANTHROPIC: {
            "default": "claude-3-5-sonnet-20241022",
            "powerful": "claude-3-opus-20240229",
            "fast": "claude-3-haiku-20240307",
        },
        ModelProvider.OLLAMA: {
            "default": "llama3.2",
            "code": "codellama",
        },
        ModelProvider.NVIDIA: {
            "default": "moonshotai/kimi-k2.5",  # FREE via NVIDIA Build API
            "fast": "moonshotai/kimi-k2.5",
            "powerful": "moonshotai/kimi-k2.5",
        },
    }
    
    def __init__(self):
        self.status: Dict[ModelProvider, ProviderStatus] = {}
        self.circuit_breaker_threshold = 5  # Open after 5 consecutive failures
        self.circuit_breaker_timeout = 300  # Reset after 5 minutes
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Initialize provider status
        for provider in ModelProvider:
            self.status[provider] = ProviderStatus(provider=provider)
        
        # Load API keys
        self._load_api_keys()
        
        # Initialize clients (lazy loading)
        self.clients: Dict[ModelProvider, Any] = {}
        
        logger.info("🧠 Model Router initialized with auto-failover")
    
    def _load_api_keys(self):
        """Load all API keys from environment"""
        self.api_keys = {
            ModelProvider.XAI_GROK: [
                os.getenv('XAI_API_KEY'),
                os.getenv('XAI_API_KEY_2'),
                os.getenv('XAI_API_KEY_3'),
                os.getenv('XAI_API_KEY_4'),
            ],
            ModelProvider.OPENROUTER: [
                os.getenv('OPENROUTER_API_KEY'),
                os.getenv('OPENROUTER_API_KEY_2'),
                os.getenv('OPENROUTER_API_KEY_3'),
                os.getenv('OPENROUTER_API_KEY_4'),
                os.getenv('OPENROUTER_API_KEY_5'),
            ],
            ModelProvider.COHERE: [os.getenv('COHERE_API_KEY')],
            ModelProvider.OPENAI: [os.getenv('OPENAI_API_KEY')],
            ModelProvider.ANTHROPIC: [os.getenv('ANTHROPIC_API_KEY')],
            ModelProvider.OLLAMA: ["local"],  # No key needed
            ModelProvider.NVIDIA: [os.getenv("NVIDIA_API_KEY") or os.getenv("NGC_API_KEY")],  # Real key required
        }
        
        # Filter out None values
        for provider, keys in self.api_keys.items():
            self.api_keys[provider] = [k for k in keys if k]
    
    def _get_client(self, provider: ModelProvider):
        """Get or create client for provider (lazy initialization)"""
        if provider in self.clients:
            return self.clients[provider]
        
        # Import libraries only when needed
        if provider == ModelProvider.XAI_GROK:
            try:
                from langchain_openai import ChatOpenAI
                keys = self.api_keys[provider]
                if keys:
                    client = ChatOpenAI(
                        model=self.PROVIDER_MODELS[provider]["default"],
                        openai_api_key=keys[0],
                        openai_api_base="https://api.x.ai/v1",
                        temperature=0.7,
                        timeout=60,
                    )
                    self.clients[provider] = client
                    return client
            except Exception as e:
                logger.error(f"Failed to initialize xAI client: {e}")
                return None
        
        elif provider == ModelProvider.OPENROUTER:
            try:
                from langchain_openai import ChatOpenAI
                keys = self.api_keys[provider]
                if keys:
                    client = ChatOpenAI(
                        model=self.PROVIDER_MODELS[provider]["default"],
                        openai_api_key=keys[0],
                        openai_api_base="https://openrouter.ai/api/v1",
                        temperature=0.7,
                        timeout=60,
                        default_headers={
                            "HTTP-Referer": "https://chatty.ai",
                            "X-Title": "CHATTY AI",
                        },
                    )
                    self.clients[provider] = client
                    return client
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter client: {e}")
                return None
        
        elif provider == ModelProvider.COHERE:
            try:
                from langchain_cohere import ChatCohere
                keys = self.api_keys[provider]
                if keys and keys[0]:
                    client = ChatCohere(
                        model=self.PROVIDER_MODELS[provider]["default"],
                        cohere_api_key=keys[0],
                        temperature=0.7,
                    )
                    self.clients[provider] = client
                    return client
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {e}")
                return None
        
        elif provider == ModelProvider.OPENAI:
            try:
                from langchain_openai import ChatOpenAI
                keys = self.api_keys[provider]
                if keys and keys[0]:
                    client = ChatOpenAI(
                        model=self.PROVIDER_MODELS[provider]["default"],
                        openai_api_key=keys[0],
                        temperature=0.7,
                    )
                    self.clients[provider] = client
                    return client
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                return None
        
        elif provider == ModelProvider.ANTHROPIC:
            try:
                from langchain_anthropic import ChatAnthropic
                keys = self.api_keys[provider]
                if keys and keys[0]:
                    client = ChatAnthropic(
                        model=self.PROVIDER_MODELS[provider]["default"],
                        anthropic_api_key=keys[0],
                        temperature=0.7,
                    )
                    self.clients[provider] = client
                    return client
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                return None
        
        elif provider == ModelProvider.OLLAMA:
            try:
                from langchain_ollama import ChatOllama
                client = ChatOllama(
                    model=self.PROVIDER_MODELS[provider]["default"],
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    timeout=30,
                )
                self.clients[provider] = client
                return client
            except Exception as e:
                logger.error(f"Failed to initialize Ollama client: {e}")
                return None
        
        elif provider == ModelProvider.NVIDIA:
            try:
                from langchain_openai import ChatOpenAI
                keys = self.api_keys[provider]
                api_key = keys[0] if keys and keys[0] != "free" else None
                
                # NVIDIA Build API - hosts Kimi K2.5 for free
                client = ChatOpenAI(
                    model=self.PROVIDER_MODELS[provider]["default"],
                    openai_api_key=api_key or "not-needed",
                    openai_api_base="https://integrate.api.nvidia.com/v1",
                    temperature=0.7,
                    timeout=120,
                    default_headers={
                        "Authorization": f"Bearer {api_key}",
                    } if api_key else {},
                )
                self.clients[provider] = client
                logger.info("✅ NVIDIA Build API (Kimi 2.5) client initialized")
                return client
            except Exception as e:
                logger.error(f"Failed to initialize NVIDIA client: {e}")
                return None
        
        return None
    
    def _check_circuit_breaker(self, provider: ModelProvider) -> bool:
        """Check if circuit breaker allows requests to this provider"""
        status = self.status[provider]
        
        if not status.circuit_breaker_open:
            return True
        
        # Check if it's time to reset
        if status.circuit_breaker_reset_time and datetime.now() > status.circuit_breaker_reset_time:
            status.circuit_breaker_open = False
            status.consecutive_failures = 0
            logger.info(f"🔓 Circuit breaker reset for {provider.value}")
            return True
        
        return False
    
    def _record_success(self, provider: ModelProvider, latency: float):
        """Record a successful request"""
        status = self.status[provider]
        status.success_count += 1
        status.consecutive_failures = 0
        status.circuit_breaker_open = False
        status.last_used = datetime.now()
        
        # Update average latency
        if status.average_latency == 0:
            status.average_latency = latency
        else:
            status.average_latency = (status.average_latency * 0.9) + (latency * 0.1)
    
    def _record_failure(self, provider: ModelProvider, error: str):
        """Record a failed request"""
        status = self.status[provider]
        status.error_count += 1
        status.consecutive_failures += 1
        status.last_error = error
        status.last_used = datetime.now()
        
        # Check if we should open circuit breaker
        if status.consecutive_failures >= self.circuit_breaker_threshold:
            status.circuit_breaker_open = True
            status.circuit_breaker_reset_time = datetime.now() + timedelta(seconds=self.circuit_breaker_timeout)
            logger.warning(f"🔴 Circuit breaker opened for {provider.value} - {error}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        task_type: TaskType = TaskType.CHAT,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        model_preference: str = "default",
        require_confidence: bool = True,
    ) -> GenerationResult:
        """
        Generate content with automatic failover
        
        Args:
            prompt: The user prompt
            system_prompt: System instructions
            task_type: Type of task for optimal model selection
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            model_preference: "default", "fast", "powerful", "cheap"
            require_confidence: Whether to include confidence scoring
        
        Returns:
            GenerationResult with success status and metadata
        """
        # Get priority list for this task type
        priority_list = self.TASK_PROVIDER_PRIORITY.get(task_type, [
            ModelProvider.XAI_GROK,
            ModelProvider.OPENROUTER,
            ModelProvider.COHERE,
        ])
        
        # Try each provider in priority order
        last_error = None
        fallback_used = False
        
        for provider in priority_list:
            # Skip if circuit breaker is open
            if not self._check_circuit_breaker(provider):
                logger.debug(f"⏭️ Skipping {provider.value} - circuit breaker open")
                fallback_used = True
                continue
            
            # Skip if no API keys
            if not self.api_keys.get(provider):
                logger.debug(f"⏭️ Skipping {provider.value} - no API keys")
                fallback_used = True
                continue
            
            # Try generation with retries
            for attempt in range(self.max_retries):
                start_time = time.time()
                
                try:
                    result = await self._try_generate(
                        provider=provider,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        model_preference=model_preference,
                    )
                    
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    self._record_success(provider, latency)
                    
                    # Calculate confidence
                    confidence = self._calculate_confidence(result, provider)
                    
                    logger.info(f"✅ Generated with {provider.value} in {latency:.0f}ms")
                    
                    return GenerationResult(
                        success=True,
                        content=result,
                        provider_used=provider,
                        model_used=self._get_model_name(provider, model_preference),
                        latency_ms=latency,
                        fallback_used=fallback_used,
                        confidence=confidence,
                    )
                    
                except Exception as e:
                    latency = (time.time() - start_time) * 1000
                    error_msg = str(e)
                    last_error = error_msg
                    
                    logger.warning(f"⚠️ {provider.value} attempt {attempt + 1} failed: {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                    else:
                        self._record_failure(provider, error_msg)
                        fallback_used = True
        
        # All providers failed
        logger.error(f"❌ All providers failed. Last error: {last_error}")
        return GenerationResult(
            success=False,
            content="",
            error=f"All providers failed. Last error: {last_error}",
            fallback_used=True,
            confidence=0.0,
        )
    
    async def _try_generate(
        self,
        provider: ModelProvider,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        temperature: float,
        model_preference: str,
    ) -> str:
        """Attempt generation with a specific provider"""
        client = self._get_client(provider)
        
        if not client:
            raise Exception(f"Client not available for {provider.value}")
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Ollama is local/free — no token limit binding needed
        if provider == ModelProvider.OLLAMA:
            response = await client.ainvoke(messages)
            return response.content

        # All OpenAI-compatible providers
        openai_compat = [
            ModelProvider.XAI_GROK,
            ModelProvider.OPENROUTER,
            ModelProvider.OPENAI,
            ModelProvider.NVIDIA,
            ModelProvider.ANTHROPIC,
            ModelProvider.COHERE,
        ]
        if provider in openai_compat:
            response = await client.bind(max_tokens=max_tokens).ainvoke(messages)
            return response.content

        raise Exception(f"Unknown provider: {provider.value}")
    
    def _get_model_name(self, provider: ModelProvider, preference: str) -> str:
        """Get the actual model name being used"""
        models = self.PROVIDER_MODELS.get(provider, {})
        return models.get(preference, models.get("default", "unknown"))
    
    def _calculate_confidence(self, content: str, provider: ModelProvider) -> float:
        """Calculate confidence score for generated content"""
        # Base confidence by provider reliability
        base_confidence = {
            ModelProvider.XAI_GROK: 0.92,
            ModelProvider.OPENROUTER: 0.90,
            ModelProvider.ANTHROPIC: 0.91,
            ModelProvider.OPENAI: 0.89,
            ModelProvider.COHERE: 0.85,
            ModelProvider.OLLAMA: 0.75,
            ModelProvider.NVIDIA: 0.88,  # Kimi 2.5 is high quality
        }.get(provider, 0.80)
        
        # Adjust based on content quality signals
        if not content or len(content) < 10:
            return 0.1
        
        # Check for hallucination indicators
        hallucination_indicators = [
            "I apologize, but I cannot",
            "I'm not sure",
            "I don't have information",
            "As an AI language model",
            "I cannot fulfill this request",
        ]
        
        for indicator in hallucination_indicators:
            if indicator.lower() in content.lower():
                base_confidence *= 0.7
        
        # Content length factor (very short or very long might be suspicious)
        content_len = len(content)
        if content_len < 50:
            base_confidence *= 0.9
        elif content_len > 10000:
            base_confidence *= 0.95
        
        return min(base_confidence, 1.0)
    
    def health_check(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        return {
            "timestamp": datetime.now().isoformat(),
            "providers": {
                provider.value: {
                    "available": status.is_available and not status.circuit_breaker_open,
                    "circuit_breaker_open": status.circuit_breaker_open,
                    "success_rate": self._calculate_success_rate(status),
                    "average_latency_ms": round(status.average_latency, 2),
                    "consecutive_failures": status.consecutive_failures,
                    "last_error": status.last_error,
                    "api_keys_configured": len(self.api_keys.get(provider, [])) > 0,
                }
                for provider, status in self.status.items()
            },
            "overall_health": self._calculate_overall_health(),
        }
    
    def _calculate_success_rate(self, status: ProviderStatus) -> float:
        """Calculate success rate for a provider"""
        total = status.success_count + status.error_count
        if total == 0:
            return 1.0  # Assume good if no data
        return status.success_count / total
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        available = sum(
            1 for s in self.status.values()
            if s.is_available and not s.circuit_breaker_open
        )
        total = len(self.status)
        
        if available == total:
            return "excellent"
        elif available >= total / 2:
            return "degraded"
        elif available > 0:
            return "critical"
        return "down"
    
    def get_best_provider_for_task(self, task_type: TaskType) -> Optional[ModelProvider]:
        """Get the best available provider for a specific task"""
        priority_list = self.TASK_PROVIDER_PRIORITY.get(task_type, [ModelProvider.XAI_GROK])
        
        for provider in priority_list:
            if self._check_circuit_breaker(provider) and self.api_keys.get(provider):
                return provider
        
        return None
    
    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: str = "",
        task_type: TaskType = TaskType.CHAT,
        max_concurrent: int = 5,
    ) -> List[GenerationResult]:
        """Generate multiple prompts with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(prompt: str) -> GenerationResult:
            async with semaphore:
                return await self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    task_type=task_type,
                )
        
        tasks = [generate_with_semaphore(p) for p in prompts]
        return await asyncio.gather(*tasks)


# Global router instance
router = ModelRouter()


# Convenience functions for common operations
async def generate_code(prompt: str, language: str = "python") -> GenerationResult:
    """Generate code with optimal model selection"""
    system = f"You are an expert {language} developer. Write clean, well-documented, production-ready code."
    return await router.generate(
        prompt=prompt,
        system_prompt=system,
        task_type=TaskType.CODE_GENERATION,
        temperature=0.3,  # Lower temperature for code
    )


async def review_code(code: str, language: str = "python") -> GenerationResult:
    """Review code for issues and improvements"""
    prompt = f"Review this {language} code for bugs, security issues, and improvements:\n\n```\n{code}\n```"
    system = "You are a senior code reviewer. Identify issues and suggest specific fixes."
    return await router.generate(
        prompt=prompt,
        system_prompt=system,
        task_type=TaskType.CODE_REVIEW,
        temperature=0.3,
    )


async def create_content(topic: str, format: str = "blog post") -> GenerationResult:
    """Create marketing content"""
    prompt = f"Write a compelling {format} about: {topic}"
    system = "You are an expert content marketer. Create engaging, SEO-optimized content."
    return await router.generate(
        prompt=prompt,
        system_prompt=system,
        task_type=TaskType.CONTENT_CREATION,
        temperature=0.8,
    )


async def analyze_data(data_description: str, question: str) -> GenerationResult:
    """Analyze data and answer questions"""
    prompt = f"Data: {data_description}\n\nQuestion: {question}"
    system = "You are a data analyst. Provide clear, data-backed insights."
    return await router.generate(
        prompt=prompt,
        system_prompt=system,
        task_type=TaskType.ANALYSIS,
        temperature=0.4,
    )


async def chat(message: str, context: str = "") -> GenerationResult:
    """General chat with context"""
    prompt = message
    if context:
        prompt = f"Context: {context}\n\nUser: {message}"
    return await router.generate(
        prompt=prompt,
        task_type=TaskType.CHAT,
        temperature=0.7,
    )


# Test function
async def test_router():
    """Test the model router"""
    print("🧪 Testing CHATTY Model Router")
    print("=" * 60)
    
    # Health check
    health = router.health_check()
    print(f"\n📊 Health Status: {health['overall_health']}")
    print("\nProvider Status:")
    for provider, status in health['providers'].items():
        available = "✅" if status['available'] else "❌"
        print(f"  {available} {provider}: {status['success_rate']*100:.0f}% success rate")
    
    # Test generation
    print("\n📝 Testing generation...")
    result = await router.generate(
        prompt="Say 'Hello from CHATTY Model Router' and tell me which model you are.",
        task_type=TaskType.CHAT,
    )
    
    if result.success:
        print(f"✅ Success! Used: {result.provider_used.value}")
        print(f"   Model: {result.model_used}")
        print(f"   Latency: {result.latency_ms:.0f}ms")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Response: {result.content[:100]}...")
    else:
        print(f"❌ Failed: {result.error}")
    
    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_router())
    else:
        # Print health check
        health = router.health_check()
        print(json.dumps(health, indent=2))
