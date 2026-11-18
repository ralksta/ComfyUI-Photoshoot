"""
Pose - assemble a body posture from dropdowns.

Returns a STRING that goes into the "pose" input of "build prompt", where it
replaces the {pose} placeholder.

The point is not just convenience but unambiguity: "her arms on her back" reads
literally as *arms lying on top of the back*, and the model duly guesses at it.
The values here are worded so that they allow only one reading - "both arms
held behind the back, hands clasped together".

As with the expression, no possessive pronouns, so the same block fits any
figure.

Dice: when "wuerfeln_<field>" is on, that field's dropdown is ignored and a
value is drawn from the list instead. Together with batch count (the number
field next to the queue button) and the seed widget, every run gets a different
pose that way. "haltung_gruppe" keeps the spread in check - on "sitting" the
figure stays seated and only the variant changes.
"""

import json
import random
import re

from . import eigene

PRESETS = {
    "haltung": [
        ("Stehend", "standing"),
        ("Stehend, Gewicht auf einem Bein", "standing with the weight on one leg"),
        ("Angelehnt", "leaning against a wall"),
        ("Gehend", "walking"),
        ("Vorgebeugt", "bending forward"),
        ("Sitzend", "sitting"),
        ("Auf einem Stuhl sitzend", "sitting on a chair"),
        ("Auf einem Hocker sitzend", "sitting on a stool"),
        ("Auf einer Tischkante sitzend", "sitting on the edge of a table"),
        ("Auf dem Boden sitzend", "sitting on the floor"),
        ("Zurückgelehnt", "reclining"),
        ("Kniend", "kneeling"),
        ("Auf einem Knie", "kneeling on one knee"),
        ("Hockend", "squatting"),
        ("Auf allen Vieren", "on all fours"),
        ("Auf dem Rücken liegend", "lying on the back"),
        ("Auf dem Bauch liegend", "lying on the stomach"),
        ("Auf der Seite liegend", "lying on one side"),
        # Appended 2026-09-23 after a render test (videoflow preset_kandidaten,
        # three seeds each, user verdict "ja"); kept at the end so the posters
        # keep their order.
        ("Strecken", "standing and stretching, both arms raised overhead, the body elongated"),
        ("In der Drehung", "caught turning in mid-motion, the hair swinging out, the skirt or coat flaring"),
        ("Seitlich auf dem Boden", "sitting sideways on the floor, both legs folded to one side, leaning on one hand"),
        ("Bauchlage, Kinn in den Händen", "lying on the stomach, chin propped on both hands, lower legs raised and crossed in the air"),
        ("Im Schneidersitz", "sitting cross-legged on the floor, back straight, hands resting on the knees"),
        ("Fersensitz", "kneeling and sitting back on the heels, back straight, hands resting on the thighs"),
    ],
    # Placement in the room and in the frame. Without this axis the figure
    # implicitly always ends up in the foreground and dead centre - and then
    # even changing arm positions look identical from a wide shot. The wordings
    # are deliberately spatial (middle ground, doorway, far wall), not merely
    # "left/right".
    "raum": [
        # Every one of these has to name the subject. "Farther back in the
        # background of the space" does not, and the model then reads it as a
        # second element rather than as a position for the person it was just
        # given: measured on one seed, that phrasing produced two women, one
        # squatting in front and one standing behind. "A small figure deep
        # inside a large room" never did, because it says whose position it is.
        ("Vordergrund", "the subject placed in the foreground"),
        ("Bildmitte", "the subject centered in the middle ground"),
        ("Hintergrund", "the subject farther back in the space"),
        ("Tief im Raum", "a small figure deep inside a large room"),
        ("Am Fenster", "near a window"),
        ("Im Türrahmen", "in a doorway"),
        ("An der Wand", "against the far wall"),
        ("An der Raumkante", "off to one side of the room"),
        ("Zwischen Möbeln", "among the furniture in the room"),
        ("Gehend durch den Raum", "moving through the open space of the room"),
    ],
    "koerper": [
        ("Frontal zur Kamera", "facing the camera directly"),
        ("Leicht zur Seite gedreht", "turned slightly to the side"),
        ("Dreiviertelansicht", "in a three-quarter view"),
        ("Im Profil", "in profile"),
        ("Von hinten", "seen from behind"),
        ("Über die Schulter gedreht", "torso turned away, looking back over the shoulder"),
    ],
    "arme": [
        # The case it hinges on - deliberately spelled out twice over.
        ("Hinter dem Rücken", "both arms held behind the back, hands clasped together"),
        ("Hinter dem Rücken, Handgelenke gekreuzt",
         "both arms behind the back with the wrists crossed"),
        ("Hinter dem Kopf", "both arms raised behind the head"),
        ("Über dem Kopf gestreckt", "both arms stretched above the head"),
        ("Vor der Brust verschränkt", "arms crossed in front of the chest"),
        ("Seitlich hängend", "arms hanging relaxed at the sides"),
        ("Hände auf den Hüften", "hands on the hips"),
        ("Hände im Schoß", "hands resting in the lap"),
        ("Hände auf den Knien", "hands resting on the knees"),
        ("Hinter sich abgestützt", "hands propped on the surface behind"),
        ("Auf die Unterarme gestützt", "leaning on the forearms"),
        ("Eine Hand am Gesicht", "one hand touching the face"),
        ("Eine Hand im Haar", "one hand running through the hair"),
        ("Arme umschlingen die Knie", "arms wrapped around the knees"),
        # Appended 2026-09-30 after a render test (tools/wortlabor/selfie.json,
        # peace-a, three seeds, rendered in the pose slot next to an eye-level
        # selfie; adopted by the user). A gesture for the phone: the Series
        # draws it on selfie photos only, the die never (SELFIE_GESTEN).
        ("Peace-Zeichen", "making a peace sign with two fingers next to her face"),
        # Appended after render test (tools/wortlabor/winkel_props.json, group C,
        # 3 seeds each against bare-word controls). Kept at the end and excluded
        # from Pose Builder dice and Series unless state["requisiten"] is true.
        ("Kaffeetasse", "holding a warm ceramic coffee mug with both hands in front of her chest"),
        ("Buch in der Hand", "holding an open hardcover book in both hands at waist height, looking up from the pages"),
        ("Weinglas", "holding a stemmed glass of red wine by the stem in one hand at chest height, the other arm relaxed"),
        ("Blumenstrauß", "cradling a bouquet of fresh cut flowers wrapped in kraft paper in her arms against her chest"),
    ],
    "beine": [
        ("Geschlossen", "legs closed together"),
        ("Leicht geöffnet", "legs slightly apart"),
        ("Weit gespreizt", "legs spread wide apart"),
        ("Übereinandergeschlagen", "legs crossed"),
        ("Knöchel gekreuzt", "ankles crossed"),
        ("Angewinkelt", "knees drawn up"),
        ("Ein Knie angewinkelt", "one knee bent"),
        ("Ausgestreckt", "legs stretched out"),
        ("Knie zusammen, Füße auseinander", "knees together, feet apart"),
        ("Untergeschlagen", "legs tucked underneath"),
    ],
    # Body tension has to fit every base posture, because both fields are
    # drawn independently. "sitting up straight" used to stand here for
    # "upright" and contradicted lying down in the same sentence - the model
    # read "lying on the back, ... sitting up straight" and settled on the
    # upright posture. "slouching" carried a sitting position with it too. Now
    # every wording holds up standing, sitting and lying down alike.
    "spannung": [
        ("Aufrecht", "with an upright posture"),
        ("Schultern zurück", "shoulders drawn back"),
        ("Rücken durchgedrückt", "back arched"),
        ("Entspannt", "a relaxed, loose posture"),
        ("Angespannt", "a tense, rigid posture"),
        ("Zusammengesunken", "with a slumped posture"),
        ("Zusammengekauert", "curled up"),
    ],
}

