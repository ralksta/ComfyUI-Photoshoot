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
VORLAGE = "{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}"
SZENE = "a sunlit loft with tall windows, wooden floor, plants in the corner"
# The style node's state: the same text the example carried as free text
# until 2.2.0 ("editorial photography, 85mm, ..."), now as two dropdowns with
# the look left open - pick black & white there and it is in the prompt.
STYLE_STATE = {
    "felder": {"look": "—", "genre": "Editorial", "optik": "85mm f/1.4", "finish": "—"},
    "wuerfeln": {},
    "gruppe": "alle",
    "details": "",
}

# The graph. Each entry: (id, type, (pos_x, pos_y), (size_w, size_h), widgets, title)
# Explicit pixel coordinates ensure zero overlap with custom DOM panels.
# One short note per step, at the top of its frame. English, two to four
# lines: what the step is for and the one thing people get wrong there.
DOKU = "https://github.com/ralksta/ComfyUI-Photoshoot/blob/main/docs/nodes.md"
HINWEISE = {
    90: ("**Models.** Krea 2 Turbo, its Qwen3-VL text encoder and the Qwen-Image "
         "VAE, under the Comfy-Org file names. Flux or SD 3.5 work too - pick your "
         "own files here."),
    91: ("**Who.** Build the person once and save her. Her clothes come from the "
         "**Wardrobe** on the left: outfits as tabs - she wears the open one, and "
         "the series changes through all of them."),
    92: ("**Look.** Scene, light and style stay the same for the whole series. "
         "**Black & white?** Pick it under *Look* in the style node, then switch "
         "on *Monochrome* in step 6 (Ctrl+B)."),
    93: ("**The shoot.** Press **Start shooting** inside the node - not Queue. "
         "The axes vary framing, pose, expression, outfit and ratio; the contact "
         "sheet shows the photos. [All controls](%s)" % DOKU),
    94: ("**Prompt.** The template sets the order of the blocks. Keep `{style}` "
         "first: a black & white look only wins at the front."),
    95: ("**Render.** Two passes: 8 steps, then a 1.5x refine at denoise 0.44. The "
         "negative is empty on purpose (CFG 1)."),
    96: ("**Output.** *Monochrome* ships bypassed - select it and press Ctrl+B for "
         "true black & white."),
}
# The anchor set says what differs there.
ANKER_HINWEISE = {
    90: ("**Models.** Krea 2 Turbo, its text encoder and VAE. The **LoRA** below is "
         "optional: pick your character LoRA, then Ctrl+B to switch it on."),
    93: ("**The shoot.** Six reference images of one person: one seed, a fixed "
         "ratio, calm moods, so everything the text leaves open is invented once. "
         "Press **Start shooting** inside the node."),
}

# Nodes that exist only in the front end: no signature, no outputs, nothing to
# validate against /object_info.
NUR_FRONTEND = {"MarkdownNote", "Note"}

# Node colours, id -> (title bar, body). The monochrome node is the one people
# overlook, so it is the one node in the graph with a colour of its own; the
# notes are a quiet dark so they read as help, not as nodes.
FARBEN = {52: ("#5a2a15", "#8a4a25"),
          **{i: ("#2b2b2b", "#1f1f1f") for i in range(90, 97)}}

