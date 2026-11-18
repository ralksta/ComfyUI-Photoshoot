"""
Smoke test - runs without a running ComfyUI.

    python tests/smoke.py

Checks what can go wrong at startup and what ComfyUI only ever reports as
"Failed to import": importing the package, every INPUT_TYPES, whether the
preset response can be serialised, and whether a photoshoot run hands back
values in the promised shape.

folder_paths and aiohttp are deliberately NOT stubbed in: the package has to
stay importable without them, or a missing ComfyUI dependency takes every node
down with it instead of just the preset route.
"""

import importlib.util
import json
import pathlib
import sys
import types

WURZEL = pathlib.Path(__file__).resolve().parent.parent


def lade_paket():
    """Load the package - the directory name contains hyphens."""
    sys.modules.setdefault(
        "folder_paths",
        types.SimpleNamespace(get_user_directory=lambda: str(WURZEL / "tests" / "_tmp")),
    )
    spec = importlib.util.spec_from_file_location(
        "krea2kit", WURZEL / "__init__.py", submodule_search_locations=[str(WURZEL)]
    )
    modul = importlib.util.module_from_spec(spec)
    sys.modules["krea2kit"] = modul
    spec.loader.exec_module(modul)
    return modul


def i18n_ui():
    return importlib.import_module("krea2kit.nodes.i18n").UI


