"""2D section sheets (matplotlib) – the main way to SHOW fits, clearances and wall thicknesses.

    from sections import sec_x, sec_y, sec_z, draw, note, save_sheet, new_sheet
    fig, axs = new_sheet(2, 2)
    draw(axs[0], sec_x(12.0), [(top, "#2b2b2e", "top"), (cap, "#4a90d9", "button")], (-10, 10), (10, 25), "YZ at x = 12")
    note(axs[0], "0.3 mm gap", xy=(5.3, 21.5), xytext=(7, 24))
    save_sheet(fig, "button", title="button", label="Button cap in the top shell – XZ / YZ / plan")

Each sheet lands in out/<stem>.png and in the viewer's "2D sections" tab (viewer/sections/index.json).
Items are drawn in order – later items on top. Holes in a section are drawn white.
"""
import json
import os
import shutil
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from build123d import Face, Plane

HERE = os.path.dirname(os.path.abspath(__file__))


def sec_x(x):
    """Section plane x = const, drawn as (Y, Z)."""
    return Plane(origin=(x, 0, 0), x_dir=(0, 1, 0), z_dir=(-1, 0, 0)), "Y", "Z"


def sec_y(y):
    """Section plane y = const, drawn as (X, Z)."""
    return Plane(origin=(0, y, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0)), "X", "Z"


def sec_z(z):
    """Section plane z = const (plan view), drawn as (X, Y)."""
    return Plane(origin=(0, 0, z), x_dir=(1, 0, 0), z_dir=(0, 0, 1)), "X", "Y"


def polygons(shape, plane, step=0.04):
    """[(points3d, is_hole)] of the section of `shape` with `plane`."""
    cut = shape & Face.make_rect(2000, 2000, plane)
    out = []
    if cut is None:
        return out
    for f in cut.faces():
        for w, hole in [(f.outer_wire(), False)] + [(iw, True) for iw in f.inner_wires()]:
            pts = []
            for e in w.edges():
                n = max(2, int(e.length / step))
                pts += [e.position_at(i / n) for i in range(n)]
            out.append((pts, hole))
    return out


def draw(ax, sec, items, xlim, ylim, title):
    """sec = sec_x/sec_y/sec_z(...); items = [(shape, color, legend_label_or_None)]."""
    plane, u, v = sec
    for k, (shape, col, lab) in enumerate(items):
        first = True
        for pts, hole in polygons(shape, plane):
            ax.add_patch(Polygon([(getattr(p, u), getattr(p, v)) for p in pts], closed=True, fc="white" if hole else col,
                                 ec=col, lw=0.6, zorder=2 * k + (3 if hole else 2),
                                 label=lab if first and not hole and lab else None))
            first = False
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.grid(True, lw=0.3, alpha=0.6)
    ax.set_title(title, fontsize=10.5); ax.set_xlabel(f"{u} [mm]"); ax.set_ylabel(f"{v} [mm]")


def note(ax, text, xy, xytext, color="black"):
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=8.5, color=color,
                arrowprops=dict(arrowstyle="->", lw=0.7, color=color), zorder=60)


def new_sheet(rows=1, cols=1, size=(13, 13)):
    fig, axs = plt.subplots(rows, cols, figsize=size, squeeze=False)
    return fig, [a for row in axs for a in row]


def save_sheet(fig, stem, title, label, dpi=115):
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    sec_dir = os.path.join(HERE, "viewer", "sections")
    os.makedirs(sec_dir, exist_ok=True)
    fn = os.path.join(HERE, "out", f"{stem}.png")
    fig.tight_layout()
    fig.savefig(fn, dpi=dpi)
    plt.close(fig)
    shutil.copy(fn, os.path.join(sec_dir, f"{stem}.png"))
    idx_path = os.path.join(sec_dir, "index.json")
    try:
        idx = json.load(open(idx_path, encoding="utf-8"))
    except Exception:
        idx = []
    idx = [e for e in idx if e["file"] != f"sections/{stem}.png"] + [{"file": f"sections/{stem}.png", "title": title, "label": label}]
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", fn)
    return fn


def remove_sheet(stem):
    """Drop a sheet that no longer applies (e.g. a removed variant) from out/ and from the viewer tab."""
    for p in (os.path.join(HERE, "out", f"{stem}.png"), os.path.join(HERE, "viewer", "sections", f"{stem}.png")):
        if os.path.exists(p):
            os.remove(p)
    idx_path = os.path.join(HERE, "viewer", "sections", "index.json")
    if os.path.exists(idx_path):
        idx = [e for e in json.load(open(idx_path, encoding="utf-8")) if e["file"] != f"sections/{stem}.png"]
        json.dump(idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
