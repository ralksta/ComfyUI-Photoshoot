// The Studio sidebar: the whole shoot in one column, over the full height.
//
// A tab in ComfyUI's left sidebar ("Photoshoot"), with the tabs Person, Look
// (light, style and the Location node's sets), Pose, Shoot, Director and Your
// setup. It has no interface of its own for
// the Photoshoot nodes: each section is the node's own panel, drawn by the
// same function that draws it on the canvas (registriereBauer() in panel.mjs,
// person.mjs and shooting.mjs), on the same node.properties. A write in one
// goes through schreibeState() and the other view draws again (ansicht() in
// shared.mjs), undo covers both.
//
// Which nodes: the Series chosen in the head (the selected one, else the
// first), and what regie.mjs' ziele() finds wired to it - the same nodes a
// shoot file is written to.
//
// "Your setup" holds widgets of any node, pinned through the node's context
// menu (a LoRA loader's lora_name and strength, a sampler's steps). The pins
// live in the workflow (graph.extra.photoshootPins), so they are saved with
// it and undo sees them.
//
// Which tab and which series are shown is view, not setting: nothing of it
// goes into the workflow; the tab is remembered in the browser.

import {
  aktualisierePresets,
  ansicht,
  bauerFuer,
  beimEntfernen,
  einstellung,
  erzeugeUndVerbinde,
  injiziereCSS,
  kopiere,
  ladePresets,
  leseState,
  markenleiste,
  merkeFuerUndo,
  promptJoinNode,
  registriereStudioOeffner,
  schreibeState,
  setzeAnsicht,
  verbindeNodes,
  zeigeToast,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=3.0.0";
import { regieInto, shootZeile, ziele } from "./regie.mjs?v=3.0.0";
import { oeffneLightbox } from "./lightbox.mjs?v=3.0.0";

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const TAB_ID = "photoshoot-studio";
const SERIE = "Krea2Photoshooting";
const CSS_ID = "photoshoot-studio-css";
const MERK = "photoshoot.studio.reiter";
const PINS = "photoshootPins";
const EMBED = new Set(["person", "wardrobe", "lighting", "style", "location"]);
const STANDARD_VORLAGE = "{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}";

// Tab -> the shoot sections it shows (the keys of /krea2/presets "shoot",
// the same ziele() resolves). Regie and Setup draw their own content.
const REITER = [
  ["person", "Person", ["person", "wardrobe"]],
  ["look", "Look", ["lighting", "style", "location"]],
  ["pose", "Pose", ["pose", "expression"]],
  ["shoot", "Shoot", ["series"]],
  ["regie", "Regie", []],
  ["setup", "Dein Setup", []],
];

const CSS = `
.k2-studio{height:100%;min-height:0;display:flex;flex-direction:column;background:#1b1b1b;color:#d7d7d7;
  font:11px/1.35 -apple-system,Segoe UI,Roboto,sans-serif;box-sizing:border-box}
.k2-studio *{box-sizing:border-box}
.k2-studio-kopf{padding:10px 12px 0;display:flex;flex-direction:column;gap:8px;border-bottom:1px solid #303030;
  background:#1f1f1f}
.k2-studio-kopf .k2-marke{border-bottom:0;padding-bottom:0}
.k2-studio-serie{display:flex;align-items:center;gap:6px;font-size:10px;color:#8a8a8a;text-transform:uppercase;
  letter-spacing:.06em}
.k2-studio-serie select{flex:1;min-width:0;background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;border-radius:4px;
  padding:3px 4px;font:inherit;font-size:11px;text-transform:none;letter-spacing:0}
.k2-studio-reiter{display:flex;gap:1px;overflow-x:auto;scrollbar-width:none}
.k2-studio-reiter button{background:none;border:0;border-bottom:2px solid transparent;padding:7px 6px;cursor:pointer;
  color:#9a9a9a;font:inherit;font-size:11px;font-weight:500;white-space:nowrap;flex:0 0 auto}
.k2-studio-reiter button:hover{color:#e8e8e8}
.k2-studio-reiter button[aria-selected="true"]{color:#f0f0f0;border-color:#f66744}
.k2-studio-reiter button:focus-visible{outline:1px solid #f66744;outline-offset:-1px}
.k2-studio-inhalt{flex:1;min-height:0;overflow-y:auto;padding:10px 12px 240px;display:flex;flex-direction:column;gap:14px}
.k2-studio-inhalt::-webkit-scrollbar{width:7px}
.k2-studio-inhalt::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-studio-abschnitt{display:flex;flex-direction:column;gap:6px}
.k2-studio-titel{display:flex;align-items:baseline;gap:6px;font-size:9.5px;letter-spacing:.09em;text-transform:uppercase;
  color:#8a8a8a;font-weight:600}
.k2-studio-titel b{color:#e6e6e6;font-weight:600;text-transform:none;letter-spacing:0;font-size:12px}
.k2-studio-titel .k2-studio-hin{margin-left:auto;background:none;border:1px solid transparent;border-radius:4px;color:#8e8e8e;
  cursor:pointer;font:inherit;font-size:10px;text-transform:none;letter-spacing:0;padding:1px 5px}
.k2-studio-titel .k2-studio-hin:hover{color:#f66744;border-color:#3d3d3d}
.k2-studio-fehlt{color:#8e8e8e;font-style:italic;font-size:11px;padding:6px 8px;border:1px dashed #3d3d3d;border-radius:6px}
.k2-studio-fehlt .k2-studio-hin{margin-top:6px;background:none;border:1px solid #3d3d3d;border-radius:4px;color:#f66744;
  cursor:pointer;font:inherit;font-style:normal;font-size:11px;padding:3px 8px}
.k2-studio-fehlt .k2-studio-hin:hover{border-color:#f66744;background:rgba(246,103,68,.08)}
.k2-studio-lb{display:flex;justify-content:flex-start;padding-top:2px}
.k2-studio-lb .k2-lb-auf{font-size:11px;padding:3px 10px}
.k2-pins{display:flex;flex-direction:column;gap:6px}
.k2-pin{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 6px;align-items:center;background:#222;
  border:1px solid #333;border-radius:6px;padding:6px 8px}
.k2-pin-name{font-size:9.5px;letter-spacing:.04em;color:#a8a8a8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.k2-pin-name b{color:#e6e6e6;font-weight:600;letter-spacing:0}
.k2-pin-feld{grid-column:1/-1;display:flex;gap:6px;align-items:center}
.k2-pin-feld select,.k2-pin-feld input[type=number],.k2-pin-feld input[type=text],.k2-pin-feld textarea{flex:1;min-width:0;
  background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;border-radius:4px;padding:4px 5px;font:inherit;font-size:11px}
.k2-pin-feld textarea{resize:vertical;min-height:48px}
.k2-pin-feld input[type=range]{flex:1;min-width:0;accent-color:#f66744}
.k2-pin-feld input[type=range] + .k2-pin-zahl{flex:0 0 76px}
.k2-pin-feld input[type=checkbox]{accent-color:#f66744;width:15px;height:15px}
.k2-pin-feld select:focus,.k2-pin-feld input:focus,.k2-pin-feld textarea:focus{outline:none;border-color:#f66744}
.k2-pin-weg{background:none;border:0;color:#8e8e8e;cursor:pointer;font-size:14px;line-height:1;padding:0 3px}
.k2-pin-weg:hover{color:#f66744}
.k2-pin.k2-pin-fehlt{opacity:.55}
.k2-pin.k2-pin-fehlt .k2-pin-feld{font-style:italic;color:#8e8e8e}
.k2-studio-notiz{color:#8e8e8e;font-size:11px;line-height:1.45}
.k2-studio-titel .k2-studio-tag{font-size:9px;color:#8e8e8e;text-transform:none;letter-spacing:0}
.k2-studio-vorlage{width:100%;background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;border-radius:4px;
  padding:4px 6px;font:inherit;font-size:10.5px;resize:vertical;min-height:42px}
.k2-studio-vorlage:focus{outline:none;border-color:#f66744}
.k2-wl-box{display:flex;flex-direction:column;gap:7px}
.k2-wl-feld{display:flex;flex-direction:column;gap:3px;font-size:10px;color:#b0b0b0}
.k2-wl-feld select,.k2-wl-feld input,.k2-wl-feld textarea{background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;
  border-radius:4px;padding:4px 6px;font:inherit;font-size:10.5px;width:100%}
.k2-wl-feld textarea{resize:vertical;min-height:40px}
.k2-wl-feld select:focus,.k2-wl-feld input:focus,.k2-wl-feld textarea:focus{outline:none;border-color:#f66744}
.k2-wl-reihen{display:flex;flex-direction:column;gap:8px;margin-top:2px}
.k2-wl-reihe{background:#222;border:1px solid #333;border-radius:6px;padding:6px 8px;display:flex;flex-direction:column;gap:5px}
.k2-wl-kopf{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10.5px}
.k2-wl-kopf b{color:#e8e8e8}
.k2-wl-wort{font-size:9.5px;color:#9a9a9a;font-style:italic;word-break:break-word}
.k2-wl-gitter{display:grid;grid-template-columns:1fr 1fr;gap:6px}
.k2-wl-kachel{position:relative;display:block;aspect-ratio:2/3;background:#161616;border:1px solid #303030;
  border-radius:4px;overflow:hidden}
.k2-wl-kachel img{width:100%;height:100%;object-fit:cover;display:block}
.k2-wl-seed{position:absolute;left:4px;bottom:4px;background:rgba(0,0,0,.72);color:#d7d7d7;font-size:8.5px;
  padding:1px 4px;border-radius:3px}
.k2-wl-warten{display:flex;align-items:center;justify-content:center;height:100%;color:#7a7a7a;font-size:10px}
.k2-studio-personen{display:flex;flex-direction:column;gap:6px;background:#202020;border:1px solid #303030;
  border-radius:6px;padding:7px 8px}
.k2-studio-ptabs{display:flex;align-items:center;gap:6px}
.k2-studio-pbtn{background:#181818;border:1px solid #3a3a3a;border-radius:4px;color:#b0b0b0;cursor:pointer;
  font:inherit;font-size:10.5px;font-weight:500;padding:3px 9px}
.k2-studio-pbtn:hover{color:#f0f0f0;border-color:#555}
.k2-studio-pbtn[aria-selected="true"]{background:rgba(246,103,68,.16);color:#f66744;border-color:#f66744}
.k2-studio-pcheck{margin-left:auto;display:flex;align-items:center;gap:5px;font-size:10.5px;color:#c8c8c8;cursor:pointer}
.k2-studio-pcheck input{accent-color:#f66744;margin:0}
.k2-studio-paar{display:flex;align-items:center;gap:6px;font-size:10px;color:#9a9a9a}
.k2-studio-paar select{flex:1;min-width:0;background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;
  border-radius:4px;padding:3px 5px;font:inherit;font-size:10.5px}
.k2-cast-bar{display:flex;flex-direction:column;gap:5px;background:#1f1f1f;border:1px solid #2e2e2e;
  border-radius:6px;padding:6px 8px}
.k2-cast-kopf{display:flex;align-items:center;justify-content:space-between;gap:6px;font-size:10.5px}
.k2-cast-kopf b{color:#dcdcdc;font-weight:600}
.k2-cast-liste{display:flex;flex-wrap:wrap;gap:4px}
.k2-cast-karte{display:inline-flex;align-items:center;gap:4px;background:#262626;border:1px solid #3c3c3c;
  border-radius:5px;padding:3px 6px;font-size:10px;max-width:100%}
.k2-cast-karte:hover{border-color:#f66744}
.k2-cast-laden{background:none;border:none;color:#e6e6e6;cursor:pointer;font:inherit;padding:0;
  display:inline-flex;align-items:center;gap:4px;min-width:0;text-align:left}
.k2-cast-sub{color:#8e8e8e;font-size:9px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:140px}
.k2-cast-lora{background:#2d201c;border:1px solid #8c4835;color:#f3a893;font-size:8.5px;border-radius:3px;padding:0 3px}
.k2-cast-form{display:flex;gap:4px;align-items:center}
.k2-cast-form input{flex:1;min-width:0}
.k2-pack-box{display:flex;flex-direction:column;background:#222;border:1px solid #333;border-radius:5px;overflow:hidden}
.k2-pack-kopf{display:flex;align-items:center;gap:5px;padding:4px 7px;font-size:10px}
.k2-pack-toggle{background:none;border:none;color:#c9a08f;cursor:pointer;font:inherit;padding:0 2px;font-size:10px}
.k2-pack-kopf b{color:#e6e6e6;font-weight:600;cursor:pointer}
.k2-pack-meta{color:#8e8e8e;font-size:9.5px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.k2-pack-dice{display:inline-flex;align-items:center;gap:2px;font-size:9.5px;color:#b8b8b8;cursor:pointer;
  padding:1px 4px;border:1px solid #383838;border-radius:4px;background:#1b1b1b}
.k2-pack-dice.k2-an{border-color:#f66744;color:#f3d6cb;background:#2e201b}
.k2-pack-dice input{display:none}
.k2-pack-items{border-top:1px solid #2e2e2e;display:flex;flex-direction:column;gap:3px;padding:5px 7px;
  background:#1b1b1b;max-height:240px;overflow-y:auto}
.k2-pack-item{display:flex;flex-direction:column;gap:3px;padding:3px 5px;border:1px solid #2a2a2a;
  border-radius:4px;background:#212121;font-size:9.5px}
.k2-pack-item-top{display:flex;align-items:center;gap:5px}
.k2-pack-item-cat{color:#8a8f98;font-family:ui-monospace,Menlo,monospace;font-size:8.5px;flex-shrink:0}
.k2-pack-item-lbl{color:#e6e6e6;font-weight:600}
.k2-pack-item-prm{color:#9a9a9a;font-size:9px;word-break:break-word}
.k2-pack-edit{display:flex;flex-direction:column;gap:3px;margin-top:2px}
.k2-pack-edit input,.k2-pack-edit textarea{background:#161616;color:#d7d7d7;border:1px solid #3d3d3d;
  border-radius:4px;padding:3px 5px;font:inherit;font-size:9.5px;width:100%}
.k2-modell-tabs{display:flex;flex-wrap:wrap;gap:4px}
.k2-modell-grid{display:flex;flex-direction:column;gap:5px;margin-top:4px}
.k2-modell-zeile{display:flex;flex-direction:column;gap:2px;font-size:9.5px;color:#b5b5b5}
.k2-modell-zeile input{background:#181818;color:#d7d7d7;border:1px solid #3a3a3a;border-radius:4px;
  padding:3px 6px;font:inherit;font-size:10px;width:100%}
.k2-icon-logo,.k2-icon-shoot{display:inline-block;width:16px;height:16px;flex-shrink:0;vertical-align:middle;
  background-repeat:no-repeat;background-position:center;background-size:contain}
.side-bar-button-icon.k2-icon-logo{width:1em;height:1em}
.k2-icon-logo{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E%3Cg fill='none' stroke='%238a8f98' stroke-width='5.5'%3E%3Crect x='2.75' y='2.75' width='27.5' height='39.5' rx='5'/%3E%3Crect x='2.75' y='50' width='39.5' height='27.25' rx='5'/%3E%3Crect x='50' y='50' width='27.25' height='27.25' rx='5'/%3E%3C/g%3E%3Crect x='37' y='0' width='43' height='43' rx='5' fill='%23f66744'/%3E%3Ccircle cx='58.5' cy='15' r='6.5' fill='%231b1d21'/%3E%3Cpath d='M44 43a14.5 14.5 0 0 1 29 0z' fill='%231b1d21'/%3E%3C/svg%3E")}
.k2-icon-shoot{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 80'%3E%3Cg fill='none' stroke='%238a8f98' stroke-width='5.5'%3E%3Crect x='2.75' y='2.75' width='27.5' height='39.5' rx='5'/%3E%3Crect x='2.75' y='50' width='39.5' height='27.25' rx='5'/%3E%3Crect x='50' y='50' width='27.25' height='27.25' rx='5'/%3E%3C/g%3E%3Crect x='37' y='0' width='43' height='43' rx='5' fill='%23f66744'/%3E%3Cpolygon points='51,10 70,21.5 51,33' fill='%231b1d21'/%3E%3C/svg%3E")}
html:not(.k2-hat-photoshoot) .k2-ab-auto{display:none!important}
html:not(.k2-hat-serie) .k2-ab-serie{display:none!important}
html:not(.k2-hat-photoshoot) [data-testid="action-bar-buttons"]:not(:has(> :not(.k2-ab-auto):not(:has(.k2-ab-auto)))){display:none!important}
`;

function css() {
  injiziereCSS();
  if (document.getElementById(CSS_ID)) return;
  const s = document.createElement("style");
  s.id = CSS_ID;
  s.textContent = CSS;
  document.head.appendChild(s);
}

const el = (tag, klasse, text) => {
  const e = document.createElement(tag);
  if (klasse) e.className = klasse;
  if (text != null) e.textContent = text;
  return e;
};
const alleNodes = () => {
  const g = app.canvas?.graph || app.graph;
  return g?._nodes || g?.nodes || [];
};
const klassenName = (klasse) => globalThis.LiteGraph?.registered_node_types?.[klasse]?.title || klasse;

// ------------------------------------------------------------------ View ---
// zeige: the node a compact panel asked for, scrolled to once drawn.
const sicht = { serieId: null, reiter: "person", personNr: 1, zeige: null, zeigeAbschnitt: null };

function eingangNode(node, eingang) {
  const linkId = node?.inputs?.find((i) => i.name === eingang)?.link;
  if (linkId == null) return null;
  const g = app.canvas?.graph || app.graph;
  const link = g?.links?.get?.(linkId) ?? g?.links?.[linkId];
  return (link && g?.getNodeById?.(link.origin_id)) || null;
}
let _vonNode = false;   // opened from a node: its series stands
try {
  const r = localStorage.getItem(MERK);
  if (REITER.some(([k]) => k === r)) sicht.reiter = r;
} catch (e) {
  // no storage - the sidebar starts on Person
}

let wurzel = null;
let inhalt = null;
let _daten = null;
let griffe = [];        // { weg() } of every panel drawn into the column
let generation = 0;     // a newer drawing makes an older one's late panels go
let ticker = 0;
let letzterStand = "";

// Node objects get a number of their own: undo builds new nodes under the
// same ids, and the column has to be drawn again for them.
const _nummern = new WeakMap();
let _naechste = 1;
const objNr = (n) => {
  if (!n) return 0;
  if (!_nummern.has(n)) _nummern.set(n, _naechste++);
  return _nummern.get(n);
};

function serien() {
  return alleNodes().filter((n) => n?.comfyClass === SERIE);
}

function gewaehlteSerie() {
  try {
    return Object.values(app.canvas?.selected_nodes || {}).find((n) => n?.comfyClass === SERIE) || null;
  } catch (e) {
    return null;
  }
}

function aktuelleSerie() {
  const liste = serien();
  return liste.find((n) => n.id === sicht.serieId) || gewaehlteSerie() || liste[0] || null;
}

function zieleJetzt(serie) {
  const info = _daten?.shoot;
  if (!info) return {};
  try {
    return ziele(serie, info);
  } catch (e) {
    return {};
  }
}

// ------------------------------------------------------------------ Pins ---
const pins = () => (Array.isArray(app.graph?.extra?.[PINS]) ? app.graph.extra[PINS] : []);
const pinSchluessel = (p) => String(p.nodeId) + "|" + p.widget;

function setzePins(liste) {
  if (!app.graph) return;
  app.graph.extra = app.graph.extra || {};
  if (liste.length) app.graph.extra[PINS] = liste;
  else delete app.graph.extra[PINS];
  app.graph.setDirtyCanvas?.(true, true);
  merkeFuerUndo();
  zeichneBald();
}

function istAngeheftet(node, w) {
  return pins().some((p) => String(p.nodeId) === String(node.id) && p.widget === w.name);
}

function schaltePin(node, w) {
  const schluessel = String(node.id) + "|" + w.name;
  if (pins().some((p) => pinSchluessel(p) === schluessel)) {
    setzePins(pins().filter((p) => pinSchluessel(p) !== schluessel));
  } else {
    setzePins([...pins(), { nodeId: node.id, widget: w.name,
                            label: (node.title || node.type) + " · " + (w.label || w.name) }]);
  }
}

// Widgets a user can pin: the node's own values, not its buttons, previews
// or our panels.
function anheftbar(node) {
  return (node.widgets || []).filter((w) => w?.name && !String(w.name).startsWith("k2_") &&
    !w.options?.hidden && !["button", "custom", "hidden", "converted-widget"].includes(String(w.type)) &&
    !w.element && ["string", "number", "boolean"].includes(typeof w.value));
}

function schreibeWidget(node, w, wert) {
  w.value = wert;
  try {
    w.callback?.(w.value, app.canvas, node, undefined, undefined);
  } catch (e) {
    // a pack's own callback - the value is set
  }
  node.setDirtyCanvas?.(true, true);
  app.graph?.setDirtyCanvas?.(true, true);
  merkeFuerUndo();
}

// A control matching the widget: combo -> select, number -> number field
// (and a slider for a narrow range), toggle -> checkbox, text -> input. Values are read live,
// every time the tab draws.
function steuerung(node, w) {
  const feld = el("div", "k2-pin-feld");
  const typ = String(w.type || "").toLowerCase();
  const o = w.options || {};
  if (typ === "combo") {
    const auswahl = el("select");
    let werte = o.values;
    if (typeof werte === "function") {
      try { werte = werte(w, node); } catch (e) { werte = []; }
    }
    werte = Array.isArray(werte) ? werte : [];
    if (!werte.includes(w.value)) werte = [w.value, ...werte];
    for (const v of werte) {
      const opt = el("option", null, String(v));
      opt.value = String(v);
      auswahl.append(opt);
    }
    auswahl.value = String(w.value);
    auswahl.onchange = () => schreibeWidget(node, w, werte.find((v) => String(v) === auswahl.value) ?? auswahl.value);
    feld.append(auswahl);
  } else if (typeof w.value === "number") {
    // The canvas keeps a legacy step ten times too large in "step"; the real
    // one is "step2" where the front end has it.
    const schritt = Number(o.step2) || (Number(o.step) ? Number(o.step) / 10 : 1);
    const ganz = o.precision === 0 || (o.round === 1 && Number.isInteger(w.value));
    const zahl = el("input", "k2-pin-zahl");
    zahl.type = "number";
    for (const [k, v] of [["min", o.min], ["max", o.max]]) if (Number.isFinite(Number(v))) zahl[k] = String(v);
    zahl.step = String(schritt);
    zahl.value = String(w.value);
    const setze = (roh) => {
      let v = Number(roh);
      if (!Number.isFinite(v)) return;
      if (Number.isFinite(Number(o.min))) v = Math.max(Number(o.min), v);
      if (Number.isFinite(Number(o.max))) v = Math.min(Number(o.max), v);
      if (ganz) v = Math.round(v);
      else v = Number(v.toFixed(Math.max(0, Math.min(6, Number.isInteger(o.precision) ? o.precision : 4))));
      schreibeWidget(node, w, v);
      zahl.value = String(w.value);
      if (regler) regler.value = String(w.value);
    };
    // A slider too where the range is a narrow one (denoise, a LoRA loader's
    // strength where the pack limits it); on -100…100 or a seed up to 2^64 a
    // slider cannot hit a value, so those keep the number field alone.
    let regler = null;
    if (Number.isFinite(Number(o.min)) && Number.isFinite(Number(o.max)) && Number(o.max) - Number(o.min) <= 10) {
      regler = el("input");
      regler.type = "range";
      regler.min = String(o.min);
      regler.max = String(o.max);
      regler.step = String(schritt);
      regler.value = String(w.value);
      regler.oninput = () => { zahl.value = regler.value; };
      regler.onchange = () => setze(regler.value);
      feld.append(regler);
    }
    zahl.onchange = () => setze(zahl.value);
    feld.append(zahl);
  } else if (typeof w.value === "boolean") {
    const box = el("input");
    box.type = "checkbox";
    box.checked = !!w.value;
    box.onchange = () => schreibeWidget(node, w, box.checked);
    const name = el("span", null, String(o.on && w.value ? o.on : !w.value && o.off ? o.off : ""));
    feld.append(box, name);
  } else {
    const mehrzeilig = typ === "customtext" || o.multiline;
    const text = el(mehrzeilig ? "textarea" : "input");
    if (!mehrzeilig) text.type = "text";
    text.value = String(w.value ?? "");
    text.onchange = () => schreibeWidget(node, w, text.value);
    feld.append(text);
  }
  return feld;
}

function zeichnePins(ziel) {
  const liste = pins();
  if (!liste.length) {
    ziel.append(el("div", "k2-studio-notiz",
      uet("Rechtsklick auf einen beliebigen Node → „An Photoshoot Studio anheften“ legt seine Einstellungen hierher, etwa lora_name und strength deiner LoRA-Loader.", "ui")));
    return;
  }
  const box = el("div", "k2-pins");
  for (const p of liste) {
    const node = app.graph?.getNodeById?.(p.nodeId) || null;
    const w = node?.widgets?.find((x) => x.name === p.widget) || null;
    const zeile = el("div", "k2-pin" + (w ? "" : " k2-pin-fehlt"));
    const name = el("div", "k2-pin-name");
    if (node) {
      name.append(el("b", null, node.title || node.type), " · " + (w?.label || p.widget));
    } else {
      name.textContent = p.label || p.widget;
    }
    name.title = name.textContent;
    const weg = el("button", "k2-pin-weg", "×");
    weg.type = "button";
    weg.title = uet("Lösen", "ui");
    weg.setAttribute("aria-label", weg.title + ": " + name.textContent);
    weg.onclick = () => setzePins(pins().filter((x) => pinSchluessel(x) !== pinSchluessel(p)));
    zeile.append(name, weg);
    if (w) zeile.append(steuerung(node, w));
    else zeile.append(el("div", "k2-pin-feld", node ? uet("Widget fehlt", "ui") : uet("Node entfernt", "ui")));
    box.append(zeile);
  }
  ziel.append(box);
}

const _packUi = {
  pasteOffen: false, pasteName: "", pasteJson: "", meldung: "", fehler: false,
  offen: "", editKey: "", editLabel: "", editPrompt: "", editGroup: "",
};

const _castUi = { liste: null, laden: false, speichernOffen: false, name: "", meldung: "", fehler: false };

async function ladeCharaktere() {
  if (_castUi.laden) return;
  _castUi.laden = true;
  try {
    const r = await fetch("/krea2/characters", { cache: "no-store" });
    const d = await r.json().catch(() => ({}));
    _castUi.liste = Array.isArray(d.characters) ? d.characters : [];
  } catch (e) {
    _castUi.liste = [];
  } finally {
    _castUi.laden = false;
    zeichneBald();
  }
}

function _aktiverLoRA() {
  for (const n of alleNodes()) {
    const cls = n?.comfyClass || "";
    if (cls !== "LoraLoaderModelOnly" && cls !== "LoraLoader") continue;
    if (n.mode === 2 || n.mode === 4) continue;
    const wName = n.widgets?.find((w) => w.name === "lora_name");
    const wStr = n.widgets?.find((w) => w.name === "strength_model");
    const val = String(wName?.value || "").trim();
    if (!val || val === "None") continue;
    return { name: val, strength: Number(wStr?.value ?? 1.0) };
  }
  return null;
}

function _setzeLoRA(lora) {
  if (!lora?.name) return;
  const n = alleNodes().find((x) => {
    const cls = x?.comfyClass || "";
    return (cls === "LoraLoaderModelOnly" || cls === "LoraLoader") && x.mode !== 2 && x.mode !== 4;
  });
  if (!n) return;
  const wName = n.widgets?.find((w) => w.name === "lora_name");
  const wStr = n.widgets?.find((w) => w.name === "strength_model");
  if (wName) {
    const vals = wName.options?.values;
    if (!Array.isArray(vals) || vals.includes(lora.name)) wName.value = lora.name;
  }
  if (wStr && typeof lora.strength === "number" && !Number.isNaN(lora.strength)) {
    wStr.value = lora.strength;
  }
  n.graph?.setDirtyCanvas?.(true, true);
  merkeFuerUndo();
}

function _slotZiele(serie, z, p2Ext, personNr) {
  if (personNr === 2) {
    const w2Ext = p2Ext ? eingangNode(p2Ext, "garderobe") : null;
    return {
      pNode: p2Ext || serie,
      pProp: p2Ext ? "personState" : "person2State",
      wNode: w2Ext || (!p2Ext ? serie : null),
      wProp: w2Ext ? "wardrobeState" : "wardrobe2State",
    };
  }
  return {
    pNode: z.person || serie,
    pProp: "personState",
    wNode: z.wardrobe || (!z.person ? serie : null),
    wProp: "wardrobeState",
  };
}

function _charakterKurz(personState) {
  const f = personState?.felder || {};
  const leer = _daten?.leer;
  const teile = [f.gender, f.age, f.hair, f.hairColor]
    .filter((x) => x && x !== leer)
    .map((x, idx) => uet(x, "person/" + ["gender", "age", "hair", "hairColor"][idx]));
  return teile.slice(0, 3).join(" · ");
}

function zeichneCharakterKarten(ziel, serie, z, p2Ext, personNr) {
  if (_castUi.liste === null && !_castUi.laden) ladeCharaktere();
  const bar = el("div", "k2-cast-bar");
  const kopf = el("div", "k2-cast-kopf");
  kopf.append(el("b", null, uet("Charakter-Karten", "ui")));
  const saveToggle = el("button", "k2-textknopf" + (_castUi.speichernOffen ? " k2-an" : ""),
    "+ " + uet("Karte speichern", "ui"));
  saveToggle.type = "button";
  saveToggle.onclick = () => {
    _castUi.speichernOffen = !_castUi.speichernOffen;
    _castUi.meldung = "";
    zeichne();
  };
  kopf.append(saveToggle);
  bar.append(kopf);

  const zieleSlot = _slotZiele(serie, z, p2Ext, personNr);

  if (_castUi.speichernOffen) {
    const form = el("div", "k2-cast-form");
    const inp = el("input", "k2-frei");
    inp.type = "text";
    inp.placeholder = uet("Name der Charakter-Karte …", "ui");
    inp.value = _castUi.name;
    inp.oninput = () => { _castUi.name = inp.value; };
    inp.onkeydown = (ev) => {
      ev.stopPropagation();
      if (ev.key === "Enter") saveDo.click();
    };
    const saveDo = el("button", "k2-textknopf k2-an", uet("Speichern", "ui"));
    saveDo.type = "button";
    saveDo.onclick = async () => {
      const name = _castUi.name.trim();
      if (!name) return;
      saveDo.disabled = true;
      try {
        const person = zieleSlot.pNode ? leseState(zieleSlot.pNode, zieleSlot.pProp, {}) : {};
        const wardrobe = zieleSlot.wNode ? leseState(zieleSlot.wNode, zieleSlot.wProp, {}) : {};
        const lora = personNr === 1 ? _aktiverLoRA() : null;
        const r = await fetch("/krea2/characters", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            summary: _charakterKurz(person),
            person,
            wardrobe,
            lora: lora || {},
          }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
        _castUi.liste = d.characters || [];
        _castUi.speichernOffen = false;
        _castUi.name = "";
        _castUi.fehler = false;
        _castUi.meldung = "";
        zeigeToast(uetf("Charakter-Karte gespeichert: {0}", "ui", d.name || name), "success");
        zeichne();
      } catch (err) {
        saveDo.disabled = false;
        _castUi.fehler = true;
        _castUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
        zeichne();
      }
    };
    form.append(inp, saveDo);
    bar.append(form);
  }

  const liste = _castUi.liste || [];
  if (liste.length) {
    const wrap = el("div", "k2-cast-liste");
    for (const c of liste) {
      const pill = el("div", "k2-cast-karte");
      const btn = el("button", "k2-cast-laden");
      btn.type = "button";
      btn.title = uetf("In Person {0} laden", "ui", personNr)
        + (c.lora?.name ? ` · LoRA: ${c.lora.name} (${c.lora.strength})` : "");
      btn.append(el("span", null, c.name));
      if (c.summary) btn.append(el("span", "k2-cast-sub", c.summary));
      if (c.lora?.name) {
        const b = el("span", "k2-cast-lora", "LoRA");
        b.title = `${c.lora.name} (${c.lora.strength})`;
        btn.append(b);
      }
      btn.onclick = () => {
        if (zieleSlot.pNode && c.person && Object.keys(c.person).length) {
          schreibeState(zieleSlot.pNode, zieleSlot.pProp, c.person);
        }
        if (zieleSlot.wNode && c.wardrobe && Object.keys(c.wardrobe).length) {
          schreibeState(zieleSlot.wNode, zieleSlot.wProp, c.wardrobe);
        }
        if (personNr === 1 && c.lora?.name) _setzeLoRA(c.lora);
        zeigeToast(uetf("Charakter-Karte „{0}“ in Person {1} geladen", "ui", c.name, personNr), "info");
        zeichne();
      };
      const weg = el("button", "k2-pin-weg", "×");
      weg.type = "button";
      weg.title = uetf("Charakter-Karte löschen: {0}", "ui", c.name);
      weg.onclick = async () => {
        weg.disabled = true;
        try {
          const r = await fetch("/krea2/characters/delete", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: c.name }),
          });
          const d = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
          _castUi.liste = d.characters || [];
          zeigeToast(uetf("Charakter-Karte gelöscht: {0}", "ui", c.name), "info");
          zeichne();
        } catch (err) {
          _castUi.fehler = true;
          _castUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
          zeichne();
        }
      };
      pill.append(btn, weg);
      wrap.append(pill);
    }
    bar.append(wrap);
  } else if (_castUi.liste !== null) {
    bar.append(el("div", "k2-studio-notiz", uet("Noch keine Charakter-Karten gespeichert.", "ui")));
  }
  if (_castUi.meldung) {
    bar.append(el("div", _castUi.fehler ? "k2-warn" : "k2-studio-notiz", _castUi.meldung));
  }
  ziel.append(bar);
}

