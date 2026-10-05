# Inputs

Three kinds of starting point, often mixed. Whatever the input, end up with: reference geometry in device
coordinates, a list of interfaces (everything that touches the outside world), the process, and the clearance set.

## 1. Electronics STEP (PCB assembly)

1. `python step_load.py board.step` – inventory: board outline, tallest parts, parts outside the board outline.
   Always load through `step_load.load()` (keeps nested transforms); `import_step()` misplaces components.
2. Identify the interfaces from the inventory, then confirm with the user in one message:
   connectors at the edges (USB-C, terminals, banana jacks), switches and their actuator tips, LEDs (light pipes),
   mounting holes, tall parts (capacitors, inductors, TO-220), the battery and its wires, anything mounted in the wall
   (panel jacks are positioned by the wall, not by the PCB – move them with their holes).
3. Measure from the model, not from assumptions: e.g. actuator tip y, connector face y, part heights. Print them.
4. STEP data is often wrong in small ways (a jack not rotated, a missing nut, a generic battery). When the user says
   reality differs, model the real part as an `extra` body for the checks and note the pseudo-collision in the README.
5. Things the STEP does not contain – ask: battery pack (dimensions, wire exit), cables and their bend space,
   magnets, labels, screws (head Ø, length, thread core Ø), light pipe Ø, nut sizes.

## 2. Photos, brochures, datasheets, an existing product

- Get a scale: a dimensioned drawing, a datasheet, a known part in the photo (USB-C receptacle 8.94 × 3.16 mm,
  18650 cell Ø18.5 × 65, M3 head Ø5.5, 2.54 mm pin pitch) or a caliper measurement from the user.
- Extract the visual language: plan shape and corner radii, edge treatment (chamfer + round), split line height,
  inlays / side bands, button shape, recess depths, logo placement. Write them as parameters with the source in the
  comment ("R17.4 – measured on the previous model, v2.step").
- If an old CAD model exists, load it and measure it (bounding boxes, sections at a few heights) instead of guessing;
  reuse exact shapes such as logo outlines by extracting faces from it.
- List every dimension that is a guess and get it confirmed before details are built on top of it.

## 3. Plain description

Ask only what blocks the first model (one short message):
- what goes inside (board size or STEP, battery, connectors and on which face),
- how it is mounted and used (desk, wall, magnets, DIN rail, handheld; IP rating),
- process and quantity (MJF / FDM prototype → injection molding?), material, colour,
- hard limits: outer size, look of an existing product family.
Then build a simple first version quickly, show it, and iterate – a picture gets better feedback than questions.

## Reference values worth knowing

| item | typical value |
|---|---|
| USB-C receptacle face | 8.94 × 3.16 mm; plug overmold up to ~12.5 × 6.5 mm – keep the face ≤ 0.7 mm behind the outer wall or add a recess |
| tact switch (side) | Ø3.5 actuator, travel 0.25 mm – see Buttons in design-rules.md |
| light pipe | Ø3 rod; hole Ø3.6 in FDM still tight – ask for the real fit before changing |
| self-tapping plastic screw ~M3 | pilot Ø2.4–2.5 in the boss, clearance Ø3.4–3.5, head pocket Ø(head + 0.4) |
| magnet pocket | magnet + 0.2 per side, corner R ≤ 0.3 (sharp magnet corners), ≥ 0.8 mm floor |
| 4 mm banana / panel jack | D-hole with flats against rotation; rotate the flats 90° between the two jacks (poka-yoke) |
