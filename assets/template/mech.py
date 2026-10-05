"""Reusable build123d helpers for enclosure models.

Coordinate convention (keep it in every project): the electronics coordinate system.
Top copper of the main PCB at z = 0, +Y = front, -Y = back, X = width. Units: mm.
"""
from build123d import (Align, Axis, Box, Circle, Compound, Cylinder, GeomType, Plane, Pos, RectangleRounded,
                       chamfer, extrude, fillet)

# ---------------------------------------------------------------- feature registry
# Every solid added *inside* the cavity (bosses, ribs, pins, light-pipe sleeves, moving parts) is registered
# with feat(), so checks.py can test it against every electronic component.
FEAT = []      # (name, shape)
CAVITY = []    # [cavity solid] – parts fully inside it are only checked against FEAT, not against the walls


def feat(name, shape):
    if not hasattr(shape, "bounding_box"):          # ShapeList (several disjoint pieces) -> Compound
        shape = Compound(list(shape))
    FEAT.append((name, shape))
    return shape


def reset():
    FEAT.clear()
    CAVITY.clear()


# ---------------------------------------------------------------- primitives
def cyl(d, z0, z1, x=0.0, y=0.0):
    """Vertical cylinder Ø d from z0 to z1."""
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def rrect(size, r, z0, z1, x=0.0, y=0.0):
    """Vertical rounded-rectangle prism (size = (sx, sy)); r must be < min(size) / 2."""
    return Pos(x, y, z0) * extrude(RectangleRounded(size[0], size[1], r), z1 - z0)


def box(x0, x1, y0, y1, z0, z1):
    """Axis-aligned box from min/max coordinates."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def wall_plane(y, x=0.0, z=0.0, outward=-1):
    """Plane on a wall normal to Y: local x = world X, local y = world Z, extrude goes outward (default -Y = back wall).
    Use outward=+1 for the front wall. Mixing up x_dir/z_dir here mirrors cut-outs – always use this helper."""
    if outward < 0:
        return Plane(origin=(x, y, z), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return Plane(origin=(x, y, z), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))


def wall_cut(sketch, y_in, y_out, x=0.0, z=0.0):
    """Prism of a 2D sketch through a wall normal to Y, from y_in (inner side) to y_out (outer side)."""
    outward = -1 if y_out < y_in else 1
    pl = wall_plane(y_in, x, z, outward)
    return pl * extrude(sketch, abs(y_in - y_out))


def side_mask(x_from, z0=-100, z1=100, reach=200):
    """Region |x| >= x_from (both sides), for features that exist only near the side walls."""
    w = reach - x_from
    return (Pos(x_from + w / 2, 0, (z0 + z1) / 2) * Box(w, 2 * reach, z1 - z0) +
            Pos(-(x_from + w / 2), 0, (z0 + z1) / 2) * Box(w, 2 * reach, z1 - z0))


def _vertical(face):
    try:
        return abs(face.normal_at().Z) < 1e-6
    except Exception:
        return False


def soften(solid, ch, r):
    """Chamfer `ch` on the top and bottom perimeter of a vertical prism, then round the chamfer edges with `r`."""
    bb = solid.bounding_box()
    rim = solid.edges().filter_by(lambda e: abs(e.center().Z - bb.max.Z) < 1e-6 or abs(e.center().Z - bb.min.Z) < 1e-6)
    s = chamfer(rim, ch)
    faces = [f for f in s.faces() if f.geom_type != GeomType.PLANE and not _vertical(f)]
    faces += [f for f in s.faces() if f.geom_type == GeomType.PLANE and 0.01 < abs(f.normal_at().Z) < 0.99]
    edges = {e for f in faces for e in f.edges()}
    return fillet(list(edges), r) if r > 0 else s


def top_edges(shape, z, tol=1e-6):
    return shape.edges().filter_by(lambda e: abs(e.center().Z - z) < tol)


def fuse_all(pieces):
    """Fuse many solids in ONE operation – sequential `a += b` can leave pieces disconnected."""
    return pieces[0].fuse(*pieces[1:]).clean() if len(pieces) > 1 else pieces[0]


def split_z(shape, z, big=1000):
    """(above, below) halves of a shape cut at height z."""
    above = shape & (Pos(0, 0, z + big / 2) * Box(big, big, big))
    below = shape & (Pos(0, 0, z - big / 2) * Box(big, big, big))
    return above, below


def solids_of(shape):
    return list(shape.solids()) if shape is not None else []


def stack_axis(shape, axis):
    """Min/max of a shape along 'x' | 'y' | 'z'."""
    bb = shape.bounding_box()
    return {"x": (bb.min.X, bb.max.X), "y": (bb.min.Y, bb.max.Y), "z": (bb.min.Z, bb.max.Z)}[axis]


__all__ = ["FEAT", "CAVITY", "feat", "reset", "cyl", "rrect", "box", "wall_plane", "wall_cut", "side_mask", "soften",
           "top_edges", "fuse_all", "split_z", "solids_of", "stack_axis", "Axis", "Circle"]
