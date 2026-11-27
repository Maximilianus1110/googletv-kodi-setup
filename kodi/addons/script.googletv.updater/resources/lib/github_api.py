# -*- coding: utf-8 -*-
"""GitHub REST API, Git Smart-HTTP & Codeload ZIP client using Python's standard library.

Automatically falls back to Git Smart-HTTP (info/refs?service=git-upload-pack) and
GitHub's Atom Commit Feed (commits/<branch>.atom) when unauthenticated REST API calls
hit GitHub's 60 req/hr rate limit (HTTP 403).
"""

import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
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
        elif exc.code == 403 and ("rate limit" in body.lower() or not (token and token.strip())):
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


def _sort_branches(branches):
    def _sort_key(b):
        n = b["name"]
        if n == "main":
            return (0, n)
        if n == "master":
            return (1, n)
        return (2, n.lower())

    branches.sort(key=_sort_key)
    return branches


def _fetch_branches_via_git_refs(owner, repo, timeout=15):
    """Rate-limit-free branch discovery via Git Smart-HTTP info/refs."""
    url = (
        f"https://github.com/{urllib.parse.quote(owner)}/"
        f"{urllib.parse.quote(repo)}.git/info/refs?service=git-upload-pack"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "git/2.43.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        raise GitHubAPIError(f"Git Smart-HTTP Abfrage fehlgeschlagen: {exc}") from exc

    branches = []
    for match in re.finditer(r"([0-9a-f]{40})\s+refs/heads/([^\s\x00]+)", raw):
        sha, name = match.group(1), match.group(2).strip()
        if name:
            branches.append({
                "name": name,
                "sha": sha,
                "short_sha": sha[:7],
                "protected": name in ("main", "master"),
            })
    if not branches:
        raise GitHubAPIError("Keine Branches über Git Smart-HTTP gefunden.")
    return _sort_branches(branches)


def _fetch_branch_details_via_atom(owner, repo, branch, timeout=15):
    """Rate-limit-free commit details via GitHub Atom feed & Git Smart-HTTP."""
    encoded_branch = urllib.parse.quote(branch, safe="/")
    atom_url = (
        f"https://github.com/{urllib.parse.quote(owner)}/"
        f"{urllib.parse.quote(repo)}/commits/{encoded_branch}.atom"
    )
    req = urllib.request.Request(atom_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml_text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise GitHubAPIError(f"Branch '{branch}' auf GitHub nicht gefunden (HTTP 404).") from exc
        raise GitHubAPIError(f"Commit-Feed HTTP {exc.code}: {exc.reason}") from exc
    except Exception as exc:
        raise GitHubAPIError(f"Commit-Feed konnte nicht geladen werden: {exc}") from exc

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise GitHubAPIError(f"Keine Commits für Branch '{branch}' im Atom-Feed gefunden.")

    entry_id = entry.findtext("atom:id", default="", namespaces=ns)
    sha_match = re.search(r"Commit/([0-9a-f]{40})", entry_id)
    sha = sha_match.group(1) if sha_match else ""

    title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
    content_html = entry.findtext("atom:content", default="", namespaces=ns) or ""
    pre_match = re.search(r"<pre[^>]*>(.*?)</pre>", content_html, flags=re.DOTALL)
    if pre_match:
        full_message = html.unescape(pre_match.group(1)).strip()
    else:
        full_message = title
    first_line = full_message.splitlines()[0].strip() if full_message else title

    updated = (entry.findtext("atom:updated", default="", namespaces=ns) or "").strip()
    author_el = entry.find("atom:author", ns)
    author_name = ""
    if author_el is not None:
        author_name = (author_el.findtext("atom:name", default="", namespaces=ns) or "").strip()

    return {
        "name": branch,
        "sha": sha,
        "short_sha": sha[:7] if sha else "",
        "message": first_line,
        "full_message": full_message,
        "author": author_name,
        "date": _format_iso_date(updated),
        "raw_date": updated,
    }


def fetch_branches(owner, repo, token="", timeout=15):
    """Return all branches for owner/repo sorted with main/master first."""
    owner = owner.strip()
    repo = repo.strip()
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/branches?per_page=100"
    try:
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
        return _sort_branches(branches)
    except GitHubAPIError:
        if not (token and token.strip()):
            return _fetch_branches_via_git_refs(owner, repo, timeout=timeout)
        raise


def fetch_branch_details(owner, repo, branch, token="", timeout=15):
    """Fetch detailed commit info for a specific branch (with Atom fallback)."""
    owner = owner.strip()
    repo = repo.strip()
    branch = branch.strip()
    encoded_branch = urllib.parse.quote(branch, safe="/")
    url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/branches/{encoded_branch}"
    try:
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
    except GitHubAPIError:
        if not (token and token.strip()):
            return _fetch_branch_details_via_atom(owner, repo, branch, timeout=timeout)
        raise


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
