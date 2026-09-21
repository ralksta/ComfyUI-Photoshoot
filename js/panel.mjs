// The interface itself. Pose, expression, lighting and style are structurally
// identical - one long field with families, several short fields, a die on
// each - so one blueprint serves all four, fed from /krea2/presets.

import {
  applyAdaptiveCanvasOnly,
  eigeneHinweis,
  eigeneKopie,
  installCanvasZoomPassthrough,
  injiziereCSS,
  ladePresets,
  leseState,
  markenleiste,
  merkeBenutzt,
  merkliste,
  passtSuche,
  registriereStateInjektion,
  schreibeState,
  t,
  tf,
} from "./shared.mjs?v=2.6.0";

import { app } from "../../scripts/app.js";

// From this length on a field gets a search over its chips and a row of the
// recently used ones (90 moods, 30 light setups).
const LANGE_LISTE = 12;

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
    const treffer = daten.felder[cat].find((e) => e.label === label)?.wert ?? state.eigene?.[cat]?.[label];
    if (treffer) teile.push(treffer);
  }
  const frei = (state.details || "").trim().replace(/[,;.\s]+$/, "");
  if (frei) teile.push(frei);
  return teile.join(", ");
}

export function baueNode(node, opts) {
  // bereich: "pose", "ausdruck", "lighting" or "style" - the English display
  // labels for this node's labels live under that key.
  const { daten, prop, vorgabe, bereich, teil } = opts;
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root";
  installCanvasZoomPassthrough(root);

  const lies = () => leseState(node, prop, vorgabe);
  const schreib = (s) => {
    // The prompts of the custom entries in use travel with the workflow.
    s = { ...s, eigene: eigeneKopie(daten, s.felder, null, s.eigene) };
    schreibeState(node, prop, s);
    zeichne();
  };

  // A profile sheet like the Person and Wardrobe nodes: one row per field,
  // name, what is set, the die; a click opens it. Closed by default, and only
  // one open at a time - which row is open is a matter of view, not a setting,
  // so it lives here and not in the state.
  let offen = null;
  // What is typed into the open field's search; view state like "offen".
  let suche = "";
  let sucheFokus = false;
  const gruppenFeld = daten.gruppenFeld;
  const DETAILS = "__details";
  const leer = (l) => !l || l === daten.leer;
  const beschriftung = (cat, l) => t(l, bereich + "/" + cat);

  // The seed and its "control after generate" only matter for a die. They
  // were a number on every node; now they are hidden and shown in the panel
  // while a field is being rolled.
  const seedWidget = () => node.widgets?.find((w) => w.name === "seed");
  const steuerWidget = () => node.widgets?.find(
    (w) => w.name === "control_after_generate" || w.name === "control_after_generated");
  const versteckeSeed = () => {
    for (const w of [seedWidget(), steuerWidget()]) {
      if (!w) continue;
      if (w._state && !w._state.options?.k2Versteckt) {
        w._state.options = { ...(w._state.options || {}), hidden: true, k2Versteckt: true };
      }
      if (w.options) w.options.hidden = true;
    }
  };

  function chip(text, an, onclick, titel) {
    const c = document.createElement("div");
    c.className = "k2-chip" + (an ? " k2-an" : "");
    c.textContent = text;
    if (titel) c.title = titel;
    c.onclick = onclick;
    return c;
  }

  // The options of one field: family chips over the long field, then the
  // variants as chips. A click on the chosen one clears it.
  function auswahl(state, cat) {
    const teile = [];
    const schluessel = bereich + "/" + cat;
    const setze = (label) => {
      if (!leer(label)) merkeBenutzt(schluessel, label);
      suche = "";
      schreib({ ...state, felder: { ...state.felder, [cat]: label } });
    };
    const lang = (daten.felder[cat] || []).length > LANGE_LISTE;
    const familieVon = (label) =>
      cat === gruppenFeld ? Object.keys(daten.gruppen).find((g) => daten.gruppen[g].includes(label)) : null;
    let eintraege = daten.felder[cat] || [];
    if (cat === gruppenFeld) {
      const fam = document.createElement("div");
      fam.className = "k2-chips";
      for (const g of [daten.alle, ...Object.keys(daten.gruppen)]) {
        fam.append(chip(g === daten.alle ? t("alle", "ui") : t(g, "familien"),
                        (state.gruppe || daten.alle) === g, () => schreib({ ...state, gruppe: g })));
        fam.lastChild.classList.add("k2-fam");
      }
      teile.push(fam);
      if (state.gruppe && state.gruppe !== daten.alle) {
        eintraege = eintraege.filter((e) => daten.gruppen[state.gruppe]?.includes(e.label));
      }
    }
    const box = document.createElement("div");
    box.className = "k2-chips" + (eintraege.length > 12 ? " k2-scroll" : "");
    for (const e of eintraege) {
      const an = state.felder?.[cat] === e.label;
      box.append(chip(beschriftung(cat, e.label), an, () => setze(an ? daten.leer : e.label), e.wert));
      const fam = familieVon(e.label);
      box.lastChild.dataset.suche = [e.label, beschriftung(cat, e.label), e.wert, fam,
                                     fam && t(fam, "familien")].join(" ");
    }
    if (lang) {
      // The recently used ones, then a search that filters the chips in place -
      // typing must not redraw the node, or the field would lose the focus.
      const bekannt = new Set((daten.felder[cat] || []).map((e) => e.label));
      const zuletzt = merkliste("zuletzt", schluessel).filter((l) => bekannt.has(l));
      if (zuletzt.length) {
        const reihe = document.createElement("div");
        reihe.className = "k2-zuletzt";
        const titel = document.createElement("span");
        titel.textContent = t("Zuletzt", "ui");
        reihe.append(titel);
        for (const l of zuletzt) {
          const an = state.felder?.[cat] === l;
          reihe.append(chip(beschriftung(cat, l), an, () => setze(an ? daten.leer : l),
                            daten.felder[cat].find((e) => e.label === l)?.wert));
          reihe.lastChild.classList.add("k2-klein");
        }
        teile.push(reihe);
      }
      const feld = document.createElement("input");
      feld.className = "k2-frei k2-chipsuche";
      feld.type = "search";
      feld.placeholder = t("Suchen …", "ui");
      feld.value = suche;
      const keine = document.createElement("div");
      keine.className = "k2-keine";
      keine.textContent = t("Keine Treffer", "ui");
      const filtere = () => {
        let treffer = 0;
        for (const c of box.children) {
          const zeigen = passtSuche(suche, [c.dataset.suche]);
          c.style.display = zeigen ? "" : "none";
          if (zeigen) treffer++;
        }
        keine.style.display = treffer ? "none" : "";
      };
      feld.oninput = () => { suche = feld.value; filtere(); box.scrollTop = 0; };
      feld.onkeydown = (ev) => {
        if (ev.key === "Enter") {
          ev.preventDefault();
          const erster = suche.trim() && Array.from(box.children).find((c) => c.style.display !== "none");
          if (erster) erster.click();
        } else if (ev.key === "Escape" && suche) {
          ev.preventDefault();
          suche = "";
          feld.value = "";
          filtere();
        }
        ev.stopPropagation();   // typing must not reach the canvas shortcuts
      };
      filtere();
      teile.push(feld);
      if (sucheFokus) {
        sucheFokus = false;
        queueMicrotask(() => feld.focus());
      }
      teile.push(box, keine);
      return teile;
    }
    teile.push(box);
    return teile;
  }

  function wuerfelKnopf(state, cat) {
    const b = document.createElement("span");
    const an = !!state.wuerfeln?.[cat];
    b.className = "k2-wuerfel k2-klein" + (an ? " k2-an" : "");
    b.textContent = "🎲";
    b.title = an
      ? t("wird gewürfelt — klicken für fest", "ui")
      : t("fest — klicken zum Würfeln", "ui");
    b.onclick = (ev) => {
      ev.stopPropagation();
      const w = { ...(state.wuerfeln || {}) };
      if (an) delete w[cat];
      else w[cat] = true;
      schreib({ ...state, wuerfeln: w });
    };
    return b;
  }

  function zeile(state, cat) {
    const istText = cat === DETAILS;
    const istOffen = offen === cat;
    const rollt = !istText && !!state.wuerfeln?.[cat];
    const bereichEl = document.createElement("div");
    bereichEl.className = "k2-bereich" + (istOffen ? " k2-offen" : "");
    const kopf = document.createElement("div");
    kopf.className = "k2-kopf";
    kopf.tabIndex = 0;
    kopf.setAttribute("role", "button");
    kopf.setAttribute("aria-expanded", String(istOffen));
    const chev = document.createElement("span");
    chev.className = "k2-chev";
    chev.textContent = "▶";
    const name = document.createElement("span");
    name.className = "k2-bname";
    name.textContent = istText ? t("Details", "ui") : t(cat, "kategorien");
    const kurz = document.createElement("span");
    const wert = istText ? (state.details || "").trim() : state.felder?.[cat];
    const gesetzt = istText ? !!wert : !leer(wert);
    kurz.className = "k2-kurz" + (gesetzt || rollt ? "" : " k2-leer");
    kurz.textContent = rollt ? t("wird gewürfelt", "ui")
      : !gesetzt ? t("nichts gesetzt", "ui")
      : istText ? wert : beschriftung(cat, wert);
    kurz.title = kurz.textContent;
    kopf.append(chev, name, kurz, istText ? document.createElement("span") : wuerfelKnopf(state, cat));
    const umschalten = () => {
      offen = istOffen ? null : cat;
      suche = "";
      sucheFokus = !istOffen && (daten.felder[cat] || []).length > LANGE_LISTE;
      zeichne();
    };
    kopf.onclick = umschalten;
    kopf.onkeydown = (ev) => {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); umschalten(); }
    };
    bereichEl.append(kopf);
    if (istOffen) {
      const inhalt = document.createElement("div");
      inhalt.className = "k2-inhalt";
      if (istText) {
        const frei = document.createElement("input");
        frei.className = "k2-frei";
        frei.placeholder = t("Weiteres (englisch)", "ui");
        frei.value = state.details || "";
        // Write only on change, otherwise the canvas is redrawn on every
        // keystroke and the node flickers.
        frei.onchange = () => schreib({ ...state, details: frei.value });
        inhalt.append(frei);
        queueMicrotask(() => frei.focus());
      } else {
        inhalt.append(...auswahl(state, cat));
      }
      bereichEl.append(inhalt);
    }
    return bereichEl;
  }

  function zeichne() {
    const state = lies();
    root.textContent = "";
    versteckeSeed();
    const gesetzt = daten.reihenfolge.filter((c) => !leer(state.felder?.[c]) || state.wuerfeln?.[c]).length
      + ((state.details || "").trim() ? 1 : 0);
    root.append(markenleiste(teil,
      gesetzt ? tf("{0} gesetzt", "ui", gesetzt) : t("nichts gesetzt", "ui")));
    const hinweis = eigeneHinweis();
    if (hinweis) root.append(hinweis);

    const liste = document.createElement("div");
    liste.className = "k2-liste k2-panelzeilen";
    for (const cat of daten.reihenfolge) liste.append(zeile(state, cat));
    liste.append(zeile(state, DETAILS));
    root.append(liste);

    // --- the die's seed, only while something is rolled ---------------------
    if (Object.keys(state.wuerfeln || {}).length) {
      const sw = seedWidget(), cw = steuerWidget();
      const reihe = document.createElement("div");
      reihe.className = "k2-schnell k2-seedzeile";
      reihe.append("🎲 " + t("Seed", "ui"));
      const feld = document.createElement("input");
      feld.type = "number";
      feld.min = "0";
      feld.value = String(sw?.value ?? 0);
      feld.onchange = () => { if (sw) sw.value = Math.max(0, parseInt(feld.value, 10) || 0); zeichne(); };
      reihe.append(feld);
      const fest = (cw?.value || "fixed") === "fixed";
      for (const [wert, text] of [["fixed", t("fest", "ui")], ["randomize", t("neu je Lauf", "ui")]]) {
        reihe.append(chip(text, fest === (wert === "fixed"), () => { if (cw) cw.value = wert; zeichne(); }));
        reihe.lastChild.classList.add("k2-klein");
      }
      root.append(reihe);
    }

    // --- live preview ---------------------------------------------------------
    const v = document.createElement("div");
    const text = baueVorschau(daten, state, bereich);
    v.className = "k2-vorschau" + (text ? "" : " k2-leer");
    v.textContent = text || t("nichts gewählt", "ui");
    root.append(v);

    // The node follows its content: small while everything is closed, taller
    // while a row is open.
    requestAnimationFrame(passeHoeheAn);
  }

  const CHROM = 52; // title bar and the output row
  function passeHoeheAn() {
    const h = Math.ceil(root.scrollHeight) + CHROM;
    if (Math.abs((node.size?.[1] || 0) - h) > 2) {
      node.setSize?.([node.size?.[0] || opts.breite, h]);
      node.graph?.setDirtyCanvas?.(true, true);
    }
  }

  // Do not draw straight away: nodeCreated runs before configure(), so we would
  // render with defaults and jump to the loaded state milliseconds later.
  queueMicrotask(zeichne);
  node._k2Zeichne = zeichne;

  const w = node.addDOMWidget("k2_ui", "custom", root, {
    getValue: () => node.properties?.[prop],
    setValue: () => {},
    getMinHeight: () => 60,
    margin: 4,
    serialize: false, // the state hangs off node.properties, not off the widget
  });
  applyAdaptiveCanvasOnly(w);
  return root;
}

