#!/usr/bin/env python3
"""
Generates the example workflow example_workflows/photoshoot-series.json.

Workflows exported by hand carry along whatever state they happened to be in -
model names from one's own installation, half-unfolded panels, nodes that have
been dragged around. That is why the example workflow is built here: the wiring
stands as a list, the positions are computed, and after every change to the
nodes it can simply be regenerated.

    python3 tools/baue_workflow.py            # the series workflow
    python3 tools/baue_workflow.py --anker    # the anchor-set variant
    python3 tools/baue_workflow.py --referenz # the reference series, Qwen-Image-2.1
    python3 tools/baue_workflow.py --studio   # all-in-one Studio workflow
    python3 tools/baue_workflow.py --pruefen  # all shipped workflows checked
    python3 tools/baue_workflow.py --snapshot [--server URL]
                                              # refresh the core-node snapshot
    python3 tools/baue_workflow.py --snapshot --referenz [--server URL]
                                              # refresh the Qwen-Image-2.1 snapshot

Every node type, input name and output index is checked against the node
signatures, and no running ComfyUI is needed for that: the kit's own nodes
come from their NODE_CLASS_MAPPINGS, ComfyUI's from a snapshot of
/object_info (tools/object_info.core.json) that holds only the core nodes the
graph uses. The same code and the same snapshot give the same file, byte for
byte - tests/smoke.py holds the shipped workflows to that (--pruefen).

--snapshot rewrites that file from a running ComfyUI (default
http://127.0.0.1:8188, or --server / $PHOTOSHOOT_SERVER). Do it against the
version named under "Tested against" in docs/internals.md, then regenerate.
The reference workflow has a snapshot of its own (tools/object_info.qwen21.json,
see baue_referenz()), taken from a ComfyUI that has Qwen-Image-2.1.
"""

import importlib.util
import json
import os
import pathlib
import sys
import types
import urllib.error
import urllib.request
import uuid

WURZEL = pathlib.Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "example_workflows" / "photoshoot-series.json"
ANKER_ZIEL = WURZEL / "example_workflows" / "photoshoot-anchor-set.json"
SERVER = os.environ.get("PHOTOSHOOT_SERVER") or "http://127.0.0.1:8188"
SNAPSHOT = WURZEL / "tools" / "object_info.core.json"

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
         "own files here. **LoRA:** pick your file in the loader below, then Ctrl+B "
         "to switch it on, and put its trigger word into *LoRA trigger* (a person) "
         "or the prompt template (a style). More LoRAs: chain further loaders."),
    91: ("**Who.** Build the person once and save her. Her clothes come from the "
         "**Wardrobe** on the left: outfits as tabs - she wears the open one, and "
         "the series changes through all of them."),
    92: ("**Look.** Scene, light and style stay the same for the whole series. "
         "**Black & white?** Pick it under *Look* in the style node, then switch "
         "on *Monochrome* in step 5 (Ctrl+B)."),
    93: ("**The shoot.** Press **Start shooting** inside the node - not Queue. "
         "The axes vary framing, pose, expression, outfit and ratio; the contact "
         "sheet shows the photos. **Draft** first, then **Finish favourites**. "
         "[All controls](%s)" % DOKU),
    94: ("**Prompt.** The template sets the order of the blocks. Keep `{style}` "
         "first: a black & white look only wins at the front."),
    95: ("**Render.** One node: double-click it to see the inside. Two passes, "
         "8 steps and a 1.5x refine. **Draft** in the series switches the refine "
         "off: half the time, base resolution. *Monochrome* ships bypassed - select "
         "it and press Ctrl+B for true black & white."),
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
          **{i: ("#2b2b2b", "#1f1f1f") for i in (*range(90, 96), 99)}}

# The Photoshoot panels ship in their compact view (js/shared.mjs): the size
# here is the compact one, measured in ComfyUI (frontend 1.47.10, classic
# canvas; the node follows its content on load either way). The size in the
# node tables stays the full one: for the panels of a fixed height (Series,
# Person, Wardrobe) it goes into photoshootVollHoehe, which ⊞ restores; the
# builders size themselves to their content in both views.
KOMPAKT_HOEHE = {
    "Krea2Wardrobe": 160,
    "Krea2PersonBuilder": 180,
    "Krea2LightingBuilder": 210,
    "Krea2StyleBuilder": 190,
    "Krea2Photoshooting": 530,
}
FESTE_HOEHE = {"Krea2Wardrobe", "Krea2PersonBuilder", "Krea2Photoshooting"}

NODES = [
    # One long row, left to right in the order the data flows: models, the
    # person and her wardrobe, the look, the shoot, the prompt, rendering,
    # output. Every step is a frame with its note on top (y=60) and its nodes
    # below (from y=200); frames are 80 px apart, so the group padding (30 px
    # each side) never touches. The Photoshoot panels ship compact: their
    # sizes here are the full ones, KOMPAKT_HOEHE gives what is written.

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
    (21, "Krea2StyleBuilder",        (1420, 640), (400, 320), [0, "fixed"],                 None),

    # 3 · The shoot
    (93, "MarkdownNote",             (1900, 60),  (440, 110), [HINWEISE[93]],               "read me"),
    (11, "Krea2Photoshooting",       (1900, 200), (440, 1090), [1, "increment"],             None),

    # 4 · Prompt
    (94, "MarkdownNote",             (2420, 60),  (420, 110), [HINWEISE[94]],               "read me"),
    (22, "PrimitiveStringMultiline", (2420, 200), (420, 140), [VORLAGE],                    "prompt template"),
    (30, "Krea2PromptJoin",          (2420, 380), (420, 300), None,                         None),

    # 5 · Render: one subgraph node (RENDER below) instead of seven, then
    # the output top to bottom. Monochrome ships bypassed, like the LoRA in
    # the anchor workflow: the prompt gets the black and white look, this node
    # removes the colour that is left (docs/measurements.md). Ctrl+B.
    # The %date:...% token is ComfyUI's own SaveImage syntax, not ours: a
    # subfolder per day, so a series always keeps its own numbering even if
    # an older day's folder gets cleared out.
    (95, "MarkdownNote",             (2920, 60),  (440, 130), [HINWEISE[95]],               "read me"),
    (60, "RENDER",                   (2920, 220), (440, 300), None,                         None),
    (52, "Krea2Monochrome",          (2920, 570), (440, 110), ["Neutral", 1.0],             None),
    (51, "SaveImage",                (2920, 730), (440, 540), ["photoshoot/%date:yyyy-MM-dd%/series"], None),
]

