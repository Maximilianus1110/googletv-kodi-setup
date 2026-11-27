# -*- coding: utf-8 -*-
"""Startup service for automatic GitHub branch update checks on Kodi boot."""

try:
    import xbmc
    import xbmcgui
except ImportError:
    xbmc = None
    xbmcgui = None

from resources.lib import github_api, state, ui


def run_startup_check(monitor=None):
    """Check GitHub for updates on the configured branch after startup delay."""
    if xbmc is None:
        return False

    try:
        addon = ui.get_addon()
        cfg = ui.get_config(addon)
    except Exception as exc:
        ui.log(f"Startup-Konfiguration konnte nicht geladen werden: {exc}")
        return False

    mode = cfg.get("startup_check_mode", 1)
    if mode == 0:
        ui.log("Startup-Update-Prüfung ist deaktiviert (Modus 0).")
        return False

    if monitor is None:
        monitor = xbmc.Monitor()

    delay = cfg.get("startup_delay_seconds", 15)
    if monitor.waitForAbort(delay):
        return False

    # Do not interrupt active video playback
    try:
        if xbmc.Player().isPlaying():
            ui.log("Video läuft bereits – überspringe Startup-Update-Dialog.")
            return False
    except Exception:
        pass

    paths = ui.get_kodi_paths(addon)
    cur_state = state.load_state(paths["profile_dir"])
    owner = cfg["owner"]
    repo = cfg["repo"]
    branch = cfg["branch"]
    token = cfg["token"]

    try:
        details = github_api.fetch_branch_details(owner, repo, branch, token=token)
    except Exception as exc:
        ui.log(f"Startup-Check konnte GitHub nicht erreichen: {exc}")
        return False

    # If state.json was never initialized yet, initialize baseline state to avoid false prompt on first boot
    if not cur_state.get("installed_sha"):
        state.record_installation(paths["profile_dir"], owner, repo, details, mode="baseline")
        ui.log(f"Initialer Commit-Stand für Branch '{branch}' ({details['short_sha']}) gespeichert.")
        return False

    if not state.is_update_available(cur_state, branch, details["sha"]):
        ui.log(f"Setup ist aktuell ({branch} @ {details['short_sha']}).")
        return False

    if mode == 2:
        ui.notify(
            f"Neues Update auf '{branch}' ({details['short_sha']}) gefunden – installiere automatisch...",
            heading=ui.ADDON_TITLE,
        )
        return ui.run_update(mode="full", interactive=False, branch_override=branch)

    # Mode 1: Notify & ask user
    if xbmcgui is not None:
        installed_sha = cur_state.get("installed_short_sha", "?")
        installed_branch = cur_state.get("installed_branch", branch)
        msg = (
            f"Für dein Kodi-Setup ist ein neues Update auf GitHub verfügbar!\n\n"
            f"[B]Installiert:[/B] {installed_branch} ({installed_sha})\n"
            f"[B]Verfügbar:[/B] [COLOR ff00bfa5]{branch} ({details['short_sha']})[/COLOR] vom {details['date']}\n"
            f"[B]Änderung:[/B] {details['message']}\n\n"
            "Möchtest du das Update jetzt direkt herunterladen und installieren?"
        )
        if xbmcgui.Dialog().yesno(
            f"{ui.ADDON_TITLE} – Neues Update verfügbar",
            msg,
            nolabel="Später",
            yeslabel="Jetzt aktualisieren",
        ):
            return ui.run_update(mode="full", interactive=True, branch_override=branch)

    return True


if __name__ == "__main__":
    run_startup_check()
