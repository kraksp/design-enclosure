"""Load an electronics STEP (KiCad / Altium / Fusion export) WITH all nested assembly transforms.

build123d's import_step() flattens some assemblies and loses component locations – components then end up
at the origin or rotated. This reader walks the XCAF tree and applies every location.

    board, parts = load("pcb.step")          # board: largest flat part; parts: [(name, Shape), ...]
    report(board, parts)                     # print a short inventory (do this once for every new STEP)

Coordinates stay as exported. Projects should keep them (top copper at z = 0 is the usual convention);
if the export is offset, move the enclosure, not the electronics.
"""
import sys
from OCP.BRep import BRep_Builder
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Compound
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from build123d import Compound

_CACHE = {}


def compound(shapes):
    """Compound from build123d shapes or raw TopoDS shapes."""
    c = TopoDS_Compound()
    b = BRep_Builder()
    b.MakeCompound(c)
    for s in shapes:
        b.Add(c, getattr(s, "wrapped", s))
    return Compound(c)


def load(path, board_name=None):
    """Returns (board, parts). board = part named `board_name` or the largest-footprint thin part."""
    if path in _CACHE:
        return _CACHE[path]
    doc = TDocStd_Document(TCollection_ExtendedString("doc"))
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    if reader.ReadFile(path) != 1:
        raise IOError(f"cannot read STEP: {path}")
    reader.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name(lbl):
        a = TDataStd_Name()
        return a.Get().ToExtString() if lbl.FindAttribute(TDataStd_Name.GetID_s(), a) else "?"

    raw = []

    def walk(lbl, loc):
        if st.IsAssembly_s(lbl):
            comps = TDF_LabelSequence()
            st.GetComponents_s(lbl, comps)
            for i in range(1, comps.Length() + 1):
                c = comps.Value(i)
                ref = TDF_Label()
                st.GetReferredShape_s(c, ref)
                walk(ref, loc.Multiplied(st.GetLocation_s(c)))
        else:
            s = st.GetShape_s(lbl)
            if not s.IsNull():
                raw.append((name(lbl), s.Moved(loc)))

    free = TDF_LabelSequence()
    st.GetFreeShapes(free)
    for i in range(1, free.Length() + 1):
        walk(free.Value(i), TopLoc_Location())
    parts = [(n, compound([s])) for n, s in raw]

    def footprint(p):
        bb = p[1].bounding_box()
        return bb.size.X * bb.size.Y if bb.size.Z < 3.5 else 0      # boards are thin
    if board_name:
        board = next(p for p in parts if p[0] == board_name)
    else:
        board = max(parts, key=footprint)
    result = board[1], [p for p in parts if p is not board]
    _CACHE[path] = result
    return result


def report(board, parts, top=25):
    """Inventory: board outline, tallest/largest components, everything that sticks out of the board outline."""
    bb = board.bounding_box()
    print(f"board  x[{bb.min.X:.2f},{bb.max.X:.2f}] y[{bb.min.Y:.2f},{bb.max.Y:.2f}] z[{bb.min.Z:.2f},{bb.max.Z:.2f}]  "
          f"{len(parts)} parts")
    rows = []
    for n, s in parts:
        b = s.bounding_box()
        out = b.min.X < bb.min.X - 0.05 or b.max.X > bb.max.X + 0.05 or b.min.Y < bb.min.Y - 0.05 or b.max.Y > bb.max.Y + 0.05
        rows.append((b.max.Z, n, b, out))
    print("tallest:")
    for z, n, b, out in sorted(rows, key=lambda r: -r[0])[:top]:
        print(f"  {n[:40]:40} x[{b.min.X:7.2f},{b.max.X:7.2f}] y[{b.min.Y:7.2f},{b.max.Y:7.2f}] z[{b.min.Z:6.2f},{b.max.Z:6.2f}]"
              + ("  <- outside board" if out else ""))
    print("outside the board outline (connectors, switches, LEDs at the edge):")
    for z, n, b, out in rows:
        if out:
            print(f"  {n[:40]:40} x[{b.min.X:7.2f},{b.max.X:7.2f}] y[{b.min.Y:7.2f},{b.max.Y:7.2f}] z[{b.min.Z:6.2f},{b.max.Z:6.2f}]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python step_load.py <electronics.step> [board_part_name]")
    report(*load(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
