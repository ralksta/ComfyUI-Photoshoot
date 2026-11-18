# Changelog

Notable changes to Photoshoot. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.9.0] — 2026-11-18

### Added

- **Photoshoot Studio sidebar & All-in-One workflow (`photoshoot-studio.json`).**
  A new *Studio* tab in ComfyUI's left sidebar puts the entire shoot in one
  column (*Person*, *Look*, *Pose*, *Shoot*, *Director*, *Your setup*), starting
  directly on *Person*. `Photoshoot – Series` now also outputs the assembled
  `prompt` directly and can hold Person, Wardrobe, Location, Lighting, Style and
  Prompt template states internally — so a complete shoot works from a single
  node on the canvas (with **↗ Pop out as node** whenever you want a separate
  node, and **⊟ Compact view** on all canvas nodes). In *Your setup*, any widget
  from any node in the graph (such as LoRA strength or sampler steps) can be
  pinned via right-click.
- **Inline custom presets & Studio preset pack manager.** Every extendable
  dropdown now includes **+ Custom entry …** at the bottom to add your own
  hairstyles, clothing, props, poses, moods, lighting setups, looks and
  locations live without restarting ComfyUI (and `×` to remove custom entries).
  Under *Studio → Your setup*, a new **Custom presets** section lets you load or
  paste `.json` preset packs (`ComfyUI/user/krea2_presets/`) and copy a ready-made
  **LLM prompt** so ChatGPT or Claude can generate custom packs on request.
  Shared workflows carry the prompts of active custom entries automatically.
- **Lightbox, Draft mode, Next Round & live queue control.** Open the **Lightbox**
  in ComfyUI's bottom panel (or fullscreen) to browse, filter, compare side by
  side (`C`), star favourites (`F`) and mark rejects (`X`). **Draft** renders
  a fast base pass first so **Finish favourites** can upscale only your keepers;
  **Next round →** plans a follow-up series drawn exclusively from your starred
  photos. Unshot frames can be queued individually via **▶ Shoot photo**, and
  a live progress bar with **⏹ Stop** lets you interrupt renders and clear the
  queue from the panel.
- **Director & shareable shoot files.** Describe an idea in one sentence (or
  attach a reference photo in a vision chat) and let any chat LLM — or the
  built-in offline draft — assemble a complete shoot from the render-tested
  presets. Whole shoots (Person, Wardrobe, builders, Series, Location sets and
  template) can be saved, loaded and shared as a single `.json` file.
- **Location node (set builder) & Series set/light axes.** The new
  `Photoshoot – Location` node manages multiple sets as tabs (place, time of
  day, weather, season and scene text). In the Series node, the **Set** and
  **Light** axes rotate sets and automatically match indoor/outdoor lighting or
  a time-of-day arc across the shoot.
- **Selfie mode, camera angles, gaze control, Anchor set recipe & handheld props.**
  Added a **Perspective** axis and *Selfie* recipe (four render-tested selfie
  angles and smartphone look), a **Camera angle** axis with framing-matched focal
  lengths (35mm–135mm), a 1-click **Anchor set** recipe (replacing the separate
  `photoshoot-anchor-set.json` template alongside thumbnails for all three
  shipped workflows and two preset outfits), series-wide **Gaze** modes (*at the
  camera*, *mostly camera*, *away*, *mixed*), six new postures and four new moods,
  plus handheld **Props** in Wardrobe and Pose with automatic grip phrasing and
  1-click custom preset saving.

### Changed

- **Unified styled dropdowns with floating two-column preview popovers.**
  Replaced native `<select>` boxes and inline thumbnail grids across all builder
  panels with a consistent, calm row layout. Dropdowns open as floating popovers
  without shifting the panel below, showing a two-column split view (preview
  image and prompt wording on the left, searchable list with favourites on the
  right) whenever thumbnails are available.
- **Full Ctrl+Z / Ctrl+Y undo integration & 1-click auto-wiring.** Panel edits
  and *Start shooting* now record cleanly as single undo steps, and missing
  Wardrobe, Location or Series connections offer inline **+ Create & wire** and
  **⚡ Connect** buttons.

## [2.8.0] — 2026-11-17

### Added

- **All-in-One Studio mode on `Photoshoot – Series` & new
  `photoshoot-studio.json` workflow.** `Krea2Photoshooting` gains a `prompt`
  output at the end (emitting the assembled prompt with embedded Person,
  Wardrobe, Location, Scene, Lighting, Style and Prompt template states from
  the node), plus `ui.text` history reporting so single-node Studio graphs
  populate the contact sheet and render Outfit previews without `Build Prompt`
  or separate canvas boxes. Each Studio section can still be popped out onto
  the canvas as a standalone node via **↗ Pop out as node**.

### Changed

- **Slimmer legacy compact nodes on the canvas.** Removed the redundant
  `Photoshoot | SECTION` brand strip inside the collapsed compact views of
  Person, Wardrobe, Location, Lighting, Style, Pose and Expression nodes, placing
  **edit →** and **⊞** cleanly with the tabs or action bar; bumped `.mjs`
  cache-busting query strings to `2.8.0`.

## [2.7.3] — 2026-11-17

### Changed

- **Cleaner Person-to-Wardrobe transition in Studio & Person Builder.** Removed
  the **Full / Close / Figure / Wide** preview filter bar and word counter from
  the Person node, and hid the redundant `Clothes: Wardrobe · ...` status line
  inside the Studio sidebar when a Wardrobe is already wired (keeping `+ Add
  Wardrobe` when none is connected); bumped `.mjs` cache-busting query strings
  to `2.7.3`.

## [2.7.2] — 2026-11-17

### Added

- **Live GPU progress & queue stop in Series and Lightbox.** Highlights the
  currently rendering frame in the contact sheet, compact strip and Lightbox
  filmstrip, shows live queue counts (`Rendering photo N · M left in queue`),
  and adds a **⏹ Stop** button to clear the queue and interrupt the current
  run directly from the panel.
- **Single-photo shooting for unshot frames.** Unshot frames in the contact
  sheet and Lightbox show **▶ Shoot photo** and queue Take 1 directly without
  incrementing the take counter.
- **1-click auto-wiring & node creation.** Missing `person_data`, `scene`, and
  `lighting` links in Series warnings get inline **⚡ Connect** buttons; the
  Person node, Series axes and Studio sidebar offer **+ Add Wardrobe**,
  **+ Add Location**, and **+ Create & wire** to spawn and connect missing nodes.
- **Wardrobe & Location tab reordering & interactive Series rail.** Added `‹`/`›`
  buttons to reorder Wardrobe outfits and Location sets; clicking outfit cards
  in the Series toggles `outfitAuswahl` directly, and `✎` buttons jump straight
  to editing that outfit or set.
- **Saved block presets & Build Prompt placeholder inspector.** Person, Lighting
  and Style panels now save and load presets live (`/krea2/bausteine`) with
  full builder state alongside text for legacy Load nodes. `Build Prompt`
  displays wired/matched placeholder chips, warns on mismatches, and offers a
  1-click **Default template** button.
- **Resolved dice preview.** Builder panels with active dice display the
  seed-resolved English sentence via `/krea2/vorschau` plus a **↻ Re-roll**
  button.

## [2.7.1] — 2026-11-17

### Added

- **Wardrobe & Studio ergonomics for props and series poses.** Added handheld
  props (`prop` dropdown with the render-tested presets and `propText` custom
  free-text field using the grip templates) directly under **Accessories** in
  the **Wardrobe**, alongside jewellery, eyewear and headwear, with Series
  coupling so tight close-ups, back views, selfies and incompatible postures
  drop props cleanly and Outfit previews remain unaffected. Also added a direct
  jump button on the Studio sidebar's *Pose* tab to the *Shoot* tab when no
  standalone Pose or Expression node is wired.

### Changed

- **No duplicate sunglasses in hand props.** Removed *Sonnenbrille* from the
  *Pose* node's arm prop list since sunglasses already live in Wardrobe
  eyewear; bumped `.mjs` cache-busting query strings to `2.7.1`.

## [2.7.0] — 2026-11-17

### Added

- **Selfie mode: a perspective axis in the Series, the render-tested
  wordings only.** A new axis row *Perspective* (off until switched on, so
  every series from before is unchanged) appends the camera angle to the
  framing's wording, exactly as the wording lab rendered it: *Selfie from
  above*, *Eye-level selfie*, *Selfie lying down* and *Mirror selfie*,
  rendered on 2026-09-30 (three seeds, against the bare word) and adopted by
  the user. *From above* came out only slightly above eye level and was
  adopted as it is. A selfie keeps a hand free for the phone (arm positions
  one hand at the face, in the hair or the new peace sign; postures that need
  both hands drop out), faces the camera (no back view, no profile), gets
  9:16 or 4:5; lying down lies on its back, the mirror selfie stands, is the
  only full-body one and looks at the screen, not the lens; close-up to
  medium shot for the others. New entries, appended: the mood *Blowing a
  kiss* in a new *selfie* family, the arm position *Peace sign*, and the
  Style genre *Smartphone / social*, which clears the lens when chosen (its
  wording carries its own). They join a series only on selfie photos and a
  die only when asked, so no existing series or seed changes. A recipe
  *Selfie* sets it up (four framings in turn, all four perspectives,
  friendly moods, gaze mostly into the camera, focus off). The contact sheet,
  Lightbox, compact view, Studio sidebar, caption, next round, saved series,
  shoot files (`"perspectives"`, switch `"perspective"`) and the Director
  know it. Not adopted and in round 2 of the lab: selfie from below, over the
  shoulder, pout, tongue out, eye roll.
- **Location node: the set as a builder.** *Photoshoot – Location* composes
  where the photo is taken - place (families studio, urban, nature,
  interior), time of day, weather, season and free text - in the panel the
  other builders share, with its compact view and a place in the Studio
  sidebar's *Look* tab. A node holds several **sets as tabs** (+, duplicate,
  delete, a name each), like the Wardrobe holds outfits; `szene` is the open
  set for Build Prompt, `ort_data` carries every set to the Series. The
  family says indoors or outdoors, from the place or, for a set written as
  free text, from its family chip: weather and season only apply outdoors.
  The lists hold only render-tested wordings - so far the example workflow's
  loft, as *Sunlit loft* - and the empty ones say *awaiting render test*;
  until the candidates pass, a set is its free text, a saved scene (chips
  under *Details*, from *Save Scene*, route `/krea2/szenen`) or a custom entry
  (builder `location`, also in the LLM prompt and the template export).
  Shoot files carry the node's sets (section `location`). 22 nodes.
- **Series: set and light axes.** The **Set** axis changes the Location
  node's sets over the series, in blocks (*loft → street → café*, the framing
  order starting over with each set, as with outfits) or mixed; close-up and
  portrait get the set's short form - the first clause of each part, what is
  behind the head - and the extreme close-up none. The **Light** axis, off
  until switched on, picks one of the 30 render-tested lighting setups per
  set, over the series as a time of day (morning, midday, golden hour, blue
  hour, night) or mixed, narrowed to lighting families if wanted - and fits
  it to the set: sun, sky and moon only outdoors, studio and window light only
  indoors. Both leave on new outputs **`szene`** and **`licht`**, appended
  after `foto`, and have steps of their own in the counting: without a
  Location node and with the light off, every output and every prompt stays
  byte for byte what it was (checked on the example workflows in ComfyUI).
  The contact sheet marks the sets with a stripe and names set and light per
  photo; the panel warns while an axis is on and its output leads nowhere.
  The caption appends set and light where they vary.
