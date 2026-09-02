import { registriere } from "./panel.mjs?v=2.3.0";

registriere({
  classType: "Krea2LightingBuilder",
  hiddenName: "LightingState",
  prop: "lightingState",
  datenSchluessel: "lighting",
  breite: 300,
  hoehe: 280,
  vorgabe: {
    felder: { setup: "—", richtung: "—", atmosphaere: "—" },
    wuerfeln: {},
    gruppe: "alle",
    details: "",
  },
});
