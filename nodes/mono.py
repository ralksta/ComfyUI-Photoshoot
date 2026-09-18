"""
Monochrome - make an image truly black and white.

The prompt gets you the look: with the style in front of the prompt, "black
and white photograph, monochrome" comes out of Krea 2 as a monochrome image
with the tonality of one. But not quite grey. Lipstick keeps a hint of brown,
the channel spread is small but not zero (docs/measurements.md), and a
distilled model at CFG 1 cannot be argued out of it with words. This node sits
between VAE Decode and Save Image and removes what is left.

Torch is imported inside the function: the package has to stay importable
without ComfyUI's dependencies (tests/smoke.py), and torch is one of them.
"""

# Rec. 709 luma - what a monochrome conversion in an image editor does by
# default. Equal weights would make red lips and green plants the same grey.
_LUMA = (0.2126, 0.7152, 0.0722)

# Tints as channel factors on the grey value. Mild on purpose: a sepia that is
# obviously brown is a colour image again. The labels are combo values, and
# ComfyUI's locale files translate input names but not combo values - so they
# are words both languages read the same way.
TOENUNGEN = [
    ("Neutral", (1.0, 1.0, 1.0)),
    ("Sepia (warm)", (1.0, 0.94, 0.84)),
    ("Selenium (cool)", (0.92, 0.95, 1.0)),
]


def wandle_tensor(images, toenung="Neutral", staerke=1.0):
    """Blend the image towards its tinted luma. Kept apart from the node so
    it can be tested on a plain tensor."""
    import torch
    rgb = images[..., :3]
    gewichte = torch.tensor(_LUMA, dtype=rgb.dtype, device=rgb.device)
    grau = (rgb * gewichte).sum(-1, keepdim=True)
    faktor = dict(TOENUNGEN).get(toenung, (1.0, 1.0, 1.0))
    grau = grau * torch.tensor(faktor, dtype=rgb.dtype, device=rgb.device)
    staerke = max(0.0, min(1.0, float(staerke)))
    raus = rgb * (1.0 - staerke) + grau * staerke
    if images.shape[-1] > 3:
        raus = torch.cat([raus, images[..., 3:]], dim=-1)
    return raus.clamp(0.0, 1.0)


class Krea2Monochrome:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "toenung": ([lbl for lbl, _ in TOENUNGEN],),
                # 1.0 is what the node is for. Less than that is a colour image
                # with the saturation turned down, which is sometimes the point.
                "staerke": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "wandle"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Macht das Bild wirklich schwarzweiß. Der Prompt liefert den Look, "
                   "aber Lippenstift behält einen Rest Farbe - zwischen VAE Decode und "
                   "Bild speichern hängen, und der Rest ist weg. Wahlweise neutral, "
                   "Sepia oder kühl getönt.")

    def wandle(self, images, toenung="Neutral", staerke=1.0):
        return (wandle_tensor(images, toenung, staerke),)


NODE_CLASS_MAPPINGS = {"Krea2Monochrome": Krea2Monochrome}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2Monochrome": "Photoshoot Schwarzweiß"}