# Order within the sentence: base posture, placement in the room, orientation
# towards the camera, then arms and legs, body tension last.
FOLGE = ["haltung", "raum", "koerper", "arme", "beine", "spannung"]

# Families of the base posture. Drawing can be restricted to one of them -
# otherwise the figure stands in one shot, lies down in the next and kneels in
# the third, and the four images of a run have nothing left in common.
HALTUNG_GRUPPEN = {
    "stehend": ["Stehend", "Stehend, Gewicht auf einem Bein", "Angelehnt",
                "Gehend", "Vorgebeugt", "Strecken", "In der Drehung"],
    "sitzend": ["Sitzend", "Auf einem Stuhl sitzend", "Auf einem Hocker sitzend",
                "Auf einer Tischkante sitzend", "Auf dem Boden sitzend",
                "Zurückgelehnt", "Seitlich auf dem Boden", "Im Schneidersitz"],
    "kniend":  ["Kniend", "Auf einem Knie", "Hockend", "Auf allen Vieren", "Fersensitz"],
    "liegend": ["Auf dem Rücken liegend", "Auf dem Bauch liegend",
                "Auf der Seite liegend", "Bauchlage, Kinn in den Händen"],
}

# Which body tension fits which base posture.
#
# Both fields are drawn independently, so every pairing can occur. Most are
# harmless, but a few contradict each other outright: "leaning against a wall,
# curled up" asks for a body that is upright and drawn into a ball at the same
# time, and "lying on the back, with a slumped posture" asks a horizontal body
# to sag under a gravity that is not pulling that way. Measured over 200 runs of
# a series, 12% of the photos carried one of these.
#
# The neutral four fit anywhere - they say something about shoulders, back or
# muscle tone, not about the body as a whole. "Upright" needs a vertical spine,
# which rules out lying down and the two postures that already bend the torso.
# "Slumped" needs gravity pulling down on a supported torso, which rules out
# lying down. "Curled up" needs the whole body drawn in, which rules out
# standing, walking, reclining and being on all fours.
#
# This is deliberately per posture and not per family: "Zurückgelehnt" sits, but
# reclining and curling up are opposites, and a family rule would miss that.
_SP_NEUTRAL = ["Schultern zurück", "Rücken durchgedrückt", "Entspannt",
               "Angespannt"]
