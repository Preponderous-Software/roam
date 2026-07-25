// Web Worker: loads Pyodide, unpacks the game bundle, runs the Python game loop.
//
// Communication with the main thread:
//   main → worker:  { type: 'init', sab: SharedArrayBuffer }
//   worker → main:  string (JSON frame from WebRenderer.present())
//                   { type: 'status', msg: string }
//                   { type: 'ready' }
//                   { type: 'error', msg: string }
//                   { type: 'save', files: { path: content, ... } }
//
// Input arrives via the SharedArrayBuffer ring buffer (main thread writes,
// Python reads) so key/mouse events reach the game loop without depending on
// Worker onmessage, which cannot fire while Python is blocking.
//
// ── Why IDB writes live on the main thread ───────────────────────────────────
// Pyodide's CDN build uses Atomics.wait() for time.sleep() when SharedArrayBuffer
// is available. Atomics.wait blocks the Worker's JS event loop entirely, so IDB
// callbacks (macrotasks) can never fire while Python is running. Solution: the
// Worker walks /saves synchronously and postMessages the file map to the main
// thread; the main thread writes to IDB from its own (unblocked) event loop.
// The initial save restore still runs in the Worker because it happens before
// Python starts (no Atomics.wait yet), so IDB callbacks fire normally there.

importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.0/full/pyodide.js');

const SAB_RING_SIZE = 8192;

// ── Save restore: Worker reads IDB on startup (before Python blocks) ──────────

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

// Populate /saves from IndexedDB before Python starts.
// This runs entirely before runPythonAsync, so Atomics.wait is not yet active
// and the event loop is free to process IDB callbacks normally.
// Always resolves (never rejects) — a restore failure starts with empty saves.
async function loadSavesFromIDB(pyodide) {
    try {
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
            } catch(e) { reject(e); return; }
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
            const parts = path.split('/').filter(Boolean);
            let cur = '';
            for (let i = 0; i < parts.length - 1; i++) {
                cur += '/' + parts[i];
                try { pyodide.FS.mkdir(cur); } catch {}
            }
            try {
                if (content instanceof ArrayBuffer || ArrayBuffer.isView(content)) {
                    pyodide.FS.writeFile(path, new Uint8Array(content));
                } else {
                    pyodide.FS.writeFile(path, content, { encoding: 'utf8' });
                }
                n++;
            } catch(e) { console.warn('[roam] could not restore', path, e); }
        }
        if (n > 0) console.log(`[roam] ${n} save file(s) restored from IndexedDB`);
        try { db.close(); } catch {}

    } catch(err) {
        console.warn('[roam] save restore skipped (non-fatal):', err);
    }
}

// ── Save flush: Worker collects files and postMessages to main thread ─────────
// syncSaves walks /saves synchronously (safe while Python is blocked because
// pyodide.FS is pure JavaScript) and sends the file map to the main thread,
// which writes to IDB from its own event loop. self.postMessage is synchronous
// and does NOT require the Worker event loop to be running.

function makeSyncSaves(pyodide) {
    return () => {
        const files = {};
        function walk(path) {
            let entries;
            try { entries = pyodide.FS.readdir(path); } catch { return; }
            for (const name of entries) {
                if (name === '.' || name === '..') continue;
                const full = `${path}/${name}`;
                let stat;
                try { stat = pyodide.FS.stat(full); } catch { continue; }
                if ((stat.mode & 0o170000) === 0o040000) {
                    walk(full);
                } else {
                    // Try UTF-8 (JSON saves); fall back to binary (map PNGs).
                    try {
                        files[full] = pyodide.FS.readFile(full, { encoding: 'utf8' });
                    } catch {
                        try {
                            // ArrayBuffer is transferable — main thread can
                            // receive and write it to IDB without copying.
                            files[full] = pyodide.FS.readFile(full).buffer;
                        } catch {}
                    }
                }
            }
        }
        try { walk('/saves'); } catch {}
        // postMessage is synchronous from the Worker's perspective; no event
        // loop is needed.  The main thread queues and drains these on its own.
        self.postMessage({ type: 'save', files });
    };
}

// ── Worker entry point ────────────────────────────────────────────────────────

self.onmessage = async (e) => {
    if (e.data.type !== 'init') return;

    const { sab } = e.data;
    const sabMeta = new Int32Array(sab, 0, 2);
    const sabData = new Uint8Array(sab, 8, SAB_RING_SIZE);

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

        pyodide.FS.mkdir('/saves');
        await loadSavesFromIDB(pyodide);  // runs before Python; IDB works here

        // Wire syncSaves AFTER pyodide is initialised.
        globalThis.syncSaves = makeSyncSaves(pyodide);

        self.postMessage({ type: 'status', msg: 'Installing Python packages…' });

        await pyodide.loadPackage(['Pillow', 'jsonschema', 'micropip']);
        const micropip = pyodide.pyimport('micropip');
        await micropip.install('structlog');

        self.postMessage({ type: 'status', msg: 'Downloading game…' });

        // Fetch the content-hash written by build_zip.py so the zip URL is
        // unique per build. The browser may cache game.zip?v=<hash> freely;
        // a new deploy changes the hash, forcing a fresh download.
        let zipUrl = '/web/game.zip';
        try {
            const verResp = await fetch('/web/game_version.txt', { cache: 'no-store' });
            if (verResp.ok) zipUrl += '?v=' + (await verResp.text()).trim();
        } catch (_) { /* no version file — fall back to unversioned URL */ }

        const resp = await fetch(zipUrl);
        if (!resp.ok) throw new Error(`game.zip fetch failed: ${resp.status}`);
        const buf = await resp.arrayBuffer();
        pyodide.FS.mkdir('/game');
        pyodide.unpackArchive(new Uint8Array(buf), 'zip', { extractDir: '/game' });

        self.postMessage({ type: 'status', msg: 'Starting game…' });

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
