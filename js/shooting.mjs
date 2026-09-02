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
  registriereStateInjektion,
  schreibeState,
  t as uet,
  tf as uetf,
} from "./shared.mjs?v=2.3.0";

import { app } from "../../scripts/app.js";

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
           rausch: true },
  pools: {},
  kameras: null, // null = alle
  fokusse: null,
  serienSeed: 0,
  start: 1, // photo number the series begins with
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

function plane(d, state, lauf) {
  const aktiv = state.aktiv || {};
  let kamera = null;
  const pose = {}, ausdruck = {};

  d.felder.forEach((f, platz) => {
    if (!aktiv[f.quelle]) return;
    if (f.quelle === "kamera") {
      const erlaubt = state.kameras?.length ? state.kameras : d.kamera.map((k) => k.label);
      kamera = waehle(erlaubt, lauf, platz, d);
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
    const erlaubt = (d.kameraFokus[kamera] || []).filter(
      (f) => !state.fokusse?.length || state.fokusse.includes(f),
    );
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
function baue(node, d) {
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root";
  installCanvasZoomPassthrough(root);

  const lies = () => leseState(node, PROP, VORGABE);
  const schreib = (s) => {
    schreibeState(node, PROP, s);
    zeichne();
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
  // "erreichbar" (optional) marks entries that cannot occur at all with the
  // remaining settings - they stay clickable but look dead, and say why in the
  // tooltip.
  function chipreihe(alle, gewaehltRoh, sichern, erreichbar, bereich) {
    const chips = document.createElement("div");
    chips.className = "k2-chips";
    const gewaehlt = gewaehltRoh?.length ? gewaehltRoh : alle.map((x) => x.label);
    for (const e of alle) {
      const c = document.createElement("div");
      const an = gewaehlt.includes(e.label);
      const tot = erreichbar && !erreichbar.has(e.label);
      c.className = "k2-chip" + (an ? " k2-an" : "") + (tot ? " k2-tot" : "");
      c.textContent = bereich ? uet(e.label, bereich) : e.label;
      c.title = tot
        ? e.wert + uet(" — passt zu keiner der gewählten Kameraeinstellungen", "ui")
        : e.wert;
      c.onclick = () => {
        let neu = an ? gewaehlt.filter((x) => x !== e.label) : [...gewaehlt, e.label];
        if (!neu.length) neu = [e.label]; // nie alle abwaehlen
        sichern(neu);
      };
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

  // One axis row. The dot toggles the axis, the rest unfolds it.
  function achse({ schluessel, name, stand, hinweis, inhalt }, state) {
    const an = !!state.aktiv?.[schluessel];
    const zeile = document.createElement("div");
    const klappbar = !!inhalt;
    zeile.className = "k2-achse" + (an ? " k2-hell" : "") + (klappbar ? "" : " k2-zu");
    zeile.title = hinweis;

    const punkt = document.createElement("div");
    punkt.className = "k2-punkt" + (an ? " k2-an" : "");
    punkt.onclick = (e) => {
      e.stopPropagation();
      // Fold up when switching off too - an open block belonging to a silent
      // axis shows settings that currently do nothing.
      if (an && offen === schluessel) offen = null;
      schreib({ ...state, aktiv: { ...state.aktiv, [schluessel]: !an } });
    };

    const n = document.createElement("div");
    n.className = "k2-achse-name";
    n.textContent = name;

    const w = document.createElement("div");
    w.className = "k2-achse-wert";
    w.textContent = stand;

    const p = document.createElement("div");
    p.className = "k2-pfeil";
    p.textContent = klappbar ? (offen === schluessel ? "▾" : "▸") : "";

    zeile.append(punkt, n, w, p);
    if (klappbar) {
      zeile.onclick = () => {
        offen = offen === schluessel ? null : schluessel;
        zeichne();
      };
    }
    return zeile;
  }

  async function starte(anzahl, start) {
    // Set the counter to the start number and to increment, so that the
    // series begins there and not where the last run left off. "seed" is the
    // old name of the same widget, from before it was 1-based.
    const zaehler = node.widgets?.find((w) => w.name === "foto" || w.name === "seed");
    if (zaehler) zaehler.value = Math.max(1, start || 1);
    const ctrl = node.widgets?.find(
      (w) => w.name === "control_after_generate" || w.name === "control_after_generated",
    );
    if (ctrl) ctrl.value = "increment";
    try {
      await app.queuePrompt(0, anzahl);
    } catch (e) {
      console.error("[Photoshoot] Einreihen fehlgeschlagen:", e);
    }
  }

  function zeichne() {
    const state = lies();
    root.textContent = "";

    // --- count and start button ----------------------------------------------
    const kopf = document.createElement("div");
    kopf.className = "k2-feld";
    const lbl = document.createElement("div");
    lbl.className = "k2-name";
    lbl.textContent = uet("Fotos", "ui");
    lbl.style.flex = "0 0 auto"; // five things share this row
    const zahl = document.createElement("input");
    zahl.type = "number";
    zahl.min = "1";
    zahl.max = "500";
    zahl.value = String(state.anzahl ?? 12);
    zahl.style.flex = "0 0 56px";
    zahl.onchange = () => {
      const n = Math.max(1, Math.min(500, parseInt(zahl.value, 10) || 1));
      schreib({ ...state, anzahl: n });
    };
    const anzahl = state.anzahl ?? 12;
    const start = Math.max(1, parseInt(state.start, 10) || 1);
    // Where the series begins. A new number is a new series with the same
    // settings - the answer to "how do I get different photos?", which used
    // to require editing the prompt. The die draws one; six digits so it stays
    // readable in the widget. Typing a number back in brings a series back.
    const abLbl = document.createElement("div");
    abLbl.className = "k2-achse-wert";
    abLbl.textContent = uet("ab", "ui");
    const ab = document.createElement("input");
    ab.type = "number";
    ab.min = "1";
    ab.value = String(start);
    ab.style.flex = "0 0 62px";
    ab.title = uet("Startnummer. Die Serie beginnt bei diesem Foto.", "ui");
    ab.onchange = () =>
      schreib({ ...state, start: Math.max(1, parseInt(ab.value, 10) || 1) });
    const neu = document.createElement("div");
    neu.className = "k2-chip";
    neu.textContent = "🎲";
    neu.title = uet("Neue Serie: zufällige Startnummer, gleiche Einstellungen", "ui");
    neu.onclick = () =>
      schreib({ ...state, start: 1 + Math.floor(Math.random() * 999999) });
    // The duration sits next to the count and no longer on the button: it
    // belongs to the number that is set, and the button now says only what it
    // does.
    const dauerLbl = document.createElement("div");
    dauerLbl.className = "k2-achse-wert";
    dauerLbl.style.marginLeft = "auto";

    const knopf = document.createElement("div");
    knopf.className = "k2-start";
    knopf.textContent = uet("Shooting starten", "ui");
    const beschrifte = (sek) => {
      const gesamt = anzahl * sek;
      dauerLbl.textContent = uet("ca. ", "ui") + (gesamt < 90
        ? `${Math.round(gesamt)} s`
        : `${Math.round(gesamt / 60)} min`);
      dauerLbl.title =
        sek.toFixed(1) + " " + uet("s je Bild, gemessen an den letzten Läufen", "ui");
      knopf.title = anzahl + " " + uet("Durchläufe einreihen", "ui") + ", " +
        uetf("ab Foto {0}", "ui", start);
    };
    beschrifte(_sekProBild);
    // Measure and label as soon as the history is available.
    messeSekundenProBild().then(beschrifte);
    knopf.onclick = () => starte(anzahl, start);
    kopf.append(lbl, zahl, abLbl, ab, neu, dauerLbl);
    root.append(kopf, knopf);

    // --- the six axes --------------------------------------------------------
    // Are dimensions arriving from outside? That decides what the ratio switch
    // means.
    const verbunden = (name) => !!node.inputs?.find((i) => i.name === name)?.link;
    const massAnliegend = verbunden("width_in") && verbunden("height_in");
    // Applies only when the ratio is not being varied - shooting.py decides it
    // the same way. Otherwise the framing determines the ratio.
    const extern = massAnliegend && !state.aktiv?.format ? externeMasse() : null;

    const zaehlstand = (alle, gewaehlt) =>
      !gewaehlt?.length || gewaehlt.length === alle.length
        ? uet("alle", "ui")
        : uetf("{0} von {1}", "ui", gewaehlt.length, alle.length);

    const familienStand = (quelle) => state.pools?.[d.gruppen[quelle].feld] ?? d.alle;
    // The state as displayed: the same value, only translated.
    const familienStandText = (quelle) => {
      const v = familienStand(quelle);
      return v === d.alle ? uet("alle", "ui") : uet(v, "familien");
    };

    // Which focus values can occur at all with the chosen settings. The focus
    // is coupled to the camera - a wide shot does not focus on the lips - and if
    // nothing is left after filtering, the photo gets none at all. That is
    // deliberate, but it was invisible: you clicked "feet" and nothing appeared
    // in the prompt.
    const gewaehlteKameras = state.kameras?.length
      ? state.kameras
      : d.kamera.map((k) => k.label);
    const erreichbar = new Set(
      state.aktiv?.kamera
        ? gewaehlteKameras.flatMap((k) => d.kameraFokus[k] || [])
        : d.fokus.map((f) => f.label),
    );
    const fokusGewaehlt = state.fokusse?.length
      ? state.fokusse
      : d.fokus.map((f) => f.label);
    const fokusWirksam = fokusGewaehlt.filter((f) => erreichbar.has(f));

    const familienAuswahl = (quelle) => {
      const g = d.gruppen[quelle];
      return auswahl(
        [d.alle, ...Object.keys(g.familien)].map((o) => ({
          wert: o,
          text: o === d.alle ? uet("alle", "ui") : uet(o, "familien"),
        })),
        familienStand(quelle),
        (v) => schreib({ ...state, pools: { ...state.pools, [g.feld]: v } }),
      );
    };

    const seedFeld = () => {
      const zeile = document.createElement("div");
      zeile.className = "k2-feld";
      const feld = document.createElement("input");
      feld.type = "number";
      feld.min = "0";
      feld.value = String(state.serienSeed ?? 0);
      feld.onchange = () =>
        schreib({ ...state, serienSeed: Math.max(0, parseInt(feld.value, 10) || 0) });
      // The die is the actual way to work with this: you look for a setting by
      // trying a few seeds and keeping the one whose room you like.
      const wuerfel = document.createElement("div");
      wuerfel.className = "k2-chip";
      wuerfel.textContent = "🎲";
      wuerfel.title = uet("Anderen Schauplatz suchen", "ui");
      wuerfel.onclick = () =>
        schreib({ ...state, serienSeed: Math.floor(Math.random() * 2147483647) });
      zeile.append(feld, wuerfel);
      return zeile;
    };

    const achsen = [
      {
        schluessel: "kamera",
        name: uet("Kamera", "ui"),
        stand: state.aktiv?.kamera
          ? zaehlstand(d.kamera, state.kameras)
          : uet("fest", "ui"),
        hinweis: uet("Kameraeinstellung über die Serie variieren", "ui"),
        inhalt: state.aktiv?.kamera
          ? () => chipreihe(d.kamera, state.kameras,
                            (n) => schreib({ ...state, kameras: n }), null,
                            "shooting/kamera")
          : null,
      },
      {
        schluessel: "pose",
        name: uet("Pose", "ui"),
        stand: state.aktiv?.pose ? familienStandText("pose") : uet("fest", "ui"),
        hinweis: uet("Körperhaltung variieren. Aufgeklappt: auf eine Familie einschränken.", "ui"),
        inhalt: state.aktiv?.pose ? () => familienAuswahl("pose") : null,
      },
      {
        schluessel: "ausdruck",
        name: uet("Ausdruck", "ui"),
        stand: state.aktiv?.ausdruck ? familienStandText("ausdruck") : uet("fest", "ui"),
        hinweis: uet("Mimik variieren. Aufgeklappt: auf eine Stimmungsfamilie einschränken.", "ui"),
        inhalt: state.aktiv?.ausdruck ? () => familienAuswahl("ausdruck") : null,
      },
      {
        schluessel: "fokus",
        name: uet("Schwerpunkt", "ui"),
        stand: !state.aktiv?.fokus
          ? uet("aus", "ui")
          : fokusWirksam.length
            ? zaehlstand(d.fokus, state.fokusse)
            : uet("keiner passt", "ui"),
        hinweis: uet("Bildschwerpunkt variieren (Gesicht, Beine, Füße …). Welche ", "ui") +
                 uet("möglich sind, hängt von den gewählten Kameraeinstellungen ab.", "ui"),
        inhalt: state.aktiv?.fokus
          ? () => chipreihe(d.fokus, state.fokusse,
                            (n) => schreib({ ...state, fokusse: n }), erreichbar,
                            "shooting/fokus")
          : null,
      },
      {
        schluessel: "format",
        name: uet("Format", "ui"),
        stand: state.aktiv?.format
          ? uet("gewürfelt", "ui")
          : massAnliegend
            ? (extern ? `${extern[0]}×${extern[1]}` : uet("von außen", "ui"))
            : state.festesFormat || "2:3",
        hinweis: uet("An: Seitenverhältnis passend zur Kameraeinstellung würfeln. ", "ui") +
                 uet("Aus: ein festes Verhältnis für alle Fotos.", "ui"),
        // With dimensions arriving there is nothing to choose - the upstream
        // node determines the resolution.
        inhalt: !state.aktiv?.format && !massAnliegend
          ? () => auswahl(
              Object.keys(d.ratios).map((r) => {
                const [w, h] = masseFuer(d, r, state.groesse || d.kanteStandard);
                return { wert: r, text: `${r}  ·  ${w}×${h}` };
              }),
              state.festesFormat || "2:3",
              (v) => schreib({ ...state, festesFormat: v }),
            )
          : null,
      },
      {
        schluessel: "rausch",
        name: uet("Rauschen", "ui"),
        stand: state.aktiv?.rausch
          ? uet("pro Foto", "ui")
          : uetf("Seed {0}", "ui", state.serienSeed ?? 0),
        hinweis: uet("An: jedes Foto bekommt eigenes Rauschen. Aus: die ganze Serie ", "ui") +
                 uet("teilt einen Seed, dann bleibt der Schauplatz über die Fotos gleich.", "ui"),
        inhalt: state.aktiv?.rausch ? null : seedFeld,
      },
    ];

    const liste = document.createElement("div");
    liste.className = "k2-achsen";
    for (const a of achsen) {
      liste.append(achse(a, state));
      if (offen === a.schluessel && a.inhalt) {
        const auf = document.createElement("div");
        auf.className = "k2-auf";
        auf.append(a.inhalt());
        liste.append(auf);
      }
    }
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
    // The case people stumbled over: camera "wide shot", focus "back" - the
    // intersection was empty, so no focus appeared in the prompt at all, and
    // nothing said so.
    if (state.aktiv?.fokus && !fokusWirksam.length) {
      const namen = fokusGewaehlt.map((f) => uet(f, "shooting/fokus")).join(", ");
      warne(`⚠ ${namen} ` + uet("passt zu keiner gewählten Einstellung", "ui") + " " +
            uet("— es kommt gar kein Schwerpunkt in den Prompt", "ui"),
            uet("Der Schwerpunkt ist an die Kameraeinstellung gekoppelt. Entweder ", "ui") +
            uet("eine passende Einstellung dazuwählen oder einen anderen ", "ui") +
            uet("Schwerpunkt. Die durchgestrichenen Einträge sind die, die mit den ", "ui") +
            uet("aktuellen Einstellungen nicht vorkommen können.", "ui"));
    } else if (state.aktiv?.fokus && fokusWirksam.length < fokusGewaehlt.length) {
      const tot = fokusGewaehlt
        .filter((f) => !erreichbar.has(f))
        .map((f) => uet(f, "shooting/fokus"));
      warne(`${tot.join(", ")} ` + uet("kommt mit den gewählten Einstellungen nicht vor", "ui"),
            uet("Nicht schlimm - die übrigen Schwerpunkte greifen weiterhin.", "ui"));
    }
    // A fixed seed only holds the setting together while the image size stays
    // the same: the noise is a tensor in image dimensions, and a different ratio
    // gives a different tensor. Without this notice the series seed looks
    // broken.
    if (!state.aktiv?.rausch && state.aktiv?.format) {
      warne("⚠ " + uet("Format würfelt — bei wechselnder Größe wirkt der Serien-Seed nicht", "ui"),
            uet("Das Rauschen hat Bildmaße. Ändert sich das Seitenverhältnis, ist es ", "ui") +
            uet("ein anderes Rauschfeld, auch bei gleichem Seed.", "ui"));
    }

    // --- size, applies to every axis -----------------------------------------
    // When the upstream node determines the resolution, our own size no longer
    // has any effect. In that case the actual value stands here instead of a
    // choice that would do nothing.
    if (massAnliegend && !state.aktiv?.format) {
      const zeile = document.createElement("div");
      zeile.className = "k2-feld";
      const n = document.createElement("div");
      n.className = "k2-name";
      n.textContent = uet("Größe", "ui");
      const w = document.createElement("div");
      w.className = "k2-achse-wert";
      w.style.maxWidth = "none";
      w.textContent = extern
        ? `${extern[0]}×${extern[1]}  ·  ` + uet("von außen", "ui")
        : uet("von außen — Wert erst beim Ausführen bekannt", "ui");
      zeile.title =
        uet("width_in und height_in liegen an und haben Vorrang. Die eigene ", "ui") +
        uet("Größenstufe wirkt erst wieder, wenn dort nichts angeschlossen ist ", "ui") +
        uet("oder das Format gewürfelt wird.", "ui");
      zeile.append(n, w);
      root.append(zeile);
    } else {
      const zeile = auswahl(
        // Deliberately no example ratio in the label: it used to read
        // "1088×1632 at 2:3", and that read like a commitment to 2:3 even
        // though the ratio comes from the framing.
        d.kanten.map((k) => ({
          wert: String(k),
          text: `${k} px  ·  ${((k * k) / 1e6).toFixed(1)} MP`,
        })),
        String(state.groesse || d.kanteStandard),
        (v) => schreib({ ...state, groesse: parseInt(v, 10) }),
        uet("Größe", "ui"),
      );
      zeile.title =
        uet("Kantenlänge im Quadrat. Das Seitenverhältnis kommt von der ", "ui") +
        uet("Kameraeinstellung, nicht von hier.", "ui");
      root.append(zeile);
    }

    // --- preview of the first photos -----------------------------------------
    // Short form: the base posture without its opening ("Auf dem Rücken
    // liegend" becomes "Rücken liegend"), and the dimensions only when they
    // change against the line above. That fits ten photos into the space of
    // six. Translate first, then shorten. The regex is a German space
    // optimisation and simply does not match English labels - those are shorter
    // anyway ("Lying on the back" against "Auf dem Rücken liegend"), so there
    // everything simply stays as it is.
    const kurz = (s, bereich) =>
      uet(s, bereich).replace(/^Auf (dem|der|einem|einer|allen) /, "");
    const v = document.createElement("div");
    v.className = "k2-vorschau k2-lang";
    const zeilen = [];
    let letzteMasse = null;
    const gezeigt = Math.min(10, anzahl);
    // Numbered as the widget counts: photo 1 is run 0, and a series that
    // begins at 500 shows 500.
    const breite = Math.max(2, String(start + anzahl - 1).length);
    for (let i = 0; i < gezeigt; i++) {
      const lauf = start - 1 + i;
      const p = plane(d, state, lauf);
      const teile = [];
      if (p.kamera) {
        const det = d.kameraDetail?.[p.kamera];
        // Detail level in short form - a reminder that wide framings shrink
        // the person block. Two letters rather than one: in English "full" and
        // "figure" both start with F. Translated, or German abbreviations would
        // stand in an English interface.
        const detKurz = uet({ identitaet: "Id", figur: "Fi", voll: "Vo" }[det], "ui");
        const kam = uet(p.kamera, "shooting/kamera");
        teile.push(detKurz ? `${kam}[${detKurz}]` : kam);
      }
      if (p.pose?.haltung) teile.push(kurz(p.pose.haltung, "pose/haltung"));
      if (p.pose?.raum) teile.push(uet(p.pose.raum, "pose/raum"));
      if (p.fokus) teile.push("→" + uet(p.fokus, "shooting/fokus"));
      if (p.ausdruck?.stimmung) teile.push(uet(p.ausdruck.stimmung, "ausdruck/stimmung"));
      const [bw, bh] = extern || masse(d, p.kamera, lauf, state);
      const m = `${bw}×${bh}`;
      if (m !== letzteMasse) {
        teile.push(m);
        letzteMasse = m;
      }
      zeilen.push(`${String(start + i).padStart(breite)}  ${teile.join(" · ")}`);
    }
    if (anzahl > gezeigt) {
      zeilen.push("  " + uetf("…  bis {0}", "ui", start + anzahl - 1));
    }
    v.textContent = zeilen.join("\n");
    v.style.whiteSpace = "pre";
    root.append(v);
  }

  queueMicrotask(zeichne);
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
  const CHROM = 104; // title, photo-number row, outputs
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
      const r = orig?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
  },

  async nodeCreated(node) {
    if (node.comfyClass !== CLASS_TYPE) return;
    const presets = await ladePresets();
    if (!presets?.shooting) return;
    // Folded up, the panel needs around 380 px; the rest is room for one open
    // axis. Only for new nodes - when a workflow is loaded, onConfigure puts the
    // saved size back afterwards.
    node.size = [340, 480];
    baue(node, presets.shooting);
  },
});

// Only for cross-checking against Python.
export { plane as _plane, format as _format, masse as _masse };

