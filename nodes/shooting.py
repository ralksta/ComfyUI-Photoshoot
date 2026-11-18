"""
Photoshoot - a whole series of images from one click.

The person stays, everything else moves on: framing, posture, expression and
aspect ratio. The node hands out a different sentence per run and drives the
queue itself, from a button in its own interface (js/shooting.mjs).

Why not a batch: the conditioning is computed once and brought up to the batch
size with repeat_to_batch_size (comfy/utils.py:859) - all images in a batch
necessarily share the same prompt. 50 different images need 50 runs.

Why not random: across 50 photos some combination would come up three times and
another never. Instead the photo number counts upwards and serves as the run
index. The widget is called "foto", not "seed": it used to be "seed", and the
first thing people did was set it to randomize and wonder why the series did
not count any more. The noise seed is derived from it (bildseed) and goes out
on its own output.
"""

import copy
import json
import re

from . import eigene
from . import expression_builder as EB
from . import lighting_builder as LB
from . import location_builder as OB
from . import person_builder as PeB
from . import pose_builder as PB
from . import style_builder as SB
from . import wardrobe as WB

NONE = "—"
ALLE = "alle"

# ─────────────────────────────────────────────────────────────────────────────
# Framing - the one list the kit did not have yet. On a real shoot this is the
# biggest difference between any two images.
#
# Wide framings have to demand the room explicitly (negative space, frame
# share). "wide shot, figure small" on its own loses against a long person
# block - hence the sharper wordings from medium shot outwards, and on top of
# that the photoshoot shortens the person block via detail_fuer_kamera().
# ─────────────────────────────────────────────────────────────────────────────
KAMERA = [
    ("Detail", "extreme close-up shot"),
    ("Nahaufnahme", "close-up shot"),
    ("Porträt", "portrait shot, head and shoulders"),
    # From here on there is more than the head in frame, and from here on the
    # note about proportions is needed: the Person Builder still weighs towards
    # the head - twelve fields for the face against eight for the body - and the
    # model hands out frame area roughly by that weighting, so without a
    # counterweight the head comes out too large. For the three tight framings
    # above the note would be pointless to actively harmful.
    ("Halbtotale", "medium shot, waist up, natural head-to-body proportions, "
                   "the figure does not fill the entire frame, visible space "
                   "around the subject"),
    ("Amerikanisch", "cowboy shot, from mid-thigh up, "
                     "realistic head-to-body proportions, clear space around "
                     "the figure"),
    ("Ganzkörper", "full body shot, the entire figure visible head to toe, "
                   "figure fills at most half the frame height, clear space "
                   "above the head and below the feet, realistic head-to-body "
                   "proportions with a proportionally small head"),
    ("Totale", "environmental wide establishing shot, the figure small in the "
               "middle ground of a large space, subject occupies less than a "
               "quarter of the frame, large surrounding environment and ample "
               "negative space, realistic head-to-body proportions"),
]

# Focus of the image. Appended to the framing rather than carried on its own
# output - both describe the same thing (what the image shows), and another
# placeholder in the prompt would buy nothing but wiring.
FOKUS = [
    ("Gesicht", "with the focus on the face"),
    ("Augen", "with the focus on the eyes"),
    ("Lippen", "with the focus on the lips"),
    ("Oberkörper", "with the focus on the upper body"),
    ("Dekolleté", "with the focus on the neckline"),
    ("Hände", "with the focus on the hands"),
    ("Taille", "with the focus on the waist and hips"),
    ("Beine", "with the focus on the legs"),
    ("Füße", "with the focus on the feet and shoes"),
    ("Rücken", "with the focus on the back"),
    ("Ganze Figur", "with the focus on the whole figure"),
    # On a wide or full-body shot: the room is the subject and the figure is
    # secondary - otherwise "focus on the whole figure" pulls the attention back
    # onto the person.
    ("Raum", "with the environment as the primary subject, the figure secondary"),
]

# Which focus fits which framing. A wide shot focused on the lips is a
# contradiction - as is a close-up of the feet, which would no longer be a
# close-up but a detail shot.
KAMERA_FOKUS = {
    "Detail":       ["Augen", "Lippen", "Hände", "Füße"],
    "Nahaufnahme":  ["Gesicht", "Augen", "Lippen", "Dekolleté"],
    "Porträt":      ["Gesicht", "Augen", "Dekolleté"],
    "Halbtotale":   ["Oberkörper", "Dekolleté", "Hände", "Taille", "Rücken", "Raum"],
    "Amerikanisch": ["Taille", "Beine", "Oberkörper", "Rücken", "Raum"],
    "Ganzkörper":   ["Raum", "Ganze Figur", "Beine", "Füße", "Rücken"],
    # "Room" first: on a wide shot the setting is the image, not the figure.
    # "Back" stays: a wide shot of a figure seen from behind is common. "Feet"
    # stays out - a wide shot focused on the feet contradicts itself.
    "Totale":       ["Raum", "Ganze Figur", "Beine", "Rücken"],
}

# Which placement fits which framing.
#
# The same coupling as for the focus, for the same reason - but here its absence
# does more damage: camera and placement both say something about distance.
# "portrait shot, head and shoulders" together with "farther back in the
# background" is not a skewed image but a contradiction, and the model resolves
# it by painting the person twice - once close in the portrait, once small in
# the background.
#
# For the three tight framings, therefore, only placements without a distance
# claim remain: "in the foreground" confirms the closeness, "by the window" is a
# location and not a distance. "Deep in the room" drops out everywhere except
# the wide shot, since it explicitly says "a small figure".
_RAUM_NAH = ["Vordergrund", "Am Fenster"]
_RAUM_MITTE = _RAUM_NAH + ["Bildmitte", "Im Türrahmen", "An der Raumkante",
                           "Zwischen Möbeln", "Gehend durch den Raum"]
_RAUM_WEIT = _RAUM_MITTE + ["Hintergrund", "An der Wand"]

KAMERA_RAUM = {
    "Detail":       list(_RAUM_NAH),
    "Nahaufnahme":  list(_RAUM_NAH),
    "Porträt":      list(_RAUM_NAH),
    "Halbtotale":   list(_RAUM_MITTE),
    "Amerikanisch": list(_RAUM_MITTE),
    "Ganzkörper":   list(_RAUM_WEIT),
    "Totale":       _RAUM_WEIT + ["Tief im Raum"],
}

# Aspect ratios. The concrete dimensions are computed rather than tabulated -
# that way the size can be chosen freely without maintaining nine pairs of
# numbers for every step.
RATIOS = {
    "1:1":  (1, 1),
    "4:5":  (4, 5),
    "5:4":  (5, 4),
    "3:4":  (3, 4),
    "4:3":  (4, 3),
    "2:3":  (2, 3),
    "3:2":  (3, 2),
    "9:16": (9, 16),
    "16:9": (16, 9),
}

# Selectable sizes, named after the edge length of the equivalent square. 1328
# corresponds to 1.76 MP and gives exactly 1088x1632 at 2:3 - the format used so
# far. Higher steps (1440 up to 2560) enable 2.0 MP up to 6.5 MP for Krea 2 / Flux.
KANTEN = [1024, 1152, 1280, 1328, 1440, 1536, 1664, 1792, 1920, 2048, 2304, 2560]
KANTE_STANDARD = 1328


def masse_fuer(ratio, kante):
    """Dimensions of an aspect ratio at a given square edge length.

    The pixel count stays the same across all ratios, so that compute time and
    memory use are constant over the series - otherwise a single format aborts
    with OOM in the middle of a 50-image run. Rounded to multiples of 16,
    because the VAE works in steps of 8 and 16 is on the safe side.
    """
    rw, rh = RATIOS.get(ratio, (1, 1))
    flaeche = float(kante) * float(kante)
    w = (flaeche * rw / rh) ** 0.5
    h = (flaeche * rh / rw) ** 0.5
    runde = lambda x: max(256, int(round(x / 16.0)) * 16)
    return (runde(w), runde(h))

# Which aspect ratio fits which framing. Without this coupling the full-body
# shot eventually lands in 16:9 landscape and the image is unusable. The
# extreme close-up has no 16:9 either: a face that wide fills the rest of the
# frame with a second, full-length figure - a diptych, two takes out of two.
# 4:5 took its place, so the list keeps its length and only the photos that
# had 16:9 change.
KAMERA_FORMATE = {
    "Detail":       ["1:1", "3:2", "4:5"],
    "Nahaufnahme":  ["1:1", "4:5"],
    "Porträt":      ["4:5", "1:1", "3:4"],
    "Halbtotale":   ["2:3", "3:4", "4:5"],
    "Amerikanisch": ["2:3", "3:4"],
    "Ganzkörper":   ["2:3", "3:4", "9:16"],
    "Totale":       ["3:2", "16:9", "1:1"],
}

# ─────────────────────────────────────────────────────────────────────────────
# Perspective - where the camera is (docs/ROADMAP.md, F4). The first family is
# the selfie: one arm holds the phone, which is the camera. The wording goes
# into the camera output right after the framing's own wording, before the
# focus - "portrait shot, head and shoulders, high-angle selfie, ..." - which
# is exactly the text the wording lab rendered (tools/wortlabor/selfie.json,
# "kamera_mit_ausschnitt"). Its own axis, off unless switched on, so every
# series from before comes out unchanged.
#
# Render-tested 2026-09-30 (three seeds each, pass 1, against the bare word)
# and adopted by the user: oben-a, auge-a, liegend-a, spiegel-a. "Selfie von
# oben" came out only slightly above eye level, not as a steep top-down shot;
# it was adopted as it is. Not adopted, back to the lab (selfie2.json): from
# below, over the shoulder.
# ─────────────────────────────────────────────────────────────────────────────
PERSPEKTIVE = [
    ("Selfie von oben", "high-angle selfie, phone held at arm's length above her head, "
                        "she looks up into the lens"),
    ("Selfie auf Augenhöhe", "eye-level selfie at arm's length, one arm reaching toward "
                             "the camera and out of the frame"),
    ("Selfie im Liegen", "selfie lying on her back on a bed, phone held above her face, "
                         "hair spread on the pillow"),
    ("Spiegel-Selfie", "mirror selfie, full-body reflection in a tall mirror, holding a "
                       "smartphone in front of her chest, looking at the phone screen"),
    # Classical camera angles (ROADMAP F4, appended 2026-11-17 after 2-round
    # wording lab render tests in winkel_props.json & winkel_props2.json, 3 seeds each).
    # Vogelperspektive succeeded on 2/3 seeds (1401181143, 42); seed 776610 stayed upright.
    ("Froschperspektive", "extreme low-angle shot from floor level tilted sharply up toward the ceiling"),
    ("Von oben", "steep high-angle shot looking sharply down at her from overhead, floor visible behind her shoulders as she looks up"),
    ("Vogelperspektive", "vertical overhead bird's-eye view straight down at the floor, top-down 90-degree angle looking directly down at her lying flat on the floor"),
    ("Dutch Angle", "Dutch angle shot, tilted diagonal horizon, camera rolled sideways for a slanted dynamic frame"),
]
PERSPEKTIVE_GRUPPEN = {
    "Selfie": ["Selfie von oben", "Selfie auf Augenhöhe", "Selfie im Liegen", "Spiegel-Selfie"],
    "Kamerawinkel": ["Froschperspektive", "Von oben", "Vogelperspektive", "Dutch Angle"],
}
SELFIES = tuple(PERSPEKTIVE_GRUPPEN["Selfie"])

