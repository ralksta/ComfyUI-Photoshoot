// The interface itself. Pose and expression are structurally identical - one
// long field with families, several short fields, a die on each - so one
// blueprint serves both, fed from /krea2/presets.

import {
  applyAdaptiveCanvasOnly,
  installCanvasZoomPassthrough,
  injiziereCSS,
  ladePresets,
  leseState,
  registriereStateInjektion,
  schreibeState,
  t,
} from "./shared.mjs?v=2.3.0";

import { app } from "../../scripts/app.js";

// Build the English sentence from the current state - the same order and the
// same separator as compose_pose/compose_expression in Python. Fields being
// rolled cannot be resolved here (the roll happens server side with the seed),
// so they appear as placeholders.
function baueVorschau(daten, state, bereich) {
  const teile = [];
  for (const cat of daten.reihenfolge) {
    if (state.wuerfeln?.[cat]) {
      teile.push("⟨" + t(cat, "kategorien") + " " + t("wird gewürfelt", "ui") + "⟩");
      continue;
    }
    const label = state.felder?.[cat];
    if (!label || label === daten.leer) continue;
    const treffer = daten.felder[cat].find((e) => e.label === label);
    if (treffer) teile.push(treffer.wert);
  }
  const frei = (state.details || "").trim().replace(/[,;.\s]+$/, "");
  if (frei) teile.push(frei);
  return teile.join(", ");
}

