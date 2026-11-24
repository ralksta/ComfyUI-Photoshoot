"""
Serves the preset tables to the interface.

Without this route, every label and every English equivalent would have to
exist a second time in JavaScript - two lists that would inevitably drift
apart. This way Python stays the single source, and the live preview inside
the node can assemble the English sentence without asking the server.
"""

import base64
import binascii
import copy
import json
import os
import re
import time

from . import eigene as EG
from . import expression_builder as EB
from . import i18n
from . import lighting_builder as LB
from . import location_builder as OB
from . import person_builder as PeB
from . import pose_builder as PB
from . import shoot_datei as SD
from . import shooting as SH
from . import store as ST
from . import style_builder as SB
from . import vorschau as VS


def _felder(modul, builder=None):
    """Put PRESETS into the shape the interface needs, with the thumbnail of
    each entry that has one (vorschau.ORDNER: lighting setups, postures)."""
    felder = {}
    for cat in modul.FOLGE:
        ordner = VS.ORDNER.get((builder, cat))
        felder[cat] = [_mit_bild({"label": lbl, "wert": wert}, ordner) if ordner
                       else {"label": lbl, "wert": wert} for lbl, wert in modul.PRESETS[cat]]
    return felder


def _beschreibung(modul, gruppen_feld, gruppen, builder=None):
    daten = {
        "reihenfolge": list(modul.FOLGE),
        "felder": _felder(modul, builder),
        "gruppenFeld": gruppen_feld,
        "gruppen": {name: list(labels) for name, labels in gruppen.items()},
        "leer": modul.NONE,
        "alle": modul.ALLE,
        # "cat|label" -> fields that choosing this entry clears (style_builder.LEERT).
        "leert": {"%s|%s" % k: list(v) for k, v in getattr(modul, "LEERT", {}).items()},
    }
    if modul is PB:
        daten["requisitBeidhaendig"] = list(PB.REQUISIT_BEIDHAENDIG)
    return daten


def _location():
    """The Location node: the panel blueprint's shape, plus which families
    are outdoors and indoors and which fields only apply outdoors - the same
    tables location_builder.py couples with, so the panel and the Series
    preview need no copy."""
    daten = _beschreibung(OB, "ort", OB.ORT_GRUPPEN, builder="location")
    daten.update({"draussen": list(OB.DRAUSSEN), "drinnen": list(OB.DRINNEN),
                  "nurDraussen": list(OB.NUR_DRAUSSEN)})
    return daten


def _mit_bild(eintrag, cat):
    """The entry with the path of its thumbnail (vorschau.py), where there is
    one. cat names the folder under js/vorschau/."""
    b = VS.bild(cat, eintrag["label"])
    if b:
        eintrag["bild"] = b
    return eintrag


def _person():
    """The person has more fields than pose and expression, so it needs
    collapsible sections and a different kind of control per field."""
    felder = {cat: [_mit_bild({"label": lbl, "wert": wert}, cat) for lbl, wert in PeB.PRESETS[cat]]
              for cat in list(PeB._SINGLE) + ["skinFeatures"]}
    return {
        # "felder" holds strings and nested lists - a list is one row made of
        # several fields that belong together.
        "sektionen": [{"name": name,
                       "felder": [list(e) if isinstance(e, list) else e
                                  for e in cats]}
                      for name, cats in PeB.SEKTIONEN],
        "felder": felder,
        "art": dict(PeB.FELDART),
        "namen": dict(PeB.FELDNAMEN),
        "zeilennamen": dict(PeB.ZEILENNAMEN),
        "gesichtsFelder": list(PeB.GESICHTSFELDER),
        "gesichtHinweisAb": PeB.GESICHT_HINWEIS_AB,
        "gesichtWarnungAb": PeB.GESICHT_WARNUNG_AB,
        "platzhalter": dict(PeB.PLATZHALTER),
        "gruppen": {"shoes": {name: list(labels)
                              for name, labels in PeB.SCHUH_GRUPPEN.items()},
                    "top": {name: list(labels)
                            for name, labels in PeB.OBERTEIL_GRUPPEN.items()},
                    "bottom": {name: list(labels)
                               for name, labels in PeB.UNTERTEIL_GRUPPEN.items()},
                    "headwear": {name: list(labels)
                                 for name, labels in PeB.KOPF_GRUPPEN.items()}},
        "unter": dict(PeB.UNTERFELDER),
        # The sections a Wardrobe node shows - an outfit is these fields - and
        # the Person Builder's own, which are all the others.
        "outfitSektionen": list(PeB.OUTFIT_SEKTIONEN),
        "personSektionen": list(PeB.PERSON_SEKTIONEN),
        "outfitFelder": sorted(PeB.OUTFIT_FELDER - {"free"}) + ["details"],
        "loraWeg": sorted(PeB.LORA_WEG),
        # Reference mode (referenz_text()): the preview writes the same phrase.
        "referenzSatz": PeB.REFERENZ_SATZ,
        "referenzBild": PeB.REFERENZ_BILD,
        "farben": PeB.FARBWERTE,
        "farbeEntfaellt": {cat: [feld, list(werte)]
                           for cat, (feld, werte) in PeB.FARBE_ENTFAELLT.items()},
        "eigenerStoff": PeB._EIGENER_STOFF.pattern,
        # The pools of "Inspire Me" (INSPIRATION), labels only.
        "inspiration": PeB.INSPIRATION,
        "requisitBeidhaendig": list(PB.REQUISIT_BEIDHAENDIG),
        "detailFelder": {
            "unten": sorted(PeB._FELDER_UNTEN),
            "figur": sorted(PeB._FELDER_FIGUR),
            "identitaet": sorted(PeB._FELDER_IDENTITAET),
        },
        "mindestalter": PeB.MINDESTALTER,
        "leer": PeB.NONE,
        "alle": PeB.ALLE,
    }


