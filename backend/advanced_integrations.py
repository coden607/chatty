#!/usr/bin/env python3
"""
CHATTY Advanced AI Integrations
External AI service integrations, specialized models, and advanced capabilities
"""

import os
import json
import time
import asyncio
import aiohttp
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
import base64
import hashlib
import hmac

from server import db, logger
from performance_optimizer import cache_manager

class OpenAIIntegration:
    """OpenAI API integration for advanced language processing"""

    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4-turbo-preview"
        self.backup_model = "gpt-3.5-turbo"
        self.session = None
        self.rate_limits = {
            'requests_per_minute': 50,
            'tokens_per_minute': 10000,
            'requests_per_day': 1000
        }
        self.usage_tracking = {
            'requests_today': 0,
            'tokens_used_today': 0,
            'last_reset': datetime.utcnow().date()
        }

    async def initialize(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def generate_text(self, prompt: str, max_tokens: int = 1000,
                          temperature: float = 0.7, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate text using OpenAI"""
        if not self.api_key:
            return {'error': 'OpenAI API key not configured'}

        await self.initialize()

        # Check rate limits
        if not self._check_rate_limits():
            return {'error': 'Rate limit exceeded'}

        messages = []
        if context:
            # Add context messages
            system_message = context.get('system_message', 'You are a helpful AI assistant.')
            messages.append({'role': 'system', 'content': system_message})

            # Add conversation history
            for msg in context.get('conversation', []):
                messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })

        messages.append({'role': 'user', 'content': prompt})

        payload = {
            'model': self.model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': 0.9,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0
        }

        try:
            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    usage = data.get('usage', {})

                    # Track usage
                    self._update_usage_tracking(usage)

                    return {
                        'text': data['choices'][0]['message']['content'],
                        'usage': usage,
                        'model': data.get('model'),
                        'finish_reason': data['choices'][0].get('finish_reason')
                    }
                elif response.status == 429:
                    # Rate limited - try backup model
                    return await self._fallback_generation(prompt, max_tokens, temperature)
                else:
                    error_data = await response.json()
                    return {'error': error_data.get('error', {}).get('message', 'API error')}

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return {'error': str(e)}

    async def _fallback_generation(self, prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Fallback text generation using backup model"""
        if not self.api_key:
            return {'error': 'OpenAI API key not configured'}

        payload = {
            'model': self.backup_model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens,
            'temperature': temperature
        }

        try:
            async with self.session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    usage = data.get('usage', {})
                    self._update_usage_tracking(usage)

                    return {
                        'text': data['choices'][0]['message']['content'],
                        'usage': usage,
                        'model': data.get('model'),
                        'fallback_used': True
                    }
                else:
                    return {'error': 'Both primary and backup models failed'}
        except Exception as e:
            return {'error': f'Fallback generation failed: {str(e)}'}

    def _check_rate_limits(self) -> bool:
        """Check if within rate limits"""
        current_date = datetime.utcnow().date()

        # Reset daily counters
        if self.usage_tracking['last_reset'] != current_date:
            self.usage_tracking['requests_today'] = 0
            self.usage_tracking['tokens_used_today'] = 0
            self.usage_tracking['last_reset'] = current_date

        # Check limits
        if self.usage_tracking['requests_today'] >= self.rate_limits['requests_per_day']:
            return False

        return True

    def _update_usage_tracking(self, usage: Dict[str, Any]):
        """Update usage tracking"""
        tokens_used = usage.get('total_tokens', 0)
        self.usage_tracking['requests_today'] += 1
        self.usage_tracking['tokens_used_today'] += tokens_used

class AnthropicIntegration:
    """Anthropic Claude API integration"""

    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-opus-20240229"
        self.backup_model = "claude-3-sonnet-20240229"

    async def generate_text(self, prompt: str, max_tokens: int = 1000,
                          temperature: float = 0.7) -> Dict[str, Any]:
        """Generate text using Claude"""
        if not self.api_key:
            return {'error': 'Anthropic API key not configured'}

        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        payload = {
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': [{'role': 'user', 'content': prompt}]
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/messages", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'text': data['content'][0]['text'],
                            'usage': {
                                'input_tokens': data.get('usage', {}).get('input_tokens', 0),
                                'output_tokens': data.get('usage', {}).get('output_tokens', 0)
                            },
                            'model': data.get('model'),
                            'stop_reason': data.get('stop_reason')
                        }
                    else:
                        error_data = await response.json()
                        return {'error': error_data.get('error', {}).get('message', 'API error')}
            except Exception as e:
                logger.error(f"Anthropic API error: {str(e)}")
                return {'error': str(e)}

class HuggingFaceIntegration:
    """Hugging Face model integration"""

    def __init__(self):
        self.api_key = os.environ.get('HUGGINGFACE_API_KEY')
        self.base_url = "https://api-inference.huggingface.co/models"

    async def generate_text(self, prompt: str, model: str = "microsoft/DialoGPT-medium",
                          max_length: int = 100) -> Dict[str, Any]:
        """Generate text using Hugging Face models"""
        if not self.api_key:
            return {'error': 'Hugging Face API key not configured'}

        headers = {'Authorization': f'Bearer {self.api_key}'}

        payload = {
            'inputs': prompt,
            'parameters': {
                'max_length': max_length,
                'temperature': 0.7,
                'do_sample': True,
                'pad_token_id': 50256
            }
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/{model}", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            generated_text = data[0].get('generated_text', '')
                            # Remove the original prompt from response
                            if generated_text.startswith(prompt):
                                generated_text = generated_text[len(prompt):].strip()

                            return {
                                'text': generated_text,
                                'model': model,
                                'prompt_length': len(prompt)
                            }
                        else:
                            return {'error': 'Unexpected response format'}
                    else:
                        error_data = await response.json()
                        return {'error': error_data.get('error', 'API error')}
            except Exception as e:
                logger.error(f"Hugging Face API error: {str(e)}")
                return {'error': str(e)}

class WebSearchIntegration:
    """Web search and information retrieval integration"""

    def __init__(self):
        self.search_apis = {
            'serpapi': os.environ.get('SERPAPI_KEY'),
            'google_custom_search': os.environ.get('GOOGLE_SEARCH_API_KEY'),
            'bing': os.environ.get('BING_SEARCH_API_KEY')
        }
        self.cache_ttl = 3600  # 1 hour

    async def search(self, query: str, num_results: int = 10,
                   search_engine: str = 'auto') -> Dict[str, Any]:
        """Perform web search"""
        # Check cache first
        cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            return cached_result

        # Determine which API to use
        api_choice = self._select_search_api(search_engine)

        if api_choice == 'serpapi':
            result = await self._search_serpapi(query, num_results)
        elif api_choice == 'google':
            result = await self._search_google(query, num_results)
        elif api_choice == 'bing':
            result = await self._search_bing(query, num_results)
        else:
            result = {'error': 'No search API available'}

        # Cache result
        if 'error' not in result:
            cache_manager.set(cache_key, result, self.cache_ttl)

        return result

    def _select_search_api(self, preference: str) -> str:
        """Select which search API to use"""
        if preference == 'serpapi' and self.search_apis['serpapi']:
            return 'serpapi'
        elif preference == 'google' and self.search_apis['google_custom_search']:
            return 'google'
        elif preference == 'bing' and self.search_apis['bing']:
            return 'bing'

        # Auto-select available API
        for api_name, api_key in self.search_apis.items():
            if api_key:
                if api_name == 'serpapi':
                    return 'serpapi'
                elif api_name == 'google_custom_search':
                    return 'google'
                elif api_name == 'bing':
                    return 'bing'

        return None

    async def _search_serpapi(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using SerpAPI"""
        api_key = self.search_apis['serpapi']
        if not api_key:
            return {'error': 'SerpAPI key not configured'}

        params = {
            'q': query,
            'num': num_results,
            'api_key': api_key
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://serpapi.com/search.json', params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        # Extract organic results
                        for result in data.get('organic_results', [])[:num_results]:
                            results.append({
                                'title': result.get('title', ''),
                                'link': result.get('link', ''),
                                'snippet': result.get('snippet', ''),
                                'display_link': result.get('displayed_link', '')
                            })

                        return {
                            'query': query,
                            'total_results': len(results),
                            'results': results,
                            'search_engine': 'serpapi'
                        }
                    else:
                        return {'error': f'SerpAPI returned status {response.status}'}
            except Exception as e:
                return {'error': f'SerpAPI search failed: {str(e)}'}

    async def _search_google(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using Google Custom Search API"""
        api_key = self.search_apis['google_custom_search']
        search_engine_id = os.environ.get('GOOGLE_SEARCH_ENGINE_ID')

        if not api_key or not search_engine_id:
            return {'error': 'Google Custom Search API not configured'}

        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': query,
            'num': min(num_results, 10)  # Google limits to 10
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('https://www.googleapis.com/customsearch/v1', params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        for item in data.get('items', [])[:num_results]:
                            results.append({
                                'title': item.get('title', ''),
                                'link': item.get('link', ''),
                                'snippet': item.get('snippet', ''),
                                'display_link': item.get('displayed_link', '')
                            })

                        return {
                            'query': query,
                            'total_results': len(results),
                            'results': results,
                            'search_engine': 'google'
                        }
                    else:
                        return {'error': f'Google search returned status {response.status}'}
            except Exception as e:
                return {'error': f'Google search failed: {str(e)}'}

    async def _search_bing(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using Bing Search API"""
        api_key = self.search_apis['bing']
        if not api_key:
            return {'error': 'Bing API key not configured'}

        headers = {'Ocp-Apim-Subscription-Key': api_key}
        params = {
            'q': query,
            'count': num_results,
            'responseFilter': 'Webpages'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get('https://api.bing.microsoft.com/v7.0/search', params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []

                        for webpage in data.get('webPages', {}).get('value', [])[:num_results]:
                            results.append({
                                'title': webpage.get('name', ''),
                                'link': webpage.get('url', ''),
                                'snippet': webpage.get('snippet', ''),
                                'display_link': webpage.get('displayUrl', '')
                            })

                        return {
                            'query': query,
                            'total_results': len(results),
                            'results': results,
                            'search_engine': 'bing'
                        }
                    else:
                        return {'error': f'Bing search returned status {response.status}'}
            except Exception as e:
                return {'error': f'Bing search failed: {str(e)}'}

class AdvancedAgentBehaviors:
    """Advanced agent behavior patterns and reasoning"""

    def __init__(self):
        self.behavior_patterns = self._load_behavior_patterns()
        self.reasoning_engines = {
            'logical': LogicalReasoning(),
            'probabilistic': ProbabilisticReasoning(),
            'case_based': CaseBasedReasoning()
        }

    def _load_behavior_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined behavior patterns"""
        return {
            'problem_solver': {
                'description': 'Systematic problem-solving approach',
                'steps': ['analyze', 'hypothesize', 'test', 'evaluate', 'iterate'],
                'success_criteria': ['solution_found', 'improvement_achieved']
            },
            'creative_thinker': {
                'description': 'Creative problem-solving and innovation',
                'steps': ['explore', 'brainstorm', 'prototype', 'refine', 'implement'],
                'success_criteria': ['novel_solution', 'innovation_created']
            },
            'analytical_expert': {
                'description': 'Data-driven analysis and decision making',
                'steps': ['gather_data', 'analyze_patterns', 'model_relationships', 'predict_outcomes', 'recommend_actions'],
                'success_criteria': ['insights_generated', 'predictions_accurate']
            },
            'collaborative_leader': {
                'description': 'Leading and coordinating team efforts',
                'steps': ['assess_team', 'define_goals', 'delegate_tasks', 'monitor_progress', 'provide_feedback'],
                'success_criteria': ['goals_achieved', 'team_satisfaction_high']
            }
        }

    async def execute_behavior_pattern(self, pattern_name: str, context: Dict[str, Any],
                                     agent_id: str) -> Dict[str, Any]:
        """Execute a behavior pattern"""
        if pattern_name not in self.behavior_patterns:
            return {'error': f'Unknown behavior pattern: {pattern_name}'}

        pattern = self.behavior_patterns[pattern_name]
        execution_log = []
        current_step = 0

        try:
            for step in pattern['steps']:
                execution_log.append(f"Starting step: {step}")
                current_step += 1

                # Execute step
                step_result = await self._execute_step(step, context, agent_id)
                execution_log.append(f"Step {step} result: {step_result.get('status', 'unknown')}")

                # Check for early termination
                if step_result.get('terminate', False):
                    break

                # Update context with step results
                context.update(step_result.get('context_updates', {}))

            # Evaluate success
            success = self._evaluate_pattern_success(pattern, execution_log, context)

            return {
                'pattern': pattern_name,
                'execution_log': execution_log,
                'success': success,
                'final_context': context,
                'steps_completed': current_step
            }

        except Exception as e:
            return {
                'pattern': pattern_name,
                'error': str(e),
                'execution_log': execution_log,
                'steps_completed': current_step
            }

    async def _execute_step(self, step: str, context: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Execute a single step in the behavior pattern"""
        # This would contain the actual step execution logic
        # For now, return a mock successful result

        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            'status': 'completed',
            'context_updates': {f'{step}_completed': True},
            'terminate': False
        }

    def _evaluate_pattern_success(self, pattern: Dict[str, Any], execution_log: List[str],
                                context: Dict[str, Any]) -> bool:
        """Evaluate if the behavior pattern execution was successful"""
        success_criteria = pattern.get('success_criteria', [])

        # Simple evaluation - check if critical success criteria are met
        success_score = 0
        for criterion in success_criteria:
            if context.get(f'{criterion}_achieved', False):
                success_score += 1

        # Consider successful if at least 50% of criteria met
        return success_score >= len(success_criteria) * 0.5

    async def apply_reasoning_engine(self, reasoning_type: str, problem: Dict[str, Any],
                                    agent_id: str) -> Dict[str, Any]:
        """Apply a specific reasoning engine to a problem"""
        if reasoning_type not in self.reasoning_engines:
            return {'error': f'Unknown reasoning engine: {reasoning_type}'}

        engine = self.reasoning_engines[reasoning_type]
        return await engine.reason(problem, agent_id)

class LogicalReasoning:
    """Logical reasoning engine"""

    async def reason(self, problem: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Apply logical reasoning to solve a problem"""
        premises = problem.get('premises', [])
        conclusion = problem.get('conclusion', '')

        # Simple logical inference
        reasoning_steps = []

        # Validate premises
        valid_premises = []
        for premise in premises:
            if self._validate_premise(premise):
                valid_premises.append(premise)
                reasoning_steps.append(f"Validated premise: {premise}")
            else:
                reasoning_steps.append(f"Invalid premise rejected: {premise}")

        # Draw logical conclusion
        if valid_premises and conclusion:
            inference_result = self._logical_inference(valid_premises, conclusion)
            reasoning_steps.append(f"Logical inference: {inference_result}")

            return {
                'reasoning_type': 'logical',
                'steps': reasoning_steps,
                'conclusion': inference_result,
                'confidence': 0.8
            }

        return {
            'reasoning_type': 'logical',
            'steps': reasoning_steps,
            'error': 'Insufficient premises for logical reasoning'
        }

    def _validate_premise(self, premise: str) -> bool:
        """Validate a logical premise"""
        # Simple validation - check for basic logical structure
        return len(premise.strip()) > 10 and not premise.startswith('INVALID:')

    def _logical_inference(self, premises: List[str], conclusion: str) -> str:
        """Perform logical inference"""
        # Simplified logical inference
        if any('all' in p.lower() and 'are' in p.lower() for p in premises):
            return f"Therefore: {conclusion}"
        else:
            return f"Based on premises: {conclusion}"

class ProbabilisticReasoning:
    """Probabilistic reasoning engine"""

    async def reason(self, problem: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Apply probabilistic reasoning"""
        hypotheses = problem.get('hypotheses', [])
        evidence = problem.get('evidence', [])

        probabilities = {}

        for hypothesis in hypotheses:
            prior_prob = self._calculate_prior_probability(hypothesis)
            likelihood = self._calculate_likelihood(hypothesis, evidence)

            # Bayes' theorem
            posterior_prob = (likelihood * prior_prob) / self._marginal_likelihood(evidence)

            probabilities[hypothesis] = {
                'prior': prior_prob,
                'likelihood': likelihood,
                'posterior': posterior_prob
            }

        # Sort by posterior probability
        sorted_hypotheses = sorted(probabilities.items(),
                                 key=lambda x: x[1]['posterior'], reverse=True)

        return {
            'reasoning_type': 'probabilistic',
            'probabilities': probabilities,
            'most_likely_hypothesis': sorted_hypotheses[0][0] if sorted_hypotheses else None,
            'confidence': sorted_hypotheses[0][1]['posterior'] if sorted_hypotheses else 0
        }

    def _calculate_prior_probability(self, hypothesis: str) -> float:
        """Calculate prior probability of hypothesis"""
        # Simplified - would use historical data
        return 0.5

    def _calculate_likelihood(self, hypothesis: str, evidence: List[str]) -> float:
        """Calculate likelihood of evidence given hypothesis"""
        # Simplified calculation
        supporting_evidence = sum(1 for e in evidence if e.lower() in hypothesis.lower())
        return supporting_evidence / len(evidence) if evidence else 0.5

    def _marginal_likelihood(self, evidence: List[str]) -> float:
        """Calculate marginal likelihood of evidence"""
        return 1.0  # Simplified

class CaseBasedReasoning:
    """Case-based reasoning engine"""

    def __init__(self):
        self.case_base = []  # Would store historical cases

    async def reason(self, problem: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Apply case-based reasoning"""
        current_problem = problem.get('description', '')

        # Find similar cases
        similar_cases = self._find_similar_cases(current_problem)

        if not similar_cases:
            return {
                'reasoning_type': 'case_based',
                'similar_cases': [],
                'solution': None,
                'adaptation_needed': True
            }

        # Adapt best matching case
        best_case = similar_cases[0]
        adapted_solution = self._adapt_solution(best_case, problem)

        return {
            'reasoning_type': 'case_based',
            'similar_cases': similar_cases[:3],  # Top 3
            'adapted_solution': adapted_solution,
            'similarity_score': best_case.get('similarity', 0),
            'confidence': min(best_case.get('similarity', 0) * 0.8, 0.9)
        }

    def _find_similar_cases(self, problem_description: str) -> List[Dict[str, Any]]:
        """Find cases similar to current problem"""
        # Simplified similarity matching
        # In practice, would use vector similarity or structured matching

        similar_cases = [
            {
                'case_id': 'case_001',
                'description': 'Similar problem solved before',
                'solution': 'Apply previous solution',
                'outcome': 'success',
                'similarity': 0.85
            }
        ]

        return similar_cases

    def _adapt_solution(self, case: Dict[str, Any], new_problem: Dict[str, Any]) -> str:
        """Adapt solution from similar case"""
        base_solution = case.get('solution', '')
        # Simple adaptation logic
        return f"Adapted: {base_solution}"

# Global instances
openai_integration = OpenAIIntegration()
anthropic_integration = AnthropicIntegration()
huggingface_integration = HuggingFaceIntegration()
web_search_integration = WebSearchIntegration()
advanced_behaviors = AdvancedAgentBehaviors()
