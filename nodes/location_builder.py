"""
Location - where the photo is taken: the place, the time of day, the weather
and the season, for one set or several.

Returns two STRINGs. "szene" is the open set's text: wire it into the "szene" /
"scene" input of "build prompt", where it replaces {scene} or {szene}. "ort_data"
carries every set of the node as JSON for the Series (Photoshoot), which changes
the sets over the series the way it changes outfits - in blocks or mixed - and
shortens a set for the close framings.

Why the lists are nearly empty: a wording enters PRESETS only after a render
test (docs/GUIDE.md, docs/measurements.md). The scene is free text today and
the seed holds only about a fifth of a setting together, so a place that does
not come out as written would make every series wrong in the same way. The
candidates wait in tools/wortlabor/orte.json; until they have passed, a set
is the free text under Details, a custom entry (nodes/eigene.py, builder
"location"), or the one place that has been rendered hundreds of times - the
example workflow's loft.

The families say more than where a place sits in the list: studio and
interior are indoors, urban and nature outdoors. That decides which fields
apply (weather and season only outdoors) and, in the Series, which light fits
the set (no sun in a studio, no softbox in a forest).
"""

import json
import random

from . import eigene

PRESETS = {
    # Places (17 render-tested wordings across the four families; Sonniges Loft
    # is the example workflow's scene, the remaining 16 passed orte.json
    # groups A-D).
    "ort": [
        ("Sonniges Loft", "a sunlit loft with tall windows, wooden floor, plants in the corner"),
        ("Weißer Hintergrund", "a photo studio with a seamless white paper backdrop curving into the floor"),
        ("Grauer Hintergrund", "a photo studio with a mottled grey hand-painted canvas backdrop"),
        ("Farbiger Hintergrund", "a photo studio with a saturated terracotta orange paper backdrop and matching floor"),
        ("Tageslichtstudio", "a daylight photo studio with tall industrial windows, white brick walls and a grey concrete floor"),
        ("Altstadtgasse", "a gently curving old town cobblestone lane seen at an angle, stepped pastel plaster facades, flower boxes and a corner lantern"),
        ("Großstadtstraße", "a city sidewalk in front of an angled corner storefront, glass office buildings and blurred street life receding diagonally"),
        ("Dachterrasse", "a rooftop terrace with a metal railing, the city skyline spread out behind"),
        ("Betonarchitektur", "a brutalist concrete plaza with massive raw concrete walls and wide steps"),
        ("Wald", "a winding forest path among gnarled old trees at uneven depths, mossy roots, ferns and dappled undergrowth"),
        ("Strand", "a curving sandy coastline seen at an angle, driftwood and dune grass on one side, waves breaking diagonally along the shore"),
        ("Blumenwiese", "a rolling hillside meadow of tall grass, poppies and daisies, a crooked wooden fence and scattered bushes at an angle"),
        ("Bergpanorama", "an alpine meadow on a mountainside, rocky peaks rising in the background"),
        ("Café", "a small café interior with marble tables, bentwood chairs and a wooden counter"),
        ("Altbauwohnung", "a period apartment living room, ornate plaster moulding, parquet floor, a velvet sofa"),
        ("Hotelzimmer", "a hotel room with a large bed in white linen, a bedside lamp and heavy curtains"),
        ("Bibliothek", "a quiet corner of an old library with an angled wooden bookcase, a rolling ladder on one side and a reading table"),
    ],
    # Time of day, weather and season (render-tested in orte.json groups E-G).
    "tageszeit": [
        ("Morgen", "morning, fresh pale daylight"),
        ("Mittag", "at midday under a high sun, short shadows"),
        ("Goldene Stunde", "late afternoon, warm low sunlight and long shadows"),
        ("Blaue Stunde", "at dusk, a blue twilight sky and lit windows"),
        ("Nacht", "late at night, darkness lit only by artificial lights"),
    ],
    "wetter": [
        ("Klar", "a cloudless sunny day"),
        ("Bewölkt", "a cloudy day, thick soft clouds covering the sky"),
        ("Regen", "a rainy day, puddles reflecting the surroundings, streaks of falling rain"),
        ("Nebel", "in thick fog, the background fading into soft grey mist"),
        ("Schnee", "a snowy scene, fresh white snow on every surface, snowflakes in the air"),
    ],
    "jahreszeit": [
        ("Frühling", "in spring, fresh green leaves and blossoming branches"),
        ("Sommer", "in high summer, lush deep green foliage, warm dry air"),
        ("Herbst", "autumn foliage in gold and rust, leaves drifting down"),
        ("Winter", "a winter landscape, everything under a layer of snow"),
    ],
}

