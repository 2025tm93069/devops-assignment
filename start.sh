#!/bin/bash

set -e

export DISPLAY=:99

echo "Starting X virtual display..."
Xvfb :99 -screen 0 1280x800x24 &

sleep 2

echo "Starting Fluxbox window manager..."
fluxbox -display :99 &

sleep 2

echo "Starting VNC server..."
x11vnc \
    -display :99 \
    -forever \
    -shared \
    -rfbport 5900 \
    -nopw \
    -bg -no6 -novnc-nohttp

sleep 2

echo "Starting noVNC on port 6080..."
/usr/share/novnc/utils/novnc_proxy \
    --vnc localhost:5900 \
    --listen 6080 &

sleep 3

echo "Starting ACEest Fitness and Gym..."
exec python app.py