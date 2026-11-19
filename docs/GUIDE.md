# How-To & Prompt Engineering Guide

A practical guide documenting empirical findings, prompt engineering best practices, and lessons learned from generating consistent, high-impact photo series with **ComfyUI-Photoshoot**.

---

## Table of Contents

1. [The Core Mechanics: Why Diffusion Models Flatten Faces](#1-the-core-mechanics-why-diffusion-models-flatten-faces)
2. [Action Units (FACS) vs. Abstract Moods](#2-action-units-facs-vs-abstract-moods)
3. [The "Pretty Face" & Studio Neutralizer Trap](#3-the-pretty-face--studio-neutralizer-trap)
4. [The "Less is More" Principle: Attribute Overload & Attention Dilution](#4-the-less-is-more-principle-attribute-overload--attention-dilution)
5. [Token Ordering & Placement in `Photoshoot – Build Prompt`](#5-token-ordering--placement-in-photoshoot--build-prompt)
6. [Turbo & Distilled Models (CFG 1.0) vs. Standard Models (CFG > 3.0)](#6-turbo--distilled-models-cfg-10-vs-standard-models-cfg--30)
7. [Eliminating Spatial & Physical Contradictions](#7-eliminating-spatial--physical-contradictions)
8. [Macro Focus Isolation & Head Proportion Balance](#8-macro-focus-isolation--head-proportion-balance)
9. [Practical Workflow Cheat Sheet](#9-practical-workflow-cheat-sheet)
10. [Selfie Mode: What the Render Test Found](#10-selfie-mode-what-the-render-test-found)
11. [Scene & Lighting: Two Free-Text Pitfalls](#11-scene--lighting-two-free-text-pitfalls)
12. [Couples & Anti-Attribute Bleeding](#12-couples--anti-attribute-bleeding)
13. [Asymmetric Locations: Breaking the 1-Point Corridor Trap](#13-asymmetric-locations-breaking-the-1-point-corridor-trap)

---

## 1. The Core Mechanics: Why Diffusion Models Flatten Faces

When generating portraits, diffusion models (such as Krea2, FLUX, SDXL, and SD 1.5) exhibit a strong statistical bias toward **symmetrical, pleasant, neutral studio faces** ("Resting Model Face").

### Why this happens:
* **Dataset Bias:** Large image-text datasets (LAION, WebImageText) contain millions of stock photos where neutral/pleasant model headshots are captioned with subjective adjectives (*"confident business woman"*, *"thoughtful portrait"*, *"serious gaze"*).
* **Text Encoder Limitations:** Text encoders (CLIP, T5, Qwen-VL) correlate abstract emotion adjectives with general studio aesthetics rather than distinct geometric muscle deformation.
* **Result:** Asking for `"an imperious expression"` or `"a wistful expression"` produces almost identical resting faces.

```
┌────────────────────────────────────────────────────────┐
│ Abstract Prompt: "a wistful expression"                │
│ └── Text Encoder ──► [Studio Portrait Prior]           │
│ └── Model Output ──► Neutral / Resting Face (Ineffective)          │
├────────────────────────────────────────────────────────┤
│ Physical Prompt: "tears streaming down cheeks,         │
│                   quivering downturned mouth"          │
│ └── Text Encoder ──► [Geometric Muscle Movement]       │
│ └── Model Output ──► Distinct High-Impact Emotion (Effective)    │
└────────────────────────────────────────────────────────┘
```

---

## 2. Action Units (FACS) vs. Abstract Moods

To force diffusion models to break out of their resting-face default, **describe physical muscle actions (Facial Action Coding System / FACS)** rather than emotional states.

### Empirical Prompt Mapping

| Intended Mood | Abstract Phrasing (Fails) | Physical Action Unit Prompt (Works) |
|---|---|---|
| **Radiant Joy** | `a happy joyful smile` | `laughing out loud, wide open mouth laugh showing upper and lower teeth, big happy toothy grin, crinkled joyful eyes` |
| **Shock / Surprise** | `a surprised expression` | `gasping in shock with wide open mouth, dropped agape jaw, round wide open eyes showing white sclera` |
| **Panic / Fear** | `a terrified panic expression` | `terrified gasping in horror, hands clutching face in pure panic, wide terrified eyes showing white sclera, brows raised and drawn together in terror, gasping open mouth` |
| **Rage / Anger** | `an angry furious expression` | `angry snarling scowl, bared clenching teeth, intense scowling furrowed brow, fierce raging angry glare` |
| **Seduction** | `a seductive alluring expression` | `biting lower lip with white teeth, heavy-lidded sultry bedroom eyes, sensual parted lips` |
| **Grief / Tears** | `a sad crying expression` | `crying weeping face with real tears, glistening wet tears streaming down cheeks, furrowed brow, quivering downturned mouth, red watery eyes` |
| **Disbelief / Doubt** | `a skeptical expression` | `skeptical doubtful squint, one eye narrowed squinting, one sharply arched raised eyebrow, questioning cynical smirk` |
| **Mischief** | `a playful expression` | `winking one eye tightly closed, playful roguish wink, cheeky asymmetric grin smirk, raised eyebrow` |

---

## 3. The "Pretty Face" & Studio Neutralizer Trap

Certain common adjectives and photography terms act as **semantic dampeners**. They instruct the text encoder to prioritize symmetry and calmness, actively canceling out dynamic expressions.

### Dangerous Neutralizers:
1. **`"an elegant woman"` / `"poised"`:** Pulls the latent directly into calm composure.
2. **`"subtle natural makeup"`:** Enforces smooth skin and suppresses forehead furrows, scowls, and crying creases.
3. **`"gentle even fill lighting"`:** Softens dramatic shadow depth and relaxes facial muscle rendering.
4. **`"minimalist studio backdrop"` + `"portrait of..."`:** Triggers the commercial corporate headshot embedding cluster.

> [!TIP]
> **Best Practice:** When asking for extreme emotions (Rage, Horror, Wide Laughter, Grief), omit words like *"elegant"* and *"subtle makeup"*. Keep the subject definition crisp:  
> `solo 1woman looking at camera, copper red hair, black crewneck top`

---

## 4. The "Less is More" Principle: Attribute Overload & Attention Dilution

One of the most frequent mistakes in structured prompt building is **over-selecting attributes** across every section and field.

```
┌────────────────────────────────────────────────────────┐
│ ATTENTION DILUTION IN DIFFUSION MODELS                 │
│                                                        │
│ 5 Strong Anchors:                                      │
│ [Age] [Hair] [Eyes] [Jaw] [Outfit]                     │
│  ████   ████   ████   ████   ████  (High Attention)   │
│                                                        │
│ 35 Micro-Attributes:                                   │
│ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ ▌ (Diluted / Ignored) │
└────────────────────────────────────────────────────────┘
```

### Why over-clicking degrades image quality:

1. **Fixed Token Attention Budget:**
   Every text encoder has a limited attention budget across the token sequence. If you populate 35 fields (jawline, chin point, cheekbone height, nose bridge, nostril flare, earlobe shape, eyebrow arch, eye tilt, eyelash density, eyelid fold, lip thickness, cupid bow, neckline, sleeve seams, shoe soles...), the attention weight allocated to *each individual feature* drops drastically. The model either averages everything into a generic look or ignores half the inputs.

2. **Attribute Bleeding (Cross-Attention Leakage):**
   When too many descriptive words are packed together, tokens bleed into neighboring concepts:
   * *Color Bleed:* Specifying `"copper red hair"`, `"red lipstick"`, and `"red leather"` often bleeds red tones across the entire skin and background.
   * *Anatomical Bleed:* Selecting `"high cheekbones"` + `"angular jawline"` + `"soft round cheeks"` forces the model to merge conflicting bone structures, causing unnatural "plastic surgery" facial artifacts.

3. **Micro-Contradictions in the Expression Builder:**
   In the **Photoshoot – Expression** node, the *mood* field is pre-engineered as a complete, physically harmonious Action Unit.
   * If you pick the mood *Laughing* and *simultaneously* set mouth to *Pressed tight* and eyes to *Wide with alarm*, the model receives two opposing instructions for the same face at the same time. The result is an awkward, frozen grimace.
   * **Rule of Thumb:** Leave the other fields (*eyes*, *gaze*, *mouth*, *brows*, *head*) empty unless you specifically intend an asymmetric micro-modification (such as a wink or looking to the side).

4. **The Sweet Spot for Character Design:**
   To create a distinctive, reproducible character, choose **3 to 5 strong identity anchors**:
   * **Age & Heritage** (e.g. *Late 20s, Scandinavian*)
   * **Hair** (e.g. *Wavy copper red, shoulder-length*)
   * **Eyes & 1 Unique Trait** (e.g. *Hazel eyes, light bridge freckles*)
   * **Simple, High-Contrast Clothing** (e.g. *Clean black crewneck top*)
   
   *Leave the remaining 30 micro-fields empty.* The diffusion model will naturally interpolate harmonious proportions around your anchors.

---

## 5. Token Ordering & Placement in `Photoshoot – Build Prompt`

Text encoders read prompts from left to right. Tokens positioned in the first 20–30 slots receive significantly higher attention weights than tokens positioned after token 60.

### The Dilution Problem:
If your prompt starts with 60 tokens of identity:
```
tight close-up portrait of an elegant woman, in her late 20s, Scandinavian features, fair skin with natural texture and visible pores, almond-shaped hazel eyes, wavy copper red hair, subtle natural makeup, wearing a clean black crewneck top, screaming in terror...
```
The expression tokens arrive too late and get drowned out.

### The Recommended Prompt Order:
In the **Photoshoot – Build Prompt** node, place `{expression}` right after the style:

```text
{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}, {extra}
```

This guarantees that:
1. The look (`{style}`) is read before any colour word — a black and white style at the end of the prompt still renders in colour, at the front it takes.
2. Emotion (`{expression}`) commands the facial structure — in the tests a mood only showed when it stood early and as the subject.
3. Framing (`{camera}`) sets the shot distance, and scene and lighting come before the person, so the person block does not win the frame area in a wide shot.
4. Identity (`{person}`) fills in hair, eyes, features and the outfit.

A text without any placeholder gets the parts in this same order.

---

## 6. Turbo & Distilled Models (CFG 1.0) vs. Standard Models (CFG > 3.0)

Prompt behavior differs fundamentally depending on whether you run a **distilled turbo model** or a **standard base model**:

| Property | Distilled / Turbo (e.g. Krea2 Turbo, Flux Schnell, SDXL Turbo) | Standard Diffusion (e.g. SDXL Base, Flux Dev, Krea Base) |
|---|---|---|
| **CFG Setting** | `CFG = 1.0` (8–10 steps) | `CFG = 3.5 – 7.0` (25–35 steps) |
| **Negative Prompt** | Inactive / Zeroed out | Active (`ConditioningZeroOut` not needed) |
| **Prompt Weighting \`(word:1.3)\`** | Minimal / ineffective | Highly effective |
| **Primary Lever** | **Token positioning & physical word choice** | **Prompt weights & CFG guidance scale** |
| **Expression Adherence** | Requires exact Action Unit keywords | Can be boosted with `(screaming:1.3)` |

---

## 7. Eliminating Spatial & Physical Contradictions

Diffusion models attempt to satisfy every token in a prompt. When two tokens describe mutually exclusive spatial or anatomical conditions, the model hallucinates duplicate figures or distorted limbs.

### 1. Camera Framing vs. Room Placement:
* **The Contradiction:** `"portrait shot, head and shoulders"` + `"deep in the background"`.
* **The Result:** The model resolves the contradiction by painting the person twice — once as a close-up portrait in the foreground, and once as a tiny figure in the background.
* **The Fix:** The Photoshoot engine enforces `KAMERA_RAUM`: tight framings (Detail, Close-up, Portrait) only allow near placements (`"foreground"`, `"by the window"`).

### 2. Back Views vs. Facial Tokens:
* **The Contradiction:** `"view from behind, turned away"` + `"a warm gentle smile looking at camera"`.
* **The Result:** The model twists the spine 180 degrees or generates redundant limbs to show both the back and the face.
* **The Fix:** When `koerper == "Von hinten"`, Photoshoot automatically strips all face-specific tokens (`smile`, `teeth`, `eyes`, `gaze`, `lips`, `brow`) via `_ausdruck_fuer_koerper`.

### 3. Posture vs. Muscle Tension:
* **The Contradiction:** `"leaning against a wall"` + `"curled up in a ball"`.
* **The Fix:** Postures and tensions are constrained in `HALTUNG_SPANNUNG`.

---

## 8. Macro Focus Isolation & Head Proportion Balance

### 1. The Head-Weighting Bias:
The Person Builder contains 12 fields for the face and 8 for the body. Because diffusion models allocate frame area roughly proportional to token density, *Full body* and *Wide shot* framings risk generating disproportionately large heads.
* **Solution:** On wide framings, Photoshoot automatically shortens the person description (`detail_fuer_kamera`) and injects proportion counterweights:  
  `"realistic head-to-body proportions with a proportionally small head, ample negative space"`.

### 2. Macro Floor-Level Detail Shots:
When shooting the *Feet* or *Hands* focus in an *Extreme close-up*:
* The camera is forced to macro perspective:  
  `"extreme close-up macro shot of feet and shoes, low angle floor-level perspective, camera focused tightly on the footwear and ankles"`.
* The person description is automatically pruned to only describe footwear/hosiery (`DETAIL_FUESSE`), preventing head and torso tokens from leaking into floor-level shots.

---

## 9. Practical Workflow Cheat Sheet

### Setting Up a Consistent 20-Photo Shoot:
1. **Pick Your Workflow:** Load `photoshoot-studio.json` (open **Studio** in ComfyUI's left sidebar) or modular `photoshoot-series.json`.
2. **Define Identity Once:** In *Person*, set 3–5 core anchors (age, hair, eyes, skin — or a *LoRA trigger*).
3. **Dress Her in the Wardrobe:** Add one or more outfit tabs (`Photoshoot – Wardrobe`); multiple tabs rotate automatically across the series.
4. **Keep the Expression Clean:** Pick one mood pool or arc (*Joy*, *Dominance*, *Drama*); leave eyes/mouth overrides empty unless intentionally twisting them.
5. **Check Prompt Order (Modular):** Ensure `Photoshoot – Build Prompt` keeps `{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}`.
6. **Lock Seed & Preview Cheaply:** Turn *Noise* off if keeping one face/room seed across drafts, tick **Draft** (`~10.2 s` per pass-1 frame), press **Start shooting** in the node panel (not ComfyUI's Queue button), and promote keepers via **Finish favourites**.

---

## 10. Selfie Mode: What the Render Test Found

The selfie mode (Series axis *Perspective*, recipe *Selfie*, see
[nodes.md](nodes.md#perspective-and-selfies)) ships only wordings that were
rendered and judged. The candidates are in `tools/wortlabor/selfie.json`; the
wording lab (`tools/wortlabor.py`) rendered each one on the example workflow's
person, scene and light, three seeds (776610, 1401181143, 42), 9:16 at
992×1776, pass 1, next to the bare word as the control. The render ran on an
RTX 4090 and the user judged the sheets on **2026-09-30**.

### How the perspective reaches the prompt
The lab put the perspective into the camera slot **after the framing's own
wording** — `portrait shot, head and shoulders, high-angle selfie, …` — and the
Series does exactly that: framing, perspective, then the focus. The *Selfie*
recipe switches the focus off, so its camera text is the rendered one word for
word. Groups A and B ran without a style text, so no lens description competed
with the selfie; the smartphone look (group C) was tested against the
example's editorial style.

### Adopted
| Label | Wording | Where |
|---|---|---|
| Selfie von oben | high-angle selfie, phone held at arm's length above her head, she looks up into the lens | Series perspective |
| Selfie auf Augenhöhe | eye-level selfie at arm's length, one arm reaching toward the camera and out of the frame | Series perspective |
| Selfie im Liegen | selfie lying on her back on a bed, phone held above her face, hair spread on the pillow | Series perspective |
| Spiegel-Selfie | mirror selfie, full-body reflection in a tall mirror, holding a smartphone in front of her chest, looking at the phone screen — rendered as a full body shot, with no gaze of its own | Series perspective |
| Selfie über die Schulter | over-the-shoulder selfie, her back and one shoulder to the lens, body turned away from the camera, her face turned back over the shoulder into the phone held at arm's length | Series perspective (round 2) |
| Kusshand | blowing a kiss at the camera — rendered with the camera gaze, next to the eye-level selfie | Expression, mood family *Selfie* |
| Peace-Zeichen | making a peace sign with two fingers next to her face — rendered in the pose slot | Pose, arms |
| Smartphone / Social | smartphone front-camera photo, slight wide-angle distortion, natural skin, casual social media snapshot — as the whole style text | Style, genre |

**The caveat on *Selfie von oben*.** It did not produce a strongly top-down
view: in the renders the camera sits only slightly above eye level. The user
adopted it anyway, as a selfie from a little above; a steeper alternative
("looking straight down at her upturned face") is in round 2 against it. Do not
expect a bird's-eye shot from it.

### Not adopted
- Of the adopted items, the second wordings and the bare words were not taken:
  `selfie taken from above, …`, `front-camera selfie, phone held straight in
  front of her face`, `top-down selfie while lying down, …`, `mirror selfie in
  a full-length mirror, the phone covering part of her face`, `lips pursed
  into a kiss toward the camera`, and the phone-flash look
  (`shot on an iPhone, on-camera flash, candid, slightly overexposed`).

### What round 2 tested (`tools/wortlabor/selfie2.json`) and found (3.0.0)
Rendered on `tor` (3 seeds each, pass 1):
- **Adopted — `Selfie über die Schulter`:** Naming the body twist (`"over-the-shoulder selfie, her back and one shoulder to the lens, body turned away from the camera, her face turned back over the shoulder into the phone held at arm's length"`, `schulter2-a`) succeeded cleanly across all 3 seeds in portrait and medium-shot framings and now ships coupled to `Über die Schulter gedreht` body orientation and `In die Kamera` gaze.
- **Rejected — `Selfie von unten`:** Describing the phone below (`"held low..."`) reliably caused Krea 2 to draw a visible second smartphone in her hand rather than tilting the camera up from below.
- **Rejected — `Schmollmund`, `Zunge raus`, `Augenrollen`:** Even using concrete FACS/anatomical muscle descriptions (*duck face*, *tongue sticking out*, *eyes rolled up*), Krea 2 strongly suppresses exaggerated/unflattering facial distortions at CFG 1.0 and fell back to neutral studio faces across all 3 seeds.

### Why the couplings
A selfie is a phone at arm's length, and each coupling removes a contradiction
the prompt would otherwise carry (see [section 7](#7-eliminating-spatial--physical-contradictions)):
one hand holds the phone, so both-hands arm positions and postures that need
both hands go; the phone faces her, so no back view or profile; the wording of
*im Liegen* says "on her back", so no lying on the stomach; the mirror selfie
looks at the screen, so it gets no camera gaze and no kiss at the camera; a
phone at arm's length reaches from the close-up to the waist, so only the
mirror shows the full body. None of these was rendered separately — they keep
the prompt from asking for two things at once.

---

## 11. Scene & Lighting: Two Free-Text Pitfalls

Unlike the framing/pose/expression axes, free-text *scene* and *lighting* inputs (`Photoshoot – Build Prompt`'s `{scene}`/`{lighting}` blocks) are passed through without rewriting. Two render-tested findings from writing them:

### 1. A named window puts the key light behind her, not in front of her
* **The problem:** A scene like `"a sunlit loft with tall windows, wooden floor, plants in the corner"` reliably renders the windows as a bright backdrop directly behind the subject, silhouetting her face — no matter what the lighting field says (a separate `"frontal 45 degree angle"` lighting description does not override it).
* **The fix:** State what is directly behind her instead of leaving it to the model's default composition — e.g. `"...a plain brick wall directly behind her, wooden floor, plants in the corner"`, or move the window off to the side (`"...tall windows off to the left of frame"`). Both keep the sunlit-room look while the light comes from the front. A plain studio backdrop with the light quality described only in the `{lighting}` block works too and sidesteps the issue entirely.

### 2. Wording alone rarely makes reflective materials look reflective
* **The problem:** Describing a material as `"glossy"`, `"shiny"`, or `"wet-look"` (patent leather, glossy hosiery, vinyl, ...) reliably gets the garment itself right, but the render usually comes out as a flat, matte color — no visible highlight or sheen, regardless of how the wording is phrased.
* **Why:** A specular highlight is a lighting phenomenon, not just a material description. Two things move the needle, independently of each other:
  - **Directional light.** A soft/diffuse light source (the default in most scene text) cannot produce a highlight by definition. A harder, more directional light (a spotlight, hard sunlight, a beauty dish) does.
  - **A material-specific LoRA**, if one is available for that material. These effect LoRAs are often trained lightly and need a noticeably higher strength than the usual 0.6–1.0 range — 1.5–2.0 was what produced a clearly visible highlight line in testing, where 1.0 barely showed anything.
* **In the workflow:** both Krea example workflows ship a bypassed `LoraLoaderModelOnly` slot next to the model loaders (`tools/baue_workflow.py`) — pick a file, press Ctrl+B to switch it on, and chain more of the same node for several LoRAs at once (character, style, and/or a material LoRA together).

---

*For detailed node inputs and internal architecture, see [nodes.md](nodes.md) and [internals.md](internals.md).*

---

## 12. Couples & Anti-Attribute Bleeding

Combining two characters in one comma list causes clothing and hair colour bleeding in Krea 2 (a copper-redhead's black turtleneck overwrote the second person's ivory sweater across all 3 seeds in plain comma phrasing).

Breaking subjects into separate sentences anchored to left/right spatial slots (**`Two people <interaction>. On the left, <person_1>. On the right, <person_2>.`**) eliminated colour and fabric bleed across all tested pairs and five interactions (`Nebeneinander stehend`, `Arm in Arm gehend`, `Einander zugewandt`, `Rücken an Rücken`, `Arm um die Schulter`).

---

## 13. Asymmetric Locations: Breaking the 1-Point Corridor Trap

When `{pose}` is omitted during isolated scene testing, Krea 2 places the subject vertically centered (`x = 50%`) and symmetrically mirrors backgrounds around a 1-point vanishing center:
- **Linear triggers:** Words like `"between tall office buildings"` or uniform `"tall pine trunks"` create rigid rows of tree trunks, corridors, and centered crosswalks.
- **The fix (`tools/wortlabor/orte2.json`):** Pairing a relaxed contrapposto pose (*Weight on one leg*, *Turned slightly*) with angled and curving descriptions (*a winding forest path among gnarled old trees at uneven depths*, *a city sidewalk in front of an angled corner storefront*, *a gently curving cobblestone lane seen at an angle*, *a curving sandy coastline*, *a quiet library corner with an angled wooden bookcase*) produces organic, natural compositions across every seed.
