/* arcade-scores.js 0.1.0 (arcade-social, RFC 0014); see README.md. Vendor as is. */
(function (root) {
  var API = "https://api.play.danielstephenson.dev";
  function isId(s) { return typeof s == "string" && /^[a-z][a-z0-9-]{1,30}$/.test(s); }
  var who = null, retryMs = 30000;
  function nul() { return null; }
  function here() {
    try {
      var l = root.location, m = /^([a-z][a-z0-9-]{1,30})\.play\.danielstephenson\.dev$/.exec(l.hostname);
      return l.protocol == "https:" && m && m[1] != "api" && typeof fetch == "function" ? m[1] : null;
    } catch (e) { return nul(); }
  }
  function get(path, cred) {
    return fetch(API + path, cred ? { credentials: "include" } : {})
      .then(function (r) { return r.ok ? r.json() : null; })
      .catch(nul);
  }
  function whoami() {
    if (!here()) return Promise.resolve(null);
    if (who && Date.now() - who.at < 60000) return who.p;
    who = { at: Date.now(), p: get("/v1/session", 1).then(function (s) {
      return s && typeof s.signedIn == "boolean" ? { signedIn: s.signedIn, displayName: s.displayName || null } : null;
    }) };
    return who.p;
  }
  function post(path, body, again) {
    function retry() { if (!again) setTimeout(function () { post(path, body, 1); }, retryMs); return null; }
    return fetch(API + path, {
      method: "POST", credentials: "include", body: JSON.stringify(body),
      headers: { "Content-Type": "application/json", "X-Play-Client": "1" }
    }).then(function (r) {
      if (r.status > 499) retry();
      return r.ok ? r.json() : null;
    }, retry).catch(nul);
  }
  function report(ok, path, body) {
    try {
      if (!ok || !here()) return Promise.resolve(null);
      return whoami().then(function (me) {
        return me && !me.signedIn ? null : post(path, body);
      }).catch(nul);
    } catch (e) { return Promise.resolve(null); }
  }
  function submit(board, value, run) {
    var body = { value: value };
    if (run !== undefined) body.run = run;
    return report(isId(board) && typeof value == "number" && isFinite(value) &&
      (run === undefined || typeof run == "string" && /^[A-Za-z0-9._:-]{1,64}$/.test(run)), "/v1/scores/" + board, body);
  }
  function top(board, limit) {
    var slug = here();
    if (!slug || !isId(board)) return Promise.resolve([]);
    return get("/v1/boards/" + slug + "/" + board + "?limit=" + Math.max(1, Math.min(100, limit | 0 || 10)))
      .then(function (b) { return (b && b.entries) || []; });
  }
  function signIn() {
    var url = API + "/signin?return=" + encodeURIComponent(root.location.href);
    try { root.top.location.assign(url); } catch (e) { root.location.assign(url); }
  }
  var api = {
    submit: submit, submitScore: submit, whoami: whoami, top: top, signIn: signIn,
    unlock: function (id) { return report(isId(id), "/v1/achievements/" + id, {}); },
    _reset: function (ms) { who = null; retryMs = ms; }
  };
  if (typeof module == "object" && module.exports) module.exports = api;
  root.ArcadeScores = api;
})(typeof window != "undefined" ? window : globalThis);
