// Shoot files and the Director, for the Series panel.
//
// A shoot file (nodes/shoot_datei.py) is the whole shoot in one JSON: the
// states of the Person, Wardrobe, Pose, Expression, Lighting, Style, Location
// and Series nodes as they sit in node.properties, plus the scene text and the Build
// Prompt template. This module collects them from the graph and writes them
// back; the Series panel shows one row for it (shootZeile) and a dialog for
// loading and for the Director (one sentence -> a whole shoot, via any chat LLM).
//
// Which nodes: the ones wired to this Series node - the person on its
// person_data input, her Wardrobe, the Location node on ort_data, and on the
// Build Prompt node it feeds the
// builders, the scene and the template. Where nothing is wired, the one node
// of that class in the graph, if there is exactly one; with several and none
// wired, that section is left out rather than guessed. Top-level graph only.
//
// Which class holds which section, and which inputs lead there, comes from
// /krea2/presets ("shoot"), so the two sides cannot drift apart.

import {
  injiziereCSS,
  ladePresets,
  nodeGeaendert,
  t as uet,
  tf as uetf,
  wardrobeVonPerson,
} from "./shared.mjs?v=2.9.0";

import { app } from "../../scripts/app.js";

const JOIN = "Krea2PromptJoin";
const REROUTE_TIEFE = 8;
const EMBED_ABSCHNITTE = new Set(["person", "wardrobe", "lighting", "style", "location"]);
const TEXT_PROPS = { scene: "sceneText", template: "templateText" };

// ----------------------------------------------------------------- Graph ---
const holeLink = (id) =>
  id == null ? null : (app.graph?.links?.get?.(id) ?? app.graph?.links?.[id]);
const holeNode = (id) => app.graph?.getNodeById?.(id) ?? null;
const alleNodes = () => app.graph?._nodes || app.graph?.nodes || [];

// The node on an input, through reroutes.
function quelle(node, eingang) {
  let n = node;
  let name = eingang;
  for (let i = 0; n && i < REROUTE_TIEFE; i++) {
    const inp = name == null ? n.inputs?.[0] : n.inputs?.find((x) => x.name === name);
    const link = holeLink(inp?.link);
    const q = link && holeNode(link.origin_id);
    if (!q) return null;
    if (q.type !== "Reroute") return q;
    n = q;
    name = null;
  }
  return null;
}

// The first node of a class downstream of this one, through reroutes.
function ziel(node, klasse) {
  const gesehen = new Set();
  const stapel = [node];
  while (stapel.length) {
    const n = stapel.pop();
    if (!n || gesehen.has(n.id)) continue;
    gesehen.add(n.id);
    for (const aus of n.outputs || []) {
      for (const id of aus.links || []) {
        const link = holeLink(id);
        const z = link && holeNode(link.target_id);
        if (z?.comfyClass === klasse) return z;
        if (z?.type === "Reroute") stapel.push(z);
      }
    }
  }
  return null;
}

// The one node of a class in the graph, or null when there are none or several.
function einzig(klasse) {
  const liste = alleNodes().filter((n) => n?.comfyClass === klasse);
  return liste.length === 1 ? liste[0] : null;
}

// The text widget of a scene or template node (a primitive string, a text
// box of another pack). Combos are names, not text.
function textWidget(node) {
  return (node?.widgets || []).find((w) =>
    typeof w.value === "string" && w.type !== "combo" && !/^(name|filename_prefix)$/.test(w.name)) || null;
}

const anzahlKlasse = (klasse) => alleNodes().filter((n) => n?.comfyClass === klasse).length;

