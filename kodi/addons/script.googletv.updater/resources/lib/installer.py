# -*- coding: utf-8 -*-
"""ZIP extractor and Kodi setup installer for full and quick updates."""

import glob
import os
import re
import shutil
import zipfile

from resources.lib import backup_manager

LEGACY_PATHS_TO_REMOVE = (
    "addons/plugin.video.adulthideout",
    "addons/service.adulthideout.core",
    "userdata/keymaps/secret_remote.xml",
    "addons/skin.arctic.fuse.2/shortcuts/open_adult.py",
)

KODI_21_GUISETTINGS = {
    "general.addonupdates": ("1", 1),
    "filecache.buffermode": ("4", 4),
    "filecache.memorysize": ("64", 64),
    "filecache.readfactor": ("400", 400),
    "videoplayer.adjustrefreshrate": ("2", 2),
}

QUICK_UPDATE_PREFIXES = (
    "userdata/keymaps/",
    "userdata/advancedsettings.xml",
    "addons/skin.arctic.fuse.2/shortcuts/",
    "addons/skin.arctic.fuse.2/1080i/",
    "userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/",
)


class InstallError(Exception):
    """Raised when extracting or installing the setup archive fails."""


def _find_kodi_prefix(zf):
    """Locate the prefix leading to addons/ and userdata/ inside the GitHub branch ZIP."""
    names = zf.namelist()
    for name in names:
        if "/kodi/addons/" in name or "/kodi/userdata/" in name:
            idx = name.index("/kodi/")
            return name[: idx + len("/kodi/")]
        if name.startswith("kodi/addons/") or name.startswith("kodi/userdata/"):
            return "kodi/"
    for name in names:
        if "/addons/" in name or "/userdata/" in name:
            for marker in ("/addons/", "/userdata/"):
                if marker in name:
                    idx = name.index(marker)
                    return name[: idx + 1]
    raise InstallError(
        "Das heruntergeladene Branch-Archiv enthält keinen 'kodi/addons' oder 'kodi/userdata' Ordner."
    )


def _should_skip_zip_member(rel_path):
    """Return True for files excluded during installation (matching install.sh)."""
    parts = rel_path.split("/")
    for part in parts:
        if part in ("__pycache__", ".DS_Store"):
            return True
        if part.endswith(".pyc"):
            return True
        if part.startswith("script-skinvariables-generator-includes--kodiprofile-") and part.endswith(".xml"):
            return True
    return False


def _matches_quick_mode(rel_path):
    for prefix in QUICK_UPDATE_PREFIXES:
        if rel_path == prefix or rel_path.startswith(prefix):
            return True
    return False


def remove_legacy_components(kodi_home):
    """Remove archived legacy components from the target Kodi installation."""
    removed = []
    for rel in LEGACY_PATHS_TO_REMOVE:
        target = os.path.join(kodi_home, *rel.split("/"))
        if os.path.isdir(target):
            shutil.rmtree(target, ignore_errors=True)
            removed.append(rel)
        elif os.path.isfile(target):
            try:
                os.remove(target)
                removed.append(rel)
            except OSError:
                pass
    skin_cache_pattern = os.path.join(
        kodi_home,
        "addons",
        "skin.arctic.fuse.2",
        "1080i",
        "script-skinvariables-generator-includes--kodiprofile-*.xml",
    )
    for cached_xml in glob.glob(skin_cache_pattern):
        try:
            os.remove(cached_xml)
            removed.append(os.path.relpath(cached_xml, kodi_home))
        except OSError:
            pass
    return removed


def apply_kodi21_guisettings_xml(guisettings_path):
    """Patch guisettings.xml on disk with Kodi 21 stream cache, 24p sync & update protection."""
    if not os.path.isfile(guisettings_path):
        return False
    try:
        with open(guisettings_path, "r", encoding="utf-8") as f:
            txt = f.read()
        for key, (str_val, _) in KODI_21_GUISETTINGS.items():
            pat = rf'<setting\s+id="{re.escape(key)}"(?:[^>]*/\s*>|[^>]*>[^<]*</setting>)'
            repl = f'<setting id="{key}">{str_val}</setting>'
            if re.search(pat, txt, flags=re.DOTALL):
                txt = re.sub(pat, lambda _: repl, txt, flags=re.DOTALL)
            elif "</settings>" in txt:
                txt = txt.replace("</settings>", f"    {repl}\n</settings>")
        with open(guisettings_path, "w", encoding="utf-8") as f:
            f.write(txt)
        return True
    except Exception:
        return False


