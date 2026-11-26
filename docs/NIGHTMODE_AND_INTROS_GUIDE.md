# 🌙 Nachtmodus, ⏩ Intro-Skip & ⏱️ OSD-Timeline

> [!NOTE]
> Alle Abweichungen zwischen der früheren Kurz-Dokumentation und dem tatsächlichen Verhalten im Code sind in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md) zusammengefasst.

---

## 🧭 Funktions-Schnellindex

| Funktion | Auslöser | Kern-Dateien & Funktionen | Verhalten im Überblick |
| :--- | :--- | :--- | :--- |
| **[1. Intro überspringen (`Intro skip`)](#1-intro-berspringen-theintrodb--manuelles-skip-overlay)** | Automatische Einblendung während eines erkannten Intros; Bestätigung mit **Mitte / OK** | `tmdbhelper/.../monitor/player.py` → `_fetch_intro_segments()`<br>`service.upnext/.../skip.py` → `Skipper`, `SkipButton` | Fragt beim Episodenstart TheIntroDB v4 ab. Blendet während `[start, end - 1.0s)` unten rechts den vorfokussierten Button **`Intro skip`** (Control `3010`) ein. **Kein Auto-Skip** (`autoSkipIntro = false`). |
| **[2. Nachtmodus / Dialog-Booster (`🌙`)](#2-nachtmodus--dialog-booster-drc-per-1-klick)** | **OSD-Button `🌙`** (Control `6010`) + automatische Wiederherstellung bei Folgewechsel | `skin.arctic.fuse.2/shortcuts/toggle_nightmode.py`<br>`tmdbhelper/.../monitor/player.py` → `_apply_nightmode_if_active()` | Sendet 10× `Action(volampup)` (+10 dB Dialog-Anhebung mit Kodis Peak-Limiter) und setzt `Window(10000).Property(NightMode_Active)`. Wird bei jedem neuen Video automatisch erneut angewendet. |
| **[3. OSD-Header & Medien-Titel](#3-osd-header--medien-titel-label_osd_header)** | **Steuerkreuz Oben (`▲`)**, Pause oder Spulen | `skin.arctic.fuse.2/1080i/DialogSeekBar.xml` (Control `3099`)<br>`skin.arctic.fuse.2/1080i/Includes_Labels.xml` → `Label_OSD_Header`<br>`xstreamscraper/.../scraper.py` → `_listitem()` | Zeigt Status (Spulen/Puffer/Pause) und Medientitel über der Zeitleiste an. |
| **[4. Automatisches Ausblenden (5s / 2s Auto-Hide)](#4-automatisches-ausblenden-der-timeline-5s-osd-alarmclock--2s-seekbar)** | Automatisch nach `5s` (`VideoOSD.xml`) bzw. `2s` nach Spulen (`DialogSeekBar.xml`) | `skin.arctic.fuse.2/1080i/VideoOSD.xml`<br>`skin.arctic.fuse.2/shortcuts/builtins/skinvariables-closeosd.json`<br>`skin.arctic.fuse.2/1080i/DialogSeekBar.xml` | Schließt das mit `▲` geöffnete Video-OSD nach 5 Sek. via `AlarmClock(osd_timeout)`. Reine Spul-Zeitleiste schließt 2 Sek. nach dem letzten 10s-Sprung. |

---

## 1. ⏩ Intro überspringen (TheIntroDB & manuelles Skip-Overlay)

### Kurzüberblick & Bedienung
* Wenn für eine Serienfolge in **TheIntroDB** Intro-Zeitstempel hinterlegt sind, erscheint exakt zu Beginn des Intros unten rechts der Button **`Intro skip`** (bereits fokussiert).
* **Kein automatisches Überspringen:** Das Intro läuft normal weiter, solange du nichts drückst.
* **Mitte / OK drücken:** Springt sofort ans Ende des Intros (`player.seekTime(end)`).
* **Zurück-Taste drücken:** Schließt den Button für dieses Intro-Segment (`dismissed = True`), sodass er während desselben Intros nicht erneut aufpoppt.
* **Abwarten:** 1 Sekunde vor Ende des Intros (`END_MARGIN = 1.0`) blendet sich der Button von selbst wieder aus.

### Technischer Ablauf im Code
1. **Abruf der Intro-Segmente (`_fetch_intro_segments` in [`kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 526–599):**
   * Wird bei jedem Episodenstart in einem eigenen `SafeThread` aus `_queue_episodes_worker()` gestartet.
   * Sendet einen HTTP-GET-Request (Timeout `4.0s`, Header `User-Agent: Kodi-TMDbHelper/6.0`) an:
     ```text
     https://api.theintrodb.org/v4/media?tmdb_id={tmdb_id}&season={season}&episode={episode}
     ```
   * Validiert jedes Segment in `data.get('intro')` (Zeilen 542–561):
     * `end_ms` muss vorhanden sein; fehlt `start_ms`, wird `start_ms = 0` gesetzt.
     * Umrechnung in Sekunden: `start_sec = float(start_ms) / 1000.0`, `end_sec = float(end_ms) / 1000.0`.
     * **Gültigkeitsregeln:** `start_sec >= 0.0`, `end_sec > start_sec`, Mindestlänge **`(end_sec - start_sec) >= 3.0` Sekunden**, und (sofern `total_time > 0`) **`end_sec < (total_time - 2.0)`** (damit ein fehlerhaftes Segment nicht bis ans Episodenende springt).
   * Gültige Segmente werden als `{'kind': 'intro', 'start': start_sec, 'end': end_sec}` in `payload['skip_segments']` gepackt und Base64-kodiert per JSON-RPC `JSONRPC.NotifyAll` (`message: 'Other.upnext_data'`) an `service.upnext` geschickt.
2. **Überwachung & Einblendung in `service.upnext` ([`kodi/addons/service.upnext/resources/lib/skip.py`](../kodi/addons/service.upnext/resources/lib/skip.py)):**
   * `UpNextMonitor.run()` ([`monitor.py`](../kodi/addons/service.upnext/resources/lib/monitor.py), Zeile 128) ruft jede Sekunde `self.skipper.update(self.api.data, play_time)` auf.
   * `parse_segments(data)` sortiert alle Segmente mit `kind in ('intro', 'recap')` und `0 <= start < end` aufsteigend nach Startzeit.
   * `active_segment(segments, play_time)` prüft, ob die aktuelle Abspielzeit im Intervall **`start <= play_time < (end - 1.0)`** (`END_MARGIN = 1.0`) liegt.
   * Da in [`kodi/userdata/addon_data/service.upnext/settings.xml`](../kodi/userdata/addon_data/service.upnext/settings.xml) `enableSkipSegments = true` und `autoSkipIntro = false` gesetzt sind, öffnet `Skipper.update()` den nicht-modalen `WindowXMLDialog` **`SkipButton`** (`script-upnext-skip.xml`) mit dem deutschen Label **`Intro skip`** (String-ID `30052` in [`strings.po`](../kodi/addons/service.upnext/resources/language/resource.language.de_de/strings.po)).
3. **Aktion bei Tastendruck (`SkipButton`, Zeilen 55–84 & `Skipper.skip`, Zeilen 110–122):**
   * `onInit()` setzt den Fokus direkt auf Button-ID **`3010`**.
   * Bei Klick auf `3010` (`onClick`) prüft `Skipper.skip(segment)` zur Sicherheit noch einmal `now < segment[2] - 1.0` (verhindert Rückwärtssprünge, falls der Button offen blieb) und führt `self.player.seekTime(segment[2])` aus.
   * Das Segment wird in `self.handled` (Set) eingetragen, sodass der Button für dieses Segment nicht erneut erscheint.
   * Bei `ACTION_NAV_BACK (92)`, `ACTION_PREVIOUS_MENU (10)` oder `ACTION_STOP (13)` setzt `onAction()` `self.dismissed = True`, schließt den Button und markiert das Segment ebenfalls in `self.handled`.

### Parameter & Grenzwerte
| Parameter | Wert | Datei | Bedeutung |
| :--- | :--- | :--- | :--- |
| Mindestlänge Intro | `3.0s` | `tmdbhelper/.../monitor/player.py` (Zeile 556) | Segmente `< 3 Sek.` werden als Messfehler verworfen. |
| Abstand zum Episodenende | `2.0s` | `tmdbhelper/.../monitor/player.py` (Zeile 558) | `end_sec` muss mindestens 2 Sek. vor Videoende liegen. |
| `END_MARGIN` | `1.0s` | `service.upnext/.../skip.py` (Zeile 20) | In der letzten Sekunde des Intros wird kein Button mehr gezeigt/ausgeführt. |
| `enableSkipSegments` | `true` | `userdata/addon_data/service.upnext/settings.xml` | Aktiviert die Verarbeitung von `skip_segments`. |
| `autoSkipIntro` / `autoSkipRecap` | `false` | `userdata/addon_data/service.upnext/settings.xml` | Deaktiviert automatisches Springen; erfordert Bestätigung auf Button `3010`. |

---

## 2. 🌙 Nachtmodus / Dialog-Booster (DRC per 1-Klick)

### Kurzüberblick & Bedienung
* **Einschalten:** Während der Wiedergabe **Steuerkreuz Oben (`▲`)** drücken → unten rechts auf das **`🌙`-Symbol (Button `6010`)** klicken.
  * Es erscheint die Benachrichtigung: *„🌙 Nachtmodus: Aktiviert (+10 dB Dialog-Boost & DRC)“*.
  * Leise Dialoge werden um **+10 dB** angehoben, während Kodis interner Audio-Kompressor/Limiter laute Spitzen (Explosionen, Action) abfedert.
* **Ausschalten:** Erneuter Klick auf **`🌙` (Button `6010`)** setzt die Verstärkung wieder um `-10 dB` auf `0 dB` zurück (*„☀️ Normalmodus: Deaktiviert (0 dB Standard)“*).

### Technischer Ablauf im Code
1. **Toggle-Skript ([`kodi/addons/skin.arctic.fuse.2/shortcuts/toggle_nightmode.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/toggle_nightmode.py)):**
   * Prüft im Home-Window (`xbmcgui.Window(10000)`), ob `win.getProperty("NightMode_Active") == "true"` gesetzt ist.
   * **Wenn inaktiv:** Führt in einer Schleife **10-mal** `xbmc.executebuiltin("Action(volampup)")` aus (jeder Schritt erhöht Kodis Volume-Amplification um `+1.0 dB` → zusammen `+10.0 dB`), setzt `NightMode_Active = "true"` und zeigt ein 2,5-Sekunden-Notification-Toast.
   * **Wenn aktiv:** Führt **10-mal** `xbmc.executebuiltin("Action(volampdown)")` aus (`-10.0 dB` → zurück auf `0.0 dB`), setzt `NightMode_Active = "false"` und zeigt das Deaktivierungs-Toast.
2. **Automatische Persistenz über Episodenwechsel hinweg (`_apply_nightmode_if_active` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 474–482):**
   * Da Kodis Videoplayer die Volume-Amplification beim Laden eines neuen Streams standardmäßig auf `0 dB` zurücksetzt, ruft `PlayerMonitor.get_playingitem()` bei jedem neuen Videostart `_apply_nightmode_if_active()` auf.
   * Ist `Window(10000).getProperty("NightMode_Active") == "true"`, sendet der Monitor automatisch erneut **10-mal `Action(volampup)`**, sodass der Nachtmodus beim Binge-Watching einer Staffel nahtlos aktiv bleibt.

### Besonderheiten & Edge-Cases
* **OSD bleibt nach Klick auf `🌙` offen:** Button `6010` in [`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml) (Zeilen 203–208) führt `<onclick>CancelAlarm(osd_timeout,true)</onclick>` aus, schließt das OSD aber nicht selbst. Nach dem Umschalten des Nachtmodus schließt man das OSD daher mit einem Druck auf die **Zurück-Taste**.
* **Relativer Schrittzähler (`10× volampup/down`):** Da Kodi für `volamp` relative Step-Actions verwendet, sollte man den Lautstärke-Verstärkungsregler im Audio-Einstellungsdialog (`ActivateWindow(osdaudiosettings)`) nicht parallel von Hand verschieben, während `NightMode_Active` aktiv ist.
* **Session-Lebensdauer:** Das Property `NightMode_Active` liegt im RAM (`Window(10000)`). Nach einem kompletten Kodi-Neustart startet Kodi wieder im `0 dB` Normalmodus.

---

## 3. 📺 OSD-Header & Medien-Titel (`Label_OSD_Header`)

### Kurzüberblick & Bedienung
Sobald die Zeitleiste eingeblendet wird (über **Steuerkreuz Oben `▲`**, beim Pausieren oder beim Vor-/Zurückspulen), zeigt das Label links über dem Fortschrittsbalken (`Control 3099` in [`DialogSeekBar.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/DialogSeekBar.xml)) den aktuellen Wiedergabestatus und Medientitel an.

### Technischer Ablauf im Code ([`Includes_Labels.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Labels.xml), Zeilen 928–958)
Die Variable `Label_OSD_Header` wertet von oben nach unten folgende Prioritätskette aus:
1. **Aktive Sonderzustände (Zeilen 929–947):**
   * Kanalnummer-Eingabe, numerischer Zeitsprung, Vorspulen/Zurückspulen (`FF 2x`..`32x`, `RW 2x`..`32x`).
   * **Aktives Spulen (`Player.Seeking | Player.HasPerformedSeek(3)`):** Zeigt `Suche +00:10` bzw. `-00:10` (`$LOCALIZE[773]$INFO[Player.SeekOffset, ,]`) für 3 Sekunden nach einem Sprung.
   * **Puffern (`Player.Caching`):** Zeigt `Puffern [X]%`.
   * **Abweichende Abspielgeschwindigkeit (`Player.PlaySpeed != 1.00`):** Zeigt die Geschwindigkeit (z. B. `1.25x`).
2. **Pause-Zustand (`Player.Paused`, Zeilen 948–950):**
   * **Serien (`!String.IsEmpty(VideoPlayer.TVShowTitle)`):**
     `$LOCALIZE[112] • $INFO[VideoPlayer.TVShowTitle]$VAR[Label_OSD_Plot_Episode_Number, • ,]$INFO[VideoPlayer.Title, • ,]`
   * **Filme (`!String.IsEmpty(VideoPlayer.Title)`):**
     `Pause • [Filmtitel]`
3. **Normale Wiedergabe (Zeilen 951–957):**
   * **Live-TV mit Kanalnummer:** `Kanal [Nr] • [Sendungstitel]`
   * **Serien (wenn `TVShowTitle != Title`, Zeile 952):** `[Serientitel] • [Staffel]x[Folge] • [Episodentitel]`
   * **Serien (wenn `TVShowTitle == Title`, Zeile 953):** `[Serientitel] • [Staffel]x[Folge]`
   * **Filme (Zeile 954–955):** `[Filmtitel]` (`VideoPlayer.Title` bzw. `Player.Title`)
   * **Live-TV ohne Kanalnummer (Zeile 956):** `[Sendername] • [Sendungstitel]`

### Besonderheiten & Edge-Cases
* **Verhalten mit xStream Scraper:** In [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py) (`_listitem`, Zeilen 803–835) setzt der Scraper beim Start eines Streams sowohl `Title` als auch `TVShowTitle` auf den Seriennamen (`meta['title']`). Deshalb greift während der normalen Serienwiedergabe Zeile 953 (`[Serientitel] • [Staffel]x[Folge]`), während im Pause-Zustand (Zeile 948, wo der Ungleichheits-Check fehlt) `Pause • [Serientitel] • [Staffel]x[Folge] • [Serientitel]` steht.

---

## 4. ⏱️ Automatisches Ausblenden der Timeline (5s OSD-AlarmClock & 2s Seekbar)

### Kurzüberblick & Bedienung
* Öffnest du das vollständige OSD mit **Steuerkreuz Oben (`▲`)**, blendet es sich nach **5 Sekunden** automatisch wieder aus.
* Spulst du im Vollbild direkt mit **Steuerkreuz Links / Rechts (`◄` / `►`)**, erscheint nur der untere Zeitbalken ohne Button-Reihe und blendet sich bereits **2 Sekunden** nach dem letzten Sprung wieder aus.

### Technischer Ablauf im Code
1. **Vollständiges Video-OSD (5-Sekunden-Timer in [`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml), Zeilen 9–10):**
   * Beim Öffnen (`<onload>`) von `VideoOSD.xml` wird ein Kodi-`AlarmClock` namens `osd_timeout` mit einer Laufzeit von **`00:05` (5 Sekunden)** gestartet:
     ```xml
     <onload>AlarmClock(osd_timeout,RunScript(script.skinvariables,run_executebuiltin=special://skin/shortcuts/builtins/skinvariables-closeosd.json,use_rules=True),00:05,silent)</onload>
     <onunload>CancelAlarm(osd_timeout,true)</onunload>
     ```
   * Nach Ablauf der 5 Sekunden führt `script.skinvariables` die Datei [`skinvariables-closeosd.json`](../kodi/addons/skin.arctic.fuse.2/shortcuts/builtins/skinvariables-closeosd.json) aus, welche `Dialog.Close(...)` für `musicosd`, `videoosd` sowie die Dialog-IDs `1140` bis `1149` aufruft.
2. **Wann der 5-Sekunden-Timer läuft vs. abgebrochen wird:**
   * **Kein Reset bei reinem Links/Rechts auf den Hauptbuttons:** Der `AlarmClock(osd_timeout)` wird **nur beim `<onload>`** gesetzt. Ein bloßes Bewegen des Fokus zwischen Play (`6001`), Zurück (`6002`), Stop (`6004`), Stream-Wechsel (`6009`) und Nachtmodus (`6010`) startet den Timer nicht neu.
   * **Abbruch (`CancelAlarm`) bei Untermenüs:** Sobald man auf die Einstellungs-Buttons `6005` (Info → `Window 1145`), `6006` (Audio → `Window 1146`), `6007` (Untertitel → `Window 1147`), `6008` (Video → `Window 1148`), `6009` (Stream-Wechsel), `6010` (Nachtmodus) klickt oder mit `▼` in die Episoden-Schublade (`Window 1140`, Zeile 5: `<onload>CancelAlarm(osd_timeout,true)</onload>`) wechselt, wird der 5-Sekunden-Countdown abgebrochen, damit sich das Menü nicht während der Auswahl schließt.
3. **Reine Seekbar beim Spulen & Pausieren ([`DialogSeekBar.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/DialogSeekBar.xml), Zeile 6):**
   * `DialogSeekBar.xml` ist ein eigenständiges Overlay-Fenster, das automatisch sichtbar wird, sobald eine der folgenden Bedingungen in Zeile 6 zutrifft:
     * `Player.Seeking | Player.HasPerformedSeek(2)` (während des Spulens und für **2 Sekunden** danach)
     * `Player.Paused` (während Pause, sofern nicht `OSD.AutoOnPause = Hide` nach `Exp_OSD_DelayInfo_Timing` greift)
     * `Player.Caching | Player.Forwarding | Player.Rewinding`
     * oder solange `videoosd`, `1140`–`1149` bzw. das UpNext-Popup aktiv ist.
