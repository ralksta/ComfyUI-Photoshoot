"""
Expression - assemble a facial expression from dropdowns.

Returns a STRING that goes into the "ausdruck" input of "build prompt", where
it replaces the {ausdruck} placeholder.

Deliberately kept apart from the Person Builder: a saved person should stay the
same across many images, while the expression changes in every one. Were it
part of the person, you would have to keep "X smiling", "X serious", "X
dreamy" as separate entries and update all of them on every change to the face.

None of the wordings use a possessive pronoun ("biting the lower lip" rather
than "her lower lip"), so the same expression fits any figure.

Dice: when "wuerfeln_<field>" is on, that field's dropdown is ignored and a
value is drawn from the list instead. Together with batch count (the number
field next to the queue button) and the seed widget, every run gets a different
expression that way. "stimmung_gruppe" keeps the spread in check - on
"friendly" the figure stays friendly and only the shading changes.
"""

import json
import random

PRESETS = {
    # Grouped into families, so that the list stays navigable despite its
    # length - the dropdown also has a search field.
    "stimmung": [
        # calm
        ("Neutral", "a neutral expression"),
        ("Entspannt", "a relaxed expression"),
        ("Zufrieden", "a content expression"),
        ("Gelassen", "a calm, serene expression"),
        ("Stoisch", "a stoic, impassive expression"),
        ("Unbeeindruckt", "an unimpressed expression"),
        # friendly
        ("Sanftes Lächeln", "a soft gentle smile"),
        ("Warmes Lächeln", "a warm inviting smile"),
        ("Strahlend", "a beaming, radiant smile"),
        ("Breites Lachen", "laughing openly"),
        ("Kichernd", "giggling"),
        ("Fröhlich", "a happy, joyful expression"),
        ("Amüsiert", "an amused expression"),
        ("Schelmisch", "a mischievous, playful expression"),
        ("Verschmitzt", "an impish grin"),
        ("Erleichtert", "a relieved expression"),
        # inward
        ("Verträumt", "a soft dreamy expression"),
        ("Sehnsüchtig", "a longing, yearning expression"),
        ("Wehmütig", "a wistful expression"),
        ("Nachdenklich", "a pensive expression"),
        ("Grüblerisch", "a brooding expression"),
        ("Abwesend", "a distant, absent-minded expression"),
        ("Verloren", "a lost, faraway expression"),
        ("Melancholisch", "a melancholic expression"),
        # assertive
        ("Selbstbewusst", "a confident expression"),
        ("Dominant", "a dominant, commanding expression"),
        ("Herrisch", "an imperious expression"),
        ("Fordernd", "a demanding expression"),
        ("Unnachgiebig", "an unyielding, implacable expression"),
        ("Streng", "a stern expression"),
        ("Ernst", "a serious expression"),
        ("Konzentriert", "a focused, concentrated expression"),
        ("Berechnend", "a calculating expression"),
        ("Kühl", "a cool, aloof expression"),
        ("Arrogant", "a haughty, arrogant expression"),
        ("Herablassend", "a condescending expression"),
        ("Spöttisch", "a mocking, smug expression"),
        ("Verächtlich", "a contemptuous expression"),
        ("Triumphierend", "a triumphant expression"),
        ("Trotzig", "a defiant expression"),
        ("Herausfordernd", "a challenging expression"),
        # warm, turned towards
        ("Zärtlich", "a tender, affectionate expression"),
        ("Hingebungsvoll", "a devoted, adoring expression"),
        ("Kokett", "a flirtatious expression"),
        ("Flirtend", "flirting, playfully teasing"),
        ("Neckisch", "a teasing expression"),
        ("Verführerisch", "a seductive expression"),
        ("Lasziv", "a sultry, languid expression"),
        ("Anzüglich", "a suggestive expression"),
        ("Verlangend", "a wanting, craving expression"),
        ("Begierig", "an eager, hungry expression"),
        ("Erregt", "an aroused expression"),
        ("Leidenschaftlich", "a passionate expression"),
        ("Lustvoll", "a blissful, pleasured expression"),
        ("Atemlos", "a breathless expression"),
        ("Überwältigt", "an overwhelmed expression"),
        ("Ekstatisch", "an ecstatic expression"),
        ("Unterwürfig", "a submissive expression"),
        ("Schüchtern", "a shy, bashful expression"),
        ("Verlegen", "an embarrassed expression"),
        ("Unschuldig", "an innocent, wide-eyed expression"),
        # alert
        ("Überrascht", "a surprised expression"),
        ("Erwartungsvoll", "an expectant expression"),
        ("Neugierig", "a curious expression"),
        ("Skeptisch", "a skeptical expression"),
        ("Misstrauisch", "a wary, distrustful expression"),
        ("Angespannt", "a tense expression"),
        ("Nervös", "a nervous expression"),
        # afraid
        ("Erschrocken", "a startled expression"),
        ("Alarmiert", "an alarmed expression"),
        ("Besorgt", "a worried expression"),
        ("Ängstlich", "a frightened expression"),
        ("Panisch", "a panicked expression"),
        ("Schockiert", "a shocked expression"),
        ("Fassungslos", "a stunned, disbelieving expression"),
        ("Benommen", "a dazed expression"),
        # sad
        ("Traurig", "a sad expression"),
        ("Den Tränen nahe", "on the verge of tears"),
        ("Weinend", "crying, tears running down the face"),
        ("Verzweifelt", "a desperate expression"),
        ("Untröstlich", "an inconsolable, grief-stricken expression"),
        ("Leidend", "a pained expression"),
        ("Resigniert", "a resigned expression"),
        ("Erschöpft", "an exhausted, weary expression"),
        # dismissive
        ("Genervt", "an annoyed expression"),
        ("Bitter", "a bitter expression"),
        ("Wütend", "an angry expression"),
        ("Rasend", "a furious, enraged expression"),
        ("Angewidert", "a disgusted expression"),
        ("Gelangweilt", "a bored expression"),
    ],
    # The secondary fields had to grow along: "panicked" wants a wide-open eye
    # and an open mouth, and if all that is on offer there is "half closed" and
    # "lips pursed", the face contradicts the mood.
    "augen": [
        ("Weit geöffnet", "wide open eyes"),
        ("Aufgerissen", "eyes wide with alarm"),
        ("Starr", "a fixed, unblinking stare"),
        ("Halb geschlossen", "half-closed eyes"),
        ("Geschlossen", "eyes closed"),
        ("Fest zugekniffen", "eyes squeezed shut"),
        ("Zusammengekniffen", "narrowed eyes"),
        ("Flackernd", "restless, darting eyes"),
        ("Tränenfeucht", "glistening teary eyes"),
        ("Verweint", "red, tear-stained eyes"),
        ("Nach oben verdreht", "eyes rolled upward"),
        ("Fester Blick", "a steady focused gaze"),
    ],
    "blick": [
        ("In die Kamera", "looking directly at the camera"),
        ("An der Kamera vorbei", "looking past the camera"),
        ("Ins Leere", "staring into nothing"),
        ("Nach unten", "looking down"),
        ("Nach oben", "looking up"),
        ("Von unten herauf", "looking up from beneath the brows"),
        ("Zur Seite", "looking to the side"),
        ("Über die Schulter", "glancing back over the shoulder"),
        ("Zum Gegenüber", "looking at the other person"),
    ],
    "mund": [
        ("Geschlossen", "lips closed"),
        ("Zusammengepresst", "lips pressed tightly together"),
        ("Leicht geöffnet", "lips slightly parted"),
        ("Lippen gespitzt", "pursed lips"),
        ("Unterlippe gebissen", "biting the lower lip"),
        ("Halbes Lächeln", "a faint half-smile"),
        ("Zähne sichtbar", "showing teeth"),
        ("Zähne gefletscht", "teeth bared"),
        ("Weit geöffnet", "mouth open"),
        ("Keuchend", "mouth open, breathing hard"),
        ("Schreiend", "mouth open in a scream"),
        ("Mundwinkel herabgezogen", "corners of the mouth turned down"),
        ("Verzogen", "mouth twisted"),
    ],
    "brauen": [
        ("Entspannt", "relaxed brows"),
        ("Hochgezogen", "raised eyebrows"),
        ("Eine hochgezogen", "one eyebrow raised"),
        ("Gesenkt", "lowered brows"),
        ("Zusammengezogen", "furrowed brows"),
        # Raised AND drawn together is the signature of fear and grief - the
        # two separate values cannot express it.
        ("Hoch und zusammengezogen", "brows raised and drawn together"),
    ],
    "kopf": [
        ("Gerade", "head held straight"),
        ("Leicht geneigt", "head tilted slightly"),
        ("Kinn angehoben", "chin lifted"),
        ("Kinn gesenkt", "chin lowered"),
        ("Gesenkt", "head bowed"),
        ("Zurückgeworfen", "head thrown back"),
        ("Nach vorn gebeugt", "head leaning forward"),
        ("Zur Seite gedreht", "head turned to the side"),
        ("Weggedreht", "head turned away"),
    ],
}

