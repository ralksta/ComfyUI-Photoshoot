"""
Docking API for optional add-on packs.

Helpers kept deliberately stable, so an add-on pack can reuse the building
blocks here without having to take finished prompt strings apart again:

  - parse person_data
  - drop clothing fields from the value dict
  - reuse compose_person / detail_fuer_kamera

This module registers no nodes and holds no presets. Packs import it (or
person_builder) and keep their own lists themselves.
"""

from __future__ import annotations

import json

from . import person_builder as PeB

# Legwear and shoes from the Person Builder. Add-on packs drop them only when
# asked to (barefoot, say) - by default they stay, because the Person Builder
# is the source of truth for them, not the pack.
KLEIDUNG_FELDER = (
    "hosiery",
    "hosieryColor",
    "shoes",
    "shoesColor",
)

# Optionally dropped as well, when accessories collide with what the pack puts
# on top (hat, necklace, glasses). Off by default.
ACCESSOIRE_FELDER = (
    "jewellery",
    "eyewear",
    "headwear",
)


def parse_person_data(person_data):
    """person_data (JSON string or dict) -> dict. Empty or invalid -> {}."""
    if not person_data:
        return {}
    if isinstance(person_data, dict):
        p = dict(person_data)
    else:
        try:
            p = json.loads(person_data)
        except (TypeError, ValueError):
            return {}
    if not isinstance(p, dict):
        return {}
    if "felder" in p or "texte" in p:
        try:
            _, resolved_json = PeB.Krea2PersonBuilder().build(json.dumps(p) if isinstance(p, dict) else person_data)
            return json.loads(resolved_json)
        except Exception:
            pass
    return p



def strip_felder(p, felder):
    """A copy of p in which the named keys are set to None."""
    out = dict(p or {})
    for key in felder:
        out[key] = None
    return out


def strip_kleidung(p, accessoires=False, free=False):
    """Take the clothing fields out of the value dict.

    accessoires=True drops jewellery, eyewear and headwear as well.
    free=True clears the free text, which often holds something like
    'wearing a red raincoat'.
    """
    felder = list(KLEIDUNG_FELDER)
    if accessoires:
        felder.extend(ACCESSOIRE_FELDER)
    out = strip_felder(p, felder)
    if free:
        out["free"] = ""
    return out


def setze_free(p, text):
    """Set the free text, typically a new wardrobe after stripping."""
    out = dict(p or {})
    out["free"] = (text or "").strip()
    return out


def person_aus_data(person_data, kamera_label=None, detail=None,
                    kleidung_strip=False, accessoires_strip=False,
                    free_strip=True, free_neu=None):
    """person_data plus optional corrections -> a finished person string.

    This is the recommended route for add-on packs:

      1. write the new wardrobe into free
      2. compose_person with the detail level for the camera

    kleidung_strip is off: legwear and shoes belong to the Person Builder, and
    a pack takes them away only when explicitly asked to (barefoot). free_strip
    is on, because free typically holds the old wardrobe that the pack is in
    the middle of replacing.
    """
    p = parse_person_data(person_data)
    if kleidung_strip:
        p = strip_kleidung(p, accessoires=accessoires_strip, free=free_strip)
    elif free_strip:
        p = dict(p)
        p["free"] = ""
    if free_neu is not None:
        p = setze_free(p, free_neu)
    if detail is None:
        detail = PeB.detail_fuer_kamera(kamera_label) if kamera_label else PeB.DETAIL_VOLL
    return PeB.compose_person(p, detail=detail)


# Comma and whitespace in one go, at both ends. Done separately (.strip()
# followed by .strip(",")), ", leaning back" would keep the space behind the
# comma and end up with two spaces in the middle.
_RAND = " ,\t\r\n"


def pose_anhaengen(pose, extra):
    """Join a pose and a pack's addition without doubling the comma."""
    a = (pose or "").strip(_RAND)
    b = (extra or "").strip(_RAND)
    if a and b:
        return a + ", " + b
    return a or b


# Re-exports, so that packs only ever need to import dock.
compose_person = PeB.compose_person
detail_fuer_kamera = PeB.detail_fuer_kamera
DETAIL_VOLL = PeB.DETAIL_VOLL
DETAIL_FIGUR = PeB.DETAIL_FIGUR
DETAIL_IDENTITAET = PeB.DETAIL_IDENTITAET
KAMERA_DETAIL = PeB.KAMERA_DETAIL
