#!/usr/bin/env python3
"""
Publishes a released version to the Comfy Registry (registry.comfy.org).

    python3 tools/registry.py            # shows what would happen
    python3 tools/registry.py --wirklich # does it

Run it after tools/veroeffentliche.py --wirklich. It never uploads this
working directory: `comfy node publish` zips whatever git tracks in the current
directory, and here that is the dev state - without the 18+ filter that
veroeffentliche.py applies on the way to the public repo. Instead the script
checks out the release tag of the public repo (v<version>) into a temporary
worktree and publishes from there, so the registry gets exactly what GitHub
shows.

The token (a Personal Access Token of the publisher "ralksta") is read from
the environment variable COMFY_REGISTRY_TOKEN or from the file
~/.config/comfy-registry-token. It is never printed and never written into
the repository.

The changelog for the registry's Updates section is the CHANGELOG block of
the version, as in the GitHub release.
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from veroeffentliche import WURZEL, OEFFENTLICH, git, version, changelog_abschnitt

NODE_ID = "comfyui-photoshoot"
TOKEN_DATEI = pathlib.Path.home() / ".config" / "comfy-registry-token"


def token():
    t = os.environ.get("COMFY_REGISTRY_TOKEN", "").strip()
    if not t and TOKEN_DATEI.exists():
        t = TOKEN_DATEI.read_text(encoding="utf-8").strip()
    return t or None


def registry_version():
    """The latest version the registry has, or None if it cannot be asked."""
    try:
        with urllib.request.urlopen("https://api.comfy.org/nodes/%s" % NODE_ID, timeout=20) as r:
            return (json.load(r).get("latest_version") or {}).get("version")
    except Exception as e:
        print("Registry nicht erreichbar (%s)." % e)
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wirklich", action="store_true",
                    help="tatsaechlich hochladen statt nur zu berichten")
    args = ap.parse_args()

    v = version()
    tag = "v%s" % v
    git("fetch", "-q", OEFFENTLICH, "--tags", "--force")
    zeile = git("ls-remote", "--tags", OEFFENTLICH, "refs/tags/" + tag)
    if not zeile:
        raise SystemExit("Tag %s fehlt im Public-Repo - erst tools/veroeffentliche.py --wirklich." % tag)
    commit = zeile.split()[0]

    # The public tree has to be the filtered one and carry the same version.
    pyproject = git("show", "%s:pyproject.toml" % commit)
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    if not m or m.group(1) != v:
        raise SystemExit("pyproject.toml in %s nennt %s, nicht %s." % (tag, m and m.group(1), v))
    if "MINDESTALTER = 18" not in git("show", "%s:nodes/person_builder.py" % commit):
        raise SystemExit("%s traegt den 18+-Filter nicht - so geht nichts ins Registry." % tag)

    online = registry_version()
    notiz = changelog_abschnitt(v)
    t = token()

    print("Version:        %s" % v)
    print("Quelle:         %s @ %s (%s)" % (OEFFENTLICH, tag, commit[:7]))
    print("Registry hat:   %s" % (online or "unbekannt"))
    print("Changelog:      %s" % ("CHANGELOG-Abschnitt, %d Zeichen" % len(notiz) if notiz
                                   else "KEIN CHANGELOG-Eintrag fuer %s" % v))
    print("Token:          %s" % ("vorhanden" if t else
                                   "FEHLT (COMFY_REGISTRY_TOKEN oder %s)" % TOKEN_DATEI))

    if online == v:
        print("\n%s ist schon im Registry - nichts zu tun." % v)
        return 0
    if not t:
        raise SystemExit("\nKein Token - abgebrochen.")
    if not args.wirklich:
        print("\nProbelauf. Mit --wirklich ausfuehren.")
        return 0

    with tempfile.TemporaryDirectory(prefix="photoshoot-registry-") as tmp:
        baum = pathlib.Path(tmp) / "baum"
        git("worktree", "add", "-q", "--detach", str(baum), commit)
        try:
            log = pathlib.Path(tmp) / "changelog.md"
            log.write_text(notiz or "Siehe CHANGELOG.md.", encoding="utf-8")
            e = subprocess.run(["comfy", "node", "publish", "--token", t,
                                "--changelog-file", str(log)],
                               cwd=baum, capture_output=True, text=True)
            ausgabe = (e.stdout + e.stderr).replace(t, "***")
            print(ausgabe.strip())
            if e.returncode:
                raise SystemExit("comfy node publish ist fehlgeschlagen (Exit %d)." % e.returncode)
        finally:
            git("worktree", "remove", "--force", str(baum), pruefen=False)

    print("\nVeroeffentlicht: %s %s -> https://registry.comfy.org/nodes/%s" % (NODE_ID, v, NODE_ID))
    return 0


if __name__ == "__main__":
    sys.exit(main())
