# -*- coding: utf-8 -*-
"""GitHub REST API & Codeload ZIP client using Python's standard library."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import zipfile

USER_AGENT = "GoogleTV-Kodi-Setup-Updater/1.0 (Kodi 21 Omega)"
CHUNK_SIZE = 65536


class GitHubAPIError(Exception):
    """Raised when a GitHub API request or download fails."""


class DownloadCancelledError(Exception):
    """Raised when the user cancels an active ZIP download."""


def _build_headers(token="", accept="application/vnd.github+json"):
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": accept,
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _request_json(url, token="", timeout=15):
    req = urllib.request.Request(url, headers=_build_headers(token=token))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        msg = f"GitHub API HTTP {exc.code} ({exc.reason})"
        if exc.code == 404:
            msg = "Repository oder Branch auf GitHub nicht gefunden (HTTP 404)."
        elif exc.code == 403 and "rate limit" in body.lower():
            msg = "GitHub API Rate-Limit erreicht (HTTP 403). Optional Token in den Einstellungen hinterlegen."
        elif exc.code == 401:
            msg = "GitHub Authentifizierung fehlgeschlagen (HTTP 401 – Token prüfen)."
        raise GitHubAPIError(msg) from exc
    except urllib.error.URLError as exc:
        raise GitHubAPIError(f"Netzwerkfehler bei Verbindung zu GitHub: {exc.reason}") from exc
    except Exception as exc:
        raise GitHubAPIError(f"Fehler bei GitHub-Abfrage: {exc}") from exc


def _format_iso_date(iso_str):
    if not iso_str:
        return ""
    clean = iso_str.replace("T", " ").replace("Z", "")
    return clean[:16]


def fetch_branches(owner, repo, token="", timeout=15):
    """Return all branches for owner/repo sorted with main/master first."""
    owner = owner.strip()
    repo = repo.strip()
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/branches?per_page=100"
    data = _request_json(url, token=token, timeout=timeout)
    if not isinstance(data, list):
        raise GitHubAPIError("Unerwartete Antwort beim Abrufen der Branch-Liste.")

    branches = []
    for item in data:
        name = item.get("name", "")
        commit = item.get("commit") or {}
        sha = commit.get("sha", "")
        if name:
            branches.append({
                "name": name,
                "sha": sha,
                "short_sha": sha[:7] if sha else "",
                "protected": bool(item.get("protected", False)),
            })

    def _sort_key(b):
        n = b["name"]
        if n == "main":
            return (0, n)
        if n == "master":
            return (1, n)
        return (2, n.lower())

    branches.sort(key=_sort_key)
    return branches


def fetch_branch_details(owner, repo, branch, token="", timeout=15):
    """Fetch detailed commit info for a specific branch."""
    owner = owner.strip()
    repo = repo.strip()
    branch = branch.strip()
    encoded_branch = urllib.parse.quote(branch, safe="")
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/branches/{encoded_branch}"
    data = _request_json(url, token=token, timeout=timeout)

    commit_obj = data.get("commit") or {}
    sha = commit_obj.get("sha", "")
    inner_commit = commit_obj.get("commit") or {}
    full_message = (inner_commit.get("message") or "").strip()
    first_line = full_message.splitlines()[0].strip() if full_message else ""
    author_info = inner_commit.get("author") or {}
    committer_info = inner_commit.get("committer") or {}
    author_name = author_info.get("name") or (commit_obj.get("author") or {}).get("login") or ""
    raw_date = author_info.get("date") or committer_info.get("date") or ""

    return {
        "name": data.get("name", branch),
        "sha": sha,
        "short_sha": sha[:7] if sha else "",
        "message": first_line,
        "full_message": full_message,
        "author": author_name,
        "date": _format_iso_date(raw_date),
        "raw_date": raw_date,
    }


def download_branch_zip(owner, repo, branch, dest_path, token="", progress_cb=None, timeout=60):
    """Download the ZIP archive for a branch to dest_path with progress callback.

    progress_cb(downloaded_bytes, total_bytes) -> bool (return False to cancel)
    """
    owner = owner.strip()
    repo = repo.strip()
    branch = branch.strip()
    encoded_branch = urllib.parse.quote(branch, safe="/")

    urls = []
    if not (token and token.strip()):
        urls.append(
            f"https://codeload.github.com/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/zip/refs/heads/{encoded_branch}"
        )
    urls.append(
        f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/zipball/{encoded_branch}"
    )

    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    last_error = None

    for url in urls:
        req = urllib.request.Request(url, headers=_build_headers(token=token, accept="*/*"))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                total_header = resp.headers.get("Content-Length")
                total_bytes = int(total_header) if total_header and total_header.isdigit() else 0
                downloaded = 0

                with open(dest_path, "wb") as out_file:
                    while True:
                        chunk = resp.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb is not None:
                            keep_going = progress_cb(downloaded, total_bytes)
                            if keep_going is False:
                                raise DownloadCancelledError("Download vom Benutzer abgebrochen.")

            if not zipfile.is_zipfile(dest_path):
                raise GitHubAPIError("Heruntergeladene Datei ist kein gültiges ZIP-Archiv.")
            return dest_path

        except DownloadCancelledError:
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except OSError:
                    pass
            raise
        except Exception as exc:
            last_error = exc
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except OSError:
                    pass

    raise GitHubAPIError(f"Branch-Archiv konnte nicht heruntergeladen werden: {last_error}")
