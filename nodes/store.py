"""
Building-block store - keep persons, scenes and styles around and reuse them,
plus a node that substitutes them into a prompt.

Save / load (one pair per store, same handling):

  Save / load person   ComfyUI/user/krea2_persons/
  Save / load scene    ComfyUI/user/krea2_scenes/
  Save / load style    ComfyUI/user/krea2_styles/

For the person pair the text arrives over a wire from the Person Builder; for
scene and style you type it straight into the node - hence a multiline field
there instead of a forced input.

Assembling:

  Build prompt   Substitutes {person1} {person2} {person3} {kamera} {pose}
                 {ausdruck} {szene} {stil} {extra}. Recommended order:
                 {kamera}, {szene}, {person}, {pose}, {extra}, {ausdruck},
                 {stil} - framing and room before the person. {extra} is for
                 optional packs (empty means nothing).

Note: the dropdowns are filled when ComfyUI asks for the node info. A freshly
saved block therefore only shows up after a refresh (R).
"""

import json
import os
import re
import time

import folder_paths

LEER = "— nichts gespeichert —"

# kind -> (subfolder, display name, field name, does the text arrive by wire?)
#
# "prompt" stores the fully assembled text - what falls out of the back of
# "build prompt". That lets you keep a combination that worked under a name and
# send it straight back into the engine later, without digging it out of the
# image metadata.
ARTEN = {
    "person": ("krea2_persons", "Person", "person", True),
    "szene":  ("krea2_scenes",  "Szene",  "szene",  False),
    "stil":   ("krea2_styles",  "Stil",   "stil",   False),
    "licht":  ("krea2_lights",  "Licht",  "licht",  False),
    "prompt": ("krea2_prompts", "Prompt", "prompt", True),
}

# {extra}: a block from an optional add-on pack. This package knows only the
# placeholder, never the content. With no pack and no wire it stays empty and
# disappears during cleanup - existing workflows are unaffected.
PLATZHALTER = ("person1", "person2", "person3", "kamera", "pose", "ausdruck",
                "licht", "szene", "stil", "extra")

# English spellings of the same placeholders. The interface may be in English,
# and German placeholders in the prompt text are a stumbling block there. The
# German ones stay valid - saved prompts keep working unchanged.
ALIASE = {
    "camera": "kamera",
    "expression": "ausdruck",
    "lighting": "licht",
    "light": "licht",
    "beleuchtung": "licht",
    "scene": "szene",
    "style": "stil",
    # {person} without a digit means the first person: a common typo, and the
    # obvious spelling when there is only one person anyway.
    "person": "person1",
}


def _dir(art):
    pfad = os.path.join(folder_paths.get_user_directory(), ARTEN[art][0])
    os.makedirs(pfad, exist_ok=True)
    return pfad


