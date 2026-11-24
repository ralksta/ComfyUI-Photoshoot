// Tests the graph side of shoot files in js/regie.mjs.
//
//     node tests/regie.mjs
//
// Which node gets which section of a shoot, and whether collecting a shoot and
// writing it back gives the very same node.properties. regie.mjs imports the
// ComfyUI front end, so - as in hook.mjs - the modules are copied into a
// throwaway tree under tests/_tmp/ where "../../scripts/app.js" is a stub with
// a small hand-built graph. The section table comes from Python
// (/krea2/presets "shoot"), as it does in the browser.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const hier = path.dirname(url.fileURLToPath(import.meta.url));
const wurzel = path.dirname(hier);
const tmp = path.join(hier, "_tmp", "regie");

fs.rmSync(tmp, { recursive: true, force: true });
fs.mkdirSync(path.join(tmp, "scripts"), { recursive: true });
fs.mkdirSync(path.join(tmp, "pack", "js"), { recursive: true });
fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}');
for (const datei of ["shared.mjs", "regie.mjs"]) {
  fs.copyFileSync(path.join(wurzel, "js", datei), path.join(tmp, "pack", "js", datei));
}
fs.writeFileSync(path.join(tmp, "scripts", "api.js"), "export const api = {};\n");
fs.writeFileSync(path.join(tmp, "scripts", "app.js"),
  "export const app = { graph: null, extensionManager: null, registerExtension() {},\n" +
  "  async graphToPrompt() { return { output: {} }; } };\n");

globalThis.document = { getElementById: () => null,
                        createElement: () => ({ style: {}, classList: { add() {}, remove() {} } }),
                        head: { appendChild() {} } };
Object.defineProperty(globalThis, "navigator",
                      { value: { language: "en-US" }, configurable: true });
globalThis.fetch = async () => { throw new Error("no server in this test"); };

const info = JSON.parse(execFileSync(process.env.PYTHON || "python3", ["-c", `
import importlib.util, json, sys, types
sys.modules["folder_paths"] = types.SimpleNamespace(get_user_directory=lambda: ${JSON.stringify(path.join(hier, "_tmp"))})
spec = importlib.util.spec_from_file_location("krea2kit", ${JSON.stringify(path.join(wurzel, "__init__.py"))},
                                              submodule_search_locations=[${JSON.stringify(wurzel)}])
m = importlib.util.module_from_spec(spec); sys.modules["krea2kit"] = m; spec.loader.exec_module(m)
from krea2kit.nodes import api
print(json.dumps(api.presets()["shoot"]))
`], { encoding: "utf-8", stdio: ["ignore", "pipe", "inherit"] }).trim().split("\n").pop());

const { app } = await import(url.pathToFileURL(path.join(tmp, "scripts", "app.js")));
const { ziele, sammle, wendeAn } = await import(url.pathToFileURL(path.join(tmp, "pack", "js", "regie.mjs")));

// ---------------------------------------------------------------- Graph ---
// series(1) --person_data-- person(2) --garderobe-- wardrobe(3)
// series(1) --pose--> join(4) <--lighting-- lighting(5)
//                     join(4) <--stil-- reroute(6) <-- style(7)
//                     join(4) <--szene-- scene(8), <--text-- template(9)
// two expression builders (10, 11), neither wired: ambiguous, left out.
const gezeichnet = new Map();
const knoten = (id, comfyClass, props, extra = {}) => ({
  id, comfyClass, type: comfyClass, properties: props, inputs: [], outputs: [],
  _k2Zeichne() { gezeichnet.set(id, (gezeichnet.get(id) || 0) + 1); }, ...extra,
});
const st = (o) => JSON.stringify(o);
const P = {
  person: st({ felder: { gender: "Frau", hair: "Lange Wellen" }, mehrfach: { skinFeatures: ["Sommersprossen"] },
               texte: { ageExact: "", details: "", trigger: "" }, sektion: "Grund" }),
  wardrobe: st({ outfits: [{ id: "o1", name: "Coat", felder: { shoes: "Combat Boots" }, texte: { details: "" } }],
                 aktiv: 0, sektion: "Kleidung", vorschauArt: "puppe" }),
  lighting: st({ felder: { setup: "Golden Hour" }, wuerfeln: {}, gruppe: "alle", details: "" }),
  style: st({ felder: { genre: "Editorial" }, wuerfeln: {}, gruppe: "alle", details: "" }),
  series: st({ anzahl: 9, start: 4711, groesse: 1536, pools: { haltung: "stehend" }, takes: { "3": 1 } }),
};
const nodes = [
  knoten(1, "Krea2Photoshooting", { shootingState: P.series }),
  knoten(2, "Krea2PersonBuilder", { personState: P.person }),
  knoten(3, "Krea2Wardrobe", { wardrobeState: P.wardrobe }),
  knoten(4, "Krea2PromptJoin", {}),
  knoten(5, "Krea2LightingBuilder", { lightingState: P.lighting }),
  { id: 6, type: "Reroute", properties: {}, inputs: [], outputs: [] },
  knoten(7, "Krea2StyleBuilder", { styleState: P.style }),
  { id: 8, type: "PrimitiveStringMultiline", properties: {}, inputs: [], outputs: [],
    widgets: [{ name: "value", type: "customtext", value: "a sunlit loft" }] },
  { id: 9, type: "PrimitiveStringMultiline", properties: {}, inputs: [], outputs: [],
    widgets: [{ name: "value", type: "customtext", value: "{style}, {person}" }] },
  knoten(10, "Krea2ExpressionBuilder", {}),
  knoten(11, "Krea2ExpressionBuilder", {}),
];
const byId = new Map(nodes.map((n) => [n.id, n]));
const links = new Map();
let naechster = 1;
function verbinde(von, nach, eingang) {
  const id = naechster++;
  links.set(id, { id, origin_id: von, origin_slot: 0, target_id: nach, target_slot: 0 });
  const a = byId.get(von), b = byId.get(nach);
  (a.outputs[0] ||= { name: "out", links: [] }).links.push(id);
  b.inputs.push({ name: eingang, link: id });
}
verbinde(2, 1, "person_data");
verbinde(3, 2, "garderobe");
verbinde(1, 4, "pose");
verbinde(5, 4, "lighting");
verbinde(7, 6, "");
verbinde(6, 4, "stil");
verbinde(8, 4, "szene");
verbinde(9, 4, "text");
app.graph = { _nodes: nodes, links, getNodeById: (id) => byId.get(id) ?? null, setDirtyCanvas() {} };

