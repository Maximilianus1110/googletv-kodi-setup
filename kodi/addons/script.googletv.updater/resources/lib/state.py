# -*- coding: utf-8 -*-
"""Persistent installation state tracker for script.googletv.updater."""

import datetime
import json
import os

STATE_FILENAME = "state.json"


def get_state_path(profile_dir):
    return os.path.join(profile_dir, STATE_FILENAME)


def load_state(profile_dir):
    """Load state.json from the add-on profile directory."""
    path = get_state_path(profile_dir)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(profile_dir, state_data):
    """Save state_data dict to state.json in the add-on profile directory."""
    os.makedirs(profile_dir, exist_ok=True)
    path = get_state_path(profile_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2, ensure_ascii=False)
    return path


def record_installation(profile_dir, owner, repo, branch_details, mode="full"):
    """Record a completed installation in state.json."""
    sha = branch_details.get("sha", "")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "repo": f"{owner}/{repo}",
        "installed_branch": branch_details.get("name", ""),
        "installed_sha": sha,
        "installed_short_sha": sha[:7] if sha else "",
        "installed_commit_msg": branch_details.get("message", ""),
        "installed_commit_date": branch_details.get("date", ""),
        "installed_commit_author": branch_details.get("author", ""),
        "last_update_time": now_str,
        "last_update_mode": mode,
    }
    save_state(profile_dir, data)
    return data


def is_update_available(state, target_branch, remote_sha):
    """Return True if the remote branch or commit differs from the installed state."""
    if not remote_sha:
        return False
    installed_branch = state.get("installed_branch", "")
    installed_sha = state.get("installed_sha", "")
    if not installed_sha:
        return True
    if installed_branch != target_branch:
        return True
    return installed_sha != remote_sha