# The four families of places; also tells the Series whether a set is indoors
# or outdoors (coupled to lighting setups and weather/season visibility).
ORT_GRUPPEN = {
    "studio": ("Weißer Hintergrund", "Grauer Hintergrund", "Farbiger Hintergrund", "Tageslichtstudio"),
    "stadt": ("Altstadtgasse", "Großstadtstraße", "Dachterrasse", "Betonarchitektur"),
    "natur": ("Wald", "Strand", "Blumenwiese", "Bergpanorama"),
    "innen": ("Sonniges Loft", "Café", "Altbauwohnung", "Hotelzimmer", "Bibliothek"),
}

# Outdoor families. The others (studio, interior) are indoors; a set of no
# known family is neither, and nothing is coupled to it.
DRAUSSEN = ("stadt", "natur")
DRINNEN = tuple(f for f in ORT_GRUPPEN if f not in DRAUSSEN)

# Fields that only mean something outdoors: rain or snow in a studio is a
# contradiction the model resolves by painting a window or dropping the set.
# Dropped for an indoor set, in the prompt and in the panel's preview.
NUR_DRAUSSEN = ("wetter", "jahreszeit")

FOLGE = ("ort", "tageszeit", "wetter", "jahreszeit")
NONE = "—"
ALLE = "alle"

LEERER_SATZ = {"id": "s1", "name": "",
               "felder": {cat: NONE for cat in FOLGE},
               "wuerfeln": {}, "gruppe": ALLE, "details": ""}

# Several sets as tabs, like the Wardrobe's outfits; "aktiv" is the open one,
# which the "szene" output carries.
DEFAULT_STATE = {"saetze": [dict(LEERER_SATZ)], "aktiv": 0}


def _val(cat, label, kopie=None):
    if not label or label == NONE:
        return ""
    for lbl, wert in PRESETS[cat]:
        if lbl == label:
            return wert
    # A custom entry (eigene.py), else the label as before.
    return eigene.wert("location", cat, label, kopie) or label


def _familie_eigen(name):
    """The family a custom entry names, as /krea2/presets files it (api.py
    _familie()): a family key or its English display name, any case; any
    other name is a family of its own and not one of the four."""
    name = (name or "").strip().casefold()
    if not name:
        return None
    from . import i18n
    for key in ORT_GRUPPEN:
        if name in (key.casefold(), str(i18n.FAMILIEN.get(key, "")).casefold()):
            return key
    return None


def familie_von(label):
    """The family of a place label: built-in first, then a custom entry's."""
    for fam, labels in ORT_GRUPPEN.items():
        if label in labels:
            return fam
    for e in eigene.eintraege("location", "ort"):
        if e["label"] == label:
            return _familie_eigen(e.get("gruppe"))
    return None


def familie(satz):
    """The family of a set: that of its place when one is chosen (and not
    rolled), else the family chip of the set, else None. The JS side
    (ortSaetze() in shared.mjs) reads the same from the node's state."""
    satz = satz if isinstance(satz, dict) else {}
    ort = (satz.get("felder") or {}).get("ort")
    if ort and ort != NONE and not (satz.get("wuerfeln") or {}).get("ort"):
        f = familie_von(ort)
        if f:
            return f
    g = satz.get("gruppe")
    return g if g in ORT_GRUPPEN else None


def draussen(satz):
    """True outdoors, False indoors, None when the set names no family."""
    f = familie(satz)
    return True if f in DRAUSSEN else False if f in DRINNEN else None


def _pool(cat, gruppe):
    """What a die on this field draws from: built-in labels plus custom
    entries marked for the dice; for the place, only the set's family when one
    is chosen. May be empty - the lists wait for the render test."""
    alle = [lbl for lbl, _ in PRESETS[cat]] + eigene.wuerfelbar("location", cat)
    if cat == "ort" and gruppe in ORT_GRUPPEN:
        return [l for l in alle if familie_von(l) == gruppe]
    return alle


def _ziehe(cat, seed, index, gruppe):
    labels = _pool(cat, gruppe)
    if not labels:
        return None
    # The set's index in the key, so two sets rolling the same field do not
    # land on the same entry.
    return random.Random("%d-%d-%s" % (seed, index, cat)).choice(labels)


