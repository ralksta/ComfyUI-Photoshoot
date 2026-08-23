"""
Person Builder - describe one person across 44 fields.

The logic (ordering, special cases such as lipstick finish, nail colour,
possessive pronouns, exact age) follows the composePerson function this node
was ported from.

The controls live in js/person.mjs: 44 fields stacked vertically would run well
over 800 pixels tall, hence the tabs. The node itself has no widgets, the state
sits as JSON in a hidden input - as with pose and expression. Unlike those,
there is deliberately no seed and no dice here: a person should stay the same
across many images.

Two outputs: "person" is always the full description, "person_data" is the
value dict as JSON. Only the latter lets the photoshoot shorten the block per
framing (see compose_person and detail_fuer_kamera) - a finished sentence
cannot be taken apart again reliably.

Self-test:  python -m nodes.person_builder   (from the package folder)
"""

import json

# ─────────────────────────────────────────────────────────────────────────────
# PRESETS:  category -> list of (German label, English value)
# Colour categories (skinTone/eyes/hairColor/lipColor/nailColor) supply only the
# colour word; compose() adds the suffix (" skin", " eyes", " hair", " nails").
# hair holds a template with {c} = hair colour.
# ─────────────────────────────────────────────────────────────────────────────
PRESETS = {
    "type": [
        ("Frau", "a woman"), ("Junge Frau", "a young woman"),
        ("Mann", "a man"), ("Junger Mann", "a young man"), ("Person", "a person"),
    ],
    "age": [  # {p} = her/his/their
        ("Anfang 20", "in {p} early 20s"), ("Mitte 20", "in {p} mid 20s"),
        ("Ende 20", "in {p} late 20s"), ("Anfang 30", "in {p} early 30s"),
        ("Mitte 30", "in {p} mid 30s"), ("Ende 30", "in {p} late 30s"),
        ("40er", "in {p} 40s"), ("50er", "in {p} 50s"), ("60+", "in {p} 60s"),
    ],
    "ethnicity": [
        ("Osteuropäisch", "Eastern European features"),
        ("Skandinavisch", "Scandinavian features"),
        ("Mediterran", "Mediterranean features"),
        ("Nahöstlich", "Middle Eastern features"),
        ("Latina", "Latina features"),
        ("Ostasiatisch", "East Asian features"),
        ("Südostasiatisch", "Southeast Asian features"),
        ("Südasiatisch", "South Asian features"),
        ("Afrikanisch", "African features"),
        ("Gemischt", "mixed ethnicity features"),
    ],
    "skinTone": [  # -> "<wert> skin"
        ("Sehr hell", "very fair"), ("Hell", "fair"), ("Hell gebräunt", "light tan"),
        ("Gebräunt", "tan"), ("Oliv", "olive"), ("Braun", "brown"), ("Dunkelbraun", "deep brown"),
    ],
    # Complexion, independent of the colour. Deliberately without the word
    # "skin" - that already stands in the line before, otherwise it would read
    # "very fair skin, dewy luminous skin".
    "complexion": [
        ("Dewy", "with a dewy luminous finish"),
        ("Matt", "with a matte finish"),
        ("Porzellan", "with a smooth porcelain finish"),
        ("Natürliche Poren", "with natural texture and visible pores"),
        ("Sonnengegerbt", "weathered and sun-tanned"),
        ("Rötlich", "with a rosy flush"),
        ("Blass", "pale and translucent"),
    ],
    "height": [
        ("Zierlich", "petite, short stature"), ("Durchschnittlich", "average height"),
        ("Groß", "tall"), ("Model-Größe", "very tall, model height"),
    ],
    "figure": [
        ("Sehr schlank", "very slim, slender build"), ("Schlank", "slim build"),
        ("Athletisch", "athletic, toned physique"), ("Durchschnittlich", "average build"),
        ("Kurvig", "curvy figure"), ("Sanduhr", "hourglass figure"),
        ("Mollig", "chubby, soft curves"), ("Plus-Size", "plus-size, full-figured"),
        ("Muskulös", "muscular, fit"),
    ],
    "bust": [
        ("Klein", "small bust"), ("Mittel", "medium bust"),
        ("Voll", "full bust"), ("Groß", "large bust"),
    ],
    # ── Body ─────────────────────────────────────────────────────────────────
    # A counterweight to being head-heavy. Before these fields existed the
    # builder described thirteen head features against six body ones, and image
    # models hand out frame area roughly by that weighting. It is twelve against
    # eight now, which is why the wide framings still shorten the person block
    # on top of this - see detail_fuer_kamera().
    "shoulders": [
        ("Schmal", "narrow shoulders"), ("Zierlich", "delicate sloping shoulders"),
        ("Gerade", "straight squared shoulders"), ("Breit", "broad shoulders"),
        ("Sportlich", "athletic defined shoulders"),
    ],
    "waist": [
        ("Sehr schmal", "a very narrow waist"), ("Schmal", "a slim waist"),
        ("Definiert", "a defined waist"), ("Gerade", "a straight waist"),
        ("Weich", "a soft waist"),
    ],
    "belly": [
        ("Flach", "a flat stomach"), ("Definiert", "a toned defined stomach"),
        ("Sixpack", "visible abdominal muscles"),
        ("Weich", "a soft rounded stomach"),
    ],
    "legs": [
        ("Lang", "long legs"), ("Schlank", "slender legs"),
        ("Muskulös", "muscular legs"), ("Kräftig", "strong shapely legs"),
        ("Kurz", "short legs"),
    ],
    "hips": [
        ("Schmal", "narrow hips"), ("Rund", "rounded hips"),
        ("Breit", "wide hips"), ("Betont", "pronounced curvy hips"),
    ],
    "hair": [  # {c} = Haarfarbe
        ("Lang glatt", "long straight {c} hair"), ("Lange Wellen", "long wavy {c} hair"),
        ("Bob", "chin-length {c} bob"), ("Pixie", "short {c} pixie cut"),
        ("Pferdeschwanz", "high {c} ponytail"), ("Messy Bun", "{c} hair in a messy bun"),
        ("Flechtzopf", "long {c} side braid"), ("Locken", "voluminous curly {c} hair"),
        ("Pony", "shoulder-length {c} hair with straight bangs"),
        ("Half-up", "{c} hair in a half-up style"),
        ("Sleek zurück", "sleek {c} hair slicked back into a low bun"),
        ("Kurz wellig", "short tousled {c} hair"),
    ],
    "hairColor": [  # substituted into the hair template, otherwise "<value> hair"
        ("Blond", "blonde"), ("Platinblond", "platinum blonde"), ("Dunkelblond", "dark blonde"),
        ("Braun", "brown"), ("Dunkelbraun", "dark brown"), ("Schwarz", "black"),
        ("Rot / Kupfer", "copper red"), ("Kastanie", "auburn"), ("Grau / Silber", "silver gray"),
    ],
    # ── Face ─────────────────────────────────────────────────────────────────
    # Up to here the builder described hair, eye colour and skin tone, but no
    # face. The model invented new features in every image, which happened to be
    # blonde and have green eyes. Going finer than these six fields does not pay
    # off: for "eye spacing" the model has no steerable direction, the prompt
    # would only get longer and the entries behind it weaker.
    "faceShape": [  # -> "<wert> face"
        ("Oval", "an oval"), ("Herzförmig", "a heart-shaped"),
        ("Rund", "a round"), ("Eckig", "a square"),
        ("Länglich", "a long"), ("Diamant", "a diamond-shaped"),
    ],
    "cheekbones": [
        ("Hoch betont", "high, pronounced cheekbones"),
        ("Markant", "sharp, sculpted cheekbones"),
        ("Weich", "soft cheekbones"),
        ("Flach", "flat cheekbones"),
    ],
    "nose": [
        ("Klein", "a small nose"), ("Gerade", "a straight nose"),
        ("Schmal", "a narrow nose"), ("Stupsnase", "a button nose"),
        ("Markant", "a prominent nose"), ("Leicht gebogen", "a slightly aquiline nose"),
    ],
    "eyeShape": [  # placed before the eye colour: "almond-shaped green eyes"
        ("Mandelförmig", "almond-shaped"), ("Rund", "round"),
        ("Schmal", "narrow"), ("Schlupflider", "hooded"),
        ("Weit auseinander", "wide-set"), ("Katzenaugen", "upturned"),
    ],
    "lipShape": [
        ("Voll", "full lips"), ("Schmal", "thin lips"),
        ("Breit", "wide lips"), ("Amorbogen", "a defined cupid's bow"),
        ("Volle Unterlippe", "a fuller lower lip"),
    ],
    "chin": [
        ("Spitz", "a pointed chin"), ("Schmal", "a narrow chin"),
        ("Rund", "a rounded chin"), ("Breit", "a broad chin"),
        ("Grübchen", "a dimpled chin"), ("Fliehend", "a receding chin"),
    ],
    "jawline": [
        ("Weich", "a soft jawline"), ("Definiert", "a defined jawline"),
        ("Markant", "a sharp angular jawline"), ("Schmal", "a narrow jawline"),
    ],
    "browShape": [  # shape, not position - position lives in the expression
        ("Schmal", "thin eyebrows"), ("Dicht", "thick eyebrows"),
        ("Gerade", "straight eyebrows"), ("Geschwungen", "arched eyebrows"),
        ("Buschig", "bushy eyebrows"),
    ],
    "eyes": [  # -> "<wert> eyes"
        # natural
        ("Blau", "blue"), ("Graublau", "grayish blue"), ("Eisblau", "pale icy blue"),
        ("Grün", "green"), ("Graugrün", "grayish green"),
        ("Braun", "brown"), ("Dunkelbraun", "dark brown"),
        ("Haselnuss", "hazel"), ("Grau", "gray"), ("Bernstein", "amber"),
        # exaggerated - "vivid" and "luminous" carry more weight with Krea 2
        # than "bright", which tends to just lift the whole image's brightness.
        ("Blau (strahlend)", "vivid luminous electric blue"),
        ("Grün (strahlend)", "vivid luminous emerald green"),
        ("Türkis (strahlend)", "vivid luminous turquoise"),
        ("Violett (strahlend)", "striking luminous violet"),
        ("Bernstein (leuchtend)", "glowing golden amber"),
        ("Silbergrau (strahlend)", "pale luminous silver-gray"),
        ("Rot (unnatürlich)", "unnatural glowing crimson"),
        # special case
        ("Heterochromie", "heterochromia, one blue and one green eye"),
    ],
    "hairEffect": [  # streaks and gradients - after cut and base colour
        ("Balayage", "with soft balayage highlights"),
        ("Ombré", "with an ombré fade to lighter ends"),
        ("Highlights", "with fine bright highlights"),
        ("Lowlights", "with darker lowlights"),
        ("Dip-Dye", "with brightly dip-dyed ends"),
        ("Zweifarbig", "in two contrasting colours"),
        ("Graue Strähne", "with a single silver streak"),
        ("Ansatz sichtbar", "with visibly darker roots"),
    ],
    "lashes": [
        ("Natürlich", "natural eyelashes"), ("Lang", "long eyelashes"),
        ("Voluminös", "voluminous mascara lashes"), ("Falsche Wimpern", "dramatic false eyelashes"),
        ("Wispy", "wispy fluttery lashes"),
    ],
    "lipColor": [  # -> "<finish> <wert> lipstick"
        # restrained
        ("Natürlich", "natural-tone"), ("Nude", "nude"), ("Beige", "beige"),
        ("Altrosa", "dusty rose"), ("Pfirsich", "peach"),
        # red
        ("Rot", "red"), ("Kirschrot", "cherry red"), ("Dunkelrot", "dark red"),
        ("Weinrot", "wine red"), ("Burgunder", "burgundy"),
        ("Ziegelrot", "brick red"), ("Koralle", "coral"), ("Orange", "orange"),
        # pinks
        ("Rosa", "soft pink"), ("Pink", "hot pink"), ("Fuchsia", "fuchsia"),
        ("Magenta", "magenta"), ("Neonpink", "vivid neon pink"),
        # berry and violet
        ("Beere", "berry"), ("Pflaume", "plum"), ("Mauve", "mauve"),
        ("Violett", "violet"), ("Lila", "deep purple"),
        ("Aubergine", "aubergine"),
        # dark and unusual
        ("Braun", "chocolate brown"), ("Toffee", "toffee"),
        ("Schwarz", "black"), ("Blau", "deep blue"),
        ("Gold (metallic)", "metallic gold"), ("Kupfer (metallic)", "metallic copper"),
        ("Silber (metallic)", "metallic silver"),
    ],
    "lipFinish": [
        ("Matt", "matte"), ("Gloss", "glossy"), ("Satin", "satin"),
    ],
    "eyeliner": [
        ("Ohne", "bare undefined lash lines"),
        ("Dezent", "a thin subtle eyeliner"),
        ("Kajal", "soft smudged kohl liner"),
        ("Kajal unten", "kohl liner along the lower lash line"),
        ("Cat-Eye", "a sharp winged cat-eye liner"),
        ("Breit gezogen", "a bold thick eyeliner"),
        ("Grafisch", "a graphic geometric eyeliner"),
        ("Weiß akzentuiert", "eyeliner with a white inner-corner accent"),
    ],
    "eyeshadow": [
        ("Nude", "nude eyeshadow"), ("Braun", "warm brown eyeshadow"),
        ("Bronze", "bronze eyeshadow"), ("Gold", "gold shimmer eyeshadow"),
        ("Kupfer", "copper eyeshadow"), ("Rosé", "rosy eyeshadow"),
        ("Beere", "berry eyeshadow"), ("Violett", "violet eyeshadow"),
        ("Blau", "blue eyeshadow"), ("Grün", "green eyeshadow"),
        ("Silber", "silver shimmer eyeshadow"),
        ("Schwarz verblendet", "blended black eyeshadow"),
        ("Glitzer", "glittery eyeshadow"),
    ],
    "blush": [
        ("Ohne", "bare cheeks"), ("Dezent", "a soft natural blush"),
        ("Rosig", "rosy blushed cheeks"), ("Pfirsich", "peach blush"),
        ("Kräftig", "strong sculpted blush"),
        ("Sonnenkuss", "a sun-kissed flush across the cheeks and nose"),
    ],
    "makeup": [
        ("Ohne", "no makeup, bare face"), ("Natürlich", "natural makeup"),
        ("Dezent", "subtle makeup"), ("Glam", "glamorous makeup"),
        ("Smokey Eyes", "smokey eye makeup"), ("Editorial", "bold editorial makeup"),
    ],
    "skinFeatures": [  # Mehrfachauswahl (im Node je ein Toggle)
        ("Sommersprossen", "freckles"), ("Blasse Haut", "pale skin"),
        ("Schönheitsfleck", "a beauty mark"), ("Grübchen", "dimples"),
        ("Muttermale", "moles"), ("Tattoos", "tattoos"),
        ("Piercings", "facial piercings"), ("Sommerbräune", "sun-kissed glowing skin"),
    ],
    "nailLength": [
        ("Kurz gepflegt", "short manicured nails"), ("Mittel", "medium-length nails"),
        ("Lang", "long nails"), ("Extra lang (Acryl)", "extra-long acrylic nails"),
        ("Stiletto", "stiletto-shaped nails"),
    ],
    "nailColor": [  # substituted into nailLength (replacing "nails"), otherwise "<value> nails"
        ("Rot", "red"), ("French", "french-tip"), ("Nude", "nude"),
        ("Schwarz", "black"), ("Pink", "pink"), ("Weiß", "white"),
    ],
    # Legwear. Used to be typed by hand into the free text of every prompt.
    # The make only - the colour lives in "hosieryColor" and is placed in front
    # of it. This list used to carry two colours of its own ("black tights",
    # "nude tights"), which clashed with a separate colour choice.
    "hosiery": [
        ("Nackte Beine", "bare legs"),
        ("Strumpfhose hauchdünn", "sheer 15 denier pantyhose"),
        ("Strumpfhose glänzend", "shiny glossy pantyhose"),
        ("Strumpfhose matt", "matte pantyhose"),
        ("Strumpfhose blickdicht", "opaque pantyhose"),
        ("Strumpfhose gemustert", "patterned pantyhose"),
        ("Netzstrumpfhose", "fishnet pantyhose"),
        ("Netzstrumpfhose grob", "wide-mesh fishnet pantyhose"),
        ("Halterlose Strümpfe", "hold-up stockings with lace tops"),
        ("Strümpfe mit Naht", "seamed stockings"),
        ("Strümpfe mit Strapsen", "stockings held by a suspender belt"),
        ("Overknee-Strümpfe", "over-the-knee socks"),
        ("Kniestrümpfe", "knee-high socks"),
        ("Söckchen", "short ankle socks"),
        ("Leggings", "leggings"),
    ],
    "hosieryColor": [  # placed before the legwear
        ("Hautfarben", "nude"), ("Beige", "beige"), ("Braun", "tan"),
        ("Karamell", "caramel"), ("Creme", "cream"), ("Weiß", "white"),
        ("Grau", "grey"), ("Anthrazit", "charcoal"), ("Schwarz", "black"),
        ("Rot", "red"), ("Bordeaux", "burgundy"), ("Pink", "hot pink"),
        ("Rosé", "dusty rose"), ("Violett", "purple"), ("Blau", "navy blue"),
        ("Türkis", "turquoise"), ("Grün", "emerald green"),
        ("Kupfer", "copper"), ("Gold schimmernd", "shimmering gold"),
        ("Silber schimmernd", "shimmering silver"),
    ],
    "jewellery": [
        ("Kleine Ohrstecker", "small stud earrings"),
        ("Ohrringe lang", "long dangling earrings"),
        ("Creolen", "hoop earrings"),
        ("Zarte Halskette", "a delicate necklace"),
        ("Choker", "a choker"),
        ("Statement-Kette", "a bold statement necklace"),
        ("Ringe", "several rings"),
        ("Armreif", "a bangle"),
        ("Armband", "a thin bracelet"),
        ("Fußkettchen", "an ankle chain"),
        ("Bauchnabelpiercing", "a navel piercing"),
    ],
    "eyewear": [
        ("Brille schmal", "narrow rectangular glasses"),
        ("Brille rund", "round glasses"),
        ("Hornbrille", "thick-rimmed glasses"),
        ("Lesebrille", "reading glasses low on the nose"),
        ("Sonnenbrille", "sunglasses"),
        ("Pilotenbrille", "aviator sunglasses"),
        ("Cat-Eye-Brille", "cat-eye glasses"),
    ],
    "headwear": [
        ("Stirnband", "a headband"),
        ("Haarreif", "a hair band"),
        ("Mütze", "a beanie"),
        ("Baseballkappe", "a baseball cap"),
        ("Sonnenhut", "a wide-brimmed sun hat"),
        ("Fedora", "a fedora"),
        ("Kopftuch", "a headscarf"),
    ],
    # Grouped by construction. compose() puts "wearing " in front - the
    # exception is "barefoot", which is handled separately there and therefore
    # has to stay spelled exactly like this.
    "shoes": [
        # pumps
        ("Pumps spitz", "classic pointed-toe pumps"),
        ("Pumps mandelförmig", "almond-toe pumps"),
        ("Peeptoe-Pumps", "peep-toe pumps"),
        ("Slingback-Pumps", "slingback pumps"),
        ("Mary-Jane-Pumps", "Mary Jane pumps with ankle straps"),
        ("Lack-Pumps", "shiny patent leather pumps"),
        ("Wildleder-Pumps", "suede pumps"),
        # heel shapes
        ("Stiletto High Heels", "stiletto high heels"),
        ("Sehr hohe Stilettos", "extremely high stiletto heels"),
        ("Kitten Heels", "kitten heels"),
        ("Blockabsatz-Pumps", "block heel pumps"),
        ("Keilabsatz", "wedge heels"),
        ("Plateau-Heels", "platform high heels"),
        ("Plateau-Stilettos", "platform stiletto heels"),
        ("Extreme Plateau-Heels", "towering platform stiletto heels"),
        ("Lack-Plateau-Heels", "shiny patent leather platform heels"),
        # sandals
        ("Riemchen-Sandaletten", "strappy heeled sandals"),
        ("Sandaletten mit Knöchelriemen", "strappy high-heeled sandals with ankle straps"),
        ("Zehensteg-Sandaletten", "thong-strap heeled sandals"),
        ("Plateau-Sandaletten", "platform heeled sandals"),
        ("Mules mit Absatz", "heeled mules"),
        ("Pantoletten", "heeled slides"),
        # boots
        ("Stiefeletten mit Absatz", "heeled ankle boots"),
        ("Spitze Stiletto-Stiefeletten", "pointed ankle boots with stiletto heels"),
        ("Sock-Boots", "sock boots with stiletto heels"),
        ("Kniehohe Stiefel", "knee-high heeled boots"),
        ("Overknee-Stiefel", "overknee boots"),
        ("Overknee-Lackstiefel", "thigh-high patent leather boots"),
        ("Reitstiefel", "riding boots"),
        ("Cowboystiefel", "cowboy boots"),
        ("Combat Boots", "combat boots"),
        # flat
        ("Ballerinas", "ballet flats"),
        ("Loafer", "loafers"),
        # Used to be "white sneakers". The only colour in this list, and it
        # clashed with the separate colour choice - "red white sneakers". The
        # same cleanup as was done for the tights earlier.
        ("Sneaker", "sneakers"),
        ("Flip-Flops", "flip-flops"),
        # none
        ("Nur Strümpfe", "only sheer stockings, no shoes"),
        ("Nur Socken", "only socks, no shoes"),
        ("Barfuß", "barefoot"),
    ],
    # Placed in front of the shoes. A field of its own, because image models
    # attach colours to the nearest garment when nothing else is in the way:
    # with "black opaque pantyhose" and no shoe colour, the shoes regularly came
    # out black as well. An explicit second colour gives the model a competing
    # binding.
    "shoesColor": [
        ("Schwarz", "black"), ("Weiß", "white"), ("Hautfarben", "nude"),
        ("Beige", "beige"), ("Braun", "brown"), ("Cognac", "cognac brown"),
        ("Grau", "grey"), ("Rot", "red"), ("Bordeaux", "burgundy"),
        ("Pink", "hot pink"), ("Rosé", "dusty rose"), ("Violett", "purple"),
        ("Blau", "navy blue"), ("Türkis", "turquoise"),
        ("Grün", "emerald green"), ("Gold", "gold"), ("Silber", "silver"),
        ("Kupfer", "copper"), ("Leopardenmuster", "leopard print"),
        ("Zebramuster", "zebra print"), ("Durchsichtig", "clear transparent"),
    ],
}

