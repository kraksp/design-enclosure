---
name: design-enclosure
description: Designs enclosures and mechanical parts for electronic devices as parametric Python models (build123d), starting from a text description, electronics STEP files (PCB assemblies) or photos and brochures. Checks collisions and clearances against the electronics, shows a live browser preview with toggleable layers and section planes (or headless PNG renders from several views), produces 2D section sheets, STEP files per part and dimensioned outline drawings. Use when asked to design, modify or review an enclosure, housing, case, cover, bracket, button, light pipe or similar part around electronics, or to prepare STEP files or drawings for MJF, FDM or injection molding.
license: Apache-2.0
compatibility: Python 3.10+ with build123d 0.10+, numpy, matplotlib. Any agent that can run Python and read PNG files; a browser is optional.
metadata:
  version: "1.0"
  repository: https://github.com/kraksp/design-enclosure
---

# Design enclosure

Parametric CAD in code: every dimension is a named parameter, every change is rebuilt, verified and shown as a
picture before it is reported. The person you work for is usually visual – show, don't describe.

## Working loop

Run this loop for the first model and again after every change.

1. **Set up once per session.**
   - Run `python <skill>/scripts/check_env.py`. It needs build123d, OCP, numpy and matplotlib.
   - Pick the preview mode:
     - **Live:** use this when you can open and screenshot a browser (built-in browser pane, Playwright or computer use). Serve `viewer/` and drive it with the JS API in [references/preview.md](references/preview.md).
     - **Headless:** use this in a CLI, CI or a sandbox without a display. Run `python model.py --headless` and look at `out/render/*.png`.
   - In both modes, open the PNGs yourself before you report anything. Send them to the user if your client can attach files.
2. **Take in the inputs** as described in [references/inputs.md](references/inputs.md): STEP electronics, photos and brochures, or a plain description.
   - Before modelling, settle the reference geometry, the manufacturing process and the clearance set. Ask about these only when they are missing.
   - State every assumption in device coordinates, for example "bottom = the −Z face, front = +Y with the connectors".
3. **Scaffold the project**: `python <skill>/scripts/new_project.py <dir> --name "<Device>" [--step pcb.step] [--lang pl|en]`.
   - This copies a working template: a two-shell box with standoffs, screws, a lip joint and connector cut-outs.
   - Grow `model.py` from it. Keep the helper modules unchanged unless they have a bug.
4. **Model.** Put every dimension in the PARAMETERS block, with a one-line comment giving the reason.
   - `build()` returns a dict of parts.
   - Every solid added inside the cavity (bosses, ribs, pins, sleeves, moving parts) goes through `feat(name, solid)` so that the collision check sees it.
   - Design rules and proven patterns: [references/design-rules.md](references/design-rules.md).
   - API traps: [references/build123d-notes.md](references/build123d-notes.md).
5. **Verify** every rebuild. `python model.py` runs the first three checks:
   - `validity`: every part must be one valid solid unless it is meant to be several.
   - `collisions` against every electronic component. Expected contacts are listed explicitly; anything else must be 0.
   - `fits`: measure the specific gaps you designed, using `local()` boxes. The global minimum distance is not enough.
   - A 2D section sheet (`sections.py`) through every spot you changed. It lands in the viewer's "2D sections" tab.
   - A look at the result: a viewer screenshot of the area, or `render_cut()` / `render_views()` in headless mode.
6. **Report briefly.**
   - What changed, with the key numbers: clearances, wall thicknesses, protrusions.
   - The image.
   - What was not changed, and which files must be re-printed or re-ordered.
   - Any assumption the user should confirm.
7. **Deliver.**
   - `out/<part>.step` for each part.
   - The outline drawing (`drawing.outline_drawing`): PDF at 1:1, comma decimals for Polish.
   - A README with inputs, design decisions and open issues. Keep it current: it is the memory of the project.

## Rules learned on real projects

- **Do exactly what was asked.**
  - "Don't change X" is a hard constraint.
  - "Only answer" or "just propose" means no edits.
  - "Go back to version N" means restore exactly, re-run the checks and say what is now different from the user's reference.
- **Never trade a requirement for a local exception.** If thicker walls do not fit, grow the outline. Do not thin the wall where the battery is. Local narrowings, steps and missing ribs look like defects on the print.
- **Check a claim with numbers before you promise it.** Example: a recess around a button does not reduce how far the button protrudes. Compute protrusions, gaps and wall thicknesses before you state them.
- **Tolerances stack up at moving parts.** A cap held rigidly by the shell over a tact switch with 0.25 mm of travel will either jam or stay pressed: the PCB alone plays ±0.2 mm on its pins, the print ±0.2 mm. Prefer a floating cap that rides on the actuator, or a plain hole. See design-rules.md under Buttons.
- **Keep alternatives switchable while the user is exploring**, for example `BACK_CAP = False`. Remove stale outputs (old STEP files, sheets) when a variant is dropped.
- **Ambiguous words** such as "bottom", "left", "closer to the bottom" or "one third": pick the reading that matches the user's viewer orientation, say it in one line, and keep the dimension in a parameter that is easy to flip.
- **Moving the whole design is cheap; moving the electronics is not.** Keep the electronics coordinates and move or grow the enclosure. Check the side effects: connector depth behind the wall, button protrusion, logo centring.
- **Units are mm.** Number format follows the user's language (`12,5` in Polish drawings).

## Project layout (created by new_project.py)

| file | role |
|---|---|
| `model.py` | parameters, `electronics()`, `build()`, `preview_parts()`, `run_checks()`; `python model.py [--headless]` |
| `mech.py` | primitives (`cyl`, `rrect`, `box`, `wall_cut`, `soften`, `split_z`, `fuse_all`) and the `feat()` registry |
| `step_load.py` | STEP reader that keeps nested assembly transforms; `python step_load.py pcb.step` prints an inventory |
| `checks.py` | `validity`, `collisions`, `fits`, `local` |
| `sections.py` | 2D section sheets → `out/*.png` + viewer tab |
| `render.py` | headless PNG views and exact cuts (numpy z-buffer, no OpenGL) |
| `drawing.py` | outline drawing (HLR top + side view, overall / body dimensions, notes, title block) |
| `preview.py` + `viewer/` | browser preview: GLB per part, layer toggles, views, filled section plane, 2D tab |

Coordinates: the electronics frame. The top copper of the main PCB is at z = 0, +Y is the front, −Y the back and X the width. The viewer's view buttons assume this.

## Commands

```bash
python model.py                    # build + checks + STEP to out/ + preview files
python model.py --headless         # + out/render/views.png (iso, top, front, back, right, bottom)
python render.py --views=iso,back --cut=y:-30      # extra views / an exact section render
python -m http.server 8765 --bind 127.0.0.1 --directory viewer   # live preview, reloads every 1.5 s
python step_load.py path/to/pcb.step               # what is on the board, what sticks out of it
```
