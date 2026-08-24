#!/usr/bin/env python3
"""
Generates the example workflow example_workflows/photoshoot-series.json.

Workflows exported by hand carry along whatever state they happened to be in -
model names from one's own installation, half-unfolded panels, nodes that have
been dragged around. That is why the example workflow is built here: the wiring
stands as a list, the positions are computed, and after every change to the
nodes it can simply be regenerated.

    python3 tools/baue_workflow.py           # the series workflow
    python3 tools/baue_workflow.py --anker   # the anchor-set variant

If ComfyUI is running, the script checks every node type, every input name and
every output index against /object_info. Without a running server the workflow
is still written, only unchecked.
"""

import json
import pathlib
import sys
import urllib.error
import urllib.request

WURZEL = pathlib.Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "example_workflows" / "photoshoot-series.json"
ANKER_ZIEL = WURZEL / "example_workflows" / "photoshoot-anchor-set.json"
SERVER = "http://127.0.0.1:8188"

# The file names Comfy-Org publishes for Krea 2, so the example matches what
# someone who followed the official ComfyUI tutorial already has on disk:
# https://huggingface.co/Comfy-Org/Krea-2
#
# Deliberately not whatever happens to sit in the development installation -
# local subfolders and privately renamed files make loaders that nobody else can
# resolve. If a user has other names, ComfyUI flags the loader nodes on load and
# they pick their own; the rest of the graph is unaffected.
#
# The encoder is not interchangeable: Krea 2 taps 12 layers of Qwen3-VL-4B at a
# hidden size of 2560 (see comfy/text_encoders/krea2.py). Plain Qwen3-4B has no
# vision tower and the 32B build has the wrong width - neither will load.
UNET = "krea2_turbo_fp8_scaled.safetensors"
CLIP = "qwen3vl_4b_fp8_scaled.safetensors"
VAE = "qwen_image_vae.safetensors"

# The English spelling of the placeholders - the German ones still work, but
# they have no business in an example that everyone opens.
VORLAGE = "{camera}, {scene}, {person}, {pose}, {expression}, {style}"
SZENE = "a sunlit loft with tall windows, wooden floor, plants in the corner"
STIL = "editorial photography, 85mm, natural light, shallow depth of field"

# The graph. Each entry: (id, type, column, row, widgets, title)
# Column and row are grid slots, not pixels - the grid is computed below.
NODES = [
    (1,  "UNETLoader",               0, 0, [UNET, "default"],            "Krea 2 model"),
    (2,  "CLIPLoader",               0, 1, [CLIP, "krea2", "default"],   None),
    (3,  "VAELoader",                0, 2, [VAE],                        None),

    (10, "Krea2PersonBuilder",       1, 0, None,                         "1 — build the person"),
    # The Person Builder's state is not in widgets_values but in
    # node.properties (the PixaromaResolution pattern) - see PERSON below.
    (11, "Krea2Photoshooting",       2, 0, [0, "increment"],             "2 — the series"),

    (20, "PrimitiveStringMultiline", 1, 2, [SZENE],                      "scene"),
    (21, "PrimitiveStringMultiline", 1, 3, [STIL],                       "style"),
    (22, "PrimitiveStringMultiline", 2, 2, [VORLAGE],                    "prompt template"),

    (30, "Krea2PromptJoin",          3, 0, None,                         "3 — assemble"),
    (31, "CLIPTextEncode",           4, 0, [""],                         None),
    (32, "ConditioningZeroOut",      4, 1, None,                         "negative = empty"),
    (33, "EmptySD3LatentImage",      4, 2, [1024, 1024, 1],              None),

    (40, "KSampler",                 5, 0, [0, "fixed", 8, 1.0, "euler", "simple", 1.0],
         "pass 1 — 8 steps"),
    (41, "LatentUpscaleBy",          5, 1, ["bislerp", 1.5],             None),
    (42, "KSampler",                 5, 2, [0, "fixed", 4, 1.0, "euler_ancestral", "simple", 0.44],
         "pass 2 — refine at 0.44"),

    (50, "VAEDecode",                6, 0, None,                         None),
    (51, "SaveImage",                6, 1, ["krea2/shoot"],              None),
]

