# The nodes in detail

Full reference for every node, and the reasoning behind the parts that are not
obvious. The [README](../README.md) covers what the kit does; this covers what
each control means and why it works that way.

### Building blocks

| Node | Purpose |
|---|---|
| **Photoshoot – Person** | 38 fields in five collapsible sections: basics, body, head, face, make-up. Wears the open tab of a Wardrobe on its `wardrobe` input. Outputs `person` (full text) and `person_data` (JSON, for camera-dependent shortening in Photoshoot) |
| **Photoshoot – Expression** | 94 moods in nine families, plus eyes, gaze, brows, mouth, head tilt |
| **Photoshoot – Pose** | Posture, **placement in the room**, orientation, arms, legs, body tension |
| **Photoshoot – Lighting** | 30 lighting setups in three families, plus direction and atmosphere |
| **Photoshoot – Style** | The look in two families — black & white and colour, 17 measured looks — plus genre, lens, finish |
| **Photoshoot – Location** | The set: place (studio, urban, nature, interior), time of day, weather, season — one set or several as tabs. `szene` into Build Prompt, `ort_data` into the Series, which changes the sets. Only render-tested wordings in its lists (so far: the loft); the rest waits for the render test |
| **Photoshoot – Wardrobe** | The outfits of a shoot as tabs, each with clothing and accessories and a name. Into the Person node; the Series changes through them |
| **Photoshoot – Monochrome** | An image node: true black and white, neutral, sepia or cool, between VAE Decode and Save Image |
| **Photoshoot – Save Dataset** | An output node: each photo with its training caption as `NNNN.png` + `NNNN.txt`, for a character LoRA |

The five builders — Pose, Expression, Lighting, Style and Location — share one panel,
laid out like the Person node: the brand strip, then one row per field with
its name, what is set and a die, and a *Details* row for free English text. All
rows start closed, one opens at a time, and the node grows and shrinks with
what is open. The long field (posture, mood, lighting setup, look) opens into
its family chips and the variants; the short ones into chips instead of an
unlabelled dropdown. A field with more than twelve entries (the 94 moods, the
30 light setups) also gets a search over its chips — by German or English name
or by the prompt text, Enter takes the first hit — and a row of the ones used
last. The lighting setups and the base postures open as **picture tiles**
instead of word chips: each one cut from its reference poster
(`docs/posters/`), the same person under all 30 lights and in the 18 postures
the poster shows. The six postures added after the poster, and custom entries,
stay chips under the tiles; the search filters both. The seed only matters for a die, so it is hidden until a
field is rolled; then a line under the rows holds it, with *fixed* or *new per
run*.

Every edit in a panel — Person, Wardrobe, the builders, the Series — is one
step for ComfyUI's **Ctrl+Z** / Ctrl+Y, like moving a node. (Before 2.7 the
change tracker only noticed a panel edit with the next click, so one Ctrl+Z
took back two.) Opening and closing a section is kept in the node too and is a
step of its own. If `/krea2/presets` cannot be reached, a panel shows one line
with *Retry* instead of coming up empty.

#### Style

The style used to be a free-text box in the example workflow, and the first
question after 2.2.0 was how to get black and white out of it. The answer —
type `black and white photograph, monochrome` — was correct and still
unhelpful, because nothing in the kit said so and a bare "b&w" loses against a
person block full of colour words at CFG 1.

**Photoshoot – Style** turns that into a choice. The **look** is the long field
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

