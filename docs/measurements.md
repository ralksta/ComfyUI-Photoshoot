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
