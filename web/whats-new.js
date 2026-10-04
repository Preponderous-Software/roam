// The "What's new" panel of the browser build (a button beside Saves).
//
// It lists the newest player-facing changes, read from /web/whats-new.json,
// which web/build_zip.py writes from CHANGELOG.md's "## What's new" section
// (web/whats_new.py). When that file is missing, unreadable or empty the
// button is hidden and nothing else happens.
//
// This panel only reads one JSON file and shows it. It has no access to the
// game's worlds: it never opens a browser database, never talks to the game's
// Worker and never stops or pauses the game. The one thing it stores is the
// newest entry the player has seen (localStorage, key SEEN_KEY), so the
// button can carry a dot until they open it; if storage is unavailable the
// dot is simply shown.

window.RoamWhatsNew = (function () {
  "use strict";

  const SOURCE = "/web/whats-new.json";
  const SEEN_KEY = "roam.whats-new.seen";
  const MAX_ENTRIES = 12;

  const STYLE = `
.roam-whats-new-dialog {
  font: 16px/1.45 system-ui, sans-serif; color: #ddd; background: #111;
  border: 1px solid #333; border-radius: 10px; padding: 1rem 1.1rem; margin: auto;
  width: min(34rem, calc(100vw - 32px)); max-height: calc(100dvh - 32px);
  box-sizing: border-box; overflow-y: auto; overflow-wrap: anywhere;
  user-select: text; -webkit-user-select: text; touch-action: pan-y;
}
.roam-whats-new-dialog::backdrop { background: rgba(0, 0, 0, .7); }
.roam-whats-new-dialog h3 { margin: 0 0 .75rem; font-size: 1.15rem; outline: none; }
.roam-whats-new-dialog ul { list-style: none; margin: 0; padding: 0; }
.roam-whats-new-dialog li { padding: .55rem 0; border-top: 1px solid #262626; }
.roam-whats-new-dialog li:first-child { border-top: 0; padding-top: 0; }
.roam-whats-new-dialog time { display: block; color: #888; font-size: .8rem; }
.roam-whats-new-dialog b { color: #e8c35a; font-weight: 600; }
.roam-whats-new-dialog p { margin: .15rem 0 0; color: #bbb; font-size: .95rem; }
.roam-whats-new-dialog .roam-whats-new-actions {
  display: flex; justify-content: flex-end; margin: .5rem -1.1rem -1rem; padding: .6rem 1.1rem .9rem;
  position: sticky; bottom: -1rem; background: #111; border-top: 1px solid #262626;
}
.roam-whats-new-dialog button {
  font: 16px system-ui, sans-serif; min-height: 44px; min-width: 44px;
  padding: .5rem 1.25rem; border-radius: 6px; cursor: pointer;
  border: 1px solid #444; background: #1e1e1e; color: #ddd;
  touch-action: manipulation; -webkit-tap-highlight-color: transparent;
}
.roam-whats-new-dialog button:hover { background: #2a2a2a; }
@media (max-width: 600px) { .roam-whats-new-dialog .roam-whats-new-actions button { flex: 1 1 100%; } }
.roam-whats-new-unseen { position: relative; }
.roam-whats-new-unseen::after {
  content: ""; position: absolute; top: 3px; right: 3px; width: 7px; height: 7px;
  border-radius: 50%; background: #e8c35a;
}
`;

  // -- Pure helpers (no DOM, no storage) ---------------------------------------

  function isEntry(value) {
    return !!value && typeof value === "object" &&
      typeof value.date === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value.date) &&
      typeof value.title === "string" && value.title.length > 0 &&
      typeof value.text === "string";
  }

  // The entries of a whats-new.json body; anything malformed is skipped.
  function parse(body) {
    const entries = body && Array.isArray(body.entries) ? body.entries : [];
    return entries.filter(isEntry).slice(0, MAX_ENTRIES);
  }

  function marker(entries) {
    return entries.length ? entries[0].date + " " + entries[0].title : "";
  }

  function formatDate(iso) {
    const d = new Date(iso + "T12:00:00Z");
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
  }

  // -- localStorage (the seen marker only; failures mean "not seen") ----------

  function readSeen() {
    try { return window.localStorage.getItem(SEEN_KEY) || ""; } catch (e) { return ""; }
  }

  function writeSeen(value) {
    try { window.localStorage.setItem(SEEN_KEY, value); } catch (e) { /* the dot just stays */ }
  }

  // -- The panel ---------------------------------------------------------------

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function render(dialog, entries) {
    dialog.textContent = "";
    const title = element("h3", null, "What's new in Roam");
    title.id = "roam-whats-new-title";
    title.tabIndex = -1;
    const list = element("ul");
    for (const entry of entries) {
      const item = element("li");
      const when = element("time", null, formatDate(entry.date));
      when.dateTime = entry.date;
      item.append(when, element("b", null, entry.title));
      if (entry.text) item.appendChild(element("p", null, entry.text));
      list.appendChild(item);
    }
    const actions = element("div", "roam-whats-new-actions");
    const close = element("button", null, "Close");
    close.type = "button";
    close.addEventListener("click", () => {
      if (typeof dialog.close === "function") dialog.close();
      else dialog.removeAttribute("open");
    });
    actions.appendChild(close);
    dialog.append(title, list, actions);
  }

  // options: { button: element,     - the page's "What's new" button
  //            fetchImpl: function } - optional, for tests
  // Resolves to the number of entries shown (0: the button was hidden).
  async function attach(options) {
    const open = options.button;
    const fetchImpl = options.fetchImpl || window.fetch.bind(window);
    let entries = [];
    try {
      const response = await fetchImpl(SOURCE, { cache: "no-cache" });
      if (response.ok) entries = parse(await response.json());
    } catch (e) {
      entries = [];
    }
    if (!entries.length) {
      // Hidden but kept in place, so the touch d-pad's grid does not shift.
      open.style.visibility = "hidden";
      return 0;
    }

    const style = element("style");
    style.textContent = STYLE;
    document.head.appendChild(style);

    const dialog = element("dialog", "roam-whats-new-dialog");
    dialog.setAttribute("aria-labelledby", "roam-whats-new-title");
    render(dialog, entries);
    document.body.appendChild(dialog);

    // The game's keyboard listener is on the document; while the panel is
    // open no key reaches it (Escape still closes the dialog). Same rule as
    // the Saves panel.
    window.addEventListener("keydown", (ev) => { if (dialog.open) ev.stopPropagation(); }, true);
    open.addEventListener("mouseup", () => open.blur());
    dialog.addEventListener("close", () => open.blur());
    // A tap outside the panel (on the backdrop) closes it.
    dialog.addEventListener("click", (ev) => {
      if (ev.target === dialog && typeof dialog.close === "function") dialog.close();
    });

    const newest = marker(entries);
    if (readSeen() !== newest) open.classList.add("roam-whats-new-unseen");

    open.setAttribute("aria-haspopup", "dialog");
    open.addEventListener("click", () => {
      writeSeen(newest);
      open.classList.remove("roam-whats-new-unseen");
      if (dialog.open) return;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
      // Focus the heading, not Close: on a phone, focusing Close would
      // scroll the list to its end.
      const heading = dialog.querySelector("#roam-whats-new-title");
      if (heading) heading.focus({ preventScroll: true });
      dialog.scrollTop = 0;
    });
    open.style.visibility = "visible";
    return entries.length;
  }

  return { attach: attach, parse: parse, SEEN_KEY: SEEN_KEY };
})();
