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
| `photoshoot.png` | README, at the top | The Photoshoot node: six axes, start button, preview of the first runs |
| `clothing.png` | README, "Building a person" | Person Builder, Clothing tab: the counters on the tabs, paired rows, the assembled sentence |
| `face.png` | not used | The Face tab, same pattern; kept here in case a second node image is wanted. Excluded from the published package by `.comfyignore` |
| `series.jpg` | README, "What a series looks like" | Eight rendered photos of the same person, two of them in landscape |

The package badge along the bottom edge of the node is cropped out of every
image: it still carried the old name when these were taken, and it carries no
information.

When retaking them: switch the interface to English (Settings → Comfy →
Locale) and open the example workflow — it brings a filled-in person with it,
where an empty Person Builder shows nothing but dashes. Capture the node alone,
zoomed in far enough that the labels are legible, and keep names from the
stores out of the frame.
