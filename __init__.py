"""
Photoshoot - build a person, then shoot a series of them.

Labels in, English out: you click labels in your own language and a checked
English phrase goes into the prompt. That mapping lives in Python alone and is
served to the front ends over /krea2/presets - keeping two parallel lists, one
in Python and one in JavaScript, would be a reliable way to let them drift
apart.

The package ships its own JS (WEB_DIRECTORY). Pose, expression, person and
photoshoot keep their state in node.properties, following the pattern set by
PixaromaResolution; Python only ever sees the state, the interface itself is
DOM.

nodes/dock.py is the interface for optional add-on packs and is deliberately
not imported here - it registers no nodes, the packs import it themselves.
"""

from .nodes import (api, expression_builder, person_builder, pose_builder,
                    shooting, store)

api.register()

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

for _modul in (person_builder, expression_builder, pose_builder, shooting,
               store):
    NODE_CLASS_MAPPINGS.update(_modul.NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(_modul.NODE_DISPLAY_NAME_MAPPINGS)

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
