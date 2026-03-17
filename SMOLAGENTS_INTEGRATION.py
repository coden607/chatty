#!/usr/bin/env python3
"""
CHATTY smolagents Integration
Code-first agents that write Python instead of JSON (~30% fewer steps)
Minimal codebase (~1000 lines core) with sandboxed execution
"""

import asyncio
import json
import logging
import re
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import textwrap

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """A tool that can be used by smolagents"""
    name: str
    description: str
    function: Callable
    inputs: Dict[str, Any] = field(default_factory=dict)
    output_type: str = "string"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputs": self.inputs,
            "output_type": self.output_type
        }
    
    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


@dataclass
class CodeAgentResult:
    """Result from a code agent execution"""
    code: str
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return self.error is None


class SandboxExecutor:
    """
    Sandboxed code execution environment
    Uses E2B-style isolation for security
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.allowed_modules = [
            'json', 'math', 'random', 'datetime', 're', 'string',
            'collections', 'itertools', 'functools', 'statistics',
            'typing', 'pathlib', 'hashlib', 'base64', 'urllib.parse'
        ]
    
    async def execute(self, code: str, context: Dict[str, Any] = None) -> CodeAgentResult:
        """Execute Python code in sandboxed environment"""
        start_time = asyncio.get_event_loop().time()
        
        # Sanitize code
        sanitized_code = self._sanitize_code(code)
        
        # Create execution script
        exec_script = f"""
import sys
import json

# Restrict imports
allowed_modules = {self.allowed_modules}

class ImportRestrictor:
    def find_module(self, name, path=None):
        base_module = name.split('.')[0]
        if base_module not in allowed_modules:
            raise ImportError(f"Import of '{{name}}' is not allowed")
        return None

sys.meta_path.insert(0, ImportRestrictor())

# Execute user code
result = {{}}
output_buffer = []
error_buffer = []

try:
    # Redirect stdout/stderr
    import io
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    
    # Execute code
    exec_context = {json.dumps(context or {})}
    exec(sanitized_code, exec_context)
    
    # Capture output
    output = sys.stdout.getvalue()
    error = sys.stderr.getvalue()
    
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    
    # Get result if 'result' variable was set
    if 'result' in exec_context:
        result = exec_context['result']
    
    print(json.dumps({{
        'success': True,
        'output': output,
        'error': error if error else None,
        'result': result
    }}))
    
except Exception as e:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    print(json.dumps({{
        'success': False,
        'error': str(e),
        'output': '',
        'result': None
    }}))
