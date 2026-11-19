// Holds the series preview in js/shooting.mjs to the planner in shooting.py.
//
//     node tests/plan.mjs
//
// The panel plans every photo of the contact sheet itself - framing, focus,
// pose, expression, ratio, size, outfit, set, light - so it does not ask the server on
// every change. That only works while it computes exactly what plane() will
// compute on execution; if the two drift apart, the contact sheet shows photos
// that never come out, and nothing says so.
//
// The expected values are made fresh on every run: this spawns
// tests/plan_fixture.py, which writes the /krea2/presets data and what Python
// plans for a few hundred states x 40 runs. The JS side gets that same preset
// data, as it would from the route, and has to agree field by field.
//
// shooting.mjs imports the ComfyUI front end ("../../scripts/app.js" and
// api.js), which only exists inside a running ComfyUI, so - as in hook.mjs -
// the modules are copied into a throwaway tree under tests/_tmp/ where that
// path resolves to a stub.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const hier = path.dirname(url.fileURLToPath(import.meta.url));
const wurzel = path.dirname(hier);
const tmp = path.join(hier, "_tmp", "plan");

fs.rmSync(tmp, { recursive: true, force: true });
fs.mkdirSync(path.join(tmp, "scripts"), { recursive: true });
fs.mkdirSync(path.join(tmp, "pack", "js"), { recursive: true });
fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}');
for (const datei of fs.readdirSync(path.join(wurzel, "js"))) {
  if (datei.endsWith(".mjs")) {
    fs.copyFileSync(path.join(wurzel, "js", datei), path.join(tmp, "pack", "js", datei));
  }
}
fs.writeFileSync(path.join(tmp, "scripts", "api.js"), "export const api = {};\n");
// Loading shooting.mjs registers its extension and the graphToPrompt hook;
// neither is exercised here.
fs.writeFileSync(path.join(tmp, "scripts", "app.js"), `
export const app = {
  graph: { _nodes: [] },
  extensionManager: null,
  registerExtension() {},
  async graphToPrompt() { return { output: {} }; },
};
`);

globalThis.document = { getElementById: () => null,
                        createElement: () => ({ style: {}, classList: { add() {}, remove() {} } }),
                        head: { appendChild() {} } };
Object.defineProperty(globalThis, "navigator",
                      { value: { language: "en-US" }, configurable: true });
globalThis.fetch = async () => { throw new Error("no server in this test"); };

// The Python side, fresh from the current code.
const fixture = path.join(tmp, "plan.json");
execFileSync(process.env.PYTHON || "python3", [path.join(hier, "plan_fixture.py"), fixture],
             { stdio: ["ignore", "inherit", "inherit"] });
const { presets: d, faelle } = JSON.parse(fs.readFileSync(fixture, "utf-8"));

const { VORGABE, plane, format, masse, outfitFuer, setFuer, lichtFuer } =
  await import(url.pathToFileURL(path.join(tmp, "pack", "js", "shooting_plan.mjs")));
const { _plane, _format, _masse, _outfitFuer, _setFuer, _lichtFuer } =
  await import(url.pathToFileURL(path.join(tmp, "pack", "js", "shooting.mjs")));

// Field by field, so a failure names what differs rather than "not equal".
let fehler = 0, verglichen = 0;
const gezeigt = new Map(); // case name -> mismatches printed
const zeige = (fall, lauf, feld, ist, soll) => {
  fehler++;
  const n = gezeigt.get(fall.name) || 0;
  gezeigt.set(fall.name, n + 1);
  if (n < 3) {
    console.log(`  FAIL  ${fall.name}, run ${lauf}: ${feld}   JS ${JSON.stringify(ist)}, Python ${JSON.stringify(soll)}`);
  }
};
const gleich = (fall, lauf, feld, ist, soll) => {
  verglichen++;
  if (JSON.stringify(ist ?? null) !== JSON.stringify(soll ?? null)) zeige(fall, lauf, feld, ist, soll);
};

// Re-exports on shooting.mjs must point to shooting_plan.mjs, and VORGABE must
// match SH.DEFAULT_STATE (d.vorgabe) key for key and value for value.
const norm = (x) => (x && typeof x === "object" && !Array.isArray(x)
  ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, norm(x[k])]))
  : x);
if (typeof _plane !== "function" || typeof _format !== "function" || typeof _masse !== "function" ||
    typeof _outfitFuer !== "function" || typeof _setFuer !== "function" || typeof _lichtFuer !== "function" ||
    JSON.stringify(_plane(d, structuredClone(faelle[0].state), 0, 0, 0)) !==
    JSON.stringify(plane(d, structuredClone(faelle[0].state), 0, 0, 0))) {
  fehler++;
  console.log("  FAIL  shooting.mjs re-exports do not match shooting_plan.mjs");
}
if (JSON.stringify(norm(VORGABE)) !== JSON.stringify(norm(d.vorgabe))) {
  fehler++;
  console.log(`  FAIL  VORGABE != SH.DEFAULT_STATE\n    JS:     ${JSON.stringify(norm(VORGABE))}\n    Python: ${JSON.stringify(norm(d.vorgabe))}`);
}

for (const fall of faelle) {
  const saetze = fall.saetze || [];
  for (const { lauf, plan, format: fmtSoll, masse: masseSoll, outfit, set, licht } of fall.laeufe) {
    // A copy each time: plane() must not rely on - or leave - anything in the state.
    const state = structuredClone(fall.state);
    let p;
    try {
      p = plane(d, state, lauf, fall.outfits, saetze.length);
    } catch (e) {
      zeige(fall, lauf, "plane() threw", e.message, "a plan");
      continue;
    }
    gleich(fall, lauf, "kamera", p.kamera, plan.kamera);
    gleich(fall, lauf, "fokus", p.fokus, plan.fokus);
    gleich(fall, lauf, "perspektive", p.perspektive, plan.perspektive);
    for (const quelle of ["pose", "ausdruck"]) {
      const felder = new Set([...Object.keys(plan[quelle]), ...Object.keys(p[quelle])]);
      for (const cat of felder) gleich(fall, lauf, `${quelle}.${cat}`, p[quelle][cat], plan[quelle][cat]);
    }
    gleich(fall, lauf, "format", format(d, p.kamera, lauf, state, p.perspektive), fmtSoll);
    gleich(fall, lauf, "masse", masse(d, p.kamera, lauf, state, p.perspektive), masseSoll);
    gleich(fall, lauf, "outfit", outfitFuer(d, state, lauf, fall.outfits), outfit);
    gleich(fall, lauf, "set", setFuer(d, state, lauf, saetze.length), set);
    gleich(fall, lauf, "licht", lichtFuer(d, state, lauf, saetze), licht);
    gleich(fall, lauf, "state untouched", state, fall.state);
  }
}

for (const [name, n] of gezeigt) if (n > 3) console.log(`  ...   ${name}: ${n} mismatches in all`);
console.log(`  ${faelle.length} states, ${verglichen} values compared`);

fs.rmSync(tmp, { recursive: true, force: true });
console.log(fehler ? `\n${fehler} FAILED` : "\nALL OK");
process.exit(fehler ? 1 : 0);
