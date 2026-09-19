# The nodes in detail

Full reference for every node, and the reasoning behind the parts that are not
obvious. The [README](../README.md) covers what the kit does; this covers what
each control means and why it works that way.

### Building blocks

| Node | Purpose |
|---|---|
| **Photoshoot Person** | 49 fields in seven collapsible sections: basics, body, head, face, make-up, clothing, accessories. Outputs `person` (full text) and `person_data` (JSON, for camera-dependent shortening in Photoshoot) |
| **Photoshoot Expression** | 90 moods in nine families, plus eyes, gaze, brows, mouth, head tilt |
| **Photoshoot Pose** | Posture, **placement in the room**, orientation, arms, legs, body tension |
| **Photoshoot Lighting** | 30 lighting setups in three families, plus direction and atmosphere |
| **Photoshoot Style** | The look in two families — black & white and colour, 17 measured looks — plus genre, lens, finish |
| **Photoshoot Monochrome** | An image node: true black and white, neutral, sepia or cool, between VAE Decode and Save Image |

#### Style

The style used to be a free-text box in the example workflow, and the first
question after 2.2.0 was how to get black and white out of it. The answer —
type `black and white photograph, monochrome` — was correct and still
unhelpful, because nothing in the kit said so and a bare "b&w" loses against a
person block full of colour words at CFG 1.

**Photoshoot Style** turns that into a choice. The **look** is the long field
with families: *black & white* (classic, high contrast, film noir, grainy,
high-key, coarse grain, fine & grain-free, infrared, sepia, selenium — ten,
each measured to render differently; the famous film stocks are in there as
what they look like, not by name, because the name alone did nothing, see
[measurements](measurements.md)) and *colour* (Portra, Cinestill, Kodachrome,
Polaroid, warm golden, cool desaturated, pastel — seven of sixteen tried, the
rest, teal & orange and cross-processed among them, rendered as the neutral
image).
Below it: **genre** (editorial, fashion, beauty, street, documentary …),
**lens** (85mm f/1.4 through 24mm wide angle, macro, anamorphic, tilt-shift)
and **finish** (natural skin, grain, soft focus, vignette, halation). Each
field has a die; with the look rolled and a family chosen, the roll stays
inside the family.

The look is placed first in the output on purpose, and `{style}` belongs at
the front of the prompt text. A colour treatment is the one style phrase that
has to win against the person block — "copper red hair" and "green eyes" are
colour words too — and it only does so from the front: at the end of the
prompt the same words still produced a colour image ([measured](measurements.md)).
The example workflow and the recommended order put it there. The default
(*Editorial*, *85mm f/1.4*) is the text the example workflow carried by hand
before.

Output goes into the `style` input of Build Prompt and lands at `{style}`.
Saved styles from *Save Style* keep working alongside it.

#### Monochrome

The black and white the model produces is nearly black and white. The lips in
the measured render kept a brown tint — a channel spread of up to 21 on a
scale where the colour render sits at 25 on average — and no wording talks a
distilled model at CFG 1 out of the last bit. **Photoshoot Monochrome** is an
image node for that: Rec. 709 luma, optionally tinted warm (sepia) or cool
(selenium), with a strength slider that at less than 1 becomes a
desaturation instead. It goes between VAE Decode and Save Image, and the
example workflows carry it there bypassed — `Ctrl+B` switches it on. It is not
a checkbox on the Style node because it cannot be: the Style node runs before
the sampler and hands out text, the colour exists only after VAE Decode. The
prompt is still what decides the tonality — a colour render run through this node
looks like a colour photo converted, not like one shot in black and white.

#### Person

**LoRA trigger** (under Basics): the trigger of a character LoRA, such as
`EileenX, long strawberry-blonde hair …`. With it set, the person writes gender,
age, the trigger, body and clothing, and leaves out origin, skin, hair, face,
eyes and make-up (`LORA_WEG`) — the LoRA carries the face, and a second
description of it only competes and makes the prompt long. Head, Face and
Make-up are dimmed and say *via the LoRA*. The LoRA itself is loaded in the
workflow as usual; the node only writes text.

