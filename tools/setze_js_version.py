#!/usr/bin/env python3
"""
Appends the package version to every import of one of our own .mjs files.

    python3 tools/setze_js_version.py

Why this is needed: ComfyUI serves the *.js files registered in WEB_DIRECTORY
with "cache-control: no-store", but the .mjs files sitting next to them only
with an ETag and no Cache-Control. Without Cache-Control a browser is allowed
to cache heuristically - typically a tenth of the time since Last-Modified. For
a two-week-old file that is a good day and a half in which the old interface
stays put, even though the server has long been serving the new one.

Thanks to no-store the loaders are always fetched fresh; if their import names
a new version, the browser fetches the .mjs again too.

The version lives in pyproject.toml. After every change to js/, raise it there
and run this script - otherwise users keep seeing the old interface after an
update.

What matters is that the same version stands everywhere: the same URL means one
module instance. With differing parameters the browser loads shared.mjs more
than once, and each copy would then have its own state - the translation table
set in one and empty in the other.
"""

import pathlib
import re
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
JS = WURZEL / "js"

# An import (static or dynamic) of a neighbouring .mjs, with or without a
# version already appended.
MUSTER = re.compile(r'(["\'])(\./[A-Za-z0-9_.-]+\.mjs)(\?v=[^"\']*)?\1')


def version():
    text = (WURZEL / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    if not m:
        raise SystemExit("Keine version in pyproject.toml gefunden")
    return m.group(1)


def main():
    v = version()
    geaendert = 0
    for pfad in sorted(JS.glob("*.js")) + sorted(JS.glob("*.mjs")):
        alt = pfad.read_text(encoding="utf-8")
        neu = MUSTER.sub(lambda m: '%s%s?v=%s%s' % (m.group(1), m.group(2), v, m.group(1)), alt)
        if neu != alt:
            pfad.write_text(neu, encoding="utf-8")
            geaendert += 1
            print("  %s" % pfad.relative_to(WURZEL))
    print("Version %s in %d Datei(en) gesetzt" % (v, geaendert))

    # Cross-check: no unversioned import of our own modules left over.
    offen = []
    for pfad in sorted(JS.glob("*.js")) + sorted(JS.glob("*.mjs")):
        for m in MUSTER.finditer(pfad.read_text(encoding="utf-8")):
            if not m.group(3):
                offen.append("%s: %s" % (pfad.name, m.group(2)))
    if offen:
        print("Ohne Version geblieben:", offen)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
