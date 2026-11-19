/* Declared account form (`TOKEN_FORM` -> `k.form_tk`) drawn by `veFormTK` in conversations.js.

       node tests/js/test_form_tk_khai_bao.js

   Runs the real function on a tiny fake DOM (no browser). Guarded here:
   1. A select without dependencies loads its list on open (GET); `auto_single` picks the only item on an Add form.
   2. A field hidden by `hidden_when` is emptied and not required while hidden.
   3. A dependent list POSTs its fields as a form body (a typed key never in a URL) and `fill` copies the item.
   4. The token is ONE JSON object of the sent fields; `send: false` fields stay out; a missing field throws.
   5. Edit form: fields (the workspace select too) start from the saved account; untouched = "" (no change),
      touched = a full token, so changing only the secret keeps the workspace.
*/
const fs = require("fs");
const path = require("path");
const CV = fs.readFileSync(path.join(__dirname, "..", "..", "dashboard", "conversations.js"), "utf8");

let fails = [];
function check(name, cond, extra) {
  console.log((cond ? "ok   " : "FAIL ") + name + (cond || extra === undefined ? "" : "  [" + extra + "]"));
  if (!cond) fails.push(name);
}

const a = CV.indexOf("  function veFormTK(");
const b = CV.indexOf("  // Query string of the webhook-info");
check("veFormTK found", a > 0 && b > a);
const SRC = CV.slice(a, b);