NODES = [
    # One long row, left to right in the order the data flows: models, the
    # person and her wardrobe, the look, the shoot, the prompt, rendering,
    # output. Every step is a frame with its note on top (y=60) and its nodes
    # below (from y=200); frames are 80 px apart, so the group padding (30 px
    # each side) never touches. The builder panels size themselves to their
    # content (collapsed rows), so their sizes here are the collapsed ones.

    # 0 · Models
    (90, "MarkdownNote",             (40, 60),    (340, 110), [HINWEISE[90]],               "read me"),
    (1,  "UNETLoader",               (40, 200),   (340, 100), [UNET, "default"],            "Krea 2 model"),
    (2,  "CLIPLoader",               (40, 340),   (340, 100), [CLIP, "krea2", "default"],   None),
    (3,  "VAELoader",                (40, 480),   (340, 90),  [VAE],                        None),

    # 1 · Who: the wardrobe left of the person, its wire runs straight right.
    (91, "MarkdownNote",             (460, 60),   (880, 110), [HINWEISE[91]],               "read me"),
    (13, "Krea2Wardrobe",            (460, 200),  (400, 330), None,                         None),
    (10, "Krea2PersonBuilder",       (900, 200),  (440, 430), None,                         None),

    # 2 · Look
    (92, "MarkdownNote",             (1420, 60),  (400, 110), [HINWEISE[92]],               "read me"),
    (20, "PrimitiveStringMultiline", (1420, 200), (400, 140), [SZENE],                      "scene"),
    (12, "Krea2LightingBuilder",     (1420, 380), (400, 280), [0, "fixed"],                 None),
    (21, "Krea2StyleBuilder",        (1420, 710), (400, 320), [0, "fixed"],                 None),

    # 3 · The shoot
    (93, "MarkdownNote",             (1900, 60),  (440, 110), [HINWEISE[93]],               "read me"),
    (11, "Krea2Photoshooting",       (1900, 200), (440, 960), [1, "increment"],             None),

    # 4 · Prompt
    (94, "MarkdownNote",             (2420, 60),  (420, 110), [HINWEISE[94]],               "read me"),
    (22, "PrimitiveStringMultiline", (2420, 200), (420, 140), [VORLAGE],                    "prompt template"),
    (30, "Krea2PromptJoin",          (2420, 380), (420, 300), None,                         None),

    # 5 · Render: conditioning and latent on the left, the two passes on the right.
    (95, "MarkdownNote",             (2920, 60),  (720, 110), [HINWEISE[95]],               "read me"),
    (31, "CLIPTextEncode",           (2920, 200), (340, 220), [""],                         None),
    (32, "ConditioningZeroOut",      (2920, 460), (340, 90),  None,                         "negative = empty"),
    (33, "EmptySD3LatentImage",      (2920, 590), (340, 130), [1024, 1024, 1],              None),
    (40, "KSampler",                 (3300, 200), (340, 280), [0, "fixed", 8, 1.0, "euler", "simple", 1.0],
         "pass 1 — 8 steps"),
    (41, "LatentUpscaleBy",          (3300, 520), (340, 120), ["bislerp", 1.5],             None),
    (42, "KSampler",                 (3300, 680), (340, 280), [0, "fixed", 4, 1.0, "euler_ancestral", "simple", 0.44],
         "pass 2 — refine at 0.44"),

    # 6 · Output, top to bottom. Monochrome ships bypassed, like the LoRA in
    # the anchor workflow: the prompt gets the black and white look, this node
    # removes the colour that is left (docs/measurements.md). Ctrl+B.
    (96, "MarkdownNote",             (3720, 60),  (440, 110), [HINWEISE[96]],               "read me"),
    (50, "VAEDecode",                (3720, 200), (440, 90),  None,                         None),
    (52, "Krea2Monochrome",          (3720, 330), (440, 110), ["Neutral", 1.0],             None),
    (51, "SaveImage",                (3720, 480), (440, 540), ["photoshoot/series"],        None),
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
    (13, "garderobe",   10, "garderobe"),

    (11, "person",      30, "person_1"),
    (11, "pose",        30, "pose"),
    (11, "ausdruck",    30, "ausdruck"),
    (11, "kamera",      30, "kamera"),
    (11, "width",       33, "width"),
    (11, "height",      33, "height"),
    (11, "bildseed",    40, "seed"),
    (11, "bildseed",    42, "seed"),

    (12, "licht",       30, "lighting"),

    (20, "STRING",      30, "szene"),
    (21, "stil",        30, "stil"),
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
    (50, "IMAGE",       52, "images"),
    (52, "images",      51, "images"),
]