The node is a *Steckbrief*, a profile sheet: seven sections — basics, body,
head, face, make-up, clothing, accessories — stacked as rows, one open at a
time. A closed row shows how many fields are set and a short form of them
(`Tall · Athletic (figure) · Athletic (shoulders)`), so the whole person is
readable without opening anything. It replaced six tabs whose names no longer
fit ("Make-u…", "Clothin…") and which showed one area at a time. A colour
appears in the short form as a dot in front of what it colours, the material in
brackets after the bottom; a label that occurs twice gets its field name.

Related fields share a row — hairstyle + hair colour, eye shape + eye colour,
lips + finish, nails + colour, top + colour, bottom + colour, hosiery + colour,
shoes + colour. That is not
just shorter, it is more correct: `eyeShape` and `eyes` are merged into **one**
phrase (`almond-shaped green eyes`), yet they used to live on different tabs —
you could not see one while setting the other.

Colours are a button next to the dropdown, filled with the chosen colour; the
palette opens under the row on click (arrow keys move through it, Escape closes
it). A row of dots for every colour field was tried first and was too much. The
button is greyed out where the prompt drops the colour anyway — legwear colour
with bare legs, shoe colour with no shoes. Skin tone and eyeshadow have no
dropdown, only the button and the name.

The 72 shoe models sit in one dropdown, grouped by family (the largest has
eleven entries). Before that a separate family dropdown stood in front of the
model — a click more at half the width; before that a block of chips over all
shoes, which alone took 130 px and did not fit its tab; before that one flat
list, unusable in its own way. Top and bottom work the same way.

Top and bottom open the Clothing section, above hosiery and shoes; each garment is a block of its own. The top has
twelve crop tops so far, the bottom 29 cuts in two families — skirts, and shorts
& trousers. Every wording was rendered on the same person, seed and framing
against the bare word ("crop top", "mini skirt") and kept only if the cut
actually showed; an "A-line mini skirt" looked like a plain mini skirt and was
dropped. The top is written first among the clothes, the bottom follows with
"with" (`wearing a pastel blue sleeveless crew-neck crop top in tight vertical
rib knit, with a grey mini skirt`), and plurals go without an article (`wearing
grey high-waisted hot pants`). Both stay in figure and identity framings and
drop out of foot and hand details.

The bottom has a third field, **material**, which sits indented under it
(`↳ Material`) rather than on a row of its own, where it read like a garment
(17: latex, patent, leather,
wet-look, clear PVC, silk, satin, velvet, chiffon, tulle, denim, sequins, lace,
mesh, metallic, tweed, corduroy), written between colour and cut. Latex and
patent only showed their shine with an explicit gloss wording, so latex now
reads "high-gloss latex with a wet mirror-like shine and bright white specular
highlights". Cuts that name their own fabric — denim shorts, leather leggings,
the short tulle skirt — ignore the material field instead of writing `latex denim shorts`;
the node strikes the material through and says so under it.

Clicking a field label resets that field, or the whole row.

Colour is a separate field for top, bottom, hosiery and shoes. Not only for
combinability: image models attach a colour to the nearest garment when nothing
argues against it, and with `black opaque pantyhose` and no separate shoe
colour, the shoes regularly turned black as well. An explicitly named second
colour gives the model a competing binding.

For the same reason neither material list contains a colour word any more —
"white sneakers" together with a shoe colour would have produced
`red white sneakers`.

Reset works per section (the × on its row) or for the whole node, each showing
the count — you should see what you are about to lose. Both need a second click
to confirm (`clear 3?`); any other change withdraws the confirmation.

The warning about too many face fields sits directly under the Face row.

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
A button inside the node, **Start shooting**, queues the runs itself. It is not
the Queue button above the canvas: that one renders a single run — whichever
photo number the widget shows — and leaves the rest of the series unqueued.

