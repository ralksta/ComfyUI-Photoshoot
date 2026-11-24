"""
Shoot files - a whole shoot as one shareable JSON file.

A shoot is what the Series panel works from: the person, her outfits, the
pose, expression, lighting and style builders, the series itself (count,
start number, series seed, pools, axes), the scene text and the Build Prompt
template. One file carries all of it:

  {
    "format": "photoshoot-shoot/1",
    "name": "Rainy afternoon",
    "person":     {...the Person node's state...},
    "wardrobe":   {...the Wardrobe node's state...},
    "pose":       {...}, "expression": {...}, "lighting": {...}, "style": {...},
    "location":   {...the Location node's state: its sets...},
    "series":     {...the Series node's state...},
    "scene":      "a sunlit loft with tall windows",
    "template":   "{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}"
  }

Every section is optional. The top level is English on purpose - users open
and share these files, like the custom-entry files (eigene.py). The sections
are the node states exactly as they sit in node.properties, German keys and
labels included, so saving and loading a shoot gives back the very same
properties. Custom entries in use travel as prompt copies inside their
section ("eigene", as the nodes already keep them), so the file renders on a
machine without the user's custom JSON.

pruefe() checks a file against the live presets: every label against
PRESETS, the loaded custom entries and the copies the file carries. An unknown
label is an error in the list it returns, never an exception, and is dropped
from the normalized shoot. English display labels are accepted and mapped
back to the German keys (nodes/i18n.py), so a file written by hand or by a
chat LLM can use what the interface shows. With streng=True (the Director,
regie.py) only built-in labels pass, free texts other than the scene are
dropped and nothing below 18 gets through.

Stored under ComfyUI/user/krea2_shoots/<name>.json.
"""

import copy
import difflib
import json
import os
import re
import time

from . import eigene as EG
from . import expression_builder as EB
from . import i18n
from . import lighting_builder as LB
from . import location_builder as OB
from . import person_builder as PeB
from . import pose_builder as PB
from . import shooting as SH
from . import style_builder as SB

FORMAT = "photoshoot-shoot/1"
ORDNER = "krea2_shoots"

# Section of the file -> node class that holds it (the frontend finds the
# nodes by these) and the node.properties key of its state.
ABSCHNITTE = {
    "person": ("Krea2PersonBuilder", "personState"),
    "wardrobe": ("Krea2Wardrobe", "wardrobeState"),
    "pose": ("Krea2PoseBuilder", "poseState"),
    "expression": ("Krea2ExpressionBuilder", "expressionState"),
    "lighting": ("Krea2LightingBuilder", "lightingState"),
    "style": ("Krea2StyleBuilder", "styleState"),
    "location": ("Krea2LocationBuilder", "locationState"),
    "series": ("Krea2Photoshooting", "shootingState"),
}
TEXTE = ("scene", "template")

# How the panel finds the nodes: the inputs that lead to each section - on the
# Series node for the person and the location, on the Build Prompt node it
# feeds for the rest.
# Scene and template are the text widgets of whatever node is wired there.
EINGAENGE = {
    "person": ("person_data",),
    "location": ("ort_data",),
    "pose": ("pose",),
    "expression": ("ausdruck",),
    "lighting": ("lighting", "licht"),
    "style": ("stil",),
    "scene": ("szene",),
    "template": ("text",),
}

# The four panel builders: file section -> (builder key in eigene/i18n,
# module, family field, families).
BAUSTEINE = {
    "pose": ("pose", PB, "haltung", PB.HALTUNG_GRUPPEN),
    "expression": ("ausdruck", EB, "stimmung", EB.STIMMUNG_GRUPPEN),
    "lighting": ("lighting", LB, "setup", LB.LICHT_GRUPPEN),
    "style": ("style", SB, "look", SB.LOOK_GRUPPEN),
    # Its state is a list of sets, each one in this shape (_location()).
    "location": ("location", OB, "ort", OB.ORT_GRUPPEN),
}

PERSON_FELDER = list(PeB._SINGLE)
PERSON_FAMILIEN = {"shoes": PeB.SCHUH_GRUPPEN, "top": PeB.OBERTEIL_GRUPPEN,
                   "bottom": PeB.UNTERTEIL_GRUPPEN, "headwear": PeB.KOPF_GRUPPEN}
KLEIDUNG = sorted(PeB.OUTFIT_FELDER - {"free", "propText"})
PERSON_TEXTE = ("ageExact", "details", "trigger", "referenz", "propText")

# Age labels below 18 (the dev build has them, the public one does not). The
# Director never offers or accepts them, whatever build it runs in.
MINDERJAEHRIG = frozenset(l for l, v in PeB.PRESETS["age"] if "{child}" in v or "{teen}" in v)
MINDESTALTER = 18

TEXT_MAX = 2000
SZENE_MAX = 400
NAME_MAX = 80
OUTFITS_MAX = 12
SAETZE_MAX = 12

# The series: which keys it knows and what they may hold.
ACHSEN = ("kamera", "pose", "ausdruck", "format", "fokus", "rausch", "outfit", "set", "licht",
          "perspektive")
