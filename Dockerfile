FROM python:3.10-slim

WORKDIR /app

# SDL2 libs required by pygame even when running headless (web mode)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsdl2-2.0-0 \
        libsdl2-image-2.0-0 \
        libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Suppress pygame display errors — web mode never opens a window
ENV PYGAME_HIDE_SUPPORT_PROMPT=1
ENV SDL_VIDEODRIVER=dummy
ENV SDL_AUDIODRIVER=dummy

# HTTP game server + WebSocket server
EXPOSE 8282 8766

# Save files written to /data; mount a volume here for persistence
ENV ROAM_SAVE_DIR=/data
RUN mkdir -p /data

CMD ["python3", "src/roam.py", "--web"]
