#!/usr/bin/env python3
"""
Pydantic AI n8n Workflow Engine
Self-optimizing workflows with Pydantic validation and AI-driven task routing
"""

import os
import json
import time
import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from collections import defaultdict
import concurrent.futures
from dataclasses import dataclass, field
from enum import Enum

import requests
from pydantic import BaseModel, Field, validator, ValidationError
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.models.test import TestModel

from server import db, Agent, Task, logger
from learning_system import memory_system, adaptive_learning
from openclaw_integration import MultiLLMRouter

class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

class WorkflowPriority(str, Enum):
    """Workflow priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PydanticWorkflow(BaseModel):
    """Pydantic model for workflow validation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    version: str = Field(default="1.0.0")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING)
    priority: WorkflowPriority = Field(default=WorkflowPriority.MEDIUM)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Workflow structure
    tasks: List[Dict[str, Any]] = Field(...)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution settings
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=3600, ge=60, le=86400)  # 1 hour to 24 hours
    parallel_execution: bool = Field(default=False)
    error_handling: str = Field(default="fail_fast")  # fail_fast, continue_on_error, retry_all
    
    # AI optimization settings
    auto_optimize: bool = Field(default=True)
    learning_enabled: bool = Field(default=True)
    performance_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    @validator('tasks')
    def validate_tasks(cls, v):
        if not v:
            raise ValueError('Workflow must have at least one task')
        return v
    
    @validator('dependencies')
    def validate_dependencies(cls, v, values):
        task_ids = {task.get('id') for task in values.get('tasks', [])}
        for task_id, deps in v.items():
            if task_id not in task_ids:
                raise ValueError(f'Task {task_id} not found in tasks list')
            for dep in deps:
                if dep not in task_ids:
                    raise ValueError(f'Dependency {dep} not found in tasks list')
        return v

class TaskConfig(BaseModel):
    """Pydantic model for task configuration"""
    id: str = Field(...)
    name: str = Field(...)
    type: str = Field(...)  # http_request, function_call, conditional, delay, etc.
    config: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = Field(default=0, ge=0)
    timeout: int = Field(default=300, ge=10, le=3600)
    parallel: bool = Field(default=False)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    
    @validator('type')
    def validate_task_type(cls, v):
        valid_types = ['http_request', 'function_call', 'conditional', 'delay', 'data_transform', 'ai_task']
        if v not in valid_types:
            raise ValueError(f'Invalid task type: {v}')
        return v

class WorkflowExecution(BaseModel):
    """Pydantic model for workflow execution tracking"""
    workflow_id: str
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = Field(default=WorkflowStatus.RUNNING)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    tasks_executed: int = Field(default=0)
    tasks_completed: int = Field(default=0)
    tasks_failed: int = Field(default=0)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    error_details: List[Dict[str, Any]] = Field(default_factory=list)