# English words for the same switches - what a hand-written file or an LLM uses.
ACHSEN_EN = {"camera": "kamera", "framing": "kamera", "expression": "ausdruck",
             "ratio": "format", "focus": "fokus", "noise": "rausch",
             "light": "licht", "lighting": "licht", "location": "set",
             "perspective": "perspektive"}
LICHTFOLGEN = {"je_set": "je_set", "tageszeit": "tageszeit", "gemischt": "gemischt",
               "per set": "je_set", "per_set": "je_set", "time of day": "tageszeit",
               "time_of_day": "tageszeit", "mixed": "gemischt"}
REIHENFOLGEN = {"gezogen": "gezogen", "reihum": "reihum", "weit_nah": "weit_nah",
                "drawn": "gezogen", "in turn": "reihum", "in_turn": "reihum",
                "wide to close": "weit_nah", "wide_to_close": "weit_nah",
                "wide → close": "weit_nah"}
OUTFITFOLGEN = {"bloecke": "bloecke", "gemischt": "gemischt",
                "blocks": "bloecke", "mixed": "gemischt"}
BLICKE = {
    "gemischt": "gemischt", "mixed": "gemischt",
    "kamera": "kamera", "camera": "kamera", "at the camera": "kamera",
    "into the camera": "kamera", "in die kamera": "kamera",
    "meist_kamera": "meist_kamera", "mostly camera": "meist_kamera",
    "mostly_camera": "meist_kamera", "meist kamera": "meist_kamera",
    "abgewandt": "abgewandt", "away": "abgewandt",
}
# Keys of one series run rather than its plan - kept in a saved shoot (the
# takes change the noise seed, so the same photos need them), never taken
# from the Director. Draft and the file name folder belong to the workflow
# the series renders in, not to the shoot the Director plans.
LAUF_SCHLUESSEL = ("takes", "favoriten", "wahl", "takesJeFoto", "abdeckung",
                   "verworfen", "runde", "runden", "outfitAuswahl", "entwurf", "ordner")
POOL_FELDER = [cat for cat, _ in SH.FELDER if cat != "kamera"]
POOL_FAMILIEN = {"haltung": PB.HALTUNG_GRUPPEN, "stimmung": EB.STIMMUNG_GRUPPEN}
POOL_ALLE = ("all", "any", "alle")
POOL_AUS = ("off", "none", "no", "aus", SH.NONE)


class Pruefung:
    """Collects errors (something was rejected and dropped) and notes
    (something was adjusted or left out on purpose)."""

    def __init__(self, streng):
        self.streng = streng
        self.fehler = []
        self.hinweise = []

    def f(self, text):
        self.fehler.append(text)

    def h(self, text):
        self.hinweise.append(text)


# ---------------------------------------------------------------- Labels ---
_INDEX = {}


def _anzeige(builder, feld):
    return i18n.tabelle().get(builder, {}).get(feld, {})


def _index(builder, modul, feld):
    """casefolded German label and English display name -> German label, for
    the built-in entries of one field. Built once per field."""
    schluessel = (builder, feld)
    if schluessel not in _INDEX:
        namen = {}
        anzeige = _anzeige(builder, feld)
        for label, _ in modul.PRESETS.get(feld, []):
            namen.setdefault(label.casefold(), label)
        for label, _ in modul.PRESETS.get(feld, []):
            namen.setdefault(str(anzeige.get(label, label)).casefold(), label)
        _INDEX[schluessel] = namen
    return _INDEX[schluessel]


def _vorschlag(builder, modul, feld, wert):
    """The closest English display name, for the error message."""
    anzeige = _anzeige(builder, feld)
    namen = [str(anzeige.get(l, l)) for l, _ in modul.PRESETS.get(feld, [])]
    treffer = difflib.get_close_matches(str(wert), namen, n=1, cutoff=0.6)
    return ' (closest: "%s")' % treffer[0] if treffer else ""


def feldname(builder, feld):
    """The English name of a field, as the interface shows it."""
    if builder == "person":
        return str(i18n.FELDNAMEN.get(PeB.FELDNAMEN.get(feld, feld), feld))
    return str(i18n.KATEGORIEN.get(feld, feld))


def loese_label(builder, modul, feld, wert, kopie=None, streng=False):
    """(German label, error) for one value. NONE and empty stay as they are.
    Built-in first (German or English, any case), then - unless streng - a
    loaded custom entry or the copy the state carries."""
    if wert is None or wert == "" or wert == modul.NONE:
        return wert, None
    if not isinstance(wert, str):
        return None, "not a label: %r" % (wert,)
    w = " ".join(wert.split())
    if any(w == l for l, _ in modul.PRESETS.get(feld, [])):
        return w, None
    label = _index(builder, modul, feld).get(w.casefold())
    if label:
        return label, None
    if not streng:
        for e in EG.eintraege(builder, feld):
            if w.casefold() in (e["label"].casefold(), str(e["en"]).casefold()):
                return e["label"], None
        if isinstance(kopie, dict) and isinstance(kopie.get(feld), dict) and w in kopie[feld]:
            return w, None
    return None, '%s: unknown "%s"%s' % (feld, wert, _vorschlag(builder, modul, feld, w))


