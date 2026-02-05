
import asyncio
import time
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path to import AUTOMATION_API_SERVER
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Create a mock for revenue_engine with an async method
class MockRevenueEngine:
    def __init__(self):
        self.call_count = 0

    async def generate_ai_content(self, *args, **kwargs):
        self.call_count += 1
        await asyncio.sleep(0.5) # Simulate 0.5s AI latency
        return "Mocked AI Summary"

mock_re = MockRevenueEngine()

# Mock the entire module before importing AUTOMATION_API_SERVER
sys.modules['AUTOMATED_REVENUE_ENGINE'] = MagicMock()
import AUTOMATED_REVENUE_ENGINE
AUTOMATED_REVENUE_ENGINE.revenue_engine = mock_re

sys.modules['START_COMPLETE_AUTOMATION'] = MagicMock()
sys.modules['leads_storage'] = MagicMock()
sys.modules['transparency_log'] = MagicMock()

# Now we can import the app
import AUTOMATION_API_SERVER

# Replace the local revenue_engine if it exists
AUTOMATION_API_SERVER.revenue_engine = mock_re

async def run_benchmark():
    print("\n--- Benchmarking /api/weekly/brief ---")
    start_time = time.time()

    print("Call 1...")
    await AUTOMATION_API_SERVER.weekly_brief()

    print("Call 2...")
    await AUTOMATION_API_SERVER.weekly_brief()

    print("Call 3...")
    await AUTOMATION_API_SERVER.weekly_brief()

    end_time = time.time()
    total_duration = end_time - start_time
    print(f"Total time for 3 calls: {total_duration:.2f}s")
    print(f"Total AI calls: {mock_re.call_count}")

    print("\n--- Testing /api/dashboard/all ---")
    start_time = time.time()
    data = await AUTOMATION_API_SERVER.get_dashboard_all()
    end_time = time.time()

    print(f"Consolidated call time: {end_time - start_time:.2f}s")
    print(f"Data keys present: {list(data.keys())}")

    # Verify that the brief in consolidated data is also cached
    print("\nCalling /api/dashboard/all again...")
    start_time = time.time()
    await AUTOMATION_API_SERVER.get_dashboard_all()
    end_time = time.time()
    print(f"Second consolidated call time: {end_time - start_time:.2f}s")
    print(f"Total AI calls: {mock_re.call_count}") # Should still be 1 if it was called once before

if __name__ == "__main__":
    asyncio.run(run_benchmark())
