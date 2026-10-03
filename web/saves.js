// Save export / import for the browser build ("Saves" button on the page).
//
// Adapted from tak's save panel (Stephenson-Software/tak,
// src/tak/web/assets/saves.js, PR #20), whose safety order it keeps. What is
// different here is how an import is merged: Roam's saves are worlds (one
// folder per world under /saves, e.g. /saves/save_1/rooms/room_0_0.json), and
// two browsers commonly both have a world called save_1. Merging file by file
// would mix two different worlds' rooms into one folder, so an import works a
// whole world at a time and never replaces anything:
//
//   - a world that is not here is added under its own name;
//   - a world that is here with exactly the same files (under its own name,
//     or as the copy an earlier import made) is left alone;
//   - a world that is here but differs is added as a NEW world,
//     "<name>-imported" (or -imported-2, ...); the world already here is not
//     touched.
//
// A save file is one JSON document:
//
//   {"format": "roam-saves", "version": 1, "game": "roam",
//    "exported": "<ISO time>", "files": {"/saves/<world>/<path>": <content>}}
//
// where <content> is the stored value itself when it is a string (the JSON
// saves) and {"base64": "..."} when it is bytes (map PNGs, stored as an
// ArrayBuffer; see encodeSaveRecord in game-worker.js). An import writes each
// value back as the same type, so a round trip is exact.
//
// -- Why nothing here can lose a save -----------------------------------------
// The page REPLACES the whole IndexedDB store on every sync (index.html
// _idbWrite clears it, then writes what the Worker has in memory), so a file
// written behind a running game's back would be erased by its next save. An
// import therefore runs in this order:
//
//   1. The file is read and validated in full and the change is computed and
//      shown. Storage is not touched; cancelling leaves the game running.
//   2. On confirm, stop() is called: the page sets a flag that turns every
//      later IndexedDB write of its own into a no-op (checked when the write's
//      transaction would be created) and terminates the Worker.
//   3. Other tabs are told over a BroadcastChannel to stop the same way, and
//      given a moment to do so.
//   4. The store is read again and the change recomputed. If it differs from
//      what was shown (the game saved meanwhile), it is shown again.
//   5. A backup of the store as it is now is written to a second database,
//      roam-saves.backups (the last five are kept), and read back. If that
//      fails, nothing else happens.
//   6. The new files are written in one transaction. Nothing is cleared,
//      deleted or overwritten: every path written is one that was not there.
//   7. The store is read back: every imported file must be there as written
//      and every file that was there before must be there unchanged. Then the
//      page reloads and the new Worker restores from the store.
//
// Export only reads the store, so it never stops or touches the game.

