# Measurements

Numbers from actual runs, including the ones that overturned an earlier
conclusion. Kept because the reasoning behind several defaults rests on them.

**The second pass is indispensable.** The setup computes an image at 1088×1632,
upscales the latent by a factor of 1.5 and refines at denoise 0.44. Without the
refinement, compute time falls from 24.8 to 11.4 seconds, but the image is
unusably soft — latent upscaling invents no detail, it only pulls things apart.

**Dropping both passes is not the same as dropping the refinement.** The
sentence above tests the upscale without the refine, which is the bad case.
Bypassing the upscale as well, so the graph simply stops after pass one, gives
10.2 s against 21.5 s for the full graph, measured here against local Krea 2
weights on distinct seeds so nothing came from the node cache. The output is the
base resolution — 1328×1328 against 1632×2448 in that pair — and it is sharp,
because nothing was stretched. Pass one is the same node with the same inputs
either way, so the draft and the full render share a composition by
construction, not by luck.

**img2img does not stand in for a reference mechanism.** The most-asked-for
thing after release was feeding a picture instead of building a person. Tested
with core nodes only — LoadImage, VAEEncode, the Photoshoot prompt with the
person left out, Krea 2 Turbo, one source portrait, run 3 of the series at three
denoise levels:

| denoise | framing | identity |
| --- | --- | --- |
| 0.45 | unchanged — still the full-body source, not the close-up asked for | already gone; copper red came back brown |
| 0.65 | slightly turned, still full body | a different woman |
| 0.85 | two people embracing | nothing left |

Two reasons, and neither is fixable by tuning. The latent carries the source
image's geometry, so framing and aspect ratio cannot move — every close-up the
series asks for stays whatever the source was. And once the person description
is dropped, nothing anchors the identity at all: at low denoise the picture is
too close to the source to follow direction, at high denoise the direction wins
and the face goes with it. There is no setting in between.

So the pairing needs a model or adapter built for it — a LoRA, an IPAdapter, an
identity-preserving edit model. That is why no reference workflow ships here:
the dependency-free version does not work, and shipping it would only look like
it does.

