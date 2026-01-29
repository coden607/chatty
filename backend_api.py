"""
Backend API stub for the CHATTY automation orchestration.
Provides lightweight placeholders so automation health checks succeed.
"""

from fastapi import FastAPI

app = FastAPI(title="NarcoGuard Automation Backend")


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}