# Shoes that are not shoes - no colour may go in front of these. Otherwise it
# would read "wearing red barefoot".
SCHUHE_OHNE = {"barefoot", "only sheer stockings, no shoes",
               "only socks, no shoes"}

# Possessive pronoun per type (for the age templates, {p})
TYPE_POSS = {"a woman": "her", "a young woman": "her",
             "a man": "his", "a young man": "his", "a person": "their"}

# The presets start at the early 20s, so labels alone cannot describe a minor.
# The exact-age field is free text and could, so it gets a floor. This stops
# accidents and backs the statement in the README; it is not a content filter,
# because the nodes only emit text and anything else can be typed elsewhere.
MINDESTALTER = 18

NONE = "—"   # the empty entry of a list
ALLE = "alle"  # Familienfilter aus

def _labels(cat):
    return [NONE] + [lbl for lbl, _ in PRESETS[cat]]

def _val(cat, label):
    if not label or label == NONE:
        return None
    for lbl, value in PRESETS[cat]:
        if lbl == label:
            return value
    return None

def _clean(s):
    return (s or "").strip().rstrip(",;. \t\r\n")


# ─────────────────────────────────────────────────────────────────────────────
# Detail levels: they govern how much of the person block reaches the prompt.
#
# Image models hand out frame area roughly by token weight. On wide and
# full-body shots the person block has to shrink, or the figure eats the frame -
# no matter how sharply "wide shot" is worded. The Person Builder still stores
# and shows the full description; the throttling takes effect when assembling
# for wide framings (photoshoot).
# ─────────────────────────────────────────────────────────────────────────────
DETAIL_IDENTITAET = "identitaet"
DETAIL_FIGUR = "figur"
DETAIL_VOLL = "voll"