// ---------------------------------------------------------------- Tests ---
let fehler = 0;
const pruefe = (name, ok, detail = "") => {
  console.log((ok ? "  ok    " : "  FAIL  ") + name + (ok ? "" : "   " + detail));
  if (!ok) fehler++;
};
const serie = byId.get(1);
const propsJetzt = () => JSON.stringify(nodes.map((n) => [n.id, n.properties, n.widgets?.map((w) => w.value)]));

const z = ziele(serie, info);
pruefe("person on person_data, wardrobe on the person", z.person?.id === 2 && z.wardrobe?.id === 3);
pruefe("lighting and style on Build Prompt, style through a reroute", z.lighting?.id === 5 && z.style?.id === 7);
pruefe("scene and template are the wired text nodes", z.scene?.id === 8 && z.template?.id === 9);
pruefe("no pose builder, two unwired expressions: both left out", z.pose === null && z.expression === null);

const shoot = sammle(serie, info);
pruefe("collected sections", JSON.stringify(Object.keys(shoot)) ===
  JSON.stringify(["format", "person", "wardrobe", "lighting", "style", "series", "scene", "template"]),
  Object.keys(shoot).join(","));
pruefe("sections are the node states verbatim", st(shoot.person) === P.person && st(shoot.series) === P.series);

const original = propsJetzt();
byId.get(2).properties.personState = st({ felder: { gender: "Mann" } });
byId.get(5).properties.lightingState = st({ felder: { setup: "Neonröhre" } });
byId.get(1).properties.shootingState = st({ anzahl: 3 });
byId.get(8).widgets[0].value = "changed";
const geaendert = propsJetzt();
gezeichnet.clear();
const { bericht, rueckgaengig } = wendeAn(serie, shoot, info);
pruefe("round trip: every property and text back byte for byte", propsJetzt() === original);
pruefe("every section reports its node", bericht.every((b) => b.node) && bericht.length === 7, JSON.stringify(bericht.map((b) => b.abschnitt)));
pruefe("the panels are redrawn", gezeichnet.get(2) >= 1 && gezeichnet.get(1) >= 1);
rueckgaengig();
pruefe("undo puts back what was there", propsJetzt() === geaendert);

// A section for a node that is missing is reported, not written anywhere.
const r2 = wendeAn(serie, { expression: { felder: { stimmung: "Gelassen" } } }, info);
pruefe("no node: reported as skipped", r2.bericht.length === 1 && r2.bericht[0].node === null);
pruefe("no node: nothing written", !byId.get(10).properties.expressionState && !byId.get(11).properties.expressionState);

// An empty section is a node without a state: the property stays or becomes absent.
delete byId.get(5).properties.lightingState;
wendeAn(serie, { lighting: {} }, info);
pruefe("empty section, no state: stays absent", !("lightingState" in byId.get(5).properties));
byId.get(5).properties.lightingState = P.lighting;
const r3 = wendeAn(serie, { lighting: {} }, info);
pruefe("empty section on a state: removed, and undo puts it back",
  !("lightingState" in byId.get(5).properties) && (r3.rueckgaengig(), byId.get(5).properties.lightingState === P.lighting));

