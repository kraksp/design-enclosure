# Preview: live viewer and headless renders

## Live viewer (`viewer/index.html`)

`preview.publish(parts, title=..., lang="pl"|"en")` writes `viewer/part_<name>.glb` + `viewer/scene.json`.
The page polls `scene.json` every 1.5 s and reloads the parts (layer toggles survive reloads).

Serve: `python -m http.server 8765 --bind 127.0.0.1 --directory viewer`, open http://localhost:8765.
(In agent hosts with a launch / dev-server config, register this command once and reuse it.)

What the user gets:
- layer list – one checkbox per part (electronics hidden by default),
- views: iso, top, front (+Y), back, left, right, bottom,
- section plane in X / Y / Z with a slider and flip; opaque parts get filled caps in their colour,
- "2D sections" tab with every sheet saved by `sections.save_sheet()` (`viewer/sections/index.json`).

Part dict: `name` (file-safe), `shape`, `label`, `color` (0..1), `opacity` (< 1 → no section cap, e.g. light pipes),
`visible`, `static` (export once – for large unchanged STEP data such as the PCB).

JS API for an agent driving the page (run in the page context):

```js
setView('back')                    // iso | top | front | back | left | right | bottom
cutAt('y', -30, false)             // axis, position in mm, flip
clipAt(0, 1, 0, 25)                // arbitrary plane: normal + constant
noClip()
look(-12, -95, 12, -15.8, -60, 4)  // camera position, target (mm, model coordinates) – close-ups
show('top shell', false)           // toggle a layer by its label
open2d()                           // open the 2D sections tab
```

Verification recipe in a browser: reload → wait ~3 s → `look(...)` at the changed spot → screenshot; for fits use
`cutAt(...)` through the spot and screenshot again. Reset any viewport emulation afterwards.

## Headless (`render.py`)

No browser, no OpenGL: faces are tessellated and rasterised with a numpy z-buffer (correct occlusion, flat shading,
CAD face boundaries as lines). ~1 s per view for a simple box, ~3 s for a detailed 160 mm enclosure.

```python
from render import render_views, render_cut
render_views(parts, views=("iso", "top", "front", "back", "right", "bottom"))   # + out/render/views.png sheet
render_cut(parts, "y", 10.3)          # exact B-rep cut, straight and oblique look into the cut
render_cut(parts, "x", -15.8, keep="above")
```

Views: `iso` (back-right corner, as in the live viewer), `iso_front`, `iso_below`, `top`, `bottom`, `front`, `back`, `left`, `right`, or a custom
`((dx, dy, dz), (upx, upy, upz))` camera direction. Hide electronics with `visible=False` in the part dict, or pass a
filtered list (e.g. only the shell + the switch) for close-up checks.

Use headless renders also in live mode when you need an exact cut (B-rep, not a clipping plane) or a picture for a report.

## VS Code

With the OCP CAD Viewer extension: `OCP_VSCODE=1 python model.py` also sends the parts to the VS Code panel.