function _parsePackJson(roh) {
  let s = String(roh || "").trim();
  const fence = s.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence) s = fence[1].trim();
  return JSON.parse(s);
}

function zeichneEigenePacks(ziel) {
  const box = el("div", "k2-studio-packs");
  ziel.append(box);

  const render = () => {
    box.textContent = "";
    box.append(el("div", "k2-studio-notiz",
      uet("Eigene Frisuren, Kleidung, Requisiten, Posen, Lichter und Looks als JSON-Dateien in user/krea2_presets/.", "ui")));

    const files = _daten?.custom?.files || [];
    if (files.length) {
      const liste = el("div", "k2-studio-packliste");
      for (const f of files) {
        const packBox = el("div", "k2-pack-box");
        const zeile = el("div", "k2-pack-kopf");
        const offen = _packUi.offen === f.file;
        const tog = el("button", "k2-pack-toggle", offen ? "▾" : "▸");
        tog.type = "button";
        tog.title = uet("Einträge anzeigen / bearbeiten", "ui");
        tog.onclick = () => {
          _packUi.offen = offen ? "" : f.file;
          _packUi.editKey = "";
          render();
        };
        const count = f.entries === 1 ? uet("1 Eintrag", "ui") : uetf("{0} Einträge", "ui", f.entries);
        const meta = count + (f.name && f.name !== f.file ? " · " + f.file : "");
        const titel = el("b", null, f.name || f.file);
        titel.onclick = () => tog.click();
        const span = el("span", "k2-pack-meta", meta);

        const diceLbl = el("label", "k2-pack-dice" + (f.dice ? " k2-an" : ""), "🎲");
        diceLbl.title = uet("In Zufalls-Pools einbeziehen", "ui");
        const diceInp = document.createElement("input");
        diceInp.type = "checkbox";
        diceInp.checked = !!f.dice;
        diceInp.onchange = async () => {
          try {
            const r = await fetch("/krea2/custom/update_pack", {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ file: f.file, dice: diceInp.checked }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
            _packUi.fehler = false;
            _packUi.meldung = "";
            await aktualisierePresets();
            zeichne();
          } catch (err) {
            _packUi.fehler = true;
            _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
            render();
          }
        };
        diceLbl.append(diceInp);

        const expBtn = el("button", "k2-pin-weg", "⇩");
        expBtn.type = "button";
        expBtn.title = uetf("Pack exportieren: {0}", "ui", f.file);
        expBtn.onclick = async () => {
          try {
            const r = await fetch("/krea2/custom/export?file=" + encodeURIComponent(f.file), { cache: "no-store" });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.pack) throw new Error(d.error || ("HTTP " + r.status));
            const blob = new Blob([JSON.stringify(d.pack, null, 2)], { type: "application/json" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = d.file || f.file;
            document.body.append(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
            zeigeToast(uetf("Pack exportiert: {0}", "ui", d.file || f.file), "success");
          } catch (err) {
            _packUi.fehler = true;
            _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
            render();
          }
        };

        const weg = el("button", "k2-pin-weg", "×");
        weg.type = "button";
        weg.title = uetf("Pack löschen: {0}", "ui", f.file);
        weg.setAttribute("aria-label", weg.title);
        weg.onclick = async () => {
          weg.disabled = true;
          try {
            const r = await fetch("/krea2/custom/delete", {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ file: f.file }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
            _packUi.fehler = false;
            _packUi.meldung = "";
            if (_packUi.offen === f.file) _packUi.offen = "";
            zeigeToast(uetf("Pack gelöscht: {0}", "ui", f.file), "info");
            await aktualisierePresets();
            zeichne();
          } catch (err) {
            weg.disabled = false;
            _packUi.fehler = true;
            _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
            render();
          }
        };
        zeile.append(tog, titel, span, diceLbl, expBtn, weg);
        packBox.append(zeile);

        if (offen && Array.isArray(f.items)) {
          const itemsBox = el("div", "k2-pack-items");
          for (const it of f.items) {
            const row = el("div", "k2-pack-item");
            const k = `${f.file}|${it.builder}|${it.field}|${it.label}`;
            const top = el("div", "k2-pack-item-top");
            top.append(
              el("span", "k2-pack-item-cat", `${it.builder}.${it.field}`),
              el("span", "k2-pack-item-lbl", it.label),
            );
            const spacer = el("span", "k2-pack-meta");
            top.append(spacer);
            const editBtn = el("button", "k2-pin-weg", "✎");
            editBtn.type = "button";
            editBtn.title = uet("Bearbeiten", "ui");
            editBtn.onclick = () => {
              if (_packUi.editKey === k) {
                _packUi.editKey = "";
              } else {
                _packUi.editKey = k;
                _packUi.editLabel = it.label;
                _packUi.editPrompt = it.prompt;
                _packUi.editGroup = it.group || "";
              }
              render();
            };
            const delItem = el("button", "k2-pin-weg", "×");
            delItem.type = "button";
            delItem.title = uet("Eintrag löschen", "ui");
            delItem.onclick = async () => {
              delItem.disabled = true;
              try {
                const r = await fetch("/krea2/custom/remove_entry", {
                  method: "POST", headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ builder: it.builder, field: it.field, label: it.label }),
                });
                const d = await r.json().catch(() => ({}));
                if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
                _packUi.editKey = "";
                await aktualisierePresets();
                zeichne();
              } catch (err) {
                delItem.disabled = false;
                _packUi.fehler = true;
                _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
                render();
              }
            };
            top.append(editBtn, delItem);
            row.append(top, el("div", "k2-pack-item-prm", it.prompt));

            if (_packUi.editKey === k) {
              const ed = el("div", "k2-pack-edit");
              const inL = el("input");
              inL.type = "text";
              inL.value = _packUi.editLabel;
              inL.placeholder = uet("Bezeichnung", "ui");
              inL.oninput = () => { _packUi.editLabel = inL.value; };
              inL.onkeydown = (ev) => ev.stopPropagation();

              const inP = el("textarea");
              inP.rows = 2;
              inP.value = _packUi.editPrompt;
              inP.placeholder = uet("Prompt (englisch)", "ui");
              inP.oninput = () => { _packUi.editPrompt = inP.value; };
              inP.onkeydown = (ev) => ev.stopPropagation();

              const inG = el("input");
              inG.type = "text";
              inG.value = _packUi.editGroup;
              inG.placeholder = uet("Familie (optional)", "ui");
              inG.oninput = () => { _packUi.editGroup = inG.value; };
              inG.onkeydown = (ev) => ev.stopPropagation();

              const btns = el("div", "k2-reihe");
              const okBtn = el("button", "k2-textknopf k2-an", uet("Speichern", "ui"));
              okBtn.type = "button";
              okBtn.onclick = async () => {
                okBtn.disabled = true;
                try {
                  const r = await fetch("/krea2/custom/update_pack", {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                      file: f.file,
                      builder: it.builder,
                      field: it.field,
                      old_label: it.label,
                      entry: {
                        label: _packUi.editLabel.trim(),
                        prompt: _packUi.editPrompt.trim(),
                        group: _packUi.editGroup.trim(),
                        hex: it.hex || "",
                      },
                    }),
                  });
                  const d = await r.json().catch(() => ({}));
                  if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
                  _packUi.editKey = "";
                  _packUi.fehler = false;
                  _packUi.meldung = (d.hints || []).join(" · ");
                  zeigeToast(uet("Eintrag gespeichert", "ui"), "success");
                  await aktualisierePresets();
                  zeichne();
                } catch (err) {
                  okBtn.disabled = false;
                  _packUi.fehler = true;
                  _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
                  render();
                }
              };
              const abbBtn = el("button", "k2-textknopf", uet("Abbrechen", "ui"));
              abbBtn.type = "button";
              abbBtn.onclick = () => { _packUi.editKey = ""; render(); };
              btns.append(okBtn, abbBtn);
              ed.append(inL, inP, inG, btns);
              row.append(ed);
            }
            itemsBox.append(row);
          }
          packBox.append(itemsBox);
        }
        liste.append(packBox);
      }
      box.append(liste);
    } else {
      box.append(el("div", "k2-studio-notiz", uet("Noch keine eigenen Vorgaben geladen.", "ui")));
    }

    const msgs = _daten?.custom?.messages || [];
    if (msgs.length) {
      const warn = el("div", "k2-warn", msgs.join(" · "));
      box.append(warn);
    }

    const fileInp = document.createElement("input");
    fileInp.type = "file";
    fileInp.accept = ".json,application/json";
    fileInp.style.display = "none";
    fileInp.onchange = async () => {
      const f = fileInp.files?.[0];
      fileInp.value = "";
      if (!f) return;
      try {
        const parsed = _parsePackJson(await f.text());
        const r = await fetch("/krea2/custom/import", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file: f.name, content: parsed, replace: true }),
        });
        const d = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
        _packUi.fehler = false;
        _packUi.meldung = (d.hints || []).join(" · ");
        zeigeToast(uet("Vorgaben-Pack importiert", "ui"), "success");
        await aktualisierePresets();
        zeichne();
      } catch (err) {
        _packUi.fehler = true;
        _packUi.meldung = err instanceof SyntaxError
          ? uet("Datei ist kein gültiges JSON", "ui")
          : uetf("Fehler: {0}", "ui", err?.message || err);
        render();
      }
    };

    const aktionen = el("div", "k2-reihe");
    aktionen.style.flexWrap = "wrap";
    const ladenBtn = el("button", "k2-textknopf", uet("JSON-Datei laden", "ui"));
    ladenBtn.type = "button";
    ladenBtn.onclick = () => fileInp.click();

    const pasteBtn = el("button", "k2-textknopf" + (_packUi.pasteOffen ? " k2-an" : ""), uet("JSON einfügen", "ui"));
    pasteBtn.type = "button";
    pasteBtn.onclick = () => {
      _packUi.pasteOffen = !_packUi.pasteOffen;
      _packUi.meldung = "";
      render();
    };

    const llmBtn = el("button", "k2-textknopf", uet("LLM-Prompt kopieren", "ui"));
    llmBtn.type = "button";
    llmBtn.onclick = async () => {
      llmBtn.disabled = true;
      try {
        const r = await fetch("/krea2/custom/llm_prompt", { cache: "no-store" });
        if (!r.ok) throw new Error("HTTP " + r.status);
        const ok = await kopiere(await r.text());
        _packUi.fehler = !ok;
        _packUi.meldung = ok
          ? uet("Kopiert.", "ui") + " " + uet("In ein beliebiges Chat-LLM einfügen und die Antwort unten einfügen.", "ui")
          : uet("Kopieren nicht möglich – „Prompt öffnen“ nutzen.", "ui");
        if (ok) {
          _packUi.pasteOffen = true;
          zeigeToast(uet("LLM-Prompt in Zwischenablage kopiert", "ui"), "success");
        }
      } catch (err) {
        _packUi.fehler = true;
        _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
      }
      render();
    };

    const reloadBtn = el("button", "k2-textknopf", uet("Neu laden", "ui"));
    reloadBtn.type = "button";
    reloadBtn.onclick = async () => {
      reloadBtn.disabled = true;
      try {
        const r = await fetch("/krea2/custom/reload", { method: "POST" });
        if (!r.ok) throw new Error("HTTP " + r.status);
        _packUi.fehler = false;
        _packUi.meldung = "";
        await aktualisierePresets();
        zeichne();
      } catch (err) {
        reloadBtn.disabled = false;
        _packUi.fehler = true;
        _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
        render();
      }
    };

    aktionen.append(fileInp, ladenBtn, pasteBtn, llmBtn, reloadBtn);
    box.append(aktionen);

    if (_packUi.pasteOffen) {
      const pasteBox = el("div", "k2-studio-packpaste");
      const nameInp = el("input", "k2-frei");
      nameInp.type = "text";
      nameInp.placeholder = uet("Name des Packs (z. B. 90s_fashion)", "ui");
      nameInp.value = _packUi.pasteName;
      nameInp.oninput = () => { _packUi.pasteName = nameInp.value; };
      nameInp.onkeydown = (ev) => ev.stopPropagation();

      const ta = el("textarea", "k2-studio-vorlage");
      ta.rows = 5;
      ta.placeholder = uet("JSON hier einfügen (photoshoot-presets/1)", "ui");
      ta.value = _packUi.pasteJson;
      ta.oninput = () => { _packUi.pasteJson = ta.value; };
      ta.onkeydown = (ev) => ev.stopPropagation();

      const pAktionen = el("div", "k2-reihe");
      const impBtn = el("button", "k2-textknopf k2-an", uet("Importieren", "ui"));
      impBtn.type = "button";
      impBtn.onclick = async () => {
        let parsed;
        try {
          parsed = _parsePackJson(ta.value);
        } catch (err) {
          _packUi.fehler = true;
          _packUi.meldung = uet("Datei ist kein gültiges JSON", "ui");
          render();
          return;
        }
        impBtn.disabled = true;
        try {
          const fname = nameInp.value.trim() || parsed?.name || "llm_pack";
          const r = await fetch("/krea2/custom/import", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ file: fname, content: parsed, replace: true }),
          });
          const d = await r.json().catch(() => ({}));
          if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
          _packUi.pasteOffen = false;
          _packUi.pasteName = "";
          _packUi.pasteJson = "";
          _packUi.fehler = false;
          _packUi.meldung = (d.hints || []).join(" · ");
          zeigeToast(uet("Vorgaben-Pack importiert", "ui"), "success");
          await aktualisierePresets();
          zeichne();
        } catch (err) {
          impBtn.disabled = false;
          _packUi.fehler = true;
          _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
          render();
        }
      };
      const abbBtn = el("button", "k2-textknopf", uet("Abbrechen", "ui"));
      abbBtn.type = "button";
      abbBtn.onclick = () => { _packUi.pasteOffen = false; _packUi.meldung = ""; render(); };
      pAktionen.append(impBtn, abbBtn);
      pasteBox.append(nameInp, ta, pAktionen);
      box.append(pasteBox);
    }

    if (_packUi.meldung) {
      box.append(el("div", _packUi.fehler ? "k2-warn" : "k2-studio-notiz", _packUi.meldung));
    }
  };
  render();
}

