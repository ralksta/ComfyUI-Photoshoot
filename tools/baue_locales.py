#!/usr/bin/env python3
"""
Generates locales/en/nodeDefs.json from the node definitions.

ComfyUI translates node titles and input and output names through this file
(localized_name in the workflow). The internal names stay untouched - "ausdruck"
is still called "ausdruck", only "Expression" is displayed. Existing wiring
survives unchanged.

Only the table below is maintained by hand. Everything else the script reads out
of the nodes themselves, so that the file does not drift apart when an input or
output is added.

    python3 tools/baue_locales.py

Restart ComfyUI afterwards. When an entry is missing the script reports it, and
ComfyUI simply shows the internal name.
"""

import argparse
import importlib.util
import json
import pathlib
import sys
import types

WURZEL = pathlib.Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "locales" / "en" / "nodeDefs.json"

# Node type -> English display name.
TITEL = {
    "Krea2PersonBuilder": "Photoshoot – Person",
    "Krea2ExpressionBuilder": "Photoshoot – Expression",
    "Krea2PoseBuilder": "Photoshoot – Pose",
    "Krea2LightingBuilder": "Photoshoot – Lighting",
    "Krea2StyleBuilder": "Photoshoot – Style",
    "Krea2LocationBuilder": "Photoshoot – Location",
    "Krea2Monochrome": "Photoshoot – Monochrome",
    "Krea2Photoshooting": "Photoshoot – Series",
    "Krea2PersonSave": "Photoshoot – Save Person",
    "Krea2PersonLoad": "Photoshoot – Load Person",
    "Krea2SzeneSave": "Photoshoot – Save Scene",
    "Krea2SzeneLoad": "Photoshoot – Load Scene",
    "Krea2StilSave": "Photoshoot – Save Style",
    "Krea2StilLoad": "Photoshoot – Load Style",
    "Krea2LichtSave": "Photoshoot – Save Lighting",
    "Krea2LichtLoad": "Photoshoot – Load Lighting",
    "Krea2PromptSave": "Photoshoot – Save Prompt",
    "Krea2PromptLoad": "Photoshoot – Load Prompt",
    "Krea2Bausteine": "Photoshoot – Pick Blocks",
    "Krea2PromptJoin": "Photoshoot – Build Prompt",
    "Krea2Wardrobe": "Photoshoot – Wardrobe",
    "Krea2DatasetSave": "Photoshoot – Save Dataset",
}

# Node type -> English description (the tooltip on the node).
LADEN = "Outputs the text of a saved block."
SPEICHERN = ("Stores the text under a name. Flip the switch to 'save', run once, "
             "then switch it back. New names appear in the loading node only "
             "after a refresh (R).")

BESCHREIBUNG = {
    "Krea2PersonBuilder": (
        "Builds the person as English text. 'person' is always the full "
        "description; 'person_data' is the raw values as JSON for the Photoshoot, "
        "which shortens them per camera framing. Clothes come from a Wardrobe node "
        "on 'wardrobe': the person wears its open tab."),
    "Krea2ExpressionBuilder": (
        "Composes a facial expression. Wire the output into the 'expression' "
        "input of Photoshoot Build Prompt and place it with {expression} in the "
        "text — as far forward as possible."),
    "Krea2PoseBuilder": (
        "Composes a body pose. Wire the output into the 'pose' input of "
        "Photoshoot Build Prompt and place it with {pose} in the text — as far "
        "forward as possible."),
    "Krea2LightingBuilder": (
        "Composes a photographic studio or ambient lighting setup. Wire the output "
        "into the 'lighting' input of Photoshoot Build Prompt and place it with "
        "{lighting} in the text."),
    "Krea2StyleBuilder": (
        "Composes the photographic look: colour or black and white, film stock, "
        "genre, lens, finish. Wire the output into the 'style' input of Photoshoot "
        "Build Prompt and place it with {style} in the text."),
    "Krea2Monochrome": (
        "Makes the image truly black and white. The prompt delivers the look, but "
        "lipstick keeps a trace of colour - wire this between VAE Decode and Save "
        "Image and the trace is gone. Neutral, sepia or cool tint."),
    "Krea2Photoshooting": (
        "Varies camera, pose, expression and aspect ratio across a whole series. "
        "The person is optional via 'person_data' and gets shortened per framing; "
        "with a Wardrobe on the Person node the outfit changes over the series. "
        "'person_data' and 'camera_label' are for optional extension packs. "
        "'photo' is the photo number within the series, not a source of "
        "randomness - the noise seed comes out of 'image_seed'. 'refine' goes into a "
        "refine switch (the example workflows' Render node has one; off for a "
        "draft), 'filename' into Save "
        "Image's filename_prefix. 'caption' and 'photo' at the end feed Save "
        "Dataset: the training caption (trigger and what varies, never the "
        "identity) and the photo number. 'scene' and 'lighting' at the very end: "
        "the set of this photo from a Location node on 'location_data' (shortened "
        "for the close framings) and the light of the light axis - wire them into "
        "Build Prompt's scene and lighting instead of the fixed ones. 'prompt' at "
        "the end emits the assembled prompt directly (using embedded Studio settings "
        "when no separate builder nodes are wired)."),
    "Krea2LocationBuilder": (
        "Composes the set: place, time of day, weather and season - one set or "
        "several as tabs. 'scene' is the open set: wire it into the 'scene' input "
        "of Photoshoot Build Prompt. 'location_data' goes to the Series, which "
        "changes the sets over the series like outfits and fits the light to them."),
    "Krea2Bausteine": (
        "Picks two persons, a scene and a style from the saved blocks. New "
        "entries appear only after a refresh (R)."),
    "Krea2PromptJoin": (
        "Replaces {person1} {person2} {person3} {camera} {pose} {expression} "
        "{lighting} {scene} {style} {extra}. Recommended: {style}, {expression}, {camera}, "
        "{scene}, {lighting}, {person}, {pose}, {extra}. The German spellings still "
        "work. {extra} is for extension packs. Without placeholders the parts follow "
        "in that same order."),
    "Krea2Wardrobe": (
        "The outfits of a shoot, as tabs. Wire 'wardrobe' into the Person node: the "
        "person wears the open tab, and a Series node changes through all outfits."),
    "Krea2DatasetSave": (
        "Saves each photo with its caption as a training pair for a character LoRA: "
        "output/photoshoot/dataset/<name>/NNNN.png and NNNN.txt, NNNN being the "
        "photo number. 'caption' and 'photo' come from the Series; 'trigger' goes "
        "in front of the caption unless it is already there."),
    "Krea2PersonSave": SPEICHERN, "Krea2PersonLoad": LADEN,
    "Krea2SzeneSave": SPEICHERN,  "Krea2SzeneLoad": LADEN,
    "Krea2StilSave": SPEICHERN,   "Krea2StilLoad": LADEN,
    "Krea2LichtSave": SPEICHERN,  "Krea2LichtLoad": LADEN,
    "Krea2PromptSave": SPEICHERN, "Krea2PromptLoad": LADEN,
}

