#!/usr/bin/env python3
"""
Wording lab: the render test from docs/measurements.md as one command.

A candidate file (tools/wortlabor/*.json, format photoshoot-wortlabor/1) lists
wordings to try against the bare word, in groups. This tool builds the prompt
each of them would get in a series - the example workflow's person, scene,
lighting, style and template, composed by the pack's own builders and the
Build Prompt node, with the candidate in its slot - and queues one render per
candidate and seed on a running ComfyUI. With --bogen it then lays the
results out as comparison sheets: rows are the candidates, columns the seeds,
at most six rows to a sheet so each stays readable on a phone. With
--einzeln it also saves every render on its own as a JPG. The verdict is the
user's; nothing here touches PRESETS.

    python3 tools/wortlabor.py tools/wortlabor/selfie.json
    python3 tools/wortlabor.py tools/wortlabor/orte.json --gruppe A --bogen
    python3 tools/wortlabor.py tools/wortlabor/selfie2.json --bogen --einzeln
    python3 tools/wortlabor.py tools/wortlabor/selfie.json --nur-zeigen
    python3 tools/wortlabor.py tools/wortlabor/selfie.json --nur-bogen --ausgabe ~/ComfyUI/output
    python3 tools/wortlabor.py --pruefen      # every candidate file, offline (tests/smoke.py)

Options:
    --gruppe A [--gruppe B]  only these groups
    --server URL             default http://127.0.0.1:8188 (or $PHOTOSHOOT_SERVER)
    --refine                 add the second pass (1.5x upscale, refine at 0.44),
                             as in the Render subgraph; default is pass 1 only
    --modelle FILE           model names {"UNET": ..., "CLIP": ..., "VAE": ...};
                             default tools/modelle.local.json when it exists,
                             else the Comfy-Org names the example ships with
    --nur-zeigen             print the prompt of every candidate, queue nothing
    --bogen                  after queueing, wait for the renders and write the
                             comparison sheets (needs Pillow)
    --nur-bogen              write the sheets from renders already there,
                             queue nothing
    --einzeln [PX]           also save every render on its own as a JPG, long
                             edge PX (default 1000), quality 80; with --bogen or
                             --nur-bogen, or alone (then it waits like --bogen)
    --zeilen N               candidate rows per sheet (default 6); a group with
                             more is split into sheets A1, A2, ... keeping the
                             candidates of one label together, and a control row
                             that stands for the whole group goes on every sheet
    --ausgabe DIR            ComfyUI's output folder: read the images from disk
                             instead of fetching them through /history and /view
    --ziel DIR               where sheets and single images go
                             (default tests/_tmp/wortlabor/<file>/ in this checkout)

Sheets are named after group, part and pass: bogen_A1_pass1.png, and
bogen_A1_refine.png for a --refine run, so the two passes never overwrite each
other; single images go to einzeln/<group>/<candidate>_s<seed>_<pass>.jpg next
to them. The tool prints the full path of everything it writes.

The render graph is the Render subgraph of tools/baue_workflow.py, flattened
into API format: node types, sampler settings and wiring come from its
RENDER_NODES / RENDER_LINKS, the loaders from its NODES, so a change there
reaches the lab too. Every graph is checked against the core-node snapshot
(tools/object_info.core.json) before anything is queued.

The renders themselves land in ComfyUI's output folder as
wortlabor/<file>/<group>/<candidate id>_s<seed>_00001_.png, with a _refine
before the counter for a --refine run.

Developer tooling: needs a running ComfyUI with the Krea 2 models for the
renders; tools/ is not part of the registry package (.comfyignore).
"""

import argparse
import importlib
import importlib.util
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

WURZEL = pathlib.Path(__file__).resolve().parent.parent
LABOR_ORDNER = WURZEL / "tools" / "wortlabor"
FORMAT = "photoshoot-wortlabor/1"
TMP = WURZEL / "tests" / "_tmp" / "wortlabor"

# Candidate slot (the template's English placeholder) -> Build Prompt input.
# scene and lighting start from the base (the example's scene and light) and
# can be replaced like the others: the location candidates (orte.json) put
# their set into the scene and leave the light empty.
SLOTS = {"camera": "kamera", "expression": "ausdruck", "style": "stil", "pose": "pose",
         "scene": "szene", "lighting": "lighting"}


def _bw():
    """tools/baue_workflow.py as a module: the example's states, the render
    subgraph, the model names and the snapshot loader live there."""
    if "baue_workflow" in sys.modules:
        return sys.modules["baue_workflow"]
    spec = importlib.util.spec_from_file_location("baue_workflow", WURZEL / "tools" / "baue_workflow.py")
    modul = importlib.util.module_from_spec(spec)
    sys.modules["baue_workflow"] = modul
    spec.loader.exec_module(modul)
    return modul


def _nodes(name):
    _bw().lade_kit()
    return importlib.import_module("krea2kit.nodes." + name)


