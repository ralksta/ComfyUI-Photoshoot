"""
A ready prompt for an LLM that writes custom entries (eigene.py) for you.

Served at /krea2/custom/llm_prompt as plain text. It is built from the live
presets on every request - every field with its English name, its families,
three built-in examples as a model for the wording, and the names of all
built-in entries so the LLM does not suggest them again - so it cannot fall
behind when a field or preset is added. The user pastes it into any chat
model, writes what they want at the end, and saves the answer as a .json file.

The writing rules at the top are what the render tests found (docs/GUIDE.md):
concrete visible features, short, no quality words, no film names on their own.
"""

from . import eigene
from . import expression_builder as EB
from . import i18n
from . import lighting_builder as LB
from . import person_builder as PeB
from . import pose_builder as PB
from . import style_builder as SB

# How a person field's text lands in the sentence, where it is not simply
# "<text>". Mirrors compose_person(); the examples show the rest.
SATZ = {
    "skinTone": 'becomes "<text> skin"',
    "hair": 'must contain {c} where the hair colour goes: "long wavy {c} hair"',
    "hairColor": "a hair colour; it replaces {c} in the hairstyle",
    "faceShape": 'becomes "<text> face"',
    "eyeShape": 'stands before the eye colour: "<text> green eyes"',
    "eyes": 'an eye colour; becomes "<text> eyes"',
    "lipColor": 'a colour; becomes "<finish> <text> lipstick"',
    "nailColor": 'a colour; becomes "<text> nails"',
    "top": 'one garment, no article, no colour: written as "wearing a <colour> <text>"',
    "bottom": 'one garment, no article, no colour: written as "with a <colour> <material> <text>"',
    "bottomMaterial": "a fabric or material; stands between colour and cut",
    "shoes": 'plural, no article, no colour: "wearing <colour> <text>"',
    "hosiery": 'no article, no colour: "wearing <colour> <text>"',
    "jewellery": 'with its article where singular: "wearing <text>"',
    "eyewear": 'with its article: "wearing <text>"',
    "headwear": 'with its article: "wearing <text>"',
    "skinFeatures": "a visible skin feature; several can be on at the same time",
}
FARBE = 'a colour word ("petrol blue")'
HEX = 'add "hex" for its swatch in the palette'

# builder in the file -> (module, display name, field with families, families)
BUILDER = [
    ("person", PeB, "Person and Wardrobe nodes: the person's body, face, make-up, clothing and accessories",
     {"shoes": PeB.SCHUH_GRUPPEN, "top": PeB.OBERTEIL_GRUPPEN,
      "bottom": PeB.UNTERTEIL_GRUPPEN, "headwear": PeB.KOPF_GRUPPEN}),
    ("pose", PB, "Pose node: posture, placement in the room, body, arms, legs, tension",
     {"haltung": PB.HALTUNG_GRUPPEN}),
    ("expression", EB, "Expression node: mood, eyes, gaze, mouth, brows, head",
     {"stimmung": EB.STIMMUNG_GRUPPEN}),
    ("lighting", LB, "Lighting node: light setup, direction, atmosphere",
     {"setup": LB.LICHT_GRUPPEN}),
    ("style", SB, "Style node: look (colour treatment), genre, lens, finish",
     {"look": SB.LOOK_GRUPPEN}),
]

