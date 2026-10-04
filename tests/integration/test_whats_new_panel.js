#!/usr/bin/env node
// Integration test: the What's new panel (web/whats-new.js) shows the entries
// built from CHANGELOG.md and never touches the saves.
//
//   Desktop: play a world and quit to the title, snapshot IndexedDB, open the
//            panel from the footer, check its entries, press game keys while it
//            is open, close it, and require IndexedDB to be byte-identical and
//            the game still running. The "unseen" dot is gone after a reload.
//   Touch:   (iPhone 13 profile) the button sits in the d-pad; a real tap opens
//            the panel and a tap on Close shuts it, with no page error.
//
// Usage:
//   node tests/integration/test_whats_new_panel.js [URL]
// Defaults to http://localhost:8080 and the page at /play (ROAM_PAGE=/ for a
// host that serves the page at its root, such as arcade). ROAM_SHOTS=<dir>
// saves screenshots of each step there.
//
// Exit code: 0 = pass, 1 = fail.

"use strict";

const path = require("path");
const { devices } = require("playwright");
const {
    BASE, launch, readIDB, waitForStatus, newGameThenQuit, pressKey, waitFor, attachConsole,
} = require("./roamBrowser");

const PAGE = BASE + (process.env.ROAM_PAGE || "/play");
const SHOTS = process.env.ROAM_SHOTS || "";
// Headless Chromium's own UA already marks it as a bot to arcade's play
// counter; the phone profile's UA does not, so it is tagged "monitor".
const UA_SUFFIX = " roam-integration-monitor";

let browser;
async function fail(msg) {
    process.stderr.write(`FAIL: ${msg}\n`);
    if (browser) await browser.close();
    process.exit(1);
}

async function shot(page, name) {
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, `whats-new-${name}.png`) });
}

async function expectedEntries() {
    const response = await fetch(BASE + "/web/whats-new.json");
    if (!response.ok) await fail(`/web/whats-new.json answered ${response.status}`);
    const body = await response.json();
    if (!Array.isArray(body.entries) || !body.entries.length) await fail("whats-new.json has no entries");
    return body.entries;
}

async function open(page, context) {
    const errors = [];
    attachConsole(page);
    page.on("pageerror", (e) => { errors.push(e.message); process.stderr.write(`  [${context} pageerror] ${e.message}\n`); });
    await page.goto(PAGE, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail(`${context}: game did not start`);
    await page.waitForTimeout(2000);
    return errors;
}

function same(a, b) {
    return JSON.stringify(a) === JSON.stringify(b);
}

(async () => {
    process.stderr.write(`\n=== Roam What's new panel integration test ===\nTarget: ${PAGE}\n\n`);
    const entries = await expectedEntries();
    browser = await launch();

    // ── Desktop ───────────────────────────────────────────────────────────────
    process.stderr.write("--- Desktop\n");
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await ctx.newPage();
    const errors = await open(page, "desktop");
    await newGameThenQuit(page);
    const before = await waitFor(page, async () => {
        const d = await readIDB(page);
        return Object.keys(d).length ? d : null;
    }, 30000);
    if (!before) await fail("no saves reached IndexedDB");
    await page.waitForTimeout(3000);
    const snapshot = await readIDB(page);

    const button = page.locator("#whats-new-desktop");
    if (!await button.isVisible()) await fail("the desktop What's new button is not visible");
    if (!await button.evaluate((el) => el.classList.contains("roam-whats-new-unseen"))) {
        await fail("a first visit should show the unseen dot");
    }
    await shot(page, "desktop-closed");
    await button.click();
    await page.waitForSelector(".roam-whats-new-dialog[open]");
    const items = await page.locator(".roam-whats-new-dialog li").allInnerTexts();
    if (items.length !== entries.length) await fail(`panel shows ${items.length} entries, expected ${entries.length}`);
    for (const [i, entry] of entries.entries()) {
        if (!items[i].includes(entry.title)) await fail(`entry ${i} lacks its title "${entry.title}"`);
    }
    await shot(page, "desktop-open");
    // Game keys while the panel is open must not reach the game (Enter here
    // would start loading a world at the title screen).
    await pressKey(page, "ArrowDown", 2, 200);
    await pressKey(page, "Enter", 1, 1500);
    if (!await page.locator(".roam-whats-new-dialog[open]").count()) {
        // Enter on the focused heading does nothing; the panel stays open.
        await fail("Enter closed the panel or reached something else");
    }
    await page.keyboard.press("Escape");
    await page.waitForTimeout(500);
    if (await page.locator(".roam-whats-new-dialog[open]").count()) await fail("Escape did not close the panel");
    await page.waitForTimeout(2000);
    if (!same(await readIDB(page), snapshot)) await fail("IndexedDB changed while the panel was used");
    process.stderr.write(`PASS: desktop panel listed ${items.length} entries; IndexedDB untouched\n`);

    await page.reload({ waitUntil: "domcontentloaded" });
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail("game did not restart after reload");
    await page.waitForTimeout(2000);
    if (await page.locator("#whats-new-desktop").evaluate((el) => el.classList.contains("roam-whats-new-unseen"))) {
        await fail("the unseen dot came back after the panel was read");
    }
    if (!same(await readIDB(page), snapshot)) await fail("IndexedDB changed after a reload");
    if (errors.length) await fail(`desktop page errors: ${errors.join("; ")}`);
    process.stderr.write("PASS: dot cleared after reading; saves unchanged after reload\n");
    await ctx.close();

    // ── Touch (iPhone 13 profile) ────────────────────────────────────────────
    process.stderr.write("--- Touch\n");
    const phone = devices["iPhone 13"];
    const tctx = await browser.newContext({ ...phone, userAgent: phone.userAgent + UA_SUFFIX });
    const tpage = await tctx.newPage();
    const terrors = await open(tpage, "touch");
    const tbutton = tpage.locator("#whats-new-touch");
    if (!await tbutton.isVisible()) await fail("the touch What's new button is not visible");
    if (await tpage.locator("#whats-new-desktop").count()) await fail("the desktop button is present on touch");
    await shot(tpage, "phone-closed");
    await tbutton.tap();
    await tpage.waitForSelector(".roam-whats-new-dialog[open]");
    await tpage.waitForTimeout(400);
    await shot(tpage, "phone-open");
    await tpage.locator(".roam-whats-new-dialog").getByRole("button", { name: "Close" }).tap();
    await tpage.waitForTimeout(500);
    if (await tpage.locator(".roam-whats-new-dialog[open]").count()) await fail("tapping Close did not close the panel");
    if (terrors.length) await fail(`touch page errors: ${terrors.join("; ")}`);
    process.stderr.write("PASS: touch button opens and closes the panel by tap\n");

    await browser.close();
    process.stderr.write("\nAll What's new checks passed.\n");
    process.exit(0);
})().catch((e) => fail(e && e.stack || String(e)));