# Links: (from_id, output name, to_id, input name)
# Outputs are addressed by name and translated into indices below - an index
# would be silently wrong as soon as an output is added.
LINKS = [
    (1,  "MODEL",       40, "model"),
    (1,  "MODEL",       42, "model"),
    (2,  "CLIP",        31, "clip"),
    (3,  "VAE",         50, "vae"),

    (10, "person_data", 11, "person_data"),

    (11, "person",      30, "person_1"),
    (11, "pose",        30, "pose"),
    (11, "ausdruck",    30, "ausdruck"),
    (11, "kamera",      30, "kamera"),
    (11, "width",       33, "width"),
    (11, "height",      33, "height"),
    (11, "bildseed",    40, "seed"),
    (11, "bildseed",    42, "seed"),

    (20, "STRING",      30, "szene"),
    (21, "STRING",      30, "stil"),
    (22, "STRING",      30, "text"),

    (30, "prompt",      31, "text"),
    (31, "CONDITIONING", 40, "positive"),
    (31, "CONDITIONING", 42, "positive"),
    (31, "CONDITIONING", 32, "conditioning"),
    (32, "CONDITIONING", 40, "negative"),
    (32, "CONDITIONING", 42, "negative"),

    (33, "LATENT",      40, "latent_image"),
    (40, "LATENT",      41, "samples"),
    (41, "LATENT",      42, "latent_image"),
    (42, "LATENT",      50, "samples"),
    (50, "IMAGE",       51, "images"),
]

# A filled-in example person. An empty builder shows nothing but dashes, and
# then you see neither the counters on the tabs nor the preview - precisely what
# makes this node what it is. The values are the same as in the README example.
PERSON_STATE = {
    "felder": {
        "type": "Frau", "age": "Ende 20", "ethnicity": "Skandinavisch",
        "skinTone": "Sehr hell", "complexion": "Natürliche Poren",
        "height": "Groß", "figure": "Athletisch", "shoulders": "Sportlich",
        "hair": "Lange Wellen", "hairColor": "Rot / Kupfer",
        "eyeShape": "Mandelförmig", "eyes": "Graugrün",
        "cheekbones": "Hoch betont", "nose": "Gerade",
        "lipColor": "Altrosa", "lipFinish": "Matt",
        "hosiery": "Nackte Beine", "shoes": "Combat Boots", "shoesColor": "Schwarz",
    },
    "mehrfach": {"skinFeatures": ["Sommersprossen"]},
    "texte": {"ageExact": "", "details": "wearing a charcoal wool coat"},
    "sektion": "Gesicht",
    "gruppe": {"shoes": "alle"},
}

# The anchor-set variant. Everything that differs is state rather than wiring,
# which is why it earns a file of its own: the graph is identical to the series
# workflow, and a paragraph cannot hand someone a filled-in panel.
#
# The noise axis is off, so all six runs share one seed and everything the
# description leaves open is invented once instead of six times - that is what
# holds the person still. The ratio is fixed so the set is uniform, and the mood
# is held to one family, or six reference images swing from beaming to
# tear-stained. Camera, pose and focus keep varying, because those come from the
# prompt rather than from the noise.
# Where a character LoRA goes, shown rather than described. The node ships in
# bypass mode, which passes the MODEL through untouched - the workflow runs as
# it is, and someone with a LoRA picks their file and presses Ctrl+B. Leaving
# it out entirely put the answer in the README; shipping it switched on would
# demand a file nobody has.
ANKER_LORA = (4, "LoraLoaderModelOnly", 0, 3,
              ["your-character-lora.safetensors", 1.0],
              "optional - pick a LoRA, then Ctrl+B")
BYPASS = 4

ANKER_STATE = {
    "anzahl": 6,
    "aktiv": {"kamera": True, "pose": True, "ausdruck": True, "format": False,
              "fokus": True, "rausch": False},
    "serienSeed": 776610,
    "pools": {"stimmung": "ruhig"},
    "festesFormat": "2:3",
}

GRUPPEN = [
    ("Loaders",              [1, 2, 3],                    "#3f5159"),
    ("Photoshoot",           [10, 11, 20, 21, 22, 30],     "#593f5f"),
    ("Two-pass sampling",    [31, 32, 33, 40, 41, 42],     "#3f5f44"),
]

SPALTE_X = 420
ZEILE_Y = 300
BREITE = 380


def hole_object_info():
    try:
        with urllib.request.urlopen(SERVER + "/object_info", timeout=5) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError) as e:
        print("Kein laufendes ComfyUI (%s) - Workflow wird ungeprueft gebaut." % e)
        return None


def signaturen(oi):
    """Type -> (inputs {name: type}, outputs [(name, type)])."""
    raus = {}
    for typ, d in oi.items():
        ein = {}
        for bereich in ("required", "optional"):
            for name, spec in (d["input"].get(bereich) or {}).items():
                t = spec[0]
                ein[name] = "COMBO" if isinstance(t, list) else t
        namen = d.get("output_name") or d.get("output") or []
        aus = list(zip(namen, d.get("output") or []))
        raus[typ] = (ein, aus)
    return raus


