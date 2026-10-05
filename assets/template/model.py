"""__PROJECT__ – parametric enclosure (build123d).

Coordinates = electronics: top copper at z = 0, +Y = front, -Y = back, X = width, mm.
All dimensions live in the PARAMETERS block. `python model.py` builds, checks, exports STEP to out/ and
refreshes the preview (viewer/ in a browser; with --headless also PNG renders in out/render/).

This file is a working starting point: a two-shell box around a PCB with standoffs, screws, a lip joint and one
connector cut-out. Replace / extend features, keep the structure (parameters → build() → checks → outputs).
"""
import os
import sys
import time
from build123d import Box, Compound, Pos, RectangleRounded, export_step
import mech
from mech import cyl, feat, rrect, soften, split_z, wall_cut

# ================================================================ PARAMETERS
STEP_PCB = None                    # path to the electronics STEP; None = built-in demo board
BOARD = dict(size=(60.0, 90.0), t=1.6, r=3.0)        # demo board only
HOLES = [(-25.0, -40.0), (25.0, -40.0), (-25.0, 40.0), (25.0, 40.0)]   # PCB mounting holes (Ø3.2)

# process: one clearance set that works for MJF (±0.2) and FDM 0.4 mm nozzle
CLR = 0.2                          # per side, every sliding / locating fit
WALL = 2.0                         # shell wall (≥ 1.2 = 3 FDM perimeters; ≥ 0.8 absolute minimum)
GAP_XY, GAP_TOP, GAP_BOTTOM = 1.0, 2.0, 3.0           # air around the electronics envelope
EDGE_CH, EDGE_R = 1.5, 0.8         # outer chamfer + round on top / bottom perimeter
CORNER_R = 6.0                     # plan corner radius (outer)

LIP = dict(w=0.8, h=1.5)           # tongue on the bottom shell (from the cavity into the wall), rebate in the top + CLR
STANDOFF_D = 6.0                   # PCB rests on standoffs; the screws go through the mounting holes
SCREW = dict(head_d=5.8, head_h=2.6, clear_d=3.4, pilot_d=2.5, boss_d=7.0)   # self-tapping plastic screw from below

CONNECTOR_CLR = 0.3                # around connector bodies that pass the wall
TITLE = "__PROJECT__ – enclosure"
LANG = "en"                        # viewer / drawing language: "en" | "pl"


# ================================================================ electronics
def electronics():
    """(board, [(name, shape)]) in PCB coordinates."""
    if STEP_PCB:
        from step_load import load
        return load(STEP_PCB)
    sx, sy = BOARD["size"]
    board = Pos(0, 0, -BOARD["t"]) * mech.rrect(BOARD["size"], BOARD["r"], 0, BOARD["t"])
    for x, y in HOLES:
        board -= cyl(3.2, -5, 5, x, y)
    parts = [("USB-C", mech.box(-4.47, 4.47, -sy / 2 - 1.6, -sy / 2 + 6.0, 0.0, 3.2)),   # overhangs the board edge
             ("MCU module", mech.box(-9.0, 9.0, -5.0, 20.0, 0.0, 3.2)),
             ("electrolytic C", cyl(8.0, 0.0, 11.0, 15.0, 25.0)),
             ("LED", mech.box(-1.0, 1.0, 30.0, 32.0, 0.0, 1.0))]
    return board, parts


