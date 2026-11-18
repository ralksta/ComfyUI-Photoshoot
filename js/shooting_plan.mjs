// Pure series planning logic for the photoshoot node.
//
// Kept free of ComfyUI/DOM imports so tests/plan.mjs can load it directly and
// compare every computed photo field-for-field against nodes/shooting.py.

// Has to match DEFAULT_STATE in nodes/shooting.py (checked by tests/plan.mjs).
export const VORGABE = {
  anzahl: 12,
  aktiv: {
    kamera: true, pose: true, ausdruck: true, format: true, fokus: true,
    rausch: true, outfit: true, set: true, licht: false, perspektive: false,
  },
  serienSeed: 0,
  start: 1,
  pools: {},
  takes: {},
  favoriten: [],
  abdeckung: false,
  reihenfolge: null,
  bogen: false,
  outfitFolge: "bloecke",
  setFolge: "bloecke",
  lichtFolge: "je_set",
  lichtPool: "alle",
  takesJeFoto: 1,
  wahl: {},
  entwurf: false,
  ordner: "photoshoot",
  kameras: ["Detail", "Nahaufnahme", "Porträt", "Halbtotale", "Amerikanisch", "Ganzkörper", "Totale"],
  fokusse: ["Gesicht", "Augen", "Lippen", "Oberkörper", "Dekolleté", "Hände", "Taille", "Beine", "Füße", "Rücken", "Ganze Figur", "Raum"],
  perspektiven: null,
  kameraOptik: false,
  requisiten: false,
  requisitText: "",
  groesse: 1328,
  festesFormat: "2:3",
  outfitAuswahl: null,
  verworfen: [],
  runde: 1,
  runden: [],
};

// ------------------------------------------- Selection as done in Python ---
// Has to stay character-for-character equivalent to shooting.py, or the preview
// shows something other than what comes out later. Deliberately without bit
// operations: "| 1" would truncate to 32 bits in JavaScript and compute wrongly
// for denominators from 2^31 upwards.
export function schritt(platz, d) {
  const frac = Math.sqrt(d.wurzeln[platz % d.wurzeln.length]) % 1;
  const s = Math.floor(frac * d.nenner);
  return s % 2 === 0 ? s + 1 : s;
}

export function waehle(labels, lauf, platz, d) {
  const n = labels?.length || 0;
  if (!n) return null;
  const s = schritt(platz, d);
  // Python multiplies exactly; a double only up to 2^53, which lauf * step
  // passes from photo 2^21 or so - beyond that the product goes through BigInt.
  const produkt = lauf * s;
  const pos = Number.isSafeInteger(produkt)
    ? produkt % d.nenner
    : Number((BigInt(lauf) * BigInt(s)) % BigInt(d.nenner));
  return labels[Math.floor((pos * n) / d.nenner)];
}

// Has to be the same restriction as _pool() in shooting.py, step for step, or
// the preview shows a different photo from the one that is computed later
// (tests/plan.mjs compares the two). On a selfie photo, what a hand holding
// the phone leaves.
export const istSelfie = (d, p) => !!p && (d.selfies || []).includes(p);

// Same as arme_mit_freier_hand() in pose_builder.py.
export function armeMitFreierHand(d, haltung) {
  const frei = d.eineHandFrei || [];
  const erlaubt = d.haltungArme?.[haltung];
  if (!erlaubt) return [...frei];
  return frei.filter((l) => erlaubt.includes(l) ||
    ((d.selfieGesten || []).includes(l) && erlaubt.includes("Eine Hand am Gesicht")));
}

export function pool(d, quelle, cat, state, kamera, haltung, stimmung) {
  const labels = poolOhneSelfie(d, quelle, cat, state, kamera, haltung, stimmung);
  const p = state._perspektive;
  const selfie = istSelfie(d, p);
  const festHaltung = p && d.perspektiveHaltung?.[p];
  if (!labels.length) return labels;
  if (cat === "haltung" && (selfie || festHaltung)) {
    if (selfie) {
      const frei = labels.filter((l) => armeMitFreierHand(d, l).length && (!festHaltung || festHaltung.includes(l)));
      return frei.length ? frei : festHaltung ? [...festHaltung] : labels;
    }
    const gefiltert = labels.filter((l) => festHaltung.includes(l));
    return gefiltert.length ? gefiltert : [...festHaltung];
  }
  if (!selfie) return labels;
  if (cat === "arme") {
    const frei = haltung ? armeMitFreierHand(d, haltung) : [...(d.eineHandFrei || [])];
    return frei.length ? frei : labels;
  }
  if (cat === "koerper") {
    const vorn = labels.filter((l) => (d.selfieKoerper || []).includes(l));
    return vorn.length ? vorn : labels;
  }
  return labels;
}