def main():
    kit = lade_paket()

    assert kit.WEB_DIRECTORY == "./js"
    assert len(kit.NODE_CLASS_MAPPINGS) == 22, len(kit.NODE_CLASS_MAPPINGS)
    assert set(kit.NODE_CLASS_MAPPINGS) == set(kit.NODE_DISPLAY_NAME_MAPPINGS)
    print("Nodes: %d" % len(kit.NODE_CLASS_MAPPINGS))

    # The most common place to crash at startup. As a side effect the load
    # nodes create their store folders - which is why folder_paths points at
    # tests/_tmp above.
    for name, cls in kit.NODE_CLASS_MAPPINGS.items():
        assert cls.INPUT_TYPES(), name
        assert cls.CATEGORY == "Photoshoot", name
    print("INPUT_TYPES: ok")

    # The interfaces fetch this over /krea2/presets. Whatever does not survive
    # json here arrives there as an empty panel.
    api = importlib.import_module("krea2kit.nodes.api")
    daten = json.dumps(api.presets(), ensure_ascii=False)
    assert len(daten) > 10000, len(daten)
    print("Presets: %d Bytes JSON" % len(daten))

    person_data = json.dumps({
        "gender": "woman", "figure": "hourglass figure", "bust": "full bust",
        "hair": "long {c} hair", "hairColor": "black", "eyeshadow": "bronze eyeshadow",
        "hosiery": "pantyhose", "hosieryColor": "black", "free": "wearing a coat",
    })

    # Framing-dependent shortening: no eyeshadow may come out of a wide shot,
    # but the silhouette still may.
    peb = importlib.import_module("krea2kit.nodes.person_builder")
    assert api.presets()["person"]["mindestalter"] == peb.MINDESTALTER
    p = json.loads(person_data)
    voll = peb.compose_person(p, peb.DETAIL_VOLL)
    ident = peb.compose_person(p, peb.DETAIL_IDENTITAET)
    assert "bronze eyeshadow" in voll and "bronze eyeshadow" not in ident
    assert "hourglass" in ident and "full bust" not in ident
    assert peb.detail_fuer_kamera("Totale") == peb.DETAIL_IDENTITAET
    assert peb.detail_fuer_kamera("Porträt") == peb.DETAIL_OBEN
    print("Detailstufen: voll %d, Identitaet %d Zeichen" % (len(voll), len(ident)))

    # The exact-age field is free text and has a floor. Below it, and at every
    # detail level, the prompt must never say an age under MINDESTALTER.
    for eingabe in ("12", "3", "17", " 8 Jahre"):
        for stufe in (peb.DETAIL_VOLL, peb.DETAIL_FIGUR, peb.DETAIL_IDENTITAET):
            text = peb.compose_person(dict(p, ageExact=eingabe), stufe)
            assert "%d-year-old" % peb.MINDESTALTER in text or "%d years old" % peb.MINDESTALTER in text, \
                "Alter nicht begrenzt: %r -> %s" % (eingabe, text)
    assert "a 34-year-old woman" in peb.compose_person(dict(p, ageExact="34"))
    assert "34 years old" in peb.compose_person({"ageExact": "34"})
    assert "years old" not in peb.compose_person(dict(p, ageExact=""))
    # The presets on their own cannot describe a minor either.
    assert not [v for _, v in peb.PRESETS["age"]
                if any(z in v for z in ("teen", "10s", "child", "{child}", "{teen}"))]
    print("Altersgrenze: ab %d, Vorgaben ab Anfang 20" % peb.MINDESTALTER)

    # Docking API for optional packs.
    dock = importlib.import_module("krea2kit.nodes.dock")
    getauscht = dock.person_aus_data(person_data, free_neu="wearing a red dress")
    assert "wearing a red dress" in getauscht
    assert "pantyhose" in getauscht, "Strumpf gehoert dem Person Builder"
    assert "pantyhose" not in dock.person_aus_data(person_data, kleidung_strip=True)
    assert "wearing a coat" not in getauscht
    assert dock.pose_anhaengen("standing,", ", leaning back") == "standing, leaning back"
    assert dock.parse_person_data("kein json") == {}
    print("Docking: ok")

    # A run has to be reproducible - same counter, same photo.
    sh = importlib.import_module("krea2kit.nodes.shooting")
    pbm = importlib.import_module("krea2kit.nodes.pose_builder")
    node = kit.NODE_CLASS_MAPPINGS["Krea2Photoshooting"]()
    zustand_d = sh.DEFAULT_STATE
    zustand = json.dumps(zustand_d)
    a = node.shoot(foto=8, ShootingState=zustand, person_data=person_data)
    b = node.shoot(foto=8, ShootingState=zustand, person_data=person_data)
    assert a == b, "Durchlauf nicht reproduzierbar"
    assert len(a) == len(node.RETURN_TYPES) == len(node.RETURN_NAMES)
    assert a[3] > 0 and a[4] > 0, "Bildmasse"
    assert a[8] in [lbl for lbl, _ in sh.KAMERA], a[8]
    # Photo 8 is run 7 - and photo 0, as workflows saved before the widget
    # was 1-based still send it, is the first photo just like photo 1.
    assert a[8] == sh.plane(zustand_d, 7)["kamera"]
    assert a[5] == sh.bildseed(7, zustand_d)
    # Take 0 is the seed as it always was; a re-shoot of photo 8 keeps the
    # plan (everything but the seed) and gets a different seed.
    assert sh.bildseed(7, zustand_d) == (7 * 2654435761) % (1 << 31)
    # Coverage: seven photos from any start number show every framing once.
    ab = dict(zustand_d, abdeckung=True, kameras=None)
    assert sorted(sh.plane(ab, l)["kamera"] for l in range(100, 107)) == sorted(l for l, _ in sh.KAMERA)
    # Recipes only name labels that exist, and every name is translated.
    i18n_mod = importlib.import_module("krea2kit.nodes.i18n")
    alle_kam = {l for l, _ in sh.KAMERA}
    alle_fok = {l for l, _ in sh.FOKUS}
    # The gaze chips of the panel: every mode named, and translated.
    assert set(sh.BLICK_NAMEN) == set(sh.BLICK_MODI)
    for name, beschreibung in sh.BLICK_NAMEN.values():
        assert name in i18n_mod.UI and beschreibung in i18n_mod.UI, name
    for name, beschreibung, patch in sh.REZEPTE:
        assert name in i18n_mod.UI and beschreibung in i18n_mod.UI, name
        assert set(patch.get("kameras") or []) <= alle_kam, name
        assert set(patch.get("fokusse") or []) <= alle_fok, name
        for feld, fam in (patch.get("pools") or {}).items():
            gruppen = pbm.HALTUNG_GRUPPEN if feld == "haltung" else importlib.import_module(
                "krea2kit.nodes.expression_builder").STIMMUNG_GRUPPEN
            assert fam in gruppen, (name, fam)
        assert sh.plane(dict(zustand_d, **patch), 0)["kamera"] in (patch.get("kameras") or alle_kam)
    EB_mod = importlib.import_module("krea2kit.nodes.expression_builder")
    # Dramaturgy: wide to close over the series, the last photo the closest,
    # from any start number; the mood arc goes through its four families.
    alle_kam = [l for l, _ in sh.KAMERA]
    for anzahl in (3, 7, 12, 30):
        dr = dict(zustand_d, reihenfolge="weit_nah", kameras=None, anzahl=anzahl, start=501)
        kams = [sh.plane(dr, 500 + i)["kamera"] for i in range(anzahl)]
        pos = [alle_kam.index(k) for k in kams]
        assert pos == sorted(pos, reverse=True) and kams[0] == "Totale" and kams[-1] == "Detail", (anzahl, kams)
        for bogen, stufen in sh.STIMMUNGSBOEGEN.items():
            db = dict(dr, bogen=bogen)
            for i in range(anzahl):
                st = sh.plane(db, 500 + i)["ausdruck"]["stimmung"]
                assert st in stufen[i * len(stufen) // anzahl], (bogen, anzahl, i, st)
    # Gaze modes of a series (state["blick"]): without one - or "gemischt" -
    # nothing changes, which keeps the JS preview in step.
    for lauf in range(200):
        assert sh.plane(zustand_d, lauf) == sh.plane(dict(zustand_d, blick="gemischt"), lauf), lauf
    alle_blick = {l for l, _ in EB_mod.PRESETS["blick"]}
    assert set(sh.BLICK_NICHT_ABGEWANDT) <= alle_blick and set(sh.BLICK_WEG_STIMMUNGEN) <= {l for l, _ in EB_mod.PRESETS["stimmung"]}
    kam, meist, weg = (dict(zustand_d, blick=m) for m in ("kamera", "meist_kamera", "abgewandt"))
    n_kam = n_meist = 0
    for lauf in range(300):
        pk, pm, pw = sh.plane(kam, lauf), sh.plane(meist, lauf), sh.plane(weg, lauf)
        if pk["ausdruck"].get("blick"):
            n_kam += 1
            assert pk["ausdruck"]["blick"] == sh.BLICK_KAMERA, (lauf, pk["ausdruck"])
            assert pk["ausdruck"].get("stimmung") not in sh.BLICK_WEG_STIMMUNGEN, (lauf, pk["ausdruck"])
        assert pk["pose"].get("koerper") != sh.ABGEWANDT, (lauf, pk["pose"])
        if pm["ausdruck"].get("blick") == sh.BLICK_KAMERA:
            n_meist += 1
        b = pw["ausdruck"].get("blick")
        assert b not in sh.BLICK_NICHT_ABGEWANDT, (lauf, b)
        assert not (pw["pose"].get("koerper") == "Über die Schulter gedreht" and b == "Über die Schulter"), lauf
    assert n_kam > 100, n_kam
    assert 150 <= n_meist <= 210, n_meist            # two in three of the 300 runs, minus the no-gaze views
    # Every mood of every arc exists, and every arc name is translated.
    alle_st = {l for l, _ in EB_mod.PRESETS["stimmung"]}
    for bogen, stufen in sh.STIMMUNGSBOEGEN.items():
        assert bogen in i18n_mod.UI, bogen
        assert all(set(st) <= alle_st for st in stufen), bogen
    assert sh.bogen_von({"bogen": True}) == "Freude" and sh.bogen_von({"bogen": "Aufbau"}) == "Freude"
    assert sh.bogen_von({}) is None
    # Every mood of an arc has its subject wording, and a series with an arc
    # puts it in front: the expression starts with the mood as the subject,
    # the person without its own "a woman".
    for stufen in sh.STIMMUNGSBOEGEN.values():
        for st in stufen:
            assert all(l in sh.STIMMUNG_ALS_SUBJEKT for l in st), st
    pd = json.dumps({"gender": "a woman", "age": "in {p} mid 20s", "trigger": "EileenX"})
    drama = dict(zustand_d, bogen="Drama", anzahl=4, start=1, kameras=["Porträt"])
    for f in range(1, 5):
        r = node.shoot(foto=f, ShootingState=json.dumps(drama), person_data=pd)
        koerper = sh.plane(drama, f - 1)["pose"].get("koerper")
        if koerper != sh.ABGEWANDT:
            assert r[1].startswith(("a ", "an ")) and " woman " in r[1], r[1]
            assert r[6].startswith("in her mid 20s, EileenX"), r[6]
    # An extreme close-up of the face gets the mood without gestures out of
    # frame - "both fists raised in the air" pulled the macro wide.
    assert set(sh.STIMMUNG_MAKRO) <= set(sh.STIMMUNG_ALS_SUBJEKT)
    for l in sh.STIMMUNG_ALS_SUBJEKT:
        makro = sh.stimmung_als_subjekt(l, pd, makro=True)
        assert makro.startswith(("a ", "an ")) and " woman" in makro, makro
        assert not sh._GESTE.search(makro), makro
    assert "fists" in sh.stimmung_als_subjekt("Triumphierend", pd)
    freude = dict(zustand_d, bogen="Freude", anzahl=8, start=1, reihenfolge="weit_nah")
    r = node.shoot(foto=8, ShootingState=json.dumps(freude), person_data=pd)
    assert sh.plane(freude, 7)["kamera"] == "Detail" and "fists" not in r[1], r[1]
    # Older states without "reihenfolge" keep their coverage.
    assert sh.reihenfolge({"abdeckung": True}) == "reihum" and sh.reihenfolge({}) == "gezogen"
    print("Rezepte: %d, Abdeckung: ok" % len(sh.REZEPTE))

    # Wardrobe: a chain of outfits, the person changes into them over the
    # series. The outfit replaces every clothing field, set or not - the
    # person's own jeans must not survive into a bikini.
    wr = importlib.import_module("krea2kit.nodes.wardrobe")
    wn = wr.Krea2Wardrobe()
    kette = wn.build(WardrobeState=json.dumps({"outfits": [
        {"id": "a", "name": "Rot", "felder": {"top": "Bardot-Top", "topColor": "Rot"}},
        {"id": "b", "name": " ", "felder": {"top": "Triangel-Bikini", "topColor": "Türkis",
                                              "bottom": "Bikinihöschen", "hair": "Lange Wellen"}}]}))[0]
    liste = wr.garderobe_lesen(kette)
    assert [o["name"] for o in liste] == ["Rot", "Outfit 2"], liste
    assert "hair" not in liste[1]["werte"], liste[1]  # not an outfit field
    assert liste[1]["werte"]["topColor"] == "turquoise", liste[1]
    assert wr.garderobe_lesen("kaputt") == [] and wr.garderobe_lesen(None) == []
    assert wr.garderobe_lesen(wn.build(WardrobeState=json.dumps(wr.DEFAULT_STATE))[0]) == \
        [{"name": "Outfit 1", "werte": {}}]
    # An older person that still carries clothing of its own renders as before;
    # with a Wardrobe on the Person node she wears its open tab instead, and the
    # wardrobe rides along in person_data for the series.
    pj = json.dumps(dict(json.loads(pd), bottom="light-wash blue skinny jeans", free="a red raincoat"))
    alt_state = json.dumps({"felder": {"gender": "Frau", "bottom": "Skinny Jeans"},
                            "texte": {"details": "wearing a red raincoat"}})
    person_node = peb.Krea2PersonBuilder()
    assert "jeans" in person_node.build(PersonState=alt_state)[0]
    angezogen, pw = person_node.build(PersonState=alt_state, garderobe=kette)
    assert "red Bardot" in angezogen and "jeans" not in angezogen and "raincoat" not in angezogen, angezogen
    assert len(json.loads(pw)["_garderobe"]) == 2
    zweiter = json.dumps(dict(json.loads(kette), aktiv=1))
    assert "triangle bikini" in person_node.build(PersonState=alt_state, garderobe=zweiter)[0]
    assert "garderobe" in person_node.INPUT_TYPES()["optional"]
    assert "garderobe" not in node.INPUT_TYPES()["optional"]
    zw = dict(zustand_d, anzahl=6, start=1, kameras=["Halbtotale"])
    blockweise = [sh.outfit_fuer(zw, l, 2) for l in range(6)]
    assert blockweise == [0, 0, 0, 1, 1, 1], blockweise
    gemischt = [sh.outfit_fuer(dict(zw, outfitFolge="gemischt"), l, 2) for l in range(40)]
    assert set(gemischt) == {0, 1}, gemischt
    # Every draw has a step of its own: no slot in use wraps around the prime
    # list. The outfit's slot once wrapped onto the camera's, and with two
    # outfits drawn per photo one got only the close framings, the other only
    # the wide ones.
    slots = list(range(len(sh.FELDER))) + [len(sh.FELDER) + k for k in (1, 2, 3, 4, 5)]
    assert (sh.PLATZ_SET, sh.PLATZ_LICHT) == (len(sh.FELDER) + 4, len(sh.FELDER) + 5)
    assert max(slots) < len(sh._WURZELN), (max(slots), len(sh._WURZELN))
    schritte = [sh._schritt(s) for s in slots]
    assert len(set(schritte)) == len(schritte), schritte
    assert sh._schritt(len(sh.FELDER) + 3) not in {sh._schritt(s) for s in range(len(sh.FELDER))}
    # The first sixteen primes keep their places, or every series ever shot
    # changes.
    assert sh._WURZELN[:16] == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]
    nah_weit = {"Detail", "Nahaufnahme", "Porträt"}, {"Amerikanisch", "Ganzkörper", "Totale"}
    gm = dict(zustand_d, outfitFolge="gemischt", kameras=None, reihenfolge="gezogen")
    for zahl in (2, 3):
        gesehen = {}
        for l in range(400):
            k = sh.plane(gm, l, zahl)["kamera"]
            gesehen.setdefault(sh.outfit_fuer(gm, l, zahl), set()).add(k)
        assert sorted(gesehen) == list(range(zahl)), gesehen
        for o, kams in gesehen.items():
            assert kams & nah_weit[0] and kams & nah_weit[1], (zahl, o, kams)
    assert sh.outfit_fuer(dict(zw, aktiv=dict(zw["aktiv"], outfit=False)), 0, 2) is None
    assert sh.outfit_fuer(zw, 0, 0) is None
    r1 = node.shoot(foto=1, ShootingState=json.dumps(zw), person_data=pw)
    r6 = node.shoot(foto=6, ShootingState=json.dumps(zw), person_data=pw)
    assert "red Bardot" in r1[6] and "jeans" not in r1[6] and "raincoat" not in r1[6], r1[6]
    assert "triangle bikini" in r6[6] and "Bardot" not in r6[6], r6[6]
    assert "triangle bikini" in json.loads(r6[7])["top"]
    # Without a wardrobe nothing changes; with the axis off the person keeps
    # the open tab throughout.
    ohne = node.shoot(foto=6, ShootingState=json.dumps(zw), person_data=pj)
    aus = node.shoot(foto=6, ShootingState=json.dumps(dict(zw, aktiv=dict(zw["aktiv"], outfit=False))),
                     person_data=pw)
    assert "jeans" in ohne[6] and "red Bardot" in aus[6], (ohne[6], aus[6])
    # In blocks, framings in turn and wide-to-close start over with every
    # outfit - one outfit got all the close-ups before (12-photo test).
    alle_kam = [l for l, _ in sh.KAMERA]
    wn12 = dict(zw, anzahl=12, kameras=None, reihenfolge="weit_nah")
    kams = [sh.plane(wn12, l, 3)["kamera"] for l in range(12)]
    weitest, naechst = alle_kam[-1], alle_kam[0]
    assert kams[0::4] == [weitest] * 3 and kams[3::4] == [naechst] * 3, kams
    rh12 = dict(wn12, reihenfolge="reihum")
    assert [sh.plane(rh12, l, 3)["kamera"] for l in (0, 4, 8)] == [alle_kam[0]] * 3
    # Mixed outfits, or no wardrobe: the series order as before.
    assert [sh.plane(wn12, l)["kamera"] for l in range(12)] == \
        [sh.plane(dict(wn12, outfitFolge="gemischt"), l, 3)["kamera"] for l in range(12)]
    # 7 photos, 3 outfits: blocks of 3, 2, 2, the same split as outfit_fuer().
    assert [sh._im_block(dict(zw, anzahl=7), l, 3) for l in range(7)] == \
        [(0, 3), (1, 3), (2, 3), (0, 2), (1, 2), (0, 2), (1, 2)]
    assert [sh.outfit_fuer(dict(zw, anzahl=7), l, 3) for l in range(7)] == [0, 0, 0, 1, 1, 2, 2]
    # The outfit preview: the exact texts of the render test (strumpf3_test,
    # 2026-09). A change here needs a new render test - the tights dropped out
    # of the mannequin with a single extra clause.
    e_outfit = {"felder": {"top": "Geripptes Crop Top", "topColor": "Grau", "bottom": "Minirock",
                           "bottomColor": "Schwarz", "bottomMaterial": "Leder",
                           "hosiery": "Strumpfhose matt", "hosieryColor": "Schwarz",
                           "shoes": "Kniehohe Stiefel", "shoesColor": "Schwarz"}}
    puppe = wr.vorschau_aus_state(e_outfit)  # one outfit of the state
    assert puppe.startswith("{extra}clean modern fashion e-commerce product photograph, full length shot"), puppe
    assert ("a faceless light grey fashion store mannequin standing on a small round stand, its legs covered "
            "in black matte pantyhose from the waist down to the toes, wearing a grey") in puppe, puppe
    assert puppe.endswith("wearing black knee-high heeled boots, arms at the sides"), puppe
    flach = wr.vorschau_aus_state(e_outfit, "flach")
    assert ("an outfit laid out neatly side by side: a grey sleeveless crew-neck crop top in tight vertical "
            "rib knit, a black leather mini skirt, and black knee-high heeled boots, and black matte pantyhose "
            "laid out flat to full length with the waistband and both sewn-in feet visible, no person") in flach, flach
    for label, erwartet in (("Halterlose Strümpfe", "reaching up the thighs"), ("Kniestrümpfe", "feet and lower legs"),
                            ("Leggings", "down to the ankles"), ("Netzstrumpfhose", "down to the toes")):
        t = wr.vorschau_aus_state({"felder": {"top": "Basic Crop Top", "hosiery": label}})
        assert erwartet in t, (label, t)
    assert "stretched" not in flach and "turned" not in puppe
    assert wr.vorschau_aus_state({"felder": {}}) is None
    assert "bare legs" not in wr.vorschau_aus_state({"felder": {"top": "Basic Crop Top", "hosiery": "Nackte Beine"}})
    print("Garderobe: ok")

    # Selects -> next round (naechste_runde()). The favourites say which
    # framings, families, focus areas and outfits the next round keeps.
    ebm = importlib.import_module("krea2kit.nodes.expression_builder")
    fam_p = lambda l: next(f for f, ls in pbm.HALTUNG_GRUPPEN.items() if l in ls)
    fam_a = lambda l: next(f for f, ls in ebm.STIMMUNG_GRUPPEN.items() if l in ls)
    r1 = dict(zustand_d, anzahl=12, start=101, kameras=None, fokusse=None,
              favoriten=[101, 104, 107, 3], takes={"104": 2}, wahl={"104": 1})
    favs = [sh.plane(r1, nr - 1) for nr in (101, 104, 107)]   # photo 3 is not in this series
    r2 = sh.naechste_runde(r1)
    assert r2 == sh.naechste_runde(json.loads(json.dumps(r1))), "reproducible"
    assert set(r2["kameras"] or alle_kam) == {p["kamera"] for p in favs}, r2["kameras"]
    assert set(r2["fokusse"]) == {p["fokus"] for p in favs} - {None}, r2["fokusse"]
    for feld, quelle, fam in (("haltung", "pose", fam_p), ("stimmung", "ausdruck", fam_a)):
        soll = {fam(p[quelle][feld]) for p in favs}
        ist = r2["pools"][feld]
        assert set(ist if isinstance(ist, list) else [ist]) == soll, (feld, ist, soll)
    assert r2["start"] == 113 and r2["runde"] == 2
    assert r2["favoriten"] == [] and r2["takes"] == {} and r2["wahl"] == {} and r2["verworfen"] == []
    assert r2["runden"] == [{k: v for k, v in r1.items() if k != "runden"}]
    # Every photo of the next round draws only from what the favourites showed.
    for l in range(112, 124):
        p = sh.plane(r2, l)
        assert p["kamera"] in r2["kameras"] and fam_p(p["pose"]["haltung"]) in r2["pools"]["haltung"], p
    # No selects: no next round. Favourites outside the series do not count.
    assert sh.naechste_runde(dict(r1, favoriten=[])) is None
    assert sh.naechste_runde(dict(r1, favoriten=[1, 500])) is None
    # One favourite: one framing, one family - and the pool is a plain name.
    ein = sh.naechste_runde(dict(r1, favoriten=[105]))
    p5 = sh.plane(r1, 104)
    assert ein["kameras"] == [p5["kamera"]] and ein["pools"]["haltung"] == fam_p(p5["pose"]["haltung"])
    # Switched-off axes, NONE pools and a mood arc stay as they are.
    aus = sh.naechste_runde(dict(r1, aktiv=dict(r1["aktiv"], kamera=False, pose=False),
                                 pools={"stimmung": sh.NONE}))
    assert aus["kameras"] is None and aus["pools"] == {"stimmung": sh.NONE}, aus["pools"]
    bg = sh.naechste_runde(dict(r1, bogen="Freude"))
    assert "stimmung" not in bg["pools"] and bg["bogen"] == "Freude"
    # A recipe's family pool narrows within itself (Lookbook: standing).
    lb = dict(r1, **json.loads(json.dumps(sh.REZEPTE[1][2])))
    assert sh.naechste_runde(dict(lb, start=101, favoriten=[101, 102]))["pools"]["haltung"] == "stehend"
    # Rejects: a value goes only when no kept photo of the series shows it.
    plaene = {nr: sh.plane(r1, nr - 1) for nr in range(101, 113)}
    weg_nr = 106
    weg = sh.naechste_runde(dict(r1, favoriten=[], verworfen=[weg_nr]))
    k = plaene[weg_nr]["kamera"]
    sonst = any(p["kamera"] == k for nr, p in plaene.items() if nr != weg_nr)
    assert (k in (weg["kameras"] or alle_kam)) == sonst, (k, weg["kameras"])
    # A favourite beats a reject of the same photo.
    beide = sh.naechste_runde(dict(r1, favoriten=[106], verworfen=[106]))
    assert beide["kameras"] == [k]
    # Outfits: the favourites' outfits, and the subset plans in blocks.
    o3 = dict(r1, favoriten=[101, 102], outfitFolge="bloecke")   # both in outfit 0 of 3
    ro = sh.naechste_runde(o3, 3)
    assert ro["outfitAuswahl"] == [0], ro["outfitAuswahl"]
    assert {sh.outfit_fuer(ro, l, 3) for l in range(112, 124)} == {0}
    assert sh.outfit_auswahl({"outfitAuswahl": [2, 0]}, 3) == [0, 2]
    assert sh.outfit_auswahl({"outfitAuswahl": [7]}, 3) == [0, 1, 2]
    assert [sh.outfit_fuer(dict(zw, outfitAuswahl=[0, 2]), l, 3) for l in range(6)] == [0, 0, 0, 2, 2, 2]
    # Families as a list: the union of both families.
    zwei = dict(zustand_d, pools={"haltung": ["kniend", "liegend"]})
    erlaubt = set(pbm.HALTUNG_GRUPPEN["kniend"]) | set(pbm.HALTUNG_GRUPPEN["liegend"])
    assert {sh.plane(zwei, l)["pose"]["haltung"] for l in range(60)} <= erlaubt
    # The round history is bounded; the newest round is last.
    st = dict(r1)
    for runde in range(2, sh.MAX_RUNDEN + 5):
        st = sh.naechste_runde(dict(st, favoriten=[st["start"]]))
        assert st["runde"] == runde and len(st["runden"]) == min(runde - 1, sh.MAX_RUNDEN)
    assert st["runden"][-1]["runde"] == st["runde"] - 1
    assert all("runden" not in r for r in st["runden"])
    print("Naechste Runde: ok")
    # A macro of the feet carries no arms, placement or face - the full pose
    # outvoted the macro and the whole figure came out (recipe test, photo 5006).
    fuss = dict(zustand_d, kameras=["Detail"], fokusse=["Füße"])
    for f in range(1, 9):
        r = node.shoot(foto=f, ShootingState=json.dumps(fuss))
        assert "macro shot of feet" in r[2], r[2]
        assert r[1] == "" and "window" not in r[0] and "arms" not in r[0] and "hand" not in r[0], r[:2]
    # ... and no lying or reclining base posture, which spread the figure out.
    for f in range(1, 40):
        plan = sh.plane(fuss, f - 1)
        r = node.shoot(foto=f, ShootingState=json.dumps(fuss))
        if plan["pose"].get("haltung") not in sh.FUSS_HALTUNGEN:
            assert "lying" not in r[0] and "reclin" not in r[0], r[0]
    auge = dict(zustand_d, kameras=["Detail"], fokusse=["Augen"])
    r = node.shoot(foto=3, ShootingState=json.dumps(auge))
    assert r[0] == "" and r[1], r[:2]
    # Close framings: no base posture, placement, legs or tension - only the
    # turn of the body and the arms; the expression stays whole.
    for kam in ("Nahaufnahme", "Porträt"):
        nah = dict(zustand_d, kameras=[kam], fokusse=None)
        for f in range(1, 25):
            r = node.shoot(foto=f, ShootingState=json.dumps(nah))
            plan = sh.plane(nah, f - 1)
            erlaubt = {_w for c, _w in ((c, sh._wert(pbm, c, plan["pose"].get(c))) for c in ("koerper", "arme")) if _w}
            rest = [sh._wert(pbm, c, plan["pose"].get(c)) for c in ("haltung", "raum", "beine", "spannung")]
            assert not any(x and x in r[0] and not any(x in e for e in erlaubt) for x in rest), (kam, f, r[0])
            assert r[1] or plan["pose"].get("koerper") == sh.ABGEWANDT, (kam, f)
    print("Makro zeigt nur Sichtbares: ok")
    # Saved series: stored in the user folder, only known keys, a hostile name
    # cannot leave the folder, delete removes it again.
    store = importlib.import_module("krea2kit.nodes.store")
    gespeichert = store.serie_speichern("../Mein Lookbook", {"anzahl": 5, "start": 77, "takes": {"1": 2}, "evil": 1})
    assert gespeichert == "Mein Lookbook"
    eintrag = [x for x in store.serien_liste() if x["name"] == "Mein Lookbook"]
    assert eintrag and eintrag[0]["patch"] == {"anzahl": 5, "start": 77}, eintrag
    store.serie_loeschen("Mein Lookbook")
    assert not [x for x in store.serien_liste() if x["name"] == "Mein Lookbook"]
    try:
        store.serie_speichern("../../", {})
        raise AssertionError("leerer Name angenommen")
    except ValueError:
        pass
    print("Serien speichern: ok")
    nochmal = node.shoot(foto=8, ShootingState=json.dumps(dict(zustand_d, takes={"8": 1})),
                         person_data=person_data)
    assert nochmal[5] != a[5] and nochmal[:5] == a[:5] and nochmal[6:10] == a[6:10]
    assert node.shoot(foto=9, ShootingState=json.dumps(dict(zustand_d, takes={"8": 1})),
                      person_data=person_data)[5] == node.shoot(foto=9, ShootingState=zustand,
                                                                person_data=person_data)[5]
    assert node.shoot(foto=0, ShootingState=zustand) == node.shoot(foto=1, ShootingState=zustand)
    # Any number is a valid photo number, including what "randomize" produces.
    assert node.shoot(foto=2**63 + 5, ShootingState=zustand)[3] > 0
    # A broken state must not get through.
    assert node.shoot(foto=1, ShootingState="{kaputt")
    assert node.shoot(foto=1, ShootingState=zustand, person_data="kein json")[6] == ""
    print("Photoshooting: %s, %dx%d, reproduzierbar" % (a[8], a[3], a[4]))

    # Draft and file name, the two outputs appended in 2.7.0. A draft is the
    # same photo - plan, size, seed - with refine off and "_draft" on the file.
    # szene and licht, appended after them, stay empty until a set or the
    # light axis is configured.
    assert len(a) == 16 and a[9] is True and a[13:15] == ("", "") and a[15], a[9:]
    assert a[10] == "photoshoot/s0001/08_t1", a[10]
    entwurf = node.shoot(foto=8, ShootingState=json.dumps(dict(zustand_d, entwurf=True)),
                         person_data=person_data)
    assert entwurf[:9] == a[:9] and entwurf[9] is False
    assert entwurf[10] == "photoshoot/s0001/08_t1_draft", entwurf[10]
    assert nochmal[10] == "photoshoot/s0001/08_t2", nochmal[10]
    # Padded to the widest number of the series, so the files sort in order;
    # the folder is the start number, a bad folder name falls back.
    assert sh.dateiname(dict(zustand_d, start=95, anzahl=12), 99) == "photoshoot/s0095/100_t1"
    assert sh.dateiname(dict(zustand_d, start=95, anzahl=12), 94) == "photoshoot/s0095/095_t1"
    assert sh.dateiname(dict(zustand_d, ordner="/../photoshoot/anchor/"), 0) == \
        "photoshoot/anchor/s0001/01_t1"
    assert sh.dateiname(dict(zustand_d, ordner=".."), 0) == "photoshoot/s0001/01_t1"
    # A state from before 2.7.0 knows neither key: refine on, default folder.
    alt = {k: v for k, v in zustand_d.items() if k not in ("entwurf", "ordner")}
    assert node.shoot(foto=3, ShootingState=json.dumps(alt))[9:11] == (True, "photoshoot/s0001/03_t1")
    print("Entwurf und Dateiname: ok")

    # The Location node (ROADMAP F1). No wording enters its PRESETS before a
    # render test: the one place it has is the example workflow's scene,
    # which every poster and measurement was rendered in. Extend GETESTET with
    # a wording only together with its verdict from tools/wortlabor/orte.json.
    ob = importlib.import_module("krea2kit.nodes.location_builder")
    bw_spec = importlib.util.spec_from_file_location("bw_smoke", WURZEL / "tools" / "baue_workflow.py")
    bw = importlib.util.module_from_spec(bw_spec)
    bw_spec.loader.exec_module(bw)
    GETESTET = {bw.SZENE}
    for cat, liste in ob.PRESETS.items():
        for label, wert in liste:
            assert wert in GETESTET, "ungetestete Formulierung in location %s: %s" % (cat, label)
    assert set(ob.FOLGE) == set(ob.PRESETS) and set(ob.NUR_DRAUSSEN) <= set(ob.FOLGE)
    alle_orte = {l for l, _ in ob.PRESETS["ort"]}
    assert set().union(*ob.ORT_GRUPPEN.values()) == alle_orte, "Ort ohne Familie"
    assert set(ob.DRAUSSEN) | set(ob.DRINNEN) == set(ob.ORT_GRUPPEN) and not set(ob.DRAUSSEN) & set(ob.DRINNEN)
    loc = kit.NODE_CLASS_MAPPINGS["Krea2LocationBuilder"]()
    leer_szene, leer_daten = loc.build(seed=0)
    assert leer_szene == "" and json.loads(leer_daten)["saetze"][0]["text"] == ""
    assert loc.build(seed=1, LocationState="{kaputt")[0] == ""
    satz = lambda **k: dict(json.loads(json.dumps(ob.LEERER_SATZ)), **k)
    loft = satz(felder=dict(ob.LEERER_SATZ["felder"], ort="Sonniges Loft"))
    # Weather and season are outdoor fields: an indoor set leaves them out, an
    # outdoor set (by its family chip, the text free) keeps them, one of no
    # family too. A die on an empty list rolls nothing and breaks nothing.
    regen = dict(ob.LEERER_SATZ["felder"], wetter="light rain")
    strasse = satz(gruppe="stadt", felder=regen, details="a quiet street, old stone facades")
    unbekannt = satz(felder=regen, details="somewhere")
    innen_regen = satz(felder=dict(regen, ort="Sonniges Loft"), wuerfeln={"jahreszeit": True})
    st = {"saetze": [loft, strasse, unbekannt, innen_regen], "aktiv": 1}
    szene, daten = loc.build(seed=5, LocationState=json.dumps(st))
    saetze = json.loads(daten)["saetze"]
    assert szene == "light rain, a quiet street, old stone facades" == saetze[1]["text"], szene
    assert saetze[0]["text"] == bw.SZENE and saetze[0]["kurz"] == "a sunlit loft with tall windows"
    assert saetze[1]["kurz"] == "light rain, a quiet street", saetze[1]["kurz"]
    assert saetze[2]["text"] == "light rain, somewhere" and saetze[3]["text"] == bw.SZENE
    assert [x["draussen"] for x in saetze] == [False, True, None, False], saetze
    assert [x["familie"] for x in saetze] == ["innen", "stadt", None, "innen"]
    assert loc.build(seed=5, LocationState=json.dumps(st)) == (szene, daten)
    assert ob.saetze_lesen(daten) == [{k: x[k] for k in ("name", "text", "kurz", "familie", "draussen")}
                                      for x in saetze]
    assert ob.saetze_lesen("kein json") == [] and ob.saetze_lesen(None) == []
    # A rolled place with a family chip rolls within it - or not at all.
    for seed in range(20):
        assert ob.werte_von(satz(wuerfeln={"ort": True}, gruppe="innen"), seed)["ort"] == bw.SZENE
        assert ob.werte_von(satz(wuerfeln={"ort": True}, gruppe="natur"), seed)["ort"] == ""
    print("Location: %d Orte, %d Familien, Kopplung drinnen/draussen" % (len(alle_orte), len(ob.ORT_GRUPPEN)))

    # The set and light axes of the Series (ROADMAP F2, F3). Sets in blocks
    # like outfits, the framing order starts over with every set; the close
    # framings get the short form, a macro no set; the light is off unless
    # switched on and never puts outdoor light on an indoor set.
    lb = importlib.import_module("krea2kit.nodes.lighting_builder")
    setups = {l for l, _ in lb.PRESETS["setup"]}
    assert set(sh.LICHT_NUR_DRAUSSEN) <= setups and set(sh.LICHT_NUR_DRINNEN) <= setups
    assert not set(sh.LICHT_NUR_DRAUSSEN) & set(sh.LICHT_NUR_DRINNEN)
    for name, stufe in sh.TAGESLAUF:
        assert set(stufe) <= setups and name in i18n_ui(), name
        for d in (True, False, None):
            assert [l for l in stufe if sh.licht_passt(l, d)], (name, d)
    drei = json.dumps({"saetze": saetze[:3]})
    st12 = dict(zustand_d, anzahl=12, kameras=None, reihenfolge="weit_nah")
    laeufe = [node.shoot(foto=f, ShootingState=json.dumps(st12), person_data=person_data, ort_data=drei)
              for f in range(1, 13)]
    assert [sh.set_fuer(st12, l, 3) for l in range(12)] == [0] * 4 + [1] * 4 + [2] * 4
    kams = [r[8] for r in laeufe]
    assert kams[0::4] == ["Totale"] * 3 and kams[3::4] == ["Detail"] * 3, kams
    for r in laeufe:
        k = sh.set_fuer(st12, r[12] - 1, 3)
        soll = "" if r[8] == "Detail" else saetze[k]["kurz"] if r[8] in sh.SET_KURZ else saetze[k]["text"]
        assert r[13] == soll and r[14] == "", (r[8], r[13])
        assert (soll in r[11]) if soll else True
    # Without sets or with the axis off: the outputs and plan of before.
    ohne = [node.shoot(foto=f, ShootingState=json.dumps(st12), person_data=person_data) for f in range(1, 13)]
    assert all(r[13:15] == ("", "") and r[15] for r in ohne)
    aus_set = dict(st12, aktiv=dict(st12["aktiv"], set=False))
    assert [node.shoot(foto=f, ShootingState=json.dumps(aus_set), person_data=person_data, ort_data=drei)[:13]
            for f in range(1, 13)] == [r[:13] for r in ohne]
    # The light: on, per set, the same on every photo of a set and fitting it.
    for folge in ("je_set", "tageszeit", "gemischt"):
        an = dict(st12, lichtFolge=folge, anzahl=30, aktiv=dict(st12["aktiv"], licht=True))
        je_set = {}
        for lauf in range(30):
            label = sh.licht_fuer(an, lauf, [True, False])
            assert label in setups
            k = sh.set_fuer(an, lauf, 2)
            assert sh.licht_passt(label, [True, False][k]), (folge, lauf, label)
            je_set.setdefault(k, set()).add(label)
        if folge == "je_set":
            assert all(len(v) == 1 for v in je_set.values()), je_set
    tag = dict(st12, lichtFolge="tageszeit", anzahl=10, aktiv=dict(st12["aktiv"], licht=True))
    # The day from morning to night: the first photo in the morning stage, the
    # last at night, and an outdoor set never gets the window light.
    assert sh.licht_fuer(tag, 0, []) in sh.TAGESLAUF[0][1] and sh.licht_fuer(tag, 9, []) in sh.TAGESLAUF[-1][1]
    assert sh.licht_fuer(dict(tag, aktiv=dict(tag["aktiv"], set=False)), 0, [True]) in sh.TAGESLAUF[0][1]
    assert {sh.licht_fuer(tag, l, [True]) for l in range(2)} == {"Morgendämmerung"}
    studio_pool = dict(st12, lichtPool="studio", aktiv=dict(st12["aktiv"], licht=True))
    assert {sh.licht_fuer(dict(studio_pool, lichtFolge="gemischt"), l) for l in range(40)} <= set(lb.LICHT_GRUPPEN["studio"])
    r = node.shoot(foto=3, ShootingState=json.dumps(dict(tag, kameras=["Ganzkörper"])), person_data=person_data,
                   ort_data=drei)
    assert r[14] == dict(lb.PRESETS["setup"])[sh.licht_fuer(tag, 2, [False, True, None])], r[14]
    assert r[11].endswith(r[13] + ", " + r[14]), r[11]
    print("Set- und Lichtachse: Bloecke, Kurzform, Licht passt zum Set")

    # The example workflows are generated; regenerating them with the checked-in
    # core-node snapshot must give the shipped files byte for byte (no ComfyUI
    # needed). Run in its own process, it loads the package itself.
    import subprocess
    r = subprocess.run([sys.executable, str(WURZEL / "tools" / "baue_workflow.py"), "--pruefen"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    print(r.stdout.strip().splitlines()[-1])

    # The wording lab (tools/wortlabor.py): every candidate file loads, every
    # group builds its prompts through the real builders and Build Prompt,
    # each candidate's wording is in its own prompt exactly once, and the
    # flattened render graph matches the core-node snapshot. Own process too.
    r = subprocess.run([sys.executable, str(WURZEL / "tools" / "wortlabor.py"), "--pruefen"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    print(r.stdout.strip().splitlines()[-1])

    for skript in ("baue_locales.py", "setze_js_version.py", "schneide_vorschau.py"):
        r = subprocess.run([sys.executable, str(WURZEL / "tools" / skript), "--pruefen"],
                           capture_output=True, text=True)
        assert r.returncode == 0, "%s: %s%s" % (skript, r.stdout, r.stderr)
        zeile = r.stdout.strip().splitlines()[-1]
        print("Vorschau-Zuschnitt: ok" if skript == "schneide_vorschau.py" else zeile)

    # Camera and placement both say something about distance. When they
    # contradict each other, the model paints the person twice - once near, once
    # far. That actually happened, which is why this is here.
    eng = {"Detail", "Nahaufnahme", "Porträt"}
    fern = set(sh.KAMERA_RAUM["Totale"]) - set(sh.KAMERA_RAUM["Detail"])
    schlecht = [i for i in range(200)
                if sh.plane(zustand_d, i)["kamera"] in eng
                and sh.plane(zustand_d, i)["pose"].get("raum") in fern]
    assert not schlecht, "enge Einstellung mit entfernender Raumangabe: %s" % schlecht[:5]
    # Every framing has to leave at least one placement available.
    for lbl, _ in sh.KAMERA:
        assert sh.KAMERA_RAUM.get(lbl), "keine Raumangabe fuer %s" % lbl
    print("Kamera/Raum: 200 Laeufe ohne Widerspruch")

    # Base posture and body tension, same class of contradiction: "leaning
    # against a wall, curled up" wants a body upright and balled up at once.
    # Measured at 12% of a 200-run series before the coupling existed.
    for i in range(200):
        pose = sh.plane(zustand_d, i)["pose"]
        h, s = pose.get("haltung"), pose.get("spannung")
        if h and s:
            erlaubt = pbm.HALTUNG_SPANNUNG.get(h)
            assert erlaubt is None or s in erlaubt, \
                "Lauf %d: %s + %s" % (i, h, s)
    # Every posture has to leave at least one tension available, and every
    # label in the table has to exist - a typo would silently widen the pool.
    spannungen = {lbl for lbl, _ in pbm.PRESETS["spannung"]}
    for lbl, _ in pbm.PRESETS["haltung"]:
        erlaubt = pbm.HALTUNG_SPANNUNG.get(lbl)
        assert erlaubt, "keine Spannung fuer %s" % lbl
        unbekannt = set(erlaubt) - spannungen
        assert not unbekannt, "%s nennt unbekannte Spannung %s" % (lbl, unbekannt)
    unbekannte_haltung = set(pbm.HALTUNG_SPANNUNG) - {l for l, _ in pbm.PRESETS["haltung"]}
    assert not unbekannte_haltung, "Tabelle nennt unbekannte Haltung %s" % unbekannte_haltung

    # Arms and legs are coupled to the posture the same way. Both tables must
    # cover every posture, name only real labels, and never leave a pose with
    # nothing to draw from.
    haltungen = {l for l, _ in pbm.PRESETS["haltung"]}
    for name, tabelle, cat in (("HALTUNG_ARME", pbm.HALTUNG_ARME, "arme"),
                               ("HALTUNG_BEINE", pbm.HALTUNG_BEINE, "beine"),
                               ("HALTUNG_RAUM", pbm.HALTUNG_RAUM, "raum")):
        echte = {l for l, _ in pbm.PRESETS[cat]}
        assert set(tabelle) == haltungen, \
            "%s deckt nicht alle Haltungen: %s" % (name, haltungen ^ set(tabelle))
        for h, erlaubt in tabelle.items():
            assert erlaubt, "%s laesst %s ohne Auswahl" % (name, h)
            unbekannt = set(erlaubt) - echte
            assert not unbekannt, "%s/%s nennt %s" % (name, h, unbekannt)

    # 500 runs: no drawn arm or leg position may fall outside its posture.
    verstoesse = []
    for lauf in range(500):
        gezogen = (sh.plane(zustand_d, lauf).get("pose") or {})
        h = gezogen.get("haltung")
        for cat, tabelle in (("arme", pbm.HALTUNG_ARME), ("beine", pbm.HALTUNG_BEINE),
                             ("raum", pbm.HALTUNG_RAUM)):
            wert = gezogen.get(cat)
            if h and wert and wert not in tabelle.get(h, [wert]):
                verstoesse.append("%s + %s" % (h, wert))
    assert not verstoesse, "Haltung gegen Glieder: %s" % verstoesse[:5]
    print("Haltung/Raum/Arme/Beine: 500 Laeufe ohne Widerspruch")

    # Eyes, mouth and brows against the mood. Every restricted label must name
    # real families, and 500 runs must not draw a face that contradicts itself.
    ebm = importlib.import_module("krea2kit.nodes.expression_builder")
    familien = set(ebm.STIMMUNG_GRUPPEN)
    for (cat, label), erlaubt in ebm.STIMMUNG_NUR_FUER.items():
        assert label in {l for l, _ in ebm.PRESETS[cat]}, "%s/%s" % (cat, label)
        assert erlaubt <= familien, "%s/%s nennt %s" % (cat, label, erlaubt - familien)
    gesicht = []
    for lauf in range(500):
        a = sh.plane(zustand_d, lauf)["ausdruck"]
        fam = ebm.familie_von(a.get("stimmung"))
        for cat in ("augen", "mund", "brauen"):
            if not ebm.passt_zur_stimmung(cat, a.get(cat), fam):
                gesicht.append("%s + %s" % (a.get("stimmung"), a.get(cat)))
    assert not gesicht, "Stimmung gegen Gesicht: %s" % gesicht[:5]
    print("Stimmung/Gesicht: 500 Laeufe ohne Widerspruch")

    # A subject seen from behind has no visible face: no facial detail, no
    # focus on it, and no mood whose own wording names one.
    abgewandt = ruecken = 0
    for lauf in range(500):
        plan = sh.plane(zustand_d, lauf)
        if plan["pose"].get("koerper") != sh.ABGEWANDT:
            continue
        abgewandt += 1
        assert plan["fokus"] not in sh.FOKUS_GESICHT, \
            "Fokus %s bei abgewandter Figur" % plan["fokus"]
        text = node.shoot(foto=lauf + 1, ShootingState=zustand)[1]
        treffer = [w for w in sh.GESICHTSWOERTER if w in text.lower()]
        assert not treffer, "abgewandt, aber %s im Ausdruck: %s" % (treffer, text[:80])
        ruecken += 1
    print("Von hinten: %d Laeufe, kein Gesichtstext" % ruecken)
    print("Haltung/Spannung: 200 Laeufe ohne Widerspruch")

    # Every node name has to stand literally in the source. ComfyUI-Manager
    # reads them out of the syntax tree to build extension-node-map.json, the
    # table "Install Missing Custom Nodes" uses to find the pack that provides a
    # missing node. A computed key is invisible there - it once hid eight of the
    # fourteen nodes.
    quellen = "\n".join(f.read_text(encoding="utf-8")
                        for f in sorted((WURZEL / "nodes").glob("*.py")))
    unsichtbar = [n for n in kit.NODE_CLASS_MAPPINGS if '"%s"' % n not in quellen]
    assert not unsichtbar, "nicht woertlich im Quelltext: %s" % unsichtbar
    print("Node-Namen: %d, alle woertlich im Quelltext" % len(kit.NODE_CLASS_MAPPINGS))

    # Translation: every label the interface shows needs an English
    # equivalent. When one is missing, a German word stands in the English
    # panel - exactly the kind of fault nobody reports.
    i18n = importlib.import_module("krea2kit.nodes.i18n")
    eb = importlib.import_module("krea2kit.nodes.expression_builder")
    lb = importlib.import_module("krea2kit.nodes.lighting_builder")
    sb = importlib.import_module("krea2kit.nodes.style_builder")
    ob = importlib.import_module("krea2kit.nodes.location_builder")
    luecken = i18n.fehlend([("person", peb), ("ausdruck", eb), ("pose", pbm),
                            ("lighting", lb), ("style", sb), ("location", ob)])
    for lbl, _ in sh.KAMERA:
        if lbl not in i18n.SHOOTING["kamera"]:
            luecken.append("shooting/kamera/" + lbl)
    for lbl, _ in sh.FOKUS:
        if lbl not in i18n.SHOOTING["fokus"]:
            luecken.append("shooting/fokus/" + lbl)
    for lbl, _ in sh.PERSPEKTIVE:
        if lbl not in i18n.SHOOTING["perspektive"]:
            luecken.append("shooting/perspektive/" + lbl)
    for name in peb.FELDNAMEN.values():
        if name not in i18n.FELDNAMEN:
            luecken.append("feldname/" + name)
    # Row names go through the same table as the field names - a row label
    # without an entry stayed German in the interface (issue #2).
    for name in peb.ZEILENNAMEN.values():
        if name not in i18n.FELDNAMEN:
            luecken.append("zeilenname/" + name)
    for name, _ in peb.SEKTIONEN:
        if name not in i18n.SEKTIONEN:
            luecken.append("sektion/" + name)
    for tabelle in (peb.SCHUH_GRUPPEN, peb.OBERTEIL_GRUPPEN, peb.UNTERTEIL_GRUPPEN, peb.KOPF_GRUPPEN,
                    pbm.HALTUNG_GRUPPEN, eb.STIMMUNG_GRUPPEN, lb.LICHT_GRUPPEN, sb.LOOK_GRUPPEN,
                    ob.ORT_GRUPPEN, sh.PERSPEKTIVE_GRUPPEN):
        for fam in tabelle:
            if fam not in i18n.FAMILIEN:
                luecken.append("familie/" + fam)
    for cat in list(pbm.FOLGE) + list(eb.FOLGE) + list(lb.FOLGE) + list(sb.FOLGE) + list(ob.FOLGE):
        if cat not in i18n.KATEGORIEN:
            luecken.append("kategorie/" + cat)
    assert not luecken, "ohne Uebersetzung: %s" % luecken[:10]

    # Every string the panels show through uet(..., "ui") needs an entry in
    # i18n.UI, or it stays German in the English interface. The one that
    # slipped through was the second half of a two-line warning - which is
    # why this reads the calls out of the JS, ternaries included.
    import re
    aufruf = re.compile(r'\b(?:uet|uetf|t|tf)\(\s*((?:[^()]|\([^()]*\))*?),\s*"ui"', re.S)
    literal = re.compile(r'"((?:[^"\\]|\\.)*)"')
    ui_luecken = set()
    for js in sorted((WURZEL / "js").glob("*.mjs")):
        for m in aufruf.finditer(js.read_text(encoding="utf-8")):
            for k in literal.findall(m.group(1)):
                if k not in i18n.UI:
                    ui_luecken.add("%s: %s" % (js.name, k))
    assert not ui_luecken, "UI-Text ohne Uebersetzung: %s" % sorted(ui_luecken)[:5]
    print("UI-Texte: %d Schluessel, alle uebersetzt" % len(i18n.UI))

    # The other way round: translated labels that no longer exist. Those never
    # come to light otherwise, because a dead entry is simply never looked up.
    tab = i18n.tabelle()
    verwaist = []
    for schluessel, modul in (("person", peb), ("ausdruck", eb), ("pose", pbm),
                              ("lighting", lb), ("style", sb), ("location", ob)):
        for cat, uebersetzt in tab[schluessel].items():
            echte = {l for l, _ in modul.PRESETS.get(cat, [])}
            verwaist += ["%s/%s/%s" % (schluessel, cat, l)
                         for l in uebersetzt if l not in echte]
    assert not verwaist, "verwaiste Uebersetzung: %s" % verwaist[:10]
    zahl = sum(len(v) for m in ("person", "ausdruck", "pose", "lighting", "style", "location", "shooting")
               for v in tab[m].values())
    print("Uebersetzung: %d Labels, keine Luecke" % zahl)

    # The style node: the default is the text the example workflow used to
    # carry by hand, the look comes first, every family label is real, and a
    # rolled look with the family restricted stays inside that family.
    stil = kit.NODE_CLASS_MAPPINGS["Krea2StyleBuilder"]()
    vorgabe = stil.build(seed=0)[0]
    assert vorgabe.startswith("editorial photography, 85mm lens"), vorgabe
    sw = stil.build(seed=0, StyleState=json.dumps(dict(
        sb.DEFAULT_STATE, felder={"look": "Schwarzweiß klassisch", "genre": "Editorial",
                                  "optik": sb.NONE, "finish": "Feines Korn"})))[0]
    assert sw == "black and white photograph, monochrome, rich tonal range, " \
                 "editorial photography, fine film grain", sw
    assert stil.build(seed=3, StyleState="{kaputt")[0] == vorgabe
    looks = {l for l, _ in sb.PRESETS["look"]}
    for fam, labels in sb.LOOK_GRUPPEN.items():
        assert set(labels) <= looks, "%s nennt %s" % (fam, set(labels) - looks)
    assert set().union(*sb.LOOK_GRUPPEN.values()) == looks, "Look ohne Familie"
    gewuerfelt = json.dumps(dict(sb.DEFAULT_STATE, wuerfeln={"look": True},
                                 gruppe="schwarzweiss"))
    for seed in range(40):
        text = stil.build(seed=seed, StyleState=gewuerfelt)[0]
        kopf = text.split(", editorial photography")[0]
        assert "monochrome" in kopf, text
        assert any(w in kopf for w in ("black and white", "sepia", "selenium", "platinum")), text
        assert stil.build(seed=seed, StyleState=gewuerfelt)[0] == text
    print("Stil: %d Looks in %d Familien, Schwarzweiss bleibt Schwarzweiss"
          % (len(looks), len(sb.LOOK_GRUPPEN)))

    # Monochrome: a coloured tensor comes back with equal channels, a tint
    # keeps the ordering it promises, strength 0 changes nothing. Needs torch,
    # which the package must not require - so this part is skipped without it.
    try:
        import torch
    except ImportError:
        torch = None
        print("Schwarzweiss: torch fehlt, uebersprungen")
    if torch is not None:
        mono = importlib.import_module("krea2kit.nodes.mono")
        bild = torch.rand(2, 8, 8, 3)
        grau = mono.wandle_tensor(bild)
        assert grau.shape == bild.shape
        assert torch.allclose(grau[..., 0], grau[..., 1]) and torch.allclose(grau[..., 1], grau[..., 2])
        assert torch.allclose(mono.wandle_tensor(bild, staerke=0.0), bild)
        sepia = mono.wandle_tensor(bild, "Sepia (warm)")
        assert (sepia[..., 0] >= sepia[..., 2]).all()
        mit_alpha = mono.wandle_tensor(torch.rand(1, 4, 4, 4))
        assert mit_alpha.shape[-1] == 4
        assert kit.NODE_CLASS_MAPPINGS["Krea2Monochrome"]().wandle(bild)[0].shape == bild.shape
        print("Schwarzweiss: ok")

    # Placeholders and the recommended order. Build Prompt hands its prompt to
    # the history as well ("ui"), for the contact sheet's Prompt row.
    bauer = kit.NODE_CLASS_MAPPINGS["Krea2PromptJoin"]()
    antwort = bauer.join("{kamera}", kamera="A")
    assert antwort["ui"] == {"text": ["A"]} and antwort["result"] == ("A",), antwort

    class _Join:
        """The prompt alone, as the tests below want it."""
        def join(self, *a, **k):
            return bauer.join(*a, **k)["result"]
    join = _Join()
    text = "{kamera}, {szene}, {licht}, {person}, {pose}, {extra}, {ausdruck}, {stil}"
    assert join.join(text, kamera="A", szene="B", licht="L", person_1="C", pose="D",
                     ausdruck="E", stil="F")[0] == "A, B, L, C, D, E, F"
    # Placeholders left empty leave no orphaned commas behind.
    assert join.join("{kamera}, {szene}, {stil}", kamera="A", stil="F")[0] == "A, F"
    # The English spellings mean the same as the German ones.
    assert join.join("{camera}, {scene}, {lighting}, {person}, {expression}, {style}",
                     kamera="A", szene="B", licht="L", person_1="C", ausdruck="E",
                     stil="F")[0] == "A, B, L, C, E, F"
    ohne = join.join("", kamera="A", person_1="C", szene="B", licht="L", stil="S")[0]
    assert ohne.index("S") < ohne.index("A") < ohne.index("B") < ohne.index("L") \
        < ohne.index("C"), ohne
    print("Prompt bauen: ok")

    # "Inspire Me" (js/person.mjs) draws from INSPIRATION, delivered through
    # /krea2/presets. A label that is not a preset leaves its field empty -
    # most of the old JS pools had drifted that way unnoticed.
    insp = peb.INSPIRATION
    def _gibt(cat, label):
        return any(l == label for l, _ in peb.PRESETS[cat])
    tot = []
    for k, v in insp.items():
        if k in ("archetypen", "maenner") or not isinstance(v, list):
            continue
        cat = "figure" if k == "figureMann" else k
        tot += ["%s/%s" % (cat, l) for l in v if not _gibt(cat, l)]
    tot += ["gender/%s" % l for l in insp["maenner"] if not _gibt("gender", l)]
    for a in insp["archetypen"]:
        for k, v in a.items():
            if k == "merkmalChance":
                continue
            cat = "hair" if k == "hairMann" else k
            tot += ["%s/%s" % (cat, l) for l in ([v] if isinstance(v, str) else v)
                    if not _gibt(cat, l)]
    assert not tot, "Inspire Me: keine Vorgabe: %s" % tot[:8]
    assert api.presets()["person"]["inspiration"] == json.loads(json.dumps(insp)), \
        "inspiration fehlt in /krea2/presets"
    print("Inspire Me: %d Archetypen, alle Labels vorhanden" % len(insp["archetypen"]))

    # Tops: colour in front, the article fits the first word written, and the
    # garment appears once - the wording is the one that passed the render test.
    oben = {"gender": "a woman", "top": peb._val("top", "Off-Shoulder-Crop-Top")}
    assert peb.compose_person(oben).count("off-the-shoulder crop top") == 1
    assert "wearing an off-the-shoulder crop top" in peb.compose_person(oben)
    oben["topColor"] = peb._val("topColor", "Pastellblau")
    assert "wearing a pastel blue off-the-shoulder crop top" in peb.compose_person(oben)
    assert "crop top" in peb.compose_person(oben, peb.DETAIL_IDENTITAET)
    assert "crop top" not in peb.compose_person(oben, peb.DETAIL_FUESSE)
    assert sum(len(v) for v in peb.OBERTEIL_GRUPPEN.values()) == len(peb.PRESETS["top"])
    assert peb.OBERTEIL_GRUPPEN["Crop Tops"][-1] == "One-Shoulder-Crop-Top"
    assert peb.OBERTEIL_GRUPPEN["Bikini"][0] == "Triangel-Bikini"
    print("Oberteil: ok")

    # Bottoms: "with" after a top, "wearing" on their own, no article for plurals.
    unten = {"gender": "a woman", "top": peb._val("top", "Basic Crop Top"),
             "bottom": peb._val("bottom", "Minirock"), "bottomColor": peb._val("bottomColor", "Grau")}
    assert "crop tank top with wide shoulder straps, with a grey mini skirt" in peb.compose_person(unten)
    unten.update(top=None, bottom=peb._val("bottom", "Hotpants"))
    assert "wearing grey high-waisted hot pants" in peb.compose_person(unten)
    assert "hot pants" not in peb.compose_person(unten, peb.DETAIL_HAENDE)
    assert sum(len(v) for v in peb.UNTERTEIL_GRUPPEN.values()) == len(peb.PRESETS["bottom"])
    # Material between colour and cut; cuts with their own fabric ignore it.
    stoff = {"gender": "a woman", "bottom": peb._val("bottom", "Bleistiftrock knielang"),
             "bottomColor": peb._val("bottomColor", "Schwarz"), "bottomMaterial": peb._val("bottomMaterial", "Latex")}
    assert ("wearing a black high-gloss latex with a wet mirror-like shine and bright white specular highlights "
            "high-waisted knee-length pencil skirt") in peb.compose_person(stoff)
    stoff["bottom"] = peb._val("bottom", "Jeans-Shorts")
    assert "latex" not in peb.compose_person(stoff)
    # The first twelve bottoms keep their index (tiles are cut by position).
    assert peb.PRESETS["bottom"][11][0] == "Cargohose" and peb.PRESETS["bottom"][28][0] == "Flare-Leggings"
    assert peb.UNTERTEIL_GRUPPEN["Bikini"][0] == "Bikinihöschen"
    print("Unterteil: ok")

    # Every preset of a family field sits in exactly one family, and the families
    # name no label that does not exist. They are label lists, so an appended
    # preset has to be sorted in by hand.
    for cat, tabelle in (("shoes", peb.SCHUH_GRUPPEN), ("top", peb.OBERTEIL_GRUPPEN),
                         ("bottom", peb.UNTERTEIL_GRUPPEN), ("headwear", peb.KOPF_GRUPPEN)):
        assert peb.FELDART[cat] == "familie", cat
        labels = [l for l, _ in peb.PRESETS[cat]]
        in_fam = [l for ls in tabelle.values() for l in ls]
        assert sorted(in_fam) == sorted(labels), (cat, set(labels) ^ set(in_fam))
    assert [c for c, a in peb.FELDART.items() if a == "familie"] == ["shoes", "top", "bottom", "headwear"]
    print("Familien: ok")

    # Custom entries (eigene.py): the built-in lists pass the same check as an
    # import file, so the two formats cannot drift apart.
    eg = importlib.import_module("krea2kit.nodes.eigene")
    for b in ("person", "pose", "ausdruck", "lighting", "style", "location"):
        kern = eg.exportiere_kern(b)
        gut, m = eg.pruefe(kern, "kern", gegen_kern=False)
        assert not m and len(gut) == len(kern["entries"]), (b, m[:3])
    # One good file, one full of mistakes, one duplicate across files.
    import shutil
    tmp = WURZEL / "tests" / "_tmp" / "eigene_test"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    (tmp / "a_hueten.json").write_text(json.dumps({"format": eg.FORMAT, "name": "Hüte", "entries": [
        {"field": "headwear", "label": "Trilby", "prompt": "a narrow-brimmed  straw trilby", "en": "Trilby hat"},
        {"field": "headwear", "label": "Fascinator klein", "prompt": "a tiny fascinator", "group": "Hüte"},
        {"field": "topColor", "label": "Petrol", "prompt": "petrol blue", "hex": "#0f5e6b"},
        {"field": "hair", "label": "Shag", "prompt": "a choppy layered {c} shag cut"},
        {"builder": "lighting", "field": "setup", "label": "Neonröhre", "prompt": "a single bare neon tube"},
        {"builder": "expression", "field": "stimmung", "label": "Spitzbübisch grinsend", "prompt": "a mischievous grin"},
    ]}), encoding="utf-8")
    (tmp / "b_fehler.json").write_text(json.dumps({"entries": [
        {"field": "headwear", "label": "Fedora", "prompt": "x"},          # built-in label
        {"field": "age", "label": "Uralt", "prompt": "ancient"},           # locked field
        {"field": "hair", "label": "Kaputt", "prompt": "a {p} bob"},       # foreign placeholder
        {"field": "nope", "label": "X", "prompt": "x"},                    # unknown field
        {"field": "headwear", "label": "Trilby", "prompt": "other"},       # taken in a_
        {"field": "topColor", "label": "Schlamm", "prompt": "mud", "hex": "brown"},  # kept, no swatch
        {"builder": "robot", "field": "x", "label": "y", "prompt": "z"},   # unknown builder
    ]}), encoding="utf-8")
    (tmp / "c_kaputt.json").write_text("{ not json", encoding="utf-8")
    eg.lade([str(tmp)])
    assert len(eg.eintraege("person", "headwear")) == 2
    assert eg.wert("person", "headwear", "Trilby") == "a narrow-brimmed straw trilby"
    assert len(eg.MELDUNGEN) == 8, eg.MELDUNGEN
    assert any("c_kaputt.json" in m for m in eg.MELDUNGEN)
    assert [e["hex"] for e in eg.eintraege("person", "topColor")] == ["#0f5e6b", "#8e8e8e"]
    # The builders resolve them; hair keeps its colour placeholder.
    p = peb.werte_aus_state({"felder": {"gender": "Frau", "headwear": "Trilby", "hair": "Shag",
                                        "hairColor": "Rot / Kupfer"}})
    assert "wearing a narrow-brimmed straw trilby" in peb.compose_person(p)
    assert "shag cut" in peb.compose_person(p) and "{c}" not in peb.compose_person(p)
    assert lb._val("setup", "Neonröhre") == "a single bare neon tube"
    assert lb._val("setup", "Gibt es nicht") == "Gibt es nicht"   # as before
    assert eb._val("stimmung", "Spitzbübisch grinsend") == "a mischievous grin"
    # Without a "dice" file the pools are exactly the built-in ones.
    assert eg.wuerfelbar("ausdruck", "stimmung") == []
    assert sh._wert(eb, "stimmung", "Spitzbübisch grinsend") == "a mischievous grin"
    # The interface gets them marked, in their family or "Eigene", with the
    # English name and the swatch - without touching the module tables.
    d = api.presets()
    kopf = d["person"]["felder"]["headwear"]
    assert {"label": "Trilby", "wert": "a narrow-brimmed straw trilby", "eigen": True} in kopf
    assert "Trilby" in d["person"]["gruppen"]["headwear"][eg.FAMILIE]
    assert "Fascinator klein" in d["person"]["gruppen"]["headwear"]["Hüte"]
    assert d["i18n"]["person"]["headwear"]["Trilby"] == "Trilby hat"
    assert d["person"]["farben"]["topColor"]["Petrol"] == "#0f5e6b"
    assert "Petrol" not in peb.FARBWERTE["topColor"] and "Trilby" not in i18n.PERSON["headwear"]
    assert "Neonröhre" in d["lighting"]["gruppen"][eg.FAMILIE]
    assert d["custom"]["count"] == 7
    json.dumps(d, ensure_ascii=False)
    # A shared workflow: no file here, the state carries the prompt.
    eg.lade([])
    assert peb._val("headwear", "Trilby") is None
    p = peb.werte_aus_state({"felder": {"headwear": "Trilby"},
                             "eigene": {"headwear": {"Trilby": "a narrow-brimmed straw trilby"}}})
    assert p["headwear"] == "a narrow-brimmed straw trilby"
    assert pbm._val("haltung", "X", {"haltung": {"X": "crouching low"}}) == "crouching low"
    # Import through the user folder (folder_paths points at tests/_tmp).
    datei, m = eg.speichere("../Meine Hüte", {"entries": [
        {"field": "headwear", "label": "Trilby", "prompt": "a trilby"}]})
    assert datei == "Meine_Hüte.json" and not m, (datei, m)
    assert eg.wert("person", "headwear", "Trilby") == "a trilby"
    try:
        eg.speichere("Meine Hüte", {"entries": []})
        raise AssertionError("existing name overwritten")
    except FileExistsError:
        pass
    try:
        eg.speichere("leer", {"entries": [{"field": "age", "label": "x", "prompt": "y"}]})
        raise AssertionError("file without a valid entry saved")
    except ValueError:
        pass
    eg.loesche(datei)
    assert not eg.EINTRAEGE
    # Single-entry creator & prop mirroring (person/prop -> pose/arme).
    lbl, _m = eg.fuege_hinzu("person", "prop", "Sofortbildkamera", "a vintage Polaroid camera")
    assert lbl == "Sofortbildkamera"
    p_prop = api.presets()
    expected_prop = "holding a vintage Polaroid camera with both hands in front of her chest"
    assert any(e["label"] == "Sofortbildkamera" and e.get("eigen") and e["wert"] == expected_prop
               for e in p_prop["person"]["felder"]["prop"])
    assert any(e["label"] == "Sofortbildkamera" and e.get("eigen") and e["wert"] == expected_prop
               for e in p_prop["pose"]["felder"]["arme"])
    assert pbm._val("arme", "Sofortbildkamera") == expected_prop
    eg.entferne_eintrag("person", "prop", "Sofortbildkamera")
    assert not eg.EINTRAEGE
    shutil.rmtree(tmp, ignore_errors=True)
    # A built-in entry under its English name or in other case is a duplicate
    # too - the LLM prompt lists the English names.
    gut, m = eg.pruefe({"entries": [{"field": "headwear", "label": "Bucket hat", "prompt": "x"},
                                    {"field": "headwear", "label": "FEDORA", "prompt": "x"},
                                    {"field": "headwear", "label": "Zylinderchen", "prompt": "x"},
                                    {"field": "headwear", "label": "zylinderchen", "prompt": "y"}]})
    assert [e["label"] for e in gut] == ["Zylinderchen"] and len(m) == 3, m
    # The template names every built-in entry in English, with its family.
    vorlage = eg.exportiere_kern("person")["entries"]
    fischer = next(e for e in vorlage if e["label"] == "Fischerhut")
    assert fischer["en"] == "Bucket hat" and fischer["group"] == "hats", fischer
    # The commented example in docs/ loads without a single message, and its
    # families resolve by key, by English name or as a new family.
    beispiel = json.loads(pathlib.Path(eg.BEISPIEL).read_text(encoding="utf-8"))
    gut, m = eg.pruefe(beispiel, "beispiel")
    assert not m and len(gut) == len(beispiel["entries"]) == 10, m
    tmp.mkdir(parents=True)
    shutil.copy(eg.BEISPIEL, tmp / "beispiel.json")
    eg.lade([str(tmp)])
    d = api.presets()
    fam = lambda b, f, l: next(g for g, ls in (d[b]["gruppen"].get(f, d[b]["gruppen"])
                                               if b == "person" else d[b]["gruppen"]).items() if l in ls)
    assert fam("person", "headwear", "Trilby") == eg.FAMILIE
    assert api._familie("Custom", {"Hüte": []}) == eg.FAMILIE == api._familie("eigene", {})
    assert fam("person", "headwear", "Glitzer-Haarspange") == "Haarschmuck & Tücher"
    assert fam("person", "top", "Korsage mit Cape") == "Tops & Blusen"
    assert fam("person", "bottom", "Reifrock") == "Costume"
    assert fam("pose", None, "Auf einer Treppenstufe sitzend") == "sitzend"
    assert fam("ausdruck", None, "Spitzbübisch grinsend") == "freundlich"
    assert fam("lighting", None, "Neonröhre") == "stimmung"
    assert fam("style", None, "Superia abgelaufen") == "farbe"
    shutil.rmtree(tmp, ignore_errors=True)
    # First start: the user folder appears with the example as .txt, which is
    # not loaded; a deleted example is not put back.
    shutil.rmtree(eg.ordner(), ignore_errors=True)
    eg.lade()
    txt = pathlib.Path(eg.ordner()) / eg.BEISPIEL_NAME
    assert txt.is_file() and not eg.EINTRAEGE
    txt.unlink()
    eg.lade()
    assert not txt.exists()
    # The LLM prompt names every field a file may use and none that it may not:
    # every quoted field in it passes the check, the locked ones are absent.
    import re as _re
    lp = importlib.import_module("krea2kit.nodes.llm_prompt")
    text = lp.erzeuge()
    assert 10000 < len(text) < 60000, len(text)
    for builder, _modul, _b, _f in lp.BUILDER:
        abschnitt = text.split('== "builder": "%s"' % builder, 1)[1].split('\n== ', 1)[0]
        for feld in _re.findall(r'^- "(\w+)"', abschnitt, _re.M):
            gut, m = eg.pruefe({"entries": [{"builder": builder, "field": feld, "label": "zz Test",
                                             "prompt": "{c} x" if feld == "hair" else "x"}]})
            assert gut and not m, (builder, feld, m)
    assert '- "age"' not in text and '- "gender"' not in text
    assert all(f in text for f in ('- "headwear"', '- "setup"', '- "look"', '- "stimmung"', '- "haltung"'))
    print("Eigene Eintraege: ok")

    # Thumbnails (vorschau.py): every built-in entry of these fields has one, no
    # file is left over from a renamed or removed entry, /krea2/presets names them.
    import os
    vs = importlib.import_module("krea2kit.nodes.vorschau")
    for cat in ("top", "bottom", "shoes", "hair", "headwear"):
        labels = [l for l, _ in peb.PRESETS[cat]]
        fehlt = [l for l in labels if not vs.bild(cat, l)]
        assert not fehlt, "ohne Vorschaubild: %s %s" % (cat, fehlt[:5])
        uebrig = set(os.listdir(os.path.join(vs.WURZEL, cat))) - {vs.slug(l) + ".jpg" for l in labels}
        assert not uebrig, "Vorschaubild ohne Eintrag: %s %s" % (cat, sorted(uebrig)[:5])
    assert api.presets()["person"]["felder"]["top"][0]["bild"] == "vorschau/top/basic-crop-top.jpg"
    # Lighting setups and postures (tools/schneide_vorschau.py, from the posters):
    # optional per entry - one appended after its poster has none - but no file
    # without an entry, and the builders' lists name those that exist.
    p = api.presets()
    for (builder, cat), ordner in vs.ORDNER.items():
        modul = importlib.import_module("krea2kit.nodes." + {"lighting": "lighting_builder",
                                                             "pose": "pose_builder"}[builder])
        labels = [l for l, _ in modul.PRESETS[cat]]
        uebrig = set(os.listdir(os.path.join(vs.WURZEL, ordner))) - {vs.slug(l) + ".jpg" for l in labels}
        assert not uebrig, "Vorschaubild ohne Eintrag: %s %s" % (ordner, sorted(uebrig)[:5])
        mit = {e["label"] for e in p[builder]["felder"][cat] if e.get("bild")}
        assert mit == {l for l in labels if vs.bild(ordner, l)}, (builder, cat)
    assert len(os.listdir(os.path.join(vs.WURZEL, "licht"))) == 30
    assert len(os.listdir(os.path.join(vs.WURZEL, "haltung"))) == 18
    assert p["lighting"]["felder"]["setup"][0]["bild"] == "vorschau/licht/softbox-diffuses-licht.jpg"
    assert not any(e.get("bild") for e in p["lighting"]["felder"]["richtung"])
    print("Vorschaubilder: ok")

    # Build Prompt without placeholders follows the recommended order: style,
    # expression, then framing, scene and lighting before the person.
    bp = kit.NODE_CLASS_MAPPINGS["Krea2PromptJoin"]()
    (text,) = bp.join("", person_1="PERSON", kamera="KAMERA", ausdruck="AUSDRUCK", stil="STIL",
                      szene="SZENE", licht="LICHT", pose="POSE")["result"]
    reihe = [text.index(w) for w in ("STIL", "AUSDRUCK", "KAMERA", "SZENE", "LICHT", "PERSON", "POSE")]
    assert reihe == sorted(reihe), text
    print("Prompt ohne Platzhalter: ok")

    # Reference mode: the reference image stands where the face was. The same
    # fields as with a LoRA trigger stay out, body, age and outfit stay, and
    # the reference is the subject - also with a mood subject in front.
    gesicht = {"ethnicity": "Scandinavian features", "skinTone": "very fair", "hair": "long wavy {c} hair",
               "hairColor": "copper red", "eyes": "grayish green", "eyeShape": "almond-shaped",
               "cheekbones": "high, pronounced cheekbones", "lipColor": "dusty rose",
               "skinFeatures": ["freckles"], "makeup": "glamorous makeup"}
    koerper = {"gender": "woman", "age": "in {p} late 20s", "height": "tall", "figure": "athletic",
               "shoes": "combat boots", "shoesColor": "black", "top": "white shirt"}
    ref = dict(koerper, **gesicht, referenz="1")
    for stufe in (peb.DETAIL_VOLL, peb.DETAIL_OBEN, peb.DETAIL_FIGUR, peb.DETAIL_IDENTITAET):
        text = peb.compose_person(ref, stufe)
        assert text.startswith("the same woman as in <image1>, in her late 20s"), text
        assert not [w for w in ("copper", "freckles", "almond", "Scandinavian", "fair", "dusty rose",
                                "cheekbones", "grayish", "glamorous") if w in text], text
        assert "a woman" not in text, text
        assert peb.compose_person(ref, stufe, ohne_subjekt=True) == text
    assert "tall, athletic" in peb.compose_person(ref) and "combat boots" in peb.compose_person(ref)
    assert peb.referenz_text(dict(koerper, referenz="1, 2")) == "the same woman as in <image1> and <image2>"
    assert peb.referenz_text({"gender": "man", "referenz": "1+2+3."}) == \
        "the same man as in <image1>, <image2> and <image3>"
    assert peb.referenz_text({"referenz": "02"}) == "the same person as in <image2>"
    assert peb.referenz_text({"referenz": "the woman in picture 1"}) == "the woman in picture 1"
    assert peb.referenz_text({"referenz": " ,, "}) == ""
    assert peb.compose_person(dict(ref, referenz="")).startswith("a woman, in her late 20s")
    assert peb.compose_person(dict(ref, ageExact="34")).startswith("the same woman as in <image1>, 34 years old")
    assert peb.werte_aus_state({"texte": {"referenz": "1"}})["referenz"] == "1"
    assert "referenz" in peb.DEFAULT_STATE["texte"] and peb.FELDART["referenz"] == "text"
    mit_bogen = dict(zustand_d, bogen="Drama", anzahl=4, start=1, kameras=["Porträt"])
    for f in range(1, 5):
        r = node.shoot(foto=f, ShootingState=json.dumps(mit_bogen), person_data=json.dumps(ref))
        assert r[6].startswith("the same woman as in <image1>"), r[6]
    print("Referenzmodus: ok")

    # The caption output: trigger, subject, then only what varies. None of the
    # identity - no LORA_WEG field, no age, no body, no reference phrase -
    # reaches it: the caption of the full person is the caption of the person
    # with all of that removed, photo for photo.
    garderobe = [{"name": "A", "werte": {"top": "white shirt", "shoes": "combat boots", "shoesColor": "black"}},
                 {"name": "B", "werte": {"free": "wearing a red raincoat", "hosiery": "bare legs"}}]
    voll_p = dict(ref, trigger="EileenX", ageExact="34", bust="full bust", _garderobe=garderobe)
    knapp_p = {"gender": "woman", "trigger": "EileenX", "_garderobe": garderobe}
    assert set(peb.LORA_WEG) <= set(voll_p) | {"faceShape", "nose", "chin", "jawline", "browShape", "lashes",
                                               "eyeliner", "eyeshadow", "lipShape", "lipFinish", "blush",
                                               "complexion", "hairEffect"}
    for rezept in (zustand_d, dict(zustand_d, bogen="Drama", anzahl=12, start=1)):
        for f in range(1, 121):
            s = json.dumps(rezept)
            a = node.shoot(foto=f, ShootingState=s, person_data=json.dumps(voll_p))
            b = node.shoot(foto=f, ShootingState=s, person_data=json.dumps(knapp_p))
            assert a[11] == b[11], (f, a[11], b[11])
            assert a[11].startswith("EileenX, a"), a[11]
            assert "<image" not in a[11] and not _re.search(r"\b(34|tall|athletic)\b", a[11]), a[11]
            assert a[12] == f
    assert node.shoot(foto=0, ShootingState=zustand, person_data=person_data)[12] == 1
    ohne = node.shoot(foto=3, ShootingState=zustand, person_data=json.dumps(koerper))[11]
    assert ohne.startswith("a woman, "), ohne
    ohne_person = node.shoot(foto=3, ShootingState=zustand)
    assert ohne_person[11].startswith(dict(sh.KAMERA)[ohne_person[8]].split(", ")[0] + ", "), ohne_person[11]
    # The outfit as far as the framing shows it: no boots on a portrait, only
    # boots on a feet macro.
    portraet = dict(zustand_d, kameras=["Porträt"], aktiv=dict(zustand_d.get("aktiv") or {}, fokus=False))
    cap = node.shoot(foto=1, ShootingState=json.dumps(portraet), person_data=json.dumps(koerper))[11]
    assert "white shirt" in cap and "boots" not in cap, cap
    fuesse = dict(zustand_d, kameras=["Detail"], fokusse=["Füße"])
    cap = node.shoot(foto=1, ShootingState=json.dumps(fuesse), person_data=json.dumps(koerper))[11]
    assert "black combat boots" in cap and "shirt" not in cap, cap
    print("Caption: 240 Fotos, keine Identitaet in der Bildunterschrift")

    # Save Dataset: a safe folder name, the trigger in front once, and with
    # torch at hand a real pair written to disk.
    ds = importlib.import_module("krea2kit.nodes.dataset")
    assert ds.ordnername("../../etc") == "etc" and ds.ordnername("") == "character"
    assert ds.ordnername("Eileen v2") == "Eileen v2" and "/" not in ds.ordnername("a/b\\c")
    assert ds.mit_trigger("a woman, close-up shot", "EileenX") == "EileenX, a woman, close-up shot"
    assert ds.mit_trigger("EileenX, a woman", "EileenX") == "EileenX, a woman"
    assert ds.mit_trigger("a woman", "") == "a woman"
    assert kit.NODE_CLASS_MAPPINGS["Krea2DatasetSave"].OUTPUT_NODE
    if torch is not None:
        import shutil
        ordner = WURZEL / "tests" / "_tmp" / "dataset"
        shutil.rmtree(ordner, ignore_errors=True)
        assert ds.speichere(torch.rand(1, 16, 24, 3), "a woman, close-up shot", 7, str(ordner), "EileenX") == ["0007.png"]
        assert (ordner / "0007.txt").read_text(encoding="utf-8") == "EileenX, a woman, close-up shot\n"
        assert ds.speichere(torch.rand(2, 8, 8, 3), "x", 12, str(ordner)) == ["0012_1.png", "0012_2.png"]
        from PIL import Image
        with Image.open(ordner / "0007.png") as bild:
            assert bild.size == (24, 16), bild.size
        shutil.rmtree(ordner, ignore_errors=True)
        print("Datensatz: ok")
    else:
        print("Datensatz: torch fehlt, Schreiben uebersprungen")

    pruefe_shoots()
    pruefe_selfie()
    pruefe_winkel_optik_requisiten()
    pruefe_plan_api(api, sh)
    pruefe_ux_api(api)
    pruefe_studio_all_in_one(kit, sh)
    if peb.MINDESTALTER == 0:
        pruefe_public_filter()
    pruefe_selbsttests_und_js()

    print("\nALLES OK")
    return 0


def pruefe_selbsttests_und_js():
    """Run builder self-tests and JS tests from one command unless skipped."""
    import os
    import shutil
    import subprocess
    if os.environ.get("SMOKE_NUR_PYTHON") == "1":
        return

    befehle = [
        ("person_builder", [sys.executable, "-m", "nodes.person_builder"]),
        ("pose_builder", [sys.executable, "-m", "nodes.pose_builder"]),
    ]
    node = shutil.which("node")
    if node:
        befehle += [
            ("hook.mjs", [node, "tests/hook.mjs"]),
            ("plan.mjs", [node, "tests/plan.mjs"]),
            ("regie.mjs", [node, "tests/regie.mjs"]),
        ]
    env = {**os.environ, "PYTHON": sys.executable}
    for name, cmd in befehle:
        e = subprocess.run(cmd, cwd=WURZEL, capture_output=True, text=True, env=env)
        if e.returncode:
            raise SystemExit("%s fehlgeschlagen (Exit %d):\n%s%s"
                             % (name, e.returncode, e.stdout, e.stderr))
    print("Selbsttests und JS-Tests: ok" if node else "Selbsttests: ok (node fehlt, JS-Tests uebersprungen)")


def pruefe_plan_api(api, sh):
    """Verify api.plane_serie_daten() matches shooting.py and shares DEFAULT_STATE."""
    assert api.presets()["shooting"]["vorgabe"] == sh.DEFAULT_STATE
    st = dict(sh.DEFAULT_STATE, anzahl=3, start=5, aktiv=dict(sh.DEFAULT_STATE["aktiv"], licht=True, perspektive=True))
    res = api.plane_serie_daten({"state": st, "outfits": 2, "saetze": [{"draussen": False}, {"draussen": True}]})
    assert len(res["fotos"]) == 3 and [f["foto"] for f in res["fotos"]] == [5, 6, 7], res
    for f in res["fotos"]:
        lauf = f["lauf"]
        soll = sh.plane(st, lauf, 2, 2)
        fmt = sh.format_fuer(soll["kamera"], lauf, st, soll["perspektive"])
        assert f["kamera"] == soll["kamera"] and f["fokus"] == soll["fokus"]
        assert f["perspektive"] == soll["perspektive"]
        assert f["pose"] == soll["pose"] and f["ausdruck"] == soll["ausdruck"]
        assert f["format"] == fmt and f["masse"] == list(sh.masse_fuer(fmt, st["groesse"]))
        assert f["outfit"] == sh.outfit_fuer(st, lauf, 2)
        assert f["set"] == sh.set_fuer(st, lauf, 2)
        assert f["licht"] == sh.licht_fuer(st, lauf, [False, True])
    # Explicit laeufe override and invalid input handling.
    einzeln = api.plane_serie_daten({"state": st, "laeufe": [0, 9]})
    assert [f["foto"] for f in einzeln["fotos"]] == [1, 10]
    try:
        api.plane_serie_daten("kaputt")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    print("Plan-API (/krea2/plan): ok")


def pruefe_ux_api(api):
    """Verify store CRUD (baustein_*), builder roll preview, and person detailFelder."""
    import shutil
    peb = importlib.import_module("krea2kit.nodes.person_builder")
    st = importlib.import_module("krea2kit.nodes.store")
    df = api.presets()["person"]["detailFelder"]
    assert set(df["unten"]) == peb._FELDER_UNTEN
    assert set(df["figur"]) == peb._FELDER_FIGUR
    assert set(df["identitaet"]) == peb._FELDER_IDENTITAET

    for bereich, cat in (("pose", "haltung"), ("ausdruck", "stimmung"),
                         ("lighting", "setup"), ("style", "look")):
        res = api.baue_vorschau_daten({
            "bereich": bereich, "seed": 7,
            "state": {"felder": {}, "wuerfeln": {cat: True}, "gruppe": "alle", "details": ""},
        })
        assert isinstance(res["prompt"], str) and res["prompt"].strip(), (bereich, res)
    loc_res = api.baue_vorschau_daten({
        "bereich": "location", "seed": 3,
        "state": {"felder": {"ort": "Sonniges Loft"}, "wuerfeln": {}, "gruppe": "alle", "details": ""},
    })
    assert "loft" in loc_res["prompt"], loc_res

    for art in ("person", "stil", "licht"):
        pfad = st._dir(art)
        shutil.rmtree(pfad, ignore_errors=True)
        try:
            name = st.baustein_speichern(art, "../Test Preset!", "sample text", {"x": 1})
            assert name == "Test Preset"
            liste = st.baustein_liste(art)
            assert liste == [{"name": "Test Preset", "text": "sample text", "state": {"x": 1}}], liste
            assert st._read(art, name) == "sample text"
            st.baustein_loeschen(art, name)
            assert st.baustein_liste(art) == []
        finally:
            shutil.rmtree(pfad, ignore_errors=True)
    print("UX-API (Bausteine, Vorschau, Detailfelder): ok")


def pruefe_studio_all_in_one(kit, sh):
    """Verify embedded All-in-One Studio states on Krea2Photoshooting."""
    node = kit.NODE_CLASS_MAPPINGS["Krea2Photoshooting"]()
    studio_state = dict(sh.DEFAULT_STATE, **{
        "kameras": ["Ganzkörper"],
        "aktiv": dict(sh.DEFAULT_STATE["aktiv"], set=True, licht=False, outfit=True),
        "_person": {
            "felder": {"gender": "Frau", "hair": "Lange Wellen", "hairColor": "Braun"},
            "mehrfach": {}, "texte": {},
        },
        "_wardrobe": {
            "outfits": [{"id": "o1", "name": "Boots", "felder": {"shoes": "Combat Boots", "shoesColor": "Schwarz"},
                         "texte": {"details": "wearing a red jacket"}}],
            "aktiv": 0,
        },
        "_location": {
            "saetze": [{"id": "s1", "name": "Loft", "felder": {"ort": "Sonniges Loft"},
                        "gruppe": "innen", "details": ""}],
            "aktiv": 0,
        },
        "_lighting": {
            "felder": {"setup": "Softbox diffuses Licht", "richtung": "Frontal 45°", "atmosphaere": "—"},
            "wuerfeln": {}, "gruppe": "alle", "details": "",
        },
        "_style": {
            "felder": {"look": "Schwarzweiß klassisch", "genre": "Editorial", "optik": "85mm f/1.4", "finish": "—"},
            "wuerfeln": {}, "gruppe": "alle", "details": "",
        },
        "_template": "{style}, {camera}, {scene}, {lighting}, {person}, {pose}",
    })
    out = node.shoot(foto=1, ShootingState=json.dumps(studio_state))
    assert len(out) == 16 and out[15], out
    assert "a woman" in out[6] and "red jacket" in out[6], out[6]
    assert "sunlit loft" in out[13], out[13]
    assert "softbox diffused studio lighting" in out[14], out[14]
    prompt = out[15]
    assert "black and white photograph" in prompt and "sunlit loft" in prompt and "red jacket" in prompt, prompt
    ui_res = node.shoot_ui(foto=1, ShootingState=json.dumps(studio_state))
    assert ui_res["ui"] == {"text": [prompt]} and ui_res["result"] == out, ui_res
    print("Studio All-in-One: ok")


def pruefe_public_filter():
    """Verify tools/veroeffentliche.py transforms dev files cleanly to 18+ public."""
    import re as _re
    import shutil
    ver_spec = importlib.util.spec_from_file_location("veroeffentliche_smoke", WURZEL / "tools" / "veroeffentliche.py")
    ver = importlib.util.module_from_spec(ver_spec)
    ver_spec.loader.exec_module(ver)

    peb = importlib.import_module("krea2kit.nodes.person_builder")
    tmp = WURZEL / "tests" / "_tmp" / "public_filter"
    shutil.rmtree(tmp, ignore_errors=True)
    try:
        (tmp / "nodes").mkdir(parents=True)
        (tmp / "tests").mkdir(parents=True)
        for rel in ("nodes/person_builder.py", "nodes/i18n.py", "tests/smoke.py"):
            shutil.copy2(WURZEL / rel, tmp / rel)
        ver.transformiere_fuer_public(tmp)

        pb_text = (tmp / "nodes" / "person_builder.py").read_text(encoding="utf-8")
        i18n_text = (tmp / "nodes" / "i18n.py").read_text(encoding="utf-8")
        smoke_text = (tmp / "tests" / "smoke.py").read_text(encoding="utf-8")
        assert "MINDESTALTER = 18" in pb_text and "MINDESTALTER = 0" not in pb_text
        age_block = _re.search(r'"age":\s*\[(.*?)\]', pb_text, _re.S).group(1)
        for verboten in ("Kind (6–12)", "Teenager (13–17)"):
            assert verboten not in pb_text and verboten not in i18n_text, verboten
        for verboten in ("{child}", "{teen}"):
            assert verboten not in age_block and verboten not in i18n_text, verboten
        assert "Altersgrenze: ab %d" in smoke_text

        # Runtime floor check with MINDESTALTER = 18.
        alt_min = peb.MINDESTALTER
        try:
            peb.MINDESTALTER = 18
            assert "an 18-year-old woman" in peb.compose_person({"gender": "woman", "ageExact": "12"})
            assert "18 years old" in peb.compose_person({"ageExact": "8"})
            assert peb.compose_person({"gender": "woman", "age": "{child}"}) == "a woman"
            assert peb.compose_person({"gender": "woman", "age": "{teen}"}) == "a woman"
        finally:
            peb.MINDESTALTER = alt_min
        print("Public-Filter (18+): ok")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pruefe_selfie():
    """Selfie mode (ROADMAP F4): the adopted wordings verbatim from the
    wording lab, the camera text as the lab rendered it, the couplings, and
    nothing of it in a series or a die that does not ask for it."""
    sh = importlib.import_module("krea2kit.nodes.shooting")
    pb = importlib.import_module("krea2kit.nodes.pose_builder")
    eb = importlib.import_module("krea2kit.nodes.expression_builder")
    sb = importlib.import_module("krea2kit.nodes.style_builder")
    peb = importlib.import_module("krea2kit.nodes.person_builder")
    sd = importlib.import_module("krea2kit.nodes.shoot_datei")
    api = importlib.import_module("krea2kit.nodes.api")
    kit = sys.modules["krea2kit"]

    # Verbatim what was rendered and adopted on 2026-09-30.
    labor = json.loads((WURZEL / "tools" / "wortlabor" / "selfie.json").read_text(encoding="utf-8"))
    kand = {k["id"]: k for g in labor["gruppen"] for k in g["kandidaten"]}
    uebernommen = {"oben-a": dict(sh.PERSPEKTIVE)["Selfie von oben"],
                   "auge-a": dict(sh.PERSPEKTIVE)["Selfie auf Augenhöhe"],
                   "liegend-a": dict(sh.PERSPEKTIVE)["Selfie im Liegen"],
                   "spiegel-a": dict(sh.PERSPEKTIVE)["Spiegel-Selfie"],
                   "kuss-b": dict(eb.PRESETS["stimmung"])["Kusshand"],
                   "peace-a": dict(pb.PRESETS["arme"])["Peace-Zeichen"],
                   "phone-a": dict(sb.PRESETS["genre"])["Smartphone / Social"]}
    for kid, wert in uebernommen.items():
        assert kand[kid]["wortlaut"] == wert, (kid, wert)
    assert kand["spiegel-a"]["bildausschnitt"] == "Ganzkörper"
    assert [l for l, _ in sh.PERSPEKTIVE][:4] == sh.PERSPEKTIVE_GRUPPEN["Selfie"] == list(sh.SELFIES)
    assert set(sh.PERSPEKTIVE_KAMERA) == {l for l, _ in sh.PERSPEKTIVE}
    assert set(sh.PERSPEKTIVE_FORMATE) == set(sh.SELFIES)
    assert sh.PERSPEKTIVE_BLICK["Selfie von oben"] == sh.BLICK_KAMERA
    # New entries are appended: every older one keeps its poster position.
    assert pb.PRESETS["arme"][14][0] == "Peace-Zeichen"
    assert [l for l, _ in pb.PRESETS["arme"][15:]] == pb.REQUISITEN
    assert eb.PRESETS["stimmung"][-1][0] == "Kusshand"
    assert sb.PRESETS["genre"][-1][0] == "Smartphone / Social"
    # Slots: the perspective has its own step, which no other slot shares.
    belegt = list(range(len(sh.FELDER))) + [len(sh.FELDER) + k for k in (1, 2, 3)]
    assert sh.SLOT_PERSPEKTIVE < len(sh._WURZELN) and sh.SLOT_PERSPEKTIVE not in belegt
    assert sh._schritt(sh.SLOT_PERSPEKTIVE) not in {sh._schritt(x) for x in belegt}

    basis = json.loads(json.dumps(sh.DEFAULT_STATE))
    rezept = next(patch for n, _, patch in sh.REZEPTE if n == "Selfie")
    selfie = dict(basis, **json.loads(json.dumps(rezept)))
    pd = peb.Krea2PersonBuilder().build(PersonState=json.dumps({"felder": {"gender": "Frau"}}))[1]
    node = kit.NODE_CLASS_MAPPINGS["Krea2Photoshooting"]()
    gesehen = set()
    for lauf in range(240):
        p = sh.plane(selfie, lauf)
        r = node.shoot(foto=lauf + 1, ShootingState=json.dumps(selfie), person_data=pd)
        sicht, kam = p["perspektive"], p["kamera"]
        gesehen.add(sicht)
        # The camera text is the lab's camera slot: framing, then perspective.
        assert r[2] == dict(sh.KAMERA)[kam] + ", " + dict(sh.PERSPEKTIVE)[sicht], r[2]
        assert kam in sh.PERSPEKTIVE_KAMERA[sicht], (kam, sicht)
        assert sh.format_fuer(kam, lauf, selfie, sicht) in ("9:16", "4:5")
        assert (r[3], r[4]) == sh.masse(kam, lauf, selfie, sicht)
        pose, aus = p["pose"], p["ausdruck"]
        if pose.get("arme"):
            assert pose["arme"] in pb.EINE_HAND_FREI, pose
        assert pose.get("koerper") in sh.SELFIE_KOERPER, pose
        if pose.get("haltung"):
            assert pb.arme_mit_freier_hand(pose["haltung"]), pose
            assert pose["haltung"] in sh.PERSPEKTIVE_HALTUNG.get(sicht, [pose["haltung"]]), (sicht, pose)
        if sicht == "Spiegel-Selfie":
            assert aus.get("blick") is None and aus.get("stimmung") != "Kusshand", aus
            assert "looking" not in r[1], r[1]
        if aus.get("stimmung") == "Kusshand":
            assert aus.get("blick") == sh.BLICK_KAMERA, aus
        if sicht == "Selfie von oben":
            assert aus.get("blick") == sh.BLICK_KAMERA, aus
        assert dict(sh.PERSPEKTIVE)[sicht].split(", ")[0] in r[11], r[11]
    assert gesehen == set(sh.SELFIES), gesehen
    # Kiss and peace sign turn up in a selfie series - and the mirror selfie
    # stands.
    alle = [sh.plane(dict(selfie, anzahl=400), l) for l in range(400)]
    assert any(x["ausdruck"].get("stimmung") == "Kusshand" for x in alle)
    assert any(x["pose"].get("arme") == "Peace-Zeichen" for x in alle)
    liegen = dict(selfie, perspektiven=["Selfie im Liegen"], pools={"haltung": "stehend"},
                  kameras=sh.PERSPEKTIVE_KAMERA["Selfie im Liegen"])
    assert {sh.plane(liegen, l)["pose"]["haltung"] for l in range(60)} == {"Auf dem Rücken liegend"}

    # Without the axis nothing of it: no perspective, no peace sign, no kiss,
    # from the series or from a die.
    for lauf in range(600):
        p = sh.plane(basis, lauf)
        assert p["perspektive"] is None
        assert p["pose"].get("arme") != "Peace-Zeichen" and p["ausdruck"].get("stimmung") != "Kusshand"
    assert sh.plane(dict(basis, perspektiven=["Spiegel-Selfie"]), 3)["perspektive"] is None
    for seed in range(400):
        assert pb._ziehe("arme", seed) != "Peace-Zeichen" and eb._ziehe("stimmung", seed) != "Kusshand"
        assert sb._ziehe("genre", seed) != "Smartphone / Social"
    assert eb._ziehe("stimmung", 5, eb.STIMMUNG_GRUPPEN["Selfie"]) == "Kusshand"
    # Chosen by hand they are plain entries; the smartphone genre clears the
    # lens in the panel, as it was rendered.
    assert kit.NODE_CLASS_MAPPINGS["Krea2StyleBuilder"]().build(seed=0, StyleState=json.dumps(dict(
        sb.DEFAULT_STATE, felder={"look": sb.NONE, "genre": "Smartphone / Social", "optik": sb.NONE,
                                  "finish": sb.NONE})))[0] == uebernommen["phone-a"]
    assert api.presets()["style"]["leert"] == {"genre|Smartphone / Social": ["optik"]}
    assert api.presets()["pose"]["leert"] == {}

    # Shoot files and the Director take the recipe, the axis and the list, in
    # English too.
    aus, fehler, notizen = sd.pruefe({"format": sd.FORMAT, "series": {"recipe": "Selfie"}}, streng=True)
    assert not fehler and not notizen, (fehler, notizen)
    assert aus["series"]["aktiv"]["perspektive"] is True and aus["series"]["blick"] == "meist_kamera"
    aus, fehler, _ = sd.pruefe({"format": sd.FORMAT, "series": {
        "switches": {"perspective": True}, "perspectives": ["Mirror selfie", "Selfie im Liegen"]}})
    assert not fehler and aus["series"]["perspektiven"] == ["Spiegel-Selfie", "Selfie im Liegen"], (aus, fehler)
    # The next round keeps the favourites' perspectives.
    fav = [nr for nr in range(1, 9) if sh.plane(selfie, nr - 1)["perspektive"] == "Spiegel-Selfie"]
    neu = sh.naechste_runde(dict(selfie, favoriten=fav), 0)
    assert neu["perspektiven"] == ["Spiegel-Selfie"] and neu["kameras"] == ["Ganzkörper"], neu
    print("Selfie: %d Perspektiven, Kopplungen und Wortlaute wie im Wortlabor" % len(sh.SELFIES))


def pruefe_winkel_optik_requisiten():
    """Camera angles (3.1a), dynamic lens (3.1b) and hand props (3.2)."""
    sh = importlib.import_module("krea2kit.nodes.shooting")
    pb = importlib.import_module("krea2kit.nodes.pose_builder")
    peb = importlib.import_module("krea2kit.nodes.person_builder")
    wr = importlib.import_module("krea2kit.nodes.wardrobe")
    dock = importlib.import_module("krea2kit.nodes.dock")
    sd = importlib.import_module("krea2kit.nodes.shoot_datei")
    api = importlib.import_module("krea2kit.nodes.api")
    kit = sys.modules["krea2kit"]
    node = kit.NODE_CLASS_MAPPINGS["Krea2Photoshooting"]()
    basis = json.loads(json.dumps(sh.DEFAULT_STATE))

    # Classical camera angles match the round-2 wording lab winners verbatim.
    l2 = json.loads((WURZEL / "tools" / "wortlabor" / "winkel_props2.json").read_text(encoding="utf-8"))
    k2 = {k["id"]: k for g in l2["gruppen"] for k in g["kandidaten"]}
    assert dict(sh.PERSPEKTIVE)["Froschperspektive"] == k2["frosch-c"]["wortlaut"]
    assert dict(sh.PERSPEKTIVE)["Von oben"] == k2["hoch-b"]["wortlaut"]
    assert dict(sh.PERSPEKTIVE)["Vogelperspektive"] == k2["aufsicht-c"]["wortlaut"]
    assert dict(sh.PERSPEKTIVE)["Dutch Angle"] == k2["dutch-b"]["wortlaut"]
    assert set().union(*sh.PERSPEKTIVE_GRUPPEN.values()) == {l for l, _ in sh.PERSPEKTIVE}

    # Vogelperspektive couples to lying postures even if the pool says standing.
    vogel = dict(basis, aktiv=dict(basis["aktiv"], perspektive=True),
                 perspektiven=["Vogelperspektive"], pools={"haltung": "stehend"},
                 kameras=["Halbtotale", "Ganzkörper"])
    for lauf in range(40):
        p = sh.plane(vogel, lauf)
        assert p["perspektive"] == "Vogelperspektive"
        assert p["pose"]["haltung"] in sh.PERSPEKTIVE_HALTUNG["Vogelperspektive"], p

    # Dynamic lens (3.1b): off by default, appended when on (except selfies and macro overrides).
    assert set(sh.KAMERA_OPTIK) == {l for l, _ in sh.KAMERA}
    opt = dict(basis, kameraOptik=True, aktiv=dict(basis["aktiv"], fokus=False))
    for kam in ("Totale", "Porträt", "Nahaufnahme"):
        r = node.shoot(foto=1, ShootingState=json.dumps(dict(opt, kameras=[kam])))
        assert sh.KAMERA_OPTIK[kam] in r[2], (kam, r[2])
    detail_fuss = node.shoot(foto=1, ShootingState=json.dumps(
        dict(basis, kameraOptik=True, kameras=["Detail"], fokusse=["Füße"])))
    assert sh.KAMERA_OPTIK["Detail"] not in detail_fuss[2], detail_fuss[2]

    # Hand props (3.2): absent when requisiten=False or on Pose Builder dice; drawn when on.
    l1 = json.loads((WURZEL / "tools" / "wortlabor" / "winkel_props.json").read_text(encoding="utf-8"))
    k1 = {k["id"]: k for g in l1["gruppen"] for k in g["kandidaten"]}
    assert dict(pb.PRESETS["arme"])["Kaffeetasse"] == k1["tasse-a"]["wortlaut"]
    assert dict(pb.PRESETS["arme"])["Blumenstrauß"] == k1["blumen-a"]["wortlaut"]
    assert "Sonnenbrille" not in pb.REQUISITEN and "Sonnenbrille" not in dict(pb.PRESETS["arme"])
    assert dict(peb.PRESETS["prop"]) == {l: dict(pb.PRESETS["arme"])[l] for l in pb.REQUISITEN}
    for seed in range(200):
        assert pb._ziehe("arme", seed) not in pb.REQUISITEN
    for lauf in range(300):
        assert sh.plane(basis, lauf)["pose"].get("arme") not in pb.REQUISITEN
    mit_req = dict(basis, requisiten=True, kameras=["Halbtotale"])
    gezogene_arme = {sh.plane(mit_req, l)["pose"].get("arme") for l in range(300)}
    assert gezogene_arme & set(pb.REQUISITEN), gezogene_arme
    assert len(api.presets()["shooting"]["requisiten"]) == len(pb.REQUISITEN)

    # Shoot files accept both German keys and English aliases.
    aus, fehler, _ = sd.pruefe({"format": sd.FORMAT, "series": {
        "dynamic_lens": True, "props": True, "perspectives": ["Low angle", "Dutch angle"]}}, streng=True)
    assert not fehler and aus["series"]["kameraOptik"] is True and aus["series"]["requisiten"] is True
    assert aus["series"]["perspektiven"] == ["Froschperspektive", "Dutch Angle"], aus

    # Custom prop grip template and comma-separated props list in Pose Builder and Series.
    assert pb.requisit_text("red umbrella") == "holding a red umbrella in one hand at chest height, the other arm relaxed"
    assert pb.requisit_text("a vintage Leica camera") == "holding a vintage Leica camera with both hands in front of her chest"
    assert pb.requisit_text("holding a coffee cup casually") == "holding a coffee cup casually"
    assert len(pb.requisit_liste("a red umbrella, an old camera")) == 2
    assert pb.haltung_erlaubt_requisit("Stehend") and not pb.haltung_erlaubt_requisit("Auf allen Vieren")
    pb_node = kit.NODE_CLASS_MAPPINGS["Krea2PoseBuilder"]()
    (pb_aus,) = pb_node.build(PoseState=json.dumps({"felder": {"haltung": "Stehend"}, "requisit": "red umbrella"}))
    assert "holding a red umbrella in one hand at chest height" in pb_aus, pb_aus
    s_req = dict(basis, requisitText="red umbrella, vintage camera", kameras=["Halbtotale"], pools={"haltung": "stehend"})
    gesehen_req = set()
    for f in range(1, 7):
        plan_f = sh.plane(s_req, f - 1)
        p_f = node.shoot(foto=f, ShootingState=json.dumps(s_req))[0]
        if pb.haltung_erlaubt_requisit(plan_f["pose"].get("haltung")):
            erwartet = "red umbrella" if (f - 1) % 2 == 0 else "vintage camera"
            assert erwartet in p_f, (f, p_f)
            gesehen_req.add(erwartet)
        else:
            assert "umbrella" not in p_f and "camera" not in p_f, (f, p_f)
    assert gesehen_req == {"red umbrella", "vintage camera"}, gesehen_req
    aus_req, f_req, _ = sd.pruefe({"format": sd.FORMAT, "pose": {"requisit": "red umbrella"},
                                   "series": {"prop_text": "vintage camera, red umbrella"}})
    assert not f_req and aus_req["pose"]["requisit"] == "red umbrella"
    assert aus_req["series"]["requisitText"] == "vintage camera, red umbrella"
    assert sd.pruefe({"format": sd.FORMAT, "series": {"prop_text": "red umbrella"}}, streng=True)[2]

    # Wardrobe Accessories: prop dropdown + propText custom free-text, omitted on
    # close-ups/back views/selfies/mannequin previews, suppresses conflicting arm gestures.
    w_node = wr.Krea2Wardrobe()
    wn_json = w_node.build(WardrobeState=json.dumps({"outfits": [
        {"id": "o1", "name": "Prop", "felder": {"top": "Basic Crop Top", "prop": "Kaffeetasse"},
         "texte": {"details": "", "propText": "vintage 35mm camera"}}]}))[0]
    pw_prop = peb.Krea2PersonBuilder().build(PersonState=json.dumps({"felder": {"gender": "Frau"}}),
                                             garderobe=wn_json)[1]
    assert "holding a warm ceramic coffee mug" in peb.compose_person(json.loads(pw_prop))
    assert "holding a vintage 35mm camera with both hands in front of her chest" in peb.compose_person(json.loads(pw_prop))
    assert "coffee" not in wr.vorschau_aus_state(
        {"felder": {"top": "Basic Crop Top", "prop": "Kaffeetasse"}, "texte": {"propText": "red umbrella"}})
    s_ward = dict(basis, kameras=["Halbtotale"], aktiv=dict(basis["aktiv"], fokus=False),
                  pools={"haltung": "stehend"})
    gesehen_wprop = False
    for f in range(1, 6):
        plan_w = sh.plane(s_ward, f - 1)
        if plan_w["pose"].get("koerper") != sh.ABGEWANDT and pb.haltung_erlaubt_requisit(plan_w["pose"].get("haltung")):
            res_w = node.shoot(foto=f, ShootingState=json.dumps(s_ward), person_data=pw_prop)
            assert "coffee mug" in res_w[6] and "vintage 35mm camera" in res_w[6], res_w[6]
            assert "hands" not in res_w[0] and "arms" not in res_w[0], res_w[0]
            gesehen_wprop = True
            break
    assert gesehen_wprop
    nah_w = node.shoot(foto=1, ShootingState=json.dumps(dict(basis, kameras=["Nahaufnahme"])), person_data=pw_prop)
    assert "coffee mug" not in nah_w[6] and "vintage 35mm camera" not in nah_w[6], nah_w[6]
    assert "requisitBeidhaendig" in api.presets()["person"]
    stripped_acc = dock.strip_kleidung({"prop": "x", "propText": "y"}, accessoires=True)
    assert stripped_acc.get("prop") is None and stripped_acc.get("propText") is None
    print("Winkel, Optik & Requisiten: ok")


def pruefe_shoots():
    """Shoot files (shoot_datei.py) and the Director (regie.py)."""
    import re
    import shutil
    sd = importlib.import_module("krea2kit.nodes.shoot_datei")
    rg = importlib.import_module("krea2kit.nodes.regie")
    eg = importlib.import_module("krea2kit.nodes.eigene")
    peb = importlib.import_module("krea2kit.nodes.person_builder")

    # Round trip: the node states of the example workflow, as a shoot file,
    # come back from the check unchanged - same keys, same order, same labels.
    wf = json.loads((WURZEL / "example_workflows" / "photoshoot-series.json").read_text(encoding="utf-8"))
    klasse = {c: a for a, (c, _p) in sd.ABSCHNITTE.items()}
    shoot = {"format": sd.FORMAT, "name": "Beispiel"}
    for n in wf["nodes"]:
        for k, v in (n.get("properties") or {}).items():
            if n["type"] in klasse and k == sd.ABSCHNITTE[klasse[n["type"]]][1]:
                shoot[klasse[n["type"]]] = json.loads(v)
    shoot["series"] = {"anzahl": 12, "start": 4711, "serienSeed": 9, "aktiv": {"kamera": True, "rausch": False},
                       "pools": {"haltung": ["stehend", "sitzend"], "stimmung": "ruhig", "arme": "—"},
                       "kameras": None, "fokusse": ["Gesicht"], "takes": {"3": 1}, "favoriten": [2],
                       "outfitAuswahl": [0], "runden": [{"start": 1}], "zukunft": {"x": 1}}
    shoot["scene"], shoot["template"] = "a loft", "{style}, {person}"
    assert {"person", "wardrobe", "lighting", "style"} <= set(shoot), sorted(shoot)
    aus, fehler, hinweise = sd.pruefe(copy_json(shoot))
    assert not fehler and not hinweise, (fehler, hinweise)
    assert json.dumps(aus, ensure_ascii=False) == json.dumps(shoot, ensure_ascii=False)
    assert sd.pruefe(aus)[0] == aus
    # The Location node's sets: every set checked like a builder, id and name
    # kept; an unknown place is an error and drops out; English names map back.
    ort_st = {"saetze": [{"id": "s1", "name": "Loft", "felder": {"ort": "Sonniges Loft", "wetter": "—"},
                          "wuerfeln": {}, "gruppe": "innen", "details": ""},
                         {"id": "s2", "name": "", "felder": {"ort": "—"}, "wuerfeln": {"ort": True},
                          "gruppe": "natur", "details": "a pine forest"}], "aktiv": 1}
    aus, fehler, hinweise = sd.pruefe({"location": copy_json(ort_st)})
    assert not fehler and not hinweise and aus["location"] == ort_st, (fehler, aus)
    aus, fehler, _ = sd.pruefe({"location": {"saetze": [{"felder": {"place": "Sunlit loft", "ort": "Mond"}}]}})
    assert aus["location"]["saetze"][0]["felder"] == {"ort": "Sonniges Loft"} and len(fehler) == 1, (aus, fehler)
    assert sd.ABSCHNITTE["location"] == ("Krea2LocationBuilder", "locationState")
    assert sd.pruefe({"series": {"aktiv": {"light": True}, "light_order": "time of day",
                                 "lichtPool": "Natural"}})[0]["series"] == \
        {"aktiv": {"licht": True}, "lichtFolge": "tageszeit", "lichtPool": "natuerlich"}

    # What the other 2.7 branches added to the states travels in a saved shoot
    # untouched: the reference field, Selects (rejects, rounds, the outfit
    # subset, a pool of several families), Draft and the file name folder, the
    # gaze mode. The Director takes none of the run keys and says nothing
    # about them; a reference is free text, so it goes with a note.
    extra = copy_json(shoot)
    extra["person"] = dict(extra.get("person") or {})
    extra["person"]["texte"] = dict(extra["person"].get("texte") or {}, trigger="EileenX", referenz="1, 2")
    extra["series"] = dict(extra["series"], verworfen=[5, 7], runde=2, entwurf=True, ordner="photoshoot/anchor",
                           blick="kamera", runden=[{"start": 1, "anzahl": 12, "favoriten": [2, 3],
                                                    "verworfen": [5], "runde": 1, "entwurf": True}])
    aus, fehler, hinweise = sd.pruefe(copy_json(extra))
    assert not fehler and not hinweise, (fehler, hinweise)
    assert aus == extra, aus
    assert aus["person"]["texte"]["referenz"] == "1, 2"
    for k in ("verworfen", "runde", "runden", "outfitAuswahl", "entwurf", "ordner", "blick"):
        assert aus["series"][k] == extra["series"][k], k
    assert aus["series"]["pools"]["haltung"] == ["stehend", "sitzend"]
    a, f, h = sd.pruefe({"person": {"texte": {"referenz": "x" * 3000}}})
    assert not f and len(a["person"]["texte"]["referenz"]) == sd.TEXT_MAX and len(h) == 1, (f, h)
    a, f, h = sd.pruefe(copy_json(extra), streng=True)
    assert a["person"]["texte"]["referenz"] == "" and any("referenz" in x for x in h), h
    assert not set(sd.LAUF_SCHLUESSEL) & set(a["series"]), a["series"]
    assert not [x for x in h if any('"%s"' % k in x for k in sd.LAUF_SCHLUESSEL)], h

    # English display labels map back to the German keys; unknown labels are
    # errors that drop out, never exceptions.
    en = {"person": {"hair": "Long waves", "hairColor": "auburn", "nose": "Snub"},
          "lighting": {"felder": {"setup": "Golden hour", "direction": "Backlit"}},
          "series": {"recipe": "Lookbook", "framings": ["Portrait", "Wide"], "pools": {"mood": "friendly"},
                     "mood_arc": "Joy", "order": "wide to close"}}
    aus, fehler, _ = sd.pruefe(en)
    assert aus["person"]["felder"] == {"hair": "Lange Wellen", "hairColor": "Kastanie"}, aus["person"]
    assert aus["lighting"]["felder"] == {"setup": "Golden Hour", "richtung": "Gegenlicht"}, aus["lighting"]
    assert aus["series"]["pools"] == {"haltung": "stehend", "stimmung": "freundlich"}, aus["series"]
    assert aus["series"]["kameras"] == ["Porträt"] and aus["series"]["bogen"] == "Freude"
    assert aus["series"]["reihenfolge"] == "weit_nah"
    assert len(fehler) == 2 and any('"Snub"' in f for f in fehler) and any('"Wide"' in f and "Wide shot" in f for f in fehler), fehler
    for kaputt in (None, [], "x", "{", 3, {"person": [1]}, {"person": {"felder": {"hair": 3}}},
                   {"series": {"anzahl": "viele", "pools": [1], "kameras": 5}}, {"wardrobe": {"outfits": "x"}}):
        a, f, _ = sd.pruefe(kaputt)
        assert f, kaputt

    # Custom entries: from a loaded file, or from the copy the state carries -
    # the copy is filled in on the check, so the file renders elsewhere.
    tmp = WURZEL / "tests" / "_tmp" / "shoot_eigene"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    (tmp / "hut.json").write_text(json.dumps({"entries": [
        {"field": "headwear", "label": "Trilby", "prompt": "a narrow-brimmed straw trilby"}]}), encoding="utf-8")
    eg.lade([str(tmp)])
    a, f, _ = sd.pruefe({"wardrobe": {"outfits": [{"id": "o1", "felder": {"headwear": "Trilby"}}]}})
    assert not f and a["wardrobe"]["outfits"][0]["eigene"] == {"headwear": {"Trilby": "a narrow-brimmed straw trilby"}}
    eg.lade([])
    b, f, _ = sd.pruefe(a)
    assert not f and b == a
    assert sd.pruefe({"wardrobe": {"outfits": [{"felder": {"headwear": "Trilby"}}]}})[1]
    shutil.rmtree(tmp, ignore_errors=True)

    # The Director's rules: built-in labels only, no free text but the scene,
    # nothing below 18, clothing into the wardrobe.
    streng = {"person": {"felder": {"gender": "Frau", "age": "Teenager (13–17)", "top": "Basic crop top"},
                         "texte": {"ageExact": "16", "details": "anything"}},
              "pose": {"felder": {"haltung": "Trilby"}, "details": "x"}, "template": "{person}",
              "wardrobe": {"outfits": [{"felder": {"headwear": "Trilby"}}]}}
    a, f, h = sd.pruefe(streng, streng=True)
    minderj = [l for l, v in peb.PRESETS["age"] if "{teen}" in v]
    if minderj:   # the public build has no such label; then it is simply unknown
        assert "age" not in a["person"]["felder"]
    assert a["person"]["texte"] == {"ageExact": "", "details": ""}, a["person"]
    assert "template" not in a and "top" not in a["person"]["felder"]
    assert a["wardrobe"]["outfits"][0]["felder"] == {"top": "Basisches Crop-Top"} or \
        a["wardrobe"]["outfits"][0]["felder"] == {"top": peb.PRESETS["top"][0][0]}, a["wardrobe"]
    assert sum("18" in x for x in f) >= 1 and any("Trilby" in x for x in f), f

    # The Director's prompt: its own example passes its own import cleanly,
    # every label it lists resolves, no age below 18 is offered.
    text = rg.erzeuge("a rainy afternoon in Paris")
    assert 8000 < len(text) < 40000, len(text)
    assert text.rstrip().endswith("a rainy afternoon in Paris")
    assert "Attached is a reference photo" in rg.erzeuge("", "photo")
    r = rg.importiere("Sure! Here it is:\n```json\n" + json.dumps(rg.BEISPIEL) + "\n```\nEnjoy.")
    assert not r["errors"] and not r["notes"], r
    i18n = importlib.import_module("krea2kit.nodes.i18n")
    for label in sd.MINDERJAEHRIG:
        assert '"%s"' % label not in text and i18n.PERSON["age"].get(label, label) not in text, label
    zeilen = re.findall(r'^- "(\w+)" \([^)]*\)(?:, by family:|: (.*))$', text, re.M)
    geprueft = 0
    for feld, liste in zeilen:
        if not liste or liste.startswith("the same list") or feld in (
                "recipe", "photos", "framings", "focus", "perspectives", "pools",
                "mood_arc", "order", "ratio", "gaze", "light_order", "light_families", "switches"):
            continue
        for label in liste.split("; "):
            for abschnitt, (b, m, _gf, _g) in list(sd.BAUSTEINE.items()) + [("person", ("person", peb, 0, 0))]:
                if feld in m.PRESETS:
                    assert sd.loese_label(b, m, feld, label, streng=True)[0], (feld, label)
                    geprueft += 1
                    break
    assert geprueft > 400, geprueft
    assert rg.importiere("no json here")["errors"] and rg.importiere('{"person": 1')["errors"]

    # Offline draft: label-only, passes the same import.
    r = rg.entwurf("black and white headshots of a woman in her early 30s with long straight black hair "
                   "and green eyes, golden hour, 85mm f/1.4, 10 photos")
    assert not r["errors"], r
    assert r["shoot"]["person"]["felder"] == {"gender": "Frau", "age": "Anfang 30", "hair": "Lang glatt",
                                               "hairColor": "Schwarz", "eyes": "Grün"}, r["shoot"]["person"]
    assert r["shoot"]["series"]["anzahl"] == 10 and r["shoot"]["style"]["felder"]["optik"] == "85mm f/1.4"

    assert sd.pruefe({"series": {"gaze": "mostly camera"}}, streng=True)[0]["series"]["blick"] == "meist_kamera"
    assert sd.pruefe({"series": {"gaze": "at the camera"}}, streng=True)[0]["series"]["blick"] == "kamera"
    assert sd.pruefe({"series": {"gaze": "away"}}, streng=True)[0]["series"]["blick"] == "abgewandt"
    r_selfie = rg.entwurf("mirror selfie looking into the camera, 6 photos")
    assert not r_selfie["errors"], r_selfie
    assert r_selfie["shoot"]["series"]["perspektiven"] == ["Spiegel-Selfie"], r_selfie["shoot"]["series"]
    assert r_selfie["shoot"]["series"]["aktiv"]["perspektive"] is True
    assert r_selfie["shoot"]["series"]["blick"] == "kamera"

    # The sample in docs/ loads without a single message.
    a, f, h = sd.pruefe(json.loads((WURZEL / "docs" / "shoot_example.json").read_text(encoding="utf-8")))
    assert not f and not h and "_comment" not in a, (f, h)

    # The store: save, list, load, delete; unsafe names never reach a path.
    shutil.rmtree(sd.ordner(), ignore_errors=True)
    name, f = sd.speichere("../Mein Shooting!", shoot)
    assert name == "Mein Shooting" and not f
    assert [x["name"] for x in sd.liste()] == ["Mein Shooting"]
    geladen, f, _ = sd.lade("Mein Shooting")
    assert not f and {k: v for k, v in geladen.items() if k not in ("name", "saved")} == \
        {k: v for k, v in shoot.items() if k != "name"}
    for schlecht in ("", "../", "///"):
        try:
            sd.speichere(schlecht, shoot)
            raise AssertionError(schlecht)
        except ValueError:
            pass
    sd.loesche("Mein Shooting")
    assert sd.liste() == []
    print("Shoot-Dateien und Regie: ok")


def copy_json(x):
    return json.loads(json.dumps(x))


if __name__ == "__main__":
    sys.exit(main())
