# The nodes in detail

Full reference for every node, and the reasoning behind the parts that are not
obvious. The [README](../README.md) covers what the kit does; this covers what
each control means and why it works that way.

### Building blocks

| Node | Purpose |
|---|---|
| **Photoshoot Person** | 44 fields across six tabs: basics, body, head, face, make-up, clothing. Outputs `person` (full text) and `person_data` (JSON, for camera-dependent shortening in Photoshoot) |
| **Photoshoot Expression** | 90 moods in nine families, plus eyes, gaze, brows, mouth, head tilt |
| **Photoshoot Pose** | Posture, **placement in the room**, orientation, arms, legs, body tension |

#### Person

Related fields share a row — hairstyle + hair colour, eye shape + eye colour,
lips + finish, nails + colour, hosiery + colour, shoes + colour. That is not
just shorter, it is more correct: `eyeShape` and `eyes` are merged into **one**
phrase (`almond-shaped green eyes`), yet they used to live on different tabs —
you could not see one while setting the other.

The 38 shoe models are chosen by family and then model; the largest family has
nine entries. Before that it was a block of chips covering all 38, which alone
took 130 px and made *Extras* the one tab at 346 px that did not fit the panel;
before that, a dropdown with 38 entries, which was unusable in its own way. No
tab now exceeds 206 px.

The superscript number on each tab says how many fields are set there — with 44
fields there is otherwise no way to know short of clicking through. Clicking a
field label resets that field, or the whole row.

Colour and material are separate fields for hosiery and shoes. Not only for
combinability: image models attach a colour to the nearest garment when nothing
argues against it, and with `black opaque pantyhose` and no separate shoe
colour, the shoes regularly turned black as well. An explicitly named second
colour gives the model a competing binding.

For the same reason neither material list contains a colour word any more —
"white sneakers" together with a shoe colour would have produced
`red white sneakers`.

Reset works per tab or for the whole node, each showing the count in its label
— you should see what you are about to lose. The whole-node reset needs a
second click to confirm; any other change withdraws the confirmation.

#### Expression and pose

The mood families range from *calm* through *assertive* and *engaged* to
*frightened*, *sad* and *dismissive*. The last two used to be called *tense*
and *withdrawn*, which lumped alertness together with fear and sadness together
with rejection — when rolling the dice, the same character came out curious one
time and panicked the next.

The secondary fields had to grow with them: "panicked" needs a wide-open eye and
an open mouth. If only "half-closed" and "pursed lips" were on offer, the
expression contradicted the mood.

Expression and pose have their own interface (family chips, a die per field,
live preview of the English sentence) and can roll per field — together with
*batch count* that yields several variants in one go without the scene falling
apart.

### Series

**Photoshoot Series** produces an entire series of images from one click: the
person stays, while camera framing, posture, expression and aspect ratio evolve.
A button inside the node queues the runs itself.

You operate it through six axis rows — a dot to toggle, the name, the current
setting, an arrow to expand. At most one axis is open at a time, and the details
appear directly beneath their own switch. The earlier version separated the two:
a row of 24 identical-looking chips on top, the detail blocks below. You clicked
"focus" and something appeared somewhere out of view.

Warnings deliberately stay visible outside the collapsibles. They report
contradictions between two axes or in the wiring, and a collapsed hint reaches
nobody.

Outputs: `pose`, `ausdruck`, `kamera` (STRING), `width`, `height`, `bildseed`
(INT), `person` (shortened to match the camera), plus `person_data` and
`kamera_label` for passing through to optional packs.

#### Framing wins over description

The **focus** (face, neckline, hands, waist, legs, feet, back, whole figure) is
appended to `kamera` rather than emitted separately — both describe what the
image shows. It is coupled to the framing: a wide shot does not focus on the
lips. If you restrict the focus list and none fits a given framing, that photo
gets no focus at all — falling back to the full list would defeat the selection.

This coupling was invisible for a long time and quietly missed: choosing camera
*wide shot* and focus *back* silently produced no focus in the prompt. Now
unreachable focus entries are struck through, and an empty intersection raises a
warning.

The four wide framings carry a **proportion hint** and explicitly demand
**negative space** (the figure does not fill the frame; for a wide shot: an
establishing shot with the subject under a quarter of the frame). The reason is
token weight: the Person Builder easily describes 13 head features against 6
body features, and image models allocate frame area roughly along that
weighting. Without a counterweight the head comes out too large.

`wide shot, figure small` alone loses against a long person block, so the UI
alone was not enough — it hints once 6 of the 12 face fields are set and warns
at 9, but it cannot fix the prompt. **Photoshoot additionally shortens** the
person block per framing:

