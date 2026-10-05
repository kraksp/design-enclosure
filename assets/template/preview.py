"""Publish parts to the browser preview in viewer/ (one GLB per part + scene.json).

    publish([{"name": "top", "label": "top shell", "shape": top, "color": (0.15, 0.15, 0.17)}, ...],
            title="My device – enclosure")

Part dict keys: name (file-safe id), shape, label, color (r, g, b 0..1), opacity (default 1; < 1 = no section cap),
visible (default True), static (True = export only when the GLB is missing – use for big unchanged STEP data).
The page (viewer/index.html) polls scene.json and reloads by itself. Serve it with:
    python -m http.server 8765 --bind 127.0.0.1 --directory viewer
With OCP_VSCODE=1 the same parts are also sent to the OCP CAD Viewer extension in VS Code.
"""
import json
import os
import time
from build123d import Compound, export_gltf

VIEWER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer")


def _bake(shape):
    """Bake the Location into the geometry – glTF export drops some node transforms."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.TopLoc import TopLoc_Location
    w = shape.wrapped
    baked = BRepBuilderAPI_Transform(w.Located(TopLoc_Location()), w.Location().Transformation(), True).Shape()
    return Compound(baked) if baked.ShapeType().name == "TopAbs_COMPOUND" else Compound([Compound(baked)])


def publish(parts, title="Enclosure", view="iso", lang="en", deflection=0.05):
    os.makedirs(VIEWER, exist_ok=True)
    meta, boxes = [], []
    for p in parts:
        if p.get("shape") is None:
            continue
        fn = f"part_{p['name']}.glb"
        path = os.path.join(VIEWER, fn)
        s = p["shape"] if isinstance(p["shape"], Compound) else Compound([p["shape"]])
        if not (p.get("static") and os.path.exists(path)):
            export_gltf(_bake(s), path + ".tmp", binary=True, linear_deflection=p.get("deflection", deflection),
                        angular_deflection=0.3)
            os.replace(path + ".tmp", path)
        if p.get("visible", True):
            bb = s.bounding_box()
            boxes.append((bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z))
        meta.append({"name": p["name"], "file": fn, "label": p.get("label", p["name"]),
                     "color": list(p.get("color", (0.6, 0.6, 0.6))), "opacity": p.get("opacity", 1.0),
                     "visible": p.get("visible", True), "v": int(os.path.getmtime(path))})
    bbox = [min(b[i] for b in boxes) for i in range(3)] + [max(b[i] for b in boxes) for i in range(3, 6)] if boxes else None
    with open(os.path.join(VIEWER, "scene.json"), "w", encoding="utf-8") as f:
        json.dump({"stamp": int(time.time()), "title": title, "view": view, "lang": lang, "bbox": bbox, "parts": meta},
                  f, ensure_ascii=False)
    if os.environ.get("OCP_VSCODE"):
        try:
            from ocp_vscode import show
            show(*[p["shape"] for p in parts], names=[p["name"] for p in parts],
                 colors=[p.get("color", (0.6, 0.6, 0.6)) for p in parts], alphas=[p.get("opacity", 1.0) for p in parts])
        except Exception:
            pass
