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
    assert len(kit.NODE_CLASS_MAPPINGS) == 14, len(kit.NODE_CLASS_MAPPINGS)
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
    assert peb.detail_fuer_kamera("Porträt") == peb.DETAIL_VOLL
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
    a = node.shoot(seed=7, ShootingState=zustand, person_data=person_data)
    b = node.shoot(seed=7, ShootingState=zustand, person_data=person_data)
    assert a == b, "Durchlauf nicht reproduzierbar"
    assert len(a) == len(node.RETURN_TYPES) == len(node.RETURN_NAMES)
    assert a[3] > 0 and a[4] > 0, "Bildmasse"
    assert a[8] in [lbl for lbl, _ in sh.KAMERA], a[8]
    # A broken state must not get through.
    assert node.shoot(seed=0, ShootingState="{kaputt")
    assert node.shoot(seed=0, ShootingState=zustand, person_data="kein json")[6] == ""
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
        text = node.shoot(seed=lauf, ShootingState=zustand)[1]
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
    luecken = i18n.fehlend([("person", peb), ("ausdruck", eb), ("pose", pbm)])
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
    for tabelle in (peb.SCHUH_GRUPPEN, pbm.HALTUNG_GRUPPEN, eb.STIMMUNG_GRUPPEN):
        for fam in tabelle:
            if fam not in i18n.FAMILIEN:
                luecken.append("familie/" + fam)
    for cat in list(pbm.FOLGE) + list(eb.FOLGE):
        if cat not in i18n.KATEGORIEN:
            luecken.append("kategorie/" + cat)
    assert not luecken, "ohne Uebersetzung: %s" % luecken[:10]

    # The other way round: translated labels that no longer exist. Those never
    # come to light otherwise, because a dead entry is simply never looked up.
    tab = i18n.tabelle()
    verwaist = []
    for schluessel, modul in (("person", peb), ("ausdruck", eb), ("pose", pbm)):
        for cat, uebersetzt in tab[schluessel].items():
            echte = {l for l, _ in modul.PRESETS.get(cat, [])}
            verwaist += ["%s/%s/%s" % (schluessel, cat, l)
                         for l in uebersetzt if l not in echte]
    assert not verwaist, "verwaiste Uebersetzung: %s" % verwaist[:10]
    zahl = sum(len(v) for m in ("person", "ausdruck", "pose", "shooting")
               for v in tab[m].values())
    print("Uebersetzung: %d Labels, keine Luecke" % zahl)

    # Placeholders and the recommended order.
    join = kit.NODE_CLASS_MAPPINGS["Krea2PromptJoin"]()
    text = "{kamera}, {szene}, {person}, {pose}, {extra}, {ausdruck}, {stil}"
    assert join.join(text, kamera="A", szene="B", person_1="C", pose="D",
                     ausdruck="E", stil="F")[0] == "A, B, C, D, E, F"
    # Placeholders left empty leave no orphaned commas behind.
    assert join.join("{kamera}, {szene}, {stil}", kamera="A", stil="F")[0] == "A, F"
    # The English spellings mean the same as the German ones.
    assert join.join("{camera}, {scene}, {person}, {expression}, {style}",
                     kamera="A", szene="B", person_1="C", ausdruck="E",
                     stil="F")[0] == "A, B, C, E, F"
    ohne = join.join("", kamera="A", person_1="C", szene="B")[0]
    assert ohne.index("A") < ohne.index("B") < ohne.index("C"), ohne
    print("Prompt bauen: ok")

    print("\nALLES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