_SP_GEBEUGT = _SP_NEUTRAL + ["Zusammengesunken"]
_SP_AUFRECHT = _SP_GEBEUGT + ["Aufrecht"]
_SP_EINGEROLLT = _SP_AUFRECHT + ["Zusammengekauert"]
_SP_LIEGEND = _SP_NEUTRAL + ["Zusammengekauert"]

HALTUNG_SPANNUNG = {
    # upright: can sag into itself, but cannot curl up
    "Stehend":                        list(_SP_AUFRECHT),
    "Stehend, Gewicht auf einem Bein": list(_SP_AUFRECHT),
    "Angelehnt":                      list(_SP_AUFRECHT),
    "Gehend":                         list(_SP_AUFRECHT),
    # torso already bent - "upright" would contradict itself
    "Vorgebeugt":                     list(_SP_GEBEUGT),
    "Zurückgelehnt":                  list(_SP_GEBEUGT),
    # sitting on furniture: curling up works badly on a stool or a table edge
    "Auf einem Stuhl sitzend":        list(_SP_AUFRECHT),
    "Auf einem Hocker sitzend":       list(_SP_AUFRECHT),
    "Auf einer Tischkante sitzend":   list(_SP_AUFRECHT),
    # sitting low and kneeling: curling up is the natural move here
    "Sitzend":                        list(_SP_EINGEROLLT),
    "Auf dem Boden sitzend":          list(_SP_EINGEROLLT),
    "Kniend":                         list(_SP_EINGEROLLT),
    "Hockend":                        list(_SP_EINGEROLLT),
    "Auf einem Knie":                 list(_SP_AUFRECHT),
    # on all fours the torso carries itself
    "Auf allen Vieren":               list(_SP_NEUTRAL),
    "Auf dem Rücken liegend":         list(_SP_LIEGEND),
    "Auf dem Bauch liegend":          list(_SP_LIEGEND),
    "Auf der Seite liegend":          list(_SP_LIEGEND),
    "Strecken":                       list(_SP_AUFRECHT),
    "In der Drehung":                 list(_SP_AUFRECHT),
    "Seitlich auf dem Boden":         list(_SP_EINGEROLLT),
    "Bauchlage, Kinn in den Händen":  list(_SP_LIEGEND),
    # "back straight" is in the wording - nothing slumped or curled up
    "Im Schneidersitz":               ["Aufrecht", "Schultern zurück", "Entspannt"],
    "Fersensitz":                     ["Aufrecht", "Schultern zurück", "Entspannt"],
}

# Arms and legs against the base posture, the same idea one level down. Hands
# resting in the lap need a lap, forearms need something to rest on, and knees
# can only be drawn up off a floor. Without this, one run in five asked for
# something nobody can do - "walking, arms wrapped around the knees, knees
# together, feet apart" was a real draw, and the model answers it by twisting
# the body until both halves are half-true.
_AR_STEHEND = ["Hinter dem Rücken", "Hinter dem Rücken, Handgelenke gekreuzt",
               "Hinter dem Kopf", "Über dem Kopf gestreckt",
               "Vor der Brust verschränkt", "Seitlich hängend",
               "Hände auf den Hüften", "Eine Hand am Gesicht", "Eine Hand im Haar"]