# A filled-in example person. An empty builder shows nothing but dashes, and
# then you see neither the counters on the tabs nor the preview - precisely what
# makes this node what it is. The values are the same as in the README example.
PERSON_STATE = {
    "felder": {
        "gender": "Frau", "age": "Ende 20", "ethnicity": "Skandinavisch",
        "skinTone": "Sehr hell", "complexion": "Natürliche Poren",
        "height": "Groß", "figure": "Athletisch", "shoulders": "Sportlich",
        "hair": "Lange Wellen", "hairColor": "Rot / Kupfer",
        "eyeShape": "Mandelförmig", "eyes": "Graugrün",
        "cheekbones": "Hoch betont", "nose": "Gerade",
        "lipColor": "Altrosa", "lipFinish": "Matt",
    },
    "mehrfach": {"skinFeatures": ["Sommersprossen"]},
    "texte": {"ageExact": "", "details": ""},
    "sektion": None,
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
ANKER_LORA = (4, "LoraLoaderModelOnly", (40, 610), (340, 130),
              ["your-character-lora.safetensors", 1.0],
              "optional - pick a LoRA, then Ctrl+B")
BYPASS = 4

ANKER_STATE = {
    "anzahl": 6,
    "aktiv": {"kamera": True, "pose": True, "ausdruck": True, "format": False,
              "fokus": True, "rausch": False},
    "serienSeed": 776610,
    "festesFormat": "2:3",
}

# The example's one outfit: what the example person wore before clothing moved
# out of the Person Builder. No ready-made outfit set - the tabs are for the
# user's own outfits.
WARDROBE_STATE = {
    "outfits": [
        {"id": "mantel", "name": "Coat", "texte": {"details": "wearing a charcoal wool coat"},
         "felder": {"hosiery": "Nackte Beine", "shoes": "Combat Boots", "shoesColor": "Schwarz"}},
    ],
    "aktiv": 0,
    "sektion": None,
    "vorschauArt": "puppe",
}

LIGHTING_STATE = {
    "felder": {
        "setup": "Softbox diffuses Licht",
        "richtung": "Frontal 45°",
        "atmosphaere": "Klar & gestochen scharf",
    },
    "wuerfeln": {},
    "gruppe": "alle",
    "details": "",
}

GRUPPEN = [
    ("0 · Models",          [90, 1, 2, 3],                   "#3f5159"),
    ("1 · Who",             [91, 13, 10],                    "#593f5f"),
    ("2 · Look",            [92, 20, 12, 21],                "#5f3f4f"),
    ("3 · The shoot",       [93, 11],                        "#5f4f3f"),
    ("4 · Prompt",          [94, 22, 30],                    "#4f5f3f"),
    ("5 · Render",          [95, 31, 32, 33, 40, 41, 42],    "#3f5f44"),
    ("6 · Output",          [96, 50, 52, 51],                "#3f4f5f"),
]


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
    for nid, typ, pos, size, widgets, titel in nodes:
        if sig and typ not in sig and typ not in NUR_FRONTEND:
            raise SystemExit("Node-Typ nicht vorhanden: %s" % typ)
        n = {
            "id": nid,
            "type": typ,
            "pos": list(pos),
            "size": list(size),
            "flags": {},
            "order": 0,
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "properties": {"Node name for S&R": typ},
        }
        # The kit's own nodes carry their display name ("Photoshoot – Series"),
        # so every one of them says whose it is; a free title here hid that.
        # Titles stay only on ComfyUI's nodes, where they explain a setting.
        if titel and not typ.startswith("Krea2"):
            n["title"] = titel
        if (anker and nid == ANKER_LORA[0]) or typ == "Krea2Monochrome":
            n["mode"] = BYPASS
        if widgets is not None:
            n["widgets_values"] = list(widgets)
        if anker and nid in ANKER_HINWEISE:
            n["widgets_values"] = [ANKER_HINWEISE[nid]]
        if nid in FARBEN:
            n["color"], n["bgcolor"] = FARBEN[nid]
        if typ == "Krea2PersonBuilder":
            n["properties"]["personState"] = json.dumps(PERSON_STATE, ensure_ascii=False)
        if typ == "Krea2Wardrobe":
            n["properties"]["wardrobeState"] = json.dumps(WARDROBE_STATE, ensure_ascii=False)
        if typ == "Krea2LightingBuilder":
            n["properties"]["lightingState"] = json.dumps(LIGHTING_STATE, ensure_ascii=False)
        if typ == "Krea2StyleBuilder":
            n["properties"]["styleState"] = json.dumps(STYLE_STATE, ensure_ascii=False)
        if anker and typ == "Krea2Photoshooting":
            # Same mechanism as the Person Builder: the panel reads its state
            # from node.properties, not from a widget.
            n["properties"]["shootingState"] = json.dumps(ANKER_STATE, ensure_ascii=False)
        if anker and typ == "SaveImage":
            n["widgets_values"] = ["photoshoot/anchor"]
        knoten.append(n)
        nach_id[nid] = n

    # Create the outputs - all of them, not only the wired ones, or the slots
    # shift in the front end.
    for n in knoten:
        if sig and n["type"] not in NUR_FRONTEND:
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
            if n["type"] in NUR_FRONTEND:
                continue
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

    gruppen = []
    for titel, ids, farbe in GRUPPEN:
        actual_ids = [i for i in ids if i in nach_id]
        if anker and 1 in actual_ids and ANKER_LORA[0] in nach_id:
            actual_ids.append(ANKER_LORA[0])
        min_x = min(nach_id[i]["pos"][0] for i in actual_ids)
        min_y = min(nach_id[i]["pos"][1] for i in actual_ids)
        max_x = max(nach_id[i]["pos"][0] + nach_id[i]["size"][0] for i in actual_ids)
        max_y = max(nach_id[i]["pos"][1] + nach_id[i]["size"][1] for i in actual_ids)
        gruppen.append({
            "id": len(gruppen) + 1,
            "title": titel,
            "bounding": [min_x - 30, min_y - 70, (max_x - min_x) + 60, (max_y - min_y) + 100],
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
    "Krea2LightingBuilder": ("seed",),
    "Krea2StyleBuilder": ("seed",),
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