def baue(sig, oi_roh=None, anker=False):
    knoten, nach_id = [], {}
    nodes = list(NODES) + ([ANKER_LORA] if anker else [])
    # Both samplers read the model through the loader instead of straight from
    # the UNETLoader.
    verbindungen = LINKS if not anker else (
        [(1, "MODEL", ANKER_LORA[0], "model")]
        + [(ANKER_LORA[0], "MODEL", nach, ein) if (von, aus) == (1, "MODEL")
           else (von, aus, nach, ein) for von, aus, nach, ein in LINKS])
    for nid, typ, spalte, zeile, widgets, titel in nodes:
        if sig and typ not in sig:
            raise SystemExit("Node-Typ nicht vorhanden: %s" % typ)
        n = {
            "id": nid,
            "type": typ,
            "pos": [spalte * SPALTE_X, zeile * ZEILE_Y],
            "size": [BREITE, 100],
            "flags": {},
            "order": 0,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {"Node name for S&R": typ},
        }
        if titel:
            n["title"] = titel
        if anker and nid == ANKER_LORA[0]:
            n["mode"] = BYPASS
        if widgets is not None:
            n["widgets_values"] = list(widgets)
        if typ == "Krea2PersonBuilder":
            n["properties"]["personState"] = json.dumps(PERSON_STATE, ensure_ascii=False)
        if anker and typ == "Krea2Photoshooting":
            # Same mechanism as the Person Builder: the panel reads its state
            # from node.properties, not from a widget.
            n["properties"]["shootingState"] = json.dumps(ANKER_STATE, ensure_ascii=False)
        if anker and typ == "SaveImage":
            n["widgets_values"] = ["krea2/anchor"]
        knoten.append(n)
        nach_id[nid] = n

    # Create the outputs - all of them, not only the wired ones, or the slots
    # shift in the front end.
    for n in knoten:
        if sig:
            for name, typ in sig[n["type"]][1]:
                n["outputs"].append({"name": name, "type": typ, "links": [], "slot_index": len(n["outputs"])})

    links, link_id = [], 0
    for von, aus_name, nach, ein_name in verbindungen:
        quelle, ziel = nach_id[von], nach_id[nach]
        if sig:
            aus = sig[quelle["type"]][1]
            treffer = [i for i, (nm, _) in enumerate(aus) if nm == aus_name]
            if not treffer:
                raise SystemExit("%s hat keinen Ausgang %r" % (quelle["type"], aus_name))
            slot = treffer[0]
            typ = aus[slot][1]
            ein = sig[ziel["type"]][0]
            if ein_name not in ein:
                raise SystemExit("%s hat keinen Eingang %r" % (ziel["type"], ein_name))
            if ein[ein_name] not in (typ, "COMBO", "*"):
                raise SystemExit("Typ passt nicht: %s.%s (%s) -> %s.%s (%s)"
                                 % (quelle["type"], aus_name, typ,
                                    ziel["type"], ein_name, ein[ein_name]))
        else:
            slot, typ = 0, "*"

        link_id += 1
        quelle["outputs"][slot]["links"].append(link_id)

        eingang = {"name": ein_name, "type": typ, "link": link_id}
        # Inputs that are a widget on the node (seed, width, text ...) have to
        # declare themselves as a widget input - otherwise the front end does
        # not draw them in the right place.
        if ein_name in WIDGET_EINGAENGE.get(ziel["type"], ()):
            eingang["widget"] = {"name": ein_name}
        ziel["inputs"].append(eingang)
        links.append([link_id, von, slot, nach, len(ziel["inputs"]) - 1, typ])

    # Every required input has to be filled - by a link or by a widget. Without
    # this check a forgotten wire only comes to light when ComfyUI rejects the
    # graph; that is exactly how KSampler 2 slipped through here without
    # positive.
    if oi_roh:
        for n in knoten:
            verlinkt = {e["name"] for e in n["inputs"]}
            pflicht = (oi_roh[n["type"]]["input"].get("required") or {})
            for name, spec in pflicht.items():
                if name in verlinkt:
                    continue
                opts = spec[1] if len(spec) > 1 else {}
                istWidget = isinstance(spec[0], list) or spec[0] in (
                    "INT", "FLOAT", "STRING", "BOOLEAN")
                if isinstance(opts, dict) and opts.get("forceInput"):
                    istWidget = False
                if not istWidget:
                    raise SystemExit(
                        "%s (id %d): Pflichteingang %r ist nicht verdrahtet"
                        % (n["type"], n["id"], name))

    for n in knoten:
        n["size"] = [BREITE, max(120, 40 + 26 * (len(n["inputs"]) + len(n.get("widgets_values") or [])))]

    gruppen = []
    for titel, ids, farbe in GRUPPEN:
        kx = [nach_id[i]["pos"][0] for i in ids]
        ky = [nach_id[i]["pos"][1] for i in ids]
        kh = [nach_id[i]["pos"][1] + nach_id[i]["size"][1] for i in ids]
        gruppen.append({
            "id": len(gruppen) + 1,
            "title": titel,
            "bounding": [min(kx) - 20, min(ky) - 70,
                         max(kx) - min(kx) + BREITE + 40, max(kh) - min(ky) + 100],
            "color": farbe,
            "font_size": 24,
            "flags": {},
        })

    return {
        "id": "krea2-photoshoot-example",
        "revision": 0,
        "last_node_id": max(n["id"] for n in knoten),
        "last_link_id": link_id,
        "nodes": knoten,
        "links": links,
        "groups": gruppen,
        "config": {},
        "extra": {"ds": {"scale": 0.6, "offset": [80, 60]}},
        "version": 0.4,
    }


