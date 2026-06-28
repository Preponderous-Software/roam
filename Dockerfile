FROM python:3.10-slim

WORKDIR /app

COPY . .

# Build the Python game bundle downloaded by the browser's Pyodide Worker.
# game.zip contains all source code + schemas + config; assets are served
# separately over HTTP (they're large and already in the image via COPY).
RUN python3 -c "
import zipfile, os

with zipfile.ZipFile('web/game.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk('src'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if not f.endswith('.pyc'):
                path = os.path.join(root, f)
                z.write(path, path)
    for root, dirs, files in os.walk('schemas'):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            z.write(os.path.join(root, f), os.path.join(root, f))
    for name in ('config.yml', 'version.txt'):
        if os.path.exists(name):
            z.write(name, name)
print('Built web/game.zip')
"

EXPOSE 8080

CMD ["python3", "web/serve.py"]
