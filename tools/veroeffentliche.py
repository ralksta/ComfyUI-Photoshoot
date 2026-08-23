#!/usr/bin/env python3
"""
Pushes the current state to the public repository as a single commit.

    python3 tools/veroeffentliche.py            # shows what would happen
    python3 tools/veroeffentliche.py --wirklich # does it

Two repositories, one working directory:

  origin  ComfyUI-Photoshoot-dev   private, full history
  public  ComfyUI-Photoshoot       public, one commit per release

The public state is built from an orphan branch (git checkout --orphan): it has
no predecessor and therefore carries nothing over from the working history - no
commit messages, no intermediate states, no deleted files. On the far side it is
then set by force, because it is unrelated to the previous public commit.

What gets published is exactly what git tracks on the current branch. Whatever
.gitignore excludes stays out; uncommitted changes abort the run.
"""

import argparse
import re
import subprocess
import sys
import pathlib

WURZEL = pathlib.Path(__file__).resolve().parent.parent
OEFFENTLICH = "public"
ZWEIG = "veroeffentlichung"


def git(*args, pruefen=True):
    e = subprocess.run(["git", "-C", str(WURZEL), *args],
                       capture_output=True, text=True)
    if pruefen and e.returncode:
        raise SystemExit("git %s:\n%s%s" % (" ".join(args), e.stdout, e.stderr))
    return e.stdout.strip()


def version():
    text = (WURZEL / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else "unbekannt"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wirklich", action="store_true",
                    help="tatsaechlich pushen statt nur zu berichten")
    args = ap.parse_args()

    if git("status", "--porcelain"):
        raise SystemExit("Arbeitsverzeichnis nicht sauber - erst committen.")

    zweig_vorher = git("rev-parse", "--abbrev-ref", "HEAD")
    v = version()
    dateien = git("ls-files").splitlines()

    print("Version:        %s" % v)
    print("Dateien:        %d" % len(dateien))
    print("Ziel:           %s (%s)" % (OEFFENTLICH, git("remote", "get-url", OEFFENTLICH)))
    print("Aktueller Zweig: %s" % zweig_vorher)

    if not args.wirklich:
        print("\nProbelauf. Mit --wirklich ausfuehren.")
        return 0

    git("branch", "-D", ZWEIG, pruefen=False)
    git("checkout", "--orphan", ZWEIG)
    try:
        git("add", "-A")
        git("commit", "-q", "-m", "Photoshoot %s" % v)
        # --force, because the orphan commit shares no ancestor with the
        # previous public state.
        git("push", "--force", OEFFENTLICH, "%s:main" % ZWEIG)
        print("\nGepusht: %s -> %s main" % (v, OEFFENTLICH))
    finally:
        git("checkout", "-f", zweig_vorher)
        git("branch", "-D", ZWEIG, pruefen=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
