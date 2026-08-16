import time
import re
from typing import Any, Dict

def _replace_variables_old(data: Any, context: Dict[str, Any]) -> Any:
    """Old O(N*M) implementation"""
    if isinstance(data, str):
        # Simple variable replacement
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

VAR_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

def _replace_variables_new(data: Any, context: Dict[str, Any]) -> Any:
    """New O(N) implementation"""
    if isinstance(data, str):
        if '{{' not in data:
            return data

        def _replacer(match):
            key = match.group(1).strip()
            return str(context.get(key, match.group(0)))

        return VAR_PATTERN.sub(_replacer, data)
    elif isinstance(data, dict):
        return {k: _replace_variables_new(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_variables_new(item, context) for item in data]
    else:
        return data

def benchmark():
    context = {f"key_{i}": f"value_{i}" for i in range(1000)}
    test_str = "Hello {{key_0}}, welcome to {{key_500}} and {{key_999}}. This is a test for {{non_existent}}."

    # Large context, small string with few replacements
    start = time.time()
    for _ in range(1000):
        _replace_variables_old(test_str, context)
    old_time = time.time() - start

    start = time.time()
    for _ in range(1000):
        _replace_variables_new(test_str, context)
    new_time = time.time() - start

    print(f"Old time: {old_time:.4f}s")
    print(f"New time: {new_time:.4f}s")
    print(f"Speedup: {old_time / new_time:.2f}x")

    # Plain string (no variables)
    plain_str = "This is a plain string without any variables."
    start = time.time()
    for _ in range(1000):
        _replace_variables_old(plain_str, context)
    old_plain_time = time.time() - start

    start = time.time()
    for _ in range(1000):
        _replace_variables_new(plain_str, context)
    new_plain_time = time.time() - start

    print(f"Old plain time: {old_plain_time:.4f}s")
    print(f"New plain time: {new_plain_time:.4f}s")
    print(f"Plain Speedup: {old_plain_time / new_plain_time:.2f}x")

if __name__ == "__main__":
    benchmark()
