import asyncio
import unittest
from pydantic_n8n_engine import pydantic_n8n_engine

class TestVariableReplacement(unittest.TestCase):
    def test_basic_replacement(self):
        context = {"name": "Jules", "task": "optimization"}
        data = "Hello {{name}}, let's do some {{task}}."
        expected = "Hello Jules, let's do some optimization."
        result = pydantic_n8n_engine._replace_variables(data, context)
        self.assertEqual(result, expected)

    def test_nested_replacement(self):
        context = {"user": {"name": "Jules"}, "status": "active"}
        # Note: current implementation only supports flat context for strings,
        # but supports nested dicts/lists for recursion.
        # Wait, let's check how it handles {{user.name}}
        data = {"msg": "User {{user}} is {{status}}"}
        # Current implementation does data.replace('{{user}}', str(value))
        # if user is a dict, it will stringify the dict.
        result = pydantic_n8n_engine._replace_variables(data, context)
        self.assertEqual(result["msg"], "User {'name': 'Jules'} is active")

    def test_missing_key(self):
        context = {"a": "1"}
        data = "Val {{b}}"
        # Old implementation: data = data.replace('{{a}}', '1') -> data is "Val {{b}}"
        result = pydantic_n8n_engine._replace_variables(data, context)
        self.assertEqual(result, "Val {{b}}")

    def test_non_string_values(self):
        context = {"count": 42, "pi": 3.14, "alive": True}
        data = "Count: {{count}}, Pi: {{pi}}, Alive: {{alive}}"
        expected = "Count: 42, Pi: 3.14, Alive: True"
        result = pydantic_n8n_engine._replace_variables(data, context)
        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()