def _familie(wert, gruppen):
    """A family key from its key or English name, any case; None if unknown."""
    if not isinstance(wert, str):
        return None
    klein = wert.strip().casefold()
    for key in gruppen:
        if klein in (key.casefold(), str(i18n.FAMILIEN.get(key, key)).casefold()):
            return key
    return None


def _kopie_ergaenzen(builder, felder, mehrfach, kopie):
    """The prompt copies of the custom entries in use: the ones the state
    carries, plus any loaded entry it lacks. Mirrors eigeneKopie() in
    shared.mjs, but keeps what is there untouched."""
    neu = copy.deepcopy(kopie) if isinstance(kopie, dict) else {}
    paare = [(c, l) for c, l in (felder or {}).items() if isinstance(l, str)]
    for c, labels in (mehrfach or {}).items():
        paare += [(c, l) for l in labels or [] if isinstance(l, str)]
    for cat, label in paare:
        for e in EG.eintraege(builder, cat):
            if e["label"] == label and label not in (neu.get(cat) or {}):
                neu.setdefault(cat, {})[label] = e["wert"]
    return neu or None


def _text(wert, grenze, wo, p):
    if wert is None:
        return ""
    if not isinstance(wert, str):
        p.f("%s: not a text" % wo)
        return ""
    if len(wert) > grenze:
        p.h("%s: shortened to %d characters" % (wo, grenze))
        return wert[:grenze]
    return wert


# ---------------------------------------------------------- The builders ---
def _felder(abschnitt, builder, modul, erlaubt, st, kopie, p, wo, mehrfach_felder=()):
    """Checks a "felder" dict in place order; unknown fields and labels are
    errors and drop out."""
    aus = {}
    felder = st.get("felder")
    if felder is None:
        return aus
    if not isinstance(felder, dict):
        p.f('%s: "felder" is not an object' % wo)
        return aus
    # English field names ("direction", "lens") as the interface shows them -
    # only where one field goes by that name ("Colour" names several).
    namen = [feldname(builder, f).casefold() for f in erlaubt]
    alias = {feldname(builder, f).casefold(): f for f in erlaubt
             if namen.count(feldname(builder, f).casefold()) == 1}
    for feld, wert in felder.items():
        if feld not in erlaubt and str(feld).casefold() in alias:
            feld = alias[str(feld).casefold()]
        if feld not in erlaubt:
            if feld in mehrfach_felder:
                continue   # moved to "mehrfach" by the caller
            p.f('%s: no field "%s"' % (wo, feld))
            continue
        label, fehler = loese_label(builder, modul, feld, wert, kopie, p.streng)
        if fehler:
            p.f("%s %s" % (wo, fehler))
            continue
        if p.streng and abschnitt == "person" and feld == "age" and label in MINDERJAEHRIG:
            p.f("%s: age must be 18 or over" % wo)
            continue
        aus[feld] = label
    return aus


def _flach(st, erlaubt):
    """An LLM (or a hand) may write the fields straight into the section:
    {"hair": "..."} instead of {"felder": {"hair": "..."}}."""
    if isinstance(st, dict) and "felder" not in st and any(k in erlaubt for k in st):
        felder = {k: v for k, v in st.items() if k in erlaubt}
        rest = {k: v for k, v in st.items() if k not in erlaubt}
        return {"felder": felder, **rest}
    return st


def _baustein(abschnitt, st, p):
    builder, modul, gruppenfeld, gruppen = BAUSTEINE[abschnitt]
    wo = abschnitt
    st = _flach(st, set(modul.FOLGE))
    if not isinstance(st, dict):
        p.f("%s: not an object" % wo)
        return None
    kopie = None if p.streng else st.get("eigene")
    aus = {}
    for k, v in st.items():
        if k == "felder":
            aus["felder"] = _felder(abschnitt, builder, modul, set(modul.FOLGE), st, kopie, p, wo)
        elif k == "wuerfeln":
            if isinstance(v, dict):
                aus["wuerfeln"] = {c: bool(an) for c, an in v.items() if c in modul.FOLGE}
        elif k == "gruppe":
            if v == modul.ALLE or v is None:
                aus["gruppe"] = v
            elif _familie(v, gruppen):
                aus["gruppe"] = _familie(v, gruppen)
            elif not p.streng and isinstance(v, str) and v.strip():
                aus["gruppe"] = v   # a family a custom entry brought
            else:
                p.f('%s: unknown %s family "%s"' % (wo, gruppenfeld, v))
        elif k == "details":
            if p.streng:
                if v:
                    p.h("%s: free text left out (Director uses labels only)" % wo)
            else:
                aus["details"] = _text(v, TEXT_MAX, wo + " details", p)
        elif k == "requisit" and abschnitt == "pose":
            if p.streng:
                if v:
                    p.h("pose: free text requisit left out (Director uses labels only)")
            else:
                aus["requisit"] = _text(v, 200, "pose requisit", p)
        elif k == "eigene":
            if not p.streng:
                aus["eigene"] = v
        elif k.startswith("_"):
            continue   # comments and run-time markers
        elif not p.streng:
            aus[k] = v   # a key of a newer version: kept as it is
    if not p.streng:
        kopie = _kopie_ergaenzen(builder, aus.get("felder"), None, aus.get("eigene"))
        if kopie:
            aus["eigene"] = kopie
        else:
            aus.pop("eigene", None)
    return aus


