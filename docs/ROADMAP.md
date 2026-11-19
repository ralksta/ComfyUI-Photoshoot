# Roadmap

Tracks shipped milestones, core architecture constraints, and candidate items for future releases.

> [!NOTE]
> **Invariants across all releases:** German preset labels and `Krea2*` node/API names stay frozen for workflow compatibility; core nodes emit text only; built-in presets require render tests first; Series outputs are only ever appended.

---

## Shipped Milestones (`v2.7` – `v3.0`)

| Version | Highlights |
|---|---|
| **v2.7** | Deterministic draft mode (`refine`, `dateiname`), JS↔Python 886-state parity (`tests/plan.mjs`), `Save Dataset`, offline workflow snapshots |
| **v2.8** | Undo integration, Gaze axis, Shareable shoot files (`photoshoot-shoot/1`), **Director** LLM planner, *Shoes/Tops/Bottoms/Bikini/Headwear/Bangs* matrices |
| **v2.9** | **Studio sidebar**, **Compact nodes**, **Lightbox** (`← → F X C`), **Next round →**, Live **Custom presets** (+ pack manager), **Location** set & light axes, **Selfie round 1**, **Camera angles**, **Handheld props**, **Anchor set**, `photoshoot-reference-qwen21.json` |
| **v3.0** | **Location presets** (17 asymmetric-verified places, 5 times of day, 5 weather, 4 seasons) + winter swimwear warning, **Two People / Couples** (`person_2_data`, Studio `Person 1 \| Person 2`, `compose_couple`), interactive **Wording lab**, **Character Cards (Casting Deck)**, **Model Profiles** (`krea2` / `kompakt` / `eigen`), **Visual Preset Pack Editor & Exporter**, I2V **Motion Bridge** (`motion` output), **Selfie über die Schulter** (round 2), **MiniMax-H3-Image 2K Studio workflow** (`photoshoot-studio-minimax.json`), and **ComfyUI native QoL integration** (Settings, workflow-aware branded top-bar buttons, keybindings, tooltips/aliases, toasts & live progress) |

---

## Future Ideas (`3.1+`)

| Area | Idea | Status |
|---|---|---|
| **Workflow & Review** | Mark contact-sheet tiles *outdated* when upstream person/wardrobe/scene/style/lighting state changes after render | later |
| **Workflow & Review** | Framing-conditional final pass (face refine on wide shots, model upscale on starred favourites) | render |
| **UX** | Thumbnails on Style *Look* & Location *Place* drawers matching the Pose/Lighting picture tiles | later |
| **Series Engine** | Per-frame shot list overrides & standing → sitting → lying custom camera/pose arcs | later |
| **Series Engine** | Printable proof-sheet image node (tiles + frame numbers + starred badges) | later |
| **Series Engine** | Synchronized storyboard arcs across scene, lighting, outfit & mood (*a day in her life*) | later |
| **Camera Lens** | Dynamic framing-coupled Style lens switching beyond current `kameraOptik` focal tags | later |
| **Documentation** | Reference poster sheet covering all 17 verified Location places (`tools/wortlabor/orte.json`) | later |

---

## User Customization Ideas (`3.1+`)

| Feature | Concept | Status |
|---|---|---|
| **Custom Preset Thumbnails** | Save rendered Wording Lab winners (or click `📷`) into `user/krea2_presets/thumbs/` so custom items get thumbnails in two-column dropdowns & tile grids | idea |
| **Preset & Family Mute Filter** | Optional `user/krea2_presets/_filter.json` / UI toggle to exclude selected presets or entire families (e.g. extreme items/moods) from `🎲` dice & Series pools | idea |
| **Custom Mood/Story Arcs & Archetypes** | Editable user arcs (custom mood stages or location progressions) and custom **Inspire Me** character pools stored as JSON alongside custom presets | idea |