/** Where each section of a shoot lives for this Series node: {section: node|null}. */
export function ziele(serie, info) {
  const klasse = (a) => info.abschnitte[a]?.klasse;
  const ueber = (von, a) => {
    for (const e of info.eingaenge[a] || []) {
      const q = von && quelle(von, e);
      if (q?.comfyClass === klasse(a)) return q;
    }
    return null;
  };
  const z = { series: serie };
  z.person = ueber(serie, "person") || einzig(klasse("person"));
  z.wardrobe = (z.person && wardrobeVonPerson(z.person)) || einzig(klasse("wardrobe"));
  if (info.abschnitte.location) z.location = ueber(serie, "location") || einzig(klasse("location"));
  const join = ziel(serie, JOIN) || einzig(JOIN);
  for (const a of ["pose", "expression", "lighting", "style"]) z[a] = ueber(join, a) || einzig(klasse(a));
  for (const a of info.texte) {
    const q = join && (info.eingaenge[a] || []).map((e) => quelle(join, e)).find(Boolean);
    z[a] = textWidget(q) ? q : null;
  }
  for (const a of EMBED_ABSCHNITTE) {
    if (z[a] || !serie || !info.abschnitte[a]) continue;
    const prop = info.abschnitte[a].prop;
    if ((serie.properties?.[prop] !== undefined || serie.properties?.studioModus)
        && anzahlKlasse(klasse(a)) === 0) {
      z[a] = serie;
    }
  }
  for (const a of info.texte) {
    if (z[a] || !serie) continue;
    if (serie.properties?.[TEXT_PROPS[a]] !== undefined || serie.properties?.studioModus) {
      z[a] = serie;
    }
  }
  return z;
}

function liesProp(node, prop) {
  const roh = node?.properties?.[prop];
  if (!roh) return {};
  try {
    const s = typeof roh === "string" ? JSON.parse(roh) : roh;
    return s && typeof s === "object" ? s : {};
  } catch (e) {
    return {};
  }
}

/** The shoot of this Series node as a file object - the node states verbatim. */
export function sammle(serie, info) {
  const z = ziele(serie, info);
  const shoot = { format: info.format };
  for (const [a, { prop }] of Object.entries(info.abschnitte)) {
    if (!z[a]) continue;
    if (z[a] === serie && a !== "series" && serie.properties?.[prop] === undefined) continue;
    shoot[a] = liesProp(z[a], prop);
  }
  for (const a of info.texte) {
    if (!z[a]) continue;
    if (z[a] === serie) {
      const v = serie.properties?.[TEXT_PROPS[a]];
      if (typeof v === "string" && v !== "") shoot[a] = v;
    } else {
      const w = textWidget(z[a]);
      if (w) shoot[a] = w.value;
    }
  }
  return shoot;
}

function setzeText(node, w, wert) {
  w.value = wert;
  try { w.callback?.(wert); } catch (e) { /* a pack's own callback - the value is set */ }
  node.setDirtyCanvas?.(true, true);
}

function neuZeichnen(info) {
  const klassen = new Set(Object.values(info.abschnitte).map((x) => x.klasse));
  for (const n of alleNodes()) {
    if (klassen.has(n?.comfyClass)) {
      n._k2Zeichne?.();
      nodeGeaendert(n);
    }
  }
  app.graph?.setDirtyCanvas?.(true, true);
  app.graph?.change?.();
}

// The Director's series goes onto the current one, as a recipe does: its plan
// replaces the axes and pools, while size, start number, takes and whatever
// else the panel keeps stay. A loaded shoot file replaces the whole state.
function mischeSerie(alt, neu) {
  return { ...alt, ...neu, aktiv: { ...(alt.aktiv || {}), ...(neu.aktiv || {}) },
           pools: { ...(neu.pools || {}) } };
}

// The Director picks labels, not identities: a LoRA trigger or a reference
// the current person carries stays, so a shoot in reference or LoRA mode keeps
// its person. A loaded shoot file replaces the person as a whole.
const IDENTITAET = ["trigger", "referenz"];
function behaltePerson(alt, neu) {
  const texte = { ...(neu.texte || {}) };
  for (const t of IDENTITAET) if (alt?.texte?.[t]) texte[t] = alt.texte[t];
  return { ...neu, texte };
}

/** Writes a (checked) shoot into the nodes. Returns {bericht, rueckgaengig}:
 *  per section the node it went to (null = no node, skipped), and a function
 *  that puts back exactly what was there before. mischen: the Director's
 *  series is merged onto the current one instead of replacing it, and the
 *  person keeps its LoRA trigger and reference. */
