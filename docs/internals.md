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
  person_builder.py      44 fields, hidden state, camera-dependent detail levels
  expression_builder.py  hidden state, interface in JS
  pose_builder.py        hidden state, interface in JS
  shooting.py            the series: planning, ratios, seeds
  dock.py                API for optional extension packs
  store.py               save/load for all four stores + prompt assembly
  api.py                 serves the preset tables to the interface
js/
  shared.mjs     preset loading, Nodes 2.0 adaptation, state, graphToPrompt hook
  panel.mjs      the interface (one blueprint for pose and expression)
  person.mjs     the Person Builder interface (tabs)
  shooting.mjs   the Photoshoot interface (axis rows, preview, queue button)
  pose.js        configuration for Photoshoot Pose
  expression.js  configuration for Photoshoot Expression
  person.js      loader for person.mjs
  shooting.js    loader for shooting.mjs
locales/
  en/nodeDefs.json  node titles, inputs and outputs (ComfyUI's own mechanism)
tools/
  baue_locales.py     regenerates nodeDefs.json from the node definitions
  baue_workflow.py    regenerates the example workflow
  setze_js_version.py stamps the version onto every .mjs import
tests/
  smoke.py       runs without ComfyUI
  hook.mjs       the graphToPrompt hook, needs node
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
commit even by accident.

ComfyUI only loads `*.js` from `WEB_DIRECTORY` as extensions, so the actual
implementations live in `.mjs` files next to a small `.js` loader, which keeps
them from being loaded twice.

Pose and expression follow the `PixaromaResolution` pattern: apart from the seed
the Python node has no widgets, the state sits as JSON in `node.properties` and
is only pushed into a hidden input on submit via a `graphToPrompt` hook. The
seed stays a real widget on purpose — that is the only way to get
`control_after_generate`, which is what advancing through batch count depends
on.

The German labels and their English counterparts exist exclusively in Python and
are delivered to the interface through `/krea2/presets`. Two lists maintained in
parallel would be the surest way to let them drift apart.

## Tests

```bash
python tests/smoke.py
```

Checks what can go wrong at startup and what ComfyUI would only report as
"Failed to import": importing the package, every `INPUT_TYPES`, whether the
preset response survives JSON, that a Photoshoot run is reproducible, and the
docking API, and that every label the interface shows has an English
counterpart. It deliberately runs **without** `folder_paths` and `aiohttp` — the
package has to stay importable without them, otherwise a missing ComfyUI
dependency takes down every node in the package instead of just the preset
route.

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

The Python side uses only long-lived interfaces: `folder_paths`,
`PromptServer.instance.routes`, hidden inputs, `control_after_generate`.

The interfaces, by contrast, depend on frontend internals that can change
between versions — `addDOMWidget`, `canvasOnly`, `LiteGraph.vueNodesMode`,
`app.graphToPrompt` and `app.queuePrompt`. If the panels come up empty after an
update, look there first; all four touch points sit in `js/shared.mjs` and in
the registration part of the respective interface.