# ─────────────────────────────────────────────────────────────────────────────
# The candidate file
# ─────────────────────────────────────────────────────────────────────────────
def lade_labor(pfad):
    """Read and check a candidate file. Errors are SystemExit with the reason."""
    pfad = pathlib.Path(pfad)
    try:
        labor = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit("%s: not readable (%s)" % (pfad, e))
    fehler = []
    if labor.get("format") != FORMAT:
        fehler.append("format must be %r" % FORMAT)
    seeds = labor.get("seeds")
    if not (isinstance(seeds, list) and seeds and all(isinstance(s, int) and s >= 0 for s in seeds)):
        fehler.append("seeds: a list of non-negative integers")
    if labor.get("bildformat") not in _nodes("shooting").RATIOS:
        fehler.append("bildformat: one of %s" % ", ".join(_nodes("shooting").RATIOS))
    gruppen = labor.get("gruppen") or []
    if not gruppen:
        fehler.append("no gruppen")
    ids, gids = set(), set()
    for g in gruppen:
        if not g.get("id") or g["id"] in gids:
            fehler.append("group without id or twice: %r" % g.get("id"))
        gids.add(g.get("id"))
        for slot in (g.get("feste") or {}):
            if slot not in SLOTS:
                fehler.append("%s: unknown slot %r in feste" % (g.get("id"), slot))
        if not g.get("kandidaten"):
            fehler.append("%s: no kandidaten" % g.get("id"))
        for k in g.get("kandidaten") or []:
            kid = k.get("id")
            if not kid or kid in ids or not all(c.isalnum() or c in "-_" for c in kid):
                fehler.append("candidate id missing, twice or not a file name: %r" % kid)
            ids.add(kid)
            zusatz = k["zusatz"] if "zusatz" in k else g.get("zusatz")
            if zusatz and (g.get("slot") not in BUILDER or not zusatz.get("feld")):
                fehler.append("%s: zusatz needs a builder slot and a feld" % kid)
            for slot in (k.get("feste") or {}):
                if slot not in SLOTS:
                    fehler.append("%s: unknown slot %r in feste" % (kid, slot))
            if (k.get("slot") or g.get("slot")) not in SLOTS:
                fehler.append("%s: slot must be one of %s" % (kid, ", ".join(SLOTS)))
            if not k.get("label") or "wortlaut" not in k:
                fehler.append("%s: label and wortlaut are required" % kid)
    if fehler:
        raise SystemExit("%s:\n  %s" % (pfad, "\n  ".join(fehler)))
    labor["_datei"] = pfad.stem
    labor["_kandidaten"] = {k["id"]: k for g in gruppen for k in g["kandidaten"]}
    return labor


def masse(labor):
    """The render size: the pack's own ratio arithmetic at the default edge."""
    sh = _nodes("shooting")
    return sh.masse_fuer(labor["bildformat"], int(labor.get("kante") or sh.KANTE_STANDARD))


def basis(labor):
    """The base texts, as the example workflow's nodes would produce them:
    Wardrobe -> Person Builder -> person_data, Lighting and Style builders at
    seed 0, the scene text and the prompt template."""
    b = labor.get("basis") or {}
    if b.get("von", "beispiel-workflow") != "beispiel-workflow":
        raise SystemExit("basis.von: only 'beispiel-workflow' is known")
    bw = _bw()
    kit = bw.lade_kit()
    zustand = b.get("zustaende") or {}
    m = kit.NODE_CLASS_MAPPINGS
    garderobe = m["Krea2Wardrobe"]().build(json.dumps(zustand.get("wardrobe", bw.WARDROBE_STATE)))[0]
    _, person_data = m["Krea2PersonBuilder"]().build(
        json.dumps(zustand.get("person", bw.PERSON_STATE)), garderobe)
    return {
        "person_data": person_data,
        "licht": m["Krea2LightingBuilder"]().build(0, json.dumps(zustand.get("lighting", bw.LIGHTING_STATE)))[0],
        "stil": m["Krea2StyleBuilder"]().build(0, json.dumps(zustand.get("style", bw.STYLE_STATE)))[0],
        "szene": b.get("szene", bw.SZENE),
        "vorlage": b.get("vorlage", bw.VORLAGE),
        "bildausschnitt": b.get("bildausschnitt", "Porträt"),
        "kamera_mit_ausschnitt": bool(b.get("kamera_mit_ausschnitt")),
    }


def _preset(slot, ref):
    """Built-in entries as their builder composes them: "stimmung/Breites
    Lachen", or a list of such for several fields of one builder
    (["stimmung/Warmes Lächeln", "blick/In die Kamera"])."""
    if isinstance(ref, list):
        if slot == "camera":
            return ", ".join(_preset(slot, r) for r in ref)
        werte = {}
        for r in ref:
            cat, _, label = r.partition("/")
            werte[cat] = _preset_wert(slot, cat, label, r)
        return _compose(slot)(werte, "")
    cat, _, label = ref.partition("/")
    if slot == "camera":
        # A framing ("kamera/Porträt", or the bare label as before) or an
        # adopted perspective ("perspektive/Selfie auf Augenhöhe").
        sh = _nodes("shooting")
        tabelle = dict(sh.PERSPEKTIVE if cat == "perspektive" else sh.KAMERA)
        if label not in tabelle:
            raise SystemExit("preset %r: no %s %r" % (ref, "perspective" if cat == "perspektive" else "framing", label))
        return tabelle[label]
    return _compose(slot)({cat: _preset_wert(slot, cat, label, ref)}, "")


BUILDER = {"expression": ("expression_builder", "compose_expression"),
           "pose": ("pose_builder", "compose_pose"),
           "style": ("style_builder", "compose_style"),
           "scene": ("location_builder", "compose_location")}


def _compose(slot):
    modul, funktion = BUILDER[slot]
    return getattr(_nodes(modul), funktion)


def _preset_wert(slot, cat, label, ref):
    """The prompt value of a built-in label - built-ins only, no custom entries."""
    modul = BUILDER[slot][0]
    wert = dict(_nodes(modul).PRESETS.get(cat) or []).get(label)
    if not wert:
        raise SystemExit("preset %r: not in %s.PRESETS" % (ref, modul))
    return wert


def aufloesen(wert, slot, labor, b, tiefe=0):
    """A slot value: text, {"kandidat": id}, {"preset": "cat/Label"} or {"basis": true}."""
    if isinstance(wert, str):
        return wert
    if not isinstance(wert, dict) or tiefe > 5:
        raise SystemExit("cannot read slot value %r" % (wert,))
    if "kandidat" in wert:
        k = labor["_kandidaten"].get(wert["kandidat"])
        if not k:
            raise SystemExit("unknown candidate %r" % wert["kandidat"])
        return aufloesen(k["wortlaut"], slot, labor, b, tiefe + 1)
    if "preset" in wert:
        return _preset(slot, wert["preset"])
    if wert.get("basis"):
        return {"style": b["stil"], "scene": b["szene"], "lighting": b["licht"]}.get(slot, "")
    raise SystemExit("cannot read slot value %r" % (wert,))


