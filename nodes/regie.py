"""
The Director - one sentence becomes a whole shoot, through any chat LLM.

Served at /krea2/director/llm_prompt?brief=... as plain text: a prompt that
lists every built-in label per builder and field (English display names,
grouped by family) and the shoot-file format (shoot_datei.py), and asks the
LLM to answer with a shoot file that chooses ONLY from those labels. The
answer comes back through /krea2/director/import, which runs it through
shoot_datei.pruefe(streng=True): built-in labels only, English or German, no
free text but the scene, nothing below 18. So every wording that reaches the
prompt is one the render tests already saw - the LLM plans, it does not write.

The "photo" variant asks a vision chat to reverse-engineer a reference photo
into the same file. The photo stays in the chat: only the labels come back,
no pixels enter the pipeline (img2img carried neither identity nor framing,
docs/measurements.md).

entwurf() is the offline fallback: the brief's words matched against the
English labels, for when there is no LLM at hand.

Built from the live presets on every request, like llm_prompt.py, so it
cannot fall behind when an entry is added.
"""

import json
import re

from . import expression_builder as EB
from . import i18n
from . import lighting_builder as LB
from . import person_builder as PeB
from . import pose_builder as PB
from . import shooting as SH
from . import shoot_datei as SD
from . import style_builder as SB

# Face fields: the render tests found that more than a handful make the face
# generic (GESICHT_HINWEIS_AB in person_builder.py).
GESICHT_MAX = 5

# The worked example in the prompt, in English display labels. The smoke test
# checks that it passes the Director's own import without a single error.
BEISPIEL = {
    "format": SD.FORMAT,
    "name": "Rainy café",
    "brief": "a rainy afternoon in a Paris café, quiet and a little melancholic",
    "person": {
        "felder": {"gender": "Woman", "age": "Early 30s", "hair": "Long waves",
                   "hairColor": "Auburn", "eyes": "Green", "skinTone": "Fair",
                   "figure": "Slim"},
        "mehrfach": {"skinFeatures": ["Freckles"]},
    },
    "wardrobe": {"outfits": [
        {"name": "Café", "felder": {"top": "Off-shoulder crop", "topColor": "Cream",
                                    "bottom": "Wide-leg trousers", "bottomColor": "Black",
                                    "shoes": "Block heel pumps", "shoesColor": "Black",
                                    "jewellery": "Hoops"}},
    ]},
    "lighting": {"felder": {"setup": "Overcast daylight", "richtung": "Subtle fill light",
                            "atmosphaere": "Warm film glow"}},
    "style": {"felder": {"look": "Kodak Portra", "genre": "Editorial",
                         "optik": "85mm f/1.4", "finish": "Fine grain"}},
    "series": {"recipe": "Editorial", "photos": 12,
               "framings": ["Portrait", "Medium shot", "Full body"],
               "pools": {"posture": "sitting", "mood": "introspective"},
               "mood_arc": False},
    "scene": "a small Paris café by a rain-streaked window, marble tables, espresso cups, grey afternoon light",
}

KOPF = {
    "brief": """You are the director of a portrait photo shoot in "Photoshoot", a ComfyUI
node pack that builds text prompts for photographic portraits (image model:
Krea 2). From the brief at the end you plan the whole shoot: who the person is,
what she wears (one to four outfits), the light, the look, the location, and
how the series of photos moves through framings, postures and moods.""",
    "photo": """You are the director of a portrait photo shoot in "Photoshoot", a ComfyUI
node pack that builds text prompts for photographic portraits (image model:
Krea 2). Attached is a reference photo. Reverse-engineer it into a shoot file:
the person as she looks (hair, colouring, figure, a few features), what she
wears, the light, the colour treatment, the lens and the location - and a
series plan around the framing and mood of the photo. Describe only what you
can see; leave out what the photo does not show.""",
}

