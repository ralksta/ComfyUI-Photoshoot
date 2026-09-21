"""
Custom entries - list entries users add themselves, from JSON files.

The built-in option data stays Python (PRESETS in the builders): code keys
off those labels, the wordings carry their render-test comments, and the
publish filter patches exact lines. What a user adds - a hat, a light setup,
a look - comes from JSON instead:

  ComfyUI/user/krea2_presets/*.json      the user's own files (survive updates)

  {
    "format": "photoshoot-presets/1",
    "name": "My hats",
    "entries": [
      {"field": "headwear", "label": "Trilby", "prompt": "a narrow-brimmed straw trilby"},
      {"builder": "style", "field": "look", "label": "Expired Superia",
       "prompt": "shot on expired Fuji Superia, warm cast, soft halation"}
    ]
  }

Per entry: "field" and "label" and "prompt" are required; "builder" defaults
to "person" (person, pose, expression, lighting, style); optional are "group"
(a family of that field, or a new one), "en" (display name, default the
label) and "hex" (swatch of a colour field). A file-wide "dice": true lets its
entries into the dice pools; by default a custom entry is never rolled.

Custom entries are kept apart from PRESETS, so poster positions, the smoke
test and the publish filter never see them. Nothing here is fatal: a broken
file or entry is skipped with a message, which /krea2/custom reports.
"""

import json
import os
import re

FORMAT = "photoshoot-presets/1"
ORDNER = "krea2_presets"

# The builder names a file may use -> the key of that builder in /krea2/presets.
BUILDER = {
    "person": "person",
    "pose": "pose",
    "expression": "ausdruck",
    "ausdruck": "ausdruck",
    "lighting": "lighting",
    "style": "style",
}

# Fields a file must not extend. Age and gender carry the 18+ guarantee of the
# public package; an import file must not be a way around it.
GESPERRT = {("person", "age"), ("person", "gender"), ("person", "type")}

# The family custom entries land in when they name none of the field's own.
FAMILIE = "Eigene"

LABEL_MAX = 60
PROMPT_MAX = 300
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_PLATZHALTER = re.compile(r"\{\w+\}")

# (builder key, field) -> [entry dict]; filled by lade().
EINTRAEGE = {}
MELDUNGEN = []
DATEIEN = []


def _presets(builder):
    # Imported late: the builders import this module for their fallback.
    if builder == "person":
        from . import person_builder as m
    elif builder == "pose":
        from . import pose_builder as m
    elif builder == "ausdruck":
        from . import expression_builder as m
    elif builder == "lighting":
        from . import lighting_builder as m
    else:
        from . import style_builder as m
    return m.PRESETS


def _kernnamen(builder, feld):
    """Every name a built-in entry of the field goes by, lower case: the German
    label and its English display name. The LLM prompt lists the English ones,
    so a "Bucket hat" must not load as a second bucket hat."""
    from . import i18n
    anzeige = i18n.tabelle().get(builder, {}).get(feld, {})
    namen = set()
    for label, _ in _presets(builder)[feld]:
        namen.add(label.casefold())
        namen.add(str(anzeige.get(label, label)).casefold())
    return namen


def _farbfelder(builder):
    if builder != "person":
        return set()
    from . import person_builder as m
    return set(getattr(m, "FARBWERTE", {}))


