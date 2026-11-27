# -*- coding: utf-8 -*-
"""Kodi GUI dialogs, runtime JSON-RPC integration, and user workflows."""

import json
import os
import tempfile

try:
    import xbmc
    import xbmcaddon
    import xbmcgui
    import xbmcvfs
except ImportError:
    xbmc = None
    xbmcaddon = None
    xbmcgui = None
    xbmcvfs = None

from resources.lib import backup_manager, github_api, installer, state

ADDON_ID = "script.googletv.updater"
ADDON_TITLE = "Google TV – Kodi Setup Updater"


def log(msg, level=None):
    if xbmc is not None:
        lvl = level if level is not None else xbmc.LOGINFO
        xbmc.log(f"[{ADDON_ID}] {msg}", lvl)


def get_addon():
    if xbmcaddon is None:
        raise RuntimeError("Kodi xbmcaddon Modul ist außerhalb von Kodi nicht verfügbar.")
    return xbmcaddon.Addon(ADDON_ID)


def get_kodi_paths(addon=None):
    if addon is None:
        addon = get_addon()
    kodi_home = xbmcvfs.translatePath("special://home/")
    profile_dir = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
    backup_root = os.path.join(profile_dir, "backups")
    return {
        "kodi_home": kodi_home,
        "profile_dir": profile_dir,
        "backup_root": backup_root,
    }


def get_config(addon=None):
    if addon is None:
        addon = get_addon()

    def _bool(key, default=True):
        val = addon.getSetting(key)
        if not val:
            return default
        return val.lower() == "true"

    def _int(key, default=0):
        val = addon.getSetting(key)
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return default

    return {
        "owner": (addon.getSetting("github_owner") or "Maximilianus1110").strip(),
        "repo": (addon.getSetting("github_repo") or "googletv-kodi-setup").strip(),
        "branch": (addon.getSetting("active_branch") or "dev").strip(),
        "token": (addon.getSetting("github_token") or "").strip(),
        "startup_check_mode": _int("startup_check_mode", 1),
        "startup_delay_seconds": max(3, _int("startup_delay_seconds", 15)),
        "create_backup": _bool("create_backup", True),
        "max_backups": max(1, _int("max_backups", 3)),
        "preserve_trakt": _bool("preserve_trakt", True),
        "preserve_youtube": _bool("preserve_youtube", True),
        "preserve_history": _bool("preserve_history", True),
    }


def notify(message, heading=ADDON_TITLE, icon=None, time_ms=4500):
    if xbmcgui is None:
        return
    dlg = xbmcgui.Dialog()
    if icon is None:
        icon = xbmcgui.NOTIFICATION_INFO
    dlg.notification(heading, message, icon, time_ms)


def apply_kodi_runtime_post_install(addons_updated=None, mode="full"):
    """Apply live Kodi JSON-RPC settings, enable addons, and reload keymaps/skin."""
    if xbmc is None:
        return

    if mode == "full":
        for setting_id, (_, rpc_val) in installer.KODI_21_GUISETTINGS.items():
            payload = {
                "jsonrpc": "2.0",
                "method": "Settings.SetSettingValue",
                "params": {"setting": setting_id, "value": rpc_val},
                "id": 1,
            }
            try:
                xbmc.executeJSONRPC(json.dumps(payload))
            except Exception as exc:
                log(f"JSON-RPC Settings.SetSettingValue({setting_id}) fehlgeschlagen: {exc}")

        xbmc.executebuiltin("UpdateLocalAddons()")

        for addon_id in (addons_updated or []):
            payload = {
                "jsonrpc": "2.0",
                "method": "Addons.SetAddonEnabled",
                "params": {"addonid": addon_id, "enabled": True},
                "id": 1,
            }
            try:
                xbmc.executeJSONRPC(json.dumps(payload))
            except Exception as exc:
                log(f"JSON-RPC Addons.SetAddonEnabled({addon_id}) fehlgeschlagen: {exc}")

    xbmc.executebuiltin("Action(reloadkeymaps)")
    xbmc.executebuiltin("Skin.Reset(script-skinvariables-generator-hash)")
    xbmc.executebuiltin("RunScript(script.skinvariables,action=buildtemplate,force)")
    xbmc.executebuiltin("ReloadSkin()")


