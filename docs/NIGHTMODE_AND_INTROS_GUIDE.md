# 🌙 Nachtmodus, ⏩ Intro-Skip & ⏱️ OSD-Timeline

> [!NOTE]
> Eine Übersicht aller behobenen Abweichungen zwischen früherer Doku und aktuellem Code findest du in [**`docs/ABWEICHUNGEN_ALT_VS_CODE.md`**](ABWEICHUNGEN_ALT_VS_CODE.md).

---

## 🧭 Funktions-Schnellindex

| Funktion | Auslöser | Kern-Dateien & Funktionen | Verhalten im Überblick |
| :--- | :--- | :--- | :--- |
| **[1. Intro überspringen (`Intro skip`)](#1-intro-berspringen-theintrodb--manuelles-skip-overlay)** | Automatische Einblendung während eines erkannten Intros; Bestätigung mit **Mitte / OK** | `tmdbhelper/.../monitor/player.py` → `_fetch_intro_segments()`<br>`service.upnext/.../skip.py` → `Skipper`, `SkipButton` | Fragt beim Episodenstart (auch nach Staffelwechsel) TheIntroDB v4 ab. Blendet während `[start, end - 1.0s)` unten rechts den vorfokussierten Button **`Intro skip`** (Control `3010`) ein. **Kein Auto-Skip** (`autoSkipIntro = false`). |
| **[2. Nachtmodus / Dialog-Booster (`🌙`)](#2-nachtmodus--dialog-booster-drc-per-1-klick)** | **OSD-Button `🌙`** (Control `6010`) + aktive OSD-Markierung + Episoden-Persistenz | `skin.arctic.fuse.2/shortcuts/toggle_nightmode.py`<br>`skin.arctic.fuse.2/1080i/VideoOSD.xml`, `Includes_OSD.xml`, `Includes_Labels.xml`<br>`tmdbhelper/.../monitor/player.py` → `_apply_nightmode_if_active()` | Sendet 10× `Action(volampup)` (+10 dB Dialog-Anhebung), markiert Button `6010` bei aktivem Nachtmodus im OSD mit **`AN`-Badge, `$VAR[ColorHighlight]`-Icon & Kreis-Ring** und schließt das OSD nach 5 Sek. automatisch. |
| **[3. OSD-Header mit echtem Episodentitel](#3-osd-header--echter-episodentitel-label_osd_header)** | **Steuerkreuz Oben (`▲`)**, Pause oder Spulen | `xstreamscraper/.../scraper.py` → `get_episode_title()`, `_listitem()`<br>`skin.arctic.fuse.2/1080i/DialogSeekBar.xml` (Control `3099`)<br>`skin.arctic.fuse.2/1080i/Includes_Labels.xml` → `Label_OSD_Header` | Lädt bei Serien den echten deutschen Episodentitel von TMDb und zeigt `[Serientitel] • [Staffel]x[Folge] • [Episodentitel]` (bzw. bei Pause `Pause • ...` ohne Titel-Dopplung). |
| **[4. Automatisches Ausblenden (5s / 2s Auto-Hide)](#4-automatisches-ausblenden-der-timeline-5s-osd-timer-mit-reset--2s-seekbar)** | Automatisch `5s` nach letzter OSD-Aktion (`VideoOSD.xml`) bzw. `2s` nach Spulen (`DialogSeekBar.xml`) | `skin.arctic.fuse.2/1080i/VideoOSD.xml`<br>`skin.arctic.fuse.2/1080i/Includes_Actions.xml` → `Action_OSD_Button`<br>`skin.arctic.fuse.2/1080i/DialogSeekBar.xml` | Jeder Fokuswechsel (`<onfocus>`) oder Klick (`<onclick>`) auf die OSD-Buttons/Slider setzt den 5-Sekunden-`AlarmClock(osd_timeout)` zurück. Reine Spul-Zeitleiste blendet 2 Sek. nach dem letzten 10s-Sprung aus. |

---

## 1. ⏩ Intro überspringen (TheIntroDB & manuelles Skip-Overlay)

### Kurzüberblick & Bedienung
* Wenn für eine Serienfolge in **TheIntroDB** Intro-Zeitstempel hinterlegt sind, erscheint exakt zu Beginn des Intros unten rechts der Button **`Intro skip`** (bereits fokussiert).
* **Kein automatisches Überspringen:** Das Intro läuft normal weiter, solange du nichts drückst.
* **Mitte / OK drücken:** Springt sofort ans Ende des Intros (`player.seekTime(end)`).
* **Zurück-Taste drücken:** Schließt den Button für dieses Intro-Segment (`dismissed = True`), sodass er während desselben Intros nicht erneut aufpoppt.
* **Abwarten:** 1 Sekunde vor Ende des Intros (`END_MARGIN = 1.0`) blendet sich der Button von selbst wieder aus.

### Technischer Ablauf im Code
1. **Abruf der Intro-Segmente (`_fetch_intro_segments` in [`kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 588–682):**
   * Wird bei jedem Episodenstart (auch nach einem automatischen Staffelwechsel auf `S+1, E01`) in einem eigenen `SafeThread` aus `_queue_episodes_worker()` gestartet.
   * Sendet einen HTTP-GET-Request (Timeout `4.0s`, Header `User-Agent: Kodi-TMDbHelper/6.0`) an:
     ```text
     https://api.theintrodb.org/v4/media?tmdb_id={tmdb_id}&season={season}&episode={episode}
     ```
   * Validiert jedes Segment in `data.get('intro')`:
     * `end_ms` muss vorhanden sein; fehlt `start_ms`, wird `start_ms = 0` gesetzt.
     * Umrechnung in Sekunden: `start_sec = float(start_ms) / 1000.0`, `end_sec = float(end_ms) / 1000.0`.
     * **Gültigkeitsregeln:** `start_sec >= 0.0`, `end_sec > start_sec`, Mindestlänge **`(end_sec - start_sec) >= 3.0` Sekunden**, und (sofern `total_time > 0`) **`end_sec < (total_time - 2.0)`**.
   * Nach Synchronisation mit `_queue_episodes_worker()` (`playlist_ready.wait(timeout=6.0)`) wird das Payload-Objekt (`current_episode`, `next_episode`, `play_url`, `skip_segments`, `notification_offset`) Base64-kodiert per JSON-RPC `JSONRPC.NotifyAll` (`message: 'Other.upnext_data'`) an `service.upnext` geschickt.
2. **Überwachung & Einblendung in `service.upnext` ([`kodi/addons/service.upnext/resources/lib/skip.py`](../kodi/addons/service.upnext/resources/lib/skip.py)):**
   * `UpNextMonitor.run()` ([`monitor.py`](../kodi/addons/service.upnext/resources/lib/monitor.py), Zeile 128) ruft jede Sekunde `self.skipper.update(self.api.data, play_time)` auf.
   * `active_segment(segments, play_time)` prüft, ob die aktuelle Abspielzeit im Intervall **`start <= play_time < (end - 1.0)`** (`END_MARGIN = 1.0`) liegt.
   * Da `enableSkipSegments = true` und `autoSkipIntro = false` gesetzt sind, öffnet `Skipper.update()` den nicht-modalen `WindowXMLDialog` **`SkipButton`** (`script-upnext-skip.xml`) mit dem deutschen Label **`Intro skip`** (Control-ID **`3010`**).
3. **Aktion bei Tastendruck (`SkipButton`, Zeilen 55–84 & `Skipper.skip`, Zeilen 110–122):**
   * Bei Klick auf `3010` prüft `Skipper.skip(segment)` `now < segment[2] - 1.0` und führt `self.player.seekTime(segment[2])` aus.
   * Das Segment wird in `self.handled` gespeichert, sodass der Button für dieses Intro nicht erneut erscheint.

---

## 2. 🌙 Nachtmodus / Dialog-Booster (DRC per 1-Klick & aktive OSD-Markierung)

### Kurzüberblick & Bedienung
* **Ein-/Ausschalten:** Während der Wiedergabe **Steuerkreuz Oben (`▲`)** drücken → unten rechts auf das **`🌙`-Symbol (Button `6010`)** klicken.
  * **Ein:** *„🌙 Nachtmodus: Aktiviert (+10 dB Dialog-Boost & DRC)“* – hebt leise Stimmen um **+10 dB** an und begrenzt laute Effekte über Kodis Audio-Limiter.
  * **Visuelle Markierung wenn „An“:** Solange der Nachtmodus aktiv ist (`Window(Home).Property(NightMode_Active) == true`), ist Button `6010` im OSD dauerhaft hervorgehoben: Das Mond-Icon leuchtet in der Skin-Akzentfarbe (`$VAR[ColorHighlight]`), darunter steht das Badge **`AN`** (`$VAR[Label_OSD_NightMode_Badge]`), und auch wenn der Fokus auf einem anderen Button liegt, bleibt der Button durch einen halbtransparenten Kreis (`common/circle.png`, `colordiffuse="33ffffff"`) als aktiv markiert.
  * **Aus:** *„☀️ Normalmodus: Deaktiviert (0 dB Standard)“* – senkt die Verstärkung wieder um `-10 dB` auf `0 dB` ab und entfernt die `AN`-Markierung.
  * **Automatisches OSD-Ausblenden:** Nach dem Klick auf `🌙` startet der 5-Sekunden-Countdown neu, sodass sich die OSD-Leiste nach 5 Sekunden ohne weiteren Tastendruck von selbst schließt.

### Technischer Ablauf im Code
1. **Toggle-Skript ([`kodi/addons/skin.arctic.fuse.2/shortcuts/toggle_nightmode.py`](../kodi/addons/skin.arctic.fuse.2/shortcuts/toggle_nightmode.py)):**
   * Prüft im Home-Window (`xbmcgui.Window(10000)`), ob `win.getProperty("NightMode_Active") == "true"` gesetzt ist.
   * Sendet in einer Schleife **10-mal** `xbmc.executebuiltin("Action(volampup)")` (`+10.0 dB`) bzw. beim Ausschalten **10-mal** `Action(volampdown)` (`-10.0 dB`) und aktualisiert `NightMode_Active`.
2. **Aktive Hervorhebung im Skin ([`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml), [`Includes_OSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_OSD.xml), [`Includes_Labels.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Labels.xml)):**
   * Button `6010` in `VideoOSD.xml` (Zeilen 203–218) setzt `<label>$VAR[Label_OSD_NightMode_Badge]</label>` (`AN` bei aktivem Nachtmodus) und `<textcolor>$VAR[ColorHighlight]</textcolor>` und übergibt `active_condition` sowie `iconoffset_condition` (`String.IsEqual(Window(Home).Property(NightMode_Active),true)`) an `OSD_Button_Icon_Overlay`.
   * `OSD_Button_Icon_Overlay` in `Includes_OSD.xml` (Zeilen 462–518) zeichnet bei `[$PARAM[active_condition]] + !Control.HasFocus($PARAM[id])` einen Kreis-Hintergrund (`colordiffuse="33ffffff"`) und färbt das Icon in `$VAR[ColorHighlight]` statt `panel_fg_70`.
3. **Automatische Persistenz über Episoden- und Staffelwechsel (`_apply_nightmode_if_active` in [`player.py`](../kodi/addons/plugin.video.themoviedb.helper/resources/tmdbhelper/lib/monitor/player.py), Zeilen 476–484):**
   * Da Kodi `volamp` beim Laden eines neuen Videostreams auf `0 dB` zurücksetzt, prüft `PlayerMonitor.get_playingitem()` bei jedem neuen Videostart `if Window(10000).getProperty("NightMode_Active") == "true":` und führt automatisch erneut **10-mal `Action(volampup)`** aus.

---

## 3. 📺 OSD-Header & Echter Episodentitel (`Label_OSD_Header`)

### Kurzüberblick & Bedienung
Über der Zeitleiste (`Control 3099` in [`DialogSeekBar.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/DialogSeekBar.xml)) wird der vollständige Medientitel eingeblendet:
* **Serien:** `[Serientitel] • [Staffel]x[Folge] • [Episodentitel]` (z. B. `My Name Is Earl • 1x01 • Pilot`)
* **Filme:** `[Filmtitel]`
* **Live-TV:** `Kanal [Nr] • [Sendung]` bzw. `[Sendername] • [Sendung]`
* **Bei Pause:** `Pause • [Serientitel] • [Staffel]x[Folge] • [Episodentitel]` (bzw. `Pause • [Filmtitel]`)

### Technischer Ablauf im Code
1. **Abruf des echten deutschen Episodentitels (`get_episode_title` in [`scraper.py`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py), Zeilen 323–335):**
   * Beim Start einer Episode (sowohl über `_search_and_play` als auch über `select_and_play`) ruft der Scraper `https://api.themoviedb.org/3/tv/{id}/season/{season}/episode/{episode}?api_key=...&language=de` (14 Tage im `cRequestHandler`-Cache) ab und liest `ep_data.get("name")` in `media_meta['episode_title']`.
   * In [`_listitem()`](../kodi/addons/script.module.xstreamscraper/resources/lib/scraper.py) (Zeilen 823–860) wird `info_tag.setTvShowTitle(meta['title'])` auf den Seriennamen und `info_tag.setTitle(ep_title)` auf den Episodentitel gesetzt.
2. **Formatierung in `Label_OSD_Header` ([`Includes_Labels.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Labels.xml), Zeilen 928–958):**
   * Während Spulen (`Player.Seeking | Player.HasPerformedSeek(3)`): Zeigt `Suche +00:10` / `-00:10`.
   * Während Pause (`Player.Paused`, Zeilen 948–950) und Wiedergabe (Zeilen 953–954): Prüft jeweils `!String.IsEqual(VideoPlayer.TVShowTitle,VideoPlayer.Title)`. Sind Serienname und Episodentitel unterschiedlich, werden beide getrennt durch `•` angezeigt; falls für eine Folge kein eigener Episodentitel existiert (`TVShowTitle == Title`), wird nur `[Serientitel] • [Staffel]x[Folge]` ohne Dopplung ausgegeben.

---

## 4. ⏱️ Automatisches Ausblenden der Timeline (5s OSD-Timer mit Reset & 2s Seekbar)

### Kurzüberblick & Bedienung
* **Vollständiges Video-OSD (geöffnet mit Steuerkreuz Oben `▲`):** Blendet sich nach **5 Sekunden ohne Tastendruck** automatisch aus. Jede Navigation zwischen den OSD-Buttons oder dem Timeline-Slider sowie ein Klick auf `🌙 Nachtmodus` setzt den 5-Sekunden-Timer zurück.
* **Reine Spul-Zeitleiste (bei Steuerkreuz Links / Rechts `◄` / `►`):** Blendet sich bereits **2 Sekunden** nach dem letzten 10-Sekunden-Sprung automatisch aus.

### Technischer Ablauf im Code
1. **Start & Reset des 5-Sekunden-Timers ([`VideoOSD.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/VideoOSD.xml) & [`Includes_Actions.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/Includes_Actions.xml), Zeilen 740–747):**
   * Beim Öffnen von `VideoOSD.xml` (Zeile 9) startet `<onload>` den Timer `AlarmClock(osd_timeout, ..., 00:05, silent)`.
   * Jeder Button `6001`–`6010` (über `Defs_OSD_Button`) sowie der Timeline-Slider `8200` bindet `Action_OSD_Button` ein:
     ```xml
     <include name="Action_OSD_Button">
         <onfocus condition="!String.IsEmpty(Skin.String(OSD_Timeout)) + [Window.IsVisible(videoosd) | Window.IsVisible(musicosd)]">AlarmClock(osd_timeout,RunScript(script.skinvariables,run_executebuiltin=special://skin/shortcuts/builtins/skinvariables-closeosd.json,use_rules=True),$INFO[Skin.String(OSD_Timeout),00:,],silent)</onfocus>
         <onfocus condition="String.IsEmpty(Skin.String(OSD_Timeout)) + [Window.IsVisible(videoosd) | Window.IsVisible(musicosd)]">AlarmClock(osd_timeout,RunScript(script.skinvariables,run_executebuiltin=special://skin/shortcuts/builtins/skinvariables-closeosd.json,use_rules=True),00:05,silent)</onfocus>
         <onunfocus>CancelAlarm(osd_timeout,true)</onunfocus>
         <onclick condition="!String.IsEmpty(Skin.String(OSD_Timeout)) + [Window.IsVisible(videoosd) | Window.IsVisible(musicosd)]">AlarmClock(osd_timeout,RunScript(script.skinvariables,run_executebuiltin=special://skin/shortcuts/builtins/skinvariables-closeosd.json,use_rules=True),$INFO[Skin.String(OSD_Timeout),00:,],silent)</onclick>
         <onclick condition="String.IsEmpty(Skin.String(OSD_Timeout)) + [Window.IsVisible(videoosd) | Window.IsVisible(musicosd)]">AlarmClock(osd_timeout,RunScript(script.skinvariables,run_executebuiltin=special://skin/shortcuts/builtins/skinvariables-closeosd.json,use_rules=True),00:05,silent)</onclick>
     </include>
     ```
   * Da in [`kodi/userdata/addon_data/skin.arctic.fuse.2/settings.xml`](../kodi/userdata/addon_data/skin.arctic.fuse.2/settings.xml) `<setting id="osd_timeout" type="string">05</setting>` gesetzt ist (und zusätzlich der `00:05`-Fallback existiert), startet jeder Fokuswechsel und jeder Klick auf Play/Pause (`6001`) oder Nachtmodus (`6010`) den 5-Sekunden-Countdown neu.
   * Nur beim Öffnen von Einstellungs-Dialogen (`6005` Info, `6006` Audio, `6007` Untertitel, `6008` Video, `6009` Stream-Wechsel) oder der Episoden-Schublade (`Window 1140`) wird `CancelAlarm(osd_timeout,true)` gerufen, damit sich der Dialog nicht während der Auswahl schließt.
2. **2-Sekunden-Ausblendung beim Spulen ([`DialogSeekBar.xml`](../kodi/addons/skin.arctic.fuse.2/1080i/DialogSeekBar.xml), Zeile 6):**
   Über die Sichtbarkeitsbedingung `Player.Seeking | Player.HasPerformedSeek(2)` wird die untere Zeitleiste beim direkten 10-Sekunden-Spulen (`◄` / `►`) ohne Button-Leiste eingeblendet und exakt 2 Sekunden nach dem letzten Sprung ausgeblendet.