export function wendeAn(serie, shoot, info, { mischen = false } = {}) {
  const z = ziele(serie, info);
  const vorher = [];
  const bericht = [];
  for (const [a, { prop }] of Object.entries(info.abschnitte)) {
    if (!(a in shoot)) continue;
    let n = z[a];
    if (!n && EMBED_ABSCHNITTE.has(a) && serie && anzahlKlasse(info.abschnitte[a]?.klasse) === 0) {
      n = serie;
    }
    bericht.push({ abschnitt: a, node: n || null });
    if (!n) continue;
    n.properties = n.properties || {};
    const alt = n.properties[prop];
    const wert = !mischen ? shoot[a]
      : a === "series" ? mischeSerie(liesProp(n, prop), shoot[a])
      : a === "person" ? behaltePerson(liesProp(n, prop), shoot[a]) : shoot[a];
    const leer = !Object.keys(wert || {}).length;
    // Unchanged: the stored string stays as it is, byte for byte.
    if (alt === undefined ? leer : JSON.stringify(liesProp(n, prop)) === JSON.stringify(wert) && !leer) continue;
    vorher.push(() => {
      if (alt === undefined) delete n.properties[prop];
      else n.properties[prop] = alt;
    });
    // An empty section is a node that never had a state (it shows its
    // defaults): the property goes, as it was, rather than becoming "{}".
    if (leer) delete n.properties[prop];
    else n.properties[prop] = JSON.stringify(wert);
  }
  for (const a of info.texte) {
    if (!(a in shoot)) continue;
    const zielNode = z[a] || (serie?.properties?.studioModus ? serie : null);
    if (zielNode === serie) {
      const prop = TEXT_PROPS[a];
      bericht.push({ abschnitt: a, node: serie });
      serie.properties = serie.properties || {};
      const alt = serie.properties[prop];
      const neu = String(shoot[a] ?? "");
      if (alt !== neu) {
        vorher.push(() => {
          if (alt === undefined) delete serie.properties[prop];
          else serie.properties[prop] = alt;
        });
        serie.properties[prop] = neu;
      }
      continue;
    }
    const w = textWidget(zielNode);
    bericht.push({ abschnitt: a, node: w ? zielNode : null });
    if (!w) continue;
    const alt = w.value;
    vorher.push(() => setzeText(zielNode, w, alt));
    setzeText(zielNode, w, shoot[a]);
  }
  neuZeichnen(info);
  return {
    bericht,
    rueckgaengig: () => {
      for (const f of vorher) f();
      neuZeichnen(info);
    },
  };
}

// ---------------------------------------------------------- Server calls ---
async function anfrage(pfad, daten) {
  const r = await fetch(pfad, daten === undefined ? { cache: "no-store" } : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(daten),
  });
  let antwort = null;
  try { antwort = await r.json(); } catch (e) { antwort = null; }
  if (!r.ok && !antwort) throw new Error("HTTP " + r.status);
  return antwort;
}

// The saved shoots, shared by every Series node on the page.
let _liste = null;
let _listeLaedt = false;
function zeichneSerien() {
  for (const n of alleNodes()) if (n?.comfyClass === "Krea2Photoshooting") n._k2Zeichne?.();
}
async function listeAnfrage(pfad, daten) {
  try {
    const a = await anfrage(pfad, daten);
    if (Array.isArray(a?.shoots)) _liste = a.shoots;
    zeichneSerien();
    return a;
  } catch (e) {
    _liste ||= [];
    zeichneSerien();
    return { error: String(e.message || e) };
  }
}

// --------------------------------------------------------------- Summary ---
const BEREICH = { person: "person", wardrobe: "person", pose: "pose", expression: "ausdruck",
                  lighting: "lighting", style: "style", location: "location" };
const NAMEN = { person: "Person", wardrobe: "Garderobe", pose: "Pose", expression: "Ausdruck",
                lighting: "Licht", style: "Stil", location: "Location", series: "Serie", scene: "Szene",
                template: "Prompt-Vorlage" };
const MAX_LABELS = 9;

