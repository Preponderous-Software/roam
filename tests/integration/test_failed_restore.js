#!/usr/bin/env node
// Integration test: a sync can never wipe a stored world (the tak#18 bug).
//
// The main thread used to REPLACE the whole IndexedDB store with each Worker
// sync (clear() + put), and the Worker synced even when its restore had failed,
// so after a restore that failed or skipped a file the first save erased every
// stored world. Now a sync only puts, a failed restore turns syncing off for
// the session (with a notice), and a stored world missing from the game's
// files is dropped only when the player deleted or renamed it.
//
//   1. IndexedDB cannot be opened by the Worker: play and save; every stored
//      record is unchanged and the notice is shown.
//   2. One stored file cannot be written back: the same.
//   3. Another tab stores a world after this tab restored: this tab's saves
//      keep it.
//   4. The player deletes a world in the game: it is dropped and stays dropped
//      after a reload.
//
// Usage: node tests/integration/test_failed_restore.js [URL]   (default :8080)
// Exit code: 0 = pass, 1 = fail.

"use strict";

const {
    BASE, launch, readIDB, seedIDB, toSeedRecords, waitForStatus, pressKey,
    newGameThenQuit, saveAndQuit, loadExistingSave, attachConsole,
} = require("./roamBrowser");

const worldsOf = (idb) => [...new Set(Object.keys(idb).map((k) => k.split("/")[2] || ""))].sort();
const sameRecords = (a, b) => JSON.stringify(Object.keys(a).sort().map((k) => [k, a[k]])) ===
                              JSON.stringify(Object.keys(b).sort().map((k) => [k, b[k]]));

let browser;
async function fail(msg) {
    process.stderr.write(`FAIL: ${msg}\n`);
    if (browser) await browser.close();
    process.exit(1);
}

async function boot(page) {
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail("the game did not start");
    await page.waitForTimeout(2000);
}

async function notice(page) {
    return page.evaluate(() => {
        const el = document.getElementById("saves-notice");
        return el ? el.textContent : null;
    });
}

// A context holding two stored worlds: one made by playing, and a copy of it
// under another name. Returns the page (at the title screen) and the records.
async function twoStoredWorlds(extra) {
    const ctx = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page = await ctx.newPage();
    attachConsole(page, []);
    await page.goto(`${BASE}/play`, { waitUntil: "domcontentloaded" });
    await boot(page);
    await newGameThenQuit(page);
    await page.waitForTimeout(3000);
    const played = toSeedRecords(await readIDB(page));
    if (!Object.keys(played).length) await fail("no world reached IndexedDB");
    const seed = { ...played };
    for (const [k, v] of Object.entries(played)) seed[k.replace(/^\/saves\/[^/]+\//, "/saves/precious/")] = v;
    Object.assign(seed, extra ? extra(seed) : {});
    await seedIDB(page, seed);
    return { ctx, page, stored: await readIDB(page) };
}

async function playAfterAFailedRestore(name, extra, setup) {
    process.stderr.write(`--- ${name}\n`);
    const { ctx, page, stored } = await twoStoredWorlds(extra);
    if (setup) await setup(ctx);
    await page.reload({ waitUntil: "domcontentloaded" });
    await boot(page);
    const shown = await notice(page);
    if (!shown || !/untouched/.test(shown)) await fail(`${name}: no saves notice (got ${JSON.stringify(shown)})`);
    await newGameThenQuit(page);
    await page.waitForTimeout(4000);
    const after = await readIDB(page);
    if (!sameRecords(after, stored)) {
        const lost = Object.keys(stored).filter((k) => !(k in after));
        await fail(`${name}: the store changed (lost ${lost.length}: ${lost.slice(0, 3).join(", ")})`);
    }
    process.stderr.write(`    ${Object.keys(stored).length} records unchanged, notice shown\n`);
    await ctx.close();
}

(async () => {
    process.stderr.write(`\n=== Roam failed-restore integration test ===\nTarget: ${BASE}\n\n`);
    browser = await launch();

    await playAfterAFailedRestore("1. IndexedDB cannot be opened", null, (ctx) =>
        ctx.route("**/web/game-worker.js", async (route) => {
            const response = await route.fetch();
            const body = "IDBFactory.prototype.open = function () { throw new Error('simulated IndexedDB failure'); };\n" +
                         (await response.text());
            await route.fulfill({ response, body });
        }));

    await playAfterAFailedRestore("2. one stored file cannot be written back", (seed) => {
        const file = Object.keys(seed).find((k) => k.startsWith("/saves/precious/") && k.endsWith(".json"));
        return { [file + "/cannot-restore"]: "x" };   // a path under a file
    });

    process.stderr.write("--- 3. another tab stores a world after this tab restored\n");
    const ctx = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page = await ctx.newPage();
    attachConsole(page, []);
    await page.goto(`${BASE}/play`, { waitUntil: "domcontentloaded" });
    await boot(page);
    await newGameThenQuit(page);
    await page.waitForTimeout(3000);
    const mine = toSeedRecords(await readIDB(page));
    const theirs = Object.fromEntries(Object.entries(mine).map(([k, v]) => [k.replace(/^\/saves\/[^/]+\//, "/saves/other-tab/"), v]));
    await page.evaluate((recs) => new Promise((resolve, reject) => {
        const req = indexedDB.open("roam-saves", 1);
        req.onerror = () => reject(req.error);
        req.onsuccess = (e) => {
            const db = e.target.result;
            const tx = db.transaction("files", "readwrite");
            for (const [k, v] of Object.entries(recs)) tx.objectStore("files").put(v, k);
            tx.oncomplete = () => { db.close(); resolve(); };
        };
    }), theirs);
    await loadExistingSave(page);
    await page.waitForTimeout(4000);
    await saveAndQuit(page);
    await page.waitForTimeout(3000);
    const afterPlay = await readIDB(page);
    if (!worldsOf(afterPlay).includes("other-tab")) await fail("3: this tab's save dropped the other tab's world");
    for (const k of Object.keys(theirs)) if (!(k in afterPlay)) await fail(`3: lost ${k}`);
    const myWorld = worldsOf(mine)[0];
    process.stderr.write(`    kept: ${worldsOf(afterPlay).join(", ")}\n`);

    process.stderr.write("--- 4. the player deletes a world\n");
    await pressKey(page, "Enter", 1, 2000);        // save selection (only this tab's world)
    await pressKey(page, "Backspace", 1, 1000);    // delete it...
    await pressKey(page, "Enter", 1, 3000);        // ...confirmed
    const afterDelete = await readIDB(page);
    if (worldsOf(afterDelete).includes(myWorld)) await fail(`4: the deleted world ${myWorld} is still stored`);
    if (!worldsOf(afterDelete).includes("other-tab")) await fail("4: deleting one world dropped another");
    await page.reload({ waitUntil: "domcontentloaded" });
    await boot(page);
    await page.waitForTimeout(3000);
    const afterReload = await readIDB(page);
    if (worldsOf(afterReload).includes(myWorld)) await fail("4: the deleted world came back after a reload");
    process.stderr.write(`    stored after the delete and a reload: ${worldsOf(afterReload).join(", ")}\n`);

    await browser.close();
    process.stderr.write("\nPASS\n");
})().catch(async (e) => { await fail(e && e.stack || String(e)); });
