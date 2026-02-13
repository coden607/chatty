import sys
from unittest.mock import MagicMock, patch
import time
import asyncio

# Mock heavy dependencies
sys.modules["AUTOMATED_REVENUE_ENGINE"] = MagicMock()
sys.modules["AUTOMATED_CUSTOMER_ACQUISITION"] = MagicMock()
sys.modules["START_COMPLETE_AUTOMATION"] = MagicMock()

from AUTOMATION_API_SERVER import app
from fastapi.testclient import TestClient

client = TestClient(app)

endpoints = [
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

def benchmark_sequential():
    start_time = time.time()
    for endpoint in endpoints:
        client.get(endpoint)
    end_time = time.time()
    return (end_time - start_time) * 1000

def benchmark_batch():
    start_time = time.time()
    client.get("/api/dashboard/all")
    end_time = time.time()
    return (end_time - start_time) * 1000

if __name__ == "__main__":
    print("🚀 Benchmarking Dashboard Latency...")

    # Warm up
    client.get("/api/dashboard/all")

    seq_times = []
    batch_times = []

    for _ in range(5):
        seq_times.append(benchmark_sequential())
        batch_times.append(benchmark_batch())

    avg_seq = sum(seq_times) / len(seq_times)
    avg_batch = sum(batch_times) / len(batch_times)

    print(f"Average Sequential Latency (16 calls): {avg_seq:.2f}ms")
    print(f"Average Batch Latency (1 call): {avg_batch:.2f}ms")
    print(f"🚀 Improvement: {((avg_seq - avg_batch) / avg_seq) * 100:.1f}% reduction in latency")
    print(f"⚡ Performance gain: {avg_seq / avg_batch:.1f}x faster")
