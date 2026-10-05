# design-enclosure

Agent skill for designing enclosures and mechanical parts around electronics as parametric build123d models,
with a browser preview (layers, section plane, 2D section sheets), headless renders, collision / clearance checks,
STEP export and outline drawings. The agent-facing instructions are in [SKILL.md](SKILL.md).

## Contents

```
SKILL.md                     workflow + rules (loaded by the agent)
references/                  inputs, design rules, build123d traps, preview / render API (loaded on demand)
assets/template/             project skeleton copied into every new project (model, helpers, viewer)
scripts/new_project.py       scaffold a project:  python scripts/new_project.py <dir> --name "X" [--step pcb.step]
scripts/check_env.py         check Python packages, suggest live vs headless preview
scripts/package_skill.py     zip the skill for other tools
```

Requirements: Python 3.10+, `pip install build123d matplotlib numpy` (build123d brings OCP). Optional: `ocp_vscode`.

## Using it in other agent tools

The skill follows the open Agent Skills layout: a folder with `SKILL.md` (YAML front matter `name` + `description`)
plus plain files. Nothing in it depends on one vendor's tools – the agent only needs to run Python, read and write
files and look at PNGs; a browser is optional.

- **Claude Code**: clone it as a personal or project skill:

  ```bash
  git clone https://github.com/kraksp/design-enclosure.git ~/.claude/skills/design-enclosure
  git clone https://github.com/kraksp/design-enclosure.git .claude/skills/design-enclosure   # project-only
  ```

- **Other tools with Agent Skills support**: copy the folder (or unpack `python scripts/package_skill.py`) into the
  tool's skills directory – see that tool's documentation for the location.
- **Tools without skill support** (AGENTS.md / rules files only): put the folder somewhere in the repo and add to
  `AGENTS.md`:

  ```
  For enclosure / mechanical design work read tools/design-enclosure/SKILL.md first and follow it.
  ```

## Origin

Distilled from a real product enclosure: a two-shell MJF/FDM housing with side inlays, a flexure button bar,
light pipes, panel jacks, magnets, a nameplate recess and a packaging drawing.

## License

Apache 2.0 – see [LICENSE](LICENSE).
