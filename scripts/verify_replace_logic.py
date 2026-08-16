import asyncio
import re
from typing import Any, Dict

# Copy the optimized function and VAR_PATTERN from pydantic_n8n_engine.py
VAR_PATTERN = re.compile(r'\{\{(.*?)\}\}')

def _replace_variables(data: Any, context: Dict[str, Any]) -> Any:
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
        return {k: _replace_variables(v, context) for k, v in data.items()}
    elif isinstance(data, list):
        return [_replace_variables(item, context) for item in data]
    else:
        return data

def test_replace_variables_basic():
    context = {"name": "World", "task": "testing"}
    template = "Hello {{name}}, we are {{task}}."
    result = _replace_variables(template, context)
    assert result == "Hello World, we are testing."

def test_replace_variables_nested():
    context = {"key": "value"}
    data = {"a": "{{key}}", "b": ["{{key}}", 123]}
    result = _replace_variables(data, context)
    assert result == {"a": "value", "b": ["value", 123]}

def test_replace_variables_missing():
    context = {"found": "yes"}
    template = "{{found}} and {{missing}}"
    result = _replace_variables(template, context)
    assert result == "yes and {{missing}}"

def test_replace_variables_types():
    context = {"int": 1, "float": 2.5, "bool": True, "str": "hello"}
    template = "{{int}} {{float}} {{bool}} {{str}}"
    result = _replace_variables(template, context)
    assert result == "1 2.5 True hello"

def test_replace_variables_whitespace():
    context = {"var": "val"}
    template = "{{ var }} {{  var  }}"
    result = _replace_variables(template, context)
    assert result == "val val"

if __name__ == "__main__":
    test_replace_variables_basic()
    test_replace_variables_nested()
    test_replace_variables_missing()
    test_replace_variables_types()
    test_replace_variables_whitespace()
    print("All regression tests passed!")