REGELN = """
You do not write prompt text. You choose from fixed lists: every entry below
is a wording that was tested on the image model. Use the names exactly as
listed; anything that is not listed is rejected. Leave a field out rather
than invent a value. Your answer is loaded as it is, so it must be valid JSON.

OUTPUT
Only the JSON object - nothing before or after it, no code fences, no
comments. This example shows the shape; take the values from the lists below:

%(beispiel)s

RULES
- "person": always "gender" and "age", then the few features that make her
  who she is - hair and hair colour, eyes, skin tone, figure. At most %(gesicht)d of
  the face fields (%(gesichtsfelder)s):
  more face detail made the face generic in the render tests.
- "wardrobe": one to four outfits, each with a short "name" and only the
  clothing and accessory fields. A colour field takes a colour of its list.
  With several outfits the series changes costume in blocks.
- "series": framing, posture and expression are drawn per photo. Steer them
  with "framings" (the framings to use), "pools" (a posture family and a mood
  family, "all" or "off") or a mood arc ("mood_arc"). A "recipe" sets all of
  that for a kind of shoot; whatever you set next to it wins.
- Leave out "pose" and "expression": the series draws them per photo.
- "scene" is the only free text: English, 8 to 25 words, the place as seen -
  surfaces, objects, time of day. No person, no camera or light words (they
  have their own fields).
- Nothing about age below 18, nothing that would describe a minor.
"""

FUSS = {
    "brief": """
BRIEF
%s
""",
    "photo": """
REFERENCE
The attached photo.%s
""",
}
FUSS_LEER = {
    "brief": "(Replace this line with one sentence, e.g. \"a rainy afternoon in a Paris café, "
             "melancholic, in black and white\".)",
    "photo": "",
}


def _en(builder, feld, label):
    return str(i18n.tabelle().get(builder, {}).get(feld, {}).get(label, label))


def _gleich_wie(modul, feld, gesehen):
    """The field whose list this one repeats (the colour lists), or None."""
    liste = modul.PRESETS[feld]
    for anderes in gesehen:
        if modul.PRESETS[anderes] == liste:
            return anderes
    return None


def _zeilen(builder, modul, felder, familien, beschreibung=None):
    teile = []
    gesehen = []
    for feld in felder:
        name = SD.feldname(builder, feld)
        labels = [l for l, _ in modul.PRESETS[feld]
                  if not (builder == "person" and feld == "age" and l in SD.MINDERJAEHRIG)]
        kopf = '- "%s" (%s)' % (feld, name)
        if beschreibung and feld in beschreibung:
            kopf += ", " + beschreibung[feld]
        gleich = _gleich_wie(modul, feld, gesehen)
        gesehen.append(feld)
        if gleich:
            teile.append('%s: the same list as "%s"' % (kopf, gleich))
            continue
        if feld in familien:
            teile.append(kopf + ", by family:")
            drin = set()
            for fam, fam_labels in familien[feld].items():
                eintraege = [l for l in fam_labels if l in labels]
                drin.update(eintraege)
                if eintraege:
                    teile.append("    %s: %s" % (i18n.FAMILIEN.get(fam, fam),
                                                "; ".join(_en(builder, feld, l) for l in eintraege)))
            rest = [l for l in labels if l not in drin]
            if rest:
                teile.append("    other: " + "; ".join(_en(builder, feld, l) for l in rest))
        else:
            teile.append(kopf + ": " + "; ".join(_en(builder, feld, l) for l in labels))
    return teile


