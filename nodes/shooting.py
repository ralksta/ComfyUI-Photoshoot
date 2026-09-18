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

import json

from . import expression_builder as EB
from . import person_builder as PeB
from . import pose_builder as PB

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
# shot eventually lands in 16:9 landscape and the image is unusable.
KAMERA_FORMATE = {
    "Detail":       ["1:1", "3:2", "16:9"],
    "Nahaufnahme":  ["1:1", "4:5"],
    "Porträt":      ["4:5", "1:1", "3:4"],
    "Halbtotale":   ["2:3", "3:4", "4:5"],
    "Amerikanisch": ["2:3", "3:4"],
    "Ganzkörper":   ["2:3", "3:4", "9:16"],
    "Totale":       ["3:2", "16:9", "1:1"],
}

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
_NENNER = 1 << 32
_WURZELN = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53]

DEFAULT_STATE = {
    "anzahl": 12,
    "aktiv": {"kamera": True, "pose": True, "ausdruck": True, "format": True,
              "fokus": True, "rausch": True},
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
    "kameras": [lbl for lbl, _ in KAMERA],  # Mehrfachauswahl
    "fokusse": [lbl for lbl, _ in FOKUS],  # Mehrfachauswahl
    "groesse": KANTE_STANDARD,
    "festesFormat": "2:3",  # applies when "format" is off and nothing is wired in
}


def _schritt(platz):
    """This field's step size as a fraction of _NENNER.

    sqrt of a prime is irrational, and the fractional part is distributed evenly
    over (0,1). Every field gets a different prime and therefore a beat of its
    own, commensurable with no other.
    """
    wurzel = _WURZELN[platz % len(_WURZELN)] ** 0.5
    return int((wurzel % 1.0) * _NENNER) | 1  # ungerade: nie ein Teiler von 2^32


