"""Verification: part validity, collisions with the electronics, assembly clearances.

    from checks import validity, collisions, fits, local
    validity(parts)                                   # every part: solids, is_valid, volume
    hits = collisions(parts, electronics, walls=("top", "bottom"), expected={("cap", "SW1")})
    fits([("button ↔ hole", local(cap, box), local(top, box)), ...])

Run all of it after EVERY geometry change, before showing anything to the user.
"""
from build123d import Box, Pos, Vector
import mech


def _overlap(a, b, m=0.0):
    return not (a.min.X > b.max.X + m or a.max.X < b.min.X - m or a.min.Y > b.max.Y + m or a.max.Y < b.min.Y - m
                or a.min.Z > b.max.Z + m or a.max.Z < b.min.Z - m)


def _vol(a, b):
    i = a & b
    return sum(s.volume for s in i.solids()) if i is not None and i.solids() else 0.0


def validity(parts):
    ok = True
    for k, v in parts.items():
        sols = v.solids()
        valid = all(s.is_valid for s in sols)          # is_valid is a property in build123d 0.10
        ok &= valid and len(sols) > 0
        print(f"  {k:22} solids={len(sols):3} valid={valid} vol={sum(s.volume for s in sols):10.1f} mm³")
    return ok


def collisions(parts, electronics, walls=("top", "bottom"), extra=(), expected=(), min_vol=0.005):
    """Interference volume between the enclosure and every electronic part.

    parts       – dict of enclosure parts (walls are taken from it by name)
    electronics – [(name, shape)], e.g. step_load.load() parts + [("PCB", board)]
    extra       – more [(name, shape)] to treat like electronics (battery pack, cable, magnet)
    expected    – {(feature_prefix, part_prefix)} intended contacts (press fits, heat-stake pins) – reported separately
    Features registered with mech.feat() are tested against everything; walls only against parts that leave the cavity.
    """
    cav = mech.CAVITY[0] if mech.CAVITY else None
    hits, intended = [], []
    feats = [(n, s, s.bounding_box()) for n, s in mech.FEAT]
    for pn, ps in list(electronics) + list(extra):
        pb = ps.bounding_box()
        for fn, fs, fb in feats:
            if _overlap(pb, fb):
                v = _vol(ps, fs)
                if v > min_vol:
                    (intended if any(fn.startswith(a) and pn.startswith(b) for a, b in expected) else hits).append((fn, pn, v))
        corners = [Vector(x, y, z) for x in (pb.min.X, pb.max.X) for y in (pb.min.Y, pb.max.Y) for z in (pb.min.Z, pb.max.Z)]
        if cav is None or not all(cav.is_inside(c) for c in corners):
            for k in walls:
                for es in parts[k].solids():
                    if _overlap(pb, es.bounding_box()):
                        v = _vol(ps, es)
                        if v > min_vol:
                            (intended if any(k.startswith(a) and pn.startswith(b) for a, b in expected) else hits).append(
                                (k + " (wall)", pn, v))
    print(f"COLLISIONS: {len(hits)}")
    src = dict(list(electronics) + list(extra))
    for fn, pn, v in sorted(hits, key=lambda h: -h[2]):
        b = src[pn].bounding_box()
        print(f"  {fn:30} x {pn[:34]:34} {v:8.3f} mm³  x[{b.min.X:.1f},{b.max.X:.1f}] y[{b.min.Y:.1f},{b.max.Y:.1f}] "
              f"z[{b.min.Z:.1f},{b.max.Z:.1f}]")
    for fn, pn, v in intended:
        print(f"  (intended) {fn} x {pn}: {v:.3f} mm³")
    return hits


def local(shape, x0, x1, y0, y1, z0, z1):
    """Part of a shape inside a box – measure one specific gap instead of the global minimum distance."""
    return shape & (Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0))


def fits(pairs):
    """pairs: [(label, a, b)] -> prints minimum distance and overlap volume. 0.000 distance = contact."""
    print(f"{'pair':34} {'min gap':>10} {'overlap':>12}")
    out = []
    for label, a, b in pairs:
        if a is None or b is None or not a.solids() or not b.solids():
            print(f"{label:34} {'(empty – check the local box)':>24}")
            continue
        d, v = a.distance_to(b), _vol(a, b)
        out.append((label, d, v))
        print(f"{label:34} {d:8.3f} mm {v:9.3f} mm³")
    return out