def run_update(mode="full", interactive=True, branch_override=None):
    """Download the configured branch from GitHub and install it (full or quick)."""
    addon = get_addon()
    cfg = get_config(addon)
    paths = get_kodi_paths(addon)
    branch = (branch_override or cfg["branch"]).strip()
    owner = cfg["owner"]
    repo = cfg["repo"]
    token = cfg["token"]

    progress = None
    if interactive and xbmcgui is not None:
        progress = xbmcgui.DialogProgress()
        mode_title = "Voll-Update" if mode == "full" else "Schnell-Update (Keymaps & Skin)"
        progress.create(
            ADDON_TITLE,
            f"Prüfe Branch '{branch}' auf GitHub ({owner}/{repo})...",
        )

    tmp_zip = None
    try:
        details = github_api.fetch_branch_details(owner, repo, branch, token=token)
        sha = details["sha"]
        short_sha = details["short_sha"]
        commit_msg = details["message"]

        if progress is not None:
            if progress.iscanceled():
                progress.close()
                notify("Update abgebrochen.")
                return False
            progress.update(
                5,
                f"Lade Branch '{branch}' ({short_sha}) herunter...\n{commit_msg[:75]}",
            )

        fd, tmp_zip = tempfile.mkstemp(prefix="kodi_setup_branch_", suffix=".zip")
        os.close(fd)

        def _dl_progress(downloaded, total):
            if progress is None:
                return True
            if progress.iscanceled():
                return False
            mb_done = downloaded / (1024 * 1024)
            if total > 0:
                mb_total = total / (1024 * 1024)
                pct = 5 + int((downloaded / total) * 50)
                progress.update(
                    min(55, pct),
                    f"Lade Branch '{branch}' ({short_sha}) herunter...\n{mb_done:.1f} MB / {mb_total:.1f} MB",
                )
            else:
                progress.update(
                    30,
                    f"Lade Branch '{branch}' ({short_sha}) herunter...\n{mb_done:.1f} MB geladen",
                )
            return True

        github_api.download_branch_zip(
            owner,
            repo,
            branch,
            tmp_zip,
            token=token,
            progress_cb=_dl_progress,
        )

        if progress is not None:
            progress.update(60, "Sichere Zugangsdaten (Trakt, YouTube, Historie) & erstelle Backup...")

        def _extract_progress(idx, total_files, rel_path):
            if progress is not None:
                pct = 60 + int((idx / max(1, total_files)) * 35)
                progress.update(
                    min(95, pct),
                    f"Installiere Dateien ({idx}/{total_files})...\n{rel_path[:70]}",
                )

        result = installer.install_from_zip(
            tmp_zip,
            paths["kodi_home"],
            mode=mode,
            backup_root=paths["backup_root"],
            branch=branch,
            sha=sha,
            do_backup=cfg["create_backup"] and mode == "full",
            max_backups=cfg["max_backups"],
            preserve_trakt=cfg["preserve_trakt"],
            preserve_youtube=cfg["preserve_youtube"],
            preserve_history=cfg["preserve_history"],
            progress_cb=_extract_progress,
        )

        state.record_installation(paths["profile_dir"], owner, repo, details, mode=mode)

        if progress is not None:
            progress.update(98, "Aktiviere Add-ons, lade Tastenbelegung & Skin neu...")

        apply_kodi_runtime_post_install(result.get("addons_updated"), mode=mode)

        if progress is not None:
            progress.update(100, "Update erfolgreich abgeschlossen!")
            progress.close()
            progress = None

        restored_list = result.get("restored_credentials") or []
        restored_str = ", ".join(restored_list) if restored_list else "Keine vorhandenen Logins gefunden"

        if interactive and xbmcgui is not None:
            if mode == "full":
                msg = (
                    f"[B]Branch:[/B] {branch} ([COLOR ff00bfa5]{short_sha}[/COLOR])\n"
                    f"[B]Commit:[/B] {commit_msg}\n"
                    f"[B]Dateien aktualisiert:[/B] {result['files_extracted']}\n"
                    f"[B]Erhaltene Daten:[/B] {restored_str}\n\n"
                    "Skin & Keymaps wurden bereits neu geladen. Möchtest du Kodi jetzt sauber beenden/neu starten, "
                    "damit auch alle Hintergrund-Services neu geladen werden?"
                )
                if xbmcgui.Dialog().yesno(
                    f"{ADDON_TITLE} – Update erfolgreich",
                    msg,
                    nolabel="Später (Weiter schauen)",
                    yeslabel="Kodi jetzt beenden",
                ):
                    xbmc.executebuiltin("Quit()")
            else:
                notify(
                    f"Schnell-Update ({branch} @ {short_sha}) geladen ({result['files_extracted']} Dateien).",
                    heading="Keymaps & Skin aktualisiert",
                )
        else:
            notify(
                f"Setup auf Branch '{branch}' ({short_sha}) aktualisiert!",
                heading=ADDON_TITLE,
            )
        return True

    except github_api.DownloadCancelledError:
        if progress is not None:
            progress.close()
        notify("Download vom Benutzer abgebrochen.")
        return False
    except Exception as exc:
        if progress is not None:
            progress.close()
        log(f"Update-Fehler: {exc}", level=xbmc.LOGERROR if xbmc else None)
        if interactive and xbmcgui is not None:
            xbmcgui.Dialog().ok(
                f"{ADDON_TITLE} – Fehler",
                f"Das Update konnte nicht durchgeführt werden:\n[COLOR ffff5252]{exc}[/COLOR]",
            )
        else:
            notify(f"Update fehlgeschlagen: {exc}", icon=xbmcgui.NOTIFICATION_ERROR if xbmcgui else None)
        return False
    finally:
        if tmp_zip and os.path.exists(tmp_zip):
            try:
                os.remove(tmp_zip)
            except OSError:
                pass