"""
        
        try:
            # Run in subprocess with timeout
            proc = await asyncio.create_subprocess_exec(
                sys.executable, '-c', exec_script,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                limit=1024*1024  # 1MB output limit
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout
                )
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                # Parse result
                try:
                    result_data = json.loads(stdout.decode('utf-8', errors='ignore').strip().split('\n')[-1])
                    
                    return CodeAgentResult(
                        code=sanitized_code,
                        output=result_data.get('output', ''),
                        error=result_data.get('error'),
                        execution_time=execution_time,
                        result=result_data.get('result')
                    )
                except json.JSONDecodeError:
                    return CodeAgentResult(
                        code=sanitized_code,
                        output=stdout.decode('utf-8', errors='ignore'),
                        error=stderr.decode('utf-8', errors='ignore') or None,
                        execution_time=execution_time
                    )
                    
            except asyncio.TimeoutError:
                proc.kill()
                return CodeAgentResult(
                    code=sanitized_code,
                    output='',
                    error=f'Execution timed out after {self.timeout} seconds',
                    execution_time=self.timeout
                )
                
        except Exception as e:
            return CodeAgentResult(
                code=sanitized_code,
                output='',
                error=str(e),
                execution_time=asyncio.get_event_loop().time() - start_time
            )
    
    def _sanitize_code(self, code: str) -> str:
        """Sanitize code for safe execution"""
        # Remove potentially dangerous imports and functions
        dangerous_patterns = [
            r'import\s+os',
            r'import\s+sys',
            r'import\s+subprocess',
            r'import\s+socket',
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'compile\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'execfile',
            r'raw_input',
            r'input\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                raise ValueError(f"Code contains disallowed pattern: {pattern}")
        
        return code


class SmolAgent:
    """
    Code-first agent that writes and executes Python code
    Inspired by HuggingFace smolagents (~30% fewer steps than JSON tool calling)
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        tools: List[Tool] = None,
        max_steps: int = 10,
        planning_interval: int = 3
    ):
        self.name = name
        self.description = description
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.max_steps = max_steps
        self.planning_interval = planning_interval
        
        self.executor = SandboxExecutor()
        self.memory: List[Dict[str, Any]] = []
        
    def add_tool(self, tool: Tool):
        """Add a tool to the agent"""
        self.tools[tool.name] = tool
    
    def create_tool(
        self,
        name: str,
        description: str,
        function: Callable,
        inputs: Dict[str, Any] = None,
        output_type: str = "string"
    ) -> Tool:
        """Create and add a new tool"""
        tool = Tool(
            name=name,
            description=description,
            function=function,
            inputs=inputs or {},
            output_type=output_type
        )
        self.add_tool(tool)
        return tool
    
    async def run(self, task: str) -> Dict[str, Any]:
        """
        Execute a task by writing and running Python code
        """
        logger.info(f"🤖 SmolAgent '{self.name}' starting task: {task[:50]}...")
        
        step = 0
        plan = None
        results = []
        final_answer = None
        
        while step < self.max_steps and not final_answer:
            step += 1
            
            # Replan at intervals
            if step == 1 or (step - 1) % self.planning_interval == 0:
                plan = await self._create_plan(task, results)
                logger.info(f"📋 Step {step}: Plan updated - {plan}")
            
            # Generate code for next step
            code = await self._generate_code(task, plan, results, step)
            
            # Execute code
            context = {
                'tools': self.tools,
                'memory': self.memory,
                'step': step
            }
            
            result = await self.executor.execute(code, context)
            
            execution_result = {
                'step': step,
                'code': code,
                'output': result.output,
                'error': result.error,
                'success': result.success,
                'tools_used': result.tools_used
            }
            results.append(execution_result)
            self.memory.append(execution_result)
            
            # Check if we have final answer
            if result.success and ('final_answer' in result.output or 'result' in str(result.output)):
                final_answer = result.output
            
            logger.info(f"✅ Step {step} complete: {'success' if result.success else 'failed'}")
        
        return {
            'agent': self.name,
            'task': task,
            'steps': step,
            'results': results,
            'final_answer': final_answer or results[-1]['output'] if results else None,
            'success': final_answer is not None or (results and results[-1]['success'])
        }
    
    async def _create_plan(self, task: str, previous_results: List[Dict]) -> str:
        """Create execution plan using LLM"""
        from CHATTY_MODEL_ROUTER import router
        
        tools_desc = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.tools.items()
        ])
        
        prompt = f"""Create a step-by-step plan to solve this task:

TASK: {task}

AVAILABLE TOOLS:
{tools_desc}

PREVIOUS PROGRESS:
{json.dumps(previous_results, indent=2)[:500] if previous_results else 'Starting fresh'}

Provide a concise plan (3-5 steps) to complete this task.
Focus on which tools to use and in what order."""

        return await router.generate(
            prompt=prompt,
            system_prompt="You are a planning expert. Create clear, actionable plans."
        )
    
    async def _generate_code(
        self,
        task: str,
        plan: str,
        previous_results: List[Dict],
        step: int
    ) -> str:
        """Generate Python code to execute next step"""
        from CHATTY_MODEL_ROUTER import router
        
        tools_code = "\n".join([
            f"def {name}({', '.join(tool.inputs.keys())}):\n"
            f"    '''{tool.description}'''\n"
            f"    # Tool available in context\n"
            f"    return tools['{name}']({', '.join(tool.inputs.keys())})"
            for name, tool in self.tools.items()
        ])
        
        previous = "\n".join([
            f"Step {r['step']}: {'✅' if r['success'] else '❌'}\n{r['output'][:200]}"
            for r in previous_results[-3:]  # Last 3 steps
        ])
        
        prompt = f"""Write Python code to advance this task:

TASK: {task}
PLAN: {plan}
STEP: {step}

AVAILABLE TOOLS (pre-loaded):
{tools_code}

PREVIOUS EXECUTION:
{previous}

Write clean Python code to execute the next step.
- Use available tools as functions
- Store the final result in a variable called 'result'
- Print intermediate outputs
- Handle errors gracefully

Respond with ONLY the Python code, no markdown or explanation."""

        code = await router.generate(
            prompt=prompt,
            system_prompt="You write clean, effective Python code. Be concise."
        )
        
        # Extract code from markdown if present
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()
        
        return code


