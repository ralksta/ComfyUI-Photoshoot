"""
The Python side of tests/plan.mjs - not run on its own.

    python3 tests/plan_fixture.py OUT.json

Writes the preset data the interface gets from /krea2/presets ("shooting")
and, for many series states, what shooting.py plans per run: plane(),
format_fuer(), masse(), outfit_fuer(), set_fuer() and licht_fuer().
tests/plan.mjs spawns this on every
run, so the expected values always come from the current Python code and are
never a stale copy.
"""

import json
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from nodes import api  # noqa: E402
from nodes import expression_builder as EB  # noqa: E402
from nodes import pose_builder as PB  # noqa: E402
from nodes import shooting as SH  # noqa: E402

LAEUFE = 40


# The sets of a Location node as the planner sees them: whether each one is
# outdoors (True), indoors (False) or of no family (None).
SAETZE = {"none": [], "one indoor": [False], "loft street park": [False, True, True],
          "four mixed": [True, None, False, True], "two unknown": [None, None]}


def faelle():
    """(name, state, outfits, first run[, sets]) - every state the preview
    can meet, as far as the planner is concerned."""
    basis = json.loads(json.dumps(SH.DEFAULT_STATE))
    ohne_auswahl = dict(basis, kameras=None, fokusse=None)   # as the panel stores it
    f = [("default", basis, 0, 0), ("default, panel lists", ohne_auswahl, 0, 0),
         ("default, from photo 5001", dict(basis, start=5001), 0, 5000),
         ("default, beyond the series", dict(basis, anzahl=5), 0, 20),
         # Large photo numbers: lauf * step leaves the exact range of a double
         # (2^53) from photo 2^21 or so. Run 2^40 + 1980 drew a different framing
         # in JS until the product went through BigInt.
         ("default, photo 1234567891", dict(basis, start=1234567891), 0, 1234567890),
         ("default, photo 2^40 + 1961", dict(basis, start=2 ** 40 + 1961), 0, 2 ** 40 + 1960)]
    for name, _, patch in SH.REZEPTE:
        st = dict(basis, **json.loads(json.dumps(patch)))
        f.append(("recipe %s" % name, st, 0, 0))
        f.append(("recipe %s, 3 outfits" % name, st, 3, 0))
    for ordnung in ("gezogen", "reihum", "weit_nah", None):
        for abdeckung in (False, True):
            st = dict(ohne_auswahl, reihenfolge=ordnung, abdeckung=abdeckung, anzahl=12)
            f.append(("order %s/%s" % (ordnung, abdeckung), st, 0, 0))
            for zahl in (2, 3, 4):
                for folge in ("bloecke", "gemischt"):
                    f.append(("order %s/%s, %d outfits %s" % (ordnung, abdeckung, zahl, folge),
                              dict(st, outfitFolge=folge), zahl, 0))
        f.append(("order %s, two framings" % ordnung,
                  dict(ohne_auswahl, reihenfolge=ordnung, kameras=["Totale", "Porträt"]), 0, 0))
        f.append(("order %s, 7 photos from 101" % ordnung,
                  dict(ohne_auswahl, reihenfolge=ordnung, anzahl=7, start=101), 0, 100))
    f.append(("outfits off", dict(ohne_auswahl, aktiv=dict(basis["aktiv"], outfit=False)), 3, 0))
    for bogen in list(SH.STIMMUNGSBOEGEN) + [True, "Aufbau", "gibt es nicht"]:
        for ordnung in ("weit_nah", "gezogen"):
            for anzahl, start in ((7, 1), (12, 1), (30, 501)):
                f.append(("arc %s, %s, %d from %d" % (bogen, ordnung, anzahl, start),
                          dict(ohne_auswahl, bogen=bogen, reihenfolge=ordnung, anzahl=anzahl, start=start),
                          0, start - 1))
        f.append(("arc %s, expression off" % bogen,
                  dict(ohne_auswahl, bogen=bogen, aktiv=dict(basis["aktiv"], ausdruck=False)), 0, 0))
        f.append(("arc %s, 2 outfits" % bogen, dict(ohne_auswahl, bogen=bogen, reihenfolge="weit_nah"), 2, 0))
    for fam in PB.HALTUNG_GRUPPEN:
        f.append(("posture family %s" % fam, dict(ohne_auswahl, pools={"haltung": fam}), 0, 0))
    for fam in EB.STIMMUNG_GRUPPEN:
        f.append(("mood family %s" % fam, dict(ohne_auswahl, pools={"stimmung": fam}), 0, 0))
    for cat in PB.FOLGE + EB.FOLGE:
        f.append(("pool %s none" % cat, dict(ohne_auswahl, pools={cat: SH.NONE}), 0, 0))
    f.append(("unknown family", dict(ohne_auswahl, pools={"haltung": "gibt es nicht"}), 0, 0))
    # Several families as a list, as the next round writes them (naechste_runde()).
    for feld, fams in (("haltung", ["stehend", "sitzend"]), ("haltung", ["kniend"]),
                       ("haltung", ["liegend", "gibt es nicht"]), ("haltung", []),
                       ("stimmung", ["ruhig", "freundlich"]), ("stimmung", ["in sich gekehrt"])):
        f.append(("family list %s %s" % (feld, "+".join(fams)), dict(ohne_auswahl, pools={feld: fams}), 0, 0))
        f.append(("family list %s %s, gaze camera" % (feld, "+".join(fams)),
                  dict(ohne_auswahl, pools={feld: fams}, blick="kamera"), 0, 0))
    # A subset of the wardrobe's outfits (outfitAuswahl), in blocks and mixed,
    # with every framing order; out-of-range indices fall back to all.
    for auswahl, zahl in (([0, 2], 3), ([1], 2), ([2, 0], 4), ([7], 3), ([], 3), (None, 3)):
        for folge in ("bloecke", "gemischt"):
            for ordnung in ("gezogen", "reihum", "weit_nah"):
                f.append(("outfits %s of %d %s, %s" % (auswahl, zahl, folge, ordnung),
                          dict(ohne_auswahl, outfitAuswahl=auswahl, outfitFolge=folge,
                               reihenfolge=ordnung, anzahl=12), zahl, 0))
    # States as naechste_runde() writes them: favourites across framings,
    # families and outfits of a mixed series, and rejects on their own.
    for fav, weg, zahl in (([1, 4, 7], [], 0), ([2, 3], [5], 3), ([], [1, 2, 6], 2), ([9], [], 3)):
        st = dict(ohne_auswahl, favoriten=fav, verworfen=weg, outfitFolge="bloecke")
        neu = SH.naechste_runde(st, zahl)
        f.append(("next round fav %s rej %s, %d outfits" % (fav, weg, zahl), neu, zahl, neu["start"] - 1))
    for achse in ("kamera", "pose", "ausdruck", "format", "fokus", "rausch"):
        f.append(("axis %s off" % achse, dict(basis, aktiv=dict(basis["aktiv"], **{achse: False})), 0, 0))
    f.append(("aktiv partial", dict(basis, aktiv={"pose": False}), 2, 0))
    f.append(("fixed ratio 16:9", dict(basis, aktiv=dict(basis["aktiv"], format=False),
                                       festesFormat="16:9"), 0, 0))
    for kante in SH.KANTEN:
        f.append(("size %d" % kante, dict(ohne_auswahl, groesse=kante), 0, 0))
    f.append(("framings detail only", dict(ohne_auswahl, kameras=["Detail"]), 0, 0))
    f.append(("focus feet and hands", dict(ohne_auswahl, fokusse=["Füße", "Hände"]), 0, 0))
    f.append(("focus face, wide framings", dict(ohne_auswahl, fokusse=["Gesicht"],
                                                 kameras=["Totale", "Ganzkörper"]), 0, 0))
    f.append(("takes", dict(ohne_auswahl, takes={"1": 2, "5": 1}, takesJeFoto=3,
                            wahl={"5": 1}, favoriten=[3]), 0, 0))
    # Gaze modes, alone and with everything that filters or overrides them.
    for modus in list(SH.BLICK_MODI) + ["gibt es nicht"]:
        st = dict(ohne_auswahl, blick=modus)
        f.append(("gaze %s" % modus, st, 0, 0))
        f.append(("gaze %s, from 1001" % modus, dict(st, start=1001), 0, 1000))
        f.append(("gaze %s, arc Drama" % modus, dict(st, bogen="Drama", reihenfolge="weit_nah"), 0, 0))
        for fam in ("in sich gekehrt", "zugewandt", "freundlich"):
            f.append(("gaze %s, mood family %s" % (modus, fam), dict(st, pools={"stimmung": fam}), 0, 0))
        f.append(("gaze %s, gaze none" % modus, dict(st, pools={"blick": SH.NONE}), 0, 0))
        f.append(("gaze %s, turn over the shoulder" % modus,
                  dict(st, pools={"haltung": "stehend"}), 0, 0))
        f.append(("gaze %s, expression off" % modus,
                  dict(st, aktiv=dict(basis["aktiv"], ausdruck=False)), 0, 0))
        f.append(("gaze %s, 3 outfits mixed" % modus, dict(st, outfitFolge="gemischt"), 3, 0))
        for name, _, patch in SH.REZEPTE:
            f.append(("gaze %s, recipe %s" % (modus, name),
                      dict(basis, **dict(json.loads(json.dumps(patch)), blick=modus)), 0, 0))
    # The perspective axis (selfie mode): off by default, on with every
    # framing, each perspective alone, with the couplings it has - posture
    # families (lying, standing, all fours), the selfie mood family, the gaze
    # modes, a mood arc, the camera switched off, a wardrobe, a next round.
    an = dict(basis["aktiv"], perspektive=True)
    selfie = dict(ohne_auswahl, aktiv=an)
    f.append(("perspective on, all framings", selfie, 0, 0))
    f.append(("perspective on, from 7001", dict(selfie, start=7001), 0, 7000))
    f.append(("perspective listed but off", dict(ohne_auswahl, perspektiven=["Spiegel-Selfie"]), 0, 0))
    for lbl, _ in SH.PERSPEKTIVE:
        f.append(("perspective %s" % lbl, dict(selfie, perspektiven=[lbl]), 0, 0))
        f.append(("perspective %s, its framings" % lbl,
                  dict(selfie, perspektiven=[lbl], kameras=SH.PERSPEKTIVE_KAMERA[lbl]), 0, 0))
    for fam in PB.HALTUNG_GRUPPEN:
        f.append(("perspective on, posture family %s" % fam, dict(selfie, pools={"haltung": fam}), 0, 0))
    for fam in ("Selfie", "freundlich", ["freundlich", "Selfie"], "in sich gekehrt"):
        f.append(("perspective on, mood family %s" % fam, dict(selfie, pools={"stimmung": fam}), 0, 0))
        f.append(("perspective off, mood family %s" % fam, dict(ohne_auswahl, pools={"stimmung": fam}), 0, 0))
    for modus in SH.BLICK_MODI:
        f.append(("perspective on, gaze %s" % modus, dict(selfie, blick=modus), 0, 0))
        f.append(("perspective on, gaze %s, selfie moods" % modus,
                  dict(selfie, blick=modus, pools={"stimmung": "Selfie"}), 0, 0))
        f.append(("selfie moods without a selfie, gaze %s" % modus,
                  dict(ohne_auswahl, blick=modus, pools={"stimmung": "Selfie"}), 0, 0))
    for cat in ("haltung", "arme", "koerper", "blick"):
        f.append(("perspective on, pool %s none" % cat, dict(selfie, pools={cat: SH.NONE}), 0, 0))
    f.append(("perspective on, arc Freude", dict(selfie, bogen="Freude", reihenfolge="weit_nah"), 0, 0))
    f.append(("perspective on, camera off", dict(selfie, aktiv=dict(an, kamera=False)), 0, 0))
    f.append(("perspective on, pose off", dict(selfie, aktiv=dict(an, pose=False)), 0, 0))
    f.append(("perspective on, ratio off", dict(selfie, aktiv=dict(an, format=False)), 0, 0))
    f.append(("perspective on, detail and wide only", dict(selfie, kameras=["Detail", "Totale"]), 0, 0))
    f.append(("perspective on, 3 outfits mixed", dict(selfie, outfitFolge="gemischt"), 3, 0))
    st = dict(selfie, favoriten=[1, 2, 4], verworfen=[3])
    neu = SH.naechste_runde(st, 0)
    f.append(("perspective on, next round", neu, 0, neu["start"] - 1))
    # Sets and light (set_fuer(), licht_fuer()): every set list with blocks and
    # mixed, alone and with outfits and framing orders; every light order and
    # family pool; switched off; next rounds with sets.
    for sname, saetze in SAETZE.items():
        for folge in ("bloecke", "gemischt"):
            for ordnung in ("gezogen", "reihum", "weit_nah"):
                st = dict(ohne_auswahl, setFolge=folge, reihenfolge=ordnung, anzahl=12)
                f.append(("sets %s %s, %s" % (sname, folge, ordnung), st, 0, 0, saetze))
                f.append(("sets %s %s, %s, 3 outfits" % (sname, folge, ordnung), st, 3, 0, saetze))
                f.append(("sets %s %s, %s, 2 outfits mixed" % (sname, folge, ordnung),
                          dict(st, outfitFolge="gemischt"), 2, 0, saetze))
            for licht in ("je_set", "tageszeit", "gemischt", None, "gibt es nicht"):
                for pool in (SH.ALLE, "studio", "natuerlich", ["studio", "stimmung"], [], "gibt es nicht", None):
                    st = dict(ohne_auswahl, setFolge=folge, lichtFolge=licht, lichtPool=pool,
                              aktiv=dict(basis["aktiv"], licht=True), anzahl=10, start=41)
                    f.append(("light %s pool %s, sets %s %s" % (licht, pool, sname, folge), st, 0, 40, saetze))
        f.append(("sets %s, set axis off" % sname,
                  dict(ohne_auswahl, aktiv=dict(basis["aktiv"], set=False, licht=True),
                       lichtFolge="je_set"), 2, 0, saetze))
        f.append(("sets %s, light off" % sname, dict(ohne_auswahl, reihenfolge="weit_nah"), 0, 0, saetze))
        f.append(("sets %s, light without the key" % sname,
                  dict(ohne_auswahl, aktiv={"kamera": True}), 0, 0, saetze))
        f.append(("sets %s, arc Freude, time of day" % sname,
                  dict(ohne_auswahl, bogen="Freude", reihenfolge="weit_nah", lichtFolge="tageszeit",
                       aktiv=dict(basis["aktiv"], licht=True), anzahl=15), 0, 0, saetze))
        for anzahl, start in ((1, 1), (3, 7), (40, 2 ** 40)):
            f.append(("sets %s, %d from %d, time of day" % (sname, anzahl, start),
                      dict(ohne_auswahl, anzahl=anzahl, start=start, lichtFolge="tageszeit",
                           aktiv=dict(basis["aktiv"], licht=True)), 0, start - 1, saetze))
    for fav, weg in (([1, 5, 9], []), ([2], [7, 8])):
        st = dict(ohne_auswahl, favoriten=fav, verworfen=weg, reihenfolge="reihum")
        neu = SH.naechste_runde(st, 2, 3)
        f.append(("next round fav %s rej %s, 3 sets" % (fav, weg), neu, 2, neu["start"] - 1, [False, True, None]))
    # Both together: the Selfie recipe and the perspective axis with sets in
    # blocks and mixed and the light per set or over the day, and a next
    # round of a selfie series with sets.
    rezept = next(p for n, _, p in SH.REZEPTE if n == "Selfie")
    for sname in ("loft street park", "four mixed"):
        for folge in ("bloecke", "gemischt"):
            for licht in ("je_set", "tageszeit", "gemischt"):
                st = dict(basis, **json.loads(json.dumps(rezept)))
                st = dict(st, setFolge=folge, lichtFolge=licht, aktiv=dict(st["aktiv"], licht=True))
                f.append(("recipe Selfie, sets %s %s, light %s" % (sname, folge, licht), st, 0, 0, SAETZE[sname]))
                f.append(("recipe Selfie, sets %s %s, light %s, 2 outfits" % (sname, folge, licht),
                          st, 2, 0, SAETZE[sname]))
        f.append(("perspective on, sets %s, wide to close" % sname,
                  dict(selfie, reihenfolge="weit_nah", anzahl=12), 0, 0, SAETZE[sname]))
    st = dict(selfie, favoriten=[1, 3, 6], verworfen=[2], reihenfolge="reihum",
              aktiv=dict(an, licht=True))
    neu = SH.naechste_runde(st, 2, 3)
    f.append(("perspective on, next round, 3 sets", neu, 2, neu["start"] - 1, [False, True, None]))
    # Camera angles (3.1a) and hand props (3.2) in the planner.
    winkel = dict(selfie, perspektiven=list(SH.PERSPEKTIVE_GRUPPEN["Kamerawinkel"]))
    f.append(("camera angles, all", winkel, 0, 0))
    f.append(("camera angles, Vogelperspektive with standing pool",
              dict(selfie, perspektiven=["Vogelperspektive"], pools={"haltung": "stehend"}), 0, 0))
    f.append(("props on, all framings", dict(ohne_auswahl, requisiten=True), 0, 0))
    f.append(("props on, squatting pool", dict(ohne_auswahl, requisiten=True, pools={"haltung": "kniend"}), 0, 0))
    f.append(("props on, selfie on", dict(selfie, requisiten=True), 0, 0))
    return f


def main():
    ziel = sys.argv[1]
    aus = {"presets": api.presets()["shooting"], "faelle": []}
    for name, state, outfits, erster, *rest in faelle():
        saetze = rest[0] if rest else []
        laeufe = []
        for lauf in range(erster, erster + LAEUFE):
            p = SH.plane(state, lauf, outfits, len(saetze))
            laeufe.append({"lauf": lauf, "plan": p,
                           "format": SH.format_fuer(p["kamera"], lauf, state, p["perspektive"]),
                           "masse": list(SH.masse(p["kamera"], lauf, state, p["perspektive"])),
                           "outfit": SH.outfit_fuer(state, lauf, outfits),
                           "set": SH.set_fuer(state, lauf, len(saetze)),
                           "licht": SH.licht_fuer(state, lauf, saetze)})
        aus["faelle"].append({"name": name, "state": state, "outfits": outfits, "saetze": saetze,
                              "laeufe": laeufe})
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(aus, fh, ensure_ascii=False)


if __name__ == "__main__":
    main()