def select_branch_dialog():
    """Fetch branches from GitHub and allow the user to select or type a branch."""
    if xbmcgui is None:
        return None
    addon = get_addon()
    cfg = get_config(addon)
    paths = get_kodi_paths(addon)
    cur_state = state.load_state(paths["profile_dir"])
    active_branch = cfg["branch"]
    installed_branch = cur_state.get("installed_branch", "")
    installed_short_sha = cur_state.get("installed_short_sha", "")

    dlg = xbmcgui.Dialog()
    branches = []
    try:
        branches = github_api.fetch_branches(cfg["owner"], cfg["repo"], token=cfg["token"])
    except Exception as exc:
        log(f"Konnte Branch-Liste nicht abrufen: {exc}")

    items = []
    branch_names = []
    preselect_idx = 0

    for idx, b in enumerate(branches):
        bname = b["name"]
        bsha = b["short_sha"]
        badges = []
        if bname == active_branch:
            badges.append("[COLOR ff00bfa5]AKTIV[/COLOR]")
            preselect_idx = idx
        if bname == installed_branch:
            badges.append(f"[COLOR ff0091ea]Installiert: {installed_short_sha or bsha}[/COLOR]")
        badge_str = f"  ({' • '.join(badges)})" if badges else ""
        items.append(f"🌿 {bname}  [COLOR grey]({bsha})[/COLOR]{badge_str}")
        branch_names.append(bname)

    items.append("✏️ Eigenen Branch-Namen manuell eingeben...")

    choice = dlg.select(
        f"GitHub Branch auswählen ({cfg['owner']}/{cfg['repo']})",
        items,
        preselect=preselect_idx,
    )
    if choice < 0:
        return None

    if choice == len(branch_names):
        typed = dlg.input("Branch-Namen eingeben", defaultt=active_branch)
        if not typed or not typed.strip():
            return None
        selected_branch = typed.strip()
    else:
        selected_branch = branch_names[choice]

    try:
        details = github_api.fetch_branch_details(
            cfg["owner"],
            cfg["repo"],
            selected_branch,
            token=cfg["token"],
        )
    except Exception as exc:
        dlg.ok(
            f"{ADDON_TITLE} – Branch nicht gefunden",
            f"Der Branch '[B]{selected_branch}[/B]' konnte auf GitHub nicht geladen werden:\n[COLOR ffff5252]{exc}[/COLOR]",
        )
        return None

    addon.setSetting("active_branch", selected_branch)

    prompt_msg = (
        f"[B]Ausgewählter Branch:[/B] [COLOR ff00bfa5]{selected_branch}[/COLOR]\n"
        f"[B]Neuester Commit:[/B] {details['short_sha']} ({details['date']})\n"
        f"[B]Nachricht:[/B] {details['message']}\n\n"
        f"Möchtest du das Setup jetzt direkt auf den Branch '[B]{selected_branch}[/B]' aktualisieren?"
    )
    if dlg.yesno(
        f"{ADDON_TITLE} – Branch gewechselt",
        prompt_msg,
        nolabel="Nur Branch speichern",
        yeslabel="Jetzt installieren",
    ):
        run_update(mode="full", interactive=True, branch_override=selected_branch)

    return selected_branch