def _mehrfach(st, p, wo, kopie):
    """skinFeatures - chips, any number. Also taken from "felder" where an
    LLM put them there."""
    roh = []
    m = st.get("mehrfach")
    if isinstance(m, dict) and isinstance(m.get("skinFeatures"), list):
        roh += m["skinFeatures"]
    elif m is not None and not isinstance(m, dict):
        p.f('%s: "mehrfach" is not an object' % wo)
    f = (st.get("felder") or {}).get("skinFeatures") if isinstance(st.get("felder"), dict) else None
    if isinstance(f, str):
        roh.append(f)
    elif isinstance(f, list):
        roh += f
    labels = []
    for w in roh:
        label, fehler = loese_label("person", PeB, "skinFeatures", w, kopie, p.streng)
        if fehler:
            p.f("%s %s" % (wo, fehler))
        elif label and label != PeB.NONE and label not in labels:
            labels.append(label)
    return labels


def _person_gruppe(v, p, wo):
    if not isinstance(v, dict):
        return None
    aus = {}
    for feld, wert in v.items():
        if feld not in PERSON_FAMILIEN:
            continue
        if wert == PeB.ALLE or _familie(wert, PERSON_FAMILIEN[feld]):
            aus[feld] = wert if wert == PeB.ALLE else _familie(wert, PERSON_FAMILIEN[feld])
        elif not p.streng and isinstance(wert, str):
            aus[feld] = wert
        else:
            p.h('%s: family "%s" of %s not known, shows all' % (wo, wert, feld))
    return aus


def _alter(wert, p, wo):
    """ageExact: digits only; the Director takes nothing below 18."""
    ziffern = "".join(ch for ch in str(wert or "") if ch.isdigit())
    if p.streng and ziffern and int(ziffern) < MINDESTALTER:
        p.f("%s: age must be 18 or over" % wo)
        return ""
    return str(wert or "")[:10] if not p.streng else ziffern[:3]


def _person(st, p):
    wo = "person"
    st = _flach(st, set(PERSON_FELDER) | {"skinFeatures"})
    if not isinstance(st, dict):
        p.f("person: not an object")
        return None, {}
    kopie = None if p.streng else st.get("eigene")
    erlaubt = set(PERSON_FELDER) | ({"type"} if not p.streng else set())
    aus = {}
    for k, v in st.items():
        if k == "felder":
            felder = _felder("person", "person", PeB, erlaubt - {"type"}, st, kopie, p, wo,
                             mehrfach_felder=("skinFeatures", "type"))
            if not p.streng and isinstance(v, dict) and "type" in v:
                felder["type"] = v["type"]   # older states, converted by the panel
            aus["felder"] = felder
        elif k == "mehrfach":
            aus["mehrfach"] = None   # its place; filled below, with skinFeatures from "felder"
        elif k == "texte":
            if not isinstance(v, dict):
                p.f('person: "texte" is not an object')
                continue
            texte = {}
            for t, w in v.items():
                if t == "ageExact":
                    texte[t] = _alter(w, p, "person ageExact")
                elif t in PERSON_TEXTE:
                    if p.streng:
                        if w and t in ("trigger", "referenz"):
                            p.h("person: %s from the answer ignored; the current person's %s stays" % (t, t))
                        elif w:
                            p.h("person: free text %s left out (Director uses labels only)" % t)
                        texte[t] = ""
                    else:
                        texte[t] = _text(w, TEXT_MAX, "person " + t, p)
                elif not p.streng:
                    texte[t] = w
            aus["texte"] = texte
        elif k == "gruppe":
            g = _person_gruppe(v, p, wo)
            if g is not None:
                aus["gruppe"] = g
        elif k == "eigene":
            if not p.streng:
                aus["eigene"] = v
        elif k.startswith("_"):
            continue
        elif not p.streng:
            aus[k] = v
    if "mehrfach" in st or isinstance((st.get("felder") or {}).get("skinFeatures"), (list, str)):
        m = dict(st["mehrfach"]) if isinstance(st.get("mehrfach"), dict) and not p.streng else {}
        m["skinFeatures"] = _mehrfach(st, p, wo, kopie)
        aus["mehrfach"] = m
    # The Director: clothing belongs to the Wardrobe. Taken out of the person
    # here and handed to the caller, who makes it the first outfit when the
    # file has no wardrobe of its own.
    kleidung = {}
    if p.streng and aus.get("felder"):
        for feld in list(aus["felder"]):
            if feld in PeB.OUTFIT_FELDER:
                kleidung[feld] = aus["felder"].pop(feld)
    if not p.streng:
        kopie = _kopie_ergaenzen("person", aus.get("felder"), aus.get("mehrfach"), aus.get("eigene"))
        if kopie:
            aus["eigene"] = kopie
        else:
            aus.pop("eigene", None)
    return aus, kleidung


