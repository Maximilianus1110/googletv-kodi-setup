# 🔍 Abweichungen: Bisherige Dokumentation vs. Tatsächlicher Code

Diese Übersicht dokumentiert alle Stellen, an denen die **bisherige (allgemein gehaltene) Dokumentation** vom **tatsächlichen Verhalten im Code** bzw. von den real gesetzten Konfigurationsdateien in `kodi/` abwich.

---

## 📋 Schnellübersicht aller Abweichungen

| # | Funktion / Bereich | Aussage in der alten Doku | Tatsächliches Verhalten im Code | Status |
| :--- | :--- | :--- | :--- | :--- |
| **[1](#1-upnext-countdown-bei-erkanntem-abspann-credits--notification_offset)** | **UpNext-Wechsel bei Abspannbeginn** | „15 Sek. vor Ende (oder zu Beginn des Abspanns) erscheint der 15s-Countdown, danach startet sofort die nächste Folge.“ | Bei erkanntem Abspann (`notification_offset`) erschien der Button zwar zu Abspannbeginn, aber weil `autoPlayCreditsTime` auf `0` (Default) stand, wurde der Timer nur auf die gesamte Restlaufzeit gestreckt und erst bei **`0:00` (Episodenende)** gewechselt. | ✅ **Im Code behoben** (`autoPlayCreditsTime = 15` + Fallback in `api.py`) |
| **[2](#2-upnext-verhalten-ohne-abspann-daten-standard-15-sekunden)** | **UpNext ohne Abspann-Daten** | „Nächste Folge automatisch nach 15 Sek.“ | Das Popup wird **15 Sek. vor Videoende (`0:15`)** eingeblendet und zählt bis `total_time - play_time <= 1` (`0:01`/`0:00`) herunter. `player.playnext()` wird dabei nicht vorzeitig gerufen, sondern Kodi wechselt am regulären Dateiende (`0:00`) in der Playlist. | 📖 **In Doku präzisiert** |
| **[3](#3-osd-timeline-auto-hide-5-sekunden-timer-reset)** | **OSD-Timeline Auto-Hide (5s)** | „Jeder Tastendruck auf dem Steuerkreuz setzt den 5-Sekunden-Timer zurück.“ | `AlarmClock(osd_timeout, ..., 00:05)` startet **nur einmalig beim `<onload>`** von `VideoOSD.xml`. Links/Rechts-Navigation setzt den Timer **nicht** zurück; ein Klick auf `🌙 Nachtmodus` bricht den Timer per `CancelAlarm` sogar komplett ab (OSD bleibt offen). Reine Spul-Einblendung (`DialogSeekBar.xml`) blendet nach **2 Sek.** (`Player.HasPerformedSeek(2)`) aus. | 📖 **In Doku präzisiert** |
| **[4](#4-osd-header-serientitel--episodentitel)** | **OSD-Header bei Serien** | „Zeigt `[Serientitel] • [Staffel]x[Folge] • [Episodentitel]` (z. B. `My Name Is Earl • 1x01 • Pilot`).“ | `scraper.py` (`_listitem`) schreibt in `Title` und `TVShowTitle` denselben **Seriennamen**. Dadurch unterdrückt `Includes_Labels.xml` während der Wiedergabe den vermeintlichen Episodentitel (`[Serientitel] • 1x01`), während bei **Pause** die Duplikat-Prüfung fehlt und der Serienname **doppelt** erscheint (`Pause • [Serientitel] • 1x01 • [Serientitel]`). | 📖 **In Doku präzisiert** |
| **[5](#5-in-player-episoden-schublade-window-1140-mit-steuerkreuz-unten-)** | **Episoden-Schublade (`Window 1140`)** | „Du kannst horizontal durch alle Folgen der aktuellen Staffel blättern.“ | Solange eine aktive Playlist läuft, lädt `Path_OSD_Episodes` `playlistvideo://`. Da `PlayerNextEpisodes` nur zukünftige Folgen (`> E`) einreiht und `service.upnext` gespielte Folgen aus Position `0` löscht (`reset_queue`), zeigt die Schublade **nur die aktuelle + verbleibenden Folgen** (nicht bereits vergangene Folgen `1..E-1`). Bei Filmen schließt sich `1140` sofort und öffnet `Window 1141` (Cast). | 📖 **In Doku präzisiert** |
| **[6](#6-hintergrund-preloading-zeitpunkt-staffelende--manuelle-quellenwahl)** | **Hintergrund-Preloading (`pre_resolve`)** | „Nach ca. 8 Sekunden Laufzeit startet der Scraper für die nächste Folge.“ | Der Worker wartet zuerst `1s`, baut dann synchron die Staffel-Playlist auf (`1–3s`) und wartet danach `8s` (Start effektiv nach **9–12 Sek.**). Außerdem fragt er starr `episode + 1` derselben Staffel an (kein Staffelwechsel am Staffelfinale) und überschreibt das `make_playlist: false` von `xstream_select.json`. | 📖 **In Doku präzisiert** |
| **[7](#7-multi-source-stream-scraper-anzahl-quellen--zweistufige-suche)** | **xStream Scraper Quellen & Ablauf** | „Durchsucht automatisch 14 deutsche Streaming-Anbieter & VAVOO-Mirrors.“ | In `settings.xml` sind **12 xStream-Seiten + VAVOO** aktiviert (`kinoger`, `hdfilme`, `burningseries`, `internetarchive`, `api_sites` sind `false`). Zudem sucht Auto-Play **zweistufig**: Bei Serien zuerst **nur** `serienstream` (nur `(DE)`), bei Filmen zuerst **nur** `vavoo`. Erst wenn dort kein ungespielter Stream läuft, werden die übrigen Seiten abgefragt. | 📖 **In Doku präzisiert** |
| **[8](#8-trakt-scrobbling-gesehen-schwelle-80--statt-85-)** | **Trakt Gesehen-Schwelle** | „Wenn du eine Folge zu Ende geschaut hast (über 85 %), markiert Trakt diese als Gesehen.“ | Die Schwelle im Code (`player.py` & `scrobbler.py`) liegt bei **exakt 80 %** (`>= 0.8`), nicht 85 %. Für lokale Kodi-Bibliothekseinträge gilt intern 90 %, was `service.upnext` über `markWatchedEarly` (10s nach Episodenwechsel) ausgleicht. | 📖 **In Doku präzisiert** |
| **[9](#9-erwachsenenbereich-18--adulthideout-long-press-10s-root-timeout--quellenanzahl)** | **+18 Bereich (Long-Press & 5-Min-Session)** | „5 Sek. Zurück-Taste drücken. Danach 5 Minuten frei durch 306 Quellen navigieren ohne erneute PIN.“ | 1) Kodi `mod="longpress"` löst nach **ca. 0,5–1,5 Sek.** aus (nicht 5 Sek.).<br>2) `open_adult.py` fragt **immer** den PIN ab.<br>3) In `default.py` gilt `300s` (5 Min.) **nur in Untermenüs** (`mode=...`); für das Hauptmenü (`is_root`) beträgt das Fenster **nur `10.0` Sekunden**!<br>4) Von 306 Seiten sind 11 ab Werk deaktiviert und 1 Opt-In (**294 aktive Seiten**). | 📖 **In Doku präzisiert** |
| **[10](#10-youtube-widgets-auf-der-startseite--login-url)** | **YouTube-Startseiten-Widgets** | „Auf der Startseite stehen 4 Reihen bereit: Vorschläge, Trends, Abonnements, Wiedergabeverlauf.“ | Auf der Haupt-Startseite (`Entdecken`) sind nur **2 YouTube-Reihen** (`Vorschläge` & `Trends`) eingebunden. `Meine Abonnements` existiert nur im Unterbereich `YouTube & SmartTube`; ein Widget `Wiedergabeverlauf` ist gar nicht als Startseiten-Widget konfiguriert. | 📖 **In Doku präzisiert** |
| **[11](#11-nachtmodus-persistenz--relativer-10x-pegel-zhler)** | **Nachtmodus (`🌙`)** | „Schaltet +10 dB Dialog-Boost und Peak-Limiter per 1-Klick ein/aus.“ | Sendet 10-mal `Action(volampup)` bzw. `Action(volampdown)` und speichert `NightMode_Active` in `Window(10000)`. Beim Episodenwechsel setzt Kodi `volamp` zurück, weshalb `PlayerMonitor._apply_nightmode_if_active()` bei jedem neuen Video erneut 10x `Action(volampup)` sendet. | 📖 **In Doku präzisiert** |

---

## 🔬 Detailanalyse der einzelnen Abweichungen

### 1. UpNext-Countdown bei erkanntem Abspann (`credits` / `notification_offset`)

* **Alte Aussage:**
  > „15 Sekunden vor Episodenende (oder exakt zu Beginn des Abspanns, falls TheIntroDB `credits`-Zeiten geliefert hat) erscheint unten rechts das UpNext-Popup... Läuft der Countdown ab, startet direkt die nächste Folge.“
* **Was im Code vor dem Fix wirklich passierte:**
  1. `PlayerMonitor._fetch_intro_segments()` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) liest das `credits`-Array von `https://api.theintrodb.org/v4/media` aus. Liegt `start_ms > 60000` und `total_time * 0.70 <= credits_start < total_time - 5.0`, wird `payload['notification_offset'] = int(credits_start)` per JSON-RPC (`Other.upnext_data`) an `service.upnext` gesendet.
  2. In [`api.py`](../kodi/addons/service.upnext/resources/lib/api.py) berechnet `Api.notification_time()` bei vorhandenem `notification_offset` den Auslösezeitpunkt als `total_time - int(notification_offset)`. Das Popup öffnete sich also tatsächlich exakt zu Beginn des Abspanns (z. B. 75 Sekunden vor Episodenende).
  3. In [`playbackmanager.py`](../kodi/addons/service.upnext/resources/lib/playbackmanager.py) prüft `show_popup_and_wait()` jedoch `credits_autoplay_deadline(data, play_time, total_time)`. Diese Funktion las `delay = get_setting_int('autoPlayCreditsTime')` aus.
  4. Da `autoPlayCreditsTime` in [`kodi/userdata/addon_data/service.upnext/settings.xml`](../kodi/userdata/addon_data/service.upnext/settings.xml) fehlte und in [`kodi/addons/service.upnext/resources/settings.xml`](../kodi/addons/service.upnext/resources/settings.xml) mit `default="0"` definiert war, war `delay == 0` und `credits_autoplay_deadline()` gab `None` zurück.
  5. Ohne `credits_deadline` zählte das Popup einfach `remaining = total_time - play_time` (also z. B. 75 Sekunden) bis `0:00` herunter und löste kein vorzeitiges `self.player.playnext()` aus.
* **Durchgeführte Code-Änderung:**
  * In beiden `settings.xml`-Dateien von `service.upnext` ist `autoPlayCreditsTime` nun auf `15` Sekunden gesetzt.
  * In [`api.py`](../kodi/addons/service.upnext/resources/lib/api.py) fällt `credits_autoplay_deadline()` bei `delay <= 0` automatisch auf `get_setting_int('autoPlaySeasonTime') or 15` zurück.
  * Sobald der Abspann beginnt, läuft nun ein echter **15-Sekunden-Countdown** (`credits_deadline = min(total_time, max(play_time, offset) + 15)`), nach dessen Ablauf `next_up_page.set_auto_advance()` gesetzt und sofort `self.player.playnext()` aufgerufen wird.

---

### 2. UpNext-Verhalten ohne Abspann-Daten (Standard 15 Sekunden)

* **Alte Aussage:**
  > „Nächste Folge automatisch nach 15 Sekunden.“
* **Was im Code wirklich passiert:**
  * Hat TheIntroDB **keinen** Abspann-Zeitstempel für die Episode, bestimmt `Api.notification_time()` in [`api.py`](../kodi/addons/service.upnext/resources/lib/api.py) die Einblendzeit anhand der Episodenlänge (`autoPlayTimeXS` bis `autoPlayTimeXL`, in [`settings.xml`](../kodi/userdata/addon_data/service.upnext/settings.xml) alle auf `15` gesetzt).
  * Das UpNext-Popup (mit dem vorfokussierten Button **„Abspielen“**, Control `3012`) wird also **15 Sekunden vor dem regulären Ende der Videodatei** (`total_time - play_time <= 15`) eingeblendet.
  * Wenn der Nutzer nichts drückt, läuft die Wiedergabe bis `total_time - play_time <= 1` (also bis fast `0:00`), das Popup schließt sich und Kodis interne Video-Playlist wechselt bei Dateiende (`0:00`) automatisch auf den nächsten Playlist-Eintrag.

---

### 3. OSD-Timeline Auto-Hide (5-Sekunden-Timer Reset)

* **Alte Aussage (`docs/NIGHTMODE_AND_INTROS_GUIDE.md`):**
  > „Nach genau 5 Sekunden ohne Tastendruck verschwindet die Timeline und die Menüleiste automatisch... Jeder Tastendruck auf dem Steuerkreuz setzt den 5-Sekunden-Timer zurück.“
* **Was im Code wirklich passiert:**
  * **Kein Reset bei Links/Rechts-Navigation im OSD:** In [`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml) (Zeile 9) wird lediglich beim Öffnen des Fensters (`<onload>`) einmalig folgender Timer gestartet:
    ```xml
    <onload>AlarmClock(osd_timeout,RunScript(script.skinvariables,run_executebuiltin=special://skin/shortcuts/builtins/skinvariables-closeosd.json,use_rules=True),00:05,silent)</onload>
    ```
    Weder die Buttons `6001`–`6004` noch `6009`–`6010` haben ein `<onfocus>`, das den `AlarmClock(osd_timeout)` neu startet. Bewegt man das Steuerkreuz nur nach links oder rechts zwischen Play, Stop, Stream-Wechsel und Nachtmodus, schließt sich das OSD trotzdem exakt **5 Sekunden nach dem Öffnen**.
  * **Timer-Abbruch bei Untermenüs & Nachtmodus:** Die rechten Buttons `6005` (Info), `6006` (Audio), `6007` (Untertitel), `6008` (Video) öffnen beim Fokussieren (`<onfocus>`) Unterfenster (`1145`–`1148`) und brechen bei `<onclick>` den Timer mit `CancelAlarm(osd_timeout,true)` ab. Auch ein Klick auf Button `6010` (`🌙 Nachtmodus`) führt `<onclick>CancelAlarm(osd_timeout,true)</onclick>` aus, startet danach aber keinen neuen Timer – nach dem Umschalten des Nachtmodus bleibt das OSD also offen, bis man `Zurück` drückt.
  * **Reine Seekbar beim Spulen (2 Sekunden statt 5 Sekunden):** Spult man während des Videos mit Steuerkreuz Links/Rechts (`StepBack`/`StepForward`), öffnet sich nicht `VideoOSD.xml`, sondern nur [`DialogSeekBar.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/DialogSeekBar.xml). Dessen Sichtbarkeit wird in Zeile 6 über `Player.HasPerformedSeek(2)` gesteuert – der Zeitbalken verschwindet beim Spulen also bereits nach **2 Sekunden**.

---

### 4. OSD-Header: Serientitel & Episodentitel

* **Alte Aussage (`docs/NIGHTMODE_AND_INTROS_GUIDE.md`):**
  > „Serien: `[Serientitel] • [Staffel]x[Folge] • [Episodentitel]` (z. B. `My Name Is Earl • 1x01 • Pilot`)“  
  > „Bei Pause: `Pause • [Titel]`“
* **Was im Code wirklich passiert:**
  * In [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py) (`_search_and_play`, Zeile 725 & `_listitem`, Zeilen 803–834) übergibt der xStream Scraper als `meta['title']` immer den **Seriennamen** (`data["name"]`) und setzt sowohl `info_tag.setTitle(meta['title'])` als auch `info_tag.setTvShowTitle(meta['title'])` auf diesen Seriennamen.
  * In [`Includes_Labels.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Labels.xml) (Zeilen 948–953) wertet `Label_OSD_Header` folgende Bedingungen aus:
    * **Während der Wiedergabe (Zeile 952–953):** Zeile 952 verlangt `!String.IsEqual(VideoPlayer.TVShowTitle,VideoPlayer.Title)`. Da beide Felder beim Scraper-Start den Seriennamen tragen, greift Zeile 953 und zeigt nur **`[Serientitel] • [Staffel]x[Folge]`** (ohne Episodentitel).
    * **Während Pause (Zeile 948):** In `<value condition="Player.Paused + !String.IsEmpty(VideoPlayer.TVShowTitle)">` fehlt die Abfrage `!String.IsEqual(VideoPlayer.TVShowTitle,VideoPlayer.Title)`. Dadurch wird bei Pause **`Pause • [Serientitel] • [Staffel]x[Folge] • [Serientitel]`** angezeigt.

---

### 5. In-Player Episoden-Schublade (`Window 1140`) mit Steuerkreuz Unten (`▼`)

* **Alte Aussage (`docs/AUTOPLAY_AND_STREAM_SELECT.md`):**
  > „Es öffnet sich direkt von unten die Staffel-Episoden-Schublade (Window 1140). Du kannst horizontal durch alle Folgen der aktuellen Staffel blättern...“
* **Was im Code wirklich passiert:**
  * **Nur verbleibende Playlist-Folgen statt kompletter Staffel:** In [`Custom_1140_OSD_Playlist.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml) (Zeile 41) wird als Datenquelle `$VAR[Path_OSD_Episodes]` geladen. In [`Includes_Paths.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Paths.xml) (Zeile 266) hat folgende Bedingung höchste Priorität:
    ```xml
    <value condition="!Integer.IsEqual(VideoPlayer.PlaylistLength,1) + !Integer.IsEqual(VideoPlayer.PlaylistLength,0) + Integer.IsLess(VideoPlayer.PlaylistPosition,VideoPlayer.PlaylistLength)">playlistvideo://?reload=...</value>
    ```
    Da `PlayerNextEpisodes` ([`episodes.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/player/action/episodes.py), Zeile 74: `is_future_episode`) nur Episoden mit `e_number > self.episode` zur aktuellen Folge in die Video-Playlist einreiht (und `service.upnext` über `reset_queue()` bereits gesehene Folgen von Position `0` entfernt), enthält `playlistvideo://` **nur die aktuell laufende sowie die nachfolgenden Folgen der Staffel**. Bereits vorherige Folgen der Staffel (z. B. Folge 1–3, wenn man Folge 4 gestartet hat) erscheinen nicht in der Schublade, solange die Playlist aktiv ist.
  * **Automatischer Wechsel auf Cast/Besetzung (`Window 1141`) bei Filmen:** In [`Custom_1140_OSD_Playlist.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Custom_1140_OSD_Playlist.xml) (Zeilen 6–7) schließt sich `Window 1140` sofort selbst, wenn `$EXP[Exp_OSD_HasPlaylist]` falsch ist (bei Einzel-Filmen), und ruft stattdessen `ActivateWindow(1141)` (Schauspieler/Besetzung des Films) auf.

---

### 6. Hintergrund-Preloading: Zeitpunkt, Staffelende & manuelle Quellenwahl

* **Alte Aussage (`docs/AUTOPLAY_AND_STREAM_SELECT.md`):**
  > „Nach ca. 8 Sekunden Laufzeit der aktuellen Folge startet im Hintergrund der Scraper für die nächste Folge (N+1)...“
* **Was im Code wirklich passiert:**
  * **Tatsächliche Verzögerung (ca. 9–12 Sekunden):** In [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) (`_queue_episodes_worker`, Zeilen 492–522) wartet der Thread nach `onAVStarted` zunächst `1` Sekunde (`m.waitForAbort(1)`), führt danach synchron `PlayerNextEpisodes.update()` aus (TMDb-Metadatenabruf + Listenerstellung für alle restlichen Staffelfolgen, Dauer ca. 1–3 Sekunden) und wartet erst **danach** weitere `8` Sekunden (`m.waitForAbort(8)`), bevor `RunPlugin(plugin://script.module.xstreamscraper/?id=...&episode={int(episode)+1}&preload=true)` aufgerufen wird.
  * **Kein Staffelübergang beim Preloading:** Der Aufruf inkrementiert starr `int(episode) + 1` bei gleichbleibender `season`. Läuft das Staffelfinale (z. B. `S01E10`), sucht `pre_resolve` nach `S01E11` (existiert nicht) statt nach `S02E01`.
  * **Autoplay-Queueing auch bei manueller Quellenwahl:** In [`xstream_select.json`](../kodi/userdata/addon_data/plugin.video.themoviedb.helper/players/xstream_select.json) steht zwar `"make_playlist": "false"`, aber `PlayerMonitor._queue_episodes_worker()` prüft bei jedem Episodenstart unabhängig vom gewählten Player `if playlist.size() <= 1:` und reiht die restlichen Folgen trotzdem mit `player='xstream.json'` in die Video-Playlist ein.

---

### 7. Multi-Source Stream-Scraper: Anzahl Quellen & zweistufige Suche

* **Alte Aussage (`README.md` & `docs/AUTOPLAY_AND_STREAM_SELECT.md`):**
  > „xStream Scraper durchsucht automatisch 14 deutsche Streaming-Anbieter & VAVOO-Mirrors.“  
  > Beispiel in Doku: `🟢 ✅ 1. [Filemoon • 1080p • 140ms] Kinoger [Geprüft]`
* **Was im Code wirklich passiert:**
  * **Aktivierte Seiten in [`settings.xml`](../kodi/userdata/addon_data/script.module.xstreamscraper/settings.xml):** Es sind **12 xStream-Seiten** (`filmo`, `streamcloud`, `netzkino`, `kellerkino`, `movie2k`, `megakino`, `animetoast`, `moflix-stream`, `serienstream`, `aniworld`, `filmpalast`, `einschalten`) sowie **VAVOO** (`vavoo=true`) aktiviert. Die 5 Anbieter `kinoger`, `hdfilme`, `burningseries`, `internetarchive` und `api_sites` sind in der vorkonfigurierten `settings.xml` auf `false` gesetzt (und `serienstream` wird bei Filmen in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py) Zeile 225 übersprungen).
  * **Zweistufige Prioritätssuche statt sofortiger Parallelsuche über alle Seiten:**
    * **Bei Serien (`PRIORITY_SITE = "serienstream"`):** In `_search_and_play()` ([`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 762–778) wird im 1. Schritt **ausschließlich `serienstream`** durchsucht (und in `get_hosters` Zeile 173 strikt auf `languageCode == "(DE)"` gefiltert). Sobald dort ein funktionierender Stream gefunden wird, startet das Video sofort – die anderen 11 Seiten und VAVOO werden dann überhaupt nicht abgefragt.
    * **Bei Filmen:** Im 1. Schritt werden **ausschließlich die VAVOO-Mirrors** (`_vavoo_mirrors`) getestet. Erst wenn kein VAVOO-Mirror funktioniert, startet die globale Suche über die 11 Film-Seiten.
    * **Nur bei manueller Quellenwahl (`select_and_play`):** Hier werden tatsächlich sofort VAVOO-Mirrors + alle aktivierten Seiten parallel gesammelt.

---

### 8. Trakt-Scrobbling: Gesehen-Schwelle (80 % statt 85 %)

* **Alte Aussage (`docs/TRAKT_SETUP.md`):**
  > „Wenn du eine Folge zu Ende geschaut hast (über 85 %), markiert Trakt diese Folge als ‚Gesehen‘...“
* **Was im Code wirklich passiert:**
  * Sowohl in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) (`scrobbler_sync`, Zeile 277: `if (self.getTime() / self.getTotalTime()) < 0.8: return`) als auch in [`scrobbler.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/scrobbler.py) (Zeilen 149, 164, 176: `self.progress < 80` bzw. `self.progress >= 80`) liegt die Schwelle bei **exakt 80 %**.

---

### 9. Erwachsenenbereich (+18 / `AdultHideout`): Long-Press, 10s-Root-Timeout & Quellenanzahl

* **Alte Aussage (`README.md`, `docs/ADULT_SETUP.md`, `docs/REMOTE_CONTROLS.md`):**
  > „Schnellaufruf durch 5 Sekunden langes Drücken der Zurück-Taste (Long-Press Back).“  
  > „Sobald du den PIN `0000` korrekt eingegeben hast, wird im Arbeitsspeicher ein Sitzungs-Token für 300 Sekunden (5 Minuten) hinterlegt. Während dieser Zeit kannst du frei durch alle 306 Kategorien, Kanäle und Genres navigieren, ohne den PIN jedes Mal neu eingeben zu müssen.“
* **Was im Code wirklich passiert:**
  1. **Long-Press dauert ~0,5–1,5 Sek. statt 5 Sek.:** [`secret_remote.xml`](../kodi/userdata/keymaps/secret_remote.xml) bindet `<back mod="longpress">RunScript(special://skin/shortcuts/open_adult.py)</back>`. Kodis interner Long-Press-Timer löst nach ca. 0,5 bis 1,5 Sekunden Haltezeit aus.
  2. **Shortcut/Menüpunkt erzwingt immer neue PIN-Eingabe:** [`open_adult.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/open_adult.py) liest das Sitzungs-Property `adulthideout_auth_ts` nicht aus, sondern öffnet bei jedem Aufruf sofort `dialog.numeric(0, "PIN eingeben (0000)")`.
  3. **Hauptmenü-Timeout beträgt nur 10 Sekunden (`10.0s` vs. `300.0s`):** In [`kodi/addons/plugin.video.adulthideout/default.py`](../kodi/addons/plugin.video.adulthideout/default.py) (Zeilen 1007–1014) unterscheidet `handle_routing()` zwischen dem Hauptverzeichnis (`is_root`, kein `mode=` in `sys.argv[2]`) und Untermenüs:
     ```python
     is_root = (not raw_query or raw_query == '?' or 'mode=' not in raw_query)
     allowed_window = 10.0 if is_root else 300.0
     ```
     Das 5-Minuten-Fenster (`300.0` Sek.) gilt also **nur beim Navigieren innerhalb von Untermenüs** (`mode=...`). Kehrt man nach mehr als **10 Sekunden** auf die oberste Ebene (`plugin://plugin.video.adulthideout/`) zurück, verlangt `default.py` sofort wieder den PIN `0000`.
  4. **294 statt 306 aktive Seiten:** Von 306 Website-Skripten sind in [`default.py`](../kodi/addons/plugin.video.adulthideout/default.py) (Zeilen 39–56) 11 Seiten über `FACTORY_DISABLED_MIGRATION_WEBSITES` deaktiviert und `crazyshit` hinter einem Opt-In-Setting verborgen.

---

### 10. YouTube-Widgets auf der Startseite & Login-URL

* **Alte Aussage (`docs/YOUTUBE_SETUP.md`):**
  > „Sobald dein Konto verbunden ist, stehen dir folgende Reihen auf der Startseite zur Verfügung: ⭐ Meine YouTube Vorschläge, 🔥 YouTube Trends, 🔔 Meine Abonnements, 🕒 Wiedergabeverlauf.“
* **Was im Code wirklich passiert:**
  * In [`skinvariables-shortcut-homemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-homemenu.json) (Zeilen 50–62) und [`skinvariables-shortcut-sidemenu.json`](../kodi/userdata/addon_data/script.skinvariables/nodes/skin.arctic.fuse.2/skinvariables-shortcut-sidemenu.json) (Zeilen 44–56) sind unter **Entdecken / Start & Trends** nur **2 YouTube-Widgets** definiert:
    1. `⭐ Meine YouTube Vorschläge` (`plugin://plugin.video.youtube/special/recommendations/` -> intern `FEwhat_to_watch`)
    2. `🔥 YouTube Trends` (`plugin://plugin.video.youtube/special/popular_right_now/`)
  * Das Widget `🔔 Meine Abonnements` (`special/my_subscriptions/`) ist **nur** unter dem eigenen Seitenleisten-Menüpunkt **„YouTube & SmartTube“** eingebunden.
  * Ein Widget **„🕒 Wiedergabeverlauf“** ist in den Skin-Shortcuts überhaupt nicht als Widget angelegt (nur innerhalb des geöffneten YouTube-Add-ons abrufbar).

---

### 11. Nachtmodus: Persistenz & relativer 10x-Pegel-Zähler

* **Alte Aussage (`docs/NIGHTMODE_AND_INTROS_GUIDE.md`):**
  > „Ein Klick auf das 🌙-Symbol schaltet den Nachtmodus ein (+10 dB Dialog-Boost)... Ein erneuter Klick schaltet zurück in den 0 dB Standardmodus.“
* **Was im Code wirklich passiert:**
  * [`toggle_nightmode.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/toggle_nightmode.py) setzt keinen absoluten dB-Wert per JSON-RPC, sondern sendet in einer Schleife 10-mal das relative Kommando `xbmc.executebuiltin("Action(volampup)")` (bzw. beim Ausschalten 10-mal `Action(volampdown)`) und merkt sich den Zustand in `Window(10000).setProperty("NightMode_Active", "true" / "false")`.
  * Da Kodis Videoplayer die Volume-Amplification für jeden neuen Stream auf `0 dB` zurücksetzt, prüft [`PlayerMonitor._apply_nightmode_if_active()`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py) (Zeilen 474–482) bei jedem `get_playingitem()` (also auch beim automatischen Wechsel zur nächsten Folge), ob `NightMode_Active == "true"` ist, und sendet automatisch erneut 10-mal `Action(volampup)`.
