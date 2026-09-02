"""
Serves the preset tables to the interface.

Without this route, every label and every English equivalent would have to
exist a second time in JavaScript - two lists that would inevitably drift
apart. This way Python stays the single source, and the live preview inside
the node can assemble the English sentence without asking the server.
"""

import json
import os

from . import expression_builder as EB
from . import i18n
from . import lighting_builder as LB
from . import person_builder as PeB
from . import pose_builder as PB
from . import shooting as SH
from . import style_builder as SB


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


def _person():
    """The person has more fields than pose and expression, so it needs tabs
    and a different kind of control per field."""
    felder = {cat: [{"label": lbl, "wert": wert} for lbl, wert in PeB.PRESETS[cat]]
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
                              for name, labels in PeB.SCHUH_GRUPPEN.items()}},
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
            "pose": {cat: [lbl for lbl, _ in PB.PRESETS[cat]] for cat in PB.FOLGE},
            "ausdruck": {cat: [lbl for lbl, _ in EB.PRESETS[cat]] for cat in EB.FOLGE},
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


def presets():
    return {
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
    }


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