_AR_ZURUECK = ["Hinter dem Kopf", "Über dem Kopf gestreckt", "Vor der Brust verschränkt",
               "Seitlich hängend", "Hände im Schoß", "Hinter sich abgestützt",
               "Eine Hand am Gesicht", "Eine Hand im Haar"]
REQUISITEN = ["Kaffeetasse", "Buch in der Hand", "Weinglas", "Blumenstrauß"]
_AR_STEHEND_REQUISITEN = _AR_STEHEND + REQUISITEN
_AR_VORGEBEUGT = ["Hinter dem Rücken", "Vor der Brust verschränkt", "Seitlich hängend",
                  "Hände auf den Hüften", "Hände auf den Knien",
                  "Eine Hand am Gesicht", "Eine Hand im Haar"]
_AR_SITZ = _AR_STEHEND_REQUISITEN + ["Hände im Schoß", "Hände auf den Knien"]
_AR_SITZ_BODEN = _AR_SITZ + ["Hinter sich abgestützt", "Arme umschlingen die Knie"]
_AR_ZURUECK = _AR_ZURUECK + REQUISITEN
_AR_HOCKE = ["Hinter dem Rücken", "Vor der Brust verschränkt", "Hände auf den Hüften",
             "Hände auf den Knien", "Arme umschlingen die Knie",
             "Eine Hand am Gesicht", "Eine Hand im Haar"]
_AR_VIER = ["Auf die Unterarme gestützt"]
_AR_RUECKEN = ["Hinter dem Kopf", "Über dem Kopf gestreckt", "Vor der Brust verschränkt",
               "Seitlich hängend", "Hände im Schoß", "Eine Hand am Gesicht",
               "Eine Hand im Haar"]
_AR_BAUCH = ["Über dem Kopf gestreckt", "Seitlich hängend", "Auf die Unterarme gestützt",
             "Eine Hand am Gesicht", "Eine Hand im Haar"]
_AR_SEITE = _AR_BAUCH + ["Hinter dem Kopf", "Vor der Brust verschränkt",
                         "Arme umschlingen die Knie"]

# Placement against posture. Nine of the ten placements say where in the room
# the figure is, which any posture can satisfy - you can lie on the floor near
# a window. "Gehend durch den Raum" is the exception: it claims motion, and a
# body that is sitting, kneeling or lying cannot supply it. Five runs in a
# hundred drew that pair before this table existed.
_RA_ALLE = [lbl for lbl, _ in PRESETS["raum"]]
_RA_STILL = [l for l in _RA_ALLE if l != "Gehend durch den Raum"]
# Leaning is against a wall, so it does not cross the open space either.
_BEWEGLICH = {"Stehend", "Stehend, Gewicht auf einem Bein", "Gehend", "Vorgebeugt", "In der Drehung"}

HALTUNG_RAUM = {lbl: list(_RA_ALLE) if lbl in _BEWEGLICH else list(_RA_STILL)
                for lbl, _ in PRESETS["haltung"]}

HALTUNG_ARME = {
    "Stehend":                        list(_AR_STEHEND_REQUISITEN),
    "Stehend, Gewicht auf einem Bein": list(_AR_STEHEND_REQUISITEN),
    "Angelehnt":                      list(_AR_STEHEND_REQUISITEN),
    "Gehend":                         list(_AR_STEHEND_REQUISITEN),
    "Vorgebeugt":                     list(_AR_VORGEBEUGT),
    "Sitzend":                        list(_AR_SITZ_BODEN),
    "Auf einem Stuhl sitzend":        list(_AR_SITZ),
    "Auf einem Hocker sitzend":       list(_AR_SITZ),
    "Auf einer Tischkante sitzend":   list(_AR_SITZ) + ["Hinter sich abgestützt"],
    "Auf dem Boden sitzend":          list(_AR_SITZ_BODEN),
    "Zurückgelehnt":                  list(_AR_ZURUECK),
    "Kniend":                         list(_AR_SITZ),
    "Auf einem Knie":                 list(_AR_SITZ),
    "Hockend":                        list(_AR_HOCKE),
    # on all fours both hands carry the body - nothing else is free
    "Auf allen Vieren":               list(_AR_VIER),
    "Auf dem Rücken liegend":         list(_AR_RUECKEN),
    "Auf dem Bauch liegend":          list(_AR_BAUCH),
    "Auf der Seite liegend":          list(_AR_SEITE),
    # The four postures of 2026-09-23 say part of the arms themselves: only
    # what agrees with that is left, as with all fours.
    "Strecken":                       ["Über dem Kopf gestreckt"],
    "In der Drehung":                 ["Seitlich hängend", "Hände auf den Hüften", "Eine Hand im Haar"],
    "Seitlich auf dem Boden":         ["Hände im Schoß", "Eine Hand am Gesicht", "Eine Hand im Haar"],
    "Bauchlage, Kinn in den Händen":  ["Auf die Unterarme gestützt"],
    "Im Schneidersitz":               ["Hände auf den Knien"],
    "Fersensitz":                     ["Hände im Schoß", "Hände auf den Knien"],
}

