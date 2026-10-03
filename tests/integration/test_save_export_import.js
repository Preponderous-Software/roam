#!/usr/bin/env node
// Integration test: the Saves panel (web/saves.js) carries worlds between two
// browser profiles without losing or changing anything.
//
//   A  plays a new world, gets a binary map image seeded into it, and
//      downloads its saves through the panel.
//   B  plays its own, different world under the same name, then loads A's
//      file: B's world must be untouched, A's world must arrive byte for byte
//      as "<name>-imported", and a backup of B's saves must have been kept.
//   C  (empty) loads A's file: the world arrives under its own name, loads in
//      the game and plays on with no page error.
//   A damaged file and another format are refused with nothing changed and
//   the game still running.
//
// Usage:
//   node tests/integration/test_save_export_import.js [URL]
// Defaults to http://localhost:8080 and the page at /play (ROAM_PAGE=/ for a
// host that serves the page at its root, such as arcade).
//
// Exit code: 0 = pass, 1 = fail.

"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const {
    BASE, launch, readIDB, seedIDB, toSeedRecords, makePng, waitForStatus,
    newGameThenQuit, loadExistingSave, saveAndQuit, pressKey, waitFor, attachConsole,
} = require("./roamBrowser");

const PAGE = BASE + (process.env.ROAM_PAGE || "/play");
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "roam-saves-"));

let browser;
async function fail(msg) {
    process.stderr.write(`FAIL: ${msg}\n`);
    if (browser) await browser.close();
    process.exit(1);
}

async function profile(name) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, acceptDownloads: true });
    const page = await ctx.newPage();
    const errors = [];
    attachConsole(page);
    page.on("pageerror", (e) => { errors.push(e.message); process.stderr.write(`  [${name} pageerror] ${e.message}\n`); });
    await page.goto(PAGE, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail(`${name}: game did not start`);
    await page.waitForTimeout(2000);
    return { ctx, page, errors };
}

// Play a new world: start it, walk, gather, then save and quit to the title.
async function playNewWorld(page) {
    await newGameThenQuit(page);
    await loadExistingSave(page);
    await page.waitForTimeout(3000);
    await pressKey(page, "ArrowRight", 3, 300);
    await pressKey(page, "ArrowDown", 2, 300);
    await pressKey(page, "g", 2, 400);
    await saveAndQuit(page);
    const idb = await waitFor(page, async () => {
        const d = await readIDB(page);
        return Object.keys(d).length ? d : null;
    }, 30000);
    if (!idb) await fail("no saves reached IndexedDB");
    await page.waitForTimeout(3000);
    return readIDB(page);
}

function same(a, b) {
    return a && b && a.kind === b.kind && a.len === b.len && a.text === b.text && a.b64 === b.b64;
}

async function openPanel(page) {
    if (await page.locator(".roam-saves-dialog[open]").count()) return;
    await page.locator("#saves-desktop:visible, #saves-touch:visible").click();
    await page.waitForSelector(".roam-saves-dialog[open]");
}

async function loadFile(page, file) {
    await openPanel(page);
    const [chooser] = await Promise.all([
        page.waitForEvent("filechooser"),
        page.getByRole("button", { name: "Load saves from a file" }).click(),
    ]);
    await chooser.setFiles(file);
    await page.waitForTimeout(800);
    return page.locator(".roam-saves-dialog").innerText();
}

async function confirmAndReload(page) {
    await Promise.all([
        page.waitForEvent("load", { timeout: 30000 }),
        page.getByRole("button", { name: "Load and restart" }).click(),
    ]);
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail("game did not restart after loading saves");
    await page.waitForTimeout(2000);
}

