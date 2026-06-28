// Web Worker: loads Pyodide, unpacks the game bundle, runs the Python game loop.
//
// Communication with the main thread:
//   main → worker:  { type: 'init', sab: SharedArrayBuffer }
//   worker → main:  string (JSON frame from WebRenderer.present())
//                   { type: 'status', msg: string }
//                   { type: 'ready' }
//                   { type: 'error', msg: string }
//
// Input arrives via the SharedArrayBuffer ring buffer (main thread writes,
// Python reads) so key/mouse events reach the game loop without depending on
// Worker onmessage, which cannot fire while Python is blocking.

importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.0/full/pyodide.js');

const SAB_RING_SIZE = 8192;

self.onmessage = async (e) => {
    if (e.data.type !== 'init') return;

    const { sab } = e.data;
    const sabMeta = new Int32Array(sab, 0, 2);        // [writeIdx, readIdx]
    const sabData = new Uint8Array(sab, 8, SAB_RING_SIZE);

    // Expose SAB and helpers to Python via globalThis (accessible as js.* in Pyodide)
    globalThis.sabMeta    = sabMeta;
    globalThis.sabData    = sabData;
    globalThis.sabRingSize = SAB_RING_SIZE;
    globalThis.sendToMain = (data) => self.postMessage(data);

    try {
        self.postMessage({ type: 'status', msg: 'Loading Python runtime…' });

        const pyodide = await loadPyodide({
            stdout: (msg) => console.log('[roam]', msg),
            stderr: (msg) => console.warn('[roam]', msg),
        });

        self.postMessage({ type: 'status', msg: 'Mounting save storage…' });

        // OPFS gives Python synchronous persistent file I/O without needing
        // Emscripten's async IDBFS flush cycle — saves survive page reloads and
        // are isolated per browser profile (no shared server filesystem).
        pyodide.FS.mkdir('/saves');
        try {
            const opfsRoot = await navigator.storage.getDirectory();
            await pyodide.mountNativeFS('/saves', opfsRoot);
        } catch {
            // OPFS not available in older browsers — saves are session-only
            console.warn('[roam] OPFS unavailable; saves will not persist across reloads');
        }

        self.postMessage({ type: 'status', msg: 'Downloading game…' });

        const resp = await fetch('/web/game.zip');
        if (!resp.ok) throw new Error(`game.zip fetch failed: ${resp.status}`);
        const buf = await resp.arrayBuffer();
        pyodide.FS.mkdir('/game');
        pyodide.unpackArchive(new Uint8Array(buf), 'zip', { extractDir: '/game' });

        self.postMessage({ type: 'status', msg: 'Starting game…' });

        // Run the game — this blocks for the lifetime of the session.
        await pyodide.runPythonAsync(`
import sys, os
sys.path.insert(0, '/game/src')
os.chdir('/game')
os.environ['ROAM_SAVE_DIR'] = '/saves'
exec(open('/game/web/pyodide_main.py').read())
`);

    } catch (err) {
        self.postMessage({ type: 'error', msg: String(err) });
    }
};
