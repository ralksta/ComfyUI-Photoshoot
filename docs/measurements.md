# Measurements

Empirical findings from render tests and quantitative benchmarks. Kept so every default, ordering rule, and preset decision stays traceable.

<details open>
<summary><b>Contents</b></summary>

1. [Wording Lab Method (`tools/wortlabor.py`)](#1-wording-lab-method-toolswortlaborpy)
2. [Two-Pass Rendering vs Draft Mode](#2-two-pass-rendering-vs-draft-mode)
3. [Why Plain `img2img` Fails & Identity-Edit Models](#3-why-plain-img2img-fails--identity-edit-models)
4. [Pose Coupling & Bit-Identical Reproducibility](#4-pose-coupling--bit-identical-reproducibility)
5. [Fixed Seed vs Prompt Conditioning (`22 %` Setting Hold)](#5-fixed-seed-vs-prompt-conditioning-22--setting-hold)
6. [Style Token Position, True Monochrome & Look Separation](#6-style-token-position-true-monochrome--look-separation)
7. [Location Asymmetry & Couple Anti-Bleed (`3.0.0`)](#7-location-asymmetry--couple-anti-bleed-300)

</details>

---

## 1. Wording Lab Method (`tools/wortlabor.py`)

New wordings only enter `PRESETS` after passing a side-by-side comparison against the bare word (`kontrolle: true`) on three fixed seeds (`776610`, `1401181143`, `42`) using the example workflow's exact builders and template:

```bash
python3 tools/wortlabor.py tools/wortlabor/orte.json --nur-zeigen
python3 tools/wortlabor.py tools/wortlabor/orte.json --gruppe A --bogen
python3 tools/wortlabor.py tools/wortlabor/selfie2.json --bogen --einzeln
```

- Renders **pass 1** (~8.1 s/image on RTX 4090) into `tests/_tmp/wortlabor/<file>/`, generating contact sheets (`--bogen`, max 6 rows per sheet, optional `--refine` pass 2 and `--einzeln` 1000 px JPGs).

---

## 2. Two-Pass Rendering vs Draft Mode

Measured locally on Krea 2 Turbo (fp8) across distinct seeds (`1088×1632` → `1.5×` upscale `1632×2448`):

| Mode | Time / image | Resolution | Quality & behaviour |
|---|---:|---|---|
| **Full (2 passes: 8 + 4 steps @ 0.44)** | `24.8 s` (`21.5 s` warm) | `1632×2448` | Crisp full-res output |
| **Upscale without refine pass** | `11.4 s` | `1632×2448` | **Unusably soft** — latent upscaling invents no detail |
| **Draft (bypass upscale + pass 2)** | `10.2 s` | `1088×1632` | Sharp base-res preview; **identical composition** to full render |

Because pass 1 runs the exact same initial node in Draft and Full mode, starred Draft keepers finish at full resolution without composition shifts.

---

## 3. Why Plain `img2img` Fails & Identity-Edit Models

### Plain `img2img` (`LoadImage → VAEEncode`, Person dropped)

Tested on Krea 2 Turbo, Series run 3, across three denoise levels:

| Denoise | Framing | Identity |
|---|---|---|
| `0.45` | Stuck at source full-body | Already drifting (copper hair turned brown) |
| `0.65` | Slightly turned, still full-body | Different woman |
| `0.85` | Re-composed | Complete stranger |

No sweet spot exists because the initial latent locks geometry while removing the person text unmoors identity.

### Identity-Edit (`comfyui-krea2edit`, r64 Identity Edit LoRA)

Person Builder unwired (`camera + pose + expression` only, `ref_boost` 1.0–2.0; 4.0 clings too hard to source pose):

| Anchor crop | Asked for | Result |
|---|---|---|
| Full-body anchor | Close-up | **Refused** (stayed full-body) |
| Head-and-shoulders anchor | Full body | **Followed** cleanly, identity held |
| Head-and-shoulders anchor | Extreme close-up | **Followed** cleanly, identity held |

Widening invents room/body easily; tightening refuses to invent unseen facial detail. **Crop reference anchors tight head-and-shoulders.** Reversing the order (swapping a face into a pre-generated full-body composition) reads Image 1 as a setting and fails.

---

## 4. Pose Coupling & Bit-Identical Reproducibility

- **500-run pose audit:** Independent posture/arms/legs draws produced **101 / 500 impossible contradictions** (e.g. `walking, arms wrapped around the knees`). Coupling arms, legs, and tension per posture family reduced contradictions in `smoke.py` to **0 / 500**.
- **Bit-identical runs:** Submitting identical prompt + seed via `/prompt` produces **0.00 pixel deviation** (an earlier `8.5` baseline artifact turned out to be ComfyUI's `control_after_generate` advancing one seed in the UI).

---

## 5. Fixed Seed vs Prompt Conditioning (`22 %` Setting Hold)

Measured across 5-photo series by outer-frame pixel deviation (`59 %` frame area outside the figure):

| Setup | Outer-frame deviation |
|---|---:|
| Noise per photo | `21.8` |
| Fixed series seed | `17.1` (**22 % reduction**) |
| Identical prompt + seed | `0.0` |

Holding camera and posture identical while changing only limbs/expression still measured `15.7`: the remaining **78 % of room variation** comes from prompt conditioning shifts inside an 8-step distilled model. Lock pixels with a reference latent to freeze architecture completely.

---

## 6. Style Token Position, True Monochrome & Look Separation

Measured RGB channel spread (`max - min` per pixel; `0` = pure grey) at CFG 1.0:

| Style text | Template position | RGB spread |
|---|---|---:|
| Editorial colour | Last | `25.1` |
| `black and white photograph, monochrome, …` | Last | `26.0` (rendered in full colour) |
| `black and white photograph, monochrome` | **First** | `4.9` |
| `black and white photograph, monochrome, rich tonal range, …` | **First** | `2.6` (lip peaks up to `21`) |

**Takeaway:** Put `{style}` first so it precedes hair/lip colours, and add **Photoshoot – Monochrome** to eliminate remaining skin/lip warmth.

### Black & White & Colour Look Separation

Named film stocks (*Ilford Delta 3200*, *HP5*, *Teal & Orange*, *Bleach Bypass*) clustered identically (`107.8–113.6` brightness, `1.77–1.94` grain, RGB spread unchanged). Moving **visual properties to the head of the phrase** (`extremely grainy…` → `3.44` grain, `razor sharp grain-free…` → `1.71`, `infrared glowing white skin…` → `77.7` brightness) produced measurable separation across all **10 B&W looks** and **7 Colour looks** (*Clean Digital* baseline `94.7 / 82.7 / 22.4` vs *Kodak Portra* `122.6`, *Cinestill 800T* `109.0` sat, *Polaroid* `155.5`, *Warm Golden* `35.3`, *Cool Desaturated* `17.3`).

---

## 7. Location Asymmetry & Couple Anti-Bleed (`3.0.0`)

- **Asymmetric Locations (`orte.json` → `orte2.json`):** Running `orte.json` with an empty `{pose}` slot triggered a 1-point corridor prior (`between tall office buildings`, uniform `tall pine trunks`, straight `old town alley`). Retesting with a relaxed contrapposto pose + angled phrasing (*winding forest path at uneven depths*, *city sidewalk at a corner storefront*, *gently curving cobblestone lane*, *curving sandy coastline*, *angled wooden bookcase corner*) broke central symmetry cleanly across seeds.
- **Anti-Attribute Bleed in Couples (`paare.json`):** Comma-joined descriptions (`a woman with black turtleneck..., and a man with ivory sweater...`) bled the first person's black turtleneck onto the second person on 3/3 seeds. Separating subjects into two spatial sentences — **`Two people <interaction>. On the left, <p1>. On the right, <p2>.`** — eliminated colour and fabric bleed across all 5 tested couple interactions.

---

## 8. Multi-Model Framing Profiles (`krea2` vs. `kompakt`)

Measured on `tor` (RTX 4090) across 6 diffusion models comparing `KAMERA` (`krea2`) vs. `KAMERA_KOMPAKT` (`kompakt`) on `Porträt` (`4:5`) and `Ganzkörper` (`2:3`):

| Model | Sampler / Steps | Resolution | Speed / Frame | `krea2` Full-Body | `kompakt` Full-Body |
|---|---|---|---:|---|---|
| **Krea 2 Turbo** (`krea2_turbo_fp8_scaled`) | euler / simple, 8 steps, CFG 1.0 | `832×1248` | `5.0 s` | ~12 % headroom, full head-to-toe | ~8 % headroom, fills ~80 % frame height cleanly |
| **Moody Krea 2 Mix V8SE** (`moodyKrea2Mix_V8SE_int8`) | euler / simple, 8 steps, CFG 1.0 | `832×1248` | `4.0 s` | Full head-to-toe, slightly smaller subject | Balanced margins, natural torso-to-leg ratio |
| **Z-Image Turbo** (`z_image_turbo_bf16`, Lumina2) | euler / simple, 8 steps, CFG 1.0, shift 3.0 | `832×1248` | `3.0 s` | Over-shrunk (~55 % height, ~30 % empty upper wall) | **Optimal** (~78 % height, clean shoes-to-head framing) |
| **Qwen-Image 2512** (`qwen_image_2512_fp8_e4m3fn`) | euler / simple, 16 steps, CFG 2.5, shift 3.1 | `832×1248` | `20–22 s` | Full head-to-toe, slightly stiff centered stance | Natural relaxed stance and deeper corridor perspective |
| **MOSS-Image SFT** (`moss_image_sft_int8_convrot`, Qwen 3.5 9B CLIP) | er_sde / simple, 25 steps, CFG 2.5 | `832×1248` | `7.0–8.0 s` | ~75 % height, accurate garments & curved alley | Balanced ~60 % height with deep angled alley & full figure |
| **MiniMax-H3-Image** (`minimax_h3_image_pruned_int8_convrot`, 32B CLIP) | euler / simple, 6 steps, CFG 1.0 | `1536×2304` (2K) | `19.4–20.1 s` | Sharp native 2K environmental full-body (~55 % height) | Clean contrapposto full-body (~48 % height), wide architectural alley |

**Takeaway:** Models outside the Krea 2 family respond strongly to framing tokens: **Z-Image Turbo** obeys Krea 2's explicit `"figure fills at most half the frame height"` counterweight too literally (`~30 %` blank wall), whereas switching **Model profile** to **Compact** gives tight, well-balanced framing. **MOSS-Image SFT** (`7–8 s`, `EmptyFlux2LatentImage`) and **MiniMax-H3-Image** (`~20 s` at native 2K in 6 steps via `MiniMaxH3ImageConditioning`) both follow Photoshoot's person, outfit, contrapposto, and angled location prompts cleanly out of the box.
