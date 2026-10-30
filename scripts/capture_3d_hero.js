#!/usr/bin/env node
// Records the README hero media for the opt-in 3D view (/play?view=3d):
// a short scripted walk through a freshly generated world, captured from
// the real browser build. This is a docs tool, not a test: CI does not run
// it, and nothing in it asserts on GL timing.
//
// Step 1 (this script) saves numbered PNG frames plus frames.json (how long
// the GIF shows each frame) into an output directory. Step 2,
// scripts/make_3d_hero.py, turns them into pics/roam3d-hero.gif and
// pics/roam3d-hero.png. scripts/capture_3d_hero.sh runs both.
//
// Usage (scripts/capture_3d_hero.sh does all of this):
//   python3 web/build_zip.py && python3 web/serve.py &
//   node scripts/capture_3d_hero.js [URL] [OUT_DIR]
//   python3 scripts/make_3d_hero.py OUT_DIR --out-dir pics
// URL defaults to http://localhost:8080, OUT_DIR to ./3d-hero-frames.
// Needs Playwright (npm install -g playwright; npx playwright install
// chromium). ROAM_CHROMIUM points it at a specific Chromium binary.
//
// The game's starting world is not seeded (#600), so every run walks a
// different world; the walk itself (keys, timings, the camera's turn) is fixed.
// The new save is made in a throwaway browser profile, never on disk.

"use strict";

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const BASE = process.argv[2] || process.env.ROAM_URL || "http://localhost:8080";
const OUT = path.resolve(process.argv[3] || "3d-hero-frames");
// The game area is the square under the page's status bar; a square-ish
// window keeps it free of black side bars.
const WIDTH = 640, HEIGHT = 665;

function log(msg) { process.stderr.write(`[capture] ${msg}\n`); }

async function waitFor(page, fn, maxMs, stepMs = 500) {
    const deadline = Date.now() + maxMs;
    while (Date.now() < deadline) {
        const v = await fn().catch(() => null);
        if (v) return v;
        await page.waitForTimeout(stepMs);
    }
    return null;
}

async function press(page, key, times, delay) {
    for (let i = 0; i < times; i++) {
        await page.keyboard.press(key);
        await page.waitForTimeout(delay);
    }
}