- **Wording lab: 97 location candidates.** `tools/wortlabor/orte.json`
  holds the Location node's wordings for the render test: four places per
  family (two candidates each against the bare word, the loft as the
  reference row), time of day, weather and season composed with a place by
  the node's own `compose_location()`, and a group for the close framings'
  short form. The lab gained `scene` and `lighting` slots and `zusatz.texte`.
  Nothing of it is a preset until the sheets are judged; the smoke test holds
  the Location node's lists to the tested wordings.

- **Compact nodes.** Every Photoshoot panel has a short view: **⊟** in its
  brand strip makes it compact, **⊞** full again. The compact Series keeps
  its brand strip, *Start shooting* (with its progress), *Draft*, *Finish
  favourites* and *⤢ Lightbox*, one line of what the axes do (the texts the
  axis rows show) and a strip of the current page's photos - pictures,
  dashed frames for planned ones, ♥ and ✕ - where a click opens the Lightbox
  at that photo. The Person shows her section summaries with *Inspire Me*,
  the Wardrobe its outfit tabs and the open outfit, the Pose, Expression,
  Lighting and Style builders one line per field that is set. A click on a
  summary or *edit →* opens the Studio sidebar on the node's tab for its
  series; without a sidebar, or for a node wired to no series, the node
  expands inline instead. The view is stored per node as a display-only
  property (`photoshootAnsicht`), never in the state that reaches Python, so
  the prompt is the same either way; switching is one undo step. New nodes
  start compact, workflows saved before open full, the example workflows
  ship compact. The commands *Photoshoot: Compact all* and *Photoshoot:
  Expand all* switch the whole graph. In the full view, the contact sheet
  now keeps to two rows with *+N · all in the Lightbox*; the Lightbox pages
  through the rest (pages of 24 stay where the Lightbox cannot open).
- **Wording lab: the render test as one command.** `tools/wortlabor.py`
  (developer tool, not in the registry package) reads a candidate file
  (`tools/wortlabor/*.json`), builds the prompt each candidate wording would
  get in a series - the example workflow's person, scene, lighting, style and
  template through the real builders and Build Prompt, the candidate in its
  slot - and queues one render per candidate and seed on a running ComfyUI,
  using the example's own render graph. `--bogen` then writes one comparison
  sheet per group: candidates as rows, seeds as columns, the bare-word control
  marked. `--nur-zeigen` prints the prompts without queueing. First file:
  `selfie.json`, 28 selfie wordings in three groups (perspective, selfie
  expressions, smartphone look) for the planned selfie mode; nothing of it is
  a preset until the renders are judged.
- **Shoot files: the whole shoot in one JSON.** A new row *Shoot:* in the
  Series panel saves the person, the Wardrobe's outfits, the Pose, Expression,
  Lighting and Style builders, the Series (start number, series seed, pools,
  framings, takes), the scene text and the Build Prompt template under a name
  (`ComfyUI/user/krea2_shoots/`), downloads it as a file to share and opens
  one. Loading shows what goes into which node first - the nodes wired to that
  Series, or the only one of a type - with *Apply* and *Undo*. Each section is
  the node's state verbatim, so a round trip gives back the same properties;
  every label is checked against the lists (English names work too), unknown
  ones are listed and left out, and custom entries travel as prompt copies so
  the file renders without your JSON. Format `photoshoot-shoot/1`, routes under
  `/krea2/shoots`, a commented example in `docs/shoot_example.json`. The
  Person's *Reference*, the Series' rounds, rejects and outfit subset, *Draft*
  and the file name folder travel with a saved shoot; the Director leaves
  them to the nodes (a reference it drops with a note).

- **Director: one sentence becomes a whole shoot, through any chat LLM.**
  *Director …* in the Series panel builds a prompt from the live lists
  (`/krea2/director/llm_prompt`) - every built-in label per field and family,
  the shoot-file format with a worked example, recipes, framings, mood arcs,
  and what the render tests found (at most five face fields, one to four
  outfits). Paste it into ChatGPT, Claude, Gemini or a local model, paste the
  answer back, check the preview, apply. The LLM only chooses: the import takes
  built-in labels only, no free text but the scene, nothing below 18, so every
  wording that reaches the prompt is a render-tested one. A second mode
  reverse-engineers a reference photo in a vision chat into the same file - the
  photo stays in the chat, only labels come back. Without an LLM, an offline
  draft matches the brief's words against the English labels. The person
  keeps its LoRA trigger and reference: the Director chooses the look of the
  shoot, not who is in it.

- **Six postures and four moods, render-tested.** *Stretching*, *Turning
  mid-motion*, *Sitting sideways on the floor*, *On the stomach, chin in the
  hands*, *Cross-legged* and *Sitting on the heels* (24 postures now), and the
  moods *Confused*, *Inviting*, *Smitten* and *Determined* (94 moods). Each was
  rendered with three seeds through a real series and kept only on the user's
  verdict; of eight mood candidates, four looked too alike and stayed out.
  Where a posture already says the arms, legs or back (stretching: arms
  overhead; on the stomach: forearms and crossed ankles; the two floor
  postures: back straight), the coupling tables leave only what agrees with
  it. Appended at the end,
  so the posters keep their order; the poses poster does not show them yet.

- **Series: gaze modes.** A series can now set how the eyes go through the
  whole shoot (`state["blick"]`): *kamera* (every photo looks into the
  camera), *meist_kamera* (two in three), *abgewandt* (nobody does) or
  *gemischt* (as before). Until now gaze was drawn from all nine values on
  every photo, so eye contact came one photo in nine. A photo that looks into
  the camera no longer draws a mood that looks away (thoughtful, absent, shy,
  embarrassed) or a back view (it drops every face field, the gaze with it),
  and a torso turned over the shoulder no longer gets "over the shoulder"
  twice. Without a mode the plan is unchanged. The panel offers them as a
  chip row under Expression (*mixed / at the camera / mostly camera / away*,
  names from `BLICK_NAMEN`), the axis row names the mode, saved series keep
  it, and the contact sheet plans it from the same tables (`/krea2/presets`),
  so a series with a gaze mode previews what it renders. *Mixed* counts as
  the same plan as no mode, so older runs stay in the sheet.

- **Series: selects → next round.** Star the photos that work and press
  *Next round →* under the contact sheet: the next series starts right after
  this one and draws only from the favourites' framings, posture and mood
  families, focus areas and, with a wardrobe, outfits. An optional *✕ Reject*
  in the detail box drops what only rejected photos show. *Round 2 · based on
  3 selects* with *← back to round 1* keeps the last five rounds in the state
  (`runden`), with their favourites and takes. Computed once, in Python
  (`naechste_runde()` in `shooting.py`, route `/krea2/serien/naechste_runde`);
  a pose or mood pool can now hold several families as a list, and
  `outfitAuswahl` limits the outfit axis to a subset of the wardrobe. Both
  planners know both, and the parity test covers them; states without them
  plan exactly as before.

- **Tests: the series preview against Python.** `node tests/plan.mjs` spawns
  `tests/plan_fixture.py` for what `shooting.py` plans - a few hundred states
  (every recipe, order, mood arc, family pool, switched-off axis, outfits in
  blocks and mixed, gaze mode, large photo numbers) times 40 runs - and holds
  the JS planner of the contact sheet to it field by field: framing, focus,
  every pose and expression field, ratio, size and outfit. The expected values
  come from the current code on every run, so they cannot go stale.

- **Panels: undo.** Every edit in a panel (Person, Wardrobe, the builders,
  the Series) is now one step for Ctrl+Z / Ctrl+Y. ComfyUI's change tracker
  compares the graph on mouseup, before a panel click has changed anything,
  so an edit was only recorded with the next click and one Ctrl+Z took back
  two edits. `schreibeState()` now records right after writing
  (`captureCanvasState()`); undo reloads the graph, so the panels redraw from
  their properties. *Start shooting* is one step, not one per photo. Checked
  in the front end (1.47.10), classic canvas and Nodes 2.0.

- **Series: the prompt of every photo.** The detail box of the contact sheet
  shows the prompt the photo got, with a *Copy* button. *Build Prompt* hands
  its text to ComfyUI's history as `ui` output (ComfyUI keeps it for every
  node that runs, output node or not); the sheet reads it from the same
  history entry as the picture. After a restart of ComfyUI the pictures come
  back from the workflow, the prompt does not, and the row says so.

- **Series: the contact sheet pages.** It stopped at 24 frames with a "+16"
  nobody could click, so the README's 40-photo series could not be reviewed,
  favourited or re-shot past photo 24. It now pages 24 at a time (‹ 25–48 of
  60 ›), and *+N ›* goes to the next page.

- **Series: the Lightbox.** The contact sheet big, in ComfyUI's bottom panel
  next to *Logs*: *⤢ Lightbox* in the contact sheet's head row, a
  double-click on a frame (opens at that photo) or the command *Photoshoot:
  Open Lightbox*. One photo at a time at full size, with filters (all,
  favourites, rejects, drafts, one chip per framing with counts), the
  framing, pose, mood, outfit, take, size, file and prompt beside it, and a
  filmstrip of the whole series with the planned frames dashed. *♥ Favourite*
  (F), *✕ Reject* (X), *⇆ Compare* (C: the photo next to the next one; a click
  on either stars it), *↻ Re-shoot*, *✓ Finish* for a draft, take chips to
  choose the take, and *Next round →* in the footer; ← → browse and a swipe
  does the same on a touch screen. Keys count only while the Lightbox has the
  focus, so the canvas and text fields keep theirs. The stage follows the
  panel's height; *⤢ Fullscreen* opens the same view as an overlay (Esc
  closes it), which is also what a front end without the bottom panel gets.
  With several Series nodes a select picks which one. The Lightbox has no
  plan or pictures of its own: the node hands it its photos and actions, the
  contact sheet uses the same ones, so both show the same thing, each redraws
  when the other changes something, and Ctrl+Z covers both. Tested in a
  CPU-only ComfyUI on front ends 1.47.10 and 1.53.6.

