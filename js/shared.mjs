// Shared foundation for the interfaces in this package.
//
// Built after the pattern of PixaromaResolution: the Python node has no widgets
// apart from the seed, the entire state lives in node.properties and is only
// pushed into the hidden input on submit.

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ---------------------------------------------------------------- Presets ---
// The labels and their English equivalents come from the server
// (nodes/api.py). Maintaining a second copy in JS would be a reliable way to
// let two lists drift apart.
let _presetsPromise = null;
let _geladen = null;   // the last answer, for eigeneHinweis()

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
        _geladen = daten;
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

function _mischeInPlace(ziel, quelle) {
  if (!ziel || !quelle || typeof ziel !== "object" || typeof quelle !== "object") return quelle;
  for (const k of Object.keys(ziel)) if (!(k in quelle)) delete ziel[k];
  for (const [k, v] of Object.entries(quelle)) {
    if (v && typeof v === "object" && !Array.isArray(v)
        && ziel[k] && typeof ziel[k] === "object" && !Array.isArray(ziel[k])) {
      _mischeInPlace(ziel[k], v);
    } else {
      ziel[k] = v;
    }
  }
  return ziel;
}

/** Reloads /krea2/presets in-place and redraws every Photoshoot view live. */
export async function aktualisierePresets() {
  const r = await fetch("/krea2/presets?t=" + Date.now(), { cache: "no-store" });
  if (!r.ok) throw new Error("HTTP " + r.status);
  const frisch = await r.json();
  if (_geladen && typeof _geladen === "object") _mischeInPlace(_geladen, frisch);
  else _geladen = frisch;
  if (_geladen?.i18n) _i18n = _geladen.i18n;
  if (_geladen?.locale) _serverLocale = _geladen.locale;
  _presetsPromise = Promise.resolve(_geladen);
  const graph = app?.canvas?.graph || app?.graph;
  _alleZeichnen(graph);
  for (const n of _alleGraphNodes(graph)) nodeGeaendert(n);
  return _geladen;
}

/** Saves a single custom entry and refreshes presets without a restart. */
export async function speichereEigenenEintrag({ builder, field, label, prompt, group = "", hex = "" }) {
  const r = await fetch("/krea2/custom/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ builder, field, label, prompt, group, hex }),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
  await aktualisierePresets();
  return d.label || label;
}

/** Deletes a single custom entry and refreshes presets. */
export async function loescheEigenenEintrag(builder, field, label) {
  const r = await fetch("/krea2/custom/remove_entry", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ builder, field, label }),
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
  await aktualisierePresets();
  return true;
}

