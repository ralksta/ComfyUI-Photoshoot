// Interface of the Person Builder.
//
// Its own blueprint rather than panel.mjs, because the person is structurally
// different: 20 fields instead of 6, spread across tabs, plus free text fields
// and a real multiple selection. And deliberately without a seed or dice - a
// person should stay the same across many images.

import {
  applyAdaptiveCanvasOnly,
  injiziereCSS,
  installCanvasZoomPassthrough,
  ladePresets,
  leseState,
  registriereStateInjektion,
  schreibeState,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.0.6";

import { app } from "../../scripts/app.js";

const CLASS_TYPE = "Krea2PersonBuilder";
const HIDDEN = "PersonState";
const PROP = "personState";

const VORGABE = {
  felder: {},
  mehrfach: { skinFeatures: [] },
  texte: { ageExact: "", details: "" },
  sektion: "Grund",
  gruppe: { shoes: "alle" },
};

// A tab entry is either a field name or a list of fields that belong together.
// Where only the fields themselves matter - counting, searching - the nesting is
// of no interest.
const flach = (eintraege) => (eintraege || []).flatMap((e) => (Array.isArray(e) ? e : [e]));

function wertVon(daten, cat, label) {
  if (!label || label === daten.leer) return null;
  return daten.felder[cat]?.find((e) => e.label === label)?.wert ?? null;
}

// Builds the English sentence by the same rules as compose_person(): suffixes
// on skin and eyes, hair colour into the hairstyle template, lip finish before
// the colour, nail colour substituted into the length, "wearing" before the
// shoes.
function baueVorschau(daten, state) {
  const f = state.felder || {};
  const t = state.texte || {};
  const w = (cat) => wertVon(daten, cat, f[cat]);
  const teile = [];

  const typ = w("type");
  if (typ) teile.push(typ);

  // Mirrors MINDESTALTER in person_builder.py - the preview has to show what
  // the prompt will actually say, not what was typed.
  let genau = (t.ageExact || "").replace(/\D/g, "");
  if (genau && Number(genau) < 18) genau = "18";
  if (genau) {
    teile.push(genau + " years old");
  } else if (w("age")) {
    const poss = { "a woman": "her", "a young woman": "her", "a man": "his",
                   "a young man": "his" }[typ] || "their";
    teile.push(w("age").replace("{p}", poss));
  }

  if (w("ethnicity")) teile.push(w("ethnicity"));
  if (w("skinTone")) teile.push(w("skinTone") + " skin");
  if (w("complexion")) teile.push(w("complexion"));

  // Body from top to bottom - the counterweight to being head-heavy.
  for (const cat of ["height", "figure", "shoulders", "bust", "waist",
                     "belly", "hips", "legs"]) {
    if (w(cat)) teile.push(w(cat));
  }

  if (w("hair")) teile.push(w("hair").replace("{c}", w("hairColor") || "").replace(/\s+/g, " ").trim());
  else if (w("hairColor")) teile.push(w("hairColor") + " hair");
  if (w("hairEffect")) teile.push(w("hairEffect"));

  // Face from the shape inwards: contour, cheeks, nose, brows, eyes.
  if (w("faceShape")) teile.push(w("faceShape") + " face");
  if (w("cheekbones")) teile.push(w("cheekbones"));
  if (w("nose")) teile.push(w("nose"));
  if (w("chin")) teile.push(w("chin"));
  if (w("jawline")) teile.push(w("jawline"));
  if (w("browShape")) teile.push(w("browShape"));

  // Eye shape and colour in one phrase, otherwise it would read
  // "almond-shaped eyes, green eyes". Append the word "eyes" only when it is
  // not already in the value - otherwise "one blue and one green eye eyes".
  if (w("eyeShape") || w("eyes")) {
    const satz = [w("eyeShape"), w("eyes")].filter(Boolean).join(" ");
    teile.push(satz.includes("eye") ? satz : satz + " eyes");
  }
  if (w("lashes")) teile.push(w("lashes"));
  if (w("eyeliner")) teile.push(w("eyeliner"));
  if (w("eyeshadow")) teile.push(w("eyeshadow"));

  if (w("lipShape")) teile.push(w("lipShape"));

  if (w("lipColor")) teile.push([w("lipFinish"), w("lipColor"), "lipstick"].filter(Boolean).join(" "));
  else if (w("lipFinish")) teile.push(w("lipFinish") + " lips");
  if (w("blush")) teile.push(w("blush"));
  if (w("makeup")) teile.push(w("makeup"));

  for (const label of state.mehrfach?.skinFeatures || []) {
    const v = wertVon(daten, "skinFeatures", label);
    if (v && !teile.includes(v)) teile.push(v);
  }

  const nl = w("nailLength");
  const nc = w("nailColor");
  if (nl && nc) teile.push(nl.replace("nails", nc + " nails"));
  else if (nl) teile.push(nl);
  else if (nc) teile.push(nc + " nails");

  const frei = (t.details || "").trim().replace(/[,;.\s]+$/, "");
  if (frei) teile.push(frei);

  // Legwear before the shoes, colour in front of it. With bare legs both drop
  // out, otherwise it would read "wearing black bare legs".
  const hos = w("hosiery");
  if (hos === "bare legs") teile.push("bare legs");
  else if (hos) teile.push("wearing " + [w("hosieryColor"), hos].filter(Boolean).join(" "));

  // Shoe colour goes in front in the same way. "barefoot" and the two "no
  // shoes" entries get none - there is nothing to colour there. Has to match
  // SCHUHE_OHNE in person_builder.py, or the preview shows something other than
  // what comes out later.
  const OHNE = ["barefoot", "only sheer stockings, no shoes", "only socks, no shoes"];
  const schuhe = w("shoes");
  if (OHNE.includes(schuhe)) teile.push(schuhe);
  else if (schuhe) teile.push("wearing " + [w("shoesColor"), schuhe].filter(Boolean).join(" "));

  for (const cat of ["jewellery", "eyewear", "headwear"]) {
    if (w(cat)) teile.push("wearing " + w(cat));
  }

  return teile.join(", ");
}

function baue(node, daten) {
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root";
  installCanvasZoomPassthrough(root);

  const lies = () => leseState(node, PROP, VORGABE);
  const schreib = (s) => {
    nachfrage = false;   // any other change withdraws the confirmation
    schreibeState(node, PROP, s);
    zeichne();
  };
  const name = (cat) => uet(daten.namen?.[cat] || cat, "feldnamen");

  // Confirmation before clearing all fields. Deliberately kept here and not in
  // the state - a half-asked question does not belong in the saved workflow, and
  // it should be gone the next time the node is opened.
  let nachfrage = false;

  // Just a field's dropdown, without a label - row groups put several of them
  // side by side under one shared label. "erlaubt" narrows the selection (for
  // shoes: the chosen family).
  function selectFuer(state, cat, erlaubt) {
    const sel = document.createElement("select");
    const leer = document.createElement("option");
    leer.value = daten.leer;
    leer.textContent = daten.leer;
    sel.append(leer);
    for (const e of daten.felder[cat] || []) {
      if (erlaubt && !erlaubt.includes(e.label)) continue;
      const o = document.createElement("option");
      o.value = e.label;
      o.textContent = uet(e.label, "person/" + cat);
      o.title = e.wert;
      sel.append(o);
    }
    const gesetzt = state.felder?.[cat] || daten.leer;
    // If the value there fell through the filter, the dropdown would be empty
    // and would silently jump to the first entry on the next write. So make it
    // visible instead.
    if (gesetzt !== daten.leer && !Array.from(sel.options).some((o) => o.value === gesetzt)) {
      const o = document.createElement("option");
      o.value = gesetzt;
      o.textContent = uet(gesetzt, "person/" + cat);
      sel.append(o);
    }
    sel.value = gesetzt;
    sel.onchange = () =>
      schreib({ ...state, felder: { ...state.felder, [cat]: sel.value } });
    return sel;
  }

  // A label that resets on click. You used to have to open the dropdown and
  // scroll all the way to the top to get rid of a field again.
  function beschriftung(state, text, cats) {
    const lbl = document.createElement("div");
    lbl.className = "k2-name k2-loeschbar";
    lbl.textContent = text;
    lbl.title = uet(
      cats.length > 1 ? "Klicken setzt diese Felder zurück" : "Klicken setzt dieses Feld zurück",
      "ui");
    lbl.onclick = () => {
      const felder = { ...state.felder };
      for (const c of cats) felder[c] = daten.leer;
      schreib({ ...state, felder });
    };
    return lbl;
  }

  function feldSelect(state, cat) {
    const zeile = document.createElement("div");
    zeile.className = "k2-feld";
    zeile.append(beschriftung(state, name(cat), [cat]), selectFuer(state, cat));
    return zeile;
  }

  // Several related fields in one row. Two dropdowns fit next to the label;
  // shoes need three, for family, model and colour, and get the label above them
  // - inline there would be 74 pixels left for each, too little for "stiletto
  // high heels".
  function feldGruppe(state, cats) {
    const titel = daten.zeilennamen?.[cats[0]] || name(cats[0]);
    const mitFamilie = daten.art?.[cats[0]] === "familie";

    const listen = [];
    let erlaubt = null;
    if (mitFamilie) {
      const gruppen = daten.gruppen?.[cats[0]] || {};
      const aktiv = state.gruppe?.[cats[0]] || daten.alle;
      const fam = document.createElement("select");
      for (const g of [daten.alle, ...Object.keys(gruppen)]) {
        const o = document.createElement("option");
        o.value = g;
        o.textContent = g === daten.alle ? uet("alle", "ui") : uet(g, "familien");
        fam.append(o);
      }
      fam.value = aktiv;
      fam.onchange = () =>
        schreib({ ...state, gruppe: { ...state.gruppe, [cats[0]]: fam.value } });
      listen.push(fam);
      if (aktiv !== daten.alle) erlaubt = gruppen[aktiv] || [];
    }
    for (const c of cats) listen.push(selectFuer(state, c, c === cats[0] ? erlaubt : null));

    if (listen.length <= 2) {
      const zeile = document.createElement("div");
      zeile.className = "k2-feld";
      zeile.append(beschriftung(state, titel, cats), ...listen);
      return zeile;
    }
    const block = document.createElement("div");
    block.className = "k2-block";
    const reihe = document.createElement("div");
    reihe.className = "k2-reihe";
    reihe.append(...listen);
    block.append(beschriftung(state, titel, cats), reihe);
    return block;
  }

  function feldText(state, cat) {
    const zeile = document.createElement("div");
    zeile.className = "k2-feld";
    const lbl = document.createElement("div");
    lbl.className = "k2-name k2-loeschbar";
    lbl.textContent = name(cat);
    lbl.title = uet("Klicken leert dieses Feld", "ui");
    lbl.onclick = () => schreib({ ...state, texte: { ...state.texte, [cat]: "" } });
    const inp = document.createElement("input");
    inp.placeholder = uet(daten.platzhalter?.[cat] || "", "platzhalter");
    inp.value = state.texte?.[cat] || "";
    // Write only on change - otherwise the canvas redraws on every keystroke
    // and the node flickers.
    inp.onchange = () =>
      schreib({ ...state, texte: { ...state.texte, [cat]: inp.value } });
    zeile.append(lbl, inp);
    return zeile;
  }

  function feldMehrfach(state, cat) {
    const block = document.createElement("div");
    block.className = "k2-block";
    const lbl = document.createElement("div");
    lbl.className = "k2-name k2-loeschbar";
    lbl.textContent = name(cat);
    lbl.title = uet("Klicken wählt alle ab", "ui");
    lbl.onclick = () => schreib({ ...state, mehrfach: { ...state.mehrfach, [cat]: [] } });
    const chips = document.createElement("div");
    chips.className = "k2-chips";
    const gewaehlt = state.mehrfach?.[cat] || [];
    for (const e of daten.felder[cat] || []) {
      const c = document.createElement("div");
      const an = gewaehlt.includes(e.label);
      c.className = "k2-chip" + (an ? " k2-an" : "");
      c.textContent = uet(e.label, "person/" + cat);
      c.title = e.wert;
      c.onclick = () => {
        const neu = an ? gewaehlt.filter((x) => x !== e.label) : [...gewaehlt, e.label];
        schreib({ ...state, mehrfach: { ...state.mehrfach, [cat]: neu } });
      };
      chips.append(c);
    }
    block.append(lbl, chips);
    return block;
  }

  // How many fields of a tab are set. With 44 fields across six tabs there is
  // otherwise no way to find out where something is set, short of clicking
  // through every tab.
  function zaehle(state, sektion) {
    let n = 0;
    for (const cat of flach(sektion.felder)) {
      const art = daten.art?.[cat] || "select";
      if (art === "text") {
        if ((state.texte?.[cat] || "").trim()) n++;
      } else if (art === "mehrfach") {
        if ((state.mehrfach?.[cat] || []).length) n++;
      } else if (state.felder?.[cat] && state.felder[cat] !== daten.leer) {
        n++;
      }
    }
    return n;
  }

  function zeichne() {
    const state = lies();
    root.textContent = "";

    // --- tabs ----------------------------------------------------------------
    const tabs = document.createElement("div");
    tabs.className = "k2-tabs";
    const aktiv = daten.sektionen.some((s) => s.name === state.sektion)
      ? state.sektion
      : daten.sektionen[0].name;
    for (const s of daten.sektionen) {
      const tab = document.createElement("div");
      tab.className = "k2-tab" + (s.name === aktiv ? " k2-an" : "");
      tab.textContent = uet(s.name, "sektionen");
      const n = zaehle(state, s);
      if (n) {
        const z = document.createElement("sup");
        z.className = "k2-zahl";
        z.textContent = String(n);
        tab.append(z);
      }
      tab.title = n
        ? uetf(n === 1 ? "{0} Feld gesetzt" : "{0} Felder gesetzt", "ui", n)
        : uet("nichts gesetzt", "ui");
      tab.onclick = () => schreib({ ...state, sektion: s.name });
      tabs.append(tab);
    }
    root.append(tabs);

    // --- fields of the active tab --------------------------------------------
    // An entry is either a field name or a list of related fields, which then
    // share a single row.
    const blatt = document.createElement("div");
    blatt.className = "k2-blatt";
    const sektion = daten.sektionen.find((s) => s.name === aktiv);
    for (const eintrag of sektion.felder) {
      if (Array.isArray(eintrag)) {
        blatt.append(feldGruppe(state, eintrag));
        continue;
      }
      const art = daten.art?.[eintrag] || "select";
      if (art === "text") blatt.append(feldText(state, eintrag));
      else if (art === "mehrfach") blatt.append(feldMehrfach(state, eintrag));
      else blatt.append(feldSelect(state, eintrag));
    }
    root.append(blatt);

    // --- warning when there are too many face fields ------------------------
    // Measured: at 4 fields a clean full-body shot, at 12 the composition
    // collapses. Not a gradual degradation but a tipping point - hence a notice
    // here rather than a silent decline in quality.
    const gesetzt = (daten.gesichtsFelder || []).filter(
      (c) => state.felder?.[c] && state.felder[c] !== daten.leer,
    ).length;
    if (gesetzt >= (daten.gesichtHinweisAb ?? 6)) {
      const warn = document.createElement("div");
      warn.className = "k2-name";
      const arg = gesetzt >= (daten.gesichtWarnungAb ?? 9);
      warn.style.color = arg ? "#f66744" : "#a0a0a0";
      warn.style.whiteSpace = "normal";
      const kopfteil = `${gesetzt} ${uet("Gesichtsfelder", "ui")} — `;
      warn.textContent = arg
        ? "\u26a0 " + kopfteil +
          uet("bei Ganzkörper und Totale kippt die Komposition, der Kopf wird zu groß", "ui")
        : kopfteil + uet("für weite Einstellungen reichen vier bis fünf", "ui");
      warn.title =
        uet("Bildmodelle verteilen die Bildfläche ungefähr nach der Gewichtung im ", "ui") +
        uet("Prompt. Viele Gesichtsangaben überstimmen den Hinweis auf die ", "ui") +
        uet("Proportionen. Für Porträts und Nahaufnahmen ist es unkritisch.", "ui");
      root.append(warn);
    }

    // --- reset ---------------------------------------------------------------
    // Both scopes in one row, each with its count in front: you should see what
    // you are losing before you click. The whole node needs a confirmation - 44
    // fields with no undo would otherwise be gone on one misclick.
    {
      const zeile = document.createElement("div");
      zeile.className = "k2-reset";
      const dieses = zaehle(state, sektion);
      const gesamt = daten.sektionen.reduce((n, s) => n + zaehle(state, s), 0);

      const knopf = (text, titel, tun) => {
        const k = document.createElement("span");
        k.className = "k2-reset-knopf";
        k.textContent = text;
        k.title = titel;
        k.onclick = tun;
        return k;
      };

      if (dieses) {
        zeile.append(knopf(`⟲ ${uet(aktiv, "sektionen")} (${dieses})`,
          uetf("Die {0} gesetzten Felder dieser Karte zurücksetzen", "ui", dieses), () => {
            const felder = { ...state.felder }, texte = { ...state.texte },
                  mehrfach = { ...state.mehrfach };
            for (const cat of flach(sektion.felder)) {
              const art = daten.art?.[cat] || "select";
              if (art === "text") texte[cat] = "";
              else if (art === "mehrfach") mehrfach[cat] = [];
              else felder[cat] = daten.leer;
            }
            schreib({ ...state, felder, texte, mehrfach });
          }));
      }
      if (gesamt) {
        zeile.append(nachfrage
          ? knopf(uetf("wirklich alle {0} löschen?", "ui", gesamt),
                  uet("Nochmal klicken bestätigt", "ui"), () => {
              nachfrage = false;
              schreib({ ...VORGABE, felder: {}, mehrfach: { skinFeatures: [] },
                        texte: { ageExact: "", details: "" },
                        sektion: aktiv, gruppe: { shoes: daten.alle } });
            })
          : knopf(`⟲ ${uet("alles", "ui")} (${gesamt})`,
                  uet("Alle Felder des Nodes zurücksetzen", "ui"), () => {
              nachfrage = true;
              zeichne();
            }));
      }
      if (zeile.children.length) root.append(zeile);
    }

    // --- live preview --------------------------------------------------------
    const v = document.createElement("div");
    const text = baueVorschau(daten, state);
    v.className = "k2-vorschau k2-lang" + (text ? "" : " k2-leer");
    v.textContent = text || uet("nichts gewählt", "ui");
    root.append(v);
  }

  queueMicrotask(zeichne);
  node._k2Zeichne = zeichne;

  // The height follows the node, see shooting.mjs.
  const CHROM = 48;
  const w = node.addDOMWidget("k2_person", "custom", root, {
    getValue: () => node.properties?.[PROP],
    setValue: () => {},
    getMinHeight: () => 240,
    getMaxHeight: () => Math.max(240, (node.size?.[1] || 400) - CHROM),
    margin: 4,
    serialize: false,
  });
  applyAdaptiveCanvasOnly(w);
}

registriereStateInjektion(CLASS_TYPE, HIDDEN, PROP, VORGABE);

app.registerExtension({
  name: "Krea2." + CLASS_TYPE,

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== CLASS_TYPE) return;
    const orig = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
      const r = orig?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
  },

  async nodeCreated(node) {
    if (node.comfyClass !== CLASS_TYPE) return;
    const presets = await ladePresets();
    if (!presets?.person) return;
    // The largest tab is make-up at around 206 px; plus tabs, warning,
    // preview, title and output. Only for new nodes - onConfigure restores the
    // saved size for stored workflows.
    node.size = [340, 420];
    baue(node, presets.person);
  },
});

