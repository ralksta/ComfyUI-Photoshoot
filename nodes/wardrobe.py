"""
Photoshoot Wardrobe: the outfits of a shoot, for costume changes in a series.

All clothing lives here - the Person Builder has none of its own since the
wardrobe exists. One node holds the whole wardrobe - people plan one wardrobe per shoot, and a
chain of one node per outfit (the first version) made the graph hard to read.
Every outfit carries the clothing and accessories sections of the Person
Builder (same fields, same wordings, same interface) and a name, and nothing of
the person; the interface shows them as tabs. The output goes into the Person
Builder: the person wears the open tab, and a Series node downstream dresses
her in one outfit per photo - in blocks, as on a real shoot, or mixed.

Measured before it was built: with only the clothing text changing, the face of
the README person held across a crop top, a turtleneck and a Bardot top on the
same seed; a bikini moved it visibly (broader, a slightly different type).
"""

import json
import re

from . import person_builder as PeB

# "outfits" in the order of the tabs; "id" keys the rendered preview of an
# outfit in the node's properties, so renaming or reordering keeps it.
DEFAULT_STATE = {
    "outfits": [{"id": "o1", "name": "", "felder": {}, "texte": {"details": ""}}],
    "aktiv": 0,
    "sektion": PeB.OUTFIT_SEKTIONEN[0],
}


def outfits_aus_state(state):
    """[{"name", "werte"}] of a Wardrobe state: the English values of every
    outfit, unnamed ones counted ("Outfit 2")."""
    liste = []
    for i, o in enumerate((state or {}).get("outfits") or []):
        if not isinstance(o, dict):
            continue
        werte = PeB.werte_aus_state({"felder": o.get("felder") or {}, "texte": o.get("texte") or {},
                                     "eigene": o.get("eigene")})
        werte = {k: v for k, v in werte.items() if k in PeB.OUTFIT_FELDER and v}
        name = (o.get("name") or "").strip() or "Outfit %d" % (i + 1)
        liste.append({"name": name, "werte": werte})
    return liste


garderobe_lesen = PeB.garderobe_lesen


# ------------------------------------------------------ Outfit preview ---
# The picture on an outfit's card: the outfit on its own, not on the person, so
# the clothes stand apart from her and nobody has to take the README redhead as
# the base. Rendered through the user's own workflow (the Series node swaps
# this text into Build Prompt), but with a fixed look of its own - the shoot's
# style and lighting words are unknown here, and in the tests one extra clause
# was enough to make black tights vanish from the mannequin.
#
# Render-tested 2026-09 on Krea 2 Turbo (eight hosiery kinds, accessories,
# all-black outfits). Found on the way: a white mannequin bled into jeans
# without a colour; a ghost mannequin came out as a real woman with her head
# cropped; turning the mannequin, a contrapposto or a hard light each lost the
# tights; sheer skin-coloured tights do not show on any mannequin colour (the
# swatch list on the card carries them).
_LOOK = ("{extra}clean modern fashion e-commerce product photograph, %s, bright even high-key "
         "studio light, neutral colours, a plain mid grey seamless paper studio backdrop, empty studio, ")
VORSCHAU = {
    "puppe": _LOOK % ("full length shot of a mannequin, the mannequin fills the frame from the top "
                      "of the head to the base of the stand with only a small margin")
             + "a faceless light grey fashion store mannequin standing on a small round stand, "
               "{bein}{rest}, arms at the sides",
    "flach": _LOOK % "flat lay photograph from directly above, the pieces fill the frame with a small margin"
             + "an outfit laid out neatly side by side: {teile}{bein}, no person",
}
# Hosiery has to be tied to the legs right after the mannequin - further down
# the clothing list it dropped out. In the flat lay, tights look like leggings
# unless the waistband and the feet are named; stockings have no waistband.
_BEIN_PUPPE = {
    "strumpfhose": "its legs covered in {h} from the waist down to the toes, ",
    "struempfe": "its legs in {h} reaching up the thighs, ",
    "socken": "its feet and lower legs in {h}, ",
    "leggings": "its legs covered in {h} from the waist down to the ankles, ",
    "sonst": "wearing {h}, ",
}
_BEIN_FLACH = {
    "strumpfhose": ", and {h} laid out flat to full length with the waistband and both sewn-in feet visible",
    "struempfe": ", and a pair of {h} laid out flat side by side to full length",
    "socken": ", and a pair of {h} laid out flat side by side",
    "leggings": ", and {h} laid out flat to full length",
    "sonst": ", and {h}",
}


def _beinart(wert):
    """The kind of legwear, from its English wording."""
    w = wert.lower()
    if "leggings" in w:
        return "leggings"
    if "socks" in w:
        return "socken"
    if "pantyhose" in w or "tights" in w:
        return "strumpfhose"
    if "stockings" in w:
        return "struempfe"
    return "sonst"


def _teile(satz):
    """'wearing a ..., with a ..., wearing ...' as a plain list of garments."""
    t = [re.sub(r"^(wearing|with)\s+", "", x.strip())
         for x in re.split(r",\s*(?=with |wearing )", satz) if x.strip()]
    if len(t) < 2:
        return "".join(t)
    return ", ".join(t[:-1]) + ", and " + t[-1]


def vorschau_prompt(werte, art="puppe"):
    """The preview text for an outfit (English values, as in the wardrobe).
    Contains the {extra} placeholder, which keeps Build Prompt from adding the
    shoot's style, scene and lighting on its own."""
    werte = {k: v for k, v in (werte or {}).items() if k in PeB.OUTFIT_FELDER and v}
    hosiery = werte.pop("hosiery", None)
    farbe = werte.pop("hosieryColor", None)
    rest = PeB.compose_person(werte)
    bein = ""
    if hosiery and hosiery != "bare legs":
        h = PeB.compose_person({"hosiery": hosiery, "hosieryColor": farbe}).replace("wearing ", "", 1)
        bein = (_BEIN_FLACH if art == "flach" else _BEIN_PUPPE)[_beinart(hosiery)].format(h=h)
    if not rest and not bein:
        return None
    if art == "flach":
        teile = _teile(rest) if rest else bein.removeprefix(", and ")
        return VORSCHAU["flach"].format(extra="{extra}", teile=teile, bein=bein if rest else "")
    return VORSCHAU["puppe"].format(extra="{extra}", bein=bein if rest else bein.removesuffix(", "), rest=rest)


def vorschau_aus_state(outfit, art="puppe"):
    """The preview text straight from one outfit of a Wardrobe state (labels)."""
    outfit = outfit or {}
    return vorschau_prompt(PeB.werte_aus_state({"felder": outfit.get("felder") or {},
                                                "texte": outfit.get("texte") or {},
                                                "eigene": outfit.get("eigene")}), art)


class Krea2Wardrobe:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "hidden": {
                "WardrobeState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("garderobe",)
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Die Outfits eines Shootings, als Reiter. Ausgang an den Eingang "
                   "'garderobe' des Person Builders: die Person trägt den offenen Reiter, "
                   "die Serie wechselt durch alle Outfits.")

    def build(self, WardrobeState=None):
        try:
            state = json.loads(WardrobeState) if WardrobeState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Wardrobe] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)
        outfits = outfits_aus_state(state)
        aktiv = min(max(0, int(state.get("aktiv") or 0)), max(0, len(outfits) - 1))
        return (json.dumps({"aktiv": aktiv, "outfits": outfits}, ensure_ascii=False),)


NODE_CLASS_MAPPINGS = {"Krea2Wardrobe": Krea2Wardrobe}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2Wardrobe": "Photoshoot – Wardrobe"}
