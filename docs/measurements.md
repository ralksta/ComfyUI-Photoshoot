# Measurements

Numbers from actual runs, including the ones that overturned an earlier
conclusion. Kept because the reasoning behind several defaults rests on them.

**The second pass is indispensable.** The setup computes an image at 1088×1632,
upscales the latent by a factor of 1.5 and refines at denoise 0.44. Without the
refinement, compute time falls from 24.8 to 11.4 seconds, but the image is
unusably soft — latent upscaling invents no detail, it only pulls things apart.

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