// ------------------------------------------------ Model profile switcher ---
function zeichneModellProfil(ziel, serie) {
  const wrap = el("div", "k2-studio-packs");
  if (!serie) {
    wrap.append(el("div", "k2-studio-notiz", uet("Kein Photoshoot-Node im Workflow", "ui")));
    ziel.append(wrap);
    return;
  }
  const render = () => {
    wrap.textContent = "";
    const shState = leseState(serie, "shootingState", _daten.shooting?.vorgabe || {});
    const profil = shState.modellProfil || "krea2";
    const profile = [
      ["krea2", "Krea 2 (Standard)", "Optimiert für Krea 2 – hält Kopf-Körper-Proportionen in Totale und Ganzkörper."],
      ["kompakt", "Kompakt (Flux / Qwen / SDXL)", "Kurze, modellneutrale Kamera-Angaben ohne proportionslastige Füllwörter."],
      ["eigen", "Eigene Kamera-Texte", "Überschreibt jede Kamera-Einstellung mit eigenem englischen Prompt-Text."],
    ];
    const tabs = el("div", "k2-modell-tabs");
    for (const [id, lbl] of profile) {
      const btn = el("button", "k2-textknopf" + (profil === id ? " k2-an" : ""), uet(lbl, "ui"));
      btn.type = "button";
      btn.onclick = () => {
        schreibeState(serie, "shootingState", { ...shState, modellProfil: id });
        render();
      };
      tabs.append(btn);
    }
    const beschreibung = profile.find(([id]) => id === profil)?.[2] || profile[0][2];
    wrap.append(tabs, el("div", "k2-studio-notiz", uet(beschreibung, "ui")));

    if (profil === "eigen") {
      const grid = el("div", "k2-modell-grid");
      const kTexte = { ...(shState.kameraTexte || {}) };
      for (const k of _daten.shooting?.kamera || []) {
        const z = el("label", "k2-modell-zeile");
        z.append(el("span", null, uet(k.label, "shooting/kamera")));
        const inp = el("input");
        inp.type = "text";
        inp.placeholder = k.wert;
        inp.value = kTexte[k.label] || "";
        inp.onchange = () => {
          const v = inp.value.trim();
          const neu = { ...(leseState(serie, "shootingState", _daten.shooting?.vorgabe || {}).kameraTexte || {}) };
          if (v) neu[k.label] = v;
          else delete neu[k.label];
          const akt = leseState(serie, "shootingState", _daten.shooting?.vorgabe || {});
          schreibeState(serie, "shootingState", { ...akt, modellProfil: "eigen", kameraTexte: neu });
        };
        inp.onkeydown = (ev) => ev.stopPropagation();
        z.append(inp);
        grid.append(z);
      }
      const rst = el("button", "k2-textknopf", uet("Kamera-Texte zurücksetzen", "ui"));
      rst.type = "button";
      rst.onclick = () => {
        const akt = leseState(serie, "shootingState", _daten.shooting?.vorgabe || {});
        schreibeState(serie, "shootingState", { ...akt, kameraTexte: {} });
        render();
      };
      wrap.append(grid, rst);
    }
  };
  render();
  ziel.append(wrap);
}

