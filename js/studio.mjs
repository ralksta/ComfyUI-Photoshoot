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
  erzeugeUndVerbinde,
  injiziereCSS,
  kopiere,
  ladePresets,
  markenleiste,
  merkeFuerUndo,
  promptJoinNode,
  registriereStudioOeffner,
  setzeAnsicht,
  verbindeNodes,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.9.0";
import { regieInto, shootZeile, ziele } from "./regie.mjs?v=2.9.0";
import { oeffneLightbox } from "./lightbox.mjs?v=2.9.0";

import { app } from "../../scripts/app.js";

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
const sicht = { serieId: null, reiter: "person", zeige: null, zeigeAbschnitt: null };
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

const _packUi = { pasteOffen: false, pasteName: "", pasteJson: "", meldung: "", fehler: false };

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
        const zeile = el("div", "k2-studio-pack");
        const count = f.entries === 1 ? uet("1 Eintrag", "ui") : uetf("{0} Einträge", "ui", f.entries);
        const meta = count + (f.name && f.name !== f.file ? " · " + f.file : "");
        zeile.append(el("b", null, f.name || f.file), el("span", null, meta));
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
            await aktualisierePresets();
            zeichne();
          } catch (err) {
            weg.disabled = false;
            _packUi.fehler = true;
            _packUi.meldung = uetf("Fehler: {0}", "ui", err?.message || err);
            render();
          }
        };
        zeile.append(weg);
        liste.append(zeile);
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
        if (ok) _packUi.pasteOffen = true;
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

function auslagernAlsNode(serie, a, z) {
  const info = _daten?.shoot?.abschnitte?.[a];
  const klasse = info?.klasse;
  const prop = info?.prop;
  if (!serie || !klasse) return;
  const join = promptJoinNode(serie);
  const eingaenge = _daten.shoot.eingaenge?.[a] || [];
  const joinEingang = join && eingaenge.find((e) => join.inputs?.some((i) => i.name === e));
  let neu = null;
  if (a === "person") {
    neu = erzeugeUndVerbinde(klasse, serie, "person_data", "person_data");
  } else if (a === "wardrobe") {
    let p = z.person && z.person !== serie ? z.person : null;
    if (!p) {
      const pk = _daten.shoot.abschnitte.person.klasse;
      const pp = _daten.shoot.abschnitte.person.prop;
      p = erzeugeUndVerbinde(pk, serie, "person_data", "person_data");
      if (p && p !== serie && serie.properties?.[pp] !== undefined) {
        p.properties = p.properties || {};
        p.properties[pp] = serie.properties[pp];
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
    neu.properties[prop] = serie.properties[prop];
    delete serie.properties[prop];
  }
  neu._k2Zeichne?.();
  serie._k2Zeichne?.();
  merkeFuerUndo();
  zeichne();
}

function abschnittKopf(node, a, eingebettet, z, serie) {
  const kopf = el("div", "k2-studio-titel");
  const klasse = _daten?.shoot?.abschnitte?.[a]?.klasse || node.comfyClass;
  if (eingebettet) {
    kopf.append(el("b", null, klassenName(klasse)), el("span", "k2-studio-tag", uet("im Studio", "ui")));
    const aus = el("button", "k2-studio-hin", uet("↗ Als Node auf Leinwand", "ui"));
    aus.type = "button";
    aus.title = uet("Diesen Bereich als eigenen Node auf der Leinwand anlegen", "ui");
    aus.onclick = () => auslagernAlsNode(serie, a, z);
    kopf.append(aus);
  } else {
    kopf.append(el("b", null, node.title || klassenName(node.comfyClass)), "#" + node.id);
    const hin = el("button", "k2-studio-hin", "◎ " + uet("Auf der Leinwand", "ui"));
    hin.type = "button";
    hin.title = uet("Den Node auf der Leinwand zeigen", "ui");
    hin.onclick = () => zeigeAufLeinwand(node);
    kopf.append(hin);
  }
  return kopf;
}

async function zeichnePanel(node, ziel, meine, klasse = node.comfyClass) {
  const bauen = bauerFuer(klasse);
  if (!bauen) return;
  const griff = await bauen(node, ziel);
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
  for (const a of abschnitte) {
    const box = el("div", "k2-studio-abschnitt");
    const klasse = _daten.shoot.abschnitte[a]?.klasse;
    const eingebettet = !z[a] && EMBED.has(a) && !!serie;
    const node = z[a] || (eingebettet ? serie : null);
    const istIntern = node === serie && a !== "series";
    if (!node) {
      const fehlt = el("div", "k2-studio-fehlt k2-studio-fehlt-box");
      fehlt.append(el("span", null, a === "series"
        ? uet("Kein Photoshoot-Node im Workflow", "ui")
        : uetf("Kein {0}-Node an dieser Serie", "ui", klassenName(klasse))));
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
            erzeugeUndVerbinde(klasse, serie, "person_data", "person_data");
          } else if (a === "wardrobe") {
            const p = z.person || erzeugeUndVerbinde(_daten.shoot.abschnitte.person.klasse,
                                                     serie, "person_data", "person_data");
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
      box.append(abschnittKopf(node, a, istIntern, z, serie));
      const ziel = el("div");
      box.append(ziel);
      zeichnePanel(node, ziel, meine, klasse);
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
  const teile = [sicht.reiter, serien().map((n) => n.id + ":" + objNr(n)).join(","), serie?.id,
                 Object.entries(z).map(([a, n]) => a + ":" + objNr(n)).join(",")];
  if (sicht.reiter === "setup") {
    for (const p of pins()) {
      const node = app.graph?.getNodeById?.(p.nodeId);
      const w = node?.widgets?.find((x) => x.name === p.widget);
      teile.push(pinSchluessel(p) + "=" + objNr(node) + ":" + (node?.title || "") + ":" + JSON.stringify(w?.value ?? null));
    }
    teile.push("packs=" + (_daten?.custom?.count ?? 0) + ":" + (_daten?.custom?.files || []).length);
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
  icon: "pi pi-camera",
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

// -------------------------------------------------------- Registration ---
app.registerExtension({
  name: "Krea2.Studio",

  // In the command palette and bindable to keys.
  commands: [
    { id: "Photoshoot.CompactAll", label: "Photoshoot: Compact all", icon: "pi pi-window-minimize",
      function: () => alleAnsicht(true) },
    { id: "Photoshoot.ExpandAll", label: "Photoshoot: Expand all", icon: "pi pi-window-maximize",
      function: () => alleAnsicht(false) },
  ],

  setup() {
    // The extension key "sidebarTabs" is not read by the front ends this is
    // tested against (1.47, 1.53); the workspace's call is.
    try {
      const em = app.extensionManager;
      const da = (em?.getSidebarTabs?.() || []).some((t) => t.id === TAB_ID);
      if (!da) em?.registerSidebarTab?.(TAB);
    } catch (e) {
      console.warn("[Photoshoot] Studio sidebar not available:", e);
    }
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
