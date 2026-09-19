"""
Style - the photographic look, assembled from dropdowns instead of typed.

Returns a STRING that goes into the "stil" / "style" input of "build prompt",
where it replaces the {style} or {stil} placeholder.

Why this exists: "how do I get black and white?" was the first question after
the 2.2.0 release. The answer was "type it into the style text box", which is
correct and still unhelpful - nothing in the kit said so, and the wording that
actually works at CFG 1 (a bare "b&w" is too weak against a person block full
of colour words) had to be found by trial. The look family here carries the
wordings that were measured to hold up.
"""

import json
import random

PRESETS = {
    # The look: colour treatment or film stock. Two families, because the
    # first thing you decide is "colour or not", and only then which one.
    "look": [
        # black and white - ten, measured (docs/measurements.md). Eighteen
        # wordings were rendered on one portrait; film stocks and brand looks
        # named as such ("shot on Ilford Delta 3200 ...") came out as the
        # classic image. The model at CFG 1 reads described properties -
        # contrast, grain, brightness, tone - and reads them from the head of
        # the phrase: "extremely grainy black and white photograph" gets the
        # grain that "shot on Delta 3200, heavy coarse grain" did not. So the
        # famous looks are here as what they are, with the name as a hint.
        ("Schwarzweiß klassisch", "black and white photograph, monochrome, rich tonal range"),
        ("Schwarzweiß kontrastreich", "high contrast black and white photograph, monochrome, deep blacks and bright highlights"),
        ("Schwarzweiß Film Noir", "black and white film noir photograph, monochrome, dramatic hard shadows"),
        ("Schwarzweiß körnig (Tri-X)", "grainy black and white 35mm film photograph, monochrome, visible film grain"),
        ("Schwarzweiß High-Key", "high-key black and white photograph, monochrome, bright airy tones, minimal shadows"),
        ("Schwarzweiß grob körnig (Delta 3200)", "extremely grainy black and white photograph, monochrome, heavy coarse pushed film grain, gritty shadows"),
        ("Schwarzweiß fein & kornfrei (Leica)", "razor sharp fine detail black and white photograph, monochrome, crisp micro-contrast, deep clean blacks, grain-free"),
        ("Schwarzweiß Infrarot", "infrared black and white photograph, monochrome, glowing luminous white skin and foliage, black sky, soft halo"),
        ("Sepia", "sepia toned monochrome photograph, warm brown tones"),
        ("Selen-Tonung", "selenium toned black and white print, monochrome, cool deep shadows"),
        # colour - seven of sixteen, same test (docs/measurements.md). Teal &
        # orange, cross-processed, Lomo, bleach bypass, "editorial grade",
        # "vibrant" and the like all landed on the neutral image; what stays
        # moves brightness, saturation or warmth by a measurable margin.
        ("Kodak Portra", "shot on Kodak Portra 400 film, soft natural skin tones, gentle pastel colours"),
        ("Cinestill 800T", "shot on Cinestill 800T tungsten film, warm highlights with red halation"),
        ("Kodachrome", "Kodachrome slide film look, saturated warm colours, deep contrast"),
        ("Polaroid", "instant Polaroid photograph, soft faded colours, slight vignette"),
        ("Warm Golden", "warm golden colour grade, glowing skin tones"),
        ("Kühl entsättigt", "cool desaturated colour grade, muted tones"),
        ("Pastell", "soft pastel colour palette, airy and bright"),
    ],
    "genre": [
        ("Editorial", "editorial photography"),
        ("Fashion", "high fashion photography"),
        ("Beauty", "beauty photography, flawless polished skin"),
        ("Studio-Porträt", "professional studio portrait photography"),
        ("Street", "candid street photography"),
        ("Dokumentarisch", "documentary photography, unposed and authentic"),
        ("Glamour", "glamour photography"),
        ("Boudoir", "boudoir photography, intimate and tasteful"),
        ("Lifestyle", "lifestyle photography, natural and relaxed"),
        ("Filmstill", "cinematic film still"),
        ("Lookbook", "lookbook photography, clean and product focused"),
        ("Paparazzi", "paparazzi snapshot, candid and unpolished"),
        ("Passfoto", "passport photo, plain background, frontal and evenly lit"),
    ],
    "optik": [
        ("85mm f/1.4", "85mm lens, f/1.4, shallow depth of field, creamy bokeh"),
        ("50mm f/1.8", "50mm lens, f/1.8, natural perspective"),
        ("35mm f/2", "35mm lens, f/2, environmental perspective"),
        ("135mm f/2", "135mm telephoto lens, compressed perspective, isolated subject"),
        ("24mm Weitwinkel", "24mm wide angle lens, dramatic perspective"),
        ("100mm Makro", "100mm macro lens, extreme detail"),
        ("Durchgehend scharf", "f/8, deep focus, everything sharp from front to back"),
        ("Anamorph", "anamorphic lens, oval bokeh, horizontal lens flares"),
        ("Vintage-Objektiv", "vintage lens, soft glow, swirly bokeh"),
        ("Tilt-Shift", "tilt-shift lens, narrow plane of focus"),
    ],
    "finish": [
        ("Natürliche Haut", "natural skin texture, visible pores"),
        ("Feines Korn", "fine film grain"),
        ("Grobes Korn", "heavy visible film grain"),
        ("Weichzeichner", "soft focus, dreamy glow"),
        ("Vignette", "subtle vignette"),
        ("Scharf & detailliert", "tack sharp, highly detailed"),
        ("Halation", "halation around the highlights"),
        ("Leichte Bewegungsunschärfe", "slight motion blur"),
    ],
}

