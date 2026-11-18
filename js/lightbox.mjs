// The Lightbox: the Series' contact sheet, big.
//
// A review view in ComfyUI's bottom panel - or, on a front end without one,
// and on request, a full-screen overlay: one photo at a time, filters,
// compare, a filmstrip, and the actions of the contact sheet. It keeps no plan
// and no pictures of its own. Every Series node hands it an object with its
// photos and actions (meldeSerie() from baue() in shooting.mjs); whatever the
// Lightbox does goes through that object into the node's state, so the
// contact sheet and the Lightbox always show the same series, undo covers
// both, and each redraws when the other changes something (the node's
// zeichne() calls serieGeaendert()).
//
// What the Lightbox looks at - which node, which photo, the filter, compare -
// is view, not setting: none of it goes into the node's state.

import { injiziereCSS, kopiere, ladePresets, t as uet, tf as uetf } from "./shared.mjs?v=2.9.0";

import { app } from "../../scripts/app.js";

const TAB_ID = "photoshoot-lightbox";
const BEFEHL = "Photoshoot.OpenLightbox";
const CSS_ID = "photoshoot-lightbox-css";

// The pack's dark panels, the accent of the start button. Sized for the
// bottom panel, whose height the user drags: the stage takes what is left.
const CSS = `
.k2-bogen-titel{display:flex;align-items:center;gap:6px}
.k2-bogen-kopf .k2-lb-auf{text-transform:none;letter-spacing:0;font-size:9.5px;padding:0 6px;line-height:15px}
.k2-lb{--lb-bg:#141414;--lb-panel:#1f1f1f;--lb-panel2:#282828;--lb-line:#343434;--lb-line2:#444;
  --lb-fg:#e9e7e4;--lb-muted:#9b9894;--lb-faint:#6d6a66;--lb-accent:#f66744;--lb-soft:#3a221b;
  width:100%;height:100%;min-height:0;box-sizing:border-box;display:grid;
  grid-template-columns:minmax(0,1fr) clamp(210px,26%,300px);
  grid-template-rows:auto minmax(0,1fr) auto auto;background:var(--lb-bg);color:var(--lb-fg);
  font:12.5px/1.45 -apple-system,"Segoe UI",Roboto,sans-serif;outline:none;overflow:hidden;position:relative}
.k2-lb *{box-sizing:border-box}
.k2-lb:focus-visible{box-shadow:inset 0 0 0 1px var(--lb-accent)}
.k2-lb button{font:inherit;color:inherit}
.k2-lb-filter{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:5px;align-items:center;padding:7px 12px;
  border-bottom:1px solid var(--lb-line);background:var(--lb-panel)}
.k2-lb-label{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--lb-faint);font-weight:600;
  margin-right:4px}
.k2-lb-trenn{width:1px;height:16px;background:var(--lb-line2);margin:0 3px}
.k2-lb-chip{display:inline-flex;align-items:center;gap:6px;background:var(--lb-panel2);border:1px solid var(--lb-line);
  border-radius:999px;padding:3px 10px;font-size:12px;color:var(--lb-muted);cursor:pointer;white-space:nowrap}
.k2-lb-chip:hover{border-color:var(--lb-line2);color:var(--lb-fg)}
.k2-lb-chip.k2-an{background:var(--lb-soft);border-color:var(--lb-accent);color:#f7d5ca}
.k2-lb-chip .k2-lb-n{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--lb-faint)}
.k2-lb-chip.k2-an .k2-lb-n{color:#f7d5ca}
.k2-lb-rechts{margin-left:auto;display:flex;gap:6px;align-items:center}
.k2-lb-rechts select{background:var(--lb-panel2);color:var(--lb-fg);border:1px solid var(--lb-line2);border-radius:6px;
  padding:3px 6px;font:inherit;font-size:12px;max-width:220px}
.k2-lb-knopf{display:inline-flex;align-items:center;gap:7px;background:var(--lb-panel2);border:1px solid var(--lb-line2);
  border-radius:7px;padding:5px 11px;font-size:12.5px;cursor:pointer;text-decoration:none;white-space:nowrap;
  color:var(--lb-fg)}
.k2-lb-knopf:hover:not(:disabled){border-color:#5a5a5a}
.k2-lb-knopf:disabled{opacity:.4;cursor:default}
.k2-lb-knopf:focus-visible,.k2-lb-chip:focus-visible,.k2-lb-klein:focus-visible,.k2-lb-pfeil:focus-visible{
  outline:2px solid var(--lb-accent);outline-offset:1px}
.k2-lb-knopf kbd{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:var(--lb-faint);
  border:1px solid var(--lb-line2);border-radius:4px;padding:0 4px}
.k2-lb-knopf.k2-an{border-color:var(--lb-accent);color:#f7d5ca;background:var(--lb-soft)}
.k2-lb-knopf.k2-rot.k2-an{border-color:#c85a5a;background:#361c1c;color:#f0c4c4}
.k2-lb-knopf.k2-haupt{background:var(--lb-accent);border-color:var(--lb-accent);color:#1a1210;font-weight:600}
.k2-lb-knopf.k2-haupt:hover:not(:disabled){background:#ff7a58;border-color:#ff7a58}
.k2-lb-buehne{grid-column:1;grid-row:2;position:relative;min-height:120px;background:#0e0e0e;display:flex;
  gap:12px;padding:12px 58px;touch-action:pan-y}
.k2-lb-fig{margin:0;flex:1;min-width:0;display:flex;flex-direction:column;gap:6px;align-items:center}
.k2-lb-rahmen{position:relative;flex:1;min-height:0;width:100%}
.k2-lb-rahmen img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:block}
.k2-lb-ab .k2-lb-rahmen img{cursor:pointer}
.k2-lb-platz{position:absolute;inset:0;margin:auto;max-width:100%;max-height:100%;height:100%;
  border:1.5px dashed var(--lb-line2);border-radius:4px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:4px;color:var(--lb-faint);font-size:12px;text-align:center;padding:8px}
.k2-lb-platz b{color:var(--lb-muted);font-weight:500}
.k2-lb-leer{margin:auto;color:var(--lb-muted);font-size:13px;text-align:center;max-width:46ch}
.k2-lb-fig figcaption{font-size:12px;color:var(--lb-muted);display:flex;gap:6px;align-items:center;flex-wrap:wrap;
  justify-content:center}
.k2-lb-marken{position:absolute;left:66px;top:18px;display:flex;gap:6px;z-index:1;pointer-events:none}
.k2-lb-marke{font-family:ui-monospace,Menlo,monospace;font-size:12px;background:#000b;border-radius:5px;padding:2px 7px;
  color:var(--lb-fg)}
.k2-lb-fig .k2-lb-marke{background:var(--lb-panel2)}
.k2-lb-marke.k2-fav{color:var(--lb-accent)} .k2-lb-marke.k2-rej{color:#f0a0a0} .k2-lb-marke.k2-draft{color:#e7c77d}
.k2-lb-pfeil{position:absolute;top:50%;transform:translateY(-50%);width:36px;height:36px;border-radius:50%;
  background:#000a;border:1px solid var(--lb-line2);cursor:pointer;display:grid;place-items:center;font-size:18px;
  line-height:1;z-index:1}
.k2-lb-pfeil:hover{border-color:var(--lb-accent)}
.k2-lb-pfeil.k2-l{left:12px}.k2-lb-pfeil.k2-r{right:12px}
.k2-lb-info{grid-column:2;grid-row:2/4;border-left:1px solid var(--lb-line);background:var(--lb-panel);padding:12px;
  display:flex;flex-direction:column;gap:12px;overflow:auto;min-height:0}
.k2-lb-info::-webkit-scrollbar,.k2-lb-streifen::-webkit-scrollbar{width:6px;height:6px}
.k2-lb-info::-webkit-scrollbar-thumb,.k2-lb-streifen::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-lb-dl{display:grid;grid-template-columns:auto 1fr;gap:5px 12px;margin:0;font-size:12.5px}
.k2-lb-dl dt{color:var(--lb-faint);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;padding-top:2px}
.k2-lb-dl dd{margin:0;min-width:0;overflow-wrap:anywhere}
.k2-lb-mono{font-family:ui-monospace,Menlo,monospace;font-size:11.5px}
.k2-lb-takes{display:flex;flex-wrap:wrap;gap:4px}
.k2-lb-takes .k2-lb-chip{padding:2px 8px}
.k2-lb-takes .k2-lb-chip span::first-letter{text-transform:uppercase}
.k2-lb-aktionen{display:flex;flex-wrap:wrap;gap:6px}
.k2-lb-prompt summary{cursor:pointer;color:var(--lb-muted);font-size:12px}
.k2-lb-prompt p{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#cfcac4;background:var(--lb-bg);
  border:1px solid var(--lb-line);border-radius:6px;padding:8px;margin:8px 0 6px;white-space:pre-wrap;
  user-select:text;cursor:text}
.k2-lb-notiz{color:var(--lb-faint);font-size:12px}
.k2-lb-streifen{grid-column:1;grid-row:3;display:flex;gap:6px;overflow-x:auto;padding:8px 12px;
  border-top:1px solid var(--lb-line);background:var(--lb-panel);align-items:flex-end;min-height:84px}
.k2-lb-klein{position:relative;flex:none;border:2px solid transparent;border-radius:5px;cursor:pointer;background:none;
  padding:0;height:66px}
.k2-lb-klein img{height:100%;display:block;border-radius:3px}
.k2-lb-klein.k2-an{border-color:var(--lb-accent)}
.k2-lb-klein.k2-rej img{opacity:.35}
.k2-lb-klein.k2-draft img{outline:1.5px dashed #e7c77d;outline-offset:-3px}
.k2-lb-klein .k2-lb-nr{position:absolute;left:4px;top:3px;font-family:ui-monospace,Menlo,monospace;font-size:10px;
  background:#000a;border-radius:3px;padding:0 3px;color:var(--lb-fg)}
.k2-lb-klein .k2-lb-h{position:absolute;right:4px;top:2px;color:var(--lb-accent);font-size:12px}
.k2-lb-klein.k2-geplant{border:1.5px dashed var(--lb-line2);display:flex;align-items:flex-end;justify-content:center;
  font-size:9.5px;color:var(--lb-faint);text-align:center;padding:3px;line-height:1.15;width:auto;min-width:40px}
.k2-lb-klein.k2-geplant.k2-an{border-color:var(--lb-accent);border-style:dashed}
.k2-lb-klein.k2-rendert{border-color:var(--lb-accent);box-shadow:0 0 8px rgba(246,103,68,.75)}
.k2-lb-knopf.k2-stopp{border-color:#a8483c;color:#f0a89e;background:#2c1714}
.k2-lb-knopf.k2-stopp:hover{border-color:var(--lb-accent);color:#ffd0c8;background:#3a1d19}
.k2-lb-klein.k2-geplant .k2-lb-nr{background:none;color:var(--lb-muted)}
.k2-lb-fuss{grid-column:1/-1;grid-row:4;display:flex;flex-wrap:wrap;gap:10px;align-items:center;
  justify-content:space-between;padding:7px 12px;border-top:1px solid var(--lb-line);background:var(--lb-panel2);
  font-size:12.5px}
.k2-lb-fuss .k2-lb-stand{display:flex;gap:10px;align-items:center;flex-wrap:wrap;min-width:0}
.k2-lb-meldung{color:#8fc58a;font-size:12px}
.k2-lb-meldung.k2-warn{color:var(--lb-accent)}
.k2-lb-overlay{position:fixed;inset:0;z-index:3000;background:rgba(0,0,0,.82);padding:18px;display:flex}
.k2-lb-overlay > .k2-lb{border:1px solid var(--lb-line);border-radius:10px}
.k2-lb-schmal{grid-template-columns:minmax(0,1fr)}
.k2-lb-schmal .k2-lb-info{display:none}
`;

