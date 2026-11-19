"""
Cuts the thumbnails of the lighting setups and the base postures out of the
reference posters (docs/posters/), into js/vorschau/licht/ and
js/vorschau/haltung/ - the same folder, naming and JPEG settings as the
Wardrobe's thumbnails (nodes/vorschau.py), so /krea2/presets delivers them the
same way and the panels show them as tiles.

    python3 tools/schneide_vorschau.py            # writes the files
    python3 tools/schneide_vorschau.py --pruefen  # only checks the labels and
                                                  # that every file is there

Needs Pillow (not a dependency of the pack; tools/ is not shipped). Re-runnable:
it overwrites what it wrote before and removes files no entry names any more.

The poster geometry is measured on the _web.jpg versions; the full-size PNG
next to it is exactly twice as large and is used when present, for sharper
tiles. The lighting poster follows the pack's order of setups; the pose poster
has an order of its own (POSE_POSTER). Entries appended after a poster was
made are not on it and keep plain chips - thumbnails for light and posture are
optional, unlike those for clothes, shoes, hair and headwear.
"""

import argparse
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

from nodes import lighting_builder as LB  # noqa: E402
from nodes import pose_builder as PB  # noqa: E402
from nodes import vorschau as VS  # noqa: E402

POSTER = os.path.join(WURZEL, "docs", "posters")
BREITE = 150          # as the existing thumbnails (150×200)
QUALITAET = 80        # their quantisation tables are libjpeg's quality 80

# Poster tile -> label on the pose poster (18 tiles, 6 × 3).
POSE_POSTER = [
    "Stehend", "Angelehnt", "Stehend, Gewicht auf einem Bein", "Gehend", "Vorgebeugt",
    "Auf einem Stuhl sitzend", "Auf einem Hocker sitzend", "Auf einer Tischkante sitzend",
    "Auf dem Boden sitzend", "Zurückgelehnt", "Kniend", "Auf einem Knie", "Hockend",
    "Auf allen Vieren", "Auf dem Rücken liegend", "Auf dem Bauch liegend",
    "Auf der Seite liegend", "Strecken",
]

# name, poster, labels in tile order, columns, x of column c, width, y of each
# row, height (all in the _web.jpg's pixels), output size.
BOEGEN = [
    ("licht", "photoshoot_lighting_matrix_30",
     [lbl for lbl, _ in LB.PRESETS["setup"]][:30], 6,
     lambda c: 12 + c * 292, 280, [132 + r * 337 for r in range(5)], 280, (BREITE, BREITE)),
    ("haltung", "photoshoot_poses_matrix_18",
     POSE_POSTER, 6,
     lambda c: 12 + c * 282, 270, [132, 549, 966], 358, (BREITE, 200)),
]


def _quelle(name):
    """The full-size PNG and its scale, else the web JPEG."""
    png = os.path.join(POSTER, name + ".png")
    if os.path.exists(png):
        return png, 2
    return os.path.join(POSTER, name + "_web.jpg"), 1


def _zuschnitt(box, ziel):
    """Crop the box (x0, y0, x1, y1) centred to the target's aspect ratio."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    soll = ziel[0] / ziel[1]
    if w / h > soll:                     # too wide: trim the sides
        neu = h * soll
        x0 += (w - neu) / 2
        x1 = x0 + neu
    else:                                # too tall: trim top and bottom
        neu = w / soll
        y0 += (h - neu) / 2
        y1 = y0 + neu
    return tuple(round(v) for v in (x0, y0, x1, y1))


def pruefe():
    """Every poster label is a built-in label of its field, none twice."""
    fehler = []
    for ordner, _, labels, *_ in BOEGEN:
        echte = {lbl for lbl, _ in (LB.PRESETS["setup"] if ordner == "licht" else PB.PRESETS["haltung"])}
        fehler += ["%s: %s ist kein Eintrag" % (ordner, l) for l in labels if l not in echte]
        if len(set(labels)) != len(labels):
            fehler.append("%s: doppelt" % ordner)
    return fehler


def schneide():
    from PIL import Image

    for ordner, name, labels, spalten, x_von, breite, zeilen, hoehe, groesse in BOEGEN:
        pfad, faktor = _quelle(name)
        bild = Image.open(pfad).convert("RGB")
        ziel = os.path.join(VS.WURZEL, ordner)
        os.makedirs(ziel, exist_ok=True)
        soll = set()
        for i, label in enumerate(labels):
            r, c = divmod(i, spalten)
            x0, y0 = x_von(c), zeilen[r]
            box = _zuschnitt((x0 * faktor, y0 * faktor, (x0 + breite) * faktor, (y0 + hoehe) * faktor), groesse)
            kachel = bild.crop(box).resize(groesse, Image.LANCZOS)
            datei = VS.slug(label) + ".jpg"
            soll.add(datei)
            kachel.save(os.path.join(ziel, datei), "JPEG", quality=QUALITAET, progressive=True, optimize=True)
        for alt in set(os.listdir(ziel)) - soll:
            os.remove(os.path.join(ziel, alt))
        print("%s: %d Kacheln aus %s" % (ordner, len(labels), os.path.basename(pfad)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pruefen", action="store_true", help="only check labels and files")
    args = ap.parse_args()
    fehler = pruefe()
    if args.pruefen:
        for ordner, _, labels, *_ in BOEGEN:
            fehler += ["%s: %s fehlt" % (ordner, l) for l in labels
                       if not os.path.exists(os.path.join(VS.WURZEL, ordner, VS.slug(l) + ".jpg"))]
    if fehler:
        print("\n".join(fehler))
        sys.exit(1)
    if not args.pruefen:
        schneide()
    print("ok")


if __name__ == "__main__":
    main()
