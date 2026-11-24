# Workflows, Character Consistency & FAQ

Reference guide for the shipped example workflows, LoRA setups, character consistency workflows, and common questions. For individual node controls see [nodes.md](nodes.md); for first steps see [quickstart.md](quickstart.md).

---

## Example workflows

Five workflows ship in [`example_workflows/`](../example_workflows/) (and appear in ComfyUI's template browser under **ComfyUI-Photoshoot**):

| Workflow | Nodes | Use case |
|---|---:|---|
| [`photoshoot-studio.json`](../example_workflows/photoshoot-studio.json) | 11 | **All-in-One Studio (Krea 2)** — edit Person, Wardrobe, Look, Pose, Shoot & Director in the Studio sidebar with a compact Series node on the canvas |
| [`photoshoot-studio-zimage.json`](../example_workflows/photoshoot-studio-zimage.json) | 16 | **Studio · Z-Image Turbo (Fast Start)** — 8-step single-pass Studio workflow (`lumina2`, `Compact` profile, ~3 s/image) |
| [`photoshoot-studio-minimax.json`](../example_workflows/photoshoot-studio-minimax.json) | 14 | **Studio · MiniMax-H3-Image (2K)** — single-pass 2K Studio workflow (`MiniMaxH3ImageConditioning`, 6 Euler steps, Compact profile) |
| [`photoshoot-series.json`](../example_workflows/photoshoot-series.json) | 21 | **Modular Builders** — every builder node laid out side by side on the canvas and wired into *Build Prompt* |
| [`photoshoot-reference-qwen21.json`](../example_workflows/photoshoot-reference-qwen21.json) | 30 | **Reference & Dataset** — feed up to two anchor crops into Qwen-Image-2.1 to generate consistent multi-framing training pairs (`NNNN.png` + `NNNN.txt`) |

Every workflow is generated and verified against ComfyUI's node signatures by `tools/baue_workflow.py` (which can also build a gitignored local Studio workflow for MOSS-Image via `--moss`). Every shipped workflow carries Comfy-Org HuggingFace model URLs so ComfyUI and Comfy Desktop 1.2 can download missing weights directly into the right folder on load.

### Two-pass Render subgraph & models

Inside the studio and series workflows sits one **Render (2 passes)** subgraph node (double-click to open): 8 steps at full denoise, a 1.5× latent upscale, then 4 steps at denoise `0.44`. On the canvas it exposes only `model`, `positive`, `width`, `height`, `seed`, and the **`refine`** switch driven by the Series (`Draft`).

> [!WARNING]
> **Avoid upscaling without the refinement pass.** Latent upscaling stretches the first pass (`11.4 s` vs `24.8 s`) and comes out soft because upscaling invents no detail. Either run both passes or bypass the upscale completely via **Draft**.

The loaders reference the files [Comfy-Org publishes for Krea 2](https://huggingface.co/Comfy-Org/Krea-2) (`krea2_turbo_fp8_scaled`, `qwen3vl_4b_fp8_scaled` with CLIP type `krea2`, and `qwen_image_vae`). Other checkpoints work too, though the **text encoder is specific**: Krea 2 taps twelve layers of Qwen3-VL-4B at hidden size `2560`, so plain Qwen3-4B (no vision tower) and the 32B build will not load.

### Draft before you shoot

Before running 40 full images, tick **Draft** under *Start shooting*:

- The Series turns `refine` off, skipping the upscale and second sampler (a lazy switch, so nothing extra is computed).
- Measured on local Krea 2 weights: **10.2 s per image instead of 21.5 s**, at base resolution instead of 1.5×. Six calibration images take 61 s instead of 129 s.
- Because the series counts deterministically rather than rolling random dice, runs `1..6` in Draft match runs `1..6` in the final shoot in composition and framing.
- Star your keepers (**♥ Favourite**) in the contact sheet or Lightbox and press **Finish favourites**: only those exact frames re-queue with pass 2 enabled, matching seed, take, framing, and pose. Draft frames carry a dashed border until the final image replaces them (`photoshoot/s0001/07_t1_draft_00001_.png` vs `photoshoot/s0001/07_t1_00001_.png`).

---

## Wiring patterns

### Modular canvas vs All-in-One Studio

In **Studio mode** (`photoshoot-studio.json`), Person, Wardrobe, Location, Lighting, Style, and the prompt template live directly inside `Krea2Photoshooting`'s state, which emits the complete **`prompt`** output. Any section can be popped out as its own node with **↗ Pop out as node**.

In **Modular mode** (`photoshoot-series.json`):

```text
Wardrobe ──► Person Builder ──person_data──► Photoshoot ──┬── person       ─┐
 outfits     38 fields, saved once          the series  ├── pose          │
                                                        ├── expression    ├──► Build Prompt ──► Sampler
Location ─────────────────────ort_data──────────────────┼── scene / light │
 sets & weather                                         ├── camera        │
Style ──────────────────────────────────────────────────┴── width / height / image_seed
```

- **Standalone Pose / Expression:** wire directly into Build Prompt without a Series node when shooting single custom compositions.
- **Set & Light axes:** wire `Krea2LocationBuilder.ort_data` into `Photoshoot.ort_data`, and take `szene` / `licht` from the Series into Build Prompt instead of static nodes.
- **Two people / couples:** wire a second Person node into `Photoshoot.person_2_data` (or enable **Person 2** directly inside *Studio → Person*). The Series outputs `compose_couple()` ("*Two people … On the left, … On the right, …*") on `person`, or fills `{person1}` and `{person2}` separately when a custom template names `{person2}`.
- **Image-to-Video Motion Bridge:** wire the 17th output `motion` into any I2V prompt node for movement cues tailored to the current framing and transition to the next photo.

---

## Character consistency

### Already have your character?

Unwire **Person Builder** — `{person}` simply drops out without stray commas while framing, pose, placement, expression, focus, and aspect ratio still vary:

```text
close-up shot, with the focus on the neckline, walking, near a window, torso
turned away, looking back over the shoulder, arms wrapped around the knees,
knees together, feet apart, back arched, a soft gentle smile, eyes closed,
looking past the camera, furrowed brows, pursed lips, head tilted slightly
```

Put your LoRA trigger into **`{extra}`** in Build Prompt, or even better: keep **Person Builder** wired and fill in **LoRA trigger** or **Reference** alongside body/outfit fields. Leaving the face fields empty (or suppressed by trigger/reference mode) avoids conflicting signals between text and weights while holding height, body proportions, and Wardrobe outfits steady across every frame.

> [!NOTE]
> **Why plain `img2img` does not work.** The initial latent locks in the source image's spatial geometry, so framings and ratios stay stuck. Tested across three denoise levels ([measurements.md](measurements.md)): at `0.45` neither framing nor identity held; at `0.85` the direction landed on a complete stranger. You need a text-only anchor seed, a LoRA, or an identity-edit model.

### Need a character to use elsewhere?

1. **Switch the Noise axis off first** — before rolling shots, not after. With *Noise* on, every run invents new unspecified facial details. Switching it off reveals a single fixed **Series seed** with a die beside it: roll until you find a face you like, then leave the seed alone while camera, pose, and expression keep varying.
2. **Recovering a single photo's seed:** If you spotted a great face at photo `N` with *Noise* still on, type `((N - 1) × 2654435761) mod 2³¹` into the fixed seed field — for example, photo 8 is seed **`1401181143`**.
3. **One-click Anchor set recipe:** Select **Anchor set** in the Series panel for six framings at `2:3`, *Calm* mood, and a locked series seed (`photoshoot/anchor`).

### From an anchor set to a character LoRA

Four optional steps to graduate from a temporary seed to a reusable character:

1. **Anchor set:** Render the six-photo Anchor set above and keep two references: a **tight head-and-shoulders crop** and a **full-body shot**.
2. **Reference series with Qwen-Image-2.1:** Open [`photoshoot-reference-qwen21.json`](../example_workflows/photoshoot-reference-qwen21.json). Set Person Builder's *Reference* field to `1, 2` so the prompt says `"the same woman as in <image1> and <image2>"` and suppresses textual hair/face/makeup while keeping age, build, and Wardrobe outfits active. Runs in ComfyUI core (24 GB VRAM default; swap to int8 on 16 GB; experimental — settings not render-benchmarked yet).
3. **Dataset export:** Enable **Photoshoot – Save Dataset** (`Ctrl+B`) in that workflow. Each photo saves alongside `NNNN.txt` captions carrying your LoRA trigger + what varies (*framing, pose, expression, outfit*) — **never identity fields**, so the LoRA binds the face cleanly to the trigger word instead of English adjectives.
4. **Train & run your Character LoRA:** Enable the bypassed `LoraLoaderModelOnly` (`Ctrl+B`) in the main Krea workflow and type your trigger into *LoRA trigger* on the Person node.

> [!NOTE]
> **Commercial licence note:** [Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1) carries the **non-commercial** Qwen Research License. For commercial reference workflows, swap in Krea 2 with the Krea 2 Identity Edit LoRA via [comfyui-krea2edit](https://github.com/lbouaraba/comfyui-krea2edit) fed from `pose`, `ausdruck`, and `kamera` (requires a tight head-and-shoulders crop, [measured](measurements.md)).

---

## Adding & chaining LoRAs

Both workflows ship with a `LoraLoaderModelOnly` between `UNETLoader` and the Render node, **bypassed** (`Ctrl+B`):

1. Pick your `.safetensors` file and set strength (`1.0` to start; `0.5–0.8` for style LoRAs).
2. Select the loader and press **`Ctrl+B`** to un-bypass.
3. Place triggers properly:
   - **Character LoRA trigger** → *LoRA trigger* field on Person Builder (automatically strips conflicting face/hair fields).
   - **Style / aesthetic trigger** → front of Build Prompt's template, e.g. `myStyle, {style}, {expression}, …`.
4. To switch LoRAs without panning the canvas, right-click any LoRA loader → **Pin to Photoshoot Studio** to place `lora_name` and `strength_model` in *Studio → Your setup*.

---

## Model compatibility

Photoshoot outputs standard English prompt strings, pixel dimensions, and integer seeds — it makes no model API calls:

- **T5 / LLM text encoders (Krea 2, MOSS-Image, MiniMax-H3, Z-Image, Qwen-Image, Flux, SD 3.5):** Best match. Prompts run 760–1,000 characters (~190–250 tokens), reading connected natural-language clauses reliably.
- **CLIP-only models (SD 1.5, SDXL):** Chunk at 77 tokens; trim optional Person Builder fields and lean on distance shortening (*Wide shot* sends `[identity]` automatically). Default edges (`1024–1536 px`) target modern DiT models rather than 512 px SD 1.5.

### Using other models (Z-Image Turbo, MOSS-Image, MiniMax-H3-Image, Qwen-Image)

In **Photoshoot Studio → Your setup**, switch **Model profile** to **Compact** for non-Krea-2 models (drops Krea-2's head-proportion counterweight padding so figures do not shrink in full-body shots). Benchmarked configurations ([measurements.md](measurements.md#8-multi-model-framing-profiles-krea2-vs-kompakt)):

| Model | CLIP `type` | Latent / Conditioning | Sampler / Steps / CFG | Studio profile |
|---|---|---|---|---|
| **Krea 2 Turbo** | `krea2` (`Huihui-Qwen3-VL-4B` / `qwen3vl_4b`) | `EmptySD3LatentImage` (2-pass or Draft) | `euler` / `simple`, 8 steps, CFG `1.0` | **Krea 2** |
| **Z-Image Turbo** | `lumina2` (`qwen_3_4b`) + `ae.safetensors` | `EmptySD3LatentImage` + `ModelSamplingAuraFlow` (`shift: 3.0`) | `euler` / `simple`, 8 steps, CFG `1.0` | **Compact** |
| **MOSS-Image SFT** | `moss_image` (`qwen3.5_9b`) + `flux2-vae_small` | `EmptyFlux2LatentImage` | `er_sde` / `simple`, 25 steps, CFG `2.5` | **Compact** |
| **MiniMax-H3-Image** | `minimax` (`qwen3vl_32b_minimax_h3`) | `MiniMaxH3ImageConditioning` (~2K single pass) | `euler` / `simple`, 6 steps, CFG `1.0` | **Compact** |
| **Qwen-Image 2512** | `qwen_image` (`qwen_2.5_vl_7b`) | `EmptySD3LatentImage` + `ModelSamplingAuraFlow` (`shift: 3.1`) | `euler` / `simple`, 16–25 steps, CFG `2.5` | **Compact** |

To generate a ready-to-open local Studio workflow for MOSS-Image outside git:

```bash
python3 tools/baue_workflow.py --moss     # -> example_workflows/photoshoot-studio-moss.local.json
```

---

## Custom presets, Comfy Desktop & saved blocks

- User stores live outside the repository under `ComfyUI/user/krea2_persons|scenes|styles|lights|prompts|characters|series|shoots|presets/`.
- **Comfy Desktop 1.2 & multi-build sharing:** Set `PHOTOSHOOT_USER_DIR=/path/to/shared/photoshoot` in a build's startup environment to share character cards, custom presets, series, and shoots across builds, or use **Studio → Your setup → Data & Backup** for 1-click `.zip` export and restore.
- Add custom items live via **+ Custom entry …** at the bottom of extendable dropdowns, test candidate wordings in **Studio → Your setup → Wording lab**, or paste JSON packs (`photoshoot-presets/1`) generated from `/krea2/custom/llm_prompt`. See [nodes.md#custom-entries](nodes.md#custom-entries).

---

## FAQ

<details>
<summary><b>Why does the photo number count up instead of rolling a random seed?</b></summary>

Each integer photo number deterministically hashes via a Kronecker sequence into a distinct noise seed and field step index. Consecutive frames look just as varied as random seeds, while letting you reproduce any individual frame (`Photo 8`), continue a shoot cleanly at `Photo 13`, or run quick *Draft* previews knowing `1..6` match the full render.

</details>

<details>
<summary><b>How do I get a completely fresh series or fix just one bad image?</b></summary>

- **Fresh series:** Increment the start number (or click **↻ New series**) and press **Start shooting**. Typing an old start number brings back that exact shoot plan.
- **Fix one image:** Click the tile in the contact sheet (or Lightbox) → **↻ Re-shoot** → **Re-shoot 1 photo**. Framing, pose, outfit, and expression stay identical while a new take gets fresh noise.

</details>

<details>
<summary><b>How do I narrow down a shoot around my favourites?</b></summary>

Star keepers (**♥ Favourite** / `F`), optionally reject misses (**✕ Reject** / `X`), and click **Next round →**. The next series automatically filters framings, pose families, mood families, focus targets, and outfits down to your selects (while **← back to round 1** restores earlier rounds).

</details>

<details>
<summary><b>How do I get true Black & White without coloured lipstick?</b></summary>

Pick a *Black & White* look in **Photoshoot – Style** and ensure **`{style}` sits first** in your prompt template (tested at the end, the person block overrides it back into colour). For pixels with zero chromatic tint on lips or skin, select the bypassed **Photoshoot – Monochrome** node before Save Image and press **`Ctrl+B`** ([measured](measurements.md)). *(Lighting → Film Noir adds contrast, not colour removal.)*

</details>

<details>
<summary><b>Why do my renders look different from the reference posters?</b></summary>

Photoshoot emits prompt text only. All reference sheets in [`docs/POSTERS.md`](POSTERS.md) were rendered with Krea 2 Turbo (fp8) + Qwen3-VL-4B, 8 steps, CFG `1.0`, 0 LoRAs (garment sheets add the 4-step 1.5× refine pass). A distilled CFG-1 model responds differently to word order and token weight than checkpoints using strong negative prompts.

</details>
