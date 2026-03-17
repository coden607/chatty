#!/usr/bin/env python3
"""
CHATTY Pydantic AI Enhanced Integration
Type-safe structured outputs with validation and dependency injection
Latest Pydantic AI v1 features for reliable AI responses
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


# Structured output models for common AI tasks
class LeadInfo(BaseModel):
    """Structured lead information"""
    name: str = Field(description="Contact person's full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    company: Optional[str] = Field(None, description="Company or organization name")
    title: Optional[str] = Field(None, description="Job title or role")
    industry: Optional[str] = Field(None, description="Industry sector")
    source: str = Field(description="How this lead was discovered")
    notes: Optional[str] = Field(None, description="Additional relevant information")
    priority: int = Field(default=3, ge=1, le=5, description="Priority score 1-5")


class ContentPiece(BaseModel):
    """Structured content output"""
    title: str = Field(description="Content title")
    content_type: str = Field(description="Type: blog, social, email, etc.")
    target_audience: str = Field(description="Intended audience")
    key_points: List[str] = Field(default_factory=list, description="Main points covered")
    seo_keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    content: str = Field(description="The actual content")
    call_to_action: Optional[str] = Field(None, description="Call to action")
    word_count: int = Field(description="Approximate word count")


class AnalysisResult(BaseModel):
    """Structured analysis output"""
    summary: str = Field(description="Executive summary")
    key_findings: List[str] = Field(default_factory=list, description="Key findings")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    risks: List[str] = Field(default_factory=list, description="Potential risks or concerns")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in analysis")
    data_sources: List[str] = Field(default_factory=list, description="Sources analyzed")


class TaskPlan(BaseModel):
    """Structured task execution plan"""
    objective: str = Field(description="Main objective")
    steps: List[str] = Field(description="Sequential steps to complete")
    estimated_time: str = Field(description="Estimated time to complete")
    resources_needed: List[str] = Field(default_factory=list, description="Required resources")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    success_criteria: List[str] = Field(description="How to measure success")


class EmailDraft(BaseModel):
    """Structured email output"""
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    tone: str = Field(description="Tone: professional, friendly, urgent, etc.")
    personalization_notes: Optional[str] = Field(None, description="Personalization suggestions")
    follow_up_suggestions: List[str] = Field(default_factory=list, description="Follow-up email ideas")


class SentimentAnalysis(BaseModel):
    """Structured sentiment analysis"""
    overall_sentiment: str = Field(description="positive, negative, neutral, mixed")
    sentiment_score: float = Field(ge=-1.0, le=1.0, description="-1 (negative) to 1 (positive)")
    emotions: Dict[str, float] = Field(default_factory=dict, description="Detected emotions with scores")
    key_phrases: List[str] = Field(default_factory=list, description="Important phrases")
    topics: List[str] = Field(default_factory=list, description="Detected topics")
    urgency_level: int = Field(ge=1, le=5, description="Urgency level 1-5")


class CodeReview(BaseModel):
    """Structured code review output"""
    overall_quality: int = Field(ge=1, le=10, description="Overall quality score 1-10")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Code issues found")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    security_concerns: List[str] = Field(default_factory=list, description="Security issues")
    performance_notes: List[str] = Field(default_factory=list, description="Performance considerations")
    documentation_status: str = Field(description="adequate, needs_improvement, missing")


class StructuredAIClient:
    """
    Client for generating structured AI outputs using Pydantic models
    Ensures type safety and validation
    """
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        
    async def generate_structured(
        self,
        prompt: str,
        output_model: Type[T],
        system_prompt: str = None,
        context: Dict[str, Any] = None
    ) -> T:
        """
        Generate structured output validated against Pydantic model
        
        Args:
            prompt: The task/prompt for the AI
            output_model: Pydantic model class for output structure
            system_prompt: Optional system prompt
            context: Optional context data
            
        Returns:
            Validated instance of output_model
        """
        from CHATTY_MODEL_ROUTER import router
        
        # Build schema description
        schema_desc = self._build_schema_description(output_model)
        
        # Build full prompt
        full_prompt = f"""{prompt}