// ------------------------------------------------------ Wording lab (5b) ---
const _wlUi = {
  ziel: "location/ort",
  label: "",
  wortA: "",
  wortB: "",
  laeuft: false,
  meldung: "",
  fehler: false,
  status: "",
  reihen: [],
};
const _WL_SEEDS = [776610, 42];
const _WL_CLASS = {
  lighting: ["Krea2LightingBuilder", "LightingState"],
  style: ["Krea2StyleBuilder", "StyleState"],
  location: ["Krea2LocationBuilder", "LocationState"],
  pose: ["Krea2PoseBuilder", "PoseState"],
  ausdruck: ["Krea2ExpressionBuilder", "ExpressionState"],
};

function wortlaborFelder() {
  if (!_daten) return [];
  const liste = [];
  const pNamen = _daten.person?.namen || {};
  for (const cat of Object.keys(_daten.person?.felder || {})) {
    if (cat === "age" || cat === "gender" || cat === "type") continue;
    const base = pNamen[cat] || cat;
    const grp = (_daten.person?.outfitFelder || []).includes(cat) ? "Wardrobe" : "Person";
    liste.push({ id: `person/${cat}`, builder: "person", cat,
      text: `${uet(grp, "ui")} · ${uet(base, "person/felder", cat)}` });
  }
  const bNamen = {
    location: uet("Location", "ui"),
    lighting: uet("Lighting", "ui"),
    style: uet("Style", "ui"),
    pose: uet("Pose", "ui"),
    ausdruck: uet("Expression", "ui"),
  };
  for (const b of ["location", "lighting", "style", "pose", "ausdruck"]) {
    const sek = _daten[b];
    if (!sek) continue;
    for (const cat of (sek.reihenfolge || [])) {
      liste.push({ id: `${b}/${cat}`, builder: b, cat,
        text: `${bNamen[b]} · ${uet(cat, b + "/felder")}` });
    }
  }
  return liste;
}

