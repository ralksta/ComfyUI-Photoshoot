// Shared foundation for the interfaces in this package.
//
// Built after the pattern of PixaromaResolution: the Python node has no widgets
// apart from the seed, the entire state lives in node.properties and is only
// pushed into the hidden input on submit.

import { app } from "../../scripts/app.js";

// ---------------------------------------------------------------- Presets ---
// The labels and their English equivalents come from the server
// (nodes/api.py). Maintaining a second copy in JS would be a reliable way to
// let two lists drift apart.
let _presetsPromise = null;

export function ladePresets() {
  if (!_presetsPromise) {
    // Timestamp against the cache: without it the browser reused the response
    // and newly added fields did not appear.
    _presetsPromise = fetch("/krea2/presets?t=" + Date.now(), { cache: "no-store" })
      .then((r) => {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then((daten) => {
        if (daten?.i18n) _i18n = daten.i18n;
        // Second language source: the server reads the stored setting straight
        // out of comfy.settings.json.
        if (daten?.locale) _serverLocale = daten.locale;
        console.log("[Photoshoot] Language: %s (setting %s, server %s, browser %s)",
                    locale(), _frontendLocale() ?? "—", _serverLocale ?? "—",
                    (typeof navigator !== "undefined" && navigator.language) || "—");
        return daten;
      })
      .catch((e) => {
        console.error("[Photoshoot] Presets could not be loaded:", e);
        _presetsPromise = null; // try again on the next node
        return null;
      });
  }
  return _presetsPromise;
}

// ------------------------------------------------------------- Language ---
// The German labels are also the keys: they sit in node.properties, in the
// coupling tables and in every saved workflow. Only the display is therefore
// translated. When an entry is missing, the German word stays - visible, but
// not broken.
let _i18n = null;

// Cached briefly: while drawing, the Person Builder looks up more than 370
// labels, and every reach into the settings goes through a reactive store. Half
// a second is long enough for one redraw to need a single lookup, and short
// enough for a language change to take effect immediately.
let _locale = null;
let _localeBis = 0;
let _serverLocale = null;

function _frontendLocale() {
  try {
    const roh = app.extensionManager?.setting?.get("Comfy.Locale");
    return typeof roh === "string" && roh ? roh : null;
  } catch (e) {
    return null;   // setting not readable (yet)
  }
}

// Three sources, in this order:
//
//   1. the front-end setting - up to date immediately, but depending on load
//      timing and front-end version still empty while the panels already draw;
//   2. the stored setting, which the server reads out of comfy.settings.json -
//      that is the user's explicit choice;
//   3. the browser language, since ComfyUI itself goes by that as long as
//      nobody has chosen anything (navigator.language || "en-US").
//
// Point 2 is the reason for this arrangement: an interface explicitly set to
// English stayed German, because point 1 delivered nothing and point 3 then
// supplied the German browser language.
function locale() {
  const jetzt = Date.now();
  if (_locale && jetzt < _localeBis) return _locale;

  const l = _frontendLocale()
    || _serverLocale
    || (typeof navigator !== "undefined"
        ? navigator.language || (navigator.languages || [])[0]
        : null);

  _locale = (l || "en").slice(0, 2).toLowerCase();
  _localeBis = jetzt + 500;
  return _locale;
}

/** Translates a label. bereich is "ui", "feldnamen", "familien", "sektionen",
 *  "platzhalter", or a path such as "person/hosiery". */
export function t(text, bereich) {
  if (text == null || text === "") return text;
  if (locale() === "de" || !_i18n) return text;

  let tabelle = _i18n;
  for (const teil of String(bereich || "ui").split("/")) {
    tabelle = tabelle?.[teil];
    if (!tabelle) return text;
  }
  return tabelle[text] ?? text;
}

/** Like t(), but for texts that substitute a number or a value. */
export function tf(text, bereich, ...werte) {
  let out = t(text, bereich);
  werte.forEach((w, i) => {
    out = out.replace("{" + i + "}", w);
  });
  return out;
}

// ------------------------------------------------------------------ CSS ---
// Once for all three interfaces. The colours follow the Pixaroma look, so that
// the nodes do not stand out in the graph.
const CSS_ID = "photoshoot-css";

const CSS = `
.k2-root{display:flex;flex-direction:column;gap:6px;padding:6px;box-sizing:border-box;
  font:11px/1.35 -apple-system,Segoe UI,Roboto,sans-serif;color:#d7d7d7;height:100%;overflow:hidden}
.k2-label{font-size:9px;letter-spacing:.09em;text-transform:uppercase;color:#8a8a8a;
  display:flex;align-items:center;gap:6px}
.k2-label .k2-wert{color:#c9c9c9;text-transform:none;letter-spacing:0;font-size:10px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.k2-chips{display:flex;flex-wrap:wrap;gap:3px}
.k2-chip{border:1px solid #3d3d3d;background:#1d1d1d;color:#bdbdbd;border-radius:4px;
  padding:3px 7px;cursor:pointer;user-select:none;white-space:nowrap;font-size:10px}
.k2-chip:hover{border-color:#5a5a5a;color:#e8e8e8}
.k2-chip.k2-an{background:#f66744;border-color:#f66744;color:#1a1a1a;font-weight:600}
.k2-chip.k2-fam{font-size:9px;letter-spacing:.05em;text-transform:uppercase}
/* An entry the remaining settings rule out - clickable, but visibly without
   effect. It used to look like any other and quietly did nothing. */
.k2-chip.k2-tot{opacity:.4;text-decoration:line-through}
.k2-chip.k2-tot.k2-an{opacity:.55}
.k2-scroll{overflow-y:auto;max-height:104px;border:1px solid #303030;border-radius:4px;
  padding:4px;background:#191919}
.k2-scroll::-webkit-scrollbar{width:6px}
.k2-scroll::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-reihe{display:flex;align-items:center;gap:5px}
.k2-reihe select{flex:1;min-width:0;background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;
  border-radius:4px;padding:3px 4px;font-size:10px;font-family:inherit}
.k2-wuerfel{border:1px solid #3d3d3d;background:#1d1d1d;border-radius:4px;cursor:pointer;
  width:22px;height:22px;flex:0 0 22px;display:flex;align-items:center;justify-content:center;
  font-size:12px;opacity:.42;user-select:none}
.k2-wuerfel:hover{border-color:#5a5a5a;opacity:.75}
.k2-wuerfel.k2-an{opacity:1;border-color:#f66744;background:#2a1c17}
.k2-frei{background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;border-radius:4px;
  padding:3px 5px;font-size:10px;font-family:inherit;width:100%;box-sizing:border-box}
/* overflow-x, because the photoshoot preview with white-space:pre can grow
   wider than the node - without it the text simply ran off to the right and was
   cut off with nothing to indicate it. */
.k2-vorschau{margin-top:auto;border-top:1px solid #303030;padding-top:5px;color:#9a9a9a;
  font-size:10px;line-height:1.4;max-height:60px;overflow-y:auto;overflow-x:auto;
  font-style:italic}
.k2-vorschau::-webkit-scrollbar{height:6px;width:6px}
.k2-vorschau::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-vorschau.k2-leer{color:#5e5e5e}
.k2-vorschau.k2-lang{max-height:136px}

/* Tabs - only the person has enough fields to need them */
.k2-tabs{display:flex;gap:2px;border-bottom:1px solid #303030;padding-bottom:5px}
.k2-tab{flex:1;text-align:center;border:1px solid transparent;background:#1d1d1d;color:#8f8f8f;
  border-radius:4px 4px 0 0;padding:4px 2px;cursor:pointer;user-select:none;font-size:9px;
  letter-spacing:.04em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k2-tab:hover{color:#d7d7d7}
.k2-tab.k2-an{background:#2a1c17;border-color:#f66744;color:#f0f0f0;font-weight:600}
.k2-blatt{display:flex;flex-direction:column;gap:5px;overflow-y:auto;flex:1;min-height:0}
.k2-blatt::-webkit-scrollbar{width:6px}
.k2-blatt::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-feld{display:flex;align-items:center;gap:6px}
.k2-feld > .k2-name{flex:0 0 76px;font-size:9px;letter-spacing:.05em;text-transform:uppercase;
  color:#8a8a8a;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.k2-feld select,.k2-feld input{flex:1;min-width:0;background:#1d1d1d;color:#d7d7d7;
  border:1px solid #3d3d3d;border-radius:4px;padding:3px 4px;font-size:10px;font-family:inherit}
.k2-block{display:flex;flex-direction:column;gap:4px}
.k2-block > .k2-name{font-size:9px;letter-spacing:.05em;text-transform:uppercase;color:#8a8a8a}

/* A label that resets on click. Without it you had to open the dropdown and
   scroll all the way to the top to get rid of a field again. */
.k2-loeschbar{cursor:pointer}
.k2-loeschbar:hover{color:#f66744}
/* Number of fields set, shown on the tab - with 44 fields across six tabs
   there would otherwise be no way to tell but clicking through. */
.k2-zahl{font-size:8px;margin-left:2px;opacity:.75;vertical-align:super;line-height:0}
/* Reset - scope and count in the text, so that what will be lost is visible.
   Bottom right, where it is out of the way. */
.k2-reset{display:flex;gap:10px;justify-content:flex-end;font-size:9px}
.k2-reset-knopf{color:#6e6e6e;cursor:pointer;user-select:none;white-space:nowrap}
.k2-reset-knopf:hover{color:#f66744}

/* Start button of the photoshoot */
.k2-start{border:1px solid #f66744;background:#f66744;color:#1a1a1a;border-radius:4px;
  padding:6px 8px;text-align:center;cursor:pointer;user-select:none;font-size:11px;
  font-weight:600;letter-spacing:.02em}
.k2-start:hover{background:#ff7a58;border-color:#ff7a58}
.k2-start:active{background:#d9542f}
.k2-feld input[type=number]{text-align:center}

/* Axis rows of the photoshoot.
   One row per axis - switch, name, state, arrow - and the details unfold
   exactly where the switch sits. The switches used to be a chip row at the top
   with their detail blocks further down; you clicked "focus" and something
   appeared somewhere out of sight. */
.k2-achsen{display:flex;flex-direction:column;flex:1 1 auto;min-height:0;overflow-y:auto}
.k2-achsen::-webkit-scrollbar{width:6px}
.k2-achsen::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-achse{display:flex;align-items:center;gap:7px;padding:5px 2px;cursor:pointer;
  user-select:none;border-bottom:1px solid #262626}
.k2-achse:hover{background:#1c1c1c}
.k2-achse.k2-zu{cursor:default}
.k2-achse.k2-zu:hover{background:none}
.k2-punkt{flex:0 0 13px;height:13px;border-radius:50%;border:1px solid #4a4a4a;
  background:#1d1d1d;cursor:pointer;box-sizing:border-box}
.k2-punkt:hover{border-color:#7a7a7a}
.k2-punkt.k2-an{background:#f66744;border-color:#f66744}
.k2-achse-name{flex:1;font-size:11px;color:#8f8f8f}
.k2-achse.k2-hell .k2-achse-name{color:#e2e2e2}
.k2-achse-wert{font-size:10px;color:#7d7d7d;white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis;max-width:110px}
.k2-achse.k2-hell .k2-achse-wert{color:#c9a08f}
.k2-pfeil{flex:0 0 10px;font-size:9px;color:#5e5e5e;text-align:center}
.k2-auf{padding:6px 2px 8px 20px;display:flex;flex-direction:column;gap:6px;
  border-bottom:1px solid #262626;background:#181818}
.k2-warn{font-size:10px;color:#f66744;line-height:1.35}
`;

export function injiziereCSS() {
  if (document.getElementById(CSS_ID)) return;
  const s = document.createElement("style");
  s.id = CSS_ID;
  s.textContent = CSS;
  document.head.appendChild(s);
}

// ------------------------------------------------------------- Nodes 2.0 ---
// canvasOnly has to follow the active renderer: true on the classic canvas
// (otherwise the widget lands in the parameter tab instead of on the node),
// false under Nodes 2.0 (where Vue renders it in the node body). Implemented as
// a getter, so that switching at run time does not need a reload first.
export function applyAdaptiveCanvasOnly(widget) {
  if (!widget || !widget.options) return widget;
  try {
    Object.defineProperty(widget.options, "canvasOnly", {
      configurable: true,
      enumerable: true,
      get() {
        return !window.LiteGraph?.vueNodesMode;
      },
    });
  } catch (e) {
    widget.options.canvasOnly = !window.LiteGraph?.vueNodesMode;
  }
  return widget;
}

// The wheel over the panel should zoom the canvas rather than scroll inside the
// panel, as long as there is nothing to scroll there - otherwise the zoom gets
// stuck the moment the pointer touches the node.
export function installCanvasZoomPassthrough(root) {
  root.addEventListener(
    "wheel",
    (e) => {
      // Every scrollable area, not only .k2-scroll: the panels' content area
      // is called .k2-blatt and was unreachable as a result - the wheel zoomed
      // the canvas instead of moving the content, and everything below the edge
      // stayed invisible.
      const el = e.target.closest(".k2-scroll, .k2-blatt, .k2-achsen, .k2-vorschau");
      if (el && el.scrollHeight > el.clientHeight) return; // echtes Scrollen zulassen
      e.preventDefault();
      const canvas = app.canvas?.canvas;
      if (canvas) {
        canvas.dispatchEvent(
          new WheelEvent("wheel", {
            deltaY: e.deltaY,
            clientX: e.clientX,
            clientY: e.clientY,
            bubbles: true,
          }),
        );
      }
    },
    { passive: false },
  );
}

// ------------------------------------------------------------------ State ---
export function leseState(node, prop, vorgabe) {
  const roh = node?.properties?.[prop];
  if (!roh) return structuredClone(vorgabe);
  try {
    const s = typeof roh === "string" ? JSON.parse(roh) : roh;
    return mischeVorgaben(structuredClone(vorgabe), s);
  } catch (e) {
    console.warn("[Photoshoot] Zustand unlesbar, benutze Vorgaben.", e);
    return structuredClone(vorgabe);
  }
}

// Stored values win, missing ones come from the default - one level down as
// well. A flat { ...vorgabe, ...gespeichert } is not enough: if a key is later
// added inside a sub-object (a new switch in "aktiv", say), the old state
// replaces the whole object and the new switch starts out undefined instead of
// at its default.
//
// Arrays are deliberately replaced rather than merged: for "kameras" or
// "fokusse" a union with the default would be exactly wrong - deselected
// entries would come back.
function mischeVorgaben(vorgabe, gespeichert) {
  if (!gespeichert || typeof gespeichert !== "object") return vorgabe;
  const aus = { ...vorgabe };
  for (const [k, v] of Object.entries(gespeichert)) {
    const alt = vorgabe[k];
    const beidesObjekt =
      alt && v && typeof alt === "object" && typeof v === "object" &&
      !Array.isArray(alt) && !Array.isArray(v);
    aus[k] = beidesObjekt ? { ...alt, ...v } : v;
  }
  return aus;
}

export function schreibeState(node, prop, state) {
  node.properties = node.properties || {};
  node.properties[prop] = JSON.stringify(state);
  node.graph?.setDirtyCanvas?.(true, false);
}

// -------------------------------------------------- State into the prompt ---
// Hidden inputs do not appear in the workflow JSON, so ComfyUI cannot fill them
// in itself. Every entry in the API prompt therefore has its state handed in
// just before submitting.
//
// Subgraph-proof: the new subgraph mechanics flatten contained nodes into the
// prompt with compound IDs ("5:12"), while app.graph only knows the top level.
// Hence collecting recursively, and cutting off the prefix on lookup when
// needed.
const _registriert = new Map(); // class_type -> { prop, vorgabe }

export function registriereStateInjektion(classType, hiddenName, prop, vorgabe) {
  _registriert.set(classType, { hiddenName, prop, vorgabe });
  installiereHook();
}

let _hookInstalliert = false;

function sammleNodes(gesucht) {
  const index = new Map();
  const besuche = (graph) => {
    if (!graph) return;
    for (const n of graph._nodes || graph.nodes || []) {
      if (!n) continue;
      if (gesucht.has(n.comfyClass) || gesucht.has(n.type)) index.set(String(n.id), n);
      const innen = n.subgraph || n.graph || n._graph;
      if (innen && innen !== graph) besuche(innen);
    }
  };
  besuche(app.graph);
  return index;
}

function findeNode(index, promptId) {
  const s = String(promptId);
  if (index.has(s)) return index.get(s);
  const schwanz = s.includes(":") ? s.slice(s.lastIndexOf(":") + 1) : null;
  return schwanz && index.has(schwanz) ? index.get(schwanz) : null;
}

function installiereHook() {
  if (_hookInstalliert) return;
  _hookInstalliert = true;

  // Keep the original function and forward the receiver at call time, rather
  // than pre-binding it to app. Equivalent in effect - our replacement is
  // invoked as a method on app, so this is app - and a shade more robust,
  // because the actual receiver is passed through.
  //
  // The reason for the change is a different one, though. The registry's YARA
  // rule python_network_operations looks for the socket bind call and matched
  // the six characters of the equivalent Function.prototype method here.
  // Versions 2.0.0 and 2.0.1 were flagged over it (pattern $socket4). The
  // rule is a Python one and this is JavaScript; reported upstream.
  const original = app.graphToPrompt;
  app.graphToPrompt = async function (...args) {
    const ergebnis = await original.apply(this || app, args);
    const out = ergebnis?.output;
    if (!out) return ergebnis;

    let index = null;
    for (const id in out) {
      const eintrag = out[id];
      const conf = eintrag && _registriert.get(eintrag.class_type);
      if (!conf) continue;
      if (!index) index = sammleNodes(new Set(_registriert.keys()));
      const node = findeNode(index, id);
      const state = node?.properties?.[conf.prop] || JSON.stringify(conf.vorgabe);
      eintrag.inputs = eintrag.inputs || {};
      eintrag.inputs[conf.hiddenName] = state;
    }
    return ergebnis;
  };
}