def auftraege(labor, nur_gruppen=None):
    """One entry per candidate: its group, the slot, the resolved wording and
    the finished prompt - the same text for every seed."""
    b = basis(labor)
    sh = _nodes("shooting")
    join = _nodes("store").Krea2PromptJoin()
    raus = []
    for g in labor["gruppen"]:
        if nur_gruppen and g["id"] not in nur_gruppen:
            continue
        for k in g["kandidaten"]:
            slot = k.get("slot") or g["slot"]
            werte = {"camera": "", "expression": "", "pose": "", "style": b["stil"],
                     "scene": b["szene"], "lighting": b["licht"]}
            # The group's fixed slots, then the candidate's own (a mirror
            # selfie cannot look into the lens and at the screen at once).
            for s, w in dict(g.get("feste") or {}, **(k.get("feste") or {})).items():
                werte[s] = aufloesen(w, s, labor, b)
            wortlaut = aufloesen(k["wortlaut"], slot, labor, b)
            werte[slot] = wortlaut
            # The group's zusatz: builder fields composed together with the
            # candidate, as a series sends mood and gaze in one expression
            # ({"feld": "stimmung", "preset": ["blick/In die Kamera"]}). Only
            # for candidates in the group's slot; "zusatz": null opts out.
            # "texte" puts a text (or another candidate's wording) into a field
            # - a time of day on a place that is itself still a candidate.
            zusatz = k["zusatz"] if "zusatz" in k else g.get("zusatz")
            if zusatz and slot == g["slot"]:
                felder = {}
                for ref in zusatz.get("preset") or []:
                    cat, _, label = ref.partition("/")
                    felder[cat] = _preset_wert(slot, cat, label, ref)
                for cat, w in (zusatz.get("texte") or {}).items():
                    felder[cat] = aufloesen(w, slot, labor, b)
                felder[zusatz["feld"]] = wortlaut
                werte[slot] = _compose(slot)(felder, "")
            slotwert = werte[slot]
            ausschnitt = k.get("bildausschnitt") or g.get("bildausschnitt") or b["bildausschnitt"]
            if ausschnitt not in dict(sh.KAMERA):
                raise SystemExit("%s: bildausschnitt %r is no framing" % (k["id"], ausschnitt))
            # The Series' own framing wording in front of the camera slot, the
            # way the Series appends its perspective to it (ROADMAP F4).
            if b["kamera_mit_ausschnitt"]:
                werte["camera"] = ", ".join(t for t in (dict(sh.KAMERA)[ausschnitt], werte["camera"]) if t)
            # The person block shortened for the framing, as the series does it.
            person = sh._person_fuer_kamera(b["person_data"], ausschnitt)
            prompt = join.join(text=b["vorlage"], person_1=person,
                               **{SLOTS[s]: v for s, v in werte.items()})["result"][0]
            raus.append({"gruppe": g, "kandidat": k, "slot": slot, "wortlaut": wortlaut,
                         "slotwert": slotwert,
                         "prompt": prompt, "bildausschnitt": ausschnitt})
    if nur_gruppen:
        unbekannt = set(nur_gruppen) - {g["id"] for g in labor["gruppen"]}
        if unbekannt:
            raise SystemExit("no such group: %s" % ", ".join(sorted(unbekannt)))
    return raus


def praefix(labor, gruppe, kandidat, seed, refine=False):
    """The render's filename_prefix. A --refine run gets its own, so the two
    passes of a candidate never stand under one name."""
    return "wortlabor/%s/%s/%s_s%d%s" % (labor["_datei"], gruppe["id"], kandidat["id"], seed,
                                         "_refine" if refine else "")


def durchgang(refine):
    """The pass as it appears in file names: pass1 or refine."""
    return "refine" if refine else "pass1"


def _ist_render(dateiname, stamm):
    """Is this ComfyUI's file for exactly this prefix (stamm_00001_.png) -
    not the refine render of the same candidate (stamm_refine_00001_.png)?"""
    return re.fullmatch(re.escape(stamm) + r"_\d{5,}_\.png", dateiname) is not None


# ─────────────────────────────────────────────────────────────────────────────
# The render graph in API format
# ─────────────────────────────────────────────────────────────────────────────
PRIMITIV = {"INT", "FLOAT", "STRING", "COMBO", "BOOLEAN"}
# Widgets that carry a hidden control_after_generate value right after them.
MIT_STEUERUNG = {"seed", "noise_seed"}


def _widgets_als_inputs(typ, widgets, oi):
    """A UI node's widgets_values as named API inputs, by the input order in
    /object_info (widget inputs only, the seed's control value skipped)."""
    namen = []
    for bereich in ("required", "optional"):
        for name, spec in (oi[typ]["input"].get(bereich) or {}).items():
            opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
            if spec[0] in PRIMITIV and not opts.get("forceInput"):
                namen.append(name)
    werte, i = {}, 0
    for name in namen:
        if i >= len(widgets):
            break
        werte[name] = widgets[i]
        i += 2 if name in MIT_STEUERUNG else 1
    if i != len(widgets):
        raise SystemExit("%s: %d widget values do not match the inputs %s"
                         % (typ, len(widgets), namen))
    return werte


