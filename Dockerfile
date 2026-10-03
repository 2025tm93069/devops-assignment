FROM python:3.12-slim

WORKDIR /app

# Install GUI and VNC/noVNC dependencies
RUN apt-get update && apt-get install -y \
    python3-tk \
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# noVNC web interface
EXPOSE 6080

CMD ["bash", "-c", "\
    Xvfb :99 -screen 0 1280x800x24 & \
    sleep 2 && \
    fluxbox -display :99 & \
    sleep 2 && \
    x11vnc -display :99 -forever -shared -rfbport 5900 -nopw -bg && \
    sleep 2 && \
    /usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 6080 & \
    sleep 3 && \
    python app.py \
"]