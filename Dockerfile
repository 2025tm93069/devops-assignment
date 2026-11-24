# ==========================================
# ACEest Fitness and Gym
# Dockerized Tkinter Application
# ==========================================

FROM python:3.12-slim

# Application directory
WORKDIR /app

# Install GUI and remote-display dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY start.sh .

# Make startup script executable
RUN python -c "from pathlib import Path; p = Path('start.sh'); p.write_bytes(p.read_bytes().replace(bytes((13, 10)), bytes((10,))))" \
    && chmod +x start.sh

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=6 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 6080), timeout=2); s.close()"

# noVNC web interface
EXPOSE 6080

# Start application
ENTRYPOINT ["/app/start.sh"]