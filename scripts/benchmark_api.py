import asyncio
import time
import httpx

async def benchmark():
    async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
        endpoints = [
            "/api/status",
            "/api/revenue",
            "/api/leads",
            "/api/narcoguard/workflows",
            "/api/agents",
            "/api/autonomy/status",
            "/api/pipelines",
            "/api/campaigns",
            "/api/n8n/workflows",
            "/api/transparency/report",
            "/api/content/briefs",
            "/api/grants",
            "/api/experiments/pricing",
            "/api/kpi/anomalies",
            "/api/weekly/brief",
            "/api/tasks",
            "/api/agents/collab",
            "/api/user/messages"
        ]

        print(f"Benchmarking {len(endpoints)} endpoints...")

        # Sequential
        start = time.perf_counter()
        for ep in endpoints:
            try:
                await client.get(ep)
            except Exception as e:
                print(f"Error sequential {ep}: {e}")
        end = time.perf_counter()
        seq_time = end - start
        print(f"Sequential Total: {seq_time:.4f}s")

        # Parallel (Simulated Browser)
        start = time.perf_counter()
        await asyncio.gather(*[client.get(ep) for ep in endpoints], return_exceptions=True)
        end = time.perf_counter()
        par_time = end - start
        print(f"Parallel (Browser-style): {par_time:.4f}s")

        # Batch (Bolt ⚡ optimization)
        start = time.perf_counter()
        try:
            await client.get("/api/dashboard/all")
        except Exception as e:
            print(f"Error batch: {e}")
        end = time.perf_counter()
        batch_time = end - start
        print(f"Batch API (Bolt ⚡): {batch_time:.4f}s")

        print("-" * 30)
        print(f"Latency Reduction vs Sequential: {(1 - batch_time/seq_time)*100:.1f}%")
        print(f"Latency Reduction vs Parallel: {(1 - batch_time/par_time)*100:.1f}%")

if __name__ == "__main__":
    try:
        asyncio.run(benchmark())
    except Exception as e:
        print(f"Error: {e}")
