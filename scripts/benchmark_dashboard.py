
import asyncio
import httpx
import time

API_BASE = "http://localhost:8080"
ENDPOINTS = [
    "/api/leads",
    "/api/narcoguard/workflows",
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

async def benchmark_sequential():
    async with httpx.AsyncClient() as client:
        start = time.time()
        for endpoint in ENDPOINTS:
            try:
                await client.get(f"{API_BASE}{endpoint}", timeout=30)
            except Exception as e:
                print(f"Error fetching {endpoint}: {e}")
        end = time.time()
        return end - start

async def benchmark_parallel():
    async with httpx.AsyncClient() as client:
        start = time.time()
        tasks = [client.get(f"{API_BASE}{endpoint}", timeout=30) for endpoint in ENDPOINTS]
        await asyncio.gather(*tasks)
        end = time.time()
        return end - start

async def benchmark_batch():
    async with httpx.AsyncClient() as client:
        start = time.time()
        try:
            await client.get(f"{API_BASE}/api/dashboard/all", timeout=30)
        except Exception as e:
            print(f"Error fetching batch: {e}")
        end = time.time()
        return end - start

async def main():
    print("Starting benchmark (sequential)...")
    seq_time = await benchmark_sequential()
    print(f"Sequential time: {seq_time:.4f}s")

    print("Starting benchmark (parallel)...")
    par_time = await benchmark_parallel()
    print(f"Parallel time: {par_time:.4f}s")

    print("Starting benchmark (batch)...")
    batch_time = await benchmark_batch()
    print(f"Batch time: {batch_time:.4f}s")

    print(f"Sequential vs Batch improvement: {((seq_time - batch_time) / seq_time) * 100:.2f}%")
    print(f"Parallel vs Batch improvement: {((par_time - batch_time) / par_time) * 100:.2f}%")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Benchmark failed: {e}. Is the server running?")
