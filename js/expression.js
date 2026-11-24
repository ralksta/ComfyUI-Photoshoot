import { registriere } from "./panel.mjs?v=3.1.0";

registriere({
  classType: "Krea2ExpressionBuilder",
  hiddenName: "ExpressionState",
  prop: "expressionState",
  datenSchluessel: "ausdruck",
  breite: 320,
  teil: "Expression",
  vorgabe: {
    felder: { stimmung: "—", augen: "—", blick: "—", brauen: "—", mund: "—", kopf: "—" },
    wuerfeln: {},
    gruppe: "alle",
    details: "",
  },
});
