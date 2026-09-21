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


def transformiere_fuer_public(wurzel):
    """Passt den Stand auf dem Orphan-Branch fuer das oeffentliche Repo an.

    Erzwingt im oeffentlichen Release die Altersbegrenzung (18+)
    in Python, JS und den Tests und entfernt U18-Presets.
    """
    def ersetze_pflicht(text, alt, neu, dateiname):
        if alt not in text:
            raise SystemExit("Fehler beim Vorbereiten fuer Public: Muster in %s nicht gefunden!" % dateiname)
        return text.replace(alt, neu)

    pb_pfad = wurzel / "nodes" / "person_builder.py"
    pb = pb_pfad.read_text(encoding="utf-8")
    if "MINDESTALTER = 18" not in pb:
        pb = ersetze_pflicht(
            pb,
            'NONE = "—"',
            '# The presets start at the early 20s, so labels alone cannot describe a minor.\n'
            '# The exact-age field is free text and could, so it gets a floor. This stops\n'
            '# accidents and backs the statement in the README; it is not a content filter,\n'
            '# because the nodes only emit text and anything else can be typed elsewhere.\n'
            'MINDESTALTER = 18\n\n'
            'NONE = "—"',
            pb_pfad.name
        )

    # Remove U18 presets for public
    pb = ersetze_pflicht(
        pb,
        '        ("Kind (6–12)", "{child}"),\n        ("Teenager (13–17)", "{teen}"),\n',
        '',
        pb_pfad.name
    )

    pb = ersetze_pflicht(
        pb,
        '    exact = "".join(ch for ch in _clean(p.get("ageExact")) if ch.isdigit()) if ok("ageExact") else ""\n'
        '    if exact and int(exact) > 0:',
        '    exact = "".join(ch for ch in _clean(p.get("ageExact")) if ch.isdigit()) if ok("ageExact") else ""\n'
        '    if exact and int(exact) < MINDESTALTER:\n'
        '        exact = str(MINDESTALTER)\n'
        '    if exact and int(exact) > 0:',
        pb_pfad.name
    )

    pb = ersetze_pflicht(
        pb,
        '"ageExact": "genaues Alter, z. B. 34 (schlägt den Bereich)",',
        '"ageExact": "genaues Alter, z. B. 34 (schlägt den Bereich, ab 18)",',
        pb_pfad.name
    )
    pb_pfad.write_text(pb, encoding="utf-8")

    i18n_pfad = wurzel / "nodes" / "i18n.py"
    i18n = i18n_pfad.read_text(encoding="utf-8")
    i18n = ersetze_pflicht(
        i18n,
        '        "Kind (6–12)": "Child (6–12)", "Teenager (13–17)": "Teenager (13–17)",\n',
        '',
        i18n_pfad.name
    )
    i18n_pfad.write_text(i18n, encoding="utf-8")

    js_pfad = wurzel / "js" / "person.mjs"
    js = js_pfad.read_text(encoding="utf-8")
    js = ersetze_pflicht(
        js,
        '  let genau = (t.ageExact || "").replace(/\\D/g, "");\n'
        '  if (genau && Number(genau) > 0) {',
        '  // Mirrors MINDESTALTER in person_builder.py - the preview has to show what\n'
        '  // the prompt will actually say, not what was typed.\n'
        '  let genau = (t.ageExact || "").replace(/\\D/g, "");\n'
        '  if (genau && Number(genau) < 18) genau = "18";\n'
        '  if (genau && Number(genau) > 0) {',
        js_pfad.name
    )
    js_pfad.write_text(js, encoding="utf-8")

    smoke_pfad = wurzel / "tests" / "smoke.py"
    smoke = smoke_pfad.read_text(encoding="utf-8")
    smoke = ersetze_pflicht(
        smoke,
        '    # Exact-age field & gender combinations: in dev mode, exact age numbers pass through without clamping.\n'
        '    assert "a 12-year-old girl" in peb.compose_person(dict(p, gender="woman", ageExact="12"))\n'
        '    assert "a 15-year-old girl" in peb.compose_person(dict(p, gender="woman", ageExact="15"))\n'
        '    assert "an 18-year-old woman" in peb.compose_person(dict(p, gender="woman", ageExact="18"))\n'
        '    assert "a 24-year-old woman" in peb.compose_person(dict(p, gender="woman", ageExact="24"))\n'
        '    assert "a 26-year-old trans woman" in peb.compose_person(dict(p, gender="trans woman", ageExact="26"))\n'
        '    assert "a 14-year-old boy" in peb.compose_person(dict(p, gender="man", ageExact="14"))\n'
        '    assert "a 30-year-old man" in peb.compose_person(dict(p, gender="man", ageExact="30"))\n'
        '    assert "a 10-year-old child" in peb.compose_person(dict(p, gender="person", ageExact="10"))\n'
        '    assert "a young girl" in peb.compose_person(dict(p, gender="woman", age="{child}"))\n'
        '    assert "a teenage girl" in peb.compose_person(dict(p, gender="woman", age="{teen}"))\n'
        '    assert "a teenage trans girl" in peb.compose_person(dict(p, gender="trans woman", age="{teen}"))\n'
        '    assert "a woman, in her early 20s" in peb.compose_person(dict(p, gender="woman", age="in {p} early 20s"))\n'
        '    assert "a trans woman, in her late 20s" in peb.compose_person(dict(p, gender="trans woman", age="in {p} late 20s"))\n'
        '    # Legacy type compatibility\n'
        '    assert "a 34-year-old woman" in peb.compose_person(dict(p, type="Frau", ageExact="34"))\n'
        '    assert "years old" not in peb.compose_person(dict(p, ageExact=""))\n'
        '    print("Altersgrenze: Dev-Modus (exakte Alterseingabe ohne Begrenzung, U18 aktiv)")',
        '    # The exact-age field is free text and has a floor. Below it, and at every\n'
        '    # detail level, the prompt must never say an age under MINDESTALTER.\n'
        '    for eingabe in ("12", "3", "17", " 8 Jahre"):\n'
        '        for stufe in (peb.DETAIL_VOLL, peb.DETAIL_FIGUR, peb.DETAIL_IDENTITAET):\n'
        '            text = peb.compose_person(dict(p, ageExact=eingabe), stufe)\n'
        '            assert "%d-year-old" % peb.MINDESTALTER in text or "%d years old" % peb.MINDESTALTER in text, \\\n'
        '                "Alter nicht begrenzt: %r -> %s" % (eingabe, text)\n'
        '    assert "a 34-year-old woman" in peb.compose_person(dict(p, ageExact="34"))\n'
        '    assert "34 years old" in peb.compose_person({"ageExact": "34"})\n'
        '    assert "years old" not in peb.compose_person(dict(p, ageExact=""))\n'
        '    # The presets on their own cannot describe a minor either.\n'
        '    assert not [v for _, v in peb.PRESETS["age"]\n'
        '                if any(z in v for z in ("teen", "10s", "child", "{child}", "{teen}"))]\n'
        '    print("Altersgrenze: ab %d, Vorgaben ab Anfang 20" % peb.MINDESTALTER)',
        smoke_pfad.name
    )
    smoke_pfad.write_text(smoke, encoding="utf-8")


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
        print("\nWende Public-Filter an (Altersbegrenzung 18+)...")
        transformiere_fuer_public(WURZEL)
        print("Fuehre Smoke-Test auf Public-Stand aus...")
        e = subprocess.run([sys.executable, str(WURZEL / "tests" / "smoke.py")],
                           capture_output=True, text=True)
        if e.returncode:
            raise SystemExit("Smoke-Test auf Public-Stand fehlgeschlagen:\n%s%s" % (e.stdout, e.stderr))
        print("Smoke-Test fuer Public erfolgreich.")

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