The node has a **photo number** widget, not a seed (it was called `seed` until
2.3.0, and people set it to *randomize* and asked why the series no longer
counted). The queue needs it — it climbs with every run — but next to "photos"
and "from" it was a third number on the node, so it is hidden and the panel
says *Next: photo N* instead. It is 1-based and still saved with the workflow.
The noise seed is derived from it and leaves on the `bildseed` output.

The top of the panel is one row: **photos** (the count), **from no.** (the
start number) and *↻ New series*. *Start shooting* sets the counter to the
start number, so a series can begin at 500 as easily as at 1 — and a new start
number is a new series with the same settings, which is the answer to "how do I
get different photos without changing the prompt". Type the number back in and
the series comes back. The button itself says which photos it queues and how
long that takes, measured on your last runs.

You operate it through six axis rows — a small switch, the name, what the axis
currently does (`all 7 framings`, `standing only`, `follows framing · 1328 px`,
`one seed · 4711`), an arrow to expand. The switches are deliberately neutral:
six orange dots next to an orange start button all shouted at once. At most one
axis is open at a time, and the details appear directly beneath their own row.
Camera has a quick choice by detail level (close, figure, wide); pose and
expression pick a family by chip; *Format* holds the ratio and the size
together, since both are the image dimensions. The last chip of a selection
cannot be deselected — it shakes instead of silently doing nothing.

**Recipes** set the axes for a kind of shoot in one click — *Editorial*
(everything varies), *Lookbook* (full body and portrait in turn, standing, calm,
2:3, one seed so the setting stays), *Headshots* (portrait and close-up,
friendly, focus on face and eyes, no pose), *Shoes* (detail and full body in
turn, standing, focus on the feet, no expression) and *Test sheet* (seven photos, every
framing once — for checking a new person). A recipe is a patch on the state
(`REZEPTE` in `shooting.py`); start number, size, takes and favourites stay.
The chip of the recipe the settings match is lit; change anything and the row
says *custom*, with nothing lost.

**Saved series** sit next to the recipes: *+ Save* stores the current settings
under a name in `ComfyUI/user/krea2_series/` — count, start number, switches,
pools, framings, focus, ratio, coverage, takes per photo, size and series seed,
so a saved series is that exact series again, not only its kind. Takes,
favourites and chosen takes are left out; they belong to one run. The × next
to a saved series deletes the file. Names go through the same filter as the
person store, so `../` cannot leave the folder.

**Order** (under Camera) decides how the framings follow each other:

- *drawn* — spread by the Kronecker steps, as before;
- *each once, in turn* — coverage: the chosen framings in order, so seven
  photos from any start number show all seven (a short drawn series can miss
  some, and which ones is chance);
- *wide → close* — dramaturgy: the series opens with the widest chosen framing
  and ends with the closest, like a real shoot. The last photo is always the
  closest, whatever the count.

**Mood arcs** (under Expression) let the mood develop over the series instead
of jumping. An arc has four stages, one per equal part of the series; a stage
is a small group of related moods, so within it the mood still varies. *Joy*:
relaxed, serene → gentle and warm smile → laughing, beaming → triumphant.
*Drama*: shy, embarrassed → frightened, worried → panicked, shocked →
desperate, crying. *Dominance*: confident, focused → stern, aloof →
imperious, demanding → contemptuous, condescending. Only moods that came out
visibly in a render test are in the arcs; sad, disgusted and contemptuous
wordings stayed close to neutral and are left out of the early stages.

With an arc the mood is written as the **subject**: the expression output
reads "a terrified woman screaming in sheer horror, eyes wide open …, hands
clutching her hair" (`STIMMUNG_ALS_SUBJEKT`), and the person output drops its
own "a woman" so the two join into one sentence. That was the finding of the
expression tests: 150-word prompts with the mood at the end stayed neutral with
every wording, model, encoder, seed and sampler setting tried; the mood as the
subject near the front, with a short person — a character LoRA's trigger —
screamed, laughed and cried. Without a LoRA, with the person described in
full, only *Joy* came through reliably: in a *Drama* series the gestures
showed, the faces stayed calm, and six takes of "crying" had no tear. The
detail shot at the close end of an arc shows the face (eyes or lips), not a
macro of the shoes, and gets the mood without gestures out of frame
(`STIMMUNG_MAKRO`, and hands, arms and shoulders dropped from the others):
"cheering with both fists raised in the air" turned four macros out of four
into a full figure or a double exposure. Both need the photo's place in the series, which the node
takes from the start number and the count (`_position()` in `shooting.py`);
all of it is integer arithmetic, because Python and JavaScript round halves
differently and the contact sheet has to show what comes out.

