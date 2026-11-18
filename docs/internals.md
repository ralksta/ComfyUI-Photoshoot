# Internals

How the kit is put together, how it is translated, and what to check when
something breaks after a ComfyUI update.

## Language

The kit was written in German and the labels are still German internally. The
interface follows ComfyUI's language setting, so you see English unless ComfyUI
is set to German; the prompt is English either way.

ComfyUI has no locale stored until you pick one, and falls back to the browser
language. `js/shared.mjs` derives it the same way, so the kit always speaks
whatever the surrounding interface speaks — a German browser gets a German
interface throughout, without anything being configured.

Node titles, inputs and outputs are translated through ComfyUI's own mechanism
(`locales/en/nodeDefs.json`); the panels are custom DOM and carry their own
table in `nodes/i18n.py`. Both translate the **display only** — the German
labels stay the keys everywhere, because they are what sits in
`node.properties`, in the coupling tables and in every saved workflow. Switching
language therefore changes nothing about saved persons or wired graphs.

Translation is per category, not flat: the same German label means different
things in different fields. "Schmal" is *narrow* on the nose, *slim* at the
waist and *thin* on the lips; "Braun" is *tan* for hosiery and *chocolate* for
lipstick. A single lookup table would be wrong at exactly those points.

A missing entry falls back to the German word — visible, but not broken.
`tests/smoke.py` fails on any gap, so they cannot creep in.

To add a language, copy the tables in `nodes/i18n.py` and key them by locale;
for node titles run `python3 tools/baue_locales.py` after adding a `locales/<lang>/`
target.

## Layout

```
__init__.py          bundles the mappings, exports WEB_DIRECTORY
nodes/
  i18n.py                English labels for the German building blocks
  person_builder.py      38 person fields (+ the outfit fields the Wardrobe shows), detail levels
  person_presets.py      PRESETS, group tables, colour swatches and Inspire Me pools for person_builder.py
  expression_builder.py  hidden state, interface in JS
  pose_builder.py        hidden state, interface in JS
  lighting_builder.py    hidden state, interface in JS
  style_builder.py       hidden state, interface in JS (look, genre, lens, finish)
  location_builder.py    hidden state, interface in JS: sets (place, time of day,
                         weather, season) as tabs; szene + ort_data for the Series
  mono.py                image node: true black and white, torch imported lazily
  dataset.py             Save Dataset: NNNN.png + NNNN.txt for a LoRA set, lazy imports
  shooting.py            the series: planning, ratios, seeds, outfit, set and
                         light per photo
  wardrobe.py            the outfits of a shoot, for costume changes in the series
  dock.py                API for optional extension packs
  store.py               save/load (persons, scenes, styles, lights, prompts, series)
                         + prompt assembly
  eigene.py              custom entries: loads and checks ComfyUI/user/krea2_presets/*.json
  llm_prompt.py          the prompt for a chat LLM that writes such a file
  shoot_datei.py         shoot files: the whole shoot as one JSON, its check
                         (pruefe) and the store ComfyUI/user/krea2_shoots
  regie.py               the Director: LLM prompt, import, offline draft
  api.py                 the routes: /krea2/presets for the interface, series, /krea2/plan,
                         outfit preview, saved scenes (/krea2/szenen),
                         /krea2/custom*, /krea2/shoots*, /krea2/director/*
js/
  shared.mjs     preset loading, Nodes 2.0 adaptation, state, graphToPrompt hook,
                 search, favourites and recent entries (localStorage
                 photoshoot.favoriten / photoshoot.zuletzt), custom-entry copies
  panel.mjs      the interface (one blueprint for pose, expression, lighting, style,
                 location; the location's sets as tabs)
  person.mjs     the Person Builder interface (sections), also the Wardrobe node
  shooting.mjs   the Photoshoot interface (axis rows, preview, queue button)
  shooting_plan.mjs  the series planner and seeded PRNG shared with shooting.py, imported by shooting.mjs
  regie.mjs      shoot files and the Director: finds the nodes of a shoot,
                 collects and writes their states, the shoot row and dialog
  lightbox.mjs   the Lightbox: the Series' contact sheet big, in the bottom
                 panel or an overlay; imported by shooting.mjs, no loader
  studio.mjs     the Studio sidebar: the panels of a shoot in one column, and
                 pinned widgets of any node; imported by shooting.mjs, no loader
  vorschau/      thumbnails: <field>/<slug>.jpg (nodes/vorschau.py names them)
  pose.js        configuration for Photoshoot – Pose
  expression.js  configuration for Photoshoot – Expression
  lighting.js    configuration for Photoshoot – Lighting
  style.js       configuration for Photoshoot – Style
  location.js    configuration for Photoshoot – Location
  person.js      loader for person.mjs
  shooting.js    loader for shooting.mjs
locales/
  en/nodeDefs.json  node titles, inputs and outputs (ComfyUI's own mechanism)
tools/
  baue_locales.py     regenerates nodeDefs.json from the node definitions
  baue_workflow.py    regenerates the example workflows, offline (--anker, --referenz;
                      --pruefen compares, --snapshot refreshes object_info.core.json
                      from a running ComfyUI, --snapshot --referenz object_info.qwen21.json)
  object_info.core.json  the signatures of the ComfyUI core nodes the example uses
  object_info.qwen21.json  the same for the reference workflow, from a ComfyUI with Qwen-Image-2.1
  wortlabor.py        wording lab: renders candidate wordings on a running ComfyUI and
                      lays them out as comparison sheets of at most six rows, named per
                      pass, into tests/_tmp/wortlabor/<file>/ (--nur-zeigen, --bogen,
                      --einzeln for single JPGs, --pruefen)
  wortlabor/          its candidate files (photoshoot-wortlabor/1): selfie.json (round 1,
                      judged 2026-09-30), selfie2.json (round 2), orte.json (the
                      Location node's wordings)
  setze_js_version.py stamps the version onto every .mjs import
  schneide_vorschau.py cuts the lighting and posture thumbnails out of the
                      posters (Pillow; --pruefen checks labels and files)
  exportiere_presets.py writes the built-in entries in the custom-entry format
  veroeffentliche.py  builds the public release (dry run; --wirklich publishes)
  registry.py         publishes the public tag to the Comfy Registry
  sync_tor.sh         runs local checks, pushes to origin/main, wakes and updates tor, restarts ComfyUI
docs/                 reference, guide, posters, custom_entries_example.json
example_workflows/    generated by tools/baue_workflow.py - not edited by hand
tests/
  smoke.py         runs without ComfyUI
  hook.mjs         the graphToPrompt hook, needs node
  plan.mjs         the series preview in shooting.mjs against shooting.py, needs node
  plan_fixture.py  its Python side, spawned by plan.mjs
  regie.mjs        shoot files on a stub graph: which node gets which section,
                   collect and write back byte for byte, undo, needs node
```

