"""Create a new enclosure project from the skill template.

    python new_project.py <target_dir> [--name "Device name"] [--step path/to/pcb.step] [--lang pl|en]

Copies assets/template (model.py, mech.py, step_load.py, checks.py, sections.py, render.py, drawing.py,
preview.py, viewer/) into <target_dir>, fills in the project name / STEP path and writes a README stub.
Never overwrites an existing model.py.
"""
import argparse
import os
import shutil
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(SKILL, "assets", "template")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--name", default=None)
    ap.add_argument("--step", default=None)
    ap.add_argument("--lang", default="en", choices=("en", "pl"))
    a = ap.parse_args()
    target = os.path.abspath(a.target)
    name = a.name or os.path.basename(target)
    if os.path.exists(os.path.join(target, "model.py")):
        sys.exit(f"{target}/model.py already exists – not overwriting. Copy single helper files by hand if needed.")
    os.makedirs(target, exist_ok=True)
    for item in os.listdir(TEMPLATE):
        src, dst = os.path.join(TEMPLATE, item), os.path.join(target, item)
        if item == "__pycache__":
            continue
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    m = os.path.join(target, "model.py")
    s = open(m, encoding="utf-8").read().replace("__PROJECT__", name)
    if a.step:
        s = s.replace("STEP_PCB = None ", f"STEP_PCB = r\"{os.path.abspath(a.step)}\" ", 1)
    s = s.replace('LANG = "en"', f'LANG = "{a.lang}"', 1)
    open(m, "w", encoding="utf-8").write(s)
    readme = os.path.join(target, "README.md")
    if not os.path.exists(readme):
        open(readme, "w", encoding="utf-8").write(
            f"# {name} – enclosure\n\nParametric build123d model. All dimensions: PARAMETERS block in `model.py`.\n\n"
            "```bash\npython model.py              # build + checks + STEP to out/ + preview\n"
            "python model.py --headless   # + PNG renders in out/render/\n"
            "python -m http.server 8765 --bind 127.0.0.1 --directory viewer   # preview at http://localhost:8765\n```\n\n"
            "## Inputs\n\n## Design decisions\n\n## Open issues\n")
    for d in ("out", os.path.join("viewer", "sections")):
        os.makedirs(os.path.join(target, d), exist_ok=True)
    print(f"project ready: {target}\n  next: cd {target} && python model.py")


if __name__ == "__main__":
    main()
