# Design rules and proven patterns

## Processes

| | MJF (PA12) | FDM (0.4 nozzle) | Injection molding |
|---|---|---|---|
| tolerance | ±0.2 mm (or ±0.2 %) | ±0.1–0.2, holes print undersize | ±0.05–0.1 |
| min wall / feature | 0.5 (aim ≥ 0.8) | 0.8 = 2 lines; 1.2 = 3 lines (reliable) | 0.8–1.0; nominal 1.8–2.5 uniform |
| sliding fit per side | 0.2 | 0.2 | 0.05–0.1 |
| button cap in a hole per side | 0.3 | 0.3 | 0.15 |
| notes | no supports, rough surface | elephant foot ≈ 0.15 on the first layer – chamfer bed edges 0.5; bridges / overhangs; printed upside-down recesses fail | draft 1–2°, no undercuts (or slides/lifters), core out thick sections |

Default: one clearance set that works for both MJF and FDM prototypes (0.2 per side, 0.3 for button caps, walls ≥ 0.8,
≥ 1.2 where FDM must join perimeters).

## Shells

- Plan: rounded rectangle; edges: chamfer + round on top / bottom perimeter (`mech.soften`).
- Split into top / bottom at a height that avoids connectors; joint = tongue on one shell, rebate (+ clearance) in the
  other – only where the wall is solid (not where an inlay groove is).
- Walls of the bottom fall inward on tall FDM prints: add a **skirt** on the top shell (band 1.2 × 2.5 mm, 0.2 inside
  the bottom's inner wall) – it holds the walls when closed. Interrupt only for real obstacles (nuts, connectors).
- Uniform wall thickness everywhere. If something does not fit, **grow the outline**; never thin one spot.
- Side bands / inlays in a groove: groove depth + wall behind ≥ 1.2–1.6; where the band wraps the corner arc,
  thicken the wall from inside parallel to the outside, and let that thickening overlap the straight wall by ≥ 2 mm
  in one step – so FDM perimeters join instead of leaving a gap at the corner.
- Corner print gaps in FDM = two perimeters just touching; give the slicer ≥ 0.8 mm common width.

## Fixing the electronics

- PCB on standoffs + locating pins (pin Ø = hole − 0.4) from the bottom, hold-down tubes from the top (+0.15 gap).
- Screws from below through the PCB mounting holes: head pocket, clearance hole, pilot hole in the top boss.
  Bosses near tall parts can be shortened (no socket) – check collisions.
- Battery pack: cradle ribs shaped to the pack (+0.4), hold-down ribs from the top, a stop at the end, room for the wire
  exit and its bend (≥ 2 mm, ask where the wires leave the pack).
- Magnets: pocket from inside, ≥ 0.8 mm floor; a raised rim around the pocket if the floor gets too thin.

## Openings

- Connector holes: tight around the visible body (+0.2), larger from inside for mounting tabs.
- USB-C face ≤ 0.7 mm behind the outside, or a small recess (≈ 11.4 × 5.4 × 0.8, stadium) around it.
- Panel jacks: D-hole with flats; counterbore from inside for the washer, keep ≥ 1.5 mm wall at the jack; model the nut
  and check it against the PCB.
- Light pipes: sleeve from the ceiling (ID for the pipe collar, ≤ 15 mm long, lead-in chamfer at the bottom), small
  hole in the top for the tip. Ask the user for the real fit before changing light-pipe holes.
- Label / nameplate recess: plate + 0.5 per side, corner R ≥ plate R, depth 0.2 for a foil label (0.5 for aluminium);
  keep it off magnet pockets and screw heads.

## Buttons

- **Top buttons over tact switches: flexure bar.** One part with two caps on spring arms (1.2 mm), a mounting block
  pinned to the ceiling with two Ø2.4 pins (heat-staked), pads under the caps that hide the gap, pusher Ø3 0.25 mm
  above the actuator, caps 0.5 below the surface with a 0.5 chamfer (hides FDM elephant foot), 0.3 gap in the hole.
  Works because the arm compliance absorbs the tolerances in Z.
- **Side switch with a short actuator (travel 0.25 mm): no rigid cap.** A cap fixed to the shell jams or stays pressed
  (PCB play ±0.2 + print ±0.2 > travel). Use, in this order:
  1. a plain hole Ø(actuator + 0.4), actuator protruding ~0.5 mm (simplest, always works),
  2. a loose cap riding on the actuator: pocket Ø(actuator + 0.4), 0.1 in front of the tip, flange inside ≥ 0.8 from the
     wall, flange cut away where it would touch the PCB (≥ 1.2 mm above it), 0.3 gap in the wall hole,
  3. a cap pressed on the actuator (crush ribs) – sensitive to FDM hole shrinkage, test before relying on it.
- A recess around a button frames it but does not change how far it protrudes – only the wall position does.

## Injection molding (when asked "what would it take")

- Draft 1–2° on all walls along the pull direction (0.5° absolute minimum); textured faces need about 1° more per
  0.025 mm of texture depth.
- Uniform nominal wall 1.8–2.5 mm; ribs 0.5–0.6 × wall; core out bosses (OD ≈ 2 × screw, wall 0.6 × nominal).
- Everything perpendicular to the pull is an undercut: side holes (USB, jacks, buttons in side walls) → slides; inlay
  grooves on side walls → slides on both sides (expensive – prefer flat recesses without undercut); horizontal pins
  from walls → lifters (prefer features that release in the pull direction).
- Family mold: top + bottom (similar volume, same material/colour, always used as a pair) is a good candidate;
  small flexible parts (button bars – POM/PP) and transparent / soft parts go to separate tools.
- Online instant quotes (e.g. Xometry) price one part per file – upload parts separately and ask for a family mold in
  the notes.
