"""Headless renders (PNG) for CLI / CI / agents without a browser. Pure Python + numpy (software z-buffer, no OpenGL).

    from render import render_views, render_cut
    render_views(parts)                       # out/render/view_<name>.png + contact sheet out/render/views.png
    render_cut(parts, "y", 10.3)              # exact B-rep cut (filled section faces), seen from the cut side

`parts` = the list of dicts that preview.publish() takes (name, shape, color, opacity, visible).
Command line:  python render.py [--views=iso,top,front] [--cut=y:10.3]   (uses model.build() + model.preview_parts())
Faces get flat Lambert shading, CAD face boundaries and silhouettes are drawn as dark lines.
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from build123d import Box, Pos

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "render")
# camera direction (target -> camera) and screen-up; +Y = front of the device, Z up. "iso" looks at the back-right
# corner like the live viewer, "iso_front" at the front-left one.
VIEWS = {
    "iso": ((0.55, -0.62, 0.56), (0, 0, 1)), "iso_front": ((-0.55, 0.62, 0.56), (0, 0, 1)),
    "iso_below": ((0.55, -0.62, -0.56), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)), "bottom": ((0, 0, -1), (0, 1, 0)),
    "front": ((0, 1, 0), (0, 0, 1)), "back": ((0, -1, 0), (0, 0, 1)),
    "left": ((-1, 0, 0), (0, 0, 1)), "right": ((1, 0, 0), (0, 0, 1)),
}
LIGHT = np.array([0.4, 0.3, 1.0])
LIGHT /= np.linalg.norm(LIGHT)


def _mesh(parts, tol):
    """Triangles of all visible parts: (tri[N,3,3], rgb[N,3], face_id[N])."""
    tris, cols, ids, fid = [], [], [], 0
    for p in parts:
        if not p.get("visible", True) or p.get("shape") is None:
            continue
        base = 0.22 + 0.78 * np.asarray(p.get("color", (0.6, 0.6, 0.6)), float)   # lift near-black colours
        for f in p["shape"].faces():
            try:
                v, t = f.tessellate(tol, 0.3)
            except Exception:
                continue
            if not t:
                continue
            v = np.array([[q.X, q.Y, q.Z] for q in v])
            tris.append(v[np.array(t, dtype=int)])
            cols.append(np.repeat(base[None], len(t), 0))
            ids.append(np.full(len(t), fid))
            fid += 1
    if not tris:
        raise ValueError("nothing to render")
    return np.concatenate(tris), np.concatenate(cols), np.concatenate(ids)


def _camera(view):
    d, up = VIEWS[view] if isinstance(view, str) else view
    d = np.asarray(d, float); d /= np.linalg.norm(d)
    up = np.asarray(up, float)
    right = np.cross(up, d)
    if np.linalg.norm(right) < 1e-6:
        right = np.cross((0, 1, 0), d)
    right /= np.linalg.norm(right)
    return right, np.cross(d, right), d          # screen x, screen y, towards the camera


def _raster(tri, col, ids, view, px=900, margin=0.06):
    rx, ry, rz = _camera(view)
    P = tri @ np.stack([rx, ry, rz], 1)                      # (N,3,3): screen x, y, depth (bigger = closer)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    facing = n @ rz
    lo, hi = P[..., :2].reshape(-1, 2).min(0), P[..., :2].reshape(-1, 2).max(0)
    span = (hi - lo).max() * (1 + 2 * margin)
    W = int(px * (hi - lo)[0] / (hi - lo).max() + 2 * margin * px) + 2
    H = int(px * (hi - lo)[1] / (hi - lo).max() + 2 * margin * px) + 2
    s = px / (hi - lo).max()
    X = (P[..., 0] - lo[0]) * s + margin * px
    Y = (hi[1] - P[..., 1]) * s + margin * px
    Z = P[..., 2]
    zbuf = np.full((H, W), -np.inf)
    img = np.ones((H, W, 3))
    idb = np.full((H, W), -1)
    shade = 0.32 + 0.68 * np.abs(n @ LIGHT)
    rgb = np.clip(col * shade[:, None], 0, 1)
    order = np.argsort(-np.abs(facing))                       # big, facing triangles first – fewer overwrites
    for i in order:
        x, y, z = X[i], Y[i], Z[i]
        x0, x1 = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), W - 1)
        y0, y1 = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), H - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(d) < 1e-12:
            continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
        c = 1 - a - b
        m = (a >= -1e-3) & (b >= -1e-3) & (c >= -1e-3)
        if not m.any():
            continue
        zz = a * z[0] + b * z[1] + c * z[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        w = m & (zz > sub)
        sub[w] = zz[w]
        img[y0:y1 + 1, x0:x1 + 1][w] = rgb[i]
        idb[y0:y1 + 1, x0:x1 + 1][w] = ids[i]
    # lines: face boundaries (id change) and silhouettes (background / depth jump)
    edge = np.zeros((H, W), bool)
    edge[:, 1:] |= idb[:, 1:] != idb[:, :-1]
    edge[1:, :] |= idb[1:, :] != idb[:-1, :]
    img[edge] *= 0.35
    return img


def _save(img, fn, title=None):
    h, w = img.shape[:2]
    fig = plt.figure(figsize=(w / 100, h / 100 + (0.3 if title else 0)), dpi=100)
    ax = fig.add_axes([0, 0, 1, h / (h + (30 if title else 0))])
    ax.imshow(img, interpolation="antialiased"); ax.axis("off")
    if title:
        fig.text(0.5, 1 - 15 / (h + 30), title, ha="center", va="center", fontsize=11)
    fig.savefig(fn); plt.close(fig)


def render_views(parts, views=("iso", "top", "front", "back", "right", "bottom"), tol=0.15, px=800, sheet=True):
    """One PNG per view + a contact sheet. Returns the file list (look at them / send them to the user)."""
    os.makedirs(OUT, exist_ok=True)
    tri, col, ids = _mesh(parts, tol)
    files, imgs = [], []
    for v in views:
        img = _raster(tri, col, ids, v, px)
        fn = os.path.join(OUT, f"view_{v}.png")
        _save(img, fn, v)
        files.append(fn); imgs.append((v, img))
    if sheet and len(imgs) > 1:
        cols = min(3, len(imgs))
        rows = (len(imgs) + cols - 1) // cols
        fig, axs = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4.2), squeeze=False)
        for ax in axs.flat:
            ax.axis("off")
        for ax, (v, img) in zip(axs.flat, imgs):
            ax.imshow(img); ax.set_title(v, fontsize=11)
        fig.tight_layout()
        fn = os.path.join(OUT, "views.png")
        fig.savefig(fn, dpi=100); plt.close(fig)
        files.append(fn)
    print("rendered:", *[os.path.relpath(f, HERE) for f in files])
    return files


def render_cut(parts, axis, value, keep="below", views=(), tol=0.1, px=900):
    """Exact section: each part is intersected with a half-space (B-rep boolean), so cut faces are real faces.
    keep='below' keeps coordinates < value and looks at the cut from the + side."""
    big = 5000
    half = Pos(*[value + (-big / 2 if keep == "below" else big / 2) if a == axis else 0 for a in "xyz"]) * Box(big, big, big)
    cut = []
    for p in parts:
        if p.get("visible", True) and p.get("shape") is not None:
            s = p["shape"] & half
            if s is not None and s.solids():
                cut.append({**p, "shape": s})
    sgn = 1 if keep == "below" else -1
    straight = {"x": ((sgn, 0, 0), (0, 0, 1)), "y": ((0, sgn, 0), (0, 0, 1)), "z": ((0, 0, sgn), (0, 1, 0))}[axis]
    oblique = {"x": ((sgn, -0.45, 0.35), (0, 0, 1)), "y": ((0.45, sgn, 0.35), (0, 0, 1)), "z": ((0.4, -0.5, sgn), (0, 0, 1))}[axis]
    os.makedirs(OUT, exist_ok=True)
    tri, col, ids = _mesh(cut, tol)
    files = []
    for name, v in [("straight", straight), ("oblique", oblique)] + [(w, w) for w in views]:
        img = _raster(tri, col, ids, v, px)
        fn = os.path.join(OUT, f"cut_{axis}{value:g}_{name}.png")
        _save(img, fn, f"{axis} = {value:g} mm ({name})")
        files.append(fn)
    print("rendered:", *[os.path.relpath(f, HERE) for f in files])
    return files


if __name__ == "__main__":
    import model                                          # the project's model.py
    parts = model.preview_parts(model.build())
    views, cuts = ("iso", "top", "front", "back", "right", "bottom"), []
    for a in sys.argv[1:]:
        if a.startswith("--views="):
            views = tuple(a.split("=", 1)[1].split(","))
        elif a.startswith("--cut="):                      # --cut=y:10.3
            ax_, val = a.split("=", 1)[1].split(":")
            cuts.append((ax_, float(val)))
    render_views(parts, views)
    for ax_, val in cuts:
        render_cut(parts, ax_, val)
