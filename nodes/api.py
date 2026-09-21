"""
Serves the preset tables to the interface.

Without this route, every label and every English equivalent would have to
exist a second time in JavaScript - two lists that would inevitably drift
apart. This way Python stays the single source, and the live preview inside
the node can assemble the English sentence without asking the server.
"""

import copy
import json
import os

from . import eigene as EG
from . import expression_builder as EB
from . import i18n
from . import lighting_builder as LB
from . import person_builder as PeB
from . import pose_builder as PB
from . import shooting as SH
from . import style_builder as SB
from . import vorschau as VS


def _felder(modul):
    """Put PRESETS into the shape the interface needs."""
    return {cat: [{"label": lbl, "wert": wert} for lbl, wert in modul.PRESETS[cat]]
            for cat in modul.FOLGE}


def _beschreibung(modul, gruppen_feld, gruppen):
    return {
        "reihenfolge": list(modul.FOLGE),
        "felder": _felder(modul),
        "gruppenFeld": gruppen_feld,
        "gruppen": {name: list(labels) for name, labels in gruppen.items()},
        "leer": modul.NONE,
        "alle": modul.ALLE,
    }


def _mit_bild(eintrag, cat):
    """The entry with the path of its thumbnail (vorschau.py), where there is one."""
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
        "farben": PeB.FARBWERTE,
        "farbeEntfaellt": {cat: [feld, list(werte)]
                           for cat, (feld, werte) in PeB.FARBE_ENTFAELLT.items()},
        "eigenerStoff": PeB._EIGENER_STOFF.pattern,
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
        # Person detail level per framing (identity/figure/full) - the preview
        # can show it too, without asking the server.
        "kameraDetail": {lbl: PeB.detail_fuer_kamera(lbl) for lbl, _ in SH.KAMERA},
        "ratios": {k: list(v) for k, v in SH.RATIOS.items()},
        "kanten": list(SH.KANTEN),
        "kanteStandard": SH.KANTE_STANDARD,
        "rezepte": [{"name": n, "beschreibung": b, "patch": patch}
                    for n, b, patch in SH.REZEPTE],
        "boegen": {k: [list(st) for st in v] for k, v in SH.STIMMUNGSBOEGEN.items()},
        "felder": [{"cat": cat, "quelle": q} for cat, q in SH.FELDER],
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
        "leer": SH.NONE,
        "alle": SH.ALLE,
    }


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
    return daten


def presets():
    return _eigene_einfuegen({
        "pose": _beschreibung(PB, "haltung", PB.HALTUNG_GRUPPEN),
        "ausdruck": _beschreibung(EB, "stimmung", EB.STIMMUNG_GRUPPEN),
        "lighting": _beschreibung(LB, "setup", LB.LICHT_GRUPPEN),
        "style": _beschreibung(SB, "look", SB.LOOK_GRUPPEN),
        "person": _person(),
        "shooting": _shooting(),
        # Display labels for other languages. The German labels stay the keys
        # everywhere - only what the user reads gets translated. See
        # nodes/i18n.py.
        "i18n": i18n.tabelle(),
        "locale": _locale(),
        # Files and messages of the custom entries, for the interface.
        "custom": EG.stand(),
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
        for b in ("person", "pose", "ausdruck", "lighting", "style"):
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
