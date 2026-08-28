"""
Lighting - assemble a studio or natural lighting setup from dropdowns.

Returns a STRING that goes into the "licht" / "lighting" input of "build prompt",
where it replaces the {lighting} or {licht} placeholder.
"""

import json
import random

PRESETS = {
    "setup": [
        # studio
        ("Softbox diffuses Licht", "softbox diffused studio lighting, gentle fill"),
        ("Rembrandt-Licht", "classic Rembrandt lighting with distinct triangle shadow"),
        ("Beauty Dish", "beauty dish key light with crisp catchlights in the eyes"),
        ("90s Direct Flash", "raw on-camera direct flash, 90s editorial fashion aesthetic"),
        ("Split-Lighting", "dramatic split lighting with half face in deep shadow"),
        ("Butterfly / Paramount", "flattering butterfly lighting with subtle shadow under nose and chin"),
        ("High-Key Studio", "bright high-key studio lighting, clean and shadowless"),
        ("Low-Key Moody", "moody low-key studio lighting with deep rich blacks"),
        ("Studio-Ringlicht", "macro studio ring light, sharp circular catchlights in pupils, even illumination"),
        ("Von oben / Top Light", "dramatic top-down overhead spotlight, sculptured cheekbones and shadows"),
        # natural & ambient
        ("Golden Hour", "warm golden hour sunlight, low angle warm illumination"),
        ("Blue Hour / Dämmerung", "atmospheric blue hour ambient light, cool tones"),
        ("Cinematic Fensterlicht", "cinematic window light with soft volumetric falloff"),
        ("Bewölktes Tageslicht", "soft overcast daylight with even natural illumination"),
        ("Hartes Sonnenlicht", "harsh direct midday sunlight with sharp distinct shadows"),
        ("Sonnenuntergang / Abendrot", "dramatic fiery sunset illumination, warm crimson and deep orange glow"),
        ("Schattenspiel / Blätter", "dappled sunlight filtered through window blinds and leaves, geometric cast shadows"),
        ("Morgendämmerung", "soft pale morning dawn light, gentle cool atmosphere"),
        # mood & creative
        ("Neon Akzente", "vibrant neon rim lighting, dual-tone cyan and magenta"),
        ("Jalousie-Schatten (Gobo)", "studio venetian blind gobo light projection, sharp horizontal shadow stripes across face"),
        ("Laser-Grid (Sci-Fi)", "sharp vibrant red laser beams projecting geometric grid lines across face"),
        ("Flammenschein / Kaminlicht", "warm flickering amber and deep orange firelight glow illuminating skin, low warm key"),
        ("Kerzenlicht / Warmes Glühen", "soft flickering candlelight, warm intimate glow"),
        ("Blaulicht / Sirenen-Schimmer", "dramatic dual-tone blue and red strobe rim lighting reflecting on skin"),
        ("Wasser-Kaustik (Projektion)", "shimmering aquatic water caustics light projection across skin, dynamic rippling reflections"),
        ("Volumetrische Lichtstrahlen", "dramatic volumetric god rays beaming through light haze"),
        ("Dramatisches Chiaroscuro", "dramatic chiaroscuro lighting, strong contrast between light and dark"),
        ("Mondlicht (Nacht)", "cool ethereal blue moonlight, deep night atmosphere, subtle silver reflections"),
        ("Prisma / Farbregen", "creative rainbow prism light refractions, subtle chromatic lens flare across face"),
        ("Film Noir Schatten", "classic black and white film noir lighting with dramatic venetian blind shadows"),
    ],
    "richtung": [
        ("Frontal 45°", "45-degree key light"),
        ("Streiflicht / Rim Light", "strong rim light defining silhouette and hair edges"),
        ("Gegenlicht", "backlit setup with subtle lens flare"),
        ("Seitliches Streiflicht", "dramatic side raking light emphasizing textures"),
        ("Dezentes Aufhelllicht", "balanced ambient fill light, soft natural contrast"),
        ("Von oben / Top Light", "top-down overhead lighting"),
    ],
    "atmosphaere": [
        ("Volumetrischer Dunst", "subtle volumetric light rays, atmospheric haze"),
        ("Klar & gestochen scharf", "clean crystal-clear air, sharp contrast"),
        ("Warmer Film-Glow", "warm vintage film glow, subtle halation"),
        ("Kühle Farbtiefe", "cool cinematic color grading, moody shadows"),
        ("Traumhaftes Bokeh", "dreamy background light bokeh"),
    ],
}

LICHT_GRUPPEN = {
    "studio": (
        "Softbox diffuses Licht", "Rembrandt-Licht", "Beauty Dish",
        "90s Direct Flash", "Split-Lighting", "Butterfly / Paramount",
        "High-Key Studio", "Low-Key Moody", "Studio-Ringlicht",
        "Von oben / Top Light",
    ),
    "natuerlich": (
        "Golden Hour", "Blue Hour / Dämmerung", "Cinematic Fensterlicht",
        "Bewölktes Tageslicht", "Hartes Sonnenlicht", "Sonnenuntergang / Abendrot",
        "Schattenspiel / Blätter", "Morgendämmerung",
    ),
    "stimmung": (
        "Neon Akzente", "Jalousie-Schatten (Gobo)", "Laser-Grid (Sci-Fi)",
        "Flammenschein / Kaminlicht", "Kerzenlicht / Warmes Glühen",
        "Blaulicht / Sirenen-Schimmer", "Wasser-Kaustik (Projektion)",
        "Volumetrische Lichtstrahlen", "Dramatisches Chiaroscuro",
        "Mondlicht (Nacht)", "Prisma / Farbregen", "Film Noir Schatten",
    ),
}

FOLGE = ("setup", "richtung", "atmosphaere")
NONE = "—"
ALLE = "alle"

DEFAULT_STATE = {
    "felder": {"setup": "Softbox diffuses Licht", "richtung": "Frontal 45°", "atmosphaere": "Klar & gestochen scharf"},
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


def compose_lighting(werte, details=""):
    teile = [werte[cat] for cat in FOLGE if werte.get(cat)]
    frei = (details or "").strip().rstrip(",;. \t\r\n")
    if frei:
        teile.append(frei)
    return ", ".join(teile)


class Krea2LightingBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True}),
            },
            "hidden": {
                "LightingState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("licht",)
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Setzt ein fotorealistisches Studio- oder Ambient-Licht-Setup zusammen. "
                   "Ausgang an den Eingang 'licht' von 'Photoshoot Prompt bauen' hängen, "
                   "im Text mit {lighting} oder {licht} platzieren.")

    def build(self, seed=0, LightingState=None):
        try:
            state = json.loads(LightingState) if LightingState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Lighting] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        felder = state.get("felder") or {}
        wuerfeln = state.get("wuerfeln") or {}
        gruppe = state.get("gruppe") or ALLE

        werte = {}
        for cat in FOLGE:
            if wuerfeln.get(cat):
                erlaubt = None
                if cat == "setup" and gruppe != ALLE:
                    erlaubt = LICHT_GRUPPEN.get(gruppe)
                label = _ziehe(cat, seed, erlaubt)
            else:
                label = felder.get(cat)
            werte[cat] = _val(cat, label)
        return (compose_lighting(werte, state.get("details", "")),)


NODE_CLASS_MAPPINGS = {"Krea2LightingBuilder": Krea2LightingBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2LightingBuilder": "Photoshoot Licht"}
