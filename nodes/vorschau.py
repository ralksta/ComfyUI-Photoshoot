"""
Preview thumbnails of the built-in entries - what a milkmaid top or a cloche
looks like before you pick it.

Clothes, shoes and headwear are shown alone on the Wardrobe's preview
mannequin in its studio look (shoes as a three-quarter close-up, so the heel
shows); hairstyles on the README person, as a crop of their poster tile. Every
entry of a field is rendered the same way, so the thumbnails compare with each
other. They live in js/vorschau/<field>/<slug>.jpg, where the web
server already serves the package's JS, and /krea2/presets names the file for
each entry that has one. A custom entry (eigene.py) has none; the list then
shows its prompt text only.

The thumbnails are built outside the package from the rendered tiles
(~/.cache/photoshoot-doku: puppe_kacheln.py, puppe_schuhe_nah.py,
vorschau_bauen.py); this module only knows the file names.
"""

import os
import re
import unicodedata

WURZEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js", "vorschau")


def slug(label):
    """The file name of a label: ASCII, lower case, dashes. "Fascinator",
    "Pillbox mit Schleier" -> "pillbox-mit-schleier", "Mütze" -> "mutze"."""
    s = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "x"


def _vorhanden():
    try:
        return {cat: set(os.listdir(os.path.join(WURZEL, cat)))
                for cat in os.listdir(WURZEL) if os.path.isdir(os.path.join(WURZEL, cat))}
    except OSError:
        return {}


# Read once: the files ship with the package and do not change at run time.
_DATEIEN = _vorhanden()


def bild(cat, label):
    """The path of the entry's thumbnail relative to js/, or None."""
    name = slug(label) + ".jpg"
    return "vorschau/%s/%s" % (cat, name) if name in _DATEIEN.get(cat, ()) else None
