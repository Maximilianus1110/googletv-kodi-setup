# -*- coding: utf-8 -*-
"""Credential preservation and local ZIP backup/rollback manager."""

import datetime
import json
import os
import re
import zipfile

MANIFEST_NAME = "_backup_manifest.json"
EXCLUDED_ADDON_DATA_DIRS = {
    "crop",
    "blur",
    "simplecache",
    "cache",
    "__pycache__",
    "backups",
}


def _read_file_text(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _write_file_text(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def extract_trakt_token_from_xml(xml_text):
    """Extract the value inside <setting id="trakt_token">...</setting> (ignoring self-closing tags)."""
    if not xml_text:
        return ""
    match = re.search(r'<setting\s+id="trakt_token"[^/>]*>([^<]+)</setting>', xml_text, flags=re.DOTALL)
    if not match:
        return ""
    val = match.group(1).strip()
    if not val or "<" in val or ">" in val:
        return ""
    return val


def inject_trakt_token_into_xml(xml_text, token):
    """Inject token into <setting id="trakt_token">...</setting> in settings.xml."""
    if not xml_text or not token:
        return xml_text
    token = token.strip()
    if not token or "<" in token or ">" in token:
        return xml_text
    replacement = f'<setting id="trakt_token">{token}</setting>'
    pattern = r'<setting\s+id="trakt_token"(?:[^>]*/\s*>|[^>]*>[^<]*</setting>)'
    if re.search(pattern, xml_text, flags=re.DOTALL):
        return re.sub(pattern, lambda _: replacement, xml_text, count=1, flags=re.DOTALL)
    if "</settings>" in xml_text:
        return xml_text.replace("</settings>", f"    {replacement}\n</settings>")
    return xml_text


def extract_credentials(kodi_home):
    """Read existing OAuth tokens, logins, stream history, and updater settings from kodi_home."""
    addon_data = os.path.join(kodi_home, "userdata", "addon_data")
    tmdb_settings_path = os.path.join(addon_data, "plugin.video.themoviedb.helper", "settings.xml")
    trakt_sync_path = os.path.join(addon_data, "script.module.tmdbhelper.sync.trakt", "settings.xml")
    yt_dir = os.path.join(addon_data, "plugin.video.youtube")
    history_path = os.path.join(addon_data, "script.module.xstreamscraper", "stream_history.json")
    updater_dir = os.path.join(addon_data, "script.googletv.updater")

    tmdb_xml = _read_file_text(tmdb_settings_path)
    trakt_token = extract_trakt_token_from_xml(tmdb_xml)

    creds = {
        "trakt_token": trakt_token,
        "trakt_sync_settings": _read_file_text(trakt_sync_path),
        "youtube_access_manager": _read_file_text(os.path.join(yt_dir, "access_manager.json")),
        "youtube_api_keys": _read_file_text(os.path.join(yt_dir, "api_keys.json")),
        "youtube_settings": _read_file_text(os.path.join(yt_dir, "settings.xml")),
        "stream_history": _read_file_text(history_path),
        "updater_settings": _read_file_text(os.path.join(updater_dir, "settings.xml")),
        "updater_state": _read_file_text(os.path.join(updater_dir, "state.json")),
    }
    return creds


def restore_credentials(
    kodi_home,
    creds,
    preserve_trakt=True,
    preserve_youtube=True,
    preserve_history=True,
):
    """Restore preserved credentials into kodi_home after an update."""
    if not creds:
        return []

    restored = []
    addon_data = os.path.join(kodi_home, "userdata", "addon_data")

    if preserve_trakt:
        token = creds.get("trakt_token")
        tmdb_settings_path = os.path.join(addon_data, "plugin.video.themoviedb.helper", "settings.xml")
        if token and os.path.isfile(tmdb_settings_path):
            current_xml = _read_file_text(tmdb_settings_path)
            if current_xml:
                updated_xml = inject_trakt_token_into_xml(current_xml, token)
                _write_file_text(tmdb_settings_path, updated_xml)
                restored.append("Trakt-Token (TMDb Helper)")

        trakt_sync_xml = creds.get("trakt_sync_settings")
        if trakt_sync_xml:
            trakt_sync_path = os.path.join(addon_data, "script.module.tmdbhelper.sync.trakt", "settings.xml")
            _write_file_text(trakt_sync_path, trakt_sync_xml)
            restored.append("Trakt-Sync OAuth")

    if preserve_youtube:
        yt_dir = os.path.join(addon_data, "plugin.video.youtube")
        yt_restored = False
        if creds.get("youtube_access_manager"):
            _write_file_text(os.path.join(yt_dir, "access_manager.json"), creds["youtube_access_manager"])
            yt_restored = True
        if creds.get("youtube_api_keys"):
            _write_file_text(os.path.join(yt_dir, "api_keys.json"), creds["youtube_api_keys"])
            yt_restored = True
        if creds.get("youtube_settings"):
            _write_file_text(os.path.join(yt_dir, "settings.xml"), creds["youtube_settings"])
            yt_restored = True
        if yt_restored:
            restored.append("YouTube TV-OAuth Login")

    if preserve_history and creds.get("stream_history"):
        history_path = os.path.join(addon_data, "script.module.xstreamscraper", "stream_history.json")
        _write_file_text(history_path, creds["stream_history"])
        restored.append("xStream Stream-Historie")

    updater_dir = os.path.join(addon_data, "script.googletv.updater")
    if creds.get("updater_settings"):
        _write_file_text(os.path.join(updater_dir, "settings.xml"), creds["updater_settings"])
    if creds.get("updater_state"):
        _write_file_text(os.path.join(updater_dir, "state.json"), creds["updater_state"])

    return restored


def _should_skip_backup_path(rel_parts):
    for part in rel_parts:
        if part in EXCLUDED_ADDON_DATA_DIRS:
            return True
        if part.startswith("database_v") or part.endswith(".db-shm") or part.endswith(".db-wal"):
            return True
        if part.endswith(".pyc"):
            return True
    return False


def create_backup(kodi_home, backup_root, branch="", sha="", max_backups=3):
    """Create a compressed ZIP backup of userdata (keymaps, addon_data, advancedsettings.xml)."""
    os.makedirs(backup_root, exist_ok=True)
    now = datetime.datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S_%f")
    zip_filename = f"kodi_backup_{now.strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(backup_root, zip_filename)
    if os.path.exists(zip_path):
        zip_filename = f"kodi_backup_{stamp}.zip"
        zip_path = os.path.join(backup_root, zip_filename)

    userdata_dir = os.path.join(kodi_home, "userdata")
    files_added = 0

    manifest = {
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "branch": branch or "unbekannt",
        "sha": sha or "",
        "short_sha": sha[:7] if sha else "",
        "filename": zip_filename,
    }

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=False))

        adv_xml = os.path.join(userdata_dir, "advancedsettings.xml")
        if os.path.isfile(adv_xml):
            zf.write(adv_xml, "userdata/advancedsettings.xml")
            files_added += 1

        for subdir in ("keymaps", "addon_data"):
            target_dir = os.path.join(userdata_dir, subdir)
            if not os.path.isdir(target_dir):
                continue
            for root, dirs, files in os.walk(target_dir):
                rel_root = os.path.relpath(root, kodi_home)
                rel_parts = rel_root.split(os.sep)
                dirs[:] = [d for d in dirs if not _should_skip_backup_path(rel_parts + [d])]
                if _should_skip_backup_path(rel_parts):
                    continue
                for fname in files:
                    if _should_skip_backup_path(rel_parts + [fname]):
                        continue
                    full_path = os.path.join(root, fname)
                    if os.path.abspath(full_path) == os.path.abspath(zip_path):
                        continue
                    arcname = os.path.relpath(full_path, kodi_home).replace(os.sep, "/")
                    try:
                        zf.write(full_path, arcname)
                        files_added += 1
                    except OSError:
                        pass

    prune_backups(backup_root, max_backups=max_backups)
    return {
        "path": zip_path,
        "filename": zip_filename,
        "files_added": files_added,
        "manifest": manifest,
    }