# Links: (from_id, output name, to_id, input name)
# Outputs are addressed by name and translated into indices below - an index
# would be silently wrong as soon as an output is added.
LINKS = [

    (10, "person_data", 11, "person_data"),
    (13, "garderobe",   10, "garderobe"),

    (11, "person",      30, "person_1"),
    (11, "pose",        30, "pose"),
    (11, "ausdruck",    30, "ausdruck"),
    (11, "kamera",      30, "kamera"),
    (11, "width",       60, "width"),
    (11, "height",      60, "height"),
    (11, "bildseed",    60, "seed"),

    (12, "licht",       30, "lighting"),

    (20, "STRING",      30, "szene"),
    (21, "stil",        30, "stil"),
    (22, "STRING",      30, "text"),

    (1,  "MODEL",       60, "model"),
    (2,  "CLIP",        60, "clip"),
    (3,  "VAE",         60, "vae"),
    (30, "prompt",      60, "prompt"),
    (60, "IMAGE",       52, "images"),
    (52, "images",      51, "images"),

    # 2.7.0: draft runs switch the second pass off, and every file says which
    # photo, take and pass it is (photoshoot/s0001/07_t1_draft_00001_.png).
    (11, "refine",      60, "refine"),
    (11, "dateiname",   51, "filename_prefix"),
]

# The render subgraph. Seven ComfyUI nodes that nobody has to touch for a
# series - conditioning, latent, two sampler passes, decode - sit behind one
# node on the canvas, the way ComfyUI's own Krea 2 template does it. The node
# shows only what the series feeds it (model, prompt, size, seed, refine).
# refine off: the lazy switch takes the first pass straight to the decode and
# the upscale and second pass never run - the draft that used to be Ctrl+B on
# two nodes. Since 2.7.0 the series drives it (Draft, Finish favourites).
#
# The loaders stay outside, so picking one's own files, or putting a LoRA in
# between (anchor set), happens on the canvas and not one level down.
RENDER_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "photoshoot/render"))
RENDER_NAME = "Render (2 passes)"
# The subgraph's inputs and output, in slot order: (name, type)
RENDER_EIN = [("model", "MODEL"), ("clip", "CLIP"), ("vae", "VAE"),
              ("prompt", "STRING"), ("width", "INT"), ("height", "INT"),
              ("seed", "INT"), ("refine", "BOOLEAN")]
RENDER_AUS = [("IMAGE", "IMAGE")]
# What the node's widgets show before anything is wired, in the order of the
# widget inputs above. refine is on: the example renders at full quality.
RENDER_WIDGETS = ["", 1024, 1024, 0, True]
SUB_EIN, SUB_AUS = -10, -20  # ComfyUI's ids for a subgraph's input/output node
RENDER_HINWEIS = ("**Inside the render node.** Pass 1: 8 steps at the size the "
                  "series asks for. Pass 2: a 1.5x upscale, refined at denoise "
                  "0.44. **refine** off skips pass 2 - the series turns it off "
                  "for a draft. The negative is empty on purpose (CFG 1). Change "
                  "sampler settings here; the series only sets size, seed and refine.")
RENDER_NODES = [
    (99, "MarkdownNote",             (40, -100),   (1420, 90), [RENDER_HINWEIS],             "read me"),
    (31, "CLIPTextEncode",           (40, 160),   (340, 220), [""],                         None),
    (32, "ConditioningZeroOut",      (40, 420),   (340, 90),  None,                         "negative = empty"),
    (33, "EmptySD3LatentImage",      (40, 550),   (340, 130), [1024, 1024, 1],              None),
    (40, "KSampler",                 (420, 160),  (340, 280), [0, "fixed", 8, 1.0, "euler", "simple", 1.0],
         "pass 1 — 8 steps"),
    (41, "LatentUpscaleBy",          (420, 480),  (340, 120), ["bislerp", 1.5],             None),
    (42, "KSampler",                 (800, 160),  (340, 280), [0, "fixed", 4, 1.0, "euler_ancestral", "simple", 0.44],
         "pass 2 — refine at 0.44"),
    (43, "ComfySwitchNode",          (800, 480),  (340, 110), [True],                       "refine? (off = pass 1 only)"),
    (50, "VAEDecode",                (1180, 160), (280, 90),  None,                         None),
]
RENDER_LINKS = [
    (SUB_EIN, "model",   40, "model"),
    (SUB_EIN, "model",   42, "model"),
    (SUB_EIN, "clip",    31, "clip"),
    (SUB_EIN, "vae",     50, "vae"),
    (SUB_EIN, "prompt",  31, "text"),
    (SUB_EIN, "width",   33, "width"),
    (SUB_EIN, "height",  33, "height"),
    (SUB_EIN, "seed",    40, "seed"),
    (SUB_EIN, "seed",    42, "seed"),
    (SUB_EIN, "refine",  43, "switch"),

    (31, "CONDITIONING", 40, "positive"),
    (31, "CONDITIONING", 42, "positive"),
    (31, "CONDITIONING", 32, "conditioning"),
    (32, "CONDITIONING", 40, "negative"),
    (32, "CONDITIONING", 42, "negative"),
    (33, "LATENT",       40, "latent_image"),
    (40, "LATENT",       41, "samples"),
    (41, "LATENT",       42, "latent_image"),
    (40, "LATENT",       43, "on_false"),
    (42, "LATENT",       43, "on_true"),
    (43, "output",       50, "samples"),
    (50, "IMAGE",        SUB_AUS, "IMAGE"),
]
RENDER_GRUPPEN = [
    ("Conditioning & size", [31, 32, 33],     "#3f5f44"),
    ("Two passes",          [40, 41, 42, 43], "#3f5f44"),
    ("Decode",              [50],             "#3f4f5f"),
]

# Where the three model files come from. ComfyUI reads this from the loader's
# properties and offers the download when a file is missing - the step people
# otherwise stall on before the first image.
HF = "https://huggingface.co/Comfy-Org/Krea-2/resolve/main/"
MODELL_QUELLEN = {
    "UNETLoader": (UNET, "diffusion_models"),
    "CLIPLoader": (CLIP, "text_encoders"),
    "VAELoader":  (VAE, "vae"),
}

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
# The series workflow carries the same slot, for any LoRA: a character, a
# style, a detail LoRA. More than one is a chain of these loaders, each taking
# the MODEL of the one before. Its link is appended after LINKS, so every link
# id the series workflow shipped with stays what it was.
SERIEN_LORA = (4, "LoraLoaderModelOnly", (40, 610), (340, 130),
               ["your-lora.safetensors", 1.0],
               "optional LoRA - pick a file, then Ctrl+B")
BYPASS = 4

ANKER_STATE = {
    "anzahl": 6,
    "aktiv": {"kamera": True, "pose": True, "ausdruck": True, "format": False,
              "fokus": True, "rausch": False},
    "serienSeed": 776610,
    "festesFormat": "2:3",
    # The files keep their own folder, apart from the series.
    "ordner": "photoshoot/anchor",
}

