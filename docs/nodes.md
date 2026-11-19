# Node Reference

Concise reference for every Photoshoot node, axis, and Studio tool. For workflow wiring & LoRA setups see [workflows.md](workflows.md); for prompt theory see [GUIDE.md](GUIDE.md) and [measurements.md](measurements.md).

<details open>
<summary><b>Quick Navigation</b></summary>

| Area | Jump to |
|---|---|
| **Builders** | [Building blocks](#building-blocks) · [Style](#style) · [Location](#location) · [Monochrome](#monochrome) · [Person](#person) · [Expression & Pose](#expression-and-pose) · [Wardrobe](#wardrobe) |
| **Series Engine** | [Series](#series) · [Perspective & selfies](#perspective-and-selfies) · [Sets & light](#sets-and-light) · [Framing vs description](#framing-wins-over-description) · [Counting](#counting-through-the-series) · [Noise](#noise) |
| **Review & Output** | [Contact sheet](#contact-sheet) · [Selects → next round](#selects--next-round) · [Draft & finish](#draft-and-finish) · [Lightbox](#lightbox) · [File names](#file-names) · [Caption](#caption) · [Save Dataset](#save-dataset) |
| **Studio & Ecosystem** | [Compact view](#compact-view) · [Studio sidebar](#studio-sidebar) · [Pinned widgets & packs](#your-setup-pinned-widgets--pack-editor) · [Wording lab](#your-setup-wording-lab) · [ComfyUI integration](#comfyui-integration--shortcuts) · [Storing blocks](#storing-blocks) · [Shoot files](#shoot-files) · [Director](#director) · [Custom entries](#custom-entries) · [Assembling](#assembling) · [Extension packs (docking)](#extension-packs-docking) |

</details>

---

### Building blocks

| Node | Inputs | Outputs | Purpose |
|---|---|---|---|
| **Photoshoot – Person** | `garderobe` (`wardrobe`) | `person`, `person_data` | 38 fields in 5 sections + active Wardrobe outfit ([details](#person)) |
| **Photoshoot – Wardrobe** | — | `outfit` | Multi-outfit tabs with mannequin/flat-lay preview ([details](#wardrobe)) |
| **Photoshoot – Pose** | — | `pose` | 24 postures (picture tiles), room placement, turn, arms, legs, tension |
| **Photoshoot – Expression** | — | `ausdruck` | 94 FACS-tested moods (9 families), eyes, gaze, brows, mouth, head |
| **Photoshoot – Lighting** | — | `lighting` | 30 setups (picture tiles, 3 families), direction, atmosphere |
| **Photoshoot – Style** | — | `style` | 17 measured looks (10 B&W + 7 colour), genre, lens, finish |
| **Photoshoot – Location** | — | `szene`, `ort_data` | 17 places (4 families), 5 times of day, 5 weather presets, 4 seasons as tabs |
| **Photoshoot – Monochrome** | `images`, `toenung`, `staerke` | `IMAGE` | True B&W conversion (*neutral*, *sepia*, *cool*) after VAE Decode |
| **Photoshoot – Save Dataset** | `images`, `caption`, `foto`, `name`, `trigger` | `IMAGE` | Saves `output/photoshoot/dataset/<name>/NNNN.png` + `.txt` pairs |
| **Photoshoot – Pick Blocks** | 4 inline dropdowns | 4 strings | Compact single-node block selector (looks best kept simple) |

All five scene/pose/mood/look/location builders share a uniform accordion UI: row die (**🎲** / `—` / family lock / `fixed` vs `new per photo`), searchable drawers (`> 12` entries) with favourites (**★**) and recent picks, **picture tiles** for Lighting setups and Pose postures, free **Details** text, and **Saved blocks** chips.

#### Style

- **17 Looks** (10 *Black & White*, 7 *Colour*), plus **Genre** (13, including *Smartphone / Social*), **Lens** (10), **Finish** (8), and *Details*.
- B&W looks only strip colour cleanly when `{style}` sits **first** in the prompt template; pair with **Monochrome** for zero residual tint ([measured](measurements.md#6-style-token-position-true-monochrome--look-separation)).

#### Location

- Manages multiple sets as tabs (**+** add, **⧉** duplicate, **×** double-click delete). Green dot = outdoors (*urban* / *nature*), amber = indoors (*studio* / *interior*).
- **17 render-tested places**, **5 times of day**, **5 weather** presets, **4 seasons** (`tools/wortlabor/orte.json` + asymmetric `orte2.json`).
- **Indoor/outdoor coupling:** indoor sets automatically strip weather and season tokens; `szene` carries the open tab while `ort_data` carries all tabs to the Series.

#### Monochrome

Only node that touches pixels. Sits between `VAEDecode` and `SaveImage` (`neutral`, `sepia`, `cool`, adjustable `staerke`). Shipped bypassed (`Ctrl+B` to toggle).

#### Person

- **5 sections (38 fields):** *Basics* (gender, age, LoRA trigger, Reference, origin, skin tone), *Body* (height, figure, bust, shoulders, waist, belly, hips, legs), *Head* (hair + cut/colour/highlights, eyes + shape/lashes/brows), *Face* (face shape, cheekbones, nose, jawline, chin), *Make-up* (lips + colour/finish, eyeliner, eyeshadow, blush, complexion, skin features).
- **Combined phrases:** hair + hairColour (`"long wavy copper red hair"`), eyes + eyeShape (`"almond-shaped grayish green eyes"`), lipColour + lipFinish.
- **Inspire Me (🎲):** rolls a coherent adult archetype across 8 themes without overwriting *LoRA trigger* or *Reference*.
- **Special subject modes:**
  - *LoRA trigger* suppresses textual hair/face/makeup identity fields and leads with `<gender>, <age>, <trigger>`.
  - *Reference* (`1` or `1, 2`) outputs `"the same woman as in <image1>..."` for Qwen-Image-2.1 while retaining age, build, and outfits.
- `person` emits full text; `person_data` carries raw JSON so the Series shrinks descriptions by framing distance.

#### Expression and pose

- **Pose (`pose_builder.py`):** *posture* (4 families: Standing, Sitting, Kneeling, Lying; 18 poster tiles + 6 floor/table extras), *room placement*, *body turn*, *arms*, *legs*, *tension*, plus *Details*.
- **Expression (`expression_builder.py`):** *mood* (94 presets across 9 FACS-tested families), *eyes*, *gaze*, *brows*, *mouth*, *head tilt*, plus *Details*. Note: adding eyes/mouth overrides on top of a composite mood often creates contradictions ([GUIDE §4](GUIDE.md#4-the-less-is-more-principle-attribute-overload--attention-dilution)).

---

### Series

**Photoshoot – Series** (`Krea2Photoshooting`) plans up to 500 frames and queues each prompt directly from **Start shooting**.

- **Inputs:** `foto` (`INT`, 1-based), optional `width_in`, `height_in`, `person_data`, `ort_data`, `person_2_data` (appended in 3.0.0 for couples).
- **Outputs (order preserved across versions):** `pose`, `ausdruck`, `kamera`, `width`, `height`, `bildseed`, `person` (combined couple sentence when `person_2_data` / Studio Person 2 is active), `person_data`, `kamera_label`, `refine`, `dateiname`, `caption`, `foto`, `szene`, `licht`, `prompt` (all-in-one Studio output), `motion` (I2V movement & camera transition prompt).

| Axis | Behaviour | Coupling / Notes |
|---|---|---|
| **Camera** | 7 framings + order (`random`, `round-robin`, `wide → close`) | Resets cleanly per outfit/set block |
| **Perspective** | 5 Selfies + 4 Camera Angles (off by default) | See [Perspective & selfies](#perspective-and-selfies) |
| **Pose** | Posture families, placement, turn, arms, legs, tension + handheld props | `KAMERA_RAUM`, `HALTUNG_ARME/BEINE/SPANNUNG`, `ABGEWANDT` strips face |
| **Expression** | Mood pools, arcs (*Joy*, *Dominance*, *Drama*), 4 **gaze** modes | Dark arcs require a Character LoRA to keep face blocks short |
| **Focus** | 12 targets (`Face` … `Feet`) | Struck through when incompatible with chosen framings |
| **Format** | 9 constant-pixel ratios (`1024–2560 px`) | Full-body never picks landscape; external `width_in/height_in` wins if Format is off |
| **Outfit** | Switches Wardrobe outfits in *blocks* or *mixed* | Resets framing arc on block changes |
| **Set** | Switches Location `ort_data` sets in *blocks* or *mixed* | See [Sets and light](#sets-and-light) |
| **Light** | *Per set*, *Time of day* (5 stages), or *Mixed* (off by default) | Outdoor sunlight only outdoors; studio softboxes only indoors |
| **Noise** | Distinct deterministic seed per photo or locked `serienSeed` | `takesJeFoto` renders 2–4 takes per frame |

<details>
<summary><b>Built-in Recipes</b></summary>

| Recipe | Count | Setup |
|---|---:|---|
| **Editorial** | 12 | Portrait → Full body, varied moods & poses |
| **Lookbook** | 12 | Full body & Cowboy shots for outfit showcasing |
| **Headshots** | 10 | Tight framing, Studio-safe lighting & camera gaze |
| **Shoes** | 8 | Floor-level footwear close-ups & legs |
| **Test sheet** | 7 | Every framing once (`Draft` friendly) |
| **Anchor set** | 6 | Locked seed, `2:3` ratio, calm mood, every framing once (`photoshoot/anchor`) |
| **Selfie** | 8 | Smartphone perspective cycle across all 5 selfie angles |

</details>

- **Two people / Couples:** wire a second person into `person_2_data` or enable **Person 2** in *Studio → Person*. Uses `compose_couple()` (`"Two people <interaction>. On the left, <p1>. On the right, <p2>."`) or passes `{person1}` / `{person2}` separately when `{person2}` appears in the prompt template.
- **Axis warnings:** stayed visible above the axes — warns when a focus has no valid framing, `width_in/height_in` is ignored while Format varies, `person_data`/`szene`/`licht` is missing, or when **swimwear** meets an active outdoor **Winter / Snow** set.

#### Perspective and selfies

Five render-verified **selfie** angles plus four classic angles (*Low angle*, *High angle*, *Bird's-eye*, *Dutch angle*):

| Perspective | Core couplings | Allowed framings |
|---|---|---|
| *Selfie from above* / *Eye-level* | Phone in one hand (`EINE_HAND_FREI`), no back view, `9:16`/`4:5` | Close-up, Portrait, Medium |
| *Selfie lying down* | Same + forces lying posture on back | Close-up, Portrait, Medium |
| *Mirror selfie* | Looks at phone screen (`no camera gaze` / `no kiss`) | Full body only |
| *Selfie über die Schulter* | Body `Über die Schulter gedreht`, gaze `In die Kamera` | Portrait, Medium |

#### Contact sheet

Shows every photo frame in its real aspect ratio (24 per page). Click any frame for its plan metadata and exact rendered **prompt** (with copy button), star **♥ Favourite**, reject **✕**, switch **Takes**, or queue **▶ Shoot photo** / **↻ Re-shoot** (new noise, identical plan). State persists in the workflow JSON.

#### Selects → next round

Star keepers (**♥ Favourite** / `F`) and optional rejects (**✕ Reject** / `X`), then press **Next round →**: schedules a new series continuing at the next free number restricted strictly to the framings, pose/mood families, focus areas, perspectives, and outfits of your selects (**← back to round 1** restores earlier rounds).

#### Draft and finish

**Draft** switches `refine` off so the workflow skips the 1.5× latent upscale and pass-2 sampler (`10.2 s` vs `21.5 s`, ~half runtime at identical seed & composition). Starred drafts re-queue at full quality via **Finish favourites**.

#### Lightbox

Opened via **⤢ Lightbox** (or double-clicking any tile) in ComfyUI's bottom panel or fullscreen overlay: filters by *All / Favourites / Rejects / Drafts / Framing*, side-by-side compare (`C`), and shortcuts `← →` browse · `F` favourite · `X` reject · `C` compare · `Esc` close.

#### File names

`dateiname` outputs `<folder>/s<start>/<photo>_t<take>` (with `_draft` appended when Draft is on), keeping drafts and final renders side by side under `output/photoshoot/`.

#### Caption

Outputs training captions for Character LoRAs: `trigger`, subject, `_kamera_kurz`, `pose`, `ausdruck`, and visible outfit items — **never** identity fields (`LORA_WEG`), age, body, or reference phrases ([why](workflows.md#from-an-anchor-set-to-a-character-lora)).

### Save Dataset

Wire `images`, `caption`, and `foto` from Series into **Photoshoot – Save Dataset** (`Krea2DatasetSave`) to write paired `output/photoshoot/dataset/<name>/NNNN.png` + `NNNN.txt` files compatible with kohya, ai-toolkit, and OneTrainer. Safe path cleaning prevents directory traversal; re-shooting photo `N` overwrites `000N`.

#### Framing wins over description

Wide and full-body shots automatically prune unseen facial micro-tokens (`detail_fuer_kamera`: *Wide* → `[identity]`, *Medium/Full* → `[figure]`, *Portrait/Close-up* → `[above chest]`, *Macros* → feet/hands isolated) so eye/lip weight never pulls wide framings tight ([details](measurements.md)).

#### Counting through the series

Instead of `random`, each axis steps deterministically through prime-offset Kronecker sequences (`foto` 1..N → `bildseed` + field index), preventing axes with equal list sizes from locking step and making every frame number reproducible.

#### Noise

- *Noise on:* fresh deterministic hash seed per photo number.
- *Noise off:* fixed `serienSeed` across all photos in the run (hold room layout & seed character identity; takes add a distinct offset per take).

#### Wardrobe

Hold outfits as tabs (`+`, `⧉`, `×` with colour dot = primary garment swatch). Fields: top, bottom & material, hosiery, shoes, jewellery, eyewear, headwear, plus free *Details*. **Preview** renders a mannequin or flat lay via ComfyUI's queue and tracks staleness (`outdated`) if garments change later.

#### Sets and light

When `ort_data` is connected, the **Set** axis rotates locations (*blocks* or *mixed*) and passes shortened first clauses (`kurzform`) to *Close-up* / *Portrait* shots and `""` to *Detail* macros. When **Light** is active, setups automatically respect `LICHT_NUR_DRAUSSEN` (outdoor sunlight/twilight only outside) vs `LICHT_NUR_DRINNEN` (softboxes/windows only indoors), or step across the 5-stage *Time of day* arc (*Morning → Night*).

---

### Compact view

Click **⊟** / **⊞** in any Photoshoot node bar to collapse cards to compact summaries (new nodes & shipped workflows open compact; Ctrl+clicking summaries opens the corresponding Studio tab). Commands: *Photoshoot: Compact all / Expand all*.

---

### Studio sidebar

Open **Studio** in ComfyUI's left sidebar to edit a complete shoot in one column (synced live with canvas nodes and `Ctrl+Z`, or embedded directly inside `Krea2Photoshooting` with **↗ Pop out as node**):

| Tab | Contents |
|---|---|
| **Person** | **Person 1 \| Person 2** switcher, **Character cards** casting deck, *Second person active* & *Couple interaction*, Person & Wardrobe panels |
| **Look** | Lighting (picture tiles), Style, Location sets, and All-in-One prompt template |
| **Pose** | Pose (picture tiles) & Expression (or link to Shoot when planned by Series) |
| **Shoot** | All 10 axes, recipes, Start/Draft/Finish buttons, and **⤢ Open Lightbox** |
| **Director** | One-sentence / vision-chat LLM shoot generator & save/load `.json` shoot files |
| **Your setup** | Pinned graph widgets, `.json` preset pack editor & exporter, **Model profiles**, & **Wording lab** |

#### Character cards & Model profiles

- **Character cards (`Studio → Person`)**: Save complete Person + Wardrobe states (plus active `LoraLoader` / `LoraLoaderModelOnly` file & strength) into `ComfyUI/user/krea2_characters/` via `/krea2/characters`, and 1-click load any card into **Person 1** or **Person 2** without overwriting Location, Lighting, Style, or Series settings.
- **Model profiles (`Studio → Your setup`)**: Switch `kamera` framing wordings between **Krea 2 (Default)**, **Compact (Flux / Qwen / SDXL)** (concise model-neutral framings without Krea-2's head-proportion padding), and **Custom framings** (per-framing English text overrides).

#### Your setup: pinned widgets & pack editor

Right-click any node in ComfyUI → **Pin to Photoshoot Studio** to pin LoRA loaders (`lora_name`, `strength_model`), sampler steps, or switches directly into *Your setup* (`extra.photoshootPins`, saved with the workflow). Under **Custom presets**, expand any `.json` pack to edit labels/prompts/families inline, toggle `🎲` dice pooling per pack, or export packs as downloadable `.json` files.

#### Your setup: Wording lab

Pick any field (`Wardrobe`, `Person`, `Location`, `Lighting`, `Style`, `Pose`, `Expression`), enter a label (= control) + Candidate A (optional B), click **Test on 2 seeds** to render side-by-side draft tiles directly in your active workflow, and save winners straight into Custom Presets.

#### ComfyUI integration & shortcuts

- **Settings (`ComfyUI Settings → Photoshoot`):** Override panel language (`auto` / `de` / `en`), choose whether newly placed nodes start compact, auto-open Studio on workflow load, control top-bar quick button visibility (`Top bar quick buttons`, default: Photoshoot workflows only), and set default Model profile & edge resolution for new Series nodes.
- **Top-bar buttons & keybindings:** Branded **Studio** (`Alt+Shift+P`) and **Shoot** (`Alt+Shift+S`) buttons with the Photoshoot red-corner contact-sheet logo in the action bar (and left sidebar tab), plus **Toggle Draft** (`Alt+Shift+D`) and **Open Lightbox** (`Alt+Shift+L`) shortcuts.
- **Discovery, progress & feedback:** All 22 nodes include `SEARCH_ALIASES` & `OUTPUT_TOOLTIPS`, `Krea2Photoshooting` streams live per-frame status under the node while rendering, and actions show native ComfyUI toasts & confirm dialogs.

---

### Storing blocks

Ten Save/Load nodes persist reusable text snippets outside git under `ComfyUI/user/krea2_{persons,scenes,styles,lights,prompts}/` (flip `save`, run once, then reload UI or refresh `R` for Load dropdowns).

---

### Shoot files

Store and share whole shoots (`photoshoot-shoot/1`) under `ComfyUI/user/krea2_shoots/`, download/upload `.json` files with pre-apply diff previews and **Undo** ([sample file](shoot_example.json)).

---

### Director

Turns a brief (or attached photo in any vision LLM) into a valid shoot plan restricted strictly to render-tested built-in presets, plus an offline keyword-matcher fallback.

---

### Custom entries

Extend Person, Wardrobe, Pose, Expression, Lighting, Style, or Location live via **+ Custom entry …** in dropdowns, Studio's pack manager (`user/krea2_presets/*.json`), or `/krea2/custom/llm_prompt` (`photoshoot-presets/1`).

<details>
<summary><b>Custom JSON pack format & routes (`/krea2/custom/*`)</b></summary>

```json
{
  "format": "photoshoot-presets/1",
  "name": "90s Hats",
  "dice": false,
  "entries": [
    {"builder": "person", "field": "headwear", "label": "Fischerhut", "prompt": "a soft canvas bucket hat", "en": "Bucket hat", "group": "Hats"},
    {"builder": "person", "field": "topColor", "label": "Petrol", "prompt": "petrol blue", "en": "Teal blue", "hex": "#0f5e6b"}
  ]
}
```

- Routes: `/krea2/custom/llm_prompt`, `/krea2/custom/template`, `/krea2/custom/add`, `/krea2/custom/reload`.
- Reserved built-in keys & locked fields (`age`, `gender`, `type`) cannot be overridden; active custom entries travel inside saved workflow JSON so shared workflows keep working without the pack file.

</details>

---

### Assembling

**Photoshoot – Build Prompt** (`Krea2PromptJoin`) replaces `{style}`, `{expression}`, `{camera}`, `{scene}`, `{lighting}`, `{person}` (`{person1}`, `{person2}`, `{person3}`), `{pose}`, and `{extra}`, dropping empty slots without double commas. Recommended order: `{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}`.

---

### Extension packs (docking)

Third-party packs import `nodes/dock.py`:
- `parse_person_data()`, `strip_kleidung()`, `setze_free()`, `build_person_block()`, `pose_anhaengen()`
- `compose_person()`, `compose_couple()`, `baue_motion()`, `detail_fuer_kamera()`, `PAAR_INTERAKTIONEN`, `DETAIL_*`, `KAMERA_DETAIL`
