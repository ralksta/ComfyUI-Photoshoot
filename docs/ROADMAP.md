# Roadmap: Photoshoot 2.7 → 3.0

Where the kit goes next, what is built already and what still waits on a
render test. Written after a five-part review (workflow, UX, feature set,
character consistency, new ideas); each item names the files it touches.

The rules that do not move: German labels and class names are keys and are
never renamed; the core nodes only emit text; new wordings ship only after a
render test; the Series only ever appends outputs, so saved workflows keep
their links.

## Status legend

- **PR** – being built on its own branch, see the pull request
- **done** – built, on its way into the next release
- **render** – structure can be built now, wording/quality needs a render test on a GPU
- **later** – planned, not started

## 0 · Foundation (2.7.0)

| Item | Status |
|---|---|
| **Fix: mixed outfit order moved in lock-step with the framing.** `_WURZELN` had 16 primes, the outfit draw sat in slot 16 and wrapped onto the camera's step: with two outfits mixed, one only ever got close-ups and the other only wide shots. | done |
| **JS↔Python planner parity test** (`tests/plan.mjs`). The planner exists twice (`shooting.py`, `shooting.mjs`) and was only compared by hand. Gaze modes existed in Python only. | done |
| **Real ComfyUI test bed for the panels.** CPU-only ComfyUI + Playwright: load the example workflow, click through the panels, screenshot. Found feasible; used by every UI change below. | done (dev tooling) |
| **Offline workflow generator.** `tools/baue_workflow.py` needs a running server for the core-node signatures and crashes without one; check in a snapshot of `/object_info` for the core nodes it uses. | done |

## A · Workflow: draft fast, finish what you keep

The README already recommends drafting a series at one pass and re-rendering
the keepers, but the kit had no way to do that: *Re-shoot* changes the seed,
the photo counter is hidden, and every file is `series_000NN_.png`.

1. **Draft → Finish favourites.** A *Draft* switch next to *Start shooting*
   and a new `refine` output on the Series (appended), wired to the render
   subgraph's refine switch. *Finish favourites* queues the starred photos at
   their chosen take with refine on: same seed, same composition, full
   resolution. — done
2. **File names that say which photo it is.** A `dateiname` output
   (appended) into Save Image: `photoshoot/s0500/507_t1_draft`. — done
3. **The prompt every photo got.** Build Prompt returns its text as UI
   output, so the history keeps it; the contact sheet shows it with a copy
   button. — done (UX)
4. **Contact sheet notices upstream changes** (person, wardrobe, style,
   light, scene) and marks old frames *outdated* instead of passing them off
   as current. — later
5. **Final pass by framing:** face refine for wide shots, model upscale for
   finished favourites. — render

## B · UX: safe, complete, discoverable

1. **Undo for panel edits** (ComfyUI's change tracker), **Inspire Me no
   longer wipes the LoRA trigger** and asks before overwriting a filled
   person. — done
2. **Contact sheet shows all photos** (it stopped at 24; the README's 40-photo
   series could not be reviewed past that). — done
3. **Gaze modes in the panel** (*mixed / camera / mostly camera / away*),
   the planner already had them. — done
4. **Start shooting is robust:** no double queue, progress "queued 12/40",
   errors in the panel, listeners removed with the node. — done
5. **Empty and error states:** a Retry line when presets fail to load, a
   first-run hint on an empty person, a notice when `person_data` is not
   wired. — done
6. Builders on par with the Person node: keyboard-reachable chips,
   favourites, thumbnails for the looks from the posters (light setups and
   postures: done with B8). — later
7. **Lightbox:** the contact sheet big, in ComfyUI's bottom panel (or full
   screen): filters by favourite, reject, draft and framing, compare, take
   choice, re-shoot, finish a draft, next round, keys ← → F X C. Same data
   and actions as the node's contact sheet, no second copy. — done
8. **Studio sidebar:** the shoot in one column in ComfyUI's left sidebar —
   Person, Look, Pose, Shoot, Director — each tab the node's own panel on the
   same state; lighting setups and postures as picture tiles cut from the
   posters (on the canvas panels too); *Your setup* with widgets of any node
   pinned from its context menu (LoRA file and strength). — done
9. **Compact nodes:** ⊟ / ⊞ in every panel's brand strip, stored per node
   as display only (never in the prompt). The Series keeps start, draft,
   finish, an axes summary and a strip of the photos (a click opens the
   Lightbox there); Person, Wardrobe and the builders keep their summaries
   and *edit →*, which opens the Studio sidebar on the node's tab (or
   expands it where there is none). New nodes and the example workflows start
   compact, older workflows open full; *Photoshoot: Compact all / Expand all*
   as commands. In the full view the contact sheet keeps to two rows, the
   rest in the Lightbox. — done

## C · Feature set

