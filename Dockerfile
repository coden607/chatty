# CHATTY Complete Automation System - Docker Container
# Runs 24/7 autonomous AI automation with all components

FROM python:3.11-slim-bookworm

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs generated_content chroma_db temp_audio tmp

# Create non-root user for security
RUN useradd -m -u 1000 chatty && \
    chown -R chatty:chatty /app
USER chatty

# Expose ports
EXPOSE 8000 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command: Run continuous mode
CMD ["python3", "CHATTY_CONTINUOUS_MODE.py"]
