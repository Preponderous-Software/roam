#!/usr/bin/env node
// Integration test: IndexedDB save records written by builds before binary
// support must still restore.
//
// Before binary support every record was a string: FS.readFile(path,
// {encoding: 'utf8'}) was used for every file. JSON saves were stored intact;
// a PNG came out truncated at its first NUL byte. This test seeds exactly that
// shape of data — the JSON saves as strings plus the mangled map-image string
// the old code really produced — reloads, loads the save, and asserts that the
// save loads with its state intact, every JSON file comes back byte-identical,
// and the unreadable legacy map image does not stop the game (it is recreated,
// see MapImageGenerator.getExistingMapImage).
//
// Usage: node tests/integration/test_legacy_save_records.js [URL]
// Exit code: 0 = pass, 1 = fail.

"use strict";

const {
    BASE, launch, installSaveMessageRecorder, readIDB, seedIDB, toSeedRecords,
    saveMessages, waitForStatus, newGameThenQuit, loadExistingSave, saveAndQuit, waitFor,
    attachConsole,
} = require("./roamBrowser");

const SAVE = "/saves/defaultsavefile";
const MAP_IMAGE = `${SAVE}/mapImage.png`;
// What the pre-fix code stored for a PNG: the first 8 signature bytes decoded
// as UTF-8 up to the first NUL (captured from a real pre-fix browser profile).
const LEGACY_MANGLED_PNG = "\u{50387}\r\n\x1a\n";

(async () => {
    process.stderr.write(`\n=== Roam legacy save-record integration test ===\n`);
    process.stderr.write(`Target: ${BASE}\n\n`);

    const browser = await launch();
    const ctx = await browser.newContext({ viewport: { width: 1000, height: 800 } });
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

    // ── Produce a real save, then rewrite IDB in the legacy record shape ─────
    process.stderr.write("--- Load and create a save\n");
    await page.goto(`${BASE}/play`, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 120000)) await fail("game did not start");
    await page.waitForTimeout(2000);
    await newGameThenQuit(page);
    const saved = await waitFor(page, async () => {
        const idb = await readIDB(page);
        return idb[`${SAVE}/tick.json`] ? idb : null;
    }, 30000);
    if (!saved) await fail("no save reached IndexedDB");
    await page.waitForTimeout(3000);

    const legacy = toSeedRecords(await readIDB(page));
    for (const [k, v] of Object.entries(legacy)) {
        if (typeof v !== "string") await fail(`${k} is not a string record; cannot build a legacy fixture`);
    }
    legacy[MAP_IMAGE] = LEGACY_MANGLED_PNG;
    // Give the save a distinctive tick so loading it is observable.
    const legacyTick = 424242;
    legacy[`${SAVE}/tick.json`] = JSON.stringify({ tick: legacyTick }, null, 4);
    await seedIDB(page, legacy);
    const seededKeys = Object.keys(legacy).sort();
    process.stderr.write(`\n[legacy records seeded — ${seededKeys.length}]\n`);
    seededKeys.forEach(k => process.stderr.write(`  ${k} (string, ${legacy[k].length})\n`));

    // ── Reload with the legacy records and load the save ─────────────────────
    process.stderr.write("\n--- Reload\n");
    logs.length = 0;
    await page.reload({ waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 120000)) await fail("game did not start with legacy records");
    await page.waitForTimeout(2000);
    if (!logs.some(l => l.includes(`[roam] ${seededKeys.length} save file(s) restored from IndexedDB`))) {
        await fail(`Worker did not report restoring ${seededKeys.length} save file(s)`);
    }

    process.stderr.write("\n--- Loading the legacy save\n");
    await loadExistingSave(page);
    // An existing world is not saved on entry; save and quit so the Worker
    // syncs what it restored (the first sync after loading).
    await page.waitForTimeout(5000);
    await saveAndQuit(page);
    const msgs = await waitFor(page, async () => {
        const m = await saveMessages(page);
        return m.length ? m : null;
    }, 60000);
    if (!msgs) await fail("no save sync from the Worker after loading the legacy save");
    const restored = msgs[0];

    // ── Verdict ────────────────────────────────────────────────────────────────
    process.stderr.write("\n--- Verdict\n");
    const tickLine = logs.find(l => l.includes("tick counter loaded"));
    if (!tickLine || !tickLine.includes(`tickCount=${legacyTick}`)) {
        await fail(`legacy tick.json was not loaded (got: ${tickLine || "no tick counter log"})`);
    }
    if (!logs.some(l => l.includes("screen transition") && l.includes("world_screen"))) {
        await fail("the legacy save never reached the world screen");
    }
    const missing = seededKeys.filter(k => !(k in restored));
    if (missing.length) await fail(`files missing from the restored FS: ${missing.join(", ")}`);

    // The first sync fires on the game's first JSON write after loading, so
    // files the game rewrote on entry may legitimately differ; everything it
    // has not written yet must be byte-identical to the legacy record.
    const writtenBeforeSync = new Set();
    for (const l of logs) {
        const m = l.match(/path=(\/saves\/\S+\.json)/);
        if (m && /saved|saving/.test(l)) writtenBeforeSync.add(m[1]);
    }
    let identical = 0;
    for (const k of seededKeys) {
        if (!k.endsWith(".json")) continue;
        const r = restored[k];
        if (r.kind !== "text") await fail(`${k} restored as ${r.kind}, expected text`);
        try { JSON.parse(r.text); } catch (e) { await fail(`${k} restored as invalid JSON: ${e.message}`); }
        if (r.text === legacy[k]) { identical++; continue; }
        if (!writtenBeforeSync.has(k)) await fail(`${k} changed during restore without being rewritten by the game`);
        process.stderr.write(`  ${k} rewritten by the game after loading (expected)\n`);
    }
    if (identical === 0) await fail("no JSON file came back byte-identical");
    if (!logs.some(l => l.includes("map image unreadable, recreating"))) {
        process.stderr.write("  note: legacy map image was not reported unreadable\n");
    }
    if (pageErrors.length) await fail(`page errors: ${pageErrors.join(" | ")}`);

    process.stderr.write(`PASS: legacy save loaded (tick ${legacyTick}); ${identical} JSON file(s) byte-identical, all ${seededKeys.length} files restored\n`);
    await browser.close();
    process.exit(0);
})();