_BE_STEHEND = ["Geschlossen", "Leicht geöffnet", "Weit gespreizt",
               "Übereinandergeschlagen", "Knöchel gekreuzt", "Ein Knie angewinkelt"]
_BE_GEHEND = ["Leicht geöffnet", "Ein Knie angewinkelt"]
_BE_VORGEBEUGT = ["Geschlossen", "Leicht geöffnet", "Weit gespreizt",
                  "Ein Knie angewinkelt"]
_BE_SITZ = ["Geschlossen", "Leicht geöffnet", "Übereinandergeschlagen",
            "Knöchel gekreuzt", "Ein Knie angewinkelt", "Ausgestreckt",
            "Knie zusammen, Füße auseinander"]
_BE_SITZ_BODEN = ["Geschlossen", "Leicht geöffnet", "Weit gespreizt",
                  "Übereinandergeschlagen", "Angewinkelt", "Ein Knie angewinkelt",
                  "Ausgestreckt", "Untergeschlagen", "Knie zusammen, Füße auseinander"]
_BE_ZURUECK = ["Geschlossen", "Leicht geöffnet", "Übereinandergeschlagen",
               "Knöchel gekreuzt", "Angewinkelt", "Ein Knie angewinkelt", "Ausgestreckt"]
_BE_KNIE = ["Geschlossen", "Leicht geöffnet", "Ein Knie angewinkelt",
            "Knie zusammen, Füße auseinander", "Untergeschlagen"]
_BE_HOCKE = ["Geschlossen", "Leicht geöffnet", "Weit gespreizt", "Angewinkelt"]
_BE_VIER = ["Geschlossen", "Leicht geöffnet", "Knie zusammen, Füße auseinander"]
_BE_LIEGEND = ["Geschlossen", "Leicht geöffnet", "Weit gespreizt",
               "Übereinandergeschlagen", "Knöchel gekreuzt", "Angewinkelt",
               "Ein Knie angewinkelt", "Ausgestreckt"]
_BE_BAUCH = ["Geschlossen", "Leicht geöffnet", "Ein Knie angewinkelt", "Ausgestreckt",
             "Knie zusammen, Füße auseinander"]

HALTUNG_BEINE = {
    "Stehend":                        list(_BE_STEHEND),
    "Stehend, Gewicht auf einem Bein": list(_BE_STEHEND),
    "Angelehnt":                      list(_BE_STEHEND),
    # a stride is a stride: crossed or closed legs are not walking
    "Gehend":                         list(_BE_GEHEND),
    "Vorgebeugt":                     list(_BE_VORGEBEUGT),
    "Sitzend":                        list(_BE_SITZ_BODEN),
    "Auf einem Stuhl sitzend":        list(_BE_SITZ),
    "Auf einem Hocker sitzend":       list(_BE_SITZ),
    "Auf einer Tischkante sitzend":   list(_BE_SITZ),
    "Auf dem Boden sitzend":          list(_BE_SITZ_BODEN),
    "Zurückgelehnt":                  list(_BE_ZURUECK),
    "Kniend":                         list(_BE_KNIE),
    "Auf einem Knie":                 list(_BE_KNIE),
    "Hockend":                        list(_BE_HOCKE),
    "Auf allen Vieren":               list(_BE_VIER),
    "Auf dem Rücken liegend":         list(_BE_LIEGEND),
    "Auf dem Bauch liegend":          list(_BE_BAUCH),
    "Auf der Seite liegend":          list(_BE_LIEGEND),
    "Strecken":                       ["Geschlossen", "Leicht geöffnet"],
    "In der Drehung":                 list(_BE_GEHEND),
    "Seitlich auf dem Boden":         ["Angewinkelt", "Untergeschlagen"],
    "Bauchlage, Kinn in den Händen":  ["Knöchel gekreuzt"],
    "Im Schneidersitz":               ["Übereinandergeschlagen"],
    "Fersensitz":                     ["Untergeschlagen"],
}