function wortlaborKameraFuer(builder, cat) {
  if (builder === "ausdruck" || ["hair", "hairColor", "hairEffect", "headwear", "eyewear",
      "eyes", "eyeShape", "lipColor", "lipShape", "blush", "eyeshadow", "faceShape",
      "cheekbones", "nose", "chin", "jawline"].includes(cat)) return "Porträt";
  if (builder === "location" || ["shoes", "shoesColor", "bottom", "bottomColor", "hosiery",
      "hosieryColor", "beine", "haltung"].includes(cat)) return "Ganzkörper";
  return "Halbtotale";
}

function patcheProbeGraph(aus, builder, cat, wort, seed, laufTag) {
  const outfitFelder = new Set(_daten?.person?.outfitFelder || []);
  const istWardrobe = builder === "person" && outfitFelder.has(cat);
  for (const n of Object.values(aus)) {
    if (n.class_type === "SaveImage" && n.inputs) {
      n.inputs.filename_prefix = `photoshoot_wortlabor/${laufTag}`;
    }
    if (n.class_type === "Krea2Photoshooting" && n.inputs) {
      let st = {};
      try { st = JSON.parse(n.inputs.ShootingState || "{}"); } catch (e) { st = {}; }
      const kam = wortlaborKameraFuer(builder, cat);
      st = {
        ...st,
        kameras: [kam],
        festesFormat: "2:3",
        entwurf: true,
        serienSeed: seed,
        takes: {},
        _vorschau: true,
        _probe: { builder, cat, wort, seed },
        aktiv: { ...(st.aktiv || {}), kamera: true, format: false, rausch: false },
      };
      n.inputs.ShootingState = JSON.stringify(st);
      n.inputs.foto = 1;
    }
    if (builder === "person" && !istWardrobe && n.class_type === "Krea2PersonBuilder" && n.inputs) {
      let st = {};
      try { st = JSON.parse(n.inputs.PersonState || "{}"); } catch (e) { st = {}; }
      st.felder = { ...(st.felder || {}), [cat]: wort };
      n.inputs.PersonState = JSON.stringify(st);
    }
    if (istWardrobe && n.class_type === "Krea2Wardrobe" && n.inputs) {
      let st = {};
      try { st = JSON.parse(n.inputs.WardrobeState || "{}"); } catch (e) { st = {}; }
      const outfits = Array.isArray(st.outfits) && st.outfits.length
        ? st.outfits.map((o) => ({ ...o, felder: { ...(o.felder || {}) } }))
        : [{ id: "o1", name: "Lab", felder: {}, texte: {} }];
      const idx = Math.min(Math.max(0, parseInt(st.aktiv, 10) || 0), outfits.length - 1);
      outfits[idx].felder[cat] = wort;
      st.outfits = outfits;
      n.inputs.WardrobeState = JSON.stringify(st);
    }
    const cls = _WL_CLASS[builder];
    if (cls && n.class_type === cls[0] && n.inputs) {
      let st = {};
      try { st = JSON.parse(n.inputs[cls[1]] || "{}"); } catch (e) { st = {}; }
      if (builder === "location") {
        const saetze = Array.isArray(st.saetze) && st.saetze.length
          ? st.saetze.map((s) => ({ ...s, felder: { ...(s.felder || {}) } }))
          : [{ id: "s1", name: "", felder: {}, wuerfeln: {}, gruppe: "alle", details: "" }];
        const idx = Math.min(Math.max(0, parseInt(st.aktiv, 10) || 0), saetze.length - 1);
        saetze[idx].felder[cat] = wort;
        st.saetze = saetze;
      } else {
        st.felder = { ...(st.felder || {}), [cat]: wort };
        if (st.wuerfeln) delete st.wuerfeln[cat];
      }
      n.inputs[cls[1]] = JSON.stringify(st);
    }
  }
}

async function polleWortlaborBild(promptId) {
  for (let i = 0; i < 600; i++) {
    if (!wurzel?.isConnected) return null;
    const h = await fetch(`/history/${promptId}`, { cache: "no-store" });
    const e = h.ok ? (await h.json())[promptId] : null;
    if (e?.status?.completed !== undefined) {
      let bild = null;
      for (const a of Object.values(e.outputs || {})) {
        for (const b of a?.images || []) {
          if (!bild || (b.type === "output" && bild.type !== "output")) bild = b;
        }
      }
      return bild ? { filename: bild.filename, subfolder: bild.subfolder || "", type: bild.type || "output" } : null;
    }
    await new Promise((ok) => setTimeout(ok, 1200));
  }
  return null;
}