def _outfit(o, i, p):
    wo = "wardrobe outfit %d" % (i + 1)
    o = _flach(o, set(KLEIDUNG))
    if not isinstance(o, dict):
        p.f("%s: not an object" % wo)
        return None
    kopie = None if p.streng else o.get("eigene")
    aus = {}
    for k, v in o.items():
        if k == "id":
            aus["id"] = str(v)[:40]
        elif k == "name":
            aus["name"] = _text(v, 60, wo + " name", p)
        elif k == "felder":
            aus["felder"] = _felder("person", "person", PeB, set(KLEIDUNG), o, kopie, p, wo)
        elif k == "texte":
            if not isinstance(v, dict):
                continue
            if p.streng:
                if v.get("details") or v.get("propText"):
                    p.h("%s: free text left out (Director uses labels only)" % wo)
                aus["texte"] = {"details": ""}
            else:
                aus["texte"] = {**v, "details": _text(v.get("details"), TEXT_MAX, wo + " details", p)}
                if "propText" in v:
                    aus["texte"]["propText"] = _text(v.get("propText"), TEXT_MAX, wo + " propText", p)
        elif k == "eigene":
            if not p.streng:
                aus["eigene"] = v
        elif k.startswith("_"):
            continue
        elif not p.streng:
            aus[k] = v
    aus.setdefault("id", "o%d" % (i + 1))
    aus.setdefault("name", "")
    aus.setdefault("felder", {})
    aus.setdefault("texte", {"details": ""})
    if not p.streng:
        kopie = _kopie_ergaenzen("person", aus["felder"], None, aus.get("eigene"))
        if kopie:
            aus["eigene"] = kopie
        else:
            aus.pop("eigene", None)
    return aus


def _wardrobe(st, p):
    if isinstance(st, list):
        st = {"outfits": st}
    if not isinstance(st, dict):
        p.f("wardrobe: not an object")
        return None
    aus = {}
    for k, v in st.items():
        if k == "outfits":
            if not isinstance(v, list):
                p.f('wardrobe: "outfits" is not a list')
                continue
            if len(v) > OUTFITS_MAX:
                p.h("wardrobe: only the first %d outfits" % OUTFITS_MAX)
            outfits = [_outfit(o, i, p) for i, o in enumerate(v[:OUTFITS_MAX])]
            outfits = [o for o in outfits if o is not None]
            # Ids key the rendered previews; they have to be unique.
            gesehen = set()
            for i, o in enumerate(outfits):
                if o["id"] in gesehen:
                    o["id"] = "o%d_%d" % (i + 1, len(gesehen))
                gesehen.add(o["id"])
            aus["outfits"] = outfits
        elif k == "aktiv":
            try:
                aus["aktiv"] = max(0, int(v or 0))
            except (TypeError, ValueError):
                aus["aktiv"] = 0
        elif k.startswith("_"):
            continue
        elif not p.streng or k in ("sektion", "vorschauArt"):
            aus[k] = v
    if "outfits" in aus:
        if not aus["outfits"]:
            aus["outfits"] = [{"id": "o1", "name": "", "felder": {}, "texte": {"details": ""}}]
        if "aktiv" in aus:
            aus["aktiv"] = min(aus["aktiv"], len(aus["outfits"]) - 1)
    return aus


def _location(st, p):
    """The Location node's state: a list of sets, each in a builder's shape
    and checked like one (_baustein()), with its id and name kept."""
    if isinstance(st, list):
        st = {"saetze": st}
    if not isinstance(st, dict):
        p.f("location: not an object")
        return None
    aus = {}
    for k, v in st.items():
        if k == "saetze":
            if not isinstance(v, list):
                p.f('location: "saetze" is not a list')
                continue
            if len(v) > SAETZE_MAX:
                p.h("location: only the first %d sets" % SAETZE_MAX)
            saetze = []
            for i, satz in enumerate(v[:SAETZE_MAX]):
                if not isinstance(satz, dict):
                    p.f("location set %d: not an object" % (i + 1))
                    continue
                kopf = {k2: satz[k2] for k2 in ("id", "name") if k2 in satz}
                rest = _baustein("location", {k2: w for k2, w in satz.items() if k2 not in kopf}, p)
                if rest is None:
                    continue
                if "name" in kopf:
                    kopf["name"] = _text(kopf["name"], NAME_MAX, "location name", p)
                kopf.setdefault("id", "s%d" % (i + 1))
                saetze.append({**kopf, **rest})
            gesehen = set()
            for i, satz in enumerate(saetze):
                if satz["id"] in gesehen:
                    satz["id"] = "s%d_%d" % (i + 1, len(gesehen))
                gesehen.add(satz["id"])
            aus["saetze"] = saetze or [copy.deepcopy(OB.LEERER_SATZ)]
        elif k == "aktiv":
            try:
                aus["aktiv"] = max(0, int(v or 0))
            except (TypeError, ValueError):
                aus["aktiv"] = 0
        elif k.startswith("_"):
            continue
        elif not p.streng:
            aus[k] = v
    if "saetze" in aus and "aktiv" in aus:
        aus["aktiv"] = min(aus["aktiv"], len(aus["saetze"]) - 1)
    return aus


# ------------------------------------------------------------- The series ---
def _rezept(name):
    """(German name, patch) of a built-in recipe from its German or English
    name, or None."""
    if not isinstance(name, str):
        return None
    klein = name.strip().casefold()
    for n, _b, patch in SH.REZEPTE:
        if klein in (n.casefold(), str(i18n.UI.get(n, n)).casefold()):
            return n, patch
    return None