def _shooting():
    """Everything the photoshoot interface needs in order to compute.

    The preview should show the first few photos without asking the server on
    every change - for that it needs the same lists and the same ordering that
    plane() in shooting.py works through.
    """
    return {
        "kamera": [{"label": lbl, "wert": wert} for lbl, wert in SH.KAMERA],
        "fokus": [{"label": lbl, "wert": wert} for lbl, wert in SH.FOKUS],
        "kameraFokus": {k: list(v) for k, v in SH.KAMERA_FOKUS.items()},
        # A body turned away shows no face - no face focus then (plane()).
        "abgewandt": SH.ABGEWANDT,
        "fokusGesicht": list(SH.FOKUS_GESICHT),
        # Placement per framing - the preview has to filter exactly as plane()
        # does, or it shows a different photo than the one that comes out.
        "kameraRaum": {k: list(v) for k, v in SH.KAMERA_RAUM.items()},
        # Body tension per base posture, for the same reason.
        "haltungSpannung": {k: list(v) for k, v in PB.HALTUNG_SPANNUNG.items()},
        "haltungRaum": {k: list(v) for k, v in PB.HALTUNG_RAUM.items()},
        # "cat|label" -> families, because JSON keys cannot be tuples.
        "stimmungNurFuer": {"%s|%s" % k: sorted(v)
                            for k, v in EB.STIMMUNG_NUR_FUER.items()},
        "haltungArme": {k: list(v) for k, v in PB.HALTUNG_ARME.items()},
        "haltungBeine": {k: list(v) for k, v in PB.HALTUNG_BEINE.items()},
        "kameraFormate": {k: list(v) for k, v in SH.KAMERA_FORMATE.items()},
        # The perspective axis (selfie mode) and its couplings, as plane()
        # applies them.
        "perspektive": [{"label": lbl, "wert": wert} for lbl, wert in SH.PERSPEKTIVE],
        "perspektiveGruppen": {k: list(v) for k, v in SH.PERSPEKTIVE_GRUPPEN.items()},
        "perspektiveKamera": {k: list(v) for k, v in SH.PERSPEKTIVE_KAMERA.items()},
        "perspektiveFormate": {k: list(v) for k, v in SH.PERSPEKTIVE_FORMATE.items()},
        "perspektiveHaltung": {k: list(v) for k, v in SH.PERSPEKTIVE_HALTUNG.items()},
        "perspektiveKoerper": {k: list(v) for k, v in SH.PERSPEKTIVE_KOERPER.items()},
        "perspektiveBlick": dict(SH.PERSPEKTIVE_BLICK),
        "selfies": list(SH.SELFIES),
        "selfieKoerper": list(SH.SELFIE_KOERPER),
        "eineHandFrei": list(PB.EINE_HAND_FREI),
        "selfieGesten": list(PB.SELFIE_GESTEN),
        "requisiten": list(PB.REQUISITEN),
        "kameraOptik": dict(SH.KAMERA_OPTIK),
        "stimmungNurAufWahl": [l for l, _ in EB.PRESETS["stimmung"] if EB.nur_auf_wahl(l)],
        "slotPerspektive": SH.SLOT_PERSPEKTIVE,
        # Person detail level per framing (identity/figure/full) - the preview
        # can show it too, without asking the server.
        "kameraDetail": {lbl: PeB.detail_fuer_kamera(lbl) for lbl, _ in SH.KAMERA},
        "ratios": {k: list(v) for k, v in SH.RATIOS.items()},
        "kanten": list(SH.KANTEN),
        "kanteStandard": SH.KANTE_STANDARD,
        "rezepte": [{"name": n, "beschreibung": b, "patch": patch}
                    for n, b, patch in SH.REZEPTE],
        "boegen": {k: [list(st) for st in v] for k, v in SH.STIMMUNGSBOEGEN.items()},
        # Gaze modes of a series (state["blick"]) - the preview plans them
        # with the same tables as plane().
        "blick": {"modi": list(SH.BLICK_MODI), "kamera": SH.BLICK_KAMERA,
                  "weg": SH.blick_weg(), "wegStimmungen": list(SH.BLICK_WEG_STIMMUNGEN),
                  "kameraStimmungen": list(SH.BLICK_KAMERA_STIMMUNGEN),
                  "schulterKoerper": SH.SCHULTER_KOERPER, "schulterBlick": SH.SCHULTER_BLICK,
                  # the panel's chip row: name and tooltip per mode
                  "namen": {m: {"name": n, "beschreibung": b}
                            for m, (n, b) in SH.BLICK_NAMEN.items()}},
        "felder": [{"cat": cat, "quelle": q} for cat, q in SH.FELDER],
        # The set and light axes (set_fuer(), licht_fuer(), szene_fuer()):
        # the slots are len(felder) + 4 and + 5, as in shooting.py.
        "set": {"folgen": list(SH.SET_FOLGEN), "kurz": list(SH.SET_KURZ), "weg": list(SH.SET_WEG)},
        "licht": {"folgen": list(SH.LICHT_FOLGEN),
                  "setups": [lbl for lbl, _ in LB.PRESETS["setup"]],
                  "familien": {k: list(v) for k, v in LB.LICHT_GRUPPEN.items()},
                  "nurDraussen": list(SH.LICHT_NUR_DRAUSSEN),
                  "nurDrinnen": list(SH.LICHT_NUR_DRINNEN),
                  "tageslauf": [[name, list(stufe)] for name, stufe in SH.TAGESLAUF]},
        "nenner": SH._NENNER,
        "wurzeln": list(SH._WURZELN),
        "gruppen": {
            "pose": {"feld": "haltung",
                     "familien": {k: list(v) for k, v in PB.HALTUNG_GRUPPEN.items()}},
            "ausdruck": {"feld": "stimmung",
                         "familien": {k: list(v) for k, v in EB.STIMMUNG_GRUPPEN.items()}},
        },
        "listen": {
            "pose": {cat: [lbl for lbl, _ in PB.PRESETS[cat]] + EG.wuerfelbar("pose", cat)
                     for cat in PB.FOLGE},
            "ausdruck": {cat: [lbl for lbl, _ in EB.PRESETS[cat]] + EG.wuerfelbar("ausdruck", cat)
                         for cat in EB.FOLGE},
        },
        "vorgabe": copy.deepcopy(SH.DEFAULT_STATE),
        "modellProfile": list(SH.MODELL_PROFILE),
        "kameraKompakt": [{"label": lbl, "wert": w} for lbl, w in SH.KAMERA_KOMPAKT],
        "paarInteraktionen": [{"label": lbl, "wert": w} for lbl, w in SH.PAAR_INTERAKTIONEN],
        "leer": SH.NONE,
        "alle": SH.ALLE,
    }