def check_for_updates_dialog():
    """Compare installed state against latest remote commit on the active branch."""
    if xbmcgui is None:
        return
    addon = get_addon()
    cfg = get_config(addon)
    paths = get_kodi_paths(addon)
    cur_state = state.load_state(paths["profile_dir"])
    dlg = xbmcgui.Dialog()

    try:
        details = github_api.fetch_branch_details(
            cfg["owner"],
            cfg["repo"],
            cfg["branch"],
            token=cfg["token"],
        )
    except Exception as exc:
        dlg.ok(
            f"{ADDON_TITLE} – Fehler bei Update-Prüfung",
            f"GitHub konnte nicht erreicht werden:\n[COLOR ffff5252]{exc}[/COLOR]",
        )
        return

    installed_branch = cur_state.get("installed_branch") or "Unbekannt"
    installed_sha = cur_state.get("installed_short_sha") or "Kein Stand gespeichert"
    installed_date = cur_state.get("last_update_time") or "-"
    has_update = state.is_update_available(cur_state, cfg["branch"], details["sha"])

    status_line = (
        "[COLOR fffbc02d][B]⚡ Neues Update / anderer Branch verfügbar![/B][/COLOR]"
        if has_update
        else "[COLOR ff00bfa5][B]✓ Dein Kodi-Setup ist auf dem neuesten Stand![/B][/COLOR]"
    )

    msg = (
        f"{status_line}\n\n"
        f"[B]Lokal installiert:[/B] Branch '{installed_branch}' • Commit {installed_sha} (Update: {installed_date})\n"
        f"[B]GitHub ({cfg['branch']}):[/B] Commit {details['short_sha']} vom {details['date']} ({details['author']})\n"
        f"[B]Commit-Info:[/B] {details['message']}"
    )

    yes_label = "Jetzt aktualisieren" if has_update else "Trotzdem neu installieren"
    if dlg.yesno(
        f"{ADDON_TITLE} – Update-Status",
        msg,
        nolabel="Schließen",
        yeslabel=yes_label,
    ):
        run_update(mode="full", interactive=True)


def show_backup_manager_dialog():
    """Interactive submenu to create, restore (rollback), or prune local backups."""
    if xbmcgui is None:
        return
    addon = get_addon()
    cfg = get_config(addon)
    paths = get_kodi_paths(addon)
    cur_state = state.load_state(paths["profile_dir"])
    dlg = xbmcgui.Dialog()

    while True:
        backups = backup_manager.list_backups(paths["backup_root"])
        options = [
            "➕ Neues lokales Backup jetzt erstellen",
            f"⏪ Backup wiederherstellen / Rollback ({len(backups)} verfügbar)",
            "🗑️ einzelnes Backup löschen",
            "⬅️ Zurück zum Hauptmenü",
        ]
        sel = dlg.select(f"{ADDON_TITLE} – Backup & Rollback Manager", options)
        if sel < 0 or sel == 3:
            return

        if sel == 0:
            try:
                info = backup_manager.create_backup(
                    paths["kodi_home"],
                    paths["backup_root"],
                    branch=cur_state.get("installed_branch") or cfg["branch"],
                    sha=cur_state.get("installed_sha", ""),
                    max_backups=cfg["max_backups"],
                )
                notify(
                    f"Backup erstellt: {info['filename']} ({info['files_added']} Dateien)",
                    heading="Backup erfolgreich",
                )
            except Exception as exc:
                dlg.ok("Backup-Fehler", f"Backup konnte nicht erstellt werden:\n{exc}")

        elif sel == 1:
            if not backups:
                dlg.ok("Keine Backups", "Es wurden noch keine lokalen Backups auf diesem Gerät angelegt.")
                continue
            b_items = [
                f"📦 {b['created_at']}  •  Branch: {b['branch'] or '-'} ({b['short_sha'] or '-'})  •  {b['size_mb']} MB"
                for b in backups
            ]
            b_idx = dlg.select("Backup zum Wiederherstellen auswählen", b_items)
            if b_idx < 0:
                continue
            chosen = backups[b_idx]
            if dlg.yesno(
                "Backup wiederherstellen (Rollback)",
                f"Möchtest du die Einstellungen & Keymaps vom [B]{chosen['created_at']}[/B] "
                f"(Branch: {chosen['branch'] or '-'}) jetzt wiederherstellen?",
                nolabel="Abbrechen",
                yeslabel="Wiederherstellen",
            ):
                try:
                    res = backup_manager.restore_backup(paths["kodi_home"], chosen["path"])
                    apply_kodi_runtime_post_install(mode="quick")
                    notify(
                        f"Backup wiederhergestellt ({res['restored_count']} Dateien).",
                        heading="Rollback erfolgreich",
                    )
                except Exception as exc:
                    dlg.ok("Rollback-Fehler", f"Wiederherstellung fehlgeschlagen:\n{exc}")

        elif sel == 2:
            if not backups:
                dlg.ok("Keine Backups", "Keine lokalen Backups zum Löschen vorhanden.")
                continue
            b_items = [
                f"🗑️ {b['created_at']}  •  {b['filename']} ({b['size_mb']} MB)"
                for b in backups
            ]
            b_idx = dlg.select("Backup zum Löschen auswählen", b_items)
            if b_idx >= 0:
                try:
                    os.remove(backups[b_idx]["path"])
                    notify(f"Backup gelöscht: {backups[b_idx]['filename']}")
                except OSError as exc:
                    dlg.ok("Fehler", f"Konnte Datei nicht löschen:\n{exc}")


