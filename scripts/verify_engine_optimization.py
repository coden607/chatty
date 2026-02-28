import asyncio
import time
import re
from typing import Any, Dict, List

# Optimized function to test
def _replace_variables(data: Any, context: Dict[str, Any]) -> Any:
    if isinstance(data, str):
        return re.sub(
            r'\{\{(.*?)\}\}',
            lambda m: str(context.get(m.group(1).strip(), m.group(0))),
            data
        )
    elif isinstance(data, dict):
        return {k: _replace_variables(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_variables(item, context) for item in data]
    else:
        return data

# Mock Task Execution
async def _execute_task_mock(task, context):
    delay = task.get('config', {}).get('delay', 0.1)
    await asyncio.sleep(delay)
    return {"status": "ok", "task_id": task['id']}

# Mock Workflow Logic (Simplified from pydantic_n8n_engine.py)
async def execute_workflow_mock(tasks_list, dependencies, parallel=False):
    completed_tasks = set()
    pending_tasks = {task['id']: task for task in tasks_list}
    tasks_executed = 0
    start_time = time.time()

    context = {} # Simplified

    while pending_tasks:
        ready_tasks = []
        for task in pending_tasks.values():
            task_deps = dependencies.get(task['id'], [])
            if all(dep in completed_tasks for dep in task_deps):
                ready_tasks.append(task)

        if not ready_tasks:
            if pending_tasks:
                raise ValueError("Circular dependency or deadlock")
            break

        if parallel:
            results = await asyncio.gather(*[_execute_task_mock(t, context) for t in ready_tasks])
            for task, result in zip(ready_tasks, results):
                completed_tasks.add(task['id'])
                del pending_tasks[task['id']]
                tasks_executed += 1
        else:
            for task in ready_tasks:
                await _execute_task_mock(task, context)
                completed_tasks.add(task['id'])
                del pending_tasks[task['id']]
                tasks_executed += 1

    return time.time() - start_time, tasks_executed

async def main():
    print("--- Verification: Variable Replacement ---")
    context = {"user": "Bolt", "action": "optimize"}
    template = "Hello {{ user }}, time to {{ action }}!"
    result = _replace_variables(template, context)
    print(f"Result: {result}")
    assert result == "Hello Bolt, time to optimize!"

    # Performance benchmark
    large_context = {f"v_{i}": f"val_{i}" for i in range(100)}
    large_template = " ".join([f"{{{{v_{i}}}}}" for i in range(100)])

    start = time.time()
    for _ in range(1000):
        _replace_variables(large_template, large_context)
    duration = time.time() - start
    print(f"Regex replacement duration (1000 iterations): {duration:.4f}s")

    print("\n--- Verification: Task Execution (Fix & Parallel) ---")
    tasks = [{'id': f't_{i}', 'name': f'Task {i}', 'config': {'delay': 0.1}} for i in range(5)]
    deps = {} # All independent

    print("Executing sequentially...")
    seq_time, count = await execute_workflow_mock(tasks, deps, parallel=False)
    print(f"Sequential: {seq_time:.4f}s for {count} tasks")
    assert count == 5
    assert seq_time >= 0.5

    print("Executing in parallel...")
    tasks = [{'id': f't_{i}', 'name': f'Task {i}', 'config': {'delay': 0.1}} for i in range(5)]
    par_time, count = await execute_workflow_mock(tasks, deps, parallel=True)
    print(f"Parallel: {par_time:.4f}s for {count} tasks")
    assert count == 5
    assert par_time < 0.2
    print(f"Speedup: {seq_time / par_time:.2f}x")

    print("\n--- Verification: Dependency Handling ---")
    # t1 -> t2
    tasks = [
        {'id': 't1', 'name': 'Task 1', 'config': {'delay': 0.1}},
        {'id': 't2', 'name': 'Task 2', 'config': {'delay': 0.1}}
    ]
    deps = {'t2': ['t1']}
    dep_time, count = await execute_workflow_mock(tasks, deps, parallel=True)
    print(f"Dependency execution time: {dep_time:.4f}s")
    assert count == 2
    assert dep_time >= 0.2 # Must be serial due to dependency

    print("\n✅ Verification Successful!")

if __name__ == "__main__":
    asyncio.run(main())
