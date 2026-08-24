// Tests the graphToPrompt hook in js/shared.mjs.
//
//     node tests/hook.mjs
//
// That hook is the single point through which every node's state reaches the
// API prompt: hidden inputs do not appear in the workflow JSON, so ComfyUI
// cannot fill them in itself. If it breaks, every node silently ships its
// defaults instead of what the user set - and nothing says so.
//
// shared.mjs imports the ComfyUI front end from "../../scripts/app.js", which
// only exists inside a running ComfyUI. So the test builds a throwaway tree
// under tests/_tmp/ where that path resolves to a stub.

import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const hier = path.dirname(url.fileURLToPath(import.meta.url));
const wurzel = path.dirname(hier);
const tmp = path.join(hier, "_tmp", "hook");

fs.rmSync(tmp, { recursive: true, force: true });
fs.mkdirSync(path.join(tmp, "scripts"), { recursive: true });
fs.mkdirSync(path.join(tmp, "pack", "js"), { recursive: true });
fs.writeFileSync(path.join(tmp, "package.json"), '{"type":"module"}');
fs.copyFileSync(path.join(wurzel, "js", "shared.mjs"),
                path.join(tmp, "pack", "js", "shared.mjs"));

// The stub insists on being called with itself as the receiver. The real
// graphToPrompt is a method on app and uses this, so a hook that loses the
// receiver would break it - this is what catches that.
fs.writeFileSync(path.join(tmp, "scripts", "app.js"), `
export const app = {
  graph: { _nodes: [] },
  extensionManager: null,
  async graphToPrompt() {
    if (this !== app) throw new Error("wrong receiver");
    return { output: {
      "1":    { class_type: "Krea2PoseBuilder",   inputs: {} },
      "5:12": { class_type: "Krea2PersonBuilder", inputs: {} },
      "9":    { class_type: "SomeoneElsesNode",   inputs: {} },
    } };
  },
};
`);

globalThis.document = { getElementById: () => null,
                        createElement: () => ({ style: {}, classList: { add() {}, remove() {} } }),
                        head: { appendChild() {} } };
globalThis.navigator = { language: "en-US" };
globalThis.fetch = async () => { throw new Error("no server in this test"); };

const { app } = await import(url.pathToFileURL(path.join(tmp, "scripts", "app.js")));
const { registriereStateInjektion } =
  await import(url.pathToFileURL(path.join(tmp, "pack", "js", "shared.mjs")));

let fehler = 0;
const pruefe = (name, ist, soll) => {
  const ok = ist === soll;
  if (!ok) fehler++;
  console.log(`  ${ok ? "ok  " : "FAIL"}  ${name}${ok ? "" : `   got ${ist}, want ${soll}`}`);
};

// Node id 12 sits in a subgraph, so the prompt calls it "5:12" while
// app.graph only knows the 12.
app.graph._nodes = [
  { type: "Krea2PoseBuilder",   id: 1,  properties: { poseState:   '{"saved":"pose-1"}' } },
  { type: "Krea2PersonBuilder", id: 12, properties: { personState: '{"saved":"person-12"}' } },
];
registriereStateInjektion("Krea2PoseBuilder",   "PoseState",   "poseState",   { empty: true });
registriereStateInjektion("Krea2PersonBuilder", "PersonState", "personState", { empty: true });

const o = (await app.graphToPrompt()).output;
pruefe("state reaches the prompt",       o["1"].inputs.PoseState,      '{"saved":"pose-1"}');
pruefe("compound subgraph id resolves",  o["5:12"].inputs.PersonState, '{"saved":"person-12"}');
pruefe("other packs left alone",         JSON.stringify(o["9"].inputs), "{}");

pruefe("second call still works",
       (await app.graphToPrompt()).output["1"].inputs.PoseState, '{"saved":"pose-1"}');

app.graph._nodes = [{ type: "Krea2PoseBuilder", id: 1, properties: {} }];
pruefe("falls back to the default",
       (await app.graphToPrompt()).output["1"].inputs.PoseState, '{"empty":true}');

// Called detached, this is undefined. The hook has to supply app anyway, or
// the real graphToPrompt loses its receiver.
app.graph._nodes = [{ type: "Krea2PoseBuilder", id: 1, properties: { poseState: '{"x":1}' } }];
const detached = app.graphToPrompt;
try {
  pruefe("detached call keeps the receiver",
         (await detached()).output["1"].inputs.PoseState, '{"x":1}');
} catch (e) {
  console.log(`  FAIL  detached call keeps the receiver   ${e.message}`);
  fehler++;
}

fs.rmSync(path.join(hier, "_tmp"), { recursive: true, force: true });
console.log(fehler ? `\n${fehler} FAILED` : "\nALL OK");
process.exit(fehler ? 1 : 0);