def modellnamen(pfad=None):
    """UNET/CLIP/VAE: the given file, else tools/modelle.local.json (the same
    override baue_workflow.py --lokal uses), else the shipped Comfy-Org names."""
    bw = _bw()
    namen = {"UNET": bw.UNET, "CLIP": bw.CLIP, "VAE": bw.VAE}
    quelle = pathlib.Path(pfad) if pfad else (bw.LOKAL_MODELLE if bw.LOKAL_MODELLE.exists() else None)
    if quelle:
        try:
            eigene = json.loads(quelle.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise SystemExit("%s: not readable (%s)" % (quelle, e))
        namen.update({k: v for k, v in eigene.items() if k in namen and v})
    return namen, quelle


def api_graph(prompt, breite, hoehe, seed, dateipraefix, refine, modelle, oi):
    """The example's render path as one API-format prompt: loaders, then the
    Render subgraph with its inputs filled in and the refine switch resolved,
    then Save Image."""
    bw = _bw()
    graph = {}
    lader = {"UNETLoader": "UNET", "CLIPLoader": "CLIP", "VAELoader": "VAE"}
    aus_id = {}
    for nid, typ, _pos, _size, widgets, _titel in bw.NODES:
        if typ in lader or typ == "SaveImage":
            werte = _widgets_als_inputs(typ, widgets, oi)
            if typ in lader:
                werte[next(iter(werte))] = modelle[lader[typ]]
            else:
                werte["filename_prefix"] = dateipraefix
            graph[str(nid)] = {"class_type": typ, "inputs": werte}
            aus_id[typ] = str(nid)
    # What the Series and the loaders feed the subgraph's inputs.
    von_aussen = {"model": [aus_id["UNETLoader"], 0], "clip": [aus_id["CLIPLoader"], 0],
                  "vae": [aus_id["VAELoader"], 0], "prompt": prompt, "width": breite,
                  "height": hoehe, "seed": seed, "refine": refine}

    schalter = {}
    for nid, typ, _pos, _size, widgets, _titel in bw.RENDER_NODES:
        if typ in bw.NUR_FRONTEND:
            continue
        if typ == "ComfySwitchNode":
            schalter[nid] = {}
            continue
        graph[str(nid)] = {"class_type": typ,
                           "inputs": _widgets_als_inputs(typ, widgets, oi) if widgets else {}}

    sig = bw.signaturen(oi)

    def ausgang(von, name):
        typ = graph[str(von)]["class_type"]
        return [str(von), [n for n, _ in sig[typ][1]].index(name)]

    # The switch first: which of its inputs the refine value picks.
    for von, aus, nach, ein in bw.RENDER_LINKS:
        if nach in schalter:
            schalter[nach][ein] = (von, aus)
    for nid, eingaenge in schalter.items():
        wahl = eingaenge["switch"]
        if wahl[0] != bw.SUB_EIN or wahl[1] != "refine":
            raise SystemExit("the render switch is no longer driven by refine - update wortlabor.py")
        schalter[nid] = eingaenge["on_true" if refine else "on_false"]

    bild = None
    for von, aus, nach, ein in bw.RENDER_LINKS:
        if nach in schalter:
            continue
        if von in schalter:
            von, aus = schalter[von]
        quelle = von_aussen[aus] if von == bw.SUB_EIN else ausgang(von, aus)
        if nach == bw.SUB_AUS:
            bild = quelle
        else:
            graph[str(nach)]["inputs"][ein] = quelle
    graph[aus_id["SaveImage"]]["inputs"]["images"] = bild

    # Without refine the upscale and pass 2 feed nothing: keep only what the
    # saved image depends on, or ComfyUI would still run them.
    noetig, offen = set(), [aus_id["SaveImage"]]
    while offen:
        nid = offen.pop()
        if nid in noetig:
            continue
        noetig.add(nid)
        offen += [v[0] for v in graph[nid]["inputs"].values() if isinstance(v, list)]
    return {nid: graph[nid] for nid in sorted(graph, key=int) if nid in noetig}


def pruefe_api(graph, oi):
    """Check an API graph against /object_info signatures: known types, known
    and complete inputs, links to existing outputs of the right type, literal
    values of the right kind. Returns a list of errors."""
    sig = _bw().signaturen(oi)
    fehler = []
    art = {"INT": int, "FLOAT": (int, float), "STRING": str, "COMBO": str, "BOOLEAN": bool}
    for nid, n in graph.items():
        typ = n["class_type"]
        if typ not in oi:
            fehler.append("%s: unknown type %s" % (nid, typ))
            continue
        ein, _ = sig[typ]
        for name in oi[typ]["input"].get("required") or {}:
            if name not in n["inputs"]:
                fehler.append("%s %s: required input %s missing" % (nid, typ, name))
        for name, wert in n["inputs"].items():
            soll = ein.get(name)
            if soll is None:
                fehler.append("%s %s: no input %s" % (nid, typ, name))
            elif isinstance(wert, list):
                q = graph.get(wert[0])
                if not q or not (0 <= wert[1] < len(sig[q["class_type"]][1])):
                    fehler.append("%s %s.%s: link to a missing output %s" % (nid, typ, name, wert))
                elif sig[q["class_type"]][1][wert[1]][1] != soll:
                    fehler.append("%s %s.%s: %s delivers %s, wants %s" % (
                        nid, typ, name, q["class_type"], sig[q["class_type"]][1][wert[1]][1], soll))
            elif soll not in art or not isinstance(wert, art[soll]) or (soll != "BOOLEAN" and isinstance(wert, bool)):
                fehler.append("%s %s.%s: %r is no %s" % (nid, typ, name, wert, soll))
    return fehler


# ─────────────────────────────────────────────────────────────────────────────
# Talking to ComfyUI
# ─────────────────────────────────────────────────────────────────────────────
def _anfrage(server, pfad, daten=None, roh=False):
    body = json.dumps(daten).encode("utf-8") if daten is not None else None
    req = urllib.request.Request(server + pfad, data=body,
                                 headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            inhalt = r.read()
    except urllib.error.HTTPError as e:
        inhalt = e.read()
        try:
            return e.code, json.loads(inhalt)
        except ValueError:
            return e.code, inhalt.decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        raise SystemExit("No ComfyUI at %s (%s). Start it, or pass --server." % (server, e))
    return 200, (inhalt if roh else json.loads(inhalt))


def einreihen(server, jobs, client_id):
    """POST every graph to /prompt. Stops at the first rejection and prints
    what the server said - they would all fail the same way."""
    for i, job in enumerate(jobs, 1):
        code, antwort = _anfrage(server, "/prompt", {"prompt": job["graph"], "client_id": client_id})
        if code != 200 or antwort.get("node_errors"):
            print("\nComfyUI rejected %s (HTTP %d):" % (job["praefix"], code))
            print(json.dumps(antwort, indent=2, ensure_ascii=False))
            raise SystemExit(1)
        job["prompt_id"] = antwort["prompt_id"]
        print("[%d/%d] queued %s" % (i, len(jobs), job["praefix"]))


def warten(server, jobs):
    """Poll /history until every queued prompt is done; attach its images."""
    offen = {j["prompt_id"]: j for j in jobs}
    start, gemeldet = time.time(), 0
    while offen:
        for pid in list(offen):
            code, h = _anfrage(server, "/history/" + pid)
            if code != 200 or pid not in h:
                continue
            job = offen.pop(pid)
            status = (h[pid].get("status") or {}).get("status_str")
            job["bilder"] = [b for aus in (h[pid].get("outputs") or {}).values()
                             for b in aus.get("images") or [] if b.get("type") == "output"]
            if status == "error" or not job["bilder"]:
                grund = [m[1] for m in (h[pid].get("status") or {}).get("messages") or []
                         if m and m[0] == "execution_error"]
                print("  failed: %s (%s)" % (job["praefix"], "%s: %s" % (
                    grund[0].get("node_type"), grund[0].get("exception_message", "").strip()[:160])
                    if grund else status))
        fertig = len(jobs) - len(offen)
        if fertig != gemeldet:
            gemeldet = fertig
            print("  finished %d/%d  (%.0f s)" % (fertig, len(jobs), time.time() - start))
        if offen:
            time.sleep(2)


def _suche_in_history(server, jobs):
    """--nur-bogen without --ausgabe: the newest image of every prefix in the
    server's history."""
    code, h = _anfrage(server, "/history?max_items=10000")
    if code != 200:
        raise SystemExit("GET /history failed (HTTP %d)" % code)
    for job in jobs:
        ordner, _, stamm = job["praefix"].rpartition("/")
        treffer = [b for eintrag in h.values() for aus in (eintrag.get("outputs") or {}).values()
                   for b in aus.get("images") or []
                   if b.get("type") == "output" and b.get("subfolder") == ordner
                   and _ist_render(b.get("filename", ""), stamm)]
        job["bilder"] = sorted(treffer, key=lambda b: b["filename"])[-1:]


def _suche_auf_platte(ausgabe, jobs):
    for job in jobs:
        ordner, _, stamm = job["praefix"].rpartition("/")
        dateien = sorted(d for d in (ausgabe / ordner).glob(stamm + "_*.png") if _ist_render(d.name, stamm))
        job["datei"] = dateien[-1] if dateien else None


# ─────────────────────────────────────────────────────────────────────────────
# The comparison sheet
# ─────────────────────────────────────────────────────────────────────────────
# The poster palette (docs/posters): near-black ground, dark cards, orange accent.
GRUND, KARTE, RAND = (13, 15, 20), (21, 24, 33), (38, 42, 54)
WEISS, GRAU, AKZENT = (236, 238, 242), (150, 156, 170), (240, 140, 50)
SCHRIFTEN = {
    False: ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf", "Arial.ttf"],
    True: ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
           "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
           "C:/Windows/Fonts/arialbd.ttf", "Arial Bold.ttf"],
}


def _pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise SystemExit("The sheet needs Pillow. Run this with ComfyUI's Python (it has it), "
                         "or: pip install pillow")
    return Image, ImageDraw, ImageFont


def _schrift(groesse, fett=False):
    _, _, ImageFont = _pil()
    for name in SCHRIFTEN[fett]:
        try:
            return ImageFont.truetype(name, groesse)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=groesse)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def _umbrechen(zeichnen, text, schrift, breite):
    zeilen, zeile = [], ""
    for wort in text.split():
        probe = (zeile + " " + wort).strip()
        if zeichnen.textlength(probe, font=schrift) <= breite or not zeile:
            zeile = probe
        else:
            zeilen.append(zeile)
            zeile = wort
    return zeilen + ([zeile] if zeile else [])