1. **Shoot files** (`photoshoot-shoot/1`): a whole shoot — person fields,
   wardrobe, builders, series state, template — as one shareable JSON, saved
   and loaded from the Series panel. Foundation for C2 and E1. — done
2. **Shot list and custom arcs:** pin framing, pose family, mood, outfit per
   photo number; arcs for camera and pose (standing → sitting → lying), not
   only mood. — later
3. **Sets:** a location axis in the Series — now part of F1–F2. — done (F2)
4. **Camera angle** (eye level, low, high, overhead, Dutch), coupled to
   framing and posture. — the axis is built (F4, *Perspective*, with the
   selfie family); the other angles: render
5. Light that changes across the series (F3) — done; lens that follows framing (F4). — later
6. Couples / two people in one series. — render, last (attribute bleed)

## D · Character consistency

Photoshoot holds a person today through text and one seed (anchor set) or a
LoRA trigger. The research (September 2026):

- **Qwen-Image-2.1** (2026-09-20) generates and edits in one 7B model with up
  to 10 reference images, supported by ComfyUI core with no custom nodes
  (`TextEncodeQwenImage21`). Licence: Qwen Research License, **non-commercial**.
  int8 ≈ 12 GB VRAM, GGUF ≈ 8 GB.
- **Krea 2 Identity Edit LoRA** via `comfyui-krea2edit`: already measured in
  `docs/measurements.md` — identity held in every run, all six axes followed
  from a tight head-and-shoulders anchor. Needs a custom node pack.
- PuLID, InstantID, IP-Adapter, Flux Kontext, ACE++ do not apply: Krea 2 is
  not Flux-based.

Decided with the user (2026-09-30): Qwen-Image-2.1 as the reference route,
both goals (reference series and LoRA dataset), example workflow sized for
24 GB VRAM or more. The Krea 2 Identity Edit route is documented as the
alternative for commercial use.

Plan:

1. **Reference mode in the Person node:** a new identity source that drops
   face, hair and make-up (the `LORA_WEG` path) and names the reference
   instead ("the same woman as in `<image1>`" - Qwen-Image-2.1's own tags for
   its reference images). Body and outfit stay. *Reference* field under
   Basics. — done; wording: render
2. **Caption output + Save Dataset node:** the Series emits a training
   caption (trigger + only what varies: framing, pose, expression, outfit,
   light), a new *Photoshoot – Save Dataset* node writes `NNNN.png` +
   `NNNN.txt`. Anchor set → dataset → character LoRA → trigger series.
   Series outputs `caption` and `foto` appended. — done
