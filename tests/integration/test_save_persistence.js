#!/usr/bin/env node
// Integration test: verifies save files written during gameplay persist across
// a page reload via IndexedDB.
//
// Usage:
//   node tests/integration/test_save_persistence.js [URL]
//
// Defaults to http://localhost:8080.  Pass the live URL to test production:
//   ROAM_URL=https://roam.preponderous.org node tests/integration/test_save_persistence.js
//
// Exit code: 0 = pass, 1 = fail.
// Requires: npm install -g playwright && npx playwright install chromium

"use strict";

const { chromium } = require("playwright");

const BASE = process.env.ROAM_URL || process.argv[2] || "http://localhost:8080";

async function readIDB(page) {
    return page.evaluate(() => new Promise((resolve) => {
        const req = indexedDB.open("roam-saves", 1);
        req.onerror = () => resolve({});
        req.onsuccess = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains("files")) { db.close(); resolve({}); return; }
            const result = {};
            const tx = db.transaction("files", "readonly");
            const cursor = tx.objectStore("files").openCursor();
            cursor.onsuccess = (ev) => {
                const c = ev.target.result;
                if (c) { result[c.key] = String(c.value).length; c.continue(); }
                else   { db.close(); resolve(result); }
            };
            cursor.onerror = () => { db.close(); resolve(result); };
        };
    })).catch(() => ({}));
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

(async () => {
    process.stderr.write(`\n=== Roam save-persistence integration test ===\n`);
    process.stderr.write(`Target: ${BASE}\n\n`);

    const browser = await chromium.launch({ headless: true });
    const ctx = await browser.newContext({
        viewport: { width: 412, height: 915 },
        userAgent: "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    });
    const page = await ctx.newPage();

    page.on("console", msg => {
        const t = msg.type() === "error" ? "ERR" : msg.type() === "warning" ? "WARN" : "LOG";
        process.stderr.write(`  [browser:${t}] ${msg.text()}\n`);
    });
    page.on("pageerror", e => process.stderr.write(`  [pageerror] ${e.message}\n`));

    // ── Load #1 ────────────────────────────────────────────────────────────────
    process.stderr.write("--- Load\n");
    await page.goto(`${BASE}/play`, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 120000)) {
        process.stderr.write("FAIL: game did not reach Starting game…\n");
        await browser.close(); process.exit(1);
    }
    await page.waitForTimeout(2000);

    // ── Navigate into world (title → save select → world) ─────────────────────
    process.stderr.write("--- Navigating into world\n");
    await pressKey(page, "Enter", 3, 600);
    await pressKey(page, "ArrowDown", 1, 400);
    await pressKey(page, "Enter", 3, 800);
    await page.waitForTimeout(2000);

    // ── Poll IDB until files appear ────────────────────────────────────────────
    process.stderr.write("--- Polling IndexedDB\n");
    let idb1 = {};
    for (let i = 0; i < 30; i++) {
        await page.waitForTimeout(1000);
        idb1 = await readIDB(page);
        if (Object.keys(idb1).length > 0) {
            process.stderr.write(`  files appeared after ${i+1}s\n`);
            break;
        }
    }

    if (Object.keys(idb1).length === 0) {
        process.stderr.write("FAIL: no save files reached IndexedDB after 30s of gameplay\n");
        await browser.close(); process.exit(1);
    }

    process.stderr.write(`\n[IDB before reload — ${Object.keys(idb1).length} file(s)]\n`);
    for (const [k, v] of Object.entries(idb1)) process.stderr.write(`  ${k} (${v} chars)\n`);

    // ── Reload ─────────────────────────────────────────────────────────────────
    process.stderr.write("\n--- Reload\n");
    await page.reload({ waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 120000)) {
        process.stderr.write("FAIL: game did not restart after reload\n");
        await browser.close(); process.exit(1);
    }
    await page.waitForTimeout(2000);

    const idb2 = await readIDB(page);
    process.stderr.write(`\n[IDB after reload — ${Object.keys(idb2).length} file(s)]\n`);
    for (const [k, v] of Object.entries(idb2)) process.stderr.write(`  ${k} (${v} chars)\n`);

    // ── Verdict ────────────────────────────────────────────────────────────────
    process.stderr.write("\n--- Verdict\n");
    const k1 = Object.keys(idb1).sort();
    const k2 = Object.keys(idb2).sort();
    const allRestored = k1.every(k => k2.includes(k));

    if (allRestored && k2.length >= k1.length) {
        process.stderr.write(`PASS: ${k1.length} save file(s) persisted and restored across reload\n`);
        k1.forEach(k => process.stderr.write(`  ${k}\n`));
        await browser.close();
        process.exit(0);
    } else {
        process.stderr.write(`FAIL: before [${k1.join(", ")}] vs after [${k2.join(", ")}]\n`);
        await browser.close();
        process.exit(1);
    }
})();
