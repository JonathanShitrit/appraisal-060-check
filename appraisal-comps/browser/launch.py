#!/usr/bin/env python3
"""
launch.py - the browser's MCP stdio server command, started by the app from
.mcp.json. Finds the workspace, loads settings/sites.json, and execs the
pinned Playwright MCP server restricted to the sites enabled there.

stdout is the MCP channel: this script must never print to it. It writes
to stderr which source found the workspace (cwd chain,
CLAUDE_CODE_WORKSPACE_HOST_PATHS, ~/mnt, or the SessionStart hook's handoff:
on the desktop app this server is told nothing about the selected folder and
starts before the hook, so it waits for the path the hook leaves in
CLAUDE_PLUGIN_DATA). When no site is enabled it writes BROWSER_OFF to stderr and exits 1 instead of
starting a browser with no sites allowed (Design Principles, "Trust": an
origin allowed by default, or by a malformed sites.json, is an anti-goal).

    python3 -I launch.py
"""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from workspace import HANDOFF_WAIT_SECONDS, search_workspaces, wait_for_workspace_handoff  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sites import Site, load_sites  # noqa: E402

PLAYWRIGHT_MCP_VERSION = "0.0.85"

NO_SITE_ENABLED = "no site enabled in settings/sites.json"


def playwright_command(sites: list[Site], profile_dir: Path) -> list[str]:
    """The argv for the pinned Playwright MCP server, restricted to sites'
    origins. Pure: no filesystem writes, no exec."""
    origins = [site.origin for site in sites]
    return [
        "npx", "-y", f"@playwright/mcp@{PLAYWRIGHT_MCP_VERSION}",
        "--user-data-dir", str(profile_dir),
        "--allowed-origins", ";".join(origins),
    ]


def handoff_wait_seconds() -> float:
    """How long to wait for the hook's handoff. Tests shorten it with
    APPRAISAL_COMPS_HANDOFF_WAIT."""
    override = os.environ.get("APPRAISAL_COMPS_HANDOFF_WAIT", "")
    if override:
        return float(override)
    return HANDOFF_WAIT_SECONDS


def main() -> None:
    search = search_workspaces(Path.cwd())
    candidates = search.candidates
    source = search.source
    if source == "none":
        handoff_workspace = wait_for_workspace_handoff(handoff_wait_seconds())
        if handoff_workspace is None:
            print("launch.py: workspace source none: []", file=sys.stderr)
            print("BROWSER_OFF: no Appraisal Comps folder found, and the session hook "
                  "didn't report one. Start a new chat with the folder selected.", file=sys.stderr)
            sys.exit(1)
        candidates = [handoff_workspace]
        source = "handoff"
    # R20: say which source found the workspace, so the desktop check can see it.
    found_names = ", ".join(str(candidate) for candidate in candidates)
    print(f"launch.py: workspace source {source}: [{found_names}]", file=sys.stderr)
    if len(candidates) != 1:
        print(f"BROWSER_OFF: found {len(candidates)} Appraisal Comps folders, not one", file=sys.stderr)
        sys.exit(1)
    workspace = candidates[0]

    sites, problems = load_sites(workspace / "settings" / "sites.json")
    if not sites:
        detail = "; ".join(problems) if problems else NO_SITE_ENABLED
        print(f"BROWSER_OFF: {detail}", file=sys.stderr)
        sys.exit(1)

    # Fix round 1, item 5: check npx is there before creating anything. If the
    # browser isn't going to start, there's no profile folder to create either.
    npx_path = shutil.which("npx")
    if npx_path is None:
        print("BROWSER_OFF: npx not found on PATH", file=sys.stderr)
        sys.exit(1)

    # The profile stays out of CLAUDE_PLUGIN_DATA (it changes every session -
    # see the spike results) and out of the workspace (never exported or
    # synced). Created only now, because the browser is actually launching.
    profile_dir = Path.home() / "Library/Application Support/Appraisal Comps/browser-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    # This Mac's npm registry stalled the spike; pin the public one before exec.
    os.environ["npm_config_registry"] = "https://registry.npmjs.org/"

    command = playwright_command(sites, profile_dir)
    os.execvp(npx_path, [npx_path, *command[1:]])


if __name__ == "__main__":
    main()