function zeichneWortlabor(ziel, serie) {
  const box = el("div", "k2-wl-box");
  ziel.append(box);
  const felder = wortlaborFelder();
  if (felder.length && !felder.some((f) => f.id === _wlUi.ziel)) _wlUi.ziel = felder[0].id;

  const render = () => {
    box.textContent = "";
    box.append(el("div", "k2-studio-notiz",
      uet("Testet Formulierungen auf 2 festen Seeds (Entwurf) gegen das nackte Wort – direkt im aktiven Workflow.", "ui")));

    const fZiel = el("label", "k2-wl-feld", uet("Feld", "ui"));
    const sel = el("select");
    for (const f of felder) {
      const o = el("option", null, f.text);
      o.value = f.id;
      sel.append(o);
    }
    sel.value = _wlUi.ziel;
    sel.disabled = _wlUi.laeuft;
    sel.onchange = () => { _wlUi.ziel = sel.value; };
    fZiel.append(sel);

    const fLbl = el("label", "k2-wl-feld", uet("Bezeichnung (dient auch als Kontrolle)", "ui"));
    const inpLbl = el("input");
    inpLbl.type = "text";
    inpLbl.placeholder = uet("z. B. Strohhut oder Altstadtgasse", "ui");
    inpLbl.value = _wlUi.label;
    inpLbl.disabled = _wlUi.laeuft;
    inpLbl.oninput = () => { _wlUi.label = inpLbl.value; };
    inpLbl.onkeydown = (ev) => ev.stopPropagation();
    fLbl.append(inpLbl);

    const fA = el("label", "k2-wl-feld", uet("Kandidat A (englischer Prompt)", "ui"));
    const inpA = el("textarea");
    inpA.rows = 2;
    inpA.placeholder = uet("z. B. a wide-brimmed woven straw sun hat", "ui");
    inpA.value = _wlUi.wortA;
    inpA.disabled = _wlUi.laeuft;
    inpA.oninput = () => { _wlUi.wortA = inpA.value; };
    inpA.onkeydown = (ev) => ev.stopPropagation();
    fA.append(inpA);

    const fB = el("label", "k2-wl-feld", uet("Kandidat B (optional)", "ui"));
    const inpB = el("textarea");
    inpB.rows = 2;
    inpB.placeholder = uet("zweite Formulierung zum direkten Vergleich", "ui");
    inpB.value = _wlUi.wortB;
    inpB.disabled = _wlUi.laeuft;
    inpB.oninput = () => { _wlUi.wortB = inpB.value; };
    inpB.onkeydown = (ev) => ev.stopPropagation();
    fB.append(inpB);

    const akt = el("div", "k2-reihe");
    const startBtn = el("button", "k2-textknopf k2-an",
      _wlUi.laeuft ? ("⏳ " + (_wlUi.status || uet("rendert …", "ui"))) : ("▶ " + uet("Auf 2 Seeds testen", "ui")));
    startBtn.type = "button";
    startBtn.disabled = _wlUi.laeuft;
    startBtn.onclick = async () => {
      const eintrag = felder.find((f) => f.id === _wlUi.ziel);
      const label = _wlUi.label.trim();
      const wortA = _wlUi.wortA.trim();
      const wortB = _wlUi.wortB.trim();
      if (!eintrag || !label || !wortA) {
        _wlUi.fehler = true;
        _wlUi.meldung = uet("Bitte Feld, Bezeichnung und Kandidat A ausfüllen.", "ui");
        render();
        return;
      }
      if (!serie) {
        _wlUi.fehler = true;
        _wlUi.meldung = uet("Kein Photoshoot-Node im Workflow", "ui");
        render();
        return;
      }
      _wlUi.laeuft = true;
      _wlUi.fehler = false;
      _wlUi.meldung = "";
      _wlUi.reihen = [
        { id: "a", titel: uet("Kandidat A", "ui"), wort: wortA, bilder: {}, gespeichert: false },
        ...(wortB ? [{ id: "b", titel: uet("Kandidat B", "ui"), wort: wortB, bilder: {}, gespeichert: false }] : []),
        { id: "k", titel: uet("Kontrolle", "ui"), wort: label, bilder: {}, gespeichert: false },
      ];
      _wlUi.status = uet("reiht ein …", "ui");
      render();
      try {
        const jobs = [];
        for (const r of _wlUi.reihen) {
          for (const seed of _WL_SEEDS) {
            const g = await app.graphToPrompt();
            const aus = structuredClone(g.output);
            patcheProbeGraph(aus, eintrag.builder, eintrag.cat, r.wort, seed, `wl_${Date.now()}_${r.id}_s${seed}`);
            const q = await api.queuePrompt(0, { output: aus, workflow: g.workflow });
            if (!q?.prompt_id) throw new Error(uet("Einreihen fehlgeschlagen", "ui"));
            jobs.push({ reihe: r, seed, promptId: q.prompt_id });
          }
        }
        let fertig = 0;
        _wlUi.status = `${fertig}/${jobs.length}`;
        render();
        await Promise.all(jobs.map(async (j) => {
          const bild = await polleWortlaborBild(j.promptId);
          j.reihe.bilder[j.seed] = bild;
          fertig++;
          _wlUi.status = `${fertig}/${jobs.length}`;
          render();
        }));
        _wlUi.meldung = uet("Fertig — Gewinner direkt als eigenen Eintrag speichern.", "ui");
        zeigeToast(uet("Wortlabor fertig — Gewinner speichern", "ui"), "success");
      } catch (err) {
        _wlUi.fehler = true;
        _wlUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
      } finally {
        _wlUi.laeuft = false;
        _wlUi.status = "";
        render();
      }
    };
    akt.append(startBtn);
    box.append(fZiel, fLbl, fA, fB, akt);

    if (_wlUi.meldung) {
      box.append(el("div", _wlUi.fehler ? "k2-warn" : "k2-studio-notiz", _wlUi.meldung));
    }
    if (_wlUi.reihen.length) {
      const eintrag = felder.find((f) => f.id === _wlUi.ziel);
      const gitterBox = el("div", "k2-wl-reihen");
      for (const r of _wlUi.reihen) {
        const karte = el("div", "k2-wl-reihe");
        const kopf = el("div", "k2-wl-kopf");
        kopf.append(el("b", null, r.titel));
        if (eintrag && _wlUi.label.trim()) {
          const saveBtn = el("button", "k2-textknopf" + (r.gespeichert ? " k2-an" : ""),
            r.gespeichert ? ("✓ " + uet("Gespeichert", "ui")) : ("+ " + uet("Als eigenen Eintrag speichern", "ui")));
          saveBtn.type = "button";
          saveBtn.disabled = _wlUi.laeuft || r.gespeichert;
          saveBtn.onclick = async () => {
            saveBtn.disabled = true;
            try {
              const resp = await fetch("/krea2/custom/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ builder: eintrag.builder, field: eintrag.cat,
                  label: _wlUi.label.trim(), prompt: r.wort }),
              });
              const d = await resp.json().catch(() => ({}));
              if (!resp.ok) throw new Error(d.error || ("HTTP " + resp.status));
              r.gespeichert = true;
              await aktualisierePresets();
              zeichne();
            } catch (err) {
              _wlUi.fehler = true;
              _wlUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
              render();
            }
          };
          kopf.append(saveBtn);
        }
        karte.append(kopf, el("div", "k2-wl-wort", r.wort));
        const g = el("div", "k2-wl-gitter");
        for (const seed of _WL_SEEDS) {
          const b = r.bilder[seed];
          if (b) {
            const a = el("a", "k2-wl-kachel");
            a.href = `/view?filename=${encodeURIComponent(b.filename)}&subfolder=${encodeURIComponent(b.subfolder || "")}&type=${encodeURIComponent(b.type || "output")}`;
            a.target = "_blank";
            a.rel = "noopener";
            const img = document.createElement("img");
            img.src = a.href + "&preview=webp;75";
            a.append(img, el("span", "k2-wl-seed", `Seed ${seed}`));
            g.append(a);
          } else {
            const d = el("div", "k2-wl-kachel");
            d.append(el("div", "k2-wl-warten", _wlUi.laeuft ? "…" : "—"), el("span", "k2-wl-seed", `Seed ${seed}`));
            g.append(d);
          }
        }
        karte.append(g);
        gitterBox.append(karte);
      }
      box.append(gitterBox);
    }
  };
  render();
}

// --------------------------------------------------------------- Drawing ---
function abbauen() {
  generation++;
  for (const g of griffe.splice(0)) {
    try { g.weg(); } catch (e) { /* already gone */ }
  }
}

function zeigeAufLeinwand(node) {
  try {
    app.canvas?.selectNode?.(node);
    app.canvas?.centerOnNode?.(node);
    app.graph?.setDirtyCanvas?.(true, true);
  } catch (e) {
    // an older canvas - nothing to show
  }
}

function auslagernAlsNode(serie, a, z, personNr = 1) {
  const info = _daten?.shoot?.abschnitte?.[a];
  const klasse = info?.klasse;
  const prop = personNr === 2
    ? (a === "person" ? "person2State" : a === "wardrobe" ? "wardrobe2State" : info?.prop)
    : info?.prop;
  const zielProp = info?.prop;
  if (!serie || !klasse) return;
  const join = promptJoinNode(serie);
  const eingaenge = _daten.shoot.eingaenge?.[a] || [];
  const joinEingang = join && eingaenge.find((e) => join.inputs?.some((i) => i.name === e));
  let neu = null;
  if (a === "person") {
    const eingang = personNr === 2 ? "person_2_data" : "person_data";
    neu = erzeugeUndVerbinde(klasse, serie, "person_data", eingang);
  } else if (a === "wardrobe") {
    const pEingang = personNr === 2 ? "person_2_data" : "person_data";
    let p = personNr === 2
      ? eingangNode(serie, "person_2_data")
      : (z.person && z.person !== serie ? z.person : null);
    if (!p) {
      const pk = _daten.shoot.abschnitte.person.klasse;
      const pp = personNr === 2 ? "person2State" : _daten.shoot.abschnitte.person.prop;
      const pz = _daten.shoot.abschnitte.person.prop;
      p = erzeugeUndVerbinde(pk, serie, "person_data", pEingang);
      if (p && p !== serie && serie.properties?.[pp] !== undefined) {
        p.properties = p.properties || {};
        p.properties[pz] = serie.properties[pp];
        delete serie.properties[pp];
        p._k2Zeichne?.();
      }
    }
    if (p && p !== serie) neu = erzeugeUndVerbinde(klasse, p, "garderobe", "garderobe");
  } else if (a === "location") {
    neu = erzeugeUndVerbinde(klasse, serie, "ort_data", "ort_data");
    const szFrei = !serie.outputs?.find((o) => o.name === "szene")?.links?.length;
    if (join && szFrei) verbindeNodes(serie, "szene", join, "szene");
  } else if (join && joinEingang) {
    neu = erzeugeUndVerbinde(klasse, join, joinEingang);
  } else {
    neu = globalThis.LiteGraph?.createNode?.(klasse) || null;
    if (neu) {
      neu.pos = [(serie.pos?.[0] ?? 420) - 390, (serie.pos?.[1] ?? 120)];
      (serie.graph || app.canvas?.graph || app.graph)?.add?.(neu);
    }
  }
  if (!neu) return;
  if (prop && serie.properties?.[prop] !== undefined) {
    neu.properties = neu.properties || {};
    neu.properties[zielProp || prop] = serie.properties[prop];
    delete serie.properties[prop];
  }
  neu._k2Zeichne?.();
  serie._k2Zeichne?.();
  merkeFuerUndo();
  zeichne();
}

function abschnittKopf(node, a, eingebettet, z, serie, personNr = 1) {
  const kopf = el("div", "k2-studio-titel");
  const klasse = _daten?.shoot?.abschnitte?.[a]?.klasse || node.comfyClass;
  const zusatz = personNr === 2 ? " 2" : "";
  if (eingebettet) {
    kopf.append(el("b", null, klassenName(klasse) + zusatz), el("span", "k2-studio-tag", uet("im Studio", "ui")));
    const aus = el("button", "k2-studio-hin", uet("↗ Als Node auf Leinwand", "ui"));
    aus.type = "button";
    aus.title = uet("Diesen Bereich als eigenen Node auf der Leinwand anlegen", "ui");
    aus.onclick = () => auslagernAlsNode(serie, a, z, personNr);
    kopf.append(aus);
  } else {
    kopf.append(el("b", null, (node.title || klassenName(node.comfyClass)) + (personNr === 2 && !node.title ? " 2" : "")), "#" + node.id);
    const hin = el("button", "k2-studio-hin", "◎ " + uet("Auf der Leinwand", "ui"));
    hin.type = "button";
    hin.title = uet("Den Node auf der Leinwand zeigen", "ui");
    hin.onclick = () => zeigeAufLeinwand(node);
    kopf.append(hin);
  }
  return kopf;
}

async function zeichnePanel(node, ziel, meine, klasse = node.comfyClass, opts = null) {
  const bauen = bauerFuer(klasse);
  if (!bauen) return;
  const griff = await bauen(node, ziel, opts);
  if (!griff) return;
  if (meine !== generation) griff.weg();
  else griffe.push(griff);
}

