"""
Reference images - the second half of "the same person".

The 44 attribute fields describe a type, not an identity. They invent someone
who does not exist yet: Scandinavian, late 20s, copper red long waves, a
straight nose. Two images from that text are two sisters, because text has no
word for eye spacing, nose bridge width or jaw angle. That is not a gap in the
field list - it is a gap in the language.

A reference image closes it, and only that. The attributes stay: a face adapter
transfers the face, nothing else. Hair length, figure, the coat and the boots
still come out of the person block, and so does everything the series varies.
Casting first, anchoring second.

This module stays a pure passthrough. It emits IMAGE and a FLOAT and knows
nothing about how they are consumed - InstantID, PuLID, IP-Adapter FaceID,
InfiniteYou, Qwen-Image-Edit, Flux Kontext/Redux and ReActor all want a face
image and a weight, and all of them want it in a different node. Bundling one of
them would tie the pack to a model family and add dependencies; the pack has
none and emits text, numbers and now pixels.

  Save      ComfyUI/user/krea2_person_refs/<name>/NNN.png
  Load      all refs of one person as one batch, plus a camera-coupled strength

torch, numpy and PIL are imported inside the functions rather than at the top.
The package has to stay importable without them - the same reason folder_paths
and aiohttp are not hard requirements. Inside ComfyUI they are always there.
"""

import os
import time

import folder_paths

from .shooting import KAMERA
from .store import _safe_name

ORDNER = "krea2_person_refs"
LEER = "— nichts gespeichert —"

# More references do not keep making the face better - after a handful the
# adapter is averaging over the same face and the extra images only cost VRAM
# and time. Eight is where that stops paying.
MAX_REFS = 8

# ─────────────────────────────────────────────────────────────────────────────
# How much reference a framing can actually carry.
#
# A face adapter at full weight on a wide shot has almost no pixel area to work
# with: at "Totale" the head is forty pixels across. The adapter cannot put a
# face in there, but it still pulls - it fights the framing and drags the head
# back up in size, which is the exact failure the detail levels in
# person_builder.py were built to avoid. Turning the adapter down as the camera
# pulls back is the image-side counterpart to the person block shrinking with
# distance: on a close-up identity is the image, on a wide shot the room is.
#
# These are positions on the 0..1 axis between staerke_fern and staerke_nah, not
# weights. The shape of the curve lives here, its height belongs to the user -
# every adapter reads its weight on a different scale.
# ─────────────────────────────────────────────────────────────────────────────
KAMERA_ANTEIL = {
    "Detail":       1.0,
    "Nahaufnahme":  0.9,
    "Porträt":      0.8,
    "Halbtotale":   0.6,
    "Amerikanisch": 0.45,
    "Ganzkörper":   0.3,
    "Totale":       0.0,
}

# The table has to name exactly the framings the series knows. A label that
# drifted apart would fall through to full strength on a wide shot - silently,
# and precisely in the case the table exists for. Better the pack fails to
# import and says why.
_ABWEICHUNG = set(KAMERA_ANTEIL) ^ {lbl for lbl, _ in KAMERA}
if _ABWEICHUNG:
    raise RuntimeError(
        "identity.KAMERA_ANTEIL und shooting.KAMERA sind auseinandergelaufen: %s"
        % sorted(_ABWEICHUNG))


def _wurzel():
    pfad = os.path.join(folder_paths.get_user_directory(), ORDNER)
    os.makedirs(pfad, exist_ok=True)
    return pfad


def _ordner(name):
    """Folder of one person - the name always goes through _safe_name.

    Same reasoning as store._pfad: the name comes out of a free text field on
    the save node and out of a dropdown on the load node, and a hand-built
    workflow walks straight past the dropdown. A name that _safe_name empties
    out cannot hit a path.
    """
    sauber = _safe_name(name)
    if not sauber:
        raise ValueError("unbrauchbarer Name")
    return os.path.join(_wurzel(), sauber)


def _personen():
    try:
        namen = [d for d in os.listdir(_wurzel())
                 if os.path.isdir(os.path.join(_wurzel(), d))]
    except OSError:
        namen = []
    return sorted(namen, key=str.lower)