LOOK_GRUPPEN = {
    "schwarzweiss": (
        "Schwarzweiß klassisch", "Schwarzweiß kontrastreich", "Schwarzweiß Film Noir",
        "Schwarzweiß körnig (Tri-X)", "Schwarzweiß High-Key",
        "Schwarzweiß grob körnig (Delta 3200)", "Schwarzweiß fein & kornfrei (Leica)",
        "Schwarzweiß Infrarot", "Sepia", "Selen-Tonung",
    ),
    "farbe": (
        "Kodak Portra", "Cinestill 800T", "Kodachrome", "Polaroid",
        "Warm Golden", "Kühl entsättigt", "Pastell",
    ),
}

# The look comes first on purpose. A colour treatment is the one style word
# that has to win against the person block - "copper red hair" and "green
# eyes" are colour words too - and the model weighs early tokens more.
FOLGE = ("look", "genre", "optik", "finish")
NONE = "—"
ALLE = "alle"

# Matches the style text the example workflow used to carry as free text:
# "editorial photography, 85mm, natural light, shallow depth of field".
DEFAULT_STATE = {
    "felder": {"look": NONE, "genre": "Editorial", "optik": "85mm f/1.4", "finish": NONE},
    "wuerfeln": {},
    "gruppe": ALLE,
    "details": "",
}


def _val(cat, label):
    if not label or label == NONE:
        return ""
    for lbl, wert in PRESETS[cat]:
        if lbl == label:
            return wert
    return label


def _ziehe(cat, seed, erlaubt=None):
    labels = erlaubt if erlaubt else [lbl for lbl, _ in PRESETS[cat]]
    return random.Random("%d-%s" % (seed, cat)).choice(labels)


def compose_style(werte, details=""):
    teile = [werte[cat] for cat in FOLGE if werte.get(cat)]
    frei = (details or "").strip().rstrip(",;. \t\r\n")
    if frei:
        teile.append(frei)
    return ", ".join(teile)


class Krea2StyleBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True}),
            },
            "hidden": {
                "StyleState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("stil",)
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Setzt den fotografischen Look zusammen: Farbe oder Schwarzweiß, "
                   "Filmlook, Genre, Objektiv, Finish. Ausgang an den Eingang 'stil' "
                   "von 'Photoshoot Prompt bauen' hängen, im Text mit {style} oder "
                   "{stil} platzieren.")

    def build(self, seed=0, StyleState=None):
        try:
            state = json.loads(StyleState) if StyleState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Style] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        felder = state.get("felder") or {}
        wuerfeln = state.get("wuerfeln") or {}
        gruppe = state.get("gruppe") or ALLE

        werte = {}
        for cat in FOLGE:
            if wuerfeln.get(cat):
                erlaubt = None
                if cat == "look" and gruppe != ALLE:
                    erlaubt = LOOK_GRUPPEN.get(gruppe)
                label = _ziehe(cat, seed, erlaubt)
            else:
                label = felder.get(cat)
            werte[cat] = _val(cat, label)
        return (compose_style(werte, state.get("details", "")),)


NODE_CLASS_MAPPINGS = {"Krea2StyleBuilder": Krea2StyleBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2StyleBuilder": "Photoshoot Stil"}
