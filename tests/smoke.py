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
    assert len(kit.NODE_CLASS_MAPPINGS) == 16, len(kit.NODE_CLASS_MAPPINGS)
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
        "type": "a woman", "figure": "hourglass figure", "bust": "full bust",
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
    for eingabe in ("12", "3", "17", " 8 Jahre", "0"):
        for stufe in (peb.DETAIL_VOLL, peb.DETAIL_FIGUR, peb.DETAIL_IDENTITAET):
            text = peb.compose_person(dict(p, ageExact=eingabe), stufe)
            assert "years old" not in text or "%d years old" % peb.MINDESTALTER in text, \
                "Alter nicht begrenzt: %r -> %s" % (eingabe, text)
    assert "34 years old" in peb.compose_person(dict(p, ageExact="34"))
    assert "years old" not in peb.compose_person(dict(p, ageExact=""))
    # The presets on their own cannot describe a minor either.
    assert not [v for _, v in peb.PRESETS["age"]
                if any(z in v for z in ("teen", "10s", "child"))]
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

    # Reference images. torch, numpy and PIL are not installed here - identity.py
    # imports them inside its functions for exactly that reason, so everything
    # below the pixels is testable without them. torch itself gets a stub with
    # the two calls the empty path makes.
    idm = importlib.import_module("krea2kit.nodes.identity")

    # The name goes into a path. A name that walks out of the folder must not
    # survive - same guard as the block store, same helper.
    assert idm._safe_name("../../etc/passwd") == "etcpasswd"
    for boese in ("..", "/", "", "   ", "./."):
        try:
            idm._ordner(boese)
        except ValueError:
            pass
        else:
            assert False, "Ordner aus unbrauchbarem Namen: %r" % boese

    # The strength follows the framing, tight to wide, and never leaves the two
    # widgets' range. Monotone: a wider shot may never want more adapter.
    werte = [idm.staerke_fuer(lbl, 0.15, 0.95) for lbl, _ in sh.KAMERA]
    assert werte[0] == 0.95 and abs(werte[-1] - 0.15) < 1e-9, werte
    assert werte == sorted(werte, reverse=True), werte
    assert all(0.15 <= w <= 0.95 for w in werte), werte
    # Nothing wired to kamera_label: single-image work, treat it as a close-up.
    assert idm.staerke_fuer(None, 0.15, 0.95) == 0.95
    assert idm.staerke_fuer("", 0.15, 0.95) == 0.95
    assert idm.staerke_fuer("Handyfoto", 0.15, 0.95) == 0.95
    # The two widgets rescale the whole curve, they do not shift the shape.
    flach = [idm.staerke_fuer(lbl, 0.5, 0.5) for lbl, _ in sh.KAMERA]
    assert flach == [0.5] * len(sh.KAMERA), flach
    print("Identitaet/Staerke: %s" % ", ".join("%s %.2f" % (lbl, w)
                                               for (lbl, _), w in zip(sh.KAMERA, werte)))

    # References of different sizes cannot go into one batch - torch.cat needs
    # identical height and width. Everything matching the first image survives.
    assert idm._auswahl([]) == ([], [])
    assert idm._auswahl([(64, 64)]) == ([0], [])
    assert idm._auswahl([(64, 64), (32, 99), (64, 64)]) == ([0, 2], [1])
    assert idm._auswahl([(32, 99), (64, 64), (64, 64)]) == ([0], [1, 2])
    print("Identitaet/Mischgroessen: ok")

    # A person without references must not take the graph down - the whole
    # bootstrap workflow runs the first series without one.
    torch_stub = types.SimpleNamespace(zeros=lambda *masse: ("zeros",) + masse)
    sys.modules.setdefault("torch", torch_stub)
    idnode = kit.NODE_CLASS_MAPPINGS["Krea2Identity"]()
    for name in (None, idm.LEER, "Niemand Gespeichertes"):
        bild, staerke, anzahl = idnode.laden(name=name, kamera_label="Totale")
        assert anzahl == 0 and bild == ("zeros", 1, 1, 1, 3), (name, bild)
        assert abs(staerke - 0.15) < 1e-9, staerke
    assert kit.NODE_CLASS_MAPPINGS["Krea2Identity"].IS_CHANGED(name=idm.LEER) == 0.0
    print("Identitaet/leer: kein Absturz, anzahl 0")

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
