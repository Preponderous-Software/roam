// Shared Playwright helpers for the browser save integration tests.
//
// Save records in IndexedDB ('roam-saves' / 'files', keyed by FS path) are
// either strings (UTF-8 text files: the JSON saves) or ArrayBuffers (binary
// files: map PNGs). See encodeSaveRecord() in web/game-worker.js.

"use strict";

const { chromium } = require("playwright");

const BASE = process.env.ROAM_URL || process.argv[2] || "http://localhost:8080";

async function launch() {
    // ROAM_CHROMIUM lets a local run point at a specific Chromium binary; CI
    // uses the Playwright-managed one.
    return chromium.launch({
        headless: true,
        executablePath: process.env.ROAM_CHROMIUM || undefined,
    });
}

// Installed as an init script: records every { type: 'save' } message the
// game Worker posts, i.e. the /saves tree as read from the Emscripten FS.
// The first message after a (re)load therefore shows what the Worker restored
// from IndexedDB into the FS. Resets on every navigation.
function installSaveMessageRecorder() {
    window.__roamSaveMessages = [];
    const NativeWorker = window.Worker;
    window.Worker = class extends NativeWorker {
        constructor(...args) {
            super(...args);
            this.addEventListener("message", (e) => {
                const d = e.data;
                if (d && typeof d === "object" && d.type === "save") {
                    window.__roamSaveMessages.push(d.files);
                }
            });
        }
    };
}

// Normalise a record/file value to { kind, len, b64 } inside the page.
const DESCRIBE_FN = `(v) => {
    if (typeof v === "string") {
        return { kind: "text", len: v.length, text: v };
    }
    const u8 = v instanceof ArrayBuffer ? new Uint8Array(v)
             : ArrayBuffer.isView(v) ? new Uint8Array(v.buffer, v.byteOffset, v.byteLength)
             : null;
    if (!u8) return { kind: "other", len: 0 };
    let s = "";
    for (let i = 0; i < u8.length; i += 0x8000) {
        s += String.fromCharCode.apply(null, u8.subarray(i, i + 0x8000));
    }
    return { kind: "bytes", len: u8.length, b64: btoa(s) };
}`;

// Full contents of the IDB store: { path: { kind, len, text | b64 } }.
async function readIDB(page) {
    return page.evaluate((describeSrc) => new Promise((resolve) => {
        const describe = eval(describeSrc);
        const req = indexedDB.open("roam-saves", 1);
        req.onerror = () => resolve({});
        req.onsuccess = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains("files")) { db.close(); resolve({}); return; }
            const result = {};
            const cursor = db.transaction("files", "readonly").objectStore("files").openCursor();
            cursor.onsuccess = (ev) => {
                const c = ev.target.result;
                if (c) { result[c.key] = describe(c.value); c.continue(); }
                else   { db.close(); resolve(result); }
            };
            cursor.onerror = () => { db.close(); resolve(result); };
        };
    }), DESCRIBE_FN).catch(() => ({}));
}

// The Worker's save messages since the last navigation, described like readIDB.
async function saveMessages(page) {
    return page.evaluate((describeSrc) => {
        const describe = eval(describeSrc);
        return (window.__roamSaveMessages || []).map((files) => {
            const out = {};
            for (const [k, v] of Object.entries(files)) out[k] = describe(v);
            return out;
        });
    }, DESCRIBE_FN);
}

async function waitForStatus(page, target, maxMs = 120000) {
    const deadline = Date.now() + maxMs;
    let last = "";
    while (Date.now() < deadline) {
        const s = await page.evaluate(() => {
            const el = document.getElementById("bar-status");
            return el ? el.textContent.trim() : "";
        }).catch(() => "");
        if (s !== last) { process.stderr.write(`  [status] ${s}\n`); last = s; }
        if (s === target) return true;
        const err = await page.evaluate(() => {
            const el = document.getElementById("error");
            return (el && el.style.display !== "none") ? el.textContent.trim() : "";
        }).catch(() => "");
        if (err) { process.stderr.write(`  [error] ${err}\n`); return false; }
        await page.waitForTimeout(500);
    }
    process.stderr.write(`  [timeout] never reached status "${target}"\n`);
    return false;
}

async function pressKey(page, key, times = 1, delay = 400) {
    for (let i = 0; i < times; i++) {
        await page.keyboard.press(key);
        await page.waitForTimeout(delay);
    }
}

// Title → new save → world (the new world is saved on entry), then save and
// quit back to the title screen. At the title screen the game writes nothing,
// so IndexedDB can be inspected or seeded without a sync racing it.
async function newGameThenQuit(page) {
    await pressKey(page, "Enter", 3, 600);
    await pressKey(page, "ArrowDown", 1, 400);
    await pressKey(page, "Enter", 3, 800);
    await page.waitForTimeout(5000);
    await saveAndQuit(page);
}