**Paired with an identity-edit model, five of the six axes carry — the camera
does not.** Tested against [comfyui-krea2edit](https://github.com/lbouaraba/comfyui-krea2edit)
and the Krea 2 Identity Edit LoRA (r64), with the Person Builder unwired so the
prompt was framing, pose and expression only, one generated portrait as the
anchor:

| what was asked | what happened |
| --- | --- |
| identity | held in every run — face, freckles, hair, even the boots |
| pose | followed: torso turned away, looking back over the shoulder, walking |
| clothing, scene | followed ("change her outfit to a red raincoat" was exact) |
| framing | never followed; every close-up came back full body |

`ref_boost` is the dial that matters, and it governs pose, not likeness. At the
recommended 4.0 the model clung to the source and the pose barely moved; at 1.0
and 2.0 the direction landed and the identity still held. An imperative prefix
("Keep this person exactly as she is. Restage the photograph: …") changed
nothing measurable against the plain description, so the description style the
Photoshoot node already writes is fine.

Framing depends entirely on how the anchor is cropped, which took a second
round of tests to see. Against a full-body anchor nothing tightens the shot:
"close-up shot, with the focus on the neckline" does nothing, "Zoom in to a
close-up of her head and shoulders" does nothing, and "Reframe as a tight
close-up portrait, her head and shoulders filling the frame" moves the crop
slightly and no more — at `ref_boost` 2.0, so this is not the fidelity dial
either.

Crop that same anchor to head and shoulders and the axis comes alive. "Full
body shot, the whole figure from head to toe" pulled back to nearly the whole
figure; "extreme close-up shot, her face filling the frame" went the other way
and filled it. Identity held in both.

| anchor | asked for | result |
| --- | --- | --- |
| full body | close-up | refused |
| head and shoulders | full body | followed |
| head and shoulders | extreme close-up | followed |

The model opens up but will not move in. Widening invents body and room, which
is easy; tightening would mean inventing facial detail that is not in the
source pixels, which it declines to do. So the rule is: crop the anchor tight
and the whole camera axis works from there.

Nor does going the other way round work. Letting the Photoshoot series generate
the composition first and then swapping the person in through the two-image
mode splits into two failures: "replace the woman in the photograph" gives the
right person at a recomposed framing, and "put this person into this scene,
same close-up framing" keeps the framing and leaves the original person
untouched. That mode reads image 1 as a *place*, not as a composition to hold.

So the pairing carries all six axes, provided the anchor is a tight crop. Feed
it a full-body reference and you are stuck at full body; feed it head and
shoulders and framing, pose, expression, clothing and setting all take
direction while the person stays put.

**One run in five asked for an impossible pose.** With 18 postures, 14 arm
positions and 10 leg positions drawn independently, 101 of 500 runs combined
them into something no body can hold — `walking, arms wrapped around the knees`,
`standing, legs stretched out`, `leaning against a wall, legs tucked
underneath`. An image model does not refuse such a prompt; it satisfies both
halves partway and twists the torso to do it, so the symptom looks like bad
anatomy rather than a bad instruction. Found in a render, not in the code, for
exactly that reason. Coupling arms and legs to the posture the way tension
already was takes the same 500 runs to zero.

**Runs are bit-identical reproducible.** Two runs with identical seed and
identical prompt, submitted via `/prompt`, produced the same image pixel for
pixel — deviation exactly 0.00. An earlier measurement had produced 8.5 here; it
ran through the interface, where `control_after_generate` had advanced one of
the seeds. The measurement setup was at fault, not the pipeline.

That also means the A/B comparison of `euler_ancestral` against `euler` in the
second pass was misjudged: the measured difference of 8.0 was held against a
supposed noise floor of 8.5 and dismissed as "not measurable". The floor is at 0.
The question is open and would need measuring again.

**A fixed seed holds the setting together only by a fifth.** Two series of five
photos each, same counter values and therefore pairwise identical pose,
expression and camera; the only difference was the noise. Measured as mean
deviation in the outer frame (18 % all around, 59 % of the area — that is where
the setting lives, the figure sits in the middle):

| | Frame deviation |
|---|---|
| Noise per photo | 21.8 |
| Fixed series seed | 17.1 |
| Identical run | 0.0 |

The gain is visible: with a fixed seed the same headboard and the same candle
arrangement return, while with changing noise a gothic arched window appears one
time and a pointed-arch canopy the next. But measured, it is only 22 % less
deviation.

The remaining 78 % come from the **prompt**, not the seed. The camera is not the
driver — pairs with the same framing deviated just as much as pairs with
different framing (16.7 against 17.3). Even two photos with the same seed, the
same camera *and* the same basic posture, differing only in arms, legs and
expression, still came in at 15.7. Every change to the prompt text rearranges
the space.

That is what to expect from a distilled eight-step model: the seed only sets the
starting point, the conditioning steers every single step. Anyone who really
wants to nail down the setting has to put it into the latent
(`Set Reference Latent`) instead of describing it.

**A style at the end of the prompt cannot change the colour.** The first
question after 2.2.0 was how to get black and white. Tested on the example
workflow (Krea 2 Turbo, CFG 1, 8 + 4 steps), same photo number, the style text
swapped and the template changed, colour measured as the mean spread between
the largest and smallest RGB channel per pixel — 0 would be pure grey:

| style text | position in prompt | spread |
| --- | --- | --- |
| `editorial photography, 85mm, natural light, shallow depth of field` | last | 25.1 |
| `black and white photograph, monochrome, rich tonal range, …` | last | 26.0 |
| `black and white photograph, monochrome, grayscale, no colour, …` | last | 25.0 |
| `black and white photograph, monochrome, rich tonal range, …` | first | 2.6 |
| `black and white photograph, monochrome` | first | 4.9 |

At the end of the prompt the style does nothing to the colour, and stronger
wording does not help — the person block with its hair and eye colour comes
first and wins. At the front the same words produce a clean monochrome image.
The concern was the framing: the recommended order put the camera first so
that the person block would not win the frame area. A wide shot (run 7 of the
series) rendered with the style in front is still a wide shot, figure small
against the wall, room and window in frame. So the style goes first, the
camera second, and the person still after both.

**Nearly grey is not grey.** The monochrome render above (spread 2.6 on
average) still peaks at 21 on the lips, and the shorter wording peaks at 67
with six percent of the pixels above 20. Visible as a brown lipstick in an
otherwise grey image. That is what the Monochrome image node is for: the
prompt decides the tonality, the node removes what is left.

**Film stocks and brand looks do nothing; described properties do.** Eighteen
black and white wordings rendered on the same portrait (photo 1, camera held
at *Portrait*, Monochrome node on), measured as mean brightness, standard
deviation as contrast, and mean difference to a 2 px blur as grain:

| look | brightness | contrast | grain |
| --- | --- | --- | --- |
| classic | 98.8 | 78.1 | 2.17 |
| high contrast | 99.5 | 88.6 | 1.77 |
| film noir | 79.2 | 79.1 | 2.00 |
| grainy | 96.5 | 76.2 | 2.98 |
| high-key | 115.0 | 84.8 | 1.77 |
| sepia | 75.1 | 67.3 | 1.64 |
| fine art, soft, low-key, Leica Monochrom, Tri-X, HP5, Delta 3200, fashion, studio on white, platinum print, infrared | 107.8 – 113.6 | 81.4 – 83.2 | 1.77 – 1.94 |

The bottom row is eleven wordings that came out as one picture: "shot on
Ilford Delta 3200, heavy coarse grain" has less grain than "grainy 35mm film",
"studio portrait on white seamless background" kept the loft, "low-key, single
light source" is as bright as the rest. The model at CFG 1 reads what a look
*is* — contrast, grain, brightness, tone — and not what it is called. The
family therefore ships the seven that differ, and the Tri-X name survives only
as a hint on the grainy one.

The portraits also differ slightly from one look to the next although the
photo number and the noise seed are the same. That is the prompt at work, not
the style: a changed word rearranges the composition (see the 78 % above), and
nothing short of a reference latent pins it.

**Describing the famous look works where naming it did not.** Second pass on
the same portrait, six wordings that put the property at the head of the
phrase and leave the name out:

| wording (head of phrase) | derived from | brightness | contrast | grain | verdict |
| --- | --- | --- | --- | --- | --- |
| razor sharp fine detail …, grain-free | Leica Monochrom | 93.3 | 80.7 | 1.71 | kept — least grain of all |
| extremely grainy …, heavy coarse pushed grain | Delta 3200 | 88.1 | 72.0 | 3.44 | kept — most grain of all |
| infrared …, glowing white skin, black sky | infrared film | 77.7 | 84.1 | 2.11 | kept — black sky, rim glow |
| gritty grainy high contrast … | Tri-X | 100.3 | 79.6 | 2.96 | same as *grainy* (2.98) |
| gentle low contrast …, soft fine grain | HP5 | 98.3 | 74.7 | 2.10 | same as *classic* |
| matte flat low contrast monochrome print | platinum print | 95.1 | 78.9 | 1.80 | between classic and Leica |

"Shot on Ilford Delta 3200, heavy coarse grain" had measured 1.94 grain;
"extremely grainy black and white photograph, heavy coarse pushed film grain"
measures 3.44. Same properties, different position: the model takes the
adjectives on the head noun and lets a trailing list go. The three that
separated are in the family under their properties, with the film name as a
hint in the label.

**Colour looks, same test.** Sixteen wordings on the same portrait, no
Monochrome node; saturation is the mean HSV S, warmth the mean of R − B:

| look | brightness | contrast | saturation | warmth | verdict |
| --- | --- | --- | --- | --- | --- |
| Clean Digital (the neutral reference) | 94.7 | 82.7 | 82.7 | 22.4 | dropped — it is what no look gives you |
| Kodak Portra | 122.6 | 85.3 | 88.4 | 22.9 | kept — bright and soft |
| Fuji Pro 400H | 114.7 | 82.1 | 84.0 | 21.9 | dropped — a paler Portra |
| Cinestill 800T | 102.3 | 82.9 | 109.0 | 24.9 | kept — most saturated, halation |
| Kodachrome | 95.2 | 80.6 | 107.2 | 33.4 | kept — saturated and warm |
| Polaroid | 155.5 | 88.4 | 63.1 | 11.6 | kept — frame, washed out |
| Warm Golden | 91.2 | 81.2 | 98.1 | 35.3 | kept — warmest |
| Kühl entsättigt | 92.4 | 74.8 | 87.0 | 17.3 | kept — coolest, lowest contrast |
| Pastell | 122.2 | 92.1 | 76.4 | 21.7 | kept — bright, least saturated after Polaroid |
| Cross-Processed, Verblichener Film, Lomo, Editorial Grade, Teal & Orange, Kräftig & satt, Bleach Bypass | 92 – 108 | 77 – 85 | 82 – 89 | 18 – 25 | dropped — on the neutral image |

Teal & orange did not shift a single channel; Lomo drew a vignette and
nothing else. As with black and white, the model follows a described property
(bright, saturated, warm, cool, faded) and ignores a named treatment. The two
families *analog film* and *digital grade* collapsed into one *colour* family
with these seven.