function injiziereLightboxCSS() {
  injiziereCSS();
  if (document.getElementById(CSS_ID)) return;
  const s = document.createElement("style");
  s.id = CSS_ID;
  s.textContent = CSS;
  document.head.appendChild(s);
}

// ------------------------------------------------------------ Registry ---
// node id -> what baue() in shooting.mjs hands over. Undo reloads the graph
// and builds every node anew under the same id, so the Lightbox holds the id,
// never the node, and finds the new object here.
const serien = new Map();

export function meldeSerie(serie) {
  injiziereLightboxCSS();
  serien.set(serie.node.id, serie);
  zeichneBald();
}

export function meldeAb(serie) {
  if (serien.get(serie.node.id) === serie) serien.delete(serie.node.id);
  zeichneBald();
}

export function serieGeaendert(id) {
  if (id === angezeigt) zeichneBald();
}

// ---------------------------------------------------------------- View ---
const sicht = {
  id: null,            // the Series node it was opened from
  nr: null,            // the photo on the stage
  filter: "alle",      // "alle" | "fav" | "rej" | "entwurf" | a framing label
  vergleich: false,    // compare: the photo next to the next one
  promptOffen: false,
  meldung: null,       // { text, warn } - the last action's answer, in the footer
};
let angezeigt = null;  // node id actually drawn (the remembered one, or a fallback)
let wurzel = null;
let panelEl = null;    // the bottom panel's element while the tab is mounted
let overlay = null;
let fokusGewuenscht = false;
let geplantRAF = 0;
let letzterStand = null; // what the last drawing showed, for the keys
let kopiert = null;

