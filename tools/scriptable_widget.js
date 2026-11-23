// Forellen statistik – iPhone-widget för appen Scriptable.
// Visar besök och sidvisningar på forellenslussfors.se från Cloudflare Web Analytics.
//
// Installera: Scriptable → + → klistra in hela filen → döp till "Forellen" → kör en gång
// (▶︎) och klistra in Cloudflare-nyckeln när den frågar. Nyckeln sparas i iPhonens
// nyckelring, aldrig i skriptet. Lägg sedan till en Scriptable-widget på hemskärmen,
// håll in den → Redigera widget → Script: Forellen.
// Ett tryck på widgeten kör skriptet och visar en färsk, större vy direkt.
// Byta nyckel: öppna Scriptable, kör Forellen därifrån, stäng vyn och välj "Byt nyckel".
//
// Cloudflare räknar dagar i UTC och siffrorna släpar några timmar.

const ACCOUNT = "817bbf005400304d46e1f931cf574253";
const HOST = "forellenslussfors.se";
const KEY = "forellen_cf_token";
const DASH = "https://dash.cloudflare.com/" + ACCOUNT + "/web-analytics";
const RUN = "scriptable:///run/" + encodeURIComponent(Script.name()) + "?tap=1";
const C = { bg: new Color("#0B1E1D"), card: new Color("#16302E"), text: Color.white(),
            muted: new Color("#9FB8B5"), accent: new Color("#E06A2C"), ice: new Color("#8FD3D9") };
const NAMES = { SE: "Sverige", LV: "Lettland", LT: "Litauen", EE: "Estland", FI: "Finland", NO: "Norge",
                DE: "Tyskland", PL: "Polen", GB: "Storbr.", US: "USA", DK: "Danmark", NL: "Nederl." };

async function token(forceAsk) {
  if (!forceAsk && Keychain.contains(KEY)) return Keychain.get(KEY);
  if (config.runsInWidget) return null;
  const a = new Alert();
  a.title = "Cloudflare-nyckel";
  a.message = "Klistra in API-nyckeln (Account Analytics: Read). Den sparas bara i nyckelringen.";
  a.addSecureTextField("nyckel");
  a.addAction("Spara"); a.addCancelAction("Avbryt");
  if (await a.presentAlert() === -1) return null;
  const t = a.textFieldValue(0).trim();
  if (t) Keychain.set(KEY, t);
  return t || null;
}

function iso(d) { return d.toISOString().slice(0, 10); }

async function load(tok) {
  const now = new Date(), from = new Date(now.getTime() - 6 * 864e5);
  const q = `query($acc:String!,$from:Date!,$to:Date!,$host:String!){viewer{accounts(filter:{accountTag:$acc}){
    days:rumPageloadEventsAdaptiveGroups(limit:100,filter:{date_geq:$from,date_leq:$to,requestHost:$host}){count sum{visits} dimensions{date}}
    ctry:rumPageloadEventsAdaptiveGroups(limit:40,orderBy:[count_DESC],filter:{date_geq:$from,date_leq:$to,requestHost:$host}){count dimensions{countryName}}}}}`;
  const r = new Request("https://api.cloudflare.com/client/v4/graphql");
  r.method = "POST";
  r.headers = { "Authorization": "Bearer " + tok, "Content-Type": "application/json" };
  r.body = JSON.stringify({ query: q, variables: { acc: ACCOUNT, from: iso(from), to: iso(now), host: HOST } });
  const j = await r.loadJSON();
  if (j.errors && j.errors.length) throw new Error(j.errors[0].message);
  const a = j.data.viewer.accounts[0];
  const byDay = {};
  a.days.forEach(g => byDay[g.dimensions.date] = { views: g.count, visits: g.sum.visits });
  const days = [];
  for (let i = 6; i >= 0; i--) { const d = iso(new Date(now.getTime() - i * 864e5)); days.push({ date: d, ...(byDay[d] || { views: 0, visits: 0 }) }); }
  const ctry = {};
  a.ctry.forEach(g => { const k = g.dimensions.countryName || "?"; ctry[k] = (ctry[k] || 0) + g.count; });
  const top = Object.entries(ctry).sort((x, y) => y[1] - x[1]).slice(0, 6);
  return { days, top };
}

function flag(cc) { return /^[A-Z]{2}$/.test(cc) ? String.fromCodePoint(...[...cc].map(c => 127397 + c.charCodeAt(0))) : "🌍"; }