// World → options → save and return to the title screen. Saving on the way
// out is synchronous, so this always ends with a Worker sync of /saves.
async function saveAndQuit(page) {
    await pressKey(page, "Escape", 1, 1500);
    await pressKey(page, "Enter", 1, 1500);
    await pressKey(page, "Enter", 1, 3000);
}

// Title → save select → load the first (existing) save.
async function loadExistingSave(page) {
    await pressKey(page, "Enter", 1, 2000);
    await pressKey(page, "Enter", 1, 1500);
}

async function waitFor(page, fn, maxMs, stepMs = 1000) {
    const deadline = Date.now() + maxMs;
    while (Date.now() < deadline) {
        const v = await fn();
        if (v) return v;
        await page.waitForTimeout(stepMs);
    }
    return null;
}

// A small but real PNG (RGB, deflate-compressed, CRC-checked chunks). The
// signature's 0x89 byte and the NUL bytes in the chunk lengths are exactly what
// the old utf8 read mangled, so it exercises the binary path end to end.
function makePng(width, height) {
    const zlib = require("zlib");
    const crcTable = [];
    for (let n = 0; n < 256; n++) {
        let c = n;
        for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
        crcTable.push(c >>> 0);
    }
    const crc32 = (buf) => {
        let c = 0xffffffff;
        for (const b of buf) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8);
        return (c ^ 0xffffffff) >>> 0;
    };
    const chunk = (type, data) => {
        const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
        const td = Buffer.concat([Buffer.from(type, "latin1"), data]);
        const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td));
        return Buffer.concat([len, td, crc]);
    };
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(width, 0); ihdr.writeUInt32BE(height, 4);
    ihdr[8] = 8; ihdr[9] = 2; // 8-bit RGB
    const rows = [];
    for (let y = 0; y < height; y++) {
        const row = Buffer.alloc(1 + width * 3);
        for (let x = 0; x < width; x++) {
            row[1 + x * 3] = (x * 37 + y * 11) & 0xff;
            row[2 + x * 3] = (x * y) & 0xff;
            row[3 + x * 3] = 0xff - ((x + y) & 0xff);
        }
        rows.push(row);
    }
    return Buffer.concat([
        Buffer.from(PNG_SIGNATURE),
        chunk("IHDR", ihdr),
        chunk("IDAT", zlib.deflateSync(Buffer.concat(rows))),
        chunk("IEND", Buffer.alloc(0)),
    ]);
}

// Replace the whole IDB store. Values given as { b64 } are stored as an
// ArrayBuffer (the binary record format); strings are stored as-is (the text
// record format, and the only format the pre-fix code ever wrote).
async function seedIDB(page, records) {
    return page.evaluate((recs) => new Promise((resolve, reject) => {
        const decoded = {};
        for (const [k, v] of Object.entries(recs)) {
            if (typeof v === "string") { decoded[k] = v; continue; }
            const bin = atob(v.b64);
            const u8 = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
            decoded[k] = u8.buffer;
        }
        const req = indexedDB.open("roam-saves", 1);
        req.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains("files")) db.createObjectStore("files");
        };
        req.onerror = () => reject(req.error);
        req.onsuccess = (e) => {
            const db = e.target.result;
            const tx = db.transaction("files", "readwrite");
            const store = tx.objectStore("files");
            store.clear();
            for (const [k, v] of Object.entries(decoded)) store.put(v, k);
            tx.oncomplete = () => { db.close(); resolve(); };
            tx.onerror = () => { db.close(); reject(tx.error); };
        };
    }), records);
}

// IDB snapshot (from readIDB) → raw records accepted by seedIDB.
function toSeedRecords(idb) {
    const out = {};
    for (const [k, v] of Object.entries(idb)) out[k] = v.kind === "bytes" ? { b64: v.b64 } : v.text;
    return out;
}

const PNG_SIGNATURE = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];

// True when b64 decodes to a structurally complete PNG (signature + IEND).
function isCompletePng(b64) {
    const buf = Buffer.from(b64 || "", "base64");
    if (buf.length < PNG_SIGNATURE.length + 12) return false;
    if (!PNG_SIGNATURE.every((b, i) => buf[i] === b)) return false;
    return buf.subarray(buf.length - 8, buf.length - 4).toString("latin1") === "IEND";
}

function stripAnsi(s) {
    return s.replace(/\x1b\[[0-9;]*m/g, "");
}

function attachConsole(page, sink) {
    page.on("console", (msg) => {
        const t = msg.type() === "error" ? "ERR" : msg.type() === "warning" ? "WARN" : "LOG";
        const text = msg.text();
        if (sink) sink.push(stripAnsi(text));
        process.stderr.write(`  [browser:${t}] ${text}\n`);
    });
}

module.exports = {
    BASE, launch, installSaveMessageRecorder, readIDB, seedIDB, toSeedRecords, makePng, saveMessages,
    waitForStatus, pressKey, newGameThenQuit, saveAndQuit, loadExistingSave, waitFor,
    isCompletePng, attachConsole,
};