def _liste(v, tabelle, i18n_tab, wo, p):
    """kameras/fokusse/perspektiven: None (= all) or a list of labels, German or English."""
    if v is None or v == []:
        return v
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        p.f("%s: not a list" % wo)
        return None
    namen = {}
    for label, _ in tabelle:
        namen.setdefault(label.casefold(), label)
        namen.setdefault(str(i18n_tab.get(label, label)).casefold(), label)
    aus = []
    for w in v:
        label = namen.get(str(w).strip().casefold())
        if not label:
            treffer = difflib.get_close_matches(str(w), [i18n_tab.get(l, l) for l, _ in tabelle], n=1)
            p.f('%s: unknown entry "%s"%s' % (wo, w, ' (closest: "%s")' % treffer[0] if treffer else ""))
        elif label not in aus:
            aus.append(label)
    return aus or None


def _poolfeld(cat):
    """A pool field from its key or English name ("posture", "mood")."""
    if cat in POOL_FELDER:
        return cat
    return next((x for x in POOL_FELDER
                 if str(i18n.KATEGORIEN.get(x, x)).casefold() == str(cat).casefold()), None)


def _pools(v, p):
    if not isinstance(v, dict):
        p.f('series: "pools" is not an object')
        return {}
    aus = {}
    for cat, wahl in v.items():
        c = _poolfeld(cat)
        if not c:
            p.f('series pools: no field "%s"' % cat)
            continue
        if wahl is None or (isinstance(wahl, str) and wahl.strip().casefold() in POOL_ALLE):
            aus[c] = SH.ALLE
        elif wahl is False or (isinstance(wahl, str) and wahl.strip().casefold() in POOL_AUS):
            aus[c] = SH.NONE
        elif c in POOL_FAMILIEN and isinstance(wahl, list):
            # Several families (the selects' next round narrows to those).
            familien = []
            for w in wahl:
                fam = _familie(w, POOL_FAMILIEN[c]) or (w if not p.streng and isinstance(w, str) else None)
                if fam is None:
                    p.f('series pools: "%s" is not a family of %s' % (w, i18n.KATEGORIEN.get(c, c)))
                elif fam not in familien:
                    familien.append(fam)
            if familien:
                aus[c] = familien
        elif c in POOL_FAMILIEN and _familie(wahl, POOL_FAMILIEN[c]):
            aus[c] = _familie(wahl, POOL_FAMILIEN[c])
        elif c in POOL_FAMILIEN and not p.streng and isinstance(wahl, str):
            aus[c] = wahl   # a family a custom entry brought
        else:
            p.f('series pools: "%s" is not a family of %s (all, off%s)'
                % (wahl, i18n.KATEGORIEN.get(c, c),
                   "".join(", " + str(i18n.FAMILIEN.get(g, g)) for g in POOL_FAMILIEN.get(c, {}))))
    return aus


def _bogen(v, p):
    if v in (None, False, "", "off", "none"):
        return False
    klein = str(v).strip().casefold()
    for name in SH.STIMMUNGSBOEGEN:
        if klein in (name.casefold(), str(i18n.UI.get(name, name)).casefold()):
            return name
    p.f('series: unknown mood arc "%s" (%s)' % (v, ", ".join(i18n.UI.get(n, n) for n in SH.STIMMUNGSBOEGEN)))
    return False


def _ganzzahl(v, unten, oben, wo, p):
    try:
        n = int(v)
    except (TypeError, ValueError):
        p.f("%s: not a number" % wo)
        return None
    if n < unten or (oben is not None and n > oben):
        p.h("%s: %d brought into %d..%s" % (wo, n, unten, oben if oben is not None else "∞"))
    return max(unten, n if oben is None else min(oben, n))


