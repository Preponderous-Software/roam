#!/usr/bin/env node
// Integration test: the opt-in 3D view's camera, camera-relative movement and
// 3D picking (Preponderous RFC 0021), driven by simulated keys and pointer
// events in /play?view=3d.
//
//   Movement: for each camera quadrant (turned with E), pressing W must make
//             the player face the grid direction "away from the camera"
//             (read back from the worldview messages).
//   Picking:  the page's raycast at each tile within 3 of the player, at its projected centre
//             returns that tile (or, when hidden, the wall/trunk/rock in
//             front of it), and hovering a tile makes the game itself (the
//             2D status line in its frames) name what is on it, which is only
//             possible if the pointed tile reached WorldScreen.
//   Fallback: under CI's software WebGL the "switch to 2D?" prompt appears
//             after 10 slow seconds; it is recorded and dismissed (Keep 3D).
//
// Usage: node tests/integration/test_view3d_controls.js [URL]
// Defaults to http://localhost:8080. ROAM_SHOTS=<dir> saves screenshots.

"use strict";

const path = require("path");
const { chromium } = require("playwright");
const { BASE, waitForStatus, pressKey, waitFor, attachConsole } = require("./roamBrowser");

const SHOTS = process.env.ROAM_SHOTS || "";
const OVERALL_TIMEOUT_MS = 12 * 60 * 1000;
let browser;
async function fail(msg) {
    process.stderr.write(`FAIL: ${msg}\n`);
    if (browser) await browser.close();
    process.exit(1);
}
// Screenshots are evidence, not assertions: a slow software renderer must
// not fail the test by timing one out.
async function shot(page, name) {
    if (!SHOTS) return;
    try { await page.screenshot({ path: path.join(SHOTS, name), timeout: 60000 }); }
    catch (e) { process.stderr.write(`  [screenshot ${name} skipped: ${e.message.split("\n")[0]}]\n`); }
}
setTimeout(() => fail(`timed out after ${OVERALL_TIMEOUT_MS / 60000} minutes`), OVERALL_TIMEOUT_MS).unref();

// Records the 2D frame strings the Worker posts, so the test can read what
// the game itself drew (its status line) without touching the page's code.
function recordFrames() {
    window.__frames = [];
    const NativeWorker = window.Worker;
    window.Worker = class extends NativeWorker {
        constructor(...args) {
            super(...args);
            this.addEventListener("message", (e) => {
                if (typeof e.data === "string") {
                    window.__frames.push(e.data);
                    if (window.__frames.length > 40) window.__frames.shift();
                }
            });
        }
    };
}

// Camera quadrant q (E turns it one step) -> facing after pressing W.
const FACING_AFTER_W = ["up", "left", "down", "right"];