The genre **Smartphone / social** is the look of a phone's front camera
("smartphone front-camera photo, slight wide-angle distortion, natural skin,
casual social media snapshot"), for the [selfie series](#perspective-and-selfies).
It carries its own lens and finish in one wording, the way it was
render-tested, so choosing it clears the lens (`LEERT` in `style_builder.py`)
— "85mm lens, shallow depth of field" next to "slight wide-angle distortion"
would argue. Set a lens again afterwards if you want one. The die never rolls
it: it was appended, and a rolled genre must stay what it was for every seed.

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

#### Location

The scene was a free text and still can be: the example workflow's primitive
string on Build Prompt's `scene` input works as before. **Photoshoot –
Location** makes it a set the Series can plan with. Its long field is the
**place**, in four families: *studio* and *interior* are indoors, *urban* and
*nature* outdoors. Below it **time of day**, **weather** and **season**, and
*Details* for free English text — the whole set can be just that.

The lists are nearly empty on purpose. A wording goes into the lists only
after a render test, and the seed holds only about a fifth of a setting
together ([measured](measurements.md)): a place that does not come out as
written would make every series wrong the same way. So the place list holds
the one set every poster and measurement was rendered in — *Sunlit loft*,
the example workflow's scene — and the other fields say *awaiting render
test*. The candidates (four places per family, the times of day, weather and
seasons, each against the bare word) are in `tools/wortlabor/orte.json`, run by
`tools/wortlabor.py`. Until they pass, a set is its free text, a saved scene
(the *Saved scenes* chips under Details, from *Save Scene*), or a custom entry
(builder `location`, see [custom entries](#custom-entries)); a custom place
names its family with `group`.

The **family** is more than a filter here. It tells the node whether the set
is indoors or outdoors — from the place when one is chosen, else from the
family chip, so a set written as free text gets one too. Weather and season
only apply outdoors: an indoor set leaves them out (the row says *outdoors
only*), because rain in a studio is a contradiction the model resolves by
painting a window or dropping the set. And the Series fits the light to it
(below).

A node holds **several sets as tabs**, like the Wardrobe holds outfits: **+**
adds one, **⧉** duplicates the open one, **×** deletes it after a second
click, and each has a name the Series shows (without one, its place, else
*Set 2*). The dot on a tab is green outdoors, amber indoors, empty without a
family. The `szene` output is the **open tab**, so the node works without a
Series too; `ort_data` carries every set to the Series.

#### Monochrome

The black and white the model produces is nearly black and white. The lips in
the measured render kept a brown tint — a channel spread of up to 21 on a
scale where the colour render sits at 25 on average — and no wording talks a
distilled model at CFG 1 out of the last bit. **Photoshoot – Monochrome** is an
image node for that: Rec. 709 luma, optionally tinted warm (sepia) or cool
(selenium), with a strength slider that at less than 1 becomes a
desaturation instead. It goes between VAE Decode and Save Image, and the
example workflows carry it there bypassed — `Ctrl+B` switches it on. It is not
a checkbox on the Style node because it cannot be: the Style node runs before
the sampler and hands out text, the colour exists only after VAE Decode. The
prompt is still what decides the tonality — a colour render run through this node
looks like a colour photo converted, not like one shot in black and white.

#### Person

An empty Person node says where to begin: **🎲 Inspire Me** rolls a coherent
person — gender and age, then one archetype that keeps origin, skin, hair and
eyes plausible together, then body, face and (not for men) a little make-up.
The pools are `INSPIRATION` in `person_builder.py`, labels only; the smoke test
fails on a label that is not a preset. It replaces the person fields and keeps
what dice have no say over: the LoRA trigger, the free details and clothing
from an older version. With more than three fields set it asks first
(*Replace 17 fields?*), a second click confirms — like *⟲ everything*.

**LoRA trigger** (under Basics): the trigger of a character LoRA, such as
`EileenX, long strawberry-blonde hair …`. With it set, the person writes gender,
age, the trigger, body and the outfit, and leaves out origin, skin, hair, face,
eyes and make-up (`LORA_WEG`) — the LoRA carries the face, and a second
description of it only competes and makes the prompt long. Head, Face and
Make-up are dimmed and say *via the LoRA*. The LoRA itself is loaded in the
workflow as usual; the node only writes text.

**Reference** (under Basics, right below the trigger): reference mode, for a
model that takes pictures of the person along with the prompt — Qwen-Image-2.1
in the [reference workflow](../example_workflows/photoshoot-reference-qwen21.json).
Type the image numbers, `1` or `1, 2`, and the person block starts with
`the same woman as in <image1> and <image2>` (the noun follows the gender;
Qwen-Image-2.1 labels its reference images `<image1>`, `<image2>` …) instead
of `a woman`. The same fields as with a trigger stay out (`LORA_WEG`), because
the picture shows the face; age, body and the outfit stay, because a face crop
shows nothing below the shoulders. Anything that is not a list of numbers is
taken as written, for models that name their pictures differently. The
wording is a first draft and still **needs a render test**. With a trigger and
a reference both set, both are written: the reference first, the trigger after
the age.

The node is a *Steckbrief*, a profile sheet: five sections — basics, body,
head, face, make-up — stacked as rows, one open at a time (clothing and
accessories moved to the Wardrobe node, which uses the same rows). A closed row shows how many fields are set and a short form of them
(`Tall · Athletic (figure) · Athletic (shoulders)`), so the whole person is
readable without opening anything. It replaced six tabs whose names no longer
fit ("Make-u…", "Clothin…") and which showed one area at a time. A colour
appears in the short form as a dot in front of what it colours, the material in
brackets after the bottom; a label that occurs twice gets its field name.

Related fields share a row — hairstyle + hair colour, eye shape + eye colour,
lips + finish, nails + colour, and in the Wardrobe top + colour, bottom +
colour, hosiery + colour, shoes + colour. That is not
just shorter, it is more correct: `eyeShape` and `eyes` are merged into **one**
phrase (`almond-shaped green eyes`), yet they used to live on different tabs —
you could not see one while setting the other.

Colours are a button next to the field, filled with the chosen colour; the
palette opens under the row on click (arrow keys move through it, Escape closes
it). A row of dots for every colour field was tried first and was too much. The
button is greyed out where the prompt drops the colour anyway — legwear colour
with bare legs, shoe colour with no shoes. Skin tone and eyeshadow have no
list, only the button and the name.

A list of more than twelve entries — the 72 shoes, the tops, bottoms,
headwear, hairstyles — is a button that opens the list under its row, like the
palette. Typing filters it by the German or English name, the prompt text or
the family ("veil" finds the pillbox, "Stiefel" the boots), Enter takes the
first hit and Escape closes. ☆ keeps a favourite, and the five used last sit on
top; both stay in your browser, not in the workflow. The families stay as
headings. For tops, bottoms, shoes, hairstyles and headwear a picture sits
above the list: the entry under the pointer or the keyboard focus, with its
prompt text next to it. Clothes, shoes and hats are shown alone on the
Wardrobe's preview mannequin in its fixed studio look — neutral, so nobody
reads the picture as "this is what my person will look like" — and shoes as
a close-up from a three-quarter angle, because from the front a pump shows
neither heel nor profile. Hairstyles are the Person node's and stay on the
README person; a faceless mannequin has no hair. The mannequin shows no socks,
no sheer stockings and nothing of "barefoot" (its plastic feet), so those and
the perspex pumps keep feet close-ups from the shoe poster. On the mannequin
the leather cat mask and the visor hold, which do not in a portrait of the
person. The thumbnails ship with the package (`js/vorschau/`, about 1.2 MB); a
custom entry shows its prompt only. Short lists are ordinary dropdowns. The shoes went through four
designs before this one: one flat list, a block of chips that alone took
130 px, a family dropdown in front of the model, and one dropdown grouped by
family — none of them could be searched.

In the Wardrobe, top and bottom open the Clothing section, above hosiery and
shoes; each garment is a block of its own. The top has 38 cuts in three
families — crop tops, tops & blouses, bikini — and the bottom 41 — skirts
(including five ruffled ones), shorts & trousers, bikini. Every wording was
rendered on the same person, seed and framing
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

**Headwear** has 29 entries in four families — hats (cloche, top hat, Panama,
bowler, boater, cartwheel, pillbox with veil, fascinator and more), caps &
beanies (newsboy, sailor hat, fisherman cap, trapper hat, visor), hair
accessories & scarves, and fetish. Several needed more than the word: "a cloche
hat" came out as an ordinary brimmed hat, and only "a close-fitting
bell-shaped felt cloche hat with a narrow downturned brim" gave the bell;
"sailor cap" gave a peaked officer's cap, so the sailor hat is the white dixie
cup and the peaked one is the *white captain's hat*.

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

Two entries belong to the selfie: the mood **Blowing a kiss** ("blowing a kiss
at the camera"), the first of the mood family *selfie*, and the arm position
**Peace sign** ("making a peace sign with two fingers next to her face"). Both
can be picked by hand like any other entry. The dice leave them out — a mood
die rolls the *selfie* family only when that family is chosen, the arms die
never rolls the peace sign — and the Series draws them only on a selfie photo
(see [Perspective and selfies](#perspective-and-selfies)). They were appended,
and a die or a series that does not ask for a selfie gives exactly what it
gave before.

### Series

**Photoshoot – Series** produces an entire series of images from one click: the
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

You operate it through ten axis rows — a small switch, the name, what the axis
currently does (`all 7 framings`, `standing only`, `follows framing · 1328 px`,
`one seed · 4711`), an arrow to expand. The switches are deliberately neutral:
seven orange dots next to an orange start button would all shout at once. At most one
axis is open at a time, and the details appear directly beneath their own row.
Camera has a quick choice by detail level (close, figure, wide); pose and
expression pick a family by chip; *Format* holds the ratio and the size
together, since both are the image dimensions. The last chip of a selection
cannot be deselected — it shakes instead of silently doing nothing.

**Recipes** set the axes for a kind of shoot in one click — *Editorial*
(everything varies), *Lookbook* (full body and portrait in turn, standing, calm,
2:3, one seed so the setting stays), *Headshots* (portrait and close-up,
friendly, focus on face and eyes, no pose), *Shoes* (detail and full body in
turn, standing, focus on the feet, no expression), *Test sheet* (seven photos, every
framing once — for checking a new person) and *Selfie* (see
[Perspective and selfies](#perspective-and-selfies)). A recipe is a patch on the state
(`REZEPTE` in `shooting.py`); start number, size, takes and favourites stay.
The chip of the recipe the settings match is lit; change anything and the row
says *custom*, with nothing lost.

**Saved series** sit next to the recipes: *+ Save* stores the current settings
under a name in `ComfyUI/user/krea2_series/` — count, start number, switches,
pools, framings, focus, perspectives, gaze, ratio, coverage, takes per photo, size, series seed
and the set and light order and light families, so a saved series is that exact series again, not only its kind. Takes,
favourites and chosen takes are left out; they belong to one run. The × next
to a saved series deletes the file. Names go through the same filter as the
person store, so `../` cannot leave the folder. To keep the person, outfits,
light and look together with the series, save a [shoot](#shoot-files) instead.

**Order** (under Camera) decides how the framings follow each other:

- *drawn* — spread by the Kronecker steps, as before;
- *each once, in turn* — coverage: the chosen framings in order, so seven
  photos from any start number show all seven (a short drawn series can miss
  some, and which ones is chance);
- *wide → close* — dramaturgy: the series opens with the widest chosen framing
  and ends with the closest, like a real shoot. The last photo is always the
  closest, whatever the count.

**Gaze** (under Expression) sets how the eyes go through the whole series
(`state["blick"]`, `BLICK_MODI` in `shooting.py`): *mixed* draws the gaze per
photo as before, which gives eye contact about one photo in nine; *at the
camera* makes every photo look into the lens, *mostly camera* two in three, and
*away* none. A photo that looks into the camera no longer draws a mood that
looks away (thoughtful, absent, shy, embarrassed) or a back view. The axis row
names the mode when it is not *mixed*, and the contact sheet plans it too.

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

#### Perspective and selfies

**Perspective** is the camera angle, an axis of its own under Camera — off
until you switch it on, so a series without it is the series it always was.
Its first family is the **selfie**, four perspectives whose wordings were
render-tested on 2026-09-30 (three seeds each, against the bare word) and
adopted:

| Perspective | Wording | Framings |
|---|---|---|
| *Selfie from above* | high-angle selfie, phone held at arm's length above her head, she looks up into the lens | close-up, portrait, medium shot |
| *Eye-level selfie* | eye-level selfie at arm's length, one arm reaching toward the camera and out of the frame | close-up, portrait, medium shot |
| *Selfie lying down* | selfie lying on her back on a bed, phone held above her face, hair spread on the pillow | close-up, portrait, medium shot |
| *Mirror selfie* | mirror selfie, full-body reflection in a tall mirror, holding a smartphone in front of her chest, looking at the phone screen | full body |

The wording goes into the `kamera` output right after the framing's own —
`portrait shot, head and shoulders, high-angle selfie, …` — and before the
focus, which is exactly the text the [wording lab](measurements.md) rendered.
Open the row to choose which perspectives the series draws from; one whose
framings none of the chosen framings are is struck through, and a photo whose
framing no chosen perspective allows simply gets none (as with the focus).
The perspective has its own draw step (`SLOT_PERSPEKTIVE` in `shooting.py`),
so switching it on changes no other axis's draw.

A selfie holds the phone in one hand, and the series follows from that
(`PERSPEKTIVE_*`, `SELFIE_KOERPER` in `shooting.py`, `EINE_HAND_FREI` in
`pose_builder.py`):

- **arms**: only positions that leave a hand free — one hand at the face, one
  hand in the hair, the peace sign; postures that need both hands (all fours,
  stretching, chin in both hands, cross-legged and heel-sitting with both
  hands on the knees) are not drawn;
- **body**: facing the camera, turned slightly or three-quarter — no back
  view, no profile;
- **lying down** lies on its back (its wording says so), whatever the posture
  pool; the **mirror selfie** stands in front of the mirror;
- **gaze**: *from above* looks into the lens (its wording says so), the
  **mirror selfie** looks at the screen, not the lens — it gets no gaze of its
  own and no *blowing a kiss*; a photo that blows a kiss looks into the camera;
- **ratio**: 9:16 or 4:5, a phone's formats, instead of the framing's;
- **moods**: the *selfie* family (blowing a kiss) joins whatever mood pool is
  set, on selfie photos only; the peace sign likewise joins the arms.

The recipe **Selfie** sets it up: eight photos, close-up, portrait, medium
shot and full body in turn (so the mirror selfie comes up too), all four
selfie perspectives, friendly moods, gaze mostly into the camera, focus off so
the camera text is framing plus perspective and nothing else. Pair it with the
Style genre *Smartphone / social*. The caption names the perspective with the
framing ("portrait shot, high-angle selfie"); the next round keeps the
favourites' perspectives. In a shoot file the list is `"perspectives"` and the
switch `"perspective"`.

With a Location node the recipe leaves the [Set and Light](#sets-and-light)
axes as they are: the sets still change in blocks or mixed, the light per set
or over the day, and the `kamera` output carries the perspective while
`szene` and `licht` carry the set and the light. Nothing couples a
perspective to a set yet: *lying down* says *on a bed* and the mirror selfie
*a tall mirror*, which an outdoor set contradicts - choose the perspectives
to fit the sets.

Two things to know. The wordings say *her* and *she*, as they were rendered
with the example's woman; for a man the prompt still reads *her*. And *Selfie
from above* came out only slightly above eye level in the render test, not as
a steep top-down shot; it was adopted as it is, and a steeper alternative is in
the second round of the lab ([GUIDE](GUIDE.md#10-selfie-mode-what-the-render-test-found)).

#### Contact sheet

Below the axes, every photo of the series is a frame in its real aspect ratio,
numbered as the counter counts — the motif of the logo. Once a photo is
rendered, its picture fills the frame: the panel reads ComfyUI's history, where
every run of this node carries its photo number and its settings, and takes the
newest run whose settings match the current ones (count, start, favourites and
takes do not change what photo N is, so they are left out of the comparison).
Change an axis and the frames empty, because those pictures belong to a
different series; a line under the sheet then says the pictures of the
previous settings are kept, and switching back brings them.

The sheet on the node keeps to **two rows** of frames — as many as fit the
node's width, 14 on the example's Series — and names the rest under them:
**+16 · all in the Lightbox** opens the Lightbox at the first photo not shown,
which pages through the whole series with filters and keys (see *Lightbox*).
So a 40-photo series no longer makes the node 40 frames tall. Only where the
Lightbox cannot open does the sheet fall back to pages of 24 frames with ‹ ›
in its head row (*25–48 of 60*) and a *+N ›* after the last frame.

A click on a frame shows framing, pose, placement, focus and mood, the
**prompt** that photo got, with *Copy*, and three actions: **favourite** (a heart on the frame, saved with the workflow),
**re-shoot** and **open image**. Re-shooting keeps the plan and changes only the
noise: each photo number counts its takes (`takes` in the state), and
`bildseed` adds a second odd constant per take — take 0 is the seed it always
was, so older series come out unchanged. Marked photos are queued one by one
with the counter set to *fixed*, and the counter is put back afterwards.

The prompt comes from the same history entry as the picture: *Build Prompt*
hands its finished text to ComfyUI's history as well (see *Assembling*). It is
there only while ComfyUI keeps that run; after a restart the remembered
pictures come back without it, and the row says so.

*Start shooting* queues photo by photo and counts on the button (*queued
12/40*); it is disabled meanwhile, so a double click cannot queue the series
twice. If ComfyUI refuses a photo — a missing model, a node error — it shows
its own error dialog, the queueing stops there, and a line in the panel names
the photo. A series whose `person_data` input is not wired says so above the
sheet: without it there is no person to shorten per framing and no outfits.
The whole run is one step for Ctrl+Z, not one per photo.

**Takes per photo** (under Noise: 1–4) render every planned photo several
times, each take with its own noise, so you pick the better one per shot
instead of hoping. *Start shooting* then queues photo by photo, take by take.
The detail box shows all takes of a photo side by side; a click makes one the
chosen take (`wahl` in the state), which the frame, the favourite and *open
image* then refer to.

#### Selects → next round

The loop a photographer works in: shoot, select, reshoot. Star the photos that
work, optionally mark the ones that do not with **✕ Reject** (a favourite and a
reject exclude each other; a rejected frame is dimmed), and press **Next
round →** under the contact sheet. The next round is a new series with:

- **framings** narrowed to those of the favourites; the ratio follows the
  framing by itself, as always;
- the **pose** and **expression** pools narrowed to the favourites' posture
  and mood families (several families are kept as a list, and the axis row
  says *sitting, lying only*);
- **focus areas** narrowed to theirs;
- with a wardrobe, the **outfits** narrowed to theirs (`outfitAuswahl`,
  indices into the Wardrobe's list; the Outfit axis says *1 of 3 outfits*,
  dims the others on the rail and has *Use all outfits* to undo it);
- a **start number** right after this round (start + count), so every photo
  is new; count, order, size, gaze mode and series seed stay.

Rejects only take something away that no kept photo of the round shows: one
bad lying pose does not strike the lying family while another lying photo is
unmarked, and a favourite always wins. Without favourites, rejects alone can
start a next round that drops what failed.

What does not narrow: a switched-off axis, a pool set to *none*, and the mood
while a **mood arc** is on (the arc is a dramaturgy over positions, the family
pool has no say under it). A favourite whose posture is a custom entry without
a built-in family leaves the pose pool as it is. Favourites all of one framing
give a next round of that one framing — the selects said so; pose, mood,
focus within the framing, ratio and noise still vary. To widen it again, pick
more framings under Camera.

The round is computed in Python (`naechste_runde()` in `shooting.py`, behind
`POST /krea2/serien/naechste_runde`): it replays `plane()` for every photo of
the series, so it works on the plan that was rendered as long as the settings
did not change since. Only favourites inside the current series (start …
start + count − 1) count. The same selects always give the same next round.

Favourites, rejects, takes and chosen takes belong to their round: the next
round starts without them, and the previous state goes onto a small history
(`runden`, the last five rounds). The row under the contact sheet says *Round 2
· based on 3 selects*, and **← back to round 1** brings that round back —
settings, favourites and takes, so its pictures return too. Going back
discards the selects of the round you leave (the panel asks first); pressing
*Next round* again recreates the same round.

ComfyUI keeps its history in memory, so after a restart it is empty while the
pictures are still on disk. The node therefore remembers what it found — file,
subfolder and type per photo and take — in its properties, which are saved
with the workflow; for the ten most recent settings, so going back to earlier
settings brings their pictures back as well. Runs from before a state key
existed are filled up with the defaults before comparing, so extending the
state does not empty the sheet.

#### Draft and finish

Under *Start shooting* sit **Draft** and **Finish favourites**. With *Draft*
on, every run goes out with the `refine` output off; wired into a refine
switch (the example workflows' Render node has one), that skips the upscale
and second pass — about half the time, at the base resolution. Shoot the
series as a draft, star the keepers, then press **Finish favourites**: it
queues the starred photos that are still drafts (or whose picture the sheet no
longer knows), each at the take the contact sheet shows for it (the chosen
take, else the newest), with draft off — the same
seed and plan, now with the second pass. The counter is put back afterwards,
as after a re-shoot, and *Draft* stays on for the next round. It queues like
*Start shooting*: the button counts (*queued 2/5*), nothing can be queued twice
meanwhile, the run is one undo step, and it stops at a photo ComfyUI refuses.

The finish run does not touch the saved state: the draft flag and the take
go into that one prompt only (the `graphToPrompt` hook takes a per-run
override from the panel), so undo, the saved workflow and the panel all stay
as they were. The contact sheet records per picture whether it was a draft
(a dashed frame, "Draft" in the detail box) and shows the finished picture of
a take as soon as there is one, however old the draft. `entwurf` is no part
of the plan comparison, so the draft and the finished photo 7 sit in the same
frame.

Both buttons are greyed out while the `refine` output has no link — in a
workflow from before 2.7.0, say — and their tooltip says what to wire; the
runs are then finals, never marked as drafts.

#### Lightbox

The contact sheet is 52 pixels a frame; to judge a round you want the photos
big. **⤢ Lightbox** in the contact sheet's head row opens them in ComfyUI's
bottom panel, next to *Logs* — as does a double-click on a frame (the
Lightbox opens at that photo) and the command *Photoshoot: Open Lightbox*
(for the selected Series node, else the last one). It opens on the node it was
opened from and stays there; with several Series nodes in the graph a select
in its head row picks another.

- **Filters** on top: *All*, *♥ Favourites*, *✕ Rejects*, *Drafts*, then one
  chip per framing, each with its count of rendered photos.
- **The stage** shows the photo at full size, fitted to the panel, with its
  number, ♥, ✕ and *Draft* as badges and ‹ › to either side. Drag the panel
  taller and the stage grows with it; *⤢ Fullscreen* shows the same view over
  the whole window (Esc or *✕ Close* returns).
- **Beside it** framing, pose, focus, outfit and mood (the same rows as the
  detail box), the takes as chips — a click chooses the take, as in the
  contact sheet — the size, the file Save Image wrote, and the prompt, folded
  away, with *Copy*.
- **Actions:** *♥ Favourite* (F), *✕ Reject* (X), *⇆ Compare* (C) — the photo
  next to the next one in the filter; a click on either picture stars it or
  takes the star back — *↻ Re-shoot* (queued right away, one new take) and,
  for a draft, *✓ Finish* (that photo at full quality, like *Finish
  favourites*).
- **The filmstrip** runs through the whole series in number order; under
  *All* the photos not shot yet are there as dashed frames with their
  framing, and a click shows their plan.
- **The footer** counts the round — *Round 2 · 3 selects · 1 rejected* — and
  has **Next round →**, the same next round as under the contact sheet.

← and → go through the rendered photos of the filter; on a touch screen a
swipe on the stage does the same. The keys work only while the Lightbox has
the focus (click into it), so the canvas and every text field keep theirs.

The Lightbox holds no plan and no pictures of its own. The Series node hands
it its photos — the plan, sizes, outfits, the pictures from the history and
the takes — and its actions, and the contact sheet draws from the very same
functions. Every action is a write of the node's state, so the contact sheet
follows a star set in the Lightbox at once and the other way round, and
Ctrl+Z takes it back in both. Which photo is on the stage, the filter and
compare are view only and never saved.

#### File names

The `dateiname` output is a file name prefix that says which photo it is;
wired into Save Image's `filename_prefix` (as in the example workflows) the
files come out as

    photoshoot/s0001/07_t1_00001_.png        photo 7, take 1
    photoshoot/s0001/07_t1_draft_00001_.png  the same photo as a draft
    photoshoot/s0500/507_t2_00001_.png       series from 500, photo 507, take 2

The folder `s<start>` is the series: its start number, which *New series*
draws and which brings a series back when typed in again. The photo number
is the one on the contact sheet, padded to the widest number of the series
so the files sort in order; the take counts from 1, as the contact sheet
shows it. Save Image appends its own counter, so a second render of the same
take does not overwrite the first. The first folder is `photoshoot`, from the
state key `ordner` (the anchor set uses `photoshoot/anchor`). Workflows from
before 2.7.0 keep their static prefix until you wire the output.

Warnings deliberately stay visible outside the collapsibles. They report
contradictions between two axes or in the wiring, and a collapsed hint reaches
nobody.

Outputs: `pose`, `ausdruck`, `kamera` (STRING), `width`, `height`, `bildseed`
(INT), `person` (shortened to match the camera), plus `person_data` and
`kamera_label` for passing through to optional packs, and since 2.7.0
`refine` (BOOLEAN, off for a draft), `dateiname` (STRING, the file name
prefix), `caption` (STRING) and `foto` (INT, the photo number of this run),
the last two for Save Dataset. New outputs are only ever appended, so saved
workflows keep their links.

#### Caption

`caption` is the training caption of the photo, for a character LoRA: the
trigger from the Person node, the subject, then only what varies —
the framing (the head of its wording and the focus, `full body shot, with the
focus on the legs`), the pose, the expression and the outfit as far as the
framing shows it (no boots on a portrait, only boots on a feet macro). With a
mood arc the mood written as the subject stands in for the expression, as in
the prompt.

What makes the person never goes in: none of the `LORA_WEG` fields, no age, no
body, no reference phrase. Whatever a caption describes, the LoRA learns as
separate from the trigger; a face spelled out in every caption ends up
belonging to the words, and the trigger alone is weak. The smoke test holds
this photo for photo: the caption of a fully described person is the caption
of the same person with everything but gender, trigger and wardrobe removed.

Without a trigger on the person the caption starts with the subject
(`a woman, close-up shot, …`); Save Dataset then puts its own *trigger* in
front. That is the case in a reference series, whose Person node names the
images instead.

### Save Dataset

**Photoshoot – Save Dataset** writes each photo it gets as
`output/photoshoot/dataset/<name>/NNNN.png` and its caption as `NNNN.txt` next
to it — the pair kohya, ai-toolkit and OneTrainer read. Wire `caption` and
`foto` from the Series: the number is the photo number, so a re-shoot of photo
7 replaces `0007` instead of adding a file, and the set stays in series order
(a batch of several images gets `0007_1`, `0007_2` …). *name* is the folder,
cleaned of anything a path could escape with; *trigger* goes in front of the
caption unless it already starts with it. The node shows what it saved, like
Save Image.

The path from a person to a LoRA: the anchor set (or the reference workflow)
renders the series, you delete the pairs you do not like — both files — and
train on the folder. Then the LoRA's trigger goes into the Person node and the
Krea workflow shoots with it.

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
| Detail / close-up / portrait | full, but nothing below the chest line | full |
| Medium / cowboy / full body | figure (no micro make-up) | mood + coarse |
| Wide | identity (silhouette, hair, rough figure) | mood only |

The close framings leave out bottom, hosiery, shoes, legs, hips, waist and
belly: a "knee-length pencil skirt" in a portrait pulled it to three-quarter or
full length on two seeds out of two, and without them all eight test portraits
came out chest-up.

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

The last axis is **noise**. Switched on, every photo gets its own seed, spread
across the run counter. Switched off, the whole series shares one series seed,
and then the setting is preserved: a scene text describes "a gothic bed of dark
wood", not *this* bed — everything it leaves open the model fills in from the
noise, and with new noise it comes out differently. Pose, expression and camera
keep varying, since those come from the prompt.

This only works at a constant image size. Noise is a tensor in image dimensions;
a different aspect ratio is a different noise field, even at the same seed. The
interface therefore warns when the series seed is set while the ratio is still
rolling.

#### Wardrobe

Clothes are not part of the person, and a real shoot has costume changes: the
model stays, the clothes change. The **Photoshoot – Wardrobe** node holds the
outfits of a shoot, one per tab — each with *Clothing* and *Accessories* (the
fields and wordings the Person Builder used to carry) and a name the contact
sheet shows. **+** adds an outfit, **⧉** duplicates the open one (the start for
a variant), **×** deletes it after a second click. Its `wardrobe` output goes
into the Person Builder's `wardrobe` input: the person wears the **open tab** —
also without a series, when her text goes straight into Build Prompt — and
carries the whole wardrobe along in `person_data`, so the Series node
downstream can change through it. The first version had one node per outfit,
chained into the series; one wardrobe per shoot is how people plan it, and a
chain of five nodes made the graph hard to read.

The outfit **replaces** the person's clothing — every clothing and accessories
field, the bottom's material and the clothing details, whether the outfit sets
them or not. A person in jeans does not keep the jeans under a bikini. Persons
from before the Wardrobe still carry clothes of their own; they render as
before, and the Person Builder lists them with *Move to Wardrobe* (into the
wired Wardrobe as a new tab, or a new Wardrobe node next to the person) and
*remove*.

The outfits follow each other **in blocks** by default: twelve photos and three
outfits are four photos each, in the order of the tabs, and the framing order
starts over with every outfit: with *wide → close* each outfit opens wide and
ends close, instead of the first outfit getting all the close-ups and the last
all the full-body shots. *Mixed* draws the
outfit per photo instead. The draw has its own place in the counting, so a
series shot before the wardrobe existed keeps every framing, pose and seed.

Measured before it was built: with only the clothing text changing, the face
held across a crop top, a turtleneck and a Bardot top on the same seed; a
bikini moved it visibly — broader, a slightly different type. That is the one
limit: the person block is text and seed, and a lot of bare skin changes the
picture enough to change the face with it. A character LoRA holds it.

In the Series node the wardrobe is the **Outfit** axis. Its row says how many
outfits are wired and in which order; opened, it holds the order chips and the
**rail** — every outfit as a card with its name and its garments, each with a
swatch in the outfit's colour. In the contact sheet a stripe in the
outfit's main colour (the top's, else the bottom's) runs under every frame, so
the blocks read at a glance, and the detail box names the outfit. The Series
node reads the outfits from the Wardrobe node directly, so the rail and the
stripes are right before the first run and follow every edit.

**Render preview** in the Wardrobe node puts a picture on the open outfit,
**Render outfits** in the Series node on all of them, and the rail shows them
too: the outfit on its own, not on the person, so the clothes stand apart from
her. *Mannequin* (the default, chosen in the Wardrobe node) dresses a faceless
light grey store mannequin; *Flat lay* lays the pieces out side by side, seen
from above. It is one run per outfit through your own workflow — the preview
text is swapped into Build Prompt for that run — but with a fixed studio look of
its own (bright light, mid grey backdrop) instead of the shoot's style and
lighting, and the contact sheet never takes those runs for photos. A picture
made before the outfit changed stays, dimmed and marked *outdated*.

The wordings come from render tests on Krea 2: the mannequin is light grey
because a white one bled into jeans without a colour; it stands frontal
because turning it, a contrapposto or a hard light each made black tights
vanish; legwear is named right after the mannequin and tied to its legs,
because further down the list it dropped out; and in the flat lay tights get
their waistband and feet, or they read as leggings. Two things no wording
fixed, which is why the swatch list stays under the picture: sheer
skin-coloured tights do not show on any mannequin, and the flat lay sometimes
lays out one stocking instead of a pair. A ghost mannequin was tried and
dropped: it came out as a real woman with her head cropped.

#### Sets and light

**Set** and **Light** are the two axes for the world around the person
(ROADMAP F2, F3). Neither brings a wording of its own: a set is the Location
node's text, a light one of the Lighting node's 30 render-tested setups.

The **Set** axis reads the Location node on the Series' `location_data`
input (`ort_data`). Its sets follow each other **in blocks** by default — the
series in equal parts in the order of the tabs, *loft → street → café* — or
*mixed*, drawn per photo. As with the outfits, the framing order starts over
with every set: with *wide → close* each set opens wide and ends close,
instead of the first set getting only wide shots. With outfits in blocks too,
a block is where both stay the same. Its row lists the sets with their text
and whether they are indoors or outdoors; in the contact sheet a stripe in the
set's colour runs over every frame, and the detail box names the set.

What the framing shows of the set: from the medium shot out the whole set;
close-up and portrait only what is behind the head — the **short form**, the
first clause of each part of the set ("a sunlit loft with tall windows"
instead of "…, wooden floor, plants in the corner"); the extreme close-up
none. The floor and the corner are out of frame in a portrait, and naming them
pulled the camera back, the way a full pose did on the close framings. The
rule only shortens and adds no words; group H of the wording lab tests it.

The **Light** axis is off until switched on — nothing upstream asks for it,
and a series without it stays what it was. On, it draws from the 30 setups:

- *per set* — each set gets one setup, the same on all of its photos;
  without sets, one setup for the series;
- *time of day* — the day over the series in five equal parts: morning,
  midday, golden hour, blue hour, night (`TAGESLAUF`), each stage with an
  outdoor and an indoor way to say it (dawn or window light, moonlight or
  candles);
- *mixed* — drawn per photo.

*Per set* and *mixed* can be narrowed to the Lighting node's families
(studio, natural, mood). Whatever the order, the light fits the photo's set:
**outdoor light only outdoors** — the setups whose wording names the sun, the
sky or the time of day (golden hour, blue hour, overcast daylight, midday sun,
sunset, dawn, moonlight) — and **studio and window light only indoors** (the
setups that say studio or window). A set of no family takes every setup.

Both axes leave on outputs of their own, appended after the others so saved
workflows keep their wiring: **`szene`** (the set of this photo, shortened for
the framing) and **`licht`** (the setup's wording). They are empty until a
set or the light axis is configured. Wire them into Build Prompt's `scene` and
`lighting` in place of the fixed scene and the Lighting node; the panel warns
while one is on and its output leads nowhere. The caption appends both, as
they vary. Each axis has its own step in the counting (`PLATZ_SET`,
`PLATZ_LICHT` in `shooting.py`), so a series planned before them keeps every
framing, pose and seed.

### Compact view

A shoot is seven panels on the canvas, and in full the Series alone is a
thousand pixels tall. Every Photoshoot panel therefore has a second, short
view: **⊟** at the right end of its brand strip makes it compact, **⊞** makes
it full again. What stays on the canvas is what you need all the time; the
rest is a click away in the Studio sidebar.

| Node | Compact shows |
|---|---|
| **Series** | the brand strip with count and time, *Start shooting* (with its progress, disabled while it queues), *Draft*, *Finish favourites* and **⤢ Lightbox**; one line of what the axes do — framing and order, perspective (when on), pose, expression and gaze, outfit, format, the same texts as the axis rows; a **strip** of the current page's photos: the picture once rendered, a dashed frame while only planned, ♥ and ✕ as marked; and the warnings |
| **Person** | the summaries of every section in one run (what the closed rows show), **🎲 Inspire Me** and **edit →** |
| **Wardrobe** | the outfit tabs (switching and *+* work), the open outfit's summary and **edit →** |
| **Pose, Expression, Lighting, Style** | one line per field that is set, as its closed row shows it, and **edit →** |

A click on a photo in the strip opens the Lightbox at that photo. A click on
a summary line, or on **edit →**, opens the Studio sidebar on the tab that
has this node's panel (Shoot, Person, Look or Pose) for the series the node
belongs to. Where that cannot be — a front end without the sidebar, a node
wired to no series — or where the Lightbox cannot open, the click expands the
node instead, so it never does nothing. The recipes, the shoot files row, the
axes, the contact sheet with its detail box and the round row are hidden in
the compact Series; nothing of them is lost, the sidebar's Shoot tab and the
Lightbox have all of it.

A compact node is as tall as its content; expanding gives it back the height
it had (the builders follow their content in both views). The Series keeps
its thirteen outputs either way — LiteGraph cannot hide a slot, and saved
workflows link by index — so it is about half its full height.

The view is **display only**: it is stored per node in its own property
(`photoshootAnsicht`, with `photoshootVollHoehe` for the height to go back
to), never in the state the node sends, so compact and full give the very
same prompt. The switch is one step for Ctrl+Z. A node you add starts
compact; a workflow saved before this existed opens as it was, full. The
example workflows ship compact. The commands **Photoshoot: Compact all** and
**Photoshoot: Expand all** (command palette, bindable to a key) switch every
Photoshoot node of the graph at once, as one undo step. A node off screen —
or on a canvas zoomed out so far that ComfyUI stops drawing the panels —
takes its new height once it shows.

### Studio sidebar

The panels are built for a node on the canvas; with the whole shoot open they
compete for room with the graph. The **Studio sidebar** puts them into one
column over the full height: the camera icon **Studio** in ComfyUI's left
icon bar (next to Nodes, Models and Workflows) opens it.

It works on the Series chosen in its head — the selected one when it opens,
else the first; with several a select picks another — and on the nodes wired
to it, the same ones a shoot file is written to: the person on `person_data`
and her Wardrobe, the Location node on `ort_data`, and on the Build Prompt
node it feeds the Pose, Expression, Lighting and Style builders (where nothing
is wired, the only one of its type in the graph). A tab without its node says so — *No Photoshoot – Lighting node
wired to this series*.

| Tab | Shows |
|---|---|
| **Person** | the Person panel and the Wardrobe panel |
| **Look** | Lighting (the 30 setups as picture tiles), Style and Location (its sets as tabs) |
| **Pose** | Pose (the postures as picture tiles) and Expression |
| **Shoot** | the Series panel — count, recipes, *Start shooting*, *Draft*, *Finish favourites*, the axes — without the contact sheet: **⤢ Open Lightbox** opens it big instead |
| **Director** | the Director inline (idea, LLM prompt, answer, preview, *Apply*), and the shoot files row (saved shoots, save, file down and up) |
| **Your setup** | widgets of any node you pinned (below) |

Each section is **the node's own panel**, drawn by the same code as on the
canvas and on the same state — not a copy. A tile picked in the sidebar is
set on the node at once and its canvas panel follows, an edit on the canvas
shows in the sidebar, and Ctrl+Z takes either back. Queueing belongs to the
node, not to a view: a series started in the sidebar counts on the canvas
button too, and neither can start a second one. *◎ On canvas* next to a
section's name selects the node and centres the canvas on it. Which tab is
open is remembered in the browser; nothing about the sidebar goes into the
workflow.

#### Your setup: pinned widgets

The rest of a workflow has settings you change as often as the person: the
LoRA and its strength, steps, a sampler. **Right-click any node → Pin to
Photoshoot Studio** lists its widgets; pick one and it appears in *Your
setup* as a control of its kind — a select for a list (with the list's own
options), a number field for a number (with its min, max and
step; a slider next to it where the range is narrow, like denoise), a
checkbox for a switch, a text field for text — labelled with the
node's title and the widget's name. A pinned widget is ticked in that menu;
picking it again, or its **×** in the sidebar, unpins it.

A change in the sidebar sets the widget on the node, runs its callback and is
one step for Ctrl+Z; a change on the node shows in the sidebar within a
moment. The pins are stored in the workflow (`extra.photoshootPins`: node id,
widget name, label), so they are saved, shared and undone with it. A pinned
node that is deleted stays in the list, greyed out, as *node removed*, until
you unpin it.

Several LoRA loaders chained, each with `lora_name` and `strength_model`
pinned, gives one place to switch LoRAs and weigh them against each other
without scrolling the canvas.

### Storing blocks

| Node | Location |
|---|---|
| **Photoshoot – Save / Load Person** | `ComfyUI/user/krea2_persons/` |
| **Photoshoot – Save / Load Scene** | `ComfyUI/user/krea2_scenes/` |
| **Photoshoot – Save / Load Style** | `ComfyUI/user/krea2_styles/` |
| **Photoshoot – Save / Load Lighting** | `ComfyUI/user/krea2_lights/` |
| **Photoshoot – Save / Load Prompt** | `ComfyUI/user/krea2_prompts/` |
| **Photoshoot – Pick Blocks** | four dropdowns, four outputs in one node |

Newly saved entries appear in the loading nodes only after a refresh (R) —
dropdowns are filled when ComfyUI queries the node definitions.

### Shoot files

A **shoot file** is the whole shoot in one JSON (`photoshoot-shoot/1`): the
Person node's fields, the Wardrobe's outfits, the Pose, Expression, Lighting
and Style builders, the Location node's sets, the Series (count, start number, series seed, switches,
pools, framings, focus, perspectives, ratio, size, order, mood arc, takes), the scene text
and the Build Prompt template. It is what you hand someone so they shoot the
same series — or what you keep so you can come back to it.

The row **Shoot:** under the recipes in the Series panel holds it:

- the saved shoots as chips (`ComfyUI/user/krea2_shoots/`) — a click shows
  what will be set where, *Apply* sets it, *Undo* takes it back; × deletes;
- *+ Save* stores the current shoot under a name;
- *⇩ File* downloads it as a `.json` to share, *⇧ File* opens one — with
  the same preview before anything changes;
- *Director …* — below.

**Which nodes.** The ones wired to this Series node: the person on its
`person_data` input, the Wardrobe on that person, the Location node on
`ort_data`, and on the Build Prompt node
the Series feeds, whatever sits on `pose`, `ausdruck`, `lighting`, `stil`,
`szene` and `text` (through reroutes too). Scene and template are the text of
whatever node is wired there — a primitive string, the scene save node. Where
nothing is wired, the one node of that type in the graph is taken, if there
is exactly one; with several and none wired, that section is left out rather
than guessed. The preview names the node each section goes to, or says it is
skipped. Only the top-level graph is searched, not the inside of subgraphs.

**The format.** The top level is English, like the custom-entry files; each
section is the node's state exactly as the node keeps it, so saving and loading
gives back the very same properties, and a section a file leaves out leaves
that node alone. A loaded shoot replaces the Series state as a whole (takes
included — they change the noise seed, so the same photos need them). Labels
can be the German keys a saved file carries or the English names the interface
shows; both load. Every label is checked against the lists — built-in entries,
your custom entries, and the prompt copies of custom entries the file carries
(as a workflow does), so a shoot using your own hat renders on a machine
without your JSON. An unknown label is listed in the preview and left out; the
rest still applies. [docs/shoot_example.json](shoot_example.json) is a
commented example.

| Route | |
|---|---|
| `GET /krea2/shoots` | the folder and the saved shoots |
| `GET /krea2/shoots/load?name=` | one shoot, checked: `{"shoot", "errors", "notes"}` |
| `POST /krea2/shoots/save` | `{"name": ..., "shoot": {...}}` checks and stores it |
| `POST /krea2/shoots/delete` | `{"name": ...}` |
| `POST /krea2/shoots/check` | `{"shoot": {...}}` checks a file without storing it |

### Director

One sentence becomes a whole shoot, through any chat LLM — ChatGPT, Claude,
Gemini, a local model. *Director …* in the Series panel:

1. Write the idea in one sentence ("a rainy afternoon in a Paris café,
   melancholic, black and white").
2. *Copy LLM prompt* (or *Open prompt* when the browser will not copy) and
   paste it into the chat. The prompt lists every built-in label per field,
   grouped by family, the shoot-file format with a worked example, the
   recipes, framings and mood arcs, and the rules the render tests found — at
   most five face fields, one to four outfits, the scene as a place seen.
3. Paste the answer back and *Import*. The preview shows what goes where and
   what was rejected; *Apply* (or *Apply anyway* without the rejected labels),
   and *Undo* if it is not what you meant.

The LLM only **chooses**; it does not write prompt text. The import accepts
built-in labels only (English or German), no free text except the scene, no
custom entries, nothing below 18 — so every wording that reaches the prompt is
one the render tests already saw. Clothing the LLM put on the person moves into
the wardrobe; free texts, the template and pose or expression sections are left
out with a note. The Director's series goes onto the current one like a recipe:
its plan replaces the axes and pools, while size, start number and takes stay.
The person keeps its *LoRA trigger* and *Reference*: the Director chooses the
look of the shoot, not who is in it.

**From a reference photo:** the second mode asks a chat model that takes images
to reverse-engineer an attached photo into the same file — the person as she
looks, the clothes, the light, the look, the location, a series plan around it.
The photo stays in the chat; only labels come back, and no pixels enter the
pipeline. That is on purpose: img2img carried neither the identity nor the
framing of a source picture ([measurements](measurements.md)).

**Offline draft:** without an LLM, the brief's words are matched against the
English labels — "long straight black hair", "golden hour", "85mm f/1.4",
"headshots", "10 photos". Rough, but label-only and checked by the same import.

| Route | |
|---|---|
| `GET /krea2/director/llm_prompt?brief=...&mode=brief\|photo` | the prompt, as plain text |
| `POST /krea2/director/import` | `{"answer": "..."}` — the chat answer as pasted (code fences and text around the JSON are fine): `{"shoot", "errors", "notes"}` |
| `POST /krea2/director/draft` | `{"brief": "..."}` — the offline draft, same answer |

### Custom entries

Your own list entries — a hat, a cut, a light setup, a look — come from JSON
files in `ComfyUI/user/krea2_presets/`. On the first start that folder is
created with `example.json.txt` in it: [the commented example](custom_entries_example.json)
with one entry per case. Rename a copy to `.json` and restart ComfyUI to try it. They appear in the lists of the
Person, Wardrobe, Pose, Expression, Lighting and Style nodes next to the
built-in ones, in the family they name or under *Custom*.

```json
{
  "format": "photoshoot-presets/1",
  "name": "My hats",
  "entries": [
    {"field": "headwear", "label": "Trilby", "prompt": "a narrow-brimmed straw trilby"},
    {"field": "topColor", "label": "Petrol", "prompt": "petrol blue", "hex": "#0f5e6b"},
    {"field": "hair", "label": "Shag", "prompt": "a choppy layered {c} shag cut"},
    {"builder": "lighting", "field": "setup", "label": "Neon tube",
     "prompt": "a single bare neon tube", "group": "Mood"}
  ]
}
```

| Key | |
|---|---|
| `field` | the field, as the built-in lists name it (`headwear`, `top`, `stimmung`, `setup`, `look`, ...) |
| `label` | what the list shows; must not clash with a built-in entry of that field |
| `prompt` | the English text that goes into the prompt, at most 300 characters |
| `builder` | `person` (default, also the Wardrobe), `pose`, `expression`, `lighting`, `style`, `location` |
| `group` | optional: the family to sort it into — as the English interface names it (`Hats`, `mood`) or by its German key; a new name makes a new family |
| `en` | optional: display name in the English interface (default: the label) |
| `hex` | optional: the swatch of a colour field (`#rrggbb`) |

`"dice": true` at the top of a file lets its entries into the dice and the
Series pools; without it a custom entry is only used when you pick it, so every
seed rolls what it always rolled. Hair may use `{c}` for the hair colour; other
placeholders are refused. Age and gender cannot be extended.

A file that does not parse, or an entry that breaks a rule, is skipped with a
message in the ComfyUI console; everything else in the file still loads. The
folder is read when ComfyUI starts. A file with problems shows as one line
in every Photoshoot panel, with a link to the messages. For scripts:

| Route | |
|---|---|
| `GET /krea2/custom` | the files loaded, the messages, the number of entries |
| `GET /krea2/custom/template` | every built-in entry in this format |
| `GET /krea2/custom/llm_prompt` | the prompt for a chat LLM (below) |
| `POST /krea2/custom/reload` | reads the folder again |
| `POST /krea2/custom/import` | `{"file": name, "content": {...}, "replace": false}` saves and loads a file; 409 if the name exists and `replace` is not set |
| `POST /krea2/custom/delete` | `{"file": name}` removes a file |

After a reload or import, reload the browser tab to see the new lists.

**With an LLM:** `http://<comfyui>/krea2/custom/llm_prompt` is a ready prompt
for any chat model — every field with its families, three built-in examples
of the wording, the names already taken, the rules and what the render tests
found about wording. Paste it, write what you want at the end ("12 hats from
the 1920s"), save the answer as a `.json` file in the folder. Render a test
image per entry before relying on it: a plausible wording does not always
hold.

A workflow remembers the prompt of every custom entry it uses, so it renders
the same on a machine without your file. `http://<comfyui>/krea2/custom/template`
shows every built-in entry in this format — a template to copy from, with the
exact field names.

### Assembling

**Photoshoot – Build Prompt** replaces the placeholders `{person1}` `{person2}`
`{person3}` `{camera}` `{pose}` `{expression}` `{scene}` `{style}` `{extra}` in
the prompt text, and `{person}` is short for `{person1}`. Placeholders left empty
leave no orphaned commas behind. `{extra}` is for optional extension packs; with
nothing wired to it, it has no effect.

Besides its `prompt` output the node returns the finished text as `ui` text,
so it lands in ComfyUI's history for that run. ComfyUI keeps the `ui` of every
node that runs, not only of output nodes (and a cached run hands its stored
`ui` back); the Series' contact sheet reads it from there. Nothing is shown on
the node itself.

The German spellings `{kamera}` `{ausdruck}` `{szene}` `{stil}` mean exactly the
same and keep working — the kit was German first, and prompts saved back then
still run. Mixing both in one text is fine.

**Recommended order** in the prompt text:

```text
{style}, {expression}, {camera}, {scene}, {lighting}, {person}, {pose}, {extra}
```

The expression comes right after the style (since 2.5.0).
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
