// The interface itself. Pose, expression, lighting, style and location are
// structurally identical - one long field with families, several short
// fields, a die on each - so one blueprint serves all five, fed from
// /krea2/presets. The location holds several sets as tabs ("mehrere"), each
// in that same shape.

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
  installCanvasZoomPassthrough,
  injiziereCSS,
  istKompakt,
  labelAusRequisit,
  ladePresets,
  leseState,
  markenleiste,
  merkeBenutzt,
  ortDraussen,
  ortGesperrt,
  ortName,
  passeKompaktAn,
  PROP_ANSICHT,
  presetFehler,
  registriereBauer,
  registriereStateInjektion,
  requisitVorschau,
  schreibeState,
  speichereEigenenEintrag,
  t,
  tf,
} from "./shared.mjs?v=2.9.0";

import { app } from "../../scripts/app.js";

// From this length on a field gets a search over its chips and a row of the
// recently used ones (90 moods, 30 light setups).
const LANGE_LISTE = 12;

// Build the English sentence from the current state - the same order and the
// same separator as compose_pose/compose_expression in Python. Fields being
// rolled cannot be resolved here (the roll happens server side with the seed),
// so they appear as placeholders.
function baueVorschau(daten, state, bereich, gesperrt = new Set()) {
  const teile = [];
  for (const cat of daten.reihenfolge) {
    if (gesperrt.has(cat)) continue;
    if (state.wuerfeln?.[cat]) {
      teile.push("⟨" + t(cat, "kategorien") + " " + t("wird gewürfelt", "ui") + "⟩");
      continue;
    }
    if (bereich === "pose" && cat === "arme" && (state.requisit || "").trim()) {
      const text = requisitVorschau(daten, state.requisit);
      if (text) teile.push(text);
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
  // labels for this node's labels live under that key. ziel: an element to
  // draw into instead of the node (the Studio sidebar) - the same panel on
  // the same state, without the node's widget, size and zoom handling.
  const { daten, prop, vorgabe, bereich, teil, ziel, mehrere } = opts;
  injiziereCSS();

  const root = document.createElement("div");
  root.className = "k2-root" + (ziel ? " k2-studio-panel" : "");
  if (!ziel) installCanvasZoomPassthrough(root);

  // Several sets (the Location node): the whole state with every set, the
  // open one clamped. The panel below works on the open set in the
  // blueprint's shape, as the Wardrobe does with its outfits.
  const liesGanz = () => {
    const g = leseState(node, prop, vorgabe);
    if (!Array.isArray(g.saetze) || !g.saetze.length) g.saetze = structuredClone(vorgabe.saetze);
    g.aktiv = Math.min(Math.max(0, parseInt(g.aktiv, 10) || 0), g.saetze.length - 1);
    return g;
  };
  const lies = () => {
    if (!mehrere) return leseState(node, prop, vorgabe);
    const g = liesGanz();
    const satz = g.saetze[g.aktiv] || {};
    return { felder: { ...vorgabe.saetze[0].felder, ...(satz.felder || {}) }, wuerfeln: { ...(satz.wuerfeln || {}) },
             gruppe: satz.gruppe || daten.alle, details: satz.details || "", eigene: satz.eigene };
  };
  // The Series reads the sets from this node's state: after a write, every
  // Series panel draws again (its set axis, its contact sheet).
  const serienNeuZeichnen = () => {
    for (const n of app.graph?._nodes || []) if (n.comfyClass === "Krea2Photoshooting") n._k2Zeichne?.();
  };
  const schreibGanz = (g) => {
    frageSatz = false;
    schreibeState(node, prop, g);
    zeichne();
    serienNeuZeichnen();
  };
  const schreib = (s) => {
    // The prompts of the custom entries in use travel with the workflow.
    s = { ...s, eigene: eigeneKopie(daten, s.felder, null, s.eigene) };
    if (mehrere) {
      const g = liesGanz();
      const alt = g.saetze[g.aktiv] || {};
      g.saetze[g.aktiv] = { id: alt.id || neueId(), name: alt.name || "", felder: s.felder,
                            wuerfeln: s.wuerfeln || {}, gruppe: s.gruppe || daten.alle,
                            details: s.details || "", ...(s.eigene ? { eigene: s.eigene } : {}) };
      schreibGanz(g);
      return;
    }
    schreibeState(node, prop, s);
    zeichne();
  };
  const neueId = () => "s" + Date.now().toString(36) + Math.floor(Math.random() * 1296).toString(36);
  let frageSatz = false;   // the delete button of a set asks once
  let wuerfelStand = { key: null, text: "", laedt: false };
  // Saved scenes (/krea2/szenen) for a set's free text; fetched once the
  // details row of the location is opened.
  let szenen = null;
  async function ladeSzenen() {
    try {
      const r = await fetch("/krea2/szenen", { cache: "no-store" });
      szenen = r.ok ? await r.json() : [];
    } catch (e) {
      szenen = [];
    }
    zeichne();
  }

  // Calm profile rows like the Person Builder: label, styled dropdown button,
  // and the die; clicking a button floats its list beneath the row without
  // shifting anything else. Which dropdown is open is view state only.
  let offen = null;
  let wahlSuche = "";
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

  function wahlBox(state, cat) {
    const schluessel = bereich + "/" + cat;
    const alleEintraege = daten.felder[cat] || [];
    const istLang = alleEintraege.length > LANGE_LISTE;
    const istFamilie = cat === gruppenFeld;
    let eintraege = alleEintraege;
    const kopfExtras = [];

    if (gesperrtJetzt(state).has(cat)) {
      kopfExtras.push(anotiz(t("Nur für Sets draußen – dieses Set ist drinnen (Studio oder Innenraum) und lässt das Feld weg.", "ui")));
    }
    if (istFamilie) {
      const fam = document.createElement("div");
      fam.className = "k2-chips";
      for (const g of [daten.alle, ...Object.keys(daten.gruppen || {})]) {
        fam.append(chip(g === daten.alle ? t("alle", "ui") : t(g, "familien"),
                        (state.gruppe || daten.alle) === g, () => schreib({ ...state, gruppe: g })));
        fam.lastChild.classList.add("k2-fam");
      }
      kopfExtras.push(fam);
      if (state.gruppe && state.gruppe !== daten.alle) {
        eintraege = eintraege.filter((e) => daten.gruppen[state.gruppe]?.includes(e.label));
      }
      if (daten.draussen) {
        kopfExtras.push(anotiz(t("Die Familie sagt der Serie auch, ob das Set drinnen oder draußen ist – danach richtet sich das Licht.", "ui")));
      }
    }
    if (!eintraege.length) {
      const leerHinweis = document.createElement("div");
      leerHinweis.className = "k2-anotiz k2-rendertest";
      leerHinweis.textContent = t("Noch keine getesteten Einträge — sie warten auf den Render-Test. Bis dahin: eigene Einträge (Custom entries) oder das Set unter Details als freier Text.", "ui");
      kopfExtras.push(leerHinweis);
    }

    const fussExtras = [];
    if (bereich === "pose" && cat === "arme") {
      const zeile = document.createElement("div");
      zeile.className = "k2-reihe";
      const inp = document.createElement("input");
      inp.className = "k2-frei";
      inp.placeholder = t("Eigenes Requisit (englisch), z. B. a vintage camera", "ui");
      inp.value = state.requisit || "";
      inp.onchange = () => {
        const val = inp.value;
        offen = null;
        wahlSuche = "";
        schreib({ ...state, requisit: val,
                  felder: val.trim() ? { ...state.felder, arme: daten.leer } : state.felder });
      };
      inp.onkeydown = (ev) => ev.stopPropagation();
      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.className = "k2-textknopf";
      saveBtn.textContent = "+";
      saveBtn.title = t("Als eigene Vorgabe speichern", "ui");
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
          offen = null;
          wahlSuche = "";
          const aktuell = lies();
          const wuerfeln = { ...(aktuell.wuerfeln || {}) };
          delete wuerfeln[cat];
          schreib({
            ...aktuell,
            requisit: "",
            wuerfeln,
            felder: { ...(aktuell.felder || {}), [cat]: savedLabel },
          });
          root.querySelector(`.k2-wahlknopf[data-feld="${cat}"]`)?.focus();
        } catch (err) {
          saveBtn.disabled = false;
          saveBtn.title = err?.message || String(err);
        }
      };
      zeile.append(inp, saveBtn);
      fussExtras.push(zeile);
    }

    const zumKnopf = () => root.querySelector(`.k2-wahlknopf[data-feld="${cat}"]`)?.focus();
    return baueWahlBox({
      feld: cat,
      eintraege,
      alleEintraege,
      aktiv: state.felder?.[cat] || daten.leer,
      leer: daten.leer,
      schluessel,
      beschriftung: (lbl) => beschriftung(cat, lbl),
      gruppen: istFamilie && (!state.gruppe || state.gruppe === daten.alle) ? daten.gruppen : null,
      wahlSuche,
      mitSuche: istLang,
      kopfExtras,
      fussExtras,
      onSuche: (v) => { wahlSuche = v; },
      onWaehle: (lbl) => {
        if (!leer(lbl) && istLang) merkeBenutzt(schluessel, lbl);
        offen = null;
        wahlSuche = "";
        // An entry that brings a field of its own along clears it (LEERT in
        // style_builder.py: the smartphone genre carries its own lens).
        const felder = { ...state.felder, [cat]: lbl };
        const wuerfeln = { ...(state.wuerfeln || {}) };
        delete wuerfeln[cat];
        for (const f of daten.leert?.[cat + "|" + lbl] || []) {
          felder[f] = daten.leer;
          delete wuerfeln[f];
        }
        const extra = bereich === "pose" && cat === "arme" ? { requisit: "" } : {};
        schreib({ ...state, ...extra, felder, wuerfeln });
        zumKnopf();
      },
      onFavorit: () => {
        zeichne();
        const neu = root.querySelector(".k2-wahlbox .k2-suche");
        neu?.focus();
        neu?.setSelectionRange(neu.value.length, neu.value.length);
      },
      onSchliessen: () => { offen = null; wahlSuche = ""; zeichne(); zumKnopf(); },
    });
  }

  function anotiz(text) {
    const n = document.createElement("div");
    n.className = "k2-anotiz";
    n.textContent = text;
    return n;
  }
  // Fields the open set's family rules out (weather and season indoors).
  const gesperrtJetzt = (state) => (daten.nurDraussen ? ortGesperrt(daten, state) : new Set());

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
      offen = null;
      wahlSuche = "";
      const w = { ...(state.wuerfeln || {}) };
      if (an) delete w[cat];
      else w[cat] = true;
      schreib({ ...state, wuerfeln: w });
    };
    return b;
  }

  // Name and short value of a row as the compact view's lines show them.
  // gesetzt: set or rolled.
  function kurzfassung(state, cat) {
    const istText = cat === DETAILS;
    const rollt = !istText && !!state.wuerfeln?.[cat];
    const req = bereich === "pose" && cat === "arme" && !rollt ? (state.requisit || "").trim() : "";
    const wert = istText ? (state.details || "").trim() : (req || state.felder?.[cat]);
    const gesetzt = istText || !!req ? !!wert : !leer(wert);
    const name = document.createElement("span");
    name.className = "k2-bname";
    name.textContent = istText ? t("Details", "ui") : t(cat, "kategorien");
    const kurz = document.createElement("span");
    const aus = !istText && gesperrtJetzt(state).has(cat);
    kurz.className = "k2-kurz" + (gesetzt || rollt ? "" : " k2-leer") + (aus && (gesetzt || rollt) ? " k2-aus" : "");
    kurz.textContent = rollt ? t("wird gewürfelt", "ui")
      : !gesetzt ? (!istText && !(daten.felder[cat] || []).length ? t("wartet auf Render-Test", "ui")
                                                                    : t("nichts gesetzt", "ui"))
      : istText || req ? wert : beschriftung(cat, wert);
    if (aus && (gesetzt || rollt)) kurz.textContent += " · " + t("nur draußen", "ui");
    kurz.title = kurz.textContent;
    return { name, kurz, gesetzt: gesetzt || rollt };
  }

  function zeile(state, cat) {
    if (cat === DETAILS) {
      const stueck = document.createElement("div");
      stueck.className = "k2-stueck";
      const row = document.createElement("div");
      row.className = "k2-feld";
      const lbl = document.createElement("div");
      lbl.className = "k2-name k2-loeschbar";
      lbl.textContent = t("Details", "ui");
      lbl.title = t("Klicken leert dieses Feld", "ui");
      lbl.onclick = () => {
        offen = null;
        wahlSuche = "";
        schreib({ ...state, details: "" });
      };
      const frei = document.createElement("input");
      frei.className = "k2-frei";
      frei.placeholder = t("Weiteres (englisch)", "ui");
      frei.value = state.details || "";
      // Write only on change, otherwise the canvas is redrawn on every
      // keystroke and the node flickers.
      frei.onchange = () => schreib({ ...state, details: frei.value });
      frei.onkeydown = (ev) => ev.stopPropagation();
      row.append(lbl, frei);
      stueck.append(row);
      // The location: a saved scene (Save Scene node) as this set's text.
      if (mehrere) {
        if (szenen === null) { szenen = []; ladeSzenen(); }
        if (szenen.length) {
          const reihe = document.createElement("div");
          reihe.className = "k2-chips k2-szenen";
          const titel = document.createElement("span");
          titel.className = "k2-anotiz";
          titel.textContent = t("Gespeicherte Szenen:", "ui");
          reihe.append(titel);
          for (const sz of szenen) {
            reihe.append(chip(sz.name, (state.details || "").trim() === sz.text.trim(),
                              () => schreib({ ...state, details: sz.text }), sz.text));
            reihe.lastChild.classList.add("k2-klein");
          }
          stueck.append(reihe);
        }
      }
      return stueck;
    }

    const istOffen = offen === cat;
    const rollt = !!state.wuerfeln?.[cat];
    const req = bereich === "pose" && cat === "arme" && !rollt ? (state.requisit || "").trim() : "";
    const feldWert = state.felder?.[cat] || daten.leer;
    const gesetzt = rollt || !!req || !leer(feldWert);
    const aus = gesperrtJetzt(state).has(cat);

    const stueck = document.createElement("div");
    stueck.className = "k2-stueck";
    const row = document.createElement("div");
    row.className = "k2-feld";

    const lbl = document.createElement("div");
    lbl.className = "k2-name k2-loeschbar";
    lbl.textContent = t(cat, "kategorien");
    lbl.title = t("Klicken setzt dieses Feld zurück", "ui");
    lbl.onclick = () => {
      offen = null;
      wahlSuche = "";
      const w = { ...(state.wuerfeln || {}) };
      delete w[cat];
      const extra = bereich === "pose" && cat === "arme" ? { requisit: "" } : {};
      schreib({ ...state, ...extra, felder: { ...state.felder, [cat]: daten.leer }, wuerfeln: w });
    };

    const k = document.createElement("button");
    k.type = "button";
    k.className = "k2-wahlknopf"
      + (gesetzt ? "" : " k2-leer")
      + (aus && gesetzt ? " k2-ignoriert" : "")
      + (istOffen ? " k2-offen" : "");
    k.dataset.feld = cat;
    k.setAttribute("aria-expanded", String(istOffen));
    const textEl = document.createElement("span");
    textEl.textContent = rollt ? "🎲 " + t("wird gewürfelt", "ui")
      : req ? req
      : !leer(feldWert) ? beschriftung(cat, feldWert)
      : daten.leer;
    k.append(textEl);
    const eintrag = (daten.felder[cat] || []).find((e) => e.label === feldWert);
    const wortWert = eintrag?.wert ?? state.eigene?.[cat]?.[feldWert];
    k.title = aus && gesetzt
      ? t("Nur für Sets draußen – dieses Set ist drinnen (Studio oder Innenraum) und lässt das Feld weg.", "ui")
      : (wortWert || "");

    const istLang = (daten.felder[cat] || []).length > LANGE_LISTE;
    k.onclick = (ev) => {
      ev.stopPropagation();
      offen = istOffen ? null : cat;
      wahlSuche = "";
      zeichne();
      if (offen) {
        (istLang ? root.querySelector(".k2-wahlbox .k2-suche")
          : root.querySelector(".k2-wahlbox .k2-eintrag.k2-an .k2-eintrag-name")
            || root.querySelector(".k2-wahlbox .k2-eintrag-name"))?.focus();
      }
    };

    row.append(lbl, k, wuerfelKnopf(state, cat));
    stueck.append(row);
    if (istOffen) stueck.append(wahlBox(state, cat));
    return stueck;
  }

  // The location: one tab per set - a dot for outdoors (green), indoors
  // (amber) or no family (grey) - and + for a new one.
  function satzReiter(ganz) {
    const reiter = document.createElement("div");
    reiter.className = "k2-reiter";
    ganz.saetze.forEach((satz, i) => {
      const r = document.createElement("button");
      r.type = "button";
      r.className = "k2-reiter-tab" + (i === ganz.aktiv ? " k2-an" : "");
      const punkt = document.createElement("b");
      punkt.className = "k2-mini";
      const d = ortDraussen(daten, satz);
      punkt.style.background = d === true ? "#6fae6a" : d === false ? "#c9a25a" : "transparent";
      punkt.title = d === true ? t("draußen", "ui") : d === false ? t("drinnen", "ui") : t("ohne Familie", "ui");
      r.append(punkt, ortName(daten, satz, i));
      r.onclick = () => { if (i !== ganz.aktiv) schreibGanz({ ...ganz, aktiv: i }); };
      reiter.append(r);
    });
    const neu = document.createElement("button");
    neu.type = "button";
    neu.className = "k2-reiter-tab k2-reiter-neu";
    neu.textContent = "+";
    neu.title = t("Neues Set", "ui");
    neu.onclick = () => schreibGanz({ ...ganz, aktiv: ganz.saetze.length,
      saetze: [...ganz.saetze, { ...structuredClone(vorgabe.saetze[0]), id: neueId() }] });
    reiter.append(neu);
    return reiter;
  }

  // The open set's name (what the Series and its contact sheet call it),
  // duplicate, and delete - never the last set, and only on a second click.
  function satzZeile(ganz) {
    const satz = ganz.saetze[ganz.aktiv];
    const zeile = document.createElement("div");
    zeile.className = "k2-feld k2-outfitname";
    const lbl = document.createElement("div");
    lbl.className = "k2-name";
    lbl.textContent = t("Name", "ui");
    const inp = document.createElement("input");
    inp.placeholder = ortName(daten, { ...satz, name: "" }, ganz.aktiv);
    inp.value = satz.name || "";
    inp.onchange = () => {
      const g = liesGanz();
      g.saetze[g.aktiv] = { ...g.saetze[g.aktiv], name: inp.value.trim() };
      schreibGanz(g);
    };
    inp.onkeydown = (ev) => ev.stopPropagation();
    const kopie = document.createElement("button");
    kopie.type = "button";
    kopie.className = "k2-textknopf";
    kopie.textContent = "⧉";
    kopie.title = t("Set duplizieren", "ui");
    kopie.onclick = () => {
      const saetze = [...ganz.saetze];
      saetze.splice(ganz.aktiv + 1, 0, { ...structuredClone(satz), id: neueId(),
                                         name: satz.name ? satz.name + " 2" : "" });
      schreibGanz({ ...ganz, saetze, aktiv: ganz.aktiv + 1 });
    };
    zeile.append(lbl, inp);
    if (ganz.saetze.length > 1) {
      const verschiebe = (dir) => {
        const j = ganz.aktiv + dir;
        if (j < 0 || j >= ganz.saetze.length) return;
        const saetze = [...ganz.saetze];
        [saetze[ganz.aktiv], saetze[j]] = [saetze[j], saetze[ganz.aktiv]];
        schreibGanz({ ...ganz, saetze, aktiv: j });
      };
      const links = document.createElement("button");
      links.type = "button";
      links.className = "k2-textknopf";
      links.textContent = "‹";
      links.disabled = ganz.aktiv === 0;
      links.title = t("Nach links verschieben", "ui");
      links.onclick = () => verschiebe(-1);
      const rechts = document.createElement("button");
      rechts.type = "button";
      rechts.className = "k2-textknopf";
      rechts.textContent = "›";
      rechts.disabled = ganz.aktiv === ganz.saetze.length - 1;
      rechts.title = t("Nach rechts verschieben", "ui");
      rechts.onclick = () => verschiebe(1);
      zeile.append(links, rechts);
    }
    zeile.append(kopie);
    if (ganz.saetze.length > 1) {
      const weg = document.createElement("button");
      weg.type = "button";
      weg.className = "k2-textknopf" + (frageSatz ? " k2-frage" : "");
      weg.textContent = frageSatz ? t("löschen?", "ui") : "×";
      weg.title = frageSatz ? t("Nochmal klicken bestätigt", "ui") : t("Set löschen", "ui");
      weg.onclick = () => {
        if (!frageSatz) { frageSatz = true; zeichne(); return; }
        schreibGanz({ ...ganz, saetze: ganz.saetze.filter((_, i) => i !== ganz.aktiv),
                      aktiv: Math.max(0, ganz.aktiv - 1) });
      };
      zeile.append(weg);
    }
    return zeile;
  }

  function zeichne() {
    folge.gezeichnet();
    const state = lies();
    const ganz = mehrere ? liesGanz() : null;
    root.textContent = "";
    if (!ziel) versteckeSeed();
    const gesetzt = daten.reihenfolge.filter((c) => !leer(state.felder?.[c]) || state.wuerfeln?.[c] ||
      (bereich === "pose" && c === "arme" && (state.requisit || "").trim())).length
      + ((state.details || "").trim() ? 1 : 0);
    const hinweis = eigeneHinweis();

    // --- compact: slim layout without the duplicate brand strip; a click on
    // the summary rows or on "edit" opens the Studio sidebar. --------------
    const kompakt = !ziel && istKompakt(node);
    root.classList.toggle("k2-kompakt", kompakt);
    if (kompakt) {
      const block = document.createElement("div");
      block.className = "k2-kompakt-inhalt";
      const aktionen = document.createElement("div");
      aktionen.className = "k2-kompakt-aktionen";
      aktionen.append(bearbeitenKnopf(node), ansichtKnopf(node));
      const zeilen = document.createElement("div");
      zeilen.className = "k2-kompakt-zeilen k2-panelzeilen";
      for (const cat of [...daten.reihenfolge, DETAILS]) {
        const k = kurzfassung(state, cat);
        if (!k.gesetzt) continue;
        const z = document.createElement("div");
        z.className = "k2-kopf";
        z.append(k.name, k.kurz);
        zeilen.append(z);
      }
      if (!zeilen.childElementCount) {
        const z = document.createElement("div");
        z.className = "k2-kopf";
        z.append(kurzfassung(state, daten.reihenfolge[0]).kurz);
        zeilen.append(z);
      }
      if (ganz) {
        const kopf = document.createElement("div");
        kopf.className = "k2-kompakt-kopf";
        const reiter = satzReiter(ganz);
        reiter.style.margin = "0";
        kopf.append(reiter, aktionen);
        block.append(kopf);
        if (hinweis) block.append(hinweis);
        block.append(alsBearbeiten(zeilen, node));
      } else {
        if (hinweis) block.append(hinweis);
        block.append(alsBearbeiten(zeilen, node));
        const knoepfe = document.createElement("div");
        knoepfe.className = "k2-kompakt-knoepfe";
        knoepfe.append(aktionen);
        block.append(knoepfe);
      }
      root.append(block);
      passeKompaktAn(node, root);
      return;
    }

    const marke = markenleiste(teil,
      ganz ? (ganz.saetze.length === 1 ? t("1 Set", "ui") : tf("{0} Sets", "ui", ganz.saetze.length))
        : gesetzt ? tf("{0} gesetzt", "ui", gesetzt) : t("nichts gesetzt", "ui"), ziel ? null : node);
    root.append(marke);
    if (hinweis) root.append(hinweis);
    const bausteinArt = bereich === "lighting" ? "licht" : bereich === "style" ? "stil" : null;
    if (bausteinArt) {
      root.append(bausteinZeile({
        key: node,
        art: bausteinArt,
        zeichne,
        leseAktuell: async () => {
          const st = lies();
          let txt = baueVorschau(daten, st, bereich, gesperrtJetzt(st));
          if (Object.keys(st.wuerfeln || {}).length) {
            try {
              const r = await fetch("/krea2/vorschau", {
                method: "POST", headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ bereich, seed: Number(seedWidget()?.value ?? 0), state: st }),
              });
              if (r.ok) txt = (await r.json()).prompt || txt;
            } catch (e) { /* keep client preview */ }
          }
          return { text: txt, state: st };
        },
        wendeAn: (eintrag) => {
          if (eintrag.state && typeof eintrag.state === "object") {
            schreib({ ...vorgabe, ...eintrag.state });
          } else {
            schreib({ ...vorgabe, details: eintrag.text || "" });
          }
        },
      }));
    }
    if (ganz) root.append(satzReiter(ganz), satzZeile(ganz));

    const liste = document.createElement("div");
    liste.className = "k2-panel-felder k2-panelzeilen";
    for (const cat of daten.reihenfolge) liste.append(zeile(state, cat));
    liste.append(zeile(state, DETAILS));
    root.append(liste);

    // --- the die's seed, only while something is rolled ---------------------
    const hatWuerfel = Object.keys(state.wuerfeln || {}).length > 0;
    const seedWert = Math.max(0, parseInt(seedWidget()?.value ?? 0, 10) || 0);
    if (hatWuerfel && seedWidget()) {
      const sw = seedWidget(), cw = steuerWidget();
      const reihe = document.createElement("div");
      reihe.className = "k2-schnell k2-seedzeile";
      reihe.append("🎲 " + t("Seed", "ui"));
      const feld = document.createElement("input");
      feld.type = "number";
      feld.min = "0";
      feld.value = String(seedWert);
      feld.onchange = () => { if (sw) sw.value = Math.max(0, parseInt(feld.value, 10) || 0); zeichne(); };
      const neuSeed = document.createElement("button");
      neuSeed.type = "button";
      neuSeed.className = "k2-textknopf";
      neuSeed.textContent = "↻ " + t("Neu würfeln", "ui");
      neuSeed.title = t("Neuen zufälligen Seed würfeln", "ui");
      neuSeed.onclick = () => {
        if (sw) sw.value = Math.floor(Math.random() * 1000000);
        zeichne();
      };
      reihe.append(feld, neuSeed);
      const fest = (cw?.value || "fixed") === "fixed";
      for (const [wert, text] of [["fixed", t("fest", "ui")], ["randomize", t("neu je Lauf", "ui")]]) {
        reihe.append(chip(text, fest === (wert === "fixed"), () => { if (cw) cw.value = wert; zeichne(); }));
        reihe.lastChild.classList.add("k2-klein");
      }
      root.append(reihe);
    }

    // --- live preview ---------------------------------------------------------
    const v = document.createElement("div");
    const text = baueVorschau(daten, state, bereich, gesperrtJetzt(state));
    v.className = "k2-vorschau" + (text ? "" : " k2-leer");
    v.textContent = text || t("nichts gewählt", "ui");
    if (hatWuerfel) {
      const key = JSON.stringify({ bereich, seed: seedWert, state });
      if (wuerfelStand.key !== key) {
        wuerfelStand = { key, text: "", laedt: true };
        fetch("/krea2/vorschau", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: key,
        }).then((r) => (r.ok ? r.json() : null)).then((a) => {
          if (wuerfelStand.key !== key) return;
          wuerfelStand = { key, text: a?.prompt || "", laedt: false };
          zeichne();
        }).catch(() => {
          if (wuerfelStand.key === key) wuerfelStand.laedt = false;
        });
      }
      if (wuerfelStand.text) {
        const aufgeloest = document.createElement("div");
        aufgeloest.className = "k2-wuerfel-vorschau";
        aufgeloest.textContent = "🎲 → " + wuerfelStand.text;
        v.append(aufgeloest);
      }
    } else {
      wuerfelStand = { key: null, text: "", laedt: false };
    }
    root.append(v);

    // The node follows its content: small while everything is closed, taller
    // while a row is open.
    if (!ziel) requestAnimationFrame(passeHoeheAn);
  }

  const CHROM = 52; // title bar and the output row
  // A panel off screen is not laid out (its height reads 0): it is sized
  // once it shows, rather than shrunk to nothing.
  let wartet = false;
  if (!ziel && typeof ResizeObserver === "function") {
    const beobachter = new ResizeObserver(() => {
      if (wartet && root.scrollHeight && !istKompakt(node)) passeHoeheAn();
    });
    beobachter.observe(root);
    beimEntfernen(node, () => beobachter.disconnect());
  }
  function passeHoeheAn() {
    wartet = !root.scrollHeight;
    if (wartet || istKompakt(node)) return;
    const h = Math.ceil(root.scrollHeight) + CHROM;
    if (Math.abs((node.size?.[1] || 0) - h) > 2) {
      node.setSize?.([node.size?.[0] || opts.breite, h]);
      node.graph?.setDirtyCanvas?.(true, true);
    }
  }

  // A click anywhere else closes an open floating list.
  const woanders = (ev) => {
    if (!offen) return;
    if (ev.target.closest?.(".k2-wahlbox, .k2-wahlknopf") && root.contains(ev.target)) return;
    offen = null;
    wahlSuche = "";
    zeichne();
  };
  document.addEventListener("pointerdown", woanders);

  // The other view of this node (canvas or sidebar) draws again after a write
  // here, and this one after a write there (shared.mjs, ansicht()).
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
  // Has a compact view; the height follows the content in both.
  node._k2Kompakt = { vollHoehe: null };

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
  const { classType, hiddenName, prop, vorgabe, datenSchluessel, breite, teil, mehrere } = cfg;

  registriereStateInjektion(classType, hiddenName, prop, vorgabe);

  // The Studio sidebar (studio.mjs) draws this panel for a node into its own
  // column: the same function on the same state.
  registriereBauer(classType, async (node, ziel) => {
    const presets = await ladePresets();
    if (!presets?.[datenSchluessel]) return null;
    return baueNode(node, { daten: presets[datenSchluessel], prop, vorgabe, breite, teil,
                            bereich: datenSchluessel, ziel, mehrere });
  });

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
      // The panel sets the height to its content; the width only for a new
      // node - a loaded one keeps its saved width.
      const bauen = (presets) => {
        // A new node starts compact; a loaded one keeps what it was saved
        // with, full when it has no view property (saved before there was one).
        if (!node._k2Geladen) {
          node.size = [breite, 240];
          node.properties = node.properties || {};
          node.properties[PROP_ANSICHT] ??= "kompakt";
        }
        baueNode(node, { daten: presets[datenSchluessel], prop, vorgabe, breite, teil,
                         bereich: datenSchluessel, mehrere });
      };
      const presets = await ladePresets();
      if (presets?.[datenSchluessel]) bauen(presets);
      else presetFehler(node, bauen);
    },
  });
}

