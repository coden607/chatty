
import asyncio
import time
import re
from typing import Any, Dict
import logging

# Mock logging and db objects since we can't easily import from server.py due to complex dependencies
class MockLogger:
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

import sys
from unittest.mock import MagicMock

# Mocking the problematic imports
sys.modules['server'] = MagicMock()
sys.modules['server'].logger = MockLogger()
sys.modules['server'].db = MagicMock()
sys.modules['server'].Agent = MagicMock()
sys.modules['server'].Task = MagicMock()
sys.modules['learning_system'] = MagicMock()
sys.modules['openclaw_integration'] = MagicMock()

from pydantic_n8n_engine import pydantic_n8n_engine, PydanticWorkflow

async def benchmark_parallel():
    print("--- Benchmarking Parallel Execution ---")

    # Workflow with 3 independent delays of 1s each
    workflow_data = {
        'name': 'Benchmark Parallel',
        'description': 'Measuring speedup from parallel execution',
        'parallel_execution': True,
        'tasks': [
            {'id': 't1', 'name': 'Delay 1', 'type': 'delay', 'config': {'seconds': 1}},
            {'id': 't2', 'name': 'Delay 2', 'type': 'delay', 'config': {'seconds': 1}},
            {'id': 't3', 'name': 'Delay 3', 'type': 'delay', 'config': {'seconds': 1}},
        ],
        'dependencies': {}
    }

    # Register workflow
    workflow = pydantic_n8n_engine.register_workflow(workflow_data)

    start = time.time()
    await pydantic_n8n_engine.execute_workflow(workflow.id)
    duration_parallel = time.time() - start
    print(f"Parallel duration (expected ~1s): {duration_parallel:.2f}s")

    # Now test sequential
    workflow_data['parallel_execution'] = False
    workflow_data['id'] = 'bench_seq'
    workflow_seq = pydantic_n8n_engine.register_workflow(workflow_data)

    start = time.time()
    await pydantic_n8n_engine.execute_workflow(workflow_seq.id)
    duration_seq = time.time() - start
    print(f"Sequential duration (expected ~3s): {duration_seq:.2f}s")

    speedup = duration_seq / duration_parallel
    print(f"Parallel speedup: {speedup:.2f}x")

def benchmark_regex():
    print("\n--- Benchmarking Regex Substitution ---")

    context = {f"var_{i}": f"value_{i}" for i in range(1000)}
    template = " ".join([f"{{{{var_{i}}}}}" for i in range(1000)])

    # Legacy loop-based approach (simulated)
    def legacy_replace(data, ctx):
        for key, value in ctx.items():
            if isinstance(value, (str, int, float, bool)):
                data = data.replace(f'{{{{{key}}}}}', str(value))
        return data

    # New regex-based approach
    def new_replace(data, ctx):
        def replacer(match):
            key = match.group(1).strip()
            return str(ctx.get(key, match.group(0)))
        return re.sub(r'\{\{(.*?)\}\}', replacer, data)

    start = time.time()
    for _ in range(100):
        legacy_replace(template, context)
    duration_legacy = time.time() - start
    print(f"Legacy (loop) duration: {duration_legacy:.4f}s")

    start = time.time()
    for _ in range(100):
        new_replace(template, context)
    duration_new = time.time() - start
    print(f"New (regex) duration: {duration_new:.4f}s")

    speedup = duration_legacy / duration_new
    print(f"Regex speedup: {speedup:.2f}x")

if __name__ == "__main__":
    asyncio.run(benchmark_parallel())
    benchmark_regex()