const lebende = () => [...serien.values()].filter((s) => s.node.graph);

function aktuelleSerie() {
  const s = serien.get(sicht.id);
  if (s?.node.graph) return s;
  // While undo rebuilds the node, or after it was deleted: another one, but
  // the remembered id stays, so the node comes back once it is rebuilt.
  return lebende()[0] || null;
}

// The Series node selected on the canvas, if any - for the command.
function gewaehlteSerie() {
  try {
    const sel = Object.values(app.canvas?.selected_nodes || {});
    return sel.find((n) => serien.has(n.id))?.id ?? null;
  } catch (e) {
    return null;
  }
}

function zeichneBald() {
  if (geplantRAF || typeof requestAnimationFrame !== "function") return;
  geplantRAF = requestAnimationFrame(() => {
    geplantRAF = 0;
    zeichne();
  });
}

// Pictures stay the same element from one drawing to the next, so the stage
// does not flicker when a favourite redraws everything.
const bilder = new Map();
function bildElement(url, alt) {
  let img = bilder.get(url);
  if (!img) {
    if (bilder.size > 800) bilder.clear();
    img = document.createElement("img");
    img.decoding = "async";
    img.src = url;
    bilder.set(url, img);
  }
  img.alt = alt || "";
  img.draggable = false;
  return img;
}

// ------------------------------------------------------------ Placement ---
function holeWurzel() {
  if (wurzel) return wurzel;
  injiziereLightboxCSS();
  wurzel = document.createElement("div");
  wurzel.className = "k2-lb";
  wurzel.tabIndex = 0;
  wurzel.setAttribute("role", "region");
  wurzel.setAttribute("aria-label", "Photoshoot Lightbox");
  wurzel.addEventListener("keydown", taste);
  // The English table comes with the presets; a workflow without a Series
  // node has not asked for them yet.
  ladePresets().then(zeichneBald);
  // Narrow: the info column goes, the stage stays.
  if (typeof ResizeObserver === "function") {
    new ResizeObserver(() => {
      wurzel.classList.toggle("k2-lb-schmal", wurzel.clientWidth > 0 && wurzel.clientWidth < 560);
    }).observe(wurzel);
  }
  return wurzel;
}

