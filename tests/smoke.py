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


def main():
    kit = lade_paket()

    assert kit.WEB_DIRECTORY == "./js"
    assert len(kit.NODE_CLASS_MAPPINGS) == 20, len(kit.NODE_CLASS_MAPPINGS)
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
    assert nochmal[5] != a[5] and nochmal[:5] == a[:5] and nochmal[6:] == a[6:]
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
    luecken = i18n.fehlend([("person", peb), ("ausdruck", eb), ("pose", pbm),
                            ("lighting", lb), ("style", sb)])
    for lbl, _ in sh.KAMERA:
        if lbl not in i18n.SHOOTING["kamera"]:
            luecken.append("shooting/kamera/" + lbl)
    for lbl, _ in sh.FOKUS:
        if lbl not in i18n.SHOOTING["fokus"]:
            luecken.append("shooting/fokus/" + lbl)
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
                    pbm.HALTUNG_GRUPPEN, eb.STIMMUNG_GRUPPEN, lb.LICHT_GRUPPEN, sb.LOOK_GRUPPEN):
        for fam in tabelle:
            if fam not in i18n.FAMILIEN:
                luecken.append("familie/" + fam)
    for cat in list(pbm.FOLGE) + list(eb.FOLGE) + list(lb.FOLGE) + list(sb.FOLGE):
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
                              ("lighting", lb), ("style", sb)):
        for cat, uebersetzt in tab[schluessel].items():
            echte = {l for l, _ in modul.PRESETS.get(cat, [])}
            verwaist += ["%s/%s/%s" % (schluessel, cat, l)
                         for l in uebersetzt if l not in echte]
    assert not verwaist, "verwaiste Uebersetzung: %s" % verwaist[:10]
    zahl = sum(len(v) for m in ("person", "ausdruck", "pose", "lighting", "style", "shooting")
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

    # Placeholders and the recommended order.
    join = kit.NODE_CLASS_MAPPINGS["Krea2PromptJoin"]()
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
    for b in ("person", "pose", "ausdruck", "lighting", "style"):
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
    print("Vorschaubilder: ok")

    # Build Prompt without placeholders follows the recommended order: style,
    # expression, then framing, scene and lighting before the person.
    bp = kit.NODE_CLASS_MAPPINGS["Krea2PromptJoin"]()
    (text,) = bp.join("", person_1="PERSON", kamera="KAMERA", ausdruck="AUSDRUCK", stil="STIL",
                      szene="SZENE", licht="LICHT", pose="POSE")
    reihe = [text.index(w) for w in ("STIL", "AUSDRUCK", "KAMERA", "SZENE", "LICHT", "PERSON", "POSE")]
    assert reihe == sorted(reihe), text
    print("Prompt ohne Platzhalter: ok")

    print("\nALLES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
