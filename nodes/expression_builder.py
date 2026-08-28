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
        ("Neutral", "a calm neutral face, relaxed natural facial features, calm composed expression"),
        ("Entspannt", "a deeply relaxed expression, softened facial features, gentle at-ease composure"),
        ("Zufrieden", "a content peaceful expression, gentle subtle warmth, tranquil facial features"),
        ("Gelassen", "a serene composed expression, smooth unbothered features, calm steady stillness"),
        ("Stoisch", "a stoic impassive expression, completely unmoving facial features, unwavering flat gaze"),
        ("Unbeeindruckt", "an unimpressed deadpan expression, unblinking neutral eyes, totally unmoved flat mouth"),
        # friendly
        ("Sanftes Lächeln", "a soft gentle smile, tender upturned mouth corners, warm relaxed eyes"),
        ("Warmes Lächeln", "a warm friendly smile, crinkled crinkles at the eyes, inviting open face"),
        ("Strahlend", "a beaming radiant smile, bright wide toothy smile, glowing joyful crinkled eyes"),
        ("Breites Lachen", "laughing heartily out loud, wide open laughing mouth showing teeth, joyful squinted eyes"),
        ("Kichernd", "giggling playfully, hand covering a suppressed grinning mouth, amused crinkled eyes"),
        ("Fröhlich", "a bright cheerful happy expression, buoyant lively smile, joyful open face"),
        ("Amüsiert", "an amused delighted expression, suppressed chuckling smirk, twinkling lively eyes"),
        ("Schelmisch", "a mischievous playful expression, sly asymmetric half-grin, roguish glint in the eyes"),
        ("Verschmitzt", "an impish cheeky grin, crooked smirk, playful mischievous eyes"),
        ("Erleichtert", "a relieved comforted expression, long exhaling breath, softened shoulders and loosened jaw"),
        # inward
        ("Verträumt", "a soft dreamy faraway expression, hazy unfocused eyes gazing into distance, relaxed parted lips"),
        ("Sehnsüchtig", "a longing yearning expression, wistful distant gaze, soft melancholic eyes, slightly parted lips"),
        ("Wehmütig", "a wistful nostalgic expression, gentle bittersweet half-smile, faintly sorrowful eyes"),
        ("Nachdenklich", "a deep pensive expression, introspective contemplative gaze looking away, pressed lips, slight brow furrow"),
        ("Grüblerisch", "a brooding troubled expression, heavily furrowed brow, dark intense downward gaze, tightly set jaw"),
        ("Abwesend", "an absent-minded vacant stare, glazed unfocused eyes staring into nothing, blank expression"),
        ("Verloren", "a lost bewildered expression, vulnerable faraway gaze, faint tremble in the lips"),
        ("Melancholisch", "a quiet melancholic expression, sorrowful heavy-lidded eyes, subtly downturned corners of the mouth"),
        # assertive
        ("Selbstbewusst", "a confident poised expression, direct unwavering eye contact, self-assured subtle smirk, firm jaw"),
        ("Dominant", "a commanding dominant expression, intense penetrating direct glare, firm set jaw, authoritative composure"),
        ("Herrisch", "an imperious haughty expression, raised chin looking down the nose, sharp demanding gaze"),
        ("Fordernd", "a sharp demanding expression, intensely focused piercing gaze, firm unyielding lips"),
        ("Unnachgiebig", "an unyielding implacable expression, tightly locked jaw, hard resolute gaze, stone-faced"),
        ("Streng", "a stern severe expression, drawn together hard eyebrows, tightly compressed straight lips"),
        ("Ernst", "a grave serious expression, unsmiling mouth, solemn intense gaze, steady focused brow"),
        ("Konzentriert", "a deeply concentrated laser-focused expression, narrowed sharp eyes, furrowed brow, tight focused mouth"),
        ("Berechnend", "a cold calculating expression, sharp analytical narrowed eyes, subtle restrained smirk"),
        ("Kühl", "a cool aloof expression, frosty detached gaze, impassive aristocratic face, chin slightly lifted"),
        ("Arrogant", "a haughty arrogant expression, chin raised high looking down at the viewer, condescending smirk"),
        ("Herablassend", "a condescending patronizing expression, smug asymmetric lip curl, disdainful hooded eyes"),
        ("Spöttisch", "a mocking smug expression, sharp cynical one-sided smirk, arched brow, derisive glint in the eyes"),
        ("Verächtlich", "a sneering contemptuous expression, curled upper lip in disgust, disdainful narrowing eyes"),
        ("Triumphierend", "a triumphant victorious expression, exultant broad grin, gleaming proud eyes, lifted chin"),
        ("Trotzig", "a defiant rebellious expression, stubborn thrust-out chin, fiery unyielding glare, pressed firm lips"),
        ("Herausfordernd", "a bold challenging expression, head cocked back, intense direct stare, provocative slight grin"),
        # warm, turned towards
        ("Zärtlich", "a tender affectionate expression, warm softened eyes full of love, gentle delicate smile"),
        ("Hingebungsvoll", "a devoted adoring expression, reverent glowing eyes gazing softly, open affectionate face"),
        ("Kokett", "a coy flirtatious expression, coyly tilted head looking up through lashes, subtle inviting half-smile"),
        ("Flirtend", "a flirtatious teasing expression, playful wink, alluring smile, dynamic teasing gaze"),
        ("Neckisch", "a cheeky teasing expression, tongue pressed against cheek, playful smirk, narrowed winking eyes"),
        ("Verführerisch", "a seductive alluring expression, biting the lower lip, heavy-lidded sultry bedroom eyes, sensual gaze"),
        ("Lasziv", "a sultry lascivious expression, heavy hooded languid eyes, sensually parted lips, breathy sensual tension"),
        ("Anzüglich", "a suggestive expression, knowing provocative smirk, sultry lingering gaze"),
        ("Verlangend", "a craving longing expression, dilated pupils, hungrily parted trembling lips, intense gaze"),
        ("Begierig", "an eager ravenous expression, hungry passionate gaze, parted lips, excited intensity"),
        ("Erregt", "an intensely aroused expression, flushed cheeks, heavy breathy parted lips, dilated sultry eyes"),
        ("Leidenschaftlich", "a fiery passionate expression, fervent intense gaze, breathless parted lips, emotional heat"),
        ("Lustvoll", "a blissful ecstatic expression, closed eyes in pure pleasure, tilted back head, soft open lips"),
        ("Atemlos", "a breathless gasping expression, parted trembling lips taking in air, wide glistening eyes"),
        ("Überwältigt", "an overwhelmed emotional expression, hand near chest, glistening eyes wide with awe, parted lips"),
        ("Ekstatisch", "an ecstatic rapturous expression, euphoric glowing face, head tilted back with wide open joyful smile"),
        ("Unterwürfig", "a timid submissive expression, lowered chin looking up through brows, averted shy gaze, soft parted lips"),
        ("Schüchtern", "a shy bashful expression, blushing red cheeks, eyes looking down and away, timid gentle smile"),
        ("Verlegen", "an embarrassed flustered expression, flushed pink cheeks, sheepish awkward half-smile, averted nervous eyes"),
        ("Unschuldig", "an innocent wide-eyed expression, wide clear guileless eyes, naive gentle mouth, soft youthful face"),
        # alert
        ("Überrascht", "shocked gasping face, mouth wide open in shock, dropped agape jaw, round wide open eyes"),
        ("Erwartungsvoll", "an expectant keen expression, leaned-forward posture, bright wide attentive eyes, poised anticipation"),
        ("Neugierig", "an inquisitive curious expression, head cocked to one side, arched eyebrow, intently probing eyes"),
        ("Skeptisch", "skeptical doubtful squint, one eye narrowed squinting, one sharply arched raised eyebrow, questioning cynical smirk"),
        ("Misstrauisch", "a suspicious distrustful expression, guarded narrowed eyes, tense tightened jaw, wary sidelong glance"),
        ("Angespannt", "a tense stressed expression, tightly clenched jaw muscles, strained neck tendons, guarded vigilant eyes"),
        ("Nervös", "a nervous apprehensive expression, bitten lower lip, darting restless eyes, tense worried face"),
        # afraid
        ("Erschrocken", "startled gasping face, mouth dropped open in shock, round wide alarmed eyes"),
        ("Alarmiert", "an alarmed panicked expression, wide vigilant eyes, knitted high brow, tense gasping breath"),
        ("Besorgt", "a deeply worried anxious expression, knitted furrowed eyebrows, troubled eyes, downturned uneasy mouth"),
        ("Ängstlich", "a frightened fearful expression, eyes wide with terror, trembling lips, raised and knitted eyebrows"),
        ("Panisch", "terrified gasping in horror, hands clutching face in pure panic, wide terrified eyes showing white sclera, brows raised and drawn together in terror, gasping open mouth"),
        ("Schockiert", "shocked horrified gasping face, jaw dropped wide open in astonishment, wide staring eyes"),
        ("Fassungslos", "a stunned disbelieving expression, mouth slightly agape in utter disbelief, motionless dazed wide eyes"),
        ("Benommen", "a dazed concussed expression, unfocused sluggish half-closed eyes, slack limp jaw, disoriented face"),
        # sad
        ("Traurig", "a sad dejected expression, heavily downturned mouth corners, sorrowful moist eyes, slumped brows"),
        ("Den Tränen nahe", "on the verge of tears, brimming glistening teary eyes, quivering trembling lower lip, grief-stricken face"),
        ("Weinend", "crying weeping face with real tears, glistening wet tears streaming down cheeks, furrowed brow, quivering downturned mouth"),
        ("Verzweifelt", "a desperate agonized expression, weeping with furrowed contracted brow, anguished trembling mouth"),
        ("Untröstlich", "an inconsolable heartbroken expression, face twisted in immense grief, streaming tears, clenched sobbing eyes"),
        ("Leidend", "a pained suffering expression, grimacing with tightly squeezed eyes, furrowed brow, strained tense mouth"),
        ("Resigniert", "a defeated resigned expression, hopeless hollow eyes, slack mouth, heavy defeated downward gaze"),
        ("Erschöpft", "an exhausted weary expression, heavy drooping eyelids, dark under-eye shadows, totally drained slack face"),
        # dismissive
        ("Genervt", "an annoyed irritated expression, exasperated rolled upward eyes, tightly pressed lips in vexation"),
        ("Bitter", "a bitter resentful expression, downturned grim mouth, cold resentful eyes, hardened sour face"),
        ("Wütend", "angry snarling scowl, bared clenching teeth, intense scowling furrowed brow, fierce raging angry glare"),
        ("Rasend", "furiously shouting in rage, wide open angry mouth showing teeth, scowling furrowed brow"),
        ("Angewidert", "a disgusted repulsed expression, wrinkled crinkled nose, curled raised upper lip in distaste, narrowed revolted eyes"),
        ("Gelangweilt", "a completely bored uninterested expression, resting cheek on hand, half-closed heavy eyelids, deadpan unimpressed mouth"),
    ],
    # The secondary fields had to grow along: "panicked" wants a wide-open eye
    # and an open mouth, and if all that is on offer there is "half closed" and
    # "lips pursed", the face contradicts the mood.
    "augen": [
        ("Weit geöffnet", "wide open eyes"),
        ("Aufgerissen", "eyes wide with alarm, visible sclera"),
        ("Starr", "a fixed, unblinking stare"),
        ("Halb geschlossen", "half-closed heavy-lidded eyes"),
        ("Geschlossen", "eyes closed"),
        ("Fest zugekniffen", "eyes squeezed tightly shut with crinkles"),
        ("Zusammengekniffen", "narrowed squinting eyes"),
        ("Flackernd", "restless, darting eyes"),
        ("Tränenfeucht", "glistening teary eyes brimming with moisture"),
        ("Verweint", "red, puffy tear-stained crying eyes"),
        ("Nach oben verdreht", "eyes rolled upward in exasperation"),
        ("Fester Blick", "a steady focused piercing gaze"),
    ],
    "blick": [
        ("In die Kamera", "looking directly at the camera"),
        ("An der Kamera vorbei", "looking past the camera"),
        ("Ins Leere", "staring into nothing, unfocused gaze"),
        ("Nach unten", "looking down"),
        ("Nach oben", "looking up"),
        ("Von unten herauf", "looking up from beneath lowered brows"),
        ("Zur Seite", "looking to the side"),
        ("Über die Schulter", "glancing back over the shoulder"),
        ("Zum Gegenüber", "looking at the other person"),
    ],
    "mund": [
        ("Geschlossen", "lips closed"),
        ("Zusammengepresst", "lips pressed tightly together"),
        ("Leicht geöffnet", "lips slightly parted, relaxed jaw"),
        ("Lippen gespitzt", "pursed lips, pout"),
        ("Unterlippe gebissen", "biting the lower lip with teeth"),
        ("Halbes Lächeln", "a faint asymmetric half-smile"),
        ("Zähne sichtbar", "showing teeth in a smile"),
        ("Zähne gefletscht", "teeth bared in an aggressive snarl"),
        ("Weit geöffnet", "mouth wide open"),
        ("Keuchend", "mouth open, panting, breathing hard"),
        ("Schreiend", "mouth wide open in a scream"),
        ("Mundwinkel herabgezogen", "corners of the mouth pulled sharply down"),
        ("Verzogen", "mouth twisted in a grimace"),
    ],
    "brauen": [
        ("Entspannt", "relaxed brows"),
        ("Hochgezogen", "raised arched eyebrows"),
        ("Eine hochgezogen", "one eyebrow raised skeptically"),
        ("Gesenkt", "lowered brow line"),
        ("Zusammengezogen", "deeply furrowed brows"),
        # Raised AND drawn together is the signature of fear and grief - the
        # two separate values cannot express it.
        ("Hoch und zusammengezogen", "brows raised and drawn together with worry"),
    ],
    "kopf": [
        ("Gerade", "head held straight"),
        ("Leicht geneigt", "head tilted slightly"),
        ("Kinn angehoben", "chin lifted with confidence"),
        ("Kinn gesenkt", "chin lowered"),
        ("Gesenkt", "head bowed down"),
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

# Eyes and mouth against the mood, and this one is written as an exclusion list
# rather than as nine near-identical tables: almost every option fits almost
# every mood - closed eyes, a half smile, a tilted head belong anywhere - and
# only a dozen are tied to something particular. Naming those dozen says what
# is true; nine tables repeating the free ones would bury it.
#
# It mattered more than the pose couplings did. 273 of 500 runs drew a face
# that contradicted its own mood: "flirting, tear-stained eyes", "gentle smile,
# eyes squeezed shut", "unyielding, eyes rolled up". The model does not refuse
# those either - it averages them, and the result reads as a model that cannot
# hit an expression rather than as a prompt asking for two.
#
# Gaze and head are deliberately absent. Looking away or tilting the head suits
# any mood there is.
STIMMUNG_NUR_FUER = {
    ("augen", "Aufgerissen"):        {"wachsam", "verängstigt", "abweisend"},
    ("augen", "Tränenfeucht"):       {"traurig", "in sich gekehrt", "zugewandt"},
    ("augen", "Verweint"):           {"traurig"},
    ("augen", "Fest zugekniffen"):   {"verängstigt", "traurig", "abweisend"},
    ("augen", "Nach oben verdreht"): {"abweisend", "zugewandt"},

    ("mund", "Zähne gefletscht"):    {"abweisend"},
    ("mund", "Schreiend"):           {"verängstigt", "abweisend"},
    ("mund", "Keuchend"):            {"zugewandt", "verängstigt"},
    ("mund", "Weit geöffnet"):       {"wachsam", "verängstigt", "abweisend"},
    ("mund", "Mundwinkel herabgezogen"): {"traurig", "abweisend"},
    ("mund", "Verzogen"):            {"traurig", "abweisend", "verängstigt"},
    ("mund", "Unterlippe gebissen"): {"zugewandt", "wachsam", "in sich gekehrt"},

    # The only brow that carries a mood of its own - raised *and* knitted is
    # worry. The other five suit anything.
    ("brauen", "Hoch und zusammengezogen"):
        {"verängstigt", "traurig", "wachsam", "in sich gekehrt"},
}

_FAMILIE = {m: f for f, ms in STIMMUNG_GRUPPEN.items() for m in ms}


def familie_von(stimmung):
    """Which family a mood belongs to, or None."""
    return _FAMILIE.get(stimmung)


def passt_zur_stimmung(cat, label, familie):
    """False only when this label is tied to families that exclude this one."""
    erlaubt = STIMMUNG_NUR_FUER.get((cat, label))
    return erlaubt is None or familie is None or familie in erlaubt


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