def _refs(name):
    """Paths of the stored references, in file name order."""
    try:
        ordner = _ordner(name)
        dateien = [f for f in os.listdir(ordner) if f.lower().endswith(".png")]
    except (OSError, ValueError):
        return []
    return [os.path.join(ordner, f) for f in sorted(dateien)]


def staerke_fuer(kamera_label, fern, nah):
    """Adapter weight for this framing, between fern and nah.

    Without a framing - nothing wired to kamera_label - the near value applies.
    Someone who does not wire the series in is working on single images, and
    those are portraits far more often than wide shots.
    """
    if not kamera_label:
        return float(nah)
    anteil = KAMERA_ANTEIL.get(kamera_label)
    if anteil is None:
        # Cannot happen while the import check above holds; it can happen with a
        # hand-edited workflow that sends some other string.
        print("[Photoshoot Identity] Unknown framing '%s' - using the near value."
              % kamera_label)
        return float(nah)
    return float(fern) + (float(nah) - float(fern)) * anteil


def _auswahl(groessen):
    """Which references can go into one batch, given their (h, w) sizes.

    Stacking into a batch needs identical height and width, and references
    collected over months are not identical - one came out of a portrait run at
    1088x1632, the next out of a square one. So: everything that matches the
    first image survives, the rest is dropped and named.

    Dropped rather than resized on purpose. Resizing changes how much of the
    frame the face occupies, and a face adapter reads exactly that; a stretched
    reference would quietly push the whole batch towards a wrong face shape. A
    skipped file is visible in the log, a distorted one is not.
    """
    if not groessen:
        return [], []
    erste = tuple(groessen[0])
    behalten = [i for i, g in enumerate(groessen) if tuple(g) == erste]
    verworfen = [i for i, g in enumerate(groessen) if tuple(g) != erste]
    return behalten, verworfen


