# How-To & Prompt Engineering Guide

A practical guide documenting empirical findings, prompt engineering best practices, and lessons learned from generating consistent, high-impact photo series with **ComfyUI-Photoshoot**.

---

## Table of Contents

1. [The Core Mechanics: Why Diffusion Models Flatten Faces](#1-the-core-mechanics-why-diffusion-models-flatten-faces)
2. [Action Units (FACS) vs. Abstract Moods](#2-action-units-facs-vs-abstract-moods)
3. [The "Pretty Face" & Studio Neutralizer Trap](#3-the-pretty-face--studio-neutralizer-trap)
4. [The "Less is More" Principle: Attribute Overload & Attention Dilution](#4-the-less-is-more-principle-attribute-overload--attention-dilution)
5. [Token Ordering & Placement in `Photoshoot Build Prompt`](#5-token-ordering--placement-in-photoshoot-build-prompt)
6. [Turbo & Distilled Models (CFG 1.0) vs. Standard Models (CFG > 3.0)](#6-turbo--distilled-models-cfg-10-vs-standard-models-cfg--30)
7. [Eliminating Spatial & Physical Contradictions](#7-eliminating-spatial--physical-contradictions)
8. [Macro Focus Isolation & Head Proportion Balance](#8-macro-focus-isolation--head-proportion-balance)
9. [Practical Workflow Cheat Sheet](#9-practical-workflow-cheat-sheet)

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

One of the most frequent mistakes in structured prompt building is **over-selecting attributes** across every tab and dropdown.

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
   In the **Photoshoot Ausdruck** (Expression Builder) node, the primary dropdown (`Stimmung`) is pre-engineered as a complete, physically harmonious Action Unit.
   * If you select `Stimmung = Strahlend (Lachen)` and *simultaneously* pick `Mund = Zusammengepresst` (pursed lips) and `Augen = Aufgerissen` (wide alarmed eyes), the model receives two opposing mouth instructions at the same time. The result is an awkward, frozen grimace.
   * **Rule of Thumb:** Keep secondary dropdowns (`augen`, `blick`, `mund`, `brauen`, `kopf`) on **`"— keine Auswahl —"`** unless you specifically intend an asymmetric micro-modification (such as a wink or looking to the side).

4. **The Sweet Spot for Character Design:**
   To create a distinctive, reproducible character, choose **3 to 5 strong identity anchors**:
   * **Age & Heritage** (e.g. *Late 20s, Scandinavian*)
   * **Hair** (e.g. *Wavy copper red, shoulder-length*)
   * **Eyes & 1 Unique Trait** (e.g. *Hazel eyes, light bridge freckles*)
   * **Simple, High-Contrast Clothing** (e.g. *Clean black crewneck top*)
   
   *Leave the remaining 30 micro-fields empty.* The diffusion model will naturally interpolate harmonious proportions around your anchors.

---

## 5. Token Ordering & Placement in `Photoshoot Build Prompt`

Text encoders read prompts from left to right. Tokens positioned in the first 20–30 slots receive significantly higher attention weights than tokens positioned after token 60.

### The Dilution Problem:
If your prompt starts with 60 tokens of identity:
```
tight close-up portrait of an elegant woman, in her late 20s, Scandinavian features, fair skin with natural texture and visible pores, almond-shaped hazel eyes, wavy copper red hair, subtle natural makeup, wearing a clean black crewneck top, screaming in terror...
```
The expression tokens arrive too late and get drowned out.

### The Recommended Prompt Order:
In the **Photoshoot Prompt bauen** (`Krea2PromptJoin`) node, place `{ausdruck}` near the front:

```text
{stil}, {kamera}, {ausdruck}, {person1}, {pose}, {licht}, {szene}
```

This guarantees that:
1. The look (`{stil}`) is read before any colour word — a black and white style at the end of the prompt still renders in colour, at the front it takes.
2. Framing (`{kamera}`) sets the shot distance.
3. Emotion (`{ausdruck}`) commands the facial structure.
4. Identity (`{person1}`) fills in hair, eyes, and features.
5. Environment (`{szene}`) frames the background.

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
The Person Builder contains 12 fields for the face and 8 for the body. Because diffusion models allocate frame area roughly proportional to token density, full-body shots (`Ganzkörper`) and wide shots (`Totale`) risk generating disproportionately large heads.
* **Solution:** On wide framings, Photoshoot automatically shortens the person description (`detail_fuer_kamera`) and injects proportion counterweights:  
  `"realistic head-to-body proportions with a proportionally small head, ample negative space"`.

### 2. Macro Floor-Level Detail Shots:
When shooting footwear (`Füße`) or hands (`Hände`) in **Detail** mode:
* The camera is forced to macro perspective:  
  `"extreme close-up macro shot of feet and shoes, low angle floor-level perspective, camera focused tightly on the footwear and ankles"`.
* The person description is automatically pruned to only describe footwear/hosiery (`DETAIL_FUESSE`), preventing head and torso tokens from leaking into floor-level shots.

---

## 9. Practical Workflow Cheat Sheet

### Setting Up a Consistent 20-Photo Shoot:
1. **Define Identity Once:** Use `Photoshoot Person` to set up 3–5 core anchors (age, hair, eyes, skin, simple top). Save it via `Photoshoot Person speichern`.
2. **Keep Sub-Dropdowns Empty:** In `Photoshoot Ausdruck`, pick 1 `Stimmung` and leave sub-dropdowns on `"— keine Auswahl —"`.
3. **Wire to Photoshoot Serie:** Connect `person_data` from Person Builder to `person_data` on `Photoshoot Serie`.
4. **Set the Prompt Template:** In `Photoshoot Prompt bauen`, use:
   ```text
   {stil}, {kamera}, {ausdruck}, {person1}, {pose}, {licht}, {szene}
   ```
5. **Lock Scene Seed (Optional):** If you want the same room environment across all shots, disable the `rausch` (noise) toggle in Photoshoot Serie. The seed stays constant while camera, pose, and expression vary.
6. **Run Queue:** Click **Photoshoot starten**. The photo number counts up from the start number, and every photo is a distinct, non-colliding image. For a fresh series with the same settings, roll the die next to the start number and click again.

---

*For detailed node inputs and internal architecture, see [nodes.md](nodes.md) and [internals.md](internals.md).*
