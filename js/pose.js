import { registriere } from "./panel.mjs?v=2.3.0";

registriere({
  classType: "Krea2PoseBuilder",
  hiddenName: "PoseState",
  prop: "poseState",
  datenSchluessel: "pose",
  breite: 300,
  hoehe: 370,
  vorgabe: {
    felder: {
      haltung: "—",
      raum: "—",
      koerper: "—",
      arme: "—",
      beine: "—",
      spannung: "—",
    },
    wuerfeln: {},
    gruppe: "alle",
    details: "",
  },
});
