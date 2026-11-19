#!/usr/bin/env python3
"""
setup_workspace.py - copy the Appraisal Comps workspace template into the
appraiser's folder.

Run once, when the appraiser first installs the appraisal-comps plugin:

    python3 -I setup_workspace.py --into <the folder he selected>

Copies every file from templates/workspace/ that is missing from the target
folder, and prints "created <path>" or "kept <path>" for each one. A file
that is already there is never overwritten, so running this again after an
update leaves his settings and data exactly as he left them.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace import plugin_root

TEMPLATE = plugin_root() / "templates" / "workspace"


def copy_missing(template: Path, target: Path) -> None:
    for template_path in sorted(template.rglob("*")):
        if template_path.is_dir():
            continue
        relative_path = template_path.relative_to(template)
        target_path = target / relative_path
        if target_path.exists():
            print(f"kept {relative_path}")
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_path, target_path)
        print(f"created {relative_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--into", required=True, help="the folder he selected for this workflow")
    args = parser.parse_args()
    target = Path(args.into)
    target.mkdir(parents=True, exist_ok=True)
    copy_missing(TEMPLATE, target)


if __name__ == "__main__":
    main()
