"""
English display labels for the German building blocks.

The German labels are also the keys: they sit in node.properties, in
KAMERA_FOKUS, in the families and in every saved workflow. What gets translated
here is therefore the display and nothing else - this is what appears in place
of the German label when ComfyUI runs in another language. None of it ever goes
into a prompt; there the English value from PRESETS still lands.

Translation happens per category, not flat. The same German label means
different things in different fields: "Schmal" is narrow on the nose, slim at
the waist and thin on the lips; "Braun" is tan for hosiery and chocolate on the
lips. A single flat table would necessarily be wrong in those places.

When an entry is missing, the German label stays. That is visible but not
broken - and tests/smoke.py reports the gaps.

Which language applies is decided by js/shared.mjs: the Comfy.Locale setting,
and when nothing is set there, the browser language - the same way ComfyUI
itself does it. On a German browser everything is German without any setting at
all.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Person Builder - option lists per category
# ─────────────────────────────────────────────────────────────────────────────
PERSON = {
    "gender": {
        "Frau": "Woman", "Mann": "Man", "Transfrau": "Trans woman", "Person": "Person",
    },
    "age": {
        "Anfang 20": "Early 20s", "Mitte 20": "Mid 20s", "Ende 20": "Late 20s",
        "Anfang 30": "Early 30s", "Mitte 30": "Mid 30s", "Ende 30": "Late 30s",
        "40er": "40s", "50er": "50s", "60+": "60+", "Senior (70+)": "Senior (70+)",
    },
    "ethnicity": {
        "Osteuropäisch": "Eastern European", "Skandinavisch": "Scandinavian",
        "Mediterran": "Mediterranean", "Nahöstlich": "Middle Eastern",
        "Latina": "Latina", "Ostasiatisch": "East Asian",
        "Südostasiatisch": "Southeast Asian", "Südasiatisch": "South Asian",
        "Afrikanisch": "African", "Gemischt": "Mixed",
    },
    "skinTone": {
        "Sehr hell": "Very fair", "Hell": "Fair", "Hell gebräunt": "Light tan",
        "Gebräunt": "Tan", "Oliv": "Olive", "Braun": "Brown",
        "Dunkelbraun": "Deep brown",
    },
    "complexion": {
        "Dewy": "Dewy", "Matt": "Matte", "Porzellan": "Porcelain",
        "Natürliche Poren": "Natural pores", "Sonnengegerbt": "Weathered",
        "Rötlich": "Rosy", "Blass": "Pale",
    },
    "height": {
        "Klein": "Short", "Zierlich": "Petite",
        "Durchschnittlich": "Average", "Groß": "Tall",
        "Model-Größe": "Model height",
    },
    "figure": {
        "Sehr schlank": "Very slim", "Schlank": "Slim", "Athletisch": "Athletic",
        "Durchschnittlich": "Average", "Kurvig": "Curvy", "Sanduhr": "Hourglass",
        "Mollig": "Chubby", "Plus-Size": "Plus-size", "Stämmig": "Stocky",
        "Muskulös": "Muscular",
    },
    "bust": {
        "Klein": "Small", "Mittel": "Medium", "Voll": "Full", "Groß": "Large",
    },
    "shoulders": {
        "Schmal": "Narrow", "Zierlich": "Delicate", "Gerade": "Squared",
        "Breit": "Broad", "Sportlich": "Athletic",
    },
    "waist": {
        "Sehr schmal": "Very narrow", "Schmal": "Slim", "Definiert": "Defined",
        "Gerade": "Straight", "Weich": "Soft",
    },
    "belly": {
        "Flach": "Flat", "Definiert": "Toned", "Sixpack": "Six-pack",
        "Weich": "Soft",
    },
    "legs": {
        "Lang": "Long", "Schlank": "Slender", "Muskulös": "Muscular",
        "Kräftig": "Strong", "Kurz": "Short",
    },
    "hips": {
        "Schmal": "Narrow", "Rund": "Rounded", "Breit": "Wide",
        "Betont": "Pronounced",
    },
    "hair": {
        "Lang glatt": "Long straight", "Lange Wellen": "Long waves",
        "Bob": "Bob", "Pixie": "Pixie", "Pferdeschwanz": "Ponytail",
        "Messy Bun": "Messy bun", "Flechtzopf": "Side braid",
        "Locken": "Curls", "Pony": "Bangs", "Half-up": "Half-up",
        "Sleek zurück": "Sleek back", "Kurz wellig": "Short tousled",
    },
    "hairColor": {
        "Blond": "Blonde", "Platinblond": "Platinum blonde",
        "Dunkelblond": "Dark blonde", "Braun": "Brown",
        "Dunkelbraun": "Dark brown", "Schwarz": "Black",
        "Rot / Kupfer": "Copper red", "Kastanie": "Auburn",
        "Grau / Silber": "Silver grey",
    },
    "faceShape": {
        "Oval": "Oval", "Herzförmig": "Heart-shaped", "Rund": "Round",
        "Eckig": "Square", "Länglich": "Long", "Diamant": "Diamond",
    },
    "cheekbones": {
        "Hoch betont": "High, pronounced", "Markant": "Sculpted",
        "Weich": "Soft", "Flach": "Flat",
    },
    "nose": {
        "Klein": "Small", "Gerade": "Straight", "Schmal": "Narrow",
        "Stupsnase": "Button", "Markant": "Prominent",
        "Leicht gebogen": "Slightly aquiline",
    },
    "eyeShape": {
        "Mandelförmig": "Almond-shaped", "Rund": "Round", "Schmal": "Narrow",
        "Schlupflider": "Hooded", "Weit auseinander": "Wide-set",
        "Katzenaugen": "Upturned",
    },
    "lipShape": {
        "Voll": "Full", "Schmal": "Thin", "Breit": "Wide",
        "Amorbogen": "Cupid's bow", "Volle Unterlippe": "Fuller lower lip",
    },
    "chin": {
        "Spitz": "Pointed", "Schmal": "Narrow", "Rund": "Rounded",
        "Breit": "Broad", "Grübchen": "Dimpled", "Fliehend": "Receding",
    },
    "jawline": {
        "Weich": "Soft", "Definiert": "Defined", "Markant": "Sharp",
        "Schmal": "Narrow",
    },
    "browShape": {
        "Schmal": "Thin", "Dicht": "Thick", "Gerade": "Straight",
        "Geschwungen": "Arched", "Buschig": "Bushy",
    },
    "eyes": {
        "Blau": "Blue", "Graublau": "Greyish blue", "Eisblau": "Icy blue",
        "Grün": "Green", "Graugrün": "Greyish green", "Braun": "Brown",
        "Dunkelbraun": "Dark brown", "Haselnuss": "Hazel", "Grau": "Grey",
        "Bernstein": "Amber", "Blau (strahlend)": "Blue (vivid)",
        "Grün (strahlend)": "Green (vivid)", "Türkis (strahlend)": "Turquoise (vivid)",
        "Violett (strahlend)": "Violet (vivid)", "Bernstein (leuchtend)": "Amber (glowing)",
        "Silbergrau (strahlend)": "Silver-grey (vivid)",
        "Rot (unnatürlich)": "Crimson (unnatural)", "Heterochromie": "Heterochromia",
    },
    "hairEffect": {
        "Balayage": "Balayage", "Ombré": "Ombré", "Highlights": "Highlights",
        "Lowlights": "Lowlights", "Dip-Dye": "Dip-dye",
        "Zweifarbig": "Two-tone", "Graue Strähne": "Silver streak",
        "Ansatz sichtbar": "Visible roots",
    },
    "lashes": {
        "Natürlich": "Natural", "Lang": "Long", "Voluminös": "Voluminous",
        "Falsche Wimpern": "False lashes", "Wispy": "Wispy",
    },
    "lipColor": {
        "Natürlich": "Natural", "Nude": "Nude", "Beige": "Beige",
        "Altrosa": "Dusty rose", "Pfirsich": "Peach", "Rot": "Red",
        "Kirschrot": "Cherry red", "Dunkelrot": "Dark red",
        "Weinrot": "Wine red", "Burgunder": "Burgundy",
        "Ziegelrot": "Brick red", "Koralle": "Coral", "Orange": "Orange",
        "Rosa": "Soft pink", "Pink": "Hot pink", "Fuchsia": "Fuchsia",
        "Magenta": "Magenta", "Neonpink": "Neon pink", "Beere": "Berry",
        "Pflaume": "Plum", "Mauve": "Mauve", "Violett": "Violet",
        "Lila": "Deep purple", "Aubergine": "Aubergine",
        "Braun": "Chocolate", "Toffee": "Toffee", "Schwarz": "Black",
        "Blau": "Deep blue", "Gold (metallic)": "Gold (metallic)",
        "Kupfer (metallic)": "Copper (metallic)",
        "Silber (metallic)": "Silver (metallic)",
    },
    "lipFinish": {"Matt": "Matte", "Gloss": "Gloss", "Satin": "Satin"},
    "eyeliner": {
        "Ohne": "None", "Dezent": "Subtle", "Kajal": "Kohl",
        "Kajal unten": "Kohl, lower lid", "Cat-Eye": "Cat-eye",
        "Breit gezogen": "Bold", "Grafisch": "Graphic",
        "Weiß akzentuiert": "White accent",
    },
    "eyeshadow": {
        "Nude": "Nude", "Braun": "Warm brown", "Bronze": "Bronze",
        "Gold": "Gold", "Kupfer": "Copper", "Rosé": "Rosy", "Beere": "Berry",
        "Violett": "Violet", "Blau": "Blue", "Grün": "Green",
        "Silber": "Silver", "Schwarz verblendet": "Blended black",
        "Glitzer": "Glitter",
    },
    "blush": {
        "Ohne": "None", "Dezent": "Subtle", "Rosig": "Rosy",
        "Pfirsich": "Peach", "Kräftig": "Strong", "Sonnenkuss": "Sun-kissed",
    },
    "makeup": {
        "Ohne": "None", "Natürlich": "Natural", "Dezent": "Subtle",
        "Glam": "Glam", "Smokey Eyes": "Smokey eyes", "Editorial": "Editorial",
    },
    "skinFeatures": {
        "Sommersprossen": "Freckles", "Blasse Haut": "Pale skin",
        "Schönheitsfleck": "Beauty mark", "Grübchen": "Dimples",
        "Muttermale": "Moles", "Tattoos": "Tattoos", "Piercings": "Piercings",
        "Sommerbräune": "Sun-kissed",
    },
    "nailLength": {
        "Kurz gepflegt": "Short", "Mittel": "Medium", "Lang": "Long",
        "Extra lang (Acryl)": "Extra long (acrylic)", "Stiletto": "Stiletto",
    },
    "nailColor": {
        "Rot": "Red", "French": "French", "Nude": "Nude", "Schwarz": "Black",
        "Pink": "Pink", "Weiß": "White",
    },
    "hosiery": {
        "Nackte Beine": "Bare legs",
        "Strumpfhose hauchdünn": "Sheer tights (15 den)",
        "Strumpfhose glänzend": "Glossy tights",
        "Strumpfhose matt": "Matte tights",
        "Strumpfhose blickdicht": "Opaque tights",
        "Strumpfhose gemustert": "Patterned tights",
        "Netzstrumpfhose": "Fishnet tights",
        "Netzstrumpfhose grob": "Wide-mesh fishnets",
        "Halterlose Strümpfe": "Hold-up stockings",
        "Strümpfe mit Naht": "Seamed stockings",
        "Strümpfe mit Strapsen": "Stockings with suspenders",
        "Overknee-Strümpfe": "Over-the-knee socks",
        "Kniestrümpfe": "Knee-high socks",
        "Söckchen": "Ankle socks", "Leggings": "Leggings",
    },
    "hosieryColor": {
        "Hautfarben": "Nude", "Beige": "Beige", "Braun": "Tan",
        "Karamell": "Caramel", "Creme": "Cream", "Weiß": "White",
        "Grau": "Grey", "Anthrazit": "Charcoal", "Schwarz": "Black",
        "Rot": "Red", "Bordeaux": "Burgundy", "Pink": "Hot pink",
        "Rosé": "Dusty rose", "Violett": "Purple", "Blau": "Navy",
        "Türkis": "Turquoise", "Grün": "Emerald", "Kupfer": "Copper",
        "Gold schimmernd": "Shimmering gold",
        "Silber schimmernd": "Shimmering silver",
    },
    "jewellery": {
        "Kleine Ohrstecker": "Small studs", "Ohrringe lang": "Drop earrings",
        "Creolen": "Hoops", "Zarte Halskette": "Delicate necklace",
        "Choker": "Choker", "Statement-Kette": "Statement necklace",
        "Ringe": "Rings", "Armreif": "Bangle", "Armband": "Bracelet",
        "Fußkettchen": "Ankle chain", "Bauchnabelpiercing": "Navel piercing",
    },
    "eyewear": {
        "Brille schmal": "Rectangular glasses", "Brille rund": "Round glasses",
        "Hornbrille": "Thick-rimmed glasses", "Lesebrille": "Reading glasses",
        "Sonnenbrille": "Sunglasses", "Pilotenbrille": "Aviators",
        "Cat-Eye-Brille": "Cat-eye glasses",
    },
    "headwear": {
        "Stirnband": "Headband", "Haarreif": "Hair band", "Mütze": "Beanie",
        "Baseballkappe": "Baseball cap", "Sonnenhut": "Sun hat",
        "Fedora": "Fedora", "Kopftuch": "Headscarf",
    },
    "shoes": {
        "Pumps spitz": "Pointed-toe pumps",
        "Pumps mandelförmig": "Almond-toe pumps",
        "Peeptoe-Pumps": "Peep-toe pumps", "Slingback-Pumps": "Slingback pumps",
        "Mary-Jane-Pumps": "Mary Jane pumps", "Lack-Pumps": "Patent pumps",
        "Wildleder-Pumps": "Suede pumps", "Stiletto High Heels": "Stiletto heels",
        "Sehr hohe Stilettos": "Very high stilettos", "Kitten Heels": "Kitten heels",
        "Blockabsatz-Pumps": "Block heel pumps", "Keilabsatz": "Wedges",
        "Plateau-Heels": "Platform heels", "Plateau-Stilettos": "Platform stilettos",
        "Extreme Plateau-Heels": "Towering platforms",
        "Lack-Plateau-Heels": "Patent platforms",
        "Riemchen-Sandaletten": "Strappy sandals",
        "Sandaletten mit Knöchelriemen": "Ankle-strap sandals",
        "Zehensteg-Sandaletten": "Thong sandals",
        "Plateau-Sandaletten": "Platform sandals",
        "Mules mit Absatz": "Heeled mules", "Pantoletten": "Heeled slides",
        "Stiefeletten mit Absatz": "Heeled ankle boots",
        "Spitze Stiletto-Stiefeletten": "Pointed stiletto booties",
        "Sock-Boots": "Sock boots", "Kniehohe Stiefel": "Knee-high boots",
        "Overknee-Stiefel": "Over-the-knee boots",
        "Overknee-Lackstiefel": "Patent thigh-highs",
        "Reitstiefel": "Riding boots", "Cowboystiefel": "Cowboy boots",
        "Combat Boots": "Combat boots", "Ballerinas": "Ballet flats",
        "Loafer": "Loafers", "Sneaker": "Sneakers", "Flip-Flops": "Flip-flops",
        "Nur Strümpfe": "Stockings only", "Nur Socken": "Socks only",
        "Barfuß": "Barefoot",
    },
    "shoesColor": {
        "Schwarz": "Black", "Weiß": "White", "Hautfarben": "Nude",
        "Beige": "Beige", "Braun": "Brown", "Cognac": "Cognac",
        "Grau": "Grey", "Rot": "Red", "Bordeaux": "Burgundy",
        "Pink": "Hot pink", "Rosé": "Dusty rose", "Violett": "Purple",
        "Blau": "Navy", "Türkis": "Turquoise", "Grün": "Emerald",
        "Gold": "Gold", "Silber": "Silver", "Kupfer": "Copper",
        "Leopardenmuster": "Leopard print", "Zebramuster": "Zebra print",
        "Durchsichtig": "Clear",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Expression
# ─────────────────────────────────────────────────────────────────────────────
AUSDRUCK = {
    "stimmung": {
        "Neutral": "Neutral", "Entspannt": "Relaxed", "Zufrieden": "Content",
        "Gelassen": "Serene", "Stoisch": "Stoic", "Unbeeindruckt": "Unimpressed",
        "Sanftes Lächeln": "Gentle smile", "Warmes Lächeln": "Warm smile",
        "Strahlend": "Beaming", "Breites Lachen": "Laughing",
        "Kichernd": "Giggling", "Fröhlich": "Joyful", "Amüsiert": "Amused",
        "Schelmisch": "Mischievous", "Verschmitzt": "Impish",
        "Erleichtert": "Relieved", "Verträumt": "Dreamy",
        "Sehnsüchtig": "Longing", "Wehmütig": "Wistful",
        "Nachdenklich": "Pensive", "Grüblerisch": "Brooding",
        "Abwesend": "Absent-minded", "Verloren": "Faraway",
        "Melancholisch": "Melancholic", "Selbstbewusst": "Confident",
        "Dominant": "Dominant", "Herrisch": "Imperious",
        "Fordernd": "Demanding", "Unnachgiebig": "Unyielding",
        "Streng": "Stern", "Ernst": "Serious", "Konzentriert": "Focused",
        "Berechnend": "Calculating", "Kühl": "Aloof", "Arrogant": "Arrogant",
        "Herablassend": "Condescending", "Spöttisch": "Mocking",
        "Verächtlich": "Contemptuous", "Triumphierend": "Triumphant",
        "Trotzig": "Defiant", "Herausfordernd": "Challenging",
        "Zärtlich": "Tender", "Hingebungsvoll": "Devoted", "Kokett": "Coy",
        "Flirtend": "Flirting", "Neckisch": "Teasing",
        "Verführerisch": "Seductive", "Lasziv": "Sultry",
        "Anzüglich": "Suggestive", "Verlangend": "Wanting",
        "Begierig": "Eager", "Erregt": "Aroused",
        "Leidenschaftlich": "Passionate", "Lustvoll": "Blissful",
        "Atemlos": "Breathless", "Überwältigt": "Overwhelmed",
        "Ekstatisch": "Ecstatic", "Unterwürfig": "Submissive",
        "Schüchtern": "Shy", "Verlegen": "Embarrassed",
        "Unschuldig": "Innocent", "Überrascht": "Surprised",
        "Erwartungsvoll": "Expectant", "Neugierig": "Curious",
        "Skeptisch": "Skeptical", "Misstrauisch": "Wary",
        "Angespannt": "Tense", "Nervös": "Nervous",
        "Erschrocken": "Startled", "Alarmiert": "Alarmed",
        "Besorgt": "Worried", "Ängstlich": "Frightened",
        "Panisch": "Panicked", "Schockiert": "Shocked",
        "Fassungslos": "Stunned", "Benommen": "Dazed", "Traurig": "Sad",
        "Den Tränen nahe": "On the verge of tears", "Weinend": "Crying",
        "Verzweifelt": "Desperate", "Untröstlich": "Inconsolable",
        "Leidend": "Pained", "Resigniert": "Resigned",
        "Erschöpft": "Exhausted", "Genervt": "Annoyed", "Bitter": "Bitter",
        "Wütend": "Angry", "Rasend": "Furious", "Angewidert": "Disgusted",
        "Gelangweilt": "Bored",
    },
    "augen": {
        "Weit geöffnet": "Wide open", "Aufgerissen": "Wide with alarm",
        "Starr": "Fixed stare", "Halb geschlossen": "Half-closed",
        "Geschlossen": "Closed", "Fest zugekniffen": "Squeezed shut",
        "Zusammengekniffen": "Narrowed", "Flackernd": "Darting",
        "Tränenfeucht": "Teary", "Verweint": "Tear-stained",
        "Nach oben verdreht": "Rolled upward", "Fester Blick": "Steady gaze",
    },
    "blick": {
        "In die Kamera": "At the camera", "An der Kamera vorbei": "Past the camera",
        "Ins Leere": "Into nothing", "Nach unten": "Down", "Nach oben": "Up",
        "Von unten herauf": "Up from beneath the brows", "Zur Seite": "To the side",
        "Über die Schulter": "Over the shoulder",
        "Zum Gegenüber": "At the other person",
    },
    "mund": {
        "Geschlossen": "Closed", "Zusammengepresst": "Pressed tight",
        "Leicht geöffnet": "Slightly parted", "Lippen gespitzt": "Pursed",
        "Unterlippe gebissen": "Biting lower lip",
        "Halbes Lächeln": "Half-smile", "Zähne sichtbar": "Showing teeth",
        "Zähne gefletscht": "Teeth bared", "Weit geöffnet": "Wide open",
        "Keuchend": "Panting", "Schreiend": "Screaming",
        "Mundwinkel herabgezogen": "Corners turned down", "Verzogen": "Twisted",
    },
    "brauen": {
        "Entspannt": "Relaxed", "Hochgezogen": "Raised",
        "Eine hochgezogen": "One raised", "Gesenkt": "Lowered",
        "Zusammengezogen": "Furrowed",
        "Hoch und zusammengezogen": "Raised and drawn together",
    },
    "kopf": {
        "Gerade": "Straight", "Leicht geneigt": "Tilted slightly",
        "Kinn angehoben": "Chin lifted", "Kinn gesenkt": "Chin lowered",
        "Gesenkt": "Bowed", "Zurückgeworfen": "Thrown back",
        "Nach vorn gebeugt": "Leaning forward",
        "Zur Seite gedreht": "Turned to the side", "Weggedreht": "Turned away",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Pose
# ─────────────────────────────────────────────────────────────────────────────
POSE = {
    "haltung": {
        "Stehend": "Standing",
        "Stehend, Gewicht auf einem Bein": "Standing, weight on one leg",
        "Angelehnt": "Leaning against a wall", "Gehend": "Walking",
        "Vorgebeugt": "Bending forward", "Sitzend": "Sitting",
        "Auf einem Stuhl sitzend": "Sitting on a chair",
        "Auf einem Hocker sitzend": "Sitting on a stool",
        "Auf einer Tischkante sitzend": "Sitting on a table edge",
        "Auf dem Boden sitzend": "Sitting on the floor",
        "Zurückgelehnt": "Reclining", "Kniend": "Kneeling",
        "Auf einem Knie": "On one knee", "Hockend": "Squatting",
        "Auf allen Vieren": "On all fours",
        "Auf dem Rücken liegend": "Lying on the back",
        "Auf dem Bauch liegend": "Lying on the stomach",
        "Auf der Seite liegend": "Lying on one side",
    },
    "raum": {
        "Vordergrund": "Foreground", "Bildmitte": "Middle ground",
        "Hintergrund": "Background", "Tief im Raum": "Deep in the room",
        "Am Fenster": "By the window", "Im Türrahmen": "In a doorway",
        "An der Wand": "Against the far wall",
        "An der Raumkante": "To one side of the room",
        "Zwischen Möbeln": "Among the furniture",
        "Gehend durch den Raum": "Moving through the room",
    },
    "koerper": {
        "Frontal zur Kamera": "Facing the camera",
        "Leicht zur Seite gedreht": "Turned slightly",
        "Dreiviertelansicht": "Three-quarter view", "Im Profil": "In profile",
        "Von hinten": "From behind",
        "Über die Schulter gedreht": "Looking back over the shoulder",
    },
    "arme": {
        "Hinter dem Rücken": "Behind the back",
        "Hinter dem Rücken, Handgelenke gekreuzt": "Behind the back, wrists crossed",
        "Hinter dem Kopf": "Behind the head",
        "Über dem Kopf gestreckt": "Stretched overhead",
        "Vor der Brust verschränkt": "Crossed in front",
        "Seitlich hängend": "Hanging at the sides",
        "Hände auf den Hüften": "Hands on hips",
        "Hände im Schoß": "Hands in the lap",
        "Hände auf den Knien": "Hands on the knees",
        "Hinter sich abgestützt": "Propped up behind",
        "Auf die Unterarme gestützt": "Leaning on the forearms",
        "Eine Hand am Gesicht": "One hand at the face",
        "Eine Hand im Haar": "One hand in the hair",
        "Arme umschlingen die Knie": "Wrapped around the knees",
    },
    "beine": {
        "Geschlossen": "Closed together", "Leicht geöffnet": "Slightly apart",
        "Weit gespreizt": "Spread wide", "Übereinandergeschlagen": "Crossed",
        "Knöchel gekreuzt": "Ankles crossed", "Angewinkelt": "Knees drawn up",
        "Ein Knie angewinkelt": "One knee bent", "Ausgestreckt": "Stretched out",
        "Knie zusammen, Füße auseinander": "Knees together, feet apart",
        "Untergeschlagen": "Tucked underneath",
    },
    "spannung": {
        "Aufrecht": "Upright", "Schultern zurück": "Shoulders back",
        "Rücken durchgedrückt": "Back arched", "Entspannt": "Relaxed",
        "Angespannt": "Tense", "Zusammengesunken": "Slumped",
        "Zusammengekauert": "Curled up",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Photoshoot
# ─────────────────────────────────────────────────────────────────────────────
SHOOTING = {
    "kamera": {
        "Detail": "Extreme close-up", "Nahaufnahme": "Close-up",
        "Porträt": "Portrait", "Halbtotale": "Medium shot",
        "Amerikanisch": "Cowboy shot", "Ganzkörper": "Full body",
        "Totale": "Wide shot",
    },
    "fokus": {
        "Gesicht": "Face", "Augen": "Eyes", "Lippen": "Lips",
        "Oberkörper": "Upper body", "Dekolleté": "Neckline", "Hände": "Hands",
        "Taille": "Waist", "Beine": "Legs", "Füße": "Feet",
        "Rücken": "Back", "Ganze Figur": "Whole figure", "Raum": "Environment",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Field labels, tabs, families
# ─────────────────────────────────────────────────────────────────────────────
FELDNAMEN = {
    "Geschlecht": "Gender", "Typ": "Type", "Alter": "Age", "genaues Alter": "exact age",
    "Herkunft": "Origin", "Hautton": "Skin tone", "Größe": "Height",
    "Figur": "Figure", "Büste": "Bust", "Frisur": "Hair", "Haarfarbe": "Colour",
    "Augen": "Eyes", "Wimpern": "Lashes", "Teint": "Complexion",
    "Schultern": "Shoulders", "Taille": "Waist", "Bauch": "Stomach",
    "Hüfte": "Hips", "Beine": "Legs", "Strähnen": "Highlights",
    "Kinn": "Chin", "Kieferlinie": "Jawline", "Eyeliner": "Eyeliner",
    "Lidschatten": "Eyeshadow", "Rouge": "Blush", "Strümpfe": "Hosiery",
    "Strumpffarbe": "Colour", "Schmuck": "Jewellery", "Brille": "Eyewear",
    "Kopfbedeckung": "Headwear", "Gesichtsform": "Face shape",
    "Wangenknochen": "Cheekbones", "Nase": "Nose", "Augenform": "Eye shape",
    "Brauenform": "Brows", "Lippenform": "Lip shape", "Lippen": "Lips",
    "Finish": "Finish", "Make-up": "Make-up", "Hautmerkmale": "Skin features",
    "Nägel": "Nails", "Nagelfarbe": "Colour", "Schuhe": "Shoes",
    "Schuhfarbe": "Colour", "Details": "Details",
}

SEKTIONEN = {
    "Grund": "Basics", "Körper": "Body", "Kopf": "Head", "Gesicht": "Face",
    "Make-up": "Make-up", "Kleidung": "Clothing",
}

FAMILIEN = {
    # Shoes
    "Pumps": "Pumps", "Absätze": "Heels", "Sandaletten": "Sandals",
    "Stiefel": "Boots", "flach": "flat", "ohne": "none",
    # Posture
    "stehend": "standing", "sitzend": "sitting", "kniend": "kneeling",
    "liegend": "lying",
    # Mood
    "ruhig": "calm", "freundlich": "friendly", "in sich gekehrt": "introspective",
    "bestimmend": "assertive", "zugewandt": "engaged", "wachsam": "alert",
    "verängstigt": "frightened", "traurig": "sad", "abweisend": "dismissive",
}

# Category names as they appear above the option lists. The key is the internal
# category name - it is German and is shown directly in the panel.
KATEGORIEN = {
    # Pose
    "haltung": "posture", "raum": "placement", "koerper": "body",
    "arme": "arms", "beine": "legs", "spannung": "tension",
    # Expression
    "stimmung": "mood", "augen": "eyes", "blick": "gaze", "mund": "mouth",
    "brauen": "brows", "kopf": "head",
    # Photoshoot
    "kamera": "camera", "fokus": "focus", "format": "ratio",
    "ausdruck": "expression", "pose": "pose", "rausch": "noise",
}

PLATZHALTER = {
    "genaues Alter, z. B. 34 (schlägt den Bereich)":
        "exact age, e.g. 34 (overrides the range)",
    "genaues Alter, z. B. 34 (schlägt den Bereich, ab 18)":
        "exact age, e.g. 34 (overrides the range, 18 and up)",
    "Weitere Details (englisch), z. B. wearing a red raincoat":
        "further details, e.g. wearing a red raincoat",
    "Name, z. B. Bibliothek abends": "Name, e.g. library at night",
    "Text fuer diesen Baustein": "Text for this block",
}

# ─────────────────────────────────────────────────────────────────────────────
# Strings used by the interfaces (js/). The key is the German text.
# ─────────────────────────────────────────────────────────────────────────────
UI = {
    # Shared
    "alle": "all",
    "Alle": "All",
    "gewürfelt": "rolled",
    "nichts gewählt": "nothing selected",
    "fest — klicken zum Würfeln": "fixed — click to roll",
    "Nochmal klicken bestätigt": "Click again to confirm",
    "Klicken wählt alle ab": "Click to deselect all",
    "Zurücksetzen": "Reset",
    "Alle Felder des Nodes zurücksetzen": "Reset every field of this node",
    "Vorschau": "Preview",
    "Würfeln": "Roll",
    "Details": "Details",
    "wird gewürfelt": "is rolled",
    "wird gewürfelt — klicken für fest": "rolled — click to fix",
    "Weiteres (englisch)": "Anything else (English)",

    # Person Builder: labels, tabs, reset
    "Klicken setzt dieses Feld zurück": "Click to reset this field",
    "Klicken setzt diese Felder zurück": "Click to reset these fields",
    "Klicken leert dieses Feld": "Click to clear this field",
    "nichts gesetzt": "nothing set",
    "{0} Feld gesetzt": "{0} field set",
    "{0} Felder gesetzt": "{0} fields set",
    "Die {0} gesetzten Felder dieser Karte zurücksetzen":
        "Reset the {0} fields set on this tab",
    "wirklich alle {0} löschen?": "really clear all {0}?",
    "alles": "everything",

    # Photoshoot: header, axes, states
    "Fotos": "Photos",
    "Shooting starten": "Start shooting",
    "ca. ": "approx. ",
    "Anderen Schauplatz suchen": "Look for a different setting",
    "Kamera": "Camera", "Pose": "Pose", "Ausdruck": "Expression",
    "Schwerpunkt": "Focus", "Format": "Ratio", "Rauschen": "Noise",
    "fest": "fixed", "aus": "off", "keiner passt": "none fits",
    "pro Foto": "per photo", "Seed {0}": "seed {0}",
    "{0} von {1}": "{0} of {1}",
    "An: jedes Foto bekommt eigenes Rauschen. Aus: die ganze Serie ":
        "On: every photo gets its own noise. Off: the whole series ",
    "⚠ width/height liegen an, werden aber ignoriert — Format ausschalten":
        "⚠ width/height are wired but ignored — switch the ratio axis off",
    "— es kommt gar kein Schwerpunkt in den Prompt":
        "— no focus reaches the prompt at all",
    "Der Schwerpunkt ist an die Kameraeinstellung gekoppelt. Entweder ":
        "The focus is coupled to the framing. Either ",
    "von außen — Wert erst beim Ausführen bekannt":
        "external — value only known at run time",
    "width_in und height_in liegen an und haben Vorrang. Die eigene ":
        "width_in and height_in are wired and take precedence. The node's own ",
    "Kameraeinstellung, nicht von hier.": "framing, not from here.",
    "…  bis {0}": "…  up to {0}",
    # Short form of the person detail level in the preview. Two letters,
    # because in English "full" and "figure" start with the same one.
    "Vo": "Fu", "Fi": "Fi", "Id": "Id",
    "Detailstufe voll": "person: full detail",
    "Detailstufe Figur": "person: figure only",
    "Detailstufe Identität": "person: identity only",

    # Person Builder
    "Gesichtsfelder": "face fields",
    "für weite Einstellungen reichen vier bis fünf":
        "four or five is enough for wide framings",
    "bei Ganzkörper und Totale kippt die Komposition, der Kopf wird zu groß":
        "with full body and wide shots the composition tips over, the head grows too large",
    "Bildmodelle verteilen die Bildfläche ungefähr nach der Gewichtung im ":
        "Image models allocate frame area roughly by the weighting in the ",
    "Prompt. Viele Gesichtsangaben überstimmen den Hinweis auf die ":
        "prompt. Many face details override the hint about ",
    "Proportionen. Für Porträts und Nahaufnahmen ist es unkritisch.":
        "proportions. For portraits and close-ups it is uncritical.",

    # Photoshoot
    "Durchläufe einreihen": "runs queued",
    "Kameraeinstellung über die Serie variieren": "Vary the framing across the series",
    "Körperhaltung variieren. Aufgeklappt: auf eine Familie einschränken.":
        "Vary the posture. Expanded: restrict to one family.",
    "Mimik variieren. Aufgeklappt: auf eine Stimmungsfamilie einschränken.":
        "Vary the expression. Expanded: restrict to one mood family.",
    "Bildschwerpunkt variieren (Gesicht, Beine, Füße …). Welche ":
        "Vary the focus (face, legs, feet …). Which are ",
    "möglich sind, hängt von den gewählten Kameraeinstellungen ab.":
        "possible depends on the chosen framings.",
    "Schwerpunkt. Die durchgestrichenen Einträge sind die, die mit den ":
        "Focus. The struck-through entries are those that cannot occur with the ",
    "aktuellen Einstellungen nicht vorkommen können.":
        "current framings.",
    "Nicht schlimm - die übrigen Schwerpunkte greifen weiterhin.":
        "Not a problem — the remaining focus entries still apply.",
    "eine passende Einstellung dazuwählen oder einen anderen ":
        "add a matching framing or pick a different ",
    "passt zu keiner gewählten Einstellung": "matches none of the chosen framings",
    "kommt mit den gewählten Einstellungen nicht vor":
        "does not occur with the chosen framings",
    " — passt zu keiner der gewählten Kameraeinstellungen":
        " — matches none of the chosen framings",
    "An: Seitenverhältnis passend zur Kameraeinstellung würfeln. ":
        "On: roll an aspect ratio matching the framing. ",
    "Aus: ein festes Verhältnis für alle Fotos.":
        "Off: one fixed ratio for every photo.",
    "Größe": "Size",
    "Kantenlänge im Quadrat. Das Seitenverhältnis kommt von der ":
        "Edge length as a square. The aspect ratio comes from the ",
    "Größenstufe wirkt erst wieder, wenn dort nichts angeschlossen ist ":
        "The size step applies again once nothing is wired there ",
    "oder das Format gewürfelt wird.": "or the ratio is rolled.",
    "von außen": "external",
    "Das Rauschen hat Bildmaße. Ändert sich das Seitenverhältnis, ist es ":
        "Noise has image dimensions. If the aspect ratio changes it is ",
    "teilt einen Seed, dann bleibt der Schauplatz über die Fotos gleich.":
        "shares one seed, which keeps the setting the same across photos.",
    "Format würfelt — bei wechselnder Größe wirkt der Serien-Seed nicht":
        "Ratio is rolling — with changing size the series seed has no effect",
    "s je Bild, gemessen an den letzten Läufen":
        "s per image, measured from recent runs",
}


# ─────────────────────────────────────────────────────────────────────────────
# Delivery
# ─────────────────────────────────────────────────────────────────────────────
def tabelle():
    """Everything the interface needs in order to translate.

    The shape mirrors the presets: one dict per building block, from category
    to {German label: English display label}. The interface looks up with the
    same category it drew the list with.
    """
    return {
        "person": PERSON,
        "ausdruck": AUSDRUCK,
        "pose": POSE,
        "shooting": SHOOTING,
        "feldnamen": FELDNAMEN,
        "sektionen": SEKTIONEN,
        "familien": FAMILIEN,
        "kategorien": KATEGORIEN,
        "platzhalter": PLATZHALTER,
        "ui": UI,
    }


def fehlend(presets_modul_paare):
    """Labels with no translation - for tests/smoke.py.

    presets_modul_paare: [(key, module), ...] as in tabelle().
    """
    luecken = []
    for schluessel, modul in presets_modul_paare:
        tab = tabelle().get(schluessel) or {}
        for cat, eintraege in modul.PRESETS.items():
            haben = tab.get(cat) or {}
            for lbl, _ in eintraege:
                if lbl not in haben:
                    luecken.append("%s/%s/%s" % (schluessel, cat, lbl))
    return luecken