function zeichne() {
  if (!wurzel) return;
  css();
  abbauen();
  const meine = generation;
  wurzel.textContent = "";
  const liste = serien();
  const serie = aktuelleSerie();
  const z = zieleJetzt(serie);

  // --- head: brand, series, tabs --------------------------------------------
  const kopf = el("div", "k2-studio-kopf");
  kopf.append(markenleiste("Studio", serie ? (serie.title || klassenName(SERIE)) + " #" + serie.id : ""));
  if (liste.length > 1) {
    const reihe = el("label", "k2-studio-serie");
    reihe.append(uet("Serie", "ui"));
    const auswahl = el("select");
    for (const n of liste) {
      const opt = el("option", null, (n.title || klassenName(SERIE)) + " #" + n.id);
      opt.value = String(n.id);
      auswahl.append(opt);
    }
    auswahl.value = String(serie?.id);
    auswahl.onchange = () => {
      sicht.serieId = liste.find((n) => String(n.id) === auswahl.value)?.id ?? null;
      zeichne();
    };
    reihe.append(auswahl);
    kopf.append(reihe);
  }
  const reiter = el("div", "k2-studio-reiter");
  reiter.setAttribute("role", "tablist");
  for (const [k, name] of REITER) {
    const b = el("button", null, uet(name, "ui"));
    b.type = "button";
    b.setAttribute("role", "tab");
    b.setAttribute("aria-selected", String(sicht.reiter === k));
    b.onclick = () => {
      sicht.reiter = k;
      try { localStorage.setItem(MERK, k); } catch (e) { /* no storage */ }
      zeichne();
    };
    reiter.append(b);
  }
  kopf.append(reiter);
  wurzel.append(kopf);

  inhalt = el("div", "k2-studio-inhalt");
  inhalt.setAttribute("role", "tabpanel");
  wurzel.append(inhalt);

  if (!_daten) {
    inhalt.append(el("div", "k2-studio-fehlt",
      "⚠ Photoshoot: presets could not be loaded (/krea2/presets) — details in the console."));
    letzterStand = stand();
    return;
  }

  // --- the tab ----------------------------------------------------------------
  const abschnitte = REITER.find(([k]) => k === sicht.reiter)?.[2] || [];
  const p2Ext = serie ? eingangNode(serie, "person_2_data") : null;
  if (sicht.reiter === "person" && serie) {
    const shState = leseState(serie, "shootingState", _daten.shooting?.vorgabe || {});
    const pBar = el("div", "k2-studio-personen");
    const tabs = el("div", "k2-studio-ptabs");
    for (const [nr, lbl] of [[1, "Person 1"], [2, "Person 2"]]) {
      const btn = el("button", "k2-studio-pbtn", uet(lbl, "ui"));
      btn.type = "button";
      btn.setAttribute("aria-selected", String((sicht.personNr || 1) === nr));
      btn.onclick = () => { sicht.personNr = nr; zeichne(); };
      tabs.append(btn);
    }
    if (p2Ext) {
      tabs.append(el("span", "k2-studio-pcheck", uet("Person 2 verdrahtet", "ui")));
    } else {
      const lbl = el("label", "k2-studio-pcheck");
      const box = el("input");
      box.type = "checkbox";
      box.checked = !!shState.person2Aktiv;
      box.onchange = () => {
        schreibeState(serie, "shootingState", { ...shState, person2Aktiv: box.checked });
        zeichne();
      };
      lbl.append(box, uet("Zweite Person aktiv", "ui"));
      tabs.append(lbl);
    }
    pBar.append(tabs);
    if (p2Ext || shState.person2Aktiv) {
      const paar = el("label", "k2-studio-paar");
      paar.append(uet("Paar-Interaktion", "ui"));
      const sel = el("select");
      const opt0 = el("option", null, "—");
      opt0.value = "";
      sel.append(opt0);
      for (const e of _daten.shooting?.paarInteraktionen || []) {
        const opt = el("option", null, uet(e.label, "shooting/paarInteraktionen"));
        opt.value = e.label;
        sel.append(opt);
      }
      sel.value = shState.paarInteraktion || "";
      sel.onchange = () => schreibeState(serie, "shootingState", { ...shState, paarInteraktion: sel.value });
      paar.append(sel);
      pBar.append(paar);
    }
    inhalt.append(pBar);
    zeichneCharakterKarten(inhalt, serie, z, p2Ext, sicht.personNr || 1);
  }
  if (sicht.reiter === "pose" && !z.pose && !z.expression && z.series) {
    const box = el("div", "k2-studio-abschnitt");
    const hinweis = el("div", "k2-studio-fehlt");
    hinweis.append(el("div", null, uet("In diesem Workflow plant die Serie Pose und Ausdruck selbst.", "ui")));
    const knopf = el("button", "k2-studio-hin", uet("Im Reiter „Shoot“ öffnen →", "ui"));
    knopf.type = "button";
    knopf.onclick = () => {
      sicht.reiter = "shoot";
      try { localStorage.setItem(MERK, "shoot"); } catch (e) { /* no storage */ }
      zeichne();
    };
    hinweis.append(knopf);
    box.append(hinweis);
    inhalt.append(box);
  }
  const personNr = sicht.reiter === "person" && serie ? (sicht.personNr || 1) : 1;
  for (const a of abschnitte) {
    const box = el("div", "k2-studio-abschnitt");
    const klasse = _daten.shoot.abschnitte[a]?.klasse;
    let node = null;
    let eingebettet = false;
    let panelOpts = null;
    if (personNr === 2) {
      if (a === "person") {
        eingebettet = !p2Ext;
        node = p2Ext || serie;
        panelOpts = eingebettet ? { prop: "person2State", wardrobeProp: "wardrobe2State" } : null;
      } else if (a === "wardrobe") {
        const w2Ext = p2Ext ? eingangNode(p2Ext, "garderobe") : null;
        eingebettet = !p2Ext;
        node = w2Ext || (!p2Ext ? serie : null);
        panelOpts = eingebettet ? { prop: "wardrobe2State" } : null;
      }
    } else {
      eingebettet = !z[a] && EMBED.has(a) && !!serie;
      node = z[a] || (eingebettet ? serie : null);
    }
    const istIntern = node === serie && a !== "series";
    if (!node) {
      const fehlt = el("div", "k2-studio-fehlt k2-studio-fehlt-box");
      fehlt.append(el("span", null, a === "series"
        ? uet("Kein Photoshoot-Node im Workflow", "ui")
        : (personNr === 2 && a === "wardrobe"
          ? uet("Kein Wardrobe-Node an Person 2", "ui")
          : uetf("Kein {0}-Node an dieser Serie", "ui", klassenName(klasse)))));
      const join = a !== "series" && serie ? promptJoinNode(serie) : null;
      const eingaenge = _daten.shoot.eingaenge?.[a] || [];
      const joinEingang = join && eingaenge.find((e) => join.inputs?.some((i) => i.name === e));
      const kannBauen = a !== "series" && serie && klasse && (
        a === "person" || a === "wardrobe" || a === "location" || !!joinEingang
      );
      if (kannBauen) {
        const knopf = el("button", "k2-textknopf", uet("+ Anlegen & verbinden", "ui"));
        knopf.type = "button";
        knopf.onclick = () => {
          if (a === "person") {
            erzeugeUndVerbinde(klasse, serie, "person_data", personNr === 2 ? "person_2_data" : "person_data");
          } else if (a === "wardrobe") {
            const p = personNr === 2
              ? p2Ext
              : (z.person || erzeugeUndVerbinde(_daten.shoot.abschnitte.person.klasse,
                                                 serie, "person_data", "person_data"));
            if (p) erzeugeUndVerbinde(klasse, p, "garderobe", "garderobe");
          } else if (a === "location") {
            erzeugeUndVerbinde(klasse, serie, "ort_data", "ort_data");
            const szFrei = !serie.outputs?.find((o) => o.name === "szene")?.links?.length;
            if (join && szFrei) verbindeNodes(serie, "szene", join, "szene");
          } else if (join && joinEingang) {
            erzeugeUndVerbinde(klasse, join, joinEingang);
          }
          zeichne();
        };
        fehlt.append(knopf);
      }
      box.append(fehlt);
    } else {
      box.append(abschnittKopf(node, a, istIntern, z, serie, personNr));
      const ziel = el("div");
      box.append(ziel);
      zeichnePanel(node, ziel, meine, klasse, panelOpts);
      // Asked for by a compact node: into view once the panels above it
      // have drawn (they come in asynchronously).
      if (sicht.zeige != null && node.id === sicht.zeige && (!sicht.zeigeAbschnitt || sicht.zeigeAbschnitt === a)) {
        sicht.zeige = null;
        sicht.zeigeAbschnitt = null;
        const spalte = inhalt;
        setTimeout(() => {
          if (!box.isConnected) return;
          spalte.scrollTop += box.getBoundingClientRect().top - spalte.getBoundingClientRect().top - 10;
        }, 250);
      }
    }
    inhalt.append(box);
  }
  if (sicht.reiter === "look" && serie && (!z.template || z.template === serie)) {
    const box = el("div", "k2-studio-abschnitt");
    const titel = el("div", "k2-studio-titel");
    titel.append(el("b", null, uet("Prompt-Vorlage", "ui")), el("span", "k2-studio-tag", uet("im Studio", "ui")));
    const area = el("textarea", "k2-studio-vorlage");
    area.rows = 2;
    area.placeholder = STANDARD_VORLAGE;
    area.value = typeof serie.properties?.templateText === "string"
      ? serie.properties.templateText : STANDARD_VORLAGE;
    area.onchange = () => {
      serie.properties = serie.properties || {};
      serie.properties.templateText = area.value;
      serie.graph?.setDirtyCanvas?.(true, false);
      merkeFuerUndo();
    };
    area.onkeydown = (ev) => ev.stopPropagation();
    box.append(titel, area);
    inhalt.append(box);
  }

  if (sicht.reiter === "regie") {
    if (!serie) {
      inhalt.append(el("div", "k2-studio-fehlt", uet("Kein Photoshoot-Node im Workflow", "ui")));
    } else {
      const regie = el("div", "k2-studio-abschnitt");
      regieInto(serie, regie);
      inhalt.append(regie);
      // The shoot files row of the Series panel: saved shoots, file, Director.
      const dateien = el("div", "k2-studio-abschnitt");
      dateien.append(el("div", "k2-studio-titel", uet("Shooting-Dateien", "ui")));
      let zeile = null;
      const neu = () => {
        const z2 = shootZeile(serie, neu);
        if (zeile) zeile.replaceWith(z2);
        else dateien.append(z2);
        zeile = z2;
      };
      neu();
      // The list arrives later and redraws the Series node; this row follows.
      const folge = ansicht(serie, neu);
      griffe.push({ weg: () => folge.weg() });
      inhalt.append(dateien);
    }
  }

  if (sicht.reiter === "setup") {
    const box = el("div", "k2-studio-abschnitt");
    box.append(el("div", "k2-studio-titel", uet("Angeheftet", "ui")));
    zeichnePins(box);
    inhalt.append(box);

    const packsBox = el("div", "k2-studio-abschnitt");
    packsBox.append(el("div", "k2-studio-titel", uet("Eigene Vorgaben", "ui")));
    zeichneEigenePacks(packsBox);
    inhalt.append(packsBox);

    const modBox = el("div", "k2-studio-abschnitt");
    modBox.append(el("div", "k2-studio-titel", uet("Modell-Profil", "ui")));
    zeichneModellProfil(modBox, serie);
    inhalt.append(modBox);

    const wlBox = el("div", "k2-studio-abschnitt");
    wlBox.append(el("div", "k2-studio-titel", uet("Wortlabor", "ui")));
    zeichneWortlabor(wlBox, serie);
    inhalt.append(wlBox);
  }
  letzterStand = stand();
}

// What the column shows, as a string: the series, the nodes wired to it (as
// objects - undo replaces them) and, on the setup tab, the pins with their
// live values. Checked on a timer while the tab is open; a change draws the
// column again, never while something in it has the focus for typing.
function stand() {
  const serie = aktuelleSerie();
  const z = zieleJetzt(serie);
  const p2 = serie ? eingangNode(serie, "person_2_data") : null;
  const w2 = p2 ? eingangNode(p2, "garderobe") : null;
  const teile = [sicht.reiter, sicht.personNr, serien().map((n) => n.id + ":" + objNr(n)).join(","), serie?.id,
                 Object.entries(z).map(([a, n]) => a + ":" + objNr(n)).join(","),
                 objNr(p2) + ":" + objNr(w2)];
  if (sicht.reiter === "setup") {
    for (const p of pins()) {
      const node = app.graph?.getNodeById?.(p.nodeId);
      const w = node?.widgets?.find((x) => x.name === p.widget);
      teile.push(pinSchluessel(p) + "=" + objNr(node) + ":" + (node?.title || "") + ":" + JSON.stringify(w?.value ?? null));
    }
    teile.push("packs=" + JSON.stringify((_daten?.custom?.files || []).map((f) => [f.file, f.dice, f.entries])));
    teile.push("modell=" + JSON.stringify(serie ? leseState(serie, "shootingState", {}).modellProfil || "krea2" : ""));
  }
  return teile.join("|");
}