def plane_serie_daten(daten):
    """Compute a series plan on the server from the same Python functions as
    Krea2Photoshooting.shoot()."""
    if not isinstance(daten, dict):
        raise ValueError("JSON object expected")
    state = daten.get("state")
    if state is None:
        state = copy.deepcopy(SH.DEFAULT_STATE)
    elif not isinstance(state, dict):
        raise ValueError("state must be an object")

    outfits_roh = daten.get("outfits", 0)
    outfits = len(outfits_roh) if isinstance(outfits_roh, list) else max(0, int(outfits_roh or 0))

    saetze_roh = daten.get("saetze", 0)
    if isinstance(saetze_roh, list):
        draussen = [s.get("draussen") if isinstance(s, dict) else s for s in saetze_roh]
        saetze = len(draussen)
    else:
        saetze = max(0, int(saetze_roh or 0))
        draussen = [None] * saetze

    laeufe_roh = daten.get("laeufe")
    if laeufe_roh is None:
        start = max(1, int(state.get("start") or 1))
        anzahl = max(1, min(int(state.get("anzahl") or 12), 500))
        laeufe = list(range(start - 1, start - 1 + anzahl))
    else:
        if not isinstance(laeufe_roh, list):
            raise ValueError("laeufe must be a list")
        laeufe = [max(0, int(x)) for x in laeufe_roh]

    kante = int(state.get("groesse") or SH.KANTE_STANDARD)
    fotos = []
    for lauf in laeufe:
        plan = SH.plane(state, lauf, outfits, saetze)
        fmt = SH.format_fuer(plan["kamera"], lauf, state, plan["perspektive"])
        w, h = SH.masse_fuer(fmt, kante)
        fotos.append({
            "lauf": lauf,
            "foto": lauf + 1,
            "kamera": plan["kamera"],
            "fokus": plan["fokus"],
            "perspektive": plan["perspektive"],
            "pose": plan["pose"],
            "ausdruck": plan["ausdruck"],
            "format": fmt,
            "masse": [w, h],
            "outfit": SH.outfit_fuer(state, lauf, outfits),
            "set": SH.set_fuer(state, lauf, saetze),
            "licht": SH.licht_fuer(state, lauf, draussen),
        })
    return {"fotos": fotos}


