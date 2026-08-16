import requests
import time
import subprocess
import os
import signal

def test_weekly_brief_cache():
    url = "http://localhost:8080/api/weekly/brief"

    print("🚀 Starting benchmark...")

    # First call - should trigger AI generation (or template)
    print("First call (should be slower)...")
    start = time.time()
    resp1 = requests.get(url, timeout=30.0)
    duration1 = time.time() - start
    print(f"First call took: {duration1:.4f}s")

    # Second call - should be cached
    print("Second call (should be nearly instant)...")
    start = time.time()
    resp2 = requests.get(url, timeout=30.0)
    duration2 = time.time() - start
    print(f"Second call took: {duration2:.4f}s")

    if duration2 < duration1:
        print(f"✅ Success! Second call was {duration1/duration2:.1f}x faster.")
    else:
        print(f"⚠️ Note: Second call took {duration2:.4f}s (First: {duration1:.4f}s).")
        if duration2 < 0.1: # Threshold for "instant"
             print("✅ Success! Second call was nearly instant.")
        else:
             print("❌ Failure: Second call was not significantly faster.")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()
    print("✅ Response contents match.")

def main():
    # Set offline mode for consistent results without needing keys
    os.environ["CHATTY_OFFLINE_MODE"] = "true"

    # Start server
    server_process = subprocess.Popen(
        ["python3", "AUTOMATION_API_SERVER.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )

    print("Waiting for server to start...")
    # Give it a few seconds to boot
    time.sleep(5)

    try:
        test_weekly_brief_cache()
    finally:
        print("Shutting down server...")
        os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)

if __name__ == "__main__":
    main()
