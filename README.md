# 🎬 Google TV & Android TV – Kodi Mediacenter Setup (Ultimate Edition)

[![Kodi](https://img.shields.io/badge/Kodi-21.2%20Omega-blue.svg)](https://kodi.tv)
[![Platform](https://img.shields.io/badge/Platform-Google%20TV%20%7C%20Android%20TV-green.svg)](https://android.com/tv)
[![Interface](https://img.shields.io/badge/Skin-Arctic%20Fuse%202-purple.svg)](https://github.com/jurialmunkey/skin.arctic.fuse.2)
[![Trakt](https://img.shields.io/badge/Sync-Trakt.tv-red.svg)](https://trakt.tv)

Ein schlüsselfertiges, im Code tiefenoptimiertes Kodi-Setup für den **Google TV Streamer**, **Chromecast mit Google TV**, **Nvidia Shield TV** oder jede andere **Android TV / Fire TV** Box.

---

## 📖 Dokumentations-Übersicht (Code-basiert & strukturiert)

Alle Funktionen sind im Ordner [`docs/`](docs/) anhand des **tatsächlichen Quellcodes** (mit exakten Dateipfaden, Funktionsnamen, Schwellenwerten und Edge-Cases) dokumentiert und für schnelles Nachschlagen mit einem **Funktions-Schnellindex** versehen:

| Dokumentation | Inhalt & abgedeckte Code-Module |
| :--- | :--- |
| 🔍 [**Abweichungen: Alte Doku vs. Code**](docs/ABWEICHUNGEN_ALT_VS_CODE.md) | **Neu:** Systematische Übersicht aller 11 Punkte, in denen die frühere Kurz-Doku vom realen Code-Verhalten abwich (inkl. Fix für den 15s-Abspann-Autoplay-Timer). |
| ⏩ [**Autoplay, Preloading, Episodenschublade & Scraper**](docs/AUTOPLAY_AND_STREAM_SELECT.md) | Staffel-Queueing (`PlayerNextEpisodes`), Hintergrund-Preloading (`pre_resolve`), UpNext & Abspann-Countdown (`autoPlayCreditsTime = 15`), `Window 1140`/`1141`, 2-stufiger Scraper (`serienstream`/`vavoo`), `PlaybackWatcher` (5× Failover) & Live-Speedtest (`select_and_play`). |
| 🌙 [**Nachtmodus, Intro-Skip & OSD-Timeline**](docs/NIGHTMODE_AND_INTROS_GUIDE.md) | TheIntroDB v4 Online-Abfrage (`_fetch_intro_segments`), `Intro skip`-Overlay (`Control 3010`), Nachtmodus (`10× volampup` + Episoden-Persistenz), `Label_OSD_Header` sowie 5s-OSD-`AlarmClock` vs. 2s-Spul-Seekbar. |
| 🎮 [**Fernbedienung, OSD-Buttons & Fenster-IDs**](docs/REMOTE_CONTROLS.md) | Komplette Referenz für `player_controls.xml`, `secret_remote.xml`, alle 10 OSD-Buttons (`6001`–`6010`), Timeline-Slider (`8200`), UpNext-/Skip-Buttons (`3010`/`3012`/`4013`) und Seitenleisten-Navigation. |
| 🎬 [**Trakt-Integration & 80-%-Scrobbling**](docs/TRAKT_SETUP.md) | `VideoInfoTag`-Metadaten-Injektion (`_listitem`), interne Scrobbler-Zeitmessung, **80-%-Gesehen-Schwelle**, `markWatchedEarly`-Prüfung, Token-Erhalt bei `./install.sh` und die 5 Trakt-Widget-Pfade. |
| 📺 [**YouTube TV-OAuth & SmartTube-Brücke**](docs/YOUTUBE_SETUP.md) | Gepatchter 1-Schritt TV-Login (`token_types = ['tv']` in `yt_login.py`), persönlicher `FEwhat_to_watch`-Feed, Verteilung der YouTube-Widgets und Direktstart von `org.smarttube.stable`. |
| 🔒 [**Erwachsenenbereich (+18 / AdultHideout)**](docs/ADULT_SETUP.md) | Long-Press-Back (`mod="longpress"`), `open_adult.py`, zweistufiges RAM-Timeout in `default.py` (**`10.0s` Hauptmenü** vs. **`300.0s` Untermenüs**), **294 aktive** von 306 Quellen und Zero-Leak-Tarnung. |
| 🚀 [**Kodi Autostart & Launcher-Manager**](docs/ANDROID_TV_AUTOSTART.md) | Android Doze-Whitelist & Hintergrund-AppOps (`apply_keep_alive`), automatische Projectivy-Accessibility-Freischaltung und `pm disable-user`-Deaktivierung des Google-TV-Launchers mit Black-Screen-Schutz. |
| 🛠️ [**Fehlerbehebung & System-Interna**](docs/TROUBLESHOOTING.md) | Cloudflare DoH-DNS-Bypass, `stream_failures.json` (60 Min. TTL), MD5-Selbstheilung (`addonTools.repair`), Android 11+ `u0_a`-Locks, `smartredraw=false` und 64 MB `filecache` in `guisettings.xml`. |

---

## ✨ Kernfunktionen & Technische Architektur im Überblick

* 🎨 **Modernes Netflix-UI (`skin.arctic.fuse.2`):**
  * Vorkonfigurierte Seitenleiste (*Entdecken*, *Filme*, *Serien*, *Live-TV*, *YouTube & SmartTube*) über `script.skinvariables`.
  * `smartredraw = false` und `algorithmdirtyregions = 3` in [`advancedsettings.xml`](kodi/userdata/advancedsettings.xml) für flüssige 60fps-Navigation ohne unsichtbare Dialoge bei pausiertem Video.
* ⚡ **Zweistufiger Multi-Source Stream-Scraper (`script.module.xstreamscraper`):**
  * **12 aktivierte deutsche xStream-Seiten + VAVOO-Mirrors** (mit automatischem Cloudflare DNS-over-HTTPS Bypass in `plugin.video.xstream`).
  * **Intelligente 2-Stufen-Suche:** Prüft bei Serien zuerst gezielt `serienstream` (gefiltert auf `(DE)`), bei Filmen zuerst die schnellen `vavoo`-Mirrors. Erst wenn dort kein ungespielter Stream läuft, werden alle übrigen Seiten parallel via `ThreadPoolExecutor` abgefragt.
  * **10s-Tiefentest & 5× Failover:** `streamTest.check()` prüft HLS-Playlists bis zum ersten echten Video-Segment (4 Ebenen tief, max. 10 Sek.). Scheitert der Kodi-Player-Start dennoch, wechselt `PlaybackWatcher` automatisch bis zu 5-mal auf den nächsten Stream.
  * **Stream-Rotation (`streamHistory.py`):** Merkt sich gespielte Streams pro Titel (`stream_history.json`) und sperrt ausgefallene Hoster für 60 Minuten (`stream_failures.json`).
* ⏩ **Nahtloses Autoplay, Hintergrund-Preloading & Abspann-Wechsel:**
  * **Staffel-Queueing:** `PlayerMonitor._queue_episodes_worker()` reiht nach 1 Sekunde alle nachfolgenden Episoden der aktuellen Staffel in `PlayList(PLAYLIST_VIDEO)` ein.
  * **Hintergrund-Preloading (`preload=true`):** Ca. 9–12 Sekunden nach Start einer Folge wird im Hintergrund bereits der Stream für Folge `N+1` aufgelöst, getestet und für 2 Stunden im RAM (`Window(10000)` Property `xstream.preload.tv.<id>.<s>.<e>`) gecacht – für **0 Sekunden Ladezeit** beim Episodenwechsel.
  * **UpNext-Countdown (15 Sek. bei Abspann oder Folgenende):** Erkennt über **TheIntroDB** den Abspannbeginn (`credits` → `notification_offset`, sofern zwischen 70 % Laufzeit und 5 Sek. vor Ende) oder blendet sich 15 Sekunden vor Videoende ein. Nach dem **15-Sekunden-Countdown** (`autoPlayCreditsTime = 15`) startet automatisch die nächste Folge.
* 📺 **In-Player Episoden-Schublade & Smarter Stream-Wechsler:**
  * **Steuerkreuz Unten (`▼`):** Öffnet direkt im Video die horizontale **Episoden-Schublade (`Window 1140`)** für die verbleibenden Folgen bzw. bei Filmen automatisch die **Besetzung (`Window 1141`)**.
  * **OSD-Button `🔄` (`Control 6009`):** Öffnet mitten im Video `select_and_play()` mit **TCP-Ping-Messung**, **Qualitäts- & Speed-Ampel** (`🟢 < 280ms`, `🟡 <= 650ms`, `🔴 > 650ms` / fehlerhaft) sowie optionalem **Top-5 Live-Speedtest** (echte HLS-Auflösungs-Erkennung `4K`/`1080p`/`720p`) und setzt das Video an exakt derselben Sekunde (`resume`) fort.
* 🌙 **Nachtmodus (`🌙`) & Manuelles Intro-Überspringen (`Intro skip`):**
  * **Nachtmodus (`Control 6010`):** Schaltet per 1-Klick `+10 dB` Dynamikkompression (`10× Action(volampup)`) ein/aus und stellt diese über `PlayerMonitor._apply_nightmode_if_active()` bei jedem Episodenwechsel automatisch wieder her.
  * **Intro Skip (`Control 3010`):** Gleiche Episoden beim Start mit `api.theintrodb.org/v4/media` ab und blendet während eines erkannten Intros (`>= 3.0s`) unten rechts den Button **`Intro skip`** ein (**kein Auto-Skip**; Sprung nur nach Druck auf **Mitte / OK**).
* ▶️ **Trakt „Weiterschauen“ & 80-%-Scrobbling:**
  * Der Scraper injiziert `tmdb_id`, `tvshow.tmdb`, `season` und `episode` in das `VideoInfoTag`.
  * Unter **80 %** Fortschritt landet das Video mit Resume-Balken unter *„▶️ Weiterschauen“*; ab **80 %** (`>= 0.8`) wird es bei Trakt als gesehen markiert und schaltet unter *„📺 Nächste Episoden“* automatisch Folge `N+1` frei.
* 📺 **YouTube (1-Schritt TV-OAuth) & SmartTube:**
  * Gepatchte [`yt_login.py`](kodi/addons/plugin.video.youtube/resources/lib/youtube_plugin/youtube/helper/yt_login.py) (`token_types = ['tv']`) für den Geräte-Login ohne Google-Sicherheitsblockade.
  * Persönliche Empfehlungen (`FEwhat_to_watch`) und Trends auf der Startseite sowie Direktstart der Android-App **SmartTube** (`org.smarttube.stable`).
* 🔒 **Diskreter +18 Bereich (`AdultHideout`):**
  * PIN **`0000`**, Schnellaufruf per **Long-Press auf die Zurück-Taste** (~1 Sekunde Haltezeit) oder über *Add-ons & Live-TV → 🔒 Archiv (+18 PIN)*.
  * Zweistufiges RAM-Timeout (**10 Sekunden** für das Hauptmenü `is_root`, **5 Minuten / 300 Sekunden** gleitend innerhalb der Untermenüs `mode=...`), **294 aktive Quellen** und Zero-Leak-Tarnung (`cacheToDisc=False`, kein Trakt-Scrobbling).

---

## 🚀 Schnellstart: 1-Klick Installation via ADB

### Voraussetzungen
1. Ein Google TV / Android TV Gerät mit aktiviertem **Entwicklermodus & USB-/Netzwerk-Debugging**.
2. **Kodi 21.2 (Omega)** auf dem Gerät installiert (aus dem Google Play Store oder per APK).
3. Ein PC (Linux, macOS oder Windows mit WSL/Git-Bash) mit installiertem `adb`.

### Installation in 3 Schritten:

```bash
# 1. Repository klonen
git clone git@github.com:Maximilianus1110/googletv-kodi-setup.git
cd googletv-kodi-setup

# 2. Gerät anschließen (USB) oder per WLAN verbinden
adb connect <IP-DEINES-FERNSEHERS>:5555

# 3. Installations-Skript ausführen
./install.sh
```

Was [`install.sh`](install.sh) dabei automatisch ausführt:
1. Stoppt Kodi sauber (`am force-stop org.xbmc.kodi`).
2. Erstellt ein lokales Backup deiner bisherigen Keymaps und `addon_data` auf dem Fernseher (`/sdcard/kodi_backup_YYYYMMDD_HHMMSS`).
3. Liest bestehende **Trakt-OAuth-Tokens** vom Gerät aus und stellt sie nach dem Update wieder her.
4. Überträgt alle Add-ons, Skin-Anpassungen und Keymaps (beschleunigt per `tar`-Bundle über WLAN/USB).
5. Patcht Kodis `guisettings.xml` (**64 MB RAM-Stream-Cache**, **24p-Refresh-Sync** und **Auto-Update-Schutz** `general.addonupdates = 1`).
6. Aktiviert das **Standby Keep-Alive** (Doze-Whitelist & Hintergrund-AppOps) und startet Kodi neu.

---

## 📦 Enthaltene Add-ons & Code-Patches

| Add-on / Modul | ID | Version & Spezifische Code-Anpassungen in diesem Setup |
| :--- | :--- | :--- |
| **Arctic Fuse 2** | `skin.arctic.fuse.2` | Gepatcht: OSD-Buttons `6009` (`change_stream.py`) & `6010` (`toggle_nightmode.py`), 5s `AlarmClock(osd_timeout)`, `open_adult.py` PIN-Launcher, `Label_OSD_Header` & Vorkonfigurierte Shortcut-Menüs |
| **TheMovieDb Helper** | `plugin.video.themoviedb.helper` | 6.21.2 – Gepatcht in `monitor/player.py`: `_queue_episodes_worker()` (Staffel-Queueing + Preload-Trigger), `_fetch_intro_segments()` (TheIntroDB v4 Intro & Abspann-Offset), `_apply_nightmode_if_active()` (+10 dB Persistenz) & `scrobbler_update()`-Schutz bei Abspann-Autoplay |
| **xStream Scraper** | `script.module.xstreamscraper` | 2026.11.02.7 – Gepatcht in `scraper.py`, `streamTest.py`, `streamHistory.py`: 2-Stufen-Suche (`serienstream`/`vavoo`), `pre_resolve()` RAM-Cache, `select_and_play()` mit TCP-Ping-Ampel, Top-5 Live-Speedtest & Resume, 10s HLS-Segment-Prüfung, `PlaybackWatcher` (5× Failover) & `VideoInfoTag`-Injektion |
| **xStream** | `plugin.video.xstream` | 2026.10.06~nightly – Gepatcht in `requestHandler.py`: `quietWindows()` Context-Manager (unterdrückt Dialoge bei Autoplay/Preload) & Cloudflare DoH-DNS-Bypass (`__doh_request`) |
| **Up Next (Autoplay)** | `service.upnext` | 1.3.4 – Gepatcht in `api.py`, `skip.py` & `settings.xml`: Manuelles `Intro skip`-Overlay (`autoSkipIntro = false`) sowie **15-Sekunden-Countdown mit aktivem `player.playnext()` bei erkanntem Abspannbeginn** (`autoPlayCreditsTime = 15`) |
| **YouTube** | `plugin.video.youtube` | 7.4.4 – Gepatcht in `yt_login.py`: `token_types = ['tv']` (1-Schritt TV-Client OAuth ohne Google-Sicherheitsblockade) |
| **AdultHideout** | `plugin.video.adulthideout` | 1.0.27 – Gepatcht in `default.py`: PIN-Guard (`0000`) mit zweistufigem RAM-Timeout (`10.0s` Hauptmenü / `300.0s` Untermenüs), DNS-Retry & 294 aktiven Quellen |
| **AdultHideout Core** | `service.adulthideout.core` | 1.0.1 – Gepatcht in `service.py`: Leichtgewichtiger Python-Fallback-Standby-Service für Android TV |
| **VAVOO.TO** | `plugin.video.vavooto` | 2026.11.02.5 – Deutsche Live-TV-Gruppen & VOD-Mirror-Resolver (`vjackson`) |
| **ResolveURL** | `script.module.resolveurl` | Aktuelle Hoster-Resolver (VOE, Filemoon, Streamwish, Vidmoly, DoodStream etc.) |
| **Trakt Sync** | `script.module.tmdbhelper.sync.trakt` | 1.2.9 – Cloud-Scrobbling, Watchlist & *„Weil du geschaut hast“*-Empfehlungen |

---

## 🛠️ Wartungs-Befehle

```bash
# Nur die Tastenbelegung (player_controls.xml & secret_remote.xml) neu übertragen
./install.sh --keymaps-only

# Kodi Autostart / Standby Keep-Alive / Google-TV-Launcher-Manager starten
./autostart-kodi.sh

# Ein lokales Backup des aktuellen Kodi-Stands vom TV auf den PC ziehen (./backups/)
./backup.sh

# Kodi über ADB sauber neu starten
adb shell "am force-stop org.xbmc.kodi; am start -n org.xbmc.kodi/.Main"
```

---

## ⚖️ Lizenz & Haftungsausschluss

Dieses Repository dient rein privaten Archivierungs- und Dokumentationszwecken. Sämtliche Add-ons sind Open-Source-Projekte dritter Entwickler. Es werden keine urheberrechtlich geschützten Medieninhalte gehostet.
