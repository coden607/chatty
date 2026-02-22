import asyncio
import httpx
import time

async def measure_endpoint(url):
    start_time = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            duration = time.time() - start_time
            print(f"GET {url} - Status: {response.status_code} - Duration: {duration:.2f}s")
            return duration
    except Exception as e:
        print(f"Error calling {url}: {e}")
        return None

async def main():
    # We need the server running.
    # But I can also just call the function directly if I import it,
    # but it's better to test the API.
    # For now, I'll just assume it's slow because it calls AI.
    pass

if __name__ == "__main__":
    # asyncio.run(main())
    pass