def _kurz(wert):
    """A fixed slot value for the sheet's header: the text, or what it refers to."""
    if isinstance(wert, str):
        return wert or "(empty)"
    if "kandidat" in wert:
        return "candidate %s" % wert["kandidat"]
    if "preset" in wert:
        p = wert["preset"]
        return "preset %s" % (" + ".join(p) if isinstance(p, list) else p)
    return "base"


ZEILEN = 6


def bogen_teile(gruppe, zeilen=ZEILEN):
    """The group's candidates split into sheets of at most `zeilen` rows.

    The candidates of one label stay together (a perspective with its two
    wordings and its bare word), unless that block alone is longer. A control
    row whose label no other candidate carries stands for the whole group
    (the "Breites Lachen" every selfie expression is judged against), so it
    goes at the end of every sheet. A group that fits on one sheet stays one
    part in the file's own order (orte.json H sets each full set, a control
    with a label of its own, next to its short form)."""
    kandidaten = gruppe["kandidaten"]
    if len(kandidaten) <= zeilen:
        return [list(kandidaten)]
    labels = [k["label"] for k in kandidaten if not k.get("kontrolle")]
    fuer_alle = [k for k in kandidaten if k.get("kontrolle") and k["label"] not in labels]
    rest = [k for k in kandidaten if k not in fuer_alle]
    platz = max(1, zeilen - len(fuer_alle))
    bloecke = []
    for k in rest:
        if bloecke and bloecke[-1][-1]["label"] == k["label"]:
            bloecke[-1].append(k)
        else:
            bloecke.append([k])
    teile = []
    for block in bloecke:
        while len(block) > platz:
            teile.append(block[:platz])
            block = block[platz:]
        if teile and len(teile[-1]) + len(block) <= platz:
            teile[-1] = teile[-1] + block
        else:
            teile.append(list(block))
    return [t + fuer_alle for t in teile] or [list(fuer_alle)]


