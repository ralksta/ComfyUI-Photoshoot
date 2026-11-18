// Interface of the photoshoot node.
//
// What sets it apart from the other panels: it holds a button that works the
// queue itself. One click queues N runs, the counter climbs as it goes, and the
// node hands out a different photo per run.

import {
  alsBearbeiten,
  alsEinSchritt,
  ansicht,
  applyAdaptiveCanvasOnly,
  beimEntfernen,
  erzeugeUndVerbinde,
  injiziereCSS,
  installCanvasZoomPassthrough,
  istKompakt,
  ladePresets,
  leseState,
  locationVonSerie,
  markenleiste,
  oeffneStudio,
  ortSaetze,
  outfitBild,
  outfitBildUrl,
  outfitHauptfarbe,
  passeKompaktAn,
  promptJoinNode,
  PROP_ANSICHT,
  rendereUndMerke,
  verbindeNodes,
  wardrobeVonPerson,
  registriereStateInjektion,
  schreibeState,
  kopiere,
  presetFehler,
  registriereBauer,
  setzeAnsicht,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.9.0";

import {
  VORGABE,
  bogenVon,
  format,
  lichtFuer,
  masse,
  masseFuer,
  outfitAuswahl,
  outfitFuer,
  plane,
  reihenfolgeVon,
  setFuer,
} from "./shooting_plan.mjs?v=2.9.0";
import { shootZeile } from "./regie.mjs?v=2.9.0";
import { lightboxDa, meldeAb, meldeSerie, oeffneLightbox, serieGeaendert } from "./lightbox.mjs?v=2.9.0";
// The Studio sidebar: no loader of its own, it comes with the Series.
import "./studio.mjs?v=2.9.0";

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const CLASS_TYPE = "Krea2Photoshooting";
const HIDDEN = "ShootingState";
const PROP = "shootingState";

// The refine output (appended in 2.7.0). Only when it is wired does a draft
// switch anything off: in a workflow from before, or with the output left
// open, Draft and Finish favourites are greyed out and the runs are finals.
const REFINE = "refine";
function refineVerdrahtet(node) {
  return !!node.outputs?.find((o) => o.name === REFINE)?.links?.length;
}

// What one run gets, on top of the saved state. Finish favourites queues the
// starred photos with draft off and their chosen take while the panel stays
// on draft - so the override lives on the node for the length of the queue
// call (node._k2Lauf) and never touches the saved state, the undo history or
// what the panel shows. A draft with nothing to switch off is no draft.
function _parseProp(props, name) {
  const raw = props?.[name];
  if (!raw) return null;
  if (typeof raw === "object") return raw;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch (e) { return null; }
}

function fuerDenLauf(node, roh) {
  const extra = node._k2Lauf;
  const props = node.properties || {};
  const hatPersonKabel = !!node.inputs?.find((i) => i.name === "person_data")?.link;
  const hatOrtKabel = !!node.inputs?.find((i) => i.name === "ort_data")?.link;
  const einbetten = {};
  if (!hatPersonKabel) {
    const p = _parseProp(props, "personState");
    const w = _parseProp(props, "wardrobeState");
    if (p) einbetten._person = p;
    if (w) einbetten._wardrobe = w;
  }
  if (!hatOrtKabel) {
    const loc = _parseProp(props, "locationState");
    if (loc) einbetten._location = loc;
  }
  const l = _parseProp(props, "lightingState");
  if (l) einbetten._lighting = l;
  const s = _parseProp(props, "styleState");
  if (s) einbetten._style = s;
  if (typeof props.sceneText === "string" && props.sceneText.trim()) einbetten._scene = props.sceneText;
  if (typeof props.templateText === "string" && props.templateText.trim()) einbetten._template = props.templateText;
  const hatEinbetten = Object.keys(einbetten).length > 0;
  let st;
  try { st = JSON.parse(roh); } catch (e) { return roh; }
  if (!extra && !hatEinbetten && !(st.entwurf && !refineVerdrahtet(node))) return roh;
  if (!refineVerdrahtet(node)) st.entwurf = false;
  return JSON.stringify({ ...st, ...einbetten, ...(extra || {}) });
}

// Time estimate on the button.
//
// This used to be a fixed number (46 s), read off the first log line of a
// session - but that one included loading the model. In the steady state it is
// around 13 s, so the estimate was almost three times too high. And it could
// never grow along when the size step goes up.
//
// Now taken from the last successful runs. Median rather than mean, so that a
// single outlier - the first run after startup, with the model load - does not
// skew the estimate.
const SEK_PRO_BILD_VORGABE = 15;
let _sekProBild = SEK_PRO_BILD_VORGABE;

async function messeSekundenProBild() {
  try {
    const r = await fetch("/history?max_items=8", { cache: "no-store" });
    if (!r.ok) return _sekProBild;
    const daten = await r.json();
    const dauern = [];
    for (const eintrag of Object.values(daten)) {
      const m = eintrag?.status?.messages;
      if (!m || eintrag.status.status_str !== "success") continue;
      const start = m.find((x) => x[0] === "execution_start")?.[1]?.timestamp;
      const ende = m.find((x) => x[0] === "execution_success")?.[1]?.timestamp;
      if (start && ende && ende > start) dauern.push((ende - start) / 1000);
    }
    if (!dauern.length) return _sekProBild;
    dauern.sort((a, b) => a - b);
    _sekProBild = dauern[Math.floor(dauern.length / 2)];
  } catch (e) {
    // With no history the default stands - better a rough estimate than a
    // broken interface.
  }
  return _sekProBild;
}

// --------------------------------------------------------------- Build ---
// ziel: an element to draw into instead of the node (the Studio sidebar's
// Shoot tab) - the same panel on the same state, without the contact sheet
// (the Lightbox is the big one), the node's widget and its zoom handling;
// returns { root, weg } then.
// ort: the Location presets (/krea2/presets "location"), for the sets.
function baue(node, d, person, ziel = null, ort = null) {
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root k2-serie" + (ziel ? " k2-studio-panel" : "");
  if (!ziel) installCanvasZoomPassthrough(root);
  // What goes when this view goes: with the node on the canvas, with the
  // sidebar's column there.
  const aufraeumen = [];

  const vorgabe = { ...VORGABE, ...(d.vorgabe || {}) };
  const lies = () => leseState(node, PROP, vorgabe);
  const schreib = (s) => {
    schreibeState(node, PROP, s);
    zeichne();
    // Other settings, other photos: the contact sheet looks again.
    ladeSpaeter();
  };

  // Which axis is currently unfolded. Deliberately kept here and not in the
  // state: this is a matter of view, not a setting - and the state travels to
  // Python on execution, where it would have no business being. Only ever one
  // axis open; two open blocks were exactly the crowding this is meant to
  // remove.
  let offen = null;

  // ------------------------------------------ Dimensions from outside ---
  // When values arrive at width_in/height_in, they decide the resolution - but
  // only on execution. Up to this point the preview still computed with its own
  // size and its own ratio, and so showed dimensions that never came out. So
  // read the upstream node directly instead.
  const holeLink = (id) =>
    id == null ? null : (app.graph?.links?.get?.(id) ?? app.graph?.links?.[id]);

  function ausgangswert(eingang) {
    const link = holeLink(node.inputs?.find((i) => i.name === eingang)?.link);
    const quelle = link && app.graph?.getNodeById?.(link.origin_id);
    if (!quelle) return null;

    // Resolution Pixaroma keeps its state in properties, as our nodes do -
    // the same construction, so the same way of reading it.
    const roh = quelle.properties?.resolutionState;
    if (roh) {
      try {
        const s = typeof roh === "string" ? JSON.parse(roh) : roh;
        const v = Number(link.origin_slot === 0 ? s.w : s.h);
        if (Number.isFinite(v) && v > 0) return v;
      } catch (e) {
        // Unreadable - fall through to the generic attempt below.
      }
    }
    // Otherwise a widget named like the output. Covers primitives and simple
    // INT nodes.
    const name = quelle.outputs?.[link.origin_slot]?.name;
    const v = Number(quelle.widgets?.find((x) => x.name === name)?.value);
    return Number.isFinite(v) && v > 0 ? v : null;
  }

  const externeMasse = () => {
    const w = ausgangswert("width_in"), h = ausgangswert("height_in");
    return w && h ? [w, h] : null;
  };

  // ------------------------------------------------------- Building parts ---
  // The photo counter and its "control after generate" are ComfyUI widgets the
  // queue needs - they climb with every run. On the node they were a third
  // number next to "photos" and "from", so they are hidden and the panel says
  // "next: photo N" instead.
  const zaehlerWidget = () => node.widgets?.find((w) => w.name === "foto" || w.name === "seed");
  const steuerWidget = () => node.widgets?.find(
    (w) => w.name === "control_after_generate" || w.name === "control_after_generated");
  // The Vue front end reads "hidden" from the widget's reactive _state, the
  // canvas from options; both are set, and again on every redraw, because
  // loading a workflow can rebuild the state.
  const versteckeZaehler = () => {
    for (const w of [zaehlerWidget(), steuerWidget()]) {
      if (!w) continue;
      // A new object, assigned through the reactive state - setting the flag
      // on the existing one changes it without Vue noticing (options and
      // _state.options are often the same object). The marker keeps this to
      // once per rebuild.
      if (w._state && !w._state.options?.k2Versteckt) {
        w._state.options = { ...(w._state.options || {}), hidden: true, k2Versteckt: true };
      }
      if (w.options) w.options.hidden = true;
    }
  };

  // Saved series (ComfyUI/user/krea2_series, routes in api.py) and whether
  // the name field for saving is open.
  let eigene = [];
  let speichernOffen = false;
  const SERIEN_SCHLUESSEL = ["anzahl", "start", "aktiv", "pools", "kameras", "fokusse", "perspektiven",
                             "festesFormat", "abdeckung", "reihenfolge", "bogen",
                             "takesJeFoto", "groesse", "serienSeed", "blick",
                             "kameraOptik", "requisiten", "requisitText", "setFolge", "lichtFolge", "lichtPool"];
  // ------------------------------------------------------- Wardrobe ---
  // The outfits of the Wardrobe node on the person that feeds this series -
  // the same list outfits_aus_state() gives Python, read from the node's state
  // instead of the executed output, so the contact sheet knows them before a
  // run.
  function personNode() {
    const link = holeLink(node.inputs?.find((i) => i.name === "person_data")?.link);
    const person = link && app.graph?.getNodeById?.(link.origin_id);
    if (person?.comfyClass === "Krea2PersonBuilder") return person;
    if (node.properties?.personState || node.properties?.wardrobeState || node.properties?.studioModus) return node;
    return null;
  }
  function wardrobeNode() {
    const p = personNode();
    if (p && p !== node) return wardrobeVonPerson(p);
    if (node.properties?.wardrobeState || node.properties?.studioModus) return node;
    return null;
  }
  function garderobe() {
    const q = wardrobeNode();
    if (!q) return [];
    let st = {};
    try { st = JSON.parse(q.properties?.wardrobeState || "{}"); } catch (e) { st = {}; }
    return (Array.isArray(st.outfits) ? st.outfits : []).map((o, i) => ({
      ...o, felder: o.felder || {}, name: (o.name || "").trim() || uetf("Outfit {0}", "ui", i + 1), node: q }));
  }

  // ----------------------------------------------------------- Sets ---
  // The sets of the Location node on ort_data, read from its state as the
  // wardrobe is (ortSaetze() in shared.mjs), so the contact sheet knows them
  // before a run - count, names and indoors/outdoors, as Python gets them
  // from ort_data.
  const saetzeJetzt = () => (ort ? ortSaetze(ort, locationVonSerie(node)) : []);
  // A set's colour on the contact sheet: a stripe on top of its frames.
  const SET_FARBEN = ["#6f9fc4", "#c49a6f", "#8fb46f", "#b47fa8", "#c4c06f", "#6fc4b0"];
  const setFarbe = (k) => SET_FARBEN[k % SET_FARBEN.length];

  // An outfit as a short list: garment and colour swatch per row. The colours
  // are the Person Builder's (FARBWERTE), so a swatch matches its colour button.
  const OUTFIT_ZEILEN = [["top", "topColor"], ["bottom", "bottomColor"], ["hosiery", "hosieryColor"],
                         ["shoes", "shoesColor"], ["jewellery"], ["eyewear"], ["headwear"], ["prop"]];
  const leerLabel = (l) => !l || l === person?.leer;
  function farbeVon(o, farbCat) {
    const l = o.felder[farbCat];
    return leerLabel(l) ? null : person?.farben?.[farbCat]?.[l] || null;
  }
  // The colour of the stripe under a frame: the top's, else the bottom's.
  const hauptfarbe = (o) => outfitHauptfarbe(person, o);
  function outfitKarte(o, nr, index, outfitsLen, state, aktiv) {
    const karte = document.createElement("div");
    karte.className = "k2-okarte" + (aktiv ? "" : " k2-aus");
    const kopf = document.createElement("div");
    kopf.className = "k2-okarte-kopf-zeile";
    kopf.style.borderColor = hauptfarbe(o);
    const schalter = document.createElement("button");
    schalter.type = "button";
    schalter.className = "k2-okarte-schalter";
    schalter.textContent = `${nr}  ${o.name}`;
    schalter.title = uet("Klicken: Outfit in dieser Serie an-/abwählen", "ui");
    schalter.onclick = () => {
      const alle = [...Array(outfitsLen).keys()];
      const bisher = outfitAuswahl(state, outfitsLen);
      const drin = bisher.includes(index);
      const neu = drin ? bisher.filter((x) => x !== index) : [...bisher, index].sort((a, b) => a - b);
      if (!neu.length) {
        karte.animate?.([{ transform: "translateX(-2px)" }, { transform: "translateX(2px)" },
                         { transform: "none" }], 180);
        return;
      }
      schreib({ ...state, outfitAuswahl: neu.length === alle.length ? null : neu });
    };
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "k2-okarte-edit";
    edit.textContent = "✎";
    edit.title = uet("In Wardrobe bearbeiten", "ui");
    edit.onclick = (ev) => {
      ev.stopPropagation();
      try {
        const st = JSON.parse(o.node.properties?.wardrobeState || "{}");
        o.node.properties.wardrobeState = JSON.stringify({ ...st, aktiv: index });
        o.node._k2Zeichne?.();
      } catch (e) { /* ignore */ }
      if (!oeffneStudio(o.node, "wardrobe")) {
        app.canvas?.selectNode?.(o.node);
        app.canvas?.centerOnNode?.(o.node);
      }
    };
    kopf.append(schalter, edit);
    karte.append(kopf);
    // The rendered preview, when there is one; dimmed once the outfit changed.
    const vb = outfitBild(o.node, o);
    if (vb) {
      const a = document.createElement("a");
      a.className = "k2-okarte-bild" + (vb.aktuell ? "" : " k2-alt");
      a.href = outfitBildUrl(vb.datei, false);
      a.target = "_blank";
      a.rel = "noopener";
      a.style.backgroundImage = `url("${outfitBildUrl(vb.datei, true)}")`;
      a.title = vb.aktuell ? uet("Bild öffnen", "ui") : uet("Veraltet — das Outfit wurde seitdem geändert", "ui");
      karte.append(a);
    }
    let zeilen = 0;
    for (const [cat, farbCat] of OUTFIT_ZEILEN) {
      const l = o.felder[cat];
      if (leerLabel(l)) continue;
      const z = document.createElement("div");
      z.className = "k2-okarte-zeile";
      const fleck = document.createElement("b");
      const hex = farbCat && farbeVon(o, farbCat);
      fleck.className = "k2-mini" + (hex ? "" : " k2-ohne");
      if (hex) fleck.style.background = hex;
      z.append(fleck, uet(l, "person/" + cat));
      karte.append(z);
      zeilen++;
    }
    const propFrei = (o.texte?.propText || "").trim();
    if (propFrei) {
      const z = document.createElement("div");
      z.className = "k2-okarte-zeile";
      const fleck = document.createElement("b");
      fleck.className = "k2-mini k2-ohne";
      z.append(fleck, "“" + propFrei + "”");
      karte.append(z);
      zeilen++;
    }
    if (!zeilen) {
      const z = document.createElement("div");
      z.className = "k2-okarte-zeile k2-leer";
      z.textContent = uet("nichts gesetzt", "ui");
      karte.append(z);
    }
    return karte;
  }

  // Render every outfit's preview, one after the other, in the Wardrobe
  // node's chosen kind (mannequin or flat lay).
  let vorschauStatus = null;   // null, or text while rendering / after an error
  async function rendereOutfits() {
    const liste = garderobe();
    const q = wardrobeNode();
    if (!liste.length || !q || vorschauStatus) return;
    let art = "puppe";
    try { art = JSON.parse(q.properties?.wardrobeState || "{}").vorschauArt === "flach" ? "flach" : "puppe"; } catch (e) { /* default */ }
    for (const [i, o] of liste.entries()) {
      vorschauStatus = uetf("rendert {0} von {1} …", "ui", i + 1, liste.length);
      zeichne();
      if (!(await rendereUndMerke(q, o, art, (m) => { vorschauStatus = m; }))) { zeichne(); return; }
      zeichne();
    }
    vorschauStatus = null;
    zeichne();
  }

  async function serienAnfrage(pfad, daten) {
    try {
      const r = await fetch(pfad, daten ? {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(daten),
      } : { cache: "no-store" });
      if (r.ok) eigene = await r.json();
    } catch (e) {
      // Without the route the row simply shows the built-in recipes.
    }
    zeichne();
  }
  queueMicrotask(() => serienAnfrage("/krea2/serien"));

  // Selected frame in the contact sheet and the frames marked for a re-shoot.
  // A view, not a setting - neither travels to Python.
  let gewaehlt = null;
  const markiert = new Set();
  // Page of the contact sheet.
  const PRO_SEITE = 24;
  let seite = 0;
  // Photos von … von + gezeigt - 1 of the page the selected photo is on.
  // The page follows the selected photo, so a frame chosen elsewhere is
  // never out of sight.
  function seiteVon(start, anzahl, proSeite) {
    const seiten = Math.max(1, Math.ceil(anzahl / proSeite));
    if (gewaehlt != null && gewaehlt >= start && gewaehlt < start + anzahl) {
      seite = Math.floor((gewaehlt - start) / proSeite);
    }
    seite = Math.min(Math.max(0, seite), seiten - 1);
    const von = start + seite * proSeite;
    return { seiten, von, gezeigt: Math.min(proSeite, start + anzahl - von) };
  }
  // Frames per row of the contact sheet: 52 px each and 5 between. The
  // width is the one the frames had last time (measured after drawing, and
  // drawn again when that gives another count); before that, the panel's
  // width less its padding and the sheet's scrollbar. A resize of the node
  // measures anew.
  let proZeile = 0;
  let rasterBreite = 0;
  let rootBreite = 0;
  const zeilenBreite = () => {
    const breite = rasterBreite || (root.clientWidth || (node.size?.[0] || 360) - 8) - 12 - 6;
    return Math.max(1, Math.floor((breite + 5) / 57));
  };
  if (!ziel && typeof ResizeObserver === "function") {
    const beobachter = new ResizeObserver(() => {
      if (!proZeile || !root.clientWidth || root.clientWidth === rootBreite) return;
      rootBreite = root.clientWidth;
      rasterBreite = 0;
      zeichne();
    });
    beobachter.observe(root);
    aufraeumen.push(() => beobachter.disconnect());
  }
  // The prompt just copied from the detail box, for the button's answer.
  let kopiert = null;
  // The last click on a frame: a second one on the same frame opens the Lightbox.
  let letzterKlick = null;

  // Chips in the axes. "erreichbar" (optional) marks entries that cannot
  // occur at all with the remaining settings - they stay clickable but look
  // dead, and say why in the tooltip. The last chip cannot be deselected; it
  // shakes briefly instead of silently doing nothing.
  function chipreihe(alle, gewaehltRoh, sichern, erreichbar, bereich) {
    const chips = document.createElement("div");
    chips.className = "k2-chips";
    const gew = gewaehltRoh?.length ? gewaehltRoh : alle.map((x) => x.label);
    for (const e of alle) {
      const c = document.createElement("button");
      c.type = "button";
      const an = gew.includes(e.label);
      const tot = erreichbar && !erreichbar.has(e.label);
      c.className = "k2-chip" + (an ? " k2-an" : "") + (tot ? " k2-tot" : "");
      c.textContent = bereich ? uet(e.label, bereich) : e.label;
      c.setAttribute("aria-pressed", String(an));
      c.title = tot
        ? e.wert + uet(" — passt zu keiner der gewählten Kameraeinstellungen", "ui")
        : e.wert;
      c.onclick = () => {
        const neu = an ? gew.filter((x) => x !== e.label) : [...gew, e.label];
        if (!neu.length) {
          c.animate?.([{ transform: "translateX(-2px)" }, { transform: "translateX(2px)" },
                       { transform: "none" }], 180);
          return;
        }
        sichern(neu.length === alle.length ? null : neu);
      };
      chips.append(c);
    }
    return chips;
  }

  // Families as chips, one of them active ("all" included).
  function familienChips(state, quelle) {
    const g = d.gruppen[quelle];
    const aktiv = state.pools?.[g.feld] ?? d.alle;
    const chips = document.createElement("div");
    chips.className = "k2-chips";
    for (const f of [d.alle, ...Object.keys(g.familien)]) {
      const c = document.createElement("button");
      c.type = "button";
      const drin = Array.isArray(aktiv) ? aktiv.includes(f) : aktiv === f;
      c.className = "k2-chip" + (drin ? " k2-an" : "");
      c.textContent = f === d.alle ? uet("alle", "ui") : uet(f, "familien");
      c.onclick = () => schreib({ ...state, pools: { ...state.pools, [g.feld]: f } });
      chips.append(c);
    }
    return chips;
  }

  function auswahl(optionen, wert, sichern, beschriftung) {
    const zeile = document.createElement("div");
    zeile.className = "k2-feld";
    if (beschriftung) {
      const n = document.createElement("div");
      n.className = "k2-name";
      n.textContent = beschriftung;
      zeile.append(n);
    }
    const sel = document.createElement("select");
    for (const o of optionen) {
      const opt = document.createElement("option");
      opt.value = o.wert;
      opt.textContent = o.text;
      sel.append(opt);
    }
    sel.value = wert;
    sel.onchange = () => sichern(sel.value);
    zeile.append(sel);
    return zeile;
  }

  const notiz = (text) => {
    const n = document.createElement("div");
    n.className = "k2-anotiz";
    n.textContent = text;
    return n;
  };

  // One axis row: a switch, the name, what it currently does, the fold arrow.
  function achse({ schluessel, name, stand, hinweis, inhalt, zusatz, an: anVorgabe }, state) {
    const an = anVorgabe ?? !!state.aktiv?.[schluessel];
    const box = document.createElement("div");
    box.className = "k2-achse-box" + (offen === schluessel && inhalt ? " k2-offen" : "");
    const zeile = document.createElement("div");
    zeile.className = "k2-achse" + (an ? " k2-hell" : "") + (inhalt ? "" : " k2-zu");
    zeile.title = hinweis;

    const schalter = document.createElement("button");
    schalter.type = "button";
    schalter.className = "k2-schalter";
    schalter.setAttribute("role", "switch");
    schalter.setAttribute("aria-checked", String(an));
    schalter.setAttribute("aria-label", name);
    schalter.onclick = (e) => {
      e.stopPropagation();
      schreib({ ...state, aktiv: { ...state.aktiv, [schluessel]: !an } });
    };

    const n = document.createElement("div");
    n.className = "k2-achse-name";
    n.textContent = name;
    const w = document.createElement("div");
    w.className = "k2-achse-wert";
    w.textContent = zusatz ? `${stand} · ${zusatz}` : stand;
    const p = document.createElement("div");
    p.className = "k2-pfeil";
    p.textContent = inhalt ? "▶" : "";

    zeile.append(schalter, n, w, p);
    if (inhalt) {
      zeile.tabIndex = 0;
      zeile.setAttribute("role", "button");
      zeile.setAttribute("aria-expanded", String(offen === schluessel));
      const auf = () => { offen = offen === schluessel ? null : schluessel; zeichne(); };
      zeile.onclick = auf;
      zeile.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); auf(); }
      };
    }
    box.append(zeile);
    if (offen === schluessel && inhalt) {
      const auf = document.createElement("div");
      auf.className = "k2-auf";
      auf.append(...[].concat(inhalt()));
      box.append(auf);
    }
    return box;
  }

  // Queueing in progress ({n, gesamt}) and what went wrong last time. Not a
  // setting, but not one view's either: it hangs on the node, so the canvas
  // panel and the sidebar see the same run and neither can start a second.
  // While it runs the button is disabled, so a double click cannot queue the
  // series twice.
  const einreihung = (node._k2Einreihen ||= {
    einreihen: null, einreiheFehler: null, rundeFehler: null,
    warteschlange: [], aktivFoto: null, abbruch: false,
  });
  einreihung.warteschlange ||= [];

  // One photo into the queue. app.queuePrompt does not throw on a refused
  // prompt - it shows ComfyUI's own error dialog and returns false.
  async function reiheEin() {
    let ok = false;
    try {
      ok = await app.queuePrompt(0, 1);
    } catch (e) {
      console.error("[Photoshoot] Einreihen fehlgeschlagen:", e);
    }
    return ok !== false;
  }

  function merkeWarteschlange(nr) {
    einreihung.warteschlange.push(nr);
    if (einreihung.aktivFoto == null) einreihung.aktivFoto = nr;
  }

  async function stoppeLauf() {
    einreihung.abbruch = true;
    einreihung.warteschlange = [];
    einreihung.aktivFoto = null;
    zeichne();
    try {
      await fetch("/queue", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clear: true }),
      });
    } catch (e) { /* ignore */ }
    try { await fetch("/interrupt", { method: "POST" }); } catch (e) { /* ignore */ }
    try { await api.interrupt?.(); } catch (e) { /* ignore */ }
  }

  async function starte(anzahl, start, jeFoto = 1) {
    if (einreihung.einreihen) return;
    const zaehler = zaehlerWidget();
    const ctrl = steuerWidget();
    if (!zaehler) return;
    einreihung.einreihen = { n: 0, gesamt: anzahl * jeFoto };
    einreihung.einreiheFehler = null;
    einreihung.abbruch = false;
    zeichne();
    // Photo by photo rather than app.queuePrompt(0, N), so the button can
    // count. One undo step for the whole run instead of one per photo.
    await alsEinSchritt(async () => {
      // Set the counter to the start number, so that the series begins there
      // and not where the last run left off. With several takes per photo each
      // number is queued once per take, the take written into the state before
      // it goes into the prompt - the take moves the seed (bildseed in
      // shooting.py) - and the counter stands on "fixed" meanwhile.
      if (ctrl) ctrl.value = jeFoto > 1 ? "fixed" : "increment";
      const takes = { ...(lies().takes || {}) };
      let nr = Math.max(1, start || 1);
      zaehler.value = nr;
      try {
        for (; nr < start + anzahl; nr++) {
          if (einreihung.abbruch) break;
          for (let t = 0; t < jeFoto; t++) {
            if (einreihung.abbruch) break;
            if (jeFoto > 1) {
              takes[String(nr)] = t;
              schreibeState(node, PROP, { ...lies(), takes: { ...takes } });
              zaehler.value = nr;
            }
            if (!(await reiheEin())) {
              einreihung.einreiheFehler = uetf("⚠ Foto {0} wurde nicht eingereiht — ComfyUI hat es abgelehnt, siehe dessen Fehlermeldung", "ui", nr);
              return;
            }
            merkeWarteschlange(nr);
            einreihung.einreihen.n++;
            zeichne();
          }
        }
      } finally {
        // "increment" advanced the counter by itself; with takes it stood
        // still and goes behind the series (or onto the refused photo).
        if (jeFoto > 1) zaehler.value = einreihung.einreiheFehler ? nr : start + anzahl;
        if (ctrl) ctrl.value = "increment";
      }
    });
    einreihung.einreihen = null;
    zeichne();
  }

  // Re-shoot single photos: the same plan with a new take, so a new seed.
  // An unshot photo renders its first take (0) rather than skipping to take 2.
  async function nachfotografieren(nummern) {
    const zaehler = zaehlerWidget(), ctrl = steuerWidget();
    if (!zaehler || !nummern.length || einreihung.einreihen) return;
    const vorher = { wert: zaehler.value, modus: ctrl?.value };
    einreihung.einreihen = { n: 0, gesamt: nummern.length };
    einreihung.einreiheFehler = null;
    einreihung.abbruch = false;
    zeichne();
    await alsEinSchritt(async () => {
      const state = lies();
      const takes = { ...(state.takes || {}) };
      let geaendert = false;
      for (const nr of nummern) {
        if (bildFuer(state, nr)) {
          takes[String(nr)] = (takes[String(nr)] || 0) + 1;
          geaendert = true;
        }
      }
      // Written before queueing: the state goes into the prompt when it is built.
      if (geaendert) schreibeState(node, PROP, { ...state, takes });
      if (ctrl) ctrl.value = "fixed";
      try {
        for (const nr of nummern) {
          if (einreihung.abbruch) break;
          zaehler.value = nr;
          if (!(await reiheEin())) {
            einreihung.einreiheFehler = uetf("⚠ Foto {0} wurde nicht eingereiht — ComfyUI hat es abgelehnt, siehe dessen Fehlermeldung", "ui", nr);
            break;
          }
          merkeWarteschlange(nr);
          einreihung.einreihen.n++;
          zeichne();
        }
      } finally {
        zaehler.value = vorher.wert;
        if (ctrl && vorher.modus) ctrl.value = vorher.modus;
      }
    });
    einreihung.einreihen = null;
    // Only the photos just queued: the Lightbox re-shoots one while others
    // may still be marked here.
    for (const nr of nummern) markiert.delete(nr);
    zeichne();
  }

  // Finish favourites: the starred photos again, each at the take the contact
  // sheet shows for it (the chosen one, else the newest), with draft off - the
  // same seed and plan as the draft, now with the second pass. The take and
  // the draft flag go in per run (fuerDenLauf), the counter is put back like
  // after a re-shoot.
  const fertigerTake = (state, nr) =>
    bildFuer(state, nr)?.take ?? Number(state.wahl?.[String(nr)] ?? state.takes?.[String(nr)] ?? 0);
  // Favourites still to finish: those whose picture is a draft, or unknown
  // (history gone) - a finished one would only come out of the cache again.
  const zuFertigen = (state) => [...new Set((state.favoriten || []).map(Number))]
    .filter((nr) => nr >= 1 && bildFuer(state, nr)?.entwurf !== false);
  // Queued like a re-shoot: behind the same guard, counting on the button, as
  // one undo step, and it stops at the first photo ComfyUI refuses. The
  // Lightbox finishes a single draft the same way (nummern = [nr]).
  async function fertigstellen(nummern = null) {
    const zaehler = zaehlerWidget(), ctrl = steuerWidget();
    if (!zaehler || einreihung.einreihen || !refineVerdrahtet(node)) return;
    const state = lies();
    nummern = nummern || zuFertigen(state);
    if (!nummern.length) return;
    const vorher = { wert: zaehler.value, modus: ctrl?.value };
    einreihung.einreihen = { n: 0, gesamt: nummern.length };
    einreihung.einreiheFehler = null;
    einreihung.abbruch = false;
    zeichne();
    await alsEinSchritt(async () => {
      if (ctrl) ctrl.value = "fixed";
      try {
        for (const nr of nummern) {
          if (einreihung.abbruch) break;
          node._k2Lauf = { entwurf: false,
                           takes: { ...(state.takes || {}), [String(nr)]: fertigerTake(state, nr) } };
          zaehler.value = nr;
          if (!(await reiheEin())) {
            einreihung.einreiheFehler = uetf("⚠ Foto {0} wurde nicht eingereiht — ComfyUI hat es abgelehnt, siehe dessen Fehlermeldung", "ui", nr);
            break;
          }
          merkeWarteschlange(nr);
          einreihung.einreihen.n++;
          zeichne();
        }
      } finally {
        node._k2Lauf = null;
        zaehler.value = vorher.wert;
        if (ctrl && vorher.modus) ctrl.value = vorher.modus;
      }
    });
    einreihung.einreihen = null;
    zeichne();
  }

  // ------------------------------------------------ Selects → next round ---
  // The favourites (and rejects) of this round become the next round's pools.
  // Computed in Python only (naechste_runde() in shooting.py, behind
  // /krea2/serien/naechste_runde); the panel sends its state and applies the
  // answer. The earlier rounds travel in state.runden, so "back" is a pop.
  // Photo numbers of this series among a list - the ones naechste_runde()
  // counts (_nummern_im_bogen() there); here only for the labels.
  const imBogen = (s, liste) => {
    const ab = Math.max(1, parseInt(s.start, 10) || 1), n = Math.max(1, parseInt(s.anzahl, 10) || 1);
    return new Set((liste || []).map(Number).filter((nr) => nr >= ab && nr < ab + n)).size;
  };
  async function naechsteRunde() {
    // Not while photos are being queued: they would go out with the next
    // round's state.
    if (einreihung.einreihen) return;
    einreihung.rundeFehler = null;
    try {
      const outfits = lies().aktiv?.outfit === false ? 0 : garderobe().length;
      const saetze = saetzeJetzt().length;
      const r = await fetch("/krea2/serien/naechste_runde", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: lies(), outfits, saetze }),
      });
      const antwort = await r.json();
      if (!r.ok || !antwort?.state) throw new Error(antwort?.error || String(r.status));
      markiert.clear();
      gewaehlt = null;
      schreib(antwort.state);
    } catch (e) {
      console.error("[Photoshoot] Nächste Runde fehlgeschlagen:", e);
      einreihung.rundeFehler = uet("Nächste Runde fehlgeschlagen", "ui");
      zeichne();
    }
  }
  function vorigeRunde(state) {
    const runden = state.runden || [];
    if (!runden.length || einreihung.einreihen) return;
    const auswahl = imBogen(state, state.favoriten) + imBogen(state, state.verworfen);
    if (auswahl && !window.confirm(uet("Zurück zur vorigen Runde? Favoriten und Verworfene dieser Runde gehen verloren.", "ui"))) return;
    markiert.clear();
    gewaehlt = null;
    schreib({ ...runden[runden.length - 1], runden: runden.slice(0, -1) });
  }
  function verwerfenKnopf(nr, verworfen) {
    const k = document.createElement("button");
    k.type = "button";
    k.className = "k2-textknopf" + (verworfen.has(nr) ? " k2-an" : "");
    k.textContent = "✕ " + uet("Verwerfen", "ui");
    k.title = uet("Für die nächste Runde: was nur verworfene Fotos zeigen, fällt weg.", "ui");
    k.onclick = () => schalteVerworfen(nr);
    return k;
  }
  function rundenLeiste(state) {
    const leiste = document.createElement("div");
    leiste.className = "k2-runde";
    const runden = state.runden || [];
    const runde = Math.max(1, parseInt(state.runde, 10) || 1);
    if (runde > 1 || runden.length) {
      const vorher = runden[runden.length - 1];
      const teile = [uetf("Runde {0}", "ui", runde)];
      const fav = vorher ? imBogen(vorher, vorher.favoriten) : 0;
      const weg = vorher ? imBogen(vorher, vorher.verworfen) : 0;
      if (fav) teile.push(uetf("aus {0} Favoriten", "ui", fav));
      if (weg) teile.push(uetf("{0} verworfen", "ui", weg));
      const text = document.createElement("span");
      text.textContent = teile.join(" · ");
      leiste.append(text);
      if (vorher) {
        const zurueck = document.createElement("button");
        zurueck.type = "button";
        zurueck.className = "k2-textknopf";
        zurueck.textContent = "← " + uetf("zurück zu Runde {0}", "ui", Math.max(1, parseInt(vorher.runde, 10) || 1));
        zurueck.title = uet("Die vorige Runde mit ihren Einstellungen, Favoriten und Takes zurückholen.", "ui");
        zurueck.onclick = () => vorigeRunde(state);
        leiste.append(zurueck);
      }
    }
    const { fav, weg, moeglich } = rundenStand(state);
    const los = document.createElement("button");
    los.type = "button";
    los.className = "k2-start k2-klein";
    los.textContent = uet("Nächste Runde", "ui") + " →";
    los.disabled = !moeglich;
    los.title = los.disabled
      ? uet("Erst Favoriten (♥) im Kontaktbogen markieren: die nächste Runde behält ihre Einstellungen, Pose- und Stimmungsfamilien, Schwerpunkte und Outfits.", "ui")
      : uetf("Neue Serie ab Foto {0}: nur die Einstellungen, Pose- und Stimmungsfamilien, Schwerpunkte und Outfits der Auswahl ({1} ♥, {2} ✕).", "ui",
             Math.max(1, parseInt(state.start, 10) || 1) + (parseInt(state.anzahl, 10) || 1), fav, weg);
    los.onclick = naechsteRunde;
    leiste.append(los);
    if (einreihung.rundeFehler) {
      const f = document.createElement("span");
      f.className = "k2-warn";
      f.textContent = einreihung.rundeFehler;
      leiste.append(f);
    }
    return leiste;
  }

  // ------------------------------------------------- Pictures from history ---
  // Which finished picture belongs to which photo number. Read from ComfyUI's
  // history: every run of this node carries its photo number and its state in
  // the prompt. Only runs whose series settings match the current ones count -
  // count, start, favourites and takes excluded, since they do not change what
  // photo N is. Every take of a number is kept (the newest run per take); the
  // frame shows the chosen one, or the latest. Draft or not is no part of the
  // plan either: the draft and the finished photo 7 are the same frame, and
  // per take the finished one wins over a draft, however old.
  let aufnahmen = new Map();   // photo number -> Map(take -> picture)
  // Filled up with the defaults first: runs from before a key existed (say
  // "abdeckung") must still match - otherwise every extension of the state
  // would empty the contact sheet.
  const planSchluessel = (s) => {
    const kopie = { ...vorgabe, ...(s || {}), aktiv: { ...vorgabe.aktiv, ...(s?.aktiv || {}) } };
    for (const k of ["anzahl", "start", "favoriten", "takes", "takesJeFoto", "wahl",
                     "verworfen", "runde", "runden", "entwurf", "ordner"]) delete kopie[k];
    if (!kopie.kameras?.length || kopie.kameras.length === d.kamera.length) delete kopie.kameras;
    if (!kopie.fokusse?.length || kopie.fokusse.length === d.fokus.length) delete kopie.fokusse;
    // "mixed" gaze is the same plan as no gaze mode, which is what every run
    // from before the gaze chips carries.
    if (!kopie.blick || kopie.blick === "gemischt") delete kopie.blick;
    // The same for the axes that came later: at their "absent" reading (set
    // on, light and perspective off, the default orders and pools) they are
    // no part of the key, so a state from before them - and the pictures the
    // node remembers under its key - stays the same plan.
    const a = kopie.aktiv;
    if (a.set === true) delete a.set;
    if (!a.licht) delete a.licht;
    if (!a.perspektive) delete a.perspektive;
    if (!kopie.perspektiven?.length) delete kopie.perspektiven;
    if (!kopie.kameraOptik) delete kopie.kameraOptik;
    if (!kopie.requisiten) delete kopie.requisiten;
    if (!kopie.requisitText) delete kopie.requisitText;
    if ((kopie.setFolge ?? "bloecke") === "bloecke") delete kopie.setFolge;
    if ((kopie.lichtFolge ?? "je_set") === "je_set") delete kopie.lichtFolge;
    if ((kopie.lichtPool ?? d.alle) === d.alle) delete kopie.lichtPool;
    const sortiert = (x) => (x && typeof x === "object" && !Array.isArray(x)
      ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, sortiert(x[k])]))
      : x);
    return JSON.stringify(sortiert(kopie));
  };
  // ComfyUI keeps its history in memory only - after a restart it is empty,
  // while the pictures are still on disk. So the node remembers what it found
  // (file, subfolder, type per photo and take) in its properties, which travel
  // with the saved workflow. Per settings, for the last ten, so switching back
  // to earlier settings brings their pictures back too.
  const PROP_BILDER = "photoshootBilder";
  const kurzSchluessel = (text) => {
    let h = 0;
    for (let i = 0; i < text.length; i++) h = (Math.imul(h, 31) + text.charCodeAt(i)) | 0;
    return (h >>> 0).toString(36);
  };
  const bildUrl = (b, extra) => "/view?" + new URLSearchParams({
    filename: b.filename, subfolder: b.subfolder || "", type: b.type || "output", ...extra });
  async function ladeBilder() {
    try {
      const soll = planSchluessel(lies());
      const schluessel = kurzSchluessel(soll);
      const ablage = node.properties?.[PROP_BILDER]?.plaene || {};
      const neu = new Map();
      // What was remembered first; the history can only add or replace.
      for (const [nr, takes] of Object.entries(ablage[schluessel]?.bilder || {})) {
        const m = new Map();
        for (const [t, b] of Object.entries(takes)) {
          m.set(Number(t), { nummer: -1, take: Number(t), datei: b, entwurf: !!b.entwurf,
                             klein: bildUrl(b, { preview: "webp;60" }), gross: bildUrl(b, {}) });
        }
        neu.set(Number(nr), m);
      }
      const r = await fetch("/history?max_items=200", { cache: "no-store" });
      const verlauf = r.ok ? await r.json() : {};
      for (const eintrag of Object.values(verlauf)) {
        const prompt = eintrag?.prompt?.[2];
        const ich = prompt?.[String(node.id)];
        if (ich?.class_type !== CLASS_TYPE) continue;
        let st;
        try { st = JSON.parse(ich.inputs?.[HIDDEN] || "{}"); } catch (e) { continue; }
        if (planSchluessel(st) !== soll) continue;
        const nr = Math.max(1, parseInt(ich.inputs?.foto ?? ich.inputs?.seed, 10) || 1);
        let bild = null;
        for (const aus of Object.values(eintrag.outputs || {})) {
          for (const b of aus?.images || []) {
            if (!bild || (b.type === "output" && bild.type !== "output")) bild = b;
          }
        }
        if (!bild) continue;
        const nummer = eintrag.prompt[0];
        const take = (st.takes || {})[String(nr)] || 0;
        const entwurf = !!st.entwurf;
        if (!neu.has(nr)) neu.set(nr, new Map());
        const alt = neu.get(nr).get(take);
        // A finished take is never replaced by a draft of it; among equals
        // the newest run wins.
        if (alt && (alt.entwurf === entwurf ? alt.nummer > nummer : entwurf)) continue;
        const datei = { filename: bild.filename, subfolder: bild.subfolder || "", type: bild.type || "output",
                        ...(entwurf ? { entwurf: true } : {}) };
        neu.get(nr).set(take, { nummer, take, datei, entwurf, prompt: promptAus(eintrag),
                                klein: bildUrl(datei, { preview: "webp;60" }), gross: bildUrl(datei, {}) });
      }
      aufnahmen = neu;
      // Remember, only when something is there - and only the ten newest
      // settings, so the workflow file does not grow without end.
      if (neu.size) {
        const bilder = {};
        for (const [nr, takes] of neu) {
          bilder[nr] = Object.fromEntries([...takes].map(([t, e]) => [t, e.datei]));
        }
        const plaene = { ...ablage };
        delete plaene[schluessel];
        plaene[schluessel] = { bilder, zeit: Date.now() };
        const behalten = Object.entries(plaene).sort((a, b) => (b[1].zeit || 0) - (a[1].zeit || 0)).slice(0, 10);
        const alt = JSON.stringify(ablage[schluessel]?.bilder || {});
        if (alt !== JSON.stringify(bilder)) {
          node.properties = node.properties || {};
          node.properties[PROP_BILDER] = { plaene: Object.fromEntries(behalten) };
        }
      }
      zeichne();
    } catch (e) {
      // No history - the contact sheet simply stays empty frames.
    }
  }
  // The prompt a run got: Build Prompt hands it to the history as ui text
  // (Krea2PromptJoin.join in store.py). Only while ComfyUI keeps that run in
  // its history - the remembered pictures carry no prompt.
  function promptAus(eintrag) {
    const knoten = eintrag.prompt?.[2] || {};
    for (const [id, aus] of Object.entries(eintrag.outputs || {})) {
      if (knoten[id]?.class_type === "Krea2PromptJoin" && typeof aus?.text?.[0] === "string") return aus.text[0];
    }
    for (const [id, aus] of Object.entries(eintrag.outputs || {})) {
      if (knoten[id]?.class_type === "Krea2Photoshooting" && typeof aus?.text?.[0] === "string") return aus.text[0];
    }
    return null;
  }
  // Pictures remembered for other settings - the contact sheet says so when
  // an axis change leaves it empty.
  const andereBilder = (schluessel) => Object.entries(node.properties?.[PROP_BILDER]?.plaene || {})
    .some(([k, v]) => k !== schluessel && Object.keys(v?.bilder || {}).length);
  // The picture a frame shows: the chosen take if it exists, else the latest.
  function bildFuer(state, nr) {
    const takes = aufnahmen.get(nr);
    if (!takes?.size) return null;
    const wahl = state.wahl?.[String(nr)];
    if (wahl != null && takes.has(wahl)) return takes.get(wahl);
    return takes.get(Math.max(...takes.keys()));
  }
  let ladeTimer = null;
  const ladeSpaeter = () => { clearTimeout(ladeTimer); ladeTimer = setTimeout(ladeBilder, 400); };
  const aufFertig = () => {
    if (!ziel && einreihung.warteschlange.length) {
      einreihung.warteschlange.shift();
      einreihung.aktivFoto = einreihung.warteschlange[0] ?? null;
      zeichne();
    }
    ladeSpaeter();
  };
  const aufLeer = () => {
    if (!ziel && (einreihung.warteschlange.length || einreihung.aktivFoto != null)) {
      einreihung.warteschlange = [];
      einreihung.aktivFoto = null;
      zeichne();
    }
  };
  const aufStatus = (ev) => {
    const rem = ev?.detail?.exec_info?.queue_remaining;
    if (rem === 0 && !einreihung.einreihen) aufLeer();
  };
  api.addEventListener?.("executed", ladeSpaeter);
  api.addEventListener?.("execution_success", aufFertig);
  api.addEventListener?.("execution_error", aufLeer);
  api.addEventListener?.("execution_interrupted", aufLeer);
  api.addEventListener?.("status", aufStatus);
  aufraeumen.push(() => {
    api.removeEventListener?.("executed", ladeSpaeter);
    api.removeEventListener?.("execution_success", aufFertig);
    api.removeEventListener?.("execution_error", aufLeer);
    api.removeEventListener?.("execution_interrupted", aufLeer);
    api.removeEventListener?.("status", aufStatus);
    clearTimeout(ladeTimer);
  });

  // ----------------------------------------------- One source of truth ---
  // The photos of the series - plan, size, outfit, pictures and takes - and
  // what can be done with them, in one place. The contact sheet below and the
  // Lightbox (lightbox.mjs) both read and act through these, so they show the
  // same photos, and every action is a write of this node's state through
  // schreib(): one undo step, and both views redraw (zeichne() tells the
  // Lightbox, see the end of it).
  const verbunden = (name) => !!node.inputs?.find((i) => i.name === name)?.link;
  // Photos von … von + anzahl - 1 as the contact sheet shows them.
  function planeFotos(state, von, anzahl) {
    const outfits = garderobe();
    const outfitZahl = state.aktiv?.outfit !== false ? outfits.length : 0;
    const saetze = saetzeJetzt();
    const draussen = saetze.map((x) => x.draussen);
    // Sizes from outside only while the ratio axis is off - as shooting.py.
    const extern = verbunden("width_in") && verbunden("height_in") && !state.aktiv?.format
      ? externeMasse() : null;
    const liste = [];
    for (let nr = von; nr < von + anzahl; nr++) {
      const lauf = nr - 1;
      const p = plane(d, state, lauf, outfitZahl, saetze.length);
      const [bw, bh] = extern || masse(d, p.kamera, lauf, state, p.perspektive);
      const o = outfitZahl ? outfits[outfitFuer(d, state, lauf, outfitZahl)] : null;
      const k = setFuer(d, state, lauf, saetze.length);
      const sz = k != null ? { ...saetze[k], nr: k } : null;
      const licht = lichtFuer(d, state, lauf, draussen);
      liste.push({ nr, p, bw, bh, o, s: sz, licht, bild: bildFuer(state, nr), takes: aufnahmen.get(nr) || new Map() });
    }
    return liste;
  }
  // Detail level of a framing as a word: the quick choice and the detail box.
  const detailWoerter = () => ({ voll: uet("nah", "ui"), oben: uet("nah", "ui"),
                                  figur: uet("Figur", "ui"), identitaet: uet("weit", "ui") });
  // What a photo is, row by row: the detail box and the Lightbox's info column.
  function merkmale(f) {
    const detailWort = detailWoerter();
    return [
      [uet("Kamera", "ui"), f.p.kamera &&
        `${uet(f.p.kamera, "shooting/kamera")} (${detailWort[d.kameraDetail?.[f.p.kamera]] || ""})`],
      [uet("Pose", "ui"), [f.p.pose?.haltung && uet(f.p.pose.haltung, "pose/haltung"),
                           f.p.pose?.raum && uet(f.p.pose.raum, "pose/raum")].filter(Boolean).join(" · ")],
      [uet("Perspektive", "ui"), f.p.perspektive && uet(f.p.perspektive, "shooting/perspektive")],
      [uet("Schwerpunkt", "ui"), f.p.fokus && uet(f.p.fokus, "shooting/fokus")],
      [uet("Outfit", "ui"), f.o?.name],
      // The set, and what of it the framing shows (szene_fuer() in shooting.py).
      [uet("Set", "ui"), f.s && (f.s.name + (d.set?.weg?.includes(f.p.kamera) ? " · " + uet("nicht im Bild", "ui")
        : d.set?.kurz?.includes(f.p.kamera) ? " · " + uet("kurz", "ui") : ""))],
      [uet("Licht", "ui"), f.licht && uet(f.licht, "lighting/setup")],
      [uet("Stimmung", "ui"), f.p.ausdruck?.stimmung && uet(f.p.ausdruck.stimmung, "ausdruck/stimmung")],
    ].filter(([, v]) => v);
  }
  // A favourite and a reject exclude each other.
  const nummernVon = (liste) => new Set((liste || []).map(Number));
  function schalteFavorit(nr) {
    const state = lies();
    const f = nummernVon(state.favoriten);
    if (f.has(nr)) f.delete(nr); else f.add(nr);
    schreib({ ...state, favoriten: [...f].sort((a, b) => a - b),
              verworfen: [...nummernVon(state.verworfen)].filter((x) => x !== nr) });
  }
  function schalteVerworfen(nr) {
    const state = lies();
    const v = nummernVon(state.verworfen);
    if (v.has(nr)) v.delete(nr); else v.add(nr);
    schreib({ ...state, verworfen: [...v].sort((a, b) => a - b),
              favoriten: [...nummernVon(state.favoriten)].filter((x) => x !== nr) });
  }
  // The take a frame shows and Finish favourites renders.
  function waehleTake(nr, take) {
    const state = lies();
    schreib({ ...state, wahl: { ...(state.wahl || {}), [String(nr)]: take } });
  }
  // The round, its selects and rejects inside this series, and whether a next
  // round can start (not while photos are being queued).
  function rundenStand(state) {
    const favoriten = nummernVon(state.favoriten);
    const fav = imBogen(state, [...favoriten]);
    const weg = imBogen(state, [...nummernVon(state.verworfen)].filter((x) => !favoriten.has(x)));
    return { runde: Math.max(1, parseInt(state.runde, 10) || 1), fav, weg,
             moeglich: (fav > 0 || weg > 0) && !einreihung.einreihen };
  }
  const serie = {
    node,
    lies,
    // Every photo of the series, planned or shot.
    fotos: (state = lies()) => planeFotos(state, Math.max(1, parseInt(state.start, 10) || 1),
                                          Math.max(1, parseInt(state.anzahl, 10) || 1)),
    merkmale,
    schalteFavorit,
    schalteVerworfen,
    waehleTake,
    nachfotografieren: (nummern) => nachfotografieren(nummern),
    fertigstellen: (nummern) => fertigstellen(nummern),
    naechsteRunde: () => naechsteRunde(),
    stopp: () => stoppeLauf(),
    rundenStand,
    refine: () => refineVerdrahtet(node),
    // Queueing and what went wrong - the Lightbox shows it in its footer.
    lage: () => ({
      einreihen: einreihung.einreihen,
      einreiheFehler: einreihung.einreiheFehler,
      rundeFehler: einreihung.rundeFehler,
      aktivFoto: einreihung.aktivFoto,
      warteschlange: einreihung.warteschlange?.length || 0,
    }),
  };
  // The Lightbox takes the canvas view's object; the sidebar's acts the same
  // on the same node and needs no entry of its own.
  if (!ziel) {
    meldeSerie(serie);
    aufraeumen.push(() => meldeAb(serie));
  }

  function zeichne() {
    folge.gezeichnet();
    if (!ziel) versteckeZaehler();
    const state = lies();
    root.textContent = "";
    // The compact view (shared.mjs): brand strip, start, draft and finish,
    // one line of what the axes do and a strip of the photos. It goes into
    // one block of natural height, which the node's height is measured from.
    const kompakt = !ziel && istKompakt(node);
    root.classList.toggle("k2-kompakt", kompakt);
    const box = kompakt ? document.createElement("div") : root;
    if (kompakt) {
      box.className = "k2-kompakt-inhalt";
      root.append(box);
    }
    const anzahl = state.anzahl ?? 12;
    const start = Math.max(1, parseInt(state.start, 10) || 1);
    const dauerText = (sek) => {
      const gesamt = anzahl * Math.max(1, parseInt(state.takesJeFoto, 10) || 1) * sek;
      return "≈ " + (gesamt < 90 ? `${Math.round(gesamt)} s` : `${Math.round(gesamt / 60)} min`);
    };

    // --- brand strip ---------------------------------------------------------
    const marke = markenleiste("Series", uetf("{0} Fotos", "ui", anzahl) + " · " + dauerText(_sekProBild),
                               ziel ? null : node);
    box.append(marke);

    // --- count, start number, start button, status ---------------------------
    const serie = document.createElement("div");
    serie.className = "k2-serie-zeile";
    const zahlLbl = document.createElement("label");
    zahlLbl.textContent = uet("Fotos", "ui");
    const zahl = document.createElement("input");
    zahl.type = "number";
    zahl.min = "1";
    zahl.max = "500";
    zahl.value = String(anzahl);
    zahl.onchange = () => {
      const n = Math.max(1, Math.min(500, parseInt(zahl.value, 10) || 1));
      schreib({ ...state, anzahl: n });
    };
    zahlLbl.append(zahl);
    // Where the series begins. A new number is a new series with the same
    // settings - the answer to "how do I get different photos?". Typing a
    // number back in brings a series back.
    const abLbl = document.createElement("label");
    abLbl.textContent = uet("ab Nr.", "ui");
    const ab = document.createElement("input");
    ab.type = "number";
    ab.min = "1";
    ab.value = String(start);
    ab.title = uet("Startnummer. Die Serie beginnt bei diesem Foto.", "ui");
    ab.onchange = () =>
      schreib({ ...state, start: Math.max(1, parseInt(ab.value, 10) || 1) });
    abLbl.append(ab);
    const neu = document.createElement("button");
    neu.type = "button";
    neu.className = "k2-textknopf";
    neu.textContent = "↻ " + uet("Neue Serie", "ui");
    neu.title = uet("Neue Serie: zufällige Startnummer, gleiche Einstellungen", "ui");
    neu.onclick = () => schreib({ ...state, start: 1 + Math.floor(Math.random() * 999999) });
    serie.append(zahlLbl, abLbl, neu);
    if (!kompakt) root.append(serie);

    // --- recipes -------------------------------------------------------------
    // One click sets the axes for a kind of shoot (REZEPTE in shooting.py).
    // The chip of the recipe the state matches is lit; after any change of
    // your own none is, and nothing is lost - the axes simply are what they are.
    const gleich = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
    const passt = (patch) => Object.entries(patch).every(([k, v]) => {
      if (k === "aktiv") return Object.entries(v).every(([a, an]) => !!state.aktiv?.[a] === an);
      if (k === "pools") {
        const felder = new Set([...Object.keys(v), ...Object.keys(state.pools || {})]);
        return [...felder].every((f) => (v[f] ?? d.alle) === (state.pools?.[f] ?? d.alle));
      }
      if (k === "kameras" || k === "fokusse" || k === "perspektiven") {
        const norm = (x) => (x?.length ? [...x].sort() : null);
        return gleich(norm(v), norm(state[k]));
      }
      if (k === "abdeckung") return (reihenfolgeVon(state) === "reihum") === !!v;
      if (k === "reihenfolge") return reihenfolgeVon(state) === v;
      if (k === "bogen") return (bogenVon(d, state) || false) === (v || false);
      return gleich(v, state[k]);
    });
    const rezepte = document.createElement("div");
    rezepte.className = "k2-schnell k2-rezepte";
    rezepte.append(uet("Rezept", "ui") + ":");
    let getroffen = false;
    for (const r of d.rezepte || []) {
      const an = passt(r.patch);
      getroffen ||= an;
      const c = document.createElement("button");
      c.type = "button";
      c.className = "k2-chip k2-klein" + (an ? " k2-an" : "");
      c.textContent = uet(r.name, "ui");
      c.title = uet(r.beschreibung, "ui");
      c.onclick = () => schreib({
        ...state, ...r.patch,
        aktiv: { ...state.aktiv, ...r.patch.aktiv },
        pools: { ...r.patch.pools },
      });
      rezepte.append(c);
    }
    // Saved series next to the built-in recipes, each with an × to delete.
    const anwenden = (patch) => schreib({
      ...state, ...patch,
      aktiv: { ...state.aktiv, ...(patch.aktiv || {}) },
      pools: { ...(patch.pools || {}) },
    });
    for (const r of eigene) {
      const an = passt(r.patch);
      getroffen ||= an;
      const gruppe = document.createElement("span");
      gruppe.className = "k2-eigene";
      const c = document.createElement("button");
      c.type = "button";
      c.className = "k2-chip k2-klein" + (an ? " k2-an" : "");
      c.textContent = r.name;
      c.title = uet("Gespeicherte Serie: Einstellungen, Startnummer, Größe und Seed.", "ui");
      c.onclick = () => anwenden(r.patch);
      const weg = document.createElement("button");
      weg.type = "button";
      weg.className = "k2-weg-klein";
      weg.textContent = "×";
      weg.title = uetf("Gespeicherte Serie löschen: {0}", "ui", r.name);
      weg.setAttribute("aria-label", weg.title);
      weg.onclick = () => serienAnfrage("/krea2/serien/loeschen", { name: r.name });
      gruppe.append(c, weg);
      rezepte.append(gruppe);
    }
    if (!getroffen) {
      const eigen = document.createElement("span");
      eigen.className = "k2-eigen";
      eigen.textContent = uet("eigene Einstellung", "ui");
      rezepte.append(eigen);
    }
    // Save the current settings under a name.
    if (speichernOffen) {
      const feld = document.createElement("input");
      feld.className = "k2-serien-name";
      feld.placeholder = uet("Name der Serie", "ui");
      const ok = document.createElement("button");
      ok.type = "button";
      ok.className = "k2-textknopf";
      ok.textContent = uet("Speichern", "ui");
      const abbrechen = document.createElement("button");
      abbrechen.type = "button";
      abbrechen.className = "k2-textknopf";
      abbrechen.textContent = uet("Abbrechen", "ui");
      const sichern = () => {
        const name = feld.value.trim();
        if (!name) { feld.focus(); return; }
        const patch = Object.fromEntries(SERIEN_SCHLUESSEL.filter((k) => k in state).map((k) => [k, state[k]]));
        speichernOffen = false;
        serienAnfrage("/krea2/serien", { name, patch });
      };
      ok.onclick = sichern;
      abbrechen.onclick = () => { speichernOffen = false; zeichne(); };
      feld.onkeydown = (e) => {
        if (e.key === "Enter") sichern();
        else if (e.key === "Escape") { speichernOffen = false; zeichne(); }
      };
      rezepte.append(feld, ok, abbrechen);
      queueMicrotask(() => feld.focus());
    } else {
      const plus = document.createElement("button");
      plus.type = "button";
      plus.className = "k2-chip k2-klein k2-plus";
      plus.textContent = "+ " + uet("Speichern", "ui");
      plus.title = uet("Diese Einstellungen als eigene Serie speichern", "ui");
      plus.onclick = () => { speichernOffen = true; zeichne(); };
      rezepte.append(plus);
    }
    // The compact view has none: a recipe is a setting, made in the full one.
    if (!kompakt) root.append(rezepte);
    // Shoot files and the Director (regie.mjs): the whole shoot, not just the
    // series. The sidebar has them in its Director tab.
    if (!ziel && !kompakt) root.append(shootZeile(node, zeichne));

    const refineAn = refineVerdrahtet(node);
    const entwurfAn = refineAn && !!state.entwurf;
    const knopf = document.createElement("button");
    knopf.type = "button";
    knopf.className = "k2-start";
    const knopfText = document.createElement("b");
    knopfText.textContent = uet("Shooting starten", "ui");
    const knopfSub = document.createElement("small");
    const jeFoto = Math.max(1, parseInt(state.takesJeFoto, 10) || 1);
    knopf.append(knopfText, knopfSub);
    // The duration comes from the last runs; measured once the history is in.
    const beschrifte = (sek) => {
      knopfSub.textContent = uetf("Fotos {0}–{1}", "ui", start, start + anzahl - 1) +
        (jeFoto > 1 ? " · " + uetf("{0} Takes je Foto", "ui", jeFoto) : "") +
        (entwurfAn ? " · " + uet("Entwurf", "ui") : "") + " · " + dauerText(sek);
      marke.querySelector(".k2-marke-zahl").textContent =
        uetf("{0} Fotos", "ui", anzahl) + " · " + dauerText(sek);
      knopf.title = sek.toFixed(1) + " " + uet("s je Bild, gemessen an den letzten Läufen", "ui");
    };
    beschrifte(_sekProBild);
    messeSekundenProBild().then((sek) => { if (!einreihung.einreihen) beschrifte(sek); });
    if (einreihung.einreihen) {
      knopf.disabled = true;
      knopf.classList.add("k2-laeuft");
      knopfText.textContent = uetf("eingereiht {0}/{1}", "ui", einreihung.einreihen.n, einreihung.einreihen.gesamt);
    }
    knopf.onclick = () => starte(anzahl, start, jeFoto);
    box.append(knopf);
    if (einreihung.einreiheFehler) {
      const f = document.createElement("div");
      f.className = "k2-warn";
      f.textContent = einreihung.einreiheFehler;
      box.append(f);
    }

    // --- draft and finish ---------------------------------------------------
    // Draft: the series goes out without the render node's second pass, for
    // looking at many photos quickly. Finish favourites: the starred ones
    // again at full quality, same seed, same take. Both need the refine
    // output wired; without it they say so instead of doing nothing.
    const entwurfZeile = document.createElement("div");
    entwurfZeile.className = "k2-entwurf-zeile";
    const ohneRefine = uet("Verbinde den Ausgang refine mit einem refine-Schalter (der Render-Node der Beispiel-Workflows hat einen), dann geht Entwurf.", "ui");
    const ent = document.createElement("button");
    ent.type = "button";
    ent.className = "k2-textknopf k2-entwurf-knopf" + (entwurfAn ? " k2-an" : "");
    ent.textContent = (entwurfAn ? "☑ " : "☐ ") + uet("Entwurf", "ui");
    ent.setAttribute("aria-pressed", String(entwurfAn));
    ent.disabled = !refineAn || !!einreihung.einreihen;
    ent.title = refineAn
      ? uet("Entwurf: ohne zweiten Durchgang – etwa halbe Zeit, Grundauflösung. Favoriten danach fertigstellen.", "ui")
      : ohneRefine;
    ent.onclick = () => schreib({ ...state, entwurf: !state.entwurf });
    const favZahl = new Set((state.favoriten || []).map(Number)).size;
    const offenZahl = zuFertigen(state).length;
    const fertig = document.createElement("button");
    fertig.type = "button";
    fertig.className = "k2-textknopf k2-fertig-knopf";
    fertig.textContent = "✓ " + (offenZahl
      ? uetf("{0} Favoriten fertigstellen", "ui", offenZahl) : uet("Favoriten fertigstellen", "ui"));
    fertig.disabled = !refineAn || !offenZahl || !!einreihung.einreihen;
    fertig.title = !refineAn ? ohneRefine
      : !favZahl ? uet("Erst Fotos im Kontaktbogen als Favorit markieren.", "ui")
      : !offenZahl ? uet("Alle Favoriten sind fertig.", "ui")
      : uet("Die Favoriten in voller Qualität: gleicher Take, gleicher Seed, mit zweitem Durchgang.", "ui");
    fertig.onclick = () => fertigstellen();
    entwurfZeile.append(ent, fertig);
    if (einreihung.einreihen || einreihung.warteschlange.length) {
      const stopp = document.createElement("button");
      stopp.type = "button";
      stopp.className = "k2-textknopf k2-stopp";
      stopp.textContent = "⏹ " + uet("Stopp", "ui");
      stopp.title = uet("Laufendes Rendering abbrechen und Warteschlange leeren", "ui");
      stopp.onclick = stoppeLauf;
      entwurfZeile.append(stopp);
    }
    // Compact: the way to the Lightbox, which the contact sheet has otherwise.
    if (kompakt) {
      const lb = document.createElement("button");
      lb.type = "button";
      lb.className = "k2-textknopf k2-lb-auf";
      lb.textContent = "⤢ " + uet("Lightbox", "ui");
      lb.title = uet("In der Lightbox ansehen: groß, mit Filtern, Vergleich und Tasten (← → F X C).", "ui");
      lb.onclick = () => { if (!oeffneLightbox(node.id)) setzeAnsicht(node, false); };
      entwurfZeile.append(lb);
    }
    box.append(entwurfZeile);

    const status = document.createElement("div");
    status.className = "k2-status";
    const naechstes = Math.max(1, parseInt(zaehlerWidget()?.value, 10) || start);
    const links = document.createElement("span");
    if (einreihung.aktivFoto != null) {
      const nb = document.createElement("b");
      nb.textContent = uetf("Rendert Foto {0}", "ui", einreihung.aktivFoto);
      links.append(nb);
      if (einreihung.warteschlange.length > 1) {
        links.append(" · " + uetf("noch {0} in Queue", "ui", einreihung.warteschlange.length - 1));
      }
    } else {
      links.append(uet("Nächstes:", "ui") + " ");
      const nb = document.createElement("b");
      nb.textContent = uetf("Foto {0}", "ui", naechstes);
      links.append(nb);
    }
    const rechts = document.createElement("span");
    let imBogen = 0;
    for (let nr = start; nr < start + anzahl; nr++) if (aufnahmen.get(nr)?.size) imBogen++;
    // The counter can stand outside this series - after a workflow load, or
    // when the start number was changed. Queue would render that photo;
    // Start shooting resets it. Said here, or "next: photo 1" next to a
    // series from 101 reads like a bug.
    rechts.textContent = naechstes < start || naechstes > start + anzahl
      ? uetf("Start setzt ihn auf {0}", "ui", start)
      : uetf("{0} von {1} im Bogen", "ui", imBogen, anzahl);
    status.append(links, rechts);
    if (!kompakt) root.append(status);

    // --- the axes -------------------------------------------------------------
    // Are dimensions arriving from outside? That decides what the ratio switch
    // means.
    const massAnliegend = verbunden("width_in") && verbunden("height_in");
    // Applies only when the ratio is not being varied - shooting.py decides it
    // the same way. Otherwise the framing determines the ratio.
    const extern = massAnliegend && !state.aktiv?.format ? externeMasse() : null;

    // Which focus values can occur at all with the chosen settings. The focus
    // is coupled to the camera - a wide shot does not focus on the lips - and if
    // nothing is left after filtering, the photo gets none at all.
    const alleKameras = d.kamera.map((k) => k.label);
    const gewaehlteKameras = state.kameras?.length ? state.kameras : alleKameras;
    const erreichbar = new Set(
      state.aktiv?.kamera
        ? gewaehlteKameras.flatMap((k) => d.kameraFokus[k] || [])
        : d.fokus.map((f) => f.label),
    );
    const fokusGewaehlt = state.fokusse?.length ? state.fokusse : d.fokus.map((f) => f.label);
    const fokusWirksam = fokusGewaehlt.filter((f) => erreichbar.has(f));
    // The perspectives the chosen framings allow (PERSPEKTIVE_KAMERA).
    const alleSichten = (d.perspektive || []).map((p) => p.label);
    const sichtErreichbar = new Set(alleSichten.filter((l) => !state.aktiv?.kamera ||
      gewaehlteKameras.some((k) => (d.perspektiveKamera?.[l] || []).includes(k))));

    const familienStand = (quelle) => {
      const v = state.pools?.[d.gruppen[quelle].feld] ?? d.alle;
      if (Array.isArray(v)) return uetf("nur {0}", "ui", v.map((f) => uet(f, "familien")).join(", "));
      return v === d.alle ? uet("alle Familien", "ui") : uetf("nur {0}", "ui", uet(v, "familien"));
    };
    const kante = state.groesse || d.kanteStandard;
    const fest = state.festesFormat || "2:3";
    const [festW, festH] = masseFuer(d, fest, kante);

    // Size, the second half of the format: an edge length in the square.
    const groessenZeile = () => {
      if (massAnliegend && !state.aktiv?.format) {
        return notiz(extern
          ? `${extern[0]}×${extern[1]}  ·  ` + uet("von außen", "ui")
          : uet("von außen — Wert erst beim Ausführen bekannt", "ui"));
      }
      const zeile = auswahl(
        d.kanten.map((k) => ({ wert: String(k), text: `${k} px  ·  ${((k * k) / 1e6).toFixed(1)} MP` })),
        String(kante),
        (v) => schreib({ ...state, groesse: parseInt(v, 10) }),
        uet("Größe", "ui"),
      );
      zeile.title = uet("Kantenlänge im Quadrat. Das Seitenverhältnis kommt von der ", "ui") +
                    uet("Kameraeinstellung, nicht von hier.", "ui");
      return zeile;
    };

    const detailWort = detailWoerter();

    // The wardrobe on the input, and whether the outfit axis uses it. An
    // older state has no "outfit" switch and counts as on, as in Python.
    const outfits = garderobe();
    const outfitAn = state.aktiv?.outfit !== false;
    // The outfits a next round kept (outfitAuswahl), as outfitAuswahl() plans them.
    const outfitsInGebrauch = outfitAuswahl(state, outfits.length);

    const blickJetzt = (d.blick?.modi || []).includes(state.blick) ? state.blick : "gemischt";

    // The sets of the Location node on ort_data and the light axis. The set
    // switch reads as on without a key (like the outfit), the light as off:
    // a series without it plans as it always did (licht_fuer()).
    const saetze = saetzeJetzt();
    const setAn = state.aktiv?.set !== false;
    const lichtAn = !!state.aktiv?.licht;
    const lichtFolge = (d.licht?.folgen || []).includes(state.lichtFolge) ? state.lichtFolge : "je_set";
    const LICHT_FOLGEN = {
      je_set: [uet("je Set", "ui"), uet("Jedes Set bekommt ein passendes Licht und behält es auf allen seinen Fotos.", "ui")],
      tageszeit: [uet("Tageszeit", "ui"), uet("Der Tag über die Serie: Morgen, Mittag, Goldene Stunde, Blaue Stunde, Nacht – je Set das passende Licht dazu.", "ui")],
      gemischt: [uet("gemischt", "ui"), uet("Jedes Foto zieht sein Licht, passend zu seinem Set.", "ui")],
    };
    const lichtFamilien = (() => {
      const w = state.lichtPool ?? d.alle;
      const namen = (Array.isArray(w) ? w : [w]).filter((f) => d.licht?.familien?.[f]);
      return namen;
    })();

    const achsen = [
      {
        schluessel: "kamera",
        name: uet("Kamera", "ui"),
        stand: !state.aktiv?.kamera
          ? uet("aus", "ui")
          : state.kameras?.length && state.kameras.length < alleKameras.length
            ? uetf("{0} von {1} Einstellungen", "ui", state.kameras.length, alleKameras.length)
            : uetf("alle {0} Einstellungen", "ui", alleKameras.length),
        hinweis: uet("Kameraeinstellung über die Serie variieren", "ui"),
        zusatz: !state.aktiv?.kamera ? null
          : [{ reihum: uet("reihum", "ui"), weit_nah: uet("weit → nah", "ui") }[reihenfolgeVon(state)],
             state.kameraOptik ? "28–100mm" : null].filter(Boolean).join(" · ") || null,
        inhalt: state.aktiv?.kamera
          ? () => {
              // Quick choice by detail level: close, figure, wide - or all.
              const schnell = document.createElement("div");
              schnell.className = "k2-schnell";
              schnell.append(uet("Schnell:", "ui"));
              const gruppen = { alle: alleKameras };
              for (const [lbl, det] of Object.entries(d.kameraDetail || {})) (gruppen[det] ||= []).push(lbl);
              const sortiert = (a) => [...a].sort().join("|");
              for (const [g, labels] of Object.entries(gruppen)) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" +
                  (sortiert(gewaehlteKameras) === sortiert(labels) ? " k2-an" : "");
                c.textContent = g === "alle" ? uet("alle", "ui") : detailWort[g] || g;
                c.onclick = () => schreib({ ...state, kameras: g === "alle" ? null : labels });
                schnell.append(c);
              }
              // Order: drawn, in turn (coverage), or wide to close (dramaturgy).
              const ordnung = document.createElement("div");
              ordnung.className = "k2-schnell";
              ordnung.append(uet("Reihenfolge:", "ui"));
              const jetzt = reihenfolgeVon(state);
              for (const [wert, text, titel] of [
                ["gezogen", uet("gezogen", "ui"), uet("Verteilt gezogen, jedes Foto anders – wie bisher.", "ui")],
                ["reihum", uet("jede einmal, reihum", "ui"), uet("Jede gewählte Einstellung kommt reihum genau einmal dran, statt verteilt gezogen zu werden.", "ui")],
                ["weit_nah", uet("weit → nah", "ui"), uet("Dramaturgie: die Serie beginnt mit der weitesten Einstellung und endet mit der nächsten.", "ui")],
              ]) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (jetzt === wert ? " k2-an" : "");
                c.textContent = text;
                c.title = titel;
                c.setAttribute("aria-pressed", String(jetzt === wert));
                c.onclick = () => schreib({ ...state, reihenfolge: wert, abdeckung: wert === "reihum" });
                ordnung.append(c);
              }
              // Optional framing-coupled focal length (28mm wide .. 100mm macro).
              const optik = document.createElement("div");
              optik.className = "k2-schnell";
              optik.append(uet("Brennweite:", "ui"));
              for (const [wert, text, titel] of [
                [false, uet("aus Stil-Node", "ui"), uet("Die Brennweite kommt nur aus dem Style-Builder.", "ui")],
                [true, uet("je Einstellung (28–100mm)", "ui"), uet("Weitwinkel (28mm f/5.6) für weite Einstellungen, 50mm halbtotal, 85mm f/1.4 für Porträts, 100mm Makro nah.", "ui")],
              ]) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (!!state.kameraOptik === wert ? " k2-an" : "");
                c.textContent = text;
                c.title = titel;
                c.setAttribute("aria-pressed", String(!!state.kameraOptik === wert));
                c.onclick = () => schreib({ ...state, kameraOptik: wert });
                optik.append(c);
              }
              return [ordnung, schnell, optik, chipreihe(d.kamera, state.kameras,
                (n) => schreib({ ...state, kameras: n }), null, "shooting/kamera")];
            }
          : null,
      },
      {
        // Perspective axis (selfie mode & camera angles): appended to the
        // framing's wording. Off unless switched on.
        schluessel: "perspektive",
        name: uet("Perspektive", "ui"),
        stand: !state.aktiv?.perspektive
          ? uet("aus", "ui")
          : state.perspektiven?.length && state.perspektiven.length < alleSichten.length
            ? uetf("{0} von {1} Perspektiven", "ui", state.perspektiven.length, alleSichten.length)
            : uetf("alle {0} Perspektiven", "ui", alleSichten.length),
        hinweis: uet("Kamerawinkel über die Serie variieren, zuerst die Selfies. Aus: keine Perspektive im Prompt.", "ui"),
        inhalt: state.aktiv?.perspektive
          ? () => {
              const schnell = document.createElement("div");
              schnell.className = "k2-schnell";
              schnell.append(uet("Schnell:", "ui"));
              const sortiert = (a) => [...a].sort().join("|");
              const gewaehlt = state.perspektiven?.length ? state.perspektiven : alleSichten;
              for (const [g, labels] of [["alle", alleSichten], ...Object.entries(d.perspektiveGruppen || {})]) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (sortiert(gewaehlt) === sortiert(labels) ? " k2-an" : "");
                c.textContent = g === "alle" ? uet("alle", "ui") : uet(g, "familien");
                c.onclick = () => schreib({ ...state, perspektiven: g === "alle" ? null : labels });
                schnell.append(c);
              }
              return [
                schnell,
                chipreihe(d.perspektive || [], state.perspektiven,
                          (n) => schreib({ ...state, perspektiven: n }), sichtErreichbar, "shooting/perspektive"),
                notiz(uet("Nahaufnahme bis Halbtotale, das Spiegel-Selfie mit Ganzkörper. Durchgestrichen: passt zu keiner gewählten Kameraeinstellung.", "ui")),
                notiz(uet("Ein Selfie hat das Handy in einer Hand: nur Armhaltungen mit einer freien Hand, keine Rückenansicht, Format 9:16 oder 4:5. Im Liegen liegt sie auf dem Rücken; das Spiegel-Selfie zeigt den ganzen Körper und blickt aufs Display, nicht in die Linse.", "ui")),
                notiz(uet("Passt zum Stil-Genre Smartphone / Social.", "ui")),
              ];
            }
          : null,
      },
      {
        schluessel: "pose",
        name: uet("Pose", "ui"),
        stand: state.aktiv?.pose ? familienStand("pose") : uet("aus", "ui"),
        hinweis: uet("Körperhaltung variieren. Aufgeklappt: auf eine Familie einschränken.", "ui"),
        zusatz: state.aktiv?.pose ? ((state.requisitText || "").trim() || (state.requisiten ? uet("mit Requisiten", "ui") : null)) : null,
        inhalt: state.aktiv?.pose
          ? () => {
              const req = document.createElement("div");
              req.className = "k2-schnell";
              req.append(uet("Requisiten:", "ui"));
              for (const [wert, text, titel] of [
                [false, uet("aus", "ui"), uet("Armhaltungen ohne Requisiten – bisherige Serien unverändert.", "ui")],
                [true, uet("mit Requisiten (Tasse, Buch …)", "ui"), uet("Mischt Kaffeetasse, Buch, Weinglas und Blumenstrauß zu passenden Haltungen.", "ui")],
              ]) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (!!state.requisiten === wert ? " k2-an" : "");
                c.textContent = text;
                c.title = titel;
                c.setAttribute("aria-pressed", String(!!state.requisiten === wert));
                c.onclick = () => schreib({ ...state, requisiten: wert });
                req.append(c);
              }
              const frei = document.createElement("input");
              frei.className = "k2-frei";
              frei.placeholder = uet("Eigenes Requisit (englisch), z. B. a vintage camera, a red umbrella", "ui");
              frei.value = state.requisitText || "";
              frei.onchange = () => schreib({ ...state, requisitText: frei.value.trim() });
              frei.onkeydown = (ev) => ev.stopPropagation();
              return [req, frei, familienChips(state, "pose")];
            }
          : null,
      },
      {
        schluessel: "ausdruck",
        name: uet("Ausdruck", "ui"),
        stand: !state.aktiv?.ausdruck ? uet("aus", "ui")
          : bogenVon(d, state) ? uet("Stimmungsbogen", "ui") + " · " + uet(bogenVon(d, state), "ui")
          : familienStand("ausdruck"),
        hinweis: uet("Mimik variieren. Aufgeklappt: auf eine Stimmungsfamilie einschränken.", "ui"),
        zusatz: state.aktiv?.ausdruck && blickJetzt !== "gemischt"
          ? uet(d.blick?.namen?.[blickJetzt]?.name || blickJetzt, "ui") : null,
        inhalt: state.aktiv?.ausdruck
          ? () => {
              // Gaze over the whole series (BLICK_MODI in shooting.py): the
              // planner and this preview already follow it.
              const blick = document.createElement("div");
              blick.className = "k2-schnell";
              blick.append(uet("Blick:", "ui"));
              for (const m of d.blick?.modi || []) {
                const info = d.blick.namen?.[m] || { name: m };
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (blickJetzt === m ? " k2-an" : "");
                c.textContent = uet(info.name, "ui");
                if (info.beschreibung) c.title = uet(info.beschreibung, "ui");
                c.setAttribute("aria-pressed", String(blickJetzt === m));
                c.onclick = () => schreib({ ...state, blick: m });
                blick.append(c);
              }
              // Mood arc: the mood develops over the series instead of
              // jumping - then the family choice has nothing to say. Each arc
              // shows its stages: the first mood of each, joined by arrows.
              const zeile = document.createElement("div");
              zeile.className = "k2-schnell";
              zeile.append(uet("Stimmungsbogen:", "ui"));
              const jetzt = bogenVon(d, state);
              const knopf = (wert, text, titel) => {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + ((jetzt || false) === wert ? " k2-an" : "");
                c.textContent = text;
                if (titel) c.title = titel;
                c.onclick = () => schreib({ ...state, bogen: wert });
                zeile.append(c);
              };
              knopf(false, uet("aus", "ui"));
              for (const [name, stufen] of Object.entries(d.boegen || {})) {
                knopf(name, uet(name, "ui"),
                      stufen.map((st) => uet(st[0], "ausdruck/stimmung")).join(" → "));
              }
              if (!jetzt) return [blick, zeile, familienChips(state, "ausdruck")];
              const verlauf = notiz(d.boegen[jetzt].map((st) => uet(st[0], "ausdruck/stimmung")).join(" → "));
              return [blick, zeile, verlauf,
                      notiz(uet("Die Stimmung entwickelt sich über die Serie, Stufe für Stufe; innerhalb einer Stufe variiert sie.", "ui")),
                      notiz(uet("Wirkt am stärksten mit {expression} gleich nach {style} in der Prompt-Vorlage und einer Charakter-LoRA.", "ui"))];
            }
          : null,
      },
      {
        schluessel: "fokus",
        name: uet("Schwerpunkt", "ui"),
        stand: !state.aktiv?.fokus
          ? uet("aus", "ui")
          : !fokusWirksam.length
            ? uet("keiner passt", "ui")
            : state.fokusse?.length && state.fokusse.length < d.fokus.length
              ? uetf("{0} von {1} Bereichen", "ui", fokusWirksam.length, d.fokus.length)
              : uet("alle Bereiche", "ui"),
        hinweis: uet("Bildschwerpunkt variieren (Gesicht, Beine, Füße …). Welche ", "ui") +
                 uet("möglich sind, hängt von den gewählten Kameraeinstellungen ab.", "ui"),
        inhalt: state.aktiv?.fokus
          ? () => {
              const teile = [chipreihe(d.fokus, state.fokusse,
                (n) => schreib({ ...state, fokusse: n }), erreichbar, "shooting/fokus")];
              if (d.fokus.some((f) => !erreichbar.has(f.label))) {
                teile.push(notiz(uet("Durchgestrichen: kommt mit den gewählten Einstellungen nicht vor.", "ui")));
              }
              return teile;
            }
          : null,
      },
      {
        schluessel: "format",
        name: uet("Format", "ui"),
        stand: state.aktiv?.format
          ? uetf("folgt der Einstellung · {0} px", "ui", kante)
          : massAnliegend
            ? (extern ? `${extern[0]}×${extern[1]}` : uet("von außen", "ui"))
            : `${fest} · ${festW}×${festH}`,
        hinweis: uet("An: Seitenverhältnis passend zur Kameraeinstellung würfeln. ", "ui") +
                 uet("Aus: ein festes Verhältnis für alle Fotos.", "ui"),
        // Ratio and size together: both are the image dimensions.
        inhalt: () => {
          const teile = [];
          if (state.aktiv?.format) {
            teile.push(notiz(uet("Jede Einstellung wählt ein passendes Seitenverhältnis – Ganzkörper wird nie Querformat.", "ui")));
          } else if (!massAnliegend) {
            const chips = document.createElement("div");
            chips.className = "k2-chips";
            for (const r of Object.keys(d.ratios)) {
              const [rw, rh] = d.ratios[r];
              const s = 11 / Math.max(rw, rh);
              const c = document.createElement("button");
              c.type = "button";
              c.className = "k2-chip" + (r === fest ? " k2-an" : "");
              const icon = document.createElement("i");
              icon.className = "k2-rrect";
              icon.style.width = rw * s + "px";
              icon.style.height = rh * s + "px";
              c.append(icon, r);
              c.onclick = () => schreib({ ...state, festesFormat: r });
              chips.append(c);
            }
            teile.push(chips);
          }
          teile.push(groessenZeile());
          return teile;
        },
      },
      {
        schluessel: "outfit",
        an: outfitAn,
        name: uet("Outfit", "ui"),
        stand: !outfits.length
          ? uet("keine Garderobe", "ui")
          : !outfitAn
            ? uet("aus", "ui")
            : (outfitsInGebrauch.length < outfits.length
                ? uetf("{0} von {1} Outfits", "ui", outfitsInGebrauch.length, outfits.length)
                : outfits.length === 1 ? uet("1 Outfit", "ui") : uetf("{0} Outfits", "ui", outfits.length)) + " · " +
              (state.outfitFolge === "gemischt" ? uet("gemischt", "ui") : uet("in Blöcken", "ui")),
        hinweis: uet("Kostümwechsel: die Outfits der Wardrobe am Person Builder, ", "ui") +
                 uet("über die Serie verteilt", "ui"),
        inhalt: () => {
          if (!outfits.length) {
            const teile = [notiz(uet("Eine Wardrobe an den Eingang garderobe des Person Builders hängen, ", "ui") +
                                 uet("dann wechselt die Person hier die Outfits.", "ui"))];
            const pn = personNode();
            if (pn) {
              const btn = document.createElement("button");
              btn.type = "button";
              btn.className = "k2-textknopf";
              btn.textContent = uet("+ Wardrobe anlegen", "ui");
              btn.title = pn === node
                ? uet("In der Studio-Seitenleiste bearbeiten", "ui")
                : uet("Wardrobe-Node daneben anlegen und mit garderobe verbinden", "ui");
              btn.onclick = () => (pn === node
                ? oeffneStudio(node, "wardrobe")
                : erzeugeUndVerbinde("Krea2Wardrobe", pn, "garderobe", "garderobe"));
              teile.push(btn);
            }
            return teile;
          }
          const folge = document.createElement("div");
          folge.className = "k2-schnell";
          folge.append(uet("Folge:", "ui"));
          for (const [wert, text, titel] of [
            ["bloecke", uet("in Blöcken", "ui"), uet("Wie bei einem echten Shooting: erst alle Fotos im ersten Outfit, dann im zweiten. Die Kameraeinstellungen fangen mit jedem Outfit neu an.", "ui")],
            ["gemischt", uet("gemischt", "ui"), uet("Jedes Foto zieht sein Outfit.", "ui")],
          ]) {
            const c = document.createElement("button");
            c.type = "button";
            c.className = "k2-chip k2-klein" + ((state.outfitFolge || "bloecke") === wert ? " k2-an" : "");
            c.textContent = text;
            c.title = titel;
            c.onclick = () => schreib({ ...state, outfitFolge: wert });
            folge.append(c);
          }
          // Preview pictures, all outfits in one go (mannequin or flat lay is
          // chosen in the Wardrobe node).
          const vorschau = document.createElement("div");
          vorschau.className = "k2-schnell";
          const los = document.createElement("button");
          los.type = "button";
          los.className = "k2-textknopf";
          los.disabled = !!vorschauStatus && !vorschauStatus.startsWith("⚠");
          los.textContent = vorschauStatus || "▶ " + uetf("{0} Outfits rendern", "ui", outfits.length);
          los.title = uet("Ein Lauf je Outfit durch den eigenen Workflow, mit festem Studio-Look statt Stil und Licht des Shootings.", "ui");
          los.onclick = () => { if (vorschauStatus?.startsWith("⚠")) vorschauStatus = null; rendereOutfits(); };
          vorschau.append(los);
          // The rail: every outfit as a card.
          const stange = document.createElement("div");
          stange.className = "k2-stange";
          outfits.forEach((o, i) => {
            stange.append(outfitKarte(o, i + 1, i, outfits.length, state, outfitsInGebrauch.includes(i)));
          });
          if (outfitsInGebrauch.length < outfits.length) {
            // Narrowed by a next round; one click brings every outfit back.
            const alle = document.createElement("button");
            alle.type = "button";
            alle.className = "k2-textknopf";
            alle.textContent = uet("Alle Outfits verwenden", "ui");
            alle.onclick = () => schreib({ ...state, outfitAuswahl: null });
            return [folge, vorschau, stange, alle];
          }
          return [folge, vorschau, stange];
        },
      },
      {
        schluessel: "set",
        an: setAn,
        name: uet("Set", "ui"),
        stand: !saetze.length
          ? uet("kein Location-Node", "ui")
          : !setAn
            ? uet("aus", "ui")
            : (saetze.length === 1 ? uet("1 Set", "ui") : uetf("{0} Sets", "ui", saetze.length)) + " · " +
              (state.setFolge === "gemischt" ? uet("gemischt", "ui") : uet("in Blöcken", "ui")),
        hinweis: uet("Schauplatzwechsel: die Sets des Location-Nodes am Eingang ort_data, über die Serie verteilt", "ui"),
        inhalt: () => {
          if (!saetze.length) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "k2-textknopf";
            btn.textContent = uet("+ Location anlegen", "ui");
            btn.title = uet("Location-Node anlegen und mit Serie und Build Prompt verbinden", "ui");
            btn.onclick = () => {
              erzeugeUndVerbinde("Krea2LocationBuilder", node, "ort_data", "ort_data");
              const j = promptJoinNode(node);
              const szFrei = !node.outputs?.find((o) => o.name === "szene")?.links?.length;
              if (j && szFrei) verbindeNodes(node, "szene", j, "szene");
            };
            return [notiz(uet("Einen Photoshoot-Location-Node an den Eingang ort_data hängen, dann wechselt die Serie die Sets; ", "ui") +
                          uet("den Ausgang szene an szene von Build Prompt statt des festen Szenentexts.", "ui")), btn];
          }
          const folge = document.createElement("div");
          folge.className = "k2-schnell";
          folge.append(uet("Folge:", "ui"));
          for (const [wert, text, titel] of [
            ["bloecke", uet("in Blöcken", "ui"), uet("Wie bei einem echten Shooting: erst alle Fotos im ersten Set, dann im zweiten. Die Kameraeinstellungen fangen mit jedem Set neu an.", "ui")],
            ["gemischt", uet("gemischt", "ui"), uet("Jedes Foto zieht sein Set.", "ui")],
          ]) {
            const c = document.createElement("button");
            c.type = "button";
            c.className = "k2-chip k2-klein" + ((state.setFolge || "bloecke") === wert ? " k2-an" : "");
            c.textContent = text;
            c.title = titel;
            c.onclick = () => schreib({ ...state, setFolge: wert });
            folge.append(c);
          }
          // Every set: its colour on the contact sheet, name, indoors or
          // outdoors, and its text.
          const locNode = locationVonSerie(node);
          const liste = document.createElement("div");
          liste.className = "k2-satzliste";
          saetze.forEach((sz, k) => {
            const z = document.createElement("div");
            z.className = "k2-satz";
            const punkt = document.createElement("b");
            punkt.className = "k2-mini";
            punkt.style.background = setFarbe(k);
            const name = document.createElement("span");
            name.className = "k2-satz-name";
            name.textContent = `${k + 1}  ${sz.name}`;
            const wo = document.createElement("span");
            wo.className = "k2-anotiz";
            wo.textContent = sz.draussen === true ? uet("draußen", "ui")
              : sz.draussen === false ? uet("drinnen", "ui") : uet("ohne Familie", "ui");
            const edit = document.createElement("button");
            edit.type = "button";
            edit.className = "k2-satz-edit";
            edit.textContent = "✎";
            edit.title = uet("Im Location-Node bearbeiten", "ui");
            edit.onclick = (ev) => {
              ev.stopPropagation();
              if (!locNode) return;
              try {
                const st = JSON.parse(locNode.properties?.locationState || "{}");
                locNode.properties.locationState = JSON.stringify({ ...st, aktiv: k });
                locNode._k2Zeichne?.();
              } catch (e) { /* ignore */ }
              if (!oeffneStudio(locNode, "location")) {
                app.canvas?.selectNode?.(locNode);
                app.canvas?.centerOnNode?.(locNode);
              }
            };
            const text = document.createElement("div");
            text.className = "k2-satz-text" + (sz.text ? "" : " k2-leer");
            text.textContent = sz.text || uet("nichts gesetzt", "ui");
            text.title = sz.kurz ? uet("Kurzform (Nahaufnahme, Porträt):", "ui") + " " + sz.kurz : "";
            z.append(punkt, name, wo, edit, text);
            liste.append(z);
          });
          return [folge, liste,
                  notiz(uet("Nahaufnahme und Porträt bekommen die Kurzform – den ersten Teil jeder Angabe, was hinter dem Kopf zu sehen ist; Detail kein Set.", "ui"))];
        },
      },
      {
        schluessel: "licht",
        an: lichtAn,
        name: uet("Licht", "ui"),
        stand: !lichtAn
          ? uet("aus", "ui")
          : LICHT_FOLGEN[lichtFolge][0] +
            (lichtFolge !== "tageszeit" && lichtFamilien.length
              ? " · " + lichtFamilien.map((f) => uet(f, "familien")).join("/") : ""),
        hinweis: uet("Das Licht wechselt mit dem Set oder als Tageszeit über die Serie – aus den 30 Setups des Licht-Nodes.", "ui"),
        inhalt: lichtAn
          ? () => {
              const folge = document.createElement("div");
              folge.className = "k2-schnell";
              folge.append(uet("Folge:", "ui"));
              for (const [wert, [text, titel]] of Object.entries(LICHT_FOLGEN)) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (lichtFolge === wert ? " k2-an" : "");
                c.textContent = text;
                c.title = titel;
                c.setAttribute("aria-pressed", String(lichtFolge === wert));
                c.onclick = () => schreib({ ...state, lichtFolge: wert });
                folge.append(c);
              }
              const teile = [folge];
              if (lichtFolge === "tageszeit") {
                teile.push(notiz(d.licht.tageslauf.map(([n]) => uet(n, "ui")).join(" → ")));
              } else {
                // The setup families the axis draws from.
                const chips = document.createElement("div");
                chips.className = "k2-chips";
                for (const f of [d.alle, ...Object.keys(d.licht.familien)]) {
                  const c = document.createElement("button");
                  c.type = "button";
                  const drin = f === d.alle ? !lichtFamilien.length : lichtFamilien.includes(f);
                  c.className = "k2-chip" + (drin ? " k2-an" : "");
                  c.textContent = f === d.alle ? uet("alle", "ui") : uet(f, "familien");
                  c.onclick = () => schreib({ ...state, lichtPool: f });
                  chips.append(c);
                }
                teile.push(chips);
              }
              teile.push(notiz(uet("Draußen-Licht (Sonne, Golden Hour, Mond …) nur bei Sets draußen, Studio- und Fensterlicht nur drinnen.", "ui")));
              return teile;
            }
          : null,
      },
      {
        schluessel: "rausch",
        name: uet("Rauschen", "ui"),
        stand: state.aktiv?.rausch
          ? uet("neu pro Foto", "ui")
          : uetf("ein Seed · {0}", "ui", state.serienSeed ?? 0),
        hinweis: uet("An: jedes Foto bekommt eigenes Rauschen. Aus: die ganze Serie ", "ui") +
                 uet("teilt einen Seed, dann bleibt der Schauplatz über die Fotos gleich.", "ui"),
        zusatz: (parseInt(state.takesJeFoto, 10) || 1) > 1
          ? uetf("{0} Takes", "ui", state.takesJeFoto) : null,
        inhalt: () => {
          // Takes per photo: every planned photo rendered several times with
          // its own noise, to pick the better one per shot.
          const takesZeile = document.createElement("div");
          takesZeile.className = "k2-schnell";
          takesZeile.append(uet("Takes je Foto:", "ui"));
          for (const k of [1, 2, 3, 4]) {
            const c = document.createElement("button");
            c.type = "button";
            c.className = "k2-chip k2-klein" + ((parseInt(state.takesJeFoto, 10) || 1) === k ? " k2-an" : "");
            c.textContent = String(k);
            c.onclick = () => schreib({ ...state, takesJeFoto: k });
            takesZeile.append(c);
          }
          if (state.aktiv?.rausch) {
            return [notiz(uet("Jedes Foto bekommt eigenes Rauschen. Ausschalten hält den Schauplatz über die Serie gleich.", "ui")), takesZeile];
          }
          const zeile = document.createElement("div");
          zeile.className = "k2-feld";
          const n = document.createElement("div");
          n.className = "k2-name";
          n.textContent = "Seed";
          const feld = document.createElement("input");
          feld.type = "number";
          feld.min = "0";
          feld.value = String(state.serienSeed ?? 0);
          feld.onchange = () =>
            schreib({ ...state, serienSeed: Math.max(0, parseInt(feld.value, 10) || 0) });
          // The actual way to work with this: try a few seeds, keep the one
          // whose room you like.
          const anders = document.createElement("button");
          anders.type = "button";
          anders.className = "k2-textknopf";
          anders.textContent = "↻ " + uet("Anderer Schauplatz", "ui");
          anders.title = uet("Anderen Schauplatz suchen", "ui");
          anders.onclick = () =>
            schreib({ ...state, serienSeed: Math.floor(Math.random() * 2147483647) });
          zeile.append(n, feld, anders);
          return [zeile, takesZeile];
        },
      },
    ];

    if (kompakt) {
      // One line of what the axes do: the texts their rows show, a click
      // opens the Shoot tab of the Studio sidebar (or this node, expanded).
      const zeile = document.createElement("div");
      zeile.className = "k2-kurzfassung k2-achsen-kurz";
      const teile = achsen.filter((a) => ["kamera", "pose", "ausdruck", "outfit", "format"].includes(a.schluessel) ||
        (a.schluessel === "set" && saetze.length) || (a.schluessel === "licht" && lichtAn) ||
        (a.schluessel === "perspektive" && state.aktiv?.perspektive));
      teile.forEach((a, i) => {
        // One axis never breaks; the dot ends a part, so no line starts with it.
        const teil = document.createElement("span");
        teil.className = "k2-achsteil";
        const wert = document.createElement("b");
        wert.textContent = a.zusatz ? `${a.stand} · ${a.zusatz}` : a.stand;
        teil.append(a.name + " ", wert);
        if (i < teile.length - 1) {
          const trenner = document.createElement("i");
          trenner.textContent = "·";
          teil.append(trenner);
        }
        zeile.append(teil, " ");
      });
      box.append(alsBearbeiten(zeile, node));
    } else {
      const liste = document.createElement("div");
      liste.className = "k2-achsen";
      for (const a of achsen) liste.append(achse(a, state));
      root.append(liste);
    }

    // --- warnings -------------------------------------------------------------
    // Always visible, never behind a click: these are contradictions in the
    // wiring or between two axes, and a folded-away notice reaches nobody -
    // in the compact view too, under its photo strip.
    const warnungen = [];
    const warne = (text, titel, aktion = null) => {
      const w = document.createElement("div");
      w.className = "k2-warn";
      w.textContent = text;
      if (titel) w.title = titel;
      if (!aktion) { warnungen.push(w); return; }
      const z = document.createElement("div");
      z.className = "k2-warn-zeile";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "k2-textknopf";
      btn.textContent = "⚡ " + aktion.label;
      btn.onclick = aktion.onclick;
      z.append(w, btn);
      warnungen.push(z);
    };
    if (massAnliegend && state.aktiv?.format) {
      warne(uet("⚠ width/height liegen an, werden aber ignoriert — Format ausschalten", "ui"));
    }
    // Without person_data the series plans framing, pose and expression, but
    // shortens no person to the framing and changes no outfits. Embedded Studio
    // states satisfy this directly on the node.
    const hatEingebettet = !!(node.properties?.personState || node.properties?.wardrobeState || node.properties?.studioModus);
    if (!verbunden("person_data") && !hatEingebettet) {
      warne(uet("⚠ person_data ist nicht verbunden — den Ausgang person_data der Person hier anschließen", "ui"),
            uet("Ohne ihn kennt die Serie keine Person: kein Kürzen je Einstellung, keine Outfits.", "ui"),
            { label: uet("Verbinden", "ui"),
              onclick: () => erzeugeUndVerbinde("Krea2PersonBuilder", node, "person_data", "person_data") });
    }
    // A set or light axis whose output leads nowhere changes nothing in the
    // picture unless prompt output itself is wired directly (All-in-One Studio).
    const ausgangFrei = (name) => !node.outputs?.find((o) => o.name === name)?.links?.length;
    const join = promptJoinNode(node);
    const viaPrompt = !ausgangFrei("prompt");
    if (saetze.length && setAn && ausgangFrei("szene") && !viaPrompt) {
      warne(uet("⚠ Sets liegen an, aber der Ausgang szene ist nicht verbunden — an szene von Build Prompt hängen", "ui"),
            uet("Sonst bekommt Build Prompt weiter den festen Szenentext.", "ui"),
            join ? { label: uet("Verbinden", "ui"), onclick: () => verbindeNodes(node, "szene", join, "szene") } : null);
    }
    if (lichtAn && ausgangFrei("licht") && !viaPrompt) {
      warne(uet("⚠ Die Lichtachse ist an, aber der Ausgang licht ist nicht verbunden — an lighting von Build Prompt hängen", "ui"),
            uet("Sonst bekommt Build Prompt weiter das Licht des Licht-Nodes.", "ui"),
            join ? { label: uet("Verbinden", "ui"), onclick: () => {
              const slot = join.inputs?.find((i) => i.name === "lighting") ? "lighting" : "licht";
              verbindeNodes(node, "licht", join, slot);
            } } : null);
    }
    if (state.aktiv?.fokus && !fokusWirksam.length) {
      const namen = fokusGewaehlt.map((f) => uet(f, "shooting/fokus")).join(", ");
      warne(`⚠ ${namen} ` + uet("passt zu keiner gewählten Einstellung", "ui") + " " +
            uet("— es kommt gar kein Schwerpunkt in den Prompt", "ui"),
            uet("Der Schwerpunkt ist an die Kameraeinstellung gekoppelt. Entweder ", "ui") +
            uet("eine passende Einstellung dazuwählen oder einen anderen ", "ui") +
            uet("Schwerpunkt. Die durchgestrichenen Einträge sind die, die mit den ", "ui") +
            uet("aktuellen Einstellungen nicht vorkommen können.", "ui"));
    } else if (state.aktiv?.fokus && fokusWirksam.length < fokusGewaehlt.length) {
      const tot = fokusGewaehlt.filter((f) => !erreichbar.has(f)).map((f) => uet(f, "shooting/fokus"));
      warne(`${tot.join(", ")} ` + uet("kommt mit den gewählten Einstellungen nicht vor", "ui"),
            uet("Nicht schlimm - die übrigen Schwerpunkte greifen weiterhin.", "ui"));
    }
    // A fixed seed only holds the setting together while the image size stays
    // the same: the noise is a tensor in image dimensions.
    if (!state.aktiv?.rausch && state.aktiv?.format) {
      warne("⚠ " + uet("Format würfelt — bei wechselnder Größe wirkt der Serien-Seed nicht", "ui"),
            uet("Das Rauschen hat Bildmaße. Ändert sich das Seitenverhältnis, ist es ", "ui") +
            uet("ein anderes Rauschfeld, auch bei gleichem Seed.", "ui"));
    }
    if (!kompakt) root.append(...warnungen);

    // --- contact sheet ---------------------------------------------------------
    // The sidebar is too narrow for it: a button opens the Lightbox instead,
    // which is the contact sheet big.
    if (ziel) {
      const zeile = document.createElement("div");
      zeile.className = "k2-studio-lb";
      const auf = document.createElement("button");
      auf.type = "button";
      auf.className = "k2-textknopf k2-lb-auf";
      auf.textContent = "⤢ " + uet("Lightbox öffnen", "ui");
      auf.title = uet("In der Lightbox ansehen: groß, mit Filtern, Vergleich und Tasten (← → F X C).", "ui");
      auf.onclick = () => oeffneLightbox(node.id);
      zeile.append(auf);
      root.append(zeile);
      return;
    }
    const favoriten = new Set((state.favoriten || []).map(Number));
    const verworfen = new Set((state.verworfen || []).map(Number));
    if (kompakt) {
      // The strip: the frames of the contact sheet's current page, small -
      // the picture once rendered, dashed while only planned, ♥ and ✕ as
      // marked. A click opens that photo in the Lightbox.
      const { von, gezeigt } = seiteVon(start, anzahl, PRO_SEITE);
      proZeile = 0;
      const streifen = document.createElement("div");
      streifen.className = "k2-streifen";
      for (const { nr, bild } of planeFotos(state, von, gezeigt)) {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "k2-mini-bild" + (bild ? "" : " k2-geplant") + (verworfen.has(nr) ? " k2-verworfen" : "") +
          (nr === einreihung.aktivFoto ? " k2-rendert" : "");
        if (bild) b.style.backgroundImage = `url("${bild.klein}")`;
        b.title = uetf("Foto {0}", "ui", nr);
        b.setAttribute("aria-label", b.title);
        if (favoriten.has(nr) || verworfen.has(nr)) {
          const zeichen = document.createElement("em");
          zeichen.textContent = (favoriten.has(nr) ? "♥" : "") + (verworfen.has(nr) ? "✕" : "");
          b.append(zeichen);
        }
        b.onclick = () => { if (!oeffneLightbox(node.id, nr)) setzeAnsicht(node, false); };
        streifen.append(b);
      }
      box.append(streifen, ...warnungen);
      passeKompaktAn(node, root);
      serieGeaendert(node.id);
      return;
    }
    // Every photo as a frame in its real ratio, like the frames in the logo;
    // once rendered, with the picture in it. A click shows the details and the
    // actions below: favourite, mark for a re-shoot, open the picture.
    const bogen = document.createElement("div");
    bogen.className = "k2-bogen";
    // Two rows of frames, the rest in the Lightbox, which pages through all
    // of them. Without it, 24 frames a page and ‹ › as before.
    const knapp = lightboxDa();
    proZeile = knapp ? zeilenBreite() : 0;
    const { seiten, von, gezeigt } = knapp ? { seiten: 1, von: start, gezeigt: Math.min(anzahl, 2 * proZeile) }
      : seiteVon(start, anzahl, PRO_SEITE);
    const blaettern = (neu) => {
      seite = Math.min(Math.max(0, neu), seiten - 1);
      gewaehlt = start + seite * PRO_SEITE;
      zeichne();
    };
    const kopf = document.createElement("div");
    kopf.className = "k2-bogen-kopf";
    const kl = document.createElement("span");
    kl.className = "k2-bogen-titel";
    kl.append(uet("Kontaktbogen", "ui"));
    const lb = document.createElement("button");
    lb.type = "button";
    lb.className = "k2-textknopf k2-lb-auf";
    lb.textContent = "⤢ " + uet("Lightbox", "ui");
    lb.title = uet("In der Lightbox ansehen: groß, mit Filtern, Vergleich und Tasten (← → F X C).", "ui");
    lb.onclick = () => oeffneLightbox(node.id, gewaehlt);
    kl.append(lb);
    const kr = document.createElement("span");
    kr.className = "k2-seiten";
    if (seiten > 1) {
      const pfeil = (text, titel, ziel, aus) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "k2-blaettern";
        b.textContent = text;
        b.title = titel;
        b.setAttribute("aria-label", titel);
        b.disabled = aus;
        b.onclick = () => blaettern(ziel);
        return b;
      };
      const mitte = document.createElement("span");
      mitte.textContent = uetf("{0}–{1} von {2}", "ui", von, von + gezeigt - 1, anzahl);
      kr.append(pfeil("‹", uet("Vorige Seite", "ui"), seite - 1, seite === 0), mitte,
                pfeil("›", uet("Nächste Seite", "ui"), seite + 1, seite === seiten - 1));
    } else {
      kr.textContent = uetf("{0} Fotos", "ui", anzahl);
    }
    kopf.append(kl, kr);
    const raster = document.createElement("div");
    raster.className = "k2-bilder";
    if (gewaehlt == null || gewaehlt < von || gewaehlt >= von + gezeigt) gewaehlt = von;
    const plaene = planeFotos(state, von, gezeigt);
    for (const { nr, p, bw, bh, o, s: sz, bild } of plaene) {
      const hoehe = 46, breite = 52;
      const w = Math.min(breite, (hoehe * bw) / bh), h = Math.min(hoehe, (breite * bh) / bw);
      const b = document.createElement("button");
      b.type = "button";
      b.className = "k2-bild" + (nr === gewaehlt ? " k2-gewaehlt" : "") + (bild ? " k2-fertig" : "") +
        (verworfen.has(nr) ? " k2-verworfen" : "") + (bild?.entwurf ? " k2-entwurf" : "") +
        (nr === einreihung.aktivFoto ? " k2-rendert" : "");
      b.setAttribute("aria-label", uetf("Foto {0}", "ui", nr));
      b.title = uet("Doppelklick: in der Lightbox öffnen", "ui");
      const rahmen = document.createElement("div");
      rahmen.className = "k2-rahmen";
      rahmen.style.width = w + "px";
      rahmen.style.height = h + "px";
      if (bild) rahmen.style.backgroundImage = `url("${bild.klein}")`;
      const nummer = document.createElement("i");
      nummer.textContent = String(nr);
      rahmen.append(nummer);
      // Costume changes: a stripe in the outfit's main colour under the frame.
      if (o) {
        const streifen = document.createElement("b");
        streifen.className = "k2-ostreifen";
        streifen.style.background = hauptfarbe(o);
        streifen.title = o.name;
        rahmen.append(streifen);
      }
      // Set changes: a stripe in the set's colour over the frame.
      if (sz) {
        const streifen = document.createElement("b");
        streifen.className = "k2-sstreifen";
        streifen.style.background = setFarbe(sz.nr);
        streifen.title = sz.name;
        rahmen.append(streifen);
      }
      if (favoriten.has(nr) || markiert.has(nr) || verworfen.has(nr)) {
        const zeichen = document.createElement("em");
        zeichen.textContent = (favoriten.has(nr) ? "♥" : "") + (verworfen.has(nr) ? "✕" : "") +
          (markiert.has(nr) ? "↻" : "");
        rahmen.append(zeichen);
      }
      const unter = document.createElement("span");
      unter.className = "k2-bild-label";
      unter.textContent = p.kamera ? uet(p.kamera, "shooting/kamera") : "—";
      b.append(rahmen, unter);
      // A second click on the same frame opens it in the Lightbox. Counted
      // here rather than by dblclick: the first click redraws the sheet, so
      // the second lands on a new button.
      b.onclick = () => {
        const jetzt = Date.now();
        const doppelt = letzterKlick?.nr === nr && jetzt - letzterKlick.zeit < 450;
        letzterKlick = doppelt ? null : { nr, zeit: jetzt };
        gewaehlt = nr;
        if (doppelt) oeffneLightbox(node.id, nr);
        zeichne();
      };
      raster.append(b);
    }
    // What follows this page, as a button to it.
    const danach = start + anzahl - (von + gezeigt);
    let mehrLb = null;
    if (danach > 0 && knapp) {
      const mehr = document.createElement("button");
      mehr.type = "button";
      mehr.className = "k2-mehr k2-mehr-lb";
      mehr.textContent = uetf("+{0} · alle in der Lightbox", "ui", danach);
      mehr.title = uet("In der Lightbox ansehen: groß, mit Filtern, Vergleich und Tasten (← → F X C).", "ui");
      mehr.onclick = () => oeffneLightbox(node.id, von + gezeigt);
      mehrLb = mehr;
    } else if (danach > 0) {
      const mehr = document.createElement("button");
      mehr.type = "button";
      mehr.className = "k2-mehr";
      mehr.textContent = `+${danach} ›`;
      mehr.title = uet("Nächste Seite", "ui");
      mehr.onclick = () => blaettern(seite + 1);
      raster.append(mehr);
    }
    bogen.append(kopf, raster);
    if (mehrLb) bogen.append(mehrLb);
    if (knapp) {
      requestAnimationFrame(() => {
        const breite = raster.clientWidth;
        if (!breite || !raster.isConnected || breite === rasterBreite) return;
        rasterBreite = breite;
        rootBreite = root.clientWidth;
        if (zeilenBreite() !== proZeile) zeichne();
      });
    }
    // An axis change is a different plan: its frames are empty while the
    // pictures of the earlier settings wait in the node.
    let imPlan = 0;
    for (let nr = start; nr < start + anzahl; nr++) if (aufnahmen.get(nr)?.size) imPlan++;
    if (!imPlan && andereBilder(kurzSchluessel(planSchluessel(state)))) {
      bogen.append(notiz(uet("Die Bilder der vorigen Einstellungen bleiben erhalten — zurückstellen, um sie zu sehen.", "ui")));
    }

    const g = plaene.find((x) => x.nr === gewaehlt);
    if (g) {
      const det = document.createElement("div");
      det.className = "k2-detail";
      const zeile = (k, v) => {
        if (!v) return;
        const a = document.createElement("span");
        a.textContent = k;
        const b = document.createElement("b");
        b.textContent = v;
        det.append(a, b);
      };
      const bild = g.bild;
      zeile(uet("Foto", "ui"), `${g.nr} · ${g.bw}×${g.bh}` +
        (bild && (bild.take || g.takes.size > 1)
          ? " · " + uetf("Take {0}", "ui", bild.take + 1) : "") +
        (bild?.entwurf ? " · " + uet("Entwurf", "ui") : ""));
      for (const [k, v] of merkmale(g)) zeile(k, v);
      // The prompt this take got, from the same history entry as its picture.
      if (bild) {
        const a = document.createElement("span");
        a.textContent = uet("Prompt", "ui");
        const box = document.createElement("div");
        box.className = "k2-prompt";
        if (bild.prompt) {
          const text = document.createElement("div");
          text.className = "k2-prompt-text";
          text.textContent = bild.prompt;
          // The answer to the click outlives a redraw (a finished run
          // redraws the sheet) for a moment.
          const kopie = document.createElement("button");
          kopie.type = "button";
          kopie.className = "k2-textknopf";
          const frisch = kopiert && kopiert.text === bild.prompt && Date.now() < kopiert.bis;
          kopie.textContent = !frisch ? uet("Kopieren", "ui")
            : kopiert.ok ? "✓ " + uet("Kopiert", "ui") : uet("Kopieren fehlgeschlagen", "ui");
          kopie.onclick = async () => {
            kopiert = { text: bild.prompt, ok: await kopiere(bild.prompt), bis: Date.now() + 1500 };
            zeichne();
            setTimeout(zeichne, 1600);
          };
          box.append(text, kopie);
        } else {
          box.classList.add("k2-anotiz");
          box.textContent = uet("nicht mehr im Verlauf — ComfyUI wurde seitdem neu gestartet", "ui");
        }
        det.append(a, box);
      }

      // All takes of this photo side by side; a click makes one the chosen.
      const takes = g.takes;
      if (takes.size > 1) {
        const streifen = document.createElement("div");
        streifen.className = "k2-takes";
        for (const t of [...takes.keys()].sort((a, b) => a - b)) {
          const bt = takes.get(t);
          const k = document.createElement("button");
          k.type = "button";
          k.className = "k2-take" + (bild?.take === t ? " k2-an" : "") + (bt.entwurf ? " k2-entwurf" : "");
          k.style.backgroundImage = `url("${bt.klein}")`;
          k.style.aspectRatio = `${g.bw} / ${g.bh}`;
          k.title = uetf("Take {0}", "ui", t + 1) + (bt.entwurf ? " · " + uet("Entwurf", "ui") : "");
          const z = document.createElement("i");
          z.textContent = String(t + 1);
          k.append(z);
          k.onclick = () => waehleTake(g.nr, t);
          streifen.append(k);
        }
        det.append(streifen);
      }

      const aktionen = document.createElement("div");
      aktionen.className = "k2-aktionen";
      const fav = document.createElement("button");
      fav.type = "button";
      fav.className = "k2-textknopf" + (favoriten.has(g.nr) ? " k2-an" : "");
      fav.textContent = (favoriten.has(g.nr) ? "♥ " : "♡ ") + uet("Favorit", "ui");
      fav.onclick = () => schalteFavorit(g.nr);
      const verw = verwerfenKnopf(g.nr, verworfen);
      aktionen.append(fav, verw);
      if (!bild) {
        const schiessen = document.createElement("button");
        schiessen.type = "button";
        schiessen.className = "k2-textknopf";
        schiessen.textContent = "▶ " + uet("Foto schießen", "ui");
        schiessen.title = uet("Nur dieses geplante Foto jetzt einreihen", "ui");
        schiessen.disabled = !!einreihung.einreihen;
        schiessen.onclick = () => nachfotografieren([g.nr]);
        aktionen.append(schiessen);
      }
      const mark = document.createElement("button");
      mark.type = "button";
      mark.className = "k2-textknopf" + (markiert.has(g.nr) ? " k2-an" : "");
      mark.textContent = "↻ " + uet("Nachfotografieren", "ui");
      mark.title = uet("Gleiche Planung, neues Rauschen", "ui");
      mark.onclick = () => {
        if (markiert.has(g.nr)) markiert.delete(g.nr); else markiert.add(g.nr);
        zeichne();
      };
      aktionen.append(mark);
      if (bild) {
        const oeffnen = document.createElement("a");
        oeffnen.className = "k2-textknopf";
        oeffnen.href = bild.gross;
        oeffnen.target = "_blank";
        oeffnen.rel = "noopener";
        oeffnen.textContent = uet("Bild öffnen", "ui");
        aktionen.append(oeffnen);
      } else {
        const noch = document.createElement("span");
        noch.className = "k2-anotiz";
        noch.textContent = uet("noch nicht fotografiert", "ui");
        aktionen.append(noch);
      }
      det.append(aktionen);
      bogen.append(det);
    }

    if (markiert.size) {
      const leiste = document.createElement("div");
      leiste.className = "k2-nachhol";
      const los = document.createElement("button");
      los.type = "button";
      los.className = "k2-start k2-klein";
      los.textContent = markiert.size === 1
        ? uet("1 Foto nachfotografieren", "ui")
        : uetf("{0} Fotos nachfotografieren", "ui", markiert.size);
      los.onclick = () => nachfotografieren([...markiert].sort((a, b) => a - b));
      const weg = document.createElement("button");
      weg.type = "button";
      weg.className = "k2-textknopf";
      weg.textContent = uet("Auswahl aufheben", "ui");
      weg.onclick = () => { markiert.clear(); zeichne(); };
      leiste.append(los, weg);
      bogen.append(leiste);
    }
    bogen.append(rundenLeiste(state));
    root.append(bogen);
    // Whatever changed here - a write, new pictures, queueing - the Lightbox
    // draws again if it shows this node.
    serieGeaendert(node.id);
  }

  // The other view of this node (canvas or sidebar) follows every write and
  // every drawing here (shared.mjs, ansicht()).
  const folge = ansicht(node, zeichne);
  aufraeumen.push(() => folge.weg());
  const alleWeg = () => { for (const f of aufraeumen.splice(0)) f(); };
  if (ziel) {
    ziel.append(root);
    zeichne();
    queueMicrotask(ladeBilder);
    return { root, weg: () => { alleWeg(); root.remove(); } };
  }
  beimEntfernen(node, alleWeg);

  queueMicrotask(zeichne);
  queueMicrotask(ladeBilder);
  node._k2Zeichne = zeichne;

  // When a different ratio is chosen in the upstream node, this node hears
  // nothing about it - there is no event to hook onto and the connection stays
  // the same. So look rather than wait. Reading two numbers out of properties
  // costs nothing; a redraw only happens when they have actually changed, since
  // otherwise the caret in the number fields would be lost on every tick.
  const standJetzt = () => (externeMasse() || []).join("×");
  // Record immediately, not on the first tick. This started out as an initial
  // assignment inside the tick itself - which swallowed exactly the change that
  // happened between build and first tick, leaving the first switch on the
  // upstream node without effect.
  let letzteExtern = standJetzt();
  const ticker = setInterval(() => {
    // Once the node is deleted it no longer hangs off the graph. Without this
    // exit the tick would keep running until the page is reloaded.
    if (!node.graph) {
      clearInterval(ticker);
      return;
    }
    const jetzt = standJetzt();
    if (jetzt !== letzteExtern) {
      letzteExtern = jetzt;
      zeichne();
    }
  }, 500);

  // The height follows the node: hard-wired, everything below the edge stayed
  // unreachable and dragging it larger did not help.
  const CHROM = 72; // title and outputs - the photo-number row is hidden now
  // A fixed height in the full view, the content's in the compact one. 860
  // since the set and light axes: two more rows, and two more outputs above
  // the panel; 890 with the perspective row.
  node._k2Kompakt = { vollHoehe: 890 };
  const w = node.addDOMWidget("k2_shooting", "custom", root, {
    getValue: () => node.properties?.[PROP],
    setValue: () => {},
    getMinHeight: () => (istKompakt(node) ? 40 : 240),
    getMaxHeight: () => Math.max(240, (node.size?.[1] || 560) - CHROM),
    margin: 4,
    serialize: false,
  });
  applyAdaptiveCanvasOnly(w);
}