def _series(st, p):
    if not isinstance(st, dict):
        p.f("series: not an object")
        return None
    st = dict(st)
    # English key spellings, as the LLM prompt names them: photos, framings, ...
    for en, de in (("photos", "anzahl"), ("framings", "kameras"), ("focus", "fokusse"),
                   ("perspectives", "perspektiven"),
                   ("mood_arc", "bogen"), ("order", "reihenfolge"), ("ratio", "festesFormat"),
                   ("outfit_order", "outfitFolge"), ("gaze", "blick"), ("switches", "aktiv"),
                   ("dynamic_lens", "kameraOptik"), ("props", "requisiten"),
                   ("prop_text", "requisitText"),
                   ("set_order", "setFolge"), ("light_order", "lichtFolge"),
                   ("light_families", "lichtPool")):
        if en in st and de not in st:
            st[de] = st.pop(en)
    # A recipe goes first, and whatever the file sets next to it wins - per
    # switch and per pool, so "Lookbook" with a mood family keeps its posture.
    rezept = st.pop("recipe", None)
    if rezept is not None:
        r = _rezept(rezept)
        if r:
            patch = copy.deepcopy(r[1])
            pools = st.get("pools")
            if isinstance(pools, dict):
                pools = {**patch.get("pools", {}), **{_poolfeld(k) or k: v for k, v in pools.items()}}
            aktiv = st.get("aktiv")
            if isinstance(aktiv, dict):
                aktiv = {**patch.get("aktiv", {}), **aktiv}
            st = {**patch, **st}
            if pools is not None:
                st["pools"] = pools
            if aktiv is not None:
                st["aktiv"] = aktiv
        else:
            p.f('series: unknown recipe "%s" (%s)'
                % (rezept, ", ".join(i18n.UI.get(n, n) for n, _, _ in SH.REZEPTE)))
    aus = {}
    for k, v in st.items():
        wo = "series " + k
        if k == "anzahl":
            n = _ganzzahl(v, 1, 500, wo, p)
            if n is not None:
                aus[k] = n
        elif k == "start":
            n = _ganzzahl(v, 1, None, wo, p)
            if n is not None:
                aus[k] = n
        elif k == "serienSeed":
            n = _ganzzahl(v, 0, 0xffffffffffffffff, wo, p)
            if n is not None:
                aus[k] = n
        elif k == "groesse":
            try:
                g = int(v)
            except (TypeError, ValueError):
                g = None
            if g in SH.KANTEN:
                aus[k] = g
            else:
                p.f("%s: %r is not one of %s" % (wo, v, ", ".join(map(str, SH.KANTEN))))
        elif k == "festesFormat":
            if v in SH.RATIOS:
                aus[k] = v
            else:
                p.f("%s: %r is not one of %s" % (wo, v, ", ".join(SH.RATIOS)))
        elif k == "aktiv":
            if not isinstance(v, dict):
                p.f("%s: not an object" % wo)
                continue
            achsen = {}
            for a, an in v.items():
                a2 = ACHSEN_EN.get(str(a).casefold(), a)
                if a2 in ACHSEN:
                    achsen[a2] = bool(an)
                elif not p.streng:
                    achsen[a] = an
                else:
                    p.f('series switches: no axis "%s"' % a)
            aus[k] = achsen
        elif k == "pools":
            aus[k] = _pools(v, p)
        elif k == "kameras":
            aus[k] = _liste(v, SH.KAMERA, i18n.SHOOTING["kamera"], "series framings", p)
        elif k == "fokusse":
            aus[k] = _liste(v, SH.FOKUS, i18n.SHOOTING["fokus"], "series focus", p)
        elif k == "perspektiven":
            aus[k] = _liste(v, SH.PERSPEKTIVE, i18n.SHOOTING["perspektive"], "series perspectives", p)
        elif k == "bogen":
            aus[k] = _bogen(v, p)
        elif k == "reihenfolge":
            if v is None:
                aus[k] = None
            elif str(v).strip().casefold() in REIHENFOLGEN:
                aus[k] = REIHENFOLGEN[str(v).strip().casefold()]
            else:
                p.f('%s: "%s" is not drawn, in turn or wide to close' % (wo, v))
        elif k == "outfitFolge":
            if str(v).strip().casefold() in OUTFITFOLGEN:
                aus[k] = OUTFITFOLGEN[str(v).strip().casefold()]
            else:
                p.f('%s: "%s" is not blocks or mixed' % (wo, v))
        elif k == "setFolge":
            if str(v).strip().casefold() in OUTFITFOLGEN:
                aus[k] = OUTFITFOLGEN[str(v).strip().casefold()]
            else:
                p.f('%s: "%s" is not blocks or mixed' % (wo, v))
        elif k == "lichtFolge":
            if str(v).strip().casefold() in LICHTFOLGEN:
                aus[k] = LICHTFOLGEN[str(v).strip().casefold()]
            else:
                p.f('%s: "%s" is not per set, time of day or mixed' % (wo, v))
        elif k == "lichtPool":
            namen = v if isinstance(v, list) else [v]
            if v in (None, SH.ALLE) or (isinstance(v, str) and v.strip().casefold() in POOL_ALLE):
                aus[k] = SH.ALLE
            else:
                fam = [_familie(f, LB.LICHT_GRUPPEN) for f in namen]
                if fam and all(fam):
                    aus[k] = fam[0] if not isinstance(v, list) else fam
                else:
                    p.f("%s: unknown light family in %r" % (wo, v))
        elif k == "blick":
            b = BLICKE.get(str(v).strip().casefold()) if isinstance(v, str) else None
            if b in SH.BLICK_MODI:
                aus[k] = b
            else:
                p.f("%s: %r is not one of %s" % (wo, v, ", ".join(SH.BLICK_MODI)))
        elif k in ("kameraOptik", "requisiten"):
            aus[k] = bool(v)
        elif k == "requisitText":
            if p.streng:
                if v:
                    p.h("series: free text prop left out (Director uses labels only)")
            else:
                aus[k] = _text(v, 300, wo, p)
        elif k.startswith("_"):
            continue   # run-time markers such as "_vorschau"
        elif p.streng:
            if k in LAUF_SCHLUESSEL:
                continue
            p.h('series: "%s" left out' % k)
        else:
            aus[k] = v   # run data (takes, favourites) and keys of newer versions
    return aus


