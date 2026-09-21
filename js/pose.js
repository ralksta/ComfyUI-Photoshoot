import { registriere } from "./panel.mjs?v=2.6.0";

registriere({
  classType: "Krea2PoseBuilder",
  hiddenName: "PoseState",
  prop: "poseState",
  datenSchluessel: "pose",
  breite: 320,
  teil: "Pose",
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
