
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import asyncio
import time

# Add root directory to sys.path to find AUTOMATION_API_SERVER
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock dependencies before importing the app
sys.modules['AUTOMATED_REVENUE_ENGINE'] = MagicMock()
sys.modules['AUTOMATED_CUSTOMER_ACQUISITION'] = MagicMock()
sys.modules['START_COMPLETE_AUTOMATION'] = MagicMock()
sys.modules['transparency_log'] = MagicMock()

import AUTOMATION_API_SERVER

class TestAutomationApi(unittest.IsolatedAsyncioTestCase):

    async def test_dashboard_all_structure(self):
        # Test that the consolidated endpoint returns the expected keys
        with patch('AUTOMATION_API_SERVER.get_status', return_value={'status': 'ok'}), \
             patch('AUTOMATION_API_SERVER.get_leads', return_value={'total': 0, 'leads': []}), \
             patch('AUTOMATION_API_SERVER.get_narcoguard_workflows', return_value={'workflows': []}), \
             patch('AUTOMATION_API_SERVER.get_agents', return_value={'agents': []}), \
             patch('AUTOMATION_API_SERVER.get_tasks', return_value={'tasks': []}), \
             patch('AUTOMATION_API_SERVER.get_collab_feed', return_value={'events': []}), \
             patch('AUTOMATION_API_SERVER.get_user_messages', return_value={'messages': []}), \
             patch('AUTOMATION_API_SERVER.get_autonomy_status', return_value={'state': {}, 'settings': {}}), \
             patch('AUTOMATION_API_SERVER.get_pipelines', return_value={'pipelines': []}), \
             patch('AUTOMATION_API_SERVER.get_campaigns', return_value={'campaigns': []}), \
             patch('AUTOMATION_API_SERVER.get_n8n_workflows', return_value={'workflows': []}), \
             patch('AUTOMATION_API_SERVER.get_transparency_report', return_value={'completed': []}), \
             patch('AUTOMATION_API_SERVER.get_content_briefs', return_value={'briefs': []}), \
             patch('AUTOMATION_API_SERVER.get_grants', return_value={'grants': []}), \
             patch('AUTOMATION_API_SERVER.get_pricing_experiments', return_value={'experiments': []}), \
             patch('AUTOMATION_API_SERVER.get_kpi_anomalies', return_value={'anomalies': []}), \
             patch('AUTOMATION_API_SERVER.weekly_brief', return_value={'summary': 'test'}):

            response = await AUTOMATION_API_SERVER.get_dashboard_all()

            expected_keys = [
                "status", "leads", "workflows", "agents", "tasks", "collab",
                "messages", "autonomy", "pipelines", "campaigns", "n8n",
                "transparency", "briefs", "grants", "experiments", "anomalies", "weekly"
            ]
            for key in expected_keys:
                self.assertIn(key, response)

    async def test_weekly_brief_cache(self):
        # Test that weekly_brief uses the cache
        AUTOMATION_API_SERVER._weekly_brief_cache = {"data": None, "timestamp": 0}

        # Mock revenue_engine and transparency_log/collab_feed
        mock_engine = MagicMock()

        # Define an async function for generate_ai_content
        async def mock_gen(s, u):
            return "AI Response"

        mock_engine.generate_ai_content = mock_gen

        with patch('AUTOMATION_API_SERVER.revenue_engine', mock_engine), \
             patch('AUTOMATION_API_SERVER.transparency_log', []), \
             patch('AUTOMATION_API_SERVER.collab_feed', []):

            # First call - should call generate_ai_content
            # We can't easily mock count of calls to async def mock_gen in a way that unittest.Mock works
            # So we use a counter in a wrapper
            call_count = 0
            original_gen = mock_engine.generate_ai_content
            async def wrapped_gen(s, u):
                nonlocal call_count
                call_count += 1
                return await original_gen(s, u)

            mock_engine.generate_ai_content = wrapped_gen

            res1 = await AUTOMATION_API_SERVER.weekly_brief()
            self.assertEqual(res1['summary'], "AI Response")
            self.assertEqual(call_count, 1)

            # Second call - should use cache
            res2 = await AUTOMATION_API_SERVER.weekly_brief()
            self.assertEqual(res2['summary'], "AI Response")
            self.assertEqual(call_count, 1) # Still 1

            # Manually expire cache
            AUTOMATION_API_SERVER._weekly_brief_cache["timestamp"] -= 61

            # Third call - should call generate_ai_content again
            res3 = await AUTOMATION_API_SERVER.weekly_brief()
            self.assertEqual(res3['summary'], "AI Response")
            self.assertEqual(call_count, 2)

if __name__ == '__main__':
    unittest.main()
