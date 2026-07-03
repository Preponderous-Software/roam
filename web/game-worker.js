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

// ── Save persistence via raw IndexedDB ────────────────────────────────────────
// localStorage is not available in Workers; Emscripten's IDBFS/OPFS backends
// are unreliable in Pyodide 0.26 (IDBFS may not be bundled; OPFS Access Handle
// Pool FS only opens handles for files that already exist at mount time).
// Direct IndexedDB from the Worker is the simplest approach that is guaranteed
// to work across sessions and browser vendors.
//
// Layout: one database ("roam-saves"), one object store ("files").
// Keys = Emscripten FS paths ("/saves/slot1/player.json"), values = content.
//
// Two operations:
//   loadSavesFromIDB(pyodide)  — called once at startup, awaited before Python
//   syncSaves()                — flushes /saves snapshot to IDB; called after
//                                every write (from Python) + on a 3 s interval

const IDB_NAME    = 'roam-saves';
const IDB_STORE   = 'files';
const IDB_VERSION = 1;

function idbOpen() {
    return new Promise((resolve, reject) => {
        const req = indexedDB.open(IDB_NAME, IDB_VERSION);
        req.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(IDB_STORE)) {
                db.createObjectStore(IDB_STORE);
            }
        };
        req.onsuccess = (e) => resolve(e.target.result);
        req.onerror   = (e) => reject(e.target.error);
    });
}

async function loadSavesFromIDB(pyodide) {
    let db;
    try { db = await idbOpen(); }
    catch(err) { console.warn('[roam] IDB open failed on load:', err); return; }

    await new Promise((resolve) => {
        const tx      = db.transaction(IDB_STORE, 'readonly');
        const store   = tx.objectStore(IDB_STORE);
        const keysReq = store.getAllKeys();
        const valsReq = store.getAll();
        let keys = null, vals = null;

        function done() {
            if (keys === null || vals === null) return;
            let n = 0;
            for (let i = 0; i < keys.length; i++) {
                const path  = keys[i];
                const value = vals[i];
                // Ensure all ancestor directories exist
                const parts = path.split('/').filter(Boolean);
                let cur = '';
                for (let j = 0; j < parts.length - 1; j++) {
                    cur += '/' + parts[j];
                    try { pyodide.FS.mkdir(cur); } catch {}
                }
                try {
                    pyodide.FS.writeFile(path, value, { encoding: 'utf8' });
                    n++;
                } catch(e) { console.warn('[roam] could not restore', path, e); }
            }
            if (n > 0) console.log(`[roam] ${n} save file(s) restored from IndexedDB`);
            resolve();
        }

        keysReq.onsuccess = () => { keys = keysReq.result; done(); };
        valsReq.onsuccess = () => { vals = valsReq.result; done(); };
        keysReq.onerror   = () => resolve();
        valsReq.onerror   = () => resolve();
    });
    db.close();
}

function flushSavesToIDB(pyodide) {
    // Walk /saves and snapshot every file into a flat path→content map.
    const files = {};
    function walk(path) {
        let entries;
        try { entries = pyodide.FS.readdir(path); } catch { return; }
        for (const name of entries) {
            if (name === '.' || name === '..') continue;
            const full = `${path}/${name}`;
            const stat = pyodide.FS.stat(full);
            if (pyodide.FS.isDir(stat.mode)) {
                walk(full);
            } else {
                try { files[full] = pyodide.FS.readFile(full, { encoding: 'utf8' }); }
                catch {}
            }
        }
    }
    walk('/saves');

    return new Promise((resolve) => {
        idbOpen()
            .then((db) => {
                const tx    = db.transaction(IDB_STORE, 'readwrite');
                const store = tx.objectStore(IDB_STORE);
                store.clear();
                for (const [path, content] of Object.entries(files)) {
                    store.put(content, path);
                }
                tx.oncomplete = () => { db.close(); resolve(); };
                tx.onerror    = () => { db.close(); resolve(); };
            })
            .catch(() => resolve());
    });
}

// ── Worker entry point ────────────────────────────────────────────────────────

self.onmessage = async (e) => {
    if (e.data.type !== 'init') return;

    const { sab } = e.data;
    const sabMeta = new Int32Array(sab, 0, 2);        // [writeIdx, readIdx]
    const sabData = new Uint8Array(sab, 8, SAB_RING_SIZE);

    // Expose SAB and helpers to Python via globalThis (accessible as js.* in Pyodide)
    globalThis.sabMeta     = sabMeta;
    globalThis.sabData     = sabData;
    globalThis.sabRingSize = SAB_RING_SIZE;
    globalThis.sendToMain  = (data) => self.postMessage(data);

    try {
        self.postMessage({ type: 'status', msg: 'Loading Python runtime…' });

        const pyodide = await loadPyodide({
            stdout: (msg) => console.log('[roam]', msg),
            stderr: (msg) => console.warn('[roam]', msg),
        });

        self.postMessage({ type: 'status', msg: 'Restoring saves…' });

        // Create /saves in the Emscripten in-memory FS, then populate it with
        // any files written in prior sessions.  This must be awaited before
        // Python starts so the save-selection screen sees existing slots.
        pyodide.FS.mkdir('/saves');
        await loadSavesFromIDB(pyodide);

        // syncSaves() is exposed to Python (js.syncSaves) and called:
        //   • immediately after every writeJsonAtomically (via _try_opfs_sync)
        //   • every 3 s as a backstop for unexpected exits
        //   • explicitly at end of session in pyodide_main.py
        globalThis.syncSaves = () => {
            flushSavesToIDB(pyodide).catch(
                (err) => console.warn('[roam] IDB flush failed:', err)
            );
        };
        setInterval(syncSaves, 3000);

        self.postMessage({ type: 'status', msg: 'Installing Python packages…' });

        // Pillow and jsonschema are bundled with Pyodide; structlog comes from PyPI.
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