let geplant = 0;
function zeichneBald() {
  if (geplant || !wurzel?.isConnected) return;
  geplant = requestAnimationFrame(() => {
    geplant = 0;
    zeichne();
  });
}

function schaue() {
  if (!wurzel?.isConnected) return;
  const f = document.activeElement;
  if (f && wurzel.contains(f) && f.matches?.("input, textarea, select")) return;
  if (stand() !== letzterStand) zeichne();
}

// ------------------------------------------------------------ Placement ---
function holeWurzel() {
  if (wurzel) return wurzel;
  css();
  wurzel = el("div", "k2-studio");
  wurzel.setAttribute("aria-label", "Photoshoot Studio");
  return wurzel;
}

const TAB = {
  id: TAB_ID,
  icon: "k2-icon-logo",
  title: "Photoshoot Studio",
  tooltip: "Photoshoot Studio",
  // The label under the icon: "Photoshoot" is one letter too wide for the
  // bar and breaks in two.
  label: "Studio",
  type: "custom",
  // ComfyUI calls render() whenever it mounts the tab, possibly more than
  // once with the same element; one root is moved in and drawn again.
  render(element) {
    element.style.height = "100%";
    element.style.minHeight = "0";
    const w = holeWurzel();
    if (w.parentElement !== element) element.append(w);
    // Opened on a selected Series node: that one - unless a node's "edit"
    // opened it, which chose its own series.
    const sel = gewaehlteSerie();
    if (sel && !_vonNode) sicht.serieId = sel.id;
    _vonNode = false;
    if (!ticker) ticker = setInterval(schaue, 700);
    ladePresets().then((d) => {
      _daten = d;
      zeichne();
    });
  },
  destroy() {
    clearInterval(ticker);
    ticker = 0;
    abbauen();
    wurzel?.remove();
  },
};

// ------------------------------------------------ Opened from a node ---
// A compact node's summary and its "edit" (shared.mjs, oeffneStudio()): the
// tab that shows the node's section, for the series it belongs to - the
// same ziele() the column draws from. False when that cannot be: no sidebar
// in this front end, presets not in yet, or a node wired to no series (the
// column would only say so); the node then expands inline instead.
function tabDa() {
  try {
    return (app.extensionManager?.getSidebarTabs?.() || []).some((t) => t.id === TAB_ID);
  } catch (e) {
    return false;
  }
}

function oeffneFuer(node, wunschAbschnitt = null) {
  const leiste = app.extensionManager?.sidebarTab;
  if (!_daten?.shoot || !tabDa() || typeof leiste?.toggleSidebarTab !== "function") return false;
  let serie = null;
  let abschnitt = wunschAbschnitt;
  if (node?.comfyClass === SERIE) {
    serie = node;
    abschnitt ||= "series";
  } else {
    for (const s of serien()) {
      const z = zieleJetzt(s);
      abschnitt ||= Object.keys(z).find((a) => z[a] === node && (node !== s || a === "series")) || null;
      if (z[abschnitt] === node || (wunschAbschnitt && EMBED.has(wunschAbschnitt) && node === s)) {
        serie = s;
        break;
      }
    }
  }
  const reiter = abschnitt && REITER.find(([, , a]) => a.includes(abschnitt))?.[0];
  if (!serie || !reiter) return false;
  sicht.serieId = serie.id;
  sicht.reiter = reiter;
  sicht.zeige = node.id;
  sicht.zeigeAbschnitt = wunschAbschnitt;
  try { localStorage.setItem(MERK, reiter); } catch (e) { /* no storage */ }
  if (leiste.activeSidebarTabId === TAB_ID && wurzel?.isConnected) {
    zeichne();
  } else {
    _vonNode = true;
    leiste.toggleSidebarTab(TAB_ID);
  }
  return true;
}

// Every Photoshoot node of the graph on the canvas (a subgraph when one is
// open) compact or full, as one undo step.
function alleAnsicht(kompakt) {
  const graph = app.canvas?.graph || app.graph;
  setzeAnsicht((graph?._nodes || graph?.nodes || []).filter((n) => n?._k2Kompakt), kompakt);
}

function starteAktiveSerie() {
  const serie = aktuelleSerie();
  if (!serie?._k2Starten) {
    zeigeToast(uet("Kein Photoshoot-Node im Workflow", "ui"), "warn");
    return;
  }
  serie._k2Starten();
}

function schalteAktivenEntwurf() {
  const serie = aktuelleSerie();
  if (!serie?._k2SchalteEntwurf) {
    zeigeToast(uet("Kein Photoshoot-Node im Workflow", "ui"), "warn");
    return;
  }
  const an = serie._k2SchalteEntwurf();
  zeigeToast(uet(an ? "Entwurf: AN" : "Entwurf: AUS", "ui"), "info");
}

const _gebundeneGraphen = new WeakSet();

function _graphNodes(g) {
  return g?._nodes || g?.nodes || [];
}

function hatPhotoshootNodes() {
  const pruefe = (g) => _graphNodes(g).some(
    (n) => typeof n?.comfyClass === "string" && n.comfyClass.startsWith("Krea2") && n.comfyClass !== "Krea2Monochrome",
  );
  return pruefe(app.canvas?.graph) || (app.graph !== app.canvas?.graph && pruefe(app.graph));
}

function hatSerieNode() {
  const pruefe = (g) => _graphNodes(g).some((n) => n?.comfyClass === SERIE);
  return pruefe(app.canvas?.graph) || (app.graph !== app.canvas?.graph && pruefe(app.graph));
}

function aktualisiereLeiste() {
  const root = document.documentElement;
  if (!root) return;
  root.classList.toggle("k2-hat-photoshoot", hatPhotoshootNodes());
  root.classList.toggle("k2-hat-serie", hatSerieNode());
}

function bindeGraph(g) {
  if (!g || _gebundeneGraphen.has(g)) return;
  _gebundeneGraphen.add(g);
  const ev = g.events;
  if (ev?.addEventListener) {
    const neu = () => queueMicrotask(aktualisiereLeiste);
    ev.addEventListener("node:added", neu);
    ev.addEventListener("node:removed", neu);
    ev.addEventListener("configured", neu);
  }
}

// -------------------------------------------------------- Registration ---
app.registerExtension({
  name: "Krea2.Studio",

  // In the command palette and bindable to keys.
  commands: [
    { id: "Photoshoot.ToggleStudio", label: "Photoshoot: Toggle Studio", icon: "k2-icon-logo",
      function: () => app.extensionManager?.sidebarTab?.toggleSidebarTab?.(TAB_ID) },
    { id: "Photoshoot.StartShooting", label: "Photoshoot: Start shooting", icon: "k2-icon-shoot",
      function: () => starteAktiveSerie() },
    { id: "Photoshoot.ToggleDraft", label: "Photoshoot: Toggle Draft mode", icon: "pi pi-bolt",
      function: () => schalteAktivenEntwurf() },
    { id: "Photoshoot.CompactAll", label: "Photoshoot: Compact all", icon: "pi pi-window-minimize",
      function: () => alleAnsicht(true) },
    { id: "Photoshoot.ExpandAll", label: "Photoshoot: Expand all", icon: "pi pi-window-maximize",
      function: () => alleAnsicht(false) },
  ],

  keybindings: [
    { combo: { alt: true, shift: true, key: "p" }, commandId: "Photoshoot.ToggleStudio" },
    { combo: { alt: true, shift: true, key: "s" }, commandId: "Photoshoot.StartShooting" },
    { combo: { alt: true, shift: true, key: "d" }, commandId: "Photoshoot.ToggleDraft" },
  ],

  get actionBarButtons() {
    const modus = einstellung("Photoshoot.ActionBarButtons", "Photoshoot workflows (Studio + Shoot)");
    // Read reactive workflow refs so tab/subgraph switches re-sync visibility.
    void app.extensionManager?.workflow?.activeWorkflow;
    void app.extensionManager?.workflow?.activeSubgraph;
    if (modus === "Off") return [];
    const nurPs = modus.startsWith("Photoshoot workflows");
    const mitShoot = !modus.includes("Studio only");
    if (nurPs) queueMicrotask(aktualisiereLeiste);
    const basis = nurPs ? "k2-ab-btn k2-ab-auto" : "k2-ab-btn";
    const knoepfe = [{
      icon: "k2-icon-logo",
      label: "Studio",
      tooltip: "Photoshoot Studio (Alt+Shift+P)",
      class: basis,
      onClick: () => app.extensionManager?.sidebarTab?.toggleSidebarTab?.(TAB_ID),
    }];
    if (mitShoot) {
      knoepfe.push({
        icon: "k2-icon-shoot",
        label: "Shoot",
        tooltip: "Photoshoot: Start shooting (Alt+Shift+S)",
        class: nurPs ? "k2-ab-btn k2-ab-auto k2-ab-serie" : "k2-ab-btn",
        onClick: () => starteAktiveSerie(),
      });
    }
    return knoepfe;
  },

  afterConfigureGraph() {
    bindeGraph(app.graph);
    bindeGraph(app.canvas?.graph);
    aktualisiereLeiste();
    queueMicrotask(aktualisiereLeiste);
    if (!einstellung("Photoshoot.AutoOpenStudio", false)) return;
    if (!serien().length) return;
    const leiste = app.extensionManager?.sidebarTab;
    if (tabDa() && leiste?.activeSidebarTabId !== TAB_ID) {
      leiste?.toggleSidebarTab?.(TAB_ID);
    }
  },

  nodeCreated(node) {
    bindeGraph(node?.graph);
    if (typeof node?.comfyClass === "string" && node.comfyClass.startsWith("Krea2")) {
      aktualisiereLeiste();
      beimEntfernen(node, () => queueMicrotask(aktualisiereLeiste));
    }
  },

  setup() {
    css();
    // The extension key "sidebarTabs" is not read by the front ends this is
    // tested against (1.47, 1.53); the workspace's call is.
    try {
      const em = app.extensionManager;
      const da = (em?.getSidebarTabs?.() || []).some((t) => t.id === TAB_ID);
      if (!da) em?.registerSidebarTab?.(TAB);
    } catch (e) {
      console.warn("[Photoshoot] Studio sidebar not available:", e);
    }
    bindeGraph(app.graph);
    bindeGraph(app.canvas?.graph);
    aktualisiereLeiste();
    try {
      app.extensionManager?.workflow?.onUserActivation?.(() => {
        bindeGraph(app.graph);
        bindeGraph(app.canvas?.graph);
        aktualisiereLeiste();
        queueMicrotask(aktualisiereLeiste);
      });
    } catch (e) { /* older frontend */ }
    registriereStudioOeffner(oeffneFuer);
    ladePresets().then((d) => { if (d) _daten = d; });
  },

  // Right-click on any node: pin one of its widgets to "Your setup". One
  // entry with a submenu of the node's widgets; a pinned one is ticked and
  // unpins.
  getNodeMenuItems(node) {
    const widgets = anheftbar(node);
    if (!widgets.length) return [];
    return [null, {
      content: uet("An Photoshoot Studio anheften", "ui"),
      has_submenu: true,
      submenu: {
        options: widgets.map((w) => ({
          content: (istAngeheftet(node, w) ? "✓ " : "") + (w.label || w.name),
          callback: () => schaltePin(node, w),
        })),
      },
    }];
  },
});