# Silhouette plus coarse identity. Enough for the same person to stay
# recognisable, without the micro make-up and fine facial work that the model
# renders large.
_FELDER_IDENTITAET = frozenset({
    "type", "age", "ageExact", "ethnicity", "skinTone", "complexion",
    "height", "figure",
    "hair", "hairColor", "hairEffect",
    "eyes",  # colour from a distance, without shape, lashes or liner
    "hosiery", "hosieryColor", "shoes", "shoesColor",
    "headwear",
    "skinFeatures",
    "free",
})

# Plus body and coarse facial contour. For cowboy and full-body shots: figure
# and clothing count, eyeshadow and blush do not.
_FELDER_FIGUR = _FELDER_IDENTITAET | frozenset({
    "shoulders", "bust", "waist", "belly", "hips", "legs",
    "faceShape", "eyeShape", "lipShape",
    "makeup",
    "jewellery", "eyewear",
    "nailLength", "nailColor",
})

# Framing -> detail level. Tight = everything, wide = identity only.
KAMERA_DETAIL = {
    "Detail": DETAIL_VOLL,
    "Nahaufnahme": DETAIL_VOLL,
    "Porträt": DETAIL_VOLL,
    "Halbtotale": DETAIL_FIGUR,
    "Amerikanisch": DETAIL_FIGUR,
    "Ganzkörper": DETAIL_FIGUR,
    "Totale": DETAIL_IDENTITAET,
}