function bars(days, w, h) {
  const ctx = new DrawContext(); ctx.size = new Size(w, h); ctx.opaque = false; ctx.respectScreenScale = true;
  const max = Math.max(1, ...days.map(d => d.views)), gap = 4, bw = (w - gap * (days.length - 1)) / days.length;
  days.forEach((d, i) => {
    const bh = Math.max(2, (d.views / max) * h);
    const p = new Path(); p.addRoundedRect(new Rect(i * (bw + gap), h - bh, bw, bh), 2, 2);
    ctx.addPath(p); ctx.setFillColor(i === days.length - 1 ? C.accent : C.ice); ctx.fillPath();
  });
  return ctx.getImage();
}

function txt(stack, s, size, color, weight) {
  const t = stack.addText(s); t.textColor = color; t.font = weight === "b" ? Font.boldSystemFont(size) : Font.systemFont(size);
  t.lineLimit = 1; t.minimumScaleFactor = 0.7; return t;
}

function build(data, err, famIn) {
  const fam = famIn || config.widgetFamily || "medium";
  const w = new ListWidget(); w.backgroundColor = C.bg; w.url = RUN; w.setPadding(12, 14, 12, 14);
  w.refreshAfterDate = new Date(Date.now() + 30 * 60e3);
  const head = w.addStack(); head.centerAlignContent();
  txt(head, "🎣 Forellen", 13, C.muted, "b"); head.addSpacer();
  txt(head, new Date().toLocaleTimeString("sv-SE", { hour: "2-digit", minute: "2-digit" }), 11, C.muted);
  w.addSpacer(6);
  if (err) { txt(w, err, 12, C.accent); return w; }
  const t = data.days[6], y = data.days[5], week = data.days.reduce((s, d) => s + d.views, 0);
  const row = w.addStack(); row.layoutHorizontally();
  const left = row.addStack(); left.layoutVertically();
  txt(left, String(t.views), fam === "small" ? 30 : 34, C.text, "b");
  txt(left, "sidvisningar i dag", 11, C.muted);
  txt(left, `${t.visits} besök · i går ${y.views}/${y.visits}`, 11, C.ice);
  if (fam !== "small") {
    row.addSpacer();
    const right = row.addStack(); right.layoutVertically();
    data.top.slice(0, fam === "large" ? 6 : 3).forEach(([cc, n]) => txt(right, `${flag(cc)} ${NAMES[cc] || cc} ${n}`, 12, C.text));
    if (!data.top.length) txt(right, "inga besök än", 12, C.muted);
  }
  if (fam === "large") {
    w.addSpacer(10);
    const DOW = ["sön", "mån", "tis", "ons", "tor", "fre", "lör"];
    data.days.slice().reverse().forEach(d => {
      const dt = new Date(d.date + "T12:00:00Z"), r = w.addStack();
      txt(r, `${DOW[dt.getUTCDay()]} ${dt.getUTCDate()}/${dt.getUTCMonth() + 1}`, 13, C.muted); r.addSpacer();
      txt(r, `${d.views} sidvisn. · ${d.visits} besök`, 13, C.text);
    });
  }
  w.addSpacer();
  const img = w.addImage(bars(data.days, fam === "small" ? 130 : 290, 28)); img.imageSize = new Size(fam === "small" ? 130 : 290, 28);
  w.addSpacer(3);
  txt(w, `7 dagar: ${week} sidvisningar` + (fam === "small" ? "" : " · länder senaste 7 d"), 10, C.muted);
  return w;
}

async function main() {
  const fam = config.runsInWidget ? null : "large";   // tapped or run in the app: large view
  const tok = await token(false);
  let widget, authErr = false;
  if (!tok) widget = build(null, "Ingen nyckel. Tryck på widgeten för att lägga in den.", fam);
  else {
    try { widget = build(await load(tok), null, fam); }
    catch (e) { authErr = /auth|token|permission/i.test(e.message); widget = build(null, "Kunde inte hämta: " + e.message, fam); }
  }
  if (config.runsInWidget) { Script.setWidget(widget); return; }
  await widget.presentLarge();
  const tapped = args.queryParameters && args.queryParameters.tap;
  if (tapped && !authErr) return;   // from the widget: just the view, no questions
  if (authErr) { await token(true); return; }
  const a = new Alert(); a.title = "Forellen statistik";
  a.addAction("Klar"); a.addAction("Öppna Cloudflare"); a.addAction("Byt nyckel");
  const c = await a.presentSheet();
  if (c === 1) Safari.open(DASH);
  if (c === 2) await token(true);
}
await main();
Script.complete();