class Krea2IdentitySave:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "name": ("STRING", {"default": "", "multiline": False,
                                "placeholder": "Name der Person"}),
            "speichern": ("BOOLEAN", {"default": False,
                                      "label_on": "speichern", "label_off": "aus"}),
            "nur_wenn_leer": ("BOOLEAN", {"default": False,
                                          "label_on": "nur wenn leer",
                                          "label_off": "immer"}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "save"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Legt Referenzbilder einer Person unter ihrem Namen ab, "
                   "hoechstens %d. 'nur wenn leer' schreibt nur, solange noch "
                   "keine Referenz da ist - damit saet der erste Lauf einer "
                   "Serie die Identitaet und alle weiteren nutzen sie. Das Bild "
                   "geht unveraendert durch." % MAX_REFS)

    # Same as in store.py: the node normally sits at the end of a dead branch
    # and would drop out of the execution plan.
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kw):
        return time.time() if kw.get("speichern") else False

    def save(self, image, name="", speichern=False, nur_wenn_leer=False):
        if not speichern:
            return (image,)

        sauber = _safe_name(name)
        if not sauber:
            print("[Photoshoot Identity] No usable name - nothing saved.")
            return (image,)

        vorhanden = _refs(sauber)
        if nur_wenn_leer and vorhanden:
            print("[Photoshoot Identity] '%s' already has %d reference(s) - "
                  "nothing saved ('nur wenn leer')." % (sauber, len(vorhanden)))
            return (image,)

        try:
            import numpy as np
            from PIL import Image
        except ImportError as e:
            print("[Photoshoot Identity] numpy/PIL missing (%s) - nothing saved." % e)
            return (image,)

        ordner = _ordner(sauber)
        os.makedirs(ordner, exist_ok=True)

        # Continue where the folder left off instead of counting the files: a
        # deleted 002.png must not make the next save overwrite 003.png.
        nummern = []
        for pfad in vorhanden:
            stamm = os.path.splitext(os.path.basename(pfad))[0]
            if stamm.isdigit():
                nummern.append(int(stamm))
        naechste = (max(nummern) + 1) if nummern else 1

        platz = MAX_REFS - len(vorhanden)
        stapel = list(image)
        if platz <= 0:
            print("[Photoshoot Identity] '%s' is full (%d references) - "
                  "nothing saved." % (sauber, MAX_REFS))
            return (image,)
        if len(stapel) > platz:
            print("[Photoshoot Identity] '%s' has room for %d more - dropping "
                  "%d of %d images from the batch."
                  % (sauber, platz, len(stapel) - platz, len(stapel)))
            stapel = stapel[:platz]

        for bild in stapel:
            roh = np.clip(bild.cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
            pfad = os.path.join(ordner, "%03d.png" % naechste)
            Image.fromarray(roh).save(pfad, compress_level=4)
            print("[Photoshoot Identity] saved: %s" % pfad)
            naechste += 1

        return (image,)


class Krea2Identity:
    @classmethod
    def INPUT_TYPES(cls):
        # Filled when ComfyUI asks for the node info - a person saved just now
        # only shows up after a refresh (R). Same as the load nodes in store.py.
        namen = _personen()
        return {
            "required": {
                "name": (namen if namen else [LEER],),
                "staerke_nah": ("FLOAT", {"default": 0.95, "min": 0.0, "max": 2.0,
                                          "step": 0.05}),
                "staerke_fern": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 2.0,
                                           "step": 0.05}),
            },
            "optional": {
                # The last output of the Photoshoot Series node. Without it the
                # strength stays at staerke_nah.
                "kamera_label": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("IMAGE", "FLOAT", "INT")
    RETURN_NAMES = ("image", "staerke", "anzahl")
    FUNCTION = "laden"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Gibt die Referenzbilder einer Person als Stapel aus, dazu "
                   "eine Staerke, die der Einstellung folgt: nah voll, weit fast "
                   "aus. In einen Face-Adapter (InstantID, PuLID, IP-Adapter "
                   "FaceID, ...) haengen - dieses Paket bringt keinen mit.")

    # Re-saving has to refresh the node; the folder mtime moves when a file is
    # added or removed.
    @classmethod
    def IS_CHANGED(cls, **kw):
        try:
            return os.path.getmtime(_ordner(kw.get("name")))
        except (OSError, TypeError, ValueError):
            return 0.0

    def laden(self, name=None, staerke_nah=0.95, staerke_fern=0.15,
              kamera_label=None):
        staerke = staerke_fuer(kamera_label, staerke_fern, staerke_nah)

        import torch

        # A missing reference must never take the graph down with it - the
        # series is supposed to run on the attributes alone, that is the whole
        # bootstrap workflow. 1x1 black plus anzahl 0 is something a downstream
        # node can be switched on and off against.
        def _leer(grund):
            print("[Photoshoot Identity] %s - no reference image." % grund)
            return (torch.zeros(1, 1, 1, 3), staerke, 0)

        if not name or name == LEER:
            return _leer("No person selected")

        pfade = _refs(name)
        if not pfade:
            return _leer("'%s' has no stored references" % name)

        try:
            import numpy as np
            from PIL import Image
        except ImportError as e:
            return _leer("numpy/PIL missing (%s)" % e)

        bilder, namen, groessen = [], [], []
        for pfad in pfade:
            try:
                with Image.open(pfad) as bild:
                    roh = np.array(bild.convert("RGB"), dtype=np.float32) / 255.0
            except (OSError, ValueError) as e:
                print("[Photoshoot Identity] '%s' could not be read: %s"
                      % (os.path.basename(pfad), e))
                continue
            bilder.append(torch.from_numpy(roh))
            namen.append(os.path.basename(pfad))
            groessen.append(roh.shape[:2])

        if not bilder:
            return _leer("'%s': no readable reference" % name)

        behalten, verworfen = _auswahl(groessen)
        if verworfen:
            h, w = groessen[behalten[0]]
            print("[Photoshoot Identity] '%s': %s skipped, not %dx%d."
                  % (name, ", ".join(namen[i] for i in verworfen), w, h))

        stapel = torch.stack([bilder[i] for i in behalten], dim=0)
        print("[Photoshoot Identity] '%s': %d reference(s), strength %.2f (%s)."
              % (name, len(behalten), staerke, kamera_label or "ohne Kamera"))
        return (stapel, staerke, len(behalten))


NODE_CLASS_MAPPINGS = {
    "Krea2IdentitySave": Krea2IdentitySave,
    "Krea2Identity": Krea2Identity,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2IdentitySave": "Photoshoot Identität speichern",
    "Krea2Identity": "Photoshoot Identität",
}