function platziere() {
  const ziel = overlay?.isConnected ? overlay : panelEl;
  const w = holeWurzel();
  if (ziel && w.parentElement !== ziel) ziel.append(w);
}

// The bottom panel: ComfyUI's store (app.extensionManager.bottomPanel) with
// the tab registered through the extension's bottomPanelTabs. Opening
// toggles only when the tab is not already the visible one.
function unteresPanel() {
  try {
    const bp = app.extensionManager?.bottomPanel;
    if (typeof bp?.toggleBottomPanelTab !== "function") return null;
    const drin = Object.values(bp.panels || {}).some((p) => p?.tabs?.some?.((t) => t.id === TAB_ID));
    return drin ? bp : null;
  } catch (e) {
    return null;
  }
}

function zeigePanel() {
  const bp = unteresPanel();
  if (!bp) return false;
  try {
    const offen = bp.bottomPanelVisible && bp.activeBottomPanelTabId === TAB_ID;
    if (!offen) bp.toggleBottomPanelTab(TAB_ID);
    return true;
  } catch (e) {
    return false;
  }
}

function oeffneOverlay() {
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.className = "k2-lb-overlay";
    overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) schliesseOverlay(); });
  }
  document.body.append(overlay);
  platziere();
  fokusGewuenscht = true;
  zeichneBald();
}

function schliesseOverlay() {
  if (!overlay?.isConnected) return;
  overlay.remove();
  if (panelEl) {
    platziere();
    fokusGewuenscht = true;
    zeichneBald();
  } else {
    wurzel?.remove();
  }
}

// Whether the Lightbox can open here: in the bottom panel, or as its own
// overlay on the page - which any browser can, so this is false only without
// a document (tests). The Series' contact sheet keeps to two rows while it is
// true, the rest being one click away.
export function lightboxDa() {
  return typeof document !== "undefined" && !!document.body;
}

/** Open the Lightbox on a Series node (default: the selected one, else the
 *  last one), at photo nr if given. Returns whether it opened. */
export function oeffneLightbox(id = null, nr = null) {
  if (!lightboxDa()) return false;
  try {
    oeffne(id, nr);
    return true;
  } catch (e) {
    console.warn("[Photoshoot] Lightbox could not be opened:", e);
    return false;
  }
}

function oeffne(id, nr) {
  injiziereLightboxCSS();
  id = id ?? gewaehlteSerie() ?? sicht.id ?? lebende()[0]?.node.id ?? null;
  if (id !== sicht.id) {
    sicht.id = id;
    sicht.nr = null;
    sicht.filter = "alle";
    sicht.vergleich = false;
  }
  if (nr != null) {
    sicht.nr = nr;
    sicht.filter = "alle";
  }
  sicht.meldung = null;
  holeWurzel();
  fokusGewuenscht = true;
  if (!overlay?.isConnected && !zeigePanel()) oeffneOverlay();
  zeichneBald();
}

// -------------------------------------------------------------- Drawing ---
const el = (tag, klasse, text) => {
  const e = document.createElement(tag);
  if (klasse) e.className = klasse;
  if (text != null) e.textContent = text;
  return e;
};
const knopf = (klasse, text, klick, titel) => {
  const b = el("button", klasse, text);
  b.type = "button";
  if (titel) b.title = titel;
  if (klick) b.onclick = klick;
  return b;
};
const kbd = (b, zeichen) => { b.append(" ", el("kbd", null, zeichen)); return b; };