def pruefe(daten, quelle="", vergeben=None, gegen_kern=True):
    """Checks one parsed file. Returns (entries, messages).

    vergeben: labels already taken per (builder, field), across files - a
    later duplicate is skipped. gegen_kern=False skips the clash with the
    built-in labels - for checking the built-in entries themselves. Pure apart
    from reading PRESETS, so the smoke test runs it without ComfyUI.
    """
    vergeben = {} if vergeben is None else vergeben
    meldungen = []
    gut = []
    pre = f"{quelle}: " if quelle else ""
    if not isinstance(daten, dict):
        return [], [pre + "not a JSON object"]
    if daten.get("format") not in (None, FORMAT):
        meldungen.append(pre + f"unknown format {daten.get('format')!r}, read as {FORMAT}")
    liste = daten.get("entries")
    if not isinstance(liste, list):
        return [], meldungen + [pre + '"entries" is missing or not a list']
    wuerfeln = daten.get("dice") is True
    for i, e in enumerate(liste, 1):
        wo = f"{pre}entry {i}"
        if not isinstance(e, dict):
            meldungen.append(f"{wo}: not an object")
            continue
        builder = BUILDER.get(str(e.get("builder", "person")).strip().lower())
        feld = str(e.get("field", "")).strip()
        label = str(e.get("label", "")).strip()
        prompt = " ".join(str(e.get("prompt", "")).split())
        wo = f"{wo} ({label or '?'})"
        if not builder:
            meldungen.append(f"{wo}: unknown builder {e.get('builder')!r}")
            continue
        presets = _presets(builder)
        if feld not in presets:
            meldungen.append(f"{wo}: {builder} has no field {feld!r}")
            continue
        if (builder, feld) in GESPERRT:
            meldungen.append(f"{wo}: the field {feld!r} cannot be extended")
            continue
        if not label or not prompt:
            meldungen.append(f"{wo}: label and prompt must not be empty")
            continue
        if len(label) > LABEL_MAX or len(prompt) > PROMPT_MAX:
            meldungen.append(f"{wo}: label over {LABEL_MAX} or prompt over {PROMPT_MAX} characters")
            continue
        if label == "—":
            meldungen.append(f"{wo}: '—' is reserved for 'nothing'")
            continue
        if gegen_kern and label.casefold() in _kernnamen(builder, feld):
            meldungen.append(f"{wo}: {label!r} is already a built-in {feld}; the built-in one stays")
            continue
        schon = vergeben.setdefault((builder, feld), set())
        if label.casefold() in schon:
            meldungen.append(f"{wo}: {label!r} is already defined for {feld}; the first one stays")
            continue
        # Only the placeholders the field's own values use ({c} = hair colour).
        erlaubt = set(_PLATZHALTER.findall(" ".join(w for _, w in presets[feld])))
        fremd = set(_PLATZHALTER.findall(prompt)) - erlaubt
        if fremd:
            meldungen.append(f"{wo}: placeholder {', '.join(sorted(fremd))} not allowed in {feld}")
            continue
        hexwert = str(e.get("hex", "")).strip()
        if hexwert and not _HEX.match(hexwert):
            meldungen.append(f"{wo}: hex {hexwert!r} is not #rrggbb; no swatch")
            hexwert = ""
        if feld in _farbfelder(builder) and not hexwert:
            hexwert = "#8e8e8e"
        gruppe = str(e.get("group", "")).strip()
        schon.add(label.casefold())
        gut.append({
            "builder": builder, "feld": feld, "label": label, "wert": prompt,
            "gruppe": gruppe, "en": str(e.get("en", "")).strip() or label,
            "hex": hexwert, "wuerfeln": wuerfeln, "datei": quelle,
        })
    return gut, meldungen


def ordner():
    """ComfyUI/user/krea2_presets, or None outside ComfyUI."""
    try:
        import folder_paths
    except ImportError:
        return None
    return os.path.join(folder_paths.get_user_directory(), ORDNER)


# The commented example (docs/). On the first start it is copied into the new
# user folder as example.json.txt: whoever opens the folder finds it, and the
# .txt keeps it out of the lists until it is renamed.
BEISPIEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "docs", "custom_entries_example.json")
BEISPIEL_NAME = "example.json.txt"


def _lege_an(verz):
    """Creates the user folder with the example in it - only when the folder
    does not exist yet, so a deleted example stays deleted."""
    try:
        os.makedirs(verz)
        if os.path.isfile(BEISPIEL):
            with open(BEISPIEL, encoding="utf-8") as q, \
                 open(os.path.join(verz, BEISPIEL_NAME), "w", encoding="utf-8") as z:
                z.write(q.read())
    except OSError as ex:
        print("[Photoshoot] custom entries: folder not created (%s)" % ex)


def lade(verzeichnisse=None):
    """(Re)reads every *.json from the given folders (default: the user
    folder, created with the example on first use). Replaces EINTRAEGE,
    MELDUNGEN and DATEIEN."""
    if verzeichnisse is None:
        o = ordner()
        if o and not os.path.isdir(o):
            _lege_an(o)
        verzeichnisse = [o] if o else []
    neu, meldungen, dateien, vergeben = {}, [], [], {}
    for verz in verzeichnisse:
        if not verz or not os.path.isdir(verz):
            continue
        for name in sorted(os.listdir(verz)):
            if not name.lower().endswith(".json"):
                continue
            pfad = os.path.join(verz, name)
            try:
                with open(pfad, encoding="utf-8") as f:
                    daten = json.load(f)
            except (OSError, ValueError) as ex:
                meldungen.append(f"{name}: cannot be read ({ex})")
                continue
            gut, m = pruefe(daten, name, vergeben)
            meldungen += m
            dateien.append({"file": name, "name": str(daten.get("name", "")) if isinstance(daten, dict) else "",
                            "entries": len(gut)})
            for e in gut:
                neu.setdefault((e["builder"], e["feld"]), []).append(e)
    EINTRAEGE.clear()
    EINTRAEGE.update(neu)
    MELDUNGEN[:] = meldungen
    DATEIEN[:] = dateien
    for m in meldungen:
        print("[Photoshoot] custom entries:", m)
    return EINTRAEGE


