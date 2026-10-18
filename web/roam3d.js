// Roam 3D scene (RFC 0017): renders a world snapshot (the /api/v1/snapshot
// shape, also used by the browser build's "worldview" messages) as an HD-2D
// diorama. Tiles become textured terrain with biome height, rocks and trunks
// become blocks, and creatures, items and the player are camera-facing sprite
// cards; light sources are point lights at night.
//
// Shared by the spectator page (spectator/index.html, orbit camera) and the
// opt-in 3D view of the browser game (web/index.html with ?view=3d, fixed
// follow camera). Needs three.js r147 (global THREE) loaded first, and
// THREE.OrbitControls when { orbit: true }.
//
//   const scene = Roam3DScene.create({ canvas, orbit, hooks, onApplied });
//   scene.apply(snapshot);      // any time; room terrain is rebuilt only when
//                               // a room's terrain (or its revision) changes
"use strict";

(function () {
  const GROUND = new Set(["Grass", "WoodFloor", "StoneFloor", "CaveFloor", "CaveEntrance", "CaveLadder", "MatureCrop", "YoungCrop"]);
  const BLOCK = new Set(["Stone", "CoalOre", "IronOre", "GoldOre"]);
  const TRUNK = new Set(["OakWood", "JungleWood"]);
  const FRUIT = new Set(["Apple", "Banana"]);
  const FLAT = new Set(["Bed", "StoneBed"]);
  const CANOPY = "Leaves";
  const CARD_SCALE = { Bear: 1.25, Chicken: .7, Deer: 1.15, Rabbit: .7, Snake: .65, Wolf: 1.0, Npc: 1.0, Torch: 1.0,
    GoldenLantern: 1.0, Campfire: .9, Chest: .8, IronChest: .8, Fence: 1.0, Gravestone: .9, Excrement: .5,
    BearMeat: .5, ChickenMeat: .5, Wheat: .7, WheatSeed: .5 };
  const BIOME_ELEV = { grassland: 0, forest: 0.5, jungle: 0.5, mountain: 3.5, empty: 0, cave: 0 };
  const TRUNK_H = 2.4, CANOPY_LO = 1.4, CANOPY_HI = 2.4, CAVE_WALL = 2.5;
  const SHADOW_LIGHTS = 4, PLAIN_LIGHTS = 12;
  const isTerrain = n => GROUND.has(n) || BLOCK.has(n) || TRUNK.has(n) || FRUIT.has(n) || FLAT.has(n) || n === CANOPY;

  function hash(x, y) { let h = Math.imul(x, 374761393) ^ Math.imul(y, 668265263); h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
  function vnoise(x, y) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const s = t => t * t * (3 - 2 * t);
    const a = hash(xi, yi), b = hash(xi + 1, yi), c = hash(xi, yi + 1), d = hash(xi + 1, yi + 1);
    return a + (b - a) * s(xf) + (c - a) * s(yf) + (a - b - c + d) * s(xf) * s(yf);
  }
  const plateau = t => { t = t * t * (3 - 2 * t); return t * t * (3 - 2 * t); };
  const rockH = (biome, X, Z) => biome === "mountain" ? 1 + Math.floor(hash(X * 7 + 3, Z * 5 + 1) * 2.2) * 0.5 : 0.8;
  const roomKey = (x, y, z) => `${x},${y},${z}`;
  const WHITE = [1, 1, 1];
  const srgb = c => [Math.pow(c[0] / 255, 2.2), Math.pow(c[1] / 255, 2.2), Math.pow(c[2] / 255, 2.2)];
  const shade = (c, k) => [c[0] * k, c[1] * k, c[2] * k];

  function create(opts) {
    const canvas = opts.canvas;
    const hooks = opts.hooks || {};
    Object.assign(hooks, { frames: 0, fps: 0, chunkBuilds: 0, cards: 0, applies: 0 });
    const onApplied = opts.onApplied || (() => {});
    const followOffset = opts.followOffset || [0, 26, 24];
    const reducedMotion = !!opts.reducedMotion;
    const onCameraChange = opts.onCameraChange || (() => {});

    // ---- textures ---------------------------------------------------------
    const texCache = new Map();
    function pixelTex(t) {
      t.wrapS = t.wrapT = THREE.RepeatWrapping;
      t.magFilter = THREE.NearestFilter;
      t.minFilter = THREE.NearestMipmapLinearFilter;
      t.encoding = THREE.sRGBEncoding;
      t.anisotropy = 4;
      return t;
    }
    function canvasTex(draw) {
      const c = document.createElement("canvas"); c.width = c.height = 32;
      draw(c.getContext("2d"));
      return pixelTex(new THREE.CanvasTexture(c));
    }
    function noiseTex(kind) {
      return canvasTex(g => {
        let s = kind.length * 9301 + 49297;
        const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
        for (let y = 0; y < 32; y++) for (let x = 0; x < 32; x++) {
          const v = kind === "cliff" ? 175 + rnd() * 60 - (y % 8 === 0 ? 40 : 0) : 205 + rnd() * 50;
          g.fillStyle = `rgb(${v | 0},${v | 0},${v | 0})`; g.fillRect(x, y, 1, 1);
        }
      });
    }
    // Unknown class or a sprite that failed to load: a visible magenta
    // placeholder, like Renderer.loadImage's fallback.
    function missingTex() {
      return canvasTex(g => { g.fillStyle = "#ff00ff"; g.fillRect(0, 0, 32, 32); g.fillStyle = "#000"; g.fillRect(0, 0, 16, 16); g.fillRect(16, 16, 16, 16); });
    }
    function tex(key) {
      if (texCache.has(key)) return texCache.get(key);
      let t;
      if (key === "ground" || key === "cliff") t = noiseTex(key);
      else if (key === "missing") t = missingTex();
      else {
        t = pixelTex(new THREE.TextureLoader().load("/" + key, undefined, undefined, () => {
          t.image = missingTex().image; t.needsUpdate = true;
        }));
      }
      texCache.set(key, t);
      return t;
    }

    // ---- snapshot state ---------------------------------------------------
    let snap = null, G = 17, roomsByKey = new Map();
    function imageOf(name) {
      const i = snap.classes.indexOf(name);
      const img = i >= 0 ? snap.classImages[i] : null;
      return img || "missing";
    }
    const names = idxs => idxs.map(i => snap.classes[i]);
    function biomeAt(rx, ry) { const r = roomsByKey.get(roomKey(rx, ry, 0)); return r ? r.biome : null; }
    function surfaceHeight(X, Z) {
      const u = (X + 0.5) / G - 0.5, v = (Z + 0.5) / G - 0.5;
      const rx = Math.floor(u), ry = Math.floor(v), fx = plateau(u - rx), fy = plateau(v - ry);
      const lerp = (a, b, t) => a + (b - a) * t;
      const blend = f => lerp(lerp(f(rx, ry), f(rx + 1, ry), fx), lerp(f(rx, ry + 1), f(rx + 1, ry + 1), fx), fy);
      let h = blend((x, y) => BIOME_ELEV[biomeAt(x, y)] || 0);
      const m = blend((x, y) => biomeAt(x, y) === "mountain" ? 1 : 0);
      if (m > 0) h += m * (vnoise(X * 0.18, Z * 0.18) * 3.2 + vnoise(X * 0.5, Z * 0.5) * 0.8);
      return Math.round(h * 2) / 2;
    }

    // ---- geometry batcher (one draw call per texture per room) -------------
    const matCache = new Map();
    function terrainMat(key) {
      if (!matCache.has(key)) matCache.set(key, new THREE.MeshStandardMaterial({ map: tex(key), vertexColors: true, roughness: 0.95, metalness: 0 }));
      return matCache.get(key);
    }
    class Batch {
      constructor() { this.parts = new Map(); }
      part(key) {
        if (!this.parts.has(key)) this.parts.set(key, { pos: [], nrm: [], uv: [], col: [], idx: [] });
        return this.parts.get(key);
      }
      quad(key, a, b, c, d, n, col, uvScale = [1, 1]) {
        const p = this.part(key), base = p.pos.length / 3;
        for (const v of [a, b, c, d]) p.pos.push(v[0], v[1], v[2]);
        for (let i = 0; i < 4; i++) { p.nrm.push(n[0], n[1], n[2]); p.col.push(col[0], col[1], col[2]); }
        p.uv.push(0, 0, uvScale[0], 0, uvScale[0], uvScale[1], 0, uvScale[1]);
        p.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
      }
      build() {
        const group = new THREE.Group();
        for (const [key, p] of this.parts) {
          const g = new THREE.BufferGeometry();
          g.setAttribute("position", new THREE.Float32BufferAttribute(p.pos, 3));
          g.setAttribute("normal", new THREE.Float32BufferAttribute(p.nrm, 3));
          g.setAttribute("uv", new THREE.Float32BufferAttribute(p.uv, 2));
          g.setAttribute("color", new THREE.Float32BufferAttribute(p.col, 3));
          g.setIndex(p.idx);
          const mesh = new THREE.Mesh(g, terrainMat(key));
          mesh.castShadow = true; mesh.receiveShadow = true;
          group.add(mesh);
        }
        return group;
      }
    }
    function column(batch, X, Z, y0, y1, topKey, sideKey, topCol, sideCol, neighbourTop, bottom) {
      if (y1 <= y0) return;
      batch.quad(topKey, [X, y1, Z + 1], [X + 1, y1, Z + 1], [X + 1, y1, Z], [X, y1, Z], [0, 1, 0], topCol);
      if (bottom) batch.quad(topKey, [X, y0, Z], [X + 1, y0, Z], [X + 1, y0, Z + 1], [X, y0, Z + 1], [0, -1, 0], shade(topCol, .5));
      const sides = [
        [[1, 0], [X + 1, Z + 1], [X + 1, Z], .82],
        [[-1, 0], [X, Z], [X, Z + 1], .70],
        [[0, 1], [X, Z + 1], [X + 1, Z + 1], .90],
        [[0, -1], [X + 1, Z], [X, Z], .62],
      ];
      for (const [[dx, dz], p, q, k] of sides) {
        const lo = Math.max(y0, neighbourTop(X + dx, Z + dz));
        if (lo >= y1) continue;
        batch.quad(sideKey, [p[0], lo, p[1]], [q[0], lo, q[1]], [q[0], y1, q[1]], [p[0], y1, p[1]], [dx, 0, dz], shade(sideCol, k), [1, y1 - lo]);
      }
    }

    const cardGeo = new THREE.PlaneGeometry(1, 1); cardGeo.translate(0, 0.5, 0);
    const fruitGeo = new THREE.BoxGeometry(1, 1, 1);
    const cardMats = new Map();
    function cardMat(key) {
      if (!cardMats.has(key)) cardMats.set(key, new THREE.MeshStandardMaterial({ map: tex(key), alphaTest: 0.5, side: THREE.DoubleSide, roughness: 1 }));
      return cardMats.get(key);
    }

    function buildChunk(room) {
      const cave = room.z < 0;
      const X0 = room.x * G, Z0 = room.y * G;
      const heights = new Float32Array(G * G), solid = new Float32Array(G * G);
      const stacks = room.tiles.map(names);
      const canopy = new Uint8Array(G * G);
      for (let r = 0; r < G; r++) for (let c = 0; c < G; c++) {
        const i = r * G + c, ents = stacks[i], X = X0 + c, Z = Z0 + r;
        const h = cave ? 0 : surfaceHeight(X, Z);
        let top = h;
        if (cave && !ents.includes("CaveFloor")) top = h + CAVE_WALL;
        else if (ents.some(e => BLOCK.has(e))) top = h + rockH(room.biome, X, Z);
        if (ents.some(e => TRUNK.has(e))) top = h + TRUNK_H;
        heights[i] = h; solid[i] = top;
        if (ents.includes(CANOPY) && !ents.some(e => TRUNK.has(e))) canopy[i] = 1;
      }
      const inRoom = (X, Z) => X >= X0 && X < X0 + G && Z >= Z0 && Z < Z0 + G;
      const idx = (X, Z) => (Z - Z0) * G + (X - X0);
      const solidAt = (X, Z) => inRoom(X, Z) ? solid[idx(X, Z)] : -3;
      const groundAt = (X, Z) => inRoom(X, Z) ? heights[idx(X, Z)] : (cave ? -3 : surfaceHeight(X, Z));
      const batch = new Batch();
      const bg = srgb(room.backgroundColor).map(v => Math.min(1, v * 1.25));
      const sideIsRock = cave || room.biome === "mountain";
      const sideKey = sideIsRock ? "cliff" : "ground";
      const sideCol = sideIsRock ? srgb([128, 124, 120]) : srgb([150, 108, 70]);
      const fruit = [];
      for (let r = 0; r < G; r++) for (let c = 0; c < G; c++) {
        const i = r * G + c, ents = stacks[i], X = X0 + c, Z = Z0 + r, h = heights[i];
        const groundEnt = [...ents].reverse().find(e => GROUND.has(e));
        const blockEnt = ents.find(e => BLOCK.has(e) && e !== "Stone") || ents.find(e => BLOCK.has(e));
        const trunkEnt = ents.find(e => TRUNK.has(e));
        if (cave && !ents.includes("CaveFloor")) {
          const k = imageOf(blockEnt || "Stone");
          column(batch, X, Z, -1, h + CAVE_WALL, k, k, shade(WHITE, .8), shade(WHITE, .75), solidAt, false);
          continue;
        }
        const topKey = groundEnt ? imageOf(groundEnt) : "ground";
        const topCol = groundEnt === "CaveFloor" ? [1.7, 1.6, 1.5] : groundEnt ? WHITE : bg;
        column(batch, X, Z, -3, h, topKey, sideKey, topCol, sideCol, (nx, nz) => Math.min(groundAt(nx, nz), h), false);
        if (blockEnt) column(batch, X, Z, h, h + rockH(room.biome, X, Z), imageOf(blockEnt), imageOf(blockEnt), WHITE, WHITE, solidAt, false);
        if (trunkEnt) column(batch, X, Z, h, h + TRUNK_H, imageOf(trunkEnt), imageOf(trunkEnt), shade(WHITE, .95), WHITE, solidAt, false);
        if (canopy[i]) {
          const liftAt = (x, z) => room.biome === "jungle" ? Math.round(vnoise(x * .35, z * .35) * 3) * .4 : 0;
          const lift = liftAt(X, Z);
          column(batch, X, Z, h + CANOPY_LO + lift, h + CANOPY_HI + lift, imageOf(CANOPY), imageOf(CANOPY), WHITE, WHITE,
            (nx, nz) => inRoom(nx, nz) && canopy[idx(nx, nz)] && heights[idx(nx, nz)] === h && liftAt(nx, nz) === lift ? h + CANOPY_HI + lift : -99, true);
        }
        for (const e of ents) {
          if (FLAT.has(e)) column(batch, X, Z, h, h + .25, imageOf(e), imageOf("WoodFloor"), WHITE, shade(WHITE, .8), solidAt, false);
          else if (FRUIT.has(e)) fruit.push([e, X + .5, h + CANOPY_LO - .3, Z + .5]);
        }
      }
      const group = batch.build();
      for (const [e, x, y, z] of fruit) {
        const m = new THREE.Mesh(fruitGeo, cardMat(imageOf(e)));
        m.position.set(x, y, z); m.scale.setScalar(.35); m.castShadow = true; m.receiveShadow = true;
        group.add(m);
      }
      hooks.chunkBuilds++;
      return { group, heights };
    }
    // A room's terrain signature: its terrain classes, colour and biome, plus
    // the neighbour biomes that shape its edge heights. Creatures and the
    // player are cards, not terrain, so their moves never rebuild a room. When
    // the source sends revisions (the browser game), an unchanged revision
    // skips even computing the signature.
    function aroundKey(room) {
      let around = "";
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) around += biomeAt(room.x + dx, room.y + dy) + ";";
      return around;
    }
    function terrainSignature(room) {
      const terrain = room.tiles.map(t => t.filter(i => isTerrain(snap.classes[i])).map(i => snap.classes[i]).join("+")).join(",");
      return [room.biome, room.backgroundColor.join("."), terrain].join("|");
    }

    // ---- scene ------------------------------------------------------------
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, alpha: false });
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(32, 1, 0.5, 2000);
    const controls = opts.orbit ? new THREE.OrbitControls(camera, canvas) : null;
    if (controls) {
      controls.enableDamping = true; controls.dampingFactor = 0.08;
      controls.maxPolarAngle = Math.PI * 0.47; controls.minDistance = 8; controls.maxDistance = 420;
    }
    const target = new THREE.Vector3();
    const chunks = new Map();
    const cardGroup = new THREE.Group(); scene.add(cardGroup);
    const player = new THREE.Mesh(cardGeo, cardMat("assets/images/player_down.png"));
    player.scale.setScalar(1.05); player.castShadow = true; player.visible = false; scene.add(player);
    const playerTarget = new THREE.Vector3();
    let playerPlaced = false, follow = true;

    const hemi = new THREE.HemisphereLight(0xcfe6ff, 0x5a4a32, 0.55);
    const sun = new THREE.DirectionalLight(0xffffff, 2.2);
    sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.bias = -0.0006; sun.shadow.normalBias = 0.03;
    scene.add(hemi, sun, sun.target);
    // A fixed pool, so the light count (and so the shaders) never changes.
    const pointLights = [];
    for (let i = 0; i < SHADOW_LIGHTS + PLAIN_LIGHTS; i++) {
      const l = new THREE.PointLight(0xff8a4a, 0, 10, 1.6);
      if (i < SHADOW_LIGHTS) { l.castShadow = true; l.shadow.mapSize.set(512, 512); l.shadow.bias = -0.002; l.shadow.camera.near = 0.2; }
      l.userData = { seed: i * 1.7, on: false, cls: "" };
      l.visible = false;
      scene.add(l); pointLights.push(l);
    }
    const daySky = new THREE.Color(0x9fc9ef), duskSky = new THREE.Color(0xe7a07a), nightSky = new THREE.Color(0x0b1328);
    scene.fog = new THREE.Fog(daySky.clone(), 160, 520);

    function disposeGroup(g) { g.traverse(o => { if (o.isMesh && o.geometry !== fruitGeo && o.geometry !== cardGeo) o.geometry.dispose(); }); }

    function apply(s) {
      snap = s; G = s.gridSize;
      roomsByKey = new Map(s.rooms.map(r => [roomKey(r.x, r.y, r.z), r]));
      const viewZ = s.player.room[2];
      for (const [k, ch] of chunks) {
        if (!roomsByKey.has(k)) { scene.remove(ch.group); disposeGroup(ch.group); chunks.delete(k); }
      }
      for (const room of s.rooms) {
        const k = roomKey(room.x, room.y, room.z), old = chunks.get(k), around = aroundKey(room);
        if (old && old.around === around && room.revision !== undefined && old.revision === room.revision) {
          old.room = room; continue;
        }
        const sig = terrainSignature(room);
        if (old && old.around === around && old.sig === sig) { old.room = room; old.revision = room.revision; continue; }
        if (old) { scene.remove(old.group); disposeGroup(old.group); }
        const built = buildChunk(room);
        chunks.set(k, { sig, around, revision: room.revision, room, ...built });
        scene.add(built.group);
      }
      for (const ch of chunks.values()) ch.group.visible = ch.room.z === viewZ;
      cardGroup.clear();
      for (const room of s.rooms) {
        if (room.z !== viewZ) continue;
        const ch = chunks.get(roomKey(room.x, room.y, room.z));
        room.tiles.forEach((tile, i) => {
          for (const name of names(tile)) {
            if (isTerrain(name)) continue;
            const m = new THREE.Mesh(cardGeo, cardMat(imageOf(name)));
            m.position.set(room.x * G + (i % G) + .5, ch.heights[i], room.y * G + Math.floor(i / G) + .5);
            m.scale.setScalar(CARD_SCALE[name] || .9); m.castShadow = true;
            cardGroup.add(m);
          }
        });
      }
      hooks.cards = cardGroup.children.length;
      const P = s.player, pch = chunks.get(roomKey(...P.room));
      const pX = P.room[0] * G + P.x + .5, pZ = P.room[1] * G + P.y + .5;
      const pY = pch ? pch.heights[P.y * G + P.x] : 0;
      playerTarget.set(pX, pY, pZ);
      player.material = cardMat(`assets/images/player_${P.direction}.png`);
      player.visible = true;
      if (!playerPlaced) { player.position.copy(playerTarget); recentre(); playerPlaced = true; }
      const lights = s.lights.filter(l => l.room[2] === viewZ).map(l => {
        const ch = chunks.get(roomKey(...l.room));
        const x = l.room[0] * G + l.x + .5, z = l.room[1] * G + l.y + .5;
        return { x, y: (ch ? ch.heights[l.y * G + l.x] : 0) + 0.9, z, r: l.radiusTiles, cls: l.entityClass, d: Math.hypot(x - pX, z - pZ) };
      }).sort((a, b) => a.d - b.d);
      pointLights.forEach((pl, i) => {
        const src = lights[i];
        pl.userData.on = !!src;
        // An unused light is hidden, not just dimmed: three.js renders a
        // shadow-casting point light's six shadow faces whenever it is
        // visible, even at intensity 0. (Shaders recompile only when the
        // number of lights in view changes.)
        pl.visible = !!src;
        if (!src) return;
        pl.position.set(src.x, src.y, src.z); pl.distance = src.r * 1.6; pl.userData.cls = src.cls;
        pl.color.set(src.cls === "GoldenLantern" ? 0xffd9a0 : 0xff8a4a);
      });
      const span = (2 * s.radius + 1) * G * 0.75;
      Object.assign(sun.shadow.camera, { left: -span, right: span, top: span, bottom: -span, near: 1, far: 600 });
      sun.shadow.camera.updateProjectionMatrix();
      sun.target.position.set(pX, 0, pZ);
      updateCanopyFade();
      hooks.applies++; hooks.lastTick = s.tick;
      onApplied(s, { rooms: s.rooms.filter(r => r.z === viewZ).length, lights: lights.length, viewZ });
    }

    function applyLighting(t) {
      if (!snap) return;
      const dn = snap.dayNight, inCave = snap.player.room[2] < 0;
      const dark = dn.enabled ? dn.overlayOpacity / 200 : 0; // Roam's own curve: 0 midday .. 1 midnight
      const warm = Math.max(0, 1 - Math.abs(dark - 0.45) / 0.3);
      const progress = dn.cycleLengthTicks > 0 ? (snap.tick % dn.cycleLengthTicks) / dn.cycleLengthTicks : 0;
      const sky = daySky.clone().lerp(nightSky, dark).lerp(duskSky, warm * 0.55);
      const bg = inCave ? new THREE.Color(0x07080b) : sky;
      scene.background = bg; scene.fog.color.copy(bg);
      const ang = progress * Math.PI * 2, r = 220, c = sun.target.position;
      sun.position.set(c.x + Math.sin(ang + .6) * r * .6, Math.max(40, Math.cos(ang) * r), c.z + r * .55);
      sun.intensity = inCave ? 0 : (1 - dark) * 1.25 + dark * 0.22;
      sun.color.setRGB(1, 1, 1).lerp(new THREE.Color(0xffb07a), warm).lerp(new THREE.Color(0x8fa6ff), dark * dark);
      // In caves the hemisphere light is a viewer convenience: Roam has no ambient cave light.
      hemi.intensity = inCave ? 0.6 : 0.62 - dark * 0.47;
      hemi.color.set(0xcfe6ff).lerp(new THREE.Color(0x4c5c9a), dark);
      for (const l of pointLights) {
        const flicker = 1 + 0.12 * Math.sin(t * 9 + l.userData.seed) + 0.07 * Math.sin(t * 23 + l.userData.seed * 3);
        l.intensity = l.userData.on ? (0.3 + dark * 3.2) * flicker * (l.userData.cls === "Torch" ? 1 : 1.3) : 0;
      }
    }

    function recentre() {
      target.copy(player.position);
      if (controls) {
        camera.position.copy(player.position).add(new THREE.Vector3(...followOffset));
        controls.target.copy(target);
        camera.lookAt(target);
      } else {
        placeFollowCamera(1);
      }
    }

    const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
    // Returns { room, tile: [c, r], entities } under a client point, or null.
    function pick(clientX, clientY) {
      if (!snap) return null;
      const rect = canvas.getBoundingClientRect();
      ndc.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
      ray.setFromCamera(ndc, camera);
      const visible = [...chunks.values()].filter(ch => ch.group.visible);
      const hit = ray.intersectObjects(visible.map(ch => ch.group), true)[0];
      if (!hit) return null;
      const p = hit.point.clone().addScaledVector(hit.face.normal, -0.01);
      const X = Math.floor(p.x), Z = Math.floor(p.z);
      const rx = Math.floor(X / G), ry = Math.floor(Z / G), c = X - rx * G, r = Z - ry * G;
      const ch = visible.find(v => v.room.x === rx && v.room.y === ry);
      if (!ch) return null;
      return { room: ch.room, tile: [c, r], world: [X, Z, ch.room.z], entities: names(ch.room.tiles[r * G + c]) };
    }

    // Screen point (client coordinates) of the centre of a world tile's top
    // face on the level in view, or null when it is not in a loaded room.
    // Used by tests to check that picking there returns that tile.
    const _proj = new THREE.Vector3();
    function tileToClient(worldX, worldY) {
      if (!snap) return null;
      const rx = Math.floor(worldX / G), ry = Math.floor(worldY / G);
      const ch = chunks.get(roomKey(rx, ry, snap.player.room[2]));
      if (!ch) return null;
      const i = (worldY - ry * G) * G + (worldX - rx * G);
      _proj.set(worldX + 0.5, ch.heights[i] + ch.group.position.y, worldY + 0.5).project(camera);
      const rect = canvas.getBoundingClientRect();
      return { x: rect.left + (_proj.x + 1) / 2 * rect.width, y: rect.top + (1 - _proj.y) / 2 * rect.height };
    }

    // ---- follow camera (the game's 3D view; RFC 0021) ----------------------
    // Third person behind the player: yaw in 90-degree snaps (rotate), a fixed
    // pitch, and a zoom distance, eased towards their targets (instantly with
    // reduced motion). Yaw 0 puts the camera south of the player looking
    // north; it grows counter-clockwise seen from above, so quadrant 1 is the
    // camera on the east side looking west. Never stored outside the page.
    const QUARTER = Math.PI / 2, PITCH = 0.82, MIN_DIST = 12, MAX_DIST = 80;
    const rig = { yaw: 0, yawTarget: 0, dist: 35, distTarget: 35, quadrant: 0 };
    if (opts.camera) {
      rig.yaw = rig.yawTarget = (opts.camera.quadrant || 0) * QUARTER;
      rig.dist = rig.distTarget = Math.min(MAX_DIST, Math.max(MIN_DIST, opts.camera.dist || 35));
      rig.quadrant = ((opts.camera.quadrant || 0) % 4 + 4) % 4;
    }
    function quadrantOf(yaw) { return ((Math.round(yaw / QUARTER) % 4) + 4) % 4; }
    function updateQuadrant() {
      const q = quadrantOf(rig.yawTarget);
      if (q !== rig.quadrant) { rig.quadrant = q; onCameraChange({ quadrant: q, dist: rig.distTarget }); }
    }
    function rotate(quarterTurns) { rig.yawTarget = Math.round(rig.yawTarget / QUARTER + quarterTurns) * QUARTER; updateQuadrant(); }
    function setYaw(radians) { rig.yawTarget = radians; rig.yaw = radians; updateQuadrant(); }
    function snapYaw() { rig.yawTarget = Math.round(rig.yawTarget / QUARTER) * QUARTER; updateQuadrant(); }
    function zoom(factor) {
      rig.distTarget = Math.min(MAX_DIST, Math.max(MIN_DIST, rig.distTarget * factor));
      onCameraChange({ quadrant: rig.quadrant, dist: rig.distTarget });
    }
    function groundUnder(x, z) {
      if (!snap) return 0;
      if (snap.player.room[2] < 0) return CAVE_WALL;
      return surfaceHeight(Math.floor(x), Math.floor(z));
    }
    const _camOffset = new THREE.Vector3();
    function placeFollowCamera(dt) {
      const k = reducedMotion ? 1 : 1 - Math.exp(-dt * 12);
      rig.yaw += (rig.yawTarget - rig.yaw) * k;
      rig.dist += (rig.distTarget - rig.dist) * k;
      _camOffset.set(Math.sin(rig.yaw) * Math.cos(PITCH), Math.sin(PITCH), Math.cos(rig.yaw) * Math.cos(PITCH)).multiplyScalar(rig.dist);
      camera.position.copy(target).add(_camOffset);
      // Never inside a mountain: keep the camera above the ground under it.
      const floor = groundUnder(camera.position.x, camera.position.z) + 2;
      if (camera.position.y < floor) camera.position.y = floor;
      camera.lookAt(target);
    }

    // Canopy near the player fades so trees never hide them.
    let canopyFaded = false;
    function updateCanopyFade() {
      if (controls || !snap) return;
      const P = snap.player, ch = chunks.get(roomKey(...P.room));
      let near = false;
      if (ch && P.room[2] === 0) {
        const room = ch.room;
        for (let dy = -3; dy <= 3 && !near; dy++) for (let dx = -3; dx <= 3 && !near; dx++) {
          const x = P.x + dx, y = P.y + dy;
          if (x < 0 || y < 0 || x >= G || y >= G) continue;
          if (names(room.tiles[y * G + x]).includes(CANOPY)) near = true;
        }
      }
      if (near === canopyFaded) return;
      canopyFaded = near;
      const key = imageOf(CANOPY);
      if (!matCache.has(key)) return;
      const m = matCache.get(key);
      m.transparent = near; m.opacity = near ? 0.35 : 1; m.depthWrite = !near; m.needsUpdate = true;
    }

    function resize() {
      const w = canvas.clientWidth || window.innerWidth, h = canvas.clientHeight || window.innerHeight;
      renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
    }
    window.addEventListener("resize", resize);
    resize();
    camera.position.set(...followOffset);
    camera.lookAt(0, 0, 0);

    const clock = new THREE.Clock();
    const camDir = new THREE.Vector3(), step = new THREE.Vector3();
    let fpsFrames = 0, fpsSince = performance.now();
    let lastT = 0;
    function frame() {
      const t = clock.getElapsedTime(), dt = Math.min(0.1, t - lastT);
      lastT = t;
      step.copy(playerTarget).sub(player.position);
      if (step.lengthSq() > 64) player.position.copy(playerTarget); else player.position.addScaledVector(step, 0.2);
      if (controls) {
        if (follow && playerPlaced) {
          const delta = player.position.clone().sub(target);
          target.add(delta); camera.position.add(delta);
          controls.target.copy(target);
        }
      } else {
        if (playerPlaced) target.copy(player.position);
        placeFollowCamera(dt);
      }
      if (controls) controls.update();
      camera.getWorldDirection(camDir);
      const yaw = Math.atan2(-camDir.x, -camDir.z);
      player.rotation.y = yaw;
      for (const c of cardGroup.children) c.rotation.y = yaw;
      applyLighting(reducedMotion ? 0 : t);
      renderer.render(scene, camera);
      hooks.frames++; fpsFrames++;
      const now = performance.now();
      if (now - fpsSince >= 1000) { hooks.fps = Math.round(fpsFrames * 1000 / (now - fpsSince)); fpsFrames = 0; fpsSince = now; }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);

    return {
      apply, recentre, pick, resize, tileToClient,
      rotate, setYaw, snapYaw, zoom,
      getCamera() { return { quadrant: rig.quadrant, dist: rig.distTarget, yaw: rig.yawTarget }; },
      getPlayerTile() { return snap ? { room: snap.player.room.slice(), x: snap.player.x, y: snap.player.y } : null; },
      setFollow(on) { follow = !!on; },
      readPixels(size) {
        const gl = renderer.getContext();
        const w = gl.drawingBufferWidth, h = gl.drawingBufferHeight, n = size || 64;
        const px = new Uint8Array(4 * n * n);
        gl.readPixels(Math.floor(w / 2) - n / 2, Math.floor(h / 2) - n / 2, n, n, gl.RGBA, gl.UNSIGNED_BYTE, px);
        const colours = new Set();
        for (let i = 0; i < px.length; i += 4) colours.add(`${px[i]},${px[i + 1]},${px[i + 2]}`);
        return colours.size;
      },
    };
  }

  window.Roam3DScene = { create };
})();