window.RoamSaves = (function () {
  "use strict";

  const FORMAT = "roam-saves";
  const FORMAT_VERSION = 1;
  const GAME = "roam";
  const IDB_NAME = "roam-saves";
  const IDB_STORE = "files";
  const IDB_VERSION = 1;
  const BACKUP_DB = "roam-saves.backups";
  const BACKUP_STORE = "backups";
  const BACKUPS_KEPT = 5;
  const ROOT = "/saves";
  const MAX_FILE_BYTES = 50 * 1024 * 1024;
  const MAX_FILES = 20000;
  const MAX_PATH_LENGTH = 1024;

  // -- Pure helpers (no DOM, no storage) ---------------------------------------

  function bytesToBase64(bytes) {
    let binary = "";
    for (let i = 0; i < bytes.length; i += 0x8000) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    }
    return btoa(binary);
  }

  function base64ToBytes(text) {
    if (!/^[A-Za-z0-9+/]*={0,2}$/.test(text) || text.length % 4 !== 0) {
      throw new Error("not base64");
    }
    const binary = atob(text);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
  }

  function asBytes(value) {
    if (value instanceof Uint8Array) return value;
    if (value instanceof ArrayBuffer) return new Uint8Array(value);
    if (ArrayBuffer.isView(value)) return new Uint8Array(value.buffer, value.byteOffset, value.byteLength);
    return null;
  }

  // A stored value as it goes into the file. Anything that is neither text nor
  // bytes fails the whole export rather than being left out of it quietly.
  function encodeValue(path, value) {
    if (typeof value === "string") return value;
    const bytes = asBytes(value);
    if (bytes) return { base64: bytesToBase64(bytes) };
    throw new Error("the stored file " + path + " is of a kind this export cannot write");
  }

  function sameValue(a, b) {
    if (typeof a === "string" || typeof b === "string") return a === b;
    const x = asBytes(a), y = asBytes(b);
    if (!x || !y || x.length !== y.length) return false;
    for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return false;
    return true;
  }

  // entries: Map or [[path, value], ...] as read from the store.
  function buildExport(entries, now) {
    const files = {};
    for (const [path, value] of entries) files[path] = encodeValue(path, value);
    return {
      format: FORMAT,
      version: FORMAT_VERSION,
      game: GAME,
      exported: (now || new Date()).toISOString(),
      files: files,
    };
  }

  // The world a path belongs to ("save_1" for /saves/save_1/tick.json), or ""
  // for a file directly in /saves.
  function worldOf(path) {
    const rest = path.slice(ROOT.length + 1);
    const slash = rest.indexOf("/");
    return slash < 0 ? "" : rest.slice(0, slash);
  }

  // Why a path may not be imported, or null if it may.
  function checkPath(path) {
    if (typeof path !== "string" || !path) return "an empty path";
    if (path.length > MAX_PATH_LENGTH) return "a path that is too long";
    if (!path.startsWith(ROOT + "/")) return "a path outside " + ROOT + "/";
    if (/[\u0000-\u001f\u007f\\]/.test(path)) return "a path with a control character or backslash";
    const parts = path.slice(ROOT.length + 1).split("/");
    for (const part of parts) {
      if (part === "" || part === "." || part === "..") return "a path with an empty, . or .. part";
    }
    const world = worldOf(path);
    // The game's own rule for a save name (SaveSelectionScreen._isValidSaveName).
    if (world && (world !== world.trim() || world.indexOf("..") >= 0)) return "a world name the game would refuse";
    return null;
  }

  // Validate a whole save file without touching storage. Never throws:
  // returns { ok: true, files: Map, exported } or { ok: false, reason }.
  function parseImport(text) {
    const refuse = (reason) => ({ ok: false, reason: reason });
    if (typeof text !== "string") return refuse("The file could not be read. Nothing was changed.");
    if (text.length > MAX_FILE_BYTES) return refuse("The file is too large to be a Roam saves file. Nothing was changed.");
    let doc;
    try { doc = JSON.parse(text); }
    catch (e) { return refuse("This is not a Roam saves file (it is not readable JSON). Nothing was changed."); }
    if (!doc || typeof doc !== "object" || Array.isArray(doc) || doc.format !== FORMAT) {
      return refuse("This is not a Roam saves file. Nothing was changed.");
    }
    if (typeof doc.version !== "number" || !Number.isInteger(doc.version)) {
      return refuse("The saves file has no readable version. Nothing was changed.");
    }
    if (doc.version > FORMAT_VERSION) {
      return refuse("The saves file was made by a newer version of Roam; reload the page to get " +
                    "the newest version, then try again. Nothing was changed.");
    }
    if (doc.version !== FORMAT_VERSION) {
      return refuse("The saves file's version (" + doc.version + ") is not one this page reads. Nothing was changed.");
    }
    if (doc.game !== GAME) {
      return refuse("This file holds saves for another game, not Roam. Nothing was changed.");
    }
    if (!doc.files || typeof doc.files !== "object" || Array.isArray(doc.files)) {
      return refuse("The saves file has no list of files. Nothing was changed.");
    }
    const paths = Object.keys(doc.files);
    if (paths.length === 0) return refuse("The saves file contains no saves. Nothing was changed.");
    if (paths.length > MAX_FILES) return refuse("The saves file holds too many files. Nothing was changed.");
    const files = new Map();
    for (const path of paths) {
      const problem = checkPath(path);
      if (problem) {
        return refuse("The saves file contains " + problem + " (" + String(path).slice(0, 80) +
                      "), so it was not loaded. Nothing was changed.");
      }
      const value = doc.files[path];
      if (typeof value === "string") { files.set(path, value); continue; }
      if (value && typeof value === "object" && !Array.isArray(value) &&
          Object.keys(value).length === 1 && typeof value.base64 === "string") {
        try { files.set(path, base64ToBytes(value.base64)); continue; }
        catch (e) { /* falls through to the refusal */ }
      }
      return refuse("The saves file is damaged: " + path + " cannot be read. Nothing was changed.");
    }
    return { ok: true, files: files, exported: typeof doc.exported === "string" ? doc.exported : "" };
  }

  function groupByWorld(files) {
    const worlds = new Map();
    for (const [path, value] of files) {
      const world = worldOf(path);
      if (!worlds.has(world)) worlds.set(world, new Map());
      worlds.get(world).set(path.slice(ROOT.length + 1 + (world ? world.length + 1 : 0)), value);
    }
    return worlds;
  }

  function sameWorld(a, b) {
    if (!a || !b || a.size !== b.size) return false;
    for (const [rel, value] of a) if (!b.has(rel) || !sameValue(b.get(rel), value)) return false;
    return true;
  }

  // What an import of `incoming` (Map path -> value) would do to `current`.
  // Returns { writes: Map(path -> value), added: [world], renamed: [[from, to]],
  //           same: [world], kept: [world], looseAdded: [path], looseKept: [path] }.
  // Every path in `writes` is absent from `current`.
  function plan(current, incoming) {
    const have = groupByWorld(current);
    const taken = new Set(have.keys());
    const result = { writes: new Map(), added: [], renamed: [], same: [], kept: [], looseAdded: [], looseKept: [] };
    const inWorlds = groupByWorld(incoming);
    const names = Array.from(inWorlds.keys()).filter((w) => w !== "").sort();
    for (const name of names) {
      const files = inWorlds.get(name);
      let target = name;
      // Already here, under its own name or as an earlier import's copy.
      let twin = sameWorld(have.get(name), files) ? name : null;
      for (const [localName, localFiles] of have) {
        if (!twin && localName && sameWorld(localFiles, files)) twin = localName;
      }
      if (twin) { result.same.push(twin === name ? name : name + " (as " + twin + ")"); continue; }
      if (have.has(name)) {
        let n = 1;
        target = name + "-imported";
        while (taken.has(target) || inWorlds.has(target)) { n += 1; target = name + "-imported-" + n; }
        result.renamed.push([name, target]);
      } else {
        result.added.push(name);
      }
      taken.add(target);
      for (const [rel, value] of files) result.writes.set(ROOT + "/" + target + "/" + rel, value);
    }
    // Files directly in /saves (the game writes none today): added when
    // absent, otherwise the one here is kept.
    const loose = inWorlds.get("") || new Map();
    for (const [rel, value] of loose) {
      const path = ROOT + "/" + rel;
      if (!current.has(path)) { result.looseAdded.push(path); result.writes.set(path, value); }
      else if (!sameValue(current.get(path), value)) result.looseKept.push(path);
    }
    for (const name of have.keys()) if (name && !inWorlds.has(name)) result.kept.push(name);
    result.kept.sort();
    return result;
  }

  function planKey(p) {
    return JSON.stringify([Array.from(p.writes.keys()).sort(), p.renamed]);
  }

  // -- IndexedDB ---------------------------------------------------------------

  function openDb(name, storeName) {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(name, IDB_VERSION);
      request.onupgradeneeded = (ev) => {
        const db = ev.target.result;
        if (!db.objectStoreNames.contains(storeName)) db.createObjectStore(storeName);
      };
      request.onsuccess = (ev) => resolve(ev.target.result);
      request.onerror = () => reject(request.error);
      request.onblocked = () => reject(new Error("the save storage is busy in another tab"));
    });
  }

  function finish(tx) {
    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error("IndexedDB transaction failed"));
      tx.onabort = () => reject(tx.error || new Error("IndexedDB transaction aborted"));
    });
  }

  async function readStore() {
    const db = await openDb(IDB_NAME, IDB_STORE);
    try {
      const tx = db.transaction(IDB_STORE, "readonly");
      const done = finish(tx);
      const entries = new Map();
      await new Promise((resolve, reject) => {
        const cursor = tx.objectStore(IDB_STORE).openCursor();
        cursor.onsuccess = (ev) => {
          const c = ev.target.result;
          if (c) { entries.set(c.key, c.value); c.continue(); } else resolve();
        };
        cursor.onerror = () => reject(cursor.error);
      });
      await done;
      return entries;
    } finally { db.close(); }
  }

  function listBackupKeys(db) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(BACKUP_STORE, "readonly");
      const request = tx.objectStore(BACKUP_STORE).getAllKeys();
      request.onsuccess = () => resolve(request.result.slice().sort());
      request.onerror = () => reject(request.error);
    });
  }

  async function writeBackup(doc) {
    const db = await openDb(BACKUP_DB, BACKUP_STORE);
    try {
      const key = doc.exported;
      let tx = db.transaction(BACKUP_STORE, "readwrite");
      let done = finish(tx);
      tx.objectStore(BACKUP_STORE).put(doc, key);
      await done;
      tx = db.transaction(BACKUP_STORE, "readonly");
      done = finish(tx);
      const stored = await new Promise((resolve, reject) => {
        const request = tx.objectStore(BACKUP_STORE).get(key);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
      await done;
      if (!stored || JSON.stringify(stored.files) !== JSON.stringify(doc.files)) {
        throw new Error("the backup did not read back as written");
      }
      // Keep the newest few, only ever after the new one is safely stored.
      const keys = await listBackupKeys(db);
      const old = keys.slice(0, Math.max(0, keys.length - BACKUPS_KEPT));
      if (old.length) {
        tx = db.transaction(BACKUP_STORE, "readwrite");
        done = finish(tx);
        for (const k of old) tx.objectStore(BACKUP_STORE).delete(k);
        await done;
      }
    } finally { db.close(); }
  }

  async function readBackups() {
    const db = await openDb(BACKUP_DB, BACKUP_STORE);
    try {
      return await new Promise((resolve, reject) => {
        const tx = db.transaction(BACKUP_STORE, "readonly");
        const request = tx.objectStore(BACKUP_STORE).getAll();
        request.onsuccess = () => resolve(request.result.slice().sort((a, b) =>
          a.exported < b.exported ? 1 : a.exported > b.exported ? -1 : 0));
        request.onerror = () => reject(request.error);
      });
    } finally { db.close(); }
  }

  // Add only: `add` (Map path -> value) holds paths that are not in the store.
  async function addToStore(add) {
    const db = await openDb(IDB_NAME, IDB_STORE);
    try {
      const tx = db.transaction(IDB_STORE, "readwrite");
      const done = finish(tx);
      const store = tx.objectStore(IDB_STORE);
      for (const [path, value] of add) store.add(value, path);  // add() fails rather than overwrite
      await done;
    } finally { db.close(); }
  }

  // -- Downloads ---------------------------------------------------------------

  function download(doc, name) {
    const blob = new Blob([JSON.stringify(doc, null, 1)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = name;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    setTimeout(() => { URL.revokeObjectURL(url); link.remove(); }, 60000);
  }

  function exportName(iso, kind) {
    return "roam-" + (kind || "saves") + "-" + String(iso).slice(0, 10) + ".json";
  }

  // -- The panel ---------------------------------------------------------------

  const STYLE = `
.roam-saves-dialog button {
  font: 16px system-ui, sans-serif; min-height: 44px; min-width: 44px;
  padding: .5rem 1rem; border-radius: 6px; cursor: pointer;
  border: 1px solid #444; background: #1e1e1e; color: #ddd;
  touch-action: manipulation; -webkit-tap-highlight-color: transparent;
}
.roam-saves-dialog button:hover { background: #2a2a2a; }
.roam-saves-dialog button.primary { background: #0f2a0f; color: #8e8; border-color: #2a5a2a; }
.roam-saves-dialog button:disabled { opacity: .5; cursor: not-allowed; }
.roam-saves-dialog {
  font: 16px/1.45 system-ui, sans-serif; color: #ddd; background: #111;
  border: 1px solid #333; border-radius: 10px; padding: 1rem 1.1rem; margin: auto;
  width: min(34rem, calc(100vw - 32px)); max-height: calc(100dvh - 32px);
  box-sizing: border-box; overflow-y: auto; overflow-wrap: anywhere;
  user-select: text; -webkit-user-select: text; touch-action: pan-y;
}
.roam-saves-dialog::backdrop { background: rgba(0, 0, 0, .7); }
.roam-saves-dialog h3 { margin: 0 0 .5rem; font-size: 1.15rem; }
.roam-saves-dialog p { margin: .5rem 0; }
.roam-saves-dialog ul { margin: .25rem 0 .75rem; padding-left: 1.25rem; }
.roam-saves-actions { display: flex; flex-wrap: wrap; gap: .5rem; margin: .75rem 0; }
.roam-saves-message { color: #9fd0ff; }
.roam-saves-message.error { color: #ff8a8a; }
.roam-saves-note { color: #999; font-size: .9rem; }
@media (max-width: 600px) { .roam-saves-actions button { flex: 1 1 100%; } }
`;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function button(label, className, onClick) {
    const node = element("button", className, label);
    node.type = "button";
    node.addEventListener("click", onClick);
    return node;
  }

  // options: { button: element,           - the page's "Saves" button
  //            stop: function () {} }     - stop the game and every save write
  function attach(options) {
    const stop = options.stop || function () {};
    const open = options.button;
    let stopped = false;

    function stopGame() {
      if (stopped) return;
      stopped = true;
      try { stop(); } catch (e) { console.warn("[roam] stopping the game failed:", e); }
    }

    const style = element("style");
    style.textContent = STYLE;
    document.head.appendChild(style);

    const holder = element("div");
    open.addEventListener("click", () => showMenu());
    open.setAttribute("aria-haspopup", "dialog");
    const dialog = element("dialog", "roam-saves-dialog");
    dialog.setAttribute("aria-labelledby", "roam-saves-title");
    const fileInput = element("input");
    fileInput.type = "file";
    fileInput.accept = ".json,application/json";
    fileInput.style.display = "none";
    fileInput.setAttribute("aria-hidden", "true");
    fileInput.tabIndex = -1;
    holder.append(fileInput, dialog);
    // The game's keyboard listener is on the document and takes Enter,
    // Escape (which quits from the title screen), arrows and letters. While
    // the panel is open no key reaches it, wherever focus is: this listener
    // runs first (capture, on window) and stops the event there. The keys'
    // own defaults (Escape closes the dialog, Enter presses a button) still
    // happen. keyup is let through: the game only uses it to stop a held
    // arrow's repeat.
    window.addEventListener("keydown", (ev) => { if (dialog.open) ev.stopPropagation(); }, true);
    // The button must not keep keyboard focus (a closing dialog hands focus
    // back to it), or the game's Enter would also press it.
    open.addEventListener("mouseup", () => open.blur());
    dialog.addEventListener("close", () => open.blur());
    document.body.appendChild(holder);

    let channel = null;
    try {
      channel = new BroadcastChannel("roam-saves");
      channel.onmessage = (ev) => {
        if (!ev.data || ev.data.type !== "import") return;
        stopGame();
        render([
          element("h3", null, "Saves were loaded in another tab"),
          element("p", null, "This tab's game was stopped so it cannot overwrite them. Reload to keep playing."),
        ], [button("Reload", "primary", () => location.reload())]);
        showDialog();
      };
    } catch (e) { /* no BroadcastChannel: single-tab safety still holds */ }

    function showDialog() {
      if (dialog.open) return;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }

    function close() {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
    }

    function render(nodes, actions) {
      dialog.textContent = "";
      if (nodes[0]) nodes[0].id = "roam-saves-title";
      dialog.append(...nodes);
      if (actions && actions.length) {
        const row = element("div", "roam-saves-actions");
        row.append(...actions);
        dialog.appendChild(row);
        // Re-rendering removed the focused button; keep focus in the panel.
        if (dialog.open) actions[0].focus();
      }
    }

    function message(text, isError) {
      const node = element("p", "roam-saves-message" + (isError ? " error" : ""), text);
      node.setAttribute("role", isError ? "alert" : "status");
      return node;
    }

    function list(title, items) {
      if (!items.length) return [];
      const ul = element("ul");
      for (const item of items.slice(0, 12)) ul.appendChild(element("li", null, item));
      if (items.length > 12) ul.appendChild(element("li", null, "…and " + (items.length - 12) + " more"));
      return [element("p", null, title), ul];
    }

    async function showMenu(notice, noticeIsError) {
      const nodes = [
        element("h3", null, "Your saves"),
        element("p", null, "Your worlds are kept in this browser only. Download them to keep a copy, " +
          "or to carry them to another browser, device or Roam site and load them there."),
      ];
      if (notice) nodes.push(message(notice, noticeIsError));
      const actions = [
        button("Download my saves", "primary", exportSaves),
        button("Load saves from a file", null, () => { fileInput.value = ""; fileInput.click(); }),
        button("Close", null, close),
      ];
      if (stopped) {
        nodes.push(message("The game was stopped. Reload the page to keep playing.", true));
        actions.splice(1, 1);
        actions.unshift(button("Reload", null, () => location.reload()));
      }
      const backupNodes = [];
      try {
        const backups = await readBackups();
        if (backups.length) {
          backupNodes.push(element("p", "roam-saves-note",
            "Before each load, the saves this browser had were kept as a backup:"));
          const row = element("div", "roam-saves-actions");
          for (const backup of backups) {
            row.appendChild(button("Download backup from " + backup.exported.replace("T", " ").slice(0, 16),
              null, () => download(backup, exportName(backup.exported, "backup"))));
          }
          backupNodes.push(row);
        }
      } catch (e) { console.warn("[roam] could not list save backups:", e); }
      render(nodes.concat(backupNodes), actions);
      showDialog();
    }

    async function exportSaves() {
      let entries;
      try { entries = await readStore(); }
      catch (e) {
        console.warn("[roam] export failed:", e);
        showMenu("Your saves could not be read just now, so nothing was downloaded. Reloading the page usually fixes this.", true);
        return;
      }
      if (entries.size === 0) { showMenu("There are no saves in this browser yet."); return; }
      let doc;
      try { doc = buildExport(entries); }
      catch (e) { showMenu("Your saves could not be written to a file: " + e.message, true); return; }
      const worlds = Array.from(groupByWorld(entries).keys()).filter((w) => w);
      download(doc, exportName(doc.exported));
      showMenu("Downloaded " + worlds.length + " world(s) (" + entries.size + " files) as " +
               exportName(doc.exported) + ".");
    }

    fileInput.addEventListener("change", async () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      if (file.size > MAX_FILE_BYTES) { showMenu("That file is too large to be a Roam saves file. Nothing was changed.", true); return; }
      let text;
      try { text = await file.text(); }
      catch (e) { showMenu("That file could not be read. Nothing was changed.", true); return; }
      const parsed = parseImport(text);
      if (!parsed.ok) { showMenu(parsed.reason, true); return; }
      let current;
      try { current = await readStore(); }
      catch (e) { showMenu("Your current saves could not be read, so nothing was loaded. Nothing was changed.", true); return; }
      confirmImport(parsed, plan(current, parsed.files), false);
    });

    function confirmImport(parsed, p, again) {
      const nodes = [element("h3", null, "Load these saves?")];
      if (again) nodes.push(message("Your saves changed while this was open (the game saved). This is the up-to-date list.", true));
      if (!p.writes.size) {
        render(nodes.concat([message("Every world in this file is already here, exactly the same. Nothing needs to change.")]),
          [button(stopped ? "Reload" : "Close", null, stopped ? () => location.reload() : close)]);
        showDialog();
        return;
      }
      nodes.push(...list("New worlds (" + p.added.length + "):", p.added));
      nodes.push(...list("Already here but different: the file's copy is added under a new name, and yours is kept (" +
        p.renamed.length + "):",
        p.renamed.map(([from, to]) => from + " → " + to)));
      nodes.push(...list("Already here, unchanged (" + p.same.length + "):", p.same));
      nodes.push(...list("Your other worlds, kept as they are (" + p.kept.length + "):", p.kept));
      nodes.push(element("p", "roam-saves-note",
        "Nothing here is replaced or deleted. A backup of your saves as they are now is kept in this " +
        "browser first. The game then restarts; progress since your last save is not kept."));
      render(nodes, [
        button("Load and restart", "primary", () => applyImport(parsed, p)),
        button("Cancel", null, stopped ? () => location.reload() : close),
      ]);
      showDialog();
    }

    function failed(text) {
      render([element("h3", null, "Saves were not loaded"), message(text, true)],
        [button("Reload", "primary", () => location.reload())]);
      showDialog();
    }

    async function applyImport(parsed, shown) {
      for (const b of dialog.querySelectorAll("button")) b.disabled = true;
      stopGame();
      if (channel) {
        try { channel.postMessage({ type: "import" }); } catch (e) {}
        await new Promise((resolve) => setTimeout(resolve, 300));
      }
      let current;
      try { current = await readStore(); }
      catch (e) { failed("Your current saves could not be read, so nothing was loaded. Nothing was changed."); return; }
      const p = plan(current, parsed.files);
      if (planKey(p) !== planKey(shown)) { confirmImport(parsed, p, true); return; }
      if (current.size) {
        try { await writeBackup(buildExport(current)); }
        catch (e) {
          console.warn("[roam] backup failed:", e);
          failed("A backup of your current saves could not be kept, so nothing was loaded. Nothing was changed.");
          return;
        }
      }
      try {
        await addToStore(p.writes);
        const after = await readStore();
        for (const [path, value] of p.writes) {
          if (!after.has(path) || !sameValue(after.get(path), value)) throw new Error(path + " did not read back");
        }
        for (const [path, value] of current) {
          if (!after.has(path) || !sameValue(after.get(path), value)) throw new Error(path + " changed");
        }
      } catch (e) {
        console.warn("[roam] import failed:", e);
        failed("The saves could not be written completely (" + e.message + "). Your saves from just " +
               "before are in the backup offered under Saves after reloading.");
        return;
      }
      render([element("h3", null, "Saves loaded"), message("Restarting the game…")], []);
      location.reload();
    }

    return { showMenu: showMenu };
  }

  return {
    attach: attach,
    // Exposed for tests.
    _parseImport: parseImport,
    _buildExport: buildExport,
    _plan: plan,
    _checkPath: checkPath,
  };
})();