# ================================================================ build
def build():
    t0 = time.time()
    mech.reset()
    board, parts = electronics()
    bb = Compound([board] + [s for _, s in parts]).bounding_box()
    bbb = board.bounding_box()
    # cavity = electronics envelope + air; outer = cavity + wall (in plan: board outline; height: tallest part)
    in_w, in_l = bbb.size.X + 2 * GAP_XY, bbb.size.Y + 2 * GAP_XY
    xc, yc = (bbb.min.X + bbb.max.X) / 2, (bbb.min.Y + bbb.max.Y) / 2
    z_floor, z_ceil = bbb.min.Z - GAP_BOTTOM, bb.max.Z + GAP_TOP
    z_bot, z_top = z_floor - WALL, z_ceil + WALL
    z_split = (z_floor + z_ceil) / 2
    r_in = max(CORNER_R - WALL, 0.5)
    outer = soften(Pos(xc, yc, z_bot) * mech.extrude(RectangleRounded(in_w + 2 * WALL, in_l + 2 * WALL, CORNER_R),
                                                     z_top - z_bot), EDGE_CH, EDGE_R)
    cavity = Pos(xc, yc, z_floor) * mech.extrude(RectangleRounded(in_w, in_l, r_in), z_ceil - z_floor)
    mech.CAVITY.append(cavity)
    top, bottom = split_z(outer - cavity, z_split)

    # lip joint: tongue on the bottom shell, rebate (tongue + CLR) in the top shell
    def ring(grow0, grow1, z0, z1):
        a = Pos(xc, yc, z0) * mech.extrude(RectangleRounded(in_w + 2 * grow1, in_l + 2 * grow1, r_in + grow1), z1 - z0)
        b = Pos(xc, yc, z0 - 1) * mech.extrude(RectangleRounded(in_w + 2 * grow0, in_l + 2 * grow0, r_in + grow0), z1 - z0 + 2)
        return a - b
    bottom += feat("lip tongue", ring(0.0, LIP["w"], z_split - 0.01, z_split + LIP["h"]))
    top -= ring(-CLR, LIP["w"] + CLR, z_split - 0.01, z_split + LIP["h"] + CLR)

    # PCB standoffs + pins (bottom), screw bosses (top), screw head pocket + clearance (bottom)
    z_pcb_bot = bbb.min.Z
    for x, y in HOLES:
        bottom += feat(f"standoff {x},{y}", cyl(STANDOFF_D, z_floor - 0.5, z_pcb_bot, x, y))
        top += feat(f"screw boss {x},{y}", cyl(SCREW["boss_d"], bbb.max.Z + 0.2, z_ceil + 0.5, x, y))
        top -= cyl(SCREW["pilot_d"], bbb.max.Z, z_ceil - 1.2, x, y)
        bottom -= cyl(SCREW["head_d"], z_bot - 1, z_bot + SCREW["head_h"], x, y)
        bottom -= cyl(SCREW["clear_d"], z_bot, z_pcb_bot + 0.1, x, y)

    # connector cut-outs: every part that sticks out of the cavity gets a hole (body + CONNECTOR_CLR)
    for name, s in parts:
        p = s.bounding_box()
        if p.min.Y < cavity.bounding_box().min.Y:            # back wall (-Y)
            sk = RectangleRounded(p.size.X + 2 * CONNECTOR_CLR, p.size.Z + 2 * CONNECTOR_CLR,
                                  CONNECTOR_CLR + 0.3)          # bounding-box hole; shape it to the real body later
            hole = wall_cut(sk, yc - in_l / 2 + 0.5, yc - in_l / 2 - WALL - 1, (p.min.X + p.max.X) / 2, (p.min.Z + p.max.Z) / 2)
            top -= hole
            bottom -= hole
    print(f"  build {time.time() - t0:.1f}s")
    return dict(top=top, bottom=bottom)


def preview_parts(P):
    """Everything the preview / renders show. Electronics hidden by default (toggle in the viewer)."""
    board, parts = electronics()
    return [
        {"name": "top", "label": "top shell", "shape": P["top"], "color": (0.15, 0.15, 0.17)},
        {"name": "bottom", "label": "bottom shell", "shape": P["bottom"], "color": (0.22, 0.22, 0.25)},
        {"name": "pcb", "label": "PCB", "shape": board, "color": (0.1, 0.45, 0.2), "visible": False},
        {"name": "components", "label": "components", "shape": Compound([s for _, s in parts]),
         "color": (0.55, 0.55, 0.6), "visible": False},
    ]


def run_checks(P):
    from checks import collisions, fits, local, validity
    board, parts = electronics()
    ok = validity(P)
    hits = collisions(P, parts + [("PCB", board)], walls=("top", "bottom"))
    fits([("top ↔ bottom", P["top"], P["bottom"])])
    return ok and not hits


if __name__ == "__main__":
    t0 = time.time()
    P = build()
    run_checks(P)
    os.makedirs("out", exist_ok=True)
    for k, v in P.items():
        export_step(v, f"out/{k}.step")
    parts = preview_parts(P)
    from preview import publish
    publish(parts, title=TITLE, lang=LANG)
    if "--headless" in sys.argv or os.environ.get("HEADLESS"):
        from render import render_views
        render_views(parts)
    print(f"done in {time.time() - t0:.1f}s")