export function baueNode(node, opts) {
  // bereich: "pose" or "ausdruck" - the English display labels for this node's
  // labels live under that key.
  const { daten, prop, vorgabe, bereich } = opts;
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root";
  installCanvasZoomPassthrough(root);

  const lies = () => leseState(node, prop, vorgabe);
  const schreib = (s) => {
    schreibeState(node, prop, s);
    zeichne();
  };

  const gruppenFeld = daten.gruppenFeld;
  const kurzeFelder = daten.reihenfolge.filter((c) => c !== gruppenFeld);

  function zeichne() {
    const state = lies();
    root.textContent = "";

    // --- long field: family chips, variants underneath --------------------
    const kopf = document.createElement("div");
    kopf.className = "k2-label";
    const titel = document.createElement("span");
    titel.textContent = t(gruppenFeld, "kategorien").toUpperCase();
    const gewaehlt = document.createElement("span");
    gewaehlt.className = "k2-wert"; // pushes the die to the right via flex:1
    const lang = state.felder?.[gruppenFeld];
    gewaehlt.textContent =
      lang && lang !== daten.leer ? t(lang, bereich + "/" + gruppenFeld) : "";
    kopf.append(titel, gewaehlt, wuerfelKnopf(state, gruppenFeld));
    root.append(kopf);

    const famZeile = document.createElement("div");
    famZeile.className = "k2-chips";
    const gruppenNamen = [daten.alle, ...Object.keys(daten.gruppen)];
    for (const g of gruppenNamen) {
      const c = document.createElement("div");
      c.className = "k2-chip k2-fam" + (state.gruppe === g ? " k2-an" : "");
      c.textContent = g === daten.alle ? t("alle", "ui") : t(g, "familien");
      c.onclick = () => schreib({ ...state, gruppe: g });
      famZeile.append(c);
    }
    root.append(famZeile);

    const box = document.createElement("div");
    box.className = "k2-scroll k2-chips";
    const sichtbar =
      state.gruppe && state.gruppe !== daten.alle
        ? daten.felder[gruppenFeld].filter((e) => daten.gruppen[state.gruppe]?.includes(e.label))
        : daten.felder[gruppenFeld];
    for (const e of sichtbar) {
      const c = document.createElement("div");
      const aktiv = state.felder?.[gruppenFeld] === e.label;
      c.className = "k2-chip" + (aktiv ? " k2-an" : "");
      c.textContent = t(e.label, bereich + "/" + gruppenFeld);
      c.title = e.wert;
      c.onclick = () =>
        schreib({
          ...state,
          felder: { ...state.felder, [gruppenFeld]: aktiv ? daten.leer : e.label },
        });
      box.append(c);
    }
    root.append(box);

    // --- short fields: selection plus die ------------------------------------
    for (const cat of kurzeFelder) {
      const zeile = document.createElement("div");
      zeile.className = "k2-reihe";

      const sel = document.createElement("select");
      const leer = document.createElement("option");
      leer.value = daten.leer;
      leer.textContent = t(cat, "kategorien") + " —";
      sel.append(leer);
      for (const e of daten.felder[cat]) {
        const o = document.createElement("option");
        o.value = e.label;
        o.textContent = t(e.label, bereich + "/" + cat);
        o.title = e.wert;
        sel.append(o);
      }
      sel.value = state.felder?.[cat] || daten.leer;
      sel.disabled = !!state.wuerfeln?.[cat];
      sel.onchange = () =>
        schreib({ ...state, felder: { ...state.felder, [cat]: sel.value } });

      zeile.append(sel, wuerfelKnopf(state, cat));
      root.append(zeile);
    }

    // --- free text ------------------------------------------------------------
    const frei = document.createElement("input");
    frei.className = "k2-frei";
    frei.placeholder = t("Weiteres (englisch)", "ui");
    frei.value = state.details || "";
    // Write only on change, otherwise the canvas is redrawn on every keystroke
    // and the node flickers.
    frei.onchange = () => schreib({ ...state, details: frei.value });
    root.append(frei);

    // --- live preview ---------------------------------------------------------
    const v = document.createElement("div");
    const text = baueVorschau(daten, state, bereich);
    v.className = "k2-vorschau" + (text ? "" : " k2-leer");
    v.textContent = text || t("nichts gewählt", "ui");
    root.append(v);
  }

  function wuerfelKnopf(state, cat) {
    const b = document.createElement("div");
    const an = !!state.wuerfeln?.[cat];
    b.className = "k2-wuerfel" + (an ? " k2-an" : "");
    b.textContent = "🎲";
    b.title = an
      ? t("wird gewürfelt — klicken für fest", "ui")
      : t("fest — klicken zum Würfeln", "ui");
    b.onclick = () => {
      const w = { ...(state.wuerfeln || {}) };
      if (an) delete w[cat];
      else w[cat] = true;
      schreib({ ...state, wuerfeln: w });
    };
    return b;
  }

  // Do not draw straight away: nodeCreated runs before configure(), so we would
  // render with defaults and jump to the loaded state milliseconds later.
  queueMicrotask(zeichne);
  node._k2Zeichne = zeichne;

  const w = node.addDOMWidget("k2_ui", "custom", root, {
    getValue: () => node.properties?.[prop],
    setValue: () => {},
    getMinHeight: () => opts.hoehe,
    getMaxHeight: () => opts.hoehe,
    margin: 4,
    serialize: false, // the state hangs off node.properties, not off the widget
  });
  applyAdaptiveCanvasOnly(w);
  return root;
}

// Shared registration for both nodes.
export function registriere(cfg) {
  const { classType, hiddenName, prop, vorgabe, datenSchluessel, hoehe, breite } = cfg;

  registriereStateInjektion(classType, hiddenName, prop, vorgabe);

  app.registerExtension({
    name: "Krea2." + classType,

    async beforeRegisterNodeDef(nodeType, nodeData) {
      if (nodeData.name !== classType) return;
      // Redraw after a workflow is loaded - configure() may run before or
      // after nodeCreated, depending on the front-end version.
      const orig = nodeType.prototype.onConfigure;
      nodeType.prototype.onConfigure = function (info) {
        const r = orig?.apply(this, arguments);
        queueMicrotask(() => this._k2Zeichne?.());
        return r;
      };
    },

    async nodeCreated(node) {
      if (node.comfyClass !== classType) return;
      const presets = await ladePresets();
      if (!presets) return;
      node.size = [breite, hoehe + 78]; // room for title, seed row, output
      baueNode(node, { daten: presets[datenSchluessel], prop, vorgabe, hoehe,
                       bereich: datenSchluessel });
    },
  });
}