def detail_fuer_kamera(kamera_label):
    """Which person detail level fits this framing."""
    return KAMERA_DETAIL.get(kamera_label, DETAIL_VOLL)


def _erlaubt(detail, key):
    if detail == DETAIL_VOLL or not detail:
        return True
    if detail == DETAIL_FIGUR:
        return key in _FELDER_FIGUR
    return key in _FELDER_IDENTITAET


def compose_person(p, detail=DETAIL_VOLL):
    """Person text out of the value dict. p = dict of English values.

    detail governs the token load: at DETAIL_IDENTITAET (wide shot) and
    DETAIL_FIGUR (full body and similar), the facial and make-up micro-details
    drop out, which the model would otherwise reward with frame area.
    DETAIL_VOLL is the full kit unchanged - so the Person Builder still stores
    and shows everything; the throttling only takes effect during the shoot, or
    deliberately via the argument.
    """
    def ok(key):
        return _erlaubt(detail, key)

    feats = (p.get("skinFeatures") or []) if ok("skinFeatures") else []
    typ = p.get("type") if ok("type") else None
    poss = TYPE_POSS.get(typ, "their")
    parts = []

    if typ:
        parts.append(typ)
    exact = "".join(ch for ch in _clean(p.get("ageExact")) if ch.isdigit()) if ok("ageExact") else ""
    if exact and int(exact) < MINDESTALTER:
        exact = str(MINDESTALTER)
    if exact:
        parts.append(exact + " years old")
    elif ok("age") and p.get("age"):
        parts.append(p["age"].replace("{p}", poss))

    if ok("ethnicity") and p.get("ethnicity"):  parts.append(p["ethnicity"])
    if ok("skinTone") and p.get("skinTone"):   parts.append(p["skinTone"] + " skin")
    if ok("complexion") and p.get("complexion"): parts.append(p["complexion"])

    # Body from top to bottom. These entries are the counterweight to how
    # head-heavy the description is - the more of them are set, the smaller the
    # head comes out in the image.
    if ok("height") and p.get("height"):    parts.append(p["height"])
    if ok("figure") and p.get("figure"):    parts.append(p["figure"])
    if ok("shoulders") and p.get("shoulders"): parts.append(p["shoulders"])
    if ok("bust") and p.get("bust"):      parts.append(p["bust"])
    if ok("waist") and p.get("waist"):     parts.append(p["waist"])
    if ok("belly") and p.get("belly"):     parts.append(p["belly"])
    if ok("hips") and p.get("hips"):      parts.append(p["hips"])
    if ok("legs") and p.get("legs"):      parts.append(p["legs"])

    hair_ok = ok("hair")
    hair_color_ok = ok("hairColor")
    if hair_ok and p.get("hair"):
        color = (p.get("hairColor") or "") if hair_color_ok else ""
        parts.append(" ".join(p["hair"].replace("{c}", color).split()).strip())
    elif hair_color_ok and p.get("hairColor"):
        parts.append(p["hairColor"] + " hair")
    if ok("hairEffect") and p.get("hairEffect"):
        parts.append(p["hairEffect"])

    # Face from the shape inwards: contour, cheeks, nose, brows, eyes.
    if ok("faceShape") and p.get("faceShape"):  parts.append(p["faceShape"] + " face")
    if ok("cheekbones") and p.get("cheekbones"): parts.append(p["cheekbones"])
    if ok("nose") and p.get("nose"):       parts.append(p["nose"])
    if ok("chin") and p.get("chin"):       parts.append(p["chin"])
    if ok("jawline") and p.get("jawline"):    parts.append(p["jawline"])
    if ok("browShape") and p.get("browShape"):  parts.append(p["browShape"])

    # Eye shape and colour belong in one phrase: "almond-shaped green eyes"
    # rather than "almond-shaped eyes, green eyes". Append the word "eyes" only
    # when it is not already in the value - otherwise heterochromia would read
    # "one blue and one green eye eyes". At DETAIL_IDENTITAET only the colour
    # remains (eyeShape is not permitted there).
    eye_shape = p.get("eyeShape") if ok("eyeShape") else None
    eye_color = p.get("eyes") if ok("eyes") else None
    if eye_shape or eye_color:
        satz = " ".join(x for x in [eye_shape, eye_color] if x)
        parts.append(satz if "eye" in satz else satz + " eyes")
    if ok("lashes") and p.get("lashes"):    parts.append(p["lashes"])
    if ok("eyeliner") and p.get("eyeliner"):  parts.append(p["eyeliner"])
    if ok("eyeshadow") and p.get("eyeshadow"): parts.append(p["eyeshadow"])

    if ok("lipShape") and p.get("lipShape"): parts.append(p["lipShape"])

    if ok("lipColor") and p.get("lipColor"):
        finish = p.get("lipFinish") if ok("lipFinish") else None
        parts.append(" ".join(x for x in [finish, p["lipColor"], "lipstick"] if x))
    elif ok("lipFinish") and p.get("lipFinish"):
        parts.append(p["lipFinish"] + " lips")
    if ok("blush") and p.get("blush"):  parts.append(p["blush"])
    if ok("makeup") and p.get("makeup"): parts.append(p["makeup"])

    for f in feats:
        parts.append(f)

    nl = p.get("nailLength") if ok("nailLength") else None
    nc = p.get("nailColor") if ok("nailColor") else None
    if nl and nc:
        parts.append(nl.replace("nails", nc + " nails"))
    elif nl:
        parts.append(nl)
    elif nc:
        parts.append(nc + " nails")

    free = _clean(p.get("free")) if ok("free") else ""
    if free:
        parts.append(free)

    # Legwear before the shoes - that way it reads like a description of
    # getting dressed from the bottom up. The colour goes in front: "black sheer
    # 15 denier pantyhose". With bare legs both drop out, otherwise it would
    # read "wearing black bare legs".
    hos = p.get("hosiery") if ok("hosiery") else None
    hosf = p.get("hosieryColor") if ok("hosieryColor") else None
    if hos == "bare legs":
        parts.append("bare legs")
    elif hos:
        parts.append("wearing " + " ".join(x for x in [hosf, hos] if x))

    # Shoe colour goes in front, as with the legwear. For "barefoot" and the
    # two "no shoes" entries it drops out - there is nothing to colour there.
    shoes = p.get("shoes") if ok("shoes") else None
    shoesf = p.get("shoesColor") if ok("shoesColor") else None
    if shoes == "barefoot":
        parts.append("barefoot")
    elif shoes in SCHUHE_OHNE:
        parts.append(shoes)
    elif shoes:
        parts.append("wearing " + " ".join(x for x in [shoesf, shoes] if x))

    if ok("jewellery") and p.get("jewellery"):  parts.append("wearing " + p["jewellery"])
    if ok("eyewear") and p.get("eyewear"):    parts.append("wearing " + p["eyewear"])
    if ok("headwear") and p.get("headwear"):   parts.append("wearing " + p["headwear"])

    return ", ".join(x for x in parts if x)