def _safe_name(name):
    """Reduce to what is safe to use as a file name.

    Guards against "../" and directory separators - the name comes from a free
    text field and would otherwise end up in a path unchecked.
    """
    name = re.sub(r"[^\w\s-]", "", (name or "").strip(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", name).strip()[:80]


def _list(art):
    try:
        namen = [f[:-5] for f in os.listdir(_dir(art)) if f.endswith(".json")]
    except OSError:
        namen = []
    return sorted(namen, key=str.lower)


def _pfad(art, name):
    """Path to the stored file - the name always goes through _safe_name.

    On reads too: the name does come from a dropdown that ComfyUI checks
    against the list, but a hand-built workflow walks straight past that. A
    name that _safe_name empties out cannot hit a file.
    """
    sauber = _safe_name(name)
    if not sauber:
        raise ValueError("unbrauchbarer Name")
    return os.path.join(_dir(art), sauber + ".json")


def _read(art, name):
    with open(_pfad(art, name), "r", encoding="utf-8") as fh:
        return json.load(fh).get("text", "")


def _make_save(art):
    _, titel, feld, per_kabel = ARTEN[art]

    class Save:
        @classmethod
        def INPUT_TYPES(cls):
            if per_kabel:
                textfeld = ("STRING", {"forceInput": True})
            else:
                textfeld = ("STRING", {"multiline": True, "default": "",
                                       "placeholder": "Text fuer diesen Baustein"})
            return {"required": {
                feld: textfeld,
                "name": ("STRING", {"default": "", "multiline": False,
                                    "placeholder": "Name, z. B. Bibliothek abends"}),
                "speichern": ("BOOLEAN", {"default": False,
                                          "label_on": "speichern", "label_off": "aus"}),
            }}

        RETURN_TYPES = ("STRING",)
        RETURN_NAMES = (feld,)
        FUNCTION = "save"
        CATEGORY = "Photoshoot"
        DESCRIPTION = ("Legt den Text unter einem Namen ab. Schalter auf 'speichern' "
                       "stellen, einmal ausfuehren, danach wieder aus. Neue Namen "
                       "erscheinen im Lade-Node erst nach Refresh (R).")

        # Without this nothing happens: ComfyUI pulls execution backwards from
        # the output nodes. This node sits at the end of a dead branch - its
        # output normally goes nowhere - and would quietly drop out of the
        # execution plan. OUTPUT_NODE makes it a root node in its own right.
        OUTPUT_NODE = True

        # Otherwise ComfyUI serves the cached result for identical inputs and
        # never gets round to writing at all.
        @classmethod
        def IS_CHANGED(cls, **kw):
            return time.time() if kw.get("speichern") else False

        def save(self, **kw):
            text = kw.get(feld) or ""
            name = kw.get("name")
            if not kw.get("speichern"):
                return (text,)

            sauber = _safe_name(name)
            if not sauber:
                print("[Photoshoot %s] No usable name - nothing saved." % titel)
                return (text,)
            if not text.strip():
                print("[Photoshoot %s] Empty text - nothing saved." % titel)
                return (text,)

            pfad = _pfad(art, sauber)
            neu = not os.path.exists(pfad)
            with open(pfad, "w", encoding="utf-8") as fh:
                json.dump({"name": sauber, "art": art, "text": text,
                           "gespeichert": time.strftime("%Y-%m-%d %H:%M:%S")},
                          fh, ensure_ascii=False, indent=2)

            print("[Photoshoot %s] %s: %s" % (titel, "created" if neu else "updated", pfad))
            return (text,)

    Save.__name__ = "Krea2%sSave" % art.capitalize()
    return Save


def _make_load(art):
    _, titel, feld, _ = ARTEN[art]

    class Load:
        @classmethod
        def INPUT_TYPES(cls):
            namen = _list(art)
            return {"required": {feld: (namen if namen else [LEER],)}}

        RETURN_TYPES = ("STRING",)
        RETURN_NAMES = (feld,)
        FUNCTION = "load"
        CATEGORY = "Photoshoot"
        DESCRIPTION = "Gibt den Text eines gespeicherten Bausteins aus."

        # If the file on disk changes, the node has to run again.
        @classmethod
        def IS_CHANGED(cls, **kw):
            try:
                return os.path.getmtime(_pfad(art, kw.get(feld)))
            except (OSError, TypeError, ValueError):
                return 0.0

        def load(self, **kw):
            name = kw.get(feld)
            if not name or name == LEER:
                return ("",)
            try:
                return (_read(art, name),)
            except (OSError, ValueError) as e:
                print("[Photoshoot %s] '%s' could not be read: %s" % (titel, name, e))
                return ("",)

    Load.__name__ = "Krea2%sLoad" % art.capitalize()
    return Load


KEINE = "—"


class Krea2Bausteine:
    """Four dropdowns, four outputs - replaces four separate load nodes."""

    @classmethod
    def INPUT_TYPES(cls):
        # Here every list needs an empty entry: unlike the separate nodes, a
        # dropdown cannot simply be unplugged when you only want one person in
        # the image.
        personen = [KEINE] + _list("person")
        return {"required": {
            "person_1": (personen,),
            "person_2": (personen,),
            "szene": ([KEINE] + _list("szene"),),
            "stil": ([KEINE] + _list("stil"),),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("person_1", "person_2", "szene", "stil")
    FUNCTION = "waehlen"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Waehlt zwei Personen, eine Szene und einen Stil aus den "
                   "gespeicherten Bausteinen. Neue Eintraege erscheinen erst "
                   "nach Refresh (R).")

    @classmethod
    def IS_CHANGED(cls, person_1, person_2, szene, stil):
        # If any of the four files on disk changes, run again.
        stempel = []
        for art, name in (("person", person_1), ("person", person_2),
                          ("szene", szene), ("stil", stil)):
            try:
                stempel.append(os.path.getmtime(_pfad(art, name)))
            except (OSError, TypeError, ValueError):
                stempel.append(0.0)
        return stempel

    def _hole(self, art, name):
        if not name or name == KEINE or name == LEER:
            return ""
        try:
            return _read(art, name)
        except (OSError, ValueError) as e:
            print("[Photoshoot] '%s' could not be read: %s" % (name, e))
            return ""

    def waehlen(self, person_1, person_2, szene, stil):
        return (self._hole("person", person_1), self._hole("person", person_2),
                self._hole("szene", szene), self._hole("stil", stil))


def _aufraeumen(text):
    """Clean up the debris that placeholders left empty leave behind.

    Without this the prompt reads " , , sitting on a desk", or a line with
    nothing but a full stop left on it - both would otherwise reach the text
    encoder.
    """
    zeilen = []
    for zeile in text.splitlines():
        z = re.sub(r"[ \t]+", " ", zeile).strip()
        z = re.sub(r"(?:,\s*){2,}", ", ", z)   # ", , ," -> ", "
        z = re.sub(r"\s+([,;.])", r"\1", z)    # " ," -> ","
        z = re.sub(r",\s*(?=[.;:!?])", "", z)  # "a woman,." -> "a woman."
        z = re.sub(r"\.\s*(?=\.)", "", z)      # ".." -> "."
        z = re.sub(r"^[,;.\s]+", "", z)        # leading punctuation
        zeilen.append("" if z in (",", ".", ";") else z)
    text = "\n".join(zeilen)
    text = re.sub(r"\n{3,}", "\n\n", text)     # collapse runs of blank lines
    return text.strip().strip(",").strip()


class Krea2PromptJoin:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"text": ("STRING", {"forceInput": True})},
            "optional": {
                "person_1": ("STRING", {"forceInput": True}),
                "person_2": ("STRING", {"forceInput": True}),
                "person_3": ("STRING", {"forceInput": True}),
                "kamera": ("STRING", {"forceInput": True}),
                "pose": ("STRING", {"forceInput": True}),
                "ausdruck": ("STRING", {"forceInput": True}),
                "licht": ("STRING", {"forceInput": True}),
                "lighting": ("STRING", {"forceInput": True}),
                "szene": ("STRING", {"forceInput": True}),
                "stil": ("STRING", {"forceInput": True}),
                # A block from an optional add-on pack. This package does not
                # know the content, only the {extra} placeholder.
                "extra": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "join"
    CATEGORY = "Photoshoot"
    DESCRIPTION = ("Ersetzt {person1} {person2} {person3} {kamera} {pose} {ausdruck} "
                   "{licht} {szene} {stil} {extra}. Empfohlen: {kamera}, {szene}, {licht}, "
                   "{person}, {pose}, {extra}, {ausdruck}, {stil}. {extra} optional für "
                   "Erweiterungs-Packs. Ohne Platzhalter: Kamera/Szene/Licht vor Person.")

    def join(self, text, person_1="", person_2="", person_3="", kamera="",
             pose="", ausdruck="", licht="", lighting="", szene="", stil="", extra=""):
        werte = {"person1": person_1 or "", "person2": person_2 or "",
                 "person3": person_3 or "", "kamera": kamera or "",
                 "pose": pose or "",
                 "ausdruck": ausdruck or "",
                 "licht": licht or lighting or "",
                 "szene": szene or "", "stil": stil or "",
                 "extra": extra or ""}
        basis = text or ""

        # Map the English spellings onto the internal names first, so that
        # below there is only ever one set of placeholders.
        for engl, intern in ALIASE.items():
            basis = re.sub(r"\{%s\}" % engl, "{%s}" % intern, basis)

        if any("{%s}" % p in basis for p in PLATZHALTER):
            for p in PLATZHALTER:
                basis = basis.replace("{%s}" % p, werte[p])
        else:
            # No placeholder: framing, room and lighting before the person.
            vorn = [werte[p] for p in ("kamera", "szene", "licht",
                                       "person1", "person2", "person3",
                                       "pose", "extra", "ausdruck") if werte[p]]
            hinten = [werte[p] for p in ("stil",) if werte[p]]
            basis = ". ".join(vorn + ([basis] if basis.strip() else []) + hinten)

        return (_aufraeumen(basis),)


# Die Klassen entstehen in der Schleife, die Namen stehen darunter ausgeschrieben.
_KLASSEN = {art: (_make_save(art), _make_load(art)) for art in ARTEN}

NODE_CLASS_MAPPINGS = {
    "Krea2PersonSave": _KLASSEN["person"][0],
    "Krea2PersonLoad": _KLASSEN["person"][1],
    "Krea2SzeneSave":  _KLASSEN["szene"][0],
    "Krea2SzeneLoad":  _KLASSEN["szene"][1],
    "Krea2StilSave":   _KLASSEN["stil"][0],
    "Krea2StilLoad":   _KLASSEN["stil"][1],
    "Krea2LichtSave":  _KLASSEN["licht"][0],
    "Krea2LichtLoad":  _KLASSEN["licht"][1],
    "Krea2PromptSave": _KLASSEN["prompt"][0],
    "Krea2PromptLoad": _KLASSEN["prompt"][1],
    "Krea2Bausteine":  Krea2Bausteine,
    "Krea2PromptJoin": Krea2PromptJoin,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Krea2PersonSave": "Photoshoot Person speichern",
    "Krea2PersonLoad": "Photoshoot Person laden",
    "Krea2SzeneSave":  "Photoshoot Szene speichern",
    "Krea2SzeneLoad":  "Photoshoot Szene laden",
    "Krea2StilSave":   "Photoshoot Stil speichern",
    "Krea2StilLoad":   "Photoshoot Stil laden",
    "Krea2LichtSave":  "Photoshoot Licht speichern",
    "Krea2LichtLoad":  "Photoshoot Licht laden",
    "Krea2PromptSave": "Photoshoot Prompt speichern",
    "Krea2PromptLoad": "Photoshoot Prompt laden",
    "Krea2Bausteine":  "Photoshoot Bausteine wählen",
    "Krea2PromptJoin": "Photoshoot Prompt bauen",
}
