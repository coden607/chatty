
import asyncio
import time
import httpx
import os
import subprocess
import sys
from unittest.mock import MagicMock

async def measure_request(url):
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
        end_time = time.time()
        return end_time - start_time, response.status_code, response.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return None, None, None

async def main():
    # Start the server in the background
    env = os.environ.copy()
    env["CHATTY_OFFLINE_MODE"] = "true"
    env["PYTHONPATH"] = f"{env.get('PYTHONPATH', '')}:{os.getcwd()}"

    # We want to ensure we don't use real AI and we can see the cache effect.
    # The server will use AUTOMATED_REVENUE_ENGINE which we can't easily mock from here
    # without modifying the server code or using a wrapper.

    server_process = subprocess.Popen(
        ["python3", "AUTOMATION_API_SERVER.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for the server to start
    print("Waiting for server to start...")
    await asyncio.sleep(10)

    url = "http://localhost:8080/api/weekly/brief"

    print("Request 1...")
    duration1, status1, data1 = await measure_request(url)
    if duration1:
        print(f"Request 1 took {duration1:.4f} seconds, status {status1}")

    print("Request 2 (should hit cache)...")
    duration2, status2, data2 = await measure_request(url)
    if duration2:
        print(f"Request 2 took {duration2:.4f} seconds, status {status2}")

    if duration1 and duration2:
        if duration2 < duration1:
            print(f"✅ Success: Request 2 was {duration1/duration2:.1f}x faster than Request 1")
        else:
            print("❌ Failure: Request 2 was not faster than Request 1")

    # Terminate the server
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()

if __name__ == "__main__":
    asyncio.run(main())
