#!/usr/bin/env node
// Integration test: the browser game's opt-in 3D view (RFC 0017 stage 3).
//
//   Default /play: the 2D game boots and enters a world exactly as before, and
//                  the page never requests three.js or web/roam3d.js, creates
//                  no 3D canvas and receives no worldview message.
//   /play?view=3d: the game enters a world, the Worker sends worldview
//                  messages (a full one first), the 3D canvas draws a
//                  non-empty frame behind the 2D HUD, and nothing errors.
//                  Reports FPS and the Worker's measured build cost; in CI
//                  the GPU is SwiftShader, so FPS is a floor, not a threshold.
//
// Usage:
//   node tests/integration/test_view3d_flag.js [URL]
// Defaults to http://localhost:8080. ROAM_SHOTS=<dir> saves screenshots.
//
// Exit code: 0 = pass, 1 = fail.

"use strict";

const path = require("path");
const { chromium } = require("playwright");
const { BASE, waitForStatus, pressKey, waitFor, attachConsole } = require("./roamBrowser");

const SHOTS = process.env.ROAM_SHOTS || "";
const THREE_D_URL = /three(\.min)?\.js|\/web\/roam3d\.js/;

let browser;
async function fail(msg) {
    process.stderr.write(`FAIL: ${msg}\n`);
    if (browser) await browser.close();
    process.exit(1);
}

// A software renderer can starve the page; never let a stuck evaluate hang
// the job: fail with what is known after this long.
const OVERALL_TIMEOUT_MS = 12 * 60 * 1000;
setTimeout(() => fail(`timed out after ${OVERALL_TIMEOUT_MS / 60000} minutes`), OVERALL_TIMEOUT_MS).unref();

const step = (msg) => process.stderr.write(`  [step] ${msg}\n`);
// The ?view=3d hooks the test reads. The page's snapshot (the whole merged
// world) is left out: serializing it on every read is needless work for a
// page that software GL already keeps busy.
const HOOK_FIELDS = ["messages", "applies", "frames", "fps", "messagesPerSecond", "buildMs", "every",
    "chunkBuilds", "cards", "error"];
const pickHooks = (fields) => {
    const h = window.__roam3dView;
    return h ? Object.fromEntries(fields.map(f => [f, h[f] === undefined ? null : h[f]])) : null;
};
let lastHooks = null;
// A starved page can leave a call pending forever. Fail naming the step and
// the last hooks the page answered with, instead of waiting for the overall
// timer, which cannot tell which step stalled.
async function bounded(label, promise, ms = 60000) {
    const timer = setTimeout(() => fail(`${label}: no answer in ${ms / 1000} s; last hooks ${JSON.stringify(lastHooks)}`), ms);
    try { return await promise; } finally { clearTimeout(timer); }
}

async function openGame(query, viewport) {
    const ctx = await browser.newContext({ viewport: viewport || { width: 1280, height: 800 } });
    const page = await ctx.newPage();
    const requests = [], errors = [];
    page.on("request", r => requests.push(r.url()));
    page.on("pageerror", e => errors.push(e.message));
    attachConsole(page);
    await page.goto(BASE + "/play" + query, { waitUntil: "domcontentloaded", timeout: 30000 });
    if (!await waitForStatus(page, "Starting game…", 180000)) await fail(`${query || "default"}: game did not start`);
    await page.waitForTimeout(3000);
    // Title -> save selection -> new save -> world (as newGameThenQuit does).
    await pressKey(page, "Enter", 3, 600);
    await pressKey(page, "ArrowDown", 1, 400);
    await pressKey(page, "Enter", 3, 800);
    return { ctx, page, requests, errors };
}