function zeichne() {
  if (!wurzel || !wurzel.isConnected) return;
  const w = wurzel;
  const hatteFokus = fokusGewuenscht || w.contains(document.activeElement);
  fokusGewuenscht = false;
  const altStreifen = w.querySelector(".k2-lb-streifen")?.scrollLeft || 0;
  const altInfo = w.querySelector(".k2-lb-info")?.scrollTop || 0;
  w.textContent = "";
  const tasten = uet("Tasten: ← → blättern, F Favorit, X verwerfen, C vergleichen, Esc schließt das Vollbild", "ui");

  const serie = aktuelleSerie();
  angezeigt = serie?.node.id ?? null;
  const imOverlay = !!overlay?.isConnected;

  // --- filter row, series choice, fullscreen ---
  const filter = el("div", "k2-lb-filter");
  const rechts = el("div", "k2-lb-rechts");
  const alleSerien = lebende();
  if (alleSerien.length > 1) {
    const sel = el("select");
    sel.title = uet("Welche Serie", "ui");
    for (const s of alleSerien) {
      const o = el("option", null, `${s.node.title || uet("Serie", "ui")} #${s.node.id}`);
      o.value = String(s.node.id);
      sel.append(o);
    }
    sel.value = String(angezeigt);
    sel.onchange = () => {
      const id = alleSerien.find((s) => String(s.node.id) === sel.value)?.node.id;
      Object.assign(sicht, { id, nr: null, filter: "alle", vergleich: false, meldung: null });
      fokusGewuenscht = true;
      zeichne();
    };
    rechts.append(sel);
  }
  if (imOverlay) {
    rechts.append(kbd(knopf("k2-lb-knopf", "✕ " + uet("Schließen", "ui"), schliesseOverlay), "Esc"));
  } else {
    rechts.append(knopf("k2-lb-knopf", "⤢ " + uet("Vollbild", "ui"), oeffneOverlay));
  }

  if (!serie) {
    filter.append(el("span", "k2-lb-label", uet("Lightbox", "ui")), rechts);
    const b = el("div", "k2-lb-buehne");
    b.append(el("div", "k2-lb-leer", uet("Keine Serie im Workflow — eine Photoshoot-Serie anlegen, dann erscheinen ihre Fotos hier.", "ui")));
    w.append(filter, b);
    letzterStand = null;
    if (hatteFokus) w.focus({ preventScroll: true });
    return;
  }

  const state = serie.lies();
  const alle = serie.fotos(state);
  const fav = new Set((state.favoriten || []).map(Number));
  const rej = new Set((state.verworfen || []).map(Number));
  const geschossen = alle.filter((f) => f.bild);
  const passt = (f, filt = sicht.filter) =>
    filt === "alle" ? true
      : filt === "fav" ? fav.has(f.nr)
      : filt === "rej" ? rej.has(f.nr)
      : filt === "entwurf" ? !!f.bild?.entwurf
      : f.p.kamera === filt;
  // A framing filter whose framing is gone (other settings) falls back.
  const kameras = [...new Set(geschossen.map((f) => f.p.kamera).filter(Boolean))];
  if (!["alle", "fav", "rej", "entwurf", ...kameras].includes(sicht.filter)) sicht.filter = "alle";
  const sichtbar = geschossen.filter((f) => passt(f));
  let f = alle.find((x) => x.nr === sicht.nr) || null;
  if (!f || (sicht.filter !== "alle" && !sichtbar.includes(f))) {
    f = sichtbar[0] || (sicht.filter === "alle" ? alle[0] : null);
  }
  sicht.nr = f?.nr ?? null;

  // What ← → and compare step through: the pictures in the filter. From a
  // planned frame, the next picture by number.
  const nachbar = (von, d) => {
    if (!sichtbar.length || !von) return null;
    const i = sichtbar.indexOf(von);
    if (i >= 0) return sichtbar.length > 1 ? sichtbar[(i + d + sichtbar.length) % sichtbar.length] : null;
    return d > 0 ? sichtbar.find((x) => x.nr > von.nr) || sichtbar[0]
                 : [...sichtbar].reverse().find((x) => x.nr < von.nr) || sichtbar[sichtbar.length - 1];
  };
  letzterStand = { serie, f, nachbar };

  const chip = (schluessel, text, n) => {
    const c = knopf("k2-lb-chip" + (sicht.filter === schluessel ? " k2-an" : ""), text, () => {
      sicht.filter = schluessel;
      sicht.meldung = null;
      zeichne();
    });
    c.setAttribute("aria-pressed", String(sicht.filter === schluessel));
    c.append(el("span", "k2-lb-n", String(n)));
    return c;
  };
  const titel = el("span", "k2-lb-label", uet("Kontaktbogen", "ui"));
  titel.title = tasten;
  filter.append(
    titel,
    chip("alle", uet("Alle", "ui"), geschossen.length),
    chip("fav", "♥ " + uet("Favoriten", "ui"), geschossen.filter((x) => passt(x, "fav")).length),
    chip("rej", "✕ " + uet("Verworfen", "ui"), geschossen.filter((x) => passt(x, "rej")).length),
    chip("entwurf", uet("Entwürfe", "ui"), geschossen.filter((x) => passt(x, "entwurf")).length),
  );
  if (kameras.length) {
    filter.append(el("span", "k2-lb-trenn"));
    for (const k of kameras) {
      filter.append(chip(k, uet(k, "shooting/kamera"), geschossen.filter((x) => x.p.kamera === k).length));
    }
  }
  filter.append(rechts);

  // --- stage ---
  const buehne = el("div", "k2-lb-buehne");
  const marken = (x, ziel) => {
    ziel.append(el("span", "k2-lb-marke", String(x.nr)));
    if (fav.has(x.nr)) ziel.append(el("span", "k2-lb-marke k2-fav", "♥"));
    if (rej.has(x.nr)) ziel.append(el("span", "k2-lb-marke k2-rej", "✕"));
    if (x.bild?.entwurf) ziel.append(el("span", "k2-lb-marke k2-draft", uet("Entwurf", "ui")));
  };
  const kameraText = (x) => (x.p.kamera ? uet(x.p.kamera, "shooting/kamera") : "—");
  const bildRahmen = (x) => {
    const r = el("div", "k2-lb-rahmen");
    if (x.bild) {
      r.append(bildElement(x.bild.gross, uetf("Foto {0}", "ui", x.nr) + ", " + kameraText(x)));
    } else {
      const platz = el("div", "k2-lb-platz");
      platz.style.aspectRatio = `${x.bw} / ${x.bh}`;
      platz.append(el("b", null, kameraText(x)), el("span", null, uet("noch nicht fotografiert", "ui")));
      r.append(platz);
    }
    return r;
  };
  let partner = null;
  if (!f) {
    buehne.append(el("div", "k2-lb-leer", geschossen.length ? uet("Nichts in diesem Filter.", "ui")
      : uet("Noch keine Bilder in dieser Serie — Shooting starten.", "ui")));
  } else if (sicht.vergleich && (partner = nachbar(f, 1)) && partner !== f) {
    buehne.classList.add("k2-lb-ab");
    for (const x of [f, partner]) {
      const fig = el("figure", "k2-lb-fig");
      const r = bildRahmen(x);
      // In compare, a click on a picture stars it (or takes the star back).
      r.onclick = () => { serie.schalteFavorit(x.nr); };
      r.title = uet("Klick auf ein Bild: Favorit an/aus", "ui");
      const cap = el("figcaption");
      marken(x, cap);
      cap.append(kameraText(x) + (x.p.ausdruck?.stimmung
        ? " · " + uet(x.p.ausdruck.stimmung, "ausdruck/stimmung") : ""));
      fig.append(r, cap);
      buehne.append(fig);
    }
  } else {
    const m = el("div", "k2-lb-marken");
    marken(f, m);
    const fig = el("figure", "k2-lb-fig");
    fig.append(bildRahmen(f));
    buehne.append(m, fig);
    if (sicht.vergleich && !sicht.meldung) {
      sicht.meldung = { text: uet("Nur ein Foto in diesem Filter — nichts zum Vergleichen.", "ui") };
    }
  }
  if (f && sichtbar.length) {
    const l = knopf("k2-lb-pfeil k2-l", "‹", () => schritt(-1));
    l.setAttribute("aria-label", uet("Vorheriges Foto", "ui"));
    const r = knopf("k2-lb-pfeil k2-r", "›", () => schritt(1));
    r.setAttribute("aria-label", uet("Nächstes Foto", "ui"));
    buehne.append(l, r);
  }
  // Swipe on a touch screen.
  let tx = null;
  buehne.addEventListener("touchstart", (e) => { tx = e.touches[0].clientX; }, { passive: true });
  buehne.addEventListener("touchend", (e) => {
    if (tx == null) return;
    const dx = e.changedTouches[0].clientX - tx;
    tx = null;
    if (Math.abs(dx) > 40) schritt(dx < 0 ? 1 : -1);
  });

  // --- info column ---
  const info = el("aside", "k2-lb-info");
  const lage = serie.lage();
  const stand = serie.rundenStand(state);
  if (f) {
    info.append(el("div", "k2-lb-label", uetf("Foto {0}", "ui", f.nr) + " · " + uetf("Runde {0}", "ui", stand.runde)));
    const dl = el("dl", "k2-lb-dl");
    const zeile = (k, v) => {
      if (v == null || v === "") return;
      const dd = el("dd");
      if (v instanceof Node) dd.append(v); else dd.textContent = v;
      dl.append(el("dt", null, k), dd);
      return dd;
    };
    for (const [k, v] of serie.merkmale(f)) zeile(k, v);
    // Takes: the chosen one is what the frame, the favourite and Finish mean.
    if (f.takes.size > 1) {
      const takes = el("div", "k2-lb-takes");
      for (const t of [...f.takes.keys()].sort((a, b) => a - b)) {
        const an = f.bild?.take === t;
        const c = knopf("k2-lb-chip" + (an ? " k2-an" : ""), null, () => serie.waehleTake(f.nr, t));
        const s = el("span", null, uetf("Take {0}", "ui", t + 1) + (an ? " · " + uet("gewählt", "ui") : "") +
          (f.takes.get(t)?.entwurf ? " · " + uet("Entwurf", "ui") : ""));
        c.append(s);
        c.setAttribute("aria-pressed", String(an));
        takes.append(c);
      }
      zeile("Take", takes);
    } else if (f.bild) {
      zeile("Take", String(f.bild.take + 1));
    }
    zeile(uet("Größe", "ui"), `${f.bw}×${f.bh}` + (f.bild?.entwurf ? " · " + uet("Entwurf", "ui") : ""))
      ?.classList.add("k2-lb-mono");
    // The file the picture is in, as Save Image wrote it (the dateiname output).
    if (f.bild?.datei?.filename) {
      const d = f.bild.datei;
      zeile(uet("Datei", "ui"), (d.subfolder ? d.subfolder + "/" : "") + d.filename)?.classList.add("k2-lb-mono");
    }
    info.append(dl);

    const aktionen = el("div", "k2-lb-aktionen");
    aktionen.append(
      kbd(knopf("k2-lb-knopf" + (fav.has(f.nr) ? " k2-an" : ""), "♥ " + uet("Favorit", "ui"),
                () => serie.schalteFavorit(f.nr)), "F"),
      kbd(knopf("k2-lb-knopf k2-rot" + (rej.has(f.nr) ? " k2-an" : ""), "✕ " + uet("Verwerfen", "ui"),
                () => serie.schalteVerworfen(f.nr),
                uet("Für die nächste Runde: was nur verworfene Fotos zeigen, fällt weg.", "ui")), "X"),
      kbd(knopf("k2-lb-knopf" + (sicht.vergleich ? " k2-an" : ""), "⇆ " + uet("Vergleichen", "ui"),
                () => { sicht.vergleich = !sicht.vergleich; sicht.meldung = null; zeichne(); }), "C"),
    );
    const neu = knopf("k2-lb-knopf", f.bild ? "↻ " + uet("Nachfotografieren", "ui") : "▶ " + uet("Foto schießen", "ui"),
      async () => {
        const nr = f.nr;
        await serie.nachfotografieren([nr]);
        const l = serie.lage();
        sicht.meldung = l.einreiheFehler ? { text: l.einreiheFehler, warn: true }
          : { text: uetf("Foto {0} eingereiht — das neue Bild erscheint, sobald es gerendert ist.", "ui", nr) };
        zeichneBald();
      },
      f.bild ? uet("Gleiche Planung, neues Rauschen", "ui") : uet("Nur dieses geplante Foto jetzt einreihen", "ui"));
    neu.disabled = !!lage.einreihen;
    aktionen.append(neu);
    if (f.bild?.entwurf && serie.refine()) {
      const fertig = knopf("k2-lb-knopf", "✓ " + uet("Fertigstellen", "ui"), async () => {
        const nr = f.nr;
        await serie.fertigstellen([nr]);
        const l = serie.lage();
        sicht.meldung = l.einreiheFehler ? { text: l.einreiheFehler, warn: true }
          : { text: uetf("Foto {0} eingereiht — das neue Bild erscheint, sobald es gerendert ist.", "ui", nr) };
        zeichneBald();
      }, uet("In voller Qualität fertigstellen: gleicher Take, gleicher Seed, mit zweitem Durchgang.", "ui"));
      fertig.disabled = !!lage.einreihen;
      aktionen.append(fertig);
    }
    if (f.bild) {
      const a = el("a", "k2-lb-knopf", uet("Bild öffnen", "ui"));
      a.href = f.bild.gross;
      a.target = "_blank";
      a.rel = "noopener";
      aktionen.append(a);
    }
    info.append(aktionen);

    // The prompt this take got, from the same history entry as its picture.
    if (f.bild) {
      const det = el("details", "k2-lb-prompt");
      det.open = sicht.promptOffen;
      det.addEventListener("toggle", () => { sicht.promptOffen = det.open; });
      det.append(el("summary", null, uet("Prompt", "ui")));
      if (f.bild.prompt) {
        det.append(el("p", null, f.bild.prompt));
        const frisch = kopiert && kopiert.text === f.bild.prompt && Date.now() < kopiert.bis;
        const k = knopf("k2-lb-knopf", !frisch ? uet("Kopieren", "ui")
          : kopiert.ok ? "✓ " + uet("Kopiert", "ui") : uet("Kopieren fehlgeschlagen", "ui"), async () => {
          kopiert = { text: f.bild.prompt, ok: await kopiere(f.bild.prompt), bis: Date.now() + 1500 };
          zeichne();
          setTimeout(zeichneBald, 1600);
        });
        det.append(k);
      } else {
        det.append(el("p", "k2-lb-notiz", uet("nicht mehr im Verlauf — ComfyUI wurde seitdem neu gestartet", "ui")));
      }
      info.append(det);
    }
  }

  // --- filmstrip: the pictures in the filter; under "All" the planned
  //     frames too, dashed, in number order ---
  const streifen = el("div", "k2-lb-streifen");
  streifen.setAttribute("aria-label", uet("Kontaktbogen", "ui"));
  let aktivesKlein = null;
  for (const x of sicht.filter === "alle" ? alle : sichtbar) {
    const k = knopf("k2-lb-klein" + (x === f ? " k2-an" : "") + (x.bild ? "" : " k2-geplant") +
                    (rej.has(x.nr) ? " k2-rej" : "") + (x.bild?.entwurf ? " k2-draft" : "") +
                    (x.nr === lage.aktivFoto ? " k2-rendert" : ""), null, () => {
      sicht.nr = x.nr;
      sicht.meldung = null;
      zeichne();
    });
    k.setAttribute("aria-label", uetf("Foto {0}", "ui", x.nr) + ", " + kameraText(x));
    if (x.bild) {
      k.append(bildElement(x.bild.klein, ""), el("span", "k2-lb-nr", String(x.nr)));
      if (fav.has(x.nr)) k.append(el("span", "k2-lb-h", "♥"));
    } else {
      k.style.width = Math.round((62 * x.bw) / x.bh) + "px";
      k.append(el("span", "k2-lb-nr", String(x.nr)), document.createElement("br"), kameraText(x));
    }
    if (x === f) aktivesKlein = k;
    streifen.append(k);
  }

  // --- footer: the round, its selects, Next round ---
  const fuss = el("div", "k2-lb-fuss");
  const links = el("div", "k2-lb-stand");
  links.append(el("span", null, [uetf("Runde {0}", "ui", stand.runde), uetf("{0} Favoriten", "ui", stand.fav),
                                  uetf("{0} verworfen", "ui", stand.weg)].join(" · ")));
  const meldung = lage.einreihen
    ? { text: uetf("eingereiht {0}/{1}", "ui", lage.einreihen.n, lage.einreihen.gesamt) }
    : lage.aktivFoto != null
      ? { text: uetf("Rendert Foto {0}", "ui", lage.aktivFoto) +
          (lage.warteschlange > 1 ? " · " + uetf("noch {0} in Queue", "ui", lage.warteschlange - 1) : "") }
      : lage.einreiheFehler ? { text: lage.einreiheFehler, warn: true }
      : lage.rundeFehler ? { text: lage.rundeFehler, warn: true }
      : sicht.meldung;
  if (meldung) links.append(el("span", "k2-lb-meldung" + (meldung.warn ? " k2-warn" : ""), meldung.text));
  const rechtsFuss = el("div", "k2-lb-rechts");
  if ((lage.einreihen || lage.warteschlange > 0) && serie.stopp) {
    rechtsFuss.append(knopf("k2-lb-knopf k2-stopp", "⏹ " + uet("Stopp", "ui"), () => serie.stopp(),
                            uet("Laufendes Rendering abbrechen und Warteschlange leeren", "ui")));
  }
  const los = knopf("k2-lb-knopf k2-haupt", uet("Nächste Runde", "ui") + " →", async () => {
    const start = Math.max(1, parseInt(state.start, 10) || 1) + (parseInt(state.anzahl, 10) || 1);
    await serie.naechsteRunde();
    const l = serie.lage();
    Object.assign(sicht, { nr: null, filter: "alle", vergleich: false,
                           meldung: l.rundeFehler ? { text: l.rundeFehler, warn: true }
                             : { text: uetf("Runde {0} geplant — ab Foto {1}.", "ui", stand.runde + 1, start) } });
    fokusGewuenscht = true;
    zeichneBald();
  });
  los.disabled = !stand.moeglich;
  los.title = los.disabled
    ? uet("Erst Favoriten (♥) im Kontaktbogen markieren: die nächste Runde behält ihre Einstellungen, Pose- und Stimmungsfamilien, Schwerpunkte und Outfits.", "ui")
    : uetf("Neue Serie ab Foto {0}: nur die Einstellungen, Pose- und Stimmungsfamilien, Schwerpunkte und Outfits der Auswahl ({1} ♥, {2} ✕).", "ui",
           Math.max(1, parseInt(state.start, 10) || 1) + (parseInt(state.anzahl, 10) || 1), stand.fav, stand.weg);
  rechtsFuss.append(los);
  fuss.append(links, rechtsFuss);

  w.append(filter, buehne, info, streifen, fuss);
  info.scrollTop = altInfo;
  // The strip keeps its place and brings the current photo into view.
  streifen.scrollLeft = altStreifen;
  if (aktivesKlein) {
    const l = aktivesKlein.offsetLeft - streifen.offsetLeft, r = l + aktivesKlein.offsetWidth;
    if (l < streifen.scrollLeft) streifen.scrollLeft = l - 12;
    else if (r > streifen.scrollLeft + streifen.clientWidth) streifen.scrollLeft = r - streifen.clientWidth + 12;
  }
  // The next picture, fetched ahead so → shows it at once.
  const weiter = f && nachbar(f, 1);
  if (weiter?.bild) bildElement(weiter.bild.gross, "");
  if (hatteFokus) w.focus({ preventScroll: true });
}

