# ⏩ Autoplay, Staffelwechsel, Preloading, Episoden-Schublade & Stream-Scraper

> [!NOTE]
> Eine Übersicht aller behobenen Abweichungen zwischen früherer Doku und aktuellem Code findest du in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md).

---

## 🧭 Funktions-Schnellindex

| Funktion | Auslöser | Kern-Dateien & Funktionen | Verhalten im Überblick |
| :--- | :--- | :--- | :--- |
| **[1. Staffel- & Staffelwechsel-Queueing](#1-automatisches-staffel--staffelwechsel-queueing-playlist-aufbau)** | Automatisch (`1s` nach Episodenstart) | `tmdbhelper/.../monitor/player.py` → `_queue_episodes_worker()`<br>`tmdbhelper/.../player/action/episodes.py` → `PlayerNextEpisodes.all_episodes` | Reiht alle nachfolgenden Episoden der aktuellen Staffel in `PlayList(PLAYLIST_VIDEO)` ein. Am Staffelende (`<= 1` Restfolge) wird automatisch **`Staffel S+1`** geladen und angehängt. |
| **[2. Hintergrund-Preloading (inkl. Staffelwechsel)](#2-hintergrund-vorabladen-preloading-fr-folge-n1-bzw-s1-e01)** | Automatisch (~`9–12s` nach Episodenstart) | `tmdbhelper/.../monitor/player.py` → `_queue_episodes_worker()`<br>`xstreamscraper/.../scraper.py` → `pre_resolve()` | Ermittelt aus `pne.next_episodes[0]` die exakte nächste Folge (regulär `S, E+1` oder beim Staffelfinale **`S+1, E01`**), löst den Stream lautlos im Hintergrund auf und cacht ihn für 2 Std. im RAM (`Window(10000)`). |
| **[3. UpNext-Countdown & Auto-Advance](#3-upnext-popup--automatischer-folgenwechsel-abspann--episodenende--staffelwechsel)** | Automatisch bei Abspannbeginn (`notification_offset`) oder `15s` vor Videoende | `tmdbhelper/.../monitor/player.py` → `_fetch_intro_segments()`<br>`service.upnext/.../api.py` → `credits_autoplay_deadline()`<br>`service.upnext/.../playbackmanager.py` → `show_popup_and_wait()` | Synchronisiert über `playlist_ready` mit dem Playlist-Aufbau, blendet das UpNext-Popup mit **15-Sekunden-Countdown** ein und ruft nach Ablauf aktiv **`self.player.playnext()`** auf (auch über Staffelgrenzen und bei `includeWatched = true`). |
| **[4. In-Player Episoden-Schublade](#4-in-player-episoden-schublade-window-1140--cast-fallback-window-1141)** | **Steuerkreuz Unten (`▼`)** im Vollbild-Video | `keymaps/player_controls.xml`<br>`skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml`<br>`skin.arctic.fuse.2/1080i/Includes_Paths.xml` → `Path_OSD_Episodes` | Öffnet bei Serien `Window 1140` mit den verbleibenden Playlist-Folgen (`playlistvideo://`). Bei Einzel-Filmen schließt `1140` sofort und öffnet `Window 1141` (Cast/Besetzung). |
| **[5. Automatischer Multi-Source Scraper](#5-automatischer-multi-source-scraper-zweistufige-suche--failover)** | Klick auf Film oder Serienfolge | `xstreamscraper/.../scraper.py` → `_search_and_play()`, `PlaybackWatcher`<br>`xstreamscraper/.../streamTest.py` → `check()`<br>`xstreamscraper/.../streamHistory.py` | Zweistufige Suche über 12 aktive xStream-Seiten + VAVOO (Serien: erst `serienstream (DE)`, dann Rest + VAVOO; Filme: erst VAVOO, dann 11 Film-Seiten), 10s-Stream-Check bis zum 1. HLS-Segment, bis zu 5 Player-Failovers. |
| **[6. Smarter Stream-Wechsler & Voll-Benchmark](#6-manuelle-stream-auswahl-in-player--kontextmen--live-benchmark-aller-streams)** | **OSD-Button `🔄`** (ID `6009`) oder Kontextmenü *„Abspielen mit...“* | `skin.arctic.fuse.2/shortcuts/change_stream.py`<br>`xstreamscraper/.../scraper.py` → `select_and_play()`, `_ping_candidates()`<br>`xstreamscraper/.../streamTest.py` → `ping_host()`, `probe()` | Sammelt alle Quellen parallel, misst TCP-Ping für **alle** Hoster gleichermaßen (über `_HOSTER_DOMAINS`), prüft beim **Live-Benchmark** sämtliche gelisteten Streams auf echte Auflösung (`4K`/`1080p`/`720p`) und setzt an exakt derselben Sekunde (`resume`) fort. |

---

## 1. 📋 Automatisches Staffel- & Staffelwechsel-Queueing (Playlist-Aufbau)

### Kurzüberblick & Bedienung
Sobald du eine Serienfolge startest, reiht TMDb Helper automatisch alle verbleibenden Folgen der aktuellen Staffel in Kodis Video-Playlist ein. Erreichst du die vorletzte oder letzte Folge einer Staffel, wird automatisch auch die **nächste Staffel (`Staffel S+1`)** ab Folge 1 in die Playlist eingereiht.

### Technischer Ablauf im Code
1. **Trigger bei Stream-Start:** Beim Start des Videos ruft `PlayerMonitor.onAVStarted()` in [`kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) `get_playingitem()` → `queue_autoplay_episodes()` auf und startet `_queue_episodes_worker(tmdb_id, season, episode)` in einem `SafeThread`.
2. **Synchronisations-Event (`playlist_ready`):** `_queue_episodes_worker` erzeugt ein `threading.Event()` (`playlist_ready`) und übergibt es an den parallel startenden Thread `_fetch_intro_segments()`, damit `service.upnext` erst dann benachrichtigt wird, wenn die Playlist fertig aufgebaut ist.
3. **Erkennung von Erststart oder Staffelende (Zeilen 508–524):**
   Nach `1` Sekunde Wartezeit (`m.waitForAbort(1)`) prüft der Worker die aktive `PlayList(PLAYLIST_VIDEO)`:
   ```python
   pos = playlist.getposition()
   remaining_in_playlist = (playlist.size() - 1 - pos) if (playlist.size() > 0 and pos >= 0) else 0
   if playlist.size() <= 1 or remaining_in_playlist <= 0:
       pne.update(forced=True, single=False, clear=False)
   ```
   * **`playlist.size() <= 1`:** Trifft beim ersten Start einer Episode zu.
   * **`remaining_in_playlist <= 0`:** Trifft zu, wenn man mehrere Folgen geschaut hat und nun bei der **letzten Folge der bisherigen Staffel-Playlist** (dem Staffelfinale) angekommen ist.
4. **Automatischer Einschluss von `Staffel S+1` (`PlayerNextEpisodes.all_episodes` in [`episodes.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/player/action/episodes.py), Zeilen 30–42):**
   ```python
   current_season = BaseViewFactory('episodes', 'tv', self.tmdb_id, season=self.season).data or []
   future_current = [i for i in current_season if self.is_future_episode(i)]
   if len(future_current) <= 1:
       next_season = BaseViewFactory('episodes', 'tv', self.tmdb_id, season=self.season + 1).data or []
       if next_season:
           return list(current_season) + list(next_season)
   return current_season
   ```
   * Solange in der aktuellen Staffel noch 2 oder mehr Folgen offen sind (`len(future_current) > 1`), wird nur die aktuelle Staffel geladen.
   * Bei der vorletzten oder letzten Folge (`len(future_current) <= 1`) lädt `all_episodes` automatisch `self.season + 1` nach. Da `is_future_episode()` (Zeilen 81–90) alle Episoden mit `s_number > self.season` als zukünftige Folgen akzeptiert, werden die Folgen der neuen Staffel (`S+1, E01..E_n`) nahtlos an die bestehende Video-Playlist angehängt (`clear=False`).

---

## 2. ⚡ Hintergrund-Vorabladen (Preloading für Folge `N+1` bzw. `S+1, E01`)

### Kurzüberblick & Bedienung
Nach ca. 9–12 Sekunden Laufzeit der aktuellen Folge sucht und prüft der Scraper im Hintergrund bereits den Stream für die nächste Episode – am Ende einer Staffel automatisch für **Folge 1 der nächsten Staffel (`S+1, E01`)** – und legt die fertige Stream-URL im RAM ab (`0` Sekunden Ladezeit beim Folgenwechsel).

### Technischer Ablauf im Code
1. **Exakte Bestimmung der nächsten Folge über Staffelgrenzen ([`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 522–530):**
   `_queue_episodes_worker()` liest das erste Element aus `pne.next_episodes` aus:
   ```python
   next_list = pne.next_episodes or []
   if next_list:
       info = next_list[0].get('infolabels') or {}
       next_season = int(info.get('season') or season)
       next_episode = int(info.get('episode') or (int(episode) + 1))
   else:
       has_next = False
   ```
   * **Mitten in der Staffel (z. B. `S01E03`):** `next_list[0]` ist `S01E04` → `next_season = 1, next_episode = 4`.
   * **Am Staffelfinale (z. B. `S01E10`, wenn Staffel 2 existiert):** `next_list[0]` ist `S02E01` → `next_season = 2, next_episode = 1`.
   * **Am Serienfinale (keine weitere Folge/Staffel existiert):** `next_list` ist leer → `has_next = False`, der Worker beendet sich ohne unnötigen Preload-Aufruf.
2. **Trigger nach 8 Sekunden (`m.waitForAbort(8)`, Zeilen 540–547):**
   Ruft im Hintergrund auf:
   ```python
   executebuiltin(f"RunPlugin(plugin://script.module.xstreamscraper/?id={tmdb_id}&season={next_season}&episode={next_episode}&preload=true)")
   ```
3. **Lautlose Auflösung & Speicherung im RAM (`pre_resolve` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 374–426):**
   * Läuft mit `dialog._silent = True` und `with quietWindows():` komplett unsichtbar im Hintergrund.
   * Prüft zuerst ungespielte Streams auf `serienstream (DE)`, danach als Fallback alle übrigen aktivierten Seiten und VAVOO-Mirrors via `streamTest.check()`.
   * Speichert den ersten funktionierenden Stream über `_set_preload_cache()` für **7200 Sekunden (2 Stunden)** in `xbmcgui.Window(10000)` unter dem Property `xstream.preload.tv.<tmdb_id>.<next_season>.<next_episode>`.
4. **Sofortstart beim Episoden-/Staffelwechsel (`_search_and_play`, Zeilen 756–762):**
   Startet die nächste Folge (egal ob `S, E+1` oder `S+1, E01`), entnimmt `_get_preload_cache(key, pop=True)` die fertige Stream-URL aus dem RAM, trägt den Hoster in `streamHistory.remember()` ein und übergibt den Stream inkl. echtem TMDb-Episodentitel (`get_episode_title`) sofort an den Kodi-Player.

---

## 3. ⏭️ UpNext-Popup & Automatischer Folgenwechsel (Abspann, Episodenende & Staffelwechsel)

### Kurzüberblick & Bedienung
Am Ende einer Serienfolge – entweder **exakt zu Beginn des Abspanns** (falls in TheIntroDB hinterlegt) oder **15 Sekunden vor Ende der Videodatei** – erscheint unten rechts das **UpNext-Popup** (am Staffelfinale bereits mit Titel und Thumbnail von **Staffel `S+1`, Folge `1`**):
* **Ohne Tastendruck:** Nach Ablauf des **15-Sekunden-Countdowns** schaltet `service.upnext` aktiv per `self.player.playnext()` auf die nächste Folge um.
* **Mitte / OK auf „Abspielen“ (Control `3012`, vorfokussiert):** Startet die nächste Folge sofort.
* **Rechts + OK auf „Abbrechen“ (Control `4013` → `3013`) oder Zurück-Taste:** Schließt das Popup; das aktuelle Video läuft ohne Auto-Wechsel bis zum Ende weiter.
* **„Schaust du noch?“ (`StillWatching`):** Erscheint nach **5 automatisch durchgelaufenen Folgen in Folge** (`playedInARow = 5`).

### Technischer Ablauf im Code
1. **Abspann-Abfrage & Synchronisation (`_fetch_intro_segments` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 549–625):**
   * Initialisiert `payload` für jede Episode mit eindeutiger Episoden- und Serien-ID:
     ```python
     payload = {
         'current_episode': {
             'episodeid': f"{tmdb_id}.{season}.{episode}",
             'tvshowid': str(tmdb_id),
             'season': int(season),
             'episode': int(episode),
         }
     }
     ```
   * Fragt `https://api.theintrodb.org/v4/media?tmdb_id={tmdb_id}&season={season}&episode={episode}` (Timeout `4.0s`) ab und wartet bis zu `5s` (`10 × 0.5s`), falls `self.getTotalTime()` direkt nach Stream-Start noch `0` ist.
   * Enthält `data.get('credits')` einen gültigen Abspann-Start (`start_ms > 60000` und `total_time * 0.70 <= credits_start < total_time - 5.0`), wird `payload['notification_offset'] = int(credits_start)` gesetzt.
   * **Warten auf `playlist_ready` (Zeile 604):** `playlist_ready.wait(timeout=6.0)` stellt sicher, dass `_queue_episodes_worker()` die `PlayList(PLAYLIST_VIDEO)` (inkl. `Staffel S+1` am Staffelfinale) bereits aktualisiert hat, bevor `JSONRPC.NotifyAll` (`Other.upnext_data`) an `service.upnext` gesendet wird.
2. **Tracking & Episodenermittlung in `service.upnext` ([`monitor.py`](../kodi/addons/service.upnext/resources/lib/monitor.py) & [`playitem.py`](../kodi/addons/service.upnext/resources/lib/playitem.py)):**
   * `UpNextMonitor.onNotification()` empfängt `Other.upnext_data` und aktiviert `self.player.enable_tracking()`.
   * Da `current_episode.tvshowid` beim Wechsel von Staffel `S` auf Staffel `S+1` identisch bleibt (`str(tmdb_id)`), erkennt `PlayItem.get_next()` (`playitem.py` Zeile 47), dass es sich um dieselbe Serie handelt, und liest über `self.api.get_next_in_playlist(position)` das nächste Element (auch `S+1, E01`) aus `PlayList(PLAYLIST_VIDEO)` aus.
   * Da `includeWatched = true` in [`settings.xml`](../kodi/userdata/addon_data/service.upnext/settings.xml) gesetzt ist, funktioniert der automatische Übergang auch dann, wenn Folgen oder Staffeln bei Trakt bereits als gesehen markiert waren.
3. **15-Sekunden-Countdown & aktives `self.player.playnext()` ([`api.py`](../kodi/addons/service.upnext/resources/lib/api.py) & [`playbackmanager.py`](../kodi/addons/service.upnext/resources/lib/playbackmanager.py)):**
   * **Fall A (Mit Abspann-Offset `notification_offset`):** Popup öffnet sich bei `play_time >= notification_offset`. `credits_autoplay_deadline()` setzt mit `autoPlayCreditsTime = 15` die Deadline auf `min(total_time, max(play_time, offset) + 15)`. Nach 15 Sekunden (`remaining <= 0`) ruft `_update_credits_progress()` `page.set_auto_advance()` auf.
   * **Fall B (Ohne Abspann-Offset):** Popup öffnet sich 15 Sekunden vor Videoende (`autoPlayTimeXS..XL = 15`). Sobald der Countdown `total_time - play_time <= 1` erreicht (ohne Abbruch), ruft `show_popup_and_wait()` (Zeile 247) ebenfalls `next_up_page.set_auto_advance()` auf.
   * **Aktiver Wechsel:** In beiden Fällen ist `next_up_page.is_auto_advance() == True`, sodass `launch_popup()` (Zeile 156) sofort **`self.player.playnext()`** ausführt.
   * Sobald die neue Folge (bzw. `S+1, E01`) startet, feuert erneut `PlayerMonitor.onAVStarted()` und lädt automatisch die Intro-/Abspann-Segmente für die neue Folge sowie den Preload für die darauffolgende Episode.

---

## 4. 📺 In-Player Episoden-Schublade (`Window 1140`) & Cast-Fallback (`Window 1141`)

### Kurzüberblick & Bedienung
* **Steuerkreuz Unten (`▼`)** während der Vollbild-Wiedergabe ([`player_controls.xml`](../kodi/userdata/keymaps/player_controls.xml): `<down>ActivateWindow(1140)</down>`):
  * **Bei Serien:** Öffnet von unten die horizontale **Episoden-Schublade (`Window 1140`)** zum Blättern und direkten Anwählen.
  * **Bei Einzel-Filmen:** Schließt `Window 1140` im `<onload>` und öffnet automatisch die **Schauspieler-/Besetzungs-Schublade (`Window 1141`)**.

### Technischer Ablauf im Code ([`Custom_1140_OSD_Playlist.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml) & [`Includes_Paths.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Paths.xml))
* In `Custom_1140_OSD_Playlist.xml` (Zeilen 6–7) prüft das Fenster beim Öffnen `$EXP[Exp_OSD_HasPlaylist]`. Ist keine Playlist aktiv (Einzel-Film), wird `Dialog.Close(1140,true)` und `ActivateWindow(1141)` ausgeführt.
* Bei Serien lädt Container `7000` die Variable `$VAR[Path_OSD_Episodes]` (`Includes_Paths.xml` Zeilen 265–269), welche während einer aktiven Video-Playlist `playlistvideo://` anzeigt (also die aktuell laufende Folge sowie alle kommenden Folgen der Playlist – am Staffelfinale inklusive der bereits angehängten Folgen von `Staffel S+1`).

---

## 5. 🔍 Automatischer Multi-Source Scraper (Zweistufige Suche & Failover)

### Technischer Ablauf im Code ([`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), [`streamTest.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/streamTest.py), [`streamHistory.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/streamHistory.py))
1. **Aktivierte Quellen ([`kodi/userdata/addon_data/script.module.xstreamscraper/settings.xml`](../kodi/userdata/addon_data/script.module.xstreamscraper/settings.xml)):**
   `vavoo` + **12 deutsche xStream-Seiten** (`serienstream`, `aniworld`, `animetoast`, `filmpalast`, `filmo`, `streamcloud`, `netzkino`, `kellerkino`, `movie2k`, `megakino`, `moflix-stream`, `einschalten`).
2. **Zweistufige Prioritätssuche beim Auto-Play (`_search_and_play`, Zeilen 741–821):**
   * **Stufe 1:** Bei Serien wird zuerst gezielt `serienstream` (gefiltert auf `languageCode == "(DE)"`) nach noch ungespielten Streams durchsucht; bei Filmen zuerst die `vavoo`-Mirrors.
   * **Stufe 2 (Fallback):** Liefert Stufe 1 keinen funktionierenden Stream, werden alle übrigen aktivierten Seiten parallel per `ThreadPoolExecutor` durchsucht und nach `streamHistory.order()` sortiert.
3. **10s-Stream-Check & 5× Player-Failover:**
   * `streamTest.check()` prüft jeden aufgelösten Link mit `10s` Zeitlimit (`LIMIT = 10`) bis zum ersten echten HLS-Videosegment (bis zu 4 Playlist-Ebenen tief).
   * `PlaybackWatcher` überwacht nach `setResolvedUrl` für 10 Sekunden, ob Kodi tatsächlich `onAVStarted` meldet, und schaltet bei einem Player-Fehler automatisch bis zu **5-mal (`MAX_FAILOVERS = 5`)** auf den nächsten Stream weiter.

---

## 6. 🎯 Manuelle Stream-Auswahl (In-Player & Kontextmenü) + Live-Benchmark aller Streams

### Kurzüberblick & Bedienung
* **Mitten im Video:** **Steuerkreuz Oben (`▲`)** → **`🔄`-Symbol (Button `6009`)** klicken.
* **Vor dem Start:** Auf einem Poster **Mitte / OK gedrückt halten** (Kontextmenü) → *„Abspielen mit...“* → *„xStream Scraper (Quelle manuell wählen)“*.

### Technischer Ablauf im Code (`select_and_play` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 414–645)
1. **Gleichberechtigte Sammlung aller Quellen:**
   `select_and_play()` sammelt sofort **alle** VAVOO-Mirrors und **alle** aktivierten xStream-Seiten parallel (`candidates = mirrors + hosters`).
2. **Gleichberechtigter TCP-Ping für alle Hoster (`_ping_target` & `_HOSTER_DOMAINS`, Zeilen 420–468):**
   * Manche xStream-Seiten (wie `serienstream` oder `aniworld`) liefern vor der Auflösung nur den Hoster-Namen (z. B. `"VOE"`, `"Filemoon"`, `"Vidmoly"`) und einen internen Redirect-Pfad `/r?...` statt einer fertigen Hoster-URL.
   * Damit diese Streams beim initialen TCP-Ping exakt genauso bewertet werden wie VAVOO-Mirrors oder Direktlinks, löst `_ping_target()` den Hoster-Namen über `_HOSTER_DOMAINS` (`voe.sx`, `filemoon.sx`, `streamwish.to`, `vidmoly.to`, `luluvdo.com`, `speedfiles.net`, `vidoza.net`, `streamtape.com`, `dood.li`) auf und misst parallel (`ThreadPoolExecutor(max_workers=8)`, Timeout `1.2s`) die TCP-Latenz für **alle** Kandidaten.
3. **Ampel-Sortierung (`_rank_and_format_candidates`, Zeilen 470–524):**
   Sortiert nach `(probe_rank, status_tier, host_prio, ping_ms)`:
   * `🟢 ✅ [Geprüft]`: Im Live-Benchmark erfolgreich getestet
   * `🟢`: Ping `< 280 ms`
   * `🟡`: Ping `280–650 ms` oder unbekannt
   * `🔴` / `🔴 ❌ [Defekt]`: Ping `> 650 ms` oder fehlerhaft
4. **Live-Benchmark über ALLE Streams (Menüeintrag `0`: `⚡ [Live-Speedtest: Alle Streams auflösen & echte Auflösung messen]`, Zeilen 589–619):**
   * Klickst du auf Eintrag `0`, werden **alle** noch ungeprüften Streams der Liste (`to_test = [c for c in ranked if "_probe_ok" not in c]`) nacheinander mit `_test_with_probe(cand, limit=5)` aufgelöst, bis zum ersten HLS-Videosegment geladen, auf ihre reale Auflösung (`4K`, `1080p`, `720p`, `480p`, `HD`) untersucht und mit ihrer echten Ladezeit in `ms` neu sortiert.
   * Du kannst den Benchmark jederzeit mit *Abbrechen* stoppen; alle bis dahin geprüften Streams behalten ihr `🟢 ✅ [Geprüft]`-Ergebnis.
5. **Sekundengenauer Resume (`resume_time`):**
   Wurde der Wechsler mitten im Video über Button `6009` ([`change_stream.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/change_stream.py)) geöffnet, übergibt `_listitem()` `StartOffset` & `setResumePoint` und `_play()` erzwingt zusätzlich per `player.seekTime(target)` die Fortsetzung an exakt derselben Sekunde.