// The Director's series goes onto the current one, as a recipe does.
byId.get(1).properties.shootingState = P.series;
wendeAn(serie, { series: { anzahl: 6, pools: { stimmung: "ruhig" }, aktiv: { pose: false } } }, info, { mischen: true });
const gemischt = JSON.parse(byId.get(1).properties.shootingState);
pruefe("Director series: plan replaced, size and start kept",
  gemischt.anzahl === 6 && gemischt.start === 4711 && gemischt.groesse === 1536 &&
  JSON.stringify(gemischt.pools) === st({ stimmung: "ruhig" }) && gemischt.aktiv.pose === false,
  JSON.stringify(gemischt));
wendeAn(serie, { series: { anzahl: 6 } }, info);
pruefe("shoot file series: replaces the whole state", byId.get(1).properties.shootingState === st({ anzahl: 6 }));

// The Director keeps who the person is: trigger and reference stay, the
// labels come from the answer. A shoot file replaces the person whole.
byId.get(2).properties.personState = st({ felder: { gender: "Frau" },
  texte: { ageExact: "", details: "", trigger: "EileenX", referenz: "1, 2" } });
wendeAn(serie, { person: { felder: { gender: "Mann", hair: "Kurz" }, texte: { trigger: "", referenz: "" } } }, info, { mischen: true });
const dp = JSON.parse(byId.get(2).properties.personState);
pruefe("Director person: labels replaced, trigger and reference kept",
  dp.felder.gender === "Mann" && dp.texte.trigger === "EileenX" && dp.texte.referenz === "1, 2", JSON.stringify(dp));
wendeAn(serie, { person: { felder: { gender: "Mann" }, texte: {} } }, info);
pruefe("shoot file person: replaces the whole state",
  !JSON.parse(byId.get(2).properties.personState).texte.trigger);
byId.get(2).properties.personState = P.person;

// Wired wins over "the only one"; an unwired node counts only when it is
// the only one of its class.
for (const n of [knoten(12, "Krea2PersonBuilder", {}), knoten(13, "Krea2PoseBuilder", {})]) {
  nodes.push(n);
  byId.set(n.id, n);
}
const z2 = ziele(serie, info);
pruefe("a second, unwired person does not take over", z2.person?.id === 2);
pruefe("the only pose builder is taken although unwired", z2.pose?.id === 13);

// The Location node's sets: wired to the Series' ort_data input, collected
// verbatim and written back byte for byte; a second, unwired one does not
// take over.
const ortState = st({ saetze: [{ id: "s1", name: "Loft", felder: { ort: "Sonniges Loft" }, wuerfeln: {},
                                 gruppe: "innen", details: "" }], aktiv: 0 });
for (const n of [knoten(14, "Krea2LocationBuilder", { locationState: ortState }),
                 knoten(15, "Krea2LocationBuilder", {})]) {
  nodes.push(n);
  byId.set(n.id, n);
}
const z3a = ziele(serie, info);
pruefe("two Location nodes, none wired: left out", z3a.location === null);
verbinde(14, 1, "ort_data");
const z3 = ziele(serie, info);
pruefe("location on ort_data", z3.location?.id === 14);
const mitOrt = sammle(serie, info);
pruefe("the location's sets verbatim", st(mitOrt.location) === ortState);
byId.get(14).properties.locationState = st({ saetze: [] });
wendeAn(serie, { location: mitOrt.location }, info);
pruefe("location written back byte for byte", byId.get(14).properties.locationState === ortState);

// All-in-One Studio mode on a standalone Krea2Photoshooting node.
app.graph._nodes = [knoten(99, "Krea2Photoshooting", {
  studioModus: true,
  shootingState: P.series,
  personState: P.person,
  templateText: "{style}, {person}",
})];
const sSolo = app.graph._nodes[0];
const zSolo = ziele(sSolo, info);
pruefe("studio mode maps embedded sections to Series",
  zSolo.person === sSolo && zSolo.wardrobe === sSolo && zSolo.lighting === sSolo &&
  zSolo.style === sSolo && zSolo.location === sSolo && zSolo.template === sSolo);
const colSolo = sammle(sSolo, info);
pruefe("studio mode sammle collects embedded properties",
  st(colSolo.person) === P.person && colSolo.template === "{style}, {person}" && colSolo.lighting === undefined);
wendeAn(sSolo, { style: JSON.parse(P.style), scene: "a quiet pier" }, info);
pruefe("studio mode wendeAn writes styleState and sceneText onto Series",
  sSolo.properties.styleState === P.style && sSolo.properties.sceneText === "a quiet pier");

console.log(fehler ? `\n${fehler} FAILED` : "\nALL OK");
process.exit(fehler ? 1 : 0);
