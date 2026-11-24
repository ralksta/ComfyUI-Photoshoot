#!/usr/bin/env python3
"""
Builds the Locations Reference Poster (17 built-in places across 4 families)
for docs/posters/photoshoot_locations_matrix_17.png (+ _web.jpg), matching
the Tops/Bottoms/Headwear matrix layout and two-pass Krea 2 workflow.

Works with any running ComfyUI — e.g. Google Colab via Cloudflare tunnel
(tools/colab_krea2_comfyui.ipynb) or local/tor ComfyUI:

    python3 tools/baue_location_poster.py --nur-zeigen
    python3 tools/baue_location_poster.py --server https://<url>.trycloudflare.com --comfy-org
    python3 tools/baue_location_poster.py --nur-poster
    python3 tools/baue_location_poster.py --nur-poster --thumbs

Nothing private is sent to the server: only the 17 built-in SFW English
location prompts on the README example person with 0 LoRAs.
"""

import argparse
import io
import os
import pathlib
import sys
import uuid

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

from nodes import i18n  # noqa: E402
from nodes import location_builder as LB  # noqa: E402
from nodes import shooting as SH  # noqa: E402
from nodes import vorschau as VS  # noqa: E402
from tools import baue_workflow as BW  # noqa: E402
from tools import wortlabor as WL  # noqa: E402

POSTER_DIR = WURZEL / "docs" / "posters"
CACHE_DIR = WURZEL / "tests" / "_tmp" / "location_poster"
MASTER_NAME = "photoshoot_locations_matrix_17.png"
WEB_NAME = "photoshoot_locations_matrix_17_web.jpg"

# Family order, English display badge & accent color (matches Photoshoot dark UI).
FAMILIEN_STIL = {
    "studio": ("STUDIO", (110, 86, 207)),
    "stadt":  ("URBAN", (43, 138, 158)),
    "natur":  ("NATURE", (47, 143, 91)),
    "innen":  ("INTERIOR", (194, 120, 50)),
}

# Master geometry (6 columns, 3529 px total width -> _web.jpg is 1764 px).
SPALTEN = 6
RAND = 34
LUECKE = 25
KACHEL_B = 556
KACHEL_H = 834        # exact 2:3 ratio
FUSS_H = 148
KOPF_H = 228
HINTERGRUND = (14, 14, 18)
KARTE_BG = (22, 23, 30)
KARTE_RAHMEN = (40, 42, 54)
TEXT_HELL = (242, 243, 247)
TEXT_GEDIMMT = (154, 158, 173)
PILL_BG = (30, 32, 42)
PILL_RAHMEN = (56, 60, 78)


def eintraege():
    """All 17 built-in locations in family order (studio, urban, nature, interior)."""
    wert_von = dict(LB.PRESETS["ort"])
    en_von = i18n.LOCATION["ort"]
    liste = []
    for fam in ("studio", "stadt", "natur", "innen"):
        for lbl in LB.ORT_GRUPPEN[fam]:
            liste.append({
                "id": VS.slug(lbl),
                "label": lbl,
                "en": en_von.get(lbl, lbl),
                "familie": fam,
                "wortlaut": wert_von[lbl],
            })
    return liste


def baue_prompts(seed=0):
    """Compose the 17 full-body prompts using the pack's own builders."""
    labor = {
        "bildformat": "2:3",
        "basis": {
            "von": "beispiel-workflow",
            "bildausschnitt": "Ganzkörper",
            "kamera_mit_ausschnitt": True,
        },
    }
    b = WL.basis(labor)
    join = WL._nodes("store").Krea2PromptJoin()
    ausschnitt = b["bildausschnitt"]
    kamera = dict(SH.KAMERA)[ausschnitt]
    person = SH._person_fuer_kamera(b["person_data"], ausschnitt)
    breite, hoehe = WL.masse(labor)

    liste = []
    for idx, e in enumerate(eintraege(), start=1):
        # Empty lighting slot so studio softbox does not compete with natural/outdoor sets
        werte = {
            "camera": kamera,
            "expression": "",
            "pose": "",
            "style": b["stil"],
            "scene": e["wortlaut"],
            "lighting": "",
        }
        prompt = join.join(
            text=b["vorlage"],
            person_1=person,
            **{WL.SLOTS[s]: v for s, v in werte.items()},
        )["result"][0]
        liste.append({
            **e,
            "nr": idx,
            "seed": seed,
            "breite": breite,
            "hoehe": hoehe,
            "prompt": prompt,
        })
    return liste