(async () => {
    browser = await chromium.launch({
        headless: true,
        executablePath: process.env.ROAM_CHROMIUM || undefined,
        args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    });
    // Low graphics (no shadow maps) and a small viewport: CI renders WebGL in
    // software, and this test is about input, not looks.
    const ctx = await browser.newContext({ viewport: { width: 640, height: 480 } });
    const page = await ctx.newPage();
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    attachConsole(page);
    await page.addInitScript(recordFrames);
    await page.goto(BASE + "/play?view=3d&gfx=low", { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail("game did not start");
    await page.waitForTimeout(3000);
    await pressKey(page, "Enter", 3, 600);
    await pressKey(page, "ArrowDown", 1, 400);
    await pressKey(page, "Enter", 3, 800);
    if (!await waitFor(page, () => page.evaluate(() => window.__roam3dView && window.__roam3dView.applies >= 3), 90000)) {
        await fail("no worldview reached the 3D scene");
    }

    const step = (msg) => process.stderr.write(`  [step] ${msg}\n`);
    // --- fallback prompt (software WebGL is slow) ---------------------------
    const prompted = await waitFor(page, () => page.evaluate(() => !!document.getElementById("view3d-slow")), 45000, 1000);
    const fps = await page.evaluate(() => window.__roam3dView.fps);
    console.log(`fallback: prompt ${prompted ? "shown" : "not shown"} at ${fps} fps`);
    if (fps > 0 && fps < 12 && !prompted) await fail("slow 3D (under 12 fps) did not offer the 2D view");
    if (prompted) {
        await shot(page, "view3d-slow-prompt.png");
        // A DOM click, not page.click: under a starved software renderer
        // Playwright's actionability waits can time out.
        await page.evaluate(() => [...document.querySelectorAll("#view3d-slow button")]
            .find(b => b.textContent === "Keep 3D").click());
        if (await page.evaluate(() => !!document.getElementById("view3d-slow"))) await fail("Keep 3D did not close the prompt");
    }

    // Rendering is covered by test_view3d_flag.js; from here on the test is
    // about input, so drawing is paused to keep CI's software renderer from
    // starving the page (camera, picking and messages keep working).
    await page.evaluate(() => window.__roam3dScene.setRenderingPaused(true));

    // --- camera-relative movement -------------------------------------------
    for (let q = 0; q < 4; q++) {
        step(`quadrant ${q}: reading camera`);
        const cam = await page.evaluate(() => window.__roam3dScene.getCamera());
        step(`quadrant ${q}: camera ${JSON.stringify(cam)}; pressing W`);
        if (cam.quadrant !== q) await fail(`camera quadrant ${cam.quadrant}, expected ${q}`);
        await page.keyboard.down("w");
        await page.waitForTimeout(250);
        await page.keyboard.up("w");
        const facing = await waitFor(page, () => page.evaluate(want => {
            const s = window.__roam3dView.snapshot;
            return s && s.player.direction === want ? s.player.direction : null;
        }, FACING_AFTER_W[q]), 45000, 500);
        const now = await page.evaluate(() => window.__roam3dView.snapshot.player);
        console.log(`quadrant ${q}: W -> facing ${now.direction} (expected ${FACING_AFTER_W[q]}), tile ${JSON.stringify(now)}`);
        if (!facing) await fail(`quadrant ${q}: W made the player face ${now.direction}, expected ${FACING_AFTER_W[q]}`);
        if (q === 1) await shot(page, "view3d-quadrant1.png");
        await page.keyboard.press("e");  // next quadrant (consumed by the page)
        await page.waitForTimeout(600);
    }
    const back = await page.evaluate(() => window.__roam3dScene.getCamera().quadrant);
    if (back !== 0) await fail(`four E presses should return to quadrant 0, got ${back}`);

    // --- picking -------------------------------------------------------------
    // For every tile around the player, pick at its projected centre. A tile
    // whose top is visible must pick back to itself; one hidden behind a wall,
    // trunk or rock legitimately picks the occluder.
    const NAMES = { Grass: "Grass", WoodFloor: "Wood Floor", Stone: "Stone", OakWood: "Oak Wood",
                    Bed: "Bed", Torch: "Torch", Leaves: "Leaves", Apple: "Apple", CaveFloor: "Cave Floor" };
    const TALL = new Set(["OakWood", "JungleWood", "Stone", "CoalOre", "IronOre", "GoldOre", "Leaves"]);
    // In small batches: each raycast tests every triangle of the rooms in
    // view, and one long evaluate would starve the page under software GL.
    step("picking survey");
    const tiles = await page.evaluate(() => {
        const s = window.__roam3dView.snapshot, G = s.gridSize, P = s.player;
        const px = P.room[0] * G + P.x, py = P.room[1] * G + P.y, out = [];
        for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) if (dx || dy) out.push({ x: px + dx, y: py + dy });
        return out;
    });
    const survey = [];
    for (let i = 0; i < tiles.length; i += 8) {
        survey.push(...await page.evaluate(batch => batch.map(t => {
            const c = window.__roam3dScene.tileToClient(t.x, t.y);
            if (!c) return null;
            const hit = window.__roam3dScene.pick(c.x, c.y);
            return { t, c, hit: hit ? { world: hit.world, entities: hit.entities } : null };
        }).filter(Boolean), tiles.slice(i, i + 8)));
    }
    const matches = survey.filter(r => r.hit && r.hit.world[0] === r.t.x && r.hit.world[1] === r.t.y);
    const misses = survey.filter(r => !matches.includes(r));
    const unexplained = misses.filter(r => !(r.hit && r.hit.entities.some(e => TALL.has(e))));
    console.log(`pick: ${matches.length}/${survey.length} tiles around the player pick back to themselves; ` +
        `${misses.length - unexplained.length} hidden behind a wall/trunk/rock; unexplained: ${JSON.stringify(unexplained.slice(0, 5))}`);
    if (matches.length < 15) await fail(`only ${matches.length} tiles picked back to themselves`);
    if (unexplained.length) await fail(`picks that missed with no occluder: ${JSON.stringify(unexplained.slice(0, 5))}`);

    // The game must act on the picked tile: hover a visible tile whose first
    // entity's name is not on screen yet; the game's own status line must
    // then show that name (WorldScreen.handleMouseOver -> pointed tile).
    const onScreen = new Set(await page.evaluate(() => window.__frames.flatMap(f => {
        try { return JSON.parse(f).calls.filter(c => c.text).map(c => c.text); } catch (e) { return []; }
    })));
    let b = matches.find(r => r.hit.entities.length && NAMES[r.hit.entities[0]] && !onScreen.has(NAMES[r.hit.entities[0]]));
    if (!b) {
        // Everything near the player shares one name (all grass, say): look
        // further out for a visible tile whose first entity has another name.
        const far = await page.evaluate(([names, seen]) => {
            const s = window.__roam3dView.snapshot, G = s.gridSize, P = s.player;
            const px = P.room[0] * G + P.x, py = P.room[1] * G + P.y, out = [];
            for (const r of s.rooms) {
                if (r.z !== P.room[2]) continue;
                r.tiles.forEach((stack, i) => {
                    const first = stack.length ? s.classes[stack[0]] : null;
                    if (!first || !names[first] || seen.includes(names[first])) return;
                    const x = r.x * G + (i % G), y = r.y * G + Math.floor(i / G);
                    const d = Math.max(Math.abs(x - px), Math.abs(y - py));
                    if (d >= 1 && d <= 8) out.push({ x, y, d });
                });
            }
            return out.sort((a, b) => a.d - b.d).slice(0, 40);
        }, [NAMES, [...onScreen]]);
        for (let i = 0; i < far.length && !b; i += 8) {
            const got = await page.evaluate(batch => batch.map(t => {
                const c = window.__roam3dScene.tileToClient(t.x, t.y);
                const hit = c && window.__roam3dScene.pick(c.x, c.y);
                return hit && hit.world[0] === t.x && hit.world[1] === t.y ? { t, c, hit: { world: hit.world, entities: hit.entities } } : null;
            }).filter(Boolean), far.slice(i, i + 8));
            b = got[0];
        }
    }
    if (!b) await fail(`no visible tile whose name is not already on screen (${[...onScreen].slice(0, 6).join(", ")})`);
    step("hovering");
    await page.evaluate(() => { window.__frames.length = 0; });
    await page.mouse.move(b.c.x, b.c.y, { steps: 3 });
    const want = NAMES[b.hit.entities[0]];
    const said = await waitFor(page, () => page.evaluate(w =>
        window.__frames.some(f => f.includes(`"text":"${w}"`)), want), 20000, 500);
    const pointed = await page.evaluate(() => window.__roam3dView.pointed);
    console.log(`hover: tile ${JSON.stringify(b.t)} (${b.hit.entities.join("+")}); page sent ${JSON.stringify(pointed)}; ` +
        `game status named "${want}": ${!!said}`);
    if (!said) await fail(`hovering ${JSON.stringify(b.t)} in 3D did not make the game name "${want}"`);
    await shot(page, "view3d-hover.png");

    if (errors.length) await fail(`page errors: ${errors.join("; ")}`);
    await browser.close();
    console.log("PASS: camera-relative movement and 3D picking work in ?view=3d");
})().catch(e => fail(e.stack || String(e)));
