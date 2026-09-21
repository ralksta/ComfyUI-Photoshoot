# CLAUDE.md

Photoshoot is a ComfyUI custom node pack for text-to-image portrait series
(built against Krea 2). You build a person once (Person, Pose, Expression,
Lighting, Style builders), then the Series node ("Photoshoot") plans a whole
shoot: framing, pose, placement, expression, aspect ratio and seed vary while
the person stays the same. The nodes only emit prompt text, plus one image node
(`mono.py`, true black and white). No runtime dependencies beyond ComfyUI.

`docs/internals.md` has the full file layout, the translation model and the
frontend touch points; read it before larger changes. `docs/nodes.md` explains
each node, `docs/GUIDE.md` the prompt-engineering findings behind the wordings.

## Key facts

- Node class names keep the old `Krea2*` prefix (`Krea2PersonBuilder`, ...),
  as do the API routes (`/krea2/presets`, `/krea2/serien`) and the store folders
  (`ComfyUI/user/krea2_persons|scenes|styles|lights|prompts|series`). Renaming
  them breaks saved workflows. Display names are "Photoshoot ...", category is
  always `"Photoshoot"` (smoke test checks this). There are 20 nodes; the smoke
  test asserts the exact count, so update it when adding or removing a node.
- Code identifiers, internal labels and tool names are German (`baue_`,
  `WURZEL`, `PRESETS`, `SCHUH_GRUPPEN`, `--wirklich`); comments, docstrings,
  docs, commits and CHANGELOG are English. Match this when editing.
- German labels are the keys everywhere (node.properties, saved workflows,
  coupling tables). Never rename an existing label; only its English display
  text or prompt value may change.

## Where option data lives

All built-in option data is Python dicts, no JSON/YAML data files. The JS panels get
everything from `/krea2/presets` (`nodes/api.py`); never add a parallel list in JS.
JSON is only for users' own entries and optional add-on packs: `nodes/eigene.py`
loads `ComfyUI/user/krea2_presets/*.json`, keeps them apart from `PRESETS` (posters,
smoke test and the publish filter never see them) and every builder's `_val` falls
back to it. Age and gender cannot be extended that way. Its routes
(`/krea2/custom`, `/template`, `/llm_prompt`, `/import`, ...) and their JSON keys
are English on purpose: users open them themselves.

- `nodes/person_builder.py`: `PRESETS` = category -> list of
  `(German label, English prompt value)`. Families for grouped lists:
  `SCHUH_GRUPPEN`, `OBERTEIL_GRUPPEN`, `UNTERTEIL_GRUPPEN`; sections, field
  kinds, colours in `SEKTIONEN`, `FELDART`, `FARBWERTE`.
- `nodes/pose_builder.py`, `expression_builder.py`, `lighting_builder.py`,
  `style_builder.py`: same `PRESETS` shape plus family/coupling tables
  (`HALTUNG_*`, `STIMMUNG_GRUPPEN`, `LICHT_GRUPPEN`, ...).
- `nodes/shooting.py`: series planning (framings, ratios, seeds, recipes, mood arcs).
- `nodes/i18n.py`: English display labels, per category (the same German word
  translates differently per field). Also the UI strings.

Adding an entry: add the tuple to `PRESETS`, put the label into its family
table if the category has one, add the English display label to `nodes/i18n.py`,
then run the smoke test (it fails on any missing translation). Tops, bottoms,
shoes, hair and headwear also need a thumbnail in `js/vorschau/<field>/`: the
entry alone on the Wardrobe's preview mannequin (shoes as a three-quarter
close-up), hair as a crop of its poster tile on the README person
(`nodes/vorschau.py` names the file; the smoke test fails without it; the
render scripts live in `~/.cache/photoshoot-doku`). New presets are
appended so existing ones keep their position on the reference posters
(`docs/posters/`, `docs/POSTERS.md`), and wordings are added only after a
render test; commit messages say so.

## Checks (all run without ComfyUI)

```bash
python3 tests/smoke.py              # import, INPUT_TYPES, presets JSON, i18n gaps, series logic; ends "ALLES OK"
node tests/hook.mjs                 # graphToPrompt hook in js/shared.mjs; ends "ALL OK"
python3 -m nodes.person_builder     # self-test, ends "ok"
python3 -m nodes.pose_builder       # self-test, ends "ok"
```

Scratch output goes to `tests/_tmp/` (gitignored). `tests/` and `tools/` are
excluded from the registry package via `.comfyignore`.

## Frontend (js/)

ComfyUI only loads `*.js` from `WEB_DIRECTORY`, so each `.js` is a tiny loader
and the real code is in `.mjs` (`shared.mjs`, `panel.mjs`, `person.mjs`,
`shooting.mjs`). Node state lives as JSON in `node.properties` and is pushed
into a hidden input by the `graphToPrompt` hook in `shared.mjs`.

After any change in `js/`: bump `version` in `pyproject.toml`, then run
`python3 tools/setze_js_version.py`, which stamps `?v=<version>` onto every
`.mjs` import (otherwise browsers keep the cached old UI). All imports must
carry the same version.

## Generated files

- `locales/en/nodeDefs.json`: `python3 tools/baue_locales.py` (only the
  `TITEL` table in the script is hand-maintained).
- `example_workflows/*.json`: `python3 tools/baue_workflow.py` (`--anker` for the
  anchor-set variant, `--lokal` for a local copy using `tools/modelle.local.json`;
  `*.local.*` files are gitignored). Do not hand-edit the shipped workflows.
- Screenshots and images in `docs/`: see `docs/README.md` for which file is used
  where and how to retake them (English locale, example workflow loaded).

## Versioning and release

- SemVer in `pyproject.toml`; `CHANGELOG.md` follows Keep a Changelog with a
  `## [x.y.z] — YYYY-MM-DD` section (Added/Changed/Fixed, bold lead-ins). The
  release tool uses that section as the GitHub release notes.
- Remotes: `origin` = ComfyUI-Photoshoot-dev (private, full history, normal
  pushes); `public` = ComfyUI-Photoshoot (release repo, one orphan commit per
  release, force-pushed). Check released state on `public`, not `origin`.
- `tools/veroeffentliche.py` (dry run; `--wirklich` publishes) builds the public
  state and applies an 18+ filter via exact string replacements in
  `nodes/person_builder.py`, `nodes/i18n.py`, `js/person.mjs` and
  `tests/smoke.py`. Changing those matched lines (age presets, `NONE = "—"`,
  the `ageExact` handling) breaks publishing; update the patterns with them.
- `tools/registry.py` publishes the public tag to the Comfy Registry afterwards.
- Never run the publish tools unless asked.

## Commits

Subjects are plain English sentences, often with an area prefix:
`Series: ...`, `Person: ...`, `Person Builder: ...`, `Docs: ...`, `Posters: ...`,
and `Release x.y.z` for version bumps.
