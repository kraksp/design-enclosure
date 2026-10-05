"""Outline (envelope) drawing: top view + side view with overall dimensions, notes and a title block.
Typical audience: packaging suppliers, mechanical integrators, quotation requests.

    from drawing import outline_drawing
    outline_drawing(assembly, body=[top, bottom], title="Device – overall dimensions", notes=[...], lang="pl")

assembly – everything visible from outside (shells, side parts, protruding connectors, buttons, labels)
body     – shapes that define the "body" envelope (without protrusions)
Hidden-line projection (HLR) of the real 3D model, 1:1 on A4/A3 when it fits (else 1:2), PDF + PNG.
"""
import datetime
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from build123d import Compound, Plane

HERE = os.path.dirname(os.path.abspath(__file__))
LW_EDGE, LW_THIN, FONT = 0.35, 0.18, 8.5
TXT = {
    "pl": dict(top="WIDOK Z GÓRY", side="WIDOK Z BOKU", overall="gabaryt", body="korpus", notes="UWAGI",
               scale="skala", units="wymiary w mm", print_="druk 100%",
               n1="Gabaryt całkowity: {L} × {W} × {H} mm (dł. × szer. × wys.)",
               n2="Korpus bez elementów wystających: {L} × {W} × {H} mm", tol="Tolerancja wymiarów gabarytowych ±{t} mm."),
    "en": dict(top="TOP VIEW", side="SIDE VIEW", overall="overall", body="body", notes="NOTES",
               scale="scale", units="dimensions in mm", print_="print at 100%",
               n1="Overall envelope: {L} × {W} × {H} mm (L × W × H)",
               n2="Body without protrusions: {L} × {W} × {H} mm", tol="Envelope tolerance ±{t} mm."),
}
SHEETS = {"A4": (297.0, 210.0), "A3": (420.0, 297.0)}


def _fmt(v, lang, n=1):
    s = f"{v:.{n}f}"
    return s.replace(".", ",") if lang == "pl" else s


def _project(shape, plane):
    local = plane.to_local_coords(shape)
    visible, _ = local.project_to_viewport((0, 0, 5000), (0, 1, 0), (0, 0, 0))
    return list(visible), local.bounding_box()


def _edges(ax, edges, ox, oy, s):
    for e in edges:
        n = max(2, int(e.length / 0.3))
        pts = [e.position_at(i / n) for i in range(n + 1)]
        ax.plot([p.X * s + ox for p in pts], [p.Y * s + oy for p in pts], color="black", lw=LW_EDGE, solid_capstyle="round")


def _hdim(ax, xa, xb, ya, yb, y, text):
    sgn = 1 if y > max(ya, yb) else -1
    for x, y0 in ((xa, ya), (xb, yb)):
        ax.plot([x, x], [y0 + sgn * 1.0, y + sgn * 1.5], color="black", lw=LW_THIN)
    ax.annotate("", xy=(xa, y), xytext=(xb, y), arrowprops=dict(arrowstyle="<|-|>", lw=LW_THIN, color="black",
                                                               shrinkA=0, shrinkB=0, mutation_scale=7))
    ax.text((xa + xb) / 2, y + sgn * 1.0, text, ha="center", va="bottom" if sgn > 0 else "top", fontsize=FONT)


def _vdim(ax, ya, yb, xa, xb, x, text):
    sgn = 1 if x > max(xa, xb) else -1
    for y, x0 in ((ya, xa), (yb, xb)):
        ax.plot([x0 + sgn * 1.0, x + sgn * 1.5], [y, y], color="black", lw=LW_THIN)
    ax.annotate("", xy=(x, ya), xytext=(x, yb), arrowprops=dict(arrowstyle="<|-|>", lw=LW_THIN, color="black",
                                                               shrinkA=0, shrinkB=0, mutation_scale=7))
    ax.text(x + sgn * 1.2, (ya + yb) / 2, text, ha="left" if sgn > 0 else "right", va="center", fontsize=FONT)