function schritt(d) {
  const s = letzterStand;
  const ziel = s?.f && s.nachbar(s.f, d);
  if (!ziel) return;
  sicht.nr = ziel.nr;
  sicht.meldung = null;
  zeichne();
}

// Keys only while the Lightbox has the focus - never from the canvas or a
// text field - and taken from ComfyUI's own shortcuts while they are handled.
function taste(e) {
  if (e.ctrlKey || e.metaKey || e.altKey || e.isComposing) return;
  if (e.target?.closest?.("input, textarea, select, [contenteditable='true']")) return;
  const s = letzterStand;
  const k = e.key.length === 1 ? e.key.toLowerCase() : e.key;
  let erledigt = true;
  if (k === "ArrowRight") schritt(1);
  else if (k === "ArrowLeft") schritt(-1);
  else if (k === "f" && s?.f) s.serie.schalteFavorit(s.f.nr);
  else if (k === "x" && s?.f) s.serie.schalteVerworfen(s.f.nr);
  else if (k === "c" && s?.f) { sicht.vergleich = !sicht.vergleich; sicht.meldung = null; zeichne(); }
  else if (k === "Escape" && overlay?.isConnected) schliesseOverlay();
  else erledigt = false;
  if (erledigt) {
    e.preventDefault();
    e.stopPropagation();
  }
}