# Selfie mode (docs/ROADMAP.md, F4). One hand holds the phone, so a selfie
# keeps only the arm positions that leave the other one free - both hands at
# the hips, on the knees or behind the head would need a third. The peace sign
# is made with the free hand, wherever a hand at the face fits the posture.
EINE_HAND_FREI = ["Eine Hand am Gesicht", "Eine Hand im Haar", "Peace-Zeichen"]
# Gestures made for the phone camera. The Series draws them on selfie photos
# only and the die skips them: appended to "arme", they would otherwise change
# what every existing series and seed rolled.
SELFIE_GESTEN = ["Peace-Zeichen"]


def arme_mit_freier_hand(haltung):
    """The arm positions of a selfie for this base posture: EINE_HAND_FREI as
    far as HALTUNG_ARME allows it (the peace sign where a hand at the face
    fits). All of EINE_HAND_FREI for a posture without a table entry, an
    empty list for one that needs both hands (all fours, stretching)."""
    erlaubt = HALTUNG_ARME.get(haltung)
    if erlaubt is None:
        return list(EINE_HAND_FREI)
    return [l for l in EINE_HAND_FREI
            if l in erlaubt or (l in SELFIE_GESTEN and "Eine Hand am Gesicht" in erlaubt)]


# Render-tested grip templates for arbitrary user props (tools/wortlabor/props_schablone.json):
# anchoring the hand at chest height with the other arm relaxed prevents bent posture
# and out-of-frame downward hanging seen with bare "holding <object>".
REQUISIT_SCHABLONE = "holding %s in one hand at chest height, the other arm relaxed"
REQUISIT_BEIDHAENDIG = ("camera", "book", "mug", "cup", "bowl", "box", "bouquet", "flowers",
                        "laptop", "tablet", "pillow", "cat", "puppy", "guitar")
_SCHON_FORMULIERT = ("holding ", "carrying ", "cradling ", "wearing ",
                     "one hand ", "both hands ", "touching ", "raising ", "making ")
_ARTIKEL_DAVOR = ("a ", "an ", "the ", "her ", "his ", "two ", "some ", "several ")


def requisit_text(roh):
    """Wrap a short English prop noun ('a vintage camera', 'red umbrella') into
    a tested grip wording unless the caller already wrote a full phrase."""
    t = " ".join(str(roh or "").strip().rstrip(",;.").split())
    if not t:
        return ""
    klein = t.casefold()
    if klein.startswith(_SCHON_FORMULIERT):
        return t
    if not klein.startswith(_ARTIKEL_DAVOR) and not klein.endswith("s"):
        t = ("an " if klein[:1] in "aeiou" else "a ") + t
        klein = t.casefold()
    if any(w in klein for w in REQUISIT_BEIDHAENDIG):
        return "holding %s with both hands in front of her chest" % t
    return REQUISIT_SCHABLONE % t


def requisit_liste(roh):
    """Split a comma- or semicolon-separated prop string into formatted grip phrases."""
    return [requisit_text(x) for x in re.split(r"[,;]+", str(roh or "")) if requisit_text(x)]


def haltung_erlaubt_requisit(haltung):
    """True if this base posture allows holding a prop (standing, sitting, reclining)."""
    if not haltung or haltung == NONE:
        return True
    erlaubt = HALTUNG_ARME.get(haltung) or []
    return any(r in erlaubt for r in REQUISITEN)


ALLE = "alle"

NONE = "—"

# The entire state except the seed sits as JSON in a hidden input; the actual
# controls live in js/pose.js. The seed deliberately stays a real widget - that
# is the only way to get control_after_generate, and stepping onwards over
# batch count hangs on exactly that.
DEFAULT_STATE = {
    "felder": {cat: NONE for cat in FOLGE},
    "wuerfeln": {},
    "gruppe": ALLE,
    "requisit": "",
    "details": "",
}


def _labels(cat):
    return [NONE] + [lbl for lbl, _ in PRESETS[cat]]


