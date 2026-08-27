import { registriere } from "./panel.mjs?v=2.1.6";

registriere({
  classType: "Krea2ExpressionBuilder",
  hiddenName: "ExpressionState",
  prop: "expressionState",
  datenSchluessel: "ausdruck",
  breite: 300,
  hoehe: 360,
  vorgabe: {
    felder: { stimmung: "—", augen: "—", blick: "—", brauen: "—", mund: "—", kopf: "—" },
    wuerfeln: {},
    gruppe: "alle",
    details: "",
  },
});