def _modelle(comfy_org=False, modelle_pfad=None):
    if comfy_org:
        return {"UNET": BW.UNET, "CLIP": BW.CLIP, "VAE": BW.VAE}
    namen, _ = WL.modellnamen(modelle_pfad)
    return namen


def _holen_aus_history(items, server, refine, cache_dir, warten_auf_rest=True):
    """Fetch finished renders from ComfyUI /history with retry on tunnel blips."""
    import json
    import time
    import urllib.parse
    import urllib.request

    cache_dir.mkdir(parents=True, exist_ok=True)
    durchgang = WL.durchgang(refine)
    ziel_von = {}
    stamm_von = {}
    for item in items:
        ziel = cache_dir / f"{item['nr']:02d}_{item['id']}_{durchgang}.png"
        item["datei"] = ziel
        ziel_von[item["nr"]] = ziel
        stamm = f"{item['nr']:02d}_{item['id']}_s{item['seed']}"
        if refine:
            stamm += "_refine"
        stamm_von[item["nr"]] = stamm

    def _get_json(pfad):
        for versuch in range(6):
            try:
                with urllib.request.urlopen(server + pfad, timeout=20) as r:
                    return json.loads(r.read().decode("utf-8"))
            except Exception as e:
                if versuch == 5:
                    raise
                time.sleep(2 * (versuch + 1))

    def _get_bytes(pfad):
        for versuch in range(6):
            try:
                with urllib.request.urlopen(server + pfad, timeout=60) as r:
                    return r.read()
            except Exception:
                if versuch == 5:
                    raise
                time.sleep(2 * (versuch + 1))

    while True:
        offene = [it for it in items if not (it["datei"].exists() and it["datei"].stat().st_size > 10_000)]
        if not offene:
            print(f"Alle {len(items)} Einzelbilder lokal gesichert!")
            return

        h = _get_json("/history?max_items=200")
        for it in offene:
            stamm = stamm_von[it["nr"]]
            treffer = [
                b
                for eintrag in h.values()
                for aus in (eintrag.get("outputs") or {}).values()
                for b in (aus.get("images") or [])
                if b.get("type") == "output"
                and b.get("subfolder") == "location_poster"
                and WL._ist_render(b.get("filename", ""), stamm)
            ]
            if not treffer:
                continue
            b = sorted(treffer, key=lambda x: x["filename"])[-1]
            q = urllib.parse.urlencode({
                "filename": b["filename"],
                "subfolder": b.get("subfolder", ""),
                "type": b.get("type", "output"),
            })
            roh = _get_bytes("/view?" + q)
            it["datei"].write_bytes(roh)
            print(f"  ✓ {it['nr']:02d}/17 {it['en']} -> {it['datei'].name}", flush=True)

        rest = [it for it in items if not (it["datei"].exists() and it["datei"].stat().st_size > 10_000)]
        if not rest or not warten_auf_rest:
            if rest:
                print(f"Noch {len(rest)} Bilder offen.")
            return
        time.sleep(8)


