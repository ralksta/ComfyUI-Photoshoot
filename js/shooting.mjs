// Interface of the photoshoot node.
//
// What sets it apart from the other panels: it holds a button that works the
// queue itself. One click queues N runs, the counter climbs as it goes, and the
// node hands out a different photo per run.

import {
  applyAdaptiveCanvasOnly,
  injiziereCSS,
  installCanvasZoomPassthrough,
  ladePresets,
  leseState,
  markenleiste,
  outfitBild,
  outfitBildUrl,
  outfitHauptfarbe,
  rendereUndMerke,
  wardrobeVonPerson,
  registriereStateInjektion,
  schreibeState,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.6.0";

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const CLASS_TYPE = "Krea2Photoshooting";
const HIDDEN = "ShootingState";
const PROP = "shootingState";

// Has to match DEFAULT_STATE in shooting.py. If a key Python knows about is
// missing here, the interface shows it as "off" while the computation runs as
// if it were on - which is what happened with "rausch", which at first existed
// only in Python.
const VORGABE = {
  anzahl: 12,
  aktiv: { kamera: true, pose: true, ausdruck: true, format: true, fokus: true,
           rausch: true, outfit: true },
  pools: {},
  kameras: null, // null = alle
  fokusse: null,
  serienSeed: 0,
  start: 1, // photo number the series begins with
  takes: {}, // re-shoots per photo number, see bildseed() in shooting.py
  favoriten: [], // photo numbers marked in the contact sheet
  abdeckung: false, // framings in turn instead of drawn (older key, see reihenfolge)
  reihenfolge: null, // "gezogen" | "reihum" | "weit_nah", null = from abdeckung
  bogen: false, // mood arc over the series: false or its name (see STIMMUNGSBOEGEN)
  takesJeFoto: 1, // renders per planned photo, each with its own noise
  wahl: {}, // photo number -> the take shown and meant ("7": 1)
  outfitFolge: "bloecke", // outfits of a wired wardrobe: "bloecke" | "gemischt"
};

// Time estimate on the button.
//
// This used to be a fixed number (46 s), read off the first log line of a
// session - but that one included loading the model. In the steady state it is
// around 13 s, so the estimate was almost three times too high. And it could
// never grow along when the size step goes up.
//
// Now taken from the last successful runs. Median rather than mean, so that a
// single outlier - the first run after startup, with the model load - does not
// skew the estimate.
const SEK_PRO_BILD_VORGABE = 15;
let _sekProBild = SEK_PRO_BILD_VORGABE;

async function messeSekundenProBild() {
  try {
    const r = await fetch("/history?max_items=8", { cache: "no-store" });
    if (!r.ok) return _sekProBild;
    const daten = await r.json();
    const dauern = [];
    for (const eintrag of Object.values(daten)) {
      const m = eintrag?.status?.messages;
      if (!m || eintrag.status.status_str !== "success") continue;
      const start = m.find((x) => x[0] === "execution_start")?.[1]?.timestamp;
      const ende = m.find((x) => x[0] === "execution_success")?.[1]?.timestamp;
      if (start && ende && ende > start) dauern.push((ende - start) / 1000);
    }
    if (!dauern.length) return _sekProBild;
    dauern.sort((a, b) => a - b);
    _sekProBild = dauern[Math.floor(dauern.length / 2)];
  } catch (e) {
    // With no history the default stands - better a rough estimate than a
    // broken interface.
  }
  return _sekProBild;
}

// ------------------------------------------- Selection as done in Python ---
// Has to stay character-for-character equivalent to shooting.py, or the preview
// shows something other than what comes out later. Deliberately without bit
// operations: "| 1" would truncate to 32 bits in JavaScript and compute wrongly
// for denominators from 2^31 upwards.
function schritt(platz, d) {
  const frac = Math.sqrt(d.wurzeln[platz % d.wurzeln.length]) % 1;
  const s = Math.floor(frac * d.nenner);
  return s % 2 === 0 ? s + 1 : s;
}

function waehle(labels, lauf, platz, d) {
  const n = labels?.length || 0;
  if (!n) return null;
  const pos = (lauf * schritt(platz, d)) % d.nenner;
  return labels[Math.floor((pos * n) / d.nenner)];
}

function pool(d, quelle, cat, state, kamera, haltung, stimmung) {
  const wahl = state.pools?.[cat] ?? d.alle;
  if (wahl === d.leer) return [];
  const alle = d.listen[quelle][cat] || [];
  // A mood arc names the moods of this photo's stage (see plane()).
  if (cat === "stimmung" && state._stimmungen) {
    const nur = alle.filter((l) => state._stimmungen.includes(l));
    if (nur.length) return nur;
  }
  const g = d.gruppen[quelle];
  if (cat === g.feld && wahl !== d.alle) {
    const erlaubt = g.familien[wahl] || [];
    return alle.filter((l) => erlaubt.includes(l));
  }
  // Has to be the same restriction as _pool() in shooting.py, or the preview
  // shows a different photo from the one that is computed later.
  if (cat === "raum" && kamera && d.kameraRaum?.[kamera]) {
    const erlaubt = d.kameraRaum[kamera];
    return alle.filter((l) => erlaubt.includes(l));
  }
  // Tension, arms and legs against the base posture, same reasoning.
  const kopplung = { spannung: d.haltungSpannung, arme: d.haltungArme,
                     beine: d.haltungBeine, raum: d.haltungRaum }[cat];
  if (kopplung && haltung && kopplung[haltung]) {
    const erlaubt = kopplung[haltung];
    const gefiltert = alle.filter((l) => erlaubt.includes(l));
    return gefiltert.length ? gefiltert : alle;
  }
  // Eyes, mouth and brows against the mood - the exclusion list from
  // EB.STIMMUNG_NUR_FUER, keyed "cat|label" because JSON has no tuples.
  if (quelle === "ausdruck" && stimmung && d.stimmungNurFuer) {
    const familien = d.gruppen.ausdruck.familien || {};
    const familie = Object.keys(familien).find((f) => familien[f].includes(stimmung));
    const gefiltert = alle.filter((l) => {
      const nur = d.stimmungNurFuer[cat + "|" + l];
      return !nur || !familie || nur.includes(familie);
    });
    return gefiltert.length ? gefiltert : alle;
  }
  return alle;
}

// Same as reihenfolge(), bogen_von() and _position() in shooting.py.
function bogenVon(d, state) {
  const b = state.bogen;
  // True and "Aufbau" are the first version's one arc; "Freude" replaced it.
  if (b === true || b === "Aufbau") return "Freude";
  return d.boegen && d.boegen[b] ? b : null;
}
function reihenfolgeVon(state) {
  const r = state.reihenfolge;
  if (r === "gezogen" || r === "reihum" || r === "weit_nah") return r;
  return state.abdeckung ? "reihum" : "gezogen";
}
function position(state, lauf) {
  const n = Math.max(1, parseInt(state.anzahl, 10) || 1);
  const i = lauf - (Math.max(1, parseInt(state.start, 10) || 1) - 1);
  return [Math.min(Math.max(i, 0), n - 1), n];
}

// Same as _im_block() in shooting.py: the position within the outfit's block.
function imBlock(state, lauf, outfits) {
  if (!outfits || state.aktiv?.outfit === false || state.outfitFolge === "gemischt") return null;
  const [i, n] = position(state, lauf);
  const b = Math.floor((i * outfits) / n);
  const anfang = Math.ceil((b * n) / outfits), ende = Math.ceil(((b + 1) * n) / outfits);
  return [i - anfang, ende - anfang];
}

// Same as outfit_fuer() in shooting.py: which outfit this photo wears.
function outfitFuer(d, state, lauf, outfits) {
  if (!outfits || state.aktiv?.outfit === false) return null;
  if (state.outfitFolge === "gemischt") {
    return waehle([...Array(outfits).keys()], lauf, d.felder.length + 3, d);
  }
  const [i, n] = position(state, lauf);
  return Math.floor((i * outfits) / n);
}

function plane(d, state, lauf, outfits = 0) {
  const aktiv = state.aktiv || {};
  let kamera = null;
  const pose = {}, ausdruck = {};
  const ordnung = reihenfolgeVon(state);
  const [i, n] = position(state, lauf);
  // In blocks, the framing order starts over with every outfit (plane() in
  // shooting.py).
  const block = imBlock(state, lauf, outfits);
  // Mood arc: the stage follows the position in the series, equal parts.
  const bogen = bogenVon(d, state);
  if (bogen && aktiv.ausdruck) {
    const stufen = d.boegen[bogen];
    state = { ...state, _stimmungen: stufen[Math.floor((i * stufen.length) / n)] };
  }

  d.felder.forEach((f, platz) => {
    if (!aktiv[f.quelle]) return;
    if (f.quelle === "kamera") {
      const erlaubt = state.kameras?.length ? state.kameras : d.kamera.map((k) => k.label);
      if (ordnung === "reihum") {
        // Coverage, as in plane() in shooting.py: the framings in turn.
        const reihe = d.kamera.map((k) => k.label).filter((l) => erlaubt.includes(l));
        kamera = (reihe.length ? reihe : erlaubt)[(block ? block[0] : lauf) % (reihe.length || erlaubt.length)];
      } else if (ordnung === "weit_nah") {
        // Dramaturgy: widest to closest over the series, integer rounding as
        // in Python.
        let reihe = d.kamera.map((k) => k.label).filter((l) => erlaubt.includes(l)).reverse();
        if (!reihe.length) reihe = erlaubt;
        const [bi, bn] = block || [i, n];
        const k = bn > 1 ? Math.floor((2 * bi * (reihe.length - 1) + (bn - 1)) / (2 * (bn - 1))) : 0;
        kamera = reihe[k];
      } else {
        kamera = waehle(erlaubt, lauf, platz, d);
      }
    } else {
      // kamera is already settled here - it is the first field in d.felder.
      // The same holds for haltung against spannung: d.felder follows FOLGE,
      // which puts the base posture first and the body tension last.
      const label = waehle(pool(d, f.quelle, f.cat, state, kamera, pose.haltung,
                                ausdruck.stimmung),
                           lauf, platz, d);
      (f.quelle === "pose" ? pose : ausdruck)[f.cat] = label;
    }
  });
  // The focus depends on the camera and is therefore drawn afterwards.
  let fokus = null;
  if (aktiv.fokus && kamera) {
    let erlaubt = (d.kameraFokus[kamera] || []).filter(
      (f) => !state.fokusse?.length || state.fokusse.includes(f),
    );
    // As in shooting.py: a body turned away shows no face, so no face focus.
    if (d.abgewandt && pose.koerper === d.abgewandt) {
      erlaubt = erlaubt.filter((f) => !(d.fokusGesicht || []).includes(f));
    } else if (kamera === "Detail" && bogenVon(d, state) && aktiv.ausdruck) {
      // As in shooting.py: with a mood arc a detail shot shows the face.
      const gesicht = erlaubt.filter((f) => (d.fokusGesicht || []).includes(f));
      if (gesicht.length) erlaubt = gesicht;
    }
    fokus = waehle(erlaubt, lauf, d.felder.length + 2, d);
  }
  return { kamera, fokus, pose, ausdruck };
}

function format(d, kamera, lauf, state) {
  if (!state.aktiv?.format) return state.festesFormat || "2:3";
  const erlaubt = d.kameraFormate[kamera] || Object.keys(d.ratios);
  return waehle(erlaubt, lauf, d.felder.length + 1, d);
}

// Mirrors masse_fuer() from shooting.py.
function masseFuer(d, ratio, kante) {
  const [rw, rh] = d.ratios[ratio] || [1, 1];
  const flaeche = kante * kante;
  const runde = (x) => Math.max(256, Math.round(x / 16) * 16);
  return [runde(Math.sqrt((flaeche * rw) / rh)), runde(Math.sqrt((flaeche * rh) / rw))];
}

function masse(d, kamera, lauf, state) {
  const kante = state.groesse || d.kanteStandard;
  return masseFuer(d, format(d, kamera, lauf, state), kante);
}

// --------------------------------------------------------------- Build ---
function baue(node, d, person) {
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root k2-serie";
  installCanvasZoomPassthrough(root);

  const lies = () => leseState(node, PROP, VORGABE);
  const schreib = (s) => {
    schreibeState(node, PROP, s);
    zeichne();
    // Other settings, other photos: the contact sheet looks again.
    ladeSpaeter();
  };

  // Which axis is currently unfolded. Deliberately kept here and not in the
  // state: this is a matter of view, not a setting - and the state travels to
  // Python on execution, where it would have no business being. Only ever one
  // axis open; two open blocks were exactly the crowding this is meant to
  // remove.
  let offen = null;

  // ------------------------------------------ Dimensions from outside ---
  // When values arrive at width_in/height_in, they decide the resolution - but
  // only on execution. Up to this point the preview still computed with its own
  // size and its own ratio, and so showed dimensions that never came out. So
  // read the upstream node directly instead.
  const holeLink = (id) =>
    id == null ? null : (app.graph?.links?.get?.(id) ?? app.graph?.links?.[id]);

  function ausgangswert(eingang) {
    const link = holeLink(node.inputs?.find((i) => i.name === eingang)?.link);
    const quelle = link && app.graph?.getNodeById?.(link.origin_id);
    if (!quelle) return null;

    // Resolution Pixaroma keeps its state in properties, as our nodes do -
    // the same construction, so the same way of reading it.
    const roh = quelle.properties?.resolutionState;
    if (roh) {
      try {
        const s = typeof roh === "string" ? JSON.parse(roh) : roh;
        const v = Number(link.origin_slot === 0 ? s.w : s.h);
        if (Number.isFinite(v) && v > 0) return v;
      } catch (e) {
        // Unreadable - fall through to the generic attempt below.
      }
    }
    // Otherwise a widget named like the output. Covers primitives and simple
    // INT nodes.
    const name = quelle.outputs?.[link.origin_slot]?.name;
    const v = Number(quelle.widgets?.find((x) => x.name === name)?.value);
    return Number.isFinite(v) && v > 0 ? v : null;
  }

  const externeMasse = () => {
    const w = ausgangswert("width_in"), h = ausgangswert("height_in");
    return w && h ? [w, h] : null;
  };

  // ------------------------------------------------------- Building parts ---
  // The photo counter and its "control after generate" are ComfyUI widgets the
  // queue needs - they climb with every run. On the node they were a third
  // number next to "photos" and "from", so they are hidden and the panel says
  // "next: photo N" instead.
  const zaehlerWidget = () => node.widgets?.find((w) => w.name === "foto" || w.name === "seed");
  const steuerWidget = () => node.widgets?.find(
    (w) => w.name === "control_after_generate" || w.name === "control_after_generated");
  // The Vue front end reads "hidden" from the widget's reactive _state, the
  // canvas from options; both are set, and again on every redraw, because
  // loading a workflow can rebuild the state.
  const versteckeZaehler = () => {
    for (const w of [zaehlerWidget(), steuerWidget()]) {
      if (!w) continue;
      // A new object, assigned through the reactive state - setting the flag
      // on the existing one changes it without Vue noticing (options and
      // _state.options are often the same object). The marker keeps this to
      // once per rebuild.
      if (w._state && !w._state.options?.k2Versteckt) {
        w._state.options = { ...(w._state.options || {}), hidden: true, k2Versteckt: true };
      }
      if (w.options) w.options.hidden = true;
    }
  };

  // Saved series (ComfyUI/user/krea2_series, routes in api.py) and whether
  // the name field for saving is open.
  let eigene = [];
  let speichernOffen = false;
  const SERIEN_SCHLUESSEL = ["anzahl", "start", "aktiv", "pools", "kameras", "fokusse",
                             "festesFormat", "abdeckung", "reihenfolge", "bogen",
                             "takesJeFoto", "groesse", "serienSeed"];
  // ------------------------------------------------------- Wardrobe ---
  // The outfits of the Wardrobe node on the person that feeds this series -
  // the same list outfits_aus_state() gives Python, read from the node's state
  // instead of the executed output, so the contact sheet knows them before a
  // run.
  function wardrobeNode() {
    const link = holeLink(node.inputs?.find((i) => i.name === "person_data")?.link);
    const person = link && app.graph?.getNodeById?.(link.origin_id);
    return person?.comfyClass === "Krea2PersonBuilder" ? wardrobeVonPerson(person) : null;
  }
  function garderobe() {
    const q = wardrobeNode();
    if (!q) return [];
    let st = {};
    try { st = JSON.parse(q.properties?.wardrobeState || "{}"); } catch (e) { st = {}; }
    return (Array.isArray(st.outfits) ? st.outfits : []).map((o, i) => ({
      ...o, felder: o.felder || {}, name: (o.name || "").trim() || uetf("Outfit {0}", "ui", i + 1), node: q }));
  }

  // An outfit as a short list: garment and colour swatch per row. The colours
  // are the Person Builder's (FARBWERTE), so a swatch matches its colour button.
  const OUTFIT_ZEILEN = [["top", "topColor"], ["bottom", "bottomColor"], ["hosiery", "hosieryColor"],
                         ["shoes", "shoesColor"], ["jewellery"], ["eyewear"], ["headwear"]];
  const leerLabel = (l) => !l || l === person?.leer;
  function farbeVon(o, farbCat) {
    const l = o.felder[farbCat];
    return leerLabel(l) ? null : person?.farben?.[farbCat]?.[l] || null;
  }
  // The colour of the stripe under a frame: the top's, else the bottom's.
  const hauptfarbe = (o) => outfitHauptfarbe(person, o);
  function outfitKarte(o, nr) {
    const karte = document.createElement("div");
    karte.className = "k2-okarte";
    const kopf = document.createElement("div");
    kopf.className = "k2-okarte-kopf";
    kopf.style.borderColor = hauptfarbe(o);
    kopf.textContent = `${nr}  ${o.name}`;
    karte.append(kopf);
    // The rendered preview, when there is one; dimmed once the outfit changed.
    const vb = outfitBild(o.node, o);
    if (vb) {
      const a = document.createElement("a");
      a.className = "k2-okarte-bild" + (vb.aktuell ? "" : " k2-alt");
      a.href = outfitBildUrl(vb.datei, false);
      a.target = "_blank";
      a.rel = "noopener";
      a.style.backgroundImage = `url("${outfitBildUrl(vb.datei, true)}")`;
      a.title = vb.aktuell ? uet("Bild öffnen", "ui") : uet("Veraltet — das Outfit wurde seitdem geändert", "ui");
      karte.append(a);
    }
    let zeilen = 0;
    for (const [cat, farbCat] of OUTFIT_ZEILEN) {
      const l = o.felder[cat];
      if (leerLabel(l)) continue;
      const z = document.createElement("div");
      z.className = "k2-okarte-zeile";
      const fleck = document.createElement("b");
      const hex = farbCat && farbeVon(o, farbCat);
      fleck.className = "k2-mini" + (hex ? "" : " k2-ohne");
      if (hex) fleck.style.background = hex;
      z.append(fleck, uet(l, "person/" + cat));
      karte.append(z);
      zeilen++;
    }
    if (!zeilen) {
      const z = document.createElement("div");
      z.className = "k2-okarte-zeile k2-leer";
      z.textContent = uet("nichts gesetzt", "ui");
      karte.append(z);
    }
    return karte;
  }

  // Render every outfit's preview, one after the other, in the Wardrobe
  // node's chosen kind (mannequin or flat lay).
  let vorschauStatus = null;   // null, or text while rendering / after an error
  async function rendereOutfits() {
    const liste = garderobe();
    const q = wardrobeNode();
    if (!liste.length || !q || vorschauStatus) return;
    let art = "puppe";
    try { art = JSON.parse(q.properties?.wardrobeState || "{}").vorschauArt === "flach" ? "flach" : "puppe"; } catch (e) { /* default */ }
    for (const [i, o] of liste.entries()) {
      vorschauStatus = uetf("rendert {0} von {1} …", "ui", i + 1, liste.length);
      zeichne();
      if (!(await rendereUndMerke(q, o, art, (m) => { vorschauStatus = m; }))) { zeichne(); return; }
      zeichne();
    }
    vorschauStatus = null;
    zeichne();
  }

  async function serienAnfrage(pfad, daten) {
    try {
      const r = await fetch(pfad, daten ? {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(daten),
      } : { cache: "no-store" });
      if (r.ok) eigene = await r.json();
    } catch (e) {
      // Without the route the row simply shows the built-in recipes.
    }
    zeichne();
  }
  queueMicrotask(() => serienAnfrage("/krea2/serien"));

  // Selected frame in the contact sheet and the frames marked for a re-shoot.
  // A view, not a setting - neither travels to Python.
  let gewaehlt = null;
  const markiert = new Set();

  // Chips in the axes. "erreichbar" (optional) marks entries that cannot
  // occur at all with the remaining settings - they stay clickable but look
  // dead, and say why in the tooltip. The last chip cannot be deselected; it
  // shakes briefly instead of silently doing nothing.
  function chipreihe(alle, gewaehltRoh, sichern, erreichbar, bereich) {
    const chips = document.createElement("div");
    chips.className = "k2-chips";
    const gew = gewaehltRoh?.length ? gewaehltRoh : alle.map((x) => x.label);
    for (const e of alle) {
      const c = document.createElement("button");
      c.type = "button";
      const an = gew.includes(e.label);
      const tot = erreichbar && !erreichbar.has(e.label);
      c.className = "k2-chip" + (an ? " k2-an" : "") + (tot ? " k2-tot" : "");
      c.textContent = bereich ? uet(e.label, bereich) : e.label;
      c.setAttribute("aria-pressed", String(an));
      c.title = tot
        ? e.wert + uet(" — passt zu keiner der gewählten Kameraeinstellungen", "ui")
        : e.wert;
      c.onclick = () => {
        const neu = an ? gew.filter((x) => x !== e.label) : [...gew, e.label];
        if (!neu.length) {
          c.animate?.([{ transform: "translateX(-2px)" }, { transform: "translateX(2px)" },
                       { transform: "none" }], 180);
          return;
        }
        sichern(neu.length === alle.length ? null : neu);
      };
      chips.append(c);
    }
    return chips;
  }

  // Families as chips, one of them active ("all" included).
  function familienChips(state, quelle) {
    const g = d.gruppen[quelle];
    const aktiv = state.pools?.[g.feld] ?? d.alle;
    const chips = document.createElement("div");
    chips.className = "k2-chips";
    for (const f of [d.alle, ...Object.keys(g.familien)]) {
      const c = document.createElement("button");
      c.type = "button";
      c.className = "k2-chip" + (aktiv === f ? " k2-an" : "");
      c.textContent = f === d.alle ? uet("alle", "ui") : uet(f, "familien");
      c.onclick = () => schreib({ ...state, pools: { ...state.pools, [g.feld]: f } });
      chips.append(c);
    }
    return chips;
  }

  function auswahl(optionen, wert, sichern, beschriftung) {
    const zeile = document.createElement("div");
    zeile.className = "k2-feld";
    if (beschriftung) {
      const n = document.createElement("div");
      n.className = "k2-name";
      n.textContent = beschriftung;
      zeile.append(n);
    }
    const sel = document.createElement("select");
    for (const o of optionen) {
      const opt = document.createElement("option");
      opt.value = o.wert;
      opt.textContent = o.text;
      sel.append(opt);
    }
    sel.value = wert;
    sel.onchange = () => sichern(sel.value);
    zeile.append(sel);
    return zeile;
  }

  const notiz = (text) => {
    const n = document.createElement("div");
    n.className = "k2-anotiz";
    n.textContent = text;
    return n;
  };

  // One axis row: a switch, the name, what it currently does, the fold arrow.
  function achse({ schluessel, name, stand, hinweis, inhalt, zusatz, an: anVorgabe }, state) {
    const an = anVorgabe ?? !!state.aktiv?.[schluessel];
    const box = document.createElement("div");
    box.className = "k2-achse-box" + (offen === schluessel && inhalt ? " k2-offen" : "");
    const zeile = document.createElement("div");
    zeile.className = "k2-achse" + (an ? " k2-hell" : "") + (inhalt ? "" : " k2-zu");
    zeile.title = hinweis;

    const schalter = document.createElement("button");
    schalter.type = "button";
    schalter.className = "k2-schalter";
    schalter.setAttribute("role", "switch");
    schalter.setAttribute("aria-checked", String(an));
    schalter.setAttribute("aria-label", name);
    schalter.onclick = (e) => {
      e.stopPropagation();
      schreib({ ...state, aktiv: { ...state.aktiv, [schluessel]: !an } });
    };

    const n = document.createElement("div");
    n.className = "k2-achse-name";
    n.textContent = name;
    const w = document.createElement("div");
    w.className = "k2-achse-wert";
    w.textContent = zusatz ? `${stand} · ${zusatz}` : stand;
    const p = document.createElement("div");
    p.className = "k2-pfeil";
    p.textContent = inhalt ? "▶" : "";

    zeile.append(schalter, n, w, p);
    if (inhalt) {
      zeile.tabIndex = 0;
      zeile.setAttribute("role", "button");
      zeile.setAttribute("aria-expanded", String(offen === schluessel));
      const auf = () => { offen = offen === schluessel ? null : schluessel; zeichne(); };
      zeile.onclick = auf;
      zeile.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); auf(); }
      };
    }
    box.append(zeile);
    if (offen === schluessel && inhalt) {
      const auf = document.createElement("div");
      auf.className = "k2-auf";
      auf.append(...[].concat(inhalt()));
      box.append(auf);
    }
    return box;
  }

  async function starte(anzahl, start, jeFoto = 1) {
    // Set the counter to the start number and to increment, so that the
    // series begins there and not where the last run left off. "seed" is the
    // old name of the same widget, from before it was 1-based.
    const zaehler = zaehlerWidget();
    const ctrl = steuerWidget();
    if (jeFoto <= 1) {
      if (zaehler) zaehler.value = Math.max(1, start || 1);
      if (ctrl) ctrl.value = "increment";
      try {
        await app.queuePrompt(0, anzahl);
      } catch (e) {
        console.error("[Photoshoot] Einreihen fehlgeschlagen:", e);
      }
      zeichne();
      return;
    }
    // Several takes per photo: each number is queued once per take, with the
    // take written into the state before it goes into the prompt - the take
    // moves the seed (bildseed in shooting.py). Counter on "fixed" meanwhile,
    // then behind the series and on "increment" again.
    if (!zaehler) return;
    const state = lies();
    const takes = { ...(state.takes || {}) };
    if (ctrl) ctrl.value = "fixed";
    try {
      for (let nr = start; nr < start + anzahl; nr++) {
        for (let t = 0; t < jeFoto; t++) {
          takes[String(nr)] = t;
          schreibeState(node, PROP, { ...lies(), takes: { ...takes } });
          zaehler.value = nr;
          await app.queuePrompt(0, 1);
        }
      }
    } catch (e) {
      console.error("[Photoshoot] Einreihen fehlgeschlagen:", e);
    } finally {
      zaehler.value = start + anzahl;
      if (ctrl) ctrl.value = "increment";
      zeichne();
    }
  }

  // Re-shoot single photos: the same plan with a new take, so a new seed.
  // The counter is set to each number in turn with "fixed", so it does not
  // run on, and put back afterwards.
  async function nachfotografieren(nummern) {
    const zaehler = zaehlerWidget(), ctrl = steuerWidget();
    if (!zaehler || !nummern.length) return;
    const vorher = { wert: zaehler.value, modus: ctrl?.value };
    const state = lies();
    const takes = { ...(state.takes || {}) };
    for (const nr of nummern) takes[String(nr)] = (takes[String(nr)] || 0) + 1;
    // Written before queueing: the state goes into the prompt when it is built.
    schreibeState(node, PROP, { ...state, takes });
    if (ctrl) ctrl.value = "fixed";
    try {
      for (const nr of nummern) {
        zaehler.value = nr;
        await app.queuePrompt(0, 1);
      }
    } catch (e) {
      console.error("[Photoshoot] Nachfotografieren fehlgeschlagen:", e);
    } finally {
      zaehler.value = vorher.wert;
      if (ctrl && vorher.modus) ctrl.value = vorher.modus;
      markiert.clear();
      zeichne();
    }
  }

  // ------------------------------------------------- Pictures from history ---
  // Which finished picture belongs to which photo number. Read from ComfyUI's
  // history: every run of this node carries its photo number and its state in
  // the prompt. Only runs whose series settings match the current ones count -
  // count, start, favourites and takes excluded, since they do not change what
  // photo N is. Every take of a number is kept (the newest run per take); the
  // frame shows the chosen one, or the latest.
  let aufnahmen = new Map();   // photo number -> Map(take -> picture)
  // Filled up with the defaults first: runs from before a key existed (say
  // "abdeckung") must still match - otherwise every extension of the state
  // would empty the contact sheet.
  const planSchluessel = (s) => {
    const kopie = { ...VORGABE, ...(s || {}), aktiv: { ...VORGABE.aktiv, ...(s?.aktiv || {}) } };
    for (const k of ["anzahl", "start", "favoriten", "takes", "takesJeFoto", "wahl"]) delete kopie[k];
    const sortiert = (x) => (x && typeof x === "object" && !Array.isArray(x)
      ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, sortiert(x[k])]))
      : x);
    return JSON.stringify(sortiert(kopie));
  };
  // ComfyUI keeps its history in memory only - after a restart it is empty,
  // while the pictures are still on disk. So the node remembers what it found
  // (file, subfolder, type per photo and take) in its properties, which travel
  // with the saved workflow. Per settings, for the last ten, so switching back
  // to earlier settings brings their pictures back too.
  const PROP_BILDER = "photoshootBilder";
  const kurzSchluessel = (text) => {
    let h = 0;
    for (let i = 0; i < text.length; i++) h = (Math.imul(h, 31) + text.charCodeAt(i)) | 0;
    return (h >>> 0).toString(36);
  };
  const bildUrl = (b, extra) => "/view?" + new URLSearchParams({
    filename: b.filename, subfolder: b.subfolder || "", type: b.type || "output", ...extra });
  async function ladeBilder() {
    try {
      const soll = planSchluessel(lies());
      const schluessel = kurzSchluessel(soll);
      const ablage = node.properties?.[PROP_BILDER]?.plaene || {};
      const neu = new Map();
      // What was remembered first; the history can only add or replace.
      for (const [nr, takes] of Object.entries(ablage[schluessel]?.bilder || {})) {
        const m = new Map();
        for (const [t, b] of Object.entries(takes)) {
          m.set(Number(t), { nummer: -1, take: Number(t), datei: b,
                             klein: bildUrl(b, { preview: "webp;60" }), gross: bildUrl(b, {}) });
        }
        neu.set(Number(nr), m);
      }
      const r = await fetch("/history?max_items=200", { cache: "no-store" });
      const verlauf = r.ok ? await r.json() : {};
      for (const eintrag of Object.values(verlauf)) {
        const prompt = eintrag?.prompt?.[2];
        const ich = prompt?.[String(node.id)];
        if (ich?.class_type !== CLASS_TYPE) continue;
        let st;
        try { st = JSON.parse(ich.inputs?.[HIDDEN] || "{}"); } catch (e) { continue; }
        if (planSchluessel(st) !== soll) continue;
        const nr = Math.max(1, parseInt(ich.inputs?.foto ?? ich.inputs?.seed, 10) || 1);
        let bild = null;
        for (const aus of Object.values(eintrag.outputs || {})) {
          for (const b of aus?.images || []) {
            if (!bild || (b.type === "output" && bild.type !== "output")) bild = b;
          }
        }
        if (!bild) continue;
        const nummer = eintrag.prompt[0];
        const take = (st.takes || {})[String(nr)] || 0;
        if (!neu.has(nr)) neu.set(nr, new Map());
        const alt = neu.get(nr).get(take);
        if (alt && alt.nummer > nummer) continue;
        const datei = { filename: bild.filename, subfolder: bild.subfolder || "", type: bild.type || "output" };
        neu.get(nr).set(take, { nummer, take, datei,
                                klein: bildUrl(datei, { preview: "webp;60" }), gross: bildUrl(datei, {}) });
      }
      aufnahmen = neu;
      // Remember, only when something is there - and only the ten newest
      // settings, so the workflow file does not grow without end.
      if (neu.size) {
        const bilder = {};
        for (const [nr, takes] of neu) {
          bilder[nr] = Object.fromEntries([...takes].map(([t, e]) => [t, e.datei]));
        }
        const plaene = { ...ablage };
        delete plaene[schluessel];
        plaene[schluessel] = { bilder, zeit: Date.now() };
        const behalten = Object.entries(plaene).sort((a, b) => (b[1].zeit || 0) - (a[1].zeit || 0)).slice(0, 10);
        const alt = JSON.stringify(ablage[schluessel]?.bilder || {});
        if (alt !== JSON.stringify(bilder)) {
          node.properties = node.properties || {};
          node.properties[PROP_BILDER] = { plaene: Object.fromEntries(behalten) };
        }
      }
      zeichne();
    } catch (e) {
      // No history - the contact sheet simply stays empty frames.
    }
  }
  // The picture a frame shows: the chosen take if it exists, else the latest.
  function bildFuer(state, nr) {
    const takes = aufnahmen.get(nr);
    if (!takes?.size) return null;
    const wahl = state.wahl?.[String(nr)];
    if (wahl != null && takes.has(wahl)) return takes.get(wahl);
    return takes.get(Math.max(...takes.keys()));
  }
  let ladeTimer = null;
  const ladeSpaeter = () => { clearTimeout(ladeTimer); ladeTimer = setTimeout(ladeBilder, 400); };
  api.addEventListener("executed", ladeSpaeter);
  api.addEventListener("execution_success", ladeSpaeter);

  function zeichne() {
    versteckeZaehler();
    const state = lies();
    root.textContent = "";
    const anzahl = state.anzahl ?? 12;
    const start = Math.max(1, parseInt(state.start, 10) || 1);
    const dauerText = (sek) => {
      const gesamt = anzahl * Math.max(1, parseInt(state.takesJeFoto, 10) || 1) * sek;
      return "≈ " + (gesamt < 90 ? `${Math.round(gesamt)} s` : `${Math.round(gesamt / 60)} min`);
    };

    // --- brand strip ---------------------------------------------------------
    const marke = markenleiste("Series", uetf("{0} Fotos", "ui", anzahl) + " · " + dauerText(_sekProBild));
    root.append(marke);

    // --- count, start number, start button, status ---------------------------
    const serie = document.createElement("div");
    serie.className = "k2-serie-zeile";
    const zahlLbl = document.createElement("label");
    zahlLbl.textContent = uet("Fotos", "ui");
    const zahl = document.createElement("input");
    zahl.type = "number";
    zahl.min = "1";
    zahl.max = "500";
    zahl.value = String(anzahl);
    zahl.onchange = () => {
      const n = Math.max(1, Math.min(500, parseInt(zahl.value, 10) || 1));
      schreib({ ...state, anzahl: n });
    };
    zahlLbl.append(zahl);
    // Where the series begins. A new number is a new series with the same
    // settings - the answer to "how do I get different photos?". Typing a
    // number back in brings a series back.
    const abLbl = document.createElement("label");
    abLbl.textContent = uet("ab Nr.", "ui");
    const ab = document.createElement("input");
    ab.type = "number";
    ab.min = "1";
    ab.value = String(start);
    ab.title = uet("Startnummer. Die Serie beginnt bei diesem Foto.", "ui");
    ab.onchange = () =>
      schreib({ ...state, start: Math.max(1, parseInt(ab.value, 10) || 1) });
    abLbl.append(ab);
    const neu = document.createElement("button");
    neu.type = "button";
    neu.className = "k2-textknopf";
    neu.textContent = "↻ " + uet("Neue Serie", "ui");
    neu.title = uet("Neue Serie: zufällige Startnummer, gleiche Einstellungen", "ui");
    neu.onclick = () => schreib({ ...state, start: 1 + Math.floor(Math.random() * 999999) });
    serie.append(zahlLbl, abLbl, neu);
    root.append(serie);

    // --- recipes -------------------------------------------------------------
    // One click sets the axes for a kind of shoot (REZEPTE in shooting.py).
    // The chip of the recipe the state matches is lit; after any change of
    // your own none is, and nothing is lost - the axes simply are what they are.
    const gleich = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);
    const passt = (patch) => Object.entries(patch).every(([k, v]) => {
      if (k === "aktiv") return Object.entries(v).every(([a, an]) => !!state.aktiv?.[a] === an);
      if (k === "pools") {
        const felder = new Set([...Object.keys(v), ...Object.keys(state.pools || {})]);
        return [...felder].every((f) => (v[f] ?? d.alle) === (state.pools?.[f] ?? d.alle));
      }
      if (k === "kameras" || k === "fokusse") {
        const norm = (x) => (x?.length ? [...x].sort() : null);
        return gleich(norm(v), norm(state[k]));
      }
      if (k === "abdeckung") return (reihenfolgeVon(state) === "reihum") === !!v;
      if (k === "reihenfolge") return reihenfolgeVon(state) === v;
      if (k === "bogen") return (bogenVon(d, state) || false) === (v || false);
      return gleich(v, state[k]);
    });
    const rezepte = document.createElement("div");
    rezepte.className = "k2-schnell k2-rezepte";
    rezepte.append(uet("Rezept", "ui") + ":");
    let getroffen = false;
    for (const r of d.rezepte || []) {
      const an = passt(r.patch);
      getroffen ||= an;
      const c = document.createElement("button");
      c.type = "button";
      c.className = "k2-chip k2-klein" + (an ? " k2-an" : "");
      c.textContent = uet(r.name, "ui");
      c.title = uet(r.beschreibung, "ui");
      c.onclick = () => schreib({
        ...state, ...r.patch,
        aktiv: { ...state.aktiv, ...r.patch.aktiv },
        pools: { ...r.patch.pools },
      });
      rezepte.append(c);
    }
    // Saved series next to the built-in recipes, each with an × to delete.
    const anwenden = (patch) => schreib({
      ...state, ...patch,
      aktiv: { ...state.aktiv, ...(patch.aktiv || {}) },
      pools: { ...(patch.pools || {}) },
    });
    for (const r of eigene) {
      const an = passt(r.patch);
      getroffen ||= an;
      const gruppe = document.createElement("span");
      gruppe.className = "k2-eigene";
      const c = document.createElement("button");
      c.type = "button";
      c.className = "k2-chip k2-klein" + (an ? " k2-an" : "");
      c.textContent = r.name;
      c.title = uet("Gespeicherte Serie: Einstellungen, Startnummer, Größe und Seed.", "ui");
      c.onclick = () => anwenden(r.patch);
      const weg = document.createElement("button");
      weg.type = "button";
      weg.className = "k2-weg-klein";
      weg.textContent = "×";
      weg.title = uetf("Gespeicherte Serie löschen: {0}", "ui", r.name);
      weg.setAttribute("aria-label", weg.title);
      weg.onclick = () => serienAnfrage("/krea2/serien/loeschen", { name: r.name });
      gruppe.append(c, weg);
      rezepte.append(gruppe);
    }
    if (!getroffen) {
      const eigen = document.createElement("span");
      eigen.className = "k2-eigen";
      eigen.textContent = uet("eigene Einstellung", "ui");
      rezepte.append(eigen);
    }
    // Save the current settings under a name.
    if (speichernOffen) {
      const feld = document.createElement("input");
      feld.className = "k2-serien-name";
      feld.placeholder = uet("Name der Serie", "ui");
      const ok = document.createElement("button");
      ok.type = "button";
      ok.className = "k2-textknopf";
      ok.textContent = uet("Speichern", "ui");
      const abbrechen = document.createElement("button");
      abbrechen.type = "button";
      abbrechen.className = "k2-textknopf";
      abbrechen.textContent = uet("Abbrechen", "ui");
      const sichern = () => {
        const name = feld.value.trim();
        if (!name) { feld.focus(); return; }
        const patch = Object.fromEntries(SERIEN_SCHLUESSEL.filter((k) => k in state).map((k) => [k, state[k]]));
        speichernOffen = false;
        serienAnfrage("/krea2/serien", { name, patch });
      };
      ok.onclick = sichern;
      abbrechen.onclick = () => { speichernOffen = false; zeichne(); };
      feld.onkeydown = (e) => {
        if (e.key === "Enter") sichern();
        else if (e.key === "Escape") { speichernOffen = false; zeichne(); }
      };
      rezepte.append(feld, ok, abbrechen);
      queueMicrotask(() => feld.focus());
    } else {
      const plus = document.createElement("button");
      plus.type = "button";
      plus.className = "k2-chip k2-klein k2-plus";
      plus.textContent = "+ " + uet("Speichern", "ui");
      plus.title = uet("Diese Einstellungen als eigene Serie speichern", "ui");
      plus.onclick = () => { speichernOffen = true; zeichne(); };
      rezepte.append(plus);
    }
    root.append(rezepte);

    const knopf = document.createElement("button");
    knopf.type = "button";
    knopf.className = "k2-start";
    const knopfText = document.createElement("b");
    knopfText.textContent = uet("Shooting starten", "ui");
    const knopfSub = document.createElement("small");
    const jeFoto = Math.max(1, parseInt(state.takesJeFoto, 10) || 1);
    knopf.append(knopfText, knopfSub);
    // The duration comes from the last runs; measured once the history is in.
    const beschrifte = (sek) => {
      knopfSub.textContent = uetf("Fotos {0}–{1}", "ui", start, start + anzahl - 1) +
        (jeFoto > 1 ? " · " + uetf("{0} Takes je Foto", "ui", jeFoto) : "") + " · " + dauerText(sek);
      marke.querySelector(".k2-marke-zahl").textContent =
        uetf("{0} Fotos", "ui", anzahl) + " · " + dauerText(sek);
      knopf.title = sek.toFixed(1) + " " + uet("s je Bild, gemessen an den letzten Läufen", "ui");
    };
    beschrifte(_sekProBild);
    messeSekundenProBild().then(beschrifte);
    knopf.onclick = () => starte(anzahl, start, jeFoto);
    root.append(knopf);

    const status = document.createElement("div");
    status.className = "k2-status";
    const naechstes = Math.max(1, parseInt(zaehlerWidget()?.value, 10) || start);
    const links = document.createElement("span");
    links.append(uet("Nächstes:", "ui") + " ");
    const nb = document.createElement("b");
    nb.textContent = uetf("Foto {0}", "ui", naechstes);
    links.append(nb);
    const rechts = document.createElement("span");
    let imBogen = 0;
    for (let nr = start; nr < start + anzahl; nr++) if (aufnahmen.get(nr)?.size) imBogen++;
    // The counter can stand outside this series - after a workflow load, or
    // when the start number was changed. Queue would render that photo;
    // Start shooting resets it. Said here, or "next: photo 1" next to a
    // series from 101 reads like a bug.
    rechts.textContent = naechstes < start || naechstes > start + anzahl
      ? uetf("Start setzt ihn auf {0}", "ui", start)
      : uetf("{0} von {1} im Bogen", "ui", imBogen, anzahl);
    status.append(links, rechts);
    root.append(status);

    // --- the axes -------------------------------------------------------------
    // Are dimensions arriving from outside? That decides what the ratio switch
    // means.
    const verbunden = (name) => !!node.inputs?.find((i) => i.name === name)?.link;
    const massAnliegend = verbunden("width_in") && verbunden("height_in");
    // Applies only when the ratio is not being varied - shooting.py decides it
    // the same way. Otherwise the framing determines the ratio.
    const extern = massAnliegend && !state.aktiv?.format ? externeMasse() : null;

    // Which focus values can occur at all with the chosen settings. The focus
    // is coupled to the camera - a wide shot does not focus on the lips - and if
    // nothing is left after filtering, the photo gets none at all.
    const alleKameras = d.kamera.map((k) => k.label);
    const gewaehlteKameras = state.kameras?.length ? state.kameras : alleKameras;
    const erreichbar = new Set(
      state.aktiv?.kamera
        ? gewaehlteKameras.flatMap((k) => d.kameraFokus[k] || [])
        : d.fokus.map((f) => f.label),
    );
    const fokusGewaehlt = state.fokusse?.length ? state.fokusse : d.fokus.map((f) => f.label);
    const fokusWirksam = fokusGewaehlt.filter((f) => erreichbar.has(f));

    const familienStand = (quelle) => {
      const v = state.pools?.[d.gruppen[quelle].feld] ?? d.alle;
      return v === d.alle ? uet("alle Familien", "ui") : uetf("nur {0}", "ui", uet(v, "familien"));
    };
    const kante = state.groesse || d.kanteStandard;
    const fest = state.festesFormat || "2:3";
    const [festW, festH] = masseFuer(d, fest, kante);

    // Size, the second half of the format: an edge length in the square.
    const groessenZeile = () => {
      if (massAnliegend && !state.aktiv?.format) {
        return notiz(extern
          ? `${extern[0]}×${extern[1]}  ·  ` + uet("von außen", "ui")
          : uet("von außen — Wert erst beim Ausführen bekannt", "ui"));
      }
      const zeile = auswahl(
        d.kanten.map((k) => ({ wert: String(k), text: `${k} px  ·  ${((k * k) / 1e6).toFixed(1)} MP` })),
        String(kante),
        (v) => schreib({ ...state, groesse: parseInt(v, 10) }),
        uet("Größe", "ui"),
      );
      zeile.title = uet("Kantenlänge im Quadrat. Das Seitenverhältnis kommt von der ", "ui") +
                    uet("Kameraeinstellung, nicht von hier.", "ui");
      return zeile;
    };

    // Detail level of a framing as a word: the quick choice and the detail box.
    const detailWort = { voll: uet("nah", "ui"), oben: uet("nah", "ui"), figur: uet("Figur", "ui"), identitaet: uet("weit", "ui") };

    // The wardrobe on the input, and whether the outfit axis uses it. An
    // older state has no "outfit" switch and counts as on, as in Python.
    const outfits = garderobe();
    const outfitAn = state.aktiv?.outfit !== false;
    const outfitZahl = outfitAn ? outfits.length : 0;

    const achsen = [
      {
        schluessel: "kamera",
        name: uet("Kamera", "ui"),
        stand: !state.aktiv?.kamera
          ? uet("aus", "ui")
          : state.kameras?.length && state.kameras.length < alleKameras.length
            ? uetf("{0} von {1} Einstellungen", "ui", state.kameras.length, alleKameras.length)
            : uetf("alle {0} Einstellungen", "ui", alleKameras.length),
        hinweis: uet("Kameraeinstellung über die Serie variieren", "ui"),
        zusatz: !state.aktiv?.kamera ? null
          : { reihum: uet("reihum", "ui"), weit_nah: uet("weit → nah", "ui") }[reihenfolgeVon(state)] || null,
        inhalt: state.aktiv?.kamera
          ? () => {
              // Quick choice by detail level: close, figure, wide - or all.
              const schnell = document.createElement("div");
              schnell.className = "k2-schnell";
              schnell.append(uet("Schnell:", "ui"));
              const gruppen = { alle: alleKameras };
              for (const [lbl, det] of Object.entries(d.kameraDetail || {})) (gruppen[det] ||= []).push(lbl);
              const sortiert = (a) => [...a].sort().join("|");
              for (const [g, labels] of Object.entries(gruppen)) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" +
                  (sortiert(gewaehlteKameras) === sortiert(labels) ? " k2-an" : "");
                c.textContent = g === "alle" ? uet("alle", "ui") : detailWort[g] || g;
                c.onclick = () => schreib({ ...state, kameras: g === "alle" ? null : labels });
                schnell.append(c);
              }
              // Order: drawn, in turn (coverage), or wide to close (dramaturgy).
              const ordnung = document.createElement("div");
              ordnung.className = "k2-schnell";
              ordnung.append(uet("Reihenfolge:", "ui"));
              const jetzt = reihenfolgeVon(state);
              for (const [wert, text, titel] of [
                ["gezogen", uet("gezogen", "ui"), uet("Verteilt gezogen, jedes Foto anders – wie bisher.", "ui")],
                ["reihum", uet("jede einmal, reihum", "ui"), uet("Jede gewählte Einstellung kommt reihum genau einmal dran, statt verteilt gezogen zu werden.", "ui")],
                ["weit_nah", uet("weit → nah", "ui"), uet("Dramaturgie: die Serie beginnt mit der weitesten Einstellung und endet mit der nächsten.", "ui")],
              ]) {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + (jetzt === wert ? " k2-an" : "");
                c.textContent = text;
                c.title = titel;
                c.setAttribute("aria-pressed", String(jetzt === wert));
                c.onclick = () => schreib({ ...state, reihenfolge: wert, abdeckung: wert === "reihum" });
                ordnung.append(c);
              }
              return [ordnung, schnell, chipreihe(d.kamera, state.kameras,
                (n) => schreib({ ...state, kameras: n }), null, "shooting/kamera")];
            }
          : null,
      },
      {
        schluessel: "pose",
        name: uet("Pose", "ui"),
        stand: state.aktiv?.pose ? familienStand("pose") : uet("aus", "ui"),
        hinweis: uet("Körperhaltung variieren. Aufgeklappt: auf eine Familie einschränken.", "ui"),
        inhalt: state.aktiv?.pose ? () => familienChips(state, "pose") : null,
      },
      {
        schluessel: "ausdruck",
        name: uet("Ausdruck", "ui"),
        stand: !state.aktiv?.ausdruck ? uet("aus", "ui")
          : bogenVon(d, state) ? uet("Stimmungsbogen", "ui") + " · " + uet(bogenVon(d, state), "ui")
          : familienStand("ausdruck"),
        hinweis: uet("Mimik variieren. Aufgeklappt: auf eine Stimmungsfamilie einschränken.", "ui"),
        inhalt: state.aktiv?.ausdruck
          ? () => {
              // Mood arc: the mood develops over the series instead of
              // jumping - then the family choice has nothing to say. Each arc
              // shows its stages: the first mood of each, joined by arrows.
              const zeile = document.createElement("div");
              zeile.className = "k2-schnell";
              zeile.append(uet("Stimmungsbogen:", "ui"));
              const jetzt = bogenVon(d, state);
              const knopf = (wert, text, titel) => {
                const c = document.createElement("button");
                c.type = "button";
                c.className = "k2-chip k2-klein" + ((jetzt || false) === wert ? " k2-an" : "");
                c.textContent = text;
                if (titel) c.title = titel;
                c.onclick = () => schreib({ ...state, bogen: wert });
                zeile.append(c);
              };
              knopf(false, uet("aus", "ui"));
              for (const [name, stufen] of Object.entries(d.boegen || {})) {
                knopf(name, uet(name, "ui"),
                      stufen.map((st) => uet(st[0], "ausdruck/stimmung")).join(" → "));
              }
              if (!jetzt) return [zeile, familienChips(state, "ausdruck")];
              const verlauf = notiz(d.boegen[jetzt].map((st) => uet(st[0], "ausdruck/stimmung")).join(" → "));
              return [zeile, verlauf,
                      notiz(uet("Die Stimmung entwickelt sich über die Serie, Stufe für Stufe; innerhalb einer Stufe variiert sie.", "ui")),
                      notiz(uet("Wirkt am stärksten mit {expression} gleich nach {style} in der Prompt-Vorlage und einer Charakter-LoRA.", "ui"))];
            }
          : null,
      },
      {
        schluessel: "fokus",
        name: uet("Schwerpunkt", "ui"),
        stand: !state.aktiv?.fokus
          ? uet("aus", "ui")
          : !fokusWirksam.length
            ? uet("keiner passt", "ui")
            : state.fokusse?.length && state.fokusse.length < d.fokus.length
              ? uetf("{0} von {1} Bereichen", "ui", fokusWirksam.length, d.fokus.length)
              : uet("alle Bereiche", "ui"),
        hinweis: uet("Bildschwerpunkt variieren (Gesicht, Beine, Füße …). Welche ", "ui") +
                 uet("möglich sind, hängt von den gewählten Kameraeinstellungen ab.", "ui"),
        inhalt: state.aktiv?.fokus
          ? () => {
              const teile = [chipreihe(d.fokus, state.fokusse,
                (n) => schreib({ ...state, fokusse: n }), erreichbar, "shooting/fokus")];
              if (d.fokus.some((f) => !erreichbar.has(f.label))) {
                teile.push(notiz(uet("Durchgestrichen: kommt mit den gewählten Einstellungen nicht vor.", "ui")));
              }
              return teile;
            }
          : null,
      },
      {
        schluessel: "format",
        name: uet("Format", "ui"),
        stand: state.aktiv?.format
          ? uetf("folgt der Einstellung · {0} px", "ui", kante)
          : massAnliegend
            ? (extern ? `${extern[0]}×${extern[1]}` : uet("von außen", "ui"))
            : `${fest} · ${festW}×${festH}`,
        hinweis: uet("An: Seitenverhältnis passend zur Kameraeinstellung würfeln. ", "ui") +
                 uet("Aus: ein festes Verhältnis für alle Fotos.", "ui"),
        // Ratio and size together: both are the image dimensions.
        inhalt: () => {
          const teile = [];
          if (state.aktiv?.format) {
            teile.push(notiz(uet("Jede Einstellung wählt ein passendes Seitenverhältnis – Ganzkörper wird nie Querformat.", "ui")));
          } else if (!massAnliegend) {
            const chips = document.createElement("div");
            chips.className = "k2-chips";
            for (const r of Object.keys(d.ratios)) {
              const [rw, rh] = d.ratios[r];
              const s = 11 / Math.max(rw, rh);
              const c = document.createElement("button");
              c.type = "button";
              c.className = "k2-chip" + (r === fest ? " k2-an" : "");
              const icon = document.createElement("i");
              icon.className = "k2-rrect";
              icon.style.width = rw * s + "px";
              icon.style.height = rh * s + "px";
              c.append(icon, r);
              c.onclick = () => schreib({ ...state, festesFormat: r });
              chips.append(c);
            }
            teile.push(chips);
          }
          teile.push(groessenZeile());
          return teile;
        },
      },
      {
        schluessel: "outfit",
        an: outfitAn,
        name: uet("Outfit", "ui"),
        stand: !outfits.length
          ? uet("keine Garderobe", "ui")
          : !outfitAn
            ? uet("aus", "ui")
            : (outfits.length === 1 ? uet("1 Outfit", "ui") : uetf("{0} Outfits", "ui", outfits.length)) + " · " +
              (state.outfitFolge === "gemischt" ? uet("gemischt", "ui") : uet("in Blöcken", "ui")),
        hinweis: uet("Kostümwechsel: die Outfits der Wardrobe am Person Builder, ", "ui") +
                 uet("über die Serie verteilt", "ui"),
        inhalt: () => {
          if (!outfits.length) {
            return notiz(uet("Eine Wardrobe an den Eingang garderobe des Person Builders hängen, ", "ui") +
                         uet("dann wechselt die Person hier die Outfits.", "ui"));
          }
          const folge = document.createElement("div");
          folge.className = "k2-schnell";
          folge.append(uet("Folge:", "ui"));
          for (const [wert, text, titel] of [
            ["bloecke", uet("in Blöcken", "ui"), uet("Wie bei einem echten Shooting: erst alle Fotos im ersten Outfit, dann im zweiten. Die Kameraeinstellungen fangen mit jedem Outfit neu an.", "ui")],
            ["gemischt", uet("gemischt", "ui"), uet("Jedes Foto zieht sein Outfit.", "ui")],
          ]) {
            const c = document.createElement("button");
            c.type = "button";
            c.className = "k2-chip k2-klein" + ((state.outfitFolge || "bloecke") === wert ? " k2-an" : "");
            c.textContent = text;
            c.title = titel;
            c.onclick = () => schreib({ ...state, outfitFolge: wert });
            folge.append(c);
          }
          // Preview pictures, all outfits in one go (mannequin or flat lay is
          // chosen in the Wardrobe node).
          const vorschau = document.createElement("div");
          vorschau.className = "k2-schnell";
          const los = document.createElement("button");
          los.type = "button";
          los.className = "k2-textknopf";
          los.disabled = !!vorschauStatus && !vorschauStatus.startsWith("⚠");
          los.textContent = vorschauStatus || "▶ " + uetf("{0} Outfits rendern", "ui", outfits.length);
          los.title = uet("Ein Lauf je Outfit durch den eigenen Workflow, mit festem Studio-Look statt Stil und Licht des Shootings.", "ui");
          los.onclick = () => { if (vorschauStatus?.startsWith("⚠")) vorschauStatus = null; rendereOutfits(); };
          vorschau.append(los);
          // The rail: every outfit as a card.
          const stange = document.createElement("div");
          stange.className = "k2-stange";
          outfits.forEach((o, i) => stange.append(outfitKarte(o, i + 1)));
          return [folge, vorschau, stange];
        },
      },
      {
        schluessel: "rausch",
        name: uet("Rauschen", "ui"),
        stand: state.aktiv?.rausch
          ? uet("neu pro Foto", "ui")
          : uetf("ein Seed · {0}", "ui", state.serienSeed ?? 0),
        hinweis: uet("An: jedes Foto bekommt eigenes Rauschen. Aus: die ganze Serie ", "ui") +
                 uet("teilt einen Seed, dann bleibt der Schauplatz über die Fotos gleich.", "ui"),
        zusatz: (parseInt(state.takesJeFoto, 10) || 1) > 1
          ? uetf("{0} Takes", "ui", state.takesJeFoto) : null,
        inhalt: () => {
          // Takes per photo: every planned photo rendered several times with
          // its own noise, to pick the better one per shot.
          const takesZeile = document.createElement("div");
          takesZeile.className = "k2-schnell";
          takesZeile.append(uet("Takes je Foto:", "ui"));
          for (const k of [1, 2, 3, 4]) {
            const c = document.createElement("button");
            c.type = "button";
            c.className = "k2-chip k2-klein" + ((parseInt(state.takesJeFoto, 10) || 1) === k ? " k2-an" : "");
            c.textContent = String(k);
            c.onclick = () => schreib({ ...state, takesJeFoto: k });
            takesZeile.append(c);
          }
          if (state.aktiv?.rausch) {
            return [notiz(uet("Jedes Foto bekommt eigenes Rauschen. Ausschalten hält den Schauplatz über die Serie gleich.", "ui")), takesZeile];
          }
          const zeile = document.createElement("div");
          zeile.className = "k2-feld";
          const n = document.createElement("div");
          n.className = "k2-name";
          n.textContent = "Seed";
          const feld = document.createElement("input");
          feld.type = "number";
          feld.min = "0";
          feld.value = String(state.serienSeed ?? 0);
          feld.onchange = () =>
            schreib({ ...state, serienSeed: Math.max(0, parseInt(feld.value, 10) || 0) });
          // The actual way to work with this: try a few seeds, keep the one
          // whose room you like.
          const anders = document.createElement("button");
          anders.type = "button";
          anders.className = "k2-textknopf";
          anders.textContent = "↻ " + uet("Anderer Schauplatz", "ui");
          anders.title = uet("Anderen Schauplatz suchen", "ui");
          anders.onclick = () =>
            schreib({ ...state, serienSeed: Math.floor(Math.random() * 2147483647) });
          zeile.append(n, feld, anders);
          return [zeile, takesZeile];
        },
      },
    ];

    const liste = document.createElement("div");
    liste.className = "k2-achsen";
    for (const a of achsen) liste.append(achse(a, state));
    root.append(liste);

    // --- warnings -------------------------------------------------------------
    // Always visible, never behind a click: these are contradictions in the
    // wiring or between two axes, and a folded-away notice reaches nobody.
    const warne = (text, titel) => {
      const w = document.createElement("div");
      w.className = "k2-warn";
      w.textContent = text;
      if (titel) w.title = titel;
      root.append(w);
    };
    if (massAnliegend && state.aktiv?.format) {
      warne(uet("⚠ width/height liegen an, werden aber ignoriert — Format ausschalten", "ui"));
    }
    if (state.aktiv?.fokus && !fokusWirksam.length) {
      const namen = fokusGewaehlt.map((f) => uet(f, "shooting/fokus")).join(", ");
      warne(`⚠ ${namen} ` + uet("passt zu keiner gewählten Einstellung", "ui") + " " +
            uet("— es kommt gar kein Schwerpunkt in den Prompt", "ui"),
            uet("Der Schwerpunkt ist an die Kameraeinstellung gekoppelt. Entweder ", "ui") +
            uet("eine passende Einstellung dazuwählen oder einen anderen ", "ui") +
            uet("Schwerpunkt. Die durchgestrichenen Einträge sind die, die mit den ", "ui") +
            uet("aktuellen Einstellungen nicht vorkommen können.", "ui"));
    } else if (state.aktiv?.fokus && fokusWirksam.length < fokusGewaehlt.length) {
      const tot = fokusGewaehlt.filter((f) => !erreichbar.has(f)).map((f) => uet(f, "shooting/fokus"));
      warne(`${tot.join(", ")} ` + uet("kommt mit den gewählten Einstellungen nicht vor", "ui"),
            uet("Nicht schlimm - die übrigen Schwerpunkte greifen weiterhin.", "ui"));
    }
    // A fixed seed only holds the setting together while the image size stays
    // the same: the noise is a tensor in image dimensions.
    if (!state.aktiv?.rausch && state.aktiv?.format) {
      warne("⚠ " + uet("Format würfelt — bei wechselnder Größe wirkt der Serien-Seed nicht", "ui"),
            uet("Das Rauschen hat Bildmaße. Ändert sich das Seitenverhältnis, ist es ", "ui") +
            uet("ein anderes Rauschfeld, auch bei gleichem Seed.", "ui"));
    }

    // --- contact sheet ---------------------------------------------------------
    // Every photo as a frame in its real ratio, like the frames in the logo;
    // once rendered, with the picture in it. A click shows the details and the
    // actions below: favourite, mark for a re-shoot, open the picture.
    const favoriten = new Set((state.favoriten || []).map(Number));
    const bogen = document.createElement("div");
    bogen.className = "k2-bogen";
    const gezeigt = Math.min(24, anzahl);
    const kopf = document.createElement("div");
    kopf.className = "k2-bogen-kopf";
    const kl = document.createElement("span");
    kl.textContent = uet("Kontaktbogen", "ui");
    const kr = document.createElement("span");
    kr.textContent = anzahl > gezeigt
      ? uetf("erste {0} von {1}", "ui", gezeigt, anzahl)
      : uetf("{0} Fotos", "ui", anzahl);
    kopf.append(kl, kr);
    const raster = document.createElement("div");
    raster.className = "k2-bilder";
    const plaene = [];
    if (gewaehlt == null || gewaehlt < start || gewaehlt >= start + gezeigt) gewaehlt = start;
    for (let i = 0; i < gezeigt; i++) {
      const nr = start + i;
      const lauf = nr - 1;
      const p = plane(d, state, lauf, outfitZahl);
      const [bw, bh] = extern || masse(d, p.kamera, lauf, state);
      const o = outfitZahl ? outfits[outfitFuer(d, state, lauf, outfitZahl)] : null;
      plaene.push({ nr, p, bw, bh, o });
      const hoehe = 46, breite = 52;
      const w = Math.min(breite, (hoehe * bw) / bh), h = Math.min(hoehe, (breite * bh) / bw);
      const bild = bildFuer(state, nr);
      const b = document.createElement("button");
      b.type = "button";
      b.className = "k2-bild" + (nr === gewaehlt ? " k2-gewaehlt" : "") + (bild ? " k2-fertig" : "");
      b.setAttribute("aria-label", uetf("Foto {0}", "ui", nr));
      const rahmen = document.createElement("div");
      rahmen.className = "k2-rahmen";
      rahmen.style.width = w + "px";
      rahmen.style.height = h + "px";
      if (bild) rahmen.style.backgroundImage = `url("${bild.klein}")`;
      const nummer = document.createElement("i");
      nummer.textContent = String(nr);
      rahmen.append(nummer);
      // Costume changes: a stripe in the outfit's main colour under the frame.
      if (o) {
        const streifen = document.createElement("b");
        streifen.className = "k2-ostreifen";
        streifen.style.background = hauptfarbe(o);
        streifen.title = o.name;
        rahmen.append(streifen);
      }
      if (favoriten.has(nr) || markiert.has(nr)) {
        const zeichen = document.createElement("em");
        zeichen.textContent = (favoriten.has(nr) ? "♥" : "") + (markiert.has(nr) ? "↻" : "");
        rahmen.append(zeichen);
      }
      const unter = document.createElement("span");
      unter.className = "k2-bild-label";
      unter.textContent = p.kamera ? uet(p.kamera, "shooting/kamera") : "—";
      b.append(rahmen, unter);
      b.onclick = () => { gewaehlt = nr; zeichne(); };
      raster.append(b);
    }
    if (anzahl > gezeigt) {
      const mehr = document.createElement("span");
      mehr.className = "k2-mehr";
      mehr.textContent = `+${anzahl - gezeigt}`;
      raster.append(mehr);
    }
    bogen.append(kopf, raster);

    const g = plaene.find((x) => x.nr === gewaehlt);
    if (g) {
      const det = document.createElement("div");
      det.className = "k2-detail";
      const zeile = (k, v) => {
        if (!v) return;
        const a = document.createElement("span");
        a.textContent = k;
        const b = document.createElement("b");
        b.textContent = v;
        det.append(a, b);
      };
      const bild = bildFuer(state, g.nr);
      zeile(uet("Foto", "ui"), `${g.nr} · ${g.bw}×${g.bh}` +
        (bild && (bild.take || aufnahmen.get(g.nr)?.size > 1)
          ? " · " + uetf("Take {0}", "ui", bild.take + 1) : ""));
      zeile(uet("Kamera", "ui"), g.p.kamera &&
        `${uet(g.p.kamera, "shooting/kamera")} (${detailWort[d.kameraDetail?.[g.p.kamera]] || ""})`);
      zeile(uet("Pose", "ui"), [g.p.pose?.haltung && uet(g.p.pose.haltung, "pose/haltung"),
                                g.p.pose?.raum && uet(g.p.pose.raum, "pose/raum")].filter(Boolean).join(" · "));
      zeile(uet("Schwerpunkt", "ui"), g.p.fokus && uet(g.p.fokus, "shooting/fokus"));
      zeile(uet("Outfit", "ui"), g.o?.name);
      zeile(uet("Stimmung", "ui"), g.p.ausdruck?.stimmung && uet(g.p.ausdruck.stimmung, "ausdruck/stimmung"));

      // All takes of this photo side by side; a click makes one the chosen.
      const takes = aufnahmen.get(g.nr);
      if (takes && takes.size > 1) {
        const streifen = document.createElement("div");
        streifen.className = "k2-takes";
        for (const t of [...takes.keys()].sort((a, b) => a - b)) {
          const bt = takes.get(t);
          const k = document.createElement("button");
          k.type = "button";
          k.className = "k2-take" + (bild?.take === t ? " k2-an" : "");
          k.style.backgroundImage = `url("${bt.klein}")`;
          k.style.aspectRatio = `${g.bw} / ${g.bh}`;
          k.title = uetf("Take {0}", "ui", t + 1);
          const z = document.createElement("i");
          z.textContent = String(t + 1);
          k.append(z);
          k.onclick = () => schreib({ ...state, wahl: { ...(state.wahl || {}), [String(g.nr)]: t } });
          streifen.append(k);
        }
        det.append(streifen);
      }

      const aktionen = document.createElement("div");
      aktionen.className = "k2-aktionen";
      const fav = document.createElement("button");
      fav.type = "button";
      fav.className = "k2-textknopf" + (favoriten.has(g.nr) ? " k2-an" : "");
      fav.textContent = (favoriten.has(g.nr) ? "♥ " : "♡ ") + uet("Favorit", "ui");
      fav.onclick = () => {
        const f = new Set(favoriten);
        if (f.has(g.nr)) f.delete(g.nr); else f.add(g.nr);
        schreib({ ...state, favoriten: [...f].sort((a, b) => a - b) });
      };
      const mark = document.createElement("button");
      mark.type = "button";
      mark.className = "k2-textknopf" + (markiert.has(g.nr) ? " k2-an" : "");
      mark.textContent = "↻ " + uet("Nachfotografieren", "ui");
      mark.title = uet("Gleiche Planung, neues Rauschen", "ui");
      mark.onclick = () => {
        if (markiert.has(g.nr)) markiert.delete(g.nr); else markiert.add(g.nr);
        zeichne();
      };
      aktionen.append(fav, mark);
      if (bild) {
        const oeffnen = document.createElement("a");
        oeffnen.className = "k2-textknopf";
        oeffnen.href = bild.gross;
        oeffnen.target = "_blank";
        oeffnen.rel = "noopener";
        oeffnen.textContent = uet("Bild öffnen", "ui");
        aktionen.append(oeffnen);
      } else {
        const noch = document.createElement("span");
        noch.className = "k2-anotiz";
        noch.textContent = uet("noch nicht fotografiert", "ui");
        aktionen.append(noch);
      }
      det.append(aktionen);
      bogen.append(det);
    }

    if (markiert.size) {
      const leiste = document.createElement("div");
      leiste.className = "k2-nachhol";
      const los = document.createElement("button");
      los.type = "button";
      los.className = "k2-start k2-klein";
      los.textContent = markiert.size === 1
        ? uet("1 Foto nachfotografieren", "ui")
        : uetf("{0} Fotos nachfotografieren", "ui", markiert.size);
      los.onclick = () => nachfotografieren([...markiert].sort((a, b) => a - b));
      const weg = document.createElement("button");
      weg.type = "button";
      weg.className = "k2-textknopf";
      weg.textContent = uet("Auswahl aufheben", "ui");
      weg.onclick = () => { markiert.clear(); zeichne(); };
      leiste.append(los, weg);
      bogen.append(leiste);
    }
    root.append(bogen);
  }

  queueMicrotask(zeichne);
  queueMicrotask(ladeBilder);
  node._k2Zeichne = zeichne;

  // When a different ratio is chosen in the upstream node, this node hears
  // nothing about it - there is no event to hook onto and the connection stays
  // the same. So look rather than wait. Reading two numbers out of properties
  // costs nothing; a redraw only happens when they have actually changed, since
  // otherwise the caret in the number fields would be lost on every tick.
  const standJetzt = () => (externeMasse() || []).join("×");
  // Record immediately, not on the first tick. This started out as an initial
  // assignment inside the tick itself - which swallowed exactly the change that
  // happened between build and first tick, leaving the first switch on the
  // upstream node without effect.
  let letzteExtern = standJetzt();
  const ticker = setInterval(() => {
    // Once the node is deleted it no longer hangs off the graph. Without this
    // exit the tick would keep running until the page is reloaded.
    if (!node.graph) {
      clearInterval(ticker);
      return;
    }
    const jetzt = standJetzt();
    if (jetzt !== letzteExtern) {
      letzteExtern = jetzt;
      zeichne();
    }
  }, 500);

  // The height follows the node: hard-wired, everything below the edge stayed
  // unreachable and dragging it larger did not help.
  const CHROM = 72; // title and outputs - the photo-number row is hidden now
  const w = node.addDOMWidget("k2_shooting", "custom", root, {
    getValue: () => node.properties?.[PROP],
    setValue: () => {},
    getMinHeight: () => 240,
    getMaxHeight: () => Math.max(240, (node.size?.[1] || 560) - CHROM),
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
      // Loaded from a workflow: its saved size stands (see nodeCreated).
      this._k2Geladen = true;
      const r = orig?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
    // A wardrobe wired in or out changes the outfit axis and the stripes.
    const origVerbindung = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function () {
      const r = origVerbindung?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
  },

  async nodeCreated(node) {
    if (node.comfyClass !== CLASS_TYPE) return;
    const presets = await ladePresets();
    if (!presets?.shooting) return;
    // Brand strip, series row, start, six axes and a contact sheet of twelve
    // frames with its detail box. Only for new nodes - when a workflow is
    // loaded, onConfigure puts the saved size back afterwards.
    // The default size only for a new node. nodeCreated awaits the presets,
    // and a workflow's configure() runs in the meantime - setting the size
    // here unconditionally threw away every saved size.
    if (!node._k2Geladen) node.size = [360, 760];
    baue(node, presets.shooting, presets.person);
  },
});

// Only for cross-checking against Python.
export { plane as _plane, format as _format, masse as _masse };

