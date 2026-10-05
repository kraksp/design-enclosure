"""Check the Python environment for design-enclosure and suggest the preview mode.

    python check_env.py

Prints versions of the required / optional packages, whether a GUI session is likely, and the install command
for anything that is missing. Exit code 1 when a required package is missing.
"""
import importlib
import os
import platform
import shutil
import sys

REQUIRED = {"build123d": "build123d", "OCP": "cadquery-ocp", "numpy": "numpy", "matplotlib": "matplotlib"}
OPTIONAL = {"ocp_vscode": "ocp_vscode (live view in VS Code)", "playwright": "playwright (scripted browser screenshots)"}


def version(mod):
    try:
        m = importlib.import_module(mod)
        return getattr(m, "__version__", "ok")
    except Exception:
        return None


def main():
    print(f"python {sys.version.split()[0]} on {platform.system()} {platform.release()}")
    missing = []
    for mod, pkg in REQUIRED.items():
        v = version(mod)
        print(f"  {'OK ' if v else 'MISSING'} {mod:12} {v or ''}")
        if not v:
            missing.append(pkg)
    for mod, desc in OPTIONAL.items():
        v = version(mod)
        print(f"  {'opt' if v else ' - '} {mod:12} {v or ''}  {desc}")
    gui = platform.system() in ("Windows", "Darwin") or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    ci = any(os.environ.get(k) for k in ("CI", "GITHUB_ACTIONS", "HEADLESS"))
    print(f"GUI session likely: {gui and not ci}   CI/headless env: {ci}   browser on PATH: "
          f"{any(shutil.which(b) for b in ('chrome', 'chromium', 'msedge', 'firefox', 'google-chrome'))}")
    print("suggested preview: " + ("live viewer (python -m http.server ... --directory viewer) + renders for yourself"
                                   if gui and not ci else "headless renders: python model.py --headless"))
    if missing:
        print("install: pip install " + " ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main()