def _serie():
    kam = i18n.SHOOTING["kamera"]
    fok = i18n.SHOOTING["fokus"]
    rezepte = ["    %s: %s" % (i18n.UI.get(n, n), i18n.UI.get(b, b)) for n, b, _ in SH.REZEPTE]
    boegen = ["    %s: %s" % (i18n.UI.get(n, n), " -> ".join(
        "/".join(_en("ausdruck", "stimmung", l) for l in stufe) for stufe in stufen))
        for n, stufen in SH.STIMMUNGSBOEGEN.items()]
    return [
        '\n== "series" - the plan of the photos',
        '- "recipe" (optional), one of:', *rezepte,
        '- "photos": the number of photos, 4 to 24',
        '- "framings": a list from: ' + "; ".join(kam[l] for l, _ in SH.KAMERA),
        '- "focus" (optional): a list from: ' + "; ".join(fok[l] for l, _ in SH.FOKUS),
        '- "perspectives" (optional, with "switches": {"perspective": true}): a list from: '
        + "; ".join(i18n.SHOOTING["perspektive"][l] for l, _ in SH.PERSPEKTIVE)
        + " - selfies; the Selfie recipe sets them",
        '- "pools": {"posture": <family>, "mood": <family>}; "all" or "off" also work',
        "    posture families: " + "; ".join(i18n.FAMILIEN.get(f, f) for f in PB.HALTUNG_GRUPPEN),
        "    mood families: " + "; ".join(i18n.FAMILIEN.get(f, f) for f in EB.STIMMUNG_GRUPPEN),
        '- "mood_arc" (optional, instead of a mood family): false or one of',
        *boegen,
        '- "order" (optional): "drawn", "in turn" or "wide to close"',
        '- "ratio" (optional, with "switches": {"ratio": false}): one of ' + ", ".join(SH.RATIOS),
        '- "gaze" (optional): "mixed", "at the camera", "mostly camera" or "away"',
        '- "light_order" (optional, with "switches": {"light": true}): "per set", "time of day" or "mixed"',
        '- "light_families" (optional, with "switches": {"light": true}): "all" or a lighting family ('
        + "; ".join(i18n.FAMILIEN.get(f, f) for f in LB.LICHT_GRUPPEN) + ")",
        '- "switches" (optional): {"camera", "pose", "expression", "ratio", "focus",'
        ' "noise", "outfit", "set", "light", "perspective": true or false} - false keeps that axis still'
        ' (light and perspective are off unless true)',
    ]


def erzeuge(brief="", art="brief"):
    """The whole prompt as text. art: "brief" or "photo"."""
    art = "photo" if art == "photo" else "brief"
    beispiel = json.dumps(BEISPIEL, ensure_ascii=False, indent=1)
    teile = [KOPF[art], REGELN % {
        "beispiel": beispiel, "gesicht": GESICHT_MAX,
        "gesichtsfelder": ", ".join(SD.feldname("person", f) for f in PeB.GESICHTSFELDER)}]
    teile.append("FIELDS")
    person = [f for f in SD.PERSON_FELDER if f not in PeB.OUTFIT_FELDER] + ["skinFeatures"]
    teile.append('\n== "person" - in "felder"; "skinFeatures" is a list in "mehrfach"')
    teile += _zeilen("person", PeB, person, {})
    teile.append('\n== "wardrobe" - each outfit\'s "felder"')
    teile += _zeilen("person", PeB, SD.KLEIDUNG, SD.PERSON_FAMILIEN)
    for abschnitt, text in (("lighting", "the light, the same for the whole series"),
                            ("style", "the look: colour treatment, genre, lens, finish")):
        builder, modul, gruppenfeld, gruppen = SD.BAUSTEINE[abschnitt]
        teile.append('\n== "%s" - in "felder": %s' % (abschnitt, text))
        teile += _zeilen(builder, modul, list(modul.FOLGE), {gruppenfeld: gruppen})
    teile += _serie()
    brief = " ".join(str(brief or "").split())[:1000]
    teile.append(FUSS[art] % ((" " + brief) if art == "photo" and brief
                              else (brief or FUSS_LEER[art])))
    return "\n".join(teile)


# ------------------------------------------------------------------ Import ---
_ZAUN = re.compile(r"^```[a-zA-Z]*\s*|\s*```\s*$")