# Order within the sentence: base mood first, then top to bottom through the
# face, head position last.
FOLGE = ["stimmung", "augen", "blick", "brauen", "mund", "kopf"]

# Families of the base mood - the same groups PRESETS["stimmung"] above is
# sorted by. Drawing can be restricted to one of them, otherwise the same
# figure swings between ecstatic and bored.
# "tense" and "withdrawn" were split up along the way. They held six entries
# each and threw alertness together with fear, and grief together with
# rejection; drawing at random, the same figure came out curious one time and
# panicked the next.
STIMMUNG_GRUPPEN = {
    "ruhig": ["Neutral", "Entspannt", "Zufrieden", "Gelassen", "Stoisch",
              "Unbeeindruckt"],
    "freundlich": ["Sanftes Lächeln", "Warmes Lächeln", "Strahlend",
                   "Breites Lachen", "Kichernd", "Fröhlich", "Amüsiert",
                   "Schelmisch", "Verschmitzt", "Erleichtert"],
    "in sich gekehrt": ["Verträumt", "Sehnsüchtig", "Wehmütig", "Nachdenklich",
                        "Grüblerisch", "Abwesend", "Verloren", "Melancholisch"],
    "bestimmend": ["Selbstbewusst", "Dominant", "Herrisch", "Fordernd",
                   "Unnachgiebig", "Streng", "Ernst", "Konzentriert",
                   "Berechnend", "Kühl", "Arrogant", "Herablassend",
                   "Spöttisch", "Verächtlich", "Triumphierend", "Trotzig",
                   "Herausfordernd"],
    "zugewandt": ["Zärtlich", "Hingebungsvoll", "Kokett", "Flirtend",
                  "Neckisch", "Verführerisch", "Lasziv", "Anzüglich",
                  "Verlangend", "Begierig", "Erregt", "Leidenschaftlich",
                  "Lustvoll", "Atemlos", "Überwältigt", "Ekstatisch",
                  "Unterwürfig", "Schüchtern", "Verlegen", "Unschuldig"],
    "wachsam": ["Überrascht", "Erwartungsvoll", "Neugierig", "Skeptisch",
                "Misstrauisch", "Angespannt", "Nervös"],
    "verängstigt": ["Erschrocken", "Alarmiert", "Besorgt", "Ängstlich",
                    "Panisch", "Schockiert", "Fassungslos", "Benommen"],
    "traurig": ["Traurig", "Den Tränen nahe", "Weinend", "Verzweifelt",
                "Untröstlich", "Leidend", "Resigniert", "Erschöpft"],
    "abweisend": ["Genervt", "Bitter", "Wütend", "Rasend", "Angewidert",
                  "Gelangweilt"],
}

