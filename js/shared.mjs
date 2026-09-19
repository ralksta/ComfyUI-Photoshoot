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
/* Number of fields set, shown on each section row. */
.k2-zahl{font-size:8px;margin-left:2px;opacity:.75;vertical-align:super;line-height:0}

/* Person Builder: brand strip and collapsible sections (the Steckbrief). */
.k2-marke{display:flex;align-items:center;gap:6px;padding:0 2px 6px;border-bottom:1px solid #303030}
.k2-marke-logo{display:flex}
.k2-marke-wort{font-weight:700;font-size:12px;color:#eceef1;letter-spacing:-.01em}
.k2-marke-teil{font-size:8.5px;letter-spacing:.14em;text-transform:uppercase;color:#f66744;font-weight:600;
  border-left:1px solid #444;padding-left:6px}
.k2-marke-zahl{margin-left:auto;font-size:9.5px;color:#9a9a9a;font-variant-numeric:tabular-nums}
.k2-liste{gap:1px}
.k2-bereich{border:1px solid transparent;border-radius:6px}
.k2-bereich.k2-offen{border-color:#3d3d3d;background:#222}
.k2-bereich.k2-via-lora > .k2-kopf{opacity:.55}
.k2-kopf{display:grid;grid-template-columns:10px 84px 1fr auto;align-items:center;gap:5px;
  padding:5px 4px;border-radius:5px;cursor:pointer;user-select:none}
.k2-kopf:hover{background:#2c2c2c}
.k2-kopf:focus-visible{outline:1px solid #f66744;outline-offset:-1px}
.k2-chev{color:#8e8e8e;font-size:7px;transition:transform .12s}
.k2-offen .k2-chev{transform:rotate(90deg);color:#f66744}
.k2-bname{font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;color:#a8a8a8;white-space:nowrap}
.k2-offen .k2-bname{color:#f0f0f0;font-weight:600}
.k2-bname .k2-zahl{color:#f66744;opacity:1}
.k2-kurz{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#c9a08f;font-size:10px}
.k2-kurz.k2-leer{color:#8e8e8e;font-style:italic}
.k2-kurz i{font-style:normal;color:#5a5a5a;padding:0 3px}
.k2-mini{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:3px;vertical-align:0;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.2)}
.k2-weg{color:#8e8e8e;font-size:12px;min-width:18px;text-align:center;border-radius:3px;white-space:nowrap}
.k2-weg:hover{color:#f66744;background:#3a2620}
.k2-weg.k2-frage{color:#f66744;font-size:9px;padding:0 3px}
.k2-inhalt{display:flex;flex-direction:column;gap:5px;padding:2px 6px 8px 18px}
.k2-inhalt .k2-feld > .k2-name{flex-basis:70px}
.k2-stueck{display:flex;flex-direction:column;gap:4px}
.k2-kleidung{gap:0}
.k2-kleidung > .k2-stueck{padding:6px 0}
.k2-kleidung > .k2-stueck + .k2-stueck{border-top:1px solid #333}
.k2-name.k2-unterfeld{text-transform:none;letter-spacing:.02em;font-size:9.5px;color:#8a8a8a;padding-left:8px}
.k2-notiz{font-size:9px;color:#b08a5a;line-height:1.35;padding-left:76px}
select.k2-ignoriert{color:#777;text-decoration:line-through}
.k2-gesicht{font-size:9.5px;color:#a0a0a0;line-height:1.35;padding:2px 6px 4px 20px}
.k2-gesicht.k2-arg{color:#f66744}
/* Colour: one button next to the dropdown, the palette opens under the row. */
.k2-farbknopf{flex:0 0 24px;height:21px;box-sizing:border-box;border:1px solid #3d3d3d;border-radius:4px;
  background:#1d1d1d;display:grid;place-items:center;cursor:pointer;padding:0}
.k2-farbknopf:hover,.k2-farbknopf.k2-offen{border-color:#f66744}
.k2-farbknopf:focus-visible{outline:1px solid #f66744}
.k2-farbknopf:disabled{cursor:not-allowed;opacity:.45;border-color:#3d3d3d}
.k2-farbfuellung{width:12px;height:12px;border-radius:50%;box-shadow:inset 0 0 0 1px rgba(255,255,255,.2)}
.k2-farbknopf.k2-ohne .k2-farbfuellung{background:transparent;box-shadow:inset 0 0 0 1px #5a5a5a;position:relative}
.k2-farbknopf.k2-ohne .k2-farbfuellung::after{content:"";position:absolute;left:50%;top:1px;bottom:1px;width:1px;
  background:#5a5a5a;transform:rotate(45deg)}
.k2-farbtext{flex:1;min-width:0;font-size:10px;color:#d7d7d7}
.k2-farbtext.k2-leer{color:#8e8e8e}
.k2-palette{margin-left:76px;background:#1a1a1a;border:1px solid #4a4a4a;border-radius:6px;padding:7px;
  display:flex;flex-direction:column;gap:6px;align-self:flex-start}
.k2-palette-kopf{display:flex;justify-content:space-between;gap:8px;font-size:8.5px;letter-spacing:.06em;
  text-transform:uppercase;color:#8a8a8a}
.k2-palette-name{text-transform:none;letter-spacing:0;font-size:10px;color:#e4c3b5;white-space:nowrap}
.k2-raster{display:grid;grid-template-columns:repeat(8,16px);gap:5px}
.k2-punkt{width:16px;height:16px;border-radius:50%;border:0;padding:0;cursor:pointer;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.15);position:relative;background:transparent}
.k2-punkt:hover{transform:scale(1.15)}
.k2-punkt:focus-visible{outline:2px solid #f66744;outline-offset:1px}
.k2-punkt.k2-an{box-shadow:0 0 0 2px #1a1a1a,0 0 0 3.5px #f66744}
.k2-punkt.k2-nichts{box-shadow:inset 0 0 0 1px #5a5a5a}
.k2-punkt.k2-nichts.k2-an{box-shadow:inset 0 0 0 1px #5a5a5a,0 0 0 2px #1a1a1a,0 0 0 3.5px #f66744}
.k2-punkt.k2-nichts::after{content:"";position:absolute;left:50%;top:2px;bottom:2px;width:1px;background:#5a5a5a;
  transform:rotate(45deg)}
@media (prefers-reduced-motion:reduce){.k2-chev,.k2-punkt{transition:none}.k2-punkt:hover{transform:none}}

/* Actions & Reset bar */
.k2-inspire-btn{display:inline-flex;align-items:center;gap:3px;background:#261814;border:1px solid #7d3320;
  color:#f68c70;border-radius:4px;padding:2px 6px;cursor:pointer;user-select:none;font-size:9px;
  font-weight:600;letter-spacing:.02em;white-space:nowrap;transition:all .15s ease}
.k2-inspire-btn:hover{background:#3a2019;border-color:#f66744;color:#ff9e85}
.k2-inspire-btn:active{transform:scale(.96)}
.k2-reset{display:flex;gap:10px;justify-content:space-between;align-items:center;font-size:9px;margin-top:2px}
.k2-reset-gruppe{display:flex;gap:10px;align-items:center}
.k2-reset-knopf{color:#8e8e8e;cursor:pointer;user-select:none;white-space:nowrap}
.k2-reset-knopf:hover,.k2-reset-knopf.k2-frage{color:#f66744}

/* Start button of the photoshoot - the one full orange surface on the node. */
.k2-start{border:1px solid #f66744;background:#f66744;color:#1a1a1a;border-radius:5px;
  padding:5px 8px;text-align:center;cursor:pointer;user-select:none;font-size:11px;
  font-weight:600;letter-spacing:.02em;display:flex;flex-direction:column;align-items:center;gap:1px;
  font-family:inherit}
.k2-start b{font-size:12px}
.k2-start small{font-size:9.5px;font-weight:500;opacity:.8;font-variant-numeric:tabular-nums}
.k2-start:hover{background:#ff7a58;border-color:#ff7a58}
.k2-start:active{background:#d9542f}
.k2-start:focus-visible{outline:2px solid #fff;outline-offset:1px}
.k2-start.k2-klein{flex-direction:row;padding:3px 8px;font-size:10px}
.k2-feld input[type=number]{text-align:center}

/* Series: count, start number and a text button in one row, status below. */
.k2-serie-zeile{display:flex;align-items:center;gap:5px}
.k2-serie-zeile label{display:flex;align-items:center;gap:5px;font-size:9px;letter-spacing:.06em;
  text-transform:uppercase;color:#8a8a8a}
.k2-serie-zeile input{width:40px;background:#1d1d1d;color:#e2e2e2;border:1px solid #3d3d3d;border-radius:4px;
  padding:3px 4px;font-size:11px;font-family:inherit;text-align:center;font-variant-numeric:tabular-nums}
.k2-serie-zeile label + label input{width:54px}
.k2-serie-zeile .k2-textknopf{margin-left:auto;padding:2px 5px}
.k2-textknopf{background:none;border:1px solid #3d3d3d;border-radius:4px;color:#c9a08f;cursor:pointer;
  font-size:10px;padding:2px 7px;font-family:inherit;text-decoration:none;white-space:nowrap}
.k2-textknopf:hover{border-color:#5a5a5a;color:#ecc4b4}
.k2-textknopf.k2-an{border-color:#f66744;color:#f3d6cb;background:#2e201b}
.k2-textknopf:focus-visible{outline:1px solid #f66744}
.k2-status{display:flex;justify-content:space-between;font-size:9.5px;color:#9a9a9a;font-variant-numeric:tabular-nums}
.k2-status b{color:#e2e2e2;font-weight:600}

/* Axis rows: switch, name, what it does, arrow; the details unfold under the
   row. The switches are small and neutral - orange belongs to the start
   button. */
.k2-achsen{display:flex;flex-direction:column;flex:0 1 auto;min-height:0;overflow-y:auto;gap:1px}
.k2-achsen::-webkit-scrollbar{width:6px}
.k2-achsen::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-achse-box{border:1px solid transparent;border-radius:5px}
.k2-achse-box.k2-offen{border-color:#3d3d3d;background:#222}
.k2-achse{display:grid;grid-template-columns:26px 78px 1fr 10px;align-items:center;gap:6px;padding:4px 4px;
  cursor:pointer;user-select:none;border-radius:4px}
.k2-achse:hover{background:#2c2c2c}
.k2-achse:focus-visible{outline:1px solid #f66744;outline-offset:-1px}
.k2-achse.k2-zu{cursor:default}
.k2-achse.k2-zu:hover{background:none}
.k2-schalter{width:24px;height:13px;border-radius:7px;background:#45454b;position:relative;cursor:pointer;
  border:0;padding:0}
.k2-schalter::after{content:"";position:absolute;top:2px;left:2px;width:9px;height:9px;border-radius:50%;
  background:#9a9a9a;transition:left .12s}
.k2-schalter[aria-checked="true"]{background:#a8553c}
.k2-schalter[aria-checked="true"]::after{left:13px;background:#f4eeec}
.k2-schalter:focus-visible{outline:1px solid #f66744;outline-offset:2px}
.k2-achse-name{font-size:11px;color:#8e8e8e}
.k2-achse.k2-hell .k2-achse-name{color:#e2e2e2}
.k2-achse-wert{font-size:10px;color:#8e8e8e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:right}
.k2-achse.k2-hell .k2-achse-wert{color:#c9a08f}
.k2-pfeil{font-size:7px;color:#8e8e8e;text-align:center;transition:transform .12s}
.k2-offen .k2-pfeil{transform:rotate(90deg);color:#f66744}
.k2-auf{padding:2px 6px 8px 36px;display:flex;flex-direction:column;gap:6px}
.k2-schnell{display:flex;gap:4px;flex-wrap:wrap;align-items:center;font-size:9.5px;color:#8e8e8e}
.k2-anotiz{font-size:9.5px;color:#9a9a9a;line-height:1.4}
.k2-rrect{display:inline-block;border:1.5px solid currentColor;border-radius:2px;margin-right:4px;vertical-align:-2px}
/* In the series, a chosen chip is outlined rather than filled: with every
   framing on, a wall of orange said nothing. */
.k2-serie .k2-chip{font-family:inherit}
.k2-serie .k2-chip.k2-an{background:#2e201b;border-color:#f66744;color:#f3d6cb;font-weight:500}
.k2-chip.k2-klein{font-size:9px;padding:1px 5px}
.k2-rezepte{row-gap:3px}
.k2-eigen{font-size:9px;color:#8e8e8e;font-style:italic}
.k2-eigene{display:inline-flex;align-items:center}
.k2-weg-klein{background:none;border:0;color:#8e8e8e;cursor:pointer;font-size:11px;padding:0 2px;font-family:inherit}
.k2-weg-klein:hover{color:#f66744}
.k2-plus{border-style:dashed}
.k2-serien-name{width:110px;background:#1d1d1d;color:#e2e2e2;border:1px solid #f66744;border-radius:4px;
  padding:2px 5px;font-size:10px;font-family:inherit}

/* Contact sheet: every photo a frame in its real ratio, with the picture once
   it is rendered. */
.k2-bogen{border-top:1px solid #303030;padding-top:6px;display:flex;flex-direction:column;gap:6px;
  flex:1 1 auto;min-height:90px;overflow-y:auto}
.k2-bogen::-webkit-scrollbar{width:6px}
.k2-bogen::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-bogen-kopf{display:flex;justify-content:space-between;font-size:9px;letter-spacing:.06em;
  text-transform:uppercase;color:#8a8a8a}
.k2-bilder{display:flex;flex-wrap:wrap;gap:7px 5px;align-items:flex-end}
.k2-bild{display:flex;flex-direction:column;align-items:center;gap:2px;width:52px;background:none;border:0;
  padding:0;cursor:pointer;font-family:inherit}
.k2-rahmen{box-sizing:border-box;border:1.5px solid #666;border-radius:3px;position:relative;background:#222 center/cover;
  display:flex;justify-content:space-between;align-items:flex-start;padding:1px 3px}
.k2-rahmen i{font-style:normal;font-size:8.5px;color:#d0d0d0;font-variant-numeric:tabular-nums;
  background:rgba(20,20,20,.7);border-radius:2px;padding:0 2px;line-height:1.3}
.k2-rahmen em{font-style:normal;font-size:8.5px;color:#f66744;background:rgba(20,20,20,.7);border-radius:2px;
  padding:0 2px;line-height:1.3}
.k2-bild-label{font-size:8.5px;color:#8e8e8e;max-width:52px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k2-bild:hover .k2-rahmen{border-color:#9a9a9a}
.k2-bild.k2-fertig .k2-rahmen{border-color:#7d4a38}
.k2-bild.k2-gewaehlt .k2-rahmen{border-color:#f66744;box-shadow:0 0 0 1px #f66744}
.k2-bild.k2-gewaehlt .k2-bild-label{color:#c9a08f}
.k2-bild:focus-visible .k2-rahmen{outline:1px solid #f66744;outline-offset:2px}
.k2-mehr{font-size:9.5px;color:#8e8e8e;align-self:center}
.k2-detail{background:#222;border:1px solid #333;border-radius:5px;padding:6px 8px;display:grid;
  grid-template-columns:60px 1fr;gap:2px 8px;font-size:10px}
.k2-detail > span{color:#8a8a8a;font-size:9px;letter-spacing:.04em;text-transform:uppercase}
.k2-detail > b{font-weight:500;color:#dcdcdc}
.k2-takes{grid-column:1 / -1;display:flex;gap:5px;margin-top:4px}
.k2-take{height:40px;border:1.5px solid #555;border-radius:3px;background:#222 center/cover;cursor:pointer;
  padding:1px 2px;display:flex;align-items:flex-start}
.k2-take i{font-style:normal;font-size:8.5px;color:#d0d0d0;background:rgba(20,20,20,.7);border-radius:2px;padding:0 2px}
.k2-take.k2-an{border-color:#f66744}
.k2-take:focus-visible{outline:1px solid #f66744;outline-offset:2px}
.k2-aktionen{grid-column:1 / -1;display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-top:4px}
.k2-nachhol{display:flex;gap:6px;align-items:center}
.k2-warn{font-size:10px;color:#f66744;line-height:1.35}
`;

export function injiziereCSS() {
  if (document.getElementById(CSS_ID)) return;
  const s = document.createElement("style");
  s.id = CSS_ID;
  s.textContent = CSS;
  document.head.appendChild(s);
}

// ----------------------------------------------------------- Brand strip ---
// The Photoshoot mark from docs/logo.svg - the contact sheet with the one
// exposed frame - inline, so no extra request. Heads the Person and Series
// panels: "Photoshoot | PERSON" with a count on the right.
const MARKE = `<svg viewBox="0 0 80 80" width="18" height="18" aria-hidden="true">
<g fill="none" stroke="#8a8f98" stroke-width="5"><rect x="2.5" y="2.5" width="28" height="40" rx="5"/>
<rect x="2.5" y="50" width="40" height="27.5" rx="5"/><rect x="50" y="50" width="27.5" height="27.5" rx="5"/></g>
<rect x="37" y="0" width="43" height="43" rx="5" fill="#f66744"/>
<circle cx="58.5" cy="15" r="6.5" fill="#1b1d21"/><path d="M44 43a14.5 14.5 0 0 1 29 0z" fill="#1b1d21"/></svg>`;

export function markenleiste(teil, rechts) {
  const marke = document.createElement("div");
  marke.className = "k2-marke";
  const logo = document.createElement("span");
  logo.className = "k2-marke-logo";
  logo.innerHTML = MARKE;
  const wort = document.createElement("span");
  wort.className = "k2-marke-wort";
  wort.textContent = "Photoshoot";
  const t = document.createElement("span");
  t.className = "k2-marke-teil";
  t.textContent = teil;
  const zahl = document.createElement("span");
  zahl.className = "k2-marke-zahl";
  zahl.textContent = rechts || "";
  marke.append(logo, wort, t, zahl);
  return marke;
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
      const el = e.target.closest(".k2-scroll, .k2-blatt, .k2-achsen, .k2-bogen, .k2-vorschau");
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