def _val(cat, label, kopie=None):
    if not label or label == NONE:
        return None
    for lbl, value in PRESETS[cat]:
        if lbl == label:
            return value
    # A custom entry (eigene.py): its file, else the copy in the node state.
    w = eigene.wert("pose", cat, label, kopie)
    if w is None and cat == "arme":
        w = eigene.wert("person", "prop", label, kopie)
        if w is not None:
            return requisit_text(w)
    return w


def _ziehe(cat, seed, erlaubt=None):
    """Draw a label from one category.

    The sub-seed is tied to the field name, so that the fields do not march in
    lockstep - otherwise arms and legs would land on the same list position
    together at every seed. random.Random seeded with a string goes through its
    SHA-512, not through PYTHONHASHSEED: same seed, same pose, even after a
    restart.
    """
    # Custom entries join the pool only from a file marked "dice": true, so
    # without one every seed rolls exactly what it always rolled.
    labels = erlaubt if erlaubt else [lbl for lbl, _ in PRESETS[cat]
                                      if lbl not in SELFIE_GESTEN and lbl not in REQUISITEN] \
        + eigene.wuerfelbar("pose", cat)
    return random.Random("%d-%s" % (seed, cat)).choice(labels)


def compose_pose(werte, details=""):
    teile = [werte[cat] for cat in FOLGE if werte.get(cat)]
    frei = (details or "").strip().rstrip(",;. \t\r\n")
    if frei:
        teile.append(frei)
    return ", ".join(teile)


class Krea2PoseBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        # PoseState is `hidden`, not `required`: hidden inputs produce neither
        # a widget nor an input dot in the Vue front end. The JS side keeps the
        # state in node.properties and pushes it in here on execution, through
        # a graphToPrompt hook.
        return {
            "required": {
                # control_after_generate steps the seed onwards after every
                # queued run - exactly the way the KSampler varies its own noise
                # over batch count.
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True}),
            },
            "hidden": {
                "PoseState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("pose",)
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Setzt eine Koerperhaltung zusammen. Ausgang an den Eingang "
                   "'pose' von 'Photoshoot Prompt bauen' haengen und im Text mit "
                   "{pose} platzieren - moeglichst weit vorn.")

    def build(self, seed=0, PoseState=None):
        try:
            state = json.loads(PoseState) if PoseState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Pose] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        felder = state.get("felder") or {}
        wuerfeln = state.get("wuerfeln") or {}
        gruppe = state.get("gruppe") or ALLE

        werte = {}
        labels = {}
        for cat in FOLGE:
            if wuerfeln.get(cat):
                erlaubt = None
                if cat == "haltung" and gruppe != ALLE:
                    erlaubt = HALTUNG_GRUPPEN.get(gruppe)
                # Body tension has to fit the base posture - see
                # HALTUNG_SPANNUNG. FOLGE puts haltung first, so it is settled
                # here whether it was rolled or picked from the dropdown.
                elif cat == "spannung" and labels.get("haltung"):
                    erlaubt = HALTUNG_SPANNUNG.get(labels["haltung"]) or None
                label = _ziehe(cat, seed, erlaubt)
            else:
                label = felder.get(cat)
            labels[cat] = label
            werte[cat] = _val(cat, label, state.get("eigene"))
        if not wuerfeln.get("arme") and (state.get("requisit") or "").strip():
            werte["arme"] = requisit_text(state["requisit"])
        return (compose_pose(werte, state.get("details", "")),)


NODE_CLASS_MAPPINGS = {"Krea2PoseBuilder": Krea2PoseBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2PoseBuilder": "Photoshoot – Pose"}


if __name__ == "__main__":
    s = compose_pose({
        "haltung": "sitting on a stool",
        "raum": "near a window",
        "koerper": "facing the camera directly",
        "arme": "both arms held behind the back, hands clasped together",
        "beine": "legs spread wide apart",
        "spannung": "shoulders drawn back",
    })
    print(s)
    assert "near a window" in s
    assert FOLGE.index("raum") == 1
    assert arme_mit_freier_hand("Auf allen Vieren") == []
    assert arme_mit_freier_hand("Stehend") == EINE_HAND_FREI
    assert "Peace-Zeichen" in arme_mit_freier_hand("Seitlich auf dem Boden")
    assert set(EINE_HAND_FREI) <= {l for l, _ in PRESETS["arme"]}
    print("ok")