Close framings (close-up, portrait) carry only the turn of the body and the
arms of the pose (`NAH_SICHTBAR`); base posture, placement, legs and tension
pulled them out to a medium shot. A macro detail shot (extreme close-up with
the focus on feet, hands, eyes or lips) only carries what is in frame (`DETAIL_SICHTBAR` in `shooting.py`): the
feet the base posture and the legs, the hands the arms, eyes and lips no pose
but the expression. For the feet the base posture only stays when it keeps the
feet on the floor in front of the camera (`FUSS_HALTUNGEN`: standing, sitting
on a chair, stool or table edge, kneeling, squatting); lying, reclining,
sitting on the floor and all fours spread the figure out and are dropped. With the full pose — placement, orientation, "looking back
over the shoulder" — the macro lost and the whole figure came out.

#### Contact sheet

Below the axes, every photo of the series is a frame in its real aspect ratio,
numbered as the counter counts — the motif of the logo. Once a photo is
rendered, its picture fills the frame: the panel reads ComfyUI's history, where
every run of this node carries its photo number and its settings, and takes the
newest run whose settings match the current ones (count, start, favourites and
takes do not change what photo N is, so they are left out of the comparison).
Change an axis and the frames empty, because those pictures belong to a
different series.

A click on a frame shows framing, pose, placement, focus and mood, and three
actions: **favourite** (a heart on the frame, saved with the workflow),
**re-shoot** and **open image**. Re-shooting keeps the plan and changes only the
noise: each photo number counts its takes (`takes` in the state), and
`bildseed` adds a second odd constant per take — take 0 is the seed it always
was, so older series come out unchanged. Marked photos are queued one by one
with the counter set to *fixed*, and the counter is put back afterwards.

**Takes per photo** (under Noise: 1–4) render every planned photo several
times, each take with its own noise, so you pick the better one per shot
instead of hoping. *Start shooting* then queues photo by photo, take by take.
The detail box shows all takes of a photo side by side; a click makes one the
chosen take (`wahl` in the state), which the frame, the favourite and *open
image* then refer to.

ComfyUI keeps its history in memory, so after a restart it is empty while the
pictures are still on disk. The node therefore remembers what it found — file,
subfolder and type per photo and take — in its properties, which are saved
with the workflow; for the ten most recent settings, so going back to earlier
settings brings their pictures back as well. Runs from before a state key
existed are filled up with the defaults before comparing, so extending the
state does not empty the sheet.

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
in 16:9 landscape. The extreme close-up has no 16:9 either: a face that wide
made the model fill the rest of the frame with a second, full-length figure —
a diptych, two takes out of two — so it draws from 1:1, 3:2 and 4:5. Size is chosen via an edge length (1024 to 1536, named after
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
{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}, {extra}
```

The expression comes right after the style (new in the unreleased version).
In the expression tests a mood only showed when it stood early and as the
subject — "a terrified woman screaming …" — while "…, a frightened
expression" at the end of a long prompt stayed neutral whatever the wording;
with a mood arc the Photoshoot writes it exactly that way (see *Mood arcs*).
Framing and space come before the person — otherwise the person block wins the
frame area even in a wide shot. The style goes in front of both, and that is
new: it used to close the prompt, and there a colour treatment did not take.
"black and white photograph, monochrome" at the end of the prompt came out in
colour, however it was worded; at the front it came out monochrome, and the
wide shot stayed a wide shot ([measured](measurements.md)). If the text
contains no placeholder at all, the node appends the parts in that same order.

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