# Which framings a perspective allows; a photo whose framing none of the
# chosen ones allows gets no perspective (as with the focus). A phone at arm's
# length reaches from the close-up to the waist; the mirror selfie is the one
# that shows the whole figure - its wording says "full-body reflection", and
# it was rendered as a full body shot.
_SELFIE_NAH = ["Nahaufnahme", "Porträt", "Halbtotale"]
PERSPEKTIVE_KAMERA = {
    "Selfie von oben": list(_SELFIE_NAH),
    "Selfie auf Augenhöhe": list(_SELFIE_NAH),
    "Selfie im Liegen": list(_SELFIE_NAH),
    "Spiegel-Selfie": ["Ganzkörper"],
    "Froschperspektive": ["Halbtotale", "Amerikanisch", "Ganzkörper", "Totale"],
    "Von oben": ["Nahaufnahme", "Porträt", "Halbtotale", "Amerikanisch", "Ganzkörper"],
    "Vogelperspektive": ["Nahaufnahme", "Porträt", "Halbtotale", "Amerikanisch", "Ganzkörper"],
    "Dutch Angle": ["Porträt", "Halbtotale", "Amerikanisch", "Ganzkörper", "Totale"],
}
# A phone's formats instead of the framing's: upright, as a phone holds it.
PERSPEKTIVE_FORMATE = {p: ["9:16", "4:5"] for p in SELFIES}
# Base postures a perspective allows, where its wording implies one: "lying
# on her back" does not go with lying on the stomach, and a reflection in a
# tall mirror is taken standing in front of it, not walking past. Every
# selfie also drops the postures that need both hands
# (pose_builder.arme_mit_freier_hand()). Overhead bird's-eye works with lying postures.
PERSPEKTIVE_HALTUNG = {
    "Selfie im Liegen": ["Auf dem Rücken liegend"],
    "Spiegel-Selfie": ["Stehend", "Stehend, Gewicht auf einem Bein"],
    "Vogelperspektive": ["Auf dem Rücken liegend", "Auf dem Bauch liegend",
                         "Auf der Seite liegend", "Bauchlage, Kinn in den Händen"],
}

# Framing-coupled focal length (ROADMAP F4, render-tested in winkel_props.json).
# Wide framings use 28mm f/5.6 for environmental sharpness; portraits use 85mm f/1.4;
# tight detail shots use 100mm macro. Inactive unless state["kameraOptik"] is true.
_OPTIK_WEIT = "shot on a 28mm wide-angle lens at f/5.6, deep depth of field, expansive room perspective"
_OPTIK_MITTE = "shot on a 50mm standard lens, natural perspective"
_OPTIK_PORTRAIT = "shot on an 85mm f/1.4 portrait lens wide open, shallow depth of field, creamy background bokeh"
_OPTIK_MAKRO = "shot on a 100mm f/2.8 macro lens, paper-thin depth of field, background melted into soft blur"
KAMERA_OPTIK = {
    "Totale": _OPTIK_WEIT,
    "Ganzkörper": _OPTIK_WEIT,
    "Amerikanisch": _OPTIK_MITTE,
    "Halbtotale": _OPTIK_MITTE,
    "Porträt": _OPTIK_PORTRAIT,
    "Nahaufnahme": _OPTIK_MAKRO,
    "Detail": _OPTIK_MAKRO,
}
# A selfie faces its phone: no back view, no profile, no turn away.
SELFIE_KOERPER = ["Frontal zur Kamera", "Leicht zur Seite gedreht", "Dreiviertelansicht"]
# Perspectives whose wording says where the eyes go, and the gaze that makes
# of the gaze field: "she looks up into the lens" is the camera; the mirror
# selfie looks at the phone screen, not the lens, so no gaze of its own.
PERSPEKTIVE_BLICK = {"Selfie von oben": "In die Kamera", "Spiegel-Selfie": None}

# Fields the series steps through, with where they come from.
#   quelle: "kamera" | "pose" | "ausdruck"
FELDER = (
    [("kamera", "kamera")]
    + [(cat, "pose") for cat in PB.FOLGE]
    + [(cat, "ausdruck") for cat in EB.FOLGE]
)

# Step sizes for the enumeration.
#
# The obvious approach would be (run * factor) % length with integer factors.
# That was measured and failed: fields with related list lengths march in
# lockstep. Of 66 field pairs, 18 were rigidly coupled - "koerper" and "mund"
# reached only 6 of 36 possible pairings, so the same body turn always arrived
# with the same mouth. Over a series that reads as mechanical.
#
# A Kronecker sequence instead: the step size is the fractional part of a square
# root, and therefore irrational. Irrational steps cannot, by definition, fall
# into a common beat. The arithmetic is integer over a fixed denominator, so
# that even large counter values stay exact - in floating point the result
# eventually drifts away and the series would no longer be reproducible.
#
# One prime per slot, and no slot may wrap around the list. Slots 0 .. 12 are
# FELDER, then format (len(FELDER) + 1), focus (+ 2) and outfit (+ 3). The list
# used to end at 53, sixteen primes, so the outfit's slot 16 wrapped to slot 0
# and shared the camera's step: with two outfits drawn per photo, one outfit
# only ever got the close framings and the other the wide ones. The primes from
# 59 on were appended for that; the first sixteen keep their places, so every
# other field of every series stays what it was.
#
# A new axis takes the next free slot after the outfit (len(FELDER) + 4, ...)
# and appends a prime here if it runs out. The set took + 4, the light
# + 5 (PLATZ_SET, PLATZ_LICHT below) and the perspective + 6
# (SLOT_PERSPEKTIVE). It must never be inserted into
# FELDER, PB.FOLGE or EB.FOLGE: that shifts every later slot and changes every
# series ever shot. The smoke test checks that no slot in use wraps.
_NENNER = 1 << 32
_WURZELN = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53,
            59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131]
# The perspective's slot, after the set (+ 4) and the light (+ 5).
SLOT_PERSPEKTIVE = len(FELDER) + 6

DEFAULT_STATE = {
    "anzahl": 12,
    # "set" does nothing without a Location node on ort_data, like "outfit"
    # without a wardrobe. "licht" is the one axis that is off unless switched
    # on: nothing upstream asks for it, and a series without it has to stay
    # what it was (no "licht" key reads as off, see licht_fuer()).
    "aktiv": {"kamera": True, "pose": True, "ausdruck": True, "format": True,
              "fokus": True, "rausch": True, "outfit": True, "set": True, "licht": False,
              "perspektive": False},
    # Applies when "rausch" is off: every photo in the series then gets this
    # seed instead of one of its own.
    "serienSeed": 0,
    # Where the series begins. The start button sets the photo counter to
    # this; the die next to it draws a new one. Only the interface reads it -
    # Python gets the photo number through the widget - but it is listed here
    # so that both sides know the same keys.
    "start": 1,
    # Pool per field: a family name, ALLE, or NONE for "do not use this field".
    "pools": {},
    # Re-shoots per photo number ("7": 2 = photo 7 was shot again twice). The
    # take goes into the noise seed, so a re-shoot keeps the plan - camera,
    # pose, expression - and gets a new picture. Take 0 is the seed as it has
    # always been, so older series come out unchanged.
    "takes": {},
    # Photo numbers marked as favourites in the contact sheet. Only the
    # interface reads them.
    "favoriten": [],
    # Framings in turn instead of drawn - see plane(). Superseded by
    # "reihenfolge" and still read when that is missing.
    "abdeckung": False,
    # "gezogen" | "reihum" | "weit_nah", None = from "abdeckung" - see
    # reihenfolge(). And the mood arc of the dramaturgy.
    "reihenfolge": None,
    "bogen": False,
    # Outfits from a wired wardrobe: "bloecke" (costume changes - the series
    # in as many equal parts as there are outfits, as on a real shoot) or
    # "gemischt" (drawn per photo). Without a wardrobe the axis does nothing.
    "outfitFolge": "bloecke",
    # The sets of a wired Location node, the same two ways (see set_fuer()).
    "setFolge": "bloecke",
    # The light axis (licht_fuer()): "je_set" (one setup per set, fitting it),
    # "tageszeit" (the day from morning to night over the series) or
    # "gemischt" (drawn per photo); and the setup families it draws from.
    "lichtFolge": "je_set",
    "lichtPool": ALLE,
    # Renders per planned photo, each a take with its own noise, and which take
    # counts per photo number. Both only for the interface; the take of a run
    # arrives through "takes".
    "takesJeFoto": 1,
    "wahl": {},
    # Draft: the run goes out with refine off (the "refine" output), so the
    # render subgraph skips its second pass - half the time, base resolution.
    # Not part of the plan: draft and final of photo 7 are the same photo, and
    # "Finish favourites" re-queues the keepers with it off.
    "entwurf": False,
    # First folder of the "dateiname" output (see dateiname()); the anchor set
    # uses "photoshoot/anchor".
    "ordner": "photoshoot",
    "kameras": [lbl for lbl, _ in KAMERA],  # Mehrfachauswahl
    "fokusse": [lbl for lbl, _ in FOKUS],  # Mehrfachauswahl
    # The perspectives the axis draws from, None = all; the axis is off
    # unless aktiv["perspektive"] is true (a missing key counts as off).
    "perspektiven": None,
    # Framing-coupled focal length (28mm-100mm) and hand props in the arm pool.
    # Both off by default so existing series and seeds stay unchanged.
    "kameraOptik": False,
    "requisiten": False,
    "requisitText": "",
    "groesse": KANTE_STANDARD,
    "festesFormat": "2:3",  # applies when "format" is off and nothing is wired in
    # Which outfits of a wired wardrobe the series uses: 0-based indices into
    # the Wardrobe's list, None = all of them. Set by the next round (see
    # naechste_runde()); the blocks and the mixed draw run over this subset.
    "outfitAuswahl": None,
    # Selects → next round (naechste_runde()). Photo numbers marked as rejects
    # in the contact sheet, the round this state is (1 = the first) and the
    # states of the earlier rounds, newest last, bounded by MAX_RUNDEN. Only
    # the interface and naechste_runde() read them; plane() never does.
    "verworfen": [],
    "runde": 1,
    "runden": [],
}


def _schritt(platz):
    """This field's step size as a fraction of _NENNER.

    sqrt of a prime is irrational, and the fractional part is distributed evenly
    over (0,1). Every field gets a different prime and therefore a beat of its
    own, commensurable with no other - as long as the slot does not wrap
    around _WURZELN (see there).
    """
    wurzel = _WURZELN[platz % len(_WURZELN)] ** 0.5
    return int((wurzel % 1.0) * _NENNER) | 1  # ungerade: nie ein Teiler von 2^32


