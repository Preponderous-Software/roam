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
        //
        // pyodide.mountNativeFS() returns { syncfs } — call syncfs() to flush
        // Emscripten's in-memory cache to the actual OPFS backing store.
        pyodide.FS.mkdir('/saves');
        let _nativeFSMount = null;
        try {
            const opfsRoot = await navigator.storage.getDirectory();
            _nativeFSMount = await pyodide.mountNativeFS('/saves', opfsRoot);
            console.log('[roam] OPFS mounted; saves will persist across reloads');
        } catch(err) {
            // OPFS not available in older browsers or non-secure contexts
            console.warn('[roam] OPFS unavailable; saves will not persist:', err);
        }

        // Expose syncSaves() to Python (accessible as js.syncSaves) so that
        // after every write the in-memory FS is flushed to OPFS.
        // Also called on a 3-second interval so saves persist even if the tab
        // is closed between explicit sync points.
        globalThis.syncSaves = () => {
            if (_nativeFSMount && typeof _nativeFSMount.syncfs === 'function') {
                _nativeFSMount.syncfs().catch(
                    (err) => console.warn('[roam] syncfs failed:', err)
                );
            }
        };
        // Periodic flush — fires during Python's time.sleep() yields.
        setInterval(syncSaves, 3000);

        self.postMessage({ type: 'status', msg: 'Installing Python packages…' });

        // Pillow and jsonschema are bundled with Pyodide; structlog comes from PyPI.
        // micropip handles PyPI installs and skips packages already available.
        await pyodide.loadPackage(['Pillow', 'jsonschema', 'micropip']);
        const micropip = pyodide.pyimport('micropip');
        await micropip.install('structlog');

        self.postMessage({ type: 'status', msg: 'Downloading game…' });

        const resp = await fetch('/web/game.zip');
        if (!resp.ok) throw new Error(`game.zip fetch failed: ${resp.status}`);
        const buf = await resp.arrayBuffer();
        pyodide.FS.mkdir('/game');
        pyodide.unpackArchive(new Uint8Array(buf), 'zip', { extractDir: '/game' });

        self.postMessage({ type: 'status', msg: 'Starting game…' });

        // Run the game — this blocks for the lifetime of the session.
        // /game/web/ is added to sys.path so pyodide_main.py can import
        // pyodide_compat (the synchronous ThreadPoolExecutor shim).
        await pyodide.runPythonAsync(`
import sys, os
sys.path.insert(0, '/game/src')
sys.path.insert(0, '/game/web')
os.chdir('/game')
os.environ['ROAM_SAVE_DIR'] = '/saves'
exec(open('/game/web/pyodide_main.py').read())
`);

    } catch (err) {
        self.postMessage({ type: 'error', msg: String(err) });
    }
};