// -------------------------------------------------------- Registration ---
// A custom tab in ComfyUI's bottom panel (next to Logs and Terminal), which
// also gives the command Workspace.ToggleBottomPanelTab.photoshoot-lightbox.
// render() can come more than once for the same element; destroy() when the
// tab is closed or another one is chosen.
const TAB = {
  id: TAB_ID,
  title: "Lightbox",
  type: "custom",
  render(element) {
    // The element ComfyUI hands over has auto height inside a panel the user
    // resizes; filled, the stage grows and shrinks with the panel.
    element.style.height = "100%";
    element.style.minHeight = "0";
    panelEl = element;
    platziere();
    zeichneBald();
  },
  destroy() {
    panelEl = null;
    if (!overlay?.isConnected) wurzel?.remove();
  },
};

app.registerExtension({
  name: "Krea2.Lightbox",
  bottomPanelTabs: [TAB],
  commands: [{
    id: BEFEHL,
    label: "Photoshoot: Open Lightbox",
    icon: "pi pi-images",
    function: () => oeffneLightbox(),
  }],
  setup() {
    // A front end that takes the store call but not the extension key.
    try {
      const bp = app.extensionManager?.bottomPanel;
      if (!unteresPanel() && typeof bp?.registerBottomPanelTab === "function") bp.registerBottomPanelTab(TAB);
    } catch (e) {
      // No bottom panel: the Lightbox opens as an overlay.
    }
  },
});