def _waehle(labels, lauf, platz):
    """Draw one entry for this run."""
    n = len(labels)
    if not n:
        return None
    return labels[((lauf * _schritt(platz)) % _NENNER) * n // _NENNER]


# Gaze for a whole series (state["blick"]: a chip row under the expression axis
# of the Series panel, and videoflow's shooting). Without a mode plane() is
# unchanged.
# The JS preview plans the modes too, from the tables below that /krea2/presets
# sends (tests/plan.mjs holds both sides together). "blick" used to be drawn
# uniformly from all nine values on every photo, so a series asked for eye
# contact got it one photo in nine.
#   gemischt      as before
#   kamera        every photo looks into the camera
#   meist_kamera  two photos in three look into the camera, the third elsewhere
#   abgewandt     nobody looks into the camera
BLICK_MODI = ("gemischt", "kamera", "meist_kamera", "abgewandt")
BLICK_KAMERA = "In die Kamera"
# Not "at the other person": in a solo shoot it brought a second person into the
# picture (videoflow, ZWEITE_PERSON).
BLICK_NICHT_ABGEWANDT = (BLICK_KAMERA, "Zum Gegenüber")
# Moods whose own wording turns the eyes away ("gaze looking away", "eyes cast
# down", "averted") - they contradict "looking directly at the camera". Chosen by
# reading, not by a word list: "Herrisch" says "looking down at the viewer".
BLICK_WEG_STIMMUNGEN = ("Nachdenklich", "Abwesend", "Schüchtern", "Verlegen")
# Moods whose own wording looks into the lens ("blowing a kiss at the
# camera"): drawn only on a photo that looks there, and they take the camera
# gaze along.
BLICK_KAMERA_STIMMUNGEN = ("Kusshand",)
# The torso already turned over the shoulder says the gaze; not twice.
SCHULTER_KOERPER = "Über die Schulter gedreht"
SCHULTER_BLICK = "Über die Schulter"


# How the panel names the modes, with a tooltip each. German like every label;
# the English display text is in i18n.UI.
BLICK_NAMEN = {
    "gemischt": ("gemischt", "Jedes Foto zieht seinen Blick – mal in die Kamera, meist woandershin."),
    "kamera": ("in die Kamera", "Jedes Foto blickt in die Kamera."),
    "meist_kamera": ("meist Kamera", "Zwei von drei Fotos blicken in die Kamera, das dritte woandershin."),
    "abgewandt": ("abgewandt", "Niemand blickt in die Kamera."),
}


def blick_weg():
    """The gazes that do not look into the camera - what "abgewandt" and the
    third photo of "meist_kamera" draw from. Built-in entries only."""
    return [lbl for lbl, _ in EB.PRESETS["blick"] if lbl not in BLICK_NICHT_ABGEWANDT]


def blick_modus(state):
    m = (state or {}).get("blick")
    return m if m in BLICK_MODI and m != "gemischt" else None


def _blick_in_kamera(state, lauf):
    """Does this photo look into the camera under the series' gaze mode?"""
    m = blick_modus(state)
    return m == "kamera" or (m == "meist_kamera" and int(lauf) % 3 != 2)


def _pool(quelle, cat, state, kamera_label=None, haltung_label=None,
          stimmung_label=None):
    """The labels this field is allowed to draw from: _pool_ohne_selfie(),
    then perspective constraints (selfie hand/body and PERSPEKTIVE_HALTUNG)."""
    labels = _pool_ohne_selfie(quelle, cat, state, kamera_label, haltung_label, stimmung_label)
    perspektive = state.get("_perspektive")
    if not labels:
        return labels
    if cat == "haltung" and (perspektive in SELFIES or perspektive in PERSPEKTIVE_HALTUNG):
        fest = PERSPEKTIVE_HALTUNG.get(perspektive)
        if perspektive in SELFIES:
            # Only postures with a hand free for the phone; "im Liegen" lies on
            # its back. When the posture pool has none of those, the perspective
            # wins - it names the posture itself.
            frei = [l for l in labels if PB.arme_mit_freier_hand(l) and (fest is None or l in fest)]
            return frei or (list(fest) if fest else labels)
        return [l for l in labels if l in fest] or list(fest)
    if perspektive not in SELFIES:
        return labels
    if cat == "arme":
        frei = PB.arme_mit_freier_hand(haltung_label) if haltung_label else list(PB.EINE_HAND_FREI)
        return frei or labels
    if cat == "koerper":
        return [l for l in labels if l in SELFIE_KOERPER] or labels
    return labels


def _pool_ohne_selfie(quelle, cat, state, kamera_label=None, haltung_label=None,
                      stimmung_label=None):
    modul = PB if quelle == "pose" else EB
    gruppen = (PB.HALTUNG_GRUPPEN if quelle == "pose" else EB.STIMMUNG_GRUPPEN)
    gruppenfeld = "haltung" if quelle == "pose" else "stimmung"

    wahl = (state.get("pools") or {}).get(cat, ALLE)
    if wahl == NONE:
        return []
    # Custom entries only from a file marked "dice": true, as in the builders.
    alle = [lbl for lbl, _ in modul.PRESETS[cat]] + eigene.wuerfelbar(quelle, cat)
    # Selfie gestures, hand props and selfie expressions stay out unless asked for:
    # on any ordinary photo none of them enters the pool, so seeds stay unchanged.
    selfie = state.get("_perspektive") in SELFIES
    if cat == "arme":
        if not selfie:
            alle = [l for l in alle if l not in PB.SELFIE_GESTEN]
        if not state.get("requisiten") or selfie:
            alle = [l for l in alle if l not in PB.REQUISITEN]
    nur_auf_wahl = [l for l in alle if cat == "stimmung" and EB.nur_auf_wahl(l)]
    frei = [l for l in alle if l not in nur_auf_wahl]
    # A mood arc names the moods of this photo's stage (see plane()).
    if cat == "stimmung" and state.get("_stimmungen"):
        return [l for l in frei if l in state["_stimmungen"]] or frei
    if cat == gruppenfeld and wahl != ALLE:
        # One family, or several as a list - the next round narrows to the
        # families of the favourites, and those can be more than one.
        namen = [f for f in (wahl if isinstance(wahl, list) else [wahl]) if isinstance(f, str)]
        gewaehlt = [l for l in alle if any(l in gruppen.get(f, []) for f in namen)
                    or (selfie and l in nur_auf_wahl)]
        if cat == "stimmung" and state.get("_blick_weg"):
            gewaehlt = [l for l in gewaehlt if l not in BLICK_KAMERA_STIMMUNGEN] or gewaehlt
        # A photo that looks into the camera does not get a mood that looks away.
        if cat == "stimmung" and state.get("_blick_kamera"):
            return [l for l in gewaehlt if l not in BLICK_WEG_STIMMUNGEN] or gewaehlt
        return gewaehlt
    if not selfie:
        alle = frei
    if cat == "stimmung" and state.get("_blick_weg"):
        alle = [l for l in alle if l not in BLICK_KAMERA_STIMMUNGEN] or alle
    if cat == "stimmung" and state.get("_blick_kamera"):
        alle = [l for l in alle if l not in BLICK_WEG_STIMMUNGEN] or alle
    # ... and is not seen from behind: the back view drops every face field,
    # the gaze with it. Over the shoulder stays - that looks back into the camera.
    if cat == "koerper" and state.get("_blick_kamera"):
        alle = [l for l in alle if l != ABGEWANDT] or alle
    # Two constraints can apply to the same field, and the placement carries
    # both: the framing says how far away the figure may be (KAMERA_RAUM), the
    # posture says whether it can cross the room at all (HALTUNG_RAUM). They
    # have to intersect - answering with whichever comes first would let the
    # other one through.
    if cat == "raum" and kamera_label:
        erlaubt = KAMERA_RAUM.get(kamera_label)
        if erlaubt is not None:
            alle = [l for l in alle if l in erlaubt]
    # Placement, tension, arms and legs all depend on the base posture.
    # "haltung" comes first in FOLGE, so it is settled by the time these are
    # drawn.
    HALTUNG_KOPPLUNG = {"spannung": PB.HALTUNG_SPANNUNG,
                        "arme": PB.HALTUNG_ARME,
                        "beine": PB.HALTUNG_BEINE,
                        "raum": PB.HALTUNG_RAUM}
    tabelle = HALTUNG_KOPPLUNG.get(cat)
    if tabelle is not None and haltung_label:
        erlaubt = tabelle.get(haltung_label)
        if erlaubt is not None:
            return [l for l in alle if l in erlaubt] or alle
    # Eyes, mouth and brows against the mood - see EB.STIMMUNG_NUR_FUER.
    # "stimmung" is first in EB.FOLGE, so the family is settled here.
    if quelle == "ausdruck" and stimmung_label:
        familie = EB.familie_von(stimmung_label)
        gefiltert = [l for l in alle
                     if EB.passt_zur_stimmung(cat, l, familie)]
        return gefiltert or alle
    return alle


# Dramaturgy: mood arcs. Each is a list of stages, one per equal part of the
# series; a stage is a small group of related moods, so within a stage the mood
# is still drawn. Only moods that came out visibly in the expression tests
# (18.09., EileenX LoRA, emotion as subject) - quiet ones such as sad, disgust
# or contempt stayed nearly neutral and are left out. Names are German keys,
# translated in i18n.UI.
STIMMUNGSBOEGEN = {
    "Freude": [["Entspannt", "Gelassen"],
               ["Sanftes Lächeln", "Warmes Lächeln"],
               ["Breites Lachen", "Strahlend"],
               ["Triumphierend"]],
    "Drama": [["Schüchtern", "Verlegen"],
              ["Ängstlich", "Besorgt"],
              ["Panisch", "Schockiert"],
              ["Verzweifelt", "Weinend"]],
    "Dominanz": [["Selbstbewusst", "Konzentriert"],
                 ["Streng", "Kühl"],
                 ["Herrisch", "Fordernd"],
                 ["Verächtlich", "Herablassend"]],
}

# The mood as the subject of the sentence. Found in the expression tests: a
# mood only shows when it is the subject at the start - "a terrified woman
# screaming ..." - and the prompt is short; "..., a frightened expression"
# after a long person block stayed neutral whatever the wording. {wer} is the
# person's noun (woman/man/person), {poss} the possessive. Written for the
# arcs; the article is added by _artikel().
STIMMUNG_ALS_SUBJEKT = {
    "Entspannt": "relaxed {wer} with a calm easy expression, soft gaze, loose shoulders",
    "Gelassen": "serene {wer} with a peaceful composed face and a faint smile, calm eyes",
    "Sanftes Lächeln": "smiling {wer} with a soft gentle smile and warm eyes",
    "Warmes Lächeln": "{wer} smiling warmly, cheeks raised, eyes crinkled with warmth",
    "Breites Lachen": "joyful {wer} laughing out loud, head tilted back, wide open mouth showing teeth, eyes crinkled with laughter",
    "Strahlend": "beaming {wer} with a radiant wide smile showing teeth, eyes sparkling with joy",
    "Triumphierend": "ecstatic triumphant {wer} cheering with both fists raised in the air, mouth wide open in a victorious shout",
    "Schüchtern": "shy {wer} smiling bashfully, eyes cast down, chin tucked, blushing cheeks, lips pressed into a small smile",
    "Verlegen": "embarrassed {wer} covering {poss} mouth with one hand, flushed cheeks, eyes averted, sheepish smile",
    "Ängstlich": "frightened {wer} gasping in fear, eyes wide open showing the whites, brows raised and pulled together, lips stretched, trembling",
    "Besorgt": "worried {wer} biting {poss} lip, brows drawn together, anxious eyes, hands clasped at {poss} chest",
    "Panisch": "terrified {wer} screaming in sheer horror, eyes wide open showing white sclera, brows raised and drawn together, screaming open mouth, hands clutching {poss} hair",
    "Schockiert": "horrified {wer} staring in shock, both hands covering {poss} mouth, eyes wide open with dilated pupils",
    "Verzweifelt": "despairing {wer} screaming in anguish, head thrown back, eyes squeezed shut, hands clawing at {poss} hair",
    "Weinend": "heartbroken {wer} sobbing hysterically, mouth open in a wail, eyes squeezed, hands pressed to {poss} face",
    "Selbstbewusst": "confident {wer} with a self-assured half smile, chin slightly raised, steady direct gaze, one hand on {poss} hip",
    "Konzentriert": "focused {wer} with an intense concentrated stare, brows slightly lowered, lips pressed together",
    "Streng": "stern commanding {wer} glaring coldly, jaw clenched, lips pressed into a thin line, eyebrows lowered, arms crossed, chin raised",
    "Kühl": "aloof {wer} looking down {poss} nose with an icy unimpressed stare, chin raised, arms folded",
    "Herrisch": "imperious dominant {wer} pointing at the viewer, cold piercing stare, one eyebrow raised, chin lifted, mouth set in a hard line",
    "Fordernd": "demanding {wer} gesturing impatiently with an open palm, hard stare, eyebrows raised, lips tight",
    "Verächtlich": "contemptuous arrogant {wer} sneering, one corner of the mouth pulled up in a smug smirk, looking down {poss} nose with narrowed eyes",
    "Herablassend": "condescending {wer} with a patronizing smirk, one eyebrow raised, head tilted back, arms crossed",
}


# The same moods for an extreme close-up of the eyes or lips. A gesture in the
# subject - "cheering with both fists raised in the air" - outvoted the macro:
# four takes out of four came out as a full figure or a double exposure with
# the face pasted over it. Where the gesture is the main clause, the face
# carries the mood alone; for the rest stimmung_als_subjekt() drops the clauses
# with hands, arms and shoulders.
STIMMUNG_MAKRO = {
    "Triumphierend": "ecstatic triumphant {wer} shouting in victory, mouth wide open, eyes shining with joy",
    "Verlegen": "embarrassed {wer} with flushed cheeks, eyes averted, a sheepish smile",
    "Herrisch": "imperious dominant {wer} with a cold piercing stare, one eyebrow raised, chin lifted, mouth set in a hard line",
    "Fordernd": "demanding {wer} with a hard impatient stare, eyebrows raised, lips tight",
}
_GESTE = re.compile(r"\b(hands?|fists?|arms?|palms?|shoulders)\b")


def stimmung_als_subjekt(label, person_data, makro=False):
    """The mood of an arc written as the subject, or None. makro: for an
    extreme close-up of the face, without gestures out of frame."""
    text = STIMMUNG_ALS_SUBJEKT.get(label)
    if not text:
        return None
    if makro:
        text = STIMMUNG_MAKRO.get(label) or ", ".join(
            [t for i, t in enumerate(text.split(", ")) if i == 0 or not _GESTE.search(t)])
    try:
        p = json.loads(person_data) if isinstance(person_data, str) and person_data else (person_data or {})
    except (TypeError, ValueError):
        p = {}
    wer, poss = PeB.geschlecht(p if isinstance(p, dict) else {})
    return PeB._artikel(text.format(wer=wer, poss=poss))


def bogen_von(state):
    """The mood arc of this state, or None. True is the first arc (older
    states knew only one)."""
    b = state.get("bogen")
    # True and "Aufbau" are the one arc of the first version; its successor
    # is "Freude".
    if b is True or b == "Aufbau":
        return "Freude"
    return b if b in STIMMUNGSBOEGEN else None


def reihenfolge(state):
    """How the framings follow each other: "gezogen" (drawn by the Kronecker
    steps), "reihum" (coverage, each once in turn) or "weit_nah" (dramaturgy,
    from the widest to the closest). Older states only know "abdeckung"."""
    r = state.get("reihenfolge")
    if r in ("gezogen", "reihum", "weit_nah"):
        return r
    return "reihum" if state.get("abdeckung") else "gezogen"


def _position(state, lauf):
    """Where this photo stands in its series: 0 .. anzahl-1, and anzahl.

    Dramaturgy needs it, the drawn order does not. A photo outside the series
    (the counter ran on, a hand-set number) is clamped to the nearest end.
    """
    n = max(1, int(state.get("anzahl") or 1))
    i = int(lauf) - (max(1, int(state.get("start") or 1)) - 1)
    return min(max(i, 0), n - 1), n


def outfit_auswahl(state, anzahl):
    """The outfits of a wardrobe of `anzahl` this series uses, as indices:
    state["outfitAuswahl"] where it names outfits that exist, else all.
    With the default every index is in, so series without the key plan as
    they always did."""
    alle = list(range(int(anzahl or 0)))
    wahl = state.get("outfitAuswahl")
    if not isinstance(wahl, list):
        return alle
    return [k for k in alle if k in wahl] or alle


def _im_block(state, lauf, outfits, saetze=0):
    """Where this photo stands within its block: (0 .. size-1, size), or None
    when neither outfits nor sets are in blocks. Outfit block b holds the
    positions i with i * outfits // n == b (see outfit_fuer()), set blocks
    the same with the sets (set_fuer()); with both, a block is where outfit
    and set stay the same - the intersection of the two, since both split the
    same series. Only outfits in blocks give exactly what they always did."""
    aktiv = state.get("aktiv") or {}
    teile = []
    if outfits and aktiv.get("outfit", True) and state.get("outfitFolge") != "gemischt":
        teile.append(len(outfit_auswahl(state, outfits)))
    if saetze and aktiv.get("set", True) and state.get("setFolge") != "gemischt":
        teile.append(int(saetze))
    if not teile:
        return None
    i, n = _position(state, lauf)
    anfang, ende = 0, n
    for m in teile:
        b = i * m // n
        anfang = max(anfang, -(-b * n // m))
        ende = min(ende, -(-(b + 1) * n // m))
    return i - anfang, ende - anfang


def plane(state, lauf, outfits=0, saetze=0):
    """What this photo shows. A pure function - same run, same result.

    outfits: how many outfits a wired wardrobe holds; saetze: how many sets a
    wired Location node holds. In blocks, framings in turn and wide-to-close
    start over with every outfit and every set, as on a real shoot: otherwise
    one outfit got all the close-ups and the next all the full-body shots
    (12-photo test, three outfits) - and one set would only ever be seen wide."""
    aktiv = state.get("aktiv") or {}
    kamera_label = None
    pose_labels, ausdruck_labels = {}, {}
    ordnung = reihenfolge(state)
    i, n = _position(state, lauf)
    block = _im_block(state, lauf, outfits, saetze)
    # Mood arc: the stage follows the position in the series, in equal parts;
    # within a stage the mood is still drawn. Integer arithmetic only, so the
    # JS preview computes the same.
    bogen = bogen_von(state)
    if bogen and aktiv.get("ausdruck", True):
        stufen = STIMMUNGSBOEGEN[bogen]
        state = dict(state, _stimmungen=stufen[i * len(stufen) // n])
    if _blick_in_kamera(state, lauf):
        state = dict(state, _blick_kamera=True)
    elif blick_modus(state):
        # The gaze mode turns this photo away from the lens.
        state = dict(state, _blick_weg=True)
    perspektive = None

    for platz, (cat, quelle) in enumerate(FELDER):
        if platz == 1:
            # The perspective, once the framing is settled (FELDER starts with
            # the camera) and before the pose and the expression, which it
            # couples: a selfie has one hand on the phone.
            perspektive = perspektive_fuer(state, kamera_label, lauf)
            if perspektive:
                state = dict(state, _perspektive=perspektive)
                blick = PERSPEKTIVE_BLICK.get(perspektive, False)
                if blick == BLICK_KAMERA:
                    state["_blick_kamera"] = True
                elif blick is None:
                    state["_blick_weg"] = True
        if not aktiv.get(quelle, True):
            continue
        if quelle == "kamera":
            erlaubt = state.get("kameras") or [lbl for lbl, _ in KAMERA]
            if ordnung == "reihum":
                # Coverage: the chosen framings in turn, in their order from
                # wide-open KAMERA - every one once per len(erlaubt) photos. A
                # short series drawn by the Kronecker steps is even but may
                # miss a framing; this cannot.
                reihe = [lbl for lbl, _ in KAMERA if lbl in erlaubt] or erlaubt
                kamera_label = reihe[(block[0] if block else int(lauf)) % len(reihe)]
            elif ordnung == "weit_nah":
                # Dramaturgy: from the widest chosen framing to the closest,
                # spread over the series; the last photo is always the
                # closest. Rounded as floor(x + 0.5) in integers - Python and
                # JS round halves differently.
                reihe = [lbl for lbl, _ in reversed(KAMERA) if lbl in erlaubt] or erlaubt
                bi, bn = block or (i, n)
                if bn > 1:
                    k = (2 * bi * (len(reihe) - 1) + (bn - 1)) // (2 * (bn - 1))
                else:
                    k = 0
                kamera_label = reihe[k]
            else:
                kamera_label = _waehle(erlaubt, lauf, platz)
        else:
            # kamera_label is already settled here: the camera is the first
            # field in FELDER and the pose comes after it. The same holds for
            # haltung against spannung - FELDER follows PB.FOLGE, which puts the
            # base posture first and the body tension last.
            label = _waehle(_pool(quelle, cat, state, kamera_label,
                                  pose_labels.get("haltung"),
                                  ausdruck_labels.get("stimmung")), lauf, platz)
            (pose_labels if quelle == "pose" else ausdruck_labels)[cat] = label

    # Gaze mode of the series (see BLICK_MODI). Only when the field was drawn at
    # all - a pool of NONE, a switched-off expression axis or a back view keep
    # their "no gaze".
    modus = blick_modus(state)
    if modus and ausdruck_labels.get("blick"):
        platz = next(k for k, (c, q) in enumerate(FELDER) if c == "blick")
        weg = blick_weg()
        if pose_labels.get("koerper") == SCHULTER_KOERPER:
            weg = [l for l in weg if l != SCHULTER_BLICK]
        if state.get("_blick_kamera"):
            ausdruck_labels["blick"] = BLICK_KAMERA
        elif ausdruck_labels["blick"] not in weg:
            ausdruck_labels["blick"] = _waehle(weg, lauf, platz)
    # A perspective that says where the eyes go sets the gaze (the mirror
    # selfie: none, its wording looks at the screen), and a mood that blows
    # the camera a kiss looks into it.
    if ausdruck_labels.get("blick"):
        if perspektive in PERSPEKTIVE_BLICK:
            ausdruck_labels["blick"] = PERSPEKTIVE_BLICK[perspektive]
        elif ausdruck_labels.get("stimmung") in BLICK_KAMERA_STIMMUNGEN and not state.get("_blick_weg"):
            ausdruck_labels["blick"] = BLICK_KAMERA

    # The focus is drawn after the camera, because it depends on it: a wide
    # shot cannot focus on the lips.
    fokus_label = None
    if aktiv.get("fokus", True) and kamera_label:
        erlaubt = [f for f in KAMERA_FOKUS.get(kamera_label, [])
                   if not state.get("fokusse") or f in state["fokusse"]]
        # If nothing is left after filtering, this photo simply gets no focus
        # at all. Falling back to the full camera list would be more convenient
        # but would defeat the selection: someone who sets "legs and feet only"
        # would still get a neckline on the portrait.
        if pose_labels.get("koerper") == ABGEWANDT:
            erlaubt = [f for f in erlaubt if f not in FOKUS_GESICHT]
        # With a mood arc the close end of the series is about the face: a
        # detail shot there gets eyes or lips, not a macro of the boots (the
        # arc test ended "desperate" on the shoes).
        elif kamera_label == "Detail" and bogen_von(state) and aktiv.get("ausdruck", True):
            erlaubt = [f for f in erlaubt if f in FOKUS_GESICHT] or erlaubt
        fokus_label = _waehle(erlaubt, lauf, len(FELDER) + 2)

    return {"kamera": kamera_label, "fokus": fokus_label, "perspektive": perspektive,
            "pose": pose_labels, "ausdruck": ausdruck_labels}


def perspektive_fuer(state, kamera_label, lauf):
    """This photo's perspective, or None: drawn from the chosen ones
    (state["perspektiven"], None = all) that allow this framing
    (PERSPEKTIVE_KAMERA), on its own slot. None while the axis is off - it
    is off unless switched on."""
    if not (state.get("aktiv") or {}).get("perspektive"):
        return None
    alle = [lbl for lbl, _ in PERSPEKTIVE]
    erlaubt = [l for l in alle if l in (state.get("perspektiven") or alle)]
    if kamera_label:
        erlaubt = [l for l in erlaubt if kamera_label in PERSPEKTIVE_KAMERA.get(l, ())]
    return _waehle(erlaubt, lauf, SLOT_PERSPEKTIVE)


def outfit_fuer(state, lauf, anzahl):
    """Which of `anzahl` outfits this photo wears: an index, or None without a
    wardrobe or with the axis switched off. A pure function of the state, like
    plane(); the draw has its own slot after format and focus, so that series
    shot before the wardrobe keep every other value."""
    if not anzahl or not (state.get("aktiv") or {}).get("outfit", True):
        return None
    liste = outfit_auswahl(state, anzahl)
    if state.get("outfitFolge") == "gemischt":
        return _waehle(liste, lauf, len(FELDER) + 3)
    i, n = _position(state, lauf)
    return liste[i * len(liste) // n]


# ─────────────────────────────────────────────────────────────────────────────
# Sets and light (ROADMAP F2, F3). The sets come from a Location node on
# ort_data (location_builder.py), change over the series like outfits - in
# blocks or mixed - and each has a slot of its own; so does the light. Neither
# has a wording of its own: a set is the Location node's text, a light one of
# the 30 render-tested setups of the Lighting node (lighting_builder.py).
# ─────────────────────────────────────────────────────────────────────────────
PLATZ_SET = len(FELDER) + 4
PLATZ_LICHT = len(FELDER) + 5
SET_FOLGEN = ("bloecke", "gemischt")
LICHT_FOLGEN = ("je_set", "tageszeit", "gemischt")

# Which setups fit which sets, read off their wording. Outdoors only: the
# ones that name the sun, the sky or the time of day as the source - a
# softbox studio at golden hour is a contradiction the model resolves by
# dropping one of the two. Indoors only: the ones that name a studio or a
# window. The rest (mood lights, the classic portrait patterns, dappled light
# "through window blinds and leaves") fit either. A set of no known family
# takes every setup.
LICHT_NUR_DRAUSSEN = ("Golden Hour", "Blue Hour / Dämmerung", "Bewölktes Tageslicht",
                      "Hartes Sonnenlicht", "Sonnenuntergang / Abendrot", "Morgendämmerung",
                      "Mondlicht (Nacht)")
LICHT_NUR_DRINNEN = ("Softbox diffuses Licht", "High-Key Studio", "Low-Key Moody",
                     "Studio-Ringlicht", "Cinematic Fensterlicht", "Jalousie-Schatten (Gobo)")

# The day over the series: five stages in equal parts, like a mood arc; within
# a stage the setup is drawn from those that fit the photo's set. Each stage
# has an outdoor and an indoor way to say it (sun or window, moon or candle),
# so every set gets its time of day. Names are German keys (i18n.UI).
TAGESLAUF = [
    ("Morgen", ["Morgendämmerung", "Cinematic Fensterlicht"]),
    ("Mittag", ["Hartes Sonnenlicht", "Bewölktes Tageslicht", "Cinematic Fensterlicht"]),
    ("Goldene Stunde", ["Golden Hour", "Sonnenuntergang / Abendrot", "Schattenspiel / Blätter"]),
    ("Blaue Stunde", ["Blue Hour / Dämmerung", "Kerzenlicht / Warmes Glühen"]),
    ("Nacht", ["Mondlicht (Nacht)", "Neon Akzente", "Flammenschein / Kaminlicht"]),
]

# Framings that see only what is behind the head: the set in its short form
# (location_builder.kurzform()). A macro sees none of it, and a room in the
# prompt pulled the camera back the way the full pose did (DETAIL_SICHTBAR).
SET_KURZ = ("Nahaufnahme", "Porträt")
SET_WEG = ("Detail",)


def set_fuer(state, lauf, anzahl):
    """Which of `anzahl` sets this photo is taken in: an index, or None without
    a Location node or with the axis switched off. Blocks split the series in
    equal parts in the node's order (loft -> street -> cafe); mixed draws per
    photo from the set's own slot. Pure, like outfit_fuer()."""
    if not anzahl or not (state.get("aktiv") or {}).get("set", True):
        return None
    liste = list(range(int(anzahl)))
    if state.get("setFolge") == "gemischt":
        return _waehle(liste, lauf, PLATZ_SET)
    i, n = _position(state, lauf)
    return liste[i * len(liste) // n]


def licht_passt(label, draussen):
    """Does this setup fit a set that is outdoors (True), indoors (False) or
    of no known family (None)?"""
    if draussen is True:
        return label not in LICHT_NUR_DRINNEN
    if draussen is False:
        return label not in LICHT_NUR_DRAUSSEN
    return True


def licht_pool(state):
    """The setups the light axis draws from: the built-in 30, or the families
    of state["lichtPool"] (one name or a list). Built-in only - every one is
    render-tested; custom setups stay in the Lighting node."""
    alle = [lbl for lbl, _ in LB.PRESETS["setup"]]
    wahl = state.get("lichtPool", ALLE)
    namen = [f for f in (wahl if isinstance(wahl, list) else [wahl])
             if isinstance(f, str) and f in LB.LICHT_GRUPPEN]
    if not namen:
        return alle
    return [l for l in alle if any(l in LB.LICHT_GRUPPEN[f] for f in namen)] or alle


def licht_fuer(state, lauf, draussen=()):
    """The lighting setup of this photo, as a label, or None while the light
    axis is off (the default: a state without "licht" plans as it always did).

    draussen: per set of the wired Location node, whether it is outdoors
    (location_builder.draussen()); empty without one. The photo's set
    (set_fuer()) decides which setups fit:
      je_set     one setup per set, the same on every photo of it - drawn by
                 the set's number, so a set keeps its light when the series
                 is re-planned; without sets, one setup for the series
      tageszeit  TAGESLAUF over the series, the stage by position
      gemischt   drawn per photo
    """
    if not (state.get("aktiv") or {}).get("licht", False):
        return None
    draussen = list(draussen or [])
    k = set_fuer(state, lauf, len(draussen))
    d = draussen[k] if k is not None else None
    folge = state.get("lichtFolge")
    if folge == "tageszeit":
        i, n = _position(state, lauf)
        stufe = TAGESLAUF[i * len(TAGESLAUF) // n][1]
        return _waehle([l for l in stufe if licht_passt(l, d)] or stufe, lauf, PLATZ_LICHT)
    pool = licht_pool(state)
    liste = [l for l in pool if licht_passt(l, d)] or pool
    if folge == "gemischt":
        return _waehle(liste, lauf, PLATZ_LICHT)
    return _waehle(liste, (k or 0) + 1, PLATZ_LICHT)


def szene_fuer(satz, kamera_label):
    """A set's text for this framing: whole from the medium shot out, its
    short form for close-up and portrait, nothing for a macro."""
    if not satz:
        return ""
    if kamera_label in SET_WEG:
        return ""
    if kamera_label in SET_KURZ:
        return satz.get("kurz") or ""
    return satz.get("text") or ""


def format_fuer(kamera_label, lauf, state, perspektive=None):
    """Which aspect ratio this photo gets. A selfie takes the phone's
    formats (PERSPEKTIVE_FORMATE) instead of the framing's."""
    if not state.get("aktiv", {}).get("format", True):
        return state.get("festesFormat") or "2:3"
    erlaubt = (PERSPEKTIVE_FORMATE.get(perspektive) or KAMERA_FORMATE.get(kamera_label)
               or list(RATIOS))
    # Its own slot in the step-size list, so the ratio does not move in
    # lockstep with the camera.
    return _waehle(erlaubt, lauf, len(FELDER) + 1)


def masse(kamera_label, lauf, state, perspektive=None):
    """Image dimensions for this photo - coupled to the framing."""
    kante = int(state.get("groesse") or KANTE_STANDARD)
    return masse_fuer(format_fuer(kamera_label, lauf, state, perspektive), kante)


def _wert(modul, cat, label):
    for lbl, wert in modul.PRESETS[cat]:
        if lbl == label:
            return wert
    return eigene.wert("pose" if modul is PB else "ausdruck", cat, label)


def bildseed(lauf, state=None):
    """Noise seed for this photo, derived from the run counter.

    Not the counter itself: 0, 1, 2 sit close together in noise space and give
    images that resemble each other. The factor is Knuth's scattering constant
    for 32 bits (2^32 / the golden ratio); it pulls consecutive numbers far
    apart and is still unique - photo 7 always gets the same seed, so the series
    stays recoverable.

    A re-shoot (state["takes"], counted per photo number) shifts the seed, so
    the same plan comes out as a new picture; take 0 changes nothing.

    When the "rausch" axis is switched off, the whole series gets the same seed.
    That holds the setting together: the scene text describes "a gothic bed of
    dark wood", not *this* bed - everything it leaves open the model invents out
    of the noise, and with new noise it comes out differently. Pose, expression
    and camera keep varying, since those come from the prompt and not from the
    seed.
    """
    state = state or {}
    take = take_von(state, lauf)
    if not (state.get("aktiv") or {}).get("rausch", True):
        basis = int(state.get("serienSeed") or 0)
    else:
        basis = int(lauf) * 2654435761
    # A re-shoot moves the seed by a second odd constant per take, far away in
    # noise space from both the original and the neighbouring photos.
    return (basis + take * 1597334677) % (1 << 31)


def take_von(state, lauf):
    """The take of this photo (0 = first shot), as bildseed() reads it."""
    return int(((state or {}).get("takes") or {}).get(str(int(lauf) + 1), 0) or 0)


def dateiname(state, lauf):
    """A file name prefix that says which photo it is, for Save Image.

    <ordner>/s<start>/<photo>_t<take>[_draft], e.g. photoshoot/s0500/507_t1_draft.
    The series is its start number: that is what "New series" changes and
    what brings a series back when typed in again, and every photo of it
    keeps it however often it is re-shot or finished. The photo number is the
    one on the contact sheet, padded to the widest number of the series so
    the files sort in order; the take counts from 1, as the contact sheet
    shows it. Save Image appends its own counter, so a second render of the
    same take does not overwrite the first.
    """
    state = state or {}
    ordner = "/".join(t for t in str(state.get("ordner") or "").replace("\\", "/").split("/")
                      if t and t not in (".", "..")) or "photoshoot"
    start = max(1, int(state.get("start") or 1))
    n = max(1, int(state.get("anzahl") or 1))
    breite = max(2, len(str(start + n - 1)))
    name = "%s/s%04d/%0*d_t%d" % (ordner, start, breite, int(lauf) + 1,
                                  take_von(state, lauf) + 1)
    return name + ("_draft" if state.get("entwurf") else "")


def _ausdruck_fuer_detail(werte, detail):
    """Couple the expression to how wide the framing is.

    On a wide shot, lashes and brow shape are invisible, yet they still load the
    prompt with face tokens and pull the composition back onto the head.
    Identity = mood only; figure = mood plus coarse expression; full =
    everything.
    """
    if detail == PeB.DETAIL_IDENTITAET:
        keep = {"stimmung"}
    elif detail == PeB.DETAIL_FIGUR:
        keep = {"stimmung", "blick", "mund", "kopf"}
    else:
        return werte
    return {cat: (werte.get(cat) if cat in keep else None) for cat in EB.FOLGE}


# A face that is turned away cannot carry an expression. The mood may still
# read through posture and shoulders, so it stays; eyes, gaze, mouth and brows
# go, and the focus may not sit on the face either.
ABGEWANDT = "Von hinten"
FOKUS_GESICHT = {"Gesicht", "Augen", "Lippen"}
GESICHTSWOERTER = ("smile", "smiling", "grin", "teeth", "eyes", "gaze", "lips",
                   "mouth", "brow", "frown", "pout", "stare", "wink")


def _ausdruck_fuer_koerper(werte, koerper_label):
    """Drop the facial detail when the subject is seen from behind.

    Same mechanism as _ausdruck_fuer_detail, different trigger. Without it, one
    run in six asked for a back view wearing a half-smile and looking into the
    camera - the model answers by twisting the body far enough to show both,
    which is where the spare limbs came from.
    """
    if koerper_label != ABGEWANDT:
        return werte
    # The mood may stay when it reads through posture and shoulders. It may not
    # when its own wording names something on the face - "a beaming, radiant
    # smile" behind a back view is the same contradiction one level up. Decided
    # on the text rather than by taste, so new moods are covered automatically.
    stimmung = werte.get("stimmung") or ""
    if any(w in stimmung.lower() for w in GESICHTSWOERTER):
        stimmung = None
    return {cat: (stimmung if cat == "stimmung" else None) for cat in EB.FOLGE}


# Series recipes: one click sets the axes for a kind of shoot. Each is a patch
# on the state - count, switches, pools, framings, focus, ratio, coverage;
# start number, size, takes and favourites stay as they are. Names and
# descriptions are German keys, translated like every other label (i18n.UI).
_ALLE_AN = {"kamera": True, "pose": True, "ausdruck": True, "format": True,
            "fokus": True, "rausch": True, "perspektive": False}
REZEPTE = [
    ("Editorial", "Alles variiert: jede Einstellung, Pose, Stimmung und jedes Format.",
     {"anzahl": 12, "aktiv": dict(_ALLE_AN), "pools": {}, "kameras": None,
      "fokusse": None, "abdeckung": False, "reihenfolge": "gezogen", "bogen": False}),
    # Full body and portrait in turn: the test render had cowboy shot and full
    # body next to each other, and they came out nearly the same.
    ("Lookbook", "Ganzkörper und Porträt im Wechsel, stehend, ruhig, 2:3 und ein Seed für den gleichen Ort.",
     {"anzahl": 8, "aktiv": dict(_ALLE_AN, format=False, fokus=False, rausch=False),
      "pools": {"haltung": "stehend", "stimmung": "ruhig"},
      "kameras": ["Porträt", "Ganzkörper"], "fokusse": None,
      "festesFormat": "2:3", "abdeckung": True, "reihenfolge": "reihum", "bogen": False}),
    ("Headshots", "Porträt und Nahaufnahme, freundlich, Schwerpunkt Gesicht und Augen, ohne Pose.",
     {"anzahl": 8, "aktiv": dict(_ALLE_AN, pose=False),
      "pools": {"stimmung": "freundlich"}, "kameras": ["Nahaufnahme", "Porträt"],
      "fokusse": ["Gesicht", "Augen"], "abdeckung": False, "reihenfolge": "gezogen", "bogen": False}),
    ("Schuhe", "Detail und Ganzkörper im Wechsel, stehend, Schwerpunkt Füße, ohne Ausdruck.",
     {"anzahl": 8, "aktiv": dict(_ALLE_AN, ausdruck=False), "pools": {"haltung": "stehend"},
      "kameras": ["Detail", "Ganzkörper"], "fokusse": ["Füße"], "abdeckung": True,
      "reihenfolge": "reihum", "bogen": False}),
    ("Test-Bogen", "Sieben Fotos, jede Kameraeinstellung genau einmal – zum Prüfen einer Person.",
     {"anzahl": 7, "aktiv": dict(_ALLE_AN), "pools": {}, "kameras": None,
      "fokusse": None, "abdeckung": True, "reihenfolge": "reihum", "bogen": False}),
    # Selfie mode (ROADMAP F4): the four framings a selfie allows in turn, so
    # the full body - the mirror selfie - comes up too; phone formats, gaze
    # mostly into the lens, friendly moods plus the selfie ones. Focus off,
    # so the camera text is the framing and the perspective as rendered.
    ("Selfie", "Selfies: Nahaufnahme bis Halbtotale mit dem Handy in der Hand, Ganzkörper im Spiegel, 9:16 oder 4:5, Blick meist in die Kamera.",
     {"anzahl": 8, "aktiv": dict(_ALLE_AN, fokus=False, perspektive=True),
      "pools": {"stimmung": "freundlich"},
      "kameras": ["Nahaufnahme", "Porträt", "Halbtotale", "Ganzkörper"], "fokusse": None,
      "perspektiven": list(PERSPEKTIVE_GRUPPEN["Selfie"]), "blick": "meist_kamera",
      "abdeckung": True, "reihenfolge": "reihum", "bogen": False}),
    ("Anker-Set", "Sechs Referenzfotos einer Person: ein Seed, festes Format 2:3, ruhige Stimmung, jede Einstellung einmal.",
     {"anzahl": 6, "aktiv": dict(_ALLE_AN, format=False, rausch=False),
      "pools": {"stimmung": "ruhig"},
      "kameras": ["Nahaufnahme", "Porträt", "Halbtotale", "Amerikanisch", "Ganzkörper", "Totale"],
      "fokusse": None, "festesFormat": "2:3", "abdeckung": True,
      "reihenfolge": "reihum", "bogen": False}),
]


# ─────────────────────────────────────────────────────────────────────────────
# Selects → next round. The loop a photographer works in: shoot, select,
# reshoot. The favourites of a round say what worked, so the next round draws
# only from their framings, posture families, mood families, focus areas and
# outfits - and starts at a new photo number, so it brings new pictures of
# the same kind instead of the same pictures again.
#
# Computed here only; the panel asks for it through /krea2/serien/naechste_runde
# (api.py) and applies the answer, so there is no second copy in JS. It works
# on the plan, not on the pictures: plane() is replayed for every photo of the
# series, which is exactly what was rendered as long as the settings did not
# change since - the contact sheet shows pictures only under that condition
# too.
# ─────────────────────────────────────────────────────────────────────────────
MAX_RUNDEN = 5


def _nummern_im_bogen(state, nummern):
    """The photo numbers among `nummern` that belong to this series (start ..
    start + anzahl - 1), sorted, each once. A favourite from an earlier start
    number was shot under a different plan position; replaying it here would
    describe a photo that never existed."""
    start = max(1, int(state.get("start") or 1))
    n = max(1, int(state.get("anzahl") or 1))
    aus = set()
    for x in nummern or []:
        try:
            nr = int(x)
        except (TypeError, ValueError):
            continue
        if start <= nr < start + n:
            aus.add(nr)
    return sorted(aus)


def _familie_von(quelle, label):
    gruppen = PB.HALTUNG_GRUPPEN if quelle == "pose" else EB.STIMMUNG_GRUPPEN
    return next((f for f, labels in gruppen.items() if label in labels), None)


def _familien_im_pool(quelle, wahl):
    """The families a pool currently allows, in table order, or None when the
    pool names none this code knows (then the next round leaves it alone).
    "All" leaves out the opt-in families (EB.NUR_AUF_WAHL): they are not in
    that pool, a selfie only adds them to it."""
    gruppen = PB.HALTUNG_GRUPPEN if quelle == "pose" else EB.STIMMUNG_GRUPPEN
    if wahl is None or wahl == ALLE:
        return [f for f in gruppen if f not in EB.NUR_AUF_WAHL]
    namen = wahl if isinstance(wahl, list) else [wahl]
    return [f for f in gruppen if f in namen] or None


def _eingrenzen(aktuell, wert_von, favoriten, verworfen, uebrige):
    """One axis of the next round: the values of `aktuell` (in its order) the
    favourites show - all of them without favourites - minus the values that
    only rejected photos show. `wert_von(nr)` is a photo's value on this axis.
    None when the axis stays as it is: no favourite has a value on it, or the
    result would be empty.

    A value counts as rejected only when no other photo of the series that
    was kept shows it: one bad lying pose does not strike lying poses while a
    second one is unmarked, and a favourite always wins."""
    gut = {wert_von(nr) for nr in favoriten} - {None}
    if favoriten and not gut:
        return None
    behalten = {wert_von(nr) for nr in uebrige} - {None}
    weg = {wert_von(nr) for nr in verworfen} - behalten - {None}
    neu = [x for x in aktuell if (not gut or x in gut) and x not in weg]
    return neu or None


def naechste_runde(state, outfits=0, saetze=0):
    """The state of the next round, or None without selects.

    state: the Series state of the round just shot; outfits: how many outfits
    the wired wardrobe holds (0 without one), saetze how many sets the wired
    Location node holds, as plane() takes them. The sets and the light are
    not narrowed: a round keeps its places.

    From the favourites in this series (state["favoriten"]), and the rejects
    (state["verworfen"]) where only those show something:
      - framings (kameras) narrowed to theirs; the ratio follows the framing
        by itself (KAMERA_FORMATE). A single framing stays a single framing:
        the selects said so, and pose, mood, focus and ratio still vary;
      - posture and mood pools narrowed to their families (one family as its
        name, several as a list, all of them as ALLE). A mood arc stays as it
        is: it is a dramaturgy over positions, and the pool has no say under
        it;
      - focus areas (fokusse) narrowed to theirs;
      - with a wardrobe, the outfits (outfitAuswahl) narrowed to theirs.
    An axis that is switched off, a pool of NONE, or an axis on which no
    favourite has a value stays as it is. Order, count, size, gaze mode and
    the series seed stay too.

    The new round starts right after this one (start + anzahl), so every
    photo number is new and the round is reproducible: the same selects give
    the same next round. Favourites, rejects, takes and chosen takes belong to
    the old round and are cleared; the old state goes onto state["runden"]
    (at most MAX_RUNDEN), from where the panel brings it back.
    """
    state = dict(state or {})
    favoriten = _nummern_im_bogen(state, state.get("favoriten"))
    verworfen = [nr for nr in _nummern_im_bogen(state, state.get("verworfen"))
                 if nr not in favoriten]
    if not favoriten and not verworfen:
        return None
    aktiv = state.get("aktiv") or {}
    an = lambda achse: aktiv.get(achse, True)
    start = max(1, int(state.get("start") or 1))
    n = max(1, int(state.get("anzahl") or 1))
    plaene = {nr: plane(state, nr - 1, outfits, saetze) for nr in range(start, start + n)}
    uebrige = [nr for nr in plaene if nr not in verworfen]
    grenze = lambda aktuell, wert_von: _eingrenzen(aktuell, wert_von, favoriten,
                                                   verworfen, uebrige)
    neu = dict(state)
    pools = dict(state.get("pools") or {})

    if an("kamera"):
        alle = [lbl for lbl, _ in KAMERA]
        aktuell = [l for l in alle if l in (state.get("kameras") or alle)]
        k = grenze(aktuell, lambda nr: plaene[nr]["kamera"])
        if k is not None:
            neu["kameras"] = None if k == alle else k

    if aktiv.get("perspektive"):
        alle = [lbl for lbl, _ in PERSPEKTIVE]
        aktuell = [l for l in alle if l in (state.get("perspektiven") or alle)]
        k = grenze(aktuell, lambda nr: plaene[nr].get("perspektive"))
        if k is not None:
            neu["perspektiven"] = None if k == alle else k

    if an("fokus"):
        alle = [lbl for lbl, _ in FOKUS]
        aktuell = [l for l in alle if l in (state.get("fokusse") or alle)]
        f = grenze(aktuell, lambda nr: plaene[nr]["fokus"])
        if f is not None:
            neu["fokusse"] = None if f == alle else f

    for quelle, feld in (("pose", "haltung"), ("ausdruck", "stimmung")):
        wahl = pools.get(feld, ALLE)
        if not an(quelle) or wahl == NONE or (feld == "stimmung" and bogen_von(state)):
            continue
        aktuell = _familien_im_pool(quelle, wahl)
        if aktuell is None:
            continue
        # A label without a built-in family (a custom entry) cannot be kept
        # by family: narrowing would drop exactly what was liked.
        if any(plaene[nr][quelle].get(feld) and not _familie_von(quelle, plaene[nr][quelle][feld])
               for nr in favoriten):
            continue
        fam = grenze(aktuell, lambda nr: _familie_von(quelle, plaene[nr][quelle].get(feld)))
        if fam is not None:
            pools[feld] = ALLE if fam == _familien_im_pool(quelle, ALLE) else fam[0] if len(fam) == 1 else fam
    neu["pools"] = pools

    if outfits and an("outfit"):
        aktuell = outfit_auswahl(state, outfits)
        o = grenze(aktuell, lambda nr: outfit_fuer(state, nr - 1, outfits))
        if o is not None:
            neu["outfitAuswahl"] = None if o == list(range(outfits)) else o

    alt = {k: v for k, v in state.items() if k != "runden"}
    neu.update({
        "start": start + n,
        "favoriten": [], "verworfen": [], "takes": {}, "wahl": {},
        "runde": max(1, int(state.get("runde") or 1)) + 1,
        "runden": (list(state.get("runden") or []) + [alt])[-MAX_RUNDEN:],
    })
    return neu


KAMERA_DETAIL_FOKUS = {
    "Füße": "extreme close-up macro shot of feet and shoes, low angle floor-level perspective, camera focused tightly on the footwear and ankles",
    "Hände": "extreme close-up macro shot of hands, camera focused tightly on the hands and fingers",
    "Augen": "extreme close-up macro portrait shot, camera focused tightly on the eyes",
    "Lippen": "extreme close-up macro shot of the lips and mouth",
}


# What a macro detail shot can show of the pose and the face. Found in the
# recipe test: "extreme close-up macro shot of feet" followed by "lying on the
# stomach, near a window, torso turned away, looking back over the shoulder,
# one hand touching the face" and a haughty expression came out as the whole
# figure lying on the floor - the full pose outvoted the macro. So a macro keeps
# only what is in the frame: feet the base posture and the legs, hands the arms,
# eyes and lips no pose but the expression, which is what eyes and mouth show.
DETAIL_SICHTBAR = {
    "Füße": ({"haltung", "beine"}, False),
    "Hände": ({"arme"}, False),
    "Augen": (set(), True),
    "Lippen": (set(), True),
}


# Base postures a macro of the feet can carry: the feet stay on or near the
# floor and in front of the camera. Lying, reclining, sitting on the floor and
# all fours spread the body out - with those the feet macro still came out as
# the whole figure (recipe test, photos 4007 and 5006), so they are dropped.
FUSS_HALTUNGEN = set(PB.HALTUNG_GRUPPEN["stehend"]) | {
    "Sitzend", "Auf einem Stuhl sitzend", "Auf einem Hocker sitzend",
    "Auf einer Tischkante sitzend", "Kniend", "Auf einem Knie", "Hockend"}


# Close framings keep only what the frame shows of the pose: the turn of the
# body and the arms (a hand at the face). Found in the mood-arc test: a
# close-up with "lying on the stomach, near a window, leaning on the forearms,
# legs stretched out" came out as a medium shot, the face small and the mood
# lost - while the Headshots recipe, pose off, gave the best close portraits.
NAH_SICHTBAR = {"Nahaufnahme": {"koerper", "arme"}, "Porträt": {"koerper", "arme"}}


def _nur_sichtbares(pose_werte, ausdruck_werte, plan):
    """Pose and expression cut down to what a close or macro shot shows."""
    nah = NAH_SICHTBAR.get(plan.get("kamera"))
    if nah is not None:
        return {cat: (w if cat in nah else None) for cat, w in pose_werte.items()}, ausdruck_werte
    if plan.get("kamera") != "Detail":
        return pose_werte, ausdruck_werte
    regel = DETAIL_SICHTBAR.get(plan.get("fokus"))
    if not regel:
        return pose_werte, ausdruck_werte
    pose_felder, mit_ausdruck = regel
    if plan.get("fokus") == "Füße" and plan.get("pose", {}).get("haltung") not in FUSS_HALTUNGEN:
        pose_felder = pose_felder - {"haltung"}
    pose_werte = {cat: (w if cat in pose_felder else None) for cat, w in pose_werte.items()}
    if not mit_ausdruck:
        ausdruck_werte = {cat: None for cat in ausdruck_werte}
    return pose_werte, ausdruck_werte


def _person_fuer_kamera(person_data, kamera_label, fokus_label=None, ohne_subjekt=False, prop_erlaubt=True):
    """Shorten full person_data (JSON) to the camera and focus detail level."""
    if not person_data:
        return ""
    try:
        p = json.loads(person_data) if isinstance(person_data, str) else person_data
    except (TypeError, ValueError):
        print("[Photoshoot] person_data unreadable, person left out.")
        return ""
    if not isinstance(p, dict):
        return ""
    if not prop_erlaubt or kamera_label in ("Detail", "Nahaufnahme"):
        p = {k: v for k, v in p.items() if k not in ("prop", "propText")}
    if kamera_label in ("Detail", "Nahaufnahme"):
        if fokus_label == "Füße":
            return PeB.compose_person(p, detail=PeB.DETAIL_FUESSE)
        if fokus_label == "Hände":
            return PeB.compose_person(p, detail=PeB.DETAIL_HAENDE)
    detail = PeB.detail_fuer_kamera(kamera_label)
    return PeB.compose_person(p, detail=detail, ohne_subjekt=ohne_subjekt)


# ─────────────────────────────────────────────────────────────────────────────
# Training caption for a character LoRA (the caption output). A caption names
# the trigger and describes what changes from photo to photo - framing, pose,
# expression, outfit - and never what makes the person. Whatever a caption
# describes, the LoRA learns as separate from the trigger: a face spelled out
# in every caption ends up belonging to the words rather than to the trigger,
# which is then weak on its own. So the identity fields (LORA_WEG), age and
# body stay out even when they are set, and the reference phrase too.
# ─────────────────────────────────────────────────────────────────────────────
def _outfit_im_bild(p, kamera_label, fokus_label=None, prop_erlaubt=True):
    """The outfit as far as this framing shows it: a portrait has no shoes, a
    feet macro nothing but legwear and shoes (the same cut as the person
    block in _person_fuer_kamera())."""
    if kamera_label in ("Detail", "Nahaufnahme") and fokus_label == "Füße":
        sichtbar = PeB._FELDER_FUESSE
    elif kamera_label in ("Detail", "Nahaufnahme") and fokus_label == "Hände":
        sichtbar = PeB._FELDER_HAENDE
    else:
        detail = PeB.detail_fuer_kamera(kamera_label)
        sichtbar = {k for k in PeB.OUTFIT_FELDER if PeB._erlaubt(detail, k)}
    if not prop_erlaubt or kamera_label in ("Detail", "Nahaufnahme"):
        sichtbar = sichtbar - {"prop", "propText"}
    q = {k: v for k, v in p.items() if k in PeB.OUTFIT_FELDER and k in sichtbar}
    return PeB.compose_person(q, ohne_subjekt=True) if q else ""


def _kamera_kurz(plan):
    """The framing for a caption: the head of its wording and the focus -
    "full body shot, with the focus on the legs". The rest of the prompt
    wording (frame share, proportions, macro instructions) steers the model
    and describes nothing a trainer should learn."""
    kamera = dict(KAMERA).get(plan.get("kamera"), "").split(", ")[0]
    # A selfie is part of what varies: "portrait shot, high-angle selfie".
    perspektive = dict(PERSPEKTIVE).get(plan.get("perspektive"), "").split(", ")[0]
    fokus = dict(FOKUS).get(plan.get("fokus"), "")
    return ", ".join(t for t in (kamera, perspektive, fokus) if t)


def caption_fuer(person_data, plan, pose, ausdruck, subjekt=None, prop_erlaubt=True):
    """The training caption of this photo: trigger, subject, then what varies.

    The trigger comes from the person (LoRA trigger field). Without one the
    caption starts with the subject ("a woman, ..."), and Save Dataset puts
    its own trigger in front. subjekt is the mood written as the subject when
    a mood arc is on; it then stands for the expression.
    """
    try:
        p = json.loads(person_data) if isinstance(person_data, str) and person_data else (person_data or {})
    except (TypeError, ValueError):
        p = {}
    p = p if isinstance(p, dict) else {}
    teile = [PeB._clean(p.get("trigger"))]
    if subjekt:
        teile.append(subjekt)
    elif p:
        teile.append(PeB._artikel(PeB.geschlecht(p)[0]))
    teile += [_kamera_kurz(plan), pose]
    if not subjekt:
        teile.append(ausdruck)
    teile.append(_outfit_im_bild(p, plan.get("kamera"), plan.get("fokus"), prop_erlaubt=prop_erlaubt))
    return ", ".join(t for t in teile if t)


class Krea2Photoshooting:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # The photo number, not a random value: the button in the
                # interface sets it to the start number and puts
                # control_after_generate on increment. 1 is the first photo;
                # 0 still arrives from workflows saved before the rename and
                # counts as the first photo too.
                "foto": ("INT", {"default": 1, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True}),
            },
            "optional": {
                # Dimensions from outside, e.g. from "Resolution Pixaroma".
                # They apply only when varying the ratio is switched off -
                # otherwise the framing decides the ratio, and a fixed value
                # from outside would contradict it.
                "width_in": ("INT", {"forceInput": True}),
                "height_in": ("INT", {"forceInput": True}),
                # Raw values from the Person Builder (person_data output).
                # Reassembled per framing - a wide shot without eyeshadow, a
                # portrait with everything. Wiring the finished person string in
                # here buys nothing: that one cannot be shortened.
                "person_data": ("STRING", {"forceInput": True}),
                # The sets of a Location node (its ort_data output). Without
                # one the set axis does nothing and "szene" stays empty.
                "ort_data": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "ShootingState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    # person / person_data / kamera_label at the end: existing workflows keep
    # wiring pose/ausdruck/kamera/width/height/bildseed at the same indices.
    # person_data and kamera_label are there for optional packs that replace
    # fields and re-compose at the same detail level. refine (off for a draft,
    # into the render node's refine switch) and dateiname (into Save Image's
    # filename_prefix) came in 2.7.0 - appended, for the same reason. So did
    # caption and foto, which feed Save Dataset: the training caption and the
    # photo number of this run. szene (the set of this photo, shortened for
    # the framing) and licht (the setup of the light axis) came with the set
    # and light axes; both are empty until those are configured.
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "INT", "INT",
                    "STRING", "STRING", "STRING", "BOOLEAN", "STRING", "STRING", "INT",
                    "STRING", "STRING", "STRING")
    RETURN_NAMES = ("pose", "ausdruck", "kamera", "width", "height", "bildseed",
                    "person", "person_data", "kamera_label", "refine", "dateiname",
                    "caption", "foto", "szene", "licht", "prompt")
    FUNCTION = "shoot_ui"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Variiert Kamera, Pose, Mimik und Bildformat über eine ganze "
                   "Serie. Person optional per person_data - wird je Einstellung "
                   "gekürzt; hängt am Person Builder eine Wardrobe, wechselt "
                   "das Outfit über die Serie. person_data und kamera_label für optionale "
                   "Packs. 'foto' ist die Fotonummer in der Serie, keine "
                   "Zufallsquelle - der Rausch-Seed kommt aus bildseed. "
                   "refine geht in den Refine-Schalter des Render-Nodes "
                   "(aus bei Entwurf), dateiname in filename_prefix von Save Image. "
                   "caption und foto am Ende für Datensatz speichern: die "
                   "Trainings-Bildunterschrift (Trigger und was sich ändert, nie die "
                   "Identität) und die Fotonummer. szene und licht: das Set dieses "
                   "Fotos aus dem Location-Node an ort_data (je Einstellung gekürzt) "
                   "und das Licht der Lichtachse. prompt: der fertig zusammengesetzte "
                   "Gesamtprompt (nutzt eingebettete Studio-Einstellungen, wenn keine "
                   "externen Nodes verdrahtet sind).")

    def shoot_ui(self, *args, **kwargs):
        res = self.shoot(*args, **kwargs)
        return {"ui": {"text": [res[-1]]}, "result": res}

    def shoot(self, foto=1, ShootingState=None, width_in=None, height_in=None,
              person_data=None, ort_data=None):
        try:
            state = json.loads(ShootingState) if ShootingState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        # Photo 1 is run 0: series shot before the widget was 1-based keep
        # the same pictures under the same numbers.
        lauf = max(0, int(foto or 0) - 1)
        # The wardrobe comes with the person: a Wardrobe node on the Person
        # Builder puts its outfits into person_data ("_garderobe"). When
        # nothing is wired into person_data, fall back to embedded Studio
        # states (_person / _wardrobe) injected from node.properties.
        try:
            p_roh = json.loads(person_data) if isinstance(person_data, str) and person_data else person_data
        except (TypeError, ValueError):
            p_roh = None
        if not person_data and (isinstance(state.get("_person"), dict) or isinstance(state.get("_wardrobe"), dict)):
            p_roh = PeB.werte_aus_state(state.get("_person") or {})
            if isinstance(state.get("_wardrobe"), dict):
                w_outfits = WB.outfits_aus_state(state["_wardrobe"])
                if w_outfits:
                    try:
                        k_akt = min(max(0, int(state["_wardrobe"].get("aktiv") or 0)), len(w_outfits) - 1)
                    except (TypeError, ValueError):
                        k_akt = 0
                    p_roh = PeB.mit_outfit(p_roh, w_outfits[k_akt]["werte"])
                    p_roh["_garderobe"] = w_outfits
            person_data = json.dumps(p_roh, ensure_ascii=False)
        outfits = PeB.garderobe_lesen(p_roh.get("_garderobe")) if isinstance(p_roh, dict) else []
        saetze = OB.saetze_lesen(ort_data)
        if not ort_data and isinstance(state.get("_location"), dict):
            saetze = OB.saetze_von(state["_location"], lauf)
        plan = plane(state, lauf, len(outfits), len(saetze))
        detail = PeB.detail_fuer_kamera(plan["kamera"])

        # Costume change: the person wears this photo's outfit, and everything
        # downstream - the person block, the mood subject, person_data for the
        # packs - sees the dressed person.
        k = outfit_fuer(state, lauf, len(outfits))
        p_akt = p_roh
        if k is not None:
            p_akt = PeB.mit_outfit(p_roh, outfits[k]["werte"])
            person_data = json.dumps(p_akt, ensure_ascii=False)

        prop_ok = (plan["kamera"] not in ("Detail", "Nahaufnahme")
                   and plan.get("perspektive") not in SELFIES
                   and plan.get("fokus") != "Rücken"
                   and plan["pose"].get("koerper") != ABGEWANDT
                   and PB.haltung_erlaubt_requisit(plan["pose"].get("haltung")))
        pose_werte = {cat: _wert(PB, cat, plan["pose"].get(cat)) for cat in PB.FOLGE}
        if prop_ok and isinstance(p_akt, dict) and (p_akt.get("prop") or p_akt.get("propText")) \
                and not state.get("requisiten") and not (state.get("requisitText") or "").strip():
            pose_werte["arme"] = None
        if (state.get("requisitText") or "").strip() and plan.get("perspektive") not in SELFIES \
                and PB.haltung_erlaubt_requisit(plan["pose"].get("haltung")):
            req_liste = PB.requisit_liste(state.get("requisitText"))
            if req_liste:
                pose_werte["arme"] = req_liste[lauf % len(req_liste)]
        ausdruck_werte = {cat: _wert(EB, cat, plan["ausdruck"].get(cat)) for cat in EB.FOLGE}
        ausdruck_werte = _ausdruck_fuer_detail(ausdruck_werte, detail)
        ausdruck_werte = _ausdruck_fuer_koerper(ausdruck_werte,
                                                plan["pose"].get("koerper"))

        pose_werte, ausdruck_werte = _nur_sichtbares(pose_werte, ausdruck_werte, plan)

        pose = PB.compose_pose(pose_werte, "")
        ausdruck = EB.compose_expression(ausdruck_werte, "")

        fokus_lbl = plan.get("fokus")
        if plan.get("kamera") == "Detail" and fokus_lbl in KAMERA_DETAIL_FOKUS:
            kamera = KAMERA_DETAIL_FOKUS[fokus_lbl]
        else:
            # Framing, perspective, focus, optional framing-coupled lens: the
            # perspective right after the framing's wording, as the lab rendered it.
            optik = (KAMERA_OPTIK.get(plan["kamera"], "")
                     if state.get("kameraOptik") and plan.get("perspektive") not in SELFIES else "")
            kamera = ", ".join(t for t in (
                dict(KAMERA).get(plan["kamera"], "") if plan["kamera"] else "",
                dict(PERSPEKTIVE).get(plan.get("perspektive"), ""),
                dict(FOKUS).get(fokus_lbl, "") if fokus_lbl else "",
                optik) if t)

        # With a mood arc the mood becomes the subject at the front: the
        # expression output then reads "a terrified woman screaming ...", and
        # the person drops its own leading "a woman". Not on feet or hands
        # macros, and not with the body turned away (no face to show).
        subjekt = None
        if (bogen_von(state) and ausdruck_werte.get("stimmung")
                and plan["pose"].get("koerper") != ABGEWANDT
                and not (plan.get("kamera") == "Detail" and plan.get("fokus") in ("Füße", "Hände"))):
            subjekt = stimmung_als_subjekt(plan["ausdruck"].get("stimmung"), person_data,
                                           makro=plan.get("kamera") == "Detail")
        if subjekt:
            ausdruck = subjekt
        person = _person_fuer_kamera(person_data, plan["kamera"], plan.get("fokus"),
                                     ohne_subjekt=bool(subjekt), prop_erlaubt=prop_ok)

        # Pass the raw data through unchanged - a pack downstream can replace
        # fields and re-compose, using kamera_label for the same detail level as
        # here.
        if person_data is None or person_data == "":
            pd_out = ""
        elif isinstance(person_data, str):
            pd_out = person_data
        else:
            pd_out = json.dumps(person_data, ensure_ascii=False)
        kamera_label = plan["kamera"] or ""

        # When dimensions arrive from outside and the ratio is not being
        # varied, they win - the upstream node then decides the resolution.
        wuerfelt_format = state.get("aktiv", {}).get("format", True)
        if not wuerfelt_format and width_in and height_in:
            w, h = int(width_in), int(height_in)
        else:
            w, h = masse(plan["kamera"], lauf, state, plan.get("perspektive"))

        # The set of this photo, as far as the framing shows it, and the
        # light of the light axis. Both empty until configured, so the
        # caption and every other output stay what they were. Embedded Studio
        # lighting / style / template / preview-override build the combined
        # prompt output directly on this node when running without extra nodes.
        s = set_fuer(state, lauf, len(saetze))
        szene = szene_fuer(saetze[s] if s is not None else None, plan["kamera"])
        if not szene and state.get("_scene") and plan["kamera"] not in SET_WEG:
            szene = str(state.get("_scene") or "").strip()
        licht_label = licht_fuer(state, lauf, [x["draussen"] for x in saetze])
        if isinstance(state.get("_lighting"), dict):
            l_state = copy.deepcopy(state["_lighting"])
            if licht_label:
                l_state.setdefault("felder", {})["setup"] = licht_label
                if isinstance(l_state.get("wuerfeln"), dict):
                    l_state["wuerfeln"].pop("setup", None)
            licht = LB.Krea2LightingBuilder().build(seed=lauf, LightingState=json.dumps(l_state))[0]
        else:
            licht = dict(LB.PRESETS["setup"]).get(licht_label, "") if licht_label else ""

        caption = caption_fuer(person_data, plan, pose, ausdruck, subjekt, prop_erlaubt=prop_ok)
        caption = ", ".join(t for t in (caption, szene, licht) if t)

        stil = (SB.Krea2StyleBuilder().build(seed=lauf, StyleState=json.dumps(state["_style"]))[0]
                if isinstance(state.get("_style"), dict) else "")
        vorlage = str(state.get("_template") or "")
        if state.get("_vorschauPrompt"):
            prompt = str(state["_vorschauPrompt"])
        else:
            from . import store as ST
            prompt = ST.Krea2PromptJoin().join(
                vorlage, person_1=person, kamera=kamera, pose=pose,
                ausdruck=ausdruck, licht=licht, szene=szene, stil=stil)["result"][0]

        return (pose, ausdruck, kamera, w, h, bildseed(lauf, state),
                person, pd_out, kamera_label, not state.get("entwurf"),
                dateiname(state, lauf), caption, lauf + 1, szene, licht, prompt)


NODE_CLASS_MAPPINGS = {"Krea2Photoshooting": Krea2Photoshooting}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2Photoshooting": "Photoshoot – Serie"}
