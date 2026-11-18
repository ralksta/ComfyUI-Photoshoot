"""
Grouping, colour swatch and inspiration tables for Person Builder.

Kept separate from person_builder.py so the node logic stays readable while
PRESETS, MINDESTALTER, NONE and compose_person stay in person_builder.py.
"""

# Shoes that are not shoes - no colour may go in front of these. Otherwise it
# would read "wearing red barefoot".
SCHUHE_OHNE = {"barefoot", "only sheer stockings, no shoes",
               "only socks, no shoes"}

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

# A colour the prompt drops, so the interface greys its button out: legwear
# colour with bare legs, shoe colour with no shoes (see compose_person()).
FARBE_ENTFAELLT = {"hosieryColor": ("hosiery", ["bare legs"]),
                   "shoesColor": ("shoes", sorted(SCHUHE_OHNE))}


def vervollstaendige_farbwerte(presets):
    """Fill the clothing colour swatch maps from person_builder.PRESETS."""
    for cat in ("topColor", "bottomColor", "hosieryColor", "shoesColor"):
        FARBWERTE[cat] = {lbl: _KLEIDFARBEN[lbl] for lbl, _ in presets[cat]}
    return FARBWERTE


# "Inspire Me" in the Person panel (js/person.mjs) rolls a coherent person
# from these pools - labels only, so the interface keeps no list of its own.
# Gender and age first, then one archetype, which keeps skin, hair and eyes
# plausible together; the rest is drawn independently. A label missing from
# PRESETS leaves its field empty (the smoke test fails on one). Clothing is not
# rolled - that is the Wardrobe's. Appended here so nothing above moves.
INSPIRATION = {
    # Repeats weight the draw.
    "gender": ["Frau", "Frau", "Frau", "Mann", "Mann", "Transfrau", "Person"],
    "age": ["Anfang 20", "Mitte 20", "Ende 20", "Anfang 30", "Mitte 30", "Ende 30",
            "40er", "50er"],
    # The genders that get the men's pools below and no make-up.
    "maenner": ["Mann"],
    "height": ["Durchschnittlich", "Groß", "Zierlich"],
    "figure": ["Athletisch", "Schlank", "Sanduhr", "Schlank definiert", "Kurvig",
               "Durchschnittlich"],
    "figureMann": ["Athletisch", "Schlank definiert", "Schlank", "Muskulös", "Durchschnittlich"],
    "shoulders": ["Sportlich", "Gerade", "Schmal", "Breit"],
    "cheekbones": ["Hoch betont", "Markant", "Weich"],
    "nose": ["Gerade", "Klein", "Schmal", "Leicht gebogen", "Stupsnase"],
    "eyeShape": ["Mandelförmig", "Rund", "Weit auseinander", "Katzenaugen"],
    # Make-up: lips with this chance, eyeshadow on top with the second.
    "schminkChance": 0.65,
    "lidschattenChance": 0.5,
    "lipColor": ["Nude", "Altrosa", "Mauve", "Koralle"],
    "lipFinish": ["Matt", "Satin", "Gloss"],
    "eyeshadow": ["Nude", "Braun", "Gold"],
    "archetypen": [
        {"ethnicity": "Skandinavisch",
         "skinTone": ["Sehr hell", "Hell"],
         "complexion": ["Natürliche Poren", "Dewy", "Porzellan"],
         "hairColor": ["Blond", "Platinblond", "Dunkelblond", "Rot / Kupfer", "Erdbeerblond"],
         "eyes": ["Eisblau", "Blau", "Graugrün", "Grün", "Graublau"],
         "hair": ["Lange Wellen", "Lang glatt", "Curtain Bangs", "Messy Bun", "Pferdeschwanz"],
         "hairMann": ["Kurz wellig", "Undercut", "Fransiger Kurzhaarschnitt"],
         "skinFeatures": ["Sommersprossen"], "merkmalChance": 0.35},
        {"ethnicity": "Mediterran",
         "skinTone": ["Hell gebräunt", "Gebräunt", "Oliv"],
         "complexion": ["Natürliche Poren", "Dewy", "Matt"],
         "hairColor": ["Braun", "Dunkelbraun", "Kastanie", "Schwarz"],
         "eyes": ["Braun", "Dunkelbraun", "Haselnuss", "Bernstein"],
         "hair": ["Locken", "Lange Wellen", "Wolf Cut / Stufenschnitt", "Half-up"],
         "hairMann": ["Kurz wellig", "Fransiger Kurzhaarschnitt", "Undercut"]},
        {"ethnicity": "Osteuropäisch",
         "skinTone": ["Sehr hell", "Hell", "Hell gebräunt"],
         "complexion": ["Matt", "Natürliche Poren", "Porzellan"],
         "hairColor": ["Dunkelblond", "Braun", "Kastanie", "Dunkelbraun"],
         "eyes": ["Eisblau", "Graublau", "Graugrün", "Dunkelbraun"],
         "hair": ["Lang glatt", "Lange Wellen", "Bob", "Flechtzopf"],
         "hairMann": ["Undercut", "Buzzcut / Abrasur", "Kurz wellig"]},
        {"ethnicity": "Nahöstlich",
         "skinTone": ["Hell gebräunt", "Gebräunt", "Oliv", "Bronze"],
         "complexion": ["Natürliche Poren", "Matt", "Dewy"],
         "hairColor": ["Schwarz", "Dunkelbraun"],
         "eyes": ["Dunkelbraun", "Braun", "Haselnuss"],
         "hair": ["Lange Wellen", "Locken", "Lang glatt"],
         "hairMann": ["Kurz wellig", "Undercut", "Fransiger Kurzhaarschnitt"]},
        {"ethnicity": "Ostasiatisch",
         "skinTone": ["Sehr hell", "Hell", "Hell gebräunt"],
         "complexion": ["Glas-Haut", "Porzellan", "Natürliche Poren"],
         "hairColor": ["Schwarz", "Dunkelbraun"],
         "eyes": ["Dunkelbraun", "Braun"],
         "hair": ["Lang glatt", "Bob", "Curtain Bangs", "Pixie"],
         "hairMann": ["Undercut", "Fransiger Kurzhaarschnitt", "Kurz wellig"]},
        {"ethnicity": "Südasiatisch",
         "skinTone": ["Gebräunt", "Braun", "Dunkelbraun", "Hell gebräunt"],
         "complexion": ["Dewy", "Natürliche Poren", "Matt"],
         "hairColor": ["Schwarz", "Dunkelbraun"],
         "eyes": ["Dunkelbraun", "Braun", "Haselnuss"],
         "hair": ["Lang glatt", "Lange Wellen", "Locken", "Flechtzopf"],
         "hairMann": ["Kurz wellig", "Undercut"]},
        {"ethnicity": "Afrikanisch",
         "skinTone": ["Braun", "Dunkelbraun", "Ebenholz"],
         "complexion": ["Dewy", "Natürliche Poren", "Matt"],
         "hairColor": ["Schwarz", "Dunkelbraun"],
         "eyes": ["Dunkelbraun", "Braun"],
         "hair": ["Afro", "Braids / Zöpfe", "Buzzcut / Abrasur", "Locken"],
         "hairMann": ["Afro", "Buzzcut / Abrasur", "Braids / Zöpfe"]},
        {"ethnicity": "Latina",
         "skinTone": ["Hell gebräunt", "Gebräunt", "Bronze", "Oliv"],
         "complexion": ["Dewy", "Natürliche Poren", "Glas-Haut"],
         "hairColor": ["Braun", "Dunkelbraun", "Kastanie", "Schwarz"],
         "eyes": ["Braun", "Haselnuss", "Bernstein", "Dunkelbraun"],
         "hair": ["Lange Wellen", "Locken", "Lang glatt", "Pferdeschwanz"],
         "hairMann": ["Kurz wellig", "Fransiger Kurzhaarschnitt", "Undercut"]},
    ],
}