ALLE = "alle"

NONE = "—"

# The entire state except the seed sits as JSON in a hidden input; the actual
# controls live in js/expression.js. The seed deliberately stays a real widget -
# that is the only way to get control_after_generate, and stepping onwards over
# batch count hangs on exactly that.
DEFAULT_STATE = {
    "felder": {cat: NONE for cat in
               ["stimmung", "augen", "blick", "brauen", "mund", "kopf"]},
    "wuerfeln": {},
    "gruppe": ALLE,
    "details": "",
}


def _labels(cat):
    return [NONE] + [lbl for lbl, _ in PRESETS[cat]]


def _val(cat, label):
    if not label or label == NONE:
        return None
    for lbl, value in PRESETS[cat]:
        if lbl == label:
            return value
    return None


def _ziehe(cat, seed, erlaubt=None):
    """Draw a label from one category.

    The sub-seed is tied to the field name, so that the fields do not march in
    lockstep - otherwise eyes and mouth would land on the same list position
    together at every seed. random.Random seeded with a string goes through its
    SHA-512, not through PYTHONHASHSEED: same seed, same expression, even after
    a restart.
    """
    labels = erlaubt if erlaubt else [lbl for lbl, _ in PRESETS[cat]]
    return random.Random("%d-%s" % (seed, cat)).choice(labels)


def compose_expression(werte, details=""):
    teile = [werte[cat] for cat in FOLGE if werte.get(cat)]
    frei = (details or "").strip().rstrip(",;. \t\r\n")
    if frei:
        teile.append(frei)
    return ", ".join(teile)


class Krea2ExpressionBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        # ExpressionState is `hidden`, not `required`: hidden inputs produce
        # neither a widget nor an input dot in the Vue front end. The JS side
        # keeps the state in node.properties and pushes it in here on
        # execution, through a graphToPrompt hook.
        return {
            "required": {
                # control_after_generate steps the seed onwards after every
                # queued run - exactly the way the KSampler varies its own noise
                # over batch count.
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                                 "control_after_generate": True}),
            },
            "hidden": {
                "ExpressionState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ausdruck",)
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Setzt einen Gesichtsausdruck zusammen. Ausgang an den Eingang "
                   "'ausdruck' von 'Photoshoot Prompt bauen' haengen, im Text mit "
                   "{ausdruck} platzieren - moeglichst weit vorn.")

    def build(self, seed=0, ExpressionState=None):
        try:
            state = json.loads(ExpressionState) if ExpressionState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Expression] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        felder = state.get("felder") or {}
        wuerfeln = state.get("wuerfeln") or {}
        gruppe = state.get("gruppe") or ALLE

        werte = {}
        for cat in FOLGE:
            if wuerfeln.get(cat):
                erlaubt = None
                if cat == "stimmung" and gruppe != ALLE:
                    erlaubt = STIMMUNG_GRUPPEN.get(gruppe)
                label = _ziehe(cat, seed, erlaubt)
            else:
                label = felder.get(cat)
            werte[cat] = _val(cat, label)
        return (compose_expression(werte, state.get("details", "")),)


NODE_CLASS_MAPPINGS = {"Krea2ExpressionBuilder": Krea2ExpressionBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2ExpressionBuilder": "Photoshoot Ausdruck"}


if __name__ == "__main__":
    print(compose_expression({
        "stimmung": "a soft dreamy expression", "augen": "half-closed eyes",
        "blick": "looking directly at the camera", "mund": "lips slightly parted",
        "brauen": "relaxed brows", "kopf": "head tilted slightly",
    }, "blushing cheeks"))
