# Documentation

| | |
|---|---|
| [GUIDE.md](GUIDE.md) | How-to & prompt engineering guide: empirical learnings, FACS Action Units, token order, avoiding neutralizers |
| [nodes.md](nodes.md) | Every node in detail, and the reasoning behind the controls that are not obvious |
| [internals.md](internals.md) | Layout, translation, tests, the ComfyUI versions this was built against |
| [measurements.md](measurements.md) | Numbers from actual runs, including one conclusion that turned out to be wrong |

The [README](../README.md) covers what the kit does and how to start; these
cover what everything means.

## Images

| File | Used in | Shows |
|---|---|---|
| `banner.png` | README, at the top | Header: a strip of photos, two node cards, the logo. Built from `logo.svg` and the images below |
| `logo.svg` | in the banner | Wordmark with a contact-sheet motif, one frame exposed. Adapts to light and dark themes |
| `workflow.jpg` | README, under the introduction | The example workflow in the new look: Person Builder, lighting and style, the Series node with the contact sheet of the Joy series in `series.jpg` |
| `photoshoot.png` | README, "The photoshoot" | The Series node: brand strip, count and start number, recipes, start button, axis switches (*wide → close*, *mood arc · Joy*), contact sheet of the Joy series with photo 8 open, its four takes side by side, marked as favourite |
| `clothing.png` | README, "Building a person" | Person Builder, Clothing section open: the brand strip, the section rows with their short forms, colour buttons, the material under the bottom, the assembled sentence |
| `face.png` | not used | Person Builder, Face section open, the other sections closed with their short forms; kept for a second node image. Excluded from the published package by `.comfyignore` |
| `series.jpg` | README, "What a series looks like" | The Joy series: eight rendered photos of the same person, wide shot to extreme close-up, relaxed to triumphant, each labelled with framing and mood |
| `posters/` | README, [POSTERS.md](POSTERS.md) | Reference sheets: 72 shoes, 12 tops, 29 bottoms, 30 lighting setups, black & white and colour looks, hairstyles, poses, expressions. Each as a full-resolution PNG and a half-size `_web.jpg` |

The node screenshots keep the package badge along the bottom edge; it reads
*Photoshoot* since the rename.

When retaking them: switch the interface to English (Settings → Comfy →
Locale) and open the example workflow — it brings a filled-in person with it,
where an empty Person Builder shows nothing but dashes. Capture the node alone,
zoomed in far enough that the labels are legible, and keep names from the
stores out of the frame.