(async () => {
    fs.mkdirSync(OUT, { recursive: true });
    for (const f of fs.readdirSync(OUT)) if (/^frame-\d+\.png$|^still\.png$|^frames\.json$/.test(f)) fs.unlinkSync(path.join(OUT, f));

    const browser = await chromium.launch({
        headless: true,
        executablePath: process.env.ROAM_CHROMIUM || undefined,
        args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    });
    const ctx = await browser.newContext({ viewport: { width: WIDTH, height: HEIGHT } });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => log(`page error: ${e.message}`));
    await page.goto(BASE + "/play?view=3d", { waitUntil: "domcontentloaded", timeout: 60000 });

    // Title -> new game -> world, the same key path as the 3D integration tests.
    const started = await waitFor(page, () => page.evaluate(() => {
        const el = document.getElementById("bar-status");
        return el && el.textContent.trim() === "Starting game…";
    }), 180000);
    if (!started) throw new Error("the game did not start");
    await page.waitForTimeout(3000);
    await press(page, "Enter", 3, 600);
    await press(page, "ArrowDown", 1, 400);
    await press(page, "Enter", 3, 800);
    const inWorld = await waitFor(page, () => page.evaluate(() =>
        window.__roam3dView && window.__roam3dView.applies >= 3), 120000);
    if (!inWorld) throw new Error("no world view reached the 3D scene");
    log("in the world");

    // Page chrome that is not part of the game: the one-line 3D hint, and the
    // "switch to 2D?" offer a software renderer can trigger (keep 3D).
    const tidy = () => page.evaluate(() => {
        const n = document.getElementById("view3d-notice");
        if (n) n.remove();
        const slow = document.getElementById("view3d-slow");
        if (slow) {
            const keep = [...slow.querySelectorAll("button")].find((b) => b.textContent === "Keep 3D");
            if (keep) keep.click(); else slow.remove();
        }
    });
    await tidy();
    // Let the starting rooms finish building and the textures load.
    await page.waitForTimeout(6000);

    // The game area (2D HUD canvas over the 3D canvas), without the page's
    // status bar.
    const clip = await page.evaluate(() => {
        const r = document.getElementById("canvas-wrap").getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height) };
    });
    log(`game area ${JSON.stringify(clip)}`);

    // Frame-stepped capture. A software renderer draws a full-quality frame
    // in about half a second, and a screenshot taken while it draws back to
    // back can wait for a minute. So drawing is paused between frames: each
    // frame lets the scene draw exactly once, pauses it again, then takes the
    // screenshot of a still page. Each frame carries the time the GIF shows
    // it for (`ms`), so playback speed does not depend on how fast this
    // machine draws.
    await page.evaluate(() => window.__roam3dScene.setRenderingPaused(true));
    const frames = [];
    async function frame(ms) {
        await tidy();
        const before = await page.evaluate(() => window.__roam3dView.frames);
        await page.evaluate(() => window.__roam3dScene.setRenderingPaused(false));
        await waitFor(page, () => page.evaluate((b) => window.__roam3dView.frames > b, before), 30000, 50);
        await page.evaluate(() => window.__roam3dScene.setRenderingPaused(true));
        const file = `frame-${String(frames.length).padStart(3, "0")}.png`;
        await page.screenshot({ path: path.join(OUT, file), clip, timeout: 60000 });
        frames.push({ file, ms });
    }
    const player = () => page.evaluate(() => {
        const p = window.__roam3dView.snapshot.player;
        return `${p.room.join(",")}:${p.x},${p.y}`;
    });
    // A short tap of a movement key (about one tile at the game's walking
    // speed), then one frame once the player's card has glided there. A
    // blocked step (a tree or a rock in the way) adds no frame.
    async function stepTile(key) {
        const from = await player();
        await page.keyboard.down(key);
        await page.waitForTimeout(120);
        await page.keyboard.up(key);
        await page.waitForTimeout(350);
        const to = await player();
        if (to === from) { log(`step ${key} blocked at ${from}`); return; }
        log(`step ${key}: ${from} -> ${to}`);
        await frame(170);
    }
    async function walk(key, tiles) {
        for (let i = 0; i < tiles; i++) await stepTile(key);
    }
    // The camera swung once all the way round the player, in `n` frames.
    // It ends where it started (quadrant 0), so W / A / S / D keep their
    // usual meaning for the rest of the walk.
    async function orbit(n = 14) {
        const yaw0 = await page.evaluate(() => window.__roam3dScene.getCamera().yaw);
        for (let i = 1; i <= n; i++) {
            const k = i / n, ease = k * k * (3 - 2 * k);
            await page.evaluate((y) => window.__roam3dScene.setYaw(y), yaw0 + ease * 2 * Math.PI);
            await frame(120);
        }
        await page.evaluate((y) => window.__roam3dScene.setYaw(y), yaw0);
    }

    // "\\" (the ASCII alternative to F3, which opened the in-game menu
    // instead in headless Chromium) hides the debug readout (tick / TPS),
    // which is on by default, and the pointer goes to a corner so no hover
    // label follows it. The camera comes in a little closer than the default.
    await tidy();
    await page.keyboard.press("Backslash");
    await page.mouse.move(clip.x + clip.width - 2, clip.y + 2);
    await page.evaluate(() => window.__roam3dScene.zoom(0.65));
    await page.waitForTimeout(1500);

    // The walk. The player starts in the middle of the starting home, whose
    // doorway is three tiles south (towards the camera): walk out through it,
    // along the front of the home to just past its corner, stop for one turn
    // of the camera all the way round, then head north beside the home.
    await frame(1000);
    // The still: the opening view (the home, the player inside, the HUD).
    fs.copyFileSync(path.join(OUT, frames[0].file), path.join(OUT, "still.png"));
    await walk("s", 4);
    await walk("d", 4);
    await orbit();
    await walk("w", 3);
    await frame(1400);

    fs.writeFileSync(path.join(OUT, "frames.json"), JSON.stringify({ base: BASE, width: WIDTH, height: HEIGHT, frames }, null, 2));
    log(`${frames.length} frames -> ${OUT}`);
    await browser.close();
})().catch((e) => { process.stderr.write(`FAIL: ${e.stack || e}\n`); process.exit(1); });
