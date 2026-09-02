import { registriere } from "./panel.mjs?v=2.3.0";

registriere({
  classType: "Krea2StyleBuilder",
  hiddenName: "StyleState",
  prop: "styleState",
  datenSchluessel: "style",
  breite: 300,
  hoehe: 300,
  // Has to match DEFAULT_STATE in style_builder.py.
  vorgabe: {
    felder: { look: "—", genre: "Editorial", optik: "85mm f/1.4", finish: "—" },
    wuerfeln: {},
    gruppe: "alle",
    details: "",
  },
});