def clear_stream_failures(kodi_home):
    """Delete stream_failures.json so temporarily blocked hosters are reset immediately."""
    failures_path = os.path.join(
        kodi_home,
        "userdata",
        "addon_data",
        "script.module.xstreamscraper",
        "stream_failures.json",
    )
    if os.path.isfile(failures_path):
        os.remove(failures_path)
        return True
    return False


def install_from_zip(
    zip_path,
    kodi_home,
    mode="full",
    backup_root=None,
    branch="",
    sha="",
    do_backup=True,
    max_backups=3,
    preserve_trakt=True,
    preserve_youtube=True,
    preserve_history=True,
    progress_cb=None,
):
    """Extract and apply a GitHub branch ZIP archive into kodi_home.

    mode: "full" (all addons & userdata) or "quick" (only keymaps & skin shortcuts/XMLs).
    """
    if not os.path.isfile(zip_path) or not zipfile.is_zipfile(zip_path):
        raise InstallError(f"Ungültiges ZIP-Archiv: {zip_path}")

    kodi_home_abs = os.path.abspath(kodi_home)
    os.makedirs(kodi_home_abs, exist_ok=True)

    creds = backup_manager.extract_credentials(kodi_home_abs)
    backup_info = None
    if mode == "full" and do_backup and backup_root:
        backup_info = backup_manager.create_backup(
            kodi_home_abs,
            backup_root,
            branch=branch,
            sha=sha,
            max_backups=max_backups,
        )

    addons_updated = set()
    files_extracted = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        kodi_prefix = _find_kodi_prefix(zf)
        members_to_extract = []

        for member in zf.infolist():
            if member.is_dir():
                continue
            if not member.filename.startswith(kodi_prefix):
                continue
            rel_path = member.filename[len(kodi_prefix):].lstrip("/")
            if not rel_path:
                continue
            if not (rel_path.startswith("addons/") or rel_path.startswith("userdata/")):
                continue
            if _should_skip_zip_member(rel_path):
                continue
            if mode == "quick" and not _matches_quick_mode(rel_path):
                continue
            members_to_extract.append((member, rel_path))

        if not members_to_extract:
            raise InstallError("Keine passenden Setup-Dateien im ZIP-Archiv gefunden.")

        total_files = len(members_to_extract)
        for idx, (member, rel_path) in enumerate(members_to_extract, start=1):
            norm_rel = os.path.normpath(rel_path)
            if norm_rel.startswith("..") or os.path.isabs(norm_rel):
                continue
            dest_path = os.path.abspath(os.path.join(kodi_home_abs, norm_rel))
            if not dest_path.startswith(kodi_home_abs + os.sep):
                continue

            parts = rel_path.split("/")
            if len(parts) >= 2 and parts[0] == "addons":
                addons_updated.add(parts[1])

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with zf.open(member, "r") as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            files_extracted += 1

            if progress_cb is not None and (idx == 1 or idx == total_files or idx % 20 == 0):
                progress_cb(idx, total_files, rel_path)

    removed_legacy = remove_legacy_components(kodi_home_abs)
    restored_creds = backup_manager.restore_credentials(
        kodi_home_abs,
        creds,
        preserve_trakt=preserve_trakt,
        preserve_youtube=preserve_youtube,
        preserve_history=preserve_history,
    )

    if mode == "full":
        guisettings_path = os.path.join(kodi_home_abs, "userdata", "guisettings.xml")
        apply_kodi21_guisettings_xml(guisettings_path)

    return {
        "mode": mode,
        "files_extracted": files_extracted,
        "addons_updated": sorted(addons_updated),
        "restored_credentials": restored_creds,
        "removed_legacy": removed_legacy,
        "backup_info": backup_info,
    }
