import { registriere } from "./panel.mjs?v=3.0.0";

registriere({
  classType: "Krea2LightingBuilder",
  hiddenName: "LightingState",
  prop: "lightingState",
  datenSchluessel: "lighting",
  breite: 320,
  teil: "Lighting",
  vorgabe: {
    felder: { setup: "—", richtung: "—", atmosphaere: "—" },
    wuerfeln: {},
    gruppe: "alle",
    details: "",
  },
});