# ─────────────────────────────────────────────────────────────────────────────
# ComfyUI node
# ─────────────────────────────────────────────────────────────────────────────
_SINGLE = ["type", "age", "ethnicity", "skinTone", "complexion",
           "height", "figure", "bust", "shoulders", "waist", "belly",
           "hips", "legs",
           "hair", "hairColor", "hairEffect",
           "faceShape", "cheekbones", "nose", "chin", "jawline", "eyeShape",
           "browShape", "lipShape",
           "eyes", "lashes", "eyeliner", "eyeshadow", "blush",
           "lipColor", "lipFinish", "makeup",
           "nailLength", "nailColor", "hosiery", "hosieryColor",
           "shoes", "shoesColor",
           "jewellery", "eyewear", "headwear"]

# Families of the shoe list - at 38 entries the only field that is unusable as
# a plain dropdown. The rest sit between 3 and 12.
SCHUH_GRUPPEN = {
    "Pumps": ["Pumps spitz", "Pumps mandelförmig", "Peeptoe-Pumps",
              "Slingback-Pumps", "Mary-Jane-Pumps", "Lack-Pumps",
              "Wildleder-Pumps"],
    "Absätze": ["Stiletto High Heels", "Sehr hohe Stilettos", "Kitten Heels",
                "Blockabsatz-Pumps", "Keilabsatz", "Plateau-Heels",
                "Plateau-Stilettos", "Extreme Plateau-Heels",
                "Lack-Plateau-Heels"],
    "Sandaletten": ["Riemchen-Sandaletten", "Sandaletten mit Knöchelriemen",
                    "Zehensteg-Sandaletten", "Plateau-Sandaletten",
                    "Mules mit Absatz", "Pantoletten"],
    "Stiefel": ["Stiefeletten mit Absatz", "Spitze Stiletto-Stiefeletten",
                "Sock-Boots", "Kniehohe Stiefel", "Overknee-Stiefel",
                "Overknee-Lackstiefel", "Reitstiefel", "Cowboystiefel",
                "Combat Boots"],
    "flach": ["Ballerinas", "Loafer", "Sneaker", "Flip-Flops"],
    "ohne": ["Nur Strümpfe", "Nur Socken", "Barfuß"],
}