export function poolOhneSelfie(d, quelle, cat, state, kamera, haltung, stimmung) {
  const wahl = state.pools?.[cat] ?? d.alle;
  if (wahl === d.leer) return [];
  let alle = d.listen[quelle][cat] || [];
  const weg = d.blick?.wegStimmungen || [];
  const kameraStimmungen = d.blick?.kameraStimmungen || [];
  // Selfie gestures, hand props and selfie moods stay out unless asked for.
  const selfie = istSelfie(d, state._perspektive);
  if (cat === "arme") {
    if (!selfie) alle = alle.filter((l) => !(d.selfieGesten || []).includes(l));
    if (!state.requisiten || selfie) alle = alle.filter((l) => !(d.requisiten || []).includes(l));
  }
  const nurAufWahl = cat === "stimmung" ? alle.filter((l) => (d.stimmungNurAufWahl || []).includes(l)) : [];
  const frei = alle.filter((l) => !nurAufWahl.includes(l));
  // A mood arc names the moods of this photo's stage (see plane()).
  if (cat === "stimmung" && state._stimmungen?.length) {
    const nur = frei.filter((l) => state._stimmungen.includes(l));
    return nur.length ? nur : frei;
  }
  const g = d.gruppen[quelle];
  if (cat === g.feld && wahl !== d.alle) {
    // One family, or several as a list (the next round narrows to the
    // favourites' families).
    const erlaubt = (Array.isArray(wahl) ? wahl : [wahl])
      .flatMap((f) => (typeof f === "string" && g.familien[f]) || []);
    let gewaehlt = alle.filter((l) => erlaubt.includes(l) || (selfie && nurAufWahl.includes(l)));
    if (cat === "stimmung" && state._blickWeg) {
      const ohne = gewaehlt.filter((l) => !kameraStimmungen.includes(l));
      if (ohne.length) gewaehlt = ohne;
    }
    // A photo that looks into the camera gets no mood that looks away.
    if (cat === "stimmung" && state._blickKamera) {
      const blickend = gewaehlt.filter((l) => !weg.includes(l));
      return blickend.length ? blickend : gewaehlt;
    }
    return gewaehlt;
  }
  if (!selfie) alle = frei;
  if (cat === "stimmung" && state._blickWeg) {
    const ohne = alle.filter((l) => !kameraStimmungen.includes(l));
    if (ohne.length) alle = ohne;
  }
  if (cat === "stimmung" && state._blickKamera) {
    const blickend = alle.filter((l) => !weg.includes(l));
    if (blickend.length) alle = blickend;
  }
  // ... and is not seen from behind; over the shoulder stays.
  if (cat === "koerper" && state._blickKamera) {
    const vorn = alle.filter((l) => l !== d.abgewandt);
    if (vorn.length) alle = vorn;
  }
  // The framing says how far away the figure may be, the base posture whether
  // it can cross the room at all - the placement has to satisfy both.
  if (cat === "raum" && kamera && d.kameraRaum?.[kamera]) {
    const erlaubt = d.kameraRaum[kamera];
    alle = alle.filter((l) => erlaubt.includes(l));
  }
  // Placement, tension, arms and legs against the base posture.
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

// Same as blick_modus() and _blick_in_kamera() in shooting.py: the gaze mode
// of the series, and whether this photo looks into the camera under it.
export function blickModus(d, state) {
  const m = state.blick;
  return (d.blick?.modi || []).includes(m) && m !== "gemischt" ? m : null;
}

export function blickInKamera(d, state, lauf) {
  const m = blickModus(d, state);
  return m === "kamera" || (m === "meist_kamera" && lauf % 3 !== 2);
}

// An axis switch as Python reads it: aktiv.get(key, True) - a key the state
// does not carry counts as on.
export function an(state, key) {
  const aktiv = state.aktiv || {};
  return key in aktiv ? !!aktiv[key] : true;
}

// Same as reihenfolge(), bogen_von() and _position() in shooting.py.
export function bogenVon(d, state) {
  const b = state.bogen;
  // True and "Aufbau" are the first version's one arc; "Freude" replaced it.
  if (b === true || b === "Aufbau") return "Freude";
  return d.boegen && d.boegen[b] ? b : null;
}

export function reihenfolgeVon(state) {
  const r = state.reihenfolge;
  if (r === "gezogen" || r === "reihum" || r === "weit_nah") return r;
  return state.abdeckung ? "reihum" : "gezogen";
}

export function position(state, lauf) {
  const n = Math.max(1, parseInt(state.anzahl, 10) || 1);
  const i = lauf - (Math.max(1, parseInt(state.start, 10) || 1) - 1);
  return [Math.min(Math.max(i, 0), n - 1), n];
}

// Same as outfit_auswahl() in shooting.py: the wardrobe indices in use.
export function outfitAuswahl(state, outfits) {
  const alle = [...Array(Math.max(0, outfits || 0)).keys()];
  const wahl = state.outfitAuswahl;
  if (!Array.isArray(wahl)) return alle;
  const liste = alle.filter((k) => wahl.includes(k));
  return liste.length ? liste : alle;
}

// Same as _im_block() in shooting.py: the position within the block where
// outfit and set stay the same (outfits and sets in blocks).
export function imBlock(state, lauf, outfits, saetze = 0) {
  const teile = [];
  if (outfits && an(state, "outfit") && state.outfitFolge !== "gemischt") {
    teile.push(outfitAuswahl(state, outfits).length);
  }
  if (saetze && an(state, "set") && state.setFolge !== "gemischt") teile.push(saetze);
  if (!teile.length) return null;
  const [i, n] = position(state, lauf);
  let anfang = 0, ende = n;
  for (const m of teile) {
    const b = Math.floor((i * m) / n);
    anfang = Math.max(anfang, Math.ceil((b * n) / m));
    ende = Math.min(ende, Math.ceil(((b + 1) * n) / m));
  }
  return [i - anfang, ende - anfang];
}

// Same as outfit_fuer() in shooting.py: which outfit this photo wears.
export function outfitFuer(d, state, lauf, outfits) {
  if (!outfits || !an(state, "outfit")) return null;
  const liste = outfitAuswahl(state, outfits);
  if (state.outfitFolge === "gemischt") {
    return waehle(liste, lauf, d.felder.length + 3, d);
  }
  const [i, n] = position(state, lauf);
  return liste[Math.floor((i * liste.length) / n)];
}

// Same as set_fuer() in shooting.py: which set this photo is taken in.
export function setFuer(d, state, lauf, anzahl) {
  if (!anzahl || !an(state, "set")) return null;
  const liste = [...Array(anzahl).keys()];
  if (state.setFolge === "gemischt") return waehle(liste, lauf, d.felder.length + 4, d);
  const [i, n] = position(state, lauf);
  return liste[Math.floor((i * liste.length) / n)];
}

// Same as licht_pool() and licht_fuer() in shooting.py: the setup of the
// light axis, fitted to the photo's set (outdoor light only outdoors).
export function lichtPool(d, state) {
  const alle = d.licht.setups;
  const wahl = state.lichtPool ?? d.alle;
  const namen = (Array.isArray(wahl) ? wahl : [wahl]).filter((f) => typeof f === "string" && d.licht.familien[f]);
  if (!namen.length) return alle;
  const liste = alle.filter((l) => namen.some((f) => d.licht.familien[f].includes(l)));
  return liste.length ? liste : alle;
}

export function lichtFuer(d, state, lauf, draussen = []) {
  if (!state.aktiv?.licht) return null;
  const L = d.licht;
  const k = setFuer(d, state, lauf, draussen.length);
  const dr = k != null ? draussen[k] ?? null : null;
  const passt = (l) => (dr === true ? !L.nurDrinnen.includes(l) : dr === false ? !L.nurDraussen.includes(l) : true);
  const platz = d.felder.length + 5;
  if (state.lichtFolge === "tageszeit") {
    const [i, n] = position(state, lauf);
    const stufe = L.tageslauf[Math.floor((i * L.tageslauf.length) / n)][1];
    const f = stufe.filter(passt);
    return waehle(f.length ? f : stufe, lauf, platz, d);
  }
  const p = lichtPool(d, state);
  const f = p.filter(passt);
  const liste = f.length ? f : p;
  if (state.lichtFolge === "gemischt") return waehle(liste, lauf, platz, d);
  return waehle(liste, (k ?? 0) + 1, platz, d);
}

// The stage of the day a photo is in, for the axis row (TAGESLAUF).
export function tagesStufe(d, state, lauf) {
  const [i, n] = position(state, lauf);
  return d.licht.tageslauf[Math.floor((i * d.licht.tageslauf.length) / n)][0];
}

export function plane(d, state, lauf, outfits = 0, saetze = 0) {
  let kamera = null;
  const pose = {}, ausdruck = {};
  const ordnung = reihenfolgeVon(state);
  const [i, n] = position(state, lauf);
  // In blocks, the framing order starts over with every outfit and every set
  // (plane() in shooting.py).
  const block = imBlock(state, lauf, outfits, saetze);
  // Mood arc: the stage follows the position in the series, equal parts.
  const bogen = bogenVon(d, state);
  if (bogen && an(state, "ausdruck")) {
    const stufen = d.boegen[bogen];
    state = { ...state, _stimmungen: stufen[Math.floor((i * stufen.length) / n)] };
  }
  if (blickInKamera(d, state, lauf)) state = { ...state, _blickKamera: true };
  else if (blickModus(d, state)) state = { ...state, _blickWeg: true };
  let perspektive = null;

  d.felder.forEach((f, platz) => {
    if (platz === 1) {
      // The perspective, once the framing is settled (plane() in shooting.py).
      perspektive = perspektiveFuer(d, state, kamera, lauf);
      if (perspektive) {
        state = { ...state, _perspektive: perspektive };
        const blick = d.perspektiveBlick?.[perspektive];
        if (blick === d.blick?.kamera) state._blickKamera = true;
        else if (blick === null) state._blickWeg = true;
      }
    }
    if (!an(state, f.quelle)) return;
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
  // Gaze mode of the series, as in plane() in shooting.py: only where the
  // gaze was drawn at all - a pool of NONE, the expression switched off or a
  // back view keep their "no gaze".
  const modus = blickModus(d, state);
  if (modus && ausdruck.blick) {
    const platz = d.felder.findIndex((f) => f.cat === "blick");
    let weg = d.blick.weg;
    if (pose.koerper === d.blick.schulterKoerper) weg = weg.filter((l) => l !== d.blick.schulterBlick);
    if (state._blickKamera) ausdruck.blick = d.blick.kamera;
    else if (!weg.includes(ausdruck.blick)) ausdruck.blick = waehle(weg, lauf, platz, d);
  }
  // A perspective that says where the eyes go sets the gaze, a mood that
  // blows the camera a kiss looks into it.
  if (ausdruck.blick) {
    if (perspektive && Object.hasOwn(d.perspektiveBlick || {}, perspektive)) {
      ausdruck.blick = d.perspektiveBlick[perspektive];
    } else if ((d.blick?.kameraStimmungen || []).includes(ausdruck.stimmung) && !state._blickWeg) {
      ausdruck.blick = d.blick.kamera;
    }
  }
  // The focus depends on the camera and is therefore drawn afterwards.
  let fokus = null;
  if (an(state, "fokus") && kamera) {
    let erlaubt = (d.kameraFokus[kamera] || []).filter(
      (f) => !state.fokusse?.length || state.fokusse.includes(f),
    );
    // As in shooting.py: a body turned away shows no face, so no face focus.
    if (d.abgewandt && pose.koerper === d.abgewandt) {
      erlaubt = erlaubt.filter((f) => !(d.fokusGesicht || []).includes(f));
    } else if (kamera === "Detail" && bogenVon(d, state) && an(state, "ausdruck")) {
      // As in shooting.py: with a mood arc a detail shot shows the face.
      const gesicht = erlaubt.filter((f) => (d.fokusGesicht || []).includes(f));
      if (gesicht.length) erlaubt = gesicht;
    }
    fokus = waehle(erlaubt, lauf, d.felder.length + 2, d);
  }
  return { kamera, fokus, perspektive, pose, ausdruck };
}

// Same as perspektive_fuer() in shooting.py: off unless switched on, the
// chosen perspectives that allow this framing, drawn on their own slot.
export function perspektiveFuer(d, state, kamera, lauf) {
  if (!state.aktiv?.perspektive) return null;
  const alle = (d.perspektive || []).map((p) => p.label);
  const wahl = state.perspektiven?.length ? state.perspektiven : alle;
  let erlaubt = alle.filter((l) => wahl.includes(l));
  if (kamera) erlaubt = erlaubt.filter((l) => (d.perspektiveKamera?.[l] || []).includes(kamera));
  return waehle(erlaubt, lauf, d.slotPerspektive, d);
}

// A selfie takes the phone's formats (PERSPEKTIVE_FORMATE).
export function format(d, kamera, lauf, state, perspektive = null) {
  if (!an(state, "format")) return state.festesFormat || "2:3";
  const erlaubt = d.perspektiveFormate?.[perspektive] || d.kameraFormate[kamera] || Object.keys(d.ratios);
  return waehle(erlaubt, lauf, d.felder.length + 1, d);
}

// Mirrors masse_fuer() from shooting.py.
export function masseFuer(d, ratio, kante) {
  const [rw, rh] = d.ratios[ratio] || [1, 1];
  const flaeche = kante * kante;
  const runde = (x) => Math.max(256, Math.round(x / 16) * 16);
  return [runde(Math.sqrt((flaeche * rw) / rh)), runde(Math.sqrt((flaeche * rh) / rw))];
}

export function masse(d, kamera, lauf, state, perspektive = null) {
  const kante = state.groesse || d.kanteStandard;
  return masseFuer(d, format(d, kamera, lauf, state, perspektive), kante);
}