function kurz(liste) {
  return liste.length > MAX_LABELS
    ? liste.slice(0, MAX_LABELS).join(" · ") + " · +" + (liste.length - MAX_LABELS)
    : liste.join(" · ");
}

function labels(st, bereich, leer) {
  return Object.entries(st?.felder || {})
    .filter(([, l]) => typeof l === "string" && l && l !== leer)
    .map(([c, l]) => uet(l, bereich + "/" + c));
}

function zusammenfassung(a, st, daten) {
  const leer = daten.person?.leer ?? "—";
  if (a === "scene" || a === "template") {
    const s = String(st || "");
    return s.length > 140 ? s.slice(0, 140) + " …" : s;
  }
  if (a === "person") {
    const m = (st?.mehrfach?.skinFeatures || []).map((l) => uet(l, "person/skinFeatures"));
    return kurz([...labels(st, "person", leer), ...m]);
  }
  if (a === "wardrobe") {
    return (st?.outfits || []).map((o, i) =>
      ((o.name || "").trim() || uetf("Outfit {0}", "ui", i + 1)) + ": " +
      (kurz(labels(o, "person", leer)) || "—")).join("  |  ");
  }
  if (a === "location") {
    return (st?.saetze || []).map((s, i) =>
      ((s.name || "").trim() || uetf("Set {0}", "ui", i + 1)) + ": " +
      (kurz(labels(s, "location", leer)) || (s.details || "").trim().slice(0, 60) || "—")).join("  |  ");
  }
  if (a === "series") {
    const sh = daten.shooting || {};
    const teile = [uetf("{0} Fotos", "ui", st?.anzahl ?? 12)];
    if (st?.start) teile.push(uetf("ab Nr. {0}", "ui", st.start));
    teile.push(st?.kameras?.length ? st.kameras.map((l) => uet(l, "shooting/kamera")).join(", ")
                                   : uet("alle Einstellungen", "ui"));
    for (const [c, v] of Object.entries(st?.pools || {})) {
      if (v === sh.alle) continue;
      const wert = v === sh.leer ? uet("aus", "ui")
        : (Array.isArray(v) ? v : [v]).map((f) => uet(f, "familien")).join("/");
      teile.push(uet(c, "kategorien") + ": " + wert);
    }
    if (st?.bogen) teile.push(uet("Stimmungsbogen", "ui") + " " + uet(st.bogen, "ui"));
    return teile.join(" · ");
  }
  return kurz(labels(st, BEREICH[a], leer)) || "—";
}

// ---------------------------------------------------------------- Dialog ---
const CSS_ID = "photoshoot-regie-css";
const CSS = `
.k2-regie-hg{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:10000;display:flex;
  align-items:center;justify-content:center;font:12px/1.4 -apple-system,Segoe UI,Roboto,sans-serif}
.k2-regie{background:#202020;border:1px solid #3d3d3d;border-radius:8px;color:#d7d7d7;
  width:min(620px,calc(100vw - 32px));max-height:calc(100vh - 48px);overflow:auto;padding:14px 16px;
  box-shadow:0 12px 40px rgba(0,0,0,.5);display:flex;flex-direction:column;gap:9px}
.k2-regie h3{margin:0;font-size:13px;color:#eceef1;display:flex;align-items:center;gap:8px}
.k2-regie h3 small{font-weight:400;color:#8e8e8e;font-size:11px}
.k2-regie h3 .k2-weg-klein{margin-left:auto;font-size:16px}
.k2-regie textarea{width:100%;box-sizing:border-box;background:#161616;color:#d7d7d7;border:1px solid #3d3d3d;
  border-radius:5px;padding:6px 8px;font:inherit;resize:vertical}
.k2-regie textarea:focus{outline:none;border-color:#f66744}
.k2-regie-zeile{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.k2-regie-zeile .k2-textknopf{padding:4px 9px;font-size:11px}
.k2-regie .k2-chip{font-family:inherit}
.k2-regie .k2-chip.k2-an{background:#2e201b;border-color:#f66744;color:#f3d6cb}
.k2-regie-notiz{color:#8e8e8e;font-size:11px}
.k2-regie-titel{font-size:9.5px;letter-spacing:.09em;text-transform:uppercase;color:#8a8a8a;margin-top:2px}
.k2-regie-liste{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;border:1px solid #303030;
  border-radius:6px;padding:8px;background:#191919}
.k2-regie-liste b{color:#eceef1;font-weight:600;white-space:nowrap}
.k2-regie-liste span{color:#c9c9c9;word-break:break-word}
.k2-regie-liste i{display:block;font-style:normal;font-size:10px;color:#8e8e8e}
.k2-regie-liste .k2-regie-fehlt{color:#b08a5a}
.k2-regie-fehler{color:#ec8f7a;font-size:11px;margin:0;padding-left:16px}
.k2-regie-hinweise{color:#8e8e8e;font-size:11px;margin:0;padding-left:16px}
.k2-regie-status{color:#9fc79a;font-size:11px}
.k2-regie-start{background:#f66744;border:0;color:#1a1a1a;font-weight:600;border-radius:5px;
  padding:5px 12px;cursor:pointer;font:inherit;font-weight:600}
.k2-regie-start:disabled{opacity:.4;cursor:default}
.k2-regie.k2-regie-inline{width:auto;max-height:none;overflow:visible;box-shadow:none;padding:10px 12px}
`;