def bogen_name(gruppe, teil, teile, refine):
    """bogen_A_pass1.png for a group on one sheet, bogen_A2_refine.png for
    the second of several of a --refine run."""
    return "bogen_%s%s_%s.png" % (gruppe["id"], teil + 1 if teile > 1 else "", durchgang(refine))


def bogen(labor, gruppe, jobs, bild_von, ziel, kandidaten=None, teil="", refine=False):
    """One sheet: a row per candidate (label, wording, control marked), a
    column per seed. bild_von(job) returns a PIL image or None. kandidaten:
    the rows of this sheet (default the whole group), teil: "(1/3)" in the
    title."""
    Image, ImageDraw, _ = _pil()
    seeds = labor["seeds"]
    zellen_b = 300
    w, h = masse(labor)
    zellen_h = int(zellen_b * h / w)
    rand, luecke, text_b = 36, 14, 440
    kandidaten = list(kandidaten if kandidaten is not None else gruppe["kandidaten"])
    zeile_h = zellen_h + 2 * luecke
    breite = rand * 2 + text_b + len(seeds) * (zellen_b + luecke)

    titel, klein, label_s, text_s, marke = (_schrift(38, True), _schrift(20), _schrift(26, True),
                                            _schrift(21), _schrift(15, True))
    feste = ", ".join("%s = %s" % (s, _kurz(v)) for s, v in (gruppe.get("feste") or {}).items())
    unterzeile = "slot: %s  ·  %s %dx%d  ·  %s  ·  fixed: %s" % (
        gruppe["slot"], labor["bildformat"], w, h,
        "pass 1 + refine" if refine else "pass 1", feste or "—")
    if (labor.get("basis") or {}).get("kamera_mit_ausschnitt"):
        unterzeile += "  ·  camera = the framing's wording, then the value"
    # The header grows with the lines the fixed slots need.
    unterzeilen = _umbrechen(ImageDraw.Draw(Image.new("RGB", (1, 1))), unterzeile, klein,
                             breite - 2 * rand)
    kopf_h = 160 + 28 * len(unterzeilen)
    hoehe = kopf_h + len(kandidaten) * (zeile_h + luecke) + rand
    bild = Image.new("RGB", (breite, hoehe), GRUND)
    z = ImageDraw.Draw(bild)

    z.text((rand, rand), "WORDING LAB · %s · %s %s%s" % (labor.get("name", labor["_datei"]).upper(),
                                                       gruppe["id"], gruppe.get("titel", ""),
                                                       " " + teil if teil else ""),
           font=titel, fill=WEISS)
    for i, zeile in enumerate(unterzeilen):
        z.text((rand, rand + 54 + 28 * i), zeile, font=klein, fill=GRAU)
    for i, s in enumerate(seeds):
        x = rand + text_b + i * (zellen_b + luecke)
        z.text((x + 4, kopf_h - 40), "seed %d" % s, font=klein, fill=GRAU)
    z.line((rand, kopf_h - 12, breite - rand, kopf_h - 12), fill=RAND, width=2)

    nach_id = {(j["kandidat"]["id"], j["seed"]): j for j in jobs}
    wortlaute = {j["kandidat"]["id"]: j["slotwert"] for j in jobs}
    ausschnitte = {j["kandidat"]["id"]: j["bildausschnitt"] for j in jobs}
    y = kopf_h
    for k in kandidaten:
        kontrolle = bool(k.get("kontrolle"))
        z.rounded_rectangle((rand - 12, y, breite - rand + 12, y + zeile_h), radius=10,
                            fill=KARTE, outline=AKZENT if kontrolle else RAND, width=2)
        ty = y + luecke + 6
        for zeile in _umbrechen(z, k["label"], label_s, text_b - 40):
            z.text((rand + 6, ty), zeile, font=label_s, fill=WEISS)
            ty += 34
        marken = ([k["id"], k.get("slot") or gruppe["slot"], ausschnitte.get(k["id"], "")]
                  + (["CONTROL"] if kontrolle else []))
        mx = rand + 6
        for m in marken:
            tb = z.textlength(m, font=marke)
            farbe = AKZENT if m == "CONTROL" else GRAU
            z.rounded_rectangle((mx, ty + 4, mx + tb + 14, ty + 28), radius=5, outline=farbe, width=1)
            z.text((mx + 7, ty + 8), m, font=marke, fill=farbe)
            mx += tb + 24
        ty += 44
        text = "“%s”" % wortlaute.get(k["id"], "")
        if k.get("feste"):
            text += "  (%s)" % ", ".join("%s = %s" % (s, _kurz(v)) for s, v in k["feste"].items())
        for zeile in _umbrechen(z, text, text_s, text_b - 40):
            if ty > y + zeile_h - 30:
                z.text((rand + 6, ty), "…", font=text_s, fill=GRAU)
                break
            z.text((rand + 6, ty), zeile, font=text_s, fill=(200, 204, 214))
            ty += 29
        for i, s in enumerate(seeds):
            x = rand + text_b + i * (zellen_b + luecke)
            job = nach_id.get((k["id"], s))
            b = bild_von(job) if job else None
            if b is None:
                z.rectangle((x, y + luecke, x + zellen_b, y + luecke + zellen_h), fill=GRUND, outline=RAND)
                z.text((x + 20, y + luecke + zellen_h // 2), "missing", font=klein, fill=GRAU)
                continue
            b = b.convert("RGB")
            b.thumbnail((zellen_b, zellen_h))
            bild.paste(b, (x + (zellen_b - b.width) // 2, y + luecke + (zellen_h - b.height) // 2))
        y += zeile_h + luecke
    ziel.parent.mkdir(parents=True, exist_ok=True)
    bild.save(ziel)
    return ziel


def ausgeben(labor, jobs, args):
    """The sheets (--bogen, --nur-bogen) and the single images (--einzeln),
    into --ziel or tests/_tmp/wortlabor/<file>/, whichever way the images
    arrive (from disk with --ausgabe, else through /view)."""
    Image, _, _ = _pil()
    import io

    if args.ausgabe:
        def bild_von(job):
            return Image.open(job["datei"]) if job.get("datei") else None
    else:
        cache = {}

        def bild_von(job):
            if not job.get("bilder"):
                return None
            b = job["bilder"][-1]
            schluessel = (b["subfolder"], b["filename"])
            if schluessel not in cache:
                q = urllib.parse.urlencode({"filename": b["filename"], "subfolder": b["subfolder"],
                                            "type": b["type"]})
                code, roh = _anfrage(args.server, "/view?" + q, roh=True)
                cache[schluessel] = Image.open(io.BytesIO(roh)) if code == 200 else None
            return cache[schluessel]

    ordner = (pathlib.Path(args.ziel).expanduser() if args.ziel else TMP / labor["_datei"]).resolve()
    geschrieben = 0
    if args.bogen or args.nur_bogen:
        for g in labor["gruppen"]:
            eigene = [j for j in jobs if j["gruppe"] is g]
            if not eigene:
                continue
            teile = bogen_teile(g, args.zeilen)
            for i, kandidaten in enumerate(teile):
                ids = {k["id"] for k in kandidaten}
                hier = [j for j in eigene if j["kandidat"]["id"] in ids]
                pfad = bogen(labor, g, hier, bild_von, ordner / bogen_name(g, i, len(teile), args.refine),
                             kandidaten, "(%d/%d)" % (i + 1, len(teile)) if len(teile) > 1 else "",
                             args.refine)
                fehlen = sum(1 for j in hier if bild_von(j) is None)
                print("sheet %s%s" % (pfad, "  (%d missing)" % fehlen if fehlen else ""))
                geschrieben += 1
    if args.einzeln:
        n = einzeln_schreiben(jobs, bild_von, ordner / "einzeln", args.einzeln, args.refine)
        print("%d single images (JPG, long edge %d px) in %s" % (n, args.einzeln, ordner / "einzeln"))
    if geschrieben:
        print("%d sheets in %s" % (geschrieben, ordner))


def einzeln_schreiben(jobs, bild_von, ordner, kante, refine):
    """Every render on its own, long edge `kante`, JPG quality 80:
    einzeln/<group>/<candidate>_s<seed>_<pass>.jpg - big enough to judge a
    face on a phone, small enough to push."""
    Image, _, _ = _pil()
    n = 0
    for job in jobs:
        b = bild_von(job)
        if b is None:
            continue
        b = b.convert("RGB")
        faktor = float(kante) / max(b.size)
        if faktor < 1:
            b = b.resize((max(1, round(b.width * faktor)), max(1, round(b.height * faktor))),
                         Image.LANCZOS)
        ziel = ordner / job["gruppe"]["id"] / ("%s_s%d_%s.jpg" % (job["kandidat"]["id"], job["seed"],
                                                                 durchgang(refine)))
        ziel.parent.mkdir(parents=True, exist_ok=True)
        b.save(ziel, "JPEG", quality=80, optimize=True)
        n += 1
    return n


# ─────────────────────────────────────────────────────────────────────────────
def jobs_fuer(labor, args, oi):
    breite, hoehe = masse(labor)
    modelle, _ = modellnamen(args.modelle)
    jobs = []
    for a in auftraege(labor, args.gruppe):
        for seed in labor["seeds"]:
            p = praefix(labor, a["gruppe"], a["kandidat"], seed, args.refine)
            graph = api_graph(a["prompt"], breite, hoehe, seed, p, args.refine, modelle, oi)
            fehler = pruefe_api(graph, oi)
            if fehler:
                raise SystemExit("%s: the graph does not match the node signatures:\n  %s"
                                 % (p, "\n  ".join(fehler)))
            jobs.append(dict(a, seed=seed, praefix=p, graph=graph))
    return jobs


def zeigen(labor, args):
    breite, hoehe = masse(labor)
    modelle, quelle = modellnamen(args.modelle)
    print("%s: %s %dx%d, seeds %s, %s, models %s"
          % (labor["_datei"], labor["bildformat"], breite, hoehe,
             ", ".join(map(str, labor["seeds"])), "pass 1 + refine" if args.refine else "pass 1 only",
             quelle or "Comfy-Org names"))
    for a in auftraege(labor, args.gruppe):
        k = a["kandidat"]
        print("\n[%s %s] %s  ·  %s%s  ·  person for %s"
              % (a["gruppe"]["id"], a["gruppe"].get("titel", ""), k["id"], k["label"],
                 " (control)" if k.get("kontrolle") else "", a["bildausschnitt"]))
        print("  %s <- %s" % (a["slot"], a["slotwert"]))
        print("  " + a["prompt"])


def pruefen():
    """Offline check of every candidate file: loads, every group builds, each
    candidate's wording is in its own prompt exactly once, and every API graph
    (with and without refine) matches the core-node snapshot."""
    bw = _bw()
    oi = bw.lade_object_info()
    dateien = sorted(LABOR_ORDNER.glob("*.json"))
    if not dateien:
        raise SystemExit("no candidate files in %s" % LABOR_ORDNER)
    for datei in dateien:
        labor = lade_labor(datei)
        alle = auftraege(labor)
        assert {a["gruppe"]["id"] for a in alle} == {g["id"] for g in labor["gruppen"]}
        for a in alle:
            n = a["prompt"].count(a["wortlaut"])
            assert a["wortlaut"] and n == 1, "%s: wording %d times in its prompt" % (a["kandidat"]["id"], n)
            # An empty slot must leave no debris behind (Build Prompt cleans up).
            t = a["prompt"]
            assert t[:1].isalnum() and not t.rstrip().endswith(",") and ", ," not in t, t[:80]
        # The sheets: every candidate on a sheet, in order, one label's
        # candidates together, no sheet over ZEILEN rows unless one label
        # alone is longer; the two passes never share a file name.
        for g in labor["gruppen"]:
            teile = bogen_teile(g)
            fuer_alle = [k for k in teile[0] if all(k in t for t in teile)] if len(teile) > 1 else []
            reihe = [k for t in teile for k in t if k not in fuer_alle] + fuer_alle
            assert [k["id"] for k in reihe] == [k["id"] for k in g["kandidaten"] if k not in fuer_alle] \
                + [k["id"] for k in fuer_alle], g["id"]
            bloecke = {}
            for k in g["kandidaten"]:
                bloecke[k["label"]] = bloecke.get(k["label"], 0) + 1
            for t in teile:
                assert len(t) <= max([ZEILEN] + [bloecke[k["label"]] + len(fuer_alle) for k in t]), (g["id"], len(t))
            namen = {bogen_name(g, i, len(teile), r) for i in range(len(teile)) for r in (False, True)}
            assert len(namen) == 2 * len(teile), namen
        assert _ist_render("a_s1_00001_.png", "a_s1") and not _ist_render("a_s1_refine_00001_.png", "a_s1")
        breite, hoehe = masse(labor)
        modelle = {"UNET": bw.UNET, "CLIP": bw.CLIP, "VAE": bw.VAE}
        for refine in (False, True):
            g = api_graph(alle[0]["prompt"], breite, hoehe, labor["seeds"][0], "x", refine, modelle, oi)
            fehler = pruefe_api(g, oi)
            assert not fehler, fehler
            typen = sorted(n["class_type"] for n in g.values())
            assert ("LatentUpscaleBy" in typen) == refine and typen.count("KSampler") == 1 + refine, typen
        print("%s: %d groups, %d candidates, %d renders, %d sheets, graphs ok"
              % (datei.relative_to(WURZEL), len(labor["gruppen"]), len(alle), len(alle) * len(labor["seeds"]),
                 sum(len(bogen_teile(g)) for g in labor["gruppen"])))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Wording lab: render candidate wordings side by side.")
    ap.add_argument("datei", nargs="?", help="candidate file, e.g. tools/wortlabor/selfie.json")
    ap.add_argument("--gruppe", action="append", help="only this group (repeatable)")
    ap.add_argument("--server", default=os.environ.get("PHOTOSHOOT_SERVER") or "http://127.0.0.1:8188")
    ap.add_argument("--refine", action="store_true", help="add the second pass")
    ap.add_argument("--modelle", help="JSON with UNET/CLIP/VAE file names")
    ap.add_argument("--nur-zeigen", action="store_true", help="print the prompts, queue nothing")
    ap.add_argument("--bogen", action="store_true", help="wait for the renders, then write the sheets")
    ap.add_argument("--nur-bogen", action="store_true", help="sheets from existing renders only")
    ap.add_argument("--einzeln", nargs="?", const=1000, type=int, metavar="PX",
                    help="also save every render as a JPG, long edge PX (default 1000)")
    ap.add_argument("--zeilen", type=int, default=ZEILEN, help="candidate rows per sheet (default 6)")
    ap.add_argument("--ausgabe", type=pathlib.Path, help="ComfyUI's output folder")
    ap.add_argument("--ziel", help="folder for sheets and single images "
                                   "(default tests/_tmp/wortlabor/<file>/)")
    ap.add_argument("--pruefen", action="store_true", help="offline check of all candidate files")
    args = ap.parse_args()
    args.server = args.server.rstrip("/")
    if args.ausgabe:
        args.ausgabe = args.ausgabe.expanduser()

    if args.pruefen:
        return pruefen()
    if not args.datei:
        ap.error("a candidate file is required")
    labor = lade_labor(args.datei)
    if args.nur_zeigen:
        zeigen(labor, args)
        return 0
    if args.zeilen < 1 or (args.einzeln is not None and args.einzeln < 64):
        ap.error("--zeilen must be at least 1, --einzeln at least 64 px")
    if args.bogen or args.nur_bogen or args.einzeln:
        _pil()  # fail before an hour of rendering, not after

    oi = _bw().lade_object_info()
    jobs = jobs_fuer(labor, args, oi)
    if args.nur_bogen:
        if args.ausgabe:
            _suche_auf_platte(args.ausgabe, jobs)
        else:
            _suche_in_history(args.server, jobs)
        ausgeben(labor, jobs, args)
        return 0

    modelle, quelle = modellnamen(args.modelle)
    print("%d renders on %s (%s, models: %s)" % (len(jobs), args.server,
          "pass 1 + refine" if args.refine else "pass 1 only", quelle or "Comfy-Org names"))
    einreihen(args.server, jobs, str(uuid.uuid4()))
    if not (args.bogen or args.einzeln):
        print("Queued. Sheets later: the same command with --nur-bogen%s."
              % (" --refine" if args.refine else ""))
        return 0
    try:
        warten(args.server, jobs)
    except KeyboardInterrupt:
        print("\nStopped waiting; the queue keeps rendering. Sheets later with --nur-bogen.")
        return 1
    if args.ausgabe:
        _suche_auf_platte(args.ausgabe, jobs)
    ausgeben(labor, jobs, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
