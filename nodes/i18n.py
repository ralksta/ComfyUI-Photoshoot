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
        "Gebräunt": "Tan", "Oliv": "Olive", "Bronze": "Bronze", "Braun": "Brown",
        "Dunkelbraun": "Deep brown", "Ebenholz": "Deep ebony",
    },
    "complexion": {
        "Dewy": "Dewy", "Matt": "Matte", "Porzellan": "Porcelain",
        "Glas-Haut": "Glass skin", "Geölt / Wet-Glow": "Oiled wet-glow",
        "Natürliche Poren": "Natural pores", "Sonnengegerbt": "Weathered",
        "Rötlich": "Rosy", "Blass": "Pale",
    },
    "height": {
        "Klein": "Short", "Zierlich": "Petite",
        "Durchschnittlich": "Average", "Groß": "Tall",
        "Model-Größe": "Model height",
    },
    "figure": {
        "Sehr schlank": "Very slim", "Schlank": "Slim", "Schlank definiert": "Lean toned",
        "Athletisch": "Athletic", "Durchschnittlich": "Average", "Kurvig": "Curvy",
        "Sanduhr": "Hourglass", "Birnenform": "Pear-shaped",
        "Mollig": "Chubby", "Plus-Size": "Plus-size", "Stämmig": "Stocky",
        "Muskulös": "Muscular",
    },
    "bust": {
        "Klein": "Small", "Mittel": "Medium", "Voll": "Full", "Groß": "Large",
        "Sehr groß": "Very large", "Sehr groß (Kontrast)": "Very large (contrast)",
        "Massiv / Stacked": "Massive / Stacked", "Extrem": "Extreme",
    },

    "shoulders": {
        "Schmal": "Narrow", "Zierlich": "Delicate", "Gerade": "Squared",
        "Breit": "Broad", "Sportlich": "Athletic",
    },
    "waist": {
        "Sehr schmal": "Very narrow", "Schmal": "Slim",
        "Wespentaille": "Corset waist", "Definiert": "Defined",
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
        "Locken": "Curls", "Afro": "Afro", "Braids / Zöpfe": "Box braids",
        "Pony": "Bangs", "Curtain Bangs": "Curtain bangs",
        "Wolf Cut / Stufenschnitt": "Wolf cut", "Half-up": "Half-up",
        "Sleek zurück": "Sleek back", "Wet-Look": "Wet-look",
        "Space Buns": "Space buns", "Kurz wellig": "Short tousled",
        "Buzzcut / Abrasur": "Buzzcut", "Undercut": "Undercut",
        "Langes Haar mit Pony": "Long with blunt bangs", "Seitenpony": "Side-swept bangs",
        "Wispy Bangs": "Wispy bangs", "Baby Bangs": "Baby bangs",
        "Locken mit Pony": "Curly bangs", "Bob mit Pony": "Bob with bangs",
        "Fransiger Kurzhaarschnitt": "Choppy bangs",
    },
    "hairColor": {
        "Blond": "Blonde", "Platinblond": "Platinum blonde",
        "Dunkelblond": "Dark blonde", "Braun": "Brown",
        "Dunkelbraun": "Dark brown", "Schwarz": "Black",
        "Rot / Kupfer": "Copper red", "Kastanie": "Auburn",
        "Erdbeerblond": "Strawberry blonde", "Grau / Silber": "Silver grey",
        "Eisweiß": "Icy white", "Pastellrosa": "Pastel pink",
        "Mitternachtsblau": "Midnight blue", "Smaragdgrün": "Emerald green",
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
        "Monolid": "Monolid", "Schlupflider": "Hooded", "Tief liegend": "Deep-set",
        "Weit auseinander": "Wide-set", "Katzenaugen": "Upturned",
    },
    "lipShape": {
        "Voll": "Full", "Schmal": "Thin", "Schmollmund": "Pouty",
        "Breit": "Wide", "Amorbogen": "Cupid's bow", "Volle Unterlippe": "Fuller lower lip",
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
        "Schmal": "Thin", "Dicht": "Thick", "Soap Brows": "Soap brows",
        "Gerade": "Straight", "Geschwungen": "Arched", "Buschig": "Bushy",
        "Bleached": "Bleached",
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
        "Ohne": "None", "Natürlich": "Natural", "Clean Girl": "Clean girl",
        "Dezent": "Subtle", "Glam": "Glam", "Smokey Eyes": "Smokey eyes",
        "Gothic / Dark Grunge": "Gothic grunge", "90s Vintage": "90s vintage",
        "Editorial": "Editorial",
    },
    "skinFeatures": {
        "Sommersprossen": "Freckles", "Blasse Haut": "Pale skin",
        "Schönheitsfleck": "Beauty mark", "Grübchen": "Dimples",
        "Muttermale": "Moles", "Tattoos": "Tattoos", "Piercings": "Piercings",
        "Sommerbräune": "Sun-kissed", "Vitiligo": "Vitiligo",
        "Feine Narbe": "Delicate scar", "Nasenring / Septum": "Septum ring",
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
        "Punkte-Strumpfhose": "Polka dot tights",
        "Spitzen-Strumpfhose": "Floral lace tights",
        "Netzstrumpfhose": "Fishnet tights",
        "Netzstrumpfhose grob": "Wide-mesh fishnets",
        "Netzstrümpfe mit Naht": "Seamed fishnets with garters",
        "Halterlose Strümpfe": "Hold-up stockings",
        "Strümpfe mit Naht": "Seamed stockings",
        "Strümpfe mit Strapsen": "Stockings with suspenders",
        "Cage-Strapsgürtel": "Cage garter belt",
        "Latex-Strümpfe": "Latex stockings",
        "Overknee-Strümpfe": "Over-the-knee socks",
        "Kniestrümpfe": "Knee-high socks",
        "Söckchen": "Ankle socks", "Leggings": "Leggings",
        "Lack-Leggings": "Wet-look leggings",
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
        "Perlenkette": "Pearl necklace", "Choker": "Choker",
        "Leder-Choker mit O-Ring": "Leather O-ring choker",
        "Leder-Choker mit Kette": "Leather leash collar",
        "Leder-Armfesseln": "Leather wrist cuffs",
        "Brust-Harness (Leder)": "Chest leather harness",
        "Schenkel-Harness (Leder)": "Thigh garter harness",
        "Lange Lederhandschuhe": "Leather opera gloves",
        "Lange Latex-Handschuhe": "Latex opera gloves",
        "Reitgerte in Hand": "Riding crop in hand",
        "Statement-Kette": "Statement necklace",
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
        "Baseballkappe": "Baseball cap", "Barett": "Beret",
        "Sonnenhut": "Sun hat", "Cowboyhut": "Cowboy hat",
        "Fedora": "Fedora", "Kopftuch": "Headscarf",
        "Lack-Schirmmütze (Domina)": "Patent officer cap",
        "Leder-Hasenmaske": "Leather bunny mask",
        "Leder-Katzenmaske": "Leather cat mask",
        "Augenbinde": "Blindfold",
        "Glockenhut": "Cloche", "Fischerhut": "Bucket hat", "Zylinder": "Top hat",
        "Schiebermütze": "Newsboy cap", "Pillbox mit Schleier": "Pillbox with veil",
        "Fascinator": "Fascinator", "Panamahut": "Panama hat", "Melone": "Bowler",
        "Kreissäge": "Boater", "Schlapphut": "Floppy hat", "Wagenradhut": "Cartwheel hat",
        "Matrosenmütze": "Sailor hat", "Weiße Kapitänsmütze": "White captain's hat",
        "Elbsegler": "Fisherman cap", "Uschanka": "Trapper hat", "Visor": "Visor",
    },
    "prop": {
        "Kaffeetasse": "Coffee mug",
        "Buch in der Hand": "Open book",
        "Weinglas": "Wine glass",
        "Blumenstrauß": "Flower bouquet",
    },
    "shoes": {
        "Pumps spitz": "Pointed-toe pumps",
        "Pumps mandelförmig": "Almond-toe pumps",
        "Peeptoe-Pumps": "Peep-toe pumps", "Slingback-Pumps": "Slingback pumps",
        "Mary-Jane-Pumps": "Mary Jane pumps", "Lack-Pumps": "Patent pumps",
        "Wildleder-Pumps": "Suede pumps",
        "Transparent-Pumps (Perspex)": "Clear perspex pumps",
        "Stiletto High Heels": "Stiletto heels",
        "Sehr hohe Stilettos": "Very high stilettos", "Kitten Heels": "Kitten heels",
        "Blockabsatz-Pumps": "Block heel pumps", "Keilabsatz": "Wedges",
        "Plateau-Heels": "Platform heels", "Plateau-Stilettos": "Platform stilettos",
        "Extreme Plateau-Heels": "Towering platforms",
        "Lack-Plateau-Heels": "Patent platforms",
        "Clogs mit Holzsohle": "Wooden clogs",
        "Riemchen-Sandaletten": "Strappy sandals",
        "Sandaletten mit Knöchelriemen": "Ankle-strap sandals",
        "Schnür-Sandaletten (Wrap-Up)": "Lace-up wrap sandals",
        "Zehensteg-Sandaletten": "Thong sandals",
        "Plateau-Sandaletten": "Platform sandals",
        "Mules mit Absatz": "Heeled mules", "Pantoletten": "Heeled slides",
        "Espadrilles mit Keilabsatz": "Wedge espadrilles",
        "Stiefeletten mit Absatz": "Heeled ankle boots",
        "Spitze Stiletto-Stiefeletten": "Pointed stiletto booties",
        "Schnür-Stiefeletten": "Lace-up ankle boots",
        "Sock-Boots": "Sock boots", "Kniehohe Stiefel": "Knee-high boots",
        "Overknee-Stiefel": "Over-the-knee boots",
        "Overknee-Lackstiefel": "Patent thigh-highs",
        "Reitstiefel": "Riding boots", "Cowboystiefel": "Cowboy boots",
        "Combat Boots": "Combat boots",
        "Spitzenschuhe (Ballett)": "Ballet pointe shoes",
        "Ballettschläppchen": "Ballet slippers",
        "Gymnastikschuhe": "Gymnastics shoes",
        "Latein-Tanzschuhe": "Latin dance heels",
        "Jazzschuhe": "Jazz shoes",
        "Schlittschuhe (Eiskunstlauf)": "Figure ice skates",
        "Rollschuhe (Quad Skates)": "Quad roller skates",
        "Laufschuhe": "Running shoes",
        "Wanderschuhe": "Hiking boots",
        "Ballet Heels (Extrem)": "Ballet heels (extreme)",
        "Absatzlose Heels (Heelless)": "Heelless shoes",
        "Schritthohe Lackstiefel": "Crotch-high patent boots",
        "Huf-Heels (Hoof Boots)": "Hoof boots",
        "Korsett-Schnürstiefel": "Corset lace-up boots",
        "Latex-Overknees": "Latex thigh-highs",
        "Metall-Stilettos (Pin Heels)": "Pin heel stilettos",
        "Pole-Dance-Plateaus (8-Inch)": "8-inch pole platforms",
        "Bondage-Fessel-Sandaletten": "Bondage ankle heels",
        "Lack-Domina-Pumps": "Patent domina pumps",
        "Ballerinas": "Ballet flats",
        "Flache Riemchensandalen": "Flat strappy sandals",
        "Gladiator-Sandalen": "Gladiator sandals",
        "Espadrilles": "Flat espadrilles",
        "Loafer": "Loafers", "Sneaker": "Sneakers",
        "Chunky Sneaker": "Chunky sneakers", "Flip-Flops": "Flip-flops",
        "Nur Strümpfe": "Stockings only", "Nur Socken": "Socks only",
        "Barfuß": "Barefoot",
        "Knöchelriemen-Pumps": "Ankle-strap pumps",
        "D'Orsay-Pumps": "D'Orsay pumps",
        "Oxford mit Absatz": "Heeled oxfords",
        "T-Strap-Plateaus": "T-strap platforms",
        "Chelsea Boots": "Chelsea boots",
        "D'Orsay-Ballerinas": "D'Orsay flats",
    },
    "top": {
        "Basic Crop Top": "Basic crop top",
        "Puffärmel-Crop-Top": "Puff sleeve crop",
        "Wickel-Crop-Top": "Wrap crop top",
        "Wickel-Crop-Top langärmelig": "Long sleeve wrap crop",
        "Geripptes Crop Top": "Ribbed crop top",
        "Crop Top mit Knopfleiste": "Button-up crop",
        "Off-Shoulder-Crop-Top": "Off-shoulder crop",
        "Bustier-Crop-Top (Spaghettiträger)": "Strappy crop top",
        "Neckholder-Crop-Top": "Halter crop top",
        "Crop Top mit Knoten vorn": "Tie-front crop",
        "Crop Top mit Karree-Ausschnitt": "Square neck crop",
        "One-Shoulder-Crop-Top": "One-shoulder crop",
        "Peplum-Top": "Peplum top",
        "Korsett-Top mit Puffärmeln": "Corset top",
        "Milkmaid-Top": "Milkmaid top",
        "Bustier-Top mit Schleife": "Bustier top",
        "Bardot-Top": "Bardot top",
        "Lochstickerei-Wickelbluse": "Eyelet wrap blouse",
        "Top mit tiefem V-Ausschnitt": "Plunging V-neck",
        "Top mit Herzausschnitt": "Sweetheart neckline",
        "Top mit Schlüsselloch": "Keyhole neckline",
        "Ärmelloser Rollkragen": "Sleeveless turtleneck",
        "Top mit Wasserfallausschnitt": "Cowl neckline",
        "Top mit Schnürausschnitt": "Lace-up neckline",
        "U-Boot-Top mit Cutout": "Boat neck cutout",
        "Stehkragen-Top mit Reißverschluss": "Zip-up high collar",
        "Top mit Illusion-Passe": "Illusion neckline",
        "Triangel-Bikini": "Triangle bikini",
        "Bandeau-Bikini": "Bandeau bikini",
        "Bügel-Bikini": "Underwire bikini",
        "Sport-Bikini": "Sports bikini",
        "High-Neck-Bikini": "High-neck bikini",
        "One-Shoulder-Bikini": "One-shoulder bikini",
        "Volant-Bikini": "Flounce bikini",
        "Criss-Cross-Bikini": "Criss-cross bikini",
        "Fransen-Bikini": "Fringe bikini",
        "Bandeau-Bikini mit Schleife": "Bow bandeau bikini",
        "Tankini": "Tankini",
    },
    "topColor": {
        "Schwarz": "Black",
        "Weiß": "White",
        "Creme": "Cream",
        "Beige": "Beige",
        "Grau": "Grey",
        "Rot": "Red",
        "Bordeaux": "Burgundy",
        "Pink": "Hot pink",
        "Rosé": "Dusty rose",
        "Pastellrosa": "Pastel pink",
        "Violett": "Purple",
        "Pastellblau": "Pastel blue",
        "Blau": "Navy",
        "Türkis": "Turquoise",
        "Mint": "Mint",
        "Grün": "Emerald",
        "Gelb": "Yellow",
        "Gold": "Gold",
        "Silber": "Silver",
        "Leopardenmuster": "Leopard print",
    },
    "bottom": {
        "Minirock": "Mini skirt",
        "Bleistiftrock knielang": "Pencil skirt",
        "Faltenrock mini": "Pleated mini skirt",
        "Plisseerock midi": "Pleated midi skirt",
        "Maxirock mit Beinschlitz": "Slit maxi skirt",
        "Wickelrock mini": "Wrap mini skirt",
        "Jeans-Shorts": "Denim shorts",
        "Hotpants": "Hot pants",
        "Skinny Jeans": "Skinny jeans",
        "Weite Hose": "Wide-leg trousers",
        "Leder-Leggings": "Leather leggings",
        "Cargohose": "Cargo pants",
        "Micro-Minirock": "Micro mini skirt",
        "Skater-Minirock": "Skater skirt",
        "Bleistiftrock mit Schlitz vorn": "Front-slit pencil skirt",
        "Maxirock mit zwei Schlitzen": "Double-slit maxi skirt",
        "High-Low-Rock": "High-low skirt",
        "Midirock im Schrägschnitt": "Bias-cut midi skirt",
        "Tüllrock kurz": "Short tulle skirt",
        "Korsettrock": "Corset skirt",
        "Fransenrock (Latein)": "Fringe skirt (Latin)",
        "Tennisrock": "Tennis skirt",
        "Hosenrock (Skort)": "Skort",
        "Radlerhose": "Bike shorts",
        "Hotpants high-cut": "High-cut hot pants",
        "Booty Shorts": "Booty shorts",
        "Palazzohose mit Schlitzen": "Slit palazzo trousers",
        "Leggings mit Schnürung": "Lace-up leggings",
        "Flare-Leggings": "Flared leggings",
        "Bikinihöschen": "Bikini bottom",
        "String-Bikinihöschen": "String bikini bottom",
        "High-Cut-Bikinihöschen": "High-cut bikini bottom",
        "High-Waist-Bikinihöschen": "High-waisted bikini bottom",
        "Bikinihöschen mit Umschlagbund": "Fold-over bikini bottom",
        "Bikinihöschen mit Röckchen": "Skirted bikini bottom",
        "Bikinihöschen mit Gürtel": "Belted bikini bottom",
        "Stufen-Volantrock": "Tiered ruffle skirt", "Asymmetrischer Volantrock": "Asymmetric ruffle skirt",
        "Schnürrock mit Petticoat": "Lace-up skirt with petticoat",
        "Rock mit Seitenschleife": "Side-bow skirt", "Volant-Überrock": "Ruffled overskirt",
    },
    "bottomMaterial": {
        "Latex": "Latex",
        "Lack": "Patent",
        "Leder": "Leather",
        "Wetlook": "Wet-look",
        "PVC transparent": "Clear PVC",
        "Seide": "Silk",
        "Satin": "Satin",
        "Samt": "Velvet",
        "Chiffon": "Chiffon",
        "Tüll": "Tulle",
        "Denim": "Denim",
        "Pailletten": "Sequins",
        "Spitze": "Lace",
        "Netz": "Mesh",
        "Metallic": "Metallic",
        "Tweed": "Tweed",
        "Cord": "Corduroy",
    },
    "bottomColor": {
        "Schwarz": "Black",
        "Weiß": "White",
        "Creme": "Cream",
        "Beige": "Beige",
        "Grau": "Grey",
        "Rot": "Red",
        "Bordeaux": "Burgundy",
        "Pink": "Hot pink",
        "Rosé": "Dusty rose",
        "Pastellrosa": "Pastel pink",
        "Violett": "Purple",
        "Pastellblau": "Pastel blue",
        "Blau": "Navy",
        "Türkis": "Turquoise",
        "Mint": "Mint",
        "Grün": "Emerald",
        "Gelb": "Yellow",
        "Gold": "Gold",
        "Silber": "Silver",
        "Leopardenmuster": "Leopard print",
        "Jeansblau": "Denim blue",
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
        "Skeptisch": "Skeptical", "Misstrauisch": "Wary", "Verwirrt": "Confused",
        "Einladend": "Inviting", "Entschlossen": "Determined", "Verliebt": "Smitten",
        "Kusshand": "Blowing a kiss",
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
        "Strecken": "Stretching", "In der Drehung": "Turning mid-motion",
        "Seitlich auf dem Boden": "Sitting sideways on the floor",
        "Bauchlage, Kinn in den Händen": "On the stomach, chin in the hands",
        "Im Schneidersitz": "Cross-legged", "Fersensitz": "Sitting on the heels",
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
        "Peace-Zeichen": "Peace sign",
        "Kaffeetasse": "Coffee mug",
        "Buch in der Hand": "Open book",
        "Weinglas": "Wine glass",
        "Blumenstrauß": "Flower bouquet",
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
    "perspektive": {
        "Selfie von oben": "Selfie from above", "Selfie auf Augenhöhe": "Eye-level selfie",
        "Selfie im Liegen": "Selfie lying down", "Spiegel-Selfie": "Mirror selfie",
        "Selfie über die Schulter": "Over-the-shoulder selfie",
        "Froschperspektive": "Low angle", "Von oben": "High angle",
        "Vogelperspektive": "Overhead bird's-eye", "Dutch Angle": "Dutch angle",
    },
    "paarInteraktionen": {
        "Nebeneinander stehend": "Standing side by side",
        "Arm in Arm gehend": "Walking arm in arm",
        "Einander zugewandt": "Facing each other",
        "Rücken an Rücken": "Back to back",
        "Arm um die Schulter": "Arm around shoulder",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Lighting
# ─────────────────────────────────────────────────────────────────────────────
LIGHTING = {
    "setup": {
        "Softbox diffuses Licht": "Softbox diffused light",
        "Rembrandt-Licht": "Rembrandt lighting",
        "Beauty Dish": "Beauty dish",
        "90s Direct Flash": "90s direct flash",
        "Split-Lighting": "Split lighting",
        "Butterfly / Paramount": "Butterfly / Paramount",
        "High-Key Studio": "High-key studio",
        "Low-Key Moody": "Low-key moody",
        "Studio-Ringlicht": "Studio ring light",
        "Von oben / Top Light": "Top light / Overhead",
        "Golden Hour": "Golden hour",
        "Blue Hour / Dämmerung": "Blue hour / Twilight",
        "Cinematic Fensterlicht": "Cinematic window light",
        "Bewölktes Tageslicht": "Overcast daylight",
        "Hartes Sonnenlicht": "Direct harsh sunlight",
        "Sonnenuntergang / Abendrot": "Sunset glow",
        "Schattenspiel / Blätter": "Dappled sunlight",
        "Morgendämmerung": "Morning dawn",
        "Neon Akzente": "Neon accents",
        "Jalousie-Schatten (Gobo)": "Venetian blind gobo",
        "Laser-Grid (Sci-Fi)": "Laser grid",
        "Flammenschein / Kaminlicht": "Firelight glow",
        "Kerzenlicht / Warmes Glühen": "Candlelight / Warm glow",
        "Blaulicht / Sirenen-Schimmer": "Emergency siren rim",
        "Wasser-Kaustik (Projektion)": "Water caustics projection",
        "Volumetrische Lichtstrahlen": "Volumetric god rays",
        "Dramatisches Chiaroscuro": "Dramatic chiaroscuro",
        "Mondlicht (Nacht)": "Moonlight night",
        "Prisma / Farbregen": "Prism refraction",
        "Film Noir Schatten": "Film noir shadows",
    },
    "richtung": {
        "Frontal 45°": "Frontal 45°",
        "Streiflicht / Rim Light": "Rim light / Silhouette",
        "Gegenlicht": "Backlit",
        "Seitliches Streiflicht": "Side raking light",
        "Dezentes Aufhelllicht": "Subtle fill light",
        "Von oben / Top Light": "Top light / Overhead",
    },
    "atmosphaere": {
        "Volumetrischer Dunst": "Volumetric haze",
        "Klar & gestochen scharf": "Crystal clear & sharp",
        "Warmer Film-Glow": "Warm film glow",
        "Kühle Farbtiefe": "Cool cinematic grading",
        "Traumhaftes Bokeh": "Dreamy bokeh",
    },
}

STYLE = {
    "look": {
        "Schwarzweiß klassisch": "Black & white classic",
        "Schwarzweiß kontrastreich": "Black & white high contrast",
        "Schwarzweiß Film Noir": "Black & white film noir",
        "Schwarzweiß körnig (Tri-X)": "Black & white grainy (Tri-X)",
        "Schwarzweiß High-Key": "Black & white high-key",
        "Schwarzweiß grob körnig (Delta 3200)": "Black & white coarse grain (Delta 3200)",
        "Schwarzweiß fein & kornfrei (Leica)": "Black & white fine & grain-free (Leica)",
        "Schwarzweiß Infrarot": "Black & white infrared",
        "Sepia": "Sepia",
        "Selen-Tonung": "Selenium toned",
        "Kodak Portra": "Kodak Portra",
        "Cinestill 800T": "Cinestill 800T",
        "Kodachrome": "Kodachrome",
        "Polaroid": "Polaroid",
        "Warm Golden": "Warm golden",
        "Kühl entsättigt": "Cool desaturated",
        "Pastell": "Pastel",
    },
    "genre": {
        "Editorial": "Editorial", "Fashion": "Fashion", "Beauty": "Beauty",
        "Studio-Porträt": "Studio portrait", "Street": "Street",
        "Dokumentarisch": "Documentary", "Glamour": "Glamour", "Boudoir": "Boudoir",
        "Lifestyle": "Lifestyle", "Filmstill": "Film still", "Lookbook": "Lookbook",
        "Paparazzi": "Paparazzi", "Passfoto": "Passport photo",
        "Smartphone / Social": "Smartphone / social",
    },
    "optik": {
        "85mm f/1.4": "85mm f/1.4", "50mm f/1.8": "50mm f/1.8", "35mm f/2": "35mm f/2",
        "135mm f/2": "135mm f/2", "24mm Weitwinkel": "24mm wide angle",
        "100mm Makro": "100mm macro", "Durchgehend scharf": "Deep focus",
        "Anamorph": "Anamorphic", "Vintage-Objektiv": "Vintage lens",
        "Tilt-Shift": "Tilt-shift",
    },
    "finish": {
        "Natürliche Haut": "Natural skin", "Feines Korn": "Fine grain",
        "Grobes Korn": "Heavy grain", "Weichzeichner": "Soft focus",
        "Vignette": "Vignette", "Scharf & detailliert": "Sharp & detailed",
        "Halation": "Halation", "Leichte Bewegungsunschärfe": "Slight motion blur",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Location
# ─────────────────────────────────────────────────────────────────────────────
LOCATION = {
    "ort": {
        "Sonniges Loft": "Sunlit loft",
        "Weißer Hintergrund": "White backdrop studio",
        "Grauer Hintergrund": "Grey canvas backdrop",
        "Farbiger Hintergrund": "Coloured backdrop studio",
        "Tageslichtstudio": "Daylight loft studio",
        "Altstadtgasse": "Old town alley",
        "Großstadtstraße": "Downtown street",
        "Dachterrasse": "Rooftop terrace",
        "Betonarchitektur": "Brutalist concrete plaza",
        "Wald": "Forest",
        "Strand": "Sandy beach",
        "Blumenwiese": "Wildflower meadow",
        "Bergpanorama": "Mountain panorama",
        "Café": "Café",
        "Altbauwohnung": "Period apartment",
        "Hotelzimmer": "Hotel room",
        "Bibliothek": "Library",
    },
    "tageszeit": {
        "Morgen": "Morning",
        "Mittag": "Midday",
        "Goldene Stunde": "Golden hour",
        "Blaue Stunde": "Blue hour",
        "Nacht": "Night",
    },
    "wetter": {
        "Klar": "Clear",
        "Bewölkt": "Overcast",
        "Regen": "Rain",
        "Nebel": "Fog",
        "Schnee": "Snow",
    },
    "jahreszeit": {
        "Frühling": "Spring",
        "Sommer": "Summer",
        "Herbst": "Autumn",
        "Winter": "Winter",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Field labels, tabs, families
# ─────────────────────────────────────────────────────────────────────────────
FELDNAMEN = {
    "Geschlecht": "Gender", "Typ": "Type", "Alter": "Age", "genaues Alter": "exact age",
    "LoRA-Trigger": "LoRA trigger", "Referenz": "Reference",
    "Herkunft": "Origin", "Hautton": "Skin tone", "Größe": "Height",
    "Figur": "Figure", "Büste": "Bust", "Frisur": "Hair", "Haarfarbe": "Colour",
    "Augen": "Eyes", "Wimpern": "Lashes", "Teint": "Complexion",
    "Schultern": "Shoulders", "Taille": "Waist", "Bauch": "Stomach",
    "Hüfte": "Hips", "Beine": "Legs", "Strähnen": "Highlights",
    "Kinn": "Chin", "Kieferlinie": "Jawline", "Eyeliner": "Eyeliner",
    "Lidschatten": "Eyeshadow", "Rouge": "Blush", "Strümpfe": "Hosiery",
    "Strumpffarbe": "Colour", "Schmuck": "Jewellery", "Brille": "Eyewear",
    "Kopfbedeckung": "Headwear", "Requisit": "Prop", "Eigenes Requisit": "Custom prop", "Gesichtsform": "Face shape",
    "Wangenknochen": "Cheekbones", "Nase": "Nose", "Augenform": "Eye shape",
    "Brauenform": "Brows", "Lippenform": "Lip shape", "Lippen": "Lips",
    "Finish": "Finish", "Make-up": "Make-up", "Hautmerkmale": "Skin features",
    "Nägel": "Nails", "Nagelfarbe": "Colour", "Schuhe": "Shoes",
    "Schuhfarbe": "Colour", "Details": "Details",
    "Oberteil": "Top", "Oberteilfarbe": "Colour",
    "Unterteil": "Bottom", "Unterteilfarbe": "Colour", "Material": "Material",
    "Licht": "Lighting", "Licht-Setup": "Lighting setup",
    "Lichtrichtung": "Direction", "Atmosphäre": "Atmosphere",
    "Licht speichern": "Save Lighting", "Licht laden": "Load Lighting",
}

SEKTIONEN = {
    "Grund": "Basics", "Körper": "Body", "Kopf": "Head", "Gesicht": "Face",
    "Make-up": "Make-up", "Kleidung": "Clothing", "Accessoires": "Accessories",
}

FAMILIEN = {
    # Shoes
    "Pumps": "Pumps", "Absätze": "Heels", "Sandaletten": "Sandals",
    "Stiefel": "Boots", "Tanz & Sport": "dance & sport", "Fetish": "fetish", "flach": "flat", "ohne": "none",
    # Tops
    "Crop Tops": "crop tops", "Tops & Blusen": "tops & blouses", "Bikini": "bikini",
    "Röcke": "skirts", "Shorts & Hosen": "shorts & trousers",
    # Headwear
    # Custom entries without a family of their own (eigene.py)
    "Eigene": "custom",
    "Hüte": "hats", "Mützen & Kappen": "caps & beanies", "Haarschmuck & Tücher": "hair accessories & scarves",
    # Posture
    "stehend": "standing", "sitzend": "sitting", "kniend": "kneeling",
    "liegend": "lying",
    # Mood
    "ruhig": "calm", "freundlich": "friendly", "in sich gekehrt": "introspective",
    "bestimmend": "assertive", "zugewandt": "engaged", "wachsam": "alert",
    "verängstigt": "frightened", "traurig": "sad", "abweisend": "dismissive",
    # Mood and perspective (selfie mode & camera angles)
    "Selfie": "selfie", "Kamerawinkel": "camera angles",
    # Lighting
    "studio": "studio", "natuerlich": "natural", "stimmung": "mood",
    # Style
    "schwarzweiss": "black & white", "farbe": "colour",
    # Location ("studio" as for the light)
    "stadt": "urban", "natur": "nature", "innen": "interior",
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
    # Lighting
    "setup": "lighting setup", "richtung": "direction", "atmosphaere": "atmosphere",
    # Style
    "look": "look", "genre": "genre", "optik": "lens", "finish": "finish",
    # Location
    "ort": "place", "tageszeit": "time of day", "wetter": "weather", "jahreszeit": "season",
    # Photoshoot
    "kamera": "camera", "fokus": "focus", "format": "ratio",
    "ausdruck": "expression", "pose": "pose", "licht": "lighting", "rausch": "noise",
    "set": "set", "perspektive": "perspective",
}

PLATZHALTER = {
    "genaues Alter, z. B. 34 (schlägt den Bereich)":
        "exact age, e.g. 34 (overrides the range)",
    "genaues Alter, z. B. 34 (schlägt den Bereich, ab 18)":
        "exact age, e.g. 34 (overrides the range, 18 and up)",
    "Weitere Details (englisch), z. B. wearing a red raincoat":
        "further details, e.g. wearing a red raincoat",
    "Eigenes Requisit (englisch), z. B. a vintage camera":
        "Custom prop (English), e.g. a vintage camera",
    "Trigger einer Charakter-LoRA, z. B. EileenX – Gesicht, Haare und Make-up kommen dann aus der LoRA":
        "trigger of a character LoRA, e.g. EileenX – face, hair and make-up then come from the LoRA",
    "Nummer des Referenzbilds, z. B. 1 oder 1, 2 – Gesicht, Haare und Make-up kommen dann aus dem Bild":
        "number of the reference image, e.g. 1 or 1, 2 – face, hair and make-up then come from the image",
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
    "Inspire": "Inspire",
    "Inspire Me": "Inspire Me",
    "Inspiriere mich": "Inspire Me",
    "Stimmige Person auswürfeln": "Roll a coherent character",
    "Details": "Details",
    "wird gewürfelt": "is rolled",
    "wird gewürfelt — klicken für fest": "rolled — click to fix",
    "Weiteres (englisch)": "Anything else (English)",

    # Person Builder: labels, sections, reset
    "Klicken setzt dieses Feld zurück": "Click to reset this field",
    "Klicken setzt diese Felder zurück": "Click to reset these fields",
    "Klicken leert dieses Feld": "Click to clear this field",
    "nichts gesetzt": "nothing set",
    "Name": "Name",
    # Builder panels: the die's seed line.
    "Seed": "Seed",
    "neu je Lauf": "new per run",
    "z. B. Casual, Abend, Strand": "e.g. Casual, Evening, Beach",
    # Wardrobe in the Series node: the outfit axis and its rail.
    "Outfit": "Outfit",
    "Outfit {0}": "Outfit {0}",
    "{0} Outfits": "{0} outfits",
    "1 Outfit": "1 outfit",
    "keine Garderobe": "no wardrobe",
    "in Blöcken": "in blocks",
    "gemischt": "mixed",
    "Folge:": "Order:",
    "Kostümwechsel: die Outfits der Wardrobe am Person Builder, ":
        "Costume changes: the outfits of the Wardrobe on the Person node, ",
    "über die Serie verteilt": "spread over the series",
    "Eine Wardrobe an den Eingang garderobe des Person Builders hängen, ":
        "Wire a Wardrobe into the Person node's wardrobe input, ",
    "dann wechselt die Person hier die Outfits.": "and the person changes outfits here.",
    "Kleidung: Wardrobe · {0}": "Clothes: Wardrobe · {0}",
    "Kleidung: keine — eine Wardrobe an den Eingang garderobe hängen":
        "Clothes: none — wire a Wardrobe into the wardrobe input",
    "Kleidung aus einer älteren Version: ": "Clothing from an older version: ",
    "In Wardrobe übernehmen": "Move to Wardrobe",
    "Als Outfit in die angeschlossene Wardrobe, oder in eine neue daneben":
        "As an outfit into the wired Wardrobe, or into a new one next to it",
    "entfernen": "remove",
    "Aus der Person": "From the person",
    "Neues Outfit": "New outfit",
    "Outfit duplizieren": "Duplicate outfit",
    "Outfit löschen": "Delete outfit",
    "löschen?": "delete?",
    "Vorschau rendern": "render preview",
    "rendert …": "rendering …",
    "Ein Lauf durch den eigenen Workflow, mit festem Studio-Look statt Stil und Licht des Shootings.":
        "One run through your own workflow, with a fixed studio look instead of the shoot's style and light.",
    "Wie bei einem echten Shooting: erst alle Fotos im ersten Outfit, dann im zweiten. Die Kameraeinstellungen fangen mit jedem Outfit neu an.":
        "As on a real shoot: all photos in the first outfit, then in the second. The framings start over with every outfit.",
    "Jedes Foto zieht sein Outfit.": "Every photo draws its outfit.",
    "Puppe": "Mannequin",
    "Flat Lay": "Flat lay",
    "Das Outfit an einer gesichtslosen Schaufensterpuppe im Studio.":
        "The outfit on a faceless store mannequin in a studio.",
    "Die Teile von oben nebeneinander ausgelegt.": "The pieces laid out side by side, seen from above.",
    "{0} Outfits rendern": "render {0} outfits",
    "Ein Lauf je Outfit durch den eigenen Workflow, mit festem Studio-Look statt Stil und Licht des Shootings.":
        "One run per outfit through your own workflow, with a fixed studio look instead of the shoot's style and light.",
    "rendert {0} von {1} …": "rendering {0} of {1} …",
    "wartet auf {0} von {1} …": "waiting for {0} of {1} …",
    "⚠ Kein Build-Prompt-Node im Workflow — die Vorschau braucht einen":
        "⚠ No Build Prompt node in the workflow — the preview needs one",
    "⚠ Vorschau fehlgeschlagen — Details in der Konsole": "⚠ Preview failed — details in the console",
    "Veraltet — das Outfit wurde seitdem geändert": "Outdated — the outfit has changed since",
    "veraltet": "outdated",
    "wirklich alle {0} löschen?": "really clear all {0}?",
    "alles": "everything",
    "{0} gesetzt": "{0} set",
    "über die LoRA": "via the LoRA",
    "über das Referenzbild": "via the reference image",
    "{0} löschen?": "clear {0}?",
    "Die {0} gesetzten Felder dieses Bereichs löschen": "Clear the {0} fields set in this section",
    "Farbe wählen": "Choose a colour",
    "keine Farbe": "no colour",
    "Keine Farbe bei {0}": "No colour with {0}",
    "{0} nennt seinen eigenen Stoff – das Material bleibt aus dem Prompt":
        "{0} names its own fabric – the material stays out of the prompt",

    # Photoshoot: header, axes, states
    "ab Nr.": "from no.",
    "Neue Serie": "New series",
    "{0} Fotos": "{0} photos",
    "Fotos {0}–{1}": "photos {0}–{1}",
    "Nächstes:": "Next:",
    "Foto {0}": "photo {0}",
    "{0} von {1} im Bogen": "{0} of {1} in the sheet",
    "Start setzt ihn auf {0}": "Start sets it to {0}",
    "Rezept": "Recipe",
    "Reihenfolge:": "Order:",
    "gezogen": "drawn",
    "weit → nah": "wide → close",
    "Verteilt gezogen, jedes Foto anders – wie bisher.": "Drawn and spread out, every photo different – as before.",
    "Dramaturgie: die Serie beginnt mit der weitesten Einstellung und endet mit der nächsten.":
        "Dramaturgy: the series opens with the widest framing and ends with the closest.",
    "Stimmungsbogen": "mood arc",
    "Stimmungsbogen:": "Mood arc:",
    # Gaze over the series (BLICK_NAMEN in shooting.py)
    "Blick:": "Gaze:",
    "in die Kamera": "at the camera", "meist Kamera": "mostly camera", "abgewandt": "away",
    "Jedes Foto zieht seinen Blick – mal in die Kamera, meist woandershin.":
        "Every photo draws its own gaze – now and then at the camera, mostly elsewhere.",
    "Jedes Foto blickt in die Kamera.": "Every photo looks into the camera.",
    "Zwei von drei Fotos blicken in die Kamera, das dritte woandershin.":
        "Two photos in three look into the camera, the third elsewhere.",
    "Niemand blickt in die Kamera.": "Nobody looks into the camera.",
    "Freude": "Joy", "Dominanz": "Dominance", "Drama": "Drama",
    "Wirkt am stärksten mit {expression} gleich nach {style} in der Prompt-Vorlage und einer Charakter-LoRA.":
        "Works best with {expression} right after {style} in the prompt template, and a character LoRA.",
    "Die Stimmung entwickelt sich über die Serie, Stufe für Stufe; innerhalb einer Stufe variiert sie.":
        "The mood develops over the series, stage by stage; within a stage it still varies.",
    "Speichern": "Save",
    "Abbrechen": "Cancel",
    "Name der Serie": "Series name",
    "Diese Einstellungen als eigene Serie speichern": "Save these settings as a series of your own",
    "Gespeicherte Serie: Einstellungen, Startnummer, Größe und Seed.":
        "Saved series: settings, start number, size and seed.",
    "Gespeicherte Serie löschen: {0}": "Delete saved series: {0}",
    "Takes je Foto:": "Takes per photo:",
    "{0} Takes": "{0} takes",
    "{0} Takes je Foto": "{0} takes each",
    "eigene Einstellung": "custom",
    "reihum": "in turn",
    "jede einmal, reihum": "each once, in turn",
    "Jede gewählte Einstellung kommt reihum genau einmal dran, statt verteilt gezogen zu werden.":
        "Every chosen framing comes up exactly once in turn, instead of being drawn.",
    "Editorial": "Editorial", "Lookbook": "Lookbook", "Headshots": "Headshots",
    "Schuhe": "Shoes", "Test-Bogen": "Test sheet", "Selfie": "Selfie",
    "Alles variiert: jede Einstellung, Pose, Stimmung und jedes Format.":
        "Everything varies: every framing, pose, mood and ratio.",
    "Ganzkörper und Porträt im Wechsel, stehend, ruhig, 2:3 und ein Seed für den gleichen Ort.":
        "Full body and portrait in turn, standing, calm, 2:3 and one seed for the same setting.",
    "Porträt und Nahaufnahme, freundlich, Schwerpunkt Gesicht und Augen, ohne Pose.":
        "Portrait and close-up, friendly, focus on face and eyes, no pose.",
    "Detail und Ganzkörper im Wechsel, stehend, Schwerpunkt Füße, ohne Ausdruck.":
        "Detail and full body in turn, standing, focus on the feet, no expression.",
    "Sieben Fotos, jede Kameraeinstellung genau einmal – zum Prüfen einer Person.":
        "Seven photos, every framing exactly once – for checking a person.",
    "Selfies: Nahaufnahme bis Halbtotale mit dem Handy in der Hand, Ganzkörper im Spiegel, 9:16 oder 4:5, Blick meist in die Kamera.":
        "Selfies: close-up to medium shot with the phone in hand, full body in the mirror, 9:16 or 4:5, gaze mostly into the camera.",
    # The perspective axis (selfie mode)
    "Perspektive": "Perspective",
    "alle {0} Perspektiven": "all {0} perspectives",
    "{0} von {1} Perspektiven": "{0} of {1} perspectives",
    "Kamerawinkel über die Serie variieren, zuerst die Selfies. Aus: keine Perspektive im Prompt.":
        "Vary the camera angle over the series, selfies first. Off: no perspective in the prompt.",
    "Ein Selfie hat das Handy in einer Hand: nur Armhaltungen mit einer freien Hand, keine Rückenansicht, Format 9:16 oder 4:5. Im Liegen liegt sie auf dem Rücken; das Spiegel-Selfie zeigt den ganzen Körper und blickt aufs Display, nicht in die Linse.":
        "A selfie has the phone in one hand: only arm positions with a hand free, no back view, 9:16 or 4:5. Lying down she lies on her back; the mirror selfie shows the whole body and looks at the screen, not the lens.",
    "Nahaufnahme bis Halbtotale, das Spiegel-Selfie mit Ganzkörper. Durchgestrichen: passt zu keiner gewählten Kameraeinstellung.":
        "Close-up to medium shot, the mirror selfie with full body. Struck through: fits none of the chosen framings.",
    "Passt zum Stil-Genre Smartphone / Social.": "Goes with the style genre Smartphone / social.",
    "alle {0} Einstellungen": "all {0} framings",
    "{0} von {1} Einstellungen": "{0} of {1} framings",
    "alle Familien": "all families",
    # Searchable lists (Person/Wardrobe) and the search over long chip lists
    "Suchen …": "Search …", "Keine Treffer": "No matches", "Favoriten": "Favourites",
    "Zuletzt benutzt": "Recently used", "Zuletzt": "Recent",
    "Als Favorit merken": "Add to favourites", "Favorit entfernen": "Remove from favourites",
    # The thumbnail row of a searchable list (vorschau.py)
    "Zeig auf einen Eintrag, um ihn zu sehen": "Point at an entry to see it",
    "Keine Vorschau": "No preview",
    # A custom entries file with problems (eigene.py)
    "1 Meldung zu eigenen Einträgen": "1 message about custom entries",
    "{0} Meldungen zu eigenen Einträgen": "{0} messages about custom entries",
    "nur {0}": "{0} only",
    "alle Bereiche": "all areas",
    "{0} von {1} Bereichen": "{0} of {1} areas",
    "folgt der Einstellung · {0} px": "follows framing · {0} px",
    "Brennweite:": "Lens:",
    "aus Stil-Node": "from Style node",
    "je Einstellung (28–100mm)": "per framing (28–100mm)",
    "Die Brennweite kommt nur aus dem Style-Builder.": "Focal length comes from the Style node only.",
    "Weitwinkel (28mm f/5.6) für weite Einstellungen, 50mm halbtotal, 85mm f/1.4 für Porträts, 100mm Makro nah.":
        "Wide-angle (28mm f/5.6) for wide shots, 50mm medium, 85mm f/1.4 for portraits, 100mm macro close-up.",
    "Requisiten:": "Props:",
    "mit Requisiten": "with props",
    "mit Requisiten (Tasse, Buch …)": "with props (mug, book …)",
    "Armhaltungen ohne Requisiten – bisherige Serien unverändert.":
        "Arm positions without props – keeps existing series unchanged.",
    "Mischt Kaffeetasse, Buch, Weinglas und Blumenstrauß zu passenden Haltungen.":
        "Mixes coffee mug, book, wine glass and flowers with matching postures.",
    "Eigenes Requisit (englisch), z. B. a vintage camera":
        "Custom prop (English), e.g. a vintage camera",
    "Eigenes Requisit (englisch), z. B. a vintage camera, a red umbrella":
        "Custom prop (English), e.g. a vintage camera, a red umbrella",
    "neu pro Foto": "new per photo",
    "ein Seed · {0}": "one seed · {0}",
    "Schnell:": "Quick:",
    "nah": "close", "Figur": "figure", "weit": "wide",
    "Durchgestrichen: kommt mit den gewählten Einstellungen nicht vor.":
        "Struck through: cannot occur with the chosen framings.",
    "Jede Einstellung wählt ein passendes Seitenverhältnis – Ganzkörper wird nie Querformat.":
        "Each framing picks a ratio that suits it – a full-body shot is never landscape.",
    "Jedes Foto bekommt eigenes Rauschen. Ausschalten hält den Schauplatz über die Serie gleich.":
        "Every photo gets its own noise. Switch off to keep the same setting across the series.",
    "Anderer Schauplatz": "Other setting",
    "Kontaktbogen": "Contact sheet",
    # Contact sheet pages, the prompt of a photo, an emptied sheet
    "{0}–{1} von {2}": "{0}–{1} of {2}",
    "Vorige Seite": "Previous page", "Nächste Seite": "Next page",
    "Prompt": "Prompt", "Kopieren": "Copy", "Kopiert": "Copied", "Kopieren fehlgeschlagen": "Copy failed",
    "nicht mehr im Verlauf — ComfyUI wurde seitdem neu gestartet":
        "no longer in the history — ComfyUI has restarted since",
    "Die Bilder der vorigen Einstellungen bleiben erhalten — zurückstellen, um sie zu sehen.":
        "Pictures of the previous settings are kept — switch back to see them.",
    # Start shooting: progress and a refused photo; a series without a person
    "eingereiht {0}/{1}": "queued {0}/{1}",
    "⚠ Foto {0} wurde nicht eingereiht — ComfyUI hat es abgelehnt, siehe dessen Fehlermeldung":
        "⚠ Photo {0} was not queued — ComfyUI refused it, see its error message",
    "⚠ person_data ist nicht verbunden — den Ausgang person_data der Person hier anschließen":
        "⚠ person_data is not connected — wire the Person's person_data output in here",
    "Ohne ihn kennt die Serie keine Person: kein Kürzen je Einstellung, keine Outfits.":
        "Without it the series knows no person: nothing shortened per framing, no outfits.",
    "⚠ Badekleidung im Schnee/Winter — Outfit passt nicht zum Set":
        "⚠ Swimwear in snow/winter — outfit does not match the set",
    "Ein gewähltes Set spielt draußen im Winter oder Schnee, während das Outfit Badekleidung trägt.":
        "An active outdoor set uses winter or snow while an outfit wears swimwear.",
    # Person: Inspire Me over a filled person, the first-run hint
    "{0} Felder ersetzen?": "Replace {0} fields?",
    "Neu hier? 🎲 Inspire Me würfelt eine stimmige Person — oder einen Bereich aufklappen und selbst wählen. Jedes Feld ist optional.":
        "New here? 🎲 Inspire Me rolls a coherent person — or open a section and choose yourself. Every field is optional.",
    "Foto": "Photo",
    "Stimmung": "Mood",
    "Take {0}": "take {0}",
    "Entwurf": "Draft",
    "Entwurf: ohne zweiten Durchgang – etwa halbe Zeit, Grundauflösung. Favoriten danach fertigstellen.":
        "Draft: without the second pass – about half the time, base resolution. Finish your favourites afterwards.",
    "Verbinde den Ausgang refine mit einem refine-Schalter (der Render-Node der Beispiel-Workflows hat einen), dann geht Entwurf.":
        "Wire the refine output to a refine switch (the example workflows' Render node has one) to use Draft.",
    "Favoriten fertigstellen": "Finish favourites",
    "{0} Favoriten fertigstellen": "Finish {0} favourites",
    "Erst Fotos im Kontaktbogen als Favorit markieren.": "Mark photos as favourites in the contact sheet first.",
    "Alle Favoriten sind fertig.": "All favourites are finished.",
    "Die Favoriten in voller Qualität: gleicher Take, gleicher Seed, mit zweitem Durchgang.":
        "The favourites at full quality: same take, same seed, with the second pass.",
    "Favorit": "Favourite",
    "Nachfotografieren": "Re-shoot",
    "Gleiche Planung, neues Rauschen": "Same plan, new noise",
    "Bild öffnen": "Open image",
    "noch nicht fotografiert": "not shot yet",
    "1 Foto nachfotografieren": "Re-shoot 1 photo",
    "{0} Fotos nachfotografieren": "Re-shoot {0} photos",
    "Auswahl aufheben": "Clear selection",
    # Selects -> next round (naechste_runde() in shooting.py)
    "Verwerfen": "Reject",
    "Für die nächste Runde: was nur verworfene Fotos zeigen, fällt weg.":
        "For the next round: whatever only rejected photos show is dropped.",
    "Nächste Runde": "Next round",
    "Nächste Runde fehlgeschlagen": "Next round failed",
    "Runde {0}": "Round {0}",
    "aus {0} Favoriten": "based on {0} selects",
    "{0} verworfen": "{0} rejected",
    "zurück zu Runde {0}": "back to round {0}",
    "Die vorige Runde mit ihren Einstellungen, Favoriten und Takes zurückholen.":
        "Bring back the previous round with its settings, favourites and takes.",
    "Zurück zur vorigen Runde? Favoriten und Verworfene dieser Runde gehen verloren.":
        "Go back to the previous round? The favourites and rejects of this round are lost.",
    "Erst Favoriten (♥) im Kontaktbogen markieren: die nächste Runde behält ihre Einstellungen, Pose- und Stimmungsfamilien, Schwerpunkte und Outfits.":
        "Mark favourites (♥) in the contact sheet first: the next round keeps their framings, "
        "pose and mood families, focus areas and outfits.",
    "Neue Serie ab Foto {0}: nur die Einstellungen, Pose- und Stimmungsfamilien, Schwerpunkte und Outfits der Auswahl ({1} ♥, {2} ✕).":
        "A new series from photo {0}: only the framings, pose and mood families, focus areas "
        "and outfits of the selects ({1} ♥, {2} ✕).",
    "{0} von {1} Outfits": "{0} of {1} outfits",
    # The Lightbox (js/lightbox.mjs): the contact sheet big, in the bottom panel
    "Lightbox": "Lightbox",
    "In der Lightbox ansehen: groß, mit Filtern, Vergleich und Tasten (← → F X C).":
        "Review in the Lightbox: big, with filters, compare and keys (← → F X C).",
    "Doppelklick: in der Lightbox öffnen": "Double-click: open in the Lightbox",
    "Tasten: ← → blättern, F Favorit, X verwerfen, C vergleichen, Esc schließt das Vollbild":
        "Keys: ← → browse, F favourite, X reject, C compare, Esc leaves fullscreen",
    "Welche Serie": "Which series",
    "Vollbild": "Fullscreen",
    "Keine Serie im Workflow — eine Photoshoot-Serie anlegen, dann erscheinen ihre Fotos hier.":
        "No Series in the workflow — add a Photoshoot Series and its photos show up here.",
    "Verworfen": "Rejects",
    "Entwürfe": "Drafts",
    "Nichts in diesem Filter.": "Nothing in this filter.",
    "Noch keine Bilder in dieser Serie — Shooting starten.": "No pictures in this series yet — start shooting.",
    "Klick auf ein Bild: Favorit an/aus": "Click a picture to star it or take the star back",
    "Nur ein Foto in diesem Filter — nichts zum Vergleichen.": "Only one photo in this filter — nothing to compare.",
    "Vorheriges Foto": "Previous photo", "Nächstes Foto": "Next photo",
    "gewählt": "chosen",
    "Vergleichen": "Compare",
    "Fertigstellen": "Finish",
    "In voller Qualität fertigstellen: gleicher Take, gleicher Seed, mit zweitem Durchgang.":
        "Finish at full quality: same take, same seed, with the second pass.",
    "Foto {0} eingereiht — das neue Bild erscheint, sobald es gerendert ist.":
        "Photo {0} queued — the new picture appears once it is rendered.",
    "{0} Favoriten": "{0} selects",
    "Runde {0} geplant — ab Foto {1}.": "Round {0} planned — from photo {1}.",
    "Alle Outfits verwenden": "Use all outfits",
    "Fotos": "Photos",
    "ab": "from",
    "ab Foto {0}": "from photo {0}",
    "Startnummer. Die Serie beginnt bei diesem Foto.":
        "Starting number. The series begins with this photo.",
    "Neue Serie: zufällige Startnummer, gleiche Einstellungen":
        "New series: random starting number, same settings",
    "Shooting starten": "Start shooting",
    "ca. ": "approx. ",
    "Anderen Schauplatz suchen": "Look for a different setting",
    "Kamera": "Camera", "Pose": "Pose", "Ausdruck": "Expression",
    "Schwerpunkt": "Focus", "Format": "Format", "Rauschen": "Noise",
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
    "ein anderes Rauschfeld, auch bei gleichem Seed.":
        "a different noise field, even at the same seed.",
    "Das Rauschen hat Bildmaße. Ändert sich das Seitenverhältnis, ist es ":
        "Noise has image dimensions. If the aspect ratio changes it is ",
    "teilt einen Seed, dann bleibt der Schauplatz über die Fotos gleich.":
        "shares one seed, which keeps the setting the same across photos.",
    "Format würfelt — bei wechselnder Größe wirkt der Serien-Seed nicht":
        "Ratio is rolling — with changing size the series seed has no effect",
    "s je Bild, gemessen an den letzten Läufen":
        "s per image, measured from recent runs",

    # Shoot files and the Director (js/regie.mjs)
    "Shooting": "Shoot",
    "Gespeichertes Shooting laden: Person, Garderobe, Bausteine, Serie, Szene und Vorlage.":
        "Load saved shoot: person, wardrobe, builders, series, scene and template.",
    "Gespeichertes Shooting löschen: {0}": "Delete saved shoot: {0}",
    "Name des Shootings": "Name of the shoot",
    "Das ganze Shooting unter einem Namen speichern": "Save the whole shoot under a name",
    "Gespeichert: {0}": "Saved: {0}",
    "Fehler: {0}": "Error: {0}",
    "Datei": "File",
    "Als Datei herunterladen (zum Teilen)": "Download as a file (to share)",
    "Shooting-Datei öffnen": "Open a shoot file",
    "Datei ist kein gültiges JSON": "The file is not valid JSON",
    "Shooting laden: {0}": "Load shoot: {0}",
    "Regie": "Director",
    "Regie: ein Satz wird ein ganzes Shooting, über ein beliebiges Chat-LLM":
        "Director: one sentence becomes a whole shoot, through any chat LLM",
    "ein Satz wird ein ganzes Shooting, über ein beliebiges Chat-LLM":
        "one sentence becomes a whole shoot, through any chat LLM",
    "Idee in einem Satz": "The idea in one sentence",
    "z. B. ein verregneter Nachmittag in einem Pariser Café, melancholisch, schwarzweiß":
        "e.g. a rainy afternoon in a Paris café, melancholic, black and white",
    "Aus einer Idee": "From a brief",
    "Aus einem Referenzfoto": "From a reference photo",
    "LLM-Prompt kopieren": "Copy LLM prompt",
    "Prompt öffnen": "Open prompt",
    "Offline-Entwurf": "Offline draft",
    "Nur Wörter der Idee gegen die Listen – ohne LLM, grob":
        "Only the brief's words against the lists – no LLM, rough",
    "In ein beliebiges Chat-LLM einfügen und die Antwort unten einfügen.":
        "Paste it into any chat LLM, then paste its answer below.",
    "In ein Chat-LLM mit Bildeingabe einfügen, das Foto anhängen und die Antwort unten einfügen. Das Foto bleibt im Chat – zurück kommen nur Labels.":
        "Paste it into a chat LLM that takes images, attach the photo, then paste its answer below. "
        "The photo stays in the chat – only labels come back.",
    "Kopiert.": "Copied.",
    "Kopieren nicht möglich – „Prompt öffnen“ nutzen.": "Could not copy – use “Open prompt”.",
    "Antwort des LLM": "The LLM's answer",
    "Antwort hier einfügen (JSON)": "Paste the answer here (JSON)",
    "Importieren": "Import",
    "Wird geprüft …": "Checking …",
    "Das wird gesetzt": "This will be set",
    "kein Node – wird übersprungen": "no node – skipped",
    "{0} abgelehnt": "{0} rejected",
    "Hinweise": "Notes",
    "Übernehmen": "Apply",
    "Trotzdem übernehmen": "Apply anyway",
    "Übernommen.": "Applied.",
    "Rückgängig": "Undo",
    "Rückgängig gemacht.": "Undone.",
    "Schließen": "Close",
    "Nichts zu übernehmen.": "Nothing to apply.",
    "alle Einstellungen": "all framings",
    "ab Nr. {0}": "from no. {0}",
    # Section names in the preview
    "Person": "Person",
    "Garderobe": "Wardrobe",
    "Licht": "Lighting",
    "Stil": "Style",
    "Serie": "Series",
    "Szene": "Scene",
    "Prompt-Vorlage": "Prompt template",
    # Studio sidebar (js/studio.mjs)
    "Look": "Look",
    "Shoot": "Shoot",
    "Dein Setup": "Your setup",
    "Lightbox öffnen": "Open Lightbox",
    "Kein Photoshoot-Node im Workflow": "No Photoshoot (Series) node in this workflow",
    "Kein {0}-Node an dieser Serie": "No {0} node wired to this series",
    "In diesem Workflow plant die Serie Pose und Ausdruck selbst.":
        "In this workflow, the Series node plans pose and expression itself.",
    "Im Reiter „Shoot“ öffnen →": "Open in the Shoot tab →",
    "Auf der Leinwand": "On canvas",
    "Den Node auf der Leinwand zeigen": "Select the node and show it on the canvas",
    "im Studio": "in Studio",
    "↗ Als Node auf Leinwand": "↗ Pop out as node",
    "Diesen Bereich als eigenen Node auf der Leinwand anlegen": "Create a standalone node for this section on the canvas",
    "Shooting-Dateien": "Shoot files",
    "Angeheftet": "Pinned",
    "An Photoshoot Studio anheften": "Pin to Photoshoot Studio",
    "Rechtsklick auf einen beliebigen Node → „An Photoshoot Studio anheften“ legt seine Einstellungen hierher, etwa lora_name und strength deiner LoRA-Loader.":
        "Right-click any node → “Pin to Photoshoot Studio” puts its settings here, such as lora_name and strength of your LoRA loaders.",
    "Lösen": "Unpin",
    "Widget fehlt": "widget missing",
    "Node entfernt": "node removed",
    # Compact view (js/shared.mjs, the panels)
    "Kompakt anzeigen": "Compact view",
    "Voll anzeigen": "Full view",
    "bearbeiten": "edit",
    "In der Studio-Seitenleiste bearbeiten": "Edit in the Studio sidebar",
    "+{0} · alle in der Lightbox": "+{0} · all in the Lightbox",
    # Location node and the Series' set and light axes
    "Location": "Location",
    "Set": "Set",
    "1 Set": "1 set",
    "{0} Sets": "{0} sets",
    "Set {0}": "Set {0}",
    "Neues Set": "New set",
    "Set duplizieren": "Duplicate set",
    "Set löschen": "Delete set",
    "draußen": "outdoors",
    "drinnen": "indoors",
    "ohne Familie": "no family",
    "nur draußen": "outdoors only",
    "wartet auf Render-Test": "awaiting render test",
    "Noch keine getesteten Einträge — sie warten auf den Render-Test. Bis dahin: eigene Einträge (Custom entries) oder das Set unter Details als freier Text.":
        "No tested entries yet — they are awaiting the render test. Until then: your own entries (Custom entries), or describe the set as free text under Details.",
    "Die Familie sagt der Serie auch, ob das Set drinnen oder draußen ist – danach richtet sich das Licht.":
        "The family also tells the Series whether the set is indoors or outdoors – the light follows it.",
    "Nur für Sets draußen – dieses Set ist drinnen (Studio oder Innenraum) und lässt das Feld weg.":
        "For outdoor sets only – this set is indoors (studio or interior) and leaves the field out.",
    "Gespeicherte Szenen:": "Saved scenes:",
    "kein Location-Node": "no Location node",
    "Schauplatzwechsel: die Sets des Location-Nodes am Eingang ort_data, über die Serie verteilt":
        "Set changes: the sets of the Location node on the location_data input, spread over the series",
    "Einen Photoshoot-Location-Node an den Eingang ort_data hängen, dann wechselt die Serie die Sets; ":
        "Wire a Photoshoot Location node into the location_data input and the series changes its sets; ",
    "den Ausgang szene an szene von Build Prompt statt des festen Szenentexts.":
        "wire the scene output into Build Prompt's scene instead of the fixed scene text.",
    "Wie bei einem echten Shooting: erst alle Fotos im ersten Set, dann im zweiten. Die Kameraeinstellungen fangen mit jedem Set neu an.":
        "As on a real shoot: first every photo in the first set, then in the second. The framings start over with every set.",
    "Jedes Foto zieht sein Set.": "Every photo draws its set.",
    "Kurzform (Nahaufnahme, Porträt):": "Short form (close-up, portrait):",
    "Nahaufnahme und Porträt bekommen die Kurzform – den ersten Teil jeder Angabe, was hinter dem Kopf zu sehen ist; Detail kein Set.":
        "Close-up and portrait get the short form – the first part of each entry, what is seen behind the head; an extreme close-up gets no set.",
    "nicht im Bild": "not in frame",
    "kurz": "short",
    "je Set": "per set",
    "Tageszeit": "time of day",
    "Jedes Set bekommt ein passendes Licht und behält es auf allen seinen Fotos.":
        "Every set gets a fitting light and keeps it on all of its photos.",
    "Der Tag über die Serie: Morgen, Mittag, Goldene Stunde, Blaue Stunde, Nacht – je Set das passende Licht dazu.":
        "The day over the series: morning, midday, golden hour, blue hour, night – with the light that fits each set.",
    "Jedes Foto zieht sein Licht, passend zu seinem Set.": "Every photo draws its light, fitting its set.",
    "Das Licht wechselt mit dem Set oder als Tageszeit über die Serie – aus den 30 Setups des Licht-Nodes.":
        "The light changes with the set or as a time of day over the series – from the Lighting node's 30 setups.",
    "Draußen-Licht (Sonne, Golden Hour, Mond …) nur bei Sets draußen, Studio- und Fensterlicht nur drinnen.":
        "Outdoor light (sun, golden hour, moon …) only on outdoor sets, studio and window light only indoors.",
    "Morgen": "Morning", "Mittag": "Midday", "Goldene Stunde": "Golden hour",
    "Blaue Stunde": "Blue hour", "Nacht": "Night",
    "⚠ Sets liegen an, aber der Ausgang szene ist nicht verbunden — an szene von Build Prompt hängen":
        "⚠ Sets are wired in, but the scene output is not connected — wire it into Build Prompt's scene",
    "Sonst bekommt Build Prompt weiter den festen Szenentext.": "Otherwise Build Prompt keeps getting the fixed scene text.",
    "⚠ Die Lichtachse ist an, aber der Ausgang licht ist nicht verbunden — an lighting von Build Prompt hängen":
        "⚠ The light axis is on, but the lighting output is not connected — wire it into Build Prompt's lighting",
    "Sonst bekommt Build Prompt weiter das Licht des Licht-Nodes.": "Otherwise Build Prompt keeps getting the Lighting node's light.",

    # UX enhancements (2.7.2)
    "Nach links verschieben": "Move left",
    "Nach rechts verschieben": "Move right",
    "Neu würfeln": "Re-roll",
    "Neuen zufälligen Seed würfeln": "Roll a new random seed",
    "Voll": "Full",
    "Nah": "Close",
    "Weit": "Wide",
    "{0} Wörter": "{0} words",
    "+ Wardrobe anlegen": "+ Add Wardrobe",
    "Wardrobe-Node daneben anlegen und mit garderobe verbinden": "Create a Wardrobe node next to this one and wire it to wardrobe",
    "+ Location anlegen": "+ Add Location",
    "Location-Node anlegen und mit Serie und Build Prompt verbinden": "Create a Location node and wire it to Series and Build Prompt",
    "+ Anlegen & verbinden": "+ Create & wire",
    "Verbinden": "Connect",
    "Stopp": "Stop",
    "Laufendes Rendering abbrechen und Warteschlange leeren": "Interrupt current render and clear the queue",
    "Rendert Foto {0}": "Rendering photo {0}",
    "noch {0} in Queue": "{0} left in queue",
    "Foto schießen": "Shoot photo",
    "Nur dieses geplante Foto jetzt einreihen": "Queue only this planned photo now",
    "In Wardrobe bearbeiten": "Edit in Wardrobe",
    "Im Location-Node bearbeiten": "Edit in Location node",
    "Klicken: Outfit in dieser Serie an-/abwählen": "Click to include or exclude this outfit in the series",
    "Gespeichert": "Saved",
    "Name des Bausteins": "Block name",
    "Unter einem Namen speichern": "Save under a name",
    "Gespeicherten Baustein laden": "Load saved block",
    "Gespeicherten Baustein löschen: {0}": "Delete saved block: {0}",
    "Standard-Vorlage": "Default template",
    "Empfohlene Platzhalter-Reihenfolge in die Vorlage einsetzen": "Insert the recommended placeholder order into the template",
    "Unbekannter Platzhalter: {0}": "Unknown placeholder: {0}",
    "Eingang verbunden, fehlt im Text: {0}": "Input wired, missing in text: {0}",

    # Inline custom entries & Studio preset pack manager (2.8.3)
    "Eigenen Eintrag löschen": "Delete custom entry",
    "Eigener Eintrag …": "Custom entry …",
    "Name der Vorgabe": "Preset name",
    "Prompt (englisch), z. B. layered {c} wolf cut": "Prompt (English), e.g. layered {c} wolf cut",
    "Prompt (englisch)": "Prompt (English)",
    "Name und Prompt dürfen nicht leer sein": "Name and prompt must not be empty",
    "Als eigene Vorgabe speichern": "Save as custom preset",
    "Eigene Vorgaben": "Custom presets",
    "Eigene Frisuren, Kleidung, Requisiten, Posen, Lichter und Looks als JSON-Dateien in user/krea2_presets/.":
        "Your own hairstyles, clothing, props, poses, lights and looks as JSON files in user/krea2_presets/.",
    "{0} Einträge": "{0} entries",
    "1 Eintrag": "1 entry",
    "Pack löschen: {0}": "Delete pack: {0}",
    "Noch keine eigenen Vorgaben geladen.": "No custom presets loaded yet.",
    "JSON-Datei laden": "Load JSON file",
    "JSON einfügen": "Paste JSON",
    "Name des Packs (z. B. 90s_fashion)": "Pack name (e.g. 90s_fashion)",
    "JSON hier einfügen (photoshoot-presets/1)": "Paste JSON here (photoshoot-presets/1)",
    "Neu laden": "Reload",
    "Anker-Set": "Anchor set",
    "Sechs Referenzfotos einer Person: ein Seed, festes Format 2:3, ruhige Stimmung, jede Einstellung einmal.":
        "Six reference photos of one person: one seed, fixed 2:3 ratio, calm moods, each framing once.",

    # Interactive Wording Lab in Studio -> Your setup (3.0.0)
    "Lighting": "Lighting",
    "Style": "Style",
    "Expression": "Expression",
    "Wortlabor": "Wording lab",
    "Testet Formulierungen auf 2 festen Seeds (Entwurf) gegen das nackte Wort – direkt im aktiven Workflow.":
        "Tests wordings on 2 fixed seeds (draft) against the bare word — directly in the active workflow.",
    "Feld": "Field",
    "Bezeichnung (dient auch als Kontrolle)": "Label (also used as control)",
    "z. B. Strohhut oder Altstadtgasse": "e.g. Straw hat or Old town alley",
    "Kandidat A (englischer Prompt)": "Candidate A (English prompt)",
    "z. B. a wide-brimmed woven straw sun hat": "e.g. a wide-brimmed woven straw sun hat",
    "Kandidat B (optional)": "Candidate B (optional)",
    "zweite Formulierung zum direkten Vergleich": "second wording to compare side by side",
    "Auf 2 Seeds testen": "Test on 2 seeds",
    "Bitte Feld, Bezeichnung und Kandidat A ausfüllen.":
        "Please fill in Field, Label and Candidate A.",
    "Kandidat A": "Candidate A",
    "Kandidat B": "Candidate B",
    "Kontrolle": "Control",
    "reiht ein …": "queueing …",
    "Einreihen fehlgeschlagen": "Queue failed",
    "Fertig — Gewinner direkt als eigenen Eintrag speichern.":
        "Done — save the winner directly as a custom preset.",
    "Als eigenen Eintrag speichern": "Save as custom preset",

    # Two People / Couples switcher in Studio (3.0.0)
    "Person 1": "Person 1",
    "Person 2": "Person 2",
    "Zweite Person aktiv": "Second person active",
    "Person 2 verdrahtet": "Person 2 wired",
    "Paar-Interaktion": "Couple interaction",
    "Kein Wardrobe-Node an Person 2": "No Wardrobe node on Person 2",

    # Character Cards / Casting-Deck, Visual Pack Editor & Exporter, Model Profiles
    "Charakter-Karten": "Character cards",
    "Karte speichern": "Save card",
    "Name der Charakter-Karte …": "Character card name …",
    "In Person {0} laden": "Load into Person {0}",
    "Charakter-Karte löschen: {0}": "Delete character card: {0}",
    "Noch keine Charakter-Karten gespeichert.": "No character cards saved yet.",
    "Einträge anzeigen / bearbeiten": "Show / edit entries",
    "In Zufalls-Pools einbeziehen": "Include in dice pools",
    "Pack exportieren: {0}": "Export pack: {0}",
    "Bearbeiten": "Edit",
    "Eintrag löschen": "Delete entry",
    "Bezeichnung": "Label",
    "Familie (optional)": "Family (optional)",
    "Modell-Profil": "Model profile",
    "Krea 2 (Standard)": "Krea 2 (Default)",
    "Optimiert für Krea 2 – hält Kopf-Körper-Proportionen in Totale und Ganzkörper.":
        "Tuned for Krea 2 — preserves head-to-body proportions in full and wide shots.",
    "Kompakt (Flux / Qwen / SDXL)": "Compact (Flux / Qwen / SDXL)",
    "Kurze, modellneutrale Kamera-Angaben ohne proportionslastige Füllwörter.":
        "Concise, model-neutral framings without proportion padding.",
    "Eigene Kamera-Texte": "Custom framings",
    "Überschreibt jede Kamera-Einstellung mit eigenem englischen Prompt-Text.":
        "Override each framing with your own English prompt text.",
    "Kamera-Texte zurücksetzen": "Reset framings",

    # ComfyUI QoL Toasts & Shortcuts
    "Charakter-Karte gespeichert: {0}": "Character card saved: {0}",
    "Charakter-Karte „{0}“ in Person {1} geladen": "Character card “{0}” loaded into Person {1}",
    "Charakter-Karte gelöscht: {0}": "Character card deleted: {0}",
    "Pack exportiert: {0}": "Pack exported: {0}",
    "Pack gelöscht: {0}": "Pack deleted: {0}",
    "Eintrag gespeichert": "Entry saved",
    "Vorgaben-Pack importiert": "Preset pack imported",
    "LLM-Prompt in Zwischenablage kopiert": "LLM prompt copied to clipboard",
    "Wortlabor fertig — Gewinner speichern": "Wording lab finished — save your winner",
    "Entwurf: AN": "Draft: ON",
    "Entwurf: AUS": "Draft: OFF",
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
        "lighting": LIGHTING,
        "style": STYLE,
        "location": LOCATION,
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