def lies_antwort(antwort):
    """The JSON object out of a chat answer: code fences and any text around
    it are dropped. Returns the parsed object; raises ValueError."""
    if isinstance(antwort, dict):
        return antwort
    text = str(antwort or "").strip()
    text = _ZAUN.sub("", text).strip()
    anfang, ende = text.find("{"), text.rfind("}")
    if anfang < 0 or ende <= anfang:
        raise ValueError("no JSON object in the answer")
    try:
        return json.loads(text[anfang:ende + 1])
    except ValueError as e:
        raise ValueError("the answer is not valid JSON (%s)" % e)


def importiere(antwort):
    """{"shoot", "errors", "notes"} for a chat answer, checked by the
    Director's rules. shoot is None when nothing could be read."""
    try:
        daten = lies_antwort(antwort)
    except ValueError as e:
        return {"shoot": None, "errors": [str(e)], "notes": []}
    shoot, fehler, hinweise = SD.pruefe(daten, streng=True)
    return {"shoot": shoot, "errors": fehler, "notes": hinweise}


# ----------------------------------------------------------- Offline draft ---
_WORT = re.compile(r"[a-z0-9&+/°.'-]+")

# Fields whose one-word labels are adjectives ("Long", "Straight", "Black"):
# such a label only counts right before one of these nouns - "long legs",
# "black hair", "green eyes". Without that one "long" filled six fields.
NOMEN = {
    "skinTone": ("skin",), "complexion": ("skin", "complexion"), "height": ("height",),
    "figure": ("figure", "build", "body"), "bust": ("bust", "chest"),
    "shoulders": ("shoulders",), "waist": ("waist",), "belly": ("belly", "stomach"),
    "hips": ("hips",), "legs": ("legs",), "hairColor": ("hair",),
    "hairEffect": ("hair", "highlights"), "faceShape": ("face",),
    "cheekbones": ("cheekbones",), "nose": ("nose",), "chin": ("chin",),
    "jawline": ("jaw", "jawline"), "eyeShape": ("eyes",), "browShape": ("brows", "eyebrows"),
    "lipShape": ("lips",), "eyes": ("eyes",), "lashes": ("lashes",), "eyeliner": ("eyeliner",),
    "eyeshadow": ("eyeshadow",), "blush": ("blush",), "lipColor": ("lips", "lipstick"),
    "lipFinish": ("lips", "lipstick"), "makeup": ("makeup", "make-up"),
    "nailLength": ("nails",), "nailColor": ("nails",), "bottomMaterial": (),
    "hosieryColor": (), "topColor": (), "bottomColor": (), "shoesColor": (),
}


def _woerter(text):
    return _WORT.findall(str(text or "").casefold().replace("black and white", "black & white"))


def _stellen(woerter, label_en):
    """Every position where the English label stands as a run of whole words."""
    such = _woerter(label_en)
    if not such or (len(such) == 1 and len(such[0]) < 3):
        return []
    return [i for i in range(len(woerter) - len(such) + 1) if woerter[i:i + len(such)] == such]


def _kandidaten(woerter, builder, modul, feld, rang):
    """(words, rank, position, field, label) for every label of the field in the brief."""
    aus = []
    for label, _ in modul.PRESETS[feld]:
        if builder == "person" and feld == "age" and label in SD.MINDERJAEHRIG:
            continue
        n = len(_woerter(_en(builder, feld, label)))
        for pos in _stellen(woerter, _en(builder, feld, label)):
            if n == 1 and feld in NOMEN:
                if pos + 1 >= len(woerter) or woerter[pos + 1] not in NOMEN[feld]:
                    continue
            aus.append((n, rang, pos, (builder, feld), label))
    return aus