def show_main_menu():
    """Display the main TV-friendly updater dialog menu."""
    if xbmcgui is None:
        return
    addon = get_addon()
    dlg = xbmcgui.Dialog()

    while True:
        cfg = get_config(addon)
        paths = get_kodi_paths(addon)
        cur_state = state.load_state(paths["profile_dir"])
        backups = backup_manager.list_backups(paths["backup_root"])

        branch = cfg["branch"]
        inst_branch = cur_state.get("installed_branch", "")
        inst_sha = cur_state.get("installed_short_sha", "")
        status_badge = (
            f"Installiert: {inst_branch}@{inst_sha}"
            if inst_branch and inst_sha
            else "Noch kein Update-Stand gespeichert"
        )

        menu_items = [
            f"🚀 Voll-Update starten  [COLOR ff00bfa5](Branch: {branch})[/COLOR]",
            f"🌿 Branch auswählen / wechseln  [COLOR grey](Aktiv: {branch})[/COLOR]",
            f"⚡ Schnell-Update: Nur Keymaps & Skin-Menüs  [COLOR grey](Branch: {branch})[/COLOR]",
            f"🔍 Auf Updates prüfen & Commit-Vergleich  [COLOR grey]({status_badge})[/COLOR]",
            f"💾 Backup & Rollback Manager  [COLOR grey]({len(backups)} Sicherungen)[/COLOR]",
            "🛠️ Wartung: Hoster-Fehlersperre (stream_failures.json) zurücksetzen",
            "⚙️ Add-on Einstellungen öffnen",
        ]

        choice = dlg.select(f"{ADDON_TITLE} ({cfg['owner']}/{cfg['repo']})", menu_items)
        if choice < 0:
            break
        elif choice == 0:
            if dlg.yesno(
                f"{ADDON_TITLE} – Voll-Update starten",
                f"Möchtest du dein Kodi-Setup jetzt vom GitHub-Branch '[B][COLOR ff00bfa5]{branch}[/COLOR][/B]' "
                f"({cfg['owner']}/{cfg['repo']}) aktualisieren?\n\n"
                "Trakt-Tokens, YouTube-Logins und Stream-Historie bleiben automatisch erhalten.",
                nolabel="Abbrechen",
                yeslabel="Update starten",
            ):
                run_update(mode="full", interactive=True)
                break
        elif choice == 1:
            select_branch_dialog()
        elif choice == 2:
            run_update(mode="quick", interactive=True)
            break
        elif choice == 3:
            check_for_updates_dialog()
        elif choice == 4:
            show_backup_manager_dialog()
        elif choice == 5:
            cleared = installer.clear_stream_failures(paths["kodi_home"])
            if cleared:
                notify("stream_failures.json gelöscht – alle Hoster sind wieder freigegeben!")
            else:
                notify("Keine Hoster-Fehlersperre aktiv (stream_failures.json nicht vorhanden).")
        elif choice == 6:
            addon.openSettings()