class PydanticN8NEngine:
    """Pydantic AI n8n workflow engine with self-optimization"""
    
    def __init__(self):
        self.name = "Pydantic AI n8n Engine"
        self.workflows: Dict[str, PydanticWorkflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.task_registry: Dict[str, callable] = {}
        self.ai_optimizer = AIWorkflowOptimizer()
        self.performance_monitor = PerformanceMonitor()
        self.error_handler = ErrorHandler()
        
        # Execution state
        self.running_executions: Dict[str, asyncio.Task] = {}
        self.execution_queue = asyncio.Queue()
        
        # Configuration
        self.max_concurrent_workflows = 10
        self.auto_optimize_interval = 300  # 5 minutes
        
        # Initialize built-in tasks
        self._register_builtin_tasks()
    
    def register_workflow(self, workflow_data: Dict[str, Any]) -> PydanticWorkflow:
        """Register a new workflow with Pydantic validation"""
        try:
            workflow = PydanticWorkflow(**workflow_data)
            self.workflows[workflow.id] = workflow
            
            logger.info(f"✅ Registered workflow: {workflow.name} (ID: {workflow.id})")
            return workflow
            
        except ValidationError as e:
            logger.error(f"❌ Workflow validation failed: {e}")
            raise ValueError(f"Invalid workflow configuration: {e}")
    
    def register_task(self, task_id: str, task_function: callable):
        """Register a custom task function"""
        self.task_registry[task_id] = task_function
        logger.info(f"✅ Registered task: {task_id}")
    
    async def execute_workflow(self, workflow_id: str, inputs: Dict[str, Any] = None) -> WorkflowExecution:
        """Execute a workflow with AI-driven optimization"""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = self.workflows[workflow_id]
            
            # Create execution record
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                status=WorkflowStatus.RUNNING
            )
            self.executions[execution.execution_id] = execution
            
            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.updated_at = datetime.utcnow()
            
            logger.info(f"🚀 Starting workflow execution: {workflow.name}")
            
            # Execute workflow
            await self._execute_workflow_internal(workflow, execution, inputs or {})
            
            # Update execution status
            execution.completed_at = datetime.utcnow()
            execution.status = WorkflowStatus.COMPLETED
            
            # Update workflow status
            workflow.status = WorkflowStatus.COMPLETED
            workflow.updated_at = datetime.utcnow()
            
            # Performance monitoring
            await self.performance_monitor.record_execution(execution)
            
            # Auto-optimize if enabled
            if workflow.auto_optimize:
                await self.ai_optimizer.optimize_workflow(workflow, execution)
            
            logger.info(f"✅ Workflow completed: {workflow.name}")
            return execution
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {str(e)}")
            
            # Update execution status
            if 'execution' in locals():
                execution.status = WorkflowStatus.FAILED
                execution.completed_at = datetime.utcnow()
                execution.error_details.append({
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Update workflow status
            if 'workflow' in locals():
                workflow.status = WorkflowStatus.FAILED
                workflow.updated_at = datetime.utcnow()
            
            raise
    
    async def _execute_workflow_internal(self, workflow: PydanticWorkflow, execution: WorkflowExecution, inputs: Dict[str, Any]):
        """Internal workflow execution logic"""
        # Prepare execution context
        context = {
            'workflow': workflow,
            'execution': execution,
            'inputs': inputs,
            'outputs': {},
            'task_results': {},
            'execution_order': []
        }
        
        # Build execution graph
        execution_graph = self._build_execution_graph(workflow)
        
        # Execute tasks based on dependencies
        completed_tasks = set()
        pending_tasks = set(workflow.tasks)
        
        while pending_tasks:
            # Find tasks ready to execute
            ready_tasks = self._get_ready_tasks(pending_tasks, completed_tasks, execution.dependencies)
            
            if not ready_tasks:
                # Check for circular dependencies
                raise ValueError("Circular dependency detected in workflow")
            
            # Execute ready tasks
            for task in ready_tasks:
                try:
                    result = await self._execute_task(task, context)
                    context['task_results'][task['id']] = result
                    context['execution_order'].append(task['id'])
                    completed_tasks.add(task['id'])
                    pending_tasks.remove(task)
                    
                    execution.tasks_executed += 1
                    execution.tasks_completed += 1
                    
                    logger.info(f"✅ Task completed: {task['name']}")
                    
                except Exception as e:
                    execution.tasks_failed += 1
                    
                    if workflow.error_handling == 'fail_fast':
                        raise
                    elif workflow.error_handling == 'continue_on_error':
                        logger.warning(f"⚠️ Task failed but continuing: {task['name']} - {str(e)}")
                        context['task_results'][task['id']] = {'error': str(e)}
                        completed_tasks.add(task['id'])
                        pending_tasks.remove(task)
                    else:  # retry_all
                        raise
    
    def _build_execution_graph(self, workflow: PydanticWorkflow) -> Dict[str, List[str]]:
        """Build execution dependency graph"""
        graph = {}
        for task in workflow.tasks:
            task_id = task['id']
            dependencies = workflow.dependencies.get(task_id, [])
            graph[task_id] = dependencies
        return graph
    
    def _get_ready_tasks(self, pending_tasks: set, completed_tasks: set, dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Get tasks ready for execution"""
        ready_tasks = []
        
        for task in pending_tasks:
            task_id = task['id']
            task_deps = dependencies.get(task_id, [])
            
            # Check if all dependencies are completed
            if all(dep in completed_tasks for dep in task_deps):
                ready_tasks.append(task)
        
        return ready_tasks
    
    async def _execute_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task"""
        task_id = task['id']
        task_type = task['type']
        task_config = task.get('config', {})
        
        logger.info(f"🔄 Executing task: {task['name']} (Type: {task_type})")
        
        # Execute based on task type
        if task_type == 'http_request':
            return await self._execute_http_request(task_config, context)
        elif task_type == 'function_call':
            return await self._execute_function_call(task_config, context)
        elif task_type == 'conditional':
            return await self._execute_conditional(task_config, context)
        elif task_type == 'delay':
            return await self._execute_delay(task_config, context)
        elif task_type == 'data_transform':
            return await self._execute_data_transform(task_config, context)
        elif task_type == 'ai_task':
            return await self._execute_ai_task(task_config, context)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _execute_http_request(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request task"""
        try:
            method = config.get('method', 'GET').upper()
            url = config.get('url', '')
            headers = config.get('headers', {})
            data = config.get('data', {})
            
            # Replace variables in URL and data
            url = self._replace_variables(url, context)
            data = self._replace_variables(data, context)
            
            # Make request
            response = await asyncio.to_thread(
                requests.request,
                method=method,
                url=url,
                headers=headers,
                json=data,
                timeout=config.get('timeout', 30)
            )
            
            return {
                'status_code': response.status_code,
                'response': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                'headers': dict(response.headers)
            }
            
        except Exception as e:
            raise Exception(f"HTTP request failed: {str(e)}")
    
    async def _execute_function_call(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute function call task"""
        try:
            function_name = config.get('function')
            function_args = config.get('args', {})
            
            if function_name not in self.task_registry:
                raise ValueError(f"Function {function_name} not registered")
            
            # Replace variables in arguments
            function_args = self._replace_variables(function_args, context)
            
            # Execute function
            function = self.task_registry[function_name]
            result = await asyncio.to_thread(function, **function_args)
            
            return {'result': result}
            
        except Exception as e:
            raise Exception(f"Function call failed: {str(e)}")
    
    async def _execute_conditional(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional task"""
        try:
            condition = config.get('condition', '')
            true_value = config.get('true_value')
            false_value = config.get('false_value')
            
            # Evaluate condition
            condition_result = self._evaluate_condition(condition, context)
            
            return {
                'condition': condition,
                'result': true_value if condition_result else false_value,
                'condition_result': condition_result
            }
            
        except Exception as e:
            raise Exception(f"Conditional evaluation failed: {str(e)}")
    
    async def _execute_delay(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute delay task"""
        try:
            delay_seconds = config.get('seconds', 1)
            delay_seconds = self._replace_variables(delay_seconds, context)
            
            await asyncio.sleep(delay_seconds)
            
            return {'delayed': True, 'seconds': delay_seconds}
            
        except Exception as e:
            raise Exception(f"Delay execution failed: {str(e)}")
    
    async def _execute_data_transform(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data transformation task"""
        try:
            input_data = config.get('input', {})
            transformation_rules = config.get('rules', [])
            
            # Replace variables in input data
            input_data = self._replace_variables(input_data, context)
            
            # Apply transformations
            result = input_data
            for rule in transformation_rules:
                result = self._apply_transformation(result, rule)
            
            return {'transformed_data': result}
            
        except Exception as e:
            raise Exception(f"Data transformation failed: {str(e)}")
    
    async def _execute_ai_task(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI task with LLM integration"""
        try:
            prompt = config.get('prompt', '')
            model = config.get('model', 'gpt-3.5-turbo')
            max_tokens = config.get('max_tokens', 1000)
            
            # Replace variables in prompt
            prompt = self._replace_variables(prompt, context)
            
            # Use AI optimizer for task execution
            result = await self.ai_optimizer.execute_ai_task(prompt, model, max_tokens)
            
            return {'ai_result': result}
            
        except Exception as e:
            raise Exception(f"AI task execution failed: {str(e)}")
    
    def _replace_variables(self, data: Any, context: Dict[str, Any]) -> Any:
        """Replace variables in data with context values"""
        if isinstance(data, str):
            # Simple variable replacement
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool)):
                    data = data.replace(f'{{{{{key}}}}}', str(value))
            return data
        elif isinstance(data, dict):
            return {k: self._replace_variables(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_variables(item, context) for item in data]
        else:
            return data
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate conditional expression"""
        try:
            # Simple condition evaluation (could be enhanced with proper expression parser)
            # For now, support basic comparisons
            if '==' in condition:
                left, right = condition.split('==', 1)
                left = left.strip()
                right = right.strip()
                
                left_val = context.get(left, left)
                right_val = context.get(right, right)
                
                return left_val == right_val
            elif '!=' in condition:
                left, right = condition.split('!=', 1)
                left = left.strip()
                right = right.strip()
                
                left_val = context.get(left, left)
                right_val = context.get(right, right)
                
                return left_val != right_val
            else:
                # Assume it's a boolean expression
                return bool(context.get(condition, False))
                
        except Exception:
            return False
    
    def _apply_transformation(self, data: Any, rule: Dict[str, Any]) -> Any:
        """Apply data transformation rule"""
        rule_type = rule.get('type')
        
        if rule_type == 'map':
            # Map transformation
            mapping = rule.get('mapping', {})
            if isinstance(data, dict):
                return {mapping.get(k, k): v for k, v in data.items()}
        elif rule_type == 'filter':
            # Filter transformation
            condition = rule.get('condition', '')
            if isinstance(data, list):
                return [item for item in data if self._evaluate_condition(condition, {'item': item})]
        elif rule_type == 'aggregate':
            # Aggregate transformation
            if isinstance(data, list):
                agg_type = rule.get('aggregate_type', 'sum')
                field = rule.get('field', '')
                
                if agg_type == 'sum':
                    return sum(item.get(field, 0) for item in data)
                elif agg_type == 'avg':
                    values = [item.get(field, 0) for item in data]
                    return sum(values) / len(values) if values else 0
        
        return data
    
    def _register_builtin_tasks(self):
        """Register built-in task functions"""
        self.register_task('send_email', self._send_email_task)
        self.register_task('log_message', self._log_message_task)
        self.register_task('get_time', self._get_time_task)
        self.register_task('calculate', self._calculate_task)
    
    async def _send_email_task(self, **kwargs) -> Dict[str, Any]:
        """Built-in email sending task"""
        # This would integrate with actual email service
        logger.info(f"📧 Email task: {kwargs}")
        return {'status': 'sent', 'message': 'Email sent successfully'}
    
    async def _log_message_task(self, **kwargs) -> Dict[str, Any]:
        """Built-in logging task"""
        message = kwargs.get('message', '')
        level = kwargs.get('level', 'info')
        
        if level == 'info':
            logger.info(f"📝 Log: {message}")
        elif level == 'warning':
            logger.warning(f"⚠️ Log: {message}")
        elif level == 'error':
            logger.error(f"❌ Log: {message}")
        
        return {'status': 'logged', 'message': message}
    
    async def _get_time_task(self, **kwargs) -> Dict[str, Any]:
        """Built-in time retrieval task"""
        format_str = kwargs.get('format', '%Y-%m-%d %H:%M:%S')
        return {'current_time': datetime.now().strftime(format_str)}
    
    async def _calculate_task(self, **kwargs) -> Dict[str, Any]:
        """Built-in calculation task"""
        expression = kwargs.get('expression', '0')
        try:
            # Secure calculation using restricted eval
            # Only allow numbers, basic math operators (+, -, *, /), dots, parentheses, and whitespace
            if not re.match(r"^[0-9+\-*/().\s]+$", str(expression)):
                return {'error': "Invalid characters in expression", 'expression': expression}

            # Execute eval with no built-ins to prevent arbitrary code execution
            result = eval(str(expression), {"__builtins__": {}}, {})
            return {'result': result, 'expression': expression}
        except Exception as e:
            logger.error(f"Calculation failed for expression '{expression}': {e}")
            return {'error': "Calculation failed", 'expression': expression}

class AIWorkflowOptimizer:
    """AI-driven workflow optimization engine"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
        self.optimization_history = []
        self.performance_baseline = {}
    
    async def optimize_workflow(self, workflow: PydanticWorkflow, execution: WorkflowExecution):
        """Optimize workflow based on execution performance"""
        try:
            # Analyze performance metrics
            performance_analysis = await self._analyze_performance(execution)
            
            # Generate optimization suggestions
            suggestions = await self._generate_optimizations(workflow, performance_analysis)
            
            # Apply optimizations
            optimized_workflow = await self._apply_optimizations(workflow, suggestions)
            
            # Store optimization history
            self.optimization_history.append({
                'workflow_id': workflow.id,
                'execution_id': execution.execution_id,
                'performance_analysis': performance_analysis,
                'suggestions': suggestions,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"🔧 Workflow optimized: {workflow.name}")
            return optimized_workflow
            
        except Exception as e:
            logger.error(f"Workflow optimization failed: {str(e)}")
            return workflow
    
    async def _analyze_performance(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze workflow execution performance"""
        total_time = (execution.completed_at - execution.started_at).total_seconds()
        success_rate = execution.tasks_completed / max(execution.tasks_executed, 1)
        
        performance_metrics = {
            'total_execution_time': total_time,
            'success_rate': success_rate,
            'tasks_per_second': execution.tasks_executed / max(total_time, 1),
            'bottlenecks': self._identify_bottlenecks(execution),
            'resource_usage': self._analyze_resource_usage(execution)
        }
        
        return performance_metrics
    
    def _identify_bottlenecks(self, execution: WorkflowExecution) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        # This would analyze task execution times
        # For now, return mock data
        return [
            {
                'task_id': 'http_request_1',
                'bottleneck_type': 'network_latency',
                'impact': 'high',
                'suggestion': 'Add caching or parallel execution'
            }
        ]
    
    def _analyze_resource_usage(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Analyze resource usage during execution"""
        return {
            'cpu_usage': 0.5,  # Mock data
            'memory_usage': 0.3,
            'network_calls': 10,
            'database_queries': 5
        }
    
    async def _generate_optimizations(self, workflow: PydanticWorkflow, performance_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions using AI"""
        try:
            # Use LLM to generate optimization suggestions
            prompt = f"""
            Analyze this workflow performance data and suggest optimizations:
            
            Workflow: {workflow.name}
            Performance Analysis: {json.dumps(performance_analysis, indent=2)}
            
            Current Configuration:
            - Tasks: {len(workflow.tasks)}
            - Dependencies: {len(workflow.dependencies)}
            - Parallel Execution: {workflow.parallel_execution}
            - Error Handling: {workflow.error_handling}
            
            Please provide specific optimization suggestions focusing on:
            1. Task execution order
            2. Parallelization opportunities
            3. Resource optimization
            4. Error handling improvements
            """
            
            optimization_task = {
                'description': 'Generate workflow optimization suggestions',
                'prompt': prompt
            }
            
            result = self.multi_llm_router.route_task(optimization_task)
            
            # Parse suggestions from AI response
            suggestions = self._parse_optimization_suggestions(result.get('content', ''))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate optimizations: {str(e)}")
            return []
    
    def _parse_optimization_suggestions(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse optimization suggestions from AI response"""
        # Simple parsing - could be enhanced with proper NLP
        suggestions = []
        
        if 'parallel' in ai_response.lower():
            suggestions.append({
                'type': 'parallelization',
                'description': 'Enable parallel execution for independent tasks',
                'priority': 'high',
                'impact': 'medium'
            })
        
        if 'cache' in ai_response.lower():
            suggestions.append({
                'type': 'caching',
                'description': 'Add caching for expensive operations',
                'priority': 'medium',
                'impact': 'high'
            })
        
        return suggestions
    
    async def _apply_optimizations(self, workflow: PydanticWorkflow, suggestions: List[Dict[str, Any]]) -> PydanticWorkflow:
        """Apply optimization suggestions to workflow"""
        try:
            # Create a copy of the workflow
            optimized_workflow = workflow.copy()
            
            for suggestion in suggestions:
                suggestion_type = suggestion['type']
                
                if suggestion_type == 'parallelization':
                    optimized_workflow.parallel_execution = True
                elif suggestion_type == 'caching':
                    # Add caching configuration
                    optimized_workflow.config = optimized_workflow.config or {}
                    optimized_workflow.config['caching'] = True
            
            return optimized_workflow
            
        except Exception as e:
            logger.error(f"Failed to apply optimizations: {str(e)}")
            return workflow
    
    async def execute_ai_task(self, prompt: str, model: str = 'gpt-3.5-turbo', max_tokens: int = 1000) -> str:
        """Execute AI task using multi-LLM router"""
        try:
            ai_task = {
                'description': 'Execute AI task',
                'prompt': prompt,
                'model': model,
                'max_tokens': max_tokens
            }
            
            result = self.multi_llm_router.route_task(ai_task)
            return result.get('content', '')
            
        except Exception as e:
            logger.error(f"AI task execution failed: {str(e)}")
            return f"Error: {str(e)}"

class PerformanceMonitor:
    """Monitor workflow performance and generate insights"""
    
    def __init__(self):
        self.execution_history = []
        self.performance_metrics = {}
    
    async def record_execution(self, execution: WorkflowExecution):
        """Record execution metrics"""
        self.execution_history.append(execution)
        
        # Update performance metrics
        workflow_id = execution.workflow_id
        if workflow_id not in self.performance_metrics:
            self.performance_metrics[workflow_id] = {
                'total_executions': 0,
                'average_execution_time': 0,
                'success_rate': 0,
                'total_failures': 0
            }
        
        metrics = self.performance_metrics[workflow_id]
        metrics['total_executions'] += 1
        
        if execution.status == WorkflowStatus.COMPLETED:
            execution_time = (execution.completed_at - execution.started_at).total_seconds()
            metrics['average_execution_time'] = (
                (metrics['average_execution_time'] * (metrics['total_executions'] - 1) + execution_time) 
                / metrics['total_executions']
            )
        else:
            metrics['total_failures'] += 1
        
        metrics['success_rate'] = (
            (metrics['total_executions'] - metrics['total_failures']) / metrics['total_executions']
        )
    
    def get_performance_report(self, workflow_id: str = None) -> Dict[str, Any]:
        """Get performance report for workflows"""
        if workflow_id:
            return self.performance_metrics.get(workflow_id, {})
        
        return {
            'total_workflows': len(self.performance_metrics),
            'total_executions': sum(m['total_executions'] for m in self.performance_metrics.values()),
            'average_success_rate': sum(m['success_rate'] for m in self.performance_metrics.values()) / max(len(self.performance_metrics), 1),
            'workflows': self.performance_metrics
        }

class ErrorHandler:
    """Handle workflow execution errors and recovery"""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.recovery_strategies = self._load_recovery_strategies()
    
    def _load_error_patterns(self) -> Dict[str, Any]:
        """Load error pattern definitions"""
        return {
            'network_timeout': {
                'patterns': [r'timeout', r'connection refused', r'network error'],
                'severity': 'medium',
                'recovery': 'retry_with_backoff'
            },
            'authentication_error': {
                'patterns': [r'unauthorized', r'forbidden', r'invalid credentials'],
                'severity': 'high',
                'recovery': 'refresh_authentication'
            },
            'data_validation_error': {
                'patterns': [r'validation failed', r'invalid data', r'missing required field'],
                'severity': 'low',
                'recovery': 'fix_data_format'
            }
        }
    
    def _load_recovery_strategies(self) -> Dict[str, callable]:
        """Load recovery strategy functions"""
        return {
            'retry_with_backoff': self._retry_with_backoff,
            'refresh_authentication': self._refresh_authentication,
            'fix_data_format': self._fix_data_format
        }
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow execution error"""
        error_type = self._classify_error(str(error))
        
        if error_type in self.error_patterns:
            recovery_strategy = self.error_patterns[error_type]['recovery']
            
            if recovery_strategy in self.recovery_strategies:
                recovery_function = self.recovery_strategies[recovery_strategy]
                return await recovery_function(error, context)
        
        # Default error handling
        return {
            'action': 'fail',
            'message': f'Unhandled error: {str(error)}',
            'retry': False
        }
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error based on message patterns"""
        error_message_lower = error_message.lower()
        
        for error_type, config in self.error_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, error_message_lower):
                    return error_type
        
        return 'unknown_error'
    
    async def _retry_with_backoff(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry with exponential backoff"""
        retry_count = context.get('retry_count', 0)
        if retry_count < 3:
            delay = 2 ** retry_count
            await asyncio.sleep(delay)
            
            return {
                'action': 'retry',
                'delay': delay,
                'retry_count': retry_count + 1
            }
        
        return {'action': 'fail', 'message': 'Max retries exceeded'}
    
    async def _refresh_authentication(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh authentication credentials"""
        # This would integrate with actual authentication system
        return {
            'action': 'refresh_auth',
            'message': 'Authentication needs to be refreshed'
        }
    
    async def _fix_data_format(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix data format issues"""
        return {
            'action': 'fix_data',
            'message': 'Data format needs to be corrected'
        }

# Global instance
pydantic_n8n_engine = PydanticN8NEngine()

async def main():
    """Test the Pydantic n8n engine"""
    logger.info("🚀 Testing Pydantic AI n8n Engine")
    
    # Create a sample workflow
    workflow_data = {
        'name': 'Test Workflow',
        'description': 'A test workflow for Pydantic validation',
        'tasks': [
            {
                'id': 'task_1',
                'name': 'Log Start',
                'type': 'function_call',
                'config': {
                    'function': 'log_message',
                    'args': {'message': 'Workflow started', 'level': 'info'}
                }
            },
            {
                'id': 'task_2',
                'name': 'Get Time',
                'type': 'function_call',
                'config': {
                    'function': 'get_time',
                    'args': {'format': '%Y-%m-%d %H:%M:%S'}
                }
            }
        ],
        'dependencies': {
            'task_2': ['task_1']
        }
    }
    
    # Register and execute workflow
    workflow = pydantic_n8n_engine.register_workflow(workflow_data)
    execution = await pydantic_n8n_engine.execute_workflow(workflow.id)
    
    print(f"Workflow execution completed: {execution.status}")

if __name__ == "__main__":
    asyncio.run(main())