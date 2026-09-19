// Interface of the Person Builder.
//
// Its own blueprint rather than panel.mjs, because the person is structurally
// different: 49 fields instead of 6, in collapsible sections, plus free text fields
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
  markenleiste,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.5.0";

import { app } from "../../scripts/app.js";

const CLASS_TYPE = "Krea2PersonBuilder";
const HIDDEN = "PersonState";
const PROP = "personState";

const VORGABE = {
  felder: {},
  mehrfach: { skinFeatures: [] },
  texte: { ageExact: "", details: "", trigger: "" },
  sektion: "Grund",
};

// A section entry is either a field name or a list of fields that belong together.
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
  // With a character LoRA's trigger, face, hair and skin come from the LoRA
  // and stay out - LORA_WEG in person_builder.py.
  const trigger = (t.trigger || "").trim().replace(/[,;.\s]+$/, "");
  const loraWeg = new Set(trigger ? daten.loraWeg || [] : []);
  const w = (cat) => (loraWeg.has(cat) ? null : wertVon(daten, cat, f[cat]));
  const teile = [];

  let gen = w("gender") || w("type");
  if (gen === "a young woman" || gen === "young woman") gen = "woman";
  if (gen === "a young man" || gen === "young man") gen = "man";
  if (gen === "a woman") gen = "woman";
  if (gen === "a man") gen = "man";
  if (gen === "a trans woman") gen = "trans woman";
  if (gen === "a person") gen = "person";

  const poss = { woman: "her", "trans woman": "her", man: "his", person: "their" }[gen] || "their";

  // Mirrors MINDESTALTER in person_builder.py - the preview has to show what
  // the prompt will actually say, not what was typed.
  let genau = (t.ageExact || "").replace(/\D/g, "");
  if (genau && Number(genau) < 18) genau = "18";
  if (genau && Number(genau) > 0) {
    const alter = Number(genau);
    let subjekt = null;
    if (gen === "woman") subjekt = alter < 18 ? "girl" : "woman";
    else if (gen === "trans woman") subjekt = alter < 18 ? "trans girl" : "trans woman";
    else if (gen === "man") subjekt = alter < 18 ? "boy" : "man";
    else if (gen === "person") subjekt = alter < 13 ? "child" : (alter < 18 ? "teenager" : "person");

    if (subjekt) {
      const art = ("aeiou8".includes(String(alter)[0]) || [11, 18, 80].includes(alter)) ? "an" : "a";
      teile.push(`${art} ${alter}-year-old ${subjekt}`);
    } else {
      teile.push(alter + " years old");
    }
  } else if (w("age")) {
    const ageVal = w("age");
    if (ageVal === "{child}") {
      const sub = { woman: "young girl", "trans woman": "young trans girl", man: "young boy", person: "young child" }[gen] || "young child";
      teile.push(sub.startsWith("a") || sub.startsWith("e") || sub.startsWith("i") || sub.startsWith("o") || sub.startsWith("u") ? "an " + sub : "a " + sub);
    } else if (ageVal === "{teen}") {
      const sub = { woman: "teenage girl", "trans woman": "teenage trans girl", man: "teenage boy", person: "teenager" }[gen] || "teenager";
      teile.push("a " + sub);
    } else {
      if (gen) {
        teile.push(gen === "woman" ? "a woman" : (gen === "trans woman" ? "a trans woman" : (gen === "man" ? "a man" : "a person")));
      }
      teile.push(ageVal.replace("{p}", poss));
    }
  } else if (gen) {
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

  for (const label of loraWeg.has("skinFeatures") ? [] : state.mehrfach?.skinFeatures || []) {
    const v = wertVon(daten, "skinFeatures", label);
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

function _zufall(arr) {
  if (!arr || !arr.length) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}

function wuerflePersona(daten, stateAktuell) {
  const f = {};
  const t = { ageExact: "", details: "" };
  const m = { skinFeatures: [] };

  const valid = (cat, label) => {
    return daten.felder?.[cat]?.some((e) => e.label === label) ? label : daten.leer;
  };

  // 1. Gender
  const genPool = ["Frau", "Frau", "Frau", "Mann", "Mann", "Transfrau", "Person"];
  const gender = _zufall(genPool);
  f.gender = valid("gender", gender);

  // 2. Age (20s to 50s)
  const agePool = [
    "Anfang 20", "Mitte 20", "Ende 20", "Anfang 30", "Mitte 30", "Ende 30", "40er", "50er"
  ];
  f.age = valid("age", _zufall(agePool));

  // 3. Coherent Ethnicity Archetypes
  const archetypes = [
    {
      ethnicity: "Skandinavisch",
      skinTone: ["Sehr hell", "Hell", "Kühles Porzellan"],
      complexion: ["Natürliche Poren", "Zarter Glanz", "Frisch & taufrisch"],
      hairColor: ["Honigblond", "Platinblond", "Aschblond", "Rot / Kupfer", "Hellbraun"],
      eyes: ["Eisblau", "Helles Blau", "Graugrün", "Klares Grün", "Graublau"],
      hairF: ["Lange Wellen", "Beach Waves", "Lange glatte Haare", "Curtain Bangs", "Messy Bun"],
      hairM: ["Mittellang strukturiert", "Klassischer Seitenscheitel", "Kurzer Fade Cut"],
      features: ["Sommersprossen"],
      featuresChance: 0.35,
    },
    {
      ethnicity: "Mediterran",
      skinTone: ["Hell gebräunt", "Gebräunt", "Oliv"],
      complexion: ["Natürliche Poren", "Zarter Glanz", "Satin Finish"],
      hairColor: ["Warmes Schokobraun", "Dunkelbraun", "Schwarzbraun", "Kastanienbraun"],
      eyes: ["Warmes Braun", "Dunkelbraun", "Haselnuss", "Bernstein"],
      hairF: ["Voluminöse Locken", "Lange Wellen", "Schulterlang gestuft", "Sanfte Wellen"],
      hairM: ["Lockiges Deckhaar", "Messy Crop", "Klassischer Seitenscheitel"],
      features: [],
      featuresChance: 0,
    },
    {
      ethnicity: "Osteuropäisch",
      skinTone: ["Sehr hell", "Hell", "Hell gebräunt"],
      complexion: ["Matte Textur", "Natürliche Poren", "Feine Textur"],
      hairColor: ["Dunkelblond", "Aschbraun", "Kastanienbraun", "Schwarzbraun"],
      eyes: ["Eisblau", "Graublau", "Graugrün", "Dunkelbraun"],
      hairF: ["Lange glatte Haare", "Lange Wellen", "Kurzer Bob", "Long Bob"],
      hairM: ["Undercut", "Kurzer Fade Cut", "Slicked Back"],
      features: [],
      featuresChance: 0,
    },
    {
      ethnicity: "Nahöstlich",
      skinTone: ["Hell gebräunt", "Gebräunt", "Oliv", "Warmes Gold"],
      complexion: ["Natürliche Poren", "Satin Finish", "Zarter Glanz"],
      hairColor: ["Tiefschwarz", "Schwarz", "Schwarzbraun"],
      eyes: ["Dunkelbraun", "Tiefbraun", "Haselnuss"],
      hairF: ["Lange Wellen", "Voluminöse Locken", "Lange glatte Haare"],
      hairM: ["Klassischer Seitenscheitel", "Kurzer Fade Cut", "Messy Crop"],
      features: [],
      featuresChance: 0,
    },
    {
      ethnicity: "Ostasiatisch",
      skinTone: ["Sehr hell", "Hell", "Kühles Porzellan", "Warmes Gold"],
      complexion: ["Frisch & taufrisch", "Gleichmäßig", "Natürliche Poren"],
      hairColor: ["Tiefschwarz", "Schwarz", "Schwarzbraun"],
      eyes: ["Dunkelbraun", "Schwarzbraun"],
      hairF: ["Lange glatte Haare", "Kurzer Bob", "Curtain Bangs", "Pixie Cut"],
      hairM: ["Undercut", "Messy Crop", "Klassischer Seitenscheitel"],
      features: [],
      featuresChance: 0,
    },
    {
      ethnicity: "Südasiatisch",
      skinTone: ["Gebräunt", "Braun", "Tiefbraun", "Hell gebräunt"],
      complexion: ["Zarter Glanz", "Natürliche Poren", "Satin Finish"],
      hairColor: ["Tiefschwarz", "Schwarz"],
      eyes: ["Dunkelbraun", "Tiefbraun", "Haselnuss"],
      hairF: ["Lange glatte Haare", "Lange Wellen", "Voluminöse Locken"],
      hairM: ["Klassischer Seitenscheitel", "Kurzer Fade Cut"],
      features: [],
      featuresChance: 0,
    },
    {
      ethnicity: "Afrikanisch",
      skinTone: ["Braun", "Tiefbraun", "Warmes Ebenholz", "Dunkles Espresso"],
      complexion: ["Zarter Glanz", "Natürliche Poren", "Satin Finish"],
      hairColor: ["Tiefschwarz", "Schwarz"],
      eyes: ["Dunkelbraun", "Tiefbraun"],
      hairF: ["Afro", "Braids / Zöpfe", "Kurze Twists", "Buzz Cut"],
      hairM: ["Kurze Twists", "Fade Cut", "Buzz Cut", "Afro"],
      features: [],
      featuresChance: 0,
    },
    {
      ethnicity: "Latina",
      skinTone: ["Hell gebräunt", "Gebräunt", "Warmes Gold", "Oliv"],
      complexion: ["Zarter Glanz", "Natürliche Poren", "Frisch & taufrisch"],
      hairColor: ["Warmes Schokobraun", "Kastanienbraun", "Schwarz"],
      eyes: ["Warmes Braun", "Haselnuss", "Bernstein", "Dunkelbraun"],
      hairF: ["Lange Wellen", "Beach Waves", "Voluminöse Locken"],
      hairM: ["Lockiges Deckhaar", "Kurzer Fade Cut", "Messy Crop"],
      features: [],
      featuresChance: 0,
    },
  ];

  const arch = _zufall(archetypes);
  f.ethnicity = valid("ethnicity", arch.ethnicity);
  f.skinTone = valid("skinTone", _zufall(arch.skinTone));
  f.complexion = valid("complexion", _zufall(arch.complexion));
  f.hairColor = valid("hairColor", _zufall(arch.hairColor));
  f.eyes = valid("eyes", _zufall(arch.eyes));

  const isMann = gender === "Mann";
  const hairPool = isMann ? arch.hairM : arch.hairF;
  f.hair = valid("hair", _zufall(hairPool));

  // 4. Figure & Body
  f.height = valid("height", _zufall(["Mittelgroß", "Groß", "Zierlich"]));
  const figures = isMann
    ? ["Athletisch", "Sportlich", "Definiert", "Schlank", "Muskulös"]
    : ["Athletisch", "Schlank", "Sanduhr", "Sportlich", "Kurvig", "Definiert"];
  f.figure = valid("figure", _zufall(figures));
  f.shoulders = valid("shoulders", _zufall(["Sportlich", "Natürlich", "Schmal", "Definiert"]));

  // 5. Facial structure
  f.cheekbones = valid("cheekbones", _zufall(["Hoch betont", "Markant", "Sanft", "Definiert"]));
  f.nose = valid("nose", _zufall(["Gerade", "Fein", "Klassisch", "Leichter Schwung"]));
  f.eyeShape = valid("eyeShape", _zufall(["Mandelförmig", "Offener Blick", "Groß & rund", "Katzenaugen"]));

  // 6. Makeup (if female / trans female)
  if (!isMann && Math.random() > 0.35) {
    f.lipColor = valid("lipColor", _zufall(["Nude", "Altrosa", "Rosenholz", "Warmes Koralle"]));
    f.lipFinish = valid("lipFinish", _zufall(["Matt", "Satin", "Soft Tint"]));
    if (Math.random() > 0.5) {
      f.eyeshadow = valid("eyeshadow", _zufall(["Natürliche Nudetöne", "Warmes Taupe", "Champagner Glow"]));
    }
  }

  // 7. Skin Features
  if (arch.featuresChance && Math.random() < arch.featuresChance) {
    m.skinFeatures = arch.features.filter((feat) =>
      daten.felder?.skinFeatures?.some((e) => e.label === feat)
    );
  }

  // 8. Shoes
  const shoesList = isMann
    ? ["Sneaker", "Combat Boots", "Loafer"]
    : ["Combat Boots", "Sneaker", "Loafer", "Stiefeletten mit Absatz", "Ballerinas", "Riemchen-Sandaletten", "Stiletto High Heels"];
  f.shoes = valid("shoes", _zufall(shoesList));
  f.shoesColor = valid("shoesColor", _zufall(["Schwarz", "Weiß", "Cognac / Braun", "Nude"]));

  // 9. Editorial Fashion Details
  const outfits = [
    "wearing a charcoal wool coat over a minimal top",
    "wearing an oversized beige cashmere sweater and tailored trousers",
    "wearing a crisp white cotton shirt with rolled-up sleeves",
    "wearing a structured black tailored blazer",
    "wearing a relaxed cream linen shirt",
    "wearing a classic trench coat over a dark turtleneck",
    "wearing a vintage brown leather jacket and minimalist tee",
    "wearing a clean silk slip top in muted tones",
  ];
  t.details = _zufall(outfits);

  return {
    ...stateAktuell,
    felder: f,
    texte: t,
    mehrfach: m,
  };
}

function baue(node, daten) {
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root";
  installCanvasZoomPassthrough(root);

  const lies = () => {
    const s = leseState(node, PROP, VORGABE);
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
    return s;
  };
  const schreib = (s) => {
    nachfrage = false;   // any other change withdraws the confirmation
    frageBereich = null;
    offeneFarbe = null;
    schreibeState(node, PROP, s);
    zeichne();
  };
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
  let frageBereich = null;     // the × of one section
  // The colour field whose palette is open. Also not state: an open palette
  // is a moment, not a setting.
  let offeneFarbe = null;

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

  // A field's dropdown, without a label. With families (shoes, top, bottom) the
  // models sit in <optgroup>s of the one dropdown.
  function selectFuer(state, cat) {
    const sel = document.createElement("select");
    const leerOpt = document.createElement("option");
    leerOpt.value = leer;
    leerOpt.textContent = leer;
    sel.append(leerOpt);
    const option = (e) => {
      const o = document.createElement("option");
      o.value = e.label;
      o.textContent = label(cat, e.label);
      o.title = e.wert;
      return o;
    };
    const gruppen = daten.art?.[cat] === "familie" ? daten.gruppen?.[cat] : null;
    if (gruppen) {
      for (const [g, labels] of Object.entries(gruppen)) {
        const og = document.createElement("optgroup");
        const n = uet(g, "familien");
        og.label = n.charAt(0).toUpperCase() + n.slice(1);
        for (const e of daten.felder[cat] || []) if (labels.includes(e.label)) og.append(option(e));
        sel.append(og);
      }
    } else {
      for (const e of daten.felder[cat] || []) sel.append(option(e));
    }
    const wert = state.felder?.[cat] || leer;
    // A value that is no longer in the list stays visible instead of the
    // dropdown silently jumping to the first entry on the next write.
    if (wert !== leer && !Array.from(sel.options).some((o) => o.value === wert)) {
      const o = document.createElement("option");
      o.value = wert;
      o.textContent = label(cat, wert);
      sel.append(o);
    }
    sel.value = wert;
    sel.onchange = () => schreib({ ...state, felder: { ...state.felder, [cat]: sel.value } });
    return sel;
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

  // One swatch button per colour field. The palette opens on click, inline
  // under the row - a floating layer would be clipped by the scrolling list.
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
      offeneFarbe = offeneFarbe === cat ? null : cat;
      zeichne();
      // Focus on the chosen colour, or on "no colour" when none is set.
      if (offeneFarbe) (root.querySelector(".k2-palette .k2-an") || root.querySelector(".k2-palette .k2-punkt"))?.focus();
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

  // A row: label, dropdowns, colour buttons. A colour field on its own (skin
  // tone, eyeshadow) shows its name next to the button instead of a dropdown.
  // The open palette and the material under the bottom follow below the row.
  function feldZeile(state, cats) {
    const erst = cats[0];
    const stueck = document.createElement("div");
    stueck.className = "k2-stueck";
    const zeile = document.createElement("div");
    zeile.className = "k2-feld";
    const zeilenname = daten.zeilennamen?.[erst];
    zeile.append(beschriftung(state, zeilenname ? uet(zeilenname, "feldnamen") : name(erst), cats));
    for (const c of cats) zeile.append(istFarbe(c) ? farbKnopf(state, c) : selectFuer(state, c));
    if (cats.length === 1 && istFarbe(erst)) {
      const t = document.createElement("span");
      t.className = "k2-farbtext" + (gesetzt(state, erst) ? "" : " k2-leer");
      t.textContent = gesetzt(state, erst) ? label(erst, state.felder[erst]) : leer;
      zeile.append(t);
    }
    stueck.append(zeile);
    for (const c of cats) if (offeneFarbe === c) stueck.append(palette(state, c));

    const unter = daten.unter?.[erst];
    if (unter) {
      const z = document.createElement("div");
      z.className = "k2-feld";
      z.append(beschriftung(state, "↳ " + name(unter), [unter], "k2-unterfeld"));
      const sel = selectFuer(state, unter);
      z.append(sel);
      stueck.append(z);
      if (gesetzt(state, unter) && gesetzt(state, erst) && stoffIgnoriert(state, erst)) {
        sel.classList.add("k2-ignoriert");
        const notiz = document.createElement("div");
        notiz.className = "k2-notiz";
        notiz.textContent = uetf("{0} nennt seinen eigenen Stoff – das Material bleibt aus dem Prompt",
                                 "ui", label(erst, state.felder[erst]));
        stueck.append(notiz);
      }
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
  // Fields a character LoRA's trigger takes over (LORA_WEG in Python).
  const viaLora = (state) => new Set((state.texte?.trigger || "").trim() ? daten.loraWeg || [] : []);

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

  function zeichne() {
    const state = lies();
    root.textContent = "";
    const gesamt = daten.sektionen.reduce((n, s) => n + zaehle(state, s), 0);

    // --- brand strip ---------------------------------------------------------
    root.append(markenleiste("Person",
      gesamt ? uetf("{0} gesetzt", "ui", gesamt) : uet("nichts gesetzt", "ui")));

    // --- sections, one open at a time ---------------------------------------
    // state.sektion is the open one; null closes all. Workflows from before
    // the Steckbrief open on the tab they were saved on.
    const liste = document.createElement("div");
    liste.className = "k2-blatt k2-liste";
    for (const s of daten.sektionen) {
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
        teile.forEach((t, i) => {
          if (i) {
            const trenner = document.createElement("i");
            trenner.textContent = "·";
            kurz.append(trenner);
          }
          if (t.punkt) {
            const d = document.createElement("b");
            d.className = "k2-mini";
            d.style.background = t.punkt;
            kurz.append(d);
          }
          kurz.append(t.text);
        });
      } else {
        kurz.textContent = ganzLora ? uet("über die LoRA", "ui") : uet("nichts gesetzt", "ui");
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
          else { frageBereich = s.name; zeichne(); }
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

    // --- actions & reset bar -------------------------------------------------
    {
      const zeile = document.createElement("div");
      zeile.className = "k2-reset";

      const inspireBtn = document.createElement("span");
      inspireBtn.className = "k2-inspire-btn";
      inspireBtn.textContent = "🎲 " + uet("Inspire Me", "ui");
      inspireBtn.title = uet("Stimmige Person auswürfeln", "ui");
      inspireBtn.onclick = () => schreib(wuerflePersona(daten, state));
      zeile.append(inspireBtn);

      if (gesamt) {
        const k = document.createElement("span");
        k.className = "k2-reset-knopf" + (nachfrage ? " k2-frage" : "");
        if (nachfrage) {
          k.textContent = uetf("wirklich alle {0} löschen?", "ui", gesamt);
          k.title = uet("Nochmal klicken bestätigt", "ui");
          k.onclick = () => {
            nachfrage = false;
            schreib({ ...VORGABE, felder: {}, mehrfach: { skinFeatures: [] },
                      texte: { ageExact: "", details: "", trigger: "" },
                      sektion: state.sektion, gruppe: {} });
          };
        } else {
          k.textContent = `⟲ ${uet("alles", "ui")} (${gesamt})`;
          k.title = uet("Alle Felder des Nodes zurücksetzen", "ui");
          k.onclick = () => { nachfrage = true; frageBereich = null; zeichne(); };
        }
        zeile.append(k);
      }
      root.append(zeile);
    }

    // --- live preview --------------------------------------------------------
    const v = document.createElement("div");
    const text = baueVorschau(daten, state);
    v.className = "k2-vorschau k2-lang" + (text ? "" : " k2-leer");
    v.textContent = text || uet("nichts gewählt", "ui");
    root.append(v);
  }

  // A click anywhere else closes an open palette. One listener per node; it
  // does nothing while no palette is open.
  document.addEventListener("pointerdown", (ev) => {
    if (!offeneFarbe) return;
    if (ev.target.closest?.(".k2-palette, .k2-farbknopf") && root.contains(ev.target)) return;
    offeneFarbe = null;
    zeichne();
  });

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
    // Brand strip, seven section rows, the open section (make-up is the
    // tallest), actions and preview. Only for new nodes - onConfigure restores
    // the saved size for stored workflows; a smaller node scrolls the list.
    node.size = [360, 560];
    baue(node, presets.person);
  },
});