# Tabs of the interface. Without this split, 44 fields would stack up and the
# node would be over 1000 pixels tall; this way only one group is ever visible.
#
# A nested list is ONE row: the fields in it belong together and share a single
# label. Each of them used to stand on its own, which put "Extras" at 10 rows
# and around 346 pixels - with roughly 300 pixels of visible area, the only tab
# that did not fit.
#
# Two moves are folded in here. Nail polish is make-up and sat under Extras only
# for want of space. And "eyeShape" was on "Face" while "eyes" was on "Head" -
# even though compose_person() fuses the two into a single phrase
# ("almond-shaped green eyes"). You could not see one while setting the other.
SEKTIONEN = [
    ("Grund",    ["type", "age", "ageExact", "ethnicity", "skinTone",
                  "complexion"]),
    ("Körper",   ["height", "figure", "shoulders", "bust", "waist", "belly",
                  "hips", "legs"]),
    ("Kopf",     [["hair", "hairColor"], "hairEffect", ["eyeShape", "eyes"],
                  "lashes"]),
    ("Gesicht",  ["faceShape", "cheekbones", "nose", "chin", "jawline",
                  "browShape", "lipShape"]),
    ("Make-up",  ["eyeliner", "eyeshadow", "blush", ["lipColor", "lipFinish"],
                  "makeup", "skinFeatures", ["nailLength", "nailColor"]]),
    ("Kleidung", [["hosiery", "hosieryColor"], ["shoes", "shoesColor"],
                  "jewellery", "eyewear", "headwear", "details"]),
]