# The example's one outfit: what the example person wore before clothing moved
# out of the Person Builder. No ready-made outfit set - the tabs are for the
# user's own outfits.
WARDROBE_STATE = {
    "outfits": [
        {"id": "mantel", "name": "Coat",
         "felder": {"top": "Ärmelloser Rollkragen", "topColor": "Schwarz",
                    "hosiery": "Nackte Beine", "shoes": "Combat Boots", "shoesColor": "Schwarz"},
         "texte": {"details": "wearing a charcoal wool coat"}},
        {"id": "cafe", "name": "Café",
         "felder": {"top": "Bardot-Top", "topColor": "Creme",
                    "bottom": "Plisseerock midi", "bottomColor": "Beige",
                    "shoes": "Blockabsatz-Pumps", "shoesColor": "Schwarz",
                    "prop": "Kaffeetasse"},
         "texte": {"details": ""}},
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
    ("5 · Render",          [95, 60, 52, 51],                "#3f5f44"),
]


def hole_json(pfad):
    try:
        with urllib.request.urlopen(SERVER + pfad, timeout=10) as r:
            return json.load(r)
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise SystemExit("Kein ComfyUI unter %s (%s)." % (SERVER, e))


def lade_kit():
    """The package, loaded without ComfyUI (the directory name has hyphens) -
    the same way tests/smoke.py and tools/baue_locales.py do it."""
    if "krea2kit" in sys.modules:
        return sys.modules["krea2kit"]
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


def _kern_typen():
    """ComfyUI's own node types in the graph: what the snapshot has to hold."""
    alle = [e[1] for e in NODES + RENDER_NODES + [ANKER_LORA]]
    return sorted({t for t in alle
                   if not t.startswith("Krea2") and t != "RENDER" and t not in NUR_FRONTEND})


def _schlank(eintrag):
    """An /object_info entry cut down to what the checks read: input names,
    their type (a combo is just "COMBO" - its options are the files on the
    machine the snapshot was taken on, which have no business in the repo)
    and forceInput; outputs with their names."""
    ein = {}
    for bereich in ("required", "optional"):
        teil = {}
        for name, spec in (eintrag["input"].get(bereich) or {}).items():
            t = spec[0]
            opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            teil[name] = ["COMBO" if isinstance(t, list) else t] + (
                [{"forceInput": True}] if opts.get("forceInput") else [])
        if teil:
            ein[bereich] = teil
    return {"input": ein, "output": list(eintrag.get("output") or []),
            "output_name": list(eintrag.get("output_name") or eintrag.get("output") or [])}


def kit_object_info():
    """The kit's nodes in the shape of /object_info, straight from the classes."""
    raus = {}
    for typ, cls in lade_kit().NODE_CLASS_MAPPINGS.items():
        spec = cls.INPUT_TYPES()
        typen = list(cls.RETURN_TYPES)
        raus[typ] = _schlank({
            "input": {b: {n: list(v) for n, v in (spec.get(b) or {}).items()}
                      for b in ("required", "optional")},
            "output": typen,
            "output_name": list(getattr(cls, "RETURN_NAMES", None) or typen),
        })
    return raus


def lade_object_info():
    """Signatures for every node in the graph, offline: the snapshot for
    ComfyUI's nodes, the classes for the kit's."""
    if not SNAPSHOT.exists():
        raise SystemExit("%s fehlt - mit --snapshot gegen ein laufendes ComfyUI erzeugen."
                         % SNAPSHOT.relative_to(WURZEL))
    kern = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["nodes"]
    fehlt = [t for t in _kern_typen() if t not in kern]
    if fehlt:
        raise SystemExit("Nicht im Snapshot: %s - --snapshot neu erzeugen." % ", ".join(fehlt))
    return {**kern, **kit_object_info()}


def schreibe_snapshot():
    """Refresh tools/object_info.core.json from a running ComfyUI, and check
    on the way that the server runs the same kit as this checkout."""
    oi = hole_json("/object_info")
    fehlt = [t for t in _kern_typen() if t not in oi]
    if fehlt:
        raise SystemExit("Der Server kennt nicht: %s" % ", ".join(fehlt))
    version = (hole_json("/system_stats").get("system") or {}).get("comfyui_version", "?")
    daten = {
        "_": ("Core-node signatures for tools/baue_workflow.py, cut from /object_info. "
              "Regenerate with: python3 tools/baue_workflow.py --snapshot"),
        "comfyui_version": version,
        "nodes": {t: _schlank(oi[t]) for t in _kern_typen()},
    }
    SNAPSHOT.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("%s: %d Core-Nodes, ComfyUI %s"
          % (SNAPSHOT.relative_to(WURZEL), len(daten["nodes"]), version))
    # A server with another checkout of the kit (or an old one, not restarted)
    # would have validated against something else than what is built here.
    abweichend = [t for t, e in kit_object_info().items()
                  if t in oi and _schlank(oi[t]) != e]
    if abweichend:
        print("Achtung: der Server hat andere Signaturen fuer %s - Neustart vergessen?"
              % ", ".join(sorted(abweichend)))


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


# Types that take whatever type is wired to them (ComfySwitchNode's "*").
PASST_SICH_AN = {"COMFY_MATCHTYPE_V3", "*"}
# Inputs a node gets in this order whether wired or not: slot indices follow
# the list, and for the switch the front end expects its own order.
EINGANGS_REIHE = {"ComfySwitchNode": [("on_false", "*"), ("on_true", "*"), ("switch", "BOOLEAN")]}


def _knoten(nid, typ, pos, size, widgets, titel):
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
    if widgets is not None:
        n["widgets_values"] = list(widgets)
    if nid in FARBEN:
        n["color"], n["bgcolor"] = FARBEN[nid]
    if typ in MODELL_QUELLEN:
        datei, ordner = MODELL_QUELLEN[typ]
        n["properties"]["models"] = [{"name": datei, "url": HF + ordner + "/" + datei,
                                      "directory": ordner}]
    for name, t in EINGANGS_REIHE.get(typ, ()):
        n["inputs"].append({"name": name, "type": t, "link": None})
    if typ in KOMPAKT_HOEHE:
        n["properties"]["photoshootAnsicht"] = "kompakt"
        if typ in FESTE_HOEHE:
            n["properties"]["photoshootVollHoehe"] = size[1]
        n["size"][1] = KOMPAKT_HOEHE[typ]
    return n


def _render_instanz(nid, pos, size):
    """The subgraph node on the canvas: every input, wired or not, in slot order."""
    n = _knoten(nid, RENDER_ID, pos, size, RENDER_WIDGETS, None)
    del n["properties"]["Node name for S&R"]
    for name, typ in RENDER_EIN:
        e = {"name": name, "type": typ, "link": None}
        if typ in ("STRING", "INT", "BOOLEAN"):
            e["widget"] = {"name": name}
        n["inputs"].append(e)
    return n


def _ausgaenge(knoten, sig):
    # Create the outputs - all of them, not only the wired ones, or the slots
    # shift in the front end.
    for n in knoten:
        if n["type"] == RENDER_ID:
            aus = RENDER_AUS
        elif sig and n["type"] not in NUR_FRONTEND:
            aus = sig[n["type"]][1]
        else:
            continue
        for name, typ in aus:
            n["outputs"].append({"name": name, "type": typ, "links": [], "slot_index": len(n["outputs"])})


def _verdrahte(verbindungen, nach_id, sig, sub=None):
    """Links for one graph level. sub = the subgraph's {"inputs", "outputs"}
    entries, whose ids -10/-20 stand for its input and output node."""
    links = []
    for von, aus_name, nach, ein_name in verbindungen:
        if von == SUB_EIN:
            slot = [nm for nm, _ in RENDER_EIN].index(aus_name)
            typ = RENDER_EIN[slot][1]
        else:
            quelle = nach_id[von]
            aus = RENDER_AUS if quelle["type"] == RENDER_ID else (sig[quelle["type"]][1] if sig else None)
            if aus is None:
                slot, typ = 0, "*"
            else:
                treffer = [i for i, (nm, _) in enumerate(aus) if nm == aus_name]
                if not treffer:
                    raise SystemExit("%s hat keinen Ausgang %r" % (quelle["type"], aus_name))
                slot = treffer[0]
                typ = aus[slot][1]

        if nach == SUB_AUS:
            ziel = None
            ziel_slot = [nm for nm, _ in RENDER_AUS].index(ein_name)
        else:
            ziel = nach_id[nach]
            if ziel["type"] == RENDER_ID:
                ein = dict(RENDER_EIN)
            else:
                ein = sig[ziel["type"]][0] if sig else None
            if ein is not None:
                if ein_name not in ein:
                    raise SystemExit("%s hat keinen Eingang %r" % (ziel["type"], ein_name))
                soll = ein[ein_name]
                if typ in PASST_SICH_AN:
                    typ = soll
                if soll not in (typ, "COMBO", "*") and soll not in PASST_SICH_AN:
                    raise SystemExit("Typ passt nicht: %s.%s (%s) -> %s.%s (%s)"
                                     % (nach_id.get(von, {}).get("type", "subgraph"), aus_name, typ,
                                        ziel["type"], ein_name, soll))

        link_id = len(links) + 1
        if von == SUB_EIN:
            sub["inputs"][slot]["linkIds"].append(link_id)
        else:
            quelle["outputs"][slot]["links"].append(link_id)

        if ziel is None:
            sub["outputs"][ziel_slot]["linkIds"].append(link_id)
        else:
            vorhanden = [i for i, e in enumerate(ziel["inputs"]) if e["name"] == ein_name]
            if vorhanden:
                ziel_slot = vorhanden[0]
                ziel["inputs"][ziel_slot]["link"] = link_id
                ziel["inputs"][ziel_slot]["type"] = typ
            else:
                eingang = {"name": ein_name, "type": typ, "link": link_id}
                # Inputs that are a widget on the node (seed, width, text ...)
                # have to declare themselves as a widget input - otherwise the
                # front end does not draw them in the right place.
                if ein_name in WIDGET_EINGAENGE.get(ziel["type"], ()):
                    eingang["widget"] = {"name": ein_name}
                ziel["inputs"].append(eingang)
                ziel_slot = len(ziel["inputs"]) - 1
        links.append((link_id, von, slot, nach, ziel_slot, typ))
    return links


def _pruefe_pflicht(knoten, oi_roh):
    # Every required input has to be filled - by a link or by a widget. Without
    # this check a forgotten wire only comes to light when ComfyUI rejects the
    # graph; that is exactly how KSampler 2 slipped through here without
    # positive.
    for n in knoten:
        if n["type"] in NUR_FRONTEND or n["type"] == RENDER_ID:
            continue
        verlinkt = {e["name"] for e in n["inputs"] if e["link"] is not None}
        pflicht = (oi_roh[n["type"]]["input"].get("required") or {})
        for name, spec in pflicht.items():
            if name in verlinkt:
                continue
            opts = spec[1] if len(spec) > 1 else {}
            istWidget = isinstance(spec[0], list) or spec[0] in (
                "INT", "FLOAT", "STRING", "BOOLEAN", "COMBO")
            if isinstance(opts, dict) and opts.get("forceInput"):
                istWidget = False
            if not istWidget:
                raise SystemExit(
                    "%s (id %d): Pflichteingang %r ist nicht verdrahtet"
                    % (n["type"], n["id"], name))


def _gruppen(gruppen_def, nach_id, extra=None):
    gruppen = []
    for titel, ids, farbe in gruppen_def:
        actual_ids = [i for i in ids if i in nach_id] + list((extra or {}).get(titel, ()))
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
    return gruppen


def _render_subgraph(sig, oi_roh):
    knoten = [_knoten(*e) for e in RENDER_NODES]
    for n in knoten:
        if sig and n["type"] not in sig and n["type"] not in NUR_FRONTEND:
            raise SystemExit("Node-Typ nicht vorhanden: %s" % n["type"])
    nach_id = {n["id"]: n for n in knoten}
    _ausgaenge(knoten, sig)
    # Pins down the left and right edge; ComfyUI lays the slots out itself.
    x0 = min(n["pos"][0] for n in knoten) - 260
    x1 = max(n["pos"][0] + n["size"][0] for n in knoten) + 100
    sub = {
        "inputs": [{"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "photoshoot/render/in/" + name)),
                    "name": name, "type": typ, "linkIds": [],
                    "pos": [x0 + 130, 190 + 20 * i]}
                   for i, (name, typ) in enumerate(RENDER_EIN)],
        "outputs": [{"id": str(uuid.uuid5(uuid.NAMESPACE_URL, "photoshoot/render/out/" + name)),
                     "name": name, "type": typ, "linkIds": [], "pos": [x1 + 20, 190]}
                    for name, typ in RENDER_AUS],
    }
    links = _verdrahte(RENDER_LINKS, nach_id, sig, sub)
    if oi_roh:
        _pruefe_pflicht(knoten, oi_roh)
    return {
        "id": RENDER_ID,
        "version": 1,
        "state": {"lastGroupId": len(RENDER_GRUPPEN), "lastNodeId": max(nach_id),
                  "lastLinkId": len(links), "lastRerouteId": 0},
        "revision": 0,
        "config": {},
        "name": RENDER_NAME,
        "inputNode": {"id": SUB_EIN, "bounding": [x0, 160, 150, 40 + 20 * len(RENDER_EIN)]},
        "outputNode": {"id": SUB_AUS, "bounding": [x1, 160, 130, 60]},
        "inputs": sub["inputs"],
        "outputs": sub["outputs"],
        "widgets": [],
        "nodes": knoten,
        "groups": _gruppen(RENDER_GRUPPEN, nach_id),
        "links": [{"id": i, "origin_id": v, "origin_slot": vs, "target_id": z,
                   "target_slot": zs, "type": t} for i, v, vs, z, zs, t in links],
        "extra": {},
    }


def baue(sig, oi_roh=None, anker=False):
    knoten, nach_id = [], {}
    lora = ANKER_LORA if anker else SERIEN_LORA
    nodes = list(NODES) + [lora]
    # The render node reads the model through the loader instead of straight
    # from the UNETLoader.
    ueber_lora = [(lora[0], "MODEL", nach, ein) if (von, aus) == (1, "MODEL")
                  else (von, aus, nach, ein) for von, aus, nach, ein in LINKS]
    verbindungen = ([(1, "MODEL", lora[0], "model")] + ueber_lora if anker
                    else ueber_lora + [(1, "MODEL", lora[0], "model")])
    for nid, typ, pos, size, widgets, titel in nodes:
        if typ == "RENDER":
            n = _render_instanz(nid, pos, size)
            knoten.append(n)
            nach_id[nid] = n
            continue
        if sig and typ not in sig and typ not in NUR_FRONTEND:
            raise SystemExit("Node-Typ nicht vorhanden: %s" % typ)
        n = _knoten(nid, typ, pos, size, widgets, titel)
        if nid == lora[0] or typ == "Krea2Monochrome":
            n["mode"] = BYPASS
        if anker and nid in ANKER_HINWEISE:
            n["widgets_values"] = [ANKER_HINWEISE[nid]]
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
            n["widgets_values"] = ["photoshoot/%date:yyyy-MM-dd%/anchor"]
        knoten.append(n)
        nach_id[nid] = n

    _ausgaenge(knoten, sig)
    links = _verdrahte(verbindungen, nach_id, sig)
    if oi_roh:
        _pruefe_pflicht(knoten, oi_roh)
    extra = {"0 · Models": [lora[0]]}

    return {
        "id": "krea2-photoshoot-example",
        "revision": 0,
        "last_node_id": max(n["id"] for n in knoten),
        "last_link_id": len(links),
        "nodes": knoten,
        "links": [list(l) for l in links],
        "groups": _gruppen(GRUPPEN, nach_id, extra),
        "definitions": {"subgraphs": [_render_subgraph(sig, oi_roh)]},
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
    "SaveImage": ("filename_prefix",),
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
STUDIO_ZIEL = WURZEL / "example_workflows" / "photoshoot-studio.json"
STUDIO_LOKAL_ZIEL = WURZEL / "example_workflows" / "photoshoot-studio.local.json"

STUDIO_LOCATION_STATE = {
    "saetze": [
        {"id": "loft", "name": "Loft", "felder": {"ort": "Sonniges Loft"},
         "wuerfeln": {}, "gruppe": "innen", "details": ""},
    ],
    "aktiv": 0,
    "sektion": None,
}

STUDIO_HINWEISE = {
    93: ("**All-in-One Studio.** Open the **Photoshoot Studio** tab in the left "
         "sidebar (or click **edit** below) to configure **Person**, **Wardrobe**, "
         "**Look**, **Pose** and **Shoot** in one place without extra nodes on "
         "the canvas. **Black & white?** Pick a black & white *Look* under "
         "*Look → Style*, then switch on *Monochrome* on the right (Ctrl+B). "
         "Press **Start shooting** to run. [All controls](%s)" % DOKU),
}

STUDIO_NODES = [
    (90, "MarkdownNote",       (40, 60),   (340, 110), [HINWEISE[90]],        "read me"),
    (1,  "UNETLoader",         (40, 200),  (340, 100), [UNET, "default"],     "Krea 2 model"),
    (2,  "CLIPLoader",         (40, 340),  (340, 100), [CLIP, "krea2", "default"], None),
    (3,  "VAELoader",          (40, 480),  (340, 90),  [VAE],                 None),

    (93, "MarkdownNote",       (460, 60),  (440, 110), [STUDIO_HINWEISE[93]], "read me"),
    (11, "Krea2Photoshooting", (460, 200), (440, 1090), [1, "increment"],     None),

    (95, "MarkdownNote",       (980, 60),  (440, 130), [HINWEISE[95]],        "read me"),
    (60, "RENDER",             (980, 220), (440, 300), None,                  None),
    (52, "Krea2Monochrome",    (980, 570), (440, 110), ["Neutral", 1.0],      None),
    (51, "SaveImage",          (980, 730), (440, 540), ["photoshoot/%date:yyyy-MM-dd%/studio"], None),
]

STUDIO_LINKS = [
    (1,  "MODEL",     4,  "model"),
    (4,  "MODEL",     60, "model"),
    (2,  "CLIP",      60, "clip"),
    (3,  "VAE",       60, "vae"),
    (11, "prompt",    60, "prompt"),
    (11, "width",     60, "width"),
    (11, "height",    60, "height"),
    (11, "bildseed",  60, "seed"),
    (11, "refine",    60, "refine"),
    (60, "IMAGE",     52, "images"),
    (52, "images",    51, "images"),
    (11, "dateiname", 51, "filename_prefix"),
]

STUDIO_GRUPPEN = [
    ("0 · Models",    [90, 1, 2, 3],       "#3f5159"),
    ("1 · The shoot", [93, 11],            "#5f4f3f"),
    ("2 · Render",    [95, 60, 52, 51],    "#3f5f44"),
]


def baue_studio(sig, oi_roh=None):
    """Compact all-in-one workflow: only Models, Series (carrying Person/Look) and Render."""
    knoten, nach_id = [], {}
    lora = SERIEN_LORA
    for nid, typ, pos, size, widgets, titel in list(STUDIO_NODES) + [lora]:
        if typ == "RENDER":
            n = _render_instanz(nid, pos, size)
            knoten.append(n)
            nach_id[nid] = n
            continue
        if sig and typ not in sig and typ not in NUR_FRONTEND:
            raise SystemExit("Node-Typ nicht vorhanden: %s" % typ)
        n = _knoten(nid, typ, pos, size, widgets, titel)
        if nid == lora[0] or typ == "Krea2Monochrome":
            n["mode"] = BYPASS
        if typ == "Krea2Photoshooting":
            n["properties"]["studioModus"] = True
            n["properties"]["personState"] = json.dumps(PERSON_STATE, ensure_ascii=False)
            n["properties"]["wardrobeState"] = json.dumps(WARDROBE_STATE, ensure_ascii=False)
            n["properties"]["lightingState"] = json.dumps(LIGHTING_STATE, ensure_ascii=False)
            n["properties"]["styleState"] = json.dumps(STYLE_STATE, ensure_ascii=False)
            n["properties"]["locationState"] = json.dumps(STUDIO_LOCATION_STATE, ensure_ascii=False)
            n["properties"]["templateText"] = VORLAGE
        knoten.append(n)
        nach_id[nid] = n

    _ausgaenge(knoten, sig)
    links = _verdrahte(STUDIO_LINKS, nach_id, sig)
    if oi_roh:
        _pruefe_pflicht(knoten, oi_roh)
    extra = {"0 · Models": [lora[0]]}

    return {
        "id": "krea2-photoshoot-studio-example",
        "revision": 0,
        "last_node_id": max(n["id"] for n in knoten),
        "last_link_id": len(links),
        "nodes": knoten,
        "links": [list(l) for l in links],
        "groups": _gruppen(STUDIO_GRUPPEN, nach_id, extra),
        "definitions": {"subgraphs": [_render_subgraph(sig, oi_roh)]},
        "config": {},
        "extra": {"ds": {"scale": 0.65, "offset": [80, 60]}},
        "version": 0.4,
    }


def lokale_modelle():
    """{"UNET": ..., "CLIP": ..., "VAE": ...} from the local file, or None."""
    if not LOKAL_MODELLE.exists():
        return None
    try:
        return json.loads(LOKAL_MODELLE.read_text(encoding="utf-8"))
    except ValueError as e:
        raise SystemExit("%s ist kein gueltiges JSON: %s"
                         % (LOKAL_MODELLE.relative_to(WURZEL), e))


def als_text(wf):
    return json.dumps(wf, ensure_ascii=False, indent=2) + "\n"


def pruefe_ausgeliefert():
    """Rebuild all shipped workflows and compare them with the files, byte for
    byte. A difference means the nodes, the graph or the snapshot changed and
    the example was not regenerated (or was edited by hand)."""
    oi = lade_object_info()
    sig = signaturen(oi)
    abweichend = []
    if ZIEL.read_text(encoding="utf-8") != als_text(baue(sig, oi, anker=False)):
        abweichend.append(str(ZIEL.relative_to(WURZEL)))
    if not STUDIO_ZIEL.is_file() or STUDIO_ZIEL.read_text(encoding="utf-8") != als_text(baue_studio(sig, oi)):
        abweichend.append(str(STUDIO_ZIEL.relative_to(WURZEL)))
    oi = lade_object_info_referenz()
    if REFERENZ_ZIEL.read_text(encoding="utf-8") != als_text(baue_referenz(signaturen(oi), oi)):
        abweichend.append(str(REFERENZ_ZIEL.relative_to(WURZEL)))
    if abweichend:
        print("Nicht aktuell: %s - python3 tools/baue_workflow.py [--studio|--referenz] ausfuehren."
              % ", ".join(abweichend))
        return 1
    print("Beispiel-Workflows: aktuell")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# The reference variant (--referenz): example_workflows/photoshoot-reference-
# qwen21.json. Not the Krea graph with a different model but a graph of its
# own, so it is built by its own function and shares only the helpers above.
#
# Qwen-Image-2.1 generates and edits in one model and takes up to ten reference
# images through TextEncodeQwenImage21, in ComfyUI core since 2026-09 - no
# custom nodes. Two anchors of the person go in (a tight face crop as image 1,
# a full-body shot as image 2); the Person node in reference mode writes "the
# same woman as in <image1> and <image2>" instead of a face, and the series
# varies everything else. Licence: Qwen Research License, non-commercial.
#
# Loaders, file names and sampler settings follow ComfyUI's own template
# "Qwen Image 2.1: Image Edit" (comfyui-workflow-templates), sized for 24 GB:
# the bf16 diffusion model and the int8 text encoder. The template's prompt
# enhancer (a second 9B LLM) is left out - the series writes the prompt.
#
# The output size is the open question for the render test. The encoder's
# latent is sized to image 1 ("any other size shifts the edit"), so that is the
# default and the series' ratio axis is fixed; a switch hands the sampler an
# empty latent at the series' size instead, as an experiment.
#
# Checked offline like the Krea workflows, against a snapshot of its own:
# tools/object_info.qwen21.json holds the core nodes of this graph as a ComfyUI
# with Qwen-Image-2.1 reports them (TextEncodeQwenImage21 and QwenImage21Cache
# do not exist in the version the kit is tested against, so they cannot go
# into object_info.core.json). Refresh it with --snapshot --referenz against
# such a server. The encoder's growing "images" input is stored spelled out as
# its slots, images.image_1 ... - that is how a workflow wires it.
# ─────────────────────────────────────────────────────────────────────────────
REFERENZ_ZIEL = WURZEL / "example_workflows" / "photoshoot-reference-qwen21.json"
REFERENZ_SNAPSHOT = WURZEL / "tools" / "object_info.qwen21.json"
QWEN_UNET = "qwen_image_2.1_bf16.safetensors"
QWEN_CLIP = "qwen3vl_8b_int8_convrot.safetensors"
QWEN_VAE = "qwen_image_2.1_vae_bf16.safetensors"
QWEN_HF = "https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/"
QWEN_QUELLEN = {
    "UNETLoader": (QWEN_UNET, "diffusion_models"),
    "CLIPLoader": (QWEN_CLIP, "text_encoders"),
    "VAELoader":  (QWEN_VAE, "vae"),
}
QWEN_LIZENZ = "https://huggingface.co/Qwen/Qwen-Image-2.1"

REFERENZ_HINWEISE = {
    90: ("**Models.** Qwen-Image-2.1 (bf16) with its Qwen3-VL-8B encoder (int8) and "
         "VAE, Comfy-Org file names, sized for 24 GB; on 16 GB pick "
         "`qwen_image_2.1_int8_convrot`. **Non-commercial licence.** The LoRA slot "
         "is for a turbo LoRA: pick it, Ctrl+B, and lower the sampler's steps."),
    96: ("**Anchors.** Image 1: a tight head-and-shoulders crop of your person, "
         "image 2: a full-body shot - the anchor-set workflow makes both. The "
         "photo takes image 1's size and ratio, so crop it to 2:3."),
    91: ("**Who.** Reference mode: *Reference* is `1, 2`, so the person reads "
         "`the same woman as in <image1> and <image2>` and face, hair and make-up "
         "come from the pictures. Age, body and the outfits stay."),
    92: ("**Look.** Scene, light and style stay the same for the whole series - "
         "the anchors fix the person, not the room."),
    93: ("**The shoot.** Press **Start shooting** inside the node - not Queue. "
         "The ratio axis is off: the photo follows image 1, whatever the series "
         "says. [All controls](%s)" % DOKU),
    94: ("**Prompt.** The template sets the order of the blocks; the person block "
         "names the reference images."),
    95: ("**Render.** The Comfy template's settings: 25 steps, CFG 1, euler. The "
         "latent comes from the encoder, sized to image 1. *series size* on is an "
         "experiment: an empty latent at the size the series asks for."),
    97: ("**Dataset** (bypassed). Ctrl+B and every photo also lands in "
         "`output/photoshoot/dataset/<name>/` as NNNN.png + NNNN.txt: the caption is "
         "the trigger plus what varies. Put your LoRA's trigger into *trigger*."),
}

REFERENZ_NODES = [
    # 0 · Models, then the turbo LoRA slot (bypassed) and the encoder cache
    # the template puts between model and sampler.
    (90, "MarkdownNote",             (40, 60),    (340, 130), [REFERENZ_HINWEISE[90]],     "read me"),
    (1,  "UNETLoader",               (40, 230),   (340, 100), [QWEN_UNET, "default"],      "Qwen-Image-2.1 model"),
    (2,  "CLIPLoader",               (40, 370),   (340, 100), [QWEN_CLIP, "qwen_image", "default"], None),
    (3,  "VAELoader",                (40, 510),   (340, 90),  [QWEN_VAE],                  None),
    (4,  "LoraLoaderModelOnly",      (40, 640),   (340, 130), ["your-turbo-lora.safetensors", 1.0],
         "optional turbo LoRA - pick it, then Ctrl+B"),
    (5,  "QwenImage21Cache",         (40, 810),   (340, 100), ["auto", "default"],         None),

    # 1 · Anchors
    (96, "MarkdownNote",             (460, 60),   (340, 130), [REFERENZ_HINWEISE[96]],     "read me"),
    (70, "LoadImage",                (460, 230),  (340, 400), ["anchor_face.png", "image"], "image 1 - face anchor (tight crop)"),
    (71, "LoadImage",                (460, 680),  (340, 400), ["anchor_full_body.png", "image"], "image 2 - full-body anchor"),

    # 2 · Who
    (91, "MarkdownNote",             (880, 60),   (880, 130), [REFERENZ_HINWEISE[91]],     "read me"),
    (13, "Krea2Wardrobe",            (880, 230),  (400, 330), None,                        None),
    (10, "Krea2PersonBuilder",       (1320, 230), (440, 430), None,                        None),

    # 3 · Look
    (92, "MarkdownNote",             (1840, 60),  (400, 130), [REFERENZ_HINWEISE[92]],     "read me"),
    (20, "PrimitiveStringMultiline", (1840, 230), (400, 140), [SZENE],                     "scene"),
    (12, "Krea2LightingBuilder",     (1840, 410), (400, 280), [0, "fixed"],                None),
    (21, "Krea2StyleBuilder",        (1840, 670), (400, 320), [0, "fixed"],                None),

    # 4 · The shoot
    (93, "MarkdownNote",             (2320, 60),  (440, 130), [REFERENZ_HINWEISE[93]],     "read me"),
    (11, "Krea2Photoshooting",       (2320, 230), (440, 1090), [1, "increment"],            None),

    # 5 · Prompt
    (94, "MarkdownNote",             (2840, 60),  (420, 130), [REFERENZ_HINWEISE[94]],     "read me"),
    (22, "PrimitiveStringMultiline", (2840, 230), (420, 140), [VORLAGE],                   "prompt template"),
    (30, "Krea2PromptJoin",          (2840, 410), (420, 300), None,                        None),

    # 6 · Render
    (95, "MarkdownNote",             (3340, 60),  (760, 130), [REFERENZ_HINWEISE[95]],     "read me"),
    (31, "TextEncodeQwenImage21",    (3340, 230), (340, 300), ["", "", 1024],              None),
    (33, "EmptyLatentImage",         (3340, 580), (340, 130), [1024, 1024, 1],             "series size (experiment)"),
    (43, "ComfySwitchNode",          (3340, 750), (340, 110), [False],                     "series size? (off = image 1's size)"),
    (40, "KSampler",                 (3760, 230), (340, 280), [0, "fixed", 25, 1.0, "euler", "simple", 1.0],
         "25 steps, CFG 1"),
    (50, "VAEDecode",                (3760, 560), (340, 90),  None,                        None),
    (51, "SaveImage",                (3760, 700), (340, 480), ["photoshoot/reference"],    None),

    # 7 · Dataset, bypassed: the anchor/dataset path of the same series.
    (97, "MarkdownNote",             (4180, 60),  (360, 150), [REFERENZ_HINWEISE[97]],     "read me"),
    (80, "Krea2DatasetSave",         (4180, 250), (360, 420), [1, "my-character", ""],     None),
]

REFERENZ_LINKS = [
    (1,  "MODEL",        4,  "model"),
    (4,  "MODEL",        5,  "model"),
    (5,  "MODEL",        40, "model"),
    (2,  "CLIP",         31, "clip"),
    (3,  "VAE",          31, "vae"),
    (3,  "VAE",          50, "vae"),
    (70, "IMAGE",        31, "images.image_1"),
    (71, "IMAGE",        31, "images.image_2"),

    (13, "garderobe",    10, "garderobe"),
    (10, "person_data",  11, "person_data"),

    (11, "person",       30, "person_1"),
    (11, "pose",         30, "pose"),
    (11, "ausdruck",     30, "ausdruck"),
    (11, "kamera",       30, "kamera"),
    (12, "licht",        30, "lighting"),
    (20, "STRING",       30, "szene"),
    (21, "stil",         30, "stil"),
    (22, "STRING",       30, "text"),

    (30, "prompt",       31, "prompt"),
    (11, "width",        33, "width"),
    (11, "height",       33, "height"),
    (11, "bildseed",     40, "seed"),
    (31, "positive",     40, "positive"),
    (31, "negative",     40, "negative"),
    (31, "latent",       43, "on_false"),
    (33, "LATENT",       43, "on_true"),
    (43, "output",       40, "latent_image"),
    (40, "LATENT",       50, "samples"),
    (50, "IMAGE",        51, "images"),
    # The file says which photo it is, as in the Krea workflows. refine stays
    # unwired: there is no second pass to skip, so Draft is greyed out here.
    (11, "dateiname",    51, "filename_prefix"),

    (50, "IMAGE",        80, "images"),
    (11, "caption",      80, "caption"),
    (11, "foto",         80, "foto"),
]

REFERENZ_GRUPPEN = [
    ("0 · Models",          [90, 1, 2, 3, 4, 5],             "#3f5159"),
    ("1 · Anchors",         [96, 70, 71],                    "#3f5159"),
    ("2 · Who",             [91, 13, 10],                    "#593f5f"),
    ("3 · Look",            [92, 20, 12, 21],                "#5f3f4f"),
    ("4 · The shoot",       [93, 11],                        "#5f4f3f"),
    ("5 · Prompt",          [94, 22, 30],                    "#4f5f3f"),
    ("6 · Render",          [95, 31, 33, 43, 40, 50, 51],    "#3f5f44"),
    ("7 · Dataset",         [97, 80],                        "#4f4f5f"),
]

# The person in reference mode: basics and body only - face, hair and make-up
# come from the anchors, and fields that would be dropped anyway only confuse.
REFERENZ_PERSON_STATE = {
    "felder": {"gender": "Frau", "age": "Ende 20", "height": "Groß",
               "figure": "Athletisch", "shoulders": "Sportlich"},
    "mehrfach": {"skinFeatures": []},
    "texte": {"ageExact": "", "details": "", "trigger": "", "referenz": "1, 2"},
    # Basics open, so the reference field is the first thing in view.
    "sektion": "Grund",
    "gruppe": {"shoes": "alle"},
}
# Twelve photos, every framing, one fixed ratio: the picture follows image 1.
REFERENZ_STATE = {
    "anzahl": 12,
    "aktiv": {"kamera": True, "pose": True, "ausdruck": True, "format": False,
              "fokus": True, "rausch": True},
    "festesFormat": "2:3",
    "ordner": "photoshoot/reference",
}
REFERENZ_BYPASS = {4, 80}
REFERENZ_WIDGETS = {
    "TextEncodeQwenImage21": ("prompt",),
    "EmptyLatentImage": ("width", "height"),
    "Krea2DatasetSave": ("foto",),
    "SaveImage": ("filename_prefix",),
}
# The encoder's reference images are one growing input ("images", autogrow):
# the front end names its slots images.image_1, images.image_2, ... and keeps
# one empty slot after the last wired one.
REFERENZ_EINGAENGE = {
    "TextEncodeQwenImage21": [("clip", "CLIP"), ("images.image_1", "IMAGE"),
                              ("images.image_2", "IMAGE"), ("images.image_3", "IMAGE"),
                              ("vae", "VAE")],
}


def _kern_typen_referenz():
    """ComfyUI's own node types in the reference graph."""
    return sorted({e[1] for e in REFERENZ_NODES
                   if not e[1].startswith("Krea2") and e[1] not in NUR_FRONTEND})


def _autogrow_ausgeschrieben(eintrag):
    """An /object_info entry with every growing input (autogrow with named
    slots) spelled out as optional inputs of its slot type, the way a workflow
    names them: images -> images.image_1 ... images.image_16."""
    eintrag = json.loads(json.dumps(eintrag))
    for bereich in ("required", "optional"):
        teil = eintrag["input"].get(bereich) or {}
        for name, spec in list(teil.items()):
            vorlage = (spec[1].get("template") or {}) if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if spec[0] != "COMFY_AUTOGROW_V3" or "names" not in vorlage:
                continue
            (_, (slot_typ, *_)), = vorlage["input"]["required"].items()
            del teil[name]
            eintrag["input"].setdefault("optional", {}).update(
                {"%s.%s" % (name, n): [slot_typ] for n in vorlage["names"]})
    return eintrag


def lade_object_info_referenz():
    """Signatures for the reference graph, offline: its own snapshot for
    ComfyUI's nodes, the classes for the kit's."""
    if not REFERENZ_SNAPSHOT.exists():
        raise SystemExit("%s fehlt - mit --snapshot --referenz gegen ein ComfyUI mit "
                         "Qwen-Image-2.1 erzeugen." % REFERENZ_SNAPSHOT.relative_to(WURZEL))
    kern = json.loads(REFERENZ_SNAPSHOT.read_text(encoding="utf-8"))["nodes"]
    fehlt = [t for t in _kern_typen_referenz() if t not in kern]
    if fehlt:
        raise SystemExit("Nicht im Snapshot: %s - --snapshot --referenz neu erzeugen."
                         % ", ".join(fehlt))
    return {**kern, **kit_object_info()}


def schreibe_snapshot_referenz():
    """Refresh tools/object_info.qwen21.json from a running ComfyUI that has
    the Qwen-Image-2.1 nodes (master since 2026-09)."""
    oi = hole_json("/object_info")
    fehlt = [t for t in _kern_typen_referenz() if t not in oi]
    if fehlt:
        raise SystemExit("Der Server kennt nicht: %s - ComfyUI mit Qwen-Image-2.1 noetig."
                         % ", ".join(fehlt))
    version = (hole_json("/system_stats").get("system") or {}).get("comfyui_version", "?")
    daten = {
        "_": ("Core-node signatures of the reference workflow (Qwen-Image-2.1) for "
              "tools/baue_workflow.py, cut from /object_info of a ComfyUI that has "
              "those nodes. Regenerate with: python3 tools/baue_workflow.py --snapshot --referenz"),
        "comfyui_version": version,
        "nodes": {t: _schlank(_autogrow_ausgeschrieben(oi[t])) for t in _kern_typen_referenz()},
    }
    REFERENZ_SNAPSHOT.write_text(json.dumps(daten, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
    print("%s: %d Core-Nodes, ComfyUI %s"
          % (REFERENZ_SNAPSHOT.relative_to(WURZEL), len(daten["nodes"]), version))


def baue_referenz(sig, oi_roh=None):
    WIDGET_EINGAENGE.update(REFERENZ_WIDGETS)
    EINGANGS_REIHE.update(REFERENZ_EINGAENGE)
    knoten, nach_id = [], {}
    for nid, typ, pos, size, widgets, titel in REFERENZ_NODES:
        if sig and typ not in sig and typ not in NUR_FRONTEND:
            raise SystemExit("Node-Typ nicht vorhanden: %s" % typ)
        n = _knoten(nid, typ, pos, size, widgets, titel)
        if typ in QWEN_QUELLEN:
            datei, ordner = QWEN_QUELLEN[typ]
            n["properties"]["models"] = [{"name": datei, "url": QWEN_HF + ordner + "/" + datei,
                                          "directory": ordner}]
        if typ == "MarkdownNote":
            n["color"], n["bgcolor"] = FARBEN[90]
        if nid in REFERENZ_BYPASS:
            n["mode"] = BYPASS
        if typ == "Krea2PersonBuilder":
            n["properties"]["personState"] = json.dumps(REFERENZ_PERSON_STATE, ensure_ascii=False)
        if typ == "Krea2Wardrobe":
            n["properties"]["wardrobeState"] = json.dumps(WARDROBE_STATE, ensure_ascii=False)
        if typ == "Krea2LightingBuilder":
            n["properties"]["lightingState"] = json.dumps(LIGHTING_STATE, ensure_ascii=False)
        if typ == "Krea2StyleBuilder":
            n["properties"]["styleState"] = json.dumps(STYLE_STATE, ensure_ascii=False)
        if typ == "Krea2Photoshooting":
            n["properties"]["shootingState"] = json.dumps(REFERENZ_STATE, ensure_ascii=False)
        knoten.append(n)
        nach_id[nid] = n

    _ausgaenge(knoten, sig)
    links = _verdrahte(REFERENZ_LINKS, nach_id, sig)
    if oi_roh:
        _pruefe_pflicht(knoten, oi_roh)
    return {
        "id": "krea2-photoshoot-reference-qwen21",
        "revision": 0,
        "last_node_id": max(n["id"] for n in knoten),
        "last_link_id": len(links),
        "nodes": knoten,
        "links": [list(l) for l in links],
        "groups": _gruppen(REFERENZ_GRUPPEN, nach_id),
        "config": {},
        "extra": {"ds": {"scale": 0.5, "offset": [80, 60]}},
        "version": 0.4,
    }


def main_referenz():
    """--referenz: build the reference workflow, checked against its snapshot."""
    if "--lokal" in sys.argv[1:]:
        raise SystemExit("--lokal has no reference variant yet.")
    oi = lade_object_info_referenz()
    wf = baue_referenz(signaturen(oi), oi)
    REFERENZ_ZIEL.write_text(als_text(wf), encoding="utf-8")
    print("%s: %d Nodes, %d Verbindungen, geprueft"
          % (REFERENZ_ZIEL.relative_to(WURZEL), len(wf["nodes"]), len(wf["links"])))
    return 0


def main():
    global SERVER
    argv = sys.argv[1:]
    if "--server" in argv:
        SERVER = argv[argv.index("--server") + 1].rstrip("/")
    if "--snapshot" in argv:
        if "--referenz" in argv:
            schreibe_snapshot_referenz()
        else:
            schreibe_snapshot()
        return 0
    if "--pruefen" in argv:
        return pruefe_ausgeliefert()
    if "--referenz" in argv:
        return main_referenz()
    lokal = "--lokal" in argv
    anker = "--anker" in argv
    studio = "--studio" in argv
    ziel = STUDIO_ZIEL if studio else (ANKER_ZIEL if anker else ZIEL)

    if lokal:
        namen = lokale_modelle()
        if not namen:
            raise SystemExit(
                "No %s found. Create one, for example:\n"
                '  {"UNET": "krea2/krea2_turbo_fp8_scaled.safetensors",\n'
                '   "CLIP": "mein-encoder.safetensors",\n'
                '   "VAE":  "meine-vae.safetensors"}'
                % LOKAL_MODELLE.relative_to(WURZEL))
        ziel = STUDIO_LOKAL_ZIEL if studio else (ANKER_LOKAL_ZIEL if anker else LOKAL_ZIEL)

    oi = lade_object_info()
    sig = signaturen(oi)
    wf = baue_studio(sig, oi) if studio else baue(sig, oi, anker=anker)

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
    ziel.write_text(als_text(wf), encoding="utf-8")
    print("%s: %d Nodes, %d Verbindungen, geprueft%s"
          % (ziel.relative_to(WURZEL), len(wf["nodes"]), len(wf["links"]),
             ", local model names" if lokal else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