def list_backups(backup_root):
    """Return a list of backup metadata dicts sorted newest first."""
    if not os.path.isdir(backup_root):
        return []

    backups = []
    for fname in os.listdir(backup_root):
        if not (fname.startswith("kodi_backup_") and fname.endswith(".zip")):
            continue
        fpath = os.path.join(backup_root, fname)
        if not os.path.isfile(fpath) or not zipfile.is_zipfile(fpath):
            continue

        manifest = {}
        try:
            with zipfile.ZipFile(fpath, "r") as zf:
                if MANIFEST_NAME in zf.namelist():
                    manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
        except Exception:
            manifest = {}

        size_bytes = os.path.getsize(fpath)
        mtime = os.path.getmtime(fpath)
        created_at = manifest.get("created_at") or datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

        backups.append({
            "filename": fname,
            "path": fpath,
            "created_at": created_at,
            "branch": manifest.get("branch", ""),
            "sha": manifest.get("sha", ""),
            "short_sha": manifest.get("short_sha", ""),
            "size_bytes": size_bytes,
            "size_mb": round(size_bytes / (1024 * 1024), 2),
            "mtime": mtime,
        })

    backups.sort(key=lambda b: (b["created_at"], b["mtime"], b["filename"]), reverse=True)
    return backups


def prune_backups(backup_root, max_backups=3):
    """Delete oldest backups if count exceeds max_backups."""
    if max_backups is None or int(max_backups) < 1:
        return []
    backups = list_backups(backup_root)
    removed = []
    for old in backups[int(max_backups):]:
        try:
            os.remove(old["path"])
            removed.append(old["filename"])
        except OSError:
            pass
    return removed


def restore_backup(kodi_home, backup_zip_path):
    """Restore userdata files from a backup ZIP archive into kodi_home."""
    if not os.path.isfile(backup_zip_path) or not zipfile.is_zipfile(backup_zip_path):
        raise ValueError(f"Ungültige Backup-Datei: {backup_zip_path}")

    restored_count = 0
    manifest = {}
    kodi_home_abs = os.path.abspath(kodi_home)

    with zipfile.ZipFile(backup_zip_path, "r") as zf:
        for member in zf.infolist():
            if member.filename == MANIFEST_NAME:
                try:
                    manifest = json.loads(zf.read(MANIFEST_NAME).decode("utf-8"))
                except Exception:
                    pass
                continue
            if member.is_dir():
                continue
            norm_rel = os.path.normpath(member.filename)
            if norm_rel.startswith("..") or os.path.isabs(norm_rel):
                continue
            if not norm_rel.startswith("userdata" + os.sep) and not norm_rel.startswith("userdata/"):
                continue

            dest_path = os.path.abspath(os.path.join(kodi_home_abs, norm_rel))
            if not dest_path.startswith(kodi_home_abs + os.sep):
                continue

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with zf.open(member, "r") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            restored_count += 1

    return {
        "restored_count": restored_count,
        "manifest": manifest,
    }