# Label for a row group. With no entry, the name of the first field applies -
# "Frisur", "Lippen", "Nägel", "Strümpfe", "Schuhe" are right as they stand.
ZEILENNAMEN = {"eyeShape": "Augen"}

# Kind of control per field; anything not named here is a plain dropdown.
FELDART = {
    "ageExact": "text",
    "details": "text",
    "skinFeatures": "mehrfach",  # chips to switch on and off, any number of them
    # Two dropdowns: the family first, after which at most 9 models remain.
    # Before that a chip block over all 38 - which took up 130 pixels on its own
    # and was the main reason the tab did not fit. The 38-entry dropdown that
    # preceded it was unusable in its own way; putting the family in front
    # solves both.
    "shoes": "familie",
}

# Fields that aim at the head. The interface counts them and warns when too
# many are set.
#
# Measured on a pair with identical seed, identical framing ("full body shot ...
# proportionally small head") and identical prompt: with 4 face fields (18% face
# share of the person text) a clean full-body shot came out; with 12 fields
# (48%) the composition collapsed - head over half the image height, legs
# anatomically wrong beneath the shoulders. It is not a gradual degradation but
# a tipping point.
#
# The warning alone is not enough: the photoshoot shortens the same person block
# via detail_fuer_kamera() to identity/figure/full - see compose_person().
GESICHTSFELDER = [
    "faceShape", "cheekbones", "nose", "chin", "jawline", "eyeShape",
    "browShape", "lipShape", "lashes", "eyeliner", "eyeshadow", "blush",
]
GESICHT_HINWEIS_AB = 6   # ab hier ein neutraler Hinweis
GESICHT_WARNUNG_AB = 9   # ab hier deutlich

