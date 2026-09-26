#!/usr/bin/env node
// Integration test: verifies save files written during gameplay persist across
// a page reload via IndexedDB — including binary files, which must come back
// from IndexedDB into the game's filesystem, and back out again, byte-for-byte.
//
// The web build does not currently stitch a minimap (WebRenderer.saveImage is
// a no-op), so the binary file is seeded: a real PNG is placed in IndexedDB as
// the save's mapImage.png, the page is reloaded, and the Worker's first sync
// after loading the save must carry those exact bytes (IDB → FS → IDB).
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

const {
    BASE, launch, installSaveMessageRecorder, readIDB, seedIDB, toSeedRecords,
    makePng, saveMessages, waitForStatus, newGameThenQuit, loadExistingSave, saveAndQuit,
    waitFor, isCompletePng, attachConsole,
} = require("./roamBrowser");

const MAP_IMAGE = "/saves/defaultsavefile/mapImage.png";

(async () => {
    process.stderr.write(`\n=== Roam save-persistence integration test ===\n`);
    process.stderr.write(`Target: ${BASE}\n\n`);

    const browser = await launch();
    const ctx = await browser.newContext({
        viewport: { width: 412, height: 915 },
        userAgent: "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    });
    await ctx.addInitScript(installSaveMessageRecorder);
    const page = await ctx.newPage();
    const logs = [];
    const pageErrors = [];
    attachConsole(page, logs);
    page.on("pageerror", e => { pageErrors.push(e.message); process.stderr.write(`  [pageerror] ${e.message}\n`); });

    const fail = async (msg) => {
        process.stderr.write(`FAIL: ${msg}\n`);
        await browser.close();
        process.exit(1);
    };

    // ── Load #1 ────────────────────────────────────────────────────────────────
    process.stderr.write("--- Load\n");
    await page.goto(`${BASE}/play`, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 120000)) {
        await fail("game did not reach Starting game…");
    }
    await page.waitForTimeout(2000);

    // ── New game → world → save and quit to title ─────────────────────────────
    process.stderr.write("--- New game, then save and quit\n");
    await newGameThenQuit(page);

    process.stderr.write("--- Polling IndexedDB\n");
    const polled = await waitFor(page, async () => {
        const idb = await readIDB(page);
        return Object.keys(idb).length ? idb : null;
    }, 30000);
    if (!polled) await fail("no save files reached IndexedDB after 30s of gameplay");
    await page.waitForTimeout(3000);   // let any trailing sync settle
    const saved = await readIDB(page);

    for (const [k, v] of Object.entries(saved)) {
        if (!k.endsWith(".json")) continue;
        if (v.kind !== "text") await fail(`${k} was stored as ${v.kind}, expected text`);
        try { JSON.parse(v.text); } catch (e) { await fail(`${k} in IndexedDB is not valid JSON: ${e.message}`); }
    }

    // ── Seed a real PNG as the save's map image (binary record) ───────────────
    const png = makePng(64, 48);
    const pngB64 = png.toString("base64");
    const seeded = toSeedRecords(saved);
    seeded[MAP_IMAGE] = { b64: pngB64 };
    await seedIDB(page, seeded);
    const idb1 = await readIDB(page);

    process.stderr.write(`\n[IDB before reload — ${Object.keys(idb1).length} file(s)]\n`);
    for (const [k, v] of Object.entries(idb1)) process.stderr.write(`  ${k} (${v.kind}, ${v.len})\n`);
    if (idb1[MAP_IMAGE].kind !== "bytes" || idb1[MAP_IMAGE].b64 !== pngB64) {
        await fail("could not seed the binary map image record");
    }

    // ── Reload ─────────────────────────────────────────────────────────────────
    process.stderr.write("\n--- Reload\n");
    await page.reload({ waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 120000)) {
        await fail("game did not restart after reload");
    }
    await page.waitForTimeout(2000);

    const idb2 = await readIDB(page);
    process.stderr.write(`\n[IDB after reload — ${Object.keys(idb2).length} file(s)]\n`);
    for (const [k, v] of Object.entries(idb2)) process.stderr.write(`  ${k} (${v.kind}, ${v.len})\n`);

    const k1 = Object.keys(idb1).sort();
    const k2 = Object.keys(idb2).sort();
    if (!(k1.every(k => k2.includes(k)) && k2.length >= k1.length)) {
        await fail(`before [${k1.join(", ")}] vs after [${k2.join(", ")}]`);
    }
    if (!logs.some(l => l.includes(`[roam] ${k1.length} save file(s) restored from IndexedDB`))) {
        await fail(`Worker did not report restoring ${k1.length} save file(s)`);
    }

    // ── Load the save; the Worker's syncs show what it restored ──────────────
    process.stderr.write("\n--- Loading the save after reload\n");
    await loadExistingSave(page);
    // An existing world is not saved on entry; save and quit so the Worker
    // syncs what it restored (the first sync after loading).
    await page.waitForTimeout(5000);
    await saveAndQuit(page);
    const msgs = await waitFor(page, async () => {
        const m = await saveMessages(page);
        return m.length ? m : null;
    }, 60000);
    if (!msgs) await fail("no save sync from the Worker after loading the save");
    const restored = msgs[0];

    // The main thread writes each sync to IDB; the record must still be bytes.
    await page.waitForTimeout(3000);
    const idb3 = await readIDB(page);

    process.stderr.write("\n--- Verdict\n");
    const missing = k1.filter(k => !(k in restored));
    if (missing.length) await fail(`files missing from the restored FS: ${missing.join(", ")}`);
    const fsPng = restored[MAP_IMAGE];
    if (fsPng.kind !== "bytes" || fsPng.b64 !== pngB64) {
        await fail(`${MAP_IMAGE} did not survive IDB → FS → sync: ${png.length} bytes in, ${fsPng.kind} ${fsPng.len} out`);
    }
    const idbPng = idb3[MAP_IMAGE];
    if (!idbPng || idbPng.kind !== "bytes" || idbPng.b64 !== pngB64 || !isCompletePng(idbPng.b64)) {
        await fail(`${MAP_IMAGE} did not survive FS → IDB: ${idbPng ? idbPng.kind + " " + idbPng.len : "missing"}`);
    }
    if (logs.some(l => l.includes("map image unreadable"))) {
        await fail("the game could not read the restored map image");
    }
    if (pageErrors.length) await fail(`page errors: ${pageErrors.join(" | ")}`);

    process.stderr.write(`PASS: ${k1.length} save file(s) persisted and restored across reload\n`);
    k1.forEach(k => process.stderr.write(`  ${k}\n`));
    process.stderr.write(`PASS: ${MAP_IMAGE} round-tripped IDB → FS → IDB byte-identically (${png.length} bytes)\n`);
    await browser.close();
    process.exit(0);
})();