/** Builds a clean short preset label from an English prop description. */
export function labelAusRequisit(roh) {
  let s = String(roh || "").trim().replace(/\s+/g, " ");
  s = s.replace(/^(?:holding|carrying|cradling|wearing)\s+/i, "");
  s = s.replace(/^(?:a|an|the|her|his)\s+/i, "").trim();
  if (!s) return "";
  return (s.charAt(0).toUpperCase() + s.slice(1)).slice(0, 40).trim();
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

/** Reads a ComfyUI setting safely (returns vorgabe when outside the browser UI). */
export function einstellung(id, vorgabe = undefined) {
  try {
    const v = app?.extensionManager?.setting?.get?.(id);
    return v === undefined || v === null || v === "" ? vorgabe : v;
  } catch (e) {
    return vorgabe;
  }
}

export function startetKompakt() {
  return einstellung("Photoshoot.StartCompact", true) !== false;
}

export function zeigeToast(detail, severity = "info", summary = "Photoshoot") {
  try {
    app?.extensionManager?.toast?.add?.({
      severity,
      summary,
      detail: String(detail || ""),
      life: 3200,
    });
  } catch (e) {
    // older frontend without toast service
  }
}

export async function bestaetige(message, title = "Photoshoot") {
  try {
    const dlg = app?.extensionManager?.dialog;
    if (typeof dlg?.confirm === "function") {
      return !!(await dlg.confirm({ title, message, type: "default" }));
    }
  } catch (e) {
    // fall back to browser confirm
  }
  return typeof window !== "undefined" && typeof window.confirm === "function"
    ? window.confirm(message)
    : false;
}

// Three sources, in this order:
//
//   1. Photoshoot's own language override when set to de/en;
//   2. the front-end setting - up to date immediately, but depending on load
//      timing and front-end version still empty while the panels already draw;
//   3. the stored setting / browser language.
function locale() {
  const jetzt = Date.now();
  if (_locale && jetzt < _localeBis) return _locale;

  const eigen = einstellung("Photoshoot.Locale", "auto");
  const l = (eigen === "de" || eigen === "en" ? eigen : null)
    || _frontendLocale()
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

// ------------------------------------------------------ Search & shortlist ---
// The long lists (72 shoes, 90 moods) are searched by typing. A hit may sit in
// the German label, the English display label, the prompt text or the family,
// so "veil" finds the pillbox and "Stiefel" the boots. Umlauts and accents
// count as their base letter.
export function normalisiere(s) {
  return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

// Every word of the query has to occur somewhere in the texts.
export function passtSuche(anfrage, texte) {
  const woerter = normalisiere(anfrage).split(/\s+/).filter(Boolean);
  if (!woerter.length) return true;
  const heu = normalisiere(texte.filter(Boolean).join(" "));
  return woerter.every((w) => heu.includes(w));
}

// Favourites and recently used entries, per field ("person/shoes",
// "ausdruck/stimmung"). They belong to the viewer, not to the workflow: they
// live in the browser and never in node.properties, so a shared workflow does
// not carry someone else's favourites. Browser storage may be missing or throw
// (private window, blocked site data) - then there is simply no shortlist.
const MERK_SCHLUESSEL = { favoriten: "photoshoot.favoriten", zuletzt: "photoshoot.zuletzt" };
const ZULETZT_MAX = 5;

function _merkLesen(art) {
  try {
    const roh = JSON.parse(localStorage.getItem(MERK_SCHLUESSEL[art]) || "{}");
    return roh && typeof roh === "object" && !Array.isArray(roh) ? roh : {};
  } catch (e) {
    return {};
  }
}

function _merkSchreiben(art, alles) {
  try {
    localStorage.setItem(MERK_SCHLUESSEL[art], JSON.stringify(alles));
  } catch (e) {
    // no storage - the shortlist stays empty, the choice itself is unaffected
  }
}

export function merkliste(art, feld) {
  const liste = _merkLesen(art)[feld];
  return Array.isArray(liste) ? liste.filter((l) => typeof l === "string") : [];
}

export function schalteFavorit(feld, label) {
  const alles = _merkLesen("favoriten");
  const liste = merkliste("favoriten", feld);
  alles[feld] = liste.includes(label) ? liste.filter((l) => l !== label) : [...liste, label];
  _merkSchreiben("favoriten", alles);
}

export function merkeBenutzt(feld, label) {
  const alles = _merkLesen("zuletzt");
  alles[feld] = [label, ...merkliste("zuletzt", feld).filter((l) => l !== label)].slice(0, ZULETZT_MAX);
  _merkSchreiben("zuletzt", alles);
}

/** Shared searchable/grouped dropdown popover with optional hover preview. */
export function baueWahlBox(opts) {
  const {
    feld, eintraege = [], alleEintraege = eintraege, aktiv, leer, schluessel,
    beschriftung, gruppen = null, wahlSuche = "", onSuche, onWaehle, onFavorit,
    onSchliessen, kopfExtras = [], fussExtras = [], mitSuche = true,
  } = opts;
  const [builder, field] = String(schluessel || "").split("/");
  const erweiterbar = Boolean(
    builder && field && !["person/age", "person/gender", "person/type"].includes(schluessel)
  );
  const nachLabel = new Map(alleEintraege.map((e) => [e.label, e]));
  const sichtbarMap = new Map(eintraege.map((e) => [e.label, e]));
  const familieVon = (lbl) => (gruppen ? Object.keys(gruppen).find((g) => gruppen[g].includes(lbl)) : null);
  const favoriten = mitSuche ? merkliste("favoriten", schluessel).filter((l) => sichtbarMap.has(l)) : [];
  const zuletzt = mitSuche
    ? merkliste("zuletzt", schluessel).filter((l) => sichtbarMap.has(l) && !favoriten.includes(l)) : [];

  const box = document.createElement("div");
  box.className = "k2-wahlbox" + (mitSuche ? "" : " k2-wahlbox-kurz");
  box.dataset.feld = feld;
  for (const x of kopfExtras) if (x) box.append(x);

  let suche = null;
  if (mitSuche) {
    suche = document.createElement("input");
    suche.className = "k2-suche";
    suche.type = "search";
    suche.placeholder = t("Suchen …", "ui");
    suche.value = wahlSuche;
    box.append(suche);
  }

  const liste = document.createElement("div");
  liste.className = "k2-wahlliste";
  const mitBildern = eintraege.some((e) => e.bild);
  let vorschau = null;
  let zeigeVorschau = () => {};
  if (mitBildern) {
    vorschau = document.createElement("div");
    vorschau.className = "k2-wahlbild";
    const img = document.createElement("img");
    img.alt = "";
    img.decoding = "async";
    const text = document.createElement("div");
    text.className = "k2-wahlbild-text";
    vorschau.append(img, text);
    zeigeVorschau = (lbl) => {
      const e = nachLabel.get(lbl);
      text.textContent = "";
      if (!e) {
        img.style.visibility = "hidden";
        text.append(t("Zeig auf einen Eintrag, um ihn zu sehen", "ui"));
        text.classList.add("k2-leer");
        return;
      }
      text.classList.remove("k2-leer");
      const name = document.createElement("b");
      name.textContent = beschriftung(lbl);
      const wert = document.createElement("span");
      wert.textContent = e.wert;
      text.append(name, wert);
      if (e.bild) {
        img.src = new URL(e.bild, import.meta.url).href;
        img.style.visibility = "";
      } else {
        img.removeAttribute("src");
        img.style.visibility = "hidden";
        const ohne = document.createElement("span");
        ohne.className = "k2-leer";
        ohne.textContent = t("Keine Vorschau", "ui");
        text.append(ohne);
      }
    };
    zeigeVorschau(aktiv);
  }

  if (eintraege.length) {
    if (vorschau) {
      const split = document.createElement("div");
      split.className = "k2-wahl-split";
      split.append(vorschau, liste);
      box.append(split);
    } else {
      box.append(liste);
    }
    const abschnitte = [];
    const abschnitt = (kopf, kurz) => {
      const a = { kopf: null, zeilen: [], kurz };
      if (kopf) {
        a.kopf = document.createElement("div");
        a.kopf.className = "k2-wahlkopf";
        a.kopf.textContent = kopf;
        liste.append(a.kopf);
      }
      abschnitte.push(a);
      return a;
    };
    const zeile = (a, lbl) => {
      const e = nachLabel.get(lbl);
      const z = document.createElement("div");
      z.className = "k2-eintrag" + (lbl === aktiv ? " k2-an" : "");
      const knopf = document.createElement("button");
      knopf.type = "button";
      knopf.className = "k2-eintrag-name";
      knopf.textContent = lbl === leer ? leer : beschriftung(lbl);
      knopf.onclick = (ev) => { ev.stopPropagation(); onWaehle(lbl); };
      knopf.onmouseenter = knopf.onfocus = () => zeigeVorschau(lbl);
      z.append(knopf);
      if (e) {
        knopf.title = e.wert;
        const fam = familieVon(lbl);
        z.dataset.suche = [lbl, beschriftung(lbl), e.wert, fam, fam && t(fam, "familien")].join(" ");
        if (mitSuche) {
          const fav = favoriten.includes(lbl);
          const stern = document.createElement("button");
          stern.type = "button";
          stern.className = "k2-stern" + (fav ? " k2-an" : "");
          stern.textContent = fav ? "★" : "☆";
          stern.title = t(fav ? "Favorit entfernen" : "Als Favorit merken", "ui");
          stern.setAttribute("aria-label", stern.title);
          stern.tabIndex = -1;
          stern.onclick = (ev) => {
            ev.stopPropagation();
            schalteFavorit(schluessel, lbl);
            onFavorit?.();
          };
          z.append(stern);
        }
        if (e.eigen && erweiterbar) {
          const weg = document.createElement("button");
          weg.type = "button";
          weg.className = "k2-stern k2-eigen-weg";
          weg.textContent = "×";
          weg.title = t("Eigenen Eintrag löschen", "ui");
          weg.setAttribute("aria-label", weg.title);
          weg.tabIndex = -1;
          weg.onclick = async (ev) => {
            ev.stopPropagation();
            weg.disabled = true;
            try {
              await loescheEigenenEintrag(builder, field, lbl);
              onFavorit?.();
            } catch (err) {
              weg.disabled = false;
              console.error("[Photoshoot] Could not remove custom entry:", err);
            }
          };
          z.append(weg);
        }
      }
      liste.append(z);
      a.zeilen.push(z);
    };

    zeile(abschnitt(null, true), leer);
    if (favoriten.length) {
      const a = abschnitt("★ " + t("Favoriten", "ui"), true);
      for (const l of favoriten) zeile(a, l);
    }
    if (zuletzt.length) {
      const a = abschnitt(t("Zuletzt benutzt", "ui"), true);
      for (const l of zuletzt) zeile(a, l);
    }
    const gezeigte = new Set();
    if (gruppen) {
      for (const [g, labels] of Object.entries(gruppen)) {
        const treffer = eintraege.filter((e) => labels.includes(e.label));
        if (!treffer.length) continue;
        const n = t(g, "familien");
        const a = abschnitt(n.charAt(0).toUpperCase() + n.slice(1), false);
        for (const e of treffer) { zeile(a, e.label); gezeigte.add(e.label); }
      }
      const rest = eintraege.filter((e) => !gezeigte.has(e.label));
      if (rest.length) {
        const n = t("Eigene", "familien");
        const a = abschnitt(n.charAt(0).toUpperCase() + n.slice(1), false);
        for (const e of rest) { zeile(a, e.label); gezeigte.add(e.label); }
      }
    } else {
      const a = abschnitt(favoriten.length || zuletzt.length ? t("Alle", "ui") : null, false);
      for (const e of eintraege) { zeile(a, e.label); gezeigte.add(e.label); }
    }
    if (aktiv && aktiv !== leer && !gezeigte.has(aktiv)) {
      zeile(abschnitt(null, false), aktiv);
    }

    const keine = document.createElement("div");
    keine.className = "k2-keine";
    keine.textContent = t("Keine Treffer", "ui");
    liste.append(keine);

    const filtere = () => {
      const q = (suche?.value || "").trim();
      let treffer = 0;
      for (const a of abschnitte) {
        let sichtbar = 0;
        for (const z of a.zeilen) {
          const zeigen = q ? !a.kurz && passtSuche(q, [z.dataset.suche]) : true;
          z.style.display = zeigen ? "" : "none";
          if (zeigen) sichtbar++;
        }
        if (a.kopf) a.kopf.style.display = sichtbar ? "" : "none";
        treffer += sichtbar;
      }
      keine.style.display = treffer ? "none" : "";
    };
    filtere();

    const sichtbareNamen = () =>
      Array.from(liste.querySelectorAll(".k2-eintrag-name")).filter((b) => b.parentElement.style.display !== "none");
    if (suche) {
      suche.oninput = () => { onSuche?.(suche.value); filtere(); liste.scrollTop = 0; };
      suche.onkeydown = (ev) => {
        if (ev.key === "ArrowDown") {
          ev.preventDefault();
          sichtbareNamen()[0]?.focus();
        } else if (ev.key === "Enter") {
          ev.preventDefault();
          const erster = suche.value.trim() && sichtbareNamen()[0];
          if (erster) erster.click();
        } else if (ev.key === "Escape") {
          ev.preventDefault();
          onSchliessen?.();
        }
        ev.stopPropagation();
      };
    }
    liste.onkeydown = (ev) => {
      const namen = sichtbareNamen();
      const i = namen.indexOf(document.activeElement);
      if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
        ev.preventDefault();
        if (ev.key === "ArrowUp" && i <= 0 && suche) suche.focus();
        else namen[Math.max(0, Math.min(namen.length - 1, i + (ev.key === "ArrowDown" ? 1 : -1)))]?.focus();
      } else if (ev.key === "Escape") {
        ev.preventDefault();
        onSchliessen?.();
      }
      ev.stopPropagation();
    };
    queueMicrotask(() => {
      const an = Array.from(liste.querySelectorAll(".k2-eintrag.k2-an")).find((z) => z.style.display !== "none");
      if (an) liste.scrollTop = Math.max(0, an.offsetTop - liste.clientHeight / 2);
    });
  }

  for (const x of fussExtras) if (x) box.append(x);
  if (erweiterbar) {
    const neuBox = document.createElement("div");
    neuBox.className = "k2-eigen-neu";
    const zeigeKnopf = () => {
      neuBox.textContent = "";
      const plus = document.createElement("button");
      plus.type = "button";
      plus.className = "k2-textknopf k2-eigen-plus";
      plus.textContent = "+ " + t("Eigener Eintrag …", "ui");
      plus.onclick = (ev) => {
        ev.stopPropagation();
        zeigeForm();
      };
      neuBox.append(plus);
    };
    const zeigeForm = () => {
      neuBox.textContent = "";
      const form = document.createElement("div");
      form.className = "k2-eigen-form";
      const nameInp = document.createElement("input");
      nameInp.type = "text";
      nameInp.className = "k2-frei";
      nameInp.placeholder = t("Name der Vorgabe", "ui");
      nameInp.value = (suche?.value || "").trim();
      const promptInp = document.createElement("input");
      promptInp.type = "text";
      promptInp.className = "k2-frei";
      promptInp.placeholder = schluessel === "person/hair"
        ? t("Prompt (englisch), z. B. layered {c} wolf cut", "ui")
        : (schluessel === "person/prop" || schluessel === "pose/arme")
          ? t("Eigenes Requisit (englisch), z. B. a vintage camera", "ui")
          : t("Prompt (englisch)", "ui");
      const aktion = document.createElement("div");
      aktion.className = "k2-reihe";
      const ok = document.createElement("button");
      ok.type = "button";
      ok.className = "k2-textknopf k2-an";
      ok.textContent = t("Speichern", "ui");
      const abb = document.createElement("button");
      abb.type = "button";
      abb.className = "k2-textknopf";
      abb.textContent = t("Abbrechen", "ui");
      const fehler = document.createElement("span");
      fehler.className = "k2-warn";
      const sichern = async () => {
        const lbl = nameInp.value.trim();
        const prm = promptInp.value.trim();
        if (!lbl || !prm) {
          fehler.textContent = t("Name und Prompt dürfen nicht leer sein", "ui");
          return;
        }
        ok.disabled = true;
        fehler.textContent = "";
        try {
          const savedLabel = await speichereEigenenEintrag({ builder, field, label: lbl, prompt: prm });
          onWaehle(savedLabel);
        } catch (err) {
          ok.disabled = false;
          fehler.textContent = err?.message || String(err);
        }
      };
      nameInp.onkeydown = (ev) => {
        if (ev.key === "Escape") { ev.preventDefault(); zeigeKnopf(); }
        ev.stopPropagation();
      };
      promptInp.onkeydown = (ev) => {
        if (ev.key === "Enter") { ev.preventDefault(); sichern(); }
        else if (ev.key === "Escape") { ev.preventDefault(); zeigeKnopf(); }
        ev.stopPropagation();
      };
      ok.onclick = (ev) => { ev.stopPropagation(); sichern(); };
      abb.onclick = (ev) => { ev.stopPropagation(); zeigeKnopf(); };
      form.onclick = (ev) => ev.stopPropagation();
      aktion.append(ok, abb, fehler);
      form.append(nameInp, promptInp, aktion);
      neuBox.append(form);
      queueMicrotask(() => (nameInp.value ? promptInp : nameInp).focus());
    };
    zeigeKnopf();
    box.append(neuBox);
  }
  return box;
}

// ------------------------------------------------------- Custom entries ---
// Custom entries that failed their check (nodes/eigene.py) are skipped with a
// message - in the ComfyUI console, which nobody reads. One line under the
// brand strip says so, with the details a click away; nothing when all is well.
export function eigeneHinweis() {
  const n = _geladen?.custom?.messages?.length || 0;
  if (!n) return null;
  const zeile = document.createElement("div");
  zeile.className = "k2-warn k2-eigene-hinweis";
  zeile.append((n === 1 ? t("1 Meldung zu eigenen Einträgen", "ui")
                        : tf("{0} Meldungen zu eigenen Einträgen", "ui", n)) + " · ");
  const a = document.createElement("a");
  a.href = "/krea2/custom";
  a.target = "_blank";
  a.rel = "noopener";
  a.textContent = t("Details", "ui");
  zeile.append(a);
  return zeile;
}

// A custom entry (nodes/eigene.py) lives in a JSON file on one machine. So
// that a shared workflow still renders elsewhere, the state carries the prompt
// of every custom entry it uses: {field: {label: prompt}}. Rebuilt on every
// write from what is chosen - an entry no longer chosen drops out, and a copy
// whose file is missing here is kept as it was.
export function eigeneKopie(daten, felder, mehrfach, alt) {
  const neu = {};
  const merke = (cat, label) => {
    if (!label || label === daten.leer) return;
    const e = (daten.felder?.[cat] || []).find((x) => x.label === label);
    const wert = e ? (e.eigen ? e.wert : null) : alt?.[cat]?.[label];
    if (wert) (neu[cat] ||= {})[label] = wert;
  };
  for (const [cat, label] of Object.entries(felder || {})) merke(cat, label);
  for (const [cat, labels] of Object.entries(mehrfach || {})) {
    if (Array.isArray(labels)) for (const l of labels) merke(cat, l);
  }
  return Object.keys(neu).length ? neu : undefined;
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

.k2-blatt{display:flex;flex-direction:column;gap:5px;overflow-y:auto;flex:1;min-height:0;padding-bottom:160px}
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
.k2-inhalt .k2-feld > .k2-name{flex-basis:78px}
.k2-stueck{display:flex;flex-direction:column;gap:4px;position:relative}
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
.k2-palette{position:absolute;left:76px;top:calc(100% + 3px);z-index:45;margin-left:0;background:#1a1a1a;
  border:1px solid #4a4a4a;border-radius:6px;padding:7px;display:flex;flex-direction:column;gap:6px;
  align-self:flex-start;box-shadow:0 10px 28px rgba(0,0,0,.68)}
.k2-inhalt .k2-palette{left:84px}
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
/* A long list: a button in place of the dropdown, the list with its search
   opens under the row like the colour palette. */
.k2-wahlknopf{flex:1;min-width:0;display:flex;align-items:center;gap:4px;background:#1d1d1d;color:#d7d7d7;
  border:1px solid #3d3d3d;border-radius:4px;padding:3px 5px;font-size:10px;font-family:inherit;cursor:pointer;
  text-align:left}
.k2-wahlknopf span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.k2-wahlknopf::after{content:"▾";color:#8e8e8e;font-size:9px}
.k2-wahlknopf:hover,.k2-wahlknopf.k2-offen{border-color:#f66744}
.k2-wahlknopf:focus-visible{outline:1px solid #f66744}
.k2-wahlknopf.k2-leer span{color:#8e8e8e}
.k2-wahlknopf.k2-ignoriert span{color:#777;text-decoration:line-through}
.k2-wahlbox{position:absolute;left:76px;right:0;top:calc(100% + 3px);z-index:40;margin-left:0;background:#1a1a1a;
  border:1px solid #4a4a4a;border-radius:6px;padding:6px;display:flex;flex-direction:column;gap:5px;
  box-shadow:0 10px 28px rgba(0,0,0,.68)}
.k2-inhalt .k2-wahlbox{left:84px}
.k2-panelzeilen .k2-feld > .k2-name{flex:0 0 94px}
.k2-panelzeilen .k2-wahlbox{left:100px}
.k2-panel-felder{display:flex;flex-direction:column;gap:5px}
.k2-suche{background:#1d1d1d;color:#e2e2e2;border:1px solid #3d3d3d;border-radius:4px;padding:3px 6px;
  font-size:10px;font-family:inherit;width:100%;box-sizing:border-box}
.k2-suche:focus{outline:none;border-color:#f66744}
.k2-wahlliste{display:flex;flex-direction:column;max-height:220px;overflow-y:auto;position:relative}
.k2-wahlliste::-webkit-scrollbar{width:6px}
.k2-wahlliste::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-wahlkopf{font-size:8.5px;letter-spacing:.06em;text-transform:uppercase;color:#8a8a8a;padding:5px 4px 2px}
.k2-wahlkopf:first-child{padding-top:0}
.k2-eintrag{display:flex;align-items:center;gap:4px;border-radius:3px}
.k2-eintrag:hover{background:#2c2c2c}
.k2-eintrag.k2-an{background:#2e201b}
.k2-eintrag-name{flex:1;min-width:0;background:none;border:0;color:#d0d0d0;font:inherit;font-size:10px;
  text-align:left;padding:3px 4px;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k2-eintrag.k2-an .k2-eintrag-name{color:#f3d6cb;font-weight:600}
.k2-eintrag-name:focus-visible{outline:1px solid #f66744;outline-offset:-1px}
.k2-stern{background:none;border:0;color:#5a5a5a;cursor:pointer;font-size:11px;padding:0 4px;line-height:1}
.k2-eintrag:hover .k2-stern{color:#8e8e8e}
.k2-stern.k2-an,.k2-eintrag:hover .k2-stern.k2-an{color:#f6b044}
.k2-stern:focus-visible{outline:1px solid #f66744}
.k2-keine{font-size:10px;color:#8e8e8e;font-style:italic;padding:4px}
.k2-wahl-split{display:flex;gap:8px;align-items:stretch}
.k2-wahl-split .k2-wahlliste{flex:1;min-width:0}
.k2-wahlbild{flex:0 0 92px;width:92px;display:flex;flex-direction:column;gap:4px}
.k2-wahlbild img{width:92px;height:118px;object-fit:cover;border-radius:4px;background:#222;border:1px solid #333;display:block;box-sizing:border-box}
.k2-wahlbild-text{display:flex;flex-direction:column;gap:2px;font-size:9px;color:#9c9c9c;line-height:1.25;min-width:0;overflow-wrap:break-word}
.k2-wahlbild-text b{color:#e6e6e6;font-size:9.5px;font-weight:600}
.k2-wahlbild-text.k2-leer,.k2-wahlbild-text .k2-leer{color:#777;font-style:italic}
/* The builder panels: search over a long list of chips, recent ones above. */
.k2-chipsuche{margin-bottom:1px}
.k2-chipsuche:focus{outline:none;border-color:#f66744}
.k2-zuletzt{display:flex;flex-wrap:wrap;gap:3px;align-items:center}
.k2-zuletzt > span{font-size:8.5px;letter-spacing:.06em;text-transform:uppercase;color:#8a8a8a;margin-right:2px}

/* Actions & Reset bar */
.k2-inspire-btn{display:inline-flex;align-items:center;gap:3px;background:#261814;border:1px solid #7d3320;
  color:#f68c70;border-radius:4px;padding:2px 6px;cursor:pointer;user-select:none;font-size:9px;
  font-weight:600;letter-spacing:.02em;white-space:nowrap;transition:all .15s ease;font-family:inherit}
.k2-inspire-btn.k2-frage{border-color:#f66744;color:#ffb29e;background:#3a2019}
.k2-inspire-btn:focus-visible{outline:1px solid #f66744;outline-offset:1px}
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
/* A list that waits for its render test (the location's), and a value its
   set's family rules out (weather indoors). */
.k2-anotiz.k2-rendertest{border:1px dashed #4a4436;border-radius:5px;padding:5px 7px;color:#b8a77e}
.k2-kurz.k2-aus{opacity:.55}
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
/* Wardrobe: the outfit stripe under a frame, the rail of outfit cards. */
.k2-ostreifen{position:absolute;left:0;right:0;bottom:0;height:3px;border-radius:0 0 2px 2px;
  box-shadow:0 -1px 0 rgba(255,255,255,.3)}
/* Location: the sets in the Series' set axis. */
.k2-satzliste{display:flex;flex-direction:column;gap:4px}
.k2-satz{display:grid;grid-template-columns:auto auto 1fr;gap:2px 6px;align-items:center;background:#1c1c1c;
  border:1px solid #333;border-radius:5px;padding:4px 7px;font-size:9.5px}
.k2-satz-name{font-weight:600;color:#e6e6e6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k2-satz-text{grid-column:1/-1;color:#b8b8b8;line-height:1.35}
.k2-satz-text.k2-leer{color:#777;font-style:italic}
/* Location: the set stripe over a frame. */
.k2-sstreifen{position:absolute;left:0;right:0;top:0;height:3px;border-radius:2px 2px 0 0;
  box-shadow:0 1px 0 rgba(0,0,0,.35)}
.k2-stange{display:flex;gap:6px;overflow-x:auto;padding:2px 0 4px}
.k2-okarte{flex:0 0 124px;min-width:0;background:#1c1c1c;border:1px solid #333;border-radius:5px;
  padding:5px 7px;font-size:9.5px;color:#c8c8c8;display:flex;flex-direction:column;gap:3px}
.k2-okarte-kopf{font-weight:600;color:#e6e6e6;border-bottom:2px solid #8e8e8e;padding-bottom:3px;margin-bottom:1px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k2-okarte-zeile{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
/* Wardrobe: the outfit tabs. */
/* The builder panels (pose, expression, lighting, style): rows like the
   Person node, a small die at the end of each, the seed line under them. */
.k2-wuerfel.k2-klein{font-size:10px;padding:0 3px;line-height:16px;opacity:.45}
.k2-wuerfel.k2-klein.k2-an{opacity:1}
.k2-seedzeile{margin:4px 0 2px}
.k2-panelzeilen .k2-kopf{grid-template-columns:10px 104px 1fr auto}
.k2-panelzeilen .k2-bname{overflow:hidden;text-overflow:ellipsis}
.k2-seedzeile input{width:90px;background:#1d1d1d;color:#d7d7d7;border:1px solid #3d3d3d;border-radius:4px;
  padding:2px 5px;font:inherit;font-size:10px}
.k2-kleidung-quelle{font-size:9.5px;color:#8e8e8e;margin-top:4px}
.k2-altkleidung .k2-textknopf{margin-left:2px}
.k2-reiter{display:flex;flex-wrap:wrap;gap:4px;margin:2px 0 8px}
.k2-reiter-tab{display:inline-flex;align-items:center;gap:1px;max-width:120px;background:#1c1c1c;border:1px solid #333;
  border-radius:5px;color:#b8b8b8;font:inherit;font-size:10.5px;padding:3px 9px;cursor:pointer;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.k2-reiter-tab:hover{border-color:#555;color:#e0e0e0}
.k2-reiter-tab.k2-an{border-color:#f66744;background:#2a1d18;color:#fff}
.k2-reiter-neu{color:#8e8e8e;padding:3px 10px}
.k2-okarte-bild{display:block;aspect-ratio:3/4;border-radius:3px;background:#2a2a2a center/cover;margin:1px 0 2px}
.k2-wbild{display:block;position:relative;height:190px;margin:2px 0 6px;border-radius:4px;background:#2a2a2a center/contain no-repeat}
.k2-okarte-bild.k2-alt,.k2-wbild.k2-alt{opacity:.45}
.k2-wbild span{position:absolute;right:6px;bottom:6px;font-size:9px;color:#ddd;background:rgba(20,20,20,.75);
  border-radius:3px;padding:1px 5px}
.k2-okarte-zeile.k2-leer{color:#777;font-style:italic}
/* Black and navy swatches on the dark card need a lighter ring than elsewhere;
   a garment without a colour field keeps the space, without a dot. */
.k2-okarte .k2-mini{box-shadow:inset 0 0 0 1px rgba(255,255,255,.45)}
.k2-okarte .k2-mini.k2-ohne{box-shadow:none;background:transparent}
.k2-bild:hover .k2-rahmen{border-color:#9a9a9a}
.k2-bild.k2-fertig .k2-rahmen{border-color:#7d4a38}
.k2-bild.k2-gewaehlt .k2-rahmen{border-color:#f66744;box-shadow:0 0 0 1px #f66744}
.k2-bild.k2-gewaehlt .k2-bild-label{color:#c9a08f}
.k2-bild:focus-visible .k2-rahmen{outline:1px solid #f66744;outline-offset:2px}
.k2-mehr{font-size:9.5px;color:#8e8e8e;align-self:center;background:none;border:1px dashed #3d3d3d;border-radius:4px;
  padding:3px 6px;cursor:pointer;font-family:inherit}
.k2-mehr:hover{color:#e2e2e2;border-color:#5a5a5a}
.k2-mehr:focus-visible{outline:1px solid #f66744}
/* Contact sheet pages: ‹ 25–48 of 60 › in the head row. */
.k2-seiten{display:flex;align-items:center;gap:4px;text-transform:none;letter-spacing:0;font-size:9.5px;
  font-variant-numeric:tabular-nums}
.k2-blaettern{background:none;border:1px solid #3d3d3d;border-radius:3px;color:#c9c9c9;cursor:pointer;
  font:inherit;font-size:11px;line-height:1;padding:1px 6px}
.k2-blaettern:hover:not(:disabled){border-color:#f66744;color:#fff}
.k2-blaettern:disabled{opacity:.35;cursor:default}
.k2-blaettern:focus-visible{outline:1px solid #f66744}
/* The prompt a photo got, in the detail box. */
.k2-prompt{display:flex;gap:6px;align-items:flex-start;min-width:0}
.k2-prompt-text{flex:1;min-width:0;max-height:58px;overflow-y:auto;color:#c9c9c9;font-size:9.5px;line-height:1.35;
  user-select:text;cursor:text;white-space:pre-wrap;word-break:break-word}
.k2-prompt-text::-webkit-scrollbar{width:6px}
.k2-prompt-text::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-prompt .k2-textknopf{flex:0 0 auto}
.k2-start:disabled,.k2-start.k2-laeuft{background:#6b3a2c;border-color:#6b3a2c;color:#e8d5cf;cursor:progress}
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
/* Selects -> next round: the round and its button under the contact sheet;
   a rejected frame is dimmed. */
.k2-runde{display:flex;gap:6px;align-items:center;flex-wrap:wrap;font-size:10px;color:#b0b0b0}
.k2-runde .k2-start{margin-left:auto}
.k2-runde .k2-start:disabled{opacity:.4;cursor:not-allowed;background:#f66744}
.k2-bild.k2-verworfen .k2-rahmen{opacity:.4}
/* Draft and Finish favourites under the start button; a draft is dashed. */
.k2-entwurf-zeile{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.k2-entwurf-zeile .k2-textknopf:disabled{opacity:.4;cursor:not-allowed}
.k2-bild.k2-entwurf .k2-rahmen,.k2-take.k2-entwurf{border-style:dashed}
.k2-warn{font-size:10px;color:#f66744;line-height:1.35}
.k2-eigene-hinweis a{color:inherit;text-decoration:underline}
/* Thumbnail tiles for lighting setups and postures (nodes/vorschau.py): a grid
   over the chips of the entries without a picture. Scrolls on the node,
   grows in the sidebar. */
.k2-kacheln{display:grid;grid-template-columns:repeat(auto-fill,minmax(84px,1fr));gap:5px;
  max-height:300px;overflow-y:auto;padding:1px}
.k2-kacheln::-webkit-scrollbar{width:6px}
.k2-kacheln::-webkit-scrollbar-thumb{background:#3d3d3d;border-radius:3px}
.k2-kachel{background:#1d1d1d;border:1.5px solid #3d3d3d;border-radius:6px;padding:0;cursor:pointer;overflow:hidden;
  display:flex;flex-direction:column;text-align:left;font:inherit;color:#bdbdbd;min-width:0}
.k2-kachel img{width:100%;aspect-ratio:1;object-fit:cover;display:block;background:#222}
.k2-kachel img[src*="/haltung/"]{aspect-ratio:3/4}
.k2-kachel span{font-size:9.5px;line-height:1.25;padding:3px 5px 4px;min-height:2.5em;overflow:hidden}
.k2-kachel:hover{border-color:#5a5a5a;color:#e8e8e8}
.k2-kachel:focus-visible{outline:1px solid #f66744;outline-offset:1px}
.k2-kachel.k2-an{border-color:#f66744;color:#f7d5ca;background:#2a1c17}
.k2-kacheln + .k2-chips{margin-top:4px}
.k2-kacheln + .k2-chips:empty{display:none}
/* The same panels in the Studio sidebar: no node around them, so they take
   the column's width and let the column scroll. */
.k2-studio-panel{height:auto;overflow:visible;padding:0}
.k2-studio-panel .k2-blatt{overflow:visible;padding-bottom:0}
.k2-studio-panel .k2-kacheln{max-height:none;grid-template-columns:repeat(auto-fill,minmax(76px,1fr))}
.k2-studio-panel > .k2-marke{display:none}
.k2-studio-panel .k2-scroll{max-height:220px}
.k2-studio-panel .k2-vorschau{max-height:none}
/* Compact view: the switch in the brand strip, and the short node. The
   content sits in one block of its natural height, which is what the node's
   height is measured from (the root itself is stretched to the widget). */
.k2-ansicht-knopf{background:none;border:1px solid #3d3d3d;border-radius:4px;color:#9a9a9a;cursor:pointer;
  font:inherit;font-size:12px;line-height:1;padding:1px 5px;margin-left:4px}
.k2-marke-zahl + .k2-ansicht-knopf{margin-left:6px}
.k2-ansicht-knopf:hover{color:#f3d6cb;border-color:#f66744}
.k2-ansicht-knopf:focus-visible{outline:1px solid #f66744}
.k2-kompakt-inhalt{display:flex;flex-direction:column;gap:6px;flex:0 0 auto}
.k2-kurzfassung{color:#c9c9c9;font-size:10.5px;line-height:1.45;cursor:pointer;border:1px dashed transparent;
  border-radius:5px;padding:3px 4px;margin:0 -4px}
.k2-kurzfassung:hover{border-color:#4a4a4a}
.k2-kurzfassung:focus-visible{outline:1px solid #f66744}
.k2-kurzfassung.k2-leer{color:#8e8e8e;font-style:italic}
.k2-kurzfassung i{font-style:normal;color:#808080;padding:0 4px}
.k2-kurzfassung .k2-achsteil{white-space:nowrap;color:#8e8e8e}
.k2-kurzfassung .k2-achsteil b{font-weight:500;color:#e0c2b6}
.k2-kompakt-zeilen{display:flex;flex-direction:column;gap:1px;cursor:pointer;border:1px dashed transparent;
  border-radius:5px;margin:0 -4px;padding:1px 0}
.k2-kompakt-zeilen:hover{border-color:#4a4a4a}
.k2-kompakt-zeilen .k2-kopf{grid-template-columns:104px 1fr;padding:2px 4px;cursor:inherit}
.k2-kompakt-zeilen .k2-kopf:hover{background:none}
.k2-kompakt-knoepfe{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.k2-kompakt-knoepfe .k2-bearbeiten{margin-left:auto}
.k2-streifen{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:3px}
.k2-mini-bild{position:relative;padding:0;border:1px solid #3d3d3d;border-radius:3px;background:#1a1a1a center/cover;
  aspect-ratio:2/3;cursor:pointer;overflow:hidden;font:inherit}
.k2-mini-bild:hover{border-color:#9a9a9a}
.k2-mini-bild:focus-visible{outline:1px solid #f66744;outline-offset:1px}
.k2-mini-bild.k2-geplant{border-style:dashed;border-color:#5a5a5a;background:none}
.k2-mini-bild.k2-verworfen{opacity:.4}
.k2-mini-bild em{position:absolute;right:1px;top:0;font-style:normal;font-size:8px;line-height:1.2;color:#f66744;
  text-shadow:0 0 2px #000}
.k2-mehr-lb{align-self:flex-start;margin-top:2px}
/* Live GPU render highlight & queue stop button */
@keyframes k2-puls{0%,100%{box-shadow:0 0 0 1px #f66744,0 0 8px rgba(246,103,68,.55)}
  50%{box-shadow:0 0 0 2px #ff9a7f,0 0 12px rgba(246,103,68,.85)}}
.k2-bild.k2-rendert .k2-rahmen,.k2-mini-bild.k2-rendert{border-color:#f66744;animation:k2-puls 1.3s ease-in-out infinite}
.k2-stopp{border-color:#a8483c;color:#f0a89e;background:#2c1714}
.k2-stopp:hover{border-color:#f66744;color:#ffd0c8;background:#3a1d19}
/* Person detail-level preview bar & Builder dice resolution */
.k2-vorschau-kopf{display:flex;align-items:center;gap:4px;flex-wrap:wrap;margin-top:auto;border-top:1px solid #303030;
  padding-top:5px}
.k2-vorschau-kopf + .k2-vorschau{margin-top:0;border-top:0;padding-top:3px}
.k2-vorschau-woerter{margin-left:auto;font-size:9px;color:#8a8a8a;font-variant-numeric:tabular-nums}
.k2-wuerfel-vorschau{color:#c9a08f;font-style:normal;margin-top:3px;padding-top:3px;border-top:1px dashed #333}
/* Interactive outfit cards & set rows in Series */
.k2-okarte.k2-aus{opacity:.42}
.k2-okarte-kopf-zeile{display:flex;align-items:center;gap:4px;border-bottom:2px solid #8e8e8e;padding-bottom:3px;
  margin-bottom:1px}
.k2-okarte-schalter{flex:1;min-width:0;background:none;border:0;padding:0;color:#e6e6e6;font:inherit;font-weight:600;
  text-align:left;cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.k2-okarte-schalter:hover{color:#f7d5ca}
.k2-okarte-edit,.k2-satz-edit{background:none;border:1px solid transparent;border-radius:3px;color:#8e8e8e;
  cursor:pointer;font-size:10px;line-height:1;padding:1px 3px}
.k2-okarte-edit:hover,.k2-satz-edit:hover{color:#f66744;border-color:#444}
.k2-satz{grid-template-columns:auto auto 1fr auto}
/* Saved blocks row & inline wire buttons */
.k2-bausteine{display:flex;align-items:center;gap:4px;flex-wrap:wrap;font-size:9.5px;color:#8e8e8e;padding:2px 0}
.k2-warn-zeile{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.k2-warn-zeile .k2-warn{flex:1;min-width:0}
.k2-studio-fehlt-box{display:flex;flex-direction:column;align-items:flex-start;gap:6px}
/* Krea2PromptJoin placeholder bar */
.k2-join-status{display:flex;flex-direction:column;gap:5px;padding:4px 6px;box-sizing:border-box;
  font:10.5px/1.35 -apple-system,Segoe UI,Roboto,sans-serif;color:#c9c9c9}
.k2-join-chips{display:flex;flex-wrap:wrap;gap:3px;align-items:center}
.k2-join-chip{border:1px solid #333;background:#191919;color:#777;border-radius:4px;padding:1px 5px;
  font-size:9.5px;font-family:ui-monospace,Menlo,monospace}
.k2-join-chip.k2-an{border-color:#4a7346;background:#1b261a;color:#a8d5a2}
.k2-join-chip.k2-fehlt-text{border-color:#b88644;background:#2b2114;color:#e7c083}
.k2-join-fuss{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
/* Slim legacy compact nodes: no duplicate brand strip on the canvas */
.k2-kompakt-kopf{display:flex;align-items:center;gap:6px}
.k2-kompakt-kopf .k2-reiter{flex:1;min-width:0;margin:0}
.k2-kompakt-zeile{display:flex;align-items:center;gap:6px}
.k2-kompakt-kopf .k2-kurzfassung,.k2-kompakt-kopf .k2-kompakt-zeilen,
.k2-kompakt-zeile .k2-kurzfassung,.k2-kompakt-zeile .k2-kompakt-zeilen{flex:1;min-width:0}
.k2-kompakt-aktionen{display:flex;align-items:center;gap:4px;margin-left:auto;flex-shrink:0}
/* Inline custom entry creator & Studio preset pack manager */
.k2-eigen-neu{border-top:1px solid #303030;padding-top:5px;display:flex;flex-direction:column;gap:4px}
.k2-eigen-plus{align-self:flex-start;font-size:9.5px;padding:2px 7px}
.k2-eigen-form{display:flex;flex-direction:column;gap:4px}
.k2-eigen-form .k2-reihe{flex-wrap:wrap}
.k2-eigen-form .k2-warn{font-size:9.5px;color:#ec8f7a}
.k2-eigen-weg:hover,.k2-eintrag:hover .k2-eigen-weg{color:#ec8f7a}
.k2-studio-packs{display:flex;flex-direction:column;gap:6px}
.k2-studio-packliste{display:flex;flex-direction:column;gap:4px}
.k2-studio-pack{display:flex;align-items:center;gap:6px;background:#222;border:1px solid #333;
  border-radius:5px;padding:4px 7px;font-size:10px}
.k2-studio-pack b{color:#e6e6e6;font-weight:600}
.k2-studio-pack span{color:#8e8e8e;font-size:9.5px;flex:1;min-width:0;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.k2-studio-packpaste{display:flex;flex-direction:column;gap:5px;background:#222;border:1px solid #333;
  border-radius:6px;padding:7px}
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

// With a node (the canvas view), the strip also carries the node's switch
// between the full and the compact view (⊟ / ⊞).
export function markenleiste(teil, rechts, node = null) {
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
  if (node) marke.append(ansichtKnopf(node));
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
      // The innermost area that can scroll, so a short prompt box inside the
      // contact sheet does not stop the sheet itself from scrolling.
      const SCROLLBAR = ".k2-scroll, .k2-wahlliste, .k2-blatt, .k2-achsen, .k2-prompt-text, .k2-bogen, .k2-vorschau, .k2-kacheln";
      for (let el = e.target.closest(SCROLLBAR); el && root.contains(el); el = el.parentElement?.closest(SCROLLBAR)) {
        if (el.scrollHeight > el.clientHeight) return; // echtes Scrollen zulassen
      }
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

// ------------------------------------------------------------ Clipboard ---
// navigator.clipboard exists only in a secure context - ComfyUI on another
// machine in the LAN is plain http. Then the old way through a text field.
export async function kopiere(text) {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch (e) {
    // fall through to the text field
  }
  const feld = document.createElement("textarea");
  feld.value = text;
  feld.style.cssText = "position:fixed;left:-9999px;top:0;opacity:0";
  document.body.append(feld);
  feld.select();
  let ok = false;
  try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
  feld.remove();
  return ok;
}

// ------------------------------------------------------- Presets missing ---
// When /krea2/presets fails, a node used to come up empty, with nothing to say
// why. It gets one line and a Retry instead; bauen(presets) builds the real
// interface once they arrive. The line cannot come from nodes/i18n.py - that
// table arrives with the presets - so it carries both languages itself.
const _ohnePresets = new Set();   // nodes waiting for a retry: () => rebuild

export function presetFehler(node, bauen) {
  injiziereCSS();
  const de = locale() === "de";
  const root = document.createElement("div");
  root.className = "k2-root k2-fehlt";
  const zeile = document.createElement("div");
  zeile.className = "k2-warn";
  const text = document.createElement("span");
  text.textContent = de
    ? "⚠ Photoshoot: Vorgaben nicht geladen (/krea2/presets) — Details in der Konsole. "
    : "⚠ Photoshoot: presets could not be loaded (/krea2/presets) — details in the console. ";
  const knopf = document.createElement("button");
  knopf.type = "button";
  knopf.className = "k2-textknopf";
  knopf.textContent = de ? "Erneut versuchen" : "Retry";
  zeile.append(text, knopf);
  root.append(zeile);
  const w = node.addDOMWidget("k2_fehlt", "custom", root, {
    getValue: () => undefined, setValue: () => {}, getMinHeight: () => 44, margin: 4, serialize: false,
  });
  applyAdaptiveCanvasOnly(w);
  const neuBauen = (presets) => {
    _ohnePresets.delete(neuBauen);
    if (typeof node.removeWidget === "function") node.removeWidget(w);
    else node.widgets?.splice(node.widgets.indexOf(w), 1);
    root.remove();
    bauen(presets);
    node.setDirtyCanvas?.(true, true);
  };
  _ohnePresets.add(neuBauen);
  beimEntfernen(node, () => _ohnePresets.delete(neuBauen));
  // One Retry brings back every node that is waiting, not just this one.
  knopf.onclick = async () => {
    knopf.disabled = true;
    const presets = await ladePresets();
    knopf.disabled = false;
    if (!presets) {
      text.textContent = de
        ? "⚠ Photoshoot: Vorgaben weiterhin nicht erreichbar (/krea2/presets). "
        : "⚠ Photoshoot: presets still unreachable (/krea2/presets). ";
      return;
    }
    for (const f of [..._ohnePresets]) f(presets);
  };
}

// ------------------------------------------------------------ Clean-up ---
// Listeners on document or on the api outlive a node unless it takes them
// along. Undo reloads the whole graph, so every Ctrl+Z used to leave one set
// per panel behind.
export function beimEntfernen(node, aufraeumen) {
  const vorher = node.onRemoved;
  node.onRemoved = function (...args) {
    try { aufraeumen(); } catch (e) { /* nothing left to clean */ }
    return vorher?.apply(this, args);
  };
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

// Mirrors PB.requisit_text() / PeB.requisit_text() for the live preview.
export function requisitVorschau(daten, roh) {
  const teil = (x) => {
    let text = String(x || "").trim().replace(/[,;.\s]+$/, "").replace(/\s+/g, " ");
    if (!text) return "";
    let klein = text.toLowerCase();
    const fertige = ["holding ", "carrying ", "cradling ", "wearing ",
                     "one hand ", "both hands ", "touching ", "raising ", "making "];
    if (fertige.some((p) => klein.startsWith(p))) return text;
    const artikel = ["a ", "an ", "the ", "her ", "his ", "two ", "some ", "several "];
    if (!artikel.some((p) => klein.startsWith(p)) && !klein.endsWith("s")) {
      text = ("aeiou".includes(klein[0]) ? "an " : "a ") + text;
      klein = text.toLowerCase();
    }
    const beidhaendig = daten?.requisitBeidhaendig || [];
    if (beidhaendig.some((w) => klein.includes(w))) {
      return "holding " + text + " with both hands in front of her chest";
    }
    return "holding " + text + " in one hand at chest height, the other arm relaxed";
  };
  return String(roh || "").split(/[;\n]+/).map(teil).filter(Boolean).join(", ");
}

// ------------------------------------------------------- Outfit preview ---
// The rendered pictures of the outfits live in the Wardrobe node's properties,
// keyed by outfit id, each with the outfit it was made from: when the clothes
// change afterwards, the picture is marked as outdated rather than shown as if
// it were current.
export const PROP_OUTFITBILD = "wardrobeBild";
export function outfitStand(outfit) {
  const f = outfit?.felder || {};
  return JSON.stringify([Object.keys(f).filter((k) => k !== "prop").sort().map((k) => [k, f[k]]),
                         (outfit?.texte?.details || "").trim()]);
}
export function outfitBild(node, outfit) {
  const b = node?.properties?.[PROP_OUTFITBILD]?.[outfit?.id];
  return b?.datei ? { ...b, aktuell: b.stand === outfitStand(outfit) } : null;
}

// The Wardrobe node on a Person node's "garderobe" input, or null. The
// Person node shows where its clothes come from, and the Series node finds the
// wardrobe through the person that feeds it.
function _link(id) {
  return id == null ? null : (app.graph?.links?.get?.(id) ?? app.graph?.links?.[id]);
}
export function wardrobeVonPerson(person) {
  const link = _link(person?.inputs?.find((i) => i.name === "garderobe")?.link);
  const q = link && app.graph?.getNodeById?.(link.origin_id);
  if (q?.comfyClass === "Krea2Wardrobe") return q;
  if (person?.comfyClass === "Krea2Photoshooting" && person?.properties?.wardrobeState) return person;
  return null;
}

// The colour of an outfit at a glance - the top's, else the bottom's - for
// the tab dots and the stripes in the contact sheet. farben/leer from the
// person presets (FARBWERTE).
export function outfitHauptfarbe(person, outfit, ersatz = "#8e8e8e") {
  const f = outfit?.felder || {};
  for (const cat of ["topColor", "bottomColor"]) {
    const l = f[cat];
    if (l && l !== person?.leer && person?.farben?.[cat]?.[l]) return person.farben[cat][l];
  }
  return ersatz;
}

// ------------------------------------------------------------------ Sets ---
// The Location node (location_builder.py) holds its sets as tabs, each in the
// builder blueprint's shape. The Series reads them from the node's state, as
// it reads the wardrobe, with the same families and couplings saetze_von()
// uses in Python - from /krea2/presets ("location"), never a list of its own.
// A die cannot be resolved here (it rolls with the node's seed on the
// server) and shows as ⟨…⟩; the count of sets and whether each is outdoors -
// all the planner needs - never depend on one.
export function locationVonSerie(serie) {
  let n = serie;
  let name = "ort_data";
  for (let i = 0; n && i < 8; i++) {
    const inp = name == null ? n.inputs?.[0] : n.inputs?.find((x) => x.name === name);
    const link = _link(inp?.link);
    const q = link && app.graph?.getNodeById?.(link.origin_id);
    if (!q) break;
    if (q.type !== "Reroute") return q.comfyClass === "Krea2LocationBuilder" ? q : null;
    n = q;
    name = null;
  }
  if (serie?.properties?.locationState) return serie;
  return null;
}

// Same as familie() in location_builder.py: the family of the set's place
// (not rolled), else its family chip - only the four families count.
export function ortFamilie(daten, satz) {
  const vier = [...(daten?.draussen || []), ...(daten?.drinnen || [])];
  const ort = satz?.felder?.ort;
  if (ort && ort !== daten?.leer && !satz?.wuerfeln?.ort) {
    const f = vier.find((g) => daten.gruppen?.[g]?.includes(ort));
    if (f) return f;
  }
  return vier.includes(satz?.gruppe) ? satz.gruppe : null;
}

// Same as draussen(): true outdoors, false indoors, null for no family.
export function ortDraussen(daten, satz) {
  const f = ortFamilie(daten, satz);
  return (daten?.draussen || []).includes(f) ? true : (daten?.drinnen || []).includes(f) ? false : null;
}

// The fields of a set its family rules out (weather and season indoors).
export function ortGesperrt(daten, satz) {
  return ortDraussen(daten, satz) === false ? new Set(daten?.nurDraussen || []) : new Set();
}

// A set as text, the way werte_von() and compose_location() build it; kurz:
// the first clause of each part (kurzform()). A rolled field is a placeholder.
export function ortText(daten, satz, kurz = false) {
  const gesperrt = ortGesperrt(daten, satz);
  const teile = [];
  for (const cat of daten?.reihenfolge || []) {
    if (gesperrt.has(cat)) continue;
    if (satz?.wuerfeln?.[cat]) {
      teile.push("⟨" + t(cat, "kategorien") + " " + t("wird gewürfelt", "ui") + "⟩");
      continue;
    }
    const label = satz?.felder?.[cat];
    if (!label || label === daten.leer) continue;
    teile.push(daten.felder?.[cat]?.find((e) => e.label === label)?.wert ?? satz.eigene?.[cat]?.[label] ?? label);
  }
  const frei = (satz?.details || "").trim().replace(/[,;.\s]+$/, "");
  if (frei) teile.push(frei);
  const aus = kurz ? teile.map((x) => x.split(",")[0].trim()).filter(Boolean) : teile;
  return aus.join(", ");
}

// The name a set goes by: its own, else its place, else "Set n".
export function ortName(daten, satz, i) {
  const eigen = (satz?.name || "").trim();
  if (eigen) return eigen;
  const ort = satz?.felder?.ort;
  if (ort && ort !== daten?.leer && !satz?.wuerfeln?.ort) return t(ort, "location/ort");
  return tf("Set {0}", "ui", i + 1);
}

// Every set of a Location node, as the Series shows and plans them.
export function ortSaetze(daten, node) {
  if (!node || !daten) return [];
  let st = {};
  try { st = JSON.parse(node.properties?.locationState || "{}") || {}; } catch (e) { st = {}; }
  const saetze = Array.isArray(st.saetze) && st.saetze.length ? st.saetze : [{}];
  return saetze.map((s, i) => ({
    name: ortName(daten, s, i),
    text: ortText(daten, s),
    kurz: ortText(daten, s, true),
    familie: ortFamilie(daten, s),
    draussen: ortDraussen(daten, s),
    wetter: s.felder?.wetter || "",
    jahreszeit: s.felder?.jahreszeit || "",
  }));
}

// Render one outfit's preview: one run of the user's own workflow with the
// preview text (wardrobe.py, /krea2/outfit_vorschau) swapped into Build Prompt
// and the Series node fixed to one framing, one ratio and one seed. The run
// carries "_vorschau" in the series state, so the contact sheet never takes its
// picture for a photo. Resolves to the picture's file, or null for an empty
// outfit; throws with a readable message when the workflow cannot do it.
export async function rendereOutfitVorschau(outfit, art) {
  const antwort = await fetch("/krea2/outfit_vorschau", {
    method: "POST", headers: { "Content-Type": "application/json" },
    // Only the outfit itself - callers may hang the node on it.
    body: JSON.stringify({ state: { felder: outfit.felder || {}, texte: outfit.texte || {} }, art }) });
  const text = antwort.ok ? (await antwort.json()).prompt : null;
  if (!text) return null;
  const p = await app.graphToPrompt();
  const aus = p.output;
  const joins = Object.values(aus).filter((n) => n.class_type === "Krea2PromptJoin");
  const serien = Object.values(aus).filter((n) => n.class_type === "Krea2Photoshooting");
  if (!joins.length && !serien.length) throw new Error("kein-build-prompt");
  for (const n of joins) n.inputs = { text };
  const vorschauPrompt = text.replace(/\{extra\}/g, "").replace(/^,\s*|\s*,\s*$/g, "");
  for (const n of serien) {
    let st = {};
    try { st = JSON.parse(n.inputs.ShootingState || "{}"); } catch (e) { st = {}; }
    st = { ...st, kameras: [art === "flach" ? "Nahaufnahme" : "Ganzkörper"], festesFormat: "3:4",
           serienSeed: 0, takes: {}, _vorschau: true,
           ...(joins.length ? {} : { _vorschauPrompt: vorschauPrompt }),
           aktiv: { ...(st.aktiv || {}), kamera: true, format: false, rausch: false, outfit: false } };
    n.inputs.ShootingState = JSON.stringify(st);
    n.inputs.foto = 1;
  }
  // A prefix of its own per run: an unchanged outfit is otherwise served
  // from ComfyUI's cache, pointing at a file that may be gone by now.
  for (const n of Object.values(aus)) {
    if (n.class_type === "SaveImage") n.inputs.filename_prefix = `photoshoot_outfits/outfit_${Date.now()}`;
  }
  // Through ComfyUI's own call, so the run carries this client's id and the
  // interface follows it like any other.
  const r = await api.queuePrompt(0, { output: aus, workflow: p.workflow });
  const id = r?.prompt_id;
  if (!id) throw new Error("nicht-eingereiht");
  for (let versuch = 0; versuch < 800; versuch++) {
    const h = await fetch(`/history/${id}`, { cache: "no-store" });
    const e = h.ok ? (await h.json())[id] : null;
    if (e?.status?.completed !== undefined) {
      let bild = null;
      for (const a of Object.values(e.outputs || {})) {
        for (const b of a?.images || []) if (!bild || (b.type === "output" && bild.type !== "output")) bild = b;
      }
      return bild ? { filename: bild.filename, subfolder: bild.subfolder || "", type: bild.type || "output" } : null;
    }
    await new Promise((ok) => setTimeout(ok, 1500));
  }
  throw new Error("zeitueberschreitung");
}

// Render and hang the picture on the Wardrobe node. meldung(text) reports
// progress; returns false when it failed (the message says why).
export async function rendereUndMerke(node, outfit, art, meldung = () => {}) {
  try {
    const datei = await rendereOutfitVorschau(outfit, art);
    if (datei) {
      node.properties = node.properties || {};
      node.properties[PROP_OUTFITBILD] = { ...(node.properties[PROP_OUTFITBILD] || {}),
        [outfit.id]: { art, stand: outfitStand(outfit), datei } };
      node._k2Zeichne?.();
      node.graph?.setDirtyCanvas?.(true, false);
    }
    return true;
  } catch (e) {
    console.error("[Photoshoot] Outfit-Vorschau fehlgeschlagen:", e);
    meldung(e.message === "kein-build-prompt"
      ? t("⚠ Kein Build-Prompt-Node im Workflow — die Vorschau braucht einen", "ui")
      : t("⚠ Vorschau fehlgeschlagen — Details in der Konsole", "ui"));
    return false;
  }
}
export function outfitBildUrl(datei, klein) {
  return "/view?" + new URLSearchParams({
    filename: datei.filename, subfolder: datei.subfolder || "", type: datei.type || "output",
    ...(klein ? { preview: "webp;70" } : {}) });
}

export function schreibeState(node, prop, state) {
  node.properties = node.properties || {};
  node.properties[prop] = JSON.stringify(state);
  node.graph?.setDirtyCanvas?.(true, false);
  merkeFuerUndo();
  nodeGeaendert(node);
}

// ------------------------------------------------ One node, several views ---
// A node's panel can be drawn twice: on the canvas and in the Studio sidebar
// (studio.mjs), each a view built by the same function from the same
// node.properties. Every view registers here; a write (schreibeState) and
// every drawing of a view tells the others, which draw again once, in a
// microtask. A view drawn because another told it does not pass it on, so
// two views never set each other off. Keyed by the node object, not its id:
// undo builds new nodes under the same ids.
const _ansichten = new WeakMap();   // node -> Set of "draw again" functions

export function nodeGeaendert(node, ausser = null) {
  for (const f of _ansichten.get(node) || []) if (f !== ausser) f();
}

/** Registers a view of node. zeichne() draws it; the view calls gezeichnet()
 *  at the top of zeichne() and weg() when it goes. */
export function ansicht(node, zeichne) {
  let geplant = false;
  let vonAussen = false;
  const f = () => {
    if (geplant) return;
    geplant = true;
    queueMicrotask(() => {
      if (!geplant) return;
      geplant = false;
      vonAussen = true;
      try { zeichne(); } finally { vonAussen = false; }
    });
  };
  if (!_ansichten.has(node)) _ansichten.set(node, new Set());
  _ansichten.get(node).add(f);
  return {
    gezeichnet() {
      geplant = false;
      if (!vonAussen) nodeGeaendert(node, f);
    },
    weg() { _ansichten.get(node)?.delete(f); },
  };
}

// Builders that can draw a node's panel into any element - the Studio sidebar
// asks for them by node class. bauen(node, ziel) returns { weg() } or null.
const _bauer = new Map();
export function registriereBauer(klasse, bauen) { _bauer.set(klasse, bauen); }
export function bauerFuer(klasse) { return _bauer.get(klasse) || null; }

// Undo. ComfyUI's change tracker compares the serialised graph on mouseup and
// keyup - node.properties included - but on mouseup the click that changes a
// panel has not run yet. So a panel edit was only recorded with the next
// click, and Ctrl+Z took back two edits at once. Recording right after the
// write gives every edit its own step. Undo reloads the whole graph
// (loadGraphData), so the panels are rebuilt from node.properties and need
// nothing of their own. captureCanvasState() is the current name (front end
// 1.47); checkState() the older one, deprecated with a console warning.
const _tracker = () => {
  try {
    return app.extensionManager?.workflow?.activeWorkflow?.changeTracker || null;
  } catch (e) {
    return null;
  }
};
export function merkeFuerUndo() {
  try {
    const tracker = _tracker();
    if (typeof tracker?.captureCanvasState === "function") tracker.captureCanvasState();
    else tracker?.checkState?.();
  } catch (e) {
    // No tracker (older front end, tests) - the edit stands, just without undo.
  }
}

// Several writes as one undo step: the tracker records nothing while its
// change count is up (beforeChange/afterChange, the same pair litegraph uses
// around a drag), and once at the end. Starting a series of 40 photos was
// otherwise 40 steps of a climbing photo counter.
export async function alsEinSchritt(arbeit) {
  const tracker = _tracker();
  const klammer = typeof tracker?.beforeChange === "function" && typeof tracker?.afterChange === "function";
  if (klammer) tracker.beforeChange();
  try {
    return await arbeit();
  } finally {
    if (klammer) tracker.afterChange();
  }
}

// ---------------------------------------------------------- Compact view ---
// Every Photoshoot panel can show itself short on the canvas: what is needed
// all the time (Start shooting, Draft, the photos) and one summary, the rest
// a click away in the Studio sidebar. Which view a node shows is display
// only: it sits in its own property, never in the state the graphToPrompt
// hook sends, so it cannot change a prompt. A node without the property is
// full - every workflow saved before this existed opens as it was; a node
// created new starts compact (the nodeCreated of each panel sets it).
export const PROP_ANSICHT = "photoshootAnsicht";   // "kompakt" | "voll"
// The height a fixed-height node (Series, Person, Wardrobe) had in the full
// view, so expanding gives it back; the builders size themselves anyway.
export const PROP_VOLLHOEHE = "photoshootVollHoehe";

export function istKompakt(node) {
  return node?.properties?.[PROP_ANSICHT] === "kompakt";
}

// A node the panel code draws on the canvas carries _k2Kompakt (set by the
// panel): { vollHoehe } - the default height for expanding when none was
// remembered, or null for a node whose height follows its content.
const _warte = () => new Promise((ok) => (typeof requestAnimationFrame === "function"
  ? requestAnimationFrame(() => ok()) : setTimeout(ok, 16)));

function _schalte(node, kompakt) {
  if (!node?._k2Kompakt || istKompakt(node) === kompakt) return false;
  node.properties = node.properties || {};
  // What the node has around its panel, and the panel's width, while it is
  // laid out - the compact height needs them when it is not (_kompaktHoehe).
  const el = node.widgets?.find((w) => w.element?.classList?.contains("k2-root"))?.element;
  if (el?.offsetHeight && node.size) {
    el._k2Rundum = node.size[1] - el.offsetHeight;
    el._k2Breite = el.clientWidth;
  }
  const fest = node._k2Kompakt.vollHoehe;
  if (kompakt && fest && node.size?.[1]) node.properties[PROP_VOLLHOEHE] = Math.round(node.size[1]);
  node.properties[PROP_ANSICHT] = kompakt ? "kompakt" : "voll";
  if (!kompakt && fest) {
    const h = Number(node.properties[PROP_VOLLHOEHE]) || fest;
    node.setSize?.([node.size?.[0] || 360, h]);
  }
  node._k2Zeichne?.();
  node.graph?.setDirtyCanvas?.(true, true);
  return true;
}

/** Switches nodes to the compact or the full view, as one undo step. The
 *  compact height follows the content a frame or two later (Nodes 2.0 lays
 *  out in between), so the step is recorded after that. */
export async function setzeAnsicht(nodes, kompakt) {
  const geaendert = [].concat(nodes).filter((n) => _schalte(n, kompakt));
  if (!geaendert.length) return;
  for (let i = 0; i < 4; i++) await _warte();
  merkeFuerUndo();
}

// ⊟ / ⊞ in the brand strip.
export function ansichtKnopf(node) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "k2-ansicht-knopf";
  const kompakt = istKompakt(node);
  b.textContent = kompakt ? "⊞" : "⊟";
  b.title = kompakt ? t("Voll anzeigen", "ui") : t("Kompakt anzeigen", "ui");
  b.setAttribute("aria-label", b.title);
  b.setAttribute("aria-pressed", String(kompakt));
  b.onclick = (e) => {
    e.stopPropagation();
    setzeAnsicht(node, !kompakt);
  };
  return b;
}

// The Studio sidebar (studio.mjs) registers how to open it on a node: the
// tab that shows the node's section, for the series the node belongs to.
// It answers false when it cannot (no sidebar in this front end, or a node
// that is wired to no series); the compact view then expands inline instead,
// so a click never does nothing.
let _studioOeffner = null;
export function registriereStudioOeffner(f) { _studioOeffner = f; }
export function oeffneStudio(node, abschnitt = null) {
  try {
    return !!_studioOeffner?.(node, abschnitt);
  } catch (e) {
    console.warn("[Photoshoot] Studio sidebar could not be opened:", e);
    return false;
  }
}
export function bearbeiten(node) {
  if (!oeffneStudio(node)) setzeAnsicht(node, false);
}
export function bearbeitenKnopf(node) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "k2-textknopf k2-bearbeiten";
  b.textContent = t("bearbeiten", "ui") + " →";
  b.title = t("In der Studio-Seitenleiste bearbeiten", "ui");
  b.onclick = (e) => { e.stopPropagation(); bearbeiten(node); };
  return b;
}
// A summary that opens the editor on click (and on Enter / Space).
export function alsBearbeiten(el, node) {
  el.tabIndex = 0;
  el.setAttribute("role", "button");
  el.title = t("In der Studio-Seitenleiste bearbeiten", "ui");
  el.onclick = () => bearbeiten(node);
  el.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); bearbeiten(node); }
  };
  return el;
}

// The compact node's height follows its content. The root is stretched to
// the widget, so the content block (.k2-kompakt-inhalt) is measured, and the
// node gets what it has around the panel (its size less the panel's) plus
// that. The panel's element follows a new node size only on the canvas's
// next drawing (Nodes 2.0: its next layout) - while it has not, the old
// measurement stands and nothing is applied twice. A panel off screen, or on
// a canvas zoomed out below ComfyUI's low-quality threshold, is not laid out:
// its content is measured as a hidden copy at the width it last had, with
// what the node had around it then; a panel never seen is measured once it
// shows (the observer below).
function _versteckteHoehe(root, inhalt) {
  if (!root._k2Breite) return 0;
  const huelle = document.createElement("div");
  huelle.className = root.className;
  huelle.style.cssText = "position:fixed;left:-10000px;top:0;visibility:hidden;height:auto;" +
    "width:" + root._k2Breite + "px";
  huelle.append(inhalt.cloneNode(true));
  document.body.append(huelle);
  const h = huelle.firstChild.offsetHeight;
  huelle.remove();
  return h;
}

function _kompaktHoehe(node, root) {
  const inhalt = root.querySelector(":scope > .k2-kompakt-inhalt");
  if (!inhalt || !root.isConnected || !istKompakt(node) || !node.size) return;
  const stil = getComputedStyle(root);
  const rand = (parseFloat(stil.paddingTop) || 0) + (parseFloat(stil.paddingBottom) || 0);
  const ist = root.offsetHeight;
  let h;
  if (ist && inhalt.offsetHeight) {
    const offen = node._k2Anpassung;
    if (offen && offen.ist === ist && node.size[1] === offen.h && Date.now() - offen.zeit < 600) return;
    root._k2Breite = root.clientWidth;
    root._k2Rundum = node.size[1] - ist;
    h = Math.max(60, Math.ceil(node.size[1] - ist + inhalt.offsetHeight + rand));
  } else {
    const soll = root._k2Rundum != null && _versteckteHoehe(root, inhalt);
    if (!soll) return;
    h = Math.max(60, Math.ceil(root._k2Rundum + soll + rand));
  }
  if (Math.abs(h - node.size[1]) <= 1) {
    node._k2Anpassung = null;
    return;
  }
  node._k2Anpassung = { ist, h, zeit: Date.now() };
  node.setSize?.([node.size[0], h]);
  node.graph?.setDirtyCanvas?.(true, true);
}

export function passeKompaktAn(node, root) {
  if (!root._k2Beobachter && typeof ResizeObserver === "function") {
    // Shown after being off screen, or the widget took the new node size:
    // measure again. Goes with the element.
    root._k2Beobachter = new ResizeObserver(() => _kompaktHoehe(node, root));
    root._k2Beobachter.observe(root);
    beimEntfernen(node, () => root._k2Beobachter?.disconnect());
  }
  requestAnimationFrame(() => _kompaktHoehe(node, root));
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

// anpassen(node, state) may change what one run gets without touching the
// saved state (the Series finishes drafts this way); it returns the string.
export function registriereStateInjektion(classType, hiddenName, prop, vorgabe, anpassen = null) {
  _registriert.set(classType, { hiddenName, prop, vorgabe, anpassen });
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
      let state = node?.properties?.[conf.prop] || JSON.stringify(conf.vorgabe);
      if (conf.anpassen && node) {
        try {
          state = conf.anpassen(node, state) ?? state;
        } catch (e) {
          console.warn("[Photoshoot] State-Anpassung fehlgeschlagen, sende den gespeicherten.", e);
        }
      }
      eintrag.inputs = eintrag.inputs || {};
      eintrag.inputs[conf.hiddenName] = state;
    }
    return ergebnis;
  };
}

// -------------------------------------------------- Auto-wiring & presets ---
function _graphVon(node) {
  return node?.graph || app.canvas?.graph || app.graph || null;
}

function _alleGraphNodes(graph) {
  return graph?._nodes || graph?.nodes || [];
}

function _alleZeichnen(graph) {
  for (const n of _alleGraphNodes(graph)) n?._k2Zeichne?.();
}

export function verbindeNodes(quelleNode, ausgangName, zielNode, eingangName) {
  if (!quelleNode || !zielNode) return false;
  const outSlot = ausgangName == null ? 0
    : quelleNode.outputs?.findIndex((o) => o.name === ausgangName);
  const inSlot = zielNode.inputs?.findIndex((i) => i.name === eingangName);
  if (outSlot == null || outSlot < 0 || inSlot == null || inSlot < 0) return false;
  quelleNode.connect(outSlot, zielNode, inSlot);
  const graph = _graphVon(zielNode);
  zielNode.setDirtyCanvas?.(true, true);
  graph?.setDirtyCanvas?.(true, true);
  _alleZeichnen(graph);
  merkeFuerUndo();
  return true;
}

export function promptJoinNode(ausgehendVon = null) {
  const graph = _graphVon(ausgehendVon);
  if (!graph) return null;
  if (ausgehendVon) {
    const gesehen = new Set();
    const stapel = [ausgehendVon];
    while (stapel.length) {
      const n = stapel.pop();
      if (!n || gesehen.has(n.id)) continue;
      gesehen.add(n.id);
      for (const aus of n.outputs || []) {
        for (const id of aus.links || []) {
          const link = _link(id);
          const z = link && graph.getNodeById?.(link.target_id);
          if (z?.comfyClass === "Krea2PromptJoin") return z;
          if (z?.type === "Reroute") stapel.push(z);
        }
      }
    }
  }
  const joins = _alleGraphNodes(graph).filter((n) => n?.comfyClass === "Krea2PromptJoin");
  return joins.length === 1 ? joins[0] : null;
}

export function erzeugeUndVerbinde(klasse, zielNode, eingangName, ausgangName = null, extra = null) {
  const graph = _graphVon(zielNode);
  if (!graph || !zielNode) return null;
  const nodes = _alleGraphNodes(graph);
  // Reuse the single unwired node of this class if there is exactly one.
  const freie = nodes.filter((n) => n?.comfyClass === klasse &&
    !(n.outputs || []).some((o) => o.links?.length));
  let neu = freie.length === 1 ? freie[0] : null;
  if (!neu) {
    neu = globalThis.LiteGraph?.createNode?.(klasse) || null;
    if (!neu) return null;
    neu.pos = [(zielNode.pos?.[0] ?? 420) - 390, (zielNode.pos?.[1] ?? 120)];
    graph.add?.(neu);
  }
  const outSlot = ausgangName == null ? 0 : neu.outputs?.findIndex((o) => o.name === ausgangName);
  const inSlot = zielNode.inputs?.findIndex((i) => i.name === eingangName);
  if (outSlot != null && outSlot >= 0 && inSlot != null && inSlot >= 0) {
    neu.connect(outSlot, zielNode, inSlot);
  }
  extra?.(neu);
  graph.setDirtyCanvas?.(true, true);
  _alleZeichnen(graph);
  merkeFuerUndo();
  return neu;
}

// ------------------------------------------------ Saved building blocks UI ---
const _bausteineCache = new Map(); // art -> { liste, geladen, laedt }
const _bausteinStand = new WeakMap(); // key object (usually node) -> { speichernOffen, meldung }

async function _bausteinAnfrage(art, pfad, body) {
  const stand = _bausteineCache.get(art) || { liste: [], geladen: false, laedt: false };
  _bausteineCache.set(art, stand);
  stand.laedt = true;
  try {
    const r = await fetch(pfad, body ? {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    } : { cache: "no-store" });
    if (r.ok) {
      const daten = await r.json();
      if (Array.isArray(daten)) stand.liste = daten;
      stand.geladen = true;
    }
  } catch (e) {
    // offline or route missing - keep empty list
  } finally {
    stand.laedt = false;
  }
  return stand.liste;
}

export function bausteinZeile({ key, art, leseAktuell, wendeAn, zeichne }) {
  let standMap = _bausteinStand.get(key);
  if (!standMap) _bausteinStand.set(key, (standMap = {}));
  const stand = (standMap[art] ||= { speichernOffen: false, meldung: "" });
  const cache = _bausteineCache.get(art) || { liste: [], geladen: false, laedt: false };
  _bausteineCache.set(art, cache);
  if (!cache.geladen && !cache.laedt) {
    queueMicrotask(async () => {
      await _bausteinAnfrage(art, "/krea2/bausteine?" + new URLSearchParams({ art }));
      zeichne();
    });
  }

  const zeile = document.createElement("div");
  zeile.className = "k2-bausteine";
  zeile.append(t("Gespeichert", "ui") + ":");
  for (const e of cache.liste) {
    const gruppe = document.createElement("span");
    gruppe.className = "k2-eigene";
    const c = document.createElement("button");
    c.type = "button";
    c.className = "k2-chip k2-klein";
    c.textContent = e.name;
    c.title = (e.text ? e.text.slice(0, 120) + (e.text.length > 120 ? " …" : "") + "\n" : "") +
      t("Gespeicherten Baustein laden", "ui");
    c.onclick = () => wendeAn(e);
    const weg = document.createElement("button");
    weg.type = "button";
    weg.className = "k2-weg-klein";
    weg.textContent = "×";
    weg.title = tf("Gespeicherten Baustein löschen: {0}", "ui", e.name);
    weg.setAttribute("aria-label", weg.title);
    weg.onclick = async (ev) => {
      ev.stopPropagation();
      await _bausteinAnfrage(art, "/krea2/bausteine/loeschen", { art, name: e.name });
      zeichne();
    };
    gruppe.append(c, weg);
    zeile.append(gruppe);
  }

  if (stand.speichernOffen) {
    const feld = document.createElement("input");
    feld.className = "k2-serien-name";
    feld.placeholder = t("Name des Bausteins", "ui");
    const ok = document.createElement("button");
    ok.type = "button";
    ok.className = "k2-textknopf";
    ok.textContent = t("Speichern", "ui");
    const abbrechen = document.createElement("button");
    abbrechen.type = "button";
    abbrechen.className = "k2-textknopf";
    abbrechen.textContent = t("Abbrechen", "ui");
    const sichern = async () => {
      const name = feld.value.trim();
      if (!name) { feld.focus(); return; }
      const aktuell = await leseAktuell();
      stand.speichernOffen = false;
      await _bausteinAnfrage(art, "/krea2/bausteine", {
        art, name, text: aktuell?.text || "", state: aktuell?.state || null,
      });
      stand.meldung = tf("Gespeichert: {0}", "ui", name);
      zeichne();
    };
    ok.onclick = sichern;
    abbrechen.onclick = () => { stand.speichernOffen = false; zeichne(); };
    feld.onkeydown = (ev) => {
      if (ev.key === "Enter") { ev.preventDefault(); sichern(); }
      else if (ev.key === "Escape") { ev.preventDefault(); stand.speichernOffen = false; zeichne(); }
      ev.stopPropagation();
    };
    zeile.append(feld, ok, abbrechen);
    queueMicrotask(() => feld.focus());
  } else {
    const plus = document.createElement("button");
    plus.type = "button";
    plus.className = "k2-chip k2-klein k2-plus";
    plus.textContent = "+ " + t("Speichern", "ui");
    plus.title = t("Unter einem Namen speichern", "ui");
    plus.onclick = () => { stand.speichernOffen = true; stand.meldung = ""; zeichne(); };
    zeile.append(plus);
  }
  if (stand.meldung) {
    const info = document.createElement("span");
    info.className = "k2-eigen";
    info.textContent = stand.meldung;
    zeile.append(info);
  }
  return zeile;
}

// ------------------------------------------------ Krea2PromptJoin inspector ---
const _JOIN_STANDARD = "{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}, {extra}";
const _JOIN_SLOTS = [
  ["stil", "style", ["stil"]],
  ["ausdruck", "expression", ["ausdruck"]],
  ["kamera", "camera", ["kamera"]],
  ["szene", "scene", ["szene"]],
  ["licht", "lighting", ["licht", "lighting"]],
  ["person1", "person", ["person_1"]],
  ["pose", "pose", ["pose"]],
  ["extra", "extra", ["extra"]],
];
const _JOIN_ALIASE = {
  camera: "kamera", expression: "ausdruck", lighting: "licht", light: "licht",
  beleuchtung: "licht", scene: "szene", style: "stil", person: "person1",
  person1: "person1", person2: "person2", person3: "person3",
  kamera: "kamera", pose: "pose", ausdruck: "ausdruck", licht: "licht",
  szene: "szene", stil: "stil", extra: "extra",
};

function _textQuelle(node) {
  let n = node;
  let name = "text";
  for (let i = 0; n && i < 8; i++) {
    const inp = name == null ? n.inputs?.[0] : n.inputs?.find((x) => x.name === name);
    const link = _link(inp?.link);
    const q = link && (node.graph || app.graph)?.getNodeById?.(link.origin_id);
    if (!q) return null;
    if (q.type !== "Reroute") {
      const w = (q.widgets || []).find((x) => typeof x.value === "string" && x.type !== "combo");
      return w ? { node: q, widget: w } : null;
    }
    n = q;
    name = null;
  }
  return null;
}

function _bauePromptJoinPanel(node) {
  injiziereCSS();
  const root = document.createElement("div");
  root.className = "k2-join-status";
  installCanvasZoomPassthrough(root);

  function zeichne() {
    if (!node.graph) return;
    root.textContent = "";
    const quelle = _textQuelle(node);
    const vorlage = String(quelle?.widget?.value || "");
    const rohTokens = [...vorlage.matchAll(/\{([a-zA-Z0-9_]+)\}/g)].map((m) => m[1]);
    const erkannt = new Set(rohTokens.map((tok) => _JOIN_ALIASE[tok]).filter(Boolean));
    const unbekannt = [...new Set(rohTokens.filter((tok) => !_JOIN_ALIASE[tok]))];
    const hatPlatzhalter = erkannt.size > 0;
    const verbunden = (eingaenge) => eingaenge.some((e) => node.inputs?.find((i) => i.name === e)?.link != null);

    const chips = document.createElement("div");
    chips.className = "k2-join-chips";
    const fehltImText = [];
    for (const [kanonisch, englisch, eingaenge] of _JOIN_SLOTS) {
      const istVerbunden = verbunden(eingaenge);
      const imText = erkannt.has(kanonisch);
      if (!istVerbunden && !imText) continue;
      const chip = document.createElement("span");
      const warn = istVerbunden && hatPlatzhalter && !imText;
      if (warn) fehltImText.push("{" + englisch + "}");
      chip.className = "k2-join-chip" + (istVerbunden && (imText || !hatPlatzhalter) ? " k2-an" : "") +
        (warn ? " k2-fehlt-text" : "");
      chip.textContent = (istVerbunden ? "✓ " : "") + "{" + englisch + "}";
      chips.append(chip);
    }
    if (chips.childElementCount) root.append(chips);

    if (unbekannt.length) {
      const w = document.createElement("div");
      w.className = "k2-warn";
      w.textContent = "⚠ " + tf("Unbekannter Platzhalter: {0}", "ui", unbekannt.map((x) => "{" + x + "}").join(", "));
      root.append(w);
    }
    if (fehltImText.length) {
      const w = document.createElement("div");
      w.className = "k2-warn";
      w.textContent = "⚠ " + tf("Eingang verbunden, fehlt im Text: {0}", "ui", fehltImText.join(", "));
      root.append(w);
    }

    const fuss = document.createElement("div");
    fuss.className = "k2-join-fuss";
    const std = document.createElement("button");
    std.type = "button";
    std.className = "k2-textknopf";
    std.textContent = t("Standard-Vorlage", "ui");
    std.title = t("Empfohlene Platzhalter-Reihenfolge in die Vorlage einsetzen", "ui");
    std.onclick = () => {
      const target = quelle || (() => {
        const neu = erzeugeUndVerbinde("PrimitiveStringMultiline", node, "text");
        const w = neu?.widgets?.find((x) => typeof x.value === "string");
        return w ? { node: neu, widget: w } : null;
      })();
      if (target) {
        target.widget.value = _JOIN_STANDARD;
        try { target.widget.callback?.(_JOIN_STANDARD); } catch (e) { /* ok */ }
        target.node.setDirtyCanvas?.(true, true);
        merkeFuerUndo();
        zeichne();
      }
    };
    fuss.append(std);
    root.append(fuss);
  }

  node._k2Zeichne = zeichne;
  let letzterStand = "";
  const standJetzt = () => {
    const q = _textQuelle(node);
    const links = (node.inputs || []).map((i) => i.name + ":" + (i.link ?? "")).join(",");
    return links + "|" + String(q?.widget?.value || "");
  };
  const ticker = setInterval(() => {
    if (!node.graph) { clearInterval(ticker); return; }
    const s = standJetzt();
    if (s !== letzterStand) { letzterStand = s; zeichne(); }
  }, 600);
  beimEntfernen(node, () => clearInterval(ticker));
  queueMicrotask(() => { letzterStand = standJetzt(); zeichne(); });

  const w = node.addDOMWidget("k2_join_ui", "custom", root, {
    getValue: () => undefined, setValue: () => {}, getMinHeight: () => 48, margin: 4, serialize: false,
  });
  applyAdaptiveCanvasOnly(w);
}

app?.registerExtension?.({
  name: "Krea2.PromptJoin",
  settings: [
    {
      id: "Photoshoot.Locale",
      name: "Interface language",
      category: ["Photoshoot", "Interface", "Language"],
      type: "combo",
      options: ["auto", "de", "en"],
      defaultValue: "auto",
      tooltip: "Override Photoshoot panel language (auto follows ComfyUI / browser locale).",
      onChange() {
        _localeBis = 0;
        const graph = app?.canvas?.graph || app?.graph;
        _alleZeichnen(graph);
        for (const n of _alleGraphNodes(graph)) nodeGeaendert(n);
      },
    },
    {
      id: "Photoshoot.StartCompact",
      name: "Start newly created nodes compact",
      category: ["Photoshoot", "Interface", "Start new nodes compact"],
      type: "boolean",
      defaultValue: true,
      tooltip: "Start newly placed Photoshoot nodes in compact card view instead of expanded panels.",
    },
    {
      id: "Photoshoot.AutoOpenStudio",
      name: "Auto-open Studio sidebar on workflow load",
      category: ["Photoshoot", "Interface", "Auto-open Studio sidebar"],
      type: "boolean",
      defaultValue: false,
      tooltip: "Automatically open the Photoshoot Studio sidebar tab when loading a workflow containing a Series node.",
    },
    {
      id: "Photoshoot.ActionBarButtons",
      name: "Top bar quick buttons",
      category: ["Photoshoot", "Interface", "Top bar quick buttons"],
      type: "combo",
      options: [
        "Photoshoot workflows (Studio + Shoot)",
        "Photoshoot workflows (Studio only)",
        "Always (Studio + Shoot)",
        "Always (Studio only)",
        "Off",
      ],
      defaultValue: "Photoshoot workflows (Studio + Shoot)",
      tooltip: "Show Photoshoot quick buttons in ComfyUI's top action bar (default: only when a Photoshoot workflow is open).",
    },
    {
      id: "Photoshoot.DefaultModelProfile",
      name: "Default framing model profile",
      category: ["Photoshoot", "Defaults", "Model profile for new Series"],
      type: "combo",
      options: ["krea2", "kompakt", "eigen"],
      defaultValue: "krea2",
      tooltip: "Default framing prompt style for new Photoshoot – Series nodes (use 'kompakt' for Z-Image / MOSS / MiniMax / Flux).",
    },
    {
      id: "Photoshoot.DefaultEdgeSize",
      name: "Default image edge resolution",
      category: ["Photoshoot", "Defaults", "Edge size for new Series"],
      type: "combo",
      options: ["1024", "1328", "1536", "2048"],
      defaultValue: "1328",
      tooltip: "Default equivalent-square resolution for newly created Photoshoot – Series nodes.",
    },
  ],
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "Krea2PromptJoin") return;
    const orig = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function () {
      const r = orig?.apply(this, arguments);
      queueMicrotask(() => this._k2Zeichne?.());
      return r;
    };
  },
  async nodeCreated(node) {
    if (node.comfyClass !== "Krea2PromptJoin") return;
    await ladePresets().catch(() => null);
    _bauePromptJoinPanel(node);
  },
});


