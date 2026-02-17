import time
import asyncio
import httpx

API_BASE = "http://localhost:8080"

async def main():
    print("--- Caching Verification ---")
    async with httpx.AsyncClient() as client:
        # First call (cache miss)
        start = time.time()
        resp1 = await client.get(f"{API_BASE}/api/weekly/brief", timeout=30)
        print(f"First call (miss): {time.time() - start:.4f}s")

        # Second call (cache hit)
        start = time.time()
        resp2 = await client.get(f"{API_BASE}/api/weekly/brief", timeout=30)
        print(f"Second call (hit): {time.time() - start:.4f}s")

        if resp1.json() == resp2.json():
            print("Success: Cache returns identical data.")
        else:
            print("Warning: Cache data mismatch.")

if __name__ == "__main__":
    asyncio.run(main())
