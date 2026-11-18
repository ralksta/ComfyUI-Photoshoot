# Documentation

| | |
|---|---|
| [quickstart.md](quickstart.md) | Six steps from the example workflow to a finished series, for a first shoot |
| [GUIDE.md](GUIDE.md) | How-to & prompt engineering guide: empirical learnings, FACS Action Units, token order, avoiding neutralizers |
| [nodes.md](nodes.md) | Every node in detail, and the reasoning behind the controls that are not obvious |
| [internals.md](internals.md) | Layout, translation, tests, the ComfyUI versions this was built against |
| [measurements.md](measurements.md) | Numbers from actual runs, including one conclusion that turned out to be wrong |

The [README](../README.md) covers what the kit does and how to start; these
cover what everything means.

## Images

| File | Used in | Shows |
|---|---|---|
| `banner.png` | README, at the top | Header: the logo and two photos on the left (kept from 2.5.0), on the right two photos of the Joy series and two node cards - the Wardrobe with its Evening mannequin and the Series node with the Outfit axis and contact sheet (`banner_26.py` in the doc workspace) |
| `logo.svg` | in the banner | Wordmark with a contact-sheet motif, one frame exposed. Adapts to light and dark themes |
| `workflow.jpg` | README, under the introduction | The example workflow's *Who*, *Look* and *The shoot* frames: a Wardrobe with three outfits (Evening open, its mannequin preview), the Person, scene, light and style, and the Series node with the contact sheet of an 8-photo Joy series in three outfits. Shot at 100 % in a large window and cropped clear of the toolbar, the queue panel and the minimap |
| `photoshoot.png` | README, "The photoshoot" | The Series node: brand strip, count and start number, recipes, start button, the seven axis switches (*wide → close*, *mood arc · Joy*, *3 outfits · in blocks*), contact sheet of the Joy series in three outfits with their colour stripes, photo 8 open with its four takes, marked as favourite |
| `wardrobe.png` | README, "Dressing her: the Wardrobe" | A Wardrobe node with three outfits (Casual, Evening, Summer; the example workflow ships one), Evening tab open: the tabs, the rendered mannequin preview, the Clothing section with colour buttons, the assembled sentence. Render the three outfit previews first (Series node, Outfit axis) |
| `search.png` | README, "Building a person" | The Wardrobe's top list open: search field, the milkmaid top under the pointer with its thumbnail and prompt, the families below |
| `face.png` | not used | Person Builder, Face section open, the other sections closed with their short forms; kept for a second node image. Excluded from the published package by `.comfyignore` |
| `series.jpg` | README, "What a series looks like" | The Joy series: eight rendered photos of the same person, wide shot to extreme close-up, relaxed to triumphant, each labelled with framing and mood |
| `posters/` | README, [POSTERS.md](POSTERS.md) | Reference sheets: 72 shoes, 27 tops, 34 bottoms, 18 bikini cuts, 29 headwear, 9 bangs, 30 lighting setups, black & white and colour looks, hairstyles, poses, expressions. Each as a full-resolution PNG and a half-size `_web.jpg`; the PNGs stay out of the registry package (`.comfyignore`), GitHub has them |

The node screenshots keep the package badge along the bottom edge; it reads
*Photoshoot* since the rename.

When retaking them: switch the interface to English (Settings → Comfy →
Locale) and open the example workflow — it brings a filled-in person with it,
where an empty Person Builder shows nothing but dashes. Capture the node alone,
zoomed in far enough that the labels are legible, and keep names from the
stores out of the frame.
