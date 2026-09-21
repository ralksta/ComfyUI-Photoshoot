"""
Writes the built-in list entries in the custom-entry format (nodes/eigene.py)
- a template to copy from when writing your own file.

    python3 tools/exportiere_presets.py                  # all builders -> stdout
    python3 tools/exportiere_presets.py lighting style   # only these
    python3 tools/exportiere_presets.py -o vorlage.json

Builders: person, pose, expression, lighting, style. The entries are built-in
labels, so importing this file unchanged adds nothing - every one of them
clashes with its original, and the original stays.
"""

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from nodes import eigene  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("builder", nargs="*", choices=["person", "pose", "expression", "lighting", "style"])
    ap.add_argument("-o", "--ausgabe", help="file instead of stdout")
    args = ap.parse_args()
    namen = args.builder or ["person", "pose", "expression", "lighting", "style"]
    daten = {"format": eigene.FORMAT, "name": "Built-in entries (template)", "entries": []}
    for n in namen:
        daten["entries"] += eigene.exportiere_kern(eigene.BUILDER[n])["entries"]
    text = json.dumps(daten, ensure_ascii=False, indent=1)
    if args.ausgabe:
        pathlib.Path(args.ausgabe).write_text(text + "\n", encoding="utf-8")
        print("%d entries -> %s" % (len(daten["entries"]), args.ausgabe), file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