# Inputs that are really a widget on the node.
WIDGET_EINGAENGE = {
    "KSampler": ("seed",),
    "EmptySD3LatentImage": ("width", "height"),
    "CLIPTextEncode": ("text",),
    "Krea2Photoshooting": ("person_data",),
    "Krea2PromptJoin": ("text",),
}


# Local model names, for building a copy that runs on this machine.
#
# The shipped workflow must name what Comfy-Org publishes, or it is broken for
# everyone else. But the machine this is developed on has its own files, and
# re-picking three loaders by hand after every rebuild is tedious.
#
# So: put your names in tools/modelle.local.json and run with --lokal. Both that
# file and the workflow it writes are in .gitignore, so local names cannot reach
# a commit even by accident - the flag writes to a different path and never
# touches the file that ships.
LOKAL_MODELLE = WURZEL / "tools" / "modelle.local.json"
LOKAL_ZIEL = WURZEL / "example_workflows" / "photoshoot-series.local.json"
ANKER_LOKAL_ZIEL = WURZEL / "example_workflows" / "photoshoot-anchor-set.local.json"


def lokale_modelle():
    """{"UNET": ..., "CLIP": ..., "VAE": ...} from the local file, or None."""
    if not LOKAL_MODELLE.exists():
        return None
    try:
        return json.loads(LOKAL_MODELLE.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit("%s ist kein gueltiges JSON: %s"
                         % (LOKAL_MODELLE.relative_to(WURZEL), e))


def main():
    lokal = "--lokal" in sys.argv[1:]
    anker = "--anker" in sys.argv[1:]
    ziel = ANKER_ZIEL if anker else ZIEL

    if lokal:
        namen = lokale_modelle()
        if not namen:
            raise SystemExit(
                "No %s found. Create one, for example:\n"
                '  {"UNET": "krea2/krea2_turbo_fp8_scaled.safetensors",\n'
                '   "CLIP": "mein-encoder.safetensors",\n'
                '   "VAE":  "meine-vae.safetensors"}'
                % LOKAL_MODELLE.relative_to(WURZEL))
        ziel = ANKER_LOKAL_ZIEL if anker else LOKAL_ZIEL

    oi = hole_object_info()
    sig = signaturen(oi) if oi else None
    wf = baue(sig, oi, anker=anker)

    if lokal:
        # Substitute on the finished graph rather than through the constants:
        # NODES is built at import time and carries the names by then.
        fuer_typ = {"UNETLoader": "UNET", "CLIPLoader": "CLIP", "VAELoader": "VAE"}
        gesetzt = 0
        for n in wf["nodes"]:
            schluessel = fuer_typ.get(n["type"])
            if schluessel and namen.get(schluessel) and n.get("widgets_values"):
                n["widgets_values"][0] = namen[schluessel]
                gesetzt += 1
        if gesetzt != 3:
            raise SystemExit("only %d of 3 loaders set - has the graph changed?" % gesetzt)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("%s: %d Nodes, %d Verbindungen%s%s"
          % (ziel.relative_to(WURZEL), len(wf["nodes"]), len(wf["links"]),
             ", gegen /object_info geprueft" if sig else ", ungeprueft",
             ", local model names" if lokal else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