# ------------------------------------------------------------- The whole ---
def pruefe(daten, streng=False):
    """Checks a shoot file. Returns (shoot, errors, notes).

    shoot is the normalized file: German labels, unknown ones dropped, key
    order kept, so a file that passes unchanged comes back identical. errors
    lists what was rejected, notes what was adjusted. Never raises on bad
    content. streng: the Director's rules (see the module docstring).
    """
    p = Pruefung(streng)
    if isinstance(daten, str):
        try:
            daten = json.loads(daten)
        except ValueError as e:
            return None, ["not valid JSON: %s" % e], []
    if not isinstance(daten, dict):
        return None, ["a shoot file is a JSON object"], []
    fmt = daten.get("format")
    if fmt not in (None, FORMAT):
        p.h("unknown format %r, read as %s" % (fmt, FORMAT))
    aus = {}
    kleidung = {}
    for k, v in daten.items():
        if k == "format":
            aus[k] = FORMAT
        elif k in ("name", "brief"):
            aus[k] = _text(v, NAME_MAX if k == "name" else TEXT_MAX, k, p)
        elif k == "person":
            if v is not None:
                aus[k], kleidung = _person(v, p)
        elif k == "wardrobe":
            if v is not None:
                aus[k] = _wardrobe(v, p)
        elif k == "location":
            if v is not None:
                aus[k] = _location(v, p)
        elif k in BAUSTEINE:
            if v is not None:
                aus[k] = _baustein(k, v, p)
        elif k == "series":
            if v is not None:
                aus[k] = _series(v, p)
        elif k == "scene":
            aus[k] = " ".join(_text(v, SZENE_MAX, k, p).split()) if streng else _text(v, TEXT_MAX, k, p)
        elif k == "template":
            if streng:
                if v:
                    p.h("template left out (the Director keeps yours)")
            else:
                aus[k] = _text(v, TEXT_MAX, k, p)
        elif k in ("saved", "gespeichert", "version") or k.startswith("_"):
            continue   # store metadata and "_comment" keys
        elif not streng:
            aus[k] = v   # a section of a newer version: kept as it is
        else:
            p.h('"%s" left out' % k)
    aus = {k: v for k, v in aus.items() if v is not None}
    if kleidung:
        w = aus.get("wardrobe")
        if not w or not w.get("outfits") or not any(o.get("felder") for o in w["outfits"]):
            aus["wardrobe"] = {"outfits": [{"id": "o1", "name": "", "felder": kleidung,
                                            "texte": {"details": ""}}], "aktiv": 0}
            p.h("person: clothing moved into the wardrobe")
        else:
            p.h("person: clothing left out, the wardrobe dresses her")
    aus.setdefault("format", FORMAT)
    if not any(k in aus for k in list(ABSCHNITTE) + list(TEXTE)):
        p.f("nothing to set: no person, wardrobe, builder, series, scene or template")
    return aus, p.fehler, p.hinweise


# ------------------------------------------------------------------ Store ---
def ordner():
    """ComfyUI/user/krea2_shoots (or $PHOTOSHOOT_USER_DIR/krea2_shoots), created on first use."""
    from .store import benutzer_ordner
    basis = benutzer_ordner()
    if not basis:
        return None
    pfad = os.path.join(basis, ORDNER)
    os.makedirs(pfad, exist_ok=True)
    return pfad


def _name(name):
    """Safe as a file name - no "../", no separators (as store._safe_name)."""
    name = re.sub(r"[^\w\s-]", "", str(name or "").strip(), flags=re.UNICODE)
    name = re.sub(r"\s+", " ", name).strip()[:NAME_MAX]
    if not name:
        raise ValueError("unusable name")
    return name


def _pfad(name):
    verz = ordner()
    if not verz:
        raise ValueError("no ComfyUI user folder")
    return os.path.join(verz, _name(name) + ".json")


def liste():
    """Saved shoots as [{"name", "brief", "saved"}], sorted by name."""
    verz = ordner()
    aus = []
    try:
        dateien = sorted(f for f in os.listdir(verz or "") if f.endswith(".json"))
    except OSError:
        return aus
    for f in dateien:
        try:
            with open(os.path.join(verz, f), encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue   # a broken file is skipped, not fatal
        if isinstance(d, dict):
            aus.append({"name": f[:-5], "brief": str(d.get("brief") or "")[:200],
                        "saved": str(d.get("saved") or "")})
    return sorted(aus, key=lambda x: x["name"].lower())


def speichere(name, shoot):
    """Checks and writes a shoot. Returns (name, errors); raises ValueError
    when nothing in it passes."""
    sauber = _name(name)
    daten, fehler, _ = pruefe(shoot)
    if daten is None or not any(k in daten for k in list(ABSCHNITTE) + list(TEXTE)):
        raise ValueError("; ".join(fehler) or "nothing to save")
    daten = {"format": FORMAT, "name": sauber,
             **{k: v for k, v in daten.items() if k not in ("format", "name")},
             "saved": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(_pfad(sauber), "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1)
    return sauber, fehler


def lade(name):
    """(shoot, errors, notes) of a saved shoot, checked as on import."""
    with open(_pfad(name), encoding="utf-8") as fh:
        return pruefe(json.load(fh))


def loesche(name):
    pfad = _pfad(name)
    if not os.path.isfile(pfad):
        raise FileNotFoundError(_name(name))
    os.remove(pfad)
