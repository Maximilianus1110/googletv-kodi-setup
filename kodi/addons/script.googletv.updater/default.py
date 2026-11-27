# -*- coding: utf-8 -*-
"""Main entry point for script.googletv.updater."""

import sys
from urllib.parse import parse_qsl

from resources.lib import ui


def _parse_args(argv):
    params = {}
    for raw in argv[1:]:
        clean = raw.lstrip("?")
        if "=" in clean:
            for k, v in parse_qsl(clean.replace(",", "&")):
                params[k.strip().lower()] = v.strip()
        elif clean.strip():
            params["action"] = clean.strip().lower()
    return params


def main(argv=None):
    if argv is None:
        argv = sys.argv
    params = _parse_args(argv)
    action = params.get("action", "")
    branch = params.get("branch")

    if action in ("update", "full"):
        ui.run_update(mode="full", interactive=True, branch_override=branch)
    elif action in ("quick", "keymaps"):
        ui.run_update(mode="quick", interactive=True, branch_override=branch)
    elif action == "branch":
        ui.select_branch_dialog()
    elif action == "check":
        ui.check_for_updates_dialog()
    elif action == "backups":
        ui.show_backup_manager_dialog()
    else:
        ui.show_main_menu()


if __name__ == "__main__":
    main()
