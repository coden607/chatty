import time
import re
from typing import Any, Dict

def _replace_variables_old(data: Any, context: Dict[str, Any]) -> Any:
    """Old implementation using loop and replace"""
    if isinstance(data, str):
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                data = data.replace(f'{{{{{key}}}}}', str(value))
        return data
    elif isinstance(data, dict):
        return {k: _replace_variables_old(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_variables_old(item, context) for item in data]
    else:
        return data

# Pre-compile the pattern for better performance in the new method
VAR_PATTERN = re.compile(r'\{\{(.*?)\}\}')

def _replace_variables_new(data: Any, context: Dict[str, Any]) -> Any:
    """New implementation using regex with pre-compiled pattern"""
    if isinstance(data, str):
        if '{{' not in data:
            return data

        def replace_match(match):
            var_name = match.group(1).strip()
            if var_name in context:
                val = context[var_name]
                if isinstance(val, (str, int, float, bool)):
                    return str(val)
            return match.group(0)

        return VAR_PATTERN.sub(replace_match, data)
    elif isinstance(data, dict):
        return {k: _replace_variables_new(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_variables_new(item, context) for item in data]
    else:
        return data

# Benchmark
context = {f"var_{i}": f"value_{i}" for i in range(100)}
test_string_with_vars = "Template with " + " ".join([f"{{{{var_{i}}}}}" for i in range(100)])
test_string_without_vars = "Just a simple string without any variables for speed testing"

iterations = 10000

print(f"Benchmarking with {len(context)} variables and {iterations} iterations...")

print("\n--- STRING WITH VARS ---")
start = time.time()
for _ in range(iterations):
    _replace_variables_old(test_string_with_vars, context)
end = time.time()
print(f"Old method: {end - start:.4f}s")

start = time.time()
for _ in range(iterations):
    _replace_variables_new(test_string_with_vars, context)
end = time.time()
print(f"New method: {end - start:.4f}s")

print("\n--- STRING WITHOUT VARS ---")
start = time.time()
for _ in range(iterations):
    _replace_variables_old(test_string_without_vars, context)
end = time.time()
print(f"Old method: {end - start:.4f}s")

start = time.time()
for _ in range(iterations):
    _replace_variables_new(test_string_without_vars, context)
end = time.time()
print(f"New method: {end - start:.4f}s")
