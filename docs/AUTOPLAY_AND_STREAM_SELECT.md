# ⏩ Autoplay, Preloading, Episoden-Schublade & Stream-Scraper

> [!NOTE]
> Eine Gegenüberstellung zwischen der früheren Kurz-Dokumentation und dem tatsächlichen Code-Verhalten (inkl. des behobenen `autoPlayCreditsTime`-Bugs) findest du in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md).

---

## 🧭 Funktions-Schnellindex

| Funktion | Auslöser | Kern-Dateien & Funktionen | Verhalten im Überblick |
| :--- | :--- | :--- | :--- |
| **[1. Staffel-Playlist Queueing](#1-automatisches-staffel-queueing-playlist-aufbau)** | Automatisch (`1s` nach Episodenstart) | `tmdbhelper/.../monitor/player.py` → `_queue_episodes_worker()`<br>`tmdbhelper/.../player/action/episodes.py` → `PlayerNextEpisodes.update()` | Reiht alle nachfolgenden Episoden (`> aktuelle Folge`) der laufenden Staffel in Kodis `PlayList(PLAYLIST_VIDEO)` ein. |
| **[2. Hintergrund-Preloading](#2-hintergrund-vorabladen-preloading-fr-folge-n1)** | Automatisch (~`9–12s` nach Episodenstart) | `tmdbhelper/.../monitor/player.py` → `_queue_episodes_worker()`<br>`xstreamscraper/.../scraper.py` → `pre_resolve()` | Sucht & prüft im Hintergrund lautlos (`quietWindows`) den ersten funktionierenden Stream für `Folge N+1` und legt ihn für 2 Std. im RAM (`Window(10000)`) ab. |
| **[3. UpNext-Countdown & Abspann-Wechsel](#3-upnext-popup--automatischer-folgenwechsel-abspann--episodenende)** | Automatisch bei Abspannbeginn (`notification_offset`) oder `15s` vor Videoende | `tmdbhelper/.../monitor/player.py` → `_fetch_intro_segments()`<br>`service.upnext/.../api.py` → `credits_autoplay_deadline()`<br>`service.upnext/.../playbackmanager.py` → `launch_up_next()` | Blendet das UpNext-Popup mit **15-Sekunden-Countdown** ein und startet danach automatisch die nächste Folge (`player.playnext()` bei Abspann bzw. Playlist-Übergang am Ende). |
| **[4. In-Player Episoden-Schublade](#4-in-player-episoden-schublade-window-1140--cast-fallback-window-1141)** | **Steuerkreuz Unten (`▼`)** im Vollbild-Video | `keymaps/player_controls.xml`<br>`skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml`<br>`skin.arctic.fuse.2/1080i/Includes_Paths.xml` → `Path_OSD_Episodes` | Öffnet bei Serien `Window 1140` mit den verbleibenden Playlist-Folgen (bzw. Staffelfolgen). Bei Einzel-Filmen schließt `1140` sofort und öffnet `Window 1141` (Cast/Besetzung). |
| **[5. Automatischer Multi-Source Scraper](#5-automatischer-multi-source-scraper-zweistufige-suche--failover)** | Klick auf Film oder Serienfolge | `xstreamscraper/.../scraper.py` → `_search_and_play()`, `PlaybackWatcher`<br>`xstreamscraper/.../streamTest.py` → `check()`<br>`xstreamscraper/.../streamHistory.py` | Zweistufige Suche (Serien: erst `serienstream (DE)`, dann Rest + VAVOO; Filme: erst VAVOO, dann 11 Film-Seiten), 10s-Stream-Check bis zum 1. HLS-Segment, bis zu 5 Player-Failovers. |
| **[6. Smarter Stream-Wechsler & Speedtest](#6-manuelle-stream-auswahl-in-player--kontextmen--live-speedtest)** | **OSD-Button `🔄`** (ID `6009`) oder Kontextmenü *„Abspielen mit...“* | `skin.arctic.fuse.2/shortcuts/change_stream.py`<br>`xstreamscraper/.../scraper.py` → `select_and_play()`<br>`xstreamscraper/.../streamTest.py` → `ping_host()`, `probe()` | Sammelt alle Quellen parallel, misst TCP-Ping (8 Threads), zeigt Qualitäts-/Speed-Ampel (`🟢/🟡/🔴`), bietet Top-5 Live-Speedtest und setzt auf Wunsch an exakt derselben Sekunde (`resume`) fort. |

---

## 1. 📋 Automatisches Staffel-Queueing (Playlist-Aufbau)

### Kurzüberblick & Bedienung
Sobald du eine beliebige Serienfolge startest, wird die restliche Staffel im Hintergrund automatisch in die Kodi-Wiedergabeliste eingereiht, ohne dass du eine Playlist manuell erstellen musst.

### Technischer Ablauf im Code
1. **Trigger bei Stream-Start:** Sobald Kodi das Video- und Audiosignal öffnet, feuert `PlayerMonitor.onAVStarted()` in [`kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) und ruft `get_playingitem()` auf.
2. **Metadaten-Prüfung:** Wenn `self.dbtype == 'episode'` sowie `tmdb_id`, `season` und `episode` gesetzt sind (Zeile 484: `queue_autoplay_episodes()`), startet ein Hintergrund-Thread (`SafeThread`) mit `_queue_episodes_worker(tmdb_id, season, episode)`.
3. **1-Sekunden-Stabilisierung:** Der Worker wartet zunächst `1` Sekunde (`m.waitForAbort(1)`) und prüft, ob `PlayList(PLAYLIST_VIDEO).size() <= 1` ist (Zeilen 497–501).
4. **Playlist-Generierung:** Trifft dies zu, instanziiert er `PlayerNextEpisodes(tmdb_id, season, episode, player='xstream.json')` aus [`episodes.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/player/action/episodes.py) und ruft `pne.update(forced=True, single=False, clear=False)` auf:
   * `all_episodes` lädt alle Episoden der aktuellen Staffel (`season=self.season`).
   * `is_future_episode()` (Zeilen 74–83) filtert auf Episoden derselben Staffel mit `e_number > self.episode`.
   * `finalise_item()` setzt für jede Folge `player='xstream.json'`, `mode='play'`, `ignore_default='true'` und `allow_playlist='false'`.
   * Da `clear=False` übergeben wird, bleibt die aktuell laufende Folge auf Index `0` erhalten und alle verbleibenden Folgen der Staffel werden ab Index `1` angehängt.

### Besonderheiten & Edge-Cases
* **Nur aktuelle Staffel:** `BaseViewFactory('episodes', 'tv', self.tmdb_id, season=self.season)` (`episodes.py` Zeile 34) lädt bewusst nur die aktuelle Staffel, um riesige Playlists bei Serien mit vielen Staffeln zu vermeiden.
* **Greift auch nach manueller Quellenwahl:** Selbst wenn eine Folge über *„xStream Scraper (Quelle manuell wählen)“* ([`xstream_select.json`](../kodi/userdata/addon_data/plugin.video.themoviedb.helper/players/xstream_select.json) mit `"make_playlist": "false"`) gestartet wurde, ist `playlist.size()` beim Start `<= 1`. Dadurch reiht `_queue_episodes_worker` die Folge-Episoden trotzdem für Autoplay mit dem Standard-Player `xstream.json` ein.

---

## 2. ⚡ Hintergrund-Vorabladen (Preloading für Folge `N+1`)

### Kurzüberblick & Bedienung
Während du die aktuelle Folge schaust, sucht und testet der Scraper im Hintergrund bereits den besten Stream für die nächste Folge (`N+1`) und speichert die fertige Video-URL im Arbeitsspeicher. Beim Episodenwechsel startet die nächste Folge dadurch in **0 Sekunden** ohne Suchfenster.

### Technischer Ablauf im Code
1. **Zeitpunkt des Starts (~9–12 Sekunden nach Wiedergabebeginn):**
   In [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) (`_queue_episodes_worker`, Zeile 515) wartet der Thread nach Abschluss von `PlayerNextEpisodes.update()` weitere **8 Sekunden** (`m.waitForAbort(8)`) und führt dann aus:
   ```python
   executebuiltin(f"RunPlugin(plugin://script.module.xstreamscraper/?id={tmdb_id}&season={season}&episode={int(episode)+1}&preload=true)")
   ```
2. **Routing in `main.py`:**
   In [`kodi/addons/script.module.xstreamscraper/main.py`](../kodi/addons/script.module.xstreamscraper/main.py) (Zeilen 25–26) erkennt das Plugin `params.get("preload") == "true"` und ruft `scraper.pre_resolve(type, tmdb_id, season, episode)` auf.
3. **Lautlose Suche & Vorab-Test (`pre_resolve` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 360–412):**
   * Prüft zuerst via `_get_preload_cache(key)`, ob für `tv.<id>.<season>.<episode>` bereits ein gültiger Cache-Eintrag existiert.
   * Setzt `dialog._silent = True` und aktiviert den Context-Manager `with quietWindows():` ([`requestHandler.py`](../kodi/addons/plugin.video.xstream/resources/lib/handler/requestHandler.py), Zeile 77), sodass keinerlei Ladebalken oder Fehlerdialoge im laufenden Video aufpoppen.
   * Sucht wie beim normalen Serien-Autoplay zuerst auf der Prioritätsseite `serienstream` (nur noch nicht gespielte Streams aus `streamHistory.used(key)`).
   * Testet jeden Kandidaten über `streamTest.runLimited(lambda c=candidate: _test(c))` (echte Auflösung über ResolveURL/VAVOO + HTTP-Abruf bis zum ersten HLS-Videosegment).
   * Findet `serienstream` keinen gültigen Stream, durchsucht `pre_resolve` als Fallback alle übrigen aktivierten Seiten sowie VAVOO-Mirrors.
4. **Speichern im RAM-Cache (`_set_preload_cache`, Zeilen 345–358):**
   Sobald der erste funktionierende Stream gefunden ist, wird er als JSON-String im Home-Window (`xbmcgui.Window(10000)`) unter dem Property-Namen `xstream.preload.tv.<tmdb_id>.<season>.<episode>` gespeichert:
   ```json
   {
     "candidate": {"site": "...", "name": "...", "link": "..."},
     "url": "https://.../master.m3u8|User-Agent=...",
     "ts": 1732620000.0
   }
   ```
5. **Abruf beim Start der nächsten Folge (`_search_and_play`, Zeilen 729–735):**
   Startet Folge `N+1`, ruft `_search_and_play` sofort `_get_preload_cache(key, pop=True)` auf:
   * Ist der Eintrag jünger als **7200 Sekunden (2 Stunden)**, wird das Window-Property gelöscht (`pop=True`), der Kandidat in `streamHistory.remember(key, cand)` vermerkt und die vorbereitete URL sofort an `_play(preloaded_url, media_meta)` übergeben.

### Parameter & Grenzwerte
| Parameter / Property | Wert | Datei | Bedeutung |
| :--- | :--- | :--- | :--- |
| `m.waitForAbort(8)` | `8s` (+ `1s` + Queue-Zeit) | `tmdbhelper/.../monitor/player.py` | Wartezeit nach Playlist-Aufbau vor Start von `preload=true`. |
| `xstream.preload.<key>` | JSON in `Window(10000)` | `xstreamscraper/.../scraper.py` | RAM-Cache-Property für die vorab aufgelöste Stream-URL. |
| Cache-TTL (`time.time() - ts`) | `7200s` (2 Stunden) | `xstreamscraper/.../scraper.py` (Zeile 334) | Maximale Gültigkeitsdauer eines vorgeladenen Streams. |

### Besonderheiten & Edge-Cases
* **Staffelende:** Da `_queue_episodes_worker` starr `episode={int(episode)+1}` derselben Staffel übergibt, läuft das Preloading bei der letzten Folge einer Staffel ins Leere (kein automatisches Preloading von `Staffel S+1, Folge 1`).

---

## 3. ⏭️ UpNext-Popup & Automatischer Folgenwechsel (Abspann & Episodenende)

### Kurzüberblick & Bedienung
Am Ende einer Serienfolge – entweder **exakt zu Beginn des Abspanns** (sofern der Abspann in TheIntroDB hinterlegt ist) oder **15 Sekunden vor dem Ende der Videodatei** – erscheint unten rechts das **UpNext-Popup**:
* **Ohne Tastendruck:** Ein **15-Sekunden-Countdown** läuft herunter; danach startet automatisch die nächste Folge.
* **Mitte / OK auf „Abspielen“ (Control `3012`, standardmäßig fokussiert):** Startet die nächste Folge sofort.
* **Rechts + OK auf „Abbrechen“ (Control `4013` → `3013`) oder Zurück-Taste:** Schließt das Popup; die aktuelle Folge läuft ohne automatischen Wechsel bis zum Ende weiter.
* **„Schaust du noch?“ (`StillWatching`):** Nach **5 automatisch durchgelaufenen Folgen in Folge** (`playedInARow = 5`) fragt UpNext nach einer Bestätigung, bevor weiter abgespielt wird.

### Technischer Ablauf im Code
1. **Abspann-Erkennung über TheIntroDB (`_fetch_intro_segments` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 526–599):**
   * Beim Start der Episode ruft TMDb Helper `https://api.theintrodb.org/v4/media?tmdb_id={tmdb_id}&season={season}&episode={episode}` (Timeout `4.0s`) ab.
   * Ist `self.getTotalTime()` direkt nach `onAVStarted` noch `0`, wartet der Thread bis zu `5` Sekunden (`10 × 0.5s`) auf die gültige Gesamtlaufzeit.
   * Für den ersten Eintrag in `data.get('credits')` wird geprüft:
     * `start_ms > 60000` (Abspann darf frühestens nach 60 Sekunden Laufzeit beginnen)
     * `(total_time * 0.70) <= credits_start < (total_time - 5.0)` (Abspann muss zwischen **70 % der Gesamtlaufzeit** und **5 Sekunden vor Ende** liegen).
   * Ist die Bedingung erfüllt, wird `payload['notification_offset'] = int(credits_start)` gesetzt und Base64-kodiert per `JSONRPC.NotifyAll` (`sender: 'plugin.video.themoviedb.helper.SIGNAL'`, `message: 'Other.upnext_data'`) an `service.upnext` gesendet.
2. **Zeitpunkt der Popup-Einblendung (`Api.notification_time` in [`kodi/addons/service.upnext/resources/lib/api.py`](../kodi/addons/service.upnext/resources/lib/api.py), Zeilen 234–256):**
   `UpNextMonitor.run()` ([`monitor.py`](../kodi/addons/service.upnext/resources/lib/monitor.py), Zeile 132) prüft im 1-Sekunden-Takt `if total_time - play_time > notification_time:`:
   * **Fall A (Abspann durch TheIntroDB bekannt):** `notification_offset` ist gesetzt → `notification_time = total_time - int(notification_offset)`. Das Popup öffnet sich exakt bei `play_time >= notification_offset` (zu Abspannbeginn).
   * **Fall B (Kein Abspann bekannt):** `customAutoPlayTime` ist `true` und alle Längen-Kategorien (`autoPlayTimeXS` bis `autoPlayTimeXL`) stehen in [`settings.xml`](../kodi/userdata/addon_data/service.upnext/settings.xml) auf `15`. Das Popup öffnet sich **15 Sekunden vor Videoende**.
3. **15-Sekunden-Countdown & Wechsel-Auslösung (`PlaybackManager.show_popup_and_wait` & `launch_popup` in [`playbackmanager.py`](../kodi/addons/service.upnext/resources/lib/playbackmanager.py)):**
   * **Bei erkanntem Abspann (Fall A):**
     `credits_autoplay_deadline()` ([`api.py`](../kodi/addons/service.upnext/resources/lib/api.py), Zeilen 14–27) liest `autoPlayCreditsTime` (`15` Sekunden, mit Fallback auf `autoPlaySeasonTime` bzw. `15`) und setzt `credits_deadline = min(total_time, max(play_time, offset) + 15)`.
     Alle `100 ms` aktualisiert `_update_credits_progress()` die verbleibenden Sekunden (`Window.Property(remaining)`) und den Fortschrittsbalken (`Control 3014`). Sobald die **15 Sekunden abgelaufen sind** (`remaining <= 0`), setzt `page.set_auto_advance()` das Flag `auto_advance = True`, beendet die Warteschleife und ruft in `launch_popup()` (Zeile 156) aktiv **`self.player.playnext()`** auf!
   * **Ohne Abspann-Zeitstempel (Fall B):**
     `credits_deadline` ist `None`. Der Countdown zählt die verbleibenden 15 Sekunden der Datei bis `total_time - play_time <= 1` (`0:01`) herunter, schließt das Popup und lässt Kodis Videoplayer am regulären Dateiende (`0:00`) auf die nächste Folge in `PlayList(PLAYLIST_VIDEO)` wechseln.

### Parameter & Einstellungen ([`kodi/userdata/addon_data/service.upnext/settings.xml`](../kodi/userdata/addon_data/service.upnext/settings.xml))
| Einstellung | Wert | Bedeutung |
| :--- | :--- | :--- |
| `simpleMode` | `1` | Nutzt das vollständige Skin-Template `script-upnext-upnext.xml` (in Arctic Fuse 2: `OSD_UpNext`). |
| `autoPlayMode` | `0` | Automatische Wiedergabe aktiv (`0 = Autoplay`, `1 = Nicht automatisch abspielen`). |
| `enablePlaylist` | `true` | Erlaubt UpNext, die nächste Folge aus Kodis `PlayList(PLAYLIST_VIDEO)` zu lesen. |
| `playedInARow` | `5` | Nach 5 automatisch gewechselten Folgen erscheint der `StillWatching`-Dialog. |
| `autoPlaySeasonTime` / `autoPlayTimeXS..XL` | `15` | Popup erscheint 15 Sekunden vor Dateiende, wenn kein Abspann-Offset vorliegt. |
| `autoPlayCreditsTime` | `15` | Countdown-Dauer (15 Sek.) ab Abspannbeginn (`notification_offset`) bis zum automatischen `player.playnext()`. |
| `stopAfterClose` | `false` | Klick auf „Abbrechen“ stoppt nicht das aktuelle Video, sondern bricht nur den Auto-Wechsel ab. |

---

## 4. 📺 In-Player Episoden-Schublade (`Window 1140`) & Cast-Fallback (`Window 1141`)

### Kurzüberblick & Bedienung
* Drückst du während der Vollbild-Wiedergabe **Steuerkreuz Unten (`▼`)**:
  * **Bei Serien:** Öffnet sich von unten die horizontale **Episoden-Schublade (`Window 1140`)**. Du kannst mit Links/Rechts durch die Folgen blättern und mit **Mitte / OK** direkt wechseln.
  * **Bei Filmen:** Öffnet sich automatisch die **Besetzungs-/Schauspieler-Schublade (`Window 1141`)**.
  * **Bei Live-TV:** Öffnet sich das normale Video-OSD (`<FullscreenLiveTV>` → `<down>OSD</down>`).

### Technischer Ablauf im Code
1. **Keymap-Bindung ([`kodi/userdata/keymaps/player_controls.xml`](../kodi/userdata/keymaps/player_controls.xml), Zeilen 5 & 12):**
   In `<FullscreenVideo>` ist `<down>` fest auf `ActivateWindow(1140)` gemappt.
2. **Fenster-Logik in [`Custom_1140_OSD_Playlist.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml) (Zeilen 5–7):**
   ```xml
   <onload>CancelAlarm(osd_timeout,true)</onload>
   <onload condition="!$EXP[Exp_OSD_HasPlaylist]">Dialog.Close(1140,true)</onload>
   <onload condition="!$EXP[Exp_OSD_HasPlaylist]">ActivateWindow(1141)</onload>
   ```
   * Die Expression `Exp_OSD_HasPlaylist` ([`Includes_Expressions.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Expressions.xml), Zeile 219) ist wahr bei `VideoPlayer.Content(episodes)`, `VideoPlayer.Content(livetv)` oder wenn `VideoPlayer.PlaylistLength > 1` ist.
   * Läuft ein einzelner Film (`Exp_OSD_HasPlaylist == false`), schließt sich `Window 1140` noch im `<onload>` und öffnet stattdessen `Window 1141` (`Custom_1141_OSD_Cast.xml`).
3. **Datenquelle der Episoden-Liste (`Path_OSD_Episodes` in [`Includes_Paths.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Paths.xml), Zeilen 265–269):**
   Container `7000` in `Window 1140` nutzt `$VAR[Path_OSD_Episodes]` mit folgender Prioritätsreihenfolge:
   1. **Aktive Video-Playlist (`playlistvideo://`):** Wenn `PlaylistLength > 1` und `PlaylistPosition < PlaylistLength`.
   2. **Lokale Kodi-Datenbank (`videodb://`):** Wenn die Serie in der lokalen Kodi-DB existiert.
   3. **TMDb Helper Online-Staffel (`plugin://plugin.video.themoviedb.helper/?info=episodes...`):** Fallback (z. B. bei der letzten Folge der Staffel).

### Besonderheiten & Edge-Cases
* **Warum `playlistvideo://` nur die aktuelle + nachfolgende Folgen zeigt:** Da `PlayerNextEpisodes` beim Start von Folge `E` nur die Episoden `>= E` in der Playlist belässt und `service.upnext` beim Episodenwechsel über `Api.reset_queue()` (`Playlist.Remove` auf Index `0`) die jeweils beendete Folge aus der Playlist entfernt, zeigt `Window 1140` während einer laufenden Staffel-Playlist die **aktuell laufende sowie alle kommenden Folgen der Staffel**. Erst bei der letzten Folge der Staffel (wenn `PlaylistPosition < PlaylistLength` nicht mehr zutrifft) fällt `Path_OSD_Episodes` auf den TMDb-Helper-Pfad zurück und listet wieder alle Folgen der Staffel ab Folge 1 auf.

---

## 5. 🔍 Automatischer Multi-Source Scraper (Zweistufige Suche & Failover)

### Kurzüberblick & Bedienung
Ein Klick auf einen Film oder eine Serienfolge in den Startseiten-Widgets startet `xstream.json` (`plugin://script.module.xstreamscraper/?id={tmdb}...`). Der Scraper sucht automatisch nach deutschen Streams, prüft die Videodaten vorab und wechselt bei Fehlern im Hintergrund auf den nächsten Hoster.

### Technischer Ablauf im Code
1. **Brücke zu xStream ([`xstreamBridge.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/xstreamBridge.py)):**
   Bindet zur Laufzeit die Site-Scraper aus `plugin.video.xstream/sites` in `sys.path` ein und leitet `tools.infoDialog` ins Kodi-Log um, damit parallele Suchen keine Popup-Meldungen werfen.
2. **Aktivierte Anbieter ([`kodi/userdata/addon_data/script.module.xstreamscraper/settings.xml`](../kodi/userdata/addon_data/script.module.xstreamscraper/settings.xml)):**
   * **Aktiviert (`true`):** `vavoo` + **12 xStream-Sites** (`serienstream`, `aniworld`, `animetoast`, `filmpalast`, `filmo`, `streamcloud`, `netzkino`, `kellerkino`, `movie2k`, `megakino`, `moflix-stream`, `einschalten`).
   * **Deaktiviert (`false`):** `kinoger`, `hdfilme`, `burningseries`, `internetarchive`, `api_sites`.
3. **Zweistufige Prioritätssuche in `_search_and_play()` ([`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 715–793):**
   * **Stufe 1 (Prioritäts-Quelle):**
     * **Bei Serien (`PRIORITY_SITE = "serienstream"`):** Es wird zunächst **nur `serienstream`** abgefragt (`find(lambda site: site == "serienstream")`). In `get_hosters()` (Zeile 173) werden alle fremdsprachigen Einträge ausgefiltert (`a.get("languageCode") != "(DE)"`).
     * **Bei Filmen:** Es werden zunächst **nur die VAVOO-Mirrors** (`_vavoo_mirrors`) abgefragt (sofern in `plugin.video.vavooto` `stream_select != "0"` steht).
     * Aus Stufe 1 werden über `fresh(priority)` nur Streams getestet, die für diesen Titel noch nicht in `stream_history.json` stehen, und über `skipFailed=True` kürzlich gescheiterte Hoster übersprungen.
   * **Stufe 2 (Fallback über alle übrigen Quellen):**
     Erst wenn Stufe 1 keinen funktionierenden Stream liefert, ruft `streams()` `find(lambda site: site != PRIORITY_SITE)` auf (parallele Suche via `ThreadPoolExecutor` über alle übrigen aktivierten Sites), kombiniert diese mit den restlichen VAVOO-Mirrors und sortiert sie über `streamHistory.order()` (1. ungespielte gesunde Streams, 2. am längsten nicht gespielte Streams, 3. kürzlich gescheiterte Streams).
4. **Tiefen-Prüfung jedes Kandidaten (`_test` & `streamTest.check` in [`streamTest.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/streamTest.py)):**
   * Jeder Kandidat wird in einem Daemon-Thread mit striktem **10-Sekunden-Zeitlimit (`LIMIT = 10`)** (`runLimited`) über `vjackson.resolve` (VAVOO) bzw. `resolveurl.resolve` aufgelöst.
   * `streamTest.check(url, deadline)` ruft die aufgelöste Video-URL ab. Ist es eine HLS-Playlist (`#EXTM3U`), folgt der Tester bis zu **4 Verschachtelungsebenen (`for depth in range(4)`)** bis zum **ersten tatsächlichen Video-Segment** und verwirft leere Playlists, HTML-Fehlerseiten (`<!doctype`, `<html`) oder reine Textdateien.
5. **Kodi-Player-Überwachung & Failover (`PlaybackWatcher` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 48–89 & 780–793):**
   * Selbst wenn `streamTest.check` erfolgreich war, wartet `PlaybackWatcher` nach `setResolvedUrl` bis zu **10 Sekunden (`streamTest.LIMIT`)** auf Kodis `onAVStarted`.
   * Meldet Kodi `onPlayBackError` oder startet das Video nicht innerhalb von 10 Sekunden, schließt `_close_error_dialog()` automatisch Kodis Fehlerdialog (`Dialog.Close(okdialog,true)`), stoppt den hängenden Player und startet über `_replay()` automatisch den nächsten funktionierenden Stream aus dem Generator (bis zu **`MAX_FAILOVERS = 5`** Versuche).

### Stream-Rotation & Fehler-Gedächtnis ([`streamHistory.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/streamHistory.py))
* **`stream_history.json` (`MAX_TITLES = 200`, `MAX_STREAMS = 50`):** Speichert pro Film (`movie.<tmdb_id>`) bzw. Episode (`tv.<tmdb_id>.<s>.<e>`) die bereits gespielten `site|hoster`-Kombinationen. Startest du denselben Titel direkt noch einmal (weil z. B. der Ton asynchron war), wählt der Scraper automatisch einen anderen Stream.
* **`stream_failures.json` (`FAILED_SECONDS = 3600` / 60 Minuten):**
  * **Timeout (`failures.timedOut`):** Sperrt den gesamten Hoster titelübergreifend für 60 Minuten (`host|<hostername>`), und sortiert verbleibende Kandidaten dieses Hosters ans Ende der Warteschlange.
  * **Defekter Link / 404 (`failures.broken`):** Sperrt nur diese Kombination für den aktuellen Titel (`<key>|<site>|<hoster>`).

---

## 6. 🎯 Manuelle Stream-Auswahl (In-Player & Kontextmenü) + Live-Speedtest

### Kurzüberblick & Bedienung
Du kannst jederzeit manuell aus einer nach Qualität und Latenz sortierten Liste aller Hoster wählen:
* **Option A – Mitten im laufenden Video:** **Steuerkreuz Oben (`▲`)** drücken → in der unteren Leiste rechts auf das **`🔄`-Symbol (Button `6009`)** klicken. Das Video pausiert, der Auswahldialog öffnet sich, und nach Auswahl setzt der neue Stream **an exakt derselben Sekunde** fort.
* **Option B – Vor dem Start:** Auf einem Poster **Mitte / OK gedrückt halten** (Kontextmenü) → **„Abspielen mit...“** → **„xStream Scraper (Quelle manuell wählen)“** wählen.

### Technischer Ablauf im Code
1. **In-Player Auslöser ([`kodi/addons/skin.arctic.fuse.2/shortcuts/change_stream.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/change_stream.py)):**
   * Liest `curr_time = int(player.getTime())` sowie `tmdb_id`, `tvshow.tmdb`, `season` und `episode` aus dem aktiven `VideoInfoTag` (mit Fallback auf die `Window(10000)`-Properties `TMDbHelper.playing.*` und `VideoPlayer.UniqueId(...)`).
   * Schließt das OSD (`Dialog.Close(videoosd,true)`), pausiert den Player (`player.pause()`) und ruft auf:
     ```python
     RunPlugin(plugin://script.module.xstreamscraper/?id={_id}&season={season}&episode={episode}&select=true&resume={curr_time})
     ```
2. **Parallele Gesamtsuche & TCP-Ping (`select_and_play` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 530–628):**
   * Im Gegensatz zum Auto-Play sammelt `select_and_play()` sofort **alle** VAVOO-Mirrors + **alle** aktivierten xStream-Seiten (`candidates = mirrors + hosters`).
   * `_ping_candidates()` (Zeilen 429–454) misst parallel mit `ThreadPoolExecutor(max_workers=8)` über `streamTest.ping_host()` (TCP-Connect auf Port 80/443, Timeout `1.2s`) die Latenz zu jeder eindeutigen Hoster-Domain in Millisekunden.
3. **Sortierung & Ampel-Formatierung (`_rank_and_format_candidates`, Zeilen 455–509):**
   Jeder Kandidat wird nach dem Tupel `(probe_rank, status_tier, host_prio, ping_ms)` sortiert:
   * **`probe_rank`:** `0` = im Live-Speedtest positiv geprüft (`🟢 ✅ [Geprüft]`), `1` = noch ungeprüft, `2` = im Speedtest oder zuvor gescheitert (`🔴 ❌ [Defekt]` / `[Fehlerhaft]`).
   * **`status_tier` & Ampel-Badge:**
     * `🟢` (Tier `0`): Ping `< 280 ms` und nicht fehlerhaft
     * `🟡` (Tier `1`): Ping `280–650 ms` oder Ping unbekannt (`None`)
     * `🔴` (Tier `2`): Ping `> 650 ms` oder in `stream_failures.json` als fehlerhaft markiert
   * **`host_prio` (`_HOSTER_PRIO`, Zeilen 414–417):**
     * Priorität `1`: `voe`, `vavoo`
     * Priorität `2`: `filemoon` (Standard-Qualitätslabel `1080p`), `streamwish`, `vidmoly`, `luluvdo`, `speedfiles`
     * Priorität `3`: `vidoza`, `streamtape`
     * Priorität `4`: `doodstream` / `dood`
     * Priorität `5`: sonstige Hoster
4. **Live-Speedtest der Top-5 (Menüeintrag `0`: `⚡ [Live-Speedtest: Top-5 Streams auflösen & echte Auflösung messen]`):**
   * Wählt die ersten 5 noch ungeprüften Kandidaten der sortierten Liste (`to_test = [c for c in ranked if "_probe_ok" not in c][:5]`).
   * Führt pro Kandidat `_test_with_probe(cand, limit=6)` (`6s` Timeout) aus: Löst den Hoster auf, lädt über `streamTest.probe()` die HLS-Master-Playlist bis zum ersten Videosegment, parst die reale Videoauflösung (`RESOLUTION=\d+x(\d+)` bzw. `NAME="(\d+)p"` → `4K`, `1080p`, `720p`, `480p`, Fallback `HD`) und misst die komplette End-to-End-Ladezeit in `ms`.
   * Sortiert die geprüften Streams mit `🟢 ✅ ... [Geprüft]` ganz nach oben und öffnet das Auswahlmenü erneut.
5. **Nahtloser Resume an derselben Sekunde (`_listitem` & `_play` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 824–826 & 863–876):**
   * Wurde `resume_time` übergeben, setzt `_listitem` sowohl `info_tag.setResumePoint(float(resume_time))` als auch `o.setProperty('StartOffset', str(float(resume_time)))`.
   * Zusätzlich überwacht `_play()` den neuen Stream nach `player.play(path, o)` für bis zu `8.0` Sekunden: Sobald `player.isPlayingVideo()` und `player.getTotalTime() > 0` erfüllt sind, prüft es `if player.getTime() < target - 5:` und erzwingt aktiv `player.seekTime(target)`, falls ein HLS-Hoster den `StartOffset` beim Initialisieren ignoriert hat.
   * Bricht man den Auswahldialog mit `Zurück` ab (`chosen < 0`, Zeile 574), hebt `select_and_play` die Pause des laufenden Videos automatisch wieder auf (`xbmc.Player().pause()`).