def entwurf(brief):
    """A shoot from the brief's words alone - no LLM. The English labels found
    in the brief, longest first, each word used once; a colour word right before
    a garment colours that garment. Crude, but label-only like the Director,
    and checked by the same import."""
    woerter = _woerter(brief)
    felder = ([("person", PeB, f) for f in SD.KLEIDUNG]
              + [("person", PeB, f) for f in SD.PERSON_FELDER if f not in PeB.OUTFIT_FELDER]
              + [("lighting", LB, f) for f in LB.FOLGE] + [("style", SB, f) for f in SB.FOLGE])
    kandidaten = []
    for rang, (builder, modul, feld) in enumerate(felder):
        kandidaten += _kandidaten(woerter, builder, modul, feld, rang)
    kandidaten.sort(key=lambda k: (-k[0], k[1], k[2]))
    belegt, gewaehlt = set(), {}
    for n, _, pos, ziel, label in kandidaten:
        stellen = set(range(pos, pos + n))
        if ziel in gewaehlt or stellen & belegt:
            continue
        gewaehlt[ziel] = (label, pos)
        belegt |= stellen
    person, outfit, bausteine = {}, {}, {}
    for (builder, feld), (label, pos) in gewaehlt.items():
        if builder != "person":
            bausteine.setdefault(builder, {})[feld] = label
        elif feld not in PeB.OUTFIT_FELDER:
            person[feld] = label
        else:
            outfit[feld] = label
            farbfeld = feld + "Color"
            for n in (2, 1):
                if farbfeld not in PeB.PRESETS or pos - n < 0 or set(range(pos - n, pos)) & belegt:
                    continue
                davor = " ".join(woerter[pos - n:pos])
                farbe = next((l for l, _ in PeB.PRESETS[farbfeld]
                              if _en("person", farbfeld, l).casefold() == davor), None)
                if farbe:
                    outfit[farbfeld] = farbe
                    belegt |= set(range(pos - n, pos))
                    break
    name = " ".join(str(brief or "").split())
    shoot = {"format": SD.FORMAT, "name": name[:40].rsplit(" ", 1)[0] if len(name) > 40 else name,
             "brief": name}
    if person:
        shoot["person"] = {"felder": person}
    if outfit:
        shoot["wardrobe"] = {"outfits": [{"name": "", "felder": outfit}]}
    # "black and white" names no look of its own, but a family: its first look.
    sw = SB.LOOK_GRUPPEN.get("schwarzweiss")
    if sw and "look" not in bausteine.get("style", {}) and \
            _stellen(woerter, str(i18n.FAMILIEN.get("schwarzweiss", ""))):
        bausteine.setdefault("style", {})["look"] = sw[0]
    for abschnitt in ("lighting", "style"):
        builder = SD.BAUSTEINE[abschnitt][0]
        if bausteine.get(builder):
            shoot[abschnitt] = {"felder": bausteine[builder]}
    serie = {}
    for n, _, _ in SH.REZEPTE:
        if _stellen(woerter, str(i18n.UI.get(n, n))):
            serie["recipe"] = n
    for n in SH.STIMMUNGSBOEGEN:
        if _stellen(woerter, str(i18n.UI.get(n, n))):
            serie["bogen"] = n
    pools = {}
    for feld, gruppen in SD.POOL_FAMILIEN.items():
        for fam in gruppen:
            if _stellen(woerter, str(i18n.FAMILIEN.get(fam, fam))):
                pools[feld] = fam
    if pools:
        serie["pools"] = pools
    kameras = [l for l, _ in SH.KAMERA if _stellen(woerter, i18n.SHOOTING["kamera"][l])]
    if kameras:
        serie["kameras"] = kameras
    perspektiven = [l for l, _ in SH.PERSPEKTIVE if _stellen(woerter, i18n.SHOOTING["perspektive"][l])]
    if perspektiven:
        serie["perspektiven"] = perspektiven
        serie.setdefault("aktiv", {})["perspektive"] = True
    for such, modus in (("mostly camera", "meist_kamera"), ("at the camera", "kamera"),
                        ("into the camera", "kamera"), ("eye contact", "kamera"),
                        ("looking away", "abgewandt")):
        if _stellen(woerter, such):
            serie["blick"] = modus
            break
    zahl = re.search(r"\b(\d{1,3})\s+(?:photos|pictures|images|shots|frames)\b", name.casefold())
    if zahl:
        serie["anzahl"] = int(zahl.group(1))
    if serie:
        shoot["series"] = serie
    return importiere(shoot)