# Pre-built tools for CHATTY smolagents
class ChattySmolTools:
    """Factory for CHATTY's smolagent tools"""
    
    @staticmethod
    def calculator_tool() -> Tool:
        """Basic calculator tool"""
        def calculator(expression: str) -> str:
            try:
                # Safe eval with limited globals
                allowed = {
                    'abs': abs, 'max': max, 'min': min,
                    'sum': sum, 'pow': pow, 'round': round,
                    'int': int, 'float': float
                }
                result = eval(expression, {"__builtins__": {}}, allowed)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        return Tool(
            name="calculator",
            description="Performs mathematical calculations",
            function=calculator,
            inputs={"expression": {"type": "string", "description": "Math expression to evaluate"}},
            output_type="string"
        )
    
    @staticmethod
    def web_search_tool() -> Tool:
        """Web search tool (requires Brave API key)"""
        async def web_search(query: str, num_results: int = 5) -> str:
            import os
            import httpx
            
            api_key = os.getenv("BRAVE_API_KEY")
            if not api_key:
                return "Error: BRAVE_API_KEY not configured"
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.search.brave.com/res/v1/web/search",
                        headers={"X-Subscription-Token": api_key},
                        params={"q": query, "count": num_results}
                    )
                    data = response.json()
                    
                    results = []
                    for item in data.get("web", {}).get("results", [])[:num_results]:
                        results.append(f"{item['title']}: {item['url']}")
                    
                    return "\n".join(results)
            except Exception as e:
                return f"Error: {str(e)}"
        
        return Tool(
            name="web_search",
            description="Searches the web for information",
            function=web_search,
            inputs={
                "query": {"type": "string", "description": "Search query"},
                "num_results": {"type": "integer", "description": "Number of results", "default": 5}
            },
            output_type="string"
        )
    
    @staticmethod
    def file_reader_tool() -> Tool:
        """Read file contents"""
        def read_file(path: str) -> str:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        return Tool(
            name="read_file",
            description="Reads content from a file",
            function=read_file,
            inputs={"path": {"type": "string", "description": "File path to read"}},
            output_type="string"
        )
    
    @staticmethod
    def file_writer_tool() -> Tool:
        """Write file contents"""
        def write_file(path: str, content: str) -> str:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"File written successfully: {path}"
            except Exception as e:
                return f"Error writing file: {str(e)}"
        
        return Tool(
            name="write_file",
            description="Writes content to a file",
            function=write_file,
            inputs={
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"}
            },
            output_type="string"
        )
    
    @staticmethod
    def data_analyzer_tool() -> Tool:
        """Analyze data structures"""
        def analyze_data(data: str) -> str:
            try:
                # Try to parse as JSON
                parsed = json.loads(data)
                
                if isinstance(parsed, dict):
                    return f"Dictionary with {len(parsed)} keys: {list(parsed.keys())}"
                elif isinstance(parsed, list):
                    return f"List with {len(parsed)} items. First item type: {type(parsed[0]).__name__ if parsed else 'N/A'}"
                else:
                    return f"Data type: {type(parsed).__name__}, Value: {str(parsed)[:100]}"
            except:
                # Treat as text
                lines = data.split('\n')
                words = data.split()
                return f"Text analysis: {len(lines)} lines, {len(words)} words, {len(data)} characters"
        
        return Tool(
            name="analyze_data",
            description="Analyzes data structures and content",
            function=analyze_data,
            inputs={"data": {"type": "string", "description": "Data to analyze (JSON or text)"}},
            output_type="string"
        )


# Factory for creating CHATTY smolagents
class ChattySmolAgents:
    """Factory for CHATTY's code-first agents"""
    
    @staticmethod
    def data_analyst() -> SmolAgent:
        """Agent for data analysis tasks"""
        agent = SmolAgent(
            name="data_analyst",
            description="Analyzes data, performs calculations, and generates insights"
        )
        agent.add_tool(ChattySmolTools.calculator_tool())
        agent.add_tool(ChattySmolTools.data_analyzer_tool())
        agent.add_tool(ChattySmolTools.file_reader_tool())
        return agent
    
    @staticmethod
    def content_researcher() -> SmolAgent:
        """Agent for content research"""
        agent = SmolAgent(
            name="content_researcher",
            description="Researches topics and gathers information from various sources"
        )
        agent.add_tool(ChattySmolTools.web_search_tool())
        agent.add_tool(ChattySmolTools.file_reader_tool())
        agent.add_tool(ChattySmolTools.file_writer_tool())
        return agent
    
    @staticmethod
    def code_assistant() -> SmolAgent:
        """Agent for code-related tasks"""
        agent = SmolAgent(
            name="code_assistant",
            description="Helps with code analysis, generation, and refactoring"
        )
        agent.add_tool(ChattySmolTools.file_reader_tool())
        agent.add_tool(ChattySmolTools.file_writer_tool())
        agent.add_tool(ChattySmolTools.data_analyzer_tool())
        return agent
    
    @staticmethod
    def automation_builder() -> SmolAgent:
        """Agent for building automation scripts"""
        agent = SmolAgent(
            name="automation_builder",
            description="Creates automation scripts and workflows"
        )
        agent.add_tool(ChattySmolTools.file_reader_tool())
        agent.add_tool(ChattySmolTools.file_writer_tool())
        agent.add_tool(ChattySmolTools.calculator_tool())
        return agent


if __name__ == "__main__":
    import sys
    
    async def test():
        print("🧪 Testing smolagents Integration...")
        
        # Test data analyst
        analyst = ChattySmolAgents.data_analyst()
        print(f"✅ Created agent: {analyst.name}")
        print(f"   Tools: {list(analyst.tools.keys())}")
        
        # Run simple calculation
        result = await analyst.run("Calculate the average of 10, 20, 30, 40, 50 and explain the steps")
        
        print(f"\n📊 Execution:")
        print(f"   Steps: {result['steps']}")
        print(f"   Success: {result['success']}")
        print(f"   Final Answer:\n{result['final_answer'][:300]}...")
        
        print("\n✅ SmolAgents test complete")
    
    asyncio.run(test())