# Internal input/output name -> English label. Applies to every node; the same
# name means the same thing everywhere here.
ANSCHLUESSE = {
    "person": "person", "person_1": "person_1", "person_2": "person_2",
    "person_3": "person_3", "person_data": "person_data",
    "pose": "pose", "ausdruck": "expression", "licht": "lighting",
    "lighting": "lighting", "kamera": "camera",
    "kamera_label": "camera_label", "szene": "scene", "stil": "style",
    "extra": "extra", "prompt": "prompt", "text": "text",
    "width": "width", "height": "height", "width_in": "width_in",
    "height_in": "height_in", "bildseed": "image_seed", "seed": "seed",
    "foto": "photo", "images": "images", "toenung": "tint", "staerke": "strength",
    "name": "name", "speichern": "save",
    "garderobe": "wardrobe", "outfit": "outfit",
    "refine": "refine", "dateiname": "filename",
    "caption": "caption", "trigger": "trigger",
    "ort_data": "location_data",
}


def lade_kit():
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
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pruefen", action="store_true", help="only check that nodeDefs.json is current")
    args = ap.parse_args()

    kit = lade_kit()
    raus = {}
    fehlend = set()

    for typ, cls in sorted(kit.NODE_CLASS_MAPPINGS.items()):
        eintrag = {"display_name": TITEL.get(typ, typ)}
        if typ not in TITEL:
            fehlend.add("Titel: " + typ)
        # The tooltip on the node. Without a translation the German text would
        # stand here, in the middle of an English interface.
        if typ in BESCHREIBUNG:
            eintrag["description"] = BESCHREIBUNG[typ]
        elif getattr(cls, "DESCRIPTION", None):
            fehlend.add("Beschreibung: " + typ)

        spec = cls.INPUT_TYPES()
        eingaenge = {}
        for bereich in ("required", "optional"):
            for name in (spec.get(bereich) or {}):
                if name in ANSCHLUESSE:
                    eingaenge[name] = {"name": ANSCHLUESSE[name]}
                else:
                    fehlend.add("Eingang: " + name)
        if eingaenge:
            eintrag["inputs"] = eingaenge

        # ComfyUI addresses outputs by index, not by name.
        namen = getattr(cls, "RETURN_NAMES", None) or getattr(cls, "RETURN_TYPES", ())
        ausgaenge = {}
        for i, name in enumerate(namen):
            if name in ANSCHLUESSE:
                ausgaenge[str(i)] = {"name": ANSCHLUESSE[name]}
            else:
                fehlend.add("Ausgang: " + name)
        if ausgaenge:
            eintrag["outputs"] = ausgaenge

        raus[typ] = eintrag

    if fehlend:
        print("\nOhne Uebersetzung (ComfyUI zeigt den internen Namen):")
        for f in sorted(fehlend):
            print("  " + f)
        return 1

    inhalt = json.dumps(raus, ensure_ascii=False, indent=2) + "\n"
    if args.pruefen:
        if not ZIEL.is_file() or ZIEL.read_text(encoding="utf-8") != inhalt:
            print("%s ist nicht aktuell (python3 tools/baue_locales.py ausfuehren)" % ZIEL.relative_to(WURZEL))
            return 1
        print("%s: %d Nodes, aktuell" % (ZIEL.relative_to(WURZEL), len(raus)))
        return 0

    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(inhalt, encoding="utf-8")
    print("%s: %d Nodes" % (ZIEL.relative_to(WURZEL), len(raus)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