You must respond with a valid JSON object that matches this schema:
{schema_desc}

Requirements:
- Response must be valid JSON
- Include ALL required fields
- Use appropriate types (string, number, boolean, array, object)
- Do not include markdown formatting

Respond with ONLY the JSON object."""

        if context:
            full_prompt += f"\n\nCONTEXT:\n{json.dumps(context, indent=2, default=str)}"
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await router.generate(
                    prompt=full_prompt,
                    system_prompt=system_prompt or "You always respond with valid, well-formed JSON."
                )
                
                # Extract JSON from response
                json_str = self._extract_json(response)
                
                # Parse and validate
                data = json.loads(json_str)
                validated = output_model.model_validate(data)
                
                logger.info(f"✅ Generated structured output: {output_model.__name__}")
                return validated
                
            except (json.JSONDecodeError, ValidationError) as e:
                last_error = e
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                continue
            except Exception as e:
                last_error = e
                logger.error(f"❌ Unexpected error: {e}")
                raise
        
        # All retries failed
        logger.error(f"❌ Failed to generate valid output after {self.max_retries} attempts")
        raise ValueError(f"Could not generate valid {output_model.__name__}: {last_error}")
    
    def _build_schema_description(self, model: Type[BaseModel]) -> str:
        """Build human-readable schema description from Pydantic model"""
        lines = ["{"]
        
        for name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            description = field_info.description or ""
            required = field_info.is_required()
            
            type_str = str(field_type).replace("<class '", "").replace("'>", "")
            
            line = f'  "{name}": {type_str}'
            if description:
                line += f'  // {description}'
            if not required:
                line += ' (optional)'
            
            lines.append(line)
        
        lines.append("}")
        return "\n".join(lines)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text response"""
        # Try code blocks first
        if "```json" in text:
            return text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            return text.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        
        return text.strip()


# Specialized AI functions using structured outputs
class PydanticAIFunctions:
    """High-level AI functions with guaranteed structured outputs"""
    
    def __init__(self):
        self.client = StructuredAIClient()
    
    async def extract_leads(self, text: str, source: str = "unknown") -> List[LeadInfo]:
        """Extract structured lead information from text"""
        
        class LeadList(BaseModel):
            leads: List[LeadInfo] = Field(description="List of extracted leads")
        
        result = await self.client.generate_structured(
            prompt=f"Extract all potential business leads from this text:\n\n{text}",
            output_model=LeadList,
            system_prompt="You are a lead extraction specialist. Identify all potential business contacts with complete information.",
            context={"source": source}
        )
        
        return result.leads
    
    async def create_content(
        self,
        topic: str,
        content_type: str,
        target_audience: str,
        word_count: int = 500
    ) -> ContentPiece:
        """Create structured content"""
        return await self.client.generate_structured(
            prompt=f"Create a {content_type} about '{topic}' for {target_audience}. Target length: {word_count} words.",
            output_model=ContentPiece,
            system_prompt="You are a professional content creator. Create engaging, SEO-optimized content.",
            context={"requested_word_count": word_count}
        )
    
    async def analyze_market(
        self,
        industry: str,
        focus_areas: List[str] = None
    ) -> AnalysisResult:
        """Generate market analysis"""
        return await self.client.generate_structured(
            prompt=f"Provide a comprehensive market analysis for the {industry} industry.",
            output_model=AnalysisResult,
            system_prompt="You are a market research analyst. Provide data-driven insights and actionable recommendations.",
            context={"focus_areas": focus_areas or ["market_size", "competition", "trends"]}
        )
    
    async def plan_task(
        self,
        objective: str,
        constraints: List[str] = None
    ) -> TaskPlan:
        """Create a task execution plan"""
        return await self.client.generate_structured(
            prompt=f"Create a detailed plan to achieve this objective: {objective}",
            output_model=TaskPlan,
            system_prompt="You are a project planning expert. Create clear, actionable plans with realistic timelines.",
            context={"constraints": constraints or []}
        )
    
    async def draft_email(
        self,
        purpose: str,
        recipient_info: Dict[str, str],
        tone: str = "professional"
    ) -> EmailDraft:
        """Draft a structured email"""
        return await self.client.generate_structured(
            prompt=f"Draft an email for this purpose: {purpose}",
            output_model=EmailDraft,
            system_prompt=f"You are an expert email copywriter. Write compelling, {tone} emails.",
            context={"recipient": recipient_info, "tone": tone}
        )
    
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """Analyze sentiment of text"""
        return await self.client.generate_structured(
            prompt=f"Analyze the sentiment and emotional tone of this text:\n\n{text}",
            output_model=SentimentAnalysis,
            system_prompt="You are a sentiment analysis expert. Provide detailed emotional and tonal analysis."
        )
    
    async def review_code(self, code: str, language: str = "python") -> CodeReview:
        """Review code quality"""
        return await self.client.generate_structured(
            prompt=f"Review this {language} code:\n\n```{language}\n{code}\n```",
            output_model=CodeReview,
            system_prompt="You are a senior code reviewer. Identify issues, suggest improvements, and assess quality."
        )


