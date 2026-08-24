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

import importlib.util
import json
import pathlib
import sys
import types

WURZEL = pathlib.Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "locales" / "en" / "nodeDefs.json"

# Node type -> English display name.
TITEL = {
    "Krea2PersonBuilder": "Photoshoot Person",
    "Krea2ExpressionBuilder": "Photoshoot Expression",
    "Krea2PoseBuilder": "Photoshoot Pose",
    "Krea2Photoshooting": "Photoshoot Series",
    "Krea2PersonSave": "Photoshoot Save Person",
    "Krea2PersonLoad": "Photoshoot Load Person",
    "Krea2SzeneSave": "Photoshoot Save Scene",
    "Krea2SzeneLoad": "Photoshoot Load Scene",
    "Krea2StilSave": "Photoshoot Save Style",
    "Krea2StilLoad": "Photoshoot Load Style",
    "Krea2PromptSave": "Photoshoot Save Prompt",
    "Krea2PromptLoad": "Photoshoot Load Prompt",
    "Krea2Bausteine": "Photoshoot Pick Blocks",
    "Krea2PromptJoin": "Photoshoot Build Prompt",
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
        "which shortens them per camera framing."),
    "Krea2ExpressionBuilder": (
        "Composes a facial expression. Wire the output into the 'expression' "
        "input of Photoshoot Build Prompt and place it with {expression} in the "
        "text — as far forward as possible."),
    "Krea2PoseBuilder": (
        "Composes a body pose. Wire the output into the 'pose' input of "
        "Photoshoot Build Prompt and place it with {pose} in the text — as far "
        "forward as possible."),
    "Krea2Photoshooting": (
        "Varies camera, pose, expression and aspect ratio across a whole series. "
        "The person is optional via 'person_data' and gets shortened per framing. "
        "'person_data' and 'camera_label' at the end are for optional extension "
        "packs. The seed is the run counter, not the source of randomness."),
    "Krea2Bausteine": (
        "Picks two persons, a scene and a style from the saved blocks. New "
        "entries appear only after a refresh (R)."),
    "Krea2PromptJoin": (
        "Replaces {person1} {person2} {person3} {camera} {pose} {expression} "
        "{scene} {style} {extra}. Recommended: {camera}, {scene}, {person}, "
        "{pose}, {extra}, {expression}, {style}. The German spellings still work. "
        "{extra} is for extension packs. Without placeholders: camera and scene "
        "before the person."),
    "Krea2PersonSave": SPEICHERN, "Krea2PersonLoad": LADEN,
    "Krea2SzeneSave": SPEICHERN,  "Krea2SzeneLoad": LADEN,
    "Krea2StilSave": SPEICHERN,   "Krea2StilLoad": LADEN,
    "Krea2PromptSave": SPEICHERN, "Krea2PromptLoad": LADEN,
}

# Internal input/output name -> English label. Applies to every node; the same
# name means the same thing everywhere here.
ANSCHLUESSE = {
    "person": "person", "person_1": "person_1", "person_2": "person_2",
    "person_3": "person_3", "person_data": "person_data",
    "pose": "pose", "ausdruck": "expression", "kamera": "camera",
    "kamera_label": "camera_label", "szene": "scene", "stil": "style",
    "extra": "extra", "prompt": "prompt", "text": "text",
    "width": "width", "height": "height", "width_in": "width_in",
    "height_in": "height_in", "bildseed": "image_seed", "seed": "seed",
    "name": "name", "speichern": "save",
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

    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(json.dumps(raus, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print("%s: %d Nodes" % (ZIEL.relative_to(WURZEL), len(raus)))

    if fehlend:
        print("\nOhne Uebersetzung (ComfyUI zeigt den internen Namen):")
        for f in sorted(fehlend):
            print("  " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