| Framing | Person detail | Expression |
|---|---|---|
| Detail / close-up / portrait | full | full |
| Medium / cowboy / full body | figure (no micro make-up) | mood + coarse |
| Wide | identity (silhouette, hair, rough figure) | mood only |

To use it, wire `person_data` from the Person Builder into the Photoshoot
input and put its `person` output into the prompt — not the full `person` string
from the builder, which cannot be shortened reliably once composed.

The focus entry **Raum** (`environment as primary subject, figure secondary`) is
selectable for wide and full-body framings and preferred there; "whole figure"
alone pulls attention back onto the person.

The pose axis **Raum** places the figure in the space (foreground, by a window,
in a doorway, deep inside the room). Without it the figure implicitly always
ends up in the foreground, and from a wide shot even varying arm positions look
identical.

#### Counting through the series

Enumeration uses a **Kronecker sequence** — each field's step size is the
fractional part of a square root. The obvious route via integer factors
(`run * factor % length`) was measured and rejected: fields with related list
lengths marched in lockstep, and 18 of 66 field pairs were rigidly coupled. With
irrational step sizes 4 pairs remain, at the level of random noise rather than
fixed structure.

The aspect ratio is coupled to the framing so a full-body shot does not end up
in 16:9 landscape. Size is chosen via an edge length (1024 to 1536, named after
the square); the pixel count stays equal across all ratios, so compute time and
memory stay constant over the series. 1328 at 2:3 gives exactly 1088×1632.

With ratio rolling off, a fixed ratio applies — or, if something is wired to
`width_in`/`height_in`, the dimensions of the upstream node (e.g.
`Resolution Pixaroma`). The interface then reads those dimensions directly from
the upstream node and shows them in the ratio row and the preview instead of
computing from its own size step, which no longer applies. `Resolution Pixaroma`
stores its state in `node.properties` following the same pattern, so it is
readable without executing; for other sources a widget named like the output is
used.

Because a change there fires no event to hook onto, the node polls every 500 ms
and redraws only on an actual change. Redrawing every tick would throw the caret
out of the number fields.

#### Noise

The sixth axis is **noise**. Switched on, every photo gets its own seed, spread
across the run counter. Switched off, the whole series shares one series seed,
and then the setting is preserved: a scene text describes "a gothic bed of dark
wood", not *this* bed — everything it leaves open the model fills in from the
noise, and with new noise it comes out differently. Pose, expression and camera
keep varying, since those come from the prompt.

This only works at a constant image size. Noise is a tensor in image dimensions;
a different aspect ratio is a different noise field, even at the same seed. The
interface therefore warns when the series seed is set while the ratio is still
rolling.

### Storing blocks

| Node | Location |
|---|---|
| **Photoshoot Save / Load Person** | `ComfyUI/user/krea2_persons/` |
| **Photoshoot Save / Load Scene** | `ComfyUI/user/krea2_scenes/` |
| **Photoshoot Save / Load Style** | `ComfyUI/user/krea2_styles/` |
| **Photoshoot Save / Load Prompt** | `ComfyUI/user/krea2_prompts/` |
| **Photoshoot Pick Blocks** | four dropdowns, four outputs in one node |

Newly saved entries appear in the loading nodes only after a refresh (R) —
dropdowns are filled when ComfyUI queries the node definitions.

### Assembling

**Photoshoot Build Prompt** replaces the placeholders `{person1}` `{person2}`
`{person3}` `{camera}` `{pose}` `{expression}` `{scene}` `{style}` `{extra}` in
the prompt text, and `{person}` is short for `{person1}`. Placeholders left empty
leave no orphaned commas behind. `{extra}` is for optional extension packs; with
nothing wired to it, it has no effect.

The German spellings `{kamera}` `{ausdruck}` `{szene}` `{stil}` mean exactly the
same and keep working — the kit was German first, and prompts saved back then
still run. Mixing both in one text is fine.

**Recommended order** in the prompt text:

```text
{camera}, {scene}, {person}, {pose}, {extra}, {expression}, {style}
```

Framing and space come before the person — otherwise the person block wins the
frame area even in a wide shot. If the text contains no placeholder at all, the
node appends the parts in that same order (camera and scene before person, style
last).

### Extension packs (docking)

A pack that wants to change the person should not rewrite the finished prompt
string with regexes. Instead:

1. read `person_data` (JSON) from the Person Builder or Photoshoot
2. drop the clothing fields (`nodes/dock.py`)
3. set their own layer and call `compose_person` again
4. put the **new** `person` string into the prompt

Stable helpers in `nodes/dock.py`: `parse_person_data`, `strip_kleidung`,
`person_aus_data`, `pose_anhaengen`, `detail_fuer_kamera`. Photoshoot emits
`person_data` and `kamera_label` for this purpose. `dock.py` registers no nodes,
holds no preset lists of its own, and is imported by the packs themselves.
