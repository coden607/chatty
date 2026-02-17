import time
import asyncio
import httpx

API_BASE = "http://localhost:8080"
ENDPOINTS = [
    "/api/leads",
    "/api/narcoguard/workflows",
    "/api/agents",
    "/api/tasks",
    "/api/agents/collab",
    "/api/user/messages",
    "/api/autonomy/status",
    "/api/pipelines",
    "/api/campaigns",
    "/api/n8n/workflows",
    "/api/transparency/report",
    "/api/content/briefs",
    "/api/grants",
    "/api/experiments/pricing",
    "/api/kpi/anomalies",
    "/api/weekly/brief"
]

async def measure_sequential():
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        for ep in ENDPOINTS:
            try:
                await client.get(f"{API_BASE}{ep}", timeout=30)
            except Exception as e:
                # print(f"Error fetching {ep}: {e}")
                pass
    return time.time() - start_time

async def measure_parallel():
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"{API_BASE}{ep}", timeout=30) for ep in ENDPOINTS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return time.time() - start_time

async def main():
    print("--- Performance Baseline ---")
    try:
        # Test if server is up
        async with httpx.AsyncClient() as client:
            await client.get(f"{API_BASE}/api/health", timeout=5)
    except Exception:
        print("Server is not running. Measurement skipped.")
        return

    seq_time = await measure_sequential()
    print(f"Sequential requests (16): {seq_time:.4f}s")

    par_time = await measure_parallel()
    print(f"Parallel requests (16): {par_time:.4f}s")

    # After optimization, we will test the batch endpoint
    try:
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            resp = await client.get(f"{API_BASE}/api/dashboard/all", timeout=30)
            if resp.status_code == 200:
                batch_time = time.time() - start_time
                print(f"Batch request (1): {batch_time:.4f}s")
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())
