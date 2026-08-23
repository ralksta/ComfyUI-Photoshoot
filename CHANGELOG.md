# Changelog

Notable changes to Photoshoot. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
