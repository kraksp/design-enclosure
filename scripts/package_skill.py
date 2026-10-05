"""Zip the skill for another agent tool (or for upload where skills are installed from a .zip).

    python package_skill.py [out_dir]      ->  <out_dir>/design-enclosure.zip   (default: current directory)

The archive contains the folder design-enclosure/ with SKILL.md at its root, without caches.
"""
import os
import sys
import zipfile

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = os.path.basename(SKILL)
SKIP_DIRS = {"__pycache__", ".git", "out"}
SKIP_EXT = {".pyc", ".glb"}


def main():
    out_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{NAME}.zip")
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(SKILL):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if os.path.splitext(f)[1] in SKIP_EXT:
                    continue
                p = os.path.join(root, f)
                z.write(p, os.path.join(NAME, os.path.relpath(p, SKILL)))
                n += 1
    print(f"{out}  ({n} files)")


if __name__ == "__main__":
    main()