KOPF = """You write custom list entries for "Photoshoot", a ComfyUI node pack that
builds text prompts for photographic portraits (image model: Krea 2). Each entry
adds one choice to one list - a hat, a top, a light setup, a mood. The node puts
the entry's "prompt" text into the image prompt. Your answer is saved as a .json
file and loaded as it is, so it must be valid JSON.

OUTPUT
Only the JSON object below - nothing before or after it, no code fences, no
comments. Every entry needs "field", "label" and "prompt"; "builder" is
"person" when left out.

{
  "format": "photoshoot-presets/1",
  "name": "<a short name for this set>",
  "entries": [
    {"builder": "person", "field": "headwear", "label": "Trilby", "group": "Hats",
     "prompt": "a narrow-brimmed straw trilby"}
  ]
}

Optional keys per entry:
- "group": one of the families listed for that field (use the English name
  exactly as listed), or a new short name to start a new family.
- "en": a different display name for the English interface (default: label).
- "hex": "#rrggbb", only for colour fields - the swatch shown in the palette.

RULES (an entry that breaks one is skipped)
- Use only the builders and fields listed below, spelled exactly as listed.
- "label": short, at most 60 characters, unique within its field, and not one
  of the built-in names listed for that field.
- "prompt": English, at most 300 characters. Placeholders in curly braces only
  where a field says so ({c} in hairstyles).
- Age and gender cannot be extended; do not write entries for them.

WRITING THE PROMPT TEXT (what the render tests showed)
- Describe what is visible: shape, cut, length, material, texture, how it sits.
  "a close-fitting bell-shaped felt cloche hat with a narrow downturned brim"
  worked where "a cloche hat" came out as an ordinary brimmed hat.
- Keep it short: about 4 to 15 words. No quality or mood words ("beautiful",
  "stunning", "elegant", "masterpiece"), no camera or style words in a garment.
- A brand or film name on its own does little - describe the look instead.
- Follow the grammar of the examples of the field exactly: with or without an
  article, singular or plural, no colour where the field has its own colour.
- Do not repeat a built-in entry under another name; make each entry clearly
  different from the built-in ones and from each other.
- Nothing about age, and nothing that would describe a minor.
"""

FUSS = """
(Note for you, the person pasting this: render one test image per entry
before relying on it. A plausible wording does not always hold - in the render
tests a "bustle skirt" came out as a plain tiered skirt. Save the answer as
<name>.json in ComfyUI/user/krea2_presets/ and restart ComfyUI.)

WHAT I WANT
(Replace this paragraph with your request, for example: "12 hats from the
1920s to the 1960s", "8 light setups for a moody film-noir series", "the tops
from this list: ...". Say which builder or field if it is not obvious.)
"""


def _name(builder, modul, cat):
    if builder == "person":
        return i18n.FELDNAMEN.get(PeB.FELDNAMEN.get(cat, cat), cat)
    return i18n.KATEGORIEN.get(cat, cat)


def _felder(builder, modul):
    if builder == "person":
        return [c for c in list(PeB._SINGLE) + ["skinFeatures"] if c in modul.PRESETS]
    return list(modul.FOLGE)


def erzeuge():
    """The whole prompt as text."""
    anzeige = i18n.tabelle()
    teile = [KOPF, "FIELDS"]
    farben = set(PeB.FARBWERTE)
    for builder, modul, beschreibung, familien in BUILDER:
        schluessel = eigene.BUILDER[builder]
        teile.append('\n== "builder": "%s" - %s' % (builder, beschreibung))
        for cat in _felder(builder, modul):
            if (schluessel, cat) in eigene.GESPERRT:
                continue
            liste = modul.PRESETS[cat]
            namen = anzeige.get(schluessel, {}).get(cat, {})
            en = lambda l: namen.get(l, l)
            zeile = '\n- "%s" (%s)' % (cat, _name(builder, modul, cat))
            hinweis = SATZ.get(cat)
            if cat in farben:
                hinweis = "%s; %s" % (hinweis or FARBE, HEX)
            if hinweis:
                zeile += ": " + hinweis
            teile.append(zeile)
            if cat in familien:
                fam = [str(i18n.FAMILIEN.get(g, g)) for g in familien[cat]]
                teile.append("  families: " + ", ".join(fam))
            n = len(liste)
            for i in sorted({0, n // 2, n - 1}) if n > 3 else range(n):
                label, wert = liste[i]
                teile.append('  example: "%s" -> "%s"' % (en(label), wert))
            teile.append("  built-in (do not repeat): " + "; ".join(en(l) for l, _ in liste))
    teile.append(FUSS)
    return "\n".join(teile)
