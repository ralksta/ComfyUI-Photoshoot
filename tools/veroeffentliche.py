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
import shutil

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


def changelog_abschnitt(v):
    """The CHANGELOG block for this version, without its heading.

    Returns None when there is no entry - a release then gets a one-liner
    rather than the wrong version's notes.
    """
    text = (WURZEL / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^## \[%s\][^\n]*\n(.*?)(?=^## \[|\Z)"
                  % re.escape(v), text, re.M | re.S)
    return m.group(1).strip() if m else None


def veroeffentliche_release(v, commit, notiz):
    """Tag the orphan commit on the public repo and open a GitHub release.

    Deliberately after the push and deliberately non-fatal: the release is a
    shop window, the push is the delivery. If gh is missing or the tag is
    already there, say so and name the manual command instead of making a
    finished publish look failed.

    The public repo is built from orphan commits, so consecutive tags share no
    ancestor. The release notes are unaffected; only GitHub's "compare" view
    between two tags shows the whole tree as changed.
    """
    tag = "v%s" % v
    url = git("remote", "get-url", OEFFENTLICH)
    m = re.search(r"github\.com[:/](.+?)(?:\.git)?$", url)
    if not m:
        print("Kein GitHub-Repo in %s - Release uebersprungen." % url)
        return
    repo = m.group(1)

    if git("ls-remote", "--tags", OEFFENTLICH, "refs/tags/" + tag):
        print("Tag %s existiert schon - Release uebersprungen." % tag)
        return

    if not shutil.which("gh"):
        print("gh nicht gefunden. Release von Hand:\n"
              "  git push %s %s:refs/tags/%s\n"
              "  gh release create %s --repo %s --notes-file CHANGELOG.md"
              % (OEFFENTLICH, commit, tag, tag, repo))
        return

    git("push", OEFFENTLICH, "%s:refs/tags/%s" % (commit, tag))
    e = subprocess.run(["gh", "release", "create", tag, "--repo", repo,
                        "--title", "Photoshoot %s" % v, "--notes", notiz],
                       capture_output=True, text=True)
    if e.returncode:
        print("Tag %s gesetzt, Release fehlgeschlagen:\n%s%s\n"
              "Nachholen mit:\n  gh release create %s --repo %s"
              % (tag, e.stdout, e.stderr, tag, repo))
    else:
        print("Release:        %s" % e.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wirklich", action="store_true",
                    help="tatsaechlich pushen statt nur zu berichten")
    ap.add_argument("--ohne-release", action="store_true",
                    help="nur pushen, keinen Tag und kein GitHub-Release")
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

    notiz = changelog_abschnitt(v)
    print("Release-Notiz:  %s"
          % ("CHANGELOG-Abschnitt, %d Zeichen" % len(notiz) if notiz
             else "KEIN CHANGELOG-Eintrag fuer %s" % v))

    if not args.wirklich:
        print("\nProbelauf. Mit --wirklich ausfuehren.")
        return 0

    git("branch", "-D", ZWEIG, pruefen=False)
    git("checkout", "--orphan", ZWEIG)
    try:
        git("add", "-A")
        git("commit", "-q", "-m", "Photoshoot %s" % v)
        commit = git("rev-parse", "HEAD")
        # --force, because the orphan commit shares no ancestor with the
        # previous public state.
        git("push", "--force", OEFFENTLICH, "%s:main" % ZWEIG)
        print("\nGepusht: %s -> %s main" % (v, OEFFENTLICH))
        if not args.ohne_release:
            veroeffentliche_release(v, commit, notiz or "Siehe CHANGELOG.md.")
    finally:
        git("checkout", "-f", zweig_vorher)
        git("branch", "-D", ZWEIG, pruefen=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