def outline_drawing(assembly, body, title, notes=(), lang="pl", tol=0.3, stem="outline_drawing"):
    t = TXT[lang]
    f = lambda v: _fmt(v, lang)
    asm = assembly if isinstance(assembly, Compound) else Compound(list(assembly))
    bod = Compound(list(body)).bounding_box()
    abb = asm.bounding_box()
    long_y = abb.size.Y >= abb.size.X              # long axis horizontal on the sheet
    if long_y:   # top: page x = Y, page y = -X ; side seen from +X: page x = Y, page y = Z
        top_pl = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(0, 0, 1))
        side_pl = Plane(origin=(0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
        L0, L1, B0, B1 = abb.min.Y, abb.max.Y, bod.min.Y, bod.max.Y
    else:        # top: page x = X, page y = Y ; side seen from -Y (front): page x = X, page y = Z
        top_pl = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, 0, 1))
        side_pl = Plane(origin=(0, 0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        L0, L1, B0, B1 = abb.min.X, abb.max.X, bod.min.X, bod.max.X
    top_e, tbb = _project(asm, top_pl)
    side_e, sbb = _project(asm, side_pl)
    L_all, W_all, H_all = L1 - L0, tbb.size.Y, sbb.size.Y
    body_L = B1 - B0
    body_W = bod.size.X if long_y else bod.size.Y
    body_H = bod.size.Z

    need_w, need_h = L_all + 140, W_all + H_all + 175
    for sheet, s in (("A4", 1.0), ("A3", 1.0), ("A3", 0.5), ("A3", 0.25)):
        pw, ph = SHEETS[sheet]
        if need_w * s <= pw and need_h * s + (1 - s) * 60 <= ph:
            break
    fig = plt.figure(figsize=(pw / 25.4, ph / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, pw); ax.set_ylim(0, ph); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(plt.Rectangle((10, 10), pw - 20, ph - 20, fill=False, lw=0.7))

    X = lambda v: (v - L0) * s + (pw - L_all * s) / 2
    ox = X(0)
    top_cy = ph - 45 - (W_all * s) / 2
    oy_top = top_cy - (tbb.min.Y + tbb.max.Y) / 2 * s
    side_bottom = top_cy - W_all * s / 2 - 45
    oy_side = side_bottom - sbb.max.Y * s
    yt_top, yt_bot = oy_top + tbb.max.Y * s, oy_top + tbb.min.Y * s
    zs_top, zs_bot = oy_side + sbb.max.Y * s, oy_side + sbb.min.Y * s

    _edges(ax, top_e, ox, oy_top, s)
    ax.text(X((L0 + L1) / 2), yt_top + 30, t["top"], ha="center", fontsize=11, weight="bold")
    _hdim(ax, X(L0), X(L1), yt_top, yt_top, yt_top + 20, f"{f(L_all)}  ({t['overall']})")
    if abs(body_L - L_all) > 0.05:
        _hdim(ax, X(B0), X(B1), yt_top, yt_top, yt_top + 11, f"{f(body_L)}  ({t['body']})")
        for a, b in ((L0, B0), (B1, L1)):
            if b - a > 0.05:
                _hdim(ax, X(a), X(b), yt_bot, yt_bot, yt_bot - 8, f(b - a))
    _vdim(ax, yt_bot, yt_top, X(B1) - 10, X(B1) - 10, X(L1) + 10, f(W_all))

    _edges(ax, side_e, ox, oy_side, s)
    ax.text(X((L0 + L1) / 2), zs_top + 12, t["side"], ha="center", fontsize=11, weight="bold")
    _hdim(ax, X(L0), X(L1), zs_bot, zs_bot, zs_bot - 10, f(L_all))
    _vdim(ax, zs_bot, zs_top, X(L1) - 10, X(L1) - 10, X(L1) + 10, f(H_all))
    if abs(body_H - H_all) > 0.05:
        _vdim(ax, zs_bot, zs_bot + body_H * s, X(L0) + 10, X(L0) + 10, X(L0) - 10, f(body_H))

    lines = [t["n1"].format(L=f(L_all), W=f(W_all), H=f(H_all)), t["n2"].format(L=f(body_L), W=f(body_W), H=f(body_H))]
    lines += list(notes) + [t["tol"].format(t=_fmt(tol, lang))]
    ax.text(20, 62, t["notes"], fontsize=9.5, weight="bold", va="top")
    for i, line in enumerate(lines):
        ax.text(20, 55 - i * 5.0, f"{i + 1}. {line}", fontsize=8, va="top")
    tb_w, tb_h = min(150, pw / 2.2), 30
    tb_x = pw - 10 - tb_w
    ax.add_patch(plt.Rectangle((tb_x, 10), tb_w, tb_h, fill=False, lw=0.7))
    ax.plot([tb_x, tb_x + tb_w], [25, 25], color="black", lw=0.4)
    ax.text(tb_x + 4, 32.5, title, fontsize=10.5, weight="bold", va="center")
    sc = "1:1" if s == 1 else f"1:{int(round(1 / s))}"
    ax.text(tb_x + 4, 17.5, f"{t['scale']} {sc} ({sheet}, {t['print_']})    {t['units']}    {datetime.date.today():%Y-%m-%d}",
            fontsize=8, va="center")
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    pdf, png = os.path.join(HERE, "out", f"{stem}.pdf"), os.path.join(HERE, "out", f"{stem}.png")
    fig.savefig(pdf); fig.savefig(png, dpi=150); plt.close(fig)
    print(f"saved {pdf} / .png – envelope {L_all:.2f} × {W_all:.2f} × {H_all:.2f} mm, {sheet} {sc}")
    return pdf, png