(async () => {
    process.stderr.write(`\n=== Roam save export/import integration test ===\nTarget: ${PAGE}\n\n`);
    browser = await launch();

    // ── A: play, seed a binary map image, download ─────────────────────────────
    process.stderr.write("--- Profile A: play and download\n");
    const A = await profile("A");
    const played = await playNewWorld(A.page);
    const world = Object.keys(played)[0].split("/")[2];
    const png = makePng(32, 24);
    const seeded = toSeedRecords(played);
    seeded[`/saves/${world}/mapImage.png`] = { b64: png.toString("base64") };
    await seedIDB(A.page, seeded);   // at the title screen nothing syncs
    const aIdb = await readIDB(A.page);

    await openPanel(A.page);
    const [download] = await Promise.all([
        A.page.waitForEvent("download"),
        A.page.getByRole("button", { name: "Download my saves" }).click(),
    ]);
    const exportFile = path.join(TMP, download.suggestedFilename());
    await download.saveAs(exportFile);
    if (!/^roam-saves-\d{4}-\d\d-\d\d\.json$/.test(download.suggestedFilename())) {
        await fail(`unexpected download name ${download.suggestedFilename()}`);
    }
    const doc = JSON.parse(fs.readFileSync(exportFile, "utf8"));
    if (doc.format !== "roam-saves" || doc.version !== 1 || doc.game !== "roam") await fail("bad export header");
    for (const [k, v] of Object.entries(aIdb)) {
        const f = doc.files[k];
        const ok = v.kind === "text" ? f === v.text : f && f.base64 === v.b64;
        if (!ok) await fail(`export is missing or differs at ${k}`);
    }
    if (Object.keys(doc.files).length !== Object.keys(aIdb).length) await fail("export has extra files");
    // The game must still run after a download.
    await pressKey(A.page, "Escape", 1, 300);
    if ((await readIDB(A.page))[`/saves/${world}/mapImage.png`].b64 !== png.toString("base64")) {
        await fail("A's store changed after the download");
    }
    process.stderr.write(`PASS: A exported ${Object.keys(doc.files).length} files of world "${world}"\n`);

    // ── B: own world with the same name, then load A's file ───────────────────
    process.stderr.write("\n--- Profile B: same world name, load A's file\n");
    const B = await profile("B");
    const bBefore = await playNewWorld(B.page);
    if (!Object.keys(bBefore).every((k) => k.startsWith(`/saves/${world}/`))) {
        await fail(`B's world is not also called ${world}: ${Object.keys(bBefore).join(", ")}`);
    }

    // Refusals first: nothing changes and the game is not stopped.
    const junk = path.join(TMP, "junk.json");
    fs.writeFileSync(junk, "{not json");
    let text = await loadFile(B.page, junk);
    if (!/not a Roam saves file/.test(text)) await fail(`junk file not refused: ${text}`);
    const other = path.join(TMP, "other.json");
    fs.writeFileSync(other, JSON.stringify({ format: "tak-saves", version: 1, game: "tidewater-saves", files: { "/saves/x": "y" } }));
    text = await loadFile(B.page, other);
    if (!/not a Roam saves file/.test(text)) await fail(`other format not refused: ${text}`);
    const escape = path.join(TMP, "escape.json");
    fs.writeFileSync(escape, JSON.stringify({ format: "roam-saves", version: 1, game: "roam", files: { "/saves/../x": "y" } }));
    text = await loadFile(B.page, escape);
    if (!/Nothing was changed/.test(text)) await fail(`.. path not refused: ${text}`);
    await B.page.getByRole("button", { name: "Close" }).click();
    if (await B.page.evaluate(() => document.getElementById("bar-status").textContent.includes("Stopped"))) {
        await fail("a refused file stopped the game");
    }
    if (JSON.stringify(await readIDB(B.page)) !== JSON.stringify(bBefore)) await fail("a refused file changed B's saves");
    process.stderr.write("PASS: damaged, foreign and escaping files refused; nothing changed\n");

    text = await loadFile(B.page, exportFile);
    if (!text.includes(`${world} → ${world}-imported`)) await fail(`confirmation does not show the copy: ${text}`);
    await confirmAndReload(B.page);
    const bAfter = await readIDB(B.page);
    for (const [k, v] of Object.entries(bBefore)) {
        if (!same(bAfter[k], v)) await fail(`B's own ${k} changed or vanished`);
    }
    for (const [k, v] of Object.entries(aIdb)) {
        const moved = k.replace(`/saves/${world}/`, `/saves/${world}-imported/`);
        if (!same(bAfter[moved], v)) await fail(`${moved} did not arrive byte for byte`);
    }
    if (Object.keys(bAfter).length !== Object.keys(bBefore).length + Object.keys(aIdb).length) {
        await fail("B has unexpected extra files");
    }
    const backups = await B.page.evaluate(() => new Promise((resolve) => {
        const r = indexedDB.open("roam-saves.backups", 1);
        r.onsuccess = () => {
            const db = r.result;
            const q = db.transaction("backups", "readonly").objectStore("backups").getAll();
            q.onsuccess = () => { db.close(); resolve(q.result); };
        };
        r.onerror = () => resolve([]);
    }));
    if (backups.length !== 1 || Object.keys(backups[0].files).length !== Object.keys(bBefore).length) {
        await fail("no backup of B's saves was kept");
    }
    process.stderr.write(`PASS: B kept its "${world}" untouched; A's arrived as "${world}-imported" byte for byte; backup kept\n`);

    // Loading the same file again changes nothing.
    text = await loadFile(B.page, exportFile);
    if (!text.includes("already here, exactly the same")) await fail(`reload of same file: ${text}`);
    await B.page.getByRole("button", { name: "Close" }).click();

    // ── C: empty profile; the world arrives under its own name and plays ─────
    process.stderr.write("\n--- Profile C: load into an empty browser and play\n");
    const C = await profile("C");
    await loadFile(C.page, exportFile);
    await confirmAndReload(C.page);
    const cIdb = await readIDB(C.page);
    for (const [k, v] of Object.entries(aIdb)) if (!same(cIdb[k], v)) await fail(`C: ${k} differs`);
    if (Object.keys(cIdb).length !== Object.keys(aIdb).length) await fail("C has unexpected files");
    await loadExistingSave(C.page);
    await C.page.waitForTimeout(4000);
    await saveAndQuit(C.page);
    await C.page.waitForTimeout(3000);
    const cPlayed = await readIDB(C.page);
    const loc = `/saves/${world}/playerLocation.json`;
    if (!cPlayed[loc] || cPlayed[loc].text !== aIdb[loc].text) await fail("C did not resume at A's location");
    const inv = `/saves/${world}/playerInventory.json`;
    if (!cPlayed[inv] || cPlayed[inv].text !== aIdb[inv].text) await fail("C did not resume with A's inventory");

    for (const p of [A, B, C]) if (p.errors.length) await fail(`page errors: ${p.errors.join(" | ")}`);
    process.stderr.write("PASS: C loaded A's world and resumed with the same location and inventory; no page errors\n");
    await browser.close();
    process.exit(0);
})().catch((e) => fail(e.stack || String(e)));