def _waehle(labels, lauf, platz):
    """Draw one entry for this run."""
    n = len(labels)
    if not n:
        return None
    return labels[((lauf * _schritt(platz)) % _NENNER) * n // _NENNER]


def _pool(quelle, cat, state, kamera_label=None, haltung_label=None,
          stimmung_label=None):
    """The labels this field is allowed to draw from."""
    modul = PB if quelle == "pose" else EB
    gruppen = (PB.HALTUNG_GRUPPEN if quelle == "pose" else EB.STIMMUNG_GRUPPEN)
    gruppenfeld = "haltung" if quelle == "pose" else "stimmung"

    wahl = (state.get("pools") or {}).get(cat, ALLE)
    if wahl == NONE:
        return []
    alle = [lbl for lbl, _ in modul.PRESETS[cat]]
    if cat == gruppenfeld and wahl != ALLE:
        return [l for l in alle if l in gruppen.get(wahl, [])]
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


def plane(state, lauf):
    """What this photo shows. A pure function - same run, same result."""
    aktiv = state.get("aktiv") or {}
    kamera_label = None
    pose_labels, ausdruck_labels = {}, {}

    for platz, (cat, quelle) in enumerate(FELDER):
        if not aktiv.get(quelle, True):
            continue
        if quelle == "kamera":
            erlaubt = state.get("kameras") or [lbl for lbl, _ in KAMERA]
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
        fokus_label = _waehle(erlaubt, lauf, len(FELDER) + 2)

    return {"kamera": kamera_label, "fokus": fokus_label,
            "pose": pose_labels, "ausdruck": ausdruck_labels}


def format_fuer(kamera_label, lauf, state):
    """Which aspect ratio this photo gets."""
    if not state.get("aktiv", {}).get("format", True):
        return state.get("festesFormat") or "2:3"
    erlaubt = KAMERA_FORMATE.get(kamera_label) or list(RATIOS)
    # Its own slot in the step-size list, so the ratio does not move in
    # lockstep with the camera.
    return _waehle(erlaubt, lauf, len(FELDER) + 1)


def masse(kamera_label, lauf, state):
    """Image dimensions for this photo - coupled to the framing."""
    kante = int(state.get("groesse") or KANTE_STANDARD)
    return masse_fuer(format_fuer(kamera_label, lauf, state), kante)


def _wert(modul, cat, label):
    for lbl, wert in modul.PRESETS[cat]:
        if lbl == label:
            return wert
    return None


def bildseed(lauf, state=None):
    """Noise seed for this photo, derived from the run counter.

    Not the counter itself: 0, 1, 2 sit close together in noise space and give
    images that resemble each other. The factor is Knuth's scattering constant
    for 32 bits (2^32 / the golden ratio); it pulls consecutive numbers far
    apart and is still unique - photo 7 always gets the same seed, so the series
    stays recoverable.

    When the "rausch" axis is switched off, the whole series gets the same seed.
    That holds the setting together: the scene text describes "a gothic bed of
    dark wood", not *this* bed - everything it leaves open the model invents out
    of the noise, and with new noise it comes out differently. Pose, expression
    and camera keep varying, since those come from the prompt and not from the
    seed.
    """
    state = state or {}
    if not (state.get("aktiv") or {}).get("rausch", True):
        return int(state.get("serienSeed") or 0) % (1 << 31)
    return (int(lauf) * 2654435761) % (1 << 31)


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


KAMERA_DETAIL_FOKUS = {
    "Füße": "extreme close-up macro shot of feet and shoes, low angle floor-level perspective, camera focused tightly on the footwear and ankles",
    "Hände": "extreme close-up macro shot of hands, camera focused tightly on the hands and fingers",
    "Augen": "extreme close-up macro portrait shot, camera focused tightly on the eyes",
    "Lippen": "extreme close-up macro shot of the lips and mouth",
}


def _person_fuer_kamera(person_data, kamera_label, fokus_label=None):
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
    if kamera_label in ("Detail", "Nahaufnahme"):
        if fokus_label == "Füße":
            return PeB.compose_person(p, detail=PeB.DETAIL_FUESSE)
        if fokus_label == "Hände":
            return PeB.compose_person(p, detail=PeB.DETAIL_HAENDE)
    detail = PeB.detail_fuer_kamera(kamera_label)
    return PeB.compose_person(p, detail=detail)


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
            },
            "hidden": {
                "ShootingState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    # person / person_data / kamera_label at the end: existing workflows keep
    # wiring pose/ausdruck/kamera/width/height/bildseed at the same indices.
    # person_data and kamera_label are there for optional packs that replace
    # fields and re-compose at the same detail level.
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "INT", "INT",
                    "STRING", "STRING", "STRING")
    RETURN_NAMES = ("pose", "ausdruck", "kamera", "width", "height", "bildseed",
                    "person", "person_data", "kamera_label")
    FUNCTION = "shoot"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Variiert Kamera, Pose, Mimik und Bildformat über eine ganze "
                   "Serie. Person optional per person_data - wird je Einstellung "
                   "gekürzt. person_data und kamera_label am Ende für optionale "
                   "Packs. 'foto' ist die Fotonummer in der Serie, keine "
                   "Zufallsquelle - der Rausch-Seed kommt aus bildseed.")

    def shoot(self, foto=1, ShootingState=None, width_in=None, height_in=None,
              person_data=None):
        try:
            state = json.loads(ShootingState) if ShootingState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        # Photo 1 is run 0: series shot before the widget was 1-based keep
        # the same pictures under the same numbers.
        lauf = max(0, int(foto or 0) - 1)
        plan = plane(state, lauf)
        detail = PeB.detail_fuer_kamera(plan["kamera"])

        pose_werte = {cat: _wert(PB, cat, plan["pose"].get(cat)) for cat in PB.FOLGE}
        ausdruck_werte = {cat: _wert(EB, cat, plan["ausdruck"].get(cat)) for cat in EB.FOLGE}
        ausdruck_werte = _ausdruck_fuer_detail(ausdruck_werte, detail)
        ausdruck_werte = _ausdruck_fuer_koerper(ausdruck_werte,
                                                plan["pose"].get("koerper"))

        pose = PB.compose_pose(pose_werte, "")
        ausdruck = EB.compose_expression(ausdruck_werte, "")

        fokus_lbl = plan.get("fokus")
        if plan.get("kamera") == "Detail" and fokus_lbl in KAMERA_DETAIL_FOKUS:
            kamera = KAMERA_DETAIL_FOKUS[fokus_lbl]
        else:
            kamera = dict(KAMERA).get(plan["kamera"], "") if plan["kamera"] else ""
            fokus = dict(FOKUS).get(fokus_lbl, "") if fokus_lbl else ""
            if kamera and fokus:
                kamera = kamera + ", " + fokus
            elif fokus:
                kamera = fokus

        person = _person_fuer_kamera(person_data, plan["kamera"], plan.get("fokus"))

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
            w, h = masse(plan["kamera"], lauf, state)

        return (pose, ausdruck, kamera, w, h, bildseed(lauf, state),
                person, pd_out, kamera_label)


NODE_CLASS_MAPPINGS = {"Krea2Photoshooting": Krea2Photoshooting}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2Photoshooting": "Photoshoot Serie"}
