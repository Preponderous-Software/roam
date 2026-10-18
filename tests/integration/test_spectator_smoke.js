#!/usr/bin/env node
// Integration test: the Roam 3D spectator (RFC 0017 stage 1, docs/spectator.md)
// renders a real running game.
//
// Needs a game already running with restEnabled: true and a world open (see
// tests/integration/spectatorGame.py). Checks that /api/v1/snapshot answers
// 200 with rooms and a player, that /spectator/ loads, polls the snapshot and
// draws a non-empty WebGL frame, and that the page logs no console error or
// page error and no request fails (other than the expected first-poll 503).
//
// Usage:
//   node tests/integration/test_spectator_smoke.js [URL]
// Defaults to http://127.0.0.1:8090. ROAM_SHOTS=<dir> saves a screenshot.
//
// Exit code: 0 = pass, 1 = fail.

"use strict";

const path = require("path");
const { chromium } = require("playwright");

const BASE = process.env.ROAM_REST_URL || process.argv[2] || "http://127.0.0.1:8090";
const SHOTS = process.env.ROAM_SHOTS || "";

let browser;
async function fail(msg) {
    process.stderr.write(`FAIL: ${msg}\n`);
    if (browser) await browser.close();
    process.exit(1);
}

async function snapshotWithRetry() {
    // The game builds a WorldView only while someone polls, so the first
    // request can be a 503 "no world view published yet".
    for (let attempt = 0; attempt < 40; attempt++) {
        const res = await fetch(`${BASE}/api/v1/snapshot?radius=1`);
        if (res.status === 200) return res.json();
        if (res.status !== 503) await fail(`snapshot returned HTTP ${res.status}`);
        await new Promise(r => setTimeout(r, 250));
    }
    await fail("snapshot never returned 200");
}

(async () => {
    const snap = await snapshotWithRetry();
    if (snap.format !== "roam-world-snapshot") await fail(`unexpected format ${snap.format}`);
    if (!snap.rooms.length) await fail("snapshot has no rooms");
    if (!snap.player || !Array.isArray(snap.player.room)) await fail("snapshot has no player");
    console.log(`snapshot: tick ${snap.tick}, ${snap.rooms.length} room(s), ${snap.classes.length} class(es)`);

    browser = await chromium.launch({
        headless: true,
        executablePath: process.env.ROAM_CHROMIUM || undefined,
        args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
    });
    const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
    const problems = [];
    page.on("console", m => { if (m.type() === "error" && !/status of 503/.test(m.text())) problems.push(`console: ${m.text()}`); });
    page.on("pageerror", e => problems.push(`pageerror: ${e.message}`));
    page.on("requestfailed", r => problems.push(`requestfailed: ${r.url()}`));
    page.on("response", r => {
        if (r.status() >= 400 && !(r.status() === 503 && r.url().includes("/api/v1/snapshot"))) {
            problems.push(`HTTP ${r.status()}: ${r.url()}`);
        }
    });

    await page.goto(`${BASE}/spectator/`, { waitUntil: "load", timeout: 60000 });
    try {
        await page.waitForFunction("window.__roam3d && window.__roam3d.polls >= 3 && window.__roam3d.frames >= 3", null, { timeout: 60000 });
    } catch (e) {
        const hooks = await page.evaluate(() => window.__roam3d).catch(() => null);
        await fail(`page did not poll and render: ${JSON.stringify(hooks)} ${problems.join("; ")}`);
    }
    await page.waitForTimeout(1500);
    const result = await page.evaluate(() => {
        const c = document.getElementById("c");
        const gl = c.getContext("webgl2") || c.getContext("webgl");
        const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight;
        const px = new Uint8Array(4 * 64 * 64);
        gl.readPixels(Math.floor(w / 2) - 32, Math.floor(h / 2) - 32, 64, 64, gl.RGBA, gl.UNSIGNED_BYTE, px);
        const colours = new Set();
        for (let i = 0; i < px.length; i += 4) colours.add(`${px[i]},${px[i + 1]},${px[i + 2]}`);
        return { hooks: window.__roam3d, colours: colours.size, status: document.getElementById("status").textContent };
    });
    console.log(`page: ${JSON.stringify(result)}`);
    if (SHOTS) await page.screenshot({ path: path.join(SHOTS, "spectator.png") });
    if (result.hooks.error) await fail(`page reported an error: ${result.hooks.error}`);
    if (result.hooks.chunkBuilds < 1) await fail("no room terrain was built");
    if (result.colours < 4) await fail(`WebGL frame looks empty (${result.colours} colour(s) at the centre)`);
    if (problems.length) await fail(problems.join("; "));
    await browser.close();
    console.log("PASS: spectator renders a running game");
})().catch(e => fail(e.stack || String(e)));