def werte_von(satz, seed=0, index=0):
    """The prompt values of one set, field by field, with its dice rolled and
    the outdoor-only fields dropped for an indoor set."""
    felder = satz.get("felder") or {}
    wuerfeln = satz.get("wuerfeln") or {}
    gruppe = satz.get("gruppe") or ALLE
    innen = draussen(satz) is False
    werte = {}
    for cat in FOLGE:
        if innen and cat in NUR_DRAUSSEN:
            werte[cat] = ""
            continue
        label = _ziehe(cat, seed, index, gruppe) if wuerfeln.get(cat) else felder.get(cat)
        werte[cat] = _val(cat, label, satz.get("eigene"))
    return werte


def _teile(werte, details):
    teile = [werte[cat] for cat in FOLGE if werte.get(cat)]
    frei = (details or "").strip().rstrip(",;. \t\r\n")
    if frei:
        teile.append(frei)
    return teile


def compose_location(werte, details=""):
    return ", ".join(_teile(werte, details))


def kurzform(werte, details=""):
    """The set as a close framing sees it: what is behind the head.

    No wording for this has been render-tested, so the rule only shortens:
    the first clause of each part - the place, the time of day, the weather,
    the season, the free text. "a sunlit loft with tall windows, wooden floor,
    plants in the corner" becomes "a sunlit loft with tall windows"; the floor
    and the corner are out of frame in a portrait, and naming them pulled the
    camera back the way a full pose did on the close framings (NAH_SICHTBAR in
    shooting.py)."""
    return ", ".join(t.split(",")[0].strip() for t in _teile(werte, details) if t.split(",")[0].strip())


def saetze_von(state, seed=0):
    """Every set of a node state as the Series reads it: name, full text,
    short form, family and whether it is outdoors."""
    state = state if isinstance(state, dict) else {}
    saetze = state.get("saetze")
    if not isinstance(saetze, list) or not saetze:
        saetze = [dict(LEERER_SATZ)]
    raus = []
    for i, satz in enumerate(saetze):
        satz = satz if isinstance(satz, dict) else {}
        werte = werte_von(satz, seed, i)
        raus.append({
            "name": str(satz.get("name") or "").strip(),
            "text": compose_location(werte, satz.get("details", "")),
            "kurz": kurzform(werte, satz.get("details", "")),
            "familie": familie(satz),
            "draussen": draussen(satz),
        })
    return raus


def saetze_lesen(ort_data):
    """The sets out of an ort_data string, as the Series gets them; [] for
    nothing or something unreadable."""
    if not ort_data:
        return []
    try:
        d = json.loads(ort_data) if isinstance(ort_data, str) else ort_data
    except (TypeError, ValueError):
        print("[Photoshoot] ort_data unreadable, no sets.")
        return []
    liste = d.get("saetze") if isinstance(d, dict) else None
    if not isinstance(liste, list):
        return []
    raus = []
    for s in liste:
        if not isinstance(s, dict):
            continue
        d_ = s.get("draussen")
        raus.append({"name": str(s.get("name") or ""), "text": str(s.get("text") or ""),
                     "kurz": str(s.get("kurz") or ""), "familie": s.get("familie"),
                     "draussen": d_ if d_ in (True, False) else None})
    return raus


class Krea2LocationBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True}),
            },
            "hidden": {
                "LocationState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("szene", "ort_data")
    OUTPUT_TOOLTIPS = (
        "Complete English location, time-of-day, weather and season prompt for the open set.",
        "JSON list of all Location sets for Photoshoot – Series (scaled per framing & coupled with lighting).",
    )
    SEARCH_ALIASES = ["location", "scene", "ort", "szene", "background", "setting", "weather", "wetter"]
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Setzt den Schauplatz zusammen: Ort, Tageszeit, Wetter, Jahreszeit, "
                   "ein Set oder mehrere als Reiter. 'szene' ist das offene Set, an den "
                   "Eingang 'szene' von 'Photoshoot Prompt bauen'; 'ort_data' an die "
                   "Serie, die die Sets über die Serie wechselt.")

    def build(self, seed=0, LocationState=None):
        try:
            state = json.loads(LocationState) if LocationState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Location] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)
        if not isinstance(state, dict):
            state = dict(DEFAULT_STATE)
        saetze = saetze_von(state, int(seed or 0))
        try:
            aktiv = int(state.get("aktiv") or 0)
        except (TypeError, ValueError):
            aktiv = 0
        aktiv = min(max(0, aktiv), len(saetze) - 1)
        daten = {"saetze": saetze, "aktiv": aktiv}
        return (saetze[aktiv]["text"], json.dumps(daten, ensure_ascii=False))


NODE_CLASS_MAPPINGS = {"Krea2LocationBuilder": Krea2LocationBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2LocationBuilder": "Photoshoot – Location"}