# Labels in the interface - the keys come from the original editor and are in
# English.
FELDNAMEN = {
    "type": "Typ", "age": "Alter", "ageExact": "genaues Alter",
    "ethnicity": "Herkunft", "skinTone": "Hautton",
    "height": "Größe", "figure": "Figur", "bust": "Büste",
    "hair": "Frisur", "hairColor": "Haarfarbe", "eyes": "Augen",
    "lashes": "Wimpern", "complexion": "Teint",
    "shoulders": "Schultern", "waist": "Taille", "belly": "Bauch",
    "hips": "Hüfte", "legs": "Beine", "hairEffect": "Strähnen",
    "chin": "Kinn", "jawline": "Kieferlinie",
    "eyeliner": "Eyeliner", "eyeshadow": "Lidschatten", "blush": "Rouge",
    "hosiery": "Strümpfe", "hosieryColor": "Strumpffarbe", "jewellery": "Schmuck", "eyewear": "Brille",
    "headwear": "Kopfbedeckung",
    "faceShape": "Gesichtsform", "cheekbones": "Wangenknochen", "nose": "Nase",
    "eyeShape": "Augenform", "browShape": "Brauenform", "lipShape": "Lippenform",
    "lipColor": "Lippen", "lipFinish": "Finish", "makeup": "Make-up",
    "skinFeatures": "Hautmerkmale",
    "nailLength": "Nägel", "nailColor": "Nagelfarbe",
    "shoes": "Schuhe", "shoesColor": "Schuhfarbe",
    "details": "Details",
}

# Free text fields need a placeholder instead of a preset list.
PLATZHALTER = {
    "ageExact": "genaues Alter, z. B. 34 (schlägt den Bereich, ab 18)",
    "details": "Weitere Details (englisch), z. B. wearing a red raincoat",
}

DEFAULT_STATE = {
    "felder": {cat: NONE for cat in _SINGLE},
    "mehrfach": {"skinFeatures": []},
    "texte": {"ageExact": "", "details": ""},
    "sektion": SEKTIONEN[0][0],
    "gruppe": {"shoes": ALLE},
}


class Krea2PersonBuilder:
    @classmethod
    def INPUT_TYPES(cls):
        # PersonState is `hidden`, not `required`: hidden inputs produce
        # neither a widget nor an input dot in the Vue front end. The JS side
        # keeps the state in node.properties and pushes it in here on
        # execution, through a graphToPrompt hook.
        return {
            "required": {},
            "hidden": {
                "PersonState": ("STRING", {"default": json.dumps(DEFAULT_STATE)}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("person", "person_data")
    FUNCTION = "build"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Baut die Person als englischen Text. person ist immer die "
                   "volle Beschreibung; person_data ist der Wertdict als JSON "
                   "fuer Photoshooting, das je Kameraeinstellung kuerzt.")

    def build(self, PersonState=None):
        try:
            state = json.loads(PersonState) if PersonState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Person] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)

        felder = state.get("felder") or {}
        texte = state.get("texte") or {}

        p = {cat: _val(cat, felder.get(cat)) for cat in _SINGLE}
        p["ageExact"] = texte.get("ageExact", "")
        p["free"] = texte.get("details", "")

        # Skin features are now any number of chips instead of three
        # dropdowns. Duplicates are dropped, so that "tattoos, tattoos" does not
        # end up in the prompt.
        feats, gesehen = [], set()
        for label in (state.get("mehrfach") or {}).get("skinFeatures") or []:
            wert = _val("skinFeatures", label)
            if wert and wert not in gesehen:
                gesehen.add(wert)
                feats.append(wert)
        p["skinFeatures"] = feats

        # person_data: raw values for the framing-dependent compose_person() in
        # the photoshoot. Without this output you would have to take the
        # finished text apart again - which cannot be done reliably.
        return (compose_person(p), json.dumps(p, ensure_ascii=False))


NODE_CLASS_MAPPINGS = {"Krea2PersonBuilder": Krea2PersonBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2PersonBuilder": "Photoshoot Person"}


# Quick self-test:  python -m nodes.person_builder  (from the package folder)
if __name__ == "__main__":
    demo = {
        "type": "a woman", "ageExact": "34", "ethnicity": "Eastern European features",
        "skinTone": "fair", "figure": "hourglass figure", "bust": "full bust",
        "height": "very tall, model height", "hair": "high {c} ponytail",
        "hairColor": "platinum blonde", "eyes": "green", "eyeShape": "almond-shaped",
        "lashes": "dramatic false eyelashes", "cheekbones": "high, pronounced cheekbones",
        "nose": "a small nose", "lipColor": "red", "lipFinish": "glossy",
        "eyeliner": "a sharp winged cat-eye liner", "eyeshadow": "bronze eyeshadow",
        "makeup": "glamorous makeup",
        "skinFeatures": ["freckles", "tattoos"], "nailLength": "long nails",
        "nailColor": "red", "free": "wearing a red sports bra", "shoes": "sneakers",
        "shoesColor": "white",
    }
    voll = compose_person(demo, DETAIL_VOLL)
    figur = compose_person(demo, DETAIL_FIGUR)
    ident = compose_person(demo, DETAIL_IDENTITAET)
    print("VOLL (%d): %s" % (len(voll), voll))
    print("FIGUR (%d): %s" % (len(figur), figur))
    print("IDENT (%d): %s" % (len(ident), ident))
    assert "cat-eye" in voll and "cat-eye" not in figur and "cat-eye" not in ident
    assert "hourglass" in ident and "full bust" not in ident
    assert detail_fuer_kamera("Totale") == DETAIL_IDENTITAET
    assert detail_fuer_kamera("Porträt") == DETAIL_VOLL
    print("ok")
