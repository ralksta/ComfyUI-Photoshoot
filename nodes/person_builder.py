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
import re

from . import eigene

# ─────────────────────────────────────────────────────────────────────────────
# PRESETS:  category -> list of (German label, English value)
# Colour categories (skinTone/eyes/hairColor/lipColor/nailColor) supply only the
# colour word; compose() adds the suffix (" skin", " eyes", " hair", " nails").
# hair holds a template with {c} = hair colour.
# ─────────────────────────────────────────────────────────────────────────────
PRESETS = {
    "gender": [
        ("Frau", "woman"),
        ("Mann", "man"),
        ("Transfrau", "trans woman"),
        ("Person", "person"),
    ],
    "age": [  # {p} = her/his/their
        ("Anfang 20", "in {p} early 20s"),
        ("Mitte 20", "in {p} mid 20s"),
        ("Ende 20", "in {p} late 20s"),
        ("Anfang 30", "in {p} early 30s"),
        ("Mitte 30", "in {p} mid 30s"),
        ("Ende 30", "in {p} late 30s"),
        ("40er", "in {p} 40s"),
        ("50er", "in {p} 50s"),
        ("60+", "in {p} 60s"),
        ("Senior (70+)", "in {p} 70s"),
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
        ("Gebräunt", "tan"), ("Oliv", "olive"), ("Bronze", "bronze"), ("Braun", "brown"),
        ("Dunkelbraun", "deep brown"), ("Ebenholz", "deep ebony"),
    ],
    # Complexion, independent of the colour. Deliberately without the word
    # "skin" - that already stands in the line before, otherwise it would read
    # "very fair skin, dewy luminous skin".
    "complexion": [
        ("Dewy", "with a dewy luminous finish"),
        ("Matt", "with a matte finish"),
        ("Porzellan", "with a smooth porcelain finish"),
        ("Glas-Haut", "with a glass skin luminous glow"),
        ("Geölt / Wet-Glow", "with a glistening oiled skin finish"),
        ("Natürliche Poren", "with natural texture and visible pores"),
        ("Sonnengegerbt", "weathered and sun-tanned"),
        ("Rötlich", "with a rosy flush"),
        ("Blass", "pale and translucent"),
    ],
    # "Klein" and "Zierlich" are the same height, not two steps of one scale.
    # In English "petite" means short *and* slightly built, so it fights every
    # fuller figure - "petite, short stature, plus-size, full-figured" asks for
    # two things at once. "short" carries no build with it.
    "height": [
        ("Klein", "short"), ("Zierlich", "petite, short stature"),
        ("Durchschnittlich", "average height"),
        ("Groß", "tall"), ("Model-Größe", "very tall, model height"),
    ],
    "figure": [
        ("Sehr schlank", "very slim, slender build"), ("Schlank", "slim build"),
        ("Schlank definiert", "lean, toned and sculpted physique"),
        ("Athletisch", "athletic, toned physique"), ("Durchschnittlich", "average build"),
        ("Kurvig", "curvy figure"), ("Sanduhr", "hourglass figure"),
        ("Birnenform", "pear-shaped figure, wider hips and slender waist"),
        ("Mollig", "chubby, soft curves"), ("Plus-Size", "plus-size, full-figured"),
        ("Stämmig", "stocky, solid build"), ("Muskulös", "muscular, fit"),
    ],
    "bust": [
        ("Klein", "small bust"), ("Mittel", "medium bust"),
        ("Voll", "full bust"), ("Groß", "large bust"),
        ("Sehr groß", "very large full bust"),
        ("Sehr groß (Kontrast)", "very large prominent bust contrasting with a slender waist"),
        ("Massiv / Stacked", "huge heavy bust, deeply endowed chest, prominent cleavage contrasting with a narrow ribcage"),
        ("Extrem", "extreme oversized bust, heavy deep cleavage"),
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
        ("Wespentaille", "a tiny cinched corset wasp waist"),
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
        ("Afro", "voluminous naturally textured {c} afro"),
        ("Braids / Zöpfe", "long {c} box braids"),
        ("Pony", "shoulder-length {c} hair with straight bangs"),
        ("Curtain Bangs", "shoulder-length {c} hair with soft curtain bangs"),
        ("Wolf Cut / Stufenschnitt", "layered {c} wolf cut with textured ends"),
        ("Half-up", "{c} hair in a half-up style"),
        ("Sleek zurück", "sleek {c} hair slicked back into a low bun"),
        ("Wet-Look", "sleek wet-look {c} hair styled back"),
        ("Space Buns", "{c} hair in high twin space buns"),
        ("Kurz wellig", "short tousled {c} hair"),
        ("Buzzcut / Abrasur", "ultra-short {c} buzzcut"),
        ("Undercut", "{c} hairstyle with an edgy shaved undercut"),
        # Bangs from a reference sheet, rendered as a head-and-shoulders
        # portrait against "{c} hair with bangs" (two seeds): all seven passed.
        ("Langes Haar mit Pony", "long straight {c} hair with heavy blunt bangs"),
        ("Seitenpony", "{c} hair with long side-swept bangs falling over one eye"),
        ("Wispy Bangs", "long {c} hair with light wispy bangs"),
        ("Baby Bangs", "{c} bob with very short micro bangs high on the forehead"),
        ("Locken mit Pony", "short curly {c} hair with curly bangs"),
        ("Bob mit Pony", "rounded {c} bob with full blunt bangs"),
        ("Fransiger Kurzhaarschnitt", "short choppy {c} hair with textured choppy bangs"),
    ],
    "hairColor": [  # substituted into the hair template, otherwise "<value> hair"
        ("Blond", "natural light blonde"), ("Platinblond", "clean pale platinum blonde"), ("Dunkelblond", "natural dark blonde"),
        ("Braun", "natural brown"), ("Dunkelbraun", "dark brown"), ("Schwarz", "natural black"),
        ("Rot / Kupfer", "natural copper red"), ("Kastanie", "auburn"), ("Erdbeerblond", "natural strawberry blonde"),
        ("Grau / Silber", "silver gray"), ("Eisweiß", "icy platinum white"),
        ("Pastellrosa", "pastel pink"), ("Mitternachtsblau", "deep midnight blue"),
        ("Smaragdgrün", "rich emerald green"),
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
        ("Schmal", "narrow"), ("Monolid", "monolid"),
        ("Schlupflider", "hooded"), ("Tief liegend", "deep-set"),
        ("Weit auseinander", "wide-set"), ("Katzenaugen", "upturned"),
    ],
    "lipShape": [
        ("Voll", "full lips"), ("Schmal", "thin lips"),
        ("Schmollmund", "pouty plump lips"),
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
        ("Soap Brows", "laminated feathered soap eyebrows"),
        ("Gerade", "straight eyebrows"), ("Geschwungen", "arched eyebrows"),
        ("Buschig", "bushy eyebrows"), ("Bleached", "bleached pale eyebrows"),
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
        ("Clean Girl", "minimalist clean-girl glowing makeup"),
        ("Dezent", "subtle makeup"), ("Glam", "glamorous makeup"),
        ("Smokey Eyes", "smokey eye makeup"),
        ("Gothic / Dark Grunge", "dark gothic makeup with smoked eyes and bold dark lips"),
        ("90s Vintage", "90s vintage matte makeup with contoured brown tones"),
        ("Editorial", "bold editorial makeup"),
    ],
    "skinFeatures": [  # Mehrfachauswahl (im Node je ein Toggle)
        ("Sommersprossen", "freckles"), ("Blasse Haut", "pale skin"),
        ("Schönheitsfleck", "a beauty mark"), ("Grübchen", "dimples"),
        ("Muttermale", "moles"), ("Tattoos", "tattoos"),
        ("Piercings", "facial piercings"), ("Sommerbräune", "sun-kissed glowing skin"),
        ("Vitiligo", "vitiligo pigmentation patterns"),
        ("Feine Narbe", "a delicate facial scar"),
        ("Nasenring / Septum", "a subtle septum nose ring"),
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
        ("Punkte-Strumpfhose", "sheer polka dot patterned tights"),
        ("Spitzen-Strumpfhose", "intricate floral lace tights"),
        ("Netzstrumpfhose", "fishnet pantyhose"),
        ("Netzstrumpfhose grob", "wide-mesh fishnet pantyhose"),
        ("Netzstrümpfe mit Naht", "fishnet stockings with back seam and garter straps"),
        ("Halterlose Strümpfe", "hold-up stockings with lace tops"),
        ("Strümpfe mit Naht", "seamed stockings"),
        ("Strümpfe mit Strapsen", "stockings held by a suspender belt"),
        ("Cage-Strapsgürtel", "wide multi-strap leather suspender garter belt"),
        ("Latex-Strümpfe", "skin-tight shiny latex thigh-high stockings"),
        ("Overknee-Strümpfe", "over-the-knee socks"),
        ("Kniestrümpfe", "knee-high socks"),
        ("Söckchen", "short ankle socks"),
        ("Leggings", "leggings"),
        ("Lack-Leggings", "high-gloss wet-look patent leggings"),
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
        ("Perlenkette", "a classic pearl necklace"),
        ("Choker", "a choker"),
        ("Leder-Choker mit O-Ring", "a black leather choker with a polished steel O-ring"),
        ("Leder-Choker mit Kette", "a black leather collar with a silver chain leash"),
        ("Leder-Armfesseln", "black leather wrist cuffs with buckle straps"),
        ("Brust-Harness (Leder)", "a strappy black leather chest harness with silver buckles"),
        ("Schenkel-Harness (Leder)", "a black leather thigh garter harness with O-rings"),
        ("Lange Lederhandschuhe", "elbow-length black leather opera gloves"),
        ("Lange Latex-Handschuhe", "skin-tight glossy black latex opera gloves"),
        ("Reitgerte in Hand", "holding a short black leather riding crop"),
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
        ("Barett", "a classic wool beret"),
        ("Sonnenhut", "a wide-brimmed sun hat"),
        ("Cowboyhut", "a wide-brim western cowboy hat"),
        ("Fedora", "a fedora"),
        ("Kopftuch", "a headscarf"),
        ("Lack-Schirmmütze (Domina)", "a peaked black patent leather biker officer cap"),
        ("Leder-Hasenmaske", "a black leather bunny mask with tall upright ears"),
        ("Leder-Katzenmaske", "a sculpted black leather cat mask"),
        ("Augenbinde", "a black silk blindfold covering the eyes"),
        # Hats from a reference chart, render-tested 2026-09-21 on the poster
        # person. Cloche, bowler, floppy hat and sailor hat needed a second
        # wording: the bare words gave a brimmed hat, a wide brim, a stiff felt
        # hat and a peaked officer cap.
        ("Glockenhut", "a close-fitting bell-shaped 1920s felt cloche hat with a narrow downturned brim"),
        ("Fischerhut", "a bucket hat"),
        ("Zylinder", "a tall black silk top hat"),
        ("Schiebermütze", "a tweed newsboy cap"),
        ("Pillbox mit Schleier", "a small pillbox hat with a short birdcage veil"),
        ("Fascinator", "a feathered fascinator pinned to the side of the head"),
        ("Panamahut", "a white straw Panama hat with a black band"),
        ("Melone", "a black bowler hat with a hard rounded crown and a short curled brim"),
        ("Kreissäge", "a flat-topped straw boater hat with a ribbon band"),
        ("Schlapphut", "a wide floppy sun hat with a soft drooping brim"),
        ("Wagenradhut", "an oversized cartwheel hat with a very wide flat brim"),
        ("Matrosenmütze", "a white canvas dixie cup sailor hat with the brim turned up all around"),
        ("Weiße Kapitänsmütze", "a white captain's hat with a black patent peak"),
        ("Elbsegler", "a navy captain's cap with a braided cord above the peak"),
        ("Uschanka", "a fur trapper hat with the ear flaps down"),
        ("Visor", "a sun visor"),
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
        ("Transparent-Pumps (Perspex)", "clear transparent perspex high heel pumps"),
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
        ("Clogs mit Holzsohle", "wooden sole platform clogs"),
        # sandals
        ("Riemchen-Sandaletten", "strappy heeled sandals"),
        ("Sandaletten mit Knöchelriemen", "strappy high-heeled sandals with ankle straps"),
        ("Schnür-Sandaletten (Wrap-Up)", "lace-up ankle wrap high heel sandals"),
        ("Zehensteg-Sandaletten", "thong-strap heeled sandals"),
        ("Plateau-Sandaletten", "platform heeled sandals"),
        ("Mules mit Absatz", "heeled mules"),
        ("Pantoletten", "heeled slides"),
        ("Espadrilles mit Keilabsatz", "canvas espadrille wedges with ankle ribbons"),
        # boots
        ("Stiefeletten mit Absatz", "heeled ankle boots"),
        ("Spitze Stiletto-Stiefeletten", "pointed ankle boots with stiletto heels"),
        ("Schnür-Stiefeletten", "victorian lace-up heeled ankle boots"),
        ("Sock-Boots", "sock boots with stiletto heels"),
        ("Kniehohe Stiefel", "knee-high heeled boots"),
        ("Overknee-Stiefel", "overknee boots"),
        ("Overknee-Lackstiefel", "thigh-high patent leather boots"),
        ("Cowboystiefel", "cowboy boots"),
        ("Combat Boots", "combat boots"),
        # dance & sports
        ("Reitstiefel", "tall polished leather equestrian riding boots"),
        ("Spitzenschuhe (Ballett)", "satin ballet pointe shoes with ribbon ties around ankles"),
        ("Ballettschläppchen", "soft leather split-sole ballet slippers"),
        ("Gymnastikschuhe", "leather rhythmic gymnastics slippers"),
        ("Latein-Tanzschuhe", "strappy Latin ballroom dance heels"),
        ("Jazzschuhe", "soft black leather jazz shoes"),
        ("Schlittschuhe (Eiskunstlauf)", "white leather figure ice skates with polished steel blades"),
        ("Rollschuhe (Quad Skates)", "retro quad roller skates with wheels and front toe stop"),
        ("Laufschuhe", "athletic running sneakers with cushioned foam soles"),
        ("Wanderschuhe", "rugged leather outdoor hiking boots with grip tread"),
        # fetish & extreme
        ("Ballet Heels (Extrem)", "extreme vertical ballet high heels with arched foot locked on tiptoes"),
        ("Absatzlose Heels (Heelless)", "avant-garde heelless curved platform high heels with no rear heel"),
        ("Schritthohe Lackstiefel", "crotch-high black patent leather boots reaching up to the hips with rear lace-up closure"),
        ("Huf-Heels (Hoof Boots)", "cloven hoof platform high heel boots"),
        ("Korsett-Schnürstiefel", "thigh-high corset-laced leather boots with metallic eyelets from toe to top"),
        ("Latex-Overknees", "skin-tight shiny black latex thigh-high boots"),
        ("Metall-Stilettos (Pin Heels)", "needle-thin metal pin stiletto high heels with sharp pointed toe"),
        ("Pole-Dance-Plateaus (8-Inch)", "towering 8-inch clear acrylic platform stiletto ankle boots"),
        ("Bondage-Fessel-Sandaletten", "strappy leather bondage high heels with buckle straps and padlock ankle cuffs"),
        ("Lack-Domina-Pumps", "glossy black patent dominatrix pointed pumps with extreme 14cm thin stiletto heels"),
        # flat
        ("Ballerinas", "ballet flats"),
        ("Flache Riemchensandalen", "flat strappy leather sandals"),
        ("Gladiator-Sandalen", "knee-high lace-up gladiator sandals"),
        ("Espadrilles", "classic flat canvas espadrilles"),
        ("Loafer", "loafers"),
        ("Sneaker", "sneakers"),
        ("Chunky Sneaker", "chunky platform fashion sneakers"),
        ("Flip-Flops", "flip-flops"),
        # none
        ("Nur Strümpfe", "only sheer stockings, no shoes"),
        ("Nur Socken", "only socks, no shoes"),
        ("Barfuß", "barefoot"),
        # added after the 66-shoe poster: appended rather than sorted into
        # their families (SCHUH_GRUPPEN does that), so the first 66 indices
        # keep matching their poster position for tools that crop tiles by index.
        ("Knöchelriemen-Pumps", "closed pointed-toe pumps with a thin ankle strap and stiletto heels"),
        ("D'Orsay-Pumps", "pointed d'Orsay pumps with cut-away sides baring the arch and stiletto heels"),
        ("Oxford mit Absatz", "heeled leather oxford lace-up shoes with a low block heel"),
        ("T-Strap-Plateaus", "open-toe T-strap platform high heels with a chunky heel"),
        ("Chelsea Boots", "leather chelsea ankle boots with elastic side panels and a low stacked heel"),
        ("D'Orsay-Ballerinas", "pointed d'Orsay flats with cut-away sides baring the arch"),
    ],
    # Placed in front of the shoes. A field of its own, because image models
    # attach colours to the nearest garment when nothing else is in the way:
    # with "black opaque pantyhose" and no shoe colour, the shoes regularly came
    # out black as well. An explicit second colour gives the model a competing
    # binding.
    # Tops - the garment only, the colour lives in "topColor" and goes in
    # front: "wearing a pastel blue ribbed crop top ...". Every wording was
    # rendered (same person, seed and framing, three seeds each) against a bare
    # "crop top" and kept only if the cut showed: all twelve crop tops of the
    # first round did. The first entry is what the bare word gives anyway.
    "top": [
        ("Basic Crop Top", "plain scoop-neck crop tank top with wide shoulder straps"),
        ("Puffärmel-Crop-Top", "cropped top with a square neckline and short gathered puff sleeves with elastic cuffs"),
        ("Wickel-Crop-Top", "short-sleeved wrap crop top with a deep crossover V-neckline, tied in a knot at the side of the waist"),
        ("Wickel-Crop-Top langärmelig", "long-sleeved wrap crop top with a crossover V-neckline"),
        ("Geripptes Crop Top", "sleeveless crew-neck crop top in tight vertical rib knit"),
        ("Crop Top mit Knopfleiste", "sleeveless V-neck crop top with a row of small buttons down the front"),
        ("Off-Shoulder-Crop-Top", "off-the-shoulder crop top with an elasticated ruffled neckline across the upper arms, bare shoulders"),
        ("Bustier-Crop-Top (Spaghettiträger)", "V-neck bustier crop top with double thin spaghetti straps"),
        ("Neckholder-Crop-Top", "halter-neck crop top with a high gathered band around the neck, bare shoulders"),
        ("Crop Top mit Knoten vorn", "short-sleeved V-neck crop top tied in a knot at the center front"),
        ("Crop Top mit Karree-Ausschnitt", "sleeveless crop top with a straight square neckline and wide straps"),
        ("One-Shoulder-Crop-Top", "asymmetric one-shoulder crop top, the other shoulder bare"),
        # Tops and necklines from reference sheets, same test against a bare
        # "top" (two seeds): all fifteen passed; the keyhole only as a
        # teardrop below the collar - "at the chest" turned into a slit.
        ("Peplum-Top", "fitted peplum top with a flared ruffle hem below the waist and flutter sleeves"),
        ("Korsett-Top mit Puffärmeln", "structured corset top with visible boning and long puffed sleeves"),
        ("Milkmaid-Top", "milkmaid top with a sweetheart neckline, short puff sleeves and a tie at the bust"),
        ("Bustier-Top mit Schleife", "sleeveless bustier top with a gathered bust, a bow at the center and a pointed hem"),
        ("Bardot-Top", "Bardot off-the-shoulder top with a ruffled neckline and a shirred waist"),
        ("Lochstickerei-Wickelbluse", "eyelet lace wrap blouse with ruffled cap sleeves and a tie belt"),
        ("Top mit tiefem V-Ausschnitt", "fitted top with a deep plunging V-neckline"),
        ("Top mit Herzausschnitt", "fitted short-sleeved top with a sweetheart neckline"),
        ("Top mit Schlüsselloch", "fitted high-neck top with a small teardrop keyhole cutout just below the collar"),
        ("Ärmelloser Rollkragen", "fitted sleeveless turtleneck top"),
        ("Top mit Wasserfallausschnitt", "sleeveless top with a draped cowl neckline"),
        ("Top mit Schnürausschnitt", "fitted top with a lace-up V-neckline"),
        ("U-Boot-Top mit Cutout", "fitted boat-neck top with a horizontal slit cutout across the chest"),
        ("Stehkragen-Top mit Reißverschluss", "fitted long-sleeved top with a high collar and a front zip"),
        ("Top mit Illusion-Passe", "fitted top with a sheer mesh illusion yoke above the bust"),
        # Bikini tops against a bare "bikini top": that one is already a
        # triangle, hence first; halter looked the same and push-up like
        # underwire, both left out.
        ("Triangel-Bikini", "triangle bikini top with string ties"),
        ("Bandeau-Bikini", "strapless bandeau bikini top"),
        ("Bügel-Bikini", "underwire bikini top with molded cups"),
        ("Sport-Bikini", "sporty bikini top with a scoop neck and wide straps"),
        ("High-Neck-Bikini", "high-neck bikini top"),
        ("One-Shoulder-Bikini", "one-shoulder bikini top"),
        ("Volant-Bikini", "ruffled bikini top with a flounce overlay"),
        ("Criss-Cross-Bikini", "criss-cross bikini top with straps wrapped around the torso"),
        ("Fransen-Bikini", "fringe bikini top with long fringe hanging from the cups"),
        ("Bandeau-Bikini mit Schleife", "bandeau bikini top gathered with a bow at the center"),
        ("Tankini", "tankini top that reaches down to the waist"),
    ],
    "topColor": [
        ("Schwarz", "black"),
        ("Weiß", "white"),
        ("Creme", "cream"),
        ("Beige", "beige"),
        ("Grau", "grey"),
        ("Rot", "red"),
        ("Bordeaux", "burgundy"),
        ("Pink", "hot pink"),
        ("Rosé", "dusty rose"),
        ("Pastellrosa", "pastel pink"),
        ("Violett", "purple"),
        ("Pastellblau", "pastel blue"),
        ("Blau", "navy blue"),
        ("Türkis", "turquoise"),
        ("Mint", "mint green"),
        ("Grün", "emerald green"),
        ("Gelb", "yellow"),
        ("Gold", "gold"),
        ("Silber", "silver"),
        ("Leopardenmuster", "leopard print"),
    ],
    # Bottoms - skirts, shorts and trousers, colour in "bottomColor" in front.
    # Rendered like the tops (same person, full body, three seeds, against a
    # bare "mini skirt"): all passed; "A-line mini skirt" looked exactly like
    # the bare word and is folded into "Minirock".
    "bottom": [
        ("Minirock", "mini skirt"),
        ("Bleistiftrock knielang", "high-waisted knee-length pencil skirt"),
        ("Faltenrock mini", "pleated mini skirt"),
        ("Plisseerock midi", "flowing pleated midi skirt ending below the knee"),
        ("Maxirock mit Beinschlitz", "floor-length maxi skirt with a thigh-high side slit"),
        ("Wickelrock mini", "mini wrap skirt with an asymmetric hem and a tie at the waist"),
        ("Jeans-Shorts", "high-waisted denim shorts with frayed hems"),
        ("Hotpants", "high-waisted hot pants"),
        ("Skinny Jeans", "high-waisted skinny jeans"),
        ("Weite Hose", "high-waisted wide-leg trousers with a front crease"),
        ("Leder-Leggings", "skin-tight leather leggings"),
        ("Cargohose", "baggy low-rise cargo pants with side pockets"),
        # Second round, appended so the first twelve keep their index (tiles
        # are cut by position). Same render test, one seed: 17 of 18 passed;
        # "skin-tight bodycon mini skirt" looked like the bare "mini skirt".
        ("Micro-Minirock", "micro mini skirt"),
        ("Skater-Minirock", "flared skater mini skirt"),
        ("Bleistiftrock mit Schlitz vorn", "knee-length pencil skirt with a high front slit"),
        ("Maxirock mit zwei Schlitzen", "floor-length maxi skirt with two thigh-high side slits"),
        ("High-Low-Rock", "high-low skirt, short in front and long at the back"),
        ("Midirock im Schrägschnitt", "bias-cut midi slip skirt, fluid and clinging to the hips"),
        ("Tüllrock kurz", "short layered tulle skirt"),
        ("Korsettrock", "high-waisted corset skirt with a front lace-up"),
        ("Fransenrock (Latein)", "Latin dance mini skirt with long swinging fringe"),
        ("Tennisrock", "pleated tennis skirt"),
        ("Hosenrock (Skort)", "mini skort"),
        ("Radlerhose", "bike shorts"),
        ("Hotpants high-cut", "high-cut hot pants with high leg openings"),
        ("Booty Shorts", "booty shorts"),
        ("Palazzohose mit Schlitzen", "wide palazzo trousers with high side slits"),
        ("Leggings mit Schnürung", "leggings with lace-up sides from ankle to hip"),
        ("Flare-Leggings", "flared leggings, tight to the knee and flaring to the ankle"),
        # Bikini bottoms against a bare "bikini bottom": Brazilian and hipster
        # looked the same from the front and stay out.
        ("Bikinihöschen", "bikini bottom"),
        ("String-Bikinihöschen", "string bikini bottom with side ties"),
        ("High-Cut-Bikinihöschen", "high-cut bikini bottom with high leg openings"),
        ("High-Waist-Bikinihöschen", "high-waisted bikini bottom"),
        ("Bikinihöschen mit Umschlagbund", "bikini bottom with a folded-over waistband"),
        ("Bikinihöschen mit Röckchen", "skirted bikini bottom with a short ruffled overskirt"),
        ("Bikinihöschen mit Gürtel", "bikini bottom with a thin belt and a round buckle"),
        # Ruffled skirts from a "fantasy skirts" chart, render-tested 2026-09-21:
        # they read as ordinary fashion skirts, so they join the skirts family.
        # A bustle skirt was dropped - it rendered as another tiered mini.
        ("Stufen-Volantrock", "tiered ruffle mini skirt with three layers of flounces"),
        ("Asymmetrischer Volantrock", "asymmetric ruffled high-low skirt, short at the front and "
                                      "cascading to the calves at the back"),
        ("Schnürrock mit Petticoat", "high-waisted high-low skirt with a corset lace-up front and a white "
                                     "ruffled petticoat peeking out"),
        ("Rock mit Seitenschleife", "flared skirt with a large bow at the side of the waist and a draped "
                                    "cascade on one side"),
        ("Volant-Überrock", "ruffled overskirt split open at the front over a short white ruffled underskirt"),
    ],
    # Material of the bottom, written between colour and cut: "a black
    # high-gloss latex pencil skirt". Rendered on a black pencil skirt and
    # black hot pants against no material word; latex and patent only showed
    # their shine with "high-gloss" in front; for latex a follow-up test chose
    # the wording with specular highlights over "high-gloss" alone (still too
    # little shine) and over "mirror-shine" and "liquid shine". Tweed, knit and
    # corduroy were unreadable in black; in grey tweed and corduroy passed,
    # knit looked like the bare word and stays out.
    "bottomMaterial": [
        ("Latex", "high-gloss latex with a wet mirror-like shine and bright white specular highlights"),
        ("Lack", "high-gloss patent vinyl"),
        ("Leder", "leather"),
        ("Wetlook", "wet-look"),
        ("PVC transparent", "transparent PVC"),
        ("Seide", "silk"),
        ("Satin", "satin"),
        ("Samt", "velvet"),
        ("Chiffon", "chiffon"),
        ("Tüll", "tulle"),
        ("Denim", "denim"),
        ("Pailletten", "sequin"),
        ("Spitze", "lace"),
        ("Netz", "mesh"),
        ("Metallic", "metallic"),
        ("Tweed", "tweed"),
        ("Cord", "corduroy"),
    ],
    "bottomColor": None,   # filled in below: the top colours plus denim blue
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

def _val(cat, label, kopie=None):
    if not label or label == NONE:
        return None
    for lbl, value in PRESETS[cat]:
        if lbl == label:
            return value
    # A custom entry (eigene.py): its file, else the copy the node state carries.
    return eigene.wert("person", cat, label, kopie)

def _clean(s):
    return (s or "").strip().rstrip(",;. \t\r\n")


def _artikel(wort):
    if not wort:
        return ""
    w = wort.lower()
    if (w.startswith(("a", "e", "i", "o", "u", "8", "11", "18", "80"))
            and not w.startswith(("uni", "use", "one"))):
        return "an " + wort
    return "a " + wort


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
DETAIL_OBEN = "oben"
DETAIL_FUESSE = "fuesse"
DETAIL_HAENDE = "haende"

# Silhouette plus coarse identity. Enough for the same person to stay
# recognisable, without the micro make-up and fine facial work that the model
# renders large.
_FELDER_IDENTITAET = frozenset({
    "gender", "type", "age", "ageExact", "trigger", "ethnicity", "skinTone", "complexion",
    "height", "figure",
    "hair", "hairColor", "hairEffect",
    "eyes",  # colour from a distance, without shape, lashes or liner
    "top", "topColor", "bottom", "bottomColor", "bottomMaterial",
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

# Below the chest line. A portrait, close-up or face macro cannot show them, and
# in the wardrobe render test a "knee-length pencil skirt" or "pleated midi
# skirt" pulled a portrait out to three-quarter and full length, two seeds out
# of two - the same way off-frame gestures pulled macros wide.
_FELDER_UNTEN = frozenset({
    "bottom", "bottomColor", "bottomMaterial", "hosiery", "hosieryColor",
    "shoes", "shoesColor", "legs", "hips", "waist", "belly",
})

_FELDER_FUESSE = frozenset({"gender", "skinTone", "complexion", "hosiery", "hosieryColor", "shoes", "shoesColor", "free"})
_FELDER_HAENDE = frozenset({"gender", "skinTone", "complexion", "nailLength", "nailColor", "jewellery", "free"})

# Framing -> detail level. Tight = everything in frame, wide = identity only.
KAMERA_DETAIL = {
    "Detail": DETAIL_OBEN,
    "Nahaufnahme": DETAIL_OBEN,
    "Porträt": DETAIL_OBEN,
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
    if detail == DETAIL_OBEN:
        return key not in _FELDER_UNTEN
    if detail == DETAIL_FIGUR:
        return key in _FELDER_FIGUR
    if detail == DETAIL_IDENTITAET:
        return key in _FELDER_IDENTITAET
    if detail == DETAIL_FUESSE:
        return key in _FELDER_FUESSE
    if detail == DETAIL_HAENDE:
        return key in _FELDER_HAENDE
    return True


# With a character LoRA the face, hair and skin come from the LoRA; describing
# them as well gives the model two sources for one thing, and in the expression
# tests the long face description buried the mood (a 150-word prompt stayed
# neutral where 40 words screamed). So with a trigger set these stay out.
LORA_WEG = frozenset({
    "ethnicity", "skinTone", "complexion", "hair", "hairColor", "hairEffect",
    "faceShape", "cheekbones", "nose", "chin", "jawline", "browShape",
    "eyeShape", "eyes", "lashes", "eyeliner", "eyeshadow", "lipShape",
    "lipColor", "lipFinish", "blush", "makeup", "skinFeatures",
})


def geschlecht(p):
    """The noun and possessive for the person: ("woman", "her") and so on."""
    g = p.get("gender") or p.get("type") or ""
    nomen = {"Frau": "woman", "woman": "woman", "a woman": "woman",
             "Mann": "man", "man": "man", "a man": "man",
             "Transfrau": "trans woman", "trans woman": "trans woman", "a trans woman": "trans woman",
             "Junge Frau": "woman", "a young woman": "woman", "young woman": "woman",
             "Junger Mann": "man", "a young man": "man", "young man": "man"}.get(g, "person")
    return nomen, {"woman": "her", "trans woman": "her", "man": "his"}.get(nomen, "their")


def compose_person(p, detail=DETAIL_VOLL, ohne_subjekt=False):
    """Person text out of the value dict. p = dict of English values.

    detail governs the token load: at DETAIL_IDENTITAET (wide shot) and
    DETAIL_FIGUR (full body and similar), the facial and make-up micro-details
    drop out, which the model would otherwise reward with frame area.
    DETAIL_FUESSE and DETAIL_HAENDE isolate feet/hands and suppress distracting
    facial/hair tokens on macro shots. DETAIL_OBEN (portrait, close-up, face
    macros) keeps everything above the chest line and drops what is below it.
    DETAIL_VOLL is the full kit unchanged.

    With a LoRA trigger (p["trigger"]) the fields in LORA_WEG stay out and the
    trigger follows gender and age. ohne_subjekt leaves out the leading "a
    woman" - the Photoshoot puts a mood in front as the subject instead ("a
    terrified woman screaming ...").
    """
    trigger = _clean(p.get("trigger"))

    def ok(key):
        return _erlaubt(detail, key) and not (trigger and key in LORA_WEG)

    feats = (p.get("skinFeatures") or []) if ok("skinFeatures") else []

    # Gender & Type with backward compatibility
    gen_raw = (p.get("gender") if ok("gender") else None) or (p.get("type") if ok("type") else None)
    gen = None
    age_legacy = None
    if gen_raw:
        if gen_raw in ("Frau", "woman", "a woman"):
            gen = "woman"
        elif gen_raw in ("Mann", "man", "a man"):
            gen = "man"
        elif gen_raw in ("Transfrau", "trans woman", "a trans woman"):
            gen = "trans woman"
        elif gen_raw in ("Person", "person", "a person"):
            gen = "person"
        elif gen_raw in ("Junge Frau", "a young woman", "young woman"):
            gen = "woman"
            age_legacy = "in {p} early 20s"
        elif gen_raw in ("Junger Mann", "a young man", "young man"):
            gen = "man"
            age_legacy = "in {p} early 20s"

    if detail == DETAIL_FUESSE:
        subjekt = {"woman": "a woman's lower legs and feet", "trans woman": "a trans woman's lower legs and feet",
                   "man": "a man's lower legs and feet", "person": "a person's lower legs and feet"}.get(gen, "lower legs and feet")
        teile = [subjekt]
        if p.get("skinTone"):
            teile.append(p["skinTone"] + " skin")
        if p.get("complexion"):
            teile.append(p["complexion"])
        hos = p.get("hosiery")
        if hos == "bare legs":
            teile.append("bare legs")
        elif hos:
            h_col = p.get("hosieryColor")
            teile.append("wearing " + ("%s %s" % (h_col, hos) if h_col else hos))
        schuhe = p.get("shoes")
        if schuhe in SCHUHE_OHNE:
            teile.append(schuhe)
        elif schuhe:
            s_col = p.get("shoesColor")
            teile.append("wearing " + ("%s %s" % (s_col, schuhe) if s_col else schuhe))
        frei = _clean(p.get("free"))
        if frei:
            teile.append(frei)
        return ", ".join(teile)

    if detail == DETAIL_HAENDE:
        subjekt = {"woman": "a woman's hands", "trans woman": "a trans woman's hands",
                   "man": "a man's hands", "person": "a person's hands"}.get(gen, "hands")
        teile = [subjekt]
        if p.get("skinTone"):
            teile.append(p["skinTone"] + " skin")
        if p.get("complexion"):
            teile.append(p["complexion"])
        nl = p.get("nailLength")
        nc = p.get("nailColor")
        if nl and nc:
            teile.append(nl.replace("nails", nc + " nails"))
        elif nl:
            teile.append(nl)
        elif nc:
            teile.append(nc + " nails")
        if p.get("jewellery"):
            teile.append("wearing " + p["jewellery"])
        frei = _clean(p.get("free"))
        if frei:
            teile.append(frei)
        return ", ".join(teile)

    poss = {"woman": "her", "trans woman": "her", "man": "his", "person": "their"}.get(gen, "their")
    parts = []

    exact = "".join(ch for ch in _clean(p.get("ageExact")) if ch.isdigit()) if ok("ageExact") else ""
    if exact and int(exact) < MINDESTALTER:
        exact = str(MINDESTALTER)
    if exact and int(exact) > 0:
        alter = int(exact)
        subjekt = None
        if gen == "woman":
            subjekt = "girl" if alter < 18 else "woman"
        elif gen == "trans woman":
            subjekt = "trans girl" if alter < 18 else "trans woman"
        elif gen == "man":
            subjekt = "boy" if alter < 18 else "man"
        elif gen == "person":
            subjekt = "child" if alter < 13 else ("teenager" if alter < 18 else "person")

        if subjekt and not ohne_subjekt:
            parts.append(_artikel(f"{alter}-year-old {subjekt}"))
        else:
            parts.append(f"{alter} years old")
    elif ok("age") and (p.get("age") or age_legacy):
        age_val = p.get("age") or age_legacy
        if age_val == "{child}":
            sub = {"woman": "young girl", "trans woman": "young trans girl", "man": "young boy", "person": "young child"}.get(gen, "young child")
            parts.append(_artikel(sub))
        elif age_val == "{teen}":
            sub = {"woman": "teenage girl", "trans woman": "teenage trans girl", "man": "teenage boy", "person": "teenager"}.get(gen, "teenager")
            parts.append(_artikel(sub))
        else:
            if gen and not ohne_subjekt:
                parts.append(_artikel(gen))
            parts.append(age_val.replace("{p}", poss))
    elif gen and not ohne_subjekt:
        parts.append(_artikel(gen))

    if trigger:
        parts.append(trigger)

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

    # Top first among the clothes - it is what a waist-up frame shows. The
    # colour goes in front, as with legwear and shoes; the article is picked
    # for the first word actually written ("an off-the-shoulder" vs "a").
    top = p.get("top") if ok("top") else None
    topf = p.get("topColor") if ok("topColor") else None
    if top:
        text = " ".join(x for x in [topf, top] if x)
        parts.append("wearing " + _artikel(text))

    # Bottom right after the top and joined with "with", the way the render
    # test wrote it ("wearing a white crop top, with a grey pencil skirt").
    unten = p.get("bottom") if ok("bottom") else None
    untenf = p.get("bottomColor") if ok("bottomColor") else None
    untenm = p.get("bottomMaterial") if ok("bottomMaterial") else None
    if unten and untenm and _EIGENER_STOFF.search(unten):
        untenm = None
    if unten:
        text = " ".join(x for x in [untenf, untenm, unten] if x)
        text = text if _OHNE_ARTIKEL.search(unten) else _artikel(text)
        parts.append(("with " if top else "wearing ") + text)

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
_SINGLE = ["gender", "age", "ethnicity", "skinTone", "complexion",
           "height", "figure", "bust", "shoulders", "waist", "belly",
           "hips", "legs",
           "hair", "hairColor", "hairEffect",
           "faceShape", "cheekbones", "nose", "chin", "jawline", "eyeShape",
           "browShape", "lipShape",
           "eyes", "lashes", "eyeliner", "eyeshadow", "blush",
           "lipColor", "lipFinish", "makeup",
           "nailLength", "nailColor", "hosiery", "hosieryColor",
           "top", "topColor", "bottom", "bottomColor", "bottomMaterial", "shoes", "shoesColor",
           "jewellery", "eyewear", "headwear"]

# Families of the shoe list - divided into families so the list stays organized.
SCHUH_GRUPPEN = {
    "Pumps": ["Pumps spitz", "Pumps mandelförmig", "Peeptoe-Pumps",
              "Slingback-Pumps", "Mary-Jane-Pumps", "Lack-Pumps",
              "Wildleder-Pumps", "Transparent-Pumps (Perspex)",
              "Knöchelriemen-Pumps", "D'Orsay-Pumps"],
    "Absätze": ["Stiletto High Heels", "Sehr hohe Stilettos", "Kitten Heels",
                "Blockabsatz-Pumps", "Keilabsatz", "Plateau-Heels",
                "Plateau-Stilettos", "Extreme Plateau-Heels",
                "Lack-Plateau-Heels", "Clogs mit Holzsohle",
                "Oxford mit Absatz"],
    "Sandaletten": ["Riemchen-Sandaletten", "Sandaletten mit Knöchelriemen",
                    "Schnür-Sandaletten (Wrap-Up)", "Zehensteg-Sandaletten",
                    "Plateau-Sandaletten", "Mules mit Absatz", "Pantoletten",
                    "Espadrilles mit Keilabsatz", "T-Strap-Plateaus"],
    "Stiefel": ["Stiefeletten mit Absatz", "Spitze Stiletto-Stiefeletten",
                "Schnür-Stiefeletten", "Sock-Boots", "Kniehohe Stiefel",
                "Overknee-Stiefel", "Overknee-Lackstiefel",
                "Cowboystiefel", "Combat Boots", "Chelsea Boots"],
    "Tanz & Sport": ["Reitstiefel", "Spitzenschuhe (Ballett)", "Ballettschläppchen",
                    "Gymnastikschuhe", "Latein-Tanzschuhe", "Jazzschuhe",
                    "Schlittschuhe (Eiskunstlauf)", "Rollschuhe (Quad Skates)",
                    "Laufschuhe", "Wanderschuhe"],
    "Fetish": ["Ballet Heels (Extrem)", "Absatzlose Heels (Heelless)",
               "Schritthohe Lackstiefel", "Huf-Heels (Hoof Boots)",
               "Korsett-Schnürstiefel", "Latex-Overknees",
               "Metall-Stilettos (Pin Heels)", "Pole-Dance-Plateaus (8-Inch)",
               "Bondage-Fessel-Sandaletten", "Lack-Domina-Pumps"],
    "flach": ["Ballerinas", "Flache Riemchensandalen", "Gladiator-Sandalen",
              "Espadrilles", "Loafer", "Sneaker", "Chunky Sneaker", "Flip-Flops",
              "D'Orsay-Ballerinas"],
    "ohne": ["Nur Strümpfe", "Nur Socken", "Barfuß"],
}

PRESETS["bottomColor"] = list(PRESETS["topColor"]) + [("Jeansblau", "light-wash blue")]

# Cuts that name their own fabric ignore the material field - otherwise it
# would read "latex denim shorts" or "satin leather leggings".
_EIGENER_STOFF = re.compile(r"\b(?:denim|jeans|leather|tulle)\b")

# Plural garments take no article: "wearing grey hot pants", not "a grey hot pants".
_OHNE_ARTIKEL = re.compile(r"\b(?:shorts|jeans|pants|trousers|leggings)\b")

# Families of the tops and bottoms, by label like the shoes. New presets are
# appended to PRESETS (poster positions), so a family cannot be a slice of it:
# anything appended would land in the last family.
OBERTEIL_GRUPPEN = {
    "Crop Tops": ["Basic Crop Top", "Puffärmel-Crop-Top", "Wickel-Crop-Top",
                  "Wickel-Crop-Top langärmelig", "Geripptes Crop Top",
                  "Crop Top mit Knopfleiste", "Off-Shoulder-Crop-Top",
                  "Bustier-Crop-Top (Spaghettiträger)", "Neckholder-Crop-Top",
                  "Crop Top mit Knoten vorn", "Crop Top mit Karree-Ausschnitt",
                  "One-Shoulder-Crop-Top"],
    "Tops & Blusen": ["Peplum-Top", "Korsett-Top mit Puffärmeln", "Milkmaid-Top",
                      "Bustier-Top mit Schleife", "Bardot-Top",
                      "Lochstickerei-Wickelbluse", "Top mit tiefem V-Ausschnitt",
                      "Top mit Herzausschnitt", "Top mit Schlüsselloch",
                      "Ärmelloser Rollkragen", "Top mit Wasserfallausschnitt",
                      "Top mit Schnürausschnitt", "U-Boot-Top mit Cutout",
                      "Stehkragen-Top mit Reißverschluss", "Top mit Illusion-Passe"],
    "Bikini": ["Triangel-Bikini", "Bandeau-Bikini", "Bügel-Bikini", "Sport-Bikini",
               "High-Neck-Bikini", "One-Shoulder-Bikini", "Volant-Bikini",
               "Criss-Cross-Bikini", "Fransen-Bikini", "Bandeau-Bikini mit Schleife",
               "Tankini"],
}

UNTERTEIL_GRUPPEN = {
    "Röcke": ["Minirock", "Bleistiftrock knielang", "Faltenrock mini", "Plisseerock midi",
              "Maxirock mit Beinschlitz", "Wickelrock mini", "Micro-Minirock",
              "Skater-Minirock", "Bleistiftrock mit Schlitz vorn",
              "Maxirock mit zwei Schlitzen", "High-Low-Rock", "Midirock im Schrägschnitt",
              "Tüllrock kurz", "Korsettrock", "Fransenrock (Latein)", "Tennisrock",
              "Hosenrock (Skort)", "Stufen-Volantrock", "Asymmetrischer Volantrock",
              "Schnürrock mit Petticoat", "Rock mit Seitenschleife", "Volant-Überrock"],
    "Shorts & Hosen": ["Jeans-Shorts", "Hotpants", "Skinny Jeans", "Weite Hose",
                       "Leder-Leggings", "Cargohose", "Radlerhose", "Hotpants high-cut",
                       "Booty Shorts", "Palazzohose mit Schlitzen", "Leggings mit Schnürung",
                       "Flare-Leggings"],
    "Bikini": ["Bikinihöschen", "String-Bikinihöschen", "High-Cut-Bikinihöschen",
               "High-Waist-Bikinihöschen", "Bikinihöschen mit Umschlagbund",
               "Bikinihöschen mit Röckchen", "Bikinihöschen mit Gürtel"],
}

# Families of the headwear - with the hats of 2026-09-21 the flat list had 29
# entries.
KOPF_GRUPPEN = {
    "Hüte": ["Sonnenhut", "Cowboyhut", "Fedora", "Glockenhut", "Fischerhut", "Zylinder",
             "Pillbox mit Schleier", "Fascinator", "Panamahut", "Melone", "Kreissäge",
             "Schlapphut", "Wagenradhut"],
    "Mützen & Kappen": ["Mütze", "Baseballkappe", "Barett", "Schiebermütze", "Matrosenmütze",
                        "Weiße Kapitänsmütze", "Elbsegler", "Uschanka", "Visor"],
    "Haarschmuck & Tücher": ["Stirnband", "Haarreif", "Kopftuch"],
    "Fetish": ["Lack-Schirmmütze (Domina)", "Leder-Hasenmaske", "Leder-Katzenmaske", "Augenbinde"],
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
    ("Grund",    ["gender", "age", "ageExact", "trigger", "ethnicity", "skinTone",
                  "complexion"]),
    ("Körper",   ["height", "figure", "shoulders", "bust", "waist", "belly",
                  "hips", "legs"]),
    ("Kopf",     [["hair", "hairColor"], "hairEffect", ["eyeShape", "eyes"],
                  "lashes"]),
    ("Gesicht",  ["faceShape", "cheekbones", "nose", "chin", "jawline",
                  "browShape", "lipShape"]),
    ("Make-up",  ["eyeliner", "eyeshadow", "blush", ["lipColor", "lipFinish"],
                  "makeup", "skinFeatures", ["nailLength", "nailColor"]]),
    ("Kleidung", [["top", "topColor"], ["bottom", "bottomColor"],
                  ["hosiery", "hosieryColor"], ["shoes", "shoesColor"], "details"]),
    # Jewellery, glasses and headwear are not garments and got lost at the end
    # of the clothing list - their own section since the Steckbrief layout.
    ("Accessoires", ["jewellery", "eyewear", "headwear"]),
]

# Fields that are not a row of their own but hang under another one: the
# material belongs to the bottom and was read as a garment of its own when it
# stood on a separate row.
UNTERFELDER = {"bottom": "bottomMaterial"}

# What an outfit is: the clothing and accessories sections, the material under
# the bottom, and the free text of the clothing section ("details", stored as
# "free"). A Wardrobe node sets these and nothing else; in the series an outfit
# replaces all of them on the person, set or not, so no garment of the person's
# own survives into another outfit.
OUTFIT_SEKTIONEN = ("Kleidung", "Accessoires")

OUTFIT_FELDER = frozenset(
    [f for name, eintraege in SEKTIONEN if name in OUTFIT_SEKTIONEN
     for e in eintraege for f in (e if isinstance(e, list) else [e]) if f != "details"]
    + list(UNTERFELDER.values()) + ["free"])


# The Person Builder's own sections: everything but the outfit, which lives in
# the Wardrobe node. The fields stay in the value dict - older workflows and
# saved persons that still carry clothing render as before.
PERSON_SEKTIONEN = [name for name, _ in SEKTIONEN if name not in OUTFIT_SEKTIONEN]


def garderobe_lesen(garderobe):
    """The outfit list of a Wardrobe output: [{"name": ..., "werte": {...}}].
    The output is {"aktiv": i, "outfits": [...]}; a bare list is read too.
    Anything unreadable counts as no wardrobe."""
    if not garderobe:
        return []
    try:
        daten = json.loads(garderobe) if isinstance(garderobe, str) else garderobe
    except (TypeError, ValueError):
        print("[Photoshoot] wardrobe unreadable, ignored.")
        return []
    liste = daten.get("outfits") if isinstance(daten, dict) else daten
    if not isinstance(liste, list):
        return []
    return [o for o in liste if isinstance(o, dict) and isinstance(o.get("werte"), dict)]


def garderobe_aktiv(garderobe):
    """The outfit the person wears outside a series: the Wardrobe's open tab."""
    try:
        daten = json.loads(garderobe) if isinstance(garderobe, str) else garderobe
        return max(0, int(daten.get("aktiv") or 0)) if isinstance(daten, dict) else 0
    except (TypeError, ValueError, AttributeError):
        return 0


def mit_outfit(p, outfit):
    """The person's value dict wearing this outfit (a dict of the same English
    values, as the Wardrobe node writes them)."""
    q = {k: v for k, v in p.items() if k not in OUTFIT_FELDER}
    q.update({k: v for k, v in (outfit or {}).items() if k in OUTFIT_FELDER})
    return q


# Label for a row group. With no entry, the name of the first field applies -
# "Frisur", "Lippen", "Nägel", "Strümpfe", "Schuhe" are right as they stand.
ZEILENNAMEN = {"eyeShape": "Augen"}

# Kind of control per field; anything not named here is a plain dropdown.
FELDART = {
    "ageExact": "text",
    "details": "text",
    "trigger": "text",   # a character LoRA's trigger - see LORA_WEG
    "skinFeatures": "mehrfach",  # chips to switch on and off, any number of them
    # One dropdown with the families as <optgroup>s. Before that a separate
    # family dropdown in front of the model (a click more at half the width),
    # before that a chip block over all shoes that did not fit the tab, before
    # that one flat list that was unusable in its own way.
    "shoes": "familie",
    "top": "familie",
    "bottom": "familie",
    "headwear": "familie",
}

# What a colour button and the palette show per colour label. A plain hex, or a
# CSS gradient for metallics, patterns and the special cases (heterochromia half
# and half, French nails with a white tip, "clear" as a checkerboard). Purely for
# the interface - the prompt gets the English value from PRESETS as before.
_KLEIDFARBEN = {
    "Schwarz": "#141414", "Weiß": "#f4f4f4", "Creme": "#efe6d2", "Beige": "#d6c2a0", "Grau": "#8a8a8a",
    "Rot": "#c4162a", "Bordeaux": "#6a1428", "Pink": "#e0307a", "Rosé": "#c9848c", "Pastellrosa": "#f4bccb",
    "Violett": "#6a3aa0", "Pastellblau": "#a9c8ec", "Blau": "#1f2d5a", "Türkis": "#1fb5b0", "Mint": "#a8e6cf",
    "Grün": "#1f7a55", "Gelb": "#f2d23a", "Gold": "linear-gradient(135deg,#f3d27a,#b8862f)",
    "Silber": "linear-gradient(135deg,#f0f0f0,#9a9a9a)",
    "Leopardenmuster": "radial-gradient(circle at 30% 30%,#3a2412 18%,transparent 20%),"
                       "radial-gradient(circle at 72% 64%,#3a2412 16%,transparent 18%),#c8963e",
    "Zebramuster": "repeating-linear-gradient(45deg,#111 0 3px,#f4f4f4 3px 6px)",
    "Jeansblau": "#7fa3c8", "Hautfarben": "#e2b79a", "Braun": "#6b4428", "Cognac": "#9a5a2a",
    "Kupfer": "linear-gradient(135deg,#e39a6a,#9a4a26)", "Karamell": "#b07a44", "Anthrazit": "#3a3a3e",
    "Gold schimmernd": "linear-gradient(135deg,#f7e3a0,#c9a24a,#f7e3a0)",
    "Silber schimmernd": "linear-gradient(135deg,#fafafa,#b0b0b0,#fafafa)",
    "Durchsichtig": "repeating-conic-gradient(#bbb 0 25%,#eee 0 50%) 0 0/8px 8px",
}
FARBWERTE = {
    "skinTone": {"Sehr hell": "#f6dfcf", "Hell": "#ecc9ae", "Hell gebräunt": "#dcac85", "Gebräunt": "#c68e63",
                 "Oliv": "#b58a5c", "Bronze": "#a06b3f", "Braun": "#7d4f2e", "Dunkelbraun": "#5a3620",
                 "Ebenholz": "#3a2316"},
    "hairColor": {"Blond": "#d9b56a", "Platinblond": "#ece2c6", "Dunkelblond": "#a9844c", "Braun": "#6b4428",
                  "Dunkelbraun": "#3b2517", "Schwarz": "#141111", "Rot / Kupfer": "#b4532a", "Kastanie": "#7a3522",
                  "Erdbeerblond": "#d08a5c", "Grau / Silber": "#b9b9b9", "Eisweiß": "#eef2f5",
                  "Pastellrosa": "#f1b5c8", "Mitternachtsblau": "#1d2a55", "Smaragdgrün": "#1f7a55"},
    "eyes": {"Blau": "#4f7fb8", "Graublau": "#7d93a8", "Eisblau": "#a9d0e6", "Grün": "#4f8a4f",
             "Graugrün": "#7f9486", "Braun": "#6b4428", "Dunkelbraun": "#3b2517", "Haselnuss": "#8a6a3a",
             "Grau": "#8f959a", "Bernstein": "#c08a2e", "Blau (strahlend)": "#2f8fff",
             "Grün (strahlend)": "#2fcf6a", "Türkis (strahlend)": "#1fd6c8", "Violett (strahlend)": "#9a5cff",
             "Bernstein (leuchtend)": "#ffb020", "Silbergrau (strahlend)": "#d6dde3",
             "Rot (unnatürlich)": "#d0102a", "Heterochromie": "linear-gradient(90deg,#4f7fb8 50%,#6b4428 50%)"},
    "eyeshadow": {"Nude": "#d8b49a", "Braun": "#8a5a3a", "Bronze": "linear-gradient(135deg,#c98a4a,#7a4a22)",
                  "Gold": "linear-gradient(135deg,#f3d27a,#b8862f)",
                  "Kupfer": "linear-gradient(135deg,#e39a6a,#9a4a26)", "Rosé": "#d99aa0", "Beere": "#8a2a4a",
                  "Violett": "#7a4aa0", "Blau": "#3a5aa0", "Grün": "#3a7a4a",
                  "Silber": "linear-gradient(135deg,#f0f0f0,#9a9a9a)",
                  "Schwarz verblendet": "radial-gradient(#111 30%,#555)",
                  "Glitzer": "conic-gradient(#f3d27a,#fff,#d99aa0,#fff,#a9d0e6,#fff,#f3d27a)"},
    "lipColor": {"Natürlich": "#c98f86", "Nude": "#c99a86", "Beige": "#d6b39a", "Altrosa": "#c07a80",
                 "Pfirsich": "#f0a07a", "Rot": "#c4162a", "Kirschrot": "#b0102a", "Dunkelrot": "#7a1020",
                 "Weinrot": "#6a1428", "Burgunder": "#5a1424", "Ziegelrot": "#a0402a", "Koralle": "#f06a5a",
                 "Orange": "#f06a1a", "Rosa": "#f0a0b8", "Pink": "#e0307a", "Fuchsia": "#d0208a",
                 "Magenta": "#c0107a", "Neonpink": "#ff2a9a", "Beere": "#8a2a4a", "Pflaume": "#5a2040",
                 "Mauve": "#a0707a", "Violett": "#7a3aa0", "Lila": "#4a1a6a", "Aubergine": "#3a1430",
                 "Braun": "#5a3020", "Toffee": "#9a6a4a", "Schwarz": "#141111", "Blau": "#1a2a6a",
                 "Gold (metallic)": "linear-gradient(135deg,#f3d27a,#b8862f)",
                 "Kupfer (metallic)": "linear-gradient(135deg,#e39a6a,#9a4a26)",
                 "Silber (metallic)": "linear-gradient(135deg,#f0f0f0,#9a9a9a)"},
    "nailColor": {"Rot": "#c4162a", "French": "linear-gradient(180deg,#fff 34%,#f2d6cc 34%)",
                  "Nude": "#d9b39f", "Schwarz": "#141111", "Pink": "#e0307a", "Weiß": "#f4f4f4"},
}
for _cat in ("topColor", "bottomColor", "hosieryColor", "shoesColor"):
    FARBWERTE[_cat] = {lbl: _KLEIDFARBEN[lbl] for lbl, _ in PRESETS[_cat]}

# A colour the prompt drops, so the interface greys its button out: legwear
# colour with bare legs, shoe colour with no shoes (see compose_person()).
FARBE_ENTFAELLT = {"hosieryColor": ("hosiery", ["bare legs"]),
                   "shoesColor": ("shoes", sorted(SCHUHE_OHNE))}

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
    "gender": "Geschlecht", "age": "Alter", "ageExact": "genaues Alter",
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
    "top": "Oberteil", "topColor": "Oberteilfarbe",
    "bottom": "Unterteil", "bottomColor": "Unterteilfarbe", "bottomMaterial": "Material",
    "details": "Details",
    "trigger": "LoRA-Trigger",
}

# Free text fields need a placeholder instead of a preset list.
PLATZHALTER = {
    "ageExact": "genaues Alter, z. B. 34 (schlägt den Bereich, ab 18)",
    "details": "Weitere Details (englisch), z. B. wearing a red raincoat",
    "trigger": "Trigger einer Charakter-LoRA, z. B. EileenX – Gesicht, Haare und Make-up kommen dann aus der LoRA",
}

DEFAULT_STATE = {
    "felder": {cat: NONE for cat in _SINGLE},
    "mehrfach": {"skinFeatures": []},
    "texte": {"ageExact": "", "details": "", "trigger": ""},
    "sektion": SEKTIONEN[0][0],
    "gruppe": {"shoes": ALLE, "top": ALLE, "bottom": ALLE},
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
            "optional": {
                # A Wardrobe node: the person wears its open tab, and the
                # series changes through all its outfits (see shooting.py).
                "garderobe": ("STRING", {"forceInput": True}),
            },
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
                   "fuer Photoshooting, das je Kameraeinstellung kuerzt. Die Kleidung "
                   "kommt aus einer Wardrobe an 'garderobe': die Person traegt den offenen Reiter.")

    def build(self, PersonState=None, garderobe=None):
        try:
            state = json.loads(PersonState) if PersonState else dict(DEFAULT_STATE)
        except (TypeError, ValueError):
            print("[Photoshoot Person] State unreadable, using defaults.")
            state = dict(DEFAULT_STATE)
        p = werte_aus_state(state)
        # Dressed from the wardrobe: the open tab replaces every clothing
        # field, and the whole wardrobe travels along in person_data under
        # "_garderobe" for the series' costume changes.
        outfits = garderobe_lesen(garderobe)
        if outfits:
            k = min(garderobe_aktiv(garderobe), len(outfits) - 1)
            p = mit_outfit(p, outfits[k]["werte"])
            p["_garderobe"] = outfits
        # person_data: raw values for the framing-dependent compose_person() in
        # the photoshoot. Without this output you would have to take the
        # finished text apart again - which cannot be done reliably.
        return (compose_person(p), json.dumps(p, ensure_ascii=False))


def werte_aus_state(state):
    """The English value dict of a Person Builder state (labels -> values).
    The Wardrobe node reads its clothing fields through the same function."""
    felder = state.get("felder") or {}
    texte = state.get("texte") or {}
    # Prompts of the custom entries in use, so the workflow renders without their file.
    kopie = state.get("eigene")

    p = {cat: _val(cat, felder.get(cat), kopie) for cat in _SINGLE}
    if not p.get("gender") and felder.get("type"):
        p["gender"] = _val("gender", felder.get("type")) or felder.get("type")
    p["ageExact"] = texte.get("ageExact", "")
    p["free"] = texte.get("details", "")
    p["trigger"] = texte.get("trigger", "")

    # Skin features are now any number of chips instead of three
    # dropdowns. Duplicates are dropped, so that "tattoos, tattoos" does not
    # end up in the prompt.
    feats, gesehen = [], set()
    for label in (state.get("mehrfach") or {}).get("skinFeatures") or []:
        wert = _val("skinFeatures", label, kopie)
        if wert and wert not in gesehen:
            gesehen.add(wert)
            feats.append(wert)
    p["skinFeatures"] = feats
    return p


NODE_CLASS_MAPPINGS = {"Krea2PersonBuilder": Krea2PersonBuilder}
NODE_DISPLAY_NAME_MAPPINGS = {"Krea2PersonBuilder": "Photoshoot – Person"}


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
    assert detail_fuer_kamera("Porträt") == DETAIL_OBEN
    oben = compose_person(demo, DETAIL_OBEN)
    assert "cat-eye" in oben and "sneakers" not in oben and "sneakers" in voll
    print("ok")
