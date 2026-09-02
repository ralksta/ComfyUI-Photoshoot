# Changelog

Notable changes to Photoshoot. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