def eintraege(builder, feld):
    return EINTRAEGE.get((builder, feld), [])


def wert(builder, feld, label, kopie=None):
    """The prompt of a custom entry: the loaded file first, then the copy the
    node state carries (kopie = state["eigene"]), so a shared workflow still
    renders on a machine without the file."""
    if not label:
        return None
    for e in eintraege(builder, feld):
        if e["label"] == label:
            return e["wert"]
    if isinstance(kopie, dict):
        w = (kopie.get(feld) or {}).get(label) if isinstance(kopie.get(feld), dict) else None
        if isinstance(w, str) and w.strip():
            return " ".join(w.split())[:PROMPT_MAX]
    return None


def wuerfelbar(builder, feld):
    """Labels of the custom entries that may be rolled (file with "dice": true)."""
    return [e["label"] for e in eintraege(builder, feld) if e["wuerfeln"]]


def _kernfamilien(builder, feld):
    """label -> English family name of the built-in entries of one field."""
    from . import i18n
    if builder == "person":
        from . import person_builder as m
        tabelle = {"shoes": m.SCHUH_GRUPPEN, "top": m.OBERTEIL_GRUPPEN,
                   "bottom": m.UNTERTEIL_GRUPPEN, "headwear": m.KOPF_GRUPPEN}.get(feld, {})
    else:
        from . import pose_builder, expression_builder, lighting_builder, style_builder
        tabelle = {("pose", "haltung"): pose_builder.HALTUNG_GRUPPEN,
                   ("ausdruck", "stimmung"): expression_builder.STIMMUNG_GRUPPEN,
                   ("lighting", "setup"): lighting_builder.LICHT_GRUPPEN,
                   ("style", "look"): style_builder.LOOK_GRUPPEN}.get((builder, feld), {})
    return {l: str(i18n.FAMILIEN.get(g, g)) for g, labels in tabelle.items() for l in labels}


def exportiere_kern(builder):
    """The built-in entries of one builder in the file format - a template for
    users (German label, English name, English family), and in the smoke test
    proof that the core passes the same check."""
    from . import i18n
    name = [k for k, v in BUILDER.items() if v == builder][0]
    eintraege = []
    for feld, liste in _presets(builder).items():
        if (builder, feld) in GESPERRT:
            continue
        anzeige = i18n.tabelle().get(builder, {}).get(feld, {})
        familien = _kernfamilien(builder, feld)
        for label, prompt in liste:
            e = {"builder": name, "field": feld, "label": label, "en": anzeige.get(label, label)}
            if label in familien:
                e["group"] = familien[label]
            e["prompt"] = prompt
            eintraege.append(e)
    return {"format": FORMAT, "name": f"Built-in {name} entries (template)", "entries": eintraege}


def _dateiname(name):
    """A safe *.json name inside the folder - no "../", no separators."""
    stamm = re.sub(r"[^\w\s.-]", "", str(name or "").strip(), flags=re.UNICODE)
    stamm = re.sub(r"\s+", "_", stamm).strip("._")[:80]
    if stamm.lower().endswith(".json"):
        stamm = stamm[:-5]
    return (stamm.strip("._") or "eigene") + ".json"


def speichere(name, daten, ersetzen=False):
    """Writes an imported file into the user folder and reloads. Raises
    ValueError when nothing in it passes the check, FileExistsError when the
    name is taken and ersetzen is False. Returns (file name, messages)."""
    verz = ordner()
    if not verz:
        raise ValueError("no ComfyUI user folder")
    datei = _dateiname(name or (daten.get("name") if isinstance(daten, dict) else ""))
    pfad = os.path.join(verz, datei)
    if os.path.exists(pfad) and not ersetzen:
        raise FileExistsError(datei)
    # Checked against the other loaded files, as lade() will do.
    vergeben = {}
    for (b, f), liste in EINTRAEGE.items():
        vergeben[(b, f)] = {e["label"] for e in liste if e["datei"] != datei}
    gut, meldungen = pruefe(daten, datei, vergeben)
    if not gut:
        raise ValueError("; ".join(meldungen) or "no entries")
    os.makedirs(verz, exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)
    lade()
    return datei, meldungen


def loesche(name):
    verz = ordner()
    datei = _dateiname(name)
    pfad = os.path.join(verz or "", datei)
    if not verz or not os.path.isfile(pfad):
        raise FileNotFoundError(datei)
    os.remove(pfad)
    lade()
    return datei


def stand():
    """What /krea2/custom answers - English keys, users read it."""
    return {"folder": ordner(), "files": list(DATEIEN), "messages": list(MELDUNGEN),
            "count": sum(len(v) for v in EINTRAEGE.values())}