function css() {
  injiziereCSS();
  if (document.getElementById(CSS_ID)) return;
  const s = document.createElement("style");
  s.id = CSS_ID;
  s.textContent = CSS;
  document.head.appendChild(s);
}

function el(tag, klasse, text) {
  const e = document.createElement(tag);
  if (klasse) e.className = klasse;
  if (text != null) e.textContent = text;
  return e;
}
function knopf(text, klick, klasse = "k2-textknopf") {
  const b = el("button", klasse, text);
  b.type = "button";
  b.onclick = klick;
  return b;
}

async function kopiere(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    // Not a secure context, or no permission: the old way.
    const ta = el("textarea");
    ta.value = text;
    ta.style.cssText = "position:fixed;opacity:0;top:0;left:0";
    document.body.appendChild(ta);
    ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e2) { ok = false; }
    ta.remove();
    return ok;
  }
}

// Remembered per page, so closing and reopening keeps the brief and the answer.
const _entwurf = { brief: "", antwort: "", modus: "brief" };

/** The dialog. opts.ergebnis ({shoot, errors, notes}) skips straight to the
 *  preview (loading a saved shoot or a file); without it, the Director. */
export async function oeffneDialog(serie, opts = {}) {
  css();
  const daten = await ladePresets();
  if (!daten?.shoot) return;
  const hg = el("div", "k2-regie-hg");
  const box = el("div", "k2-regie");
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  hg.append(box);
  const zu = () => { hg.remove(); document.removeEventListener("keydown", taste, true); };
  const taste = (e) => { if (e.key === "Escape") { e.stopPropagation(); zu(); } };
  document.addEventListener("keydown", taste, true);
  hg.addEventListener("mousedown", (e) => { if (e.target === hg) zu(); });
  document.body.append(hg);
  regieInhalt(serie, box, daten, { ...opts, zu });
}

/** The Director inline, in an element of its own (the Studio sidebar's
 *  Director tab): the dialog's content without the dialog. */
export async function regieInto(serie, ziel) {
  css();
  const daten = await ladePresets();
  if (!daten?.shoot) return;
  const box = el("div", "k2-regie k2-regie-inline");
  ziel.append(box);
  regieInhalt(serie, box, daten, {});
}

