# build123d / OCP notes (0.10)

Traps that cost real time, with the fix. Check here before debugging geometry.

| symptom | cause | fix |
|---|---|---|
| components at the origin / unrotated after import | `import_step` loses nested assembly locations | `step_load.load()` (XCAF walk with `GetLocation_s`) |
| `Polygon` wedge / triangle in the wrong place | `Polygon(...)` centres itself on its bounding box by default | `Polygon(*pts, align=None)` |
| `ValueError: width and height must be > 2*radius` | `RectangleRounded(w, h, r)` with r ≥ min(w, h) / 2 | r = min(w, h) / 2 − 0.05 for a stadium |
| cut-out appears on the wrong side / mirrored / at z = −7 | Plane x_dir / z_dir combination flips local axes | `mech.wall_plane()` / `mech.wall_cut()`; verify local y = world Z with one test cut |
| pieces of a part disconnected after several `+=` | sequential fuse of touching solids | `mech.fuse_all([...])` = one `fuse(*rest).clean()` |
| `AttributeError: ShapeList has no bounding_box` | `a - b` can return a ShapeList | wrap: `Compound(list(s))` (`feat()` does it) |
| `TypeError: 'bool' object is not callable` | `is_valid` is a property | `shape.is_valid` |
| `a & b` is `None` | empty intersection | test for `None` before `.solids()` |
| distance between two 2D faces is "0.8" although they overlap | faces lie on different z planes | move both to the same plane before measuring |
| fillet fails | edge selection includes tangent / tiny edges | select by position (`filter_by(lambda e: ...)`), fillet before boolean cuts, smaller radius |
| glTF model 1000× too small / lying on its side | glTF is metres and Y-up | viewer scales ×1000 and rotates +90° about X (built in) |
| glTF loses some transforms | node locations not baked | `preview._bake()` (built in) |
| `UnicodeEncodeError: 'charmap'` on Windows | console code page | `PYTHONIOENCODING=utf-8` |
| `"\n"` inside generated code turns into a real newline / SyntaxError | shell heredoc + Python string escaping | edit files with the editor tool, not with heredoc-generated Python |

## Useful snippets

```python
# section of a part at a plane, as polygons (sections.polygons does this)
cut = shape & Face.make_rect(400, 400, Plane(origin=(0, y, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0)))

# exact minimum distance with the closest points
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
d = BRepExtrema_DistShapeShape(a.wrapped, b.wrapped); d.Value(); d.PointOnShape1(1)

# hidden-line projection for drawings (drawing.py): transform into a view frame, then project along -Z
local = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)).to_local_coords(shape)   # side view from +X
visible, hidden = local.project_to_viewport((0, 0, 5000), (0, 1, 0), (0, 0, 0))

# chamfer only the top face edges of a cap
cap = chamfer(cap.edges().filter_by(lambda e: abs(e.center().Z - z_top) < 1e-6), 0.5)

# reuse exact shapes (logo letters) from an old model
old = import_step("old.step"); letters = [s for s in old.solids() if s.volume < 20 and s.bounding_box().min.Z > 21.5]
```

Performance: a ~150 × 90 mm two-shell enclosure with ~60 features builds in 20–40 s; the full collision check against
~1300 PCB parts ~1 min (bounding-box prefilter in `checks.collisions`). Keep heavy STEP parts `static` in the preview.