3. **Second example workflow `photoshoot-reference-qwen21`:** anchor images
   in, Qwen-Image-2.1 renders the series from the Photoshoot plan. Core nodes
   only; built offline by `baue_workflow.py --referenz` against its own
   snapshot (`object_info.qwen21.json`), validated against ComfyUI master. Open for the render test: the output size (image 1's latent vs.
   the series' size), steps, a turbo LoRA. — done; quality: render
4. Anchor set with face-first framings for a better reference. — render

## E · Big leaps

1. **Director:** one sentence ("moody autumn editorial in a Berlin loft, 12
   shots") becomes a whole shoot. Any chat LLM fills a shoot file (C1); the
   import accepts only built-in labels, so every wording stays render-tested
   and nothing new reaches the prompt unchecked. A **reverse-engineer this
   photo** variant does the same from a reference photo in a vision chat. — done
   (plus an offline draft that matches the brief's words to the labels)
2. **Selects → next round:** star the photos that work, and the next series
   narrows its pools to their framings, pose families and moods, with a new
   start number. The loop a photographer works in: shoot, select, reshoot. — done
3. **Proof sheet image node:** the contact sheet as a printable image, frame
   numbers, favourites circled, the plan under each frame. — later
4. **Storyboard arcs:** scene, light, outfit and mood moving through the same
   stages ("a day in her life"). — later, builds on C2 and C3
5. **Motion bridge:** a motion prompt from photo N to N+1 for image-to-video,
   via `dock.py`. — later
6. **Wording lab:** the render-test method as a feature — candidate vs. bare
   word on the same seeds, keep writes a custom entry. — later

## F · The shoot's world (3.0)

Person, look and series are in place; what a real shoot still has and the kit
does not is the world around the person and a series planned as a story.
Decided with the user on 2026-09-30, in this order; a clickable design comes
first, as it did for the lightbox.

1. **Location builder.** The scene is a free text today, and the seed holds
   only about 22 % of a setting (`docs/measurements.md`). A builder in the
   `PRESETS` shape: families *studio, urban, nature, interior*, each with
   render-tested variants, plus **time of day, weather, season**. Couplings:
   golden hour and sunlight only outdoors, a warning when the outfit does not
   fit the set (swimwear in snow). — **structure done** (PR): the node with
   sets as tabs, the four families, indoors/outdoors from the place or the
   family chip, weather and season only outdoors, compact view, Studio *Look*
   tab, shoot files, custom entries (builder `location`), saved scenes as a
   set's text. Its lists hold only the loft (the example's scene); **render**:
   the 97 candidates in `tools/wortlabor/orte.json` (four places per family,
   time of day, weather, season, the short form), then a poster. Open: the
   outfit-against-set warning, which needs the weather and season labels.
2. **Location axis in the Series.** Sets change in blocks like outfits today
   (*loft → street → café*), or mixed; own step slot, `szene` output appended.
   Close framings shorten the set to what is behind the head. — **done** (PR):
   slot `len(FELDER) + 4`, the framing order starts over with each set block
   (with outfits: where both stay the same); close-up and portrait get the
   first clause of each part, the extreme close-up no set — the rule is group H
   of the wording lab.
3. **Light axis.** The light changes with the set or over the series as a time
   of day (*morning window → golden hour → blue hour*). The 30 setups are
   already render-tested, so this needs no new wordings; own step slot,
   coupled to the set (outdoor light only outdoors). — **done** (PR): off by
   default, *per set*, *time of day* (five stages) or *mixed*, lighting
   families as a pool, slot `len(FELDER) + 5`, `licht` output appended; studio
   and window light only indoors as well.
4. **Camera angle and lens.** Eye level, low, high, overhead, Dutch, coupled
   to framing and posture (overhead only with lying postures); a lens that
   follows the framing (35 mm wide, 85 mm portrait, 100 mm macro) as an
   either-or with the Style node's lens. — render

   **Selfie mode**, planned with F4 — done for round 1; round 2: render.
   The candidates of `tools/wortlabor/selfie.json` were rendered on
   2026-09-30 (RTX 4090, three seeds, pass 1) and judged by the user; only
   the adopted wordings ship (findings in [GUIDE §10](GUIDE.md#10-selfie-mode-what-the-render-test-found)).
   - A **Perspektive** axis in the Series (camera angle), off by default,
     appended to the framing's wording as the lab rendered it, with a
     *Selfie* family of four: *Selfie von oben* (adopted although it came out
     only slightly above eye level), *Selfie auf Augenhöhe*, *Selfie im
     Liegen*, *Spiegel-Selfie*. — done. *Selfie von unten* and *Selfie über
     die Schulter* were not adopted: round 2 (`selfie2.json`), with a steeper
     *von oben* alternative. — render
   - Couplings: a selfie means one arm holds the phone (arm positions drop to
     the ones that leave a hand free, postures that need both hands go); *im
     Liegen* lies on its back only; *Spiegel-Selfie* shows the phone, is the
     full-body one, stands, and sends the gaze to the screen, not the lens.
     Framings close-up, portrait and medium only, except the mirror selfie;
     no back view or profile; 9:16 or 4:5. — done
   - Style: a genre *Smartphone / Social* (phone-a, lens and finish in one
     wording as rendered; choosing it clears the lens). — done. The phone
     flash look (phone-b) was not adopted; a separate front-camera lens and
     phone-flash finish were not built.
   - A *Selfie* mood family with *Kusshand* ("blowing a kiss at the camera"),
     and the *Peace-Zeichen* as an arm position (rendered in the pose slot).
     — done. *Schmollmund*, *Zunge raus*, *Augenrollen*: round 2. — render
   - A Series recipe *Selfie*: 9:16 or 4:5, gaze mostly into the camera,
     selfie perspectives only. — done
5. **Hands and props.** A cup, a book, flowers, sunglasses, a jacket over the
   shoulder; interaction with the set (window frame, wall, stairs). Own field,
   coupled to the arm positions and to the set. — render
6. **Shot list and story arcs.** Pin framing, pose family, mood, set or light
   per photo number (*photo 1: wide at the window, photo 12: detail of the
   hands*); the rest is drawn as now. Arcs for every axis, not only mood:
   pose, set, light — *a day in her life* instead of 40 single photos. Edited
   in the storyboard view. — later
7. Smaller: **brief recipes** with rules (headshot, dating profile, lookbook,
   cover), **pose from a reference image** (Qwen-Image-2.1 pose control, an
   optional route beside the text), **delivery** (selects as a folder, a proof
   sheet image, social crops), **two people** last. — later

## Order

1. Foundation (planner fix, parity test) — everything else builds on it.
2. In parallel: Workflow (A1–A2 + offline generator), UX (B1–B5 + A3),
   Shoot files + Director (C1, E1), Consistency (D1–D3), Selects (E2).
3. Render tests on the user's machine for everything marked *render*; then
   release 2.7.0 (or 3.0.0 once reference mode and the Director are in).
4. Lightbox (done, B7), then the Studio sidebar (done, B8) - the two views from the clickable design -
   and compact nodes (done, B9), which lean on both.
5. F · the shoot's world: F1–F3 together (location builder, location axis,
   light axis), then F6 (shot list and arcs) on the storyboard, then F4–F5.
