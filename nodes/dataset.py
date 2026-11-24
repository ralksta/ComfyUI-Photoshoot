"""
Save Dataset - the images of a series as a training set for a character LoRA.

Each photo goes to output/photoshoot/dataset/<name>/ as NNNN.png next to
NNNN.txt, the pair every LoRA trainer reads (kohya, ai-toolkit, OneTrainer).
NNNN is the photo number of the series, so a re-shoot of photo 7 replaces
0007 instead of adding an eighth-and-a-half, and the set stays in series order.

The caption comes from the Series' caption output: the trigger plus what varies
(framing, pose, expression, outfit), never the identity - see caption_fuer()
in shooting.py. Without a trigger on the person (a reference series, which
names its images instead), this node's own trigger goes in front.

torch, numpy, PIL and folder_paths are imported inside the functions: the
package has to stay importable without ComfyUI (tests/smoke.py).
"""

import os
import re

# Where the sets go, under ComfyUI's output folder.
UNTERORDNER = ("photoshoot", "dataset")


def ordnername(name):
    """A safe folder name: no path, no dots at the front, nothing a file
    system trips over. An empty name becomes "character"."""
    name = re.sub(r"[^\w\- ]+", "_", (name or "").strip(), flags=re.UNICODE).strip(" ._")
    return name[:80] or "character"


def mit_trigger(caption, trigger):
    """The caption with the trigger in front, unless it already starts with it."""
    caption = (caption or "").strip()
    trigger = (trigger or "").strip().rstrip(",;. ")
    if not trigger or caption == trigger or caption.startswith(trigger + ","):
        return caption
    return trigger + (", " + caption if caption else "")


def speichere(images, caption, foto, ordner, trigger=""):
    """Write the batch into `ordner`: NNNN.png and NNNN.txt per image. A batch
    of more than one gets NNNN_1, NNNN_2, ... Returns the file names written.
    Kept apart from the node so it can be tested on a plain tensor."""
    import numpy as np
    from PIL import Image

    os.makedirs(ordner, exist_ok=True)
    text = mit_trigger(caption, trigger)
    nummer = "%04d" % max(0, int(foto or 0))
    namen = []
    for i, bild in enumerate(images):
        stamm = nummer if len(images) == 1 else "%s_%d" % (nummer, i + 1)
        pixel = np.clip(255.0 * bild.cpu().numpy(), 0, 255).astype(np.uint8)
        Image.fromarray(pixel).save(os.path.join(ordner, stamm + ".png"), compress_level=4)
        with open(os.path.join(ordner, stamm + ".txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        namen.append(stamm + ".png")
    return namen


class Krea2DatasetSave:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "caption": ("STRING", {"forceInput": True}),
                # The photo number from the Series (its foto output); typed by
                # hand it is simply the number of the next pair.
                "foto": ("INT", {"default": 1, "min": 0, "max": 99999}),
                "name": ("STRING", {"default": "character"}),
            },
            "optional": {
                # Only used when the caption does not start with it already.
                "trigger": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ()
    OUTPUT_TOOLTIPS = ()
    SEARCH_ALIASES = ["dataset", "datensatz", "lora training", "caption", "save dataset", "training"]
    FUNCTION = "speichern"
    OUTPUT_NODE = True
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Speichert jedes Foto mit seiner Bildunterschrift als Trainingspaar "
                   "für eine Charakter-LoRA: output/photoshoot/dataset/<name>/NNNN.png "
                   "und NNNN.txt, NNNN ist die Fotonummer. caption und foto kommen "
                   "aus der Serie; trigger kommt vor die Unterschrift, wenn sie ihn "
                   "noch nicht hat.")

    def speichern(self, images, caption, foto=1, name="character", trigger=""):
        import folder_paths
        unterordner = os.path.join(*UNTERORDNER, ordnername(name))
        ordner = os.path.join(folder_paths.get_output_directory(), unterordner)
        namen = speichere(images, caption, foto, ordner, trigger)
        return {"ui": {"images": [{"filename": n, "subfolder": unterordner, "type": "output"}
                                  for n in namen]}}


NODE_CLASS_MAPPINGS = {"Krea2DatasetSave": Krea2DatasetSave}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2DatasetSave": "Photoshoot – Datensatz speichern"}
