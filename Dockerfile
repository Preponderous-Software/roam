FROM python:3.10-slim

WORKDIR /app

COPY . .

# Build the Python game bundle downloaded by the browser's Pyodide Worker.
# game.zip contains all source code + schemas + config; assets are served
# separately over HTTP (they're large and already in the image via COPY).
RUN python3 web/build_zip.py

EXPOSE 8080

CMD ["python3", "web/serve.py"]