// What the dialog shows, drawn into box. opts.zu closes the dialog; inline
// there is nothing to close, so no ×, and Cancel only drops the preview.
function regieInhalt(serie, box, daten, opts) {
  const info = daten.shoot;
  const zu = opts.zu || null;
  const regie = !opts.ergebnis;
  let ergebnis = opts.ergebnis || null;
  let angewandt = null;
  let status = "";
  let beschaeftigt = false;
  const verwerfen = () => { ergebnis = null; angewandt = null; status = ""; male(); };

  async function schritt(fn) {
    if (beschaeftigt) return;
    beschaeftigt = true;
    status = uet("Wird geprüft …", "ui");
    male();
    try {
      await fn();
    } catch (e) {
      status = uetf("Fehler: {0}", "ui", e.message || e);
    }
    beschaeftigt = false;
    male();
  }

  function male() {
    box.textContent = "";
    const kopf = el("h3", null, regie ? uet("Regie", "ui") : opts.titel || "");
    if (regie) kopf.append(el("small", null, uet("ein Satz wird ein ganzes Shooting, über ein beliebiges Chat-LLM", "ui")));
    if (zu) kopf.append(knopf("×", zu, "k2-weg-klein"));
    box.append(kopf);

    if (regie) {
      box.append(el("div", "k2-regie-titel", uet("Idee in einem Satz", "ui")));
      const brief = el("textarea");
      brief.rows = 2;
      brief.placeholder = uet("z. B. ein verregneter Nachmittag in einem Pariser Café, melancholisch, schwarzweiß", "ui");
      brief.value = _entwurf.brief;
      brief.oninput = () => { _entwurf.brief = brief.value; };
      box.append(brief);

      const modi = el("div", "k2-regie-zeile");
      for (const [m, text] of [["brief", uet("Aus einer Idee", "ui")], ["photo", uet("Aus einem Referenzfoto", "ui")]]) {
        modi.append(knopf(text, () => { _entwurf.modus = m; male(); },
                          "k2-chip k2-klein" + (_entwurf.modus === m ? " k2-an" : "")));
      }
      box.append(modi);

      const url = () => "/krea2/director/llm_prompt?" +
        new URLSearchParams({ brief: _entwurf.brief, mode: _entwurf.modus });
      const aktionen = el("div", "k2-regie-zeile");
      aktionen.append(
        knopf(uet("LLM-Prompt kopieren", "ui"), () => schritt(async () => {
          const r = await fetch(url(), { cache: "no-store" });
          if (!r.ok) throw new Error("HTTP " + r.status);
          status = (await kopiere(await r.text())) ? uet("Kopiert.", "ui")
            : uet("Kopieren nicht möglich – „Prompt öffnen“ nutzen.", "ui");
        })),
        Object.assign(el("a", "k2-textknopf", uet("Prompt öffnen", "ui") + " ↗"),
                      { href: url(), target: "_blank", rel: "noopener" }),
      );
      const offline = knopf(uet("Offline-Entwurf", "ui"), () => schritt(async () => {
        ergebnis = await anfrage("/krea2/director/draft", { brief: _entwurf.brief });
        angewandt = null;
        status = "";
      }));
      offline.title = uet("Nur Wörter der Idee gegen die Listen – ohne LLM, grob", "ui");
      aktionen.append(offline);
      box.append(aktionen);
      box.append(el("div", "k2-regie-notiz", _entwurf.modus === "photo"
        ? uet("In ein Chat-LLM mit Bildeingabe einfügen, das Foto anhängen und die Antwort unten einfügen. Das Foto bleibt im Chat – zurück kommen nur Labels.", "ui")
        : uet("In ein beliebiges Chat-LLM einfügen und die Antwort unten einfügen.", "ui")));

      box.append(el("div", "k2-regie-titel", uet("Antwort des LLM", "ui")));
      const antwort = el("textarea");
      antwort.rows = 5;
      antwort.placeholder = uet("Antwort hier einfügen (JSON)", "ui");
      antwort.value = _entwurf.antwort;
      antwort.oninput = () => { _entwurf.antwort = antwort.value; };
      box.append(antwort);
      const imp = el("div", "k2-regie-zeile");
      imp.append(knopf(uet("Importieren", "ui"), () => schritt(async () => {
        ergebnis = await anfrage("/krea2/director/import", { answer: _entwurf.antwort });
        angewandt = null;
        status = "";
      })));
      box.append(imp);
    }

    if (ergebnis) vorschau();
    if (status) box.append(el("div", "k2-regie-status", status));
  }

  function vorschau() {
    const shoot = ergebnis.shoot;
    const fehler = ergebnis.errors || [];
    const hinweise = ergebnis.notes || [];
    box.append(el("div", "k2-regie-titel", uet("Das wird gesetzt", "ui")));
    const z = ziele(serie, info);
    const abschnitte = [...Object.keys(info.abschnitte), ...info.texte].filter((a) => shoot && a in shoot);
    if (abschnitte.length) {
      const liste = el("div", "k2-regie-liste");
      for (const a of abschnitte) {
        const name = el("b", null, uet(NAMEN[a] || a, "ui"));
        const text = el("span", null, zusammenfassung(a, shoot[a], daten));
        const wo = el("i");
        if (z[a]) wo.textContent = "→ " + (z[a].title || z[a].type) + " #" + z[a].id;
        else { wo.textContent = uet("kein Node – wird übersprungen", "ui"); wo.className = "k2-regie-fehlt"; }
        text.append(wo);
        liste.append(name, text);
      }
      box.append(liste);
    }
    if (fehler.length) {
      box.append(el("div", "k2-regie-titel", uetf("{0} abgelehnt", "ui", fehler.length)));
      const ul = el("ul", "k2-regie-fehler");
      for (const f of fehler) ul.append(el("li", null, f));
      box.append(ul);
    }
    if (hinweise.length) {
      box.append(el("div", "k2-regie-titel", uet("Hinweise", "ui")));
      const ul = el("ul", "k2-regie-hinweise");
      for (const h of hinweise) ul.append(el("li", null, h));
      box.append(ul);
    }
    const zeile = el("div", "k2-regie-zeile");
    if (angewandt) {
      zeile.append(el("span", "k2-regie-status", uet("Übernommen.", "ui")),
                   knopf(uet("Rückgängig", "ui"), () => {
                     angewandt.rueckgaengig();
                     angewandt = null;
                     status = uet("Rückgängig gemacht.", "ui");
                     male();
                   }),
                   knopf(uet("Schließen", "ui"), zu || verwerfen));
    } else {
      const los = knopf(fehler.length ? uet("Trotzdem übernehmen", "ui") : uet("Übernehmen", "ui"), () => {
        angewandt = wendeAn(serie, shoot, info, { mischen: regie });
        status = "";
        male();
      }, "k2-regie-start");
      los.disabled = !abschnitte.length;
      if (!abschnitte.length) zeile.append(el("span", "k2-regie-notiz", uet("Nichts zu übernehmen.", "ui")));
      zeile.append(los, knopf(uet("Abbrechen", "ui"), zu || verwerfen));
    }
    box.append(zeile);
  }

  male();
}