// ---- fake DOM: enough for the markup veFormTK writes ----
function attrs(s) { const o = {}; s.replace(/([a-z-]+)="([^"]*)"/g, (_, k, v) => { o[k] = v.replace(/&quot;/g, '"').replace(/&amp;/g, "&"); }); return o; }
function node(tag, at, parent) {
  const n = { tag, id: at.id || "", cls: at.class || "", dataset: {}, hidden: false, disabled: false, parent,
              value: at.value || "", type: at.type || "", options: [], selectedIndex: 0 };
  Object.keys(at).forEach((k) => { if (k.startsWith("data-")) n.dataset[k.slice(5)] = at[k]; });
  if (tag === "select") {
    Object.defineProperty(n, "innerHTML", {
      set(h) {
        n.options = [];
        h.replace(/<option([^>]*)>([^<]*)<\/option>/g, (_, at2, txt) => {
          const x = attrs(at2); n.options.push({ value: x.value || "", text: txt, dataset: x["data-i"] != null ? { i: x["data-i"] } : {} });
        });
        n.selectedIndex = 0; n.value = n.options.length ? n.options[0].value : "";
      }, get() { return ""; } });
    Object.defineProperty(n, "_v", { value: null, writable: true });
  }
  return n;
}
function makeHost() {
  const host = { nodes: [] };
  Object.defineProperty(host, "innerHTML", {
    set(h) {
      host.nodes = [];
      let cur = null;
      h.replace(/<(div|select|input|button)([^>]*)>/g, (_, tag, at) => {
        const x = attrs(at);
        const n = node(tag, x, cur);
        if (tag === "div" && (x.class || "") === "ht-ftk") cur = n;
        host.nodes.push(n);
      });
    }, get() { return ""; } });
  host.querySelector = function (q) {
    let m;
    if ((m = /^#(.+)$/.exec(q))) return host.nodes.find((n) => n.id === m[1]) || null;
    if ((m = /^\.ht-ftk\[data-k="(.+)"\]$/.exec(q))) return host.nodes.find((n) => n.cls === "ht-ftk" && n.dataset.k === m[1]) || null;
    if ((m = /^\[data-(st|load|gen|copy)="(.+)"\]$/.exec(q))) return host.nodes.find((n) => n.dataset[m[1]] === m[2]) || null;
    return null;
  };
  return host;
}
// A select's value must follow selectedIndex the way a browser does.
function pick(sel, value) { sel.value = value; sel.selectedIndex = sel.options.findIndex((o) => o.value === value); }

const calls = [];
const replies = {
  "/ext/p/connections": { connections: [{ id: "ws1", label: "Shop" }] },
  "/ext/p/accounts": { accounts: [{ id: "acc9", username: "shop", platform: "instagram" }] },
};
const api = async (url, opts) => { calls.push({ url, opts }); return replies[url]; };
const window = { t: (k, v) => k + (v ? ":" + JSON.stringify(v) : ""), crypto: require("crypto").webcrypto };
const esc = (s) => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const fd = (o) => ({ form: o });
const veFormTK = new Function("api", "fd", "esc", "window", "infoBtn", "infoBody",
  SRC + "\nreturn veFormTK;")(api, fd, esc, window, () => "", (h) => "<div>" + h + "</div>");

const FORM = { fields: [
  { key: "connection_id", type: "select", label: "WS", send: true, required: false, initial: "meta.connection_id",
    options: { url: "/ext/p/connections", list: "connections", value: "id", label: "{label}", from: [], fill: {}, auto_single: true } },
  { key: "api_key", type: "password", label: "API key", send: true, required: false, required_unless: "connection_id", hidden_when: "connection_id" },
  { key: "account", type: "select", label: "Acc", send: false, required: false,
    options: { url: "/ext/p/accounts", list: "accounts", value: "id", label: "@{username} ({platform})",
               from: ["connection_id", "api_key"], fill: { account_id: "id", username: "username" }, auto_single: false } },
  { key: "account_id", type: "text", label: "Account ID", send: true, required: true, initial: "meta.account_id" },
  { key: "username", type: "text", label: "Username", send: true, required: true, initial: "external_id" },
  { key: "secret", type: "password", label: "Secret", send: true, required: false, generate: true },
] };
const tick = () => new Promise((r) => setTimeout(r, 0));

(async () => {
  // ---- Add form ----
  const h = makeHost();
  const f = veFormTK(h, FORM, null);
  await tick(); await tick(); await tick();
  const q = (k) => h.querySelector("#htF_" + k);
  check("1. connection list loaded by GET", calls[0] && calls[0].url === "/ext/p/connections" && !calls[0].opts);
  check("1. auto_single picked the only workspace", q("connection_id").value === "ws1", q("connection_id").value);
  check("2. API key hidden while a workspace is chosen", h.querySelector('.ht-ftk[data-k="api_key"]').hidden === true);
  const post = calls.find((c) => c.url === "/ext/p/accounts");
  check("3. dependent list POSTed with the workspace", post && post.opts.method === "POST" && post.opts.body.form.connection_id === "ws1",
        JSON.stringify(post));
  check("3. key never in the URL", calls.every((c) => !/api_key|ws1/.test(c.url)));
  let threw = "";
  try { f.token(); } catch (e) { threw = e.message; }
  check("4. missing required fields throw", /Account ID/.test(threw) && /Username/.test(threw) && !/API key/.test(threw), threw);
  pick(q("account"), "acc9"); q("account").onchange();
  check("3. fill copied account id and username", q("account_id").value === "acc9" && q("username").value === "shop");
  q("secret").value = "s3cret"; q("secret").oninput();
  const tok = JSON.parse(f.token());
  check("4. one JSON token, send:false left out", JSON.stringify(tok) === JSON.stringify(
    { connection_id: "ws1", account_id: "acc9", username: "shop", secret: "s3cret" }), JSON.stringify(tok));

  // No workspace: the API key shows again and becomes required.
  pick(q("connection_id"), ""); q("connection_id").onchange();
  check("2. API key shown without a workspace", h.querySelector('.ht-ftk[data-k="api_key"]').hidden === false);
  threw = ""; try { f.token(); } catch (e) { threw = e.message; }
  check("2. API key required without a workspace", /API key/.test(threw), threw);

  // ---- Edit form ----
  calls.length = 0;
  const h2 = makeHost();
  const acc = { external_id: "shop", meta: { account_id: "acc9", connection_id: "ws1" } };
  const g = veFormTK(h2, FORM, acc);
  await tick(); await tick();
  const q2 = (k) => h2.querySelector("#htF_" + k);
  check("5. edit starts from the saved account", q2("account_id").value === "acc9" && q2("username").value === "shop");
  check("5. edit selects the saved workspace", q2("connection_id").value === "ws1", q2("connection_id").value);
  check("5. saved workspace hides the API key", h2.querySelector('.ht-ftk[data-k="api_key"]').hidden === true);
  check("5. untouched edit sends no token", g.token() === "");
  q2("secret").value = "new"; q2("secret").oninput();
  const t2 = JSON.parse(g.token());
  check("5. changing only the secret keeps the workspace", t2.connection_id === "ws1" && t2.secret === "new" && t2.account_id === "acc9",
        JSON.stringify(t2));

  // ---- Generated secret ----
  const h3 = makeHost();
  const k3 = veFormTK(h3, FORM, null);
  await tick(); await tick();
  const s3 = h3.querySelector("#htF_secret");
  check("6. generate button drawn", !!h3.querySelector('[data-gen="secret"]') && !!h3.querySelector('[data-copy="secret"]'));
  check("6. no generate button on plain fields", !h3.querySelector('[data-gen="account_id"]'));
  h3.querySelector('[data-gen="secret"]').onclick();
  const v1 = s3.value;
  check("6. 64 hex chars", /^[0-9a-f]{64}$/.test(v1), v1);
  check("6. shown after generating", s3.type === "text");
  h3.querySelector('[data-gen="secret"]').onclick();
  check("6. a new value each press", s3.value !== v1 && /^[0-9a-f]{64}$/.test(s3.value));
  h3.querySelector("#htF_account_id").value = "a"; h3.querySelector("#htF_username").value = "u";
  check("6. generated secret is sent", JSON.parse(k3.token()).secret === s3.value);
  // Edit: generating marks the form dirty, so a rotated secret is posted.
  const h4 = makeHost();
  const k4 = veFormTK(h4, FORM, { external_id: "shop", meta: { account_id: "acc9", connection_id: "ws1" } });
  await tick(); await tick();
  h4.querySelector('[data-gen="secret"]').onclick();
  check("6. edit + generate posts the new secret", JSON.parse(k4.token()).secret === h4.querySelector("#htF_secret").value);

  console.log("\n" + (fails.length ? fails.length + " FAIL" : "ALL OK"));
  process.exit(fails.length ? 1 : 0);
})();