registriereStateInjektion(CLASS_TYPE, HIDDEN, PROP, VORGABE, fuerDenLauf);

// The Studio sidebar's Shoot tab (studio.mjs) draws this panel into its column.
registriereBauer(CLASS_TYPE, async (node, ziel) => {
  const presets = await ladePresets();
  return presets?.shooting ? baue(node, presets.shooting, presets.person, ziel, presets.location) : null;
});

app.registerExtension({
  name: "Krea2." + CLASS_TYPE,

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== CLASS_TYPE) return;
    const orig = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      // Loaded from a workflow: its saved size stands (see nodeCreated).
      this._k2Geladen = true;
      const r = orig?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
    // A wardrobe or a Location node wired in or out changes the outfit and
    // set axes and the stripes.
    const origVerbindung = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function () {
      const r = origVerbindung?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
  },

  async nodeCreated(node) {
    if (node.comfyClass !== CLASS_TYPE) return;
    // Brand strip, series row, start, ten axes and a contact sheet of twelve
    // frames with its detail box. Only for new nodes - when a workflow is
    // loaded, onConfigure puts the saved size back afterwards.
    // The default size only for a new node. nodeCreated awaits the presets,
    // and a workflow's configure() runs in the meantime - setting the size
    // here unconditionally threw away every saved size.
    // A new node starts compact; a loaded one keeps what it was saved with,
    // full when it has no view property (saved before there was one).
    const bauen = (presets) => {
      if (!node._k2Geladen) {
        node.size = [360, 890];
        node.properties = node.properties || {};
        node.properties[PROP_ANSICHT] ??= "kompakt";
      }
      baue(node, presets.shooting, presets.person, null, presets.location);
    };
    const presets = await ladePresets();
    if (presets?.shooting) bauen(presets);
    else presetFehler(node, bauen);
  },
});

// Only for cross-checking against Python.
export { plane as _plane, format as _format, masse as _masse, outfitFuer as _outfitFuer,
         setFuer as _setFuer, lichtFuer as _lichtFuer };

