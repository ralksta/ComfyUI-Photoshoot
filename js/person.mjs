// Interface of the Person Builder, and of the Wardrobe node, which is the same
// interface cut down to the clothing and accessories sections.
//
// Its own blueprint rather than panel.mjs, because the person is structurally
// different: 38 fields instead of 6, in collapsible sections, plus free text fields
// and a real multiple selection. And deliberately without a seed or dice - a
// person should stay the same across many images.

import {
  alsBearbeiten,
  ansicht,
  ansichtKnopf,
  applyAdaptiveCanvasOnly,
  baueWahlBox,
  bausteinZeile,
  bearbeitenKnopf,
  beimEntfernen,
  eigeneHinweis,
  eigeneKopie,
  erzeugeUndVerbinde,
  injiziereCSS,
  installCanvasZoomPassthrough,
  istKompakt,
  labelAusRequisit,
  ladePresets,
  leseState,
  registriereStateInjektion,
  schreibeState,
  markenleiste,
  merkeBenutzt,
  outfitBild,
  outfitBildUrl,
  outfitHauptfarbe,
  passeKompaktAn,
  PROP_ANSICHT,
  presetFehler,
  registriereBauer,
  rendereUndMerke,
  requisitVorschau,
  speichereEigenenEintrag,
  wardrobeVonPerson,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.9.0";

import { app } from "../../scripts/app.js";

// From this length on a field is a searchable list instead of a dropdown.
const LANGE_LISTE = 12;

// The two nodes this interface serves. "sektionen" names the presets key
// that lists the sections to show (all of them when missing).
const PERSON = {
  classType: "Krea2PersonBuilder",
  hidden: "PersonState",
  prop: "personState",
  vorgabe: {
    felder: {},
    mehrfach: { skinFeatures: [] },
    texte: { ageExact: "", details: "", trigger: "", referenz: "" },
    sektion: "Grund",
  },
  teil: "Person",
  sektionen: "personSektionen",
  inspire: true,
  groesse: [360, 560],
};
// The Wardrobe holds all outfits of a shoot as tabs ("mehrere"): the field
// interface below edits the active one. Same shape as DEFAULT_STATE in
// wardrobe.py.
const WARDROBE = {
  classType: "Krea2Wardrobe",
  hidden: "WardrobeState",
  prop: "wardrobeState",
  vorgabe: {
    outfits: [{ id: "o1", name: "", felder: {}, texte: { details: "" } }],
    aktiv: 0,
    sektion: "Kleidung",
    vorschauArt: "puppe",
  },
  teil: "Wardrobe",
  sektionen: "outfitSektionen",
  mehrere: true,
  groesse: [360, 560],
};
const neueOutfitId = () => "o" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

// A section entry is either a field name or a list of fields that belong together.
// Where only the fields themselves matter - counting, searching - the nesting is
// of no interest.
const flach = (eintraege) => (eintraege || []).flatMap((e) => (Array.isArray(e) ? e : [e]));

function wertVon(daten, cat, label, eigene) {
  if (!label || label === daten.leer) return null;
  // Last the copy of a custom entry whose file is missing here (eigeneKopie).
  return daten.felder[cat]?.find((e) => e.label === label)?.wert ?? eigene?.[cat]?.[label] ?? null;
}

// The phrase that names the reference images - referenz_text() in
// person_builder.py, with its wording from /krea2/presets. Image numbers
// ("1", "1, 2") become "the same woman as in <image1> and <image2>", anything
// else is taken as written.
function referenzText(daten, roh, gen) {
  const ref = (roh || "").trim().replace(/[,;.\s]+$/, "");
  if (!ref || !/^[\d\s,;+&/]+$/.test(ref) || !daten.referenzSatz) return ref;
  const nummern = [...new Set((ref.match(/\d+/g) || []).map((n) => String(Number(n))))];
  if (!nummern.length) return "";
  const bilder = nummern.map((n) => daten.referenzBild.replace("{}", n));
  const liste = bilder.length === 1 ? bilder[0] : bilder.slice(0, -1).join(", ") + " and " + bilder[bilder.length - 1];
  const wer = ["woman", "man", "trans woman"].includes(gen) ? gen : "person";
  return daten.referenzSatz.replace("{wer}", wer).replace("{bilder}", liste);
}

// Builds the English sentence by the same rules as compose_person(): suffixes
// on skin and eyes, hair colour into the hairstyle template, lip finish before
// the colour, nail colour substituted into the length, "wearing" before the
// shoes.
function baueVorschau(daten, state, detail = "voll") {
  const f = state.felder || {};
  const t = state.texte || {};
  // With a character LoRA's trigger, face, hair and skin come from the LoRA
  // and stay out - LORA_WEG in person_builder.py. The same with a reference
  // image, which then stands as the subject.
  const trigger = (t.trigger || "").trim().replace(/[,;.\s]+$/, "");
  const mitReferenz = !!(t.referenz || "").trim().replace(/[,;.\s]+$/, "");
  const loraWeg = new Set(trigger || mitReferenz ? daten.loraWeg || [] : []);
  const df = daten.detailFelder || {};
  const erlaubtSet = detail === "figur" ? new Set(df.figur || [])
    : detail === "identitaet" ? new Set(df.identitaet || []) : null;
  const verbotenSet = detail === "oben" ? new Set(df.unten || []) : null;
  const erlaubt = (cat) => {
    const key = cat === "details" ? "free" : cat;
    if (loraWeg.has(cat)) return false;
    if (verbotenSet && verbotenSet.has(key)) return false;
    if (erlaubtSet && !erlaubtSet.has(key)) return false;
    return true;
  };
  const w = (cat) => (erlaubt(cat) ? wertVon(daten, cat, f[cat], state.eigene) : null);
  const teile = [];

  let gen = w("gender") || w("type");
  if (gen === "a young woman" || gen === "young woman") gen = "woman";
  if (gen === "a young man" || gen === "young man") gen = "man";
  if (gen === "a woman") gen = "woman";
  if (gen === "a man") gen = "man";
  if (gen === "a trans woman") gen = "trans woman";
  if (gen === "a person") gen = "person";

  const poss = { woman: "her", "trans woman": "her", man: "his", person: "their" }[gen] || "their";
  const referenz = referenzText(daten, t.referenz, gen);
  if (referenz) teile.push(referenz);

  // Mirrors MINDESTALTER in person_builder.py (delivered as daten.mindestalter) -
  // the preview has to show what the prompt will actually say, not what was typed.
  let genau = erlaubt("ageExact") ? (t.ageExact || "").replace(/\D/g, "") : "";
  const minAlter = Number(daten?.mindestalter) || 0;
  if (minAlter && genau && Number(genau) > 0 && Number(genau) < minAlter) genau = String(minAlter);
  if (genau && Number(genau) > 0) {
    const alter = Number(genau);
    let subjekt = null;
    if (gen === "woman") subjekt = alter < 18 ? "girl" : "woman";
    else if (gen === "trans woman") subjekt = alter < 18 ? "trans girl" : "trans woman";
    else if (gen === "man") subjekt = alter < 18 ? "boy" : "man";
    else if (gen === "person") subjekt = alter < 13 ? "child" : (alter < 18 ? "teenager" : "person");

    if (subjekt && !referenz) {
      const art = ("aeiou8".includes(String(alter)[0]) || [11, 18, 80].includes(alter)) ? "an" : "a";
      teile.push(`${art} ${alter}-year-old ${subjekt}`);
    } else {
      teile.push(alter + " years old");
    }
  } else if (w("age")) {
    const ageVal = w("age");
    if (ageVal === "{child}" && !minAlter) {
      const sub = { woman: "young girl", "trans woman": "young trans girl", man: "young boy", person: "young child" }[gen] || "young child";
      teile.push(sub.startsWith("a") || sub.startsWith("e") || sub.startsWith("i") || sub.startsWith("o") || sub.startsWith("u") ? "an " + sub : "a " + sub);
    } else if (ageVal === "{teen}" && !minAlter) {
      const sub = { woman: "teenage girl", "trans woman": "teenage trans girl", man: "teenage boy", person: "teenager" }[gen] || "teenager";
      teile.push("a " + sub);
    } else if (ageVal === "{child}" || ageVal === "{teen}") {
      if (gen && !referenz) {
        teile.push(gen === "woman" ? "a woman" : (gen === "trans woman" ? "a trans woman" : (gen === "man" ? "a man" : "a person")));
      }
    } else {
      if (gen && !referenz) {
        teile.push(gen === "woman" ? "a woman" : (gen === "trans woman" ? "a trans woman" : (gen === "man" ? "a man" : "a person")));
      }
      teile.push(ageVal.replace("{p}", poss));
    }
  } else if (gen && !referenz) {
    teile.push(gen === "woman" ? "a woman" : (gen === "trans woman" ? "a trans woman" : (gen === "man" ? "a man" : "a person")));
  }
  if (trigger) teile.push(trigger);

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

  for (const label of erlaubt("skinFeatures") ? state.mehrfach?.skinFeatures || [] : []) {
    const v = wertVon(daten, "skinFeatures", label, state.eigene);
    if (v && !teile.includes(v)) teile.push(v);
  }

  const nl = w("nailLength");
  const nc = w("nailColor");
  if (nl && nc) teile.push(nl.replace("nails", nc + " nails"));
  else if (nl) teile.push(nl);
  else if (nc) teile.push(nc + " nails");

  // Top first among the clothes, the bottom joined with "with". Mirrors the
  // same block in compose_person(): colour in front, material between colour
  // and cut unless the cut names its own fabric, no article for plurals.
  const artikel = (s) => {
    const k = s.toLowerCase();
    return (/^(a|e|i|o|u|8|11|18|80)/.test(k) && !/^(uni|use|one)/.test(k) ? "an " : "a ") + s;
  };
  const top = w("top");
  if (top) teile.push("wearing " + artikel([w("topColor"), top].filter(Boolean).join(" ")));
  const unten = w("bottom");
  if (unten) {
    const stoff = /\b(denim|jeans|leather|tulle)\b/.test(unten) ? null : w("bottomMaterial");
    const text = [w("bottomColor"), stoff, unten].filter(Boolean).join(" ");
    const mehrzahl = /\b(shorts|jeans|pants|trousers|leggings)\b/.test(unten);
    teile.push((top ? "with " : "wearing ") + (mehrzahl ? text : artikel(text)));
  }

  const frei = erlaubt("details") ? (t.details || "").trim().replace(/[,;.\s]+$/, "") : "";
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
  if (w("prop")) teile.push(requisitVorschau(daten, w("prop")));
  const propFrei = erlaubt("propText") ? requisitVorschau(daten, t.propText || "") : "";
  if (propFrei) teile.push(propFrei);

  return teile.join(", ");
}

function _zufall(arr) {
  if (!arr || !arr.length) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}

// "Inspire Me": a coherent person from the pools in INSPIRATION
// (person_builder.py, delivered as daten.inspiration). The person fields are
// replaced; what the dice have no say over stays - every text field (the LoRA
// trigger, the free details, whatever is added later) and clothing from an
// older version. Only the exact age goes, since it would beat the rolled age
// range.
function wuerflePersona(daten, stateAktuell) {
  const pools = daten.inspiration || {};
  const valid = (cat, label) =>
    daten.felder?.[cat]?.some((e) => e.label === label) ? label : daten.leer;
  const zieh = (cat, pool) => valid(cat, _zufall(pool));

  // Clothing is the Wardrobe's; old clothing fields in the person stay put.
  const outfit = new Set(daten.outfitFelder || []);
  const f = Object.fromEntries(Object.entries(stateAktuell.felder || {}).filter(([c]) => outfit.has(c)));
  const t = { ...(stateAktuell.texte || {}), ageExact: "" };
  const m = { ...(stateAktuell.mehrfach || {}), skinFeatures: [] };

  f.gender = zieh("gender", pools.gender);
  f.age = zieh("age", pools.age);
  const mann = (pools.maenner || []).includes(f.gender);

  // One archetype keeps skin, hair and eyes plausible together.
  const arch = _zufall(pools.archetypen) || {};
  f.ethnicity = valid("ethnicity", arch.ethnicity);
  for (const cat of ["skinTone", "complexion", "hairColor", "eyes"]) f[cat] = zieh(cat, arch[cat]);
  f.hair = zieh("hair", mann ? arch.hairMann : arch.hair);

  f.height = zieh("height", pools.height);
  f.figure = zieh("figure", mann ? pools.figureMann : pools.figure);
  for (const cat of ["shoulders", "cheekbones", "nose", "eyeShape"]) f[cat] = zieh(cat, pools[cat]);

  if (!mann && Math.random() < (pools.schminkChance ?? 0)) {
    f.lipColor = zieh("lipColor", pools.lipColor);
    f.lipFinish = zieh("lipFinish", pools.lipFinish);
    if (Math.random() < (pools.lidschattenChance ?? 0)) f.eyeshadow = zieh("eyeshadow", pools.eyeshadow);
  }

  if (arch.skinFeatures?.length && Math.random() < (arch.merkmalChance ?? 0)) {
    m.skinFeatures = arch.skinFeatures.filter((l) => valid("skinFeatures", l) !== daten.leer);
  }

  for (const [cat, l] of Object.entries(f)) if (l === daten.leer) delete f[cat];
  return { ...stateAktuell, felder: f, texte: t, mehrfach: m };
}

// Person and Series nodes read the outfits straight from the Wardrobe node's
// state (the person's preview, the series' outfit axis and contact sheet), so
// an edit or rewiring there redraws them.
function serienNeuZeichnen() {
  for (const n of app.graph?._nodes || []) {
    if (n.comfyClass === "Krea2Photoshooting" || n.comfyClass === "Krea2PersonBuilder") n._k2Zeichne?.();
  }
}


// ziel: an element to draw into instead of the node (the Studio sidebar) -
// the same interface on the same state, without the node's widget and zoom
// handling; returns { root, weg } then.
function baue(node, daten, cfg, ziel = null) {
  injiziereCSS();
  const PROP = cfg.prop;
  const sektionen = cfg.sektionen
    ? daten.sektionen.filter((s) => (daten[cfg.sektionen] || []).includes(s.name))
    : daten.sektionen;

  const root = document.createElement("div");
  root.className = "k2-root" + (ziel ? " k2-studio-panel" : "");
  if (!ziel) installCanvasZoomPassthrough(root);

  // Wardrobe: the whole state with every outfit, the active one clamped.
  const liesGanz = () => {
    const g = leseState(node, PROP, cfg.vorgabe);
    if (!Array.isArray(g.outfits) || !g.outfits.length) g.outfits = structuredClone(cfg.vorgabe.outfits);
    g.aktiv = Math.min(Math.max(0, parseInt(g.aktiv, 10) || 0), g.outfits.length - 1);
    return g;
  };
  const lies = () => {
    // The Wardrobe shows the active outfit in the person's shape, so the
    // field interface below works on it unchanged.
    if (cfg.mehrere) {
      const g = liesGanz();
      const o = g.outfits[g.aktiv];
      return { felder: { ...(o.felder || {}) }, mehrfach: {}, eigene: o.eigene,
               texte: { details: o.texte?.details || "", name: o.name || "" },
               sektion: g.sektion, gruppe: g.gruppe || {} };
    }
    const s = leseState(node, PROP, cfg.vorgabe);
    if (s.felder && s.felder.type && !s.felder.gender) {
      if (s.felder.type === "Junge Frau") {
        s.felder.gender = "Frau";
        if (!s.felder.age || s.felder.age === daten.leer) s.felder.age = "Anfang 20";
      } else if (s.felder.type === "Junger Mann") {
        s.felder.gender = "Mann";
        if (!s.felder.age || s.felder.age === daten.leer) s.felder.age = "Anfang 20";
      } else {
        s.felder.gender = s.felder.type;
      }
      delete s.felder.type;
    }
    if (s.felder?.age && s.felder.age !== daten.leer
        && !(daten.felder?.age || []).some((e) => e.label === s.felder.age)) {
      s.felder.age = daten.leer;
    }
    return s;
  };
  const schreibGanz = (g) => {
    schreibeState(node, PROP, g);
    zeichne();
    serienNeuZeichnen();
  };
  const schreib = (s) => {
    nachfrage = false;   // any other change withdraws the confirmation
    frageBereich = null;
    frageInspire = false;
    offeneFarbe = null;
    offeneWahl = null;
    wahlSuche = "";
    frageOutfit = false;
    // The prompts of the custom entries in use travel with the workflow.
    const eigene = eigeneKopie(daten, s.felder, s.mehrfach, s.eigene);
    if (cfg.mehrere) {
      const g = liesGanz();
      const o = g.outfits[g.aktiv];
      g.outfits[g.aktiv] = { ...o, name: s.texte?.name ?? o.name ?? "", felder: s.felder || {},
                             texte: { details: s.texte?.details || "" }, eigene };
      schreibGanz({ ...g, sektion: s.sektion, gruppe: s.gruppe || {} });
      return;
    }
    schreibeState(node, PROP, { ...s, eigene });
    zeichne();
  };
  // The person without her old clothing fields.
  function ohneKleidung(state, alt) {
    const felder = { ...state.felder };
    for (const c of alt) delete felder[c];
    return { ...state, felder, texte: { ...state.texte, details: "" } };
  }
  // Old clothing into a Wardrobe: the wired one gets it as a new tab, or a new
  // Wardrobe node appears to the left and is wired in. Then the person drops it.
  function inWardrobeUebernehmen(state, alt, altText) {
    const outfit = {
      id: "o" + Date.now().toString(36), name: uet("Aus der Person", "ui"),
      felder: Object.fromEntries(alt.map((c) => [c, state.felder[c]])), texte: { details: altText },
      eigene: state.eigene,
    };
    let w = wardrobeVonPerson(node);
    let st;
    if (w) {
      try { st = JSON.parse(w.properties?.wardrobeState || "{}"); } catch (e) { st = {}; }
      const outfits = [...(Array.isArray(st.outfits) ? st.outfits : []), outfit];
      st = { sektion: "Kleidung", ...st, outfits, aktiv: outfits.length - 1 };
    } else {
      w = globalThis.LiteGraph.createNode("Krea2Wardrobe");
      w.pos = [node.pos[0] - 400, node.pos[1]];
      app.graph.add(w);
      st = { outfits: [outfit], aktiv: 0, sektion: "Kleidung", vorschauArt: "puppe" };
      w.connect(0, node, node.inputs.findIndex((i) => i.name === "garderobe"));
    }
    w.properties = w.properties || {};
    w.properties.wardrobeState = JSON.stringify(st);
    w._k2Zeichne?.();
    schreib(ohneKleidung(state, alt));
  }

  // Wardrobe: rendering the active outfit's preview, and its status line; the
  // half-asked "delete this outfit?".
  let vorschauStatus = null;
  let frageOutfit = false;
  const name = (cat) => uet(daten.namen?.[cat] || cat, "feldnamen");
  const leer = daten.leer;
  const gesetzt = (state, cat) => !!state.felder?.[cat] && state.felder[cat] !== leer;
  const label = (cat, lbl) => uet(lbl, "person/" + cat);
  const wertVonLabel = (cat, lbl) =>
    (daten.felder[cat] || []).find((e) => e.label === lbl)?.wert ?? null;
  const istFarbe = (cat) => !!daten.farben?.[cat];

  // Confirmations before clearing. Deliberately kept here and not in the state -
  // a half-asked question does not belong in the saved workflow, and it should
  // be gone the next time the node is opened.
  let nachfrage = false;       // "everything"
  let frageInspire = false;    // Inspire Me over a filled person
  let frageBereich = null;     // the × of one section
  // The colour field whose palette is open. Also not state: an open palette
  // is a moment, not a setting.
  let offeneFarbe = null;
  // The long list that is open, and what has been typed into its search -
  // a moment as well, so also not state.
  let offeneWahl = null;
  let wahlSuche = "";

  // The fields of a section including those hanging under another field (the
  // material under the bottom).
  const alleFelder = (sektion) =>
    flach(sektion.felder).flatMap((c) => (daten.unter?.[c] ? [c, daten.unter[c]] : [c]));

  // Cuts that name their own fabric ignore the material - same rule as
  // _EIGENER_STOFF in person_builder.py, which is where the pattern comes from.
  const eigenerStoff = new RegExp(daten.eigenerStoff || "$^");
  const stoffIgnoriert = (state, cat) =>
    eigenerStoff.test(wertVonLabel(cat, state.felder?.[cat]) || "");

  // The colour the prompt drops anyway: legwear colour with bare legs, shoe
  // colour with no shoes. Returns the label of the reason, or null.
  function farbeEntfaellt(state, cat) {
    const regel = daten.farbeEntfaellt?.[cat];
    if (!regel) return null;
    const [feld, werte] = regel;
    return werte.includes(wertVonLabel(feld, state.felder?.[feld])) ? state.felder[feld] : null;
  }

  // Every dropdown uses the same styled button and floating list. Short lists
  // (<= LANGE_LISTE) open slim without search or shortlists; long ones keep
  // search, favourites, recent entries and hover thumbnails.
  function selectFuer(state, cat) {
    return wahlKnopf(state, cat);
  }

  function wahlKnopf(state, cat) {
    const k = document.createElement("button");
    k.type = "button";
    k.className = "k2-wahlknopf";
    k.dataset.feld = cat;
    const wert = state.felder?.[cat] || leer;
    const text = document.createElement("span");
    text.textContent = wert === leer ? leer : label(cat, wert);
    k.append(text);
    if (wert === leer) k.classList.add("k2-leer");
    k.title = wert === leer ? "" : (wertVonLabel(cat, wert) || "");
    k.setAttribute("aria-expanded", String(offeneWahl === cat));
    if (offeneWahl === cat) k.classList.add("k2-offen");
    const istLang = (daten.felder[cat] || []).length > LANGE_LISTE;
    k.onclick = (ev) => {
      ev.stopPropagation();
      offeneFarbe = null;
      offeneWahl = offeneWahl === cat ? null : cat;
      wahlSuche = "";
      zeichne();
      if (offeneWahl) {
        (istLang ? root.querySelector(".k2-wahlbox .k2-suche")
          : root.querySelector(".k2-wahlbox .k2-eintrag.k2-an .k2-eintrag-name")
            || root.querySelector(".k2-wahlbox .k2-eintrag-name"))?.focus();
      }
    };
    return k;
  }

  function wahlBox(state, cat) {
    const eintraege = daten.felder[cat] || [];
    const istLang = eintraege.length > LANGE_LISTE;
    const schluessel = "person/" + cat;
    const zumKnopf = () => root.querySelector(`.k2-wahlknopf[data-feld="${cat}"]`)?.focus();
    return baueWahlBox({
      feld: cat,
      eintraege,
      aktiv: state.felder?.[cat] || leer,
      leer,
      schluessel,
      beschriftung: (lbl) => label(cat, lbl),
      gruppen: daten.art?.[cat] === "familie" ? daten.gruppen?.[cat] : null,
      wahlSuche,
      mitSuche: istLang,
      onSuche: (v) => { wahlSuche = v; },
      onWaehle: (lbl) => {
        if (lbl !== leer && istLang) merkeBenutzt(schluessel, lbl);
        schreib({ ...state, felder: { ...state.felder, [cat]: lbl } });
        zumKnopf();
      },
      onFavorit: () => {
        zeichne();
        const neu = root.querySelector(".k2-wahlbox .k2-suche");
        neu?.focus();
        neu?.setSelectionRange(neu.value.length, neu.value.length);
      },
      onSchliessen: () => { offeneWahl = null; wahlSuche = ""; zeichne(); zumKnopf(); },
    });
  }


  // A label that resets on click. You used to have to open the dropdown and
  // scroll all the way to the top to get rid of a field again.
  function beschriftung(state, text, cats, klasse = "") {
    const lbl = document.createElement("div");
    lbl.className = "k2-name k2-loeschbar " + klasse;
    lbl.textContent = text;
    lbl.title = uet(
      cats.length > 1 ? "Klicken setzt diese Felder zurück" : "Klicken setzt dieses Feld zurück",
      "ui");
    lbl.onclick = () => {
      const felder = { ...state.felder };
      for (const c of cats) felder[c] = leer;
      schreib({ ...state, felder });
    };
    return lbl;
  }

  function schalteFarbe(cat) {
    offeneWahl = null;
    wahlSuche = "";
    offeneFarbe = offeneFarbe === cat ? null : cat;
    zeichne();
    // Focus on the chosen colour, or on "no colour" when none is set.
    if (offeneFarbe) (root.querySelector(".k2-palette .k2-an") || root.querySelector(".k2-palette .k2-punkt"))?.focus();
  }

  // One swatch button per colour field. The palette floats below the row.
  function farbKnopf(state, cat) {
    const k = document.createElement("button");
    k.type = "button";
    k.className = "k2-farbknopf";
    k.dataset.farbe = cat;
    const fuellung = document.createElement("span");
    fuellung.className = "k2-farbfuellung";
    k.append(fuellung);
    const grund = farbeEntfaellt(state, cat);
    if (grund) {
      k.disabled = true;
      k.classList.add("k2-ohne");
      k.title = uetf("Keine Farbe bei {0}", "ui", label(daten.farbeEntfaellt[cat][0], grund));
      return k;
    }
    const aktiv = state.felder?.[cat] || leer;
    if (aktiv === leer) k.classList.add("k2-ohne");
    else fuellung.style.background = daten.farben[cat][aktiv] || "#777";
    k.title = aktiv === leer ? uet("Farbe wählen", "ui") : label(cat, aktiv);
    k.setAttribute("aria-label", k.title);
    k.setAttribute("aria-expanded", String(offeneFarbe === cat));
    if (offeneFarbe === cat) k.classList.add("k2-offen");
    k.onclick = (ev) => {
      ev.stopPropagation();
      schalteFarbe(cat);
    };
    return k;
  }

  function palette(state, cat) {
    const pal = document.createElement("div");
    pal.className = "k2-palette";
    pal.dataset.farbe = cat;
    const aktiv = state.felder?.[cat] || leer;
    const kopf = document.createElement("div");
    kopf.className = "k2-palette-kopf";
    const titel = document.createElement("span");
    titel.textContent = name(cat);
    const zeige = document.createElement("span");
    zeige.className = "k2-palette-name";
    const ruhe = aktiv === leer ? uet("keine Farbe", "ui") : label(cat, aktiv);
    zeige.textContent = ruhe;
    kopf.append(titel, zeige);
    const raster = document.createElement("div");
    raster.className = "k2-raster";
    const punkt = (lbl, css, text) => {
      const p = document.createElement("button");
      p.type = "button";
      p.className = "k2-punkt" + (lbl === aktiv ? " k2-an" : "") + (lbl === leer ? " k2-nichts" : "");
      if (css) p.style.background = css;
      p.title = text;
      p.setAttribute("aria-label", text);
      p.onmouseenter = p.onfocus = () => { zeige.textContent = text; };
      p.onmouseleave = p.onblur = () => { zeige.textContent = ruhe; };
      p.onclick = (ev) => {
        ev.stopPropagation();
        schreib({ ...state, felder: { ...state.felder, [cat]: lbl } });
        root.querySelector(`.k2-farbknopf[data-farbe="${cat}"]`)?.focus();
      };
      raster.append(p);
    };
    punkt(leer, null, uet("keine Farbe", "ui"));
    for (const e of daten.felder[cat] || []) punkt(e.label, daten.farben[cat][e.label], label(cat, e.label));
    // Arrow keys walk the grid, Escape closes and returns to the button.
    raster.onkeydown = (ev) => {
      const punkte = Array.from(raster.children);
      const i = punkte.indexOf(document.activeElement);
      const spalten = 8;
      const schritt = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: spalten, ArrowUp: -spalten }[ev.key];
      if (schritt && i >= 0) {
        ev.preventDefault();
        punkte[Math.max(0, Math.min(punkte.length - 1, i + schritt))].focus();
      } else if (ev.key === "Escape") {
        ev.preventDefault();
        offeneFarbe = null;
        zeichne();
        root.querySelector(`.k2-farbknopf[data-farbe="${cat}"]`)?.focus();
      }
    };
    pal.append(kopf, raster);
    return pal;
  }

  // A row: label, styled dropdowns, colour buttons. Standalone colour fields
  // (skin tone, eyeshadow) carry the same styled button next to the swatch.
  // Each row anchors its floating popover directly beneath itself.
  function feldZeile(state, cats) {
    const erst = cats[0];
    const stueck = document.createElement("div");
    stueck.className = "k2-stueck";
    const haupt = document.createElement("div");
    haupt.className = "k2-stueck";
    const zeile = document.createElement("div");
    zeile.className = "k2-feld";
    const zeilenname = daten.zeilennamen?.[erst];
    zeile.append(beschriftung(state, zeilenname ? uet(zeilenname, "feldnamen") : name(erst), cats));
    for (const c of cats) zeile.append(istFarbe(c) ? farbKnopf(state, c) : selectFuer(state, c));
    if (cats.length === 1 && istFarbe(erst)) {
      const k = document.createElement("button");
      k.type = "button";
      const an = gesetzt(state, erst);
      k.className = "k2-wahlknopf" + (an ? "" : " k2-leer") + (offeneFarbe === erst ? " k2-offen" : "");
      k.setAttribute("aria-expanded", String(offeneFarbe === erst));
      const t = document.createElement("span");
      t.textContent = an ? label(erst, state.felder[erst]) : leer;
      k.append(t);
      k.onclick = (ev) => { ev.stopPropagation(); schalteFarbe(erst); };
      zeile.append(k);
    }
    haupt.append(zeile);
    for (const c of cats) if (offeneFarbe === c) haupt.append(palette(state, c));
    for (const c of cats) if (offeneWahl === c) haupt.append(wahlBox(state, c));
    stueck.append(haupt);

    const unter = daten.unter?.[erst];
    if (unter) {
      const unterBlock = document.createElement("div");
      unterBlock.className = "k2-stueck";
      const z = document.createElement("div");
      z.className = "k2-feld";
      z.append(beschriftung(state, "↳ " + name(unter), [unter], "k2-unterfeld"));
      const sel = selectFuer(state, unter);
      z.append(sel);
      unterBlock.append(z);
      if (offeneWahl === unter) unterBlock.append(wahlBox(state, unter));
      if (gesetzt(state, unter) && gesetzt(state, erst) && stoffIgnoriert(state, erst)) {
        sel.classList.add("k2-ignoriert");
        const notiz = document.createElement("div");
        notiz.className = "k2-notiz";
        notiz.textContent = uetf("{0} nennt seinen eigenen Stoff – das Material bleibt aus dem Prompt",
                                 "ui", label(erst, state.felder[erst]));
        unterBlock.append(notiz);
      }
      stueck.append(unterBlock);
    }
    return stueck;
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
    const stueck = document.createElement("div");
    stueck.className = "k2-stueck";
    stueck.append(zeile);
    if (cat === "propText") {
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "k2-textknopf";
      saveBtn.textContent = "+";
      saveBtn.title = uet("Als eigene Vorgabe speichern", "ui");
      saveBtn.setAttribute("aria-label", saveBtn.title);
      saveBtn.onmousedown = (ev) => ev.preventDefault();
      saveBtn.onclick = async (ev) => {
        ev.stopPropagation();
        const raw = inp.value.trim();
        if (!raw) { inp.focus(); return; }
        const eigenLabel = labelAusRequisit(raw) || raw.slice(0, 40);
        saveBtn.disabled = true;
        try {
          const savedLabel = await speichereEigenenEintrag({
            builder: "person", field: "prop", label: eigenLabel, prompt: raw,
          });
          const aktuell = lies();
          schreib({
            ...aktuell,
            felder: { ...(aktuell.felder || {}), prop: savedLabel },
            texte: { ...(aktuell.texte || {}), propText: "" },
          });
        } catch (err) {
          saveBtn.disabled = false;
          let errEl = stueck.querySelector(".k2-notiz");
          if (!errEl) {
            errEl = document.createElement("div");
            errEl.className = "k2-notiz";
            stueck.append(errEl);
          }
          errEl.textContent = err?.message || String(err);
        }
      };
      zeile.append(saveBtn);
    }
    return stueck;
  }

  function feldMehrfach(state, cat) {
    const block = document.createElement("div");
    block.className = "k2-block k2-stueck";
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
      c.textContent = label(cat, e.label);
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

  // How many fields of a section are set.
  function zaehle(state, sektion) {
    let n = 0;
    for (const cat of alleFelder(sektion)) {
      const art = daten.art?.[cat] || "select";
      if (art === "text") {
        if ((state.texte?.[cat] || "").trim()) n++;
      } else if (art === "mehrfach") {
        if ((state.mehrfach?.[cat] || []).length) n++;
      } else if (gesetzt(state, cat)) {
        n++;
      }
    }
    return n;
  }

  // What a closed section shows: the labels of what is set, in field order. A
  // colour gets no word of its own but a dot in front of what it colours; it
  // stands alone with its name only when nothing else in its row is set. The
  // material rides on the bottom in brackets. Labels that occur twice ("athletic"
  // figure and shoulders) get their field name.
  // Fields a character LoRA's trigger or a reference image takes over
  // (LORA_WEG in Python).
  const viaLora = (state) => new Set((state.texte?.trigger || "").trim() || (state.texte?.referenz || "").trim()
    ? daten.loraWeg || [] : []);

  function kurzfassung(state, sektion) {
    const teile = [];
    const weg = viaLora(state);
    for (const eintrag of sektion.felder) {
      const cats = (Array.isArray(eintrag) ? eintrag : [eintrag]).filter((c) => !weg.has(c));
      if (!cats.length) continue;
      const farbe = cats.find((c) => istFarbe(c) && gesetzt(state, c) && !farbeEntfaellt(state, c));
      const punkt = farbe ? daten.farben[farbe][state.felder[farbe]] : null;
      const dinge = cats.filter((c) => !istFarbe(c));
      // Colour first in its row (lips + finish): "Dusty rose, matte".
      if (farbe && cats[0] === farbe) {
        const rest = dinge.filter((c) => gesetzt(state, c)).map((c) => label(c, state.felder[c]).toLowerCase());
        teile.push({ text: [label(farbe, state.felder[farbe]), ...rest].join(", "), punkt, feld: farbe });
        continue;
      }
      let vergeben = false;
      for (const cat of dinge) {
        const art = daten.art?.[cat] || "select";
        if (art === "text") {
          const t = (state.texte?.[cat] || "").trim();
          if (t) teile.push({ text: cat === "ageExact" ? t : "“" + t + "”" });
        } else if (art === "mehrfach") {
          for (const l of state.mehrfach?.[cat] || []) teile.push({ text: label(cat, l) });
        } else if (gesetzt(state, cat)) {
          let text = label(cat, state.felder[cat]);
          const u = daten.unter?.[cat];
          if (u && gesetzt(state, u) && !stoffIgnoriert(state, cat)) {
            text += " (" + label(u, state.felder[u]).toLowerCase() + ")";
          }
          teile.push({ text, feld: cat, punkt: vergeben ? null : punkt });
          vergeben = true;
        }
      }
      if (farbe && !vergeben) teile.push({ text: label(farbe, state.felder[farbe]), punkt, feld: farbe });
    }
    const anzahl = {};
    for (const t of teile) anzahl[t.text] = (anzahl[t.text] || 0) + 1;
    for (const t of teile) {
      if (anzahl[t.text] > 1 && t.feld) t.text += " (" + name(t.feld).toLowerCase() + ")";
    }
    return teile;
  }

  // The parts of a summary into an element: "·" between them, a colour dot
  // in front of what it colours.
  function haengeKurzAn(el, teile) {
    teile.forEach((t, i) => {
      if (i) {
        const trenner = document.createElement("i");
        trenner.textContent = "·";
        el.append(trenner);
      }
      if (t.punkt) {
        const d = document.createElement("b");
        d.className = "k2-mini";
        d.style.background = t.punkt;
        el.append(d);
      }
      el.append(t.text);
    });
  }

  function leereBereich(state, sektion) {
    const felder = { ...state.felder }, texte = { ...state.texte },
          mehrfach = { ...state.mehrfach };
    for (const cat of alleFelder(sektion)) {
      const art = daten.art?.[cat] || "select";
      if (art === "text") texte[cat] = "";
      else if (art === "mehrfach") mehrfach[cat] = [];
      else felder[cat] = leer;
    }
    schreib({ ...state, felder, texte, mehrfach });
  }

  // Measured: at 4 face fields a clean full-body shot, at 12 the composition
  // collapses. Not a gradual degradation but a tipping point - hence a notice
  // right under the Face row rather than a silent decline in quality.
  function gesichtsWarnung(state) {
    const n = (daten.gesichtsFelder || []).filter((c) => gesetzt(state, c)).length;
    if (n < (daten.gesichtHinweisAb ?? 6)) return null;
    const arg = n >= (daten.gesichtWarnungAb ?? 9);
    const warn = document.createElement("div");
    warn.className = "k2-gesicht" + (arg ? " k2-arg" : "");
    const kopfteil = `${n} ${uet("Gesichtsfelder", "ui")} — `;
    warn.textContent = arg
      ? "⚠ " + kopfteil +
        uet("bei Ganzkörper und Totale kippt die Komposition, der Kopf wird zu groß", "ui")
      : kopfteil + uet("für weite Einstellungen reichen vier bis fünf", "ui");
    warn.title =
      uet("Bildmodelle verteilen die Bildfläche ungefähr nach der Gewichtung im ", "ui") +
      uet("Prompt. Viele Gesichtsangaben überstimmen den Hinweis auf die ", "ui") +
      uet("Proportionen. Für Porträts und Nahaufnahmen ist es unkritisch.", "ui");
    return warn;
  }

  // "Inspire Me". A filled person is not thrown away on one click: from more
  // than three fields it asks first, like "everything" does. Text fields the
  // dice keep (the LoRA trigger and any other but the exact age) do not count.
  function inspireKnopf(state, gesamt) {
    const bleibt = sektionen.flatMap(alleFelder).filter((c) =>
      daten.art?.[c] === "text" && c !== "ageExact" && (state.texte?.[c] || "").trim()).length;
    const ersetzt = gesamt - bleibt;
    const inspireBtn = document.createElement("button");
    inspireBtn.type = "button";
    inspireBtn.className = "k2-inspire-btn" + (frageInspire ? " k2-frage" : "");
    if (frageInspire) {
      inspireBtn.textContent = "🎲 " + uetf("{0} Felder ersetzen?", "ui", ersetzt);
      inspireBtn.title = uet("Nochmal klicken bestätigt", "ui");
      inspireBtn.onclick = () => schreib(wuerflePersona(daten, state));
    } else {
      inspireBtn.textContent = "🎲 " + uet("Inspire Me", "ui");
      inspireBtn.title = uet("Stimmige Person auswürfeln", "ui");
      inspireBtn.onclick = () => {
        if (ersetzt > 3) {
          frageInspire = true;
          nachfrage = false;
          frageBereich = null;
          zeichne();
        } else {
          schreib(wuerflePersona(daten, state));
        }
      };
    }
    return inspireBtn;
  }

  // Wardrobe: one tab per outfit with its colour, + for a new one.
  function outfitReiter(ganz) {
    const reiter = document.createElement("div");
    reiter.className = "k2-reiter";
    ganz.outfits.forEach((o, i) => {
      const r = document.createElement("button");
      r.type = "button";
      r.className = "k2-reiter-tab" + (i === ganz.aktiv ? " k2-an" : "");
      const punkt = document.createElement("b");
      punkt.className = "k2-mini";
      punkt.style.background = outfitHauptfarbe(daten, o, "transparent");
      r.append(punkt, (o.name || "").trim() || uetf("Outfit {0}", "ui", i + 1));
      r.onclick = () => { vorschauStatus = null; frageOutfit = false; schreibGanz({ ...ganz, aktiv: i }); };
      reiter.append(r);
    });
    const neu = document.createElement("button");
    neu.type = "button";
    neu.className = "k2-reiter-tab k2-reiter-neu";
    neu.textContent = "+";
    neu.title = uet("Neues Outfit", "ui");
    neu.onclick = () => schreibGanz({ ...ganz, aktiv: ganz.outfits.length,
      outfits: [...ganz.outfits, { id: neueOutfitId(), name: "", felder: {}, texte: { details: "" } }] });
    reiter.append(neu);
    return reiter;
  }

  // The compact view: slim layout without the duplicate brand strip, the
  // Wardrobe's tabs, the summaries of all sections in one run, and the way
  // to the editor - the Studio sidebar, or this node expanded.
  function zeichneKompakt(state, gesamt, hinweis, ganz) {
    const block = document.createElement("div");
    block.className = "k2-kompakt-inhalt";
    const aktionen = document.createElement("div");
    aktionen.className = "k2-kompakt-aktionen";
    aktionen.append(bearbeitenKnopf(node), ansichtKnopf(node));
    const text = document.createElement("div");
    const teile = sektionen.flatMap((s) => kurzfassung(state, s));
    text.className = "k2-kurzfassung" + (teile.length ? "" : " k2-leer");
    if (teile.length) haengeKurzAn(text, teile);
    else text.textContent = uet("nichts gesetzt", "ui");
    if (ganz) {
      const kopf = document.createElement("div");
      kopf.className = "k2-kompakt-kopf";
      const reiter = outfitReiter(ganz);
      reiter.style.margin = "0";
      kopf.append(reiter, aktionen);
      block.append(kopf);
      if (hinweis) block.append(hinweis);
      block.append(alsBearbeiten(text, node));
    } else {
      if (hinweis) block.append(hinweis);
      block.append(alsBearbeiten(text, node));
      const knoepfe = document.createElement("div");
      knoepfe.className = "k2-kompakt-knoepfe";
      if (cfg.inspire) knoepfe.append(inspireKnopf(state, gesamt));
      knoepfe.append(aktionen);
      block.append(knoepfe);
    }
    root.append(block);
    passeKompaktAn(node, root);
  }

  function zeichne() {
    folge.gezeichnet();
    const state = lies();
    root.textContent = "";
    const gesamt = sektionen.reduce((n, s) => n + zaehle(state, s), 0);

    // --- brand strip ---------------------------------------------------------
    const ganz = cfg.mehrere ? liesGanz() : null;
    const hinweis = eigeneHinweis();
    const kompakt = !ziel && istKompakt(node);
    root.classList.toggle("k2-kompakt", kompakt);
    if (kompakt) {
      zeichneKompakt(state, gesamt, hinweis, ganz);
      return;
    }
    const marke = markenleiste(cfg.teil, ganz
      ? (ganz.outfits.length === 1 ? uet("1 Outfit", "ui") : uetf("{0} Outfits", "ui", ganz.outfits.length))
      : gesamt ? uetf("{0} gesetzt", "ui", gesamt) : uet("nichts gesetzt", "ui"), ziel ? null : node);
    root.append(marke);
    if (hinweis) root.append(hinweis);
    if (!cfg.mehrere) {
      root.append(bausteinZeile({
        key: node,
        art: "person",
        zeichne,
        leseAktuell: () => {
          const st = lies();
          return { text: baueVorschau(daten, st, "voll"), state: st };
        },
        wendeAn: (eintrag) => {
          if (eintrag.state && typeof eintrag.state === "object") {
            schreib({ ...structuredClone(cfg.vorgabe), ...eintrag.state });
          } else {
            schreib({ ...structuredClone(cfg.vorgabe),
                      texte: { ...cfg.vorgabe.texte, details: eintrag.text || "" } });
          }
        },
      }));
    }
    // First run: an empty person says where to begin.
    if (!cfg.mehrere && !gesamt) {
      const start = document.createElement("div");
      start.className = "k2-anotiz k2-erststart";
      start.textContent = uet("Neu hier? 🎲 Inspire Me würfelt eine stimmige Person — oder einen Bereich aufklappen und selbst wählen. Jedes Feld ist optional.", "ui");
      root.append(start);
    }

    // --- outfit tabs (Wardrobe) ----------------------------------------------
    // One tab per outfit with its colour, + for a new one.
    if (ganz) root.append(outfitReiter(ganz));

    // --- outfit name (Wardrobe) ----------------------------------------------
    // The name the contact sheet shows for this outfit; without one the series
    // counts ("Outfit 2").
    if (ganz) {
      const o = ganz.outfits[ganz.aktiv];
      const zeile = document.createElement("div");
      zeile.className = "k2-feld k2-outfitname";
      const lbl = document.createElement("div");
      lbl.className = "k2-name";
      lbl.textContent = uet("Name", "ui");
      const inp = document.createElement("input");
      inp.placeholder = uet("z. B. Casual, Abend, Strand", "ui");
      inp.value = state.texte?.name || "";
      inp.onchange = () => schreib({ ...state, texte: { ...state.texte, name: inp.value } });
      // Duplicate: the start for a variant ("Abend" in red). Delete: never the
      // last outfit, and only on a second click.
      const kopie = document.createElement("button");
      kopie.type = "button";
      kopie.className = "k2-textknopf";
      kopie.textContent = "⧉";
      kopie.title = uet("Outfit duplizieren", "ui");
      kopie.onclick = () => {
        const neu = { ...structuredClone(o), id: neueOutfitId(),
                      name: o.name ? o.name + " 2" : "" };
        const outfits = [...ganz.outfits];
        outfits.splice(ganz.aktiv + 1, 0, neu);
        schreibGanz({ ...ganz, outfits, aktiv: ganz.aktiv + 1 });
      };
      zeile.append(lbl, inp);
      if (ganz.outfits.length > 1) {
        const verschiebe = (dir) => {
          const j = ganz.aktiv + dir;
          if (j < 0 || j >= ganz.outfits.length) return;
          const outfits = [...ganz.outfits];
          [outfits[ganz.aktiv], outfits[j]] = [outfits[j], outfits[ganz.aktiv]];
          schreibGanz({ ...ganz, outfits, aktiv: j });
        };
        const links = document.createElement("button");
        links.type = "button";
        links.className = "k2-textknopf";
        links.textContent = "‹";
        links.disabled = ganz.aktiv === 0;
        links.title = uet("Nach links verschieben", "ui");
        links.onclick = () => verschiebe(-1);
        const rechts = document.createElement("button");
        rechts.type = "button";
        rechts.className = "k2-textknopf";
        rechts.textContent = "›";
        rechts.disabled = ganz.aktiv === ganz.outfits.length - 1;
        rechts.title = uet("Nach rechts verschieben", "ui");
        rechts.onclick = () => verschiebe(1);
        zeile.append(links, rechts);
      }
      zeile.append(kopie);
      if (ganz.outfits.length > 1) {
        const weg = document.createElement("button");
        weg.type = "button";
        weg.className = "k2-textknopf" + (frageOutfit ? " k2-frage" : "");
        weg.textContent = frageOutfit ? uet("löschen?", "ui") : "×";
        weg.title = frageOutfit ? uet("Nochmal klicken bestätigt", "ui") : uet("Outfit löschen", "ui");
        weg.onclick = () => {
          if (!frageOutfit) { frageOutfit = true; zeichne(); return; }
          frageOutfit = false;
          const outfits = ganz.outfits.filter((_, i) => i !== ganz.aktiv);
          schreibGanz({ ...ganz, outfits, aktiv: Math.max(0, ganz.aktiv - 1) });
        };
        zeile.append(weg);
      }
      root.append(zeile);

      // The preview: the outfit on a mannequin or as a flat lay, rendered
      // through the workflow on demand; dimmed once the outfit changed since.
      const art = ganz.vorschauArt === "flach" ? "flach" : "puppe";
      const vb = outfitBild(node, o);
      const block = document.createElement("div");
      block.className = "k2-wvorschau";
      if (vb) {
        const a = document.createElement("a");
        a.className = "k2-wbild" + (vb.aktuell ? "" : " k2-alt");
        a.href = outfitBildUrl(vb.datei, false);
        a.target = "_blank";
        a.rel = "noopener";
        a.style.backgroundImage = `url("${outfitBildUrl(vb.datei, true)}")`;
        a.title = vb.aktuell ? uet("Bild öffnen", "ui") : uet("Veraltet — das Outfit wurde seitdem geändert", "ui");
        if (!vb.aktuell) {
          const hinweis = document.createElement("span");
          hinweis.textContent = uet("veraltet", "ui");
          a.append(hinweis);
        }
        block.append(a);
      }
      const knoepfe = document.createElement("div");
      knoepfe.className = "k2-schnell";
      for (const [wert, text, titel] of [
        ["puppe", uet("Puppe", "ui"), uet("Das Outfit an einer gesichtslosen Schaufensterpuppe im Studio.", "ui")],
        ["flach", uet("Flat Lay", "ui"), uet("Die Teile von oben nebeneinander ausgelegt.", "ui")],
      ]) {
        const c = document.createElement("button");
        c.type = "button";
        c.className = "k2-chip k2-klein" + (art === wert ? " k2-an" : "");
        c.textContent = text;
        c.title = titel;
        c.onclick = () => schreibGanz({ ...ganz, vorschauArt: wert });
        knoepfe.append(c);
      }
      const los = document.createElement("button");
      los.type = "button";
      los.className = "k2-textknopf";
      const laeuft = !!vorschauStatus && !vorschauStatus.startsWith("⚠");
      los.disabled = laeuft;
      los.textContent = vorschauStatus || "▶ " + uet("Vorschau rendern", "ui");
      los.title = uet("Ein Lauf durch den eigenen Workflow, mit festem Studio-Look statt Stil und Licht des Shootings.", "ui");
      los.onclick = async () => {
        vorschauStatus = uet("rendert …", "ui");
        zeichne();
        const ok = await rendereUndMerke(node, o, art, (m) => { vorschauStatus = m; });
        if (ok) vorschauStatus = null;
        zeichne();
        serienNeuZeichnen();
      };
      knoepfe.append(los);
      block.append(knoepfe);
      root.append(block);
    }

    // --- sections, one open at a time ---------------------------------------
    // state.sektion is the open one; null closes all. Workflows from before
    // the Steckbrief open on the tab they were saved on.
    const liste = document.createElement("div");
    liste.className = "k2-blatt k2-liste";
    for (const s of sektionen) {
      const offen = state.sektion === s.name;
      // Every field of this section comes from the LoRA: dimmed, and the row
      // says so instead of listing values that do not reach the prompt.
      const lora = viaLora(state);
      const ganzLora = lora.size && alleFelder(s).every((c) => lora.has(c));
      const bereich = document.createElement("div");
      bereich.className = "k2-bereich" + (offen ? " k2-offen" : "") + (ganzLora ? " k2-via-lora" : "");

      const kopf = document.createElement("div");
      kopf.className = "k2-kopf";
      kopf.tabIndex = 0;
      kopf.setAttribute("role", "button");
      kopf.setAttribute("aria-expanded", String(offen));
      const chev = document.createElement("span");
      chev.className = "k2-chev";
      chev.textContent = "▶";
      const n = zaehle(state, s);
      const bname = document.createElement("span");
      bname.className = "k2-bname";
      bname.textContent = uet(s.name, "sektionen");
      if (n) {
        const z = document.createElement("sup");
        z.className = "k2-zahl";
        z.textContent = String(n);
        bname.append(z);
      }
      const teile = kurzfassung(state, s);
      const kurz = document.createElement("span");
      kurz.className = "k2-kurz" + (teile.length ? "" : " k2-leer");
      if (teile.length) {
        haengeKurzAn(kurz, teile);
      } else {
        // Also when only some of the section's fields are the LoRA's, but
        // every one that is set is (make-up with the lips set, say): the
        // count says 2, so "nothing set" would be wrong.
        kurz.textContent = !(ganzLora || (n && lora.size)) ? uet("nichts gesetzt", "ui")
          : (state.texte?.trigger || "").trim() ? uet("über die LoRA", "ui") : uet("über das Referenzbild", "ui");
      }
      kurz.title = teile.map((t) => t.text).join(" · ");
      const fragt = frageBereich === s.name;
      const weg = document.createElement("span");
      weg.className = "k2-weg" + (fragt ? " k2-frage" : "");
      if (n) {
        weg.textContent = fragt ? uetf("{0} löschen?", "ui", n) : "×";
        weg.title = fragt ? uet("Nochmal klicken bestätigt", "ui")
                          : uetf("Die {0} gesetzten Felder dieses Bereichs löschen", "ui", n);
        weg.onclick = (ev) => {
          ev.stopPropagation();
          if (fragt) leereBereich(state, s);
          else { frageBereich = s.name; frageInspire = false; zeichne(); }
        };
      }
      kopf.append(chev, bname, kurz, weg);
      const umschalten = () => schreib({ ...state, sektion: offen ? null : s.name });
      kopf.onclick = umschalten;
      kopf.onkeydown = (ev) => {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); umschalten(); }
      };
      bereich.append(kopf);

      if (offen) {
        const inhalt = document.createElement("div");
        inhalt.className = "k2-inhalt" + (s.name === "Kleidung" ? " k2-kleidung" : "");
        for (const eintrag of s.felder) {
          const art = Array.isArray(eintrag) ? "zeile" : daten.art?.[eintrag] || "select";
          if (art === "text") inhalt.append(feldText(state, eintrag));
          else if (art === "mehrfach") inhalt.append(feldMehrfach(state, eintrag));
          else inhalt.append(feldZeile(state, Array.isArray(eintrag) ? eintrag : [eintrag]));
        }
        bereich.append(inhalt);
      }
      liste.append(bereich);
      if (s.name === "Gesicht") {
        const warn = gesichtsWarnung(state);
        if (warn) liste.append(warn);
      }
    }
    root.append(liste);

    // --- clothing from before the Wardrobe (Person) ---------------------------
    // Older workflows keep their clothes in the person, and Python still
    // renders them - so they are shown here, with the way out, rather than
    // hidden where nobody can see or change them.
    if (!cfg.mehrere) {
      const alt = (daten.outfitFelder || []).filter((c) => c !== "details" && gesetzt(state, c));
      const altText = (state.texte?.details || "").trim();
      if (alt.length || altText) {
        const box = document.createElement("div");
        box.className = "k2-warn k2-altkleidung";
        const teile = alt.filter((c) => !/Color$|Material$/.test(c)).map((c) => label(c, state.felder[c]));
        if (altText) teile.push(altText);
        box.append(uet("Kleidung aus einer älteren Version: ", "ui") + teile.join(" · "));
        const nach = document.createElement("button");
        nach.type = "button";
        nach.className = "k2-textknopf";
        nach.textContent = uet("In Wardrobe übernehmen", "ui");
        nach.title = uet("Als Outfit in die angeschlossene Wardrobe, oder in eine neue daneben", "ui");
        nach.onclick = () => inWardrobeUebernehmen(state, alt, altText);
        const weg = document.createElement("button");
        weg.type = "button";
        weg.className = "k2-textknopf";
        weg.textContent = uet("entfernen", "ui");
        weg.onclick = () => schreib(ohneKleidung(state, alt));
        box.append(" ", nach, " ", weg);
        root.append(box);
      }
    }

    // --- actions & reset bar -------------------------------------------------
    {
      const zeile = document.createElement("div");
      zeile.className = "k2-reset";

      if (cfg.inspire) zeile.append(inspireKnopf(state, gesamt));

      if (gesamt) {
        const k = document.createElement("span");
        k.className = "k2-reset-knopf" + (nachfrage ? " k2-frage" : "");
        if (nachfrage) {
          k.textContent = uetf("wirklich alle {0} löschen?", "ui", gesamt);
          k.title = uet("Nochmal klicken bestätigt", "ui");
          k.onclick = () => {
            nachfrage = false;
            // Wardrobe: only the active outfit's fields; its name survives.
            if (cfg.mehrere) {
              schreib({ felder: {}, mehrfach: {}, texte: { details: "", name: state.texte?.name || "" },
                        sektion: state.sektion, gruppe: {} });
            } else {
              schreib({ ...structuredClone(cfg.vorgabe), sektion: state.sektion, gruppe: {} });
            }
          };
        } else {
          k.textContent = `⟲ ${uet("alles", "ui")} (${gesamt})`;
          k.title = uet("Alle Felder des Nodes zurücksetzen", "ui");
          k.onclick = () => { nachfrage = true; frageBereich = null; frageInspire = false; zeichne(); };
        }
        zeile.append(k);
      }
      root.append(zeile);
    }

    // --- live preview --------------------------------------------------------
    const text = baueVorschau(daten, state);
    const v = document.createElement("div");
    v.className = "k2-vorschau k2-lang" + (text ? "" : " k2-leer");
    v.textContent = text || uet("nichts gewählt", "ui");
    root.append(v);
    // Where the clothes come from: the open tab of the wired Wardrobe.
    // Inside the Studio sidebar the Wardrobe sits directly below, so skip when
    // mounted on the Series node directly (embedded Studio mode) or wired in Studio.
    if (!cfg.mehrere && node.comfyClass !== "Krea2Photoshooting") {
      const w = wardrobeVonPerson(node);
      let name = null;
      if (w) {
        try {
          const st = JSON.parse(w.properties?.wardrobeState || "{}");
          const i = Math.min(Math.max(0, st.aktiv || 0), (st.outfits?.length || 1) - 1);
          name = (st.outfits?.[i]?.name || "").trim() || uetf("Outfit {0}", "ui", i + 1);
        } catch (e) { name = null; }
      }
      if (!ziel || !w) {
        const k = document.createElement("div");
        k.className = "k2-kleidung-quelle";
        if (name) {
          k.textContent = uetf("Kleidung: Wardrobe · {0}", "ui", name);
        } else {
          k.append(uet("Kleidung: keine — eine Wardrobe an den Eingang garderobe hängen", "ui") + " ");
          const addBtn = document.createElement("button");
          addBtn.type = "button";
          addBtn.className = "k2-textknopf";
          addBtn.textContent = uet("+ Wardrobe anlegen", "ui");
          addBtn.title = uet("Wardrobe-Node daneben anlegen und mit garderobe verbinden", "ui");
          addBtn.onclick = () => erzeugeUndVerbinde("Krea2Wardrobe", node, "garderobe", "garderobe");
          k.append(addBtn);
        }
        root.append(k);
      }
    }
  }

  // A click anywhere else closes an open palette or list. One listener per
  // node; it does nothing while neither is open, and goes with the node - undo
  // and every workflow load rebuild all nodes, and each left one behind.
  const woanders = (ev) => {
    if (!offeneFarbe && !offeneWahl) return;
    if (ev.target.closest?.(".k2-palette, .k2-farbknopf, .k2-wahlbox, .k2-wahlknopf") && root.contains(ev.target)) return;
    offeneFarbe = null;
    offeneWahl = null;
    wahlSuche = "";
    zeichne();
  };
  document.addEventListener("pointerdown", woanders);
  // The other view of this node (canvas or sidebar) follows every write here.
  const folge = ansicht(node, zeichne);
  const weg = () => {
    document.removeEventListener("pointerdown", woanders);
    folge.weg();
  };
  if (ziel) {
    ziel.append(root);
    zeichne();
    return { root, weg: () => { weg(); root.remove(); } };
  }
  beimEntfernen(node, weg);

  queueMicrotask(zeichne);
  node._k2Zeichne = zeichne;

  // The height follows the node, see shooting.mjs.
  const CHROM = 48;
  // A fixed height in the full view (it scrolls inside), the content's in
  // the compact one.
  node._k2Kompakt = { vollHoehe: cfg.groesse[1] };
  const w = node.addDOMWidget("k2_" + cfg.teil.toLowerCase(), "custom", root, {
    getValue: () => node.properties?.[PROP],
    setValue: () => {},
    getMinHeight: () => (istKompakt(node) ? 40 : 240),
    getMaxHeight: () => Math.max(240, (node.size?.[1] || 400) - CHROM),
    margin: 4,
    serialize: false,
  });
  applyAdaptiveCanvasOnly(w);
}