// ------------------------------------------------------------ Panel row ---
const _zeilenStand = new WeakMap(); // Series node -> {speichernOffen, meldung}

function herunterladen(name, shoot) {
  const blob = new Blob([JSON.stringify(shoot, null, 1)], { type: "application/json" });
  const a = el("a");
  a.href = URL.createObjectURL(blob);
  a.download = (name || "shoot").replace(/[^\w\s-]/g, "").trim().replace(/\s+/g, "_") + ".json";
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

/** The shoot row under the recipes: saved shoots as chips, save, file
 *  download and upload, and the Director. zeichne redraws the panel. */
export function shootZeile(serie, zeichne) {
  const stand = _zeilenStand.get(serie) || { speichernOffen: false, meldung: "" };
  _zeilenStand.set(serie, stand);
  if (_liste === null && !_listeLaedt) {
    _listeLaedt = true;
    queueMicrotask(() => listeAnfrage("/krea2/shoots"));
  }
  const meldung = (text) => { stand.meldung = text; zeichne(); };
  const info = async () => (await ladePresets())?.shoot;

  const zeile = el("div", "k2-schnell k2-rezepte k2-shoots");
  zeile.append(uet("Shooting", "ui") + ":");
  for (const s of _liste || []) {
    const gruppe = el("span", "k2-eigene");
    const c = knopf(s.name, async () => {
      try {
        const a = await anfrage("/krea2/shoots/load?" + new URLSearchParams({ name: s.name }));
        if (a?.error) throw new Error(a.error);
        oeffneDialog(serie, { ergebnis: a, titel: uetf("Shooting laden: {0}", "ui", s.name) });
      } catch (e) {
        meldung(uetf("Fehler: {0}", "ui", e.message || e));
      }
    }, "k2-chip k2-klein");
    c.title = (s.brief ? s.brief + "\n" : "") +
      uet("Gespeichertes Shooting laden: Person, Garderobe, Bausteine, Serie, Szene und Vorlage.", "ui");
    const weg = knopf("×", () => listeAnfrage("/krea2/shoots/delete", { name: s.name }), "k2-weg-klein");
    weg.title = uetf("Gespeichertes Shooting löschen: {0}", "ui", s.name);
    weg.setAttribute("aria-label", weg.title);
    gruppe.append(c, weg);
    zeile.append(gruppe);
  }

  if (stand.speichernOffen) {
    const feld = el("input", "k2-serien-name");
    feld.placeholder = uet("Name des Shootings", "ui");
    const sichern = async () => {
      const name = feld.value.trim();
      if (!name) { feld.focus(); return; }
      stand.speichernOffen = false;
      const i = await info();
      const a = await listeAnfrage("/krea2/shoots/save", { name, shoot: sammle(serie, i) });
      meldung(a?.error ? uetf("Fehler: {0}", "ui", a.error) : uetf("Gespeichert: {0}", "ui", a?.name || name));
    };
    feld.onkeydown = (e) => {
      if (e.key === "Enter") sichern();
      else if (e.key === "Escape") { stand.speichernOffen = false; zeichne(); }
    };
    zeile.append(feld, knopf(uet("Speichern", "ui"), sichern),
                 knopf(uet("Abbrechen", "ui"), () => { stand.speichernOffen = false; zeichne(); }));
    queueMicrotask(() => feld.focus());
  } else {
    const plus = knopf("+ " + uet("Speichern", "ui"), () => { stand.speichernOffen = true; stand.meldung = ""; zeichne(); },
                       "k2-chip k2-klein k2-plus");
    plus.title = uet("Das ganze Shooting unter einem Namen speichern", "ui");
    zeile.append(plus);
  }

  const runter = knopf("⇩ " + uet("Datei", "ui"), async () => {
    const i = await info();
    // Through the check, so the file carries the prompt copies of custom
    // entries exactly as a saved shoot does.
    const a = await anfrage("/krea2/shoots/check", { shoot: sammle(serie, i) }).catch(() => null);
    herunterladen("photoshoot-shoot", a?.shoot || sammle(serie, i));
  }, "k2-chip k2-klein");
  runter.title = uet("Als Datei herunterladen (zum Teilen)", "ui");

  const hoch = knopf("⇧ " + uet("Datei", "ui"), () => {
    const inp = el("input");
    inp.type = "file";
    inp.accept = ".json,application/json";
    inp.onchange = async () => {
      const datei = inp.files?.[0];
      if (!datei) return;
      let roh;
      try { roh = JSON.parse(await datei.text()); } catch (e) {
        meldung(uet("Datei ist kein gültiges JSON", "ui"));
        return;
      }
      try {
        const a = await anfrage("/krea2/shoots/check", { shoot: roh });
        oeffneDialog(serie, { ergebnis: a, titel: uetf("Shooting laden: {0}", "ui", datei.name) });
      } catch (e) {
        meldung(uetf("Fehler: {0}", "ui", e.message || e));
      }
    };
    inp.click();
  }, "k2-chip k2-klein");
  hoch.title = uet("Shooting-Datei öffnen", "ui");

  const regie = knopf(uet("Regie", "ui") + " …", () => oeffneDialog(serie), "k2-chip k2-klein k2-plus");
  regie.title = uet("Regie: ein Satz wird ein ganzes Shooting, über ein beliebiges Chat-LLM", "ui");
  zeile.append(runter, hoch, regie);
  if (stand.meldung) zeile.append(el("span", "k2-eigen", stand.meldung));
  return zeile;
}