def _render_auf_server(items, server, refine, comfy_org, modelle_pfad, cache_dir):
    """Queue all missing renders on ComfyUI (Colab or local) and save locally."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    oi = BW.lade_object_info()
    modelle = _modelle(comfy_org=comfy_org, modelle_pfad=modelle_pfad)
    durchgang = WL.durchgang(refine)

    offene = []
    for item in items:
        ziel = cache_dir / f"{item['nr']:02d}_{item['id']}_{durchgang}.png"
        item["datei"] = ziel
        if ziel.exists() and ziel.stat().st_size > 10_000:
            continue
        praefix = f"location_poster/{item['nr']:02d}_{item['id']}_s{item['seed']}"
        if refine:
            praefix += "_refine"
        graph = WL.api_graph(
            item["prompt"], item["breite"], item["hoehe"],
            item["seed"], praefix, refine, modelle, oi,
        )
        fehler = WL.pruefe_api(graph, oi)
        if fehler:
            raise SystemExit("API-Graph-Fehler:\n" + "\n".join(fehler))
        offene.append({
            "item": item,
            "praefix": praefix,
            "graph": graph,
        })

    if not offene:
        print(f"Alle {len(items)} Einzelbilder bereits im Cache ({cache_dir}).")
        return

    print(f"Reihe {len(offene)} von {len(items)} Orten auf {server} ein ({durchgang}) ...")
    client_id = str(uuid.uuid4())
    WL.einreihen(server, offene, client_id)
    _holen_aus_history(items, server, refine, cache_dir, warten_auf_rest=True)


def _lade_schrift(groesse, fett=False):
    from PIL import ImageFont

    kandidaten = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if fett
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for p in kandidaten:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, groesse)
            except OSError:
                pass
    return ImageFont.load_default()


def _umbrechen(draw, text, font, max_breite, max_zeilen=3):
    woerter = text.split()
    zeilen, aktuell = [], ""
    for w in woerter:
        probe = f"{aktuell} {w}".strip()
        if draw.textlength(probe, font=font) <= max_breite or not aktuell:
            aktuell = probe
        else:
            zeilen.append(aktuell)
            aktuell = w
    if aktuell:
        zeilen.append(aktuell)
    if len(zeilen) > max_zeilen:
        zeilen = zeilen[:max_zeilen]
        while len(zeilen[-1]) > 4 and draw.textlength(zeilen[-1] + "…", font=font) > max_breite:
            zeilen[-1] = zeilen[-1][:-1].rstrip()
        zeilen[-1] += "…"
    return zeilen


def _cover_crop(im, ziel_b, ziel_h):
    from PIL import Image

    w, h = im.size
    soll = ziel_b / ziel_h
    ist = w / h
    if ist > soll:
        neu_w = int(round(h * soll))
        x0 = (w - neu_w) // 2
        im = im.crop((x0, 0, x0 + neu_w, h))
    elif ist < soll:
        neu_h = int(round(w / soll))
        y0 = (h - neu_h) // 2
        im = im.crop((0, y0, w, y0 + neu_h))
    return im.resize((ziel_b, ziel_h), Image.LANCZOS)


def baue_poster(items, refine, cache_dir, poster_dir):
    """Stitch the 17 rendered tiles into master PNG + half-size _web.jpg."""
    from PIL import Image, ImageDraw

    durchgang = WL.durchgang(refine)
    zeilen = (len(items) + SPALTEN - 1) // SPALTEN
    karte_h = KACHEL_H + FUSS_H
    gesamt_b = RAND * 2 + SPALTEN * KACHEL_B + (SPALTEN - 1) * LUECKE
    gesamt_h = KOPF_H + zeilen * karte_h + (zeilen - 1) * LUECKE + RAND

    canvas = Image.new("RGB", (gesamt_b, gesamt_h), HINTERGRUND)
    draw = ImageDraw.Draw(canvas)

    # Header logo: crisp contact-sheet emblem matching docs/logo.svg
    logo_x = RAND
    logo_y = 46
    s = 1.45  # scale factor from logo.svg's 80x80 icon grid
    # 4 outline frames
    for rx, ry, rw, rh in ((0, 0, 30, 42), (38, 0, 42, 42), (0, 50, 42, 30), (50, 50, 30, 30)):
        draw.rounded_rectangle(
            (logo_x + int(rx * s), logo_y + int(ry * s),
             logo_x + int((rx + rw) * s), logo_y + int((ry + rh) * s)),
            radius=6, outline=(138, 143, 152), width=4,
        )
    # Highlighted coral frame (#f66744) with portrait silhouette
    hx0, hy0 = logo_x + int(38 * s), logo_y
    hx1, hy1 = logo_x + int(80 * s), logo_y + int(42 * s)
    draw.rounded_rectangle((hx0, hy0, hx1, hy1), radius=6, fill=(246, 103, 68))
    cx, cy, cr = logo_x + int(59 * s), logo_y + int(15 * s), int(6 * s)
    draw.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(27, 29, 33))
    sx0, sy0 = logo_x + int(45 * s), logo_y + int(28 * s)
    sx1, sy1 = logo_x + int(73 * s), logo_y + int(56 * s)
    draw.pieslice((sx0, sy0, sx1, sy1), start=180, end=360, fill=(27, 29, 33))
    text_x = logo_x + int(80 * s) + 32

    f_titel = _lade_schrift(60, fett=True)
    f_sub = _lade_schrift(25, fett=False)
    f_pill = _lade_schrift(18, fett=True)
    f_karte = _lade_schrift(24, fett=True)
    f_badge = _lade_schrift(16, fett=True)
    f_wort = _lade_schrift(17, fett=False)

    draw.text((text_x, 42), "LOCATIONS MATRIX", font=f_titel, fill=TEXT_HELL)
    draw.text(
        (text_x, 112),
        "17 render-tested places across 4 families, full body on the README person",
        font=f_sub,
        fill=TEXT_GEDIMMT,
    )

    # Header pills
    px = text_x
    py = 152
    for label in ("17 PLACES", "4 FAMILIES", "COMFYUI-PHOTOSHOOT"):
        tw = draw.textlength(label, font=f_pill)
        pw = int(tw + 26)
        ph = 32
        draw.rounded_rectangle((px, py, px + pw, py + ph), radius=6, fill=PILL_BG, outline=PILL_RAHMEN, width=2)
        draw.text((px + 13, py + 6), label, font=f_pill, fill=(195, 198, 214))
        px += pw + 12

    # Subtle separator line
    draw.line((RAND, KOPF_H - 18, gesamt_b - RAND, KOPF_H - 18), fill=(32, 34, 44), width=2)

    # Cards
    for idx, item in enumerate(items):
        r, c = divmod(idx, SPALTEN)
        x0 = RAND + c * (KACHEL_B + LUECKE)
        y0 = KOPF_H + r * (karte_h + LUECKE)

        bild_pfad = item.get("datei") or (cache_dir / f"{item['nr']:02d}_{item['id']}_{durchgang}.png")
        if not bild_pfad.exists():
            raise SystemExit(f"Einzelbild fehlt: {bild_pfad}")

        draw.rectangle((x0, y0, x0 + KACHEL_B, y0 + karte_h), fill=KARTE_BG, outline=KARTE_RAHMEN, width=2)
        im = Image.open(bild_pfad).convert("RGB")
        kachel = _cover_crop(im, KACHEL_B, KACHEL_H)
        canvas.paste(kachel, (x0, y0))

        # Footer text + colored family badge
        fy = y0 + KACHEL_H + 14
        fam_label, fam_farbe = FAMILIEN_STIL[item["familie"]]
        bw_badge = int(draw.textlength(fam_label, font=f_badge) + 20)
        bh_badge = 26
        bx0 = x0 + KACHEL_B - 16 - bw_badge
        draw.rounded_rectangle((bx0, fy + 2, bx0 + bw_badge, fy + 2 + bh_badge), radius=5, fill=fam_farbe)
        draw.text((bx0 + 10, fy + 6), fam_label, font=f_badge, fill=(255, 255, 255))

        draw.text((x0 + 16, fy), item["en"], font=f_karte, fill=TEXT_HELL)

        zeilen_txt = _umbrechen(draw, f'"{item["wortlaut"]}"', f_wort, KACHEL_B - 32, max_zeilen=3)
        ty = fy + 38
        for z in zeilen_txt:
            draw.text((x0 + 16, ty), z, font=f_wort, fill=TEXT_GEDIMMT)
            ty += 24

    poster_dir.mkdir(parents=True, exist_ok=True)
    master_pfad = poster_dir / MASTER_NAME
    web_pfad = poster_dir / WEB_NAME
    canvas.save(master_pfad, "PNG", optimize=True)

    web = canvas.resize((gesamt_b // 2, gesamt_h // 2), Image.LANCZOS)
    web.save(web_pfad, "JPEG", quality=86, progressive=True, optimize=True)
    print(f"\nMaster-Poster: {master_pfad} ({gesamt_b}x{gesamt_h})")
    print(f"Web-Poster:    {web_pfad} ({gesamt_b // 2}x{gesamt_h // 2})")


def schreibe_thumbs(items, refine, cache_dir):
    """Optional: export 150x200 JPEG UI thumbnails to js/vorschau/ort/."""
    from PIL import Image

    durchgang = WL.durchgang(refine)
    ziel_dir = pathlib.Path(VS.WURZEL) / "ort"
    ziel_dir.mkdir(parents=True, exist_ok=True)
    for item in items:
        bild_pfad = item.get("datei") or (cache_dir / f"{item['nr']:02d}_{item['id']}_{durchgang}.png")
        im = Image.open(bild_pfad).convert("RGB")
        thumb = _cover_crop(im, 150, 200)
        thumb.save(ziel_dir / f"{item['id']}.jpg", "JPEG", quality=80, progressive=True, optimize=True)
    print(f"UI-Thumbnails: {len(items)} Dateien nach {ziel_dir}")


def main():
    ap = argparse.ArgumentParser(description="Render & stitch the 17-place Locations Reference Poster.")
    ap.add_argument("--server", default=os.environ.get("PHOTOSHOOT_SERVER", "http://127.0.0.1:8188"),
                    help="ComfyUI server URL (e.g. Colab Cloudflare tunnel URL)")
    ap.add_argument("--comfy-org", action="store_true",
                    help="Use default Comfy-Org model filenames (recommended for Colab)")
    ap.add_argument("--modelle", help="Optional JSON file overriding UNET/CLIP/VAE filenames")
    ap.add_argument("--seed", type=int, default=0, help="Seed for all 17 renders (default: 0)")
    ap.add_argument("--kein-refine", action="store_true",
                    help="Pass 1 only (faster draft test; default is Two-Pass Refine)")
    ap.add_argument("--nur-zeigen", action="store_true",
                    help="Dry-run: print all 17 composed prompts and exit without rendering")
    ap.add_argument("--nur-poster", action="store_true",
                    help="Skip rendering and stitch poster from cached images")
    ap.add_argument("--abholen", action="store_true",
                    help="Do not queue new jobs; fetch already-queued renders from /history and stitch")
    ap.add_argument("--thumbs", action="store_true",
                    help="Also export 150x200 Studio UI thumbnails to js/vorschau/ort/")
    ap.add_argument("--cache", type=pathlib.Path, default=CACHE_DIR,
                    help="Directory for cached individual PNG renders")
    args = ap.parse_args()

    refine = not args.kein_refine
    items = baue_prompts(seed=args.seed)

    if args.nur_zeigen:
        print(f"=== {len(items)} Location-Prompts (seed={args.seed}, refine={refine}, {items[0]['breite']}x{items[0]['hoehe']}) ===\n")
        for it in items:
            print(f"[{it['nr']:02d}] {it['familie']:<6} | {it['en']} ({it['label']})")
            print(f"     {it['prompt']}\n")
        return

    if args.abholen:
        _holen_aus_history(items, server=args.server.rstrip("/"), refine=refine, cache_dir=args.cache, warten_auf_rest=True)
    elif not args.nur_poster:
        _render_auf_server(
            items,
            server=args.server.rstrip("/"),
            refine=refine,
            comfy_org=args.comfy_org,
            modelle_pfad=args.modelle,
            cache_dir=args.cache,
        )

    baue_poster(items, refine=refine, cache_dir=args.cache, poster_dir=POSTER_DIR)
    if args.thumbs:
        schreibe_thumbs(items, refine=refine, cache_dir=args.cache)


if __name__ == "__main__":
    main()