// Shared registration for both nodes.
export function registriere(cfg) {
  const { classType, hiddenName, prop, vorgabe, datenSchluessel, breite, teil } = cfg;

  registriereStateInjektion(classType, hiddenName, prop, vorgabe);

  app.registerExtension({
    name: "Krea2." + classType,

    async beforeRegisterNodeDef(nodeType, nodeData) {
      if (nodeData.name !== classType) return;
      // Redraw after a workflow is loaded - configure() may run before or
      // after nodeCreated, depending on the front-end version.
      const orig = nodeType.prototype.onConfigure;
      nodeType.prototype.onConfigure = function (info) {
        // Loaded from a workflow: its saved width stands (see nodeCreated).
        this._k2Geladen = true;
        const r = orig?.apply(this, arguments);
        queueMicrotask(() => this._k2Zeichne?.());
        return r;
      };
    },

    async nodeCreated(node) {
      if (node.comfyClass !== classType) return;
      const presets = await ladePresets();
      if (!presets) return;
      // The panel sets the height to its content; the width only for a new
      // node - a loaded one keeps its saved width.
      if (!node._k2Geladen) node.size = [breite, 240];
      baueNode(node, { daten: presets[datenSchluessel], prop, vorgabe, breite, teil,
                       bereich: datenSchluessel });
    },
  });
}

