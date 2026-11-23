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

# Copy application files
COPY app.py .
COPY start.sh .

# Make startup script executable
RUN chmod +x start.sh

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DISPLAY=:99

# noVNC web interface
EXPOSE 6080

# Start application
ENTRYPOINT ["/app/start.sh"]