- **Studio sidebar: the whole shoot in one column.** *Studio* (the camera
  icon in ComfyUI's left icon bar) opens the shoot over the full height, with
  the tabs *Person* (Person and Wardrobe), *Look* (Lighting and Style), *Pose*
  (Pose and Expression), *Shoot* (the Series panel with *Start shooting*,
  *Draft* and the axes; *⤢ Open Lightbox* in place of the contact sheet) and
  *Director* (the Director inline, and the shoot files row). It works on the
  selected Series (a select when there are several) and the nodes wired to
  it, the same ones a shoot file goes to; a missing one is named. Every
  section is the node's own panel, drawn by the same code on the same state -
  pick something in the sidebar and the canvas panel follows, and the other
  way round, one step for Ctrl+Z either way; a series started in one counts
  in the other. **Your setup** holds widgets of any node in the graph:
  right-click a node → *Pin to Photoshoot Studio* → the widget, and it shows
  as a control of its kind (list, number, switch, text), labelled
  with node and widget name - a LoRA loader's file and strength, steps, a
  sampler. The pins are saved in the workflow and undone with it; a deleted
  node stays listed as *node removed* until unpinned. Tested in a CPU-only
  ComfyUI on front ends 1.47.10 and 1.53.6, with and without Nodes 2.0.

- **Lighting setups and postures as picture tiles.** The 30 lighting setups
  and the 18 postures of the pose poster open as tiles with their picture,
  on the canvas panels and in the sidebar: the same person under every light
  and in every posture, cut from the reference posters
  (`tools/schneide_vorschau.py`, into `js/vorschau/licht/` and
  `js/vorschau/haltung/`). Postures added after the poster and custom
  entries stay chips under the tiles; the search filters both. These
  thumbnails are optional per entry, unlike the Wardrobe's.

- **Empty and error states.** When `/krea2/presets` cannot be reached, a
  panel shows one line with *Retry* instead of an empty node (one Retry
  brings back every waiting node). An empty Person says where to begin; a
  Series whose `person_data` is not wired says so; and when an axis change
  empties the contact sheet, a line says the earlier pictures are kept and
  come back when the setting does.

- **Series: Draft, then Finish favourites.** A *Draft* switch under *Start
  shooting* sends the new `refine` output off, so the render node skips its
  upscale and second pass - about half the time, base resolution. Star the
  keepers in the contact sheet and *Finish favourites* queues just those
  photo numbers, each at the take the sheet shows for it, with draft off:
  same seed, same composition, full resolution. The draft flag and take go
  into those runs only (a per-run override in the `graphToPrompt` hook), so
  the panel stays on draft and undo and the saved state are untouched; the
  counter is put back as after a re-shoot. The contact sheet records per
  picture whether it was a draft (dashed frame), shows the finished take as
  soon as there is one, and keeps `entwurf` out of the plan comparison, so
  draft and final of photo 7 share a frame. Both buttons are greyed out,
  with a tooltip saying what to wire, while `refine` has no link. Tested in
  a CPU-only ComfyUI with the render swapped for an empty image: three
  drafts, two favourites finished, the counter back at 4.

- **Series: file names that say which photo it is.** The new `dateiname`
  output (*filename*) goes into Save Image's `filename_prefix`:
  `photoshoot/s0001/07_t1_00001_.png` is photo 7, take 1 of the series that
  starts at 1, and a draft of it ends in `_draft`. The folder is the start
  number, so a series keeps its folder through re-shoots and finishes; the
  anchor set writes to `photoshoot/anchor/s0001/`. Old workflows keep their
  static prefix until the output is wired.

- **Person: reference mode (needs render test).** A *Reference* field under
  Basics, right below the LoRA trigger. Type the numbers of the reference
  images (`1`, `1, 2`) and the person block starts with
  `the same woman as in <image1> and <image2>` - Qwen-Image-2.1's tags for
  its reference images, the noun from the gender - instead of `a woman`, and
  leaves face, hair, skin and make-up out as a trigger does (`LORA_WEG`). Age,
  body and outfit stay. Anything but numbers is written as typed. The panel
  preview writes the same text (wording served by `/krea2/presets`), and the
  sections the picture takes over say *via the reference image*. The wording
  is new and **not render-tested yet**.

- **Series: `caption` and `foto` outputs** (appended after `refine` and `dateiname`,
  so saved workflows keep their links). `caption` is the training caption for a
  character LoRA: the trigger, the subject, then only what varies - the
  framing's head wording and focus, pose, expression, the outfit as far as
  the framing shows it. No identity field, age, body or reference phrase ever
  reaches it; the smoke test holds that over 240 photos. `foto` is the photo
  number of the run. The caption is assembled from existing, render-tested
  wordings; no new prompt text.

- **Photoshoot – Save Dataset** (`Krea2DatasetSave`, the 21st node). Writes
  each photo as `output/photoshoot/dataset/<name>/NNNN.png` with its caption
  in `NNNN.txt`, NNNN being the photo number, so a re-shoot replaces its pair.
  An optional *trigger* goes in front of captions that lack one. Tested by
  executing it in ComfyUI (CPU) and on a synthetic tensor.

- **Example workflow: reference series with Qwen-Image-2.1 (needs render
  test).** `example_workflows/photoshoot-reference-qwen21.json`, built by
  `python3 tools/baue_workflow.py --referenz`: two anchor images (face crop as
  image 1, full body as image 2) into `TextEncodeQwenImage21`, the Person node
  in reference mode, Series, Build Prompt, KSampler at the settings of
  ComfyUI's own Qwen-Image-2.1 template (25 steps, CFG 1, euler), the
  Comfy-Org model files with their download links (bf16 model, int8 text
  encoder: 24 GB), a bypassed slot for a turbo LoRA, and a bypassed Save
  Dataset branch. `dateiname` names the files (`photoshoot/reference/...`);
  `refine` stays unwired, there is no second pass, so Draft is greyed out
  there. The latent comes from the encoder, sized to image 1, so the
  ratio axis is off; a switch tries the series' own size instead. Core nodes
  only, needs a ComfyUI with Qwen-Image-2.1 support. Checked offline like
  the Krea workflows, against a snapshot of its own
  (`tools/object_info.qwen21.json`, `--snapshot --referenz`), and against
  ComfyUI master: every node type, input and link valid, and the Photoshoot part
  executes. Qwen-Image-2.1 is non-commercial (Qwen Research License); the
  README names Krea 2 Identity Edit as the route for commercial work.

- **Example workflow: a LoRA slot.** The series workflow now carries a
  `LoraLoaderModelOnly` between the Krea 2 model and the render node, shipped
  bypassed like the one in the anchor set: pick a file, press Ctrl+B, put the
  trigger into *LoRA trigger* or the template. The README says how, and how to
  chain several. Every link the workflow shipped with keeps its id; the anchor
  set is unchanged.

### Changed

- **Maintenance & robustness checks:** `tests/smoke.py` now also runs
  `tools/baue_locales.py --pruefen`, `tools/setze_js_version.py --pruefen`, and
  `tools/schneide_vorschau.py --pruefen` offline, while `tools/sync_tor.sh` wakes
  `tor` if needed and runs the PyTorch smoke tests (`Krea2Monochrome`,
  `Krea2DatasetSave`) against the server venv. `nodes/regie.py` and
  `nodes/shoot_datei.py` accept English gaze modes and the 2.7 light/set axes;
  `js/studio.mjs` normalises pin node IDs and inspects the active canvas graph,
  and `js/lightbox.mjs` keeps action feedback visible in compare mode.
- **Series: the full view is 890 px tall for new nodes** (the example
  workflows' 1090): three more axis rows (set, light, perspective) and two
  more outputs. Saved workflows keep their size; the axis list scrolls there
  as before.
- **Saved series keep the gaze mode** and the set and light settings: the
  panel sent `blick` along, but the store dropped it.
- **Wording lab: sheets a phone can read, per pass, where the docs say.**
  `tools/wortlabor.py` splits a group into sheets of at most six candidate
  rows (`bogen_A1_…`, `--zeilen`), keeping one label's candidates together
  and repeating a group-wide control on every sheet (a group that fits on
  one sheet keeps the file's order) - an 18-row sheet came out 272×2000 on a
  phone. Sheet names carry the pass (`bogen_A_pass1.png`,
  `bogen_A_refine.png`) and refine renders their own prefix, so `--refine`
  no longer overwrites the first pass. `--einzeln` also saves every render as
  a 1000 px JPG. Sheets now always go to `tests/_tmp/wortlabor/<file>/` (or
  `--ziel`), also with `--ausgabe`, as documented, and the tool prints the
  full path. A camera slot can name an adopted perspective
  (`{"preset": "perspektive/…"}`). Round 2 of the selfie candidates:
  `tools/wortlabor/selfie2.json`.

- **Example workflows: rendering is one node.** The seven render nodes
  (conditioning, latent, both sampler passes, decode) now sit in a subgraph,
  *Render (2 passes)*; double-click it to see or change the inside. On the
  canvas it shows only what the series feeds it and a **refine** switch: off,
  a lazy switch hands pass 1 straight to the decode, so drafting no longer
  means bypassing two nodes with Ctrl+B. The render and output frames are
  one, the loaders stay on the canvas, and each carries its Comfy-Org download
  link, so ComfyUI offers the download when a model file is missing. Tested
  in the front end: refine off renders 1328 px, on 1992 px; the Series node
  stays on the canvas, so its state and the contact sheet are unaffected.

- **Series: Start shooting counts and cannot double-queue.** It queues photo
  by photo, shows *queued 12/40* on the button and is disabled meanwhile, so
  a double click no longer queues the series twice. When ComfyUI refuses a
  photo (a missing model, a node error) queueing stops there and a line in
  the panel names the photo, next to ComfyUI's own error dialog. *Re-shoot*
  and *Finish favourites* queue the same way.

- **Example workflows: the series drives refine and the file name.** Both
  workflows wire the Series node's new `refine` output into the render
  node's refine input and `filename` into Save Image; the notes point to
  *Draft* and *Finish favourites* instead of the refine switch. Appended
  outputs only - workflows saved before keep every link.

- **Example workflows: SaveImage fallback prefix per day.** The default
  `filename_prefix` on `SaveImage` in `photoshoot-series.json` and
  `photoshoot-anchor-set.json` now uses `photoshoot/%date:yyyy-MM-dd%/series`
  and `photoshoot/%date:yyyy-MM-dd%/anchor`, keeping per-day numbering tidy
  when an older day's folder is cleared.

### Fixed

- **Person: glossy pantyhose renders reliably in more poses.** *Strumpfhose
  glänzend* now emits `"glossy sheer pantyhose that catches the light"`
  instead of `"shiny glossy pantyhose"`: in squatting poses where the old
  wording rendered bare legs (0/6), the new wording recovered it to 6/6
  across the same seeds.

- **Mixed outfits marched in step with the framing.** With outfits drawn per
  photo (*mixed* order) the outfit draw shared the camera's step size: the
  list of step primes had sixteen entries and the outfit sits in slot 16,
  which wrapped around to slot 0, the camera's. With two outfits, the first
  only ever got the close framings and the second only the wide ones. The
  list now has 32 primes, so every draw has a step of its own; the first
  sixteen keep their places, so every other value of every existing series is
  unchanged - only which outfit a photo wears in mixed order moves. The smoke
  test checks that no slot in use wraps and that every outfit gets both close
  and wide framings.

- **The contact sheet showed the wrong placement.** The panel's planner
  filtered the placement by the framing only, while `plane()` also filters it
  by the base posture - so about one photo in four showed a different
  placement in the detail box ("in the doorway") than the one rendered ("by
  the window"). It now intersects both, as Python does; found by the new
  parity test. Two smaller gaps closed with it: from photo 2^21 or so the
  preview's draw lost precision (the product of run and step passed 2^53 and
  now goes through BigInt), and an axis switch missing from the state counted
  as off in the preview but as on in Python.

- **Inspire Me left most fields empty and wiped the LoRA trigger.** About 60
  of the labels in its pools (in `js/person.mjs`) were not presets - "Kühles
  Porzellan", "Tiefbraun", "Kurzer Bob", "Soft Tint" - and a label that is not
  a preset leaves its field empty, so a roll left a good part of the person
  blank: the complexion nearly always, hair, eyes and make-up often. The pools are now `INSPIRATION` in
  `person_builder.py`, built from existing labels only and delivered through
  `/krea2/presets`; the smoke test fails on a label that is not a preset. It
  keeps the LoRA trigger, the free details and older clothing, and with more
  than three fields set it asks before replacing them (*Replace 17 fields?*).

- **Person: a section said *nothing set* next to a count.** When every field
  set in a section comes from the LoRA trigger or the reference image, but
  the section also has fields that do not (make-up with only the lips set),
  its row said *nothing set* while counting two; it now says *via the LoRA*
  or *via the reference image*.

- **Panels left listeners behind.** The Series' history listeners and the
  Person panel's click-outside listener were never removed; since undo and
  every workflow load rebuild all nodes, each left a set behind. They now go
  with the node (`node.onRemoved`).

- **Tools: the workflow generator runs offline.** `tools/baue_workflow.py`
  crashed without a running ComfyUI (an IndexError while wiring). It now
  takes the kit's signatures from its classes and ComfyUI's from
  `tools/object_info.core.json`, a snapshot of the thirteen core nodes it
  uses (ComfyUI 0.28.0; `--snapshot` refreshes it from a running server).
  Regenerating reproduced the shipped workflows byte for byte, and the smoke
  test now holds them to that (`--pruefen`).

## [2.6.0] — 2026-09-21

### Added

- **Wardrobe: costume changes within a series.** The new *Photoshoot –
  Wardrobe* node holds the outfits of a shoot as tabs - each with clothing,
  accessories and a name, added, duplicated and deleted in the node. Wire it
  into the Person node's new `wardrobe` input: the person wears the open tab,
  and the Series node changes through all of them, in blocks (twelve photos,
  three outfits: four each) or mixed. In blocks, framings in turn and
  wide-to-close start over with every outfit, so each is shot wide and close
  instead of one getting all the close-ups. The outfit replaces all of the
  person's clothing, so nothing of one outfit survives into the next. In the
  Series node the *Outfit* axis shows the outfits as a rail of cards with
  colour swatches, and a stripe in each outfit's colour runs under its frames
  in the contact sheet. *Render preview* (one outfit, in the Wardrobe node)
  and *Render outfits* (all, in the Series node) show an outfit on a faceless
  mannequin or as a flat lay, in a fixed studio look, through one run of your
  own workflow per outfit. Render-tested: eight kinds of legwear, accessories
  and all-black outfits in the previews; a 12-photo series in three outfits
  kept the same face throughout (a bikini moves the face more than other
  outfits do).

- **Searchable lists.** In the Person and Wardrobe nodes every list longer
  than twelve entries (shoes, tops, bottoms, headwear, hair, ...) opens under
  its row: type to filter - by the German or English name, the prompt text or
  the family, so "veil" finds the pillbox - star favourites, and the five most
  recently used sit on top. For tops, bottoms, shoes, hairstyles and headwear
  a picture of the entry under the pointer sits above the list, so you can
  see what a milkmaid top or a cloche is before you pick it: clothes, shoes
  and hats alone on the Wardrobe's neutral mannequin in its studio look
  (shoes as a close-up from a three-quarter angle, so heel and profile show),
  hairstyles on the README person. Barefoot, socks, stockings and perspex
  pumps do not show on a mannequin; theirs are feet close-ups from the shoe
  poster. Enter takes the
  first hit, Escape closes. The
  Pose, Expression, Lighting and Style panels get the same search over their
  long chip lists (90 moods, 30 light setups) plus a row of recent ones.
  Favourites and recent entries stay in your browser, not in the workflow.

- **Custom entries.** Your own hats, cuts, light setups, looks and so on, from
  JSON files in `ComfyUI/user/krea2_presets/`: per entry the field, a label
  and the English prompt text, optionally a family and a colour swatch. They
  appear in the lists of every builder and the Wardrobe, in their family or
  under *Custom*. A workflow carries the prompt of each custom entry it uses,
  so it renders the same on a machine without the file. They are never rolled
  unless the file says `"dice": true`, so every seed keeps its result.
  - A broken file or entry is skipped with a message, and a file with
    problems shows as one line in every Photoshoot panel, linking to the
    messages. Age and gender cannot be extended, and an entry may not repeat
    a built-in one, under its German or English name.
  - On the first start the folder is created with a commented example,
    `example.json.txt` (one entry per case; also in
    `docs/custom_entries_example.json`).
  - `/krea2/custom/template` shows every built-in entry in the same format.
  - `/krea2/custom/llm_prompt` is a ready prompt for any chat LLM to write
    such a file, built from the live presets: every field, its families,
    examples, the names already taken, and the wording rules from the render
    tests.

  See *Custom entries* in [docs/nodes.md](docs/nodes.md#custom-entries).

- **Sixteen hats** in *Headwear*, which is now sorted into families (hats,
  caps & beanies, hair accessories & scarves, fetish): cloche, bucket hat, top
  hat, newsboy cap, pillbox with veil, fascinator, Panama, bowler, boater,
  floppy hat, cartwheel hat, sailor hat, white captain's hat, fisherman cap,
  trapper hat, visor. Cloche, bowler, floppy and sailor hat needed a more
  exact wording than the bare word.

- **Five ruffled skirts** in the skirts family: tiered ruffle, asymmetric
  ruffle, lace-up with petticoat, side bow, ruffled overskirt. A bustle skirt
  did not make it - it rendered as another tiered mini.

- **Tops & blouses** as a second top family: peplum, corset, milkmaid,
  bustier, Bardot, eyelet wrap blouse and nine necklines (plunging V,
  sweetheart, keyhole, sleeveless turtleneck, cowl, lace-up, boat-neck cutout,
  zip-up high collar, illusion yoke).

- **Bikini** families for top (11 cuts, tankini included) and bottom (7 cuts).

- **Seven bangs hairstyles**: long with blunt bangs, side-swept, wispy, baby
  bangs, curly, bob with bangs, choppy.

- **Every new wording is render-tested** against the bare word on the poster
  person; what looked like the bare word stayed out (halter and push-up bikini
  tops, Brazilian and hipster bottoms, the bustle skirt).

- **Posters**: new [headwear](docs/POSTERS.md#headwear-matrix-29-hats-caps--accessories),
  [bikini](docs/POSTERS.md#bikini-matrix-11-tops-7-bottoms) and
  [bangs](docs/POSTERS.md#bangs-matrix-9-fringe-cuts) posters; the
  [tops poster](docs/POSTERS.md#tops-matrix-27-tops) shows all 27 tops and the
  [bottoms poster](docs/POSTERS.md#bottoms-matrix-34-skirts-shorts--trousers)
  all 34 bottoms, all on the README's person with her scene, light, style and
  seed. The headwear sheet also shows the entries that do not hold in a
  portrait (visor, leather cat mask, thin headband and hair band).

- **Quickstart.** `docs/quickstart.md` walks through a first shoot in six
  steps: install, load the example workflow, build and dress the person,
  draft a test sheet, shoot the series, pick from the contact sheet.

### Changed

- **Clothing moved from the Person Builder to the Wardrobe.** The person has
  five sections now (basics, body, head, face, make-up); what she wears comes
  from the Wardrobe on her `wardrobe` input, and *Inspire Me* no longer rolls
  shoes and a coat. Persons saved with clothing still render as before; the
  Person Builder lists those clothes with *Move to Wardrobe* and *remove*. The
  example workflows carry a Wardrobe with one outfit, the coat the example
  person wore before.
- **Long lists are no longer dropdowns.** In the Person and Wardrobe nodes a
  list of more than twelve entries opens as a searchable list under its row
  (see *Searchable lists*); short ones stay dropdowns. The saved value is the
  same label as before.
- **Pose, Expression, Lighting and Style look like the Person node.** One row
  per field - name, what is set, a die - and a *Details* row, all closed by
  default, one open at a time; the node grows with what is open. The long
  field opens into its families and variants, the short ones into chips
  instead of unlabelled dropdowns. The seed is hidden until a field is rolled.
- **The example workflows read left to right.** One long row of seven frames
  - Models, Who (person and wardrobe), Look, The shoot, Prompt, Render,
  Output - each with a short English note on top saying what the step is for
  and the one thing people get wrong there ("press Start shooting, not Queue",
  "keep `{style}` first", "Monochrome ships bypassed"). Every panel opens
  collapsed.
- **Every node says it is Photoshoot's.** Display names are now "Photoshoot –
  Person", "Photoshoot – Series", "Photoshoot – Style" and so on, and the
  example workflows no longer give the kit's nodes titles of their own
  ("lighting", "2 — the series"), which hid whose they were. Class names are
  unchanged, so saved workflows load as before.

### Fixed

- **Build Prompt without placeholders put the expression last.** The docs
  and the node's description promised the recommended order - style, then
  the expression, then framing, scene and lighting before the person - but
  a text without placeholders still got the expression at the end, where a
  mood did not show in the tests. It now follows that order; with
  placeholders nothing changes. The description recommended the old order too.
- **German text in the English interface** of the Save nodes: the field
  placeholders and the switch ("speichern"/"aus") are English now, as is the
  error for an unusable name.
- **Saved node sizes were lost on load.** Person, Series and the builder
  panels set their default size once the presets had arrived - after a loaded
  workflow had already restored its own - so every saved size snapped back to
  the default (and nodes spilled out of their group frames). The default is
  now only for new nodes.
- **Skirts pulled portraits wide.** Portraits, close-ups and detail shots
  still carried the whole outfit, and a "knee-length pencil skirt" or "pleated
  midi skirt" turned the portrait into a three-quarter or full-length shot on
  two seeds out of two. These framings now leave out what is below the chest
  line: bottom, hosiery, shoes, legs, hips, waist and belly. In the re-render
  all eight portraits (four outfits, two seeds) came out chest-up. Medium shots
  and wider are unchanged; portraits of a person with a bottom set change.

## [2.5.0] — 2026-09-18

### Added

- **Contact sheet in the Series node.** Every photo as a frame in its real
  aspect ratio, filled with the rendered picture from ComfyUI's history; a
  click shows framing, pose, focus and mood. Replaces the text preview whose
  lines ran out of the node.
- **Series recipes**: *Editorial*, *Lookbook* (full body and portrait in
  turn), *Headshots*, *Shoes* (standing, macro and full body) and *Test sheet*
  set all axes in one click, each checked in a test render; the matching recipe is lit, any
  change of your own shows *custom*.
- **LoRA trigger** in the Person Builder: with a character LoRA's trigger set,
  the person writes gender, age, trigger, body and clothing, and leaves face,
  hair, skin and make-up to the LoRA.
- **Moods as the subject**: with a mood arc the expression reads "a terrified
  woman screaming …" and the person joins it without its own "a woman" — the
  one form in which moods showed in the expression tests. The example
  workflows put `{expression}` right after `{style}`.
- **Dramaturgy**: order *wide → close* (the series opens wide and ends in the
  closest framing) next to *drawn* and *in turn*, and **mood arcs** —
  *Joy* (calm → laughing → triumphant), *Dominance* (confident → imperious, stern)
  and *Drama* (embarrassed → frightened → panicked → crying) — in four stages
  over the series, built only from moods that showed in render tests.
- **Saved series**: *+ Save* in the recipe row keeps the current settings
  under a name (`ComfyUI/user/krea2_series/`), shown next to the recipes and
  deleted with ×; start number and seed included, so it is that series again.
- **Coverage** (*each once, in turn*, under Camera): the chosen framings in
  order instead of drawn, so a short series cannot miss one.
- **Takes per photo** (1–4, under Noise): every planned photo is rendered
  several times with its own noise; the detail box shows the takes side by
  side and a click chooses one.
- The contact sheet **remembers its pictures** in the workflow, so it
  survives a ComfyUI restart (the history lives in memory only).
- **Favourites and re-shoots.** Mark photos in the contact sheet; *Re-shoot*
  renders just those again with the same plan and new noise. Each photo counts
  its takes, and the take goes into the seed (take 0 is the old seed, so
  existing series are unchanged).

### Fixed

- **Gestures pulled macros wide.** With a mood arc, the extreme close-up at the
  end of the series still carried the whole mood — "cheering with both fists
  raised in the air" — and four takes out of four came out as a full figure or
  a double exposure. A macro of the eyes or lips now gets the mood without
  gestures out of frame: its own face wording for triumphant, embarrassed,
  imperious and demanding, and the clauses with hands, arms and shoulders
  dropped from the rest.
- **Extreme close-ups in 16:9 came out as diptychs.** A face that wide filled
  the rest of the frame with a second, full-length figure of the same woman —
  two takes out of two in the README drama series. The extreme close-up now
  draws from 1:1, 3:2 and 4:5; the list keeps its length, so only the photos
  that had 16:9 change.
- **Close-ups came out as medium shots.** A close-up or portrait still carried
  the whole pose — "lying on the stomach, near a window, leaning on the
  forearms, legs stretched out" — and the figure won over the framing. Close
  framings now keep only the turn of the body and the arms. Same seed before
  and after: the portraits and close-ups of a mood arc come out close.

- The contact sheet could show a face focus for a photo whose body is turned
  away; Python leaves the face out there. The preview now applies the same
  rule — checked on 624 photos, preview and Python identical.

- **Macro detail shots showed the whole figure.** An extreme close-up of the
  feet, hands, eyes or lips still carried the full pose and expression
  ("lying on the stomach, near a window, looking back over the shoulder, one
  hand touching the face …"), which outvoted the macro. Now a macro keeps what
  is in frame: feet the base posture and legs, hands the arms, eyes and lips
  the expression only; for the feet, lying and reclining postures are dropped
  too. Found in the recipe test; same seed before and after, hands, eyes and
  feet come out close.

### Changed

- **Person Builder as a profile sheet (Steckbrief).** The six tabs are gone;
  the sections sit as rows, one open at a time, and a closed row shows how
  many fields are set and a short form of them — the whole person reads at a
  glance, and the truncated tab names ("Make-u…", "Clothin…") are gone. A
  brand strip with the Photoshoot mark heads the node.
- **Colour buttons.** Every colour field (skin tone, hair, eyes, eyeshadow,
  lips, nails, top, bottom, hosiery, shoes) is a button in the chosen colour
  next to its dropdown; the palette opens on click and works with the arrow
  keys. Greyed out where the prompt drops the colour (bare legs, no shoes).
- **Accessories** (jewellery, eyewear, headwear) are a section of their own;
  Clothing keeps the garments, each as a block, with the **material indented
  under the bottom**. When the cut names its own fabric, the material is
  struck through with a note, instead of silently missing from the prompt.
- **Families in one dropdown.** Shoes, tops and bottoms no longer have a
  family dropdown in front; the families are groups inside the model list.
- **Series node, reworked.** A brand strip like the Person node; count, start
  number and *↻ New series* in one row; the start button says which photos it
  queues and how long; small neutral switches instead of six orange dots, and
  axis states that say something (`all 7 framings`, `standing only`,
  `follows framing · 1328 px`). The photo-number widget is hidden — the panel
  shows *Next: photo N*. Ratio and size are one axis, *Format*; families are
  chips; camera has a quick choice (close, figure, wide).
- Clearing a section asks once (`clear 3?`), like clearing everything; labels
  that occur twice in a short form get their field name
  (`Athletic (shoulders)`); the face-field warning sits under the Face row.

## [2.4.0] — 2026-09-18

### Added

- **Bottom material**, after a follow-up test: latex now reads "high-gloss latex
  with a wet mirror-like shine and bright white specular highlights" (more
  shine than "high-gloss" alone), and tweed and corduroy joined, rendered in
  grey where black hid them; knit looked like the bare word and stays out.
- **Bottom material** (latex, patent, leather, wet-look, clear PVC, silk, satin,
  velvet, chiffon, tulle, denim, sequins, lace, mesh, metallic), written
  between colour and cut. Latex and patent only showed their shine with
  "high-gloss"; tweed, knit and corduroy were unreadable in black and wait for
  a lighter test. Cuts that name their own fabric (denim, leather, tulle)
  ignore it.
- **Seventeen more bottoms** (micro, skater, front-slit pencil, double-slit
  maxi, high-low, bias-cut midi, short tulle, corset, Latin fringe, tennis,
  skort; bike shorts, high-cut hot pants, booty shorts, slit palazzo, lace-up
  and flared leggings), appended after the first twelve.
- **Bottom** field next to the top, with colour and two families: skirts (mini,
  pencil, pleated mini, pleated midi, slit maxi, wrap mini) and shorts &
  trousers (denim shorts, hot pants, skinny jeans, wide-leg trousers, leather
  leggings, cargo pants). Rendered full body against a bare "mini skirt"; all
  passed, an "A-line mini skirt" looked like the bare word and became "mini
  skirt". Written after the top with "with", plurals without an article.
- **Top** field in Photoshoot Person (Clothing tab), with its own colour and
  families, starting with twelve crop tops: basic, puff sleeve, wrap, long
  sleeve wrap, ribbed, button-up, off-shoulder, strappy bustier, halter,
  tie-front, square neck and one-shoulder. Each wording was rendered on the
  same person, seed and framing (three seeds) against a bare "crop top" and
  kept only because the cut showed. The top is written first among the
  clothes ("wearing a pastel blue ribbed crop top ...") and stays in figure
  and identity framings, but not in feet or hand details.
- **Six more shoes** (72 in total): ankle-strap pumps, d'Orsay pumps, heeled
  oxfords, T-strap platforms, chelsea boots and d'Orsay flats, each sorted into
  its family. They sit at the end of the list, so the first 66 keep their
  position on the shoe poster, which now shows all 72: the six fill the last
  row, rendered with the same scenes and seed rule as the rest.
- **Tops and bottoms posters** ([Tops](docs/POSTERS.md#tops-matrix-12-crop-tops),
  [Bottoms](docs/POSTERS.md#bottoms-matrix-34-skirts-shorts--trousers)) in the
  style of the shoe poster: every cut on the README's person with her scene,
  light, style and seed, waist up for the tops and full body for the bottoms,
  captioned with the colour and the exact wording the node writes.

## [2.3.0] — 2026-09-02

### Added

- **Photoshoot Style node** (`Krea2StyleBuilder`). The look as a choice instead
  of free text: two families — *black & white* (classic, high contrast, film
  noir, grainy, high-key, coarse grain, fine & grain-free, infrared, sepia,
  selenium) and *colour* (Portra, Cinestill, Kodachrome, Polaroid, warm
  golden, cool desaturated, pastel) — plus genre, lens and finish, a die per
  field, and a free-text tail. Every look was rendered on the same portrait
  and kept only if it measurably differs: 10 of 18 black and white wordings
  survived, 7 of 16 colour ones. Famous film stocks are described rather than
  named, because the name alone did nothing at CFG 1. The look is emitted
  first so that it wins against colour words in the person block. Output
  goes into the `style` input of Build Prompt. Prompted by the first question
  after 2.2.0: "how do I get black and white?"
- **Photoshoot Monochrome node** (`Krea2Monochrome`). An image node that makes
  the render truly black and white — Rec. 709 luma, neutral, sepia or cool,
  with a strength slider. The prompt gets the look but leaves a trace of
  colour in lipstick; this removes it. Wire between VAE Decode and Save Image
  — the example workflows ship it there bypassed, `Ctrl+B` switches it on.
- **Start number for the series.** Next to the photo count sits a start
  number with a die. *Start shooting* begins the series there, so a new
  number is a new series with the same settings — no prompt edit needed. The
  preview numbers its lines accordingly.
- **FAQ** in the README: photo number versus seed, a new series with the same
  settings, black and white, why your images differ from the posters. And a
  note at the top that the nodes write text and the model decides the picture.
- **Three posters** in [`docs/POSTERS.md`](docs/POSTERS.md): the ten black &
  white looks and the seven colour looks on one portrait, same photo number
  and seed, and a ten-photo black & white series.
- **Three bust presets** in the Person Builder — *very large (contrast)*,
  *massive / stacked*, *extreme* — and **size steps up to 2560 px** (6.5 MP)
  in the photoshoot for models that render that large.
- **Docking API** (`nodes/dock.py`): `parse_person_data` now accepts the
  Person Builder's raw state as well as its resolved values and resolves it
  itself, so an extension pack can hand in either.
### Changed

- **`{style}` moves to the front of the prompt.** The example workflow's
  template, the recommended order in the docs and Build Prompt's fallback
  order without placeholders now begin with the style. Measured: "black and
  white photograph, monochrome" at the end of the prompt rendered in colour
  regardless of wording (channel spread 25–26, same as the colour render); at
  the front it rendered monochrome (spread 3–5), and a wide shot stayed a wide
  shot. See [`docs/measurements.md`](docs/measurements.md).
- **The photoshoot's counter is called `foto`, not `seed`**, and is 1-based:
  photo 1 is the first photo, as in the preview. It was a run counter all
  along — the noise seed leaves on `bildseed` — but a widget named "seed" got
  set to randomize, and then the series no longer counted. Workflows saved
  before load unchanged (widget values are positional) and a `0` still means
  the first photo; workflows saved in API format need the key renamed.
  Example workflows and the English locale are updated.
- **Example workflows, tidied.** Five numbered groups, one per step —
  models; person, lighting, style, scene; series and prompt; sampling;
  output — with room between them and no node behind another. The output
  group is a vertical stack, VAE Decode, black & white, Save Image, so the
  Monochrome node sits in the reading path; it is the one coloured node in
  the graph, and a note next to the Style node says where black and white
  is switched on. They carry the Style node in place of the style text box,
  the Monochrome node bypassed, `{style}` at the front of the template and
  the photo counter at 1. Both now show a thumbnail in ComfyUI's template
  browser. Regenerated with `tools/baue_workflow.py` against a running
  ComfyUI.

- **Natural hair colours read "natural"** in the prompt — "natural copper
  red" instead of "copper red", likewise blonde, brown, black — against the
  dyed, over-saturated look the bare colour word produced. Fantasy colours
  are unchanged. This changes the text of every saved person with one of
  those colours, on purpose.

### Fixed

- **German leftovers in the English interface.** One warning in the
  photoshoot panel had its second half untranslated; the smoke test now reads
  every panel string out of the JS and fails on a missing entry. Combo values
  cannot be translated by ComfyUI's locale files, so the two that were German
  are language-neutral now: the Monochrome tint and the empty-store
  placeholder of the load nodes.
- **Measurements** for all of the above in
  [`docs/measurements.md`](docs/measurements.md): style position, residual
  colour, named versus described film looks, colour looks.

## [2.2.0] — 2026-08-28

### Added

- **Photoshoot Lighting & Atmosphere Studio Engine ([#5](https://github.com/ralksta/ComfyUI-Photoshoot/issues/5)).**
  New standalone node suite (`Photoshoot Lighting` / `Krea2LightingBuilder`, `Krea2LichtSave`,
  `Krea2LichtLoad`) with interactive canvas UI to compose realistic studio setups (Softbox,
  Rembrandt, Beauty Dish, 90s Direct Flash, Split, Butterfly, High-Key, Low-Key), natural/ambient
  sunlight (Golden Hour, Overcast, Cinematic Window Light, Blue Hour), and creative atmospheres
  with direction and volumetric haze. Supports saving/loading lighting blocks and wire inputs
  (`{lighting}` / `{licht}`) in `Photoshoot Build Prompt`.
- **FACS-Based Action Units Overhaul in Expression Builder.**
  Replaced passive semantic emotion adjectives with concrete Facial Action Coding System (FACS)
  muscle triggers (bared clenching teeth, dropped agape jaw, winking eyes, furrowed scowls, real wet
  tears) to force diffusion models (especially at CFG 1.0) out of their neutral resting face prior.
- **Comprehensive How-To & Prompt Engineering Guide ([`docs/GUIDE.md`](docs/GUIDE.md)).**
  In-depth documentation covering empirical learnings, FACS Action Units, token priority budgets,
  the "Less is More" 3–5 anchor rule, avoiding studio neutralizer traps, and handling turbo vs
  standard diffusion models.
- **Inspire Me / Random Character Generator.** A dedicated `Inspire Me` button in the Person
  Builder action bar generates coherent, aesthetically balanced character archetypes across
  ethnicities, realistic skin tones, hair colors, eye shades, figure, makeup, and curated fashion
  details with a single click.
- **Massive 66-Model Footwear & Shoe Engine.**
  Extensively expanded the footwear library to **66 curated, photorealistic shoe models** across
  8 structured categories with dedicated material, heel, and strap definitions:
  - *Pumps (8):* Pointed-toe classic pumps, Almond-toe, Peep-toe, Slingback, Mary Jane, High-gloss patent, Soft suede, Clear perspex Cinderella heels.
  - *Heels & Platforms (10):* 4-inch stiletto pumps, Sky-high stilettos, Vintage kitten heels, Chunky block heels, Cork wedge heels, Heeled platform pumps, Platform stilettos, Towering extreme platform heels, Glossy patent platform heels, Wooden platform clogs.
  - *Sandals (8):* Strappy high-heel sandals, Ankle-strap heels, Wrap-up lace stiletto sandals, Thong high-heel sandals, Heeled platform sandals, Open-toe mules, Minimalist slide sandals, Wedge espadrilles.
  - *Boots (9):* Heeled ankle boots, Pointed stiletto booties, Lace-up Victorian boots, Sock boots, Knee-high leather boots, Over-the-knee suede boots, Patent thigh-high boots, Western cowboy boots, Heavy combat boots.
  - *Dance & Sport (10):* Tall leather riding boots, Ballet pointe shoes with satin ribbons, Soft ballet slippers, Gymnastics toe shoes, Latin ballroom heels, Split-sole jazz shoes, White figure ice skates, Vintage quad roller skates, Running sneakers, Sturdy hiking boots.
  - *Fetish & Extreme (10):* Extreme vertical ballet heels, Heelless cantilever shoes, Crotch-high patent boots, Hoof platform boots, Corset-laced thigh-high boots, Skin-tight latex boots, Steel pin heel stilettos, 8-inch clear pole dancer platforms, Bondage padlock sandals, Patent dominatrix spike pumps.
  - *Flats & Sneakers (8):* Classic ballet flats, Flat strappy leather sandals, Tall gladiator lace-up sandals, Canvas espadrilles, Leather penny loafers, Clean white minimalist sneakers, Chunky retro sneakers, Beach flip-flops.
  - *Bare & Socks (3):* Sheer stockings (15 denier), Slouchy ribbed cotton socks, Completely barefoot with clean soles.
  
  Visual reference available in the [Footwear & Shoe Matrix Poster](docs/POSTERS.md#footwear--shoe-matrix-66-models).
- **Isolated Macro Focus Engine for Feet & Hands.** Added specialized detail isolators
  (`DETAIL_FUESSE`, `DETAIL_HAENDE`) that automatically strip conflicting upper-body, head, and facial
  tokens when framing is macro feet or hands, guaranteeing crystal-clear footwear and manicure renders.
- **Major Person Builder Presets Expansion:**
  - *Hairstyles & Colors:* Afro, Box Braids, Curtain Bangs, Wolf Cut, Sleek Wet-Look, Space Buns, Buzzcut, Undercut, Strawberry blonde, Icy white, Pastel pink, Midnight blue, Emerald green.
  - *Silhouettes & Body:* Corset waist (Wespentaille), Pear-shaped figure, Lean toned physique, Very large bust.
  - *Fashion & Fetish Accessories:* Leather O-ring chokers, Leash collar, Leather wrist cuffs, Chest harness, Thigh garter harness, Leather & latex opera gloves, Riding crop, Peaked biker officer cap, Leather bunny & cat masks, Silk blindfold.
  - *Legwear & Hosiery:* Polka dot tights, Floral lace tights, Latex stockings, Wet-look patent leggings, Wide cage garter belt, Seamed fishnets with garters.
  - *Make-up & Features:* Gothic dark grunge, Clean girl glow, 90s vintage matte, Vitiligo, Delicate facial scar, Septum nose ring, Pouty lips, Monolid, Deep-set eyes, Laminated soap brows, Bleached brows, Glass skin, Oiled wet-glow complexion, Deep ebony skin tone.
- **Visual Reference Posters & Style Matrices Suite ([`docs/POSTERS.md`](docs/POSTERS.md)).**
  Complete high-resolution visual contact sheets and interactive `<details>` previews in `README.md`
  cataloging 146 precision prompt presets with 100% English typography and official project branding:
  - *[Footwear & Shoe Matrix (66 Models)](docs/POSTERS.md#footwear--shoe-matrix-66-models)*
  - *[Lighting & Atmosphere Studio Matrix (30 Setups)](docs/POSTERS.md#lighting--atmosphere-studio-matrix-30-setups)*
  - *[Hairstyles & Hair Colors Matrix (20 Presets)](docs/POSTERS.md#hairstyles--hair-colors-matrix-20-presets)*
  - *[Poses & Postures Reference Guide (18 Full-Body Postures)](docs/POSTERS.md#poses--postures-reference-guide-18-full-body-postures)*
  - *[Expressions & Emotion Spectrum Matrix (12 Facial Moods)](docs/POSTERS.md#expressions--emotion-spectrum-12-facial-moods)*
- **Non-Overlapping Example Workflow Layouts.**
  Upgraded `tools/baue_workflow.py` with explicit pixel placement and dimensions tailored to
  custom HTML panels, cleanly organizing Person Builder, Lighting Studio, Series Engine, and Two-Pass
  Sampling without overlapping nodes.

## [2.1.7] — 2026-08-28

### Added

- **Dedicated Gender field and smart age phrasing in Person Builder.** The vague
  `type` field in the Basic tab has been replaced with `gender` (`Woman`, `Man`,
  `Trans woman`, `Person`), which pairs naturally with `age` and `ageExact`.
  Prompts now compose fluent expressions such as `a 28-year-old woman`,
  `a 26-year-old trans woman`, `a young girl`, or `a man, in his 40s`.
  Existing workflows and saved states using `type` continue to load and migrate
  seamlessly.

### Changed

- **Clean output directories.** Example workflows now save generated images to
  `photoshoot/series` and `photoshoot/anchor` instead of `krea2/shoot`.

## [2.1.6] — 2026-08-27

### Fixed

- **The "Augen" row on the Head tab stayed German in the English interface**
  ([#2](https://github.com/ralksta/ComfyUI-Photoshoot/issues/2)). Field labels
  run through `t(..., "feldnamen")`, but the label of a *row group* - the one
  shared by `eyeShape` and `eyes` - was taken straight from `ZEILENNAMEN` and
  drawn as it came off the server. It is the only entry in that table, so the
  gap showed up exactly once. The row name now takes the same trip through the
  translation table as every other label, and `tests/smoke.py` checks
  `ZEILENNAMEN` alongside `FELDNAMEN`, so a second entry cannot slip through
  the same way.

- **`tests/hook.mjs` could not start on Node 21 and newer.** It set
  `globalThis.navigator` by assignment; Node ships its own `navigator` as a
  getter-only property, so the test threw before reaching its first check. It
  now uses `Object.defineProperty()`.

## [2.1.5] — 2026-08-24

### Changed

- The changelog is now reachable from the top of the README instead of from
  line 336, next to a release badge that shows which version is current. Twelve
  releases in the registry and nothing on the repository front page reads as a
  project that stopped.

## [2.1.4] — 2026-08-24

The anchor workflow's `LoraLoaderModelOnly` landed after 2.1.3 had already gone
to the registry, so the published package and the repository disagreed about
what that file contains. A version number should mean one thing; this one
re-publishes so it does.

## [2.1.3] — 2026-08-24

### Added

- **An anchor-set workflow.** `example_workflows/photoshoot-anchor-set.json`,
  built by `tools/baue_workflow.py --anker`. Node for node it is the series
  workflow; everything that differs is state — noise axis off with a seed in
  place, ratio fixed, mood held to one family, count at six, output to
  `krea2/anchor`.

  That is exactly why it earns a file where the draft variant did not. The
  draft was a gesture, `Ctrl+B` on two nodes, and a sentence carries a gesture.
  A filled-in panel is not something a sentence can hand over, and the setting
  that matters here — turning the noise axis off *before* looking for a person
  — is the one people get wrong in the obvious order.

  It also carries a `LoraLoaderModelOnly`, wired between the `UNETLoader` and
  both samplers and shipped bypassed. Left out, the answer to "where does my
  LoRA go" lived in prose; switched on, the file would demand a model nobody
  has. Bypassed, it shows the place and stays out of the way until someone
  picks a file and presses `Ctrl+B`.

## [2.1.2] — 2026-08-24

### Fixed

- **A subject seen from behind was still given a face.** All 82 back views in
  500 runs carried eyes, gaze, mouth and brows, and 18 of them additionally
  pointed the focus at the face, the eyes or the lips of someone turned away.
  `seen from behind, looking into the camera` was a real draw.

  This is the eighth of these and the only one that broke anatomy rather than
  meaning: the model twists the body far enough to show both the back and the
  face, and the spare limbs come out of that twist. Found because a reader
  counted three arms in a demonstration image.

  `_ausdruck_fuer_koerper()` now drops the facial detail for a back view, the
  same mechanism `_ausdruck_fuer_detail()` already used for wide framings, and
  the focus can no longer land on the face. The mood survives, since it reads
  through posture and shoulders — unless its own wording names something
  facial. "A beaming, radiant smile" behind a back view is the same
  contradiction one level up, so that is decided on the text rather than by
  taste, which also covers moods added later.

## [2.1.1] — 2026-08-24

### Fixed

- **A placement that did not name the subject produced a second person.** The
  wide shot drew `farther back in the background of the space`, and the model
  read that as a description of something else in the room rather than as a
  position for the woman it had just been given: one squatting in front, one
  standing behind. Naming the subject fixes it — `the subject farther back in
  the space` gives one figure on the same seed. The foreground and middle
  ground entries were reworded the same way.

  This is the seventh contradiction of the day and the first that came from
  wording rather than from a missing coupling. The couplings ask whether two
  fields can be true at once; this one was a single field that could be read as
  being about someone else.

  Verified by rendering, not by reading, and the first two attempts were wrong.
  Removing the depth claim from the wide-shot camera text changed nothing and
  was reverted. The second wording said `the subject standing farther back`,
  which fixed the duplicate and introduced a fresh contradiction, because the
  drawn posture was squatting — the image obligingly showed her standing. No
  placement names a posture now, checked across all ten.

## [2.1.0] — 2026-08-24

### Fixed

- **Eyes, mouth and brows are now coupled to the mood.** The fifth of these and
  by far the largest: **273 of 500 runs drew a face that contradicted its own
  expression** — `flirting, tear-stained eyes`, `gentle smile, eyes squeezed
  shut`, `unyielding, eyes rolled up`. With brows counted, 297.

  It is also the one that hurt most, because it lands in the face, which is
  where anyone looks first. And it hid behind a plausible excuse: an image
  model handed two contradictory instructions averages them, and the result
  reads as a model that cannot hit an expression rather than as a prompt asking
  for two things.

  Written as an exclusion list (`STIMMUNG_NUR_FUER`) rather than as nine tables
  per family, because almost every option fits almost every mood — closed eyes,
  a half smile, a tilted head belong anywhere — and only a dozen are tied to
  something particular. Naming those dozen states what is true. Gaze and head
  tilt are deliberately unrestricted: they suit any mood there is.

  `stimmung` is first in the expression order, so the family is settled before
  the face is drawn. The preview filters identically. 500 runs, no
  contradiction.

## [2.0.11] — 2026-08-24

### Fixed

- **Placement is now coupled to the posture as well.** The fourth of these, and
  the smallest: 25 of 500 runs put `moving through the open space of the room`
  on a body that was sitting, kneeling, lying or on all fours. Nine of the ten
  placements say only *where* the figure is, which any posture can satisfy —
  you can lie on the floor near a window. That one claims motion.

  The placement now has to satisfy two constraints at once, so `_pool()` had to
  learn to intersect them rather than answer with whichever matched first: the
  framing still decides how far away the figure may be, and the posture decides
  whether it can cross the room at all. Found while pulling captions for a
  demonstration sheet, where the tile would have read "lying on the stomach,
  moving through the open space".

## [2.0.10] — 2026-08-24

Documentation only — no node changed.

### Added

- **How to build an anchor set**, and the trap in it. Turning the noise axis
  off is what holds a person still across a series — it swaps the per-run seed
  for one series seed and offers a die to look with. The obvious order is the
  wrong one: people find someone they like at run 7, switch the axis off, and
  get a stranger, because the seed changes from `7 × 2654435761 mod 2³¹` to
  whatever the series seed happens to be. Switch it off *first*, then roll.
  For keeping a particular run, that formula is the answer.

  Also says which framings to keep and why: a close-up carries the face and
  nothing below the shoulders, a full-body shot carries the clothes and the
  build but no facial detail. And that a character LoRA slots in with a single
  `LoraLoaderModelOnly`, without being necessary for any of it.

## [2.0.9] — 2026-08-24

### Fixed

- **Arms and legs are now coupled to the posture.** Camera against placement was
  fixed in 2.0.3, posture against tension in 2.0.4. The remaining pair was the
  worst of the three: 18 postures, 14 arm positions and 10 leg positions drawn
  independently. Measured over 500 runs, **one in five asked for something
  nobody can do** — `walking, arms wrapped around the knees, knees together,
  feet apart` was a real draw, and so were `standing, legs stretched out` and
  `leaning against a wall, legs tucked underneath`.

  The model does not refuse those. It splits the difference and twists the body
  until both halves are half-true, which reads as bad anatomy rather than as a
  bad prompt — that is how this was found, in a render, not in the code.

  `HALTUNG_ARME` and `HALTUNG_BEINE` work exactly like `HALTUNG_SPANNUNG`:
  `haltung` comes first in `FOLGE`, so it is settled before arms and legs are
  drawn. Hands resting in the lap need a lap; forearms need something to rest
  on; a stride is not a stride with the ankles crossed. After the change the
  same 500 runs contain no contradiction at all. The preview in `js/shooting.mjs`
  filters identically, and the tables go out over `/krea2/presets`.

## [2.0.8] — 2026-08-24

Documentation only — no node changed.

### Fixed

- **The second pass was made to sound mandatory in a way the measurement did
  not support.** What was measured is that keeping the 1.5× upscale while
  dropping the refinement gives an unusably soft image, because latent
  upscaling invents no detail. Dropping *both* is a different thing: you get
  the base resolution, and it is sharp. Measured on distinct seeds so nothing
  came from the node cache — 10.2 s against 21.5 s, 1328×1328 against
  1632×2448. Told apart now in the README and in `docs/measurements.md`.
- **The stated prompt length was too low.** 620 to 770 characters, the README
  claimed. Remeasured over 1000 runs of the shipped example workflow: 759 to
  996, median 842. The old range sat entirely below the real minimum, and the
  number is what the section uses to argue that CLIP-only models will split the
  prompt.

### Added

- **How to draft before shooting a series.** Select the `LatentUpscaleBy` and
  the second `KSampler` and press `Ctrl+B`. Bypass passes the latent straight
  through — both take a LATENT and return one — so the decode reads the first
  sampler and you get pass one on its own, at half the time per image. Press it
  again to go back; nothing has to be re-entered, which matters because the
  person, the scene and the axis restrictions live in the nodes.

  What it is for is the first five or six runs: check the setup, fix what is
  wrong, then shoot properly. Since the series counts through combinations
  rather than drawing at random, those are the same runs you will render at
  full size later — a preview of the real thing, not a stand-in.
- **The Person Builder is optional, and the README now says so.** Unwire it and
  the `{person}` placeholder drops from the prompt without stray commas,
  leaving framing, pose, placement, expression and ratio to vary around
  whatever supplies the identity — a LoRA and its trigger word, an IPAdapter
  reference, an identity-preserving edit model. The most common request after
  release was a reference-image input, and this is most of what people were
  asking for.
- **A measurement of whether img2img can stand in for that.** It cannot, and
  the reasons are structural: the latent carries the source image's geometry,
  so framing and aspect ratio cannot move, and with the description gone
  nothing anchors the identity. At denoise 0.45 the framing had not changed and
  the face already had; at 0.85 the direction won and the person was someone
  else. In `docs/measurements.md`, so nobody has to find out the same way.

## [2.0.7] — 2026-08-23

### Added

- **A neutral "Short" height and a "Stocky" build.** The only short height was
  "Petite", and in English that means short *and* slightly built, so it fought
  every fuller figure — `petite, short stature, plus-size, full-figured` asks
  for two things at once, and the model averages them. "Short" carries no build
  with it. "Stocky, solid build" fills the other gap: short and solid otherwise
  only went through "Muscular", which means something else. Prompted by a
  reader whose character is shorter and plumper than the usual default.

### Fixed

- **Said which button starts the series.** The quick start read "press the
  button", the node reference read "a button inside the node queues the runs
  itself" — both true, neither saying that the Queue button above the canvas is
  not the one. Queue renders a single run, photo 1, because the seed widget is
  the run counter; that is correct behaviour and it looks exactly like a broken
  node to anyone who has not found the panel yet. Both places now name **Start
  shooting** and state the difference. Reported by a user who got one image and
  reasonably concluded the series did not work.
- **The stated prompt length was too low.** The README claimed 620 to 770
  characters, roughly 150–190 tokens. Remeasured over 1000 runs of the shipped
  example workflow: 759 to 996 characters, median 842 — the old range sat
  entirely below the real minimum. It matters, because the number is what the
  section uses to argue that CLIP-only models at 77 tokens per chunk will split
  the prompt.

### Changed

- The model section says outright that **nothing goes in**: these nodes take no
  image and no reference. A workflow driven by one portrait photo has to guess
  the body, because the photo holds none below the shoulders; here you state
  it. The two combine — an IPAdapter can carry the face while these fields say
  what the photo cannot show.

## [2.0.6] — 2026-08-23

### Added

- **A floor of 18 on the exact-age field.** The presets could never describe a
  minor — `type` offers woman, young woman, man, young man, person, and `age`
  runs from the early 20s to 60+. The one numeric path was `ageExact`, which is
  free text: `compose_person()` pulled the digits out and appended
  `" years old"`. It now clamps anything below `MINDESTALTER` to 18, and the
  live preview in `js/person.mjs` does the same, so what you see is what the
  prompt says.

  This is a guardrail, not a content filter, and the README says so. The nodes
  only emit text; anyone can type text into any other node. What it does do is
  rule out the accident and back the statement about scope with something that
  holds when someone tests it.

## [2.0.5] — 2026-08-22

### Fixed

- **Eight of the fourteen nodes were invisible to ComfyUI-Manager.** The store
  nodes were registered in a loop with a computed key
  (`NODE_CLASS_MAPPINGS["Krea2%sSave" % art.capitalize()]`). That is equivalent
  at run time, but the Manager reads node names statically out of the syntax
  tree to build `extension-node-map.json` — the table "Install Missing Custom
  Nodes" uses to work out which pack provides a node someone's workflow needs.
  A computed key cannot be read there.

  Measured by running the Manager's own `scanner.py` against the package: 6 of
  14 found before, 14 of 14 after. Anyone opening a shared workflow that used
  `Krea2PersonSave` would have been offered nothing.

  The names are written out literally now. They are unchanged — they sit in
  every saved workflow — and `tests/smoke.py` checks both that the set is
  exactly what the loop produced and that every name appears verbatim in the
  source, so the next refactor cannot quietly hide them again.

## [2.0.4] — 2026-08-22

### Fixed

- **Body tension no longer contradicts the base posture.** Both fields were
  drawn independently, so a series could ask for "leaning against a wall,
  curled up" — a body upright and balled up at once — or "lying on the back,
  with a slumped posture", where nothing is there to slump. Measured over a
  200-run series: 24 photos, 12%.

  This is the same class of fault as the camera-and-placement contradiction
  fixed in 1.4.0, on a different pair of axes. It does not double the figure the
  way that one did, but the model still has to reconcile two instructions that
  cannot both hold.

  `HALTUNG_SPANNUNG` in `nodes/pose_builder.py` now names the tensions each
  posture allows, and both the photoshoot and the Pose node's own dice draw from
  it. Deliberately per posture rather than per family: "reclining" sits, but
  reclining and curling up are opposites, and a family rule would miss that.

  **This changes what a series produces.** 36% of runs get a different tension —
  more than the 12% that were contradictory, because a smaller pool shifts where
  the counting sequence lands even for pairings that were fine. Everything else
  is untouched: same camera, same focus, same posture, same expression, same
  ratio. Series generated before this version are no longer reproducible in
  their tension field. The same trade was made in 1.4.0.

  `tests/smoke.py` checks the 200 runs, that every posture keeps at least one
  tension, and that no label in the table is a typo. Verified to fail when the
  coupling is switched off, naming run 7 — the run that surfaced this.

- Confirmed the browser preview computes exactly what the server does: 200 runs
  through `plane()` in Python and `_plane()` in `js/shooting.mjs`, compared
  field by field, 200/200 identical.

- Leftovers from the rename. Two German tooltips still told the user to wire
  into "Krea-2 Prompt bauen", a node that has been called "Photoshoot Prompt
  bauen" since 2.0.0; the example workflow shipped a node group titled
  "Krea-2 Kit"; `docs/internals.md` spoke of "every Krea-2 node"; and the
  injected stylesheet carried the id `krea2-kit-css`. The English side was
  already correct throughout — only the German source strings and the internal
  id had been missed.

- The example workflow named models from the development installation: a
  diffusion model under a local subfolder, a privately renamed VAE, and a
  non-standard build of the text encoder. Three loaders that nobody else could
  resolve. It now names the files [Comfy-Org publishes for Krea
  2](https://huggingface.co/Comfy-Org/Krea-2) — `krea2_turbo_fp8_scaled`,
  `qwen3vl_4b_fp8_scaled` and `qwen_image_vae` — so the example matches what
  anyone who followed the official ComfyUI tutorial already has.

  The README now also says that the text encoder is the one part that cannot be
  swapped: Krea 2 taps twelve layers of Qwen3-VL-4B at hidden size 2560
  (`comfy/text_encoders/krea2.py`), so plain Qwen3-4B and the 32B build will not
  load.

- `docs/README.md` was half German. The earlier translation pass covered `.py`,
  `.mjs` and `.js` but not Markdown, so the image table and the notes on
  retaking the screenshots stayed behind. It ships with the package.

## [2.0.3] — 2026-08-22

### Fixed

- **The actual reason the registry flagged 2.0.0 and 2.0.1.** The reason is
  readable after all, through
  `https://api.comfy.org/nodes/comfyui-photoshoot/versions?include_status_reason=true`.

  On 2.0.1 there was exactly one finding left: the YARA rule
  `python_network_operations`, pattern `$socket4`, matching six characters in
  `js/shared.mjs` — the `Function.prototype` method that pre-binds a receiver,
  which the rule looks for as a socket call. A Python rule firing on JavaScript,
  severity `info`, confidence 90.

  The hook now keeps the original function and forwards the receiver at call
  time instead. That is equivalent in effect — our replacement is invoked as a
  method on `app`, so `this` is `app` — and a shade more robust, since the
  actual receiver is passed through rather than assumed.

  Reported upstream, because the rule will fire on a large share of ComfyUI
  front-end extensions.

- The `.comfyignore` from 2.0.1 was not wrong, only incomplete: it cleared three
  of the four findings on 2.0.0 (`subprocess`, `urlopen`, `importlib`, all in
  developer tooling). The fourth is the one above.

### Added

- `tests/hook.mjs` — a regression test for the graphToPrompt hook, the single
  point through which every node's state reaches the API prompt. It checks the
  receiver is preserved, compound subgraph ids resolve, other packs' nodes are
  left alone, and an unset node falls back to its default. Verified to fail when
  the receiver is deliberately dropped, so it is not a test that passes
  regardless. Needs node; excluded from the published package like everything
  under `tests/`.

### Added

- `tools/baue_workflow.py --lokal` builds a copy of the example workflow against
  model files named differently on the machine you are working on. It reads
  `tools/modelle.local.json` and writes `photoshoot-series.local.json`, never
  touching the file that ships; both paths are in `.gitignore`, so local names
  cannot reach a commit even by accident.

### Removed

- Four `console.log` markers left over from debugging, two of them carrying a
  timestamp from the session that tracked down the `.mjs` caching problem. The
  language diagnostic stays — it answers "why is my interface in the wrong
  language" in one line — and is now in English.

## [2.0.2] — 2026-08-22

### Changed

- **Comments and docstrings are now in English**, across the nodes, the
  JavaScript, the build tooling and the smoke test. The package is public, and
  German comments shut contributors out of the part that explains *why* the code
  looks the way it does — which is most of what these comments are for.

  Identifiers, state keys and the German label tables are deliberately untouched.
  Those keys live in `node.properties` of every saved workflow and in every saved
  person; renaming them would break other people's stored work for no gain. The
  German labels are the German localisation itself and have to stay.

  Verified as comment-only: with docstrings stripped, the Python AST is identical
  to the previous commit except for twelve console messages that were translated
  along with them. In JavaScript the only differences outside comments are the
  CSS comments inside the stylesheet template literal.

## [2.0.1] — 2026-08-21

### Fixed

- **An attempt at the flag on 2.0.0**, which did not work. A `.comfyignore` now
  keeps `tools/` and `tests/` out of the package, along with `docs/face.png`,
  which no document embeds — 34 files instead of 38.

  The reasoning was that the tooling looks like malware to a scanner:
  `veroeffentliche.py` runs git through `subprocess`, `baue_workflow.py` opens
  network connections, and two files write into `sys.modules`. None of it is
  touched at runtime. That reasoning was wrong, or at least incomplete: 2.0.1 was
  flagged as well, with the tooling gone. The registry reports no reason
  (`status_detail` is empty), and none of the three documented prohibitions —
  `eval`/`exec`, runtime pip installation, obfuscated code — applies to this
  package. Under investigation.

  Keeping the development tooling out of the published archive is right either
  way, so the change stands.

## [2.0.0] — 2026-08-21

### Changed

- **Renamed from Krea-2 Kit to Photoshoot.** "Kit" said nothing about what it
  does, and "Krea-2" tied it to one model although the nodes work with any
  text-to-image model — only the measurements and the example workflow are
  Krea 2 specific.

  Only the visible layer changed: package name, display names, category,
  console prefix, documentation. **Node types are unchanged** —
  `Krea2PersonBuilder` and friends keep their names — and the stores stay under
  `ComfyUI/user/krea2_*`. Existing workflows and saved persons survive the
  rename untouched. The price is a name in the code that the interface no
  longer shows.

- The example workflow is now `example_workflows/photoshoot-series.json`.

## [1.4.0] — 2026-08-21

### Fixed

- The detail-level tags in the Photoshoot preview were German one-letter
  abbreviations (`[V] [F] [T]`) and stayed German in an English interface. They
  are two letters now — `Fu` / `Fi` / `Id`, because "full" and "figure" share a
  first letter in English — and go through the translation table.
- The preview could run past the right edge of the node and was simply cut off,
  with nothing indicating there was more. It scrolls horizontally now.

### Changed

- The example workflow ships with a filled-in person (the one from the README).
  An empty Person Builder shows nothing but dashes — neither the per-tab counters
  nor the live preview, which are the point of the node.

## [1.3.4] — 2026-08-21

### Changed

- The example workflow's prompt template now uses the English placeholder
  spellings (`{camera}, {scene}, {person}, {pose}, {expression}, {style}`). The
  German ones still work, but they had no business in the example everybody
  opens first.
- Node descriptions — the tooltips — are translated too, via
  `nodeDefs.<name>.description`. They were the last German text left in an
  otherwise English interface. `tools/baue_locales.py` reports any node whose
  description has no translation.
- The README lists the English placeholders first and mentions the German ones
  as the still-valid originals.

## [1.3.3] — 2026-08-21

### Fixed

- **Updates did not reach the browser.** ComfyUI serves the registered
  `*.js` extension files with `cache-control: no-store`, but the `.mjs` files
  next to them — where the interfaces actually live — go out with only an ETag
  and no Cache-Control. Browsers may then cache heuristically, typically a tenth
  of the age of the file, so a two-week-old file sticks around for a day and a
  half. The panels kept showing the previous version while the server had long
  been serving the new one; the English interface arriving as German was this,
  not a translation problem.

  Every import of an own `.mjs` now carries `?v=<version>`. The loaders are
  never cached, so a new version there pulls fresh modules.
  `tools/setze_js_version.py` writes it from `pyproject.toml` — **run it after
  changing anything under `js/`**, or users keep the old interface.

## [1.3.2] — 2026-08-21

### Fixed

- **An interface explicitly set to English stayed German.** The locale was read
  only from `app.extensionManager.setting`, which depending on load order and
  frontend version hands back nothing while the panels are already drawing. The
  fallback then took the browser language — German — even though the user had
  chosen English.

  The locale now comes from three sources in order: the frontend setting, the
  stored setting that the server reads out of `comfy.settings.json` and serves
  with the presets, and finally the browser language. The panels log which one
  won, so a wrong language can be diagnosed from the browser console instead of
  guessed at.

## [1.3.1] — 2026-08-21

### Fixed

- Language detection assumed English whenever `Comfy.Locale` was unset. ComfyUI
  itself falls back to the browser language there, so on a German browser the
  surrounding interface was German while the kit could have shown English.
  `js/shared.mjs` now derives the locale the same way ComfyUI does.

## [1.3.0] — 2026-08-21

### Fixed

- **The same person appeared twice in one image.** Camera framing and the pose
  axis *Raum* both say something about distance, and nothing kept them from
  contradicting each other: `portrait shot, head and shoulders` together with
  `farther back in the background of the space` asks for a near figure and a far
  one at once, and the model obliges by painting both — once close up, once
  small in the background. It hit 14 of 40 runs.

  `KAMERA_RAUM` now couples the two, the same way `KAMERA_FOKUS` already coupled
  focus to framing. The three close framings keep only placements that carry no
  distance ("in the foreground" confirms nearness, "near a window" is a location,
  not a distance); "deep in the room" survives for the wide shot alone. The
  smoke test checks 200 runs for contradictions.

  Series are numbered, so **this changes which photo a given run number
  produces** for any series whose framing and placement previously clashed.

### Changed

- The JS preview filters placements exactly like `plane()` does, so it keeps
  showing what will actually be rendered.

## [1.2.0] — 2026-08-21

### Added

- **Example workflow** — `example_workflows/photoshoot-series.json`, the whole
  kit wired up: person, photoshoot, prompt assembly and a two-pass sampler
  (8 steps, 1.5× latent upscale, 4 steps at denoise 0.44). `width`/`height` and
  `bildseed` come from the Photoshoot node, so framing drives the ratio and runs
  stay reproducible.
- `tools/baue_workflow.py` generates it and validates every node type, input
  name, output index and required input against a running ComfyUI. The workflow
  was verified by executing it, not merely by loading it — which is how a
  missing `positive` on the second sampler was caught.
- `docs/` lists the screenshots the README wants.

## [1.1.0] — 2026-08-21

### Added

- **Multilingual interface.** The panels follow ComfyUI's language setting:
  German stays German, everything else gets English. Node titles, inputs and
  outputs go through ComfyUI's own `locales/en/nodeDefs.json`; the custom DOM
  panels use a table in `nodes/i18n.py`. 600 preset labels plus field names,
  tabs, families and every tooltip.
- English placeholder spellings in prompt assembly: `{camera}` `{expression}`
  `{scene}` `{style}` alongside the German ones, mixable in one text.
- `tools/baue_locales.py` regenerates `nodeDefs.json` from the node definitions,
  so it cannot drift when an input or output is added.
- The smoke test now fails on any missing or orphaned translation.

### Notes

- Only the **display** is translated. The German labels remain the keys — they
  sit in `node.properties`, in the coupling tables and in every saved workflow.
  Saved persons and wired graphs are unaffected by the language.
- Translation is per category, because the same German word differs by field
  ("Braun" is *tan* for hosiery, *chocolate* for lipstick).

## [1.0.0] — 2026-08-21

First tagged release. Everything below describes the state at that tag; the
kit was in use before it, and node type names have been stable throughout, so
existing workflows keep finding their nodes.

### Nodes

- **Photoshoot Person** — 44 fields across six tabs, hidden state, two
  outputs (`person`, `person_data`).
- **Krea-2 Gesichtsausdruck** — 90 moods in nine families plus eyes, gaze,
  brows, mouth and head tilt, with per-field rolling.
- **Photoshoot Pose** — posture, placement in the room, orientation, arms, legs,
  body tension.
- **Photoshoot Seriesing** — a whole series from one click across six axes;
  queues the runs itself.
- **Save/load** for persons, scenes, styles and prompts, plus
  **Krea-2 Bausteine wählen** (four dropdowns in one node).
- **Krea-2 Prompt bauen** — placeholder substitution with comma cleanup.

### Added in the run-up to this release

- Camera-dependent detail levels: `compose_person` takes a detail level, and
  Photoshooting picks it per framing (full / figure / identity), shortening
  the expression along with it. `person_data` exists so this is possible at
  all — a composed string cannot be taken apart reliably.
- Pose axis **Raum**, placing the figure in the space rather than implicitly
  in the foreground.
- Focus entry **Raum**, making the environment the primary subject for wide
  and full-body framings.
- Wide framings now demand negative space explicitly.
- `nodes/dock.py` — a stable API for optional extension packs, plus the
  `{extra}` placeholder in prompt assembly. The kit knows the placeholder, not
  the content; packs live in their own directory outside this repository.
- `tests/smoke.py`, which runs without a ComfyUI installation.
- `LICENSE` (MIT), `pyproject.toml`, this changelog.

### Changed

- Without placeholders, prompt assembly now puts camera and scene *before* the
  person. With the person first, its block won the frame area even in a wide
  shot.
- `dock.person_aus_data` no longer strips hosiery and shoes by default. Those
  belong to the Person Builder, which is what the surrounding comment always
  said; only the default contradicted it. The bundled pack passes the flag
  explicitly and is unaffected.

### Fixed

- `nodes/api.py` imported `aiohttp` at module level, which defeated the
  guard inside `register()`: a missing `aiohttp` took down every Krea-2 node
  instead of just the preset route. It is now imported where it is used.
- Store file names pass through `_safe_name` when reading, not only when
  writing. The dropdown is validated by ComfyUI, but a hand-built workflow
  bypasses that.
- `dock.pose_anhaengen` left a double space when the appended part started
  with a comma.