def baue_vorschau_daten(daten):
    """Resolve a builder's current state (including active dice) into its
    English prompt string using the exact Python builder."""
    if not isinstance(daten, dict):
        raise ValueError("JSON object expected")
    bereich = daten.get("bereich")
    seed = max(0, int(daten.get("seed") or 0))
    state = daten.get("state")
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    if bereich == "pose":
        text = PB.Krea2PoseBuilder().build(seed=seed, PoseState=json.dumps(state))[0]
    elif bereich == "ausdruck":
        text = EB.Krea2ExpressionBuilder().build(seed=seed, ExpressionState=json.dumps(state))[0]
    elif bereich == "lighting":
        text = LB.Krea2LightingBuilder().build(seed=seed, LightingState=json.dumps(state))[0]
    elif bereich == "style":
        text = SB.Krea2StyleBuilder().build(seed=seed, StyleState=json.dumps(state))[0]
    elif bereich == "location":
        text = OB.Krea2LocationBuilder().build(
            seed=seed, LocationState=json.dumps({"saetze": [state], "aktiv": 0}))[0]
    else:
        raise ValueError("unknown builder: %s" % bereich)
    return {"prompt": text}


def baue_studio_vorschau(daten):
    """Resolve the full prompt, block breakdown, dimensions and motion cue for a photo."""
    if not isinstance(daten, dict):
        raise ValueError("JSON object expected")
    state = copy.deepcopy(daten.get("state") if daten.get("state") is not None else SH.DEFAULT_STATE)
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    foto = max(1, int(daten.get("foto") or state.get("start") or 1))

    def _als_json(val):
        if val is None or val == "":
            return None
        return val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)

    res = SH.Krea2Photoshooting().shoot(
        foto=foto,
        ShootingState=json.dumps(state, ensure_ascii=False),
        person_data=_als_json(daten.get("person_data")),
        ort_data=_als_json(daten.get("ort_data")),
        person_2_data=_als_json(daten.get("person_2_data")),
    )
    (pose, ausdruck, kamera, w, h, seed, person, _pd, kamera_label,
     _refine, _dateiname, _caption, foto_nr, szene, licht, prompt, motion) = res

    stil = (SB.Krea2StyleBuilder().build(seed=max(0, foto_nr - 1), StyleState=json.dumps(state["_style"]))[0]
            if isinstance(state.get("_style"), dict) else "")

    neu_bauen = False
    if not licht and str(daten.get("lighting_text") or "").strip():
        licht = str(daten["lighting_text"]).strip()
        neu_bauen = True
    if not szene and str(daten.get("scene_text") or "").strip():
        szene = str(daten["scene_text"]).strip()
        neu_bauen = True
    if not stil and str(daten.get("style_text") or "").strip():
        stil = str(daten["style_text"]).strip()
        neu_bauen = True
    vorlage = str(state.get("_template") or "")
    if not vorlage and str(daten.get("template_text") or "").strip():
        vorlage = str(daten["template_text"]).strip()
        neu_bauen = True

    if neu_bauen:
        prompt = ST.Krea2PromptJoin().join(
            vorlage, person_1=person, kamera=kamera, pose=pose,
            ausdruck=ausdruck, licht=licht, szene=szene, stil=stil)["result"][0]

    return {
        "foto": foto_nr,
        "prompt": prompt,
        "motion": motion,
        "words": len(prompt.split()) if prompt else 0,
        "width": w,
        "height": h,
        "seed": seed,
        "kamera_label": kamera_label,
        "blocks": {
            "style": stil,
            "expression": ausdruck,
            "camera": kamera,
            "scene": szene,
            "lighting": licht,
            "person": person,
            "pose": pose,
        },
    }