# Dependency injection container for AI operations
class DependencyContainer:
    """
    Type-safe dependency injection for AI operations
    Provides runtime context like DB connections, API clients, etc.
    """
    
    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
    
    def register(self, name: str, dependency: Any):
        """Register a dependency"""
        self._dependencies[name] = dependency
    
    def get(self, name: str) -> Any:
        """Get a dependency"""
        return self._dependencies.get(name)
    
    def has(self, name: str) -> bool:
        """Check if dependency exists"""
        return name in self._dependencies


# Global instances
_structured_client: Optional[StructuredAIClient] = None
_pydantic_functions: Optional[PydanticAIFunctions] = None
_dependency_container: Optional[DependencyContainer] = None


def get_structured_client() -> StructuredAIClient:
    """Get global structured AI client"""
    global _structured_client
    if _structured_client is None:
        _structured_client = StructuredAIClient()
    return _structured_client


def get_pydantic_functions() -> PydanticAIFunctions:
    """Get global Pydantic AI functions"""
    global _pydantic_functions
    if _pydantic_functions is None:
        _pydantic_functions = PydanticAIFunctions()
    return _pydantic_functions


def get_dependency_container() -> DependencyContainer:
    """Get global dependency container"""
    global _dependency_container
    if _dependency_container is None:
        _dependency_container = DependencyContainer()
    return _dependency_container


if __name__ == "__main__":
    async def test():
        print("🧪 Testing Pydantic AI Enhanced Integration...")
        
        functions = get_pydantic_functions()
        
        # Test content creation
        print("\n1. Testing content creation...")
        content = await functions.create_content(
            topic="AI in Healthcare",
            content_type="blog_post",
            target_audience="healthcare executives",
            word_count=300
        )
        print(f"✅ Created: {content.title}")
        print(f"   Type: {content.content_type}")
        print(f"   Keywords: {', '.join(content.seo_keywords[:3])}")
        
        # Test sentiment analysis
        print("\n2. Testing sentiment analysis...")
        sentiment = await functions.analyze_sentiment(
            "This product exceeded my expectations! The quality is outstanding and customer service was very helpful."
        )
        print(f"✅ Sentiment: {sentiment.overall_sentiment} ({sentiment.sentiment_score:.2f})")
        print(f"   Emotions: {list(sentiment.emotions.keys())[:3]}")
        
        # Test task planning
        print("\n3. Testing task planning...")
        plan = await functions.plan_task(
            objective="Launch a new SaaS product in 3 months",
            constraints=["Budget: $50,000", "Team: 5 people", "Remote team"]
        )
        print(f"✅ Plan created: {plan.objective}")
        print(f"   Steps: {len(plan.steps)}")
        print(f"   Time estimate: {plan.estimated_time}")
        
        print("\n✅ Pydantic AI test complete")
    
    asyncio.run(test())
