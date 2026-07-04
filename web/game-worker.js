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

// ── Save persistence via IndexedDB ────────────────────────────────────────────
// Keys = Emscripten FS paths, values = UTF-8 file contents.
// Both operations are fully non-throwing: any error is caught and logged so
// the game always starts even when IDB is unavailable (mobile restrictions,
// private-browsing quotas, Ecosia WebView quirks, etc.).

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

// Populate /saves in the Emscripten in-memory FS from IndexedDB.
// Always resolves (never rejects) so a failed restore never prevents startup.
async function loadSavesFromIDB(pyodide) {
    try {
        // 5-second timeout guards against IDB hanging on some mobile WebViews.
        const db = await Promise.race([
            idbOpen(),
            new Promise((_, rej) =>
                setTimeout(() => rej(new Error('IDB open timeout')), 5000)
            ),
        ]);

        const entries = await new Promise((resolve, reject) => {
            const result  = [];
            let tx, cursorReq;
            try {
                tx        = db.transaction(IDB_STORE, 'readonly');
                cursorReq = tx.objectStore(IDB_STORE).openCursor();
            } catch(e) {
                // db.transaction() can throw synchronously on some WebViews.
                reject(e);
                return;
            }
            cursorReq.onsuccess = (ev) => {
                const c = ev.target.result;
                if (c) { result.push({ path: c.key, content: c.value }); c.continue(); }
                else   resolve(result);
            };
            cursorReq.onerror = () => reject(cursorReq.error);
            tx.onerror        = () => reject(tx.error);
            tx.onabort        = () => reject(new Error('IDB transaction aborted'));
        });

        let n = 0;
        for (const { path, content } of entries) {
            // Ensure every ancestor directory exists before writing the file.
            const parts = path.split('/').filter(Boolean);
            let cur = '';
            for (let i = 0; i < parts.length - 1; i++) {
                cur += '/' + parts[i];
                try { pyodide.FS.mkdir(cur); } catch {}
            }
            try { pyodide.FS.writeFile(path, content, { encoding: 'utf8' }); n++; }
            catch(e) { console.warn('[roam] could not restore', path, e); }
        }
        if (n > 0) console.log(`[roam] ${n} save file(s) restored from IndexedDB`);
        try { db.close(); } catch {}

    } catch(err) {
        // Non-fatal: game starts with an empty /saves.
        console.warn('[roam] save restore skipped:', err);
    }
}

// Walk /saves in the Emscripten FS and write every file to IndexedDB.
// Also always resolves — a failed flush is logged but never propagated.
async function flushSavesToIDB(pyodide) {
    const files = {};

    function walk(path) {
        let entries;
        try { entries = pyodide.FS.readdir(path); } catch { return; }
        for (const name of entries) {
            if (name === '.' || name === '..') continue;
            const full = `${path}/${name}`;
            let stat;
            try { stat = pyodide.FS.stat(full); } catch { continue; }
            if (pyodide.FS.isDir(stat.mode)) {
                walk(full);
            } else {
                // Binary files (e.g. map PNGs) are read as Uint8Array.
                // Text files (JSON saves) are read as UTF-8 strings.
                // We store them as-is; writeFile handles both types.
                try {
                    files[full] = pyodide.FS.readFile(full, { encoding: 'utf8' });
                } catch {
                    try { files[full] = pyodide.FS.readFile(full); } catch {}
                }
            }
        }
    }

    try { walk('/saves'); } catch {}

    try {
        const db = await Promise.race([
            idbOpen(),
            new Promise((_, rej) =>
                setTimeout(() => rej(new Error('IDB open timeout')), 5000)
            ),
        ]);

        await new Promise((resolve, reject) => {
            let tx;
            try {
                tx = db.transaction(IDB_STORE, 'readwrite');
            } catch(e) { reject(e); return; }
            tx.onerror    = () => reject(tx.error);
            tx.onabort    = () => reject(new Error('IDB flush aborted'));
            tx.oncomplete = () => resolve();
            const store = tx.objectStore(IDB_STORE);
            try { store.clear(); } catch {}
            for (const [path, content] of Object.entries(files)) {
                try { store.put(content, path); } catch {}
            }
        });

        try { db.close(); } catch {}

    } catch(err) {
        console.warn('[roam] IDB flush failed:', err);
    }
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

        // Create /saves in the Emscripten in-memory FS, then pre-populate it
        // from IndexedDB so Python sees prior-session save slots on startup.
        pyodide.FS.mkdir('/saves');
        await loadSavesFromIDB(pyodide);  // always resolves; never throws

        // syncSaves is exposed to Python (js.syncSaves) and is fire-and-forget.
        // It is also called every 3 s as a backstop for unexpected exits.
        globalThis.syncSaves = () => {
            flushSavesToIDB(pyodide);  // errors handled inside; never throws
        };
        setInterval(syncSaves, 3000);

        self.postMessage({ type: 'status', msg: 'Installing Python packages…' });

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