def _dekodiere_base64(roh, max_bytes):
    if not isinstance(roh, str) or not roh.strip():
        raise ValueError("base64 data missing")
    s = roh.strip()
    if s.startswith("data:") and "," in s:
        s = s.split(",", 1)[1].strip()
    if len(s) > (max_bytes * 4 // 3) + 1024:
        raise ValueError("payload too large")
    try:
        raw = base64.b64decode(s, validate=True)
    except (ValueError, binascii.Error) as e:
        raise ValueError("invalid base64 data") from e
    if len(raw) > max_bytes:
        raise ValueError("payload too large")
    return raw


def _paket_version():
    pfad = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pyproject.toml")
    try:
        with open(pfad, "r", encoding="utf-8") as fh:
            m = re.search(r'^version\s*=\s*"([^"]+)"', fh.read(), re.M)
            return m.group(1) if m else "3.1.0"
    except OSError:
        return "3.1.0"


def _locale():
    """The stored language setting, if the server knows it.

    A second source next to the front-end setting: the JS side cannot always
    reach app.extensionManager.setting - depending on when it loads and on the
    front-end version there is nothing there yet, and it then falls back to the
    browser language even though something else was explicitly chosen. This is
    the value the user actually set.
    """
    try:
        import app.user_manager  # noqa: F401  (only to locate the path)
    except ImportError:
        pass
    try:
        import folder_paths
        pfad = os.path.join(folder_paths.get_user_directory(),
                            "default", "comfy.settings.json")
        with open(pfad, "r", encoding="utf-8") as fh:
            return json.load(fh).get("Comfy.Locale") or None
    except (OSError, ValueError, ImportError, AttributeError):
        return None


def _familie(name, gruppen):
    """The family a custom entry names: the key itself ("stimmung"), or its
    English display name as the interface shows it ("Mood"), any case; a new
    name becomes a family of its own, no name means "Eigene"."""
    name = (name or "").strip()
    if not name or name.lower() in (EG.FAMILIE.lower(), str(i18n.FAMILIEN.get(EG.FAMILIE, "")).lower()):
        return EG.FAMILIE
    if name in gruppen:
        return name
    klein = name.lower()
    for key in gruppen:
        if klein in (key.lower(), str(i18n.FAMILIEN.get(key, "")).lower()):
            return key
    return name


def _eigene_einfuegen(daten):
    """Custom entries (eigene.py) into the lists, marked "eigen". They go into
    the family they name, or into "Eigene"; colour fields get their swatch,
    the display table their English name. Works on copies - FARBWERTE and the
    i18n tables are module data and must not grow with every request."""
    if not EG.EINTRAEGE:
        return daten
    daten["i18n"] = copy.deepcopy(daten["i18n"])
    daten["person"]["farben"] = {k: dict(v) for k, v in daten["person"]["farben"].items()}
    for (builder, feld), liste in EG.EINTRAEGE.items():
        ziel = daten.get(builder)
        felder = (ziel or {}).get("felder", {}).get(feld)
        if felder is None:   # a field this interface does not show
            continue
        if builder == "person":
            gruppen = ziel["gruppen"].get(feld)
        else:
            gruppen = ziel["gruppen"] if feld == ziel["gruppenFeld"] else None
        anzeige = daten["i18n"].setdefault(builder, {}).setdefault(feld, {})
        for e in liste:
            felder.append({"label": e["label"], "wert": e["wert"], "eigen": True})
            if gruppen is not None:
                gruppen.setdefault(_familie(e["gruppe"], gruppen), []).append(e["label"])
            if builder == "person" and feld in ziel["farben"]:
                ziel["farben"][feld][e["label"]] = e["hex"]
            anzeige[e["label"]] = e["en"]
    # Mirror custom props (person/prop) into Pose -> Arms (pose/arme).
    props = EG.EINTRAEGE.get(("person", "prop")) or []
    if props:
        arme = daten["pose"]["felder"]["arme"]
        schon = {e["label"] for e in arme}
        anzeige = daten["i18n"].setdefault("pose", {}).setdefault("arme", {})
        for e in props:
            if e["label"] in schon:
                continue
            arme.append({"label": e["label"], "wert": PB.requisit_text(e["wert"]), "eigen": True})
            anzeige[e["label"]] = e["en"]
            schon.add(e["label"])
    return daten


def presets():
    return _eigene_einfuegen({
        "pose": _beschreibung(PB, "haltung", PB.HALTUNG_GRUPPEN, "pose"),
        "ausdruck": _beschreibung(EB, "stimmung", EB.STIMMUNG_GRUPPEN),
        "lighting": _beschreibung(LB, "setup", LB.LICHT_GRUPPEN, "lighting"),
        "style": _beschreibung(SB, "look", SB.LOOK_GRUPPEN, builder="style"),
        "location": _location(),
        "person": _person(),
        "shooting": _shooting(),
        # Display labels for other languages. The German labels stay the keys
        # everywhere - only what the user reads gets translated. See
        # nodes/i18n.py.
        "i18n": i18n.tabelle(),
        "locale": _locale(),
        # Files and messages of the custom entries, for the interface.
        "custom": EG.stand(),
        # Shoot files (shoot_datei.py): which node class and property holds
        # each section, and which inputs of Series and Build Prompt lead to it.
        "shoot": {"format": SD.FORMAT,
                  "abschnitte": {k: {"klasse": c, "prop": p} for k, (c, p) in SD.ABSCHNITTE.items()},
                  "eingaenge": {k: list(v) for k, v in SD.EINGAENGE.items()},
                  "texte": list(SD.TEXTE)},
    })


def register():
    """Register the route.

    Fails quietly when there is no server behind it - importing outside of
    ComfyUI (tests) the module is missing, and in theory a future version could
    bring the custom nodes up before the server. Without this guard an
    AttributeError would take the whole package with it and every node here
    would be gone, not just the interface.
    """
    try:
        # Both imported here rather than at module level: aiohttp belongs to
        # ComfyUI, not to this package. An import at module level would do the
        # very damage this try block guards against - without aiohttp every node
        # here would be gone, not just the route.
        from aiohttp import web
        from server import PromptServer
        routes = PromptServer.instance.routes
    except (ImportError, AttributeError) as e:
        print("[Photoshoot] No PromptServer (%s), preset route skipped." % e)
        return

    # Saved series of the Series panel (store.py). Answers always carry the
    # whole list, so the panel needs no second request after saving.
    from . import store as ST

    def _serien_antwort():
        return web.json_response(ST.serien_liste(), headers={"Cache-Control": "no-store"})

    @routes.get("/krea2/serien")
    async def _serien(_request):
        return _serien_antwort()

    @routes.post("/krea2/serien")
    async def _serie_speichern(request):
        try:
            daten = await request.json()
            ST.serie_speichern(daten.get("name"), daten.get("patch"))
        except (ValueError, TypeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)
        return _serien_antwort()

    @routes.post("/krea2/serien/loeschen")
    async def _serie_loeschen(request):
        try:
            ST.serie_loeschen((await request.json()).get("name"))
        except (ValueError, TypeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)
        return _serien_antwort()

    # Selects → next round (naechste_runde() in shooting.py). The panel sends
    # its state and the number of outfits it sees on the wardrobe (and of sets
    # on the Location node) and applies
    # the state that comes back; computed here only, so the logic has no copy
    # in JS. {"state": null} means there were no selects to go on.
    @routes.post("/krea2/serien/naechste_runde")
    async def _naechste_runde(request):
        try:
            daten = await request.json()
            state = daten.get("state")
            if not isinstance(state, dict):
                raise ValueError("state missing")
            neu = SH.naechste_runde(state, max(0, int(daten.get("outfits") or 0)),
                                    max(0, int(daten.get("saetze") or 0)))
        except (ValueError, TypeError, AttributeError) as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"state": neu}, headers={"Cache-Control": "no-store"})

    # Saved scenes (store.py, ComfyUI/user/krea2_scenes) for the Location
    # panel: a click puts one into a set's free text. Read on every request,
    # so a scene saved a moment ago is there without a refresh.
    @routes.get("/krea2/szenen")
    async def _szenen(_request):
        return web.json_response(ST.szenen_liste(), headers={"Cache-Control": "no-store"})

    # Saved building blocks (person, stil, licht, szene) with full builder
    # state and text so panels can save/load live without a node refresh.
    @routes.get("/krea2/bausteine")
    async def _bausteine(request):
        try:
            art = request.query.get("art", "")
            return web.json_response(ST.baustein_liste(art), headers={"Cache-Control": "no-store"})
        except ValueError as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/bausteine")
    async def _baustein_speichern(request):
        try:
            daten = await request.json()
            art = daten.get("art", "")
            ST.baustein_speichern(art, daten.get("name"), daten.get("text", ""), daten.get("state"))
            return web.json_response(ST.baustein_liste(art), headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/bausteine/loeschen")
    async def _baustein_loeschen(request):
        try:
            daten = await request.json()
            art = daten.get("art", "")
            ST.baustein_loeschen(art, daten.get("name"))
            return web.json_response(ST.baustein_liste(art), headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    # Character cards (Casting-Deck in Studio -> Person): save/load complete
    # Person + Wardrobe + optional LoRA metadata under ComfyUI/user/krea2_characters/.
    @routes.get("/krea2/characters")
    async def _charaktere(_request):
        return web.json_response({"characters": ST.charakter_liste()}, headers={"Cache-Control": "no-store"})

    @routes.post("/krea2/characters")
    async def _charakter_speichern(request):
        try:
            daten = await request.json()
            name = ST.charakter_speichern(daten.get("name"), daten)
            return web.json_response({"ok": True, "name": name, "characters": ST.charakter_liste()},
                                     headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/characters/delete")
    async def _charakter_loeschen(request):
        try:
            daten = await request.json()
            ST.charakter_loeschen(daten.get("name"))
            return web.json_response({"ok": True, "characters": ST.charakter_liste()},
                                     headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.get("/krea2/characters/portrait")
    async def _charakter_portrait_lesen(request):
        name = request.query.get("name", "")
        bild = ST.charakter_portrait_lesen(name)
        if not bild:
            return web.json_response({"error": "portrait not found"}, status=404,
                                     headers={"Cache-Control": "no-store"})
        raw, ctype = bild
        return web.Response(body=raw, content_type=ctype, headers={"Cache-Control": "no-store"})

    @routes.post("/krea2/characters/portrait")
    async def _charakter_portrait_speichern(request):
        try:
            daten = await request.json()
            name = daten.get("name")
            if daten.get("delete"):
                ST.charakter_portrait_loeschen(name)
            else:
                raw = _dekodiere_base64(daten.get("data"), ST.PORTRAIT_MAX_BYTES)
                ST.charakter_portrait_speichern(name, raw)
            return web.json_response({"ok": True, "characters": ST.charakter_liste()},
                                     headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/prompt_vorschau")
    async def _prompt_vorschau(request):
        try:
            return web.json_response(baue_studio_vorschau(await request.json()),
                                     headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.get("/krea2/backup/status")
    async def _backup_status(_request):
        return web.json_response(ST.speicher_status(), headers={"Cache-Control": "no-store"})

    @routes.get("/krea2/backup/export")
    async def _backup_export(_request):
        try:
            daten = ST.backup_erzeugen(_paket_version())
            datum = time.strftime("%Y-%m-%d")
            return web.Response(
                body=daten,
                content_type="application/zip",
                headers={
                    "Content-Disposition": 'attachment; filename="photoshoot-backup-%s.zip"' % datum,
                    "Cache-Control": "no-store",
                },
            )
        except (RuntimeError, ValueError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/backup/import")
    async def _backup_import(request):
        try:
            daten = await request.json()
            raw = _dekodiere_base64(daten.get("data"), ST.BACKUP_MAX_BYTES)
            ergebnis = ST.backup_einspielen(raw, ueberschreiben=bool(daten.get("overwrite")))
            EG.lade()
            return web.json_response({
                **ergebnis,
                "status": ST.speicher_status(),
                "characters": ST.charakter_liste(),
            }, headers={"Cache-Control": "no-store"})
        except (RuntimeError, ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/vorschau")
    async def _vorschau(request):
        try:
            return web.json_response(baue_vorschau_daten(await request.json()),
                                     headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError) as e:
            return web.json_response({"error": str(e)}, status=400)

    # Custom entries (eigene.py): read once at start, then on request. Every
    # answer is the whole state - files, messages, count - like the series.
    # Users open these addresses themselves, so they and their keys are
    # English, unlike the routes only the panels call.
    EG.lade()

    def _eigene_antwort(extra=None, status=200):
        return web.json_response({**EG.stand(), **(extra or {})}, status=status,
                                 headers={"Cache-Control": "no-store"})

    @routes.get("/krea2/custom")
    async def _eigene(_request):
        return _eigene_antwort()

    # The built-in entries in the file format, as a template to copy from.
    # tools/exportiere_presets.py writes the same, but tools/ is not shipped.
    @routes.get("/krea2/custom/template")
    async def _eigene_vorlage(_request):
        eintraege = []
        for b in ("person", "pose", "ausdruck", "lighting", "style", "location"):
            eintraege += EG.exportiere_kern(b)["entries"]
        return web.json_response({"format": EG.FORMAT, "name": "Built-in entries (template)",
                                  "entries": eintraege},
                                 dumps=lambda d: json.dumps(d, ensure_ascii=False, indent=1))

    # A prompt for any chat LLM that writes such a file (llm_prompt.py), built
    # from the live presets so it never names a field that does not exist.
    @routes.get("/krea2/custom/llm_prompt")
    async def _eigene_llm_prompt(_request):
        from . import llm_prompt
        return web.Response(text=llm_prompt.erzeuge(), content_type="text/plain", charset="utf-8",
                            headers={"Cache-Control": "no-store"})

    @routes.post("/krea2/custom/reload")
    async def _eigene_neu(_request):
        EG.lade()
        return _eigene_antwort()

    @routes.post("/krea2/custom/import")
    async def _eigene_import(request):
        # {"file": name, "content": {...the file...}, "replace": bool}
        try:
            daten = await request.json()
            datei, meldungen = EG.speichere(daten.get("file"), daten.get("content"),
                                            bool(daten.get("replace")))
        except FileExistsError as e:
            return _eigene_antwort({"error": "exists", "file": str(e)}, status=409)
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _eigene_antwort({"error": str(e)}, status=400)
        return _eigene_antwort({"file": datei, "hints": meldungen})

    @routes.post("/krea2/custom/delete")
    async def _eigene_loeschen(request):
        try:
            EG.loesche((await request.json()).get("file"))
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _eigene_antwort({"error": str(e)}, status=400)
        return _eigene_antwort()

    @routes.post("/krea2/custom/add")
    async def _eigene_hinzufuegen(request):
        try:
            daten = await request.json()
            lbl, meldungen = EG.fuege_hinzu(
                daten.get("builder"), daten.get("field"),
                daten.get("label"), daten.get("prompt"),
                daten.get("group", ""), daten.get("hex", ""),
            )
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _eigene_antwort({"error": str(e)}, status=400)
        return _eigene_antwort({"label": lbl, "hints": meldungen})

    @routes.post("/krea2/custom/remove_entry")
    async def _eigene_eintrag_loeschen(request):
        try:
            daten = await request.json()
            EG.entferne_eintrag(daten.get("builder"), daten.get("field"), daten.get("label"))
        except FileNotFoundError as e:
            return _eigene_antwort({"error": str(e)}, status=404)
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _eigene_antwort({"error": str(e)}, status=400)
        return _eigene_antwort()

    @routes.get("/krea2/custom/export")
    async def _eigene_exportieren(request):
        try:
            name, pack = EG.lese_pack(request.query.get("file", ""))
            return web.json_response({"ok": True, "file": name, "pack": pack},
                                     headers={"Cache-Control": "no-store"})
        except FileNotFoundError as e:
            return web.json_response({"error": str(e)}, status=404)
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.post("/krea2/custom/update_pack")
    async def _eigene_pack_bearbeiten(request):
        try:
            daten = await request.json()
            hints = []
            if "entry" in daten and isinstance(daten["entry"], dict):
                _lbl, hints = EG.bearbeite_eintrag(
                    daten.get("file"), daten.get("builder"), daten.get("field"),
                    daten.get("old_label"), daten["entry"],
                )
            elif "dice" in daten:
                EG.setze_pack_wuerfel(daten.get("file"), bool(daten.get("dice")), daten.get("name"))
            else:
                raise ValueError("nothing to update")
        except FileNotFoundError as e:
            return _eigene_antwort({"error": str(e)}, status=404)
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _eigene_antwort({"error": str(e)}, status=400)
        return _eigene_antwort({"ok": True, "hints": hints})

    # Shoot files (shoot_datei.py) and the Director (regie.py). Users open and
    # share these, so routes and keys are English, like /krea2/custom. Every
    # answer that changes the store carries the whole list, as the series do.
    from . import regie as RG

    def _shoots_antwort(extra=None, status=200):
        return web.json_response({"folder": SD.ordner(), "shoots": SD.liste(), **(extra or {})},
                                 status=status, headers={"Cache-Control": "no-store"})

    def _pruef_antwort(shoot, fehler, hinweise):
        return web.json_response({"shoot": shoot, "errors": fehler, "notes": hinweise},
                                 headers={"Cache-Control": "no-store"})

    @routes.get("/krea2/shoots")
    async def _shoots(_request):
        return _shoots_antwort()

    @routes.get("/krea2/shoots/load")
    async def _shoot_laden(request):
        try:
            return _pruef_antwort(*SD.lade(request.query.get("name")))
        except (ValueError, OSError) as e:
            return web.json_response({"error": str(e)}, status=404)

    @routes.post("/krea2/shoots/save")
    async def _shoot_speichern(request):
        # {"name": ..., "shoot": {...the shoot file...}}
        try:
            daten = await request.json()
            name, fehler = SD.speichere(daten.get("name"), daten.get("shoot"))
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _shoots_antwort({"error": str(e)}, status=400)
        return _shoots_antwort({"name": name, "errors": fehler})

    @routes.post("/krea2/shoots/delete")
    async def _shoot_loeschen(request):
        try:
            SD.loesche((await request.json()).get("name"))
        except (ValueError, TypeError, AttributeError, OSError) as e:
            return _shoots_antwort({"error": str(e)}, status=400)
        return _shoots_antwort()

    # A shoot file from disk (the panel's "open file"): checked, not stored.
    @routes.post("/krea2/shoots/check")
    async def _shoot_pruefen(request):
        try:
            daten = await request.json()
        except ValueError as e:
            return _pruef_antwort(None, ["not valid JSON: %s" % e], [])
        return _pruef_antwort(*SD.pruefe(daten.get("shoot") if isinstance(daten, dict) else None))

    @routes.get("/krea2/director/llm_prompt")
    async def _regie_prompt(request):
        text = RG.erzeuge(request.query.get("brief", ""), request.query.get("mode", "brief"))
        return web.Response(text=text, content_type="text/plain", charset="utf-8",
                            headers={"Cache-Control": "no-store"})

    @routes.post("/krea2/director/import")
    async def _regie_import(request):
        # {"answer": "...the chat answer, as pasted..."}
        try:
            daten = await request.json()
        except ValueError as e:
            return web.json_response({"shoot": None, "errors": [str(e)], "notes": []})
        return web.json_response(RG.importiere((daten or {}).get("answer")),
                                 headers={"Cache-Control": "no-store"})

    # Offline: the brief's words matched against the English labels.
    @routes.post("/krea2/director/draft")
    async def _regie_entwurf(request):
        try:
            daten = await request.json()
        except ValueError as e:
            return web.json_response({"shoot": None, "errors": [str(e)], "notes": []})
        return web.json_response(RG.entwurf((daten or {}).get("brief", "")),
                                 headers={"Cache-Control": "no-store"})

    # The preview text for an outfit card (wardrobe.py). The panel sends a
    # Wardrobe node's state and swaps the answer into Build Prompt for one run.
    from . import wardrobe as WR

    @routes.post("/krea2/outfit_vorschau")
    async def _outfit_vorschau(request):
        try:
            daten = await request.json()
            art = "flach" if daten.get("art") == "flach" else "puppe"
            text = WR.vorschau_aus_state(daten.get("state") or {}, art)
        except (ValueError, TypeError, AttributeError) as e:
            return web.json_response({"error": str(e)}, status=400)
        return web.json_response({"prompt": text}, headers={"Cache-Control": "no-store"})

    @routes.post("/krea2/plan")
    async def _serie_planen(request):
        try:
            daten = await request.json()
            return web.json_response(plane_serie_daten(daten), headers={"Cache-Control": "no-store"})
        except (ValueError, TypeError, AttributeError) as e:
            return web.json_response({"error": str(e)}, status=400)

    @routes.get("/krea2/presets")
    async def _handler(_request):
        # Without these headers the browser decides for itself whether to
        # reuse the response - it used to carry only ETag and Last-Modified.
        # The consequence: newly added fields did not appear even though the
        # server had long been serving them, and it looked like a bug in the
        # interface.
        return web.json_response(presets(), headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        })
