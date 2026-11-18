import { registriere } from "./panel.mjs?v=2.9.0";

registriere({
  classType: "Krea2LocationBuilder",
  hiddenName: "LocationState",
  prop: "locationState",
  datenSchluessel: "location",
  breite: 320,
  teil: "Location",
  // Several sets as tabs, like the Wardrobe's outfits; each set has the
  // blueprint's shape. Has to match DEFAULT_STATE in location_builder.py.
  mehrere: true,
  vorgabe: {
    saetze: [{
      id: "s1",
      name: "",
      felder: { ort: "—", tageszeit: "—", wetter: "—", jahreszeit: "—" },
      wuerfeln: {},
      gruppe: "alle",
      details: "",
    }],
    aktiv: 0,
  },
});
