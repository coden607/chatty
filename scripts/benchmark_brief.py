import time
import requests
import json
import subprocess
import os

def run_benchmark():
    url = "http://localhost:8080/api/weekly/brief"

    print("Starting server...")
    env = os.environ.copy()
    env["CHATTY_OFFLINE_MODE"] = "true" # Keep it fast for testing but we can simulate delay
    server_proc = subprocess.Popen(
        ["python3", "-m", "uvicorn", "AUTOMATION_API_SERVER:app", "--host", "0.0.0.0", "--port", "8080"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )

    # Wait for server to start
    max_retries = 10
    for i in range(max_retries):
        try:
            requests.get("http://localhost:8080/api/health")
            print("Server is up!")
            break
        except:
            time.sleep(1)
    else:
        print("Server failed to start")
        server_proc.terminate()
        return

    print("Running benchmark for /api/weekly/brief...")

    times = []
    for i in range(5):
        start = time.time()
        response = requests.get(url)
        end = time.time()
        elapsed = end - start
        times.append(elapsed)
        print(f"Request {i+1}: {elapsed:.4f}s")

    avg_time = sum(times) / len(times)
    print(f"Average time: {avg_time:.4f}s")

    server_proc.terminate()

if __name__ == "__main__":
    run_benchmark()
