# -*- coding: utf-8 -*-
# Prueft, ob hinter einem aufgeloesten Link wirklich Videodaten liegen, und begrenzt die Zeit pro Stream.
import re, socket, threading, time, requests
from urllib.parse import parse_qsl, urljoin, urlparse

LIMIT = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
_PLAYLIST_MAX = 512 * 1024
_session = requests.session()

class Cancelled(BaseException):
	"""Der Nutzer hat abgebrochen. BaseException, damit es die except-Exception-Bloecke der Suche passiert."""

class StreamTimeout(Exception):
	pass

def runLimited(func, limit=LIMIT, cancelled=None):
	"""Fuehrt func hoechstens limit Sekunden aus. Ein haengender Aufruf laeuft als Daemon-Thread aus,
	sein Ergebnis wird verworfen; ein ThreadPoolExecutor wuerde hier auf ihn warten."""
	box = {}
	def worker():
		try: box["result"] = func()
		except Exception as e: box["error"] = e
	thread = threading.Thread(target=worker, daemon=True)
	thread.start()
	end = time.monotonic() + limit
	while thread.is_alive():
		if cancelled and cancelled(): raise Cancelled()
		remaining = end - time.monotonic()
		if remaining <= 0: raise StreamTimeout("mehr als %s Sekunden" % limit)
		thread.join(min(0.1, remaining))
	if "error" in box: raise box["error"]
	return box.get("result")

def _splitUrl(url):
	target, _, rawHeaders = url.partition("|")
	headers = dict(parse_qsl(rawHeaders))
	if not any(name.lower() == "user-agent" for name in headers):
		headers["User-Agent"] = USER_AGENT
	return target, headers

def _fetch(url, headers, deadline):
	"""Liefert finale URL, Content-Type und den Anfang der Antwort (bei Playlisten die ganze Datei)."""
	remaining = deadline - time.monotonic()
	if remaining <= 0: raise StreamTimeout("Zeitlimit erreicht")
	res = _session.get(url, headers=headers, stream=True, timeout=(remaining, remaining))
	try:
		if not res.ok: raise Exception("HTTP %s" % res.status_code)
		data = b""
		for chunk in res.iter_content(4096):
			data += chunk
			if not _isPlaylist(data) or len(data) >= _PLAYLIST_MAX: break
			if time.monotonic() > deadline: raise StreamTimeout("Zeitlimit erreicht")
		return res.url, res.headers.get("Content-Type", "").lower(), data
	finally:
		res.close()

def _isPlaylist(data):
	return data.lstrip(b"\xef\xbb\xbf \r\n\t").startswith(b"#EXTM3U")

def _firstEntry(playlist):
	for line in playlist.decode("utf-8", "ignore").splitlines():
		line = line.strip()
		if line and not line.startswith("#"): return line

def _looksLikeHtml(data):
	head = data.lstrip(b"\xef\xbb\xbf \r\n\t")[:15].lower()
	return head.startswith((b"<!doctype", b"<html", b"<head", b"<body", b"<?xml"))

def check(url, deadline=None):
	"""Wirft eine Exception, wenn der Stream keine Videodaten liefert. Bei HLS wird bis zum ersten
	Segment durchgegangen, denn tote Streams haben oft noch eine gueltige Playlist."""
	if deadline is None: deadline = time.monotonic() + LIMIT
	target, headers = _splitUrl(url)
	for depth in range(4):
		final, contentType, data = _fetch(target, headers, deadline)
		if _isPlaylist(data):
			entry = _firstEntry(data)
			if not entry: raise Exception("Leere Playlist")
			target = urljoin(final, entry)
			continue
		if not data: raise Exception("Keine Daten")
		if _looksLikeHtml(data): raise Exception("Webseite statt Video")
		# HLS-Segmente werden oft als Text oder Bild getarnt, darum gilt der Content-Type nur fuer Direktlinks.
		if depth == 0 and "text" in contentType: raise Exception("Keine Videodatei")
		return
	raise Exception("Playlist zu tief verschachtelt")

def detect_resolution(data=b"", url="", hint=""):
	"""Ermittelt die Videoaufloesung aus einer HLS-Master-Playlist, URL oder Hoster-Hinweisen."""
	if data and _isPlaylist(data):
		text = data.decode("utf-8", "ignore")
		heights = [int(m) for m in re.findall(r"RESOLUTION=\s*\d+x(\d+)", text, re.I)]
		heights += [int(m) for m in re.findall(r'NAME=["\'](\d{3,4})p', text, re.I)]
		if heights:
			best = max(heights)
			if best >= 2160: return "4K"
			if best >= 1080: return "1080p"
			if best >= 720: return "720p"
			if best >= 480: return "480p"
			return f"{best}p"
	meta_text = f"{hint} {url}".lower()
	if re.search(r"(?:^|[^a-z0-9])(2160p|4k|uhd)(?:[^a-z0-9]|$)", meta_text): return "4K"
	if re.search(r"(?:^|[^a-z0-9])(1080p|fhd|fullhd)(?:[^a-z0-9]|$)", meta_text): return "1080p"
	if re.search(r"(?:^|[^a-z0-9])(720p)(?:[^a-z0-9]|$)", meta_text): return "720p"
	if re.search(r"(?:^|[^a-z0-9])(480p|360p|sd)(?:[^a-z0-9]|$)", meta_text): return "480p"
	if re.search(r"(?:^|[^a-z0-9])hd(?:[^a-z0-9]|$)", meta_text): return "HD"
	return ""

def ping_host(url_or_host, timeout=1.2):
	"""Misst die TCP-Verbindungszeit (Latenz) in ms fuer eine URL oder Domain."""
	if not url_or_host: return None
	target = str(url_or_host).partition("|")[0].strip()
	if not target: return None
	if "://" not in target:
		target = "https://" + target
	parsed = urlparse(target)
	host = parsed.hostname
	if not host or "." not in host: return None
	port = parsed.port or (80 if parsed.scheme == "http" else 443)
	t0 = time.monotonic()
	sock = None
	try:
		sock = socket.create_connection((host, port), timeout=timeout)
		return max(1, int((time.monotonic() - t0) * 1000))
	except Exception:
		return None
	finally:
		if sock:
			try: sock.close()
			except Exception: pass

def probe(url, deadline=None, hint=""):
	"""Wie check(), misst aber zusaetzlich die reale Antwortzeit in ms und liest die Stream-Aufloesung aus."""
	if deadline is None: deadline = time.monotonic() + LIMIT
	t0 = time.monotonic()
	target, headers = _splitUrl(url)
	master_data = b""
	final_url = target
	for depth in range(4):
		final, contentType, data = _fetch(target, headers, deadline)
		final_url = final
		if _isPlaylist(data):
			if not master_data or b"RESOLUTION=" in data.upper():
				master_data = data
			entry = _firstEntry(data)
			if not entry: raise Exception("Leere Playlist")
			target = urljoin(final, entry)
			continue
		if not data: raise Exception("Keine Daten")
		if _looksLikeHtml(data): raise Exception("Webseite statt Video")
		if depth == 0 and "text" in contentType: raise Exception("Keine Videodatei")
		ms = max(1, int((time.monotonic() - t0) * 1000))
		res = detect_resolution(master_data, final_url, hint) or "HD"
		return res, ms
	raise Exception("Playlist zu tief verschachtelt")