for (const cfg of [PERSON, WARDROBE]) {
  registriereStateInjektion(cfg.classType, cfg.hidden, cfg.prop, cfg.vorgabe);
  // The Studio sidebar (studio.mjs) draws this interface into its own column.
  registriereBauer(cfg.classType, async (node, ziel) => {
    const presets = await ladePresets();
    return presets?.person ? baue(node, presets.person, cfg, ziel) : null;
  });

  app.registerExtension({
    name: "Krea2." + cfg.classType,

    async beforeRegisterNodeDef(nodeType, nodeData) {
      if (nodeData.name !== cfg.classType) return;
      const orig = nodeType.prototype.onConfigure;
      nodeType.prototype.onConfigure = function () {
        // Loaded from a workflow: its saved size stands (see nodeCreated).
        this._k2Geladen = true;
        const r = orig?.apply(this, arguments);
        queueMicrotask(() => this._k2Zeichne?.());
        return r;
      };
      // Wiring a wardrobe in or out changes what the person wears and what
      // the series shows.
      const origVerbindung = nodeType.prototype.onConnectionsChange;
      nodeType.prototype.onConnectionsChange = function () {
        const r = origVerbindung?.apply(this, arguments);
        queueMicrotask(() => { this._k2Zeichne?.(); serienNeuZeichnen(); });
        return r;
      };
    },

    async nodeCreated(node) {
      if (node.comfyClass !== cfg.classType) return;
      // Person: brand strip, five section rows, the open section (make-up is
      // the tallest), actions and preview. Only for new nodes - onConfigure
      // restores the saved size for stored workflows; a smaller node scrolls.
      // Only for a new node - a loaded one keeps its saved size. nodeCreated
      // awaits the presets while configure() runs, so an unconditional size
      // here overwrote the saved one.
      const bauen = (presets) => {
        // A new node starts compact; a loaded one keeps what it was saved
        // with, full when it has no view property (saved before there was one).
        if (!node._k2Geladen) {
          node.size = [...cfg.groesse];
          node.properties = node.properties || {};
          node.properties[PROP_ANSICHT] ??= "kompakt";
        }
        baue(node, presets.person, cfg);
      };
      const presets = await ladePresets();
      if (!presets?.person) {
        presetFehler(node, bauen);
        return;
      }
      bauen(presets);
    },
  });
}
