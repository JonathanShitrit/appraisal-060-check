---
name: setup
description: Set up the Appraisal Comps folder on first install, or log in to a work site in the browser profile. Use the first time the plugin runs in a folder, or whenever the appraiser wants to enable a site in settings/sites.json.
---

# Setup

Goal: turn the folder the appraiser selected into a working Appraisal Comps folder, and connect any work sites he wants Claude to read.

## Steps

1. Find the folder he selected for this chat, as an absolute path your shell sees (on the chat side, that is under `~/mnt/`). Run:
   `python3 -I ${CLAUDE_PLUGIN_ROOT}/tools/setup_workspace.py --into <that folder>`
   Show him the `created`/`kept` list.
2. Run `python3 -I ${CLAUDE_PLUGIN_ROOT}/tests/run_tests.py`. It must pass. If anything fails, stop and report it; don't continue setup on a broken plugin.
3. Ask him for a contributor code (like `A-001`, not a name) and the export mode (`firm` or `external`), then run
   `python3 -I ${CLAUDE_PLUGIN_ROOT}/tools/export_learning.py init --contributor <code> --mode <firm|external>`.
4. Work sites. The browser is off until he enables a site. If he wants one now, follow the `browser-read` skill's "Before" and "Logging in" sections. Otherwise, tell him he can enable sites later the same way.

## Done when

The tests pass, `settings/export.json` exists, and he has seen the `created`/`kept` list from step 1.