The example workflow names the model files [Comfy-Org publishes for Krea
2](https://huggingface.co/Comfy-Org/Krea-2), so it matches what a user who
followed the official tutorial already has. To build a copy that runs against
differently named files here, put them in `tools/modelle.local.json`:

```json
{ "UNET": "...", "CLIP": "...", "VAE": "..." }
```

and run `python3 tools/baue_workflow.py --lokal`. That writes
`example_workflows/photoshoot-series.local.json` and never touches the file that
ships. Both paths are in `.gitignore`, so local model names cannot reach a
commit even by accident. `tools/wortlabor.py` reads the same file for its
renders (or another one with `--modelle`).

The reference workflow (`python3 tools/baue_workflow.py --referenz`) is built
by its own function, `baue_referenz()`, and checked offline like the others,
against a snapshot of its own: `tools/object_info.qwen21.json`. Its encoder
and cache nodes are not in the ComfyUI the kit is tested against, so they
cannot go into `object_info.core.json`; refresh that file with
`--snapshot --referenz --server URL` against a ComfyUI with Qwen-Image-2.1
(core since 2026-09, 0.38.0 here). `--pruefen` covers it too. Its loaders name the files
[Comfy-Org publishes for Qwen-Image-2.1](https://huggingface.co/Comfy-Org/Qwen-Image-2.1),
as ComfyUI's own *Qwen Image 2.1: Image Edit* template does. It never touches
the two Krea workflows.

ComfyUI only loads `*.js` from `WEB_DIRECTORY` as extensions, so the actual
implementations live in `.mjs` files next to a small `.js` loader, which keeps
them from being loaded twice.

Pose, expression, lighting and style follow the `PixaromaResolution` pattern:
apart from the seed the Python node has no widgets, the state sits as JSON in
`node.properties` and is only pushed into a hidden input on submit via a
`graphToPrompt` hook. The seed stays a real widget on purpose — that is the
only way to get `control_after_generate`, which is what advancing through batch
count depends on. The photoshoot's counter is the same kind of widget, named
`foto` since 2.3.0: the front end attaches `control_after_generate` to the
option, not to the name, so any name works — and "seed" was the wrong one, it
made people set it to randomize.

The German labels and their English counterparts exist exclusively in Python and
are delivered to the interface through `/krea2/presets`. Two lists maintained in
parallel would be the surest way to let them drift apart.

### Shoot files and the Director

A shoot file (`nodes/shoot_datei.py`) carries each node's state verbatim, the
same JSON that sits in `node.properties`, under English top-level keys - so
saving and loading changes nothing, and a key a newer version adds to a state
passes through untouched. `pruefe()` checks every label against `PRESETS`, the
loaded custom entries and the copies the file carries, maps English display
names back through `nodes/i18n.py`, and returns the normalized shoot with a
list of errors; it never raises on content. `/krea2/presets` delivers which
node class and property hold each section and which inputs lead there
(`"shoot"`), so `js/regie.mjs` has no list of its own.

The Director (`nodes/regie.py`) builds its LLM prompt from the live presets
like `llm_prompt.py` and imports through `pruefe(streng=True)`: built-in labels
only, no free text but the scene, nothing below 18 whatever the build. The
smoke test runs the prompt's own example through that import and resolves
every label the prompt lists.

### Custom entries

Users' own entries come from JSON (`nodes/eigene.py`), the built-in ones stay
Python: code keys off built-in labels ("Barfuß", the coupling tables), the
wordings carry their render-test comments, and the publish filter patches exact
lines in `person_builder.py`. The loaded entries sit in `eigene.EINTRAEGE`,
apart from `PRESETS`, so poster positions, the smoke test and the publish filter
never see them. Every builder's `_val()` and the series' `_wert()` fall back to
them, and `/krea2/presets` appends them to the lists, marked `eigen`, in their
family or under *Eigene* (*Custom*). The node state carries the prompt of each
custom entry in use (`state.eigene`, per outfit in the Wardrobe), so a shared
workflow renders without the file; `_val()` takes the file first, then that copy.
Custom entries join the dice pools only from a file with `"dice": true`, so no
seed changes what it rolls. The routes under `/krea2/custom` are English on
purpose - users open them themselves. The smoke test runs the built-in entries
through the same check as an import file, and checks that every field the LLM
prompt names passes it.

## Tests

```bash
python tests/smoke.py
```

Checks what can go wrong at startup and what ComfyUI would only report as
"Failed to import": importing the package, every `INPUT_TYPES`, whether the
preset response survives JSON, that a Photoshoot run is reproducible, and the
docking API, that every label the interface shows has an English
counterpart, and that regenerating the example workflows gives the shipped
files byte for byte (`tools/baue_workflow.py --pruefen`). It deliberately runs **without** `folder_paths` and `aiohttp` — the
package has to stay importable without them, otherwise a missing ComfyUI
dependency takes down every node in the package instead of just the preset
route.

The contact sheet of the Series panel plans its photos in JavaScript
(`js/shooting.mjs`), so it need not ask the server on every change. Two
planners have to agree to the last draw, and this holds them together:

```bash
node tests/plan.mjs
```

The shoot row finds its nodes by walking the graph; `node tests/regie.mjs` holds
that to a stub graph (wired, through a reroute, the only one of its class, two
unwired) and checks that collecting a shoot and writing it back gives the same
properties byte for byte.

It spawns `tests/plan_fixture.py`, which writes the `/krea2/presets` data and
what `plane()`, `format_fuer()`, `masse()`, `outfit_fuer()`, `set_fuer()` and
`licht_fuer()` give for several hundred states (defaults, every recipe, every
order, the mood arcs, family pools and family lists, switched-off axes, outfits
in blocks and mixed and as a subset, sets of every kind with every light order
and pool, gaze modes, next-round states, large photo numbers, the perspective
axis with its selfie couplings, the Selfie recipe with sets and light), 40 runs each. The JS planner gets the same preset data and has to
agree field by field; the expected values come from the current Python code on
every run, so there is no fixture to go stale. A change to the planner goes
into both files, and any table the JS side needs goes through `_shooting()` in
`nodes/api.py`, never as a copy in JS.

The step sizes of the draws are one prime per slot (`_WURZELN` in
`nodes/shooting.py`): FELDER, then format, focus, outfit, set (`PLATZ_SET`,
`len(FELDER) + 4`), light (`PLATZ_LICHT`, + 5) and the perspective
(`SLOT_PERSPEKTIVE`, + 6). A new axis takes the next free slot; inserting into
FELDER, `PB.FOLGE` or `EB.FOLGE` would shift every later slot and change every
series ever shot. The same goes for a list an axis already draws from: the
selfie entries appended to `arme` and `stimmung` (the peace sign, the kiss)
are left out of every pool and die that does not ask for a selfie, so the
draws that were there stay what they were.

**Sets and light.** The Series reads the sets from `ort_data` in Python
(`location_builder.saetze_lesen()`: text, short form, family, outdoors) and
from the Location node's state in the panel (`ortSaetze()` in `shared.mjs`,
the node on `ort_data`, through reroutes), with the families and couplings from
`/krea2/presets` ("location"). The planner needs only the number of sets and
whether each is outdoors, and neither depends on a die, so the contact sheet
plans the same sets and lights as Python. Both axes are opt-in for the plan:
without a Location node and with `aktiv.licht` off (the default, and what an
old state without the key reads as) `szene` and `licht` are empty and every
other output is unchanged. `planSchluessel()` in the panel leaves the keys of
the later axes out while they read as absent (set on, light and perspective
off, the default set and light orders and pool), so a state from before them
keeps its key and the pictures the node remembers under it; otherwise the
code reads their defaults (the perspective's `false` sits in `VORGABE`).

The person and pose builders additionally carry self-tests:

```bash
python -m nodes.person_builder
python -m nodes.pose_builder
```

## Tested against

| | |
|---|---|
| ComfyUI | `806e092` (0.28.0) |
| Frontend | `comfyui-frontend-package` 1.47.10 |
| Nodes 2.0 | enabled (`Comfy.VueNodes.Enabled = true`) |

`tools/object_info.core.json` is cut from that version's `/object_info`. After
testing against a newer ComfyUI, refresh it (`python3 tools/baue_workflow.py
--snapshot --server http://127.0.0.1:8188`), regenerate both workflows and
update the table; the smoke test fails while the shipped workflows differ from
what the generator builds.

The Python side uses only long-lived interfaces: `folder_paths`,
`PromptServer.instance.routes`, hidden inputs, `control_after_generate`.

The interfaces, by contrast, depend on frontend internals that can change
between versions — `addDOMWidget`, `canvasOnly`, `LiteGraph.vueNodesMode`,
`app.graphToPrompt`, `app.queuePrompt`, the change tracker
(`app.extensionManager.workflow.activeWorkflow.changeTracker`), the bottom
panel (see *Lightbox* below), the sidebar and the node context menu (see
*Studio sidebar*). If the panels come up empty after an update,
look there first; these touch points sit in `js/shared.mjs` and in the
registration part of the respective interface.

**Lightbox.** `js/lightbox.mjs` registers a tab of type `custom` in the
bottom panel through the extension's `bottomPanelTabs` (the same list
`app.extensionManager.bottomPanel.registerBottomPanelTab()` fills; `setup()`
calls that one if the key was not honoured). ComfyUI calls the tab's
`render(el)` whenever it mounts it - possibly more than once with the same
element - and `destroy()` when it unmounts; the Lightbox keeps one root
element and moves it in and out. The element handed over has auto height, so
`render()` sets it to 100% or the stage would not follow the panel. Opening
uses the store's `toggleBottomPanelTab(id)`, only when
`bottomPanelVisible`/`activeBottomPanelTabId` say the tab is not already the
visible one; registering the tab also gives the command
`Workspace.ToggleBottomPanelTab.photoshoot-lightbox`, and the extension's
`commands` adds `Photoshoot.OpenLightbox`. Without the store (or the tab),
the Lightbox opens as its own full-screen overlay. Checked against 1.47.10
and 1.53.6.

It has no data of its own: `baue()` in `shooting.mjs` hands every Series node's
photos and actions to it (`meldeSerie()`) - `fotos()` is the contact sheet's
own planner and picture lookup, the actions are the ones its buttons call - and
the node's `zeichne()` ends with `serieGeaendert()`, which redraws the
Lightbox. It holds the node's id, never the node: undo rebuilds every node
under the same id, and the Lightbox finds the new one. Its keys are handled on
its own root and stopped there, so ComfyUI's single-key shortcuts do not fire
while it has the focus, and nothing is taken while it has not; Ctrl+Z is left
to the change tracker (a capture listener on `window`).

**Studio sidebar.** `js/studio.mjs` registers a sidebar tab of type
`custom` with `app.extensionManager.registerSidebarTab({id, icon, title,
tooltip, label, type, render, destroy})` in the extension's `setup()`. The
extension key `sidebarTabs` is not read by 1.47 or 1.53 (unlike
`bottomPanelTabs`), so it is not used; the tab is registered once, checked
against `getSidebarTabs()`. The tab is mounted through the same
`ExtensionSlot` as the bottom panel: `render(el)` whenever the tab is shown,
possibly again with the same element, `destroy()` when another tab is chosen.
The sidebar keeps one root, moves it in, sets the element to full height and
scrolls inside its own column. While mounted it checks every 0.7 s what it
shows (the series, the node objects `ziele()` resolves - undo replaces them -
and the pins with their values) and draws again on a change, never while one
of its text fields has the focus.

It has no panels of its own. `panel.mjs`, `person.mjs` and `shooting.mjs`
register their builder per node class (`registriereBauer()` in `shared.mjs`);
the same function that draws the node's widget draws into a sidebar element
when given one (`ziel`), minus the DOM widget, the node's size and the canvas
zoom passthrough, and returns `{ weg() }`. Both views register with
`ansicht(node, zeichne)`: `schreibeState()` and every drawing of one view tell
the others, which draw again once, in a microtask; a view drawn because it
was told does not pass it on, so two views cannot set each other off. The
Series keeps its queueing state on the node (`node._k2Einreihen`), so both
views see the same run. The Director goes inline through `regieInto()` in
`regie.mjs`, the dialog's content without the dialog.

Pinning uses the extension hook `getNodeMenuItems(node)`: both front ends
append what it returns to `LGraphCanvas.getNodeMenuOptions`, which feeds the
classic context menu and the Nodes 2.0 one (`useMoreOptionsMenu` converts
`has_submenu`/`submenu.options` with per-item callbacks). The pins live in
`app.graph.extra.photoshootPins` - serialised with the workflow, so the change
tracker, saving and undo cover them. A pinned control writes `widget.value`,
calls `widget.callback(value, canvas, node)`, dirties the canvas and records
an undo step (`merkeFuerUndo()`). Checked against 1.47.10 and 1.53.6, with
and without Nodes 2.0.

**Compact view.** Each canvas panel draws either its full or its compact
view from the same function (`zeichne()` in `panel.mjs`, `person.mjs`,
`shooting.mjs`); the compact one reuses what the full one shows - the closed
rows' summaries, the axis rows' texts, the contact sheet's page and planner -
and computes nothing of its own. Which view is `node.properties.
photoshootAnsicht` (display only, never in the state the hook sends);
`setzeAnsicht()` in `shared.mjs` switches, restores the full height of the
fixed-height panels from `photoshootVollHoehe`, and records one undo step a
few frames later, once the height has followed. The compact height is
measured from the content block `.k2-kompakt-inhalt`: the node gets what it
has around the panel (its size less the panel element's) plus that. The
panel element follows a new node size only on the canvas's next drawing
(Nodes 2.0: its next layout), so a `ResizeObserver` on it measures again
then; a panel off screen, or on a canvas zoomed out below ComfyUI's
low-quality threshold, is not laid out and is measured once it shows. New
nodes get the property in `nodeCreated` unless `onConfigure` ran first (a
loaded node). The summary's click goes to `oeffneStudio(node)`, which
`studio.mjs` registers: it finds the node among `ziele()` of every series,
opens its tab through the sidebar store's `toggleSidebarTab`, and answers
false where it cannot, so the node expands instead. The commands
`Photoshoot.CompactAll` / `Photoshoot.ExpandAll` come with the Studio
extension's `commands`.

**Undo.** The change tracker records the serialised graph — `node.properties`
included — on mouseup and keyup. A panel click changes the state after the
mouseup, so `schreibeState()` calls `captureCanvasState()` right after writing
(`checkState()` on older front ends; it is deprecated in 1.47 and warns).
`alsEinSchritt()` wraps a run of writes in the tracker's
`beforeChange()`/`afterChange()`, so *Start shooting* is one step. Undo and
redo reload the whole graph (`loadGraphData`): every node is removed and built
again from its properties, so the panels need no undo code of their own — but
anything a panel hangs on `document` or `api` has to go with the node
(`beimEntfernen()` wraps `node.onRemoved`), or each Ctrl+Z leaves a set of
listeners behind.

**Queueing.** `app.queuePrompt()` does not throw on a refused prompt; it shows
ComfyUI's error dialog and returns `false` (also when another queueing loop is
already running). The Series queues one photo per call to count and to stop
at the first refusal.