(async () => {
    browser = await chromium.launch({
        headless: true,
        executablePath: process.env.ROAM_CHROMIUM || undefined,
        args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    });

    // --- default: unchanged 2D game, no 3D code -----------------------------
    const plain = await openGame("");
    await plain.page.waitForTimeout(6000);
    const plainState = await plain.page.evaluate(() => ({
        world3d: !!document.getElementById("world3d"),
        hooks: typeof window.__roam3dView,
        scene: typeof window.Roam3DScene,
        three: typeof window.THREE,
    }));
    const loaded3d = plain.requests.filter(u => THREE_D_URL.test(u));
    console.log(`default: ${JSON.stringify(plainState)}, 3D requests: ${loaded3d.length}`);
    if (loaded3d.length) await fail(`default /play requested 3D code: ${loaded3d.join(", ")}`);
    if (plainState.world3d || plainState.hooks !== "undefined" || plainState.scene !== "undefined" || plainState.three !== "undefined") {
        await fail(`default /play has 3D state: ${JSON.stringify(plainState)}`);
    }
    if (plain.errors.length) await fail(`default /play page errors: ${plain.errors.join("; ")}`);
    if (SHOTS) await plain.page.screenshot({ path: path.join(SHOTS, "play-2d.png") });
    await plain.ctx.close();

    // --- ?view=3d: worldview messages drive the 3D canvas ---------------------
    // Low graphics (no shadow maps) and a small viewport for the 3D part: CI
    // renders WebGL in software (SwiftShader), and the cost scales with pixels.
    const three = await openGame("?view=3d&gfx=low", { width: 640, height: 480 });
    const readHooks = async (label) => {
        lastHooks = await bounded(label, three.page.evaluate(pickHooks, HOOK_FIELDS));
        return lastHooks;
    };
    step("waiting for worldview messages");
    const ok = await waitFor(three.page, async () => {
        const h = await readHooks("worldview wait");
        return h && h.messages >= 5 && h.applies >= 3;
    }, 90000);
    if (!ok) {
        await fail(`no worldview messages reached the 3D scene: ${JSON.stringify(lastHooks)}; errors: ${three.errors.join("; ")}`);
    }
    // Walk a little so deltas (not just the full message) are exercised.
    // Drawing is paused meanwhile so software GL cannot starve the page;
    // worldview messages keep being applied (as in test_view3d_controls.js).
    step(`walking with drawing paused (hooks ${JSON.stringify(lastHooks)})`);
    await bounded("pause drawing", three.page.evaluate(() => window.__roam3dScene.setRenderingPaused(true)));
    await bounded("walk", (async () => {
        await pressKey(three.page, "d", 4, 350);
        await pressKey(three.page, "s", 3, 350);
    })());
    const before = await readHooks("hooks after the walk");
    await bounded("resume drawing", three.page.evaluate(() => window.__roam3dScene.setRenderingPaused(false)));
    await three.page.waitForTimeout(5000);
    step(`probing the 3D frame (hooks ${JSON.stringify(before)})`);
    const after = await bounded("frame probe", three.page.evaluate((fields) => {
        const c = document.getElementById("world3d");
        const gl = c.getContext("webgl2") || c.getContext("webgl");
        const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
        const px = new Uint8Array(4 * 64 * 64);
        gl.readPixels(Math.floor(w / 2) - 32, Math.floor(h / 2) - 32, 64, 64, gl.RGBA, gl.UNSIGNED_BYTE, px);
        const colours = new Set();
        for (let i = 0; i < px.length; i += 4) colours.add(`${px[i]},${px[i + 1]},${px[i + 2]}`);
        const hv = window.__roam3dView;
        return { hooks: Object.fromEntries(fields.map(f => [f, hv[f] === undefined ? null : hv[f]])), colours: colours.size,
                 notice: (document.getElementById("view3d-notice") || {}).textContent || "" };
    }, HOOK_FIELDS));
    // Rates come from the page's own clock (performance.now): under a software
    // renderer the test's waits can stretch well past their nominal length.
    console.log(`view=3d: fps ${after.hooks.fps}, worldview messages/s ${after.hooks.messagesPerSecond}, ` +
        `worker build+encode+post avg ${after.hooks.buildMs === null ? "n/a" : after.hooks.buildMs.toFixed(2)} ms ` +
        `(every ${after.hooks.every} tick(s)), chunk builds ${after.hooks.chunkBuilds}, cards ${after.hooks.cards}, ` +
        `centre colours ${after.colours}`);
    if (SHOTS) await three.page.screenshot({ path: path.join(SHOTS, "play-3d.png") });
    if (after.hooks.error) await fail(`3D scene error: ${after.hooks.error}`);
    if (after.colours < 4) await fail(`3D frame looks empty (${after.colours} colour(s))`);
    if (!/experimental/.test(after.notice)) await fail(`3D notice missing: "${after.notice}"`);
    if (after.hooks.messages <= before.messages) await fail("worldview messages stopped arriving");
    if (three.errors.length) await fail(`?view=3d page errors: ${three.errors.join("; ")}`);
    await three.ctx.close();

    await browser.close();
    console.log("PASS: 3D view is opt-in and renders the running game");
})().catch(e => fail(e.stack || String(e)));
